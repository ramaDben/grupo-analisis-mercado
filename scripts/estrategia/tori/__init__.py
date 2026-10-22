"""La estrategia de Tori Trades (doctrina: docs/metodologia-tendencias.md)."""
from __future__ import annotations

from estrategia.contrato import Etiqueta, Marcos
from estrategia.tori import lectura as _lectura
from estrategia.tori import puntaje as _puntaje
from estrategia.tori.parametros import PARAMETROS, Parametros
from estrategia.tori.procedencia import PROCEDENCIA

PARAMETROS_M15 = PARAMETROS  # marcador del contrato: la Task 1 lo reemplaza por velas_ab_min=30

MARCOS = Marcos(
    contexto=("W1", "D1"), operativo="H4",
    velas={"W1": 156, "D1": 250, "H4": 180},
    etiquetas={
        "W1": Etiqueta("contexto", "de meses"),
        "D1": Etiqueta("posicional", "de semanas"),
        "H4": Etiqueta("swing", "de una a dos semanas"),
    },
)

MARCOS_INTRADIA = Marcos(
    contexto=("W1", "D1", "H4"),
    operativo="H1",
    velas={"W1": 156, "D1": 250, "H4": 180, "H1": 600},
    etiquetas={
        "W1": Etiqueta("contexto", "de meses"),
        "D1": Etiqueta("posicional", "de semanas"),
        "H4": Etiqueta("swing", "de una a dos semanas"),
        "H1": Etiqueta("intradía", "de 8 a 10 horas"),
    },
)


class Tori:
    nombre = "tori"
    marcos = MARCOS
    procedencia = PROCEDENCIA

    def __init__(self, parametros: Parametros = PARAMETROS, marcos: Marcos = MARCOS) -> None:
        self.p = parametros
        self.marcos = marcos

    def leer(self, ticker, velas, digits, en_curso=None):
        return _lectura.leer(ticker, velas, digits, en_curso, self.marcos, self.p)

    def seguir(self, referencia, velas, digits, en_curso=None):
        return _lectura.seguir(referencia.ticker, referencia, velas, digits, en_curso,
                               self.marcos, self.p)  # lo implementa la Task S3-6

    def puntuar(self, lectura, horizonte):
        return _puntaje.puntuar(lectura, horizonte, self.p)

    def divergencia(self, preparada, actual):
        return _lectura.divergencia(preparada, actual)


def crear() -> Tori:
    return Tori()


def crear_intradia(parametros: Parametros = PARAMETROS) -> Tori:
    return Tori(parametros=parametros, marcos=MARCOS_INTRADIA)
