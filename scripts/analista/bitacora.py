"""Bitácora de los planes entregados: rastro ante un reclamo y base de un historial honesto.

Se versiona: es historia de lo que el equipo recibió, no estado generado, mismo
criterio que la bitácora de envíos del carrusel. Una entrada por informe con
plan; el desenlace se completa después con `bot_analistas.py --desenlaces`.

El desenlace se mide desde la vela posterior a la que se usó al preparar
(`vela`), y no desde la hora del reloj: las marcas de MT5 vienen en hora del
servidor, y compararlas con la hora de Chile movería la entrada varias velas.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from analista import RAIZ

RUTA = RAIZ / "data" / "bitacora_planes_analistas.json"
ESPERA = timedelta(hours=24)


def _leer(ruta: Path) -> list[dict[str, Any]]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def anotar(pieza: dict[str, Any], html: Path, analista: str, ahora: datetime, ruta: Path = RUTA) -> bool:
    """Una entrada por informe con plan. Devuelve False si la pieza no trae plan."""
    plan = pieza["datos"].get("plan") or {}
    if not plan.get("hay_plan"):
        return False
    entradas = _leer(ruta)
    entradas.append({
        "creada": ahora.isoformat(),
        "ticker": pieza["datos"]["ticker"],
        "alcista": plan["sesgo"] == "Alcista",
        "gatillo": plan["niveles"]["gatillo"],
        "invalidacion": plan["niveles"]["invalidacion"],
        "vela": plan["niveles"]["vela"],
        "estadistica": plan["estadistica"],
        "analista": analista,
        "huella_html": hashlib.sha256(html.read_bytes()).hexdigest(),
        "desenlace": None,
    })
    _escribir(ruta, entradas)
    return True


def _evaluar(e: dict[str, Any], df: pd.DataFrame) -> str:
    """¿Cruzó el gatillo en las 24 velas siguientes? Si cruzó, ¿qué tocó primero?"""
    from analista.estadistica import HORIZONTE, desenlace, indicadores

    tiempos = pd.to_datetime(df["time"])
    posteriores = [int(i) for i in df.index[tiempos > pd.Timestamp(e["vela"])]][:HORIZONTE]
    ind = indicadores(df)
    for i in posteriores:
        cierre = float(df["close"].iat[i])
        if (cierre > e["gatillo"]) if e["alcista"] else (cierre < e["gatillo"]):
            return "activado_" + desenlace(df, i, e["alcista"], ind)
    return "no_se_activo"


def completar(serie: Callable[[str], pd.DataFrame], ahora: datetime, ruta: Path = RUTA) -> int:
    """Completa el desenlace de las entradas de más de 24 h. Devuelve cuántas completó."""
    entradas, completadas = _leer(ruta), 0
    for e in entradas:
        if e["desenlace"] is None and ahora - datetime.fromisoformat(e["creada"]) > ESPERA:
            e["desenlace"] = _evaluar(e, serie(e["ticker"]))
            completadas += 1
    if completadas:
        _escribir(ruta, entradas)
    return completadas
