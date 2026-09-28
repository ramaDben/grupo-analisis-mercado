#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Medición histórica de la dirección de cuatro ejes contra la EMA 50 sola.

Fase 1 del spec `docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md`
(§5). Recorre las series de `data central/DATA PRECIOS OHLC/`, arma en cada vela
H1 los mismos dicts que entrega `analizar_activo` (indicadores de velas
cerradas, `rango_hoy` reconstruido sin fuga) y aplica la regla de adopción
fijada antes de ver los números.

**Las marcas son hora de Santiago aunque el sello diga UTC** (medido el
2026-09-28). La medición no deriva un desfase constante: interpreta cada marca
como `America/Santiago`, la convierte con `zoneinfo`, verifica la hipótesis con
dos pruebas y aborta si alguna falla.

Uso:
    uv run python scripts/medir_direccion.py
    uv run python scripts/medir_direccion.py --series XAUUSD USDCLP
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
for _p in (SRC, RAIZ / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import agenda_mercado as agenda  # noqa: E402
import direccion_gi as dg  # noqa: E402
from guardrails.cuenta import cuenta_correcta  # noqa: E402
from market_data_mcp.mt5_client import adx, atr, ema  # noqa: E402

DIR_SERIES = RAIZ / "data central" / "DATA PRECIOS OHLC"
DIR_SALIDA = RAIZ / "docs" / "mediciones"
SANTIAGO = ZoneInfo("America/Santiago")
NY = ZoneInfo("America/New_York")
COLUMNAS = ["time", "open", "high", "low", "close", "tick_volume"]


class MedicionAbortada(RuntimeError):
    """La medición no puede seguir sin mentir: se detiene con el detalle."""


@lru_cache(maxsize=1)
def cfg_medicion() -> dict[str, Any]:
    return json.loads(dg.CONFIG.read_text(encoding="utf-8"))["medicion"]


def valor(clave: str) -> Any:
    return cfg_medicion()[clave]["valor"]


# ─────────────────────────────────────────────────────────────────────────────
# Carga y sellos
# ─────────────────────────────────────────────────────────────────────────────
def cargar_serie(simbolo: str, marco: str, directorio: Path = DIR_SERIES) -> tuple[pd.DataFrame, dict[str, Any]]:
    """La serie ordenada, o `MedicionAbortada` si no salió de MT5 y de la cuenta declarada."""
    ruta = directorio / f"{simbolo}_{marco}.json"
    if not ruta.exists():
        raise MedicionAbortada(f"falta {ruta.name}: corre el extractor antes de medir")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    meta = {k: v for k, v in datos.items() if k != "rows"}
    if meta.get("source") != "MT5" or meta.get("broker") != "MT5":
        raise MedicionAbortada(
            f"{ruta.name}: la serie no salio de MT5 (source={meta.get('source')}, broker={meta.get('broker')})"
        )
    veredicto = cuenta_correcta(meta.get("cuenta"), ubicacion=ruta.name)
    if not veredicto.ok:
        raise MedicionAbortada(f"{ruta.name}: {veredicto.detalle}")
    df = pd.DataFrame(datos["rows"])[COLUMNAS]
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time", kind="stable").reset_index(drop=True), meta


# ─────────────────────────────────────────────────────────────────────────────
# Zona horaria (spec §5.4)
# ─────────────────────────────────────────────────────────────────────────────
def localizar(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `time_ny` leyendo cada marca como hora de Santiago.

    Las horas ambiguas (la que se repite en abril) y las inexistentes (la que
    falta en septiembre) quedan en `NaT`: resolverlas por el orden de las filas
    sería suponer algo que el archivo no dice. Marca, no borra, para que los
    indicadores sigan viendo todas las velas.
    """
    out = df.copy()
    local = out["time"].dt.tz_localize(SANTIAGO, ambiguous="NaT", nonexistent="NaT")
    out["time_ny"] = local.dt.tz_convert(NY)
    return out


def prueba_hora_extraccion(df: pd.DataFrame, meta: dict[str, Any]) -> dict[str, Any]:
    """La última vela cae dentro de la hora de extracción, leída en Santiago.

    Solo aplica a las series cuyo mercado estaba abierto al extraer (última vela
    del mismo día que la extracción). Las demás no dicen nada de la zona.
    """
    extraccion = datetime.fromisoformat(meta["as_of_utc"]).astimezone(SANTIAGO).replace(tzinfo=None)
    ultima = pd.Timestamp(df["time"].iloc[-1]).to_pydatetime()
    if ultima.date() != extraccion.date():
        return {"aplica": False, "ok": None,
                "detalle": f"ultima vela {ultima:%Y-%m-%d %H:%M}, extraida {extraccion:%Y-%m-%d %H:%M}: mercado cerrado"}
    ok = ultima <= extraccion < ultima + timedelta(hours=1)
    return {"aplica": True, "ok": ok,
            "detalle": f"ultima vela {ultima:%H:%M}, extraccion {extraccion:%H:%M} (Santiago)"}


def prueba_moda_volumen(df_loc: pd.DataFrame) -> dict[str, Any]:
    """La moda mensual de la hora NY de la vela de mayor volumen es la misma todos los meses."""
    d = df_loc.dropna(subset=["time_ny"]).copy()
    d = d[d["time_ny"].dt.weekday < 5]
    d["dia"] = d["time_ny"].dt.date
    picos = d.loc[d.groupby("dia")["tick_volume"].idxmax()].copy()
    picos["mes"] = picos["time_ny"].dt.strftime("%Y-%m")
    picos["hora"] = picos["time_ny"].dt.hour
    horas = picos.groupby("mes")["hora"].agg(lambda s: int(s.mode().iloc[0]))
    ok = len(horas) > 0 and horas.nunique() == 1
    return {"ok": bool(ok), "hora": int(horas.iloc[0]) if ok else None,
            "horas_por_mes": {k: int(v) for k, v in horas.items()}}


def verificar_zona(cargadas: dict[str, tuple[pd.DataFrame, dict[str, Any]]], serie_moda: str) -> dict[str, Any]:
    """Las dos pruebas de §5.4. Aborta si alguna falla o si ninguna serie permite la primera."""
    extraccion = {s: prueba_hora_extraccion(df, meta) for s, (df, meta) in cargadas.items()}
    aplican = {s: r for s, r in extraccion.items() if r["aplica"]}
    if not aplican:
        raise MedicionAbortada("ninguna serie tenia el mercado abierto al extraer: no se puede verificar la zona")
    fallan = {s: r["detalle"] for s, r in aplican.items() if not r["ok"]}
    if fallan:
        raise MedicionAbortada(f"la ultima vela no cae en la hora de extraccion: {fallan}")
    if serie_moda not in cargadas:
        raise MedicionAbortada(f"falta {serie_moda} para la prueba de volumen")
    moda = prueba_moda_volumen(localizar(cargadas[serie_moda][0]))
    if not moda["ok"]:
        raise MedicionAbortada(f"la hora NY del pico de volumen de {serie_moda} cambia entre meses: {moda['horas_por_mes']}")
    return {"extraccion": extraccion, "moda_volumen": {serie_moda: moda}}
