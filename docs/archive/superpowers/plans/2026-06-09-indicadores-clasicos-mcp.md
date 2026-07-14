# Indicadores Clásicos Completos en MCP market-data — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ampliar `get_asset_levels` para que devuelva EMA 50/100, MACD y Bollinger Bands, y actualizar `/apertura` para ofrecer los 6 indicadores clásicos en su menú.

**Architecture:** Compute-all: el DataFrame se descarga una sola vez; se calculan todos los indicadores encima sin cambiar la firma del tool. Los campos nuevos siempre están presentes en la respuesta.

**Tech Stack:** Python 3.11, pandas, pytest, FastMCP · Markdown (apertura.md)

---

## Archivos que cambian

| Acción | Archivo |
|---|---|
| Modificar | `src/market_data_mcp/mt5_client.py` — agregar `macd()` y `bollinger()` |
| Modificar | `src/market_data_mcp/tools/levels.py` — exponer 8 campos nuevos, mínimo 150 barras |
| Modificar | `tests/test_levels.py` — tests nuevos + actualizar test de camino feliz |
| Modificar | `.claude/commands/apertura.md` — menú 6 opciones + render template |

---

## Task 1: Agregar `macd()` y `bollinger()` a `mt5_client.py`

**Files:**
- Modify: `src/market_data_mcp/mt5_client.py`
- Test: `tests/test_levels.py`

- [ ] **Step 1: Escribir los tests de las funciones nuevas**

Al final de `tests/test_levels.py`, antes del bloque de camino feliz, agregar:

```python
# --- macd() y bollinger() (mt5_client) ---

def test_macd_serie_creciente_hist_positivo():
    """Con serie creciente la línea MACD > señal → histograma positivo."""
    from market_data_mcp import mt5_client
    serie = pd.Series(range(1, 101), dtype="float64")
    macd_l, macd_s, macd_h = mt5_client.macd(serie)
    assert isinstance(macd_l, float)
    assert isinstance(macd_s, float)
    assert isinstance(macd_h, float)
    assert macd_h > 0, "serie creciente → histograma positivo"


def test_macd_serie_decreciente_hist_negativo():
    from market_data_mcp import mt5_client
    serie = pd.Series(range(100, 0, -1), dtype="float64")
    _, _, macd_h = mt5_client.macd(serie)
    assert macd_h < 0, "serie decreciente → histograma negativo"


def test_bollinger_upper_mayor_que_lower():
    from market_data_mcp import mt5_client
    rng = np.random.default_rng(7)
    serie = pd.Series(100 + rng.standard_normal(60).cumsum())
    bb_u, bb_m, bb_l = mt5_client.bollinger(serie)
    assert isinstance(bb_u, float) and isinstance(bb_m, float) and isinstance(bb_l, float)
    assert bb_u > bb_m > bb_l, "upper > mid > lower siempre"


def test_bollinger_banda_media_es_sma():
    """La banda media debe coincidir con la SMA de los últimos `period` valores."""
    from market_data_mcp import mt5_client
    serie = pd.Series(range(1, 41), dtype="float64")  # 40 valores, period=20
    _, bb_m, _ = mt5_client.bollinger(serie, period=20)
    sma_manual = float(serie.iloc[-20:].mean())
    assert abs(bb_m - sma_manual) < 1e-9
```

- [ ] **Step 2: Ejecutar los tests y verificar que fallan**

```
pytest tests/test_levels.py::test_macd_serie_creciente_hist_positivo tests/test_levels.py::test_macd_serie_decreciente_hist_negativo tests/test_levels.py::test_bollinger_upper_mayor_que_lower tests/test_levels.py::test_bollinger_banda_media_es_sma -v
```

Salida esperada: 4 × `FAILED` con `AttributeError: module 'market_data_mcp.mt5_client' has no attribute 'macd'`

- [ ] **Step 3: Implementar `macd()` y `bollinger()` en `mt5_client.py`**

En `src/market_data_mcp/mt5_client.py`, después de la función `atr()` (línea ~119), agregar:

```python
def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float, float, float]:
    """MACD estándar (12, 26, 9). Retorna (macd_line, signal_line, histogram) del último bar."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


def bollinger(
    series: pd.Series,
    period: int = 20,
    std: int = 2,
) -> tuple[float, float, float]:
    """Bandas de Bollinger (20, 2). Retorna (upper, mid, lower) del último bar."""
    mid = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    upper = mid + std * sigma
    lower = mid - std * sigma
    return float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])
```

- [ ] **Step 4: Ejecutar los tests y verificar que pasan**

```
pytest tests/test_levels.py::test_macd_serie_creciente_hist_positivo tests/test_levels.py::test_macd_serie_decreciente_hist_negativo tests/test_levels.py::test_bollinger_upper_mayor_que_lower tests/test_levels.py::test_bollinger_banda_media_es_sma -v
```

Salida esperada: 4 × `PASSED`

- [ ] **Step 5: Ejecutar suite completa para verificar que no hay regresiones**

```
pytest tests/ -v
```

Salida esperada: todos los tests existentes siguen en `PASSED`.

- [ ] **Step 6: Commit**

```
git add src/market_data_mcp/mt5_client.py tests/test_levels.py
git commit -m "feat(mcp): agregar macd() y bollinger() a mt5_client"
```

---

## Task 2: Exponer todos los indicadores en `get_asset_levels`

**Files:**
- Modify: `src/market_data_mcp/tools/levels.py`
- Test: `tests/test_levels.py`

- [ ] **Step 1: Actualizar `test_ticker_valido_nunca_devuelve_none_ni_lanza` para incluir nuevas claves**

En `tests/test_levels.py`, en la función `test_ticker_valido_nunca_devuelve_none_ni_lanza`, reemplazar la línea del assert de camino feliz:

```python
# Antes (línea ~86):
        for k in ("price", "s1", "s2", "r1", "r2", "rsi_14", "atr_14", "trend", "timestamp"):
            assert k in res

# Después:
        for k in (
            "price", "s1", "s2", "r1", "r2", "rsi_14", "atr_14", "trend", "timestamp",
            "ema_50", "ema_100",
            "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_mid", "bb_lower",
        ):
            assert k in res
```

- [ ] **Step 2: Agregar assertions al test de camino feliz mockeado**

En `test_camino_feliz_con_mt5_mockeado`, después del bloque final `# Serie con deriva alcista`, agregar:

```python
    # Campos nuevos siempre presentes y con tipos correctos
    for k in ("ema_50", "ema_100", "bb_upper", "bb_mid", "bb_lower"):
        assert k in res, f"falta campo {k}"
        assert isinstance(res[k], float), f"{k} debe ser float"
        assert res[k] > 0, f"{k} debe ser positivo"

    for k in ("macd_line", "macd_signal", "macd_hist"):
        assert k in res, f"falta campo {k}"
        assert isinstance(res[k], float), f"{k} debe ser float"

    # EMA 50 > EMA 100 en serie con deriva alcista fuerte
    assert res["ema_50"] >= res["ema_100"], "EMA rápida >= EMA lenta en tendencia alcista"

    # Bollinger: upper > mid > lower
    assert res["bb_upper"] > res["bb_mid"] > res["bb_lower"]
```

- [ ] **Step 3: Agregar test de umbral mínimo 150 barras**

Al final de `tests/test_levels.py` agregar:

```python
def test_insuficientes_datos_umbral_150(collector, monkeypatch):
    """El umbral mínimo de barras es 150 (suficiente para MACD + Bollinger)."""
    from market_data_mcp import mt5_client

    df_corto = _df_ohlc(n=149)  # 1 bar por debajo del umbral
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df_corto)

    levels.register(collector)
    res = collector.tools["get_asset_levels"](ticker="XAUUSD", timeframe="H4")

    assert res["error"] == "INSUFFICIENT_DATA"
    assert "150" in res["message"]
```

- [ ] **Step 4: Ejecutar los tests nuevos y verificar que fallan**

```
pytest tests/test_levels.py::test_ticker_valido_nunca_devuelve_none_ni_lanza tests/test_levels.py::test_camino_feliz_con_mt5_mockeado tests/test_levels.py::test_insuficientes_datos_umbral_150 -v
```

Salida esperada: los 3 tests fallan porque `ema_50`, `ema_100`, etc. aún no están en el dict de retorno y el umbral sigue siendo 100.

- [ ] **Step 5: Actualizar `levels.py`**

**5a.** Cambiar el umbral mínimo de barras (línea ~180):

```python
# Antes:
        if len(df) < 100:
            return {
                "error": "INSUFFICIENT_DATA",
                "message": f"Solo {len(df)} velas disponibles para {ticker} {timeframe}. Mínimo requerido: 100.",
            }

# Después:
        if len(df) < 150:
            return {
                "error": "INSUFFICIENT_DATA",
                "message": f"Solo {len(df)} velas disponibles para {ticker} {timeframe}. Mínimo requerido: 150.",
            }
```

**5b.** Actualizar el import interno de mt5_client (línea ~145):

```python
# Antes:
            from market_data_mcp.mt5_client import get_rates, ema, atr, TIMEFRAME_MAP

# Después:
            from market_data_mcp.mt5_client import get_rates, ema, atr, macd, bollinger, TIMEFRAME_MAP
```

**5c.** Agregar cálculo de indicadores nuevos después de `ema100_val` (líneas ~187-188):

```python
        # Antes:
        close = df["close"]
        ema100_val = float(ema(close, 100).iloc[-1])
        atr14_val = float(atr(df, 14).iloc[-1])
        current = float(close.iloc[-1])

        # Después:
        close = df["close"]
        ema100_val = float(ema(close, 100).iloc[-1])
        ema50_val  = float(ema(close, 50).iloc[-1])
        atr14_val  = float(atr(df, 14).iloc[-1])
        macd_l, macd_s, macd_h = macd(close)
        bb_u, bb_m, bb_l = bollinger(close)
        current = float(close.iloc[-1])
```

**5d.** Actualizar el dict de retorno para incluir los campos nuevos:

```python
        return {
            "ticker":       ticker,
            "timeframe":    timeframe.upper(),
            "price":        round(current, digits),
            "s2":           levels["s2"],
            "s1":           levels["s1"],
            "r1":           levels["r1"],
            "r2":           levels["r2"],
            "rsi_14":       round(rsi14_val, 1),
            "atr_14":       round(atr14_val, digits),
            "ema_50":       round(ema50_val, digits),
            "ema_100":      round(ema100_val, digits),
            "macd_line":    round(macd_l, 4),
            "macd_signal":  round(macd_s, 4),
            "macd_hist":    round(macd_h, 4),
            "bb_upper":     round(bb_u, digits),
            "bb_mid":       round(bb_m, digits),
            "bb_lower":     round(bb_l, digits),
            "trend":        trend,
            "timestamp":    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
```

- [ ] **Step 6: Ejecutar los tests actualizados y verificar que pasan**

```
pytest tests/test_levels.py -v
```

Salida esperada: todos los tests en `PASSED`, incluyendo los 3 nuevos.

- [ ] **Step 7: Ejecutar suite completa**

```
pytest tests/ -v
```

Salida esperada: todos los tests en `PASSED`.

- [ ] **Step 8: Commit**

```
git add src/market_data_mcp/tools/levels.py tests/test_levels.py
git commit -m "feat(mcp): exponer ema_50/100, macd_*, bb_* en get_asset_levels"
```

---

## Task 3: Actualizar `/apertura` con menú de 6 indicadores

**Files:**
- Modify: `.claude/commands/apertura.md`

No hay tests unitarios para archivos Markdown. La validación es visual: ejecutar `/apertura` al terminar.

- [ ] **Step 1: Actualizar el menú del PASO 3**

Reemplazar el bloque completo del menú en PASO 3 (el bloque de código con las 3 opciones + nota "Próximamente"):

```markdown
# Antes:
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI    — sobrecompra/sobreventa
2. ATR    — volatilidad (útil en USD/CLP)
3. Limpio — solo niveles, sin indicador
— Próximamente (requiere ampliar el MCP): MACD · SMA 50+200 · Bollinger

Si el director elige una opción "Próximamente" (MACD/SMA/Bollinger), responde:
`Ese indicador aún no está en el MCP. Por ahora elige RSI, ATR o Limpio.` y vuelve a preguntar. No falles.

# Después:
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI        — sobrecompra/sobreventa
2. ATR        — volatilidad del marco
3. EMA 50/100 — tendencia por medias móviles
4. MACD       — momentum y cruces
5. Bollinger  — volatilidad y bandas de precio
6. Limpio     — solo niveles, sin indicador
```

Eliminar también el párrafo que empieza con "Si el director elige una opción 'Próximamente'..." ya que todas las opciones están disponibles.

- [ ] **Step 2: Actualizar el PASO 4C para extraer los campos nuevos del JSON**

En el bloque del PASO 4C, donde dice "extraer `rsi_14` (RSI) o `atr_14` (ATR) de ese mismo resultado", ampliar:

```markdown
- Si el resultado de 4A fue exitoso: extraer del resultado según el indicador elegido:
  - RSI → `rsi_14`
  - ATR → `atr_14`
  - EMA 50/100 → `ema_50`, `ema_100`
  - MACD → `macd_line`, `macd_signal`, `macd_hist`
  - Bollinger → `bb_upper`, `bb_mid`, `bb_lower`
```

- [ ] **Step 3: Actualizar la tabla de `{{lectura_indicador}}` en PASO 5**

Reemplazar la tabla de 2 filas (RSI y ATR) con la tabla de 6 filas:

```markdown
| Indicador | Línea `{{lectura_indicador}}` |
|---|---|
| RSI | `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]` |
| ATR | `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco` |
| EMA 50/100 | Ver reglas abajo |
| MACD | Ver reglas abajo |
| Bollinger | `📐 Bollinger [TF]: banda alta [bb_upper] \| media [bb_mid] \| baja [bb_lower] — precio [tocando banda alta / baja / en el centro]` |
| Limpio | *(omitir línea completa)* |
```

Agregar después de la tabla las reglas de interpretación:

```markdown
**Reglas EMA 50/100:**
- Precio > ema_50 Y precio > ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio sobre ambas → *Alcista* 🟢`
- Precio < ema_50 Y precio < ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio bajo ambas → *Bajista* 🔴`
- Precio entre ema_50 y ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio entre ambas → *Esperar confirmación* 🟡`

**Reglas MACD:**
- macd_hist > 0 → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — momentum *Alcista* 🟢`
- macd_hist < 0 → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — momentum *Bajista* 🔴`
- abs(macd_hist) < 0.0001 × precio → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — *Sin señal clara* 🟡`
```

- [ ] **Step 4: Commit**

```
git add .claude/commands/apertura.md
git commit -m "feat(apertura): menu 6 indicadores (EMA 50/100, MACD, Bollinger)"
```

---

## Verificación final

- [ ] Ejecutar `pytest tests/ -v` y confirmar que todos los tests pasan
- [ ] Invocar `/apertura` con un activo real (ej. XAUUSD en H1) y elegir EMA 50/100 → verificar que el mensaje incluye la línea `📐 EMA 50 H1: ... | EMA 100 H1: ...`
- [ ] Repetir con MACD y con Bollinger
