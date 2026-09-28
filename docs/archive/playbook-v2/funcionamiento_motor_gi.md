# Manual de Arquitectura y Funcionamiento: Motor Cuantitativo Grupo Inteligencia (Motor GI)
## Evaluación de Mercado, Modelo ADC+ATR, Capacidad de Trading Táctico y Límites Operativos

**Documento:** Especificación Técnica y Conceptual del Sistema Cuantitativo  
**Área:** Research, Desarrollo Cuantitativo & Trading — Grupo Inteligencia  
**Fecha:** 28 de agosto de 2026  
**Versión:** 2.4 (Post-Auditoría Externa ADC+ATR)  
**Entorno Operativo:** Python 3.12 · MetaTrader 5 API · MCP Servers (Market Data, Brandkit) · FRED & Tesoro US · Banco Central de Chile  

---

## 1. Filosofía y Arquitectura General del Motor GI

El **Motor GI** es un sistema híbrido de inteligencia de mercado que combina **análisis macroeconómico soberano (Top-Down)** con **modelación cuantitativa de series temporales y volatilidad (Bottom-Up)**.

A diferencia de los robots tradicionales de análisis técnico (que analizan velas de forma aislada) o de los modelos econométricos teóricos (que carecen de sincronización intradiaria con los precios), el Motor GI opera bajo una arquitectura de **cinco capas concatenadas**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA 1: INGESTA MACRO Y SOBERANA                     │
│  (FRED, Tesoro EE.UU., BCCh, BCE, BoJ, Calendario Oficial de Eventos)  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 CAPA 2: MOTOR DE SESGO Y REGÍMENES (R0 - R4)           │
│  (Clasificación de Régimen Intermercado, Matriz de Drivers y Sesgos)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│             CAPA 3: GATES DE EXCLUSIÓN Y PROTECCIÓN DE CAPITAL         │
│  (Filtro Feriados, Blackouts Tier-1, Agotamiento D1, Veto de Playbook) │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               CAPA 4: SCREENER CUANTITATIVO (SCORE_GI 0-100)           │
│  (Factor Técnico 35%, Catalizador 25%, Espacio ADC 20%, Momentum 20%) │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│             CAPA 5: MODELACIÓN DE VOLATILIDAD Y SALIDAS                │
│  (Presupuesto ADC+ATR, Niveles Pivote, Stories 16:9/9:16, Mensajes WA) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ingesta de Datos y Fuentes de Verdad

El sistema no depende de opiniones ni estimaciones sintéticas; procesa datos oficiales en tiempo real:

1. **Datos de Mercado en Tiempo Real (Tick & OHLCV):**
   * Conexión directa a través de MetaTrader 5 API (`mt5_client.py`).
   * Timeframes evaluados: **H1 (horario)** para la estructura táctica intradiaria y **D1 (diario)** para el contexto de tendencia y presupuesto diario.
   * Regla de aislamiento: Todos los indicadores de estado se calculan sobre **velas cerradas (`df.iloc[:-1]`)** para evitar la auto-anulación de canales y la distorsión del True Range al abrirse una barra.
2. **Drivers Macroeconómicos Intermercado:**
   * Tasa del Tesoro de EE.UU. a 10 años (DGS10) y spreads de la curva (2Y-10Y, 3M-10Y) extraídos de FRED/Tesoro.
   * DXY (Índice Dólar), Cobre Grado A (LME/COMEX), Petróleo WTI y Brent.
   * Diferenciales de tasas swap (SOFR vs. Cámara Promedio Chile para USD/CLP).
3. **Agenda y Calendario Macroeconómico:**
   * Registro estructurado de eventos de alto y medio impacto (NFP, CPI, FOMC, TPM Banco Central, PIB, Jackson Hole).
   * Mapeo de impacto por activo y sincronización con la hora oficial de Santiago de Chile (`America/Santiago`).

---

## 3. El Motor de Sesgo Macro y Regímenes (Playbook V2)

El motor clasifica el entorno macroeconómico global en uno de **cinco regímenes cuantitativos ($R_0$ a $R_4$)**, los cuales condicionan de forma obligatoria las direcciones operativas permitidas:

| Régimen | Nombre / Entorno | Driver Dominante | Comportamiento Táctico Permitido |
|:---:|---|---|---|
| **$R_0$** | **Normal / Rango** | Volatilidad contenida, sin catalizadores extremos. | Operaciones de reversión a la media entre soportes ($S_1$) y resistencias ($R_1$). |
| **$R_1$** | **Risk-On / Desinflación** | Caída de rendimientos US (UST 10Y $\downarrow$), DXY $\downarrow$, Cobre $\uparrow$. | **Compras en Nasdaq (US100), S&P 500, Cripto y Oro**; **Ventas en USD/CLP**. Prohibidos cortos en índices. |
| **$R_2$** | **Risk-Off / Vuelo a Calidad** | Shock geopolítico o crediticio, VIX disparado, bolsas $\downarrow$. | **Compras en Oro (XAU/USD) y Dólar Global**; **Ventas en Índices y Cripto**. Prohibidas compras en renta variable. |
| **$R_3$** | **Estanflación / Shock Oferta** | Petróleo $\uparrow\uparrow$, Cobre presionado, inflación persistente. | **Compras en Petróleo (WTI/Brent) y Commodities**; **Ventas en Renta Variable y Bonos**. |
| **$R_4$** | **Hawkish Fed / Dólar Fuerte** | Subida de tasas US (UST 10Y $\uparrow$), DXY disparado, Fed restrictiva. | **Compras en USD/CLP y USD/JPY**; **Ventas en Oro, Índices y Monedas Emergentes**. Prohibidos largos en Oro/Nasdaq. |

---

## 4. Algoritmo de Screening Cuantitativo (Score GI - 100 Puntos)

Cada activo del catálogo es sometido al escáner `screener_gi.py`, el cual ejecuta una **evaluación en dos fases**:

### Fase A: Los 4 Gates de Exclusión Binaria (Cero Tolerancia)
Si un activo activa cualquiera de estos 4 gates, queda **inmediatamente descartado (Score = 0)**:
1. **Gate de Feriados (`gate_feriado`):** Excluye activos cuyo mercado de origen esté cerrado (ej. feriado bancario en Chile para USD/CLP o feriado US para índices de Wall Street).
2. **Gate de Agotamiento Diario (`gate_agotamiento`):** Si el rango recorrido hoy en D1 ya consumió **$\ge 90\%$ del $\text{ATR}_{14}\text{ (D1)}$**, el activo queda descartado. *Razón cuantitativa:* Intentar entrar cuando el presupuesto del día está agotado expone al trader a trampas de fin de movimiento y reversiones.
3. **Gate de Blackout Macroeconómico (`gate_blackout`):** Bloquea la emisión de señales en una ventana de **30 minutos antes y 30 minutos después** de un dato Tier-1 (CPI, NFP, Minutas Fed). *Razón cuantitativa:* En un blackout, el libro de órdenes se vacía (*liquidity black hole*), los spreads se multiplican y el análisis técnico pierde consistencia estadística frente al slippage.
4. **Gate de Coherencia con el Playbook (`gate_playbook`):** Si la dirección técnica (H1) contradice el régimen macroeconómico del Playbook (ej. el precio de Oro intenta romper al alza pero el régimen vigente es $R_4$ - Hawkish Fed / Dólar Fuerte), el activo es **vetado**.

---

### Fase B: Ponderación de Factores ($Score\_GI \in [0, 100]$)
Los activos que superan los 4 gates son evaluados en una escala de 100 puntos:

$$\text{Score\_GI} = \text{Factor Técnico (35)} + \text{Factor Catalizador (25)} + \text{Factor Espacio (20)} + \text{Factor Momentum (20)}$$

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ESTRUCTURA DE PUNTUACIÓN                        │
├────────────────────────┬─────────┬─────────────────────────────────────┤
│ Factor                 │ Máximo  │ Criterio Cuantitativo               │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 1. Técnico             │ 35 pts  │ Alineación EMAs (20/50/100) +       │
│                        │         │ Quiebre Donchian 50 / Bandas        │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 2. Catalizador Macro   │ 25 pts  │ Impacto calendario hoy + Variación  │
│                        │         │ en puntos básicos de UST 10Y        │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 3. Espacio ADC + ATR   │ 20 pts  │ Distancia a meta $\ge 1.5\times ATR$│
│                        │         │ con piso de sesión activa ($>15\%$) │
├────────────────────────┼─────────┼─────────────────────────────────────┤
│ 4. Momentum            │ 20 pts  │ ADX > 25 con RSI en zona de         │
│                        │         │ expansión (50-68 alcista / 32-50 b.)│
└────────────────────────┴─────────┴─────────────────────────────────────┘
```

* **Umbral de Calificación:** Solo los activos con **Score $\ge 65/100$** son calificados como oportunidades de alta convicción para el Carrusel de Alertas.

---

## 5. El Modelo ADC + ATR (Ancho Dinámico de Canal + Volatilidad)

El **Modelo ADC + ATR** es el motor central de cálculo de volatilidad del sistema:

### 1. Fórmulas Matemáticas Implementadas
* **ATR (Average True Range):** Suavizado exacto de **Welles Wilder RMA** ($\alpha = 1/\text{periodo}$, equivalente a `span = 27` para 14 períodos) con seed SMA:
  $$TR_t = \max\left(H_t - L_t, \; |H_t - C_{t-1}|, \; |L_t - C_{t-1}|\right)$$
  $$ATR_t = \frac{1}{14} TR_t + \frac{13}{14} ATR_{t-1}$$
* **Canal de Donchian (ADC):** Extremos móviles de 50 barras en H1 calculados sobre velas cerradas:
  $$\text{Donchian High} = \max_{i=1..50}(H_{t-i}), \quad \text{Donchian Low} = \min_{i=1..50}(L_{t-i})$$
* **Impulso Táctico ADC+ATR:** Presupuesto de recorrido tras un quiebre de compresión:
  $$\text{Impulso ADC+ATR} = 1.5 \times \text{ATR}_{14}\text{ (H1)}$$

### 2. Presupuesto de Volatilidad vs. Camino de Precios
* **Concepto Crucial:** El valor arrojado por el modelo ($1.5\times\text{ATR}$) representa un **presupuesto de volatilidad disponible**, es decir, *la amplitud estadística esperada que el activo suele desplegar en una hora de expansión tendencial*.
* **No es una garantía determinista:** Hacia el cliente, este valor se comunica estrictamente como **"Volatilidad típica"** para no inducir a falsas certezas de precio objetivo garantizado sin contexto de liquidez.

---

## 6. ¿Tiene el Motor GI la Capacidad de Definir con Precisión Puntos de Entrada y Salida (Trades)?

### **Respuesta Directa:**
> **SÍ, a nivel de Niveles Estructurales, Triggers Cuantitativos, Stop Loss Basados en Volatilidad y Metas Estadísticas.**  
> **NO, a nivel de ejecución algorítmica de microestructura (Order Flow / Level 2 HFT / Ruteo de Órdenes a Broker).**

A continuación se detalla cómo el motor define con exactitud cada componente de un trade:

```
─────────────────────────────────────────────────────────────────────────────
                             ESTRUCTURA DE UN TRADE
─────────────────────────────────────────────────────────────────────────────
                                                   [ Meta 2 / R2 / Expansión ]
                                                   ▲ (Precio + 1.5x ATR)
                                                   │
                                                   [ Meta 1 / R1 / S/R Estructural ]
                                                   ▲ (S/R Histórico H1)
                                                   │
  ═════════════════════════════════════════════════[ PUNTO DE ENTRADA / TRIGGER ]
                                                   ▲ Quiebre Donchian 50 (Vela cerrada)
                                                   │ o Pullback a EMA 20 en H1
                                                   │
                                                   ▼
                                                   [ STOP LOSS TÁCTICO ]
                                                   (Precio Entrada - 1.0x ATR H1
                                                    o bajo EMA 50 / Soporte S1)
─────────────────────────────────────────────────────────────────────────────
```

### 1. Puntos de Entrada (Triggers de Compra / Venta)
El Motor GI define tres tipos de gatillos precisos de entrada:
1. **Entrada por Ruptura de Compresión (Breakout ADC):**
   * *Regla:* Ruptura confirmada del Canal Donchian de 50 períodos en H1 sobre vela cerrada (`close[t-1] > Donchian_High[50]`), acompañada de $ADX > 25$ y $RSI \in [50, 68]$ en compras.
2. **Entrada por Pullback en Tendencia Estable:**
   * *Regla:* Testeo y rechazo de la **EMA 20 en H1** a favor de la tendencia marcada por la EMA 100, validada con histograma MACD en expansión.
3. **Entrada por Reversión en Rango ($R_0$):**
   * *Regla:* Testeo de la Banda Inferior de Bollinger ($20, 2\sigma$) o Soporte $S_1$ con RSI $< 35$ y divergencia estocástica.

---

### 2. Puntos de Salida: Gestión de Riesgo (Stop Loss)
El motor no utiliza distancias fijas en pips/puntos arbitrarios, sino **Stop Loss Adaptativos calibrados por Volatilidad**:
* **Stop Loss por Volatilidad Táctica:** Fijado a **$1.0 \times \text{ATR}_{14}\text{ (H1)}$** desde el punto de entrada.
* **Stop Loss Estructural:** Ubicado inmediatamente detrás del último mínimo relevante de 20 barras o por debajo de la **EMA 50 en H1**.
* **Invalidación Inmediata:** Si el precio reingresa al canal Donchian y cierra por debajo de la línea media (`donchian_mid`), la tesis cuantitativa queda abortada.

---

### 3. Puntos de Salida: Toma de Beneficios (Take Profit / Metas)
El motor establece metas en dos escalones:
* **Meta 1 (Táctica / Parcial):** El nivel pivote horizontal inmediato más cercano ($R_1$ en compras / $S_1$ en ventas), calculado dinámicamente según la concentración de precios históricos.
* **Meta 2 (Expansión Tendencial):** Proyección del presupuesto completo de volatilidad:
  $$\text{Target}_{\text{Alcista}} = \text{Precio de Entrada} + (1.5 \times \text{ATR}_{14}\text{ H1})$$
  $$\text{Target}_{\text{Bajista}} = \text{Precio de Entrada} - (1.5 \times \text{ATR}_{14}\text{ H1})$$

---

### 4. Dimensionamiento de Posición (Position Sizing por Volatility Targeting)
El motor calcula el lotaje exacto a operar en función del riesgo monetario tolerado:

$$\text{Lote} = \frac{\text{Capital en Riesgo (\$USD)}}{\text{Distancia al Stop Loss (puntos)} \times \text{Valor del Punto por Lote}}$$

* *Ejemplo:* Si el ATR de USD/CLP es $3,50\text{ CLP}$, el Stop Loss es $3,50\text{ CLP}$. Para un riesgo de $\$1.000\text{ USD}$ en una cuenta con valor de punto de $\$1.000\text{ CLP/lote}$, el motor computa exactamente el tamaño de posición para que un stop nunca sobrepase el riesgo presupuestado.

---

## 7. Qué HACE el Motor GI vs. Qué NO HACE

Para mantener una total transparencia operativa, cuantitativa y de cumplimiento normativo, se definen los límites del sistema:

| Capacidad / Función | ¿Lo hace el Motor GI? | Detalle / Justificación Técnica |
|---|:---:|---|
| **Escanear múltiples mercados simultáneamente** | ✅ **SÍ** | Monitorea FX, Commodities, Índices y Cripto en tiempo real vía MT5 API. |
| **Identificar el Régimen Macroeconómico ($R_0-R_4$)** | ✅ **SÍ** | Cruza bonos del Tesoro, DXY, commodities y agenda de bancos centrales. |
| **Filtrar trampas de mercado y falsos quiebres** | ✅ **SÍ** | Aplica 4 gates binarios (feriados, agotamiento D1, blackouts macro, sesgo). |
| **Calcular niveles de Soporte, Resistencia y Pivotes** | ✅ **SÍ** | Calcula niveles $S_1, S_2, R_1, R_2$ basados en clusters y ATR. |
| **Definir Niveles de Entrada, Stop Loss y Take Profit** | ✅ **SÍ** | Define precios exactos de entrada, stops por ATR y metas tácticas. |
| **Calcular el tamaño de posición óptimo (Lotaje)** | ✅ **SÍ** | Utiliza Volatility Targeting y paridad de riesgo por activo. |
| **Generar piezas visuales y mensajes para clientes** | ✅ **SÍ** | Produce Stories de marca (16:9 y 9:16) y textos estructurados para WhatsApp. |
| **Ejecutar órdenes automáticas en el broker (Auto-trading)** | ❌ **NO** | No envía órdenes `buy/sell` directas a mercado; requiere confirmación del trader o gestor. |
| **Lectura de Order Flow / DOM de Nivel 2 en tiempo real** | ❌ **NO** | Opera sobre velas OHLCV de H1/D1 de MT5; no hace micro-lectura de libro de órdenes HFT. |
| **Predecir el futuro o garantizar rentabilidad** | ❌ **NO** | El ATR y los scores modelan probabilidades y distribuciones pasadas, no certezas absolutas. |
| **Emitir asesoría financiera personalizada pública** | ❌ **NO** | En piezas abiertas informa análisis técnico-cuantitativo y volatilidad; la recomendación formal requiere firma acreditada. |

---

## 8. Resumen Ejecutivo del Flujo Operativo Diario

```
  08:30 CLT  ──► Ingesta de Curva del Tesoro (UST 10Y) y Agenda Económica del día.
  09:00 CLT  ──► Clasificación del Régimen de Mercado ($R_0$ a $R_4$) en el Macro Bias Engine.
  09:30 CLT  ──► Apertura de Mercados y Filtrado por Gates (Blackouts, Feriados, Agotamiento).
  10:30 CLT  ──► Ejecución del Screener Cuantitativo (Score GI):
                 • Selección del Top 3 de Activos con mayor convicción ($\ge 65/100$).
                 • Cálculo de Soporte, Resistencia, Entrada, Stop y Volatilidad Típica.
  10:45 CLT  ──► Renderizado automático del Pipeline de Stories (horizontal y vertical) y WhatsApp.
  Durante el día ► Monitoreo de Blackouts: Bloqueo automático ante noticias de alto impacto.
```

---

*Fin del Documento de Especificación del Motor GI.*
