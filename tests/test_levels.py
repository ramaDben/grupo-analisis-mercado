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


# --- Camino feliz con mt5_client vendorizado mockeado (issue #30) ---

def _df_ohlc(n: int = 300) -> pd.DataFrame:
    """OHLC sintético con tendencia alcista clara y velas suficientes (>=100)."""
    x = np.linspace(0, 8 * np.pi, n)
    base = 100 + 0.05 * np.arange(n) + 3 * np.sin(x)  # deriva alcista + oscilación
    return pd.DataFrame({
        "time":  pd.date_range("2026-01-01", periods=n, freq="h"),
        "open":  base,
        "high":  base + 0.5,
        "low":   base - 0.5,
        "close": base,
    })


def test_camino_feliz_con_mt5_mockeado(collector, monkeypatch):
    """Con mt5_client vendorizado podemos mockear get_rates y validar el cálculo
    real de precio, S/R, RSI, ATR y tendencia — sin MT5 ni el terminal abierto.

    Antes de #30 este camino era inalcanzable en CI: mt5_client vivía fuera del
    repo y la tool caía siempre en MT5_UNAVAILABLE."""
    from market_data_mcp import mt5_client

    df = _df_ohlc()
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df)

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")

    # No es un error: es payload técnico completo
    assert "error" not in res, res
    assert res["ticker"] == "XAUUSD"
    assert res["timeframe"] == "H4"

    # Contrato S/R: R1/R2 por encima del precio, S1/S2 por debajo
    assert res["r1"] > res["price"] > res["s1"]
    assert res["r2"] >= res["r1"]
    assert res["s2"] <= res["s1"]

    # RSI siempre en rango; ATR positivo; tendencia válida
    assert 0.0 <= res["rsi_14"] <= 100.0
    assert res["atr_14"] > 0
    assert res["trend"] in {"ALCISTA", "BAJISTA", "LATERAL"}

    # Serie con deriva alcista → precio por encima de la EMA100 → ALCISTA
    assert res["trend"] == "ALCISTA"


# --- macd() y bollinger() (mt5_client) ---

def test_macd_serie_creciente_hist_positivo():
    """Con serie creciente la línea MACD > señal → histograma positivo."""
    from market_data_mcp import mt5_client
    serie = pd.Series(range(1, 101), dtype="float64")
    macd_l, macd_s, macd_h = mt5_client.macd(serie)
    assert isinstance(macd_l, float)
    assert isinstance(macd_s, float)
    assert isinstance(macd_h, float)
    assert macd_h > 0, "serie creciente → histograma positivo"


def test_macd_serie_decreciente_hist_negativo():
    from market_data_mcp import mt5_client
    serie = pd.Series(range(100, 0, -1), dtype="float64")
    _, _, macd_h = mt5_client.macd(serie)
    assert macd_h < 0, "serie decreciente → histograma negativo"


def test_bollinger_upper_mayor_que_lower():
    from market_data_mcp import mt5_client
    rng = np.random.default_rng(7)
    serie = pd.Series(100 + rng.standard_normal(60).cumsum())
    bb_u, bb_m, bb_l = mt5_client.bollinger(serie)
    assert isinstance(bb_u, float) and isinstance(bb_m, float) and isinstance(bb_l, float)
    assert bb_u > bb_m > bb_l, "upper > mid > lower siempre"


def test_bollinger_banda_media_es_sma():
    """La banda media debe coincidir con la SMA de los últimos `period` valores."""
    from market_data_mcp import mt5_client
    serie = pd.Series(range(1, 41), dtype="float64")  # 40 valores, period=20
    _, bb_m, _ = mt5_client.bollinger(serie, period=20)
    sma_manual = float(serie.iloc[-20:].mean())
    assert abs(bb_m - sma_manual) < 1e-9


def test_mt5_no_instalado_retorna_error_no_lanza(collector, monkeypatch):
    """Regresión (#30/#31): mt5_client importa MetaTrader5 de forma perezosa
    dentro de get_rates. Si el paquete no está instalado (caso de CI), el
    ModuleNotFoundError surge en la llamada, no en el import de levels.py.
    get_asset_levels debe convertirlo en MT5_UNAVAILABLE, nunca propagarlo.

    Este test reproduce el entorno de CI incluso en máquinas con MT5 instalado."""
    from market_data_mcp import mt5_client

    def _sin_mt5(*args, **kwargs):
        raise ModuleNotFoundError("No module named 'MetaTrader5'")

    monkeypatch.setattr(mt5_client, "get_rates", _sin_mt5)

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")

    assert res["error"] == "MT5_UNAVAILABLE"
    assert isinstance(res["message"], str) and res["message"]
