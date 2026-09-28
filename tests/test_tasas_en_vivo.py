"""Rendimientos del Tesoro en vivo (decisión del director, 2026-09-28).

La curva de FRED llega con uno a cuatro días hábiles de rezago, y el carrusel
publicaba "+24 bps en 5 días (dato al 24 Sep)" un lunes 28 con el mercado en vivo
moviéndose. Este módulo lee el rendimiento al contado del día. Nunca lanza: una
fuente caída devuelve {} y el consumidor cae a FRED con la fecha a la vista.
"""
from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from market_data_mcp import tasas_en_vivo as tv

NY = ZoneInfo("America/New_York")


def _respuesta(*quotes: dict) -> bytes:
    return json.dumps({"FormattedQuoteResult": {"FormattedQuote": list(quotes)}}).encode("utf-8")


US10Y = {"symbol": "US10Y", "last": "5.234%", "previous_day_closing": "5.181%",
         "last_time": "2026-09-28T09:31:46.000-0400"}
US2Y = {"symbol": "US2Y", "last": "4.918%", "previous_day_closing": "4.864%",
        "last_time": "2026-09-28T09:31:45.000-0400"}


def test_lee_valor_cierre_previo_y_variacion_del_dia():
    pedidas = []

    def descargar(url):
        pedidas.append(url)
        return _respuesta(US10Y, US2Y)

    r = tv.rendimientos_en_vivo(("DGS2", "DGS10"), descargar=descargar)
    assert len(pedidas) == 1, "una sola consulta para todas las series"
    assert r["DGS10"]["valor"] == 5.234
    assert r["DGS10"]["cierre_previo"] == 5.181
    assert r["DGS10"]["delta_1d_bps"] == 5.3
    assert r["DGS2"]["delta_1d_bps"] == 5.4
    assert r["DGS10"]["fecha"] == "2026-09-28"
    assert r["DGS10"]["momento"] == datetime(2026, 9, 28, 9, 31, 46, tzinfo=NY)


def test_una_fuente_caida_devuelve_vacio_y_no_lanza():
    def cae(url):
        raise OSError("sin red")

    assert tv.rendimientos_en_vivo(("DGS10",), descargar=cae) == {}


def test_una_respuesta_rota_devuelve_vacio():
    assert tv.rendimientos_en_vivo(("DGS10",), descargar=lambda u: b"<html>") == {}


def test_una_cotizacion_sin_valor_se_omite_y_no_se_inventa():
    sin_valor = {**US2Y, "last": ""}
    r = tv.rendimientos_en_vivo(("DGS2", "DGS10"), descargar=lambda u: _respuesta(US10Y, sin_valor))
    assert set(r) == {"DGS10"}


def test_sin_cierre_previo_la_variacion_es_null_y_nunca_cero():
    sin_previo = {**US10Y, "previous_day_closing": ""}
    r = tv.rendimientos_en_vivo(("DGS10",), descargar=lambda u: _respuesta(sin_previo))
    assert r["DGS10"]["delta_1d_bps"] is None


def test_una_serie_sin_simbolo_conocido_no_se_consulta():
    assert tv.rendimientos_en_vivo(("DFII10",), descargar=lambda u: _respuesta(US10Y)) == {}
