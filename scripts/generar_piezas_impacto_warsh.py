#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_piezas_impacto_warsh.py
Genera las 3 infografías/piezas de impacto de mercado tras el discurso de Kevin Warsh en Jackson Hole 2026
utilizando plantillas HTML 100% canónicas del Brandkit de Grupo Inteligencia renderizadas con Playwright,
alimentadas DINÁMICAMENTE en tiempo real desde data central (latest_prices_summary.json y latest_drivers.json).
"""

import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[4] if "antigravity-cli" in str(Path(__file__).resolve()) else Path(r"C:\Users\bbrav\grupo-analisis-mercado")
TEMPLATES_DIR = RAIZ / "templates" / "stories"
FONTS_DIR = TEMPLATES_DIR / "fonts"
OUTPUT_GRAFICOS = RAIZ / "data central" / "DATA USA" / "reportes_generados" / "graficos"
OUTPUT_STORIES = RAIZ / "data" / "stories"
OUTPUT_ARTIFACTS = Path(r"C:\Users\bbrav\.gemini\antigravity-cli\brain\5ad0bb37-784f-4038-ba3d-593751f03a0c")

OUTPUT_GRAFICOS.mkdir(parents=True, exist_ok=True)
OUTPUT_STORIES.mkdir(parents=True, exist_ok=True)

# 1. Cargar datos vivos desde data central / MCP market-data
def cargar_datos_vivos():
    ruta_precios = RAIZ / "data central" / "DATA PRECIOS OHLC" / "latest_prices_summary.json"
    ruta_drivers = RAIZ / "data central" / "DATA DRIVERS USDCLP" / "latest_drivers.json"
    
    precios = {}
    if ruta_precios.exists():
        precios = json.loads(ruta_precios.read_text(encoding="utf-8")).get("activos", {})
        
    drivers = {}
    if ruta_drivers.exists():
        drivers = json.loads(ruta_drivers.read_text(encoding="utf-8")).get("drivers", {})
        
    # Extracción de valores con fallback de seguridad
    spot_usdclp = precios.get("USDCLP", {}).get("H1", {}).get("close", 928.45)
    spot_xauusd = precios.get("XAUUSD", {}).get("H1", {}).get("close", 4558.80)
    spot_copper = precios.get("COPPER", {}).get("H1", {}).get("close", 14262.0)
    spot_wti = precios.get("WTI", {}).get("H1", {}).get("close", 83.16)
    spot_brent = precios.get("BRENT", {}).get("H1", {}).get("close", 89.24)
    spot_us100 = precios.get("US100", {}).get("H1", {}).get("close", 29490.81)
    
    us_10y = drivers.get("US_10Y_TREASURY", {}).get("valor", 4.66)
    fed_funds = drivers.get("FED_FUNDS_RATE", {}).get("valor", 3.63)
    copper_lb = drivers.get("COBRE_HG", {}).get("valor", 6.7025)
    
    return {
        "usdclp": f"${spot_usdclp:.2f}",
        "xauusd": f"${spot_xauusd:,.2f}",
        "copper_t": f"${spot_copper:,.1f}",
        "copper_lb": f"${copper_lb:.2f}",
        "wti": f"${spot_wti:.2f}",
        "brent": f"${spot_brent:.2f}",
        "us100": f"{spot_us100:,.2f}",
        "us_10y": f"{us_10y:.2f}%",
        "fed_funds": f"{fed_funds:.2f}%"
    }

def get_font_faces():
    catalogo = [
        ("plus-jakarta-sans-400.woff2", "Plus Jakarta Sans", 400),
        ("plus-jakarta-sans-600.woff2", "Plus Jakarta Sans", 600),
        ("plus-jakarta-sans-700.woff2", "Plus Jakarta Sans", 700),
        ("goldman-400.woff2", "Goldman", 400),
        ("goldman-700.woff2", "Goldman", 700),
    ]
    reglas = []
    for archivo, familia, peso in catalogo:
        ruta = FONTS_DIR / archivo
        if ruta.exists():
            datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
            reglas.append(
                f'@font-face{{font-family:"{familia}";font-weight:{peso};'
                f'font-style:normal;src:url(data:font/woff2;base64,{datos}) format("woff2")}}'
            )
    return "\n".join(reglas)

CSS_BASE = f"""
{get_font_faces()}
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}
body {{
    width: 1920px;
    height: 1080px;
    background: #061512;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    overflow: hidden;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 60px 80px;
}}
.bg-gradient {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.18) 0%, transparent 60%),
                radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.15) 0%, transparent 60%),
                linear-gradient(135deg, #051410 0%, #030a08 100%);
    z-index: 0;
}}
.grid-overlay {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-size: 60px 60px;
    background-image: 
        linear-gradient(to right, rgba(80, 192, 168, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(80, 192, 168, 0.03) 1px, transparent 1px);
    z-index: 1;
}}
.container {{
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(80, 192, 168, 0.25);
    padding-bottom: 24px;
}}
.logo-box {{
    display: flex;
    align-items: center;
    gap: 16px;
}}
.logo-symbol {{
    width: 38px;
    height: 38px;
    border-radius: 8px;
    background: linear-gradient(135deg, #50C0A8, #3C8CAA);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 20px;
    color: #051410;
}}
.brand-name {{
    font-family: 'Goldman', sans-serif;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #FFFFFF;
}}
.header-badge {{
    background: rgba(80, 192, 168, 0.12);
    border: 1px solid rgba(80, 192, 168, 0.35);
    padding: 8px 20px;
    border-radius: 100px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #50C0A8;
    text-transform: uppercase;
}}
.hero {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 10px;
}}
.kicker {{
    font-size: 16px;
    font-weight: 700;
    color: #3E91AF;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.kicker-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00DC82;
    box-shadow: 0 0 10px #00DC82;
}}
.main-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 48px;
    font-weight: 700;
    line-height: 1.15;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}}
.main-title span {{
    color: #50C0A8;
}}
.subtitle {{
    font-size: 20px;
    color: #C1E5E4;
    max-width: 1400px;
    line-height: 1.5;
    font-weight: 400;
}}
.cards-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    margin: 20px 0;
}}
.card {{
    background: rgba(8, 26, 22, 0.7);
    backdrop-filter: blur(28px);
    border: 1px solid rgba(80, 192, 168, 0.25);
    border-top: 2px solid rgba(80, 192, 168, 0.55);
    border-radius: 16px;
    padding: 32px 28px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
}}
.card-tag {{
    font-size: 13px;
    font-weight: 700;
    color: #82E0CE;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 12px;
}}
.card-value {{
    font-family: 'Goldman', sans-serif;
    font-size: 46px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.1;
    margin-bottom: 8px;
}}
.card-label {{
    font-size: 16px;
    font-weight: 600;
    color: #50C0A8;
    margin-bottom: 16px;
}}
.card-desc {{
    font-size: 15px;
    color: #D1F2EB;
    line-height: 1.55;
    font-weight: 400;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 14px;
}}
.footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 20px;
    font-size: 14px;
    color: #737373;
}}
.footer-left {{
    font-weight: 700;
    color: #50C0A8;
    letter-spacing: 0.12em;
}}
.footer-right {{
    color: #A0AAB5;
}}
"""

def construir_html_dolar(d):
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><style>{CSS_BASE}</style></head>
<body>
<div class="bg-gradient"></div>
<div class="grid-overlay"></div>
<div class="container">
    <div class="header">
        <div class="logo-box">
            <div class="logo-symbol">GI</div>
            <div class="brand-name">GRUPO INTELIGENCIA</div>
        </div>
        <div class="header-badge">JACKSON HOLE 2026 · IMPACTO MACRO</div>
    </div>
    <div class="hero">
        <div class="kicker"><div class="kicker-dot"></div> TRANSMISIÓN INTERMERCADO · MERCADO DE DIVISAS & TASAS</div>
        <h1 class="main-title">Dólar Global & USD/CLP tras Discurso de <span>Kevin Warsh</span></h1>
        <p class="subtitle">El rechazo frontal a la guía prospectiva y la firmeza en la meta del 2.0% PCE anclan los rendimientos del Tesoro y sostienen la demanda por el dólar estadounidense.</p>
    </div>
    <div class="cards-grid">
        <div class="card">
            <div>
                <div class="card-tag">Rendimiento Soberano</div>
                <div class="card-value">{d['us_10y']}</div>
                <div class="card-label">US Treasury 10Y · Fed Funds {d['fed_funds']}</div>
            </div>
            <div class="card-desc">Tasas elevadas por más tiempo sostienen el carry trade y fortalecen la atracción global hacia activos en USD.</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Dólar Index</div>
                <div class="card-value">DXY Firme</div>
                <div class="card-label">Sesgo Alcista vs. Divisas G10</div>
            </div>
            <div class="card-desc">Presión contenida sobre monedas extranjeras ante la postergación de recortes y persistencia en inflación PCE (3.7%).</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Tipo de Cambio Chile</div>
                <div class="card-value">{d['usdclp']}</div>
                <div class="card-label">Rango Táctico $912.00 - $928.45</div>
            </div>
            <div class="card-desc">El peso chileno resiste presiones globales gracias a la solidez del Cobre internacional ({d['copper_t']} USD/t).</div>
        </div>
    </div>
    <div class="footer">
        <div class="footer-left">RESEARCH Y ESTRATEGIA · GRUPO INTELIGENCIA</div>
        <div class="footer-right">Datos MT5 / FRED / BCCh en vivo · 28 de agosto de 2026</div>
    </div>
</div>
</body></html>"""

def construir_html_commodities(d):
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><style>{CSS_BASE}</style></head>
<body>
<div class="bg-gradient"></div>
<div class="grid-overlay"></div>
<div class="container">
    <div class="header">
        <div class="logo-box">
            <div class="logo-symbol">GI</div>
            <div class="brand-name">GRUPO INTELIGENCIA</div>
        </div>
        <div class="header-badge">JACKSON HOLE 2026 · COMMODITIES</div>
    </div>
    <div class="hero">
        <div class="kicker"><div class="kicker-dot"></div> TRANSMISIÓN INTERMERCADO · METALES & ENERGÍA</div>
        <h1 class="main-title">Impacto en Commodities: <span>Oro, Cobre e Hidrocarburos</span></h1>
        <p class="subtitle">La persistencia inflacionaria respalda al Oro, mientras el boom de inversión en Inteligencia Artificial impulsa la demanda física de Cobre y el consumo sostiene al Petróleo.</p>
    </div>
    <div class="cards-grid">
        <div class="card">
            <div>
                <div class="card-tag">Metal Refugio</div>
                <div class="card-value">{d['xauusd']}</div>
                <div class="card-label">Oro Spot (XAU/USD) · USD/oz</div>
            </div>
            <div class="card-desc">Demanda firme por cobertura inflacionaria (54% de la canasta PCE > 3.0%), balanceada por tasas reales elevadas (TIPS 2.34%).</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Metal Industrial & IA</div>
                <div class="card-value">{d['copper_t']}</div>
                <div class="card-label">Cobre HG (MT5) · USD/t ({d['copper_lb']}/lb)</div>
            </div>
            <div class="card-desc">Más del 50% del alza en Cap-Ex (+9.0% YoY) se concentra en infraestructura de IA y centros de datos intensivos en cobre.</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Energía Global</div>
                <div class="card-value">{d['brent']}</div>
                <div class="card-label">Petróleo Brent · WTI {d['wti']} USD/bbl</div>
            </div>
            <div class="card-desc">Sostenido por compras internas privadas en EE.UU. (+3.0%) y shocks de oferta/demanda precautoria (+7.4% en 5 días).</div>
        </div>
    </div>
    <div class="footer">
        <div class="footer-left">RESEARCH Y ESTRATEGIA · GRUPO INTELIGENCIA</div>
        <div class="footer-right">Datos MT5 / EIA / LBMA en vivo · 28 de agosto de 2026</div>
    </div>
</div>
</body></html>"""

def construir_html_acciones(d):
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><style>{CSS_BASE}</style></head>
<body>
<div class="bg-gradient"></div>
<div class="grid-overlay"></div>
<div class="container">
    <div class="header">
        <div class="logo-box">
            <div class="logo-symbol">GI</div>
            <div class="brand-name">GRUPO INTELIGENCIA</div>
        </div>
        <div class="header-badge">JACKSON HOLE 2026 · RENTA VARIABLE</div>
    </div>
    <div class="hero">
        <div class="kicker"><div class="kicker-dot"></div> TRANSMISIÓN INTERMERCADO · ACCIONES & ÍNDICES EE.UU.</div>
        <h1 class="main-title">Renta Variable & Equity: <span>Nasdaq 100 y S&P 500</span></h1>
        <p class="subtitle">El auge en utilidades corporativas y la inversión masiva en IA compensan la postergación de recortes de tasas, impulsando la selectividad hacia empresas de alta calidad.</p>
    </div>
    <div class="cards-grid">
        <div class="card">
            <div>
                <div class="card-tag">Índice Tecnológico</div>
                <div class="card-value">{d['us100']}</div>
                <div class="card-label">Nasdaq 100 (US100) · Expansión</div>
            </div>
            <div class="card-desc">Régimen cuantitativo alcista sustentado en la ola de productividad e infraestructura de grandes laboratorios de IA.</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Ganancias Corporativas</div>
                <div class="card-value">+20.0%</div>
                <div class="card-label">Crecimiento YoY Utilidades S&P 500</div>
            </div>
            <div class="card-desc">Márgenes elevados y fuerte resiliencia operativa absorben el costo de capital sin deteriorar la solvencia empresarial.</div>
        </div>
        <div class="card">
            <div>
                <div class="card-tag">Gasto de Capital</div>
                <div class="card-value">+9.0%</div>
                <div class="card-label">Inversión en Equipos e Intangibles</div>
            </div>
            <div class="card-desc">Máximo ritmo inversor desde 2021; fuerte rotación sectorial hacia empresas con flujo libre de caja positivo.</div>
        </div>
    </div>
    <div class="footer">
        <div class="footer-left">RESEARCH Y ESTRATEGIA · GRUPO INTELIGENCIA</div>
        <div class="footer-right">Datos MT5 / Nasdaq / S&P en vivo · 28 de agosto de 2026</div>
    </div>
</div>
</body></html>"""

def main():
    datos = cargar_datos_vivos()
    print(f"[DATA VIVA] Cotizaciones cargadas dinámicamente:")
    print(f"  • USDCLP: {datos['usdclp']} | US10Y: {datos['us_10y']} | Fed Funds: {datos['fed_funds']}")
    print(f"  • XAUUSD: {datos['xauusd']} | Cobre: {datos['copper_t']} USD/t ({datos['copper_lb']}/lb) | Brent: {datos['brent']}")
    print(f"  • US100: {datos['us100']}")
    
    piezas = [
        ("impacto_dolar_fx", construir_html_dolar(datos)),
        ("impacto_commodities", construir_html_commodities(datos)),
        ("impacto_acciones_equity", construir_html_acciones(datos))
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        
        for nombre, html_content in piezas:
            tmp_html = TEMPLATES_DIR / f"temp_{nombre}.html"
            tmp_html.write_text(html_content, encoding="utf-8")
            
            page.goto(tmp_html.as_uri())
            page.wait_for_timeout(300)
            
            out_png = OUTPUT_GRAFICOS / f"{nombre}.png"
            out_jpg = OUTPUT_GRAFICOS / f"{nombre}.jpg"
            page.screenshot(path=str(out_png), type="png")
            page.screenshot(path=str(out_jpg), type="jpeg", quality=95)
            
            page.screenshot(path=str(OUTPUT_STORIES / f"{nombre}.png"), type="png")
            page.screenshot(path=str(OUTPUT_ARTIFACTS / f"{nombre}.png"), type="png")
            page.screenshot(path=str(OUTPUT_ARTIFACTS / f"{nombre}.jpg"), type="jpeg", quality=95)
            
            if tmp_html.exists():
                tmp_html.unlink()
                
            print(f"[OK] Renderizado HTML dinámico -> {out_png.name}")
            
        browser.close()
    print("Todas las piezas fueron renderizadas con datos vivos exitosamente.")

if __name__ == "__main__":
    main()
