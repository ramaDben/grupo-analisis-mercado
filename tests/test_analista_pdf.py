"""El PDF del correo: sale del HTML con el correo armado por JavaScript, sin editor ni botones."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import oportunidad_html as oh  # noqa: E402
from analista import pdf  # noqa: E402

HOY = date(2026, 10, 12)
EJECUTIVO = {"nombre": "Camila Rojas", "cargo": "Ejecutiva comercial", "contacto": "+56 9 1111 2222"}


def test_pdf_vacio_no_se_entrega(tmp_path):
    pytest.importorskip("pypdf")
    vacio = tmp_path / "x.pdf"
    vacio.write_bytes(b"")
    with pytest.raises(pdf.PdfFallido):
        pdf.verificar(vacio)


def test_el_pdf_muestra_el_correo_y_no_el_editor(tmp_path):
    pytest.importorskip("playwright")
    PdfReader = pytest.importorskip("pypdf").PdfReader
    pieza = fx.pieza_oportunidad(tmp_path, laminas=True)
    html = oh.guardar(pieza, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    ruta = pdf.rendir(html)
    assert ruta == html.with_suffix(".pdf")
    lector = PdfReader(str(ruta))
    texto = "".join(p.extract_text() for p in lector.pages)
    assert "ASUNTO SUGERIDO" in texto and "nivel clave" in texto  # el correo se armó con JS antes de imprimir
    assert "Preparar correo para tu cliente" not in texto
    assert "Copiar texto de WhatsApp" not in texto
    assert len(lector.pages) >= 1
    assert sum(len(p.images) for p in lector.pages) >= 1  # el gráfico del correo


def test_una_imagen_rota_del_correo_no_entrega_pdf(tmp_path):
    import re

    pytest.importorskip("playwright")
    pytest.importorskip("pypdf")
    html = oh.guardar(fx.pieza_oportunidad(tmp_path, laminas=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    texto = html.read_text(encoding="utf-8")
    ultima = list(re.finditer(r'src="data:image/png;base64,[^"]*"', texto))[-1]  # una imagen del correo
    roto = texto[:ultima.start()] + 'src="file:///no-existe.png"' + texto[ultima.end():]
    html.write_text(roto, encoding="utf-8")
    with pytest.raises(pdf.PdfFallido, match="imagen"):
        pdf.rendir(html, espera_ms=1500)
    assert not html.with_suffix(".pdf").exists()
