# Spec-Compliance Report — 104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra

**Gate:** 1 (Spec-Compliance)
**Issue:** #104
**Timestamp:** 2026-07-03T05:59:04Z
**Verdict:** SPEC_COMPLIANCE: ✅

## Hallazgos

- (vacío — sin discrepancias bloqueantes)
- **Resuelto (re-auditoría):** la nota de la revisión anterior sobre
  `src/market_data_mcp/tools/symbol_spec.py:112-126` (`_offset_servidor_minutos` redondeaba
  `server_utc_offset_minutes` a una grilla de 15 minutos, en tensión con "se expone crudo" de
  `design.md` §6.1) quedó corregida en el commit `aa2be77`: ahora `return round(delta_minutos)`
  (resolución de minuto entero, sin grilla de 15/30/60), con docstring actualizado citando
  `design.md` §6.1, y test nuevo
  `test_offset_servidor_minutos_expone_drift_crudo_no_multiplo_de_15` que fija un drift de 187
  minutos (no múltiplo de 15) y verifica que se expone tal cual (`== 187`), no `180`. El fix es
  mínimo (8 líneas en `symbol_spec.py`, 13 líneas de test nuevo), no toca ninguna otra función,
  no introduce archivos ni comportamiento fuera de `RNF2`/`design.md` §6.1 — no es alcance
  nuevo, es la corrección exacta de la divergencia ya señalada.
- T12 de `tasks.md` (actualizar tabla de tools MCP en `CLAUDE.md`/`docs/architecture.md`) sigue
  sin marcar, pero está explícitamente definido como diferible/opcional en el propio
  `tasks.md` ("Fuera del núcleo del Change... No bloquea la suite ni el merge del núcleo") —
  no se audita como faltante.

## Verificación del delta actualizado (2 commits)

- `5c26606` (feat, auditado en la revisión previa) + `aa2be77` (fix, auditado ahora).
- `git diff master...HEAD --stat` sigue tocando exactamente los mismos 5 archivos de código/datos
  de `design.md` §2 (`tools/symbol_spec.py`, `mt5_client.py`, `server.py`,
  `config/feriados_bolsa.json`, `tests/test_symbol_spec.py`) más `tasks.md` — ningún archivo
  nuevo fuera de ese conjunto en `aa2be77` (solo modifica 2 de esos 5: `symbol_spec.py` y
  `tests/test_symbol_spec.py`).
- `aa2be77` no cambia ninguna clave del contrato observable (R3/R4/R7/R8), no cambia el
  algoritmo `opera` (§4 de `design.md`), no cambia el mapeo de 16 tickers NYSE, no toca
  `config/feriados_bolsa.json` ni `server.py` — el fix es puramente interno a
  `_offset_servidor_minutos` y su cobertura de test.
- `rg -n "def register" src/market_data_mcp/tools/symbol_spec.py` → 1 coincidencia (AC1 se
  mantiene); `rg -n "symbol_spec" src/market_data_mcp/server.py` → 3 coincidencias (sin cambios).
- Sin over-engineering ni divergencia nueva: el fix está acotado al hallazgo ya identificado,
  con autorización del director, y su test adicional cubre exactamente ese caso (RNF2).

## Evidencia

- `git log --oneline master..HEAD` → `aa2be77`, `5c26606` (2 commits)
- `git diff master...HEAD --stat`
- `git show aa2be77` (diff completo del fix)
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/spec.md`
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/design.md`
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/tasks.md`
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/proposal.md`
- `src/market_data_mcp/tools/symbol_spec.py`
- `src/market_data_mcp/mt5_client.py`
- `src/market_data_mcp/server.py`
- `config/feriados_bolsa.json`
- `tests/test_symbol_spec.py`
- `src/market_data_mcp/catalog.py`, `config/activos.json` (verificación de los 16 tickers NYSE)
