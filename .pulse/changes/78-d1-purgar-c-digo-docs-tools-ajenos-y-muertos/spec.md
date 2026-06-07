# Spec — D1 (#78)

## Resultado esperado
- El MCP `market-data` expone **solo** `get_asset_levels`.
- No queda código que devuelva `DEPRECATED` ni docs que recomienden el MCP ajeno `reporte-flash`.
- `pytest market_data_mcp/tests/` pasa en verde.
- Ningún `.claude/commands/*.md` referencia `get_economic_events` ni `get_market_context`.

## No-objetivos
- No se toca la lógica de `levels.py` ni `mt5_client.py`.
- No se reescriben `docs/architecture.md`, `docs/setup-guide.md`, `docs/design/decomposition.md` (→ D3/A5).

Detalle de archivos y líneas en `design.md`.
