"""Quién firma el informe: el director, con su acreditación dicha con exactitud.

Una credencial vencida impresa es peor que ninguna, así que la vigencia se
decide con la fecha del pedido y no con la del config. Y el informe no menciona
a la CMF (decisión del director, 2026-10-08): la acreditación se nombra tal como
figura en el certificado. Va sin enlace: el de la CMV no reconocía el
certificado, y un enlace que no verifica desacredita la firma.
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


CAMPOS_ACREDITACION = ("entidad", "categoria", "numero", "vigente_hasta")


def _validar_acreditacion(ac: dict[str, Any]) -> None:
    """Un error acá tiene que frenar el arranque, no reventar cada pedido después."""
    for campo in CAMPOS_ACREDITACION:
        if not str(ac.get(campo) or "").strip():
            raise AutorInvalido(f"la acreditación del autor no trae «{campo}»")
    try:
        date.fromisoformat(ac["vigente_hasta"])
    except ValueError as exc:
        raise AutorInvalido(f"vigente_hasta tiene que ser AAAA-MM-DD, y dice {ac['vigente_hasta']!r}") from exc
    if any("cmf" in str(v).lower() for v in ac.values()):
        raise AutorInvalido("el informe no nombra a la CMF: la acreditación va como figura en su certificado")


def cargar(config: dict[str, Any], raiz: Path) -> Autor:
    datos = config.get("autor")
    if not datos or not datos.get("nombre") or not datos.get("cargo"):
        raise AutorInvalido("config/analistas_telegram.json no trae el bloque «autor» con nombre y cargo")
    if datos.get("acreditacion"):
        _validar_acreditacion(datos["acreditacion"])
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
