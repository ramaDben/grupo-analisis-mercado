"""
genesis_bridge.regime_filter
Filtro de régimen macroeconómico Point-in-Time sin lookahead bias.
Consume snapshots históricos de macro_bias_history.jsonl y aplica la matriz SSOT.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from genesis.strategy.contract import Direction
from genesis_bridge.errors import RegimeLeakageError

DEFAULT_HISTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "data central"
    / "DATA DRIVERS USDCLP"
    / "macro_bias_history.jsonl"
)


class RegimeHistoryManager:
    """Gestiona los snapshots macroeconómicos históricos para consultas Point-in-Time."""

    def __init__(self, history_path: Path | str | None = None) -> None:
        self._history_path = Path(history_path) if history_path is not None else DEFAULT_HISTORY_PATH
        self._snapshots: list[dict[str, Any]] = []
        self._file_hash: str = ""
        self._load_history()

    def _load_history(self) -> None:
        if not self._history_path.exists():
            self._snapshots = []
            self._file_hash = ""
            return

        raw_text = self._history_path.read_text(encoding="utf-8")
        self._file_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        snapshots = []
        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                item = json.loads(line_str)
                # Parsear timestamp UTC
                as_of_str = item.get("as_of_utc", "")
                dt = datetime.fromisoformat(as_of_str.replace("Z", "+00:00"))
                item["_dt"] = dt
                snapshots.append(item)
            except Exception:
                continue

        # Ordenar cronológicamente
        self._snapshots = sorted(snapshots, key=lambda x: x["_dt"])

    @property
    def history_hash(self) -> str:
        return self._file_hash

    def get_snapshot_at(self, target_time: datetime) -> dict[str, Any] | None:
        """
        Retorna el último snapshot macro disponible con as_of_utc <= target_time.
        Si no existe ninguno, retorna None (Point-in-Time estricto).
        """
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        valid_snapshots = [s for s in self._snapshots if s["_dt"] <= target_time]
        if not valid_snapshots:
            return None
        return valid_snapshots[-1]

    def get_regime_code_at(self, target_time: datetime) -> str:
        """
        Retorna el código de régimen vigente en target_time.
        Si no hay snapshot disponible, lanza RegimeLeakageError o retorna R0_CALMA_RANGO por defecto defensivo.
        """
        snap = self.get_snapshot_at(target_time)
        if snap is None:
            # Fallback seguro: Calma / Rango
            return "R0_CALMA_RANGO"
        return snap.get("regimen", "R0_CALMA_RANGO")

    def is_direction_allowed(
        self,
        setup_id: str,
        symbol: str,
        direction: Direction,
        timestamp: datetime,
        matrix_ssot: Mapping[str, Any],
    ) -> bool:
        """
        Verifica si una intención de trading está autorizada en timestamp según la matriz SSOT.
        """
        regime = self.get_regime_code_at(timestamp)
        regime_setups = matrix_ssot.get(regime, {})

        setup_entry = regime_setups.get(setup_id)
        if setup_entry is None:
            for k, v in regime_setups.items():
                if k.endswith(setup_id) or setup_id.endswith(k):
                    setup_entry = v
                    break

        if setup_entry is None:
            return False

        if setup_entry.get("estado") == "PROHIBIDA":
            return False

        allowed_dirs = setup_entry.get("direcciones", {}).get(symbol.upper(), [])
        dir_str = "LONG" if direction is Direction.LONG else "SHORT"
        return dir_str in allowed_dirs

    def apply_point_in_time_filter(
        self,
        df: Any,
        setup_id: str,
        symbol: str,
        matrix_ssot: Mapping[str, Any],
    ) -> Any:
        """
        Aplica el filtro de régimen Point-in-Time barra por barra sobre el DataFrame.
        Añade las columnas 'regime_code' y 'regime_allowed' para auditoría.
        Descarta barras donde el régimen declare PROHIBIDA la estrategia para el activo.
        """
        if len(df) == 0:
            return df

        regimes = []
        allowed_flags = []
        for _, row in df.iterrows():
            ts = row["timestamp"]
            if hasattr(ts, "to_pydatetime"):
                ts = ts.to_pydatetime()
            regime = self.get_regime_code_at(ts)
            regimes.append(regime)

            # Verificar si la estrategia está permitida en este régimen para el activo
            regime_setups = matrix_ssot.get(regime, {})
            setup_entry = regime_setups.get(setup_id)
            if setup_entry is None:
                for k, v in regime_setups.items():
                    if k.endswith(setup_id) or setup_id.endswith(k):
                        setup_entry = v
                        break

            if setup_entry is None or setup_entry.get("estado") == "PROHIBIDA":
                allowed_flags.append(False)
            else:
                allowed_dirs = setup_entry.get("direcciones", {}).get(symbol.upper(), [])
                allowed_flags.append(len(allowed_dirs) > 0)

        df_annotated = df.copy()
        df_annotated["regime_code"] = regimes
        df_annotated["regime_allowed"] = allowed_flags
        return df_annotated[df_annotated["regime_allowed"]].reset_index(drop=True)
