#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extractor_precios.py
Ingesta y cálculo de indicadores técnicos OHLC para el Playbook Cuantitativo Intermercado.
Descarga velas H1 y D1 de MT5 (con fallback a yfinance) y persiste series limpias con ATR, EMA, SMA y Canales Donchian.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

OUTPUT_DIR = BASE_DIR / "data central" / "DATA PRECIOS OHLC"

# Mapeo de activos a MT5 y yfinance
ASSET_CONFIG = {
    "USDCLP": {
        "mt5_symbol": ["USDCLP", "USDCLP.spot"],
        "yf_symbol": "USDCLP=X",
        "nombre": "Dólar / Peso Chileno",
        "digits": 2
    },
    "XAUUSD": {
        "mt5_symbol": ["XAUUSD", "GOLD", "XAUUSD.spot"],
        "yf_symbol": "GC=F",
        "nombre": "Oro Spot",
        "digits": 2
    },
    "WTI": {
        "mt5_symbol": ["WTI.spot", "WTI", "OIL"],
        "yf_symbol": "CL=F",
        "nombre": "Petróleo Crudo WTI",
        "digits": 2
    },
    "BRENT": {
        "mt5_symbol": ["BRENT.spot", "BRENT", "UKOIL"],
        "yf_symbol": "BZ=F",
        "nombre": "Petróleo Crudo Brent",
        "digits": 2
    },
    "US100": {
        "mt5_symbol": ["US100.spot", "US100", "NAS100"],
        "yf_symbol": "NQ=F",
        "nombre": "Nasdaq 100",
        "digits": 2
    },
    "COPPER": {
        "mt5_symbol": ["COPPER", "COPPER.spot", "HG"],
        "yf_symbol": "HG=F",
        "nombre": "Cobre COMEX de Alta Calidad",
        "digits": 4
    }
}


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el set exacto de indicadores requeridos por el Playbook Cuantitativo."""
    if len(df) == 0:
        return df

    df = df.copy()
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    # True Range
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # ATR 14 y ATR 20 (suavizado exponencial y simple)
    df["atr_14"] = tr.ewm(span=14, adjust=False).mean()
    df["atr_20"] = tr.ewm(span=20, adjust=False).mean()

    # EMAs institucionales
    df["ema_16"] = close.ewm(span=16, adjust=False).mean()
    df["ema_20"] = close.ewm(span=20, adjust=False).mean()
    df["ema_50"] = close.ewm(span=50, adjust=False).mean()
    df["ema_200"] = close.ewm(span=200, adjust=False).mean()

    # RSI 14 (Wilder)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["rsi_14"] = df["rsi_14"].fillna(50.0)

    # Canales Donchian 50
    df["donchian_50_high"] = high.rolling(window=50, min_periods=1).max()
    df["donchian_50_low"] = low.rolling(window=50, min_periods=1).min()
    df["donchian_50_mid"] = (df["donchian_50_high"] + df["donchian_50_low"]) / 2.0

    # SMA 20 (Reversión a la media)
    df["sma_20"] = close.rolling(window=20, min_periods=1).mean()

    return df


def descargar_velas_mt5(tickers: list[str] | str, timeframe: str, n_bars: int = 10000) -> pd.DataFrame | None:
    """Intenta descargar velas desde MetaTrader 5 probando la lista de símbolos candidatos."""
    candidates = [tickers] if isinstance(tickers, str) else tickers
    try:
        from market_data_mcp import mt5_client
        mt5_client.connect()
        for sym in candidates:
            df = mt5_client.get_rates(sym, timeframe, n_bars)
            if df is not None and len(df) > 0:
                return df
    except Exception:
        pass
    return None


def descargar_velas_yfinance(yf_symbol: str, timeframe: str, n_bars: int = 10000) -> pd.DataFrame | None:
    """Fallback a yfinance para entornos sin MT5 o terminal cerrado."""
    try:
        import yfinance as yf

        interval_map = {
            "H1": "1h",
            "D1": "1d",
            "M15": "15m"
        }
        interval = interval_map.get(timeframe.upper(), "1d")
        period = "730d" if interval == "1h" else "5y"

        ticker_obj = yf.Ticker(yf_symbol)
        df_raw = ticker_obj.history(period=period, interval=interval)

        if df_raw is None or len(df_raw) == 0:
            return None

        df = pd.DataFrame()
        df["time"] = df_raw.index.tz_localize(None)
        df["open"] = df_raw["Open"].values
        df["high"] = df_raw["High"].values
        df["low"] = df_raw["Low"].values
        df["close"] = df_raw["Close"].values
        df["tick_volume"] = df_raw["Volume"].values if "Volume" in df_raw else 0

        return df.tail(n_bars).reset_index(drop=True)
    except Exception as exc:
        print(f"[WARN] yfinance error para {yf_symbol}: {exc}")
        return None


def extraer_activo(asset_id: str, timeframe: str = "H1", n_bars: int = 10000) -> dict | None:
    """Descarga y calcula indicadores para un activo y temporalidad."""
    cfg = ASSET_CONFIG.get(asset_id)
    if not cfg:
        return None

    fuente = "MT5"
    df = descargar_velas_mt5(cfg["mt5_symbol"], timeframe, n_bars)

    if df is None or len(df) == 0:
        fuente = "YFINANCE"
        df = descargar_velas_yfinance(cfg["yf_symbol"], timeframe, n_bars)

    if df is None or len(df) == 0:
        return None

    import hashlib

    df_ind = calcular_indicadores(df)
    ultimo = df_ind.iloc[-1]

    # Convertir registros a lista cronológica
    velas_list = []
    for _, row in df_ind.iterrows():
        t_str = row["time"].isoformat() if hasattr(row["time"], "isoformat") else str(row["time"])
        velas_list.append({
            "time": t_str,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "tick_volume": int(row["tick_volume"]) if "tick_volume" in row and not np.isnan(row["tick_volume"]) else 0,
            "rsi_14": float(row["rsi_14"]) if not np.isnan(row["rsi_14"]) else None,
            "atr_14": float(row["atr_14"]) if not np.isnan(row["atr_14"]) else None,
            "atr_20": float(row["atr_20"]) if not np.isnan(row["atr_20"]) else None,
            "ema_16": float(row["ema_16"]) if not np.isnan(row["ema_16"]) else None,
            "ema_20": float(row["ema_20"]) if not np.isnan(row["ema_20"]) else None,
            "ema_50": float(row["ema_50"]) if not np.isnan(row["ema_50"]) else None,
            "ema_200": float(row["ema_200"]) if not np.isnan(row["ema_200"]) else None,
            "sma_20": float(row["sma_20"]) if not np.isnan(row["sma_20"]) else None,
            "donchian_50_high": float(row["donchian_50_high"]) if not np.isnan(row["donchian_50_high"]) else None,
            "donchian_50_low": float(row["donchian_50_low"]) if not np.isnan(row["donchian_50_low"]) else None,
        })

    # Hash determinista de los datos
    raw_bytes = json.dumps(velas_list, sort_keys=True).encode("utf-8")
    data_hash = hashlib.sha256(raw_bytes).hexdigest()

    payload = {
        "symbol": asset_id,
        "nombre": cfg["nombre"],
        "timeframe": timeframe,
        "source": fuente,
        "broker": "MT5" if fuente == "MT5" else "YFINANCE",
        "timezone": "UTC",
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "bar_count": len(velas_list),
        "data_hash": data_hash,
        "quality_report_id": f"QR-{asset_id}-{timeframe}-{data_hash[:8]}",
        "snapshot_actual": {
            "open": float(ultimo["open"]),
            "high": float(ultimo["high"]),
            "low": float(ultimo["low"]),
            "close": float(ultimo["close"]),
            "change_pct": round(((float(ultimo["close"]) - float(ultimo["open"])) / float(ultimo["open"])) * 100, 2) if float(ultimo["open"]) != 0 else 0.0,
            "rsi_14": float(ultimo["rsi_14"]) if not np.isnan(ultimo["rsi_14"]) else None,
            "atr_14": float(ultimo["atr_14"]) if not np.isnan(ultimo["atr_14"]) else None,
            "atr_20": float(ultimo["atr_20"]) if not np.isnan(ultimo["atr_20"]) else None,
            "ema_16": float(ultimo["ema_16"]) if not np.isnan(ultimo["ema_16"]) else None,
            "ema_20": float(ultimo["ema_20"]) if not np.isnan(ultimo["ema_20"]) else None,
            "ema_50": float(ultimo["ema_50"]) if not np.isnan(ultimo["ema_50"]) else None,
            "ema_200": float(ultimo["ema_200"]) if not np.isnan(ultimo["ema_200"]) else None,
            "sma_20": float(ultimo["sma_20"]) if not np.isnan(ultimo["sma_20"]) else None,
            "donchian_50_high": float(ultimo["donchian_50_high"]) if not np.isnan(ultimo["donchian_50_high"]) else None,
            "donchian_50_low": float(ultimo["donchian_50_low"]) if not np.isnan(ultimo["donchian_50_low"]) else None,
        },
        "rows": velas_list
    }

    return payload


def ejecutar_extraccion_precios() -> dict:
    """Ejecuta la descarga de todos los activos en M15, H1, D1 y W1 y persiste en JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    resumen = {
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "activos": {}
    }

    for asset_id in ASSET_CONFIG.keys():
        resumen["activos"][asset_id] = {}
        for tf in ["M15", "H1", "D1", "W1"]:
            data = extraer_activo(asset_id, tf)
            if data:
                archivo_out = OUTPUT_DIR / f"{asset_id}_{tf}.json"
                with open(archivo_out, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                resumen["activos"][asset_id][tf] = data["snapshot_actual"]
                resumen["activos"][asset_id][f"{tf}_fuente"] = data["source"]
                print(f"[OK] Precios {asset_id} {tf} ({data['source']}) -> {archivo_out.name}")
            else:
                print(f"[WARN] No se pudieron obtener precios para {asset_id} {tf}")
                resumen["activos"][asset_id][tf] = None

    # Guardar resumen rápido
    summary_file = OUTPUT_DIR / "latest_prices_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"[OK] Ingesta de precios OHLC completada -> {summary_file}")
    return resumen


if __name__ == "__main__":
    ejecutar_extraccion_precios()
