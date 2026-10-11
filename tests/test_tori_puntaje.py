"""El escáner de Tori ordena por situación y horizonte (spec §5)."""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import Escenario, Lectura, Linea, Prueba, Referencia  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.puntaje import CONTRA_SECUENCIA, puntuar, situacion  # noqa: E402

TRES = (Escenario("⬆️", "a", "a"), Escenario("↔️", "b", "b"), Escenario("⬇️", "c", "c"))


def _diag(rol, calidad="A+", toques=3, empinada=False, valor=100.0):
    return Linea(rol, "diagonal", ((1, 90.0), (2, 95.0)), "H4", toques, calidad, valor, empinada)


def _lectura(estado, lineas, metricas, prueba=None, direccion="ALCISTA"):
    ref = Referencia(100.0, "línea", lineas[0] if lineas else None)
    return Lectura("X", "H4", 101.0, direccion, estado, tuple(lineas), prueba, ref,
                   ref if lineas else None, None, TRES, "s", (), (), metricas)


RUPTURA = _lectura("RUPTURA", [_diag("accion"), _diag("seguridad")],
                   {"dist_seguridad_atr_d1": 0.5, "velas_desde_ruptura": 2.0})
A_PUNTO = _lectura("TENDENCIA", [_diag("accion"), _diag("seguridad")],
                   {"dist_accion_atr_d1": 0.4, "dist_seguridad_atr_d1": 1.5})
TENDENCIA = _lectura("TENDENCIA", [_diag("seguridad")], {"dist_seguridad_atr_d1": 1.5})
RANGO = _lectura("RANGO", [Linea("rango", "horizontal", ((1, 110.0),), "H4", 3, "", 110.0),
                           Linea("rango", "horizontal", ((1, 100.0),), "H4", 3, "", 100.0)],
                 {}, direccion="LATERAL")


def _orden(horizonte, *lecturas):
    return [situacion(l, P) for l in sorted(lecturas, key=lambda l: -puntuar(l, horizonte, P).puntos)]


def test_sesion_premia_la_ruptura_reciente():
    assert _orden("sesion", RANGO, TENDENCIA, A_PUNTO, RUPTURA) == ["ruptura", "a_punto", "tendencia", "rango"]


def test_semana_premia_la_linea_a_mas_cerca_y_sin_romper():
    assert _orden("semana", RANGO, TENDENCIA, RUPTURA, A_PUNTO) == ["a_punto", "ruptura", "tendencia", "rango"]


def test_los_adicionales_no_invierten_las_situaciones():
    cargada = replace(TENDENCIA, metricas={**TENDENCIA.metricas, "confluencia": 1.0,
                                           "doble_confirmacion": 1.0, "semanas_principal": 6.0})
    for h in ("sesion", "semana"):
        assert puntuar(cargada, h, P).puntos < puntuar(A_PUNTO, h, P).puntos


def test_lejos_de_la_seguridad_resta():
    lejos = replace(RUPTURA, metricas={**RUPTURA.metricas, "dist_seguridad_atr_d1": 3.0})
    assert puntuar(lejos, "sesion", P).puntos < puntuar(RUPTURA, "sesion", P).puntos
    assert puntuar(lejos, "sesion", P).desglose["lejos_de_seguridad"] < 0


def test_una_linea_empinada_o_de_dos_toques_no_es_principal():
    empinada = replace(RUPTURA, lineas=(_diag("accion", empinada=True), _diag("seguridad")))
    b = replace(RUPTURA, lineas=(_diag("accion", calidad="B", toques=2), _diag("seguridad")))
    assert situacion(empinada, P) != "ruptura" and situacion(b, P) != "ruptura"


def test_en_semana_una_a_mas_en_prueba_espera_el_cierre():
    cierre = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))
    prueba = _lectura("PRUEBA", [_diag("seguridad")], {"dist_seguridad_atr_d1": 0.2},
                      prueba=Prueba(_diag("seguridad"), 100.0, cierre))
    assert puntuar(prueba, "semana", P).excluido is not None
    assert puntuar(prueba, "sesion", P).excluido is None


def test_sin_estructura_se_excluye():
    vacia = replace(RANGO, lineas=(Linea("rango", "horizontal", ((1, 110.0),), "H4", 1, "", 110.0),
                                   Linea("rango", "horizontal", ((1, 100.0),), "H4", 1, "", 100.0)))
    for h in ("sesion", "semana"):
        assert puntuar(vacia, h, P).excluido == "sin líneas trazables: no hay estructura que leer"


def test_el_rango_no_se_excluye_en_sesion():
    assert puntuar(RANGO, "sesion", P).excluido is None


def test_sin_linea_de_seguridad_la_ruptura_no_es_setup():
    assert situacion(replace(RUPTURA, lineas=(_diag("accion"),)), P) != "ruptura"


def test_contra_la_secuencia_mayor_se_excluye():
    contra = replace(RUPTURA, metricas={**RUPTURA.metricas, "contra_secuencia": 1.0})
    for h in ("sesion", "semana"):
        assert puntuar(contra, h, P).excluido == CONTRA_SECUENCIA


def test_el_rebote_en_la_seguridad_a_mas_es_a_punto():
    assert situacion(replace(TENDENCIA, estado="REBOTE"), P) == "a_punto"


def test_el_rebote_en_una_seguridad_b_es_tendencia():
    b = replace(TENDENCIA, estado="REBOTE", lineas=(_diag("seguridad", calidad="B", toques=2),))
    assert situacion(b, P) == "tendencia"
