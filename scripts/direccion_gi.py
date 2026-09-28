#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dirección técnica de cuatro ejes. Fase 1: se calcula en sombra y se mide.

**El problema que cierra.** La dirección de toda pieza era una sola línea
(`screener_gi.direccion_tecnica`: precio contra la EMA 50 de H1). Nunca decía
LATERAL, no distinguía una corrección de un cambio de tendencia y no informaba
convicción.

**Ejes independientes, no votos.** EMA, MACD y RSI salen del mismo cierre
suavizado: si votaran juntos, "4 de 4" sería la misma señal contada cuatro
veces, que es la confianza inflada que hundió al Playbook V2. Cada eje mide algo
distinto y los combina un árbol explícito, cuya rama **es** el motivo que lee el
cliente:

1. Fondo (D1): precio contra `ema_50` y `ema_50` contra `ema_100`. Es el ancla.
2. Día (H1): precio contra `ema_50`, con histéresis, más la posición en el
   Donchian 50, que confirma el lado.
3. Fuerza (`adx_14` de H1): decide LATERAL, la convicción y el desempate de la
   corrección. **No vota dirección**, porque sube igual en una caída.
4. Espacio (consumo de ATR diario): **solo texto**. Ya pesa en el escáner como
   gate y como factor, y usarlo acá también lo contaría tres veces.

Los umbrales viven en `config/direccion.json` y en esta fase son fijos. Un test
impide que aparezcan escritos acá.

Spec: docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "direccion.json"

ALCISTA = "ALCISTA"
BAJISTA = "BAJISTA"
LATERAL = "LATERAL"
TRANSICION = "TRANSICION"


@lru_cache(maxsize=1)
def _cfg() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def umbrales() -> dict[str, float]:
    return {k: float(v["valor"]) for k, v in _cfg()["umbrales"].items()}


def _num(d: dict[str, Any], campo: str) -> float | None:
    """El campo como número finito, o `None`.

    `None`, `NaN`, infinito o un booleano cuentan como ausentes: el ADX da `NaN`
    en una serie plana, y comparar contra `NaN` devuelve `False` en silencio en
    vez de avisar que falta el dato.
    """
    v = d.get(campo)
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def posicion_canal(h1: dict[str, Any]) -> float | None:
    """Dónde está el precio dentro del Donchian 50 de H1.

    El canal es de velas cerradas, así que en un quiebre `p` sale de [0, 1]:
    `p > 1` es un precio sobre el máximo de 50 velas y `p < 0` bajo el mínimo. Es
    un estado válido. Sin ancho de canal no hay posición.
    """
    precio = _num(h1, "price")
    alto = _num(h1, "donchian_50_high")
    bajo = _num(h1, "donchian_50_low")
    if precio is None or alto is None or bajo is None or alto <= bajo:
        return None
    return (precio - bajo) / (alto - bajo)


def eje_fondo(d1: dict[str, Any]) -> str | None:
    precio = _num(d1, "price")
    e50 = _num(d1, "ema_50")
    e100 = _num(d1, "ema_100")
    if precio is None or e50 is None or e100 is None:
        return None
    if precio > e50 and e50 > e100:
        return ALCISTA
    if precio < e50 and e50 < e100:
        return BAJISTA
    return TRANSICION


def eje_dia(h1: dict[str, Any], previa: str | None = None) -> str:
    """El lado del precio contra la EMA 50 de H1. Nunca LATERAL.

    Con `previa`, solo cambia de lado si el precio cruza la media por **más de**
    `histeresis_atr` x ATR 14 de H1. Sin `previa` (o sin ATR) se lee sin
    histéresis, y el empate exacto se resuelve alcista, igual que
    `direccion_tecnica`.
    """
    precio = _num(h1, "price")
    e50 = _num(h1, "ema_50")
    if precio is None or e50 is None:
        raise ValueError("H1 sin price o ema_50: no hay dirección que leer")
    atr = _num(h1, "atr_14")
    if previa is not None and atr is not None:
        banda = umbrales()["histeresis_atr"] * atr
        if previa == ALCISTA:
            return BAJISTA if precio < e50 - banda else ALCISTA
        return ALCISTA if precio > e50 + banda else BAJISTA
    return ALCISTA if precio >= e50 else BAJISTA


def canal_confirma(lado: str, p: float) -> bool:
    u = umbrales()
    if lado == ALCISTA:
        return p >= u["p_confirma_alcista"]
    return p <= u["p_confirma_bajista"]


def consumo_diario(d1: dict[str, Any], hoy: str | None = None) -> float | None:
    """`rango_hoy / atr_14` de D1, con la regla de `fecha_barra` del escáner.

    Si la vela D1 es de un día anterior a `hoy` (fecha ISO de Santiago), el
    mercado todavía no registra la jornada y el consumo es 0: la misma regla que
    `screener_gi.gate_agotamiento`.
    """
    fecha = d1.get("fecha_barra")
    if hoy and fecha and str(fecha) < hoy:
        return 0.0
    atr = _num(d1, "atr_14")
    rango = _num(d1, "rango_hoy")
    if atr is None or rango is None or atr <= 0:
        return None
    return rango / atr
