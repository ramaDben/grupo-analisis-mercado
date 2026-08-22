"""
tests/genesis_bridge/test_regime_filter.py
Tests unitarios del gestor de historial de régimen Point-in-Time y prevención de lookahead bias.
"""

from datetime import datetime, timezone
import pytest

from genesis.strategy.contract import Direction
from genesis_bridge.regime_filter import RegimeHistoryManager


def test_regime_point_in_time_lookup():
    """El gestor debe retornar el último snapshot previo o igual al timestamp consultado."""
    mgr = RegimeHistoryManager()
    assert mgr.history_hash != ""

    # Consulta con fecha actual
    now_utc = datetime.now(timezone.utc)
    snap = mgr.get_snapshot_at(now_utc)
    assert snap is not None
    assert "regimen" in snap


def test_regime_direction_permission():
    """Verifica el filtrado de direcciones permitidas según la matriz SSOT."""
    mgr = RegimeHistoryManager()
    dummy_matrix = {
        "R0_CALMA_RANGO": {
            "BREAKOUT_DONCHIAN_H1": {
                "estado": "OPTIMA",
                "direcciones": {"XAUUSD": ["LONG", "SHORT"]}
            }
        }
    }

    now_utc = datetime.now(timezone.utc)
    allowed_long = mgr.is_direction_allowed("BREAKOUT_DONCHIAN_H1", "XAUUSD", Direction.LONG, now_utc, dummy_matrix)
    assert allowed_long is True

    allowed_usdclp = mgr.is_direction_allowed("BREAKOUT_DONCHIAN_H1", "USDCLP", Direction.LONG, now_utc, dummy_matrix)
    assert allowed_usdclp is False
