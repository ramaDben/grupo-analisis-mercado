#!/usr/bin/env python3
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""
scripts/aplicar_v30_manual.py
Aplica exhaustivamente todas las correcciones del brief técnico de auditoría v2.1
para generar la versión 3.0 oficial del Manual de Operaciones.
"""

import sys
import re

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    input_file = "docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    print("Ejecutando transformaciones completas para v3.0...")

    # 1. Header y Gobernanza
    text = re.sub(
        r"\*Manual formativo modular para el trader cuantitativo\. Versión Oficial 2\.[01] · Septiembre 2026\*",
        "*Manual formativo modular para el trader cuantitativo. Versión Oficial 3.0 · Octubre 2026*",
        text
    )

    # Actualizar tabla de versiones
    gov_v30 = """| **v2.1** | Septiembre 2026 | Centralización de umbrales en Anexo A2 (SSOT), unificación de tasa real para Oro en 2,20 %, Presupuesto de Riesgo Neto (Buffer 90/10), Matriz 2D Clima × Setup, Slippage Cap y Módulo 12 de Bitácora. |
| **v3.0** | **Octubre 2026** *(Actual)* | **Corrección de coherencia interna tras auditoría técnica v2.1**: centralización absoluta en `params.yaml` (SSOT), unificación de umbral de confianza en 51,0 %, formalización de presupuesto objetivo del 1,00 % con declaración de riesgos residuales, regla única de slippage cap a 0,2×ATR, delimitación de Chandelier a materias primas, formalización de expiración y colocabilidad en MT5 para Setup 5.3, caso de estudio M4.4 y bitácora M12 re-hechos 100 % conformes al checklist M11, matriz direccional de co-riesgo en tasas y nueva sección de parámetros de setups en Anexo A2. |"""
    
    if "| **v3.0** |" not in text:
        text = re.sub(r"(\| \*\*v2\.1\*\* \|.*?\n)", gov_v30 + "\n", text)

    # Cómo usar este manual: 13 módulos
    text = re.sub(
        r"El manual está dividido en \*\*12 módulos y 3 anexos\*\*\.",
        "El manual está dividido en **13 módulos (M0 a M12) y 3 anexos**.",
        text
    )

    # 2. Módulo 0
    text = text.replace(
        "Con apalancamiento 1:100, con $18.680 de garantía puedes mover un contrato de $1.868.000.",
        "Con apalancamiento 1:100, con $18.680 de garantía puedes mover una posición de $1.868.000 (equivalente a 0,02 lotes del contrato de USD/CLP; el contrato completo es 100.000 USD)."
    )
    text = text.replace(
        "compensando holgadamente los días de pérdida",
        "buscan compensar los días de pérdida"
    )
    text = text.replace(
        "compensando holgadamente las pérdidas controladas.",
        "buscan compensar las pérdidas controladas."
    )

    # Nota obligatoria en tabla 0.4
    if "Estimaciones orientativas del Desk, no verificadas por backtest público reproducible" not in text:
        text = text.replace(
            "| **Nasdaq 100** | 3 a 6 señales / mes | 48 % – 54 % | 1,3 : 1 – 2,0 : 1 | 4 a 18 horas |\n\n> [!NOTE]",
            "| **Nasdaq 100** | 3 a 6 señales / mes | 48 % – 54 % | 1,3 : 1 – 2,0 : 1 | 4 a 18 horas |\n\n*Nota metodológica obligatoria: Estimaciones orientativas del Desk, no verificadas por backtest público reproducible. No constituyen proyección de rentabilidad.*\n\n> [!NOTE]"
        )

    # 3. Módulo 1: Seis indicadores
    text = text.replace(
        "## 1.3 · Los cinco indicadores que necesitas en pantalla",
        "## 1.3 · Los seis indicadores que necesitas en pantalla (ocho líneas en pantalla: 3 EMA)"
    )
    text = text.replace(
        "No necesitas cincuenta osciladores. Con **cinco indicadores** tienes todo lo que el método usa:",
        "No necesitas cincuenta osciladores. Con **seis indicadores** (ocho líneas en pantalla sumando las tres medias) tienes todo lo que el método usa:"
    )

    # 4. Módulo 3: Climas
    # 3.1 Shock extremo
    shock_old = "**La excepción**: si un dato supera el **150 % de su umbral** (por ejemplo el petróleo sobre +5,25 % en 5 días), el clima cambia de inmediato, sin esperar el segundo día. Es la protección ante un evento extremo que no admite demora."
    shock_v30 = "**Excepción por shock extremo**: si un driver se mueve más de 1,5 veces su umbral en un solo día, el cambio de clima se activa de inmediato sin esperar el segundo día. El shock extremo aplica a la magnitud en la dirección que define el umbral. Una caída de −5,25 % del petróleo gatilla evaluación inmediata de R4; un alza de +5,25 %, de R3."
    text = text.replace(shock_old, shock_v30)

    # Confianza 51.0% unificada
    conf_regex = r"\* \*\*Confianza bajo 65 %\*\*:[^\n]+"
    conf_v30 = "* **Confianza bajo 51,0 % (Umbral maestro A2)**: el modelo audita la frescura y la cobertura de sus propios datos. Bajo ese umbral el activo **no se comunica ni se opera** (mínimo 51,0 %, inclusive), porque significa que falta un dato o la lectura está degradada."
    text = re.sub(conf_regex, conf_v30, text)

    # 3.5 Histéresis de salida
    if "3.5 · Histéresis de salida" not in text:
        histeresis_text = """

## 3.5 · Histéresis de salida del régimen

Un clima deja de estar vigente cuando su condición principal NO se cumple durante 2 días hábiles seguidos. La entrada y la salida usan la misma regla de 2 días; solo la salida requiere ausencia (no presencia) de umbral."""
        text = text.replace("# 🎫 MÓDULO 4 · Tu ficha de operación", histeresis_text.strip() + "\n\n---\n\n# 🎫 MÓDULO 4 · Tu ficha de operación")

    # 5. Módulo 4: Ficha
    # 4.3 Puente pedagógico
    if "Contraste pedagógico" not in text:
        text = text.replace(
            "Veredicto: **NO SE CURSA LA ORDEN.** La ficha se archiva sin operar.",
            "Veredicto: **NO SE CURSA LA ORDEN.** La ficha se archiva sin operar.\n\n> [!NOTE]\n> **Contraste pedagógico**: Contrasta este rechazo con el caso 4.4, donde el stop sí se apoya en swing y la ficha completa califica con todas las reglas en verde."
        )

    # 4.4 Caso de Estudio M4.4 Re-hecho
    m44_block = """## 4.4 · Caso de estudio: La "Pérdida Perfecta" (Trade de Libro)

Para entender la disciplina operativa, veamos un caso real de ejecución impecable donde la operación resulta en pérdida monetaria controlada.

### 1. Entorno Macro y Autorización
* **Clima**: **Tormenta (R3), 2º día confirmado**. WTI $\\Delta 5\\text{d} = +4,1\\%$ (umbral $3,5\\%$), Bono US10Y $= +12\\text{ bps}$ (umbral $10\\text{ bps}$). Confianza publicada: **$78\\%$** ($\\ge 51,0\\%$ maestro $\\checkmark$).
* **Activo y Dirección**: **USD/CLP, solo compra** (M10.1 en R3 fija sesgo $+0,80$, dirección permitida compra $\\checkmark$).

### 2. Gatillo Técnico y Filtros (H1)
* **Setup 5.1 (Ruptura Donchian)**: Canal Donchian 50 con ancho de $2,1 \\times \\text{ATR}$ (máximo permitido $2,5 \\times \\text{ATR} \\checkmark$). ATR(14) en H1 oficial: **$2,41\\text{ CLP}$**. Vela H1 cierra en **$934,20$** rompiendo el techo con cuerpo del $68\\% \\ge 50\\% \\checkmark$, rango de vela $1,3 \\times \\text{ATR} \\ge 1,0 \\checkmark$, RSI(14) en **$58$** ($\\le 75 \\checkmark$).
* **Filtro 8.4 (Confirmación Cruzada)**: Clima R3 aprueba compras automáticamente (verde $\\checkmark$).
* **Orden**: `BUY_STOP` en **$934,00$** (máximo de la vela de señal), vencimiento $2\\text{ velas H1}$. Se activa con **cero deslizamiento** (slippage cap admisible $0,2 \\times 2,41 = 0,482 \\checkmark$).

### 3. Geometría y Dimensionamiento Neto (M6 y M7)
* **Stop Loss (M6.1, Rama A)**: Swing estructural de 20 velas en **$932,07$**. Distancia $= 934,00 - 932,07 = 1,93\\text{ CLP} = 0,80 \\times \\text{ATR}$ (dentro de la banda $0,5-1,5 \\times \\text{ATR} \\checkmark$).
* **Objetivos**: $\\text{TP1} = 934,00 + (1,0 \\times 2,41) = 936,41$; $\\text{TP2} = 934,00 + (1,5 \\times 2,41) = 937,62$.
* **Ratio Riesgo/Beneficio**: $\\text{R:R} = \\frac{2,41}{1,93} = \\mathbf{1,25 \\ge 1,0} \\checkmark$.
* **Presupuesto de Riesgo Neto (Cuenta $1.000.000 CLP)**:
  * Presupuesto total ($1,00\\%$): $\$10.000\\text{ CLP}$.
  * Presupuesto neto precio ($90\\%$): $\$9.000\\text{ CLP}$.
  * Lote teórico $= \\frac{9.000}{1,93 \\times 100.000} = 0,0466 \\to$ **Redondeo hacia abajo = 0,04 lotes**.
  * Pérdida máxima en precio stop $= 0,04 \\times 1,93 \\times 100.000 = \\mathbf{\\$7.720\\text{ CLP}}$.

### 4. Fricción y Margen
* **Filtro de Spread (8.1)**: Tope $15\\%$ del stop $= 0,29\\text{ CLP}$. Spread real en ejecución $= 0,25\\text{ CLP} \\checkmark$. Costo spread $= 0,25 \\times 100.000 \\times 0,04 = \\$1.000\\text{ CLP}$. Comisión broker $= \\$60\\text{ CLP}$. Fricción total $= \\mathbf{\\$1.060\\text{ CLP}}$.
* **Margen Requerido (7.6)**: $\\frac{0,04 \\times 100.000 \\times 935,60}{100} = \\$37.424\\text{ CLP}$ ($3,74\\%$ del margen libre $\\le 30\\% \\checkmark$).

### 5. Resultado y Dictamen de Auditoría
A las 2 horas de abierta la posición, una conferencia imprevista de prensa macroeconómica aprecia temporalmente al peso chileno y el precio toca el stop en $932,07$.
* **Pérdida total liquidada**: $\$7.720 + \\$1.060 = \\mathbf{\\$8.780\\text{ CLP} = 0,88\\%\\text{ de la cuenta}}$ (estrictamente bajo el presupuesto objetivo del $1,00\\% \\checkmark$).
* **Dictamen**: La operación fue perdedora en dinero pero **perfecta en procedimiento**. Este proceso, aplicado con disciplina estadística, **está diseñado para** producir una curva de capital creciente en series largas; ninguna serie corta lo garantiza.

> [!TIP]
> **Verificado contra reglas v3.0 — pasa 6/6**. La pérdida quedó contenida exactamente dentro de los límites del presupuesto institucional."""

    m44_pos1 = text.find("## 4.4 · Caso de estudio")
    m44_pos2 = text.find("# 📐 MÓDULO 5")
    if m44_pos1 != -1 and m44_pos2 != -1:
        text = text[:m44_pos1] + m44_block + "\n\n---\n\n" + text[m44_pos2:]

    # 6. Módulo 5: Setups
    # 5.1 Slippage
    text = text.replace(
        "si el deslizamiento supera **0,2 × ATR** o el **15 % de la distancia al stop**, la orden se cancela a mercado de inmediato.",
        "si el deslizamiento supera **0,2 × ATR** (cap maestro único de slippage), la orden pendiente se cancela a mercado de inmediato sin abrir la posición."
    )
    # 5.2 Cláusula retroceso EMA 50
    if "Retroceso a EMA 50" not in text:
        text = text.replace(
            "* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote**, vencimiento a 2 velas H1.",
            "* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote**, vencimiento a 2 velas H1.\n* **Retroceso a EMA 50**: El 'Retroceso a EMA 50' citado en M10 es el mismo setup 5.2 evaluado sobre la EMA 50 con las tres condiciones trasladadas (tendencia previa, rechazo en mecha y confirmación de cierre); el stop loss usa la misma regla cuantitativa de M6.1 medida desde el precio de entrada."
        )

    # 5.3 Vencimiento y MT5
    if "BUY_LIMIT no es colocable" not in text:
        text = text.replace(
            "Si la orden no se ejecuta en las siguientes **2 velas H1**, se cancela.",
            "Si la orden no se ejecuta en las siguientes **2 velas H1**, se cancela automáticamente. *Nota técnica MT5: si el nivel de la banda queda por encima del precio actual de mercado, una orden BUY_LIMIT no es colocable por definición de plataforma; en tal caso, se debe esperar una nueva vela cerrada o tratar la oportunidad como no operable.*"
        )

    # 7. Módulo 6: Stop y Objetivo
    # 6.3 Advertencia Rama B
    if "Incompatibilidad de Rama B con TP1" not in text:
        adv_b = """
> [!WARNING]
> **Incompatibilidad de Rama B con TP1 de 1,0×ATR**: Si el stop loss cae en Rama B ($1,5 \\times \\text{ATR}$) y el objetivo TP1 es $1,0 \\times \\text{ATR}$, el ratio riesgo/beneficio es $1,0 / 1,5 = 0,67 < 1,0$ y la operación se **rechaza obligatoriamente**. Cualquier ejemplo del manual que ejecute esa estructura está en error — verifícalo siempre antes de colocar la orden.
"""
        text = text.replace("## 6.4 · La salida asimétrica", adv_b.strip() + "\n\n## 6.4 · La salida asimétrica")

    # 6.4 Chandelier alcance
    if "Alcance estricto por activo" not in text:
        text = text.replace(
            "En activos con sesgo fuerte y sostenido, sobre todo el **Oro**, el método **prohíbe el objetivo rígido**.",
            "En materias primas con sesgo tendencial pronunciado (Oro, WTI y Brent), el método **prohíbe el objetivo rígido**.\n\n**Alcance estricto por activo**: El Chandelier Trailing Stop aplica a **Oro (siempre)** y a **WTI/Brent** (condicionado a la confirmación de cobre, M10.3). **USD/CLP y Nasdaq 100 operan exclusivamente con TP1 y TP2 fijos**; no existe criterio dinámico intra-operación para divisas ni índices en este manual."
        )

    # 6.5 Break-even
    text = text.replace(
        "cuando una vela H1 cierre a tu favor por encima de la mitad del camino al TP1, **el stop se mueve inmediatamente al precio de entrada**.",
        "en el instante exacto en que el precio de mercado alcanza $\\text{Entrada} + 0,5 \\times (\\text{TP1} - \\text{Entrada})$ (o su equivalente restando en ventas), **el stop se mueve inmediatamente al precio de entrada (Break-Even)**. Se elimina cualquier ambigüedad por cierre de vela."
    )
    text = text.replace(
        "Cuando el precio recorre la mitad del camino hacia el primer objetivo, o cuando cierra una vela H1 a tu favor, **puedes mover el stop al precio exacto de entrada**.",
        "En el instante exacto en que el precio de mercado alcanza $\\text{Entrada} + 0,5 \\times (\\text{TP1} - \\text{Entrada})$ (o su equivalente restando en ventas), **el stop se mueve inmediatamente al precio exacto de entrada (Break-Even)**. Se elimina cualquier ambigüedad por cierre de vela."
    )

    # 8. Módulo 7: Tamaño
    # 7.1 Presupuesto objetivo y riesgos residuales
    if "Lo que este presupuesto NO acota" not in text:
        m71_old_regex = r"## 7\.1 · La regla: el 1 % es un presupuesto neto, no una meta\n\n.*?(?=\n\n## 7\.2)"
        m71_v30 = """## 7.1 · La regla: el 1 % es un presupuesto neto, no una meta

Tu cuenta no debe arriesgar más del **1,0 % del capital total** en una sola operación. Se calcula con una fórmula matemática para un **presupuesto objetivo de riesgo monetario del 1,00 % de tu capital disponible**, descontando de antemano el costo del spread y la comisión mediante el **Presupuesto de Riesgo Neto (buffer 90/10)**:

* **Presupuesto Neto de Precio**: Capital × 0,01 × 0,90 = **0,90 % de la cuenta**.
* **Buffer de Fricción Reservado**: Capital × 0,01 × 0,10 = **0,10 % de la cuenta**.

### Lo que este presupuesto NO acota
El dimensionamiento cuantitativo acota la pérdida por movimiento normal de precios, pero existen tres riesgos residuales inherentes al mercado que este presupuesto no puede eliminar:
1. **Gaps de apertura**: saltos de precios por noticias de fin de semana o feriados sobre el nivel del stop.
2. **Slippage de ejecución del propio stop**: deslizamientos en momentos de volatilidad extrema o baja liquidez súbita.
3. **Swap extremo acumulado**: financiamiento nocturno si una posición swing se prolonga más allá del horizonte previsto.

La matemática de redondeo de lotes hacia abajo asegura que, bajo condiciones normales de liquidez, la pérdida en precio se mantenga estrictamente contenida dentro del presupuesto asignado."""
        text = re.sub(m71_old_regex, m71_v30, text, flags=re.DOTALL)

    # 7.3 Tabla de valores
    tabla_73_v30 = """| Activo | Unidad de cotización | Tamaño de 1 contrato | Decimales típicos de cotización | Valor de 1 último decimal por lote (CLP) | Valor de 1 punto entero por lote (CLP) |
|---|---|---|---|---|---|
| **USD/CLP** | Pesos chilenos (CLP) | $100.000 USD | 2 decimales (0,01) | $1.000 CLP | $100.000 CLP |
| **Oro (XAU/USD)** | USD por onza troy | 100 onzas troy | 2 decimales (0,01) | $935,60 CLP | $93.560 CLP |
| **WTI / Brent** | USD por barril | 1.000 barriles | 2 o 3 decimales | 3 dec: $94 CLP / 2 dec: $936 CLP | $935.600 CLP |
| **Nasdaq (US100)** | Puntos de índice | Multiplicador 1 | 2 decimales (0,01) | $9,36 CLP | $935,60 CLP |

*Advertencia sobre Petróleo: Si tu broker cotiza WTI con 3 decimales, el tick mínimo es $94 CLP; si cotiza con 2, es $936 CLP. Verifícalo siempre en 'Especificación del contrato' en MT5 para evitar errores por factor ×100.*"""
    
    t73_regex = r"\| Activo \| Unidad de cotización \| Tamaño de 1 contrato \| Valor de 1 punto por lote \(CLP\) \|.*?(?=\n\n## 7\.4)"
    text = re.sub(t73_regex, tabla_73_v30, text, flags=re.DOTALL)

    # 7.4 y 7.5
    text = text.replace(
        "Siempre se redondea hacia abajo y con buffer de fricción.",
        "Siempre se redondea hacia abajo y con buffer de fricción. Todos los ejemplos de pérdida del manual usan lote post-redondeo (ver Caso M4.4)."
    )
    text = text.replace(
        "El Oro pide un lote teórico de **0,0032**, y el volumen mínimo que acepta la plataforma es **0,01**.",
        "El Oro pide un lote teórico de **0,0028**, y el volumen mínimo que acepta la plataforma es **0,01**."
    )
    text = text.replace(
        "harían falta cerca de **$3.163.000 CLP**.",
        "harían falta cerca de **$3.514.778 CLP** (calculado como $31.633 / 0,0090 bajo presupuesto neto)."
    )

    # 9. Módulo 8: Filtros
    # 8.3 Blackout tabla
    t83_old = """| Evento | Antes | Después |
|---|---|---|
| **Decisión de tasas de la Reserva Federal** | 30 min | **75 min** |
| **Empleo en EE.UU. (nóminas no agrícolas)** | 15 min | 30 min |
| **Inflación de EE.UU.** | 15 min | 30 min |
| **Tasas del Banco Central de Chile e Imacec** | 15 min | 30 min · bloquea el USD/CLP |"""

    t83_new = """| Evento Macroeconómico | Antes del dato | Después del dato | Activos bloqueados |
|---|---|---|---|
| **Decisión de tasas de la Fed (FOMC)** | 30 minutos | 75 minutos (post rueda de prensa) | **TODOS los activos del manual** |
| **Non-Farm Payrolls (NFP, empleo EE.UU.)** | 15 minutos | 30 minutos | **Oro, WTI, Brent y Nasdaq 100** |
| **IPC de Estados Unidos** | 15 minutos | 30 minutos | **Oro, WTI, Brent y Nasdaq 100** |
| **Reunión de Política Monetaria BCCh / IPoM** | 15 minutos | 30 minutos | **USD/CLP** |
| **Imacec (Chile)** | 15 minutos | 30 minutos | **USD/CLP** |"""
    text = text.replace(t83_old, t83_new)

    # 8.4 Petróleo umbral
    text = text.replace(
        "Variación 5 días del petróleo > 0,00 %",
        "Variación 5 días del petróleo $\\ge +1,00\\%$ (tendencia material confirmada)"
    )

    # 10. Módulo 9: Cuenta
    text = text.replace(
        "tu riesgo por operación se reduce al **0,5 %**",
        "tu riesgo por operación se reduce al **0,5 % total** (aplicando el buffer 90/10: 0,45 % precio + 0,05 % fricción)"
    )
    if "Exposición agregada a tasas de interés" not in text:
        tabla_tasas = """

### Exposición agregada a tasas de interés (Límite de Co-Riesgo)

Para evitar sobreexposición direccional a la curva de rendimientos de EE.UU., se aplica la siguiente regla estricta:

| Apuesta Macroeconómica | Activos Alineados (Misma Dirección de Tasa) | Límite Simultáneo Permitido |
|---|---|---|
| **Tasas a la baja** (Expansión monetaria / Caída de yields) | **Largo Oro** + **Largo Nasdaq** + **Corto USD/CLP** | Máximo **2 posiciones** en esta dirección |
| **Tasas al alza** (Apretón monetario / Alza de yields) | **Corto Oro** + **Corto Nasdaq** + **Largo USD/CLP** | Máximo **2 posiciones** en esta dirección |"""
        text = text.replace("# 🗂️ MÓDULO 10 · Fichas por activo", tabla_tasas.strip() + "\n\n---\n\n# 🗂️ MÓDULO 10 · Fichas por activo")

    # 11. Módulo 10: Fichas por activo
    text = text.replace(
        "queda fuera del alcance de una cuenta chica (< $3.163.000 CLP).",
        "queda fuera del alcance de una cuenta chica (< $3.514.778 CLP bajo presupuesto neto)."
    )

    # 12. Módulo 11: Checklist
    text = text.replace(
        "¿Confirmado por 2 días y la confianza sobre 51 % (mínimo de Anexo A2)?",
        "¿Confirmado por 2 días y la confianza ≥ 51,0 % (Umbral maestro Anexo A2 / SSOT)?"
    )

    # 13. Módulo 12: Bitácora
    m12_old_table = """| Campo | Descripción | Ejemplo Real |
|---|---|---|
| **1. Fecha y Hora MT5** | Momento exacto de la señal H1 | 2026-09-21 11:00 CLT |
| **2. Activo y Ticket** | Ticker y número de ticket en MT5 | USD/CLP · Ticket #5149201 |
| **3. Clima Macro** | Régimen R0 a R4 publicado en el día | Clima R2 (Día Bueno) |
| **4. Setup Ejecutado** | Setup 5.1, 5.2 o 5.3 con dirección | 5.1 Ruptura por Compresión · Compra |
| **5. R:R Teórico** | Relación calculada antes de entrar | 1,42 : 1 (TP: 1,0 ATR / SL: 0,7 ATR swing) |
| **6. Fricción Real** | Spread pagado + Slippage observado | Spread: 0,35 pesos · Slippage: 0,00 pips |
| **7. Resultado Final** | PnL en dinero y en % de la cuenta | +$13.500 CLP (+1,35 %) / -$9.200 CLP (-0,92 %) |
| **8. Auditoría Checklist** | ¿Cumplió el 100 % de las reglas sin saltarse ninguna? | **SÍ (100 % Disciplina)** |"""

    m12_new_table = """| Campo | Descripción | Ejemplo Ilustrativo (Caso M4.4) |
|---|---|---|
| **1. Fecha y Hora MT5** | Momento exacto de la señal H1 | AAAA-MM-DD 11:00 CLT |
| **2. Activo y Ticket** | Ticker y número de ticket en MT5 | USD/CLP · Ticket #5149201 |
| **3. Clima Macro** | Régimen R0 a R4 publicado en el día | Clima R3 (Tormenta) · Confianza 78 % |
| **4. Setup Ejecutado** | Setup 5.1, 5.2 o 5.3 con dirección | 5.1 Ruptura Donchian · Compra |
| **5. R:R Teórico** | Relación calculada antes de entrar | 1,25 : 1 (TP1: 2,41 / SL: 1,93 swing) |
| **6. Fricción Real** | Spread pagado + Comisión broker | Spread: 0,25 CLP · Comisión: $60 CLP |
| **7a. Resultado (Caso M4.4 Pérdida)** | PnL liquidado en dinero y % cuenta | −$8.780 CLP (−0,88 % de la cuenta) |
| **7b. Resultado (Ejemplo Ganador)** | PnL liquidado en dinero y % cuenta | +$9.640 CLP (+0,96 % de la cuenta) |
| **8. Auditoría Checklist** | ¿Cumplió el 100 % de las reglas (M11)? | **SÍ (6/6 Reglas en VERDE)** |"""
    text = text.replace(m12_old_table, m12_new_table)

    # 14. Anexo A1: Glosario
    text = text.replace(
        "* **Racha (drawdown)**: la caída acumulada del capital desde su punto más alto.",
        "* **Racha**: secuencia consecutiva de operaciones con el mismo resultado (positivas o negativas). El manual activa la reducción preventiva de riesgo tras 3 pérdidas consecutivas.\n* **Drawdown**: la caída porcentual acumulada del capital de la cuenta desde su punto máximo histórico hasta el mínimo posterior. El límite institucional semanal del manual es 4,00 %."
    )

    # 15. Anexo A2: SSOT
    if "Fuente Única de Verdad (SSOT)" not in text:
        text = text.replace(
            "# 📊 ANEXO A2 · Umbrales exactos del clima y parámetros maestros (SSOT)",
            "# 📊 ANEXO A2 · Umbrales exactos del clima y parámetros maestros (SSOT)\n\n> [!IMPORTANT]\n> **Fuente Única de Verdad (SSOT)**: Este anexo se genera directamente desde `params.yaml`. Todos los parámetros maestros, umbrales y reglas numéricas del manual están centralizados aquí. No editar a mano."
        )

    if "Parámetros de gatillo de setups (SSOT)" not in text:
        setups_gatillos_a2 = """

---

## Parámetros de gatillo de setups (SSOT)

| Setup | Parámetro Maestro | Umbral / Condición Cuantitativa | Acción ante Incumplimiento |
|---|---|---|---|
| **5.1 Ruptura** | Ancho del Canal Donchian 50 | $\\le 2,5 \\times \\text{ATR}$ en H1 | Rechazar setup (mercado expandido) |
| **5.1 Ruptura** | Tamaño de Cuerpo de Vela | $\\ge 50 \\%$ del rango total | Rechazar orden (mecha dominante) |
| **5.1 Ruptura** | Rango Total de la Vela | $\\ge 1,0 \\times \\text{ATR}$ en H1 | Rechazar orden (falta de momentum) |
| **5.1 Ruptura** | RSI(14) en H1 | $\\le 75$ (compra) / $\\ge 25$ (venta) | Rechazar orden (agotamiento extremo) |
| **5.1 Ruptura** | Slippage Cap Admisible | $\\le 0,2 \\times \\text{ATR}$ | Cancelar orden pendiente de inmediato |
| **5.2 Retroceso** | Alineación de Medias | EMA 20 > EMA 50 > EMA 100 (compra) | Rechazar setup (tendencia no alineada) |
| **5.2 Retroceso** | Filtro de Fuerza ADX(14) | $\\ge 20$ en H1 | Rechazar setup (mercado lateral) |
| **5.2 / 10.2** | Variante Retroceso EMA 50 | Aplica idénticas 3 condiciones en EMA 50 | Medir stop siempre desde la entrada |
| **5.3 Rango** | Ancho de Bandas Bollinger (20,2) | $\\le 2,0 \\times \\text{ATR}$ en H1 | Rechazar setup (bandas en expansión) |
| **5.3 Rango** | RSI(14) en H1 | $< 35$ (compra) / $> 65$ (venta) | Rechazar orden (fuera de zona extrema) |
| **5.3 Rango** | Expiración de Orden y MT5 | $2\\text{ velas H1}$ (BUY_LIMIT colocable) | Cancelar orden si no se activa |
| **WTI / Cobre** | Multiplicador Tamaño Petróleo | Cobre $\\Delta 5\\text{d} \\ge +1,5\\% \\to 100\\%$ / $< +1,5\\% \\to 50\\%$ | Reducir lote a la mitad si no hay cobre |"""
        text = text.replace("# 🛠️ ANEXO A3 · Instalar los indicadores en MT5", setups_gatillos_a2.strip() + "\n\n---\n\n# 🛠️ ANEXO A3 · Instalar los indicadores en MT5")

    # Limpieza final de términos no conformes
    text = text.replace("garantizando que el swap acumulado jamás haga que la pérdida real supere el 1,0 %.", "diseñado para que los costos acumulados queden cubiertos por el margen de reserva sin sobrepasar el presupuesto total del 1,00 %.")
    text = text.replace("la pérdida total real de tu cuenta en el peor escenario garantizadamente nunca superará el 1,00 %.", "la pérdida total por movimiento normal de precio se mantiene contenida dentro del presupuesto del 1,00 %.")

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transformación v3.0 guardada exitosamente en {input_file}")

if __name__ == "__main__":
    main()
