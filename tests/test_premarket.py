#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_premarket.py
Suite de pruebas para la calculadora de lotaje multidivisa y el renderizador de briefings premarket.py.
"""

import pytest
from market_data_mcp.bias_reader import calcular_lote_riesgo
from scripts.premarket import render_briefing_activo


def test_calcular_lote_usdclp_multidivisa():
    """Valida la conversión de moneda para cuenta USD operando USDCLP (P&L en CLP)."""
    capital_usd = 25000.0
    riesgo_pct = 1.0       # $250 USD
    sl_puntos = 2.83       # 2.83 pesos
    spot = 921.60

    lotes, riesgo_usd, tick_val = calcular_lote_riesgo(capital_usd, riesgo_pct, sl_puntos, "USDCLP", spot)

    assert riesgo_usd == 250.0
    assert abs(tick_val - 108.51) < 0.1
    # 250 / (2.83 * 108.51) = 250 / 307.08 = 0.814 -> 0.81
    assert lotes == 0.81


def test_calcular_lote_xauusd_oro():
    """Valida el cálculo de lotaje para Oro Spot."""
    capital_usd = 10000.0
    riesgo_pct = 1.0       # $100 USD
    sl_puntos = 27.43      # $27.43 USD
    spot = 4519.50

    lotes, riesgo_usd, tick_val = calcular_lote_riesgo(capital_usd, riesgo_pct, sl_puntos, "XAUUSD", spot)

    assert riesgo_usd == 100.0
    assert tick_val == 100.0
    # 100 / (27.43 * 100) = 100 / 2743 = 0.036 -> 0.04
    assert lotes == 0.04


def test_calcular_lote_wti_and_us100():
    """Valida el cálculo de lotaje para Petróleo WTI y Nasdaq US100."""
    # WTI: $10,000 capital, 1% riesgo ($100), SL 0.99 pts, tick_val = 1,000 USD/pt
    lotes_wti, _, tick_wti = calcular_lote_riesgo(10000.0, 1.0, 0.99, "WTI", 86.20)
    assert tick_wti == 1000.0
    # 100 / (0.99 * 1000) = 100 / 990 = 0.101 -> 0.10
    assert lotes_wti == 0.10

    # US100: $20,000 capital, 1% riesgo ($200), SL 156.7 pts, tick_val = 20 USD/pt
    lotes_us100, _, tick_us100 = calcular_lote_riesgo(20000.0, 1.0, 156.7, "US100", 29317.0)
    assert tick_us100 == 20.0
    # 200 / (156.7 * 20) = 200 / 3134 = 0.063 -> 0.06
    assert lotes_us100 == 0.06


def test_render_briefing_activo():
    """Valida que el briefing en texto contenga todos los bloques requeridos."""
    activo_dummy = {
        "symbol_id": "USDCLP",
        "nombre": "Dólar / Peso Chileno",
        "tipo": "FX_EMERGENTE",
        "sesgo_score": 0.10,
        "sesgo_etiqueta": "NEUTRAL / RANGO",
        "parametros_riesgo": {
            "precio_spot": 921.60,
            "atr_h1": 1.89,
            "atr_d1": 7.21,
            "distancia_sl_h1_puntos": 2.83,
            "distancia_sl_d1_puntos": 18.03,
            "take_profit_tipo": "NIVEL_OPUESTO_CANAL",
            "trailing_stop_mult_atr": None
        },
        "setups_permitidos": ["FADE_SUPPORT_RESISTANCE_M15"],
        "setups_prohibidos": ["BREAKOUT_CHASE_LONG"],
        "justificacion_vectores": ["Cobre estable frena alzas"]
    }
    rendered = render_briefing_activo(activo_dummy, {}, {}, 25000.0, 1.0)
    assert "Dólar / Peso Chileno" in rendered
    assert "$921.60" in rendered
    assert "0.81 Lotes" in rendered
    assert "FADE_SUPPORT_RESISTANCE_M15" in rendered
    assert "BREAKOUT_CHASE_LONG" in rendered
    assert "Cobre estable frena alzas" in rendered


def test_el_factor_de_apalancamiento_reduce_el_lote():
    """Emitir el factor y no aplicarlo lo dejaría como la confianza del modelo:
    un número correcto que nadie lee.

    El Playbook §4 manda "apalancamiento reducido al 50 %" en el shock
    precautorio del crudo. Si el lote no cambia, la instrucción es decorativa.
    """
    # El lote se cuantiza a 2 decimales (paso del broker), así que se eligen
    # valores que dividen limpio: con SL de 0,5 pts en WTI el lote crudo es 0,50
    # y su mitad 0,25. Con 1,0 pt daría 0,125, que redondea a 0,12 y mezclaría
    # el efecto del factor con el de la cuantización.
    base, riesgo_base, _ = calcular_lote_riesgo(25000.0, 1.0, 0.5, "WTI", 90.0)
    mitad, riesgo_mitad, _ = calcular_lote_riesgo(
        25000.0, 1.0, 0.5, "WTI", 90.0, factor_apalancamiento=0.5
    )

    assert base == pytest.approx(0.50)
    assert mitad == pytest.approx(0.25)
    # El presupuesto de riesgo NO se escala: es el mismo, y el factor decide
    # cuánto de ese presupuesto se pone en juego.
    assert riesgo_mitad == riesgo_base


def test_el_factor_por_defecto_no_altera_el_lote():
    """La contraparte: sin factor explícito el resultado tiene que ser idéntico
    al de antes, o el cambio sería una regresión silenciosa en los otros cuatro
    activos."""
    sin, _, _ = calcular_lote_riesgo(25000.0, 1.0, 30.0, "XAUUSD", 4500.0)
    con_uno, _, _ = calcular_lote_riesgo(25000.0, 1.0, 30.0, "XAUUSD", 4500.0, factor_apalancamiento=1.0)

    assert sin == con_uno


def test_el_briefing_aplica_el_factor_que_trae_el_snapshot():
    """El contrato de orden: `premarket` tiene que leer el campo del snapshot,
    no asumir 1.0."""
    import inspect
    import sys
    from pathlib import Path as _P
    raiz = _P(__file__).resolve().parents[1]
    if str(raiz / "scripts") not in sys.path:
        sys.path.insert(0, str(raiz / "scripts"))
    import premarket

    fuente = inspect.getsource(premarket.render_briefing_activo)
    assert "factor_apalancamiento" in fuente, (
        "el briefing dimensiona sin mirar el factor: un shock precautorio saldría "
        "con lote completo"
    )
