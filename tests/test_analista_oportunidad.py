"""El escenario de la simulación semanal, sacado solo de la `Lectura` de la estrategia."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import oportunidad as op  # noqa: E402


def test_tendencia_alcista_entra_al_precio_del_lunes_con_stop_en_la_invalidacion():
    e = op.escenario(fx.lectura(precio=4000.0, invalidacion=3950.0), 2)
    assert (e.direccion, e.entrada, e.stop, e.objetivo) == ("ALCISTA", 4000.0, 3950.0, 4150.0)
    assert e.simulable and not e.entrada_pendiente
    assert e.dias_objetivo == 3.0  # 150 / ATR D1 50


def test_tendencia_bajista_proyecta_hacia_abajo():
    e = op.escenario(fx.lectura(direccion="BAJISTA", precio=4186.17, invalidacion=4227.32,
                                objetivo=4149.96), 2)
    assert (e.entrada, e.stop, e.objetivo) == (4186.17, 4227.32, 4062.72)


@pytest.mark.parametrize("estado", ["REBOTE", "RUPTURA"])
def test_rebote_y_ruptura_simulan_igual_que_la_tendencia(estado):
    e = op.escenario(fx.lectura(estado=estado), 2)
    assert e.simulable and e.objetivo == 4150.0


def test_rango_con_la_resistencia_vigilada_simula_el_falso_quiebre_bajista():
    e = op.escenario(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                                rango=(14567.0, 14206.0), atr=85.86), 0)
    assert e.direccion == "BAJISTA" and e.entrada_pendiente
    assert (e.entrada, e.stop) == (14567.0, 14610.0)  # 14567 + 0,5 × 85,86, redondeado a digits 0
    assert e.objetivo == 14438.0  # 14567 − 3 × 43


def test_rango_con_el_soporte_vigilado_simula_el_falso_quiebre_alcista():
    e = op.escenario(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14300.0,
                                rango=(14567.0, 14206.0), vigilar=14206.0, atr=86.0), 0)
    assert e.direccion == "ALCISTA" and (e.entrada, e.stop, e.objetivo) == (14206.0, 14163.0, 14335.0)


def test_rango_con_bordes_diagonales_se_identifica_por_valor_actual():
    e = op.escenario(fx.lectura(ticker="USDJPY", estado="RANGO", direccion="LATERAL", precio=157.0,
                                rango=(158.363, 155.35), vigilar=155.35, tipo_rango="diagonal", atr=0.4), 3)
    assert e.direccion == "ALCISTA" and e.entrada == 155.35


def test_prueba_no_simula():
    e = op.escenario(fx.lectura(estado="PRUEBA"), 2)
    assert not e.simulable and "prueba" in e.motivo


def test_sin_invalidacion_no_simula():
    e = op.escenario(fx.lectura(invalidacion=None), 2)
    assert not e.simulable and "invalidación" in e.motivo


def test_riesgo_bajo_un_cuarto_de_atr_no_simula():
    e = op.escenario(fx.lectura(precio=4000.0, invalidacion=3996.0, atr=20.0), 2)  # 4 < 5
    assert not e.simulable and "sobre la línea" in e.motivo


def test_precio_del_otro_lado_de_la_invalidacion_no_simula():
    e = op.escenario(fx.lectura(precio=3940.0, invalidacion=3950.0), 2)
    assert not e.simulable and "otro lado" in e.motivo


def test_a_dict_es_serializable_y_completo():
    d = op.escenario(fx.lectura(), 2).a_dict()
    assert set(d) == {"ticker", "estado", "direccion", "entrada", "stop", "objetivo",
                      "entrada_pendiente", "dias_objetivo", "motivo"}
