"""Tests del motor de render de Stories GI (`scripts/story_render.py`, issues #109/#119).

Cubre el mapeo puro payload -> HTML (`build_context`/`resolver_loops`/`build_html`, AC2-AC9)
sin depender de Playwright, y un test de integración de render real (AC1) que se salta
(`skipif`) si Chromium no está instalado en la máquina de ejecución. El módulo vive en
`scripts/` (fuera del paquete `market_data_mcp`), así que se inserta `scripts/` en `sys.path`
directamente en este archivo -- no se toca `conftest.py` (contrato de design.md D2/§5).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import story_render  # noqa: E402 (import tras el ajuste de sys.path)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "stories"
FIXTURE_TEMPLATE = FIXTURES_DIR / "fixture_template.html"
FIXTURE_CHART = FIXTURES_DIR / "fixture_chart.png"
ALERTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "alerta.html"
QUOTE_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "quote.html"

# Fixture inline de `resolver_loops` (R4/AC4-AC6): recibe `html: str`, sin archivo.
FIXTURE_FOR_HTML = "<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->"

# Payload de ejemplo de spec.md §"Contrato de datos", con `variacion`/`vol_pct`
# omitidos y `chart_png: None` (ejerce CB-4 y el fence `chart_svg`).
PAYLOAD_EJEMPLO: dict = {
    "plantilla": "alerta",
    "activo": {"ticker_mt5": "XAUUSD", "nombre": "Oro", "digits": 2},
    "chip_categoria": "COMMODITIES · ORO",
    "fecha_hora": "13 JUL 2026 · 11:15",
    "titular": "El Oro rompe soporte clave y activa señal de riesgo bajista",
    "parrafo": (
        "El metal perdió la zona de 2.320 con volumen creciente, confirmando "
        "presión vendedora. Un cierre bajo el soporte abriría espacio hacia "
        "nuevos mínimos; se recomienda gestión estricta del riesgo."
    ),
    "rotulo_activo": "ORO · XAU/USD",
    "tag_riesgo": "RIESGO ALTO",
    "precio_actual": "2.318,40",
    "soporte": "2.300,00",
    "resistencia": "2.360,00",
    "rotulo_grafico": "XAU/USD · VELAS 4H",
    "chart_png": None,
    "fuente": "COMEX",
    "sesgo": "Bajista",
}

# Payload de ejemplo de `quote` (spec.md/design.md #121 §"Contrato de payload
# story_quote"): tokens 100% escalares, sin fences ni loops.
PAYLOAD_QUOTE: dict = {
    "plantilla": "quote",
    "cita": "El mercado premia la paciencia más que la predicción.",
    "autor": "Nombre Analista",
    "autor_sub": "Head of Trading, Grupo Inteligencia",
}


def _png_size(path: Path) -> tuple[int, int]:
    """Lee width/height del chunk IHDR de un PNG (offsets 16/20, big-endian, sin Pillow)."""
    data = path.read_bytes()
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def _chromium_disponible() -> bool:
    """True si Playwright está instalado y su Chromium existe en disco. Cualquier
    excepción (módulo ausente, navegador no instalado, etc.) se traduce en `skip`."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# AC3 (heredado) / contrato mínimo aislado del snapshot de marca
# ---------------------------------------------------------------------------


def test_build_html_contract():
    html = story_render.build_html(PAYLOAD_EJEMPLO, FIXTURE_TEMPLATE)

    # Escalares inyectados.
    assert "COMMODITIES · ORO" in html
    assert "El Oro rompe soporte clave y activa señal de riesgo bajista" in html
    assert "2.318,40" in html
    assert "2.300,00" in html
    assert "2.360,00" in html
    assert "RIESGO ALTO" in html

    # Sin variación/vol/chart_png -> fences ausentes eliminados por completo.
    assert 'class="variacion"' not in html
    assert 'class="vol"' not in html
    assert "img-alerta" not in html

    # Fence complementario: sin chart_png -> se conserva el SVG decorativo.
    assert "svg-alerta" in html

    # Guardia: ningún token huérfano.
    assert "{{" not in html
    assert "}}" not in html


def test_build_html_token_huerfano_lanza_error(tmp_path):
    plantilla = tmp_path / "con_huerfano.html"
    plantilla.write_text(
        "<p>{{titular}}</p><p>{{token_inventado}}</p>", encoding="utf-8"
    )

    with pytest.raises(story_render.StoryRenderError):
        story_render.build_html(PAYLOAD_EJEMPLO, plantilla)


# ---------------------------------------------------------------------------
# AC2/AC7: tokens escalares dinámicos + catálogo de helpers en build_context
# ---------------------------------------------------------------------------


def test_build_context_escalar_extra_no_op():
    payload = {**PAYLOAD_EJEMPLO, "nota_interna": "solo para QA"}

    html = story_render.build_html(payload, FIXTURE_TEMPLATE)

    assert "nota_interna" not in html
    assert "solo para QA" not in html


def test_build_context_impacto_badge():
    payload = {**PAYLOAD_EJEMPLO, "impacto": "alto"}

    contexto = story_render.build_context(payload)

    assert contexto["impacto_badge"] == "ALTO"


# ---------------------------------------------------------------------------
# AC4-AC6: resolver_loops (array vacío / 1 elemento / N elementos)
# ---------------------------------------------------------------------------


def test_resolver_loops_vacio():
    resultado = story_render.resolver_loops(FIXTURE_FOR_HTML, {"filas": []})

    assert resultado == ""
    assert "{{nombre}}" not in resultado
    assert "FOR:filas" not in resultado
    assert "ENDFOR:filas" not in resultado


def test_resolver_loops_uno():
    resultado = story_render.resolver_loops(
        FIXTURE_FOR_HTML, {"filas": [{"nombre": "USD/CLP"}]}
    )

    assert resultado.count("USD/CLP") == 1
    assert "{{nombre}}" not in resultado
    assert "FOR:filas" not in resultado
    assert "ENDFOR:filas" not in resultado


def test_resolver_loops_n():
    payload = {
        "filas": [
            {"nombre": "USD/CLP"},
            {"nombre": "Oro"},
            {"nombre": "WTI"},
        ]
    }

    resultado = story_render.resolver_loops(FIXTURE_FOR_HTML, payload)

    assert resultado.count("USD/CLP") == 1
    assert resultado.count("Oro") == 1
    assert resultado.count("WTI") == 1
    assert resultado.index("USD/CLP") < resultado.index("Oro") < resultado.index("WTI")
    assert "FOR:filas" not in resultado
    assert "ENDFOR:filas" not in resultado
    assert "{{nombre}}" not in resultado


# ---------------------------------------------------------------------------
# AC8: orden canónico loops -> fences -> tokens -> guardia (fence por elemento)
# ---------------------------------------------------------------------------


def test_orden_canonico_loops_fences(tmp_path):
    plantilla = tmp_path / "loops_con_fence.html"
    plantilla.write_text(
        "<!-- FOR:filas -->"
        "<p>{{nombre}}<!-- IF:activo --> (activo)<!-- ENDIF:activo --></p>"
        "<!-- ENDFOR:filas -->",
        encoding="utf-8",
    )
    payload = {
        "filas": [
            {"nombre": "USD/CLP", "activo": True},
            {"nombre": "Oro", "activo": False},
        ]
    }

    html = story_render.build_html(payload, plantilla)

    # Cada fila se evalúa con sus propios datos -- no una sola vez sobre el payload.
    assert "USD/CLP (activo)" in html
    assert "Oro (activo)" not in html
    assert "<p>Oro</p>" in html
    assert "FOR:filas" not in html
    assert "IF:activo" not in html
    assert "{{" not in html


# ---------------------------------------------------------------------------
# AC9: snapshot de marca `templates/stories/alerta.html`
# ---------------------------------------------------------------------------


def test_alerta_no_placeholders():
    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html

    for valor in (
        PAYLOAD_EJEMPLO["titular"],
        PAYLOAD_EJEMPLO["parrafo"],
        PAYLOAD_EJEMPLO["precio_actual"],
        PAYLOAD_EJEMPLO["soporte"],
        PAYLOAD_EJEMPLO["resistencia"],
        PAYLOAD_EJEMPLO["tag_riesgo"],
    ):
        assert valor in html

    # Payload sin variación/vol -> esos slots no aparecen; sin chart_png -> SVG
    # decorativo presente, sin <img>.
    assert "<img" not in html
    assert "<svg" in html


def test_alerta_chart_embebido():
    payload = copy.deepcopy(PAYLOAD_EJEMPLO)
    payload["chart_png"] = str(FIXTURE_CHART)

    html = story_render.build_html(payload, ALERTA_TEMPLATE)

    assert "<img" in html
    assert "file:///" in html
    assert "<svg" not in html


def test_alerta_chart_png_inexistente_lanza_error():
    payload = copy.deepcopy(PAYLOAD_EJEMPLO)
    payload["chart_png"] = str(FIXTURES_DIR / "no_existe.png")

    with pytest.raises(story_render.StoryRenderError):
        story_render.build_html(payload, ALERTA_TEMPLATE)


# ---------------------------------------------------------------------------
# AC1: dimensiones exactas del render (requiere Chromium; se salta si no está)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_render_dimensiones_1920x1080(tmp_path):
    salida = tmp_path / "story_test.png"

    resultado = story_render.render_story(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# AC3/AC4/AC5 (#121): snapshot de marca `templates/stories/quote.html`
# ---------------------------------------------------------------------------


def test_quote_no_placeholders():
    html = story_render.build_html(PAYLOAD_QUOTE, QUOTE_TEMPLATE)

    assert PAYLOAD_QUOTE["cita"] in html
    assert PAYLOAD_QUOTE["autor"] in html
    assert PAYLOAD_QUOTE["autor_sub"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_quote_autor_sub_vacio():
    payload = {**PAYLOAD_QUOTE, "autor_sub": ""}

    html = story_render.build_html(payload, QUOTE_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_quote_render_dimensiones(tmp_path):
    salida = tmp_path / "story_quote_test.png"

    resultado = story_render.render_story(PAYLOAD_QUOTE, QUOTE_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)
