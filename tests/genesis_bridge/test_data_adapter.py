"""
tests/genesis_bridge/test_data_adapter.py
Tests unitarios del adaptador de datos OHLC y perfiles de costos institucionales (Regla R40).
"""

import pytest
from genesis_bridge.data_adapter import (
    get_costs_config,
    get_firm_profile,
    get_symbol_figure,
    load_ohlc_as_dataframe,
)


def test_costs_are_strictly_non_zero():
    """Regla R40: Los costos institucionales no pueden ser cero o nulos por omisión."""
    for symbol in ["XAUUSD", "USDCLP", "US100", "WTI", "BRENT"]:
        costs = get_costs_config(symbol)
        assert costs.default_spread_points > 0, f"Spread debe ser > 0 para {symbol}"
        assert costs.commission_per_lot > 0, f"Comisión debe ser > 0 para {symbol}"
        assert costs.slippage_points > 0, f"Slippage debe ser > 0 para {symbol}"


def test_symbol_figures():
    """Verifica que las especificaciones de figuras de símbolos sean coherentes."""
    xau = get_symbol_figure("XAUUSD")
    assert xau.symbol == "XAUUSD"
    assert xau.tick_value == 1.0
    assert xau.volume_step == 0.01


def test_load_ohlc_dataframe_and_hash():
    """Carga de dataset OHLC con hash SHA-256 determinista."""
    df, data_hash = load_ohlc_as_dataframe("XAUUSD", "H1")
    assert len(df) > 0
    assert len(data_hash) == 64
    for col in ["timestamp", "open", "high", "low", "close", "tick_volume", "bid", "ask"]:
        assert col in df.columns
