# -*- coding: utf-8 -*-
"""Generador y validador de textos para la cobertura de Ventas Minoristas, Inflación y Decisión FOMC."""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from guardrails import texto_cliente, precios, autoridades

TEXTO_MACRO = """🚨 *PANORAMA MACRO · VENTAS MINORISTAS, INFLACIÓN Y DECISIÓN DE LA FED* 🇺🇸
━━━━━━━━━━━━━━━━━━━
*El consumo repunta a +1,2% mensual y aleja recortes agresivos de tasas previo al FOMC*

Las ventas minoristas de EE.UU. de agosto aceleraron con fuerza hasta un +1,2% mensual (frente al +0,8% proyectado y revirtiendo la caída previa de -0,5%). El indicador subyacente (Core Retail Sales) saltó a +1,4% (frente a +0,6% esperado), confirmando que el consumo privado se mantiene dinámico.

📊 *Cifras oficiales de ventas minoristas (Agosto)*:
• 📈 *Ventas minoristas generales (MoM)*: *+1,2%* (Consenso: +0,8% | Previo: -0,5%)
• ⚡ *Ventas minoristas subyacentes (MoM)*: *+1,4%* (Consenso: +0,6% | Previo: -0,2%)
• 🎯 *Grupo de control (Retail Control MoM)*: *+1,4%* (Consenso: +0,4% | Previo: -0,4%)
• 🏛️ *Organismo emisor*: U.S. Census Bureau

💡 *La relación con la inflación y la decisión de tasas*:
1. *Presión de demanda sobre precios*: Un consumidor resistente sostiene el gasto en servicios y bienes, limitando la velocidad con la que la inflación (IPC) puede converger al objetivo del 2,0%.
2. *Menos urgencia para la Fed*: La fortaleza de la actividad descarta temores de una recesión inminente. Esto reduce drásticamente el margen para que la Reserva Federal inicie su ciclo con un recorte agresivo de 50 bps en la reunión del FOMC de hoy (15:00 CLT).
3. *Reacción intermercado*: Los rendimientos de los bonos del Tesoro repuntan, el dólar global (DXY) se afirma y los activos sensibles a tasas de descuento enfrentan cautela antes de las palabras de Kevin Warsh a las 15:30 CLT.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• FOMC: Comité Federal de Mercado Abierto, órgano de la Fed que fija las tasas de interés.
• Fed: Reserva Federal, el banco central de Estados Unidos.
• MoM: Variación mensual respecto al mes anterior.
• IPC: Índice de Precios al Consumidor, medida de inflación de los hogares.
• DXY: Índice que mide la fuerza del dólar frente a las principales divisas mundiales.
• Bps: Puntos base (100 bps equivalen a 1,0% de tasa).
━━━━━━━━━━━━━━━━━━━"""

TEXTO_FOREX = """🚨 *RADAR DÓLAR & FX · IMPACTO DE VENTAS MINORISTAS EN USD/CLP* 🇨🇱🇺🇸
━━━━━━━━━━━━━━━━━━━
*El consumo en EE.UU. afianza al dólar global y presiona al par USD/CLP hacia $957.60*

El fuerte salto en las ventas minoristas de EE.UU. (+1,2% frente a +0,8% esperado) consolida la fortaleza del dólar a nivel global. Al reducirse las probabilidades de recortes profundos de tasas por parte de la Fed hoy a las 15:00 CLT, el diferencial de tasas continúa jugando a favor de la divisa estadounidense frente a monedas emergentes como el peso chileno.

📊 *Niveles técnicos USD/CLP (USDCLP · H1)*:
• Precio spot: $957.60
• 🟢 Resistencia clave: $964.68 (máximo de rango reciente)
• 🔴 Soporte clave: $944.20 (media móvil EMA 20 en H1)
• 💡 Tendencia H1: Alcista (respaldada por demanda de dólares y tasas firmes)

💡 *Lectura operativa previa al FOMC*:
El cruce mantiene una estructura compradora sobre la zona de soporte de $944.20. Una confirmación técnica sobre la resistencia de $964.68 abriría recorrido hacia $967.47. Por el contrario, solo una sorpresa expansiva de la Fed esta tarde perforando los $944.20 aliviaría la presión alcista en el tipo de cambio.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• USDCLP: Par de divisas Dólar estadounidense frente a Peso chileno.
• FOMC: Reunión de política monetaria de la Reserva Federal de EE.UU.
• Fed: Banco central estadounidense emisor del dólar.
• EMA: Media móvil exponencial, indicador técnico de tendencia.
• H1: Marco temporal de velas de 1 hora para análisis intradía.
• DXY: Índice del dólar estadounidense en los mercados internacionales.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_INDICES = """🚨 *ALERTA WALL STREET · CONSUMO RESILIENTE Y CONDICIÓN DE TASAS PARA EL NASDAQ* 📈🇺🇸
━━━━━━━━━━━━━━━━━━━
*Ventas minoristas firmes mantienen elevadas las tasas de descuento y exigen cautela en el Nasdaq*

Las ventas minoristas de agosto (+1,2% mensual) demostraron la solidez de los ingresos y el gasto familiar en EE.UU. Sin embargo, para la renta variable tecnológica esto representa una presión en el costo del dinero: tasas soberanas firmes limitan la expansión de múltiplos antes del veredicto de la Fed de las 15:00 CLT.

📊 *Niveles técnicos Nasdaq 100 (US100.spot · H1)*:
• Precio spot: 29088.59
• 🟢 Resistencia clave: 29218.29 (techo técnico de la sesión)
• 🔴 Soporte clave: 29041.27 (piso intradiario inmediato)
• 💡 Tendencia H1: En compresión previa al comunicado de política monetaria

💡 *Lectura operativa*:
El índice tecnológico cotiza entre los 29041.27 y los 29218.29. Operar dentro de este rango antes del anuncio de tasas del FOMC presenta alto riesgo de volatilidad; una ruptura confirmada bajo 29041.27 habilitaría pruebas hacia 28886.84, mientras que superar 29218.29 requeriría un tono dovish por parte de Kevin Warsh en la rueda de prensa de las 15:30 CLT.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• US100: Ticker en MetaTrader 5 que replica al índice tecnológico Nasdaq 100.
• FOMC: Comité de la Fed encargado de definir la tasa de interés de referencia.
• Fed: Reserva Federal de Estados Unidos.
• H1: Marco de tiempo de 1 hora para evaluar el comportamiento diario.
• Dovish: Postura de política monetaria orientada a rebajar tasas de interés.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_COMMODITIES = """🚨 *PULSO METALES & ENERGÍA · ORO Y PETRÓLEO TRAS EL CONSUMO EN EE.UU.* 🛢️🪙
━━━━━━━━━━━━━━━━━━━
*Rendimientos firmes encarecen el costo de oportunidad del Oro previo al FOMC*

Las ventas minoristas de EE.UU. (+1,2%) frenaron el impulso reciente del Oro, al consolidar rendimientos soberanos elevados y fortalecer al dólar. Por su parte, el crudo procesa un consumo sostenido que respalda la demanda de combustibles, a la espera del reporte oficial de inventarios de la EIA.

📊 *Niveles técnicos Oro Spot (XAUUSD · H1)*:
• Precio spot: $4347.16
• 🟢 Resistencia clave: $4371.57 (resistencia inmediata H1)
• 🔴 Soporte clave: $4341.11 (piso técnico de corto plazo)
• 💡 Tendencia H1: Corrección técnica moderada

💡 *Lectura operativa*:
El Oro defiende el soporte de los $4341.11. Un quiebre bajista abriría espacio hacia $4324.44 debido al encarecimiento del costo de mantener activos sin devengo de interés. Para retomar el sesgo comprador, el metal requiere superar con volumen los $4371.57 tras el comunicado de la Fed a las 15:00 CLT.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• XAUUSD: Cotización internacional de la onza troy de Oro spot en dólares.
• EIA: Administración de Información Energética de EE.UU., publica inventarios semanales de crudo.
• FOMC: Decisión de tasas de interés de la Reserva Federal estadounidense.
• Fed: Banco central de Estados Unidos.
• H1: Gráfico de velas de 1 hora para seguimiento dentro de la sesión.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_ACCIONES = """🚨 *RADAR ACCIONES & ETFS · ROTACIÓN SECTORIAL Y COSTO DE CAPITAL* 📊🇺🇸
━━━━━━━━━━━━━━━━━━━
*Resiliencia en consumo beneficia al retail pero pone a prueba múltiplos de crecimiento*

La sorpresa alcista en ventas minoristas de EE.UU. (+1,2% general y +1,4% subyacente) impulsa las perspectivas de ingresos para las empresas de comercio minorista y consumo discrecional. No obstante, al postersgar expectativas de recortes agresivos de la Fed, el costo de financiamiento continúa siendo un viento en contra para tecnológicas de múltiplos altos.

💡 *Foco para la jornada*:
• *Consumo y retail*: El fuerte poder de compra favorece a compañías del sector minorista frente a temores de desaceleración.
• *Costo de capital*: La decisión de tasas del FOMC a las 15:00 CLT y las nuevas proyecciones de tasas (Dot Plot) serán determinantes para el costo de deuda de emisores corporativos.
• *Recomendación táctica*: Evitar acumular posiciones apalancadas en acciones individuales durante la ventana de alta sensibilidad a las declaraciones de la Fed.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• FOMC: Reunión oficial de la Reserva Federal para decidir tasas de interés.
• Fed: Sistema de la Reserva Federal de Estados Unidos.
• ETF: Fondo de inversión que cotiza en bolsa replicando un sector o índice.
• Dot Plot: Gráfico de puntos donde los miembros de la Fed proyectan la trayectoria de tasas.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_CRIPTO = """🚨 *CRIPTOMERCADOS · SENSIBILIDAD A LA LIQUIDEZ GLOBAL Y DECISIÓN DE TASAS* 🌐⚡
━━━━━━━━━━━━━━━━━━━
*Bitcoin y activos digitales a la espera del veredicto del FOMC tras ventas minoristas firmes*

El ecosistema cripto opera con cautela tras conocerse que el consumo en EE.UU. creció +1,2% en agosto. Tasas de la Fed que permanezcan altas por más tiempo representan una competencia directa de rendimiento frente a los activos digitales sin rendimiento nativo, lo que mantiene al mercado en rango a la espera de las 15:00 CLT.

💡 *Claves para seguir en la sesión*:
• *Efecto liquidez*: Un tono duro (hawkish) de Kevin Warsh fortalecería al dólar y ejercería presión sobre Bitcoin y Ethereum; un tono conciliador habilitaría rebotes por apetito de riesgo.
• *Flujos en ETFs*: La demanda institucional en fondos cotizados spot sigue siendo el amortiguador principal de liquidez en el sector.
• *Gestión de riesgo*: Esperar a la asimilación del comunicado de tasas antes de entrar en rupturas de rango intradiarias.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• FOMC: Comité de la Fed que define el costo del dinero en EE.UU.
• Fed: Reserva Federal estadounidense.
• ETF: Fondo cotizado en bolsa que permite inversión institucional en criptoactivos.
• Hawkish: Postura monetaria restrictiva que favorece tasas más altas para controlar la inflación.
━━━━━━━━━━━━━━━━━━━"""

TEXTO_CUANTITATIVO = """🚨 *CONTROL CUANTITATIVO & SEÑALES · FILTRO DE VOLATILIDAD POR EVENTO FOMC* 🎯⚖️
━━━━━━━━━━━━━━━━━━━
*Alerta de blackout macroeconómico por decisión de tasas y rueda de prensa de Kevin Warsh*

En cumplimiento de las reglas del Playbook V2 y los protocolos de Volatility Targeting, se informa a la comunidad la activación del filtro de alta volatilidad para la jornada de hoy.

⚠️ *Parámetros operativos de la jornada*:
• 🛑 *Ventana de blackout FOMC*: 14:45 a 16:30 CLT (decisión a las 15:00 y conferencia de prensa a las 15:30).
• 📉 *Ventas minoristas (+1,2%)*: Confirmaron un aumento en la volatilidad implícita de tasas soberanas y divisas.
• 🛡️ *Regla de preservación de capital*: No se autoriza la apertura de nuevas señales tácticas durante la publicación de la tasa de interés ni la emisión del comunicado oficial. Las órdenes activas deben contar con Stop Loss estrictamente verificado.

━━━━━━━━━━━━━━━━━━━
🔤 *Diccionario rápido*
• FOMC: Decisión de tasas de interés de la Reserva Federal de EE.UU.
• Blackout: Período donde se prohíbe abrir operaciones por riesgo de deslizamiento y saltos de precio.
• Stop Loss: Orden automática que corta una pérdida si el precio toca un nivel predefinido.
• Volatility Targeting: Modelo cuantitativo que calibra el tamaño de posición según el riesgo del mercado.
━━━━━━━━━━━━━━━━━━━"""

ARCHIVOS = {
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_macro.txt": TEXTO_MACRO,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_forex.txt": TEXTO_FOREX,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_indices.txt": TEXTO_INDICES,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_commodities.txt": TEXTO_COMMODITIES,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_acciones.txt": TEXTO_ACCIONES,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_cripto.txt": TEXTO_CRIPTO,
    RAIZ / "data" / "stories" / "2026-09-16_ventas_minoristas_cuantitativo.txt": TEXTO_CUANTITATIVO,
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

        v_aut = autoridades.autoridad_vigente(contenido)
        if not v_aut.ok:
            errores.append(f"Autoridad en {ruta.name}: {v_aut.detalle} ({v_aut.ubicacion})")
            
        if not errores:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")
            print(f"[OK] Validado y guardado: {ruta.name}")

    if errores:
        print("\n❌ ERRORES DE GUARDRAILS ENCONTRADOS:")
        for err in errores:
            print(f"  - {err}")
        sys.exit(1)
    print("\n✅ TODOS LOS TEXTOS CUMPLEN EL 100% DE LOS GUARDRAILS Y REGLAS CANÓNICAS.")

if __name__ == "__main__":
    validar_y_guardar()
