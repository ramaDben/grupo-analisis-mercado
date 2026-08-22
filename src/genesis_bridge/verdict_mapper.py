"""
genesis_bridge.verdict_mapper
Mapeo determinista de VerdictResult de Genesis a estados del ciclo de vida del catálogo.
"""

from __future__ import annotations

from typing import Any

from genesis.validation.verdict import VerdictKind, VerdictResult
from genesis_bridge.catalog_schema import PromotionState, TerminalState


def map_verdict_to_lifecycle(result: VerdictResult) -> tuple[str, str, dict[str, Any]]:
    """
    Traduce el veredicto emitido por Genesis al estado del ciclo de vida.
    Retorna: (estado_promocion, estado_operativo, resumen_metricas)
    """
    if result.verdict in (VerdictKind.GO, VerdictKind.GO_ENSEMBLE):
        return (
            PromotionState.GATE_ESTADISTICO_APROBADO.value,
            "BLOQUEADO",
            {
                "verdict": str(result.verdict),
                "winning_candidate_id": result.winning_candidate_id,
                "t1_dsr": result.t1_dsr,
                "n_trials_deflactado": result.n_trials_deflactado,
                "economics_confirmed": result.economics_confirmed,
            },
        )
    elif result.verdict == VerdictKind.GO_PARCIAL:
        return (
            PromotionState.GATE_ESTADISTICO_APROBADO.value,
            "BLOQUEADO",
            {
                "verdict": str(result.verdict),
                "winning_candidate_id": result.winning_candidate_id,
                "parcial": True,
            },
        )
    else:  # NO_GO
        return (
            TerminalState.RECHAZADO.value,
            "BLOQUEADO",
            {
                "verdict": str(result.verdict),
                "motivo": "Falla de uno o más gates estadísticos en el torneo Genesis",
            },
        )
