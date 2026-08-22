"""
tests/genesis_bridge/test_search_plan.py
Tests unitarios del plan de búsqueda exhaustiva y registro append-only de trials.
"""

from pathlib import Path
import pytest

from genesis_bridge.hypothesis_loader import load_hypothesis
from genesis_bridge.search_plan import AppendOnlyTrialLedger, build_search_plan


def test_build_search_plan_cardinality(tmp_path: Path):
    """El plan de búsqueda debe calcular exactamente N_trials_total = producto(cardinalidades)."""
    spec, _ = load_hypothesis("S3_BREAKOUT_DONCHIAN_H1")
    search_plan = build_search_plan(spec, "XAUUSD")

    expected_product = 1
    for card in search_plan.param_grid_cardinalities.values():
        expected_product *= card

    assert search_plan.n_trials_total == expected_product
    assert len(search_plan.trials) == expected_product
    assert search_plan.search_plan_hash != ""


def test_append_only_trial_ledger(tmp_path: Path):
    """El ledger debe persistir cada corrida en modo append-only sin sobreescribir."""
    ledger_file = tmp_path / "trial_ledger.jsonl"
    ledger = AppendOnlyTrialLedger(ledger_file)

    ledger.record_trial("TRIAL_1", 0, {"lookback": 50}, True, {"dsr": 0.95})
    ledger.record_trial("TRIAL_2", 1, {"lookback": 60}, False, {"dsr": -0.5}, failure_reason="Min trades")

    lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert "TRIAL_1" in lines[0]
    assert "TRIAL_2" in lines[1]
