"""Los contratos de `scripts/guardrails/`, que es lo que impide que se desarme.

Cuatro invariantes, y cada uno fija un modo de falla concreto:

- **El catálogo y lo que se emite son el mismo conjunto**, en las dos
  direcciones. Un slug emitido sin declarar deja al sistema rechazando algo sin
  poder decir por qué; un slug declarado que nadie emite es una promesa, y el
  test no puede distinguir una promesa de un olvido.
- **Ningún guardrail lanza.** Un guardrail vive dentro de un hook, y un hook que
  revienta no bloquea: la escritura pasa sin revisar. Una excepción convierte un
  guardia en un permiso.
- **Ningún guardrail escribe.** Son funciones puras. Un guardrail con efectos
  laterales deja de poder correrse dos veces sobre lo mismo, y el hook lo corre
  cada vez que el modelo toca un archivo.
- **El slug se emite literal.** Uno armado por concatenación es invisible al
  análisis estático, y entonces el primer invariante deja de valer sin que nadie
  se entere.
"""

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from guardrails import motivos, veredicto  # noqa: E402

GUARDRAILS = _SCRIPTS_DIR / "guardrails"

# El contrato y el catálogo no se juzgan a sí mismos: no emiten veredictos.
INFRAESTRUCTURA = frozenset({"__init__.py", "veredicto.py", "motivos.py"})


def _modulos_de_regla() -> list[Path]:
    return sorted(p for p in GUARDRAILS.glob("*.py") if p.name not in INFRAESTRUCTURA)


def _slugs_emitidos() -> tuple[set[str], list[str]]:
    """Cada slug literal que se le pasa a `falla()`, y los que no son literales."""
    emitidos: set[str] = set()
    calculados: list[str] = []
    for ruta in _modulos_de_regla():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            fn = nodo.func
            nombre = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nombre != "falla" or not nodo.args:
                continue
            primero = nodo.args[0]
            if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
                emitidos.add(primero.value)
            else:
                calculados.append(f"{ruta.name}:{primero.lineno}")
    return emitidos, calculados


def test_hay_modulos_de_regla():
    # Si el glob se queda vacío, los tres tests que siguen pasan por vacuidad y
    # el contrato entero se vuelve decorativo sin que nada se ponga rojo.
    assert _modulos_de_regla(), "no hay ningún módulo de regla en scripts/guardrails/"


def test_todo_motivo_emitido_tiene_entrada():
    emitidos, _ = _slugs_emitidos()
    sin_declarar = sorted(emitidos - set(motivos.MOTIVOS))
    assert sin_declarar == [], (
        "estos slugs se emiten y no están en motivos.MOTIVOS: "
        + ", ".join(sin_declarar)
        + " -- un rechazo que no sabe decir por qué no es auditable"
    )


def test_todo_motivo_declarado_se_emite():
    emitidos, _ = _slugs_emitidos()
    sin_uso = sorted(set(motivos.MOTIVOS) - emitidos)
    assert sin_uso == [], (
        "estos slugs están declarados y nadie los emite: "
        + ", ".join(sin_uso)
        + " -- el catálogo crece por fase; una entrada sin emisor es una promesa"
    )


def test_el_slug_se_emite_literal():
    _, calculados = _slugs_emitidos()
    assert calculados == [], (
        "slug armado en tiempo de ejecución en: "
        + ", ".join(calculados)
        + " -- invisible al análisis estático, y deja el contrato sin efecto"
    )


def test_ningun_guardrail_lanza():
    culpables = []
    for ruta in _modulos_de_regla():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Raise):
                culpables.append(f"{ruta.name}:{nodo.lineno}")
    assert culpables == [], (
        "un guardrail lanza en: "
        + ", ".join(culpables)
        + " -- un hook que revienta no bloquea, y la escritura pasa sin revisar"
    )


def test_ningun_guardrail_escribe():
    prohibidos = ("write_text", "unlink", "rmtree", "os.remove", "mkdir", "makedirs")
    culpables = []
    for ruta in _modulos_de_regla():
        fuente = ruta.read_text(encoding="utf-8")
        for palabra in prohibidos:
            if palabra in fuente:
                culpables.append(f"{ruta.name} menciona {palabra}")
    assert culpables == [], "; ".join(culpables)


def test_falla_no_corrige_el_slug_que_le_pasan():
    # Mentir sobre qué pasó es peor que no saber nombrarlo. Quien caza el typo es
    # `test_todo_motivo_emitido_tiene_entrada`, en el commit y no en producción.
    v = veredicto.falla("slug_que_no_existe", "detalle")
    assert v.motivo == "slug_que_no_existe"
    assert not v.ok


def test_lo_no_clasificado_no_es_publicable():
    # Fail-closed, mismo criterio que `categoria_del_motivo` devolviendo None:
    # algo que nadie clasificó es, por defecto, un problema nuestro.
    assert not motivos.es_publicable("slug_que_no_existe")
    assert not veredicto.falla("slug_que_no_existe", "d").publicable
    assert veredicto.aprueba().publicable


def test_el_veredicto_positivo_no_nombra_motivo():
    v = veredicto.aprueba()
    assert v.ok and v.motivo == "" and v.ubicacion is None
    assert bool(v) is True


def test_primer_fallo_cortocircuita_en_orden():
    ok = veredicto.aprueba()
    a = veredicto.falla("guion_largo", "primero")
    b = veredicto.falla("voseo", "segundo")
    assert veredicto.primer_fallo([ok, a, b]).detalle == "primero"
    assert veredicto.primer_fallo([ok, ok]).ok
    assert veredicto.primer_fallo([]).ok
