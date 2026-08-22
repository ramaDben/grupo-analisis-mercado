# Ficha Técnica: El Dilema del Oro, Tasas de Interés Reales y Cobertura Inflacionaria
**Referencia Académica**: Erb, Claude B.; Harvey, Campbell R. (2013). *The Golden Dilemma*. Financial Analysts Journal, 69(4), 10-42. (NBER Working Paper No. 18706).

---

## 1. Tesis Fundamental

A menudo se asume en el análisis financiero convencional que el oro es una "cobertura perfecta contra la inflación en el corto plazo". Erb y Harvey demostraron empíricamente que **en horizontes de corto y mediano plazo (semanas, meses, pocos años), el oro NO está correlacionado de forma simple con la inflación realizada, sino con las TASAS DE INTERÉS REALES**.

El costo de oportunidad de mantener oro (un activo con rendimiento cero en flujo de caja) es la tasa de interés real libre de riesgo que un inversor puede obtener en bonos del gobierno:
$$\text{Tasa Real} = \text{Rendimiento Nominal 10Y (DGS10)} - \text{Inflación Esperada (Breakeven 10Y)}$$

---

## 2. El Modelo Econométrico del Oro

```
                ┌──────────────────────────────────────────────┐
                │          TASAS DE INTERÉS REALES (TIPS)      │
                │        (Bono del Tesoro EE.UU. a 10 años)    │
                └──────────────────────┬───────────────────────┘
                                       │ Relación Inversa Fuerte
                                       │ (R² > 0.70 en ciclos)
                                       ▼
                ┌──────────────────────────────────────────────┐
                │             PRECIO SPOT DEL ORO              │
                │                  (XAU / USD)                 │
                └──────────────────────────────────────────────┘
```

1. **Cuando la Tasa Real Cae / Se Vuelve Negativa**:
   * El dinero en el banco pierde poder adquisitivo en términos reales.
   * Los grandes fondos soberanos e institucionales migran masivamente hacia el oro como reserva de valor.
   * **Resultado**: Rallies históricos y tendencias parabólicas en `XAU/USD`.

2. **Cuando la Tasa Real Sube Fuertemente**:
   * Los bonos del Tesoro ofrecen un rendimiento real positivo garantizado.
   * El oro sufre salidas de capital hacia renta fija libre de riesgo.
   * **Resultado**: Correcciones profundas o techos mayores en el precio del oro.

---

## 3. Cobertura Geopolítica y Compras de Bancos Centrales

El estudio complementa el modelo de tasas reales con dos variables adicionales:
* **Prima de Riesgo Geopolítico**: El oro actúa como activo desvinculado del sistema financiero occidental (sin riesgo de contraparte ni congelamiento de reservas).
* **Demanda Estructural de Bancos Centrales Emergentes (China, India, BRICS)**: Compras masivas que crean un piso estructural en el precio.

---

## 4. Regla de Implementación Operativa para XAU/USD

Para la operativa diaria de Oro en MT5:

1. **Lectura de Variables en `data central/`**:
   * Consultar `DGS10` (Rendimiento 10Y) en [`latest_drivers.json`](file:///C:/Users/bbrav/grupo-analisis-mercado/data%20central/DATA%20DRIVERS%20USDCLP/latest_drivers.json).
   * Si el 10Y retrocede mientras el Petróleo (`Brent` > $90) mantiene elevadas las presiones inflacionarias, **la tasa real está cayendo $\rightarrow$ SESGO FUERTE ALCISTA**.

2. **Filtro Técnico en MT5 (H1)**:
   * **Si Tasa Real Bajando**: Solo operar compras (*Long*). Buscar retrocesos al soporte técnico o cruce de EMA 20 sobre EMA 50.
   * **Si Tasa Real Subiendo Aceleradamente**: Prohibido comprar rupturas alcistas tardías; buscar tomas de utilidad o ventas tácticas intradía.
