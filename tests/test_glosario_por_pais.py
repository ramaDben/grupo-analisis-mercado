"""Una decisión de tasas se explica con su banco central, no con el primero que calce por nombre.

El 2026-10-27 el correo de Goldman Sachs explicó la decisión del BCE con la de la TPM chilena:
la entrada de la TPM trae el alias genérico «Interest Rate Decision» y el enganche no miraba el país.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_data_mcp.tools.calendar import _cargar_glosario, _enganchar_glosario  # noqa: E402

GLOSARIO = _cargar_glosario()


@pytest.mark.parametrize("nombre,pais", [
    ("ECB Interest Rate Decision (Oct)", "Euro Zone"),
    ("Deposit Facility Rate (Oct)", "Euro Zone"),
    ("BoC Interest Rate Decision", "Canada"),
    ("Interest Rate Decision", "Euro Zone"),
])
def test_una_decision_ajena_no_se_explica_con_la_tpm_chilena(nombre, pais):
    entrada = _enganchar_glosario(nombre, GLOSARIO, pais)
    assert entrada is None or "Banco Central de Chile" not in entrada["explicacion"], nombre


def test_la_decision_del_bce_tiene_su_explicacion():
    for nombre in ("ECB Interest Rate Decision (Oct)", "Deposit Facility Rate (Oct)"):
        entrada = _enganchar_glosario(nombre, GLOSARIO, "Euro Zone")
        assert entrada is not None and "BCE" in entrada["nombre_es"] and "euro" in entrada["explicacion"]


def test_la_tpm_chilena_sigue_enganchando_en_chile():
    for nombre in ("Interest Rate Decision", "Chile Interest Rate Decision"):
        entrada = _enganchar_glosario(nombre, GLOSARIO, "Chile")
        assert entrada["nombre_es"] == "Tasa de Política Monetaria"


def test_sin_pais_el_enganche_queda_como_antes():
    assert _enganchar_glosario("Fed Interest Rate Decision", GLOSARIO) is not None


@pytest.mark.parametrize("nombre", ["ECB Press Conference", "ECB Monetary Policy Statement"])
def test_la_conferencia_y_el_comunicado_del_bce_salen_en_espanol(nombre):
    assert "BCE" in _enganchar_glosario(nombre, GLOSARIO, "Euro Zone")["nombre_es"]
