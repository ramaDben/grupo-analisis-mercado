# Catálogo Maestro de Hipótesis Candidatas con Anclaje Teórico (SSRN & Peer-Reviewed)

> **Documento de Diseño Metodológico y Formulación de Hipótesis para Motor Genesis**  
> **Versión**: 1.3.0 (Versión Definitiva — Input Oficial para Genesis)  
> **Estado**: Aprobado como catálogo de hipótesis candidatas. **No aprobado para operación real.**  
> **Ámbito**: Formulación formal de 8 hipótesis operativas con anclaje conceptual en la literatura académica financiera (SSRN, *Journal of Finance*, NBER, AQR, Man AHL, BCCh), estructuradas como input inmutable para su validación estadística independiente en el motor **Genesis** (`ramaDben/genesis`).

---

## 1. Fundamento Epistemológico y Trazabilidad de Procedencia

Para eliminar el riesgo de *data-mining* y *p-hacking*:
1. **La literatura aporta el mecanismo económico general** (asimetría de información, fricciones de microestructura, persistencia por *underreaction* institucional o primas de riesgo).
2. **El desk formula la adaptación sintética** (timeframe H1/M15, instrumento CFD, filtros de volatilidad y régimen macro).
3. **El motor Genesis ejecuta la validación cuantitativa independiente**. Ninguna estrategia opera con capital real antes de completar el ciclo de vida de promoción.

---

## 2. Ciclo de Vida y Flujo de Promoción de Hipótesis

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. CATÁLOGO v1.3 ACEPTADO (Docs / config)                              │
│    Hipótesis teórica formulada con procedencia y espacio de búsqueda   │
│    Estado: CANDIDATO                                                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. IMPLEMENTACIÓN EN MOTOR GENESIS (ramaDben/genesis)                  │
│    Codificación de la lógica técnica y encapsulamiento en trial_ledger │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. VALIDACIÓN ESTADÍSTICA (Fase 0)                                     │
│    WFA Out-of-Sample + Purged CV + Monte Carlo + DSR/PBO               │
│    Gate: DSR > 0 | PBO < 0.20 | Sharpe OOS >= 50% IS | MaxDD <= 15%    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. INCUBACIÓN EN CUENTA DEMO / PAPER TRADING                           │
│    Prueba de ejecución en vivo (latencia, slippage real, fill rate)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. OPERACIÓN EN VIVO CON CAPITAL REAL                                  │
│    Estado: VALIDADO (con asignación de riesgo limitada)                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Protocolo de Validación Estadística en Genesis (Fase 0)

### A. Unidad de Validación Atómica (`Estrategia × Activo`)
La unidad de validación no es la estrategia abstracta, sino la tupla **`Estrategia × Activo`**. Cada tupla se registra en el ledger con un identificador único:

$$\text{trial\_id} = \text{\{ID\_SETUP\}\_\_\{SYMBOL\}\_\_v1}$$

### B. Control Estricto del Espacio de Búsqueda (*Trial Ledger Anti-P-Hacking*)
* **Regla de Parámetros**: Todo parámetro que el código pueda modificar debe pertenecer a `espacio_de_busqueda_parametros` con rango y paso de grilla pre-declarados, o estar listado en `constantes_congeladas`.
* Todas las combinaciones evaluadas por Genesis (incluidas las que fallen o den Sharpe negativo) se contabilizan en el número total de ensayos ($N_{\text{trials}}$) para el cálculo de **DSR** y **PBO**.
* **Prohibido el *cherry-picking* manual** o el re-ajuste sobre la muestra out-of-sample (OOS).

### C. Prevención de *Look-Ahead Bias* (Régimen *Point-in-Time*)
Genesis evaluará las estrategias utilizando exclusivamente el snapshot **Point-in-Time** de `macro_bias_output.json` disponible en el timestamp histórico exacto $t$, prohibiendo el uso de revisiones macroeconómicas retroactivas.

---

## 4. Pre-requisito de Infraestructura de Datos (Opción A)

Antes de iniciar la validación en Genesis, se extiende `scripts/extractor_precios.py` en `data central/DATA PRECIOS OHLC/`:
1. **Velas M15** (200 períodos) para `USDCLP`, `XAUUSD`, `WTI`, `BRENT`, `US100`, `COPPER`.
2. **Cálculo de Indicadores Técnicos**:
   * $\text{RSI}_{14}$ en M15, H1 y D1.
   * $\text{EMA}_{20}$ en M15, H1 y D1.
   * $\text{SMA}_{20}$ en H1.
3. **Métrica de Actividad**: *Tick Volume* nativo de MT5 como proxy de actividad intradía.

---

## 5. Catálogo de las 8 Hipótesis Candidatas

---

### 🟢 FAMILIA 1: Reversión a la Media y Barridos de Liquidez ($\mathcal{R}_0$)

#### Hipótesis 1: `FADE_SUPPORT_RESISTANCE_M15`
```yaml
id_setup: "FADE_SUPPORT_RESISTANCE_M15"
familia: "REVERSION_RANGO"
regimen_macro_optimo: "R0_CALMA_RANGO"
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s1_fade_m15_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Biais, Hillion & Spatt (1995)"
      paper: "An Empirical Analysis of the Limit Order Book and the Order Flow in the Paris Bourse"
      journal: "The Journal of Finance, 50(5), 1655-1689"
    - autor: "Hasbrouck & Saar (2013)"
      paper: "Low-Latency Trading"
      journal: "Journal of Financial Markets, 16(4), 646-679"
  transformaciones:
    - "Adaptación a velas M15 en instrumentos FX emergentes e índices CFD"
    - "Filtro de ejecución condicionado a régimen macro R0"
  mecanismo_preservado: "Absorción de liquidez en extremos de libro y reversión post-sweep"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S1_FADE_M15__USDCLP__v1"
  - trial_id: "S1_FADE_M15__US100__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    USDCLP: [LONG, SHORT]
    US100: [LONG, SHORT]
  R1_SHOCK_INFLACIONARIO:
    USDCLP: []
    US100: []
  R2_GOLDILOCKS_EXPANSION:
    USDCLP: [LONG, SHORT]
    US100: [LONG, SHORT]
  R3_ESTANFLACION_SHOCK:
    USDCLP: []
    US100: []
  R4_RECESION_VUELO_CALIDAD:
    USDCLP: []
    US100: []

espacio_de_busqueda_parametros:
  tamano_mecha_atr_mult:
    valor_base: 0.5
    rango_permitido: [0.3, 0.7]
    paso_grilla: 0.1
  lookback_donchian_m15:
    valor_base: 50
    rango_permitido: [30, 70]
    paso_grilla: 10
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1

constantes_congeladas:
  timeframe_ejecucion: "M15"
  timeframe_filtro_atr: "H1"
  tipo_take_profit: "NIVEL_OPUESTO_CANAL"
```
* **Qué demuestra la literatura citada**: La concentración de órdenes límite en los extremos genera barridos de liquidez transitorios seguidos de reversión por absorción del flujo informado.
* **Gatillo M15**: Perforación del nivel $S_1/R_1$, reingreso dentro del Donchian M15 y vela de rechazo con mecha $\ge \text{tamano\_mecha\_atr\_mult} \times \text{ATR}_{14}(\text{M15})$. Stop Loss a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$.

---

#### Hipótesis 2: `MEAN_REVERSION_RSI_H1`
```yaml
id_setup: "MEAN_REVERSION_RSI_H1"
familia: "REVERSION_RANGO"
regimen_macro_optimo: "R0_CALMA_RANGO"
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s2_mean_rev_rsi_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Avellaneda & Lee (2010)"
      paper: "Statistical Arbitrage in the US Equities Market"
      journal: "SSRN / Quantitative Finance, 10(7), 761-782"
  transformaciones:
    - "Modelado de Z-score mediante oscilador RSI(14) en compresión H1"
    - "Restricción de disparo a proximidad de soportes/resistencias D1"
  mecanismo_preservado: "Reversión a la media bajo procesos estacionarios Ornstein-Uhlenbeck"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S2_MEAN_REV_RSI_H1__USDCLP__v1"
  - trial_id: "S2_MEAN_REV_RSI_H1__XAUUSD__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    USDCLP: [LONG, SHORT]
    XAUUSD: [LONG, SHORT]
  R1_SHOCK_INFLACIONARIO:
    USDCLP: []
    XAUUSD: []
  R2_GOLDILOCKS_EXPANSION:
    USDCLP: [LONG, SHORT]
    XAUUSD: [LONG, SHORT]
  R3_ESTANFLACION_SHOCK:
    USDCLP: []
    XAUUSD: []
  R4_RECESION_VUELO_CALIDAD:
    USDCLP: []
    XAUUSD: []

espacio_de_busqueda_parametros:
  rsi_sobreventa_umbral:
    valor_base: 28.0
    rango_permitido: [20.0, 30.0]
    paso_grilla: 2.0
  rsi_sobrecompra_umbral:
    valor_base: 72.0
    rango_permitido: [70.0, 80.0]
    paso_grilla: 2.0
  distancia_max_nivel_atr:
    valor_base: 0.3
    rango_permitido: [0.2, 0.5]
    paso_grilla: 0.1
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1

constantes_congeladas:
  timeframe_ejecucion: "H1"
  periodo_rsi: 14
  nivel_take_profit_media: "SMA_20_H1"
```
* **Qué demuestra la literatura citada**: Procesos estacionarios modelados como Ornstein-Uhlenbeck exhiben reversión predecible desde extremos de colas estocásticas.
* **Gatillo H1**: $\text{RSI}_{14} \le \text{rsi\_sobreventa}$ o $\ge \text{rsi\_sobrecompra}$ a distancia $\le \text{distancia\_max\_nivel\_atr} \times \text{ATR}_{14}(\text{H1})$ de soporte/resistencia fractal D1, con confirmación de vela H1 reingresando a zona neutral. Stop Loss a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$; TP en $\text{SMA}_{20}(\text{H1})$.

---

### 🔴 FAMILIA 2: Ruptura y Momentum Asimétrico ($\mathcal{R}_1 / \mathcal{R}_3 / \mathcal{R}_4$)

#### Hipótesis 3: `BREAKOUT_DONCHIAN_H1` (Simétrica)
```yaml
id_setup: "BREAKOUT_DONCHIAN_H1"
familia: "RUPTURA_MOMENTUM"
regimen_macro_optimo: ["R1_SHOCK_INFLACIONARIO", "R3_ESTANFLACION_SHOCK", "R4_RECESION_VUELO_CALIDAD"]
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s3_donchian_breakout_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Moskowitz, Ooi & Pedersen (2012)"
      paper: "Time Series Momentum"
      journal: "Journal of Financial Economics, 104(2), 228-250"
    - autor: "Baltas & Kosowski (2013)"
      paper: "Improving Time-Series Momentum Strategies: The Role of Volatility Estimators and Trading Signals"
      journal: "SSRN Electronic Journal / Imperial College Business School"
  transformaciones:
    - "Canal Donchian(50) en compresión H1 con banda de filtro proporcional al ATR"
    - "Salida asimétrica por Chandelier Trailing Stop"
  mecanismo_preservado: "Persistencia de tendencia por sub-reacción institucional (underreaction)"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1"
  - trial_id: "S3_BREAKOUT_DONCHIAN_H1__WTI__v1"
  - trial_id: "S3_BREAKOUT_DONCHIAN_H1__BRENT__v1"
  - trial_id: "S3_BREAKOUT_DONCHIAN_H1__US100__v1"
  - trial_id: "S3_BREAKOUT_DONCHIAN_H1__COPPER__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    XAUUSD: []
    WTI: []
    BRENT: []
    US100: []
    COPPER: []
  R1_SHOCK_INFLACIONARIO:
    XAUUSD: [LONG]
    WTI: [LONG]
    BRENT: [LONG]
    US100: []     # Prohibido por contradicción macro
    COPPER: []
  R2_GOLDILOCKS_EXPANSION:
    XAUUSD: [LONG]
    US100: [LONG]
    COPPER: [LONG]
    WTI: []
    BRENT: []
  R3_ESTANFLACION_SHOCK:
    XAUUSD: [LONG]
    WTI: [LONG]
    BRENT: [LONG]
    US100: [SHORT]
    COPPER: [SHORT]
  R4_RECESION_VUELO_CALIDAD:
    XAUUSD: [LONG]
    US100: [SHORT]
    COPPER: [SHORT]
    WTI: [SHORT]
    BRENT: [SHORT]

espacio_de_busqueda_parametros:
  lookback_donchian:
    valor_base: 50
    rango_permitido: [30, 70]
    paso_grilla: 10
  banda_filtro_atr_mult:
    valor_base: 0.3
    rango_permitido: [0.1, 0.5]
    paso_grilla: 0.1
  expansion_rango_atr_mult:
    valor_base: 1.2
    rango_permitido: [1.0, 1.5]
    paso_grilla: 0.1
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1
  trailing_chandelier_atr_mult:
    valor_base: 3.0
    rango_permitido: [2.5, 4.0]
    paso_grilla: 0.5

constantes_congeladas:
  timeframe_ejecucion: "H1"
  periodo_atr: 14
```
* **Gatillos**:
  * *Largo*: $\text{Close}_{\text{H1}} > \text{DonchianHigh}_{N} + (b \times \text{ATR}_{14}) \land \text{Rango} \ge k \times \text{ATR}_{14}$.
  * *Corto*: $\text{Close}_{\text{H1}} < \text{DonchianLow}_{N} - (b \times \text{ATR}_{14}) \land \text{Rango} \ge k \times \text{ATR}_{14}$.
  * *Salida*: Chandelier Trailing Exit a $\text{trailing\_chandelier\_atr\_mult} \times \text{ATR}_{14}$.

---

#### Hipótesis 4: `BREAKOUT_VOLATILITY_H1` (Simétrica: Shocks Alcistas y Bajistas)
```yaml
id_setup: "BREAKOUT_VOLATILITY_H1"
familia: "RUPTURA_MOMENTUM"
regimen_macro_optimo: ["R1_SHOCK_INFLACIONARIO", "R3_ESTANFLACION_SHOCK", "R4_RECESION_VUELO_CALIDAD"]
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s4_volatility_breakout_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Kilian, L. (2009)"
      paper: "Not All Oil Price Shocks Are Alike"
      journal: "American Economic Review, 99(3), 1053-1069"
    - autor: "Lempérière, Y. et al. (2014, CFM)"
      paper: "Two Centuries of Trend Following on Non-Equity Assets"
      journal: "Journal of Investment Strategies, 3(3), 41-61"
  transformaciones:
    - "Gatillo intradiario de apertura de sesión post-shock de volatilidad D1"
    - "Filtro de actividad por RVOL en MT5"
  mecanismo_preservado: "Asimetría positiva y agrupamiento de volatilidad en energía y metales"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S4_BREAKOUT_VOL_H1__WTI__v1"
  - trial_id: "S4_BREAKOUT_VOL_H1__BRENT__v1"
  - trial_id: "S4_BREAKOUT_VOL_H1__XAUUSD__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    WTI: []
    BRENT: []
    XAUUSD: []
  R1_SHOCK_INFLACIONARIO:
    WTI: [LONG]
    BRENT: [LONG]
    XAUUSD: [LONG]
  R2_GOLDILOCKS_EXPANSION:
    WTI: [LONG]
    BRENT: [LONG]
    XAUUSD: [LONG]
  R3_ESTANFLACION_SHOCK:
    WTI: [LONG]
    BRENT: [LONG]
    XAUUSD: [LONG]
  R4_RECESION_VUELO_CALIDAD:
    WTI: [SHORT]
    BRENT: [SHORT]
    XAUUSD: [LONG]

espacio_de_busqueda_parametros:
  shock_diario_min_pct:
    valor_base: 2.5
    rango_permitido: [2.0, 3.5]
    paso_grilla: 0.5
  rvol_minimo:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.2
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1
  trailing_stop_atr_mult:
    valor_base: 3.0
    rango_permitido: [2.5, 4.0]
    paso_grilla: 0.5

constantes_congeladas:
  timeframe_ejecucion: "H1"
  timeframe_shock: "D1"
```
* **Gatillos**:
  * *Shock Positivo* ($\Delta\%_{\text{D1}} \ge +\text{shock\_min}$): Compra en la primera vela H1 que rompa el máximo de la sesión previa.
  * *Shock Negativo* ($\Delta\%_{\text{D1}} \le -\text{shock\_min}$): Venta en la primera vela H1 que rompa el mínimo de la sesión previa.
  * *Salida*: Trailing Stop a $\text{trailing\_stop\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$.

---

### 🟡 FAMILIA 3: Retroceso y Reanudación Tendencial ($\mathcal{R}_2$)

#### Hipótesis 5: `PULLBACK_EMA20_H1`
```yaml
id_setup: "PULLBACK_EMA20_H1"
familia: "PULLBACK_TENDENCIA"
regimen_macro_optimo: "R2_GOLDILOCKS_EXPANSION"
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s5_pullback_ema20_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Asness, C. S., Frazzini, A., Israel, R., & Moskowitz, T. J. (2014)"
      paper: "Fact, Fiction, and Momentum Investing"
      journal: "The Journal of Portfolio Management, 40(5), 75-92 (AQR / SSRN)"
  transformaciones:
    - "Soporte dinámico de flujo en EMA20 H1 con tendencia confirmada por EMA50/EMA200"
    - "Filtro de consolidación con RSI(14) en zona neutral [45, 55]"
  mecanismo_preservado: "Reincorporación a primas de momentum tras consolidación transitoria"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S5_PULLBACK_EMA20_H1__US100__v1"
  - trial_id: "S5_PULLBACK_EMA20_H1__XAUUSD__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    US100: []
    XAUUSD: []
  R1_SHOCK_INFLACIONARIO:
    US100: []
    XAUUSD: []   # Prohibido en R1 por riesgo de desanclaje de tasas
  R2_GOLDILOCKS_EXPANSION:
    US100: [LONG]
    XAUUSD: [LONG]
  R3_ESTANFLACION_SHOCK:
    US100: []
    XAUUSD: []
  R4_RECESION_VUELO_CALIDAD:
    US100: []
    XAUUSD: []

espacio_de_busqueda_parametros:
  rsi_rango_min:
    valor_base: 45.0
    rango_permitido: [40.0, 48.0]
    paso_grilla: 2.0
  rsi_rango_max:
    valor_base: 55.0
    rango_permitido: [52.0, 60.0]
    paso_grilla: 2.0
  distancia_max_pullback_atr:
    valor_base: 0.4
    rango_permitido: [0.2, 0.6]
    paso_grilla: 0.1
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1
  trailing_stop_atr_mult:
    valor_base: 2.5
    rango_permitido: [2.0, 3.5]
    paso_grilla: 0.5

constantes_congeladas:
  timeframe_ejecucion: "H1"
  periodo_ema_pullback: 20
  periodo_ema_filtro_rapido: 50
  periodo_ema_filtro_lento: 200
  parcial_take_profit_r1_pct: 50.0
```
* **Gatillo H1**: $\text{EMA}_{20} > \text{EMA}_{50} > \text{EMA}_{200}$, retroceso testeando $\text{EMA}_{20}$ a distancia $\le \text{distancia\_max\_pullback\_atr} \times \text{ATR}_{14}$, $\text{RSI}_{14} \in [\text{rsi\_min}, \text{rsi\_max}]$, y vela envolvente alcista H1. Stop Loss bajo $\text{EMA}_{50}$ a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}$; Salida 50% en $R_1$ y 50% con Trailing Stop a $\text{trailing\_stop\_atr\_mult} \times \text{ATR}_{14}$.

---

#### Hipótesis 6: `PULLBACK_EMA50_H1`
```yaml
id_setup: "PULLBACK_EMA50_H1"
familia: "PULLBACK_TENDENCIA"
regimen_macro_optimo: "R2_GOLDILOCKS_EXPANSION"
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s6_pullback_ema50_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Lo, A. W., Mamaysky, H., & Wang, J. (2000)"
      paper: "Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation"
      journal: "The Journal of Finance, 55(4), 1705-1765"
  transformaciones:
    - "Uso de EMA50 H1 como aproximación de soporte paramétrico suavizado"
    - "Confirmación mediante divergencia alcista oculta en oscilador RSI"
  mecanismo_preservado: "Contenido informativo no paramétrico de patrones geométricos y medias móviles"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S6_PULLBACK_EMA50_H1__XAUUSD__v1"
  - trial_id: "S6_PULLBACK_EMA50_H1__US100__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    XAUUSD: []
    US100: []
  R1_SHOCK_INFLACIONARIO:
    XAUUSD: []
    US100: []
  R2_GOLDILOCKS_EXPANSION:
    XAUUSD: [LONG]
    US100: [LONG]
  R3_ESTANFLACION_SHOCK:
    XAUUSD: []
    US100: []
  R4_RECESION_VUELO_CALIDAD:
    XAUUSD: []
    US100: []

espacio_de_busqueda_parametros:
  lookback_ema_soporte:
    valor_base: 50
    rango_permitido: [40, 60]
    paso_grilla: 5
  umbral_divergencia_rsi_puntos:
    valor_base: 3.0
    rango_permitido: [2.0, 5.0]
    paso_grilla: 1.0
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1

constantes_congeladas:
  timeframe_ejecucion: "H1"
  filtro_tendencia_d1: "Close_D1 > EMA_200_D1"
  nivel_take_profit: "DONCHIAN_HIGH_50_H1"
```
* **Gatillo H1**: Corrección hacia $\text{EMA}_{\text{soporte}}(\text{H1})$ manteniendo $\text{Close}_{\text{D1}} > \text{EMA}_{200}(\text{D1})$, confirmada por divergencia alcista oculta en RSI ($\Delta \text{RSI} \ge \text{umbral\_divergencia}$). Stop Loss bajo $\text{EMA}_{50}$ a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}$; TP al máximo Donchian 50 H1.

---

### 🔵 FAMILIA 4: Desfases Intermercado (*Lead-Lag Cross-Asset*)

#### Hipótesis 7: `COPPER_LEAD_LAG_USDCLP`
```yaml
id_setup: "COPPER_LEAD_LAG_USDCLP"
familia: "ARBITRAJE_INTERMERCADO"
regimen_macro_optimo: ["R0_CALMA_RANGO", "R2_GOLDILOCKS_EXPANSION"]
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s7_copper_lead_lag_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Hong, H., & Stein, J. C. (1999)"
      paper: "A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets"
      journal: "The Journal of Finance, 54(6), 2143-2184"
    - autor: "Caputo, R., Núñez, M., & Valdés, R. (2007)"
      paper: "Análisis del Tipo de Cambio en la Práctica"
      journal: "Banco Central de Chile, Documento de Trabajo N° 434"
    - autor: "Menkhoff, L. et al. (2012)"
      paper: "Carry Trades and Global FX Volatility"
      journal: "The Journal of Finance, 67(2), 681-718"
  transformaciones:
    - "Divergencia intradiaria entre Cobre COMEX y USD/CLP spot interbancario"
    - "Gatillo en compresión M15 sobre EMA20"
  mecanismo_preservado: "Difusión gradual de información y spillovers de materias primas a monedas de exportadores"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S7_COPPER_LEAD_LAG__USDCLP__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    USDCLP: [LONG, SHORT] # Inverso al movimiento del Cobre
  R1_SHOCK_INFLACIONARIO:
    USDCLP: []           # Prohibido por primas de riesgo desalineadas
  R2_GOLDILOCKS_EXPANSION:
    USDCLP: [SHORT]       # Con Cobre alcista, solo venta de USDCLP
  R3_ESTANFLACION_SHOCK:
    USDCLP: []
  R4_RECESION_VUELO_CALIDAD:
    USDCLP: [LONG]        # Con Cobre colapsando, solo compra de USDCLP

espacio_de_busqueda_parametros:
  cobre_umbral_intraday_pct:
    valor_base: 1.2
    rango_permitido: [1.0, 1.6]
    paso_grilla: 0.2
  usdclp_inaccion_max_pct:
    valor_base: 0.2
    rango_permitido: [0.1, 0.3]
    paso_grilla: 0.05
  latencia_max_velas_m15:
    valor_base: 4       # 4 velas M15 = 60 minutos
    rango_permitido: [2, 3, 4, 6] # 30, 45, 60, 90 minutos
    paso_grilla: 1
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1

constantes_congeladas:
  timeframe_ejecucion: "M15"
  timeframe_filtro_atr: "H1"
  periodo_ema_gatillo: 20
  salida_tp_donchian: "NIVEL_MEDIO_DONCHIAN_M15"
```
* **Gatillo M15**: $|\Delta\% \text{Cobre}| \ge \text{cobre\_umbral}$ dentro de las últimas $\text{latencia\_max\_velas\_m15}$ barras M15, con $|\Delta\% \text{USDCLP}| \le \text{usdclp\_inaccion}$. Ruptura de $\text{EMA}_{20}(\text{M15})$ en USD/CLP en dirección contraria al Cobre. Stop Loss a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$; TP en nivel medio Donchian M15.

---

#### Hipótesis 8: `REAL_YIELD_MOMENTUM_XAUUSD`
```yaml
id_setup: "REAL_YIELD_MOMENTUM_XAUUSD"
familia: "ARBITRAJE_INTERMERCADO"
regimen_macro_optimo: ["R1_SHOCK_INFLACIONARIO", "R3_ESTANFLACION_SHOCK"]
estado_validacion: "CANDIDATO"

implementacion:
  strategy_code_version: "s8_real_yield_mom_v1"
  data_schema_version: "ohlc_v2"
  regime_schema_version: "macro_bias_v2.0.0"

procedencia:
  tipo: "SINTETICA_DERIVADA"
  derivada_de:
    - autor: "Erb, C. B., & Harvey, C. R. (2013)"
      paper: "The Golden Dilemma"
      journal: "Financial Analysts Journal, 69(4), 10-42 (NBER Working Paper No. 18706)"
    - autor: "World Gold Council (2020)"
      paper: "Gold Return Attribution Model (GRAM)"
      journal: "World Gold Council Research"
  transformaciones:
    - "Gatillo técnico intradiario H1 sobre Oro condicionado a variaciones semanales de DFII10"
    - "Gestión de salida por Chandelier Trailing Exit"
  mecanismo_preservado: "Costo de oportunidad del capital (tasas reales) en activos de flujo cero"
  auditoria_humana: "PENDIENTE"

unidades_de_validacion:
  - trial_id: "S8_REAL_YIELD_MOM__XAUUSD__v1"

direcciones_por_regimen:
  R0_CALMA_RANGO:
    XAUUSD: []
  R1_SHOCK_INFLACIONARIO:
    XAUUSD: [LONG]
  R2_GOLDILOCKS_EXPANSION:
    XAUUSD: [LONG]
  R3_ESTANFLACION_SHOCK:
    XAUUSD: [LONG]
  R4_RECESION_VUELO_CALIDAD:
    XAUUSD: [LONG]

espacio_de_busqueda_parametros:
  tips_shock_5d_bps:
    valor_base: -5.0
    rango_permitido: [-8.0, -3.0]
    paso_grilla: 1.0
  lookback_dias_tips:
    valor_base: 5
    rango_permitido: [3, 5, 10]
    paso_grilla: 1 # o conjunto discreto [3, 5, 10]
  fractal_swing_bars:
    valor_base: 5
    rango_permitido: [3, 7]
    paso_grilla: 2
  stop_loss_atr_mult:
    valor_base: 1.5
    rango_permitido: [1.2, 2.0]
    paso_grilla: 0.1
  trailing_chandelier_atr_mult:
    valor_base: 3.0
    rango_permitido: [2.5, 4.0]
    paso_grilla: 0.5

constantes_congeladas:
  timeframe_ejecucion: "H1"
  serie_tasa_real: "DFII10"
```
* **Gatillo H1**: Shock semanal en TIPS $\Delta \text{DFII10}_{N\text{D}} \le \text{tips\_shock\_bps}$. Ruptura de resistencia fractal H1 (máximo de $\text{fractal\_swing\_bars}$ barras) en Oro a favor del movimiento. Stop Loss a $\text{stop\_loss\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$; Trailing Stop a $\text{trailing\_chandelier\_atr\_mult} \times \text{ATR}_{14}(\text{H1})$.

---

## 6. Matriz Declarativa Centralizada de Compatibilidad y Dirección (SSOT)

```yaml
# ==============================================================================
# MATRIZ CENTRALIZADA DE COMPATIBILIDAD Y DIRECCIÓN — FUENTE ÚNICA DE LA VERDAD
# ==============================================================================
matriz_compatibilidad_y_direccion:
  R0_CALMA_RANGO:
    S1_FADE_SUPPORT_RESISTANCE_M15: { estado: "OPTIMA",     direcciones: { USDCLP: [LONG, SHORT], US100: [LONG, SHORT] } }
    S2_MEAN_REVERSION_RSI_H1:       { estado: "OPTIMA",     direcciones: { USDCLP: [LONG, SHORT], XAUUSD: [LONG, SHORT] } }
    S3_BREAKOUT_DONCHIAN_H1:        { estado: "PROHIBIDA",  direcciones: {} }
    S4_BREAKOUT_VOLATILITY_H1:      { estado: "PROHIBIDA",  direcciones: {} }
    S5_PULLBACK_EMA20_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S6_PULLBACK_EMA50_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S7_COPPER_LEAD_LAG_USDCLP:      { estado: "OPTIMA",     direcciones: { USDCLP: [LONG, SHORT] } }
    S8_REAL_YIELD_MOMENTUM_XAUUSD:  { estado: "PROHIBIDA",  direcciones: {} }

  R1_SHOCK_INFLACIONARIO:
    S1_FADE_SUPPORT_RESISTANCE_M15: { estado: "PROHIBIDA",  direcciones: {} }
    S2_MEAN_REVERSION_RSI_H1:       { estado: "PROHIBIDA",  direcciones: {} }
    S3_BREAKOUT_DONCHIAN_H1:        { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], WTI: [LONG], BRENT: [LONG] } }
    S4_BREAKOUT_VOLATILITY_H1:      { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], WTI: [LONG], BRENT: [LONG] } }
    S5_PULLBACK_EMA20_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S6_PULLBACK_EMA50_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S7_COPPER_LEAD_LAG_USDCLP:      { estado: "PROHIBIDA",  direcciones: {} }
    S8_REAL_YIELD_MOMENTUM_XAUUSD:  { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG] } }

  R2_GOLDILOCKS_EXPANSION:
    S1_FADE_SUPPORT_RESISTANCE_M15: { estado: "SECUNDARIA", direcciones: { USDCLP: [LONG, SHORT], US100: [LONG, SHORT] } }
    S2_MEAN_REVERSION_RSI_H1:       { estado: "SECUNDARIA", direcciones: { USDCLP: [LONG, SHORT], XAUUSD: [LONG, SHORT] } }
    S3_BREAKOUT_DONCHIAN_H1:        { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], US100: [LONG], COPPER: [LONG] } }
    S4_BREAKOUT_VOLATILITY_H1:      { estado: "SECUNDARIA", direcciones: { XAUUSD: [LONG], WTI: [LONG], BRENT: [LONG] } }
    S5_PULLBACK_EMA20_H1:           { estado: "OPTIMA",     direcciones: { US100: [LONG], XAUUSD: [LONG] } }
    S6_PULLBACK_EMA50_H1:           { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], US100: [LONG] } }
    S7_COPPER_LEAD_LAG_USDCLP:      { estado: "OPTIMA",     direcciones: { USDCLP: [SHORT] } }
    S8_REAL_YIELD_MOMENTUM_XAUUSD:  { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG] } }

  R3_ESTANFLACION_SHOCK:
    S1_FADE_SUPPORT_RESISTANCE_M15: { estado: "PROHIBIDA",  direcciones: {} }
    S2_MEAN_REVERSION_RSI_H1:       { estado: "PROHIBIDA",  direcciones: {} }
    S3_BREAKOUT_DONCHIAN_H1:        { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], WTI: [LONG], BRENT: [LONG], US100: [SHORT], COPPER: [SHORT] } }
    S4_BREAKOUT_VOLATILITY_H1:      { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], WTI: [LONG], BRENT: [LONG] } }
    S5_PULLBACK_EMA20_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S6_PULLBACK_EMA50_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S7_COPPER_LEAD_LAG_USDCLP:      { estado: "PROHIBIDA",  direcciones: {} }
    S8_REAL_YIELD_MOMENTUM_XAUUSD:  { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG] } }

  R4_RECESION_VUELO_CALIDAD:
    S1_FADE_SUPPORT_RESISTANCE_M15: { estado: "PROHIBIDA",  direcciones: {} }
    S2_MEAN_REVERSION_RSI_H1:       { estado: "PROHIBIDA",  direcciones: {} }
    S3_BREAKOUT_DONCHIAN_H1:        { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], US100: [SHORT], COPPER: [SHORT], WTI: [SHORT], BRENT: [SHORT] } }
    S4_BREAKOUT_VOLATILITY_H1:      { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG], WTI: [SHORT], BRENT: [SHORT] } }
    S5_PULLBACK_EMA20_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S6_PULLBACK_EMA50_H1:           { estado: "PROHIBIDA",  direcciones: {} }
    S7_COPPER_LEAD_LAG_USDCLP:      { estado: "PERMITIDA",  direcciones: { USDCLP: [LONG] } }
    S8_REAL_YIELD_MOMENTUM_XAUUSD:  { estado: "OPTIMA",     direcciones: { XAUUSD: [LONG] } }
```

---

## 7. Plan de Implementación y Tests de Integridad para Genesis

```
grupo-analisis-mercado/
│
├── scripts/
│   └── [MODIFY] extractor_precios.py               <-- Pre-requisito: Extensión M15, RSI14, EMA20, SMA20
│
├── docs/
│   ├── [NEW] CATALOGO_ESTRATEGIAS_E_HIPOTESIS.md   <-- Manual consolidado v1.3.0
│   └── investigacion_estrategias/                  <-- 8 Fichas con procedencia y espacio de búsqueda
│       ├── 01_biais_hasbrouck_fade_liquidity.md
│       ├── 02_avellaneda_lee_mean_reversion_ou.md
│       ├── 03_baltas_kosowski_donchian_breakout.md
│       ├── 04_kilian_lemperiere_volatility_crisis_alpha.md
│       ├── 05_asness_aqr_ema_pullback_momentum.md
│       ├── 06_lo_mamaysky_nonparametric_golden_retest.md
│       ├── 07_hong_stein_caputo_copper_lead_lag.md
│       └── 08_erb_harvey_real_yield_arbitrage.md
│
├── config/
│   └── [MODIFY] playbook_config.yaml               <-- Matriz de compatibilidad SSOT y espacios de búsqueda
│
├── .agents/skills/trading-cuantitativo-intermercado/
│   └── [MODIFY] SKILL.md                          <-- Instrucciones tácticas y estado CANDIDATO
│
└── tests/
    └── [NEW] test_catalogo_estrategias.py          <-- Suite de integridad matemática y ledger
```

### Especificación de la Suite Automatizada (`tests/test_catalogo_estrategias.py`):
1. **`test_all_strategies_are_candidates`**: Valida que el 100% de las estrategias en el registro tengan `estado_validacion == "CANDIDATO"`.
2. **`test_every_active_strategy_has_search_space_or_frozen_constants`**: Valida que ninguna estrategia tenga parámetros libres sin rango o constantes congeladas.
3. **`test_every_trial_has_unique_id`**: Valida la unicidad global de cada `trial_id` (tupla `Estrategia × Activo`).
4. **`test_matrix_matches_strategy_directions`**: Valida byte a byte que las direcciones declaradas en cada ficha coincidan exactamente con `matriz_compatibilidad_y_direccion` (SSOT).
5. **`test_no_live_status_before_genesis`**: Valida que ninguna regla pueda ser ejecutada en modo real si no cuenta con el certificado de promoción de Genesis.
