"""Audita el enganche del glosario de siglas: matcher viejo vs. nuevo.

Existe porque `_enganchar_glosario` paso de un `in` de substring puro a exigir
limite de palabra, y el riesgo de ese endurecimiento es el FALSO NEGATIVO: una
clave que antes enganchaba y ahora no deja el indicador saliendo en ingles en la
pieza del cliente.

**El corpus son nombres de evento, no literales del repo.** Una primera version
cosechaba strings del AST de los tests y del texto de docs, y el resultado decia
"0 regresiones" sobre un corpus lleno de rutas de archivo y nombres de variable
(`pipeline_carrusel`, `.g-linea`, `2_us100spot.json`). Un corpus sin nombres de
evento reales no puede exhibir una regresion aunque exista, asi que ese cero no
probaba nada.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "src"))

GLOSARIO = RAIZ / "data" / "glosario_siglas.json"


def candidatos(entry: dict) -> list[str]:
    return [*entry.get("titulos_ff", [])]


def matcher_viejo(nombre: str, glosario: dict) -> str | None:
    """El comportamiento anterior: substring puro."""
    nombre_upper = nombre.upper()
    mejor = mejor_largo = None
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        for cand in (key, *entry.get("titulos_ff", [])):
            if cand.upper() in nombre_upper and (mejor_largo is None or len(cand) > mejor_largo):
                mejor, mejor_largo = entry.get("nombre_es"), len(cand)
    return mejor


def matcher_nuevo(nombre: str, glosario: dict) -> str | None:
    """El comportamiento actual: exige limite de palabra."""
    nombre_upper = nombre.upper()
    mejor = mejor_largo = None
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        for cand in (key, *entry.get("titulos_ff", [])):
            if mejor_largo is not None and len(cand) <= mejor_largo:
                continue
            patron = r"(?<![A-Z0-9])" + re.escape(cand.upper()) + r"(?![A-Z0-9])"
            if re.search(patron, nombre_upper):
                mejor, mejor_largo = entry.get("nombre_es"), len(cand)
    return mejor


def corpus_de_nombres(glosario: dict) -> list[tuple[str, str]]:
    """Nombres de evento reales, con el `nombre_es` que DEBERIAN enganchar.

    Las claves de texto y sus `titulos_ff` son los titulos que el calendario
    publica, asi que cada uno es a la vez entrada del corpus y su propia
    respuesta correcta: es el test de identidad, y el mas fuerte que hay. Si una
    clave no engancha su propio alias, la regresion es segura.
    """
    salida = []
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        esperado = entry.get("nombre_es")
        if not key.isdigit():
            salida.append((key, esperado))
        for alias in entry.get("titulos_ff", []):
            salida.append((alias, esperado))
    return salida


def main() -> int:
    glosario = json.loads(GLOSARIO.read_text(encoding="utf-8"))
    corpus = corpus_de_nombres(glosario)

    regresiones, identidad_rota, correcciones = [], [], []
    for nombre, esperado in corpus:
        viejo = matcher_viejo(nombre, glosario)
        nuevo = matcher_nuevo(nombre, glosario)
        if nuevo is None and viejo is not None:
            regresiones.append((nombre, viejo, nuevo))
        elif viejo != nuevo:
            correcciones.append((nombre, viejo, nuevo))
        # Test de identidad: su propio titulo tiene que engancharse a si mismo.
        if esperado is not None and nuevo != esperado:
            identidad_rota.append((nombre, esperado, nuevo))

    print(f"corpus: {len(corpus)} nombres de evento reales (claves + titulos_ff)")
    print()
    print(f"REGRESIONES (enganchaba y ya no): {len(regresiones)}")
    for n, v, nv in regresiones:
        print(f"  {n!r}: antes {v!r} -> ahora {nv!r}")
    print()
    print(f"IDENTIDAD ROTA (no engancha su propia entrada): {len(identidad_rota)}")
    for n, esp, nv in identidad_rota:
        print(f"  {n!r}: esperaba {esp!r} -> obtuvo {nv!r}")
    print()
    print(f"CAMBIOS DE ENGANCHE (uno por otro): {len(correcciones)}")
    for n, v, nv in correcciones:
        print(f"  {n!r}: antes {v!r} -> ahora {nv!r}")

    cortas = sorted(
        k for k in glosario
        if not k.startswith("_") and not k.isdigit() and len(k) <= 3
    )
    print()
    print(f"CLAVES CORTAS (2-3 caracteres, riesgosas por forma): {len(cortas)}")
    print("  " + ", ".join(cortas))

    return 1 if regresiones or identidad_rota else 0


if __name__ == "__main__":
    raise SystemExit(main())
