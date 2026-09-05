#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compila `docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md` a PDF A4.

**El markdown es la fuente única.** Hasta el 2026-09-04 este script tenía el
documento escrito adentro, en una constante `HTML_PAGES`, mientras el markdown
de `docs/` vivía aparte: eran dos documentos distintos con secciones distintas,
y corregir uno no tocaba al otro. El PDF en disco venía además de un tercer
método y estaba **truncado a mitad de la sección 6**, sin la parte operativa
(riesgo, lotaje, filtros, checklist y glosario), con su pie numerado sobre 11
páginas y solo 6 renderizadas.

Dos decisiones que salen de eso y conviene no revertir:

1. **La paginación es por flujo, no por páginas fijas.** El diseño anterior
   maquetaba `div.a4-page` de 794x1123 con `overflow: hidden`, así que el
   contenido que no cabía **desaparecía sin aviso**: es exactamente el modo de
   falla que dejó el manual sin su mitad operativa. Acá Chromium pagina, cada
   módulo abre página con `break-before`, y nada se recorta.
2. **Se mide el resultado.** `compilar_pdf` informa las páginas y falla si el
   PDF sale con menos de las esperadas, porque un documento de cliente que
   pierde secciones se lee como completo y nadie lo nota desde afuera.

Uso:
    uv run --extra stories --with markdown-it-py python scripts/compilar_manual_pdf.py
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "templates" / "stories" / "fonts"
ORIGEN_MD = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
SALIDA_DOCS = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"
SALIDA_CENTRAL = (
    RAIZ / "data central" / "DATA MOTOR GI" / "reportes_generados"
    / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"
)

# El manual tiene 12 módulos y 3 anexos, y cada uno abre página. Si el PDF sale
# con menos que esto, algo se recortó.
PAGINAS_MINIMAS = 16

ACENTO = "#50C0A8"

CATALOGO_FUENTES = [
    ("plus-jakarta-sans-400.woff2", "Plus Jakarta Sans", 400),
    ("plus-jakarta-sans-600.woff2", "Plus Jakarta Sans", 600),
    ("plus-jakarta-sans-700.woff2", "Plus Jakarta Sans", 700),
    ("plus-jakarta-sans-800.woff2", "Plus Jakarta Sans", 800),
    ("goldman-400.woff2", "Goldman", 400),
    ("goldman-700.woff2", "Goldman", 700),
    ("space-grotesk-600.woff2", "Space Grotesk", 600),
    ("space-grotesk-700.woff2", "Space Grotesk", 700),
]

TITULOS_CALLOUT = {
    "note": ("Nota", "#1E40AF", "#EFF6FF", "#BFDBFE"),
    "important": ("Importante", "#065F46", "#F0FDF4", "#A7F3D0"),
    "caution": ("Atención", "#991B1B", "#FEF2F2", "#FECACA"),
    "warning": ("Advertencia", "#92400E", "#FFFBEB", "#FDE68A"),
    "tip": ("Consejo", "#0C4A6E", "#F0F9FF", "#BAE6FD"),
}


def caras_de_fuente() -> str:
    reglas = []
    for archivo, familia, peso in CATALOGO_FUENTES:
        ruta = FUENTES / archivo
        if not ruta.exists():
            continue
        datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
        reglas.append(
            f"@font-face {{ font-family: '{familia}'; font-weight: {peso}; "
            f"font-style: normal; font-display: block; "
            f'src: url(data:font/woff2;base64,{datos}) format("woff2"); }}'
        )
    return "\n".join(reglas)


def procesar_callouts(html: str) -> str:
    """Convierte los avisos de GitHub (`> [!NOTE]`) en cajas con título.

    Se hace sobre el HTML ya renderizado y no sobre el markdown: envolver el
    bloque en HTML crudo antes de renderizar dejaría su contenido sin procesar,
    y estos avisos llevan negritas, listas y tablas adentro.
    """
    patron = re.compile(r"<blockquote>\s*(.*?)\s*</blockquote>", re.S)

    def reemplazo(m: re.Match[str]) -> str:
        interior = m.group(1)
        marca = re.match(r"<p>\[!(\w+)\]\s*", interior)
        if not marca:
            return m.group(0)          # cita normal, no es un aviso
        tipo = marca.group(1).lower()
        if tipo not in TITULOS_CALLOUT:
            return m.group(0)
        rotulo, _, _, _ = TITULOS_CALLOUT[tipo]
        resto = "<p>" + interior[marca.end():]
        return (
            f'<div class="aviso aviso-{tipo}">'
            f'<div class="aviso-rotulo">{rotulo}</div>{resto}</div>'
        )

    return patron.sub(reemplazo, html)


def css_avisos() -> str:
    reglas = []
    for tipo, (_, color, fondo, borde) in TITULOS_CALLOUT.items():
        reglas.append(
            f".aviso-{tipo} {{ background: {fondo}; border-left: 3px solid {borde}; }}\n"
            f".aviso-{tipo} .aviso-rotulo {{ color: {color}; }}"
        )
    return "\n".join(reglas)


def hoja_de_estilos() -> str:
    return f"""
{caras_de_fuente()}

@page {{
    size: A4 portrait;
    margin: 16mm 15mm 15mm 15mm;
}}
@page :first {{ margin: 0; }}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
    color: #1A202C;
    font-size: 10.2pt;
    line-height: 1.55;
    background: #FFFFFF;
    -webkit-font-smoothing: antialiased;
}}

/* ── Portada ─────────────────────────────────────────────────────── */
.portada {{
    width: 210mm; height: 297mm;
    background:
        radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.16) 0%, transparent 42%),
        radial-gradient(circle at 15% 85%, rgba(232, 64, 64, 0.20) 0%, transparent 45%),
        linear-gradient(145deg, #180710 0%, #2A0B1A 45%, #15050D 100%);
    color: #FFFFFF;
    padding: 20mm 17mm;
    display: flex; flex-direction: column; justify-content: space-between;
    break-after: page;
    position: relative; overflow: hidden;
}}
.portada-trama {{
    position: absolute; inset: 0;
    background-image:
        linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 32px 32px;
}}
.portada > * {{ position: relative; }}
.marca {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 11pt; letter-spacing: 0.18em;
}}
.kicker {{
    font-size: 8.5pt; font-weight: 700; letter-spacing: 0.2em;
    color: {ACENTO}; margin-bottom: 6mm;
}}
.titulo-portada {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 34pt; line-height: 1.06; text-transform: uppercase;
    text-wrap: balance;
}}
.titulo-portada span {{ color: {ACENTO}; }}
.bajada {{
    font-size: 10.5pt; line-height: 1.6; color: #E4D8DE;
    max-width: 120mm; margin-top: 7mm;
}}
.filete {{ width: 22mm; height: 3px; background: {ACENTO}; margin-top: 8mm; }}
.pastillas {{ display: flex; flex-direction: column; gap: 2.6mm; margin-top: 9mm; }}
.pastilla {{
    font-size: 9pt; font-weight: 600; color: #F3E9EE;
    border: 1px solid rgba(255,255,255,0.16); border-radius: 4px;
    padding: 2.2mm 3.4mm; background: rgba(255,255,255,0.04);
    align-self: flex-start;
}}
.aviso-portada {{
    font-size: 8.2pt; line-height: 1.5; color: #D8C7CF;
    border-left: 2px solid rgba(232,64,64,0.55);
    padding-left: 4mm; max-width: 128mm;
}}
/* El rojo de marca es para fondo claro: sobre la portada oscura no alcanza el
   contraste minimo y el rotulo se pierde. Mismo criterio que el pie de las
   Stories. */
.aviso-portada strong {{ color: #FF9A9A; letter-spacing: 0.06em; }}
.pie-portada {{
    display: flex; justify-content: space-between; align-items: flex-end;
    border-top: 1px solid rgba(255,255,255,0.14); padding-top: 4mm; margin-top: 7mm;
    font-size: 8.4pt; color: #B9A5AE;
}}

/* ── Cuerpo ──────────────────────────────────────────────────────── */
main h1 {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 17pt; line-height: 1.2; color: #15050D;
    border-bottom: 2.5px solid {ACENTO};
    padding-bottom: 3mm; margin: 0 0 6mm 0;
    break-before: page; break-after: avoid;
    text-wrap: balance;
}}
main > h1:first-child {{ break-before: auto; }}
main h2 {{
    font-size: 12.5pt; font-weight: 800; color: #0F172A;
    margin: 7mm 0 3mm 0; break-after: avoid;
    border-left: 3px solid {ACENTO}; padding-left: 3mm;
}}
main h3 {{
    font-size: 10.8pt; font-weight: 700; color: #1F2937;
    margin: 5.5mm 0 2mm 0; break-after: avoid;
}}
main h4 {{ font-size: 10pt; font-weight: 700; margin: 4mm 0 1.5mm 0; break-after: avoid; }}

p {{ margin: 0 0 3mm 0; }}
strong {{ font-weight: 700; color: #0F172A; }}
em {{ font-style: italic; }}
a {{ color: #0F766E; text-decoration: none; }}

ul, ol {{ margin: 0 0 3.5mm 5.5mm; }}
li {{ margin-bottom: 1.6mm; }}
li > ul, li > ol {{ margin-top: 1.6mm; margin-bottom: 0; }}

code {{
    font-family: 'Space Grotesk', Consolas, monospace;
    font-size: 9pt; background: #F1F5F9; color: #0F172A;
    padding: 0.4mm 1.2mm; border-radius: 2px;
}}
pre {{
    background: #0F172A; color: #E2E8F0;
    font-family: 'Space Grotesk', Consolas, monospace;
    font-size: 8.6pt; line-height: 1.55;
    padding: 4mm 5mm; border-radius: 5px;
    margin: 0 0 4mm 0; break-inside: avoid;
    border-left: 3px solid {ACENTO};
}}
pre code {{ background: none; color: inherit; padding: 0; font-size: inherit; }}

table {{
    width: 100%; border-collapse: collapse;
    font-size: 8.9pt; margin: 0 0 4.5mm 0;
    break-inside: avoid;
}}
thead {{ background: #15050D; }}
th {{
    color: #FFFFFF; font-weight: 700; font-size: 8.4pt;
    text-align: left; padding: 2.2mm 2.6mm;
    border-right: 1px solid rgba(255,255,255,0.10);
}}
th:last-child {{ border-right: none; }}
/* El `strong` global pinta oscuro, y en el encabezado el fondo tambien es
   oscuro: un titulo de columna en negrita quedaba ilegible. */
th strong, th em {{ color: inherit; }}
td {{
    padding: 2mm 2.6mm; border-bottom: 1px solid #E2E8F0;
    vertical-align: top;
}}
tbody tr:nth-child(even) {{ background: #F8FAFC; }}
td strong {{ color: #0F172A; }}

blockquote {{
    background: #F8FAFC; border-left: 3px solid #CBD5E1;
    padding: 3.5mm 4.5mm; margin: 0 0 4mm 0;
    break-inside: avoid; font-size: 9.6pt;
}}
blockquote h3 {{ margin-top: 0; font-size: 10.2pt; }}
blockquote p:last-child, blockquote ul:last-child {{ margin-bottom: 0; }}

.aviso {{
    padding: 3.5mm 4.5mm; margin: 0 0 4.5mm 0;
    border-radius: 0 4px 4px 0; font-size: 9.5pt;
    break-inside: avoid;
}}
.aviso-rotulo {{
    font-size: 8pt; font-weight: 800; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 2mm;
}}
.aviso p:last-child, .aviso ul:last-child {{ margin-bottom: 0; }}
{css_avisos()}

hr {{
    border: none; border-top: 1px solid #E2E8F0;
    margin: 5mm 0; height: 0;
}}
main h1 + hr {{ display: none; }}

/* Los envoltorios de los diagramas vienen del markdown con estilo en línea.
   Se los ancla por ese atributo para que ninguno se parta entre dos páginas. */
div[style*="justify-content: center"] {{ break-inside: avoid; margin: 4mm 0 5mm 0; }}
svg {{ max-width: 100%; height: auto; break-inside: avoid; }}
"""


def construir_portada() -> str:
    return """
<div class="portada">
  <div class="portada-trama"></div>
  <div>
    <div class="marca">GRUPO INTELIGENCIA</div>
  </div>
  <div>
    <div class="kicker">DEPARTAMENTO DE ESTUDIOS Y RESEARCH</div>
    <div class="titulo-portada">Manual de<br><span>Operaciones</span><br>Intermercado</div>
    <div class="filete"></div>
    <div class="bajada">
      De la macroeconom&iacute;a real a tu plataforma MetaTrader&nbsp;5.
      Aprende a leer el clima econ&oacute;mico, construir tu propia ficha de
      operaci&oacute;n y dimensionar el riesgo con precisi&oacute;n.
    </div>
    <div class="pastillas">
      <div class="pastilla">12 m&oacute;dulos autocontenidos y 3 anexos de consulta</div>
      <div class="pastilla">Los 5 climas del mercado, con sus umbrales exactos</div>
      <div class="pastilla">3 setups excluyentes sobre velas de 1 hora cerradas</div>
      <div class="pastilla">Del 1&nbsp;% de riesgo al lote exacto, activo por activo</div>
    </div>
  </div>
  <div>
    <div class="aviso-portada">
      <strong>AVISO DE RIESGO.</strong> Material formativo y educativo. No constituye
      asesor&iacute;a financiera personalizada ni garantiza rentabilidades futuras.
      El trading en contratos por diferencia con apalancamiento conlleva un alto
      riesgo de p&eacute;rdida de capital. Las &oacute;rdenes las ejecutas t&uacute;,
      manualmente, en tu propia plataforma.
    </div>
    <div class="pie-portada">
      <div>Manual formativo para el trader</div>
      <div style="text-align: right;">
        <div style="color:#FFFFFF; font-weight:700;">Septiembre 2026</div>
        <div>Direcci&oacute;n de Trading</div>
      </div>
    </div>
  </div>
</div>
"""


def renderizar_markdown(texto: str) -> str:
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": True, "breaks": False}).enable("table")
    return procesar_callouts(md.render(texto))


def construir_html() -> str:
    if not ORIGEN_MD.exists():
        raise SystemExit(f"No existe el markdown fuente: {ORIGEN_MD}")

    cuerpo = renderizar_markdown(ORIGEN_MD.read_text(encoding="utf-8"))
    return (
        "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<title>Manual de Operaciones · Trading Cuantitativo Intermercado</title>\n"
        f"<style>{hoja_de_estilos()}</style>\n</head>\n<body>\n"
        f"{construir_portada()}\n<main>\n{cuerpo}\n</main>\n</body>\n</html>\n"
    )


def compilar_pdf() -> int:
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    html = construir_html()
    print(f"Fuente   : {ORIGEN_MD.relative_to(RAIZ)}")
    print(f"HTML     : {len(html) / 1024:.1f} KB")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 794, "height": 1123})
        pagina.set_content(html, wait_until="load")
        pagina.emulate_media(media="print")
        pdf = pagina.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        navegador.close()

    SALIDA_DOCS.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_DOCS.write_bytes(pdf)
    if SALIDA_CENTRAL.parent.exists():
        SALIDA_CENTRAL.write_bytes(pdf)

    paginas = len(PdfReader(SALIDA_DOCS).pages)
    print(f"Salida   : {SALIDA_DOCS.relative_to(RAIZ)}")
    print(f"Tamano   : {len(pdf) / 1024:.1f} KB")
    print(f"Paginas  : {paginas}")

    if paginas < PAGINAS_MINIMAS:
        raise SystemExit(
            f"El PDF salio con {paginas} paginas y se esperan al menos "
            f"{PAGINAS_MINIMAS}. Un manual al que le faltan secciones se lee como "
            "completo, asi que la compilacion se detiene."
        )
    print("\nOK: el manual salio completo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(compilar_pdf())
