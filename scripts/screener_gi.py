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
DIR_SALIDA = RAIZ / "data" / "screener"


# ─────────────────────────────────────────────────────────────────────────────
# Las 3 tandas, ancladas a Nueva York
# ─────────────────────────────────────────────────────────────────────────────
# El plan las define en hora de Chile (10:30 / 14:30 / 16:45 CLT), y ese es el
# defecto: el desfase con Nueva York cambia dos veces al año porque los dos
# hemisferios cambian de horario en sentido opuesto. NYSE abre 09:30 CLT en
# agosto y 11:30 CLST en diciembre, así que "pre-cierre 16:45 CLT" describe en
# enero un mercado que ya cerró hace horas.
#
# La referencia es la sesión, no el reloj local: apertura + 1 h, media tarde, y
# cierre + 45 min. Expresado en hora de Nueva York el ancla no se mueve nunca, y
# la hora de Chile se deriva para comunicarla.
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
_PROHIBIDO_BAJISTA = ("SHORT", "SELL", "BREAKDOWN", "FADE_TOP", "VENTA")
_PROHIBIDO_ALCISTA = ("LONG", "BUY", "COMPRA", "CHASE", "FADE_SUPPORT")


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


# ─────────────────────────────────────────────────────────────────────────────
# Tandas
# ─────────────────────────────────────────────────────────────────────────────
def tanda_vigente(ahora_ny: datetime | None = None) -> int:
    """La tanda cuyo ancla está más cerca de la hora de Nueva York.

    Se elige la más cercana en vez de exigir una ventana exacta porque el
    director invoca a mano: si corre 20 minutos tarde, quiere la tanda que
    corresponde, no un error.
    """
    ahora = ahora_ny or datetime.now(tz=NY)
    referencia = ahora.replace(second=0, microsecond=0)

    def distancia(n: int) -> timedelta:
        h, m = TANDAS[n]["hora_ny"]
        ancla = referencia.replace(hour=h, minute=m)
        return abs(referencia - ancla)

    return min(TANDAS, key=distancia)


def hora_chile_de_tanda(n: int, dia_ny: datetime | None = None) -> str:
    """El ancla de la tanda, expresada en hora de Chile para comunicarla."""
    base = dia_ny or datetime.now(tz=NY)
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
    claves = _PROHIBIDO_BAJISTA if direccion == "BAJISTA" else _PROHIBIDO_ALCISTA
    for token in prohibidos:
        if any(c in token.upper() for c in claves):
            regimen = (sesgo.get("regimen_macro_global") or {}).get("codigo", "?")
            return f"el Playbook prohibe {token} en {regimen}"
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
    if espacio >= 1.5 and consumo < 0.70:
        return 20, f"espacio {espacio:.1f}x ATR H1 y ATR diario al {consumo:.0%}"
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

    motivo = gate_agotamiento(d1)
    if motivo:
        return {**base, "excluido": motivo}

    direccion = direccion_tecnica(h1)

    motivo = gate_blackout(ticker, eventos, ahora_santiago)
    if motivo:
        return {**base, "excluido": motivo}

    motivo = gate_playbook(direccion, sesgos.get(ticker))
    if motivo:
        return {**base, "excluido": motivo}

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
        # Impulso proyectado del modelo ADC+ATR: 1,5 x ATR14 de H1 tras el
        # quiebre. Es lo que alimenta el bloque "Impulso ADC/ATR" de la Story.
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
        from market_data_mcp.bias_reader import cargar_macro_bias, VALID_SYMBOLS
    except Exception as exc:  # noqa: BLE001
        return {}, [f"sesgo del Playbook no disponible ({exc.__class__.__name__})"]

    # El Playbook nombra WTI y US100; el catálogo técnico usa el símbolo del
    # broker (WTI.spot, US100.spot). Sin traducir, el gate no encontraría la
    # ficha del activo que está evaluando y quedaría ciego sin avisar.
    equivalencias = {"WTI": "WTI.spot", "US100": "US100.spot"}
    for sym in sorted(VALID_SYMBOLS - {"ALL"}):
        res = cargar_macro_bias(sym)
        if "error" in res:
            avisos.append(f"sesgo de {sym} no disponible ({res['error']})")
            continue
        sesgos[equivalencias.get(sym, sym)] = res
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


def _publicados_hoy(fecha_iso: str, tanda: int) -> set[str]:
    """Tickers que ya salieron en una tanda anterior de hoy.

    La tanda 2 no debe repetir la tesis de la mañana: si el cliente recibe el
    mismo activo tres veces en un día, el carrusel deja de ser una selección y
    pasa a ser insistencia.
    """
    usados: set[str] = set()
    if not DIR_SALIDA.is_dir():
        return usados
    for archivo in DIR_SALIDA.glob(f"{fecha_iso}_*_tanda*.json"):
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if datos.get("tanda", 0) >= tanda:
            continue
        for sel in datos.get("seleccion", []):
            usados.add(sel["ticker"])
    return usados


def escanear(
    tanda: int | None = None,
    top: int = 3,
    solo_renderizables: bool = True,
    ahora_ny: datetime | None = None,
    analizador: Callable[[str, str], dict[str, Any]] = analizar_activo,
) -> dict[str, Any]:
    """Recorre el universo, aplica gates, puntúa y elige el Top N de la tanda."""
    ahora_ny = ahora_ny or datetime.now(tz=NY)
    ahora_stgo = ahora_ny.astimezone(SANTIAGO)
    n_tanda = tanda or tanda_vigente(ahora_ny)

    eventos, delta_ust, avisos = _contexto_macro(ahora_stgo)
    sesgos, avisos_sesgo = _sesgos_playbook()
    avisos.extend(avisos_sesgo)

    # Abrir el canal con el terminal antes de pedir la primera vela. `get_rates`
    # no lo hace: dentro del MCP la conexión la abre el lifespan del server al
    # arrancar, así que un script tiene que abrirla por su cuenta (mismo patrón
    # que `scripts/serie_mt5.py`). Sin esto, MT5 responde -10004 'No IPC
    # connection' en cada activo y el escaneo sale vacío culpando al terminal.
    #
    # Solo cuando el analizador es el real: los tests inyectan uno sintético
    # justamente para no necesitar MT5.
    if analizador is analizar_activo:
        avisos.extend(_conectar_terminal())

    universo = cargar_universo(solo_renderizables)
    if solo_renderizables:
        avisos.append(
            f"universo limitado a {len(universo)} activos con imagen en disco. "
            "Los prompts de las que faltan estan en "
            "docs/design/stories-gi/imagenes-por-activo.md; --todos ignora el filtro"
        )

    ya_usados = _publicados_hoy(ahora_stgo.date().isoformat(), n_tanda)

    evaluados: list[dict[str, Any]] = []
    excluidos: list[dict[str, Any]] = []
    for activo in universo:
        if activo["ticker"] in ya_usados:
            excluidos.append({
                "ticker": activo["ticker"],
                "nombre": activo["nombre"],
                "clase": activo["clase"],
                "excluido": "ya salio en una tanda anterior de hoy",
            })
            continue
        res = evaluar_activo(activo, eventos, delta_ust, sesgos, ahora_stgo, analizador)
        (excluidos if "excluido" in res else evaluados).append(res)

    evaluados.sort(key=lambda r: (-r["score"], r["ticker"]))
    seleccion = [r for r in evaluados if r["score"] > 0][:top]

    if not seleccion:
        avisos.append(
            "ningun activo puntuo sobre 0: no hay tanda que publicar. "
            "Es un resultado valido, no una falla"
        )

    return {
        "tanda": n_tanda,
        "nombre_tanda": TANDAS[n_tanda]["nombre"],
        "foco": TANDAS[n_tanda]["foco"],
        "ancla_ny": "{:02d}:{:02d}".format(*TANDAS[n_tanda]["hora_ny"]),
        "hora_chile_tanda": hora_chile_de_tanda(n_tanda, ahora_ny),
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
    destino = DIR_SALIDA / f"{fecha}_{hora.replace(':', '-')}_tanda{resultado['tanda']}.json"
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino


def _imprimir(resultado: dict[str, Any]) -> None:
    r = resultado
    print(f"\nTANDA {r['tanda']} - {r['nombre_tanda']}")
    print(f"Ancla {r['ancla_ny']} Nueva York = {r['hora_chile_tanda']} hora Chile")
    print(r["foco"])
    linea = f"Generado {r['generado']} - eventos del dia: {r['eventos_del_dia']}"
    if r["delta_ust_10y_bps"] is not None:
        linea += f" - UST 10Y {r['delta_ust_10y_bps']:+.1f} bps"
    print(linea)

    print(f"\nSELECCION (score sobre {r['score_maximo_posible']})")
    if not r["seleccion"]:
        print("  (vacia)")
    for i, s in enumerate(r["seleccion"], 1):
        print(f"  {i}. {s['nombre']} ({s['ticker']}) - {s['direccion']} - {s['score']}/100")
        for nombre, f in s["factores"].items():
            print(f"       {nombre:12s} {f['puntos']:>2}/{f['max']:<2} {f['detalle']}")

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
        description="Escaner del universo para las tandas diarias de produccion"
    )
    parser.add_argument(
        "--tanda", type=int, choices=sorted(TANDAS),
        help="tanda a escanear (por defecto, la mas cercana a la hora de Nueva York)",
    )
    parser.add_argument(
        "--top", type=int, default=3,
        help="cuantos activos selecciona (default 3, el tope de adjuntos sin +2 en WhatsApp)",
    )
    parser.add_argument(
        "--todos", action="store_true",
        help="escanea tambien los activos sin imagen (su Story no va a poder rendirse)",
    )
    parser.add_argument("--json", action="store_true", help="emite solo JSON, sin reporte legible")
    parser.add_argument("--sin-guardar", action="store_true", help="no escribe en data/screener/")
    args = parser.parse_args(argv)

    resultado = escanear(tanda=args.tanda, top=args.top, solo_renderizables=not args.todos)

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
