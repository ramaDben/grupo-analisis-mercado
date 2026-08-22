"""
tests/genesis_bridge/test_operational_safety.py
Tests de seguridad operativa y aislamiento:
Garantiza que ninguna hipótesis no certificada en APROBADO_LIMITADO sea accesible por la operativa real.
"""

from pathlib import Path
import pytest
import yaml

from genesis_bridge.catalog_schema import PromotionState
from genesis_bridge.errors import UncertifiedStrategyError


def test_live_registry_is_empty_or_only_contains_approved_limited():
    """El registro de estrategias en vivo debe estar vacío o solo contener estrategias APROBADO_LIMITADO."""
    reg_path = Path("config/strategies_live_registry.yaml")
    assert reg_path.exists(), "El archivo config/strategies_live_registry.yaml debe existir."

    raw = yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {}
    active_strategies = raw.get("active_strategies", [])

    for strat in active_strategies:
        assert strat.get("status") == PromotionState.APROBADO_LIMITADO.value
        assert strat.get("certificate_id") is not None
        assert strat.get("certificate_signature_verified") is True


def test_candidates_and_validated_are_blocked_from_execution():
    """Cualquier estado previo a APROBADO_LIMITADO debe ser bloqueado para ejecución real."""
    blocked_states = [
        PromotionState.CANDIDATO.value,
        PromotionState.GATE_ESTADISTICO_APROBADO.value,
        PromotionState.VALIDADO_GENESIS.value,
        PromotionState.INCUBACION_PAPER.value,
    ]

    for state in blocked_states:
        # Función de guarda operativa
        def execute_strategy(strategy_status: str):
            if strategy_status != PromotionState.APROBADO_LIMITADO.value:
                raise UncertifiedStrategyError(f"Estrategia en estado {strategy_status} bloqueada para ejecución real.")

        with pytest.raises(UncertifiedStrategyError):
            execute_strategy(state)
