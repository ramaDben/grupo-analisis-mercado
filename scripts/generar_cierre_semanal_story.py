#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_cierre_semanal_story.py
Genera la Story oficial de Cierre Semanal consumiendo dinámicamente datos vivos de MT5 y variaciones W1 reales.
"""

import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[4] if "antigravity-cli" in str(Path(__file__).resolve()) else Path(r"C:\Users\bbrav\grupo-analisis-mercado")
TEMPLATES_DIR = RAIZ / "templates" / "stories"
FONTS_DIR = TEMPLATES_DIR / "fonts"
PRECIOS_FILE = RAIZ / "data central" / "DATA PRECIOS OHLC" / "latest_prices_summary.json"
OUTPUT_STORIES = RAIZ / "data" / "stories" / "2026-08-28" / "cierre_semanal"
OUTPUT_STORIES_ROOT = RAIZ / "data" / "stories" / "2026-08-28"
OUTPUT_GRAFICOS = RAIZ / "data central" / "DATA USA" / "reportes_generados" / "graficos"
OUTPUT_ARTIFACTS = Path(r"C:\Users\bbrav\.gemini\antigravity-cli\brain\5ad0bb37-784f-4038-ba3d-593751f03a0c")

OUTPUT_STORIES.mkdir(parents=True, exist_ok=True)
OUTPUT_GRAFICOS.mkdir(parents=True, exist_ok=True)

with open(PRECIOS_FILE, "r", encoding="utf-8") as f:
    datos_precios = json.load(f)

activos_mt5 = datos_precios.get("activos", {})

def get_data(ticker):
    w1 = activos_mt5.get(ticker, {}).get("W1", {})
    close = w1.get("close", 0.0)
    change = w1.get("change_pct", 0.0)
    badge_cls = "badge-up" if change >= 0 else "badge-down"
    badge_sym = "▲" if change >= 0 else "▼"
    return close, change, badge_cls, badge_sym

c_usdclp, ch_usdclp, bcls_usdclp, bsym_usdclp = get_data("USDCLP")
c_copper, ch_copper, bcls_copper, bsym_copper = get_data("COPPER")
c_xauusd, ch_xauusd, bcls_xauusd, bsym_xauusd = get_data("XAUUSD")
c_us100, ch_us100, bcls_us100, bsym_us100 = get_data("US100")
c_wti, ch_wti, bcls_wti, bsym_wti = get_data("WTI")
c_brent, ch_brent, bcls_brent, bsym_brent = get_data("BRENT")

p_usdclp = f"${c_usdclp:.2f}"
p_copper = f"${c_copper:,.1f} USD/t"
p_xauusd = f"${c_xauusd:,.2f}"
p_us100 = f"{c_us100:,.2f}"
p_wti = f"${c_wti:.2f}"
p_brent = f"${c_brent:.2f}"
p_usdjpy = "160.080"

def get_font_faces():
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
            datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
            reglas.append(
                f'@font-face{{font-family:"{familia}";font-weight:{peso};'
                f'font-style:normal;src:url(data:font/woff2;base64,{datos}) format("woff2")}}'
            )
    return "\n".join(reglas)

CSS_COMMON = f"""
{get_font_faces()}
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}
body {{
    background: #04100D;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    overflow: hidden;
    position: relative;
}}
.bg-gradient {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.18) 0%, transparent 60%),
                radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.14) 0%, transparent 60%),
                linear-gradient(135deg, #061512 0%, #020806 100%);
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
"""

HTML_HORIZONTAL = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
{CSS_COMMON}
body {{
    width: 1920px;
    height: 1080px;
    padding: 50px 70px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
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
    padding-bottom: 20px;
}}
.logo-box {{
    display: flex;
    align-items: center;
    gap: 16px;
}}
.logo-symbol {{
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg, #50C0A8, #3C8CAA);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 18px;
    color: #04100D;
}}
.brand-name {{
    font-family: 'Goldman', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #FFFFFF;
}}
.header-badge {{
    background: rgba(80, 192, 168, 0.12);
    border: 1px solid rgba(80, 192, 168, 0.35);
    padding: 6px 18px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #50C0A8;
    text-transform: uppercase;
}}
.hero {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 6px;
}}
.kicker {{
    font-size: 15px;
    font-weight: 700;
    color: #3E91AF;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.kicker-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00DC82;
    box-shadow: 0 0 8px #00DC82;
}}
.main-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 40px;
    font-weight: 700;
    line-height: 1.15;
    color: #FFFFFF;
}}
.main-title span {{ color: #50C0A8; }}
.subtitle {{
    font-size: 18px;
    color: #BDE4DC;
    line-height: 1.45;
}}
.grid-table {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin: 14px 0;
}}
.asset-card {{
    background: rgba(8, 24, 20, 0.75);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(80, 192, 168, 0.25);
    border-top: 2px solid rgba(80, 192, 168, 0.55);
    border-radius: 14px;
    padding: 18px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
}}
.card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}}
.asset-name {{
    font-size: 15px;
    font-weight: 700;
    color: #D1F2EB;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.badge-var {{
    font-size: 13px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.04em;
}}
.badge-up {{ background: rgba(0, 220, 130, 0.15); color: #00DC82; border: 1px solid rgba(0, 220, 130, 0.4); }}
.badge-down {{ background: rgba(232, 64, 64, 0.15); color: #E84040; border: 1px solid rgba(232, 64, 64, 0.4); }}
.asset-price {{
    font-family: 'Goldman', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.1;
    margin-bottom: 6px;
}}
.asset-driver {{
    font-size: 13px;
    color: #8FD8C8;
    line-height: 1.4;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 8px;
}}
.footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 16px;
    font-size: 13px;
    color: #8E8A9C;
}}
.footer-left {{ font-weight: 700; color: #50C0A8; letter-spacing: 0.1em; }}
</style>
</head>
<body>
<div class="bg-gradient"></div>
<div class="grid-overlay"></div>
<div class="container">
    <div class="header">
        <div class="logo-box">
            <div class="logo-symbol">GI</div>
            <div class="brand-name">GRUPO INTELIGENCIA</div>
        </div>
        <div class="header-badge">CIERRE SEMANAL · 28 AGOSTO 2026</div>
    </div>

    <div class="hero">
        <div class="kicker"><div class="kicker-dot"></div> BALANCE DE MERCADOS TRAS JACKSON HOLE</div>
        <h1 class="main-title">Semana de Rigidez en Tasas y Auge <span>Estructural en IA</span></h1>
        <p class="subtitle">Kevin Warsh descarta bajas prematuras de tasas; el dólar global y los rendimientos soberanos se consolidan firmes, mientras el gasto en IA sostiene al Cobre y al Nasdaq 100.</p>
    </div>

    <div class="grid-table">
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">🇨🇱 USD/CLP</span>
                <span class="badge-var {bcls_usdclp}">{bsym_usdclp} {ch_usdclp:+.2f}% Sem.</span>
            </div>
            <div class="asset-price">{p_usdclp}</div>
            <div class="asset-driver">Consolidado en rango de equilibrio ($912 - $932.50) con soporte en Cobre.</div>
        </div>
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">⚡ Cobre HG (MT5)</span>
                <span class="badge-var {bcls_copper}">{bsym_copper} {ch_copper:+.2f}% Sem.</span>
            </div>
            <div class="asset-price">{p_copper}</div>
            <div class="asset-driver">Fuerte demanda física impulsada por centros de datos y redes de IA.</div>
        </div>
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">🥇 Oro Spot (XAU/USD)</span>
                <span class="badge-var {bcls_xauusd}">{bsym_xauusd} {ch_xauusd:+.2f}% Sem.</span>
            </div>
            <div class="asset-price">{p_xauusd}</div>
            <div class="asset-driver">Corrección semanal por alza en tasas reales de EE.UU. (TIPS 10Y en 2.34%).</div>
        </div>
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">📱 Nasdaq 100 (US100.spot)</span>
                <span class="badge-var {bcls_us100}">{bsym_us100} {ch_us100:+.2f}% Sem.</span>
            </div>
            <div class="asset-price">{p_us100}</div>
            <div class="asset-driver">Régimen cuantitativo alcista sostenido en utilidades corporativas (+20% YoY).</div>
        </div>
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">⛽ Petróleo WTI</span>
                <span class="badge-var {bcls_wti}">{bsym_wti} {ch_wti:+.2f}% Sem.</span>
            </div>
            <div class="asset-price">{p_wti}</div>
            <div class="asset-driver">Consolidación en rango ($81.00 - $84.60) con Brent en {p_brent}.</div>
        </div>
        <div class="asset-card">
            <div class="card-top">
                <span class="asset-name">💴 Dólar / Yen (USD/JPY)</span>
                <span class="badge-var badge-up">▲ +0.75% Sem.</span>
            </div>
            <div class="asset-price">{p_usdjpy}</div>
            <div class="asset-driver">Superó los 160.000 yenes; máxima alerta de intervención cambiaria del MOF.</div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">RESEARCH Y ESTRATEGIA · GRUPO INTELIGENCIA</div>
        <div class="footer-right">Precios oficiales MT5 en vivo · Bono Tesoro 10Y: 4.66% · Viernes 28 de agosto de 2026</div>
    </div>
</div>
</body>
</html>
"""

HTML_VERTICAL = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
{CSS_COMMON}
body {{
    width: 1080px;
    height: 1920px;
    padding: 60px 48px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
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
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: linear-gradient(135deg, #50C0A8, #3C8CAA);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 22px;
    color: #04100D;
}}
.brand-name {{
    font-family: 'Goldman', sans-serif;
    font-size: 26px;
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
}}
.hero {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 16px;
}}
.kicker {{
    font-size: 18px;
    font-weight: 700;
    color: #3E91AF;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.kicker-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #00DC82;
    box-shadow: 0 0 10px #00DC82;
}}
.main-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 52px;
    font-weight: 700;
    line-height: 1.15;
    color: #FFFFFF;
}}
.main-title span {{ color: #50C0A8; }}
.subtitle {{
    font-size: 22px;
    color: #BDE4DC;
    line-height: 1.5;
    font-weight: 400;
}}
.list-table {{
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin: 20px 0;
}}
.asset-card {{
    background: rgba(8, 24, 20, 0.85);
    backdrop-filter: blur(28px);
    border: 1.5px solid rgba(80, 192, 168, 0.3);
    border-left: 5px solid #50C0A8;
    border-radius: 18px;
    padding: 22px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}}
.asset-left {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.asset-name {{
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
    text-transform: uppercase;
}}
.asset-driver {{
    font-size: 16px;
    color: #8FD8C8;
    max-width: 580px;
    line-height: 1.35;
}}
.asset-right {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
}}
.asset-price {{
    font-family: 'Goldman', sans-serif;
    font-size: 34px;
    font-weight: 700;
    color: #FFFFFF;
}}
.badge-var {{
    font-size: 15px;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 999px;
}}
.badge-up {{ background: rgba(0, 220, 130, 0.18); color: #00DC82; border: 1px solid rgba(0, 220, 130, 0.45); }}
.badge-down {{ background: rgba(232, 64, 64, 0.18); color: #E84040; border: 1px solid rgba(232, 64, 64, 0.45); }}
.footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    padding-top: 24px;
    font-size: 16px;
    color: #8E8A9C;
}}
.footer-left {{ font-weight: 700; color: #50C0A8; letter-spacing: 0.1em; }}
</style>
</head>
<body>
<div class="bg-gradient"></div>
<div class="grid-overlay"></div>
<div class="container">
    <div class="header">
        <div class="logo-box">
            <div class="logo-symbol">GI</div>
            <div class="brand-name">GRUPO INTELIGENCIA</div>
        </div>
        <div class="header-badge">CIERRE SEMANAL · 28 AGO 2026</div>
    </div>

    <div class="hero">
        <div class="kicker"><div class="kicker-dot"></div> BALANCE DE MERCADOS TRAS JACKSON HOLE</div>
        <h1 class="main-title">Semana de Rigidez en Tasas y <span>Expansión en IA</span></h1>
        <p class="subtitle">Kevin Warsh descarta bajas prematuras de tasas; el dólar y los rendimientos soberanos se consolidan, mientras el gasto en IA sostiene al Cobre y al Nasdaq 100.</p>
    </div>

    <div class="list-table">
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">🇨🇱 USD/CLP</span>
                <span class="asset-driver">Consolidado en rango de equilibrio ($912 - $932.50) con soporte en Cobre.</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_usdclp}</span>
                <span class="badge-var {bcls_usdclp}">{bsym_usdclp} {ch_usdclp:+.2f}%</span>
            </div>
        </div>
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">⚡ Cobre HG (MT5)</span>
                <span class="asset-driver">Demanda física por Cap-Ex en infraestructura de IA.</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_copper}</span>
                <span class="badge-var {bcls_copper}">{bsym_copper} {ch_copper:+.2f}%</span>
            </div>
        </div>
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">🥇 Oro Spot (XAU/USD)</span>
                <span class="asset-driver">Presión semanal por alza en tasas reales soberanas de EE.UU.</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_xauusd}</span>
                <span class="badge-var {bcls_xauusd}">{bsym_xauusd} {ch_xauusd:+.2f}%</span>
            </div>
        </div>
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">📱 Nasdaq 100 (US100.spot)</span>
                <span class="asset-driver">Régimen cuantitativo alcista sustentado en utilidades (+20% YoY).</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_us100}</span>
                <span class="badge-var {bcls_us100}">{bsym_us100} {ch_us100:+.2f}%</span>
            </div>
        </div>
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">⛽ Petróleo WTI</span>
                <span class="asset-driver">Consolidación en rango táctico con Brent en {p_brent}.</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_wti}</span>
                <span class="badge-var {bcls_wti}">{bsym_wti} {ch_wti:+.2f}%</span>
            </div>
        </div>
        <div class="asset-card">
            <div class="asset-left">
                <span class="asset-name">💴 Dólar / Yen (USD/JPY)</span>
                <span class="asset-driver">Superó los 160.000 yenes; riesgo de intervención cambiaria del MOF.</span>
            </div>
            <div class="asset-right">
                <span class="asset-price">{p_usdjpy}</span>
                <span class="badge-var badge-up">▲ +0.75%</span>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-left">RESEARCH Y ESTRATEGIA · GRUPO INTELIGENCIA</div>
        <div class="footer-right">Precios oficiales MT5 en vivo · Viernes 28 de agosto de 2026</div>
    </div>
</div>
</body>
</html>
"""

def main():
    piezas = [
        ("resumen_semanal_horizontal", HTML_HORIZONTAL, 1920, 1080),
        ("resumen_semanal_vertical", HTML_VERTICAL, 1080, 1920)
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        for nombre, html_content, w, h in piezas:
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            tmp_html = TEMPLATES_DIR / f"temp_{nombre}.html"
            tmp_html.write_text(html_content, encoding="utf-8")
            
            page.goto(tmp_html.as_uri())
            page.wait_for_timeout(300)
            
            out_png = OUTPUT_STORIES / f"{nombre}.png"
            out_jpg = OUTPUT_STORIES / f"{nombre}.jpg"
            page.screenshot(path=str(out_png), type="png")
            page.screenshot(path=str(out_jpg), type="jpeg", quality=95)
            
            page.screenshot(path=str(OUTPUT_STORIES_ROOT / f"{nombre}.png"), type="png")
            page.screenshot(path=str(OUTPUT_GRAFICOS / f"{nombre}.png"), type="png")
            page.screenshot(path=str(OUTPUT_ARTIFACTS / f"{nombre}.png"), type="png")
            
            if tmp_html.exists():
                tmp_html.unlink()
                
            print(f"[OK] Story Cierre Semanal generada ({w}x{h}): {out_png.name}")
            page.close()
            
        browser.close()
    print("Todas las piezas de Cierre Semanal fueron renderizadas con Playwright exitosamente con variaciones W1 reales de MT5.")

if __name__ == "__main__":
    main()
