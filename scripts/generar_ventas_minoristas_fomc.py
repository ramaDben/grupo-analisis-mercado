# -*- coding: utf-8 -*-
"""Generador de imagen y textos para Ventas Minoristas EE.UU., Inflación y Decisión FOMC."""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from story_grafico import construir_svg_barras
from story_render import render_story

TEMPLATE_DATO_MACRO = RAIZ / "templates" / "stories" / "dato_macro.html"
OUT_PNG = RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_fomc_macro.png"

def generar_imagen():
    # Serie histórica oficial de Ventas Minoristas EE.UU. (variación mensual MoM):
    # Abr: +0.6%, May: +0.9%, Jun: +0.2%, Jul: -0.5%, Ago: +1.2%
    barras = [
        {"valor": 0.6, "etiqueta": "Abr", "valor_etiqueta": "+0,6%", "signo": "pos"},
        {"valor": 0.9, "etiqueta": "May", "valor_etiqueta": "+0,9%", "signo": "pos"},
        {"valor": 0.2, "etiqueta": "Jun", "valor_etiqueta": "+0,2%", "signo": "pos"},
        {"valor": -0.5, "etiqueta": "Jul", "valor_etiqueta": "-0,5%", "signo": "neg"},
        {"valor": 1.2, "etiqueta": "Ago", "valor_etiqueta": "+1,2%", "signo": "pos"},
    ]
    niveles = [
        {"valor": 0.8, "etiqueta": "0,8%", "rol": "ESPERADO", "clase": "esperado"}
    ]
    
    svg = construir_svg_barras(barras, niveles)
    
    payload = {
        "plantilla": "dato_macro",
        "chip_pais": "EE.UU.",
        "fecha_hora": "16 SEP 2026 · 09:30 CLT",
        "indicador": "Ventas Minoristas (MoM)",
        "periodo": "Agosto 2026 · U.S. Census Bureau",
        "titular": "Consumo repunta a +1,2% mensual y reduce margen de recortes agresivos de la Fed",
        "significado": "El gasto de los hogares en EE.UU. superó con fuerza el consenso (+0,8%). La persistencia del consumo sostiene presiones sobre la inflación de demanda y condiciona la decisión de tasas del FOMC de esta tarde.",
        "veredicto": "Sobre Consenso",
        "veredicto_slug": "mejor",
        "actual": "+1,2%",
        "esperado": "+0,8%",
        "anterior": "-0,5%",
        "grafico": svg,
        "activos": [
            {
                "nombre": "DÓLAR / CLP",
                "direccion": "sube",
                "etiqueta": "ALCISTA",
                "porque": "El diferencial de tasas favorece al dólar ante una Fed más cauta."
            },
            {
                "nombre": "NASDAQ 100",
                "direccion": "baja",
                "etiqueta": "BAJISTA",
                "porque": "Tasas de descuento elevadas presionan múltiplos de crecimiento."
            },
            {
                "nombre": "ORO SPOT",
                "direccion": "baja",
                "etiqueta": "BAJISTA",
                "porque": "Rendimientos del Tesoro firmes incrementan costo de oportunidad."
            }
        ],
        "sello_datos": "U.S. Census Bureau · Federal Reserve · MetaTrader 5"
    }
    
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    render_story(payload, TEMPLATE_DATO_MACRO, OUT_PNG, formato="horizontal")
    print(f"[OK] Imagen renderizada en {OUT_PNG}")

if __name__ == "__main__":
    generar_imagen()
