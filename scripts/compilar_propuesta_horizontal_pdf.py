#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compila la Propuesta Ejecutiva para Gerencia a HTML y PDF Horizontal 16:9 Widescreen (16 Láminas).

Diseño de Gran Formato y Máximo Protagonismo Visual:
- Tipografía de Gran Escala (Títulos 42-46px, Textos 19-22px, Cifras 64-72px).
- Jerarquía Visual de Alto Impacto: Juego dinámico de negritas y colores fiduciarios.
- Secuencia Narrativa Expandida (16 Láminas):
    01. Portada Ejecutiva & Tesis de Conquista.
    02. Resumen Ejecutivo (BLUF) & Los 3 Indicadores Clave.
    03. Evolución del Embudo: De la Exploración a la Alta Intención.
    04. El Producto Estrella: Guía Táctica USD/CLP (Showcase Institucional).
    05. Rigor Cuantitativo Interior: Gráficos TradingView con Feed Grupo Inteligencia y Regla del 1%.
    06. Inteligencia Competitiva: El Vacío que Deja BeFX en el Mercado.
    07. La Trampa Psicológica del "Blur" vs. Autoridad Fiduciaria.
    08. Matriz Estratégica: Modelo Blur (Competencia) vs. Modelo GI (Conquista).
    09. Embudo Nativo Paso 1: Bienvenida Instantánea en 0.1 Segundos.
    10. Embudo Nativo Paso 2: Los 3 Filtros de Calificación (Sin Teclado).
    11. Embudo Nativo Paso 3: Autocompletado y Descarga Inmediata en 1 Clic.
    12. Estrategia de Doble Canal: Descarga Directa + Cortesía en WhatsApp.
    13. La Ecuación Financiera de Meta Ads: CPL = CPC ÷ CVR.
    14. Simulación Econométrica de Cartera (Base $600 USD Mensuales).
    15. Gobernanza Interdepartamental: Delimitación de Roles y Flujo Swimlane.
    16. Decisión Ejecutiva Inmediata: Plan Piloto de 10 Días ($150 USD).

Uso:
    uv run --with playwright --with pypdf --with pymupdf python scripts/compilar_propuesta_horizontal_pdf.py
"""

from __future__ import annotations

import base64
import shutil
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "templates" / "stories" / "fonts"
DIR_ARTEFACTOS = RAIZ / "docs" / "artefactos_visuales"
SALIDA_PDF = RAIZ / "docs" / "PROPUESTA_EJECUTIVA_META_ADS_HORIZONTAL_GI.pdf"
DIR_PREVIEWS = RAIZ / "scratch" / "slides_preview"

URL_BEFX_AD_LIBRARY = (
    "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=CL&q=befx"
)

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


def codificar_imagen_base64(nombre_archivo: str) -> str:
    ruta = DIR_ARTEFACTOS / nombre_archivo
    if not ruta.exists():
        return ""
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{datos}"


def generar_css() -> str:
    fuentes = caras_de_fuente()
    return f"""
{fuentes}

:root {{
    --bg-dark: #04090B;
    --bg-card: rgba(8, 22, 28, 0.92);
    --bg-card-border: rgba(83, 193, 171, 0.38);
    --mint: #53C1AB;
    --mint-glow: rgba(83, 193, 171, 0.5);
    --mint-light: #A7F3D0;
    --blue-accent: #38BDF8;
    --blue-glow: rgba(56, 189, 248, 0.4);
    --danger: #EF4444;
    --danger-bg: rgba(239, 68, 68, 0.16);
    --danger-border: rgba(239, 68, 68, 0.55);
    --warning: #F59E0B;
    --warning-bg: rgba(245, 158, 11, 0.16);
    --warning-border: rgba(245, 158, 11, 0.55);
    --success: #10B981;
    --text-white: #FFFFFF;
    --text-silver: #CBD5E1;
    --text-muted: #94A3B8;
    --font-heading: 'Goldman', sans-serif;
    --font-body: 'Plus Jakarta Sans', sans-serif;
    --font-mono: 'Space Grotesk', monospace;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html, body {{
    width: 100%;
    min-height: 100%;
    margin: 0;
    padding: 0;
    background-color: var(--bg-dark);
    color: var(--text-silver);
    font-family: var(--font-body);
    font-size: clamp(15px, 1.0vw, 19px);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
}}

/* Slide Full-Width 100% Horizontal */
.slide {{
    width: 100vw;
    min-height: 100vh;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
    background: radial-gradient(circle at 85% 15%, rgba(83, 193, 171, 0.14) 0%, transparent 60%),
                radial-gradient(circle at 15% 85%, rgba(56, 189, 248, 0.10) 0%, transparent 60%),
                var(--bg-dark);
    padding: clamp(24px, 3.5vh, 48px) clamp(30px, 4.5vw, 84px);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

/* Header */
.slide-header {{
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid rgba(83, 193, 171, 0.28);
    padding-bottom: clamp(10px, 1.6vh, 18px);
    margin-bottom: clamp(12px, 1.8vh, 22px);
    flex-shrink: 0;
}}

.header-left {{
    width: 100%;
    max-width: none;
    flex: 1;
}}

.brand-tag {{
    font-family: var(--font-mono);
    font-size: clamp(12px, 0.85vw, 15px);
    font-weight: 800;
    letter-spacing: 0.16em;
    color: var(--mint);
    text-transform: uppercase;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.brand-tag::before {{
    content: '';
    display: inline-block;
    width: 9px;
    height: 9px;
    background: var(--mint);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--mint);
}}

.slide-title {{
    font-family: var(--font-heading);
    font-size: clamp(24px, 2.2vw, 42px);
    font-weight: 700;
    color: var(--text-white);
    letter-spacing: 0.01em;
    line-height: 1.18;
    text-shadow: 0 2px 12px rgba(0,0,0,0.6);
}}

.slide-subtitle {{
    font-size: clamp(15px, 1.1vw, 21px);
    color: var(--text-muted);
    margin-top: 4px;
    font-weight: 500;
    line-height: 1.35;
}}

.header-right {{
    text-align: right;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    flex-shrink: 0;
    margin-left: 20px;
}}

.slide-badge {{
    background: rgba(83, 193, 171, 0.16);
    border: 1.5px solid var(--mint);
    color: var(--mint);
    font-family: var(--font-mono);
    font-size: clamp(12px, 0.8vw, 15px);
    font-weight: 800;
    padding: 6px 16px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
}}

.slide-number {{
    font-family: var(--font-mono);
    font-size: clamp(20px, 1.5vw, 28px);
    font-weight: 800;
    color: rgba(255, 255, 255, 0.45);
}}

/* Body */
.slide-body {{
    width: 100%;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: clamp(14px, 2.2vh, 26px);
    min-height: 0;
}}

/* Footer */
.slide-footer {{
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: clamp(10px, 1.4vh, 16px);
    margin-top: clamp(10px, 1.4vh, 16px);
    font-family: var(--font-mono);
    font-size: clamp(12px, 0.85vw, 14px);
    color: var(--text-muted);
    letter-spacing: 0.06em;
    flex-shrink: 0;
}}

/* Grid Layouts Full-Width */
.grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: clamp(20px, 2.5vw, 48px);
    align-items: center;
    width: 100%;
}}

.grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: clamp(16px, 1.8vw, 32px);
    width: 100%;
}}

.grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: clamp(12px, 1.4vw, 24px);
    width: 100%;
}}

.grid-kpi {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: clamp(16px, 1.8vw, 32px);
    width: 100%;
}}

/* Cards & Glassmorphism */
.card {{
    background: var(--bg-card);
    border: 1.5px solid var(--bg-card-border);
    border-radius: 16px;
    padding: clamp(18px, 2.2vh, 32px) clamp(22px, 2vw, 36px);
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(14px);
    position: relative;
}}

.card-success {{
    border-color: rgba(16, 185, 129, 0.45);
    background: linear-gradient(135deg, rgba(8, 30, 24, 0.92) 0%, rgba(8, 22, 28, 0.95) 100%);
}}

.card-danger {{
    border-color: var(--danger-border);
    background: linear-gradient(135deg, var(--danger-bg) 0%, rgba(22, 10, 14, 0.95) 100%);
}}

.card-warning {{
    border-color: var(--warning-border);
    background: linear-gradient(135deg, var(--warning-bg) 0%, rgba(24, 18, 10, 0.95) 100%);
}}

/* Callouts & Big Text */
.callout-box {{
    background: rgba(12, 32, 40, 0.95);
    border-left: 7px solid var(--mint);
    border-radius: 0 14px 14px 0;
    padding: clamp(16px, 2vh, 26px) clamp(22px, 2vw, 36px);
    font-size: clamp(16px, 1.15vw, 22px);
    color: #F8FAFC;
    line-height: 1.55;
    box-shadow: 0 10px 28px rgba(0,0,0,0.45);
    width: 100%;
}}

.callout-box.danger {{
    border-left-color: var(--danger);
    background: rgba(32, 12, 16, 0.95);
}}

.callout-box.warning {{
    border-left-color: var(--warning);
    background: rgba(34, 24, 10, 0.95);
}}

/* KPI Cards */
.kpi-card {{
    background: rgba(10, 28, 36, 0.92);
    border: 1.5px solid rgba(83, 193, 171, 0.4);
    border-radius: 14px;
    padding: clamp(20px, 2.5vh, 32px) clamp(18px, 1.8vw, 28px);
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 12px 30px rgba(0,0,0,0.4);
}}

.kpi-num {{
    font-family: var(--font-heading);
    font-size: clamp(38px, 3.4vw, 68px);
    font-weight: 700;
    color: var(--mint);
    line-height: 1.05;
    margin-bottom: 10px;
    text-shadow: 0 0 24px var(--mint-glow);
}}

.kpi-num.danger {{
    color: #F87171;
    text-shadow: 0 0 24px rgba(248, 113, 113, 0.45);
}}

.kpi-num.accent {{
    color: var(--blue-accent);
    text-shadow: 0 0 24px var(--blue-glow);
}}

.kpi-label {{
    font-family: var(--font-mono);
    font-size: clamp(13px, 0.9vw, 16px);
    font-weight: 800;
    text-transform: uppercase;
    color: var(--text-white);
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}}

.kpi-desc {{
    font-size: clamp(14px, 0.95vw, 17px);
    color: var(--text-silver);
    line-height: 1.45;
}}

/* Interactive Buttons */
.btn-interactive {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: linear-gradient(135deg, #53C1AB 0%, #38BDF8 100%);
    color: #04090B;
    font-family: var(--font-mono);
    font-size: clamp(14px, 0.95vw, 18px);
    font-weight: 800;
    padding: clamp(12px, 1.5vh, 18px) clamp(22px, 1.8vw, 34px);
    border-radius: 9px;
    text-decoration: none;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    box-shadow: 0 8px 24px rgba(83, 193, 171, 0.45);
    cursor: pointer;
    border: none;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.btn-interactive:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(83, 193, 171, 0.65);
}}

.btn-interactive.warning {{
    background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%);
    color: #FFFFFF;
    box-shadow: 0 8px 24px rgba(245, 158, 11, 0.45);
}}

.btn-interactive.warning:hover {{
    box-shadow: 0 12px 30px rgba(245, 158, 11, 0.65);
}}

.btn-interactive.download {{
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #FFFFFF;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.45);
}}

.btn-interactive.download:hover {{
    box-shadow: 0 12px 30px rgba(16, 185, 129, 0.65);
}}

/* Responsive Images inside Slides */
.slide img {{
    max-height: clamp(280px, 46vh, 520px);
    width: auto;
    max-width: 100%;
    object-fit: contain;
}}

/* Tables Full-Width */
.table-custom {{
    width: 100%;
    border-collapse: collapse;
    font-size: clamp(15px, 1.0vw, 19px);
}}

.table-custom th {{
    background: rgba(14, 38, 48, 0.95);
    color: var(--mint);
    font-family: var(--font-mono);
    font-size: clamp(13px, 0.9vw, 17px);
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-align: left;
    padding: clamp(12px, 1.4vh, 18px) clamp(16px, 1.4vw, 24px);
    border-bottom: 2px solid rgba(83, 193, 171, 0.4);
}}

.table-custom td {{
    padding: clamp(12px, 1.4vh, 18px) clamp(16px, 1.4vw, 24px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--text-white);
    line-height: 1.45;
}}

.table-custom tr:nth-child(even) td {{
    background: rgba(255, 255, 255, 0.025);
}}

/* Dense Table for multi-row data */
.table-dense th {{
    padding: clamp(8px, 1.1vh, 12px) clamp(12px, 1.2vw, 18px);
    font-size: clamp(12px, 0.85vw, 15px);
}}

.table-dense td {{
    padding: clamp(7px, 1vh, 11px) clamp(12px, 1.2vw, 18px);
    font-size: clamp(13px, 0.9vw, 16px);
    line-height: 1.35;
}}

/* Tag Pills */
.tag-pill {{
    display: inline-block;
    padding: 7px 16px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: clamp(12px, 0.8vw, 14px);
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
}}

.tag-danger {{
    background: rgba(239, 68, 68, 0.28);
    color: #FCA5A5;
    border: 1px solid rgba(239, 68, 68, 0.55);
}}

.tag-success {{
    background: rgba(16, 185, 129, 0.28);
    color: #6EE7B7;
    border: 1px solid rgba(16, 185, 129, 0.55);
}}

.tag-warning {{
    background: rgba(245, 158, 11, 0.28);
    color: #FDE047;
    border: 1px solid rgba(245, 158, 11, 0.55);
}}

.tag-accent {{
    background: rgba(56, 189, 248, 0.28);
    color: #BAE6FD;
    border: 1px solid rgba(56, 189, 248, 0.55);
}}

/* Presentation Deck HUD & Progress */
#progress-bar {{
    position: fixed;
    top: 0;
    left: 0;
    height: 5px;
    background: linear-gradient(90deg, #53C1AB, #38BDF8);
    z-index: 9999;
    transition: width 0.25s ease;
    box-shadow: 0 0 12px rgba(83, 193, 171, 0.7);
}}

#deck-hud {{
    position: fixed;
    bottom: 24px;
    right: 28px;
    z-index: 9990;
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(8, 22, 28, 0.94);
    border: 1.5px solid rgba(83, 193, 171, 0.45);
    border-radius: 40px;
    padding: 8px 18px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(16px);
    user-select: none;
    font-family: var(--font-mono);
}}

.hud-btn {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
    padding: 8px 14px;
    border-radius: 20px;
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.hud-btn:hover {{
    background: var(--mint);
    color: #04090B;
    border-color: var(--mint);
    box-shadow: 0 0 14px var(--mint-glow);
}}

.hud-select {{
    background: rgba(4, 9, 11, 0.95);
    color: var(--mint);
    border: 1px solid rgba(83, 193, 171, 0.4);
    border-radius: 12px;
    padding: 7px 12px;
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    outline: none;
    max-width: 260px;
}}

.hud-counter {{
    font-size: 14px;
    font-weight: 800;
    color: var(--mint);
    padding: 0 6px;
    white-space: nowrap;
}}

/* Presentation Mode (Slide-by-Slide) vs Scroll Mode */
body.mode-deck {{
    overflow: hidden;
    height: 100vh;
}}

body.mode-deck .slide {{
    display: none;
    height: 100vh;
    max-height: 100vh;
}}

body.mode-deck .slide.active {{
    display: flex;
    animation: fadeInSlide 0.22s ease-out;
}}

@keyframes fadeInSlide {{
    from {{ opacity: 0.6; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
"""


# ==============================================================================
# LÁMINAS EXPANDIDAS CON MAYOR PROTAGONISMO VISUAL (16 SLIDES)
# ==============================================================================


def construir_slide_01() -> str:
    """Lámina 01 / 16: Portada Ejecutiva & Alianza Estratégica."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">GRUPO INTELIGENCIA SpA · ALIANZA ESTRATÉGICA POST VENTA &amp; MARKETING</div>
            <div class="slide-title">SISTEMA DE CAPTACIÓN CALIFICADA EN META ADS</div>
            <div class="slide-subtitle">Maximizando el Retorno Publicitario y Conquistando Mercado vía Guías Educativas Institucionales</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">PROPUESTA ESTRATÉGICA</div>
            <div class="slide-number">01 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <!-- Hero Box -->
        <div class="card card-success" style="padding: 40px 48px; border-left: 8px solid var(--mint);">
            <div style="font-family: var(--font-mono); font-size: 16px; font-weight: 800; color: var(--mint); letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 12px;">
                TESIS EJECUTIVA DE CRECIMIENTO · SEPTIEMBRE 2026
            </div>
            <h2 style="font-family: var(--font-heading); font-size: 38px; color: #FFFFFF; line-height: 1.25; margin-bottom: 20px;">
                Desbloqueando el Máximo Potencial de Pauta: De <span style="color: #F87171;">$14.20 USD</span> a <span style="color: var(--mint); text-shadow: 0 0 20px var(--mint-glow);">$0.78 USD</span> por Lead
            </h2>
            <p style="font-size: clamp(17px, 1.15vw, 22px); color: #E2E8F0; line-height: 1.6;">
                Propuesta de valor conjunta para <strong>Gerencia General, Marketing y Dirección Comercial</strong>. 
                Al dotar a las campañas de un activo institucional de alto impacto —la 
                <strong style="color: #FFFFFF;">Guía Táctica USD/CLP 100% terminada bajo Brandkit</strong>— combinado con un formulario nativo de 1-toque en celulares, 
                Grupo Inteligencia puede capturar <strong style="color: var(--mint);">hasta 9.1x más prospectos calificados</strong>, desbloquear más de un 
                <strong style="color: #6EE7B7;">80% de eficiencia publicitaria</strong> y arrebatar cuota de mercado a competidores que recurren a la censura (*blur*).
            </p>
        </div>

        <!-- 3 Pilares Resumen -->
        <div class="grid-3" style="gap: 28px;">
            <div class="card" style="padding: 24px 28px; border-top: 4px solid var(--mint);">
                <span class="tag-pill tag-success" style="margin-bottom: 10px;">1. ACTIVO LLAVE EN MANO</span>
                <h4 style="font-family: var(--font-heading); font-size: 22px; color: #FFFFFF; margin-bottom: 8px;">Guía USD/CLP Lista</h4>
                <p style="font-size: 18px; color: var(--text-silver); line-height: 1.5;">
                    10 páginas maquetadas a 300 DPI con gráficos TradingView y feed institucional Grupo Inteligencia. Post Venta absorbe el desarrollo al 100%.
                </p>
            </div>

            <div class="card" style="padding: 24px 28px; border-top: 4px solid var(--blue-accent);">
                <span class="tag-pill tag-accent" style="margin-bottom: 10px;">2. CERO FRICCIÓN MÓVIL</span>
                <h4 style="font-family: var(--font-heading); font-size: 22px; color: #FFFFFF; margin-bottom: 8px;">Formulario de 1-Toque</h4>
                <p style="font-size: 18px; color: var(--text-silver); line-height: 1.5;">
                    Carga en 0.1s dentro de Meta. 3 toques de calificación y autollenado nativo que disparan la conversión móvil.
                </p>
            </div>

            <div class="card" style="padding: 24px 28px; border-top: 4px solid #FDE047;">
                <span class="tag-pill tag-warning" style="margin-bottom: 10px;">3. ALIANZA &amp; ENABLEMENT</span>
                <h4 style="font-family: var(--font-heading); font-size: 22px; color: #FFFFFF; margin-bottom: 8px;">Marketing + Ventas</h4>
                <p style="font-size: 18px; color: var(--text-silver); line-height: 1.5;">
                    Marketing lidera la pauta y algoritmo; Post Venta y Comercial entregan el activo en WhatsApp y conducen las Mesas.
                </p>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>GRUPO INTELIGENCIA SpA · SANTIAGO DE CHILE</span>
        <span>DOCUMENTO CONFIDENCIAL PARA GERENCIA GENERAL, MARKETING Y DIRECCIÓN COMERCIAL</span>
    </div>
</div>
"""


def construir_slide_02() -> str:
    """Lámina 02 / 16: Resumen Ejecutivo (BLUF) & Los 3 Indicadores Clave."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">RESUMEN EJECUTIVO · BOTTOM LINE UP FRONT (BLUF)</div>
            <div class="slide-title">LA OPORTUNIDAD MÓVIL: DESBLOQUEANDO HASTA 82% DE EFICIENCIA</div>
            <div class="slide-subtitle">Cómo la Sinergia entre Contenido Técnico y Experiencia Móvil de 1-Toque Multiplica los Resultados de Pauta</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">SÍNTESIS EJECUTIVA</div>
            <div class="slide-number">02 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="callout-box" style="padding: 28px 36px;">
            <strong style="color: var(--mint); font-family: var(--font-heading); font-size: 24px; display: block; margin-bottom: 8px;">
                BOTTOM LINE UP FRONT (BLUF) · IMPACTO DIRECTO EN RESULTADOS:
            </strong>
            En la pauta digital móvil, los formularios con preguntas abiertas retienen involuntariamente hasta un <strong style="color: #F87171;">82% del potencial de conversión</strong> 
            debido a la fricción de escribir en teclados táctiles. Al mismo tiempo, competidores como BeFX atraen volumen pero deterioran la confianza al entregar 
            <strong style="color: #FDE047;">guías censuradas con filtro borroso (*blur*)</strong>. 
            Grupo Inteligencia tiene la oportunidad inmediata de liderar el mercado: dotando a Marketing de la 
            <strong style="color: #FFFFFF;">Guía Táctica USD/CLP 100% Completa</strong> y un flujo de 1-toque, 
            proyectamos escalar la captación a <strong style="color: var(--mint);">9.1x más prospectos calificados con un CPL de $0.78 – $1.65 USD</strong>.
        </div>

        <div class="grid-kpi">
            <div class="kpi-card" style="border-top: 5px solid var(--mint);">
                <div class="kpi-num" style="color: var(--mint); text-shadow: 0 0 20px var(--mint-glow);">+82%</div>
                <div class="kpi-label" style="color: var(--mint-light);">Potencial de Optimización UX</div>
                <div class="kpi-desc">
                    Margen de eficiencia que se desbloquea al sustituir campos de texto libre por opciones de toque rápido en pantalla.
                </div>
            </div>

            <div class="kpi-card" style="border-top: 5px solid var(--blue-accent);">
                <div class="kpi-num accent">9.1x</div>
                <div class="kpi-label" style="color: #BAE6FD;">Multiplicador de Conversión</div>
                <div class="kpi-desc">
                    El formulario de 1-toque eleva la conversión técnica de 11% a <strong>más del 38% en celulares</strong> (de 84 a 766 prospectos).
                </div>
            </div>

            <div class="kpi-card" style="border-top: 5px solid #10B981;">
                <div class="kpi-num" style="color: #6EE7B7;">$0.78 - $1.65</div>
                <div class="kpi-label" style="color: #A7F3D0;">CPL Calificado Proyectado</div>
                <div class="kpi-desc">
                    <strong>Ahorro superior al 80% en costo por lead</strong>, entregando a Ventas prospectos segmentados por activo, nivel y capital.
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>AUDITORÍA METODOLÓGICA DE BENCHMARKS META ADS Y ESTUDIOS DE USABILIDAD MÓVIL (NIELSEN NORMAN GROUP)</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_03() -> str:
    """Lámina 03 / 16: Evolución del Embudo: De la Exploración a la Alta Intención."""
    img_anuncio_gi = codificar_imagen_base64("evidencia_anuncio_gi.png")
    img_form_gi = codificar_imagen_base64("evidencia_formulario_gi.png")
    return f"""
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">ANÁLISIS DE RENDIMIENTO &amp; OPORTUNIDAD DE ESCALA · META ADS</div>
            <div class="slide-title">EVOLUCIÓN DEL EMBUDO: DE LA EXPLORACIÓN A LA ALTA INTENCIÓN</div>
            <div class="slide-subtitle">Capitalizando el Aprendizaje de Campañas Anteriores para Desplegar Captación Técnica de Nicho</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">OPTIMIZACIÓN ESTRATÉGICA</div>
            <div class="slide-number">03 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="gap: 48px;">
            <!-- Capturas Reales de GI con encuadre positivo -->
            <div style="display: flex; gap: 20px; justify-content: center; align-items: center; background: rgba(0,0,0,0.65); padding: 22px; border-radius: 18px; border: 2px solid rgba(56, 189, 248, 0.45); box-shadow: 0 16px 40px rgba(0,0,0,0.7);">
                <div style="text-align: center; flex: 1;">
                    <span class="tag-pill tag-accent" style="margin-bottom: 10px;">FASE 1: TEST DE AWARENESS</span>
                    <img src="{img_anuncio_gi}" alt="Campaña Exploratoria Starbucks" style="max-height: 420px; width: auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);">
                </div>
                <div style="text-align: center; flex: 1;">
                    <span class="tag-pill tag-warning" style="margin-bottom: 10px;">OPORTUNIDAD DE OPTIMIZACIÓN UX</span>
                    <img src="{img_form_gi}" alt="Formulario con pregunta abierta" style="max-height: 420px; width: auto; border-radius: 8px; border: 1.5px solid var(--warning);">
                </div>
            </div>

            <!-- Diagnóstico Constructivo -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="card" style="padding: 26px 30px; border-left: 6px solid var(--blue-accent);">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 10px;">
                        1. El Valor del Test de Exploración (Awareness Inicial)
                    </h4>
                    <p style="font-size: 19px; color: var(--text-silver); line-height: 1.55;">
                        La campaña de Starbucks cumplió exitosamente su función de exploración: validó que existe interés masivo por alternativas de inversión global. 
                        Para la siguiente fase de maduración, el paso natural es alinear el botón y la promesa hacia una <strong style="color: var(--mint);">recompensa técnica tangible e inmediata</strong>, 
                        elevando el CTR al ofrecer un activo educativo formal de alto impacto.
                    </p>
                </div>

                <div class="card" style="padding: 26px 30px; border-left: 6px solid var(--mint);">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 10px;">
                        2. La Transición hacia Cero Fricción Móvil (Mobile UX)
                    </h4>
                    <p style="font-size: 19px; color: var(--text-silver); line-height: 1.55;">
                        En smartphones, pedir redactar respuestas abiertas genera abandono natural por la incomodidad del teclado táctil. 
                        Al evolucionar hacia <strong style="color: #FFFFFF;">botones de opción múltiple de 1-toque</strong>, facilitamos la experiencia del usuario, 
                        multiplicamos la tasa de finalización del formulario (&gt;38%) y capturamos datos pre-segmentados limpios para Ventas.
                    </p>
                </div>

                <div class="callout-box" style="padding: 18px 26px; font-size: 19px;">
                    <strong style="color: var(--mint);">Siguiente Salto de Escala:</strong> Dotar a Marketing de la Guía USD/CLP permite al algoritmo de Meta optimizar la subasta hacia audiencias financieras de alta intención patrimonial, reduciendo el CPL a su mínimo histórico.
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>AUDITORÍA COMPARATIVA DE CONVERSIÓN MÓVIL Y APRENDIZAJE DE CAMPAÑA</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_04() -> str:
    """Lámina 04 / 16: El Producto Estrella: Guía Táctica USD/CLP (Showcase Institucional)."""
    img_portada = codificar_imagen_base64("guia_gi_portada.png")
    return f"""
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">MUNICIÓN TÉCNICA INSTITUCIONAL · MATERIAL EDUCATIVO TERMINADO</div>
            <div class="slide-title">GUÍA TÁCTICA USD/CLP: COBRE, FED Y TASAS (10 PÁGINAS)</div>
            <div class="slide-subtitle">Un Activo 'Llave en Mano' Producido por Post Venta para que Marketing Escale la Pauta Institucional</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">ACTIVO LLAVE EN MANO</div>
            <div class="slide-number">04 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 50px;">
            <!-- Portada de la Guía a Gran Escala -->
            <div style="display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.65); padding: 22px; border-radius: 20px; border: 2.5px solid rgba(83, 193, 171, 0.45); box-shadow: 0 20px 50px rgba(0,0,0,0.8);">
                <img src="{img_portada}" alt="Portada Guía USD/CLP Grupo Inteligencia" style="max-height: 520px; width: auto; border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.9);">
            </div>

            <!-- Ficha Técnica y Pilares del Producto -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="tag-pill tag-success" style="font-size: 16px; padding: 9px 20px;">ACTIVO 100% TERMINADO POR POST VENTA</span>
                    <span style="font-family: var(--font-mono); font-size: 16px; font-weight: 800; color: var(--mint);">ESTÁNDAR DARK EMERALD GLASS</span>
                </div>

                <div class="card card-success" style="padding: 28px 32px;">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 14px;">
                        Los 3 Pilares de Autoridad Fiduciaria:
                    </h4>
                    <ul style="font-size: 19px; color: var(--text-silver); line-height: 1.6; padding-left: 24px; display: flex; flex-direction: column; gap: 14px;">
                        <li>
                            <strong style="color: #FFFFFF;">1. Gráficos Profesionales TradingView (Regla 2):</strong> Gráficos reales H1 renderizados con motor TradingView alimentado con el feed institucional de Grupo Inteligencia, con exactamente 60 velas, niveles matemáticos y cotizaciones reales. Prohibición total de IA generativa (Regla 0).
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">2. Pedagogía en 3 Capas:</strong> 1) El Hecho Técnico (Cobre/Dólar y Fed/BCCh), 2) El Impacto Ciudadano (&lt;30s en economía real), y 3) Gestión de Riesgo Estricta (Regla del 1%).
                        </li>
                        <li>
                            <strong style="color: #6EE7B7;">3. Cero Censura Interna (Regla Anti-Blur):</strong> Se entrega íntegra desde la página 1 a la 10. La confianza se gana cumpliendo la promesa publicitaria al 100%.
                        </li>
                    </ul>
                </div>

                <div style="background: rgba(12, 32, 40, 0.95); border: 2px solid var(--mint); border-radius: 12px; padding: 18px 26px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-family: var(--font-heading); font-size: 19px; color: var(--mint);">ACTIVO TERMINADO A 300 DPI:</div>
                        <div style="font-size: 16px; color: #CBD5E1;">Listo para que Marketing lo implemente de inmediato.</div>
                    </div>
                    <a href="GUIA_TACTICA_USDCLP_COBRE_FED_GI.pdf" class="btn-interactive download" target="_blank">
                        Abrir Guía Táctica GI en PDF ↗
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>PRODUCCIÓN OFICIAL DE POST VENTA Y ANÁLISIS CUANTITATIVO</span>
        <span>GRUPO INTELIGENCIA SpA · SANTIAGO DE CHILE</span>
    </div>
</div>
"""


def construir_slide_05() -> str:
    """Lámina 05 / 16: Rigor Cuantitativo Interior: Gráficos TradingView con Feed Grupo Inteligencia y Regla del 1%."""
    img_pag4 = codificar_imagen_base64("guia_gi_pagina_4.png")
    img_pag5 = codificar_imagen_base64("guia_gi_pagina_5.png")
    return f"""
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">DENSIDAD TÉCNICA &amp; GESTIÓN DE RIESGO · PÁGINAS INTERIORES</div>
            <div class="slide-title">EVIDENCIA INTERIOR: CORRELACIÓN COBRE/FED Y GRÁFICO TRADINGVIEW</div>
            <div class="slide-subtitle">Contenido Cuantitativo Real: Blindaje de Cartera, Reducción de Churn y Multiplicación del LTV</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">ANATOMÍA DEL PRODUCTO</div>
            <div class="slide-number">05 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 40px;">
            <!-- Muestras de Páginas Interiores a Gran Tamaño -->
            <div style="display: flex; gap: 20px; justify-content: center; align-items: center; background: rgba(0,0,0,0.55); padding: 22px; border-radius: 18px; border: 2px solid rgba(83,193,171,0.35); box-shadow: 0 16px 40px rgba(0,0,0,0.7);">
                <img src="{img_pag4}" alt="Página 4 Guía GI - Correlación Cobre / Fed" style="max-height: 500px; width: auto; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.18);">
                <img src="{img_pag5}" alt="Página 5 Guía GI - Lectura Técnica H1 en TradingView con Feed Grupo Inteligencia" style="max-height: 500px; width: auto; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.18);">
            </div>

            <!-- Explicación de Retención y Valor de Cartera -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="card" style="padding: 28px 32px;">
                    <div style="font-family: var(--font-mono); font-size: 14px; color: var(--mint); font-weight: 800; text-transform: uppercase; margin-bottom: 8px;">
                        IMPACTO EN LA ECONOMÍA DE LA CARTERA:
                    </div>
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 14px;">
                        Por qué la Educación Técnica Abarata el CAC y Alarga el LTV
                    </h4>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.6; padding-left: 24px; display: flex; flex-direction: column; gap: 12px;">
                        <li>
                            <strong style="color: #FFFFFF;">1. Blindaje contra Quemado de Cuentas:</strong> Un cliente que opera con la <strong>Regla del 1% de riesgo</strong> y el checklist de 30 segundos no liquida su margen en el primer mes. Su ciclo de vida transaccional pasa de semanas a años.
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">2. Filtro Automático de Calidad:</strong> Quien lee y aprecia este rigor técnico tiene real interés en operar con disciplina y capital patrimonial, filtrando curiosos de ticket bajo.
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">3. Soporte Post Venta de Alta Eficiencia:</strong> Menos fricción y consultas básicas; el cliente comprende la correlación macro antes de ingresar a la plataforma.
                        </li>
                    </ul>
                </div>

                <div style="background: rgba(12, 32, 40, 0.95); border: 2px solid var(--mint); border-radius: 12px; padding: 18px 26px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-family: var(--font-heading); font-size: 19px; color: var(--mint);">AUDITORÍA COMPLETA DEL PDF:</div>
                        <div style="font-size: 15px; color: #CBD5E1;">Revisa las 10 páginas completas maquetadas a 300 DPI.</div>
                    </div>
                    <a href="GUIA_TACTICA_USDCLP_COBRE_FED_GI.pdf" class="btn-interactive download" target="_blank">
                        Abrir Guía GI Completa ↗
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>PÁGINAS INTERIORES AUDITADAS SEGÚN MANUAL DE GOBERNANZA DE GUÍAS EDUCATIVAS</span>
        <span>GRUPO INTELIGENCIA SpA · SANTIAGO DE CHILE</span>
    </div>
</div>
"""


def construir_slide_06() -> str:
    """Lámina 06 / 16: Inteligencia Competitiva: El Vacío que Deja BeFX en el Mercado."""
    img_anuncio_befx = codificar_imagen_base64("evidencia_anuncio_befx.png")
    img_blur_befx = codificar_imagen_base64("befx_pagina_4_blur.png")
    return f"""
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">BENCHMARK COMPETITIVO DE MERCADO · META ADS CHILE</div>
            <div class="slide-title">LA OPORTUNIDAD: EL VACÍO QUE DEJA BeFX CON SU "BLUR"</div>
            <div class="slide-subtitle">Captan Volumen con "Guía USD/CLP" pero Destruyen la Confianza Bloqueando el Contenido</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">INTELIGENCIA COMPETITIVA</div>
            <div class="slide-number">06 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 40px;">
            <!-- Evidencia de BeFX: Anuncio + PDF Blur -->
            <div style="display: flex; gap: 18px; justify-content: center; align-items: center; background: rgba(0,0,0,0.65); padding: 20px; border-radius: 18px; border: 2px solid var(--warning-border); box-shadow: 0 16px 40px rgba(0,0,0,0.7);">
                <div style="text-align: center; flex: 1;">
                    <span class="tag-pill tag-warning" style="margin-bottom: 10px;">ANUNCIO EN META ADS</span>
                    <img src="{img_anuncio_befx}" alt="Anuncio BeFX en Meta" style="max-height: 440px; width: auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);">
                </div>
                <div style="text-align: center; flex: 1;">
                    <span class="tag-pill tag-danger" style="margin-bottom: 10px;">PDF CENSURADO (BLUR PÁG 4)</span>
                    <img src="{img_blur_befx}" alt="Página 4 con Blur de BeFX" style="max-height: 440px; width: auto; border-radius: 8px; border: 2px solid var(--danger);">
                </div>
            </div>

            <!-- Diagnóstico de Oportunidad -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="card card-warning" style="padding: 28px 32px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-family: var(--font-mono); font-size: 14px; color: #FDE047; font-weight: 800; text-transform: uppercase;">HALLAZGO FORENSE DE MERCADO:</span>
                        <span class="tag-pill tag-warning">PAUTA ACTIVA EN CHILE</span>
                    </div>
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 12px;">
                        El Candado Oculto de la Competencia
                    </h4>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.6; padding-left: 22px; display: flex; flex-direction: column; gap: 12px;">
                        <li>
                            <strong style="color: #FFFFFF;">El Gancho Correcto:</strong> BeFX demuestra que el activo publicitario <em>"Guía para invertir en USD/CLP"</em> atrae masivamente a la audiencia chilena.
                        </li>
                        <li>
                            <strong style="color: #FDE047;">La Falla Crítica (Blur):</strong> En el archivo entregado, tras 3 páginas básicas, <strong style="color: #F87171;">las páginas 4 a 10 están censuradas con filtro borroso</strong> exigiendo crear cuenta real.
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">La Oportunidad de Grupo Inteligencia:</strong> Capturar la misma intención de mercado pero fidelizarla con un producto 100% completo, ganando la batalla por la confianza.
                        </li>
                    </ul>
                </div>

                <div style="display: flex; gap: 16px;">
                    <a href="{URL_BEFX_AD_LIBRARY}" class="btn-interactive warning" style="flex: 1; justify-content: center; font-size: 16px; padding: 14px;" target="_blank">
                        Ver Anuncios BeFX en Meta ↗
                    </a>
                    <a href="PDF_guia_USD_CLP_BLUR_BEFX.pdf" class="btn-interactive warning" style="flex: 1; justify-content: center; font-size: 16px; padding: 14px;" target="_blank">
                        Abrir PDF Censurado (Blur) ↗
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>AUDITORÍA COMPARATIVA DE CAMPAÑAS FINANCIERAS ACTIVAS EN CHILE</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_07() -> str:
    """Lámina 07 / 16: La Trampa Psicológica del "Blur" vs. Autoridad Fiduciaria."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">PSICOLOGÍA DEL CONSUMIDOR FINANCIERO · CIENCIA DE LA CONVERSIÓN</div>
            <div class="slide-title">LA TRAMPA DEL "BLUR": REACTANCIA VS. AUTORIDAD FIDUCIARIA</div>
            <div class="slide-subtitle">Por Qué Bloquear Contenido Destruye la Venta y Cómo la Transparencia Genera Cierre Comercial</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">FUNDAMENTO CIENTÍFICO</div>
            <div class="slide-number">07 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="gap: 36px; align-items: stretch;">
            <!-- El Modelo Trampa de la Competencia -->
            <div class="card card-danger" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="tag-pill tag-danger">MODELO COMPETENCIA (BEFX BLUR)</span>
                        <span style="font-family: var(--font-mono); font-size: 14px; color: #FCA5A5; font-weight: 700;">BREHM (1966)</span>
                    </div>
                    <h3 style="font-family: var(--font-heading); font-size: 26px; color: #FFFFFF; margin-bottom: 14px;">
                        Teoría de la Reactancia Psicológica
                    </h3>
                    <p style="font-size: 19px; color: #FEE2E2; line-height: 1.6; margin-bottom: 16px;">
                        Cuando a una persona se le promete una guía gratis y luego se le <strong>bloquea el 70% del documento</strong> exigiendo abrir cuenta, 
                        el cerebro humano reacciona con una alarma de amenaza:
                    </p>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.55; padding-left: 20px; display: flex; flex-direction: column; gap: 10px;">
                        <li><strong>Sensación de Trampa:</strong> El prospecto siente que fue engañado para sacarle sus datos.</li>
                        <li><strong>Rechazo a la Llamada:</strong> Contactabilidad comercial <strong style="color: #F87171;">inferior al 18%</strong>; no contestan o cortan con molestia.</li>
                        <li><strong>Perfil Degradado:</strong> Quien acepta el candado suele ser un curioso sin capital con alta propensión a quemar la cuenta.</li>
                    </ul>
                </div>
                <div style="background: rgba(0,0,0,0.5); padding: 14px; border-radius: 8px; margin-top: 18px; border: 1px solid rgba(239,68,68,0.3); text-align: center; font-size: 16px; color: #FCA5A5; font-weight: 700;">
                    Resultado: Destrucción de la reputación institucional antes de la primera llamada
                </div>
            </div>

            <!-- El Modelo Fiduciario de Grupo Inteligencia -->
            <div class="card card-success" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="tag-pill tag-success">MODELO GRUPO INTELIGENCIA (ANTI-BLUR)</span>
                        <span style="font-family: var(--font-mono); font-size: 14px; color: #6EE7B7; font-weight: 700;">CIALDINI (1984)</span>
                    </div>
                    <h3 style="font-family: var(--font-heading); font-size: 26px; color: #FFFFFF; margin-bottom: 14px;">
                        Principio de Reciprocidad y Autoridad
                    </h3>
                    <p style="font-size: 19px; color: #DCFCE7; line-height: 1.6; margin-bottom: 16px;">
                        Entregar un documento de 10 páginas completas, maquetado a 300 DPI y con gráficos profesionales TradingView y feed institucional de Grupo Inteligencia sin pedir nada a cambio, 
                        desencadena un sesgo fiduciario inmediato:
                    </p>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.55; padding-left: 20px; display: flex; flex-direction: column; gap: 10px;">
                        <li><strong>Percepción de Élite:</strong> El prospecto asume que la firma opera a un estándar institucional inalcanzable.</li>
                        <li><strong>Gratitud y Receptividad:</strong> Contactabilidad comercial <strong style="color: var(--mint);">superior al 65%</strong>; el usuario atiende con agrado.</li>
                        <li><strong>Sales Enablement:</strong> La llamada de Ventas no es una venta en frío: es una consultoría VIP sobre el material que ya tiene.</li>
                    </ul>
                </div>
                <div style="background: rgba(0,0,0,0.5); padding: 14px; border-radius: 8px; margin-top: 18px; border: 1px solid rgba(83,193,171,0.4); text-align: center; font-size: 16px; color: var(--mint); font-weight: 700;">
                    Resultado: La llamada de ventas se convierte en una atención VIP esperada y agradecida
                </div>
            </div>
        </div>

        <div class="callout-box" style="padding: 20px 30px; font-size: 21px;">
            <strong style="color: var(--mint);">El Axioma Comercial:</strong> 
            La confianza fiduciaria no se impone con un candado forzado; se conquista demostrando superioridad técnica desde el primer segundo.
        </div>
    </div>

    <div class="slide-footer">
        <span>TEORÍA DE LA REACTANCIA PSICOLÓGICA Y CIENCIA DEL COMPORTAMIENTO COMERCIAL</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_08() -> str:
    """Lámina 08 / 16: Matriz Estratégica: Modelo Blur (Competencia) vs. Modelo GI (Conquista)."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">POSICIONAMIENTO ESTRATÉGICO &amp; DIFERENCIACIÓN RADICAL</div>
            <div class="slide-title">MATRIZ ESTRATÉGICA: CANDADO VS. CONQUISTA</div>
            <div class="slide-subtitle">Comparativa Frente a Frente de las 6 Dimensiones Críticas del Embudo de Captación</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">VENTAJA COMPETITIVA</div>
            <div class="slide-number">08 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="card" style="padding: 24px 32px;">
            <table class="table-custom">
                <thead>
                    <tr>
                        <th style="width: 25%;">Dimensión Estratégica</th>
                        <th style="width: 37%; color: #FCA5A5;">Modelo Competencia (BeFX Blur)</th>
                        <th style="width: 38%; color: #6EE7B7;">Modelo Grupo Inteligencia (Anti-Blur)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Promesa en el Anuncio</strong></td>
                        <td>"Guía Gratis USD/CLP"</td>
                        <td><strong>"Guía Táctica USD/CLP Oficial 100% Completa"</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Contenido Real Descargado</strong></td>
                        <td><span class="tag-pill tag-danger">3 págs útiles + 7 págs con Blur</span></td>
                        <td><span class="tag-pill tag-success">10 páginas íntegras + Gráficos TradingView H1</span></td>
                    </tr>
                    <tr>
                        <td><strong>Experiencia Psicológica</strong></td>
                        <td>Frustración, reactancia y sensación de trampa</td>
                        <td><strong>Gratitud, respeto y percepción fiduciaria de élite</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Recepción de Llamada Comercial</strong></td>
                        <td><span class="tag-pill tag-danger">&lt; 18% Contactabilidad (Rechazo)</span></td>
                        <td><span class="tag-pill tag-success">&gt; 65% Contactabilidad (Recepción Amable)</span></td>
                    </tr>
                    <tr>
                        <td><strong>Gancho de la Fuerza de Ventas</strong></td>
                        <td>Venta en frío: "Crea tu cuenta para desbloquear"</td>
                        <td><strong>Invitación VIP: "Cupo reservado a la Mesa Técnica"</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Calidad del Depósito Inicial</strong></td>
                        <td>Curiosos de ticket mínimo con alto riesgo de quiebra</td>
                        <td><strong>Inversores calificados con gestión de riesgo</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="callout-box" style="padding: 20px 30px; font-size: 21px;">
            <strong style="color: var(--mint);">El Factor Decisivo en Ventas:</strong> 
            El usuario que recibe un producto 100% terminado atiende el teléfono con una actitud de agradecimiento hacia Grupo Inteligencia. 
            Esto transforma la llamada comercial de una venta forzada a una consultoría técnica de alto nivel.
        </div>
    </div>

    <div class="slide-footer">
        <span>MATRIZ DE DIFERENCIACIÓN INSTITUCIONAL INTERDEPARTAMENTAL</span>
        <span>GRUPO INTELIGENCIA SpA · SANTIAGO DE CHILE</span>
    </div>
</div>
"""


def construir_slide_09() -> str:
    """Lámina 09 / 16: Embudo Nativo Paso 1: Bienvenida Instantánea en 0.1 Segundos."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">ARQUITECTURA DE CONVERSIÓN MÓVIL · FORMULARIO NATIVO DE 1-TOQUE</div>
            <div class="slide-title">PASO 1: PANTALLA DE BIENVENIDA Y CARGA EN 0.1s</div>
            <div class="slide-subtitle">Captura de Atención Inmediata dentro de Meta sin Fuga a Sitios Web Externos</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">EMBUDO MÓVIL · FASE 1</div>
            <div class="slide-number">09 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 50px;">
            <!-- Mockup Visual del Paso 1 -->
            <div style="background: rgba(0,0,0,0.75); border: 2.5px solid var(--mint); border-radius: 24px; padding: 36px; box-shadow: 0 20px 50px rgba(0,0,0,0.7); display: flex; flex-direction: column; gap: 20px; max-width: 520px; margin: 0 auto; width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-family: var(--font-mono); font-size: 14px; color: var(--mint); font-weight: 800;">META ADS · INSTANT FORM</span>
                    <span style="color: #94A3B8; font-size: 16px;">✕</span>
                </div>

                <div style="background: rgba(12,32,40,0.95); border: 1.5px solid rgba(83,193,171,0.35); border-radius: 14px; padding: 28px 24px; text-align: center;">
                    <div style="font-family: var(--font-heading); color: var(--mint); font-size: 26px; margin-bottom: 8px;">GUÍA TÁCTICA USD/CLP</div>
                    <div style="font-size: 17px; color: #CBD5E1; margin-bottom: 22px;">Manual Cuantitativo Intermercado · Edición Oficial Grupo Inteligencia SpA</div>
                    <div style="background: var(--mint); color: #04090B; font-family: var(--font-mono); font-weight: 800; font-size: 17px; padding: 16px; border-radius: 9px; box-shadow: 0 4px 16px rgba(83,193,171,0.4);">
                        OBTENER GUÍA GRATIS (1 TOQUE)
                    </div>
                </div>

                <div style="font-size: 14px; color: #94A3B8; text-align: center;">
                    🔒 Privacidad protegida · Formulario nativo oficial dentro de Instagram/Facebook
                </div>
            </div>

            <!-- Explicación Técnica de Alto Impacto -->
            <div style="display: flex; flex-direction: column; gap: 22px;">
                <div class="callout-box" style="padding: 26px 32px; font-size: 22px;">
                    <strong style="color: var(--mint); font-size: 24px; display: block; margin-bottom: 8px;">
                        Eliminación de la Fuga por Carga Lenta (0.1s vs 5.0s):
                    </strong>
                    Enviar al usuario a una página web externa que tarda 4 a 6 segundos en cargar en celular destruye el 50% del tráfico antes de ver el contenido. 
                    El Formulario Instantáneo de Meta <strong style="color: #FFFFFF;">se abre en 0.1 segundos dentro de la misma aplicación</strong>.
                </div>

                <div class="card card-success" style="padding: 28px 32px;">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 14px;">
                        Ventajas Operativas del Paso 1:
                    </h4>
                    <ul style="font-size: 19px; color: var(--text-silver); line-height: 1.6; padding-left: 24px; display: flex; flex-direction: column; gap: 12px;">
                        <li>
                            <strong style="color: #FFFFFF;">Cero Rechazo Inicial:</strong> El usuario sabe exactamente qué recibirá: la Guía Oficial de Inversión en USD/CLP de 10 páginas.
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">Recompensa Tangible:</strong> No se le pide que "hable con un asesor" a ciegas; se le ofrece un activo educativo de alto nivel.
                        </li>
                        <li>
                            <strong style="color: #6EE7B7;">Premio del Algoritmo de Meta:</strong> Al no haber rebote por lentitud, Meta asigna máxima relevancia al anuncio, abaratando el CPM en la subasta publicitaria.
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>ARQUITECTURA DE EMBUDO NATIVO META ADS · VELOCIDAD Y RETENCIÓN MÓVIL</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_10() -> str:
    """Lámina 10 / 16: Embudo Nativo Paso 2: Los 3 Filtros de Calificación (Sin Teclado)."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">ARQUITECTURA DE CONVERSIÓN MÓVIL · FORMULARIO NATIVO DE 1-TOQUE</div>
            <div class="slide-title">PASO 2: LOS 3 FILTROS ROBUSTOS DE CALIFICACIÓN (CERO TECLADO)</div>
            <div class="slide-subtitle">Segmentación de Nivel, Activo y Capital en 3 Toques Rápidos en Pantalla (&lt; 4 Segundos)</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">EMBUDO MÓVIL · FASE 2</div>
            <div class="slide-number">10 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 50px;">
            <!-- Mockup Visual del Paso 2 con los 3 Filtros -->
            <div style="background: rgba(0,0,0,0.78); border: 2.5px solid var(--mint); border-radius: 24px; padding: 32px; box-shadow: 0 20px 50px rgba(0,0,0,0.7); display: flex; flex-direction: column; gap: 16px; max-width: 530px; margin: 0 auto; width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-family: var(--font-mono); font-size: 14px; color: var(--mint); font-weight: 800;">FILTRO TÉCNICO · 3 TOQUES</span>
                    <span style="font-size: 14px; color: #94A3B8;">Paso 2 de 3</span>
                </div>

                <!-- Filtro 1 -->
                <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.3); border-radius: 10px; padding: 14px 18px;">
                    <div style="font-size: 16px; color: #FFFFFF; font-weight: 700; margin-bottom: 8px;">1. ¿Cuál es tu nivel de experiencia?</div>
                    <div style="display: flex; gap: 10px;">
                        <span style="flex: 1; background: rgba(83,193,171,0.2); border: 1.5px solid var(--mint); color: var(--mint); padding: 9px; border-radius: 6px; font-size: 14px; text-align: center; font-weight: 700;">Principiante</span>
                        <span style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #CBD5E1; padding: 9px; border-radius: 6px; font-size: 14px; text-align: center;">Opero en MT5</span>
                    </div>
                </div>

                <!-- Filtro 2 -->
                <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.3); border-radius: 10px; padding: 14px 18px;">
                    <div style="font-size: 16px; color: #FFFFFF; font-weight: 700; margin-bottom: 8px;">2. ¿Qué activo te interesa más?</div>
                    <div style="display: flex; gap: 8px;">
                        <span style="flex: 1; background: rgba(83,193,171,0.25); border: 1.5px solid var(--mint); color: #FFFFFF; padding: 9px 4px; border-radius: 6px; font-size: 13px; text-align: center; font-weight: 700;">USD/CLP &amp; Cobre</span>
                        <span style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #CBD5E1; padding: 9px 4px; border-radius: 6px; font-size: 13px; text-align: center;">Nasdaq 100</span>
                        <span style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #CBD5E1; padding: 9px 4px; border-radius: 6px; font-size: 13px; text-align: center;">Oro (XAU)</span>
                    </div>
                </div>

                <!-- Filtro 3 -->
                <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.3); border-radius: 10px; padding: 14px 18px;">
                    <div style="font-size: 16px; color: #FFFFFF; font-weight: 700; margin-bottom: 8px;">3. ¿Capital previsto de inversión?</div>
                    <div style="display: flex; gap: 8px;">
                        <span style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #CBD5E1; padding: 9px 2px; border-radius: 6px; font-size: 12px; text-align: center;">&lt; $1.000 USD</span>
                        <span style="flex: 1; background: rgba(83,193,171,0.2); border: 1.5px solid var(--mint); color: var(--mint); padding: 9px 2px; border-radius: 6px; font-size: 12px; text-align: center; font-weight: 700;">$1k a $5k USD</span>
                        <span style="flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.18); color: #CBD5E1; padding: 9px 2px; border-radius: 6px; font-size: 12px; text-align: center;">&gt; $5.000 USD</span>
                    </div>
                </div>

                <div style="background: var(--mint); color: #04090B; font-family: var(--font-mono); font-weight: 800; font-size: 16px; padding: 14px; border-radius: 8px; text-align: center;">
                    CONTINUAR A DESCARGA →
                </div>
            </div>

            <!-- Por qué este paso es oro para Ventas -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="card card-success" style="padding: 28px 32px;">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 14px;">
                        La Información que Recibe el Equipo Comercial:
                    </h4>
                    <ul style="font-size: 19px; color: var(--text-silver); line-height: 1.6; padding-left: 24px; display: flex; flex-direction: column; gap: 12px;">
                        <li>
                            <strong style="color: #FFFFFF;">1. Cero Tipeo en Celular:</strong> Se responde tocando botones en menos de 4 segundos, manteniendo una tasa de finalización <strong>superior al 38%</strong>.
                        </li>
                        <li>
                            <strong style="color: #FFFFFF;">2. Compliance 100% Políticas de Meta:</strong> Preguntar rangos de capital mediante opciones cerradas es totalmente legal en Meta Ads. No pide números de cuenta, pero perfila al lead para Ventas.
                        </li>
                        <li>
                            <strong style="color: #6EE7B7;">3. Ruteo Inteligente en el CRM:</strong> Permite asignar leads de alto patrimonio a ejecutivos Senior e invitar al usuario a la Mesa Técnica de su activo específico.
                        </li>
                    </ul>
                </div>

                <div class="callout-box" style="padding: 20px 28px; font-size: 19px;">
                    <strong style="color: var(--mint);">Sales Enablement para el Asesor:</strong> 
                    El ejecutivo de ventas sabe antes de marcar el teléfono el nombre, activo prioritario, experiencia previa y capital estimado del lead.
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>CUMPLIMIENTO DE POLÍTICAS FINANCIERAS META ADS Y SEGMENTACIÓN TÉCNICA</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_11() -> str:
    """Lámina 11 / 16: Embudo Nativo Paso 3: Autocompletado y Descarga Inmediata en 1 Clic."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">ARQUITECTURA DE CONVERSIÓN MÓVIL · FORMULARIO NATIVO DE 1-TOQUE</div>
            <div class="slide-title">PASO 3: AUTOCOMPLETADO Y DESCARGA INMEDIATA EN 1 CLIC</div>
            <div class="slide-subtitle">Captura de Datos sin Esfuerzo vía Autofill de Meta + Botón Directo al PDF Oficial</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">EMBUDO MÓVIL · FASE 3</div>
            <div class="slide-number">11 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 50px;">
            <!-- Mockup Visual del Paso 3 -->
            <div style="background: rgba(0,0,0,0.78); border: 2.5px solid var(--mint); border-radius: 24px; padding: 32px; box-shadow: 0 20px 50px rgba(0,0,0,0.7); display: flex; flex-direction: column; gap: 18px; max-width: 520px; margin: 0 auto; width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-family: var(--font-mono); font-size: 14px; color: var(--mint); font-weight: 800;">AUTOFILL NATIVO DE META</span>
                    <span style="font-size: 14px; color: #94A3B8;">Paso 3 de 3</span>
                </div>

                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.35); border-radius: 9px; padding: 12px 16px;">
                        <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase;">Nombre Completo</span>
                        <div style="font-size: 17px; color: #FFFFFF; font-weight: 600;">Carlos Silva Mendoza <span style="color: var(--mint); font-size: 13px;">(Autollenado)</span></div>
                    </div>
                    <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.35); border-radius: 9px; padding: 12px 16px;">
                        <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase;">Correo Electrónico</span>
                        <div style="font-size: 17px; color: #FFFFFF; font-weight: 600;">carlos.silva@empresa.cl <span style="color: var(--mint); font-size: 13px;">(Autollenado)</span></div>
                    </div>
                    <div style="background: rgba(12,32,40,0.95); border: 1px solid rgba(83,193,171,0.35); border-radius: 9px; padding: 12px 16px;">
                        <span style="font-size: 12px; color: #94A3B8; text-transform: uppercase;">WhatsApp / Teléfono Móvil</span>
                        <div style="font-size: 17px; color: #FFFFFF; font-weight: 600;">+56 9 8765 4321 <span style="color: var(--mint); font-size: 13px;">(Autollenado)</span></div>
                    </div>
                </div>

                <!-- Botón de Descarga Directa -->
                <a href="GUIA_TACTICA_USDCLP_COBRE_FED_GI.pdf" class="btn-interactive download" style="justify-content: center; font-size: 17px; padding: 16px;" target="_blank">
                    DESCARGAR GUÍA EN PDF AHORA ↗
                </a>

                <div style="font-size: 13px; color: #94A3B8; text-align: center;">
                    ✔ Enlace directo oficial al PDF de 10 páginas alojado en servidor seguro
                </div>
            </div>

            <!-- Explicación de la Captura Instantánea -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div class="card card-success" style="padding: 28px 32px;">
                    <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 14px;">
                        Eficiencia de Captura de Datos sin Esfuerzo:
                    </h4>
                    <div style="display: flex; flex-direction: column; gap: 14px; font-size: 18px; color: var(--text-silver); line-height: 1.6;">
                        <div>
                            <strong style="color: #6EE7B7; font-size: 20px;">Autofill Verificado de Meta:</strong><br>
                            El usuario no tiene que escribir su nombre, correo ni teléfono. Meta extrae automáticamente sus datos de registro verificados en Instagram o Facebook.
                        </div>
                        <div>
                            <strong style="color: #38BDF8; font-size: 20px;">Cumplimiento Inmediato de la Promesa:</strong><br>
                            Al tocar el botón de descarga, el PDF se abre en su visor del celular en el segundo cero. Cero esperas, cero disonancia y máxima satisfacción.
                        </div>
                        <div>
                            <strong style="color: #FFFFFF; font-size: 20px;">Derivación Automática al CRM:</strong><br>
                            Paralelamente, el webhook de Meta entrega el contacto completo y segmentado a la base comercial para el seguimiento posterior.
                        </div>
                    </div>
                </div>

                <div class="callout-box" style="padding: 18px 26px; font-size: 19px;">
                    <strong style="color: var(--mint);">Tasa de Éxito Técnico:</strong> 
                    Al no existir pasarelas complejas ni webs externas caídas, el 99% de los usuarios visualizan el archivo de inmediato.
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>ARQUITECTURA DE CONVERSIÓN MÓVIL · EXPERIENCIA DE DESCARGA DIRECTA</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_12() -> str:
    """Lámina 12 / 16: Estrategia de Doble Canal: Descarga Directa + Cortesía en WhatsApp."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">ESTRATEGIA MULTICANAL DE CONTACTO · SALES ENABLEMENT</div>
            <div class="slide-title">LA ESTRATEGIA DE DOBLE CANAL: DESCARGA DIRECTA + WHATSAPP</div>
            <div class="slide-subtitle">Cómo la Sincronización entre Meta y la Cortesía de Ventas Eleva la Contactabilidad al &gt;65%</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">CANALES DE ENTREGA</div>
            <div class="slide-number">12 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="gap: 36px; align-items: stretch;">
            <!-- Canal 1: Meta Ads Directo -->
            <div class="card card-success" style="padding: 32px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="tag-pill tag-success">CANAL 1 · META ADS (SEGUNDO 0)</span>
                        <span style="font-family: var(--font-mono); font-size: 14px; color: var(--mint); font-weight: 800;">INMEDIATO</span>
                    </div>
                    <h3 style="font-family: var(--font-heading); font-size: 26px; color: #FFFFFF; margin-bottom: 14px;">
                        Descarga Directa en Pantalla Final
                    </h3>
                    <p style="font-size: 19px; color: var(--text-silver); line-height: 1.6; margin-bottom: 16px;">
                        El usuario toca el botón de descarga en el formulario de Meta y abre el PDF en el visor de su celular al instante:
                    </p>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.55; padding-left: 20px; display: flex; flex-direction: column; gap: 10px;">
                        <li><strong>Cero Fricción:</strong> Satisface la curiosidad en el momento exacto de mayor interés.</li>
                        <li><strong>Verificación de Calidad:</strong> El usuario comprueba con sus propios ojos la calidad del gráfico TradingView y los datos reales de Grupo Inteligencia.</li>
                        <li><strong>Cumplimiento de Marca:</strong> La firma cumple la promesa publicitaria al 100%, sin trampas ni filtros difusos.</li>
                    </ul>
                </div>
                <div style="background: rgba(0,0,0,0.5); padding: 14px; border-radius: 8px; margin-top: 18px; border: 1px solid rgba(83,193,171,0.35); text-align: center; font-size: 16px; color: var(--mint); font-weight: 700;">
                    ✔ Cumplimiento instantáneo de la promesa de pauta
                </div>
            </div>

            <!-- Canal 2: WhatsApp Cortesía -->
            <div class="card" style="padding: 32px; border-color: rgba(56, 189, 248, 0.45); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="tag-pill tag-accent">CANAL 2 · WHATSAPP COMERCIAL (+3 MIN)</span>
                        <span style="font-family: var(--font-mono); font-size: 14px; color: var(--blue-accent); font-weight: 800;">HUMANO</span>
                    </div>
                    <h3 style="font-family: var(--font-heading); font-size: 26px; color: #FFFFFF; margin-bottom: 14px;">
                        Envío de Cortesía por WhatsApp
                    </h3>
                    <p style="font-size: 19px; color: var(--text-silver); line-height: 1.6; margin-bottom: 16px;">
                        A los 3 minutos de la descarga, el asesor comercial escribe con un enfoque de servicio y no de venta agresiva:
                    </p>
                    <div style="background: rgba(12, 32, 40, 0.95); border-left: 4px solid var(--blue-accent); border-radius: 8px; padding: 16px 20px; font-size: 17px; color: #BAE6FD; line-height: 1.5; font-style: italic; margin-bottom: 14px;">
                        "Hola Carlos, te adjunto por aquí también la Guía Táctica del USD/CLP para que la tengas guardada en tu chat. ¿Pudiste abrir el archivo sin problemas?"
                    </div>
                    <ul style="font-size: 18px; color: var(--text-silver); line-height: 1.55; padding-left: 20px; display: flex; flex-direction: column; gap: 8px;">
                        <li><strong>Abre el Canal Humano:</strong> Inicia la conversación con cortesía y servicio.</li>
                        <li><strong>Confirmación Amable:</strong> El prospecto responde agradeciendo el material.</li>
                    </ul>
                </div>
                <div style="background: rgba(0,0,0,0.5); padding: 14px; border-radius: 8px; margin-top: 18px; border: 1px solid rgba(56, 189, 248, 0.35); text-align: center; font-size: 16px; color: var(--blue-accent); font-weight: 700;">
                    ✔ Contactabilidad efectiva salta de &lt;18% a más del 65%
                </div>
            </div>
        </div>

        <div class="callout-box" style="padding: 20px 30px; font-size: 21px;">
            <strong style="color: var(--mint);">El Secreto de la Contactabilidad:</strong> 
            Cuando el asesor llama o escribe, el prospecto no lo ve como un telemarketer intrusivo, sino como el representante de la firma fiduciaria que le acaba de obsequiar un material de alto valor formativo.
        </div>
    </div>

    <div class="slide-footer">
        <span>SINCRONIZACIÓN DE CANALES COMERCIALES Y EXPERIENCIA DEL CLIENTE</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_13() -> str:
    """Lámina 13 / 16: La Ecuación Financiera de Meta Ads: CPL = CPC ÷ CVR."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">EFICIENCIA FINANCIERA &amp; MODELO MATEMÁTICO · META ADS</div>
            <div class="slide-title">LA ECUACIÓN FINANCIERA DE META: CPL = CPC ÷ CVR</div>
            <div class="slide-subtitle">Por Qué Ofrecer un Mejor Producto Reduce el Costo por Lead en Más de un 80%</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">MODELADO MATEMÁTICO</div>
            <div class="slide-number">13 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="grid-2" style="align-items: center; gap: 44px;">
            <!-- Ecuación y Explicación Matemática -->
            <div style="display: flex; flex-direction: column; gap: 22px;">
                <div class="card" style="padding: 28px 32px; border-left: 8px solid var(--mint);">
                    <div style="font-family: var(--font-mono); font-size: 15px; color: var(--mint); font-weight: 800; text-transform: uppercase; margin-bottom: 8px;">
                        FÓRMULA DETERMINANTE EN META ADS:
                    </div>
                    <div style="font-family: var(--font-heading); font-size: 44px; color: #FFFFFF; margin-bottom: 14px;">
                        CPL = CPC ÷ CVR
                    </div>
                    <div style="font-size: 19px; color: var(--text-silver); line-height: 1.6;">
                        • <strong style="color: #FFFFFF;">CPC (Costo por Clic):</strong> Disminuye porque un activo tangible y claro (Guía USD/CLP) eleva el CTR a <strong>~1.85% (+164% clics)</strong>, premiado por el algoritmo.<br>
                        • <strong style="color: #FFFFFF;">CVR (Conversión Formulario):</strong> Sube de 11% a <strong>~38%</strong> al eliminar el teclado táctil y usar autofill nativo de 1-toque.<br>
                        • <strong style="color: var(--mint);">Resultado Matemático:</strong> El Costo por Lead se derrumba de <strong>$7 - $14 USD a $0.78 - $1.65 USD</strong>.
                    </div>
                </div>

                <div class="callout-box" style="padding: 22px 28px; font-size: 20px;">
                    <strong style="color: var(--mint);">¿Ofrecer una descarga encarece la pauta?</strong><br>
                    <strong>No: sale hasta un 80% más barato.</strong> Meta no cobra por el archivo que se descarga, cobra por la atención. Un gancho de alto interés abarata la subasta.
                </div>
            </div>

            <!-- Panel de Comparación de Dinámica de Subasta -->
            <div class="card card-success" style="padding: 32px;">
                <h4 style="font-family: var(--font-heading); font-size: 24px; color: #FFFFFF; margin-bottom: 16px;">
                    Por Qué el Algoritmo Premia a Grupo Inteligencia:
                </h4>
                <div style="display: flex; flex-direction: column; gap: 18px; font-size: 18px; color: var(--text-silver); line-height: 1.6;">
                    <div style="background: rgba(0,0,0,0.4); padding: 16px 20px; border-radius: 10px; border: 1px solid rgba(83,193,171,0.25);">
                        <strong style="color: var(--mint); font-size: 20px;">1. Mayor Calidad del Anuncio (Relevance Score):</strong><br>
                        Meta busca que los usuarios interactúen con contenido valioso. Al ofrecer un manual técnico real, los usuarios guardan, comentan y hacen clic, reduciendo el CPM en la subasta.
                    </div>

                    <div style="background: rgba(0,0,0,0.4); padding: 16px 20px; border-radius: 10px; border: 1px solid rgba(83,193,171,0.25);">
                        <strong style="color: var(--mint); font-size: 20px;">2. Máxima Señal de Completitud para el Algoritmo:</strong><br>
                        Los formularios con fricción de teclado en smartphones sufren menor finalización. En contraste, el flujo nativo de 1-toque eleva la tasa de completitud (&gt;38%), indicándole al algoritmo de Meta que la audiencia responde favorablemente, abaratando la subasta.
                    </div>

                    <div style="background: rgba(0,0,0,0.4); padding: 16px 20px; border-radius: 10px; border: 1px solid rgba(83,193,171,0.25);">
                        <strong style="color: var(--mint); font-size: 20px;">3. Círculo Virtuoso Financiero:</strong><br>
                        Más clics a menor costo + mayor tasa de finalización = flujo masivo de prospectos a una fracción del costo tradicional.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="slide-footer">
        <span>MODELO MATEMÁTICO DE SUBASTA Y FACTOR DE CALIDAD EN META ADS MANAGER</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_14() -> str:
    """Lámina 14 / 16: Simulación Econométrica de Cartera (Base $600 USD Mensuales)."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">SIMULACIÓN ECONOMÉTRICA COMPARATIVA · PRESUPUESTO MENSUAL $600 USD</div>
            <div class="slide-title">SIMULACIÓN FINANCIERA: LÍNEA BASE VS. NUEVA ARQUITECTURA GI</div>
            <div class="slide-subtitle">Impacto Comparativo con un Presupuesto Base de $600 USD Mensuales (~$570.000 CLP)</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">UNIT ECONOMICS</div>
            <div class="slide-number">14 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <div class="card card-success" style="padding: 18px 28px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-family: var(--font-heading); font-size: 20px; color: #FFFFFF;">Matriz Comparativa de Unit Economics</span>
                <span class="tag-pill tag-success" style="font-size: 13px; padding: 5px 12px;">MERCADO CHILE (850k - 1.2M USUARIOS OBJETIVO)</span>
            </div>

            <table class="table-custom table-dense">
                <thead>
                    <tr>
                        <th style="width: 25%;">Métrica del Embudo</th>
                        <th style="width: 37%; color: #FCA5A5;">Línea Base Estándar (Formulario Abierto)</th>
                        <th style="width: 38%; color: #6EE7B7;">Nueva Arquitectura GI (Guía + 1-Toque)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Presupuesto Base</strong></td>
                        <td>$600 USD mensuales</td>
                        <td><strong>$600 USD mensuales (Mismo capital)</strong></td>
                    </tr>
                    <tr>
                        <td><strong>CTR (Tasa de Clic)</strong></td>
                        <td><span class="tag-pill tag-warning" style="font-size: 12px; padding: 3px 8px;">0.70% (Línea base)</span></td>
                        <td><span class="tag-pill tag-success" style="font-size: 12px; padding: 3px 8px;">1.85% (+164% más tráfico)</span></td>
                    </tr>
                    <tr>
                        <td><strong>Clics Generados</strong></td>
                        <td>~763 clics</td>
                        <td><strong style="color: var(--blue-accent);">~2.016 clics (+1.253 clics)</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Conversión Formulario (CVR)</strong></td>
                        <td><span class="tag-pill tag-warning" style="font-size: 12px; padding: 3px 8px;">11% (Fricción de teclado móvil)</span></td>
                        <td><span class="tag-pill tag-success" style="font-size: 12px; padding: 3px 8px;">38% (Autofill nativo de 1-toque)</span></td>
                    </tr>
                    <tr>
                        <td><strong>Leads Brutos Captados</strong></td>
                        <td>~84 contactos</td>
                        <td><strong style="color: #6EE7B7; font-size: 20px;">~766 contactos calificados (9.1x)</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Costo por Lead (CPL)</strong></td>
                        <td style="color: #FCA5A5; font-weight: 800;">$7.14 – $14.20 USD</td>
                        <td style="color: #6EE7B7; font-weight: 800; font-size: 20px;">$0.78 – $1.65 USD (-82%)</td>
                    </tr>
                    <tr>
                        <td><strong>Contactabilidad WhatsApp</strong></td>
                        <td>&lt; 18% (~15 personas)</td>
                        <td><strong style="color: var(--mint);">&gt; 65% (~498 personas receptivas)</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Conversión a Cliente Activo</strong></td>
                        <td>0.3% (0 a 1 cuenta fondeada)</td>
                        <td><strong>2.4% (18 a 19 cuentas fondeadas)</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="callout-box" style="padding: 14px 24px; font-size: 18px; line-height: 1.45;">
            <strong style="color: var(--mint);">Multiplicación del Retorno Publicitario:</strong> 
            Con el mismo presupuesto de <strong>$600 USD</strong>, la combinación de contenido fiduciario terminado y UX sin fricción 
            permite a Marketing entregar hasta <strong>9.1x más volumen comercial</strong> a Ventas, maximizando el rendimiento de cada dólar invertido.
        </div>
    </div>

    <div class="slide-footer">
        <span>MODELADO ECONOMÉTRICO REFERENCIAL BASADO EN BENCHMARKS DE META ADS Y WORDSTREAM</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_15() -> str:
    """Lámina 15 / 16: Gobernanza Interdepartamental: Delimitación de Roles y Flujo Swimlane."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">GOBERNANZA OPERATIVA &amp; ARQUITECTURA DE COOPERACIÓN</div>
            <div class="slide-title">GOBERNANZA INTERDEPARTAMENTAL: ROLES Y FLUJO SWIMLANE</div>
            <div class="slide-subtitle">Delimitación Clara de Responsabilidades desde la Producción Técnica hasta el Cierre Comercial</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">ARQUITECTURA OPERATIVA</div>
            <div class="slide-number">15 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <!-- 4 Fases Horizontales con Gran Espacio -->
        <div class="grid-4" style="gap: 22px;">
            <div class="card" style="padding: 24px 20px; border-top: 5px solid var(--mint);">
                <div style="font-family: var(--font-mono); font-size: 13px; color: var(--mint); font-weight: 800; margin-bottom: 6px;">FASE 1 · INICIO</div>
                <div style="font-family: var(--font-heading); font-size: 20px; color: #FFFFFF; margin-bottom: 10px;">Post Venta</div>
                <ul style="font-size: 16px; color: var(--text-silver); line-height: 1.5; padding-left: 16px; display: flex; flex-direction: column; gap: 6px;">
                    <li>Provee las <strong>Guías 100% terminadas</strong> bajo Brandkit.</li>
                    <li>Entrega la estructura técnica del formulario de 1-toque.</li>
                    <li>Garantiza rigor cuantitativo con gráficos TradingView y feed de Grupo Inteligencia.</li>
                </ul>
            </div>

            <div class="card" style="padding: 24px 20px; border-top: 5px solid var(--blue-accent);">
                <div style="font-family: var(--font-mono); font-size: 13px; color: var(--blue-accent); font-weight: 800; margin-bottom: 6px;">FASE 2 · PAUTA &amp; ESCALA</div>
                <div style="font-family: var(--font-heading); font-size: 20px; color: #FFFFFF; margin-bottom: 10px;">Marketing</div>
                <ul style="font-size: 16px; color: var(--text-silver); line-height: 1.5; padding-left: 16px; display: flex; flex-direction: column; gap: 6px;">
                    <li>Lidera la estrategia de pauta y segmentación en <strong>Meta Ads</strong>.</li>
                    <li>Publica el formulario nativo y optimiza el algoritmo.</li>
                    <li>Gestiona la derivación automática de leads al CRM.</li>
                </ul>
            </div>

            <div class="card" style="padding: 24px 20px; border-top: 5px solid #FDE047;">
                <div style="font-family: var(--font-mono); font-size: 13px; color: #FDE047; font-weight: 800; margin-bottom: 6px;">FASE 3 · CONTACTO</div>
                <div style="font-family: var(--font-heading); font-size: 20px; color: #FFFFFF; margin-bottom: 10px;">Ventas</div>
                <ul style="font-size: 16px; color: var(--text-silver); line-height: 1.5; padding-left: 16px; display: flex; flex-direction: column; gap: 6px;">
                    <li>Envía el PDF por <strong>WhatsApp de cortesía</strong> (+3 min).</li>
                    <li>Llamada VIP: <em>"Tengo tu cupo reservado a la Mesa Técnica"</em>.</li>
                    <li>Segmenta y agenda según el activo de interés del lead.</li>
                </ul>
            </div>

            <div class="card" style="padding: 24px 20px; border-top: 5px solid #10B981;">
                <div style="font-family: var(--font-mono); font-size: 13px; color: #10B981; font-weight: 800; margin-bottom: 6px;">FASE 4 · CIERRE</div>
                <div style="font-family: var(--font-heading); font-size: 20px; color: #FFFFFF; margin-bottom: 10px;">Mesas Técnicas</div>
                <ul style="font-size: 16px; color: var(--text-silver); line-height: 1.5; padding-left: 16px; display: flex; flex-direction: column; gap: 6px;">
                    <li>Post Venta conduce <strong>3 Clínicas semanales en vivo</strong>.</li>
                    <li>Habilita a Ventas para el cierre y fondeo de cuenta real.</li>
                    <li>Blindaje de LTV mediante la Regla del 1% de riesgo.</li>
                </ul>
            </div>
        </div>

        <div class="callout-box" style="padding: 22px 30px; font-size: 21px;">
            <strong style="color: var(--mint);">Sinergia Interdepartamental:</strong> 
            Una alianza ganar-ganar donde Post Venta absorbe el trabajo técnico de redacción y diseño de guías, 
            permitiendo a Marketing brillar optimizando la pauta y escalando resultados récord de CPL, 
            mientras Comercial recibe contactos receptivos con alto potencial patrimonial.
        </div>
    </div>

    <div class="slide-footer">
        <span>DELIMITACIÓN DE RESPONSABILIDADES Y GOBERNANZA OPERATIVA</span>
        <span>GRUPO INTELIGENCIA SpA</span>
    </div>
</div>
"""


def construir_slide_16() -> str:
    """Lámina 16 / 16: Decisión Ejecutiva Inmediata: Plan Piloto de 10 Días ($150 USD)."""
    return """
<div class="slide">
    <div class="slide-header">
        <div class="header-left">
            <div class="brand-tag">HOJA DE RUTA &amp; TOMA DE DECISIÓN EJECUTIVA</div>
            <div class="slide-title">PLAN PILOTO CONTROLADO: 10 DÍAS DE AUDITORÍA ($150 USD)</div>
            <div class="slide-subtitle">Validación Empírica Conjunta de CPL y Contactabilidad con Inversión Acotada y Riesgo Cero</div>
        </div>
        <div class="header-right">
            <div class="slide-badge">DECISIÓN HOY</div>
            <div class="slide-number">16 / 16</div>
        </div>
    </div>

    <div class="slide-body">
        <!-- Hero Card del Plan Piloto -->
        <div class="card card-success" style="padding: 32px 40px; border-left: 8px solid var(--mint);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div>
                    <span class="tag-pill tag-success" style="font-size: 15px; padding: 8px 18px;">PROPUESTA DE ACUERDO INMEDIATO PARA GERENCIA GENERAL &amp; MARKETING</span>
                    <h3 style="font-family: var(--font-heading); font-size: 32px; color: var(--text-white); margin-top: 6px;">
                        Plan Piloto Conjunto de 10 Días: Presupuesto Acotado de $150 USD
                    </h3>
                </div>
                <div style="text-align: right;">
                    <span style="font-family: var(--font-heading); font-size: 44px; color: var(--mint); text-shadow: 0 0 20px var(--mint-glow);">$150 USD</span>
                    <span style="display: block; font-family: var(--font-mono); font-size: 14px; color: #CBD5E1; font-weight: 700;">INVERSIÓN TOTAL · RIESGO CERO</span>
                </div>
            </div>

            <div class="grid-3" style="gap: 26px; font-size: 18px; color: #F1F5F9; line-height: 1.6;">
                <div style="background: rgba(0,0,0,0.55); padding: 22px; border-radius: 10px; border: 1.5px solid rgba(83,193,171,0.3);">
                    <strong style="color: var(--mint); display: block; margin-bottom: 8px; font-size: 19px;">Semana 1 · Despliegue Rápido</strong>
                    No requiere semanas de desarrollo: Post Venta ya tiene la guía terminada bajo Brandkit. Marketing solo monta el formulario nativo de 1-toque en Meta Ads Manager.
                </div>
                <div style="background: rgba(0,0,0,0.55); padding: 22px; border-radius: 10px; border: 1.5px solid rgba(83,193,171,0.3);">
                    <strong style="color: var(--mint); display: block; margin-bottom: 8px; font-size: 19px;">Semana 2 · Auditoría Conjunta (10 Días)</strong>
                    Pauta de $15 USD diarios durante 10 días para medir en tiempo real el CTR, CPL efectivo, tasa de descarga y contactabilidad en WhatsApp de la fuerza comercial.
                </div>
                <div style="background: rgba(0,0,0,0.55); padding: 22px; border-radius: 10px; border: 1.5px solid rgba(83,193,171,0.3);">
                    <strong style="color: var(--mint); display: block; margin-bottom: 8px; font-size: 19px;">Semana 3 · Decisión con Cifras Propias</strong>
                    Al día 10, Gerencia, Marketing y Comercial evalúan juntos las métricas reales del embudo para definir el plan de escalamiento formal con éxito garantizado.
                </div>
            </div>
        </div>

        <div class="callout-box" style="padding: 22px 32px; font-size: 21px;">
            <strong style="color: var(--mint);">Conclusión y Recomendación:</strong> 
            Con una inversión de solo $150 USD y los materiales listos para publicación inmediata, Grupo Inteligencia cuenta con la oportunidad técnica 
            y comercial de consolidar el liderazgo en captación financiera calificada en Chile de la mano de un equipo interdepartamental perfectamente alineado.
        </div>
    </div>

    <div class="slide-footer">
        <span>GRUPO INTELIGENCIA SpA · SANTIAGO DE CHILE</span>
        <span>PROPUESTA LISTA PARA AUTORIZACIÓN Y EJECUCIÓN INMEDIATA</span>
    </div>
</div>
"""


def compilar_presentacion() -> int:
    from playwright.sync_api import sync_playwright

    slides_html = [
        construir_slide_01(),
        construir_slide_02(),
        construir_slide_03(),
        construir_slide_04(),
        construir_slide_05(),
        construir_slide_06(),
        construir_slide_07(),
        construir_slide_08(),
        construir_slide_09(),
        construir_slide_10(),
        construir_slide_11(),
        construir_slide_12(),
        construir_slide_13(),
        construir_slide_14(),
        construir_slide_15(),
        construir_slide_16(),
    ]

    # Script interactivo de alta gama para presentación web
    script_navegacion = """
    <!-- Barra de Progreso Superior -->
    <div id="progress-bar"></div>

    <!-- HUD Flotante de Control de Presentación -->
    <div id="deck-hud">
        <button class="hud-btn" id="hud-prev" title="Anterior (← o ↑)">◀ Ant</button>
        <span class="hud-counter" id="hud-counter">01 / 16</span>
        <button class="hud-btn" id="hud-next" title="Siguiente (→ o Espacio)">Sig ▶</button>
        
        <select class="hud-select" id="hud-select" title="Saltar a diapositiva">
            <option value="0">01. Portada &amp; Alianza Estratégica</option>
            <option value="1">02. BLUF: Oportunidad Móvil (+82%)</option>
            <option value="2">03. Evolución del Embudo (Starbucks)</option>
            <option value="3">04. Guía Táctica USD/CLP (Showcase)</option>
            <option value="4">05. Rigor TradingView &amp; Regla 1%</option>
            <option value="5">06. Inteligencia: El Vacío de BeFX</option>
            <option value="6">07. La Trampa del Blur vs. Autoridad</option>
            <option value="7">08. Matriz: Candado vs. Conquista</option>
            <option value="8">09. Embudo Paso 1: Carga en 0.1s</option>
            <option value="9">10. Embudo Paso 2: Filtros Calificación</option>
            <option value="10">11. Embudo Paso 3: Autofill y Descarga</option>
            <option value="11">12. Doble Canal: Descarga + WhatsApp</option>
            <option value="12">13. Ecuación Meta: CPL = CPC ÷ CVR</option>
            <option value="13">14. Simulación Financiera ($600 USD)</option>
            <option value="14">15. Gobernanza Swimlane</option>
            <option value="15">16. Plan Piloto Conjunto ($150 USD)</option>
        </select>

        <button class="hud-btn" id="hud-mode-btn" title="Alternar Vista Diapositiva / Scroll Continuo (Tecla M)">📑 Modo Diapositiva</button>
        <button class="hud-btn" id="hud-fs-btn" title="Pantalla Completa (Tecla F)">⛶ Pantalla Completa</button>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const slides = Array.from(document.querySelectorAll('.slide'));
        const total = slides.length;
        let currentIndex = 0;
        let modeDeck = true;

        const progressBar = document.getElementById('progress-bar');
        const counterEl = document.getElementById('hud-counter');
        const selectEl = document.getElementById('hud-select');
        const modeBtn = document.getElementById('hud-mode-btn');
        const fsBtn = document.getElementById('hud-fs-btn');

        function actualizarHUD() {
            const pct = ((currentIndex + 1) / total) * 100;
            if (progressBar) progressBar.style.width = pct + '%';
            if (counterEl) counterEl.textContent = `${String(currentIndex + 1).padStart(2, '0')} / ${total}`;
            if (selectEl) selectEl.value = currentIndex;
        }

        function irASlide(index) {
            if (index < 0) index = 0;
            if (index >= total) index = total - 1;
            currentIndex = index;

            if (modeDeck) {
                slides.forEach((s, idx) => {
                    if (idx === currentIndex) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
                window.scrollTo(0, 0);
            } else {
                slides[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            actualizarHUD();
        }

        function alternarModo() {
            modeDeck = !modeDeck;
            if (modeDeck) {
                document.body.classList.add('mode-deck');
                if (modeBtn) modeBtn.textContent = '📑 Modo Diapositiva';
                irASlide(currentIndex);
            } else {
                document.body.classList.remove('mode-deck');
                slides.forEach(s => s.classList.remove('active'));
                if (modeBtn) modeBtn.textContent = '📜 Vista Continua';
                slides[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        function alternarFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                if (document.exitFullscreen) document.exitFullscreen();
            }
        }

        document.getElementById('hud-prev')?.addEventListener('click', () => irASlide(currentIndex - 1));
        document.getElementById('hud-next')?.addEventListener('click', () => irASlide(currentIndex + 1));
        selectEl?.addEventListener('change', (e) => irASlide(parseInt(e.target.value, 10)));
        modeBtn?.addEventListener('click', alternarModo);
        fsBtn?.addEventListener('click', alternarFullscreen);

        window.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;

            if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ' || e.key === 'ArrowDown') {
                e.preventDefault();
                irASlide(currentIndex + 1);
            } else if (e.key === 'ArrowLeft' || e.key === 'PageUp' || e.key === 'ArrowUp') {
                e.preventDefault();
                irASlide(currentIndex - 1);
            } else if (e.key === 'Home') {
                e.preventDefault();
                irASlide(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                irASlide(total - 1);
            } else if (e.key.toLowerCase() === 'f') {
                e.preventDefault();
                alternarFullscreen();
            } else if (e.key.toLowerCase() === 'm') {
                e.preventDefault();
                alternarModo();
            }
        });

        // Inicializar en modo diapositiva a pantalla completa
        document.body.classList.add('mode-deck');
        irASlide(0);
    });
    </script>
    """

    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Sistema de Captación Calificada en Meta Ads · Grupo Inteligencia</title>
<style>
{generar_css()}
</style>
</head>
<body class="mode-deck">
{"".join(slides_html)}
{script_navegacion}
</body>
</html>
"""

    # Guardar HTML oficial en docs y scratch
    ruta_html_docs = RAIZ / "docs" / "presentacion_horizontal.html"
    ruta_html_docs.parent.mkdir(parents=True, exist_ok=True)
    ruta_html_docs.write_text(html_completo, encoding="utf-8")

    ruta_html_scratch = DIR_PREVIEWS / "presentacion_horizontal.html"
    ruta_html_scratch.parent.mkdir(parents=True, exist_ok=True)
    ruta_html_scratch.write_text(html_completo, encoding="utf-8")
    print(f"✅ HTML Oficial generado exitosamente en:\n  -> {ruta_html_docs}\n  -> {ruta_html_scratch}")

    # Asegurar que los PDFs anexos estén en docs/
    pdf_guia = RAIZ / "docs" / "GUIA_TACTICA_USDCLP_COBRE_FED_GI.pdf"
    pdf_befx = RAIZ / "docs" / "PDF_guia_USD_CLP_BLUR_BEFX.pdf"
    if pdf_guia.exists():
        shutil.copy2(pdf_guia, DIR_PREVIEWS / pdf_guia.name)
    if pdf_befx.exists():
        shutil.copy2(pdf_befx, DIR_PREVIEWS / pdf_befx.name)

    # Generar capturas de verificación PNG con Playwright en modo responsive
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            pagina = navegador.new_page(viewport={"width": 1920, "height": 1080})
            pagina.goto(ruta_html_docs.as_uri(), wait_until="load")
            
            # En modo deck, iterar por las diapositivas para tomar screenshot de cada una
            for idx in range(16):
                pagina.evaluate(f"window.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Home' }}))") if idx == 0 else pagina.evaluate(f"document.getElementById('hud-select').value = '{idx}'; document.getElementById('hud-select').dispatchEvent(new Event('change'));")
                pagina.wait_for_timeout(100)
                preview_path = DIR_PREVIEWS / f"slide_{idx + 1}.png"
                pagina.screenshot(path=str(preview_path), full_page=False)
                print(f"Preview Slide {idx + 1}: {preview_path}")

            navegador.close()
            print("✅ Previews PNG actualizadas exitosamente.")
    except Exception as e:
        print(f"Aviso Playwright previews: {e}")

    print(f"\n🎉 ¡Versión Oficial HTML Lista! Archivo: {ruta_html_docs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(compilar_presentacion())

