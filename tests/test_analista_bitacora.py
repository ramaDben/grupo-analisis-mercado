"""Bitácora de los planes entregados y su desenlace."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

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
    assert e["vela"] == fx.PLAN["niveles"]["vela"] and e["desenlace"] is None
    assert len(e["huella_html"]) == 64 and e["analista"] == "director"


def test_sin_plan_no_anota(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["datos"]["plan"] = {"hay_plan": False, "sesgo": "Alcista", "motivo": "m"}
    ruta = tmp_path / "b.json"
    assert not bt.anotar(pieza, _html(tmp_path), "d", AHORA, ruta)
    assert not ruta.exists()


def _serie(cierres, desde="2026-10-08 09:00:00"):
    cierres = [float(c) for c in cierres]
    return pd.DataFrame({"time": pd.date_range(desde, periods=len(cierres), freq="h"), "open": cierres,
                         "close": cierres, "high": [c + 0.5 for c in cierres], "low": [c - 0.5 for c in cierres]})


def _entrada(creada: datetime, gatillo: float) -> dict:
    return {"creada": creada.isoformat(), "ticker": "T", "alcista": True, "gatillo": gatillo,
            "invalidacion": 90.0, "vela": "2026-10-08 09:00:00", "desenlace": None}


def test_completar_solo_las_de_mas_de_24_h(tmp_path):
    ruta = tmp_path / "b.json"
    ruta.write_text(json.dumps([_entrada(AHORA - timedelta(hours=30), 100.4),
                                _entrada(AHORA - timedelta(hours=2), 100.4)]), encoding="utf-8")
    # Plano hasta la vela de entrega; después cruza el gatillo y sigue subiendo.
    df = _serie([100] * 60 + [100 + k for k in range(1, 40)], desde="2026-10-05 22:00:00")
    df.loc[df["time"] == pd.Timestamp("2026-10-08 09:00:00"), "close"] = 100.0
    assert bt.completar(lambda t: df, AHORA, ruta) == 1
    primera, segunda = json.loads(ruta.read_text(encoding="utf-8"))
    assert primera["desenlace"] == "activado_recorrido" and segunda["desenlace"] is None


def test_no_se_activo(tmp_path):
    ruta = tmp_path / "b.json"
    ruta.write_text(json.dumps([_entrada(AHORA - timedelta(hours=30), 500.0)]), encoding="utf-8")
    df = _serie([100] * 120, desde="2026-10-05 22:00:00")
    bt.completar(lambda t: df, AHORA, ruta)
    assert json.loads(ruta.read_text(encoding="utf-8"))[0]["desenlace"] == "no_se_activo"


def test_la_bitacora_versionada_existe_y_es_una_lista():
    assert json.loads(bt.RUTA.read_text(encoding="utf-8")) == [] or isinstance(
        json.loads(bt.RUTA.read_text(encoding="utf-8")), list)
