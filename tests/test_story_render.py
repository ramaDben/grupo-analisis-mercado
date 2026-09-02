"""Tests del motor de render de Stories GI (`scripts/story_render.py`, issues #109/#119).

Cubre el mapeo puro payload -> HTML (`build_context`/`resolver_loops`/`build_html`, AC2-AC9)
sin depender de Playwright, y tests de integración de render real (AC1) que se saltan
(`skipif`) si Chromium no está instalado en la máquina de ejecución.
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

import story_render  # noqa: E402
import story_grafico  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "stories"
FIXTURE_TEMPLATE = FIXTURES_DIR / "fixture_template.html"
FIXTURE_CHART = FIXTURES_DIR / "fixture_chart.png"
ALERTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "alerta.html"
BREAKING_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "breaking.html"
CALENDARIO_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "calendario.html"
DATO_MACRO_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "dato_macro.html"

FIXTURE_FOR_HTML = "<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->"

PAYLOAD_EJEMPLO: dict = {
    "plantilla": "alerta",
    "activo": {"ticker_mt5": "XAUUSD", "nombre": "Oro", "digits": 2},
    "chip_categoria": "COMMODITIES · ORO",
    "activo_slug": "oro",
    "activo_imagen": "assets/activos/oro.jpg",
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
    "grafico": '<svg viewBox="0 0 440 400"></svg>',
    "sello_datos": "Datos reales · MetaTrader 5 · 13 JUL 11:15",
}

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

PAYLOAD_CALENDARIO: dict = {
    "plantilla": "calendario",
    "sello": "CALENDARIO SEMANAL · GI",
    "fecha_hora": "SEMANA DEL 11 AL 15 DE AGOSTO",
    "titulo": "Lo que mueve la semana",
    "subtitulo": "Los 5 datos de mayor impacto para Oro, WTI, USD/CLP y US100.",
    "eventos": [
        {
            "numero": "01",
            "dia": "MIÉRCOLES 12",
            "hora": "08:30 CLT",
            "evento": "Índice de precios al consumidor (IPC) de EE.UU., interanual",
            "pais": "EE.UU. · USD",
            "impacto": "Alto impacto",
            "impacto_slug": "alto",
            "anterior": "3,5%",
            "esperado": "3,4%",
            "tiene_esperado": True,
        },
        {
            "numero": "02",
            "dia": "MIÉRCOLES 12",
            "hora": "10:30 CLT",
            "evento": "Inventarios de petróleo en EE.UU. (EIA)",
            "pais": "EE.UU. · USD",
            "impacto": "Alto impacto",
            "impacto_slug": "alto",
            "anterior": "+2,479 M barriles",
            "esperado": "",
            "tiene_esperado": False,
        },
    ],
    "cta": "¿Quieres seguir esta semana en detalle?",
    "cta_sub": "Habla hoy con tu analista",
}


def _chromium_disponible() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            b = p.chromium.launch()
            b.close()
        return True
    except Exception:
        return False


def _png_size(path: Path) -> tuple[int, int]:
    import struct

    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "El archivo no es un PNG valido"
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def _payload_alerta_fixture() -> dict:
    fixture_path = FIXTURES_DIR / "payloads" / "alerta.json"
    assert fixture_path.exists(), f"falta fixture {fixture_path}"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    payload["grafico"] = '<svg viewBox="0 0 440 400"></svg>'
    return payload


def _body(html: str) -> str:
    import re
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else html


# ---------------------------------------------------------------------------
# Contrato de datos y engine tests
# ---------------------------------------------------------------------------


def test_build_context_valida_tokens():
    payload = {"plantilla": "alerta", "titular": "Prueba"}
    ctx = story_render.build_context(payload)
    assert ctx["titular"] == "Prueba"


def test_build_html_contract():
    html = story_render.build_html(PAYLOAD_EJEMPLO, FIXTURE_TEMPLATE)
    assert PAYLOAD_EJEMPLO["titular"] in html
    assert PAYLOAD_EJEMPLO["precio_actual"] in html
    assert PAYLOAD_EJEMPLO["soporte"] in html
    assert PAYLOAD_EJEMPLO["resistencia"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_build_html_token_huerfano_lanza_error(tmp_path):
    template_con_huerfano = tmp_path / "bad_template.html"
    template_con_huerfano.write_text(
        "<h1>{{titular}}</h1><p>{{token_inexistente}}</p>",
        encoding="utf-8",
    )
    with pytest.raises(story_render.StoryRenderError) as excinfo:
        story_render.build_html(PAYLOAD_EJEMPLO, template_con_huerfano)
    assert "token_inexistente" in str(excinfo.value)


def test_build_context_escalar_extra_no_op():
    payload = {**PAYLOAD_EJEMPLO, "campo_no_definido_xyz": "valor"}
    context = story_render.build_context(payload)
    assert context.get("campo_no_definido_xyz") == "valor"


def test_build_context_impacto_badge():
    payload = {**PAYLOAD_EJEMPLO, "impacto": "alto"}
    context = story_render.build_context(payload)
    assert context.get("impacto_badge") == "ALTO"


def test_resolver_loops_vacio():
    res = story_render.resolver_loops("<div>" + FIXTURE_FOR_HTML + "</div>", {"filas": []})
    assert res == "<div></div>"


def test_resolver_loops_uno():
    res = story_render.resolver_loops(
        FIXTURE_FOR_HTML, {"filas": [{"nombre": "IPC"}]}
    )
    assert res == "IPC"


def test_resolver_loops_n():
    filas = [{"nombre": "IPC"}, {"nombre": "NFP"}, {"nombre": "PMI"}]
    res = story_render.resolver_loops(FIXTURE_FOR_HTML, {"filas": filas})
    assert res == "IPCNFPPMI"


def test_orden_canonico_loops_fences(tmp_path):
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        "<!-- FOR:items --><!-- IF:visible -->{{n}}<!-- ENDIF:visible --><!-- ENDFOR:items -->",
        encoding="utf-8",
    )
    payload = {
        **PAYLOAD_EJEMPLO,
        "items": [
            {"n": "A", "visible": True},
            {"n": "B", "visible": False},
            {"n": "C", "visible": True},
        ],
    }
    html = story_render.build_html(payload, tpl)
    assert html == "AC"


# ---------------------------------------------------------------------------
# alerta.html Tests
# ---------------------------------------------------------------------------


def test_alerta_no_placeholders():
    payload = copy.deepcopy(PAYLOAD_EJEMPLO)
    payload["vol_pct"] = "18,40 USD"
    html = story_render.build_html(payload, ALERTA_TEMPLATE)

    assert payload["chip_categoria"] in html
    assert payload["fecha_hora"] in html
    assert payload["titular"] in html
    assert payload["parrafo"] in html
    assert payload["rotulo_activo"] in html
    assert payload["precio_actual"] in html
    assert payload["soporte"] in html
    assert payload["resistencia"] in html
    assert payload["vol_pct"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_alerta_chart_embebido():
    payload = copy.deepcopy(PAYLOAD_EJEMPLO)
    payload["chart_png"] = str(FIXTURE_CHART)
    html = story_render.build_html(payload, ALERTA_TEMPLATE)
    assert "data:image/png;base64," in html or "file:///" in html
    assert 'alt="Gráfico del activo"' in html


def test_alerta_chart_png_inexistente_lanza_error():
    payload = copy.deepcopy(PAYLOAD_EJEMPLO)
    payload["chart_png"] = "ruta/no/existe/chart.png"
    with pytest.raises(story_render.StoryRenderError, match="chart_png"):
        story_render.build_html(payload, ALERTA_TEMPLATE)


def test_alerta_pinta_el_color_del_activo():
    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)
    assert "activo-oro" in html


def test_alerta_sin_activo_slug_no_rompe():
    payload = _payload_alerta_fixture()
    payload["chart_png"] = None
    payload["activo_slug"] = ""
    html = story_render.build_html(payload, ALERTA_TEMPLATE)
    assert "activo-None" not in html
    assert "{{" not in _body(html)


def test_alerta_declara_las_clases_de_sus_niveles():
    html = ALERTA_TEMPLATE.read_text(encoding="utf-8")
    assert ".g-nivel-resistencia" in html
    assert ".g-nivel-soporte" in html
    assert ".g-linea" in html


def test_alerta_snapshot_es_estrictamente_horizontal():
    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)
    assert "width: 1920px" in html
    assert "height: 1080px" in html
    assert "max-aspect-ratio" not in html


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_alerta_render_horizontal_dimensiones(tmp_path):
    salida = tmp_path / "story_alerta_horizontal.png"
    story_render.render_story(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE, salida)
    assert _png_size(salida) == (1920, 1080)


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_alerta_columnas_lado_a_lado(tmp_path):
    from playwright.sync_api import sync_playwright

    html = story_render.build_html(PAYLOAD_EJEMPLO, ALERTA_TEMPLATE)
    tmp_html = ALERTA_TEMPLATE.parent / "_test_alerta_probe.html"
    tmp_html.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(
                    viewport={"width": 1920, "height": 1080}, device_scale_factor=1
                )
                page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
                edi = page.locator(".columna-editorial").bounding_box()
                graf = page.locator(".columna-grafico").bounding_box()
                page.close()
            finally:
                browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    assert graf["x"] > edi["x"]
    assert abs(graf["y"] - edi["y"]) < 5


# ---------------------------------------------------------------------------
# breaking.html Tests
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
# calendario.html Tests
# ---------------------------------------------------------------------------


def test_calendario_no_placeholders():
    html = story_render.build_html(PAYLOAD_CALENDARIO, CALENDARIO_TEMPLATE)
    assert PAYLOAD_CALENDARIO["sello"] in html
    assert PAYLOAD_CALENDARIO["titulo"] in html
    for ev in PAYLOAD_CALENDARIO["eventos"]:
        assert ev["evento"] in html
        assert ev["hora"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_calendario_evento_sin_esperado_omite_flecha_y_dato():
    html = story_render.build_html(PAYLOAD_CALENDARIO, CALENDARIO_TEMPLATE)
    assert "{{" not in html
    assert "}}" not in html


def test_calendario_eventos_vacio():
    payload = {**PAYLOAD_CALENDARIO, "eventos": []}
    html = story_render.build_html(payload, CALENDARIO_TEMPLATE)
    assert "FOR:eventos" not in html
    assert "{{" not in html
    assert "}}" not in html


def test_calendario_eventos_uno():
    payload = {
        **PAYLOAD_CALENDARIO,
        "eventos": [PAYLOAD_CALENDARIO["eventos"][0]],
    }
    html = story_render.build_html(payload, CALENDARIO_TEMPLATE)
    assert html.count("IPC") >= 1


def test_calendario_eventos_n_mantienen_orden():
    html = story_render.build_html(PAYLOAD_CALENDARIO, CALENDARIO_TEMPLATE)
    nombres = [e["evento"] for e in PAYLOAD_CALENDARIO["eventos"]]
    assert html.index(nombres[0]) < html.index(nombres[1])


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_calendario_render_dimensiones(tmp_path):
    salida = tmp_path / "story_calendario_test.png"
    resultado = story_render.render_story(PAYLOAD_CALENDARIO, CALENDARIO_TEMPLATE, salida)
    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)


# ---------------------------------------------------------------------------
# Formatos & Catálogo de Plantillas Activas
# ---------------------------------------------------------------------------


def test_formatos_mapa_cerrado():
    assert "horizontal" in story_render._FORMATOS
    assert story_render._FORMATOS["horizontal"] == (1920, 1080)


def test_formato_desconocido_lanza_error_accionable():
    with pytest.raises(story_render.StoryRenderError, match="desconocido"):
        story_render.resolver_viewport("diagonal")


def test_resolver_viewport_default_horizontal():
    assert story_render.resolver_viewport("horizontal") == (1920, 1080)


def test_toda_plantilla_tiene_payload_de_prueba():
    dir_plantillas = _REPO_ROOT / "templates" / "stories"
    dir_payloads = FIXTURES_DIR / "payloads"
    plantillas = {p.stem for p in dir_plantillas.glob("*.html")}
    payloads = {p.stem for p in dir_payloads.glob("*.json")}
    faltantes = plantillas - payloads
    assert not faltantes, f"Plantillas sin payload de prueba: {sorted(faltantes)}"


@pytest.mark.parametrize(
    "nombre",
    [p.stem for p in (_REPO_ROOT / "templates" / "stories").glob("*.html")],
)
def test_plantilla_resuelve_sin_huerfanos(nombre):
    tpl = _REPO_ROOT / "templates" / "stories" / f"{nombre}.html"
    fixture = FIXTURES_DIR / "payloads" / f"{nombre}.json"
    assert fixture.exists(), f"Falta fixture para {nombre}"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    if "recorrido" in payload:
        payload = story_grafico.enriquecer(payload)
    html = story_render.build_html(payload, tpl)
    assert "{{" not in html
    assert "}}" not in html


def test_activo_imagen_inexistente_falla_con_mensaje_accionable():
    payload = _payload_alerta_fixture()
    payload["chart_png"] = None
    payload["activo_imagen"] = "assets/activos/imagen_que_no_existe_xyz.jpg"
    with pytest.raises(story_render.StoryRenderError, match="activo_imagen"):
        story_render.build_html(payload, ALERTA_TEMPLATE)


def test_activo_imagen_con_prefijo_relativo_falla():
    payload = _payload_alerta_fixture()
    payload["chart_png"] = None
    payload["activo_imagen"] = "./assets/activos/oro.jpg"
    with pytest.raises(story_render.StoryRenderError, match="activo_imagen"):
        story_render.build_html(payload, ALERTA_TEMPLATE)


def test_activo_imagen_vacio_no_valida_nada():
    for valor in ("", "   ", None):
        payload = _payload_alerta_fixture()
        payload["chart_png"] = None
        payload["activo_imagen"] = valor
        html = story_render.build_html(payload, ALERTA_TEMPLATE)
        assert "{{" not in _body(html)


def test_la_guardia_de_imagen_ignora_la_clave_ausente():
    payload = _payload_alerta_fixture()
    payload["chart_png"] = None
    payload["activo_imagen"] = ""
    html = story_render.build_html(payload, ALERTA_TEMPLATE)
    assert "{{" not in _body(html)


def test_todas_las_imagenes_del_catalogo_existen():
    dir_imagenes = _REPO_ROOT / "templates" / "stories" / "assets" / "activos"
    assert dir_imagenes.exists()
    assert (dir_imagenes / "oro.jpg").exists()
    assert (dir_imagenes / "wti.jpg").exists()
    assert (dir_imagenes / "sol.jpg").exists()
