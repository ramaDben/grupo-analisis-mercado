# Ficha Técnica: Modelos Econométricos Estructurales para Commodities (Oro, Petróleo y Cobre)
**Referencias Académicas Principales**:
1. **World Gold Council (2018–2024)**. *Gold Return Attribution Model (GRAM): Methodology and Applications*. WGC Research.
2. **Kilian, Lutz (2009)**. *Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market*. **American Economic Review**, 99(3), 1053–1069.
3. **Kilian, Lutz & Park, Cheolbeom (2009)**. *The Impact of Oil Price Shocks on the U.S. Stock Market*. **International Economic Review**, 50(4), 1267–1287.
4. **Chen, Yu-chin & Rogoff, Kenneth (2003)**. *Commodity Currencies*. **Journal of International Economics**, 60(1), 133–160.
5. **Cashin, Paul; Céspedes, Luis Felipe; Sahay, Ratna (2004)**. *Commodity Currencies and the Real Exchange Rate*. **Journal of Development Economics**, 75(1), 239–268.
6. **Baur, Dirk G. & Lucey, Brian M. (2010)**. *Is Gold a Hedge or a Safe Haven? An Analysis of Stocks, Bonds and Gold*. **The Financial Review**, 45(2), 217–229.
7. **Barsky, Robert B. & Summers, Lawrence H. (1988)**. *Gibson's Paradox and the Gold Standard*. **Journal of Political Economy**, 96(3), 528–550 (Federal Reserve Bank of Chicago / NBER).

---

## 1. El Modelo Multifactorial GRAM (World Gold Council) y la Econometría del Oro

El **Gold Return Attribution Model (GRAM)** del Consejo Mundial del Oro (*World Gold Council*) descompone formalmente los retornos mensuales del oro ($R_{\text{Gold}, t}$) mediante una regresión lineal múltiple por Mínimos Cuadrados Ordinarios (OLS) basada en cuatro pilares teóricos y microeconómicos de oferta/demanda marginal.

```
                               ┌──────────────────────────────────────────────┐
                               │       RETORNO DEL ORO (XAU/USD) R_t          │
                               └──────────────────────┬───────────────────────┘
                                                      │
         ┌────────────────────────┬───────────────────┴───────────────┬────────────────────────┐
         ▼                        ▼                                   ▼                        ▼
┌──────────────────┐    ┌──────────────────┐                ┌──────────────────┐     ┌──────────────────┐
│  1. EXPANSIÓN    │    │   2. RIESGO E    │                │ 3. COSTO DE      │     │  4. MOMENTUM Y   │
│    ECONÓMICA     │    │  INCERTIDUMBRE   │                │    OPORTUNIDAD   │     │      FLUJOS      │
│  (PIB, Consumo,  │    │ (VIX, Spreads,   │                │ (Tasas Reales 10Y│     │  (ETFs, Posición │
│    Joyería)      │    │  Geopolítica GPR)│                │     TIPS, DXY)   │     │    COT COMEX)    │
└──────────────────┘    └──────────────────┘                └──────────────────┘     └──────────────────┘
```

### 1.1 Especificación Matemática del Modelo GRAM

$$R_{\text{Gold}, t} = \alpha + \sum_{k=1}^{K_1} \beta_{1,k} X_{1,k,t}^{\text{Econ}} + \sum_{k=1}^{K_2} \beta_{2,k} X_{2,k,t}^{\text{Risk}} + \sum_{k=1}^{K_3} \beta_{3,k} X_{3,k,t}^{\text{OppCost}} + \sum_{k=1}^{K_4} \beta_{4,k} X_{4,k,t}^{\text{Mom}} + \varepsilon_t$$

Donde los cuatro pilares incorporan las siguientes variables fundamentales:

1. **Expansión Económica ($X^{\text{Econ}}$)**:
   * Crecimiento del PIB global ponderado e ingresos disponibles.
   * Demanda de consumo de joyería en mercados clave (China, India).
   * Demanda tecnológica e industrial de metales preciosos.
   * *Efecto esperado*: $\beta_1 > 0$ (aumenta el piso de demanda a mediano/largo plazo).

2. **Riesgo e Incertidumbre Sistémica ($X^{\text{Risk}}$)**:
   * **VIX**: Volatilidad implícita del S&P 500.
   * **Credit Spreads**: Diferencial de crédito corporativo (TED Spread, High Yield OAS).
   * **GPR Index**: Índice de Riesgo Geopolítico de Caldara e Iacoviello (2018).
   * **Inflación Esperada**: Compensación por inflación a 10 años (*10Y Breakeven Inflation Rate*).
   * *Efecto esperado*: $\beta_2 > 0$ (el oro actúa como activo de convexidad positiva ante eventos de cola / cisnes negros).

3. **Costo de Oportunidad ($X^{\text{OppCost}}$) — *El Driver Cuantitativo Dominante*:**
   * **Tasas de Interés Reales ($\text{TIPS}_{10Y} = y_{10Y} - \pi_{10Y}^e$)**:
     $$\text{Tasa Real} = \text{DGS10} - \text{T10YIE}$$
   * **Índice Dólar (DXY / Broad US Dollar Index)**: Variación en la fortaleza de la divisa de denominación.
   * *Efecto esperado*: $\beta_{\text{TIPS}} \approx -1.2 \text{ a } -1.8$ y $\beta_{\text{DXY}} \approx -0.8 \text{ a } -1.1$.
   * *Evidencia de la Fed de San Francisco / Chicago*: Un incremento sostenido de 100 bps en las tasas reales a 10 años contrae el precio del oro entre un 12% y un 18% en ausencia de crisis sistémica.

4. **Momentum y Flujos Financieros ($X^{\text{Mom}}$)**:
   * Flujos netos mensuales en ETFs respaldados físicamente (GLD, IAU, PHYS).
   * Posicionamiento Neto No Comercial en Futuros COMEX (*Commitment of Traders - COT Managed Money*).
   * *Time Series Momentum* a 12 meses ($R_{t-12 \to t}$).
   * *Efecto esperado*: $\beta_4 > 0$ (persistencia de flujos institucionales y persecución de tendencia).

5. **El Componente Residual ($\varepsilon_t$) y Demanda de Bancos Centrales**:
   * Las compras no registradas de bancos centrales soberanos (PBoC, Banco de Rusia, RBI) y la desdolarización estructural de reservas se manifiestan estadísticamente como una constante positiva $\alpha > 0$ o residuos persistentes en el modelo OLS estándar.

---

## 2. Kilian (2009, AER): Descomposición Estructural del Petróleo (SVAR)

Lutz Kilian demostró que tratar todas las variaciones del precio del petróleo como equivalentes conduce a conclusiones erróneas. Mediante un modelo de **Vectores Autorregresivos Estructurales (SVAR)**, descompone las perturbaciones del crudo en tres shocks estructurales ortogonales con impactos radicalmente opuestos sobre los activos financieros.

### 2.1 El Modelo SVAR de Kilian

El sistema estructural se define en tiempo discreto:

$$A_0 Y_t = \alpha + \sum_{i=1}^p A_i Y_{t-i} + e_t$$

Donde $Y_t$ es un vector $3 \times 1$ compuesto por:
$$Y_t = \begin{bmatrix} \Delta \text{prod}_t \\ \text{rea}_t \\ \text{rpo}_t \end{bmatrix}$$

* $\Delta \text{prod}_t$: Variación porcentual de la producción global de petróleo crudo.
* $\text{rea}_t$: Índice de actividad económica real global de Kilian (derivado de tarifas de flete marítimo seco a granel / *dry cargo bulk freight rates*).
* $\text{rpo}_t$: Logaritmo del precio real del petróleo crudo (deflactado por el CPI de EE.UU.).

### 2.2 Identificación Estructural y Matriz de Cholesky

Asumiendo una estructura recursiva en $A_0^{-1}$ (identificación triangular contemporánea):

$$\begin{bmatrix} e_t^{\Delta \text{prod}} \\ e_t^{\text{rea}} \\ e_t^{\text{rpo}} \end{bmatrix} = \begin{bmatrix} a_{11} & 0 & 0 \\ a_{21} & a_{22} & 0 \\ a_{31} & a_{32} & a_{33} \end{bmatrix} \begin{bmatrix} \varepsilon_t^{\text{Supply}} \\ \varepsilon_t^{\text{Aggregate Demand}} \\ \varepsilon_t^{\text{Oil-Specific Demand}} \end{bmatrix}$$

**Restricciones de exclusión económica impuestas por Kilian**:
1. La producción física global de crudo no reacciona dentro del mismo mes a innovaciones en la demanda global agregada ni al precio del crudo ($a_{12} = 0, a_{13} = 0$).
2. La actividad económica real global no reacciona contemporáneamente a shocks específicos o precautorios del petróleo ($a_{23} = 0$), pero sí a perturbaciones en la oferta física ($a_{21}$).
3. El precio real del petróleo reacciona instantáneamente a los tres shocks ($a_{31}, a_{32}, a_{33} \neq 0$).

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                        TAXONOMÍA DE SHOCKS DE KILIAN (2009)                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 1. SHOCK DE OFERTA PETROLERA (ε_Supply)                                                                      ║
║    • Causa: Cortes de suministro físico por huelgas, sabotaje o decisiones OPEP+.                           ║
║    • Respuesta del Crudo: Alza transitoria y acotada (efecto media vida < 6 meses).                         ║
║    • Impacto Macro / S&P 500: Muy reducido. Las economías modernas absorben el shock vía inventarios.        ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 2. SHOCK DE DEMANDA GLOBAL AGREGADA (ε_Aggregate Demand)                                                     ║
║    • Causa: Expansión sincrónica del ciclo económico mundial (boom manufacturero, infraestructura).          ║
║    • Respuesta del Crudo: Alza muy persistente y de largo plazo en el precio real.                           ║
║    • Impacto en Renta Variable: POSITIVO inicial (S&P 500 sube; el alza del crudo refleja mayor actividad). ║
║    • Impacto en FX: Apreciación de monedas commodity (CAD, AUD, CLP, NOK) vs. USD.                           ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 3. SHOCK DE DEMANDA PRECAUTORIA / ESPECÍFICA (ε_Oil-Specific / Geopolitical)                                ║
║    • Causa: Pánico geopolítico, incertidumbre bélica en Medio Oriente, riesgo de cierre de estrechos.       ║
║    • Respuesta del Crudo: Pico vertical instantáneo impulsado por acumulación preventiva de inventarios.     ║
║    • Impacto Macro / S&P 500: SEVERAMENTE NEGATIVO (contracción económica, estanflación, caída de bolsas).   ║
║    • Impacto en FX y Refugios: Colapso de emergentes, vuelo al Dólar (USD) y al Oro (XAU/USD).               ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

### 2.3 Matriz de Impacto Cross-Asset por Tipo de Shock Petrolero

| Activo / Mercado | Shock de Oferta ($\varepsilon^{\text{Supply}}$) | Shock Demanda Agregada ($\varepsilon^{\text{AggDemand}}$) | Shock Demanda Precautoria ($\varepsilon^{\text{Precautionary}}$) |
| :--- | :--- | :--- | :--- |
| **WTI / Brent** | $\uparrow$ (Transitorio / Moderado) | $\uparrow\uparrow$ (Tendencia Sostenida) | $\uparrow\uparrow\uparrow$ (Pico Explosivo / Spike) |
| **Renta Variable (S&P 500)** | $\leftrightarrow$ (Neutral / Marginal $\downarrow$) | $\uparrow$ (Fase 1: Alcista; Fase 2: Drag tardío) | $\downarrow\downarrow$ (Caída Brusca / Sell-off Estanflacionario) |
| **Tasas del Tesoro (10Y Yield)**| $\leftrightarrow$ (Marginal $\uparrow$) | $\uparrow\uparrow$ (Por mayor crecimiento e inflación) | $\downarrow$ (Vuelo a la calidad / rally de bonos seguros) |
| **Dólar Global (DXY)** | $\leftrightarrow$ (Sin dirección fija) | $\downarrow$ (Apetito por riesgo global) | $\uparrow\uparrow$ (Búsqueda de liquidez y refugio seguro) |
| **Monedas Commodity (CLP/CAD/AUD)**| $\leftrightarrow$ (Neutral) | $\uparrow\uparrow$ (Fuerte apreciación por términos de intercambio) | $\downarrow\downarrow$ (Depreciación severa por aversión al riesgo) |
| **Oro (XAU/USD)** | $\leftrightarrow$ (Neutral) | $\leftrightarrow$ (Presión mixta: tasas suben) | $\uparrow\uparrow$ (Máxima prima por riesgo geopolítico) |

---

## 3. Transmisión del Cobre ("Dr. Copper") a Monedas Exportadoras y Ciclo Global

El cobre refinado (`HG` en COMEX / `CA` en LME) es el barómetro líder por excelencia de la producción manufacturera global debido a su intensiva utilización en infraestructura eléctrica, construcción, automoción, electrónica y bienes de capital.

```
                    ┌──────────────────────────────────────────────┐
                    │            PRECIO DEL COBRE (COMEX/LME)      │
                    │         "Doctor Copper" (Anticipa 3-6m)      │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                                                   ▼
┌────────────────────────────────────────┐          ┌────────────────────────────────────────┐
│     CANAL DE ACTIVIDAD GLOBAL          │          │      CANAL TÉRMINOS DE INTERCAMBIO     │
│   (Global Manufacturing PMI / China)   │          │         (Commodity Currencies)         │
└──────────────────┬─────────────────────┘          └──────────────────┬─────────────────────┘
                   │                                                   │
                   ▼                                                   ▼
┌────────────────────────────────────────┐          ┌────────────────────────────────────────┐
│  • PMI > 50: Expansión de pedidos      │          │  • Chile (CLP): Elasticidad β ≈ 0.50   │
│  • PMI < 50: Contracción manufacturera │          │  • Australia (AUD): Proxy China / ToT  │
│  • Anticipa rotación de materias primas│          │  • Canadá (CAD): Mix Cobre + Petróleo  │
└────────────────────────────────────────┘          └────────────────────────────────────────┘
```

### 3.1 El Modelo de Tipos de Cambio de Commodities (Chen & Rogoff, 2003; Cashin et al., 2004)

Chen y Rogoff demostraron que para economías con canastas exportadoras dominadas por materias primas, el tipo de cambio real de equilibrio ($q_t$) sigue una relación de cointegración de largo plazo determinada por los Términos de Intercambio Reales ($\text{ToT}_t$):

$$\ln(q_t) = \alpha + \beta \ln(\text{ToT}_t) + \gamma (r_t - r_t^*) + \varepsilon_t$$

Donde para el caso chileno (Caputo, Núñez y Valdés, BCCh):
$$\Delta \ln(\text{USD/CLP}_t) = \mu - \beta_1 \Delta \ln(\text{Cobre}_t) + \beta_2 \Delta \ln(\text{DXY}_t) - \beta_3 (\text{TPM}_t - \text{FedFunds}_t) + \omega_t$$

### 3.2 Tabla Comparativa de Sensibilidad por Divisa

| Divisa Exportadora | Commodity Principal | Elasticidad Directa Estimada ($\beta$) | Dependencia de China (% Exp.) | Mecanismo de Ajuste Predominante |
| :--- | :--- | :--- | :--- | :--- |
| **Peso Chileno (CLP)** | Cobre (`HG` / ~55% de exportaciones) | $\beta \approx 0.40 - 0.55$ | Muy Alta (~68% del cobre físico a China) | Liquidación directa de divisas mineras + Cuenta Corriente |
| **Dólar Australiano (AUD)**| Mineral de Hierro (`Iron Ore`) + Cobre | $\beta \approx 0.35 - 0.45$ | Alta (~35% de exportaciones totales) | Canal financiero de liquidez asiática (Proxy China beta) |
| **Dólar Canadiense (CAD)**| Petróleo Crudo (WTI/WCS) + Metales | $\beta_{\text{Oil}} \approx 0.30, \beta_{\text{Metals}} \approx 0.20$ | Baja-Media (Dominado por ciclo comercial EE.UU.) | Flujos transfronterizos NAFTA / USMCA |

### 3.3 El Cobre como Indicador Líder del PMI Global
* **Propiedad de Liderazgo Temporal**: Las variaciones interanuales del precio del cobre ($\Delta\% \text{Copper}_{t}$) lideran el **JPMorgan Global Manufacturing PMI** con un horizonte de **3 a 6 meses** de anticipación ($R^2 \approx 0.52$).
* **Fórmula del Indicador Sintético de Impulso**:
  $$\text{Copper Momentum Indicator (CMI)}_t = \frac{\text{Cobre}_t - \text{SMA}_{50}(\text{Cobre})}{\text{ATR}_{20}(\text{Cobre})}$$
  * Si $\text{CMI} > +2.0$ de forma sostenida: Expansión acelerada del ciclo de manufactura global.
  * Si $\text{CMI} < -2.0$: Entrada inminente en ciclo de desacumulación de inventarios (*destocking*) o recesión industrial.

---

## 4. Reglas Operativas Cuantitativas para el Trading Desk

### 4.1 Regla para XAU/USD (Oro) — *Filtro GRAM de Tasas Reales y Riesgo*

```
                           ┌──────────────────────────────────────────────┐
                           │            CONDICIÓN DE APERTURA             │
                           │               SESGO EN XAU/USD               │
                           └──────────────────────┬───────────────────────┘
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
┌────────────────────────────────────────┐                        ┌────────────────────────────────────────┐
│             SESGO ALCISTA              │                        │             SESGO BAJISTA              │
│  • TIPS 10Y a la baja (Tasa Real cae)  │                        │  • TIPS 10Y al alza (Tasa Real sube)   │
│  • DXY retrocediendo o bajo EMA 50     │                        │  • DXY en rally o sobre EMA 50         │
│  • Flujos ETF / COT en expansión       │                        │  • VIX comprimido (< 14) sin riesgo    │
└──────────────────┬─────────────────────┘                        └──────────────────┬─────────────────────┘
                   │                                                                 │
                   ▼                                                                 ▼
┌────────────────────────────────────────┐                        ┌────────────────────────────────────────┐
│ EJECUCIÓN: Comprar retrocesos en H1    │                        │ EJECUCIÓN: Prohibido comprar breakouts │
│ a niveles clave de soporte / EMA 20-50 │                        │ Buscar ventas tácticas intradía        │
└────────────────────────────────────────┘                        └────────────────────────────────────────┘
```

1. **Setup "Real Rate Drop + Safe Haven" (Long Swing)**:
   * **Condición Macro**: $\Delta \text{TIPS}_{10Y} < -5 \text{ bps}$ en la semana Y $\text{DXY} < \text{EMA}_{50}(\text{D1})$.
   * **Confirmación de Riesgo**: VIX $> 20$ o escalada en el índice de riesgo geopolítico.
   * **Gatillo Técnico en MT5 (H1)**: Esperar pullback al retroceso 38.2%–50% Fibonacci de la última onda impulsiva con confirmación de vela envolvente alcista sobre EMA 20.
   * **Stop Loss**: $1.5 \times \text{ATR}_{14}(\text{H1})$ por debajo del mínimo de oscilación.
   * **Take Profit**: $3.0 \times \text{ATR}_{14}(\text{H1})$ o extensión 161.8% Fibonacci.

2. **Filtro de Desconexión Geopolítica**:
   * Si las tasas reales suben pero el oro ignora la caída y hace nuevos máximos: **Presencia de compras soberanas de Bancos Centrales o shock de demanda precautoria**. *Prohibido ponerse corto (short) contra la tendencia.*

---

### 4.2 Regla para WTI / Brent — *Filtro de Shocks de Kilian*

```
¿El Petróleo sube con fuerza?
 │
 ├──► ¿S&P 500 sube Y Cobre sube Y Tasas suben?
 │     └──► RÉGIMEN: SHOCK DE DEMANDA AGREGADA
 │           └──► ACCIÓN: Seguir tendencia alcista en WTI, Renta Variable y Divisas Commodity.
 │
 ├──► ¿S&P 500 cae Y VIX explota (>25) Y Dólar sube?
 │     └──► RÉGIMEN: SHOCK DE DEMANDA PRECAUTORIA (GEOPOLÍTICO)
 │           └──► ACCIÓN: Comprar WTI con trailing stop ceñido; Comprar XAUUSD; VENDER Renta Variable y Divisas Emergentes.
 │
 └──► ¿El alza ocurre por titular de OPEP pero Cobre y Fletes planos?
       └──► RÉGIMEN: SHOCK DE OFERTA TRANSITORIO
             └──► ACCIÓN: Buscar ventas en resistencias extremas (Fade the news).
```

* **Gestión de Riesgo en Shocks Precautorios**:
  * Los spikes por tensión bélica tienen colas de volatilidad extremas (*positive skewness*). Reducir el apalancamiento al 50% del tamaño habitual y usar órdenes Stop garantizadas en MT5.

---

### 4.3 Regla para USD/CLP — *Intermarket Arbitrage & Divergencia Cobre/DXY*

1. **Lectura Matutina de Parámetros (08:00 a 08:30 CLT)**:
   * Extraer cotización de `COBRE_HG` (COMEX) y variación diaria $\% \Delta \text{HG}$.
   * Extraer índice `DXY` y diferencial de tasas $(\text{TPM} - \text{FedFunds})$.

2. **El Setup de Divergencia Cobre vs. USD/CLP (Venta de Alta Probabilidad)**:
   * **Gatillo Fundamental**: $\% \Delta \text{COBRE} > +1.5\%$ en la sesión europea/COMEX matutina Y $\Delta \text{DXY} \le 0.0\%$.
   * **Ineficiencia Local**: USD/CLP abre plano o subiendo en Santiago por inercia o descalce bancario.
   * **Ejecución Técnica (M15 / H1)**: Venta (*Short*) inmediata en la apertura de la bolsa local (08:30–09:00 CLT) buscando el testeo de la zona de soporte S1 del punto pivote diario.
   * **Stop Loss**: 6 pesos chilenos sobre el máximo intradía de apertura.
   * **Target**: 12 a 18 pesos chilenos a favor de la tendencia (Riesgo:Recompensa $1:2$ a $1:3$).

3. **Condición de Veto Total a Compras Swing en USD/CLP**:
   * Si el Cobre rompe al alza un rango de consolidación semanal con volumen institucional $\rightarrow$ **Estrictamente prohibido operar posiciones largas (Long) tipo swing en USD/CLP**.

---

## 5. Referencias Académicas y Fuentes de Datos

* **Barsky, R. B., & Summers, L. H. (1988)**. *Gibson's Paradox and the Gold Standard*. Journal of Political Economy, 96(3), 528–550.
* **Baur, D. G., & Lucey, B. M. (2010)**. *Is gold a hedge or a safe haven? An analysis of stocks, bonds and gold*. The Financial Review, 45(2), 217–229.
* **Baur, D. G., & McDermott, T. K. (2010)**. *Is gold a safe haven? International evidence*. Journal of Banking & Finance, 34(8), 1886–1898.
* **Caldara, D., & Iacoviello, M. (2018)**. *Measuring Geopolitical Risk*. American Economic Review, 112(4), 1194–1225.
* **Caputo, R., Núñez, M., & Valdés, R. (2007)**. *Análisis del Tipo de Cambio en la Práctica*. Documento de Trabajo N° 434, Banco Central de Chile.
* **Cashin, P., Céspedes, L. F., & Sahay, R. (2004)**. *Commodity currencies and the real exchange rate*. Journal of Development Economics, 75(1), 239–268.
* **Chen, Y. C., & Rogoff, K. (2003)**. *Commodity currencies*. Journal of International Economics, 60(1), 133–160.
* **Kilian, L. (2009)**. *Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market*. American Economic Review, 99(3), 1053–1069.
* **Kilian, L., & Park, C. (2009)**. *The Impact of Oil Price Shocks on the U.S. Stock Market*. International Economic Review, 50(4), 1267–1287.
* **World Gold Council (2018–2024)**. *Gold Return Attribution Model (GRAM)*. WGC Quantitative Research Series.
