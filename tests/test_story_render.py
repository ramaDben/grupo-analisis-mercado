"""Tests del motor de render de Stories GI (`scripts/story_render.py`, issues #109/#119).

Cubre el mapeo puro payload -> HTML (`build_context`/`resolver_loops`/`build_html`, AC2-AC9)
sin depender de Playwright, y un test de integración de render real (AC1) que se salta
(`skipif`) si Chromium no está instalado en la máquina de ejecución. El módulo vive en
`scripts/` (fuera del paquete `market_data_mcp`), así que se inserta `scripts/` en `sys.path`
directamente en este archivo -- no se toca `conftest.py` (contrato de design.md D2/§5).
"""

from __future__ import annotations

import copy
import json
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
BREAKING_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "breaking.html"
ENCUESTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "encuesta.html"
EDU_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "edu.html"
FLASH_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "flash.html"
POSTVENTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "postventa.html"

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
    # `tag_riesgo` ya NO lo consume el snapshot de alerta: la píldora de la
    # tarjeta pasó a mostrar el sesgo (dirección accionable) en vez de una
    # etiqueta de riesgo sin criterio visible para el cliente. Se conserva aquí
    # sólo porque el fixture genérico del motor (`fixture_template.html`) lo usa
    # como token de prueba en `test_build_html_contract`; para `alerta.html` es
    # una clave no referenciada, o sea un no-op silencioso (R3/CB-1).
    "tag_riesgo": "RIESGO ALTO",
    "precio_actual": "2.318,40",
    "soporte": "2.300,00",
    "resistencia": "2.360,00",
    "rotulo_grafico": "XAU/USD · VELAS 4H",
    "chart_png": None,
    "fuente": "COMEX",
    "sesgo": "Bajista",
    # El grafico de `alerta` dejo de ser un dibujo fijo del snapshot y pasa a ser
    # un token, alimentado por `scripts/story_grafico.py` con la serie real.
    # Aca va un SVG minimo a proposito: estos tests ejercen el mapeo de tokens y
    # fences, no la geometria del grafico. La geometria se prueba con la fixture
    # de `tests/fixtures/stories/payloads/alerta.json`, que si trae `recorrido`.
    "grafico": '<svg viewBox="0 0 440 400"></svg>',
    "sello_datos": "Datos reales · MetaTrader 5 · 13 JUL 11:15",
}

# Payload de ejemplo de `quote` (spec.md/design.md #121 §"Contrato de payload
# story_quote"): tokens 100% escalares, sin fences ni loops.
PAYLOAD_QUOTE: dict = {
    "plantilla": "quote",
    "cita": "El mercado premia la paciencia más que la predicción.",
    "autor": "Nombre Analista",
    "autor_sub": "Head of Trading, Grupo Inteligencia",
}

# Payload de ejemplo de `breaking` (spec.md/design.md #123 §"Contrato de payload
# story_breaking"): tokens 100% escalares, sin fences ni loops. `kicker_tema` es el
# único campo opcional (resuelto por CSS `:empty`, no por el motor).
PAYLOAD_BREAKING: dict = {
    "plantilla": "breaking",
    "kicker_tema": "BANCOS CENTRALES",
    "titular": "La Fed sorprende con una pausa más larga de lo esperado",
    "valor": "5,50%",
    "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
    "parrafo_reaccion": (
        "El mercado ajusta expectativas hacia un primer recorte más tardío, "
        "presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
    ),
}

# Payload de ejemplo de `encuesta` (spec.md/design.md #125 §"Contrato de payload
# story_encuesta"): tokens 100% escalares, sin fences ni loops. `kicker` y
# `nota_cierre` son los dos campos opcionales (resueltos por CSS `:empty`, no por
# el motor).
PAYLOAD_ENCUESTA: dict = {
    "plantilla": "encuesta",
    "kicker": "ENCUESTA DEL DÍA",
    "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
    "opcion_a": "Alcista",
    "opcion_b": "Bajista",
    "nota_cierre": "Vota en la encuesta fijada del grupo",
}


# Payload de ejemplo de `edu` (spec.md/design.md #127 §"Contrato de payload story_edu").
# Primer consumidor real del mecanismo FOR: `bullets` es un array de objetos `{"texto": ...}`.
# `ejemplo` ya viene APLANADO a `valor_a`/`operador`/`valor_b` escalares (el motor solo resuelve
# claves escalares top-level, no `ejemplo.valor_a`). `kicker` es el único campo opcional
# (resuelto por CSS `:empty`, no por el motor).
PAYLOAD_EDU: dict = {
    "plantilla": "edu",
    "kicker": "CONCEPTO DE LA SEMANA",
    "titulo_concepto": "Cruce de medias móviles",
    "definicion": (
        "Cuando una media rápida cruza a una lenta, señala un posible cambio de tendencia."
    ),
    "valor_a": "Media 50",
    "operador": "cruza sobre",
    "valor_b": "Media 200",
    "bullets": [
        {"texto": "Cruce al alza (media rápida sobre lenta) da sesgo comprador"},
        {"texto": "Cruce a la baja da sesgo vendedor"},
        {"texto": "Confirma con el precio, no operes solo por el cruce"},
    ],
}


# Payload de ejemplo de `flash` (spec.md/design.md #129 §"Contrato de payload story_flash").
# Segundo consumidor real del mecanismo FOR: `filas` es un array de objetos de claves ESCALARES
# (`nombre`/`tipo`/`valor`/`variacion`/`direccion`). `variacion` ya viene APLANADA a un escalar
# (pct formateado) y `direccion` es un slug aparte que el snapshot usa como clase CSS
# (`flash-var--<direccion>`) — el motor solo resuelve claves escalares por objeto dentro del FOR,
# no deriva flecha/color (eso lo hace el CSS). `kicker` es el único campo opcional (resuelto por
# CSS `:empty`, no por el motor).
PAYLOAD_FLASH: dict = {
    "plantilla": "flash",
    "kicker": "CIERRE DE MERCADO",
    "titulo": "Así cerró el mercado hoy",
    "fecha": "16 JUL 2026 · 17:30",
    "filas": [
        {
            "nombre": "USD/CLP",
            "tipo": "Divisa",
            "valor": "889,60",
            "variacion": "+0,42%",
            "direccion": "alcista",
        },
        {
            "nombre": "Oro",
            "tipo": "Metal",
            "valor": "2.318,40",
            "variacion": "-1,86%",
            "direccion": "bajista",
        },
        {
            "nombre": "WTI",
            "tipo": "Energía",
            "valor": "78,320",
            "variacion": "0,00%",
            "direccion": "lateral",
        },
    ],
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
        PAYLOAD_EJEMPLO["sesgo"],
    ):
        assert valor in html

    # La píldora de la tarjeta muestra el sesgo con su clase de color semántico,
    # y el antiguo elemento del tag de riesgo ya no se emite aunque el payload
    # siga trayendo la clave. Se afirma sobre la clase y no sobre el texto
    # "RIESGO ALTO", que sigue apareciendo en el comentario del CSS que documenta
    # por qué se reemplazó.
    assert 'class="tag-sesgo tag-sesgo--bajista"' in html
    assert 'class="tag-riesgo"' not in html
    assert ">RIESGO ALTO<" not in html

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


# ---------------------------------------------------------------------------
# AC3/AC4/AC5 (#123): snapshot de marca `templates/stories/breaking.html`
# ---------------------------------------------------------------------------


def test_breaking_no_placeholders():
    html = story_render.build_html(PAYLOAD_BREAKING, BREAKING_TEMPLATE)

    assert PAYLOAD_BREAKING["kicker_tema"] in html
    assert PAYLOAD_BREAKING["titular"] in html
    assert PAYLOAD_BREAKING["valor"] in html
    assert PAYLOAD_BREAKING["contexto"] in html
    assert PAYLOAD_BREAKING["parrafo_reaccion"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_breaking_kicker_vacio():
    payload = {**PAYLOAD_BREAKING, "kicker_tema": ""}

    html = story_render.build_html(payload, BREAKING_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_breaking_render_dimensiones(tmp_path):
    salida = tmp_path / "story_breaking_test.png"

    resultado = story_render.render_story(PAYLOAD_BREAKING, BREAKING_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# AC3/AC4/AC5/AC6 (#125): snapshot templates/stories/encuesta.html
# ---------------------------------------------------------------------------


def test_encuesta_no_placeholders():
    html = story_render.build_html(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE)

    assert PAYLOAD_ENCUESTA["kicker"] in html
    assert PAYLOAD_ENCUESTA["pregunta"] in html
    assert PAYLOAD_ENCUESTA["opcion_a"] in html
    assert PAYLOAD_ENCUESTA["opcion_b"] in html
    assert PAYLOAD_ENCUESTA["nota_cierre"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_encuesta_kicker_vacio():
    payload = {**PAYLOAD_ENCUESTA, "kicker": ""}

    html = story_render.build_html(payload, ENCUESTA_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


def test_encuesta_nota_vacio():
    payload = {**PAYLOAD_ENCUESTA, "nota_cierre": ""}

    html = story_render.build_html(payload, ENCUESTA_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_encuesta_render_dimensiones(tmp_path):
    salida = tmp_path / "story_encuesta_test.png"

    resultado = story_render.render_story(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# AC3/AC4/AC5/AC6 (#127): snapshot templates/stories/edu.html — PRIMER
# consumidor real del mecanismo FOR (bullets[]).
# ---------------------------------------------------------------------------


def test_edu_no_placeholders():
    html = story_render.build_html(PAYLOAD_EDU, EDU_TEMPLATE)

    assert PAYLOAD_EDU["kicker"] in html
    assert PAYLOAD_EDU["titulo_concepto"] in html
    assert PAYLOAD_EDU["definicion"] in html
    assert PAYLOAD_EDU["valor_a"] in html
    assert PAYLOAD_EDU["operador"] in html
    assert PAYLOAD_EDU["valor_b"] in html
    for bullet in PAYLOAD_EDU["bullets"]:
        assert bullet["texto"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_edu_kicker_vacio():
    payload = {**PAYLOAD_EDU, "kicker": ""}

    html = story_render.build_html(payload, EDU_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


def test_edu_bullets_vacio():
    payload = {**PAYLOAD_EDU, "bullets": []}

    html = story_render.build_html(payload, EDU_TEMPLATE)

    assert "FOR:bullets" not in html
    assert "ENDFOR:bullets" not in html
    assert "{{texto}}" not in html
    assert "{{" not in html
    assert "}}" not in html


def test_edu_bullets_uno():
    payload = {**PAYLOAD_EDU, "bullets": [{"texto": "Un único punto de aplicación"}]}

    html = story_render.build_html(payload, EDU_TEMPLATE)

    assert html.count("Un único punto de aplicación") == 1
    assert "FOR:bullets" not in html
    assert "{{texto}}" not in html


def test_edu_bullets_n():
    html = story_render.build_html(PAYLOAD_EDU, EDU_TEMPLATE)

    textos = [bullet["texto"] for bullet in PAYLOAD_EDU["bullets"]]
    for texto in textos:
        assert html.count(texto) == 1
    assert html.index(textos[0]) < html.index(textos[1]) < html.index(textos[2])
    assert "FOR:bullets" not in html
    assert "ENDFOR:bullets" not in html
    assert "{{texto}}" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_edu_render_dimensiones(tmp_path):
    salida = tmp_path / "story_edu_test.png"

    resultado = story_render.render_story(PAYLOAD_EDU, EDU_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# AC3/AC4/AC5/AC6 (#129): snapshot templates/stories/flash.html — PRIMERA
# plantilla de Fase C (listas). Segundo consumidor real del mecanismo FOR
# (filas[]), esta vez iterando varios tokens escalares por fila.
# ---------------------------------------------------------------------------


def test_flash_no_placeholders():
    html = story_render.build_html(PAYLOAD_FLASH, FLASH_TEMPLATE)

    assert PAYLOAD_FLASH["kicker"] in html
    assert PAYLOAD_FLASH["titulo"] in html
    assert PAYLOAD_FLASH["fecha"] in html
    for fila in PAYLOAD_FLASH["filas"]:
        assert fila["nombre"] in html
        assert fila["tipo"] in html
        assert fila["valor"] in html
        assert fila["variacion"] in html
        # `direccion` no aparece como texto visible, sino como clase CSS de la celda.
        assert f"flash-var--{fila['direccion']}" in html
    assert "{{" not in html
    assert "}}" not in html


def test_flash_kicker_vacio():
    payload = {**PAYLOAD_FLASH, "kicker": ""}

    html = story_render.build_html(payload, FLASH_TEMPLATE)

    assert "{{" not in html
    assert "}}" not in html


def test_flash_filas_vacio():
    payload = {**PAYLOAD_FLASH, "filas": []}

    html = story_render.build_html(payload, FLASH_TEMPLATE)

    assert "FOR:filas" not in html
    assert "ENDFOR:filas" not in html
    assert "{{nombre}}" not in html
    assert "{{variacion}}" not in html
    assert "{{" not in html
    assert "}}" not in html
    # El encabezado de la tabla (fuera del FOR) persiste con la lista vacía.
    assert "Activo" in html


def test_flash_filas_uno():
    payload = {
        **PAYLOAD_FLASH,
        "filas": [
            {
                "nombre": "USD/CLP",
                "tipo": "Divisa",
                "valor": "889,60",
                "variacion": "+0,42%",
                "direccion": "alcista",
            }
        ],
    }

    html = story_render.build_html(payload, FLASH_TEMPLATE)

    assert html.count("USD/CLP") == 1
    assert "FOR:filas" not in html
    assert "{{nombre}}" not in html


def test_flash_filas_n():
    html = story_render.build_html(PAYLOAD_FLASH, FLASH_TEMPLATE)

    nombres = [fila["nombre"] for fila in PAYLOAD_FLASH["filas"]]
    for nombre in nombres:
        assert html.count(nombre) == 1
    assert html.index(nombres[0]) < html.index(nombres[1]) < html.index(nombres[2])
    assert "FOR:filas" not in html
    assert "ENDFOR:filas" not in html
    assert "{{nombre}}" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_flash_render_dimensiones(tmp_path):
    salida = tmp_path / "story_flash_test.png"

    resultado = story_render.render_story(PAYLOAD_FLASH, FLASH_TEMPLATE, salida)

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# snapshot templates/stories/postventa.html -- pieza INTERNA del parte de
# post-venta: chip no suprimible, color semantico en los niveles y DOS loops
# independientes (respuestas / no_promesas).
#
# Los asserts de ausencia ("no debe aparecer X") se hacen contra `_body()`, no
# contra el HTML completo: el comentario de cabecera del snapshot documenta lo
# que el footer NO lleva (y por tanto nombra esas cadenas), y el <style> define
# las tres clases de sesgo aunque solo una se aplique en el cuerpo.
# ---------------------------------------------------------------------------

PAYLOAD_POSTVENTA: dict = {
    "plantilla": "postventa",
    "fecha_hora": "28 JUL 2026 · 19:23",
    "consulta": "¿Me afecta que no bajen la tasa?",
    "respuesta": "No, ya estaba en el precio. Mañana manda la Fed.",
    "activo_nombre": "USD/CLP",
    "soporte": "$923.90",
    "precio": "$930.50",
    "resistencia": "$930.80",
    "sesgo": "Bajista",
    "respuestas": [
        {"texto": "¿Cierro? → Depende del plazo, no del dato de hoy"},
        {"texto": "¿Por qué no bajan? → Inflación 4,3% contra la meta de 3%"},
        {"texto": "Con la posición en contra: explica el nivel"},
    ],
    "no_promesas": [
        {"texto": "Que el dólar siga bajando: mañana define la Fed"},
        {"texto": "Que el Banco Central baje pronto"},
    ],
    "fuente": "MT5 · GRUPO INTELIGENCIA",
}


def _body(html: str) -> str:
    """Devuelve solo el <body> del HTML resuelto (sin comentario ni <style>)."""
    return html[html.index("<body") : html.index("</body>")]


def test_postventa_no_placeholders():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    assert PAYLOAD_POSTVENTA["consulta"] in html
    assert PAYLOAD_POSTVENTA["respuesta"] in html
    assert PAYLOAD_POSTVENTA["soporte"] in html
    assert PAYLOAD_POSTVENTA["precio"] in html
    assert PAYLOAD_POSTVENTA["resistencia"] in html
    for item in PAYLOAD_POSTVENTA["respuestas"]:
        assert item["texto"] in html
    for item in PAYLOAD_POSTVENTA["no_promesas"]:
        assert item["texto"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_postventa_chip_interno_no_suprimible():
    """El chip de INTERNO es literal del snapshot: ningun payload lo quita.

    Los asserts comparan contra el texto tal como esta escrito en el HTML
    fuente ("Interno", "Post-venta"). Las mayusculas que se ven en el PNG las
    aplica el CSS con `text-transform: uppercase`, que no altera el HTML.
    """
    payload = {**PAYLOAD_POSTVENTA, "kicker": "", "chip": ""}

    cuerpo = _body(story_render.build_html(payload, POSTVENTA_TEMPLATE))

    assert "Interno" in cuerpo
    assert "Post-venta" in cuerpo


def test_postventa_footer_sin_marca_publica():
    cuerpo = _body(story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE))

    assert "@grupointeligencia" not in cuerpo
    assert "grupointeligencia.com" not in cuerpo
    assert "apalancamiento" not in cuerpo
    assert "No reenviar" in cuerpo


def test_postventa_sesgo_slug_bajista():
    cuerpo = _body(story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE))

    assert "pv-sesgo--bajista" in cuerpo
    assert "pv-sesgo--alcista" not in cuerpo


def test_postventa_sesgo_slug_alcista():
    payload = {**PAYLOAD_POSTVENTA, "sesgo": "Alcista"}

    cuerpo = _body(story_render.build_html(payload, POSTVENTA_TEMPLATE))

    assert "pv-sesgo--alcista" in cuerpo
    assert "pv-sesgo--bajista" not in cuerpo


def test_postventa_sesgo_slug_lateral():
    payload = {**PAYLOAD_POSTVENTA, "sesgo": "Lateral"}

    cuerpo = _body(story_render.build_html(payload, POSTVENTA_TEMPLATE))

    assert "pv-sesgo--lateral" in cuerpo


def test_postventa_listas_vacias_conservan_rotulos():
    payload = {**PAYLOAD_POSTVENTA, "respuestas": [], "no_promesas": []}

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert "FOR:respuestas" not in html
    assert "ENDFOR:respuestas" not in html
    assert "FOR:no_promesas" not in html
    assert "ENDFOR:no_promesas" not in html
    # Texto tal como esta en el HTML: el uppercase lo aplica el CSS.
    assert "Qué responder" in html
    assert "Qué NO prometer" in html
    assert "{{texto}}" not in html
    assert "{{" not in html


def test_postventa_listas_independientes():
    """Una lista con N y la otra con 1 no se contaminan entre si."""
    payload = {
        **PAYLOAD_POSTVENTA,
        "no_promesas": [{"texto": "Único límite del día"}],
    }

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert html.count("Único límite del día") == 1
    for item in PAYLOAD_POSTVENTA["respuestas"]:
        assert html.count(item["texto"]) == 1
    assert "{{texto}}" not in html


def test_postventa_orden_de_respuestas():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    textos = [item["texto"] for item in PAYLOAD_POSTVENTA["respuestas"]]
    assert html.index(textos[0]) < html.index(textos[1]) < html.index(textos[2])


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_postventa_render_dimensiones(tmp_path):
    salida = tmp_path / "story_postventa_test.png"

    resultado = story_render.render_story(
        PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE, salida
    )

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# Formato vertical 9:16 (Change fundacional). El formato viaja por el CLI /
# argumento de `render_story`, NUNCA por el payload: el payload es contrato de
# contenido y el formato es presentacion, asi el mismo payload rinde ambos.
# El default es "horizontal", de modo que los 7 tests de dimensiones previos
# siguen valiendo sin tocarse.
# ---------------------------------------------------------------------------


def test_formatos_mapa_cerrado():
    assert story_render._FORMATOS["horizontal"] == (1920, 1080)
    assert story_render._FORMATOS["vertical"] == (1080, 1920)


def test_formato_desconocido_lanza_error_accionable():
    with pytest.raises(story_render.StoryRenderError) as exc:
        story_render.resolver_viewport("cuadrado")

    mensaje = str(exc.value)
    assert "cuadrado" in mensaje
    assert "horizontal" in mensaje
    assert "vertical" in mensaje


def test_resolver_viewport_default_horizontal():
    assert story_render.resolver_viewport() == (1920, 1080)
    assert story_render.resolver_viewport("horizontal") == (1920, 1080)
    assert story_render.resolver_viewport("vertical") == (1080, 1920)


def test_build_html_es_independiente_del_formato():
    """El formato es puramente CSS: el HTML resuelto no cambia."""
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    assert "100vw" in html
    assert "max-aspect-ratio" in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_postventa_render_vertical_dimensiones(tmp_path):
    salida = tmp_path / "story_postventa_vertical.png"

    resultado = story_render.render_story(
        PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE, salida, formato="vertical"
    )

    assert resultado == salida
    assert _png_size(salida) == (1080, 1920)


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_postventa_render_horizontal_sigue_siendo_default(tmp_path):
    """Retrocompatibilidad: sin `formato`, el resultado no cambia."""
    salida = tmp_path / "story_postventa_default.png"

    story_render.render_story(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE, salida)

    assert _png_size(salida) == (1920, 1080)


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_postventa_vertical_apila_las_columnas(tmp_path):
    """En vertical la columna de 'no prometer' cae DEBAJO de la de 'responder';
    en horizontal quedan lado a lado. Se mide con el bounding box real."""
    from playwright.sync_api import sync_playwright

    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)
    tmp_html = POSTVENTA_TEMPLATE.parent / "_test_vertical_probe.html"
    tmp_html.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                cajas = {}
                for nombre, (w, h) in story_render._FORMATOS.items():
                    page = browser.new_page(
                        viewport={"width": w, "height": h}, device_scale_factor=1
                    )
                    page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
                    cajas[nombre] = (
                        page.locator(".pv-col--responder").bounding_box(),
                        page.locator(".pv-col--prometer").bounding_box(),
                    )
                    page.close()
            finally:
                browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    resp_h, prom_h = cajas["horizontal"]
    resp_v, prom_v = cajas["vertical"]

    # Horizontal: lado a lado (misma altura, distinta x)
    assert prom_h["x"] > resp_h["x"]
    assert abs(prom_h["y"] - resp_h["y"]) < 2

    # Vertical: apiladas (misma x, distinta altura)
    assert prom_v["y"] > resp_v["y"]
    assert abs(prom_v["x"] - resp_v["x"]) < 2


# ---------------------------------------------------------------------------
# alerta.html en formato vertical (Change 1 de la serie movil). Mismo patron
# que postventa: el snapshot deja de declarar su tamano y adapta el layout con
# `@media (max-aspect-ratio: 1/1)`. Aqui el bloque que se apila es `.contenido`
# (columna editorial + columna del grafico).
# ---------------------------------------------------------------------------


def test_alerta_snapshot_es_responsive():
    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)

    assert "100vw" in html
    assert "max-aspect-ratio" in html
    assert "width: 1920px" not in html
    assert "height: 1080px" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_alerta_render_vertical_dimensiones(tmp_path):
    salida = tmp_path / "story_alerta_vertical.png"

    story_render.render_story(
        PAYLOAD_EJEMPLO, ALERTA_TEMPLATE, salida, formato="vertical"
    )

    assert _png_size(salida) == (1080, 1920)


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_alerta_render_horizontal_sin_regresion(tmp_path):
    salida = tmp_path / "story_alerta_horizontal.png"

    story_render.render_story(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE, salida)

    assert _png_size(salida) == (1920, 1080)


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_alerta_vertical_apila_editorial_y_grafico(tmp_path):
    """En vertical la columna del grafico cae DEBAJO de la editorial; en
    horizontal quedan lado a lado. Se mide con el bounding box real."""
    from playwright.sync_api import sync_playwright

    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)
    tmp_html = ALERTA_TEMPLATE.parent / "_test_alerta_probe.html"
    tmp_html.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                cajas = {}
                for nombre, (w, h) in story_render._FORMATOS.items():
                    page = browser.new_page(
                        viewport={"width": w, "height": h}, device_scale_factor=1
                    )
                    page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
                    cajas[nombre] = (
                        page.locator(".columna-editorial").bounding_box(),
                        page.locator(".columna-grafico").bounding_box(),
                    )
                    page.close()
            finally:
                browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    edi_h, graf_h = cajas["horizontal"]
    edi_v, graf_v = cajas["vertical"]

    # Horizontal: lado a lado
    assert graf_h["x"] > edi_h["x"]
    assert abs(graf_h["y"] - edi_h["y"]) < 2

    # Vertical: apiladas
    assert graf_v["y"] > edi_v["y"]
    assert abs(graf_v["x"] - edi_v["x"]) < 2


# ---------------------------------------------------------------------------
# Contrato de TODAS las plantillas, desde las fixtures compartidas
# ---------------------------------------------------------------------------
# Los tests de arriba cubren plantilla por plantilla con payloads escritos como
# constantes. Eso dejó un agujero: `recomendacion`, `dato_macro` y `operacion`
# llegaron sin test, así que nada avisaba si un cambio en el motor les rompía el
# contrato.
#
# Este bloque cierra el agujero de raíz. Recorre `tests/fixtures/stories/payloads/`
# y exige que TODA plantilla de `templates/stories/` tenga su payload y resuelva
# sin tokens huérfanos. Una plantilla nueva sin fixture falla el test — que es lo
# que corresponde, porque una plantilla que nadie testea tampoco es una que
# alguien esté revisando.
#
# Son las MISMAS fixtures que usa `scripts/rendir_todas.py` para la revisión
# visual. Una fixture que solo vive en el test se desactualiza sin que nadie lo
# note; una que además se mira cada vez que se toca el diseño, no.

DIR_PLANTILLAS = Path(__file__).resolve().parent.parent / "templates" / "stories"
DIR_PAYLOADS = Path(__file__).resolve().parent / "fixtures" / "stories" / "payloads"

PLANTILLAS = sorted(p.stem for p in DIR_PLANTILLAS.glob("*.html"))


def test_toda_plantilla_tiene_payload_de_prueba():
    faltantes = [n for n in PLANTILLAS if not (DIR_PAYLOADS / f"{n}.json").exists()]
    assert not faltantes, (
        f"Plantillas sin payload en tests/fixtures/stories/payloads/: {faltantes}. "
        "Agrégalo: protege el contrato y alimenta scripts/rendir_todas.py."
    )


@pytest.mark.parametrize("nombre", PLANTILLAS)
def test_plantilla_resuelve_sin_huerfanos(nombre):
    ruta_payload = DIR_PAYLOADS / f"{nombre}.json"
    if not ruta_payload.exists():
        pytest.skip(f"sin payload: lo cubre test_toda_plantilla_tiene_payload_de_prueba")

    payload = json.loads(ruta_payload.read_text(encoding="utf-8"))
    if "recorrido" in payload:
        from story_grafico import enriquecer

        payload = enriquecer(payload)

    html = story_render.build_html(payload, DIR_PLANTILLAS / f"{nombre}.html")

    assert "{{" not in html, f"{nombre}: quedaron tokens sin resolver"
    assert "<!-- FOR:" not in html, f"{nombre}: quedó un bloque FOR sin expandir"
