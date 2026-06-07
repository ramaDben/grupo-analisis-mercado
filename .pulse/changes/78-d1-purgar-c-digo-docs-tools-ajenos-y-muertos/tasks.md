# Tareas — D1 (#78)

- [ ] T1. Borrar `market_data_mcp/tools/calendar.py` y `market_data_mcp/tools/context.py`.
- [ ] T2. Editar `market_data_mcp/server.py`: import sin `calendar, context`; quitar sus `.register()`; `instructions=` → "1 tool: get_asset_levels".
- [ ] T3. Borrar `market_data_mcp/tests/test_deprecated_tools.py`.
- [ ] T4. Borrar `docs/design/refactorizacion.design.md` y `docs/ideas/refactorizacion-proyecto.idea.md`.
- [ ] T5. Editar `.claude/commands/estado.md` línea 42 (MCP market-data → solo get_asset_levels).
- [ ] T6. Editar `CLAUDE.md` nota MCP (deprecadas → eliminadas en #78).
- [ ] T7. `pytest market_data_mcp/tests/` verde + grep sin referencias en comandos.
