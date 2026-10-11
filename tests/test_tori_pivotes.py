from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.pivotes import serie_de, zigzag  # noqa: E402


def test_zigzag_marca_los_giros_mayores_en_orden():
    df = vs.desde_vertices([100, 112, 106, 118], 12)
    giros = zigzag(df.to_dict("records"), 3.0)
    # El primer giro confirma también el mínimo de partida.
    assert [t for _, _, t in giros] == ["L", "H", "L"]
    assert [round(p, 1) for _, p, _ in giros] == [99.8, 112.2, 105.8]


def test_el_grafico_usa_el_mismo_zigzag():
    pytest.importorskip("PIL")  # extra `stories`: el CI corre sin él
    import tradingview_grafico

    assert tradingview_grafico._zigzag is zigzag


def test_serie_de_calcula_el_atr_como_media_simple_del_rango_verdadero():
    df = vs.desde_vertices([100, 112], 12)  # cada vela sube 1 y tiene 0,2 de mecha a cada lado
    s = serie_de(df)
    assert len(s) == 12
    assert abs(s.atr - 1.4) < 1e-9
