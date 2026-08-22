import argparse
import base64
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    import pypdf
except ImportError:
    pypdf = None

RAIZ = Path("C:/Users/bbrav/grupo-analisis-mercado")
FUENTES_DIR = RAIZ / "templates" / "stories" / "fonts"
TEMPLATE_PATH = RAIZ / "templates" / "informes" / "resumen_semanal.html"
DEFAULT_FIXTURE = RAIZ / "data" / "ejemplos" / "resumen_semanal_fixture.json"

CATALOGO_FUENTES = [
    ("dm-sans-400.woff2", "DM Sans", 400),
    ("dm-sans-700.woff2", "DM Sans", 700),
    ("space-grotesk-600.woff2", "Space Grotesk", 600),
    ("space-grotesk-700.woff2", "Space Grotesk", 700),
    ("syne-800.woff2", "Syne", 800),
    ("montserrat-700.woff2", "Montserrat", 700),
]

def _generar_bloque_fuentes() -> str:
    reglas = []
    for archivo, familia, peso in CATALOGO_FUENTES:
        ruta = FUENTES_DIR / archivo
        if ruta.exists():
            datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
            reglas.append(
                f'@font-face {{ font-family: "{familia}"; font-weight: {peso}; font-style: normal; '
                f'font-display: swap; src: url("data:font/woff2;base64,{datos}") format("woff2"); }}'
            )
    return "\n".join(reglas)

def _md_a_html(texto: str) -> str:
    """Convierte **negrita** simple a <strong>negrita</strong>"""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', str(texto))

def render_template(template_str: str, data: dict) -> str:
    # 1. Inyectar bloque de fuentes
    template_str = template_str.replace("{{bloque_fuentes}}", _generar_bloque_fuentes())

    # 2. Reemplazar campos escalares simples {{metadatos.*}}
    for k, v in data.get("metadatos", {}).items():
        template_str = template_str.replace(f"{{{{metadatos.{k}}}}}", str(v))

    # 3. Reemplazar analisis_intermercado
    for k, v in data.get("analisis_intermercado", {}).items():
        template_str = template_str.replace(f"{{{{analisis_intermercado.{k}}}}}", str(v))

    # 4. Sección Scorecard
    scorecard_match = re.search(r"{{#scorecard_activos}}(.*?){{/scorecard_activos}}", template_str, re.DOTALL)
    if scorecard_match:
        bloque_tmpl = scorecard_match.group(1)
        bloques_render = []
        for item in data.get("scorecard_activos", []):
            item_html = bloque_tmpl
            for k, v in item.items():
                item_html = item_html.replace(f"{{{{{k}}}}}", str(v))
            bloques_render.append(item_html)
        template_str = template_str.replace(scorecard_match.group(0), "".join(bloques_render))

    # 5. Sección Catalizadores Macro
    macro_match = re.search(r"{{#catalizadores_macro}}(.*?){{/catalizadores_macro}}", template_str, re.DOTALL)
    if macro_match:
        bloque_tmpl = macro_match.group(1)
        bloques_render = []
        for item in data.get("catalizadores_macro", []):
            item_html = bloque_tmpl
            for k, v in item.items():
                item_html = item_html.replace(f"{{{{{k}}}}}", str(v))
            bloques_render.append(item_html)
        template_str = template_str.replace(macro_match.group(0), "".join(bloques_render))

    # 6. Semáforo Táctico
    for grupo in ["oportunidades", "cautela", "riesgo"]:
        grupo_data = data.get("semaforo_tactico", {}).get(grupo, {})
        template_str = template_str.replace(f"{{{{semaforo_tactico.{grupo}.titulo}}}}", grupo_data.get("titulo", ""))
        
        tag_loop = f"{{{{#semaforo_tactico.{grupo}.items}}}}"
        tag_end = f"{{{{/semaforo_tactico.{grupo}.items}}}}"
        match = re.search(rf"{re.escape(tag_loop)}(.*?){re.escape(tag_end)}", template_str, re.DOTALL)
        if match:
            item_tmpl = match.group(1)
            items_render = []
            for item in grupo_data.get("items", []):
                rendered_item = item_tmpl.replace("{{{.}}}", _md_a_html(item))
                items_render.append(rendered_item)
            template_str = template_str.replace(match.group(0), "".join(items_render))

    # 7. Radar Próxima Semana
    radar_match = re.search(r"{{#radar_proxima_semana}}(.*?){{/radar_proxima_semana}}", template_str, re.DOTALL)
    if radar_match:
        bloque_tmpl = radar_match.group(1)
        bloques_render = []
        for item in data.get("radar_proxima_semana", []):
            item_html = bloque_tmpl
            impacto = str(item.get("impacto", "Medio")).lower()
            item_html = item_html.replace("{{impacto_class}}", impacto)
            for k, v in item.items():
                item_html = item_html.replace(f"{{{{{k}}}}}", str(v))
            bloques_render.append(item_html)
        template_str = template_str.replace(radar_match.group(0), "".join(bloques_render))

    return template_str

def generar_pdf_resumen(
    fixture_path: Path,
    out_pdf_path: Path,
    preview_images: bool = True
) -> dict:
    if not fixture_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {fixture_path}")

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    html_final = render_template(raw_html, data)

    tmp_dir = RAIZ / "scratch"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_html = tmp_dir / "temp_resumen_semanal.html"
    tmp_html.write_text(html_final, encoding="utf-8")

    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    preview_paths = []
    with sync_playwright() as pw:
        # A4 estándar @ 96 DPI: 794x1123 px. Con device_scale_factor=2 obtenemos alta resolución para preview.
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1600}, device_scale_factor=2)
        page.goto(tmp_html.as_uri())
        page.wait_for_timeout(400)

        # Generar PDF estricto A4 sin márgenes agregados por el navegador
        page.emulate_media(media="print")
        page.pdf(
            path=str(out_pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )

        # Si se piden previews, tomar capturas precisas de cada div .page
        if preview_images:
            page.emulate_media(media="screen")
            paginas_el = page.query_selector_all(".page")
            for i, p_el in enumerate(paginas_el):
                img_path = tmp_dir / f"preview_pagina{i+1}.png"
                p_el.screenshot(path=str(img_path))
                preview_paths.append(img_path)

        browser.close()

    total_pags = 2
    if pypdf:
        try:
            with open(out_pdf_path, "rb") as f:
                lector = pypdf.PdfReader(f)
                total_pags = len(lector.pages)
        except Exception:
            pass

    return {
        "pdf_path": str(out_pdf_path),
        "total_paginas": total_pags,
        "preview_paths": [str(p) for p in preview_paths]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de Informe Resumen Semanal PDF - Grupo Inteligencia")
    parser.add_argument("--fixture", dest="fixture", default=str(DEFAULT_FIXTURE), help="Ruta al archivo JSON de datos")
    parser.add_argument("--out", dest="out_pdf", default=str(RAIZ / "scratch" / "Resumen_Semanal_Mercados_GI.pdf"), help="Ruta de salida para el PDF")
    parser.add_argument("--preview-images", dest="preview_images", action="store_true", default=True, help="Exportar PNGs de previsualización")

    args = parser.parse_args()
    resultado = generar_pdf_resumen(
        fixture_path=Path(args.fixture),
        out_pdf_path=Path(args.out_pdf),
        preview_images=args.preview_images
    )
    print(f"[OK] PDF generado exitosamente: {resultado['pdf_path']}")
    print(f"[PAGINAS] Total de paginas: {resultado['total_paginas']}")
    for p in resultado["preview_paths"]:
        print(f"[PREVIEW] Previsualizacion: {p}")
