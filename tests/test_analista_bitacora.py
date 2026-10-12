"""Bitácora de los planes entregados (sin desenlace: no hay tasa de acierto, spec §8.4)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import bitacora as bt  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)


def _html(tmp_path: Path) -> Path:
    ruta = tmp_path / "x.html"
    ruta.write_text("<html>", encoding="utf-8")
    return ruta


def test_anota_una_entrada(tmp_path):
    ruta = tmp_path / "b.json"
    assert bt.anotar(fx.activo(tmp_path), _html(tmp_path), "director", AHORA, ruta)
    [e] = json.loads(ruta.read_text(encoding="utf-8"))
    assert e["ticker"] == "XAUUSD" and e["alcista"] is True and e["gatillo"] == 4131.0
    assert e["vela"] == fx.PLAN["niveles"]["vela"] and "desenlace" not in e
    assert len(e["huella_html"]) == 64 and e["analista"] == "director"


def test_sin_plan_no_anota(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["datos"]["plan"] = {"hay_plan": False, "sesgo": "Alcista", "motivo": "m"}
    ruta = tmp_path / "b.json"
    assert not bt.anotar(pieza, _html(tmp_path), "d", AHORA, ruta)
    assert not ruta.exists()


def test_la_bitacora_versionada_existe_y_es_una_lista():
    assert json.loads(bt.RUTA.read_text(encoding="utf-8")) == [] or isinstance(
        json.loads(bt.RUTA.read_text(encoding="utf-8")), list)


