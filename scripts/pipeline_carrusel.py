#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Carrusel de la tanda: del Top 3 del escáner a las 3 Stories listas.

Encadena lo que ya existe en vez de reimplementarlo: `screener_gi` elige,
`serie_mt5` trae la serie real, `story_grafico` calcula la geometría,
`story_render` produce el PNG y `ruta_story.ps1` decide dónde se guarda.

**El reparto de trabajo es deliberado y no conviene borrarlo.** Este script
produce los DATOS de cada pieza: precio, soporte, resistencia, dirección,
impulso proyectado, la serie del gráfico. No escribe el titular ni el párrafo,
porque eso es criterio editorial y un script no lo tiene. Por eso hay dos pasos:

    1. `--preparar`  arma los 3 payloads con todos los datos resueltos y los
                     campos editoriales vacíos, marcados como pendientes.
    2. `--rendir`    valida que estén escritos y produce las imágenes
                     horizontales 16:9 de las piezas.

Si el paso 2 encuentra un campo editorial vacío, se detiene. Es la misma razón
por la que el renderer falla ante una imagen inexistente: una pieza a medias que
sale sin avisar llega al cliente.

Uso:
    uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar
    # ... el comando /carrusel escribe titular y parrafo en cada payload ...
    uv run --extra stories python scripts/pipeline_carrusel.py --rendir data/carrusel/<dir>
    uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py \
        --despachar data/carrusel/<dir>

`--rendir` es el unico de los tres que NO necesita MetaTrader5: trabaja sobre el
payload en disco. `--despachar` si lo necesita, porque refresca cada canal contra
el mercado justo antes de enviarlo; sin el paquete ese refresco no ocurre y el
guardia de divergencia no corre para ninguna pieza.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import zlib
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
for p in (str(SRC), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import screener_gi as sc  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
DIR_TRABAJO = RAIZ / "data" / "carrusel"
PLANTILLA = RAIZ / "templates" / "stories" / "alerta.html"

# Cuántas velas de H1 lleva el gráfico de la alerta. 60 velas de H1 son dos días
# y medio de sesión: suficiente para que el nivel que se está comunicando tenga
# historia visible detrás, sin que la línea se convierta en ruido.
VELAS_GRAFICO = 60
TIMEFRAME_GRAFICO = "H1"

# Los campos que este script NO puede llenar. Se escriben vacíos y `--rendir` se
# niega a trabajar hasta que tengan texto.
CAMPOS_EDITORIALES = ("titular", "parrafo")


def _slug_de_imagen(imagen: str) -> str:
    """El slug del activo es el nombre del archivo de imagen, sin extensión.

    Es la convención del repo (`oro.jpg` -> `activo-oro`) y la que hace que
    imagen y color salgan del mismo dato. Un ETF que replica un índice comparte
    las dos cosas: `GLD.US` usa `oro.jpg` y por tanto el dorado del Oro, que es
    exactamente como debe verse.
    """
    return Path(imagen).stem


def slug_del_activo(ticker: str, imagen: str | None) -> str:
    """El slug de la foto, o el del ticker si el activo no tiene foto.

    Sin foto (cobertura fija, 2026-09-28: el cobre) se usa la regla de
    `ruta_mensaje.ps1`: minusculas y sin `.spot`, `#` ni `/`.
    """
    if imagen:
        return _slug_de_imagen(imagen)
    return ticker.lower().replace(".spot", "").replace("#", "").replace("/", "")


def _chip_categoria(clase_o_cat: str, nombre_activo: str) -> str:
    etiquetas = {
        "forex": "DIVISAS",
        "commodities": "COMMODITIES",
        "forex_commodities": "COMMODITIES",
        "crypto": "CRIPTOMONEDAS",
        "indices": "ÍNDICES",
        "etfs": "ETF",
        "etf": "ETF",
        "acciones": "ACCIONES",
    }
    cat = etiquetas.get(clase_o_cat.lower(), "MERCADO")
    return f"{cat} · {nombre_activo.upper()}"


def _serie_para(ticker: str) -> dict[str, Any]:
    """Serie real de cierres desde el terminal, como bloque `recorrido`."""
    from serie_mt5 import obtener_serie

    cierres, _tiempos = obtener_serie(ticker, TIMEFRAME_GRAFICO, VELAS_GRAFICO)
    return cierres


def direccion_publicada(direccion_tecnica: str) -> str:
    """La dirección que muestra el chip de la pieza: `Alcista` o `Bajista`.

    Sale de la lectura técnica, que es la misma que usó el escáner para elegir el
    activo. Hasta el 2026-09-27 el chip lo mandaba el Playbook V2 en los 5 activos
    con ficha; al retirarlo queda una sola vara para todo el universo.
    """
    return "Alcista" if direccion_tecnica == "ALCISTA" else "Bajista"


class PayloadIncoherenteError(ValueError):
    """El payload no describe un solo instante del mercado."""


# Tope del desfase entre el precio del analizador y el ultimo cierre de la serie,
# en fracciones del ATR de H1. **Medido, no estimado**: sobre los 16 payloads que
# quedaron en disco, 15 dan desfase EXACTAMENTE 0,000 y el peor sano da 0,0033 ATR
# (un tick de USD/JPY). El caso que motivo el control daba 1,9 ATR. 0,25 deja 75
# veces de margen sobre lo sano y 7,5 veces por debajo del fallo.
TOLERANCIA_DESFASE_ATR = 0.25


def incoherencia_del_payload(
    seleccion: dict[str, Any], cierres: list[float]
) -> str | None:
    """Por que este payload no describe un solo instante, o `None` si esta sano.

    Un payload de activo junta DOS lecturas independientes del terminal: el
    analizador tecnico (`analizar_activo`, 300 velas) da precio y niveles, y
    `serie_mt5` (60 velas) da la serie del grafico. Nada las confrontaba, y el
    2026-09-04 salieron desacopladas: GLD.US se preparo con score 100/100, precio
    410,37 y una serie que terminaba en 405,32, o sea que el precio era el CUARTO
    valor desde el final de su propia serie.

    El renderer no lo delata: dibuja el punto en `serie[idx]` y le pone como
    rotulo el precio del marcador, asi que la pieza se veia impecable con dos
    numeros distintos adentro. Por eso el control tiene que estar aca, antes de
    que el payload exista.

    Lo que este control NO cubre, para no prometer de mas: la invariante
    `soporte < precio < resistencia` la cumplen los 16 payloads de disco, GLD
    incluido (410,37 cae entre 409,72 y 424,45), asi que **no** habria atajado el
    caso. Se verifica igual porque es gratis y sostiene otra falla distinta, pero
    el desfase contra la serie es el que importa.
    """
    if not cierres:
        return "la serie del grafico vino vacia: la pieza no tendria recorrido que dibujar"

    precio = float(seleccion["precio"])
    soporte = float(seleccion["soporte"])
    resistencia = float(seleccion["resistencia"])
    ultimo = float(cierres[-1])
    atr = float(seleccion.get("atr_h1") or 0.0)

    if atr <= 0:
        return (
            "el analizador no devolvio ATR de H1, asi que el desfase contra la serie "
            "no se puede juzgar en la escala del activo"
        )

    desfase = abs(precio - ultimo)
    if desfase > TOLERANCIA_DESFASE_ATR * atr:
        return (
            f"el precio ({precio}) no es el ultimo cierre de su propia serie "
            f"({ultimo}): {desfase:.4f} de diferencia, "
            f"{desfase / atr:.2f} veces el ATR de H1. El analizador y la serie "
            "leyeron momentos distintos del mercado"
        )

    if not soporte < precio < resistencia:
        return (
            f"el precio ({precio}) no cae entre el soporte ({soporte}) y la "
            f"resistencia ({resistencia}): los niveles no corresponden a este precio"
        )

def acotar_niveles_intradia(
    spot: float,
    soporte: float,
    resistencia: float,
    atr_d1: float | None,
    digits: int,
) -> tuple[float, float]:
    """Acota soporte y resistencia al rango intradía del ATR D1 si la amplitud excede 1.5 * ATR_D1."""
    if not atr_d1 or atr_d1 <= 0:
        return soporte, resistencia

    rango_max = 1.5 * atr_d1
    if (resistencia - soporte) > rango_max or (spot - soporte) > atr_d1 or (resistencia - spot) > atr_d1:
        sop_acotado = round(spot - atr_d1, digits)
        res_acotada = round(spot + atr_d1, digits)
        return sop_acotado, res_acotada

    return soporte, resistencia


def formatear_precio(valor: float, digits: int) -> str:
    """Precio en notacion chilena con los decimales de `digits`.

    Con `digits = 0` (el cobre) va entero y sin separador de miles: "14.417" se
    lee como un decimal y no coincide con la etiqueta del grafico.
    """
    if digits == 0:
        return f"{valor:.0f}"
    return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def construir_payload(
    seleccion: dict[str, Any],
    activo_catalogo: dict[str, Any],
    ahora: datetime,
    cierres: list[float],
) -> dict[str, Any]:
    """El payload de una pieza de alerta, listo para redactar y rendir."""
    motivo = incoherencia_del_payload(seleccion, cierres)
    if motivo is not None:
        raise PayloadIncoherenteError(f"{seleccion['ticker']}: {motivo}")
    digits = activo_catalogo["digits"]
    imagen = activo_catalogo.get("imagen") or ""
    slug = slug_del_activo(seleccion["ticker"], imagen)
    cat_real = activo_catalogo.get("categoria", seleccion["clase"])

    def fmt(valor: float) -> str:
        return formatear_precio(valor, digits)

    spot_crudo = float(seleccion["precio"])
    sop_crudo = float(seleccion["soporte"])
    res_crudo = float(seleccion["resistencia"])
    atr_d1 = seleccion.get("atr_d1")

    sop_final, res_final = acotar_niveles_intradia(spot_crudo, sop_crudo, res_crudo, atr_d1, digits)

    sesgo_pieza = direccion_publicada(seleccion["direccion"])

    return {
        "plantilla": "alerta",
        # Editorial: lo llena el comando, no el script.
        "titular": "",
        "parrafo": "",
        # Identidad y marco
        "activo": activo_catalogo["nombre"],
        "activo_slug": slug,
        "activo_imagen": imagen,
        "rotulo_activo": f"{activo_catalogo['nombre'].upper()} · {seleccion['ticker']}",
        "chip_categoria": _chip_categoria(cat_real, activo_catalogo["nombre"]),
        "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
        # El chip sigue a la lectura tecnica. Ver `direccion_publicada`.
        "sesgo": sesgo_pieza,
        "tag_riesgo": sesgo_pieza.upper(),
        # Datos del motor
        "precio_actual": fmt(spot_crudo),
        "soporte": fmt(sop_final),
        "resistencia": fmt(res_final),
        "vol_pct": f"{fmt(seleccion['impulso_adc_atr'])} {activo_catalogo['unidad']}",
        # Por que ESTA temporalidad para ESTE activo. Sin default a proposito, con
        # el mismo criterio que `unidad`: la linea es obligatoria en el mensaje, y
        # una justificacion generica ("1H equilibra senal y ruido") no explica
        # nada. `preparar()` excluye al activo si falta.
        "nota_volatilidad": activo_catalogo["nota_volatilidad"],
        "volatilidad": activo_catalogo.get("volatilidad"),
        # Zona de aviso del gate de banda, si el escaner la marco.
        "banda_estrecha": seleccion.get("banda_estrecha"),
        "rotulo_grafico": (
            f"{seleccion['ticker']} · CIERRES {TIMEFRAME_GRAFICO} · "
            f"ÚLTIMAS {VELAS_GRAFICO} VELAS"
        ),
        "sello_datos": (
            f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}"
        ),
        "fuente": "MT5 · GRUPO INTELIGENCIA",
        "chart_png": None,
        "recorrido": {
            "serie": cierres,
            "lienzo": "alto",
            "marcadores": [{
                "indice": len(cierres) - 1,
                "precio": spot_crudo,
                "clase": "actual",
                "etiqueta": fmt(spot_crudo),
                "rol": "AHORA",
            }],
            "niveles": [
                {"precio": res_final, "clase": "resistencia",
                 "etiqueta": fmt(res_final), "rol": "RESISTENCIA"},
                {"precio": sop_final, "clase": "soporte",
                 "etiqueta": fmt(sop_final), "rol": "SOPORTE"},
            ],
        },
        # Trazabilidad: por qué este activo y no otro. No se rinde en la pieza,
        # pero deja el score auditable junto al payload que produjo.
        "_procedencia": {
            "score": seleccion["score"],
            "factores": seleccion["factores"],
            "ticker": seleccion["ticker"],
            # Los precios SIN formatear. El payload solo lleva la notación
            # chilena ("936,32"), que sirve para dibujar pero no para comparar:
            # el despacho necesita números para saber si el precio cruzó un
            # nivel que el texto ya dio por bueno.
            "crudos": {
                "precio": float(seleccion["precio"]),
                "soporte": float(seleccion["soporte"]),
                "resistencia": float(seleccion["resistencia"]),
            },
        },
        "_pendiente_editorial": list(CAMPOS_EDITORIALES),
    }


MAPEO_GRUPOS_WHATSAPP: dict[str, str] = {
    "forex": "02_forex_divisas",
    "commodity": "03_commodities_materias_primas",
    "commodities": "03_commodities_materias_primas",
    "forex_commodities": "03_commodities_materias_primas",
    "indices": "04_indices_bursatiles",
    "indice": "04_indices_bursatiles",
    "acciones": "05_acciones_etfs",
    "accion": "05_acciones_etfs",
    "etfs": "05_acciones_etfs",
    "etf": "05_acciones_etfs",
    "crypto": "06_criptoactivos",
    "macro": "01_macro_y_apertura",
}


class GrupoDesconocidoError(ValueError):
    """El destino pedido no corresponde a ningún canal configurado.

    Se levanta en vez de caer al canal macro: un `--grupo metales` que no se
    reconoce y termina publicando en el grupo padre es un error silencioso que
    solo se descubre cuando el cliente ya lo recibió.
    """


CONFIG_GRUPOS_PATH = Path(__file__).resolve().parent.parent / "config" / "whatsapp_grupos.json"


def _indice_alias() -> dict[str, str]:
    """alias/slug/nombre oficial -> slug de la carpeta, leído del config.

    La fuente es `config/whatsapp_grupos.json` y no una tabla propia: cuando el
    vocabulario vive en dos lados, uno queda atrás y el mismo pedido termina en
    canales distintos según quién lo ejecute.
    """
    try:
        datos = json.loads(CONFIG_GRUPOS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    indice: dict[str, str] = {}
    for slug, info in (datos.get("grupos") or {}).items():
        indice[slug.lower()] = slug
        for clave in ("nombre_oficial", "nombre_aspiracional"):
            valor = str(info.get(clave) or "").strip().lower()
            if valor:
                indice[valor] = slug
        for alias in info.get("alias", []):
            indice[str(alias).strip().lower()] = slug
    return indice


def resolver_grupo_solicitado(pedido: str) -> str:
    """El canal que pidió el director, o un error que nombra las opciones."""
    clave = str(pedido).strip().lower()
    indice = _indice_alias()
    if clave in indice:
        return indice[clave]
    # Se acepta también el nombre corto del canal ("metales & energía").
    for nombre, slug in indice.items():
        if clave and (clave in nombre or nombre.endswith(f"| {clave}")):
            return slug
    opciones = sorted({s for s in indice.values()})
    raise GrupoDesconocidoError(
        f"No reconozco el canal {pedido!r}. Canales configurados: {', '.join(opciones)}. "
        "Usa un alias de config/whatsapp_grupos.json (por ejemplo: forex, metales, indices, "
        "acciones, cripto, senales, macro)."
    )


def obtener_grupo_whatsapp(cat_o_clase: str, ticker: str) -> str:
    """Mapea un activo o categoría al directorio del grupo de WhatsApp correspondiente."""
    ticker_clean = ticker.upper()
    if (
        ticker_clean in ("USDCLP", "EURUSD", "USDJPY", "GBPUSD", "USDIDX")
        or "USD/CLP" in ticker_clean
        or "EUR/USD" in ticker_clean
        or "USD/JPY" in ticker_clean
        or "GBP/USD" in ticker_clean
    ):
        return "02_forex_divisas"
    if ticker_clean in (
        "XAUUSD", "XAGUSD", "WTI.SPOT", "WTI", "BRENT.SPOT", "BRENT", "COPPER",
        "ORO", "PLATA", "COBRE",
    ):
        return "03_commodities_materias_primas"
    if ticker_clean in (
        "BTCUSD", "ETHUSD", "SOLUSD", "LTCUSD", "ADAUSD", "DOGUSD", "DOGEUSD",
    ):
        return "06_criptoactivos"
    if ticker_clean in (
        "US100.SPOT", "US500.SPOT", "US30.SPOT", "GER40.SPOT",
        "US100", "US500", "US30", "GER40",
    ):
        return "04_indices_bursatiles"
    if (
        ticker_clean.startswith("#")
        or ticker_clean.endswith(".US")
        or cat_o_clase.lower() in ("acciones", "accion", "etf", "etfs")
    ):
        return "05_acciones_etfs"
    canal = MAPEO_GRUPOS_WHATSAPP.get(cat_o_clase.lower())
    if canal is None:
        raise GrupoDesconocidoError(
            f"No reconozco la categoria {cat_o_clase!r} (ticker {ticker!r}). "
            f"Categorias mapeadas: {', '.join(sorted(MAPEO_GRUPOS_WHATSAPP))}. "
            "Si lo que tienes es el slug de un canal, ya esta resuelto y no hay que "
            "mapearlo; si es una categoria nueva del catalogo, agregala al mapeo."
        )
    return canal


# Las cuatro etiquetas canonicas de temporalidad (`CLAUDE.md`, issue #44). Cada
# marco lleva su rango cuantificado porque decir "corto" sin numero esta prohibido:
# el cliente no sabe si son minutos o semanas.
#
# Vivian SOLO en markdown (`CLAUDE.md` y `.claude/commands/story.md`) y ahora
# tambien aca, que es lo que las publica. Un test de contrato compara las dos
# copias, porque tres tablas iguales divergen: `CLAUDE.md` todavia nombra como
# fuente unica a `.claude/commands/apertura.md`, que **ya no existe**.
MARCOS_CANONICOS: dict[str, tuple[str, str]] = {
    "M15": ("15M", "scalper (minutos a 1-2 h)"),
    "H1": ("1H", "intradía (dentro de la jornada)"),
    "H4": ("4H", "swing de jornada (1-3 días)"),
    "D1": ("1D", "posicional (días a semanas)"),
}


CANAL_AVISOS = "01_macro_y_apertura"


def canales_con_contexto_macro(
    payloads: list[dict[str, Any]],
    grupo_pedido: str | None = None,
) -> set[str]:
    """Los canales que reciben la lectura macro de esta corrida.

    Vive aparte porque las tres reglas que la componen se decidieron por separado
    y antes estaban mezcladas en tres lineas de `preparar`, donde una de ellas
    estaba equivocada y no se veia:

    1. **Todo canal con piezas** recibe su macro: es el contexto de lo que va a leer.
    2. **El canal pedido con `--grupo`**, aunque quede vacio. `grupo_pedido` llega
       ya resuelto a slug por `resolver_grupo_solicitado`, asi que se usa tal cual.
       Antes se lo pasaba a `obtener_grupo_whatsapp`, que espera una *categoria*:
       ninguna rama aplicaba, caia al default y el resultado era que el canal
       pedido no recibia nada y el macro se lo llevaba entero el de avisos.
    3. **Nunca el canal de avisos** (decision del director del 2026-09-29, que
       revierte la del 2026-09-03 "el canal de avisos, siempre"). Avisos es de
       `pipeline_avisos`: la agenda del dia y el resultado de cada dato. Con la
       regla vieja, toda tanda le armaba su contexto, y como la bitacora deduplica
       por tanda, una tanda de solo WTI reenvio a Avisos el contexto del VIX media
       hora despues del bueno. Se descarta aca y no solo al sumar, asi ni un
       `--grupo macro` ni una pieza mal mapeada lo vuelven a meter.
    """
    canales = {p["grupo"] for p in payloads if p.get("grupo")}
    if grupo_pedido:
        canales.add(grupo_pedido)
    canales.discard(CANAL_AVISOS)
    return canales


# Cierres del mensaje de alerta (decision del director, 2026-09-28): desmecanizar
# el grupo. Un solo cierre repetido en cada pieza se lee como plantilla, y cerrar
# siempre con el analista suena a soporte tecnico. El analista queda en una sola.
CIERRES_ALERTA: tuple[str, ...] = (
    "¿Cómo lo ves tú? Te leemos en el grupo.",
    "Vamos siguiendo la reacción del precio en esos niveles durante la jornada.",
    "Atentos a los bordes: ahí está la operativa del día.",
    "Si tienes dudas con la operativa, escríbele a tu analista.",
    "La configuración está clara: el precio decide por qué lado sale.",
)


def elegir_variante(opciones: tuple[str, ...], *claves: str) -> str:
    """Una variante estable para las mismas claves.

    Variar no es azar: el despacho vuelve a rendir el texto justo antes de
    enviarlo, y un cierre al azar cambiaria el mensaje que el director aprobo.
    """
    return opciones[zlib.crc32("|".join(claves).encode("utf-8")) % len(opciones)]


def construir_mensaje_alerta(payload: dict[str, Any]) -> str:
    """Genera el mensaje de texto de alerta formateado para WhatsApp según las 6 reglas canónicas."""
    activo = payload["activo"]
    rotulo = payload.get("rotulo_activo", activo)
    ticker = rotulo.split("·")[-1].strip() if "·" in rotulo else activo
    precio = payload.get("precio_actual") or payload.get("precio") or "--"
    soporte = payload.get("soporte", "--")
    resistencia = payload.get("resistencia", "--")
    vol = payload.get("vol_pct", "")
    sesgo = payload.get("sesgo", "Alcista")
    alcista = sesgo.lower() == "alcista"
    lateral = sesgo.lower() == "lateral"

    # **`no alcista` no significa bajista.** Las piezas de recap salen con el
    # chip en `Lateral`, y caer al caso bajista por descarte publicaba "presión
    # vendedora" sobre un activo del que justamente no se afirma dirección.
    #
    # Voz del director (2026-09-28): directa y de mesa, con el sesgo dicho primero
    # y el nivel que lo hace ganar camino.
    if lateral:
        nivel_vigilar = f"{soporte} y {resistencia}"
        accion = "rango; se opera de borde a borde"
    elif alcista:
        nivel_vigilar = resistencia
        accion = f"sesgo comprador; sobre {resistencia} gana camino al alza"
    else:
        nivel_vigilar = soporte
        accion = f"sesgo vendedor; bajo {soporte} gana camino a la baja"

    titular = payload.get("titular", "").strip()

    # Formato compacto (decision del director, 2026-09-28): el mensaje es para
    # actuar. El parrafo editorial, el diccionario, la guia del Manual y la
    # pregunta al canal salieron: la pieza visual ya lleva el detalle, y un texto
    # largo esconde bajo el "leer mas" justo los niveles que el cliente necesita.
    lineas = [
        f"🎯 Activo: {activo} ({ticker})",
        f"📌 Nivel a vigilar: {nivel_vigilar}",
        f"⚡ Qué esperar: {accion}",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    if titular:
        lineas.append(f"*{titular}*")
    lineas.extend([
        f"Precio actual: {precio}",
        "━━━━━━━━━━━━━━━━━━━",
        f"⬆️ Sobre {resistencia} → fuerza compradora",
        # La zona media tambien se opera (decision del director, 2026-09-28):
        # quien sabe operar la configuracion nunca tiene que quedarse esperando.
        f"↔️ Entre {soporte} y {resistencia} → rango: si rompe un borde y vuelve a "
        "entrar, es falso quiebre y el objetivo pasa a ser el borde contrario",
        f"⬇️ Bajo {soporte} → presión vendedora",
        "━━━━━━━━━━━━━━━━━━━",
    ])

    # La temporalidad, justificada por la volatilidad de ESE activo. Obligatoria
    # desde el issue #44 y nunca implementada: el token `por_que_temporalidad`
    # existia en un solo lugar del repo, que era la propia norma, y el 2026-09-04
    # dos piezas salieron sin el bloque.
    etiqueta, descripcion = MARCOS_CANONICOS[TIMEFRAME_GRAFICO]
    lineas.append(f"⏱️ *Temporalidad*: {etiqueta} · marco {descripcion}")
    nota = payload.get("nota_volatilidad")
    if nota:
        lineas.append(f"💡 Por qué {etiqueta} acá: {nota}")

    # Los bordes estrechos se dicen. El gate de banda deja pasar la pieza entre
    # 0,70x y 1,00x, y callar que sus niveles son apretados para lo que el activo
    # se mueve seria publicar la parte comoda de la medicion.
    ratio = payload.get("banda_estrecha")
    if ratio:
        veces = f"{float(ratio):.2f}".replace(".", ",")
        lineas.append(
            f"⚠️ Niveles estrechos para su volatilidad: en una hora normal el "
            f"activo recorre {veces} de la distancia entre soporte y resistencia, "
            "así que los bordes se rompen con facilidad: ojo con los falsos quiebres."
        )
    lineas.append(elegir_variante(CIERRES_ALERTA, ticker, payload.get("fecha_hora", "")))
    return "\n".join(lineas)


def limpiar_payloads(
    directorio: Path, solo_canales: set[str] | None = None
) -> list[str]:
    """Borra los payloads y archivos generados de una corrida anterior de la MISMA tanda.

    `rendir()` toma todos los `.json` sin prefijo `_` del directorio de forma recursiva.
    Sin este barrido, volver a preparar deja los viejos al lado de los nuevos.

    **`solo_canales` acota el barrido a la unidad del preparado.** El directorio de
    tanda se nombra por MINUTO y `--preparar --grupo` opera por CANAL: dos
    corridas en el mismo minuto natural comparten carpeta, y el `rglob` sobre la
    tanda entera hacia que la segunda se llevara los payloads de la primera. Paso
    el 2026-09-04 con doce payloads de commodities, y el escaner reporto
    "barridos 12 payload(s)" sin que eso se leyera como un problema.

    Sin `solo_canales` el barrido sigue siendo global, que es lo correcto para
    `--matriz`: ahi la corrida escribe todos los canales. El cambio acota la
    unidad, no elimina el barrido.
    """
    barridos = []
    if not directorio.exists():
        return barridos
    for archivo in directorio.rglob("*"):
        if archivo.is_file():
            if archivo.name.startswith("_"):
                continue
            if solo_canales is not None:
                # La carpeta de canal es el primer tramo relativo. Un archivo en
                # la raiz de la tanda (el mensaje indice) no pertenece a ningun
                # canal, asi que con barrido acotado se conserva.
                relativo = archivo.relative_to(directorio).parts
                if len(relativo) < 2 or relativo[0] not in solo_canales:
                    continue
            if archivo.suffix in (".json", ".png", ".txt"):
                archivo.unlink()
                barridos.append(archivo.name)
    # Limpiar directorios vacíos
    for sub in list(directorio.iterdir()):
        if sub.is_dir() and not any(sub.iterdir()):
            try:
                sub.rmdir()
            except OSError:
                pass
    return sorted(barridos)


# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: preparar
# ─────────────────────────────────────────────────────────────────────────────
def escribir_suplementos(
    destino: Path,
    excluidos: list[dict[str, Any]],
    grupos_activos: set[str],
    catalogo: dict[str, Any],
    ruta_historial: Path | None = None,
    buscar_noticia: Any = None,
    es_cierre: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Escribe el suplemento de cada canal que quedo sin activos publicables.

    **Solo cubre canales VACIOS.** Un suplemento junto a piezas de activo seria
    el relleno que el manual del comando prohibe; su valor esta justamente en
    que aparece cuando no hay nada mas que decir, y explica por que.

    El motivo lo pone el escaner y no se inventa aca: si el canal quedo vacio
    porque sus activos gastaron el recorrido del dia, eso es lo que se publica,
    con la cifra medida y el concepto que lo explica. Ver `suplemento_canal`.

    Devuelve los suplementos escritos y los avisos, porque un canal que se queda
    sin suplemento tambien tiene que decirlo: en silencio parece que no habia
    nada que cubrir.
    """
    from noticia_oficial import registrar_noticia
    from suplemento_canal import (
        construir_mensaje_suplemento,
        encuesta_cierre,
        registrar_suplemento,
        suplemento,
    )

    # Las exclusiones se reparten por canal con el mismo mapeo que las piezas.
    por_canal: dict[str, list[dict[str, Any]]] = {}
    for ex in excluidos:
        activo = catalogo.get(ex.get("ticker", ""))
        clase = ex.get("clase") or (activo or {}).get("clase", "")
        canal = obtener_grupo_whatsapp(clase, ex.get("ticker", ""))
        por_canal.setdefault(canal, []).append(ex)

    escritos: list[dict[str, Any]] = []
    avisos: list[str] = []
    for canal, exclusiones in sorted(por_canal.items()):
        if canal in grupos_activos:
            continue                      # el canal tiene piezas: no hay vacio que cubrir
        sup = suplemento(canal, exclusiones)
        if sup is None:
            avisos.append(
                f"{canal} quedo vacio y sin suplemento: sus {len(exclusiones)} "
                f"exclusiones no son una lectura de mercado publicable"
            )
            continue
        carpeta = destino / canal
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "0_suplemento.txt").write_text(
            construir_mensaje_suplemento(sup, es_cierre=es_cierre), encoding="utf-8"
        )
        (carpeta / "_suplemento.json").write_text(
            json.dumps(sup, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if es_cierre:
            enc = encuesta_cierre(canal)
            if enc:
                (carpeta / "_encuesta.json").write_text(
                    json.dumps(enc, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        # La ventana anti repeticion se anota al PREPARAR. Una tanda preparada y
        # descartada gasta la ventana igual, y ese error va hacia el lado
        # seguro: repetir de menos, no de mas.
        registrar_suplemento(sup, ruta=ruta_historial)

        # **La noticia es estrictamente aditiva.** El suplemento de estado de
        # arriba ya quedo escrito y es dispachable tal cual; si hay una nota
        # oficial fresca y relevante, el comando la anexa al RENDIR, porque el
        # titular viene en ingles y `--preparar` es Python puro. Si el comando
        # no corre, no se pierde nada: el canal conserva su suplemento.
        noticia = None
        if buscar_noticia is not None:
            try:
                noticia = buscar_noticia(canal)
            except Exception as e:  # noqa: BLE001
                avisos.append(
                    f"{canal}: no se pudo consultar fuentes oficiales ({e})"
                )
        if noticia:
            (carpeta / "_noticia.json").write_text(
                json.dumps(noticia, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            registrar_noticia(noticia, ruta=ruta_historial)
            sup["noticia"] = True
            avisos.append(
                f"{canal}: hay nota oficial de {noticia['organismo']} del "
                f"{noticia['fecha'].date()} para anexar al rendir"
            )

        # Generar payload de Recap para que el canal cuente con gráfico TradingView (16:9)
        ancla = sup.get("activo_ancla") or {}
        ticker_ancla = ancla.get("ticker")
        if ticker_ancla:
            slug_ancla = ticker_ancla.lower().replace(".", "").replace("#", "")
            rotulo = ancla.get("rotulo", ticker_ancla)
            nombre_act = ancla.get("nombre", rotulo)
            cat_rotulo = ancla.get("categoria", "MERCADO")

            activo_cat = catalogo.get(ticker_ancla, {})
            digits = activo_cat.get("digits", 2)
            fmt = lambda v: formatear_precio(v, digits)

            # Obtener niveles reales desde exclusiones o analizador
            spot_val = None
            sop_val = None
            res_val = None
            for ex in exclusiones:
                if ex.get("ticker") == ticker_ancla:
                    spot_val = ex.get("precio")
                    sop_val = ex.get("soporte")
                    res_val = ex.get("resistencia")
                    break

            if spot_val is None:
                try:
                    from market_data_mcp.analisis import analizar_activo
                    h1_res = analizar_activo(ticker_ancla, "H1")
                    if "error" not in h1_res:
                        spot_val = h1_res.get("price") or h1_res.get("precio")
                        sop_val = h1_res.get("s1")
                        res_val = h1_res.get("r1")
                except Exception:
                    pass

            spot_txt = fmt(float(spot_val)) if spot_val is not None else "--"
            sop_txt = fmt(float(sop_val)) if sop_val is not None else "--"
            res_txt = fmt(float(res_val)) if res_val is not None else "--"

            if es_cierre:
                titular_recap = f"{rotulo} consolida en zona de balance tras completar su recorrido"
                parrafo_recap = (
                    f"El activo completó su rango habitual de la jornada. "
                    f"Soporte técnico situado en {sop_txt} y resistencia en {res_txt}. "
                    "Estructura en compresión a la espera de la apertura del próximo ciclo."
                )
            else:
                titular_recap = f"{rotulo} define zonas de balance y niveles clave para la sesión"
                parrafo_recap = (
                    f"El activo inicia la jornada en rango técnico de consolidación. "
                    f"Soporte técnico clave en {sop_txt} y resistencia en {res_txt}. "
                    "A la espera de confirmación y flujo institucional para definir la dirección de la jornada."
                )

            momento_ahora = datetime.now(tz=SANTIAGO)
            recap_payload = {
                "activo": nombre_act,
                "rotulo_activo": rotulo,
                "activo_slug": slug_ancla,
                "categoria": cat_rotulo,
                "chip": f"{cat_rotulo} · {rotulo}",
                "direccion": "LATERAL",
                "sesgo": "Lateral",
                "tag_riesgo": "BALANCE",
                "tipo_pieza": "recap",
                "precio": spot_txt,
                "precio_actual": spot_txt,
                "soporte": sop_txt,
                "resistencia": res_txt,
                "titular": titular_recap,
                "parrafo": parrafo_recap,
                "vol_pct": f"1,5 {activo_cat.get('unidad', '')}".strip(),
                "por_que_temporalidad": f"En H1 se observa el balance completo de la jornada de {rotulo}.",
                "fecha_hora_texto": momento_ahora.strftime("%d/%m/%Y · %H:%M hrs"),
                "_procedencia": {
                    "ticker": ticker_ancla,
                    "score": 0,
                    "tipo": "recap_suplemento",
                    "crudos": {
                        "precio": float(spot_val) if spot_val is not None else 0.0,
                        "soporte": float(sop_val) if sop_val is not None else 0.0,
                        "resistencia": float(res_val) if res_val is not None else 0.0,
                    },
                }
            }

            archivo_recap = carpeta / f"1_recap_{slug_ancla}.json"
            archivo_recap.write_text(
                json.dumps(recap_payload, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            msg_alerta_recap = construir_mensaje_alerta(recap_payload)
            (carpeta / f"1_recap_{slug_ancla}_mensaje.txt").write_text(msg_alerta_recap, encoding="utf-8")
            (carpeta / "mensaje.txt").write_text(msg_alerta_recap, encoding="utf-8")

        escritos.append(sup)
        avisos.append(
            f"{canal} quedo vacio: se suplementa con "
            f"{sup['resumen']['categoria']} y el concepto "
            f"{(sup.get('concepto') or {}).get('clave', 'ninguno')}"
        )
    return escritos, avisos


def preparar(
    tanda: int | None = None,
    top: int = 3,
    solo_renderizables: bool = True,
    grupo: str | None = None,
    modo_matriz: bool = False,
    forzar: bool = False,
) -> dict[str, Any]:
    """Corre el escáner y deja los payloads listos organizados por grupo de WhatsApp."""
    resultado = sc.escanear(
        tanda=tanda,
        top=top,
        solo_renderizables=solo_renderizables,
        grupo=grupo,
        modo_matriz=modo_matriz,
        # Pedir un canal acota el universo y **nada más**. Antes esto también
        # apagaba el gate de agotamiento, sin decirlo: dos cosas sin relación
        # metidas en la misma bandera. El 2026-09-03 el canal de forex salió con
        # tres piezas cuyo recorrido diario estaba consumido al 93 %, 290 % y
        # 115 %, y el escáner no reportó ninguna exclusión porque no las hubo.
        #
        # El manual del comando ya exigía lo contrario: "una tanda de 2 piezas
        # bien elegidas es mejor que una de 3 con un relleno". Apagar un gate
        # para llenar cupos es el relleno. Ahora solo `--forzar` lo apaga, y el
        # escáner lo anuncia en sus avisos.
        ignorar_agotamiento=forzar,
    )
    ahora = datetime.now(tz=SANTIAGO)
    n_tanda = resultado["tanda"]
    slug_sesion = resultado.get("sesion_slug", f"tanda{n_tanda}")
    hora_str = ahora.strftime("%H-%M")

    catalogo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}

    destino = DIR_TRABAJO / f"{ahora.strftime('%Y-%m-%d')}_{hora_str}_{slug_sesion}"
    destino.mkdir(parents=True, exist_ok=True)

    (destino / "_screener.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # `preparar` llama a `escanear` como función y no por su CLI, así que sin
    # esto nunca se escribía en `data/screener/`: el filtro "ya salió hoy" de
    # `_publicados_hoy` lee justo de ahí, y una segunda tanda del mismo día no
    # veía la primera. Medido el 2026-09-14: USD/JPY salió dos veces en menos
    # de dos horas, en dos tandas manuales del mismo día.
    sc._guardar(resultado)

    # Los canales que ESTA corrida va a escribir: el pedido con `--grupo` o todos
    # si es una corrida completa. Avisos nunca: es de `pipeline_avisos`.
    canales_a_barrer = (
        canales_con_contexto_macro([], grupo_pedido=grupo) if grupo else None
    )
    barridos = limpiar_payloads(destino, solo_canales=canales_a_barrer)

    payloads: list[dict[str, Any]] = []
    problemas: list[str] = []
    for i, sel in enumerate(resultado["seleccion"], 1):
        activo = catalogo.get(sel["ticker"])
        # La cobertura fija sale sin foto: su pieza es el grafico del motor.
        if not activo or not (activo.get("imagen") or sel.get("cobertura_fija")):
            problemas.append(
                f"{sel['ticker']} no tiene imagen declarada: su pieza no se puede rendir"
            )
            continue
        if not activo.get("unidad"):
            problemas.append(
                f"{sel['ticker']} no declara `unidad` en config/activos.json: "
                "la volatilidad quedaria sin moneda"
            )
            continue
        try:
            cierres = _serie_para(sel["ticker"])
        except Exception as exc:  # noqa: BLE001
            problemas.append(f"{sel['ticker']}: no se pudo traer la serie ({exc})")
            continue

        try:
            payload = construir_payload(sel, activo, ahora, cierres)
        except PayloadIncoherenteError as exc:
            problemas.append(str(exc))
            continue
        cat_real = activo.get("categoria", sel["clase"])
        grupo_nombre = obtener_grupo_whatsapp(cat_real, sel["ticker"])
        if grupo_nombre == CANAL_AVISOS:
            # Una categoria mapeada a Avisos es un error del catalogo, no una pieza:
            # Avisos es de `pipeline_avisos` (decision del 2026-09-29).
            problemas.append(f"{sel['ticker']}: su categoria apunta a Avisos, que no recibe alertas del carrusel")
            continue
        grupo_dir = destino / grupo_nombre
        grupo_dir.mkdir(parents=True, exist_ok=True)

        slug_nombre = sc._normalizar(sel["ticker"]).replace(".", "").replace("#", "")
        archivo = grupo_dir / f"{i}_{slug_nombre}.json"
        archivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # Guardar borrador del mensaje de WhatsApp para ese grupo
        msg_draft = construir_mensaje_alerta(payload)
        (grupo_dir / f"{i}_{slug_nombre}_mensaje.txt").write_text(msg_draft, encoding="utf-8")

        payloads.append({
            "archivo": str(archivo),
            "ticker": sel["ticker"],
            "score": sel["score"],
            "grupo": grupo_nombre,
        })

    # Asegurar la cobertura de contexto macro diario en cada carpeta de grupo activa
    from contexto_macro_grupos import asegurar_contexto_macro_grupo
    # El tercer valor son los avisos de la fuente macro, y se descartaban con un
    # `_`. `_contexto_macro` ya emitia "la UST 10Y no tiene variacion diaria
    # calculable hoy" y "calendario no disponible: blackouts sin verificar", y
    # nadie los leia: el escaner los reporta por su cuenta, pero estos son de la
    # segunda llamada que hace el pipeline y quedaban en el piso.
    eventos_macro, delta_ust, avisos_macro = sc._contexto_macro(ahora)
    grupos_activos = canales_con_contexto_macro(payloads, grupo_pedido=grupo)

    # Cuantas piezas de niveles va a recibir cada canal. El cierre del contexto
    # macro las anuncia, y hasta el 2026-09-04 las prometia siempre: el canal de
    # avisos, que nunca lleva niveles, recibio la promesa igual.
    piezas_por_canal = Counter(p["grupo"] for p in payloads if p.get("grupo"))
    for grp in grupos_activos:
        asegurar_contexto_macro_grupo(
            grupo=grp,
            destino_grupo=destino / grp,
            eventos=eventos_macro,
            delta_ust_bps=delta_ust,
            ahora=ahora,
            piezas_de_niveles=piezas_por_canal[grp],
        )

    # Un solo descargador con cache para toda la corrida: el feed de la Fed
    # sirve a dos canales y sin cache se baja dos veces.
    from noticia_oficial import descargar_con_cache, noticia_para_canal
    from suplemento_canal import cargar_historial

    _bajar = descargar_con_cache()
    _hist = cargar_historial()
    es_cierre = (slug_sesion in ("cierre_ny", "tarde_ny") or n_tanda == 3 or "cierre" in slug_sesion)
    suplementos, avisos_sup = escribir_suplementos(
        destino, resultado.get("excluidos") or [], grupos_activos, catalogo,
        buscar_noticia=lambda canal: noticia_para_canal(
            canal, ahora=ahora, historial=_hist, descargar=_bajar
        ),
        es_cierre=es_cierre,
    )

    return {
        "tanda": n_tanda,
        "sesion_slug": slug_sesion,
        "nombre_tanda": resultado["nombre_tanda"],
        "nombre_sesion": resultado.get("nombre_sesion", resultado["nombre_tanda"]),
        "foco": resultado.get("foco", ""),
        "hora_chile_tanda": resultado["hora_chile_tanda"],
        "hora_real": ahora.strftime("%H:%M"),
        "directorio": str(destino),
        "payloads": payloads,
        "problemas": problemas,
        "suplementos": suplementos,
        "avisos": resultado["avisos"] + avisos_macro + avisos_sup + (
            [f"barridos {len(barridos)} payload(s) de una corrida anterior: "
             + ", ".join(barridos)] if barridos else []
        ),
        "campos_por_escribir": list(CAMPOS_EDITORIALES),
    }


class PiezaSinMensajeError(RuntimeError):
    """Una imagen rendida se quedó sin su texto: saldría muda."""


def piezas_del_grupo(dir_grupo: Path) -> list[Any]:
    """Las piezas de un canal, en el orden en que deben salir.

    El orden lo da el prefijo numérico que escribe `preparar`: `0_` es el
    contexto macro y `1_`, `2_`… los activos. Es el orden canónico del proyecto,
    con la agenda del día arriba y los niveles debajo.

    Las copias sin prefijo (`contexto_macro.png`, `mensaje.txt`) quedan fuera a
    propósito: `rendir` las deja por comodidad, y contarlas como piezas mandaría
    la agenda dos veces al mismo canal.
    """
    from whatsapp_sender import Pieza

    piezas: list[Any] = []
    for png in sorted(dir_grupo.glob("*.png")):
        if not png.stem[:1].isdigit():
            continue                       # copia sin prefijo: no es una pieza

        # El contexto macro guarda su texto como `0_contexto_macro.txt`; los
        # activos, como `N_slug_mensaje.txt`.
        candidatos = [
            dir_grupo / f"{png.stem}_mensaje.txt",
            dir_grupo / f"{png.stem}.txt",
        ]
        txt = next((c for c in candidatos if c.exists()), None)
        if txt is None:
            raise PiezaSinMensajeError(
                f"{png.stem} tiene imagen pero no mensaje. Se detiene el despacho: "
                "una pieza muda llega al cliente sin decir qué mira."
            )
        piezas.append(Pieza(adjunto=png, mensaje=txt.read_text(encoding="utf-8").strip()))

    return piezas


def divergencia_editorial(crudos: dict[str, Any], precio_nuevo: float) -> str | None:
    """Motivo por el que el texto ya no describe el mercado, o `None`.

    Que el precio se mueva entre que se preparó la pieza y que sale es normal y
    no invalida nada. Lo que sí la invalida es que **cruce un nivel que el texto
    da por vigente**: un párrafo que dice "se apoya en el soporte" publicado
    cuando el soporte ya se perforó es peor que no publicar.
    """
    try:
        p0 = float(crudos["precio"])
        soporte = float(crudos["soporte"])
        resistencia = float(crudos["resistencia"])
    except (KeyError, TypeError, ValueError):
        return (
            "no se pudo comparar contra los precios de preparación: el payload no "
            "trae `_procedencia.crudos`. Se prepara de nuevo antes de despachar."
        )

    niveles = (
        ("el soporte", "perforó", soporte),
        ("la resistencia", "quebró", resistencia),
    )
    for nombre, verbo, nivel in niveles:
        antes = p0 - nivel
        ahora = precio_nuevo - nivel
        if antes * ahora < 0:
            return (
                f"el precio {verbo} {nombre} de {nivel:g}: pasó de {p0:g} a "
                f"{precio_nuevo:g} y el texto quedó describiendo otro mercado"
            )

    return None


def refrescar_payload(
    payload: dict[str, Any],
    ahora: datetime,
    h1: dict[str, Any],
    digits: int,
    cierres: dict[str, Any] | list[float],
) -> tuple[dict[str, Any], str | None]:
    """Vuelve a atar el payload al mercado de ahora, justo antes de rendirlo.

    Es lo que evita que la última pieza de una tanda llegue con el precio de
    hace veinte minutos: se refrescan las cifras y el sello de procedencia, y se
    devuelve el motivo si el movimiento invalidó el texto que ya está escrito.

    **Se toca lo que es dato, nunca lo editorial**: titular y párrafo son
    criterio de quien los escribió.
    """
    nuevo = json.loads(json.dumps(payload))          # copia honda

    precio = float(h1["price"])
    soporte = float(h1["s1"])
    resistencia = float(h1["r1"])

    motivo = divergencia_editorial(
        nuevo.get("_procedencia", {}).get("crudos", {}), precio
    )

    def fmt(valor: float) -> str:
        return formatear_precio(valor, digits)

    nuevo["precio_actual"] = fmt(precio)
    nuevo["soporte"] = fmt(soporte)
    nuevo["resistencia"] = fmt(resistencia)
    nuevo["impulso_adc_atr_valor"] = round(1.5 * float(h1["atr_14"]), digits)

    unidad = str(nuevo.get("vol_pct", "")).split(" ")[-1]
    nuevo["vol_pct"] = f"{fmt(nuevo['impulso_adc_atr_valor'])} {unidad}".strip()

    nuevo["fecha_hora"] = ahora.strftime("%d %b %Y · %H:%M").upper()
    nuevo["sello_datos"] = (
        f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}"
    )

    # El chip sigue a la lectura de ahora, y se lee del mercado, no del propio
    # payload: re-derivarlo del string `nuevo["sesgo"]` seria circular. Sale de
    # `direccion_tecnica`, **la misma funcion que uso el escaner** para elegir el
    # activo. Usar `h1["trend"]` habria parecido equivalente y no lo es: `trend`
    # compara contra la EMA 100 y `direccion_tecnica` contra la EMA 50.
    if "ema_50" not in h1:
        return nuevo, motivo or (
            "el analizador no devolvio la EMA 50 de H1, asi que la direccion de "
            "la pieza no se puede confirmar contra el mercado de ahora"
        )
    tecnica = sc.direccion_tecnica(h1)
    sesgo_preparado = str(payload.get("sesgo", ""))
    if payload.get("tipo_pieza") == "recap":
        # El recap es un balance de la jornada sin direccion afirmada: su chip
        # queda en Lateral aunque las medias de ahora apunten a un lado.
        nuevo["sesgo"], nuevo["tag_riesgo"] = "Lateral", "BALANCE"
    else:
        nuevo["sesgo"] = direccion_publicada(tecnica)
        nuevo["tag_riesgo"] = nuevo["sesgo"].upper()
    # Si la lectura dio vuelta entre preparar y despachar, el titular y el
    # parrafo quedaron escritos para la direccion contraria: un parrafo alcista
    # bajo un chip bajista se contradice solo. La pieza no sale.
    if motivo is None and sesgo_preparado in ("Alcista", "Bajista") and sesgo_preparado != nuevo["sesgo"]:
        motivo = (
            f"la lectura tecnica paso de {sesgo_preparado} a {nuevo['sesgo']} y el "
            "texto quedo escrito para la direccion contraria"
        )

    nuevo["_procedencia"].setdefault("crudos", {})
    nuevo["_procedencia"]["crudos"] = {
        "precio": precio, "soporte": soporte, "resistencia": resistencia,
    }

    # El gráfico se redibuja con la serie nueva y sus niveles al día.
    serie = cierres if isinstance(cierres, list) else cierres.get("serie", [])

    # El refresco vuelve a juntar las mismas dos lecturas del terminal que junta
    # `construir_payload`, y con el mismo acoplamiento ciego: indice de una fuente
    # y precio de la otra. Si llegan desacopladas la pieza no sale, que es lo que
    # ya hace ante una divergencia de precio. Se comprueba **despues** de las otras
    # divergencias para no tapar un motivo de mercado con uno de datos: que el
    # precio haya perforado el soporte le interesa mas al director.
    if motivo is None:
        motivo = incoherencia_del_payload(
            {
                "ticker": nuevo.get("_procedencia", {}).get("ticker", nuevo.get("activo", "?")),
                "precio": precio,
                "soporte": soporte,
                "resistencia": resistencia,
                "atr_h1": h1.get("atr_14"),
            },
            serie,
        )
    recorrido = nuevo.get("recorrido", {})
    recorrido["serie"] = serie
    recorrido["marcadores"] = [{
        "indice": max(len(serie) - 1, 0),
        "precio": precio,
        "clase": "actual",
        "etiqueta": fmt(precio),
        "rol": "AHORA",
    }]
    recorrido["niveles"] = [
        {"precio": resistencia, "clase": "resistencia",
         "etiqueta": fmt(resistencia), "rol": "RESISTENCIA"},
        {"precio": soporte, "clase": "soporte",
         "etiqueta": fmt(soporte), "rol": "SOPORTE"},
    ]
    nuevo["recorrido"] = recorrido

    return nuevo, motivo


def exigir_texto_editorial(payloads: list[tuple[str, dict[str, Any]]]) -> None:
    """Detiene el render si a alguna pieza le falta un campo editorial o si infringe el linter de estilo.

    Fuente unica del freno, y por eso recibe pares `(nombre, payload)` en vez
    de leer el disco: las dos rutas de render llegan al payload por caminos
    distintos. `rendir` lo tenia y el despacho no, que es justo el que llega al
    cliente; `_refrescar_y_rendir` hacia `pop("_pendiente_editorial")` y
    descartaba la marca que existe para frenar. Dos caminos al mismo resultado
    con el freno en uno solo es el defecto recurrente del repo.
    """
    sin_escribir: list[str] = []
    for nombre, payload in payloads:
        faltan = [c for c in CAMPOS_EDITORIALES if not str(payload.get(c, "")).strip()]
        if faltan:
            sin_escribir.append(f"{nombre}: falta {', '.join(faltan)}")

    if sin_escribir:
        raise SystemExit(
            "Hay piezas sin texto editorial. Una pieza a medias que sale sin avisar "
            "llega al cliente, asi que el render se detiene:\n  "
            + "\n  ".join(sin_escribir)
        )

    # Segundo freno: Linter editorial estricto (guiones largos, voseo, placeholders)
    try:
        from validador_editorial import validar_payload_editorial

        errores_linter: list[str] = []
        for nombre, payload in payloads:
            errores_linter.extend(validar_payload_editorial(payload, identificador=nombre))
        if errores_linter:
            raise SystemExit(
                "Infracción en el linter editorial (estilo, voseo, guiones largos o placeholders):\n  "
                + "\n  ".join(errores_linter)
            )
    except ImportError:
        pass


def rendir(directorio: Path) -> dict[str, Any]:
    """Valida lo editorial, produce las piezas en horizontal y actualiza los mensajes modulares dentro de cada grupo."""
    from story_grafico import enriquecer
    from story_render import render_story

    archivos = sorted(p for p in directorio.rglob("*.json") if not p.name.startswith("_") and not p.name.startswith("0_contexto_macro"))
    if not archivos:
        raise SystemExit(f"No hay payloads de alerta en {directorio}")

    exigir_texto_editorial([
        (
            str(archivo.relative_to(directorio))
            if archivo.is_relative_to(directorio)
            else archivo.name,
            json.loads(archivo.read_text(encoding="utf-8")),
        )
        for archivo in archivos
    ])

    ahora = datetime.now(tz=SANTIAGO)
    generadas: list[dict[str, Any]] = []
    resumen_piezas: list[dict[str, Any]] = []

    for archivo in archivos:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        procedencia = payload.pop("_procedencia", {})
        payload.pop("_pendiente_editorial", None)

        ticker = procedencia.get("ticker", payload.get("activo_slug"))
        nombre = payload.get("rotulo_activo", payload.get("activo", ticker))
        soporte_val = procedencia.get("crudos", {}).get("soporte")
        if soporte_val is None and "soporte" in payload and payload["soporte"]:
            try:
                s_sop = str(payload["soporte"]).strip()
                if "," in s_sop:
                    s_sop = s_sop.replace(".", "").replace(",", ".")
                soporte_val = float(s_sop)
            except (ValueError, TypeError):
                soporte_val = None

        resistencia_val = procedencia.get("crudos", {}).get("resistencia")
        if resistencia_val is None and "resistencia" in payload and payload["resistencia"]:
            try:
                s_res = str(payload["resistencia"]).strip()
                if "," in s_res:
                    s_res = s_res.replace(".", "").replace(",", ".")
                resistencia_val = float(s_res)
            except (ValueError, TypeError):
                resistencia_val = None

        # Alerta de mercado: estándar TradingView 300 DPI de alta fidelidad
        formato = "horizontal"
        destino_local_png = archivo.parent / f"{archivo.stem}.png"

        try:
            from tradingview_grafico import generar_grafico_tv
            generar_grafico_tv(
                ticker=ticker,
                nombre=nombre,
                destino=destino_local_png,
                timeframe=TIMEFRAME_GRAFICO,
                n_velas=60,
                soporte=soporte_val,
                resistencia=resistencia_val,
            )
        except Exception:
            # Fallback a Story render tradicional si MT5 o Chromium no están en este entorno
            payload_enriquecido = enriquecer(json.loads(json.dumps(payload)))
            render_story(payload_enriquecido, PLANTILLA, destino_local_png, formato=formato)

        # Generar mensaje final para WhatsApp dentro de la carpeta del grupo
        msg_final = construir_mensaje_alerta(payload)
        (archivo.parent / "mensaje.txt").write_text(msg_final, encoding="utf-8")
        (archivo.parent / f"{archivo.stem}_mensaje.txt").write_text(msg_final, encoding="utf-8")

        grupo_nombre = archivo.parent.name if archivo.parent != directorio else "general"
        generadas.append({
            "ticker": procedencia.get("ticker", payload["activo_slug"]),
            "grupo": grupo_nombre,
            "formato": formato,
            "archivo": str(destino_local_png),
            "archivo_local": str(destino_local_png),
        })
        resumen_piezas.append({
            "activo": payload["activo"],
            "titular": payload.get("titular", ""),
            "sesgo": payload.get("sesgo", ""),
            "grupo": grupo_nombre,
        })

    # Mensaje índice general en la raíz de la tanda
    lineas_indice = [
        f"📊 *ALERTA DE MERCADO · SESIÓN MULTIACTIVO* · {ahora.strftime('%H:%M')} hrs",
        "━━━━━━━━━━━━━━━━━━━",
        f"🎯 Lo que estamos mirando ahora en {len(resumen_piezas)} activo(s):",
        "",
    ]
    for idx, item in enumerate(resumen_piezas, 1):
        num_emoji = f"{idx}️⃣"
        lineas_indice.append(f"{num_emoji} *{item['activo']}* → {item['titular'] or item['sesgo']}")
    lineas_indice.extend([
        "━━━━━━━━━━━━━━━━━━━",
        # Derivada del marco real de las piezas, no escrita a mano. La constante
        # que habia aca decia "intradía" pase lo que pase, y era el tercer lugar
        # del repo donde vivia la misma tabla de etiquetas.
        f"⏱️ Temporalidad: {MARCOS_CANONICOS[TIMEFRAME_GRAFICO][1]}",
        "━━━━━━━━━━━━━━━━━━━",
        "Cada imagen y mensaje detallado han sido modularizados en su carpeta de grupo correspondiente.",
    ])
    (directorio / "mensaje_indice.txt").write_text("\n".join(lineas_indice), encoding="utf-8")

    return {"directorio": str(directorio), "imagenes": generadas}


def falta_metatrader5() -> bool:
    """Si el paquete no está, el refresco previo al envío no puede ocurrir.

    Se pregunta por el *spec* y no con un `try: import`, porque importar MT5 tiene
    efecto (engancha el terminal) y acá solo queremos saber si existe.

    Vive aparte para que `despachar` lo consulte UNA vez por tanda. El paquete
    ausente no es el problema de una pieza como lo es un fallo de datos: significa
    que el guardia de divergencia no corre para **ninguna**, y repetir ese aviso
    por activo lo disfraza de incidencia puntual.
    """
    return importlib.util.find_spec("MetaTrader5") is None


def _refrescar_y_rendir(dir_grupo: Path) -> list[str]:
    """Vuelve a leer el mercado, redibuja las piezas de precio y reescribe sus textos.

    Solo toca las piezas de activo (`1_`, `2_`…). El contexto macro (`0_`) es la
    agenda del día: no decae por minuto y su fuente es el calendario, no una
    cotización.

    Sin MetaTrader5 valida el texto editorial y no toca el mercado. Intentar el
    refresco activo por activo solo produce el mismo `ModuleNotFoundError` repetido,
    disfrazado de fallo de datos; las piezas salen con lo que dejó `--rendir`, que es
    lo que el aviso de `despachar` advierte una vez por tanda.
    """
    from market_data_mcp.analisis import analizar_activo
    from story_grafico import enriquecer
    from story_render import render_story

    piezas = [
        p for p in sorted(dir_grupo.glob("*.json"))
        if not p.stem.startswith("0_") and not p.stem.startswith("_")
    ]
    # Mismo freno que `rendir`, y por eso antes de leer el mercado: el payload
    # en disco ya dice lo que falta. El contexto macro (`0_`) queda fuera de la
    # lista porque su texto no lo escribe el comando.
    exigir_texto_editorial([
        (p.name, json.loads(p.read_text(encoding="utf-8"))) for p in piezas
    ])

    if falta_metatrader5():
        return []

    catalogo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}
    ahora = datetime.now(tz=SANTIAGO)
    avisos: list[str] = []

    for archivo in piezas:

        payload = json.loads(archivo.read_text(encoding="utf-8"))
        ticker = payload.get("_procedencia", {}).get("ticker")
        activo = catalogo.get(ticker)
        if not ticker or not activo:
            avisos.append(f"{archivo.stem}: sin ticker en la procedencia, se despacha tal cual")
            continue

        try:
            h1 = analizar_activo(ticker, "H1")
            cierres = _serie_para(ticker)
        except Exception as exc:  # noqa: BLE001
            avisos.append(
                f"{ticker}: no se pudo refrescar ({exc}). Sale con los datos de la "
                "preparación, que ya no son de ahora."
            )
            continue

        nuevo, motivo = refrescar_payload(
            payload, ahora=ahora, h1=h1, digits=activo["digits"], cierres=cierres
        )
        if motivo:
            avisos.append(f"⚠️ {ticker} NO se despacha: {motivo}")
            archivo.rename(archivo.with_suffix(".json.divergente"))
            png = dir_grupo / f"{archivo.stem}.png"
            if png.exists():
                png.rename(png.with_suffix(".png.divergente"))
            continue

        archivo.write_text(json.dumps(nuevo, ensure_ascii=False, indent=2), encoding="utf-8")

        soporte_val = None
        resistencia_val = None
        try:
            if "soporte" in nuevo and nuevo["soporte"]:
                soporte_val = float(str(nuevo["soporte"]).replace(".", "").replace(",", "."))
            if "resistencia" in nuevo and nuevo["resistencia"]:
                resistencia_val = float(str(nuevo["resistencia"]).replace(".", "").replace(",", "."))
        except (ValueError, TypeError):
            pass

        destino_local_png = dir_grupo / f"{archivo.stem}.png"
        try:
            from tradingview_grafico import generar_grafico_tv
            generar_grafico_tv(
                ticker=ticker,
                nombre=nuevo.get("rotulo_activo", nuevo.get("activo", ticker)),
                destino=destino_local_png,
                timeframe=TIMEFRAME_GRAFICO,
                n_velas=60,
                soporte=soporte_val,
                resistencia=resistencia_val,
            )
        except Exception:
            pieza = json.loads(json.dumps(nuevo))
            pieza.pop("_procedencia", None)
            pieza.pop("_pendiente_editorial", None)
            render_story(enriquecer(pieza), PLANTILLA, destino_local_png, formato="horizontal")

        msg_final = construir_mensaje_alerta(nuevo)
        (dir_grupo / f"{archivo.stem}_mensaje.txt").write_text(msg_final, encoding="utf-8")
        (dir_grupo / "mensaje.txt").write_text(msg_final, encoding="utf-8")
        avisos.append(f"✅ {ticker} refrescado a las {ahora.strftime('%H:%M')}")

    return avisos


def _refrescar_y_rendir_avisos(dir_grupo: Path, sin_mt5: bool) -> tuple[bool, list[str]]:
    """Refresca y rinde una tanda de Avisos con su propio pipeline. `(sale, avisos)`.

    Una tanda de Avisos es un carrusel, no piezas sueltas: la portada, la
    lectura y el resultado citan el mismo mercado, así que si el refresco dice
    que el texto quedó escrito para otro mercado, o si algún freno de
    `--rendir` salta (texto sin escribir, cifra sin respaldo, datos de más de
    2 h), **no sale ninguna lámina** (spec 3.7.3). Las láminas se rinden con su
    plantilla (`_plantilla`), no con la de la alerta (spec 3.7.1).

    Un refresco que falla no deja pasar precios viejos: el freno de frescura de
    `rendir_tanda` detiene la tanda si la lectura de la preparación ya tiene más
    de 2 h (spec 3.7.4).
    """
    import pipeline_avisos as pa

    ahora = datetime.now(tz=SANTIAGO)
    meta = pa.leer_meta(dir_grupo)
    avisos: list[str] = []
    lleva_mercado = bool(meta.get("activo")) or meta.get("formato") == "resultado"
    if lleva_mercado and sin_mt5:
        avisos.append("sin MetaTrader5 no se relee el mercado: vale la lectura de la preparación si tiene menos de 2 h")
    else:
        try:
            avisos.extend(pa.refrescar_tanda(dir_grupo, ahora))
        except pa.LecturaFallidaError as exc:
            avisos.append(f"el refresco falló ({exc}): vale la lectura de la preparación si tiene menos de 2 h")
        except SystemExit as exc:
            return False, avisos + [f"⚠️ el carrusel de Avisos NO se despacha: {exc}"]
    try:
        pa.rendir_tanda(dir_grupo, ahora)
    except SystemExit as exc:
        return False, avisos + [f"⚠️ el carrusel de Avisos NO se despacha: {exc}"]
    return True, avisos


def despachar(
    directorio: Path,
    desde: int = 1,
    dry_run: bool = False,
    headless: bool = True,
    pruebas: bool = False,
) -> dict[str, Any]:
    """Rinde y despacha canal por canal, en orden y sin dejar envejecer las piezas.

    Cada pieza sale en **su propia acción**, con su espera de cadencia y su unidad
    de cupo. Esta docstring decía lo contrario hasta el 2026-09-04: describía el
    despacho por lote que **se revirtió el 2026-09-03**, mientras el código de más
    abajo hacía una pieza por acción. El motivo del cambio está en
    `whatsapp_sender.enviar_lote`: el pie del editor de medios tope en 1.024
    caracteres y la única forma de superarlo es escribir el texto en el cuadro de
    conversación antes de adjuntar, lo que solo llena el pie de UNA imagen.

    Se corrige porque una docstring que describe un diseño ya descartado es
    justamente lo que hace que alguien lo "restaure" creyendo que arregla algo.

    Y cada canal se rinde **justo antes** de despacharse, no al principio de la
    tanda: así el precio de la última pieza tiene minutos y no media hora. El
    render cabe entero dentro de la espera de cadencia, así que no cuesta tiempo.

    Lo ya entregado se salta leyendo `data/historial_despachos.json`, así que una
    reanudación no repite piezas. `--desde N` queda como control manual.
    """
    from whatsapp_sender import WhatsAppSender, huella
    from bitacora_despachos import cargar as cargar_bitacora
    from bitacora_despachos import registrar as anotar_despacho
    from bitacora_despachos import ya_despachada

    grupos = sorted(d for d in directorio.iterdir() if d.is_dir())
    if not grupos:
        raise SystemExit(f"No hay carpetas de grupo en {directorio}")

    sender = WhatsAppSender(headless=headless)
    destino_fijo = sender.config.destino_de_pruebas if pruebas else None
    if pruebas:
        print(f"\n[MODO PRUEBAS] Destino fijo para todos los canales: {destino_fijo}\n", flush=True)

    resultados: list[dict[str, Any]] = []

    # La bitacora es la unidad correcta para retomar. `--desde N` cuenta CANALES,
    # y desde el 2026-09-03 el envio cuenta PIEZAS: retomar un canal que fallo en
    # su segunda de tres reenviaba la primera. Se conserva `--desde` como control
    # manual del director, pero lo normal es que ya no haga falta.
    tanda = directorio.name
    bitacora = cargar_bitacora()

    # Se pregunta UNA vez, antes del primer canal. Sin el paquete no se refresca
    # ninguna pieza y el guardia de divergencia no corre en toda la tanda: eso hay
    # que decirlo como condición del despacho, no como un tropiezo por activo.
    sin_mt5 = falta_metatrader5()
    if sin_mt5:
        print(
            "\n[SIN REFRESCO] MetaTrader5 no está instalado en este entorno.\n"
            "    Las piezas salen con los datos de la preparación y NO se comprueba\n"
            "    si el precio invalidó su texto: ninguna se va a detener por divergente.\n"
            "    Para despachar con el freno activo, volvé a invocar con:\n"
            "      uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py"
            " --despachar <tanda>",
            flush=True,
        )

    for i, dir_grupo in enumerate(grupos, 1):
        if i < desde:
            print(f"[{i}/{len(grupos)}] {dir_grupo.name}: omitido (--desde {desde})", flush=True)
            resultados.append({"grupo": dir_grupo.name, "status": "omitido"})
            continue

        canal = dir_grupo.name
        destinatario = destino_fijo if pruebas else canal
        print(f"\n[{i}/{len(grupos)}] {canal}" + (f" -> destino: {destinatario}" if pruebas else ""), flush=True)
        es_avisos = (dir_grupo / "_avisos.json").exists()
        if es_avisos:
            sale, avisos_canal = _refrescar_y_rendir_avisos(dir_grupo, sin_mt5)
            for aviso in avisos_canal:
                print(f"    {aviso}", flush=True)
            if not sale:
                resultados.append({"grupo": canal, "status": "frenado"})
                continue
        else:
            for aviso in _refrescar_y_rendir(dir_grupo):
                print(f"    {aviso}", flush=True)

        piezas = piezas_del_grupo(dir_grupo)
        if not piezas:
            # **Un canal sin imágenes puede tener suplemento.** El suplemento es
            # solo texto por decisión de fase: se mide si el canal engancha antes
            # de pedirle una plantilla al brand kit. `piezas_del_grupo` recorre
            # los PNG, así que sin esta rama el suplemento se escribía a disco y
            # el despacho lo saltaba en silencio.
            suplemento = dir_grupo / "0_suplemento.txt"
            if suplemento.exists():
                algo_despachado = False
                texto = suplemento.read_text(encoding="utf-8").strip()
                if not pruebas and ya_despachada(bitacora, tanda, canal, "0_suplemento"):
                    print("    suplemento ya despachado segun la bitacora: se omite", flush=True)
                else:
                    print(f"    suplemento de {len(texto)} caracteres, sin adjunto...", flush=True)
                    res = sender.enviar(
                        destinatario, mensaje=texto, dry_run=dry_run
                    )
                    if not dry_run and not pruebas:
                        anotar_despacho(
                            tanda, canal, "0_suplemento",
                            huella=huella(texto),
                        )
                    # `piezas` va explicito: el suplemento ES una pieza entregada, y sin
                    # el campo el resumen final imprimia "enviado  pieza(s)" sin numero
                    # justo en los canales que solo llevan suplemento.
                    resultados.append(
                        {"grupo": canal, "suplemento": True, "piezas": 1, **res}
                    )
                    algo_despachado = True

                encuesta_file = dir_grupo / "_encuesta.json"
                if encuesta_file.exists():
                    try:
                        datos_enc = json.loads(encuesta_file.read_text(encoding="utf-8"))
                    except Exception as e:  # noqa: BLE001
                        print(f"    error al leer {encuesta_file.name}: {e}", flush=True)
                    else:
                        if not pruebas and ya_despachada(bitacora, tanda, canal, "0_encuesta"):
                            print("    encuesta de cierre ya despachada segun bitacora: se omite", flush=True)
                        else:
                            print(f"    despachando encuesta de cierre: '{datos_enc.get('pregunta')}'...", flush=True)
                            res_enc = sender.enviar_encuesta(
                                destinatario,
                                pregunta=datos_enc["pregunta"],
                                opciones=datos_enc["opciones"],
                                permitir_multiples=datos_enc.get("permitir_multiples", False),
                                forzar=True,
                                dry_run=dry_run,
                            )
                            if not dry_run and not pruebas:
                                anotar_despacho(
                                    tanda, canal, "0_encuesta",
                                    huella=huella(datos_enc["pregunta"]),
                                )
                            resultados.append({"grupo": canal, "encuesta": True, **res_enc})
                            algo_despachado = True

                if not algo_despachado:
                    resultados.append({"grupo": canal, "status": "ya_despachado"})

                # La cadencia no se maneja aca: `enviar` reserva su turno y
                # espera por su cuenta, igual que el resto de las piezas.
                continue

            print("    sin piezas: se omite", flush=True)
            resultados.append({"grupo": canal, "status": "vacio"})
            continue

        if pruebas:
            pendientes = piezas
        else:
            pendientes = [
                pz for pz in piezas
                if not ya_despachada(bitacora, tanda, canal, Path(pz.adjunto).stem)
            ]
        if not pendientes:
            print("    todas sus piezas ya salieron segun la bitacora: se omite", flush=True)
            resultados.append({"grupo": canal, "status": "ya_despachado",
                               "piezas": len(piezas)})
            continue
        if len(pendientes) < len(piezas):
            print(
                f"    {len(piezas) - len(pendientes)} pieza(s) ya despachada(s): "
                "se retoma en la que falta", flush=True
            )
        if es_avisos and not dry_run:
            restante = sender.cupo_restante()
            if len(pendientes) > restante:
                print(
                    f"    ⚠️ el carrusel de Avisos NO se despacha: lleva {len(pendientes)} "
                    f"pieza(s) y al cupo de hoy le quedan {restante}. Un carrusel a medias es "
                    "peor que ninguno.", flush=True,
                )
                resultados.append({"grupo": canal, "status": "sin_cupo", "piezas": len(pendientes)})
                continue

        def anotar(pieza: Any, _canal: str = canal) -> None:
            if pruebas:
                return
            # La huella sale de la MISMA funcion que compara el guardia de entrega
            # contra el DOM. Una segunda implementacion seria otro de los relojes
            # duplicados que ya costaron caro en este repo.
            anotar_despacho(
                tanda, _canal, Path(pieza.adjunto).stem,
                huella=huella(pieza.mensaje or ""),
            )

        print(f"    despachando {len(pendientes)} pieza(s), una por acción a '{destinatario}'...", flush=True)
        res = sender.enviar_lote(destinatario, pendientes, dry_run=dry_run, al_entregar=anotar)
        resultados.append({"grupo": canal, **res})

        # Despacho de encuesta interactiva si el canal cuenta con una generada
        encuesta_file = dir_grupo / "_encuesta.json"
        if encuesta_file.exists():
            try:
                datos_enc = json.loads(encuesta_file.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                print(f"    error al leer {encuesta_file.name}: {e}", flush=True)
            else:
                if not pruebas and ya_despachada(bitacora, tanda, canal, "0_encuesta"):
                    print("    encuesta de cierre ya despachada segun bitacora: se omite", flush=True)
                else:
                    print(f"    despachando encuesta de cierre a '{destinatario}': '{datos_enc.get('pregunta')}'...", flush=True)
                    res_enc = sender.enviar_encuesta(
                        destinatario,
                        pregunta=datos_enc["pregunta"],
                        opciones=datos_enc["opciones"],
                        permitir_multiples=datos_enc.get("permitir_multiples", False),
                        forzar=True,
                        dry_run=dry_run,
                    )
                    if not dry_run and not pruebas:
                        anotar_despacho(
                            tanda, canal, "0_encuesta",
                            huella=huella(datos_enc["pregunta"]),
                        )
                    resultados.append({"grupo": canal, "encuesta": True, **res_enc})

    return {"directorio": str(directorio), "grupos": resultados}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carrusel responsivo: Stories de alerta segun sesion y hora real")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--preparar", action="store_true",
                       help="corre el escaner y deja los payloads con lo editorial en blanco")
    grupo.add_argument("--rendir", type=Path, metavar="DIR",
                       help="rinde los payloads ya escritos de ese directorio")
    grupo.add_argument("--despachar", type=Path, metavar="DIR",
                       help="rinde y envia canal por canal: un lote por canal, refrescado justo antes de salir")
    parser.add_argument("--desde", type=int, default=1, metavar="N",
                        help="retoma el despacho desde el canal N (1-based), para no duplicar lo ya enviado")
    parser.add_argument("--dry-run", action="store_true",
                        help="con --despachar: refresca y rinde, pero no envia nada")
    parser.add_argument("--visible", action="store_false", dest="headless",
                        help="con --despachar: muestra el navegador durante el envio")
    parser.add_argument("--tanda", type=int, choices=sorted(sc.TANDAS),
                        help="fuerza una tanda especifica (por defecto detecta la sesion y hora real)")
    parser.add_argument("--top", type=int, default=3,
                        help="tope de piezas (default 3: WhatsApp muestra 3 adjuntos sin el boton +2)")
    parser.add_argument("--grupo", type=str, default=None,
                        help="filtra exclusivamente a un grupo de WhatsApp (forex, commodities, indices, acciones, crypto)")
    parser.add_argument("--matriz", action="store_true",
                        help="cobertura total: selecciona el Top 1 de cada uno de los 5 grupos de mercado")
    parser.add_argument("--todos", action="store_true",
                        help="incluye activos sin imagen (su pieza no se va a poder rendir)")
    parser.add_argument("--forzar", action="store_true",
                        help="ignora gate de agotamiento para evaluar activos en sesiones avanzadas")
    parser.add_argument("--pruebas", action="store_true",
                        help="con --despachar: envia al banco de pruebas interno (GI · Banco de Pruebas) en vez de a los canales oficiales")
    args = parser.parse_args(argv)

    if args.grupo:
        try:
            args.grupo = resolver_grupo_solicitado(args.grupo)
        except GrupoDesconocidoError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if args.preparar:
        if args.top > 3 and not args.matriz:
            print(
                f"AVISO: --top {args.top} rompe la regla de cero spam. WhatsApp muestra "
                "3 adjuntos con previsualizacion; del cuarto en adelante aparece el boton +2.",
                file=sys.stderr,
            )
        res = preparar(
            tanda=args.tanda,
            top=args.top,
            solo_renderizables=not args.todos,
            grupo=args.grupo,
            modo_matriz=args.matriz,
            forzar=args.forzar,
        )
        nombre = res.get("nombre_sesion", res["nombre_tanda"])
        print(f"\nSESIÓN: {nombre} ({res['hora_real']} hrs hora Chile)")
        print(f"Directorio: {res['directorio']}")
        print(f"\nPAYLOADS ({len(res['payloads'])})")
        for p in res["payloads"]:
            grupo_info = f"[{p.get('grupo', '')}]" if p.get("grupo") else ""
            print(f"  {p['ticker']:<12} {grupo_info:<35} score {p['score']:>3}/100  {Path(p['archivo']).name}")
        if res["problemas"]:
            print("\nPROBLEMAS")
            for p in res["problemas"]:
                print(f"  - {p}")
        if res["avisos"]:
            print("\nAVISOS DEL ESCANER")
            for a in res["avisos"]:
                print(f"  - {a}")
        print(f"\nFalta escribir en cada payload: {', '.join(res['campos_por_escribir'])}")
        print(f"Despues: uv run --extra stories python scripts/pipeline_carrusel.py --rendir {res['directorio']}")
        return 0

    if args.despachar:
        res = despachar(
            args.despachar,
            desde=args.desde,
            dry_run=args.dry_run,
            headless=args.headless,
            pruebas=args.pruebas,
        )
        print("\nRESUMEN DEL DESPACHO")
        for g in res["grupos"]:
            piezas = g.get("piezas", 0)
            print(f"  {g['grupo']:<35} {g.get('status', ''):<10} {piezas} pieza(s)")
        return 0

    res = rendir(args.rendir)
    print(f"\n{len(res['imagenes'])} imagen(es) generadas")
    for img in res["imagenes"]:
        grupo_str = f"[{img.get('grupo', '')}]" if img.get("grupo") else ""
        print(f"  {img['ticker']:<12} {grupo_str:<35} {img['formato']:<11} {img['archivo_local']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
