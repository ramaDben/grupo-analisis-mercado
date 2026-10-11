"""La estrategia de Tori Trades (doctrina: docs/metodologia-tendencias.md)."""
from __future__ import annotations

from estrategia.contrato import Etiqueta, Marcos
from estrategia.tori import lectura as _lectura
from estrategia.tori import puntaje as _puntaje
from estrategia.tori.parametros import PARAMETROS, Parametros
from estrategia.tori.procedencia import PROCEDENCIA

MARCOS = Marcos(
    contexto=("W1", "D1"), operativo="H4",
    velas={"W1": 156, "D1": 250, "H4": 180},
    etiquetas={
        "W1": Etiqueta("contexto", "de meses"),
        "D1": Etiqueta("posicional", "de semanas"),
        "H4": Etiqueta("swing", "de una a dos semanas"),
    },
)


class Tori:
    nombre = "tori"
    marcos = MARCOS
    procedencia = PROCEDENCIA

    def __init__(self, parametros: Parametros = PARAMETROS) -> None:
        self.p = parametros

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
