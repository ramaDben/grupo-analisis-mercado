"""Migra los snapshots de Stories GI a los tokens de `templates/stories/marca.css`.

Reemplaza cada hex conocido por su `var(--rol)` e inyecta el <link> a marca.css.
Con `--check` no escribe: falla si algún snapshot volvió a hardcodear un color, que
es la única forma de que la fuente única siga siendo única cuando se agregue una
plantilla nueva.

    uv run python scripts/marca_tokens.py            # migra
    uv run python scripts/marca_tokens.py --check     # verifica

El mapa es EXPLÍCITO a propósito: un regex genérico de 6 dígitos también captura
las referencias a issues de los comentarios (`#119`, `#127`), y un color que no
esté acá debe fallar el --check para que alguien decida su rol en vez de que se
cuele silenciosamente.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_STORIES = RAIZ / "templates" / "stories"
HOJA = "marca.css"
LINK = f'<link rel="stylesheet" href="{HOJA}">'

# hex -> rol semántico. Ver el encabezado de marca.css para el criterio de los
# nombres y para por qué --sube/--baja no son parte del reskin de marca.
MAPA = {
    "#0D0D1A": "fondo",
    "#10222B": "fondo-acento",
    "#120A12": "fondo-alt",
    "#123A2A": "fondo-sube",
    "#2A1220": "fondo-baja",
    "#3E91AF": "acento",
    "#1E3A5F": "acento-oscuro",
    "#00DC82": "sube",
    "#53C1AB": "sube-suave",
    "#E84040": "baja",
    "#F5A3A3": "baja-suave",
    "#FFB020": "aviso",
    "#F5F3F7": "texto-1",
    "#A9A5B4": "texto-2",
    "#6E6A7A": "texto-3",
    "#C9C5D4": "texto-borde",
    "#8E8A9C": "texto-gris",
    "#FFFFFF": "blanco",
}

# Solo 6 dígitos y con frontera: descarta `#119` de los comentarios de issue.
PATRON_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def _plantillas() -> list[Path]:
    return sorted(p for p in DIR_STORIES.glob("*.html"))


def _tokenizar(html: str) -> tuple[str, int, list[str]]:
    """Devuelve (html nuevo, nº de reemplazos, hex sin rol asignado)."""
    huerfanos: list[str] = []
    reemplazos = 0

    def _sub(match: re.Match[str]) -> str:
        nonlocal reemplazos
        hex_original = match.group(0)
        rol = MAPA.get(hex_original.upper())
        if rol is None:
            huerfanos.append(hex_original)
            return hex_original
        reemplazos += 1
        return f"var(--{rol})"

    return PATRON_HEX.sub(_sub, html), reemplazos, huerfanos


def _con_link(html: str) -> str:
    """Inserta el <link> antes del primer <style>, si no está ya.

    Va ANTES del <style> del snapshot para que las reglas propias de la plantilla
    sigan pudiendo ganarle a la hoja de marca.
    """
    if HOJA in html:
        return html
    return html.replace("<style>", f"{LINK}\n<style>", 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="no escribe; falla si queda algún color hardcodeado",
    )
    args = parser.parse_args(argv)

    if not (DIR_STORIES / HOJA).exists():
        print(f"ERROR: falta {DIR_STORIES / HOJA}", file=sys.stderr)
        return 2

    problemas = 0
    for ruta in _plantillas():
        html = ruta.read_text(encoding="utf-8")
        nuevo, n, huerfanos = _tokenizar(html)
        nuevo = _con_link(nuevo)

        if args.check:
            pendientes = n + len(huerfanos)
            falta_link = HOJA not in html
            if pendientes or falta_link:
                problemas += 1
                detalle = []
                if n:
                    detalle.append(f"{n} color(es) hardcodeado(s)")
                if huerfanos:
                    detalle.append(f"sin rol: {sorted(set(huerfanos))}")
                if falta_link:
                    detalle.append(f"sin <link> a {HOJA}")
                print(f"FALLA {ruta.name}: {'; '.join(detalle)}")
            else:
                print(f"ok    {ruta.name}")
            continue

        if huerfanos:
            problemas += 1
            print(
                f"FALLA {ruta.name}: hex sin rol en MAPA -> {sorted(set(huerfanos))}",
                file=sys.stderr,
            )
            continue

        if nuevo != html:
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"ok    {ruta.name}: {n} color(es) -> var(--rol)")
        else:
            print(f"--    {ruta.name}: sin cambios")

    if problemas:
        print(
            f"\n{problemas} plantilla(s) con problemas."
            if args.check
            else f"\n{problemas} plantilla(s) con colores sin rol asignado.",
            file=sys.stderr,
        )
        return 1

    print("\nPaleta centralizada en templates/stories/marca.css")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
