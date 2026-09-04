"""Núcleo de análisis técnico: una implementación, varios consumidores.

Por qué existe este módulo. El análisis vivía **dentro** del closure de
`register(mcp)` en `tools/levels.py`, así que solo se podía usar llamando a la
tool por MCP. Un script que necesitara los mismos indicadores no tenía cómo
pedirlos y terminaba recalculándolos, que es exactamente el problema que ya tiene
el repo: `scripts/extractor_precios.py` calcula `ema_20`, `sma_20` y el canal de
Donchian para 6 activos escribiendo a disco, mientras la tool calcula EMA 50/100
y Bollinger para los 38. Dos tuberías con la misma materia prima y distinta
profundidad, y nadie garantizando que las fórmulas coincidan.

El escáner de tandas diarias habría sido la tercera. Extraer el núcleo lo evita:
la tool MCP y el escáner llaman a la misma función, así que si un indicador
cambia, cambia para los dos.

El contrato de error se conserva tal cual: nunca se lanza para un problema
esperable (ticker fuera del catálogo, MT5 caído, velas insuficientes), siempre se
retorna `{"error": "CÓDIGO", "message": "..."}`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

# Catálogo de tickers válidos — fuente única compartida (market_data_mcp/catalog.py).
from market_data_mcp.catalog import VALID_TICKERS

# Piso del ATR restante (issue oportunidad-adx-atr): sin esto, una tarde volátil
# consume casi todo el ATR diario y bloquea cualquier /oportunidad el resto del
# día, aunque siga habiendo movimiento real posible (cierre de Wall Street,
# noticia, gap). 30% del ATR diario como mínimo disponible.
PISO_ATR_RESTANTE = 0.30


def _rsi(series: pd.Series, period: int = 14) -> float:
    """RSI de Wilder. Retorna el valor del último bar."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    return float(rsi_series.iloc[-1])


def _swing_levels(df: pd.DataFrame, pivot_bars: int = 5) -> tuple[list[float], list[float]]:
    """
    Detecta swing highs (resistencias) y swing lows (soportes) en el DataFrame.
    Un swing high es un bar cuyo high es mayor que los `pivot_bars` bars a cada lado.
    """
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)

    resistances: list[float] = []
    supports: list[float] = []

    for i in range(pivot_bars, n - pivot_bars):
        if highs[i] > max(highs[i - pivot_bars:i]) and highs[i] > max(highs[i + 1:i + pivot_bars + 1]):
            resistances.append(float(highs[i]))
        if lows[i] < min(lows[i - pivot_bars:i]) and lows[i] < min(lows[i + 1:i + pivot_bars + 1]):
            supports.append(float(lows[i]))

    return resistances, supports


def _cluster(levels: list[float], threshold: float) -> list[float]:
    """Agrupa niveles cercanos en uno solo (el más alto del grupo para R, el más bajo para S)."""
    if not levels:
        return []
    sorted_lvls = sorted(set(levels))
    clustered = [sorted_lvls[0]]
    for lvl in sorted_lvls[1:]:
        if lvl - clustered[-1] > threshold:
            clustered.append(lvl)
    return clustered


def _get_support_resistance(df: pd.DataFrame, current: float, atr14: float, digits: int) -> dict[str, float]:
    """
    Calcula S1, S2, R1, R2 garantizando que R1/R2 > current > S1/S2.
    Usa swing highs/lows como niveles primarios y proyecciones ATR como respaldo.
    """
    threshold = current * 0.0015  # 0.15% para clustering
    resistances_raw, supports_raw = _swing_levels(df)
    resistances = _cluster(resistances_raw, threshold)
    supports = _cluster(supports_raw, threshold)

    above = sorted([r for r in resistances if r > current])
    below = sorted([s for s in supports if s < current], reverse=True)

    r1 = above[0] if len(above) > 0 else round(current + atr14, digits)
    r2 = above[1] if len(above) > 1 else round(current + 2 * atr14, digits)
    s1 = below[0] if len(below) > 0 else round(current - atr14, digits)
    s2 = below[1] if len(below) > 1 else round(current - 2 * atr14, digits)

    # De donde salio cada nivel, lado por lado. El respaldo por ATR es una red de
    # seguridad correcta (garantiza R > precio > S) pero **no es un nivel**: es el
    # precio mas o menos el ATR, y sin esta marca el resultado es indistinguible
    # de una resistencia medida sobre swings. La pieza publica "Resistencia clave"
    # y el cliente lee estructura donde solo hay una banda de volatilidad.
    #
    # Los cuatro lados caen por separado, asi que se declaran por separado: se
    # puede tener una resistencia real con un soporte sintetico. Y cuando ambos
    # son sinteticos la banda vale 2 ATR **exactos por construccion**, con lo que
    # cualquier medida de "cuanto de la banda cubre una vela" devuelve un numero
    # fijo que no mide nada.
    origen = {
        "r1": "swing" if len(above) > 0 else "atr",
        "r2": "swing" if len(above) > 1 else "atr",
        "s1": "swing" if len(below) > 0 else "atr",
        "s2": "swing" if len(below) > 1 else "atr",
    }

    return {
        "s2": round(s2, digits),
        "s1": round(s1, digits),
        "r1": round(r1, digits),
        "r2": round(r2, digits),
        "origen": origen,
    }


def analizar_activo(ticker: str, timeframe: str = "H4") -> dict[str, Any]:
    """Análisis técnico de un activo del catálogo contra el terminal MT5.

    Es el cuerpo de la tool `get_asset_levels`, disponible como función para que
    un script pueda pedirlo sin pasar por MCP.

    Args:
        ticker: símbolo MT5 del catálogo (ej. XAUUSD, USDCLP, WTI.spot, QQQ.US).
        timeframe: marco temporal MT5 (M1, M5, M15, M30, H1, H4, H12, D1, W1, MN1).

    Returns:
        El dict de indicadores, o `{"error": ..., "message": ...}`. Con
        `timeframe="D1"` agrega `rango_hoy` y `atr_restante_14`, que solo tienen
        sentido ahí: en otros marcos "hoy" no corresponde a una sola barra.
    """
    if ticker not in VALID_TICKERS:
        return {
            "error": "TICKER_NOT_FOUND",
            "message": (
                f"'{ticker}' no está en el catálogo de activos. "
                f"Tickers válidos: {', '.join(sorted(VALID_TICKERS.keys()))}"
            ),
        }

    digits = VALID_TICKERS[ticker]

    try:
        from market_data_mcp.mt5_client import (
            connect, get_rates, ema, atr, adx, macd, bollinger, donchian, TIMEFRAME_MAP,
        )
    except ImportError:
        return {
            "error": "MT5_UNAVAILABLE",
            "message": "No se pudo importar mt5_client. Verificar que MT5 esté iniciado.",
        }

    if timeframe.upper() not in TIMEFRAME_MAP:
        return {
            "error": "INVALID_TIMEFRAME",
            "message": f"Timeframe '{timeframe}' inválido. Válidos: {', '.join(TIMEFRAME_MAP.keys())}",
        }

    try:
        # La conexión se intenta por prudencia, pero su fallo NO aborta: la fuente
        # de verdad es `get_rates`, que conecta de forma perezosa y reporta el
        # error correcto si de verdad no hay terminal. Exigirla acá dejaba la ruta
        # feliz sin poder testearse con datos mockeados, y CI ciega.
        try:
            connect()
        except Exception:  # noqa: BLE001
            pass
        df = get_rates(ticker, timeframe.upper(), n_bars=300)
    except ImportError:
        # mt5_client importa MetaTrader5 de forma perezosa dentro de get_rates;
        # si el paquete no está instalado (p.ej. en CI), surge aquí y no en el
        # import de arriba. Lo convertimos al contrato de error en vez de lanzar.
        return {
            "error": "MT5_UNAVAILABLE",
            "message": "MetaTrader5 no está instalado en este entorno. El MCP requiere MT5 en la máquina del director.",
        }
    except RuntimeError as exc:
        msg = str(exc).lower()
        if "initialize" in msg or "not initialized" in msg or "login" in msg:
            return {
                "error": "MT5_UNAVAILABLE",
                "message": "MT5 no está conectado. Abre MetaTrader 5 y vuelve a intentar.",
            }
        return {
            "error": "MT5_UNAVAILABLE",
            "message": f"Error al obtener datos de {ticker} {timeframe}: {exc}",
        }

    if len(df) < 150:
        return {
            "error": "INSUFFICIENT_DATA",
            "message": f"Solo {len(df)} velas disponibles para {ticker} {timeframe}. Mínimo requerido: 150.",
        }

    # P0: Indicadores de estado sobre velas cerradas (df_closed) para evitar
    # que Donchian se autoanule y que el ATR se distorsione al abrir la barra.
    # El precio spot en tiempo real (current) se evalúa contra estos niveles congelados.
    df_closed = df.iloc[:-1] if len(df) >= 2 else df
    close_closed = df_closed["close"]

    ema100_val = float(ema(close_closed, 100).iloc[-1])
    ema50_val = float(ema(close_closed, 50).iloc[-1])
    # EMA 20: el Playbook la usa como gatillo de entrada en H1 (pullback en Oro,
    # compras tendenciales en US100). No confundir con `bb_mid`, que es una SMA 20.
    ema20_val = float(ema(close_closed, 20).iloc[-1])
    atr14_val = float(atr(df_closed, 14).iloc[-1])
    adx14_val = float(adx(df_closed, 14).iloc[-1])
    macd_l, macd_s, macd_h = macd(close_closed)
    bb_u, bb_m, bb_l = bollinger(close_closed)
    dc_h, dc_l, dc_m = donchian(df_closed)
    current = float(df["close"].iloc[-1])

    if current > ema100_val:
        trend = "ALCISTA"
    elif current < ema100_val:
        trend = "BAJISTA"
    else:
        trend = "LATERAL"

    rsi14_val = _rsi(close_closed, 14)
    levels = _get_support_resistance(df_closed, current, atr14_val, digits)
    bar_open = float(df["open"].iloc[-1])
    bar_high = float(df["high"].iloc[-1])
    bar_low = float(df["low"].iloc[-1])
    change_pct = round(((current - bar_open) / bar_open) * 100, 2) if bar_open else 0.0

    resultado: dict[str, Any] = {
        "ticker":       ticker,
        "timeframe":    timeframe.upper(),
        "price":        round(current, digits),
        "open_price":   round(bar_open, digits),
        "high_price":   round(bar_high, digits),
        "low_price":    round(bar_low, digits),
        "change_pct":   change_pct,
        "s2":           levels["s2"],
        "s1":           levels["s1"],
        "r1":           levels["r1"],
        "r2":           levels["r2"],
        "niveles_origen": levels["origen"],
        "rsi_14":       round(rsi14_val, 1),
        "atr_14":       round(atr14_val, digits),
        "adx_14":       round(adx14_val, 1),
        "ema_20":       round(ema20_val, digits),
        "ema_50":       round(ema50_val, digits),
        "ema_100":      round(ema100_val, digits),
        "macd_line":    round(macd_l, 4),
        "macd_signal":  round(macd_s, 4),
        "macd_hist":    round(macd_h, 4),
        "bb_upper":     round(bb_u, digits),
        "bb_mid":       round(bb_m, digits),
        "bb_lower":     round(bb_l, digits),
        "donchian_50_high": round(dc_h, digits),
        "donchian_50_low":  round(dc_l, digits),
        "donchian_50_mid":  round(dc_m, digits),
        "trend":        trend,
    }

    # Rango recorrido hoy y ATR restante: solo tienen sentido en D1, donde la
    # última barra es la vela diaria en curso (todavía formándose). En otros
    # marcos "hoy" no corresponde a una sola barra y el campo no aplica.
    if timeframe.upper() == "D1":
        rango_hoy = float(df["high"].iloc[-1] - df["low"].iloc[-1])
        piso = PISO_ATR_RESTANTE * atr14_val
        atr_restante = max(atr14_val - rango_hoy, piso)
        resultado["rango_hoy"] = round(rango_hoy, digits)
        resultado["atr_restante_14"] = round(atr_restante, digits)
        # ATR_20 es por definición el ATR diario del Playbook (`atr_daily_period`
        # en playbook_config.yaml) y la base del stop swing, 2.5 x ATR_20(D1).
        # Sin él ese stop no era calculable desde la tool y había que ir al
        # snapshot del motor, que puede tener 24 h.
        resultado["atr_20"] = round(float(atr(df_closed, 20).iloc[-1]), digits)

    # Anclajes del Chandelier Exit: el extremo de las últimas N velas cerradas.
    #
    # Van solo en H1 porque ahí lo define el Playbook (3.0 x ATR_14(H1)), mismo
    # criterio que `atr_20` en D1. Y van los ANCLAJES, no el nivel calculado: el
    # múltiplo depende del activo y del régimen desde que se implementó la
    # descomposición de Kilian (3,0 con respaldo del cobre, 2,0 sin él), así que
    # hornearlo acá obligaría a la tool a conocer el sesgo macro. La tool mide el
    # mercado; el múltiplo viaja en el snapshot y la aritmética vive en
    # `bias_reader.nivel_chandelier`.
    if timeframe.upper() == "H1":
        from market_data_mcp.bias_reader import cargar_config_riesgo

        n = int(cargar_config_riesgo()["trailing_stop_lookback_period"])
        ventana = df_closed.tail(n)
        resultado["chandelier_lookback"] = n
        resultado["chandelier_max"] = round(float(ventana["high"].max()), digits)
        resultado["chandelier_min"] = round(float(ventana["low"].min()), digits)

    resultado["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return resultado
