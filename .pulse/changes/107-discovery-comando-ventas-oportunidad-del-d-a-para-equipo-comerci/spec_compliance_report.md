# Spec-Compliance Report — 107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci

**Gate:** 1 (Spec-Compliance)
**Issue:** #107
**Timestamp:** 2026-07-13T21:09:11Z
**Verdict:** SPEC_COMPLIANCE: ✅

## Hallazgos

(vacío — no se encontraron discrepancias)

## Verificación realizada

- **Faltantes (tasks.md → implementación)**: T1-T19 marcados `[x]` y verificados contra el
  delta real. Los 8 PASOS + bloque de rechazo `ejecutivo` existen en
  `.claude/commands/ventas.md` en el orden de `design.md` §2, cubriendo R1-R13 y RNF1-RNF4:
  - R1 (registro/invocación, rechazo explícito de `ejecutivo`) — bloque "Rechazo del flag
    `ejecutivo`" antes de PASO 1.
  - R2 (detección evento, PASO 1) — incluye guardrail `"📊 Sin oportunidad clara hoy."` + DETENER.
  - R3 (activo protagonista, PASO 2) — 1 activo obligatorio.
  - R4 (niveles técnicos, PASO 3) — `get_asset_levels` directo, sin confirmación manual previa.
  - R5/R6 (CLP/RR + digits, PASO 4) — fórmulas idénticas a `señal.md` PASO 5, fallback
    `get_symbol_spec` → `config/activos.json`, advertencia RR<1.5 no bloqueante.
  - R7 (ticket/temporalidad, PASO 5) — constante `$5.000.000 CLP`, default de temporalidad por
    naturaleza del evento + volatilidad.
  - R8/R10 (render dos piezas, PASO 6) — ambas piezas siempre juntas, templates literales del
    issue #107 con placeholders `[Corchetes]` (decisión ADR de `design.md` §3, correctamente
    aplicada — no `{{mustache}}`).
  - R9 — rechazo explícito de `ejecutivo`, continúa sin abortar.
  - R11 (aprobación, PASO 7) — 3 preguntas, DETENER sin guardar si no aprueba.
  - R12/R13 (guardado, PASO 8) — `ruta_mensaje.ps1` con `ventas_email`/`ventas_whatsapp`,
    `-Activo` siempre presente, y schema de `data/historial_ventas.json` idéntico al de
    `design.md` §4 (mismos 12 campos, mismo orden).
  - T3: `data/historial_ventas.json` existe, contenido `[]`, parsea como array vacío.
  - T13/T14: `CLAUDE.md` documenta `/ventas` en la tabla de Capa 2 (fila nueva, conteo
    actualizado 23→24) y en "No elegibles" del modo ejecutivo; `.claude/shared/modo_ejecutivo.md`
    agrega `/ventas` a la misma lista con su razón — ambos diffs acotados exactamente a esas
    líneas (verificado con `git diff CLAUDE.md .claude/shared/modo_ejecutivo.md`).
  - T20 (corrida real única) queda `[ ]` explícitamente pendiente y no bloqueante — documentado
    así en `tasks.md`, consistente con la nota de Fase D (verificación por inspección
    estructural, no ejecución en vivo, para no ensuciar `data/historial_ventas.json` reales).

- **Over-engineering**: el delta (`git status`) contiene exactamente los archivos declarados en
  el alcance IN de `spec.md`/`design.md`/`tasks.md`: `.claude/commands/ventas.md`,
  `templates/ventas_email.txt`, `templates/ventas_whatsapp.txt`, `data/historial_ventas.json`,
  el diff acotado de `CLAUDE.md` y `.claude/shared/modo_ejecutivo.md`, y el paper trail en
  `.pulse/changes/107-.../`. No se detectaron archivos ni features fuera de ese alcance
  atribuibles a este Change. Los demás archivos modificados/sin trackear en el working tree
  (`.claude/commands/apertura.md`, `.gitignore`, `data/glosario_siglas.json`,
  `data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
  `templates/encuesta_tendencia.txt`, `uv.lock`, `.agents/`, `scratch_*.py`,
  `docs/design/motor-como-cerebro-hub-gi.*`, `docs/design/stories-gi/`) son trabajo ajeno a este
  Change (confirmado por instrucción explícita del hilo principal) y no se tocan en Apply/Review
  de este Change.

- **Divergencia**: ningún hallazgo. Se verificó específicamente que `.claude/commands/ventas.md`
  reproduce palabra por palabra el bloque de "filtros de prioridad" tal como quedó fijado en
  `design.md` §2 PASO 1 (nota: el rótulo de `design.md` dice "texto idéntico, copiado literal"
  respecto de `alerta.md`, pero el bloque que `design.md` realmente fija ya es una versión
  condensada distinta del texto extendido de `alerta.md` PASO 1 — esto es una imprecisión de
  redacción interna de `design.md`, ya aprobado por el director el 2026-07-13T21:00:47Z, no una
  divergencia de la implementación respecto de su contrato autoritativo). `ventas.md` es fiel al
  bloque real de `design.md`, y `spec.md` R2 solo exige "mismo orden de filtros de prioridad", que
  se cumple. No se modificó ningún comando existente (`señal.md`, `alerta.md`, `accion.md`,
  `dato_macro.md`) ni `scripts/ruta_mensaje.ps1` ni `data/historial_senales.json` (RNF2,
  confirmado con `git status` — ninguno aparece en el diff).

## Evidencia

- `git status --short` (working tree, sin commits aún en `feat/comando-ventas` sobre `master`).
- `git diff CLAUDE.md .claude/shared/modo_ejecutivo.md`.
- Lectura completa de `idea.md`, `proposal.md`, `spec.md`, `design.md`, `tasks.md`,
  `.claude/commands/ventas.md`, `templates/ventas_email.txt`, `templates/ventas_whatsapp.txt`,
  `data/historial_ventas.json`, `.pulse/changes/107-.../state.yaml`.
- Comparación de texto contra `.claude/commands/alerta.md` (filtros de prioridad).
