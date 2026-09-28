#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compila `docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md` a PDF A4.

Estándar Editorial de Alta Resolución (300 DPI) y Cero Espacios Huérfanos:
- Portada 'Midnight Alpha & Multi-Asset' con iluminación volumétrica multicapa.
- Feed de datos MT5 dinámico leído desde `latest_prices_summary.json`.
- Aislamiento total de SVGs con tokens alfanuméricos contra `markdown-it`.
- Diagramas vectoriales con velas nítidas, contrastadas y tipografía legible >= 10pt.
- Flujo editorial continuo y equilibrado sin vacíos en blanco.
- Renderizado de alta definición con Playwright Chromium (device_scale_factor=3).
"""

from __future__ import annotations

import base64
import json
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

from artefactos_manual import (
    svg_algoritmo_stop_loss,
    svg_comprobacion_margen,
    generar_bloque_grafico_tradingview,
)

FUENTES = RAIZ / "templates" / "stories" / "fonts"
ORIGEN_MD = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
SALIDA_DOCS = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"
SALIDA_CENTRAL = (
    RAIZ / "data central" / "DATA MOTOR GI" / "reportes_generados"
    / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"
)
PRICES_JSON = RAIZ / "data central" / "DATA PRECIOS OHLC" / "latest_prices_summary.json"
VENDOR_TV_JS = RAIZ / "scripts" / "vendor" / "lightweight-charts.standalone.production.js"

PAGINAS_MINIMAS = 15

# Colores y Tokens Institucionales
FONDO_OSCURO = "#060B13"
FONDO_ALTO = "#0A131F"
ACENTO = "#00DC82"
ACENTO_CIAN = "#38BDF8"
ACENTO_DORADO = "#F59E0B"
ACENTO_NARANJA = "#E8783C"
TEXTO_PRINCIPAL = "#1E293B"
TEXTO_CLARO = "#FFFFFF"
TEXTO_MUTED = "#64748B"


def codificar_fuente(ruta: Path) -> str:
    """Retorna data-URI base64 para fuentes woff2."""
    if not ruta.exists():
        return ""
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{datos}"


def caras_de_fuente() -> str:
    """Genera declaraciones @font-face con fuentes locales base64."""
    declaraciones = []
    fuentes_map = [
        ("Plus Jakarta Sans", 400, "normal", FUENTES / "PlusJakartaSans-Regular.woff2"),
        ("Plus Jakarta Sans", 600, "normal", FUENTES / "PlusJakartaSans-SemiBold.woff2"),
        ("Plus Jakarta Sans", 700, "normal", FUENTES / "PlusJakartaSans-Bold.woff2"),
        ("Plus Jakarta Sans", 800, "normal", FUENTES / "PlusJakartaSans-ExtraBold.woff2"),
        ("Goldman", 700, "normal", FUENTES / "Goldman-Bold.woff2"),
        ("Space Grotesk", 600, "normal", FUENTES / "SpaceGrotesk-SemiBold.woff2"),
        ("Space Grotesk", 700, "normal", FUENTES / "SpaceGrotesk-Bold.woff2"),
    ]
    for familia, peso, estilo, ruta in fuentes_map:
        uri = codificar_fuente(ruta)
        if uri:
            declaraciones.append(
                f"@font-face {{ font-family: '{familia}'; font-weight: {peso}; font-style: {estilo}; font-display: block; src: url({uri}) format('woff2'); }}"
            )
    return "\n".join(declaraciones)


def procesar_callouts(html: str) -> str:
    """Transforma blockquotes de GitHub (`> [!TIPO]`) en avisos estructurados."""
    patron = re.compile(
        r"<blockquote>\s*<p>\s*(?:\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?:<br\s*/?>)?\s*)+(.*?)</p>(.*?)</blockquote>",
        re.DOTALL | re.IGNORECASE,
    )

    def reemplazo(m: re.Match[str]) -> str:
        tipo = m.group(1).lower()
        titulo = m.group(2).strip()
        resto = m.group(3).strip()
        titulo = re.sub(r'^(?:<br\s*/?>\s*)+', '', titulo).strip()
        iconos = {
            "note": "ℹ️",
            "tip": "💡",
            "important": "⚡",
            "warning": "⚠️",
            "caution": "🛑",
        }
        icono = iconos.get(tipo, "📌")
        cabecera = f'<div class="aviso-cabecera"><span class="aviso-icono">{icono}</span><span class="aviso-titulo">{titulo}</span></div>'
        contenido = f'<div class="aviso-cuerpo">{resto}</div>' if resto else ""
        return f'<div class="aviso aviso-{tipo}">{cabecera}{contenido}</div>'

    html_transformado = patron.sub(reemplazo, html)
    html_transformado = re.sub(r'\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?:<br\s*/?>)?', '', html_transformado, flags=re.IGNORECASE)
    return html_transformado


def procesar_fichas_activos(html: str) -> str:
    """Maqueta las fichas del Módulo 10 como bloques estructurados."""
    def _reemplazar(m: re.Match[str]) -> str:
        h2 = m.group(1)
        sub = m.group(2)
        tabla = m.group(3)
        return (
            f'<div class="ficha-activo">\n'
            f'{h2}\n'
            f'<div class="ficha-que-mueve">{sub}</div>\n'
            f'{tabla}\n'
            f'</div>'
        )

    patron = re.compile(
        r'(<h2[^>]*>10\.\d[^<]*</h2>)\s*'
        r'(<p><strong>Qu&eacute; lo mueve</strong>:.*?</p>)\s*'
        r'(<table>.*?</table>)',
        re.DOTALL,
    )
    return patron.sub(_reemplazar, html)


def hoja_de_estilos() -> str:
    return f"""
{caras_de_fuente()}

@page {{
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
}}
@page :first {{ margin: 0; }}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
    color: {TEXTO_PRINCIPAL};
    font-size: 9.8pt;
    line-height: 1.5;
    background: #FFFFFF;
    -webkit-font-smoothing: antialiased;
}}

/* ── Portada Midnight Alpha & Multi-Asset ────────────────────────── */
.portada {{
    width: 210mm; height: 297mm;
    background: {FONDO_OSCURO};
    color: #FFFFFF;
    padding: 20mm 18mm;
    display: flex; flex-direction: column; justify-content: space-between;
    break-after: page;
    position: relative; overflow: hidden;
}}
.portada-glow {{
    position: absolute; inset: 0;
    background:
        radial-gradient(circle at 85% 12%, rgba(56, 189, 248, 0.24) 0%, transparent 55%),
        radial-gradient(circle at 15% 45%, rgba(0, 220, 130, 0.18) 0%, transparent 60%),
        radial-gradient(circle at 75% 85%, rgba(245, 158, 11, 0.16) 0%, transparent 50%),
        linear-gradient(145deg, {FONDO_ALTO} 0%, {FONDO_OSCURO} 100%);
    z-index: 0;
}}
.portada-trama {{
    position: absolute; inset: 0;
    background-image:
        linear-gradient(to right, rgba(56, 189, 248, 0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
    background-size: 28px 28px;
    z-index: 1;
}}
.portada > * {{ position: relative; z-index: 2; }}

.cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(56, 189, 248, 0.25);
    padding-bottom: 12px;
}}
.cover-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.cover-logo-icon {{
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, #00DC82 0%, #38BDF8 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: #060B13;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
}}
.cover-logo-text {{
    font-family: 'Goldman', sans-serif;
    font-size: 13pt;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #FFFFFF;
}}
.cover-badge {{
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.40);
    color: #38BDF8;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.14em;
    padding: 4px 14px;
    border-radius: 100px;
    text-transform: uppercase;
}}

.kicker {{
    font-size: 9pt; font-weight: 700; letter-spacing: 0.20em;
    color: #38BDF8; text-transform: uppercase; margin-bottom: 3mm;
}}
.titulo-portada {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 32pt; line-height: 1.08; text-transform: uppercase;
    text-wrap: balance;
    background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #50C0A8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.filete {{
    width: 32mm; height: 3.5px;
    background: linear-gradient(90deg, #00DC82, #38BDF8, #F59E0B);
    margin: 5mm 0 4mm 0;
    border-radius: 2px;
}}
.bajada {{
    font-size: 10.5pt; line-height: 1.55; color: #CBD5E1;
    max-width: 145mm; margin-bottom: 5mm;
}}

/* Hero Card Glassmorphic Multi-Asset */
.hero-card-container {{
    background: rgba(10, 24, 38, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 10px;
    padding: 4mm 5mm;
    margin: 3mm 0 4mm 0;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.40);
}}
.hero-card-header {{
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
    padding-bottom: 2mm; margin-bottom: 3mm;
}}
.hero-card-title {{
    font-family: 'Goldman', sans-serif; font-size: 8.5pt; font-weight: 700;
    letter-spacing: 0.12em; color: #94A3B8; text-transform: uppercase;
}}
.hero-card-badge {{
    font-size: 7.5pt; font-weight: 700; color: #00DC82;
    background: rgba(0, 220, 130, 0.15); border: 1px solid rgba(0, 220, 130, 0.30);
    padding: 2px 8px; border-radius: 4px;
}}
.hero-grid-assets {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
}}
.hero-asset-box {{
    background: rgba(6, 15, 25, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 2.8mm 3mm;
    display: flex; flex-direction: column; gap: 2.5px;
}}
.hero-asset-box.oro {{ border-top: 2.5px solid #F59E0B; }}
.hero-asset-box.wti {{ border-top: 2.5px solid #E8783C; }}
.hero-asset-box.us100 {{ border-top: 2.5px solid #38BDF8; }}
.hero-asset-box.usdclp {{ border-top: 2.5px solid #00DC82; }}

.hero-asset-name {{
    font-family: 'Goldman', sans-serif; font-size: 8.2pt; font-weight: 700; color: #FFFFFF;
}}
.hero-asset-role {{
    font-size: 7.2pt; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em;
}}
.hero-asset-driver {{
    font-size: 7.4pt; color: #E2E8F0; margin-top: 1px; line-height: 1.3;
}}
.hero-asset-driver strong {{
    color: #38BDF8; font-weight: 700;
}}
.hero-asset-label {{
    font-size: 6.8pt; color: #64748B; margin-top: 2px; font-weight: 600;
}}

/* Cajas de Fórmulas y Algoritmos de Cálculo */
.caja-formula {{
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #00DC82;
    border-radius: 6px;
    padding: 3mm 3.8mm;
    margin: 2.8mm 0 3.2mm 0;
    font-size: 8.8pt;
    line-height: 1.45;
    break-inside: avoid;
    page-break-inside: avoid;
}}
.caja-formula-titulo {{
    font-family: 'Goldman', sans-serif;
    font-size: 9.2pt;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 2mm;
    display: flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 1mm;
}}
.caja-formula-paso {{
    margin-bottom: 1.8mm;
}}
.caja-formula-badge {{
    background: #0B1926;
    color: #38BDF8;
    font-family: 'Space Grotesk', monospace;
    font-size: 7.8pt;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    margin-right: 4px;
}}

/* Pastillas de Valor */
.cover-pastillas {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 3mm 0;
}}
.cover-card-glass {{
    background: rgba(10, 24, 38, 0.65);
    border: 1px solid rgba(56, 189, 248, 0.20);
    border-radius: 6px;
    padding: 2.5mm 3.5mm;
    font-size: 8.2pt; line-height: 1.35; color: #E2E8F0;
    backdrop-filter: blur(8px);
}}
.cover-card-glass strong {{
    color: #38BDF8; font-weight: 700; display: block; margin-bottom: 2px; font-size: 8.6pt;
}}

.aviso-portada {{
    background: rgba(10, 24, 38, 0.70);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-left: 3.5px solid #E84040;
    border-radius: 0 6px 6px 0;
    padding: 3mm 4.5mm;
    font-size: 8pt; line-height: 1.45; color: #94A3B8;
}}
.aviso-portada strong {{
    color: #F87171; letter-spacing: 0.06em; font-weight: 700;
}}
.pie-portada {{
    display: flex; justify-content: space-between; align-items: flex-end;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 3.5mm; margin-top: 4mm;
    font-size: 8.2pt; color: #64748B;
}}

/* ── Flujo Editorial Continuo y Equilibrado ──────────────────────── */
main {{
    width: 100%;
}}

main h1 {{
    font-family: 'Goldman', sans-serif; font-weight: 700;
    font-size: 14.5pt; line-height: 1.25; color: #0B1916;
    border-bottom: 2.5px solid {ACENTO};
    padding-bottom: 2mm; margin: 5mm 0 2.5mm 0;
    break-before: auto; break-after: avoid; page-break-after: avoid;
    text-wrap: balance;
}}
main > h1:first-child {{
    margin-top: 0;
}}

main h2 {{
    font-size: 11pt; font-weight: 800; color: #0B1916;
    margin: 4mm 0 1.8mm 0; break-after: avoid; page-break-after: avoid;
    border-left: 3.5px solid {ACENTO}; padding-left: 2.5mm;
}}
main h3 {{
    font-size: 9.8pt; font-weight: 700; color: #1E293B;
    margin: 3mm 0 1.5mm 0; break-after: avoid; page-break-after: avoid;
}}
main h4 {{
    font-size: 9.2pt; font-weight: 700; color: #334155;
    margin: 2.5mm 0 1.2mm 0; break-after: avoid; page-break-after: avoid;
}}

h2 + p, h2 + ul, h2 + ol, h2 + div,
h3 + p, h3 + ul, h3 + ol, h3 + div {{
    break-before: avoid;
    page-break-before: avoid;
}}

p {{ margin: 0 0 1.8mm 0; }}
strong {{ font-weight: 700; color: #0B1916; }}
em {{ font-style: italic; }}
a {{ color: #0F766E; text-decoration: none; }}

ul, ol {{ margin: 0 0 1.8mm 4.5mm; }}
li {{ margin-bottom: 0.9mm; }}
li > ul, li > ol {{ margin-top: 0.9mm; margin-bottom: 0; }}

code {{
    font-family: 'Space Grotesk', Consolas, monospace;
    font-size: 8.5pt; background: #F1F5F9; color: #0F172A;
    padding: 0.3mm 1.2mm; border-radius: 3px; border: 1px solid #E2E8F0;
}}
pre {{
    background: #0B1916; color: #E2E8F0;
    font-family: 'Space Grotesk', Consolas, monospace;
    font-size: 8pt; line-height: 1.45;
    padding: 3mm 4mm; border-radius: 6px;
    margin: 2mm 0 3mm 0; overflow-x: auto;
    break-inside: avoid;
}}

/* Tablas */
table {{
    width: 100%; border-collapse: collapse;
    font-size: 8.4pt; line-height: 1.38;
    margin: 2mm 0 3mm 0;
    break-inside: avoid;
}}
th, td {{
    padding: 1.8mm 2.2mm;
    border: 1px solid #CBD5E1;
    text-align: left; vertical-align: top;
}}
th {{
    background: #F1F5F9; font-weight: 700;
    color: #0F172A; border-bottom: 2px solid {ACENTO};
    font-family: 'Plus Jakarta Sans', sans-serif;
}}
tr:nth-child(even) td {{ background: #FAFAFA; }}

/* Contenedores de Diagramas SVG y Gráficos TradingView */
.contenedor-diagrama {{
    width: 100%;
    margin: 3mm 0 3.5mm 0;
    display: flex;
    justify-content: center;
    break-inside: avoid;
    page-break-inside: avoid;
}}
.contenedor-diagrama svg {{
    max-width: 100%;
    height: auto;
    display: block;
}}

/* Gráficos TradingView Alta Resolución 300 DPI */
.chart-tv {{
    background: #060F19;
    border: 1.5px solid rgba(56, 189, 248, 0.45);
    border-radius: 8px;
    overflow: hidden;
    color: #94A3B8;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45);
    display: block;
    width: 100%;
    margin: 3.5mm 0 4mm 0;
}}
.chart-tv-topbar {{
    height: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 10px;
    background: #0A1926;
    border-bottom: 1px solid rgba(56, 189, 248, 0.22);
    font-family: 'Space Grotesk', monospace;
    font-size: 8.5pt;
    white-space: nowrap;
}}
.chart-tv-topbar-left {{
    display: flex;
    align-items: center;
    gap: 7px;
}}
.chart-tv-symbol {{
    color: #FFFFFF;
    font-family: 'Goldman', sans-serif;
    font-size: 9.5pt;
    font-weight: 700;
    letter-spacing: 0.04em;
}}
.chart-tv-badge-tf {{
    background: rgba(0, 220, 130, 0.18);
    color: #00DC82;
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 700;
    font-size: 8pt;
}}
.chart-tv-badge-feed {{
    background: rgba(56, 189, 248, 0.12);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 7.8pt;
    font-weight: 700;
    letter-spacing: 0.04em;
}}
.chart-tv-ohlc {{
    display: inline-flex;
    gap: 6px;
    font-size: 8pt;
    color: #94A3B8;
    margin-left: 6px;
    font-family: 'Space Grotesk', monospace;
}}
.chart-tv-ohlc strong {{
    color: #E2E8F0;
}}
.chart-tv-ohlc .up {{ color: #00DC82; }}
.chart-tv-ohlc .down {{ color: #EF4444; }}

.chart-tv-brand-tv {{
    display: flex;
    align-items: center;
    gap: 4px;
    color: #94A3B8;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 0.06em;
}}
.chart-tv-legend {{
    height: 22px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 10px;
    background: #081420;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    font-family: 'Space Grotesk', monospace;
    font-size: 8pt;
    white-space: nowrap;
}}
.chart-tv-legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.chart-tv-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}}
.chart-tv-leg-lbl {{
    color: #94A3B8;
}}
.chart-tv-leg-val {{
    font-weight: 700;
}}
.chart-tv-wrapper {{
    position: relative;
    width: 100%;
    background: #060F19;
}}
.chart-tv-canvas {{
    width: 710px;
    height: 215px;
    display: block;
    margin: 0 auto;
}}
#manual-tv-chart a#tv-attr-logo {{
    display: none !important;
}}
#manual-tv-chart table,
#manual-tv-chart tr,
#manual-tv-chart td {{
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
}}
#manual-tv-chart tr td[colspan="3"] {{
    background: rgba(56, 189, 248, 0.25) !important;
}}
.chart-tv-caption {{
    height: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 12px;
    color: #94A3B8;
    background: #0A1926;
    border-top: 1px solid rgba(56, 189, 248, 0.25);
    font-size: 7.8pt;
    font-family: 'Space Grotesk', monospace;
    position: relative;
    z-index: 5;
}}

/* Avisos y Callouts */
.aviso {{
    border-radius: 6px; padding: 2.5mm 3.2mm;
    margin: 2.5mm 0 3.2mm 0; font-size: 8.6pt; line-height: 1.42;
    break-inside: avoid;
}}
.aviso-cabecera {{
    display: flex; align-items: center; gap: 6px;
    font-weight: 700; margin-bottom: 1mm;
}}
.aviso-icono {{ font-size: 10pt; }}
.aviso-titulo {{ font-size: 9pt; }}
.aviso-cuerpo p:last-child {{ margin-bottom: 0; }}

.aviso-note {{ background: #F0FDF4; border: 1px solid #86EFAC; border-left: 4px solid #22C55E; color: #14532D; }}
.aviso-note .aviso-cabecera {{ color: #15803D; }}
.aviso-tip {{ background: #F0F9FF; border: 1px solid #BAE6FD; border-left: 4px solid #0EA5E9; color: #0C4A6E; }}
.aviso-tip .aviso-cabecera {{ color: #0284C7; }}
.aviso-important {{ background: #FEF3C7; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; color: #78350F; }}
.aviso-important .aviso-cabecera {{ color: #B45309; }}
.aviso-warning {{ background: #FFF7ED; border: 1px solid #FED7AA; border-left: 4px solid #F97316; color: #7C2D12; }}
.aviso-warning .aviso-cabecera {{ color: #C2410C; }}
.aviso-caution {{ background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #EF4444; color: #7F1D1D; }}
.aviso-caution .aviso-cabecera {{ color: #B91C1C; }}

/* Fichas Activos Módulo 10 */
.ficha-activo {{
    border: 1px solid #E2E8F0; border-radius: 6px;
    padding: 2.5mm 3mm; margin: 2.5mm 0 3.5mm 0;
    background: #FFFFFF; break-inside: avoid;
}}
.ficha-activo h2 {{
    margin: 0 0 1.2mm 0; border-left: none; padding-left: 0;
    font-size: 10.8pt;
}}
.ficha-que-mueve {{
    font-size: 8.2pt; color: #4A5568; margin-bottom: 1.5mm;
    background: #F8FAFC; padding: 1mm 2mm; border-radius: 4px;
}}
.ficha-activo table {{ margin: 0; font-size: 8pt; }}

hr {{ border: none; border-top: 1px solid #E2E8F0; margin: 3.5mm 0; }}
"""


def construir_portada() -> str:
    """Construye la portada atemporal institucional con el universo multi-activo."""
    return f"""
<div class="portada">
  <div class="portada-glow"></div>
  <div class="portada-trama"></div>
  <div class="cover-top">
    <div class="cover-logo">
      <div class="cover-logo-icon">GI</div>
      <div class="cover-logo-text">GRUPO INTELIGENCIA</div>
    </div>
    <div class="cover-badge">SISTEMA CUANTITATIVO · EDICIÓN PÚBLICA</div>
  </div>
  <div>
    <div class="kicker">DIRECCIÓN DE TRADING · DESK CUANTITATIVO</div>
    <div class="titulo-portada">Manual de<br>Operaciones<br>Intermercado</div>
    <div class="filete"></div>
    <div class="bajada">
      De la macroeconom&iacute;a real a tu plataforma MetaTrader&nbsp;5.
      Aprende a clasificar el clima econ&oacute;mico, validar la microestructura técnica
      y dimensionar el riesgo con precisi&oacute;n matem&aacute;tica de 1&nbsp;hora.
    </div>

    <!-- Hero Card Glassmorphic: Universo Multi-Activo Atemporal -->
    <div class="hero-card-container">
      <div class="hero-card-header">
        <span class="hero-card-title">UNIVERSO DE COBERTURA · SISTEMA MULTI-ACTIVO</span>
        <span class="hero-card-badge">● EJECUCIÓN CUANTITATIVA H1</span>
      </div>
      <div class="hero-grid-assets">
        <div class="hero-asset-box oro">
          <span class="hero-asset-name">ORO · XAU/USD</span>
          <span class="hero-asset-role">Metal Precioso / Reserva</span>
          <span class="hero-asset-driver"><strong>Driver:</strong> Tasa Real TIPS 10Y</span>
          <span class="hero-asset-label">Salida Asim&eacute;trica Trailing</span>
        </div>
        <div class="hero-asset-box wti">
          <span class="hero-asset-name">PETRÓLEO · WTI</span>
          <span class="hero-asset-role">Commodity Energ&eacute;tico</span>
          <span class="hero-asset-driver"><strong>Driver:</strong> Shock Oferta / OPEP</span>
          <span class="hero-asset-label">Co-Riesgo 1% Compartido</span>
        </div>
        <div class="hero-asset-box us100">
          <span class="hero-asset-name">NASDAQ 100</span>
          <span class="hero-asset-role">Renta Variable Tech</span>
          <span class="hero-asset-driver"><strong>Driver:</strong> Tasa Bono US10Y</span>
          <span class="hero-asset-label">Ruptura & Pullback H1</span>
        </div>
        <div class="hero-asset-box usdclp">
          <span class="hero-asset-name">USD/CLP</span>
          <span class="hero-asset-role">Divisa Emergente Latam</span>
          <span class="hero-asset-driver"><strong>Driver:</strong> Cobre COMEX / LME</span>
          <span class="hero-asset-label">Rueda 09:00 - 14:00 CLT</span>
        </div>
      </div>
    </div>

    <!-- Pastillas de Valor Destacadas -->
    <div class="cover-pastillas">
      <div class="cover-card-glass">
        <strong>🌪️ 5 Climas Macro</strong>
        <span>M&aacute;quina R0–R4 con hist&eacute;resis y umbrales maestros SSOT en Anexo A2.</span>
      </div>
      <div class="cover-card-glass">
        <strong>📐 3 Setups H1</strong>
        <span>Matriz Clima &times; Setup: Ruptura Donchian, Retroceso EMA y Rango.</span>
      </div>
      <div class="cover-card-glass">
        <strong>🛡️ 1 % Riesgo Neto</strong>
        <span>Buffer 90/10 para costos, slippage cap y Chandelier Trailing Exit.</span>
      </div>
    </div>
  </div>
  <div>
    <div class="aviso-portada">
      <strong>AVISO DE RIESGO Y TRANSPARENCIA.</strong> Material formativo y educativo. No constituye
      asesor&iacute;a financiera personalizada ni garantiza rentabilidades futuras.
      El trading en contratos por diferencia con apalancamiento conlleva un alto
      riesgo de p&eacute;rdida de capital. Las &oacute;rdenes las ejecutas t&uacute;,
      manualmente, en tu propia plataforma.
    </div>
    <div class="pie-portada">
      <div>Manual Oficial para el Trader Cuantitativo · Edici&oacute;n P&uacute;blica Inicial · Versi&oacute;n 1.0</div>
      <div style="text-align: right;">
        <div style="color:#FFFFFF; font-weight:700;">Septiembre 2026</div>
        <div>Direcci&oacute;n de Trading &amp; Research</div>
      </div>
    </div>
  </div>
</div>
"""


def renderizar_markdown(texto: str) -> str:
    from markdown_it import MarkdownIt

    # Sanitización exhaustiva de remanentes de LaTeX
    texto = texto.replace(r"\text{ATR}", "ATR")
    texto = texto.replace(r"\text{H1}", "H1")
    texto = texto.replace(r"\text{D1}", "D1")
    texto = texto.replace(r"\text{CLP}", "CLP")
    texto = texto.replace(r"\text{bps}", "bps")
    texto = texto.replace(r"\times", "×")
    texto = texto.replace(r"\le", "≤")
    texto = texto.replace(r"\ge", "≥")
    texto = texto.replace(r"\Delta", "Δ")
    texto = texto.replace(r"\checkmark", "✓")
    texto = texto.replace(r"\to", "→")
    texto = texto.replace(r"\mathbf", "")

    # Reemplazo de tokens de artefactos de alta resolución
    texto = texto.replace("<!-- TOKEN_GRAFICO_EJEMPLO_H1 -->", generar_bloque_grafico_tradingview())
    texto = texto.replace("<!-- TOKEN_ALGORITMO_STOP_LOSS -->", svg_algoritmo_stop_loss())
    texto = texto.replace("<!-- TOKEN_COMPROBACION_MARGEN -->", svg_comprobacion_margen())

    # Protección de bloques HTML complejos (SVGs y Gráficos) con tokens alfanuméricos
    bloques_html: dict[str, str] = {}

    def _guardar_bloque(m: re.Match[str]) -> str:
        k = f"HTMLBLOCKTOKENXYZ{len(bloques_html)}END"
        bloques_html[k] = m.group(0)
        return f"\n\n{k}\n\n"

    # 1. Proteger bloques con comentarios de delimitación inequívoca
    texto_protegido = re.sub(
        r'<!-- START_(\w+) -->.*?<!-- END_\1 -->',
        _guardar_bloque,
        texto,
        flags=re.DOTALL
    )

    # 2. Proteger contenedores de diagramas y SVGs restantes
    texto_protegido = re.sub(
        r'<div class="contenedor-diagrama">.*?</div>',
        _guardar_bloque,
        texto_protegido,
        flags=re.DOTALL
    )
    texto_protegido = re.sub(
        r'<svg[^>]*>.*?</svg>',
        _guardar_bloque,
        texto_protegido,
        flags=re.DOTALL
    )

    md = MarkdownIt("commonmark", {"html": True, "breaks": False}).enable("table")
    html_crudo = md.render(texto_protegido)

    # Restaurar bloques HTML intactos
    for k, v in bloques_html.items():
        html_crudo = html_crudo.replace(f"<p>{k}</p>", v)
        html_crudo = html_crudo.replace(k, v)

    html = procesar_callouts(html_crudo)
    return procesar_fichas_activos(html)


def construir_html() -> str:
    if not ORIGEN_MD.exists():
        raise SystemExit(f"No existe el markdown fuente: {ORIGEN_MD}")

    tv_js = VENDOR_TV_JS.read_text(encoding="utf-8") if VENDOR_TV_JS.exists() else ""
    cuerpo = renderizar_markdown(ORIGEN_MD.read_text(encoding="utf-8"))
    return (
        "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<title>Manual de Operaciones · Trading Cuantitativo Intermercado</title>\n"
        f"<script>{tv_js}</script>\n"
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
        pagina = navegador.new_page(
            viewport={"width": 794, "height": 1123},
            device_scale_factor=3
        )
        pagina.set_content(html, wait_until="load")
        try:
            pagina.wait_for_selector('[data-chart-ready="true"]', timeout=8000)
            pagina.wait_for_timeout(400)
        except Exception:
            pass
        pagina.emulate_media(media="print")
        pdf = pagina.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        navegador.close()

    SALIDA_DOCS.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_DOCS.write_bytes(pdf)
    if SALIDA_CENTRAL.parent.exists():
        SALIDA_CENTRAL.write_bytes(pdf)

    paginas = len(PdfReader(SALIDA_DOCS).pages)
    print(f"Salida   : {SALIDA_DOCS.relative_to(RAIZ)}")
    print(f"Tamaño   : {len(pdf) / 1024:.1f} KB")
    print(f"Páginas  : {paginas}")

    if paginas < PAGINAS_MINIMAS:
        raise SystemExit(
            f"El PDF salió con {paginas} páginas y se esperan al menos "
            f"{PAGINAS_MINIMAS}. Un manual al que le faltan secciones se lee como "
            "completo, así que la compilación se detiene."
        )
    print("\n✅ ÉXITO TOTAL: Manual de Operaciones (Edición Pública Inicial v1.0) compilado a 300 DPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(compilar_pdf())
