#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compilar_informe_cierre_semanal.py
Compilador oficial de Informes de Cierre Semanal en PDF A4 de 5 páginas fijas.
Incrusta gráficos a 300 DPI en Base64 y garantiza una diagramación editorial perfecta.
"""

import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent if "scripts" in str(Path(__file__).resolve()) else Path(r"C:\Users\bbrav\grupo-analisis-mercado")
FONTS_DIR = RAIZ / "templates" / "stories" / "fonts"
GRAFICOS_DIR = RAIZ / "data" / "informes" / "2026-08-28_cierre" / "graficos"
OUTPUT_PDF = RAIZ / "data central" / "DATA USA" / "reportes_generados" / "informe_cierre_semanal_20260828_GI.pdf"
PRECIOS_FILE = RAIZ / "data central" / "DATA PRECIOS OHLC" / "latest_prices_summary.json"

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
    ]
    reglas = []
    for archivo, familia, peso in catalogo:
        ruta = FONTS_DIR / archivo
        if ruta.exists():
            datos = encode_file(ruta)
            reglas.append(
                f'@font-face{{font-family:"{familia}";font-weight:{peso};'
                f'font-style:normal;font-display:swap;'
                f'src:url(data:font/woff2;base64,{datos}) format("woff2");}}'
            )
    return "\n".join(reglas)

# Cargar imágenes Base64
img_usdclp = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'usdclp.png')}"
img_xauusd = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'xauusd.png')}"
img_copper = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'copper.png')}"
img_us100 = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'us100.png')}"
img_wti = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'wti.png')}"
img_usdjpy = f"data:image/png;base64,{encode_file(GRAFICOS_DIR / 'usdjpy.png')}"

# CSS Global de Maquetación Editorial A4
CSS_DOCUMENT = f"""
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
    color: #2D3748;
    background: #E2E8F0;
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
    padding: 16mm 20mm;
}}

/* Encabezados y Pies de página institucionales */
.page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #50C0A8;
    margin-bottom: 12px;
}}

.page-header-left {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #3E91AF;
    text-transform: uppercase;
}}

.page-header-right {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 8.5px;
    font-weight: 600;
    color: #718096;
    letter-spacing: 0.05em;
}}

.page-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid #E2E8F0;
    margin-top: 10px;
    font-size: 8.5px;
    color: #718096;
}}

.page-footer-left {{
    font-weight: 700;
    color: #50C0A8;
    letter-spacing: 0.08em;
}}

.page-footer-right {{
    font-weight: 600;
}}

/* Tipografía de Contenido */
.section-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #0B1916;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.section-title::before {{
    content: "";
    display: inline-block;
    width: 4px;
    height: 14px;
    background: #50C0A8;
    border-radius: 2px;
}}

.body-p {{
    font-size: 10.5px;
    line-height: 1.55;
    color: #334155;
    margin-bottom: 8px;
    text-align: justify;
}}

.highlight-box {{
    background: #F0FDF4;
    border-left: 3.5px solid #50C0A8;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 12px;
}}

.highlight-box p {{
    font-size: 10px;
    line-height: 1.5;
    color: #166534;
    font-weight: 500;
}}

/* Tablas estilizadas */
.table-custom {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 14px 0;
    font-size: 9.5px;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.table-custom th {{
    background: #0B1916;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 9px;
    letter-spacing: 0.04em;
    padding: 7px 10px;
    text-align: left;
    border-bottom: 2px solid #50C0A8;
}}

.table-custom td {{
    padding: 6.5px 10px;
    border-bottom: 1px solid #E2E8F0;
    color: #334155;
    vertical-align: middle;
}}

.table-custom tr:nth-child(even) td {{
    background: #F8FAFC;
}}

.table-custom tr:last-child td {{
    border-bottom: none;
}}

/* Fichas de Activos */
.asset-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}}

.asset-card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}

.asset-card-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 800;
    color: #0B1916;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.asset-badge {{
    font-family: 'Goldman', sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
}}

.badge-up {{ background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }}
.badge-down {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }}

.asset-chart-img {{
    width: 100%;
    height: 145px;
    object-fit: contain;
    border-radius: 4px;
    border: 1px solid #CBD5E1;
    margin: 4px 0 8px 0;
    background: #FFFFFF;
    display: block;
}}

.three-layers {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 9.5px;
    line-height: 1.45;
}}

.layer-item {{
    display: flex;
    gap: 6px;
}}

.layer-label {{
    font-weight: 800;
    color: #0F172A;
    min-width: 135px;
}}

.layer-prohibited {{
    color: #991B1B;
    background: #FEF2F2;
    padding: 2px 6px;
    border-radius: 4px;
    border-left: 3px solid #DC2626;
}}

/* Portada Estilo Editorial Oscuro */
.cover-page {{
    background: #04100D;
    color: #FFFFFF;
    padding: 24mm 22mm;
    justify-content: space-between;
}}

.cover-bg-glow {{
    position: absolute;
    top: 0; right: 0; bottom: 0; left: 0;
    background: radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.22) 0%, transparent 65%),
                radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.16) 0%, transparent 60%),
                linear-gradient(135deg, #061814 0%, #020806 100%);
    z-index: 0;
}}

.cover-content {{
    position: relative;
    z-index: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(80, 192, 168, 0.3);
    padding-bottom: 14px;
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
    font-size: 16px;
    color: #04100D;
}}

.cover-logo-text {{
    font-family: 'Goldman', sans-serif;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #FFFFFF;
}}

.cover-badge {{
    background: rgba(80, 192, 168, 0.15);
    border: 1px solid rgba(80, 192, 168, 0.4);
    color: #50C0A8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    padding: 5px 14px;
    border-radius: 100px;
}}

.cover-hero {{
    margin: 20px 0;
}}

.cover-kicker {{
    font-size: 11px;
    font-weight: 700;
    color: #3E91AF;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

.cover-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.18;
    color: #FFFFFF;
    margin-bottom: 12px;
}}

.cover-title span {{ color: #50C0A8; }}

.cover-subtitle {{
    font-size: 12.5px;
    color: #C1E5E4;
    line-height: 1.55;
    max-width: 90%;
    margin-bottom: 16px;
}}

.cover-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 14px;
}}

.cover-card {{
    background: rgba(8, 28, 23, 0.7);
    border: 1px solid rgba(80, 192, 168, 0.25);
    border-radius: 8px;
    padding: 10px 12px;
}}

.cover-card-header {{
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #94A3B8;
    font-weight: 700;
    margin-bottom: 4px;
}}

.cover-card-price {{
    font-family: 'Goldman', sans-serif;
    font-size: 18px;
    color: #FFFFFF;
    font-weight: 700;
}}

.cover-card-driver {{
    font-size: 9px;
    color: #718096;
    margin-top: 4px;
    line-height: 1.35;
}}

/* Escenarios */
.scenario-card {{
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
}}

.scenario-pos {{ background: #F0FDF4; border: 1px solid #86EFAC; border-left: 4px solid #16A34A; }}
.scenario-base {{ background: #FEFCE8; border: 1px solid #FDE047; border-left: 4px solid #CA8A04; }}
.scenario-risk {{ background: #FEF2F2; border: 1px solid #FCA5A5; border-left: 4px solid #DC2626; }}

.scenario-title {{
    font-size: 10.5px;
    font-weight: 800;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.scenario-pos .scenario-title {{ color: #15803D; }}
.scenario-base .scenario-title {{ color: #A16207; }}
.scenario-risk .scenario-title {{ color: #B91C1C; }}

.scenario-bullets {{
    font-size: 9.5px;
    color: #334155;
    line-height: 1.45;
    padding-left: 14px;
}}
"""

HTML_INFORME = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>{CSS_DOCUMENT}</style>
</head>
<body>

<!-- PÁGINA 1: PORTADA & SÍNTESIS EJECUTIVA -->
<div class="a4-page cover-page">
    <div class="cover-bg-glow"></div>
    <div class="cover-content">
        <div class="cover-top">
            <div class="cover-logo">
                <div class="cover-logo-icon">GI</div>
                <div class="cover-logo-text">GRUPO INTELIGENCIA</div>
            </div>
            <div class="cover-badge">INFORME OFICIAL · CIERRE SEMANAL</div>
        </div>

        <div class="cover-hero">
            <div class="cover-kicker">RESEARCH INTERMERCADO · EDICIÓN CIERRE DE SEMANA</div>
            <h1 class="cover-title">Régimen de Rigidez en Tasas y <span>Auge Estructural en IA</span></h1>
            <p class="cover-subtitle">Balance financiero tras las declaraciones de Kevin Warsh en Jackson Hole: la Reserva Federal ratifica su compromiso con la meta de inflación del 2.0%, anclando las tasas soberanas mientras el gasto en Inteligencia Artificial impulsa al Cobre y a la renta variable tecnológica.</p>
        </div>

        <div style="background: rgba(11, 35, 29, 0.8); border: 1px solid rgba(80, 192, 168, 0.35); border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;">
            <div style="font-family:'Goldman',sans-serif; font-size:12px; font-weight:700; color:#50C0A8; letter-spacing:0.06em; margin-bottom:6px;">01. RESUMEN EJECUTIVO & BALANCE MONETARIO</div>
            <p style="font-size:10px; line-height:1.55; color:#E2E8F0; text-align:justify;">
                La semana que concluye este 28 de agosto de 2026 confirmó que el banco central estadounidense no aplicará recortes prematuros de tasas de interés. Con más del 54% de la canasta del deflactor PCE creciendo sobre el 3.0% anual y el PCE núcleo en 3.7%, el rendimiento del bono del Tesoro a 10 años se consolidó en 4.66%. A pesar de la firmeza del dólar global, el auge de inversión en centros de datos (+9.0% Cap-Ex YoY) y el crecimiento de utilidades corporativas del S&P 500 (+20.0% YoY) absorbieron el costo financiero, permitiendo ganancias semanales en el Nasdaq 100 (+0.68%) y en el Cobre (+0.51%).
            </p>
        </div>

        <div>
            <div style="font-family:'Goldman',sans-serif; font-size:11px; font-weight:700; color:#3E91AF; letter-spacing:0.08em; margin-bottom:6px;">SNAPSHOT SEMANAL DE ACTIVOS CLAVE (MT5 W1)</div>
            <div class="cover-grid">
                <div class="cover-card">
                    <div class="cover-card-header"><span>🇨🇱 USD/CLP</span><span style="color:#4ADE80;">▲ +1.83%</span></div>
                    <div class="cover-card-price">$931.55</div>
                    <div class="cover-card-driver">Rango $912 - $932.50. Soporte en Cobre.</div>
                </div>
                <div class="cover-card">
                    <div class="cover-card-header"><span>⚡ COBRE HG</span><span style="color:#4ADE80;">▲ +0.51%</span></div>
                    <div class="cover-card-price">$14,251.0</div>
                    <div class="cover-card-driver">Demanda física por Cap-Ex de IA.</div>
                </div>
                <div class="cover-card">
                    <div class="cover-card-header"><span>🥇 ORO SPOT</span><span style="color:#F87171;">▼ -3.38%</span></div>
                    <div class="cover-card-price">$4,454.26</div>
                    <div class="cover-card-driver">Presión por alza en TIPS real (2.34%).</div>
                </div>
                <div class="cover-card">
                    <div class="cover-card-header"><span>📱 NASDAQ 100</span><span style="color:#4ADE80;">▲ +0.68%</span></div>
                    <div class="cover-card-price">29,463.14</div>
                    <div class="cover-card-driver">Impulsado por megacaps de IA.</div>
                </div>
                <div class="cover-card">
                    <div class="cover-card-header"><span>⛽ PETRÓLEO WTI</span><span style="color:#F87171;">▼ -3.45%</span></div>
                    <div class="cover-card-price">$83.82</div>
                    <div class="cover-card-driver">Consolidación (Brent $89.79 / -4.12%).</div>
                </div>
                <div class="cover-card">
                    <div class="cover-card-header"><span>💴 USD/JPY</span><span style="color:#4ADE80;">▲ +0.75%</span></div>
                    <div class="cover-card-price">160.080</div>
                    <div class="cover-card-driver">Quiebre de 160; riesgo directo MOF.</div>
                </div>
            </div>
        </div>

        <div style="border-top:1px solid rgba(255,255,255,0.18); padding-top:10px; display:flex; justify-content:space-between; align-items:center; font-size:9.5px; color:#94A3B8;">
            <div>FECHA: <strong style="color:#FFFFFF;">28 de agosto de 2026</strong> · ANALISTA: <strong style="color:#FFFFFF;">Área de Research & Estrategia</strong></div>
            <div style="font-family:'Goldman',sans-serif; color:#50C0A8; font-weight:700;">PÁGINA 01 / 05</div>
        </div>
    </div>
</div>

<!-- PÁGINA 2: CURVA SOBERANA DE EE.UU. Y USD/CLP -->
<div class="a4-page">
    <div>
        <div class="page-header">
            <span class="page-header-left">RESEARCH INTERMERCADO · CIERRE SEMANAL</span>
            <span class="page-header-right">VIERNES 28 DE AGOSTO DE 2026</span>
        </div>

        <div class="section-title">02. Curva Soberana de EE.UU. y Transmisión de Tasas</div>
        <p class="body-p">
            La estructura temporal de los rendimientos del Tesoro de EE.UU. refleja la asimilación del discurso de Kevin Warsh en Jackson Hole. Al consolidar una tasa terminal neutra más elevada, los tramos a 2 y 10 años operan en máximos del mes, manteniendo la curva en pendiente positiva no invertida (+47 bps) coherente con un ciclo de expansión económica.
        </p>

        <table class="table-custom">
            <thead>
                <tr>
                    <th>Instrumento / Tramo Soberano</th>
                    <th>Nivel Actual</th>
                    <th>Cambio 1D</th>
                    <th>Cambio 5D (Semana)</th>
                    <th>Lectura & Diagnóstico Oficial</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Bono del Tesoro a 2 años (DGS2)</strong></td>
                    <td><strong>4.19%</strong></td>
                    <td>+2.0 bps</td>
                    <td><strong>0.0 bps</strong></td>
                    <td>Anclado ante compromiso firme contra la inflación.</td>
                </tr>
                <tr>
                    <td><strong>Bono del Tesoro a 10 años (DGS10)</strong></td>
                    <td><strong>4.66%</strong></td>
                    <td>+2.0 bps</td>
                    <td><strong>+1.0 bps</strong></td>
                    <td>Tasa de referencia global firme en máximos mensuales.</td>
                </tr>
                <tr>
                    <td><strong>Bono del Tesoro a 30 años (DGS30)</strong></td>
                    <td><strong>5.18%</strong></td>
                    <td>+1.0 bps</td>
                    <td><strong>-1.0 bps</strong></td>
                    <td>Prima por plazo contenida en el tramo ultralargo.</td>
                </tr>
                <tr>
                    <td><strong>Tasa real a 10 años (TIPS · DFII10)</strong></td>
                    <td><strong>2.34%</strong></td>
                    <td>+2.0 bps</td>
                    <td><strong>-1.0 bps</strong></td>
                    <td>Costo real del dinero sólidamente restrictivo.</td>
                </tr>
                <tr>
                    <td><strong>Inflación esperada 10 años (T10YIE)</strong></td>
                    <td><strong>2.33%</strong></td>
                    <td>+1.0 bps</td>
                    <td><strong>-1.0 bps</strong></td>
                    <td>Expectativas ancladas cerca del objetivo de la Fed.</td>
                </tr>
                <tr>
                    <td><strong>Diferencial Curva 10Y - 2Y (Spread)</strong></td>
                    <td><strong>+0.47%</strong></td>
                    <td>0.0 bps</td>
                    <td><strong>+1.0 bps</strong></td>
                    <td>Curva no invertida (+47 bps), reflejando crecimiento.</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">03. Análisis Técnico y Transmisión por Activo</div>
        
        <!-- FICHA USD/CLP -->
        <div class="asset-card">
            <div class="asset-card-header">
                <span class="asset-card-title">🇨🇱 Dólar / Peso Chileno (USD/CLP · Spot: $931.55)</span>
                <span class="asset-badge badge-up">▲ +1.83% SEMANAL</span>
            </div>
            <img class="asset-chart-img" src="{img_usdclp}" alt="Gráfico D1 USD/CLP" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Avanzó de $914.85 a $931.55 (+1.83%). La solidez del DXY tras Jackson Hole presionó alzas tácticas, contenidas por el precio del Cobre.</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Rango de equilibrio entre $912.00 y $932.50. Compras tácticas en soporte ($915 - $920) ofrecen ratio R/R óptimo hacia $935.00.</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido comprar en rompimiento alcista ciego (Breakout Chase Long) por sobrecompra relativa en H1 (RSI 72.3).</span>
                </div>
            </div>
        </div>
    </div>

    <div class="page-footer">
        <span class="page-footer-left">GRUPO INTELIGENCIA · RESEARCH & ESTRATEGIA</span>
        <span class="page-footer-right">PÁGINA 02 / 05</span>
    </div>
</div>

<!-- PÁGINA 3: COMMODITIES Y MATERIAS PRIMAS -->
<div class="a4-page">
    <div>
        <div class="page-header">
            <span class="page-header-left">RESEARCH INTERMERCADO · COMMODITIES & METALES</span>
            <span class="page-header-right">VIERNES 28 DE AGOSTO DE 2026</span>
        </div>

        <!-- FICHA ORO SPOT -->
        <div class="asset-card">
            <div class="asset-card-header">
                <span class="asset-card-title">🥇 Oro Spot (XAU/USD · Spot: $4,454.26 USD/oz)</span>
                <span class="asset-badge badge-down">▼ -3.38% SEMANAL</span>
            </div>
            <img class="asset-chart-img" src="{img_xauusd}" alt="Gráfico D1 Oro Spot" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Corrigió desde $4,610.17 hasta $4,454.26 (-3.38%) ante el repunte de rendimientos reales en bonos TIPS (2.34%).</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Soporte clave en $4,445.00 (Donchian H1) y resistencia en $4,575.00. Compras escalonadas en zonas de soporte estructural.</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido vender en corto agresivo sin quiebre confirmado de $4,400, dada la presencia de demanda institucional.</span>
                </div>
            </div>
        </div>

        <!-- FICHA COBRE HG -->
        <div class="asset-card">
            <div class="asset-card-header">
                <span class="asset-card-title">⚡ Cobre de Alta Pureza (COPPER · Spot: $14,251.0 USD/t / $6.70 USD/lb)</span>
                <span class="asset-badge badge-up">▲ +0.51% SEMANAL</span>
            </div>
            <img class="asset-chart-img" src="{img_copper}" alt="Gráfico D1 Cobre HG" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Cerró en $14,251.0 USD/t (+0.51%). El Cap-Ex en infraestructura de IA (+9.0% anual) garantiza una demanda física sostenida.</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Soporte en $14,142 USD/t y proyección a $14,500 USD/t. Mantiene tendencia primaria alcista en gráfico diario.</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido abrir ventas en corto contra la tendencia primaria de materias primas industriales.</span>
                </div>
            </div>
        </div>

        <!-- FICHA PETRÓLEO WTI -->
        <div class="asset-card" style="margin-bottom:0;">
            <div class="asset-card-header">
                <span class="asset-card-title">⛽ Petróleo Crudo WTI (WTI.spot · Spot: $83.82 / Brent: $89.79)</span>
                <span class="asset-badge badge-down">▼ -3.45% SEMANAL</span>
            </div>
            <img class="asset-chart-img" src="{img_wti}" alt="Gráfico D1 Petróleo WTI" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Retrocedió de $86.82 a $83.82 (-3.45% / Brent -4.12%), consolidando ganancias ante la estabilización de inventarios.</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Rango de consolidación entre $81.00 y $84.60. Soporte dinámico en la EMA 50 H1 ($83.25).</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido operar sin stop loss en energía debido a la alta volatilidad de fin de semana.</span>
                </div>
            </div>
        </div>
    </div>

    <div class="page-footer">
        <span class="page-footer-left">GRUPO INTELIGENCIA · RESEARCH & ESTRATEGIA</span>
        <span class="page-footer-right">PÁGINA 03 / 05</span>
    </div>
</div>

<!-- PÁGINA 4: RENTA VARIABLE Y DIVISAS GLOBALES -->
<div class="a4-page">
    <div>
        <div class="page-header">
            <span class="page-header-left">RESEARCH INTERMERCADO · EQUITY & FX GLOBAL</span>
            <span class="page-header-right">VIERNES 28 DE AGOSTO DE 2026</span>
        </div>

        <!-- FICHA NASDAQ 100 -->
        <div class="asset-card" style="margin-bottom:14px;">
            <div class="asset-card-header">
                <span class="asset-card-title">📱 Nasdaq 100 (US100.spot · Cierre: 29,463.14 puntos)</span>
                <span class="asset-badge badge-up">▲ +0.68% SEMANAL</span>
            </div>
            <img class="asset-chart-img" style="height:175px;" src="{img_us100}" alt="Gráfico D1 Nasdaq 100" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Avanzó de 29,262.78 a 29,463.14 (+0.68%). Las utilidades corporativas del S&P 500 (+20.0% YoY) absorbieron las tasas altas sin comprimir múltiplos.</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Soporte en 29,155.00 y resistencia en 29,760.00. La estructura técnica favorece compras en retrocesos hacia la media móvil de 50 periodos.</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido sobreapalancar posiciones largas cerca del techo de los 29,760 puntos sin gestión estricta de riesgo.</span>
                </div>
            </div>
        </div>

        <!-- FICHA USD/JPY -->
        <div class="asset-card" style="margin-bottom:0;">
            <div class="asset-card-header">
                <span class="asset-card-title">💴 Dólar / Yen Japonés (USD/JPY · Spot: 160.080)</span>
                <span class="asset-badge badge-up">▲ +0.75% SEMANAL</span>
            </div>
            <img class="asset-chart-img" style="height:175px;" src="{img_usdjpy}" alt="Gráfico D1 USD/JPY" />
            <div class="three-layers">
                <div class="layer-item">
                    <span class="layer-label">📌 Qué está pasando:</span>
                    <span>Subió de 158.89 a 160.080 (+0.75%), quebrando la barrera psicológica de 160.000 y activando alerta máxima de intervención cambiaria del MOF.</span>
                </div>
                <div class="layer-item">
                    <span class="layer-label">💡 Qué significa para ti:</span>
                    <span>Resistencia en 160.150 y soporte en 159.410 (EMA 50 H1). Riesgo extremo de volatilidad bajista súbita si Tokio ejecuta ventas de reservas.</span>
                </div>
                <div class="layer-item layer-prohibited">
                    <span class="layer-label">🚫 Qué NO operar hoy:</span>
                    <span>Prohibido perseguir compras en el quiebre de 160.000 (Riesgo extremo de intervención cambiaria directa).</span>
                </div>
            </div>
        </div>
    </div>

    <div class="page-footer">
        <span class="page-footer-left">GRUPO INTELIGENCIA · RESEARCH & ESTRATEGIA</span>
        <span class="page-footer-right">PÁGINA 04 / 05</span>
    </div>
</div>

<!-- PÁGINA 5: MATRIZ DE ESCENARIOS, RADAR & DISCLAIMER -->
<div class="a4-page">
    <div>
        <div class="page-header">
            <span class="page-header-left">RESEARCH INTERMERCADO · ESCENARIOS & MARCO LEGAL</span>
            <span class="page-header-right">VIERNES 28 DE AGOSTO DE 2026</span>
        </div>

        <div class="section-title">04. Matriz de Escenarios Operativos para la Próxima Semana</div>
        
        <div class="scenario-card scenario-pos">
            <div class="scenario-title">🟢 ESCENARIO POSITIVO (EXPANSIVO · PROBABILIDAD 35%)</div>
            <ul class="scenario-bullets">
                <li>Datos del ISM Manufacturero en EE.UU. confirman ganancias de productividad aceleradas por adopción de IA.</li>
                <li>El Cobre supera los $14,500 USD/t, empujando al USD/CLP hacia la zona baja de soporte en $915.00.</li>
                <li>El Nasdaq 100 quiebra los 29,760 puntos con compras sólidas en pullbacks hacia la EMA 50 H1.</li>
            </ul>
        </div>

        <div class="scenario-card scenario-base">
            <div class="scenario-title">🟡 ESCENARIO BASE (EQUILIBRIO TÉCNICO · PROBABILIDAD 50%)</div>
            <ul class="scenario-bullets">
                <li>USD/CLP consolida en equilibrio técnico entre $918.00 y $932.50 sin quiebres direccionales limpios.</li>
                <li>Oro consolida sobre el soporte de $4,440 USD/oz y el Petróleo WTI se estabiliza en rango $81.00 - $84.60.</li>
                <li>Rendimientos del Tesoro a 10 años oscilan contenidos entre 4.60% y 4.70% a la espera de datos laborales.</li>
            </ul>
        </div>

        <div class="scenario-card scenario-risk">
            <div class="scenario-title">🔴 ESCENARIO DE RIESGO (VOLATILIDAD ASIMÉTRICA · PROBABILIDAD 15%)</div>
            <ul class="scenario-bullets">
                <li>Intervención cambiaria sorpresiva del Ministerio de Finanzas de Japón en USD/JPY (desplome hacia 155.00).</li>
                <li>Repunte de salarios en el informe NFP presiona al alza las tasas soberanas, generando toma de ganancias en bolsas.</li>
            </ul>
        </div>

        <div class="section-title" style="margin-top:10px;">🗓️ Radar Clave de la Próxima Semana</div>
        <table class="table-custom" style="margin-bottom:10px;">
            <thead>
                <tr>
                    <th>Fecha & Hora (CLT)</th>
                    <th>Evento Macroeconómico</th>
                    <th>Fuente Oficial</th>
                    <th>Impacto Esperado</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Martes 01-Sep (08:30)</strong></td>
                    <td>Publicación del <strong>Imacec de Chile</strong></td>
                    <td>Banco Central de Chile (BCCh)</td>
                    <td>Clave para proyección de TPM y USD/CLP.</td>
                </tr>
                <tr>
                    <td><strong>Miércoles 02-Sep (10:00)</strong></td>
                    <td>Índice <strong>ISM Manufacturero de EE.UU.</strong></td>
                    <td>Institute for Supply Management</td>
                    <td>Medición de actividad y pedidos de IA.</td>
                </tr>
                <tr>
                    <td><strong>Viernes 04-Sep (08:30)</strong></td>
                    <td><strong>Nóminas No Agrícolas (NFP) & Desempleo</strong></td>
                    <td>Bureau of Labor Statistics (BLS)</td>
                    <td>Determinante para la curva del Tesoro.</td>
                </tr>
            </tbody>
        </table>

        <div style="background:#04100D; color:#C1E5E4; border-radius:8px; padding:12px 16px; border:1px solid rgba(80,192,168,0.25);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.12); padding-bottom:6px; margin-bottom:8px;">
                <span style="font-family:'Goldman',sans-serif; font-size:11px; font-weight:700; color:#50C0A8;">05. FUENTES OFICIALES Y AVISO LEGAL</span>
                <span style="font-size:8.5px; color:#94A3B8;">GRUPO INTELIGENCIA RESEARCH</span>
            </div>
            <p style="font-size:8.5px; line-height:1.45; color:#94A3B8; text-align:justify;">
                Este informe ha sido elaborado exclusivamente con fines informativos y formativos por el Área de Research de Grupo Inteligencia, a partir de datos oficiales de MetaTrader 5, el Banco Central de Chile, el Departamento del Tesoro de EE.UU. y FRED (Federal Reserve Bank of St. Louis). No constituye una oferta o recomendación de compra o venta de instrumentos financieros o contratos por diferencia (CFD). Las operaciones apalancadas conllevan un riesgo sustancial para el capital.
            </p>
        </div>
    </div>

    <div class="page-footer">
        <span class="page-footer-left">GRUPO INTELIGENCIA · RESEARCH & ESTRATEGIA</span>
        <span class="page-footer-right">PÁGINA 05 / 05</span>
    </div>
</div>

</body>
</html>
"""

def main():
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = RAIZ / "scratch" / "temp_informe_cierre_semanal_editorial.html"
    tmp_html.write_text(HTML_INFORME, encoding="utf-8")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(tmp_html.as_uri())
        page.emulate_media(media="print")
        page.wait_for_timeout(500)
        
        page.pdf(
            path=str(OUTPUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()
        
    if tmp_html.exists():
        tmp_html.unlink()
        
    print(f"[OK] Informe PDF Editorial de Cierre Semanal compilado exitosamente en: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
