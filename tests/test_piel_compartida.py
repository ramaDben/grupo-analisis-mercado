"""La piel visual vive en una hoja compartida, no en tres copias.

Desde el 2026-08-12 las hojas no se enlazan: se **embeben**. Playwright navega el
HTML resuelto con `file://` desde una carpeta temporal y no resolvía
`<link href="piel.css">`, así que la pieza salía sin estilos y sin error visible.
`scripts/sincronizar_css_plantillas.py` copia las hojas dentro de un primer
`<style>`, marcado, y deja el `<style>` propio de la plantilla aparte.

Estos guardias siguen verificando lo mismo de siempre —que la hoja sea la fuente
y que nadie la duplique—, pero contra esa arquitectura. Escritos contra el
`<link>`, llevaban semanas fallando por una razón que no era un defecto de las
plantillas.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from sincronizar_css_plantillas import (  # noqa: E402
    MARCADOR_MARCA,
    MARCADOR_PIEL,
    quitar_css_embebido,
)

DIR_STORIES = _REPO_ROOT / "templates" / "stories"
PIEL_CSS = DIR_STORIES / "piel.css"

# Las tres plantillas de la familia. Las otras ocho migran en Changes aparte
# (ver §6 de la spec): una plantilla por vez, porque cada una tiene su propia
# calibración de alturas.
FAMILIA = ("alerta.html",)

# Reglas que, por definición, viven en la hoja. Si una plantilla las redeclara,
# volvemos a tener copias desincronizadas — que es exactamente lo que la hoja
# existe para evitar.
REGLAS_DE_LA_PIEL = (".velo {", ".grilla {", ".sello {", ".pulso {", ".cta-flecha {")


def test_la_hoja_existe():
    assert PIEL_CSS.exists(), "falta templates/stories/piel.css"


def test_la_hoja_declara_las_capas_de_fondo():
    css = PIEL_CSS.read_text(encoding="utf-8")

    for clase in (".foto-activo", ".velo", ".grilla", ".sello", ".pulso", ".cta"):
        assert clase in css, f"falta {clase} en piel.css"


def test_la_hoja_declara_las_fuentes():
    css = PIEL_CSS.read_text(encoding="utf-8")

    assert css.count("@font-face") >= 5
    assert "space-grotesk-700.woff2" in css
    assert "dm-sans-400.woff2" in css


def test_la_familia_incorpora_la_hoja():
    """Embebida con su marcador, o enlazada si alguna vez se vuelve al `<link>`."""
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert MARCADOR_PIEL in html or 'href="piel.css"' in html, (
            f"{nombre} no incorpora piel.css"
        )


def test_la_hoja_se_carga_despues_de_marca():
    """marca.css define los tokens que piel.css consume.

    Al revés, `var(--activo)` resolvería a nada y la pieza saldría sin su color
    de activo: la cascada no falla, simplemente no encuentra el valor.
    """
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert html.index(MARCADOR_MARCA) < html.index(MARCADOR_PIEL), (
            f"{nombre} embebe piel.css antes que marca.css"
        )


def test_ninguna_plantilla_redeclara_la_piel():
    """La regla puede estar en el bloque embebido; lo que no puede es estar DOS veces.

    Antes bastaba con buscarla en el archivo, porque la hoja se enlazaba y su
    contenido no vivía ahí. Ahora sí vive, así que buscarla a secas acusa de
    duplicar a toda plantilla que simplemente incorpora la piel. Se mira el CSS
    propio, que es donde una redeclaración sería una copia de verdad.
    """
    for nombre in FAMILIA:
        propio = quitar_css_embebido((DIR_STORIES / nombre).read_text(encoding="utf-8"))
        duplicadas = [regla for regla in REGLAS_DE_LA_PIEL if regla in propio]
        assert not duplicadas, f"{nombre} redeclara reglas de la piel: {duplicadas}"


def test_una_regla_de_la_piel_en_el_css_propio_si_se_detecta():
    """La contraparte del test de arriba.

    Ese verifica que incorporar la piel no se confunda con duplicarla; este,
    que duplicarla de verdad siga siendo detectado. Sin los dos, "no duplica"
    y "no mira" son indistinguibles.
    """
    sucio = (
        "<style>\n"
        f"  {MARCADOR_MARCA}\n"
        f"  {MARCADOR_PIEL}\n"
        "  .sello { opacity: 1; }\n"
        "</style>\n"
        "<style>\n"
        "  .sello { opacity: 0.5; }\n"
        "</style>\n"
    )
    propio = quitar_css_embebido(sucio)
    assert [r for r in REGLAS_DE_LA_PIEL if r in propio] == [".sello {"]

