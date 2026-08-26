#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bias_reader.py
Módulo compartido (DRY) para lectura de solo lectura del Playbook de Trading Cuantitativo Intermercado.
Implementa validación de staleness consciente de fines de semana/feriados, contratos de error explícitos
y calculadora de lotaje con conversión multidivisa (USD / CLP).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE_DEFAULT = BASE_DIR / "data central" / "DATA DRIVERS USDCLP" / "macro_bias_output.json"
CONFIG_FILE_DEFAULT = BASE_DIR / "config" / "playbook_config.yaml"

VALID_SYMBOLS = {"ALL", "USDCLP", "XAUUSD", "WTI", "BRENT", "US100"}

# El Playbook nombra sus fichas con el símbolo genérico del activo; el catálogo
# técnico usa el símbolo del broker. Sin traducir, quien cruce ficha y precio
# busca un ticker que MT5 no conoce y se queda ciego sin enterarse.
#
# `BRENT` mapea a None a propósito y no se omite: el broker no ofrece Brent, así
# que la ausencia es un hecho del catálogo y no un olvido. Un `.get()` sobre un
# dict sin la clave devuelve None igual, pero deja al lector sin saber si el
# activo falta porque nadie lo agregó todavía.
TICKER_MT5: dict[str, str | None] = {
    "USDCLP": "USDCLP",
    "XAUUSD": "XAUUSD",
    "WTI": "WTI.spot",
    "US100": "US100.spot",
    "BRENT": None,
}


def cargar_config_staleness(config_path: Path | None = None) -> dict[str, float]:
    """Carga los umbrales de staleness desde el YAML o usa valores por defecto."""
    c_path = config_path or CONFIG_FILE_DEFAULT
    defaults = {
        "staleness_hours_weekday": 24.0,
        "staleness_hours_weekend": 80.0
    }
    if not c_path.exists():
        return defaults

    try:
        with open(c_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            st_cfg = cfg.get("staleness_thresholds", {})
            return {
                "staleness_hours_weekday": float(st_cfg.get("staleness_hours_weekday", 24.0)),
                "staleness_hours_weekend": float(st_cfg.get("staleness_hours_weekend", 80.0))
            }
    except Exception:
        return defaults


def validar_staleness(
    as_of_str: str | None,
    config: dict[str, float] | None = None,
    now_dt: datetime | None = None
) -> tuple[bool, float, float, str | None]:
    """
    Evalúa si la fecha as_of_utc es fresca según el calendario de negocio.
    Retorna: (es_fresco, horas_antiguedad, umbral_horas, error_reason)
    """
    if not as_of_str or not isinstance(as_of_str, str):
        return False, 0.0, 0.0, "MALFORMED_DATE"

    try:
        dt_as_of = datetime.fromisoformat(as_of_str.replace("Z", "+00:00"))
    except Exception:
        return False, 0.0, 0.0, "MALFORMED_DATE"

    now = now_dt or datetime.now(timezone.utc)
    if dt_as_of.tzinfo is None:
        dt_as_of = dt_as_of.replace(tzinfo=timezone.utc)

    horas = (now - dt_as_of).total_seconds() / 3600.0
    if horas < 0:
        horas = 0.0

    cfg = config or cargar_config_staleness()
    # Sábado = 5, Domingo = 6, Lunes = 0
    # Si hoy es fin de semana o lunes, el umbral es 80h para cubrir el fin de semana
    es_fin_de_semana_o_lunes = now.weekday() in (5, 6, 0)
    umbral = cfg["staleness_hours_weekend"] if es_fin_de_semana_o_lunes else cfg["staleness_hours_weekday"]

    if horas > umbral:
        return False, horas, umbral, "STALE_DATA"

    return True, horas, umbral, None


def cargar_macro_bias(
    symbol: str = "ALL",
    output_file: Path | None = None,
    config_path: Path | None = None,
    now_dt: datetime | None = None
) -> dict[str, Any]:
    """
    Consulta de solo lectura del sesgo cuantitativo, régimen R0-R4, SL dinámico y permisos.
    Herramienta ESTRICTAMENTE DE SOLO LECTURA (Single-Writer Pattern).
    """
    sym = (symbol or "ALL").upper().strip()
    if sym not in VALID_SYMBOLS:
        return {
            "error": "TICKER_NOT_IN_CATALOG",
            "message": f"Ticker '{symbol}' no pertenece al catálogo del Playbook. Opciones: {sorted(VALID_SYMBOLS)}."
        }

    out_path = output_file or OUTPUT_FILE_DEFAULT
    if not out_path.exists():
        return {
            "error": "STALE_DATA",
            "message": f"Archivo {out_path.name} no existe. Ejecutar previamente pipeline_ingesta.py."
        }

    try:
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {
            "error": "READ_ERROR",
            "message": f"Error leyendo output de sesgo: {exc}"
        }

    as_of_str = data.get("as_of_utc")
    cfg = cargar_config_staleness(config_path)
    es_fresco, horas, umbral, razon = validar_staleness(as_of_str, cfg, now_dt=now_dt)

    if razon == "MALFORMED_DATE":
        return {
            "error": "READ_ERROR",
            "message": f"Campo 'as_of_utc' malformado o ilegible: {as_of_str}"
        }

    if not es_fresco:
        return {
            "error": "STALE_DATA",
            "as_of_utc": as_of_str,
            "antiguedad_horas": round(horas, 1),
            "umbral_horas": round(umbral, 1),
            "message": f"Los datos del Playbook tienen {horas:.1f}h de antigüedad (>umbral {umbral:.1f}h). Ejecutar previamente pipeline_ingesta.py."
        }

    if sym == "ALL":
        return data

    activo_data = data.get("activos", {}).get(sym)
    if not activo_data:
        return {
            "error": "TICKER_NOT_IN_CATALOG",
            "message": f"No se encontraron datos calculados para el ticker '{sym}'."
        }

    return {
        "schema_version": data.get("schema_version"),
        "config_hash": data.get("config_hash"),
        "as_of_utc": data.get("as_of_utc"),
        "symbol": sym,
        "regimen_macro_global": data.get("regimen_macro_global"),
        "metricas_clave": data.get("metricas_clave"),
        "confianza_general": data.get("confianza_general"),
        "activo": activo_data
    }


def calcular_lote_riesgo(
    capital_usd: float,
    riesgo_pct: float,
    sl_puntos: float,
    symbol: str,
    spot: float
) -> tuple[float, float, float]:
    """
    Calcula el tamaño de lote con Volatility Targeting y conversión multidivisa.
    Retorna: (lotes, riesgo_usd, tick_value_usd)
    """
    if sl_puntos <= 0:
        return 0.0, 0.0, 0.0

    riesgo_usd = capital_usd * (riesgo_pct / 100.0)
    sym = symbol.upper().strip()

    if sym == "USDCLP":
        # 1 lote = 100,000 USD. 1 punto (1 CLP de movimiento) = 100,000 CLP.
        # Valor en USD por punto = 100,000 / spot
        if spot <= 0:
            spot = 920.0
        tick_value_usd = 100000.0 / spot
    elif sym == "XAUUSD":
        # 1 lote = 100 oz. 1 dólar de movimiento = 100 USD.
        tick_value_usd = 100.0
    elif sym in ("WTI", "BRENT"):
        # 1 lote = 1,000 barriles. 1 dólar de movimiento = 1,000 USD.
        tick_value_usd = 1000.0
    elif sym == "US100":
        # 1 lote estándar CFD = 20 USD por punto (o 1 USD por punto mini)
        tick_value_usd = 20.0
    else:
        tick_value_usd = 1.0

    lotes_raw = riesgo_usd / (sl_puntos * tick_value_usd)
    lotes_ajustados = max(0.01, round(lotes_raw, 2))

    return lotes_ajustados, round(riesgo_usd, 2), round(tick_value_usd, 2)
