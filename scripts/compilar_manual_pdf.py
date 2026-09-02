#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compilar_manual_pdf.py
Compilador del Manual de Operaciones de Trading Cuantitativo (Motor GI v3.0)
en PDF formal A4 con portada en tono rojizo oscuro/rubí noir alineada al verde de la marca (#50C0A8).
Utiliza Playwright para renderizar tipografías vectoriales y maquetación editorial de alta gama.
"""

import sys
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(r"C:\Users\bbrav\grupo-analisis-mercado")
FONTS_DIR = BASE_DIR / "templates" / "stories" / "fonts"
OUTPUT_PDF_DOCS = BASE_DIR / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"
OUTPUT_PDF_CENTRAL = BASE_DIR / "data central" / "DATA MOTOR GI" / "reportes_generados" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf"

def encode_file(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")

def get_font_faces() -> str:
    catalogo = [
        ("plus-jakarta-sans-400.woff2", "Plus Jakarta Sans", 400),
        ("plus-jakarta-sans-600.woff2", "Plus Jakarta Sans", 600),
        ("plus-jakarta-sans-700.woff2", "Plus Jakarta Sans", 700),
        ("plus-jakarta-sans-800.woff2", "Plus Jakarta Sans", 800),
        ("goldman-400.woff2", "Goldman", 400),
        ("goldman-700.woff2", "Goldman", 700),
        ("space-grotesk-600.woff2", "Space Grotesk", 600),
        ("space-grotesk-700.woff2", "Space Grotesk", 700),
    ]
    reglas = []
    for archivo, familia, peso in catalogo:
        ruta = FONTS_DIR / archivo
        if ruta.exists():
            datos = encode_file(ruta)
            reglas.append(
                f'@font-face {{ font-family: "{familia}"; font-weight: {peso}; '
                f'font-style: normal; font-display: swap; '
                f'src: url(data:font/woff2;base64,{datos}) format("woff2"); }}'
            )
    return "\n".join(reglas)

CSS_STYLES = f"""
{get_font_faces()}

@page {{
    size: A4 portrait;
    margin: 0;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #1A202C;
    background: #CBD5E1;
    -webkit-font-smoothing: antialiased;
}}

.a4-page {{
    width: 794px;
    height: 1123px;
    background: #FFFFFF;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 13mm 15mm;
}}

/* ==========================================================================
   PORTADA ROJIZA NOIR ALINEADA AL VERDE DE MARCA (#50C0A8)
   ========================================================================== */
.a4-cover {{
    width: 794px;
    height: 1123px;
    background: radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 15% 85%, rgba(232, 64, 64, 0.20) 0%, transparent 45%),
                linear-gradient(145deg, #180710 0%, #2A0B1A 45%, #15050D 100%);
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 18mm 16mm;
    color: #FFFFFF;
}}

.cover-grid-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 32px 32px;
    pointer-events: none;
}}

.cover-top {{
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(80, 192, 168, 0.35);
    padding-bottom: 12px;
}}

.cover-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(80, 192, 168, 0.12);
    border: 1px solid #50C0A8;
    color: #50C0A8;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 4px;
}}

.cover-badge-red {{
    background: rgba(232, 64, 64, 0.18);
    border: 1px solid #E84040;
    color: #F87171;
}}

.cover-brand-name {{
    font-family: 'Goldman', sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #FFFFFF;
}}

.cover-center {{
    position: relative;
    z-index: 2;
    margin: auto 0;
}}

.cover-tagline {{
    font-family: 'Space Grotesk', sans-serif;
    color: #50C0A8;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
}}

.cover-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 36px;
    line-height: 1.15;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #FFFFFF;
    margin-bottom: 14px;
}}

.cover-title span {{
    color: #50C0A8;
}}

.cover-subtitle {{
    font-size: 13.5px;
    line-height: 1.5;
    color: #CBD5E1;
    max-width: 580px;
    margin-bottom: 24px;
}}

.cover-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 24px;
}}

.cover-pill {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 11px;
    color: #E2E8F0;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.cover-bottom {{
    position: relative;
    z-index: 2;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    font-size: 10px;
    color: #94A3B8;
}}

.disclaimer-box {{
    background: rgba(232, 64, 64, 0.08);
    border-left: 3px solid #E84040;
    padding: 8px 12px;
    border-radius: 0 4px 4px 0;
    font-size: 9.5px;
    line-height: 1.4;
    color: #E2E8F0;
    max-width: 500px;
}}

/* ==========================================================================
   PÁGINAS INTERNAS
   ========================================================================== */
.page-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #50C0A8;
    padding-bottom: 5px;
    margin-bottom: 10px;
}}

.header-left {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.header-logo {{
    font-family: 'Goldman', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #0F172A;
}}

.header-tag {{
    font-size: 9.5px;
    font-weight: 700;
    color: #50C0A8;
    background: #F0FDF4;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid #50C0A8;
}}

.header-right {{
    font-size: 9.5px;
    color: #64748B;
    font-weight: 600;
}}

.page-footer {{
    border-top: 1px solid #E2E8F0;
    padding-top: 5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9px;
    color: #64748B;
}}

.page-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 9px;
}}

h1.sec-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 15px;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 2px;
}}

h2.sub-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11.5px;
    font-weight: 700;
    color: #0E2420;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 3px;
    margin-bottom: 3px;
}}

p.body-text {{
    font-size: 9.5px;
    line-height: 1.42;
    color: #334155;
}}

/* Grillas y Cajas */
.grid-2col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
}}

.grid-3col {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 7px;
}}

.card {{
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 7px 9px;
}}

.card-accent {{
    border-left: 3px solid #50C0A8;
}}

.card-red {{
    border-left: 3px solid #E84040;
}}

.card-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 10px;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 4px;
}}

.callout-box {{
    background: #F0FDF4;
    border: 1px solid #50C0A8;
    border-radius: 6px;
    padding: 7px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

table.styled-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8.8px;
    text-align: left;
    margin-top: 3px;
}}

table.styled-table th {{
    background: #0E2420;
    color: #FFFFFF;
    font-weight: 700;
    padding: 4.5px 7px;
}}

table.styled-table td {{
    padding: 4px 7px;
    border-bottom: 1px solid #E2E8F0;
    color: #334155;
}}

table.styled-table tr:nth-child(even) {{
    background: #F8FAFC;
}}

/* Gráficos y Visuales de Velas CSS */
.candle-visual-container {{
    display: flex;
    justify-content: space-around;
    align-items: center;
    background: #0A0A0F;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 8px;
    color: #FFFFFF;
    margin-top: 3px;
}}

.candle-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 8px;
    font-family: 'Space Grotesk', sans-serif;
}}

.candle-bar {{
    position: relative;
    width: 22px;
    height: 42px;
    background: #00DC82;
    border-radius: 2px;
    margin: 5px 0;
}}

.candle-bar.red {{
    background: #E84040;
}}

.candle-bar::before {{
    content: '';
    position: absolute;
    top: -7px;
    left: 10px;
    width: 2px;
    height: 7px;
    background: inherit;
}}

.candle-bar::after {{
    content: '';
    position: absolute;
    bottom: -7px;
    left: 10px;
    width: 2px;
    height: 7px;
    background: inherit;
}}

.pill-status {{
    display: inline-block;
    padding: 1.5px 5px;
    border-radius: 3px;
    font-weight: 700;
    font-size: 8px;
}}
.pill-ready {{ background: #DCFCE7; color: #166534; border: 1px solid #00DC82; }}
.pill-armed {{ background: #FEF9C3; color: #854D0E; border: 1px solid #EAB308; }}
.pill-wait {{ background: #F1F5F9; color: #475569; border: 1px solid #94A3B8; }}
.pill-blocked {{ background: #FEE2E2; color: #991B1B; border: 1px solid #E84040; }}
"""

HTML_PAGES = """
<!-- ========================================================================
     PÁGINA 1: PORTADA EN TONO ROJIZO NOIR ALINEADA AL VERDE (#50C0A8)
     ======================================================================== -->
<div class="a4-cover">
    <div class="cover-grid-overlay"></div>
    
    <div class="cover-top">
        <div class="cover-brand-name">GRUPO INTELIGENCIA</div>
        <div style="display: flex; gap: 8px;">
            <div class="cover-badge">MOTOR GI v3.0</div>
            <div class="cover-badge cover-badge-red">FORMATIVO</div>
        </div>
    </div>

    <div class="cover-center">
        <div class="cover-tagline">DIRECCIÓN DE TRADING CUANTITATIVO</div>
        <div class="cover-title">MANUAL DE <span>OPERACIONES</span><br>INTERMERCADO</div>
        <div class="cover-subtitle">
            De la Macroeconomía Real a tu Plataforma MetaTrader 5.<br>
            Aprende a interpretar el clima macroeconómico global, auditar permisos técnicos por régimen y ejecutar con dimensionamiento exacto por volatilidad.
        </div>

        <div class="cover-pills">
            <div class="cover-pill">🏛️ 5 Regímenes Macroeconómicos (R0 a R4)</div>
            <div class="cover-pill">🎯 3 Setups Técnicos Excluyentes en H1</div>
            <div class="cover-pill">🛡️ Dimensionamiento por Volatility Targeting</div>
            <div class="cover-pill">🧭 Máquina de Estados (READY / ARMED / WAIT / BLOCKED)</div>
        </div>
    </div>

    <div class="cover-bottom">
        <div class="disclaimer-box">
            <strong>AVISO INSTITUCIONAL & TRANSPARENCIA:</strong> Material formativo y educativo de control interno. No constituye asesoría de inversión. El motor funciona como asistente analítico en laboratorio (<code>active_strategies: []</code>). Las órdenes son ejecutadas manualmente por el usuario en MT5.
        </div>
        <div style="text-align: right;">
            <div style="color: #FFFFFF; font-weight: 700;">VERSIÓN 3.0.0</div>
            <div>Agosto 2026</div>
        </div>
    </div>
</div>

<!-- ========================================================================
     PÁGINA 2: PARTE I - EL MARCO MENTAL (6 METÁFORAS ECONÓMICAS)
     ======================================================================== -->
<div class="a4-page">
    <div class="page-header">
        <div class="header-left">
            <div class="header-logo">GRUPO INTELIGENCIA</div>
            <div class="header-tag">PARTE I</div>
        </div>
        <div class="header-right">Fundamentos Económicos en Fácil</div>
    </div>

    <div class="page-content">
        <h1 class="sec-title">📖 Las 6 Grandes Verdades del Mercado Global</h1>
        <p class="body-text">Detrás de cada regla matemática de nuestro sistema existe literatura económica canónica. Aquí tienes los 6 pilares explicados a través de analogías cotidianas:</p>

        <div class="grid-2col">
            <div class="card card-accent">
                <div class="card-title">1. Ricitos de Oro (Goldilocks Economy)</div>
                <p class="body-text"><strong>La Metáfora:</strong> La niña elige la sopa que no está ni muy caliente ni muy fría, sino en el punto perfecto.<br>
                <strong>En Finanzas:</strong> Crecimiento económico sólido (cobre sube por demanda fabril) con inflación y tasas controladas. Activa el <strong>Régimen R2</strong>: escenario ideal para acciones tecnológicas (US100) y apreciación del peso chileno (USD/CLP a la baja).</p>
            </div>

            <div class="card card-accent">
                <div class="card-title">2. El Dilema del Oro y Tasas Reales (Erb & Harvey)</div>
                <p class="body-text"><strong>La Metáfora:</strong> El oro es una reserva que no paga dividendos ni arriendos.<br>
                <strong>En Finanzas:</strong> Si el Tesoro de EE.UU. paga una tasa real garantizada atractiva en bonos TIPS 10Y, el dinero prefiere ese interés. Cuando las tasas reales caen o hay crisis militar, el Oro vuela. En R1 y R3 está <strong>prohibido vender Oro en corto</strong>.</p>
            </div>

            <div class="card card-accent">
                <div class="card-title">3. Los 2 Tipos de Petróleo (Lutz Kilian, AER)</div>
                <p class="body-text"><strong>La Metáfora:</strong> Distinguir si el crudo sube por consumo real o por miedo bélico.<br>
                <strong>En Finanzas:</strong> Subida por demanda saludable → bolsas firmes. Subida por guerra o corte de suministro (R3) → encarece costos a empresas y castiga a las bolsas. El motor activa compras tácticas en Petróleo.</p>
            </div>

            <div class="card card-accent">
                <div class="card-title">4. La Verdulería del Cobre y el Peso Chileno (BCCh)</div>
                <p class="body-text"><strong>La Metáfora:</strong> Más del 50% de las exportaciones chilenas son cobre.<br>
                <strong>En Finanzas:</strong> Si el cobre sube en Londres/NY, entran miles de millones de dólares a Chile. Las mineras liquidan dólares para pagar sueldos en pesos → el dólar baja. Si el cobre colapsa (&le; -2.5%), el USD/CLP sube con fuerza.</p>
            </div>

            <div class="card card-accent">
                <div class="card-title">5. La Carretera con Lluvia: Volatility Targeting</div>
                <p class="body-text"><strong>La Metáfora:</strong> Si hay lluvia torrencial, bajas la velocidad a 50 km/h para tener la misma seguridad que a 120 km/h en sol.<br>
                <strong>En Finanzas:</strong> Tu velocidad es el lote. Si el rango de volatilidad (ATR) se duplica, <strong>tú reduces manualmente el lote a la mitad</strong>. Tu riesgo en dinero siempre se mantiene clavado en el <strong>1.0% de tu cuenta</strong>.</p>
            </div>

            <div class="card card-accent">
                <div class="card-title">6. Colas Largas y Tendencias (Moskowitz, JFE)</div>
                <p class="body-text"><strong>La Metáfora:</strong> Las tendencias macro duran más de lo intuitivo.<br>
                <strong>En Finanzas:</strong> Prohibido "adivinar techos" en regímenes de shock solo porque el RSI marque sobrecompra. Se acompaña la estructura con Stop Loss técnico.</p>
            </div>
        </div>

        <div class="callout-box">
            <span style="font-size: 16px;">⚠️</span>
            <div style="font-size: 9px; line-height: 1.4; color: #064E3B;">
                <strong>EL PUENTE ENTRE LA TEORÍA Y TU PANTALLA:</strong> Las analogías explican el <em>porqué</em> económico. Sin embargo, para hacer clic en MT5, <strong>el cuento no es suficiente</strong>: solo abres una posición si el ticket está en estado <strong>READY</strong>. Si está en ARMED, WAIT o BLOCKED, el cuento del cobre no autoriza operar.
            </div>
        </div>
    </div>

    <div class="page-footer">
        <div>Grupo de Análisis de Mercado — Dirección de Trading</div>
        <div>Página 2 de 6</div>
    </div>
</div>

<!-- ========================================================================
     PÁGINA 3: PARTE II - LA BRÚJULA MACRO D1 Y LOS 4 ESTADOS
     ======================================================================== -->
<div class="a4-page">
    <div class="page-header">
        <div class="header-left">
            <div class="header-logo">GRUPO INTELIGENCIA</div>
            <div class="header-tag">PARTE II</div>
        </div>
        <div class="header-right">Brújula Macro D1 & Máquina de Estados</div>
    </div>

    <div class="page-content">
        <h1 class="sec-title">🏛️ Los 5 Regímenes Macro y la Escala de Precedencia</h1>
        <p class="body-text">El modelo cuantitativo clasifica el mercado diario evaluando datos soberanos oficiales bajo una escala estricta de prioridad:</p>

        <div style="text-align: center; font-family: 'Space Grotesk', sans-serif; font-size: 10.5px; font-weight: 700; color: #0F172A; background: #F1F5F9; padding: 5px; border-radius: 4px; border: 1px solid #CBD5E1; margin: 3px 0;">
            Escala: R3 (Estanflación) &succ; R1 (Inflación) &succ; R4 (Recesión) &succ; R2 (Goldilocks) &succ; R0 (Calma)
        </div>

        <table class="styled-table">
            <thead>
                <tr>
                    <th>Régimen</th>
                    <th>Condiciones Oficiales (playbook_config.yaml a 5D)</th>
                    <th>Sesgo y Comportamiento de Activos</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>R3 Estanflación</strong></td>
                    <td>Rally Petróleo &ge; +3.5% <strong>Y</strong> (&Delta; DGS10 &ge; +10 bps o &Delta; TIPS &ge; +8 bps)</td>
                    <td>Oro y Crudo muy fuertes; US100 bajo presión; USD/CLP alcista dólar.</td>
                </tr>
                <tr>
                    <td><strong>R1 Inflación</strong></td>
                    <td>&Delta; Breakeven 10Y &ge; +10 bps <strong>Y</strong> (Curva 2s10s &le; 20 bps o &Delta; 10Y > +5 bps)</td>
                    <td>Oro alcista; Dólar global firme; cautela en acciones.</td>
                </tr>
                <tr>
                    <td><strong>R4 Recesión</strong></td>
                    <td>&Delta; Cobre &le; -2.5% <strong>Y</strong> (Curva 2s10s &lt; 0.0% o Bull Steepener &Delta; 2Y &le; -15 bps)</td>
                    <td>Fuerte alza en USD/CLP (peso débil); materias primas y bolsas en caída.</td>
                </tr>
                <tr>
                    <td><strong>R2 Goldilocks</strong></td>
                    <td>&Delta; Cobre &ge; +1.5% <strong>Y</strong> Tasas Estables (|&Delta; DGS10| &le; 6 bps)</td>
                    <td>Fuerte alza en Nasdaq 100; presión bajista en USD/CLP (peso chileno fuerte).</td>
                </tr>
                <tr>
                    <td><strong>R0 Calma / Rango</strong></td>
                    <td>Variables en equilibrio dinámico sin superación de umbrales</td>
                    <td>Precios rebotan en canales entre Soporte S1 y Resistencia R1.</td>
                </tr>
            </tbody>
        </table>

        <div class="grid-2col" style="margin-top: 3px;">
            <div class="card card-accent">
                <div class="card-title">⚖️ Regla de Precedencia en USD/CLP</div>
                <p class="body-text"><strong>El Régimen Macro siempre manda sobre el Cobre</strong>: En R3 o R4, aunque el cobre suba puntualmente un día +2%, el sesgo en USD/CLP <strong>sigue siendo largo Dólar</strong>. El cobre solo desempata direccionalmente en R0.</p>
            </div>
            <div class="card card-accent">
                <div class="card-title">🛡️ Histéresis Temporal (Anti-Ruido)</div>
                <p class="body-text">Toda transición de régimen requiere <strong>2 observaciones consecutivas en días hábiles (D1)</strong> para confirmarse. Shocks extremos > 150% (ej. Petróleo &ge; +5.25% o Tasas &ge; +15 bps) conmutan de inmediato.</p>
            </div>
        </div>

        <h2 class="sub-title" style="margin-top: 5px;">🎫 La Máquina de Estados del Ticket Cuantitativo (H1)</h2>
        <div class="grid-2col">
            <div class="card" style="border-left: 3px solid #00DC82;">
                <div class="card-title"><span class="pill-status pill-ready">READY</span> Gatillo Confirmado</div>
                <p class="body-text">Vela H1 cerrada cumplió todas las condiciones del setup, confirmación Dow OK y R:R &ge; 1.0. <strong>¡Ingresar orden pendiente en MT5!</strong></p>
            </div>
            <div class="card" style="border-left: 3px solid #EAB308;">
                <div class="card-title"><span class="pill-status pill-armed">ARMED</span> En Observación</div>
                <p class="body-text">Setup habilitado, pero la vela H1 cerrada no activó el gatillo. Precios en <code>null</code>. <strong>Prohibido entrar a mercado por ansiedad</strong>.</p>
            </div>
            <div class="card" style="border-left: 3px solid #94A3B8;">
                <div class="card-title"><span class="pill-status pill-wait">WAIT</span> Espera / Calma</div>
                <p class="body-text">Sin setup elegible o datos incompletos. Cero operaciones. En trading cuantitativo, <em>el silencio vale más que el ruido</em>.</p>
            </div>
            <div class="card" style="border-left: 3px solid #E84040;">
                <div class="card-title"><span class="pill-status pill-blocked">BLOCKED</span> Bloqueo Duro</div>
                <p class="body-text">Bloqueo por spread excesivo (Spread/ATR &gt; c_i), R:R &lt; 1.0 o régimen no confirmado por histéresis. <strong>No operar</strong>.</p>
            </div>
        </div>
    </div>

    <div class="page-footer">
        <div>Grupo de Análisis de Mercado — Dirección de Trading</div>
        <div>Página 3 de 6</div>
    </div>
</div>

<!-- ========================================================================
     PÁGINA 4: PARTE II - LOS 3 SETUPS TÉCNICOS EXCLUSIVOS EN H1
     ======================================================================== -->
<div class="a4-page">
    <div class="page-header">
        <div class="header-left">
            <div class="header-logo">GRUPO INTELIGENCIA</div>
            <div class="header-tag">PARTE II</div>
        </div>
        <div class="header-right">Setups Técnicos Deterministas en H1</div>
    </div>

    <div class="page-content">
        <h1 class="sec-title">🎯 Los 3 Setups Técnicos Oficiales en Gráficos H1</h1>
        <p class="body-text">En temporalidad H1, el motor opera únicamente 3 patrones con reglas matemáticas verificadas sobre velas cerradas:</p>

        <!-- SETUP 1 -->
        <div class="card card-accent">
            <div class="card-title" style="color: #00DC82;">1. BREAKOUT_ADC (Ruptura por Compresión Donchian)</div>
            <div class="grid-2col" style="align-items: center;">
                <div>
                    <p class="body-text">
                        • <strong>Compresión Previa:</strong> Ancho canal Donchian 50 barras &le; 2.5 &times; ATR(H1).<br>
                        • <strong>Vela de Ruptura:</strong> Cierre H1 sobre Donchian High 50 (compras) o bajo Donchian Low 50 (ventas).<br>
                        • <strong>Cuerpo Dominante:</strong> |Close - Open| &ge; 0.5 &times; (High - Low).<br>
                        • <strong>True Range:</strong> TR &ge; 1.0 &times; ATR(H1) y RSI &le; 75 (en compras).<br>
                        • <strong>Orden en MT5:</strong> <code>BUY_STOP</code> 1 tick sobre el High de la vela de ruptura.
                    </p>
                </div>
                <div class="candle-visual-container">
                    <div class="candle-box">
                        <span style="color: #94A3B8;">High (934.00) ─── BUY_STOP</span>
                        <div class="candle-bar"></div>
                        <span style="color: #50C0A8;">Cuerpo = 71% del rango</span>
                        <span style="color: #F87171;">Low (930.50) ─── Stop Loss</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- SETUP 2 -->
        <div class="card card-accent">
            <div class="card-title" style="color: #38BDF8;">2. PULLBACK_EMA (Retroceso a la Media en Tendencia)</div>
            <div class="grid-2col" style="align-items: center;">
                <div>
                    <p class="body-text">
                        • <strong>Tendencia Fuerte:</strong> ADX(14) &ge; 20.0.<br>
                        • <strong>Alineación de Medias:</strong> EMA(20) &gt; EMA(50) &gt; EMA(100) (en compras).<br>
                        • <strong>Gatillo de Rechazo:</strong> La vela H1 perfora intradiariamente la EMA(20) pero <strong>cierra por encima de ella</strong>.<br>
                        • <strong>Orden en MT5:</strong> <code>BUY_STOP</code> sobre el High de la barra de rechazo.
                    </p>
                </div>
                <div class="candle-visual-container">
                    <div class="candle-box">
                        <span style="color: #94A3B8;">High (20,460) ─── BUY_STOP</span>
                        <div class="candle-bar"></div>
                        <span style="color: #38BDF8;">─── EMA 20 (20,380) ───</span>
                        <span style="color: #F87171;">Low (20,360 perforó y rechazó)</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- SETUP 3 -->
        <div class="card card-accent">
            <div class="card-title" style="color: #FBBF24;">3. MEANREV_R0 (Reversión a la Media en Calma)</div>
            <div class="grid-2col" style="align-items: center;">
                <div>
                    <p class="body-text">
                        • <strong>Régimen R0 Estricto:</strong> ADX(14) &lt; 20.0 (ausencia de tendencia).<br>
                        • <strong>Reingreso a Bandas:</strong> Penúltima vela cerró fuera de Bandas Bollinger (20, 2&sigma;); última vela cierra adentro con RSI &lt; 35.0 (en compras).<br>
                        • <strong>Orden en MT5:</strong> <code>BUY_LIMIT</code> al precio de cierre de la barra.<br>
                        • <strong>Salida Obligatoria:</strong> Take Profit 1 exclusivamente en la media central SMA20.
                    </p>
                </div>
                <div class="candle-visual-container">
                    <div class="candle-box">
                        <span style="color: #50C0A8;">TP1 = Media SMA20 (929.00)</span>
                        <div class="candle-bar"></div>
                        <span style="color: #FBBF24;">─── Banda Inferior (923.00) ───</span>
                        <span style="color: #F87171;">SL = Mínimo de excursión (921.00)</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="page-footer">
        <div>Grupo de Análisis de Mercado — Dirección de Trading</div>
        <div>Página 4 de 6</div>
    </div>
</div>

<!-- ========================================================================
     PÁGINA 5: PARTE III - CASOS DE ESTUDIO REALES PASO A PASO
     ======================================================================== -->
<div class="a4-page">
    <div class="page-header">
        <div class="header-left">
            <div class="header-logo">GRUPO INTELIGENCIA</div>
            <div class="header-tag">PARTE III</div>
        </div>
        <div class="header-right">Casos de Estudio Reales Paso a Paso</div>
    </div>

    <div class="page-content">
        <h1 class="sec-title">📊 4 Casos de Estudio Reales en Gráficos</h1>

        <div class="grid-2col">
            <!-- CASO 1 -->
            <div class="card card-accent">
                <div class="card-title">🟢 CASO 1: Ruptura Alcista USD/CLP (R4)</div>
                <p class="body-text">
                    • <strong>Contexto:</strong> Cobre cae -3.2% en COMEX → Régimen R4 Recesión.<br>
                    • <strong>Gráfico H1:</strong> Donchian 50 comprimido a 2.1 × ATR. Vela de 11:00 cierra en 933.50 (rompiendo techo de 933.00) con cuerpo dominante del 71%.<br>
                    • <strong>Ticket READY:</strong> <code>BUY_STOP</code> en 934.00 | SL en 930.50 | TP1 en 938.00.<br>
                    • <strong>Ratio R:R:</strong> 4.00 / 3.50 = 1.14 ≥ 1.0.<br>
                    • <strong>Acción Alumno:</strong> Ingresa orden pendiente dentro del horario bancario (11:05 CLT).
                </p>
            </div>

            <!-- CASO 2 -->
            <div class="card card-accent">
                <div class="card-title">🟢 CASO 2: Pullback en Nasdaq 100 / US100 (R2)</div>
                <p class="body-text">
                    • <strong>Contexto:</strong> Cobre +2.1% y tasas 10Y estables → Régimen R2 Goldilocks.<br>
                    • <strong>Gráfico H1:</strong> EMA20 (20,400) &gt; EMA50 (20,320) &gt; EMA100 (20,200) con ADX = 26.5. Vela perfora a 20,380 pero cierra en 20,440.<br>
                    • <strong>Ticket READY:</strong> <code>BUY_STOP</code> en 20,460 | SL en 20,380 (80 pts) | TP1 en 20,540 (+80 pts).<br>
                    • <strong>Ratio R:R:</strong> 80 / 80 = 1.0 ≥ 1.0.
                </p>
            </div>

            <!-- CASO 3 -->
            <div class="card card-accent">
                <div class="card-title">🟢 CASO 3: Reversión a Media en USD/CLP (R0)</div>
                <p class="body-text">
                    • <strong>Contexto:</strong> Mercado en calma sin noticias → Régimen R0 con ADX = 14.2.<br>
                    • <strong>Gráfico H1:</strong> Penúltima vela cierra bajo banda Bollinger (921.00); última vela reingresa en 924.00 con RSI = 28.0.<br>
                    • <strong>Ticket READY:</strong> <code>BUY_LIMIT</code> en 924.00 | SL en 921.00 (3.00 pesos) | TP1 en media SMA20 (929.00).<br>
                    • <strong>Ratio R:R:</strong> 5.00 / 3.00 = 1.66 ≥ 1.0. Take Profit 2 es <code>null</code>.
                </p>
            </div>

            <!-- CASO 4 -->
            <div class="card card-red">
                <div class="card-title" style="color: #E84040;">🛑 CASO 4: Operación Evitada (Protección)</div>
                <p class="body-text">
                    • <strong>La Tentación:</strong> Vela verde gigante en Oro rompiendo un máximo intradiario a media hora.<br>
                    • <strong>Qué dijo el Motor:</strong> Régimen R0 → <code>BLOCKED (HIGH_FRICTION / UNCONFIRMED)</code>. En R0 está prohibido perseguir rupturas.<br>
                    • <strong>Resultado:</strong> 2 horas después el Oro se devolvió al piso del canal. Los que compraron por impulso quedaron atrapados; el alumno protegió su capital.
                </p>
            </div>
        </div>

        <div class="callout-box" style="margin-top: 3px;">
            <span style="font-size: 16px;">💡</span>
            <div style="font-size: 9px; line-height: 1.4; color: #064E3B;">
                <strong>LECCIÓN CLAVE DE LOS CASOS:</strong> En los 3 casos ganadores, la orden fue colocada <em>después</em> de que la vela H1 cerró y el ticket emitió <strong>READY</strong> con R:R ≥ 1.0. En el caso 4, la disciplina del sistema evitó una pérdida típica de novato.
            </div>
        </div>
    </div>

    <div class="page-footer">
        <div>Grupo de Análisis de Mercado — Dirección de Trading</div>
        <div>Página 5 de 6</div>
    </div>
</div>

<!-- ========================================================================
     PÁGINA 6: PARTE III - EJECUCIÓN EN MT5, SIZING Y CHECKLIST
     ======================================================================== -->
<div class="a4-page">
    <div class="page-header">
        <div class="header-left">
            <div class="header-logo">GRUPO INTELIGENCIA</div>
            <div class="header-tag">PARTE III</div>
        </div>
        <div class="header-right">Ejecución en MT5 & Checklist Diario</div>
    </div>

    <div class="page-content">
        <h1 class="sec-title">⚙️ Dimensionamiento Exacto y Ejecución en MT5</h1>

        <div class="grid-2col">
            <div class="card card-accent">
                <div class="card-title">🔍 1. Dónde leer el Valor del Punto en MT5</div>
                <p class="body-text">
                    1. En la ventana <em>Observación del Mercado</em> de MT5, clic derecho sobre el símbolo (ej. USDCLP) → <strong>Especificación</strong>.<br>
                    2. Revisa <strong>Tamaño del contrato</strong> (ej. 100,000) y <strong>Dígitos</strong> (2).<br>
                    3. Verifica el valor monetario de 1 punto por cada lote estándar.
                </p>
            </div>

            <div class="card card-accent">
                <div class="card-title">📐 2. Fórmula de Lote (1.0% de Riesgo Fijo)</div>
                <p class="body-text">
                    <strong>Fórmula:</strong> Lote = (Capital × 0.01) / (Distancia SL × Valor Punto por Lote)<br>
                    <strong>Ejemplo en USD/CLP:</strong> Cuenta $10,000 USD → Riesgo $100 USD.<br>
                    Entrada 934.00 y SL 930.50 (3.50 pesos). Con valor de $105 USD/lote:<br>
                    <strong>Lote</strong> = 100 / (3.50 × 105) = 100 / 367.50 ≈ <strong>0.27 lotes</strong>
                </p>
            </div>
        </div>

        <div class="grid-3col">
            <div class="card">
                <div class="card-title">🕒 Horario USD/CLP</div>
                <p class="body-text">Solo operar tickets emitidos entre <strong>09:00 y 14:00 CLT</strong> (rueda bancaria de Santiago). Fuera de eso, el READY no se ejecuta.</p>
            </div>
            <div class="card">
                <div class="card-title">🛑 Blackout Manual</div>
                <p class="body-text">El alumno cancela órdenes pendientes 15–30 min antes de noticias Tier-1 (FOMC, NFP, IPC, RPM BCCh).</p>
            </div>
            <div class="card">
                <div class="card-title">📊 Advertencia CFDs</div>
                <p class="body-text">El Tick Volume de MT5 no es volumen real centralizado. Prohibido filtrar con indicadores de volumen.</p>
            </div>
        </div>

        <h2 class="sub-title" style="margin-top: 4px;">📋 Lista de Chequeo Operativa (Checklist de 5 Pasos)</h2>
        <div class="card" style="background: #F8FAFC; border: 1.5px solid #50C0A8;">
            <p class="body-text" style="font-size: 9px; line-height: 1.55;">
                ☑️ <strong>Paso 1: ¿Régimen Macro Confirmado?</strong> Abrir <code>macro_bias_output.json</code> → <code>confirmado_por_historesis == true</code>.<br>
                ☑️ <strong>Paso 2: ¿Ticket en Estado READY?</strong> Abrir <code>tickets_output.json</code> → Solo operar símbolos en <code>READY</code>.<br>
                ☑️ <strong>Paso 3: ¿Filtro Horario y Blackout OK?</strong> USD/CLP entre 09:00 y 14:00 CLT; sin eventos Tier-1 en ± 30 min.<br>
                ☑️ <strong>Paso 4: ¿Lote al 1.0% Calculado?</strong> Aplicar la fórmula con la distancia al Stop Loss estructural.<br>
                ☑️ <strong>Paso 5: ¿Orden Ingresada con Precisión?</strong> Colocar orden pendiente con Entry, SL y TP1 del ticket. Vigencia: 2 velas H1.
            </p>
        </div>

        <div style="text-align: center; margin-top: 2px;">
            <p style="font-family: 'Goldman', sans-serif; font-size: 10.5px; color: #0F172A; letter-spacing: 1px;">
                ¡BUENA DISCIPLINA, CERO OPERACIONES POR IMPULSO Y ESTRICTA GESTIÓN DE RIESGO!
            </p>
        </div>
    </div>

    <div class="page-footer">
        <div>Grupo de Análisis de Mercado — Dirección de Trading</div>
        <div>Página 6 de 6</div>
    </div>
</div>
"""

def generar_html_completo() -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Manual de Operaciones - Motor GI v3.0</title>
    <style>{CSS_STYLES}</style>
</head>
<body>
{HTML_PAGES}
</body>
</html>
"""

def compilar_pdf():
    print("\n" + "=" * 80)
    print("📄 COMPILADOR DE MANUAL DE OPERACIONES EN PDF (Motor GI v3.0)")
    print("🎨 Portada: Ruby Noir / Borgoña + Verde Acento (#50C0A8)")
    print("=" * 80)

    html_content = generar_html_completo()
    
    OUTPUT_PDF_DOCS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PDF_CENTRAL.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 794, "height": 1123})
        page.set_content(html_content, wait_until="networkidle")
        
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
        )

        # Generar preview de portada en PNG
        page.locator('.a4-cover').screenshot(path=str(BASE_DIR / 'docs' / 'preview_portada.png'))
        browser.close()

    OUTPUT_PDF_DOCS.write_bytes(pdf_bytes)
    OUTPUT_PDF_CENTRAL.write_bytes(pdf_bytes)

    print(f"✅ PDF generado exitosamente en:")
    print(f"   • {OUTPUT_PDF_DOCS}")
    print(f"   • {OUTPUT_PDF_CENTRAL}")
    print(f"🖼️  Preview portada: {BASE_DIR / 'docs' / 'preview_portada.png'}")
    print(f"📊 Tamaño: {len(pdf_bytes) / 1024:.1f} KB (6 páginas fijas A4)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    compilar_pdf()
