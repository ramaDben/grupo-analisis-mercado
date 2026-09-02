#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mcp_macro_bias.py
Suite de pruebas automatizadas para el módulo bias_reader y la tool MCP get_macro_bias.
Valida contratos de Schema v2.0.0, cero mutación de archivos, staleness consciente de fines de semana y fail-closed.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from market_data_mcp.bias_reader import (
    OUTPUT_FILE_DEFAULT,
    cargar_macro_bias,
    validar_staleness,
    VALID_SYMBOLS
)


def _reloj_del_snapshot():
    """Un `now_dt` anclado al `as_of_utc` del propio snapshot versionado.

    Los dos tests de contrato de abajo validan la FORMA del payload, no su
    frescura, pero llamaban sin `now_dt` y quedaban a merced del reloj de pared
    contra un archivo que vive en git. El resultado era una bomba de tiempo: el
    2026-09-02 a las 17:53 UTC el snapshot committeado cruzó las 24 h de umbral y
    CI pasó a rojo en master y en las cinco ramas abiertas a la vez, sin que
    nadie hubiera tocado una línea de código. La última corrida verde de master
    fue a las 13:52, con el mismo commit.

    Un test cuyo resultado depende de la hora a la que corre no informa nada:
    ni afirma que el contrato está bien ni que el dato está fresco. La frescura
    ya la cubre `test_mcp_macro_bias_weekend_staleness`, que la ejercita con
    fechas sintéticas y sin depender de qué día se corra la suite.

    Es el mismo criterio que el resto del archivo: los otros cinco tests montan
    su propio JSON en `tmp_path` y pasan `now_dt` explícito.
    """
    if not OUTPUT_FILE_DEFAULT.exists():
        pytest.skip("no hay snapshot del motor en este clon")
    as_of = json.loads(OUTPUT_FILE_DEFAULT.read_text(encoding="utf-8")).get("as_of_utc")
    if not as_of:
        pytest.skip("el snapshot no declara as_of_utc")
    # Una hora después de la emisión: dentro de cualquier umbral, y sigue siendo
    # un instante real relativo al dato en vez de un valor inventado.
    return datetime.fromisoformat(as_of.replace("Z", "+00:00")) + timedelta(hours=1)


def test_mcp_macro_bias_all_contract():
    """Valida que la consulta 'ALL' retorne exactamente el contrato Schema v2.0.0."""
    res = cargar_macro_bias("ALL", now_dt=_reloj_del_snapshot())
    assert "error" not in res, f"Retornó error inesperado: {res.get('error')}"
    assert res.get("schema_version") == "2.0.0"
    assert "config_hash" in res and len(res["config_hash"]) == 16
    assert "as_of_utc" in res
    assert "regimen_macro_global" in res
    assert "metricas_clave" in res
    assert "confianza_general" in res
    assert "activos" in res
    assert "USDCLP" in res["activos"]
    assert "XAUUSD" in res["activos"]


def test_mcp_macro_bias_single_symbol_contract():
    """Valida que la consulta por símbolo individual incluya trazabilidad completa."""
    res = cargar_macro_bias("USDCLP", now_dt=_reloj_del_snapshot())
    assert "error" not in res
    assert res.get("symbol") == "USDCLP"
    assert res.get("schema_version") == "2.0.0"
    assert "config_hash" in res
    assert "regimen_macro_global" in res
    assert "metricas_clave" in res
    assert "confianza_general" in res
    assert "activo" in res
    activo = res["activo"]
    assert activo.get("nombre") == "Dólar / Peso Chileno"
    assert "setups_permitidos" in activo
    assert "setups_prohibidos" in activo
    assert "parametros_riesgo" in activo
    assert activo["parametros_riesgo"]["distancia_sl_h1_puntos"] > 0


def test_mcp_macro_bias_invalid_ticker():
    """Valida el contrato de error unificado TICKER_NOT_IN_CATALOG."""
    res = cargar_macro_bias("EURUSD")
    assert res.get("error") == "TICKER_NOT_IN_CATALOG"
    assert "EURUSD" in res.get("message", "")


def test_mcp_macro_bias_zero_mutation(tmp_path):
    """Valida que la tool MCP sea estrictamente de solo lectura y no altere el archivo."""
    test_json = tmp_path / "test_macro_bias.json"
    dummy_data = {
        "schema_version": "2.0.0",
        "config_hash": "b571f800c4e05148",
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO", "nombre": "Calma"},
        "activos": {"USDCLP": {"nombre": "USDCLP", "parametros_riesgo": {"distancia_sl_h1_puntos": 2.83}}}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    mtime_before = test_json.stat().st_mtime_ns
    content_before = test_json.read_text(encoding="utf-8")

    # Múltiples lecturas
    for _ in range(5):
        res = cargar_macro_bias("USDCLP", output_file=test_json)
        assert "error" not in res

    mtime_after = test_json.stat().st_mtime_ns
    content_after = test_json.read_text(encoding="utf-8")

    assert mtime_before == mtime_after, "El archivo fue mutado durante la lectura MCP"
    assert content_before == content_after


def test_mcp_macro_bias_weekend_staleness(tmp_path):
    """Valida que un dato de 60h sea válido en fin de semana (80h) pero stale un miércoles (24h)."""
    test_json = tmp_path / "test_weekend.json"
    # Fecha de emisión: hace 60 horas
    fecha_emision = datetime(2026, 8, 14, 21, 0, 0, tzinfo=timezone.utc)  # Viernes 21:00 UTC
    dummy_data = {
        "schema_version": "2.0.0",
        "config_hash": "b571f800c4e05148",
        "as_of_utc": fecha_emision.isoformat(),
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO"},
        "activos": {"USDCLP": {"nombre": "USDCLP"}}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    # 1. Simular Domingo 09:00 UTC (hace 60h desde viernes) -> Domingo = weekday 6
    domingo_dt = datetime(2026, 8, 16, 9, 0, 0, tzinfo=timezone.utc)
    res_domingo = cargar_macro_bias("USDCLP", output_file=test_json, now_dt=domingo_dt)
    assert "error" not in res_domingo, "Falsamente marcado como stale en fin de semana"

    # 2. Simular Miércoles 09:00 UTC (hace 60h desde lunes) -> Miércoles = weekday 2
    miercoles_dt = datetime(2026, 8, 19, 9, 0, 0, tzinfo=timezone.utc)
    res_miercoles = cargar_macro_bias("USDCLP", output_file=test_json, now_dt=miercoles_dt)
    assert res_miercoles.get("error") == "STALE_DATA"
    assert res_miercoles.get("antiguedad_horas") > 24.0


def test_mcp_macro_bias_malformed_date(tmp_path):
    """Valida fail-closed ante fecha as_of_utc corrupta retornando READ_ERROR."""
    test_json = tmp_path / "test_corrupt.json"
    dummy_data = {
        "schema_version": "2.0.0",
        "as_of_utc": "INVALID_DATE_FORMAT_1234",
        "activos": {}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    res = cargar_macro_bias("USDCLP", output_file=test_json)
    assert res.get("error") == "READ_ERROR"
    assert "as_of_utc" in res.get("message", "")


def test_mcp_macro_bias_missing_file(tmp_path):
    """Valida que si el archivo no existe se retorne STALE_DATA sin auto-ejecutar subprocesos."""
    missing_file = tmp_path / "non_existent_file.json"
    res = cargar_macro_bias("USDCLP", output_file=missing_file)
    assert res.get("error") == "STALE_DATA"
    assert not missing_file.exists(), "No debe crear archivos en lecturas de solo lectura"
