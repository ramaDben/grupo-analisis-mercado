#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_macro_bias_engine.py
Suite de pruebas automatizadas para el Motor de Sesgo Cuantitativo Intermercado (Playbook V2).
Valida determinismo, precedencia de estados R0-R4, alias de 10Y, petróleo con signo,
histéresis anti-parpadeo 2D, sesgo USDCLP por régimen y eliminación de ATR sintético.
"""

import json
import math
import pytest
from datetime import datetime, timezone
from pathlib import Path

from scripts.macro_bias_engine import (
    cargar_config,
    calcular_hash_config,
    evaluar_regimen_candidato,
    calcular_confianza,
    evaluar_activos,
    CONFIG_PATH
)

try:
    from scripts.macro_bias_engine import aplicar_histeresis
except ImportError:
    aplicar_histeresis = None


@pytest.fixture
def config_playbook():
    return cargar_config()


def test_determinismo_hash_config(config_playbook):
    """Verifica que el hash de configuración sea determinista y no nulo."""
    hash_1 = calcular_hash_config(CONFIG_PATH)
    hash_2 = calcular_hash_config(CONFIG_PATH)
    assert hash_1 == hash_2
    assert len(hash_1) == 16
    assert hash_1 != "CONFIG_NOT_FOUND"


def test_conmutacion_precedencia_r3_estanflacion(config_playbook):
    """Valida que un shock simultáneo en petróleo (rally) y tasas active con máxima prioridad R3."""
    deltas = {
        "oil_signed_pct_5d": 4.2,       # Rally > 3.5%
        "oil_max_pct_5d": 4.2,          # > 3.5% umbral R3
        "us10y_diff_5d": 0.12,          # +12 bps > 10 bps umbral
        "tips10y_diff_5d": 0.10,
        "breakeven_diff_5d": 0.14,      # También cumple R1, pero R3 tiene precedencia
        "copper_pct_5d": -1.0,
        "spread_2s10s_actual": 0.30
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R3_ESTANFLACION_SHOCK"
    assert "Estanflación" in nombre
    assert es_extremo is False


def test_conmutacion_r1_shock_inflacionario(config_playbook):
    """Valida activación de R1 cuando sube breakeven y se aplana la curva sin shock petrolero."""
    deltas = {
        "oil_signed_pct_5d": 1.0,
        "oil_max_pct_5d": 1.0,
        "us10y_diff_5d": 0.04,
        "tips10y_diff_5d": -0.02,
        "breakeven_diff_5d": 0.12,      # +12 bps > 10 bps umbral R1
        "copper_pct_5d": 0.5,
        "spread_2s10s_actual": 0.15     # < 0.20% curva plana
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R1_SHOCK_INFLACIONARIO"


def test_conmutacion_r4_recesion_curva_invertida(config_playbook):
    """Valida activación de R4 cuando la curva se invierte y el cobre colapsa."""
    deltas = {
        "oil_signed_pct_5d": -2.0,
        "oil_max_pct_5d": 2.0,
        "us10y_diff_5d": -0.08,
        "tips10y_diff_5d": -0.05,
        "breakeven_diff_5d": -0.02,
        "copper_pct_5d": -3.0,          # < -2.5% umbral cobre recesión
        "spread_2s10s_actual": -0.10    # < 0 curva invertida
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R4_RECESION_VUELO_CALIDAD"


def test_conmutacion_r2_goldilocks_expansion(config_playbook):
    """Valida activación de R2 cuando el cobre sube con tasas del Tesoro estables."""
    deltas = {
        "oil_signed_pct_5d": 0.5,
        "oil_max_pct_5d": 0.5,
        "us10y_diff_5d": 0.02,          # 2 bps <= 6 bps estable
        "tips10y_diff_5d": 0.0,
        "breakeven_diff_5d": 0.02,
        "copper_pct_5d": 2.2,           # > 1.5% expansión
        "spread_2s10s_actual": 0.40
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R2_GOLDILOCKS_EXPANSION"


def test_shock_extremo_override_inmediato(config_playbook):
    """Valida que un shock > 150% del umbral (ej. petróleo +6.0%) active el override inmediato."""
    deltas = {
        "oil_signed_pct_5d": 6.0,
        "oil_max_pct_5d": 6.0,          # > 5.25% umbral extremo
        "us10y_diff_5d": 0.16,          # > 15 bps extremo
        "tips10y_diff_5d": 0.14,
        "copper_pct_5d": 0.0,
        "spread_2s10s_actual": 0.40
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R3_ESTANFLACION_SHOCK"
    assert es_extremo is True


# ==============================================================================
# TESTS PRD: BUGS 1 A 6
# ==============================================================================

def test_10y_key_alias(config_playbook):
    """Bug 1: Valida que si se pasa solo dgs10_diff_5d con +12 bps y cobre +2.0%,
    NO califique como Goldilocks (tasas estables exige |Δ10Y| <= 6 bps)."""
    deltas = {
        "copper_pct_5d": 2.0,
        "dgs10_diff_5d": 0.12,  # +12 bps > 6 bps
        "spread_2s10s_actual": 0.40
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo != "R2_GOLDILOCKS_EXPANSION"
    assert codigo == "R0_CALMA_RANGO"


def test_goldilocks(config_playbook):
    """Bug 1: Valida que con cobre +2.0% y tasas estables vía dgs10_diff_5d (+3 bps), califique como R2."""
    deltas = {
        "copper_pct_5d": 2.0,
        "dgs10_diff_5d": 0.03,  # 3 bps <= 6 bps
        "spread_2s10s_actual": 0.40
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R2_GOLDILOCKS_EXPANSION"


def test_oil_crash_not_r3(config_playbook):
    """Bug 2: Un crash de petróleo (-4.0%) con alza de tasas NO debe activar R3 (Estanflación)."""
    deltas = {
        "oil_signed_pct_5d": -4.0,
        "oil_max_pct_5d": 4.0,
        "us10y_diff_5d": 0.12,  # 12 bps
        "tips10y_diff_5d": 0.10,
        "spread_2s10s_actual": 0.30
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo != "R3_ESTANFLACION_SHOCK"


def test_oil_rally_r3(config_playbook):
    """Bug 2: Un rally de petróleo (+4.0%) con alza de tasas SÍ debe activar R3 (Estanflación)."""
    deltas = {
        "oil_signed_pct_5d": 4.0,
        "oil_max_pct_5d": 4.0,
        "us10y_diff_5d": 0.12,  # 12 bps
        "tips10y_diff_5d": 0.10,
        "spread_2s10s_actual": 0.30
    }
    codigo, nombre, es_extremo, desc = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo == "R3_ESTANFLACION_SHOCK"


def test_hysteresis_two_days(config_playbook):
    """Bug 3 / Amenaza C: Valida que la transición R0 -> R2 requiera 2 lecturas D1 consecutivas,
    manteniendo el régimen previo activo y confirmado mientras el nuevo está en observación."""
    from scripts.macro_bias_engine import aplicar_histeresis
    assert aplicar_histeresis is not None

    prev = {
        "codigo": "R0_CALMA_RANGO",
        "nombre": "Calma / Rango / Absorción",
        "lecturas_consecutivas": 2,
        "confirmado_por_historesis": True,
        "candidato_codigo": None,
        "candidato_lecturas": 0
    }

    # Día 1: Candidato R2 (no extremo) -> se mantiene R0 activo y confirmado, R2 en observación
    res_d1 = aplicar_histeresis(prev, "R2_GOLDILOCKS_EXPANSION", "Expansión Sólida / Goldilocks", False, "Cobre en alza", config_playbook)
    assert res_d1["codigo"] == "R0_CALMA_RANGO"
    assert res_d1["confirmado_por_historesis"] is True
    assert res_d1["candidato_codigo"] == "R2_GOLDILOCKS_EXPANSION"
    assert res_d1["candidato_lecturas"] == 1

    # Día 2: Candidato R2 nuevamente -> conmuta y confirma
    res_d2 = aplicar_histeresis(res_d1, "R2_GOLDILOCKS_EXPANSION", "Expansión Sólida / Goldilocks", False, "Cobre en alza", config_playbook)
    assert res_d2["codigo"] == "R2_GOLDILOCKS_EXPANSION"
    assert res_d2["confirmado_por_historesis"] is True
    assert res_d2["lecturas_consecutivas"] == 2
    assert res_d2["candidato_codigo"] is None
    assert res_d2["candidato_lecturas"] == 0


def test_extreme_override(config_playbook):
    """Bug 3: Valida que un shock extremo active el régimen inmediatamente en día 1."""
    from scripts.macro_bias_engine import aplicar_histeresis
    assert aplicar_histeresis is not None

    prev = {
        "codigo": "R0_CALMA_RANGO",
        "nombre": "Calma / Rango / Absorción",
        "lecturas_consecutivas": 2,
        "confirmado_por_historesis": True,
        "candidato_codigo": None,
        "candidato_lecturas": 0
    }
    res = aplicar_histeresis(prev, "R3_ESTANFLACION_SHOCK", "Estanflación Shock", True, "Shock extremo petróleo", config_playbook)
    assert res["codigo"] == "R3_ESTANFLACION_SHOCK"
    assert res["confirmado_por_historesis"] is True
    assert res["lecturas_consecutivas"] == 1
    assert res["candidato_codigo"] is None


def test_usdclp_r4_long(config_playbook):
    """Bug 4: En R4 o con Cobre cayendo (-3%), el sesgo de USDCLP debe ser largo dólar (>0)."""
    deltas = {
        "copper_spot": 4.10,
        "copper_pct_5d": -3.0,
        "tpm_chile": 4.50,
        "fed_funds": 3.63,
        "fwd_extranjeros": 4450.0,
        "tips_10y": 2.35,
        "breakeven_10y": 2.34,
        "dgs10": 4.65,
        "oil_max_pct_5d": 0.0,
        "oil_signed_pct_5d": 0.0
    }
    precios = {"activos": {"USDCLP": {"H1": {"close": 940.0, "atr_14": 5.0}, "D1": {"close": 940.0, "atr_20": 10.0}}}}
    res = evaluar_activos("R4_RECESION_VUELO_CALIDAD", deltas, precios, config_playbook)
    usdclp = res["USDCLP"]
    assert usdclp["sesgo_score"] > 0
    assert any("BREAKOUT" in s or "PULLBACK" in s for s in usdclp["setups_permitidos"])
    assert any("FADE" in s or "GRID" in s for s in usdclp["setups_prohibidos"])


def test_usdclp_r2_short(config_playbook):
    """Bug 4: En R2 o con Cobre subiendo (+2%), el sesgo de USDCLP debe ser corto dólar (<0)."""
    deltas = {
        "copper_spot": 4.60,
        "copper_pct_5d": 2.0,
        "tpm_chile": 4.50,
        "fed_funds": 3.63,
        "fwd_extranjeros": 4450.0,
        "tips_10y": 2.35,
        "breakeven_10y": 2.34,
        "dgs10": 4.65,
        "oil_max_pct_5d": 0.0,
        "oil_signed_pct_5d": 0.0
    }
    precios = {"activos": {"USDCLP": {"H1": {"close": 915.0, "atr_14": 5.0}, "D1": {"close": 915.0, "atr_20": 10.0}}}}
    res = evaluar_activos("R2_GOLDILOCKS_EXPANSION", deltas, precios, config_playbook)
    usdclp = res["USDCLP"]
    assert usdclp["sesgo_score"] < 0
    assert any("PULLBACK_SHORT" in s or "BREAKDOWN" in s for s in usdclp["setups_permitidos"])
    assert any("BREAKOUT_CHASE_LONG" in s for s in usdclp["setups_prohibidos"])


def test_missing_copper(config_playbook):
    """Bug 4: Si falta el cobre (None), no emitir sesgo USDCLP (DATOS_INCOMPLETOS y setups [])."""
    deltas = {
        "copper_spot": None,
        "copper_pct_5d": None,
        "tpm_chile": 4.50,
        "fed_funds": 3.63,
        "fwd_extranjeros": 4450.0,
        "tips_10y": 2.35,
        "breakeven_10y": 2.34,
        "dgs10": 4.65,
        "oil_max_pct_5d": 0.0,
        "oil_signed_pct_5d": 0.0
    }
    precios = {"activos": {"USDCLP": {"H1": {"close": 920.0, "atr_14": 5.0}, "D1": {"close": 920.0, "atr_20": 10.0}}}}
    res = evaluar_activos("R0_CALMA_RANGO", deltas, precios, config_playbook)
    usdclp = res["USDCLP"]
    assert usdclp["sesgo_etiqueta"] == "DATOS_INCOMPLETOS"
    assert usdclp["setups_permitidos"] == []


def test_no_synthetic_atr(config_playbook):
    """Bug 6: Si falta el ATR en MT5 (None o <= 0), distancia_sl y atr deben ser None, no inventados."""
    deltas = {
        "copper_spot": 4.50,
        "copper_pct_5d": 0.0,
        "tpm_chile": 4.50,
        "fed_funds": 3.63,
        "fwd_extranjeros": 4450.0,
        "tips_10y": 2.35,
        "breakeven_10y": 2.34,
        "dgs10": 4.65,
        "oil_max_pct_5d": 0.0,
        "oil_signed_pct_5d": 0.0
    }
    precios = {"activos": {"USDCLP": {"H1": {"close": 920.0, "atr_14": None}, "D1": {"close": 920.0, "atr_20": 0.0}}}}
    res = evaluar_activos("R0_CALMA_RANGO", deltas, precios, config_playbook)
    usdclp_riesgo = res["USDCLP"]["parametros_riesgo"]
    assert usdclp_riesgo["atr_h1"] is None
    assert usdclp_riesgo["distancia_sl_h1_puntos"] is None
    assert usdclp_riesgo["atr_d1"] is None
    assert usdclp_riesgo["distancia_sl_d1_puntos"] is None


def test_formula_auditable_confianza(config_playbook):
    """Valida matemáticamente la ponderación del índice de confianza."""
    ahora = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    drivers_test = [
        {"nombre": "DGS10", "fecha": "2026-08-20", "status": "OK", "cobertura": 1.0},
        {"nombre": "DFII10", "fecha": "2026-08-20", "status": "OK", "cobertura": 1.0},
        {"nombre": "T10YIE", "fecha": "2026-08-20", "status": "OK", "cobertura": 1.0},
        {"nombre": "TPM_CHILE", "fecha": "2026-08-20", "status": "OK", "cobertura": 1.0},
    ]
    conf_total, f_frescura, f_antiguedad, f_cobertura = calcular_confianza(
        drivers_test, config_playbook, ahora=ahora
    )
    assert f_frescura == 100.0
    assert f_cobertura == 100.0
    assert conf_total >= 70.0
    esperado = 100.0 * (0.40 * 1.0 + 0.35 * (f_antiguedad / 100.0) + 0.25 * 1.0)
    assert abs(conf_total - esperado) < 0.2


def test_evaluacion_parametros_riesgo_activos(config_playbook):
    """Valida que los multiplicadores de ATR y distancias SL se calculen con precisión."""
    deltas = {
        "copper_spot": 4.48,
        "copper_pct_5d": 1.0,
        "tpm_chile": 4.50,
        "fed_funds": 3.63,
        "fwd_extranjeros": 4450.0,
        "tips_10y": 2.35,
        "breakeven_10y": 2.34,
        "dgs10": 4.65,
        "oil_max_pct_5d": 1.0,
        "oil_signed_pct_5d": 1.0
    }
    precios_dummy = {
        "activos": {
            "USDCLP": {
                "H1": {"close": 920.0, "atr_14": 4.0},
                "D1": {"close": 920.0, "atr_20": 8.0}
            },
            "XAUUSD": {
                "H1": {"close": 4500.0, "atr_14": 20.0},
                "D1": {"close": 4500.0, "atr_20": 40.0}
            },
            "WTI": {"H1": {"close": 85.0, "atr_14": 1.0}, "D1": {"close": 85.0, "atr_20": 2.0}},
            "BRENT": {"H1": {"close": 92.0, "atr_14": 1.2}, "D1": {"close": 92.0, "atr_20": 2.2}},
            "US100": {"H1": {"close": 29000.0, "atr_14": 100.0}, "D1": {"close": 29000.0, "atr_20": 250.0}}
        }
    }
    res = evaluar_activos("R0_CALMA_RANGO", deltas, precios_dummy, config_playbook)
    assert "USDCLP" in res
    assert res["USDCLP"]["parametros_riesgo"]["distancia_sl_h1_puntos"] == 6.0  # 1.5 * 4.0
    assert res["USDCLP"]["parametros_riesgo"]["distancia_sl_d1_puntos"] == 20.0  # 2.5 * 8.0

    assert "XAUUSD" in res
    assert res["XAUUSD"]["parametros_riesgo"]["distancia_sl_h1_puntos"] == 30.0  # 1.5 * 20.0
    assert res["XAUUSD"]["parametros_riesgo"]["trailing_stop_mult_atr"] == 3.0


# ==============================================================================
# TESTS P0.1: CUATRO AMENAZAS LÓGICAS (A, B, C, D)
# ==============================================================================

def test_usdclp_r3_no_lo_pisa_el_cobre(config_playbook):
    """Amenaza A: En R3 (Estanflación), un rally en Cobre (+2%) NO debe generar sesgo bajista en USDCLP."""
    deltas = {
        "copper_spot": 4.70,
        "copper_pct_5d": 2.0,  # parecería Goldilocks
        "oil_signed_pct_5d": 4.0,
        "dgs10": 4.80,
    }
    precios = {"activos": {"USDCLP": {"H1": {"close": 940.0, "atr_14": 5.0}, "D1": {"close": 940.0, "atr_20": 10.0}}}}
    res = evaluar_activos("R3_ESTANFLACION_SHOCK", deltas, precios, config_playbook)
    assert res["USDCLP"]["sesgo_score"] > 0
    assert "FADE_SUPPORT_RESISTANCE_M15" not in res["USDCLP"]["setups_permitidos"]


def test_oil_max_unsigned_no_es_r3(config_playbook):
    """Amenaza B: Si deltas solo incluye oil_max_pct_5d (unsigned) y no oil_signed_pct_5d, NO debe disparar R3."""
    deltas = {"oil_max_pct_5d": 4.0, "us10y_diff_5d": 0.12, "spread_2s10s_actual": 0.30}
    codigo, *_ = evaluar_regimen_candidato(deltas, config_playbook)
    assert codigo != "R3_ESTANFLACION_SHOCK"


def test_histeresis_no_desconfirma_regimen_activo_estable(config_playbook):
    """Amenaza C: Si R2 lleva 10 lecturas confirmadas y aparece un candidato R3 no extremo,
    el régimen activo sigue siendo R2 confirmado True, y R3 queda en observación (1/2)."""
    from scripts.macro_bias_engine import aplicar_histeresis
    prev = {
        "codigo": "R2_GOLDILOCKS_EXPANSION",
        "nombre": "Expansión Sólida / Goldilocks",
        "lecturas_consecutivas": 10,
        "confirmado_por_historesis": True,
        "candidato_codigo": None,
        "candidato_lecturas": 0
    }
    res = aplicar_histeresis(prev, "R3_ESTANFLACION_SHOCK", "Estanflación Shock", False, "Petróleo al alza", config_playbook)
    assert res["codigo"] == "R2_GOLDILOCKS_EXPANSION"
    assert res["confirmado_por_historesis"] is True
    assert res["candidato_codigo"] == "R3_ESTANFLACION_SHOCK"
    assert res["candidato_lecturas"] == 1
    assert res["lecturas_consecutivas"] == 10


def test_us100_missing_dgs10_no_default(config_playbook):
    """Amenaza D: Si falta dgs10 (None), US100 no debe inventar 4.65 ni tener sesgo alcista por default."""
    deltas = {
        "dgs10": None,
        "copper_spot": 4.50,
        "copper_pct_5d": 0.0,
        "oil_signed_pct_5d": 0.0
    }
    precios = {"activos": {"US100": {"H1": {"close": 29000.0, "atr_14": 100.0}, "D1": {"close": 29000.0, "atr_20": 250.0}}}}
    res = evaluar_activos("R0_CALMA_RANGO", deltas, precios, config_playbook)
    us100 = res["US100"]
    assert us100["sesgo_etiqueta"] == "DATOS_INCOMPLETOS"
    assert us100["setups_permitidos"] == []


def test_wti_missing_oil_signed_no_shock(config_playbook):
    """Peón suelto: Si oil_signed_pct_5d es None, WTI no debe crashear y no debe ser ALCISTA POR SHOCK en R0."""
    deltas = {
        "oil_signed_pct_5d": None,
        "oil_max_pct_5d": 4.0,
        "dgs10": 4.65,
        "copper_spot": 4.50,
        "copper_pct_5d": 0.0
    }
    precios = {"activos": {"WTI": {"H1": {"close": 85.0, "atr_14": 1.0}, "D1": {"close": 85.0, "atr_20": 2.0}}}}
    res = evaluar_activos("R0_CALMA_RANGO", deltas, precios, config_playbook)
    assert res["WTI"]["sesgo_score"] == 0.0
    assert res["WTI"]["sesgo_etiqueta"] != "ALCISTA POR SHOCK"


