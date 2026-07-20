# Idea: Stories GI · Fase C — plantilla Flash (cierre multi-activo) 16:9

> Fase explore del Change #129. Primera plantilla de la **Fase C** (plantillas con listas vía
> `<!-- FOR -->`) del roadmap Stories GI. Molde directo: `edu` (#127), primer consumidor real del
> mecanismo `FOR` del motor.

## Problema o Necesidad

El comando `/story` ya produce 5 plantillas 16:9 (`alerta`, `quote`, `breaking`, `encuesta`,
`edu`). El roadmap (`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`,
líneas 91-93) define la **Fase C** como las plantillas **con listas**: `flash`, `calendario`,
`semanal`, `earnings`. Siguiendo el orden del design doc, la primera es **`flash`** (#05 del
catálogo): un **cierre multi-activo** — una tabla de ~5 activos con su último valor y su
variación del día. Es la pieza que un ejecutivo comparte al cierre de la jornada para mostrar
"cómo cerró el mercado" de un vistazo.

## Solución Propuesta

Agregar `flash` **sin tocar el motor** (`scripts/story_render.py`), igual que `edu`:
1. Un nuevo snapshot `templates/stories/flash.html` (1920×1080, andamiaje de marca reutilizado)
   con **un bloque `<!-- FOR:filas -->…<!-- ENDFOR:filas -->`** para las filas de la tabla, y el
   contenedor de la tabla + los rótulos de columna **fuera** del FOR (persisten con `filas: []`).
2. Cada fila es un objeto con **claves escalares** (`nombre`, `tipo`, `valor`, `variacion`,
   `direccion`) — `_expandir_elemento` resuelve `{{campo}}` por objeto; la dirección alcista/
   bajista/lateral se refleja con color y flecha **por CSS** (clase derivada de `{{direccion}}`),
   sin helper del motor (los helpers de derivación solo operan sobre claves top-level, no dentro
   del FOR).
3. Registrar el tipo en `.claude/commands/story.md` (PASO 0 + bloque "Ruta `flash`"); la
   recolección de los valores/variaciones reales delega en `get_asset_levels` × N activos (mismo
   criterio que `/apertura`/`/actualizacion`), **en el prompt del comando**, no en el renderer.
4. Tests de mapeo puros con el loop `filas` en 0/1/N; `CLAUDE.md` nombra el tipo.

**Diferencia con Fase B**: `flash` es la primera plantilla que **consume datos reales del motor**
(valores + variaciones de `get_asset_levels` sobre varios activos), a diferencia de las 4 de
Fase B (100% editoriales). Pero esa recolección vive en el prompt de `/story` (el renderer sigue
siendo "tonto": payload → HTML → PNG). `flash` **NO** lleva gráfico embebido — eso es Fase D.

## Preguntas abiertas (a resolver en specify/design)

1. Forma exacta de cada fila: ¿`variacion` como objeto `{pct, direccion}` (como en `alerta`) o
   aplanado a escalares por-fila? (Los helpers de flecha/color solo corren en top-level, no en el
   FOR — probablemente haya que aplanar, como `edu` aplanó `ejemplo`.)
2. Acento de marca de `flash` (estructura) vs. verde/rojo semántico de las filas de variación.
3. Campos escalares del encabezado (título, fecha/rango, kicker opcional).
4. ¿Cuántos activos por defecto? (el layout 16:9 acota; el motor no valida cantidad.)

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` fila 05 (`flash`,
  línea 63), plan de fases (líneas 91-93).
- `.pulse/changes/archive/127-…/{idea,proposal,spec,design}.md` — molde directo (edu, primer FOR).
- `scripts/story_render.py` — motor 16:9 (`resolver_loops`, `_expandir_elemento`); **no se toca**.
- `templates/stories/edu.html` — molde de snapshot con FOR real.
- Issue #129.
