"""Estadística del plan de escenarios: desenlaces, eventos sin mirar el futuro y línea base."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import estadistica as est  # noqa: E402


def serie(cierres, rango=1.0):
    cierres = [float(c) for c in cierres]
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=len(cierres), freq="h"),
        "open": cierres, "close": cierres,
        "high": [c + rango / 2 for c in cierres], "low": [c - rango / 2 for c in cierres],
    })


def test_desenlace_recorrido():
    df = serie([100] * 61 + [100 + k for k in range(1, 25)])
    assert est.desenlace(df, 60, alcista=True) == "recorrido"


def test_desenlace_invalidacion():
    df = serie([100] * 61 + [100 - 2 * k for k in range(1, 25)])
    assert est.desenlace(df, 60, alcista=True) == "invalidacion"


def test_empate_en_la_misma_vela_es_invalidacion():
    df = serie([100] * 85)
    df.loc[61, "high"], df.loc[61, "low"] = 200.0, 0.0
    assert est.desenlace(df, 60, alcista=True) == "invalidacion"


def test_sin_definicion():
    assert est.desenlace(serie([100] * 85), 60, alcista=True) == "sin_definicion"


def test_bajista_es_espejo():
    df = serie([100] * 61 + [100 - k for k in range(1, 25)])
    assert est.desenlace(df, 60, alcista=False) == "recorrido"


def test_no_mira_el_futuro():
    rng = np.random.default_rng(1)
    base = list(100 + rng.standard_normal(900).cumsum())
    a = est.eventos(serie(base), 2, alcista=True)
    cambiado = base[:600] + [b * 3 for b in base[600:]]
    b = est.eventos(serie(cambiado), 2, alcista=True)
    assert [i for i in a if i < 600] == [i for i in b if i < 600]


def test_detecta_rupturas_en_una_serie_con_tendencia():
    rng = np.random.default_rng(7)
    base = list(100 + (rng.standard_normal(1200) + 0.05).cumsum())
    assert est.eventos(serie(base), 2, alcista=True)


def test_linea_base_solo_cuenta_horas_con_la_misma_tendencia():
    # 400 velas cayendo y luego 400 subiendo: en una compra, la base no puede
    # incluir las horas bajo la EMA 50, donde comprar es ir contra la tendencia.
    df = serie([500 - k * 0.5 for k in range(400)] + [300 + k * 0.5 for k in range(400)])
    ind = est.indicadores(df)
    limite = len(df) - est.HORIZONTE
    a_favor = [i for i in range(est.VENTANA, limite) if df["close"].iat[i] > ind["ema50"].iat[i]]
    esperado = round(100 * sum(est.desenlace(df, i, True, ind) == "recorrido" for i in a_favor) / len(a_favor))
    assert est.medir(df, 2, alcista=True).pct_base == esperado


def test_muestra_insuficiente():
    # Pendiente suave: hay horas sobre la EMA 50 para la base y casi ninguna ruptura.
    r = est.medir(serie([100 + k * 0.01 for k in range(400)]), 2, alcista=True)
    assert r.casos < est.MUESTRA_MINIMA and r.pct_condicion is None
    assert r.pct_base is not None


def test_serie_corta_no_revienta():
    r = est.medir(serie([100] * 50), 2, alcista=True)
    assert r.casos == 0 and r.pct_base is None and r.pct_condicion is None


def test_activacion_reciente_encuentra_la_ultima_ruptura():
    rng = np.random.default_rng(7)
    base = list(100 + (rng.standard_normal(1200) + 0.05).cumsum())
    df = serie(base)
    todos = est.eventos(df, 2, alcista=True)
    ultimo = todos[-1]
    corte = df.iloc[: ultimo + 3].reset_index(drop=True)  # 2 velas despues de la ruptura
    nivel = est.activacion_reciente(corte, 2, alcista=True)
    assert nivel is not None
    assert est.activacion_reciente(serie([100 + k * 0.01 for k in range(400)]), 2, alcista=True) is None


def test_el_periodo_parte_donde_se_puede_medir():
    df = serie([100 + k * 0.01 for k in range(400)])
    assert est.medir(df, 2, alcista=True).desde == str(df["time"].iat[est.VENTANA])[:10]
