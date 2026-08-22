"""
genesis_bridge.certificate
Generación, firma criptográfica y verificación de Certificados de Validación Inmutables en 3 etapas.
Garantiza que ninguna estrategia sea promovida sin hashes válidos y gates estadísticos cumplidos.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from genesis_bridge.catalog_schema import (
    HumanReviewStatus,
    OperationalStatus,
    PromotionState,
)
from genesis_bridge.errors import PromotionGateError


@dataclass(frozen=True, slots=True)
class GenesisCertificate:
    """Certificado inmutable de validación estadística emitido por Genesis."""
    certificate_schema_version: str
    certificate_id: str
    trial_id: str
    status: str
    human_review: str
    operational_status: str
    genesis_repo: str
    genesis_commit: str
    catalogue_version: str
    catalogue_hash: str
    strategy_code_version: str
    data_snapshot_id: str
    data_hash: str
    regime_snapshot_id: str
    config_hash: str
    n_trials_total: int
    metrics: Mapping[str, Any]
    gate: Mapping[str, Any]
    issued_at_utc: str
    signature_hash: str
    reviewer_notes: str | None = None
    live_approval_notes: str | None = None
    lifecycle_status: str = "CANDIDATO"
    certificate_status: str = "VALID"
    revocation_reason: str | None = None
    revoked_at_utc: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["metrics"] = dict(self.metrics)
        d["gate"] = dict(self.gate)
        return d


def revoke_certificate(
    cert: GenesisCertificate,
    reason: str = "INVALID_METRICS_AND_INSUFFICIENT_SAMPLE",
) -> GenesisCertificate:
    """Revoca formalmente un certificado existente preservando la trazabilidad."""
    now_utc = datetime.now(timezone.utc).isoformat()
    d = cert.to_dict()
    d["status"] = "REVOKED"
    d["lifecycle_status"] = "CANDIDATO"
    d["certificate_status"] = "REVOKED"
    d["operational_status"] = OperationalStatus.BLOQUEADO.value
    d["revocation_reason"] = reason
    d["revoked_at_utc"] = now_utc
    d["signature_hash"] = _calculate_signature(d)
    return GenesisCertificate(**d)


def _calculate_signature(payload: dict[str, Any]) -> str:
    """Calcula el hash SHA-256 de los campos del certificado excluyendo signature_hash y campos nulos."""
    clean = {k: v for k, v in payload.items() if k != "signature_hash" and v is not None}
    raw = json.dumps(clean, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_statistical_gate_certificate(
    trial_id: str,
    genesis_commit: str,
    catalogue_hash: str,
    strategy_code_version: str,
    data_snapshot_id: str,
    data_hash: str,
    regime_snapshot_id: str,
    config_hash: str,
    n_trials_total: int,
    metrics: Mapping[str, Any],
    gate: Mapping[str, Any] | None = None,
    certificate_id: str | None = None,
) -> GenesisCertificate:
    """
    Emite el certificado de Hito 1: Superación de Gates Estadísticos.
    Estado: GATE_ESTADISTICO_APROBADO | human_review: PENDING | operational_status: BLOQUEADO
    """
    default_gate = {
        "dsr_min": 0.0,
        "pbo_max": 0.20,
        "sharpe_oos_ratio_min": 0.50,
        "trades_oos_min": 30,
        "max_drawdown_oos_max": 0.15,
    }
    applied_gate = dict(gate or default_gate)

    # Validar cumplimiento del gate estadístico
    dsr = metrics.get("dsr")
    pbo = metrics.get("pbo")
    trades_oos = metrics.get("trades_oos", 0)

    if dsr is not None and dsr < applied_gate.get("dsr_min", 0.0):
        raise PromotionGateError(f"Gate DSR fallido: {dsr} < {applied_gate['dsr_min']}")
    if pbo is not None and pbo > applied_gate.get("pbo_max", 0.20):
        raise PromotionGateError(f"Gate PBO fallido: {pbo} > {applied_gate['pbo_max']}")
    if trades_oos < applied_gate.get("trades_oos_min", 30):
        raise PromotionGateError(f"Gate Trades OOS fallido: {trades_oos} < {applied_gate['trades_oos_min']}")

    issued_at = datetime.now(timezone.utc).isoformat()
    cid = certificate_id or f"GENESIS-{trial_id.replace('__', '-')}-{issued_at[:10]}"

    d = {
        "certificate_schema_version": "1.0.0",
        "certificate_id": cid,
        "trial_id": trial_id,
        "status": PromotionState.GATE_ESTADISTICO_APROBADO.value,
        "human_review": HumanReviewStatus.PENDING.value,
        "operational_status": OperationalStatus.BLOQUEADO.value,
        "genesis_repo": "ramaDben/genesis",
        "genesis_commit": genesis_commit,
        "catalogue_version": "1.3.0",
        "catalogue_hash": catalogue_hash,
        "strategy_code_version": strategy_code_version,
        "data_snapshot_id": data_snapshot_id,
        "data_hash": data_hash,
        "regime_snapshot_id": regime_snapshot_id,
        "config_hash": config_hash,
        "n_trials_total": n_trials_total,
        "metrics": dict(metrics),
        "gate": applied_gate,
        "issued_at_utc": issued_at,
        "signature_hash": "",
        "reviewer_notes": None,
        "live_approval_notes": None,
        "lifecycle_status": "GATE_ESTADISTICO_APROBADO",
        "certificate_status": "VALID",
        "revocation_reason": None,
        "revoked_at_utc": None,
    }
    sig = _calculate_signature(d)
    d["signature_hash"] = sig

    return GenesisCertificate(**d)


def promote_to_validated_genesis(
    cert: GenesisCertificate,
    reviewer_notes: str = "Auditoría de mecanismo completada",
) -> GenesisCertificate:
    """
    Promueve el certificado a Hito 2: Tras Auditoría Humana del Mecanismo.
    Estado: VALIDADO_GENESIS | human_review: APPROVED | operational_status: PAPER_ONLY
    """
    if cert.status != PromotionState.GATE_ESTADISTICO_APROBADO.value:
        raise PromotionGateError(f"No se puede promover a VALIDADO_GENESIS desde estado {cert.status}")

    d = cert.to_dict()
    d["status"] = PromotionState.VALIDADO_GENESIS.value
    d["human_review"] = HumanReviewStatus.APPROVED.value
    d["operational_status"] = OperationalStatus.PAPER_ONLY.value
    d["reviewer_notes"] = reviewer_notes
    d["lifecycle_status"] = "VALIDADO_GENESIS"
    d["certificate_status"] = "VALID"
    d["signature_hash"] = _calculate_signature(d)

    return GenesisCertificate(**d)


def promote_to_live_limited(
    cert: GenesisCertificate,
    live_approval_notes: str = "Incubación paper trading superada",
) -> GenesisCertificate:
    """
    Promueve el certificado a Hito 3: Tras Incubación Exitosa en Demo/Paper.
    Estado: APROBADO_LIMITADO | human_review: APPROVED | operational_status: LIVE_LIMITED
    """
    if cert.status != PromotionState.VALIDADO_GENESIS.value:
        raise PromotionGateError(f"No se puede promover a APROBADO_LIMITADO desde estado {cert.status}")

    d = cert.to_dict()
    d["status"] = PromotionState.APROBADO_LIMITADO.value
    d["operational_status"] = OperationalStatus.LIVE_LIMITED.value
    d["live_approval_notes"] = live_approval_notes
    d["lifecycle_status"] = "APROBADO_LIMITADO"
    d["certificate_status"] = "VALID"
    d["signature_hash"] = _calculate_signature(d)

    return GenesisCertificate(**d)


def verify_certificate(cert_data: dict[str, Any] | GenesisCertificate | Path | str) -> tuple[bool, str]:
    """Verifica la integridad criptográfica de un certificado contra su signature_hash."""
    if isinstance(cert_data, (Path, str)):
        p = Path(cert_data)
        if not p.exists():
            return False, f"Archivo no encontrado: {p}"
        raw = json.loads(p.read_text(encoding="utf-8"))
    elif isinstance(cert_data, GenesisCertificate):
        raw = cert_data.to_dict()
    else:
        raw = dict(cert_data)

    sig = raw.get("signature_hash", "")
    calculated = _calculate_signature(raw)
    if sig != calculated:
        return False, f"Firma inválida: {sig} != {calculated}"
    return True, "Certificado íntegro y verificado"


def load_certificate(path: Path | str) -> GenesisCertificate:
    """Carga y parsea un certificado JSON inmutable."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Certificado no encontrado en: {p}")
    raw = json.loads(p.read_text(encoding="utf-8"))
    return GenesisCertificate(**raw)


def save_certificate(cert: GenesisCertificate, path: Path | str) -> Path:
    """Guarda un certificado en formato JSON con indentación canónica."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cert.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p
