#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Módulo de Cobertura Macro Diaria por Grupo de WhatsApp.

Garantiza que cada canal temático de WhatsApp cuente con:
1. Una Story visual de Dato Macro (imagen 16:9 de alta resolución) con plantilla `dato_macro.html`,
   alimentada exclusivamente con series históricas oficiales y reales de `data central/`
   (Banco Central de Chile, Tesoro de EE.UU. FRED, FED).
2. Un mensaje de contexto macro diario en WhatsApp que prioriza información soberana de alto interés,
   con enlaces directos e interactivos para la comunidad a FRED y BCCh.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
for p in (str(SRC), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

SANTIAGO = ZoneInfo("America/Santiago")
TEMPLATE_DATO_MACRO = RAIZ / "templates" / "stories" / "dato_macro.html"
BCCH_DATA_PATH = RAIZ / "data central" / "DATA CHILE" / "raw" / "bcch_macro_data.json"
TREASURY_FED_DATA_PATH = RAIZ / "data central" / "DATA USA" / "raw" / "treasury_fed_data.json"

try:
    from market_data_mcp.curva_reader import cargar_curva_tasas
except ImportError:
    cargar_curva_tasas = None

# Un evento del calendario tiene que leerse IGUAL en el informe y en el mensaje de
# cada grupo: mismo nombre en español, mismo estado y misma notación de cifras. Por
# eso se importan los helpers del informe en vez de reescribirlos acá — dos
# traductores del mismo evento terminan discrepando y el cliente ve dos versiones.
from pipeline_informe import (  # noqa: E402
    CALENDARIO_URL,
    _PAISES_ES,
    _cifra_es,
    _distinguir,
    _estado_evento,
    _nombre_indicador,
)

try:
    from story_grafico import enriquecer
    from story_render import render_story
except ImportError:
    enriquecer = None
    render_story = None


CONFIG_MACRO_GRUPOS: dict[str, dict[str, Any]] = {
    "01_macro_y_apertura": {
        "nombre": "Macro & Apertura Global",
        "paises": ("united states", "estados unidos", "chile", "euro zone", "zona euro", "china", "japan", "japon"),
        "foco": "Panorama macroeconómico intermercado, política monetaria y catalizadores de la sesión global.",
        "interpretacion": (
            "La curva soberana de EE.UU. es la referencia de precio del dinero en el mundo: de su "
            "trayectoria, junto con los datos de actividad y empleo, cuelga el apetito por riesgo y "
            "la rotación de flujos globales."
        ),
    },
    "02_forex_divisas": {
        "nombre": "Forex & Divisas",
        "paises": ("chile", "united states", "estados unidos", "euro zone", "zona euro", "japan", "japon", "united kingdom"),
        "foco": "Diferenciales de tasas de interés de bancos centrales, fortaleza del Dollar Index (DXY) y flujos cambiarios.",
        "interpretacion": (
            "El precio del dólar lo ordena el diferencial de tasas: cuando los rendimientos del Tesoro "
            "de EE.UU. suben frente a los de Europa y Japón, el dólar gana terreno contra el euro, la "
            "libra y el yen; cuando ceden, lo pierde. En el plano local, el USD/CLP suma dos factores "
            "propios: la tasa del Banco Central de Chile y el precio del cobre."
        ),
    },
    "03_commodities_materias_primas": {
        "nombre": "Commodities & Materias Primas",
        "paises": ("united states", "estados unidos", "china", "euro zone"),
        "patrones": ("inventories", "eia", "api", "opec", "crude", "petroleo", "copper", "cobre", "gold", "oro", "prices"),
        "foco": "Tasas reales (TIPS 10Y), inventarios energéticos, demanda manufacturera industrial de China y tensiones geopolíticas.",
        "interpretacion": (
            "El comportamiento de la tasa real TIPS 10Y condiciona el costo de oportunidad del Oro (XAU/USD). "
            "Al mismo tiempo, los precios pagados en manufactura y los informes de inventarios de crudo (API/EIA) "
            "marcan la pauta para la energía y los metales básicos."
        ),
    },
    "04_indices_bursatiles": {
        "nombre": "Índices Bursátiles",
        "paises": ("united states", "estados unidos", "euro zone"),
        "patrones": ("ism", "pmi", "cpi", "gdp", "employment", "payrolls", "fomc", "fed", "tasas", "jolts"),
        "foco": "Rendimientos de bonos del Tesoro estadounidense (2s10s), política de la Fed y datos de actividad económica.",
        "interpretacion": (
            "El rendimiento del bono del Tesoro a 10 años actúa como tasa de descuento para las valoraciones bursátiles. "
            "Cifras de empleo y manufactura modulan las expectativas de recortes de tasas de la Reserva Federal "
            "e impactan directamente en el Nasdaq 100 y S&P 500."
        ),
    },
    "05_acciones_etfs": {
        "nombre": "Acciones & ETFs Internacionales",
        "paises": ("united states", "estados unidos"),
        "patrones": ("earnings", "gdp", "ism", "pmi", "fed", "yield"),
        "foco": "Temporada de balances corporativos, costo de capital, ciclo de semiconductores y flujos sectoriales.",
        "interpretacion": (
            "La rotación sectorial responde al costo del capital y las perspectivas de crecimiento económico, "
            "evaluando múltiplos en empresas tecnológicas, industriales y financieras frente a los bonos soberanos."
        ),
    },
    "06_criptoactivos": {
        "nombre": "Criptoactivos & Digital Assets",
        "paises": ("united states", "estados unidos"),
        "patrones": ("fed", "fomc", "interest rate", "cpi", "liquidity", "etf"),
        "foco": "Liquidez global, tasas de descuento en EE.UU., correlación con tecnología y flujos netos hacia ETFs spot.",
        "interpretacion": (
            "El ecosistema cripto se mueve con la liquidez: cuando las tasas cortas de EE.UU. suben, "
            "dejar el dinero en renta fija rinde más y compite con los activos de riesgo; cuando bajan, "
            "esa competencia se afloja. A eso se suman los flujos netos hacia los ETF spot de Bitcoin y Ethereum."
        ),
    },
    "07_oportunidades_cuantitativas": {
        "nombre": "Oportunidades & Trading Cuantitativo",
        "paises": ("united states", "estados unidos", "chile"),
        "foco": "Setups técnicos validados contra filtros de calendario macro y volatilidad de la jornada.",
        "interpretacion": (
            "Se auditan las operaciones para evitar operar en ventanas de blackout macroeconómico "
            "y dimensionar lotajes según el régimen de volatilidad intradía."
        ),
    },
}

ENLACES_INSTITUCIONALES: dict[str, str] = {
    "TIPS_10Y": "https://fred.stlouisfed.org/series/DFII10",
    "UST_10Y": "https://fred.stlouisfed.org/series/DGS10",
    "UST_2Y": "https://fred.stlouisfed.org/series/DGS2",
    "DXY": "https://es.tradingview.com/symbols/TVC-DXY/",
    "IMACEC_BCCH": "https://si3.bcentral.cl/Siete/",
}


class DatosMacroNoDisponiblesError(RuntimeError):
    """La serie oficial requerida no está disponible.

    Se levanta en vez de devolver una serie escrita a mano: una cifra inventada
    dentro de una pieza que lleva el sello del BCCh o de FRED es peor que no
    publicar (REGLA 1 de CLAUDE.md y §1 de .agents/rules/proyecto.md).
    """


_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre",
}
_MESES_ABR = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _mes_numero(fecha_iso: str) -> int:
    return int(fecha_iso.split("-")[1])


def _etiqueta_dia(fecha_iso: str) -> str:
    """'2026-09-10' -> '10 Sep'. El mes sale de la fecha, nunca de un literal."""
    partes = fecha_iso.split("-")
    return f"{partes[2]} {_MESES_ABR[_mes_numero(fecha_iso)]}"


def _periodo_desde(fecha_iso: str, sufijo: str) -> str:
    """Rotula el periodo de la tarjeta con el mes real del último dato."""
    return f"{_MESES_ES[_mes_numero(fecha_iso)]} · {sufijo}"


def _leer_serie(ruta: Path, camino: tuple[str, ...], etiqueta_humana: str) -> dict[str, float]:
    """Lee un histórico {fecha: valor} de data central/, o aborta diciendo qué falta."""
    if not ruta.exists():
        raise DatosMacroNoDisponiblesError(
            f"No existe la fuente oficial de {etiqueta_humana}: {ruta}. "
            "Corre la ingesta antes de generar el contexto macro."
        )
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise DatosMacroNoDisponiblesError(
            f"La fuente de {etiqueta_humana} no se pudo leer ({ruta}): {exc}"
        ) from exc
    nodo: Any = data
    for paso in camino:
        nodo = (nodo or {}).get(paso, {})
    hist = nodo.get("historico", {}) if isinstance(nodo, dict) else {}
    if not hist:
        raise DatosMacroNoDisponiblesError(
            f"La serie de {etiqueta_humana} está vacía en {ruta}."
        )
    return {str(k): float(v) for k, v in hist.items()}


def _obtener_historial_imacec() -> list[dict[str, Any]]:
    """Últimas observaciones del Imacec (variación 12 meses) desde data central/."""
    hist = _leer_serie(BCCH_DATA_PATH, ("series", "IMACEC_12M_VAR"), "Imacec del BCCh")
    fechas = sorted(hist)[-7:]
    return [
        {"etiqueta": _MESES_ABR[_mes_numero(fch)], "valor": round(hist[fch], 1), "fecha": fch}
        for fch in fechas
    ]


def _obtener_tpm_vigente() -> tuple[float, str]:
    """Tasa de Política Monetaria vigente y la fecha de esa observación."""
    hist = _leer_serie(BCCH_DATA_PATH, ("series", "TPM"), "TPM del BCCh")
    ultima = sorted(hist)[-1]
    return hist[ultima], ultima


def _obtener_historial_treasury(serie_id: str = "DFII10") -> list[dict[str, Any]]:
    """Últimas observaciones de una serie del Tesoro/FRED, rotuladas con su fecha real."""
    hist = _leer_serie(
        TREASURY_FED_DATA_PATH, ("curva_rendimientos_yields", serie_id), f"la serie {serie_id}"
    )
    fechas = sorted(hist)[-7:]
    return [
        {"etiqueta": _etiqueta_dia(fch), "valor": round(hist[fch], 2), "fecha": fch}
        for fch in fechas
    ]


def filtrar_eventos_para_grupo(grupo: str, eventos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filtra y ordena los eventos macroeconómicos priorizando datos locales de Chile para Forex."""
    cfg = CONFIG_MACRO_GRUPOS.get(grupo)
    if not cfg:
        return eventos

    paises_objetivo = tuple(p.lower() for p in cfg.get("paises", ()))
    patrones_objetivo = tuple(p.lower() for p in cfg.get("patrones", ()))

    chile_eventos = []
    resto_eventos = []

    for ev in eventos:
        pais = str(ev.get("pais", "")).lower()
        nombre = str(ev.get("nombre", "")).lower()

        coincide_pais = any(p in pais for p in paises_objetivo) if paises_objetivo else True
        coincide_patron = any(pat in nombre for pat in patrones_objetivo) if patrones_objetivo else True

        if coincide_pais and (not patrones_objetivo or coincide_patron or ev.get("impacto") == "alto"):
            if "chile" in pais:
                chile_eventos.append(ev)
            else:
                resto_eventos.append(ev)

    if grupo == "02_forex_divisas":
        return chile_eventos + resto_eventos
    return chile_eventos + resto_eventos


# Cuántos eventos entran en el mensaje antes de derivar al calendario completo.
# Más de seis y el bloque se come el "leer más" de WhatsApp, que es justo donde
# tiene que estar la lectura del canal.
MAX_EVENTOS_AGENDA = 6

_ESTADO_EMOJI = {"Publicado": "✅", "Pendiente": "🕐", "Sin cifra": "⚪"}


def _cifras_para_whatsapp(ev: dict[str, Any]) -> str:
    """Las cifras del evento en una línea, en notación chilena.

    Es la versión de `_cifras_evento` del informe sin el markdown de tabla
    (`**`, `<br>`), que en WhatsApp se ve como basura. La conversión de notación
    sí se reutiliza: es la parte que importa y no puede divergir.
    """
    actual = _cifra_es(str(ev.get("actual") or "").strip())
    consenso = _cifra_es(str(ev.get("forecast") or "").strip())
    previo = _cifra_es(str(ev.get("previo") or "").strip())
    if actual and consenso:
        return f"{actual} (se esperaba {consenso})"
    if actual:
        return actual
    if consenso:
        return f"se espera {consenso}"
    if previo:
        return f"anterior {previo}"
    return ""


def _bloque_agenda(eventos_grupo: list[dict[str, Any]], ahora: datetime) -> list[str]:
    """La agenda del día del canal, con el estado real de cada dato.

    El estado lo decide `_estado_evento`, cuyo testigo es la cifra publicada y no
    el reloj. Un dato que aún no sale se redacta en modo anticipación ("se
    espera"), nunca en pasado: es el guardrail anti-anacronismos del proyecto.
    """
    lineas = ["📅 *AGENDA DEL DÍA*"]
    if not eventos_grupo:
        lineas.append("⚪ Sin datos de alto impacto para este canal en la jornada.")
        lineas.append("━━━━━━━━━━━━━━━━━━━")
        return lineas

    visibles = eventos_grupo[:MAX_EVENTOS_AGENDA]
    nombres = _distinguir([_nombre_indicador(ev) for ev in visibles], visibles)

    for ev, nombre in zip(visibles, nombres):
        estado = _estado_evento(ev, ahora)
        hora = str(ev.get("hora_servidor", "")).split(" ")[-1] or "sin hora"
        pais = _PAISES_ES.get(str(ev.get("pais", "")), str(ev.get("pais", "")))
        cifras = _cifras_para_whatsapp(ev)
        cola = f": {cifras}" if cifras else ""
        lineas.append(f"{_ESTADO_EMOJI.get(estado, '⚪')} {hora} · {pais} · *{nombre}*{cola}")

    restantes = len(eventos_grupo) - len(visibles)
    if restantes > 0:
        lineas.append(f"…y {restantes} evento(s) más en el calendario completo.")
    lineas.append(f"🔗 Calendario económico: {CALENDARIO_URL}")
    lineas.append("━━━━━━━━━━━━━━━━━━━")
    return lineas


def construir_texto_contexto_macro(
    grupo: str,
    eventos_grupo: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime,
    con_imagen: bool = True,
) -> str:
    """Genera el mensaje de contexto macro diario en formato canónico de WhatsApp con enlaces institucionales."""
    cfg = CONFIG_MACRO_GRUPOS.get(grupo, {
        "nombre": grupo.replace("_", " ").title(),
        "foco": "Seguimiento macroeconómico de la jornada.",
        "interpretacion": "Seguimiento de factores fundamentales y técnicos de la sesión.",
    })
    nombre_grupo = cfg["nombre"]
    foco = cfg["foco"]
    interpretacion = cfg.get("interpretacion", foco)
    hora_str = ahora.strftime("%H:%M")

    lineas = [
        f"📊 *CONTEXTO MACRO DIARIO · {nombre_grupo.upper()}*",
        f"📅 {ahora.strftime('%d/%m/%Y')} · {hora_str} hrs hora Chile",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    # El calendario va PRIMERO (orden canónico del proyecto, issue #43): el
    # fundamental del día se comunica antes que la lectura de niveles.
    # Se vuelve a filtrar acá aunque el caller ya lo haya hecho: el filtro es
    # idempotente y así ningún caller futuro puede colar un evento de otro canal
    # en el mensaje de este grupo.
    lineas.extend(_bloque_agenda(filtrar_eventos_para_grupo(grupo, eventos_grupo), ahora))

    # PRIORIDAD CHILE EN FOREX & DIVISAS: cifras leídas de las series del BCCh.
    # Nunca se nombra un nivel de USD/CLP acá: el precio sale del motor en tiempo
    # de ejecución (REGLA 1), y este módulo no tiene acceso al MCP.
    if grupo == "02_forex_divisas":
        barras_imacec = _obtener_historial_imacec()
        ultimo = barras_imacec[-1]
        previo = barras_imacec[-2] if len(barras_imacec) >= 2 else None
        mes_dato = _MESES_ES[_mes_numero(ultimo["fecha"])].lower()
        valor_txt = ("+" if ultimo["valor"] > 0 else "") + _pct(ultimo["valor"], 1)
        verbo = "una contracción de" if ultimo["valor"] < 0 else "un avance de"
        comparacion = ""
        if previo is not None:
            mes_previo = _MESES_ES[_mes_numero(previo["fecha"])].lower()
            previo_txt = ("+" if previo["valor"] > 0 else "") + _pct(previo["valor"], 1)
            if ultimo["valor"] < previo["valor"]:
                comparacion = f" Se desacelera frente a {mes_previo} ({previo_txt})."
            elif ultimo["valor"] > previo["valor"]:
                comparacion = f" Mejora frente a {mes_previo} ({previo_txt})."
            else:
                comparacion = f" Repite la lectura de {mes_previo} ({previo_txt})."
        tpm_valor, tpm_fecha = _obtener_tpm_vigente()
        tpm_txt = _pct(tpm_valor, 2)

        lineas.extend([
            "🇨🇱 *FOCO LOCAL · ACTIVIDAD ECONÓMICA (IMACEC)*",
            f"El Imacec de {mes_dato} marcó {verbo} {valor_txt} anual.{comparacion}",
            f"• *Por qué le importa al peso*: con la Tasa de Política Monetaria (TPM) en {tpm_txt}, "
            "una actividad más débil le da al Banco Central más razones para seguir bajándola, y una "
            "tasa local más baja le resta atractivo al peso frente al dólar. Si la actividad sorprende "
            "al alza, el efecto es el contrario.",
            f"🔗 Serie oficial Imacec y TPM (BCCh, al {_etiqueta_dia(tpm_fecha)}): "
            f"{ENLACES_INSTITUCIONALES['IMACEC_BCCH']}",
            "━━━━━━━━━━━━━━━━━━━",
        ])

    # Curva soberana y tasas clave
    curva_info = {}
    if cargar_curva_tasas:
        try:
            res_curva = cargar_curva_tasas("ALL")
            curva_info = res_curva.get("series", {})
        except Exception:  # noqa: BLE001
            pass

    bloque_soberano = []
    enlaces_bloque = []

    if delta_ust_bps is not None:
        signo = "+" if delta_ust_bps > 0 else ""
        bloque_soberano.append(f"• 📈 Rendimiento Bono EE.UU. 10Y (UST 10Y): *{_bps(delta_ust_bps)} bps*")
        enlaces_bloque.append(f"🔗 Gráfico UST 10Y (FRED): {ENLACES_INSTITUCIONALES['UST_10Y']}")

    if curva_info:
        dgs2 = curva_info.get("DGS2", {})
        dfii10 = curva_info.get("DFII10", {})
        if dgs2.get("delta_1d_bps") is not None and grupo in ("02_forex_divisas", "04_indices_bursatiles"):
            s2 = "+" if dgs2["delta_1d_bps"] > 0 else ""
            bloque_soberano.append(f"• 🏛️ Tasa 2 Años EE.UU. (sensible a Fed): *{_bps(dgs2['delta_1d_bps'])} bps*")
        if dfii10.get("delta_1d_bps") is not None and grupo == "03_commodities_materias_primas":
            stips = "+" if dfii10["delta_1d_bps"] > 0 else ""
            bloque_soberano.append(f"• 🪙 Tasa Real TIPS 10Y (driver del Oro): *{_bps(dfii10['delta_1d_bps'])} bps*")
            enlaces_bloque.append(f"🔗 Gráfico Tasa Real TIPS 10Y (FRED): {ENLACES_INSTITUCIONALES['TIPS_10Y']}")

    if bloque_soberano:
        lineas.append("🏛️ *CURVA SOBERANA Y TASAS*")
        lineas.extend(bloque_soberano)
        if enlaces_bloque:
            links_unicos = list(dict.fromkeys(enlaces_bloque))
            lineas.extend(links_unicos)
        lineas.append("━━━━━━━━━━━━━━━━━━━")

    lineas.extend([
        f"🧠 *¿QUÉ SIGNIFICA PARA {nombre_grupo.upper()}?*",
        f"{interpretacion}",
        "━━━━━━━━━━━━━━━━━━━",
    ])
    # Solo se promete la imagen si efectivamente se produjo: un texto que anuncia
    # un gráfico inexistente llega roto al cliente.
    if con_imagen:
        lineas.append(
            "💡 *En la imagen adjunta encuentras el gráfico y el detalle de la serie oficial. "
            "A continuación compartimos los niveles técnicos y alertas para operar la jornada.*"
        )
    else:
        lineas.append(
            "💡 *A continuación compartimos los niveles técnicos y alertas para operar la jornada.*"
        )

    return "\n".join(lineas)


def _obtener_serie_continua_treasury(serie_id: str = "DFII10", n_puntos: int = 15) -> list[float]:
    """Trayectoria continua de una tasa soberana para el gráfico de línea."""
    hist = _leer_serie(
        TREASURY_FED_DATA_PATH, ("curva_rendimientos_yields", serie_id), f"la serie {serie_id}"
    )
    fechas = sorted(hist)[-n_puntos:]
    return [round(hist[fch], 2) for fch in fechas]


def _ultima_fecha_treasury(serie_id: str) -> str:
    hist = _leer_serie(
        TREASURY_FED_DATA_PATH, ("curva_rendimientos_yields", serie_id), f"la serie {serie_id}"
    )
    return sorted(hist)[-1]


# Cada grupo cuelga de UNA tasa soberana. `signo` es la elasticidad conocida del
# activo frente a esa tasa: +1 se mueve con ella, -1 en contra. La dirección que
# se publica sale de multiplicar ese signo por el movimiento MEDIDO de la serie,
# así que no queda ninguna afirmación direccional congelada en el código.
DRIVERS_SOBERANOS: dict[str, dict[str, Any]] = {
    "03_commodities_materias_primas": {
        "serie": "DFII10",
        "chip_pais": "TESORO EE.UU. · METALES",
        "indicador": "Tasa Real TIPS 10Y (EE.UU.)",
        "sufijo_periodo": "rendimiento real",
        "titular_sube": "La tasa real TIPS 10Y sube y encarece mantener metales sin rendimiento",
        "titular_baja": "La tasa real TIPS 10Y cede y alivia el costo de mantener metales",
        "titular_plano": "La tasa real TIPS 10Y se mantiene y deja al Oro sin impulso propio",
        "significado": (
            "La tasa real es lo que rinde un bono ya descontada la inflación. Cuando sube, "
            "guardar un metal que no paga interés cuesta más caro; cuando baja, cuesta menos."
        ),
        "sello": "U.S. Department of the Treasury · FRED · Grupo Inteligencia",
        "activos": [
            ("Oro (XAU/USD)", -1, "la tasa real es su costo de oportunidad directo"),
            ("Plata (XAG/USD)", -1, "sigue al Oro con más volatilidad por su uso industrial"),
        ],
    },
    "04_indices_bursatiles": {
        "serie": "DGS10",
        "chip_pais": "RENTA VARIABLE EE.UU.",
        "indicador": "Rendimiento Bono 10Y (UST 10Y)",
        "sufijo_periodo": "tasa soberana",
        "titular_sube": "El bono a 10 años sube y encarece el descuento de las tecnológicas",
        "titular_baja": "El bono a 10 años cede y alivia la valoración de las tecnológicas",
        "titular_plano": "El bono a 10 años se mantiene y deja la valoración sin presión nueva",
        "significado": (
            "El bono a 10 años es la tasa con que el mercado descuenta las ganancias futuras. "
            "Si sube, las empresas que prometen crecimiento lejano valen menos hoy."
        ),
        "sello": "U.S. Department of the Treasury · FRED · Grupo Inteligencia",
        "activos": [
            ("Nasdaq 100", -1, "es el índice más sensible a la tasa de descuento"),
            ("Dow Jones", 1, "pesa menos crecimiento futuro y más caja presente"),
        ],
    },
    "05_acciones_etfs": {
        "serie": "DGS10",
        "chip_pais": "MERCADOS ACCIONARIOS",
        "indicador": "Costo de Capital (UST 10Y)",
        "sufijo_periodo": "tasa soberana",
        "titular_sube": "El costo de capital sube y exige más rigor en los balances",
        "titular_baja": "El costo de capital cede y da aire a las empresas apalancadas",
        "titular_plano": "El costo de capital se mantiene y sostiene la selectividad por balance",
        "significado": (
            "El costo de capital es lo que le cuesta a una empresa financiarse. Cuando sube, "
            "premia a la que genera caja y castiga a la que vive de deuda."
        ),
        "sello": "U.S. Department of the Treasury · FRED · Grupo Inteligencia",
        "activos": [
            ("Mega-caps tecnológicas", -1, "sus múltiplos dependen del descuento de flujos"),
            ("Sector bancario", 1, "gana margen cuando el diferencial de tasas se abre"),
        ],
    },
    "06_criptoactivos": {
        "serie": "DGS2",
        "chip_pais": "ACTIVOS DIGITALES",
        "indicador": "Tasa Soberana 2Y (DGS2)",
        "sufijo_periodo": "liquidez",
        "titular_sube": "La tasa a 2 años sube y drena liquidez del apetito por riesgo",
        "titular_baja": "La tasa a 2 años cede y suelta liquidez hacia los activos de riesgo",
        "titular_plano": "La tasa a 2 años se mantiene y deja la liquidez sin cambio",
        "significado": (
            "La tasa a 2 años refleja lo que el mercado espera de la Fed. Cuando sube, "
            "dejar el dinero en renta fija rinde más y compite con los activos de riesgo."
        ),
        "sello": "Federal Reserve · FRED · Grupo Inteligencia",
        "activos": [
            ("Bitcoin (BTC)", -1, "responde a las condiciones de liquidez global"),
            ("Ethereum (ETH)", -1, "sigue a Bitcoin con mayor beta en fases de riesgo"),
        ],
    },
}

DRIVER_SOBERANO_POR_DEFECTO: dict[str, Any] = {
    "serie": "DGS10",
    "chip_pais": "MACRO GLOBAL",
    "indicador": "Rendimiento Bono 10Y (UST 10Y)",
    "sufijo_periodo": "tasa soberana",
    "titular_sube": "El bono a 10 años de EE.UU. sube y ordena la rotación intermercado",
    "titular_baja": "El bono a 10 años de EE.UU. cede y relaja la rotación intermercado",
    "titular_plano": "El bono a 10 años de EE.UU. se mantiene y deja la rotación sin cambio",
    "significado": (
        "La curva del Tesoro de EE.UU. es la referencia de precio del dinero en el mundo: "
        "de ella cuelga la rotación entre divisas, metales y renta variable."
    ),
    "sello": "U.S. Department of the Treasury · FRED · Grupo Inteligencia",
    "activos": [
        ("Oro (XAU/USD)", -1, "compite con un bono que sí paga interés"),
        ("Nasdaq 100", -1, "descuenta sus ganancias futuras a esa tasa"),
    ],
}

_ETIQUETA_DIRECCION = {
    "sube": "Impulso comprador",
    "baja": "Presión vendedora",
    "lateral": "Sin sesgo claro",
}


def _direccion(signo: int, movimiento: int) -> str:
    """Dirección publicada = elasticidad del activo x movimiento medido del driver."""
    producto = signo * movimiento
    if producto > 0:
        return "sube"
    if producto < 0:
        return "baja"
    return "lateral"


def _movimiento(serie: list[float]) -> int:
    if len(serie) < 2 or serie[-1] == serie[-2]:
        return 0
    return 1 if serie[-1] > serie[-2] else -1


def _pct(valor: float, decimales: int = 2) -> str:
    return f"{valor:.{decimales}f}%".replace(".", ",")


def _bps(valor: float) -> str:
    """Puntos base con signo y coma decimal.

    El resto del mensaje ya va en notación chilena (las cifras del calendario
    pasan por `_cifra_es`); dejar los bps con punto deja dos notaciones
    conviviendo en el mismo texto.
    """
    signo = "+" if valor > 0 else ""
    return f"{signo}{valor:.1f}".replace(".", ",")


def _bloque_activos(pares: list[tuple[str, int, str]], mov: int) -> list[dict[str, Any]]:
    salida = []
    for nombre, signo, porque in pares:
        direccion = _direccion(signo, mov)
        salida.append({
            "nombre": nombre,
            "direccion": direccion,
            "etiqueta": _ETIQUETA_DIRECCION[direccion],
            "porque": porque,
        })
    return salida


def _payload_soberano(cfg: dict[str, Any]) -> dict[str, Any]:
    """Payload de contexto macro para los grupos que cuelgan de una tasa soberana."""
    serie_id = cfg["serie"]
    serie = _obtener_serie_continua_treasury(serie_id, 15)
    ultima_fecha = _ultima_fecha_treasury(serie_id)
    ultimo = serie[-1]
    promedio = round(sum(serie) / len(serie), 2)
    mov = _movimiento(serie)
    if mov > 0:
        titular = cfg["titular_sube"]
    elif mov < 0:
        titular = cfg["titular_baja"]
    else:
        titular = cfg["titular_plano"]

    return {
        "plantilla": "dato_macro",
        "chip_pais": cfg["chip_pais"],
        "fecha_hora": f"{_etiqueta_dia(ultima_fecha)} {ultima_fecha[:4]} · dato de cierre",
        "titular": titular,
        # Sin consenso publicado no hay veredicto. Comparar contra el promedio de la
        # propia serie y rotularlo "esperado" afirma una expectativa que nadie emitió.
        "veredicto": "",
        "veredicto_slug": "",
        "indicador": cfg["indicador"],
        "periodo": _periodo_desde(ultima_fecha, cfg["sufijo_periodo"]),
        "actual": _pct(ultimo),
        "esperado": "",
        "anterior": _pct(serie[-2]) if len(serie) >= 2 else "",
        "significado": cfg["significado"],
        "activos": _bloque_activos(cfg["activos"], mov),
        "recorrido": {
            "serie": serie,
            "marcadores": [
                {"indice": len(serie) - 1, "precio": ultimo, "clase": "actual",
                 "etiqueta": _pct(ultimo), "rol": "ÚLTIMO"},
            ],
            "niveles": [
                {"precio": promedio, "clase": "esperado", "etiqueta": _pct(promedio),
                 "rol": "PROMEDIO 15 RUEDAS"},
            ],
            "lienzo": "macro",
        },
        "sello_datos": cfg["sello"],
    }


def construir_payload_story_macro(
    grupo: str,
    eventos_grupo: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime,
) -> dict[str, Any]:
    """Construye el payload de contexto macro del grupo a partir de series oficiales."""
    # FOREX & DIVISAS: la actividad chilena (Imacec) manda sobre el peso.
    if grupo == "02_forex_divisas":
        barras = _obtener_historial_imacec()
        actual = barras[-1]["valor"]
        anterior = barras[-2]["valor"] if len(barras) >= 2 else None
        fecha_dato = barras[-1]["fecha"]
        if anterior is None or actual == anterior:
            mov = 0
        else:
            mov = 1 if actual > anterior else -1
        verbo = "se contrae" if actual < 0 else "avanza"
        mes_dato = _MESES_ES[_mes_numero(fecha_dato)].lower()

        return {
            "plantilla": "dato_macro",
            "chip_pais": "ECONOMÍA CHILE",
            "fecha_hora": f"{_etiqueta_dia(fecha_dato)} {fecha_dato[:4]} · dato oficial",
            "titular": f"La actividad económica de {mes_dato} {verbo} {_pct(abs(actual), 1)} anual",
            "veredicto": "",
            "veredicto_slug": "",
            "indicador": "Actividad Económica (Imacec)",
            "periodo": _periodo_desde(fecha_dato, "variación anual"),
            "actual": ("+" if actual > 0 else "") + _pct(actual, 1),
            "esperado": "",
            "anterior": (("+" if anterior > 0 else "") + _pct(anterior, 1)) if anterior is not None else "",
            "significado": (
                f"El Imacec mide cuánto produjo el país en el mes. La lectura de {mes_dato} "
                "define cuánta urgencia tiene el Banco Central para seguir bajando la tasa, "
                "y esa tasa es lo que hace más o menos atractivo al peso."
            ),
            "activos": _bloque_activos([
                ("USD/CLP", -1, "menos actividad adelanta recortes de tasa y le resta atractivo al peso"),
                ("IPSA", 1, "la bolsa local refleja el consumo y la inversión internos"),
            ], mov),
            "recorrido": {"barras": barras, "niveles": []},
            "sello_datos": "Banco Central de Chile · Grupo Inteligencia",
        }

    cfg = DRIVERS_SOBERANOS.get(grupo, DRIVER_SOBERANO_POR_DEFECTO)
    return _payload_soberano(cfg)


def asegurar_contexto_macro_grupo(
    grupo: str,
    destino_grupo: Path,
    eventos: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime | None = None,
) -> Path:
    """Verifica y genera deterministamente el contexto macro en la carpeta del grupo con su Story dato_macro."""
    ahora = ahora or datetime.now(tz=SANTIAGO)
    destino_grupo.mkdir(parents=True, exist_ok=True)

    archivo_contexto = destino_grupo / "contexto_macro.txt"
    archivo_con_prefijo = destino_grupo / "0_contexto_macro.txt"
    archivo_json = destino_grupo / "0_contexto_macro.json"
    archivo_png = destino_grupo / "0_contexto_macro.png"

    eventos_filtrados = filtrar_eventos_para_grupo(grupo, eventos)

    # Se renderiza ANTES de escribir el texto, porque el texto declara si hay imagen.
    imagen_lista = False
    if enriquecer and render_story and TEMPLATE_DATO_MACRO.exists():
        try:
            payload_macro = construir_payload_story_macro(grupo, eventos_filtrados, delta_ust_bps, ahora)
            archivo_json.write_text(json.dumps(payload_macro, ensure_ascii=False, indent=2), encoding="utf-8")
            payload_enriquecido = enriquecer(dict(payload_macro))
            render_story(payload_enriquecido, TEMPLATE_DATO_MACRO, archivo_png, formato="horizontal")
            shutil.copy(archivo_png, destino_grupo / "contexto_macro.png")
            imagen_lista = archivo_png.is_file()
        except DatosMacroNoDisponiblesError:
            # Falta la serie oficial: se propaga para que el pipeline se detenga.
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"AVISO: No se pudo renderizar la Story macro para {grupo}: {exc}", file=sys.stderr)

    texto = construir_texto_contexto_macro(
        grupo, eventos_filtrados, delta_ust_bps, ahora, con_imagen=imagen_lista
    )
    archivo_contexto.write_text(texto, encoding="utf-8")
    archivo_con_prefijo.write_text(texto, encoding="utf-8")

    return archivo_contexto
