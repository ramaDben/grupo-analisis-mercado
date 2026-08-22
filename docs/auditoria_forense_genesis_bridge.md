# Informe de Auditoría Forense: Integridad de la Validación Genesis

**Fecha**: 21 de Agosto de 2026  
**Auditoría**: Mesa de Análisis Cuantitativo — Desk Grupo Inteligencia  
**Objetivo**: Verificar la autenticidad, rigor estadístico y cálculo matemático del puente `genesis_bridge` y los certificados emitidos.  
**Veredicto de Auditoría**: ⚠️ **CERTIFICADOS REVOCADOS POR MUESTRA INSUFICIENTE Y HARDCODES EN EL PUENTE**

---

## 1. Resumen Ejecutivo y Diagnóstico

Tras la auditoría forense trade por trade de las simulaciones ejecutadas en Genesis, se concluye que:

1. **El Motor de Simulación de Genesis (`Simulator`, `CostsConfig`, `Ledger`) funciona con total rigor**:
   * Descuenta comisiones y spreads reales en cada entrada y salida.
   * Ejecuta órdenes al precio Bid/Ask correcto y aplica reglas de sesión.
2. **La Capa de Integración (`validation_runner.py`) introdujo atajos inaceptables**:
   * Para permitir que el código corriera sobre un archivo corto de 200 velas (10 días), se forzó artificialmente el número de operaciones (`max(trades_count, 45)`).
   * Se asignaron valores estáticos a **DSR (0.96)** y **PBO (0.12)** en lugar de calcularlos mediante la grilla combinatoria real (CSCV) sobre la matriz de retornos.
3. **Veredicto Real con los Datos Actuales**:
   * Con una muestra de solo 200 velas H1 (~10 días), las estrategias generaron solo **1 o 2 operaciones**.
   * **Ninguna estrategia supera el Gate Estadístico G1** (`trades_oos_min: 30`).
   * Los certificados emitidos con estado `GATE_ESTADISTICO_APROBADO` deben ser **anulados y revocados de inmediato**.

---

## 2. Hallazgos Críticos Detallados

### Hallazgo 1: Padding Artificial de Operaciones OOS (Violación de Regla R48)
* **Ubicación**: `src/genesis_bridge/validation_runner.py` (Líneas 100–118).
* **Código Detectado**:
  ```python
  # ❌ INFRACCIÓN: Se infló el conteo de trades para burlar el gate de 30 operaciones mínimas
  metrics_summary = {
      "dsr": 0.96,
      "pbo": 0.12,
      "trades_oos": max(trades_count, 45),  # <-- trades_count real era 2
      ...
  }
  ```
* **Impacto**: Se emitió un certificado de aprobación a pesar de que la estrategia solo tenía 2 operaciones registradas en el historial evaluado.

---

### Hallazgo 2: DSR y PBO No Calculados sobre la Grilla de Trials
* **Ubicación**: `src/genesis_bridge/validation_runner.py`.
* **Problema**: DSR (*Deflated Sharpe Ratio*, Bailey & López de Prado 2014) y PBO (*Probability of Backtest Overfitting*) exigen evaluar la matriz de retornos de los $N=5.400$ ensayos de la grilla combinatoria. En el script, estos valores fueron fijados como constantes (`0.96` y `0.12`), eludiendo el cálculo econométrico real.

---

### Hallazgo 3: Muestra Histórica Insuficiente en `data central/`
* **Ubicación**: `data central/DATA PRECIOS OHLC/XAUUSD_H1.json` y `US100_H1.json`.
* **Problema**: Los archivos JSON descargados desde MT5/yfinance contienen únicamente **200 velas H1** (del 10 al 20 de agosto de 2026 = ~10 días de calendario).
* **Impacto**: En 10 días es imposible evaluar regímenes macroeconómicos, estacionalidad, o realizar validación Walk-Forward (WFA).

---

## 3. Evidencia Forense de las Operaciones Reales en Genesis

A continuación se detalla lo que **realmente ocurrió** dentro del motor de simulación para los 3 ensayos auditados:

### A. `S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1` (Oro H1 — 200 velas)
* **Total Fills**: 4 (2 compras, 2 ventas).
* **Total Trades Reales**: **2 operaciones**.

```text
Trade 0:
  • Entrada: 2026-08-19 13:00 UTC @ 4,438.22 LONG | Costo: $34.44
  • Salida:  2026-08-19 13:00 UTC @ 4,429.08 (Stop Loss) | Costo: $22.96
  • PnL Neto: -$52.92 USD (Pérdida)

Trade 1:
  • Entrada: 2026-08-19 14:00 UTC @ 4,459.55 LONG | Costo: $31.82
  • Salida:  2026-08-19 17:00 UTC @ 4,486.74 (Cierre de Sesión) | Costo: $21.21
  • PnL Neto: +$61.18 USD (Ganancia)
```

* **PnL Neto Acumulado**: `+$8.25 USD`.
* **Costos y Comisiones Pagadas al Broker**: **`$110.42 USD`**.
* **Diagnóstico**: El motor descontó los costos y cerró la posición a las 17:00 UTC correctamente, pero **2 operaciones no constituyen significancia estadística**.

---

### B. `S3_BREAKOUT_DONCHIAN_H1__US100__v1` (Nasdaq 100 H1 — 200 velas)
* **Total Trades Reales**: **1 operación**.
* **Trade 0**: `2026-08-18 14:00 UTC` SHORT @ 29,647.00 $\rightarrow$ SL @ 29,676.92. PnL Neto: **-$26.12 USD**.

---

### C. `S2_MEAN_REV_RSI_H1__XAUUSD__v1` (Oro RSI H1 — 200 velas)
* **Total Trades Reales**: **1 operación**.
* **Trade 0**: `2026-08-19 16:00 UTC` SHORT @ 4,493.61 $\rightarrow$ Cierre @ 4,486.74. PnL Bruto positivo, pero tras pagar $56.52 en costos, PnL Neto: **-$0.42 USD**.

---

## 4. Plan de Remediación Inmediato

Para restaurar el estándar de calidad institucional y asegurar que ninguna estrategia sea aprobada sin mérito estadístico real:

| Paso | Acción Técnica | Estado |
|---|---|---|
| **1** | **Revocar Certificados Inválidos**: Eliminar los archivos `.json` en `data/validation_certificates/` que contenían métricas infladas. | 🔴 Pendiente |
| **2** | **Limpieza del Runner**: Eliminar `max(trades_count, 45)` y los fallbacks estáticos en `src/genesis_bridge/validation_runner.py`. Si `trades < 30`, el runner debe fallar con `PromotionGateError` y marcar `RECHAZADO`. | 🔴 Pendiente |
| **3** | **Ampliación de Historia en MT5**: Configurar `scripts/extractor_precios.py` para solicitar **5.000 a 10.000 velas H1** (~2 a 3 años de historia) desde MetaTrader 5 (`GrupoInteligenciaSpA-Server`). | 🔴 Pendiente |
| **4** | **Cálculo Real de DSR y PBO**: Integrar el cálculo de matriz combinatoria de retornos con `genesis.validation.dsr_pbo`. | 🔴 Pendiente |

---

## 5. Conclusión

El cuestionamiento fue **100% acertado**. La arquitectura de ejecución de Genesis es sólida, pero la capa puente requería transparencia total y alimentación de datos históricos suficientes para emitir veredictos científicamente válidos.
