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
    s = serie_de(vs.desde_vertices([130, *ALCISTA], 12))  # 4H: unas 47 velas entre toques; la semana son 30
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
    # 18 velas por tramo: 2 toques, mas de una semana y Punto B lejos del final,
    # asi que la unica causa posible de B es el segundo toque que falta.
    s = serie_de(vs.desde_vertices([130, 100, 112, 106, 124, 120], 18))
    t = trazar(s, "alcista", P)
    assert t is not None
    c = calificar(t, s, P)
    assert len(t.toques) == 2 and c.semanas >= 1 and not c.punto_b_reciente
    assert c.calidad == "B"


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


def test_la_serie_alcista_normal_no_es_empinada():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    t = trazar(s, "alcista", P)
    assert t is not None
    assert not calificar(t, s, P).empinada


def test_a_mas_por_velas_entre_anclas():
    from estrategia.tori import PARAMETROS_M15
    from estrategia.tori.lineas import Trazo

    s = serie_de(vs.desde_vertices([100, 110, 105, 120, 115], 10, paso=900))
    t30 = Trazo("alcista", i_a=0, p_a=100.0, i_b=30, p_b=103.0, toques=(0, 15, 30), i_ruptura=None)
    c30 = calificar(t30, s, PARAMETROS_M15)
    assert c30.calidad == "A+"

    t29 = Trazo("alcista", i_a=0, p_a=100.0, i_b=29, p_b=103.0, toques=(0, 15, 29), i_ruptura=None)
    c29 = calificar(t29, s, PARAMETROS_M15)
    assert c29.calidad == "B"


def test_a_mas_por_velas_respeta_punto_b_reciente():
    from estrategia.tori import PARAMETROS_M15
    from estrategia.tori.lineas import Trazo

    s = serie_de(vs.desde_vertices([100, 120], 50, paso=900))
    i_b = len(s) - 3
    i_a = i_b - 40
    t = Trazo("alcista", i_a=i_a, p_a=100.0, i_b=i_b, p_b=104.0, toques=(i_a, i_a + 20, i_b), i_ruptura=None)
    c = calificar(t, s, PARAMETROS_M15)
    assert c.punto_b_reciente
    assert c.calidad == "B"


def test_sin_velas_ab_min_conserva_regla_semanal():
    from estrategia.tori.lineas import Trazo

    s = serie_de(vs.desde_vertices([100, 110, 105, 120, 115], 10, paso=900))
    t30 = Trazo("alcista", i_a=0, p_a=100.0, i_b=30, p_b=103.0, toques=(0, 15, 30), i_ruptura=None)
    c_p = calificar(t30, s, P)
    assert c_p.semanas < 1.0
    assert c_p.calidad == "B"

