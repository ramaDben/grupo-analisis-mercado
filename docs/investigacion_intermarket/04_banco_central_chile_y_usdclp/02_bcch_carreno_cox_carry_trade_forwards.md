# Ficha Técnica: Carry Trade, Posición Forward de Extranjeros y Volatilidad del USD/CLP
**Referencia Oficial**: Carreño, Gabriela; Cox, Pablo (Banco Central de Chile, 2014 / DT N° 722). *Carry trade y turbulencias cambiarias con el peso chileno*.

---

## 1. Tesis Fundamental

El tipo de cambio `USD/CLP` no solo responde a variables de comercio exterior (cobre y petróleo), sino intensamente a **flujos financieros de corto plazo y operaciones de arbitraje de tasas (*Carry Trade*)**.

Los dos motores financieros locales más determinantes monitoreados por el Banco Central son:
1. **El Diferencial de Tasas de Política Monetaria ($\Delta r = \text{TPM}_{\text{Chile}} - \text{Fed Funds}$)**.
2. **La Posición Neta Forward de Agentes No Residentes (Bancos y Fondos Extranjeros en T-2)**: Publicada diariamente por el BCCh (`POSICION_FORWARD_EXTRANJEROS`).

---

## 2. Dinámica del Carry Trade y Desarme de Posiciones

```
                    DIFERENCIAL DE TASAS (TPM - Fed Funds)
                                      ▲
                                      │
            SPREAD AMPLIO             │            SPREAD COMPRIMIDO
        (TPM >> Fed Funds)            │           (TPM aproxima a Fed)
                                      │
      • Inversores se endeudan        │  • Se reduce incentivo de carry
        en USD y compran CLP          │  • Menor colchón de protección
      • Peso Chileno se aprecia       │  • USD/CLP muy sensible
      • USD/CLP a la baja             │    a shocks externos
                                      │
 ◄────────────────────────────────────┼────────────────────────────────────►
                                      │
                             FLUJO FORWARD (T-2)
                                      │
                                      ▼
             POSICIÓN NETA FORWARD DE EXTRANJEROS (M USD)
      • Extranjeros compran USD Fwd (+) → Presión alcista en USD/CLP
      • Extranjeros venden USD Fwd (-)  → Presión bajista en USD/CLP
```

### Mecánica del Mercado Forward:
* Cuando los bancos offshore esperan volatilidad o depreciación en mercados emergentes, compran masivamente contratos *forward* de dólares contra pesos chilenos.
* Los bancos locales, para calzar su riesgo cambiario, deben salir al mercado spot a comprar dólares de contado $\rightarrow$ **Generando una presión alcista inmediata en el precio de pantalla del USD/CLP**.

---

## 3. Diagnóstico Cuantitativo con los Datos Oficiales de Hoy

En nuestro snapshot en vivo de [`data central/latest_drivers.json`](file:///C:/Users/bbrav/grupo-analisis-mercado/data%20central/DATA%20DRIVERS%20USDCLP/latest_drivers.json):
* **TPM Chile**: `4.50%` (actualizado hoy en vivo vía SIETE).
* **Fed Funds**: `3.63%` (actualizado hoy en vivo vía FRED).
* **Diferencial de Tasas ($\Delta r$)**: $+0.87\%$ (87 puntos básicos).
* **Posición Forward Extranjeros**: $+4.450 \text{ Millones USD}$ (posición compradora neta).

### Conclusión Econométrica:
1. Con un spread de solo 87 bps, el *carry trade* tradicional a favor del peso está en su nivel más bajo de los últimos años.
2. La elevada posición compradora de dólares de los extranjeros ($+4.450 \text{M USD}$) actúa como un **piso técnico estructural para el USD/CLP**, impidiendo caídas bruscas sostenidas a menos que el Cobre supere los $6.60 USD/lb con fuerza.

---

## 4. Regla de Implementación Operativa para USD/CLP en MT5

* **Filtro de Desarme de Forwards**:
  * Si la Posición Forward de extranjeros aumenta en más de $+300\text{M USD}$ en una semana $\rightarrow$ **Priorizar compras intradía en soportes H1**.
  * Si la Posición Forward cae por debajo de $+2.000\text{M USD}$ $\rightarrow$ Activación de escenario bajista sostenido para el USD/CLP hacia $890-$900.
