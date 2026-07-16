# Specification: Stories GI · Fase B — plantilla Edu (concepto educativo) 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #127). Fuente
> canónica del contrato de `edu`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 07, línea 65; nota bullets/FOR línea 76). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo — incluido el mecanismo `FOR`
> (`resolver_loops`) ya implementado y testeado ahí. Hereda el patrón de campo opcional
> (token + `:empty`) validado en `quote` (#121), `breaking` (#123) y `encuesta` (#125) sin
> reabrirlos. Resuelve las preguntas abiertas de `idea.md`/`proposal.md` como requisitos
> verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`edu`** (#07 del catálogo GI) al comando `/story`: una pieza educativa
(kicker + título del concepto + definición + ejemplo comparativo + lista de bullets de
aplicación), fondo **oscuro**, sin gráfico, alimentada por el criterio editorial de `/concepto`
y `/rencuesta` (definición + ejemplo real + puntos de aplicación) — a diferencia de `alerta`
(datos en vivo de `get_asset_levels`) y en la misma familia editorial que
`quote`/`breaking`/`encuesta` (100% manual/editorial). Es la **última plantilla de Fase B** y el
**primer consumidor real del mecanismo `FOR`** del motor (por su campo `bullets[]`). Consume el
motor genérico de Fase A (`scripts/story_render.py`) tal cual quedó, sin tocarlo.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/edu.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` +
  disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-58`), fondo
  **oscuro** con un acento **educativo** derivado de la paleta GI ya presente en el repo
  (candidatos del design doc: verde `#00DC82` / teals `#53C1AB`/`#3E91AF`; el hex exacto
  se fija en design/`apply`, no bloquea `specify` — ver Riesgo B). Tokens escalares
  `{{kicker}}`, `{{titulo_concepto}}`, `{{definicion}}`, `{{valor_a}}`, `{{operador}}`,
  `{{valor_b}}` + **un bloque `<!-- FOR:bullets -->…{{texto}}…<!-- ENDFOR:bullets -->`**.
- Nuevo `[tipo]` `edu` en `.claude/commands/story.md` PASO 0 (lista dura hoy `alerta`,
  `quote`, `breaking`, `encuesta`) + nuevo bloque "Ruta `edu`" — recolección editorial
  con el criterio de `/concepto`/`/rencuesta` (definición + ejemplo + N bullets), que
  **no llama a `get_asset_levels`** ni ejecuta búsqueda propia de evento. Reusa el flujo
  existente (preview → aprobación → render → `ruta_story.ps1 -Plantilla "edu"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `edu.html`
  (`build_html` contra el snapshot real), incluyendo los casos `kicker == ""` y
  **`bullets` en 0/1/N elementos**. Sin fixture nuevo en `tests/fixtures/stories/`, sin
  tocar `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy `alerta`, `quote`, `breaking`, `encuesta`) para incluir `edu`, sin tocar el resto
  de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica. `edu` es el **primer consumidor real** de
  `resolver_loops`, pero ese mecanismo YA existe y está testeado desde Fase A (#119); no
  se agrega ni cambia código del motor.
- `_FENCES` sigue fija en `("variacion", "vol", "chart_img", "chart_svg")`
  (`scripts/story_render.py`), ninguno de los 4 aplica a `edu`.
- El contrato de payload de `alerta`, `quote`, `breaking`, `encuesta` — sin cambios.
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin cambios.
- Fences `<!-- IF:kicker -->` — el motor solo resuelve fences top-level para la tupla
  fija `_FENCES`; `kicker` se resuelve por CSS `:empty`, no por fence (mismo criterio que
  `quote`/`breaking`/`encuesta`).
- Plantillas de Fase C con listas (`flash`, `calendario`, `semanal`, `earnings`) — sus
  propios Changes (convención "1 plantilla = 1 Change").
- El hex exacto del acento educativo — decisión de design/`apply` (autoría del CSS
  real), no bloqueante para `specify` (mismo criterio que Riesgo B de `encuesta`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo
  campo-por-campo dedicada a `edu` en este Change (mismo criterio que
  `breaking`/`encuesta`); el contrato de campos vive en el design doc (fila 07) y en este
  `spec.md`.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin cambios
  a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/edu.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, footer estándar) con paleta **oscura** y un acento **educativo**. Cuerpo:
chip `{{kicker}}` (etiqueta opcional, ej. "CONCEPTO DE LA SEMANA" o tema libre) +
`{{titulo_concepto}}` (título destacado, tipografía Syne, núcleo obligatorio) +
`{{definicion}}` (párrafo en voz novata, núcleo obligatorio) + bloque `ejemplo`
comparativo con tokens escalares `{{valor_a}} {{operador}} {{valor_b}}` (núcleo
obligatorio) + lista `bullets` renderizada con **`<!-- FOR:bullets -->…{{texto}}…<!-- ENDFOR:bullets -->`**.
Sin gráfico. Mapea al punto 1 de la hipótesis.

### R2 — Contrato de payload `story_edu`
```json
{
  "plantilla": "edu",
  "kicker": "CONCEPTO DE LA SEMANA",
  "titulo_concepto": "Cruce de medias móviles",
  "definicion": "Cuando una media rápida cruza a una lenta, señala un posible cambio de tendencia.",
  "ejemplo": { "valor_a": "Media 50", "operador": "cruza sobre", "valor_b": "Media 200" },
  "bullets": [
    { "texto": "Cruce al alza (media rápida sobre lenta) → sesgo comprador" },
    { "texto": "Cruce a la baja → sesgo vendedor" },
    { "texto": "Confírmalo con el precio, no operes solo por el cruce" }
  ]
}
```
- `plantilla`, `kicker`, `titulo_concepto`, `definicion`, `ejemplo`, `bullets` son las
  únicas claves del payload (sin `chart_png`, sin dato del motor).
- `titulo_concepto`, `definicion` y `ejemplo` (con sus tres sub-campos `valor_a`,
  `operador`, `valor_b` no vacíos) son siempre no vacíos — núcleo mínimo del concepto.
- `kicker` es un token **siempre presente** en el payload (nunca ausente/`None`) que
  admite string vacío `""` — es el único campo opcional escalar del contrato (mismo patrón
  exacto que `autor_sub` en `quote`, `kicker_tema` en `breaking`, `kicker`/`nota_cierre`
  en `encuesta`).
- **`bullets` es un array de objetos** `{"texto": "…"}` — no strings sueltos.
  `resolver_loops` resuelve `{{texto}}` por objeto en cada repetición (mismo criterio que
  el fixture `filas: [{"nombre": …}]` de Fase A). `bullets` puede ser `[]` (colapsa
  nativamente por el FOR, ver R4).
- `ejemplo` se aplana a tokens escalares `valor_a`/`operador`/`valor_b` en el contexto que
  consume el motor (el motor resuelve `{{clave}}` planas, no accede a `ejemplo.valor_a`);
  el comando (R7) construye el contexto con esas tres claves top-level derivadas del
  objeto `ejemplo`.
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A se dispara para `edu`.
- El contenido es texto editorial educativo (mismo criterio que `/concepto`/`/rencuesta`)
  — no lleva formateo `digits` de `config/activos.json` ni ningún dato en vivo del motor.

### R3 — Bloque `FOR:bullets` correcto; sin fences `IF` en `edu.html`
`edu.html` contiene exactamente **un** bloque `<!-- FOR:bullets -->…<!-- ENDFOR:bullets -->`
y **ningún** fence `<!-- IF:x -->`. El contenido interno del bloque referencia el campo
`{{texto}}` de cada objeto de `bullets`. Justificación (confirmada en código,
`scripts/story_render.py`): los fences top-level de `_resolver_fences` solo evalúan la
tupla fija `_FENCES` (los 4 nombres de Alerta); el token por-clave dentro de un `FOR`
(`{{texto}}`) sí se resuelve por iteración. Por tanto `kicker` NO puede condicionarse vía
fence sin tocar el motor (se resuelve vía CSS `:empty`, R5), y `bullets` SÍ usa el
mecanismo `FOR` nativo. Es el primer snapshot real que ejercita `FOR` (mismo mecanismo
validado en `test_resolver_loops_*` de Fase A).

### R4 — Colapso del bloque `FOR:bullets` con array vacío
Cuando `bullets == []`, `resolver_loops` sustituye todo el bloque
`<!-- FOR:bullets -->…<!-- ENDFOR:bullets -->` por cadena vacía (0 iteraciones, incluidas
las marcas). El **header/contenedor visual de la lista** (ej. un rótulo estático "CÓMO SE
USA" o el `<ul>` contenedor si debe persistir) va **fuera** de las marcas FOR/ENDFOR para
no desaparecer con la lista (regla R4/CB del motor, Fase A). Con `bullets` de 1..N
elementos, el bloque se repite 1..N veces, cada una con su `{{texto}}` resuelto.

### R5 — Colapso visual de `kicker` vacío (CSS, no motor)
Cuando `kicker == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano, no
hay error de guardia. El contenedor HTML del token (ej.
`<span class="edu-kicker">{{kicker}}</span>`) usa la regla CSS `:empty { display: none; }`
sobre el contenedor, de forma que con el campo vacío el contenedor colapsa (`display:
none`, no solo el texto) y el layout se reacomoda sin hueco. Mismo patrón exacto validado
en `quote` R4 (`.quote-cargo:empty`), `breaking` R4 (`.breaking-kicker:empty`) y
`encuesta` R4.

### R6 — Layout del bloque `ejemplo` comparativo
`valor_a`/`operador`/`valor_b` se presentan como un bloque comparativo legible (ej.
`Media 50` — `cruza sobre` — `Media 200`), con rótulos/separadores estáticos del snapshot
(texto fijo, no token) — sin flecha de variación, sin color condicional por dirección, sin
fila de soporte/resistencia/vol (mismo criterio de distinción de un dato de mercado en
vivo que R5 de `breaking`/`encuesta`). Los tres son tokens escalares incondicionales.

### R7 — Recolección editorial en `story.md` sin datos de mercado
`.claude/commands/story.md` PASO 0 agrega `edu` a la lista de `[tipo]` soportados (junto a
`alerta`, `quote`, `breaking`, `encuesta`). Nuevo bloque "Ruta `edu`":
1. Pregunta el título del concepto, la definición (voz novata), el ejemplo comparativo
   (valor A / operador / valor B) y los bullets de aplicación, con el criterio editorial
   de `/concepto`/`/rencuesta` (definición + ejemplo real + puntos de aplicación):
   ```
   ¿Nombre del concepto? (ej. "Cruce de medias móviles")
   ¿Definición en una o dos líneas (voz novata)?
   Ejemplo comparativo — ¿valor A? ¿operador/relación? ¿valor B?
   ¿Bullets de aplicación? (uno por línea; 2 a 4 recomendados)
   ¿Kicker/tema del chip? (ej. "CONCEPTO DE LA SEMANA" — Intro para omitir)
   ```
2. **`edu` no llama a `get_asset_levels`** ni a ninguna tool de mercado
   (`obtener_calendario_macro`, `get_chart_objects`, `get_symbol_spec`), y **no ejecuta su
   propia búsqueda de evento** (no invoca WebSearch) — es una pieza 100% editorial
   educativa, mismo criterio que `quote`/`breaking`/`encuesta`, heredado del contrato de
   `/concepto`/`/rencuesta`.
3. Si el director ya corrió `/concepto` o `/rencuesta` en la misma sesión, el bloque
   ofrece reutilizar el concepto/definición/ejemplo ya redactados ahí como base editorial
   (atajo opcional, no obligatorio — mismo criterio que R7.3 de `encuesta`).
4. Construye el contexto con `kicker` **siempre presente** (si el director no lo da, `""`)
   y con `bullets` como array de objetos `[{"texto": "..."}]` (una entrada por bullet
   dictado); si el director no dicta ninguno, `bullets: []` (la lista colapsa, R4).
5. Aplana `ejemplo` a las tres claves escalares `valor_a`/`operador`/`valor_b` en el
   contexto que consume el motor.

### R8 — Guardado bajo `_general`
El bloque "Ruta `edu`" guarda la Story bajo `-Activo "_general"` (`edu` es una pieza
educativa sin activo protagonista único, mismo criterio que `quote`), pasando
`-Plantilla "edu"` a `ruta_story.ps1`. La `[Hora]` sale del reloj de Chile (regla
canónica).

### R9 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), los límites recomendados:
- `kicker` ≤ 30 caracteres (chip corto, una sola línea, mismo límite que `kicker_tema` de
  `breaking`/`encuesta`).
- `titulo_concepto` ≤ 45 caracteres (título destacado de una línea).
- `definicion` ≤ 160 caracteres (párrafo corto en voz novata).
- `valor_a`/`operador`/`valor_b` ≤ 24 caracteres cada uno (bloque comparativo compacto).
- cada `bullet` (`texto`) ≤ 70 caracteres; se recomiendan 2 a 4 bullets.
El comando ajusta la redacción antes del preview si algún campo excede su límite; el motor
no valida longitud (mismo criterio que Alerta/`quote`/`breaking`/`encuesta`).

### R10 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de otras plantillas:
1. Test de mapeo con `kicker` no vacío y `bullets` de N elementos: `build_html` sobre
   `edu.html` con el payload de R2 produce HTML sin placeholders sin resolver, con
   `kicker`, `titulo_concepto`, `definicion`, `valor_a`, `operador`, `valor_b` y el
   `texto` de cada bullet correctamente inyectados.
2. Test de mapeo con `kicker == ""`: mismo `build_html`, el HTML resultante no contiene
   ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía).
3. Test del loop `bullets` en **0/1/N** elementos:
   - `bullets: []` → el HTML no contiene marcas `FOR:bullets`/`ENDFOR:bullets` ni
     `{{texto}}` huérfano, y el bloque desaparece limpio.
   - `bullets` con 1 elemento → el `texto` aparece exactamente una vez.
   - `bullets` con N (≥3) elementos → cada `texto` aparece y en orden.
4. Test de dimensiones del render (`skipif` sin Chromium): PNG con IHDR exactamente
   `(1920, 1080)` y tamaño > 5 KB, mismo umbral que las demás plantillas.
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `edu.html`). Sin cambios en `conftest.py`.

### R11 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza
para incluir `edu` junto a `alerta`, `quote`, `breaking`, `encuesta`, sin tocar el resto
del párrafo/sección.

## Casos borde

- **CB-1 (`kicker` ausente del payload, no `""`)**: el comando (R7) siempre construye el
  contexto con la clave `kicker` presente, aunque sea `""` — nunca la omite. Si por error
  se omitiera, el motor lanzaría `StoryRenderError` de token huérfano (mismo criterio
  fail-fast que las demás plantillas).
- **CB-2 (`bullets` ausente del payload)**: el comando siempre pasa `bullets` (aunque sea
  `[]`). Si se omitiera, `resolver_loops` lanza `StoryRenderError` ("FOR:bullets requiere
  un array en el payload") — fail-fast, no colapso silencioso.
- **CB-3 (`bullets == []`)**: el bloque FOR colapsa a cadena vacía; el header/contenedor
  externo persiste (R4). No es error.
- **CB-4 (algún campo excede el límite editorial de R9)**: el comando ajusta la redacción
  antes del preview; el motor no aborta ni trunca.
- **CB-5 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-6 (flag `ejecutivo`)**: `/story edu ejecutivo` avisa que `/story` no soporta el
  flag (mismo criterio ya vigente para las demás plantillas) y continúa generando la Story
  normal.
- **CB-7 (tipo `/story` inválido, incluyendo un `[tipo]` que no es `alerta`/`quote`/
  `breaking`/`encuesta`/`edu`)**: `.claude/commands/story.md` PASO 0 informa la lista
  actualizada de tipos disponibles y vuelve a preguntar — nunca asume un tipo por defecto.
- **CB-8 (director ya corrió `/concepto` o `/rencuesta` en la misma sesión)**: el bloque
  "Ruta `edu`" ofrece reutilizar ese concepto/definición/ejemplo como base editorial
  (R7.3); no es dependencia dura.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/edu.html` existe y contiene `width: 1920px` y `height: 1080px` (o
equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html`.

**AC2 — bloque `FOR:bullets` presente y sin fences `IF` (estructural, `rg`)**
`rg "<!-- FOR:bullets -->" templates/stories/edu.html` ≥1 match y
`rg "<!-- ENDFOR:bullets -->" templates/stories/edu.html` ≥1 match (R3); además
`rg "<!-- IF:" templates/stories/edu.html` → 0 matches.

**AC3 — mapeo de campos con `kicker` no vacío y `bullets` de N (ejecutable, `pytest`)**
DADO el payload de R2 (con `kicker` no vacío y 3 bullets),
CUANDO se ejecuta `build_html` sobre `templates/stories/edu.html`,
ENTONCES el HTML resultante contiene el texto de `kicker`, `titulo_concepto`,
`definicion`, `valor_a`, `operador`, `valor_b` y el `texto` de cada bullet correctamente
inyectados, y no contiene ningún placeholder `{{...}}` sin resolver (R2/R10).

**AC4 — colapso de `kicker` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/edu.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver, y el contenedor
de `kicker` en el CSS del snapshot declara `:empty { display: none; }`
(verificable con `rg ":empty" templates/stories/edu.html` ≥1 match) (R5/R10).

**AC5 — loop `bullets` en 0/1/N (ejecutable, `pytest`)**
DADO el payload de R2 con `bullets` en `[]`, en 1 elemento y en ≥3 elementos
respectivamente,
CUANDO se ejecuta `build_html` sobre `templates/stories/edu.html`,
ENTONCES: con `[]` el HTML no contiene `FOR:bullets`/`ENDFOR:bullets` ni `{{texto}}`; con 1
el `texto` aparece exactamente una vez; con N cada `texto` aparece y en orden (R4/R10).

**AC6 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo contra `templates/stories/edu.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que las demás plantillas).

**AC7 — sin elementos de dato de mercado en vivo (estructural, `rg`)**
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/edu.html`
→ 0 matches (confirma que `edu.html` no reutiliza el layout de tarjeta de precio de
Alerta ni sus tokens, R6).

**AC8 — `[tipo]` `edu` registrado en el comando (estructural, `rg`)**
`rg "edu" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]` soportados
del PASO 0, otro en el bloque "Ruta `edu`" (R7).

**AC9 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?30|≤ ?45|≤ ?160|≤ ?24|≤ ?70" .claude/commands/story.md` ≥1 match asociado a los
límites recomendados de `edu` (R9).

**AC10 — `story.md` documenta que `edu` no llama a datos de mercado (estructural, `rg`)**
`rg -i "no llama a .get_asset_levels.|100% editorial|sin datos de mercado|educativ"
.claude/commands/story.md` ≥1 match dentro del bloque "Ruta `edu`" (R7).

**AC11 — `CLAUDE.md` actualizado (estructural, `rg`)**
La sección "Stories GI" de `CLAUDE.md` enumera `edu` entre los `[tipo]` de `/story`
soportados (R11), distinguible por contexto de otras menciones.

**AC12 — sin regresión del motor ni de las plantillas previas (estructural, `git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html templates/stories/breaking.html templates/stories/encuesta.html
scripts/ruta_story.ps1` no muestra cambios — confirma que el motor, los snapshots
existentes y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de referencia
  del canvas GI para `edu` en 16:9. Mitigación: aprobación visual manual del director en la
  primera corrida real de `/story edu` (mismo riesgo residual heredado de Fase A y de las
  plantillas previas).
- **Riesgo B — hex exacto del acento educativo no fijado en `specify`**: el design doc solo
  da candidatos (verde `#00DC82`, teals `#53C1AB`/`#3E91AF`). El valor final se decide en
  design/`apply` durante la autoría del CSS real, no bloquea `specify` (mismo criterio que
  Riesgo B de `encuesta`). Se presenta al director en la PAUSA de design.
- **Riesgo C — límites de longitud (R9) son estimaciones editoriales**: al no existir
  golden PNG, los límites exactos pueden requerir ajuste tras la primera corrida visual;
  se documentan como guía editorial del comando, no como validación dura del motor.
- **Riesgo D — número de bullets sin límite duro**: la plantilla soporta N bullets vía
  FOR, pero un número excesivo desborda el layout 16:9. Mitigación: R9 recomienda 2 a 4
  bullets como criterio editorial; el motor no valida cantidad.

## Preguntas abiertas — resueltas

1. **Acento educativo exacto** → Riesgo B: candidatos documentados (verde/teal), hex final
   decidido en design/`apply`, presentado en la PAUSA de design.
2. **¿`kicker` es rol fijo o libre?** → R7: campo libre editorial (mismo tratamiento que
   `kicker_tema` de `breaking`), el director lo redacta o lo omite en cada corrida.
3. **Forma de `bullets`** → R2: array de objetos `[{"texto": "..."}]` (el motor resuelve
   `{{texto}}` por objeto dentro del FOR, mismo patrón que el fixture de Fase A).
4. **Header de la lista dentro o fuera del FOR** → R4: fuera de las marcas FOR/ENDFOR para
   persistir con `bullets == []`.
5. **¿`edu` se guarda con `-Activo` o `_general`?** → R8: siempre `_general` (pieza
   educativa sin activo protagonista, mismo criterio que `quote`).
6. **Aplanado de `ejemplo`** → R2/R7.5: el comando aplana `ejemplo` a `valor_a`/`operador`/
   `valor_b` escalares en el contexto que consume el motor (que resuelve claves planas).

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 07 `edu`
  (línea 65): payload `kicker, titulo_concepto, definicion, ejemplo(valor_a, operador,
  valor_b), bullets[]`, sin gráfico, fondo oscuro, fuente `/concepto`·`/rencuesta`; nota
  bullets/FOR (línea 76); plan de fases (líneas 91-92: Fase B = `quote`, `breaking`,
  `encuesta`, `edu`).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  `story_quote`, `story_breaking`, `story_encuesta`) como precedente directo de formato
  para `story_edu`.
- `.pulse/changes/archive/119-.../spec.md` — motor generalizado + mecanismo `FOR`
  (`resolver_loops`), no se reabre; molde del contrato del loop.
- `.pulse/changes/archive/121-.../spec.md` — patrón fundacional de campo opcional
  (token + `:empty`).
- `.pulse/changes/archive/123-.../spec.md` y `.../125-.../spec.md` — molde estructural
  directo de este documento (snapshot + bloque de recolección + tests de mapeo + `CLAUDE.md`).
- `scripts/story_render.py` — motor 16:9: `resolver_loops` (mecanismo FOR), `_FENCES`
  fija, `build_html`, `render_png`; **no se modifica** en este Change.
- `templates/stories/alerta.html` — referencia de esqueleto de marca (fuentes, footer).
- `templates/stories/{quote,breaking,encuesta}.html` — molde del patrón `:empty` para el
  campo opcional `kicker`.
- `tests/test_story_render.py` — suite a extender: patrón `test_quote_*`/`test_breaking_*`
  para mapeo puro, y `test_resolver_loops_vacio/uno/n` (fixture `FIXTURE_FOR_HTML`) como
  molde del test del loop `bullets`.
- `.claude/commands/story.md` — comando a extender (PASO 0 + nuevo bloque "Ruta `edu`"
  análogo a "Ruta `encuesta`").
- `.claude/commands/concepto.md`, `.claude/commands/rencuesta.md` — contrato editorial
  fuente (definición + ejemplo + puntos de aplicación).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #127 — base de este documento.
- Issue #127; precedentes cerrados #121 (quote), #123 (breaking), #125 (encuesta).
