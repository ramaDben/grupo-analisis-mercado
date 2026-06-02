"""Congela el contrato DEPRECATED de las tools de calendario y noticias.

get_economic_events y get_market_context quedaron deprecadas: el calendario y las
noticias se obtienen ahora vía WebSearch (investing.com + fuentes oficiales).
Estos tests evitan que una regresión vuelva a activar silenciosamente el camino
Finnhub legacy.
"""
from __future__ import annotations

from market_data_mcp.tools import calendar, context


def test_get_economic_events_esta_deprecado(collector):
    calendar.register(collector)
    res = collector.tools["get_economic_events"]()
    assert res["error"] == "DEPRECATED"
    assert "WebSearch" in res["message"]


def test_get_market_context_esta_deprecado(collector):
    context.register(collector)
    res = collector.tools["get_market_context"]()
    assert res["error"] == "DEPRECATED"
    assert "WebSearch" in res["message"]
