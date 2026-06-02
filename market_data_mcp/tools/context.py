"""Tool get_market_context — noticias Finnhub filtradas por relevancia para el catálogo."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

# Palabras clave de relevancia: activos del catálogo + sus drivers macro
_RELEVANCE_KEYWORDS = {
    # Activos directos
    "gold", "xau", "oil", "wti", "crude", "brent", "petroleum",
    "nasdaq", "s&p", "s&p 500", "dow jones", "dow", "ndx", "spx",
    "usd", "dollar", "peso", "clp", "copper", "cobre",
    # Acciones del catálogo
    "apple", "aapl", "microsoft", "msft", "nvidia", "nvda", "amazon", "amzn",
    "jpmorgan", "jpm", "bank of america", "bac", "goldman", "sachs", "morgan stanley",
    "boeing", "caterpillar", "ge aerospace", "deere",
    # Drivers macro
    "fed", "federal reserve", "fomc", "jerome powell",
    "inflation", "cpi", "pce", "nfp", "payroll", "payrolls", "unemployment",
    "opec", "opep", "interest rate", "treasury", "yield", "bond",
    "gdp", "pmi", "jolts", "ism", "jobless claims",
    "geopolit", "iran", "china", "tariff", "trade war", "sanctions",
    "earnings", "eps", "revenue", "guidance",
    "bcch", "banco central", "tasa", "chile",
}


def _is_relevant(headline: str, body: str) -> bool:
    text = (headline + " " + body).lower()
    return any(kw in text for kw in _RELEVANCE_KEYWORDS)


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

        # --- Código Finnhub legacy (inalcanzable; se elimina tras validación) ---
        try:
            from mt5_client import get_news, FINNHUB_API_KEY
        except ImportError:
            return {
                "error": "FINNHUB_UNAVAILABLE",
                "message": "No se pudo importar mt5_client. Verificar la instalación.",
            }

        if not FINNHUB_API_KEY:
            return {
                "error": "FINNHUB_UNAVAILABLE",
                "message": "FINNHUB_API_KEY no configurada en el .env.",
            }

        try:
            # get_news usa min_hours_old con la misma semántica que within_hours
            all_news = get_news(category=category, min_hours_old=within_hours, top_n=top_n * 3)
        except Exception as exc:
            return {
                "error": "FINNHUB_UNAVAILABLE",
                "message": f"Finnhub News no respondió: {exc}",
            }

        if all_news is None:
            return {
                "error": "FINNHUB_UNAVAILABLE",
                "message": "Finnhub News retornó una respuesta nula.",
            }

        relevant = [
            n for n in all_news
            if _is_relevant(n.get("headline", ""), n.get("body", ""))
        ][:top_n]

        if not relevant:
            return {
                "error": "NO_NEWS_FOUND",
                "message": (
                    f"Sin noticias relevantes para los activos del catálogo "
                    f"en las últimas {within_hours} hora(s). "
                    "En fin de semana o mercados cerrados es comportamiento esperado."
                ),
            }

        from datetime import datetime
        return {
            "news": relevant,
            "filtered_by": {
                "category": category,
                "within_hours": within_hours,
                "top_n": top_n,
                "relevance_filter": "activos + drivers del catálogo",
            },
            "source": "finnhub",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
