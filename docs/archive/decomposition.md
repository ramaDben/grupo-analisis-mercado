# Decomposition — WebSearch (investing.com) para calendario y noticias

Descomposición de tareas para la fase **apply**. Basado en `docs/design/websearch-calendario-noticias.design.md` e issue #10. Decisión: Opción A.

## Tareas

### T1 — `/dato_macro`: PASO 1 a WebSearch
- **Archivo**: `.claude/commands/dato_macro.md`
- **Cambio**: reemplazar la llamada a `mcp__market-data__get_economic_events` por `WebSearch` (investing.com; países CL/US/EU/CN; impacto medio/alto; hora convertida a Chile) con `WebFetch` de respaldo.
- **Contrato sin-resultados**: si no hay eventos → mensaje "Sin datos macro hoy" + DETENER.
- **Invariante**: PASOS 2–5 no cambian.
- **Dependencias**: ninguna.

### T2 — `/noticia`: PASO 1 a WebSearch
- **Archivo**: `.claude/commands/noticia.md`
- **Cambio**: reemplazar `mcp__market-data__get_market_context` por `WebSearch` con el orden de prioridad documentado + fuentes oficiales (Fed, BCCh, OPEP+, EIA, BLS). Filtro de relevancia por catálogo; frescura últimas ~4–24 h.
- **Contrato sin-resultados**: si no hay noticias relevantes → informar + DETENER.
- **Invariante**: PASOS 2–5 no cambian.
- **Dependencias**: ninguna.

### T3 — Deprecar tools del MCP
- **Archivos**: `market_data_mcp/tools/calendar.py`, `market_data_mcp/tools/context.py`
- **Cambio**: hacer que ambas tools devuelvan `{"error": "DEPRECATED", "message": "Usar WebSearch en /dato_macro y /noticia"}`. No eliminar el código aún.
- **Dependencias**: ninguna (independiente de T1/T2).

### T4 — Redirigir comandos de día
- **Archivos**: `domingo.md`, `lunes.md`, `martes.md`, `miercoles.md`, `jueves.md`, `viernes_am.md`, `viernes_pm.md`
- **Cambio**: donde llamen calendario/noticias del MCP, redirigir al flujo de `/dato_macro` y `/noticia`.
- **Dependencias**: T1, T2.

### T5 — Documentación
- **Archivos**: `CLAUDE.md`, `docs/architecture.md`
- **Cambio**: actualizar tabla de MCP y flujo: calendario y noticias ya no son responsabilidad del MCP `market-data`.
- **Dependencias**: T1–T4.

### T6 — Validación manual
- Día con datos macro / día sin datos (fin de semana) / noticia de alto impacto.
- **Dependencias**: T1–T5.

## Orden de ejecución
T1 ∥ T2 ∥ T3 (independientes) → T4 → T5 → T6.

## Fuera de alcance
`get_asset_levels` (MT5), conexión WhatsApp, eliminación definitiva de código Finnhub.
