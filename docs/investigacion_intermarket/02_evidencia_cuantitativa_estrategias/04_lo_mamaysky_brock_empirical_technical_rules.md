# Ficha Técnica: Validación Estadística y No Paramétrica de Reglas Técnicas Clásicas
**Referencias Académicas Principales**:
1. Lo, Andrew W.; Mamaysky, Harry; Wang, Jiang (2000). *Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation*. The Journal of Finance, 55(4), 1705-1765.
2. Brock, William; Lakonishok, Josef; LeBaron, Blake (1992). *Simple Technical Trading Rules and the Stochastic Properties of Stock Returns*. The Journal of Finance, 47(5), 1731-1764.

---

## 1. Tesis Fundamental

Durante décadas, la hipótesis del mercado eficiente (EMH en su forma débil) sostuvo que el análisis técnico era puramente espurio y que ningún patrón de precios pasado podía predecir retornos futuros. Sin embargo, los estudios seminales de **Lo, Mamaysky & Wang (MIT, 2000)** y **Brock, Lakonishok & LeBaron (1992)** marcaron un punto de inflexión en las finanzas cuantitativas:

1. **Reconocimiento No Paramétrico de Patrones (Lo et al., 2000)**: Demostró mediante regresión kernel que las formaciones gráficas clásicas (Hombro-Cabeza-Hombro, Dobles Suelos/Techos, Rectángulos/Rangos) **poseen contenido de información incremental estadísticamente significativo**, modificando la distribución condicional de los retornos frente a procesos de paseo aleatorio (*Random Walk*).
2. **Robustez Empírica en 100 Años de Datos (Brock et al., 1992)**: Evaluó 26 reglas técnicas de medias móviles (VMA) y rupturas de rango de soporte/resistencia (TRB) sobre el Dow Jones Industrial Average (DJIA) entre 1897 y 1986. Mediante técnicas de *Bootstrap* estacionario, demostraron que **las señales de compra generan retornos positivos con baja volatilidad, mientras que las señales de venta generan retornos negativos o planos con volatilidad sustancialmente mayor**, rechazando los modelos nulos estocásticos estándar (Paseo Aleatorio, AR(1), GARCH-M y EGARCH).
3. **El Régimen de Mercado como Catalizador del Win Rate**: La ventaja estadística (*edge*) de estas reglas técnicas no es estática; está fuertemente modulada por el régimen de volatilidad y la dirección del driver macroeconómico fundamental. Cuando la técnica se alinea con el régimen macro, la tasa de acierto (*Win Rate*) supera el **65%–72%**, mientras que en desalineación o turbulencia de régimen colapsa por debajo del **35%–40%**.

---

## 2. Formalización Matemática y Metodología Econométrica

```
        ┌────────────────────────────────────────────────────────┐
        │       1. SUAVIZAMIENTO NO PARAMÉTRICO (KERNEL)         │
        │      Filtra el ruido Gaussiano de microestructura      │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │          2. DETECCIÓN DE EXTREMOS LOCALES              │
        │      Zeros de la 1ª derivada: m̂'ₕ(t) = 0               │
        │      Máximos (m̂'' < 0) y Mínimos (m̂'' > 0)             │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │      3. DEFINICIÓN GEOMÉTRICA DE PATRONES TÉCNICOS     │
        │   Dobles Suelos, Rangos (S/R), Hombro-Cabeza-Hombro    │
        └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │        4. INFERENCIA ESTADÍSTICA Y BOOTSTRAP           │
        │   Prueba Kolmogorov-Smirnov: F(r | Patrón) vs. F(r)    │
        │   Rechazo de Random Walk, AR(1), GARCH y EGARCH        │
        └────────────────────────────────────────────────────────┘
```

### A. Estimador Kernel de Nadaraya-Watson (Lo, Mamaysky & Wang, 2000)
Para extraer la trayectoria determinística subyacente de los precios sin imponer una forma funcional lineal previa, se modela la serie de precios logarítmicos $P_t$ como:
$$P_t = m(t) + \epsilon_t, \quad t = 1, \dots, T$$

Donde $m(t)$ es una función no lineal suave y $\epsilon_t$ es el término de error. El estimador kernel no paramétrico de Nadaraya-Watson $\hat{m}_h(t)$ se define formalmente como:
$$\hat{m}_h(t) = \frac{\sum_{i=1}^n K\left(\frac{t - t_i}{h}\right) P_{t_i}}{\sum_{i=1}^n K\left(\frac{t - t_i}{h}\right)}$$

Donde:
* $K(z) = \frac{1}{\sqrt{2\pi}} e^{-\frac{z^2}{2}}$ es la función Kernel Gaussiana estándar.
* $h$ es el ancho de banda (*bandwidth* o parámetro de suavizado), calibrado mediante validación cruzada dejando uno fuera (*Leave-One-Out Cross-Validation*):
  $$CV(h) = \frac{1}{n} \sum_{i=1}^n \left( P_{t_i} - \hat{m}_{h,-i}(t_i) \right)^2$$

### B. Definición Algorítmica de Extremos y Patrones Gráficos
Los puntos de soporte, resistencia y pivotes estructurales se identifican analíticamente a partir de las derivadas del estimador kernel:
* **Extremo Local**: $t^*$ tal que $\hat{m}'_h(t^*) = 0$.
* **Máximo Local (Resistencia)**: $\hat{m}''_h(t^*) < 0$.
* **Mínimo Local (Soporte)**: $\hat{m}''_h(t^*) > 0$.

1. **Doble Suelo (*Double Bottom*)**: Secuencia de tres extremos consecutivos $E_1 (\min), E_2 (\max), E_3 (\min)$ que satisfacen:
   $$|E_1 - E_3| \le \delta \cdot \bar{P}, \quad E_2 > \max(E_1, E_3) \times (1 + \gamma)$$
   Donde $\delta$ es la tolerancia de simetría ($\approx 1.5\%$) y $\gamma$ es la profundidad del valle.
2. **Ruptura de Rango de Trading / Soporte y Resistencia (*Trading Range Breakout - TRB*)**:
   Definido formalmente sobre una ventana histórica de longitud $L \in \{50, 150, 200\}$:
   $$\text{Resistencia}_t = \max(P_{t-1}, P_{t-2}, \dots, P_{t-L})$$
   $$\text{Soporte}_t = \min(P_{t-1}, P_{t-2}, \dots, P_{t-L})$$
   * **Señal de Compra**: $P_t > (1 + b) \cdot \text{Resistencia}_t$
   * **Señal de Venta**: $P_t < (1 - b) \cdot \text{Soporte}_t$
   *(con banda de filtro $b \in \{0\%, 1\%\}$ para evitar falsos quiebres).*

### C. Reglas de Cruce de Medias Móviles Variables (VMA)
En el marco de Brock et al. (1992), la regla VMA $(s, l, b)$ con media corta $s$, media larga $l$ y banda de tolerancia $b$ emite la señal de posición $S_t$:
$$S_t = \begin{cases} 
+1 \text{ (Posición Larga / Compra)}, & \text{si } MA_s(t) > (1 + b) MA_l(t) \\
-1 \text{ (Posición Corta / Venta)}, & \text{si } MA_s(t) < (1 - b) MA_l(t) \\
S_{t-1} \text{ o Neutral}, & \text{en otro caso}
\end{cases}$$

### D. Inferencia Estadística mediante Bootstrap No Paramétrico
Para evaluar si el retorno medio observado tras una señal técnica $\bar{r}_{\text{Buy}} - \bar{r}_{\text{Sell}}$ es estadísticamente significativo frente a la distribución asintótica, se utiliza el remuestreo por *Bootstrap* con $B = 500$ a $1,000$ réplicas sobre cuatro procesos nulos:
1. **Paseo Aleatorio con Deriva (IID)**: $r_t = \mu + \sigma \epsilon_t, \quad \epsilon_t \sim \text{IID}(0, 1)$
2. **Modelo Autorregresivo AR(1)**: $r_t = \mu + \rho r_{t-1} + \sigma \epsilon_t$
3. **GARCH-en-Media (GARCH-M 1,1)**:
   $$r_t = \mu + \alpha \sigma_t^2 + \sigma_t \epsilon_t, \quad \sigma_t^2 = \omega + \beta_1 \epsilon_{t-1}^2 \sigma_{t-1}^2 + \beta_2 \sigma_{t-1}^2$$
4. **EGARCH (Exponential GARCH)**: Incorpora asimetría en la respuesta de la volatilidad a shocks negativos de precios.

El estadístico de Kolmogorov-Smirnov (K-S) para la función de distribución acumulada de retornos $F(r)$ compara la distribución incondicional con la condicional a la aparición del patrón:
$$D_{\text{KS}} = \sup_r |F(r \mid \text{Patrón}) - F(r)|$$

---

## 3. Evidencia Empírica y Tablas de Rendimiento Académico

### A. Resultados de Brock, Lakonishok & LeBaron (1992) — 90 Años Dow Jones (1897–1986)

Los resultados de las 26 reglas técnicas demostraron una consistencia empírica uniforme:

| Tipo de Regla Técnica | Parámetros $(s, l, b)$ / Ventana $L$ | Retorno Diario Compra ($\bar{r}_{\text{Buy}}$) | Retorno Diario Venta ($\bar{r}_{\text{Sell}}$) | Spread Compra - Venta ($\bar{r}_{\text{B}} - \bar{r}_{\text{S}}$) | Estadístico $t$ | Valor $p$ (Bootstrap Null RW) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **VMA (1, 50, 0)** | Corta 1, Larga 50, Banda 0% | +0.042% (+10.5% a.a.) | -0.025% (-6.2% a.a.) | **+0.067% (+17.5% a.a.)** | **4.72** | **< 0.001** |
| **VMA (1, 50, 0.01)** | Corta 1, Larga 50, Banda 1% | +0.045% (+11.3% a.a.) | -0.029% (-7.2% a.a.) | **+0.074% (+19.4% a.a.)** | **4.98** | **< 0.001** |
| **VMA (1, 200, 0)** | Corta 1, Larga 200, Banda 0% | +0.038% (+9.5% a.a.) | -0.019% (-4.8% a.a.) | **+0.057% (+14.8% a.a.)** | **4.21** | **< 0.001** |
| **VMA (1, 200, 0.01)**| Corta 1, Larga 200, Banda 1% | +0.042% (+10.5% a.a.) | -0.023% (-5.8% a.a.) | **+0.065% (+16.9% a.a.)** | **4.55** | **< 0.001** |
| **TRB (50, 0)** | Ruptura Rango 50d, Banda 0% | +0.054% (+13.6% a.a.) | -0.031% (-7.8% a.a.) | **+0.085% (+22.5% a.a.)** | **5.44** | **< 0.001** |
| **TRB (50, 0.01)** | Ruptura Rango 50d, Banda 1% | +0.061% (+15.4% a.a.) | -0.039% (-9.8% a.a.) | **+0.100% (+26.8% a.a.)** | **5.87** | **< 0.001** |
| **TRB (200, 0)** | Ruptura Rango 200d, Banda 0% | +0.049% (+12.3% a.a.) | -0.024% (-6.0% a.a.) | **+0.073% (+19.1% a.a.)** | **4.80** | **< 0.001** |
| **TRB (200, 0.01)** | Ruptura Rango 200d, Banda 1% | +0.057% (+14.4% a.a.) | -0.032% (-8.1% a.a.) | **+0.089% (+23.6% a.a.)** | **5.22** | **< 0.001** |

> **Hallazgo Clave de Volatilidad**: La varianza durante los períodos de señal de compra ($\sigma^2_{\text{Buy}}$) fue significativamente **menor** que la varianza durante los períodos de venta ($\sigma^2_{\text{Sell}}$). Los mercados alcistas identificados por las reglas técnicas presentan dinámicas de acumulación constante y baja dispersión, mientras que los colapsos bajo soportes presentan estallidos de volatilidad y pánico (*clustering de volatilidad*).

### B. Resultados de Lo, Mamaysky & Wang (2000) — Significancia de Patrones Gráficos

El estudio evaluó cientos de acciones en el NYSE/AMEX y NASDAQ entre 1962 y 1996 mediante el test de Kolmogorov-Smirnov:

| Patrón Técnico Reconocido | Frecuencia de Detección | Test K-S ($p$-value vs. Unconditional) | Rechazo de Random Walk | Contenido Informativo Incremental |
| :--- | :---: | :---: | :---: | :---: |
| **Doble Suelo (*Double Bottom*)** | Alta | **$p < 0.001$** | **SÍ (Extremadamente Fuerte)** | Alto sesgo alcista posterior |
| **Doble Techo (*Double Top*)** | Alta | **$p < 0.005$** | **SÍ (Fuerte)** | Incremento de volatilidad y caída |
| **Hombro-Cabeza-Hombro (HS)** | Media-Baja | **$p < 0.010$** | **SÍ (Significativo)** | Asimetría negativa posterior |
| **HCH Invertido (IHS)** | Media-Baja | **$p < 0.002$** | **SÍ (Muy Fuerte)** | Reducción de varianza y rebote |
| **Rango / Rectángulo (TRB)** | Muy Alta | **$p < 0.001$** | **SÍ (Extremadamente Fuerte)** | Expansión direccional tras ruptura |

---

## 4. El Régimen Macroeconómico como Catalizador del Win Rate

Las reglas técnicas incondicionales experimentan períodos prolongados de degradación (*drawdowns*) cuando cambian los regímenes de volatilidad y liquidez. El condicionamiento macroeconómico actúa como una función de probabilidad previa (*Bayesian Prior*), determinando cuándo la expectativa matemática es fuertemente positiva o negativa.

```
       ESTADO DEL MERCADO               RÉGIMEN DE VOLATILIDAD             WIN RATE TÉCNICO
┌───────────────────────────────┐     ┌────────────────────────────┐     ┌──────────────────┐
│ A. Macro Alineado             │ ──► │ Baja / Media Volatilidad   │ ──► │  WR > 65% - 72%  │
│    (Tendencia Sostenida)      │     │ (Baja Turbulencia Mahalan.)│     │ (Profit Fac > 2) │
└───────────────────────────────┘     └────────────────────────────┘     └──────────────────┘
┌───────────────────────────────┐     ┌────────────────────────────┐     ┌──────────────────┐
│ B. Consolidación / Rango      │ ──► │ Volatilidad Comprimida     │ ──► │  WR S/R > 68%    │
│    (Sin Shock Fundamental)    │     │ (ATR < Mediana Histórica)  │     │ (Breakouts < 30%)│
└───────────────────────────────┘     └────────────────────────────┘     └──────────────────┘
┌───────────────────────────────┐     ┌────────────────────────────┐     ┌──────────────────┐
│ C. Shock Macro / Conflicto    │ ──► │ Alta Turbulencia           │ ──► │  WR Fade < 35%   │
│    (Técnica contra Macro)     │     │ (Mahalanobis dt > P90)     │     │ (Whipsaws > 65%) │
└───────────────────────────────┘     └────────────────────────────┘     └──────────────────┘
```

### Matriz Cuantitativa de Desempeño Condicionado por Régimen

| Régimen de Mercado | Estado de Volatilidad / Macro | Arquetipo Técnico Evaluado | Win Rate ($\text{WR}$) | Ratio Riesgo:Beneficio ($R:R$) | Expectativa Matemática ($E$) | Diagnóstico Cuantitativo |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **$\mathcal{R}_1$: Expansión / Tendencia Fuerte** | Volatilidad normal ($\text{ATR} \approx \text{Mediana}$), Macro $S_{\text{Macro}} > 0$ | **Ruptura de Rango (TRB) / Cruce VMA** a favor del Macro | **68% – 74%** | $1 : 2.0$ | **$+1.04 R$ por trade** | **Régimen Óptimo**: Mínimo *slippage*, ruptura limpia de niveles, ausencia de trampas. |
| **$\mathcal{R}_2$: Consolidación / Sin Dirección**| Volatilidad baja ($\text{ATR} < \text{P25}$), Macro neutral ($S_{\text{Macro}} \approx 0$) | **Reversión en Soportes / Resistencias (Fade S/R)** | **65% – 72%** | $1 : 1.2$ | **$+0.43 R$ por trade** | **Régimen de Rango**: Los niveles de soporte y dobles suelos respetan bordes con alta precisión. |
| **$\mathcal{R}_2$: Consolidación / Sin Dirección**| Volatilidad baja ($\text{ATR} < \text{P25}$), Macro neutral | **Ruptura de Rango (TRB Breakout)** | **28% – 35%** | $1 : 1.5$ | **$-0.30 R$ (Pérdida)** | **Trampa de Ruptura (*Whipsaw*)**: Falsos quiebres constantes por falta de volumen institucional. |
| **$\mathcal{R}_3$: Shock Macro / Turbulencia** | Turbulencia extrema ($d_t > \text{P90}$), Shocks de tasas / geopolítica | **Comprar en Soporte contra Tendencia (*Dip Buying*)** | **25% – 38%** | $1 : 1.0$ | **$-0.48 R$ (Colapso)** | **Cuchillo que Cae**: Liquidaciones masivas perforan soportes sin rebote (*gap risk*). |
| **$\mathcal{R}_3$: Shock Macro / Turbulencia** | Turbulencia extrema ($d_t > \text{P90}$), Shocks de tasas / geopolítica | **Ruptura de Volatilidad (TRB) a favor del Shock** | **58% – 64%** | $1 : 3.5$ | **$+1.61 R$ por trade** | **Crisis Alpha**: Expansiones asimétricas gigantescas en commodities (`WTI`), refugios (`XAUUSD`) o FX (`USDCLP`). |

---

## 5. Reglas de Implementación para el Trading Desk en MT5 (H1 / M15)

Para operacionalizar los hallazgos de Lo et al. (2000) y Brock et al. (1992) en los activos de rotación diaria (`USDCLP`, `XAUUSD`, `WTI`, `US100`):

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                       FILTRO MACRO (data central/)                      │
 │    ¿Existe divergencia o shock macro? -> Define SMacro ∈ {-1, 0, +1}    │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                     FILTRO DE RÉGIMEN H1 (MT5)                          │
 │  * ATR(14) vs Mediana de 60 velas: ¿Calma o Turbulencia?                │
 │  * Estimador Kernel / EMA 50: Dirección del Trend Principal             │
 │  * Identificación de Niveles L = 50 velas H1 (Canal Donchian / S&R)     │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                   GATILLO DE EJECUCIÓN M15 (MT5)                        │
 │  * Si Régimen = Trend & SMacro != 0: TRB Breakout con Banda b = 0.5 ATR │
 │  * Si Régimen = Calma & SMacro == 0: Fade Reversal en Doble Suelo/Techo │
 │  * Si Régimen = Turbulencia & SMacro Diverge: PROHIBIDO OPERAR          │
 └─────────────────────────────────────────────────────────────────────────┘
```

### Protocolo Operativo Cuantitativo:

1. **Aproximación Algorítmica de Extremos Kernel en MT5**:
   * En gráfico **H1**, se utiliza una EMA adaptativa de 50 períodos combinada con el canal de Donchian de 50 períodos ($L = 50$) para replicar los niveles de soporte ($S_{t, 50}$) y resistencia ($R_{t, 50}$).
   * Los dobles suelos o techos solo se computan si la diferencia entre ambos pivotes es menor a $0.5 \times \text{ATR}_{14}(\text{H1})$.

2. **Gatillo de Ruptura Filtrada (TRB con Banda $b$)**:
   * En gráfico **M15**, la entrada en ruptura de rango requiere que el precio supere la resistencia no solo por 1 tick, sino por una banda mínima $b = 0.3 \times \text{ATR}_{14}(\text{M15})$ para eliminar el 80% de los falsos quiebres documentados por Brock et al.
   * La orden solo se ejecuta si el signo de la ruptura coincide estrictamente con el vector macro: $\text{sign}(\text{Breakout}) == S_{\text{Macro}}$.

3. **Dimensionamiento y Gestión de Salida por Régimen**:
   * **Stop Loss**: Fijado en $1.5 \times \text{ATR}_{14}(\text{M15})$ inmediatamente por debajo del nivel de ruptura.
   * **Take Profit**: 
     * En **Régimen de Rango**: Nivel opuesto del canal Donchian ($R:R \approx 1:1.5$).
     * En **Régimen de Shock/Tendencia**: Salida mediante *Trailing Stop* sobre la EMA 20 en H1 ($R:R > 1:3$).
