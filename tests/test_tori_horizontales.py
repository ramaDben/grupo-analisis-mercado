from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.horizontales import bordes_rango, detectar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

RANGO = [100, 110, 100, 110, 100, 110, 100, 105]


def test_detecta_el_techo_y_el_piso_con_sus_toques():
    s = serie_de(vs.desde_vertices(RANGO, 10))
    niveles = detectar(s, P)
    assert any(abs(h.precio - 110.2) < 0.3 and h.toques >= 3 for h in niveles)
    assert any(abs(h.precio - 99.8) < 0.3 and h.toques >= 3 for h in niveles)


def test_los_mas_cercanos_al_precio_van_primero():
    s = serie_de(vs.desde_vertices(RANGO, 10))
    niveles = detectar(s, P)
    assert len(niveles) >= 2
    distancias = [abs(h.precio - s.closes[-1]) for h in niveles]
    assert distancias == sorted(distancias)


def test_los_bordes_del_rango_cuentan_sus_toques():
    # 5 velas por tramo: la ventana de velas_rango debe abarcar al menos dos maximos y dos minimos.
    s = serie_de(vs.desde_vertices(RANGO, 5))
    techo, piso = bordes_rango(s, P)
    assert abs(techo.precio - 110.2) < 1e-9 and abs(piso.precio - 99.8) < 1e-9
    assert techo.toques >= 2 and piso.toques >= 2
