"""Los workflows de AGY apuntan a comandos reales y están al día.

Sin este test, la desincronización es silenciosa: alguien renombra un comando de
`.claude/commands/`, el workflow de AGY sigue apuntando al archivo viejo, y el
fallo recién aparece cuando el director invoca `/story` desde Antigravity y el
agente no encuentra su definición.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import agy_workflows  # noqa: E402

DIR_COMANDOS = _REPO_ROOT / ".claude" / "commands"
DIR_WORKFLOWS = _REPO_ROOT / ".agents" / "workflows"


def test_cada_comando_expuesto_existe():
    for nombre in agy_workflows.COMANDOS:
        comando = DIR_COMANDOS / f"{nombre}.md"
        assert comando.exists(), f"{nombre} está en COMANDOS pero no existe {comando}"


def test_los_workflows_estan_al_dia():
    # Equivale a `uv run python scripts/agy_workflows.py --check`. Falla si falta
    # un workflow, si quedó desactualizado o si sobra uno sin comando.
    assert agy_workflows.main(["--check"]) == 0


def test_ningun_workflow_supera_el_limite_de_antigravity():
    # Antigravity corta los workflows en 12.000 caracteres. Los punteros pesan
    # ~1 KB, pero el día que alguien decida inlinear un comando en vez de
    # apuntarlo, este test es lo que lo detiene: `story.md` solo ya son 43.000.
    for workflow in sorted(DIR_WORKFLOWS.glob("*.md")):
        peso = len(workflow.read_text(encoding="utf-8"))
        assert peso <= agy_workflows.LIMITE_CARACTERES, (
            f"{workflow.name} pesa {peso} caracteres y el límite es "
            f"{agy_workflows.LIMITE_CARACTERES}"
        )


def test_los_workflows_apuntan_a_su_comando_y_a_las_reglas():
    # Un puntero que no nombra su destino no sirve de puntero.
    for nombre in agy_workflows.COMANDOS:
        texto = (DIR_WORKFLOWS / f"{nombre}.md").read_text(encoding="utf-8")
        assert f".claude/commands/{nombre}.md" in texto
        assert ".agents/rules/proyecto.md" in texto


def test_los_workflows_explican_como_recibir_los_argumentos():
    # Los comandos de `.claude/commands/` esperan sus argumentos en `$ARGUMENTS`,
    # un marcador que Antigravity no documenta sustituir. Sin esta explicación, el
    # agente lee `$ARGUMENTS` literal y no se entera de que le pidieron
    # `/story alerta`: o falla, o —peor— elige el tipo por su cuenta.
    for nombre in agy_workflows.COMANDOS:
        texto = (DIR_WORKFLOWS / f"{nombre}.md").read_text(encoding="utf-8")
        assert "$ARGUMENTS" in texto, f"{nombre} no explica de dónde salen los argumentos"


def test_las_reglas_del_proyecto_existen():
    reglas = _REPO_ROOT / ".agents" / "rules" / "proyecto.md"
    assert reglas.exists(), "falta .agents/rules/proyecto.md"

    texto = reglas.read_text(encoding="utf-8")
    # Las tres que, si se pierden, producen una pieza incorrecta y no un error
    # visible: datos inventados, hora mal convertida y decimales truncados.
    assert "market-data" in texto
    assert "hora_chile.ps1" in texto
    assert "digits" in texto
