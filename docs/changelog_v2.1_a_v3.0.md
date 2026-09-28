# CHANGELOG · De Versión 2.1 a Versión 3.0 Oficial
**Documento:** `MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf`  
**Fecha de Emisión:** Octubre 2026 (Auditoría Técnica Septiembre 2026)  
**Entidad:** Grupo Inteligencia · Departamento de Research y Trading Cuantitativo  
**SSOT Maestro:** `docs/params.yaml`

---

## 1. Resumen Ejecutivo del Cambio

La versión 3.0 resuelve íntegramente las 25+ inconsistencias detectadas en la auditoría técnica v2.1. Se establece una arquitectura de gobernanza estricta donde **ningún umbral o parámetro numérico puede existir en el texto sin estar previamente registrado en `params.yaml` (SSOT)**.

Se preserva el 100 % del valor pedagógico, estilo editorial *Midnight Alpha* y la estructura modular (M0 a M12 + A1 a A3), elevando la precisión cuantitativa, coherencia lógica y rigor legal probabilístico.

---

## 2. Matriz de Decisiones Conceptuales (§1 del Brief)

| ID | Área / Tensión Previa | Resolución Técnica Adoptada (v3.0) |
|---|---|---|
| **D1** | Umbral de Confianza Discrepante (M3.4: 65 %, M11/A2: 51 %) | **Unificación en 51,0 % (inclusive) como SSOT**. M3.4 reescrito: *"Confianza bajo 51,0 % (Umbral maestro A2): el activo no se comunica ni se opera"*. Eliminada toda mención a 65 % en confianza. |
| **D2** | Presupuesto del 1 % vs. Gaps/Slippage ("Garantizadamente nunca superará") | **Reformulación como "Presupuesto Objetivo del 1,00 %"**. Se agregó la subsección *"Lo que este presupuesto NO acota"*: (i) Gaps sobre el stop en fines de semana/Oro, (ii) Slippage de ejecución del propio stop, (iii) Swap extremo multi-día. |
| **D3** | Slippage Cap con Disyunción Ambigua (0,2×ATR o 15 % stop) | **Regla Única Cuantitativa**: Si el deslizamiento supera `0,2 × ATR`, la orden pendiente se cancela a mercado de inmediato sin abrir la posición. |
| **D4** | Caso de Estudio M4.4 violaba 3 reglas propias | **Re-hecho Íntegro**: Caso R3 Tormenta compra USD/CLP (sesgo +0,80 institucional), Donchian 50 ancho 2,1 ATR, Stop Swing Rama A (distancia 1,93 = 0,80 ATR), R:R = 1,25 >= 1,0, lote 0,04, pérdida total $8.780 CLP = 0,88 % de la cuenta. Pasa 6/6 checklist M11. |
| **D5** | Confirmación Cruzada Petróleo Tautológica (Δ5d > 0,00 %) | **Umbral de Tendencia Material**: WTI $\Delta 5\text{d} \ge +1,00\%$ en M8.4, Anexo A2 y `params.yaml`. |
| **D6** | Chandelier Trailing Stop sin alcance delimitado | **Delimitación por Activo**: Chandelier aplica a Oro (siempre) y WTI/Brent (con confirmación de cobre). USD/CLP y Nasdaq 100 operan exclusivamente con TP1 y TP2 fijos. |
| **D7** | Break-Even con Gatillo Ambiguo ("cierre de vela a favor") | **Gatillo Cuantitativo Único**: El stop se mueve a precio de entrada en el instante exacto en que el precio alcanza $\text{Entrada} + 0,5 \times (\text{TP1} - \text{Entrada})$. |
| **D8** | Setup 5.3 sin vencimiento ni colocabilidad MT5 | **Formalización**: Vencimiento estricto de 2 velas H1. Nota técnica MT5 sobre colocabilidad de órdenes límite cuando la banda queda sobre el precio actual. |
| **D9** | Exposición agregada a tasas no operacionalizada | **Matriz Direccional de Tasas en M9.4**: Máximo 2 posiciones en la misma dirección de tasa (Largo Oro + Largo Nasdaq + Corto USD/CLP para tasas a la baja; inverso para tasas al alza). |
| **D10** | Parámetros de Setups ausentes del SSOT | **Nueva Sección en Anexo A2 y `params.yaml`**: RSI 75/25, cuerpo >= 50 %, rango >= 1,0 ATR, RSI 35/65, cobre +1,5 % para tamaño WTI. |

---

## 3. Detalle de Correcciones Mecánicas Aplicadas (§2 del Brief)

### Portada y Prefacio
- Actualizada la denominación oficial a **13 módulos (M0 a M12) y 3 anexos**.
- Actualizada la tabla de control de versiones y gobernanza con la entrada v3.0 (Octubre 2026).

### Módulo 0 · Conceptos Base
- **0.2**: Corregido el ejemplo de apalancamiento: *"con $18.680 de garantía puedes mover una posición de $1.868.000 (equivalente a 0,02 lotes del contrato de USD/CLP; el contrato completo es 100.000 USD)"*.
- **0.4**: Incorporada nota metodológica obligatoria al pie de la tabla de expectativas estadísticas: *"Estimaciones orientativas del Desk, no verificadas por backtest público reproducible. No constituyen proyección de rentabilidad"*. Rebajado el tono de "compensando holgadamente" a "buscan compensar".

### Módulo 1 · Gráfico H1
- **1.3**: Actualizado a *"seis indicadores que necesitas en pantalla (ocho líneas en pantalla: 3 EMA)"*, reflejando Donchian 50, EMAs 20/50/100, Bollinger 20/2, ATR 14, RSI 14 y ADX 14.

### Módulo 3 · Climas
- **3.1**: Aclarada la dirección del shock extremo (factor 1,5×): caída de −5,25 % en petróleo activa R4; alza de +5,25 % activa R3.
- **3.4**: Unificado el umbral de confianza en 51,0 % (inclusive).
- **3.5**: Incorporada la regla de **Histéresis de salida del régimen**: un clima deja de estar vigente tras 2 días hábiles consecutivos sin cumplir su condición principal.

### Módulo 4 · Ficha de Operación
- **4.3**: Agregada nota puente de contraste pedagógico entre la ficha rechazada por R:R (0,67) y el caso calificado en 4.4.
- **4.4**: Reemplazado íntegramente por el caso de estudio auditado *"La Pérdida Perfecta (Trade de Libro)"* en USD/CLP bajo clima R3.

### Módulo 5 · Setups
- **5.1**: Fijado slippage cap único a `0,2 × ATR`.
- **5.2**: Incorporada la cláusula formal del *Retroceso a EMA 50* referenciada en M10.
- **5.3**: Añadido vencimiento de 2 velas H1 y advertencia de colocabilidad para órdenes `BUY_LIMIT` en MT5.

### Módulo 6 · Stop y Objetivo
- **6.1**: Rediseñado como HUD de flujo visual continuo de alta legibilidad (viewBox 760x230).
- **6.3**: Añadida advertencia explícita de rechazo si el stop cae en Rama B (1,5×ATR) con TP1 (1,0×ATR) por generar R:R = 0,67 < 1,0.
- **6.4**: Delimitado el Chandelier Trailing Stop a Oro y WTI/Brent, declarando TP1/TP2 fijos para USD/CLP y Nasdaq 100.
- **6.5**: Establecido el gatillo matemático único para Break-Even al 50 % del recorrido hacia TP1.

### Módulo 7 · Tamaño de Posición
- **7.1**: Declarados los tres riesgos residuales no cubiertos por el presupuesto (gaps, slippage del stop, swap extremo).
- **7.3**: Desglosada la tabla de valores por punto en dos columnas ("Decimales típicos" y "Valor de 1 último decimal en CLP"), con advertencia explícita de cotización de 2 vs 3 decimales en Petróleo.
- **7.5**: Actualizado el lote teórico de Oro a **0,0028** y el capital mínimo de cuenta a **$3.514.778 CLP** bajo presupuesto neto.
- **7.6**: Rediseñado como HUD visual de comprobación de margen y solvencia en 3 pasos (viewBox 760x215).

### Módulo 8 · Filtros
- **8.3**: Agregada la columna de *Activos bloqueados* en la tabla de blackout noticioso.
- **8.4**: Fijado el umbral de WTI en $\Delta 5\text{d} \ge +1,00\%$.

### Módulo 9 · Límites y Co-Riesgo
- **9.1**: Racha adversa con buffer 90/10 declarado (0,45 % precio + 0,05 % fricción).
- **9.4**: Incorporada tabla de límites de exposición agregada por dirección de tasa.

### Módulo 10 · Fichas por Activo
- **10.2**: Sincronizado capital mínimo para Oro ($3.514.778 CLP) y cláusula de EMA 50.
- **10.4**: Sincronizada cláusula de EMA 50 en Nasdaq 100.

### Módulo 11 · Checklist de Ejecución
- Sincronizado el primer punto con la verificación de confianza $\ge 51,0\%$ maestro.

### Módulo 12 · Bitácora de Auditoría
- Reemplazado el ejemplo por el caso R3 del manual, con filas independientes para resultados ganadores y pérdidas disciplinadas.

### Anexos A1, A2 y A3
- **A1**: Separadas las definiciones de *Racha* y *Drawdown*.
- **A2**: Marcado como SSOT derivado de `params.yaml`, con nueva sección de *Parámetros de gatillo de setups*.

---

## 4. Estado de Certificación

- **Checklist de Validación Automatizado (§6)**: **16/16 Aprobadas (100 % VERDE)**.
- **Reporte Técnico**: Disponible en [`docs/reporte_validacion_v3.0.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/reporte_validacion_v3.0.md).
- **Fuente SSOT**: Disponible en [`docs/params.yaml`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/params.yaml).
