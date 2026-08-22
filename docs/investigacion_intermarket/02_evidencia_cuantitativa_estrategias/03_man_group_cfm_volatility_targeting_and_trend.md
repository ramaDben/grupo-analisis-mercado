# Ficha Técnica: Volatility Targeting, Trend Following y Crisis Alpha
**Instituciones y Autores Clave**: Man Group (AHL), Capital Fund Management (CFM), AQR Capital Management, Campbell R. Harvey (Duke University).

**Referencias Académicas Principales**:
1. **Harvey, Campbell R.; Hoyle, Edward; Korgaonkar, Russell; Rattray, Sandy; Sargaison, Matthew; Van Hemert, Otto** (2018). *The Impact of Volatility Targeting*. The Journal of Portfolio Management, 45(1), 14–33.
2. **Lempérière, Yves; Deremble, Cyril; Seager, Philip; Potters, Marc; Bouchaud, Jean-Philippe** (2014). *Two Centuries of Trend Following*. Journal of Investment Strategies, 3(3), 41–61.
3. **Hamill, Carl; Rattray, Sandy; Van Hemert, Otto** (2016). *Trend Following: Equity and Bond Crisis Alpha*. Man AHL / SSRN Working Paper.
4. **Neville, Henry; Draaisma, Teun; Funnell, Ben; Harvey, Campbell R.; Van Hemert, Otto** (2021). *The Best Strategies for Inflationary Times*. The Journal of Portfolio Management, 47(8), 8–37.
5. **Hurst, Brian; Ooi, Yao Hua; Pedersen, Lasse Heje** (2017). *A Century of Evidence on Trend-Following Investing*. The Journal of Portfolio Management, 44(1), 15–29.
6. **Carver, Robert** (2015). *Systematic Trading: A unique new method for designing trading and investing systems*. Harriman House.

---

## 1. Tesis Fundamental y Marco Institucional

Las firmas de gestión cuantitativa sistemática más exitosas del mundo (Man AHL con más de 35 años de track record, CFM y AQR) fundamentan sus arquitecturas de inversión en dos motores complementarios:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   ARQUITECTURA CUANTITATIVA SISTEMÁTICA                  │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│     MOTOR 1: SEÑAL DIRECCIONAL   │   │   MOTOR 2: VOLATILITY TARGETING  │
│   (Trend Following Multiescala)  │   │     (Gestión de Riesgo Ex-Ante)  │
│                                  │   │                                  │
│  - Captura drift y sesgos de     │   │  - Normaliza riesgo por activo   │
│    sub-reacción conductual.      │   │  - Explota el "Leverage Effect"  │
│  - Lookbacks combinados          │   │  - Escalamiento inverso:         │
│    (rápido, medio, lento).       │   │    $w_t \propto 1 / \sigma_t$    │
└─────────────────┬────────────────┘   └─────────────────┬────────────────┘
                  │                                      │
                  └──────────────────┬───────────────────┘
                                     ▼
                     ┌────────────────────────────────┐
                     │   POSICIÓN FINAL PONDERADA     │
                     │  - Convexidad Positiva         │
                     │  - Crisis Alpha en Shocks      │
                     │  - Máximo Ratio de Sharpe      │
                     └────────────────────────────────┘
```

1. **La Señal Direccional (*Trend Following / Time Series Momentum*)**:
   * Explota los sesgos de comportamiento de los participantes institucionales (anclaje, disposición, efecto manada y restricciones regulatorias/mandatos lentos), generando retornos con **asimetría positiva (*positive skewness*)**.
2. **El Dimensionamiento de Posición (*Volatility Targeting*)**:
   * Desvincula el tamaño nocional fijo y ajusta la exposición en función inversa a la volatilidad reciente del activo.
   * Explota el fenómeno de *agrupamiento de volatilidad* (*volatility clustering*, Mandelbrot / Engle) y el *efecto apalancamiento* (*leverage effect*), evitando que los activos más volátiles dominen el riesgo del portafolio o que los picos de volatilidad destruyan el capital.

---

## 2. Formalización Matemática del Volatility Targeting

### A. Ecuaciones del Modelo (Harvey et al., 2018)

Sea $P_t$ el precio de un activo en el tiempo $t$ y $r_t = \frac{P_t - P_{t-1}}{P_{t-1}}$ su retorno simple. 

1. **Estimación de la Volatilidad Realizada ($\hat{\sigma}_t$)**:
   Se modela habitualmente mediante un estimador exponencial ponderado por tiempo (EWMA) o desviación estándar de ventana móvil ($N$ días):
   $$\hat{\sigma}_{t}^2 = \lambda \hat{\sigma}_{t-1}^2 + (1-\lambda) r_t^2$$
   Donde $\lambda \in [0.90, 0.96]$ (estándar RiskMetrics: $\lambda = 0.94$, correspondiente a un período efectivo de vida media $\approx 32$ días).

2. **Cálculo del Ponderador de Escalamiento ($w_t$)**:
   Dado un objetivo de volatilidad anualizado $\sigma_{\text{target}}$ (ej. 10%, 15% o 40% en carteras estandarizadas):
   $$w_t = \frac{\sigma_{\text{target}}}{\hat{\sigma}_t \cdot \sqrt{252}}$$
   * Si la volatilidad realizada $\hat{\sigma}_t \cdot \sqrt{252} > \sigma_{\text{target}}$: El sistema desapalanca ($w_t < 1$), reduciendo drásticamente la exposición previa a caídas violentas.
   * Si la volatilidad realizada $\hat{\sigma}_t \cdot \sqrt{252} < \sigma_{\text{target}}$: El sistema incrementa la exposición ($w_t > 1$), aprovechando regímenes tranquilos de baja volatilidad (*Goldilocks*).

3. **Retorno de la Estrategia con Volatility Target ($r_t^{\text{VT}}$)**:
   $$r_t^{\text{VT}} = w_{t-1} \cdot r_t = \frac{\sigma_{\text{target}}}{\hat{\sigma}_{t-1} \cdot \sqrt{252}} \cdot r_t$$

### B. Impacto Matemático en el Ratio de Sharpe y Colapsos

Harvey et al. (2018) analizaron más de 60 activos desde 1926 hasta 2017 y probaron empíricamente que:

1. **Aumento Significativo del Sharpe en Activos de Riesgo**:
   * En renta variable e índices de crédito, el *Volatility Targeting* incrementa el Ratio de Sharpe en un **+25% a +40%** gracias a la correlación negativa entre retornos y cambios en volatilidad ($\text{Corr}(r_t, \Delta \sigma_t) < 0$).
2. **Eliminación de Colas Negativas Pesadas (*Trimming Fat Left-Tails*)**:
   * La curtosis del portafolio se reduce a la mitad (pasando de distribuciones leptocúrticas con colas grasas $\kappa > 8$ a distribuciones controladas $\kappa \approx 3.5 - 4.5$).
3. **Contracción del Maximum Drawdown (MDD)**:
   * En el S&P 500 y carteras 60/40, la máxima caída histórica se reduce de niveles del **-55%** a niveles del **-30% / -35%**, acortando a más de la mitad el tiempo requerido para recuperar máximos históricos (*drawdown duration*).

| Métrica Cuantitativa | S&P 500 Sin VT (Buy & Hold) | S&P 500 Con Volatility Target (10%) | Cartera 60/40 Sin VT | Cartera 60/40 Con Volatility Target (10%) |
| :--- | :---: | :---: | :---: | :---: |
| **Sharpe Ratio (1926-2017)** | 0.38 | **0.58 (+52%)** | 0.52 | **0.71 (+36%)** |
| **Volatilidad Anualizada** | 18.7% | **10.1% (Estable)** | 10.8% | **9.9% (Estable)** |
| **Máximo Drawdown (MDD)** | -84.5% (1929) / -50.9% (2008) | **-42.3% (1929) / -31.4% (2008)** | -53.9% (1932) / -32.5% (2008) | **-26.8% (1932) / -18.2% (2008)** |
| **Curtosis (Kurtosis $\kappa$)** | 10.4 (Colas extremas) | **4.2 (Distribución moderada)** | 8.9 | **3.8** |
| **Asimetría (Skewness $S$)** | -0.45 (Sesgo bajista) | **-0.05 (Simetría neutra/positiva)** | -0.38 | **+0.02** |

---

## 3. Parámetros Cuantitativos Probados (CFM, Man AHL, AQR)

### A. Lookback Windows y Descomposición Multi-Horizonte

La literatura de CFM (Lempérière et al., 2014) y Man AHL (Carver, 2015; Hamill et al., 2016) demuestra que optimizar un único lookback (ej. solo MA 200) genera sobreajuste (*overfitting*) y vulnerabilidad ante cambios de ciclo. La estructura estándar de un CTA institucional combina tres escalas temporales:

```
                  DESCOMPOSICIÓN TEMPORAL INSTITUCIONAL
                  
    Horizonte Rápido (Fast)      Horizonte Medio (Medium)      Horizonte Lento (Slow)
    Lookback: 10 - 40 días       Lookback: 40 - 120 días       Lookback: 120 - 300 días
    (2 a 8 semanas)              (8 a 24 semanas)              (24 a 60 semanas)
    Ponderación: 33.3%           Ponderación: 33.3%            Ponderación: 33.3%
    ┌────────────────────┐       ┌────────────────────┐        ┌────────────────────┐
    │ Giro temprano      │       │ Núcleo de tendencia│        │ Inercia macro      │
    │ y salida ágil      │  ──►  │ y persistencia     │  ──►   │ y protección broad │
    │ de shocks          │       │ intermedia         │        │ cycle              │
    └────────────────────┘       └────────────────────┘        └────────────────────┘
```

### B. Calibración de Medias Móviles Exponenciales (EWMAC - Robert Carver / AHL)

El modelo de cruce de medias ponderadas exponencialmente (EWMAC - *Exponential Weighted Moving Average Crossover*) compara una media rápida $\text{EMA}_{\text{fast}}$ con una media lenta $\text{EMA}_{\text{slow}}$.

El factor de suavizado $\alpha$ para una ventana de $N$ días se define como:
$$\alpha = \frac{2}{N+1} \quad \text{o} \quad \alpha = 1 - \exp\left(-\frac{1}{\tau}\right)$$

#### Pares EWMAC Óptimos y Factores de Escalamiento (*Forecast Scalars*):
Para que las señales de distintos horizontes tengan el mismo impacto esperado, Robert Carver define el pronóstico estandarizado $f_t$:

$$f_t = \text{clip}\left( \frac{\text{EMA}_{\text{fast}, t} - \text{EMA}_{\text{slow}, t}}{\text{ATR}_{20, t} \text{ o } \hat{\sigma}_{t}} \times \text{Scalar}, -20, +20 \right)$$

| Par EWMAC $(\tau_{\text{fast}}, \tau_{\text{slow}})$ | Horizonte | Lookback Efectivo | Forecast Scalar Teórico | Sharpe Ratio Aislado (Futures Multi-Asset) |
| :---: | :---: | :---: | :---: | :---: |
| **(2, 8)** | Ultra-Rápido | ~4 a 16 días | 10.6 | 0.28 |
| **(4, 16)** | Rápido | ~8 a 32 días | 7.5 | 0.38 |
| **(8, 32)** | Medio-Corto | ~16 a 64 días | 5.3 | 0.49 |
| **(16, 64)** | Medio | ~32 a 128 días | 3.75 | **0.56** |
| **(32, 128)** | Lento | ~64 a 256 días | 2.65 | **0.58** |
| **(64, 256)** | Macro-Lento | ~128 a 512 días | 1.87 | 0.52 |
| **Combinación Lineal de Todos** | **Multiescala** | **Completo** | **Ponderado** | **0.78 - 0.95** |

*Nota: CFM (Lempérière et al., 2014) introduce adicionalmente la función de saturación no lineal $S(x) = \tanh(x / x_0)$ para atenuar señales hiperbólicas en burbujas parabólicas.*

### C. Multiplicadores de ATR para Stop Loss y Reglas de Salida

En la literatura de Managed Futures y CTAs (Kaminski 2014, Carver 2015, Baltas 2015), existe un consenso crítico sobre los límites de pérdida y toma de beneficios:

1. **Stop Loss Volátil Dinámico**:
   * Se calibra estrictamente en función del ATR ($\text{ATR}_{14}$ o $\text{ATR}_{20}$):
     $$\text{Distancia Stop Loss} = k_{\text{SL}} \times \text{ATR}_t$$
   * **Multiplicador Swing Intradía/Táctico (1H / 4H)**: $k_{\text{SL}} = 1.50 \text{ a } 2.00$.
   * **Multiplicador Swing Macro (Diario / Semanal)**: $k_{\text{SL}} = 2.50 \text{ a } 3.00$.
2. **Prohibición de Take Profit Fijo en Trend Following**:
   * Establecer un *Take Profit* fijo (ej. 2R o 3R estático) trunca la cola derecha de la distribución de retornos, **destruyendo la asimetría positiva (*positive skewness*)** que es la fuente matemática del retorno a largo plazo.
   * La salida óptima documentada por Man AHL y CFM se ejecuta mediante:
     * **Inversión de la Señal EWMAC**: Reducción gradual a medida que el fast EMA converge con el slow EMA.
     * **Chandelier Exit / ATR Trailing Stop**: $\text{Stop Dinámico} = \max_{s \in [t-n, t]} (P_s) - 3.0 \times \text{ATR}_t$.

---

## 4. Asimetría de Retornos (*Crisis Alpha* y *Positive Skewness*)

### A. Perfil de Payoff Convexo (Hamill, Rattray & Van Hemert, 2016)

Hamill et al. demostraron que el Trend Following multi-activo exhibe un perfil de retorno equivalente a una **posición sintética larga en opciones Straddle (*Long Straddle / Long Gamma*)**:

```
                       PERFIL DE PAYOFF: TREND FOLLOWING
                       
       Retorno CTA
           ▲
           │          /                          \
           │         /                            \
           │        /                              \
           │       /                                \
           │      /                                  \
           │     /                                    \
   ────────┼────/──────────────────────────────────────\────────► Retorno del Mercado
           │   /                                        \         (Acciones / Bonos)
           │  /                                          \
           │ ┌────────────────────────────────────────────┐
           │ │ Pérdida limitada por cortes de volatilidad │
           │ └────────────────────────────────────────────┘
           ▼
               Mercado Colapsa               Mercado Dispara
               (Crash / Bear)                 (Bull Market)
```

* Durante períodos de caídas lentas o moderadas, el CTA puede sufrir pequeñas pérdidas por *whipsaws* (el "costo de prima" de la opción).
* Durante caídas severas y prolongadas (GFC 2008, Dot-Com 2000-2002, 2022), el sistema acumula posiciones cortas en activos perdedores y largas en materias primas / dólar, generando rendimientos explosivos descorrelacionados (*Crisis Alpha*).

### B. Rendimiento en Shocks Inflacionarios (Neville, Harvey et al., 2021)

Neville, Draaisma, Funnell, Harvey y Van Hemert (2021) analizaron casi un siglo de datos históricos (1925-2020) a través de los **8 mayores regímenes inflacionarios en EE.UU., Reino Unido y Japón**:

| Clase de Activo / Estrategia | Retorno Real Anualizado en Shocks Inflacionarios | Retorno Nominal Anualizado | Tasa de Acierto (% Regímenes Positivos) |
| :--- | :---: | :---: | :---: |
| **Cartera Tradicional 60/40** | **-5.3%** | +3.1% | 12% (1 de 8) |
| **Renta Variable EE.UU. (S&P 500)** | **-7.0%** | +1.4% | 25% (2 de 8) |
| **Bonos del Tesoro EE.UU. (10Y)** | **-5.0%** | +3.4% | 12% (1 de 8) |
| **Canasta de Commodities (Equal-Weight)** | **+14.0%** | **+22.4%** | **88% (7 de 8)** |
| — *Petróleo WTI / Energía* | **+41.0%** | **+49.4%** | **100% (8 de 8)** |
| — *Oro (XAUUSD)* | **+13.0%** | **+21.4%** | **75% (6 de 8)** |
| — *Cobre COMEX* | **+11.0%** | **+19.4%** | **75% (6 de 8)** |
| **Trend Following Multi-Activo (CTA)** | **+25.0%** | **+33.4%** | **100% (8 de 8)** |

> **Conclusión del estudio de Neville & Harvey**:
> *El Trend Following multi-activo y las Commodities físicas son las dos únicas estrategias que registraron retornos reales fuertemente positivos en todos los episodios de aceleración inflacionaria de los últimos 100 años.*

---

## 5. Matriz Resumen de Parámetros Empíricos Institucionales

| Parámetro / Componente | Dimensión Recomendada | Rango Operativo Aceptable | Justificación Cuantitativa |
| :--- | :--- | :--- | :--- |
| **Target de Volatilidad ($\sigma_{\text{target}}$)** | **10% - 15% anual** | 8% - 20% | Maximiza el ratio de Sharpe sin incurrir en costos excesivos de endeudamiento o margen. |
| **Estimador de Volatilidad** | **EWMA $\lambda = 0.94$ o 20D ATR** | $N = 20 \text{ a } 60$ días | Captura el agrupamiento de volatilidad (*clustering*) sin exceso de ruido de alta frecuencia. |
| **Lookback de Tendencia Rápido** | **EMA 16 / MA 20** (~3-4 semanas) | 10 a 30 días | Respuesta rápida ante cambios de régimen y giros de política monetaria. |
| **Lookback de Tendencia Medio** | **EMA 50 / MA 60** (~2-3 meses) | 40 a 90 días | Captura el ciclo intermedio de momentum en commodities y divisas. |
| **Lookback de Tendencia Lento** | **EMA 200 / MA 250** (~10-12 meses) | 150 a 300 días | Filtro macro estructural; máxima solidez estadística a través de 200 años (CFM). |
| **Stop Loss Multiplier ($k_{\text{SL}}$)** | **$1.5 \times \text{ATR}_{14}$ (1H) / $2.5 \times \text{ATR}_{20}$ (1D)**| $1.5 \times \text{ a } 3.0 \times \text{ATR}$ | Mantiene el riesgo por operación idéntico en términos de dólares independientemente del régimen de volatilidad. |
| **Take Profit Multiplier** | **Sin TP estático (Trailing Exit)** | $k_{\text{trail}} = 3.0 \times \text{ATR}$ | Garantiza asimetría positiva (*positive skewness*) permitiendo la captura de eventos de cola derecha. |
| **Límite Máximo de Apalancamiento** | **$w_{\max} = 3.0\times$** | $2.0\times \text{ a } 4.0\times$ | Evita sobreapalancamiento catastrófico durante períodos de volatilidad extremadamente comprimida. |

---

## 6. Reglas Operativas Directas para el Trading Desk

### Regla 1: Dimensionamiento de Posición Cuantitativo por Volatilidad
Para cualquier operación en MT5 (`USDCLP`, `XAUUSD`, `WTI`, `US100`), el tamaño del lote $L$ se calcula obligatoriamente mediante la fórmula de volatilidad monetaria:

$$L = \frac{\text{Capital de la Cuenta} \times \text{Riesgo Máximo por Operación (\%)}}{\text{Distancia del Stop Loss en Puntos} \times \text{Valor del Punto por Lote}}$$

Donde la $\text{Distancia del Stop Loss} = k_{\text{SL}} \times \text{ATR}_t$.
* Si la volatilidad del Cobre o del Oro se duplica ($\text{ATR}$ se duplica), el lote $L$ **se reduce automáticamente a la mitad**.
* Queda estrictamente prohibido usar un número fijo de lotes para distintas condiciones de mercado.

### Regla 2: Confluencia Multi-Horizonte (Elder - Carver AHL)
* **Filtro Macro (Gráfico Diario / 4H)**: El precio debe estar sobre la EMA 50 y la EMA 200 para compras (o bajo ambas para ventas).
* **Filtro de Momentum Táctico (Gráfico 1H)**: La EMA 16 debe tener pendiente positiva para compras (o negativa para ventas).
* **Gatillo de Entrada (Gráfico 15M)**: Rompimiento de rango o retroceso completado hacia el VWAP/EMA 16 con vela de confirmación.

### Regla 3: Salidas Asimétricas (Dejar Correr Ganancias)
* No colocar órdenes de Take Profit fijas en operaciones de tendencia respaldadas por datos macroeconómicos en `data central/`.
* Mover el Stop Loss a Breakeven una vez que el trade avance $+1.5 \times \text{ATR}$.
* Ejecutar la salida definitiva únicamente cuando el precio cierre al otro lado de la EMA 16 en 1H o por perforación del Trailing Stop a $3.0 \times \text{ATR}$.

### Regla 4: Conducción en Regímenes Inflacionarios y de Shock
* Durante shocks inflacionarios (verificados con IPC/PPI al alza y subida en tasas del Tesoro en `data central/`), priorizar con el 100% del apetito de riesgo el **Trend-Following en Commodities (Petróleo, Oro, Cobre)** y **Posiciones Largas en USD/CLP**, prohibiendo las compras de rebote contratendencia en índices tecnológicos de alta duración (`US100`).
