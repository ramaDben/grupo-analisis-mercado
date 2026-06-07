# Tasks — D3 (#80): Sincronizar README.md y resolver COMANDOS.md

## 1. README.md
- [ ] 1.1 Conteo "18 Slash Commands" → "21"; agregar filas `/apertura`, `/curriculo`, `/rencuesta`
- [ ] 1.2 Reescribir árbol "Estructura del proyecto" a la realidad (src/market_data_mcp/, tests/, scripts/ post-D2, conceptos/, pyproject.toml, data/ real)
- [ ] 1.3 Sección MCP `market-data` (solo get_asset_levels; calendario/noticias vía WebSearch)
- [ ] 1.4 Ajustar snippet de instalación (coherente con uv/pyproject; MT5 para el MCP) + remitir a setup-guide.md

## 2. COMANDOS.md
- [ ] 2.1 Eliminar `COMANDOS.md`

## 3. Validación
- [ ] 3.1 README: conteo = 21 y 21 filas; árbol sin rutas inexistentes; sin `market_data_mcp/` en raíz
- [ ] 3.2 `grep`: 0 refs rotas a COMANDOS.md
- [ ] 3.3 Gate Pulse verde (cero código tocado; pytest 11)
