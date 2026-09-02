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


def test_catalogo_incluye_etfs_con_sufijo_us():
    """Los ETF del broker llevan sufijo `.US`, no prefijo `#`.

    El prefijo `#` es de las acciones. Un payload que pida "#QQQ" (como asumía el
    plan de unificación) cae en TICKER_NOT_FOUND, y el mensaje de error lista los
    tickers válidos para que se corrija en el momento.
    """
    for ticker in ("QQQ.US", "SPY.US", "GLD.US", "IWM.US", "SOXX.US"):
        assert ticker in levels._VALID_TICKERS, f"falta el ETF {ticker}"
        assert levels._VALID_TICKERS[ticker] == 2, f"{ticker} cotiza con 2 decimales"

    # Lo que el broker NO ofrece no debe estar inventado en el catálogo.
    for inexistente in ("#QQQ", "#SPY", "#TLT", "#SMH", "TLT.US", "SMH.US"):
        assert inexistente not in levels._VALID_TICKERS, (
            f"{inexistente} no existe en el terminal: verificado con symbol_info "
            "contra la cuenta real el 2026-08-25"
        )


def test_catalogo_incluye_las_criptos_con_sus_decimales():
    """ADA y DOGE cotizan con 4 decimales y el resto con 2.

    Importa por la regla de formato de precios: mostrar 0.42 en vez de 0.4213 no es
    un redondeo cosmético, es perder dos órdenes de magnitud de precisión en un
    activo que se mueve en centavos. Y el ticker del broker es DOGUSD, no DOGEUSD.
    """
    esperado = {
        "BTCUSD": 2, "ETHUSD": 2, "SOLUSD": 2, "LTCUSD": 2,
        "ADAUSD": 4, "DOGUSD": 4,
    }
    for ticker, digits in esperado.items():
        assert ticker in levels._VALID_TICKERS, f"falta la cripto {ticker}"
        assert levels._VALID_TICKERS[ticker] == digits, f"{ticker} debe tener {digits} decimales"

    assert "DOGEUSD" not in levels._VALID_TICKERS, "el broker la llama DOGUSD"


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
        for k in (
            "price", "s1", "s2", "r1", "r2", "rsi_14", "atr_14", "adx_14", "trend", "timestamp",
            "ema_50", "ema_100",
            "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_mid", "bb_lower",
        ):
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

    # RSI siempre en rango; ATR positivo; ADX en rango 0-100; tendencia válida
    assert 0.0 <= res["rsi_14"] <= 100.0
    assert res["atr_14"] > 0
    assert 0.0 <= res["adx_14"] <= 100.0
    assert res["trend"] in {"ALCISTA", "BAJISTA", "LATERAL"}

    # Serie con deriva alcista → precio por encima de la EMA100 → ALCISTA
    assert res["trend"] == "ALCISTA"

    # Campos nuevos siempre presentes y con tipos correctos
    for k in ("ema_20", "ema_50", "ema_100", "bb_upper", "bb_mid", "bb_lower",
              "donchian_50_high", "donchian_50_low", "donchian_50_mid"):
        assert k in res, f"falta campo {k}"
        assert isinstance(res[k], float), f"{k} debe ser float"
        assert res[k] > 0, f"{k} debe ser positivo"

    for k in ("macd_line", "macd_signal", "macd_hist"):
        assert k in res, f"falta campo {k}"
        assert isinstance(res[k], float), f"{k} debe ser float"

    # EMA 50 >= EMA 100 en serie con deriva alcista fuerte
    assert res["ema_50"] >= res["ema_100"], "EMA rápida >= EMA lenta en tendencia alcista"
    assert res["ema_20"] >= res["ema_50"], "EMA 20 >= EMA 50 en tendencia alcista"

    # Bollinger: upper > mid > lower
    assert res["bb_upper"] > res["bb_mid"] > res["bb_lower"]

    # Donchian encierra al precio y el mid es el promedio de los extremos.
    assert res["donchian_50_low"] <= res["price"] <= res["donchian_50_high"]
    promedio = (res["donchian_50_high"] + res["donchian_50_low"]) / 2
    assert abs(res["donchian_50_mid"] - promedio) < 0.01


def test_ema_20_no_es_la_banda_media_de_bollinger(collector, monkeypatch):
    """`ema_20` es media EXPONENCIAL y `bb_mid` es media SIMPLE de 20.

    Es la confusión que motivó exponer el campo: el Playbook manda "EMA 20 en H1"
    como gatillo, y quien tomara `bb_mid` por esa EMA estaría usando otro indicador.
    Sobre una serie con tendencia las dos medias difieren, porque la exponencial pesa
    más los datos recientes.
    """
    from market_data_mcp import mt5_client

    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: _df_ohlc())

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H1")

    assert res["ema_20"] != res["bb_mid"], (
        "si coinciden, alguien cambió una de las dos por la otra"
    )
    # En serie alcista la exponencial va por delante de la simple.
    assert res["ema_20"] > res["bb_mid"]


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


def test_atr_restante_solo_aparece_en_d1(collector, monkeypatch):
    """rango_hoy y atr_restante_14 son un concepto de D1 (vela diaria en curso);
    en otros marcos no corresponden y no deben aparecer."""
    from market_data_mcp import mt5_client

    df = _df_ohlc()
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df)

    levels.register(collector)
    res_h4 = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")
    assert "atr_restante_14" not in res_h4
    assert "rango_hoy" not in res_h4

    res_d1 = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="D1")
    assert "atr_restante_14" in res_d1
    assert "rango_hoy" in res_d1
    assert res_d1["rango_hoy"] > 0


def test_atr_restante_nunca_baja_del_piso_30_por_ciento(collector, monkeypatch):
    """Si la vela diaria en curso ya recorrió más que el ATR completo (día muy
    volátil), el ATR restante no debe colapsar a 0: se detiene en el piso del 30%."""
    from market_data_mcp import mt5_client

    df = _df_ohlc()
    # Fuerza que la última vela (la del día en curso) tenga un rango enorme,
    # mayor que cualquier ATR14 razonable calculado sobre la serie.
    df.loc[df.index[-1], "high"] = df["high"].iloc[-1] + 1000
    df.loc[df.index[-1], "low"] = df["low"].iloc[-1] - 1000
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df)

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="D1")

    piso_esperado = levels.PISO_ATR_RESTANTE * res["atr_14"]
    assert abs(res["atr_restante_14"] - piso_esperado) < 0.05


def test_adx_serie_con_tendencia_clara_supera_umbral_de_tendencia_confirmada():
    """Con una deriva direccional fuerte y sostenida, el ADX debe superar 25
    (umbral de mercado para 'tendencia confirmada')."""
    from market_data_mcp import mt5_client
    df = _df_ohlc(n=200)  # deriva alcista + oscilación, misma serie que get_asset_levels usa
    valor = float(mt5_client.adx(df, 14).iloc[-1])
    assert 0.0 <= valor <= 100.0
    assert valor > 25.0


def test_adx_serie_lateral_sin_deriva_queda_bajo_el_gate_de_20():
    """Sin deriva direccional (ruido puro alrededor de un nivel fijo), el ADX
    debe quedar por debajo del gate de 20 que usa /oportunidad."""
    from market_data_mcp import mt5_client
    rng = np.random.default_rng(3)
    ruido = pd.Series(100 + rng.standard_normal(200) * 0.05)
    df = pd.DataFrame({"high": ruido + 0.1, "low": ruido - 0.1, "close": ruido})
    valor = float(mt5_client.adx(df, 14).iloc[-1])
    assert 0.0 <= valor <= 100.0
    assert valor < 20.0


def test_donchian_toma_los_extremos_de_la_ventana():
    """El canal es el máximo del high y el mínimo del low de las últimas `period`
    barras, con `mid` en el centro. Valores calculados a mano para que el test falle
    si alguien cambia la ventana o confunde high con close."""
    from market_data_mcp import mt5_client

    # 60 barras: high de 100 a 159, low siempre 10 abajo. La ventana de 50 son los
    # índices 10..59, así que high máximo = 159 y low mínimo = 100.
    df = pd.DataFrame({
        "high": [100 + i for i in range(60)],
        "low": [90 + i for i in range(60)],
        "close": [95 + i for i in range(60)],
    })
    dc_h, dc_l, dc_m = mt5_client.donchian(df, period=50)
    assert (dc_h, dc_l, dc_m) == (159.0, 100.0, 129.5)


def test_donchian_encierra_el_precio_en_serie_ruidosa():
    """Invariante del canal: el último cierre no puede quedar fuera de sus extremos."""
    from market_data_mcp import mt5_client
    rng = np.random.default_rng(11)
    base = pd.Series(100 + rng.standard_normal(200).cumsum())
    df = pd.DataFrame({"high": base + 0.4, "low": base - 0.4, "close": base})
    dc_h, dc_l, dc_m = mt5_client.donchian(df, period=50)
    assert dc_l <= float(base.iloc[-1]) <= dc_h
    assert dc_l < dc_m < dc_h


def test_donchian_usa_high_y_low_no_el_cierre():
    """Regresión: con una mecha larga el canal tiene que abrirse.

    Si la implementación tomara `close` en vez de `high`/`low`, una barra con mecha
    de 50 puntos no movería el canal y el ADC quedaría subestimado justo en la barra
    más volátil, que es cuando más importa.
    """
    from market_data_mcp import mt5_client
    df = pd.DataFrame({
        "high": [100.0] * 60,
        "low": [90.0] * 60,
        "close": [95.0] * 60,
    })
    df.loc[df.index[-1], "high"] = 150.0
    df.loc[df.index[-1], "low"] = 50.0
    dc_h, dc_l, _ = mt5_client.donchian(df, period=50)
    assert dc_h == 150.0, "el máximo debe seguir al high, no al close"
    assert dc_l == 50.0, "el mínimo debe seguir al low, no al close"


def test_bollinger_banda_media_es_sma():
    """La banda media debe coincidir con la SMA de los últimos `period` valores."""
    from market_data_mcp import mt5_client
    serie = pd.Series(range(1, 41), dtype="float64")  # 40 valores, period=20
    _, bb_m, _ = mt5_client.bollinger(serie, period=20)
    sma_manual = float(serie.iloc[-20:].mean())
    assert abs(bb_m - sma_manual) < 1e-9


def test_insuficientes_datos_umbral_150(collector, monkeypatch):
    """El umbral mínimo de barras es 150 (suficiente para MACD + Bollinger)."""
    from market_data_mcp import mt5_client

    df_corto = _df_ohlc(n=149)  # 1 bar por debajo del umbral
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df_corto)

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")

    assert res["error"] == "INSUFFICIENT_DATA"
    assert "150" in res["message"]


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


def test_la_ruta_feliz_no_exige_conexion_viva_a_mt5(collector, monkeypatch):
    """`analizar_activo` llama a `connect()` por prudencia, pero la fuente de verdad
    es `get_rates`. Si exigir la conexión aborta el análisis, la ruta feliz deja de
    ser testeable sin terminal y CI vuelve a quedar ciega (pasó el 2026-09-01)."""
    from market_data_mcp import mt5_client

    def connect_caido():
        raise RuntimeError("MetaTrader5 no está instalado en este entorno")

    monkeypatch.setattr(mt5_client, "connect", connect_caido)
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: _df_ohlc())

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")
    assert "error" not in res, res
    assert res["ticker"] == "XAUUSD"
