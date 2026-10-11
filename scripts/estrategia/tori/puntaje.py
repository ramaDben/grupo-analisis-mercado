"""El escáner de Tori: lo completa la Task S3-5."""
from __future__ import annotations

from estrategia.contrato import Lectura, Puntaje
from estrategia.tori.parametros import Parametros


def puntuar(lectura: Lectura, horizonte: str, p: Parametros) -> Puntaje:
    return Puntaje(0.0, {}, None)
