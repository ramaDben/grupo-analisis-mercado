"""Contrato entre la ingesta y el motor: las claves tienen que coincidir.

El motor leía `chile_series.get("TPM_CHILE")` y la ingesta escribe la serie como
`TPM`. Resultado: 665 observaciones de la Tasa de Política Monetaria en disco,
sin usar, y el motor emitiendo `spread_tasas_chile_fed_pct: null` con la
justificación "Diferencial de tasas N/A". Ese spread es el vector 2 de 3 de la
ficha USD/CLP del Playbook (carry, Carreño & Cox BCCh DT 722).

El mismo error inutilizaba el driver en el índice de confianza: TPM_CHILE contaba
como MISSING, dejando frescura y cobertura en 5/6 = 83,3 % y la confianza total en
54,6 % en vez de 65,4 %.

No es un caso aislado: es el patrón del issue de los filtros de calendario
escritos en español contra una fuente en inglés. Un `.get()` con la clave
equivocada devuelve `None` y nadie se entera. Este test compara las claves que el
motor pide contra las que existen de verdad en los archivos crudos.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

DATA_CENTRAL = RAIZ / "data central"
MOTOR = RAIZ / "scripts" / "macro_bias_engine.py"

# (variable en el motor, archivo crudo, ruta al dict de series dentro del archivo)
FUENTES = (
    ("chile_series", DATA_CENTRAL / "DATA CHILE" / "raw" / "bcch_macro_data.json", ("series",)),
    ("yields", DATA_CENTRAL / "DATA USA" / "raw" / "treasury_fed_data.json", ("curva_rendimientos_yields",)),
    ("comm_series", DATA_CENTRAL / "DATA ORO Y COMMODITIES" / "raw" / "commodities_data.json", ("commodities",)),
)


def _claves_pedidas(variable: str) -> set[str]:
    """Las claves que el motor pide de ese dict, leídas de su código fuente."""
    fuente = MOTOR.read_text(encoding="utf-8")
    return set(re.findall(rf'{variable}\.get\(\s*"([^"]+)"', fuente))


def _claves_disponibles(archivo: Path, ruta: tuple[str, ...]) -> set[str]:
    data = json.loads(archivo.read_text(encoding="utf-8"))
    for tramo in ruta:
        data = data.get(tramo) or {}
    return set(data)


@pytest.mark.parametrize("variable, archivo, ruta", FUENTES)
def test_las_claves_que_pide_el_motor_existen_en_el_archivo_crudo(variable, archivo, ruta):
    if not archivo.exists():
        pytest.skip(f"{archivo.name} no está en el clon")

    pedidas = _claves_pedidas(variable)
    assert pedidas, f"no se leyó ninguna clave de {variable}: el patrón quedó obsoleto"

    disponibles = _claves_disponibles(archivo, ruta)
    huerfanas = sorted(pedidas - disponibles)
    assert not huerfanas, (
        f"el motor pide de {variable} claves que {archivo.name} no tiene: {huerfanas}. "
        f"Disponibles: {sorted(disponibles)}. Un `.get()` con la clave equivocada "
        "devuelve None y el driver queda inutilizado en silencio."
    )


def test_el_spread_de_tasas_chile_fed_se_puede_calcular():
    """El vector de carry de la ficha USD/CLP no puede venir null si el dato está.

    TPM y DFF están ambos en disco: si el spread sale None, es un problema de
    lectura y no de datos faltantes.
    """
    from macro_bias_engine import _obtener_serie_cronologica

    ch = json.loads((DATA_CENTRAL / "DATA CHILE" / "raw" / "bcch_macro_data.json").read_text(encoding="utf-8"))
    us = json.loads((DATA_CENTRAL / "DATA USA" / "raw" / "treasury_fed_data.json").read_text(encoding="utf-8"))

    fuente = MOTOR.read_text(encoding="utf-8")
    clave_tpm = re.search(r'chile_series\.get\("(TPM[^"]*)"', fuente)
    assert clave_tpm, "no se encontró la lectura de la TPM en el motor"

    tpm = _obtener_serie_cronologica((ch.get("series", {}).get(clave_tpm.group(1)) or {}).get("historico", {}))
    dff = _obtener_serie_cronologica(
        (us.get("curva_rendimientos_yields", {}).get("DFF") or {}).get("historico", {})
    )

    assert tpm, f'la clave "{clave_tpm.group(1)}" no devuelve serie de TPM'
    assert dff, "DFF (tasa de fondos federales) no devuelve serie"
    spread = tpm[-1][1] - dff[-1][1]
    assert -10.0 < spread < 10.0, f"spread fuera de rango razonable: {spread}"
