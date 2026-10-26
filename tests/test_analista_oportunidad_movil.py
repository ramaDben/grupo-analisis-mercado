"""Pruebas de experiencia móvil y peso del HTML de /oportunidad."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import oportunidad_html as oh  # noqa: E402
from analista.autor import Autor  # noqa: E402

EJECUTIVO = {"nombre": "Camila Rojas", "cargo": "Ejecutiva comercial", "contacto": "+56 9 1111 2222"}
AUTOR = Autor(
    "Benjamín Bravo Soza",
    "Departamento de Estudios",
    None,
    None,
    {"entidad": "CMV", "categoria": "Operadores", "numero": "A-32915", "vigente_hasta": "2028-03-31"},
)


def _pieza_caterpillar(tmp_path: Path) -> dict:
    fixture_path = RAIZ / "tests" / "fixtures" / "analista" / "oportunidad_cat_2026-10-26.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    data["editorial"]["bajada"] = "La acción se mantiene en rango lateral a la espera de sus resultados corporativos del jueves."
    data["editorial"]["dias_clave"]["#CAT"] = (
        "El martes 27/10 a las 09:30 CLST se conocerán los Pedidos de bienes durables. "
        "El miércoles 28/10 a las 15:00 CLST la Fed. El jueves 29/10 a las 09:30 CLST el PIB."
    )
    for img in data.get("imagenes", {}).values():
        if img:
            fx._imagen(tmp_path, img)
    for img in data.get("ilustraciones", {}).values():
        if img:
            fx._imagen(tmp_path, img)
    data["huella"] = es._huella(data)
    return data


def test_html_caterpillar_peso_bajo_1_5_mb(tmp_path: Path):
    """El HTML generado con la fixture de Caterpillar está bajo 1,5 MB sin URLs públicas."""
    data = _pieza_caterpillar(tmp_path)
    html = oh.armar(data, tmp_path, EJECUTIVO, AUTOR, date(2026, 10, 26))
    peso_bytes = len(html.encode("utf-8"))
    assert peso_bytes < 1.5 * 1024 * 1024, f"HTML demasiado pesado: {peso_bytes / (1024 * 1024):.2f} MB"


def test_experiencia_movil_390px_sin_scroll_y_areas_tactiles(tmp_path: Path):
    """En celular de 390 px: sin scroll horizontal y todos los controles con área táctil >= 40 px."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    data = _pieza_caterpillar(tmp_path)
    html = oh.armar(data, tmp_path, EJECUTIVO, AUTOR, date(2026, 10, 26))
    ruta_html = tmp_path / "oportunidad_movil.html"
    ruta_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(ruta_html.resolve().as_uri())

        # 1. Sin scroll horizontal a 390 px
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        inner_width = page.evaluate("() => window.innerWidth")
        assert scroll_width <= inner_width, f"Hay scroll horizontal: scrollWidth {scroll_width} > innerWidth {inner_width}"

        # 2. Controles táctiles del panel con área >= 40 px
        controles = page.locator(
            "#editor input:visible, #editor button:visible, #editor a:visible, "
            ".panel input:visible, .panel button:visible, .panel a:visible"
        ).all()
        assert len(controles) > 0, "No se encontraron controles visibles en el panel"

        for ctrl in controles:
            tag = ctrl.evaluate("e => e.tagName.toLowerCase()")
            tipo = ctrl.evaluate("e => e.type || ''")
            # En radio y checkbox el área táctil incluye el label contenedor
            if tag == "input" and tipo in ("checkbox", "radio"):
                label = ctrl.locator("xpath=ancestor::label[1]")
                box = label.bounding_box() if label.count() > 0 else ctrl.bounding_box()
            else:
                box = ctrl.bounding_box()

            assert box is not None, f"Control {ctrl} sin bounding box"
            assert box["width"] >= 40, f"Control {ctrl} ({tag} {tipo}) tiene ancho {box['width']} < 40 px"
            assert box["height"] >= 40, f"Control {ctrl} ({tag} {tipo}) tiene alto {box['height']} < 40 px"

        # 3. Enlace "Ir a la vista del correo ↓" debajo de los botones del panel
        enlace_correo = page.locator("#editor a[href='#vista-correo']")
        assert enlace_correo.count() == 1
        assert "Ir a la vista del correo ↓" in enlace_correo.inner_text()
        box_enlace = enlace_correo.bounding_box()
        assert box_enlace is not None
        assert box_enlace["width"] >= 40 and box_enlace["height"] >= 40

        # Al hacer click en el enlace, navega o hace scroll hacia la vista del correo
        enlace_correo.click()
        # Verificar que el ancla apunta a #vista-correo
        assert enlace_correo.get_attribute("href") == "#vista-correo"

        # 4. Tabla de hechos apilada a 390 px (< 480 px)
        th_visibles = page.locator(".tabla-hechos .hechos-th:visible").count()
        assert th_visibles == 0, "Las cabeceras de la tabla deberían estar ocultas en pantalla chica"

        td_display = page.locator(".tabla-hechos td.hechos-td").first.evaluate(
            "e => window.getComputedStyle(e).display"
        )
        assert td_display == "block", f"Las celdas de la tabla deben ser display:block, es {td_display}"

        # 5. Etiquetas del panel en 12-13 px (no 11 px)
        etiquetas = page.locator(".editor .cliente span, .editor .cabecera-campo span, .resultado span").all()
        for et in etiquetas:
            fs = et.evaluate("e => parseFloat(window.getComputedStyle(e).fontSize)")
            assert fs >= 12, f"Etiqueta {et} tiene font-size {fs} < 12px"

        browser.close()
