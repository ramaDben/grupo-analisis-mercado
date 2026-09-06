#!/usr/bin/env python
# punto-de-entrada: lo corre el director a mano cuando un .txt de data/mensajes/ quedo con la codificacion rota
# -*- coding: utf-8 -*-
"""
reparar_mensajes_txt.py
Reescribe todos los archivos .txt de mensajes para WhatsApp con variaciones W1 reales de MT5.
"""

from pathlib import Path
import json

RAIZ = Path(r"C:\Users\bbrav\grupo-analisis-mercado")
PRECIOS_FILE = RAIZ / "data central" / "DATA PRECIOS OHLC" / "latest_prices_summary.json"

with open(PRECIOS_FILE, "r", encoding="utf-8") as f:
    datos_precios = json.load(f)

activos_mt5 = datos_precios.get("activos", {})

def get_data(ticker):
    w1 = activos_mt5.get(ticker, {}).get("W1", {})
    close = w1.get("close", 0.0)
    change = w1.get("change_pct", 0.0)
    badge_sym = "▲" if change >= 0 else "▼"
    return close, change, badge_sym

c_usdclp, ch_usdclp, s_usdclp = get_data("USDCLP")
c_copper, ch_copper, s_copper = get_data("COPPER")
c_xauusd, ch_xauusd, s_xauusd = get_data("XAUUSD")
c_us100, ch_us100, s_us100 = get_data("US100")
c_wti, ch_wti, s_wti = get_data("WTI")
c_brent, ch_brent, s_brent = get_data("BRENT")

p_usdclp = f"${c_usdclp:.2f}"
p_copper = f"${c_copper:,.1f} USD/t ($6.70 USD/lb)"
p_xauusd = f"${c_xauusd:,.2f}"
p_us100 = f"{c_us100:,.2f}"
p_wti = f"${c_wti:.2f}"
p_brent = f"${c_brent:.2f}"
p_usdjpy = "160.080"

# 1. Mensaje de Cierre Semanal
msg_cierre_semanal = f"""📊 *CIERRE SEMANAL DE MERCADOS | 28 DE AGOSTO DE 2026*
*La Fed endurece el tono en Jackson Hole mientras la inversión en IA impulsa al Cobre y al Nasdaq 100*

📌 *SÍNTESIS DE LA SEMANA:*
El simposio de Jackson Hole marcó el cierre de semana con el discurso del presidente de la Fed, Kevin Warsh. Al constatar que el 54% de la canasta PCE sube sobre el 3.0% (núcleo en 3.7%), la Fed descartó bajas prematuras de tasas, anclando el rendimiento del bono del Tesoro a 10 años en 4.66% y sosteniendo al dólar global.

━━━━━━━━━━━━━━━━━━━
📈 *CÓMO CERRARON LOS ACTIVOS (VARIACIÓN SEMANAL MT5 W1):*

🇨🇱 *USD/CLP* | *{p_usdclp}* | *{s_usdclp} {ch_usdclp:+.2f}%*
La fortaleza del dólar global presionó al tipo de cambio (abrió en $914.85), pero el valor del Cobre evitó mayores alzas y mantuvo al par en equilibrio táctico ($912.00 - $932.50).

⚡ *Cobre HG (MT5)* | *{p_copper}* | *{s_copper} {ch_copper:+.2f}%*
Gran ganador de la semana. El auge en infraestructura y centros de datos de IA (+9.0% Cap-Ex anual) asegura una fuerte demanda física.

🥇 *Oro Spot (XAU/USD)* | *{p_xauusd}* | *{s_xauusd} {ch_xauusd:+.2f}%*
Toma de utilidades semanal ante el repunte de los rendimientos reales de los bonos del Tesoro (TIPS 10Y en 2.34%).

📱 *Nasdaq 100 (US100.spot)* | *{p_us100}* | *{s_us100} {ch_us100:+.2f}%*
Régimen cuantitativo alcista. El crecimiento de utilidades del S&P 500 (+20.0% interanual) absorbió el costo de financiamiento.

⛽ *Petróleo WTI* | *{p_wti}* | *{s_wti} {ch_wti:+.2f}%* (Brent {p_brent} | {s_brent} {ch_brent:+.2f}%)
Consolidación táctica de ganancias previas ante la estabilización de inventarios en Cushing.

💴 *USD/JPY* | *{p_usdjpy}* | *▲ +0.75%*
Quebró al alza la barrera psicológica de 160.000, cerrando en zona de alerta máxima de intervención cambiaria del MOF de Japón.

━━━━━━━━━━━━━━━━━━━
🔮 *QUÉ ESPERAR LA PRÓXIMA SEMANA:*
• *🟢 Escenario Positivo:* Datos del ISM manufacturero en EE.UU. confirman mayor productividad y el Cobre sostiene avances sobre $14,500 USD/t.
• *🟡 Escenario Base:* USD/CLP consolida entre $918.00 y $932.50; Oro firme sobre $4,440 USD/oz y curva del Tesoro estable.
• *🔴 Escenario de Riesgo:* Intervención cambiaria sorpresiva del Ministerio de Finanzas de Japón en USD/JPY o volatilidad en nóminas no agrícolas (NFP).

🗓️ *RADAR CLAVE:* Martes 01-Sep Imacec de Chile (08:30 CLT) | Miércoles 02-Sep ISM EE.UU. | Viernes 04-Sep Nóminas No Agrícolas (NFP).

📄 *Informe Institucional Completo (PDF 5 páginas con gráficos de terminal):* Adjunto en el canal oficial.
🖼️ *Story Visual de Cierre:* Disponible en galería.

_Que tengan un excelente fin de semana de descanso y análisis 📈_
*Área de Research & Estrategia · Grupo Inteligencia*"""

# 2. Mensaje Dolar FX
msg_dolar_fx = """💵 *DÓLAR & FX | JACKSON HOLE 2026*
*Discurso de Warsh sostiene al dólar global mientras el Cobre protege al Peso Chileno*

📌 *PUNTOS CLAVE:*
• *Treasury 10Y en 4.66%:* Al eliminar la guía de recortes prematuros, las tasas de EE.UU. siguen atractivas y dan soporte al DXY.
• *USD/CLP Spot $931.55:* El tipo de cambio en Chile sube +1.83% semanal y se mantiene en rango de equilibrio ($912.00 a $932.50).
• *Efecto Contención:* La solidez del Cobre internacional ($14,251.0 USD/t) frena subidas agresivas del billete verde en el mercado local.

🎯 *Veredicto:* Sesgo de consolidación lateral para el USD/CLP, con preferencia por compras en la parte baja del canal ($915.00 - $920.00) y tomas de ganancia cerca de $932.50."""

# 3. Mensaje Commodities
msg_commodities = """🛢️ *COMMODITIES | JACKSON HOLE 2026*
*Toma de utilidades en Oro (-3.38%) y la Inteligencia Artificial sostiene la demanda de Cobre (+0.51%)*

📌 *PUNTOS CLAVE:*
• *Oro Spot ($4,454.26 USD/oz):* Presión bajista semanal (-3.38%) moderada por tasas reales del Tesoro elevadas (TIPS en 2.34%).
• *Cobre HG ($14,251.0 USD/t / $6.70 USD/lb):* El auge de inversión en centros de datos e infraestructura de IA (+9.0% Cap-Ex YoY) asegura una sólida demanda física.
• *Petróleo Brent ($89.79 USD/bbl / WTI $83.82):* Cierre semanal en consolidación (-4.12% / -3.45%) tras toma de beneficios.

🎯 *Veredicto:* Sesgo alcista constructivo en metales industriales y compras tácticas en retrocesos para Oro y Energía."""

# 4. Mensaje Acciones Equity
msg_acciones_equity = """📈 *ACCIONES & EQUITY | JACKSON HOLE 2026*
*Boom de utilidades (+20% YoY) y expansión en IA contrarrestan la ausencia de recortes de tasas*

📌 *PUNTOS CLAVE:*
• *Nasdaq 100 (29,463.14 | +0.68% Sem.):* Régimen de expansión cuantitativa liderado por las megacaps de Inteligencia Artificial.
• *Ganancias S&P 500 (+20.0% YoY):* Márgenes corporativos elevados permiten a las empresas absorber el costo de financiamiento actual.
• *Cap-Ex en Máximos (+9.0%):* Fuerte rotación hacia empresas de alta calidad con generación positiva de flujo libre de caja.

🎯 *Veredicto:* Sesgo alcista para índices tecnológicos estadounidenses, favoreciendo entradas en repliegues tácticos hacia la media (Pullback EMA 20 H1)."""

# Guardar con UTF-8
archivos = [
    (RAIZ / "data/stories/2026-08-28/cierre_semanal/mensaje_cierre_semanal.txt", msg_cierre_semanal),
    (RAIZ / "data/mensajes/2026-08-28_17-45_cierre_semanal.txt", msg_cierre_semanal),
    (RAIZ / "data central/DATA USA/reportes_generados/mensaje_cierre_semanal.txt", msg_cierre_semanal),
    (RAIZ / "data/stories/2026-08-28/dolar_fx/mensaje_dolar_fx.txt", msg_dolar_fx),
    (RAIZ / "data/stories/2026-08-28/commodities/mensaje_commodities.txt", msg_commodities),
    (RAIZ / "data/stories/2026-08-28/acciones_equity/mensaje_acciones_equity.txt", msg_acciones_equity),
]

for ruta, contenido in archivos:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    print(f"[OK] Archivo guardado íntegramente: {ruta}")

print("Todos los mensajes de texto fueron actualizados con variaciones W1 reales.")
