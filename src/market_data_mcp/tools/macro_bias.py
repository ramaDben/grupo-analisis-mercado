#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tool get_macro_bias — Sesgo macroeconómico intermercado, régimen R0-R4, SL dinámico y permisos técnicos.
Herramienta de SOLO LECTURA que consume el snapshot consolidado emitido por el orquestador macro.
"""

from __future__ import annotations

from typing import Any
from fastmcp import FastMCP

from market_data_mcp.bias_reader import cargar_macro_bias


def register(mcp: FastMCP) -> None:
    """Registra la tool get_macro_bias en el servidor FastMCP."""

    @mcp.tool(
        name="get_macro_bias",
        description=(
            "Consulta de solo lectura del sesgo cuantitativo, régimen R0-R4, SL dinámico por ATR "
            "y matriz de permisos técnicos para los activos del Playbook Intermercado. "
            "Acepta 'ALL', 'USDCLP', 'XAUUSD', 'WTI', 'BRENT', 'US100'. "
            "Contrato de error: retorna TICKER_NOT_IN_CATALOG, STALE_DATA o READ_ERROR si los datos "
            "no están disponibles o tienen más de 24h (80h en fines de semana)."
        )
    )
    def get_macro_bias(symbol: str = "ALL") -> dict[str, Any]:
        """Obtiene el sesgo macroeconómico, régimen y gestión de riesgo para el símbolo solicitado."""
        return cargar_macro_bias(symbol=symbol)
