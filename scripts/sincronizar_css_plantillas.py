#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Re-sincroniza el CSS de marca embebido en los snapshots de Stories.

Por qué existe, y por qué no alcanzaba `embeber_css_plantillas_v3.py`: ese script
fue una **migración de un solo uso**. Salta toda plantilla que ya contenga el
marcador `marca.css embebido`, así que después de la primera corrida dejó de
poder actualizar nada. El efecto es silencioso y grave: `marca.css` sigue siendo
la fuente única *nominal*, pero cada plantilla quedó con una copia congelada, y
un token nuevo o un color corregido no llega a ninguna pieza.

Este script hace lo que ese no puede: reemplaza el bloque embebido por el
contenido actual de `marca.css` (más `piel.css` en las plantillas que la usan),
tantas veces como haga falta. Es idempotente: correrlo dos veces no cambia nada
la segunda.

El CSS se embebe en vez de enlazarse porque Playwright no resolvía el
`<link href="marca.css">` del HTML temporal (solución del 2026-08-12), y un
estilo que no carga no da error: deja la pieza sin fecha, sin color o sin
tipografía, y el defecto solo aparece mirando el PNG.

Uso:
    uv run python scripts/sincronizar_css_plantillas.py
    uv run python scripts/sincronizar_css_plantillas.py --check   # no escribe
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_STORIES = RAIZ / "templates" / "stories"

MARCA = "marca.css"
PIEL = "piel.css"

MARCADOR_MARCA = "/* ════ marca.css embebido ════ */"
MARCADOR_PIEL = "/* ════ piel.css embebido ════ */"

# El bloque embebido es el PRIMER <style> del documento y termina en su primer
# </style>. El segundo <style> es el CSS propio de la plantilla y no se toca:
# ahí viven sus clases `.g-*`, su layout y sus media queries.
_BLOQUE = re.compile(
    r"<style>\s*\n\s*"
    + re.escape(MARCADOR_MARCA)
    + r".*?</style>",
    re.DOTALL,
)


_COMENTARIO = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINEAS_VACIAS = re.compile(r"\n{3,}")


def extraer_reglas(css: str) -> str:
    """Quita los comentarios de una hoja, dejando solo las reglas.

    No replica el criterio de `embeber_css_plantillas_v3.py`, y es a propósito.
    Ese script decidía por longitud de línea (`len(linea) < 80`) si conservaba la
    línea que cerraba un comentario, así que dejaba `*/` sueltos dentro del
    bloque embebido. Un `*/` sin apertura es CSS inválido que el navegador
    descarta en silencio: no rompe la pieza, pero deja basura que confunde a
    cualquiera que abra la plantilla a leerla.

    Acá se eliminan los comentarios completos con una sola expresión. Los
    comentarios explican *por qué* cada token es lo que es y ese razonamiento
    tiene que vivir en `marca.css`, que es la fuente; duplicarlo doce veces
    dentro de los snapshots no lo hace más verdadero.
    """
    sin_comentarios = _COMENTARIO.sub("", css)
    limpio = "\n".join(l.rstrip() for l in sin_comentarios.split("\n"))
    return _LINEAS_VACIAS.sub("\n\n", limpio).strip("\n")


def bloque_embebido(usa_piel: bool, reglas_marca: str, reglas_piel: str) -> str:
    partes = [f"<style>\n  {MARCADOR_MARCA}\n{reglas_marca}"]
    if usa_piel:
        partes.append(f"\n  {MARCADOR_PIEL}\n{reglas_piel}")
    partes.append("\n</style>")
    return "".join(partes)


def plantillas() -> list[Path]:
    return sorted(p for p in DIR_STORIES.glob("*.html"))


def sincronizar(check: bool = False) -> int:
    reglas_marca = extraer_reglas((DIR_STORIES / MARCA).read_text(encoding="utf-8"))
    reglas_piel = extraer_reglas((DIR_STORIES / PIEL).read_text(encoding="utf-8"))

    desactualizadas: list[str] = []
    sin_bloque: list[str] = []

    for ruta in plantillas():
        contenido = ruta.read_text(encoding="utf-8")
        if MARCADOR_MARCA not in contenido:
            # Plantilla que todavía enlaza las hojas o que no usa marca.css.
            sin_bloque.append(ruta.name)
            continue

        usa_piel = MARCADOR_PIEL in contenido
        nuevo_bloque = bloque_embebido(usa_piel, reglas_marca, reglas_piel)
        nuevo, n = _BLOQUE.subn(lambda _m: nuevo_bloque, contenido, count=1)
        if n != 1:
            print(
                f"FALLA: no pude delimitar el bloque embebido en {ruta.name}. "
                "Revisar que el primer <style> abra con el marcador.",
                file=sys.stderr,
            )
            return 1

        if nuevo == contenido:
            continue

        desactualizadas.append(ruta.name)
        if not check:
            ruta.write_text(nuevo, encoding="utf-8")

    if sin_bloque:
        print(f"Sin bloque embebido (se dejan como están): {', '.join(sin_bloque)}")

    if check:
        if desactualizadas:
            print(
                "FALLA: el CSS embebido quedó atrás de marca.css/piel.css en "
                f"{len(desactualizadas)} plantilla(s) -> {', '.join(desactualizadas)}\n"
                "Correr: uv run python scripts/sincronizar_css_plantillas.py",
                file=sys.stderr,
            )
            return 1
        print(f"CSS embebido al día en {len(plantillas()) - len(sin_bloque)} plantilla(s)")
        return 0

    if desactualizadas:
        print(f"Actualizadas ({len(desactualizadas)}): {', '.join(desactualizadas)}")
    else:
        print("Nada que actualizar: el CSS embebido ya estaba al día")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verifica sin escribir; sale 1 si alguna plantilla quedó atrás",
    )
    args = parser.parse_args(argv)
    return sincronizar(check=args.check)


if __name__ == "__main__":
    sys.exit(main())
