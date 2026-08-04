"""Verifica el layout de un PPTX generado: nada debe invadir la banda del pie.

Existe porque la maqueta se calcula con alturas estimadas (PowerPoint no expone
métricas de fuente) y con decenas de slides la inspección visual no alcanza. Detecta
los dos fallos que ya se produjeron: una tabla que se extiende bajo el pie —PowerPoint
ignora `row.height` cuando el texto no cabe— y bloques de texto que se solapan.

Se excluyen dos elementos que ocupan la zona baja por diseño: los textos del pie mismo
y la barra vertical de acento de las slides de portada y sección.

Uso:
    uv run --with python-pptx python scripts/verificar_capacitacion.py [ruta.pptx]
"""

from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

POR_DEFECTO = "docs/capacitacion/Analisis Fundamental - Capacitacion GI.pptx"
MARGEN_PIE = Inches(0.56)
TOLERANCIA = Inches(0.05)
SOLAPE_MINIMO = Inches(0.05)


def _pulg(emu) -> float:
    return float(emu) / 914400.0


def revisar(ruta: Path) -> list[str]:
    prs = Presentation(str(ruta))
    alto_slide, ancho_slide = prs.slide_height, prs.slide_width
    limite = alto_slide - MARGEN_PIE
    fallas: list[str] = []

    for numero, slide in enumerate(prs.slides, start=1):
        textos = []
        for forma in slide.shapes:
            alto = forma.height
            if forma.has_table:
                # el alto real de una tabla es la suma de sus filas
                alto = sum(fila.height for fila in forma.table.rows)
            if forma.top >= alto_slide - Inches(0.62):
                continue  # el pie
            if alto >= alto_slide - Inches(0.1) and forma.width <= Inches(0.2):
                continue  # la barra decorativa
            if forma.top + alto > limite + TOLERANCIA:
                fallas.append(
                    f"slide {numero}: forma en y={_pulg(forma.top):.2f}\" termina en "
                    f"{_pulg(forma.top + alto):.2f}\" (límite {_pulg(limite):.2f}\")")
            if forma.left + forma.width > ancho_slide + TOLERANCIA:
                fallas.append(f"slide {numero}: forma sale por la derecha")
            if forma.has_text_frame and forma.text_frame.text.strip():
                textos.append((forma, forma.text_frame.text.strip()[:34]))

        for indice, (una, rotulo_a) in enumerate(textos):
            for otra, rotulo_b in textos[indice + 1:]:
                cruza_x = (una.left < otra.left + otra.width - SOLAPE_MINIMO
                           and otra.left < una.left + una.width - SOLAPE_MINIMO)
                cruza_y = (una.top < otra.top + otra.height - SOLAPE_MINIMO
                           and otra.top < una.top + una.height - SOLAPE_MINIMO)
                if cruza_x and cruza_y:
                    fallas.append(
                        f"slide {numero}: se solapan «{rotulo_a}» y «{rotulo_b}»")
    return fallas


def main() -> None:
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else POR_DEFECTO)
    if not ruta.exists():
        print(f"no existe: {ruta}")
        sys.exit(2)
    fallas = revisar(ruta)
    if fallas:
        print(f"{len(fallas)} problemas de layout:")
        for falla in fallas:
            print("  " + falla)
        sys.exit(1)
    print(f"OK: {ruta.name} sin desbordes ni solapamientos")


if __name__ == "__main__":
    main()
