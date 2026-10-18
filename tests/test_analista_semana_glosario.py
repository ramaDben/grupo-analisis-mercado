"""Contrato del glosario con el tema de la semana: lo que el tema puede elegir viene clasificado.

El mapa de la semana nombra los activos que mueve un dato solo con lo que el glosario declara
(`tier`, `canales`, `si_sale_sobre_consenso`). Un evento sin esos tres campos no puede ser tema.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_data_mcp.tools.calendar import _cargar_glosario, _enganchar_glosario  # noqa: E402

# Nombres como los entrega Investing.com para los datos que el tema puede elegir.
EVENTOS_DEL_TEMA = [
    "Fed Interest Rate Decision", "FOMC Statement", "Chile Interest Rate Decision",
    "CPI (MoM) (Sep)", "Core PCE Price Index (MoM)", "Nonfarm Payrolls (Sep)",
    "ISM Manufacturing PMI (Sep)", "GDP (QoQ) (Q3)", "Imacec (YoY) (Aug)", "Crude Oil Inventories",
]
# Sin efecto auditado en el glosario: quedan fuera del tema y la guía no los menciona.
FUERA_DEL_TEMA = ["OPEP", "BCCh", "BCE", "IPC subyacente", "PCE subyacente"]


@pytest.mark.parametrize("nombre", EVENTOS_DEL_TEMA)
def test_cada_evento_del_tema_viene_clasificado(nombre):
    entrada = _enganchar_glosario(nombre, _cargar_glosario())
    assert entrada is not None, f"{nombre} no engancha con el glosario"
    for campo in ("tier", "canales", "si_sale_sobre_consenso"):
        assert entrada.get(campo), f"{nombre}: falta {campo}"


@pytest.mark.parametrize("sigla", FUERA_DEL_TEMA)
def test_lo_que_sigue_sin_clasificar_no_inventa_efecto(sigla):
    # Si alguien le agrega efecto a una de estas, debe moverla al tema con su test.
    assert "si_sale_sobre_consenso" not in _cargar_glosario()[sigla]
