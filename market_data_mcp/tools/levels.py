"""Tool get_asset_levels — análisis técnico completo con RSI, S1/S2/R1/R2 y error explícito."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastmcp import FastMCP

# Catálogo de tickers válidos (cargado una vez al importar)
_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "activos.json"


def _load_valid_tickers() -> dict[str, int]:
    """Retorna {ticker_mt5: digits} de todos los activos del catálogo."""
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    tickers: dict[str, int] = {}

    for asset in data.get("forex_commodities", []):
        t = asset["ticker_mt5"]
        tickers[t] = asset["digits"]

    for asset in data.get("indices", []):
        t = asset["ticker_mt5"]
        tickers[t] = asset["digits"]

    for sector in data.get("acciones", {}).values():
        for comp in sector.get("componentes", []):
            t = comp["ticker_mt5"]
            tickers[t] = comp["digits"]

    for comp in data.get("activos_complementarios", {}).values():
        t = comp["ticker_mt5"]
        tickers[t] = comp["digits"]

    return tickers


_VALID_TICKERS = _load_valid_tickers()


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

    return {
        "s2": round(s2, digits),
        "s1": round(s1, digits),
        "r1": round(r1, digits),
        "r2": round(r2, digits),
    }


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_asset_levels(ticker: str, timeframe: str = "H4") -> dict[str, Any]:
        """Análisis técnico completo: precio, S1/S2/R1/R2, RSI14, ATR14 y tendencia.

        Solo acepta tickers del catálogo de activos del proyecto. Si MT5 no está
        disponible o el ticker no existe, retorna {"error": "CÓDIGO", "message": "..."}.

        Args:
            ticker: Símbolo MT5 del catálogo (ej: XAUUSD, USDCLP, WTI.spot, #AAPL).
            timeframe: Marco temporal MT5 (M1, M5, M15, M30, H1, H4, H12, D1, W1, MN1).

        Returns:
            Dict con: ticker, timeframe, price, s1, s2, r1, r2, rsi_14, atr_14, trend, timestamp.
            O {"error": "CÓDIGO", "message": "..."} si el dato no está disponible.
        """
        if ticker not in _VALID_TICKERS:
            return {
                "error": "TICKER_NOT_FOUND",
                "message": (
                    f"'{ticker}' no está en el catálogo de activos. "
                    f"Tickers válidos: {', '.join(sorted(_VALID_TICKERS.keys()))}"
                ),
            }

        digits = _VALID_TICKERS[ticker]

        try:
            from market_data_mcp.mt5_client import get_rates, ema, atr, TIMEFRAME_MAP
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
            df = get_rates(ticker, timeframe.upper(), n_bars=300)
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

        if len(df) < 100:
            return {
                "error": "INSUFFICIENT_DATA",
                "message": f"Solo {len(df)} velas disponibles para {ticker} {timeframe}. Mínimo requerido: 100.",
            }

        close = df["close"]
        ema100_val = float(ema(close, 100).iloc[-1])
        atr14_val = float(atr(df, 14).iloc[-1])
        current = float(close.iloc[-1])

        if current > ema100_val:
            trend = "ALCISTA"
        elif current < ema100_val:
            trend = "BAJISTA"
        else:
            trend = "LATERAL"

        rsi14_val = _rsi(close, 14)
        levels = _get_support_resistance(df, current, atr14_val, digits)

        from datetime import datetime
        return {
            "ticker":    ticker,
            "timeframe": timeframe.upper(),
            "price":     round(current, digits),
            "s2":        levels["s2"],
            "s1":        levels["s1"],
            "r1":        levels["r1"],
            "r2":        levels["r2"],
            "rsi_14":    round(rsi14_val, 1),
            "atr_14":    round(atr14_val, digits),
            "trend":     trend,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
