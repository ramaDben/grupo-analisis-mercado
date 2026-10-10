"""Registro de estrategias y lectura de la activa (spec §2).

Las fábricas se nombran como texto ("modulo:funcion") y se importan recién al
cargarlas: así este módulo no arrastra el código de todas las estrategias, y la
estrategia de juguete de los tests nunca queda registrada en producción.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

from estrategia.contrato import Estrategia

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config" / "estrategia.json"
FABRICAS: dict[str, str] = {"tori": "estrategia.tori:crear"}


class EstrategiaDesconocida(LookupError):
    """La config nombra una estrategia que no está registrada."""


def cargar(nombre: str, fabricas: dict[str, str] | None = None) -> Estrategia:
    fabricas = FABRICAS if fabricas is None else fabricas
    if nombre not in fabricas:
        raise EstrategiaDesconocida(
            f"La estrategia «{nombre}» no está registrada. Registradas: {sorted(fabricas)}"
        )
    modulo, funcion = fabricas[nombre].split(":")
    return getattr(importlib.import_module(modulo), funcion)()


def nombre_activo(ruta: Path = CONFIG) -> str:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    nombre = datos.get("activa")
    if not isinstance(nombre, str) or not nombre:
        raise ValueError(f"{ruta} no declara la estrategia 'activa'")
    return nombre


def activa(ruta: Path = CONFIG) -> Estrategia:
    return cargar(nombre_activo(ruta))
