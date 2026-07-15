# Idea: Stories GI · Fase B — plantilla Quote 16:9

## Problema

El motor de Stories GI ya está generalizado a 16:9 (Fase A, issue #119, mergeado en
`master` como v0.2.0): `scripts/story_render.py` soporta viewport 1920×1080, tokens
escalares dinámicos, `<!-- FOR -->`/`<!-- ENDFOR -->` y helpers de derivación, validado con
la migración de `templates/stories/alerta.html`. Sin embargo, el motor generalizado hoy solo
tiene **una** plantilla real (`alerta`) — las 11 restantes del catálogo GI (issues #111-#115
+ Fases B/C/D) todavía no existen como snapshot ni como `[tipo]` de `/story`.

Esta Fase B cubre la plantilla **`quote`** (#10 del catálogo): una pieza puramente
editorial — cita + autor + cargo — sin gráfico, sin listas (`FOR`) y sin fuente de datos
del motor (el director/analista redacta el texto a mano). Es la plantilla más simple del
catálogo restante y sirve para validar que el motor generalizado de la Fase A funciona igual
de bien para un caso *sin* fences de gráfico ni loops, no solo para el caso Alerta (que sí
tiene ambos).

## Contexto observado

**Motor (Fase A, ya en `master`, NO se modifica en este Change)**:
- `scripts/story_render.py`: `render_png` con viewport `1920×1080` por defecto;
  `build_context` deriva tokens escalares dinámicamente de las claves del payload (no hay
  lista fija por plantilla); `resolver_loops` (`<!-- FOR:clave -->`) para arrays — **no
  aplica a `quote`**, que no tiene ningún campo array; fences (`<!-- IF -->`) y guardia
  (`_validar_sin_huerfanos`) se conservan; orden canónico: loops → fences → tokens → guardia.
- `templates/stories/alerta.html` es la única plantilla 16:9 existente en el repo — sirve
  de referencia de esqueleto GI (chips, titular, bajada, footer estándar) y de fuentes
  locales embebidas (`templates/stories/fonts/*.woff2`: `syne-800`, `dm-sans-400`,
  `dm-sans-700`, `space-grotesk-600`).
- `.claude/commands/story.md` PASO 0 valida `[tipo]` contra la lista dura `alerta` (único
  soportado hoy); el resto del comando (PASO 1-7) está específico al contrato
  `story_alerta` (recolección híbrida de niveles + narrativa, payload, render, guardado).

**Contrato de `quote` (catálogo, fila 10 de
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`, líneas 55-110)**:
- Campos del payload: `cita`, `autor`, `autor_sub` — sin campos array, sin `chart_png`.
- Sin gráfico (columna "Gráfico" = "no").
- Fondo oscuro (columna "Fondo" = "oscuro", igual que Alerta; el único fondo claro del
  catálogo es `macro`, fuera de esta Fase).
- Fuente de datos: **editorial manual** — "sin datos del motor; el analista redacta la
  cita. El payload es editorial." No hay comando fuente que recolecte datos de mercado para
  esta plantilla (a diferencia de `market`/`macro`/`idea`/`flash`, que sí delegan en
  `/apertura`, `/dato_macro`, etc.).

**Precedente directo (Fase A, `.pulse/changes/archive/119-.../idea.md` y `design.md`)**:
confirma que cada plantilla restante es "1 snapshot HTML 16:9 en `templates/stories/` + su
contrato de payload documentado + su recolección de datos en `story.md` + tests de mapeo" y
que "**1 plantilla = 1 Change**" — Fase B no agrupa varias plantillas (aunque el catálogo
liste `quote`, `breaking`, `encuesta`, `edu` juntas como "Fase B — Simples", cada una es su
propio Change/PR, según la convención ya fijada).

**Convenciones duras que siguen aplicando sin cambios**:
- Regla "solo lectura" del canvas Claude Design compartido de GI (`CLAUDE.md` sección
  "Stories GI"): el snapshot `quote.html` se autora en el repo, nunca se sincroniza
  automáticamente ni se sube nada hacia el canvas.
- `/story` no soporta el flag `ejecutivo` (genera imagen, no mensaje de cliente reenviable) —
  listado en `.claude/shared/modo_ejecutivo.md` bajo "No elegibles"; `quote` no cambia esto.
- Flujo de aprobación: preview de texto antes de renderizar/guardar cualquier PNG.
- `scripts/ruta_story.ps1` ya acepta `-Plantilla` genérico — no necesita cambios para
  `quote`.

## Hipótesis de solución

Alcance 100% aditivo, sin tocar el motor (`scripts/story_render.py`) ni sus tests de
`resolver_loops`/fences (ya cubiertos por Fase A):

1. **`templates/stories/quote.html`** (nuevo, snapshot 1920×1080): esqueleto GI equivalente
   al de `alerta.html` (chips, footer estándar `@grupointeligencia` + disclaimer CFD, fuentes
   locales de `templates/stories/fonts/`, paleta oscura), pero sin bloque de gráfico ni
   bloque de datos numéricos — el cuerpo central es la cita (`{{cita}}`) con atribución
   (`{{autor}}`, `{{autor_sub}}`). Sin fences `<!-- IF -->` ni `<!-- FOR -->` (no hay campos
   condicionales ni arrays en el contrato de `quote`); solo tokens escalares simples.
2. **`.claude/commands/story.md`**: agregar `quote` a la lista de `[tipo]` soportados en
   PASO 0 (junto a `alerta`) y un bloque de recolección específico para `quote` —
   editorial/manual (el director dicta o el modelo redacta la cita con criterio, sin
   delegar en ningún comando fuente de datos de mercado, a diferencia de `alerta` que delega
   en niveles de `/apertura`). Conserva el resto del flujo (preview → aprobación → render →
   guardado con `ruta_story.ps1 -Plantilla "quote"`).
3. **`tests/test_story_render.py`**: agregar tests de mapeo puros para `quote.html`
   (`build_context`/`build_html` contra el snapshot real, análogos a los que ya existen para
   `alerta.html`) — sin tocar `conftest.py` ni los tests de `resolver_loops`/fences de la
   Fase A. Reusar el patrón de render `skipif` sin Chromium si aplica, verificando IHDR
   1920×1080.
4. **`CLAUDE.md`**: solo si la sección "Stories GI" enumera explícitamente los tipos
   soportados por `/story` (hoy dice "único `[tipo]` soportado hoy: `alerta`") — actualizar
   esa enumeración para incluir `quote`. No tocar otra cosa de esa sección.
5. El motor (`build_context`, `resolver_loops`, `render_png`) y el contrato de payload de
   `alerta` **no se tocan** — Fase B solo agrega un contrato de datos y un snapshot nuevos,
   consumiendo el motor genérico tal cual quedó en Fase A.

## Preguntas abiertas

- ¿El esqueleto de `quote.html` reusa literalmente los mismos chips/footer/CSS de
  `alerta.html` (copiar y recortar), o hay algún elemento del manual de marca GI específico
  para piezas "cita" (ej. comillas decorativas, layout centrado sin chips de categoría) que
  haya que verificar contra el canvas de solo lectura antes de autorar el snapshot?
- ¿`autor_sub` es siempre un campo presente (cargo/rol) o puede venir vacío (cita anónima /
  sin atribución de cargo)? Si puede faltar, define si `quote.html` necesita una fence
  `<!-- IF:autor_sub -->` (lo cual reabriría la pregunta de si Fase B usa fences pese a no
  tener campos condicionales evidentes en el catálogo) o si el campo es obligatorio en el
  contrato y el comando lo exige siempre.
- ¿De dónde sale el texto de la cita en la práctica? El catálogo dice "editorial manual"
  pero no aclara si `/story quote` pide la cita directamente al director por prompt, o si el
  modelo la redacta con criterio (ej. resumiendo una idea de mercado de la semana) y el
  director solo aprueba — afecta el diseño del PASO de recolección en `story.md`.
- ¿Hace falta un límite de longitud de la cita para que el snapshot no desborde en 1920×1080
  (a diferencia de campos numéricos cortos, una cita es texto libre de longitud variable)?
  Define si `build_html`/la guardia existente ya cubre esto o si es puramente un criterio
  editorial del comando (pedir cita corta) sin validación en el motor.
- ¿El test de mapeo de `quote` necesita fixture propio en `tests/fixtures/stories/` o alcanza
  con reusar el patrón de test contra el snapshot real (`quote.html`), como ya se hace para
  `alerta.html`?

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), catálogo de las 12 plantillas; fila 10 `quote` (líneas 55-110): payload
  `cita, autor, autor_sub`, sin gráfico, fondo oscuro, fuente "editorial manual"; plan de
  fases (Fase B = simples sin gráfico/listas).
- `docs/design/stories-gi/plantillas-stories-gi.md` — sistema visual GI (manual de marca,
  esqueleto de chips/footer), mapeo campo-por-campo existente para `alerta` como precedente
  de documentación a replicar para `quote`.
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; conserva el contrato `story_alerta`
  original y la especificación de la Fase A (motor generalizado 16:9).
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/idea.md`
  y `design.md` — Change antecedente inmediato: generalización del motor, decisiones D1-D7
  heredadas, convención "1 plantilla = 1 Change" y plan de fases B/C/D.
- `scripts/story_render.py` — motor 16:9 ya generalizado, **no se modifica** en este Change.
- `templates/stories/alerta.html` + `templates/stories/fonts/` — única plantilla 16:9
  existente, referencia de esqueleto/paleta/fuentes para autorar `quote.html`.
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `quote` a `[tipo]`;
  nuevo bloque de recolección editorial).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para `quote`.
- `CLAUDE.md` sección "Stories GI" — actualizar solo la enumeración de tipos soportados, si
  corresponde.
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin cambios
  esperados en esta Fase).
- Issue #121 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B.
