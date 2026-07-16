# Idea: Stories GI · Fase B — plantilla Edu / Concepto educativo 16:9

## Problema

El catálogo GI de 12 plantillas 16:9 (spec/diseño aprobado, PR #118) tiene hoy **cuatro**
plantillas reales en el repo: `alerta` (Fase A, #119), `quote` (Fase B, #121, PR #122),
`breaking` (Fase B, #123, PR #124) y `encuesta` (Fase B, #125, PR #126). Este Change suma la
**quinta y última plantilla de Fase B** — `edu` (fila 07 del catálogo) — una pieza educativa
(kicker opcional + título de concepto + definición + ejemplo + lista de bullets), fondo oscuro,
**sin gráfico**, alimentada por el criterio editorial de `/concepto` y `/rencuesta`. Sigue el
patrón "1 plantilla = 1 Change" fijado en las tres Fases B previas: no reabre el motor, no
reabre `quote`/`breaking`/`encuesta`, solo agrega el quinto snapshot + su `[tipo]` en `/story` +
sus tests de mapeo.

Necesidad de negocio: la Misión del repo es "pasar de un modelo de señales a un modelo de
análisis + educación donde el cliente aprende a leer el mercado" (CLAUDE.md). `/concepto` y
`/rencuesta` ya producen contenido educativo en texto de WhatsApp; una Story 16:9 le da a
GI/ejecutivos una pieza visual reenviable (presentaciones, pantallas, feed interno) que refuerza
el mismo concepto sin agregar ningún dato de mercado ni reabrir el contrato editorial de esos
comandos.

Cierre de Fase B: al completar `edu`, las 4 plantillas "Simples" (`quote`, `breaking`, `encuesta`,
`edu`) quedan mergeadas; Fase C (`flash`, `calendario`, `semanal`, `earnings`, con listas) y
Fase D (`market`, `idea`, `macro`, con gráfico) quedan para Changes futuros.

## Contexto observado

**Motor (Fase A, ya en el repo, NO se toca en este Change)** — `scripts/story_render.py`:
viewport único `1920×1080`; tokens escalares derivados dinámicamente de las claves top-level del
payload; fences top-level (`_FENCES = ("variacion", "vol", "chart_img", "chart_svg")`) no
aplican a `edu` — ninguno de sus campos está en esa tupla fija. Orden canónico invariable:
loops → fences → tokens → guardia (`_validar_sin_huerfanos`).

**Novedad firme de este Change**: `edu` es el **primer consumidor real** del mecanismo
`<!-- FOR:clave -->…<!-- ENDFOR:clave -->` (`resolver_loops`) entre las plantillas ya mergeadas.
`quote`/`breaking`/`encuesta` no usan `FOR` (solo tokens escalares). El mecanismo ya está
implementado y probado en el motor desde Fase A (#119) — no requiere ningún cambio:
- `resolver_loops` (`scripts/story_render.py`), fixture inline en
  `tests/test_story_render.py:34` (`FIXTURE_FOR_HTML = "<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->"`)
  y tests `test_resolver_loops_vacio` (línea 184), `test_resolver_loops_uno` (línea 193),
  `test_resolver_loops_n` (línea 204) ya cubren array vacío (0 repeticiones, el bloque
  desaparece sin rastro), 1 elemento y N elementos, en orden.
- Regla ya fijada en Fase A (spec `.pulse/specs/stories-gi/spec.md`, R4/CB-3): con array vacío
  el bloque `FOR`/`ENDFOR` colapsa por completo; cualquier contenedor/header que deba persistir
  siempre (ej. el título "Puntos clave" antes de la lista) debe ubicarse **fuera** de las marcas
  `FOR`/`ENDFOR` en el HTML de `edu.html`.
- Para `edu`, el array a iterar es `bullets` — cada elemento es un objeto `{"texto": "..."}` (no
  un string suelto), porque `resolver_loops` resuelve `{{campo}}` **por objeto** dentro de cada
  repetición (mismo mecanismo que el fixture `filas: [{"nombre": "..."}]`). El token dentro del
  bloque `FOR` es `{{texto}}`, no `{{bullets}}`.

**Precedentes cerrados `quote` (#121), `breaking` (#123) y `encuesta` (#125)** — mismo patrón a
replicar, confirmado tres veces ya:
- Snapshot nuevo en `templates/stories/edu.html`, reutilizando verbatim el andamiaje de marca
  (fuentes locales `templates/stories/fonts/*.woff2`, footer estándar `@grupointeligencia` +
  `grupointeligencia.com` + disclaimer CFD, paleta base `#0D0D1A`/`#F5F3F7`) ya presente en
  `alerta.html`, `quote.html`, `breaking.html` y `encuesta.html`.
- **Patrón de campo opcional confirmado** (`autor_sub` en `quote.html`, `kicker_tema` en
  `breaking.html`, `kicker`/`nota_cierre` en `encuesta.html`): token siempre presente (payload
  trae `""` si el director no completa el campo) + CSS `.clase:empty { display:none }`. Es la vía
  correcta para el campo opcional `kicker` de `edu` — **nunca** agregar un nombre a la tupla fija
  `_FENCES` del motor.
- `.claude/commands/story.md` PASO 0 tiene hoy la lista dura de `[tipo]` soportados (`alerta`,
  `quote`, `breaking`, `encuesta`, líneas 6-36) y el patrón de "Ruta `<tipo>`" — un bloque de
  recolección propio que reemplaza los PASO 1-5 de `alerta` cuando el tipo no necesita
  `get_asset_levels`. Los bloques "Ruta `quote`" (líneas 47-111), "Ruta `breaking`" (líneas
  114-199) y "Ruta `encuesta`" (líneas 203-288) son el molde directo para el futuro bloque "Ruta
  `edu`" — con la diferencia de que `edu` necesita recolectar un **array** (`bullets`), no solo
  campos escalares.
- `tests/test_story_render.py` tiene el patrón de tests de mapeo puros contra el snapshot real
  (`build_context`/`build_html`), sin fixture nuevo, sin tocar `conftest.py` — mismo patrón a
  replicar para `edu.html`, más un caso explícito de `bullets` con N elementos (análogo a
  `test_resolver_loops_n` pero contra el snapshot real, no el fixture inline).
- `CLAUDE.md` sección "Stories GI" enumera los tipos soportados hoy (`alerta`, `quote`,
  `breaking`, `encuesta`) — se actualiza en el mismo Change para incluir `edu`.

**Contrato de `edu` (catálogo, fila 07,
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` línea 65)**:
- Campos del payload: `kicker` (opcional), `titulo_concepto`, `definicion`, `ejemplo` (compuesto
  por `valor_a`, `operador`, `valor_b`), y `bullets[]` (array → único candidato real a `FOR` de
  esta plantilla). Columna "Gráfico" = "no".
- Fondo **oscuro** (`#0D0D1A`, mismo tema que `alerta`/`quote`/`breaking`) — a diferencia de
  `encuesta` (oscuro/azul), `edu` no trae acento de color distinto documentado en el catálogo.
- Fuente de datos: **editorial**, criterio de `/concepto` y `/rencuesta` — pieza 100% educativa,
  sin precios ni dato del motor. No llama a `get_asset_levels`, `obtener_calendario_macro` ni
  ninguna tool de mercado.

**Convenciones duras que siguen aplicando sin cambios**:
- Regla "solo lectura" del canvas Claude Design compartido de GI: el snapshot `edu.html` se
  autora en el repo, nunca se sincroniza ni se sube nada hacia el canvas.
- `/story` no soporta el flag `ejecutivo` (`.claude/shared/modo_ejecutivo.md`, "No elegibles") —
  `edu` no cambia esto.
- Flujo de aprobación: preview de texto antes de renderizar/guardar cualquier PNG.
- `scripts/ruta_story.ps1` ya acepta `-Plantilla` genérico — sin cambios necesarios; por
  analogía con `quote`/`breaking`/`encuesta`, `edu` probablemente se guarda bajo `_general`
  salvo que el concepto nombre un activo específico (a decidir en Design/Specify, ver
  "Preguntas abiertas").
- "1 plantilla = 1 Change": `edu` cierra Fase B; Fase C (`flash`, `calendario`, `semanal`,
  `earnings`) queda para Changes aparte.

## Hipótesis de solución

Alcance 100% aditivo, sin tocar el motor (`scripts/story_render.py`) ni los contratos de
`alerta`/`quote`/`breaking`/`encuesta`:

1. **`templates/stories/edu.html`** (nuevo, snapshot 1920×1080): esqueleto GI equivalente al de
   `quote.html`/`breaking.html`/`encuesta.html` (fuentes locales, footer estándar, fondo oscuro
   `#0D0D1A`). Cuerpo: `kicker` (chip, OPCIONAL) + `titulo_concepto` (título destacado, núcleo
   obligatorio) + `definicion` (párrafo, núcleo obligatorio) + bloque `ejemplo` (`valor_a`,
   `operador`, `valor_b` como tokens escalares, núcleo obligatorio) + lista `bullets` vía
   `<!-- FOR:bullets -->{{texto}}<!-- ENDFOR:bullets -->` (el contenedor/header de la lista, si
   lo hay, va **fuera** del bloque FOR para no depender de que `bullets` no esté vacío).
2. **Campo opcional vía patrón `:empty` confirmado**: `kicker` es token siempre presente en el
   payload (`""` si no aplica) con su clase CSS colapsando por `:empty { display:none }` — igual
   que `autor_sub`/`kicker_tema`/`kicker` en las tres plantillas previas. Núcleo obligatorio real:
   `titulo_concepto` + `definicion` + `ejemplo` (los tres campos escalares) + `bullets` (puede ser
   `[]`, colapsa sin error — no es "opcional" en el sentido `:empty`, es el comportamiento nativo
   de `FOR` con array vacío).
3. **`bullets` como array de objetos, no de strings**: el payload trae
   `"bullets": [{"texto": "..."}, {"texto": "..."}]` porque `resolver_loops` resuelve
   `{{campo}}` por objeto dentro de cada repetición (no soporta iterar un array de strings
   sueltos) — mismo criterio que el fixture de Fase A (`filas: [{"nombre": "..."}]`).
4. **`.claude/commands/story.md`**: agregar `edu` a la lista dura de `[tipo]` en PASO 0 (junto a
   `alerta`, `quote`, `breaking`, `encuesta`) y un nuevo bloque "Ruta `edu`" — recolección
   editorial con el criterio de `/concepto`/`/rencuesta` (título + definición + ejemplo + N
   bullets, sin precios ni datos de mercado), sin llamar a `get_asset_levels`. Conserva el flujo
   preview → aprobación → render → guardado (`ruta_story.ps1 -Plantilla "edu"`). El preview debe
   listar los bullets recolectados antes de aprobar.
5. **`tests/test_story_render.py`**: tests de mapeo puros para `edu.html`
   (`build_context`/`build_html` contra el snapshot real), incluyendo al menos un caso con N
   bullets (análogo en espíritu a `test_resolver_loops_n` pero contra el snapshot real, no el
   fixture inline) y un caso con `bullets: []` (el bloque colapsa sin error) — sin fixture nuevo
   en `tests/fixtures/stories/`, sin tocar `conftest.py`.
6. **`CLAUDE.md`**: actualizar la enumeración de `[tipo]` soportados en la sección "Stories GI"
   para incluir `edu` (cierre de Fase B: `alerta`, `quote`, `breaking`, `encuesta`, `edu`).
7. El motor y los contratos de `alerta`/`quote`/`breaking`/`encuesta` **no se tocan** — este
   Change solo agrega el quinto contrato de datos y snapshot, consumiendo el motor genérico tal
   cual quedó en Fase A (incluido `resolver_loops`, ya validado, sin cambios).

## Preguntas abiertas

- Layout exacto del bloque `ejemplo` (`valor_a` + `operador` + `valor_b`): ¿se presenta como una
  "mini fórmula" horizontal (ej. "Soporte 2.300 − Resistencia 2.360 = Rango 60") o como tres
  líneas separadas? El catálogo no especifica el tratamiento visual — a definir en Design.
- Número esperado/recomendado de `bullets` (¿2-4 fijos, o cualquier N que el director dicte?) —
  afecta el diseño de la lista en `edu.html` (espaciado, tamaño de fuente) y el límite editorial
  de caracteres por bullet a fijar en `story.md` (mismo patrón que los límites de `quote`/
  `breaking`/`encuesta`).
- ¿`kicker` en `edu` es libre (ej. "CONCEPTO DE LA SEMANA", "GLOSARIO") o semi-fijo por
  convención editorial de `/concepto`/`/rencuesta`? Definir en Design.
- ¿`edu` se guarda con `-Activo` cuando el concepto se ilustra con un activo específico (ej. un
  ejemplo de RSI sobre USD/CLP) o siempre bajo `_general` como `quote`/`breaking` (a diferencia de
  `encuesta`, que sí puede llevar `-Activo`)? Definir el criterio de `ruta_story.ps1 -Activo` en
  Design/Specify, siguiendo el patrón de pregunta explícita al director ya usado en `breaking`/
  `encuesta`.
- `docs/design/stories-gi/plantillas-stories-gi.md` no tiene todavía una sección de mapeo
  campo-por-campo dedicada a `edu` (solo la fila del catálogo) — igual situación que tenían
  `breaking`/`encuesta` antes de su Change. Definir en Design si esta Fase agrega esa sección.
- ¿El bloque "Ruta `edu`" de `story.md` debe distinguir entre origen `/concepto` (concepto nuevo
  de la semana) y origen `/rencuesta` (desarrollo didáctico de una encuesta ya corrida), o la
  Story siempre usa el mismo layout (kicker + título + definición + ejemplo + bullets) sin
  importar el comando de origen? Revisar contra `.claude/commands/concepto.md` y
  `.claude/commands/rencuesta.md`.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño aprobado
  (PR #118), catálogo de las 12 plantillas; fila 07 `edu` (línea 65): payload `kicker,
  titulo_concepto, definicion, ejemplo(valor_a, operador, valor_b), bullets[]`, sin gráfico,
  fondo oscuro, fuente `/concepto` · `/rencuesta`; línea 76 (plantillas con `filas[]`/
  `bullets[]` requieren `<!-- FOR -->`); línea 91 (plan de fases: Fase B = `quote`, `breaking`,
  `encuesta`, `edu` — este Change cierra la Fase).
- `docs/design/stories-gi/plantillas-stories-gi.md` — sistema visual GI (manual de marca); no
  tiene aún sección dedicada a `edu` (ver "Preguntas abiertas").
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; bloques `change:119` (motor + `FOR`,
  R4/CB-3/AC4-AC6), `change:121` (quote), `change:123` (breaking) y `change:125` (encuesta) como
  precedente directo de formato a replicar para `story_edu`. El bloque `change:119` es la fuente
  normativa del mecanismo `FOR` que `edu` consume por primera vez en una plantilla mergeada.
- `.pulse/changes/archive/125-stories-gi-fase-b-plantilla-encuesta-16-9/` (idea.md, proposal.md,
  spec.md, design.md, tasks.md) — Change antecedente inmediato (misma Fase B): confirma el
  patrón "1 snapshot + 1 bloque de recolección en `story.md` + tests de mapeo puros +
  actualización de `CLAUDE.md`" y la convención "1 plantilla = 1 Change".
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/` y
  `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/` — Changes fundacionales
  del patrón de campo opcional (token + `:empty` CSS), replicado en `breaking`/`encuesta` y a
  replicar aquí para `kicker`.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/` —
  Change fundacional del motor y de `resolver_loops`/`FOR` (decisiones R1-R8, R4/CB-3), no se
  reabre; `edu` es su primer consumidor real fuera de los tests puros del motor.
- `scripts/story_render.py` — motor 16:9 ya generalizado, incluido `resolver_loops`, **no se
  modifica** en este Change.
- `tests/test_story_render.py:34,184,193,204` — fixture inline `FIXTURE_FOR_HTML` y tests
  `test_resolver_loops_vacio/uno/n` que ya validan el mecanismo `FOR` que `edu` reutilizará
  contra su propio snapshot.
- `templates/stories/quote.html`, `templates/stories/breaking.html` y
  `templates/stories/encuesta.html` — moldes estructurales más cercanos (plantillas "Simples",
  campo opcional vía `:empty`); ninguno usa `FOR` — `edu` es el primer snapshot mergeado que sí
  lo necesita.
- `templates/stories/alerta.html` — referencia de andamiaje base (fuentes, footer, disclaimer
  CFD) reutilizado verbatim en todas las plantillas Simples.
- `.claude/commands/story.md` — comando a extender (PASO 0, líneas 6-36: agregar `edu` a
  `[tipo]`; nuevo bloque "Ruta `edu`" análogo a "Ruta `quote`"/"Ruta `breaking`"/"Ruta
  `encuesta`", líneas 47-288).
- `.claude/commands/concepto.md` y `.claude/commands/rencuesta.md` — comandos fuente del
  criterio editorial de `edu` (concepto de la semana / desarrollo didáctico de encuesta).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de tipos soportados para incluir
  `edu` (cierre de Fase B).
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin cambios
  esperados en esta Fase).
- Issue #127 (madre de este Change); issues #121 (quote), #123 (breaking) y #125 (encuesta) como
  precedentes cerrados directos de Fase B.
