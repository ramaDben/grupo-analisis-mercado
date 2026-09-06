"""`.agents/rules/proyecto.md` se genera desde `CLAUDE.md` y no puede divergir.

Hasta el 2026-09-06 esa copia se mantenía a mano y era un fork, no un extracto:
decía cuatro gates donde el escáner tiene seis, y **no sabía que existe
`historial_despachos.json`**. AGY puede despachar, así que un canal que fallara a
la mitad se habría reenviado entero, y nada lo detectaba.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import agy_reglas  # noqa: E402

CLAUDE = _REPO_ROOT / "CLAUDE.md"
PROYECTO = _REPO_ROOT / ".agents" / "rules" / "proyecto.md"


def test_proyecto_md_esta_al_dia():
    # Equivale a `uv run python scripts/agy_reglas.py --check`. Es el test que
    # cierra el fork: un cambio en una sección `ambos` que no se regenere pone
    # la suite roja en el mismo commit.
    assert agy_reglas.main(["--check"]) == 0


def test_toda_seccion_declara_ambito():
    # Fail-closed. Un ámbito por omisión convertiría cada sección nueva en una
    # decisión que nadie tomó, y así se llega a un fork sin haberlo elegido.
    _, secciones = agy_reglas.parsear_secciones(CLAUDE.read_text(encoding="utf-8"))
    resuelto = agy_reglas.ambito_efectivo(secciones)
    problemas = agy_reglas._problemas_de_ambito(resuelto)
    assert problemas == [], "\n".join(problemas)


def test_el_parser_respeta_los_fences():
    # `CLAUDE.md` tenía un `# -> data/mensajes/...` dentro de un bloque de
    # PowerShell. Un parser por regex lo lee como encabezado H1 y parte el
    # documento donde no hay corte; los ejemplos de PowerShell con comentarios
    # `#` están por todo el repo, así que el fantasma vuelve.
    doc = (
        "## Real\n"
        "<!-- ambito: ambos -->\n"
        "texto\n"
        "```powershell\n"
        "# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01.txt\n"
        "## esto tampoco es una seccion\n"
        "```\n"
        "mas texto\n"
    )
    _, secciones = agy_reglas.parsear_secciones(doc)
    assert [s.titulo for s in secciones] == ["Real"]
    assert "# -> data/mensajes" in secciones[0].cuerpo, "el bloque tiene que viajar entero"


def test_el_marcador_no_viaja_al_archivo_generado():
    # El marcador es andamiaje de la generación, no contenido para AGY.
    assert "<!-- ambito:" not in PROYECTO.read_text(encoding="utf-8")


def test_proyecto_md_lleva_lo_de_ambos_y_lo_de_agy_pero_no_lo_de_claude():
    texto = PROYECTO.read_text(encoding="utf-8")

    # `ambos`: justo lo que el fork había perdido.
    for regla in ("historial_despachos", "gate_banda", "suplemento", "noticia_oficial"):
        assert regla in texto, f"falta una regla de ámbito ambos: {regla}"

    # `agy`: vive en el CLAUDE.md global del director, que AGY no lee.
    assert "MEMORIA GI" in texto, "OMEGA es de ámbito agy y tiene que estar"

    # `claude`: mecanismos que en AGY no existen.
    assert "hook_ingesta_macro" not in texto
    assert "SessionStart" not in texto


def test_un_ambito_desconocido_falla():
    # Un typo en el marcador no puede pasar por bueno y dejar la sección afuera.
    doc = "## Con typo\n<!-- ambito: anbos -->\ntexto\n"
    _, secciones = agy_reglas.parsear_secciones(doc)
    problemas = agy_reglas._problemas_de_ambito(agy_reglas.ambito_efectivo(secciones))
    assert problemas and "anbos" in problemas[0]


def test_un_h3_puede_sobrescribir_a_su_padre():
    # "La ingesta se engancha al arranque de sesión" vive bajo una sección
    # `ambos` y es `claude` puro: los hooks no existen en AGY.
    doc = (
        "## Padre\n<!-- ambito: ambos -->\na\n"
        "### Hijo que hereda\nb\n"
        "### Hijo que sobrescribe\n<!-- ambito: claude -->\nc\n"
        "## Otro padre\n<!-- ambito: agy -->\nd\n"
    )
    _, secciones = agy_reglas.parsear_secciones(doc)
    resuelto = dict((s.titulo, a) for s, a in agy_reglas.ambito_efectivo(secciones))
    assert resuelto == {
        "Padre": "ambos",
        "Hijo que hereda": "ambos",
        "Hijo que sobrescribe": "claude",
        "Otro padre": "agy",
    }


def test_todo_enlace_a_docs_existe():
    # Sostiene la estrategia entera. Si el plan es "puntero de una línea a
    # `docs/`", un puntero muerto es peor que no haber puesto nada: promete algo
    # que no existe, y el que lo sigue pierde el tiempo antes de darse cuenta.
    import re

    texto = CLAUDE.read_text(encoding="utf-8")
    # Rutas citadas entre backticks: `docs/algo.md`, `scripts/algo.py`, `config/x.json`.
    patron = re.compile(r"`((?:docs|scripts|config|templates|tests|src)/[\w./-]+\.\w+)`")
    faltantes = sorted(
        {ruta for ruta in patron.findall(texto) if not (_REPO_ROOT / ruta).exists()}
    )
    assert faltantes == [], "CLAUDE.md apunta a archivos que no existen: " + ", ".join(faltantes)
