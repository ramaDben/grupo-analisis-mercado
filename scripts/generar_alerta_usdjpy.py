#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_alerta_usdjpy.py
Ejecuta el pipeline oficial de Alerta de Mercado para USD/JPY ante el nivel de intervención del MOF (160.000),
con rótulos concisos de alta fidelidad (NIVEL MOF, R1, SPOT, S1) para encaje perfecto en el bloque glass.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[4] if "antigravity-cli" in str(Path(__file__).resolve()) else Path(r"C:\Users\bbrav\grupo-analisis-mercado")
SCRIPTS_DIR = RAIZ / "scripts"
TEMPLATES_DIR = RAIZ / "templates" / "stories"
STORY_DIR = RAIZ / "data" / "stories" / "2026-08-28" / "usdjpy"
STORY_DIR.mkdir(parents=True, exist_ok=True)
MENSAJES_DIR = RAIZ / "data" / "mensajes"
MENSAJES_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = Path(r"C:\Users\bbrav\.gemini\antigravity-cli\brain\5ad0bb37-784f-4038-ba3d-593751f03a0c")

def main():
    santiago_tz = ZoneInfo("America/Santiago")
    now_cl = datetime.now(santiago_tz)
    fecha_hora_str = now_cl.strftime("%d %b %Y · %H:%M").upper()
    sello_str = f"Datos reales · MetaTrader 5 · {now_cl.strftime('%d %b %H:%M').upper()}"
    
    # Payload canónico con roles concisos (máx 10-12 caracteres para no desbordar label_x)
    payload = {
        "plantilla": "alerta",
        "activo": {
            "ticker_mt5": "USDJPY",
            "nombre": "Dólar / Yen Japonés",
            "digits": 3
        },
        "chip_categoria": "DIVISAS · USD/JPY",
        "activo_slug": "usdjpy",
        "activo_imagen": "assets/activos/usdjpy.jpg",
        "fecha_hora": fecha_hora_str,
        "titular": "USD/JPY roza los 160.000 y entra en zona crítica de intervención del MOF",
        "parrafo": (
            "El par cotiza en 159.988 con RSI sobrecomprado (75.4) presionando la barrera psicológica de 160.000. "
            "El mercado vigila advertencias de tasas y posibles 'rate checks' del Ministerio de Finanzas de Japón ante "
            "el riesgo inminente de intervención cambiaria directa para frenar la depreciación del yen."
        ),
        "rotulo_activo": "DÓLAR / YEN · USD/JPY",
        "tag_riesgo": "RIESGO ALTO · MOF",
        "precio_actual": "159.988",
        "soporte": "159.410",
        "resistencia": "160.152",
        "rotulo_grafico": "USD/JPY · VELAS 1H (MT5)",
        "chart_png": None,
        "fuente": "MT5 / MOF / BoJ",
        "sesgo": "Alcista",
        "sello_datos": sello_str,
        # Hitos (punto SPOT actual)
        "hitos": [
            {
                "precio": 159.988,
                "etiqueta": "159.988",
                "clase": "actual",
                "rol": "SPOT"
            }
        ],
        # Niveles horizontales con roles concisos
        "niveles": [
            {
                "precio": 160.000,
                "etiqueta": "160.000",
                "clase": "meta",
                "rol": "NIVEL MOF"
            },
            {
                "precio": 160.152,
                "etiqueta": "160.152",
                "clase": "resistencia",
                "rol": "R1"
            },
            {
                "precio": 159.410,
                "etiqueta": "159.410",
                "clase": "soporte",
                "rol": "S1"
            }
        ],
        "recorrido": {
            "lienzo": "ancho",
            "ajuste": "meet"
        }
    }
    
    payload_json = json.dumps(payload, ensure_ascii=False)
    
    cmd1 = [sys.executable, str(SCRIPTS_DIR / "serie_mt5.py"), "--ticker", "USDJPY", "--timeframe", "H1", "--velas", "60"]
    cmd2 = [sys.executable, str(SCRIPTS_DIR / "story_grafico.py")]
    
    out_img = STORY_DIR / "alerta_usdjpy_mof.png"
    out_img_root = RAIZ / "data" / "stories" / "2026-08-28" / "alerta_usdjpy_mof.png"
    out_img_artifact = ARTIFACTS_DIR / "alerta_usdjpy_mof.png"
    
    cmd3 = [
        sys.executable, str(SCRIPTS_DIR / "story_render.py"),
        "--template", str(TEMPLATES_DIR / "alerta.html"),
        "--out", str(out_img),
        "--formato", "horizontal"
    ]
    
    print("[1/3] Extrayendo serie H1 (60 velas) e inyectando hitos/niveles concisos...")
    p1 = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout1, stderr1 = p1.communicate(input=payload_json.encode("utf-8"))
    if p1.returncode != 0:
        print(f"Error en serie_mt5: {stderr1.decode('utf-8')}")
        sys.exit(1)
        
    print("[2/3] Generando geometría SVG del gráfico...")
    p2 = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout2, stderr2 = p2.communicate(input=stdout1)
    if p2.returncode != 0:
        print(f"Error en story_grafico: {stderr2.decode('utf-8')}")
        sys.exit(1)
        
    print("[3/3] Renderizando Story 16:9 con Playwright...")
    p3 = subprocess.Popen(cmd3, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout3, stderr3 = p3.communicate(input=stdout2)
    if p3.returncode != 0:
        print(f"Error en story_render: {stderr3.decode('utf-8')}")
        sys.exit(1)
        
    if out_img.exists():
        import shutil
        shutil.copy(str(out_img), str(out_img_root))
        shutil.copy(str(out_img), str(out_img_artifact))
        print(f"[OK] Story Alerta generada exitosamente en: {out_img}")
        
    txt_mensaje = f"""🚨 *ALERTA DE MERCADO | USD/JPY EN ZONA DE INTERVENCIÓN*
*El Dólar/Yen toca los 159.988 y pone a prueba el límite de tolerancia del Banco de Japón y el MOF*

📌 *PUNTOS CLAVE DE LA ALERTA:*
• *Precio Actual:* 159.988 (Máximos de la sesión en gráfico 1H).
• *Nivel MOF:* 160.000 (Límite histórico de intervención cambiaria del Ministerio de Finanzas).
• *Resistencia Crítica:* 160.152 (Techo Donchian 50 en 160.041).
• *Soporte Táctico:* 159.410 (EMA 50 H1 en 159.430).
• *Indicador RSI:* 75.40 (Sobrecompra extrema intradía).

🏛️ *CONTEXTO MACRO & DRIVERS:*
El par USD/JPY roza el nivel psicológico de los 160.000 yenes por dólar tras el tono firme de la Fed en Jackson Hole. En estos niveles de precios, el Ministerio de Finanzas de Japón (MOF) ha ejecutado históricamente intervenciones cambiarias directas y chequeos de tasas (*rate checks*) para frenar la caída del yen.

🎯 *VEREDICTO & GESTIÓN DE RIESGO:*
• *Sesgo:* Alcista pero en zona de peligro extremo por riesgo de intervención súbita.
• *Estrategia:* Evitar compras agresivas en el quiebre de 160.000 (*Breakout Chase Prohibido*). Favorecer tomas de ganancia parciales y monitorear caídas hacia 159.410 si el MOF emite declaraciones oficiales.
"""
    
    txt_path1 = STORY_DIR / "mensaje_alerta_usdjpy.txt"
    txt_path2 = MENSAJES_DIR / f"{now_cl.strftime('%Y-%m-%d_%H-%M')}_alerta_usdjpy.txt"
    
    txt_path1.write_text(txt_mensaje, encoding="utf-8")
    txt_path2.write_text(txt_mensaje, encoding="utf-8")
    print(f"[OK] Mensaje de WhatsApp guardado en: {txt_path1}")

if __name__ == "__main__":
    main()
