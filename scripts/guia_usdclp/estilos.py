# -*- coding: utf-8 -*-
"""Módulo de estilos CSS, fuentes base64, portada y procesador de callouts."""

from __future__ import annotations

import base64
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
FUENTES = RAIZ / "templates" / "stories" / "fonts"
ASSETS = RAIZ / "templates" / "stories" / "assets"

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
    "important": ("Gestión de Riesgo y Regla del 1%", "#53C1AB", "rgba(83, 193, 171, 0.12)", "#53C1AB"),
    "warning": ("Qué NO Hacer: Advertencia Operativa", "#FBBF24", "rgba(245, 158, 11, 0.12)", "#F59E0B"),
    "critical": ("Alerta Crítica y Protocolo Obligatorio", "#F87171", "rgba(239, 68, 68, 0.15)", "#EF4444"),
    "caution": ("Precaución Cuantitativa", "#FF8A65", "rgba(231, 111, 81, 0.14)", "#E76F51"),
    "tip": ("Consejo Profesional de Trading", "#67E8F9", "rgba(62, 145, 175, 0.14)", "#3E91AF"),
    "note": ("Nota Técnica", "#94A3B8", "rgba(148, 163, 184, 0.12)", "#64748B"),
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


def codificar_asset_base64(ruta_rel: str) -> str:
    ruta = ASSETS / ruta_rel
    if not ruta.exists():
        return ""
    mime = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{datos}"


def procesar_callouts(html: str) -> str:
    patron = re.compile(r"<blockquote>\s*(.*?)\s*</blockquote>", re.S)

    def reemplazo(m: re.Match[str]) -> str:
        interior = m.group(1)
        marca = re.match(r"<p>\[!(\w+)\]\s*", interior)
        if not marca:
            return m.group(0)
        tipo = marca.group(1).lower()
        if tipo not in TITULOS_CALLOUT:
            return m.group(0)
        rotulo, color, _, borde = TITULOS_CALLOUT[tipo]
        fondo = {
            "important": "#F0FDF9",
            "warning": "#FFFBEB",
            "critical": "#FFF5F5",
            "caution": "#FFF7ED",
            "tip": "#F0F9FF",
            "note": "#F8FAFC",
        }.get(tipo, "#F8FAFC")
        resto = "<p>" + interior[marca.end():]
        return (
            f'<div class="aviso aviso-{tipo}" style="background:{fondo}; border-left: 3.5px solid {borde};">'
            f'<div class="aviso-rotulo" style="color:{color}; font-family:\'Space Grotesk\', monospace; font-size:10px; font-weight:700; text-transform:uppercase; margin-bottom:2px;">{rotulo}</div>{resto}</div>'
        )

    return patron.sub(reemplazo, html)


def construir_portada() -> str:
    img_fondo = codificar_asset_base64("activos/usdclp.jpg")
    img_logo = codificar_asset_base64("LOGO Blanco.png")

    return f"""
<section class="seccion-portada">
  <div class="portada-imagen"></div>
  <div class="portada-panel"></div>
  <div class="portada-contenido">
    <div class="portada-header">
      <div class="portada-logo">
        <img src="{img_logo}" alt="Grupo Inteligencia">
      </div>
      <div class="portada-tag-gob">
        MANUAL DE ESTRATEGIAS · EDICIÓN OFICIAL
      </div>
    </div>

    <div class="portada-centro">
      <div class="portada-badge-top">MERCADO CAMBIARIO · CHILE</div>
      <h1 class="portada-titulo">INVERTIR EN<br>USD/CLP</h1>
      <p class="portada-subtitulo">Una guía práctica para leer el dólar chileno a través del <span class="subtitulo-acento">cobre</span>, las tasas y el riesgo.</p>

      <div class="portada-pilares-grid">
        <div class="pilar-card">
          <div class="pilar-num">01</div>
          <div class="pilar-tit">Cobre y peso</div>
          <div class="pilar-desc">Cómo el precio por tonelada cambia el flujo de dólares.</div>
        </div>
        <div class="pilar-card">
          <div class="pilar-num">02</div>
          <div class="pilar-tit">Tasas</div>
          <div class="pilar-desc">Qué significa el diferencial entre el BCCh y la Fed.</div>
        </div>
        <div class="pilar-card">
          <div class="pilar-num">03</div>
          <div class="pilar-tit">Lectura H1</div>
          <div class="pilar-desc">Gráfico TradingView con feed Grupo Inteligencia.</div>
        </div>
        <div class="pilar-card">
          <div class="pilar-num">04</div>
          <div class="pilar-tit">Riesgo</div>
          <div class="pilar-desc">Una regla simple para dimensionar cada operación.</div>
        </div>
      </div>
    </div>

    <div class="portada-footer">
      <div class="portada-meta-izq">
        <strong>GRUPO INTELIGENCIA SpA · RESEARCH & ESTRATEGIA</strong><br>
        Documento pedagógico institucional · Santiago de Chile · Septiembre 2026
      </div>
      <div class="portada-meta-der">
        FEED DE MERCADO INSTITUCIONAL<br>
        <span class="acento-mint">TRADINGVIEW · GRUPO INTELIGENCIA</span>
      </div>
    </div>
  </div>
</section>
"""


def hoja_de_estilos() -> str:
    img_fondo = codificar_asset_base64("activos/usdclp.jpg")

    return f"""
{caras_de_fuente()}

@page {{
  size: A4 portrait;
  margin: 10mm 14mm 10mm 14mm;
}}

* {{
  box-sizing: border-box;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}

html, body {{
  margin: 0;
  padding: 0;
  background: #FFFFFF;
  color: #3A3F52;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 12px;
  line-height: 1.45;
}}

/* ================= PORTADA ================= */
.seccion-portada {{
  width: 100%;
  height: 1040px;
  max-height: 1040px;
  position: relative;
  page-break-after: always;
  overflow: hidden;
  background: #FFFFFF;
}}

.portada-imagen {{
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 58%;
  background: #081418 url('{img_fondo}') center center / cover no-repeat;
}}

.portada-panel {{
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 57%;
  background: #FFFFFF;
  clip-path: polygon(0 0, 78% 0, 100% 100%, 0 100%);
}}

.portada-contenido {{
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 30px 16px;
}}

.portada-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #D8E5E7;
  padding-bottom: 14px;
}}

.portada-logo img {{
  height: 34px;
  width: auto;
  filter: invert(1);
}}

.portada-tag-gob {{
  font-family: 'Space Grotesk', monospace;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #3E91AF;
  background: rgba(255,255,255,0.9);
  border: 1px solid #C1E5E4;
  padding: 5px 12px;
  border-radius: 4px;
}}

.portada-badge-top {{
  font-family: 'Space Grotesk', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #3E91AF;
  margin-bottom: 12px;
}}

.portada-titulo {{
  font-family: 'Goldman', sans-serif;
  font-size: 42px;
  font-weight: 700;
  color: #0D0D1A;
  line-height: 1.04;
  margin: 0 0 14px 0;
}}

.portada-subtitulo {{
  font-size: 13px;
  font-weight: 600;
  color: #3A3F52;
  line-height: 1.35;
  margin: 0 0 24px 0;
  max-width: 320px;
  position: relative;
  z-index: 3;
}}

.subtitulo-acento {{
  color: #176B61;
  background: #DDF4EE;
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
}}

.portada-pilares-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-width: 420px;
}}

.pilar-card {{
  background: rgba(255,255,255,0.92);
  border: 1px solid #C1E5E4;
  border-radius: 6px;
  padding: 10px 12px;
}}

.pilar-num {{
  font-family: 'Space Grotesk', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #53C1AB;
  margin-bottom: 4px;
}}

.pilar-tit {{
  font-family: 'Goldman', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: #0D0D1A;
  margin-bottom: 4px;
}}

.pilar-desc {{
  font-size: 9px;
  color: #3A3F52;
  line-height: 1.3;
}}

.portada-footer {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-top: 1px solid rgba(83, 193, 171, 0.25);
  padding-top: 14px;
  font-family: 'Space Grotesk', monospace;
  font-size: 9px;
  color: #64748B;
  line-height: 1.4;
  max-width: 580px;
}}

.acento-mint {{
  color: #53C1AB;
  font-weight: 700;
}}

/* ================= PÁGINAS DE CONTENIDO (PÁG 2 A 10) ================= */
.seccion-pagina {{
  width: 100%;
  height: 1025px;
  max-height: 1025px;
  page-break-after: always;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 0;
  background: #FFFFFF;
}}

.seccion-pagina:last-child {{
  page-break-after: avoid;
}}

.cabecera-modulo {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #C1E5E4;
  padding-bottom: 7px;
  margin-bottom: 12px;
}}

.cabecera-tag {{
  font-family: 'Space Grotesk', monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #3E91AF;
}}

.cabecera-marca {{
  font-family: 'Space Grotesk', monospace;
  font-size: 8px;
  color: #737373;
}}

.titulo-modulo {{
  font-family: 'Goldman', sans-serif;
  font-size: 21px;
  font-weight: 700;
  color: #0D0D1A;
  margin: 0 0 5px 0;
  line-height: 1.15;
}}

.subtitulo-modulo {{
  font-size: 11px;
  font-weight: 600;
  color: #3E91AF;
  margin: 0 0 12px 0;
  line-height: 1.2;
}}

.modulo-imagen {{
  height: 104px;
  margin: 0 0 12px 0;
  overflow: hidden;
  border-radius: 5px;
  border: 1px solid #D8E5E7;
  background: #0D0D1A;
  position: relative;
}}

.modulo-imagen img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 45%;
  display: block;
  opacity: 0.68;
}}

.modulo-imagen::after {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(13,13,26,0.28), rgba(83,193,171,0.08) 55%, rgba(13,13,26,0.34));
  pointer-events: none;
}}

.cuerpo-modulo {{
  flex: 1;
  display: flex;
  flex-direction: column;
}}

.cuerpo-modulo p {{
  font-size: 12px;
  line-height: 1.52;
  color: #3A3F52;
  margin: 0 0 10px 0;
}}

.cuerpo-modulo h3 {{
  font-family: 'Goldman', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #0D0D1A;
  margin: 12px 0 5px 0;
  letter-spacing: 0.02em;
}}

.cuerpo-modulo ul, .cuerpo-modulo ol {{
  margin: 2px 0 2px 16px;
  padding: 0;
}}

.cuerpo-modulo li {{
  font-size: 11.5px;
  line-height: 1.5;
  color: #3A3F52;
  margin-bottom: 4px;
}}

.cuerpo-modulo strong {{
  color: #0D0D1A;
  font-weight: 700;
}}

.formula {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 12px 0 14px 0;
  padding: 13px 16px;
  border: 1px solid #C1E5E4;
  border-left: 4px solid #53C1AB;
  border-radius: 5px;
  background: #F0FDF9;
  color: #0D0D1A;
  font-family: 'Space Grotesk', monospace;
  font-size: 14px;
  font-weight: 700;
  text-align: center;
}}

.formula-fraccion {{
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}}

.formula-fraccion .numerador {{
  padding: 0 5px 3px 5px;
  border-bottom: 1px solid #0D0D1A;
}}

.formula-fraccion .denominador {{
  padding: 3px 5px 0 5px;
  font-size: 0.88em;
}}

/* Tablas */
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  margin: 10px 0;
  background: #FFFFFF;
  border: 1px solid #D8E5E7;
  border-radius: 4px;
}}

th {{
  background: #F0FDF9;
  color: #176B61;
  font-family: 'Space Grotesk', monospace;
  font-weight: 700;
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid #C1E5E4;
}}

td {{
  padding: 6px 8px;
  border-bottom: 1px solid #E5E7EB;
  color: #3A3F52;
}}

/* Contenedores Gráficos */
.contenedor-diagrama {{
  margin: 10px 0 12px 0;
  width: 100%;
}}

.contenedor-diagrama svg {{
  display: block;
  width: 100%;
  height: auto;
}}

.chart-tv {{
  background: #071317;
  border: 1.5px solid rgba(83, 193, 171, 0.45);
  border-radius: 8px;
  overflow: hidden;
  color: #A8B4C3;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
}}

.chart-tv-topbar {{
  height: 26px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 12px;
  background: #0A1E24;
  border-bottom: 1px solid rgba(83, 193, 171, 0.22);
  font-family: 'Space Grotesk', monospace;
  font-size: 9px;
  white-space: nowrap;
}}

.chart-tv-topbar-left {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

.chart-tv-symbol {{
  color: #FFFFFF;
  font-family: 'Goldman', sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}}

.chart-tv-badge-tf {{
  background: rgba(83, 193, 171, 0.18);
  color: #53C1AB;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 700;
  font-size: 9px;
}}

.chart-tv-badge-feed {{
  background: rgba(16, 185, 129, 0.12);
  color: #6EE7B7;
  border: 1px solid rgba(16, 185, 129, 0.35);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 8.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}

.chart-tv-badge-feed::before {{
  content: "";
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 5px #10B981;
}}

.chart-tv-ohlc {{
  display: inline-flex;
  gap: 6px;
  font-size: 9px;
  color: #8FA2AD;
  margin-left: 6px;
  font-family: 'Space Grotesk', monospace;
}}

.chart-tv-ohlc strong {{
  color: #E2E8F0;
}}

.chart-tv-ohlc .up {{ color: #26A69A; }}
.chart-tv-ohlc .down {{ color: #EF5350; }}

.chart-tv-brand-tv {{
  display: flex;
  align-items: center;
  gap: 5px;
  color: #8FA2AD;
  font-size: 8.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
}}

.chart-tv-legend {{
  height: 22px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  background: #081418;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-family: 'Space Grotesk', monospace;
  font-size: 9px;
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
  color: #8FA2AD;
}}

.chart-tv-leg-val {{
  font-weight: 700;
}}

.chart-tv-wrapper {{
  position: relative;
  width: 100%;
  background: #071317;
  padding-bottom: 0;
}}

.chart-tv-canvas {{
  width: 680px;
  height: 235px;
  display: block;
}}

#usdclp-tv-chart a#tv-attr-logo {{
  display: none !important;
}}

#usdclp-tv-chart table,
#usdclp-tv-chart tr,
#usdclp-tv-chart td {{
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  border-bottom: none !important;
  box-shadow: none !important;
}}

#usdclp-tv-chart tr td[colspan="3"] {{
  background: rgba(83, 193, 171, 0.25) !important;
}}

.chart-tv-caption {{
  height: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 12px;
  color: #94A3B8;
  background: #071317;
  border-top: 1px solid rgba(83, 193, 171, 0.15);
  font-family: 'Space Grotesk', monospace;
  font-size: 8px;
}}

.chart-tv-caption-left {{
  color: #94A3B8;
}}

.chart-tv-caption-right {{
  color: #64748B;
}}

/* Optimización específica de Page Budgeting para Módulo 04 (Gráfico TradingView) */
.seccion-mod-4 .cuerpo-modulo p {{
  margin-bottom: 4px;
  line-height: 1.4;
}}
.seccion-mod-4 .cuerpo-modulo h3 {{
  margin: 6px 0 2px 0;
}}
.seccion-mod-4 .cuerpo-modulo ul {{
  margin: 2px 0 4px 16px;
}}
.seccion-mod-4 .cuerpo-modulo li {{
  margin-bottom: 2px;
}}
.seccion-mod-4 .aviso {{
  margin: 4px 0;
  padding: 6px 12px;
}}
.seccion-mod-4 .contenedor-diagrama {{
  margin: 2px 0 6px 0;
}}

/* Callouts / Avisos */
.aviso {{
  border-radius: 4px;
  padding: 10px 14px;
  margin: 10px 0;
  font-size: 11.5px;
  line-height: 1.5;
}}

.aviso p {{
  margin: 3px 0;
  color: inherit !important;
}}

.aviso strong {{
  color: inherit !important;
}}

/* Footer Página */
.pie-modulo {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #D8E5E7;
  padding-top: 7px;
  margin-top: 10px;
  font-family: 'Space Grotesk', monospace;
  font-size: 8px;
  color: #737373;
}}

.pie-modulo .pie-num {{
  color: #3E91AF;
  font-weight: 700;
}}
"""
