"""Los extras de `pyproject.toml` tienen que cubrir lo que sus scripts importan.

El defecto que fija este test se descubrió el 2026-09-06 corriendo `/informe apertura`
desde Antigravity, el segundo runner. El extra `informe` declaraba solo `matplotlib`,
que es lo que necesita el gráfico, y nadie había mirado que el PDF lo compila
`generar_pdf.py`, que importa `markdown`, `pypdf` y `playwright` en el nivel de módulo.

**En este entorno el defecto era invisible**: los tres paquetes estaban instalados por
otras vías, así que el informe salía bien. En un clon nuevo, `uv sync --extra informe`
instalaba matplotlib y el render moría con `ModuleNotFoundError`. Es el mismo modo de
falla que motiva el resto del sistema: **funciona acá y se rompe en otro lado**, y no lo
descubre nadie hasta que lo necesita.

Es también un contrato por nombre, que es el defecto recurrente del repo: dos archivos
que se hablan sin que nada verifique que coinciden. Acá los dos son `pyproject.toml` y
la lista de imports de un script que vive en otra carpeta.
"""

import ast
import sys
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# El script y el extra que tiene que cubrirlo. Se declara el par explícitamente:
# adivinar qué extra corresponde a qué script sería otro contrato implícito.
PARES = [
    (".agents/skills/generar-reporte-editorial/scripts/generar_pdf.py", "informe"),
    ("scripts/grafico_informe.py", "informe"),
    ("scripts/story_render.py", "stories"),
]

# Import que no coincide con el nombre del paquete. Vacío hoy y acá por si aparece
# uno: `sklearn` se instala como `scikit-learn`, `yaml` como `PyYAML`.
ALIAS_DE_PAQUETE: dict[str, str] = {}


def _imports_de_nivel_superior(ruta: Path) -> set[str]:
    """Los módulos que el archivo importa fuera de una función.

    Solo el nivel superior: un import dentro de una función es carga diferida y una
    dependencia opcional legítima, que es como el repo maneja `MetaTrader5`.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    modulos: set[str] = set()
    for nodo in arbol.body:
        if isinstance(nodo, ast.Import):
            modulos.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def _de_terceros(modulos: set[str]) -> set[str]:
    locales = {p.stem for p in (_REPO_ROOT / "scripts").glob("*.py")}
    locales |= {p.name for p in (_REPO_ROOT / "src").iterdir() if p.is_dir()}
    return {m for m in modulos if m not in sys.stdlib_module_names and m not in locales}


def _declarados(extra: str) -> set[str]:
    cfg = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    proyecto = cfg.get("project", {})
    paquetes = list(proyecto.get("dependencies") or [])
    paquetes += list((proyecto.get("optional-dependencies") or {}).get(extra) or [])
    # De "playwright>=1.40" queda "playwright".
    nombres = set()
    for spec in paquetes:
        nombre = spec.split(";")[0].strip()
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
            nombre = nombre.split(sep)[0]
        nombres.add(nombre.strip().lower().replace("_", "-"))
    return nombres


def test_el_extra_informe_cubre_lo_que_el_generador_importa():
    faltantes: list[str] = []
    for rel, extra in PARES:
        ruta = _REPO_ROOT / rel
        if not ruta.is_file():
            continue  # el par se declara acá; que el archivo exista es otro problema
        declarados = _declarados(extra)
        for modulo in sorted(_de_terceros(_imports_de_nivel_superior(ruta))):
            paquete = ALIAS_DE_PAQUETE.get(modulo, modulo).lower().replace("_", "-")
            if paquete not in declarados:
                faltantes.append(f"{rel} importa {modulo!r}, ausente del extra {extra!r}")

    assert faltantes == [], (
        "\n".join(faltantes)
        + "\n\nUn extra que no cubre lo que su script importa funciona en el entorno "
        "donde el paquete ya estaba y falla en un clon nuevo, que es la peor forma de "
        "fallar: nadie lo descubre hasta que lo necesita."
    )


def test_los_pares_apuntan_a_archivos_que_existen():
    # Si un script se mueve o se renombra, el test de arriba lo saltea en silencio y
    # deja de proteger nada. Esto lo pone rojo en el mismo commit.
    faltan = [rel for rel, _ in PARES if not (_REPO_ROOT / rel).is_file()]
    assert faltan == [], "PARES apunta a archivos que no existen: " + ", ".join(faltan)


def test_todo_extra_nombrado_en_pares_existe():
    cfg = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = set((cfg.get("project", {}).get("optional-dependencies") or {}))
    usados = {extra for _, extra in PARES}
    assert usados <= extras, f"extras inexistentes en pyproject: {sorted(usados - extras)}"
