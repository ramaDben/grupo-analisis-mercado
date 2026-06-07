# Propuesta — D1 (#78)

Purga en dos planos:
1. **Código MCP muerto**: borrar `tools/calendar.py` + `tools/context.py` + `tests/test_deprecated_tools.py`; desregistrar en `server.py` y corregir su `instructions=` ("3 tools" → "1 tool").
2. **Docs obsoletos**: borrar `refactorizacion.design.md` + `refactorizacion-proyecto.idea.md` (proponen migrar al ajeno `reporte-flash`).

Consistencia: actualizar el comando `/estado` y la nota del MCP en `CLAUDE.md`. Docs mayores (architecture/setup-guide/decomposition) → diferidos a D3/A5.
