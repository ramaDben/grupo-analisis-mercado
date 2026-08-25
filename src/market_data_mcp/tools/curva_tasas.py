#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tool get_curva_tasas — Curva soberana de EE.UU.: rendimientos del Tesoro, tasa real
TIPS y compensación por inflación, con deltas en puntos base.

Herramienta de SOLO LECTURA que consume la ingesta de `data central/`. La curva no es
un símbolo de mercado, así que no se puede pedir con `get_asset_levels`.
"""

from __future__ import annotations

from typing import Any
from fastmcp import FastMCP

from market_data_mcp.curva_reader import cargar_curva_tasas


def register(mcp: FastMCP) -> None:
    """Registra la tool get_curva_tasas en el servidor FastMCP."""

    @mcp.tool(
        name="get_curva_tasas",
        description=(
            "Curva soberana de EE.UU. con nivel y variación en puntos base (1 día y 5 "
            "días): DGS2, DGS10, DGS30 (rendimientos del Tesoro), DFF (tasa efectiva "
            "de fondos federales), DFII10 (tasa real TIPS 10 años) y T10YIE "
            "(compensación por inflación a 10 años), más la pendiente 2s10s. "
            "Acepta 'ALL' o el código de una serie. "
            "Incluye procedencia (Tesoro o fallback FRED) y frescura en dos ejes: "
            "antigüedad del archivo y rezago del último dato en días hábiles. "
            "Un delta que no se puede calcular viene como null, nunca como 0. "
            "Contrato de error: SERIE_NO_DISPONIBLE, STALE_DATA o READ_ERROR."
        )
    )
    def get_curva_tasas(serie: str = "ALL") -> dict[str, Any]:
        """Obtiene la curva de tasas de EE.UU. con sus variaciones en puntos base."""
        return cargar_curva_tasas(serie=serie)
