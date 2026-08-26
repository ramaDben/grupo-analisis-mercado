import argparse
import re
import base64
import markdown
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import pypdf

# La raiz se deduce de la ubicacion del script y no se escribe a mano: son cuatro
# niveles arriba (scripts -> generar-reporte-editorial -> skills -> .agents -> raiz).
# Con la ruta absoluta anterior el generador solo funcionaba en la maquina del
# director, que es la misma razon por la que .agents/mcp.json queda fuera de git.
RAIZ = Path(__file__).resolve().parents[4]
FUENTES = RAIZ / "templates" / "stories" / "fonts"

CATALOGO = [
    ("space-grotesk-600.woff2", "Space Grotesk", 600),
    ("space-grotesk-700.woff2", "Space Grotesk", 700),
    ("syne-800.woff2", "Syne", 800),
]

def _bloque_fuentes():
    reglas = []
    for archivo, familia, peso in CATALOGO:
        ruta = FUENTES / archivo
        if ruta.exists():
            datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
            reglas.append(
                f'@font-face{{font-family:"{familia}";font-weight:{peso};'
                f"font-style:normal;font-display:swap;"
                f'src:url(data:font/woff2;base64,{datos}) format("woff2")}}'
            )
    reglas.append(
        '@font-face{font-family:"Space Grotesk";font-weight:400;'
        'font-style:normal;font-display:swap;'
        f'src:url(data:font/woff2;base64,{base64.b64encode((FUENTES / "space-grotesk-600.woff2").read_bytes()).decode("ascii")}) format("woff2")}}'
    )
    return "\n".join(reglas)

# Tamano de letra base del maquetador: 10 a 10.5 px. Chromium imprime la A4 a
# 794 px de ancho, asi que 1 px equivale a 0,75 pt y el cuerpo del texto queda en
# 7,5-7,9 pt. El piso de legibilidad para texto impreso es 8 pt, y el folleto de
# este mismo repo se calibro a 11 pt con una nota explicita: "el material lo usa
# gente que no lee comodo a tamanos chicos".
#
# `escala` existe para subirlo SIN reescribir el CSS, porque este maquetador es
# compartido: cambiarlo de raiz alteraria tambien los informes ya emitidos (el del
# Motor GI entre ellos). Los documentos de cliente piden una escala mayor; los
# internos conservan la suya con el valor por defecto de 1.0.
#
# Solo se escalan los tamanos de lectura (<= 14 px). Los titulares de portada
# (46 px, 22 px) ya son grandes y multiplicarlos romperia el encuadre.
_LIMITE_ESCALADO_PX = 14.0


def _escalar_tipografia(html: str, escala: float) -> str:
    """Multiplica los tamanos de letra de lectura por `escala`."""
    if escala == 1.0:
        return html

    def _reemplazo(m: re.Match) -> str:
        valor = float(m.group(2))
        if valor > _LIMITE_ESCALADO_PX:
            return m.group(0)
        return f"{m.group(1)}{round(valor * escala, 2)}px"

    return re.sub(r"(font-size:\s*)([\d.]+)px", _reemplazo, html)


def _construir_html(
    html_content: str,
    titulo: str,
    subtitulo: str,
    badge_sup: str,
    tag_tipo: str,
    header_left: str,
    header_right: str,
    fecha: str,
    analista: str,
    paginas_badge: str,
    tema: str = "verde",
    escala: float = 1.0
) -> str:
    if tema == "verde":
        cover_bg = "#06231C"
        cover_grad_start = "#0F4539"
        cover_grad_end = "#06231C"
        disclaimer_bg = "#06231C"
        accent_color = "#3E91AF"       # Intercambio: Azul Cian para 'RESEARCH & ESTRATEGIA' y badges
        tag_color = "#82E0CE"          # Menta suave
        subtitle_color = "#D1F2EB"     # Menta claro
        divider_color = "#3E91AF"      # Azul Cian
        disclaimer_accent = "#3E91AF"  # Azul Cian para 'AVISO LEGAL'
    else:
        cover_bg = "#0D0D1A"
        cover_grad_start = "#1A1A2E"
        cover_grad_end = "#0D0D1A"
        disclaimer_bg = "#0D0D1A"
        accent_color = "#53C1AB"       # Verde Menta original
        tag_color = "#3E91AF"          # Azul Cian original
        subtitle_color = "#C1E5E4"
        divider_color = "#53C1AB"
        disclaimer_accent = "#53C1AB"

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
{_bloque_fuentes()}
@page {{
    size: A4 portrait;
    margin: 0;
}}
body {{
    margin: 0;
    padding: 0;
    font-family: 'Space Grotesk', sans-serif;
    color: #3A3F52;
    background: #FFFFFF;
}}
.page-container {{
    width: 794px;
    height: 1123px;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
    break-after: page;
}}
.cover-page {{
    background: {cover_bg};
    color: #FFFFFF;
    padding: 24mm 32mm;
    display: flex;
    flex-direction: column;
}}
.cover-gradient {{
    position: absolute;
    top: 0;
    right: 0;
    width: 42%;
    height: 100%;
    background: linear-gradient(180deg, {cover_grad_start} 0%, {cover_grad_end} 100%);
    opacity: 0.6;
}}
.flowing-container {{
    width: 794px;
    box-sizing: border-box;
    background: #FFFFFF;
    break-after: page;
}}
.flowing-table {{
    width: 100%;
    border-collapse: collapse;
}}
/* Thead/Tfoot para repetir margenes en cortes de pagina */
.flowing-table thead td {{
    padding: 13mm 24mm 0 24mm;
}}
.flowing-table tbody td {{
    padding: 0 24mm;
}}
.flowing-table tfoot td {{
    padding: 0 24mm 13mm 24mm;
}}

.header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 7px;
    border-bottom: 1px solid #C1E5E4;
    margin-bottom: 16px;
}}
.header-left {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3E91AF;
}}
.header-right {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px;
    font-weight: 600;
    color: #737373;
    letter-spacing: 0.05em;
}}
.footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 7px;
    border-top: 1px solid rgba(0,0,0,0.12);
    margin-top: 18px;
}}
.footer-left {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #53C1AB;
}}
.footer-right {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px;
    color: #737373;
    letter-spacing: 0.05em;
}}

/* Typography inside content */
.content {{
    padding-top: 4px;
}}
p {{
    font-size: 11.5px;
    line-height: 1.55;
    margin: 0 0 8px 0;
    font-weight: 400;
}}
h1 {{
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #0D0D1A;
    margin: 6px 0 16px 0;
    line-height: 1.25;
    border-bottom: 2px solid #53C1AB;
    padding-bottom: 8px;
    letter-spacing: -0.01em;
    display: block;
    transform: scaleY(1.14);
    transform-origin: left bottom;
}}
h2 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #3E91AF;
    margin: 16px 0 8px 0;
    border-left: 3.5px solid #53C1AB;
    padding-left: 10px;
    break-after: avoid;
    page-break-after: avoid;
}}
h3 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11.5px;
    font-weight: 700;
    color: #0D0D1A;
    margin: 10px 0 5px 0;
    break-after: avoid;
    page-break-after: avoid;
}}
ul, ol {{
    margin: 0 0 10px 0;
    padding-left: 18px;
    font-size: 11px;
    line-height: 1.55;
}}
li {{
    margin-bottom: 5px;
}}
li strong {{
    font-weight: 700;
    color: #0D0D1A;
}}
blockquote {{
    border-top: 1.5px solid #3E91AF;
    margin: 18px 0;
    background: rgba(62, 145, 175, 0.04);
    padding: 12px 16px;
    border-radius: 0 4px 4px 0;
    border-left: 3px solid #3E91AF;
}}
blockquote p {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: #3E91AF;
    margin: 0;
}}
hr {{
    border: none;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    margin: 18px 0;
}}
img {{
    width: 100%;
    max-height: 240px;
    object-fit: contain;
    border-radius: 5px;
    border: 1px solid #D0D7DE;
    margin: 10px 0 14px 0;
    display: block;
    box-shadow: 0 2px 8px rgba(13, 13, 26, 0.05);
    break-inside: avoid;
    page-break-inside: avoid;
}}
/* Estilo para tablas Markdown */
.content table {{
    width: 100% !important;
    display: table !important;
    table-layout: auto !important;
    border-collapse: collapse !important;
    margin: 16px 0 20px 0;
    font-size: 10.5px;
    break-inside: avoid;
    page-break-inside: avoid;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #D0D7DE;
    box-shadow: 0 2px 6px rgba(13, 13, 26, 0.04);
}}
.content th {{
    background: #0D0D1A !important;
    color: #FFFFFF !important;
    padding: 9px 12px !important;
    font-weight: 700 !important;
    text-align: left !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 10px !important;
    letter-spacing: 0.03em !important;
    border-bottom: 2px solid #53C1AB !important;
    white-space: normal !important;
}}
.content td {{
    padding: 9px 12px !important;
    border-bottom: 1px solid #E9ECEF !important;
    color: #3A3F52 !important;
    vertical-align: top !important;
    line-height: 1.45 !important;
    background: #FFFFFF !important;
    font-size: 10px !important;
    white-space: normal !important;
}}
.content tr:nth-child(even) td {{
    background: #F8FAF9 !important;
}}
</style>
</head>
<body>

<!-- PAGE 1: PORTADA -->
<div class="page-container cover-page">
    <div class="cover-gradient"></div>
    <div style="display:flex;justify-content:space-between;align-items:center;position:relative;z-index:1;">
        <span style="font-family:'Syne',sans-serif;font-size:16px;font-weight:800;letter-spacing:0.04em;color:#FFFFFF;display:inline-block;transform:scaleY(1.18);transform-origin:left center;">GRUPO INTELIGENCIA</span>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:9.5px;font-weight:700;letter-spacing:0.18em;color:{accent_color};">{badge_sup}</span>
    </div>
    
    <div style="flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;z-index:1;max-width:82%;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:600;letter-spacing:0.14em;color:{tag_color};text-transform:uppercase;margin-bottom:12px;">{tag_tipo}</span>
        <h1 style="font-family:'Syne',sans-serif;font-size:46px;font-weight:800;line-height:1.08;margin:0 0 34px 0;color:#FFFFFF;border:none;padding:0;letter-spacing:-0.02em;display:block;transform:scaleY(1.15);transform-origin:left top;">{titulo}</h1>
        <p style="font-family:'Space Grotesk',sans-serif;font-size:13px;line-height:1.6;color:{subtitle_color};margin:0 0 24px 0;max-width:90%;font-weight:400;">{subtitulo}</p>
        <div style="width:48px;height:3px;background:{divider_color};"></div>
    </div>
    
    <div style="position:relative;z-index:1;border-top:1px solid rgba(255,255,255,0.16);padding-top:12px;display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;gap:24px;">
            <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-family:'Space Grotesk',sans-serif;font-size:8px;letter-spacing:0.1em;text-transform:uppercase;color:#737373;">Fecha</span>
                <span style="font-family:'Space Grotesk',sans-serif;font-size:10.5px;font-weight:600;color:#FFFFFF;">{fecha}</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-family:'Space Grotesk',sans-serif;font-size:8px;letter-spacing:0.1em;text-transform:uppercase;color:#737373;">Analista</span>
                <span style="font-family:'Space Grotesk',sans-serif;font-size:10.5px;font-weight:600;color:#FFFFFF;">{analista}</span>
            </div>
        </div>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:8.5px;font-weight:600;color:{accent_color};">{paginas_badge}</span>
    </div>
</div>

<!-- PAGINAS FLUIDAS DE CONTENIDO -->
<div class="flowing-container">
    <table class="flowing-table">
        <thead>
            <tr><td>
                <div class="header">
                    <span class="header-left">{header_left}</span>
                    <span class="header-right">{header_right}</span>
                </div>
            </td></tr>
        </thead>
        <tbody>
            <tr><td>
                <div class="content">
                    {html_content}
                </div>
            </td></tr>
        </tbody>
        <tfoot>
            <tr><td>
                <div class="footer">
                    <span class="footer-left">GRUPO INTELIGENCIA</span>
                    <span class="footer-right">RESEARCH Y ESTRATEGIA</span>
                </div>
            </td></tr>
        </tfoot>
    </table>
</div>

<!-- PAGE FINAL: DISCLAIMER -->
<div class="page-container" style="background:{disclaimer_bg};color:#C1E5E4;padding:24mm 32mm;display:flex;flex-direction:column;">
    <div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:9px;border-bottom:1px solid rgba(255,255,255,0.15);margin-bottom:18px;flex-shrink:0;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:9.5px;font-weight:700;letter-spacing:0.14em;color:{disclaimer_accent};">AVISO LEGAL</span>
        <span style="font-family:'Syne',sans-serif;font-size:12px;font-weight:800;letter-spacing:0.04em;color:#FFFFFF;display:inline-block;transform:scaleY(1.18);transform-origin:left center;">GRUPO INTELIGENCIA</span>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;gap:12px;overflow:hidden;">
        <h2 style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#FFFFFF;margin:0;border:none;padding:0;letter-spacing:0;display:inline-block;transform:scaleY(1.15);transform-origin:left bottom;">Disclaimer</h2>
        <p style="font-family:'Space Grotesk',sans-serif;font-size:10px;line-height:1.7;color:#C1E5E4;margin:0;">Este documento ha sido elaborado por Grupo Inteligencia con fines exclusivamente informativos y no constituye una oferta, solicitud o recomendación de inversión. Las opiniones expresadas representan el análisis actual y están sujetas a cambios sin previo aviso.</p>
        <p style="font-family:'Space Grotesk',sans-serif;font-size:10px;line-height:1.7;color:#C1E5E4;margin:0;">La información contenida se basa en fuentes consideradas fiables al momento de su publicación; sin embargo, no se garantiza su exactitud, integridad o vigencia. Los mercados financieros implican riesgos, incluida la posible pérdida del capital invertido, y el desempeño pasado no garantiza resultados futuros.</p>
        <p style="font-family:'Space Grotesk',sans-serif;font-size:10px;line-height:1.7;color:#C1E5E4;margin:0;">Los niveles técnicos, escenarios y sesgos presentados corresponden a la interpretación del equipo de análisis. Este material es de uso exclusivo y no debe distribuirse a terceros sin autorización expresa.</p>
    </div>
</div>

</body>
</html>
"""
    return _escalar_tipografia(html, escala)



def _absolutizar_imagenes(html: str, base: Path) -> str:
    """Resuelve los `src` relativos contra la carpeta del markdown.

    Hace falta porque el HTML no se renderiza donde vive el markdown: se escribe
    en `scratch/temp_informe_diseno.html` y se navega con `file://`, asi que un
    `src="graficos/oro.png"` se busca dentro de `scratch/` y no aparece. El
    navegador no considera eso un error — dibuja el hueco y sigue —, de modo que
    el PDF sale con los graficos ausentes y sin que nada lo avise. Es el mismo
    fallo que ya tuvo `marca.css` con Playwright.

    Una ruta que no existe en disco se deja intacta a proposito: si el markdown
    apunta a un archivo equivocado, conviene que se vea el hueco en la revision
    y no que quede convertido en una ruta absoluta igual de rota.
    """
    def _sub(m):
        crudo = m.group(2)
        if re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|/|data:)", crudo):
            return m.group(0)  # absoluta, con esquema o data URI: no se toca
        destino = (base / unquote(crudo)).resolve()
        if not destino.is_file():
            return m.group(0)
        return f'{m.group(1)}{destino.as_uri()}{m.group(3)}'

    return re.sub(r'(<img[^>]*\ssrc=")([^"]+)(")', _sub, html)


def crear_pdf(
    md_path: str = None,
    out_path: str = None,
    titulo: str = "Minutas del FOMC",
    subtitulo: str = "Análisis de la reunión del Comité Federal de Mercado Abierto (FOMC). Perspectivas sobre tasas de interés en EE.UU., inflación, impacto de la Inteligencia Artificial y estabilidad financiera global.",
    badge_sup: str = "RESEARCH & ESTRATEGIA",
    tag_tipo: str = "REPORTE EJECUTIVO",
    header_left: str = "ANÁLISIS FUNDAMENTAL",
    header_right: str = "AGOSTO 2026 • MACROECONOMÍA",
    fecha: str = "Agosto 2026",
    analista: str = "Área de Estudios",
    tema: str = "verde",
    escala: float = 1.0
):
    if md_path:
        md_file = Path(md_path)
        if not md_file.is_absolute():
            md_file = RAIZ / md_file
    else:
        candidatos = [
            RAIZ / "data central" / "DATA USA" / "reportes_generados" / "informe_fomc.md",
            RAIZ / "data central" / "DATA CHILE" / "reportes_generados" / "informe_mercado.md",
            RAIZ / "data central" / "DATA DRIVERS USDCLP" / "reportes_generados" / "informe_drivers_usdclp.md"
        ]
        md_file = None
        for c in candidatos:
            if c.exists():
                md_file = c
                break
        if md_file is None:
            raise FileNotFoundError("No se encontro un archivo markdown para renderizar en las subcarpetas reportes_generados/")

    if out_path:
        out_pdf = Path(out_path)
        if not out_pdf.is_absolute():
            out_pdf = RAIZ / out_pdf
    else:
        out_pdf = md_file.parent / f"{md_file.stem}_GI.pdf"

    md_text = md_file.read_text(encoding="utf-8")
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    html_content = _absolutizar_imagenes(html_content, md_file.parent)

    tmp_html = RAIZ / "scratch" / "temp_informe_diseno.html"
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page()

        # Primer pase para calcular páginas
        html_inicial = _construir_html(
            html_content=html_content,
            titulo=titulo,
            subtitulo=subtitulo,
            badge_sup=badge_sup,
            tag_tipo=tag_tipo,
            header_left=header_left,
            header_right=header_right,
            fecha=fecha,
            analista=analista,
            paginas_badge="01 / --",
            tema=tema,
            escala=escala,
        )
        tmp_html.write_text(html_inicial, encoding="utf-8")
        pagina.goto(tmp_html.as_uri())
        pagina.emulate_media(media="print")
        pagina.wait_for_timeout(300)
        pagina.pdf(path=str(out_pdf), format="A4", print_background=True,
                   margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})

        # Contar páginas con pypdf
        with open(out_pdf, "rb") as f:
            lector = pypdf.PdfReader(f)
            total_pags = len(lector.pages)

        # Segundo pase con el badge final "01 / XX"
        badge_final = f"01 / {total_pags:02d}"

        html_final = _construir_html(
            html_content=html_content,
            titulo=titulo,
            subtitulo=subtitulo,
            badge_sup=badge_sup,
            tag_tipo=tag_tipo,
            header_left=header_left,
            header_right=header_right,
            fecha=fecha,
            analista=analista,
            paginas_badge=badge_final,
            tema=tema,
            escala=escala,
        )
        tmp_html.write_text(html_final, encoding="utf-8")
        pagina.goto(tmp_html.as_uri())
        pagina.emulate_media(media="print")
        pagina.wait_for_timeout(300)
        pagina.pdf(path=str(out_pdf), format="A4", print_background=True,
                   margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        navegador.close()

    print(f"PDF con diseño oficial original generado exitosamente ({total_pags} páginas) en: {out_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de Informes PDF Oficiales - Grupo Inteligencia")
    parser.add_argument("--md", dest="md_path", help="Ruta al archivo Markdown de entrada", default=None)
    parser.add_argument("--pdf", dest="out_path", help="Ruta de salida para el PDF", default=None)
    parser.add_argument("--title", dest="titulo", help="Título principal del informe", default="Minutas del FOMC")
    parser.add_argument("--subtitle", dest="subtitulo", help="Subtítulo de portada", default="Análisis de la reunión del Comité Federal de Mercado Abierto (FOMC). Perspectivas sobre tasas de interés en EE.UU., inflación, impacto de la Inteligencia Artificial y estabilidad financiera global.")
    parser.add_argument("--badge", dest="badge_sup", help="Badge superior derecho", default="RESEARCH & ESTRATEGIA")
    parser.add_argument("--tag", dest="tag_tipo", help="Tag sobre el título", default="REPORTE EJECUTIVO")
    parser.add_argument("--header-left", dest="header_left", help="Encabezado izquierdo", default="ANÁLISIS FUNDAMENTAL")
    parser.add_argument("--header-right", dest="header_right", help="Encabezado derecho", default="AGOSTO 2026 • MACROECONOMÍA")
    parser.add_argument("--date", dest="fecha", help="Fecha para la portada", default="Agosto 2026")
    parser.add_argument("--analyst", dest="analista", help="Nombre del analista o área", default="Área de Estudios")
    parser.add_argument("--escala", dest="escala", type=float, default=1.0,
                        help="Multiplica el tamano de letra de lectura (1.45 deja el cuerpo en ~11 pt)")
    parser.add_argument("--theme", dest="tema", help="Tema de color de portada (verde | oscuro)", default="verde")

    args = parser.parse_args()
    crear_pdf(
        md_path=args.md_path,
        out_path=args.out_path,
        titulo=args.titulo,
        subtitulo=args.subtitulo,
        badge_sup=args.badge_sup,
        tag_tipo=args.tag_tipo,
        header_left=args.header_left,
        header_right=args.header_right,
        fecha=args.fecha,
        analista=args.analista,
        tema=args.tema,
        escala=args.escala,
    )
