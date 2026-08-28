# -*- coding: utf-8 -*-
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from serie_mt5 import obtener_serie
from story_grafico import enriquecer
from story_render import render_story

SANTIAGO = ZoneInfo("America/Santiago")
ahora = datetime.now(tz=SANTIAGO)
fecha = ahora.strftime("%Y-%m-%d")
hora = ahora.strftime("%H-%M")
PLANTILLA = RAIZ / "templates" / "stories" / "alerta.html"

def get_ruta_story(activo_slug, hora_str, fecha_str):
    res = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(RAIZ / "scripts" / "ruta_story.ps1"),
         "-Fecha", fecha_str, "-Plantilla", "alerta", "-Hora", hora_str, "-Activo", activo_slug],
        capture_output=True, text=True, cwd=str(RAIZ)
    )
    return Path(res.stdout.strip())

def get_ruta_mensaje(activo_slug, hora_str, fecha_str):
    res = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(RAIZ / "scripts" / "ruta_mensaje.ps1"),
         "-Fecha", fecha_str, "-Tipo", "alerta", "-Hora", hora_str, "-Activo", activo_slug],
        capture_output=True, text=True, cwd=str(RAIZ)
    )
    return Path(res.stdout.strip())

# 1. USDCLP
usdclp_cierres, _ = obtener_serie("USDCLP", "H1", 60)
usdclp_payload = {
    "plantilla": "alerta",
    "activo": "Dólar / Peso Chileno",
    "activo_slug": "usdclp",
    "activo_imagen": "assets/activos/usdclp.jpg",
    "rotulo_activo": "DÓLAR / PESO CHILENO · USDCLP",
    "chip_categoria": "DIVISAS · DÓLAR / PESO CHILENO",
    "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
    "sesgo": "Alcista",
    "tag_riesgo": "ALCISTA",
    "titular": "USD/CLP presiona hacia 930 pesos en la previa de Jackson Hole",
    "parrafo": "El tipo de cambio quiebra al alza la media móvil de 20 períodos en una hora (H1) en 923,13 pesos y avanza hacia la resistencia de 928,63 pesos. Con la atención puesta en los banqueros centrales y un impulso proyectado de 2,63 pesos, la superación de 928,63 pesos extendería la presión compradora hacia 930,24 pesos.",
    "precio_actual": "927,82",
    "soporte": "926,90",
    "resistencia": "928,63",
    "vol_pct": "2,63 CLP",
    "rotulo_grafico": "USDCLP · CIERRES H1 · ÚLTIMAS 60 VELAS",
    "sello_datos": f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}",
    "fuente": "MT5 · GRUPO INTELIGENCIA",
    "chart_png": None,
    "recorrido": {
        "serie": usdclp_cierres,
        "lienzo": "alto",
        "marcadores": [{
            "indice": len(usdclp_cierres) - 1,
            "precio": 927.82,
            "clase": "actual",
            "etiqueta": "927,82",
            "rol": "AHORA"
        }],
        "niveles": [
            {"precio": 928.63, "clase": "resistencia", "etiqueta": "928,63", "rol": "RESISTENCIA"},
            {"precio": 926.90, "clase": "soporte", "etiqueta": "926,90", "rol": "SOPORTE"}
        ]
    }
}

p_usdclp = enriquecer(usdclp_payload)
dest_usdclp_h = get_ruta_story("usdclp", hora, fecha)
dest_usdclp_v = dest_usdclp_h.with_name(dest_usdclp_h.stem + "_vertical" + dest_usdclp_h.suffix)
render_story(p_usdclp, PLANTILLA, dest_usdclp_h, formato="horizontal")
render_story(p_usdclp, PLANTILLA, dest_usdclp_v, formato="vertical")

# 2. XAUUSD
xauusd_cierres, _ = obtener_serie("XAUUSD", "H1", 60)
xauusd_payload = {
    "plantilla": "alerta",
    "activo": "Oro",
    "activo_slug": "oro",
    "activo_imagen": "assets/activos/oro.jpg",
    "rotulo_activo": "ORO · XAU/USD",
    "chip_categoria": "COMMODITIES · ORO",
    "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
    "sesgo": "Alcista",
    "tag_riesgo": "ALCISTA",
    "titular": "Oro consolida en 4.600 USD a la espera de señales en Jackson Hole",
    "parrafo": "El metal precioso sostiene la media móvil de 20 períodos en una hora (H1) en 4.598,25 USD con volatilidad comprimida antes de las intervenciones de la Reserva Federal. Un quiebre sobre la resistencia de 4.614,35 USD activaría un impulso proyectado de 20,76 USD hacia la zona de 4.631,99 USD.",
    "precio_actual": "4.600,00",
    "soporte": "4.594,73",
    "resistencia": "4.614,35",
    "vol_pct": "20,76 USD",
    "rotulo_grafico": "XAUUSD · CIERRES H1 · ÚLTIMAS 60 VELAS",
    "sello_datos": f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}",
    "fuente": "MT5 · GRUPO INTELIGENCIA",
    "chart_png": None,
    "recorrido": {
        "serie": xauusd_cierres,
        "lienzo": "alto",
        "marcadores": [{
            "indice": len(xauusd_cierres) - 1,
            "precio": 4600.00,
            "clase": "actual",
            "etiqueta": "4.600,00",
            "rol": "AHORA"
        }],
        "niveles": [
            {"precio": 4614.35, "clase": "resistencia", "etiqueta": "4.614,35", "rol": "RESISTENCIA"},
            {"precio": 4594.73, "clase": "soporte", "etiqueta": "4.594,73", "rol": "SOPORTE"}
        ]
    }
}

p_xauusd = enriquecer(xauusd_payload)
dest_oro_h = get_ruta_story("oro", hora, fecha)
dest_oro_v = dest_oro_h.with_name(dest_oro_h.stem + "_vertical" + dest_oro_h.suffix)
render_story(p_xauusd, PLANTILLA, dest_oro_h, formato="horizontal")
render_story(p_xauusd, PLANTILLA, dest_oro_v, formato="vertical")

# Guardar mensajes WhatsApp
msg_usdclp = f"""🎯 Activo: Dólar / Peso Chileno (USDCLP)
📌 Nivel a vigilar: 928,63 CLP
⚡ Qué esperar: Presión compradora buscando quiebre de 928,63 hacia 930,24 CLP

━━━━━━━━━━━━━━━━━━━
⚠️ *ALERTA DE MERCADO: USD/CLP PRESIONA HACIA 930 PESOS*
🕐 {ahora.strftime('%H:%M')} hrs

*¿Qué pasó?*
El tipo de cambio supera la media móvil de 20 períodos en una hora (H1) en 923,13 pesos y acelera hacia 928,63 pesos en una jornada de cautela macroeconómica.

*Impacto y Drivers Intermercado:*
• 🏛️ *Tasas y Macro:* Mercados en contracción a la espera del discurso inaugural en el Simposio de Jackson Hole y expectativas de inflación de Michigan.
• 📊 *Modelo ADC + ATR:* Canal operativo con volatilidad intradía de 2,63 pesos, validado dentro del rango diario disponible.
• 📱 *USD/CLP (Sesgo Intradía):* *Alcista* con objetivo técnico en 928,63 pesos y extensión a 930,24 pesos.

━━━━━━━━━━━━━━━━━━━
🟢 Sobre 928,63 CLP → fuerza compradora hacia 930,24 CLP
🟡 Entre 926,90 CLP y 928,63 CLP → consolidación y espera de confirmación
🔴 Bajo 926,90 CLP → presión vendedora hacia 924,60 CLP
━━━━━━━━━━━━━━━━━━━"""

msg_xauusd = f"""🎯 Activo: Oro Spot (XAUUSD)
📌 Nivel a vigilar: 4.614,35 USD
⚡ Qué esperar: Quiebre sobre 4.614,35 para extender rebote técnico hacia 4.631,99 USD

━━━━━━━━━━━━━━━━━━━
⚠️ *ALERTA DE MERCADO: ORO CONSOLIDA EN 4.600 USD*
🕐 {ahora.strftime('%H:%M')} hrs

*¿Qué pasó?*
El oro defiende la media móvil de 20 períodos en una hora (H1) en 4.598,25 USD y comprime su rango operativo en torno a 4.600 USD.

*Impacto y Drivers Intermercado:*
• 🏛️ *Tasas y Macro:* Rendimiento del Tesoro a 10 años en 4,66% mantiene al metal en compresión a la espera de las declaraciones en Jackson Hole.
• 📊 *Modelo ADC + ATR:* Espacio proyectado de 20,76 USD por volatilidad tras romper el rango estrecho matutino.
• 📱 *XAU/USD (Sesgo Intradía):* *Alcista moderado* con primer objetivo en 4.614,35 USD y extensión a 4.631,99 USD.

━━━━━━━━━━━━━━━━━━━
🟢 Sobre 4.614,35 USD → fuerza compradora hacia 4.631,99 USD
🟡 Entre 4.594,73 USD y 4.614,35 USD → consolidación y espera de confirmación
🔴 Bajo 4.594,73 USD → presión vendedora hacia 4.582,96 USD
━━━━━━━━━━━━━━━━━━━"""

ruta_msg_usdclp = get_ruta_mensaje("usdclp", hora, fecha)
ruta_msg_usdclp.parent.mkdir(parents=True, exist_ok=True)
ruta_msg_usdclp.write_text(msg_usdclp, encoding="utf-8")

ruta_msg_oro = get_ruta_mensaje("oro", hora, fecha)
ruta_msg_oro.parent.mkdir(parents=True, exist_ok=True)
ruta_msg_oro.write_text(msg_xauusd, encoding="utf-8")

print(f"OK USDCLP: {dest_usdclp_h}")
print(f"OK XAUUSD: {dest_oro_h}")
