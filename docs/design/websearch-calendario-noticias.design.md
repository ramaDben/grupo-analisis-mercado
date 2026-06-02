# DISEÑO TÉCNICO — WebSearch (investing.com) para calendario económico y noticias

## Contexto
Basado en el issue de Discovery [#10](https://github.com/bbenja11/grupo-analisis-mercado/issues/10).
Decisión del director: **Opción A** — sacar calendario y noticias del MCP `market-data` y resolverlos en el agente (Claude) con `WebSearch` + `WebFetch`.

Finnhub está produciendo errores de **temporalidad** (fechas/horas desfasadas) y **atingencia** (noticias no relacionadas con el catálogo). El MCP Python no puede invocar `WebSearch` (esa herramienta vive en el agente), por lo que la lógica se mueve a los slash commands.

`mcp__market-data__get_asset_levels` (técnico MT5) **NO se toca**.

---

## Hallazgos clave

- `get_economic_events` (`market_data_mcp/tools/calendar.py`) y `get_market_context` (`market_data_mcp/tools/context.py`) son las únicas tools que dependen de Finnhub vía `mt5_client`.
- Consumidores directos del calendario/noticias: `/dato_macro`, `/noticia`, y los paquetes de día (`martes`–`viernes_pm`, `domingo`, `lunes`).
- investing.com es JS-pesada: `WebFetch` directo de la tabla del calendario puede no renderizar. Estrategia: `WebSearch` con query acotada + `WebFetch` como respaldo, y fuentes oficiales para datos críticos.
- El contrato de error explícito (`{"error": CÓDIGO}`) deja de aplicar a estas dos fuentes; se reemplaza por manejo de "sin resultados" desde la búsqueda.

---

## Cambios por área

### ÁREA A — `/dato_macro` (calendario económico)

**Antes**: PASO 1 llama `mcp__market-data__get_economic_events {days_ahead, min_impact}` y valida contrato Finnhub.

**Después**: PASO 1 usa `WebSearch` contra investing.com.

- **Query base**: `investing.com calendario económico hoy [FECHA] Chile Estados Unidos Zona Euro China impacto alto`.
- **Respaldo**: `WebFetch` a `https://es.investing.com/economic-calendar/` para confirmar horas exactas; si no renderiza, usar resultados de `WebSearch` + fuentes oficiales (BCCh, Fed, Eurostat, BLS).
- **Filtros a aplicar en el prompt**:
  - Países: CL, US, EU, CN.
  - Impacto: medio y alto (★★ / ★★★).
  - Conversión de hora a **Chile (CLT/CLST)** — explicitar la zona origen del dato y convertir.
- **Manejo de "sin resultados"**: si la búsqueda no devuelve eventos relevantes para hoy → mostrar "📅 Sin datos macro de impacto medio/alto hoy" y DETENER (equivalente al antiguo `NO_EVENTS_FOUND`). Fin de semana/feriado = comportamiento esperado.
- PASOS 2–5 (lista numerada, mensaje WhatsApp anticipación/resultado, aprobación, encuesta post-evento) **se mantienen sin cambios**.

### ÁREA B — `/noticia` (noticias relevantes)

**Antes**: PASO 1 llama `mcp__market-data__get_market_context {within_hours, category}`.

**Después**: PASO 1 usa `WebSearch` con el orden de prioridad ya documentado.

- **Fuentes**: investing.com **+ fuentes oficiales** (Fed, BCCh, OPEP/OPEP+, EIA, BLS) para máxima atingencia y temporalidad.
- **Queries por prioridad** (tal como ya define el comando):
  1. Bancos centrales (Fed, BCCh, BCE, tasas, discursos).
  2. Datos macro sorpresivos (IPC, NFP, PCE, PMI fuera de consenso).
  3. Geopolítica que afecte commodities.
  4. Earnings tech (NVDA, AAPL, MSFT, AMZN).
  5. OPEP+ (producción → WTI).
  6. Flujos / divisa.
- **Filtro de relevancia**: limitar a activos del catálogo (USD/CLP, Oro, WTI, US100/US500/US30, 12 acciones) y sus drivers. Reemplaza al `_RELEVANCE_KEYWORDS` de `context.py`.
- **Frescura**: priorizar noticias de las últimas ~4–24 h (campo de fecha del resultado); descartar lo viejo.
- **Manejo de "sin resultados"**: si no hay noticias relevantes recientes → informar y DETENER (equivalente a `NO_NEWS_FOUND`).
- PASOS 2–5 **se mantienen**.

### ÁREA C — Limpieza del MCP `market-data`

- **Deprecar (no eliminar aún)** `get_economic_events` y `get_market_context`: mantener como fallback durante una transición, devolviendo un error `DEPRECATED` que apunte a usar WebSearch. Decisión final de eliminación tras validar en producción 1 semana.
- `mt5_client.get_upcoming_events` / `get_news` y `FINNHUB_API_KEY`: marcar como deprecados; no removerlos hasta confirmar que ningún comando los invoca.
- Actualizar la descripción del MCP (`server.py` / docstrings) para reflejar que calendario y noticias ya no son responsabilidad del MCP.
- Actualizar `CLAUDE.md` (tabla de MCP y flujo) y `docs/architecture.md`.

### ÁREA D — Comandos de día

Revisar `domingo`, `lunes`, `martes`, `miercoles`, `jueves`, `viernes_am`, `viernes_pm`: donde llamen `get_economic_events` / `get_market_context`, redirigir al nuevo flujo WebSearch (idealmente referenciando los PASOS de `/dato_macro` y `/noticia` para no duplicar lógica).

---

## Contrato de "sin resultados" (reemplazo del contrato de error Finnhub)

| Situación | Antes (Finnhub) | Después (WebSearch) |
|-----------|-----------------|---------------------|
| No hay eventos hoy | `{"error":"NO_EVENTS_FOUND"}` | Mensaje "Sin datos macro hoy" + DETENER |
| No hay noticias | `{"error":"NO_NEWS_FOUND"}` | Mensaje "Sin noticias relevantes" + DETENER |
| Fuente caída | `{"error":"FINNHUB_UNAVAILABLE"}` | Reintentar query alterna / fuente oficial; si todo falla, informar y DETENER |

---

## Riesgos y mitigaciones

- **investing.com bloquea/no renderiza** → mitigar con `WebSearch` (no scraping directo) + fuentes oficiales para datos críticos.
- **Horas mal convertidas a Chile** → regla explícita en el prompt: identificar zona origen y convertir a CLT/CLST; verificar contra fuente oficial en datos de alto impacto (Fed, BCCh, NFP).
- **Pérdida de estructura tabular** → el prompt arma la lista numerada; no se depende de parseo automático.

---

## Fuera de alcance

- `get_asset_levels` (MT5) y toda la lógica de niveles técnicos.
- Conexión WhatsApp/Evolution API.
- Eliminación definitiva del código Finnhub (se difiere hasta validación).

---

## Plan de implementación (fase apply)

1. Reescribir PASO 1 de `.claude/commands/dato_macro.md` (WebSearch + manejo sin-resultados).
2. Reescribir PASO 1 de `.claude/commands/noticia.md` (WebSearch + fuentes oficiales).
3. Redirigir llamadas en los comandos de día (ÁREA D).
4. Deprecar tools en `calendar.py` / `context.py` con error `DEPRECATED`.
5. Actualizar `CLAUDE.md` y `docs/architecture.md`.
6. Validar manualmente: día con datos macro, día sin datos (fin de semana), noticia de alto impacto.
