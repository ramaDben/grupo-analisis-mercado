"""Tests de la tool get_symbol_spec: specs de contrato + sesiones + feriados (#104)."""
from __future__ import annotations

import json
from datetime import date, datetime, time as dtime, timezone
from types import SimpleNamespace

from market_data_mcp.tools import symbol_spec

# ── helpers ───────────────────────────────────────────────────────────────────


def _symbol_info_fake(
    trade_mode: int = 4,
    digits: int = 2,
    volume_min: float = 1.0,
    volume_step: float = 1.0,
    contract_size: float = 1.0,
    time_epoch: int | None = None,
) -> SimpleNamespace:
    """Fake del objeto SymbolInfo que retorna MetaTrader5.symbol_info()."""
    if time_epoch is None:
        time_epoch = int(datetime.now(timezone.utc).timestamp())
    return SimpleNamespace(
        trade_mode=trade_mode,
        digits=digits,
        volume_min=volume_min,
        volume_step=volume_step,
        trade_contract_size=contract_size,
        time=time_epoch,
    )


def _sesion_lunes_a_viernes(ticker, day_of_week, index, tipo):
    """Sesión 09:30-16:00 (hora servidor) de lunes a viernes; nada más."""
    if index > 0:
        return None
    # Convención MT5: 0=domingo, 1=lunes, ..., 6=sábado.
    if day_of_week in (0, 6):
        return None
    return (dtime(9, 30), dtime(16, 0))


def _sesion_sin_miercoles(ticker, day_of_week, index, tipo):
    """Como _sesion_lunes_a_viernes pero sin sesión configurada el miércoles (MT5 dow=3)."""
    if day_of_week == 3:
        return None
    return _sesion_lunes_a_viernes(ticker, day_of_week, index, tipo)


def _sesion_siempre_none(ticker, day_of_week, index, tipo):
    return None


def _registrar_con_mocks(collector, monkeypatch, get_session_fn, info=None, offset_minutes=-240):
    """Registra la tool con MT5 mockeado: symbol_info fijo + get_session parametrizable."""
    from market_data_mcp import mt5_client

    if info is None:
        info = _symbol_info_fake()

    monkeypatch.setattr(mt5_client, "get_symbol_info", lambda ticker: info)
    monkeypatch.setattr(mt5_client, "get_session", get_session_fn)
    monkeypatch.setattr(symbol_spec, "_offset_servidor_minutos", lambda info_: offset_minutes)

    symbol_spec.register(collector)
    return collector.tools["get_symbol_spec"]


# ── AC1 — registro estructural ─────────────────────────────────────────────────


def test_registro(collector):
    symbol_spec.register(collector)
    assert "get_symbol_spec" in collector.tools


# ── AC2 / CB-1 — ticker inválido ────────────────────────────────────────────────


def test_ticker_invalido(collector):
    symbol_spec.register(collector)
    res = collector.tools["get_symbol_spec"]("NOEXISTE")
    assert res == {"error": "TICKER_NOT_FOUND", "message": res["message"]}
    assert isinstance(res["message"], str) and res["message"]


# ── AC3 — camino feliz sin fecha ────────────────────────────────────────────────


def test_camino_feliz_sin_fecha(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)
    res = fn("US100.spot")

    assert "error" not in res, res
    claves_r3 = {
        "ticker", "trade_mode", "digits", "volume_min", "volume_step",
        "contract_size", "server_time", "server_utc_offset_minutes",
        "sesiones_semana", "fuente",
    }
    assert claves_r3.issubset(res.keys())
    assert res["ticker"] == "US100.spot"
    assert res["trade_mode"] == "FULL"
    assert res["fuente"] == "mt5"
    assert set(res["sesiones_semana"].keys()) == {
        "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
    }
    assert res["sesiones_semana"]["sabado"] == []
    assert res["sesiones_semana"]["domingo"] == []
    # No fijamos el offset estacional real (varía Chile/servidor según la fecha
    # en que corre el test); validamos forma y que exista exactamente 1 ventana.
    lunes = res["sesiones_semana"]["lunes"]
    assert len(lunes) == 1
    assert set(lunes[0].keys()) == {"quote", "trade"}
    for ventana in (lunes[0]["quote"], lunes[0]["trade"]):
        assert len(ventana) == 2
        for hhmm in ventana:
            assert len(hhmm) == 5 and hhmm[2] == ":"


# ── AC4 — camino feliz con fecha en día hábil normal ────────────────────────────


def test_camino_feliz_con_fecha_habil(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)
    # 2026-09-15 es martes, sin feriado NYSE. En esa fecha real, con el servidor
    # a offset -240 (equivalente a ET en horario de verano), Chile queda 1h
    # adelante (UTC-3 vs UTC-4) — igual que la nota de activos.json para los
    # índices US (09:30-16:00 ET -> 10:30-17:00 CLT).
    res = fn("US100.spot", fecha="2026-09-15")

    assert "error" not in res, res
    assert res["opera"] is True
    assert res["motivo"] is None
    assert res["horario_chile"] == {"apertura": "10:30", "cierre": "17:00"}
    assert res["fecha_consultada"] == "2026-09-15"
    assert res["calendario_feriados_fuente"] == "config/feriados_bolsa.json (NYSE)"


# ── AC5 / CB-9 — fecha de feriado NYSE (gana sobre patrón semanal) ──────────────


def test_feriado_nyse(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)
    # 2026-07-03 es viernes (con sesión en patrón semanal) y feriado NYSE.
    res = fn("US100.spot", fecha="2026-07-03")

    assert res["opera"] is False
    assert res["motivo"] == "feriado_bolsa"


# ── AC6 / CB-5 — fecha de fin de semana ─────────────────────────────────────────


def test_fin_de_semana(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)
    # 2026-07-11 es sábado.
    res = fn("US100.spot", fecha="2026-07-11")

    assert res["opera"] is False
    assert res["motivo"] == "fin_de_semana"


# ── CB-6 — día hábil sin sesión configurada ─────────────────────────────────────


def test_dia_habil_sin_sesion(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_sin_miercoles)
    # 2026-07-15 es miércoles, sin sesión configurada ese día (y sin feriado).
    res = fn("US100.spot", fecha="2026-07-15")

    assert res["opera"] is False
    assert res["motivo"] == "fuera_de_sesion_recurrente"


# ── AC7 / CB-3 — ticker sin cobertura de feriados ───────────────────────────────


def test_ticker_sin_cobertura_feriados(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)
    # XAUUSD no está mapeado a NYSE: el feriado del 2026-07-03 no debe aplicar.
    res = fn("XAUUSD", fecha="2026-07-03")

    assert res["calendario_feriados_fuente"] is None
    assert res["motivo"] != "feriado_bolsa"


# ── AC8 / CB-4 — trade_mode deshabilitado en tiempo real (fecha = hoy) ──────────


def test_trade_mode_disabled_hoy(collector, monkeypatch):
    hoy_santiago = datetime.now(symbol_spec._SANTIAGO).date()
    info = _symbol_info_fake(trade_mode=0)
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes, info=info)

    # Fuerza que el día de hoy tenga sesión configurada para aislar la señal
    # de trade_mode (evita falsos positivos si "hoy" cae en fin de semana o feriado).
    def _sesion_todos_los_dias(ticker, day_of_week, index, tipo):
        if index > 0:
            return None
        return (dtime(9, 30), dtime(16, 0))

    monkeypatch.setattr(symbol_spec, "_cargar_feriados", lambda: {})
    from market_data_mcp import mt5_client
    monkeypatch.setattr(mt5_client, "get_session", _sesion_todos_los_dias)

    res = fn("US100.spot", fecha=hoy_santiago.isoformat())

    assert res["opera"] is False
    assert res["motivo"] == "trade_mode_disabled"


# ── AC9 / CB-2 — fecha inválida ──────────────────────────────────────────────────


def test_fecha_invalida(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_lunes_a_viernes)

    for fecha_mala in ("2026-02-30", "03-07-2026"):
        res = fn("US100.spot", fecha=fecha_mala)
        assert res["error"] == "INVALID_FECHA", fecha_mala
        assert isinstance(res["message"], str) and res["message"]


# ── AC10 / CB-7 — MT5 no disponible ─────────────────────────────────────────────


def test_mt5_no_disponible(collector, monkeypatch):
    from market_data_mcp import mt5_client

    def _sin_mt5(ticker):
        raise ModuleNotFoundError("No module named 'MetaTrader5'")

    monkeypatch.setattr(mt5_client, "get_symbol_info", _sin_mt5)

    symbol_spec.register(collector)
    res = collector.tools["get_symbol_spec"]("US100.spot")

    assert res["error"] == "MT5_UNAVAILABLE"
    assert isinstance(res["message"], str) and res["message"]


# ── AC11 / CB-8 — sesión no disponible para el símbolo ──────────────────────────


def test_sesion_no_disponible(collector, monkeypatch):
    fn = _registrar_con_mocks(collector, monkeypatch, _sesion_siempre_none)
    res = fn("US100.spot")

    assert res["error"] == "SESSION_UNAVAILABLE"
    assert isinstance(res["message"], str) and res["message"]


# ── AC12 — archivo de feriados versionado (estructural) ─────────────────────────


def test_feriados_bolsa_json():
    data = json.loads(symbol_spec._FERIADOS_PATH.read_text(encoding="utf-8"))
    assert "actualizado" in data["_meta"]
    assert len(data["NYSE"]) >= 9
    assert "2026-01-01" in data["NYSE"]
    assert "2026-12-25" in data["NYSE"]


# ── unit: helpers puros ──────────────────────────────────────────────────────────


def test_parsear_fecha_iso_valida():
    assert symbol_spec._parsear_fecha_iso("2026-07-03") == date(2026, 7, 3)


def test_parsear_fecha_iso_invalida():
    assert symbol_spec._parsear_fecha_iso("2026-02-30") is None
    assert symbol_spec._parsear_fecha_iso("03-07-2026") is None
    assert symbol_spec._parsear_fecha_iso(20260703) is None  # type: ignore[arg-type]


def test_hora_str_convierte_con_offset():
    # offset -240 (ET en horario de verano) + fecha en verano austral (Chile UTC-3)
    # => 09:30 servidor -> 10:30 Chile.
    resultado = symbol_spec._hora_str(dtime(9, 30), -240, date(2026, 1, 15))
    assert resultado == "10:30"


def test_docstring_menciona_limitacion_feriados():
    doc = symbol_spec._DOCSTRING_LIMITACION
    for ticker in ("USDCLP", "XAUUSD", "WTI.spot"):
        assert ticker in doc
