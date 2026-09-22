# -*- coding: utf-8 -*-
"""Generador de artefactos y textos para la Subasta del Tesoro de EE.UU. a 20 Años (UST 20Y)."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from story_grafico import construir_svg_barras
from story_render import render_story

TEMPLATE_DATO_MACRO = RAIZ / "templates" / "stories" / "dato_macro.html"
OUT_PNG = RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_macro.png"

def generar_imagen():
    # 5 subastas consecutivas del Tesoro a 20 años:
    # Nov 2025: 4.706%, Feb 2026: 4.664%, May 2026: 5.122%, Ago 2026: 5.204%, Sep 2026: 5.420%
    barras = [
        {"valor": 4.706, "etiqueta": "Nov", "valor_etiqueta": "4,71%", "signo": "pos"},
        {"valor": 4.664, "etiqueta": "Feb", "valor_etiqueta": "4,66%", "signo": "pos"},
        {"valor": 5.122, "etiqueta": "May", "valor_etiqueta": "5,12%", "signo": "pos"},
        {"valor": 5.204, "etiqueta": "Ago", "valor_etiqueta": "5,20%", "signo": "pos"},
        {"valor": 5.420, "etiqueta": "Sep", "valor_etiqueta": "5,42%", "signo": "pos"},
    ]
    niveles = [
        {"valor": 5.204, "etiqueta": "5,204%", "rol": "PREVIO", "clase": "esperado"}
    ]
    
    svg = construir_svg_barras(barras, niveles)
    
    payload = {
        "plantilla": "dato_macro",
        "chip_pais": "EE.UU.",
        "fecha_hora": "15 SEP 2026 · 14:00 CLT",
        "indicador": "Subasta Tesoro 20Y",
        "periodo": "Bono Soberano · USD 18.000M",
        "titular": "Tasa corta en 5,420% (+21,6 bps) y profundiza la presión en el tramo largo",
        "significado": "La mayor exigencia de rendimiento en el tramo a 20 años presiona al alza el costo de financiamiento global, fortaleciendo al dólar y comprimiendo los múltiplos de valoración bursátiles.",
        "veredicto": "Sobre Previo",
        "veredicto_slug": "mejor",
        "actual": "5,420%",
        "esperado": "",
        "anterior": "5,204%",
        "grafico": svg,
        "activos": [
            {
                "nombre": "NASDAQ 100",
                "direccion": "baja",
                "etiqueta": "BAJISTA",
                "porque": "Tasas largas descuentan flujos futuros de las empresas de crecimiento."
            },
            {
                "nombre": "DÓLAR / CLP",
                "direccion": "sube",
                "etiqueta": "ALCISTA",
                "porque": "Diferencial de tasas y fortaleza del dólar global respaldan al billete verde."
            },
            {
                "nombre": "ORO SPOT",
                "direccion": "baja",
                "etiqueta": "BAJISTA",
                "porque": "Rendimientos soberanos elevados incrementan costo de oportunidad."
            }
        ],
        "sello_datos": "U.S. Department of the Treasury · MetaTrader 5"
    }
    
    render_story(payload, TEMPLATE_DATO_MACRO, OUT_PNG, formato="horizontal")
    print(f"[OK] Imagen renderizada en {OUT_PNG}")

if __name__ == "__main__":
    generar_imagen()
