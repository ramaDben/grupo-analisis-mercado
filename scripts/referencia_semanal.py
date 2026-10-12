"""La referencia semanal: lo que fijó el análisis del lunes, por activo (spec §4).

Guardarla y reemplazarla es infraestructura; la estrategia solo la lee con `seguir()`.
Es historia de lo que el cliente leyó, así que se versiona igual que
`data/historial_despachos.json`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from estrategia.contrato import SCL, Lectura, Marcos, VelaEnCurso, lectura_a_dict, lectura_de_dict

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "referencias_semanales"
MANIFIESTO = "_semana.json"
EXTRA = 60  # velas de más para que las anclas del lunes sigan dentro (sesiones.md, S4)
Lector = Callable[[str, Marcos, int], tuple[dict[str, pd.DataFrame], VelaEnCurso | None]]


def semana_de(momento: datetime) -> str:
    """La semana ISO de la fecha de Santiago: el lunes del cliente, no el de UTC."""
    año, semana, _ = momento.astimezone(SCL).date().isocalendar()
    return f"{año}-W{semana:02d}"


def slug(ticker: str) -> str:
    return ticker.lower().replace(".spot", "").replace("#", "").replace("/", "")


def ruta(semana: str, ticker: str, base: Path = DIR) -> Path:
    return base / semana / f"{slug(ticker)}.json"


def guardar(lectura: Lectura, semana: str, motivo: str, ahora: datetime, base: Path = DIR) -> Path:
    if lectura.estado == "PRUEBA":
        raise ValueError(f"{lectura.ticker}: una referencia no se guarda en PRUEBA; se lee con en_curso=None")
    destino = ruta(semana, lectura.ticker, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = {"ticker": lectura.ticker, "semana": semana, "motivo": motivo,
             "guardada": ahora.astimezone(SCL).isoformat(timespec="minutes"),
             "lectura": lectura_a_dict(lectura)}
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def cargar(semana: str, ticker: str, base: Path = DIR) -> Lectura | None:
    origen = ruta(semana, ticker, base)
    if not origen.exists():
        return None
    return lectura_de_dict(json.loads(origen.read_text(encoding="utf-8"))["lectura"])


def manifiesto(semana: str, base: Path = DIR) -> dict[str, Any] | None:
    origen = base / semana / MANIFIESTO
    return json.loads(origen.read_text(encoding="utf-8")) if origen.exists() else None


def guardar_manifiesto(semana: str, datos: dict[str, Any], base: Path = DIR) -> Path:
    destino = base / semana / MANIFIESTO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def firma(lectura: Lectura) -> tuple:
    """La estructura de la lectura: qué línea cumple qué papel y dónde está anclada.

    El objetivo no es estructura: la diaria lo cambia cuando el precio ya lo pasó, y eso no
    termina la tesis.
    """
    return tuple(sorted((x.rol, x.tipo, x.marco, x.puntos) for x in lectura.lineas if x.rol != "objetivo"))


def debe_reemplazar(referencia: Lectura, actual: Lectura) -> bool:
    """La tesis del lunes terminó: una línea se rompió por cierre o la estrategia volvió a trazar.

    No lee los avisos ni las métricas de la estrategia: compara la estructura, que es
    parte del contrato. Entre TENDENCIA, REBOTE y PRUEBA la estructura no cambia.
    """
    if firma(referencia) != firma(actual):
        return True
    return actual.estado == "RUPTURA" and referencia.estado != "RUPTURA"


class SinReferencia(LookupError):
    """El activo no tiene referencia esta semana: no sale en las diarias (spec §4)."""


@dataclass(frozen=True)
class Diaria:
    lectura: Lectura  # la que se publica hoy
    reemplazo: Lectura | None  # la nueva referencia, si la del lunes caducó
    avisos: tuple[str, ...]
    velas: dict[str, pd.DataFrame]
    referencia: Lectura | None = None  # contra la que se leyó: el despacho vuelve a seguir esa


def lectura_del_dia(estrategia, ticker: str, digits: int, semana: str, lector: Lector,
                    base: Path = DIR) -> Diaria:
    """La lectura de hoy contra la referencia de la semana, y su reemplazo si caducó.

    No guarda nada: quien publica decide si persiste el reemplazo (el escáner sí, el
    despacho no). La nueva referencia se lee sin vela en curso, porque una referencia
    nunca queda en PRUEBA.
    """
    referencia = cargar(semana, ticker, base)
    if referencia is None:
        raise SinReferencia(f"{ticker} no tiene referencia en {semana}")
    velas, en_curso = lector(ticker, estrategia.marcos, EXTRA)
    try:
        actual = estrategia.seguir(referencia, velas, digits, en_curso)
    except ValueError as exc:
        actual = estrategia.leer(ticker, velas, digits, en_curso)
        nueva = estrategia.leer(ticker, velas, digits, None)
        return Diaria(actual, nueva, (
            f"{ticker}: la referencia de la semana no se pudo seguir ({exc}); se leyó de nuevo "
            "y esa lectura pasa a ser la nueva referencia",), velas, nueva)
    if debe_reemplazar(referencia, actual):
        nueva = estrategia.leer(ticker, velas, digits, None)
        return Diaria(actual, nueva, (
            f"{ticker}: la lectura de la semana cambió de estructura ({referencia.estado.lower()} a "
            f"{actual.estado.lower()}); la lectura de este cierre pasa a ser la nueva referencia",), velas,
            referencia)
    return Diaria(actual, None, (), velas, referencia)


def lectura_actual(estrategia, ticker: str, digits: int, lector, ahora: datetime,
                 base: Path | None = None, referencia=None):
    """La lectura del día de un activo: contra la referencia de la semana, como el escáner.

    La usan el despacho, el informe, Avisos y la tool `get_lectura`. Con `referencia` (la
    que guardó la pieza al prepararse) se sigue esa; si no, la de la semana; y si el activo
    no tiene, se lee de nuevo. No guarda reemplazos: eso es solo del escáner.
    """
    base = base or DIR
    if referencia is not None:
        # La pieza se escribió contra esta referencia: se vuelve a seguir la misma.
        velas, en_curso = lector(ticker, estrategia.marcos, EXTRA)
        try:
            return estrategia.seguir(referencia, velas, digits, en_curso), velas
        except ValueError:
            return estrategia.leer(ticker, velas, digits, en_curso), velas
    try:
        diaria = lectura_del_dia(estrategia, ticker, digits, semana_de(ahora), lector, base=base)
        return diaria.lectura, diaria.velas
    except SinReferencia:
        velas, en_curso = lector(ticker, estrategia.marcos, EXTRA)
        return estrategia.leer(ticker, velas, digits, en_curso), velas
