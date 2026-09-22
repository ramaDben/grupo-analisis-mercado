# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Generador y validador de textos de auditoría técnica y explicación de filtros para clientes."""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from guardrails import texto_cliente, precios

TEXTO_FOREX = """🔍 *AUDITORÍA TÉCNICA DÓLAR & FX · POR QUÉ NO SE EMITIERON NIVELES EN DIVISAS* 📊🇨🇱
━━━━━━━━━━━━━━━━━━━
*Compresión extrema en USD/JPY y agotamiento de recorrido en GBP/USD frenaron el envío*

A la comunidad de Dólar & FX: el escáner cuantitativo evaluó los pares del mercado en vivo contra MetaTrader 5 y determinó que ningún cruce ofrecía una relación riesgo y retorno favorable para publicar niveles en esta tanda.

📊 *Los dos motivos técnicos medidos*:
1. *Banda estrecha en USD/JPY (Gráfico adjunto)*:
   • El precio oscila en 155.168 entre el soporte de 154.950 y la resistencia de 155.350.
   • La distancia total entre ambos niveles es de apenas 0,40 JPY, mientras que una vela horaria típica (ATR H1) tiene una amplitud de 0,52 JPY.
   • Una sola vela normal cubre 1,30 veces toda la banda. Operar los bordes en esta condición provocaría falsas rupturas por ruido, especialmente a horas de la Fed hoy y la decisión del BoJ de mañana.
2. *Agotamiento intradiario en GBP/USD*:
   • La libra consumió el 116% de su rango diario promedio (ATR). Entrar cuando el activo ya recorrió más del 100% de su capacidad del día presenta un riesgo asimétrico desfavorable.

💡 *Principio de Grupo Inteligencia*:
No operar cuando el mercado no ofrece espacio técnico también es una decisión profesional, y es la que protege la cuenta de pérdidas por fricción.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• USDJPY: Par de divisas Dólar estadounidense frente a Yen japonés.
• GBPUSD: Par de divisas Libra esterlina frente a Dólar estadounidense.
• ATR: Rango Verdadero Promedio, indicador de volatilidad típica del mercado.
• FOMC: Reunión de la Reserva Federal para decidir tasas de interés.
• Fed: Reserva Federal, el banco central de Estados Unidos.
• BoJ: Banco de Japón, banco central emisor del yen.
• H1: Marco de tiempo de velas de 1 hora para análisis intradía.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_COMMODITIES = """🔍 *AUDITORÍA METALES & ENERGÍA · POR QUÉ NO SE EMITIERON NIVELES EN MATERIAS PRIMAS* 🛢️🪙
━━━━━━━━━━━━━━━━━━━
*Embudo técnico en el Oro y regla de no duplicidad en crudo y plata protegieron la sesión*

A la comunidad de Metales & Energía: el modelo cuantitativo auditó los activos del sector y bloqueó la emisión de nuevos niveles tácticos para preservar el capital de los clientes antes de los eventos de alta volatilidad.

📊 *Los motivos técnicos medidos*:
1. *Embudo técnico en el Oro XAU/USD (Gráfico adjunto)*:
   • El Oro cotiza en $4332.32, encajonado entre el soporte de $4324.44 y la resistencia de $4371.57 en H1.
   • La volatilidad promedio de una sola vela horaria ($31,50 USD de ATR) cubre 1,55 veces la distancia efectiva entre niveles.
   • Colocar órdenes de entrada dentro de este rango antes del anuncio del FOMC (15:00 CLT) expone al trader a un barrido de Stop Loss por apertura de spread y saltos de precio antes de que se defina la dirección real.
2. *Regla de no duplicidad en WTI y Plata (XAG/USD)*:
   • Ambos activos ya desplegaron sus niveles y recorridos en la apertura de las 09:30. El escáner prohíbe emitir alertas repetidas sobre el mismo activo en la misma jornada para evitar la sobreoperación y las entradas tardías.

💡 *Principio de Grupo Inteligencia*:
En vísperas de un catalizador macro de primer orden, la disciplina cuantitativa manda esperar la confirmación de salida del embudo técnico.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• XAUUSD: Cotización internacional de la onza troy de Oro spot en dólares.
• WTI: Petróleo West Texas Intermediate, referencia energética en EE.UU.
• ATR: Medición de la amplitud y volatilidad de las velas.
• FOMC: Decisión de tasas de interés de la Reserva Federal.
• Stop Loss: Orden automática que limita pérdidas si el mercado va en contra.
• Spread: Diferencia entre precio de compra y venta fijada por el mercado.
• H1: Gráfico de velas de 1 hora dentro de la jornada.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_INDICES = """🔍 *AUDITORÍA WALL STREET · POR QUÉ EL PLAYBOOK BLOQUEÓ SEÑALES EN EL NASDAQ* 📈🇺🇸
━━━━━━━━━━━━━━━━━━━
*Régimen R3 de estanflación prohíbe compras agresivas en el Nasdaq previo al FOMC*

A la comunidad de Wall Street & Índices: el índice tecnológico cotiza en 29175.39, cerca de la resistencia de 29218.29 y sobre el soporte de 28824.43 en H1. A pesar de la cercanía a niveles técnicos, el Playbook V2 bloqueó de forma estricta la emisión de compras agresivas.

📊 *La razón cuantitativa del bloqueo*:
1. *Régimen macroeconómico R3 (Estanflación / Shock)*:
   • El repunte en ventas minoristas (+1,2%) y la firmeza de las tasas soberanas encarecen el costo del capital y presionan los múltiplos de valoración de las grandes tecnológicas.
2. *Prohibición de BUY THE DIP*:
   • El modelo del Playbook V2 prohíbe expresamente comprar retrocesos agresivos a menos de 4 horas de la decisión de tasas del FOMC (15:00 CLT) y las proyecciones económicas de Powell (15:30 CLT).
   • Intentar anticipar giros en soportes antes de un evento binario de la Fed genera estadísticamente las mayores pérdidas de la cartera.

💡 *Principio de Grupo Inteligencia*:
El valor de un modelo cuantitativo radica en su capacidad de imponer disciplina e impedir operaciones cuando las probabilidades matemáticas no acompañan.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• US100: Ticker en MetaTrader 5 que replica al índice tecnológico Nasdaq 100.
• FOMC: Comité de la Fed que define la tasa de interés de referencia.
• Fed: Reserva Federal de Estados Unidos.
• Playbook V2: Sistema cuantitativo de reglas y control de riesgo institucional.
• H1: Marco temporal de velas de 1 hora para análisis dentro del día.
━━━━━━━━━━━━━━━━━━━"""

ARCHIVOS = {
    RAIZ / "data" / "stories" / "2026-09-16_explicacion_filtro_forex_usdjpy.txt": TEXTO_FOREX,
    RAIZ / "data" / "stories" / "2026-09-16_explicacion_filtro_commodities_oro.txt": TEXTO_COMMODITIES,
    RAIZ / "data" / "stories" / "2026-09-16_explicacion_filtro_indices_nasdaq.txt": TEXTO_INDICES,
}

def validar_y_guardar():
    errores = []
    for ruta, contenido in ARCHIVOS.items():
        v_guion = texto_cliente.sin_guion_largo(contenido)
        if not v_guion.ok:
            errores.append(f"Guion largo en {ruta.name}: {v_guion.detalle}")
            
        v_siglas = texto_cliente.siglas_explicadas(contenido, en_linea=False)
        if not v_siglas.ok:
            errores.append(f"Siglas en {ruta.name}: {v_siglas.detalle} ({v_siglas.ubicacion})")
            
        v_tono = texto_cliente.tono_admisible(contenido)
        if not v_tono.ok:
            errores.append(f"Tono en {ruta.name}: {v_tono.detalle}")
            
        v_voseo = texto_cliente.sin_voseo(contenido)
        if not v_voseo.ok:
            errores.append(f"Voseo en {ruta.name}: {v_voseo.detalle}")
            
        v_canales = texto_cliente.canales_existen(contenido)
        if not v_canales.ok:
            errores.append(f"Canales en {ruta.name}: {v_canales.detalle}")
            
        v_prec = precios.revisar_texto(contenido)
        if not v_prec.ok:
            errores.append(f"Precios en {ruta.name}: {v_prec.detalle}")
            
        if not errores:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
            print(f"[OK] Validado y guardado: {ruta.name}")

    if errores:
        print("\n❌ ERRORES DE GUARDRAILS ENCONTRADOS:")
        for err in errores:
            print(f"  - {err}")
        sys.exit(1)
    print("\n✅ TODOS LOS TEXTOS DE EXPLICACIÓN CUMPLEN EL 100% DE LOS GUARDRAILS.")

if __name__ == "__main__":
    validar_y_guardar()
