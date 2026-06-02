"""Tests de la tool get_asset_levels: lógica técnica pura + contrato de error."""
from __future__ import annotations

import numpy as np
import pandas as pd

from market_data_mcp.tools import levels


# --- Catálogo de tickers ---

def test_valid_tickers_no_vacio_y_con_nucleo():
    assert levels._VALID_TICKERS, "el catálogo de tickers no debe estar vacío"
    # Activos núcleo del grupo
    assert "XAUUSD" in levels._VALID_TICKERS
    assert "USDCLP" in levels._VALID_TICKERS
    # digits siempre es un entero >= 0 (regla de decimales MT5)
    assert all(isinstance(d, int) and d >= 0 for d in levels._VALID_TICKERS.values())


# --- RSI (Wilder) ---

def test_rsi_serie_creciente_tiende_a_100():
    serie = pd.Series(range(1, 60), dtype="float64")
    assert 99.0 <= levels._rsi(serie, period=14) <= 100.0


def test_rsi_siempre_en_rango_0_100():
    rng = np.random.default_rng(42)
    serie = pd.Series(100 + rng.standard_normal(200).cumsum())
    assert 0.0 <= levels._rsi(serie, period=14) <= 100.0


# --- Clustering de niveles ---

def test_cluster_agrupa_cercanos_y_separa_lejanos():
    # threshold 1.0: 100.0 y 100.5 se agrupan en uno; 105.0 queda aparte
    assert levels._cluster([100.0, 100.5, 105.0], threshold=1.0) == [100.0, 105.0]


def test_cluster_lista_vacia():
    assert levels._cluster([], threshold=1.0) == []


# --- Soportes / Resistencias ---

def _df_sintetico(n: int = 80) -> pd.DataFrame:
    """OHLC sintético en forma de onda para generar swing highs/lows claros."""
    x = np.linspace(0, 6 * np.pi, n)
    base = 100 + 5 * np.sin(x)
    return pd.DataFrame({"high": base + 0.5, "low": base - 0.5, "close": base})


def test_support_resistance_quedan_del_lado_correcto_del_precio():
    """Contrato documentado: R1/R2 > precio actual > S1/S2 (siempre, vía fallback ATR)."""
    df = _df_sintetico()
    current = float(df["close"].iloc[-1])
    niveles = levels._get_support_resistance(df, current=current, atr14=1.0, digits=2)
    assert niveles["r1"] > current
    assert niveles["r2"] > current
    assert niveles["s1"] < current
    assert niveles["s2"] < current


# --- Contrato de error de get_asset_levels ---

def test_ticker_fuera_de_catalogo_retorna_error(collector):
    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="TICKER_INEXISTENTE_XYZ")
    assert res["error"] == "TICKER_NOT_FOUND"
    assert isinstance(res["message"], str) and res["message"]


def test_ticker_valido_nunca_devuelve_none_ni_lanza(collector):
    """El contrato dice: nunca array vacío, nunca None silencioso.
    Sin MT5 disponible debe devolver un error explícito; con MT5, un payload válido."""
    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD")
    assert isinstance(res, dict)
    if "error" in res:
        assert res["error"] in {"MT5_UNAVAILABLE", "INSUFFICIENT_DATA", "INVALID_TIMEFRAME"}
        assert isinstance(res["message"], str) and res["message"]
    else:
        # Camino feliz (solo si MT5 está conectado en el entorno)
        assert res["ticker"] == "XAUUSD"
        for k in ("price", "s1", "s2", "r1", "r2", "rsi_14", "atr_14", "trend", "timestamp"):
            assert k in res
