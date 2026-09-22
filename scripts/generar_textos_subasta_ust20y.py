# -*- coding: utf-8 -*-
"""Generador y validador de textos para la Subasta del Tesoro de EE.UU. a 20 Años (UST 20Y)."""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from guardrails import texto_cliente, precios

TEXTO_MACRO = """🚨 *ACTUALIZACIÓN MACRO · SUBASTA DEL TESORO DE EE.UU.* 🇺🇸
━━━━━━━━━━━━━━━━━━━
*La subasta a 20 años corta en 5,420% (+21,6 bps) y profundiza la presión en el tramo largo*

El Departamento del Tesoro de EE.UU. acaba de adjudicar la reapertura de bonos a 20 años (U.S. 20-Year Bond Auction) con una tasa de corte de 5,420%, superior a la subasta previa de agosto (5,204%), reflejando una mayor exigencia de rendimiento para financiar al gobierno estadounidense.

📊 *Cifras oficiales de la subasta*:
• 📈 *Tasa adjudicada*: *5,420%*
• 📉 *Tasa previa*: *5,204%*
• ⚡ *Variación*: *+21,6 puntos base* (+0,216%)
• 💰 *Monto adjudicado*: *USD 18.000 millones*
• 🏛️ *Emisor*: Departamento del Tesoro de EE.UU.

💡 *¿Qué significa para los mercados?*
El rendimiento del bono a 20 años (UST 20Y) incide directamente sobre la estructura de tasas de largo plazo y el costo del capital global:
1. *Fortalece al dólar*: Tasas soberanas elevadas incrementan el atractivo del billete verde en los flujos internacionales.
2. *Presiona a las acciones de crecimiento*: Al elevarse la tasa de descuento, se comprimen los múltiplos de valoración en Wall Street (US100).
3. *Encarece activos sin rendimiento*: Metales como el Oro ven incrementado su costo de oportunidad frente a los bonos soberanos.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• UST 20Y: Rendimiento del bono del Tesoro de EE.UU. a 20 años, referencia clave de tasas de largo plazo.
• US100: Ticker en MetaTrader 5 que replica al índice tecnológico Nasdaq 100.
• Bps: Puntos base (100 bps equivalen a 1%).
• Subasta del Tesoro: Colocación primaria de deuda pública por parte del gobierno estadounidense.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_INDICES = """🚨 *ALERTA WALL STREET · IMPACTO DE LA SUBASTA DEL TESORO EN EL NASDAQ 100* 📈🇺🇸
━━━━━━━━━━━━━━━━━━━
*El rendimiento del bono a 20 años salta a 5,420% y mantiene bajo presión al Nasdaq 100*

La subasta de bonos del Tesoro a 20 años cortó en 5,420% (+21,6 bps respecto al 5,204% anterior). La persistencia de tasas elevadas en el tramo largo incrementa el costo de capital y frena el apetito por riesgo en las principales tecnológicas.

📊 *Niveles técnicos Nasdaq 100 (US100.spot · H1)*:
• Precio spot: 28970.98
• 🟢 Resistencia clave: 29124.56 (EMA 50 en H1)
• 🔴 Soporte clave: 28824.43 (mínimo de rango H1)
• 💡 Tendencia H1: Bajista (bajo presión de tasas soberanas)

💡 *Lectura operativa*:
El incremento en las tasas soberanas largas presiona los modelos de descuento de flujos para las compañías tecnológicas. Si el Nasdaq 100 perfora el soporte de 28824.43 con incremento de volumen, se abrirá espacio para una extensión correctiva; superar con claridad los 29124.56 aliviaría la presión bajista intradiaria.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• UST 20Y: Rendimiento de los bonos del Tesoro de EE.UU. a 20 años, tasa de descuento a largo plazo.
• US100: Ticker en MetaTrader 5 que replica al índice tecnológico Nasdaq 100.
• Bps: Puntos base (100 bps equivalen a 1%).
• Subasta del Tesoro: Emisión pública donde el gobierno de EE.UU. coloca deuda en el mercado financiero.
• H1: Marco temporal de 1 hora, referencia para operaciones dentro de la jornada.
• EMA: Media móvil exponencial, indicador que pondera con mayor peso los precios recientes.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_FOREX = """🚨 *RADAR DÓLAR & FX · IMPACTO DE TASAS LARGAS Y COBRE EN EL USD/CLP* 🇨🇱🇺🇸
━━━━━━━━━━━━━━━━━━━
*La tasa soberana de EE.UU. a 20 años corta en 5,420% y el Cobre presiona al peso chileno*

La subasta de bonos a 20 años del Tesoro de EE.UU. cerró en 5,420% (+21,6 bps), otorgando respaldo al dólar global. Este factor, combinado con la contención del Cobre en la zona de $14061 USD/t, mantiene el sesgo comprador en el cruce local.

📊 *Niveles técnicos USD/CLP (USDCLP · H1)*:
• Precio spot: $954.60
• 🟢 Resistencia clave: $964.68 (máximo de rango H1)
• 🔴 Soporte clave: $944.70 (EMA 50 en H1)
• 💡 Tendencia H1: Alcista (respaldado por tasas y diferencial)

💡 *Lectura operativa*:
El cruce se mantiene operando sobre la EMA 50 de H1 ($944.70), confirmando la estructura compradora de la jornada. Un quiebre confirmado sobre la resistencia de $964.68 habilitaría una aceleración hacia $968.00, mientras que sólo un retroceso bajo $944.70 neutralizaría el impulso alcista actual.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• UST 20Y: Bono del Tesoro estadounidense a 20 años, referencia de financiamiento global.
• USDCLP: Par de divisas Dólar estadounidense frente a Peso chileno.
• Bps: Puntos base (100 bps equivalen a 1%).
• Subasta del Tesoro: Mecanismo de colocación de títulos soberanos de EE.UU.
• H1: Marco temporal de 1 hora para análisis dentro de la jornada.
• EMA: Media móvil exponencial que suaviza la serie de precios con foco reciente.
━━━━━━━━━━━━━━━━━━━"""

def main():
    archivos = {
        RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_macro.txt": TEXTO_MACRO,
        RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_indices.txt": TEXTO_INDICES,
        RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_forex.txt": TEXTO_FOREX,
    }
    
    for ruta, contenido in archivos.items():
        # Validar guardrails
        v_guion = texto_cliente.sin_guion_largo(contenido)
        assert v_guion.ok, f"Fallo guion largo en {ruta.name}: {v_guion.detalle}"
        
        v_siglas = texto_cliente.siglas_explicadas(contenido, en_linea=False)
        assert v_siglas.ok, f"Fallo siglas en {ruta.name}: {v_siglas.detalle} ({v_siglas.ubicacion})"
        
        v_tono = texto_cliente.tono_admisible(contenido)
        assert v_tono.ok, f"Fallo tono en {ruta.name}: {v_tono.detalle}"
        
        v_voseo = texto_cliente.sin_voseo(contenido)
        assert v_voseo.ok, f"Fallo voseo en {ruta.name}: {v_voseo.detalle}"
        
        v_canales = texto_cliente.canales_existen(contenido)
        assert v_canales.ok, f"Fallo canales en {ruta.name}: {v_canales.detalle}"
        
        v_prec = precios.revisar_texto(contenido)
        assert v_prec.ok, f"Fallo precios en {ruta.name}: {v_prec.detalle}"
        
        ruta.write_text(contenido, encoding="utf-8")
        print(f"[OK] Guardado y validado: {ruta.name}")

if __name__ == "__main__":
    main()
