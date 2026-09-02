# Solicitud de Auditoría Cuantitativa Externa
## Vulnerabilidades y Hallazgos Metodológicos en el Modelo ADC + ATR

**Destinatario:** Auditor Cuantitativo Externo / Revisor de Estrategias Cuantitativas  
**Emisor:** Área de Research & Trading — Grupo Inteligencia  
**Fecha:** 28 de agosto de 2026  
**Sistema:** Motor Cuantitativo de Análisis y Señales Intermercado (`Grupo Análisis Mercado`)  
**Entorno Técnico:** Python 3.12 · Pandas · MetaTrader 5 API · Activos FX (USD/CLP), Commodities (Oro, WTI), Índices y Cripto  

---

### 1. Resumen Ejecutivo

El presente informe detalla seis (6) hallazgos críticos detectados tras una auditoría interna adversaria sobre el **Modelo ADC + ATR (Ancho Dinámico de Canal + Average True Range)**, actualmente utilizado para medir la compresión de volatilidad, proyectar impulsos tácticos intradía y evaluar el espacio operativo de los activos en cartera.

Se solicita a la contraparte auditora externa revisar los fundamentos matemáticos, la consistencia de series temporales y la pertinencia estadística de las soluciones propuestas para cada uno de los puntos expuestos.

---

### 2. Hallazgos Técnicos y Vulnerabilidades

#### Hallazgo 1: Discrepancia Matemática en Suavizado de Volatilidad (Wilder RMA vs. Pandas EWMA)

* **Ubicación en Código:** [`src/market_data_mcp/mt5_client.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/src/market_data_mcp/mt5_client.py#L178-L188)
* **Implementación Actual:**
  ```python
  def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
      high = df["high"]
      low = df["low"]
      prev_close = df["close"].shift(1)
      tr = pd.concat([
          high - low,
          (high - prev_close).abs(),
          (low - prev_close).abs(),
      ], axis=1).max(axis=1)
      return tr.ewm(span=period, adjust=False).mean()  # span = 14
  ```
* **Análisis Matemático:**
  En Pandas, el parámetro `span=14` genera un factor de ponderación exponencial:
  $$\alpha_{\text{Pandas}} = \frac{2}{\text{span} + 1} = \frac{2}{15} \approx 0,1333$$
  Sin embargo, el estándar industrial de Welles Wilder (implementado nativamente en MetaTrader 5, TradingView y Bloomberg) utiliza el suavizado recursivo RMA:
  $$\alpha_{\text{Wilder}} = \frac{1}{\text{periodo}} = \frac{1}{14} \approx 0,0714$$
* **Impacto Operativo:**
  La implementación en código otorga un **86,7% más de peso relativo** a la vela más reciente, generando un ATR hiper-reactivo (*jumpy*) que diverge significativamente del indicador oficial del terminal MT5.
* **Propuesta de Corrección:**
  Sustituir `span=period` por `alpha=1.0/period` o `span=2*period - 1` (span 27 para 14 períodos).

---

#### Hallazgo 2: Inhomogeneidad Temporal y Dilución por Velas Nocturnas en FX Local (USD/CLP)

* **Ubicación en Código:** [`scripts/screener_gi.py:569-578`](file:///C:/Users/bbrav/grupo-analisis-mercado/scripts/screener_gi.py#L569-L578) y [`src/market_data_mcp/analisis.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/src/market_data_mcp/analisis.py)
* **Contexto de Mercado:**
  El mercado interbancario de USD/CLP opera con liquidez institucional únicamente entre **09:00 y 16:00 CLT** (7 horas al día). Las 17 horas restantes del día corresponden a cotizaciones residuales con rangos horarios mínimos ($0,10 - 0,30\text{ CLP}$).
* **Análisis del Problema:**
  Al extraer las últimas 14 o 60 velas de H1 durante la apertura matutina (09:30 - 10:30 CLT), entre el **70% y el 80% de la muestra** está compuesta por velas nocturnas sin volumen.
* **Impacto Operativo:**
  El $\text{ATR}_{14}(\text{H1})$ calculado en la mañana arroja un valor artificialmente bajo ($1,75\text{ CLP}$), cuando la volatilidad horaria real de la sesión abierta es de $3,50 - 5,00\text{ CLP}$. Esto induce a proyectar recorridos subdimensionados y fijar Stop Loss demasiado estrechos.
* **Propuesta de Corrección:**
  Filtrar la serie temporal para que el cálculo de $\text{ATR}(\text{H1})$ considere exclusivamente velas dentro del horario oficial de sesión (`horario_mercado: 09:00-16:00 CLT`) o utilizar el promedio ponderado por volumen de ticks.

---

#### Hallazgo 3: Confounding Temporal en el Validador de Consumo Diario

* **Ubicación en Código:** [`scripts/screener_gi.py:487-491`](file:///C:/Users/bbrav/grupo-analisis-mercado/scripts/screener_gi.py#L487-L491)
* **Implementación Actual:**
  ```python
  def factor_espacio(h1: dict[str, Any], d1: dict[str, Any], direccion: str) -> tuple[int, str]:
      ...
      espacio = abs(objetivo - precio) / atr_h1
      atr_d1, rango_hoy = d1.get("atr_14"), d1.get("rango_hoy")
      consumo = (rango_hoy / atr_d1) if (atr_d1 and rango_hoy is not None) else None

      if espacio >= 1.5 and consumo < 0.70:
          return 20, f"espacio {espacio:.1f}x ATR H1 y ATR diario al {consumo:.0%}"
  ```
* **Análisis del Problema:**
  El modelo premia con puntaje máximo ($20/20$) a un activo si $\text{Consumo} = \frac{\text{Rango Hoy}}{\text{ATR}_{14}(\text{D1})} < 70\%$. Sin embargo, en la tanda de apertura (10:30 CLT / apertura NY), **cualquier activo** presenta un consumo bajo simplemente porque la sesión bursátil acaba de comenzar.
* **Impacto Operativo:**
  Se genera un falso positivo estadístico: el factor "Espacio" califica con puntaje perfecto a instrumentos sin impulso real ni quiebre confirmado, confundiendo el tiempo transcurrido con capacidad direccional.
* **Propuesta de Corrección:**
  Normalizar el consumo diario en función del tiempo transcurrido de la sesión:
  $$\text{Consumo Ajustado}(t) = \frac{\text{Rango Real}(t)}{\text{ATR}_{\text{D1}} \times \sqrt{t / T_{\text{total}}}}$$

---

#### Hallazgo 4: Rigidez del Multiplicador de Impulso ($1.5\times$ Estático vs. Modulación por ADX)

* **Ubicación en Código:** [`scripts/screener_gi.py:578`](file:///C:/Users/bbrav/grupo-analisis-mercado/scripts/screener_gi.py#L578)
* **Discrepancia Documental vs. Código:**
  La especificación formal (`CLAUDE.md`) define el impulso como *"1.5 × ATR14 (H1) calibrado con la lectura de tendencia del ADX"*. No obstante, el código aplica estrictamente:
  ```python
  "impulso_adc_atr": round(1.5 * h1["atr_14"], activo["digits"])
  ```
* **Análisis del Problema:**
  El multiplicador $1.5$ no se modula según la fuerza de la tendencia ($\text{ADX}$). Un activo en fase lateral (ADX = 14) recibe la misma proyección de expansión ($1.5\times$) que un activo en ruptura tendencial violenta (ADX = 58).
* **Propuesta de Corrección:**
  Implementar una función de escala dinámica:
  $$k_{\text{impulso}} = 1.0 + \min\left(1.0, \; \frac{\text{ADX}_{14}}{50}\right) \implies k \in [1.0, 2.0]$$

---

#### Hallazgo 5: Contaminación por la Vela en Formación en Tiempo Real (`iloc[-1]`)

* **Ubicación en Código:** [`src/market_data_mcp/mt5_client.py:241-258`](file:///C:/Users/bbrav/grupo-analisis-mercado/src/market_data_mcp/mt5_client.py#L241-L258)
* **Análisis del Problema:**
  `get_rates(ticker, timeframe, n)` en MetaTrader 5 incluye como último registro la vela abierta en curso. Si el script corre al inicio de una hora (ej. 10:05 CLT), la vela posee un rango incompleto y un cierre fluctuante.
* **Impacto Operativo:**
  1. En el Canal Donchian (`rolling(50).max()`), si la vela actual marca un nuevo máximo por 1 tick, el canal absorbe el precio inmediatamente y la condición de quiebre (`precio > donchian_high`) se neutraliza a sí misma.
  2. En el ATR, una vela abierta de pocos minutos con rango estrecho deprime la media exponencial.
* **Propuesta de Corrección:**
  Calcular indicadores técnicos exclusivamente sobre velas cerradas (`df.iloc[:-1]`) y evaluar el precio spot en tiempo real contra los niveles congelados de la última vela cerrada.

---

#### Hallazgo 6: Supuesto de Espacio Continuo frente a Concentración Discreta de Liquidez

* **Análisis del Problema:**
  El modelo suma de forma lineal el impulso al precio actual ($P + \text{Impulso}$) sin verificar la presencia de zonas de absorción institucional o barreras de volatilidad (Banda Superior de Bollinger o $R_1$).
* **Impacto Operativo:**
  Proyecta metas que traspasan resistencias estructurales sin considerar si el volumen negociado promedio en el activo es suficiente para absorber la oferta pasiva en el libro de órdenes.

---

### 3. Preguntas Específicas para el Auditor Cuantitativo Externo

1. **Tratamiento de Series Temporales Discontinuas:**  
   ¿Cuál es la mejor práctica recomendada para el cálculo de ATR en instrumentos con sesiones diarias acotadas (como USD/CLP) para evitar el sesgo de dilución nocturna sin introducir discontinuidades por gaps de apertura?
2. **Calibración del Multiplicador:**  
   ¿Es metodológicamente preferible modular el multiplicador de impulso mediante una función continua del ADX/RSI o mantener multiplicadores discretos condicionados por el régimen macro global ($R_0$ a $R_4$)?
3. **Normalización del Gate de Consumo:**  
   ¿Qué función de distribución horaria de volatilidad (ej. Curva intradía en U / Volatility Smile) recomiendan para ajustar el validador de consumo diario durante las primeras dos horas de negociación?

---

*Fin del Documento de Solicitud de Auditoría.*
