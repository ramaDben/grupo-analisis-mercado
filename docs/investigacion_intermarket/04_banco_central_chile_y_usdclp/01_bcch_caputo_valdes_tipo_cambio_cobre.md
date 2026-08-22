# Ficha Técnica: Transmisión del Cobre al Tipo de Cambio USD/CLP
**Referencia Oficial**: Caputo, Rodrigo; Núñez, Marco; Valdés, Rodrigo (Banco Central de Chile, Documento de Trabajo N° 434). *Análisis del Tipo de Cambio en la Práctica*.

---

## 1. Tesis Fundamental

El peso chileno (CLP) es el caso de estudio clásico de una **moneda de commodity (*commodity currency*)**. Dado que el cobre representa más del 50% de las exportaciones chilenas y una parte sustancial de los ingresos fiscales, las variaciones en el precio internacional del metal rojo (`HG` en COMEX / LME) determinan los términos de intercambio de la economía chilena.

El estudio demuestra que:
1. Existe una **relación de cointegración de largo plazo** entre el logaritmo del precio del cobre y el tipo de cambio real y nominal.
2. A corto plazo (intradía y semanal), las desviaciones temporales del tipo de cambio respecto al precio del cobre generan **oportunidades sistemáticas de reversión a los fundamentales**.

---

## 2. El Mecanismo de Transmisión Econométrico

```
                     PRECIO DEL COBRE COMEX (HG)
                                  ▲
                                  │
                                  │ Exportaciones / Flujo de Divisas
                                  ▼
                     OFERTA DE DÓLARES EN CHILE
                     (Liquidación minera + Fisco)
                                  ▲
                                  │
                                  │ Mayor oferta local de USD
                                  ▼
                   FORTALECIMIENTO DEL PESO CHILENO
                   (Tipo de cambio USD/CLP cae)
```

### Elasticidad de Transmisión:
$$\Delta \ln(\text{USD/CLP}) \approx -\beta_1 \Delta \ln(\text{Precio Cobre}) + \beta_2 \Delta \ln(\text{DXY}) - \beta_3 (\text{TPM}_{\text{Chile}} - \text{Fed Funds})$$

Donde empíricamente:
* $\beta_1 \approx 0.40 - 0.55$: Un aumento del **10% en el precio del cobre** tiende a generar una apreciación del **4% al 5.5% en el peso chileno** (caída del USD/CLP), ceteris paribus.
* $\beta_2 \approx 0.60 - 0.75$: Sensibilidad a la fortaleza global del dólar.

---

## 3. Desfases Temporales y Ventana de Oportunidad Técnica

El mercado de futuros de cobre en Nueva York (COMEX) abre y se mueve durante la madrugada y mañana de Chile. Con frecuencia, un movimiento brusco en el cobre tarda entre **30 minutos y 2 horas** en transmitirse plenamente a la punta compradora/vendedora del mercado interbancario chileno de USD/CLP.

### El Setup de "Divergencia Cobre vs. USD/CLP":
* **Escenario**: El Cobre COMEX sube un +2.0% en la apertura, pero el USD/CLP abre plano o subiendo por inercia local.
* **Acción Cuantitativa**: **VENTA DE ALTA PROBABILIDAD (Short USD/CLP)**. El arbitraje intermercado forzará al USD/CLP a converger a la baja hacia sus niveles de soporte H1.

---

## 4. Regla de Implementación en el Trading Desk

* **Verificación matutina en `latest_drivers.json`**:
  * Si `COBRE_HG` está marcando nuevos máximos diarios (> $6.45 USD/lb) $\rightarrow$ **Prohibido abrir posiciones de compra swing en USD/CLP**.
  * Solo buscar ventas en resistencias técnicas (R1 / R2) con Stop Loss ajustado por ATR diario.
