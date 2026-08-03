"""Rinde las diez plantillas de Stories de una pasada, para revisarlas juntas.

Existe porque los defectos de consistencia no se ven revisando una plantilla a
la vez. Dos veces en el mismo día pasó lo mismo: un cambio global de paleta dejó
piezas sin regenerar y nadie lo notó, y el rojo de `operacion` sobrevivió una
ronda entera porque la revisión estaba puesta en `alerta`. Ambos se ven de
inmediato con las diez piezas una al lado de la otra.

    uv run --extra stories python scripts/rendir_todas.py
    uv run --extra stories python scripts/rendir_todas.py --formato vertical
    uv run --extra stories python scripts/rendir_todas.py --solo alerta,operacion

Salida por defecto: `data/stories/_revision/<formato>/`. Está gitignoreado como
el resto de `data/stories/`, y se sobrescribe en cada corrida a propósito — es
una vista de trabajo, no un archivo histórico.

Los payloads salen de `tests/fixtures/stories/payloads/<plantilla>.json`, los
MISMOS que protegen el contrato en `tests/test_story_render.py`. Es deliberado:
una fixture que solo se usa en el test se desactualiza sin que nadie lo note,
y una que además se mira cada vez que se toca el diseño, no.

Ninguna fixture pide datos al terminal. La de `operacion` trae una serie
congelada en vez de llamar a MT5, porque una herramienta de revisión visual no
puede depender de que MetaTrader esté abierto.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

DIR_PLANTILLAS = RAIZ / "templates" / "stories"
DIR_PAYLOADS = RAIZ / "tests" / "fixtures" / "stories" / "payloads"
DIR_SALIDA = RAIZ / "data" / "stories" / "_revision"


def _plantillas(filtro: set[str] | None) -> list[tuple[str, Path, Path]]:
    """(nombre, plantilla, payload) de cada Story que tenga fixture.

    Una plantilla sin payload NO se salta en silencio: se reporta como faltante
    al final. Ese es justamente el caso que hay que ver — una plantilla nueva sin
    fixture es una que nadie está revisando ni testeando.
    """
    encontradas = []
    for tpl in sorted(DIR_PLANTILLAS.glob("*.html")):
        nombre = tpl.stem
        if filtro and nombre not in filtro:
            continue
        encontradas.append((nombre, tpl, DIR_PAYLOADS / f"{nombre}.json"))
    return encontradas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formato", default="horizontal", choices=("horizontal", "vertical"))
    parser.add_argument("--solo", help="lista separada por comas de plantillas a rendir")
    parser.add_argument("--salida", type=Path, help="carpeta destino (por defecto data/stories/_revision)")
    args = parser.parse_args(argv)

    import story_render
    from story_grafico_operacion import enriquecer

    filtro = {s.strip() for s in args.solo.split(",")} if args.solo else None
    destino = (args.salida or DIR_SALIDA) / args.formato
    destino.mkdir(parents=True, exist_ok=True)

    viewport = story_render.resolver_viewport(args.formato)
    ok, fallidas, sin_payload = 0, [], []

    for nombre, tpl, payload_path in _plantillas(filtro):
        if not payload_path.exists():
            sin_payload.append(nombre)
            print(f"SIN PAYLOAD  {nombre}")
            continue

        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        # `operacion` necesita que su recorrido se convierta en el SVG antes de
        # rendir; el resto de las plantillas pasa derecho.
        if "recorrido" in payload:
            payload = enriquecer(payload)

        salida = destino / f"{nombre}.png"
        try:
            html = story_render.build_html(payload, tpl)
            story_render.render_png(
                html, salida, template_dir=DIR_PLANTILLAS, viewport=viewport
            )
        except Exception as exc:  # noqa: BLE001 - el reporte importa más que el tipo
            fallidas.append((nombre, exc))
            print(f"FALLA        {nombre}: {exc}")
            continue

        ok += 1
        print(f"ok           {nombre}")

    print(f"\n{ok} pieza(s) en {destino}")
    if sin_payload:
        print(f"Sin payload de prueba: {', '.join(sin_payload)}", file=sys.stderr)
    if fallidas:
        print(f"{len(fallidas)} plantilla(s) fallaron.", file=sys.stderr)
    return 1 if (fallidas or sin_payload) else 0


if __name__ == "__main__":
    raise SystemExit(main())
