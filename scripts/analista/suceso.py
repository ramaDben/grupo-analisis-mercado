"""El suceso único del seguimiento: una línea de 15 minutos fijada al primer pedido del día.

Plan: docs/superpowers/plans/2026-10-21-seguimiento-suceso-unico.md. La línea sale de la lectura
de 15 minutos (A+ con la regla del indicador del director; sin A+, la mejor B) y se evalúa contra
el cierre de las velas de 5 minutos. El suceso no se reemplaza en el día: una ruptura es su estado.
"""
from __future__ import annotations

import json
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from estrategia.contrato import SCL, Lectura, Linea
from estrategia.tori import PARAMETROS_M15
from estrategia.tori.parametros import Parametros
from referencia_diaria import fecha_de
from referencia_semanal import slug

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
    if lectura.direccion == "LATERAL" or lectura.estado == "RANGO" or lectura.vigilar.linea is None:
        return None

    linea = lectura.vigilar.linea
    t_ref = tiempos_m15[-1]
    valor_ref = linea.valor_actual

    if linea.tipo == "horizontal":
        pendiente = 0.0
    else:
        (t1, p1), (t2, p2) = linea.puntos
        if t1 not in tiempos_m15 or t2 not in tiempos_m15:
            raise ValueError(f"Anclas {t1} o {t2} no encontradas en tiempos_m15")
        i1 = tiempos_m15.index(t1)
        i2 = tiempos_m15.index(t2)
        if i2 == i1:
            raise ValueError("Las dos anclas de la línea diagonal tienen el mismo índice de tiempo")
        pendiente = (p2 - p1) / (i2 - i1)

    objetivo = lectura.objetivo.precio if lectura.objetivo is not None else None
    calidad = linea.calidad
    tolerancia = p.tolerancia_toque_atr * lectura.metricas["atr"]

    return Suceso(
        ticker=ticker,
        fecha=fecha,
        fijado=fijado,
        sentido=lectura.direccion,
        t_ref=t_ref,
        valor_ref=valor_ref,
        pendiente=pendiente,
        objetivo=objetivo,
        calidad=calidad,
        tolerancia=tolerancia,
    )


def valor_en(s: Suceso, tiempos_m15: Sequence[int], ts: int) -> float:
    """Valor de la línea del suceso en el instante `ts` (época del servidor)."""
    k = bisect_right(tiempos_m15, ts) - 1
    if k < 0:
        raise ValueError(f"ts {ts} es anterior al inicio de tiempos_m15 ({tiempos_m15[0]})")

    frac = (ts - tiempos_m15[k]) / VELA_M15_S
    if k < len(tiempos_m15) - 1:
        frac = min(1.0, frac)
    idx_ts = k + frac

    k_ref = bisect_right(tiempos_m15, s.t_ref) - 1
    if k_ref < 0:
        raise ValueError(f"t_ref {s.t_ref} no se encuentra en tiempos_m15")
    frac_ref = (s.t_ref - tiempos_m15[k_ref]) / VELA_M15_S
    if k_ref < len(tiempos_m15) - 1:
        frac_ref = min(1.0, frac_ref)
    idx_ref = k_ref + frac_ref

    return s.valor_ref + s.pendiente * (idx_ts - idx_ref)


def evaluar(s: Suceso, velas_m5: Sequence[Mapping[str, float]], precio: float,
            tiempos_m15: Sequence[int]) -> Avance:
    """En qué va el suceso según los cierres de 5 minutos posteriores a su fijación."""
    velas_validas = [v for v in velas_m5 if v["time"] >= s.t_ref + VELA_M15_S]
    velas_validas.sort(key=lambda v: v["time"])

    alcista = (s.sentido == "ALCISTA")
    toco = False
    ultima_L: float | None = None

    for v in velas_validas:
        time = int(v["time"])
        close = float(v["close"])
        high = float(v["high"])
        low = float(v["low"])
        L = valor_en(s, tiempos_m15, time + VELA_M5_S)
        ultima_L = L

        if alcista:
            if close < L:
                return Avance(estado="ruptura", valor_linea=L)
            if low <= L + s.tolerancia:
                toco = True
            if toco and s.objetivo is not None and high >= s.objetivo:
                return Avance(estado="cumplido", valor_linea=L)
        else:
            if close > L:
                return Avance(estado="ruptura", valor_linea=L)
            if high >= L - s.tolerancia:
                toco = True
            if toco and s.objetivo is not None and low <= s.objetivo:
                return Avance(estado="cumplido", valor_linea=L)

    if ultima_L is None:
        ultima_L = valor_en(s, tiempos_m15, s.t_ref + VELA_M15_S)

    if abs(precio - ultima_L) <= s.tolerancia:
        return Avance(estado="en_nivel", valor_linea=ultima_L)
    if toco:
        return Avance(estado="rebotando", valor_linea=ultima_L)
    return Avance(estado="esperando", valor_linea=ultima_L)


def linea(s: Suceso, tiempos_m15: Sequence[int]) -> Linea:
    """La línea FIJADA del suceso, para dibujarla desde la vela de la fijación.

    Se arma desde el suceso y no desde la lectura del momento: si a mediodía el motor ve otra
    línea, la lámina tiene que seguir trazando la que se fijó en la mañana.
    """
    if s.pendiente == 0.0:
        return Linea("seguridad", "horizontal", ((s.t_ref, s.valor_ref),), "M15", 0, s.calidad, s.valor_ref)
    if s.t_ref not in tiempos_m15:
        raise ValueError(f"{s.ticker}: la vela de la fijación ya no está en la ventana de 15 minutos")
    k = list(tiempos_m15).index(s.t_ref)
    if k == len(tiempos_m15) - 1:  # todavía no cerró otra vela: la segunda ancla va una vela atrás
        puntos = ((tiempos_m15[k - 1], s.valor_ref - s.pendiente), (s.t_ref, s.valor_ref))
    else:
        puntos = ((s.t_ref, s.valor_ref), (tiempos_m15[-1], s.valor_ref + s.pendiente * (len(tiempos_m15) - 1 - k)))
    return Linea("seguridad", "diagonal", puntos, "M15", 0, s.calidad, puntos[-1][1])


def ruta(fecha: str, ticker: str, base: Path = DIR_SUCESOS) -> Path:
    """Dónde vive el suceso de un activo en un día: `<base>/<AAAA-MM-DD>/<slug>.json`."""
    return base / fecha / f"{slug(ticker)}.json"


def guardar(s: Suceso, base: Path = DIR_SUCESOS) -> Path:
    destino = ruta(s.fecha, s.ticker, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(asdict(s), ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def cargar(fecha: str, ticker: str, base: Path = DIR_SUCESOS) -> Suceso | None:
    archivo = ruta(fecha, ticker, base)
    if not archivo.is_file():
        return None
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        return Suceso(**datos)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def del_dia(lectura: Lectura, tiempos_m15: Sequence[int], ticker: str, ahora: datetime,
            base: Path = DIR_SUCESOS) -> Suceso | None:
    """El suceso de hoy: el guardado si existe; si no, se elige y se guarda (sin dirección no escribe)."""
    fecha = fecha_de(ahora)
    guardado = cargar(fecha, ticker, base)
    if guardado is not None:
        return guardado

    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=SCL)
    fijado = ahora.astimezone(SCL).isoformat(timespec="minutes")

    s = elegir(lectura, tiempos_m15, ticker, fecha, fijado)
    if s is None:
        return None

    guardar(s, base)
    return s
