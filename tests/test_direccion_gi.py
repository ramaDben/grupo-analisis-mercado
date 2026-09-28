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


import ast  # noqa: E402
import json  # noqa: E402
from itertools import product  # noqa: E402


# ── Una por rama ────────────────────────────────────────────────────────────
def test_rama_0_datos_incompletos_nombra_el_campo():
    lec = dg.leer_direccion(h1_base(adx_14=None), d1_base())
    assert lec.fase == "datos_incompletos"
    assert lec.direccion == "ALCISTA"          # la de H1
    assert lec.conviccion == "debil"
    assert "h1.adx_14" in lec.ejes["faltan"]


def test_rama_0_con_nan_y_con_d1_incompleto():
    lec = dg.leer_direccion(h1_base(adx_14=float("nan")), d1_base(ema_100=None))
    assert lec.fase == "datos_incompletos"
    assert set(lec.ejes["faltan"]) >= {"h1.adx_14", "d1.ema_100"}


def test_rama_0_canal_sin_ancho():
    lec = dg.leer_direccion(h1_base(donchian_50_high=100.0, donchian_50_low=100.0), d1_base())
    assert lec.fase == "datos_incompletos"
    assert "h1.donchian_50 sin ancho" in lec.ejes["faltan"]


def test_rama_1_rango():
    lec = dg.leer_direccion(h1_base(adx_14=15.0, price=105.0), d1_base())
    assert (lec.direccion, lec.conviccion, lec.fase) == ("LATERAL", None, "rango")
    assert lec.eje2 == "ALCISTA"                # el eje 2 nunca es LATERAL


def test_rama_2_fuerte_moderada_debil():
    fuerte = dg.leer_direccion(h1_base(), d1_base())
    assert (fuerte.direccion, fuerte.conviccion, fuerte.fase) == ("ALCISTA", "fuerte", "tendencia_alineada")
    sin_canal = dg.leer_direccion(h1_base(price=101.0), d1_base(price=101.0))  # p = 0,1 no confirma
    assert sin_canal.conviccion == "moderada"
    media = dg.leer_direccion(h1_base(adx_14=22.0), d1_base())
    assert media.conviccion == "moderada"
    debil = dg.leer_direccion(h1_base(adx_14=15.0), d1_base())  # p = 0,8: fuera de la zona media
    assert (debil.conviccion, debil.fase) == ("debil", "tendencia_alineada")


def test_rama_3a_correccion_con_fuerza_manda_el_dia():
    # D1 bajista, H1 alcista, ADX 30
    lec = dg.leer_direccion(h1_base(), d1_base(price=108.0, ema_50=115.0, ema_100=120.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("ALCISTA", "moderada", "correccion_con_fuerza")


def test_rama_3b_correccion_sin_fuerza_manda_el_fondo():
    lec = dg.leer_direccion(h1_base(adx_14=22.0), d1_base(price=108.0, ema_50=115.0, ema_100=120.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("BAJISTA", "debil", "correccion")
    assert "resistencia" in lec.motivo


def test_rama_4_sin_ancla():
    lec = dg.leer_direccion(h1_base(), d1_base(ema_50=90.0, ema_100=95.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("ALCISTA", "debil", "sin_ancla")


# ── Marca sin_recorrido ─────────────────────────────────────────────────────
def test_sin_recorrido_desde_0_70_y_con_fecha_barra():
    assert dg.leer_direccion(h1_base(), d1_base(rango_hoy=6.9)).sin_recorrido is False
    assert dg.leer_direccion(h1_base(), d1_base(rango_hoy=7.0)).sin_recorrido is True
    ayer = d1_base(rango_hoy=9.0, fecha_barra="2026-09-25")
    assert dg.leer_direccion(h1_base(), ayer, hoy="2026-09-28").sin_recorrido is False
    lec = dg.leer_direccion(h1_base(), d1_base(rango_hoy=8.0))
    assert lec.fase == "tendencia_alineada"     # no cambia dirección ni convicción
    assert lec.conviccion == "fuerte"


def test_sin_rango_hoy_no_marca_ni_degrada():
    lec = dg.leer_direccion(h1_base(), d1_base(rango_hoy=None))
    assert lec.sin_recorrido is False
    assert lec.fase == "tendencia_alineada"


# ── Bordes exactos ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("adx, esperado", [(19.99, "rango"), (20.0, "tendencia_alineada")])
def test_borde_adx_20(adx, esperado):
    assert dg.leer_direccion(h1_base(adx_14=adx, price=105.0), d1_base(price=105.0)).fase == esperado


@pytest.mark.parametrize("adx, conv", [(24.99, "moderada"), (25.0, "fuerte")])
def test_borde_adx_25_en_rama_2(adx, conv):
    assert dg.leer_direccion(h1_base(adx_14=adx), d1_base()).conviccion == conv


@pytest.mark.parametrize("adx, fase", [(24.99, "correccion"), (25.0, "correccion_con_fuerza")])
def test_borde_adx_25_en_rama_3(adx, fase):
    d1_bajista = d1_base(ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1_base(adx_14=adx), d1_bajista).fase == fase


@pytest.mark.parametrize("precio, fase", [
    (102.99, "tendencia_alineada"),   # p = 0,299
    (103.0, "rango"),                 # p = 0,3
    (107.0, "rango"),                 # p = 0,7
    (107.01, "tendencia_alineada"),   # p = 0,701
])
def test_bordes_p_rango(precio, fase):
    assert dg.leer_direccion(h1_base(adx_14=15.0, price=precio), d1_base(price=precio)).fase == fase


@pytest.mark.parametrize("precio, conv", [(106.0, "fuerte"), (105.99, "moderada")])
def test_borde_p_confirma_0_6(precio, conv):
    assert dg.leer_direccion(h1_base(price=precio), d1_base(price=precio)).conviccion == conv


def test_borde_p_confirma_0_4_bajista():
    # H1 bajo la EMA 50: la ubico en 110 para que el precio quede bajo ella
    h1 = h1_base(ema_50=110.0, price=104.0)          # p = 0,4
    d1 = d1_base(price=104.0, ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1, d1).conviccion == "fuerte"
    h1b = h1_base(ema_50=110.0, price=104.01)        # p = 0,401
    assert dg.leer_direccion(h1b, d1_base(price=104.01, ema_50=115.0, ema_100=120.0)).conviccion == "moderada"


def test_quiebres_confirman_su_lado():
    assert dg.leer_direccion(h1_base(price=112.0), d1_base(price=112.0)).conviccion == "fuerte"
    h1 = h1_base(ema_50=103.0, price=98.0)           # p = -0,2
    d1 = d1_base(price=98.0, ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1, d1).conviccion == "fuerte"


def test_histeresis_viaja_en_eje2():
    h1 = h1_base(price=99.6, adx_14=30.0)             # bajo la media, dentro de la banda
    lec = dg.leer_direccion(h1, d1_base(price=99.6), previa="ALCISTA")
    assert lec.eje2 == "ALCISTA"
    assert dg.leer_direccion(h1, d1_base(price=99.6)).eje2 == "BAJISTA"   # sin previa


def test_previa_invalida_lanza():
    with pytest.raises(ValueError):
        dg.leer_direccion(h1_base(), d1_base(), previa="LATERAL")


# ── Cobertura del árbol ─────────────────────────────────────────────────────
FONDOS = {
    "ALCISTA": dict(ema_50=90.0, ema_100=80.0),
    "BAJISTA": dict(ema_50=200.0, ema_100=210.0),
    "TRANSICION": dict(ema_50=90.0, ema_100=95.0),
}
DIAS = {"ALCISTA": 50.0, "BAJISTA": 200.0}          # ema_50 de H1 bajo o sobre el precio
ADXS = [19.99, 20.0, 24.99, 25.0]
PRECIOS = [102.99, 103.0, 105.0, 107.0, 107.01, 112.0, 98.0]   # p a los dos lados de cada umbral


def test_cobertura_seis_combinaciones_una_rama_cada_una():
    for (fondo, cfg_d1), (dia, e50_h1), adx, precio in product(FONDOS.items(), DIAS.items(), ADXS, PRECIOS):
        h1 = h1_base(price=precio, ema_50=e50_h1, adx_14=adx)
        d1 = d1_base(price=precio, **cfg_d1)
        lec = dg.leer_direccion(h1, d1)
        assert lec.ejes["fondo"] == fondo and lec.ejes["dia"] == dia
        p = lec.ejes["p"]
        if adx < 20 and 0.3 <= p <= 0.7:
            esperada = "rango"
        elif fondo == "TRANSICION":
            esperada = "sin_ancla"
        elif fondo == dia:
            esperada = "tendencia_alineada"
        else:
            esperada = "correccion_con_fuerza" if adx >= 25 else "correccion"
        assert lec.fase == esperada, (fondo, dia, adx, precio, lec)


# ── Contrato de config y motivo de cliente ──────────────────────────────────
def test_ningun_numero_del_arbol_esta_escrito_en_el_codigo():
    fuente = (RAIZ / "scripts" / "direccion_gi.py").read_text(encoding="utf-8")
    numeros = {
        n.value for n in ast.walk(ast.parse(fuente))
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
        and not isinstance(n.value, bool)
    }
    assert numeros <= {0, 1}, f"umbrales escritos a mano: {sorted(numeros - {0, 1})}"


def test_todo_umbral_tiene_valor_y_origen():
    datos = json.loads((RAIZ / "config" / "direccion.json").read_text(encoding="utf-8"))
    for bloque in ("umbrales", "medicion"):
        for clave, v in datos[bloque].items():
            if clave == "series":
                continue
            assert "valor" in v and str(v.get("origen", "")).strip(), clave


def test_ningun_motivo_lleva_guion_largo_ni_medio():
    for fondo, cfg_d1 in FONDOS.items():
        for dia, e50_h1 in DIAS.items():
            for adx in (15.0, 22.0, 30.0):
                for precio in (105.0, 112.0):
                    for rango in (3.0, 8.0):
                        lec = dg.leer_direccion(
                            h1_base(price=precio, ema_50=e50_h1, adx_14=adx),
                            d1_base(price=precio, rango_hoy=rango, **cfg_d1),
                        )
                        assert "—" not in lec.motivo and "–" not in lec.motivo, lec.motivo
                        assert lec.motivo.strip()
    lec = dg.leer_direccion(h1_base(adx_14=None), d1_base())
    assert "—" not in lec.motivo and "–" not in lec.motivo


def test_a_dict_es_serializable():
    json.dumps(dg.a_dict(dg.leer_direccion(h1_base(), d1_base())))
