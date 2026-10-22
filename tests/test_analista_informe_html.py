"""Piezas compartidas de la maqueta HTML: firma del director y escape. La pieza semanal
completa se prueba en test_analista_oportunidad_html.py."""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import informe_html as ih  # noqa: E402

HOY = date(2026, 10, 12)


def test_firma_con_acreditacion_vigente():
    html = ih.bloque_firma(fx.AUTOR, HOY)
    assert "Benjamín Ignacio Bravo Soza" in html and "Departamento de Análisis Técnico" in html
    assert "Acreditación CMV" in html and "A-32915" in html and "31-03-2028" in html
    # El enlace de la CMV no reconoce el certificado (2026-10-08): no se imprime
    # aunque el config lo traiga, porque un enlace que no verifica desacredita.
    assert "cmvsystem" not in html and "Verificable" not in html
    assert ih.FRASE_GENERAL in html and "CMF" not in html


def test_acreditacion_vencida_no_se_imprime():
    html = ih.bloque_firma(fx.AUTOR, date(2028, 4, 1))
    assert "A-32915" not in html and ih.FRASE_GENERAL in html


def test_sin_foto_ni_firma_no_deja_hueco():
    html = ih.bloque_firma(fx.AUTOR, HOY)
    assert 'class="firma-foto"' not in html and 'class="firma-trazo"' not in html


def test_con_foto_va_incrustada(tmp_path):
    foto = tmp_path / "foto.png"
    foto.write_bytes(fx.PNG)
    html = ih.bloque_firma(replace(fx.AUTOR, foto=foto), HOY)
    assert '<img class="firma-foto" src="data:image/png;base64,' in html


def test_el_nombre_sale_escapado():
    html = ih.bloque_firma(replace(fx.AUTOR, nombre="O'Higgins"), HOY)
    assert "O&#x27;Higgins" in html


def test_slug_y_pildora():
    assert ih.slug("Dólar / Peso") == "dolar_peso"
    assert ih.pildora("Alcista") == '<span class="direccion alcista">ALCISTA</span>'
