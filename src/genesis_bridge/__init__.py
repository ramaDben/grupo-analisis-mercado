"""
genesis_bridge
Paquete adaptador institucional entre el Catálogo Maestro SSRN v1.3.0 y el Motor Genesis.
"""

from genesis_bridge.catalog_schema import (
    HumanReviewStatus,
    HypothesisProvenance,
    HypothesisSpec,
    OperationalStatus,
    PromotionState,
    SearchSpaceParam,
    TerminalState,
)
from genesis_bridge.certificate import (
    GenesisCertificate,
    issue_statistical_gate_certificate,
    promote_to_live_limited,
    promote_to_validated_genesis,
    verify_certificate,
)
from genesis_bridge.errors import (
    CatalogValidationError,
    GenesisBridgeError,
    PromotionGateError,
    RegimeLeakageError,
    UncertifiedStrategyError,
)

__all__ = [
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
