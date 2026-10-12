"""Tool `get_lectura`: la `Lectura` de la estrategia activa por MCP (spec §6, fase 3)."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from estrategia.contrato import SCL, Escenario, Etiqueta, Lectura, Linea, Marcos, Referencia  # noqa: E402
from market_data_mcp.tools import lectura as tool  # noqa: E402

AHORA = datetime(2026, 10, 12, 11, 0, tzinfo=SCL)


def _lec(ticker):
    lin = Linea("seguridad", "diagonal", ((100, 10.0), (200, 11.0)), "H4", 3, "A+", 11.5)
    ref = Referencia(11.5, "línea alcista de seguridad", lin)
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker=ticker, marco="H4", precio=12.0, direccion="ALCISTA", estado="TENDENCIA",
                   lineas=(lin,), en_prueba=None, vigilar=ref, invalidacion=ref, objetivo=None,
                   escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


class _Est:
    nombre = "falsa"
    marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5}, {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})

    def leer(self, ticker, velas, digits, en_curso=None):
        return _lec(ticker)


def _lector(ticker, marcos, extra):
    return {"H4": "v"}, None


def test_devuelve_la_lectura_de_la_estrategia_activa(tmp_path):
    res = tool.obtener_lectura("XAUUSD", estrategia=_Est(), lector=_lector, ahora=AHORA, base=tmp_path)
    assert res["estrategia"] == "falsa" and res["semana"] == "2026-W42"
    assert res["lectura"]["ticker"] == "XAUUSD" and res["lectura"]["direccion"] == "ALCISTA"


def test_un_ticker_fuera_del_catalogo_es_error_explicito(tmp_path):
    res = tool.obtener_lectura("NOEXISTE", estrategia=_Est(), lector=_lector, ahora=AHORA, base=tmp_path)
    assert res["error"] == "TICKER_INVALIDO" and res["message"]


def test_si_mt5_falla_el_error_es_explicito(tmp_path):
    def roto(ticker, marcos, extra):
        raise RuntimeError("MT5 no responde")

    res = tool.obtener_lectura("XAUUSD", estrategia=_Est(), lector=roto, ahora=AHORA, base=tmp_path)
    assert res["error"] == "LECTURA_NO_DISPONIBLE" and "MT5 no responde" in res["message"]


def test_la_tool_se_registra(collector):
    tool.register(collector)
    assert "get_lectura" in collector.tools
