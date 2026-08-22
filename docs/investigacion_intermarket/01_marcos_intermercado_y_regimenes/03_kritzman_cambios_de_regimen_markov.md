# Ficha Técnica: Cambios de Régimen y Modelos de Transición Estructural (Markov Switching)
**Referencia Académica**: Kritzman, Mark; Page, Sébastien; Turkington, David (2012). *Regime Shifts: Implications for Dynamic Asset Allocation*. Financial Analysts Journal, 68(3), 22-39.

---

## 1. Tesis Fundamental

Las distribuciones de retornos de los activos financieros **no son estacionarias ni gaussianas normales**. Los mercados operan en estados latentes diferenciados (al menos dos: **Régimen de Calma / Baja Volatilidad** y **Régimen de Turbulencia / Alta Volatilidad**).

Durante los cambios de régimen:
1. **Las correlaciones históricas colapsan hacia 1 o -1** (fenómeno de contagio cross-asset).
2. Las estrategias técnicas lineales (como reversión a la media simple) sufren *drawdowns* catastróficos.
3. El dimensionamiento fijo de riesgo (ej. operar siempre con el mismo lotaje) destruye cuentas en regímenes de turbulencia.

---

## 2. Formalización del Modelo de Dos Estados

El estado no observable del mercado en el tiempo $t$ se denota por $S_t \in \{1, 2\}$, donde:
* $S_t = 1$: **Régimen de Calma / Absorción** (Baja volatilidad, retornos positivos con media estable $\mu_1$, correlaciones diversificadas).
* $S_t = 2$: **Régimen de Turbulencia / Shock** (Alta volatilidad $\sigma_2 > 2\sigma_1$, saltos discretos en precios, primas de riesgo disparadas).

La probabilidad de transición entre regímenes se modela mediante una matriz estocástica de Markov:
$$\mathbf{P} = \begin{pmatrix} p_{11} & p_{12} \\ p_{21} & p_{22} \end{pmatrix}$$
Donde $p_{ij} = \mathbb{P}(S_t = j \mid S_{t-1} = i)$.

---

## 3. El Índice de Turbulencia Financiera de Kritzman

Kritzman define la distancia de Mahalanobis multivariada para medir la turbulencia en el instante $t$:
$$d_t = (\mathbf{r}_t - \boldsymbol{\mu}) \boldsymbol{\Sigma}^{-1} (\mathbf{r}_t - \boldsymbol{\mu})^\top$$

Donde:
* $\mathbf{r}_t$: Vector de retornos diarios de los activos clave (`US100`, `USDCLP`, `XAUUSD`, `WTI`, `US10Y`).
* $\boldsymbol{\mu}$: Vector de medias históricas de largo plazo.
* $\boldsymbol{\Sigma}$: Matriz de varianzas-covarianzas de largo plazo.

### Interpretación Cuantitativa:
* **$d_t < \text{Percentil 75}$**: Mercado en régimen normal $\rightarrow$ Estrategias de *Mean-Reversion*, soporte/resistencia y *Range Trading* operan con alta tasa de acierto.
* **$d_t > \text{Percentil 90}$ (Turbulencia Extrema)**: Mercado en shock $\rightarrow$ Se desactivan las compras en soportes contra tendencia; solo se permiten estrategias de *Momentum* o *Breakout* a favor del driver macro.

---

## 4. Implicancias para el Sistema de Gestión de Riesgo (Risk Management)

### A. Dynamic Position Sizing (Dimensionamiento por Régimen)
En lugar de arriesgar un número fijo de lotes, el tamaño de la posición ($V_t$) se normaliza inversamente al régimen de volatilidad:
$$V_t = \frac{\text{Riesgo Fijo en USD}}{\text{ATR}_{14}(S_t) \times \text{Valor Punto}}$$

### B. Regla Operativa en MT5
* **En Régimen 1 (Calma)**: Target Profit (TP) en 1.5 a 2.0 veces el ATR.
* **En Régimen 2 (Turbulencia)**: Stop Loss más amplio en puntos (pero menor lotaje para mantener el riesgo monetario idéntico) y gestión de salida mediante *Trailing Stop* sobre medias móviles exponenciales en H1/4H.
