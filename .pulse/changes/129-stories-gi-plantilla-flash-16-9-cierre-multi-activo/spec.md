# Specification: Stories GI · Fase C — plantilla Flash (cierre multi-activo) 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #129). Fuente canónica
> del contrato de `flash`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 05, línea 63; nota `filas[]`/FOR línea 76). Hereda el motor generalizado de Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo — incluido `resolver_loops` (mecanismo
> FOR) ya implementado y testeado. Hereda el patrón de campo opcional (token + CSS `:empty`)
> validado en `quote`/`breaking`/`encuesta`/`edu` y el patrón de aplanado de objeto anidado a
> escalares top-level validado en `edu` (#127). Resuelve las preguntas abiertas de
> `idea.md`/`proposal.md` como requisitos verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`flash`** (#05 del catálogo GI) al comando `/story`: una pieza de **cierre
multi-activo** (chip opcional + título + fecha + tabla de N activos con `nombre`, `tipo`, último
`valor` y `variacion` del día con dirección), fondo **oscuro**, sin gráfico. Es la **primera
plantilla de Fase C** (plantillas con listas) y el **segundo consumidor real del mecanismo `FOR`**
del motor (tras `edu`). Consume el motor genérico de Fase A (`scripts/story_render.py`) tal cual
quedó, sin tocarlo. A diferencia de las 4 plantillas de Fase B (100% editoriales), `flash`
alimenta sus filas con **datos reales del motor** (`get_asset_levels` × N activos), pero esa
recolección vive en el prompt de `/story` — el renderer sigue siendo un motor "tonto"
(payload → HTML → PNG). **No** lleva gráfico embebido (eso es Fase D).

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/flash.html` (1920×1080): esqueleto de marca GI (fuentes
  locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` + disclaimer CFD, igual
  criterio que `templates/stories/edu.html:16-59,197-220`), fondo **oscuro** con un acento
  **estructural** derivado de la paleta GI ya presente en el repo (candidato del design doc: teal
  `#3E91AF`; el hex exacto se fija en design/`apply`, no bloquea `specify` — ver Riesgo B).
  Tokens escalares top-level `{{kicker}}`, `{{titulo}}`, `{{fecha}}` + **un bloque
  `<!-- FOR:filas -->…{{nombre}}…{{tipo}}…{{valor}}…{{variacion}}…{{direccion}}…<!-- ENDFOR:filas -->`**.
- Nuevo `[tipo]` `flash` en `.claude/commands/story.md` PASO 0 (lista dura hoy `alerta`, `quote`,
  `breaking`, `encuesta`, `edu`) + nuevo bloque "Ruta `flash`" — recolección de los valores/
  variaciones reales delegando en `get_asset_levels` × N activos (criterio de `/apertura` PASO 4 /
  `/actualizacion`), con fallback manual (patrón `apertura.md` PASO 4A). Reusa el flujo existente
  (preview → aprobación → render → `ruta_story.ps1 -Plantilla "flash"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `flash.html` (`build_html` contra el
  snapshot real), incluyendo el loop `filas` en **0/1/N** elementos. Sin fixture nuevo en
  `tests/fixtures/stories/`, sin tocar `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados (hoy `alerta`,
  `quote`, `breaking`, `encuesta`, `edu`) para incluir `flash`, sin tocar el resto de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_expandir_elemento`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica. `flash` es el **segundo consumidor real** de `resolver_loops`,
  pero ese mecanismo YA existe y está testeado desde Fase A (#119) y en uso desde `edu` (#127); no
  se agrega ni cambia código del motor.
- `_FENCES` sigue fija en `("variacion", "vol", "chart_img", "chart_svg")`; ninguno aplica a
  `flash`. (El nombre de token por-fila `{{variacion}}` NO colisiona con el fence top-level
  `variacion`: el fence solo gobierna bloques `<!-- IF:variacion -->` top-level, que `flash.html`
  no contiene; el token `{{variacion}}` se resuelve dentro del FOR por `_expandir_elemento`.)
- **Gráfico embebido / slot de chart** — `flash` no lleva gráfico (design doc fila 05: "no (tabla
  5)"). Eso es Fase D (`market`, `idea`, `macro`).
- El contrato de payload de `alerta`, `quote`, `breaking`, `encuesta`, `edu` — sin cambios.
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin cambios.
- El hex exacto del acento estructural — decisión de design/`apply` (autoría del CSS real), no
  bloqueante para `specify` (mismo criterio que Riesgo B de `edu`/`encuesta`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo campo-por-campo
  dedicada a `flash` en este Change (mismo criterio que `breaking`/`encuesta`/`edu`); el contrato
  de campos vive en el design doc (fila 05) y en este `spec.md`.
- Las otras 3 plantillas de Fase C (`calendario`, `semanal`, `earnings`) — sus propios Changes
  (convención "1 plantilla = 1 Change").
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin cambios.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/flash.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `edu.html` (fuentes locales,
footer estándar) con paleta **oscura** y un acento **estructural** (teal candidato). Cuerpo:
chip `{{kicker}}` (etiqueta opcional, ej. "CIERRE DE MERCADO") + `{{titulo}}` (título destacado,
tipografía Syne, núcleo obligatorio) + `{{fecha}}` (fecha/hora del cierre, núcleo obligatorio) +
una **tabla de activos** cuyo encabezado (rótulos de columna "ACTIVO / TIPO / ÚLTIMO / VAR%") y
contenedor `<table>`/`<tbody>` van **fuera** de las marcas FOR/ENDFOR, y cuyas filas de datos se
generan con el bloque `<!-- FOR:filas -->…<!-- ENDFOR:filas -->`. Sin gráfico. Mapea al punto 1 de
la hipótesis.

### R2 — Contrato de payload `story_flash`
```json
{
  "plantilla": "flash",
  "kicker": "CIERRE DE MERCADO",
  "titulo": "Así cerró el mercado hoy",
  "fecha": "16 JUL 2026 · 17:30",
  "filas": [
    { "nombre": "USD/CLP", "tipo": "Divisa",  "valor": "889,60",   "variacion": "+0,42%", "direccion": "alcista" },
    { "nombre": "Oro",     "tipo": "Metal",   "valor": "2.318,40", "variacion": "-1,86%", "direccion": "bajista" },
    { "nombre": "WTI",     "tipo": "Energía", "valor": "78,320",   "variacion": "0,00%",  "direccion": "lateral" }
  ]
}
```
- `plantilla`, `kicker`, `titulo`, `fecha`, `filas` son las únicas claves del payload (sin
  `chart_png`, sin dato del motor a nivel top-level).
- `titulo` y `fecha` son siempre no vacíos — núcleo mínimo del cierre.
- `kicker` es un token **siempre presente** en el payload (nunca ausente/`None`) que admite string
  vacío `""` — es el único campo opcional escalar del contrato (mismo patrón exacto que `kicker` en
  `encuesta`/`edu`, `kicker_tema` en `breaking`, `autor_sub` en `quote`).
- **`filas` es un array de objetos** con **claves escalares** `nombre`, `tipo`, `valor`,
  `variacion`, `direccion` — no objetos anidados. `resolver_loops` resuelve `{{nombre}}`/`{{tipo}}`/
  `{{valor}}`/`{{variacion}}`/`{{direccion}}` por objeto en cada repetición (mismo criterio que el
  fixture `filas: [{"nombre": …}]` de Fase A y el `bullets: [{"texto": …}]` de `edu`). `filas` puede
  ser `[]` (colapsa nativamente por el FOR, ver R4).
- **`variacion` de cada fila viene aplanada a un escalar** (el pct ya formateado con signo y unidad,
  ej. `"+0,42%"`), **no** un objeto `{pct, direccion}`. La **dirección** viaja aparte en la clave
  escalar `direccion` (`alcista`/`bajista`/`lateral`). Justificación: los helpers de derivación del
  motor (flecha, color) solo corren sobre claves **top-level** del payload (`build_context`), no
  dentro del FOR (`_expandir_elemento` solo sustituye escalares y fences `IF` por objeto). Mismo
  criterio con que `edu` (#127) aplanó `ejemplo` a `valor_a`/`operador`/`valor_b`. La flecha ▲/▼/→
  y el color verde/rojo/neutro salen del **CSS** a partir de `{{direccion}}` (R6), no del motor.
- Sin campo `impacto`/`sesgo`/`chart_png` a nivel top-level; el token `direccion` vive **dentro**
  de cada fila, no top-level, por lo que **ningún** helper de derivación de Fase A se dispara para
  `flash` (`_aplicar_helper_slug_color` mira `payload.get("sesgo")`/`variacion` top-level, ausentes).
- El `valor` de cada fila respeta los `digits` del activo (`config/activos.json`, regla MT5 del
  repo) con coma decimal y punto de miles — pero ese formateo lo hace el **comando** (R7) al
  recolectar; el motor no formatea.

### R3 — Bloque `FOR:filas` correcto; sin fences `IF` en `flash.html`
`flash.html` contiene exactamente **un** bloque `<!-- FOR:filas -->…<!-- ENDFOR:filas -->` y
**ningún** fence `<!-- IF:x -->`. El contenido interno del bloque referencia los campos
`{{nombre}}`, `{{tipo}}`, `{{valor}}`, `{{variacion}}`, `{{direccion}}` de cada objeto de `filas`.
Justificación (confirmada en `scripts/story_render.py`): los fences top-level de
`_resolver_fences` solo evalúan la tupla fija `_FENCES` (4 nombres de Alerta); los tokens
por-fila dentro de un `FOR` sí se resuelven por iteración. Por tanto `kicker` NO se condiciona vía
fence sin tocar el motor (se resuelve vía CSS `:empty`, R5), y `filas` SÍ usa el mecanismo `FOR`
nativo (mismo mecanismo validado en `test_resolver_loops_*` de Fase A y `test_edu_bullets_*` de
#127).

### R4 — Colapso del bloque `FOR:filas` con array vacío; encabezado fuera del FOR
Cuando `filas == []`, `resolver_loops` sustituye todo el bloque
`<!-- FOR:filas -->…<!-- ENDFOR:filas -->` por cadena vacía (0 iteraciones, incluidas las marcas).
El **encabezado de la tabla** (rótulos de columna) y el contenedor `<table>`/`<tbody>` van **fuera**
de las marcas FOR/ENDFOR para no desaparecer con las filas (regla R4/CB del motor, Fase A). Con
`filas` de 1..N elementos, el bloque se repite 1..N veces, cada una con sus tokens resueltos y en
el orden del array.

### R5 — Colapso visual de `kicker` vacío (CSS, no motor)
Cuando `kicker == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano, no hay error
de guardia. El contenedor HTML del token (ej. `<span class="flash-kicker">{{kicker}}</span>`) usa
la regla CSS `:empty { display: none; }` de forma que con el campo vacío el contenedor colapsa
(`display: none`, no solo el texto) y el layout se reacomoda sin hueco. Mismo patrón exacto
validado en `quote` (`.quote-cargo:empty`), `breaking` (`.breaking-kicker:empty`), `encuesta` y
`edu` (`.edu-kicker:empty`).

### R6 — Color y flecha de variación por CSS a partir de `direccion`
La celda de variación de cada fila lleva una clase CSS derivada del token escalar `{{direccion}}`
de esa fila (ej. `class="flash-var flash-var--{{direccion}}"` → tras la sustitución
`flash-var--alcista`/`flash-var--bajista`/`flash-var--lateral`). El snapshot define reglas CSS
estáticas para las tres clases: color verde `#00DC82` + flecha `▲` para `alcista`, rojo `#E84040`
+ flecha `▼` para `bajista`, neutro (gris) + guion/flecha lateral para `lateral`. La flecha se
inyecta con `::before { content: … }` en CSS (texto fijo del snapshot, no token), sin helper del
motor. Un valor de `direccion` fuera de los tres esperados simplemente no matchea ninguna regla
de color/flecha (degradación limpia, sin error) — el comando (R7) siempre normaliza a uno de los
tres.

### R7 — Recolección en `story.md` con datos del motor (fallback manual)
`.claude/commands/story.md` PASO 0 agrega `flash` a la lista de `[tipo]` soportados (junto a
`alerta`, `quote`, `breaking`, `encuesta`, `edu`). Nuevo bloque "Ruta `flash`":
1. Pregunta la **lista de activos** del cierre (2 a 6 recomendados; el usuario los nombra o
   confirma la rotación del día), el `titulo` y opcionalmente el `kicker`.
2. Para **cada activo**, obtiene el último `valor` y la `variacion` del día vía
   `mcp__market-data__get_asset_levels` (mismo criterio que `/apertura` PASO 4 / `/actualizacion`),
   con **fallback manual** si MT5 devuelve `{"error": …}` (patrón `apertura.md` PASO 4A) — pide el
   valor y la variación a mano. Formatea `valor` según los `digits` de ese activo
   (`config/activos.json`, coma decimal y punto de miles); formatea `variacion` como pct con signo
   y `%`. Deriva `direccion` (`alcista` si var > 0, `bajista` si var < 0, `lateral` si ≈ 0).
3. **`flash` no ejecuta búsqueda editorial de evento** (no invoca WebSearch): es un tablero de
   cierre, la narrativa la da la propia tabla (dirección explícita por fila — regla de oro).
4. Construye el payload con `kicker` **siempre presente** (si el director no lo da, `""`), `titulo`
   y `fecha` no vacíos, y `filas` como array de objetos escalares `[{"nombre","tipo","valor",
   "variacion","direccion"}]`; si el director no da ningún activo, el comando insiste (una tabla
   vacía no aporta) — `filas: []` es un caso soportado por el motor (R4) pero no un flujo esperado.
5. `fecha` sale del reloj de Chile (regla canónica de `CLAUDE.md`, nunca `WebSearch` para la hora).

### R8 — Guardado con o sin `-Activo`
El bloque "Ruta `flash`" guarda la Story bajo `-Plantilla "flash"`. Como `flash` es una pieza
multi-activo sin un activo protagonista único, se guarda bajo `-Activo "_general"` (mismo criterio
que `quote`/`edu`), sin preguntar por activo. La `[Hora]` sale del reloj de Chile.

### R9 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como validación del
motor), los límites recomendados:
- `kicker` ≤ 30 caracteres (chip corto, una línea, mismo límite que las demás plantillas).
- `titulo` ≤ 45 caracteres (título destacado de una línea).
- `fecha` ≤ 40 caracteres (fecha + hora del cierre).
- por fila: `nombre` ≤ 16 caracteres, `tipo` ≤ 14 caracteres, `valor` ≤ 14 caracteres,
  `variacion` ≤ 10 caracteres (celdas compactas de la tabla).
- 2 a 6 filas recomendadas (el layout 16:9 acota; el motor no valida cantidad).
El comando ajusta la redacción antes del preview si algún campo excede su límite; el motor no
valida longitud (mismo criterio que Alerta/`quote`/`breaking`/`encuesta`/`edu`).

### R10 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de otras plantillas:
1. Test de mapeo con `kicker` no vacío y `filas` de N elementos: `build_html` sobre `flash.html`
   con el payload de R2 produce HTML sin placeholders sin resolver, con `kicker`, `titulo`,
   `fecha` y — por cada fila — `nombre`, `tipo`, `valor`, `variacion` correctamente inyectados, y
   la clase `flash-var--<direccion>` presente por fila.
2. Test de mapeo con `kicker == ""`: mismo `build_html`, el HTML resultante no contiene ningún
   `{{token}}` huérfano.
3. Test del loop `filas` en **0/1/N** elementos:
   - `filas: []` → el HTML no contiene marcas `FOR:filas`/`ENDFOR:filas` ni `{{nombre}}` huérfano,
     y el bloque desaparece limpio (el encabezado de la tabla, fuera del FOR, persiste).
   - `filas` con 1 elemento → el `nombre` de esa fila aparece exactamente una vez.
   - `filas` con N (≥3) elementos → cada `nombre` aparece y en orden.
4. Test de dimensiones del render (`skipif` sin Chromium): PNG con IHDR exactamente `(1920, 1080)`
   y tamaño > 5 KB, mismo umbral que las demás plantillas.
Sin fixture nuevo en `tests/fixtures/stories/`; sin cambios en `conftest.py`.

### R11 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza para
incluir `flash` junto a `alerta`, `quote`, `breaking`, `encuesta`, `edu`, sin tocar el resto del
párrafo/sección.

## Casos borde

- **CB-1 (`kicker` ausente del payload, no `""`)**: el comando (R7) siempre construye el payload
  con la clave `kicker` presente, aunque sea `""`. Si por error se omitiera, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que las demás plantillas).
- **CB-2 (`filas` ausente del payload)**: el comando siempre pasa `filas` (aunque sea `[]`). Si se
  omitiera, `resolver_loops` lanza `StoryRenderError` ("FOR:filas requiere un array en el payload")
  — fail-fast, no colapso silencioso.
- **CB-3 (`filas == []`)**: el bloque FOR colapsa a cadena vacía; el encabezado/contenedor externo
  persiste (R4). No es error del motor; el comando (R7.4) desalienta el flujo (tabla vacía no
  aporta).
- **CB-4 (MT5 no disponible para un activo)**: fallback manual de valor/variación para ese activo,
  mismo patrón `apertura.md` PASO 4A (R7.2). No aborta toda la tabla.
- **CB-5 (`direccion` fuera de `alcista`/`bajista`/`lateral`)**: la celda no matchea ninguna regla
  de color/flecha (degradación limpia, sin error); el comando siempre normaliza a uno de los tres
  (R6/R7.2).
- **CB-6 (algún campo excede el límite editorial de R9)**: el comando ajusta la redacción antes del
  preview; el motor no aborta ni trunca.
- **CB-7 (director rechaza el preview)**: no se renderiza ni guarda nada en `data/stories/` (mismo
  criterio CB heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-8 (flag `ejecutivo`)**: `/story flash ejecutivo` avisa que `/story` no soporta el flag
  (mismo criterio ya vigente) y continúa generando la Story normal.
- **CB-9 (tipo `/story` inválido, incluyendo un `[tipo]` que no es
  `alerta`/`quote`/`breaking`/`encuesta`/`edu`/`flash`)**: `.claude/commands/story.md` PASO 0
  informa la lista actualizada de tipos disponibles y vuelve a preguntar — nunca asume un tipo por
  defecto.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/flash.html` existe y contiene `width: 1920px` y `height: 1080px` (o
equivalente) en su CSS — mismo patrón que `templates/stories/edu.html`.

**AC2 — bloque `FOR:filas` presente y sin fences `IF` (estructural, `rg`)**
`rg "<!-- FOR:filas -->" templates/stories/flash.html` ≥1 match y
`rg "<!-- ENDFOR:filas -->" templates/stories/flash.html` ≥1 match (R3); además
`rg "<!-- IF:" templates/stories/flash.html` → 0 matches.

**AC3 — mapeo de campos con `kicker` no vacío y `filas` de N (ejecutable, `pytest`)**
DADO el payload de R2 (con `kicker` no vacío y ≥3 filas), CUANDO se ejecuta `build_html` sobre
`templates/stories/flash.html`, ENTONCES el HTML resultante contiene el texto de `kicker`,
`titulo`, `fecha` y — por cada fila — `nombre`, `tipo`, `valor`, `variacion`, más la clase
`flash-var--<direccion>` de cada fila; y no contiene ningún placeholder `{{...}}` sin resolver
(R2/R10).

**AC4 — colapso de `kicker` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker": ""`, CUANDO se ejecuta `build_html` sobre
`templates/stories/flash.html`, ENTONCES el HTML resultante no contiene ningún `{{token}}` sin
resolver, y el contenedor de `kicker` en el CSS del snapshot declara `:empty { display: none; }`
(verificable con `rg ":empty" templates/stories/flash.html` ≥1 match) (R5/R10).

**AC5 — loop `filas` en 0/1/N (ejecutable, `pytest`)**
DADO el payload de R2 con `filas` en `[]`, en 1 elemento y en ≥3 elementos respectivamente, CUANDO
se ejecuta `build_html` sobre `templates/stories/flash.html`, ENTONCES: con `[]` el HTML no
contiene `FOR:filas`/`ENDFOR:filas` ni `{{nombre}}`; con 1 el `nombre` de esa fila aparece
exactamente una vez; con N cada `nombre` aparece y en orden (R4/R10).

**AC6 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3, CUANDO se ejecuta el render completo contra `templates/stories/flash.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo umbral que
las demás plantillas).

**AC7 — sin gráfico ni tokens de dato de mercado top-level (estructural, `rg`)**
`rg "chart|<img|<svg|soporte|resistencia|precio_actual" templates/stories/flash.html` → 0 matches
(confirma que `flash.html` no reutiliza el slot de gráfico ni la tarjeta de precio de Alerta, R1).

**AC8 — `[tipo]` `flash` registrado en el comando (estructural, `rg`)**
`rg "flash" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]` soportados del
PASO 0, otro en el bloque "Ruta `flash`" (R7).

**AC9 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?30|≤ ?45|≤ ?16|≤ ?14|≤ ?10" .claude/commands/story.md` ≥1 match asociado a los límites
recomendados de `flash` (R9).

**AC10 — `story.md` documenta la recolección de datos de `flash` (estructural, `rg`)**
`rg -i "get_asset_levels|cierre|multi-?activo|fallback" .claude/commands/story.md` ≥1 match dentro
del bloque "Ruta `flash`" (R7).

**AC11 — `CLAUDE.md` actualizado (estructural, `rg`)**
La sección "Stories GI" de `CLAUDE.md` enumera `flash` entre los `[tipo]` de `/story` soportados
(R11), distinguible por contexto de otras menciones.

**AC12 — sin regresión del motor ni de las plantillas previas (estructural, `git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html templates/stories/breaking.html templates/stories/encuesta.html
templates/stories/edu.html scripts/ruta_story.ps1` no muestra cambios — confirma que el motor, los
snapshots existentes y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de referencia del
  canvas GI para `flash` en 16:9. Mitigación: aprobación visual manual del director en la primera
  corrida real de `/story flash` (mismo riesgo residual heredado de Fase A y de las plantillas
  previas).
- **Riesgo B — hex exacto del acento estructural no fijado en `specify`**: el design doc solo da
  candidatos de paleta (teals `#3E91AF`/`#53C1AB`, azul `#1E3A5F`). El valor final se decide en
  design/`apply` durante la autoría del CSS real, no bloquea `specify` (mismo criterio que Riesgo B
  de `edu`). Se presenta al director en la PAUSA de design. **Restricción de diseño**: el verde
  `#00DC82` y el rojo `#E84040` quedan reservados a la **semántica de dirección** de las filas (R6),
  así que el acento estructural NO puede ser ninguno de esos dos (evitar dilución semántica).
- **Riesgo C — límites de longitud (R9) son estimaciones editoriales**: al no existir golden PNG,
  los límites exactos pueden requerir ajuste tras la primera corrida visual; se documentan como
  guía editorial del comando, no como validación dura del motor.
- **Riesgo D — número de filas sin límite duro**: la plantilla soporta N filas vía FOR, pero un
  número excesivo desborda el layout 16:9. Mitigación: R9 recomienda 2 a 6 filas como criterio
  editorial; el motor no valida cantidad.

## Preguntas abiertas — resueltas

1. **Forma de cada fila / `variacion`** → R2: array de objetos con claves **escalares**;
   `variacion` aplanada a un escalar (pct formateado) + `direccion` escalar aparte. El motor
   resuelve `{{campo}}` por objeto dentro del FOR; flecha/color por CSS a partir de `{{direccion}}`
   (R6), sin helper del motor (mismo patrón de aplanado que `edu` con `ejemplo`).
2. **Acento estructural exacto** → Riesgo B: candidatos documentados (teal), hex final decidido en
   design/`apply`, presentado en la PAUSA de design; verde/rojo reservados a la semántica de fila.
3. **Campos escalares del encabezado** → R2: `kicker` (opcional), `titulo` y `fecha` (obligatorios).
4. **Header de la tabla dentro o fuera del FOR** → R4: fuera de las marcas FOR/ENDFOR para
   persistir con `filas == []`.
5. **¿`flash` se guarda con `-Activo` o `_general`?** → R8: siempre `_general` (pieza multi-activo
   sin activo protagonista único, mismo criterio que `quote`/`edu`).
6. **Cantidad de activos** → R9/Riesgo D: 2 a 6 recomendados (criterio editorial), el motor no
   valida cantidad.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 05 `flash`
  (línea 63): payload `filas[]`: `nombre, tipo, valor, variacion(pct+direccion)`, sin gráfico,
  fondo oscuro, fuente `get_asset_levels` × N activos; nota `filas[]`/FOR (línea 76); plan de
  fases (líneas 91-93: Fase C = `flash`, `calendario`, `semanal`, `earnings`).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`, `story_quote`,
  `story_breaking`, `story_encuesta`, `story_edu`) como precedente directo de formato para
  `story_flash`.
- `.pulse/changes/archive/119-.../spec.md` — motor generalizado + mecanismo `FOR`
  (`resolver_loops`), no se reabre; molde del contrato del loop.
- `.pulse/changes/archive/127-.../{spec,design}.md` — molde estructural directo (edu: snapshot con
  FOR real + bloque de recolección + tests de mapeo con loop 0/1/N + patrón de aplanado + `CLAUDE.md`).
- `.pulse/changes/archive/{121,123,125}-.../spec.md` — patrón de campo opcional (token + `:empty`).
- `scripts/story_render.py` — motor 16:9: `resolver_loops`/`_expandir_elemento` (mecanismo FOR),
  `build_context` (helpers solo top-level), `_FENCES` fija, `build_html`, `render_png`; **no se
  modifica** en este Change.
- `templates/stories/edu.html` — referencia de esqueleto de marca (fuentes, footer) + patrón FOR real.
- `templates/stories/{quote,breaking,encuesta,edu}.html` — molde del patrón `:empty` para el campo
  opcional `kicker`.
- `tests/test_story_render.py` — suite a extender: patrón `test_edu_*` (mapeo puro + loop
  `bullets` 0/1/N) como molde del test del loop `filas`.
- `.claude/commands/story.md` — comando a extender (PASO 0 + nuevo bloque "Ruta `flash`" análogo a
  "Ruta `edu`").
- `.claude/commands/apertura.md`, `.claude/commands/actualizacion.md` — criterio de recolección de
  valores/variaciones vía `get_asset_levels` + fallback manual PASO 4A.
- `config/activos.json` — `digits` para el formateo de `valor` por activo.
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #129 — base de este documento.
- Issue #129; precedentes cerrados #121 (quote), #123 (breaking), #125 (encuesta), #127 (edu).
