"""
tests/genesis_bridge/test_certificate.py
Tests unitarios para la emisión, validación de gates y evolución en 3 etapas del Certificado Inmutable.
"""

from pathlib import Path
import pytest

from genesis_bridge.catalog_schema import (
    HumanReviewStatus,
    OperationalStatus,
    PromotionState,
)
from genesis_bridge.certificate import (
    issue_statistical_gate_certificate,
    promote_to_live_limited,
    promote_to_validated_genesis,
    verify_certificate,
)
from genesis_bridge.errors import PromotionGateError


def test_certificate_issuance_and_signature():
    """Hito 1: Emisión tras superar gates estadísticos con status GATE_ESTADISTICO_APROBADO y operational_status BLOQUEADO."""
    metrics = {
        "dsr": 0.95,
        "pbo": 0.15,
        "sharpe_is": 1.4,
        "sharpe_oos": 1.2,
        "max_drawdown_oos": 0.08,
        "trades_oos": 50,
    }

    cert = issue_statistical_gate_certificate(
        trial_id="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1",
        genesis_commit="abc12345",
        catalogue_hash="deadbeef" * 8,
        strategy_code_version="s3_v1",
        data_snapshot_id="SNAP-001",
        data_hash="cafe" * 16,
        regime_snapshot_id="REG-001",
        config_hash="12345678",
        n_trials_total=400,
        metrics=metrics,
    )

    assert cert.status == PromotionState.GATE_ESTADISTICO_APROBADO.value
    assert cert.human_review == HumanReviewStatus.PENDING.value
    assert cert.operational_status == OperationalStatus.BLOQUEADO.value

    # Verificación de firma criptográfica
    valid, msg = verify_certificate(cert)
    assert valid is True, f"Certificado debe ser válido: {msg}"


def test_certificate_gate_failure():
    """Si los trades OOS o el DSR no alcanzan el gate, debe rechazar la emisión con PromotionGateError."""
    bad_metrics = {
        "dsr": -0.2,
        "pbo": 0.45,
        "trades_oos": 10,  # Min 30
    }

    with pytest.raises(PromotionGateError):
        issue_statistical_gate_certificate(
            trial_id="S3_FAIL",
            genesis_commit="abc",
            catalogue_hash="hash",
            strategy_code_version="v1",
            data_snapshot_id="snap",
            data_hash="hash",
            regime_snapshot_id="reg",
            config_hash="conf",
            n_trials_total=10,
            metrics=bad_metrics,
        )


def test_certificate_three_stage_evolution():
    """Evolución: GATE_ESTADISTICO_APROBADO -> VALIDADO_GENESIS -> APROBADO_LIMITADO."""
    metrics = {"dsr": 0.98, "pbo": 0.10, "trades_oos": 60}
    cert1 = issue_statistical_gate_certificate(
        trial_id="S3_EVOL",
        genesis_commit="abc",
        catalogue_hash="hash",
        strategy_code_version="v1",
        data_snapshot_id="snap",
        data_hash="hash",
        regime_snapshot_id="reg",
        config_hash="conf",
        n_trials_total=10,
        metrics=metrics,
    )

    # Hito 2: Post-Auditoría Humana
    cert2 = promote_to_validated_genesis(cert1, reviewer_notes="Auditoría OK")
    assert cert2.status == PromotionState.VALIDADO_GENESIS.value
    assert cert2.human_review == HumanReviewStatus.APPROVED.value
    assert cert2.operational_status == OperationalStatus.PAPER_ONLY.value

    # Hito 3: Post-Incubación
    cert3 = promote_to_live_limited(cert2, live_approval_notes="Incubación paper 30d superada")
    assert cert3.status == PromotionState.APROBADO_LIMITADO.value
    assert cert3.operational_status == OperationalStatus.LIVE_LIMITED.value

    # Las 3 etapas deben ser verificables criptográficamente
    assert verify_certificate(cert1)[0] is True
    assert verify_certificate(cert2)[0] is True
    assert verify_certificate(cert3)[0] is True
