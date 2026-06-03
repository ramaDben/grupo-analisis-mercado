"""Tool get_economic_events — calendario Finnhub con error explícito (nunca array vacío)."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_economic_events(
        days_ahead: int = 7,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Eventos económicos próximos desde Finnhub Economic Calendar.

        Retorna eventos filtrados por impacto y país, con hora en hora Chile.
        Si Finnhub no responde o no hay eventos, retorna {"error": "CÓDIGO", "message": "..."}.

        Args:
            days_ahead: Días hacia adelante a consultar (0 = solo hoy, default 7).
            min_impact: Nivel mínimo de impacto — 'high' | 'medium' | 'low' (default 'medium').

        Returns:
            {"events": [...], "filtered_by": {...}, "source": "finnhub", "generated_at": "..."}
            O {"error": "CÓDIGO", "message": "..."} si no hay datos disponibles.

        DEPRECADO: el calendario económico ahora se obtiene vía WebSearch
        (investing.com + fuentes oficiales) directamente en el comando /dato_macro.
        """
        return {
            "error": "DEPRECATED",
            "message": (
                "get_economic_events está deprecado. El calendario económico ahora "
                "se obtiene con WebSearch sobre investing.com en el comando /dato_macro. "
                "Ver docs/design/websearch-calendario-noticias.design.md."
            ),
        }
