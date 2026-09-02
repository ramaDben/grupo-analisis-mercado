#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_ticket_engine.py
Suite de pruebas automatizadas para el Motor de Tickets Cuantitativos H1 (Jugada 2.1).
Valida contratos de ticket deterministas, selección exclusiva de setups,
cálculo de SL/TP estructural + ATR, firma Dow sin defaults sintéticos,
ausencia de ADX/RSI inventados, estado ARMED sin precios y estado READY de verdad.
"""

import json
import math
import pytest
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from scripts.ticket_engine import (
    QuantitativeTicket,
    elegir_setup,
    evaluar_ticket_activo,
    generar_tickets,
    calcular_donchian,
    calcular_indicadores_h1
)
from scripts.macro_bias_engine import cargar_config


@pytest.fixture
def config_playbook():
    return cargar_config()


def crear_serie_h1_sintetica(
    bar_count: int = 80,
    tipo: str = "compresion_breakout_buy",
    base_price: float = 930.0,
    atr_val: float = 4.0
) -> pd.DataFrame:
    """Genera serie sintética H1 con indicadores requeridos."""
    times = [f"2026-08-20T{i%24:02d}:00:00" for i in range(bar_count)]
    df = pd.DataFrame(index=range(bar_count))
    df["time"] = times

    if tipo == "compresion_breakout_buy":
        # 78 barras oscilando en rango estrecho
        base_h = base_price + 1.0
        closes = [base_h + 0.1 * math.sin(i * 0.3) for i in range(bar_count - 1)]
        highs = [c + 0.1 for c in closes]
        lows = [c - 0.1 for c in closes]
        opens = [c - 0.05 for c in closes]

        # Penúltima barra cierra en 929.8 para True Range >= 4.0
        closes[-1] = 929.8
        lows[-1] = 930.5

        # Barra 79 (última cerrada): Breakout con cuerpo dominante y TR >= 1.0 * ATR
        donchian_h = max(highs[:-1])
        breakout_open = donchian_h
        breakout_close = donchian_h + 2.5
        breakout_high = 934.0
        breakout_low = 931.0

        closes.append(breakout_close)
        opens.append(breakout_open)
        highs.append(breakout_high)
        lows.append(breakout_low)

        df["open"] = opens
        df["high"] = highs
        df["low"] = lows
        df["close"] = closes
        df["atr_14"] = atr_val
        df["rsi_14"] = 55.0
        df["adx_14"] = 15.0

    elif tipo == "tendencia_pullback_buy":
        # Tendencia alcista clara con EMAs ordenadas
        closes = [base_price + i * 0.8 for i in range(bar_count)]
        opens = [c - 0.4 for c in closes]
        highs = [c + 0.6 for c in closes]
        lows = [c - 0.6 for c in closes]

        # En la última barra cerrada, el precio hace pullback a EMA20 y rechaza
        ema_20_val = base_price + (bar_count - 1) * 0.8 - 2.0
        lows[-1] = ema_20_val - 0.5  # perfora EMA20
        closes[-1] = ema_20_val + 1.5 # cierra arriba
        opens[-1] = ema_20_val - 0.2
        highs[-1] = closes[-1] + 0.8

        df["open"] = opens
        df["high"] = highs
        df["low"] = lows
        df["close"] = closes
        df["atr_14"] = atr_val
        df["rsi_14"] = 55.0
        df["adx_14"] = 28.0

    elif tipo == "rango_meanrev_buy":
        # Rango lateral puro alrededor de base_price
        closes = [base_price + 4.0 * math.sin(i * 0.4) for i in range(bar_count)]
        opens = [c - 0.3 for c in closes]
        highs = [c + 0.5 for c in closes]
        lows = [c - 0.5 for c in closes]

        # Penúltima barra fuera de banda inferior, última reingresa
        closes[-2] = base_price - 8.0
        lows[-2] = base_price - 9.0
        closes[-1] = base_price - 6.0  # reingresa dentro
        opens[-1] = base_price - 8.0
        highs[-1] = base_price - 5.5

        df["open"] = opens
        df["high"] = highs
        df["low"] = lows
        df["close"] = closes
        df["atr_14"] = atr_val
        # ADX conocido < 20 y RSI en sobreventa (< 35)
        df["adx_14"] = 12.0
        df["rsi_14"] = 50.0
        df.loc[df.index[-2:], "rsi_14"] = 30.0

    elif tipo == "plana_sin_trigger":
        # Serie completamente plana en rango estrecho, sin romper Donchian ni pullback
        closes = [base_price for _ in range(bar_count)]
        opens = [base_price for _ in range(bar_count)]
        highs = [base_price + 0.5 for _ in range(bar_count)]
        lows = [base_price - 0.5 for _ in range(bar_count)]

        df["open"] = opens
        df["high"] = highs
        df["low"] = lows
        df["close"] = closes
        df["atr_14"] = atr_val
        df["rsi_14"] = 50.0
        df["adx_14"] = 15.0

    else:
        closes = [base_price + math.sin(i) for i in range(bar_count)]
        opens = closes
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        df["open"] = opens
        df["high"] = highs
        df["low"] = lows
        df["close"] = closes
        df["atr_14"] = atr_val
        df["rsi_14"] = 55.0
        df["adx_14"] = 20.0

    return df


# ==============================================================================
# TESTS REQUERIDOS JUGADA 2 & 2.1
# ==============================================================================

def test_no_h1_series_blocked(config_playbook):
    """1. Sin serie H1 -> status BLOCKED, block_reason NO_H1_SERIES, lista READY vacía."""
    bias_fixture = {
        "regimen_macro_global": {"codigo": "R2_GOLDILOCKS_EXPANSION", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": 2.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": -1.2,
                "sesgo_etiqueta": "BAJISTA USD",
                "setups_permitidos": ["PULLBACK_SHORT_EMA20", "BREAKDOWN_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 930.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    assert "USDCLP" in tickets
    ticket = tickets["USDCLP"]
    assert ticket.status == "BLOCKED"
    assert ticket.block_reason == "NO_H1_SERIES"


def test_breakout_adc_buy_ready(config_playbook):
    """2. Breakout sintético + permisos Donchian + sesgo > 0 -> 1 ticket READY con R:R >= 1.0."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R4_RECESION_VUELO_CALIDAD", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": -3.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 1.2,
                "sesgo_etiqueta": "ALCISTA USD",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1", "PULLBACK_EMA20_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 940.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]

    assert ticket.status == "READY"
    assert ticket.setup == "BREAKOUT_ADC"
    assert ticket.side == "BUY"
    assert ticket.entry_type == "BUY_STOP"
    assert ticket.entry_price > 930.0
    assert ticket.stop_loss is not None
    assert ticket.stop_loss < ticket.entry_price
    assert ticket.take_profit_1 is not None
    assert ticket.take_profit_1 > ticket.entry_price
    assert ticket.rr_to_tp1 >= 1.0
    assert ticket.confirm_ok is True


def test_breakout_vetoed_by_prohibited(config_playbook):
    """3. Mismo breakout pero con el setup prohibido en el FSM -> 0 READY (status WAIT)."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R4_RECESION_VUELO_CALIDAD", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": -3.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 1.2,
                "sesgo_etiqueta": "ALCISTA USD",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": ["BREAKOUT_DONCHIAN_H1", "BREAKOUT_ADC"],  # Veto explícito
                "parametros_riesgo": {"precio_spot": 940.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]
    assert ticket.status != "READY"
    assert ticket.status in ["WAIT", "BLOCKED"]


def test_usdclp_buy_requires_positive_bias_score(config_playbook):
    """4. Ticket USDCLP BUY solo nace si sesgo_score > 0 en el bias fixture."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R2_GOLDILOCKS_EXPANSION", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": 2.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": -1.2,  # Sesgo bajista
                "sesgo_etiqueta": "BAJISTA USD",
                "setups_permitidos": ["PULLBACK_SHORT_EMA20", "BREAKDOWN_DONCHIAN_H1"],
                "setups_prohibidos": ["BREAKOUT_CHASE_LONG"],
                "parametros_riesgo": {"precio_spot": 930.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]
    if ticket.status == "READY":
        assert ticket.side == "SELL"
    else:
        assert ticket.status in ["WAIT", "BLOCKED"]


def test_missing_atr_no_ticket(config_playbook):
    """5. ATR None en bias -> status BLOCKED / MISSING_ATR, 0 tickets READY."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R4_RECESION_VUELO_CALIDAD", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": -3.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 1.2,
                "sesgo_etiqueta": "ALCISTA USD",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 940.0, "atr_h1": None, "distancia_sl_h1_puntos": None}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]
    assert ticket.status == "BLOCKED"
    assert ticket.block_reason == "MISSING_ATR"


def test_meanrev_r0_tp1_middle_bb_not_1_5_atr(config_playbook):
    """6. MEANREV en R0 debe emitir un ticket READY incondicional, con TP1 en media BB y TP2 en None."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="rango_meanrev_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": 0.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 0.0,
                "sesgo_etiqueta": "NEUTRAL / RANGO (S1 - R1)",
                "setups_permitidos": ["FADE_SUPPORT_RESISTANCE_H1", "MEAN_REVERSION_RSI_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 930.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]

    assert ticket.status == "READY"
    assert ticket.setup == "MEANREV_R0"
    assert ticket.side == "BUY"
    assert ticket.entry_type == "BUY_LIMIT"
    assert ticket.take_profit_2 is None
    assert ticket.take_profit_1 is not None
    # TP1 no debe ser exactamente entry + 1.5 * ATR (6.0 pts)
    assert abs((ticket.take_profit_1 - ticket.entry_price) - (1.5 * 4.0)) > 0.1


def test_dow_cross_confirmation_fail_blocks_ready(config_playbook):
    """8. Si la firma cruzada Dow es False, confirm_ok es False y el ticket no puede ser READY."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    # US100 en compra pero régimen es R3 (veto duro por Dow)
    bias_fixture = {
        "regimen_macro_global": {"codigo": "R3_ESTANFLACION_SHOCK", "confirmado_por_historesis": True},
        "metricas_clave": {"dgs10": 4.80},
        "activos": {
            "US100": {
                "nombre": "Nasdaq 100",
                "sesgo_score": 0.8,
                "sesgo_etiqueta": "ALCISTA",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 29000.0, "atr_h1": 100.0, "distancia_sl_h1_puntos": 150.0}
            }
        }
    }
    series_dict = {"US100": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["US100"]
    assert ticket.confirm_ok is False
    assert ticket.status != "READY"


def test_unconfirmed_regime_blocks_tickets(config_playbook):
    """Si el régimen no está confirmado por histéresis, ningún ticket puede ser READY."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=930.0, atr_val=4.0)

    bias_fixture = {
        "regimen_macro_global": {"codigo": "R4_RECESION_VUELO_CALIDAD", "confirmado_por_historesis": False},
        "metricas_clave": {"cobre_variacion_5d_pct": -3.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 1.2,
                "sesgo_etiqueta": "ALCISTA USD",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 940.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]
    assert ticket.status == "BLOCKED"
    assert ticket.block_reason == "UNCONFIRMED_REGIME"


def test_us100_missing_dgs10_dow_fails(config_playbook):
    """Jugada 2.1 A: Si métricas no contiene dgs10 (None), la firma Dow de US100 falla (confirm_ok=False) y status != READY."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="compresion_breakout_buy", base_price=29000.0, atr_val=100.0)
    bias_fixture = {
        "regimen_macro_global": {"codigo": "R2_GOLDILOCKS_EXPANSION", "confirmado_por_historesis": True},
        "metricas_clave": {"dgs10": None},  # Sin dgs10 en métricas
        "activos": {
            "US100": {
                "nombre": "Nasdaq 100",
                "sesgo_score": 0.80,
                "sesgo_etiqueta": "ALCISTA / EXPANSION",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 29000.0, "atr_h1": 100.0, "distancia_sl_h1_puntos": 150.0}
            }
        }
    }
    series_dict = {"US100": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["US100"]
    assert ticket.confirm_ok is False
    assert ticket.status != "READY"


def test_armed_no_entry_prices(config_playbook):
    """Jugada 2.1 C: Si el setup está armado pero no hay trigger activo, ARMED tiene entry_price, SL y TP en None."""
    df_h1 = crear_serie_h1_sintetica(bar_count=80, tipo="plana_sin_trigger", base_price=930.0, atr_val=4.0)
    bias_fixture = {
        "regimen_macro_global": {"codigo": "R4_RECESION_VUELO_CALIDAD", "confirmado_por_historesis": True},
        "metricas_clave": {"cobre_variacion_5d_pct": -3.0, "dgs10": 4.60},
        "activos": {
            "USDCLP": {
                "nombre": "Dólar / Peso Chileno",
                "sesgo_score": 1.2,
                "sesgo_etiqueta": "ALCISTA USD",
                "setups_permitidos": ["BREAKOUT_DONCHIAN_H1"],
                "setups_prohibidos": [],
                "parametros_riesgo": {"precio_spot": 940.0, "atr_h1": 4.0, "distancia_sl_h1_puntos": 6.0}
            }
        }
    }
    series_dict = {"USDCLP": df_h1}
    tickets = generar_tickets(bias_fixture, series_dict, config_playbook)
    ticket = tickets["USDCLP"]
    assert ticket.status == "ARMED"
    assert ticket.block_reason == "TRIGGER_PENDING"
    assert ticket.entry_price is None
    assert ticket.entry_type is None
    assert ticket.stop_loss is None
    assert ticket.take_profit_1 is None
    assert ticket.take_profit_2 is None
    assert ticket.rr_to_tp1 is None
