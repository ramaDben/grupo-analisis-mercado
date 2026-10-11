"""El PNG de revisión dibuja cada línea de la lectura o dice cuál no pudo (gate del director)."""
from __future__ import annotations

import json
from dataclasses import replace

import pytest

import test_tori_lectura as tl

from estrategia.contrato import Linea

pytest.importorskip("matplotlib")  # extra `informe`

import tori_revision  # noqa: E402


def _lectura_y_velas():
    h4 = tl.vs.desde_vertices(tl.ALCISTA * 10, 12)  # 828 velas de 4H: 138 de D1, más que las 120 de antes
    velas = tl.velas(h4)
    return tl.leer(h4), velas


def test_dibuja_las_lineas_de_w1_y_las_de_d1_con_anclas_viejas(tmp_path):
    lectura, velas = _lectura_y_velas()
    d1, w1 = velas["D1"], velas["W1"]
    vieja = Linea("contexto", "diagonal", ((int(d1["time"].iloc[0]), 100.0), (int(d1["time"].iloc[5]), 101.0)),
                  "D1", 2, "", 110.0)
    semanal = Linea("contexto", "diagonal", ((int(w1["time"].iloc[0]), 100.0), (int(w1["time"].iloc[2]), 104.0)),
                    "W1", 2, "", 120.0)
    lectura = replace(lectura, lineas=lectura.lineas + (vieja, semanal))
    no_dibujadas = tori_revision.dibujar(tmp_path / "x.png", lectura, velas, tl.MARCOS)
    assert no_dibujadas == []
    assert (tmp_path / "x.png").exists()


def test_una_linea_que_no_se_puede_dibujar_queda_registrada(tmp_path):
    lectura, velas = _lectura_y_velas()
    fuera = Linea("contexto", "diagonal", ((1, 100.0), (2, 101.0)), "W1", 2, "", 110.0)
    lectura = replace(lectura, lineas=lectura.lineas + (fuera,))
    no_dibujadas = tori_revision.dibujar(tmp_path / "x.png", lectura, velas, tl.MARCOS)
    assert len(no_dibujadas) == 1
    assert no_dibujadas[0]["marco"] == "W1" and no_dibujadas[0]["rol"] == "contexto"
    assert "ancla" in no_dibujadas[0]["motivo"]


def test_el_resumen_lleva_las_lineas_no_dibujadas(tmp_path, monkeypatch):
    _, velas = _lectura_y_velas()
    monkeypatch.setattr(tori_revision, "RAIZ", tmp_path)
    monkeypatch.setattr(tori_revision, "velas_mt5", lambda ticker, marcos, extra=0: (velas, None))
    assert tori_revision.main(["--tickers", "XAUUSD", "--motor", "matplotlib"]) == 0
    resumen = json.loads(next(tmp_path.rglob("resumen.json")).read_text(encoding="utf-8"))
    assert resumen[0]["lineas_no_dibujadas"] == []


# Motor TradingView (pedido del director, 2026-10-11): las líneas se juzgan con el mismo
# aspecto con que las traza Tori. El HTML se prueba sin navegador.

def _datos_tv(html: str) -> dict:
    inicio = html.index("const D = ") + len("const D = ")
    return json.loads(html[inicio:html.index(";\n", inicio)])


def test_el_html_tv_trae_un_panel_por_marco_con_sus_lineas():
    lectura, velas = _lectura_y_velas()
    html, no_dibujadas = tori_revision.html_tv(lectura, velas, tl.MARCOS, 2)
    assert no_dibujadas == []
    d = _datos_tv(html)
    assert [p["marco"] for p in d["paneles"]] == ["H4", "D1", "W1"]
    h4 = d["paneles"][0]
    diagonales = [x for x in lectura.lineas if x.marco == "H4" and x.tipo == "diagonal"]
    assert len([x for x in h4["lineas"] if x["tipo"] == "diagonal"]) == len(diagonales)
    for linea, x in zip((x for x in h4["lineas"] if x["tipo"] == "diagonal"), diagonales):
        (t1, p1), _ = x.puntos
        assert linea["puntos"][0] == {"time": t1, "value": p1}  # arranca en el ancla
        assert linea["puntos"][-1]["time"] > h4["velas"][-1]["time"]  # y se proyecta a la derecha
    assert "LightweightCharts" in html and "chartReady" in html


def test_el_html_tv_registra_la_linea_que_no_puede_dibujar():
    lectura, velas = _lectura_y_velas()
    fuera = Linea("contexto", "diagonal", ((1, 100.0), (2, 101.0)), "W1", 2, "", 110.0)
    lectura = replace(lectura, lineas=lectura.lineas + (fuera,))
    _, no_dibujadas = tori_revision.html_tv(lectura, velas, tl.MARCOS, 2)
    assert [(x["marco"], x["rol"]) for x in no_dibujadas] == [("W1", "contexto")]
