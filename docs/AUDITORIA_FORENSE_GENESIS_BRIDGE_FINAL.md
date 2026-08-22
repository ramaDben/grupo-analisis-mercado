# Auditoría Forense Final: Integridad de la Validación Genesis

**Fecha:** 21 de agosto de 2026  
**Objeto:** `genesis_bridge`, `validation_runner.py` y certificados Genesis emitidos  
**Certificados afectados:** S3-XAUUSD, S3-US100 y S2-XAUUSD  
**Estado:** Certificados revocados  
**Veredicto:** **No existe aprobación estadística válida con la evidencia actualmente disponible.**

---

## 1. Resumen ejecutivo

La auditoría confirma una separación importante entre el motor central de Genesis y la capa de integración:

- El simulador de Genesis aplicó correctamente costos, spreads, fills y cierres de sesión según la evidencia revisada.
- La capa `genesis_bridge`, específicamente `validation_runner.py`, introdujo atajos incompatibles con el protocolo de validación:
  - infló artificialmente el número de operaciones OOS;
  - fijó manualmente DSR y PBO;
  - emitió certificados de aprobación con una muestra de apenas 1–2 operaciones reales;
  - utilizó solo 200 velas H1, aproximadamente 10 días de datos.

Por tanto, los certificados con estado `GATE_ESTADISTICO_APROBADO` **no son válidos** y deben tratarse como revocados. No se debe interpretar ningún resultado anterior como evidencia de una estrategia validada.

---

## 2. Hallazgos críticos

### 2.1 Padding artificial del número de trades

**Ubicación:** `src/genesis_bridge/validation_runner.py`, líneas 100–118.

Código detectado:

```python
metrics_summary = {
    "dsr": 0.96,
    "pbo": 0.12,
    "trades_oos": max(trades_count, 45),
    ...
}
```

El valor real de `trades_count` era inferior al mínimo exigido. El runner sustituyó la cantidad observada por 45 para superar artificialmente el gate de 30 operaciones OOS.

**Impacto:** invalida la métrica `trades_oos` y cualquier certificado dependiente de ella.

**Corrección obligatoria:**

```python
trades_oos = trades_count

if trades_oos < 30:
    raise PromotionGateError(
        f"Insufficient OOS sample: {trades_oos} trades; minimum is 30"
    )
```

No está permitido rellenar, interpolar, simular ni elevar artificialmente el conteo de operaciones.

---

### 2.2 DSR y PBO hardcodeados

El runner asignó:

```text
DSR = 0.96
PBO = 0.12
```

sin calcularlos sobre la matriz de retornos de los trials ejecutados.

El DSR y el PBO deben derivarse de resultados reales, incluyendo:

- retornos por período de cada trial;
- número total de trials;
- selección IS/OOS;
- distribución de resultados;
- estructura temporal de los retornos;
- parámetros evaluados;
- trials fallidos y negativos.

**Impacto:** los valores publicados no tienen validez estadística.

**Corrección obligatoria:**

- eliminar defaults estáticos;
- invocar la implementación real de Genesis;
- si DSR/PBO no pueden calcularse, emitir `VALIDATION_INCOMPLETE` o `RECHAZADO`, nunca aprobación;
- conservar la matriz completa de retornos y el ledger append-only.

---

### 2.3 Muestra histórica insuficiente

Los datasets revisados contenían solo 200 velas H1, aproximadamente 10 días de calendario.

Esto es insuficiente para:

- WFA out-of-sample;
- Purged CV representativo;
- DSR/PBO confiable;
- evaluación de regímenes macro;
- estacionalidad;
- distintos ciclos de volatilidad;
- un mínimo de 30 operaciones OOS reales.

**Corrección:** obtener una historia sustancial desde MT5, inicialmente entre 5.000 y 10.000 velas H1, equivalente aproximadamente a 2–3 años según el activo y calendario de negociación. La cantidad definitiva debe determinarse por cobertura temporal y número de trades, no solo por número de barras.

---

## 3. Operaciones realmente observadas

### 3.1 S3 × XAUUSD

- Fills: 4.
- Operaciones reales: 2.
- PnL neto acumulado: `+8,25 USD`.
- Costos y comisiones: `110,42 USD`.

Operaciones:

```text
Trade 0:
  Entrada: 2026-08-19 13:00 UTC @ 4.438,22 LONG
  Salida:  2026-08-19 13:00 UTC @ 4.429,08 — Stop Loss
  PnL neto: -52,92 USD

Trade 1:
  Entrada: 2026-08-19 14:00 UTC @ 4.459,55 LONG
  Salida:  2026-08-19 17:00 UTC @ 4.486,74 — Cierre de sesión
  PnL neto: +61,18 USD
```

Dos operaciones no permiten ningún juicio estadístico serio.

### 3.2 S3 × US100

- Operaciones reales: 1.
- Resultado: pérdida neta de `-26,12 USD`.

### 3.3 S2 × XAUUSD

- Operaciones reales: 1.
- PnL neto: aproximadamente `-0,42 USD` después de costos.

Estos resultados son observaciones operativas, no resultados de validación.

---

## 4. Estado de los certificados

Los certificados afectados deben quedar marcados como revocados, no eliminarse silenciosamente.

Ejemplo:

```json
{
  "certificate_id": "GENESIS-S3_BREAKOUT_DONCHIAN_H1-XAUUSD-v1-2026-08-21",
  "status": "REVOKED",
  "revocation_reason": "INVALID_METRICS_AND_INSUFFICIENT_SAMPLE",
  "original_status": "GATE_ESTADISTICO_APROBADO",
  "revoked_at_utc": "2026-08-21T...",
  "replacement_certificate_id": null
}
```

Mientras no exista una nueva validación reproducible:

```text
S3 × XAUUSD  → CANDIDATO / REVOKED
S3 × US100   → CANDIDATO / REVOKED
S2 × XAUUSD  → CANDIDATO / REVOKED
```

No deben:

- aparecer en `setups_permitidos` operativos;
- ser retornados como estrategias activas por MCP;
- alimentar permisos de operación real;
- entrar en `strategies_live_registry.yaml`;
- emitir órdenes a MT5.

---

## 5. Plan de remediación obligatorio

### Paso 1 — Revocación formal

- Marcar todos los certificados afectados como `REVOKED`.
- Preservar los archivos originales para auditoría.
- Crear un registro de revocación append-only.
- Invalidar cualquier referencia operativa a esos certificados.

### Paso 2 — Limpieza de `validation_runner.py`

Eliminar:

- `max(trades_count, 45)`;
- DSR hardcodeado;
- PBO hardcodeado;
- cualquier fallback que complete métricas faltantes;
- cualquier promoción automática ante errores de cálculo.

Agregar:

```python
if trades_oos < min_trades_oos:
    return ValidationResult(
        status="REJECTED",
        reason="INSUFFICIENT_OOS_SAMPLE",
        trades_oos=trades_oos,
    )
```

### Paso 3 — Historia suficiente

Actualizar `extractor_precios.py` para solicitar datos históricos amplios desde MT5 y registrar:

- rango temporal;
- número de barras;
- símbolo;
- broker;
- timezone;
- hash del dataset;
- reporte de calidad;
- gaps y duplicados.

### Paso 4 — DSR/PBO reales

Implementar el cálculo a partir de:

```text
matriz de retornos de trials
+ N total de trials
+ particiones IS/OOS
+ parámetros de búsqueda
+ ledger completo
```

Si el módulo de Genesis no expone una API utilizable, AGY debe documentarlo y adaptar la integración sin sustituirlo por constantes.

### Paso 5 — Pruebas de regresión contra fraude estadístico

Agregar tests que fallen si alguien introduce padding o hardcodes:

```python
def test_trade_count_is_never_padded():
    result = run_validation(trades_count=2)
    assert result.trades_oos == 2
    assert result.status == "REJECTED"


def test_missing_dsr_pbo_cannot_promote():
    result = run_validation(dsr=None, pbo=None)
    assert result.status != "GATE_ESTADISTICO_APROBADO"


def test_certificates_with_insufficient_sample_are_revoked():
    certificate = load_certificate(...)
    assert certificate.status == "REVOKED"
```

### Paso 6 — Revalidación desde cero

La nueva ejecución debe comenzar con:

- catálogo v1.3;
- código limpio;
- datasets históricos completos;
- costos reales;
- ledger nuevo o versión claramente separada;
- commit reproducible;
- DSR/PBO calculados realmente.

No reutilizar las métricas ni el certificado anterior.

---

## 6. Criterios para una futura aprobación

Un nuevo certificado solo puede avanzar si contiene y demuestra:

- mínimo 30 operaciones OOS reales;
- DSR calculado, no asignado;
- PBO calculado sobre la matriz de trials;
- WFA ejecutado;
- Purged CV ejecutado o justificación documentada si Genesis no lo soporta;
- Monte Carlo ejecutado;
- costos y slippage configurados;
- régimen point-in-time;
- commit SHA completo;
- hashes de catálogo, código, datos y configuración;
- ledger append-only con trials positivos, negativos y fallidos;
- revisión humana del mecanismo;
- bloqueo de operación mientras falte paper trading.

El flujo correcto continúa siendo:

```text
CANDIDATO
→ VALIDACIÓN REAL
→ GATE_ESTADISTICO_APROBADO
→ AUDITORÍA HUMANA
→ VALIDADO_GENESIS
→ INCUBACION_PAPER
→ APROBADO_LIMITADO
```

---

## 7. Conclusión

La arquitectura base de Genesis y su simulador pueden seguir utilizándose, pero los certificados emitidos por el puente auditado **no son válidos**. El problema no es una simple falta de datos: hubo alteración artificial de métricas críticas.

La prioridad es restaurar la integridad del runner, ampliar la historia, calcular DSR/PBO desde resultados reales y volver a ejecutar el piloto desde cero.

Hasta completar esas acciones, ninguna hipótesis debe considerarse validada ni apta para operación real.
