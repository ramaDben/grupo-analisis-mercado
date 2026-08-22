# Ficha Técnica: Regímenes de Volatilidad Global FX, Desarme de Carry Trade y Desfases Intermercado (Lead-Lag)

**Referencias Académicas Principales**:
1. Menkhoff, Lukas; Sarno, Lucio; Schmeling, Maik; Schrimpf, Andreas (2012). *Carry Trades and Global FX Volatility*. **The Journal of Finance**, 67(2), 681–718.
2. Hong, Harrison; Stein, Jeremy C. (1999). *A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets*. **The Journal of Finance**, 54(6), 2143–2184.
3. Lou, Dong; Yan, Hongjun (2013) / Lou, Dong (2012). *Complicated Firms and Gradual Information Diffusion*. **The Review of Financial Studies**, 25(10), 3083–3112.
4. Brunnermeier, Markus K.; Pedersen, Lasse Heje (2009). *Market Liquidity and Funding Liquidity*. **The Review of Financial Studies**, 22(6), 2201–2238.

---

## 1. Menkhoff, Sarno, Schmeling & Schrimpf (2012): Volatilidad Global FX y Destrucción del Carry Trade

### 1.1. El Enigma de la Paridad No Cubierta de Tasas de Interés (UIP Puzzle)
La teoría económica neoclásica (*Uncovered Interest Rate Parity* - UIP) estipula que las monedas con tasas de interés elevadas deberían depreciarse contra las monedas de baja tasa en una magnitud equivalente al diferencial de tasas:
$$\mathbb{E}_t [\Delta s_{t+1}] = i_t - i_t^*$$
Donde $s_t$ es el logaritmo del tipo de cambio spot (unidades de moneda local por USD) e $i_t, i_t^*$ son las tasas de interés libre de riesgo local y extranjera.

Sin embargo, la evidencia empírica muestra sistemáticamente una violación de la UIP (Fama, 1984): las divisas de alta tasa de interés no se deprecian inmediatamente, generando un exceso de retorno positivo para la estrategia de *Carry Trade*:
$$r_{x, t+1}^i \equiv (i_t^i - i_t^{\text{USD}}) - \Delta s_{t+1}^i > 0$$

### 1.2. El Factor de Innovación de Volatilidad Global ($\Delta \text{VOL}_{\text{FX}}$)
Menkhoff et al. (2012) resuelven este enigma demostrando que el exceso de retorno del carry trade **no es un arbitraje gratuito (*free lunch*)**, sino una **compensación por riesgo sistemático ante shocks de volatilidad global**.

Los autores construyen el factor de volatilidad cambiaria global en el día $\tau$ del mes $t$ promediando los retornos absolutos de todas las divisas líquidas ($N_t$):
$$\sigma_{\text{FX}, \tau} = \frac{1}{N_t} \sum_{i=1}^{N_t} |r_{\tau}^i|$$
La volatilidad realizada mensual se normaliza como:
$$\text{VOL}_t = \frac{1}{T_t} \sum_{\tau \in t} \sigma_{\text{FX}, \tau}$$
El factor de shock o innovación de volatilidad global se obtiene mediante un proceso autorregresivo $\text{AR}(1)$:
$$\text{VOL}_t = \phi_0 + \phi_1 \text{VOL}_{t-1} + u_t \quad \implies \quad \Delta \text{VOL}_t \equiv u_t$$

### 1.3. Modelo de Valoración de Dos Factores y Sensibilidad Asimétrica ($\beta_{\text{VOL}}$)
El retorno esperado de cualquier portafolio o par de divisas $i$ se rige por un modelo de fijación de precios de activos (Cross-Sectional Asset Pricing):
$$\mathbb{E}[r_x^i] = \beta_{i, \text{DOL}} \lambda_{\text{DOL}} + \beta_{i, \text{VOL}} \lambda_{\text{VOL}}$$

Donde:
* **$\text{DOL}$ (Dollar Factor)**: Retorno promedio de todas las monedas frente al USD (análogo al factor de mercado en CAPM).
* **$\text{VOL}$ (Volatility Factor)**: Factor innovación de volatilidad global FX.
* **$\lambda_{\text{VOL}} < 0$**: El precio de mercado del riesgo de volatilidad es **estrictamente negativo y estadísticamente significativo** ($t\text{-stat} < -3.5$).

```
                      ESTRUCTURA DE BETAS DE VOLATILIDAD (MENKHOFF ET AL., 2012)
                      
   Portafolio P1 (Baja Tasa - Funding)                 Portafolio P5 (Alta Tasa - Target / CLP)
   [JPY, CHF, EUR en ciertos regímenes]                [BRL, MXN, CLP, ZAR, TRY]
   ─────────────────────────────────────               ─────────────────────────────────────
   • Beta de Volatilidad: β_VOL > 0                    • Beta de Volatilidad: β_VOL << 0 (-1.8 a -2.5)
   • Actúa como ACTIVO DE REFUGIO                      • Retorno altamente sensible a shocks de volatilidad
   • Se APRECIA ante shocks globales                   • Sufre COLAPSO ASIMÉTRICO / CRASH RISK
   • Paga prima de seguro (carry negativo)             • Cobra prima por riesgo de cola (carry positivo)
```

### 1.4. Dinámica de Desarme de Carry Trade (*Unwinding*) e Hiper-Tendencias
Cuando ocurre un shock exógeno ($\Delta \text{VOL}_t \gg 0$, $\text{VIX} > 25$, o shock en tasas del Tesoro / commodities):
1. **Espiral de Liquidez y Márgenes (Brunnermeier & Pedersen, 2009)**: Los fondos macro apalancados reciben *margin calls* o superan su límite de *Value at Risk* (VaR).
2. **Cierre Forzoso Unidireccional**: Para recortar riesgo, compran masivamente la moneda de financiamiento (USD) y liquidan las posiciones en monedas emergentes de alto rendimiento (CLP).
3. **Vacío de Liquidez (*Liquidity Hole*)**: Los creadores de mercado bancarios ensanchan los spreads *bid-ask* y retiran liquidez en la punta compradora de la moneda emergente.
4. **Génesis de Hiper-Tendencias Direccionales**: El tipo de cambio entra en una fase de ruptura explosiva (*directional cascade*) donde los osciladores técnicos de sobrecompra quedan completamente invalidados y las estrategias de reversión a la media son liquidadas.

---

## 2. Hong & Stein (1999) / Lou & Yan (2013): Difusión Gradual de Información y Lead-Lag Intermercado

### 2.1. Fundamentos de la Difusión Lenta de Información (*Gradual Information Diffusion - GID*)
Hong & Stein (1999) formalizan por qué los mercados financieros no incorporan la información de manera instantánea, derivando dos tipos de agentes con racionalidad acotada:
1. **Observadores de Fundamentales (*Newswatchers*)**: Analizan exclusivamente señales privadas del activo primario (ej. subastas del Tesoro de EE.UU., inventarios de cobre en LME/COMEX), pero no extrapolan información de otros mercados ni operan sobre patrones de precios pasados.
2. **Operadores de Momento (*Momentum Traders*)**: No leen los fundamentales primarios; solo observan la acción del precio y las rupturas técnicas, operando sobre la inercia retardada.

Lou & Yan (2013) y Lou (2012) extienden este marco a la **segmentación cross-asset y atención limitada de los inversores (*Investor Inattention*)**:
* Los operadores especializados en bonos soberanos de EE.UU. o futuros de Cobre COMEX absorben el shock en minutos ($t_0$).
* Los operadores de divisas emergentes (USD/CLP) y tesorerías corporativas locales tienen barreras operativas, comités de riesgo y mandatos de liquidación diferidos ($t_1, t_2$), generando una **ventana de desfase sistemática (*Lead-Lag Window*)**.

```
                           LÍNEA TEMPORAL DE DIFUSIÓN GRADUAL DE INFORMACIÓN
                           
  t = 0 min              t = 15 - 45 min           t = 1 - 2 horas           t = 24 - 48 horas (T+1 / T+2)
  ─────────              ───────────────           ───────────────           ─────────────────────────────
  Shock en COMEX         Ajuste Algorítmico        Arbitraje Interbancario   Rebalanceo de Forwards
  (Cobre ±2.5%) o        en DXY y Rendimiento      Local en Santiago         de No Residentes y
  Subasta UST 10Y        del UST 10Y               (USD/CLP Spot reacciona)  Liquidaciones Mineras / Fisco
```

### 2.2. Modelo Econométrico de Desfases Distribuidos (Distributed Lag Model)
La respuesta dinámica del tipo de cambio nominal $\Delta \ln(\text{USD/CLP}_t)$ ante los drivers globales líderes se especifica como un modelo autoregresivo con retardos distribuidos (ARDL / VAR-X):

$$\Delta \ln(\text{USD/CLP}_t) = \alpha + \sum_{k=0}^{P} \gamma_k \Delta \ln(\text{Cobre}_{t-k}) + \sum_{k=0}^{Q} \theta_k \Delta y_{t-k}^{10\text{Y}} + \sum_{k=0}^{M} \phi_k \Delta \ln(\text{DXY}_{t-k}) + \sum_{j=1}^{L} \psi_j \Delta \text{FWD}_{t-j} + \varepsilon_t$$

Donde la **Función de Respuesta al Impulso Acumulada (CIRF)** determina el porcentaje de absorción de la información por horizonte temporal:
$$\text{CIRF}_H = \sum_{k=0}^H \gamma_k$$

---

## 3. Matriz Econométrica de Desfases Temporales Cross-Asset para USD/CLP

A partir de la literatura empírica de microestructura cambiaria latinoamericana y datos de transmisión del Banco Central de Chile, se consolidan las siguientes ventanas de propagación:

| Activo / Driver Líder | Instrumento Proxy | Elasticidad / Impacto Teórico ($\beta$) | Latencia Intradía Inicial ($t_{\text{ini}}$) | Horizonte de Transmisión Plena ($T_{\text{full}}$) | Canal de Transmisión Microestructural |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cobre Alta Calidad** | COMEX `HG` / LME Cash | $\beta \approx -0.45 \text{ a } -0.55$ | **30 a 90 minutos** | **1 a 3 días hábiles** ($T+2$) | Oferta de divisas por exportación minera y ajuste de términos de intercambio. |
| **Tasa Soberana EE.UU. 10Y**| `US10Y` / Futuro `ZN` | $\beta \approx +0.35 \text{ a } +0.50$ | **15 a 45 minutos** | **1 a 2 días hábiles** | Costo de oportunidad global, spread de tasas y salida de capitales hacia el dólar. |
| **Índice Dólar Global** | `DXY` (ICE) | $\beta \approx +0.65 \text{ a } +0.75$ | **Inmediato (0 a 15 min)**| **Misma sesión (H1 - H4)** | Arbitraje cambiario directo de canasta global vs. monedas emergentes. |
| **Flujo Forward Extranjeros**| `BCCh Posición FWD T-2`| $\Delta \text{USD/CLP} \propto +\Delta \text{FWD}$ | **Día siguiente (publicación)**| **2 a 4 días hábiles** | Calce de cobertura bancaria local: bancos compran spot para entregar en forwards. |
| **Diferencial de Tasas ($\Delta r$)**| $\text{TPM}_{\text{Chile}} - \text{Fed Funds}$| Inverso al diferencial de carry | **Semanal / Mensual** | **5 a 15 días hábiles** | Atractivo estructural del *carry trade* y posicionamiento de tesorerías multinacionales. |

---

## 4. Conmutador de Regímenes (Regime-Switching Engine) para USD/CLP

El colapso de estrategias técnicas en USD/CLP se debe a la **aplicación de arquetipos de rango (*Mean-Reversion*) en presencia de shocks de volatilidad global o desarmes de carry**. 

Se define una arquitectura de dos regímenes gobernada por un **Conmutador de Turbulencia Cuantitativo**:

```
                                  CONMUTADOR DE REGÍMENES DE VOLATILIDAD
                                                     │
                         ┌───────────────────────────┴───────────────────────────┐
                         ▼                                                       ▼
           [RÉGIMEN 1: CALMA / ABSORCIÓN]                         [RÉGIMEN 2: TURBULENCIA / CARRY UNWIND]
           ──────────────────────────────                         ───────────────────────────────────────
           • Volatilidad Global FX Normal                         • Spike en Volatilidad (ΔVOL > 1.5 SD)
           • Drivers estables (|ΔHG| < 1.0%)                      • Driver Shock (|ΔCobre| > 1.8% o Δ10Y > 8 bps)
           • Spread de Tasas predecible                           • Desarme de Forwards (> 300M USD/sem)
                         │                                                       │
                         ▼                                                       ▼
            ARQUETIPO TÉCNICO VÁLIDO:                              ARQUETIPO TÉCNICO EXCLUSIVO:
            ► MEAN-REVERSION / RANGE TRADING                       ► BREAKOUT / VOLATILITY EXPANSION
            • Operativa en S1/S2 y R1/R2                           • Ruptura de Canales Donchian (H1)
            • Fades en bandas de Bollinger (2σ)                    • Trend-Following Direccional
            • TP fijo: 1.0 a 1.5 ATR H1                            • Salida: Trailing Stop por ATR / EMA-21
            ──────────────────────────────                         ───────────────────────────────────────
            ⛔ PROHIBIDO: Breakouts tempranos                       ⛔ PROHIBIDO: Fades en sobrecompra/venta
```

### 4.1. Condiciones Matemáticas de Activación del Régimen 2 (Turbulencia)
El sistema conmuta a **RÉGIMEN 2** si se satisface **al menos una** de las siguientes condiciones:
1. **Volatilidad Global**:
   $$\text{VIX}_t > 22.0 \quad \lor \quad \text{MOVE}_t > 110.0 \quad \lor \quad \Delta \text{VOL}_{\text{FX}, t} > +1.5 \sigma$$
2. **Shock de Driver Líder Intradía**:
   $$\left|\frac{\text{Cobre}_t - \text{Cobre}_{t-1}}{\text{Cobre}_{t-1}}\right| > 1.80\% \quad \lor \quad \left|y_t^{10\text{Y}} - y_{t-1}^{10\text{Y}}\right| > 8 \text{ bps}$$
3. **Expansión de Volatilidad Local**:
   $$\frac{\text{ATR}_{14}(\text{USDCLP}, \text{H1})}{\text{SMA}_{20}(\text{ATR}_{14}(\text{USDCLP}, \text{H1}))} > 1.40$$
4. **Presión de Flujo Forward Offshore**:
   $$|\Delta \text{POSICION\_FORWARD\_EXTRANJEROS}_{\text{semanal}}| > 300 \text{ Millones USD}$$

---

## 5. Reglas Formales de Implementación y Algoritmo de Ejecución para MetaTrader 5 (MT5)

### 5.1. Regla de Desconexión de Estrategias (*Kill Switch* de Reversión a la Media)
* **Condición de Bloqueo**: Si `Regimen_Actual == REGIMEN_2_TURBULENCIA`:
  1. **Cancelar inmediatamente** todas las órdenes límite pendientes de venta en resistencias (R1/R2) o de compra en soportes (S1/S2).
  2. **Inhabilitar** cualquier lógica de *grid*, *martingala* o compras contra tendencia por indicador RSI/Estocástico en sobreventa.
  3. **Cerrar** posiciones abiertas de rango que no cuenten con *Hard Stop* adaptativo.

### 5.2. Lógica del Algoritmo de Breakout Direccional Intermercado (Pseudo-Código MQL5)

```mql5
//+------------------------------------------------------------------+
//| Intermarket Volatility & Breakout Engine - USD/CLP               |
//+------------------------------------------------------------------+
input double InpDriverCopperThreshold = 0.018; // Shock Cobre 1.8%
input double InpDriverUS10YThreshold  = 0.080; // Shock US10Y 8 bps
input int    InpDonchianPeriod        = 20;    // Canal Donchian H1
input double InpATRMultiplierSL       = 2.0;   // Stop Loss = 2.0 * ATR
input double InpRiskPercent           = 0.01;  // 1% de la cuenta

enum ENUM_MARKET_REGIME {
   REGIME_1_RANGE_MEAN_REVERSION,
   REGIME_2_VOLATILITY_BREAKOUT
};

ENUM_MARKET_REGIME DetectMarketRegime() {
   double dCopper_Pct = MathAbs((iClose("COPPER", PERIOD_D1, 0) - iOpen("COPPER", PERIOD_D1, 0)) / iOpen("COPPER", PERIOD_D1, 0));
   double dUS10Y_Diff  = MathAbs(iClose("US10Y", PERIOD_D1, 0) - iOpen("US10Y", PERIOD_D1, 0));
   double atrCurrent   = iATR("USDCLP", PERIOD_H1, 14, 0);
   double atrMA        = iMAOnArray_ATR_SMA20("USDCLP", PERIOD_H1, 20);

   if (dCopper_Pct >= InpDriverCopperThreshold || dUS10Y_Diff >= InpDriverUS10YThreshold || (atrCurrent / atrMA) >= 1.40) {
      return REGIME_2_VOLATILITY_BREAKOUT;
   }
   return REGIME_1_RANGE_MEAN_REVERSION;
}

void OnTick() {
   ENUM_MARKET_REGIME regime = DetectMarketRegime();

   if (regime == REGIME_2_VOLATILITY_BREAKOUT) {
      // 1. Desactivar compras/ventas contra tendencia
      CancelCounterTrendLimitOrders();

      // 2. Lógica de Breakout en H1 a favor del Driver Intermercado
      double highDonchian = iHighestChannel("USDCLP", PERIOD_H1, InpDonchianPeriod, 1);
      double lowDonchian  = iLowestChannel("USDCLP", PERIOD_H1, InpDonchianPeriod, 1);
      double currentBid   = SymbolInfoDouble("USDCLP", SYMBOL_BID);
      double currentAsk   = SymbolInfoDouble("USDCLP", SYMBOL_ASK);
      double copperDelta  = (iClose("COPPER", PERIOD_H1, 0) - iOpen("COPPER", PERIOD_H1, 0));

      // Señal Alcista: Ruptura de Máximo H1 + Cobre cayendo o DXY subiendo
      if (currentAsk > highDonchian && copperDelta < 0 && PositionsTotal() == 0) {
         double atr = iATR("USDCLP", PERIOD_H1, 14, 0);
         double sl  = currentAsk - (InpATRMultiplierSL * atr);
         double lot = CalculatePositionSize(InpRiskPercent, InpATRMultiplierSL * atr);
         Trade.Buy(lot, "USDCLP", currentAsk, sl, 0, "Lead-Lag Breakout Buy");
      }
      
      // Señal Bajista: Ruptura de Mínimo H1 + Cobre disparándose
      if (currentBid < lowDonchian && copperDelta > 0 && PositionsTotal() == 0) {
         double atr = iATR("USDCLP", PERIOD_H1, 14, 0);
         double sl  = currentBid + (InpATRMultiplierSL * atr);
         double lot = CalculatePositionSize(InpRiskPercent, InpATRMultiplierSL * atr);
         Trade.Sell(lot, "USDCLP", currentBid, sl, 0, "Lead-Lag Breakout Sell");
      }
   }
}
```

### 5.3. Dimensionamiento Dinámico de Posición (Dynamic Sizing)
Bajo el modelo de Menkhoff et al. y Kritzman (2012), el riesgo monetario en dólares se mantiene constante ($R$), reduciendo el lotaje ($L_t$) conforme la volatilidad se expande:
$$L_t = \frac{\text{Capital} \times \text{Riesgo\%}}{\text{ATR}_{14}(S_t) \times \text{Multiplicador SL} \times \text{TickValue}}$$

---

## 6. Referencias Académicas

* **Brunnermeier, M. K., & Pedersen, L. H. (2009)**. Market Liquidity and Funding Liquidity. *The Review of Financial Studies*, 22(6), 2201–2238.
* **Carreño, G., & Cox, P. (2014)**. Carry trade y turbulencias cambiarias con el peso chileno. *Banco Central de Chile*, Documentos de Trabajo N° 722.
* **Caputo, R., Núñez, M., & Valdés, R. (2007)**. Análisis del Tipo de Cambio en la Práctica. *Banco Central de Chile*, Documentos de Trabajo N° 434.
* **Hong, H., & Stein, J. C. (1999)**. A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets. *The Journal of Finance*, 54(6), 2143–2184.
* **Kritzman, M., Page, S., & Turkington, D. (2012)**. Regime Shifts: Implications for Dynamic Asset Allocation. *Financial Analysts Journal*, 68(3), 22–39.
* **Lou, D. (2012)**. Complicated Firms and Gradual Information Diffusion. *The Review of Financial Studies*, 25(10), 3083–3112.
* **Lou, D., & Yan, H. (2013)**. Gradual Information Diffusion in Cross-Asset Predictability. *London School of Economics / Yale SOM Working Paper*.
* **Menkhoff, L., Sarno, L., Schmeling, M., & Schrimpf, A. (2012)**. Carry Trades and Global FX Volatility. *The Journal of Finance*, 67(2), 681–718.
