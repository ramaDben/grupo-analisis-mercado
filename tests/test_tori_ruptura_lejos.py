"""En una ruptura con la línea rota lejos del precio se vigila el horizontal cercano.

El 2026-11-11 el oro salió con "Nivel a vigilar: 4.738,54" y el precio en 4.046: la línea
alcista rota, muy empinada, siguió subiendo después de romperse (4.581 el día anterior) y
quedó a más de 8 ATR diarios. Decisión del director ese día: a más de `lejos_atr_d1` del
precio, se vigila el horizontal estructural más cercano del lado de la línea rota.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import Linea, Referencia  # noqa: E402
from estrategia.tori import lectura as lt  # noqa: E402
from estrategia.tori import textos  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402

PRECIO, ATR, ATR_D1 = 4046.0, 32.0, 84.0
ROTA = Linea("accion", "diagonal", ((100, 3926.77), (200, 4057.7)), "H4", 2, "B", 4738.54, True)
RESISTENCIA = Linea("contexto", "horizontal", ((50, 4134.1),), "D1", 4, "", 4134.1)
OBJETIVO = Linea("objetivo", "horizontal", ((40, 4004.3),), "D1", 4, "", 4004.3)
LEJANA = Linea("contexto", "horizontal", ((30, 4400.0),), "W1", 3, "", 4400.0)


def _vigilar(rota=ROTA, lineas=(ROTA, RESISTENCIA, OBJETIVO, LEJANA), precio=PRECIO):
    return lt._vigilar(None, "RUPTURA", rota, None, [], precio,
                       lineas=list(lineas), atr=ATR, atr_d1=ATR_D1, p=P)


def test_con_la_linea_rota_lejos_se_vigila_el_horizontal_mas_cercano_de_ese_lado():
    v = _vigilar()
    assert v.precio == 4134.1 and v.linea == RESISTENCIA
    assert v.etiqueta == "resistencia"


def test_con_la_linea_rota_cerca_se_sigue_vigilando_la_linea():
    cerca = Linea("accion", "diagonal", ((100, 3926.77), (200, 4057.7)), "H4", 2, "B", 4150.0)
    v = _vigilar(rota=cerca, lineas=(cerca, RESISTENCIA, OBJETIVO))
    assert v.linea == cerca and v.precio == 4150.0


def test_sin_horizontal_entre_el_precio_y_la_linea_se_vigila_la_linea():
    v = _vigilar(lineas=(ROTA, OBJETIVO))
    assert v.linea == ROTA


def test_el_objetivo_no_sirve_de_sustituto():
    """El objetivo está del otro lado: vigilarlo sería vigilar a favor de la operación."""
    sobre = Linea("objetivo", "horizontal", ((40, 4100.0),), "D1", 4, "", 4100.0)
    v = _vigilar(lineas=(ROTA, sobre))
    assert v.linea == ROTA


def test_un_horizontal_pegado_al_precio_no_sirve_de_sustituto():
    pegado = Linea("contexto", "horizontal", ((50, 4050.0),), "D1", 4, "", 4050.0)
    v = _vigilar(lineas=(ROTA, pegado, RESISTENCIA))
    assert v.linea == RESISTENCIA


def test_en_una_ruptura_alcista_el_sustituto_es_el_soporte_bajo_el_precio():
    rota = Linea("accion", "diagonal", ((100, 4200.0), (200, 4100.0)), "H4", 2, "B", 3500.0, True)
    soporte = Linea("contexto", "horizontal", ((50, 3980.0),), "D1", 4, "", 3980.0)
    v = _vigilar(rota=rota, lineas=(rota, soporte, RESISTENCIA))
    assert v.linea == soporte and v.etiqueta == "soporte"


def _escenarios(vigilar, invalidacion=None):
    return textos.escenarios("RUPTURA", "BAJISTA", "H4", 2, PRECIO, vigilar, invalidacion,
                             Referencia(4004.3, "objetivo", OBJETIVO), None, [], rota=ROTA)


def test_los_escenarios_nombran_la_linea_rota_y_el_nivel_que_se_vigila():
    sube, medio, baja = _escenarios(Referencia(4134.1, "resistencia", RESISTENCIA))
    todo = " ".join(e.texto for e in (sube, medio, baja))
    assert "4.738,54" not in todo
    assert "ya cerró bajo la línea alcista" in baja.texto
    assert "mientras siga bajo 4.134,10" in baja.texto and "objetivo en 4.004,30" in baja.texto
    assert "4.134,10" in medio.texto and "resistencia" in medio.texto
    assert "cierra sobre 4.134,10" in sube.texto and "deja de valer" in sube.texto
    assert "soporte del rango" not in todo and "resistencia del rango" not in todo
    assert "—" not in todo and "–" not in todo


def test_con_la_linea_cerca_los_escenarios_no_cambian():
    cerca = Referencia(4738.54, "línea alcista", ROTA)
    con = _escenarios(cerca)
    sin = textos.escenarios("RUPTURA", "BAJISTA", "H4", 2, PRECIO, cerca, None,
                            Referencia(4004.3, "objetivo", OBJETIVO), None, [])
    assert con == sin
