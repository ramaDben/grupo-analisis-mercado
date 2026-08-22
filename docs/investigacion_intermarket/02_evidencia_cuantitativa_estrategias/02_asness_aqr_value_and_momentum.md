# Ficha Técnica: Fusión de Factores Macroeconómicos y Técnicos (Value & Momentum)
**Referencia Académica**: Asness, Clifford S.; Moskowitz, Tobias J.; Pedersen, Lasse Heje (2013). *Value and Momentum Everywhere*. The Journal of Finance, 68(3), 929-985.

---

## 1. Tesis Fundamental

Los dos factores cuantitativos más persistentes y documentados en la historia financiera son:
1. **Value (Valor / Fundamentales / Macro)**: Comprar activos cuyo precio de mercado está descontado respecto a su ancla fundamental (ej. diferencial de tasas, términos de intercambio, valoración intrínseca).
2. **Momentum (Tendencia / Técnico)**: Comprar activos que han tenido un rendimiento relativo superior reciente y vender activos rezagados.

El descubrimiento empírico central del paper es que **Value y Momentum están negativamente correlacionados entre sí ($\rho \approx -0.50$), pero ambos tienen retornos esperados positivos**.

$$\text{Sharpe}(\text{Macro Value} + \text{Technical Momentum}) \gg \text{Sharpe}(\text{Macro}) \text{ o } \text{Sharpe}(\text{Technical})$$

---

## 2. Por qué la Fusión Supera a Cada Enfoque Aislado

```
                          ┌────────────────────────┐
                          │   FILTRO FUNDAMENTAL   │
                          │      (Macro Value)     │
                          │   ¿Hacia dónde DEBE    │
                          │    ir el activo?       │
                          └───────────┬────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │    CONDICIÓN DE CONFLUENCIA    │
                      │   (Solo operar cuando ambos    │
                      │      apuntan al mismo lado)    │
                      └───────────────┬────────────────┘
                                      │
                                      ▲
                          ┌───────────┴────────────┐
                          │    GATILLO TÉCNICO     │
                          │  (Technical Momentum)  │
                          │   ¿El precio ya está   │
                          │     MOVIÉNDOSE?        │
                          └────────────────────────┘
```

1. **El Problema del Analista Fundamental Puro (*Value Trap*)**:
   * Sabe que el USD/CLP debería subir porque el Cobre cae, pero entra demasiado temprano y queda atrapado en una consolidación prolongada o sufre por falta de timing.
2. **El Problema del Analista Técnico Puro (*False Breakouts*)**:
   * Ve una vela alcista o un cruce de medias en M15, pero compra justo en el techo porque desconoce que la tasa a 10 años se disparó o que el Banco Central está por intervenir.
3. **La Solución Asness-AQR (Confluencia Macro + Momentum)**:
   * El fundamental macro en `data central/` establece el **filtro direccional obligatorio** (no se permiten posiciones en contra).
   * La técnica en MT5 (H1/15M) actúa como el **gatillo de precisión temporal**.

---

## 3. Matriz de Retornos Cuantitativos del Estudio

El estudio evaluó 4 clases de activos (Renta Variable individual y por países, Bonos de Gobierno, Divisas y Commodities) desde 1972:

| Estrategia | Sharpe Ratio Incondicional | Correlación con el Mercado | Rendimiento en Caídas de Mercado |
| :--- | :---: | :---: | :---: |
| **Solo Value (Fundamental)** | 0.45 | Baja / Variable | Moderado |
| **Solo Momentum (Técnico)** | 0.60 | Próxima a 0 | Alto (Positivo en crisis) |
| **Combinación 50/50 (Value + Momentum)** | **1.15 - 1.40** | **Descorrelacionado** | **Resiliente / Retornos Sólidos** |

---

## 4. Regla de Implementación para el Trading Desk

Para cada activo de la rotación diaria (`USDCLP`, `XAUUSD`, `WTI`, `US100`):

1. **Puntaje Macro ($S_{\text{Macro}} \in [-2, +2]$)**:
   * Calculado a partir de los diferenciales de tasas, curva de rendimientos y precios de commodities en `data central/`.
2. **Puntaje Técnico ($S_{\text{Técnico}} \in [-2, +2]$)**:
   * Basado en la pendiente de la EMA 50, posición respecto al VWAP y estructura de máximos/mínimos en H1.
3. **Regla de Ejecución**:
   * **Señal de Compra Válida**: Solo si $S_{\text{Macro}} > 0$ **Y** $S_{\text{Técnico}} > 0$.
   * **Señal de Venta Válida**: Solo si $S_{\text{Macro}} < 0$ **Y** $S_{\text{Técnico}} < 0$.
   * **Divergencia ($S_{\text{Macro}} \times S_{\text{Técnico}} \le 0$)**: **MODO ESPERA / NEUTRAL**. No se toman operaciones swing.
