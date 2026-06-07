# Propuesta — D3 (#80): Sincronizar README.md y resolver COMANDOS.md

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Why
La documentación de entrada (`README.md`) miente sobre el estado del proyecto: conteo de comandos erróneo, estructura previa a `src/` (#86) y a la purga de scripts (D2). `COMANDOS.md` es un doc huérfano (nadie lo enlaza) que contradice activamente la operativa real.

## What Changes
- **`README.md`**: conteo y tabla de comandos al valor real (**21**, verificado por archivos en `.claude/commands/`), árbol de estructura real (`src/market_data_mcp/`, `tests/`, `scripts/` post-D2, `conceptos/`, `data/`, `.pulse/`), sección MCP `market-data`, e instalación coherente con el toolchain actual.
- **`COMANDOS.md`**: **eliminar** (huérfano + contradictorio; `CLAUDE.md` y `docs/commands-reference.md` ya cubren los comandos).

## Riesgos
- Conteo: el issue dice "24" pero el real es **21** → se documenta la corrección.
- Cero código tocado → gate de cierre intacto.
