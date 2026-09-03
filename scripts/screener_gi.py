#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Escáner del universo para las tandas diarias: puntúa activos y elige el Top N.

Implementa el `Score_GI` del plan de producción diaria con tres correcciones que
el plan original necesitaba para no producir resultados falsos.

**1. El score topa en 100, no en 26,5.** El plan multiplica pesos
(0,35 / 0,25 / 0,20 / 0,20) por factores que YA vienen escalados a su máximo
(T∈[0,35], M∈[0,25], C∈[0,20], F∈[0,20], que suman 100). Ese producto da
0,35×35 + 0,25×25 + 0,20×20 + 0,20×20 = 26,5, así que ningún activo podía pasar
de un cuarto del puntaje y la escala "sobre 100" era ilegible. Los rangos de
puntos SON la ponderación: `Score = T + M + C + F`.

**2. Las prohibiciones del Playbook son gates, no puntos.** La skill cuantitativa
§1 y el Playbook §2 son prohibitivos: en R1/R3 está prohibido abrir cortos en Oro
"aun con RSI sobrecomprado en 80". Con scoring puro, un setup prohibido puede
sacar 60 puntos y ganar la tanda. Acá se filtran ANTES de puntuar.

**3. Los blackouts por calendario existen.** La skill §4 define ventanas de
bloqueo alrededor de los datos de alto impacto, y el Factor Catalizador del plan
premia con +25 justo al activo que recibe el dato del día: sin el gate, el plan
elige preferentemente lo que no debería tocar. Las tandas de media mañana y de
media tarde caen dentro de esas ventanas con frecuencia.

Los indicadores salen de `market_data_mcp.analisis.analizar_activo`, la misma
función que alimenta la tool `get_asset_levels`. No se recalculan acá: el repo ya
tiene dos tuberías con la misma materia prima y distinta profundidad, y esta
habría sido la tercera.

Uso:
    uv run --with MetaTrader5 python scripts/screener_gi.py
    uv run --with MetaTrader5 python scripts/screener_gi.py --tanda 2 --top 3
    uv run --with MetaTrader5 python scripts/screener_gi.py --todos --json
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from market_data_mcp.analisis import analizar_activo  # noqa: E402
from market_data_mcp.tools.symbol_spec import _TICKER_EXCHANGE, _cargar_feriados  # noqa: E402

NY = ZoneInfo("America/New_York")
SANTIAGO = ZoneInfo("America/Santiago")

ACTIVOS_JSON = RAIZ / "config" / "activos.json"
PLAYBOOK_CONFIG = RAIZ / "config" / "playbook_config.yaml"


def _umbral_confianza() -> float:
    """El piso de confianza, del YAML que el Playbook hashea.

    Se lee del config y no se escribe aca para que un cambio de criterio quede
    registrado en el `config_hash` del snapshot. El default reproduce el valor
    real y solo aplica si el archivo falta.
    """
    try:
        import yaml

        cfg = yaml.safe_load(PLAYBOOK_CONFIG.read_text(encoding="utf-8")) or {}
        return float(cfg.get("confidence_weights", {}).get("umbral_minimo_pct", 65.0))
    except Exception:  # noqa: BLE001
        return 65.0


UMBRAL_CONFIANZA_PCT = _umbral_confianza()
DIR_SALIDA = RAIZ / "data" / "screener"


# ─────────────────────────────────────────────────────────────────────────────
# Sesiones de mercado continuas y tandas de referencia
# ─────────────────────────────────────────────────────────────────────────────
# El escáner opera de forma responsiva las 24 horas del día. La referencia es
# el ciclo global de mercado anclado a Nueva York, derivando la hora de Chile
# en tiempo real para comunicarla.
SESIONES: dict[str, dict[str, Any]] = {
    "asiatica": {
        "nombre": "Sesión Asiática / Pacífico",
        "tanda": 3,
        "foco": "Foco en activos de Asia, JPY, Oro, Cobre, Cripto y materias primas",
    },
    "europea": {
        "nombre": "Sesión Europea / Londres",
        "tanda": 1,
        "foco": "Quiebres de apertura europea, EUR, GBP, DAX y posicionamiento previo a EE.UU.",
    },
    "apertura_ny": {
        "nombre": "Apertura Wall Street",
        "tanda": 1,
        "foco": "Volatilidad de primera hora, quiebres intradía y catalizadores macro",
    },
    "tarde_ny": {
        "nombre": "Rotación de Tarde Wall Street",
        "tanda": 2,
        "foco": "Flujos vespertinos, rebalanceo institucional y continuidad de tendencia",
    },
    "cierre_ny": {
        "nombre": "Cierre Wall Street / Post-Mercado",
        "tanda": 3,
        "foco": "Balance de la sesión americana, resultados corporativos y preparación para Asia",
    },
    "fin_de_semana": {
        "nombre": "Fin de Semana / Cripto & Pre-Apertura",
        "tanda": 1,
        "foco": "Mercado OTC/Cripto y preparación estratégica para la apertura semanal",
    },
}

TANDAS: dict[int, dict[str, Any]] = {
    1: {
        "nombre": "Apertura Wall Street",
        "hora_ny": (10, 30),
        "foco": "Volatilidad y quiebres de la primera hora",
    },
    2: {
        "nombre": "Rotación de tarde",
        "hora_ny": (14, 30),
        "foco": "Flujos vespertinos, sin repetir la tesis de la mañana",
    },
    3: {
        "nombre": "Pre-cierre y sesión asiática",
        "hora_ny": (16, 45),
        "foco": "Balance de la sesión y preparación de Asia",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Blackouts por calendario (skill trading-cuantitativo-intermercado §4)
# ─────────────────────────────────────────────────────────────────────────────
# Ojo con la zona horaria: la skill nombra la zona del organismo emisor, pero
# `obtener_calendario_macro` YA entrega `hora_servidor` convertida a
# America/Santiago. Volver a convertir sería un doble ajuste, que es exactamente
# el error de ±1 h que el proyecto ya cometió una vez (issue #38). Las ventanas
# son minutos relativos al evento, así que se comparan directo en hora de Chile.
#
# `alcance` = "TODOS" significa que el evento mueve el dólar global y por tanto a
# todo activo cotizado en dólares, que es el catálogo entero. No es pereza: un
# FOMC no deja quieto a ningún activo del universo.
#
# LOS NOMBRES VAN EN INGLÉS porque así los publica la fuente. Verificado contra
# `obtener_calendario_macro` el 2026-08-25: devuelve "United States",
# "Nonfarm Payrolls", "Crude Oil Inventories". La primera versión de esta tabla
# estaba escrita en español y por eso NINGÚN blackout se activaba nunca, en
# silencio y con el escáner informando "0 exclusiones". Los alias en español
# quedan por si la fuente cambia de locale; el test de patrones es lo que
# garantiza que sigan calzando.
#
# `paises` acota la regla: sin él, un "CPI (MoM)" de Chile activaría el blackout
# de alcance TODOS que corresponde solo al IPC de EE.UU.
_BLACKOUTS: tuple[dict[str, Any], ...] = (
    {
        "etiqueta": "FOMC / decisión de la Fed",
        "paises": ("united states",),
        "patrones": ("fed interest rate decision", "fomc statement", "fomc press conference",
                     "fomc economic projections", "federal funds rate",
                     "decision de tipos de interes de la fed"),
        "antes_min": 30, "despues_min": 75, "alcance": "TODOS",
    },
    {
        "etiqueta": "Nóminas no agrícolas (NFP)",
        "paises": ("united states",),
        "patrones": ("nonfarm payrolls", "private nonfarm payrolls", "nominas no agricolas"),
        "antes_min": 15, "despues_min": 30, "alcance": "TODOS",
    },
    {
        "etiqueta": "IPC de EE.UU.",
        "paises": ("united states",),
        "patrones": ("cpi (mom)", "cpi (yoy)", "core cpi", "cpi index",
                     "ipc de ee.uu."),
        "antes_min": 15, "despues_min": 30, "alcance": "TODOS",
    },
    {
        "etiqueta": "Reunión de política monetaria del Banco Central de Chile",
        "paises": ("chile",),
        "patrones": ("interest rate decision", "monetary policy",
                     "tasa de politica monetaria"),
        "antes_min": 15, "despues_min": 45, "alcance": "USDCLP",
    },
    {
        "etiqueta": "Imacec / IPC de Chile",
        "paises": ("chile",),
        "patrones": ("imacec", "cpi", "ipc de chile"),
        "antes_min": 15, "despues_min": 20, "alcance": "USDCLP",
    },
    # Japón no aparece en esta fuente: `obtener_calendario_macro` cubre Chile,
    # EE.UU., China y Zona Euro. La regla queda escrita porque la skill la define
    # y el USD/JPY se cubre por pedido del director, pero hoy no se puede activar
    # desde acá. Para una decisión del BoJ hay que mirar el calendario a mano, con
    # la salveditud de que cae el día ANTERIOR en Chile (13 h de diferencia).
    {
        "etiqueta": "Decisión de tasas del Banco de Japón",
        "paises": ("japan", "japon"),
        "patrones": ("boj interest rate decision", "bank of japan", "boj monetary policy"),
        "antes_min": 30, "despues_min": 60, "alcance": "USDJPY",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Qué activo "recibe" el dato de cada país
# ─────────────────────────────────────────────────────────────────────────────
# Primera aproximación deliberada, por país del evento. El mecanismo fino es
# `config/drivers.json`, que mapea activo -> drivers con su elasticidad, y usarlo
# acá exigiría invertir ese mapa y resolver sinónimos de nombres de indicador.
# Queda como mejora; mientras tanto, el país ya separa lo que importa: un Imacec
# no le habla al Nasdaq y un NFP no le habla al peso chileno del mismo modo.
# Las claves van en inglés y con el nombre EXACTO que publica la fuente
# ("United States", "Euro Zone"), por lo mismo que los patrones de blackout. Los
# alias en español quedan como respaldo de locale.
_RECEPTORES_POR_PAIS: dict[str, tuple[str, ...]] = {
    "united states": ("US100.spot", "US500.spot", "US30.spot", "XAUUSD", "XAGUSD",
                      "WTI.spot", "USDIDX", "QQQ.US", "SPY.US", "IWM.US", "SOXX.US",
                      "GLD.US"),
    "estados unidos": ("US100.spot", "US500.spot", "US30.spot", "XAUUSD", "XAGUSD",
                       "WTI.spot", "USDIDX", "QQQ.US", "SPY.US", "IWM.US", "SOXX.US",
                       "GLD.US"),
    "chile": ("USDCLP",),
    "china": ("COPPER", "WTI.spot"),
    "euro zone": ("EURUSD", "GER40.spot"),
    "zona euro": ("EURUSD", "GER40.spot"),
    "japan": ("USDJPY",),
    "united kingdom": ("GBPUSD",),
}

# Eventos de segundo orden que puntúan menos (el +15 del plan). También en
# inglés: "Crude Oil Inventories", "FOMC Member Barkin Speaks", "2-Year Note
# Auction" son los nombres reales observados en la fuente.
_PATRONES_SEGUNDO_ORDEN = (
    "inventories", "eia ", "opec", "speaks", "auction", "earnings",
    "inventarios", "discurso", "resultados",
)


# ─────────────────────────────────────────────────────────────────────────────
# Prohibiciones del Playbook, clasificadas por dirección
# ─────────────────────────────────────────────────────────────────────────────
# El snapshot del motor trae `setups_prohibidos` como vocabulario controlado
# (SHORT_AGRESIVO, BUY_THE_DIP_AGGRESSIVE, FADE_TOP_RESISTANCE...). Un token
# prohibido solo bloquea si apunta en la MISMA dirección que la lectura técnica:
# que esté prohibido comprar agresivamente no impide comunicar una caída.
#
# El mapa es EXHAUSTIVO y se compara por igualdad, no por substring. La versión
# anterior eran dos tuplas de fragmentos y dejó dos huecos que nadie vio: el
# `BREAKOUT_CHASE_LONG` que el motor emite para USD/CLP en R0 (donde el Playbook
# y la skill §4 prohíben perseguir quiebres) y el `FADE_TOP_RESISTANCE`, que
# estaba citado acá arriba como ejemplo de lo que el gate capturaba y no
# capturaba. Con substrings la omisión es invisible; con un mapa exhaustivo,
# `test_todo_token_del_motor_esta_clasificado_en_el_escaner` la detecta.
#
# `None` significa "prohíbe una FORMA de operar, no un lado del mercado": no se
# opone a ninguna lectura técnica y por eso no bloquea.
_DIRECCION_PROHIBIDA: dict[str, str | None] = {
    # Bloquean una lectura BAJISTA
    "SHORT_AGRESIVO": "BAJISTA",
    "VENTA_CONTRA_TENDENCIA": "BAJISTA",
    "SHORT_FADE_OVERBOUGHT": "BAJISTA",
    "SHORT_FADE": "BAJISTA",
    "FADE_TOP_RESISTANCE": "BAJISTA",
    # Bloquean una lectura ALCISTA
    "BUY_THE_DIP_AGGRESSIVE": "ALCISTA",
    "COMPRA_SIN_CONFIRMACION": "ALCISTA",
    "LONG_INVERTIDO": "ALCISTA",
    "LONG_SWING_FADE": "ALCISTA",
    "BREAKOUT_CHASE_LONG": "ALCISTA",
    # Sin dirección
    "BREAKOUT_CHASE": None,
    "GRID_SIN_STOP": None,
    "MEAN_REVERSION_RSI_H1": None,
    "FADE_SUPPORT_RESISTANCE_M15": None,
}


def _normalizar(texto: str) -> str:
    """Minúsculas sin tildes, para comparar nombres de evento de forma estable."""
    sin_tilde = unicodedata.normalize("NFKD", texto)
    sin_tilde = "".join(c for c in sin_tilde if not unicodedata.combining(c))
    return sin_tilde.lower().strip()


# ─────────────────────────────────────────────────────────────────────────────
# Universo
# ─────────────────────────────────────────────────────────────────────────────
def cargar_universo(solo_renderizables: bool = True) -> list[dict[str, Any]]:
    """Los activos del catálogo con lo que el escáner necesita de cada uno.

    `solo_renderizables` filtra por presencia del campo `imagen`. Ese campo es el
    interruptor del activo: solo se rellena cuando el `.jpg` existe en disco, y
    sin imagen el renderer detiene la pieza (fail-fast deliberado). Escanear un
    activo que después no se puede publicar es trabajo tirado.
    """
    data = json.loads(ACTIVOS_JSON.read_text(encoding="utf-8"))
    universo: list[dict[str, Any]] = []

    def agregar(a: dict[str, Any], clase: str) -> None:
        universo.append({
            "ticker": a["ticker_mt5"],
            "nombre": a.get("nombre", a["ticker_mt5"]),
            "clase": clase,
            "categoria": a.get("categoria", clase),
            "digits": a.get("digits", 2),
            # Moneda en que cotiza, para rotular distancias de precio en la
            # pieza. Sin default a proposito: un "USD" supuesto sobre el USD/CLP
            # rotularia pesos como dolares, y un rotulo equivocado se lee peor
            # que uno ausente. `preparar()` excluye al activo si falta.
            "unidad": a.get("unidad"),
            "imagen": a.get("imagen"),
        })

    for a in data.get("forex_commodities", []):
        agregar(a, "crypto" if a.get("categoria") == "crypto" else "forex_commodities")
    for a in data.get("indices", []):
        agregar(a, "indices")
    for a in data.get("etfs", {}).get("componentes", []):
        agregar(a, "etfs")
    # `acciones` se agrupa por sector, y cada sector es un dict con metadatos del
    # sector más su lista `componentes`. No es una lista plana como
    # `forex_commodities`, ni un dict único con `componentes` como `etfs`: son
    # tres formas distintas en el mismo archivo y hay que recorrer las tres.
    for sector in data.get("acciones", {}).values():
        if not isinstance(sector, dict):
            continue
        for a in sector.get("componentes", []):
            agregar(a, "acciones")

    if solo_renderizables:
        universo = [a for a in universo if a.get("imagen")]
    return universo


def filtrar_por_grupo(universo: list[dict[str, Any]], grupo: str) -> list[dict[str, Any]]:
    """Filtra los activos del universo por grupo modular de WhatsApp o alias de categoría."""
    slug = grupo.lower().strip()
    alias = {
        "fx": "forex",
        "forex": "forex",
        "divisas": "forex",
        "dolar": "forex",
        "commodities": "commodity",
        "commodity": "commodity",
        "materias_primas": "commodity",
        "metales": "commodity",
        "energia": "commodity",
        "indices": "indice",
        "indice": "indice",
        "wallstreet": "indice",
        "acciones": "accion",
        "accion": "accion",
        "etf": "accion",
        "etfs": "accion",
        "equities": "accion",
        "crypto": "crypto",
        "cripto": "crypto",
        "criptomonedas": "crypto",
        "02_forex_divisas": "forex",
        "03_commodities_materias_primas": "commodity",
        "04_indices_bursatiles": "indice",
        "05_acciones_etfs": "accion",
        "06_criptoactivos": "crypto",
    }
    objetivo = alias.get(slug, slug)

    filtrados = []
    for a in universo:
        cat = a.get("categoria", "").lower()
        clase = a.get("clase", "").lower()
        if objetivo == "forex" and (cat == "forex" or a["ticker"] in ("USDCLP", "EURUSD", "USDJPY", "GBPUSD", "USDIDX")):
            filtrados.append(a)
        elif objetivo == "commodity" and (cat in ("commodity", "commodities") or (clase == "forex_commodities" and cat not in ("forex", "crypto"))):
            filtrados.append(a)
        elif objetivo == "crypto" and (cat == "crypto" or clase == "crypto"):
            filtrados.append(a)
        elif objetivo == "indice" and (cat in ("indice", "indices") or clase == "indices"):
            filtrados.append(a)
        elif objetivo == "accion" and (cat in ("accion", "acciones", "etf", "etfs") or clase in ("acciones", "etfs")):
            filtrados.append(a)
    return filtrados


# ─────────────────────────────────────────────────────────────────────────────
# Detección de sesión y tandas
# ─────────────────────────────────────────────────────────────────────────────
def detectar_sesion(ahora_ny: datetime | None = None) -> dict[str, Any]:
    """Detecta dinámicamente la sesión activa del mercado según la hora en Nueva York.

    Permite que el carrusel sea responsivo a cualquier hora de ejecución las 24 horas del día.
    """
    ahora = ahora_ny or datetime.now(tz=NY)
    dow = ahora.weekday()  # 0=Lunes, ..., 5=Sábado, 6=Domingo
    minutos_dia = ahora.hour * 60 + ahora.minute

    # Sábado completo o Domingo antes de las 18:00 NY (apertura semanal)
    if dow == 5 or (dow == 6 and minutos_dia < 18 * 60):
        slug = "fin_de_semana"
    # 02:00 (120 min) a 08:30 (510 min) -> Europa / Londres
    elif 2 * 60 <= minutos_dia < 8 * 60 + 30:
        slug = "europea"
    # 08:30 (510 min) a 12:30 (750 min) -> Apertura Wall Street
    elif 8 * 60 + 30 <= minutos_dia < 12 * 60 + 30:
        slug = "apertura_ny"
    # 12:30 (750 min) a 15:30 (930 min) -> Rotación Tarde Wall Street
    elif 12 * 60 + 30 <= minutos_dia < 15 * 60 + 30:
        slug = "tarde_ny"
    # 15:30 (930 min) a 18:00 (1080 min) -> Cierre Wall Street / Post-Mercado
    elif 15 * 60 + 30 <= minutos_dia < 18 * 60:
        slug = "cierre_ny"
    # 18:00 (1080 min) a 24:00 o 00:00 a 02:00 -> Asia / Pacífico
    else:
        slug = "asiatica"

    datos_sesion = SESIONES[slug]
    return {
        "slug": slug,
        "nombre": datos_sesion["nombre"],
        "tanda": datos_sesion["tanda"],
        "foco": datos_sesion["foco"],
        "hora_real_ny": ahora.strftime("%H:%M"),
        "hora_real_chile": ahora.astimezone(SANTIAGO).strftime("%H:%M"),
    }


def tanda_vigente(ahora_ny: datetime | None = None) -> int:
    """La tanda correspondiente según la sesión detectada o el ancla más cercana."""
    ahora = ahora_ny or datetime.now(tz=NY)
    sesion = detectar_sesion(ahora)
    return sesion.get("tanda", 1)


def hora_chile_de_tanda(n: int, dia_ny: datetime | None = None) -> str:
    """El ancla de la tanda, expresada en hora de Chile para comunicarla."""
    base = dia_ny or datetime.now(tz=NY)
    if n not in TANDAS:
        return base.astimezone(SANTIAGO).strftime("%H:%M")
    h, m = TANDAS[n]["hora_ny"]
    ancla_ny = base.replace(hour=h, minute=m, second=0, microsecond=0)
    return ancla_ny.astimezone(SANTIAGO).strftime("%H:%M")


# ─────────────────────────────────────────────────────────────────────────────
# Gates (prohibiciones, no puntos)
# ─────────────────────────────────────────────────────────────────────────────
def gate_feriado(ticker: str, fecha) -> str | None:
    """Excluye si el activo cotiza en una bolsa que hoy está de feriado.

    Reusa el mapa y el calendario que ya usa `get_symbol_spec`. Los activos 24/7
    (criptos) y los OTC (FX, metales) no mapean a ninguna bolsa y nunca caen acá,
    que es la limitación ya documentada en esa tool.
    """
    exchange = _TICKER_EXCHANGE.get(ticker)
    if not exchange:
        return None
    feriados = _cargar_feriados().get(exchange, [])
    if fecha.isoformat() in feriados:
        return f"feriado de {exchange}"
    return None


def gate_blackout(
    ticker: str,
    eventos: list[dict[str, Any]],
    ahora_santiago: datetime,
) -> str | None:
    """Excluye si hay una ventana de bloqueo activa que alcance a este activo."""
    for ev in eventos:
        nombre = _normalizar(ev.get("nombre", ""))
        pais = _normalizar(ev.get("pais", ""))
        try:
            hora_ev = datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(
                tzinfo=SANTIAGO
            )
        except (KeyError, ValueError):
            continue

        for bl in _BLACKOUTS:
            if pais not in bl["paises"]:
                continue
            if not any(p in nombre for p in bl["patrones"]):
                continue
            if bl["alcance"] != "TODOS" and bl["alcance"] != ticker:
                continue
            inicio = hora_ev - timedelta(minutes=bl["antes_min"])
            fin = hora_ev + timedelta(minutes=bl["despues_min"])
            if inicio <= ahora_santiago <= fin:
                return (
                    f"blackout por {bl['etiqueta']} "
                    f"({inicio.strftime('%H:%M')}-{fin.strftime('%H:%M')} hora Chile)"
                )
    return None


def gate_playbook(direccion: str, sesgo: dict[str, Any] | None) -> str | None:
    """Excluye si el Playbook prohíbe operar en la dirección que da la técnica.

    Solo aplica a los 5 activos con ficha. El resto del catálogo no tiene régimen
    ni setups permitidos, y no se le inventan: entrar al catálogo técnico no es
    entrar al Playbook.
    """
    if not sesgo or "error" in sesgo:
        return None
    activo = sesgo.get("activo") or {}
    prohibidos = activo.get("setups_prohibidos") or []
    regimen = (sesgo.get("regimen_macro_global") or {}).get("codigo", "?")
    for token in prohibidos:
        clave = token.upper()
        if clave not in _DIRECCION_PROHIBIDA:
            # Un token sin clasificar es mas probable que sea una prohibicion real
            # a que sea inocuo. No publicar un activo cuesta una pieza; publicar
            # contra el Playbook cuesta el metodo. El escaner informa el motivo,
            # asi que la exclusion queda auditada y no desaparece en silencio.
            return f"el Playbook prohibe {token} en {regimen} (sin clasificar en el escaner)"
        if _DIRECCION_PROHIBIDA[clave] == direccion:
            return f"el Playbook prohibe {token} en {regimen}"
    return None


def gate_confianza(sesgo: dict[str, Any] | None) -> str | None:
    """Excluye si el modelo declara que no ve lo suficiente.

    El motor emite `confianza_total_pct` y hasta ahora ese número solo se imprimía
    en su propia consola: un modelo que avisa que ve al 55 % y aun así publica es
    peor que uno que no avisa.

    **Solo alcanza a los 5 activos con ficha.** La confianza mide los drivers
    macro que alimentan el régimen, y el régimen solo entra al sesgo de esos
    cinco. Los otros 33 del catálogo se puntúan con técnica y calendario, sin
    insumo macro: bloquearlos por una confianza que no usan dejaría al escáner sin
    universo por nada. El scoping sale gratis, igual que en `gate_playbook`: un
    activo sin entrada de sesgo pasa de largo.

    Un sesgo con `error` tampoco se toca: ese caso ya lo informa
    `_sesgos_playbook` como aviso, y fabricar acá un motivo de confianza sobre un
    payload que no la trae sería reportar dos veces la misma falla con nombres
    distintos.
    """
    if not sesgo or "error" in sesgo:
        return None
    conf = (sesgo.get("confianza_general") or {}).get("confianza_total_pct")
    if conf is None:
        # Fail-closed y consistente con `pipeline_datos.confianza_suficiente`. Un
        # payload valido de `cargar_macro_bias` siempre trae el campo, asi que su
        # ausencia es un esquema viejo, no una lectura buena. Dejarlo pasar seria
        # la puerta de atras que el umbral existe para cerrar.
        return "el snapshot no declara la confianza del modelo"
    if float(conf) < UMBRAL_CONFIANZA_PCT:
        return (
            f"la confianza del modelo esta en {float(conf):.1f}% y el minimo es "
            f"{UMBRAL_CONFIANZA_PCT:.0f}%: bajo ese piso falta un driver o esta roto"
        )
    return None


def gate_agotamiento(d1: dict[str, Any]) -> str | None:
    """Excluye si el activo ya consumió su recorrido diario.

    El plan lo trata como 0 puntos en el Factor Espacio, pero 0 puntos en un
    factor de 20 todavía deja 80 disponibles: un activo agotado puede ganar la
    tanda con técnica y catalizador. Agotado es agotado.
    """
    atr = d1.get("atr_14")
    rango = d1.get("rango_hoy")
    if not atr or rango is None:
        return None
    consumo = rango / atr
    if consumo > 0.90:
        return f"ATR diario consumido al {consumo:.0%}"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Los 4 factores del Score_GI
# ─────────────────────────────────────────────────────────────────────────────
def direccion_tecnica(h1: dict[str, Any]) -> str:
    """ALCISTA o BAJISTA según el precio contra la EMA 50 de H1.

    La EMA 50 y no la 100 porque la tanda es intradía y la 100 reacciona
    demasiado lento para una lectura de la jornada. Nunca devuelve LATERAL: la
    pieza tiene que nombrar una dirección (regla de oro del proyecto), y para eso
    el empate exacto se resuelve del lado del precio.
    """
    return "ALCISTA" if h1["price"] >= h1["ema_50"] else "BAJISTA"


def factor_tecnico(h1: dict[str, Any], d1: dict[str, Any], direccion: str) -> tuple[int, str]:
    """T ∈ [0, 35]. Quiebre de EMA 20 con estructura detrás, rebote en EMA
    diaria, o quiebre de nivel horizontal."""
    precio, alcista = h1["price"], direccion == "ALCISTA"

    cruza_ema20 = precio > h1["ema_20"] if alcista else precio < h1["ema_20"]
    estructura = (
        precio > h1["ema_50"] and precio > h1["ema_100"]
        if alcista else
        precio < h1["ema_50"] and precio < h1["ema_100"]
    )
    if cruza_ema20 and estructura:
        return 35, "quiebre de EMA 20 en H1 con EMA 50/100 detrás"

    # Rebote en EMA diaria: el precio está a menos de medio ATR de H1 de la EMA.
    margen = 0.5 * h1["atr_14"]
    for etiqueta, nivel in (("EMA 50 diaria", d1.get("ema_50")), ("EMA 100 diaria", d1.get("ema_100"))):
        if nivel and abs(precio - nivel) <= margen:
            return 25, f"rebote en {etiqueta}"

    if alcista and precio > h1["r1"]:
        return 15, "quiebre de resistencia R1"
    if not alcista and precio < h1["s1"]:
        return 15, "quiebre de soporte S1"

    return 0, "sin gatillo tecnico"


def factor_catalizador(
    ticker: str,
    eventos: list[dict[str, Any]],
    delta_ust_bps: float | None,
) -> tuple[int, str]:
    """M ∈ [0, 25]. Receptor del dato del día, movimiento de la curva, o evento
    de segundo orden.

    El +25 exige impacto **alto**, no cualquier dato del día. El plan enumera
    "IPC, NFP, CB", que son de impacto alto, y en una jornada normal hay nueve
    eventos de impacto medio o más: si cualquiera diera el máximo, todo activo
    estadounidense sacaría 25 y el factor dejaría de discriminar entre ellos.
    Los de impacto medio caen al +15 junto con inventarios y discursos.
    """
    def es_receptor(ev: dict[str, Any]) -> bool:
        pais = _normalizar(ev.get("pais", ""))
        receptores = next(
            (v for k, v in _RECEPTORES_POR_PAIS.items() if k in pais or pais in k), ()
        )
        return ticker in receptores

    for ev in eventos:
        if _normalizar(ev.get("impacto", "")) == "alto" and es_receptor(ev):
            return 25, f"recibe el dato de alto impacto: {ev.get('nombre', '?')}"

    if delta_ust_bps is not None and abs(delta_ust_bps) >= 3.0:
        return 20, f"la UST 10Y se movio {delta_ust_bps:+.1f} bps"

    for ev in eventos:
        nombre = ev.get("nombre", "?")
        if es_receptor(ev):
            return 15, f"recibe un dato de impacto medio: {nombre}"
        if any(p in _normalizar(nombre) for p in _PATRONES_SEGUNDO_ORDEN):
            return 15, f"evento de segundo orden: {nombre}"

    return 0, "sin catalizador"


def factor_espacio(h1: dict[str, Any], d1: dict[str, Any], direccion: str) -> tuple[int, str]:
    """C ∈ [0, 20]. Espacio al objetivo medido en ATR de H1, validado contra lo
    que le queda de recorrido al día."""
    precio = h1["price"]
    objetivo = h1["r1"] if direccion == "ALCISTA" else h1["s1"]
    atr_h1 = h1["atr_14"]
    if not atr_h1:
        return 0, "sin ATR de H1"

    espacio = abs(objetivo - precio) / atr_h1
    atr_d1, rango_hoy = d1.get("atr_14"), d1.get("rango_hoy")
    consumo = (rango_hoy / atr_d1) if (atr_d1 and rango_hoy is not None) else None

    if consumo is None:
        return 0, f"espacio {espacio:.1f}x ATR H1, sin consumo diario medible"
    # P0: Piso operativo para evitar falsos positivos a primera hora (reloj vs mercado).
    # Si el consumo es < 15%, la sesión apenas comienza y no se otorga el bonus completo de 20 puntos.
    if espacio >= 1.5 and 0.15 <= consumo < 0.70:
        return 20, f"espacio {espacio:.1f}x ATR H1 y ATR diario al {consumo:.0%}"
    if espacio >= 1.5 and consumo < 0.15:
        return 10, f"espacio {espacio:.1f}x ATR H1 (sesión inicial, consumo al {consumo:.0%})"
    if espacio >= 1.0 and 0.70 <= consumo <= 0.85:
        return 10, f"espacio {espacio:.1f}x ATR H1 y ATR diario al {consumo:.0%}"
    return 0, f"espacio {espacio:.1f}x ATR H1 y ATR diario al {consumo:.0%}"


def factor_momentum(h1: dict[str, Any], direccion: str) -> tuple[int, str]:
    """F ∈ [0, 20]. ADX con RSI en zona de expansión, o ADX naciente con MACD a
    favor."""
    adx, rsi = h1["adx_14"], h1["rsi_14"]
    alcista = direccion == "ALCISTA"

    zona_sana = (50 <= rsi <= 68) if alcista else (32 <= rsi <= 50)
    if adx > 25 and zona_sana:
        return 20, f"ADX {adx:.0f} con RSI {rsi:.0f} en zona de expansion"

    macd_favor = h1["macd_hist"] > 0 if alcista else h1["macd_hist"] < 0
    if 20 <= adx <= 25 and macd_favor:
        return 10, f"ADX {adx:.0f} con MACD a favor"

    return 0, f"ADX {adx:.0f} y RSI {rsi:.0f} sin expansion"


# ─────────────────────────────────────────────────────────────────────────────
# Escaneo
# ─────────────────────────────────────────────────────────────────────────────
def evaluar_activo(
    activo: dict[str, Any],
    eventos: list[dict[str, Any]],
    delta_ust_bps: float | None,
    sesgos: dict[str, Any],
    ahora_santiago: datetime,
    analizador: Callable[[str, str], dict[str, Any]] = analizar_activo,
    ignorar_agotamiento: bool = False,
) -> dict[str, Any]:
    """Puntúa un activo, o explica por qué queda fuera."""
    ticker = activo["ticker"]
    base = {"ticker": ticker, "nombre": activo["nombre"], "clase": activo["clase"]}

    motivo = gate_feriado(ticker, ahora_santiago.date())
    if motivo:
        return {**base, "excluido": motivo}

    h1 = analizador(ticker, "H1")
    if "error" in h1:
        return {**base, "excluido": f"{h1['error']}: {h1.get('message', '')}"}
    d1 = analizador(ticker, "D1")
    if "error" in d1:
        return {**base, "excluido": f"D1 {d1['error']}: {d1.get('message', '')}"}

    if not ignorar_agotamiento:
        motivo = gate_agotamiento(d1)
        if motivo:
            return {**base, "excluido": motivo}

    direccion = direccion_tecnica(h1)

    motivo = gate_blackout(ticker, eventos, ahora_santiago)
    if motivo:
        return {**base, "excluido": motivo}

    motivo = gate_confianza(sesgos.get(ticker))
    if motivo:
        return {**base, "excluido": motivo}

    motivo = gate_playbook(direccion, sesgos.get(ticker))
    if motivo:
        return {**base, "excluido": motivo}

    # El "hasta donde" del sesgo se resuelve aca porque aca estan las dos piezas
    # en la mano: el H1 con las anclas del Chandelier y el sesgo del activo.
    # Pedirlas de nuevo en el carrusel seria un segundo viaje al terminal por
    # datos que ya viajaron, y dos calculos del mismo nivel que pueden discrepar.
    vigencia = None
    try:
        from market_data_mcp.bias_reader import resolver_vigencia
        vigencia = resolver_vigencia(sesgos.get(ticker), h1, activo["digits"])
    except ImportError:
        # Mismo criterio que `_sesgos_playbook`: sin el Playbook el escaner
        # sigue puntuando, y la pieza sale sin su "hasta donde" en vez de no salir.
        pass

    t, det_t = factor_tecnico(h1, d1, direccion)
    m, det_m = factor_catalizador(ticker, eventos, delta_ust_bps)
    c, det_c = factor_espacio(h1, d1, direccion)
    f, det_f = factor_momentum(h1, direccion)

    return {
        **base,
        "direccion": direccion,
        "score": t + m + c + f,
        "factores": {
            "tecnico":     {"puntos": t, "max": 35, "detalle": det_t},
            "catalizador": {"puntos": m, "max": 25, "detalle": det_m},
            "espacio":     {"puntos": c, "max": 20, "detalle": det_c},
            "momentum":    {"puntos": f, "max": 20, "detalle": det_f},
        },
        "precio": h1["price"],
        "soporte": h1["s1"],
        "resistencia": h1["r1"],
        "atr_h1": h1["atr_14"],
        # Hasta donde sigue vigente el sesgo del Playbook, en su gramatica.
        # `None` para los 33 activos del catalogo que no tienen ficha.
        "vigencia": vigencia,
        # Impulso proyectado del modelo ADC+ATR: 1,5 x ATR14 de H1 tras el
        # quiebre. El nombre interno sigue al modelo cuantitativo, que es donde
        # esta definido; hacia el cliente el mismo numero se comunica como
        # "Volatilidad tipica", sin la palabra proyectado y sin sumarlo al
        # precio. La pieza de alerta no lleva firma acreditada, asi que afirmar
        # un recorrido futuro la convertiria en una recomendacion de inversion
        # sin quien la respalde. El ATR es un promedio de rangos PASADOS:
        # describe cuanto se mueve el instrumento, no hacia donde va.
        "impulso_adc_atr": round(1.5 * h1["atr_14"], activo["digits"]),
    }


def _contexto_macro(ahora_santiago: datetime) -> tuple[list[dict[str, Any]], float | None, list[str]]:
    """Calendario del día y variación diaria de la UST 10Y, con sus avisos.

    Devuelve también la lista de advertencias: si el calendario no responde, el
    escáner **no puede verificar blackouts** y eso tiene que viajar en la salida.
    Un escáner que informa "0 exclusiones" cuando en realidad no pudo mirar es
    peor que uno que falla.
    """
    avisos: list[str] = []
    eventos: list[dict[str, Any]] = []
    delta_ust: float | None = None

    try:
        from market_data_mcp.tools.calendar import cargar_calendario
        cal = cargar_calendario(solo_hoy=True, min_impact="medium", ahora=ahora_santiago)
        if "error" in cal:
            avisos.append(
                f"calendario no disponible ({cal['error']}): no se pudieron verificar "
                "blackouts ni el factor catalizador"
            )
        else:
            eventos = cal.get("eventos", [])
    except Exception as exc:  # noqa: BLE001
        avisos.append(
            f"calendario no disponible ({exc.__class__.__name__}): blackouts sin verificar"
        )

    try:
        from market_data_mcp.curva_reader import cargar_curva_tasas
        curva = cargar_curva_tasas(serie="DGS10")
        if "error" in curva:
            avisos.append(f"curva del Tesoro no disponible ({curva['error']})")
        else:
            serie = (curva.get("series") or {}).get("DGS10") or {}
            delta_ust = serie.get("delta_1d_bps")
            if delta_ust is None:
                avisos.append("la UST 10Y no tiene variacion diaria calculable hoy")
    except Exception as exc:  # noqa: BLE001
        avisos.append(f"curva del Tesoro no disponible ({exc.__class__.__name__})")

    return eventos, delta_ust, avisos


def _sesgos_playbook() -> tuple[dict[str, Any], list[str]]:
    """El sesgo del Playbook para los 5 activos con ficha.

    Si el snapshot está viejo, el gate de prohibiciones queda ciego y hay que
    decirlo: seguir puntuando en silencio significaría poder publicar un corto de
    Oro en un régimen que lo prohíbe.
    """
    avisos: list[str] = []
    sesgos: dict[str, Any] = {}
    try:
        from market_data_mcp.bias_reader import (
            TICKER_MT5,
            VALID_SYMBOLS,
            cargar_macro_bias,
        )
    except Exception as exc:  # noqa: BLE001
        return {}, [f"sesgo del Playbook no disponible ({exc.__class__.__name__})"]

    # El Playbook nombra WTI y US100; el catálogo técnico usa el símbolo del
    # broker (WTI.spot, US100.spot). Sin traducir, el gate no encontraría la
    # ficha del activo que está evaluando y quedaría ciego sin avisar. La tabla
    # vive en bias_reader, junto a VALID_SYMBOLS: es la misma pregunta.
    for sym in sorted(VALID_SYMBOLS - {"ALL"}):
        res = cargar_macro_bias(sym)
        if "error" in res:
            avisos.append(f"sesgo de {sym} no disponible ({res['error']})")
            continue
        sesgos[TICKER_MT5.get(sym) or sym] = res
    if avisos:
        avisos.append(
            "gate de prohibiciones del Playbook parcialmente ciego: correr "
            "pipeline_ingesta.py y despues macro_bias_engine.py"
        )
    return sesgos, avisos


def _conectar_terminal() -> list[str]:
    """Abre la conexión con MT5. Devuelve avisos, nunca lanza."""
    try:
        from market_data_mcp import mt5_client
        mt5_client.connect()
        return []
    except Exception as exc:  # noqa: BLE001
        return [
            f"no se pudo conectar a MT5 ({exc}). Abrir MetaTrader 5 y reintentar; "
            "sin terminal no hay ningun activo que puntuar"
        ]


def _publicados_hoy(
    fecha_iso: str,
    tanda: int | None = None,
    hora_actual: str | None = None,
) -> set[str]:
    """Tickers que ya salieron en una corrida anterior de hoy.

    Si el cliente recibe el mismo activo tres veces en un día, el carrusel deja
    de ser una selección y pasa a ser insistencia.
    """
    usados: set[str] = set()
    if not DIR_SALIDA.is_dir():
        return usados
    for archivo in DIR_SALIDA.glob(f"{fecha_iso}_*.json"):
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if tanda is not None and datos.get("tanda", 0) >= tanda:
            continue
        if hora_actual is not None:
            gen = datos.get("generado", "")
            if gen:
                try:
                    hora_gen = gen.split(" ")[1].replace(":", "-")
                    if hora_gen >= hora_actual.replace(":", "-"):
                        continue
                except Exception:
                    pass
        for sel in datos.get("seleccion", []):
            usados.add(sel["ticker"])
    return usados


def escanear(
    tanda: int | None = None,
    top: int = 3,
    solo_renderizables: bool = True,
    ahora_ny: datetime | None = None,
    analizador: Callable[[str, str], dict[str, Any]] = analizar_activo,
    grupo: str | None = None,
    modo_matriz: bool = False,
    ignorar_agotamiento: bool = False,
) -> dict[str, Any]:
    """Recorre el universo, aplica gates, puntúa y elige el Top N de la sesión/tanda o matriz por grupos."""
    ahora_ny = ahora_ny or datetime.now(tz=NY)
    ahora_stgo = ahora_ny.astimezone(SANTIAGO)

    info_sesion = detectar_sesion(ahora_ny)
    n_tanda = tanda or info_sesion["tanda"]
    nombre_sesion = (
        TANDAS[tanda]["nombre"]
        if tanda and tanda in TANDAS
        else info_sesion["nombre"]
    )
    foco_sesion = (
        TANDAS[tanda]["foco"]
        if tanda and tanda in TANDAS
        else info_sesion["foco"]
    )
    sesion_slug = info_sesion["slug"] if not tanda else f"tanda{n_tanda}"

    eventos, delta_ust, avisos = _contexto_macro(ahora_stgo)
    sesgos, avisos_sesgo = _sesgos_playbook()
    avisos.extend(avisos_sesgo)

    if analizador is analizar_activo:
        avisos.extend(_conectar_terminal())

    universo = cargar_universo(solo_renderizables)
    if grupo:
        universo = filtrar_por_grupo(universo, grupo)
        avisos.append(f"universo filtrado exclusivamente al grupo/categoría '{grupo}' ({len(universo)} activos)")

    if solo_renderizables and not grupo:
        avisos.append(
            f"universo limitado a {len(universo)} activos con imagen en disco. "
            "Los prompts de las que faltan estan en "
            "docs/design/stories-gi/imagenes-por-activo.md; --todos ignora el filtro"
        )

    ya_usados = _publicados_hoy(
        ahora_stgo.date().isoformat(),
        tanda=tanda,
        hora_actual=ahora_stgo.strftime("%H:%M"),
    )

    evaluados: list[dict[str, Any]] = []
    excluidos: list[dict[str, Any]] = []
    for activo in universo:
        if activo["ticker"] in ya_usados:
            excluidos.append({
                "ticker": activo["ticker"],
                "nombre": activo["nombre"],
                "clase": activo["clase"],
                "excluido": "ya salio en una corrida anterior de hoy",
            })
            continue
        res = evaluar_activo(activo, eventos, delta_ust, sesgos, ahora_stgo, analizador, ignorar_agotamiento=ignorar_agotamiento)
        (excluidos if "excluido" in res else evaluados).append(res)

    evaluados.sort(key=lambda r: (-r["score"], r["ticker"]))

    if modo_matriz:
        # Cobertura Total: selecciona el Top 1 con score > 0 de cada una de las 5 categorías clave de mercado
        categorias_orden = ["forex", "commodity", "indice", "accion", "crypto"]
        seleccion = []
        for cat_obj in categorias_orden:
            candidatos_cat = [
                r for r in evaluados
                if r["score"] > 0 and r["ticker"] in {a["ticker"] for a in filtrar_por_grupo(universo, cat_obj)}
            ]
            if candidatos_cat:
                seleccion.append(candidatos_cat[0])
    else:
        seleccion = [r for r in evaluados if r["score"] > 0][:top]

    if not seleccion:
        avisos.append(
            "ningun activo puntuo sobre 0: no hay tanda que publicar. "
            "Es un resultado valido, no una falla"
        )

    ancla_ny_str = (
        "{:02d}:{:02d}".format(*TANDAS[n_tanda]["hora_ny"])
        if n_tanda in TANDAS
        else ahora_ny.strftime("%H:%M")
    )

    return {
        "tanda": n_tanda,
        "sesion_slug": sesion_slug,
        "nombre_tanda": nombre_sesion,
        "nombre_sesion": nombre_sesion,
        "foco": foco_sesion,
        "ancla_ny": ancla_ny_str,
        "hora_chile_tanda": hora_chile_de_tanda(n_tanda, ahora_ny),
        "hora_real_chile": ahora_stgo.strftime("%H:%M"),
        "generado": ahora_stgo.strftime("%Y-%m-%d %H:%M"),
        "delta_ust_10y_bps": delta_ust,
        "eventos_del_dia": len(eventos),
        "score_maximo_posible": 100,
        "seleccion": seleccion,
        "ranking_completo": evaluados,
        "excluidos": excluidos,
        "avisos": avisos,
    }


def _guardar(resultado: dict[str, Any]) -> Path:
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    fecha, hora = resultado["generado"].split(" ")
    slug = resultado.get("sesion_slug", f"tanda{resultado['tanda']}")
    destino = DIR_SALIDA / f"{fecha}_{hora.replace(':', '-')}_{slug}.json"
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino


def _imprimir(resultado: dict[str, Any]) -> None:
    r = resultado
    nombre = r.get("nombre_sesion", r["nombre_tanda"])
    hora_real = r.get("hora_real_chile", r["generado"].split(" ")[-1])
    print(f"\nSESIÓN: {nombre} ({hora_real} hrs hora Chile)")
    print(f"Foco: {r['foco']}")
    linea = f"Generado {r['generado']} - eventos del dia: {r['eventos_del_dia']}"
    if r["delta_ust_10y_bps"] is not None:
        linea += f" - UST 10Y {r['delta_ust_10y_bps']:+.1f} bps"
    print(linea)

    print(f"\nSELECCION (score sobre {r['score_maximo_posible']})")
    if not r["seleccion"]:
        print("  (vacia)")
    for i, s in enumerate(r["seleccion"], 1):
        print(f"  {i}. {s['nombre']} ({s['ticker']}) - {s['direccion']} - {s['score']}/100")
        for n, f in s["factores"].items():
            print(f"       {n:12s} {f['puntos']:>2}/{f['max']:<2} {f['detalle']}")

    if r["excluidos"]:
        print(f"\nEXCLUIDOS ({len(r['excluidos'])})")
        for e in r["excluidos"]:
            print(f"  {e['ticker']:<12} {e['excluido']}")

    if r["avisos"]:
        print("\nAVISOS")
        for a in r["avisos"]:
            print(f"  - {a}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Escaner responsivo del universo para alertas de mercado y carrusel"
    )
    parser.add_argument(
        "--tanda", type=int, choices=sorted(TANDAS),
        help="fuerza una tanda especifica (por defecto detecta la sesion y hora real)",
    )
    parser.add_argument(
        "--top", type=int, default=3,
        help="cuantos activos selecciona (default 3, el tope de adjuntos sin +2 en WhatsApp)",
    )
    parser.add_argument(
        "--grupo", type=str, default=None,
        help="filtra exclusivamente a un grupo de WhatsApp (forex, commodities, indices, acciones, crypto)",
    )
    parser.add_argument(
        "--matriz", action="store_true",
        help="cobertura total: selecciona el Top 1 de cada uno de los 5 grupos de mercado",
    )
    parser.add_argument(
        "--todos", action="store_true",
        help="escanea tambien los activos sin imagen (su Story no va a poder rendirse)",
    )
    parser.add_argument("--json", action="store_true", help="emite solo JSON, sin reporte legible")
    parser.add_argument("--sin-guardar", action="store_true", help="no escribe en data/screener/")
    args = parser.parse_args(argv)

    resultado = escanear(
        tanda=args.tanda,
        top=args.top,
        solo_renderizables=not args.todos,
        grupo=args.grupo,
        modo_matriz=args.matriz,
    )

    if not args.sin_guardar:
        resultado["archivo"] = str(_guardar(resultado))

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        _imprimir(resultado)
        if resultado.get("archivo"):
            print(f"\nGuardado en {resultado['archivo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

