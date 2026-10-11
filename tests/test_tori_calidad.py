"""Calidad de la línea (doctrina §2.2): A+ con 3 toques y una semana; B con 2."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.calidad import calificar  # noqa: E402
from estrategia.tori.lineas import trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

ALCISTA = [100, 112, 106, 118, 112, 124, 119]


def test_tres_toques_en_mas_de_una_semana_es_a_mas():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))  # 4H: unas 47 velas entre toques; la semana son 30
    t = trazar(s, "alcista", P)
    assert t is not None
    c = calificar(t, s, P)
    assert c.calidad == "A+" and c.semanas >= 1


def test_tres_toques_en_menos_de_una_semana_es_b():
    s = serie_de(vs.desde_vertices(ALCISTA, 12, paso=3600))  # 1H: la semana son 120 velas
    t = trazar(s, "alcista", P)
    assert t is not None
    c = calificar(t, s, P)
    assert c.calidad == "B" and c.semanas < 1


def test_dos_toques_es_b():
    s = serie_de(vs.desde_vertices([100, 112, 106, 124, 120], 12))
    t = trazar(s, "alcista", P)
    assert t is not None
    assert len(t.toques) == 2 and calificar(t, s, P).calidad == "B"


def test_un_punto_b_reciente_baja_la_calidad():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    t = trazar(s, "alcista", P)
    assert t is not None
    reciente = replace(t, i_b=len(s) - 2)
    assert calificar(reciente, s, P).punto_b_reciente
    assert calificar(reciente, s, P).calidad == "B"


def test_marca_la_linea_muy_empinada():
    s = serie_de(vs.desde_vertices([100, 140, 130, 170, 160, 200, 195], 6))
    t = trazar(s, "alcista", P)
    assert t is not None
    assert calificar(t, s, P).empinada
