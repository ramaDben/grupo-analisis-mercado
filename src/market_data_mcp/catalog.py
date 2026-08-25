"""Catálogo de tickers válidos del proyecto — fuente única compartida por las tools.

Carga `config/activos.json` una vez al importar y expone `{ticker_mt5: digits}`.
Lo usan `get_asset_levels` (tools/levels.py) y `get_chart_objects`
(tools/chart_objects.py) para validar el ticker y respetar los decimales MT5.
"""
from __future__ import annotations

import json
from pathlib import Path

# config/activos.json está en la raíz del repo (4 niveles arriba de este archivo).
_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "activos.json"


def load_valid_tickers() -> dict[str, int]:
    """Retorna {ticker_mt5: digits} de todos los activos del catálogo."""
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    tickers: dict[str, int] = {}

    for asset in data.get("forex_commodities", []):
        tickers[asset["ticker_mt5"]] = asset["digits"]

    for asset in data.get("indices", []):
        tickers[asset["ticker_mt5"]] = asset["digits"]

    # Los ETF viven en un dict con notas + `componentes`, igual que `acciones`, no
    # como lista plana: las notas explican por qué el bloque existe (ver el JSON).
    for asset in data.get("etfs", {}).get("componentes", []):
        tickers[asset["ticker_mt5"]] = asset["digits"]

    for sector in data.get("acciones", {}).values():
        for comp in sector.get("componentes", []):
            tickers[comp["ticker_mt5"]] = comp["digits"]

    for comp in data.get("activos_complementarios", {}).values():
        tickers[comp["ticker_mt5"]] = comp["digits"]

    return tickers


# Cargado una vez al importar (las tools lo importan directamente).
VALID_TICKERS: dict[str, int] = load_valid_tickers()
