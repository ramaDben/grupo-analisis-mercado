"""La paleta vive en marca.css y ninguna plantilla escribe un hex a mano."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import marca_tokens  # noqa: E402

MARCA_CSS = _REPO_ROOT / "templates" / "stories" / "marca.css"


def test_marca_css_declara_un_color_por_activo():
    css = MARCA_CSS.read_text(encoding="utf-8")

    for token in ("--activo-oro", "--activo-wti", "--activo-us100", "--activo-usdclp"):
        assert token in css, f"falta {token} en marca.css"


def test_marca_css_cascadea_el_rol_activo_por_clase():
    css = MARCA_CSS.read_text(encoding="utf-8")

    assert "body.activo-oro" in css
    assert "--activo: var(--activo-oro)" in css


def test_los_colores_de_activo_tienen_rol_en_el_mapa():
    # Sin esto, una plantilla que hardcodee #E8B44C recibiría "hex huérfano" en
    # vez de la sugerencia del token correcto.
    for hex_activo in ("#E8B44C", "#E8783C", "#4C86E8", "#C9743A"):
        assert hex_activo in marca_tokens.MAPA, f"{hex_activo} sin rol asignado"


def test_ninguna_plantilla_de_produccion_hardcodea_color():
    for plantilla in sorted((_REPO_ROOT / "templates" / "stories").glob("*.html")):
        html = plantilla.read_text(encoding="utf-8")
        _, _, huerfanos = marca_tokens._tokenizar(html)
        assert not huerfanos, f"{plantilla.name} trae hex sin token: {huerfanos}"


def test_el_gate_cubre_las_hojas_propias():
    hojas = [p.name for p in marca_tokens._hojas()]

    assert "piel.css" in hojas, "el gate no está escaneando piel.css"
    # marca.css es la fuente de los hex: escanearla la reportaría entera como
    # infracción.
    assert "marca.css" not in hojas


def test_ninguna_hoja_propia_hardcodea_color():
    for hoja in marca_tokens._hojas():
        css = hoja.read_text(encoding="utf-8")
        _, n, huerfanos = marca_tokens._tokenizar(css)
        assert not n and not huerfanos, f"{hoja.name} trae color a mano: {huerfanos or n}"
