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
import zlib
import shutil
import sys
from datetime import date, datetime, timezone
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
CALENDARIO_AGENDA_PATH = RAIZ / "data central" / "DATA AGENDA" / "calendario_2026.json"

try:
    # `_dias_habiles_entre` viene del mismo módulo a propósito: es el cálculo de
    # rezago que ya usa `get_curva_tasas`, y una segunda implementación acá
    # dejaría al texto y a la imagen midiendo la antigüedad del dato distinto.
    from market_data_mcp.curva_reader import _dias_habiles_entre, cargar_curva_tasas
except ImportError:
    cargar_curva_tasas = None
    _dias_habiles_entre = None

try:
    # La cotizacion del dia (decision del director, 2026-09-28): FRED llega con
    # dias de rezago y el carrusel publicaba la variacion de la semana pasada.
    from market_data_mcp.tasas_en_vivo import rendimientos_en_vivo
except ImportError:
    def rendimientos_en_vivo(series=(), descargar=None):  # type: ignore[no-redef]
        return {}

try:
    # El VIX y el DXY (2026-09-28): un indicador distinto por canal.
    from market_data_mcp.indices_referencia import serie_diaria
except ImportError:
    def serie_diaria(codigo, n=15, descargar=None):  # type: ignore[no-redef]
        return []

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
        # **Sin `nombre` a proposito.** No es un canal tematico: es el grupo de
        # Avisos de la comunidad, y su lectura macro ES el panorama general, sin
        # apellido. Aca vivia un nombre de canal que el director descarto el
        # 2026-09-03 por no existir en WhatsApp, y como este modulo redacta texto
        # de cliente, el 2026-09-04 un grupo real recibio una pregunta dirigida a
        # un canal que nadie puede abrir. Un test de contrato impide que vuelva.
        "sujeto": "el mercado",
        "paises": ("united states", "estados unidos", "chile", "euro zone", "zona euro", "china", "japan", "japon"),
        "foco": "Panorama macroeconómico intermercado, política monetaria y catalizadores de la sesión global.",
        "interpretacion": (
            "La curva soberana de EE.UU. es la referencia de precio del dinero en el mundo: de su "
            "trayectoria, junto con los datos de actividad y empleo, cuelga el apetito por riesgo y "
            "la rotación de flujos globales."
        ),
        # El canal de avisos lee el VIX (2026-09-28). Si su fuente no responde,
        # el canal cae al bono a 10 años, y ahí la lectura tiene que hablar de
        # tasas: por eso hay dos.
        "lectura": {
            "sube": "más cautela: el mercado le baja el apetito al riesgo y busca refugio.",
            "baja": "menos miedo: vuelve el apetito por riesgo a la bolsa y a las monedas emergentes.",
            "lateral": "volatilidad estable: el mercado se mueve por los datos del día.",
        },
        "lectura_respaldo": {
            "sube": "tasas al alza: el dólar gana fuerza y el mercado se vuelve más cauto con el riesgo.",
            "baja": "tasas a la baja: el dólar cede y los activos de riesgo toman aire.",
            "lateral": "tasas sin cambio: el mercado se mueve por los datos del día.",
        },
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
        "lectura": {
            "sube": "el dólar gana fuerza frente al euro, la libra y el peso chileno.",
            "baja": "el dólar pierde fuerza frente al euro, la libra y el peso chileno.",
            "lateral": "sin empuje nuevo desde las tasas: el dólar se mueve por los datos del día.",
        },
    },
    "03_commodities_materias_primas": {
        "nombre": "Commodities & Materias Primas",
        "paises": ("united states", "estados unidos", "china", "euro zone"),
        "patrones": ("inventories", "eia", "api", "opec", "crude", "petroleo", "copper", "cobre", "gold", "oro", "prices"),
        "foco": "Tasas del Tesoro de EE.UU., inventarios energéticos, demanda manufacturera industrial de China y tensiones geopolíticas.",
        "interpretacion": (
            "El rendimiento del bono a 10 años de EE.UU. es el costo de oportunidad del Oro (XAU/USD): "
            "compite con un metal que no paga interés. Los informes de inventarios de crudo marcan la "
            "pauta para la energía."
        ),
        "lectura": {
            "sube": "mantener oro y plata se encarece: presión a la baja sobre los metales.",
            "baja": "mantener oro y plata se abarata: alivio para los metales.",
            "lateral": "sin presión nueva desde las tasas sobre el oro y la plata.",
        },
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
        "lectura": {
            "sube": "presión sobre la bolsa, sobre todo en el Nasdaq 100.",
            "baja": "alivio para la bolsa, sobre todo en el Nasdaq 100.",
            "lateral": "sin presión nueva desde las tasas sobre la bolsa.",
        },
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
        "lectura": {
            "sube": "financiarse cuesta más: pesa sobre las tecnológicas y favorece a los bancos.",
            "baja": "financiarse cuesta menos: da aire a las tecnológicas y a las empresas con deuda.",
            "lateral": "sin cambio en el costo de financiarse de las empresas.",
        },
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
        "lectura": {
            "sube": "menos liquidez para el riesgo: presión sobre Bitcoin y Ethereum.",
            "baja": "más liquidez para el riesgo: alivio para Bitcoin y Ethereum.",
            "lateral": "liquidez sin cambio para Bitcoin y Ethereum.",
        },
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
    "IPC_BCCH": "https://si3.bcentral.cl/Siete/",
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


def _obtener_historial_ipc() -> list[dict[str, Any]]:
    """Últimas observaciones del IPC (variación mensual) desde data central/."""
    hist = _leer_serie(BCCH_DATA_PATH, ("series", "IPC_MENSUAL_VAR"), "IPC del BCCh")
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
    """Filtra y ordena los eventos macroeconómicos priorizando datos locales de Chile para Forex.

    Solo pasa el impacto alto (los 3 toros de Investing), decisión del director
    del 2026-09-28. El escáner sigue pidiendo impacto medio al calendario porque
    los blackouts lo necesitan: este filtro es de lo que se publica.
    """
    eventos = [ev for ev in eventos if ev.get("impacto") == "alto"]
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


def _es_dia_foco_chile(eventos_grupo: list[dict[str, Any]], ahora: datetime) -> bool:
    """Determina si hoy corresponde activar la tarjeta/bloque de foco local chileno en Forex.

    Se activa si:
    1. Hay un evento de alto impacto de Chile en la agenda del día (IPC, Imacec, TPM, IPoM).
    2. O la fecha de hoy coincide con un evento oficial de Chile en calendario_2026.json.
    3. O es el primer día hábil del mes (publicación habitual del Imacec).
    """
    for ev in eventos_grupo:
        pais = str(ev.get("pais", "")).lower()
        nombre = str(ev.get("nombre", "")).lower()
        if "chile" in pais and any(k in nombre for k in ("imacec", "cpi", "ipc", "interest rate", "tpm", "ipom", "actividad")):
            return True

    if CALENDARIO_AGENDA_PATH.exists():
        try:
            items = json.loads(CALENDARIO_AGENDA_PATH.read_text(encoding="utf-8"))
            hoy_str = ahora.strftime("%Y-%m-%d")
            for item in items:
                if str(item.get("pais", "")).upper() == "CHILE" and item.get("fecha_publicacion") == hoy_str:
                    return True
        except Exception:
            pass

    if ahora.day == 1 and ahora.weekday() < 5:
        return True

    return False


# Cuántos eventos entran en el mensaje antes de derivar al calendario completo.
# Más de seis y el bloque se come el "leer más" de WhatsApp, que es justo donde
# tiene que estar la lectura del canal.
MAX_EVENTOS_AGENDA = 6

_ESTADO_EMOJI = {"Publicado": "✅", "Concluido": "✅", "Pendiente": "🕐", "Sin cifra": "⚪"}


def _cifras_para_whatsapp(ev: dict[str, Any], ahora: datetime | None = None) -> str:
    """Las cifras del evento en una línea, en notación chilena.

    Es la versión de `_cifras_evento` del informe sin el markdown de tabla
    (`**`, `<br>`), que en WhatsApp se ve como basura. La conversión de notación
    sí se reutiliza: es la parte que importa y no puede divergir.
    """
    actual = _cifra_es(str(ev.get("actual") or "").strip())
    consenso = _cifra_es(str(ev.get("forecast") or "").strip())
    previo = _cifra_es(str(ev.get("previo") or "").strip())
    
    momento = None
    if ahora is not None and ev.get("hora_servidor"):
        try:
            momento = datetime.strptime(
                str(ev["hora_servidor"]).strip(), "%Y-%m-%d %H:%M"
            ).replace(tzinfo=SANTIAGO)
        except ValueError:
            pass

    if actual and consenso:
        return f"{actual} (se esperaba {consenso})"
    if actual:
        return actual
    if consenso:
        if momento is not None and momento <= ahora:
            return f"esperado {consenso} · pendiente de confirmación"
        return f"se espera {consenso}"
    if momento is not None and momento <= ahora:
        return "Concluido (impacto asimilado)"
    if previo:
        return f"anterior {previo}"
    return ""


def _bloque_agenda(eventos_grupo: list[dict[str, Any]], ahora: datetime) -> list[str]:
    """La agenda del día del canal, con el estado real de cada dato.

    El estado lo decide `_estado_evento`, cuyo testigo es la cifra publicada y no
    el reloj. Un dato que aún no sale se redacta en modo anticipación ("se
    espera"), nunca en pasado: es el guardrail anti-anacronismos del proyecto.
    Eventos de oradores o conferencias ya concluidos se reportan como tales.
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
        momento = None
        if ev.get("hora_servidor"):
            try:
                momento = datetime.strptime(
                    str(ev["hora_servidor"]).strip(), "%Y-%m-%d %H:%M"
                ).replace(tzinfo=SANTIAGO)
            except ValueError:
                pass

        if estado == "Sin cifra" and momento is not None and momento <= ahora:
            estado = "Concluido"

        hora = str(ev.get("hora_servidor", "")).split(" ")[-1] or "sin hora"
        pais = _PAISES_ES.get(str(ev.get("pais", "")), str(ev.get("pais", "")))
        cifras = _cifras_para_whatsapp(ev, ahora)
        cola = f": {cifras}" if cifras else ""
        lineas.append(f"{_ESTADO_EMOJI.get(estado, '⚪')} {hora} · {pais} · *{nombre}*{cola}")

    restantes = len(eventos_grupo) - len(visibles)
    if restantes > 0:
        lineas.append(f"…y {restantes} evento(s) más en el calendario completo.")
    lineas.append(f"🔗 Calendario económico: {CALENDARIO_URL}")
    lineas.append("━━━━━━━━━━━━━━━━━━━")
    return lineas


ROTULOS_TASA: dict[str, str] = {
    "DGS2": "Tasa a 2 años de EE.UU.",
    "DGS10": "Bono a 10 años de EE.UU.",
}

# Bajo 1 punto base el movimiento es ruido de cotizacion: publicarlo como alza o
# baja le pondria direccion a algo que no se movio.
UMBRAL_MOVIMIENTO_BPS = 1.0


def _delta_vigente(serie: dict[str, Any]) -> float | None:
    """El delta que `variacion_soberana` publica: 5 dias con rezago, 1 dia sin el."""
    d1, d5 = serie.get("delta_1d_bps"), serie.get("delta_5d_bps")
    rezago = serie.get("rezago_dias_habiles")
    if rezago is not None and rezago >= 2:
        return d5 if d5 is not None else d1
    return d1 if d1 is not None else d5


def _cotizacion_del_dia(serie_id: str, ahora: datetime) -> dict[str, Any] | None:
    """La cotizacion en vivo de la serie, solo si es de HOY en Chile.

    Una cotizacion de otro dia (fin de semana, feriado) no se publica como del dia:
    en ese caso se vuelve a FRED, que lleva su fecha a la vista.
    """
    vivo = rendimientos_en_vivo((serie_id,)).get(serie_id)
    if not vivo:
        return None
    if vivo["momento"].astimezone(SANTIAGO).date() != ahora.astimezone(SANTIAGO).date():
        return None
    return vivo


def _hora_chile(momento: datetime) -> str:
    return momento.astimezone(SANTIAGO).strftime("%H:%M")


ROTULOS_INDICE: dict[str, str] = {
    "VIX": "VIX, el índice de volatilidad de Wall Street",
    "DXY": "Dólar global (DXY)",
}


def _num(valor: float, decimales: int = 2) -> str:
    return f"{valor:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _var_pct(valor: float, decimales: int) -> str:
    signo = "+" if valor > 0 else ""
    return f"{signo}{valor:.{decimales}f}%".replace(".", ",")


def _lectura_indice(driver: dict[str, Any]) -> dict[str, Any] | None:
    """Ultimo valor del indice, su cierre previo, la variacion y hacia donde se movio."""
    puntos = serie_diaria(driver["serie"], 15)
    if len(puntos) < 2:
        return None
    (fecha, ultimo), (_, previo) = puntos[-1], puntos[-2]
    var = (ultimo / previo - 1) * 100 if previo else 0.0
    umbral = float(driver.get("umbral_mov", 0.0))
    mov = 1 if var >= umbral else (-1 if var <= -umbral else 0)
    if umbral == 0.0 and var == 0.0:
        mov = 0
    return {"puntos": puntos, "fecha": fecha, "ultimo": ultimo, "previo": previo,
            "var": var, "mov": mov}


def _bloque_tasa_del_canal(
    grupo: str, cfg: dict[str, Any], delta_ust_bps: float | None, ahora: datetime
) -> list[str]:
    """La tasa que mueve al canal y lo que significa, en dos lineas.

    La serie es la misma de la imagen (`DRIVERS_SOBERANOS`), asi texto e imagen
    hablan del mismo dato. Si la curva no la trae se cae al bono a 10 años, y si
    la curva no responde, al parametro `delta_ust_bps`. La direccion de la
    lectura sale del movimiento MEDIDO, nunca de una frase fija.
    """
    curva: dict[str, Any] = {}
    if cargar_curva_tasas:
        try:
            curva = cargar_curva_tasas("ALL").get("series", {}) or {}
        except Exception:  # noqa: BLE001
            curva = {}

    driver = DRIVERS_SOBERANOS.get(grupo, DRIVER_SOBERANO_POR_DEFECTO)
    lecturas_tasa = cfg.get("lectura_respaldo") or cfg.get("lectura") or (
        CONFIG_MACRO_GRUPOS["01_macro_y_apertura"]["lectura_respaldo"]
    )
    if driver.get("tipo") == "indice":
        indice = _lectura_indice(driver)
        if indice is not None:
            hoy = indice["fecha"] == ahora.astimezone(SANTIAGO).date()
            cuando = (
                f"hoy _(actualizado {ahora.astimezone(SANTIAGO):%H:%M} hrs Chile)_" if hoy
                else f"en el día _(cierre del {_etiqueta_dia(indice['fecha'].isoformat())})_"
            )
            clave = {1: "sube", -1: "baja", 0: "lateral"}[indice["mov"]]
            return [
                f"📊 *{ROTULOS_INDICE.get(driver['serie'], driver['serie'])}*: "
                f"{_num(indice['ultimo'])} · {_var_pct(indice['var'], driver.get('decimales_var', 1))} {cuando}",
                f"🎯 *Qué significa*: {cfg['lectura'][clave]}",
                "━━━━━━━━━━━━━━━━━━━",
            ]
        # Sin fuente del indice el canal no queda mudo: vuelve al bono a 10 años,
        # con la lectura de tasas y no la del indice.
        serie_id = "DGS10"
    else:
        serie_id = driver["serie"]
    rotulo = ROTULOS_TASA.get(serie_id, serie_id)

    # Primero la cotizacion del dia; FRED queda de respaldo, con su fecha.
    vivo = _cotizacion_del_dia(serie_id, ahora)
    if vivo is not None:
        delta = vivo["delta_1d_bps"]
        cambio = f" · {_bps(delta)} {UNIDAD_BPS} hoy" if delta is not None else ""
        lineas = [
            f"📈 *{rotulo}*: {_pct(vivo['valor'])}{cambio} "
            f"_(en vivo, {_hora_chile(vivo['momento'])} hrs Chile)_"
        ]
    else:
        serie = curva.get(serie_id) or {}
        if not serie:
            serie_id, serie = "DGS10", curva.get("DGS10") or {}
            rotulo = ROTULOS_TASA["DGS10"]
        if not serie and delta_ust_bps is not None:
            serie = {"delta_1d_bps": delta_ust_bps, "rezago_dias_habiles": 1}

        resultado = variacion_soberana(serie)
        if resultado is None:
            return []
        texto, fecha = resultado
        sufijo = f" _({fecha})_" if fecha else ""
        lineas = [f"📈 *{rotulo}*: {texto}{sufijo}"]
        delta = _delta_vigente(serie)

    lecturas = lecturas_tasa
    if delta is not None:
        if delta >= UMBRAL_MOVIMIENTO_BPS:
            clave = "sube"
        elif delta <= -UMBRAL_MOVIMIENTO_BPS:
            clave = "baja"
        else:
            clave = "lateral"
        lineas.append(f"🎯 *Qué significa*: {lecturas[clave]}")
    lineas.append("━━━━━━━━━━━━━━━━━━━")
    return lineas


CIERRES_MACRO: tuple[str, ...] = (
    "¿Cómo lo ves tú? Te leemos en el grupo.",
    "Vamos siguiendo el mercado durante la jornada.",
    "Si tienes dudas con la lectura, escríbele a tu analista.",
    "Seguimos atentos a lo que venga en la sesión.",
)


def _elegir_cierre(grupo: str, ahora: datetime) -> str:
    clave = f"{grupo}|{ahora.astimezone(SANTIAGO):%Y-%m-%d}".encode("utf-8")
    return CIERRES_MACRO[zlib.crc32(clave) % len(CIERRES_MACRO)]


def construir_texto_contexto_macro(
    grupo: str,
    eventos_grupo: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime,
    con_imagen: bool = True,
    piezas_de_niveles: int = 0,
) -> str:
    """Genera el mensaje de contexto macro diario en formato canónico de WhatsApp con enlaces institucionales.

    `piezas_de_niveles` son las piezas de activo que ese canal va a recibir en la
    misma tanda. Se pide explícito y su default es 0 porque el cierre las anuncia:
    prometerlas sin saber si existen es lo que llegó a un canal real el
    2026-09-04. Con 0 el default calla, que es el lado seguro del error.
    """
    cfg = CONFIG_MACRO_GRUPOS.get(grupo, {
        "nombre": grupo.replace("_", " ").title(),
        "foco": "Seguimiento macroeconómico de la jornada.",
        "interpretacion": "Seguimiento de factores fundamentales y técnicos de la sesión.",
    })
    # `nombre` es el apellido tematico del canal y **puede no haberlo**: el grupo
    # de Avisos no tiene tema. `sujeto` es de quien habla la interpretacion, que
    # en un canal tematico es su propio tema y en el de avisos es el mercado.
    nombre_grupo = cfg.get("nombre")
    sujeto = cfg.get("sujeto") or nombre_grupo or "el mercado"
    foco = cfg["foco"]
    interpretacion = cfg.get("interpretacion", foco)
    hora_str = ahora.strftime("%H:%M")

    encabezado = (
        f"📊 *CONTEXTO MACRO DIARIO · {nombre_grupo.upper()}*"
        if nombre_grupo
        else "📊 *CONTEXTO MACRO DIARIO*"
    )
    lineas = [
        encabezado,
        f"📅 {ahora.strftime('%d/%m/%Y')} · {hora_str} hrs hora Chile",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    # El calendario va PRIMERO (orden canónico del proyecto, issue #43): el
    # fundamental del día se comunica antes que la lectura de niveles.
    # Se vuelve a filtrar acá aunque el caller ya lo haya hecho: el filtro es
    # idempotente y así ningún caller futuro puede colar un evento de otro canal
    # en el mensaje de este grupo.
    lineas.extend(_bloque_agenda(filtrar_eventos_para_grupo(grupo, eventos_grupo), ahora))

    # PRIORIDAD CHILE EN FOREX & DIVISAS: cifras leídas de las series del BCCh
    # solo cuando hoy es día de publicación oficial de Chile o evento local.
    # Nunca se nombra un nivel de USD/CLP acá: el precio sale del motor en tiempo
    # de ejecución (REGLA 1), y este módulo no tiene acceso al MCP.
    if grupo == "02_forex_divisas" and _es_dia_foco_chile(eventos_grupo, ahora):
        try:
            barras_local = _obtener_historial_ipc()
            tipo_local = "IPC"
        except DatosMacroNoDisponiblesError:
            barras_local = _obtener_historial_imacec()
            tipo_local = "IMACEC"

        ultimo = barras_local[-1]
        previo = barras_local[-2] if len(barras_local) >= 2 else None
        mes_dato = _MESES_ES[_mes_numero(ultimo["fecha"])].lower()
        valor_txt = ("+" if ultimo["valor"] > 0 else "") + _pct(ultimo["valor"], 1)
        tpm_valor, tpm_fecha = _obtener_tpm_vigente()
        tpm_txt = _pct(tpm_valor, 2)

        if tipo_local == "IPC":
            verbo = "marcó un avance de" if ultimo["valor"] > 0 else "marcó una variación de"
            comparacion = ""
            if previo is not None:
                mes_previo = _MESES_ES[_mes_numero(previo["fecha"])].lower()
                previo_txt = ("+" if previo["valor"] > 0 else "") + _pct(previo["valor"], 1)
                if ultimo["valor"] < previo["valor"]:
                    comparacion = f" Se modera frente a {mes_previo} ({previo_txt})."
                elif ultimo["valor"] > previo["valor"]:
                    comparacion = f" Se acelera frente a {mes_previo} ({previo_txt})."
                else:
                    comparacion = f" Repite la lectura de {mes_previo} ({previo_txt})."

            lineas.extend([
                "🇨🇱 *FOCO LOCAL · INFLACIÓN (IPC)*",
                f"El IPC de {mes_dato} {verbo} {valor_txt} mensual.{comparacion}",
                f"🎯 Con la tasa del Banco Central (TPM) en {tpm_txt}, una inflación persistente "
                "frena los recortes y sostiene al peso frente al dólar.",
                f"🔗 Serie oficial IPC y TPM (BCCh, al {_etiqueta_dia(tpm_fecha)}): "
                f"{ENLACES_INSTITUCIONALES['IPC_BCCH']}",
                "━━━━━━━━━━━━━━━━━━━",
            ])
        else:
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

            lineas.extend([
                "🇨🇱 *FOCO LOCAL · ACTIVIDAD ECONÓMICA (IMACEC)*",
                f"El Imacec de {mes_dato} marcó {verbo} {valor_txt} anual.{comparacion}",
                f"🎯 Con la tasa del Banco Central (TPM) en {tpm_txt}, una actividad débil abre "
                "espacio a más recortes y le resta fuerza al peso; una sorpresa al alza, lo contrario.",
                f"🔗 Serie oficial Imacec y TPM (BCCh, al {_etiqueta_dia(tpm_fecha)}): "
                f"{ENLACES_INSTITUCIONALES['IMACEC_BCCH']}",
                "━━━━━━━━━━━━━━━━━━━",
            ])

    # Formato compacto (decision del director, 2026-09-28): una linea con el
    # indicador que mueve al canal y una con lo que significa para operar. Salieron la
    # curva en bloque, la tasa real TIPS, el "¿que significa?" generico y el
    # seguimiento de bancos centrales, que ademas narraba un tono ("mensaje de
    # cautela") que ninguna fuente habia medido.
    lineas.extend(_bloque_tasa_del_canal(grupo, cfg, delta_ust_bps, ahora))

    glosario_path = RAIZ / "data" / "glosario_siglas.json"
    if glosario_path.exists():
        try:
            glosario_dict = json.loads(glosario_path.read_text(encoding="utf-8"))
            texto_actual = "\n".join(lineas)
            siglas_encontradas = []
            for s, info in glosario_dict.items():
                if isinstance(info, dict) and re.search(rf"\b{re.escape(s)}\b", texto_actual, re.IGNORECASE):
                    exp = info.get("explicacion", "")
                    if exp:
                        siglas_encontradas.append((s, exp))
            if siglas_encontradas:
                lineas.append("🔤 *Diccionario rápido*")
                for s, exp in siglas_encontradas:
                    lineas.append(f"• {s}: {exp}")
                lineas.append("━━━━━━━━━━━━━━━━━━━")
        except Exception:
            pass
    # Solo se promete la imagen si efectivamente se produjo, y solo se prometen los
    # niveles si el canal los lleva: un texto que anuncia algo inexistente llega
    # roto al cliente. La segunda mitad de esa regla faltaba, y el motivo se ve en
    # el código que había acá: la frase de los niveles estaba escrita **dos veces**,
    # una por rama de `con_imagen`, así que al condicionar la imagen nadie notó que
    # la promesa de niveles quedaba incondicional en ambas. Ahora cada promesa es
    # una frase con su propia condición y no hay copia que se olvide.
    anuncios = []
    if con_imagen:
        anuncios.append("En la imagen adjunta va el gráfico de las últimas ruedas.")
    if piezas_de_niveles > 0:
        anuncios.append("Enseguida compartimos los niveles para operar la jornada.")
    if anuncios:
        lineas.append("💡 " + " ".join(anuncios))
    if piezas_de_niveles == 0:
        # Sin niveles el mensaje se quedaba sin cierre. Desde el 2026-09-28 el
        # cierre varia (desmecanizar el grupo, decision del director): siempre el
        # mismo se lee como plantilla. Estable por canal y dia, porque el despacho
        # compara la huella del texto aprobado.
        lineas.append(_elegir_cierre(grupo, ahora))

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


def _sello_frescura(fecha_iso: str) -> str:
    """Cómo se rotula en la IMAGEN la fecha del dato, según su rezago.

    "dato de cierre" se lee como el cierre de HOY. Con la serie rezagada eso le
    dice al cliente que el bono no se movió en cuatro días, que es lo contrario de
    lo que pasó. El 2026-09-14 la pieza salió al canal estampando "10 Sep 2026 ·
    dato de cierre" un lunes 14: FRED no tenía el viernes 11 y el último dato
    publicado era del jueves 10.

    El texto del mensaje ya distinguía los dos casos desde `variacion_soberana`
    (con rezago manda la variación de 5 días, con la fecha al lado) y por eso salió
    correcto. La imagen no miraba el rezago: dos caminos para el mismo dato y solo
    uno lo sabía, que es el defecto recurrente del repo.

    El umbral son los mismos dos días hábiles que usa el texto, para que la pieza
    no se contradiga consigo misma, y la noción de "hoy" es la de `curva_reader`
    (UTC) por la misma razón.
    """
    if _dias_habiles_entre is None:
        return "dato de cierre"
    try:
        rezago = _dias_habiles_entre(
            date.fromisoformat(fecha_iso), datetime.now(timezone.utc).date()
        )
    except ValueError:
        return "dato de cierre"
    return "último dato disponible" if rezago >= 2 else "dato de cierre"


# Cada grupo cuelga de UNA tasa soberana. `signo` es la elasticidad conocida del
# activo frente a esa tasa: +1 se mueve con ella, -1 en contra. La dirección que
# se publica sale de multiplicar ese signo por el movimiento MEDIDO de la serie,
# así que no queda ninguna afirmación direccional congelada en el código.
DRIVERS_SOBERANOS: dict[str, dict[str, Any]] = {
    # Un indicador distinto por canal (decision del director, 2026-09-28): los tres
    # canales recibian la misma imagen del bono y se leia repetitivo. El VIX y el
    # DXY no son tasas ni simbolos del broker: son `tipo: indice`, salen de
    # `indices_referencia` y, si su fuente cae, el canal vuelve al bono a 10 años.
    # `umbral_mov` es en porcentaje: bajo eso el movimiento es ruido.
    "01_macro_y_apertura": {
        "serie": "VIX",
        "tipo": "indice",
        "umbral_mov": 2.0,
        "decimales_var": 1,
        "chip_pais": "VOLATILIDAD · WALL STREET",
        "indicador": "VIX · índice de volatilidad",
        "sufijo_periodo": "cautela del mercado",
        "titular_sube": "El VIX sube: el mercado se pone más cauto con el riesgo",
        "titular_baja": "El VIX cede: vuelve el apetito por riesgo",
        "titular_plano": "El VIX se mantiene: la cautela del mercado no cambia",
        "significado": (
            "El VIX mide cuánto movimiento espera el mercado en la bolsa de EE.UU. para el "
            "próximo mes. Cuando sube hay más cautela; cuando baja, más apetito por riesgo."
        ),
        "sello": "Cboe · Grupo Inteligencia",
        "activos": [
            ("Nasdaq 100", -1, "la bolsa cae cuando crece la cautela"),
            ("Oro (XAU/USD)", 1, "se busca como refugio cuando sube la cautela"),
        ],
    },
    "02_forex_divisas": {
        "serie": "DXY",
        "tipo": "indice",
        "umbral_mov": 0.05,
        "decimales_var": 2,
        "chip_pais": "DÓLAR GLOBAL · FOREX",
        "indicador": "Dólar global (DXY)",
        "sufijo_periodo": "dólar contra seis monedas",
        "titular_sube": "El dólar global se fortalece y presiona a las demás monedas",
        "titular_baja": "El dólar global cede y da aire a las demás monedas",
        "titular_plano": "El dólar global se mantiene sin empuje nuevo",
        "significado": (
            "El DXY mide al dólar contra el euro, el yen, la libra y otras tres monedas. "
            "Si sube, el dólar gana fuerza en todo el mundo."
        ),
        "sello": "ICE · Grupo Inteligencia",
        "activos": [
            ("USD/CLP", 1, "un dólar global fuerte presiona al peso chileno"),
            ("EUR/USD", -1, "el euro es la mitad de la canasta del DXY"),
        ],
    },
    "03_commodities_materias_primas": {
        # Colgaba de la tasa real TIPS (DFII10) hasta el 2026-09-28, cuando el
        # director la saco del carrusel: el bono nominal a 10 años cuenta la misma
        # historia del costo de oportunidad sin una sigla mas que explicar.
        "serie": "DGS10",
        "chip_pais": "TESORO EE.UU. · METALES",
        "indicador": "Rendimiento Bono 10Y (UST 10Y)",
        "sufijo_periodo": "tasa soberana",
        "titular_sube": "El bono a 10 años de EE.UU. sube y encarece mantener metales sin rendimiento",
        "titular_baja": "El bono a 10 años de EE.UU. cede y alivia el costo de mantener metales",
        "titular_plano": "El bono a 10 años de EE.UU. se mantiene y deja al Oro sin impulso propio",
        "significado": (
            "El bono a 10 años es lo que rinde prestarle al gobierno de EE.UU. Cuando sube, "
            "guardar un metal que no paga interés cuesta más caro; cuando baja, cuesta menos."
        ),
        "sello": "U.S. Department of the Treasury · FRED · Grupo Inteligencia",
        "activos": [
            ("Oro (XAU/USD)", -1, "el bono que paga interés es su costo de oportunidad directo"),
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


# En palabras y no "bps": toda sigla de texto de cliente va explicada (issue #46),
# y en una linea de cifra no cabe la explicacion. Decision del 2026-09-28.
UNIDAD_BPS = "puntos básicos"


def _bps(valor: float) -> str:
    """Puntos base con signo y coma decimal.

    El resto del mensaje ya va en notación chilena (las cifras del calendario
    pasan por `_cifra_es`); dejar los bps con punto deja dos notaciones
    conviviendo en el mismo texto.
    """
    signo = "+" if valor > 0 else ""
    return f"{signo}{valor:.1f}".replace(".", ",")


def variacion_soberana(serie: dict[str, Any]) -> tuple[str, str] | None:
    """La variación publicable de una serie de la curva, con su fecha si hace falta.

    Devuelve `(texto, fecha)` o `None` si la serie no trae nada. `fecha` viene
    vacía cuando el dato es de hoy, porque ahí decirla es ruido.

    Existe porque el 2026-09-04 salió a cinco canales
    `Rendimiento Bono EE.UU. 10Y: *0,0 bps*`. Era **cierto y editorialmente
    falso**: el último dato era del 02-sep y el anterior del 01-sep, así que ese
    cero describía el movimiento de anteayer, se publicó el 04-sep sin fecha, y
    los 13 bps que el bono sí se movió en la semana estaban en el mismo JSON sin
    salir. `curva_reader` entrega once campos por serie y el consumidor leía uno.

    Tres reglas:

    1. **Con rezago de dos días hábiles o más manda la variación de 5 días**, con
       la fecha del dato al lado. Es la cifra que dice algo; la de 1 día compara
       dos días que ya pasaron.
    2. **Un `null` se dice, no se omite.** El código solo miraba `is not None`,
       así que un delta incalculable hacía desaparecer la línea, y con el bloque
       vacío se iba también el encabezado de la curva completo. `null` significa
       "no sé" y `0` significa "no se movió": callar es peor que el cero, porque
       el cero al menos se puede cuestionar.
    3. **Sin rezago manda la variación del día**, que es lo que el cliente espera
       cuando el dato es de hoy.
    """
    if not serie:
        return None

    d1 = serie.get("delta_1d_bps")
    d5 = serie.get("delta_5d_bps")
    rezago = serie.get("rezago_dias_habiles")
    fecha_iso = serie.get("fecha_dato")
    fecha = f"dato al {_etiqueta_dia(fecha_iso)}" if fecha_iso else ""

    if rezago is not None and rezago >= 2:
        if d5 is not None:
            return f"{_bps(d5)} {UNIDAD_BPS} en 5 días", fecha
        if d1 is not None:
            return f"{_bps(d1)} {UNIDAD_BPS}", fecha
        return "variación no disponible", fecha

    if d1 is not None:
        return f"{_bps(d1)} {UNIDAD_BPS}", ""
    if d5 is not None:
        return f"{_bps(d5)} {UNIDAD_BPS} en 5 días", fecha
    return "variación no disponible", fecha


def _linea_soberana(rotulo: str, serie: dict[str, Any]) -> str | None:
    """El bullet de una serie de la curva, o `None` si no hay serie."""
    resultado = variacion_soberana(serie)
    if resultado is None:
        return None
    texto, fecha = resultado
    sufijo = f" _({fecha})_" if fecha else ""
    return f"• {rotulo}: *{texto}*{sufijo}"


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


def _payload_soberano(cfg: dict[str, Any], ahora: datetime | None = None) -> dict[str, Any]:
    """Payload de contexto macro para los grupos que cuelgan de una tasa soberana."""
    serie_id = cfg["serie"]
    serie = _obtener_serie_continua_treasury(serie_id, 15)
    ultima_fecha = _ultima_fecha_treasury(serie_id)
    anterior = serie[-2] if len(serie) >= 2 else None
    mov = _movimiento(serie)
    fecha_hora = f"{_etiqueta_dia(ultima_fecha)} {ultima_fecha[:4]} · {_sello_frescura(ultima_fecha)}"
    sello = cfg["sello"]

    # La cotizacion del dia cierra la serie (decision del director, 2026-09-28):
    # sin ella la imagen terminaba en el ultimo dato de FRED, con dias de rezago.
    vivo = _cotizacion_del_dia(serie_id, ahora) if ahora is not None else None
    if vivo is not None and vivo["fecha"] > ultima_fecha:
        serie = serie[1:] + [round(vivo["valor"], 2)]
        ultima_fecha = vivo["fecha"]
        if vivo["cierre_previo"] is not None:
            anterior = round(vivo["cierre_previo"], 2)
        delta = vivo["delta_1d_bps"]
        mov = 0 if delta is None or abs(delta) < UMBRAL_MOVIMIENTO_BPS else (1 if delta > 0 else -1)
        fecha_hora = (
            f"{_etiqueta_dia(ultima_fecha)} {ultima_fecha[:4]} · en vivo "
            f"{_hora_chile(vivo['momento'])} hrs Chile"
        )
        # Corto a proposito: el pie va en una linea y a escala de celular.
        sello = "CNBC en vivo · FRED · Grupo Inteligencia"

    ultimo = serie[-1]
    promedio = round(sum(serie) / len(serie), 2)
    if mov > 0:
        titular = cfg["titular_sube"]
    elif mov < 0:
        titular = cfg["titular_baja"]
    else:
        titular = cfg["titular_plano"]

    return {
        "plantilla": "dato_macro",
        "chip_pais": cfg["chip_pais"],
        "fecha_hora": fecha_hora,
        "titular": titular,
        # Sin consenso publicado no hay veredicto. Comparar contra el promedio de la
        # propia serie y rotularlo "esperado" afirma una expectativa que nadie emitió.
        "veredicto": "",
        "veredicto_slug": "",
        "indicador": cfg["indicador"],
        "periodo": _periodo_desde(ultima_fecha, cfg["sufijo_periodo"]),
        "actual": _pct(ultimo),
        "esperado": "",
        "anterior": _pct(anterior) if anterior is not None else "",
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
        "sello_datos": sello,
    }


def construir_payload_story_macro(
    grupo: str,
    eventos_grupo: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime,
) -> dict[str, Any]:
    """Construye el payload de contexto macro del grupo a partir de series oficiales."""
    # FOREX & DIVISAS: foco local chileno solo en días de publicación o evento local
    if grupo == "02_forex_divisas" and _es_dia_foco_chile(eventos_grupo, ahora):
        try:
            barras = _obtener_historial_ipc()
            tipo_local = "IPC"
        except DatosMacroNoDisponiblesError:
            barras = _obtener_historial_imacec()
            tipo_local = "IMACEC"

        actual = barras[-1]["valor"]
        anterior = barras[-2]["valor"] if len(barras) >= 2 else None
        fecha_dato = barras[-1]["fecha"]
        if anterior is None or actual == anterior:
            mov = 0
        else:
            mov = 1 if actual > anterior else -1
        mes_dato = _MESES_ES[_mes_numero(fecha_dato)].lower()

        if tipo_local == "IPC":
            verbo = "sube a" if actual > 0 else "cae a"
            return {
                "plantilla": "dato_macro",
                "chip_pais": "INFLACIÓN CHILE",
                "fecha_hora": f"{_etiqueta_dia(fecha_dato)} {fecha_dato[:4]} · dato oficial",
                "titular": f"La inflación de {mes_dato} {verbo} {_pct(actual, 1)} mensual",
                "veredicto": "",
                "veredicto_slug": "",
                "indicador": "Inflación Mensual (IPC Chile)",
                "periodo": _periodo_desde(fecha_dato, "variación mensual"),
                "actual": ("+" if actual > 0 else "") + _pct(actual, 1),
                "esperado": "",
                "anterior": (("+" if anterior > 0 else "") + _pct(anterior, 1)) if anterior is not None else "",
                "significado": (
                    f"El IPC de {mes_dato} define el margen del Banco Central de Chile para seguir bajando la TPM. "
                    "Una inflación persistente sostiene las tasas locales y respalda al peso frente al dólar."
                ),
                "activos": _bloque_activos([
                    ("USD/CLP", -1, "tasas locales firmes por inflación defienden al peso chileno frente al dólar"),
                    ("Renta Fija / UF", 1, "los activos indexados capturan el mayor devengo por reajuste inflacionario"),
                ], mov),
                "recorrido": {"barras": barras, "niveles": []},
                "sello_datos": "Instituto Nacional de Estadísticas · Banco Central de Chile · Grupo Inteligencia",
            }
        else:
            verbo = "se contrae" if actual < 0 else "avanza"
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
    if cfg.get("tipo") == "indice":
        payload = _payload_indice(cfg, ahora)
        if payload is not None:
            return payload
        cfg = DRIVER_SOBERANO_POR_DEFECTO
    return _payload_soberano(cfg, ahora)


def _payload_indice(cfg: dict[str, Any], ahora: datetime) -> dict[str, Any] | None:
    """Payload de la imagen para un canal que cuelga de un indice (VIX, DXY)."""
    indice = _lectura_indice(cfg)
    if indice is None:
        return None
    serie = [round(v, 2) for _, v in indice["puntos"]]
    fecha_iso = indice["fecha"].isoformat()
    ahora_cl = ahora.astimezone(SANTIAGO)
    if indice["fecha"] == ahora_cl.date():
        fecha_hora = f"{_etiqueta_dia(fecha_iso)} {fecha_iso[:4]} · actualizado {ahora_cl:%H:%M} hrs Chile"
    else:
        fecha_hora = f"{_etiqueta_dia(fecha_iso)} {fecha_iso[:4]} · último cierre"
    titular = {1: cfg["titular_sube"], -1: cfg["titular_baja"], 0: cfg["titular_plano"]}[indice["mov"]]
    promedio = round(sum(serie) / len(serie), 2)
    ultimo = serie[-1]
    return {
        "plantilla": "dato_macro",
        "chip_pais": cfg["chip_pais"],
        "fecha_hora": fecha_hora,
        "titular": titular,
        "veredicto": "",
        "veredicto_slug": "",
        "indicador": cfg["indicador"],
        "periodo": _periodo_desde(fecha_iso, cfg["sufijo_periodo"]),
        "actual": _num(ultimo),
        "esperado": "",
        "anterior": _num(round(indice["previo"], 2)),
        "significado": cfg["significado"],
        "activos": _bloque_activos(cfg["activos"], indice["mov"]),
        "recorrido": {
            "serie": serie,
            "marcadores": [
                {"indice": len(serie) - 1, "precio": ultimo, "clase": "actual",
                 "etiqueta": _num(ultimo), "rol": "ÚLTIMO"},
            ],
            "niveles": [
                {"precio": promedio, "clase": "esperado", "etiqueta": _num(promedio),
                 "rol": "PROMEDIO 15 RUEDAS"},
            ],
            "lienzo": "macro",
        },
        "sello_datos": cfg["sello"],
    }


def asegurar_contexto_macro_grupo(
    grupo: str,
    destino_grupo: Path,
    eventos: list[dict[str, Any]],
    delta_ust_bps: float | None,
    ahora: datetime | None = None,
    piezas_de_niveles: int = 0,
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
        grupo, eventos_filtrados, delta_ust_bps, ahora,
        con_imagen=imagen_lista, piezas_de_niveles=piezas_de_niveles,
    )
    archivo_contexto.write_text(texto, encoding="utf-8")
    archivo_con_prefijo.write_text(texto, encoding="utf-8")

    return archivo_contexto
