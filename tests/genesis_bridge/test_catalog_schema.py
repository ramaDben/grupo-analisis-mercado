"""
tests/genesis_bridge/test_catalog_schema.py
Tests unitarios de validación del esquema del catálogo v1.3 y consistencia SSOT (fail-closed).
"""

import pytest
from genesis_bridge.catalog_schema import (
    HypothesisProvenance,
    HypothesisSpec,
    PromotionState,
    SearchSpaceParam,
    validate_hypothesis_against_matrix,
)
from genesis_bridge.errors import CatalogValidationError
from genesis_bridge.hypothesis_loader import load_catalogue, load_hypothesis


def test_catalog_loader_and_sha256():
    """El cargador del catálogo debe leer todas las hipótesis y calcular el hash SHA-256."""
    hypotheses, matrix, cat_hash = load_catalogue()
    assert len(hypotheses) >= 8, f"Se esperaban al menos 8 hipótesis, se obtuvieron {len(hypotheses)}"
    assert len(cat_hash) == 64, "El hash SHA-256 del catálogo debe tener 64 caracteres hexadecimales"
    assert "BREAKOUT_DONCHIAN_H1" in hypotheses or "S3_BREAKOUT_DONCHIAN_H1" in hypotheses
    assert "R0_CALMA_RANGO" in matrix


def test_hypothesis_ssot_validation_fail_closed():
    """Si una ficha declara direcciones en un régimen donde la matriz declara PROHIBIDA, debe fallar cerrado."""
    bad_spec = HypothesisSpec(
        id_setup="TEST_BAD_SETUP",
        familia="MOMENTUM",
        regimen_macro_optimo=("R0_CALMA_RANGO",),
        estado_validacion=PromotionState.CANDIDATO.value,
        strategy_code_version="v1",
        data_schema_version="v1",
        regime_schema_version="v1",
        procedencia=HypothesisProvenance(
            tipo="ORIGINAL",
            derivada_de=(),
            transformaciones=(),
            mecanismo_preservado="Test",
        ),
        trial_ids=("TEST_TRIAL_1",),
        direcciones_por_regimen={
            "R2_ESTRES_LIQUIDEZ": {"USDCLP": ("LONG",)}
        },
        espacio_de_busqueda_parametros={
            "p1": SearchSpaceParam(valor_base=1.0, rango_permitido=(1.0, 2.0), paso_grilla=1.0)
        },
        constantes_congeladas={},
    )

    dummy_matrix = {
        "R2_ESTRES_LIQUIDEZ": {
            "TEST_BAD_SETUP": {
                "estado": "PROHIBIDA",
                "direcciones": {}
            }
        }
    }

    with pytest.raises(CatalogValidationError):
        validate_hypothesis_against_matrix(bad_spec, dummy_matrix)


def test_search_space_grid_generation():
    """Verifica que el espacio de búsqueda genere los valores discretos esperados."""
    param = SearchSpaceParam(valor_base=1.0, rango_permitido=(1.0, 1.5), paso_grilla=0.1)
    vals = param.grid_values()
    assert len(vals) == 6
    assert vals[0] == 1.0
    assert vals[-1] == 1.5


def test_package_init_exports():
    """Verifica que genesis_bridge exporte todas las clases y funciones públicas sin errores de sintaxis."""
    import genesis_bridge

    expected_exports = [
        "CatalogValidationError",
        "GenesisBridgeError",
        "GenesisCertificate",
        "HumanReviewStatus",
        "HypothesisProvenance",
        "HypothesisSpec",
        "OperationalStatus",
        "PromotionGateError",
        "PromotionState",
        "RegimeLeakageError",
        "SearchSpaceParam",
        "TerminalState",
        "UncertifiedStrategyError",
        "issue_statistical_gate_certificate",
        "promote_to_live_limited",
        "promote_to_validated_genesis",
        "verify_certificate",
    ]

    for export_name in expected_exports:
        assert hasattr(genesis_bridge, export_name), f"genesis_bridge debe exportar {export_name}"
    assert genesis_bridge.__all__ == expected_exports
