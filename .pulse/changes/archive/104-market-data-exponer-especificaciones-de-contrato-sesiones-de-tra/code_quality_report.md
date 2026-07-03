# Code-Quality Report — 104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra

**Gate:** 2 (Code-Quality)
**Issue:** #104
**Timestamp:** 2026-07-03T06:05:00Z
**Verdict:** CODE_QUALITY: ✅

## Hallazgos

- (vacío — el único hallazgo bloqueante de la primera pasada fue corregido)

### Re-auditoría tras fix (commit `aa2be77`)

La primera pasada de este gate reportó `CODE_QUALITY: ❌` por
`src/market_data_mcp/tools/symbol_spec.py:112-126`: `_offset_servidor_minutos` redondeaba
`server_utc_offset_minutes` a una grilla de 15 minutos, contradiciendo `spec.md` RNF2 ("se
expone crudo, sin convertir, para trazabilidad/depuración") y `design.md` §6.1 ("se expone
crudo... redondeado a la resolución de minutos").

El commit `aa2be77` ("fix(mcp): exponer server_utc_offset_minutes crudo a resolución de minuto
(#104)"), con autorización del director, corrige el hallazgo:

- `_offset_servidor_minutos` ahora hace `round(delta_minutos)` (redondeo a minuto entero, sin
  grilla de 15/30/60) — verificado leyendo el diff completo del commit.
- El docstring de la función se actualizó para reflejar el comportamiento real ("se expone
  **crudo**... para preservar trazabilidad del clock drift real del servidor del broker —
  design.md §6.1"), alineado con `spec.md`/`design.md`.
- Se agregó `test_offset_servidor_minutos_expone_drift_crudo_no_multiplo_de_15`, que fija un
  drift de 187 minutos (no múltiplo de 15) y verifica que se expone como `187` (no `180`),
  cerrando el gap de cobertura señalado en la pasada anterior — ahora la NFR está protegida por
  un test de regresión explícito.

Confirmado: el fix está acotado al hallazgo reportado, no introduce cambios funcionales
adicionales ni nuevas divergencias respecto a `spec.md`/`design.md`. Gate 1 re-auditó el delta
completo y mantuvo `SPEC_COMPLIANCE: ✅` (ver `spec_compliance_report.md`, evidencia
`git show aa2be77`).

### Resto del delta (sin cambios respecto a la primera pasada)

- Separación de capas: `tools/symbol_spec.py` no importa `MetaTrader5` directamente, solo
  consume `mt5_client.get_symbol_info`/`get_session` (import perezoso), igual que el resto de
  tools del MCP.
- Naming: snake_case en funciones/módulos, constantes en UPPER_CASE con prefijo `_` para
  privadas (`_TRADE_MODE_MAP`, `_TICKER_EXCHANGE`, `_DIAS_ES`, `_MAX_VENTANAS_POR_DIA`, etc.).
- Docstrings y mensajes de error en español, consistentes con el resto del MCP.
- Contrato de error `{'error': 'CÓDIGO', 'message': '...'}` respetado en los 4 códigos
  (`TICKER_NOT_FOUND`, `INVALID_FECHA`, `MT5_UNAVAILABLE`, `SESSION_UNAVAILABLE`) — nunca se
  retorna `None` ni lista vacía como señal de error.
- No aplica manejo de secretos (`SecretStr`) en este delta — no se introducen credenciales.
- Tests: 18 casos en `tests/test_symbol_spec.py` (17 originales + el nuevo de regresión del
  fix) cubren camino feliz (con y sin `fecha`), los 4 códigos de error, las 3 ramas del
  algoritmo "feriado primero", el ticker sin cobertura de feriados (R11) y helpers puros.
  Buena cobertura de casos felices y de error para el feature nuevo, incluyendo ahora la NFR de
  trazabilidad del offset.

## Evidencia

- `git show aa2be77` — diff completo del fix (`src/market_data_mcp/tools/symbol_spec.py`,
  `tests/test_symbol_spec.py`).
- ruff check (repo completo): 2 errores preexistentes, **no relacionados con este delta**
  (`src/market_data_mcp/tools/levels.py:12` import sin usar, `tests/test_chart_objects.py:8`
  import sin usar — ambos en archivos no tocados por este Change, presentes ya en `master`).
  `ruff check` acotado a los 4 archivos del delta (`symbol_spec.py`, `mt5_client.py`,
  `server.py`, `test_symbol_spec.py`): PASSED (0 errores).
- ty check: PASSED (0 errores) en todo el repo.
- pytest: PASSED — 67 passed (suite completa), de los cuales 18 corresponden a
  `tests/test_symbol_spec.py` (100% de los AC1-AC12 + unit tests de helpers puros + regresión
  del fix).
- PR: https://github.com/bbenja11/grupo-analisis-mercado/pull/105
