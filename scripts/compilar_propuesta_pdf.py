#!/usr/bin/env python
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Compila `docs/propuesta_marketing_meta_ads_leads.md` a PDF A4 Institucional.

Genera la versión ejecutiva final con portada oscura Dark Emerald, tipografías
institucionales (Goldman, Plus Jakarta Sans, Space Grotesk) y los artefactos
visuales integrados como diagramas vectoriales nativos.

Uso:
    uv run --with markdown-it-py --with playwright --with pypdf python scripts/compilar_propuesta_pdf.py
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
ORIGEN_MD = RAIZ / "docs" / "propuesta_marketing_meta_ads_leads.md"
DIR_ARTEFACTOS = RAIZ / "docs" / "artefactos_visuales"
SALIDA_PDF = RAIZ / "docs" / "PROPUESTA_CAPTACION_META_ADS_POSTVENTA_GI.pdf"

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
    "critical": ("Alerta Crítica", "#E84040", "rgba(232, 64, 64, 0.08)", "#E84040"),
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


def extraer_svg(nombre_archivo: str) -> str:
    ruta = DIR_ARTEFACTOS / nombre_archivo
    if not ruta.exists():
        return ""
    contenido = ruta.read_text(encoding="utf-8")
    m = re.search(r"(<svg[\s\S]*?</svg>)", contenido)
    if m:
        clase = Path(nombre_archivo).stem
        return f'<div class="contenedor-diagrama diagrama-{clase}">{m.group(1)}</div>'
    return ""


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
        rotulo, color, fondo, borde = TITULOS_CALLOUT[tipo]
        resto = "<p>" + interior[marca.end():]
        return (
            f'<div class="aviso aviso-{tipo}">'
            f'<div class="aviso-rotulo" style="color:{color};">{rotulo}</div>{resto}</div>'
        )

    return patron.sub(reemplazo, html)


def codificar_imagen_base64(nombre_archivo: str) -> str:
    ruta = DIR_ARTEFACTOS / nombre_archivo
    if not ruta.exists():
        return ""
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{datos}"


def construir_panel_evidencia() -> str:
    img_anuncio_gi = codificar_imagen_base64("evidencia_anuncio_gi.png")
    img_form_gi = codificar_imagen_base64("evidencia_formulario_gi.png")
    img_anuncio_befx = codificar_imagen_base64("evidencia_anuncio_befx.png")

    return f"""
<div class="panel-evidencia-grid">
  <div class="tarjeta-evidencia peligro">
    <div class="tag-evidencia tag-peligro">PAUTA ACTIVA GI · META ADS</div>
    <div class="img-marco">
      <img src="{img_anuncio_gi}" alt="Anuncio Activo GI Starbucks">
    </div>
    <div class="pie-evidencia">
      <strong>1. Falla de CTA &amp; Disonancia</strong><br>
      Botón pasivo <em>"Ver detalles"</em> (CTR 0.70%). Conflicto cognitivo con el botón gráfico interno <em>"Habla con un asesor"</em>.
    </div>
  </div>

  <div class="tarjeta-evidencia peligro">
    <div class="tag-evidencia tag-peligro">PUNTO CRÍTICO DE FUGA (GI)</div>
    <div class="img-marco">
      <img src="{img_form_gi}" alt="Formulario Instantáneo GI">
    </div>
    <div class="pie-evidencia">
      <strong>2. Fricción Teclado Abierto</strong><br>
      Pregunta en texto libre: <em>"¿Sabias que puedes invertir en starbucks?"</em>. Provoca <strong>&gt;80% de abandono</strong> en celular sin calificar al lead.
    </div>
  </div>

  <div class="tarjeta-evidencia referencia">
    <div class="tag-evidencia tag-referencia">BENCHMARK COMPETENCIA (BeFX)</div>
    <div class="img-marco">
      <img src="{img_anuncio_befx}" alt="Anuncio Competencia BeFX">
    </div>
    <div class="pie-evidencia">
      <strong>3. Gancho Temático &amp; Blur</strong><br>
      Campaña activa con <em>"Guía USD/CLP"</em> y CTA <em>"Descargar"</em>. Captan agresivamente pero censuran páginas 4 a 10 exigiendo cuenta.
    </div>
  </div>
</div>
"""


def construir_mockup_svg() -> str:
    return """
<div class="contenedor-diagrama diagrama-mockup-movil">
<svg viewBox="0 0 920 435" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparativa Movil: Formulario Starbucks vs Formulario 1-Toque">
  <defs>
    <linearGradient id="bgPhoneGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0C1B20" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#060F12" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="btnMint" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#53C1AB"/>
      <stop offset="100%" stop-color="#3E91AF"/>
    </linearGradient>
    <filter id="glowMint" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- BACKGROUND PANEL -->
  <rect x="0" y="0" width="920" height="435" rx="10" fill="#071418" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>

  <!-- HEADER BAR -->
  <text x="30" y="28" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.15em">AUDITORÍA UX / UI · COMPARATIVA DE EXPERIENCIA MÓVIL</text>
  <text x="30" y="49" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="16.5" font-weight="700" letter-spacing="0.03em">FORMULARIO ACTUAL (TECLADO MANUAL) VS. PROPUESTA 1-TOQUE (AUTOFILL)</text>
  <line x1="30" y1="58" x2="890" y2="58" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <!-- ================= LEFT PHONE: CURRENT STARBUCKS FORM (DANGER) ================= -->
  <g transform="translate(38, 66)">
    <rect x="0" y="0" width="300" height="352" rx="20" fill="url(#bgPhoneGrad)" stroke="#E84040" stroke-width="1.5" filter="url(#glowRed)" stroke-opacity="0.5"/>
    <rect x="0" y="0" width="300" height="352" rx="20" fill="url(#bgPhoneGrad)" stroke="#E84040" stroke-width="1.2"/>

    <!-- Notch & Status -->
    <rect x="105" y="5" width="90" height="12" rx="6" fill="#04090B"/>
    <circle cx="180" cy="11" r="2.5" fill="#1B2E34"/>
    <text x="22" y="16" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">09:41</text>
    <text x="262" y="16" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">5G</text>

    <!-- Meta Header -->
    <rect x="15" y="24" width="270" height="28" rx="4" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <circle cx="32" cy="38" r="8" fill="#1E1212" stroke="#E84040" stroke-width="1"/>
    <text x="32" y="42" text-anchor="middle" fill="#E84040" font-family="'Goldman', sans-serif" font-size="7.5" font-weight="700">GI</text>
    <text x="48" y="35" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5" font-weight="700">Grupo Inteligencia</text>
    <text x="48" y="46" fill="#8FA2AD" font-family="'Plus Jakarta Sans', sans-serif" font-size="8">Formulario instantáneo · Meta Ads</text>
    <text x="270" y="40" fill="#8FA2AD" font-family="sans-serif" font-size="10">✕</text>

    <!-- Badge -->
    <rect x="15" y="57" width="270" height="20" rx="3" fill="rgba(232, 64, 64, 0.18)" stroke="rgba(232, 64, 64, 0.45)" stroke-width="1"/>
    <text x="24" y="71" fill="#FFA5A5" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="700">❌ FORMULARIO ACTUAL (ALTA FRICCIÓN)</text>

    <!-- Question Box -->
    <rect x="15" y="82" width="270" height="126" rx="6" fill="rgba(232, 64, 64, 0.05)" stroke="rgba(232, 64, 64, 0.35)" stroke-width="1"/>
    <text x="25" y="101" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="11.5" font-weight="700">¿Sabias que puedes invertir en starbucks?</text>

    <!-- Free Text Area -->
    <rect x="25" y="112" width="250" height="48" rx="4" fill="#040A0C" stroke="#E84040" stroke-width="1.2" stroke-dasharray="3,3"/>
    <text x="35" y="130" fill="#627782" font-family="'Plus Jakarta Sans', sans-serif" font-size="9" font-style="italic">Escribe tu respuesta aquí...</text>
    <text x="35" y="150" fill="#FFA5A5" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="700">⚠️ Exige abrir teclado táctil y tipear en celular</text>

    <!-- Drop off note -->
    <rect x="25" y="167" width="250" height="30" rx="4" fill="rgba(232, 64, 64, 0.22)"/>
    <text x="32" y="181" fill="#FFCCCC" font-family="'Plus Jakarta Sans', sans-serif" font-size="9" font-weight="700">Fuga &gt;80%: El prospecto no sabe qué responder.</text>
    <text x="32" y="193" fill="#FFA5A5" font-family="'Plus Jakarta Sans', sans-serif" font-size="8">Sin calificación técnica ni patrimonial.</text>

    <!-- Ad Context -->
    <rect x="15" y="214" width="270" height="38" rx="4" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <text x="24" y="229" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="8">ORIGEN: "Tu futuro crece" · CTA "Ver detalles"</text>
    <text x="24" y="244" fill="#E84040" font-family="'Plus Jakarta Sans', sans-serif" font-size="9" font-weight="700">Disonancia: botón confuso y sin gancho tangible</text>

    <!-- Button -->
    <rect x="15" y="258" width="270" height="28" rx="5" fill="#1B272C" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
    <text x="150" y="276" text-anchor="middle" fill="#8FA2AD" font-family="'Plus Jakarta Sans', sans-serif" font-size="10" font-weight="700">Continuar (Incompleto)</text>

    <!-- CPL Pill -->
    <rect x="15" y="294" width="270" height="26" rx="5" fill="rgba(232,64,64,0.18)" stroke="#E84040" stroke-width="1.2"/>
    <text x="150" y="311" text-anchor="middle" fill="#FFA5A5" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="800">CPL ACTUAL REF.: $7.14 – $14.20 USD</text>
  </g>

  <!-- ================= CENTER COMPARISON DIVIDER ================= -->
  <g transform="translate(360, 75)">
    <line x1="100" y1="10" x2="100" y2="330" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2" stroke-dasharray="4,4"/>

    <circle cx="100" cy="38" r="18" fill="#091E24" stroke="#53C1AB" stroke-width="1.8"/>
    <text x="100" y="44" text-anchor="middle" fill="#53C1AB" font-family="'Goldman', sans-serif" font-size="13" font-weight="700">VS</text>

    <rect x="10" y="72" width="180" height="52" rx="5" fill="#0A1D23" stroke="rgba(83, 193, 171, 0.35)" stroke-width="1"/>
    <text x="100" y="88" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="800">MÉTODO DE ENTRADA</text>
    <text x="100" y="103" text-anchor="middle" fill="#E84040" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Teclado táctil manual</text>
    <text x="100" y="117" text-anchor="middle" fill="#53C1AB" font-family="'Plus Jakarta Sans', sans-serif" font-size="10.5" font-weight="700">Selector nativo 1-Toque</text>

    <rect x="10" y="132" width="180" height="52" rx="5" fill="#0A1D23" stroke="rgba(83, 193, 171, 0.35)" stroke-width="1"/>
    <text x="100" y="148" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="800">TIEMPO DE LLENADO</text>
    <text x="100" y="163" text-anchor="middle" fill="#E84040" font-family="'Space Grotesk', monospace" font-size="10">~45 - 60 seg</text>
    <text x="100" y="177" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="800">&lt; 4 segundos</text>

    <rect x="10" y="192" width="180" height="52" rx="5" fill="#0A1D23" stroke="rgba(83, 193, 171, 0.35)" stroke-width="1"/>
    <text x="100" y="208" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="800">CALIFICACIÓN COMERCIAL</text>
    <text x="100" y="223" text-anchor="middle" fill="#E84040" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Nula (prospecto perdido)</text>
    <text x="100" y="237" text-anchor="middle" fill="#53C1AB" font-family="'Plus Jakarta Sans', sans-serif" font-size="10.5" font-weight="700">Activo y Nivel listos</text>

    <rect x="15" y="254" width="170" height="42" rx="5" fill="rgba(83,193,171,0.15)" stroke="#53C1AB" stroke-width="1.2"/>
    <text x="100" y="272" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="800">EFICIENCIA 9.1x LEADS</text>
    <text x="100" y="287" text-anchor="middle" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="8.5">Rescate del 82% de capital</text>
  </g>

  <!-- ================= RIGHT PHONE: PROPOSED 1-TAP FORM (SUCCESS) ================= -->
  <g transform="translate(582, 66)">
    <rect x="0" y="0" width="300" height="352" rx="20" fill="url(#bgPhoneGrad)" stroke="#53C1AB" stroke-width="1.8" filter="url(#glowMint)" stroke-opacity="0.5"/>
    <rect x="0" y="0" width="300" height="352" rx="20" fill="url(#bgPhoneGrad)" stroke="#53C1AB" stroke-width="1.2"/>

    <!-- Notch & Status -->
    <rect x="105" y="5" width="90" height="12" rx="6" fill="#04090B"/>
    <circle cx="180" cy="11" r="2.5" fill="#1B2E34"/>
    <text x="22" y="16" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">09:41</text>
    <text x="262" y="16" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">5G</text>

    <!-- Meta Header -->
    <rect x="15" y="24" width="270" height="28" rx="4" fill="rgba(83,193,171,0.08)" stroke="rgba(83,193,171,0.2)" stroke-width="1"/>
    <circle cx="32" cy="38" r="8" fill="#092620" stroke="#53C1AB" stroke-width="1"/>
    <text x="32" y="42" text-anchor="middle" fill="#53C1AB" font-family="'Goldman', sans-serif" font-size="7.5" font-weight="700">GI</text>
    <text x="48" y="35" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5" font-weight="700">Mesa Técnica · Post Venta</text>
    <text x="48" y="46" fill="#53C1AB" font-family="'Plus Jakarta Sans', sans-serif" font-size="8">Guía Institucional · Descarga Inmediata</text>
    <text x="270" y="40" fill="#8FA2AD" font-family="sans-serif" font-size="10">✕</text>

    <!-- Lead Magnet Banner -->
    <rect x="15" y="57" width="270" height="32" rx="4" fill="linear-gradient(135deg, rgba(83,193,171,0.22), rgba(62,145,175,0.1))" stroke="rgba(83,193,171,0.4)" stroke-width="1"/>
    <text x="24" y="71" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="800">📘 MANUAL DE TRADING CUANTITATIVO</text>
    <text x="24" y="83" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="8" font-weight="600">100% Completo · Sin Bloqueos · Brandkit GI</text>
    <rect x="212" y="60" width="66" height="15" rx="3" fill="#53C1AB"/>
    <text x="245" y="71" text-anchor="middle" fill="#04100D" font-family="'Space Grotesk', monospace" font-size="7.5" font-weight="800">SIN BLUR</text>

    <!-- Question -->
    <text x="18" y="103" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="800">¿QUÉ ACTIVO TE INTERESA OPERAR? (1 CLIC)</text>

    <!-- Option 1: USD/CLP (Selected, NO DIAS) -->
    <rect x="15" y="110" width="270" height="26" rx="4" fill="rgba(83,193,171,0.2)" stroke="#53C1AB" stroke-width="1.4"/>
    <circle cx="28" cy="123" r="5" fill="none" stroke="#53C1AB" stroke-width="1.8"/>
    <circle cx="28" cy="123" r="2.8" fill="#53C1AB"/>
    <text x="42" y="127" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5" font-weight="700">Dólar Observado (USD/CLP) y Cobre</text>
    <rect x="214" y="114" width="65" height="15" rx="3" fill="rgba(83,193,171,0.35)"/>
    <text x="246" y="125" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="7.5" font-weight="800">LOCAL/FX</text>

    <!-- Option 2: Nasdaq (NO DIAS) -->
    <rect x="15" y="140" width="270" height="24" rx="4" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
    <circle cx="28" cy="152" r="5" fill="none" stroke="#627782" stroke-width="1.2"/>
    <text x="42" y="156" fill="#B2C7D1" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Wall Street · Nasdaq 100 y Tech</text>
    <rect x="214" y="144" width="65" height="15" rx="3" fill="rgba(255,255,255,0.06)"/>
    <text x="246" y="155" text-anchor="middle" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="7.5">EQUITIES</text>

    <!-- Option 3: Oro (NO DIAS) -->
    <rect x="15" y="168" width="270" height="24" rx="4" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
    <circle cx="28" cy="180" r="5" fill="none" stroke="#627782" stroke-width="1.2"/>
    <text x="42" y="184" fill="#B2C7D1" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Oro Spot (XAU/USD) &amp; Commodities</text>
    <rect x="214" y="172" width="65" height="15" rx="3" fill="rgba(255,255,255,0.06)"/>
    <text x="246" y="183" text-anchor="middle" fill="#8FA2AD" font-family="'Space Grotesk', monospace" font-size="7.5">REFUGIO</text>

    <!-- Meta Autofill Notice -->
    <rect x="15" y="198" width="270" height="28" rx="4" fill="rgba(83,193,171,0.08)" stroke="rgba(83,193,171,0.2)" stroke-width="1"/>
    <text x="24" y="212" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8" font-weight="700">⚡ AUTOCOMPLETADO NATIVO META:</text>
    <text x="24" y="222" fill="#D2E8E3" font-family="'Plus Jakarta Sans', sans-serif" font-size="8">Nombre, WhatsApp y Correo pre-llenados automáticamente.</text>

    <!-- Screen 2: Direct Download Notice -->
    <rect x="15" y="230" width="270" height="24" rx="4" fill="rgba(62,145,175,0.14)" stroke="rgba(62,145,175,0.3)" stroke-width="1"/>
    <text x="24" y="245" fill="#E2EFF5" font-family="'Plus Jakarta Sans', sans-serif" font-size="8">📥 Pantalla Final: Descarga Inmediata + Envío WA por Comercial.</text>

    <!-- Submit Button -->
    <rect x="15" y="258" width="270" height="30" rx="5" fill="url(#btnMint)" filter="url(#glowMint)"/>
    <text x="150" y="278" text-anchor="middle" fill="#04100D" font-family="'Plus Jakarta Sans', sans-serif" font-size="10.5" font-weight="800">DESCARGAR MANUAL COMPLETO →</text>

    <!-- CPL Pill -->
    <rect x="15" y="294" width="270" height="26" rx="5" fill="rgba(83,193,171,0.18)" stroke="#53C1AB" stroke-width="1.2"/>
    <text x="150" y="311" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="800">CPL PROYECTADO REF.: $0.78 – $1.65 USD</text>
  </g>
</svg>
</div>
"""


def hoja_de_estilos() -> str:
    return f"""
{caras_de_fuente()}

@page {{
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
    @bottom-right {{
        content: counter(page);
        font-family: 'Space Grotesk', monospace;
        font-size: 7.5pt;
        color: #8FA2AD;
    }}
    @bottom-left {{
        content: "GRUPO INTELIGENCIA SPA · ÁREA DE POST VENTA";
        font-family: 'Space Grotesk', monospace;
        font-size: 7.5pt;
        letter-spacing: 0.1em;
        color: #53C1AB;
    }}
}}
@page :first {{ margin: 0; }}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    color: #1A282D;
    font-size: 8.7pt;
    line-height: 1.46;
    background: #FFFFFF;
    -webkit-font-smoothing: antialiased;
}}

/* ── Portada Ejecutiva Oscura ─────────────────────────────── */
.portada {{
    width: 210mm; height: 297mm;
    background: #050E11;
    color: #FFFFFF;
    padding: 24mm 22mm;
    display: flex; flex-direction: column; justify-content: space-between;
    break-after: page;
    position: relative; overflow: hidden;
}}
.portada-glow {{
    position: absolute; inset: 0;
    background:
        radial-gradient(circle at 85% 15%, rgba(83, 193, 171, 0.24) 0%, transparent 60%),
        radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.18) 0%, transparent 60%),
        linear-gradient(135deg, #07171C 0%, #03080A 100%);
    z-index: 0;
}}
.portada-trama {{
    position: absolute; inset: 0;
    background-image:
        linear-gradient(to right, rgba(83, 193, 171, 0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(83, 193, 171, 0.05) 1px, transparent 1px);
    background-size: 28px 28px;
    z-index: 1;
}}
.portada > * {{ position: relative; z-index: 2; }}

.cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(83, 193, 171, 0.3);
    padding-bottom: 14px;
}}
.cover-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.cover-logo-icon {{
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #53C1AB, #3E91AF);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700; font-size: 16px;
    color: #04100D;
}}
.cover-logo-text {{
    font-family: 'Goldman', sans-serif;
    font-size: 14pt; letter-spacing: 0.08em;
    color: #FFFFFF;
}}
.cover-badge {{
    font-family: 'Space Grotesk', monospace;
    font-size: 8pt; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: #53C1AB;
    background: rgba(83, 193, 171, 0.12);
    border: 1px solid rgba(83, 193, 171, 0.35);
    padding: 5px 12px; border-radius: 4px;
}}

.cover-main {{
    margin: auto 0;
    padding: 20px 0;
}}
.cover-tag {{
    font-family: 'Space Grotesk', monospace;
    font-size: 9pt; font-weight: 700;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: #53C1AB;
    margin-bottom: 14px;
}}
.cover-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 27pt; line-height: 1.15;
    letter-spacing: 0.02em;
    color: #FFFFFF;
    margin-bottom: 16px;
}}
.cover-title span {{
    color: #53C1AB;
}}
.cover-sub {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12pt; font-weight: 500; line-height: 1.45;
    color: #B2C7D1;
    max-width: 175mm;
    margin-bottom: 24px;
}}
.cover-meta-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}}
.cover-pill {{
    background: rgba(13, 29, 34, 0.85);
    border: 1px solid rgba(83, 193, 171, 0.25);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 8.5pt;
    color: #E2EFF5;
    display: flex; align-items: center; gap: 8px;
}}
.cover-pill strong {{
    color: #53C1AB;
    font-family: 'Space Grotesk', monospace;
}}

.cover-bottom {{
    border-top: 1px solid rgba(83, 193, 171, 0.2);
    padding-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    font-size: 8.5pt;
    color: #8FA2AD;
}}
.cover-author {{
    color: #FFFFFF;
    font-weight: 600;
}}

/* ── Estructura de Secciones por Página ────────────────────── */
.seccion-pagina {{
    break-after: page;
}}
.seccion-pagina:last-child {{
    break-after: auto;
}}

.cabecera-documento {{
    background: #081418;
    border: 1px solid rgba(83, 193, 171, 0.3);
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 12px;
}}
.cabecera-tag {{
    font-family: 'Space Grotesk', monospace;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #53C1AB;
    margin-bottom: 2px;
}}
.cabecera-titulo {{
    font-family: 'Goldman', sans-serif;
    font-size: 13pt;
    color: #FFFFFF;
    letter-spacing: 0.02em;
}}
.cabecera-meta {{
    font-size: 7.8pt;
    color: #8FA2AD;
    margin-top: 2px;
}}

h1 {{
    display: none;
}}

h2 {{
    font-family: 'Goldman', sans-serif;
    font-size: 13pt;
    color: #081D22;
    border-bottom: 1.5px solid #53C1AB;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 10px;
    letter-spacing: 0.03em;
    break-after: avoid;
}}

h3 {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9.8pt;
    font-weight: 700;
    color: #0E2E36;
    margin-top: 8px;
    margin-bottom: 5px;
    break-after: avoid;
}}

p {{
    margin-bottom: 6px;
    text-align: justify;
}}

ul, ol {{
    margin-left: 18px;
    margin-bottom: 8px;
}}
li {{
    margin-bottom: 3px;
}}

strong {{
    color: #092026;
    font-weight: 700;
}}

/* ── Tablas Institucionales ──────────────────────────────── */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 12px 0;
    font-size: 7.8pt;
    line-height: 1.35;
    break-inside: avoid;
}}
th {{
    background: #092026;
    color: #FFFFFF;
    font-family: 'Space Grotesk', monospace;
    font-size: 7.2pt;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 6px 8px;
    text-align: left;
    border: 1px solid #092026;
}}
td {{
    padding: 5px 8px;
    border: 1px solid #D6E2E6;
    color: #24353B;
}}
tr:nth-child(even) td {{
    background: #F4F8F9;
}}

/* ── Avisos y Callouts ───────────────────────────────────── */
.aviso {{
    border-radius: 5px;
    padding: 8px 12px;
    margin: 8px 0;
    font-size: 8.3pt;
    line-height: 1.4;
    break-inside: avoid;
}}
.aviso-rotulo {{
    font-family: 'Space Grotesk', monospace;
    font-size: 7.2pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 3px;
}}

/* ── Diagramas SVG Embed ─────────────────────────────────── */
.contenedor-diagrama {{
    width: 100%;
    margin: 6px 0;
    padding: 3px;
    background: #081418;
    border: 1px solid rgba(83, 193, 171, 0.35);
    border-radius: 6px;
    break-inside: avoid;
    box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}}
.contenedor-diagrama svg {{
    width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}}
.diagrama-flujo_swimlane_campana svg {{
    max-height: 420px;
}}
.diagrama-mockup-movil svg {{
    max-height: 310px;
}}
.diagrama-cascada_financiera_retorno svg {{
    max-height: 195px;
}}

/* ── Panel de Evidencia Forense (Capturas Reales) ─────────── */
.panel-evidencia-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 8px 0 10px 0;
    break-inside: avoid;
}}
.tarjeta-evidencia {{
    background: #081418;
    border: 1px solid rgba(83, 193, 171, 0.25);
    border-radius: 6px;
    padding: 7px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 3px 8px rgba(0,0,0,0.12);
}}
.tarjeta-evidencia.peligro {{
    border-color: rgba(232, 64, 64, 0.5);
    background: #0B1214;
}}
.tarjeta-evidencia.referencia {{
    border-color: rgba(62, 145, 175, 0.5);
    background: #091519;
}}
.tag-evidencia {{
    font-family: 'Space Grotesk', monospace;
    font-size: 6.8pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 5px;
    padding: 2px 5px;
    border-radius: 3px;
    display: inline-block;
    align-self: flex-start;
}}
.tag-peligro {{
    background: rgba(232, 64, 64, 0.18);
    color: #FFA5A5;
    border: 1px solid rgba(232, 64, 64, 0.4);
}}
.tag-referencia {{
    background: rgba(62, 145, 175, 0.18);
    color: #92D0E6;
    border: 1px solid rgba(62, 145, 175, 0.4);
}}
.img-marco {{
    width: 100%;
    height: 120px;
    background: #040A0C;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
    border: 1px solid rgba(255,255,255,0.06);
}}
.img-marco img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}}
.pie-evidencia {{
    font-size: 7.3pt;
    line-height: 1.32;
    color: #B2C7D1;
}}
.pie-evidencia strong {{
    color: #FFFFFF;
    font-size: 7.7pt;
}}

/* ── Cierre Institucional ────────────────────────────────── */
.cierre-institucional {{
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid #D6E2E6;
    display: flex;
    justify-content: space-between;
    font-size: 7.8pt;
    color: #627782;
}}
.cierre-firma {{
    font-family: 'Space Grotesk', monospace;
    font-weight: 700;
    color: #0E2E36;
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
    <div class="cover-badge">PROPUESTA INTERDEPARTAMENTAL</div>
  </div>

  <div class="cover-main">
    <div class="cover-tag">SISTEMA DE CAPTACIÓN CALIFICADA EN META ADS</div>
    <div class="cover-title">
      SISTEMA DE CAPTACIÓN <span>CALIFICADA EN META ADS</span>
    </div>
    <div class="cover-sub">
      Reingeniería del embudo publicitario en Facebook e Instagram, entrega de guías educativas
      100% completas bajo Brandkit, modelo econométrico de rescate del 82% del presupuesto y protocolo de
      sales enablement para la fuerza comercial.
    </div>
    <div class="cover-meta-pills">
      <div class="cover-pill"><strong>ÁREA:</strong> Post Venta &amp; Análisis</div>
      <div class="cover-pill"><strong>DESTINO:</strong> Gerencia General &amp; Comercial</div>
      <div class="cover-pill"><strong>AUDITORÍA:</strong> Meta Ad Library &amp; Ads Manager</div>
      <div class="cover-pill"><strong>ESTÁNDAR:</strong> Dark Emerald Glass Terminal</div>
    </div>
  </div>

  <div class="cover-bottom">
    <div>
      <div class="cover-author">Área de Post Venta y Análisis de Mercado</div>
      <div>Plataforma de Inteligencia Cuantitativa · Chile</div>
    </div>
    <div style="text-align: right;">
      <div style="color: #53C1AB; font-family: 'Space Grotesk', monospace; font-weight:700;">CONFIDENCIAL INSTITUCIONAL</div>
      <div>Documento de Diseño y Viabilidad · Septiembre 2026</div>
    </div>
  </div>
</div>
"""


def renderizar_markdown(texto: str) -> str:
    from markdown_it import MarkdownIt

    svg_swimlane = extraer_svg("flujo_swimlane_campana.html")
    svg_cascada = extraer_svg("cascada_financiera_retorno.html")
    svg_mockup = construir_mockup_svg()
    panel_evidencia = construir_panel_evidencia()

    # Dividir el markdown en secciones separadas por '---'
    bloques = [b.strip() for b in texto.split("\n---") if b.strip()]

    md = MarkdownIt("commonmark", {"html": True, "breaks": False}).enable("table")

    secciones_html = []
    for i, bloque in enumerate(bloques):
        # Inyectar artefactos antes o después del render según corresponda
        html_bloque = md.render(bloque)

        # Inyectar reemplazos
        html_bloque = html_bloque.replace("<!-- PANEL_EVIDENCIA_FORENSE -->", panel_evidencia)
        html_bloque = html_bloque.replace("<!-- TOKEN_SWIMLANE -->", svg_swimlane)
        html_bloque = html_bloque.replace("<!-- TOKEN_MOCKUP_MOVIL -->", svg_mockup)
        html_bloque = html_bloque.replace("<!-- TOKEN_CASCADA -->", svg_cascada)
        html_bloque = procesar_callouts(html_bloque)

        if i == 0:
            # Encabezado introductorio + Sección 1 en Página 2
            cabecera = """
<div class="cabecera-documento">
  <div class="cabecera-tag">PROPUESTA INTERDEPARTAMENTAL · POST VENTA &amp; ANÁLISIS</div>
  <div class="cabecera-titulo">REINGENIERÍA DEL EMBUDO PUBLICITARIO EN META ADS</div>
  <div class="cabecera-meta">Grupo Inteligencia SpA · 10 de Septiembre 2026 · Destino: Gerencia General, Dirección Comercial y Marketing</div>
</div>
"""
            # El bloque 0 es el título inicial, y el bloque 1 es la Sección 1
            continue
        elif i == 1:
            # Página 2: Cabecera + Sección 1
            secciones_html.append(f'<section class="seccion-pagina seccion-1">\n{cabecera}\n{html_bloque}\n</section>')
        else:
            # Páginas 3, 4, 5, 6
            num_sec = i
            secciones_html.append(f'<section class="seccion-pagina seccion-{num_sec}">\n{html_bloque}\n</section>')

    return "\n".join(secciones_html)


def construir_html() -> str:
    if not ORIGEN_MD.exists():
        raise SystemExit(f"No existe el archivo markdown: {ORIGEN_MD}")

    cuerpo = renderizar_markdown(ORIGEN_MD.read_text(encoding="utf-8"))
    return (
        "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<title>Sistema de Captación Calificada en Meta Ads · Grupo Inteligencia</title>\n"
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
    print("\n✅ OK: Propuesta ejecutiva compilada exitosamente a PDF.")
    return 0


if __name__ == "__main__":
    raise SystemExit(compilar_pdf())

