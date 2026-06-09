# Spec: Indicadores clásicos completos en MCP market-data

**Fecha:** 2026-06-09
**Estado:** Aprobado — pendiente implementación
**Issue relacionado:** — (solicitado en sesión /martes)

---

## Contexto

El tool `get_asset_levels` del MCP `market-data` actualmente solo expone RSI 14 y ATR 14 en su respuesta. El comando `/apertura` ofrece 3 opciones de indicador: RSI, ATR y Limpio.

El director quiere ampliar el menú a 6 indicadores clásicos (RSI, ATR, EMA 50/100, MACD, Bollinger Bands) manteniendo la regla "un indicador por mensaje".

---

## Enfoque elegido

**Compute-all**: calcular los 5 indicadores en cada llamada a `get_asset_levels` y devolverlos todos en el JSON de respuesta. La apertura muestra solo el que el director eligió. Sin cambios en la firma del tool.

Justificación: el DataFrame ya se descarga (300 velas). Calcular 5 indicadores encima es O(n) adicional, prácticamente gratis. Evita complejidad de API (parámetros condicionales o tools separadas).

---

## Cambios por archivo

### 1. `src/market_data_mcp/mt5_client.py`

Agregar dos funciones nuevas junto a `ema()` y `atr()`:

**`macd(series, fast=12, slow=26, signal=9) → tuple[float, float, float]`**
- `macd_line = ema(series, fast) - ema(series, slow)`
- `signal_line = ema(macd_line, signal)`
- `histogram = macd_line - signal_line`
- Retorna `(macd_line[-1], signal_line[-1], histogram[-1])` como floats

**`bollinger(series, period=20, std=2) → tuple[float, float, float]`**
- `mid = series.rolling(period).mean()`
- `sigma = series.rolling(period).std()`
- `upper = mid + std * sigma`, `lower = mid - std * sigma`
- Retorna `(upper[-1], mid[-1], lower[-1])` como floats

Las EMAs no requieren función nueva — `ema(series, period)` ya existe y acepta cualquier período.

### 2. `src/market_data_mcp/tools/levels.py`

En `get_asset_levels`, tras descargar el DataFrame y antes del `return`:

```python
# EMA 50 (EMA 100 ya existe como ema100_val)
ema50_val = float(ema(close, 50).iloc[-1])

# MACD (12, 26, 9)
macd_l, macd_s, macd_h = macd(close)

# Bollinger Bands (20, 2)
bb_u, bb_m, bb_l = bollinger(close)
```

Campos nuevos en el dict de retorno (siempre presentes, nunca null):

| Campo | Tipo | Descripción |
|---|---|---|
| `ema_50` | float | EMA 50 redondeada a `digits` |
| `ema_100` | float | EMA 100 redondeada a `digits` (ya se calculaba; ahora se expone) |
| `macd_line` | float | Línea MACD, 4 decimales |
| `macd_signal` | float | Línea señal, 4 decimales |
| `macd_hist` | float | Histograma, 4 decimales |
| `bb_upper` | float | Banda alta, redondeada a `digits` |
| `bb_mid` | float | Banda media, redondeada a `digits` |
| `bb_lower` | float | Banda baja, redondeada a `digits` |

El campo `trend` sigue usando EMA 100 como referencia (sin cambio).

Mínimo de barras requerido: sube de 100 a **150** para garantizar datos suficientes para Bollinger (20) y MACD (slow=26 + signal=9 = 35 bars mínimo; con margen holgado, 150 es seguro).

### 3. `.claude/commands/apertura.md`

**PASO 3 — menú ampliado:**

```
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI        — sobrecompra/sobreventa
2. ATR        — volatilidad del marco
3. EMA 50/100 — tendencia por medias móviles
4. MACD       — momentum y cruces
5. Bollinger  — volatilidad y bandas de precio
6. Limpio     — solo niveles, sin indicador
```

Eliminar la nota `— Próximamente (requiere ampliar el MCP): MACD · SMA 50+200 · Bollinger` ya que todos quedan disponibles.

**PASO 4C — indicador (reutiliza resultado de 4A):**

Agregar extracción de los nuevos campos del JSON del MCP:
- EMA: `ema_50`, `ema_100`
- MACD: `macd_line`, `macd_signal`, `macd_hist`
- Bollinger: `bb_upper`, `bb_mid`, `bb_lower`

**PASO 5 — línea `{{lectura_indicador}}` ampliada:**

| Indicador | Línea generada |
|---|---|
| RSI | `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]` (sin cambio) |
| ATR | `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco` (sin cambio) |
| EMA 50/100 | `📐 EMA 50 [TF]: [val] \| EMA 100 [TF]: [val] — precio [sobre/bajo] ambas → *[Alcista/Bajista]* 🟢/🔴` o `📐 EMA 50/100 [TF]: precio entre ambas → *Esperar confirmación* 🟡` |
| MACD | `📐 MACD [TF]: línea [val] \| señal [val] \| hist [val] — [cruce alcista 🟢 / cruce bajista 🔴 / sin cruce 🟡]` |
| Bollinger | `📐 Bollinger [TF]: alta [val] \| media [val] \| baja [val] — precio [tocando banda alta/baja/en el centro]` |
| Limpio | *(omitir línea)* (sin cambio) |

Reglas de interpretación EMA:
- Precio > EMA 50 **y** precio > EMA 100 → `*Alcista* 🟢`
- Precio < EMA 50 **y** precio < EMA 100 → `*Bajista* 🔴`
- Precio entre EMA 50 y EMA 100 → `*Esperar confirmación* 🟡`

Reglas de interpretación MACD:
- `macd_hist > 0` (macd_line > signal_line) → `momentum alcista 🟢`
- `macd_hist < 0` (macd_line < signal_line) → `momentum bajista 🔴`
- `abs(macd_hist) < 0.0001 * precio` → `sin señal clara 🟡`

---

## Regla invariante

"Un aviso = un indicador" se mantiene. El menú pasa de 3 a 6 opciones pero el director elige uno por activo y el mensaje muestra solo esa línea `{{lectura_indicador}}`.

---

## Testing

- Tests unitarios para `macd()` y `bollinger()` en `src/market_data_mcp/mt5_client.py` (valores conocidos contra cálculo manual)
- Test de integración: mock de `get_rates` → verificar que todos los campos nuevos aparecen en el dict de retorno
- Smoke test manual: llamar `get_asset_levels("XAUUSD", "H1")` con MT5 activo y verificar que los 8 campos nuevos están presentes y son números válidos
