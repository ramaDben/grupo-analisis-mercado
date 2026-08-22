# Biblioteca de Investigación: Análisis Intermercado y Regímenes Cuantitativos
**Grupo de Análisis de Mercado — Dirección de Trading**

Esta biblioteca recopila y formaliza la literatura académica, estudios econométricos y *working papers* de bancos centrales e instituciones financieras globales (Bridgewater, AQR, Fed de Nueva York, Banco Central de Chile, NBER, Journal of Finance) que fundamentan la integración entre el **Análisis Macroeconómico Intermercado** y la **Toma de Decisiones Técnicas Operativas**.

---

## 🏛️ Taxonomía de la Biblioteca

```
docs/investigacion_intermarket/
│
├── README_BIBLIOTECA.md                          <-- Índice general y matriz de compatibilidad
│
├── 01_marcos_intermercado_y_regimenes/           <-- Causalidad cross-asset y matrices de régimen
│   ├── 01_murphy_analisis_intermercado.md
│   ├── 02_bridgewater_all_weather_regimenes.md
│   └── 03_kritzman_cambios_de_regimen_markov.md
│
├── 02_evidencia_cuantitativa_estrategias/        <-- Validación empírica de ventaja técnica y sizing
│   ├── 01_moskowitz_pedersen_time_series_momentum.md
│   ├── 02_asness_aqr_value_and_momentum.md
│   ├── 03_man_group_cfm_volatility_targeting_and_trend.md
│   └── 04_lo_mamaysky_brock_empirical_technical_rules.md
│
├── 03_commodities_oro_y_tasas/                   <-- Modelos de tasas reales, energía y metales
│   ├── 01_erb_harvey_golden_dilemma_tasas_reales.md
│   ├── 02_estrella_mishkin_curva_rendimientos_fed.md
│   └── 03_wgc_kilian_gold_oil_structural_shocks.md
│
└── 04_banco_central_chile_y_usdclp/              <-- Microestructura oficial local y lead-lag
    ├── 01_bcch_caputo_valdes_tipo_cambio_cobre.md
    ├── 02_bcch_carreno_cox_carry_trade_forwards.md
    └── 03_menkhoff_sarno_fx_volatility_and_lead_lag.md
```

---

## 📊 Matriz de Compatibilidad: Régimen Macro vs. Estrategia Técnica

El objetivo central de esta investigación es responder: **¿Qué arquetipo técnico tiene expectativa matemática positiva ($E > 0$) bajo cada régimen de mercado?**

| Régimen Macroeconómico | Drivers Principales en `data central/` | Arquetipo Técnico Óptimo | Arquetipos Prohibidos / Penalizados |
| :--- | :--- | :--- | :--- |
| **R1: Shock Inflacionario / Cost-Push** | Petróleo $\uparrow$, Tasas 10Y $\uparrow$, Curva 2s10s aplanándose | **Breakout / Trend-Following** en Commodities y Refugios | *Mean-Reversion* en Renta Variable (caídas persistentes) |
| **R2: Expansión / Desinflación (Goldilocks)**| Tasas 10Y estables/bajando, Cobre $\uparrow$, Volatilidad $\downarrow$ | **Momentum** en Índices Tech + **Carry Trade** en FX | *Breakdowns* agresivos en Renta Variable |
| **R3: Estanflación / Tensión Geopolítica**| WTI/Brent $\uparrow$, Actividad/Imacec $\downarrow$, Tasas volátiles | **Volatility Breakout** + Momentum en Oro (`XAUUSD`) | Operativa de rango estrecho sin SL holgado |
| **R4: Desaceleración / Vuelo a la Calidad**| Cobre $\downarrow$, Curva empinándose por recortes de tasas | **Trend-Following Alcista en USD/CLP** + Venta de rebotes | Compras por "sobreventa" en materias primas cíclicas |

---

## 📚 Índice de Fichas de Investigación

### Módulo 1: Marcos Intermercado y Regímenes
1. [`01_murphy_analisis_intermercado.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/01_marcos_intermercado_y_regimenes/01_murphy_analisis_intermercado.md): La secuencia líder-rezago entre Bonos $\rightarrow$ Acciones $\rightarrow$ Commodities $\rightarrow$ Divisas.
2. [`02_bridgewater_all_weather_regimenes.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/01_marcos_intermercado_y_regimenes/02_bridgewater_all_weather_regimenes.md): Matriz de 4 cuadrantes de Bridgewater Associates (Crecimiento vs. Inflación) y rotación institucional de liquidez.
3. [`03_kritzman_cambios_de_regimen_markov.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/01_marcos_intermercado_y_regimenes/03_kritzman_cambios_de_regimen_markov.md): Modelado cuantitativo de cambios estructurales y turbulencia financiera (Markov Regime Switching).

### Módulo 2: Evidencia Cuantitativa de Estrategias Técnicas y Sizing
4. [`01_moskowitz_pedersen_time_series_momentum.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/02_evidencia_cuantitativa_estrategias/01_moskowitz_pedersen_time_series_momentum.md): Demostración de *Time Series Momentum* en 58 instrumentos globales y asimetría positiva en colas de volatilidad (*positive skewness*).
5. [`02_asness_aqr_value_and_momentum.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/02_evidencia_cuantitativa_estrategias/02_asness_aqr_value_and_momentum.md): Fusión de factores macro y técnicos para optimización de ratio de Sharpe.
6. [`03_man_group_cfm_volatility_targeting_and_trend.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/02_evidencia_cuantitativa_estrategias/03_man_group_cfm_volatility_targeting_and_trend.md): Volatility Targeting (Harvey et al., 2018), calibración de medias móviles EWMAC (Man AHL / Carver) y retornos de +25% en crisis inflacionarias (Neville et al.).
7. [`04_lo_mamaysky_brock_empirical_technical_rules.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/02_evidencia_cuantitativa_estrategias/04_lo_mamaysky_brock_empirical_technical_rules.md): Validación no paramétrica de reglas técnicas (Lo et al. MIT, Brock et al. en 90 años de datos) y variación del Win Rate (35% vs 72%) según régimen.

### Módulo 3: Commodities, Oro y Tasas de Interés
8. [`01_erb_harvey_golden_dilemma_tasas_reales.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/03_commodities_oro_y_tasas/01_erb_harvey_golden_dilemma_tasas_reales.md): Econometría del Oro vs. Tasas de Interés Reales del Tesoro a 10 años (`TIPS` / `DGS10 - Breakeven`).
9. [`02_estrella_mishkin_curva_rendimientos_fed.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/03_commodities_oro_y_tasas/02_estrella_mishkin_curva_rendimientos_fed.md): La pendiente de la curva de rendimientos (2s10s) como predictor del ciclo monetario y del apetito por riesgo.
10. [`03_wgc_kilian_gold_oil_structural_shocks.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/03_commodities_oro_y_tasas/03_wgc_kilian_gold_oil_structural_shocks.md): Modelo GRAM (World Gold Council) y descomposición de shocks de petróleo de Kilian (AER 2009: Oferta vs Demanda Agregada vs Pánico Geopolítico).

### Módulo 4: Microestructura Oficial y Modelos de USD/CLP
11. [`01_bcch_caputo_valdes_tipo_cambio_cobre.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/04_banco_central_chile_y_usdclp/01_bcch_caputo_valdes_tipo_cambio_cobre.md): Cointegración y elasticidad de transmisión del Cobre COMEX al tipo de cambio nominal chileno.
12. [`02_bcch_carreno_cox_carry_trade_forwards.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/04_banco_central_chile_y_usdclp/02_bcch_carreno_cox_carry_trade_forwards.md): Impacto del diferencial de tasas ($\Delta r = \text{TPM} - \text{Fed}$) y la posición neta forward bancaria en la tendencia del USD/CLP.
13. [`03_menkhoff_sarno_fx_volatility_and_lead_lag.md`](file:///C:/Users/bbrav/grupo-analisis-mercado/docs/investigacion_intermarket/04_banco_central_chile_y_usdclp/03_menkhoff_sarno_fx_volatility_and_lead_lag.md): Regímenes de volatilidad cambiaria de Menkhoff-Sarno (JOF 2012), difusión gradual de información (Hong-Stein / Lou-Yan) y matriz de latencias cross-asset (15 min a 2 horas).
