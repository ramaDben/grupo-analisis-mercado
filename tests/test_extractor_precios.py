"""El ATR del extractor tiene que ser el mismo que el del MCP.

El repo tenía tres implementaciones del mismo `atr_14` y dos resultados: el MCP
suavizaba con Wilder (alpha=1/n) y el extractor con `ewm(span=n)`, que es
alpha=2/(n+1). Sobre la serie H1 real de USDCLP la brecha era de -7,4 %, y ese
número no es cosmético: el Playbook define el stop como 1,5 x ATR_14(H1) y el
lote como (Capital x R%) / (Distancia SL x Valor punto). Dos ATR son dos lotes
para la misma operación.

El tercer test es el que importa a futuro: compara las dos implementaciones
sobre la misma serie. Arreglar el extractor sin él deja la puerta abierta a que
alguien vuelva a separarlas sin que nada avise.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from extractor_precios import calcular_indicadores  # noqa: E402
from market_data_mcp import mt5_client  # noqa: E402


def _ohlc(n: int = 300) -> pd.DataFrame:
    """OHLC sintético con deriva y oscilación, suficiente para estabilizar el ATR."""
    x = np.linspace(0, 8 * np.pi, n)
    base = 100 + 0.05 * np.arange(n) + 3 * np.sin(x)
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=n, freq="h"),
        "open": base,
        "high": base + 0.5 + 0.2 * np.abs(np.cos(x)),
        "low": base - 0.5 - 0.2 * np.abs(np.cos(x)),
        "close": base,
        "tick_volume": np.arange(n) + 1,
    })


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


@pytest.mark.parametrize("periodo, columna", [(14, "atr_14"), (20, "atr_20")])
def test_atr_del_extractor_usa_suavizado_wilder(periodo, columna):
    """Wilder es alpha=1/n, no span=n. La diferencia entre ambos no es de redondeo:
    para n=14, alpha vale 0,0714 contra 0,1333, casi el doble de peso a la última barra."""
    df = _ohlc()
    res = calcular_indicadores(df)

    esperado = _true_range(df).ewm(alpha=1.0 / periodo, adjust=False).mean()
    assert res[columna].iloc[-1] == pytest.approx(esperado.iloc[-1], rel=1e-9)


def test_atr_del_extractor_coincide_con_el_del_mcp():
    """Las dos tuberías leen la misma materia prima y publican el mismo nombre.

    Si este test falla, alguien volvió a separar las implementaciones y el sizing
    del Playbook dejó de ser reproducible entre `get_asset_levels` y el snapshot
    del motor.
    """
    df = _ohlc()
    del_extractor = calcular_indicadores(df)["atr_14"].iloc[-1]
    del_mcp = mt5_client.atr(df, 14).iloc[-1]

    assert del_extractor == pytest.approx(del_mcp, rel=1e-9)


def test_los_digits_del_extractor_coinciden_con_el_catalogo():
    """Tres valores para los decimales del cobre es dos de mas.

    Medido el 2026-09-03: `config/activos.json` decia 1, `ASSET_CONFIG` decia 4 y
    el terminal reporta 0. El del extractor no lo lee nadie -aparece solo en los
    literales de ASSET_CONFIG- y por eso el valor equivocado nunca dio un
    problema visible. Pero es una trampa: quien lea `ASSET_CONFIG["COPPER"]
    ["digits"] == 4` va a creerle.

    Y no era solo el cobre: WTI y Brent estaban en 2 cuando el broker los cotiza
    con 3.

    La fuente unica es `config/activos.json`, que alimenta `VALID_TICKERS` y es lo
    que `analisis.py` usa para redondear. Este test la impone sobre el extractor.
    """
    import sys
    from pathlib import Path as _P
    raiz = _P(__file__).resolve().parents[1]
    if str(raiz / "scripts") not in sys.path:
        sys.path.insert(0, str(raiz / "scripts"))
    from extractor_precios import ASSET_CONFIG
    from market_data_mcp.catalog import VALID_TICKERS

    discrepancias = []
    for asset_id, cfg in ASSET_CONFIG.items():
        candidatos = cfg["mt5_symbol"]
        ticker = next((s for s in candidatos if s in VALID_TICKERS), None)
        assert ticker, f"{asset_id}: ninguno de sus simbolos {candidatos} esta en el catalogo"
        if cfg["digits"] != VALID_TICKERS[ticker]:
            discrepancias.append(
                f"{asset_id} ({ticker}): extractor={cfg['digits']} catalogo={VALID_TICKERS[ticker]}"
            )
    assert not discrepancias, (
        "los decimales del extractor no coinciden con el catalogo: "
        + "; ".join(discrepancias)
    )


def test_el_cobre_lleva_los_decimales_del_terminal():
    """Decision del director el 2026-09-03: manda el terminal.

    `symbol_info("COPPER").digits` devuelve 0 y su bid es 14197.0, porque el
    broker cotiza el cobre por tonelada metrica en enteros. La regla de formato
    del proyecto ya contempla el caso: "nunca redondear a enteros salvo que
    digits = 0".

    Ojo con no confundir esta serie con `COBRE_COMEX` de `commodities_data.json`,
    que es el precio COMEX en USD/libra (6,602) y va con 4 decimales. Son dos
    series distintas del mismo metal, en dos unidades, y solo una es el simbolo
    operable del broker.
    """
    from market_data_mcp.catalog import VALID_TICKERS

    assert VALID_TICKERS["COPPER"] == 0
