# Specification: Stories GI · Fase A — motor de render 16:9 + migrar plantilla Alerta

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #119). Fuente
> canónica del alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (PR #118, diseño aprobado). Este documento **no reabre** el contrato de datos `story_alerta`
> heredado del Change #109 (`.pulse/specs/stories-gi/spec.md`, R1-R10/CB-1..CB-8/AC1-AC9) — lo
> hereda y solo migra su **layout y viewport**. Resuelve las 7 preguntas abiertas de `idea.md`/
> `proposal.md` como requisitos verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Generalizar `scripts/story_render.py` (issue #109) para que deje de estar atado a un único
formato (9:16) y a una única plantilla (Alerta): viewport único **1920×1080**, tokens
escalares derivados dinámicamente del payload (no una lista fija por plantilla), un mecanismo
nuevo de repetición `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` y un catálogo cerrado de
helpers de derivación reutilizables — usando la migración de `templates/stories/alerta.html`
a un layout horizontal 16:9 como caso de prueba end-to-end de la generalización. Este Change
es el cimiento arquitectónico del que dependen las Fases B/C/D (11 plantillas restantes, cada
una su propio Change).

## Alcance IN/OUT

### IN
- Cambiar `render_png` (`scripts/story_render.py:168-211`, viewport hardcodeado en la línea 206)
  de `1080×1920` a **`1920×1080`** como único default — se elimina el 9:16, sin modo dual ni
  parámetro de tamaño.
- Reemplazar `_TOKENS_ESCALARES` (tupla fija, `scripts/story_render.py:33-46`) por un recorrido
  dinámico de las claves escalares top-level del payload en `build_context`.
- Nueva función `resolver_loops(html, payload)`: expande bloques
  `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` repitiendo su contenido interno una vez por objeto
  de `payload[clave]` (array), resolviendo los tokens propios de cada objeto en su iteración.
  Un solo nivel de anidamiento (ver R4 y "Preguntas abiertas — resueltas").
- Reordenar `build_html` (`scripts/story_render.py:153-165`) al orden canónico: **loops →
  fences → tokens → guardia** (hoy es fences → tokens → guardia).
- Conservar `_resolver_fences`/`_fence_presente`/`_validar_sin_huerfanos` en su lógica; solo
  cambia su posición relativa a `resolver_loops`.
- Fijar ya en esta Fase el catálogo cerrado de 4 helpers de derivación reutilizables
  (dirección→flecha, dirección/sesgo→color, impacto→badge, chart→URI), aunque hoy solo los
  primeros dos y el último tengan consumidor real en Alerta (ver R5).
- Migrar `templates/stories/alerta.html` (hoy 1080×1920, `templates/stories/alerta.html:48-65`)
  a un rediseño horizontal 1920×1080 que conserve el sistema visual GI (colores, tipografías,
  footer) y **los mismos nombres de tokens/fences** del contrato `story_alerta` vigente.
- Sincronizar 3 documentos que mencionan literalmente `1080×1920` o `9:16`: `CLAUDE.md:249` y
  `CLAUDE.md:322` (sección "Stories GI" y tabla de comandos), `.claude/commands/story.md:1`, y
  `docs/design/stories-gi/plantillas-stories-gi.md:32` (intro del catálogo de plantillas).
- Adaptar `tests/test_story_render.py` in-place: tokens dinámicos, `resolver_loops` (array
  vacío/1/N), assert de dimensiones `(1080, 1920)` → `(1920, 1080)`.

### OUT (explícitamente diferido — no se reabre)
- El contrato de payload específico de las 11 plantillas restantes (Fase B: `quote`,
  `breaking`, `encuesta`, `edu`; Fase C: `flash`, `calendario`, `semanal`, `earnings`; Fase D:
  `market`, `idea`, `macro`) — cada una su propio Change, según el plan de fases de la spec
  canónica (PR #118).
- Modo dual 9:16/16:9 o parámetro de tamaño en `render_png` — decisión ya tomada, no se discute.
- Anidamiento de `resolver_loops` (`FOR` dentro de `FOR`) — un solo nivel alcanza para el
  catálogo completo de las 12 plantillas (ninguna lo necesita); si una plantilla futura lo
  necesitara, es extensión de un Change aparte.
- Cambios al contrato de datos `story_alerta` (nombres de campos, tipos, obligatoriedad
  semántica) — solo cambian layout/viewport, no el payload que ya construye `story.md` PASO 5.
- `scripts/ruta_story.ps1` — confirmado sin cambios (ver "Preguntas abiertas — resueltas", Q8).
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles"
  (`.claude/shared/modo_ejecutivo.md:22`); no se reabre ese criterio en esta Fase.
- El PNG de `/chart` (`data/mt5_command.json`, EA `GI_ChartExporter`) — ya se genera en
  `1920×1080` (`.claude/commands/chart.md:61`); no requiere cambios (ver R6).
- Los 6 archivos ajenos al director (`.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`,
  `templates/encuesta_posicion.txt`, `templates/encuesta_tendencia.txt`, `uv.lock`) — fuera de
  alcance de este Change, no tocar.

## Requisitos funcionales

### R1 — Viewport único 1920×1080
`render_png` abre la página con `viewport={"width": 1920, "height": 1080}` como único valor
— sin parámetro de tamaño ni modo dual. El PNG resultante tiene esas dimensiones exactas
(IHDR). Mapea al punto 1 de la hipótesis de `idea.md`/`proposal.md`.

### R2 — Tokens escalares dinámicos derivados del payload
`build_context(payload)` recorre **todas** las claves escalares top-level del payload (valores
no-`dict`/no-`list`, incluidos `None`/booleanos/números convertidos a `str`) y las expone como
candidatas de sustitución `{{clave}}`, en vez de iterar `_TOKENS_ESCALARES` (lista fija,
obligatoria). Ya no existe una noción de "campo obligatorio del payload" a nivel de
`build_context`: si el HTML de la plantilla usa un `{{token}}` que el payload no provee (ni
como escalar ni como derivado de un helper), el error surge en la guardia
`_validar_sin_huerfanos` (fase 4 de `build_html`, post-sustitución) — mismo criterio fail-fast
que hoy, aplicado de forma genérica en vez de ad hoc por plantilla. Mapea al punto 2 de la
hipótesis y resuelve Q1.

### R3 — Claves del payload no usadas en el HTML: no-op silencioso
Si el payload trae una clave escalar que ninguna plantilla referencia como `{{clave}}`, esa
clave se calcula en el contexto pero simplemente no encuentra ocurrencia que sustituir en el
HTML — no es error, no se advierte, no se loguea. `build_context` no valida "¿esta clave se
usa en algún lado?"; solo la guardia posterior valida la dirección opuesta (¿quedó algún
`{{token}}` sin resolver?). Resuelve la segunda mitad de Q1.

### R4 — `resolver_loops`: expansión de bloques `<!-- FOR:clave -->`
Nueva función que:
1. Se ejecuta **antes** de `_resolver_fences` (orden canónico: loops → fences → tokens →
   guardia).
2. Para cada bloque `<!-- FOR:clave -->…<!-- ENDFOR:clave -->`, si `payload[clave]` es un
   array de N objetos, reemplaza el bloque completo por la concatenación de N repeticiones del
   contenido interno, sustituyendo dentro de cada repetición los tokens propios del objeto
   correspondiente (`{{campo}}` → `objeto[i]["campo"]`).
3. **Array vacío** (`payload[clave] == []`): el bloque se reemplaza por una cadena vacía (0
   repeticiones) — desaparece por completo, sin dejar contenido dentro de las marcas
   `FOR`/`ENDFOR`. Los contenedores/headers que deban persistir siempre (incluso sin filas)
   deben ubicarse en el HTML **fuera** de las marcas `<!-- FOR -->`/`<!-- ENDFOR -->` —
   convención documentada para las plantillas de Fase C (`flash`, `calendario`, `semanal`,
   `earnings`), que sí usan este mecanismo.
4. Soporta un único nivel: `resolver_loops` no resuelve un `<!-- FOR -->` anidado dentro de
   otro `<!-- FOR -->` (queda fuera de alcance explícito, ver OUT).
Mapea al punto 3 de la hipótesis y resuelve Q3/Q4.

### R5 — Catálogo cerrado de 4 helpers de derivación
Se fija ya en esta Fase el conjunto (más chico que "todas las claves") de nombres de clave
conocidos que disparan lógica propia en `build_context`, aunque no todos tengan consumidor
real en Alerta hoy:
1. **Flecha de dirección**: disparada por un objeto con clave `direccion` (ej. `variacion.
   direccion`) → deriva `<contenedor>_flecha` = `▲` (alcista) / `▼` (bajista) / `""` (otro
   valor). Consumidor real hoy: `variacion_flecha` en Alerta.
2. **Slug de color direccional**: disparada por `sesgo` o `variacion.direccion` → deriva
   `sesgo_slug` (prioriza `variacion.direccion` sobre `sesgo`, igual que hoy) para la clase CSS
   de color verde `#00DC82`/rojo `#E84040`. Consumidor real hoy: `sesgo_slug` en Alerta.
3. **Badge de impacto**: disparada por `impacto` (valores `alto`/`medio`, case-insensitive) →
   deriva `impacto_badge` (`ALTO`/`MEDIO` en mayúsculas). Sin consumidor real en Alerta; su
   primer consumidor será `calendario` (Fase C) — se fija el helper ahora para que Fase C no
   requiera tocar el motor.
4. **Chart embebido**: disparada por `chart_png` → deriva `chart_src` (URI `file:///`,
   validación de existencia — CB-8 se conserva sin cambios). Consumidor real hoy en Alerta.
Mapea al punto 2 de la hipótesis y resuelve Q2.

### R6 — Migración de `templates/stories/alerta.html` a 1920×1080
El snapshot se redimensiona a horizontal (`html, body { width: 1920px; height: 1080px; }` y
`.story` equivalente), reorganizando el layout existente (chips, titular, párrafo, tarjeta de
precio con borde rojo, stats soporte/resistencia/vol, bloque de gráfico, footer) en una
composición horizontal que conserve el sistema visual GI (paleta, tipografías Syne/DM
Sans/Space Grotesk, footer estándar). **Los nombres de tokens y fences no cambian**
(`{{titular}}`, `{{soporte}}`, `<!-- IF:variacion -->`, etc. — mismo contrato `story_alerta`).
El PNG que embebe `chart_png` (generado por `/chart`, ya en `1920×1080` según
`.claude/commands/chart.md:61`) encaja nativamente en el nuevo viewport horizontal — no
requiere recorte ni lógica nueva; el ajuste visual fino, si hace falta, se resuelve con
`object-fit` en el CSS del snapshot (mismo mecanismo que hoy usa `#img-alerta`). Mapea al
punto 5 de la hipótesis y resuelve Q5.

### R7 — Sincronización de documentación
Actualizar las 3 referencias literales a `1080×1920`/9:16 identificadas por búsqueda
exhaustiva del repo (`rg` sobre `*.md`, excluidos `.pulse/changes/**` que son historial):
`CLAUDE.md:249` y `CLAUDE.md:322` (sección "Stories GI" + tabla de comandos Capa 2),
`.claude/commands/story.md:1` (descripción del comando), y
`docs/design/stories-gi/plantillas-stories-gi.md:32` (intro del catálogo de piezas del
canvas). Ningún otro `.md` del repo (README, `docs/architecture.md`,
`docs/commands-reference.md`, `docs/setup-guide.md`) menciona estas dimensiones — confirmado
por búsqueda, no requieren cambios. Resuelve Q7.

### R8 — Estrategia de migración de tests: reescritura in-place
`tests/test_story_render.py` se reescribe **in-place** (no conviven versiones paralelas 9:16 y
16:9): no existe modo dual que justifique mantener ambas, y el motor generalizado debe seguir
produciendo el contrato observable equivalente para Alerta. Concretamente:
- `test_build_html_contract` y `test_alerta_no_placeholders`/`test_alerta_chart_embebido`
  siguen validando el mismo contrato de tokens/fences de Alerta (sin cambios de aserciones de
  contenido, solo de layout implícito).
- `test_render_dimensiones_1080x1920` se renombra a `test_render_dimensiones_1920x1080` y su
  assert pasa de `(1080, 1920)` a `(1920, 1080)`.
- Se agregan tests puros nuevos de `resolver_loops` (array vacío, 1 elemento, N elementos),
  aislados con un fixture propio (no dependen de ninguna plantilla real de Fase B/C/D).
- `tests/fixtures/stories/fixture_template.html` **no necesita cambiar sus dimensiones**: es un
  HTML mínimo sin CSS de viewport (`build_html`/`resolver_loops` son puros y no dependen del
  tamaño — solo `render_png` usa el viewport). Se le pueden agregar bloques `<!-- FOR -->` para
  aislar el test de `resolver_loops` del snapshot de marca real, igual que ya aísla fences/
  tokens hoy.
Resuelve Q6.

## Casos borde

- **CB-1 (payload con clave no usada en el HTML)**: no-op silencioso, no es error (R3).
- **CB-2 (HTML usa un `{{token}}` sin origen en el payload ni en ningún helper)**: falla en la
  guardia `_validar_sin_huerfanos`, mismo mensaje accionable de hoy listando los huérfanos (R2).
- **CB-3 (`FOR` con array vacío)**: el bloque desaparece sin rastro; el header/contenedor que
  deba persistir se ubica fuera del bloque `FOR`/`ENDFOR` (R4).
- **CB-4 (`FOR` anidado)**: no soportado; si el HTML lo intentara, `resolver_loops` no lo
  resuelve (el `<!-- FOR -->` interno queda como texto literal y cae en la guardia si contiene
  tokens sin resolver) — comportamiento aceptado, no se implementa detección explícita en esta
  Fase (R4, OUT).
- **CB-5 (`impacto` con valor fuera de `alto`/`medio`)**: mismo criterio que hoy con
  `direccion` fuera de `alcista`/`bajista` — el helper no reconoce el valor y deriva cadena
  vacía o el propio valor sin badge (a definir en Design, no bloqueante para Specify).
- **CB-6 (`chart_png` con ruta inexistente)**: se conserva `StoryRenderError` accionable — sin
  cambios respecto al CB-8 heredado de `.pulse/specs/stories-gi/spec.md`.
- **CB-7 (Chromium ausente)**: se conserva el CB-7 heredado sin cambios (mensaje con
  `uv sync --extra stories && python -m playwright install chromium`).

## Criterios de aceptación

**AC1 — viewport y dimensiones exactas (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de ejemplo `story_alerta` (sin `variacion`, sin `vol_pct`, `chart_png: null`),
CUANDO se ejecuta `render_story` contra `templates/stories/alerta.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB.
_(Reemplaza AC3 del contrato heredado #109; mismo umbral de tamaño.)_

**AC2 — tokens dinámicos: payload con clave extra no usada (ejecutable, `pytest`)**
DADO un payload que incluye una clave escalar adicional que ninguna plantilla referencia (ej.
`"nota_interna": "solo para QA"`),
CUANDO se ejecuta `build_html` sobre un fixture mínimo,
ENTONCES el render se completa sin error y el HTML resultante no contiene `nota_interna` en
ninguna parte (no-op silencioso, R3/CB-1).

**AC3 — tokens dinámicos: HTML con token sin origen (ejecutable, `pytest`)**
DADO un fixture HTML con un `{{token_inventado}}` que no existe en el payload ni es derivado
de ningún helper conocido,
CUANDO se ejecuta `build_html`,
ENTONCES se lanza `StoryRenderError` mencionando `token_inventado` (guardia de huérfanos,
R2/CB-2). _(Ya cubierto en espíritu por `test_build_html_token_huerfano_lanza_error` existente
— se conserva.)_

**AC4 — `resolver_loops` con array vacío (ejecutable, `pytest`)**
DADO un payload `{"filas": []}` y un fixture con
`<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->`,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado no contiene ninguna ocurrencia de `{{nombre}}` ni del contenido interno
del bloque, y las marcas `FOR`/`ENDFOR` desaparecen (R4/CB-3).

**AC5 — `resolver_loops` con 1 elemento (ejecutable, `pytest`)**
DADO un payload `{"filas": [{"nombre": "USD/CLP"}]}` y el mismo fixture,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado contiene exactamente una ocurrencia de `USD/CLP` y ninguna marca
`FOR`/`ENDFOR` ni `{{nombre}}` sin resolver (R4).

**AC6 — `resolver_loops` con N elementos (ejecutable, `pytest`)**
DADO un payload `{"filas": [{"nombre": "USD/CLP"}, {"nombre": "Oro"}, {"nombre": "WTI"}]}` y el
mismo fixture,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado contiene `USD/CLP`, `Oro` y `WTI`, en ese orden, cada uno exactamente una
vez, y ninguna marca `FOR`/`ENDFOR` sin resolver (R4).

**AC7 — helper de badge de impacto disponible aunque sin consumidor en Alerta (ejecutable,
`pytest`)**
DADO un payload con `"impacto": "alto"` y un fixture con `{{impacto_badge}}`,
CUANDO se ejecuta `build_context`,
ENTONCES el contexto resultante contiene `impacto_badge == "ALTO"` (R5, helper 3 fijado ya en
esta Fase).

**AC8 — orden canónico `loops → fences → tokens → guardia` (ejecutable, `pytest`)**
DADO un fixture que combina un bloque `<!-- FOR:filas -->` que a su vez contiene un fence
`<!-- IF:x -->` interno a cada fila,
CUANDO se ejecuta `build_html`,
ENTONCES el resultado resuelve primero el `FOR` (produciendo N copias del fence interno) y
luego cada fence según los datos de su propia fila — verificable inspeccionando que el fence se
evalúa **por elemento**, no una sola vez sobre el payload completo (R4).

**AC9 — contrato de Alerta preservado tras la migración (ejecutable, `pytest`)**
DADO el payload de ejemplo `story_alerta` (mismo de AC1, más la variante con `chart_png`
apuntando a un fixture existente),
CUANDO se ejecuta `build_html` contra el `templates/stories/alerta.html` migrado,
ENTONCES el HTML contiene `titular`, `parrafo`, `precio_actual`, `soporte`, `resistencia` y
`tag_riesgo` correctamente inyectados, NO contiene placeholders sin resolver, omite los slots
de variación/volumen cuando el payload no los trae, y el chart embebido/SVG decorativo se
comporta exactamente igual que hoy (AC2/AC9 heredados de `.pulse/specs/stories-gi/spec.md`,
sin regresión).

**AC10 — sincronización de documentación (estructural, `rg`)**
`rg "1080.?1920" CLAUDE.md '.claude/commands/story.md' 'docs/design/stories-gi/plantillas-stories-gi.md'`
→ 0 matches (todas las referencias migradas a `1920×1080`); `rg "1920.?1080" CLAUDE.md` → ≥2
matches (línea de la sección "Stories GI" y la fila de `/story` en la tabla de comandos).

**AC11 — `resolver_loops` no soporta anidamiento, documentado (estructural)**
El docstring/comentario de `resolver_loops` en `scripts/story_render.py` menciona
explícitamente "un solo nivel" o equivalente — verificable con
`rg -i "nivel" scripts/story_render.py` ≥1 match tras la implementación (Design/Apply).
_(Criterio de documentación, no de comportamiento — el comportamiento lo cubre AC4-AC6.)_

**AC12 — sin regresión en `ruta_story.ps1` (estructural, `rg`)**
`git diff master -- scripts/ruta_story.ps1` (o equivalente al cerrar el Change) no muestra
cambios — confirma que Q8 se resolvió sin tocar el helper.

## Riesgos

- **Riesgo A — fidelidad visual del rediseño horizontal**: migrar el layout vertical de Alerta
  a horizontal implica reorganizar densidad de información (chips, titular, tarjeta, gráfico,
  footer) en un viewport más ancho y más bajo; no hay "golden PNG" de referencia del canvas
  para 16:9 de esta plantilla específica (el canvas expone el maestro en 4 tamaños, pero el
  snapshot de este repo se autora localmente). Mitigación: aprobación visual manual del
  director en la primera corrida real, igual que el piloto #109 (sin comparación pixel-a-pixel
  automatizada, ya aceptado como riesgo residual R-2 en el contrato heredado).
- **Riesgo B — helpers "adelantados" sin consumidor (badge de impacto)**: fijar el helper de
  `impacto` ya en esta Fase, sin que Alerta lo use, implica testear una pieza sin caso de uso
  real hasta Fase C. Mitigación: AC7 lo cubre con un fixture aislado (no depende de una
  plantilla real), y el criterio ya está explícitamente decidido por el director (ver
  "Decisiones ya tomadas" del prompt de este Change) — no es una apuesta especulativa del
  agente.
- **Riesgo C — deriva de `build_context` sin lista fija**: al eliminar la validación de
  "campos obligatorios" (`_TOKENS_ESCALARES` fijo), un payload incompleto para Alerta ya no
  falla temprano en `build_context` con un mensaje "campo ausente: X" — falla más tarde, en la
  guardia de huérfanos, con un mensaje distinto (lista de tokens sin resolver en el HTML, no de
  claves del payload). Mitigación: el mensaje de la guardia ya es accionable (lista los
  nombres de token exactos); documentar el cambio de comportamiento en el docstring de
  `build_context` para que quien depure no busque el mensaje antiguo.

## Preguntas abiertas — resueltas

Las 7 preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Alcance de tokens dinámicos** → R2/R3: se recorren *todas* las claves escalares del
   payload; una clave del payload no usada en el HTML es no-op silencioso (R3/CB-1); un
   `{{token}}` del HTML sin origen en el payload sigue siendo error vía la guardia (R2/CB-2).
2. **Lista de helpers especiales** → R5: se fija ya el catálogo cerrado de 4 (flecha, color,
   badge de impacto, chart), aunque el badge de impacto no tenga consumidor real hasta Fase C.
3. **Anidamiento de `resolver_loops`** → R4: un solo nivel; anidamiento explícitamente fuera de
   alcance (OUT, CB-4).
4. **Array vacío en `FOR`** → R4/CB-3: el bloque desaparece por completo (0 repeticiones);
   contenedores persistentes van fuera de las marcas `FOR`/`ENDFOR`.
5. **Aspect ratio del chart embebido** → R6: sin cambio de contrato; `/chart` ya genera PNG en
   `1920×1080` (`.claude/commands/chart.md:61`), por lo que el nuevo viewport horizontal calza
   nativamente — ajuste fino, si hiciera falta, vía `object-fit` en CSS, no en Python.
6. **Estrategia de migración de tests** → R8: reescritura in-place (no hay versiones
   paralelas); `fixture_template.html` no necesita cambiar dimensiones porque `build_html`/
   `resolver_loops` son puros y no dependen del viewport.
7. **Alcance de "sincronizar docs"** → R7: exactamente 3 archivos (`CLAUDE.md` ×2 líneas,
   `story.md`, `plantillas-stories-gi.md`); confirmado por búsqueda exhaustiva que ningún otro
   `.md` del repo menciona estas dimensiones.
8. **`scripts/ruta_story.ps1`** → confirmado sin cambios (AC12): el helper ya es agnóstico al
   tamaño/aspecto de la imagen, solo arma la ruta por fecha/activo/plantilla/hora.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), fuente canónica del alcance de esta Fase A.
- `docs/design/stories-gi/plantillas-stories-gi.md:32` — línea a sincronizar (R7).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  R1-R10/CB-1..CB-8/AC1-AC9), no se reabre salvo AC3 (dimensiones) y AC2/AC9 (verificación de
  no-regresión, ver AC1/AC9 de este documento).
- `.pulse/changes/archive/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/design.md`
  — decisiones D1-D7 heredadas (mecanismo de inyección, estructura de `story_render.py`).
- `scripts/story_render.py:29-46,58-68,71-116,119-165,168-221` — motor actual a generalizar.
- `templates/stories/alerta.html:48-65` — snapshot 9:16 a migrar.
- `.claude/commands/story.md:1` — comando a sincronizar.
- `CLAUDE.md:249,322` — sección "Stories GI" y tabla de comandos a sincronizar.
- `.claude/commands/chart.md:61` — confirma que `/chart` ya genera PNG en `1920×1080` (R6).
- `.claude/shared/modo_ejecutivo.md:22` — confirma `/story` en "No elegibles", sin cambios.
- `tests/test_story_render.py` + `tests/fixtures/stories/` — suite a extender in-place (R8).
- `scripts/ruta_story.ps1` — helper de guardado, confirmado sin cambios (AC12).
- `idea.md`, `proposal.md` de este mismo Change #119 — base de este documento.
- Issue #119 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase A.
