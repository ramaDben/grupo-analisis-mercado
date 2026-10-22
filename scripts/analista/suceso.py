"""El suceso único del seguimiento: una línea de 15 minutos fijada al primer pedido del día.

Plan: docs/superpowers/plans/2026-10-21-seguimiento-suceso-unico.md. La línea sale de la lectura
de 15 minutos (A+ con la regla del indicador del director; sin A+, la mejor B) y se evalúa contra
el cierre de las velas de 5 minutos. El suceso no se reemplaza en el día: una ruptura es su estado.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from estrategia.contrato import Lectura
from estrategia.tori import PARAMETROS_M15
from estrategia.tori.parametros import Parametros

RAIZ = Path(__file__).resolve().parents[2]
DIR_SUCESOS = RAIZ / "data" / "sucesos_diarios"
VELA_M15_S, VELA_M5_S = 900, 300

EstadoAvance = Literal["esperando", "en_nivel", "rebotando", "cumplido", "ruptura"]
EstadoResumen = Literal["esperando", "en_nivel", "rebotando", "cumplido", "ruptura", "sin_direccion", "cerrado"]


@dataclass(frozen=True)
class Suceso:
    ticker: str
    fecha: str  # AAAA-MM-DD, America/Santiago
    fijado: str  # ISO a minutos, America/Santiago
    sentido: Literal["ALCISTA", "BAJISTA"]
    t_ref: int  # apertura de la última vela M15 cerrada al fijar (época del servidor)
    valor_ref: float  # valor de la línea en esa vela (Linea.valor_actual)
    pendiente: float  # precio por vela de 15 minutos; 0.0 en un horizontal
    objetivo: float | None
    calidad: str  # "A+" o "B"
    tolerancia: float  # Parametros.tolerancia_toque_atr x ATR de 15 minutos


@dataclass(frozen=True)
class Avance:
    estado: EstadoAvance
    valor_linea: float  # valor de la línea en la última vela de 5 minutos evaluada


@dataclass(frozen=True)
class Resumen:
    """Lo que la integración arma y los textos convierten en lámina y WhatsApp."""

    estado: EstadoResumen
    sentido: Literal["ALCISTA", "BAJISTA"] | None
    nivel: float | None
    objetivo: float | None
    siguiente: float | None  # solo en ruptura: el nivel a vigilar de la lectura nueva
    calidad: str
    nota_semana: str  # "" cuando no hace falta


def elegir(lectura: Lectura, tiempos_m15: Sequence[int], ticker: str, fecha: str, fijado: str,
           p: Parametros = PARAMETROS_M15) -> Suceso | None:
    """El suceso de la lectura de 15 minutos, o None si no marca dirección."""
    raise NotImplementedError


def valor_en(s: Suceso, tiempos_m15: Sequence[int], ts: int) -> float:
    """Valor de la línea del suceso en el instante `ts` (época del servidor)."""
    raise NotImplementedError


def evaluar(s: Suceso, velas_m5: Sequence[Mapping[str, float]], precio: float,
            tiempos_m15: Sequence[int]) -> Avance:
    """En qué va el suceso según los cierres de 5 minutos posteriores a su fijación."""
    raise NotImplementedError


def guardar(s: Suceso, base: Path = DIR_SUCESOS) -> Path:
    raise NotImplementedError


def cargar(fecha: str, ticker: str, base: Path = DIR_SUCESOS) -> Suceso | None:
    raise NotImplementedError


def del_dia(lectura: Lectura, tiempos_m15: Sequence[int], ticker: str, ahora: datetime,
            base: Path = DIR_SUCESOS) -> Suceso | None:
    """El suceso de hoy: el guardado si existe; si no, se elige y se guarda (sin dirección no escribe)."""
    raise NotImplementedError
