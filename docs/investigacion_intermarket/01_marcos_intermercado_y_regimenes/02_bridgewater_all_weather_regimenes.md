# Ficha Técnica: El Marco de Regímenes Macroeconómicos de Bridgewater (All Weather)
**Referencia Institucional**: Dalio, Ray; Prince, Bob; Jensen, Greg (Bridgewater Associates, 2012-2015). *The All Weather Story: How Bridgewater Created Risk Parity and Economic Regime Allocation*.

---

## 1. Tesis Fundamental

Los precios de los activos descuentan el consenso del mercado sobre el futuro. Por lo tanto, **los grandes movimientos de precios no ocurren por los datos absolutos, sino por las *sorpresas* económicas (diferencia entre el dato oficial publicado y lo que el mercado esperaba)**.

El universo macroeconómico se divide en dos grandes fuerzas independientes:
1. **Crecimiento Económico Real (Output / PIB / Imacec)**: $\Delta Y$
2. **Inflación (Precios / IPC / PCE / Materias Primas)**: $\Delta \pi$

---

## 2. La Matriz de 4 Cuadrantes de Dalio

```
                       INFLACIÓN AL ALZA (Sorpresa +)
                                    ▲
                                    │
            CUADRANTE 2             │            CUADRANTE 1
         [SHOCK ESTANFLACIONARIO]   │     [SOBRECALENTAMIENTO / REFLACIÓN]
                                    │
      • Oro (XAU/USD)               │  • Commodities (Petróleo, Cobre)
      • Bonos Indexados (TIPS)      │  • Acciones de Valor / Energía
      • USD/CLP Alcista             │  • Divisas Productoras
                                    │
 ◄──────────────────────────────────┼──────────────────────────────────►
  CRECIMIENTO A LA BAJA             │             CRECIMIENTO AL ALZA
      (Sorpresa -)                  │                 (Sorpresa +)
                                    │
            CUADRANTE 3             │            CUADRANTE 4
            [RECESIÓN / DEFENSIVO]  │     [GOLDILOCKS / DESINFLACIÓN]
                                    │
      • Bonos Soberanos Nominales   │  • Acciones Tecnológicas (US100)
      • Dólar como Refugio Líquido  │  • Acciones de Crecimiento
      • Venta de Cobre e Índices    │  • Carry Trade en Divisas
                                    │
                                    ▼
                      INFLACIÓN A LA BAJA (Sorpresa -)
```

---

## 3. Mapeo de Activos por Cuadrante

| Cuadrante | Entorno Macroeconómico | Activos Ganadores (*Outperformers*) | Activos Perdedores (*Underperformers*) |
| :--- | :--- | :--- | :--- |
| **C1: Reflación** | Crecimiento $\uparrow$, Inflación $\uparrow$ | Petróleo (`Brent`/`WTI`), Cobre COMEX, Renta Variable Cíclica | Bonos soberanos a largo plazo (pérdida de capital) |
| **C2: Estanflación** | Crecimiento $\downarrow$, Inflación $\uparrow$ | **Oro (`XAU/USD`)**, TIPS, Divisas refugio | Renta variable en general, bonos nominales |
| **C3: Desaceleración / Recesión** | Crecimiento $\downarrow$, Inflación $\downarrow$ | Bonos soberanos (Tasas caen fuertemente), Dólar líquido | Commodities industriales (Cobre se desploma), Acciones |
| **C4: Expansión No Inflacionaria (Goldilocks)** | Crecimiento $\uparrow$, Inflación $\downarrow$ | **Tecnología (`US100`)**, S&P 500, *Carry trade* en emergentes | Oro (pierde atractivo de cobertura), Volatilidad |

---

## 4. Traducción Operativa al Trading Intradía y Swing

### A. Condicionamiento de la Dirección por Cuadrante
* Cuando `data central/latest_drivers.json` detecta **Cuadrante 2 (Estanflación)** (ej. Petróleo sobre $90 con Imacec desacelerando):
  * **Oro (`XAUUSD`)**: Solo se buscan compras técnicas en soporte (H1). Se anula cualquier señal de venta contratendencia.
  * **USD/CLP**: Sesgo alcista dominante; el peso sufre por menor crecimiento local e inflación de costos importados.

* Cuando el mercado transita a **Cuadrante 4 (Goldilocks)** (Tasas 10Y cediendo con actividad sólida):
  * **Nasdaq 100 (`US100`)**: Se activan estrategias de *Momentum* y *Trend-Following* en temporalidades 15M/1H.

---

## 5. Algoritmo de Decisión de Régimen en Código

$$\text{Régimen} = \begin{cases} 
\mathbf{C1}, & \text{si } \Delta \text{Commodities} > 0 \land \Delta \text{Imacec} \ge 0 \\
\mathbf{C2}, & \text{si } \Delta \text{WTI} > +2\sigma \land \Delta \text{TasasReales} \le 0 \\
\mathbf{C3}, & \text{si } \Delta \text{Cobre} < -1.5\sigma \land \text{Curva 2s10s aplanándose} \\
\mathbf{C4}, & \text{si } \Delta \text{Tasas 10Y} \le 0 \land \text{Inflación cediendo}
\end{cases}$$
