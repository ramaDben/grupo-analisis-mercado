"""Congela el contrato DEPRECATED de las tools de calendario y noticias.

get_economic_events fue reemplazada por obtener_calendario_macro (calendario nativo
MT5). get_market_context sigue deprecada: las noticias se obtienen vía WebSearch
(investing.com + fuentes oficiales). Este test evita que una regresión reactive
silenciosamente el camino Finnhub legacy de noticias.
"""
from __future__ import annotations

from market_data_mcp.tools import context


def test_get_market_context_esta_deprecado(collector):
    context.register(collector)
    res = collector.tools["get_market_context"]()
    assert res["error"] == "DEPRECATED"
    assert "WebSearch" in res["message"]
