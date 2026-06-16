# Extractor de objetos MT5 — diseño (sub-proyecto A)

> Fecha: 2026-06-16 · Issue/feature: extractor de niveles dibujados a mano en MT5
> Branch: `feat/extractor-objetos-mt5`

## Contexto

Hoy `get_asset_levels` (`src/market_data_mcp/tools/levels.py`) calcula soportes/resistencias
de forma **automática** (swing highs/lows + clustering + proyección ATR). Eso ignora los
niveles que el director **dibuja a mano** en MetaTrader 5 (líneas horizontales, trendlines,
canales, rectángulos de zona), que son su lectura real del mercado.

La API de Python de MetaTrader5 **no puede** leer objetos de un gráfico ni tomar screenshots:
`ObjectsTotal`, `ObjectGetDouble`, `ChartScreenShot` solo existen dentro del terminal, en MQL5.
Se necesita un puente MQL5→archivo→Python.

**Objetivo**: que Claude use los niveles reales trazados por el director (no inventados), con un
screenshot del gráfico como contexto. Da valor inmediato en el flujo WhatsApp y es la primera
pieza (capa de datos) del roadmap de plataforma "cerebro como servicio".

Es parte de un roadmap mayor (A=datos, B=agente headless, C=API+caché+cola, E=deployment).
Solo A está en alcance aquí.

## Decisiones

- **Disparador**: componente MQL5 continuo en timer, instalado una vez (datos siempre frescos).
- **Implementado como `#property service`** (no EA por chart): un Service recorre todos los charts
  abiertos con `ChartFirst`/`ChartNext` y opera cada uno por su `chart_id`. Una sola instalación
  cubre todos los activos. Mismo patrón que el archivado `mql5/archive/CalendarExporter.mq5`.
- **Objetos exportados**: líneas horizontales, trendlines, canales (equidistant/stddev/regression),
  rectángulos de zona.
- **Screenshot**: el Service genera el PNG con `ChartScreenShot`. Como esa función solo escribe en
  `MQL5/Files` (sandbox local), el Service **copia** el PNG (binario) a `Common/Files`, de modo que
  una sola variable de config (`MT5_COMMON_FILES`) localiza tanto el JSON como los PNG.
- **Fuente intercambiable**: el lado Python ubica el archivo por `MT5_COMMON_FILES`, dejando la
  fuente MT5 swappable a futuro (VPS propio vs MT5 del broker).
- **Transporte**: archivo JSON único `chart_objects.json` en `Common/Files` (sin baja latencia,
  sobrevive si el Service muere). Reactiva la env var `MT5_COMMON_FILES` (hoy dormida en `.env.example`).

## Arquitectura

```
MT5 (terminal del director)
 └─ ChartObjectsExporter.mq5  (#property service, loop con Sleep)
      · ChartFirst/ChartNext → por cada chart: símbolo, TF, precio actual, digits
      · ObjectsTotal/ObjectGet* → hlines, trendlines, channels, rectangles
      · ChartScreenShot → PNG en MQL5/Files → copia binaria a Common/Files
      └─ escribe Common/Files/chart_objects.json
                                   │
                                   ▼
MCP market-data (Python)
 └─ tools/chart_objects.py → get_chart_objects(ticker, timeframe)
      · localiza el JSON vía MT5_COMMON_FILES; valida frescura (umbral 1 h)
      · filtra por symbol+TF; clasifica hlines en soporte/resistencia vs precio
      └─ dict estructurado + ruta del screenshot, con contrato de error explícito
```

## Componentes

### `mql5/ChartObjectsExporter.mq5`
`#property service` con `input int RefrescoSegundos = 60`. Reusa helpers `JsonEscape`/`FechaIso`
del precedente. Mapea cada tipo de objeto a su fragmento JSON; el slug del PNG sigue la convención
de charts (`lowercase(symbol)` sin `.spot`/`#`/`/`, CLAUDE.md #81) y el nombre incluye TF y fecha
`YYYY-MM-DD_HH-MM`. Para trendlines calcula `valor_actual` con `ObjectGetValueByTime` y la pendiente
por orden cronológico de las anclas. Para canales recolecta los valores de las líneas al tiempo
actual y asigna `banda_superior`/`banda_inferior` (max/min).

### `src/market_data_mcp/tools/chart_objects.py`
Tool `get_chart_objects(ticker, timeframe="H4")`. Reusa `market_data_mcp.catalog.VALID_TICKERS`
(extraído de `levels.py` a un módulo compartido para no duplicar el catálogo). Contrato de error:
`TICKER_NOT_FOUND`, `MT5_COMMON_FILES_UNSET`, `NO_OBJECTS_FILE`, `OBJECTS_UNREADABLE`,
`OBJECTS_STALE`, `CHART_NOT_FOUND`. Clasifica hlines: `price < current` → soporte (orden desc),
`price > current` → resistencia (orden asc), respetando `digits`. Devuelve también trendlines,
channels, rectangles, ruta absoluta del screenshot (o `None`) y `generated_at`.

### `src/market_data_mcp/catalog.py` (nuevo, compartido)
`load_valid_tickers()` / `VALID_TICKERS` movidos desde `levels.py`. `levels.py` los reimporta con
alias (`_load_valid_tickers`, `_VALID_TICKERS`) para no romper consumidores ni tests.

## Manejo de errores

| Situación | Respuesta |
|---|---|
| Ticker fuera del catálogo | `{error: "TICKER_NOT_FOUND"}` |
| `MT5_COMMON_FILES` sin setear | `{error: "MT5_COMMON_FILES_UNSET"}` |
| JSON ausente en `Common/Files` | `{error: "NO_OBJECTS_FILE", message: "...ejecutar ChartObjectsExporter"}` |
| JSON corrupto | `{error: "OBJECTS_UNREADABLE"}` |
| Dato > 1 h (Service caído) | `{error: "OBJECTS_STALE"}` |
| No hay chart de ese symbol+TF abierto | `{error: "CHART_NOT_FOUND", message: "abrir el gráfico…"}` |

## Testing

`tests/test_chart_objects.py` (patrón de `test_levels.py`, fixture `collector` + `tmp_path` +
`monkeypatch` de `MT5_COMMON_FILES`): ticker inválido, env var ausente, archivo ausente, dato
stale, chart inexistente, clasificación soporte/resistencia, paso de trendlines/canales/rectángulos,
TF case-insensitive y screenshot ausente → `None`. Regresión: suite completa de `levels`/`calendar`.

## Fuera de alcance

Integrar estos niveles dentro de `/apertura` y los comandos de día (se evalúa tras validar A en
vivo). Sub-proyectos B/C/E del roadmap de plataforma.
