"""El nombre que lee el cliente: «línea de control», no «línea de seguridad» (director, 2026-10-21).

«Seguridad» suena a garantía. Los identificadores internos (`rol="seguridad"`, el slug del concepto,
`dist_seguridad_atr_d1`) conservan su nombre: son contratos entre módulos, no texto de cliente.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CORTE = re.compile(r'''["']\s*
\s*f?["']''')
VIEJO = re.compile(r"[Ll]íneas?( \w+)? de seguridad|protege tu operación")


def test_el_texto_que_lee_el_cliente_no_dice_linea_de_seguridad():
    restos = []
    for carpeta in ("scripts", "src", "templates", "config"):
        for ruta in (RAIZ / carpeta).rglob("*"):
            if ruta.suffix not in {".py", ".html", ".json", ".css", ".md"} or not ruta.is_file():
                continue
            # Una cadena partida en dos líneas («la línea de "` + `f"seguridad…») también cuenta: se une antes de buscar.
            texto = CORTE.sub("", ruta.read_text(encoding="utf-8", errors="ignore"))
            if VIEJO.search(texto):
                restos.append(str(ruta.relative_to(RAIZ)))
    assert not restos, "dice «línea de seguridad»: " + ", ".join(restos)
