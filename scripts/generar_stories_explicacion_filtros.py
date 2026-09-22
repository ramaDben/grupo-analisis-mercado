# -*- coding: utf-8 -*-
"""Generador de Stories y gráficos explicativos sobre los filtros cuantitativos aplicados."""
from pathlib import Path
import json
import sys

RAIZ = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

from serie_mt5 import obtener_serie
from story_grafico import enriquecer
from story_render import render_story

PLANTILLA = RAIZ / "templates" / "stories" / "alerta.html"
OUT_DIR = RAIZ / "data" / "stories"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generar_piezas():
    piezas = [
        {
            "ticker": "USDJPY",
            "out_png": OUT_DIR / "2026-09-16_explicacion_filtro_forex_usdjpy.png",
            "activo": "Dólar / Yen Japonés",
            "activo_slug": "usdjpy",
            "activo_imagen": "assets/activos/usdjpy.jpg",
            "rotulo_activo": "DÓLAR / YEN JAPONÉS · USDJPY",
            "chip_categoria": "DIVISAS · AUDITORÍA DE VOLATILIDAD",
            "sesgo": "Lateral",
            "tag_riesgo": "COMPRESIÓN",
            "titular": "Compresión extrema en USD/JPY: por qué el escáner frenó el envío de niveles",
            "parrafo": "En H1 el soporte y la resistencia se comprimieron a solo 0,40 JPY de distancia. Una vela horaria típica cubre 1,30 veces ese rango completo, por lo que operar los bordes antes del FOMC y la decisión del BoJ provocaría falsas rupturas por puro ruido.",
            "precio_fmt": "155,168",
            "soporte_fmt": "154,950",
            "resistencia_fmt": "155,350",
            "soporte_val": 154.950,
            "resistencia_val": 155.350,
            "vol_pct": "0,52 JPY",
            "nota_volatilidad": "en una hora normal el precio recorre 1,30 veces toda la distancia entre soporte y resistencia; esperar expansión",
            "volatilidad": "baja",
            "rotulo_grafico": "USDJPY · CIERRES H1 · BANDA ESTRECHA DE 1,30x ATR",
            "sello_datos": "DATOS REALES · METATRADER 5 · AUDITORÍA GI",
        },
        {
            "ticker": "XAUUSD",
            "out_png": OUT_DIR / "2026-09-16_explicacion_filtro_commodities_oro.png",
            "activo": "Oro Spot",
            "activo_slug": "oro",
            "activo_imagen": "assets/activos/oro.jpg",
            "rotulo_activo": "ORO SPOT · XAUUSD",
            "chip_categoria": "COMMODITIES · CONTROL DE RANGO ESTRECHO",
            "sesgo": "Lateral",
            "tag_riesgo": "COMPRESIÓN",
            "titular": "El Oro en embudo técnico: banda estrecha de 1,55x ATR frena señales antes de la Fed",
            "parrafo": "El precio del Oro se mantiene encajonado entre 4.324,44 y 4.371,57 en H1. La volatilidad promedio de una sola vela excede por un 55% el espacio entre niveles intradiarios, lo que activaría stops falsos por deslizamiento antes del comunicado del FOMC.",
            "precio_fmt": "4.332,32",
            "soporte_fmt": "4.324,44",
            "resistencia_fmt": "4.371,57",
            "soporte_val": 4324.44,
            "resistencia_val": 4371.57,
            "vol_pct": "31,50 USD",
            "nota_volatilidad": "la vela típica horaria cubre 1,55 veces la distancia entre niveles; se protege el capital antes del FOMC",
            "volatilidad": "media",
            "rotulo_grafico": "XAUUSD · CIERRES H1 · EMBUDO TÉCNICO PREVIO A LA FED",
            "sello_datos": "DATOS REALES · METATRADER 5 · AUDITORÍA GI",
        },
        {
            "ticker": "US100.spot",
            "out_png": OUT_DIR / "2026-09-16_explicacion_filtro_indices_nasdaq.png",
            "activo": "Nasdaq 100",
            "activo_slug": "us100",
            "activo_imagen": "assets/activos/us100.jpg",
            "rotulo_activo": "NASDAQ 100 · US100",
            "chip_categoria": "ÍNDICES · REGLA PLAYBOOK V2",
            "sesgo": "Bajista",
            "tag_riesgo": "BLOQUEO PLAYBOOK",
            "titular": "Playbook V2 bloquea compras agresivas en el Nasdaq bajo régimen de estanflación",
            "parrafo": "El modelo macro clasifica el entorno en Régimen R3 (Estanflación / Shock), donde las tasas de descuento elevadas y el consumo firme restringen múltiplos. Comprar retrocesos agresivos antes del FOMC de las 15:00 CLT está taxativamente prohibido por el algoritmo para evitar trampas de liquidez.",
            "precio_fmt": "29.175,39",
            "soporte_fmt": "28.824,43",
            "resistencia_fmt": "29.218,29",
            "soporte_val": 28824.43,
            "resistencia_val": 29218.29,
            "vol_pct": "142,55 USD",
            "nota_volatilidad": "filtro cuantitativo activo; prohibido operar compras agresivas sin confirmación de la Fed",
            "volatilidad": "alta",
            "rotulo_grafico": "US100 · CIERRES H1 · RÉGIMEN R3 Y BLOQUEO PLAYBOOK",
            "sello_datos": "DATOS REALES · METATRADER 5 · AUDITORÍA GI",
        },
    ]

    for pz in piezas:
        ticker = pz["ticker"]
        serie, _ = obtener_serie(ticker, "H1", 60)
        ultimo = serie[-1]
        
        payload = {
            "plantilla": "alerta",
            "titular": pz["titular"],
            "parrafo": pz["parrafo"],
            "activo": pz["activo"],
            "activo_slug": pz["activo_slug"],
            "activo_imagen": pz["activo_imagen"],
            "rotulo_activo": pz["rotulo_activo"],
            "chip_categoria": pz["chip_categoria"],
            "fecha_hora": "16 SEP 2026 · 11:25",
            "sesgo": pz["sesgo"],
            "tag_riesgo": pz["tag_riesgo"],
            "vigencia": None,
            "precio_actual": pz["precio_fmt"],
            "soporte": pz["soporte_fmt"],
            "resistencia": pz["resistencia_fmt"],
            "vol_pct": pz["vol_pct"],
            "nota_volatilidad": pz["nota_volatilidad"],
            "volatilidad": pz["volatilidad"],
            "banda_estrecha": None,
            "rotulo_grafico": pz["rotulo_grafico"],
            "sello_datos": pz["sello_datos"],
            "fuente": "MT5 · GRUPO INTELIGENCIA",
            "chart_png": None,
            "recorrido": {
                "serie": serie,
                "marcadores": [
                    {
                        "indice": len(serie) - 1,
                        "precio": ultimo,
                        "clase": "actual",
                        "etiqueta": pz["precio_fmt"],
                        "rol": "AHORA"
                    }
                ],
                "niveles": [
                    {
                        "precio": pz["resistencia_val"],
                        "clase": "resistencia",
                        "etiqueta": pz["resistencia_fmt"],
                        "rol": "RESISTENCIA"
                    },
                    {
                        "precio": pz["soporte_val"],
                        "clase": "soporte",
                        "etiqueta": pz["soporte_fmt"],
                        "rol": "SOPORTE"
                    }
                ]
            }
        }
        
        payload_enriquecido = enriquecer(payload)
        render_story(payload_enriquecido, PLANTILLA, pz["out_png"], formato="horizontal")
        print(f"[OK] Story generada para {ticker}: {pz['out_png']}")

if __name__ == "__main__":
    generar_piezas()
