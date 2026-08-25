"""Tool get_asset_levels — análisis técnico completo con RSI, S1/S2/R1/R2 y error explícito.

El cálculo vive en `market_data_mcp.analisis`, no acá. Este módulo solo expone la
función como tool MCP: la misma lógica la consume `scripts/screener_gi.py` sin
pasar por el protocolo, y tener una sola implementación es lo que garantiza que
el escáner de tandas y la tool no se separen con el tiempo.

Los nombres privados se re-exportan porque `tests/test_levels.py` los verifica
directamente (`levels._rsi`, `levels._cluster`, `levels._VALID_TICKERS`), y esos
tests son la prueba de que la extracción no cambió comportamiento.
"""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from market_data_mcp.analisis import (  # noqa: F401  (re-exportados a propósito)
    PISO_ATR_RESTANTE,
    _cluster,
    _get_support_resistance,
    _rsi,
    _swing_levels,
    analizar_activo,
)
from market_data_mcp.catalog import VALID_TICKERS as _VALID_TICKERS  # noqa: F401


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_asset_levels(ticker: str, timeframe: str = "H4") -> dict[str, Any]:
        """Análisis técnico completo: precio, S1/S2/R1/R2, RSI14, ATR14, ADX14 y tendencia.

        Solo acepta tickers del catálogo de activos del proyecto. Si MT5 no está
        disponible o el ticker no existe, retorna {"error": "CÓDIGO", "message": "..."}.

        Args:
            ticker: Símbolo MT5 del catálogo (ej: XAUUSD, USDCLP, WTI.spot, #AAPL).
            timeframe: Marco temporal MT5 (M1, M5, M15, M30, H1, H4, H12, D1, W1, MN1).

        Returns:
            Dict con: ticker, timeframe, price, s1, s2, r1, r2, rsi_14, atr_14, adx_14,
            ema_20, ema_50, ema_100, macd_line, macd_signal, macd_hist,
            bb_upper, bb_mid, bb_lower, donchian_50_high, donchian_50_low,
            donchian_50_mid, trend, timestamp.
            Ojo: ema_20 es media EXPONENCIAL (el gatillo del Playbook en H1) y bb_mid
            es la media SIMPLE de 20 de las Bandas de Bollinger. No son lo mismo.
            Con timeframe="D1" además incluye rango_hoy (high-low de la vela diaria
            en curso) y atr_restante_14 (= atr_14 - rango_hoy, con piso del 30% del
            atr_14: una tarde volátil no debe bloquear todo movimiento restante del día).
            O {"error": "CÓDIGO", "message": "..."} si el dato no está disponible.
        """
        return analizar_activo(ticker, timeframe)
