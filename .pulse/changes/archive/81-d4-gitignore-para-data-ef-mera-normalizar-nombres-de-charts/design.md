# Diseño — D4 (#81): .gitignore efímera + convención de charts

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Estado verificado (2026-06-07)
- **Trackeado en `data/`**: solo persistentes → `curriculo.json`, `entregas_educativas.json`, `historial_encuestas.json`, `historial_senales.json`, `mapa_conceptos.json`, `metricas_educativas.json`. **Se conservan.**
- **Efímeros ya gitignored y NO trackeados**: `plan_hoy.json`, `datos_entregables.json`, `ultimo_analisis.json`, `ultimo_evento.json`, `mt5_command.json`. → El criterio "quitar del índice" ya está cumplido; nada que destrackear.
- **Falta en `.gitignore`**: `data/mt5_response.json` (respuesta del EA; aún no existe como archivo).
- **`.pulse/` runtime** (`state.sqlite`, `state.sqlite-shm/-wal`, `audit.jsonl`): untracked, ensucia `git status` cada sesión.
- **Slug de activo canónico** (`ruta_mensaje.ps1`, #45): `lowercase(ticker_mt5)` quitando `.spot`, `#`, `/` → `usdclp`, `xauusd`, `wti`, `us100`, `copper`, `aapl`…

## Cambios

### 1. `.gitignore`
- Agregar `data/mt5_response.json` (junto a `mt5_command.json`).
- **(Decisión A)** Agregar runtime de Pulse: `.pulse/state.sqlite`, `.pulse/state.sqlite-shm`, `.pulse/state.sqlite-wal`, `.pulse/audit.jsonl`. (Los artefactos durables — `changes/`, `specs/`, `heuristics/` — SÍ se versionan.)

### 2. Convención única de nombres de chart **(Decisión B)**
**Formato:** `data/charts/<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`
- `activo_slug`: misma regla que `ruta_mensaje.ps1` (#45) → `lowercase(ticker_mt5)` sin `.spot`/`#`/`/`.
- `<TF>`: código MT5 en mayúscula (`M15`, `H1`, `H4`, `D1`).
- `<YYYY-MM-DD_HH-MM>`: fecha+hora Chile (reloj canónico).

**Ejemplos:** `usdclp_H4_2026-06-07_11-45.png` · `xauusd_M15_2026-06-07_09-30.png` · `wti_H1_…` · `aapl_H4_…`

Reemplaza el caos actual (`USD_CLP_4H_…`, `USDCLPH4.png`, `WTI.spotH1.png`, `US100.spotM15.png`, `#AAPL_4H_…`).

**Documentar en:**
- `.claude/commands/chart.md` (PASO 4 — nombre del PNG): especificar el formato. (Generador-agnóstico: aplica al pipeline propio de #87 y a charts manuales.)
- `CLAUDE.md`: una línea de regla, junto a la convención de rutas de mensaje (#45), para centralizar.

## Verificación
- `git status` limpio tras el cambio (sin `.pulse/state.sqlite*`/`audit.jsonl`).
- `.gitignore` cubre `mt5_response.json`.
- Convención documentada en `chart.md` + `CLAUDE.md`.
- Gate Pulse verde (cero código tocado; pytest 11).

## Criterios de aceptación (#81)
- [ ] `.gitignore` cubre los JSON efímeros (incl. `mt5_response.json`).
- [ ] Efímeros fuera del índice (ya cumplido).
- [ ] Convención de chart documentada y especificada.
