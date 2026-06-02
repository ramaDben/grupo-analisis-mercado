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

        # --- Código Finnhub legacy (inalcanzable; se elimina tras validación) ---
        try:
            from mt5_client import get_upcoming_events, FINNHUB_API_KEY
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
            events = get_upcoming_events(days_ahead=days_ahead, min_impact=min_impact)
        except Exception as exc:
            return {
                "error": "FINNHUB_UNAVAILABLE",
                "message": f"Finnhub no respondió: {exc}",
            }

        if not events:
            return {
                "error": "NO_EVENTS_FOUND",
                "message": (
                    f"No hay eventos de impacto '{min_impact}' en los próximos {days_ahead} día(s). "
                    "Si es fin de semana o feriado, es comportamiento esperado."
                ),
            }

        from datetime import datetime
        return {
            "events": events,
            "filtered_by": {
                "days_ahead": days_ahead,
                "countries": ["US", "EU", "CL", "GB", "JP"],
                "min_impact": min_impact,
            },
            "source": "finnhub",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
