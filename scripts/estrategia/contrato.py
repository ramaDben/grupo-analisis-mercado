"""Contrato del enchufe de estrategia: lo que toda estrategia recibe y devuelve.

Spec §4. No importa MT5 ni ningún pipeline: los tipos se construyen igual en un
test y en producción. Las validaciones de `__post_init__` hacen imposible construir
una lectura mal formada; la batería de conformidad (`tests/estrategia_conformidad.py`)
verifica lo que no se puede ver al construir, como no mirar el futuro.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

import pandas as pd

Direccion = Literal["ALCISTA", "BAJISTA", "LATERAL"]
Estado = Literal["TENDENCIA", "REBOTE", "PRUEBA", "RUPTURA", "RANGO"]
Rol = Literal["accion", "seguridad", "seguimiento", "contexto", "objetivo", "rango"]
Horizonte = Literal["sesion", "semana"]

FLECHAS = ("⬆️", "↔️", "⬇️")
CALIDADES = ("A+", "B", "")
COLUMNAS_VELAS = ("time", "open", "high", "low", "close")


def _exigir_zona(momento: datetime, campo: str) -> None:
    if momento.tzinfo is None:
        raise ValueError(f"`{campo}` tiene que venir con zona horaria (America/Santiago)")


@dataclass(frozen=True)
class Etiqueta:
    """Cómo se le nombra un marco al cliente: "swing", "de una a dos semanas" (spec §8.1)."""

    nombre: str
    duracion: str


@dataclass(frozen=True)
class Marcos:
    """Los marcos que la estrategia pide: los de contexto y el operativo."""

    contexto: tuple[str, ...]
    operativo: str
    velas: dict[str, int]  # cuántas velas cerradas pide por marco
    etiquetas: dict[str, Etiqueta]

    def __post_init__(self) -> None:
        faltan = [m for m in self.todos if m not in self.velas or m not in self.etiquetas]
        if faltan:
            raise ValueError(f"Marcos sin velas o sin etiqueta: {faltan}")

    @property
    def todos(self) -> tuple[str, ...]:
        return (*self.contexto, self.operativo)


@dataclass(frozen=True)
class Linea:
    rol: Rol
    tipo: Literal["diagonal", "horizontal"]
    puntos: tuple[tuple[int, float], ...]  # (timestamp de la vela, precio)
    marco: str
    toques: int
    calidad: str  # "A+", "B" o ""
    valor_actual: float  # el precio de la línea en la última vela cerrada
    empinada: bool = False

    def __post_init__(self) -> None:
        esperadas = 2 if self.tipo == "diagonal" else 1
        if len(self.puntos) != esperadas:
            raise ValueError(
                f"Una línea {self.tipo} lleva {esperadas} anclas; trae {len(self.puntos)}"
            )
        if self.calidad not in CALIDADES:
            raise ValueError(f"La calidad tiene que ser una de {CALIDADES}; trae {self.calidad!r}")


@dataclass(frozen=True)
class Referencia:
    """Un nivel que la pieza nombra: el que se vigila, el que invalida o el objetivo."""

    precio: float
    etiqueta: str
    linea: Linea | None = None


@dataclass(frozen=True)
class Escenario:
    flecha: str  # "⬆️", "↔️" o "⬇️"
    condicion: str  # la condición corta: "Cierre de 4 horas sobre 4.020,00"
    texto: str  # la frase de cliente

    def __post_init__(self) -> None:
        if self.flecha not in FLECHAS:
            raise ValueError(f"La flecha tiene que ser una de {FLECHAS}; trae {self.flecha!r}")


@dataclass(frozen=True)
class VelaEnCurso:
    """La vela del marco operativo que todavía no cerró. Llega aparte de las cerradas."""

    apertura: int  # timestamp de apertura, en la misma época que las velas cerradas
    precio: float  # el último precio de esa vela
    cierre: datetime  # cuándo cierra, en America/Santiago

    def __post_init__(self) -> None:
        _exigir_zona(self.cierre, "cierre")


@dataclass(frozen=True)
class Prueba:
    linea: Linea  # la línea que el precio vivo está perforando
    valor_ahora: float  # el valor de la línea en la vela abierta
    cierre_vela: datetime  # cuándo cierra la vela del marco operativo (America/Santiago)

    def __post_init__(self) -> None:
        _exigir_zona(self.cierre_vela, "cierre_vela")


@dataclass(frozen=True)
class Lectura:
    ticker: str
    marco: str
    precio: float  # el precio vivo si hay vela en curso; si no, el último cierre
    direccion: Direccion
    estado: Estado
    lineas: tuple[Linea, ...]
    en_prueba: Prueba | None
    vigilar: Referencia
    invalidacion: Referencia | None
    objetivo: Referencia | None
    escenarios: tuple[Escenario, ...]
    salida: str
    conceptos: tuple[str, ...]
    avisos: tuple[str, ...]
    metricas: dict[str, float] = field(default_factory=dict)  # de la estrategia, para puntuar
    vela: int = 0  # timestamp de la última vela cerrada del marco operativo

    def __post_init__(self) -> None:
        flechas = [e.flecha for e in self.escenarios]
        if len(flechas) != 3 or sorted(flechas) != sorted(FLECHAS):
            raise ValueError(
                f"La lectura necesita exactamente un escenario por flecha {FLECHAS}; trae {flechas}"
            )
        if (self.estado == "PRUEBA") != (self.en_prueba is not None):
            raise ValueError("`en_prueba` va solo, y siempre, con el estado PRUEBA")


@dataclass(frozen=True)
class Puntaje:
    puntos: float
    desglose: dict[str, float]
    excluido: str | None  # motivo técnico de exclusión, en texto de motivo

    def __post_init__(self) -> None:
        if not 0.0 <= self.puntos <= 100.0:
            raise ValueError(f"El puntaje va entre 0 y 100; trae {self.puntos}")


@dataclass(frozen=True)
class Fundamento:
    regla: str
    origen: tuple[str, ...]  # quién la usa: "Tori Trades, qLtq7 [51:00]"
    canonico: tuple[str, ...]  # teoría clásica: "F3 p. 56"
    empirico: tuple[str, ...]  # evidencia medida: "F4", "F6"
    no_probado: str  # lo que la evidencia no cubre; "" solo si empirico la cubre


@dataclass(frozen=True)
class Procedencia:
    fuente_doctrina: str  # ruta relativa a la raíz del repo
    fuente_citas: str  # ruta relativa a la raíz del repo
    fundamentos: tuple[Fundamento, ...]
    modos_de_falla: tuple[str, ...]


class Estrategia(Protocol):
    nombre: str
    marcos: Marcos
    procedencia: Procedencia

    def leer(self, ticker: str, velas: dict[str, pd.DataFrame], digits: int,
             en_curso: VelaEnCurso | None = None) -> Lectura: ...

    def puntuar(self, lectura: Lectura, horizonte: Horizonte) -> Puntaje: ...

    def seguir(self, referencia: Lectura, velas: dict[str, pd.DataFrame], digits: int,
               en_curso: VelaEnCurso | None = None) -> Lectura: ...

    def divergencia(self, preparada: Lectura, actual: Lectura) -> str | None: ...


def lectura_a_dict(lectura: Lectura) -> dict[str, Any]:
    """La lectura en JSON plano: así se guarda la referencia semanal (spec §4)."""
    datos = asdict(lectura)
    if lectura.en_prueba is not None:
        datos["en_prueba"]["cierre_vela"] = lectura.en_prueba.cierre_vela.isoformat()
    return datos


def _linea_de(d: dict[str, Any]) -> Linea:
    return Linea(**{**d, "puntos": tuple((int(ts), float(pr)) for ts, pr in d["puntos"])})


def _referencia_de(d: dict[str, Any] | None) -> Referencia | None:
    if d is None:
        return None
    return Referencia(d["precio"], d["etiqueta"], _linea_de(d["linea"]) if d["linea"] else None)


def lectura_de_dict(d: dict[str, Any]) -> Lectura:
    prueba = d["en_prueba"]
    return Lectura(
        ticker=d["ticker"], marco=d["marco"], precio=d["precio"], direccion=d["direccion"],
        estado=d["estado"], lineas=tuple(_linea_de(x) for x in d["lineas"]),
        en_prueba=None if prueba is None else Prueba(
            _linea_de(prueba["linea"]), prueba["valor_ahora"],
            datetime.fromisoformat(prueba["cierre_vela"])),
        vigilar=_referencia_de(d["vigilar"]), invalidacion=_referencia_de(d["invalidacion"]),
        objetivo=_referencia_de(d["objetivo"]),
        escenarios=tuple(Escenario(**e) for e in d["escenarios"]), salida=d["salida"],
        conceptos=tuple(d["conceptos"]), avisos=tuple(d["avisos"]),
        metricas=dict(d["metricas"]), vela=int(d["vela"]),
    )


def exigir_velas(velas: dict[str, pd.DataFrame], marcos: Marcos) -> None:
    """Falla con un mensaje accionable si falta un marco, una columna o el orden."""
    for marco in marcos.todos:
        df = velas.get(marco)
        if df is None or df.empty:
            raise ValueError(f"Faltan las velas de {marco}")
        faltan = [c for c in COLUMNAS_VELAS if c not in df.columns]
        if faltan:
            raise ValueError(f"Las velas de {marco} no traen las columnas {faltan}")
        if not df["time"].is_monotonic_increasing:
            raise ValueError(f"Las velas de {marco} no vienen en orden cronológico")
