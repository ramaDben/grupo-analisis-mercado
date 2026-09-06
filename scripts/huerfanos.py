"""Detecta módulos y plantillas que nadie usa, sin borrar nada.

Su única acción es fallar: `--check` devuelve 1 y nombra cada archivo
injustificado. El borrado es siempre un commit de una persona que lo miró.

Eso no es cautela decorativa. La invocación dinámica existe (`importlib`, un
`subprocess` con el nombre armado por concatenación) y es invisible al análisis
de texto, así que un detector que borrara solo convertiría un falso positivo en
código perdido. Fallando, el mismo falso positivo cuesta una línea de encabezado.

Un archivo está justificado si se cumple al menos una:

1. Lo alcanza, directa o transitivamente, algo que no está bajo juicio: un test,
   un config, un comando de `.claude/commands/`, el MCP.
2. La prosa operativa lo nombra con su comando (`PROSA_OPERATIVA`).
3. Declara su invocador externo con `punto-de-entrada:` en sus primeras líneas.

No justifican un doc de diseño ni nada bajo `archive/`: eso es la lápida, no el
uso.

Uso:
    uv run python scripts/huerfanos.py           # informa
    uv run python scripts/huerfanos.py --check    # falla si hay injustificados
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Lo que se juzga. Un módulo ejecutable o una plantilla que nadie usa es residuo;
# un doc o un config que nadie referencia, no (casi ningún doc se referencia, y
# un JSON leído por su nombre completo no siempre aparece como texto).
CANDIDATOS: dict[str, tuple[str, ...]] = {
    "scripts": (".py", ".ps1", ".cmd", ".bat"),
    "src": (".py",),
    "tools": (".py",),
    "templates": (".html", ".txt"),
}

# El índice donde se buscan las referencias.
EXTS_INDICE = frozenset(
    {
        ".py", ".md", ".ps1", ".cmd", ".bat", ".json",
        ".toml", ".yaml", ".yml", ".txt", ".html", ".css",
    }
)

# Solo el código y la configuración justifican por sí solos. La prosa justifica
# únicamente si es operativa (`PROSA_OPERATIVA`), y esa distinción es el corazón
# del detector: si cualquier `.md` contara, un doc de diseño de una función
# retirada mantendría vivo lo que documenta su retiro. Es la lápida, no el uso.
EXTS_CODIGO = frozenset({".py", ".ps1", ".cmd", ".bat", ".json", ".toml", ".yaml", ".yml"})

# `archive/` queda fuera a propósito: es donde vive lo retirado, y sus
# referencias no deben mantener vivo a nadie. Mismo criterio que los docs de
# diseño. `data/` es estado generado con sus propias reglas.
EXCLUIDOS = frozenset(
    {"__pycache__", ".git", ".venv", "node_modules", "data", "brand_atomic_system", "archive"}
)

# Prosa que le dice a una persona cómo correr algo. Nombrarla acá es lo que
# permite que la reestructuración de CLAUDE.md mueva párrafos a `docs/` sin que
# los módulos que esos párrafos documentan queden injustificados de golpe.
PROSA_OPERATIVA = (
    "CLAUDE.md",
    "README.md",
    ".agents/rules/",
    ".agents/workflows/",
    ".claude/commands/",
    "docs/documentos-largos.md",
    "docs/notas-implementacion.md",
    "docs/setup-guide.md",
    "docs/commands-reference.md",
    "docs/architecture.md",
)

# Se busca en cualquier sintaxis de comentario (`#`, `rem`, `<!--`), así que la
# marca es el texto y no el prefijo. El motivo después de los dos puntos es
# obligatorio: "declarado" sin decir quién lo llama es la misma opacidad con otro
# nombre.
MARCA = "punto-de-entrada:"
LINEAS_CABECERA = 20


def _rastreados_por_git() -> set[str]:
    """Lo no rastreado y lo gitignoreado no es el repo: es el escritorio de alguien.

    Sin esto, un archivo de trabajo a medias pone la suite roja en la máquina de
    quien lo escribió y en ninguna otra, que es la peor clase de test.
    """
    salida = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {p for p in salida.split("\0") if p}


def _util(rel: str) -> bool:
    return not any(parte in EXCLUIDOS for parte in Path(rel).parts)


def _candidato(rel: str) -> bool:
    partes = Path(rel).parts
    if not partes:
        return False
    exts = CANDIDATOS.get(partes[0])
    return bool(exts) and Path(rel).suffix in exts


def declara_punto_de_entrada(ruta: Path) -> bool:
    """True si el archivo declara su invocador externo con un motivo no vacío."""
    try:
        lineas = ruta.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return False
    for linea in lineas[:LINEAS_CABECERA]:
        if MARCA in linea:
            _, _, motivo = linea.partition(MARCA)
            return bool(motivo.strip())
    return False


def _agujas(rel: str) -> tuple[str, ...]:
    """Cómo se nombra este archivo cuando alguien lo referencia.

    Los `.py` se buscan por el nombre del módulo, que es lo que usan los
    imports y suele ser distintivo (`reloj_gi`, `pipeline_carrusel`).

    Todo lo demás se busca por nombre de archivo completo, o por su raíz
    **entre comillas**, que es como el código elige una plantilla
    (`plantilla="alerta"`). La raíz suelta no cuenta, y esa restricción hace
    falta: `templates/calculadoras/instrucciones.html` aparecía justificado por
    `README.md`, que nunca lo nombra y solo usa la palabra "instrucciones" en
    una frase. Una raíz que es una palabra corriente justifica cualquier cosa.
    """
    p = Path(rel)
    if p.suffix == ".py":
        return (p.stem,)
    return (p.name, f'"{p.stem}"', f"'{p.stem}'")


def marcar(
    candidatos: list[str],
    textos: dict[str, str],
    declarados: set[str],
) -> tuple[set[str], dict[str, str]]:
    """Marca desde raíces y propaga. Función pura: no toca el disco.

    **Marcado desde raíces, no barrido desde el total**, y la diferencia decide
    la corrección. Si el criterio fuera "alguien lo nombra", dos módulos muertos
    que se referencian entre sí se mantendrían vivos para siempre: cada uno sería
    la prueba de que el otro se usa. Acá lo vivo tiene que ser *alcanzable* desde
    algo que no está bajo juicio, desde la prosa operativa, o desde su propia
    declaración.
    """
    bajo_juicio = set(candidatos)
    agujas = {c: _agujas(c) for c in candidatos}

    def nombrado_en(rel_fuente: str, candidato: str) -> bool:
        if rel_fuente == candidato:
            return False
        texto = textos.get(rel_fuente)
        return bool(texto) and any(a in texto for a in agujas[candidato])

    porque: dict[str, str] = {}
    vivos: set[str] = set()
    for c in candidatos:
        if c in declarados:
            porque[c] = "declara punto-de-entrada"
            vivos.add(c)
            continue
        prosa = [f for f in sorted(textos) if f.startswith(PROSA_OPERATIVA) and nombrado_en(f, c)]
        if prosa:
            porque[c] = f"prosa operativa: {prosa[0]}"
            vivos.add(c)
            continue
        # Alcanzado por código o config que no está bajo juicio: un test, un
        # JSON de `config/`, el registro del MCP, `pyproject.toml`.
        externos = [
            f
            for f in sorted(textos)
            if f not in bajo_juicio and Path(f).suffix in EXTS_CODIGO and nombrado_en(f, c)
        ]
        if externos:
            porque[c] = f"referenciado por {externos[0]}"
            vivos.add(c)

    # Propagación: lo que un vivo llama, vive. Itera hasta punto fijo, porque una
    # cadena de tres eslabones se esconde detrás de su primer eslabón.
    frontera = set(vivos)
    while frontera:
        nueva: set[str] = set()
        for c in candidatos:
            if c in vivos or c in nueva:
                continue
            fuente = next((f for f in sorted(frontera) if nombrado_en(f, c)), None)
            if fuente:
                porque[c] = f"lo llama {fuente}"
                nueva.add(c)
        vivos |= nueva
        frontera = nueva

    return vivos, porque


def analizar() -> tuple[list[str], dict[str, str]]:
    """Devuelve (injustificados ordenados, motivo de justificación por archivo)."""
    rastreados = {r for r in _rastreados_por_git() if _util(r)}
    candidatos = sorted(r for r in rastreados if _candidato(r))

    textos: dict[str, str] = {}
    for rel in rastreados:
        ruta = RAIZ / rel
        if ruta.suffix not in EXTS_INDICE or not ruta.is_file():
            continue
        try:
            textos[rel] = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

    declarados = {c for c in candidatos if declara_punto_de_entrada(RAIZ / c)}
    vivos, porque = marcar(candidatos, textos, declarados)

    return [c for c in candidatos if c not in vivos], porque


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="falla si hay archivos injustificados (lo corre la suite)",
    )
    args = parser.parse_args(argv)

    injustificados, porque = analizar()

    if not injustificados:
        print(f"{len(porque)} módulo(s) y plantilla(s) justificados. Ninguno huérfano.")
        return 0

    print(f"{len(injustificados)} archivo(s) sin justificación:\n", file=sys.stderr)
    for rel in injustificados:
        try:
            n = len((RAIZ / rel).read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            n = 0
        print(f"  {rel:56s} {n:>5} líneas", file=sys.stderr)

    print(
        "\nCada uno tiene dos salidas, y las dos son decisiones de una persona:\n"
        f"  declararlo  ->  agregar `{MARCA} <quién lo llama>` en sus primeras "
        f"{LINEAS_CABECERA} líneas\n"
        "  borrarlo    ->  git rm, en un commit propio\n",
        file=sys.stderr,
    )
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
