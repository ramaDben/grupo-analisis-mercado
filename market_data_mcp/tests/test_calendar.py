"""Tests del calendario macro nativo MT5: lectura JSON + tool con contrato de error."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from market_data_mcp import mt5_client


def _ts(delta_min: int = 0) -> str:
    """generated_at relativo a ahora, formato del JSON."""
    return (datetime.now() + timedelta(minutes=delta_min)).strftime("%Y-%m-%d %H:%M")


def _payload(generated_delta_min: int = -10, eventos=None) -> dict:
    return {
        "generated_at": _ts(generated_delta_min),
        "server_tz_note": "hora servidor MT5 (broker actual = hora Chile)",
        "eventos": eventos if eventos is not None else [],
    }


def test_leer_calendario_json_parsea_archivo(tmp_path: Path):
    archivo = tmp_path / "calendario_macro.json"
    archivo.write_text(json.dumps(_payload(eventos=[{"event_id": 1}])), encoding="utf-8")
    data = mt5_client.leer_calendario_json(archivo)
    assert data["eventos"][0]["event_id"] == 1
    assert "generated_at" in data


def test_leer_calendario_json_archivo_ausente_lanza(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        mt5_client.leer_calendario_json(tmp_path / "no_existe.json")
