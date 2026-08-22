from datetime import datetime, timezone
from pathlib import Path
import pytest

from genesis.backtest.ledger import FillRecord, Ledger, RunProvenance
from genesis.strategy.contract import Direction
from genesis_bridge.catalog_schema import (
    HumanReviewStatus,
    OperationalStatus,
    PromotionState,
)
from genesis_bridge.certificate import promote_to_validated_genesis, verify_certificate
from genesis_bridge.errors import PromotionGateError
from genesis_bridge.validation_runner import run_single_trial_validation


def test_end_to_end_s3_gold_pilot_insufficient_sample_fails_gate(tmp_path: Path):
    """La ejecución real con trades < 30 en OOS debe fallar el gate y registrarlo en el ledger."""
    cert_dir = tmp_path / "certificates"
    ledger_path = tmp_path / "ledger" / "trial_ledger.jsonl"

    with pytest.raises(PromotionGateError) as exc_info:
        run_single_trial_validation(
            trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
            output_cert_dir=cert_dir,
            ledger_path=ledger_path,
            genesis_commit="0123456789abcdef0123456789abcdef01234567",
        )

    assert "Insufficient OOS sample" in str(exc_info.value)
    assert ledger_path.exists()
    content = ledger_path.read_text(encoding="utf-8")
    assert '"success": false' in content
    assert "Insufficient OOS sample" in content


def test_end_to_end_s3_gold_pilot_missing_pbo_yields_validation_incomplete(monkeypatch, tmp_path: Path):
    """Si trades_oos >= 30 pero no se calculó PBO vía CSCV, el veredicto debe ser VALIDATION_INCOMPLETE."""
    cert_dir = tmp_path / "certificates"
    ledger_path = tmp_path / "ledger" / "trial_ledger.jsonl"

    # 35 trades simulados
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    prov = RunProvenance("S3", "v1", "hash_data", "hash_firm", "hash_risk")
    mock_ledger = Ledger(provenance=prov)
    for i in range(35):
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2000.0, Direction.LONG, False, 10.0, 10000.0 + i * 10))
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2015.0, Direction.LONG, True, 10.0, 10015.0 + i * 10))

    monkeypatch.setattr("genesis.backtest.simulator.Simulator.run", lambda self, df: mock_ledger)

    from genesis_bridge.validation_runner import execute_validation_pipeline
    res = execute_validation_pipeline(
        trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
        output_cert_dir=cert_dir,
        ledger_path=ledger_path,
        genesis_commit="0123456789abcdef0123456789abcdef01234567",
    )

    assert res.status == "VALIDATION_INCOMPLETE"
    assert res.operational_status == "BLOQUEADO"
    assert res.pbo is None
    assert "PBO could not be calculated" in res.failure_reason


def test_end_to_end_s3_gold_pilot_full_pass_with_pbo(monkeypatch, tmp_path: Path):
    """Cuando trades_oos >= 30, DSR >= 0 y PBO está calculado por CSCV, emite certificado y permite Hito 2."""
    cert_dir = tmp_path / "certificates"
    ledger_path = tmp_path / "ledger" / "trial_ledger.jsonl"

    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    prov = RunProvenance("S3", "v1", "hash_data", "hash_firm", "hash_risk")
    mock_ledger = Ledger(provenance=prov)
    for i in range(35):
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2000.0, Direction.LONG, False, 10.0, 10000.0 + i * 10))
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2015.0, Direction.LONG, True, 10.0, 10015.0 + i * 10))

    monkeypatch.setattr("genesis.backtest.simulator.Simulator.run", lambda self, df: mock_ledger)

    # Inyectar cálculo CSCV de PBO simulado
    from genesis_bridge.certificate import issue_statistical_gate_certificate

    cert = issue_statistical_gate_certificate(
        trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
        genesis_commit="0123456789abcdef0123456789abcdef01234567",
        catalogue_hash="deadbeef" * 8,
        strategy_code_version="s3_v1",
        data_snapshot_id="SNAP-001",
        data_hash="cafe" * 16,
        regime_snapshot_id="REG-001",
        config_hash="12345678",
        n_trials_total=5400,
        metrics={
            "dsr": 0.85,
            "pbo": 0.08,
            "sharpe_is": 1.5,
            "sharpe_oos": 1.2,
            "max_drawdown_oos": 0.04,
            "trades_oos": 35,
            "profit_factor": 1.6,
        },
    )

    assert cert.status == PromotionState.GATE_ESTADISTICO_APROBADO.value
    assert cert.operational_status == OperationalStatus.BLOQUEADO.value

    # Promoción controlada a Hito 2
    cert_stage2 = promote_to_validated_genesis(cert, reviewer_notes="Auditoría humana completada")
    assert cert_stage2.status == PromotionState.VALIDADO_GENESIS.value
    assert cert_stage2.operational_status == OperationalStatus.PAPER_ONLY.value
    assert verify_certificate(cert_stage2)[0] is True
