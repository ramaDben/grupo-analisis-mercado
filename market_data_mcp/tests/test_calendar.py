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


from market_data_mcp.tools import calendar


_GLOSARIO = {
    "1": {"sigla": "NFP", "nombre_es": "Nóminas no agrícolas", "explicacion": "empleos nuevos…"},
}


def _eventos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [
        {"event_id": 1, "nombre": "Nóminas no agrícolas", "pais": "Estados Unidos",
         "divisa": "USD", "impacto": "alto", "hora_servidor": f"{hoy} 09:30",
         "periodo": "Mayo 2026", "previo": "175K", "forecast": "190K", "actual": None},
        {"event_id": 99, "nombre": "Discurso menor", "pais": "Zona Euro",
         "divisa": "EUR", "impacto": "bajo", "hora_servidor": f"{hoy} 11:00",
         "periodo": "", "previo": "", "forecast": "", "actual": None},
    ]


def test_camino_feliz_filtra_impacto_y_engancha_glosario(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(eventos=_eventos_hoy()))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res, res
    assert len(res["eventos"]) == 1
    ev = res["eventos"][0]
    assert ev["event_id"] == 1
    assert ev["divisa"] == "USD"
    assert ev["periodo"] == "Mayo 2026"
    assert ev["diccionario"]["sigla"] == "NFP"
    assert res["source"] == "mt5_native"


def test_evento_sin_glosario_marca_pendiente(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(eventos=_eventos_hoy()))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="high")
    ev = res["eventos"][0]
    assert ev["glosario_pendiente"] is True
    assert "diccionario" not in ev


def test_calendario_viejo_retorna_stale(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(generated_delta_min=-200))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})
    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()
    assert res["error"] == "STALE_CALENDAR"
    assert isinstance(res["message"], str) and res["message"]
