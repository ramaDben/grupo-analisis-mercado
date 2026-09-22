# -*- coding: utf-8 -*-
"""Pruebas unitarias para el orquestador maestro jornada_matutina.py."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from scripts.jornada_matutina import (
    resolver_ultima_tanda,
    auditar_editorial,
    despachar_oficial,
)


def test_resolver_ultima_tanda_directorio_inexistente():
    with pytest.raises(FileNotFoundError):
        resolver_ultima_tanda("directorio_imposible_xyz_123")


def test_resolver_ultima_tanda_encuentra_directorio_existente(tmp_path):
    tanda_fake = tmp_path / "2026-09-22_08-00_matutina"
    tanda_fake.mkdir()
    res = resolver_ultima_tanda(tanda_fake)
    assert res == tanda_fake


def test_auditar_editorial_detecta_voseo_y_guion_largo(tmp_path):
    p_err = tmp_path / "1_test_activo.json"
    p_err.write_text(
        json.dumps({
            "titular": "Activo sube — rompe resistencia",
            "parrafo": "Mirá el gráfico y sumate al grupo de trading.",
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    resultado = auditar_editorial(tmp_path)
    assert resultado is False


def test_auditar_editorial_valida_payload_conforme(tmp_path):
    p_ok = tmp_path / "1_test_valido.json"
    p_ok.write_text(
        json.dumps({
            "titular": "WTI Consolida en Soporte Clave",
            "parrafo": "El crudo mantiene la zona de demanda tras los datos de inventarios.",
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    resultado = auditar_editorial(tmp_path)
    assert resultado is True


def test_despachar_oficial_se_niega_sin_confirmacion(tmp_path):
    # Sin el flag confirmado=True, debe retornar False inmediatamente para proteger la producción
    resultado = despachar_oficial(tmp_path, confirmado=False)
    assert resultado is False
