"""Quién firma el informe: el director, con su acreditación dicha con exactitud.

Una credencial vencida impresa es peor que ninguna, así que la vigencia se
decide con la fecha del pedido y no con la del config. Y el informe no menciona
a la CMF (decisión del director, 2026-10-08): la acreditación se nombra tal como
figura en el certificado, con su enlace de verificación.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


class AutorInvalido(ValueError):
    """El config no trae quién firma; el bot no arranca así."""


@dataclass(frozen=True)
class Autor:
    nombre: str
    cargo: str
    foto: Path | None
    firma: Path | None
    acreditacion: dict[str, str] | None
    faltantes: tuple[str, ...] = ()


def _archivo(raiz: Path, valor: str | None, nombre: str, faltantes: list[str]) -> Path | None:
    if not valor:
        return None
    ruta = raiz / valor
    if ruta.exists():
        return ruta
    faltantes.append(f"la {nombre} declarada no está en {valor}: el informe sale sin ella")
    return None


def cargar(config: dict[str, Any], raiz: Path) -> Autor:
    datos = config.get("autor")
    if not datos or not datos.get("nombre") or not datos.get("cargo"):
        raise AutorInvalido("config/analistas_telegram.json no trae el bloque «autor» con nombre y cargo")
    faltantes: list[str] = []
    return Autor(
        nombre=datos["nombre"],
        cargo=datos["cargo"],
        foto=_archivo(raiz, datos.get("foto"), "foto", faltantes),
        firma=_archivo(raiz, datos.get("firma"), "firma", faltantes),
        acreditacion=datos.get("acreditacion"),
        faltantes=tuple(faltantes),
    )


def vigente(a: Autor, hoy: date) -> bool:
    if not a.acreditacion:
        return False
    return hoy <= date.fromisoformat(a.acreditacion["vigente_hasta"])


def avisos(a: Autor, hoy: date) -> list[str]:
    salida = list(a.faltantes)
    if a.acreditacion and not vigente(a, hoy):
        salida.append(f"la acreditación {a.acreditacion['numero']} venció el "
                      f"{a.acreditacion['vigente_hasta']}: el informe sale sin ella, renuévala")
    return salida
