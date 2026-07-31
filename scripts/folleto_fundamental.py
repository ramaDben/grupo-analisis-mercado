"""Genera la guía rápida de análisis fundamental en HTML autónomo y en PDF A4.

Complementa la capacitación de 55 láminas: aquella se estudia, esta se consulta con
el cliente al teléfono. De ahí las dos salidas:

- **HTML autónomo** — las fuentes de marca van incrustadas en base64, así el archivo
  se manda por correo o WhatsApp y funciona solo. Bajo 820 px de ancho las hojas A4
  se rompen en una columna y las tablas anchas se vuelven fichas apiladas, para
  consultarlo en el teléfono sin hacer zoom.
- **PDF A4 de 3 páginas** — para imprimir y tener a mano en el escritorio.

Aquí sí se usan las fuentes de marca (Syne / DM Sans / Space Grotesk), al contrario
que en el PPTX: en HTML los `.woff2` del repo funcionan nativamente, mientras que
PowerPoint necesitaría tenerlas instaladas en cada equipo.

Uso:
    uv run --extra stories python scripts/folleto_fundamental.py
"""

from __future__ import annotations

import argparse
import base64
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "templates" / "capacitacion" / "folleto.html"
FUENTES = RAIZ / "templates" / "stories" / "fonts"
SALIDA = RAIZ / "docs" / "capacitacion"

# (archivo, familia, peso). Mismo criterio tipográfico que las Stories: Syne para
# títulos, DM Sans para el cuerpo y Space Grotesk para cifras y siglas.
CATALOGO = [
    ("syne-800.woff2", "Syne", 800),
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


def construir_html() -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if "/*FUENTES*/" not in plantilla:
        raise SystemExit("la plantilla no tiene el marcador /*FUENTES*/")
    return plantilla.replace("/*FUENTES*/", _bloque_fuentes())


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
