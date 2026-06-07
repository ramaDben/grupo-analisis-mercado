# Propuesta — D2 (#79): Resolver scripts Python huérfanos

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Why
`scripts/` acumula 6 scripts que ningún comando invoca ya. Son ruido: confunden sobre cuál es la vía vigente (MCP + slash commands + helpers `.ps1`) y arrastran deps muertas (yfinance, mplfinance, pandas_ta).

## What Changes
Auditar los 8 `.py` de `scripts/`, clasificar cada uno como **eliminar** o **conservar** según uso real (invocación por comandos + dependencias intra-`scripts/`), y sincronizar las referencias en comandos/docs para que ninguna apunte a un archivo borrado. El gate de cierre sigue verde: ningún linter del gate targetea `scripts/` (ruff lo excluye; el resto apunta a `src/`/`tests/`).
