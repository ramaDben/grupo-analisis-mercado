"""Tests para Tori en marco intradía 1H (Encargo A)."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import estrategia_conformidad as conf  # noqa: E402
from estrategia import tori  # noqa: E402
from estrategia.contrato import Lectura, VelaEnCurso  # noqa: E402
from estrategia.procedencia import validar  # noqa: E402

SCL = ZoneInfo("America/Santiago")


def test_marcos_intradia_declaracion():
    assert hasattr(tori, "MARCOS_INTRADIA")
    m = tori.MARCOS_INTRADIA
    assert m.contexto == ("W1", "D1", "H4")
    assert m.operativo == "H1"
    assert m.velas == {"W1": 156, "D1": 250, "H4": 180, "H1": 600}
    assert m.etiquetas["W1"] == tori.MARCOS.etiquetas["W1"]
    assert m.etiquetas["D1"] == tori.MARCOS.etiquetas["D1"]
    assert m.etiquetas["H4"] == tori.MARCOS.etiquetas["H4"]
    assert m.etiquetas["H1"].nombre == "intradía"
    assert m.etiquetas["H1"].duracion == "de 8 a 10 horas"


def test_tori_default_conserva_h4():
    t_def = tori.crear()
    assert t_def.marcos.operativo == "H4"
    assert t_def.marcos == tori.MARCOS
    assert tori.Tori().marcos.operativo == "H4"


def test_crear_intradia_instancia_tori_con_marcos_intradia():
    assert hasattr(tori, "crear_intradia")
    t_intra = tori.crear_intradia()
    assert isinstance(t_intra, tori.Tori)
    assert t_intra.marcos == tori.MARCOS_INTRADIA
    assert t_intra.marcos.operativo == "H1"


def test_tori_intradia_lee_serie_sintetica_y_devuelve_lectura_en_h1():
    t_intra = tori.crear_intradia()
    velas = conf.velas_de(t_intra, semilla=11)
    lectura = t_intra.leer("EURUSD", velas, digits=4)
    assert isinstance(lectura, Lectura)
    assert lectura.marco == "H1"
    assert lectura.ticker == "EURUSD"
    assert len(lectura.escenarios) == 3
    assert lectura.vela == int(velas["H1"]["time"].iloc[-1])


def test_tori_intradia_con_vela_en_curso():
    t_intra = tori.crear_intradia()
    velas = conf.velas_de(t_intra, semilla=11)
    apertura = int(velas["H1"]["time"].iloc[-1]) + 3600
    cierre = datetime.fromtimestamp(apertura + 3600, tz=SCL)
    lectura = t_intra.leer("EURUSD", velas, digits=4, en_curso=VelaEnCurso(apertura, 105.0, cierre))
    assert isinstance(lectura, Lectura)
    assert lectura.marco == "H1"


def test_procedencia_declara_decision_director_2026_10_21():
    proc = tori.PROCEDENCIA
    assert validar(proc) == []
    encontrado = False
    for f in proc.fundamentos:
        if any("2026-10-21" in origen for origen in f.origen):
            encontrado = True
            assert "1H" in f.regla or "intradía" in f.regla
            assert "2.11" in f.no_probado or "doctrina" in f.no_probado
    assert encontrado, "No se encontró el fundamento con la decisión del director del 2026-10-21"
