"""La piel visual vive en una hoja compartida, no en tres copias."""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_STORIES = _REPO_ROOT / "templates" / "stories"
PIEL_CSS = DIR_STORIES / "piel.css"

# Las tres plantillas de la familia. Las otras ocho migran en Changes aparte
# (ver §6 de la spec): una plantilla por vez, porque cada una tiene su propia
# calibración de alturas.
FAMILIA = ("oportunidad.html", "alerta.html", "recomendacion.html")

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


def test_la_familia_enlaza_la_hoja():
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert 'href="piel.css"' in html, f"{nombre} no enlaza piel.css"


def test_la_hoja_se_carga_despues_de_marca():
    # marca.css define los tokens que piel.css consume: al revés, `var(--activo)`
    # resolvería a nada.
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert html.index('href="marca.css"') < html.index('href="piel.css"'), (
            f"{nombre} carga piel.css antes que marca.css"
        )


def test_ninguna_plantilla_redeclara_la_piel():
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        duplicadas = [regla for regla in REGLAS_DE_LA_PIEL if regla in html]
        assert not duplicadas, f"{nombre} redeclara reglas de la piel: {duplicadas}"
