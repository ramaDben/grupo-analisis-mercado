# Specification: Stories GI · Fase B — plantilla Encuesta 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #125). Fuente
> canónica del contrato de `encuesta`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 09, línea 67). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo, y el patrón de campo opcional
> (token + `:empty`) validado en Fase B/`quote` (`.pulse/changes/archive/121-.../spec.md`) y
> replicado en Fase B/`breaking` (`.pulse/changes/archive/123-.../spec.md`) sin reabrirlo.
> Resuelve las preguntas abiertas de `idea.md`/`proposal.md` como requisitos verificables
> (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`encuesta`** (#09 del catálogo GI) al comando `/story`: una pieza de
sentimiento binario (kicker + pregunta + dos opciones + nota de cierre), fondo oscuro/azul, sin
gráfico y sin listas, alimentada por el criterio editorial 100% de sentimiento puro de
`/encuesta` (sin precios, sin educación, sin dato del motor) — a diferencia de `alerta` (datos
en vivo de `get_asset_levels`) y en la misma familia editorial que `quote`/`breaking` (100%
manual/editorial). Consume el motor genérico de Fase A (`scripts/story_render.py`) tal cual
quedó, sin tocarlo.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/encuesta.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` +
  disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-58`), paleta
  **oscura/azul** — reemplaza el acento rojo `#E84040`/radial `#2A1220` (usado en
  `alerta`/`quote`/`breaking`) por un acento azul derivado de la paleta GI ya presente en
  el repo (candidatos del design doc: `#1E3A5F`/`#3E91AF`/`#53C1AB`; el hex exacto se fija
  en `apply`, no en `specify` — ver Riesgo B). Tokens escalares `{{kicker}}`,
  `{{pregunta}}`, `{{opcion_a}}`, `{{opcion_b}}`, `{{nota_cierre}}` — **sin fences
  `IF`/`FOR`**.
- Nuevo `[tipo]` `encuesta` en `.claude/commands/story.md` PASO 0 (lista dura hoy
  `alerta`, `quote`, `breaking`) + nuevo bloque "Ruta `encuesta`" — recolección editorial
  con el criterio de sentimiento puro de `/encuesta` (pregunta + dos opciones, sin
  precios ni datos de mercado), que **no llama a `get_asset_levels`** ni ejecuta
  búsqueda propia de evento. Reusa el flujo existente (preview → aprobación → render →
  `ruta_story.ps1 -Plantilla "encuesta"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `encuesta.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo los casos
  `kicker == ""` y `nota_cierre == ""`. Sin fixture nuevo en `tests/fixtures/stories/`,
  sin tocar `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy `alerta`, `quote`, `breaking`) para incluir `encuesta`, sin tocar el resto de la
  sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `encuesta`.
- El contrato de payload de `alerta`, `quote` y `breaking` — sin cambios.
- La última plantilla de Fase B (`edu`) — su propio Change (convención "1 plantilla = 1
  Change" heredada de Fase A/B).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fences `<!-- IF:kicker -->`/`<!-- IF:nota_cierre -->` — el motor solo resuelve fences
  top-level para la tupla fija `_FENCES` (4 nombres de Alerta); agregar `kicker` o
  `nota_cierre` a ese mecanismo requeriría tocar el motor, fuera de alcance.
  `encuesta.html` no usa fences (mismo criterio que `quote`/`breaking`).
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `encuesta` no delega en ningún dato en vivo del motor; es 100% sentimiento
  editorial, mismo contrato que `/encuesta` (CLAUDE.md: "3 tipos sin precios ni
  educación").
- Distinguir en `story.md` entre los 3 tipos de `/encuesta` (`posicion`, `tendencia`,
  `movimiento`) para adaptar el layout — la Story usa siempre el mismo layout binario
  `opcion_a`/`opcion_b` sin importar el tipo de encuesta de origen (resuelto en
  "Preguntas abiertas — resueltas").
- El hex exacto del acento azul — decisión de `apply` (autoría del CSS real), no
  bloqueante para `specify` (mismo criterio que Riesgo B de `breaking`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo
  campo-por-campo dedicada a `encuesta` en este Change (mismo criterio que `breaking`);
  el contrato de campos vive en el design doc de 2026-07-14 (fila 09) y en este
  `spec.md`.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin
  cambios a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/encuesta.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, footer estándar) con paleta **oscura/azul** en vez de oscura/rojo.
Cuerpo: chip `{{kicker}}` (etiqueta opcional, ej. "ENCUESTA DEL DÍA" o tema libre —
criterio editorial, ver R7) + `{{pregunta}}` (texto destacado, tipografía Syne, núcleo
obligatorio) + `{{opcion_a}}`/`{{opcion_b}}` (dos bloques comparativos tipo "A vs B",
núcleo obligatorio, layout simétrico lado a lado) + `{{nota_cierre}}` (línea de cierre
discreta, opcional). Sin gráfico, sin fences `IF`/`FOR` — 5 tokens escalares
incondicionales (mismo criterio que `quote`/`breaking`, confirmado por la tupla fija
`_FENCES` que no cubre ningún campo de `encuesta`). Mapea al punto 1 de la hipótesis.

### R2 — Contrato de payload `story_encuesta`
```json
{
  "plantilla": "encuesta",
  "kicker": "ENCUESTA DEL DÍA",
  "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
  "opcion_a": "Alcista",
  "opcion_b": "Bajista",
  "nota_cierre": "Vota en la encuesta fijada del grupo"
}
```
- `plantilla`, `kicker`, `pregunta`, `opcion_a`, `opcion_b`, `nota_cierre` son las únicas
  claves del payload (sin campos array, sin `chart_png`, sin dato del motor).
- `pregunta`, `opcion_a` y `opcion_b` son siempre no vacíos — el comando (R7) nunca
  construye el payload con alguno de estos tres campos como `""`; son el núcleo mínimo
  de una encuesta binaria.
- `kicker` y `nota_cierre` son tokens **siempre presentes** en el payload (nunca
  ausentes/`None`) que admiten string vacío `""` — son los dos campos opcionales del
  contrato (mismo patrón exacto que `autor_sub` en `quote` y `kicker_tema` en
  `breaking`).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `encuesta`.
- `pregunta`/`opcion_a`/`opcion_b` son texto editorial de sentimiento puro (mismo
  criterio que el mensaje WhatsApp de `/encuesta`) — no llevan formateo `digits` de
  `config/activos.json` ni ningún dato en vivo del motor.

### R3 — Sin fences `IF`/`FOR` en `encuesta.html`
`encuesta.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`.
Justificación (confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences
top-level de `_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de
Alerta); el fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un
bloque `FOR`, que `encuesta` no usa (sin arrays). Por tanto ningún campo de `encuesta`
puede condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens
son escalares incondicionales, y los dos campos opcionales (`kicker`, `nota_cierre`) se
resuelven vía CSS (R4), no vía fence. Mismo criterio que `quote` R3 / `breaking` R3.

### R4 — Colapso visual de `kicker` y `nota_cierre` vacíos (CSS, no motor)
Cuando `kicker == ""` o `nota_cierre == ""`, el token se sustituye igual (cadena vacía)
— no hay huérfano, no hay error de guardia. Los contenedores HTML de ambos tokens (ej.
`<span class="encuesta-kicker">{{kicker}}</span>` y
`<p class="encuesta-nota">{{nota_cierre}}</p>`) usan la regla CSS `:empty { display:
none; }` sobre cada contenedor, de forma que:
- Con el campo no vacío: se muestra el elemento (chip sobre la pregunta / línea de
  cierre bajo las opciones).
- Con el campo vacío: el contenedor no ocupa espacio (colapsa `display: none`, no solo
  el texto) — el layout se reacomoda sin hueco en blanco. Mismo patrón exacto validado en
  `quote` R4 (`.quote-cargo:empty`) y `breaking` R4 (`.breaking-kicker:empty`).

### R5 — Layout "A vs B" de `opcion_a`/`opcion_b`
`opcion_a` y `opcion_b` se presentan como dos bloques simétricos lado a lado (tipo
"A vs B"), cada uno con su propio rótulo visual estático (ej. "OPCIÓN A" / "OPCIÓN B" o
un separador central "VS", texto fijo del snapshot, no token) — sin flecha de
variación, sin color condicional por dirección, sin fila de soporte/resistencia/vol
(mismo criterio de distinción de un dato de mercado en vivo que R5 de `breaking`).
Resuelve la pregunta abierta de layout de `idea.md`/`proposal.md`.

### R6 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), los límites recomendados:
- `kicker` ≤ 30 caracteres (chip corto, una sola línea, mismo límite que `kicker_tema`
  de `breaking`).
- `pregunta` ≤ 90 caracteres (texto destacado central, ligeramente más largo que
  `titular` de Alerta/`breaking` por incluir la formulación completa de la pregunta).
- `opcion_a`/`opcion_b` ≤ 25 caracteres cada una (etiqueta corta de una sola opción,
  ej. "Alcista", "Bajista", "Sube", "Baja").
- `nota_cierre` ≤ 80 caracteres (línea discreta de cierre, más corta que `contexto` de
  `breaking`).
El comando ajusta la redacción antes del preview si algún campo excede su límite; el
motor no valida longitud (mismo criterio que Alerta/`quote`/`breaking`: la guardia solo
valida tokens huérfanos, no longitud de contenido).

### R7 — Recolección editorial en `story.md` sin datos de mercado
`.claude/commands/story.md` PASO 0 agrega `encuesta` a la lista de `[tipo]` soportados
(junto a `alerta`, `quote`, `breaking`). Nuevo bloque "Ruta `encuesta`":
1. Pregunta la pregunta binaria y sus dos opciones, con el mismo criterio editorial de
   `/encuesta` (sentimiento puro, sin precios ni educación — ver contrato de `/encuesta`
   en `CLAUDE.md` "Encuestas diarias"):
   ```
   ¿Cuál es la pregunta de la encuesta? (ej. "¿Cuál creen que será la tendencia hoy del Oro?")
   ¿Opción A?
   ¿Opción B?
   ¿Kicker/tema del chip? (ej. "ENCUESTA DEL DÍA" — Intro para omitir)
   ¿Nota de cierre? (ej. "Vota en la encuesta fijada del grupo" — Intro para omitir)
   ```
2. **`encuesta` no llama a `get_asset_levels`** ni a ninguna tool de mercado
   (`obtener_calendario_macro`, `get_chart_objects`, `get_symbol_spec`), y **no ejecuta
   su propia búsqueda de evento** (no invoca WebSearch) — es una pieza 100% editorial de
   sentimiento, igual criterio que `quote`/`breaking`, heredado del contrato de
   `/encuesta`.
3. Si el director ya corrió `/encuesta [tipo] [activo]` en la misma sesión, el bloque
   ofrece reutilizar la pregunta/opciones ya redactadas ahí como base editorial (atajo
   opcional, no obligatorio — mismo criterio que R7.1 de `breaking`).
4. La Story usa siempre el mismo layout binario `opcion_a`/`opcion_b`, sin distinguir
   entre los 3 tipos de `/encuesta` (`posicion`, `tendencia`, `movimiento`) — el
   contenido de la pregunta/opciones ya refleja el tipo en su redacción, no en el
   layout (resuelve la pregunta abierta "¿el bloque distingue entre tipos de
   `/encuesta`?" de `idea.md`/`proposal.md`).
5. Construye el payload con `kicker` y `nota_cierre` **siempre presentes** — si el
   director no da alguno, `""` (nunca omitir la clave).

### R8 — Guardado con o sin `-Activo` (decisión editorial)
El bloque "Ruta `encuesta`" de `story.md` pregunta al director si la pregunta nombra un
activo protagonista claro (ej. "¿Cuál creen que será la tendencia hoy del Oro?" → Oro
protagonista; a diferencia de `quote`, que siempre es `_general`):
- **Si lo tiene**: pasa `-Activo [TICKER_MT5]` a `ruta_story.ps1` (normalizado contra
  `config/activos.json`, mismo criterio que `/chart` PASO 1).
- **Si no lo tiene** (pregunta general de sentimiento sin activo único, ej. "¿Suben o
  bajan los mercados esta semana?"): se guarda bajo `-Activo "_general"`, igual que
  `quote`/`breaking` sin activo protagonista.
El criterio de decisión es editorial (lo decide el director al responder la pregunta),
no una regla automática nueva del motor ni de `ruta_story.ps1`. Resuelve la pregunta
abierta de `idea.md`/`proposal.md` sobre `-Activo` vs `_general` en `encuesta`.

### R9 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `breaking.html`:
1. Test de mapeo con `kicker` y `nota_cierre` no vacíos: `build_html` sobre
   `encuesta.html` con el payload de R2 produce HTML sin placeholders sin resolver, con
   `kicker`, `pregunta`, `opcion_a`, `opcion_b` y `nota_cierre` correctamente inyectados.
2. Test de mapeo con `kicker == ""`: mismo `build_html`, el HTML resultante no contiene
   ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se omitió el
   campo).
3. Test de mapeo con `nota_cierre == ""`: mismo criterio que el punto 2, para el
   segundo campo opcional.
4. Test de dimensiones del render (`skipif` sin Chromium): PNG con IHDR exactamente
   `(1920, 1080)` y tamaño > 5 KB, mismo umbral que `breaking`/`quote`.
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `encuesta.html`, igual que `quote.html`/`breaking.html`). Sin cambios en
`conftest.py`.

### R10 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza
para incluir `encuesta` junto a `alerta`, `quote` y `breaking` (ej. "`[tipo]` soportados
hoy: `alerta`, `quote`, `breaking`, `encuesta`"), sin tocar el resto del
párrafo/sección.

## Casos borde

- **CB-1 (`kicker`/`nota_cierre` ausentes del payload, no `""`)**: el comando (PASO de
  recolección, R7) siempre construye el payload con ambas claves presentes, aunque sean
  `""` — nunca las omite. Si por error se omitiera alguna, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que
  Alerta/`quote`/`breaking`), no un colapso silencioso distinto al de R4.
- **CB-2 (algún campo de longitud excede el límite editorial de R6)**: el comando
  ajusta la redacción antes del preview; el motor no aborta ni trunca — no hay
  validación de longitud en `build_html`.
- **CB-3 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-4 (flag `ejecutivo`)**: `/story encuesta ejecutivo` avisa que `/story` no
  soporta el flag (mismo criterio ya vigente para `alerta`/`quote`/`breaking`) y
  continúa generando la Story normal.
- **CB-5 (tipo `/story` inválido, incluyendo un valor de `[tipo]` que no es `alerta`,
  `quote`, `breaking` ni `encuesta`)**: `.claude/commands/story.md` PASO 0 informa la
  lista actualizada de tipos disponibles (`alerta`, `quote`, `breaking`, `encuesta`) y
  vuelve a preguntar — nunca asume un tipo por defecto (mismo criterio CB-1 heredado de
  `.pulse/specs/stories-gi/spec.md`).
- **CB-6 (pregunta nombra un activo protagonista ambiguo o varios activos)**: el
  director decide, al responder la pregunta de R8, si hay un activo protagonista único;
  si no lo hay con claridad, se guarda bajo `_general` (mismo criterio que
  `quote`/`breaking`).
- **CB-7 (opciones no son estrictamente antónimos, ej. "Alcista" vs "Lateral")**: el
  comando no valida que `opcion_a`/`opcion_b` sean opuestos exactos — es criterio
  editorial del director al redactar la encuesta (misma libertad que el mensaje
  WhatsApp de `/encuesta`), la plantilla solo garantiza el layout "A vs B" (R5).
- **CB-8 (director ya corrió `/encuesta [tipo] [activo]` en la misma sesión)**: el
  bloque "Ruta `encuesta`" ofrece reutilizar esa pregunta/opciones como base editorial
  (R7.3); no es una dependencia dura — si el director prefiere redactar de cero, lo
  hace directamente.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/encuesta.html` existe y contiene `width: 1920px` y `height: 1080px`
(o equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:49-50`.

**AC2 — sin fences en `encuesta.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/encuesta.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `kicker`/`nota_cierre` no vacíos (ejecutable, `pytest`)**
DADO el payload `{"kicker": "ENCUESTA DEL DÍA", "pregunta": "¿Cuál creen que será la
tendencia hoy del Oro?", "opcion_a": "Alcista", "opcion_b": "Bajista", "nota_cierre":
"Vota en la encuesta fijada del grupo"}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante contiene el texto de `kicker`, `pregunta`, `opcion_a`,
`opcion_b` y `nota_cierre` correctamente inyectados y no contiene ningún placeholder
`{{...}}` sin resolver (R2/R9).

**AC4 — colapso de `kicker` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `kicker` en el CSS del snapshot declara
`:empty { display: none; }` sobre esa clase/selector (R4/R9) — verificable con
`rg ":empty" templates/stories/encuesta.html` ≥2 matches (uno por cada campo opcional).

**AC5 — colapso de `nota_cierre` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"nota_cierre": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver, y el
contenedor de `nota_cierre` declara `:empty { display: none; }` (R4/R9).

**AC6 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story`) contra
`templates/stories/encuesta.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A / AC5 de `quote`/`breaking`).

**AC7 — layout "A vs B" sin elementos de dato de mercado en vivo (estructural, `rg`)**
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/encuesta.html`
→ 0 matches (confirma que `encuesta.html` no reutiliza el layout de tarjeta de precio de
Alerta ni sus tokens, R5).

**AC8 — `[tipo]` `encuesta` registrado en el comando (estructural, `rg`)**
`rg "encuesta" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque "Ruta `encuesta`" (R7).

**AC9 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" .claude/commands/story.md` ≥1 match asociado a los
límites recomendados de `kicker`/`pregunta`/`opcion_a`/`opcion_b`/`nota_cierre` (R6).

**AC10 — `story.md` documenta que `encuesta` no llama a datos de mercado (estructural,
`rg`)**
`rg -i "no llama a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado" .claude/commands/story.md`
≥1 match dentro del bloque "Ruta `encuesta`" (R7).

**AC11 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "encuesta" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R10), sin contar
las menciones ya existentes al comando `/encuesta` de texto plano (distinguir por
contexto: la mención nueva debe estar en la enumeración de `[tipo]` de `/story`).

**AC12 — sin regresión del motor ni de Alerta/`quote`/`breaking` (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html templates/stories/breaking.html scripts/ruta_story.ps1` no
muestra cambios — confirma que el motor, los snapshots existentes y el helper de
guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `encuesta` en 16:9 azul (mismo riesgo residual R-2
  heredado de Fase A/#109 y de `quote`/`breaking`). Mitigación: aprobación visual manual
  del director en la primera corrida real de `/story encuesta`.
- **Riesgo B — hex exacto del azul no fijado en `specify`**: el design doc solo da
  candidatos (`#1E3A5F`/`#3E91AF`/`#53C1AB`); ninguna plantilla ya renderizada en el
  repo usa hoy un fondo azul. El valor final se decide en `apply` durante la autoría del
  CSS real, no bloquea `specify` (mismo criterio que Riesgo B de `breaking` para el
  rotulado "CIFRA CLAVE").
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir
  golden PNG, los límites exactos en caracteres pueden requerir ajuste tras la primera
  corrida visual real; se documentan como guía editorial del comando, no como
  validación dura del motor (mismo criterio que Riesgo C de `breaking`).
- **Riesgo D — rol semántico de `kicker` ambiguo**: el design doc no especifica si
  `kicker` es una etiqueta fija ("ENCUESTA DEL DÍA") o libre por tema — se resuelve como
  campo libre editorial (mismo tratamiento que `kicker_tema` de `breaking`), ajustable
  por el director en cada corrida; no bloquea `specify` (ver "Preguntas abiertas —
  resueltas").

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Paleta azul exacta** → Riesgo B: candidatos documentados
   (`#1E3A5F`/`#3E91AF`/`#53C1AB`), hex final decidido en `apply` (autoría del CSS),
   sin bloquear `specify`.
2. **¿`kicker` es rol fijo o libre?** → Riesgo D/R7.1: campo libre editorial (mismo
   tratamiento que `kicker_tema` de `breaking`), el director lo redacta o lo omite en
   cada corrida.
3. **Layout de `opcion_a`/`opcion_b`** → R5: dos bloques simétricos lado a lado tipo
   "A vs B", con rótulo estático (no token) que distingue las dos opciones.
4. **¿`encuesta` se guarda con `-Activo` o siempre `_general`?** → R8: ambos caminos
   soportados, decisión editorial del director al responder la pregunta de
   recolección; sin activo protagonista claro → `_general` (mismo criterio que
   `quote`/`breaking`).
5. **Sección de mapeo campo-por-campo en `plantillas-stories-gi.md`** → fuera de
   alcance de este Change (ver "OUT"), mismo criterio que `breaking`.
6. **¿El bloque "Ruta `encuesta`" distingue entre los 3 tipos de `/encuesta`
   (`posicion`, `tendencia`, `movimiento`)?** → R7.4: no — la Story usa siempre el
   mismo layout binario `opcion_a`/`opcion_b`; el tipo de origen se refleja en la
   redacción de la pregunta/opciones, no en el layout.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 09
  `encuesta` (línea 67): payload `kicker, pregunta, opcion_a, opcion_b, nota_cierre`,
  sin gráfico, fondo oscuro/azul, fuente `/encuesta`; línea 24-26 (paleta de acentos de
  marca); línea 91 (plan de fases: Fase B = `quote`, `breaking`, `encuesta`, `edu`).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  `story_quote`, `story_breaking`) como precedente directo de formato para
  `story_encuesta`.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde del motor generalizado (R1-R8, AC1-AC12), no se reabre.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/spec.md` — molde
  fundacional del patrón de campo opcional (token + `:empty`).
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/spec.md` —
  molde estructural directo de este documento (mismo patrón "1 snapshot + 1 bloque de
  recolección + tests de mapeo puros + `CLAUDE.md`"); dos campos opcionales replicados
  con el mismo criterio que `kicker_tema`.
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-58` — referencia de esqueleto de marca (fuentes,
  footer) reutilizado sin los acentos rojos/rojizos.
- `templates/stories/breaking.html:85-99,191` y `templates/stories/quote.html:119-127,164`
  — molde directo del patrón `:empty` para los dos campos opcionales de `encuesta`.
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `encuesta` a
  `[tipo]` junto a `alerta`, `quote`, `breaking`; nuevo bloque "Ruta `encuesta`" análogo
  a "Ruta `breaking`", líneas 110-196).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `encuesta` (mismo patrón que `test_breaking_no_placeholders`/
  `test_breaking_kicker_vacio`/`test_breaking_render_dimensiones`, líneas 349-379).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- Contrato editorial `/encuesta` (`CLAUDE.md` sección "Encuestas diarias"; memoria
  `project_encuesta_sentimiento`): sentimiento puro, sin precios ni educación —
  `encuesta` (Story) hereda esta restricción.
- `idea.md`, `proposal.md` de este mismo Change #125 — base de este documento.
- Issue madre de esta Fase B · `encuesta` (a vincular en GitHub); issues #121 (quote) y
  #123 (breaking) como precedentes cerrados directos.
