"""El escenario de la simulación semanal, sacado solo de la `Lectura` de la estrategia."""
from __future__ import annotations

import json
import shutil
import subprocess
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


# Nunca sale sin simulación por una lectura incómoda: sale condicionada al nivel a vigilar
# (director, 2026-10-12). El stop queda media volatilidad 4H al otro lado del nivel.

def test_en_prueba_la_simulacion_es_el_retesteo_del_nivel():
    e = op.escenario(fx.lectura(estado="PRUEBA"), 2)  # precio 4000 sobre la línea en 3950
    assert e.simulable and e.entrada_pendiente and e.condicion == "retesteo"
    assert (e.direccion, e.entrada, e.stop, e.objetivo) == ("ALCISTA", 3950.0, 3940.0, 3980.0)


def test_sin_invalidacion_la_simulacion_espera_el_quiebre():
    e = op.escenario(fx.lectura(invalidacion=None), 2)  # el nivel a vigilar queda en el precio
    assert e.simulable and e.condicion == "quiebre"
    assert (e.entrada, e.stop, e.objetivo) == (4000.0, 3990.0, 4030.0)


def test_pegado_al_nivel_la_simulacion_es_el_retesteo_con_stop_con_margen():
    e = op.escenario(fx.lectura(precio=4000.0, invalidacion=3996.0, atr=20.0), 2)  # 4 < 5
    assert e.simulable and e.condicion == "retesteo"
    assert (e.entrada, e.stop, e.objetivo) == (3996.0, 3986.0, 4026.0)


def test_del_otro_lado_de_la_invalidacion_espera_el_cierre_sobre_el_nivel():
    e = op.escenario(fx.lectura(precio=3940.0, invalidacion=3950.0), 2)
    assert e.simulable and e.condicion == "quiebre" and e.direccion == "ALCISTA"
    assert op.texto_condicion(e.a_dict(), "3.950,00") == "Se activa si una vela de 4 horas cierra sobre 3.950,00."


def test_sin_volatilidad_medida_no_hay_niveles():
    e = op.escenario(fx.lectura(atr=0.0), 2)
    assert not e.simulable and "cuánto se mueve" in e.motivo


def test_la_entrada_a_precio_de_hoy_no_lleva_condicion():
    e = op.escenario(fx.lectura(), 2)
    assert e.condicion is None and op.texto_condicion(e.a_dict(), "4.000,00") is None


def test_a_dict_es_serializable_y_completo():
    d = op.escenario(fx.lectura(), 2).a_dict()
    assert set(d) == {"ticker", "estado", "direccion", "entrada", "stop", "objetivo",
                      "entrada_pendiente", "dias_objetivo", "motivo", "condicion",
                      "distancia_pct", "objetivo_parcial", "borde_opuesto"}


CONTRATO = {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01}
ESC = {"entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0}


def test_simular_redondea_el_volumen_hacia_abajo_y_recalcula_la_perdida():
    s = op.simular(CONTRATO, ESC, 100_000)
    # 100.000 / (50 × 950) = 2,105… → 2,10
    assert s["volumen"] == 2.1 and s["perdida"] == 99_750 and s["ganancia"] == 299_250
    assert s["bajo_minimo"] is False and s["perdida_pct"] is None


def test_simular_bajo_el_minimo_muestra_la_perdida_del_volumen_minimo():
    s = op.simular(CONTRATO, ESC, 100)
    assert s["volumen"] == 0.01 and s["bajo_minimo"] is True and s["perdida"] == 475


def test_simular_con_capital_da_los_porcentajes():
    s = op.simular(CONTRATO, ESC, 100_000, capital=5_000_000)
    assert s["perdida_pct"] == 2.0 and s["ganancia_pct"] == 5.99


@pytest.mark.parametrize("perdida", [None, 0, -5])
def test_simular_sin_perdida_aceptable_no_calcula(perdida):
    assert op.simular(CONTRATO, ESC, perdida) is None


def test_mitad_hacia_arriba_como_math_round():
    c = {"clp_unidad": 1.0, "vol_min": 1.0, "vol_paso": 1.0}
    s = op.simular(c, {"entrada": 10.0, "stop": 9.5, "objetivo": 11.5}, 0.5)
    assert s["perdida"] == 1  # round() de Python daría 0


CASOS_JS = [
    (CONTRATO, ESC, 100_000, None),
    (CONTRATO, ESC, 100, None),
    (CONTRATO, ESC, 100_000, 5_000_000),
    ({"clp_unidad": 6.83, "vol_min": 0.1, "vol_paso": 0.1}, {"entrada": 14567.0, "stop": 14610.0,
                                                             "objetivo": 14438.0}, 37_777, 1_234_567),
    (CONTRATO, ESC, 0, None),
    (CONTRATO, {"entrada": 4000.0, "stop": 4000.0, "objetivo": 4000.0}, 100_000, None),
    ({"clp_unidad": 0.0, "vol_min": 0.01, "vol_paso": 0.01}, ESC, 100_000, None),
]


@pytest.mark.parametrize("c,e,perdida,capital", CASOS_JS)
def test_el_js_del_panel_simula_igual_que_python(c, e, perdida, capital):
    node = shutil.which("node")
    if not node:
        pytest.skip("sin node para correr el JavaScript del panel")
    js = op.SIMULADOR_JS.read_text(encoding="utf-8")
    llamada = f"console.log(JSON.stringify(simular({json.dumps(c)}, {json.dumps(e)}, {json.dumps(perdida)}, {json.dumps(capital)})));"
    salida = subprocess.run([node, "-e", js + "\n" + llamada], capture_output=True, text=True, check=True)
    assert json.loads(salida.stdout) == op.simular(c, e, perdida, capital)


def test_sin_atr_tendencia_no_simula():
    e = op.escenario(fx.lectura(atr=0.0), 2)
    assert not e.simulable and "cuánto se mueve el activo" in e.motivo


def test_sin_atr_rango_no_simula():
    e = op.escenario(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                                rango=(14567.0, 14206.0), atr=0.0), 0)
    assert not e.simulable and "cuánto se mueve el activo" in e.motivo


def test_simular_con_entrada_igual_a_stop_devuelve_none():
    assert op.simular(CONTRATO, {"entrada": 4000.0, "stop": 4000.0, "objetivo": 4000.0}, 100_000) is None


def test_simular_con_contrato_sin_valor_devuelve_none():
    assert op.simular({"clp_unidad": 0.0, "vol_min": 0.01, "vol_paso": 0.01}, ESC, 100_000) is None



def test_escenario_rango_cat_produce_objetivo_parcial_y_borde_opuesto():
    from estrategia.contrato import lectura_de_dict

    fixture_path = RAIZ / "tests" / "fixtures" / "analista" / "oportunidad_cat_2026-10-26.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    lec = lectura_de_dict(data["datos"]["activos"][0]["lectura"])
    esc = op.escenario(lec, 2)
    assert esc.objetivo_parcial is True
    assert esc.borde_opuesto == 821.39
    assert esc.objetivo == 702.76
    assert esc.distancia_pct == 1.26


def test_escenario_rango_1_a_3_excede_borde_contrario_queda_limitado_al_borde():
    # En rango, si el 1:3 proyectado sobrepasa el borde contrario, se limita al borde y no es parcial.
    lec = fx.lectura(ticker="TEST", estado="RANGO", direccion="LATERAL", precio=105.0,
                     rango=(120.0, 100.0), vigilar=100.0, atr=30.0)
    esc = op.escenario(lec, 2)
    assert esc.borde_opuesto == 120.0
    assert esc.objetivo == 120.0
    assert esc.objetivo_parcial is False
