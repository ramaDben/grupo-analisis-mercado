"""Tool get_market_context — noticias Finnhub filtradas por relevancia para el catálogo."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_market_context(
        within_hours: int = 24,
        top_n: int = 5,
        category: str = "general",
    ) -> dict[str, Any]:
        """Noticias financieras recientes filtradas por relevancia para los activos del catálogo.

        Solo retorna noticias que mencionen activos o drivers del catálogo del proyecto
        (oro, petróleo, Nasdaq, USD, acciones del portafolio, Fed, OPEP, etc.).
        Si no hay noticias relevantes, retorna {"error": "NO_NEWS_FOUND", "message": "..."}.

        Args:
            within_hours: Solo noticias de las últimas X horas (default 24).
            top_n: Máximo de noticias a retornar (default 5).
            category: Categoría Finnhub — 'general' | 'forex' | 'crypto' | 'merger' (default 'general').

        Returns:
            {"news": [...], "filtered_by": {...}, "source": "finnhub", "generated_at": "..."}
            O {"error": "CÓDIGO", "message": "..."} si no hay datos disponibles.

        DEPRECADO: las noticias ahora se obtienen vía WebSearch (investing.com +
        fuentes oficiales) directamente en el comando /noticia.
        """
        return {
            "error": "DEPRECATED",
            "message": (
                "get_market_context está deprecado. Las noticias ahora se obtienen "
                "con WebSearch (investing.com + fuentes oficiales) en el comando /noticia. "
                "Ver docs/design/websearch-calendario-noticias.design.md."
            ),
        }
