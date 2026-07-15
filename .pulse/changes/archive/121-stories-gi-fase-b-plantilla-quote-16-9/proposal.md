# Proposal: Stories GI · Fase B — plantilla Quote 16:9

## Problema

El motor de Stories GI ya está generalizado a 16:9 (Fase A, issue #119, `master`
v0.2.0) pero solo tiene una plantilla real (`alerta`). Esta Fase B agrega la
plantilla **`quote`** (#10 del catálogo, PR #118): pieza puramente editorial —
cita + autor + cargo — sin gráfico, sin arrays y sin fuente de datos del motor.
Sirve además para validar que el motor generalizado funciona igual de bien para
un caso *sin* fences de gráfico ni loops (a diferencia de Alerta, que usa ambos).

## Contexto observado

**Mecanismo de fences del motor (`scripts/story_render.py`, verificado en código,
no se modifica en este Change)**: `_resolver_fences`/`_fence_presente` recorren
una tupla **fija** `_FENCES = ("variacion", "vol", "chart_img", "chart_svg")` —
los fences `<!-- IF:nombre -->` **top-level** solo existen para esos 4 nombres
de Alerta, no para cualquier clave del payload. El mecanismo de fence genérico
por clave (`_expandir_elemento`, `bool(objeto.get(clave))`) solo aplica **dentro**
de un bloque `<!-- FOR -->`, que `quote` no usa (sin arrays). Esto resuelve de
forma directa una de las preguntas abiertas del idea-doc: **`quote.html` no
puede usar un fence `<!-- IF:autor_sub -->` sin tocar el motor** (fuera de
alcance, decisión firme).

**Contrato de `quote`** (`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`,
fila 10, líneas 55-110, ya citado en `idea.md`): payload `cita`, `autor`,
`autor_sub`; sin gráfico; fondo oscuro; fuente "editorial manual" (el
analista/director redacta, sin comando de recolección de mercado).

**Precedente Fase A** (`.pulse/changes/archive/119-.../proposal.md`, molde de
este documento): pipeline `build_html` = loops → fences → tokens → guardia;
`templates/stories/alerta.html` es la única plantilla 16:9 existente (fuentes
locales `templates/stories/fonts/*.woff2`, footer/chips estándar); `.claude/commands/story.md`
PASO 0 valida `[tipo]` contra la lista dura `alerta`.

**Convenciones sin cambios** (heredadas, ya citadas en `idea.md`): regla
"solo lectura" del canvas GI; `/story` fuera del flag `ejecutivo`; flujo de
aprobación (preview antes de render/guardado); `ruta_story.ps1` ya acepta
`-Plantilla` genérico.

## Hipótesis de solución

Alcance 100% aditivo, motor sin cambios:

1. **`templates/stories/quote.html`** (nuevo, snapshot 1920×1080): reutiliza el
   esqueleto de marca de `alerta.html` como base (footer `@grupointeligencia` +
   disclaimer CFD, fuentes locales, paleta oscura) pero con layout centrado sin
   chips de categoría ni bloque de gráfico — cuerpo central: comillas
   decorativas (CSS/SVG estático, no token) + `{{cita}}` + atribución
   (`{{autor}}`, `{{autor_sub}}`). **Sin fences `IF`/`FOR`** — confirmado
   arriba que el motor no soporta un fence top-level genérico sin tocarlo;
   `autor_sub` se resuelve como campo **obligatorio pero admite string vacío**
   (`""`) en el payload — el token siempre se sustituye (nunca queda huérfano),
   y una `autor_sub` vacía se ve como línea en blanco/colapsada por CSS
   (`:empty { display: none; }` sobre el contenedor del token), sin lógica
   condicional en el motor.
2. **`.claude/commands/story.md`**: agregar `quote` a `[tipo]` en PASO 0 y un
   bloque de recolección editorial — el director dicta la cita o aprueba una
   redactada por el modelo (mismo criterio que otras piezas editoriales del
   repo, ej. `/concepto`); reusa el flujo existente preview → aprobación →
   render → `ruta_story.ps1 -Plantilla "quote"`. Se documenta como guía
   editorial (no como validación del motor) un límite recomendado de longitud
   de `cita` para no desbordar el layout 1920×1080 (a definir el valor exacto
   en `specify`, ej. rango de caracteres análogo al titular de Alerta).
3. **`tests/test_story_render.py`**: tests de mapeo puros para `quote.html`
   (`build_context`/`build_html` contra el snapshot real, incluyendo el caso
   `autor_sub=""`), análogos a los de `alerta.html`; sin fixture nuevo en
   `tests/fixtures/stories/` — se reusa el patrón de test contra snapshot real,
   no contra un fixture minimalista aparte. Sin tocar `conftest.py`.
4. **`CLAUDE.md`** § "Stories GI": solo si enumera los `[tipo]` soportados de
   `/story` (hoy dice "único `[tipo]` soportado hoy: `alerta`") — agregar
   `quote` a esa enumeración, sin tocar el resto de la sección.
5. Motor (`build_context`, `resolver_loops`, `_FENCES`, `render_png`) y contrato
   de payload de `alerta` **no se tocan**.

## Preguntas abiertas

- Valor exacto del límite de longitud recomendado para `cita` (caracteres) que
  quepa cómodo en el layout 1920×1080 sin overflow — a fijar en `specify` con
  una prueba visual del snapshot.
- Detalle CSS del layout "citas" (tamaño/posición de comillas decorativas,
  tipografía de `autor` vs `autor_sub`) — se define al autorar el HTML en
  `apply`, no bloquea `specify`.
- Confirmar en `specify` si `autor_sub=""` debe colapsar también el espaciado
  vertical que deja (no solo ocultar el texto) para que el centrado del bloque
  cita no quede descuadrado cuando falta el cargo.

## Referencias

- `.pulse/changes/121-stories-gi-fase-b-plantilla-quote-16-9/idea.md` — idea-doc
  base de esta propuesta (contexto completo, preguntas originales).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila
  10 `quote`: payload `cita, autor, autor_sub`, sin gráfico, fondo oscuro,
  fuente "editorial manual".
- `.pulse/specs/stories-gi/spec.md` — spec del dominio (contrato heredado,
  motor generalizado Fase A).
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/proposal.md`
  — molde de este documento y precedente de decisiones D1-D7/orden canónico.
- `scripts/story_render.py` (líneas 33, 182-261) — motor: `_FENCES` fija (4
  nombres top-level), fence genérico por-elemento solo dentro de `FOR`; no se
  modifica.
- `templates/stories/alerta.html` + `templates/stories/fonts/` — base de
  esqueleto/paleta/fuentes para autorar `quote.html`.
- `.claude/commands/story.md` — comando a extender (PASO 0 + recolección
  editorial).
- `tests/test_story_render.py` — suite a extender con tests de mapeo de `quote`.
- `CLAUDE.md` § "Stories GI" — actualizar enumeración de tipos si corresponde.
- Issue #121 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre.
