"""
genesis_bridge.search_plan
Generación de grilla cartesiana determinista y registro append-only de trials.
Calcula N_trials_total = producto(cardinalidades) y previene la eliminación de trials negativos.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from genesis_bridge.catalog_schema import HypothesisSpec


@dataclass(frozen=True, slots=True)
class TrialConfig:
    """Configuración concreta de un trial individual dentro del espacio de búsqueda."""
    trial_index: int
    params: Mapping[str, float]
    config_hash: str


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """Plan de búsqueda exhaustivo para una hipótesis candidata."""
    setup_id: str
    symbol: str
    n_trials_total: int
    param_names: tuple[str, ...]
    param_grid_cardinalities: Mapping[str, int]
    search_plan_hash: str
    trials: tuple[TrialConfig, ...]

    def __iter__(self) -> Iterator[TrialConfig]:
        return iter(self.trials)


def build_search_plan(spec: HypothesisSpec, symbol: str) -> SearchPlan:
    """
    Construye la grilla cartesiana determinista y calcula N_trials_total = producto(cardinalidades).
    """
    param_names = tuple(sorted(spec.espacio_de_busqueda_parametros.keys()))
    param_values: list[list[float]] = []
    cardinalities: dict[str, int] = {}

    for name in param_names:
        param_obj = spec.espacio_de_busqueda_parametros[name]
        vals = param_obj.grid_values()
        cardinalities[name] = len(vals)
        param_values.append(vals)

    # Producto cartesiano ordenado
    combinations = list(itertools.product(*param_values))
    n_trials = len(combinations)

    trials_list: list[TrialConfig] = []
    for idx, combo in enumerate(combinations):
        p_dict = {name: combo[i] for i, name in enumerate(param_names)}
        p_json = json.dumps(p_dict, sort_keys=True)
        c_hash = hashlib.sha256(p_json.encode("utf-8")).hexdigest()[:16]
        trials_list.append(TrialConfig(trial_index=idx, params=p_dict, config_hash=c_hash))

    plan_metadata = {
        "setup_id": spec.id_setup,
        "symbol": symbol,
        "n_trials_total": n_trials,
        "cardinalities": cardinalities,
    }
    plan_hash = hashlib.sha256(json.dumps(plan_metadata, sort_keys=True).encode("utf-8")).hexdigest()

    return SearchPlan(
        setup_id=spec.id_setup,
        symbol=symbol,
        n_trials_total=n_trials,
        param_names=param_names,
        param_grid_cardinalities=cardinalities,
        search_plan_hash=plan_hash,
        trials=tuple(trials_list),
    )


class AppendOnlyTrialLedger:
    """Ledger append-only que registra todos los trials evaluados sin permitir borrados."""

    def __init__(self, ledger_path: Path | str) -> None:
        self._ledger_path = Path(ledger_path)
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def record_trial(
        self,
        trial_id: str,
        trial_index: int,
        params: Mapping[str, float],
        success: bool,
        metrics: Mapping[str, Any],
        failure_reason: str | None = None,
        commit_hash: str = "",
        dataset_hash: str = "",
    ) -> None:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "trial_id": trial_id,
            "trial_index": trial_index,
            "params": dict(params),
            "success": success,
            "metrics": dict(metrics),
            "failure_reason": failure_reason,
            "commit_hash": commit_hash,
            "dataset_hash": dataset_hash,
        }
        with open(self._ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
