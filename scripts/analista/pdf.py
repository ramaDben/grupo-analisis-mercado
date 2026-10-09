"""El informe que circula es el PDF; el HTML queda como su fuente.

Google Drive no muestra HTML, y un documento firmado no debería circular en un
formato que se edita con el Bloc de notas sin tocar la firma (decisión del
director, 2026-10-09). El HTML ya trae sus fuentes e imágenes en base64 y sus
reglas de impresión (hoja de celular, cortes de página), así que el PDF sale de imprimirlo
tal cual con Chromium.
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


def rendir(html: Path) -> Path:
    """Imprime el informe a un PDF de celular junto al HTML y devuelve su ruta."""
    from playwright.sync_api import sync_playwright

    destino = html.with_suffix(".pdf")
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            try:
                pagina = navegador.new_page()
                pagina.set_content(html.read_text(encoding="utf-8"), wait_until="load")
                # Sin esperar las fuentes, el texto sale en la de respaldo.
                pagina.evaluate("document.fonts.ready.then(() => true)")
                pagina.emulate_media(media="print")
                pagina.pdf(path=str(destino), print_background=True,
                           prefer_css_page_size=True)
            finally:
                navegador.close()
    except Exception as exc:
        raise PdfFallido(f"Chromium no generó el PDF: {exc.__class__.__name__}") from exc
    return verificar(destino)
