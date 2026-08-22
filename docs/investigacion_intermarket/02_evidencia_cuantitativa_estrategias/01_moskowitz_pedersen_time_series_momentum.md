# Ficha Técnica: Time Series Momentum (TSMOM) y Edge en Shocks Macro
**Referencia Académica Principal**: Moskowitz, Tobias J.; Ooi, Yao Hua; Pedersen, Lasse Heje (2012). *Time Series Momentum*. Journal of Financial Economics, 104(2), 228-250.

---

## 1. Tesis Fundamental

El estudio de Moskowitz, Ooi y Pedersen (profesores de Chicago Booth, NYU y fundadores de AQR Capital Management) es el estudio empírico más citado en la literatura cuantitativa sobre seguimiento de tendencias (*trend-following*).

Analizando **58 contratos de futuros líquidos y activos a lo largo de 25 años** en 4 clases de activos (24 commodities, 12 índices bursátiles, 9 divisas y 13 bonos soberanos), demostraron que:
> **El retorno pasado de un activo (en su propia serie temporal) es un predictor positivo estadísticamente significativo de su retorno futuro**.

---

## 2. Formalización Matemática de la Estrategia TSMOM

Para cada activo $i$ en el mes/semana/día $t$, la señal de posición $X_t^i$ se define por el signo del retorno acumulado en una ventana previa de $k$ períodos:
$$X_t^i = \text{sign}\left( R_{t-k, t}^i \right) \in \{-1, +1\}$$

El retorno de la estrategia en el activo $i$ escalado por volatilidad es:
$$r_{t, t+1}^{\text{TSMOM}, i} = \frac{40\%}{\sigma_t^i} X_t^i \cdot r_{t, t+1}^i$$
Donde $\sigma_t^i$ es la volatilidad ex-ante estimada por el modelo de medias móviles exponenciales (EWMA) o ATR.

---

## 3. Descubrimientos Clave y Conclusiones Empíricas

### A. Asimetría Positiva en Colas de Volatilidad (*Crisis Alpha / Positive Skewness*)
* A diferencia de las estrategias basadas en comprar caídas (*dip buying* o *mean-reversion*), que tienen una asimetría negativa (ganan muchas veces poco, pero pierden de forma catastrófica cuando el mercado colapsa), **el Time Series Momentum genera retornos sustanciales durante los peores meses del mercado**.
* Durante las crisis financieras, la inflación desbordada o los shocks geopolíticos, los precios desarrollan tendencias persistentes unidireccionales (los perdedores siguen cayendo y los ganadores siguen subiendo).

```
  Frecuencia
      ▲
      │                 DISTRIBUCIÓN TSMOM
      │                 (Cola derecha extendida: Crisis Alpha)
      │                     ┌──┐
      │                    ┌┘  └┐
      │                   ┌┘    └┐
      │                 ┌─┘      └──────┐
      │           ──────┘               └─────────────► Retorno
      └───────────────────────────────────────────────
                  Pérdidas Acotadas      Ganancias Masivas
                  por Stop Loss          en Shocks de Mercado
```

### B. Comportamiento por Clase de Activo
* **Commodities (Petróleo, Cobre, Oro)**: Presentan la mayor persistencia de tendencia debido a las rigideces estructurales de oferta y demanda física.
* **Divisas (FX / USDCLP)**: Fuerte inercia por diferenciales de política monetaria sostenidos en el tiempo.
* **Renta Variable (US100 / US500)**: Momentum positivo en expansiones; caídas violentas que premian rápidamente las posiciones cortas cuando se perforan soportes mayores.

---

## 4. Regla de Implementación en el Trading Desk

1. **Alineación de Temporalidades (Elder Triple Screen)**:
   * **Pantalla 1 (Macro / 4H-1D)**: Filtro TSMOM mediante la dirección de la EMA de 50 períodos y el signo del retorno de 60 velas.
   * **Pantalla 2 (Intradía / 1H)**: Detección del retroceso técnico (oscilador RSI o MACD sobrevendido en tendencia alcista).
   * **Pantalla 3 (Ejecución / 15M)**: Entrada por rompimiento del máximo de la vela previa con Stop Loss basado en $1.5 \times \text{ATR}_{14}$.

2. **Prohibición de "Cazar Cuchillos que Caen"**:
   * Queda terminantemente prohibido comprar activos con señal TSMOM negativa en 4H argumentando "está muy barato", a menos que el driver macro haya cambiado oficialmente en `data central/`.
