# punto-de-entrada: lo corre el director a mano para revisar bandas vacias en piezas ya renderizadas
"""Detecta bandas vacías en las piezas ya renderizadas.

El aire injustificado es el defecto más difícil de cazar a ojo: no se ve como un
error, se ve como una pieza sosa. Y en un layout de dos columnas se esconde
mejor todavía, porque una columna puede estar vacía mientras la otra tiene
contenido a la misma altura — mirando la imagen completa no aparece nada raro.

    uv run --with pillow python scripts/auditar_espacios.py
    uv run --with pillow python scripts/auditar_espacios.py --min 60

Trabaja sobre los PNG de `data/stories/_revision/`, así que primero hay que
correr `rendir_todas.py`.

Método: una fila de píxeles con contenido tiene contraste horizontal alto
—texto, líneas, barras—; una fila de puro fondo casi no varía, aunque el fondo
sea un degradado, porque el degradado cambia despacio. Se analiza por separado
la mitad izquierda, la derecha y el ancho completo: así se detecta el hueco que
vive en una sola columna.

No falla el proceso: informa. Un espacio grande puede ser deliberado —el aire
que alinea el cierre de dos columnas, por ejemplo— y esa decisión la toma quien
mira la pieza, no un umbral.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_REVISION = RAIZ / "data" / "stories" / "_revision"

# Contraste horizontal mínimo para considerar que una fila tiene contenido. El
# degradado del fondo varía de forma suave, así que se queda muy por debajo.
UMBRAL_CONTRASTE = 34
# Los bordes se ignoran: el filete de marca da contraste en todas las filas.
MARGEN_FILETE = 8


def _filas_con_contenido(im, x0: int, x1: int) -> list[bool]:
    ancho, alto = im.size
    px = im.load()
    filas = []
    for y in range(alto):
        lo, hi = 255, 0
        for x in range(x0, x1, 3):  # muestreo cada 3 px: suficiente y 3x más rápido
            v = sum(px[x, y]) // 3
            if v < lo:
                lo = v
            if v > hi:
                hi = v
        filas.append(hi - lo >= UMBRAL_CONTRASTE)
    return filas


def _bandas_vacias(filas: list[bool], minimo: int) -> list[tuple[int, int]]:
    """Rachas de filas sin contenido, ignorando las de los extremos.

    Las de arriba y abajo son el margen de la pieza, no un hueco: recortarlas
    sería pedirle al diseño que llegue hasta el borde.
    """
    bandas, inicio = [], None
    for y, hay in enumerate(filas):
        if not hay and inicio is None:
            inicio = y
        elif hay and inicio is not None:
            if y - inicio >= minimo:
                bandas.append((inicio, y))
            inicio = None
    return bandas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min", type=int, default=90, help="alto mínimo de banda a reportar (px)")
    parser.add_argument("--dir", type=Path, default=DIR_REVISION / "horizontal")
    args = parser.parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print("Falta pillow. Ejecuta con: uv run --with pillow python ...", file=sys.stderr)
        return 2

    pngs = sorted(args.dir.glob("*.png"))
    if not pngs:
        print(f"No hay PNG en {args.dir}. Corre primero scripts/rendir_todas.py", file=sys.stderr)
        return 2

    total = 0
    for f in pngs:
        im = Image.open(f).convert("RGB")
        ancho, _ = im.size
        m = MARGEN_FILETE
        zonas = {
            "columna izq": (m, ancho // 2),
            "columna der": (ancho // 2, ancho - m),
            "ancho completo": (m, ancho - m),
        }
        hallazgos = []
        for nombre, (x0, x1) in zonas.items():
            for y0, y1 in _bandas_vacias(_filas_con_contenido(im, x0, x1), args.min):
                hallazgos.append((y1 - y0, nombre, y0, y1))

        # Una banda de ancho completo aparece también en las dos mitades: se
        # informa solo la más específica para no triplicar el mismo hueco.
        completas = {(y0, y1) for alto, n, y0, y1 in hallazgos if n == "ancho completo"}
        hallazgos = [
            h for h in hallazgos
            if h[1] == "ancho completo" or not any(abs(h[2] - a) < 12 and abs(h[3] - b) < 12
                                                   for a, b in completas)
        ]
        hallazgos.sort(reverse=True)

        if hallazgos:
            print(f"\n{f.stem}")
            for alto, zona, y0, y1 in hallazgos[:4]:
                print(f"   {alto:4} px vacíos  ·  {zona:15} y {y0}-{y1}")
            total += len(hallazgos)
        else:
            print(f"\n{f.stem}\n   sin bandas sobre {args.min} px")

    print(f"\n{total} banda(s) por revisar. Un hueco grande puede ser deliberado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
