# Ficha Técnica: Análisis Técnico Intermercado y Causalidad Cross-Asset
**Referencia Clásica**: Murphy, John J. (1991, 2004). *Intermarket Analysis: Profiting from Global Market Relationships*. John Wiley & Sons.

---

## 1. Tesis Fundamental

Ningún mercado opera en un vacío. Las cuatro grandes clases de activos financieros (**Divisas, Bonos, Commodities y Renta Variable**) están interconectadas por flujos globales de liquidez y expectativas de inflación y crecimiento.

El principio rector es la **secuencia causal de rotación de capital**:
$$\text{Divisas / Tasas} \longrightarrow \text{Commodities} \longrightarrow \text{Bonos} \longrightarrow \text{Acciones}$$

---

## 2. Los 4 Axiomas Intermercado de Murphy

```
         ┌──────────────────────────────────────────────┐
         │              1. DÓLAR / DIVISAS              │
         │     (Fortaleza global del Dólar Index / FX)   │
         └──────────────────────┬───────────────────────┘
                                │ Relación Inversa (-)
                                ▼
         ┌──────────────────────────────────────────────┐
         │                2. COMMODITIES                │
         │      (Petróleo, Cobre, Oro, Materias Primas)  │
         └──────────────────────┬───────────────────────┘
                                │ Presión Inflacionaria (+)
                                ▼
         ┌──────────────────────────────────────────────┐
         │             3. BONOS Y TASAS (YIELDS)         │
         │  (Yields suben cuando la inflación sube;     │
         │   Precios de bonos caen)                     │
         └──────────────────────┬───────────────────────┘
                                │ Costo de Descuento (-)
                                ▼
         ┌──────────────────────────────────────────────┐
         │              4. RENTA VARIABLE               │
         │     (Sensibilidad de múltiplos a la tasa)    │
         └──────────────────────────────────────────────┘
```

1. **Dólar vs. Commodities (Correlación Inversa)**:
   * La mayoría de las materias primas cotizan en dólares estadounidenses.
   * Un dólar fuerte encarece las materias primas para tenedores de otras monedas, contrayendo la demanda y presionando los precios a la baja.
   * *Excepción*: Shocks de oferta geopolíticos donde el petróleo y el dólar suben juntos como refugio.

2. **Commodities vs. Bonos / Tasas (Impulsor de Inflación)**:
   * El alza persistente en energía (WTI/Brent) y metales industriales (Cobre) se transmite al índice de precios al consumidor (IPC).
   * Los bancos centrales responden elevando tasas o los inversores exigen mayor rendimiento nominal, empujando al alza las tasas del Tesoro (`DGS10`, `DGS2`).

3. **Tasas de Bonos vs. Acciones (Costo de Oportunidad y Descuento)**:
   * Rendimientos altos del bono libre de riesgo a 10 años (`DGS10 > 4.5%`) compiten directamente con el dividendo y los retornos esperados de la renta variable.
   * Afecta con mayor fuerza a las empresas de crecimiento (`US100` / Tech) por la tasa de descuento de flujos futuros.

4. **Secuencia de Giro en el Ciclo Económico**:
   * **Cima del ciclo**: Los Bonos caen primero (tasas suben) $\rightarrow$ Las Acciones hacen techo $\rightarrow$ Las Commodities hacen techo al final (último impulso inflacionario).
   * **Fondo del ciclo**: Los Bonos tocan fondo y rebotan primero (tasas bajan) $\rightarrow$ Las Acciones rebotan $\rightarrow$ Las Commodities tocan fondo al final.

---

## 3. Implicancias Cuantitativas para el Trading Desk

### A. Filtrado de Falsos Rompimientos Técnicos (*Macro Confirmation Filter*)
* **Regla Operativa**: Un rompimiento alcista en `US100` (Nasdaq) en gráfico H1/4H tiene una probabilidad de fallo superior al 60% si el rendimiento a 10 años (`DGS10`) está marcando nuevos máximos de 52 semanas en paralelo.
* **Confirmación Intermercado**: La compra técnica en índices se valida cuando el 10Y cede o consolida en soporte.

### B. Posicionamiento en USD/CLP
* El par `USD/CLP` es un activo híbrido de Divisa + Commodity.
* Si el Cobre COMEX (`HG`) está en tendencia bajista y el rendimiento del Tesoro de EE.UU. sube, **el sesgo técnico debe ser exclusivamente comprador** en retrocesos a medias móviles (EMA 20/50 en H1).

---

## 4. Regla de Implementación en el Sistema
$$\text{Filtro Murphy} = \begin{cases} 
\text{PERMITIR COMPRAS EN RIESGO}, & \text{si } \Delta \text{10Y} \le 0 \text{ y } \text{Petróleo estable} \\
\text{FORZAR DEFENSIVO / BREAKOUTS}, & \text{si } \Delta \text{10Y} > 0 \text{ y } \text{Petróleo en rally}
\end{cases}$$
