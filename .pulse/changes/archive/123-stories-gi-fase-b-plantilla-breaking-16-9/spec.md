# Specification: Stories GI · Fase B — plantilla Breaking 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #123). Fuente
> canónica del contrato de `breaking`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 12, línea 70). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo, y el patrón de campo opcional
> (token + `:empty`) validado en Fase B/`quote` (`.pulse/changes/archive/121-.../spec.md`) sin
> reabrirlo. Resuelve las preguntas abiertas de `idea.md`/`proposal.md` como requisitos
> verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`breaking`** (#12 del catálogo GI) al comando `/story`: una pieza de
última hora con cifra (kicker + titular + valor + contexto + reacción), fondo oscuro/rojo, sin
gráfico y sin listas, alimentada por el criterio editorial de `/noticia` · `/alerta` — a
diferencia de `quote` (100% editorial manual, sin fuente de mercado ni de noticia) y de `alerta`
(que sí trae datos en vivo de `get_asset_levels`). Consume el motor genérico de Fase A
(`scripts/story_render.py`) tal cual quedó, sin tocarlo.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/breaking.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` +
  disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-58`), paleta
  oscura/rojiza reutilizando verbatim el degradado de fondo de `alerta.html:51-54`
  (`#0D0D1A` base, radial `#2A1220`→`#0D0D1A`) más los acentos rojos `#E84040` de
  `alerta.html` (chip/tag, borde de tarjeta, líneas SVG) aplicados al chip `kicker_tema` y
  a la tarjeta de `valor` — sin tarjeta de precio completa (sin variación %, sin
  soporte/resistencia/vol, sin gráfico). Tokens escalares `{{kicker_tema}}`,
  `{{titular}}`, `{{valor}}`, `{{contexto}}`, `{{parrafo_reaccion}}` — **sin fences
  `IF`/`FOR`**.
- Nuevo `[tipo]` `breaking` en `.claude/commands/story.md` PASO 0 (lista dura hoy
  `alerta`, `quote`) + nuevo bloque "Ruta `breaking`" — recolección editorial que
  **no ejecuta búsqueda propia de evento** (no reusa el WebSearch de `/alerta` PASO 1):
  estructura la cifra/evento que el director ya dictó o que ya salió de una corrida
  previa de `/noticia`/`/alerta` en la misma sesión. Reusa el flujo existente (preview →
  aprobación → render → `ruta_story.ps1 -Plantilla "breaking"`), con `-Activo` opcional
  según decisión editorial del director (ver R8).
- Tests de mapeo puros en `tests/test_story_render.py` para `breaking.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo el caso
  `kicker_tema == ""`. Sin fixture nuevo en `tests/fixtures/stories/`, sin tocar
  `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy `alerta`, `quote`) para incluir `breaking`, sin tocar el resto de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `breaking`.
- El contrato de payload de `alerta` y de `quote` — sin cambios.
- Las demás plantillas de Fase B (`encuesta`, `edu`) — cada una su propio Change
  (convención "1 plantilla = 1 Change" heredada de Fase A/B).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fence `<!-- IF:kicker_tema -->` — el motor solo resuelve fences top-level para la
  tupla fija `_FENCES` (4 nombres de Alerta); agregar `kicker_tema` a ese mecanismo
  requeriría tocar el motor, fuera de alcance. `breaking.html` no usa fences (mismo
  criterio que `quote`).
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `breaking` no delega en ningún dato en vivo del motor; `valor` es la cifra
  editorial de la noticia, no un precio de mercado.
- Búsqueda propia de evento/noticia dentro de `story.md` — `breaking` no reusa el
  mecanismo WebSearch de `/alerta` PASO 1; estructura lo que el director ya tiene (R7).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo
  campo-por-campo dedicada a `breaking` en este Change (decisión firme del `proposal.md`,
  punto 7 de la hipótesis); el contrato de campos vive en el design doc de 2026-07-14
  (fila 12) y en este `spec.md`.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin cambios
  a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/breaking.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, degradado de fondo `alerta.html:51-54`, footer estándar). Cuerpo:
chip `{{kicker_tema}}` (etiqueta de categoría/tema, acento rojo `#E84040`, mismo
tratamiento visual que el chip de categoría de `alerta.html`) + `{{titular}}` (tipografía
Syne, mismo peso jerárquico que el titular de Alerta) + tarjeta de `{{valor}}` con
rotulado fijo **"CIFRA CLAVE"** (texto estático del snapshot, no token) y borde/acento
rojo `#E84040` (mismo color que `.tarjeta-precio` de Alerta, pero sin variación %, sin
soporte/resistencia, sin vol — layout deliberadamente distinto al de la tarjeta de
precio, para no sugerir un dato en vivo del motor) + `{{contexto}}` (línea secundaria de
apoyo bajo la cifra) + `{{parrafo_reaccion}}` (párrafo de cierre, tipografía DM Sans).
Sin gráfico, sin chips de gráfico, sin fences `IF`/`FOR` — todos los tokens escalares
incondicionales (mismo criterio que `quote`, confirmado por la tupla fija `_FENCES` que
no cubre ningún campo de `breaking`). Mapea al punto 1 de la hipótesis.

### R2 — Contrato de payload `story_breaking`
```json
{
  "plantilla": "breaking",
  "kicker_tema": "BANCOS CENTRALES",
  "titular": "La Fed sorprende con una pausa más larga de lo esperado",
  "valor": "5,50%",
  "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
  "parrafo_reaccion": "El mercado ajusta expectativas hacia un primer recorte más tardío, presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
}
```
- `kicker_tema`, `titular`, `valor`, `contexto`, `parrafo_reaccion` son las únicas claves
  del payload (sin campos array, sin `chart_png`, sin dato del motor).
- `kicker_tema` es un token **siempre presente** en el payload (nunca ausente/`None`)
  que admite string vacío `""` — es el único campo opcional del contrato (resuelve la
  pregunta abierta 1 de `idea.md`/`proposal.md`: el candidato es `kicker_tema`, cuando la
  noticia no cae en una categoría editorial clara).
- `titular`, `valor`, `contexto` y `parrafo_reaccion` son siempre no vacíos — el comando
  (R7) nunca construye el payload con alguno de estos cuatro campos como `""`; si el
  director no puede dar contexto o reacción, el comando insiste o usa una redacción
  editorial mínima, nunca cadena vacía en estos cuatro.
- `valor` es la cifra editorial de la noticia (dato macro, porcentaje, nivel mencionado
  en la nota) — **no** un precio en vivo del motor; no lleva formateo `digits` de
  `config/activos.json` (eso es exclusivo de precios de activos vía `get_asset_levels`).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `breaking`.

### R3 — Sin fences `IF`/`FOR` en `breaking.html`
`breaking.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`.
Justificación (confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences
top-level de `_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de
Alerta); el fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un
bloque `FOR`, que `breaking` no usa (sin arrays). Por tanto ningún campo de `breaking`
puede condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens
son escalares incondicionales, y el único campo opcional (`kicker_tema`) se resuelve vía
CSS (R4), no vía fence. Mismo criterio que `quote` R3.

### R4 — Colapso visual de `kicker_tema` vacío (CSS, no motor)
Cuando `kicker_tema == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano,
no hay error de guardia. El contenedor HTML del token `kicker_tema` (ej.
`<span class="breaking-kicker">{{kicker_tema}}</span>`) usa la regla CSS
`:empty { display: none; }` sobre ese contenedor, de forma que:
- Con `kicker_tema` no vacío: se muestra el chip sobre el titular.
- Con `kicker_tema == ""`: el contenedor no ocupa espacio (colapsa `display: none`, no
  solo el texto) — el titular sube sin hueco en blanco donde estaría el chip. Mismo
  patrón exacto validado en `quote` R4 (`.quote-cargo:empty`).

### R5 — Rotulado fijo de `valor` (distinción de un precio de mercado)
La tarjeta de `{{valor}}` en `breaking.html` incluye la etiqueta estática **"CIFRA
CLAVE"** (texto fijo del snapshot, no un token) inmediatamente junto al valor, y omite
deliberadamente todo elemento visual asociado a un dato de mercado en vivo: sin flecha de
variación (▲/▼), sin color verde/rojo condicional por dirección, sin fila de
soporte/resistencia/vol, sin rótulo de ticker/activo. Resuelve la pregunta abierta 3 de
`idea.md`/`proposal.md` (tratamiento tipográfico/rotulado de `valor` que lo distinga de
un precio del motor).

### R6 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), los límites recomendados:
- `kicker_tema` ≤ 30 caracteres (chip corto, una sola línea).
- `titular` ≤ 70 caracteres (mismo límite que `titular` de Alerta,
  `.pulse/specs/stories-gi/spec.md:154`).
- `contexto` ≤ 100 caracteres (línea secundaria de apoyo bajo la cifra, más corta que un
  párrafo).
- `parrafo_reaccion` ≤ 280 caracteres (mismo límite que `parrafo` de Alerta).
El comando ajusta la redacción antes del preview si algún campo excede su límite; el
motor no valida longitud (mismo criterio que Alerta/`quote`: la guardia solo valida
tokens huérfanos, no longitud de contenido).

### R7 — Recolección editorial en `story.md` sin búsqueda propia de evento
`.claude/commands/story.md` PASO 0 agrega `breaking` a la lista de `[tipo]` soportados
(junto a `alerta`, `quote`). Nuevo bloque "Ruta `breaking`":
1. Pregunta si el director ya corrió `/noticia` o `/alerta` en la misma sesión (o tiene
   ya redactado el evento/cifra) — de ser así, reutiliza esos textos como base editorial.
   Si no, pide al director que dicte directamente `kicker_tema` (opcional), `titular`,
   `valor`, `contexto` y `parrafo_reaccion`.
2. **`breaking` no ejecuta su propia búsqueda de evento** (no invoca WebSearch ni el
   mecanismo de detección de `/alerta` PASO 1) — estructura y valida lo que el director
   ya tiene, sin investigar por cuenta propia. Resuelve la pregunta abierta 4 de
   `idea.md`/proposal.md (decisión firme del `proposal.md`, punto 3 de la hipótesis).
3. Dirección explícita obligatoria (regla de oro del repo): el titular/contexto/reacción
   deben dejar clara la lectura direccional del evento (ej. qué activo o mercado se ve
   afectado y hacia dónde), con registro profesional del repo (énfasis sin
   dramatización, `CLAUDE.md` "Registro y tono").
4. Construye el payload con `kicker_tema` **siempre presente** — si el director no da un
   tema/categoría claro, `"kicker_tema": ""` (nunca omitir la clave).

### R8 — Guardado con o sin `-Activo` (decisión editorial)
A diferencia de `quote` (siempre `_general`), el bloque "Ruta `breaking`" de `story.md`
pregunta al director si la noticia tiene un activo protagonista claro (ej. un dato de la
Fed que mueve XAUUSD):
- **Si lo tiene**: pasa `-Activo [TICKER_MT5]` a `ruta_story.ps1` (normalizado contra
  `config/activos.json`, mismo criterio que `/chart` PASO 1).
- **Si no lo tiene** (cifra macro sin activo protagonista único, ej. IPC general): se
  guarda bajo `-Activo "_general"`, igual que `quote`.
El criterio de decisión es editorial (lo decide el director al responder la pregunta),
no una regla automática nueva del motor ni de `ruta_story.ps1`. Resuelve la pregunta
abierta 5 de `idea.md`/proposal.md (decisión firme del `proposal.md`, punto 4 de la
hipótesis).

### R9 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `quote.html`:
1. Test de mapeo con `kicker_tema` no vacío: `build_html` sobre `breaking.html` con el
   payload de R2 produce HTML sin placeholders sin resolver, con `kicker_tema`,
   `titular`, `valor`, `contexto` y `parrafo_reaccion` correctamente inyectados.
2. Test de mapeo con `kicker_tema == ""`: mismo `build_html`, el HTML resultante no
   contiene ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se
   omitió el campo).
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `breaking.html`, igual que `quote.html`/`alerta.html`). Sin cambios en
`conftest.py`.

### R10 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza
para incluir `breaking` junto a `alerta` y `quote` (ej. "`[tipo]` soportados hoy:
`alerta`, `quote`, `breaking`"), sin tocar el resto del párrafo/sección.

## Casos borde

- **CB-1 (`kicker_tema` ausente del payload, no `""`)**: el comando (PASO de
  recolección, R7) siempre construye el payload con la clave `kicker_tema` presente,
  aunque sea `""` — nunca omite la clave. Si por error se omitiera, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que Alerta/`quote`), no
  un colapso silencioso distinto al de R4.
- **CB-2 (algún campo de longitud excede el límite editorial de R6)**: el comando ajusta
  la redacción antes del preview; el motor no aborta ni trunca — no hay validación de
  longitud en `build_html`.
- **CB-3 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-4 (flag `ejecutivo`)**: `/story breaking ejecutivo` avisa que `/story` no soporta
  el flag (mismo criterio ya vigente para `alerta`/`quote`) y continúa generando la Story
  normal.
- **CB-5 (director no tiene corrida previa de `/noticia`/`/alerta` ni evento claro)**: el
  comando pide que dicte directamente los 5 campos; no bloquea ni exige una corrida
  previa de otro comando (R7 no es una dependencia dura, solo un atajo si ya existe el
  texto).
- **CB-6 (`valor` sin unidad clara, ej. solo un número)**: criterio editorial del
  comando: `valor` se recolecta como texto ya formateado con su unidad si aplica (ej.
  `"5,50%"`, `"US$ 2.318"`) — no es una validación del motor, es guía de redacción en
  `story.md` (mismo criterio que R6 de `quote` para comillas).
- **CB-7 (activo protagonista ambiguo o con múltiples activos afectados)**: el director
  decide, al responder la pregunta de R8, si hay un activo protagonista único; si no lo
  hay con claridad, se guarda bajo `_general` (mismo criterio que `quote`).

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/breaking.html` existe y contiene `width: 1920px` y `height: 1080px`
(o equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:49-50`.

**AC2 — sin fences en `breaking.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/breaking.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `kicker_tema` no vacío (ejecutable, `pytest`)**
DADO el payload `{"kicker_tema": "BANCOS CENTRALES", "titular": "La Fed sorprende con una
pausa más larga de lo esperado", "valor": "5,50%", "contexto": "Tasa de referencia sin
cambios por tercera reunión consecutiva", "parrafo_reaccion": "El mercado ajusta
expectativas hacia un primer recorte más tardío, presionando al dólar al alza y a los
activos de riesgo a la baja en la sesión."}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/breaking.html`,
ENTONCES el HTML resultante contiene el texto de `kicker_tema`, `titular`, `valor`,
`contexto` y `parrafo_reaccion` correctamente inyectados y no contiene ningún
placeholder `{{...}}` sin resolver (R2/R9).

**AC4 — colapso de `kicker_tema` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker_tema": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/breaking.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `kicker_tema` en el CSS del snapshot
declara `:empty { display: none; }` sobre esa clase/selector (R4/R9) — verificable con
`rg ":empty" templates/stories/breaking.html` ≥1 match.

**AC5 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story`) contra
`templates/stories/breaking.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A / AC5 de `quote`).

**AC6 — rotulado fijo "CIFRA CLAVE" y sin elementos de precio en vivo (estructural, `rg`)**
`rg -i "CIFRA CLAVE" templates/stories/breaking.html` ≥1 match (texto estático, R5);
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/breaking.html`
→ 0 matches (confirma que `breaking.html` no reutiliza el layout de tarjeta de precio de
Alerta ni sus tokens).

**AC7 — `[tipo]` `breaking` registrado en el comando (estructural, `rg`)**
`rg "breaking" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque "Ruta `breaking`" (R7).

**AC8 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30" .claude/commands/story.md` ≥1 match asociado a los
límites recomendados de `titular`/`contexto`/`parrafo_reaccion`/`kicker_tema` (R6).

**AC9 — `story.md` documenta que `breaking` no busca su propio evento (estructural, `rg`)**
`rg -i "no ejecuta su propia búsqueda|no busca por cuenta propia|no reusa" .claude/commands/story.md`
≥1 match dentro del bloque "Ruta `breaking`" (R7, decisión firme del `proposal.md`).

**AC10 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "breaking" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R10).

**AC11 — sin regresión del motor ni de Alerta/`quote` (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html scripts/ruta_story.ps1` no muestra cambios — confirma que
el motor, los snapshots existentes y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `breaking` en 16:9 (mismo riesgo residual R-2 heredado
  de Fase A/#109 y de `quote`/#121). Mitigación: aprobación visual manual del director en
  la primera corrida real de `/story breaking`.
- **Riesgo B — rotulado "CIFRA CLAVE" es una decisión editorial de este documento, no
  verificada visualmente contra el manual de marca**: si el layout final necesita otro
  texto/tratamiento, el copy se ajusta en `apply` durante la autoría del CSS real — no
  bloquea `specify` (mismo criterio que Fase A/`quote` dejaron el detalle CSS fino para
  `apply`).
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir
  golden PNG, los límites exactos en caracteres pueden requerir ajuste tras la primera
  corrida visual real; se documentan como guía editorial del comando, no como
  validación dura del motor (mismo criterio que Riesgo B de `quote`).

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **¿Qué campo(s) activan el patrón "token + `:empty`"?** → R2/R4: único campo
   opcional es `kicker_tema` (siempre presente, admite `""`); `titular`, `valor`,
   `contexto` y `parrafo_reaccion` son siempre no vacíos en el payload construido por
   el comando.
2. **Documentación de mapeo campo-por-campo en `plantillas-stories-gi.md`** → fuera de
   alcance de este Change (ver "OUT"), decisión firme heredada del `proposal.md`.
3. **Tratamiento tipográfico/rotulado de `valor` vs. precio de mercado** → R5: etiqueta
   estática "CIFRA CLAVE" junto al valor; sin flecha de variación, sin color
   condicional por dirección, sin fila de soporte/resistencia/vol.
4. **¿El bloque "Ruta `breaking`" reusa el WebSearch de `/alerta` PASO 1?** → R7: no —
   estructura lo que el director ya dictó o ya generó con `/noticia`/`/alerta` en la
   misma sesión; no investiga por cuenta propia.
5. **¿`breaking` se guarda con o sin `-Activo`?** → R8: ambos caminos soportados,
   decisión editorial del director al responder la pregunta de recolección; sin activo
   protagonista claro → `_general` (mismo criterio que `quote`).

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 12
  `breaking` (línea 70): payload `kicker_tema, titular, valor, contexto,
  parrafo_reaccion`, sin gráfico, fondo oscuro/rojo, fuente `/noticia` · `/alerta`.
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  `story_quote`); límite de longitud de `parrafo`/`titular` de Alerta usado como
  referencia análoga para R6.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde del motor generalizado (R1-R8, AC1-AC12), no se reabre.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/spec.md` — molde
  directo de este documento; patrón de campo opcional (token + `:empty`) validado y
  reutilizado sin cambios en R4.
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-58,108,145-202,363-391` — referencia de esqueleto,
  degradado de fondo y acentos rojos (`#E84040`) que `breaking` reutiliza para chip y
  tarjeta de cifra.
- `templates/stories/quote.html` — molde más cercano de plantilla simple sin
  fences/loops, con campo opcional resuelto vía `:empty` CSS (`.quote-cargo:empty`).
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `breaking` a
  `[tipo]` junto a `alerta`, `quote`; nuevo bloque "Ruta `breaking`" análogo a "Ruta
  `quote`", líneas 40-104).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `breaking` (mismo patrón que `test_quote_no_placeholders`/`test_quote_autor_sub_vacio`,
  líneas 295-312).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #123 — base de este documento.
- Issue #123 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B ·
  `breaking`; issues #121 (quote, precedente cerrado) y #119 (motor, fundacional).
