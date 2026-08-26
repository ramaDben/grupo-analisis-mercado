"""Migra los snapshots de Stories GI a los tokens de `templates/stories/marca.css`.

Reemplaza cada hex conocido por su `var(--rol)`. Con `--check` no escribe: falla
si algún snapshot volvió a hardcodear un color, que es la única forma de que la
fuente única siga siendo única cuando se agregue una plantilla nueva.

    uv run python scripts/marca_tokens.py            # migra
    uv run python scripts/marca_tokens.py --check     # verifica

Qué se mira de cada plantilla
-----------------------------
Solo su CSS **propio**. Desde que las hojas se embeben (solución del 2026-08-12),
`marca.css` entero vive dentro de cada snapshot, y ahí los hex no son un defecto:
son la paleta. Mirarlos hacía que el gate reportara veinte colores hardcodeados
en `alerta.html` que el propio sincronizador había copiado. El corte lo hace
`quitar_css_embebido`, en `sincronizar_css_plantillas.py`, que es donde viven los
marcadores del bloque.

Por la misma razón, la exigencia dejó de ser el `<link>` y pasó a ser que la hoja
esté presente: embebida con su marcador, o enlazada si la plantilla todavía no
migró.

Qué es explícito y qué se deriva
--------------------------------
La DETECCIÓN es explícita: `PATRON_HEX` pide 6 dígitos con frontera porque un
regex más suelto captura las referencias a issues de los comentarios (`#119` es
hex válido).

El MAPA hex -> rol se deriva de `marca.css` (ver `cargar_mapa`). Escrito a mano
se pudrió una vez ya: al cambiar la paleta al verde del logo quedaron veinte hex
de la hoja sin entrada y cinco entradas apuntando a colores inexistentes, y el
gate siguió diciendo "ok" mientras sugería roles equivocados.

Qué cubre el check y qué NO
---------------------------
Cubre: hex de 6 dígitos y colores funcionales `rgb()`/`rgba()`. Los `rgba()`
estuvieron ciegos hasta agosto de 2026, y por ese hueco entraron el rojo fijo del
cromo de `alerta` y el fondo de la firma de `recomendacion`: el gate compraba una
confianza que no tenía.

De `rgba()` se permiten solo el negro y el blanco puros —`rgba(0,0,0,α)` y
`rgba(255,255,255,α)`—, que son veladuras y no color de marca: `color-mix` sobre
un rol no las expresa mejor y ya son el patrón de `piel.css`. Cualquier otra
terna hay que escribirla como `color-mix(in srgb, var(--rol) N%, transparent)`.

Ese chequeo entra por TRINQUETE, no de golpe: ocho plantillas anteriores traen
`rgba()` de colores de marca y limpiarlas es una plantilla por Change. Están
listadas en `RGBA_PENDIENTES` y salen como `aviso` en vez de `FALLA`. Todo lo
demás —las hojas `.css`, las plantillas ya limpias y cualquier plantilla nueva—
falla. Dicho sin adornos: hoy el gate PROTEGE lo limpio y solo INFORMA la deuda.

NO cubre, y conviene saberlo antes de confiar:
  · Hex de 3 dígitos (`#0af`). Se descartan a propósito: son indistinguibles de
    las referencias a issues de los comentarios (`#119` es hex válido).
  · `hsl()`, `oklch()`, `color()` y los nombres de color de CSS (`red`, `gold`).
  · Colores dentro de los SVG que inyecta `scripts/story_grafico.py` — ese
    generador no emite atributos de estilo, pero el check tampoco los miraría.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_css_plantillas import (  # noqa: E402
    _BLOQUE,
    MARCADOR_MARCA,
    quitar_css_embebido,
)

RAIZ = Path(__file__).resolve().parent.parent
DIR_STORIES = RAIZ / "templates" / "stories"
HOJA = "marca.css"
LINK = f'<link rel="stylesheet" href="{HOJA}">'

# `--rol: #hex;` en una hoja. Solo declaraciones: las mencion es de un hex
# dentro de un comentario explicativo no son la definición de un rol.
PATRON_DECLARACION = re.compile(r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;")


def cargar_mapa(hoja: Path | None = None) -> dict[str, str]:
    """hex -> rol semántico, leído de `marca.css`.

    Antes era un diccionario escrito a mano, y se pudrió: cuando la paleta pasó
    al verde del logo quedaron veinte hex de la hoja sin entrada y cinco
    entradas apuntando a colores que ya no existían. El gate seguía corriendo y
    seguía diciendo "ok", pero sugería roles equivocados y no sabía nombrar los
    nuevos. Un mapa de la paleta que se mantiene aparte de la paleta solo puede
    envejecer mal.

    Lo que sí sigue siendo explícito es la DETECCIÓN (`PATRON_HEX`): ahí el
    criterio del autor original vale entero, porque un regex genérico también
    captura las referencias a issues de los comentarios (`#119` es hex válido).
    Derivar el mapa no reintroduce ese problema.

    Ante dos roles con el mismo valor gana el primero declarado, que en
    `marca.css` es siempre el rol base: los alias van después y por `var()`.
    """
    ruta = hoja or (DIR_STORIES / HOJA)
    mapa: dict[str, str] = {}
    for rol, hex_ in PATRON_DECLARACION.findall(ruta.read_text(encoding="utf-8")):
        mapa.setdefault(hex_.upper(), rol)
    return mapa


# Solo 6 dígitos y con frontera: descarta `#119` de los comentarios de issue.
PATRON_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")

# `rgb()` / `rgba()` con los tres canales numéricos. Ver el docstring para el
# criterio de la allowlist.
PATRON_RGBA = re.compile(
    r"\brgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*[,)]"
)

# Veladuras permitidas: negro y blanco puros. No son color de marca y no hay un
# rol que las exprese mejor.
RGBA_PERMITIDOS = {(0, 0, 0), (255, 255, 255)}

# Trinquete. Las plantillas de esta lista traen `rgba()` de colores de marca de
# antes de que el check los mirara: se reportan como AVISO y no hacen fallar,
# porque limpiarlas es una plantilla por Change (misma regla que la migración de
# la piel) y no trabajo de este gate. Todo archivo FUERA de la lista falla, así
# que lo que hoy está limpio no puede volver a ensuciarse — y una plantilla nueva
# nace gateada. Al limpiar una, se saca de acá y queda protegida.
RGBA_PENDIENTES = frozenset(
    {
        "breaking.html",
        "dato_macro.html",
        "edu.html",
        "encuesta.html",
        "flash.html",
        "operacion.html",
        "oportunidad.html",
        "postventa.html",
    }
)


def _rgba_huerfanos(texto: str) -> list[str]:
    """Devuelve los `rgb()`/`rgba()` que NO son veladura permitida."""
    fuera = []
    for match in PATRON_RGBA.finditer(texto):
        canales = tuple(int(c) for c in match.groups())
        if canales not in RGBA_PERMITIDOS:
            fuera.append(f"rgb{canales}")
    return fuera


def _plantillas() -> list[Path]:
    return sorted(p for p in DIR_STORIES.glob("*.html"))


def _hojas() -> list[Path]:
    """Hojas de estilo propias, EXCEPTO marca.css.

    marca.css queda fuera a propósito: es la fuente de los hex y el único
    archivo donde escribirlos es correcto. Cualquier otra hoja —hoy piel.css—
    debe consumir `var(--rol)` como lo hacen las plantillas.
    """
    return sorted(p for p in DIR_STORIES.glob("*.css") if p.name != HOJA)


def _tokenizar(html: str, mapa: dict[str, str] | None = None) -> tuple[str, int, list[str]]:
    """Devuelve (html nuevo, nº de reemplazos, hex sin rol asignado)."""
    if mapa is None:
        mapa = cargar_mapa()
    huerfanos: list[str] = []
    reemplazos = 0

    def _sub(match: re.Match[str]) -> str:
        nonlocal reemplazos
        hex_original = match.group(0)
        rol = mapa.get(hex_original.upper())
        if rol is None:
            huerfanos.append(hex_original)
            return hex_original
        reemplazos += 1
        return f"var(--{rol})"

    # Los `rgba()` NO entran acá: no se pueden sustituir automáticamente (llevan
    # alfa, y el rol se expresa con `color-mix`). Se revisan aparte, con el
    # trinquete de RGBA_PENDIENTES.
    return PATRON_HEX.sub(_sub, html), reemplazos, huerfanos


def _tokenizar_respetando_paleta(
    html: str, mapa: dict[str, str]
) -> tuple[str, int, list[str]]:
    """Tokeniza la plantilla dejando intacta la paleta que trae embebida.

    Sin esto, migrar un snapshot lo destruye. El bloque embebido es una copia
    literal de `marca.css`, y ahí cada hex ES la definición del rol: sustituirlo
    produce `--acento: var(--acento);`, una variable que se referencia a sí misma
    y por lo tanto no resuelve a ningún color. La pieza no falla al renderizar,
    sale sin paleta.

    El peligro apareció recién al arreglar el mapa. Mientras estuvo
    desactualizado ninguno de esos hex tenía rol, así que el migrador los
    reportaba como huérfanos y se negaba a escribir: el archivo estaba a salvo
    por accidente, que es la clase de protección que deja de existir sin avisar.
    """
    bloque = _BLOQUE.search(html)
    if bloque is None:
        return _tokenizar(html, mapa)

    antes, n_antes, huerf_antes = _tokenizar(html[: bloque.start()], mapa)
    despues, n_despues, huerf_despues = _tokenizar(html[bloque.end() :], mapa)
    return (
        antes + bloque.group(0) + despues,
        n_antes + n_despues,
        huerf_antes + huerf_despues,
    )


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
    mapa = cargar_mapa()
    for ruta in _plantillas():
        html = ruta.read_text(encoding="utf-8")
        nuevo, n, huerfanos = _tokenizar_respetando_paleta(html, mapa)
        nuevo = _con_link(nuevo)

        if args.check:
            # Se mira el CSS PROPIO de la plantilla. El bloque embebido es una
            # copia literal de `marca.css`, o sea el único lugar donde escribir
            # un hex es correcto: contarlo ahí reportaba la paleta entera como
            # veinte colores hardcodeados de `alerta.html`.
            propio = quitar_css_embebido(html)
            _, n, huerfanos = _tokenizar(propio, mapa)
            rgba = _rgba_huerfanos(propio)
            deuda = ruta.name in RGBA_PENDIENTES
            pendientes = n + len(huerfanos) + (len(rgba) if not deuda else 0)
            falta_hoja = MARCADOR_MARCA not in html and HOJA not in html
            if pendientes or falta_hoja:
                problemas += 1
                detalle = []
                if n:
                    detalle.append(f"{n} color(es) hardcodeado(s)")
                if huerfanos:
                    detalle.append(f"sin rol: {sorted(set(huerfanos))}")
                if rgba and not deuda:
                    detalle.append(f"rgba() sin rol: {sorted(set(rgba))}")
                if falta_hoja:
                    detalle.append(f"no embebe ni enlaza {HOJA}")
                print(f"FALLA {ruta.name}: {'; '.join(detalle)}")
            elif rgba:
                print(f"aviso {ruta.name}: rgba() pendiente {sorted(set(rgba))}")
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

    if args.check:
        for ruta in _hojas():
            css = ruta.read_text(encoding="utf-8")
            _, n, huerfanos = _tokenizar(css, mapa)
            # Las hojas propias nacen después del gate: no tienen deuda y no
            # entran al trinquete.
            huerfanos = huerfanos + _rgba_huerfanos(css)
            if n or huerfanos:
                problemas += 1
                detalle = []
                if n:
                    detalle.append(f"{n} color(es) hardcodeado(s)")
                if huerfanos:
                    detalle.append(f"sin rol: {sorted(set(huerfanos))}")
                print(f"FALLA {ruta.name}: {'; '.join(detalle)}")
            else:
                print(f"ok    {ruta.name}")

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
