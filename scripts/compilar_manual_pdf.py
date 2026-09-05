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


def procesar_fichas_activos(html: str) -> str:
    """Envuelve las secciones del Módulo 10 en contenedores con estilos por activo."""
    activos = [
        ("10.1", "ficha-usdclp"),
        ("10.2", "ficha-oro"),
        ("10.3", "ficha-wti"),
        ("10.4", "ficha-us100"),
    ]
    for prefijo, slug in activos:
        patron = re.compile(
            rf"(<h2>\s*{re.escape(prefijo)}.*?</h2>.*?)(?=(?:<h2>|<hr\s*/?>|<h1>|$))",
            re.S,
        )
        html = patron.sub(rf'<div class="ficha-activo {slug}">\n\1</div>\n', html)
    return html


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
    color: #2D3748;
    font-size: 10.2pt;
    line-height: 1.55;
    background: #FFFFFF;
    -webkit-font-smoothing: antialiased;
}}

/* ── Portada Estilo Editorial Oscuro ─────────────────────────────── */
.portada {{
    width: 210mm; height: 297mm;
    background: #04100D;
    color: #FFFFFF;
    padding: 22mm 20mm;
    display: flex; flex-direction: column; justify-content: space-between;
    break-after: page;
    position: relative; overflow: hidden;
}}
.portada-glow {{
    position: absolute; inset: 0;
    background:
        radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.22) 0%, transparent 65%),
        radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.16) 0%, transparent 60%),
        linear-gradient(135deg, #061814 0%, #020806 100%);
    z-index: 0;
}}
.portada-trama {{
    position: absolute; inset: 0;
    background-image:
        linear-gradient(to right, rgba(80, 192, 168, 0.04) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(80, 192, 168, 0.04) 1px, transparent 1px);
    background-size: 32px 32px;
    z-index: 1;
}}
.portada > * {{ position: relative; z-index: 2; }}

.cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(80, 192, 168, 0.3);
    padding-bottom: 12px;
}}
.cover-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.cover-logo-icon {{
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #50C0A8, #3E91AF);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: #04100D;
}}
.cover-logo-text {{
    font-family: 'Goldman', sans-serif;
    font-size: 13pt;
    font-weight: 700;
    letter-spacing: 0.10em;
    color: #FFFFFF;
}}
.cover-badge {{
    background: rgba(80, 192, 168, 0.15);
    border: 1px solid rgba(80, 192, 168, 0.4);
    color: #50C0A8;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.14em;
    padding: 4px 14px;
    border-radius: 100px;
    text-transform: uppercase;
}}

.kicker {{
    font-size: 9pt; font-weight: 700; letter-spacing: 0.18em;
    color: #3E91AF; text-transform: uppercase; margin-bottom: 5mm;
}}
.titulo-portada {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 34pt; line-height: 1.08; text-transform: uppercase;
    text-wrap: balance;
}}
.titulo-portada span {{ color: {ACENTO}; }}
.filete {{ width: 22mm; height: 3px; background: {ACENTO}; margin-top: 6mm; }}
.bajada {{
    font-size: 10.8pt; line-height: 1.6; color: #C1E5E4;
    max-width: 130mm; margin-top: 6mm;
}}

.cover-pastillas {{
    display: flex; flex-direction: column; gap: 2.8mm; margin-top: 8mm;
}}
.cover-card-glass {{
    background: rgba(8, 28, 23, 0.70);
    border: 1px solid rgba(80, 192, 168, 0.28);
    border-radius: 6px;
    padding: 2.4mm 4mm;
    font-size: 9pt; font-weight: 600; color: #E2E8F0;
    align-self: flex-start;
    display: flex; align-items: center; gap: 8px;
    backdrop-filter: blur(8px);
}}
.cover-card-bullet {{
    color: {ACENTO};
    font-size: 7.5pt;
}}

.aviso-portada {{
    background: rgba(8, 28, 23, 0.65);
    border: 1px solid rgba(80, 192, 168, 0.20);
    border-left: 3.5px solid #E84040;
    border-radius: 0 6px 6px 0;
    padding: 3mm 4.5mm;
    font-size: 8.2pt; line-height: 1.5; color: #B0B5C0;
    max-width: 140mm;
}}
.aviso-portada strong {{
    color: #FF9A9A; letter-spacing: 0.06em; font-weight: 700;
}}
.pie-portada {{
    display: flex; justify-content: space-between; align-items: flex-end;
    border-top: 1px solid rgba(80, 192, 168, 0.25);
    padding-top: 4mm; margin-top: 6mm;
    font-size: 8.4pt; color: #718096;
}}

/* ── Cuerpo ──────────────────────────────────────────────────────── */
main h1 {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 17pt; line-height: 1.2; color: #0B1916;
    border-bottom: 2.5px solid {ACENTO};
    padding-bottom: 3mm; margin: 0 0 6mm 0;
    break-before: page; break-after: avoid;
    text-wrap: balance;
}}
main > h1:first-child {{ break-before: auto; }}
main h2 {{
    font-size: 12.5pt; font-weight: 800; color: #0B1916;
    margin: 7mm 0 3mm 0; break-after: avoid;
    border-left: 3px solid {ACENTO}; padding-left: 3mm;
}}
main h3 {{
    font-size: 10.8pt; font-weight: 700; color: #143028;
    margin: 5.5mm 0 2mm 0; break-after: avoid;
}}
main h4 {{ font-size: 10pt; font-weight: 700; color: #2D3748; margin: 4mm 0 1.5mm 0; break-after: avoid; }}

p {{ margin: 0 0 3mm 0; }}
strong {{ font-weight: 700; color: #0B1916; }}
em {{ font-style: italic; }}
a {{ color: #0F766E; text-decoration: none; }}

ul, ol {{ margin: 0 0 3.5mm 5.5mm; }}
li {{ margin-bottom: 1.6mm; }}
li > ul, li > ol {{ margin-top: 1.6mm; margin-bottom: 0; }}

code {{
    font-family: 'Space Grotesk', Consolas, monospace;
    font-size: 9pt; background: #F1F5F9; color: #0B1916;
    padding: 0.4mm 1.2mm; border-radius: 2px;
}}
pre {{
    background: #0B1916; color: #E2E8F0;
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
thead {{ background: #0B1916; }}
th {{
    color: #FFFFFF; font-weight: 700; font-size: 8.4pt;
    text-align: left; padding: 2.2mm 2.6mm;
    border-right: 1px solid rgba(255,255,255,0.10);
    border-bottom: 2px solid {ACENTO};
}}
th:last-child {{ border-right: none; }}
th strong, th em {{ color: inherit; }}
td {{
    padding: 2mm 2.6mm; border-bottom: 1px solid #E2E8F0;
    vertical-align: top;
    color: #334155;
}}
tbody tr:nth-child(even) {{ background: #F8FAFC; }}
td strong {{ color: #0B1916; }}

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

div[style*="justify-content: center"] {{ break-inside: avoid; margin: 4mm 0 5mm 0; }}
svg {{ max-width: 100%; height: auto; break-inside: avoid; }}

/* ── Fichas por Activo (Módulo 10) ────────────────────────────────── */
.ficha-activo {{
    margin-bottom: 4mm;
}}
.ficha-activo h2 {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2.2mm 3.2mm;
    border-radius: 4px;
    margin: 3.5mm 0 2.2mm 0;
}}
.ficha-activo table {{
    margin-bottom: 3mm;
}}

/* USD/CLP · Acento / Menta */
.ficha-usdclp h2 {{
    background: #F0FDF4;
    border-left: 4px solid #50C0A8;
    color: #065F46;
}}
.ficha-usdclp thead {{
    background: #0E2420;
}}
.ficha-usdclp th {{
    border-bottom: 2px solid #50C0A8;
}}

/* Oro · XAU/USD */
.ficha-oro h2 {{
    background: #FEF9EE;
    border-left: 4px solid #E8B44C;
    color: #854D0E;
}}
.ficha-oro thead {{
    background: #241A06;
}}
.ficha-oro th {{
    border-bottom: 2px solid #E8B44C;
}}
.ficha-oro .aviso-important {{
    background: #FEF9EE;
    border-left: 3px solid #E8B44C;
}}
.ficha-oro .aviso-important .aviso-rotulo {{
    color: #854D0E;
}}

/* WTI y Brent · Petróleo */
.ficha-wti h2 {{
    background: #FFF7ED;
    border-left: 4px solid #E8783C;
    color: #9A3412;
}}
.ficha-wti thead {{
    background: #261105;
}}
.ficha-wti th {{
    border-bottom: 2px solid #E8783C;
}}

/* Nasdaq 100 · US100 */
.ficha-us100 h2 {{
    background: #EFF6FF;
    border-left: 4px solid #4C86E8;
    color: #1E40AF;
}}
.ficha-us100 thead {{
    background: #091733;
}}
.ficha-us100 th {{
    border-bottom: 2px solid #4C86E8;
}}
"""


def construir_portada() -> str:
    return """
<div class="portada">
  <div class="portada-glow"></div>
  <div class="portada-trama"></div>
  <div class="cover-top">
    <div class="cover-logo">
      <div class="cover-logo-icon">GI</div>
      <div class="cover-logo-text">GRUPO INTELIGENCIA</div>
    </div>
    <div class="cover-badge">MANUAL OFICIAL</div>
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
    <div class="cover-pastillas">
      <div class="cover-card-glass">
        <span class="cover-card-bullet">&#9670;</span>
        <span>12 m&oacute;dulos autocontenidos y 3 anexos de consulta</span>
      </div>
      <div class="cover-card-glass">
        <span class="cover-card-bullet">&#9670;</span>
        <span>Los 5 climas del mercado, con sus umbrales exactos</span>
      </div>
      <div class="cover-card-glass">
        <span class="cover-card-bullet">&#9670;</span>
        <span>3 setups excluyentes sobre velas de 1 hora cerradas</span>
      </div>
      <div class="cover-card-glass">
        <span class="cover-card-bullet">&#9670;</span>
        <span>Del 1&nbsp;% de riesgo al lote exacto, activo por activo</span>
      </div>
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
    html = procesar_callouts(md.render(texto))
    return procesar_fichas_activos(html)


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
