"""El PDF que el bot entrega: sale del HTML del informe, en A4 y sin la interfaz de pantalla."""
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
from analista import informe_html as ih  # noqa: E402
from analista import pdf  # noqa: E402

HOY = date(2026, 10, 8)


def _chromium_disponible() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chromium_disponible(), reason="Chromium de Playwright no instalado")
def test_el_informe_sale_en_pdf_a4_con_la_firma(tmp_path):
    from pypdf import PdfReader

    html = ih.guardar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY, "activo_oro_0939")
    salida = pdf.rendir(html)

    assert salida == tmp_path / "activo_oro_0939.pdf"
    lector = PdfReader(str(salida))
    assert len(lector.pages) >= 1
    ancho, alto = float(lector.pages[0].mediabox.width), float(lector.pages[0].mediabox.height)
    assert (round(ancho), round(alto)) == (595, 842)  # A4 en puntos
    texto = " ".join(pag.extract_text() for pag in lector.pages)
    assert fx.AUTOR.nombre.split()[0] in texto


def test_un_pdf_vacio_no_se_entrega(tmp_path):
    pytest.importorskip("pypdf")  # extra `informe`: el CI corre sin él
    vacio = tmp_path / "x.pdf"
    vacio.write_bytes(b"")
    with pytest.raises(pdf.PdfFallido):
        pdf.verificar(vacio)
