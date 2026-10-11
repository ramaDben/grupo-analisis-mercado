"""Trazado de Tori (doctrina §2.1 y §4, reglas 2, 3 y 6)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.lineas import trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

# Mínimos 100, 106 y 112 alineados (pendiente 0,25 por vela), y un retroceso al final.
ALCISTA = [100, 112, 106, 118, 112, 124, 119]
# Espejo: máximos 124, 118 y 112 alineados, y un tramo final que rompe hacia arriba.
BAJISTA_ROTA = [124, 112, 118, 106, 112, 100]


def _respeta(s, t, tol):
    fin = t.i_ruptura if t.i_ruptura is not None else len(s)
    for i in range(t.i_a, fin):
        if t.sentido == "alcista":
            assert s.lows[i] >= t.valor(i) - tol - 1e-9, f"la vela {i} cruza la línea"
        else:
            assert s.highs[i] <= t.valor(i) + tol + 1e-9, f"la vela {i} cruza la línea"


def test_la_alcista_se_ancla_en_el_minimo_y_junta_los_tres_toques():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    t = trazar(s, "alcista", P)
    assert t is not None and t.i_a == 0 and abs(t.p_a - 99.8) < 1e-9
    assert len(t.toques) >= 3 and t.vigente
    assert abs(t.pendiente - 0.25) < 1e-9
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_ninguna_vela_cruza_la_linea_elegida_ni_con_una_mecha_suelta():
    df = vs.desde_vertices(ALCISTA, 12)
    df.loc[60, "low"] = df.loc[60, "low"] - 4.0  # una mecha que perfora y vuelve
    s = serie_de(df)
    t = trazar(s, "alcista", P)
    if t is not None:
        _respeta(s, t, P.tolerancia_toque_atr * s.atr)
        assert t.vigente, "una mecha no es ruptura"


def test_el_cierre_al_otro_lado_es_ruptura():
    df = vs.desde_vertices(BAJISTA_ROTA, 12)
    subida = vs.desde_vertices([100, 118], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    s = serie_de(pd.concat([df, subida], ignore_index=True))
    t = trazar(s, "bajista", P)
    assert t is not None and t.i_a == 0 and t.i_ruptura is not None
    assert s.closes[t.i_ruptura] > t.valor(t.i_ruptura)
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_sin_segundo_punto_no_hay_linea():
    s = serie_de(vs.desde_vertices([120, 100], 24))  # el mínimo es la última vela
    assert trazar(s, "alcista", P) is None


def test_una_linea_plana_no_es_diagonal():
    s = serie_de(vs.desde_vertices([100, 110, 100, 110, 100, 110], 10))
    assert trazar(s, "alcista", P) is None
    assert trazar(s, "bajista", P) is None
