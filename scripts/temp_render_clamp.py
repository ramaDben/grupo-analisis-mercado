import subprocess
import json
import os

payload = {
  "plantilla": "recomendacion",
  "chip_categoria": "METALES PRECIOSOS",
  "fecha_hora": "13 AGO 2026 · 10:51 CLT",
  "titular": "Plata mantiene impulso alcista apoyado en su par hermano",
  "sesgo_slug": "alcista",
  "activo_slug": "xagusd",
  "activo_imagen": "assets/activos/xagusd.jpg",
  "rotulo_activo": "PLATA · XAG/USD",
  "sesgo": "COMPRA",
  "entrada": "64,749",
  "tp": "70,758",
  "tp_clp": "Ganancia objetivo +$823.023",
  "sl": "63,676",
  "sl_clp": "Pérdida máxima -$147.028",
  "volumen": "0,03 lotes",
  "temporalidad": "Posicional (días a semanas)",
  "costo_mantencion": "",
  "tesis": "Todas las temporalidades menores y el Oro apuntan alcista. Si logra quebrar la EMA 100 diaria, el movimiento puede darse con mucha fuerza.",
  "sello_datos": "DATOS REALES · METATRADER 5 · 13 AGO 10:51",
  "firma_nombre": "Benjamín Bravo Soza",
  "firma_credencial": "Operador Acreditado CMV · Ingeniero en Finanzas",
  "firma_area": "Área de Estudios y Post-Venta · Grupo Inteligencia",
  "hitos": [
    {"precio": 65.031, "clase": "actual", "rol": "AHORA", "etiqueta": "65,031"}
  ],
  "niveles": [
    {"precio": 70.758, "clase": "meta", "rol": "OBJETIVO", "etiqueta": "70,758"},
    {"precio": 64.749, "clase": "entrada", "rol": "ENTRADA", "etiqueta": "64,749"},
    {"precio": 63.676, "clase": "stop", "rol": "STOP", "etiqueta": "63,676"}
  ]
}

payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')

# Call serie_mt5 with auto timeframe
p1 = subprocess.run(['uv', 'run', '--with', 'MetaTrader5', 'python', 'scripts/serie_mt5.py', '--ticker', 'XAGUSD', '--timeframe', 'auto', '--velas', '60'], input=payload_bytes, capture_output=True)
data = json.loads(p1.stdout.decode('utf-8-sig'))
data['recorrido']['ajuste'] = 'llenar'
final_json = json.dumps(data, ensure_ascii=False).encode('utf-8')

out_dir = 'data/stories/2026-08-13/xagusd/recomendacion'
os.makedirs(out_dir, exist_ok=True)

p2 = subprocess.run(['uv', 'run', 'python', 'scripts/story_grafico.py'], input=final_json, capture_output=True)
svg_json = p2.stdout

subprocess.run(['uv', 'run', '--extra', 'stories', 'python', 'scripts/story_render.py', '--template', 'templates/stories/recomendacion.html', '--out', f'{out_dir}/10-51_recomendacion_clamp.png', '--formato', 'horizontal'], input=svg_json)
