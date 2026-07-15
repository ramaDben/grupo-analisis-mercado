# Specification: Stories GI · Fase B — plantilla Quote 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #121). Fuente
> canónica del contrato de `quote`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 10, líneas 55-110). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo. Resuelve las preguntas abiertas
> de `idea.md`/`proposal.md` como requisitos verificables (sección "Preguntas abiertas —
> resueltas").

## Objetivo

Agregar la plantilla **`quote`** (#10 del catálogo GI) al comando `/story`: una pieza
100% editorial — cita + autor + cargo, sin gráfico, sin listas, sin dato del motor —
consumiendo el motor genérico de Fase A (`scripts/story_render.py`) tal cual quedó, sin
tocarlo. Sirve además como primer caso de prueba del motor sin fences `IF` ni loops `FOR`.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/quote.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, paleta oscura, footer
  `@grupointeligencia` + disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-50`),
  layout centrado sin chips de categoría ni bloque de gráfico/datos numéricos. Tokens
  escalares simples `{{cita}}`, `{{autor}}`, `{{autor_sub}}` — **sin fences `IF`/`FOR`**.
- Nuevo `[tipo]` `quote` en `.claude/commands/story.md` PASO 0 (lista dura hoy solo
  `alerta`, `.claude/commands/story.md:6-8,19-27`) + nuevo bloque de recolección editorial
  (el director dicta la cita o aprueba una redactada por el modelo). Reusa el flujo
  existente (preview → aprobación → render → `ruta_story.ps1 -Plantilla "quote"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `quote.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo el caso
  `autor_sub == ""`. Sin fixture nuevo en `tests/fixtures/stories/`, sin tocar
  `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy dice "único `[tipo]` soportado hoy: `alerta`") para incluir `quote`, sin tocar el
  resto de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `quote`.
- El contrato de payload de `alerta` — sin cambios.
- Las demás plantillas de Fase B (`breaking`, `encuesta`, `edu`) — cada una su propio
  Change (convención "1 plantilla = 1 Change" heredada de Fase A).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` genérico, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fence `<!-- IF:autor_sub -->` — el motor solo resuelve fences top-level para la
  tupla fija `_FENCES` (4 nombres de Alerta); agregar `autor_sub` a ese mecanismo
  requeriría tocar el motor, fuera de alcance. `quote.html` no usa fences.
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `quote` es 100% editorial manual, sin comando fuente de recolección de datos.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin
  cambios a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/quote.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, paleta oscura `#0D0D1A`, footer estándar) sin chips de categoría ni
bloque de gráfico/datos numéricos. Cuerpo central: comillas decorativas (CSS/SVG
estático, no token) + `{{cita}}` + atribución (`{{autor}}`, `{{autor_sub}}`). Mapea al
punto 1 de la hipótesis.

### R2 — Contrato de payload `story_quote`
```json
{
  "plantilla": "quote",
  "cita": "El mercado premia la paciencia más que la predicción.",
  "autor": "Nombre Analista",
  "autor_sub": "Head of Trading, Grupo Inteligencia"
}
```
- `cita`, `autor`, `autor_sub` son las únicas claves del payload (sin campos array, sin
  `chart_png`, sin dato del motor).
- `autor_sub` es un token **siempre presente** en el payload (nunca ausente/`None`) que
  admite string vacío `""` — resuelve Q2 (no hace falta fence).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `quote`.

### R3 — Sin fences `IF`/`FOR` en `quote.html`
`quote.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`. Justificación
(confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences top-level de
`_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de Alerta); el
fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un bloque
`FOR`, que `quote` no usa (sin arrays). Por tanto ningún campo de `quote` puede
condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens de
`quote` son escalares incondicionales. Resuelve Q2.

### R4 — Colapso visual de `autor_sub` vacío (CSS, no motor)
Cuando `autor_sub == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano,
no hay error de guardia. El contenedor HTML del token `autor_sub` (ej.
`<p class="quote-cargo">{{autor_sub}}</p>`) usa la regla CSS `:empty { display: none; }`
sobre ese contenedor, de forma que:
- Con `autor_sub` no vacío: se muestra la línea de cargo bajo `autor`.
- Con `autor_sub == ""`: el contenedor no ocupa espacio (colapsa `display: none`, no
  solo el texto) — el bloque de atribución (`autor` + `autor_sub`) permanece centrado
  sin hueco en blanco. Resuelve Q3/Q5 (colapso de espaciado, no solo de texto).

### R5 — Límite editorial de longitud de `cita`
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), un límite recomendado de **≤ 220 caracteres** para `cita` —
análogo al límite de `parrafo` de Alerta (`≤ ~280 caracteres`, contrato heredado
`.pulse/specs/stories-gi/spec.md:154`) pero más corto porque `quote` se lee a un solo
tamaño de fuente grande sin bajada de apoyo. El comando ajusta la redacción antes del
preview si la cita excede el límite; el motor no valida longitud (mismo criterio que
Alerta: guardia solo valida tokens huérfanos, no longitud de contenido). Resuelve Q1/Q4.

### R6 — Tratamiento tipográfico de comillas
Las comillas decorativas que enmarcan la cita son un elemento gráfico **estático** del
snapshot (glifo CSS o SVG inline en `quote.html`, ej. `“ ”` como pseudo-elemento
`::before`/`::after` con tipografía Syne), **no** parte del valor de `{{cita}}` — el
payload nunca incluye comillas literales alrededor del texto (`cita` es el texto plano
de la cita, sin comillas propias). Resuelve la pregunta de tratamiento tipográfico de
comillas dejada abierta en `proposal.md`.

### R7 — Recolección editorial en `story.md`
`.claude/commands/story.md` PASO 0 agrega `quote` a la lista de `[tipo]` soportados
(junto a `alerta`). Nuevo bloque de recolección: el director dicta la cita
directamente, o el modelo redacta una propuesta con criterio editorial (ej. resumiendo
una idea de mercado de la semana) y el director la aprueba/ajusta antes del preview —
sin delegar en ningún comando fuente de datos de mercado (`/apertura`, `/dato_macro`,
etc.), a diferencia de `alerta`. Resuelve Q4.

### R8 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `alerta.html`:
1. Test de mapeo con `autor_sub` no vacío: `build_html` sobre `quote.html` con el
   payload de R2 produce HTML sin placeholders sin resolver, con `cita`/`autor`/
   `autor_sub` correctamente inyectados.
2. Test de mapeo con `autor_sub == ""`: mismo `build_html`, el HTML resultante no
   contiene ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se
   omitió el campo).
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `quote.html`, igual que `alerta.html`). Sin cambios en `conftest.py`.
Resuelve Q5 (de `idea.md`).

### R9 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la frase "único `[tipo]` soportado hoy: `alerta`"
se actualiza para reflejar que `quote` también está soportado (ej. "`[tipo]` soportados
hoy: `alerta`, `quote`"), sin tocar el resto del párrafo/sección.

## Casos borde

- **CB-1 (`autor_sub` ausente del payload, no `""`)**: el comando (PASO de recolección,
  R7) siempre construye el payload con la clave `autor_sub` presente, aunque sea `""`
  — nunca omite la clave. Si por error se omitiera, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que Alerta), no un
  colapso silencioso distinto al de R4.
- **CB-2 (`cita` supera el límite editorial de 220 caracteres)**: el comando ajusta la
  redacción antes del preview (R5); el motor no aborta ni trunca — no hay validación de
  longitud en `build_html`.
- **CB-3 (`cita` con comillas literales incluidas por error)**: criterio editorial del
  comando: la cita se recolecta sin comillas propias (R6); no es una validación del
  motor, es guía de redacción en `story.md`.
- **CB-4 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-5 (flag `ejecutivo`)**: `/story quote ejecutivo` avisa que `/story` no soporta el
  flag (mismo criterio ya vigente para `alerta`) y continúa generando la Story normal.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/quote.html` existe y contiene `width: 1920px` y `height: 1080px` (o
equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:48-49`.

**AC2 — sin fences en `quote.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/quote.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `autor_sub` no vacío (ejecutable, `pytest`)**
DADO el payload `{"cita": "...", "autor": "Nombre Analista", "autor_sub": "Head of
Trading, Grupo Inteligencia"}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/quote.html`,
ENTONCES el HTML resultante contiene el texto de `cita`, `autor` y `autor_sub`
correctamente inyectados y no contiene ningún placeholder `{{...}}` sin resolver (R2/R8).

**AC4 — colapso de `autor_sub` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"autor_sub": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/quote.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `autor_sub` en el CSS del snapshot
declara `:empty { display: none; }` sobre esa clase/selector (R4/R8) — verificable con
`rg ":empty" templates/stories/quote.html` ≥1 match.

**AC5 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story` o equivalente) contra
`templates/stories/quote.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A).

**AC6 — comillas decorativas no vienen del payload (estructural, `rg`)**
`rg "❝|❞|“|”|::before|::after" templates/stories/quote.html` tiene al menos 1 match
asociado al elemento decorativo de comillas en el CSS/HTML del snapshot, confirmando
que el glifo es estático y no un token sustituible (R6).

**AC7 — `[tipo]` `quote` registrado en el comando (estructural, `rg`)**
`rg "quote" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque de recolección editorial (R7).

**AC8 — límite editorial documentado (estructural, `rg`)**
`rg "220" .claude/commands/story.md` ≥1 match asociado al límite recomendado de
longitud de `cita` (R5).

**AC9 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "quote" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R9).

**AC10 — sin regresión del motor ni de Alerta (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
scripts/ruta_story.ps1` no muestra cambios — confirma que el motor, el snapshot de
Alerta y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `quote` en 16:9 (mismo riesgo residual R-2 heredado de
  Fase A/#109). Mitigación: aprobación visual manual del director en la primera corrida
  real de `/story quote`.
- **Riesgo B — límite de 220 caracteres es una estimación editorial, no verificada
  visualmente contra el manual de marca**: si el layout final desborda con citas más
  cortas o admite más largas, el valor se ajusta en `apply` durante la autoría del CSS
  real — no bloquea `specify` (mismo criterio que Fase A dejó el detalle CSS fino para
  `apply`).

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Límite de longitud de `cita`** → R5: 220 caracteres recomendados, criterio
   editorial del comando, sin validación en el motor (CB-2).
2. **`autor_sub` siempre presente vs. puede faltar / necesita fence** → R2/R3: siempre
   presente en el payload (admite `""`), sin fence `IF:autor_sub` — el motor no lo
   soporta a nivel top-level sin tocarlo (decisión firme heredada del `proposal.md`).
3. **Colapso de espaciado con `autor_sub` vacío** → R4: `:empty { display: none; }`
   colapsa también el espacio vertical, no solo el texto.
4. **Origen del texto de la cita (dictado vs. redactado por el modelo)** → R7: ambas
   vías soportadas en el bloque de recolección de `story.md` — el director dicta o
   aprueba una propuesta del modelo.
5. **Fixture propio para el test de mapeo** → R8: no hace falta; se reusa el patrón de
   test contra el snapshot real `quote.html`, igual que `alerta.html`.
6. **Tratamiento tipográfico de comillas** → R6: elemento decorativo estático del
   snapshot (CSS/SVG), nunca parte del valor de `{{cita}}`.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 10
  `quote` (líneas 55-110): payload `cita, autor, autor_sub`, sin gráfico, fondo oscuro,
  fuente "editorial manual".
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`),
  límite de longitud de `parrafo` (línea 154) usado como referencia análoga para R5.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde de este documento y contrato del motor generalizado (R1-R8, AC1-AC12).
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-50` — única plantilla 16:9 existente, referencia de
  esqueleto/paleta/fuentes para autorar `quote.html`.
- `.claude/commands/story.md:1-27` — comando a extender (PASO 0: agregar `quote` a
  `[tipo]`; nuevo bloque de recolección editorial).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `quote`.
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #121 — base de este documento.
- Issue #121 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B.
