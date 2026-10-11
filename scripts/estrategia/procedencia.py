"""Valida el bloque de procedencia de una estrategia contra `fuentes.md` (spec §4).

Cada cita de `canonico` y `empirico` empieza con el id de una fila del resumen de
`fuentes.md` (`F1`, `F3`...). Solo sirven de respaldo las filas "verificada" o
"verificada vía": una "verificada parcial", "corregida" o "no encontrada" no
alcanza. Así nadie puede agregar una referencia de memoria.
"""
from __future__ import annotations

import re
from pathlib import Path

from estrategia.contrato import Procedencia

RAIZ = Path(__file__).resolve().parents[2]
_FILA = re.compile(r"^\|\s*(F\d+)\b[^|]*\|\s*([^|]+?)\s*\|")


def leer_estados(ruta: Path) -> dict[str, str]:
    """`{"F1": "verificada vía murphy", "F3": "verificada", ...}` desde la tabla de resumen."""
    estados: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = _FILA.match(linea)
        if m:
            estados[m.group(1)] = m.group(2).replace("*", "").strip().lower()
    return estados


def _verificada(estado: str) -> bool:
    return estado == "verificada" or estado.startswith("verificada vía")


def validar(proc: Procedencia, raiz: Path = RAIZ) -> list[str]:
    """Errores de la procedencia, en texto. Lista vacía si está completa."""
    errores: list[str] = []
    if not (raiz / proc.fuente_doctrina).exists():
        errores.append(f"la doctrina {proc.fuente_doctrina} no existe")
    ruta_citas = raiz / proc.fuente_citas
    if not ruta_citas.exists():
        return [*errores, f"el archivo de citas {proc.fuente_citas} no existe"]
    estados = leer_estados(ruta_citas)
    if not proc.fundamentos:
        errores.append("la procedencia no trae fundamentos")
    if not proc.modos_de_falla:
        errores.append("modos_de_falla vacío: el método tiene que declarar cómo falla")
    for f in proc.fundamentos:
        if not f.origen:
            errores.append(f"«{f.regla}»: sin origen")
        if not f.canonico and not f.empirico:
            errores.append(f"«{f.regla}»: sin respaldo canónico ni empírico")
        if not f.empirico and not f.no_probado.strip():
            errores.append(f"«{f.regla}»: sin evidencia empírica y con no_probado vacío")
        for cita in (*f.canonico, *f.empirico):
            fid = cita.split()[0] if cita.split() else ""
            estado = estados.get(fid)
            if estado is None:
                errores.append(f"«{f.regla}»: la cita «{cita}» no apunta a una fila de {proc.fuente_citas}")
            elif not _verificada(estado):
                errores.append(f"«{f.regla}»: la cita «{cita}» apunta a {fid}, que está «{estado}»")
    return errores
