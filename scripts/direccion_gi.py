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
from dataclasses import asdict, dataclass, field
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


@dataclass(frozen=True)
class LecturaDireccion:
    direccion: str
    conviccion: str | None
    fase: str
    sin_recorrido: bool
    eje2: str
    motivo: str
    ejes: dict[str, Any] = field(default_factory=dict)


def a_dict(lectura: LecturaDireccion) -> dict[str, Any]:
    return asdict(lectura)


_HACIA = {ALCISTA: "al alza", BAJISTA: "a la baja"}
_SUBE = {ALCISTA: "sube", BAJISTA: "baja"}
_TENDENCIA = {ALCISTA: "alcista", BAJISTA: "bajista"}
_VIGILA = {ALCISTA: "el soporte", BAJISTA: "la resistencia"}


def _motivo(direccion: str, fase: str, fondo: str | None, sin_recorrido: bool) -> str:
    """Una línea en voz de cliente: la rama del árbol dicha en simple.

    Sin guion largo, sin cifras de precio y en tuteo chileno neutro.
    """
    if fase == "rango":
        texto = ("Se mueve de lado: no tiene fuerza de tendencia y está en la zona "
                 "media de su canal de las últimas cincuenta horas.")
    elif fase == "tendencia_alineada":
        texto = f"La tendencia de fondo y la del día van {_HACIA[direccion]}."
    elif fase == "correccion_con_fuerza":
        texto = (f"Hoy {_SUBE[direccion]} con fuerza, contra la tendencia de fondo, "
                 f"que sigue {_HACIA[fondo]}.")
    elif fase == "correccion":
        texto = (f"Corrige dentro de una tendencia {_TENDENCIA[direccion]}: se vigila "
                 f"{_VIGILA[direccion]} para retomar.")
    elif fase == "sin_ancla":
        texto = f"Hoy {_SUBE[direccion]}, pero la tendencia de fondo todavía no define dirección."
    else:
        texto = (f"La lectura de la hora va {_HACIA[direccion]}, pero falta información "
                 "para contrastarla con la tendencia de fondo.")
    if sin_recorrido:
        texto += " Ojo: ya recorrió buena parte de su movimiento típico del día."
    return texto


def _faltantes(h1: dict[str, Any], d1: dict[str, Any], p: float | None) -> list[str]:
    """Los campos que impiden una lectura completa, con el marco de cada uno."""
    faltan = [f"h1.{c}" for c in ("adx_14", "donchian_50_high", "donchian_50_low") if _num(h1, c) is None]
    bordes = _num(h1, "donchian_50_high") is not None and _num(h1, "donchian_50_low") is not None
    if p is None and bordes:
        faltan.append("h1.donchian_50 sin ancho")
    faltan += [f"d1.{c}" for c in ("price", "ema_50", "ema_100") if _num(d1, c) is None]
    return faltan


def leer_direccion(
    h1: dict[str, Any],
    d1: dict[str, Any],
    previa: str | None = None,
    *,
    hoy: str | None = None,
) -> LecturaDireccion:
    """La dirección de cuatro ejes. Gana la primera rama que calce (spec §3.1).

    `previa` es el `eje2` de la lectura anterior (ALCISTA o BAJISTA), nunca la
    `direccion`, que puede ser LATERAL. La función no guarda estado.
    `hoy` (fecha ISO de Santiago) activa la regla de `fecha_barra` del consumo.
    """
    if previa is not None and previa not in (ALCISTA, BAJISTA):
        raise ValueError(f"previa tiene que ser ALCISTA o BAJISTA (el eje2), no {previa!r}")
    u = umbrales()
    dia = eje_dia(h1, previa)
    p = posicion_canal(h1)
    adx = _num(h1, "adx_14")
    fondo = eje_fondo(d1)
    consumo = consumo_diario(d1, hoy)
    sin_rec = consumo is not None and consumo >= u["consumo_sin_recorrido"]
    ejes: dict[str, Any] = {"fondo": fondo, "dia": dia, "p": p, "adx": adx, "consumo": consumo}

    def lectura(direccion: str, conviccion: str | None, fase: str) -> LecturaDireccion:
        return LecturaDireccion(
            direccion=direccion, conviccion=conviccion, fase=fase,
            sin_recorrido=sin_rec, eje2=dia,
            motivo=_motivo(direccion, fase, fondo, sin_rec), ejes=ejes,
        )

    faltan = _faltantes(h1, d1, p)
    if faltan:                                                     # rama 0
        ejes["faltan"] = faltan
        return lectura(dia, "debil", "datos_incompletos")
    if adx < u["adx_rango"] and u["p_rango_min"] <= p <= u["p_rango_max"]:   # rama 1
        return lectura(LATERAL, None, "rango")
    if fondo == TRANSICION:                                        # rama 4
        return lectura(dia, "debil", "sin_ancla")
    if fondo == dia:                                               # rama 2
        if adx >= u["adx_fuerza"]:
            conviccion = "fuerte" if canal_confirma(dia, p) else "moderada"
        elif adx >= u["adx_rango"]:
            conviccion = "moderada"
        else:
            conviccion = "debil"
        return lectura(dia, conviccion, "tendencia_alineada")
    if adx >= u["adx_fuerza"]:                                     # rama 3a
        return lectura(dia, "moderada", "correccion_con_fuerza")
    return lectura(fondo, "debil", "correccion")                   # rama 3b
