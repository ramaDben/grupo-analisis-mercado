"""El enchufe es una línea en config/estrategia.json (spec §2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia import registro  # noqa: E402


def test_la_estrategia_activa_esta_registrada():
    assert registro.nombre_activo() in registro.FABRICAS


def test_una_estrategia_desconocida_dice_cuales_hay():
    with pytest.raises(registro.EstrategiaDesconocida, match="tori"):
        registro.cargar("ema50")


def test_carga_desde_una_fabrica_por_nombre():
    e = registro.cargar("json", {"json": "json:JSONDecoder"})
    assert type(e).__name__ == "JSONDecoder"


def test_una_config_sin_activa_falla_con_mensaje(tmp_path):
    ruta = tmp_path / "estrategia.json"
    ruta.write_text(json.dumps({"_meta": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="activa"):
        registro.nombre_activo(ruta)
