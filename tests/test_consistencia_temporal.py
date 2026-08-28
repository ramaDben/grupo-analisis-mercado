# -*- coding: utf-8 -*-
"""
test_consistencia_temporal.py
Pruebas unitarias para el validador de consistencia temporal y anti-anacronismos.
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from validar_consistencia_temporal import (
    obtener_ahora_chile,
    validar_fecha_documento,
    auditar_anacronismos_texto,
    TemporalConsistencyError
)

SANTIAGO = ZoneInfo("America/Santiago")


def test_obtener_ahora_chile():
    ahora = obtener_ahora_chile()
    assert isinstance(ahora, datetime)
    assert ahora.tzinfo == SANTIAGO


def test_validar_fecha_documento_correcta():
    ahora = datetime(2026, 8, 27, 22, 0, tzinfo=SANTIAGO)
    assert validar_fecha_documento("2026-08-27", ahora=ahora) is True
    assert validar_fecha_documento("27 de agosto de 2026", ahora=ahora) is True
    assert validar_fecha_documento("27 de agosto", ahora=ahora) is True


def test_validar_fecha_documento_incorrecta():
    ahora = datetime(2026, 8, 27, 22, 0, tzinfo=SANTIAGO)
    with pytest.raises(TemporalConsistencyError, match="Error de Fecha"):
        validar_fecha_documento("2026-08-28", ahora=ahora)

    with pytest.raises(TemporalConsistencyError, match="Error de Fecha"):
        validar_fecha_documento("28 de agosto de 2026", ahora=ahora)


def test_auditar_anacronismos_detecta_pasado_sobre_futuro():
    texto_con_anacronismo = (
        "Tras la asimilación de los discursos del Simposio de Jackson Hole, "
        "el mercado nocturno reaccionó con cautela."
    )
    alertas = auditar_anacronismos_texto(texto_con_anacronismo)
    assert len(alertas) > 0
    assert any("Jackson Hole" in a for a in alertas)


def test_auditar_anacronismos_permite_modo_anticipacion():
    texto_anticipacion = (
        "Con Wall Street operando con cautela a la espera de los discursos clave del "
        "Simposio de Jackson Hole y los próximos datos de inflación en EE.UU., "
        "la atención del mercado nocturno se concentra en Asia."
    )
    alertas = auditar_anacronismos_texto(texto_anticipacion)
    assert len(alertas) == 0
