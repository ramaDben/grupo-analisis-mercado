"""
tests/genesis_bridge/test_candidate_factory.py
Tests unitarios para el contrato StrategyCandidate y RiskLevelsProvider en el candidato S3 Donchian Breakout.
"""

from datetime import datetime, timedelta, timezone
import pytest

from genesis.data.store import AnnotatedBar
from genesis.strategy.contract import Direction, EntryIntent, StrategyCandidate
from genesis_bridge.candidate_factory import S3DonchianBreakoutCandidate
from genesis_bridge.data_adapter import get_symbol_figure


def _make_bar(close: float, high: float, low: float, open_p: float = 100.0) -> AnnotatedBar:
    dt = datetime(2026, 8, 20, 14, 0, tzinfo=timezone.utc)
    return AnnotatedBar(
        timestamp_utc=dt,
        open=open_p,
        high=high,
        low=low,
        close=close,
        tick_volume=100,
        trading_day=dt.date(),
        in_session=True,
        session_open_utc=dt,
        session_close_utc=dt + timedelta(hours=3),
    )


def test_s3_candidate_duck_typing_and_warmup():
    """S3 debe implementar StrategyCandidate y no emitir señales antes de completar el warmup."""
    fig = get_symbol_figure("XAUUSD")
    candidate = S3DonchianBreakoutCandidate(figure=fig, lookback_donchian=5, atr_period=5)

    assert isinstance(candidate, StrategyCandidate)
    assert candidate.candidate_id == "S3"

    # Enviar barras sin superar el warmup
    for i in range(5):
        intents = candidate.on_bar(_make_bar(close=2000.0, high=2005.0, low=1995.0))
        assert intents == []


def test_s3_candidate_breakout_and_risk_levels():
    """S3 debe emitir señal alcista cuando el precio supera el canal con expansión y resolver sus risk_levels."""
    fig = get_symbol_figure("XAUUSD")
    candidate = S3DonchianBreakoutCandidate(
        figure=fig,
        lookback_donchian=5,
        banda_filtro_atr_mult=0.1,
        expansion_rango_atr_mult=1.0,
        stop_loss_atr_mult=1.5,
        trailing_chandelier_atr_mult=3.0,
        atr_period=5,
    )

    # 1. Warmup con rango estrecho (2000 - 2005)
    for _ in range(6):
        candidate.on_bar(_make_bar(close=2002.0, high=2005.0, low=1998.0))

    # 2. Barra de quiebre alcista masivo con expansión de rango
    breakout_bar = _make_bar(close=2030.0, high=2035.0, low=2000.0)
    intents = candidate.on_bar(breakout_bar)

    assert len(intents) == 1
    intent = intents[0]
    assert intent.direction is Direction.LONG
    assert intent.candidate_id == "S3"

    # 3. Resolver risk_levels
    sl, tp = candidate.risk_levels(intent)
    assert sl < 2030.0, f"Stop Loss debe ser menor al precio de cierre: {sl} >= 2030.0"
    assert tp > 2030.0, f"Take Profit debe ser mayor al precio de cierre: {tp} <= 2030.0"


def test_s2_mean_reversion_rsi_candidate():
    """S2 debe implementar StrategyCandidate y emitir señal al detectar sobreventa extrema + giro."""
    from genesis_bridge.candidate_factory import S2MeanReversionRSICandidate

    fig = get_symbol_figure("XAUUSD")
    candidate = S2MeanReversionRSICandidate(
        figure=fig,
        rsi_sobreventa_umbral=30.0,
        rsi_sobrecompra_umbral=70.0,
        periodo_rsi=5,
        periodo_sma=5,
    )

    # 1. Warmup a la baja para llevar el RSI a sobreventa extrema (< 30)
    prices = [2050.0, 2040.0, 2030.0, 2020.0, 2010.0, 2000.0]
    for p in prices:
        candidate.on_bar(_make_bar(close=p, high=p + 2.0, low=p - 2.0, open_p=p + 1.0))

    # 2. Barra de giro alcista (close > open)
    turn_bar = _make_bar(close=2005.0, high=2008.0, low=1998.0, open_p=2001.0)
    intents = candidate.on_bar(turn_bar)

    assert len(intents) == 1
    intent = intents[0]
    assert intent.direction is Direction.LONG
    assert intent.candidate_id == "S2"

    sl, tp = candidate.risk_levels(intent)
    assert sl < 2005.0
    assert tp >= 2005.0
