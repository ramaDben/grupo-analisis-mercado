# Ficha Técnica: La Curva de Rendimientos como Predictor del Ciclo y Riesgo
**Referencia Académica**: Estrella, Arturo; Mishkin, Frederic S. (1996, 1998). *The Yield Curve as a Predictor of U.S. Recessions*. Federal Reserve Bank of New York / Review of Economics and Statistics, 80(1), 45-61.

---

## 1. Tesis Fundamental

La estructura temporal de las tasas de interés (la **Curva de Rendimientos del Tesoro de EE.UU.**) contiene la mayor cantidad de información agregada sobre las expectativas del mercado respecto al crecimiento futuro, la inflación y la política monetaria de la Reserva Federal.

El diferencial o *spread* entre los bonos de largo plazo y corto plazo:
$$\text{Spread 2s10s} = \text{DGS10} - \text{DGS2}$$
$$\text{Spread 3m10s} = \text{DGS10} - \text{DGS3M}$$

Es el indicador econométrico líder más fiable de la historia financiera para anticipar giros en la economía y transiciones de volatilidad en los mercados.

---

## 2. Los 4 Estados de la Curva de Rendimientos

```
               PENDIENTE DE LA CURVA (10Y - 2Y)
                              ▲
                              │
          BULL STEEPENING     │     BEAR STEEPENING
        [RELAJACIÓN / CRISIS] │    [REFLACIÓN / OFERTA]
       (2Y cae más que 10Y)   │   (10Y sube más que 2Y)
                              │
      • Fed recortando tasas  │  • Crecimiento acelerado
      • Oro sube fuertemente  │  • Petróleo y Cobre suben
      • Divisas emergentes    │  • Renta variable rota
        bajo presión          │    hacia valor/energía
                              │
  ────────────────────────────┼────────────────────────────► TIEMPO
                              │
          BULL FLATTENING     │     BEAR FLATTENING
        [DESINFLACIÓN PURA]   │   [AJUSTE MONETARIO / FED]
       (10Y cae más que 2Y)   │   (2Y sube más que 10Y)
                              │
      • Inflación controlada  │  • Fed sube tasas fuerte
      • US100 / Tech lidera   │  • Presión en acciones tech
      • Máxima estabilidad    │  • Dólar global (DXY) fuerte
                              │
                              ▼
```

1. **Bear Flattening (Aplanamiento por Ajuste de la Fed)**:
   * La Fed sube tasas agresivamente; las tasas cortas (`DGS2`) suben más rápido que las largas (`DGS10`).
   * **Impacto**: Dólar global fuerte, compresión de múltiplos en tecnológicas (`US100`), caída en materias primas.
2. **Inversión de Curva ($\text{Spread} < 0$)**:
   * Alerta de tensión en el sistema bancario y restricción crediticia.
3. **Bull Steepening (Empinamiento por Descompresión / Recortes)**:
   * La Fed comienza a recortar tasas de emergencia; las tasas cortas se desploman.
   * **Impacto**: Alta volatilidad; el Oro reacciona fuertemente al alza como reserva de liquidez.

---

## 3. Implicancias Cuantitativas para el Trading

### A. Diagnóstico Actual con la Data Oficial de FRED
En nuestro snapshot de `data central/DATA USA/raw/treasury_fed_data.json`:
* `DGS10` = **4.65%**
* `DGS2` = **4.19%**
* `Spread 2s10s` = **+0.46%** (46 puntos básicos, pendiente positiva normalizada).

### B. Regla Operativa
* **Spread 2s10s > +0.30% y estable**: Condición favorable para operaciones de tendencia en acciones e índices (`US100` / `US500`).
* **Spread 2s10s aplanándose rápidamente (< +0.10%)**: Reducir exposición en tecnológicas y favorecer coberturas en activos refugio.
