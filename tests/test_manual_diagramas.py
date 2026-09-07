"""Guardia de los diagramas del manual: que ningún rótulo se escape de su SVG.

**El defecto que este test impide.** En CommonMark una línea en blanco cierra el
bloque de HTML crudo. Los 8 diagramas del manual traían renglones vacíos entre
sus grupos de figuras para poder leerlos, así que lo que venía después del primer
vacío dejaba de pertenecer al bloque del `<svg>`.

Lo que decide si el diagrama sobrevive es **qué hay en la línea siguiente**, y
ahí está la parte que engaña:

- Si es una etiqueta que se cierra sola y ocupa el renglón entero (`<line/>`,
  `<rect/>`), markdown-it abre **otro** bloque de HTML y lo emite tal cual. El
  navegador ve marcado contiguo y arma el SVG igual: el diagrama se salva de pura
  suerte. Le pasó a 6 de los 8.
- Si es cualquier otra cosa, la línea cae en un párrafo. Ese `<p>` **cierra el
  `<svg>`** en el parseo del navegador, y los `<text>` que siguen se dibujan como
  texto corriente al costado de la tarjeta.

Medido el 2026-09-07 sobre el manual: **2 diagramas roto**, el de la vela H1 del
módulo 1 y el del setup 5.1, con **18 de los 87 rótulos** derramados fuera del
dibujo. Se descubrió mirando el PDF, no compilándolo: el compilador terminaba en
código 0 y contaba bien sus páginas. Es el mismo modo de falla del
`overflow: hidden` de la maqueta vieja y del mensaje de WhatsApp al que le
faltaban renglones: se lee como completo y nadie lo nota desde afuera.

**Ojo con cómo se mide.** Buscar `"<p"` dentro del bloque da un falso positivo en
cada `<polygon>` y cada `<path>`, que es el error que se cometió al diagnosticar
esto. La condición se prueba con la etiqueta cerrada (`</?p>`).

El test compara el conteo del markdown contra el del HTML rendido, no que el
sanitizador exista: lo que importa es que el rótulo llegue al dibujo, no por qué
camino.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

pytest.importorskip("markdown_it", reason="markdown-it-py es opcional (extra del manual)")

from compilar_manual_pdf import ORIGEN_MD, compactar_svg, renderizar_markdown  # noqa: E402

SVG = re.compile(r"<svg\b.*?</svg>", re.DOTALL)
PARRAFO = re.compile(r"</?p\s*>")


@pytest.fixture(scope="module")
def markdown() -> str:
    return ORIGEN_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def html(markdown: str) -> str:
    return renderizar_markdown(markdown)


def test_ningun_svg_queda_partido_por_un_parrafo(html: str) -> None:
    bloques = SVG.findall(html)
    assert bloques, "el manual perdió sus diagramas"

    partidos = [b for b in bloques if PARRAFO.search(b)]

    assert not partidos, (
        f"{len(partidos)} de {len(bloques)} diagramas quedaron partidos por una "
        "etiqueta <p>: eso cierra el <svg> en el navegador y su leyenda se dibuja "
        "como texto al costado. Revisá que compactar_svg siga quitando las líneas "
        "en blanco de adentro de cada bloque <svg>."
    )


def test_todo_rotulo_del_markdown_llega_dentro_de_un_svg_sano(markdown: str, html: str) -> None:
    esperados = markdown.count("<text")
    assert esperados > 0, "el manual perdió sus rótulos"

    obtenidos = sum(b.count("<text") for b in SVG.findall(html) if not PARRAFO.search(b))

    assert obtenidos == esperados, (
        f"{esperados - obtenidos} de {esperados} rótulos no llegaron a un <svg> sano: "
        "el diagrama sale mudo y el cliente lee una leyenda suelta."
    )


def test_ningun_svg_del_markdown_queda_con_lineas_en_blanco_adentro(markdown: str) -> None:
    """La condición concreta que cierra el bloque de HTML crudo."""
    for bloque in SVG.findall(compactar_svg(markdown)):
        assert "\n\n" not in bloque, (
            "un <svg> conserva una línea en blanco: CommonMark cierra ahí el bloque "
            "de HTML y el resto del diagrama queda a merced de lo que siga"
        )


def test_compactar_svg_no_toca_el_texto_de_afuera() -> None:
    """El sanitizador es quirúrgico: la prosa del manual necesita sus renglones.

    Quitar las líneas en blanco del documento entero pegaría cada párrafo con el
    siguiente y convertiría las listas en un bloque corrido.
    """
    fuente = "Un párrafo.\n\nOtro párrafo.\n\n<svg>\n<text>A</text>\n\n<text>B</text>\n</svg>\n\nCierre.\n"

    salida = compactar_svg(fuente)

    assert "Un párrafo.\n\nOtro párrafo." in salida
    assert salida.endswith("\n\nCierre.\n")
    assert "<text>A</text>\n<text>B</text>" in salida
