# Code-Quality Report — 107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci

**Gate:** 2 (Code-Quality)
**Issue:** #107
**Timestamp:** 2026-07-13T21:09:11Z
**Verdict:** CODE_QUALITY: ✅

## Precondición verificada

`spec_compliance_report.md` existe con `SPEC_COMPLIANCE: ✅` (Gate 1 pasó) — se procede con Gate 2.

## Hallazgos

(vacío — no se encontraron issues atribuibles a este Change)

## Evaluación de calidad

- **Naturaleza del Change**: `.claude/commands/ventas.md` es un archivo de prompt (Capa 2), sin
  código Python/TS nuevo. No aplican las invariantes de arquitectura hexagonal, `Pydantic`,
  `SecretStr` ni docstrings de dominio (no hay `src/pulse/` en este repo — el dominio de este
  Change es `comandos`, no motor Pulse).
- **Naming**: `ventas.md`, `ventas_email.txt`, `ventas_whatsapp.txt`, `historial_ventas.json` —
  snake_case consistente con el resto de `templates/*.txt` y `data/historial_*.json` del repo.
- **JSON válido**: `data/historial_ventas.json` parsea correctamente como `[]` (verificado con
  `python -m json`).
- **Consistencia de formato Markdown**: la fila nueva de `/ventas` en `CLAUDE.md` (tabla de Capa
  2) y la entrada en "No elegibles" de `.claude/shared/modo_ejecutivo.md` no rompen la tabla ni
  la lista existentes (verificado con `grep` sobre las líneas circundantes).
- **Plantillas literales**: contenido de `templates/ventas_email.txt` y
  `templates/ventas_whatsapp.txt` coincide palabra por palabra con el contrato de `design.md` §3
  (ya validado en Gate 1).
- **Tono/registro**: `.claude/commands/ventas.md` documenta explícitamente el registro directo y
  profesional para audiencia comercial interna, manteniendo la norma anti-dramatización de
  `CLAUDE.md` (RNF1).
- **RNF2 confirmado**: `señal.md`, `alerta.md`, `accion.md`, `dato_macro.md` y
  `scripts/ruta_mensaje.ps1` no aparecen en el diff — el Change es puramente aditivo.

## Toolchain real ejecutada

```
uv run ruff check
uv run ty check
uv run pytest
```

- **ruff check**: 3 errores encontrados, los 3 en `scratch_apertura.py`, `scratch_emas.py` y
  `scratch_get_calendar.py` (variable no usada / imports no usados) — estos 3 archivos son
  trabajo en curso ajeno a este Change (confirmados explícitamente fuera de alcance por el hilo
  principal; no forman parte del diff de `/ventas`). Ningún archivo del alcance de este Change es
  Python, por lo que `ruff` no aplica directamente a la implementación de `/ventas`. No se
  corrigen ni se tocan esos 3 scratch files desde este Change.
- **ty check**: `All checks passed!` (sin errores de tipos en todo el repo).
- **pytest**: `67 passed` (suite completa preexistente — `test_calendar.py`,
  `test_chart_objects.py`, `test_levels.py`, `test_server.py`, `test_symbol_spec.py`). Sin tests
  nuevos porque `/ventas` no agrega código Python (consistente con `tasks.md`, invariante
  "no requiere módulos Python/tests pytest").
- **bandit** / **vulture**: no instalados como dependencias de este proyecto (`pyproject.toml`
  solo declara `ruff`, `ty`, `pytest` como dev-dependencies; `[tool.vulture]` está configurado
  pero el binario no está presente en el entorno `uv`). No aplican de todas formas a este Change
  (cero código Python nuevo/modificado).

## PR

Ver sección "PR creado" del reporte al hilo principal — creado tras este report,
enlazado a `Refs #107`.
