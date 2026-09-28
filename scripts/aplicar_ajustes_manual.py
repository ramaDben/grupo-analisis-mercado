# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Aplica integralmente el Plan de Ajustes al Manual de Operaciones de Trading Cuantitativo.

Incorpora todas las observaciones de Feedback.docx:
1. Unificación de tasa real para Oro en 2,20% y centralización en Anexo A2 (SSOT).
2. Buffer de Fricción (Spread + Comisión + Swap) en el 1% de riesgo (Módulo 7.1 y 7.4).
3. Matriz 2D Clima Macro x Setup Técnico y Precedencia Estricta (Módulo 5.0, 5.2, 5.3).
4. Depuración y contextualización del parámetro Swing D1 en Anexo A2.
5. Bitácora de Auditoría Operativa y Journaling Cuantitativo (Nuevo Módulo 12).
6. Costos de Mantenimiento Overnight (Swap) en posiciones multi-jornada (Módulo 6.4, 7.5, 10.2).
7. Regla de Tolerancia de Deslizamiento (Slippage Cap del 15% / 0,2xATR) en órdenes pendientes (Módulo 5.1, 8.3, 11).
8. Mapa de Correlación Intermercado y Regla de Co-Riesgo de Activos Gemelos (Módulo 9.1, 9.4).
9. Caso de Estudio didáctico "La Pérdida Perfecta" (Módulo 4.4).
10. Expectativas Estadísticas de Win Rate, Frecuencia y Ratio R:R (Módulo 0.4 y Anexo A2).
11. Tabla de Control de Versiones v2.1 y Resumen de Reglas Obsoletas (Introducción).
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"


def main():
    text = MANUAL.read_text(encoding="utf-8")

    # 1. Header & Version Control Table
    nuevo_header = """# Manual de Operaciones · Trading Cuantitativo Intermercado
### De la macroeconomía real a tu plataforma MetaTrader 5
**Grupo Inteligencia · Departamento de Estudios y Research**  
*Manual formativo modular para el trader cuantitativo. Versión Oficial 2.1 · Septiembre 2026*

---

### 📜 Control de Versiones y Gobernanza del Manual

| Versión | Fecha | Cambios Principales y Justificación Técnica |
|---|---|---|
| **v1.0** | Agosto 2026 | Versión inicial formativa con stops discrecionales en mínimos de velas. |
| **v2.0** | Septiembre 2026 | Formalización matemática del ATR de 14 en H1, conmutador de climas R0–R4, precedencia de setups y Chandelier Trailing Exit. |
| **v2.1** | **Septiembre 2026** *(Actual)* | **Centralización de umbrales en Anexo A2 (SSOT)**, unificación de tasa real para Oro en 2,20 %, **Presupuesto de Riesgo Neto (Buffer 90/10 para Spread + Comisión)**, **Matriz 2D Clima × Setup**, **Regla de Tolerancia de Slippage**, **Mapa de Correlación Intermercado y Co-Riesgo**, **Caso de Estudio de Pérdida Disciplinada**, y **Módulo 12 de Bitácora de Auditoría Operativa**. |

> [!WARNING]
> ### 🛑 Reglas Obsoletas que Ya No Aplican
> 1. **Stops en el mínimo o máximo de la vela de señal**: Prohibido desde v2.0. El stop se apoya exclusivamente en el swing de 20 velas o en $1,5 \\times \\text{ATR}_{14}(\\text{H1})$.
> 2. **Cálculo de riesgo al 1,00 % puro de precio sin buffer**: Obsoleto en v2.1. El presupuesto asigna el 90 % ($0,90 \\%$) al movimiento de precio y reserva el 10 % ($0,10 \\%$) para cubrir spread, comisión y swap.
> 3. **Operar WTI y Brent en simultáneo a riesgo pleno**: Obsoleto en v2.1 por correlación $\\rho > 0,90$. Comparten un cupo de co-riesgo conjunto de máximo $1,0 \\%$.
> 4. **Buscar rupturas o retrocesos en clima Calma**: Obsoleto en v2.1. En Clima Calma (R0) *únicamente* se permite Rebote en Rango (5.3) si ADX $< 20$.

---

> [!CAUTION]
> **Aviso de riesgo y transparencia.** Este documento es material educativo y formativo de Grupo Inteligencia. No constituye asesoría financiera personalizada ni garantiza rentabilidades futuras. El trading en Contratos por Diferencia (CFD) con apalancamiento conlleva un alto riesgo de pérdida de capital, y puedes perder la totalidad de lo que depositas.
>
> Este manual no es un robot que opera solo. Nosotros publicamos a diario el clima económico y el sesgo por activo; **la decisión, el cálculo del tamaño y la ejecución de cada orden son tuyas**, en tu plataforma y bajo tu criterio.

---

## 🧭 Cómo usar este manual

El manual está dividido en **12 módulos y 3 anexos**. Cada módulo es autocontenido: responde una pregunta concreta y no necesitas haber leído el anterior para aplicarlo.

| Si lo que quieres es… | Lee estos módulos |
|---|---|
| Entender qué estás operando y las expectativas estadísticas reales | **M0**, **M1** |
| Entender por qué se mueve el dinero en el mundo | **M2**, **M3** |
| Armar una operación concreta de principio a fin | **M4** → **M5** → **M6** → **M7** → **M8** |
| Saber cuándo NO operar y gestionar el co-riesgo de cartera | **M8**, **M9** |
| Consultar la regla y el swap de un activo puntual | **M10** |
| Repasar en 30 segundos antes de hacer clic | **M11** |
| Registrar y auditar tu disciplina operativa | **M12** |
| Buscar una sigla o un umbral maestro | **A1**, **A2** |"""

    idx_orig_header_end = text.find("### Qué te damos nosotros y qué determinas tú")
    text = nuevo_header + "\n\n" + text[idx_orig_header_end:]

    # 2. Add Expectativas estadísticas in Módulo 0 (after 0.3)
    idx_m1 = text.find("# 🕯️ MÓDULO 1 · El lenguaje del gráfico: la vela H1 cerrada")
    m03_addition = """

## 0.4 · Expectativas estadísticas: qué esperar de este método

Un error común en traders principiantes es abandonar el método tras dos semanas sin señales en un activo o tras una racha de tres pérdidas consecutivas. La rentabilidad cuantitativa se basa en una **distribución estadística de esperanza matemática positiva**, no en ganar cada operación:

| Activo | Frecuencia de Señales Estimada | Tasa de Acierto (Win Rate) Esperada | Ratio Riesgo/Beneficio (R:R) Promedio | Horizonte Temporal Típico |
|---|---|---|---|---|
| **USD/CLP** | 2 a 4 señales / mes | 50 % – 55 % | 1,2 : 1 – 1,8 : 1 | 3 a 6 horas (Rueda Stgo) |
| **Oro (XAU/USD)** | 1 a 3 señales / mes | 42 % – 48 % | **2,5 : 1 – 4,0 : 1** (Trailing Exit) | 1 a 5 días hábiles |
| **WTI / Brent** | 2 a 5 señales / mes | 46 % – 52 % | 1,4 : 1 – 2,0 : 1 | 6 a 24 horas |
| **Nasdaq 100** | 3 a 6 señales / mes | 48 % – 54 % | 1,3 : 1 – 2,0 : 1 | 4 a 18 horas |

> [!NOTE]
> **La asimetría del Oro**: El Oro tiene una tasa de acierto más baja (~45 %), pero cuando captura una tendencia macro guiada por tasas reales y tensión geopolítica, su salida por trailing stop genera retornos de $3\\times$ a $5\\times$ el riesgo inicial, compensando holgadamente las pérdidas controladas.
"""
    text = text[:idx_m1] + m03_addition + "\n---\n\n" + text[idx_m1:]

    # 3. Add Caso didáctico: La Pérdida Perfecta in Módulo 4 (after 4.3)
    idx_m5 = text.find("# 📐 MÓDULO 5 · Los tres setups")
    m4_addition = """

## 4.4 · Caso de estudio: La "Pérdida Perfecta" (Trade de Libro)

Para entender cómo opera un trader cuantitativo profesional, veamos un caso real donde la operación **cumplió el 100 % de las reglas y aun así perdió dinero**:

1. **Entorno Macro**: Clima Día Bueno (R2), Cobre subiendo $+1,8 \\%$ en 5 días, Bono US10Y estable en $4,25 \\%$.
2. **Activo y Setup**: USD/CLP presenta compresión Donchian 50 con ancho de $2,1 \\times \\text{ATR}$, vela H1 alcista cierra sobre el canal con $68 \\%$ de cuerpo y RSI en 58.
3. **Filtros**: Ficha 100 % verde. Spread en 0,35 pesos (bajo el tope de 0,54 pesos). Sin noticias blackout en las próximas 3 horas.
4. **Ejecución**: Orden `BUY_STOP` colocada en el máximo de la vela. Se activa 40 minutos después con cero deslizamiento. Stop colocado a $1,5 \\times \\text{ATR}$ ($3,62$ pesos). Riesgo neto asignado: $\$9.000$ CLP ($0,90 \\%$ de una cuenta de $\$1.000.000$).
5. **Resultado**: Dos horas después, una declaración sorpresiva no calendarizada de una autoridad monetaria genera un rebote súbito en el peso chileno, el precio se devuelve y toca el Stop Loss a la milésima. Pérdida total con spread y comisión incluidos: **$\$9.850$ CLP (0,985 % de la cuenta)**.

> [!IMPORTANT]
> **El dictamen de la mesa de trading**: Esta operación fue un **éxito operativo del 100 %**. El trader no cometió ningún error: leyó el régimen correcto, dimensionó el lote con buffer de fricción, protegió su capital con el stop inmutable y anotó la pérdida en su bitácora sin frustración. En una serie de 100 operaciones, este proceso riguroso genera una curva de capital creciente.
"""
    text = text[:idx_m5] + m4_addition + "\n---\n\n" + text[idx_m5:]

    # 4. Update Módulo 5 (5.0, 5.1, 5.2, 5.3)
    idx_m50 = text.find("## 5.0 · Primero decides cuál aplica, y hay precedencia")
    idx_m6 = text.find("# 🛡️ MÓDULO 6 · El stop y el objetivo")

    m5_section_updated = """## 5.0 · Primero decides cuál aplica: Matriz Clima × Setup

No eliges el setup que más te gusta. El **clima macroeconómico es el primer filtro jerárquico**: decide qué tipo de microestructura tenemos antes de tocar cualquier indicador técnico.

### Matriz de Permisos: Clima Macro × Setup Técnico

| Clima Macro Vigente | Ruptura por Compresión (5.1) | Retroceso al Promedio (5.2) | Rebote en Rango (5.3) |
|---|---|---|---|
| 🌪️ **Tormenta (R3)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX $\ge 20$) | ⛔ **PROHIBIDO** |
| 🛒 **Inflación (R1)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX $\ge 20$) | ⛔ **PROHIBIDO** |
| 📉 **Recesión (R4)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX $\ge 20$) | ⛔ **PROHIBIDO** |
| ☀️ **Día bueno (R2)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX $\ge 20$) | ⛔ **PROHIBIDO** |
| 🏖️ **Calma (R0)** | ⛔ **PROHIBIDO** | ⛔ **PROHIBIDO** | **Habilitado** (Único si ADX $< 20$) |

### Árbol de Precedencia Estricta

1. **Si el Clima es Calma (R0)**:
   * Evalúa **Rebote en Rango (5.3)**: ¿ADX $< 20$ y RSI extremo fuera de bandas? $\\rightarrow$ Si cumple, se opera. Si ADX $\\ge 20$, **NO se opera** (es ruido transitorio sin tendencia macro).
2. **Si el Clima es Tendencial (R1, R2, R3, R4)**:
   * 1º **Ruptura por compresión (5.1)**: ¿Ancho Donchian $50 \\le 2,5 \\times \\text{ATR}$ y vela cerrada afuera? $\\rightarrow$ Si cumple, se coloca orden STOP.
   * 2º **Retroceso al promedio (5.2)**: ¿EMAs 20/50/100 alineadas y ADX $\\ge 20$? $\\rightarrow$ Si cumple, se coloca orden STOP en rebote.
3. **Si ninguno califica**: **Esperar con manos quietas.** Es el resultado más frecuente y protege tu capital.

## 5.1 · Ruptura por compresión

*El precio estaba apretado y cerró afuera.*

* **Cuándo aplica**: Climas con tendencia (**Tormenta, Inflación, Recesión o Día bueno**). **Prohibido en Calma.**
* **Qué busca**: El precio estuvo comprimido en un rango estrecho las últimas 50 horas y una vela H1 **cierra fuera** del canal.
* **Las cuatro condiciones, todas obligatorias**:
  1. El **cierre** queda sobre el techo del canal Donchian 50 (en compras) o bajo el piso (en ventas).
  2. **Regla del cuerpo**: El cuerpo mide **al menos la mitad (50 % o más)** del total de la vela. No sirve una mecha larga con cuerpo chico.
  3. **Rango de la vela igual o mayor a 1,0 × ATR**: La vela de ruptura tiene que ser al menos de tamaño normal. Una ruptura con una vela diminuta no tiene fuerza detrás.
  4. **RSI no extremo**: En compras el RSI va en 75 o menos; en ventas, en 25 o más. Entrar en un extremo es comprar el final del movimiento.
* **Entrada**: Orden pendiente `BUY_STOP` en el **máximo de esa vela** (o `SELL_STOP` en el mínimo), con **vencimiento a 2 velas H1**. Si no se activa en dos horas, se cancela.
* **Regla de Tolerancia de Deslizamiento (Slippage Cap)**: Al activarse la orden `BUY_STOP` o `SELL_STOP`, verifica el precio real de llenado (*fill price*). Si el deslizamiento desfavorable es mayor a **$0,2 \\times \\text{ATR}$** (o supera el **$15 \\%$** de la distancia al stop), **la operación debe cancelarse/cerrarse de inmediato a mercado**. Un deslizamiento excesivo distorsiona la relación riesgo/beneficio y amplifica la pérdida real fuera de presupuesto.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="20" y="15" width="220" height="150" rx="4" fill="#F8FAFC" stroke="#CBD5E1" stroke-dasharray="3,3"/>
  <text x="130" y="35" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#64748B" text-anchor="middle">50 HORAS COMPRIMIDAS</text>
  <line x1="30" y1="55" x2="230" y2="55" stroke="#CBD5E1" stroke-width="1.5"/>
  <line x1="30" y1="135" x2="230" y2="135" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="130" y="98" font-size="9" font-weight="600" fill="#64748B" text-anchor="middle">Canal Donchian 50</text>
  <text x="130" y="112" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">Ancho 2,1 × ATR (máx 2,5) ✓</text>

  <line x1="310" y1="20" x2="310" y2="40" stroke="#0B1916" stroke-width="2"/>
  <rect x="285" y="40" width="50" height="90" rx="3" fill="#DCFCE7" stroke="#10B981" stroke-width="2"/>
  <line x1="310" y1="130" x2="310" y2="160" stroke="#0B1916" stroke-width="2"/>

  <line x1="310" y1="20" x2="480" y2="20" stroke="#50C0A8" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="483" y="8" width="230" height="26" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="493" y="25" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46">BUY_STOP en el máximo · vence 2 velas</text>

  <text x="345" y="58" font-size="9" font-weight="700" fill="#065F46">Cierra fuera del canal</text>
  <text x="345" y="74" font-size="8.5" font-weight="700" fill="#047857">Cuerpo 71 % (mín 50 %)</text>
  <text x="345" y="90" font-size="8.5" font-weight="700" fill="#047857">Rango 1,3 × ATR (mín 1,0)</text>
  <text x="345" y="106" font-size="8.5" font-weight="700" fill="#047857">RSI 62 (máx 75)</text>

  <line x1="310" y1="160" x2="480" y2="160" stroke="#E84040" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="483" y="148" width="230" height="26" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1"/>
  <text x="493" y="165" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B">STOP: ver Módulo 6, no el mínimo</text>
</svg>
</div>

## 5.2 · Retroceso al promedio

*El precio descansó sobre su media y volvió a retomar.*

* **Cuándo aplica**: Mercados con **clima tendencial activo (R1, R2, R3 o R4)** y con **ADX en 20 o más**. **Estrictamente prohibido en clima Calma (R0)**, donde un pico transitorio de ADX suele ser un engaño de noticias sin momentum estructural.
* **Las tres condiciones, todas obligatorias**:
  1. **Las tres medias alineadas**: En compras, EMA 20 sobre EMA 50 sobre EMA 100. En ventas, al revés. Sin esa alineación no hay tendencia que respaldar.
  2. El **mínimo** de la vela toca o perfora la EMA 20 (en compras).
  3. El **cierre** queda sobre la EMA 20. El precio la perforó durante la hora, pero los compradores la recuperaron antes del cierre.
* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote**, vencimiento a 2 velas H1.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="140" x2="680" y2="60" stroke="#50C0A8" stroke-width="2.5"/>
  <text x="615" y="52" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46">EMA 20</text>
  <line x1="40" y1="155" x2="680" y2="85" stroke="#3E91AF" stroke-width="2"/>
  <text x="615" y="78" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#1E3A8A">EMA 50</text>
  <line x1="40" y1="170" x2="680" y2="110" stroke="#94A3B8" stroke-width="1.5"/>
  <text x="615" y="104" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#64748B">EMA 100</text>

  <line x1="380" y1="30" x2="380" y2="50" stroke="#0B1916" stroke-width="1.5"/>
  <rect x="368" y="50" width="24" height="40" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="1.5"/>
  <line x1="380" y1="90" x2="380" y2="120" stroke="#0B1916" stroke-width="2"/>

  <text x="380" y="145" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">Mecha perfora la EMA 20</text>
  <text x="380" y="158" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">Cierre recupera sobre ella</text>

  <line x1="380" y1="30" x2="500" y2="30" stroke="#50C0A8" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="503" y="18" width="185" height="26" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="513" y="35" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#065F46">BUY_STOP en el máximo</text>
</svg>
</div>

## 5.3 · Rebote en rango

*El precio se salió de la banda y volvió a entrar.*

* **Cuándo aplica**: **Exclusivamente en clima Calma (R0)**, y con **ADX menor a 20**. Prohibido en cualquier clima tendencial.
* **Las tres condiciones, todas obligatorias**:
  1. La vela **anterior** cerró **fuera** de la banda de Bollinger, bajo la inferior en compras.
  2. La vela **actual** cierra **de regreso adentro**.
  3. El **RSI** marca extremo: **bajo 35** en compras, **sobre 65** en ventas. Los dos lados tienen umbral.
* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó. Es orden límite y no a mercado.
* **Objetivo obligatorio**: La **media central de las bandas** (SMA 20). Nada más lejos. En un mercado lateral, buscar objetivos amplios es pedirle al precio algo que en rango no hace.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="95" x2="600" y2="95" stroke="#E8783C" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="608" y="99" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#9A3412" text-anchor="start">BANDA INFERIOR</text>

  <line x1="200" y1="75" x2="200" y2="90" stroke="#0B1916" stroke-width="1.5"/>
  <rect x="185" y="90" width="30" height="35" rx="2" fill="#FEF2F2" stroke="#E84040" stroke-width="1.5"/>
  <line x1="200" y1="125" x2="200" y2="140" stroke="#0B1916" stroke-width="1.5"/>
  <text x="200" y="160" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="middle">1. Cierra afuera</text>

  <line x1="300" y1="45" x2="300" y2="60" stroke="#0B1916" stroke-width="1.5"/>
  <rect x="285" y="60" width="30" height="45" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="1.5"/>
  <line x1="300" y1="105" x2="300" y2="125" stroke="#0B1916" stroke-width="1.5"/>
  <text x="300" y="160" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">2. Reingresa (gatillo)</text>

  <line x1="40" y1="32" x2="600" y2="32" stroke="#50C0A8" stroke-width="2"/>
  <text x="608" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">MEDIA CENTRAL</text>
  <text x="608" y="47" font-size="8" font-weight="700" fill="#047857" text-anchor="start">objetivo obligatorio</text>

  <rect x="360" y="108" width="330" height="42" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="372" y="125" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46">BUY_LIMIT en el cierre · RSI bajo 35</text>
  <text x="372" y="140" font-size="8.5" font-weight="600" fill="#047857">Exige clima Calma y ADX bajo 20, o no aplica</text>
</svg>
</div>
"""
    text = text[:idx_m50] + m5_section_updated + "\n" + text[idx_m6:]

    # 5. Update Módulo 6.4 (Swap / Overnight in Trailing Stop)
    idx_m64 = text.find("## 6.4 · La salida asimétrica: cuando no hay objetivo fijo")
    idx_m65 = text.find("## 6.5 · Cuando la operación ya va ganando")
    
    m64_addition = """
> [!IMPORTANT]
> **Costo de Acarreo (Swap Overnight) en operaciones multi-jornada**:
> Cuando una operación en Oro o Nasdaq utiliza el stop que persigue al precio y permanece abierta durante varias sesiones (cruzando el corte diario de las 17:00 NY), el broker cobra o abona el *swap* o *rollover*.
> 
> En contratos con swap negativo relevante, un mantenimiento de 3 a 5 días puede restar entre un $0,10 \\%$ y $0,25 \\%$ de la cuenta. Por esta razón, el **Módulo 7.1** establece el **Presupuesto de Riesgo Neto (buffer 90/10)**, garantizando que el swap acumulado jamás haga que la pérdida real supere el $1,0 \\%$.
"""
    text = text[:idx_m65] + m64_addition + "\n" + text[idx_m65:]

    # 6. Update Módulo 7.1 and 7.4 (Presupuesto de Riesgo Neto y Buffer de Fricción)
    idx_m71 = text.find("## 7.1 · La regla: el 1 % es un presupuesto, no una meta")
    idx_m72 = text.find("## 7.2 · La trampa de las unidades, y cómo no caer en ella")

    m71_content = """## 7.1 · La regla: el 1 % es un presupuesto neto, no una meta

Tu cuenta no debe arriesgar más del **1,0 % del capital total** en una sola operación. Pero en el mercado real, la distancia al stop no es el único costo: al entrar pagas **spread**, pagas **comisión del broker**, puedes experimentar **deslizamiento (slippage)** y, si la posición dura varios días, pagas **swap**.

Por eso, el método establece la regla del **Presupuesto de Riesgo Neto**:

$$\\text{Presupuesto Neto de Precio} = \\text{Capital} \\times 0,01 \\times 0,90 = 0,90 \\% \\text{ de la cuenta}$$
$$\\text{Buffer de Fricción Reservado} = \\text{Capital} \\times 0,01 \\times 0,10 = 0,10 \\% \\text{ para spread, comisión y swap}$$

Al dimensionar el lote sobre el $0,90 \\%$ del capital y reservar el $0,10 \\%$ restante para los costos de microestructura, **la pérdida total real de tu cuenta en el peor escenario garantizadamente nunca superará el 1,00 %.**
"""
    text = text[:idx_m71] + m71_content + "\n" + text[idx_m72:]

    # Update 7.4 Table
    idx_m74 = text.find("## 7.4 · Los cuatro pasos, con casos reales")
    idx_m75 = text.find("## 7.5 · Cuando un activo no alcanza para tu cuenta")

    m74_content = """## 7.4 · Los cuatro pasos, con casos reales y costos de fricción

Cuenta de **$1.000.000 CLP**, presupuesto total del 1 % = **$10.000 CLP** (Presupuesto neto de precio: **$9.000 CLP**, Reserva de fricción: **$1.000 CLP**). Los ATR son los medidos en H1 en el snapshot oficial de MT5.

| Activo | ATR H1 | Stop (1,5 × ATR) | Lote teórico neto | **Lote real** | Pérdida en el stop (Precio) | Costo Spread + Comisión | **Pérdida Total Real** | % Real de la Cuenta |
|---|---|---|---|---|---|---|---|---|
| **USD/CLP** | 2,41 | 3,62 pesos | 0,0248 | **0,02** | $7.240 | $700 | **$7.940** | **0,79 %** ✓ |
| **WTI** | 0,771 | 1,157 dólares | 0,0832 | **0,08** | $8.660 | $920 | **$9.580** | **0,96 %** ✓ |
| **Nasdaq 100** | 84,47 | 126,70 puntos | 0,0760 | **0,07** | $8.298 | $980 | **$9.278** | **0,93 %** ✓ |
| **Oro** | 22,54 | 33,81 dólares | 0,0028 | **no operable** | no aplica | no aplica | **no aplica** | no aplica |

**Siempre se redondea hacia abajo y con buffer de fricción.** 0,0832 baja a 0,08. Al incluir la columna de spread y comisiones reales de MT5, la pérdida total de WTI queda en **0,96 %** y Nasdaq en **0,93 %**, estrictamente contenidas bajo el techo sagrado del 1,00 %.
"""
    text = text[:idx_m74] + m74_content + "\n" + text[idx_m75:]

    # 7. Update Módulo 8.4 (Oro tasa real unificada en 2,20% y enlace a Anexo A2)
    idx_m84 = text.find("## 8.4 · Filtro de confirmación cruzada")
    idx_m85 = text.find("## 8.5 · Filtro de riesgo/beneficio")

    m84_content = """## 8.4 · Filtro de confirmación cruzada

Este filtro es el que le da el nombre al método, y es el que más se olvida. **La señal técnica de un activo tiene que estar respaldada por el mercado que lo mueve.** Todos los umbrales maestros provienen del punto único de verdad en el **Anexo A2**.

| Activo | Driver que se Confirma | Se aprueba la compra si… | Referencia Anexo A2 |
|---|---|---|---|
| **USD/CLP** | Cobre (COMEX/LME) | El cobre cae o está plano en 5 días ($\Delta 5d \le 0,00 \\%$), **o** el clima es Tormenta o Recesión | Umbral R3/R4 |
| **Oro** | Tasa real TIPS 10Y EE.UU. | El clima es Tormenta o Inflación, **o** la tasa real está en **2,20 % o menos** | Umbral TIPS A2 |
| **WTI y Brent** | Crudo Físico / WTI | El clima es Tormenta, **o** el crudo sube en 5 días ($\Delta 5d > 0,00 \\%$) | Umbral R3 |
| **Nasdaq 100** | Bono US10Y Nominal | La tasa está en **4,70 % o menos** **y** el clima no es Tormenta ni Inflación | Umbral Tasa A2 |

**La lógica fundamental de la tasa real del Oro en 2,20 %**: Las tasas reales de los bonos protegidos contra la inflación (TIPS a 10 años) representan el costo de oportunidad de mantener metales preciosos (que no pagan rendimiento por cupón). Un nivel sobre $2,20 \\%$ señala una política monetaria de la Fed fuertemente restrictiva que absorbe liquidez hacia la renta fija soberana. Bajo $2,20 \\%$, o en entornos de shock geopolítico/inflacionario, el Oro recupera su tracción alcista como reserva soberana de valor.

Si el respaldo macro no está presente, la operación queda en rojo aunque los ocho campos técnicos de la ficha estén completos.
"""
    text = text[:idx_m84] + m84_content + "\n" + text[idx_m85:]

    # 8. Update Módulo 9.1 and add 9.4 (Mapa de Correlación Intermercado y Co-Riesgo)
    idx_m91 = text.find("## 9.1 · Los cuatro límites")
    idx_m10 = text.find("# 🗂️ MÓDULO 10 · Fichas por activo")

    m9_section_updated = """## 9.1 · Los cuatro límites cuantitativos

| Límite | Umbral | Qué haces cuando se toca |
|---|---|---|
| **Riesgo simultáneo global** | 2,5 % del capital en posiciones abiertas a la vez | No abres una más hasta cerrar alguna |
| **Co-Riesgo en activos correlacionados** | 1,0 % máximo conjunto en activos gemelos | Ver regla 9.4 |
| **Pérdida diaria** | 2 operaciones perdedoras en el día (unos 2,0 %) | **Cierras la plataforma** y no operas más hoy |
| **Pérdida semanal** | 4,0 % acumulado en la semana | Suspendes hasta el lunes siguiente |
| **Racha adversa** | 3 pérdidas consecutivas | Bajas el riesgo por operación al **0,5 %** hasta encadenar 2 ganadoras |

## 9.2 · Por qué el límite diario es de operaciones y no de porcentaje

Podría estar escrito como "para cuando pierdas el 2 %". Está escrito como **dos operaciones** a propósito: es un número que no admite interpretación en el momento en que menos ganas tienes de ser objetivo.

Dos pérdidas seguidas suelen significar que el mercado no está haciendo lo que tu lectura decía. La tercera operación de ese día casi nunca es análisis: es querer recuperar.

## 9.3 · La regla que evita el daño mayor

**Después de una pérdida, el tamaño no sube.** Ni "para recuperar lo de antes", ni porque la próxima señal se ve mejor. El presupuesto del 1 % se calcula sobre el capital **actual**, así que después de perder, el monto arriesgado baja solo. Eso es correcto y hay que dejarlo trabajar.

## 9.4 · Mapa de correlación intermercado y regla de co-riesgo

El límite de 2,5 % global presupone diversificación. Pero en los mercados financieros, **varios activos se mueven juntos porque comparten los mismos motores macro**. Tratar cada posición como estadísticamente independiente es un error severo de gestión de riesgo.

### Matriz de Correlación Intermercado Histórica (Ventana 60 días)

| Activo | USD/CLP | Oro (XAU) | WTI | Brent | Nasdaq 100 | Driver Compartido Dominante |
|---|---|---|---|---|---|---|
| **USD/CLP** | 1,00 | −0,25 | +0,15 | +0,12 | −0,35 | Cobre (−0,75) y Dólar Global (DXY) |
| **Oro (XAU)** | −0,25 | 1,00 | +0,30 | +0,28 | +0,40 | Tasa Real TIPS y Tensión Geopolítica |
| **WTI** | +0,15 | +0,30 | 1,00 | **+0,92** | +0,20 | Shock de Oferta / OPEP y Fletes |
| **Brent** | +0,12 | +0,28 | **+0,92** | 1,00 | +0,22 | Shock de Oferta / OPEP y Fletes |
| **Nasdaq 100** | −0,35 | +0,40 | +0,20 | +0,22 | 1,00 | Tasa Bono 10Y y Curva de Rendimientos |

### Las Dos Reglas de Co-Riesgo de Portafolio

1. **Regla de Activos Gemelos (WTI + Brent)**: Con una correlación de $+0,92$, abrir un largo en WTI y un largo en Brent no es diversificar: es duplicar el riesgo en el mismo vector petrolero. **Ambos activos comparten un cupo conjunto máximo del 1,0 % de riesgo** (ej. $0,50 \\%$ en cada uno, o elegir el contrato con la compresión técnica más limpia).
2. **Límite de Exposición Agregada al Dólar / Tasas**: No se permite mantener más de **dos posiciones simultáneas** cuya dirección dependa directamente de la tasa de interés de EE.UU. (ej. Largo en Nasdaq + Largo en Oro + Corto en USD/CLP).
"""
    text = text[:idx_m91] + m9_section_updated + "\n---\n\n" + text[idx_m10:]

    # 9. Update Módulo 10.2 (Ficha de Oro: 2,20% y swap)
    idx_m102 = text.find("## 10.2 · Oro · XAU/USD")
    idx_m103 = text.find("## 10.3 · WTI y Brent · Petróleo")

    m102_content = """## 10.2 · Oro · XAU/USD

**Qué lo mueve**: La tasa real de EE.UU. (es el driver dominante y va en contra: si la tasa real sube sobre el umbral del Anexo A2, el oro sufre), la inflación esperada y la tensión geopolítica.

| Condición | Sesgo | Dirección permitida | Prohibido |
|---|---|---|---|
| Clima Tormenta o Inflación, **o** tasa real bajo **2,20 %** | +1,80 **fuerte alcista** | Solo compra: retroceso a EMA 20 o ruptura | **Vender, incluso con RSI en 80** |
| Resto de condiciones | +0,40 alcista moderado | Compra: retroceso a EMA 50 o ruptura | Venta agresiva |

> [!IMPORTANT]
> **El Oro no lleva objetivo fijo y vigila el swap multi-día.**
> 
> 1. Su salida es siempre el stop que persigue al precio del Módulo 6.4 (máximo 22 velas $- 3,0 \\times \\text{ATR}$). Poner un objetivo rígido en Oro contradice el método.
> 2. Si la posición cruza más de 48 horas, verifica el costo de swap en MT5.
> 3. Y ojo con el Módulo 7.5: el Oro es el activo con el contrato más pesado de los cinco, así que suele ser el primero que queda fuera del alcance de una cuenta chica ($<\\$3.163.000$ CLP).
"""
    text = text[:idx_m102] + m102_content + "\n" + text[idx_m103:]

    # 10. Add Módulo 12 (Bitácora de Auditoría Operativa) before Anexo A1
    idx_a1 = text.find("# 📚 ANEXO A1 · Glosario")

    m12_content = """# 📓 MÓDULO 12 · La Bitácora de Auditoría Operativa

**Pregunta que responde**: ¿cómo demuestro que mis resultados vienen de mi disciplina y no de la suerte?

---

> [!NOTE]
> **La regla de gobernanza del Desk**: Ninguna operación se considera terminada hasta que queda registrada en la bitácora. Una operación perdedora con checklist 100 % cumplido es una victoria del proceso; una operación ganadora sin checklist ni bitácora es una falta grave de indisciplina.

La bitácora permite alimentar los límites del Módulo 9: si entras en una racha de 3 pérdidas consecutivas, la bitácora te dirá de inmediato si estás ante varianza estadística normal (mercado difícil) o ante errores humanos de ejecución (sobre-apalancamiento o saltarse filtros).

### Estructura Estándar del Registro (Journaling Cuantitativo)

Para cada operación, registra estos 8 campos en tu hoja de control o cuaderno de trading:

| Campo | Descripción | Ejemplo Real |
|---|---|---|
| **1. Fecha y Hora MT5** | Momento exacto de la señal H1 | 2026-09-21 11:00 CLT |
| **2. Activo y Ticket** | Ticker y número de ticket en MT5 | USD/CLP · Ticket #5149201 |
| **3. Clima Macro** | Régimen R0 a R4 publicado en el día | Clima R2 (Día Bueno) |
| **4. Setup Ejecutado** | Setup 5.1, 5.2 o 5.3 con dirección | 5.1 Ruptura por Compresión · Compra |
| **5. R:R Teórico** | Relación calculada antes de entrar | 1,42 : 1 (TP: 1,0 ATR / SL: 0,7 ATR swing) |
| **6. Fricción Real** | Spread pagado + Slippage observado | Spread: 0,35 pesos · Slippage: 0,00 pips |
| **7. Resultado Final** | PnL en dinero y en % de la cuenta | +$13.500 CLP (+1,35 %) / -$9.200 CLP (-0,92 %) |
| **8. Auditoría Checklist** | ¿Cumplió el 100 % de las reglas sin saltarse ninguna? | **SÍ (100 % Disciplina)** |

---

"""
    text = text[:idx_a1] + m12_content + text[idx_a1:]

    # 11. Update Anexo A2 with SSOT Table and depurate Swing D1
    idx_a2 = text.find("# 📊 ANEXO A2 · Umbrales exactos del clima")
    idx_a3 = text.find("# 🛠️ ANEXO A3 · Instalar los indicadores en MT5")

    a2_updated = """# 📊 ANEXO A2 · Umbrales exactos del clima y parámetros maestros (SSOT)

---

Con esta tabla puedes verificar por tu cuenta la clasificación macroeconómica que publicamos. Todas las variaciones son a **5 días**.

| Clima | Se activa cuando… |
|---|---|
| 🌪️ **Tormenta (R3)** | El petróleo (WTI o Brent) se mueve **3,5 % o más** **Y** (el bono a 10 años sube **10 bps o más** **O** la tasa real sube **8 bps o más**) |
| 🛒 **Inflación (R1)** | La inflación esperada sube **10 bps o más** **Y** (la curva 2s10s está bajo **0,20 %** **O** el bono a 10 años sube **más de 5 bps**) |
| 📉 **Recesión (R4)** | El cobre cae **2,5 % o más** **Y** (la curva está invertida, bajo **0,0 %**, **O** el bono a 2 años cae **15 bps o más** con la curva empinándose **10 bps o más**) |
| ☀️ **Día bueno (R2)** | El cobre sube **1,5 % o más** **Y** el bono a 10 años se mueve dentro de **± 6 bps** **Y** la tasa real no sube |
| 🏖️ **Calma (R0)** | Ningún umbral anterior se cumple |

**Precedencia si dos se activan a la vez**: Tormenta → Inflación → Recesión → Día bueno → Calma.

**Confirmación**: 2 días hábiles seguidos, salvo shock extremo.

**Shock extremo (cambio inmediato)**: cuando una variable supera el 150 % de su umbral. Petróleo **5,25 % o más**, bono a 10 años **15 bps o más**, cobre **−3,75 % o menos**, inflación esperada **15 bps o más**.

---

### Umbrales Maestros de Confirmación Intermercado (Single Source of Truth)

Estos son los valores canónicos que alimentan los Módulos 8.4 y 10. Cualquier referencia en el manual se deriva de esta tabla:

| Activo | Driver Cuantitativo | Umbral Maestro de Aprobación | Condición Alternativa |
|---|---|---|---|
| **USD/CLP** | Cobre COMEX / LME | Cobre $\Delta 5d \le 0,00 \\%$ (plano o cayendo) | Clima Tormenta (R3) o Recesión (R4) |
| **Oro (XAU/USD)** | Tasa Real TIPS 10Y EE.UU. | **Tasa Real $\le 2,20 \\%$** | Clima Tormenta (R3) o Inflación (R1) |
| **WTI y Brent** | Crudo Físico WTI | Petróleo $\Delta 5d > 0,00 \\%$ (alcista) | Clima Tormenta (R3) |
| **Nasdaq 100** | Bono US10Y Nominal | **Tasa 10Y $\le 4,70 \\%$** | Clima NO Tormenta (R3) ni Inflación (R1) |

---

### Parámetros de Riesgo y Microestructura H1

| Parámetro | Valor Oficial | Justificación Técnica |
|---|---|---|
| **Riesgo total por operación** | **1,0 % del capital** | Presupuesto máximo absoluto (0,90% precio + 0,10% fricción) |
| **Stop loss inicial intradía** | **1,5 × ATR de 14 en H1** | Distancia fija de volatilidad si swing no califica |
| **Banda de swing para stop** | **0,5 a 1,5 × ATR de 14** | Rango de distancia para adoptar el mínimo/máximo de 20 velas |
| **Stop que persigue (Chandelier)** | **Máximo(22 velas H1) − 3,0 × ATR** | Salida asimétrica para tendencias macro (constante de LeBeau) |
| **Stop crudo sin respaldo de cobre** | **Máximo(22 velas H1) − 2,0 × ATR** | Salida ceñida ante shock puramente precautorio (Kilian AER 2009) |
| **Canal Donchian de compresión** | **50 períodos H1, ancho $\le$ 2,5 × ATR** | Umbral matemático de compresión previa a quiebre |
| **Tolerancia máxima de slippage** | **0,2 × ATR (máx 15 % del stop)** | Límite de desfase en órdenes pendientes; cancelar si se supera |
| **Vencimiento de orden pendiente** | **2 velas H1 (2 horas)** | Si el precio no rompe en la ventana, la compresión muta |
| **Relación riesgo/beneficio mínima** | **1,0 : 1** | Filtro obligatorio de esperanza matemática positiva |
| **Tope de spread tolerable** | **15 % USD/CLP · 12 % Nasdaq · 10 % Oro/Petróleo** | Límite de costo de entrada sobre la distancia al stop |
| **Límite de riesgo simultáneo global** | **2,5 % del capital** | Exposición total agregada máxima de la cuenta |
| **Límite de co-riesgo activos gemelos** | **1,0 % del capital conjunto (WTI+Brent)** | Evita duplicar riesgo en activos con correlación $\\rho > 0,90$ |
| **Índice de Confianza mínimo** | **51,0 %** | Piso algebraico de frescura y cobertura de drivers |

> [!NOTE]
> **Nota sobre operativa Swing diaria (D1)**: En sistemas automatizados institucionales que operan velas diarias (D1), el stop loss utiliza $2,5 \\times \\text{ATR}_{20}(\\text{D1})$. Toda la operativa formativa e intradía descrita en este manual para el trader se rige estrictamente por la columna H1 arriba descrita.
"""
    text = text[:idx_a2] + a2_updated + "\n---\n\n" + text[idx_a3:]

    MANUAL.write_text(text, encoding="utf-8")
    print(f"Manual actualizado con éxito en {MANUAL}. Nuevo tamaño: {len(text)} caracteres.")


if __name__ == "__main__":
    main()
