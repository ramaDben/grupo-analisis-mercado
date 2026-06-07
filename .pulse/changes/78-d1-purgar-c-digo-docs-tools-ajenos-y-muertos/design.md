# Diseño — D1 (#78): Purgar código/docs/tools ajenos y muertos

**Épico:** #66 (Higiene y saneamiento del repo) · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Contexto verificado (2026-06-07)
La auditoría origen (2026-06-05) estaba parcialmente desactualizada. Estado real comprobado:
- `flash_mcp/` **ya no está trackeado** y está cubierto por `.gitignore` → sin acción.
- `market_data_mcp/tools/calendar.py` y `context.py` existen y **solo devuelven `{"error":"DEPRECATED"}`**.
- `market_data_mcp/server.py` los importa y registra; el string `instructions=` anuncia "3 tools".
- `market_data_mcp/tests/test_deprecated_tools.py` importa ambos módulos para congelar el contrato DEPRECATED.
- `docs/design/refactorizacion.design.md` y `docs/ideas/refactorizacion-proyecto.idea.md` proponen migrar al MCP `reporte-flash` (ajeno) → obsoletos.

## Cambios

### Núcleo
1. **Borrar** `market_data_mcp/tools/calendar.py` y `market_data_mcp/tools/context.py`.
2. **`market_data_mcp/server.py`**: quitar `calendar, context` del import y sus `.register(mcp)`; actualizar `instructions=` de "3 tools" a "1 tool: get_asset_levels".
3. **Borrar** `market_data_mcp/tests/test_deprecated_tools.py` (importa los módulos borrados; el guardián anti-regresión-Finnhub queda sin objeto al eliminar el código legacy).
4. **Borrar** `docs/design/refactorizacion.design.md` (obsoleto — reporte-flash ajeno).
5. **Borrar** `docs/ideas/refactorizacion-proyecto.idea.md` (decisión (a): spec origen cerrado, mismo enfoque ajeno).

### Consistencia mínima
6. **`.claude/commands/estado.md`** (línea 42): reescribir la línea del MCP `market-data` → solo `get_asset_levels`; calendario/noticias vía WebSearch.
7. **`CLAUDE.md`** (nota, línea ~193): "están deprecadas (devuelven DEPRECATED)" → "fueron eliminadas (#78)".

### Fuera de alcance (decisión (b))
`docs/architecture.md`, `docs/setup-guide.md`, `docs/design/decomposition.md` mencionan los tools deprecados pero son docs (no comandos) → se sincronizan en D3/A5.

## Verificación
- `pytest market_data_mcp/tests/` verde (test_levels.py y test_server.py no dependen de los módulos borrados).
- `grep` confirma que ningún `.claude/commands/*.md` referencia `get_economic_events` / `get_market_context`.

## Criterios de aceptación (#78)
- [ ] `flash_mcp/` fuera del árbol versionado (ya cumplido).
- [ ] `refactorizacion.design.md` eliminado.
- [ ] `calendar.py` y `context.py` eliminados; `server.py` no los registra; tests ajustados.
- [ ] Ningún comando referencia tools muertas.
