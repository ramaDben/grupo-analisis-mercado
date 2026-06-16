"""Tests de la tool get_chart_objects: lectura del JSON exportado + contrato de error."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from market_data_mcp.tools import chart_objects

_SANTIAGO = ZoneInfo("America/Santiago")


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_tool(collector):
    """Registra la tool en el collector y devuelve la función get_chart_objects."""
    chart_objects.register(collector)
    return collector.tools["get_chart_objects"]


def _generated_now() -> str:
    return datetime.now(tz=_SANTIAGO).strftime("%Y-%m-%d %H:%M")


def _escribir_json(directorio, charts, generated_at=None) -> None:
    payload = {
        "generated_at": generated_at or _generated_now(),
        "server_tz_note": "hora servidor MT5",
        "charts": charts,
    }
    (directorio / "chart_objects.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _chart_usdclp(current=889.60):
    return {
        "symbol": "USDCLP",
        "timeframe": "H4",
        "digits": 2,
        "current_price": current,
        "screenshot": "usdclp_H4_2026-06-16_12-30.png",
        "hlines": [
            {"name": "R", "price": 895.00},
            {"name": "S", "price": 884.00},
            {"name": "R2", "price": 892.50},
        ],
        "trendlines": [{"name": "T", "valor_actual": 890.0, "pendiente": "alcista"}],
        "channels": [{"name": "C", "tipo": "equidistant", "banda_superior": 900.0, "banda_inferior": 880.0}],
        "rectangles": [{"name": "Z", "min": 884.0, "max": 892.0}],
    }


# ── contrato de error ───────────────────────────────────────────────────────────

def test_ticker_invalido(collector, monkeypatch, tmp_path):
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("NOEXISTE", "H4")
    assert res["error"] == "TICKER_NOT_FOUND"


def test_env_var_no_seteada(collector, monkeypatch):
    monkeypatch.delenv("MT5_COMMON_FILES", raising=False)
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["error"] == "MT5_COMMON_FILES_UNSET"


def test_archivo_ausente(collector, monkeypatch, tmp_path):
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["error"] == "NO_OBJECTS_FILE"


def test_dato_stale(collector, monkeypatch, tmp_path):
    viejo = (datetime.now(tz=_SANTIAGO) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
    _escribir_json(tmp_path, [_chart_usdclp()], generated_at=viejo)
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["error"] == "OBJECTS_STALE"


def test_chart_inexistente(collector, monkeypatch, tmp_path):
    _escribir_json(tmp_path, [_chart_usdclp()])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "M15")  # exportado H4, no M15
    assert res["error"] == "CHART_NOT_FOUND"


# ── camino feliz + clasificación ────────────────────────────────────────────────

def test_clasifica_soporte_resistencia(collector, monkeypatch, tmp_path):
    _escribir_json(tmp_path, [_chart_usdclp(current=889.60)])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")

    assert "error" not in res
    # bajo precio -> soporte; sobre precio -> resistencia
    assert res["soportes"] == [884.00]
    # resistencias ordenadas ascendente (más cercana primero)
    assert res["resistencias"] == [892.50, 895.00]
    assert res["current_price"] == 889.60
    assert res["source"] == "mt5_objects"


def test_pasa_trendlines_canales_rectangulos_y_screenshot(collector, monkeypatch, tmp_path):
    _escribir_json(tmp_path, [_chart_usdclp()])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "h4")  # timeframe case-insensitive

    assert res["timeframe"] == "H4"
    assert res["trendlines"][0]["pendiente"] == "alcista"
    assert res["channels"][0]["banda_superior"] == 900.0
    assert res["rectangles"][0]["max"] == 892.0
    assert res["screenshot"].endswith("usdclp_H4_2026-06-16_12-30.png")


def test_sin_screenshot_devuelve_none(collector, monkeypatch, tmp_path):
    chart = _chart_usdclp()
    chart["screenshot"] = ""
    _escribir_json(tmp_path, [chart])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["screenshot"] is None
