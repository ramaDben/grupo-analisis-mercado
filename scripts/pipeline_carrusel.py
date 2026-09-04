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
"""

from __future__ import annotations

import argparse
import json
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


# ─────────────────────────────────────────────────────────────────────────────
# Las dos gramáticas de vigencia
# ─────────────────────────────────────────────────────────────────────────────
_DIRECCION_TECNICA_A_PLAYBOOK = {"ALCISTA": "LARGO", "BAJISTA": "CORTO"}


def vigencia_publicable(
    vigencia: dict[str, Any] | None, direccion_tecnica: str
) -> tuple[dict[str, Any] | None, str | None]:
    """La vigencia que se puede publicar junto a esta lectura, y el motivo si no.

    El único filtro es la contradicción de dirección. La lectura técnica de la
    pieza sale de `direccion_tecnica` (medias y estructura en H1) y la del sesgo
    sale del signo del score macro. Casi siempre coinciden, y cuando no, el gate
    del Playbook del escáner ya suele bloquear el activo. Pero "suele" no
    alcanza: si las dos frases salieran en el mismo mensaje, el cliente leería
    "fuerza compradora" y dos líneas más abajo "sesgo bajista vigente hasta X".

    Ante esa contradicción se calla la vigencia, no la lectura técnica: la pieza
    del carrusel es de niveles, y el sesgo es el añadido. Callarlo cuesta una
    línea de información; publicarlo cuesta la credibilidad del mensaje entero.
    El motivo queda en la procedencia para que la omisión sea auditable en vez
    de invisible.
    """
    if not vigencia:
        return None, None

    esperada = _DIRECCION_TECNICA_A_PLAYBOOK.get(direccion_tecnica)
    del_sesgo = vigencia.get("direccion")
    if del_sesgo and esperada and del_sesgo != esperada:
        return None, (
            f"la vigencia se omite: el sesgo del Playbook va {del_sesgo} y "
            f"contradice la lectura técnica {direccion_tecnica} de esta pieza"
        )
    return vigencia, None


def direccion_publicada(
    direccion_tecnica: str,
    vigencia: dict[str, Any] | None,
    omitida: str | None,
) -> str:
    """La dirección que muestra el chip de la pieza: `Alcista`, `Bajista` o `Lateral`.

    **El chip mostraba la lectura técnica siempre, y eso lo hacía contradecir al
    Playbook en su propia pieza**: el 2026-09-03 una alerta salió con `▲ ALCISTA`
    en verde justo encima del aviso de que el sesgo alcista había quedado
    invalidado. Un cliente lee esa contradicción en 30 segundos, que es todo el
    tiempo que el proyecto se da para explicarse.

    Decisión del director: **cuando el Playbook opina, manda el Playbook**; la
    lectura técnica queda para los 33 activos del catálogo que no tienen ficha,
    que son la mayoría del universo.

    Los tres casos en que no se afirma dirección alguna:

    - **Sesgo invalidado**: el precio perdió su borde. Afirmar la dirección que
      acaba de caer es decir lo contrario de lo que pasa.
    - **Rango** (`NIVEL_OPUESTO_CANAL`): score cero, no hay dirección que exista.
    - **Contradicción**: el score macro y las medias apuntan al revés. La
      vigencia ya se omitía; el chip seguía afirmando igual, y es justo cuando
      las dos capas discrepan que no hay que afirmar.

    `Lateral` no necesitó nada visual nuevo: la plantilla ya tenía
    `tag-sesgo--lateral` con su flecha y color de texto, y el `body` sin clase de
    sesgo deja el cromo en el acento de marca. Es la regla de color del proyecto
    aplicándose sola: el cromo no opina.
    """
    if omitida:
        return "Lateral"
    if not vigencia:
        return "Alcista" if direccion_tecnica == "ALCISTA" else "Bajista"
    if not vigencia.get("vigente"):
        return "Lateral"
    if vigencia.get("gramatica") == "RANGO":
        return "Lateral"
    return "Alcista" if vigencia.get("direccion") == "LARGO" else "Bajista"


def formatear_vigencia(
    vigencia: dict[str, Any] | None, fmt: Callable[[float], str]
) -> dict[str, Any] | None:
    """La vigencia con sus cifras en notación chilena, lista para el mensaje.

    Los números crudos viajan aparte, en `_procedencia`: el despacho necesita
    comparar el precio contra el nivel, y "933,440" no se compara con un float.
    """
    if not vigencia:
        return None

    formateada = {
        "gramatica": vigencia["gramatica"],
        "direccion": vigencia.get("direccion"),
        "vigente": bool(vigencia.get("vigente")),
        "nivel": None,
        "borde_inferior": None,
        "borde_superior": None,
    }
    if vigencia.get("nivel") is not None:
        formateada["nivel"] = fmt(float(vigencia["nivel"]))
    if vigencia.get("borde_inferior") is not None:
        formateada["borde_inferior"] = fmt(float(vigencia["borde_inferior"]))
    if vigencia.get("borde_superior") is not None:
        formateada["borde_superior"] = fmt(float(vigencia["borde_superior"]))

    # Trazabilidad, no texto de cliente: de dónde salió el nivel. "Chandelier"
    # es jerga y no aparece en el mensaje, pero sin esto la revisión del payload
    # no puede reconstruir por qué el borde está donde está.
    if vigencia["gramatica"] == "NIVEL" and vigencia.get("multiplo_atr"):
        mult = f"{float(vigencia['multiplo_atr']):.1f}".replace(".", ",")
        formateada["detalle"] = (
            f"Chandelier {vigencia.get('lookback') or '?'} velas × {mult} ATR H1"
        )
    return formateada


def bloque_vigencia(vigencia: dict[str, Any] | None) -> list[str]:
    """Las líneas del mensaje que dicen hasta dónde sigue vigente el sesgo.

    Dos gramáticas, porque son dos lecturas:

    - `NIVEL` (posición sostenida): hay dirección, y un solo borde la sostiene.
    - `RANGO` (score cero): no hay dirección, hay un canal con dos bordes.

    Y un tercer caso que no es una gramática sino su ausencia: sin vigencia el
    bloque no sale. El cierre canónico de tres escenarios va igual, así que el
    mensaje nunca queda sin lectura práctica.
    """
    if not vigencia:
        return []

    if vigencia["gramatica"] == "RANGO":
        inferior, superior = vigencia.get("borde_inferior"), vigencia.get("borde_superior")
        if not inferior or not superior:
            return []
        if vigencia.get("vigente"):
            return [
                f"🟡 *Sin sesgo direccional: el activo rota entre {inferior} y {superior}*",
                "Mientras se mueva dentro de ese rango no hay tendencia que seguir. "
                "La lectura vale hasta que salga por uno de los dos bordes.",
                "━━━━━━━━━━━━━━━━━━━",
            ]
        return [
            f"⚠️ *El activo dejó el rango de {inferior} a {superior}*",
            "La lectura de canal deja de estar vigente. Conviene esperar el nuevo "
            "marco de precios antes de volver a leerlo.",
            "━━━━━━━━━━━━━━━━━━━",
        ]

    nivel = vigencia.get("nivel")
    if not nivel:
        return []
    alcista = vigencia.get("direccion") == "LARGO"
    palabra = "alcista" if alcista else "bajista"

    if vigencia.get("vigente"):
        lado_bien = "Sobre" if alcista else "Bajo"
        lado_mal = "Bajo" if alcista else "Sobre"
        return [
            f"🎯 *El sesgo {palabra} sigue vigente hasta {nivel}*",
            f"{lado_bien} ese nivel la lectura se mantiene. {lado_mal} {nivel} "
            "se invalida y hay que volver a leer el activo.",
            "━━━━━━━━━━━━━━━━━━━",
        ]

    verbo = "perdió" if alcista else "superó"
    return [
        f"⚠️ *El sesgo {palabra} quedó invalidado: el precio {verbo} {nivel}*",
        "La lectura direccional deja de estar vigente. Conviene esperar a que el "
        "activo se reordene antes de volver a leerlo.",
        "━━━━━━━━━━━━━━━━━━━",
    ]


def divergencia_vigencia(
    vigencia: dict[str, Any] | None, precio_nuevo: float
) -> str | None:
    """Motivo por el que el sesgo dejó de estar vigente entre preparar y salir.

    Complementa a `divergencia_editorial`, que vigila el soporte y la
    resistencia. El Chandelier no es ninguno de los dos y es el stop del propio
    Playbook: una pieza que afirma "sigue vigente hasta 933,44" publicada con el
    precio en 932,90 dice exactamente lo contrario de lo que pasa.

    Solo aplica a la gramática `NIVEL`. El rango ya queda cubierto: sus dos
    bordes **son** el soporte y la resistencia que la otra función compara.
    """
    if not vigencia or vigencia.get("gramatica") != "NIVEL":
        return None
    nivel = vigencia.get("nivel")
    direccion = vigencia.get("direccion")
    if nivel is None or direccion not in ("LARGO", "CORTO"):
        return None

    nivel = float(nivel)
    sigue = precio_nuevo > nivel if direccion == "LARGO" else precio_nuevo < nivel
    if sigue:
        return None

    verbo = "perdió" if direccion == "LARGO" else "superó"
    palabra = "alcista" if direccion == "LARGO" else "bajista"
    return (
        f"el sesgo {palabra} quedó invalidado: el precio {verbo} el nivel de "
        f"{nivel:g} y quedó en {precio_nuevo:g}, así que el texto afirma una "
        f"vigencia que ya no existe"
    )


def revigenciar(
    vigencia: dict[str, Any] | None, h1: dict[str, Any], digits: int
) -> dict[str, Any] | None:
    """La vigencia recalculada contra el mercado de ahora.

    El Chandelier se mueve con cada vela que cierra, así que el nivel calculado
    al preparar la tanda envejece igual que el precio. Publicarlo veinte minutos
    después sería un dato viejo con cara de fresco, que es justo lo que el
    refresco por pieza existe para evitar.

    **Sin ratchet, a propósito.** Que el nivel solo avance a favor exige saber
    dónde entró una posición, y esto no gestiona posiciones: publica una lectura.
    El criterio es el mismo que documenta `bias_reader.nivel_chandelier`.
    """
    if not vigencia:
        return None

    from market_data_mcp.bias_reader import nivel_chandelier

    nueva = dict(vigencia)
    try:
        precio = float(h1["price"])
    except (KeyError, TypeError, ValueError):
        return nueva

    if nueva["gramatica"] == "RANGO":
        try:
            nueva["borde_inferior"] = round(float(h1["s1"]), digits)
            nueva["borde_superior"] = round(float(h1["r1"]), digits)
        except (KeyError, TypeError, ValueError):
            return nueva
        nueva["vigente"] = nueva["borde_inferior"] <= precio <= nueva["borde_superior"]
        return nueva

    direccion = nueva.get("direccion")
    clave = "chandelier_max" if direccion == "LARGO" else "chandelier_min"
    try:
        nueva["nivel"] = nivel_chandelier(
            float(h1[clave]), float(h1["atr_14"]),
            float(nueva["multiplo_atr"]), direccion, digits,
        )
    except (KeyError, TypeError, ValueError):
        # Sin anclas frescas se conserva el nivel de la preparación: es un dato
        # de hace un rato, pero es el que el texto afirma. Inventar otro sería peor.
        pass

    if nueva.get("nivel") is not None:
        nueva["vigente"] = (
            precio > float(nueva["nivel"]) if direccion == "LARGO"
            else precio < float(nueva["nivel"])
        )
    return nueva


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

    return None


def construir_payload(
    seleccion: dict[str, Any],
    activo_catalogo: dict[str, Any],
    ahora: datetime,
    cierres: list[float],
) -> dict[str, Any]:
    """Payload de `alerta` con los datos resueltos y lo editorial en blanco.

    Levanta `PayloadIncoherenteError` si las dos lecturas del terminal que se
    juntan aca no describen el mismo instante. Se niega a construir en vez de
    devolver algo marcado, por la misma politica de `rendir` ante un campo
    editorial vacio: una pieza a medias que sale sin avisar llega al cliente.
    """
    motivo = incoherencia_del_payload(seleccion, cierres)
    if motivo is not None:
        raise PayloadIncoherenteError(f"{seleccion['ticker']}: {motivo}")
    digits = activo_catalogo["digits"]
    imagen = activo_catalogo["imagen"]
    slug = _slug_de_imagen(imagen)
    cat_real = activo_catalogo.get("categoria", seleccion["clase"])

    def fmt(valor: float) -> str:
        return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")

    vigencia_cruda, omitida = vigencia_publicable(
        seleccion.get("vigencia"), seleccion["direccion"]
    )
    sesgo_pieza = direccion_publicada(seleccion["direccion"], vigencia_cruda, omitida)

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
        # El chip lo manda el Playbook cuando opina; la lectura tecnica solo
        # cubre los activos sin ficha. Ver `direccion_publicada`.
        "sesgo": sesgo_pieza,
        "tag_riesgo": sesgo_pieza.upper(),
        # Hasta donde sigue vigente el sesgo del Playbook, en la gramatica que
        # le corresponde. `None` si el activo no tiene ficha, si el modelo no lo
        # pudo leer, o si su direccion contradice la lectura tecnica de la pieza.
        "vigencia": formatear_vigencia(vigencia_cruda, fmt),
        # Datos del motor
        "precio_actual": fmt(seleccion["precio"]),
        "soporte": fmt(seleccion["soporte"]),
        "resistencia": fmt(seleccion["resistencia"]),
        "vol_pct": f"{fmt(seleccion['impulso_adc_atr'])} {activo_catalogo['unidad']}",
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
                "precio": seleccion["precio"],
                "clase": "actual",
                "etiqueta": fmt(seleccion["precio"]),
                "rol": "AHORA",
            }],
            "niveles": [
                {"precio": seleccion["resistencia"], "clase": "resistencia",
                 "etiqueta": fmt(seleccion["resistencia"]), "rol": "RESISTENCIA"},
                {"precio": seleccion["soporte"], "clase": "soporte",
                 "etiqueta": fmt(seleccion["soporte"]), "rol": "SOPORTE"},
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
                "vigencia_nivel": (
                    float(vigencia_cruda["nivel"])
                    if vigencia_cruda and vigencia_cruda.get("nivel") is not None
                    else None
                ),
            },
            # El sesgo con sus numeros, para poder recalcularlo justo antes de
            # despachar sin volver a pedirle el snapshot al Playbook.
            "vigencia": vigencia_cruda,
            "vigencia_omitida": omitida,
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
    3. **El canal de avisos, siempre**, por decision del director del 2026-09-03.
       Declararlo importa: el mismo resultado salia antes del default de
       `obtener_grupo_whatsapp`, o sea que habria seguido ocurriendo aunque la
       decision hubiera sido la contraria.
    """
    canales = {p["grupo"] for p in payloads if p.get("grupo")}
    if grupo_pedido:
        canales.add(grupo_pedido)
    canales.add(CANAL_AVISOS)
    return canales


def construir_mensaje_alerta(payload: dict[str, Any]) -> str:
    """Genera el mensaje de texto de alerta formateado para WhatsApp según las 6 reglas canónicas."""
    activo = payload["activo"]
    rotulo = payload.get("rotulo_activo", activo)
    ticker = rotulo.split("·")[-1].strip() if "·" in rotulo else activo
    precio = payload["precio_actual"]
    soporte = payload["soporte"]
    resistencia = payload["resistencia"]
    vol = payload.get("vol_pct", "")
    sesgo = payload.get("sesgo", "Alcista")
    alcista = sesgo.lower() == "alcista"
    lateral = sesgo.lower() == "lateral"

    # **`no alcista` no significa bajista.** Desde que el chip puede quedar
    # neutro (sesgo invalidado, rango, o contradicción entre el Playbook y las
    # medias), caer al caso bajista por descarte publicaba "presión vendedora"
    # sobre un activo del que justamente no se afirma dirección.
    if lateral:
        nivel_vigilar = f"{soporte} y {resistencia}"
        accion = "Definición al salir del rango, por arriba o por abajo"
    elif alcista:
        nivel_vigilar = resistencia
        accion = f"Fuerza compradora sobre {resistencia}"
    else:
        nivel_vigilar = soporte
        accion = f"Presión vendedora bajo {soporte}"

    titular = payload.get("titular", "").strip()
    parrafo = payload.get("parrafo", "").strip()

    lineas = [
        f"🎯 Activo: {activo} ({ticker})",
        f"📌 Nivel a vigilar: {nivel_vigilar}",
        f"⚡ Qué esperar: {accion}",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    # El "hasta donde" va arriba y no al final: la regla de "above the fold" pide
    # la conclusion practica en las primeras lineas, y para el director esta es
    # LA conclusion. Que el sesgo siga vigente, y hasta que nivel, es lo que
    # decide si el cliente hace algo con el mensaje o solo lo lee.
    lineas.extend(bloque_vigencia(payload.get("vigencia")))
    if titular:
        lineas.append(f"*{titular}*")
        lineas.append("")
    if parrafo:
        lineas.append(parrafo)
        lineas.append("━━━━━━━━━━━━━━━━━━━")

    lineas.extend([
        f"📊 *Niveles técnicos ({TIMEFRAME_GRAFICO})*:",
        f"• Precio actual: {precio}",
        f"• 🟢 Resistencia clave: {resistencia}",
        f"• 🔴 Soporte clave: {soporte}",
        f"• 💡 Volatilidad típica: {vol}",
        "━━━━━━━━━━━━━━━━━━━",
        f"🟢 Sobre {resistencia} → fuerza compradora",
        f"🟡 Entre {soporte} y {resistencia} → esperar confirmación",
        f"🔴 Bajo {soporte} → presión vendedora",
        "━━━━━━━━━━━━━━━━━━━",
        "Cada imagen adjunta contiene el gráfico y análisis técnico. ¿Dudas? Consulta a tu analista.",
    ])
    return "\n".join(lineas)


def limpiar_payloads(directorio: Path) -> list[str]:
    """Borra los payloads y archivos generados de una corrida anterior de la MISMA tanda.

    `rendir()` toma todos los `.json` sin prefijo `_` del directorio de forma recursiva.
    Sin este barrido, volver a preparar deja los viejos al lado de los nuevos.
    """
    barridos = []
    if not directorio.exists():
        return barridos
    for archivo in directorio.rglob("*"):
        if archivo.is_file():
            if archivo.name.startswith("_"):
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
            construir_mensaje_suplemento(sup), encoding="utf-8"
        )
        (carpeta / "_suplemento.json").write_text(
            json.dumps(sup, ensure_ascii=False, indent=2), encoding="utf-8"
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

    barridos = limpiar_payloads(destino)

    payloads: list[dict[str, Any]] = []
    problemas: list[str] = []
    for i, sel in enumerate(resultado["seleccion"], 1):
        activo = catalogo.get(sel["ticker"])
        if not activo or not activo.get("imagen"):
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
    eventos_macro, delta_ust, _ = sc._contexto_macro(ahora)
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
    suplementos, avisos_sup = escribir_suplementos(
        destino, resultado.get("excluidos") or [], grupos_activos, catalogo,
        buscar_noticia=lambda canal: noticia_para_canal(
            canal, ahora=ahora, historial=_hist, descargar=_bajar
        ),
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
        "avisos": resultado["avisos"] + avisos_sup + (
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
        return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")

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

    # La vigencia se recalcula con las anclas de ahora, igual que el precio, y
    # se vuelve a preguntar si el sesgo sigue en pie. Un motivo por soporte o
    # resistencia manda sobre este: es el que ya estaba medido contra el texto.
    vigencia_cruda = revigenciar(
        nuevo.get("_procedencia", {}).get("vigencia"), h1, digits
    )
    if motivo is None:
        motivo = divergencia_vigencia(vigencia_cruda, precio)

    nuevo["vigencia"] = formatear_vigencia(vigencia_cruda, fmt)
    nuevo["_procedencia"]["vigencia"] = vigencia_cruda

    # El chip sigue al estado recalculado. Si el precio recupero su nivel entre
    # preparar y despachar, un chip neutro junto a "el sesgo sigue vigente" seria
    # la misma contradiccion que este cambio vino a cerrar, al reves.
    #
    # Dos cosas cambiaron el 2026-09-04 y las dos venian del mismo caso, GLD.US:
    #
    # 1. **Se recalcula siempre, no solo con vigencia.** GLD llegaba con
    #    `vigencia: None` (no tiene ficha del Playbook), asi que entraba por el
    #    `else` inexistente: el sesgo "Alcista" de la preparacion sobrevivia
    #    intacto aunque la lectura de ahora fuera bajista. Los 33 activos del
    #    catalogo sin ficha estaban en ese agujero, o sea casi todos.
    # 2. **La direccion se lee del mercado, no del propio payload.** Antes se
    #    re-derivaba del string `nuevo["sesgo"]`, que es circular: si venia mal,
    #    seguia mal. Ahora sale de `direccion_tecnica`, que es **la misma funcion
    #    que uso el escaner** para elegir el activo. Usar `h1["trend"]` habria
    #    parecido equivalente y no lo es: `trend` compara contra la EMA 100 y
    #    `direccion_tecnica` contra la EMA 50, asi que preparar y refrescar
    #    habrian medido con distinta vara.
    if "ema_50" not in h1:
        return nuevo, motivo or (
            "el analizador no devolvio la EMA 50 de H1, asi que la direccion de "
            "la pieza no se puede confirmar contra el mercado de ahora"
        )
    tecnica = sc.direccion_tecnica(h1)
    nuevo["sesgo"] = direccion_publicada(tecnica, vigencia_cruda, None)
    nuevo["tag_riesgo"] = nuevo["sesgo"].upper()

    nuevo["_procedencia"].setdefault("crudos", {})
    nuevo["_procedencia"]["crudos"] = {
        "precio": precio, "soporte": soporte, "resistencia": resistencia,
        "vigencia_nivel": (
            float(vigencia_cruda["nivel"])
            if vigencia_cruda and vigencia_cruda.get("nivel") is not None
            else None
        ),
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


def rendir(directorio: Path) -> dict[str, Any]:
    """Valida lo editorial, produce las piezas en horizontal y actualiza los mensajes modulares dentro de cada grupo."""
    from story_grafico import enriquecer
    from story_render import render_story

    archivos = sorted(p for p in directorio.rglob("*.json") if not p.name.startswith("_") and not p.name.startswith("0_contexto_macro"))
    if not archivos:
        raise SystemExit(f"No hay payloads de alerta en {directorio}")

    sin_escribir: list[str] = []
    for archivo in archivos:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        faltan = [c for c in CAMPOS_EDITORIALES if not str(payload.get(c, "")).strip()]
        if faltan:
            nombre_rel = archivo.relative_to(directorio) if archivo.is_relative_to(directorio) else archivo.name
            sin_escribir.append(f"{nombre_rel}: falta {', '.join(faltan)}")

    if sin_escribir:
        raise SystemExit(
            "Hay piezas sin texto editorial. Una pieza a medias que sale sin avisar "
            "llega al cliente, asi que el render se detiene:\n  "
            + "\n  ".join(sin_escribir)
        )

    ahora = datetime.now(tz=SANTIAGO)
    generadas: list[dict[str, Any]] = []
    resumen_piezas: list[dict[str, Any]] = []

    for archivo in archivos:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        procedencia = payload.pop("_procedencia", {})
        payload.pop("_pendiente_editorial", None)

        # `story_grafico.enriquecer` consume `recorrido` y lo reemplaza por `grafico`
        payload = enriquecer(payload)

        # Alerta de mercado es exclusivamente horizontal 16:9 guardada directamente en la carpeta del grupo
        formato = "horizontal"
        destino_local_png = archivo.parent / f"{archivo.stem}.png"
        render_story(payload, PLANTILLA, destino_local_png, formato=formato)

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
        "⏱️ Temporalidad: intradía (dentro de la jornada)",
        "━━━━━━━━━━━━━━━━━━━",
        "Cada imagen y mensaje detallado han sido modularizados en su carpeta de grupo correspondiente.",
    ])
    (directorio / "mensaje_indice.txt").write_text("\n".join(lineas_indice), encoding="utf-8")

    return {"directorio": str(directorio), "imagenes": generadas}


def _refrescar_y_rendir(dir_grupo: Path) -> list[str]:
    """Vuelve a leer el mercado, redibuja las piezas de precio y reescribe sus textos.

    Solo toca las piezas de activo (`1_`, `2_`…). El contexto macro (`0_`) es la
    agenda del día: no decae por minuto y su fuente es el calendario, no una
    cotización.
    """
    from market_data_mcp.analisis import analizar_activo
    from story_grafico import enriquecer
    from story_render import render_story

    catalogo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}
    ahora = datetime.now(tz=SANTIAGO)
    avisos: list[str] = []

    for archivo in sorted(dir_grupo.glob("*.json")):
        if archivo.stem.startswith("0_") or archivo.stem.startswith("_"):
            continue

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

        pieza = json.loads(json.dumps(nuevo))
        pieza.pop("_procedencia", None)
        pieza.pop("_pendiente_editorial", None)
        render_story(enriquecer(pieza), PLANTILLA, dir_grupo / f"{archivo.stem}.png",
                     formato="horizontal")
        (dir_grupo / f"{archivo.stem}_mensaje.txt").write_text(
            construir_mensaje_alerta(nuevo), encoding="utf-8"
        )
        avisos.append(f"✅ {ticker} refrescado a las {ahora.strftime('%H:%M')}")

    return avisos


def despachar(
    directorio: Path,
    desde: int = 1,
    dry_run: bool = False,
    headless: bool = True,
) -> dict[str, Any]:
    """Rinde y despacha canal por canal, en orden y sin dejar envejecer las piezas.

    Cada canal sale en **una sola acción**: el editor de medios acepta varias
    imágenes y cada una conserva su propio pie, así que las cuatro piezas de un
    canal no necesitan cuatro aperturas de navegador espaciadas 45 s.

    Y cada canal se rinde **justo antes** de despacharse, no al principio de la
    tanda: así el precio de la última pieza tiene minutos y no media hora. El
    render cabe entero dentro de la espera de cadencia, así que no cuesta tiempo.
    """
    from whatsapp_sender import WhatsAppSender, huella
    from bitacora_despachos import cargar as cargar_bitacora
    from bitacora_despachos import registrar as anotar_despacho
    from bitacora_despachos import ya_despachada

    grupos = sorted(d for d in directorio.iterdir() if d.is_dir())
    if not grupos:
        raise SystemExit(f"No hay carpetas de grupo en {directorio}")

    sender = WhatsAppSender(headless=headless)
    resultados: list[dict[str, Any]] = []

    # La bitacora es la unidad correcta para retomar. `--desde N` cuenta CANALES,
    # y desde el 2026-09-03 el envio cuenta PIEZAS: retomar un canal que fallo en
    # su segunda de tres reenviaba la primera. Se conserva `--desde` como control
    # manual del director, pero lo normal es que ya no haga falta.
    tanda = directorio.name
    bitacora = cargar_bitacora()

    for i, dir_grupo in enumerate(grupos, 1):
        if i < desde:
            print(f"[{i}/{len(grupos)}] {dir_grupo.name}: omitido (--desde {desde})", flush=True)
            resultados.append({"grupo": dir_grupo.name, "status": "omitido"})
            continue

        print(f"\n[{i}/{len(grupos)}] {dir_grupo.name}", flush=True)
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
                texto = suplemento.read_text(encoding="utf-8").strip()
                print(f"    suplemento de {len(texto)} caracteres, sin adjunto...", flush=True)
                if ya_despachada(bitacora, tanda, dir_grupo.name, "0_suplemento"):
                    print("    suplemento ya despachado segun la bitacora: se omite", flush=True)
                    resultados.append({"grupo": dir_grupo.name, "status": "ya_despachado"})
                    continue
                res = sender.enviar(
                    dir_grupo.name, mensaje=texto, dry_run=dry_run
                )
                if not dry_run:
                    anotar_despacho(
                        tanda, dir_grupo.name, "0_suplemento",
                        huella=huella(texto),
                    )
                resultados.append({"grupo": dir_grupo.name, "suplemento": True, **res})
                # La cadencia no se maneja aca: `enviar` reserva su turno y
                # espera por su cuenta, igual que el resto de las piezas.
                continue

            print("    sin piezas: se omite", flush=True)
            resultados.append({"grupo": dir_grupo.name, "status": "vacio"})
            continue

        canal = dir_grupo.name
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

        def anotar(pieza: Any, _canal: str = canal) -> None:
            # La huella sale de la MISMA funcion que compara el guardia de entrega
            # contra el DOM. Una segunda implementacion seria otro de los relojes
            # duplicados que ya costaron caro en este repo.
            anotar_despacho(
                tanda, _canal, Path(pieza.adjunto).stem,
                huella=huella(pieza.mensaje or ""),
            )

        print(f"    despachando {len(pendientes)} pieza(s), una por acción...", flush=True)
        res = sender.enviar_lote(canal, pendientes, dry_run=dry_run, al_entregar=anotar)
        resultados.append({"grupo": canal, **res})

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
        )
        print("\nRESUMEN DEL DESPACHO")
        for g in res["grupos"]:
            piezas = g.get("piezas", "")
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
