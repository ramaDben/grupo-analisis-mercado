"""Contrato del modelo de dirección de cuatro ejes (fase 1, en sombra).

Todo con dicts construidos a mano con los nombres reales de `analizar_activo`.
Spec: docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import direccion_gi as dg  # noqa: E402


def h1_base(**cambios) -> dict:
    """H1 alcista y fuerte: precio sobre la EMA 50, ADX 30, p = 0,8."""
    h1 = {
        "ticker": "TEST", "timeframe": "H1", "price": 108.0,
        "ema_50": 100.0, "atr_14": 2.0, "adx_14": 30.0,
        "donchian_50_high": 110.0, "donchian_50_low": 100.0,
    }
    h1.update(cambios)
    return h1


def d1_base(**cambios) -> dict:
    """D1 alcista: precio > EMA 50 > EMA 100, con 30 % del ATR consumido."""
    d1 = {
        "ticker": "TEST", "timeframe": "D1", "price": 108.0,
        "ema_50": 90.0, "ema_100": 80.0, "atr_14": 10.0,
        "rango_hoy": 3.0, "fecha_barra": "2026-09-28",
    }
    d1.update(cambios)
    return d1


def test_los_umbrales_salen_del_config():
    u = dg.umbrales()
    assert u == {
        "adx_rango": 20.0, "adx_fuerza": 25.0,
        "p_rango_min": 0.3, "p_rango_max": 0.7,
        "p_confirma_alcista": 0.6, "p_confirma_bajista": 0.4,
        "histeresis_atr": 0.25, "consumo_sin_recorrido": 0.70,
    }


def test_posicion_canal_dentro_y_en_quiebre():
    assert dg.posicion_canal(h1_base(price=105.0)) == pytest.approx(0.5)
    assert dg.posicion_canal(h1_base(price=112.0)) == pytest.approx(1.2)
    assert dg.posicion_canal(h1_base(price=98.0)) == pytest.approx(-0.2)


def test_posicion_canal_sin_ancho_no_se_calcula():
    assert dg.posicion_canal(h1_base(donchian_50_high=100.0, donchian_50_low=100.0)) is None
    assert dg.posicion_canal(h1_base(donchian_50_high=None)) is None


@pytest.mark.parametrize("precio, e50, e100, esperado", [
    (108.0, 90.0, 80.0, "ALCISTA"),
    (70.0, 75.0, 80.0, "BAJISTA"),
    (95.0, 90.0, 92.0, "TRANSICION"),   # precio sobre la 50, pero la 50 bajo la 100
    (85.0, 90.0, 80.0, "TRANSICION"),   # precio bajo la 50, con la 50 sobre la 100
    (90.0, 90.0, 80.0, "TRANSICION"),   # empate exacto con la 50
])
def test_eje_fondo(precio, e50, e100, esperado):
    assert dg.eje_fondo(d1_base(price=precio, ema_50=e50, ema_100=e100)) == esperado


def test_eje_fondo_con_campo_faltante_es_none():
    assert dg.eje_fondo(d1_base(ema_100=None)) is None


def test_eje_dia_sin_previa_y_empate_alcista():
    assert dg.eje_dia(h1_base(price=101.0)) == "ALCISTA"
    assert dg.eje_dia(h1_base(price=99.0)) == "BAJISTA"
    assert dg.eje_dia(h1_base(price=100.0)) == "ALCISTA"


@pytest.mark.parametrize("precio, previa, esperado", [
    (99.6, "ALCISTA", "ALCISTA"),    # cruzó 0,4 < 0,5 (0,25 x ATR 2): no alcanza
    (99.5, "ALCISTA", "ALCISTA"),    # exactamente en el borde: "más de" no se cumple
    (99.49, "ALCISTA", "BAJISTA"),
    (100.4, "BAJISTA", "BAJISTA"),
    (100.5, "BAJISTA", "BAJISTA"),
    (100.51, "BAJISTA", "ALCISTA"),
])
def test_eje_dia_con_histeresis(precio, previa, esperado):
    assert dg.eje_dia(h1_base(price=precio), previa) == esperado


def test_eje_dia_sin_precio_o_ema_lanza():
    with pytest.raises(ValueError):
        dg.eje_dia(h1_base(ema_50=None))


def test_canal_confirma_por_lado():
    assert dg.canal_confirma("ALCISTA", 0.6) is True
    assert dg.canal_confirma("ALCISTA", 0.59) is False
    assert dg.canal_confirma("ALCISTA", 1.3) is True     # quiebre al alza
    assert dg.canal_confirma("BAJISTA", 0.4) is True
    assert dg.canal_confirma("BAJISTA", 0.41) is False
    assert dg.canal_confirma("BAJISTA", -0.2) is True    # quiebre a la baja


def test_consumo_diario_y_regla_de_fecha_barra():
    assert dg.consumo_diario(d1_base()) == pytest.approx(0.3)
    assert dg.consumo_diario(d1_base(), hoy="2026-09-28") == pytest.approx(0.3)
    # vela D1 de un día anterior: el mercado de hoy no ha consumido nada
    assert dg.consumo_diario(d1_base(fecha_barra="2026-09-25"), hoy="2026-09-28") == 0.0
    assert dg.consumo_diario(d1_base(rango_hoy=None)) is None
    assert dg.consumo_diario(d1_base(atr_14=0.0)) is None


def test_num_trata_nan_e_inf_como_faltantes():
    assert dg._num({"x": float("nan")}, "x") is None
    assert dg._num({"x": float("inf")}, "x") is None
    assert dg._num({"x": True}, "x") is None
    assert dg._num({"x": "3.5"}, "x") == 3.5
    assert dg._num({}, "x") is None
