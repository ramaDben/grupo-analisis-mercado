#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ticket_engine.py
Motor Cuantitativo de Generación y Validación de Tickets H1 (Jugada 2.1 - Motor GI v3.0).
Consume el sesgo macro de macro_bias_output.json y las series intradiarias H1,
evalúa triggers sobre velas cerradas, aplica la ley de riesgo y emite tickets deterministas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
import yaml

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "playbook_config.yaml"

DATA_CENTRAL = BASE_DIR / "data central"
PRICES_DIR = DATA_CENTRAL / "DATA PRECIOS OHLC"
BIAS_OUTPUT_FILE = DATA_CENTRAL / "DATA DRIVERS USDCLP" / "macro_bias_output.json"
TICKETS_OUTPUT_FILE = DATA_CENTRAL / "DATA DRIVERS USDCLP" / "tickets_output.json"


@dataclass(frozen=True)
class QuantitativeTicket:
    """Contrato inmutable de Ticket Cuantitativo (Motor GI v3.0)."""
    ticket_id: str
    symbol: str
    regime: str
    setup: str              # "BREAKOUT_ADC" | "PULLBACK_EMA" | "MEANREV_R0" | "WAIT"
    side: str               # "BUY" | "SELL"
    trigger_time: Optional[str]
    entry_type: Optional[str]  # "BUY_STOP" | "SELL_STOP" | "BUY_LIMIT" | "SELL_LIMIT"
    entry_price: Optional[float]
    entry_valid_until: Optional[str]
    stop_loss: Optional[float]
    take_profit_1: Optional[float]
    take_profit_2: Optional[float]
    rr_to_tp1: Optional[float]
    spread_atr_ratio: Optional[float]
    confirm_symbol: Optional[str]
    confirm_ok: bool
    invalidation_rule: Optional[str]
    session_kill_time: Optional[str]
    status: str             # "WAIT" | "ARMED" | "READY" | "BLOCKED"
    block_reason: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)


def cargar_config() -> dict:
    """Carga la configuración YAML maestra."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No se encontró archivo de configuración en {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calcular_indicadores_h1(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores técnicos necesarios sobre la serie H1 si no vienen calculados."""
    df = df.copy()
    if "close" not in df.columns:
        return df

    closes = df["close"]
    highs = df["high"]
    lows = df["low"]

    # EMAs
    if "ema_20" not in df.columns:
        df["ema_20"] = closes.ewm(span=20, adjust=False).mean()
    if "ema_50" not in df.columns:
        df["ema_50"] = closes.ewm(span=50, adjust=False).mean()
    if "ema_100" not in df.columns:
        df["ema_100"] = closes.ewm(span=100, adjust=False).mean()

    # Bollinger Bands (20, 2 std)
    if "sma_20" not in df.columns:
        df["sma_20"] = closes.rolling(window=20).mean()
    rolling_std = closes.rolling(window=20).std()
    df["bb_upper"] = df["sma_20"] + (2.0 * rolling_std)
    df["bb_lower"] = df["sma_20"] - (2.0 * rolling_std)

    # Donchian 50 (sobre las 50 barras previas, excluyendo la actual)
    df["donchian_high_50"] = highs.shift(1).rolling(window=50).max()
    df["donchian_low_50"] = lows.shift(1).rolling(window=50).min()

    # True Range & ATR 14 (Wilder alpha=1/14)
    prev_close = closes.shift(1)
    tr1 = highs - lows
    tr2 = (highs - prev_close).abs()
    tr3 = (lows - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["tr"] = tr
    if "atr_14" not in df.columns or df["atr_14"].isna().all():
        df["atr_14"] = tr.ewm(alpha=1.0/14.0, adjust=False).mean()

    # RSI 14 (Sin fillna sintético)
    if "rsi_14" not in df.columns or df["rsi_14"].isna().all():
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0/14.0, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0/14.0, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))

    # ADX 14 proxy / calculation (Sin fillna sintético)
    if "adx_14" not in df.columns or df["adx_14"].isna().all():
        up_move = highs.diff()
        down_move = -lows.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        tr_smooth = tr.ewm(alpha=1.0/14.0, adjust=False).mean()
        plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1.0/14.0, adjust=False).mean() / tr_smooth.replace(0, np.nan)
        minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1.0/14.0, adjust=False).mean() / tr_smooth.replace(0, np.nan)
        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        df["adx_14"] = dx.ewm(alpha=1.0/14.0, adjust=False).mean()

    return df


def calcular_donchian(df: pd.DataFrame, period: int = 50) -> tuple[float, float]:
    """Calcula los extremos de Donchian sobre las N barras anteriores a la última cerrada."""
    if len(df) <= period:
        return float(df["high"].max()), float(df["low"].min())
    subset = df.iloc[-(period + 1):-1]
    return float(subset["high"].max()), float(subset["low"].min())


def elegir_setup(
    regimen: str,
    sesgo_etiqueta: str,
    permitidos: list[str],
    prohibidos: list[str],
    adx: Optional[float],
    ancho_donchian: float,
    atr: float,
    ema_alineada: bool = False
) -> str:
    """
    Selecciona exactamente UN setup mutuamente excluyente según régimen y estructura.
    Prioridad:
    1. R0 con ADX conocido < 20 -> MEANREV_R0
    2. Compresión real (ancho Donchian <= 2.5 * ATR) -> BREAKOUT_ADC
    3. Tendencia con EMAs alineadas y ADX conocido >= 20 -> PULLBACK_EMA
    4. De lo contrario -> WAIT
    """
    if sesgo_etiqueta == "DATOS_INCOMPLETOS" or not permitidos:
        return "WAIT"

    # 1. R0 Rango -> Reversión a la media (Exige ADX conocido < 20)
    if regimen == "R0_CALMA_RANGO" and (adx is not None and adx < 20.0) and any(s.startswith("FADE_") or s.startswith("MEAN_REVERSION_") for s in permitidos):
        if not any(v in ["MEANREV_R0", "MEAN_REVERSION_RSI_H1", "FADE_SUPPORT_RESISTANCE_H1"] for v in prohibidos):
            return "MEANREV_R0"

    # 2. Compresión de volatilidad -> Breakout ADC (gana ante compresión real)
    if atr > 0 and ancho_donchian <= (2.5 * atr) and any(s.startswith("BREAKOUT_") or s.startswith("BREAKDOWN_") for s in permitidos):
        if not any(v in ["BREAKOUT_ADC", "BREAKOUT_DONCHIAN_H1", "BREAKOUT_CHASE_LONG", "BREAKDOWN_DONCHIAN_H1", "BREAKOUT_VOLATILITY_H1"] for v in prohibidos):
            return "BREAKOUT_ADC"

    # 3. Tendencia confirmada -> Pullback (Exige ADX conocido >= 20)
    if (adx is not None and adx >= 20.0) and ema_alineada and any(s.startswith("PULLBACK_") for s in permitidos):
        if not any(v in ["PULLBACK_EMA", "PULLBACK_EMA20_H1", "PULLBACK_SHORT_EMA20", "PULLBACK_EMA16_H1", "PULLBACK_EMA50_H1"] for v in prohibidos):
            return "PULLBACK_EMA"

    return "WAIT"


def evaluar_firma_dow(symbol: str, side: str, regimen: str, metricas: dict) -> tuple[str, bool]:
    """Evalúa la confirmación cruzada intermercado (Dow) para el ticket sin defaults sintéticos."""
    if symbol == "USDCLP":
        cu_5d = metricas.get("cobre_variacion_5d_pct")
        if side == "BUY":
            ok = (cu_5d is not None and cu_5d <= 0.0) or (regimen in ["R3_ESTANFLACION_SHOCK", "R4_RECESION_VUELO_CALIDAD"])
            return "COBRE_COMEX", bool(ok)
        else:
            ok = (cu_5d is not None and cu_5d >= 0.0) or (regimen == "R2_GOLDILOCKS_EXPANSION")
            return "COBRE_COMEX", bool(ok)

    elif symbol == "XAUUSD":
        tips_val = metricas.get("tasa_real_tips10y_pct")
        if side == "BUY":
            ok = (regimen in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"]) or (tips_val is not None and tips_val <= 2.30)
            return "TIPS_REAL_10Y", bool(ok)
        else:
            return "TIPS_REAL_10Y", False if regimen in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"] else True

    elif symbol in ["WTI", "BRENT"]:
        oil_signed = metricas.get("petroleo_shock_signed_5d_pct")
        if side == "BUY":
            ok = (regimen == "R3_ESTANFLACION_SHOCK") or (oil_signed is not None and oil_signed > 0.0)
            return "PETROLEO_INTERMERCADO", bool(ok)
        else:
            return "PETROLEO_INTERMERCADO", True

    elif symbol == "US100":
        dgs10_val = metricas.get("dgs10")
        if dgs10_val is None:
            return "DGS10", False
        if side == "BUY":
            ok = (regimen not in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"]) and (dgs10_val <= 4.70)
            return "DGS10", bool(ok)
        else:
            ok = (regimen in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"]) or (dgs10_val > 4.70)
            return "DGS10", bool(ok)

    return "INTERMARKET", True


def evaluar_ticket_activo(
    symbol: str,
    asset_bias: dict,
    regimen_dict: dict,
    metricas: dict,
    df_h1: Optional[pd.DataFrame],
    cfg: dict
) -> QuantitativeTicket:
    """Evalúa y construye el objeto QuantitativeTicket determinista para un activo."""
    regimen = regimen_dict.get("codigo", "R0_CALMA_RANGO")
    confirmado_hist = regimen_dict.get("confirmado_por_historesis", False)

    sesgo_score = asset_bias.get("sesgo_score", 0.0)
    sesgo_etiqueta = asset_bias.get("sesgo_etiqueta", "NEUTRAL")
    permitidos = asset_bias.get("setups_permitidos", [])
    prohibidos = asset_bias.get("setups_prohibidos", [])
    rp = asset_bias.get("parametros_riesgo", {})

    ticket_cfg = cfg.get("ticket_parameters", {})
    friction_caps = ticket_cfg.get("friction_caps", {})
    c_i = friction_caps.get(symbol, 0.15)
    rr_min = ticket_cfg.get("rr_min_tp1", 1.0)
    valid_bars = ticket_cfg.get("entry_valid_bars", 2)
    session_kill = ticket_cfg.get("session_kill", {}).get(symbol)

    atr_bias = rp.get("atr_h1")
    ticket_id = f"TICK-{symbol}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6]}"

    # Gate 1: Régimen confirmado
    if not confirmado_hist:
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup="WAIT", side="BUY" if sesgo_score >= 0 else "SELL",
            trigger_time=None, entry_type=None, entry_price=None, entry_valid_until=None, stop_loss=None,
            take_profit_1=None, take_profit_2=None, rr_to_tp1=None, spread_atr_ratio=None, confirm_symbol=None,
            confirm_ok=False, invalidation_rule=None, session_kill_time=session_kill, status="BLOCKED", block_reason="UNCONFIRMED_REGIME"
        )

    # Gate 2: ATR ausente
    if atr_bias is None or atr_bias <= 0:
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup="WAIT", side="BUY" if sesgo_score >= 0 else "SELL",
            trigger_time=None, entry_type=None, entry_price=None, entry_valid_until=None, stop_loss=None,
            take_profit_1=None, take_profit_2=None, rr_to_tp1=None, spread_atr_ratio=None, confirm_symbol=None,
            confirm_ok=False, invalidation_rule=None, session_kill_time=session_kill, status="BLOCKED", block_reason="MISSING_ATR"
        )

    # Gate 3: Serie H1 disponible
    if df_h1 is None or len(df_h1) < 60:
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup="WAIT", side="BUY" if sesgo_score >= 0 else "SELL",
            trigger_time=None, entry_type=None, entry_price=None, entry_valid_until=None, stop_loss=None,
            take_profit_1=None, take_profit_2=None, rr_to_tp1=None, spread_atr_ratio=None, confirm_symbol=None,
            confirm_ok=False, invalidation_rule=None, session_kill_time=session_kill, status="BLOCKED", block_reason="NO_H1_SERIES"
        )

    df_calc = calcular_indicadores_h1(df_h1)
    # Evaluamos sobre la última barra cerrada (df.iloc[-1])
    last_bar = df_calc.iloc[-1]
    prev_bar = df_calc.iloc[-2] if len(df_calc) >= 2 else last_bar

    atr_actual = float(last_bar.get("atr_14") or atr_bias)
    adx_raw = last_bar.get("adx_14")
    adx_actual = float(adx_raw) if (adx_raw is not None and not pd.isna(adx_raw)) else None
    rsi_raw = last_bar.get("rsi_14")
    rsi_actual = float(rsi_raw) if (rsi_raw is not None and not pd.isna(rsi_raw)) else None

    ema_20 = float(last_bar.get("ema_20", 0.0))
    ema_50 = float(last_bar.get("ema_50", 0.0))
    ema_100 = float(last_bar.get("ema_100", 0.0))
    ema_alineada = (ema_20 > ema_50 > ema_100) if sesgo_score >= 0 else (ema_20 < ema_50 < ema_100)

    donchian_high, donchian_low = calcular_donchian(df_calc, period=50)
    ancho_donchian = donchian_high - donchian_low

    setup_elegido = elegir_setup(
        regimen, sesgo_etiqueta, permitidos, prohibidos, adx_actual, ancho_donchian, atr_actual, ema_alineada
    )

    if setup_elegido == "WAIT":
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup="WAIT", side="BUY" if sesgo_score >= 0 else "SELL",
            trigger_time=str(last_bar.get("time")), entry_type=None, entry_price=None, entry_valid_until=None, stop_loss=None,
            take_profit_1=None, take_profit_2=None, rr_to_tp1=None, spread_atr_ratio=None, confirm_symbol=None,
            confirm_ok=False, invalidation_rule=None, session_kill_time=session_kill, status="WAIT", block_reason="NO_ELIGIBLE_SETUP"
        )

    # Determinar lado
    if setup_elegido == "MEANREV_R0":
        bb_lower = float(last_bar.get("bb_lower", last_bar["close"] - 2 * atr_actual))
        bb_upper = float(last_bar.get("bb_upper", last_bar["close"] + 2 * atr_actual))
        if prev_bar["close"] < bb_lower and last_bar["close"] >= bb_lower:
            side = "BUY"
        elif prev_bar["close"] > bb_upper and last_bar["close"] <= bb_upper:
            side = "SELL"
        else:
            side = "BUY" if sesgo_score >= 0 else "SELL"
    else:
        side = "BUY" if sesgo_score >= 0 else "SELL"

    # Firma Dow
    confirm_sym, confirm_ok = evaluar_firma_dow(symbol, side, regimen, metricas)

    # Fricción
    spread_val = rp.get("spread")
    spread_ratio = (spread_val / atr_actual) if (spread_val is not None and atr_actual > 0) else None
    if spread_ratio is not None and spread_ratio > c_i:
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup=setup_elegido, side=side,
            trigger_time=str(last_bar.get("time")), entry_type=None, entry_price=None, entry_valid_until=None, stop_loss=None,
            take_profit_1=None, take_profit_2=None, rr_to_tp1=None, spread_atr_ratio=spread_ratio, confirm_symbol=confirm_sym,
            confirm_ok=confirm_ok, invalidation_rule=None, session_kill_time=session_kill, status="BLOCKED", block_reason="HIGH_FRICTION"
        )

    # Evaluación de Triggers sobre vela cerrada
    trigger_activo = False
    entry_type = None
    entry_price = None

    if setup_elegido == "BREAKOUT_ADC":
        rango_barra = float(last_bar["high"] - last_bar["low"])
        cuerpo_barra = abs(float(last_bar["close"] - last_bar["open"]))
        es_cuerpo_dominante = (cuerpo_barra >= 0.5 * rango_barra) if rango_barra > 0 else False
        tr_barra = float(last_bar.get("tr", rango_barra))
        tr_ratio = tr_barra / atr_actual if atr_actual > 0 else 1.0
        rsi_ok_breakout = (rsi_actual <= 75.0) if (rsi_actual is not None and side == "BUY") else ((rsi_actual >= 25.0) if (rsi_actual is not None and side == "SELL") else True)

        if side == "BUY":
            if (last_bar["close"] > donchian_high) and es_cuerpo_dominante and (tr_ratio >= 1.0) and rsi_ok_breakout:
                trigger_activo = True
                entry_type = "BUY_STOP"
                entry_price = float(last_bar["high"])
        else:
            if (last_bar["close"] < donchian_low) and es_cuerpo_dominante and (tr_ratio >= 1.0) and rsi_ok_breakout:
                trigger_activo = True
                entry_type = "SELL_STOP"
                entry_price = float(last_bar["low"])

    elif setup_elegido == "PULLBACK_EMA":
        ema_20 = float(last_bar["ema_20"])
        ema_50 = float(last_bar["ema_50"])
        ema_100 = float(last_bar["ema_100"])

        if side == "BUY":
            ema_alineada = ema_20 > ema_50 > ema_100
            toco_ema = float(last_bar["low"]) <= ema_20
            cerro_arriba = float(last_bar["close"]) > ema_20
            if ema_alineada and toco_ema and cerro_arriba:
                trigger_activo = True
                entry_type = "BUY_STOP"
                entry_price = float(last_bar["high"])
        else:
            ema_alineada = ema_20 < ema_50 < ema_100
            toco_ema = float(last_bar["high"]) >= ema_20
            cerro_arriba = float(last_bar["close"]) < ema_20
            if ema_alineada and toco_ema and cerro_arriba:
                trigger_activo = True
                entry_type = "SELL_STOP"
                entry_price = float(last_bar["low"])

    elif setup_elegido == "MEANREV_R0":
        bb_lower = float(last_bar["bb_lower"])
        bb_upper = float(last_bar["bb_upper"])
        if side == "BUY":
            if float(prev_bar["close"]) < bb_lower and float(last_bar["close"]) >= bb_lower and (rsi_actual is not None and rsi_actual < 35.0):
                trigger_activo = True
                entry_type = "BUY_LIMIT"
                entry_price = float(last_bar["close"])
        else:
            if float(prev_bar["close"]) > bb_upper and float(last_bar["close"]) <= bb_upper and (rsi_actual is not None and rsi_actual > 65.0):
                trigger_activo = True
                entry_type = "SELL_LIMIT"
                entry_price = float(last_bar["close"])

    # 4. Si NO hay trigger activo -> Estado ARMED (SIN precios de orden ni SL/TP fantasma)
    if not trigger_activo:
        return QuantitativeTicket(
            ticket_id=ticket_id,
            symbol=symbol,
            regime=regimen,
            setup=setup_elegido,
            side=side,
            trigger_time=str(last_bar.get("time")),
            entry_type=None,
            entry_price=None,
            entry_valid_until=None,
            stop_loss=None,
            take_profit_1=None,
            take_profit_2=None,
            rr_to_tp1=None,
            spread_atr_ratio=round(spread_ratio, 4) if spread_ratio else None,
            confirm_symbol=confirm_sym,
            confirm_ok=confirm_ok,
            invalidation_rule=None,
            session_kill_time=session_kill,
            status="ARMED",
            block_reason="TRIGGER_PENDING"
        )

    # 5. Si HAY trigger activo -> Cálculo real de SL / TP / R:R
    dist_yaml = 1.5 * atr_actual
    swing_20_low = float(df_calc["low"].iloc[-20:].min())
    swing_20_high = float(df_calc["high"].iloc[-20:].max())

    if side == "BUY":
        dist_struct = abs(entry_price - swing_20_low)
        if 0.5 * atr_actual <= dist_struct <= 1.5 * atr_actual:
            stop_loss = swing_20_low
        else:
            stop_loss = entry_price - dist_yaml

        if setup_elegido == "MEANREV_R0":
            tp1 = float(last_bar.get("sma_20", entry_price + atr_actual))
            tp2 = None
        else:
            tp1 = entry_price + (1.0 * atr_actual)
            tp2 = entry_price + (1.5 * atr_actual)

        risk_dist = abs(entry_price - stop_loss)
        reward_dist = abs(tp1 - entry_price)
        rr_val = (reward_dist / risk_dist) if risk_dist > 0 else 0.0

    else:  # SELL
        dist_struct = abs(entry_price - swing_20_high)
        if 0.5 * atr_actual <= dist_struct <= 1.5 * atr_actual:
            stop_loss = swing_20_high
        else:
            stop_loss = entry_price + dist_yaml

        if setup_elegido == "MEANREV_R0":
            tp1 = float(last_bar.get("sma_20", entry_price - atr_actual))
            tp2 = None
        else:
            tp1 = entry_price - (1.0 * atr_actual)
            tp2 = entry_price - (1.5 * atr_actual)

        risk_dist = abs(entry_price - stop_loss)
        reward_dist = abs(entry_price - tp1)
        rr_val = (reward_dist / risk_dist) if risk_dist > 0 else 0.0

    # R:R Gate
    if rr_val < rr_min:
        return QuantitativeTicket(
            ticket_id=ticket_id, symbol=symbol, regime=regimen, setup=setup_elegido, side=side,
            trigger_time=str(last_bar.get("time")), entry_type=entry_type, entry_price=round(entry_price, 2),
            entry_valid_until=None, stop_loss=round(stop_loss, 2), take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2) if tp2 else None, rr_to_tp1=round(rr_val, 2), spread_atr_ratio=spread_ratio,
            confirm_symbol=confirm_sym, confirm_ok=confirm_ok, invalidation_rule="R:R insuficiente",
            session_kill_time=session_kill, status="BLOCKED", block_reason="RR_LESS_THAN_1"
        )

    # Estado final del trigger
    if not confirm_ok:
        status = "BLOCKED"
        block_reason = "DOW_CONFIRMATION_FAILED"
    else:
        status = "READY"
        block_reason = None

    invalidation_rule = f"Cierre H1 contra donchian_mid ({((donchian_high+donchian_low)/2.0):.2f}) o fin de sesión"
    valid_until = f"+{valid_bars} velas H1"

    return QuantitativeTicket(
        ticket_id=ticket_id,
        symbol=symbol,
        regime=regimen,
        setup=setup_elegido,
        side=side,
        trigger_time=str(last_bar.get("time")),
        entry_type=entry_type,
        entry_price=round(entry_price, 2),
        entry_valid_until=valid_until,
        stop_loss=round(stop_loss, 2),
        take_profit_1=round(tp1, 2),
        take_profit_2=round(tp2, 2) if tp2 else None,
        rr_to_tp1=round(rr_val, 2),
        spread_atr_ratio=round(spread_ratio, 4) if spread_ratio else None,
        confirm_symbol=confirm_sym,
        confirm_ok=confirm_ok,
        invalidation_rule=invalidation_rule,
        session_kill_time=session_kill,
        status=status,
        block_reason=block_reason
    )


def cargar_serie_h1_archivo(symbol: str) -> Optional[pd.DataFrame]:
    """Carga serie H1 desde data central/DATA PRECIOS OHLC/{symbol}_H1.json."""
    file_path = PRICES_DIR / f"{symbol}_H1.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows = data.get("rows", [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        return df
    except Exception:
        return None


def generar_tickets(
    bias_data: dict,
    series_dict: dict[str, Optional[pd.DataFrame]],
    cfg: dict
) -> dict[str, QuantitativeTicket]:
    """Genera el catálogo de tickets evaluados para todos los activos del bias data."""
    regimen_dict = bias_data.get("regimen_macro_global", {})
    metricas = bias_data.get("metricas_clave", {})
    activos = bias_data.get("activos", {})

    tickets_res = {}
    for sym, val in activos.items():
        df_h1 = series_dict.get(sym)
        ticket = evaluar_ticket_activo(sym, val, regimen_dict, metricas, df_h1, cfg)
        tickets_res[sym] = ticket

    return tickets_res


def ejecutar_motor_tickets(verbose: bool = True) -> dict:
    """Ejecuta el pipeline completo de tickets consumiendo macro_bias_output.json."""
    cfg = cargar_config()

    if not BIAS_OUTPUT_FILE.exists():
        raise FileNotFoundError(f"No se encontró archivo de sesgo en {BIAS_OUTPUT_FILE}")

    with open(BIAS_OUTPUT_FILE, "r", encoding="utf-8") as f:
        bias_data = json.load(f)

    # Cargar series H1 de archivos
    series_dict = {}
    for sym in bias_data.get("activos", {}).keys():
        df = cargar_serie_h1_archivo(sym)
        series_dict[sym] = df

    tickets_dict = generar_tickets(bias_data, series_dict, cfg)

    ahora_iso = datetime.now(timezone.utc).isoformat()
    ready_tickets = [t.to_dict() for t in tickets_dict.values() if t.status == "READY"]
    all_tickets = {sym: t.to_dict() for sym, t in tickets_dict.items()}

    output_payload = {
        "schema_version": "3.0.0",
        "generated_at_utc": ahora_iso,
        "regimen_activo": bias_data.get("regimen_macro_global", {}).get("codigo"),
        "total_activos_evaluados": len(tickets_dict),
        "total_tickets_ready": len(ready_tickets),
        "tickets_ready": ready_tickets,
        "tickets_evaluados": all_tickets
    }

    TICKETS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TICKETS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    if verbose:
        print("\n" + "=" * 80)
        print(f"🎯 MOTOR DE TICKETS CUANTITATIVOS H1 — MOTOR GI v3.0")
        print(f"⏰ Generated At UTC: {ahora_iso}")
        print(f"🏛️  Régimen Macroeconómico: {output_payload['regimen_activo']}")
        print(f"📊 Tickets READY: {len(ready_tickets)} / {len(tickets_dict)}")
        print("=" * 80)
        for sym, t in tickets_dict.items():
            st_color = "🟢" if t.status == "READY" else ("🟡" if t.status == "ARMED" else "🔴")
            print(f"{st_color} [{sym}] -> Status: {t.status} | Setup: {t.setup} | Side: {t.side}")
            if t.status == "READY":
                print(f"   • Entrada : {t.entry_type} {t.entry_price} ({t.entry_valid_until})")
                print(f"   • SL / TP : SL {t.stop_loss} | TP1 {t.take_profit_1} (R:R {t.rr_to_tp1})")
                print(f"   • Firma   : {t.confirm_symbol} [OK]")
            elif t.block_reason:
                print(f"   • Motivo  : {t.block_reason}")
        print("\n" + "=" * 80 + "\n")

    return output_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de Tickets Cuantitativos H1")
    parser.add_argument("--json", action="store_true", help="Imprime solo salida JSON")
    args = parser.parse_args()

    res = ejecutar_motor_tickets(verbose=not args.json)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
