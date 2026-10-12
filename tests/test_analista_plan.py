"""Plan de escenarios del informe de activo: sale de la `Lectura` de la estrategia (enchufe, S7).

Sin estadística, sin objetivo fijo y sin recorrido (spec §8.4): el gatillo es lo que la
estrategia vigila, la invalidación es su línea de seguridad y la salida es la suya.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import plan as pl  # noqa: E402
from estrategia.contrato import SCL, Escenario, Lectura, Linea, Prueba, Referencia  # noqa: E402

SEG = Linea("seguridad", "diagonal", ((100, 3980.0), (200, 3990.0)), "H4", 3, "A+", 3995.0)
ACC = Linea("accion", "diagonal", ((150, 4040.0), (250, 4030.0)), "H4", 2, "B", 4020.0)
ESC = (Escenario("⬆️", "Cierre sobre 4.020,00", "Si una vela de 4 horas cierra sobre 4.020,00, la tendencia retoma."),
       Escenario("↔️", "Entre 3.995,00 y 4.020,00", "Mientras siga entre las dos líneas, todavía no hay ruptura."),
       Escenario("⬇️", "Cierre bajo 3.995,00", "Si una vela de 4 horas cierra bajo 3.995,00, la tendencia deja de valer."))
SALIDA = "La posición se cierra cuando una vela de 4 horas cierra al otro lado de la línea de seguridad, hoy en 3.995,00. No hay objetivo fijo."


def _lectura(**cambios):
    base = Lectura(ticker="XAUUSD", marco="H4", precio=4010.0, direccion="ALCISTA", estado="TENDENCIA",
                   lineas=(SEG, ACC), en_prueba=None, vigilar=Referencia(4020.0, "línea bajista", ACC),
                   invalidacion=Referencia(3995.0, "línea alcista de seguridad", SEG), objetivo=None,
                   escenarios=ESC, salida=SALIDA, conceptos=(), avisos=(), metricas={}, vela=250)
    return replace(base, **cambios)


def test_el_plan_sale_de_la_lectura():
    p = pl.armar(_lectura(), 2, "Oro")
    assert p["hay_plan"] and p["sesgo"] == "Alcista"
    assert p["gatillo"] == ESC[0].texto  # el escenario a favor de la estrategia, tal cual
    assert "3.995,00" in p["invalidacion"] and "línea alcista de seguridad" in p["invalidacion"]
    assert p["salida"] == SALIDA
    assert p["estado"].startswith("Armado")
    assert p["niveles"] == {"gatillo": 4020.0, "invalidacion": 3995.0, "vela": 250}


def test_sin_estadistica_ni_recorrido_ni_objetivo():
    p = pl.armar(_lectura(), 2, "Oro")
    assert "estadistica" not in p and "recorrido" not in p and "objetivo" not in p


def test_la_ruptura_esta_activada_y_la_prueba_espera_el_cierre():
    assert pl.armar(_lectura(estado="RUPTURA"), 2, "Oro")["estado"].startswith("Activado")
    prueba = _lectura(estado="PRUEBA", en_prueba=Prueba(ACC, 4019.0, datetime(2026, 10, 12, 13, 0, tzinfo=SCL)))
    p = pl.armar(prueba, 2, "Oro")
    assert p["estado"].startswith("En prueba") and "13:00" in p["estado"]


def test_en_rango_o_sin_linea_de_seguridad_no_hay_plan():
    assert not pl.armar(_lectura(estado="RANGO", direccion="LATERAL"), 2, "Oro")["hay_plan"]
    sin_seguridad = pl.armar(_lectura(invalidacion=None), 2, "Oro")
    assert not sin_seguridad["hay_plan"] and sin_seguridad["motivo"]


def test_el_bajista_usa_su_escenario_a_favor():
    p = pl.armar(_lectura(direccion="BAJISTA"), 2, "Oro")
    assert p["sesgo"] == "Bajista" and p["gatillo"] == ESC[2].texto


def test_los_textos_del_plan_no_llevan_guion_largo():
    p = pl.armar(_lectura(), 2, "Oro")
    assert all("—" not in str(v) and "–" not in str(v) for v in p.values())


def test_si_lo_que_se_vigila_es_la_seguridad_la_tendencia_esta_vigente_y_no_armada():
    p = pl.armar(_lectura(vigilar=Referencia(3995.0, "línea alcista de seguridad", SEG)), 2, "Oro")
    assert p["estado"].startswith("Vigente")
