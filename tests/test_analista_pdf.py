"""El PDF que el bot entrega: sale del HTML del informe, en páginas de celular."""
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


def _medidas(pagina) -> tuple[int, int]:
    return round(float(pagina.mediabox.width)), round(float(pagina.mediabox.height))


def _destinos(pagina) -> list[str]:
    return [str(a.get_object().get("/Dest")) for a in (pagina.get("/Annots") or [])
            if a.get_object().get("/Dest") is not None]


@pytest.mark.skipif(not _chromium_disponible(), reason="Chromium de Playwright no instalado")
def test_el_informe_sale_en_paginas_de_celular_con_la_firma(tmp_path):
    from pypdf import PdfReader

    html = ih.guardar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY, "activo_oro_0939")
    salida = pdf.rendir(html)

    assert salida == tmp_path / "activo_oro_0939.pdf"
    paginas = PdfReader(str(salida)).pages
    # 108 x 192 mm en puntos: la proporción de un teléfono en vertical.
    assert all(_medidas(p) == (306, 544) for p in paginas)
    texto = " ".join(pag.extract_text() for pag in paginas)
    assert fx.AUTOR.nombre.split()[0] in texto


@pytest.mark.skipif(not _chromium_disponible(), reason="Chromium de Playwright no instalado")
@pytest.mark.parametrize("tipo", ["activo", "jornada"])
def test_el_pdf_no_trae_enlaces_internos_ni_hojas_horizontales(tipo, tmp_path):
    from pypdf import PdfReader

    html = ih.guardar(fx.PIEZAS[tipo](tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY, f"{tipo}_0939")
    paginas = PdfReader(str(pdf.rendir(html))).pages

    assert all(_medidas(p) == (306, 544) for p in paginas)
    assert [d for p in paginas for d in _destinos(p)] == []


def test_un_pdf_vacio_no_se_entrega(tmp_path):
    pytest.importorskip("pypdf")  # extra `informe`: el CI corre sin él
    vacio = tmp_path / "x.pdf"
    vacio.write_bytes(b"")
    with pytest.raises(pdf.PdfFallido):
        pdf.verificar(vacio)
