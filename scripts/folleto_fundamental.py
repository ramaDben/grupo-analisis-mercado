"""Genera la guía rápida de análisis fundamental en HTML autónomo y en PDF A4.

Complementa la capacitación de 55 láminas: aquella se estudia, esta se consulta con
el cliente al teléfono. De ahí las dos salidas:

- **HTML autónomo** — las fuentes de marca van incrustadas en base64, así el archivo
  se manda por correo o WhatsApp y funciona solo. Bajo 820 px de ancho las hojas A4
  se rompen en una columna y las tablas anchas se vuelven fichas apiladas, para
  consultarlo en el teléfono sin hacer zoom.
- **PDF A4** — para imprimir y tener a mano en el escritorio.

Las fuentes del repo se pueden usar acá y no en el PPTX: en HTML los `.woff2`
funcionan nativamente, mientras que PowerPoint las necesitaría instaladas en cada
equipo. Se usan DM Sans para todo y Space Grotesk para cifras; Syne queda fuera por
legibilidad (ver el comentario de tipografía en la plantilla).

Uso:
    uv run --frozen --with pillow python scripts/folleto_fundamental.py

Playwright viene del extra `stories` del proyecto; Pillow se inyecta con `--with`
igual que en el generador del PPTX, para no alterar el `.venv`.
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import retrato  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "templates" / "capacitacion" / "folleto.html"
FUENTES = RAIZ / "templates" / "stories" / "fonts"
SALIDA = RAIZ / "docs" / "capacitacion"
FOTO = RAIZ / "docs" / "capacitacion" / "assets" / "autor.png"

AUTOR = {
    "nombre": "Benjamín Ignacio Bravo Soza",
    "titulos": "Ingeniero en Finanzas · Diplomado en Gestión de Riesgos "
               "bajo estándar PMI",
    "cargo": "Operador Acreditado CMV",
    "area": "Área de Estudios y Post-Venta · GI",
}

# (archivo, familia, peso). DM Sans para títulos y cuerpo; Space Grotesk solo para
# cifras y siglas, donde importa el alineado tabular.
CATALOGO = [
    # Syne queda fuera a propósito: en peso 800 sus contraformas se cierran y en un
    # documento de consulta cansa la vista. Embeberla solo sumaría peso al archivo.
    ("dm-sans-400.woff2", "DM Sans", 400),
    ("dm-sans-700.woff2", "DM Sans", 700),
    ("space-grotesk-600.woff2", "Space Grotesk", 600),
]


def _bloque_fuentes() -> str:
    reglas = []
    for archivo, familia, peso in CATALOGO:
        ruta = FUENTES / archivo
        if not ruta.exists():
            print(f"  aviso: falta {archivo}, se usará la tipografía de sistema")
            continue
        datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
        reglas.append(
            f'@font-face{{font-family:"{familia}";font-weight:{peso};'
            f"font-style:normal;font-display:swap;"
            f'src:url(data:font/woff2;base64,{datos}) format("woff2")}}'
        )
    return "\n".join(reglas)


def _retrato_datauri(lado: int = 300) -> str:
    """El retrato ya recortado, como data URI.

    Va incrustado y no enlazado para que el HTML siga funcionando al mandarlo suelto
    por correo o WhatsApp. En WebP y no en PNG: con transparencia el PNG dispara el
    archivo a casi 1 MB, que es justo lo que arruina un adjunto de mensajería. 300 px
    sobran para los 17 mm a los que se imprime.
    """
    origen = retrato.resolver(FOTO)
    if origen is None:
        print("  aviso: sin retrato, la autoría va solo en texto")
        return ""
    circular = retrato.recortar(origen, lado=lado)
    if circular is None:
        return ""

    from io import BytesIO  # noqa: PLC0415

    from PIL import Image  # noqa: PLC0415

    memoria = BytesIO()
    Image.open(circular).save(memoria, "WEBP", quality=88, method=6)
    datos = base64.b64encode(memoria.getvalue()).decode("ascii")
    print(f"  retrato incrustado: {len(memoria.getvalue()) / 1024:.0f} KB en WebP")
    return f"data:image/webp;base64,{datos}"


def _bloques_autor(uri: str) -> tuple[str, str]:
    """Devuelve el bloque de cabecera y el de pie. Si no hay retrato, se omite la
    imagen pero la autoría se mantiene: el crédito no depende de la foto."""
    img_cab = f'<img src="{uri}" alt="Retrato del autor">' if uri else ""
    img_pie = f'<img src="{uri}" alt="Retrato del autor">' if uri else ""
    cabecera = f"""<div class="autor-mini">
      {img_cab}
      <div class="rol">Elaborado por</div>
      <b>{AUTOR["nombre"]}</b>
      <span>{AUTOR["titulos"]}<br>{AUTOR["cargo"]}<br>{AUTOR["area"]}</span>
    </div>"""
    pie = f"""<div class="pie-autor">
    {img_pie}
    <div class="datos">
      <b>{AUTOR["nombre"]}</b>
      <span>{AUTOR["titulos"]}<br>{AUTOR["cargo"]} · {AUTOR["area"]}</span>
    </div>
  </div>"""
    return cabecera, pie


def construir_html() -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    for marcador in ("/*FUENTES*/", "{{AUTOR_CABECERA}}", "{{AUTOR_PIE}}"):
        if marcador not in plantilla:
            raise SystemExit(f"la plantilla no tiene el marcador {marcador}")
    cabecera, pie = _bloques_autor(_retrato_datauri())
    return (plantilla
            .replace("/*FUENTES*/", _bloque_fuentes())
            .replace("{{AUTOR_CABECERA}}", cabecera)
            .replace("{{AUTOR_PIE}}", pie))


def escribir_pdf(html: Path, destino: Path) -> None:
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(html.as_uri())
        pagina.emulate_media(media="print")
        pagina.wait_for_timeout(400)  # que terminen de aplicarse las fuentes
        pagina.pdf(path=str(destino), format="A4", print_background=True,
                   margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        navegador.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-html", action="store_true",
                        help="omite el PDF (no requiere Playwright)")
    args = parser.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_html = SALIDA / "Guia rapida Analisis Fundamental - GI.html"
    ruta_html.write_text(construir_html(), encoding="utf-8")
    print(f"HTML -> {ruta_html.relative_to(RAIZ)}  "
          f"({ruta_html.stat().st_size / 1024:.0f} KB, autónomo)")

    if args.solo_html:
        return
    ruta_pdf = SALIDA / "Guia rapida Analisis Fundamental - GI.pdf"
    escribir_pdf(ruta_html, ruta_pdf)
    print(f"PDF  -> {ruta_pdf.relative_to(RAIZ)}  "
          f"({ruta_pdf.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
