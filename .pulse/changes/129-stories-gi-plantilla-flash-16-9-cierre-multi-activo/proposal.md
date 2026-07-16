# Proposal: Stories GI · Fase C — plantilla Flash (cierre multi-activo) 16:9

## Why

Continuar el roadmap Stories GI arrancando la **Fase C** (plantillas con listas `<!-- FOR -->`)
con la primera del orden del design doc: **`flash`** (#05, cierre multi-activo). Da a los
ejecutivos una pieza de "cómo cerró el mercado" — tabla compacta de activos con su último precio
y variación del día — sobre el mismo motor 16:9, sin tocarlo (todo aditivo). Molde directo: `edu`
(#127), primer consumidor real del FOR.

## What Changes

Cuatro archivos, todo aditivo (motor intacto):

1. **`templates/stories/flash.html`** (nuevo, 1920×1080): andamiaje de marca reutilizado de
   `edu.html`/`encuesta.html` (fuentes locales `fonts/*.woff2`, footer `@grupointeligencia` +
   disclaimer CFD). Cuerpo: chip `{{kicker}}` opcional + `{{titulo}}` + `{{fecha}}` + una **tabla**
   cuyo `<thead>`/rótulos de columna y contenedor van **fuera** del bloque
   `<!-- FOR:filas -->…<!-- ENDFOR:filas -->`; cada fila de datos se repite por objeto de `filas`.
   Tokens por fila (escalares): `{{nombre}}`, `{{tipo}}`, `{{valor}}`, `{{variacion}}`,
   `{{direccion}}`. La dirección (`alcista`/`bajista`/`lateral`) se refleja con color + flecha
   **por CSS** (clase `flash-var--{{direccion}}`), sin helper del motor. `kicker` opcional por CSS
   `:empty`.

2. **`.claude/commands/story.md`**: agregar `flash` a la lista dura de `[tipo]` (PASO 0) + nuevo
   bloque "Ruta `flash`" (espejo de "Ruta `edu`") — recolección de los valores/variaciones reales
   delegando en `get_asset_levels` × N activos (criterio de `/apertura`/`/actualizacion`), con
   fallback manual; arma `filas[]` como array de objetos aplanados; preview que lista las filas;
   render/guardado bajo `-Plantilla "flash"`.

3. **`tests/test_story_render.py`**: tests de mapeo puros contra `flash.html` (payload con N filas
   sin placeholders huérfanos, y el loop `filas` en **0/1/N**), más un test de dimensiones del
   render (`skipif` sin Chromium). Sin fixture nuevo, sin tocar `conftest.py`.

4. **`CLAUDE.md`** sección "Stories GI": la enumeración de `[tipo]` soportados incluye `flash`.

Artefactos SDD en `.pulse/changes/129-…/` + bloque `<!-- change:129-… -->` apéndice de
`.pulse/specs/stories-gi/spec.md`.

## Decisiones clave (a formalizar en spec/design)

- **`variacion` por fila aplanada a escalares** (`variacion` = pct ya formateado, `direccion` =
  slug): los helpers de flecha/color del motor solo corren en claves top-level, no dentro del FOR
  (`_expandir_elemento` solo sustituye escalares y fences `IF` por objeto). Mismo criterio con que
  `edu` aplanó `ejemplo`. La flecha/color salen del CSS por `{{direccion}}`.
- **Verde/rojo reservados a la semántica de la fila** (sube/baja); el acento **estructural** de
  `flash` es distinto (candidato teal `#3E91AF`) para no diluir el verde "alcista". Hex final en la
  PAUSA de design.
- **Sin gráfico embebido** (Fase D) y **sin datos del motor en el renderer** (la recolección vive
  en el prompt del comando; el renderer sigue payload → HTML → PNG).
- **1 plantilla = 1 Change** (convención heredada de Fase A/B).

## Alternativas descartadas

- Agregar un helper de derivación al motor para flechas por-fila → **descartado**: rompe "motor
  intacto"; el CSS por `{{direccion}}` resuelve lo mismo sin tocar Python.
- Agrupar `flash` + `calendario` en un Change → **descartado**: rompe "1 plantilla = 1 Change"
  (PRs más chicos y revisables).
