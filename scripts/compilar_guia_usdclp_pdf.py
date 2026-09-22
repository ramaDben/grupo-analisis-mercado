#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compila la guía táctica desde datos versionados y auditables del repositorio.

Cumple con la Gobernanza y Estándar de Producción de Guías Educativas:
- Cero Blur / 100% Abierto (Anti-Blur)
- Integridad cuantitativa: niveles H1 leídos desde el snapshot MT5 vigente
- Regla pedagógica de 3 capas
- Estándar Sin Zoom (tipografías vectoriales legibles >= 10pt)
- Page Budgeting autocontenido: exactamente 10 páginas A4 sin líneas huérfanas
- Sales Enablement hacia la Clínica Táctica de Post Venta (Martes 19:30 CLT)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
ORIGEN_MD = RAIZ / "docs" / "guia_tactica_usdclp_cobre_fed.md"
SALIDA_PDF = RAIZ / "docs" / "GUIA_TACTICA_USDCLP_COBRE_FED_GI.pdf"

# Importar artefactos y estilos modulares
from guia_usdclp.svg_artefactos_1 import (
    svg_flujo_mercado,
    svg_balancin_cobre,
    svg_matriz_cuadrantes,
    svg_grafico_tradingview_h1,
    svg_grafico_mt5_h1,
)
from guia_usdclp.svg_artefactos_2 import (
    svg_diagrama_lotajes,
    svg_checklist_hud,
    svg_timeline_sesiones,
    svg_curva_drawdown,
    svg_ticket_mesa_tecnica,
)
from guia_usdclp.estilos import (
    codificar_asset_base64,
    hoja_de_estilos,
    construir_portada,
    procesar_callouts,
)


def cargar_datos() -> dict[str, object]:
    """Carga las cifras en tiempo de compilación y rechaza fuentes no auditables."""
    import json

    precios = json.loads(
        (RAIZ / "data central" / "DATA PRECIOS OHLC" / "USDCLP_H1.json").read_text(
            encoding="utf-8"
        )
    )
    cobre = json.loads(
        (RAIZ / "data central" / "DATA PRECIOS OHLC" / "COPPER_W1.json").read_text(
            encoding="utf-8"
        )
    )
    drivers = json.loads(
        (RAIZ / "data central" / "DATA DRIVERS USDCLP" / "latest_drivers.json").read_text(
            encoding="utf-8"
        )
    )
    required = {
        "USDCLP_H1": precios,
        "COPPER_W1": cobre,
    }
    for name, payload in required.items():
        if payload.get("source") != "MT5" or payload.get("broker") != "MT5":
            raise RuntimeError(f"{name} no proviene de MT5: {payload.get('source')}")
        if payload.get("cuenta") != 51492:
            raise RuntimeError(f"{name} pertenece a una cuenta distinta de la declarada")

    h1 = precios["snapshot_actual"]
    copper_spot = cobre["snapshot_actual"]["close"]
    forward = drivers["drivers"]["POSICION_FORWARD_EXTRANJEROS_USD"]["valor"]
    return {
        "usdclp_spot": f"{h1['close']:.2f}",
        "ema50": f"{h1['ema_50']:.2f}",
        "ema200": f"{h1['ema_200']:.2f}",
        "donchian_high": f"{h1['donchian_50_high']:.2f}",
        "donchian_low": f"{h1['donchian_50_low']:.2f}",
        "atr_h1": f"{h1['atr_14']:.2f}",
        "rsi_h1": f"{h1['rsi_14']:.2f}",
        "copper": f"{copper_spot:.0f}",
        "forward": f"-${abs(forward):,.0f}".replace(",", "."),
        "tpm": f"{drivers['drivers']['CHILE_TPM']['valor']:.2f}",
        "fed": f"{drivers['drivers']['FED_FUNDS_RATE']['valor']:.2f}",
        "treasury10": f"{drivers['drivers']['US_10Y_TREASURY']['valor']:.2f}",
        "rows": precios["rows"],
    }


def renderizar_markdown(texto: str) -> str:
    from markdown_it import MarkdownIt

    bloques = [b.strip() for b in texto.split("\n---") if b.strip()]
    md = MarkdownIt("commonmark", {"html": True, "breaks": False}).enable("table")

    datos = cargar_datos()
    artefactos = {
        "<!-- TOKEN_DIAGRAMA_FLUJO_MERCADO -->": svg_flujo_mercado(datos["forward"]),
        "<!-- TOKEN_DIAGRAMA_BALANCIN_COBRE -->": svg_balancin_cobre(datos["copper"]),
        "<!-- TOKEN_MATRIZ_CUADRANTES_MACRO -->": svg_matriz_cuadrantes(
            datos["tpm"], datos["fed"]
        ),
        "<!-- TOKEN_GRAFICO_TRADINGVIEW_H1 -->": svg_grafico_tradingview_h1(
            datos,
            (RAIZ / "scripts" / "vendor" / "lightweight-charts.standalone.production.js").read_text(
                encoding="utf-8"
            ),
        ),
        "<!-- TOKEN_GRAFICO_MT5_H1 -->": svg_grafico_tradingview_h1(
            datos,
            (RAIZ / "scripts" / "vendor" / "lightweight-charts.standalone.production.js").read_text(
                encoding="utf-8"
            ),
        ),
        "<!-- TOKEN_DIAGRAMA_LOTAJES -->": svg_diagrama_lotajes(),
        "<!-- TOKEN_DIAGRAMA_CHECKLIST_HUD -->": svg_checklist_hud(),
        "<!-- TOKEN_TIMELINE_SESIONES -->": svg_timeline_sesiones(),
        "<!-- TOKEN_GRAFICO_DRAWDOWN -->": svg_curva_drawdown(),
        "<!-- TOKEN_TICKET_MESA_TECNICA -->": svg_ticket_mesa_tecnica(),
    }

    secciones_html = []
    # El bloque 0 es el título inicial (Portada)
    for i, bloque in enumerate(bloques[1:], start=1):
        html_bloque = md.render(bloque)

        # Inyectar artefactos vectoriales
        for token, svg in artefactos.items():
            if token in html_bloque:
                html_bloque = html_bloque.replace(token, svg)

        # Procesar callouts
        html_bloque = procesar_callouts(html_bloque)

        # Extraer títulos
        m_h2 = re.search(r"<h2>(.*?)</h2>", html_bloque)
        m_h3 = re.search(r"<h3>(.*?)</h3>", html_bloque)
        
        tit_texto = m_h2.group(1) if m_h2 else f"Módulo {i}"
        sub_texto = m_h3.group(1) if m_h3 else ""

        if m_h2:
            html_bloque = html_bloque.replace(m_h2.group(0), "")
        if m_h3:
            html_bloque = html_bloque.replace(m_h3.group(0), "")

        num_pag = i + 1
        imagenes_modulo = {
            1: ("activos/usdclp.jpg", "Mercado USD/CLP"),
            2: ("activos/copper.jpg", "Cobre y flujo de divisas"),
            3: ("activos/gbpusd.jpg", "Política monetaria y tasas"),
            5: ("activos/tech-circuito.jpg", "Gestión cuantitativa del riesgo"),
            9: ("activos/usdclp.jpg", "Mesa de análisis USD/CLP"),
        }
        imagen_html = ""
        if i in imagenes_modulo:
            asset, alt = imagenes_modulo[i]
            imagen_html = (
                f'<div class="modulo-imagen"><img src="{codificar_asset_base64(asset)}" '
                f'alt="{alt}"></div>'
            )

        cabecera_html = f"""
<div class="cabecera-modulo">
  <div class="cabecera-tag">GUÍA TÁCTICA USD/CLP · MÓDULO 0{i} DE 09</div>
  <div class="cabecera-marca">GRUPO INTELIGENCIA SpA · RESEARCH &amp; ESTRATEGIA</div>
</div>
<div class="titulo-modulo">{tit_texto}</div>
<div class="subtitulo-modulo">{sub_texto}</div>
"""

        pie_html = f"""
<div class="pie-modulo">
  <div>MANUAL DE ESTRATEGIAS USD/CLP · FEED INSTITUCIONAL GRUPO INTELIGENCIA</div>
  <div class="pie-num">PÁGINA {num_pag} DE 10</div>
</div>
"""

        seccion = f"""
<section class="seccion-pagina seccion-mod-{i}">
  <div>
    {cabecera_html}
  </div>
  {imagen_html}
  <div class="cuerpo-modulo">
    {html_bloque}
  </div>
  {pie_html}
</section>
"""
        secciones_html.append(seccion)

    return "\n".join(secciones_html)


def construir_html() -> str:
    if not ORIGEN_MD.exists():
        raise SystemExit(f"No existe el archivo markdown: {ORIGEN_MD}")

    datos = cargar_datos()
    texto = ORIGEN_MD.read_text(encoding="utf-8")
    for clave, valor in datos.items():
        if clave == "rows":
            continue
        texto = texto.replace("{{" + clave.upper() + "}}", valor)
    cuerpo = renderizar_markdown(texto)
    portada = construir_portada()
    lightweight_js = (
        RAIZ / "scripts" / "vendor" / "lightweight-charts.standalone.production.js"
    ).read_text(encoding="utf-8")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Guía Táctica USD/CLP: Cobre, Fed y Tasas · Grupo Inteligencia</title>
<style>{hoja_de_estilos()}</style>
<script>
// Polyfill ResizeObserver devicePixelContentBoxSize para renderizado Retina/300 DPI en Chromium headless
(function() {{
  const OrigRO = window.ResizeObserver;
  window.ResizeObserver = class extends OrigRO {{
    constructor(cb) {{
      super((entries, obs) => {{
        const dpr = window.devicePixelRatio || 1;
        const patchedEntries = entries.map(e => {{
          if (e.devicePixelContentBoxSize) {{
            const s = e.devicePixelContentBoxSize[0];
            const cs = e.contentBoxSize ? e.contentBoxSize[0] : s;
            return new Proxy(e, {{
              get(target, prop) {{
                if (prop === 'devicePixelContentBoxSize') {{
                  return [{{
                    inlineSize: Math.round(cs.inlineSize * dpr),
                    blockSize: Math.round(cs.blockSize * dpr)
                  }}];
                }}
                return target[prop];
              }}
            }});
          }}
          return e;
        }});
        cb(patchedEntries, obs);
      }});
    }}
  }};
}})();
</script>
</head>
<body>
<script>{lightweight_js}</script>
{portada}
<main>
{cuerpo}
</main>
</body>
</html>
"""


def compilar_pdf() -> int:
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    html = construir_html()
    print(f"Fuente   : {ORIGEN_MD.relative_to(RAIZ)}")
    print(f"HTML     : {len(html) / 1024:.1f} KB")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(
            viewport={"width": 794, "height": 1123},
            device_scale_factor=3
        )
        pagina.set_content(html, wait_until="load")
        pagina.wait_for_function(
            "() => document.querySelector('.chart-tv')?.dataset.chartReady === 'true'"
        )
        pagina.wait_for_timeout(400)
        pagina.emulate_media(media="print")
        pdf = pagina.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=False
        )
        navegador.close()

    SALIDA_PDF.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_PDF.write_bytes(pdf)

    paginas = len(PdfReader(SALIDA_PDF).pages)
    print(f"Salida   : {SALIDA_PDF.relative_to(RAIZ)}")
    print(f"Tamaño   : {len(pdf) / 1024:.1f} KB")
    print(f"Páginas  : {paginas}")

    if paginas == 10:
        print("\n✅ ÉXITO TOTAL: Guía táctica compilada con EXACTAMENTE 10 PÁGINAS A4.")
        return 0
    else:
        print(f"\n⚠️ ALERTA: La guía generó {paginas} páginas (se requieren 10 exactas).")
        return 1


if __name__ == "__main__":
    raise SystemExit(compilar_pdf())
