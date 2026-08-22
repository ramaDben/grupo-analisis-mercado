"""
tests/genesis_bridge/test_statistical_integrity.py
Pruebas unitarias de regresión contra fraude estadístico, padding artificial
y verificación obligatoria de revocación conforme a AUDITORIA_FORENSE_GENESIS_BRIDGE_FINAL.md.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from genesis.backtest.ledger import FillRecord, Ledger, RunProvenance
from genesis.strategy.contract import Direction
from genesis_bridge.certificate import GenesisCertificate, load_certificate, revoke_certificate
from genesis_bridge.errors import PromotionGateError
from genesis_bridge.validation_runner import (
    execute_validation_pipeline,
    is_full_git_sha,
    run_single_trial_validation,
)


def test_trade_count_is_never_padded_and_fails_if_under_minimum(monkeypatch, tmp_path):
    """Si el conteo de operaciones OOS es menor a 30, no debe haber padding y debe fallar el gate."""
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    prov = RunProvenance("S3", "v1", "hash_data", "hash_firm", "hash_risk")
    ledger = Ledger(provenance=prov)
    
    # 2 fills de entrada y 2 fills de salida (2 trades cerrados)
    ledger.append(FillRecord("S3", "XAUUSD", dt, 2000.0, Direction.LONG, False, 10.0, 9990.0))
    ledger.append(FillRecord("S3", "XAUUSD", dt, 2010.0, Direction.LONG, True, 10.0, 10010.0))
    ledger.append(FillRecord("S3", "XAUUSD", dt, 2010.0, Direction.LONG, False, 10.0, 10000.0))
    ledger.append(FillRecord("S3", "XAUUSD", dt, 2005.0, Direction.LONG, True, 10.0, 9995.0))

    monkeypatch.setattr("genesis.backtest.simulator.Simulator.run", lambda self, df: ledger)

    with pytest.raises(PromotionGateError) as exc_info:
        run_single_trial_validation(
            trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
            output_cert_dir=tmp_path / "certs",
            ledger_path=tmp_path / "ledger.jsonl",
        )

    assert "Insufficient OOS sample" in str(exc_info.value)


def test_pbo_is_not_hardcoded_and_blocks_promotion_if_missing(monkeypatch, tmp_path):
    """PBO no debe ser una constante; si no hay cálculo CSCV, el status debe ser VALIDATION_INCOMPLETE."""
    dt = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    prov = RunProvenance("S3", "v1", "hash_data", "hash_firm", "hash_risk")
    mock_ledger = Ledger(provenance=prov)
    for i in range(35):
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2000.0, Direction.LONG, False, 10.0, 10000.0 + i * 10))
        mock_ledger.append(FillRecord("S3", "XAUUSD", dt, 2015.0, Direction.LONG, True, 10.0, 10015.0 + i * 10))

    monkeypatch.setattr("genesis.backtest.simulator.Simulator.run", lambda self, df: mock_ledger)

    result = execute_validation_pipeline(
        trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
        output_cert_dir=tmp_path / "certs",
        ledger_path=tmp_path / "ledger.jsonl",
    )

    # PBO no es hardcodeado
    assert result.pbo is None
    # Bloquea la emisión de aprobación
    assert result.status == "VALIDATION_INCOMPLETE"
    assert result.operational_status == "BLOQUEADO"
    assert "PBO could not be calculated" in result.failure_reason


def test_full_git_sha_validation():
    """El validador de SHA debe requerir 40 caracteres hexadecimales."""
    assert is_full_git_sha("a" * 40) is True
    assert is_full_git_sha("0123456789abcdef0123456789abcdef01234567") is True
    assert is_full_git_sha("genesis-v1.4-verified") is False
    assert is_full_git_sha("abc1234") is False


def test_revocation_schema_distinction():
    """El certificado revocado debe separar claramente lifecycle_status, certificate_status y operational_status."""
    cert = GenesisCertificate(
        certificate_schema_version="1.0.0",
        certificate_id="TEST-CERT-01",
        trial_id="S3__XAUUSD__v1",
        status="GATE_ESTADISTICO_APROBADO",
        human_review="PENDING",
        operational_status="BLOQUEADO",
        genesis_repo="ramaDben/genesis",
        genesis_commit="genesis-v1.4",
        catalogue_version="1.3.0",
        catalogue_hash="abc",
        strategy_code_version="v1",
        data_snapshot_id="snap1",
        data_hash="data1",
        regime_snapshot_id="reg1",
        config_hash="cfg1",
        n_trials_total=5400,
        metrics={"trades_oos": 45, "dsr": 0.96},
        gate={"trades_oos_min": 30},
        issued_at_utc="2026-08-21T00:00:00Z",
        signature_hash="sig1",
    )

    revoked = revoke_certificate(cert, reason="INVALID_METRICS_AND_INSUFFICIENT_SAMPLE")

    assert revoked.status == "REVOKED"
    assert revoked.lifecycle_status == "CANDIDATO"
    assert revoked.certificate_status == "REVOKED"
    assert revoked.operational_status == "BLOQUEADO"
    assert revoked.revocation_reason == "INVALID_METRICS_AND_INSUFFICIENT_SAMPLE"
    assert revoked.revoked_at_utc is not None
