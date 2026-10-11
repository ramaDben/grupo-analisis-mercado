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
    assert tori_revision.main(["--tickers", "XAUUSD"]) == 0
    resumen = json.loads(next(tmp_path.rglob("resumen.json")).read_text(encoding="utf-8"))
    assert resumen[0]["lineas_no_dibujadas"] == []
