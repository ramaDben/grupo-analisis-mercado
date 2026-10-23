"""El correo en PDF, para verlo en el celular.

El HTML arma el correo con JavaScript y trae las imágenes publicadas por URL,
así que se abre desde disco (no con `set_content`) y se espera a que el correo
exista y sus imágenes hayan cargado. El PDF muestra solo el correo: el editor,
las simulaciones y los botones se ocultan en `@media print`.
"""
from __future__ import annotations

from pathlib import Path


class PdfFallido(RuntimeError):
    """Chromium no produjo un PDF legible."""


def verificar(ruta: Path) -> Path:
    """Un PDF sin páginas no se entrega: llegaría como archivo roto."""
    from pypdf import PdfReader

    try:
        paginas = len(PdfReader(str(ruta)).pages)
    except Exception as exc:  # pypdf lanza tipos distintos según el daño
        raise PdfFallido(f"{ruta.name} no se puede leer: {exc.__class__.__name__}") from exc
    if paginas < 1:
        raise PdfFallido(f"{ruta.name} salió sin páginas")
    return ruta


_CORREO_ARMADO = "(document.getElementById('vista-correo')||{}).innerHTML?.length > 200"
_IMAGENES_CARGADAS = ("Array.from(document.querySelectorAll('#vista-correo img'))"
                      ".every(i => i.complete && i.naturalWidth > 0)")


def rendir(html: Path) -> Path:
    """Imprime el correo a un PDF junto al HTML y devuelve su ruta."""
    from playwright.sync_api import sync_playwright

    destino = html.with_suffix(".pdf")
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            try:
                pagina = navegador.new_page()
                pagina.goto(html.as_uri(), wait_until="networkidle")
                pagina.wait_for_function(_CORREO_ARMADO, timeout=20_000)
                pagina.evaluate("document.fonts.ready.then(() => true)")
                try:
                    pagina.wait_for_function(_IMAGENES_CARGADAS, timeout=20_000)
                except Exception as exc:
                    raise PdfFallido("una imagen del correo no cargó") from exc
                pagina.emulate_media(media="print")
                pagina.pdf(path=str(destino), print_background=True,
                           prefer_css_page_size=True)
            finally:
                navegador.close()
    except PdfFallido:
        raise
    except Exception as exc:
        raise PdfFallido(f"Chromium no generó el PDF: {exc.__class__.__name__}") from exc
    return verificar(destino)
