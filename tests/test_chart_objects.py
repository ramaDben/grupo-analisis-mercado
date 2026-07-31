"""Tests de la tool get_chart_objects: lectura del JSON exportado + contrato de error."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
        "screenshot": "usdclp_H4.png",
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
    assert res["screenshot"].endswith("usdclp_H4.png")


def test_pasa_fibos_con_el_precio_de_cada_nivel(collector, monkeypatch, tmp_path):
    """El retroceso de Fibonacci viaja tal como lo exportó el Service, con precios."""
    chart = _chart_usdclp()
    chart["fibos"] = [{
        "name": "Fibo EURUSD",
        "p1": 895.00,
        "t1": "2026-07-01 09:00",
        "p2": 880.00,
        "t2": "2026-07-20 09:00",
        "niveles": [
            {"nivel": 0.0, "porcentaje": 0.0, "precio": 880.00, "etiqueta": "0.0"},
            {"nivel": 0.618, "porcentaje": 61.8, "precio": 889.27, "etiqueta": "61.8"},
            {"nivel": 1.0, "porcentaje": 100.0, "precio": 895.00, "etiqueta": "100.0"},
        ],
    }]
    _escribir_json(tmp_path, [chart])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")

    fibo = res["fibos"][0]
    assert fibo["p1"] == 895.00
    assert [n["porcentaje"] for n in fibo["niveles"]] == [0.0, 61.8, 100.0]
    assert fibo["niveles"][1]["precio"] == 889.27


def test_chart_sin_fibos_devuelve_lista_vacia(collector, monkeypatch, tmp_path):
    """Compatibilidad con el JSON del Service anterior, que no traía la clave."""
    _escribir_json(tmp_path, [_chart_usdclp()])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["fibos"] == []


def test_sin_screenshot_devuelve_none(collector, monkeypatch, tmp_path):
    chart = _chart_usdclp()
    chart["screenshot"] = ""
    _escribir_json(tmp_path, [chart])
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")
    assert res["screenshot"] is None


def test_screenshot_se_copia_a_data_charts(collector, monkeypatch, tmp_path):
    """El PNG vigente en Common/Files se copia a data/charts y se devuelve esa ruta."""
    common = tmp_path / "common"
    charts = tmp_path / "charts"
    common.mkdir()
    _escribir_json(common, [_chart_usdclp()])
    (common / "usdclp_H4.png").write_bytes(b"fake-png")  # el Service ya lo escribió
    monkeypatch.setenv("MT5_COMMON_FILES", str(common))
    monkeypatch.setenv("MT5_CHARTS_DIR", str(charts))

    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")

    destino = charts / "usdclp_H4.png"
    assert res["screenshot"] == str(destino)
    assert destino.exists()  # se recibió en data/charts


def test_screenshot_inexistente_no_copia(collector, monkeypatch, tmp_path):
    """Si el PNG aún no está en Common/Files, devuelve esa ruta sin copiar nada."""
    common = tmp_path / "common"
    charts = tmp_path / "charts"
    common.mkdir()
    _escribir_json(common, [_chart_usdclp()])  # JSON sí, PNG no
    monkeypatch.setenv("MT5_COMMON_FILES", str(common))
    monkeypatch.setenv("MT5_CHARTS_DIR", str(charts))

    tool = _get_tool(collector)
    res = tool("USDCLP", "H4")

    assert res["screenshot"] == str(common / "usdclp_H4.png")
    assert not charts.exists()
