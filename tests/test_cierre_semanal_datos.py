"""Cifras de la tabla de curva del cierre semanal.

El cierre semanal es un documento de cliente: toda sigla va explicada (issue #46),
y en una celda de tabla no cabe la explicación, así que la unidad va en palabras,
con el mismo término que ya usa la prosa del documento ("puntos base").
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import cierre_semanal_datos as csd  # noqa: E402


def test_la_variacion_va_en_puntos_base_y_sin_la_sigla():
    assert csd._bps(13.0) == "+13 puntos base"
    assert csd._bps(-4.0) == "-4 puntos base"


def test_un_delta_incalculable_se_dice_y_no_se_publica_como_cero():
    assert csd._bps(None) == "no disponible"
