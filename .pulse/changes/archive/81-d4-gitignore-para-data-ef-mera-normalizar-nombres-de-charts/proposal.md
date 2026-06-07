# Propuesta — D4 (#81): .gitignore efímera + convención de charts

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Why
`data/` debe versionar solo estado persistente (historiales, currículo, métricas). El estado efímero de runtime no debe ensuciar el repo. Y los charts necesitan un nombre predecible y consistente con el resto del sistema.

## What Changes
- **`.gitignore`**: agregar el efímero faltante (`data/mt5_response.json`) y, propuesto, el runtime de Pulse (`.pulse/state.sqlite*`, `.pulse/audit.jsonl`) que ensucia `git status` cada sesión.
- **Convención de charts**: `data/charts/<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`, con el mismo `activo_slug` de `ruta_mensaje.ps1` (#45). Documentar en `chart.md` + `CLAUDE.md`.

## Hallazgo
El criterio "quitar del índice los ya versionados" **ya está cumplido**: ningún JSON efímero está trackeado (los 6 `data/*.json` trackeados son persistentes). Solo falta `mt5_response.json` en `.gitignore` (aún no existe como archivo).
