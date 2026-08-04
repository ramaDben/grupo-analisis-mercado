"""Tests de la tool get_open_positions: lectura del terminal + contrato de error."""
from __future__ import annotations

from types import SimpleNamespace

from market_data_mcp import mt5_client
from market_data_mcp.tools import positions


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_tool(collector):
    """Registra la tool en el collector y devuelve la función get_open_positions."""
    positions.register(collector)
    return collector.tools["get_open_positions"]


def _posicion(**kwargs):
    """TradePosition de MT5 falsa: solo los atributos que la tool consume."""
    base = {
        "ticket": 522813,
        "type": 0,               # POSITION_TYPE_BUY
        "volume": 0.14,
        "price_open": 1.15130,
        "sl": 1.14550,
        "tp": 1.16542,
        "price_current": 1.15144,
        "profit": 1817.42,
        "swap": -12.5,
        "time": 1785600000,      # 2026-08-01 16:00 (hora servidor MT5)
        "comment": "",
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def _mock_mt5(monkeypatch, resultado, moneda="CLP"):
    """Sustituye las dos funciones de mt5_client que la tool importa perezosamente."""
    if isinstance(resultado, Exception):
        def _get_positions(_ticker):
            raise resultado
    else:
        def _get_positions(_ticker):
            return resultado

    monkeypatch.setattr(mt5_client, "get_positions", _get_positions)
    monkeypatch.setattr(mt5_client, "get_account_currency", lambda: moneda)


# ── contrato de error ─────────────────────────────────────────────────────────

def test_ticker_invalido(collector):
    tool = _get_tool(collector)
    res = tool("NOEXISTE")
    assert res["error"] == "TICKER_NOT_FOUND"
    assert "EURUSD" in res["message"]


def test_sin_posiciones_abiertas(collector, monkeypatch):
    """Tupla vacía = el símbolo no tiene operaciones; NO es un fallo de MT5."""
    _mock_mt5(monkeypatch, ())
    tool = _get_tool(collector)
    res = tool("EURUSD")
    assert res["error"] == "NO_OPEN_POSITIONS"


def test_mt5_sin_respuesta(collector, monkeypatch):
    """None = MT5 no respondió; se distingue de la tupla vacía."""
    _mock_mt5(monkeypatch, None)
    tool = _get_tool(collector)
    res = tool("EURUSD")
    assert res["error"] == "MT5_UNAVAILABLE"


def test_mt5_lanza_excepcion(collector, monkeypatch):
    _mock_mt5(monkeypatch, RuntimeError("terminal cerrado"))
    tool = _get_tool(collector)
    res = tool("EURUSD")
    assert res["error"] == "MT5_UNAVAILABLE"
    assert "terminal cerrado" in res["message"]


# ── camino feliz ──────────────────────────────────────────────────────────────

def test_compra_con_stop_y_objetivo(collector, monkeypatch):
    _mock_mt5(monkeypatch, (_posicion(),))
    tool = _get_tool(collector)
    res = tool("EURUSD")

    assert res["ticker"] == "EURUSD"
    assert res["total"] == 1
    assert res["moneda"] == "CLP"
    assert res["source"] == "mt5_terminal"

    pos = res["posiciones"][0]
    assert pos["tipo"] == "BUY"
    assert pos["volumen"] == 0.14
    assert pos["entrada"] == 1.1513
    assert pos["sl"] == 1.1455
    assert pos["tp"] == 1.16542
    assert pos["resultado_flotante"] == 1817.42
    assert pos["ticket"] == 522813


def test_venta_sin_stop_ni_objetivo(collector, monkeypatch):
    """MT5 usa 0.0 para 'sin definir'; la tool lo traduce a None, no a 0."""
    _mock_mt5(monkeypatch, (_posicion(type=1, sl=0.0, tp=0.0),))
    tool = _get_tool(collector)
    res = tool("EURUSD")

    pos = res["posiciones"][0]
    assert pos["tipo"] == "SELL"
    assert pos["sl"] is None
    assert pos["tp"] is None


def test_precios_respetan_digits_del_catalogo(collector, monkeypatch):
    """USDCLP tiene digits 2: el precio se redondea a 2 decimales, no a 5."""
    _mock_mt5(monkeypatch, (_posicion(price_open=927.5512, sl=931.234, tp=921.789),))
    tool = _get_tool(collector)
    res = tool("USDCLP")

    pos = res["posiciones"][0]
    assert pos["entrada"] == 927.55
    assert pos["sl"] == 931.23
    assert pos["tp"] == 921.79


def test_varias_posiciones_del_mismo_simbolo(collector, monkeypatch):
    _mock_mt5(monkeypatch, (_posicion(ticket=1), _posicion(ticket=2, type=1)))
    tool = _get_tool(collector)
    res = tool("EURUSD")

    assert res["total"] == 2
    assert [p["ticket"] for p in res["posiciones"]] == [1, 2]
    assert [p["tipo"] for p in res["posiciones"]] == ["BUY", "SELL"]


def test_hora_apertura_sin_conversion_de_zona(collector, monkeypatch):
    """El epoch de MT5 se formatea tal cual (hora del servidor), sin offset local."""
    _mock_mt5(monkeypatch, (_posicion(time=1785600000),))
    tool = _get_tool(collector)
    res = tool("EURUSD")

    assert res["posiciones"][0]["abierta_en"] == "2026-08-01 16:00"
    assert "servidor" in res["tz_note"]
