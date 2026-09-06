"""Genera `.agents/rules/proyecto.md` desde `CLAUDE.md`, por ámbito de sección.

Antigravity no lee `CLAUDE.md`, así que necesita su propia copia de las reglas.
Hasta el 2026-09-06 esa copia se mantenía a mano y **no era un extracto: era un
fork**. Decía cuatro gates donde el escáner tiene seis, no sabía del suplemento
de canal ni de la noticia oficial, y sobre todo **no sabía que existe
`historial_despachos.json`**: AGY puede despachar, así que un canal que fallara a
la mitad se habría reenviado entero.

Cada sección de `CLAUDE.md` declara su ámbito en un comentario HTML justo debajo
del encabezado:

    ## El despacho: un lote por canal
    <!-- ambito: ambos -->

`ambos` va a los dos archivos, `claude` solo a `CLAUDE.md` (hooks, el tool
`Skill`), `agy` solo a `proyecto.md` (OMEGA, que vive en el CLAUDE.md global que
AGY no lee).

**Una sección sin marcador hace fallar al generador.** Un ámbito por omisión
convertiría cada sección nueva en una decisión que nadie tomó, y así se llega a
un fork sin que nadie lo haya elegido.

Uso:
    uv run python scripts/agy_reglas.py           # genera
    uv run python scripts/agy_reglas.py --check    # verifica (lo corre la suite)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "CLAUDE.md"
DESTINO = RAIZ / ".agents" / "rules" / "proyecto.md"

AMBITOS = ("ambos", "claude", "agy")
RE_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*)$")
RE_AMBITO = re.compile(r"^<!--\s*ambito:\s*([a-z]+)\s*-->\s*$")

PREAMBULO = """# Reglas del proyecto — Grupo de Análisis de Mercado

> **Generado por `scripts/agy_reglas.py` desde `CLAUDE.md`. No lo edites a mano:**
> el cambio se pierde en la próxima corrida y la suite lo detecta. Editá la
> sección correspondiente de `CLAUDE.md` y volvé a generar.

Antigravity no lee `CLAUDE.md`, así que este archivo trae las reglas que
**cualquier** pieza tiene que cumplir. No las reemplaza: `CLAUDE.md` sigue siendo
la fuente completa y, ante cualquier duda o contradicción, manda `CLAUDE.md`.

Léelo antes de ejecutar cualquier workflow de `.agents/workflows/`.

## Dónde está el resto

- `CLAUDE.md` — las reglas completas del proyecto.
- `.claude/commands/<nombre>.md` — la definición canónica de cada comando.
- `docs/architecture.md` — cómo encaja todo.

---
"""


@dataclass
class Seccion:
    nivel: int
    titulo: str
    ambito: str | None
    lineas: list[str] = field(default_factory=list)

    @property
    def cuerpo(self) -> str:
        return "".join(self.lineas)


def parsear_secciones(texto: str) -> tuple[str, list[Seccion]]:
    """Parte el documento en secciones, respetando los bloques de código.

    **El estado de fence no es una precaución teórica.** `CLAUDE.md` tenía un
    `# -> data/mensajes/...` dentro de un bloque de PowerShell, y un parser por
    regex lo lee como un encabezado H1 y parte el documento donde no hay corte.
    Los ejemplos de PowerShell con comentarios `#` están por todo el repo.
    """
    preambulo: list[str] = []
    secciones: list[Seccion] = []
    actual: Seccion | None = None
    dentro_fence = False

    for linea in texto.splitlines(keepends=True):
        pelada = linea.lstrip()
        if pelada.startswith(("```", "~~~")):
            dentro_fence = not dentro_fence
        elif not dentro_fence:
            m = RE_ENCABEZADO.match(linea)
            if m:
                actual = Seccion(nivel=len(m.group(1)), titulo=m.group(2).strip(), ambito=None)
                actual.lineas.append(linea)
                secciones.append(actual)
                continue
            if actual is not None and len(actual.lineas) == 1:
                ma = RE_AMBITO.match(linea.strip())
                if ma:
                    actual.ambito = ma.group(1)
                    continue  # el marcador no viaja al archivo generado

        (actual.lineas if actual is not None else preambulo).append(linea)

    return "".join(preambulo), secciones


def ambito_efectivo(secciones: list[Seccion]) -> list[tuple[Seccion, str]]:
    """Resuelve el ámbito de cada sección, heredando del `##` que la contiene.

    Un `###` puede sobrescribir a su padre, y hace falta: "La ingesta se engancha
    al arranque de sesión" vive bajo una sección `ambos` y es `claude` puro,
    porque los hooks no existen en AGY.
    """
    resuelto: list[tuple[Seccion, str]] = []
    heredado: dict[int, str] = {}
    for sec in secciones:
        if sec.ambito:
            propio = sec.ambito
        else:
            padres = [n for n in heredado if n < sec.nivel]
            propio = heredado[max(padres)] if padres else ""
        heredado = {n: a for n, a in heredado.items() if n < sec.nivel}
        heredado[sec.nivel] = propio
        resuelto.append((sec, propio))
    return resuelto


def _problemas_de_ambito(resuelto: list[tuple[Seccion, str]]) -> list[str]:
    fallas = []
    for sec, ambito in resuelto:
        if not ambito:
            fallas.append(f"sin ámbito: {'#' * sec.nivel} {sec.titulo}")
        elif ambito not in AMBITOS:
            fallas.append(f"ámbito '{ambito}' no existe: {'#' * sec.nivel} {sec.titulo}")
    return fallas


def componer() -> tuple[str, list[str]]:
    """Devuelve (contenido de proyecto.md, problemas encontrados)."""
    _, secciones = parsear_secciones(FUENTE.read_text(encoding="utf-8"))
    resuelto = ambito_efectivo(secciones)
    problemas = _problemas_de_ambito(resuelto)
    if problemas:
        return "", problemas

    partes = [PREAMBULO]
    for sec, ambito in resuelto:
        if ambito in ("ambos", "agy"):
            partes.append(sec.cuerpo)
    return "".join(partes), []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="no escribe; falla si proyecto.md quedó desactualizado o falta un ámbito",
    )
    args = parser.parse_args(argv)

    esperado, problemas = componer()

    if problemas:
        print(f"{len(problemas)} sección(es) de CLAUDE.md sin ámbito válido:\n", file=sys.stderr)
        for p in problemas:
            print(f"  {p}", file=sys.stderr)
        print(
            "\nAgregá `<!-- ambito: ambos|claude|agy -->` debajo del encabezado. "
            "Sin marcador no se asume nada: un ámbito por omisión es una decisión "
            "que nadie tomó.",
            file=sys.stderr,
        )
        return 1

    actual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else None

    if args.check:
        if actual is None:
            print(f"FALLA: falta {DESTINO.relative_to(RAIZ)}", file=sys.stderr)
            return 1
        if actual != esperado:
            print(
                f"FALLA: {DESTINO.relative_to(RAIZ)} quedó desactualizado.\n"
                "Corré `uv run python scripts/agy_reglas.py` para regenerarlo.",
                file=sys.stderr,
            )
            return 1
        print(f"ok    {DESTINO.relative_to(RAIZ)} al día")
        return 0

    if actual == esperado:
        print(f"--    {DESTINO.relative_to(RAIZ)}: sin cambios")
    else:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(esperado, encoding="utf-8")
        print(f"ok    {DESTINO.relative_to(RAIZ)}: escrito ({len(esperado):,} caracteres)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
