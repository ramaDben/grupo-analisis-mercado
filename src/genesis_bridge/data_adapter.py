"""
genesis_bridge.data_adapter
Adaptador de datos y costos que conecta el repositorio desk (JSONs OHLC) con las estructuras canónicas de Genesis.
Calcula hashes criptográficos SHA-256 e inyecta perfiles de costos obligatorios (Regla R40).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from genesis.backtest.costs import CostsConfig
from genesis.data.profile import FirmProfile, load_firm_profile
from genesis.data.symbols import SymbolFigure
from genesis_bridge.errors import GenesisBridgeError

DATA_PRECIOS_DIR = Path(__file__).resolve().parents[2] / "data central" / "DATA PRECIOS OHLC"

# Costos institucionales conservadores (R40: sin costos no hay reporte)
COST_PROFILES = {
    "XAUUSD": CostsConfig(
        default_spread_points=2.5,
        commission_per_lot=7.0,
        slippage_points=1.0,
    ),
    "USDCLP": CostsConfig(
        default_spread_points=50.0,
        commission_per_lot=10.0,
        slippage_points=20.0,
    ),
    "US100": CostsConfig(
        default_spread_points=1.5,
        commission_per_lot=4.0,
        slippage_points=0.5,
    ),
    "WTI": CostsConfig(
        default_spread_points=3.0,
        commission_per_lot=6.0,
        slippage_points=1.0,
    ),
    "BRENT": CostsConfig(
        default_spread_points=3.0,
        commission_per_lot=6.0,
        slippage_points=1.0,
    ),
    "NAS100": CostsConfig(
        default_spread_points=1.5,
        commission_per_lot=4.0,
        slippage_points=0.5,
    ),
}

# Especificaciones de activos (SymbolFigure)
SYMBOL_FIGURES = {
    "XAUUSD": SymbolFigure(
        symbol="XAUUSD",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-15.0,
        swap_short=5.0,
        swap_rollover_day=3,
    ),
    "USDCLP": SymbolFigure(
        symbol="USDCLP",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-5.0,
        swap_short=2.0,
        swap_rollover_day=3,
    ),
    "US100": SymbolFigure(
        symbol="US100",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-8.0,
        swap_short=1.0,
        swap_rollover_day=3,
    ),
    "NAS100": SymbolFigure(
        symbol="NAS100",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-8.0,
        swap_short=1.0,
        swap_rollover_day=3,
    ),
    "WTI": SymbolFigure(
        symbol="WTI",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-10.0,
        swap_short=2.0,
        swap_rollover_day=3,
    ),
    "BRENT": SymbolFigure(
        symbol="BRENT",
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-10.0,
        swap_short=2.0,
        swap_rollover_day=3,
    ),
}

SYMBOL_ALIASES_TO_GENESIS = {
    "US100": "NAS100",
    "NQ": "NAS100",
    "SP500": "US500",
    "DAX": "GER40",
}


def to_genesis_symbol(symbol: str) -> str:
    """Mapea símbolos de desk a nombres canónicos de sesión en Genesis (ej. US100 -> NAS100)."""
    sym = symbol.upper()
    return SYMBOL_ALIASES_TO_GENESIS.get(sym, sym)


def get_symbol_figure(symbol: str) -> SymbolFigure:
    sym = symbol.upper()
    gen_sym = to_genesis_symbol(sym)
    if sym in SYMBOL_FIGURES:
        return SYMBOL_FIGURES[sym]
    if gen_sym in SYMBOL_FIGURES:
        return SYMBOL_FIGURES[gen_sym]
    # Default conservador
    return SymbolFigure(
        symbol=gen_sym,
        tick_value=1.0,
        volume_step=0.01,
        stops_level=0,
        freeze_level=0,
        digits=2,
        swap_long=-5.0,
        swap_short=1.0,
        swap_rollover_day=3,
    )


def get_costs_config(symbol: str) -> CostsConfig:
    sym = symbol.upper()
    gen_sym = to_genesis_symbol(sym)
    if sym in COST_PROFILES:
        return COST_PROFILES[sym]
    if gen_sym in COST_PROFILES:
        return COST_PROFILES[gen_sym]
    # Fallback con costos no nulos
    return CostsConfig(
        default_spread_points=2.0,
        commission_per_lot=5.0,
        slippage_points=1.0,
    )


def get_firm_profile(name: str = "The5ers") -> FirmProfile:
    """Retorna el perfil institucional de la firma de prop trading."""
    return load_firm_profile()


def load_ohlc_as_dataframe(
    symbol: str,
    timeframe: str = "H1",
    data_dir: Path | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Carga un archivo JSON de precios OHLC, valida su esquema y lo convierte
    en un DataFrame canónico de Genesis. Retorna (df, dataset_sha256).
    """
    base_dir = Path(data_dir) if data_dir is not None else DATA_PRECIOS_DIR
    candidates = [
        base_dir / f"{symbol.upper()}_{timeframe.upper()}.json",
        base_dir / f"{to_genesis_symbol(symbol)}_{timeframe.upper()}.json",
    ]
    # Reverse aliases
    for desk_k, gen_v in SYMBOL_ALIASES_TO_GENESIS.items():
        if symbol.upper() == gen_v:
            candidates.append(base_dir / f"{desk_k}_{timeframe.upper()}.json")

    target_file = next((f for f in candidates if f.exists()), None)
    if target_file is None:
        raise GenesisBridgeError(f"Archivo de datos no encontrado para {symbol} ({timeframe}) en: {base_dir}")

    raw_text = target_file.read_text(encoding="utf-8")
    data = json.loads(raw_text)

    rows = data.get("rows") or data.get("velas") or []
    if not rows:
        raise GenesisBridgeError(f"El archivo {target_file.name} no contiene filas en 'rows' ni 'velas'.")

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["time"], utc=True)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["tick_volume"] = df["tick_volume"].astype(float) if "tick_volume" in df else 0.0
    fig = get_symbol_figure(symbol)
    point = 10.0 ** (-fig.digits)
    df["bid"] = df["close"]
    df["ask"] = df["close"] + (get_costs_config(symbol).default_spread_points * point)
    df["last"] = df["close"]

    # Ordenar y resetear índice
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Hash determinista de la tabla de precios
    hash_payload = df[["timestamp", "open", "high", "low", "close", "tick_volume"]].to_json(
        date_format="iso", orient="records"
    )
    dataset_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

    return df, dataset_hash
