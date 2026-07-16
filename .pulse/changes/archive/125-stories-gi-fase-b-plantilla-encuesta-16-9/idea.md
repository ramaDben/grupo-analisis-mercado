# Idea: Stories GI · Fase B — plantilla Encuesta 16:9

## Problema

El catálogo GI de 12 plantillas 16:9 (spec/diseño aprobado, PR #118) tiene hoy **tres**
plantillas reales en el repo: `alerta` (Fase A, #119, motor generalizado), `quote` (Fase B,
#121, v0.3.0) y `breaking` (Fase B, #123, v0.4.0, ya archivado y promovido). Este Change suma
la cuarta de Fase B — **`encuesta`** (fila 09 del catálogo) — una pieza de **sentimiento
binario** (kicker + pregunta + dos opciones + nota de cierre), fondo oscuro/azul, **sin
gráfico y sin listas**, alimentada por el criterio editorial de `/encuesta`. Sigue el patrón
"1 plantilla = 1 Change" ya fijado en las tres Fases previas: no reabre el motor, no reabre
`quote`/`breaking`, solo agrega el cuarto snapshot + su `[tipo]` en `/story` + sus tests de
mapeo.

Necesidad de negocio: `/encuesta` ya es el comando canónico de sentimiento puro (sin precios,
sin educación — ver CLAUDE.md y memoria `project_encuesta_sentimiento`). Hoy esas encuestas
solo existen como texto de WhatsApp; una Story 16:9 le da a GI/ejecutivos una pieza visual
reenviable que refuerza la misma pregunta sin agregar ningún dato nuevo ni romper el contrato
editorial "sentimiento puro" (no precios, no educación, no dato del motor).

## Contexto observado

**Motor (Fase A, ya en el repo, NO se toca en este Change)** — `scripts/story_render.py`:
viewport único `1920×1080`; tokens escalares derivados dinámicamente de las claves top-level
del payload; `resolver_loops` (`<!-- FOR:clave -->`) no aplica — `encuesta` no tiene ningún
campo array; fences top-level (`_FENCES = ("variacion", "vol", "chart_img", "chart_svg")`) no
aplican — ninguno de los 5 campos de `encuesta` está en esa tupla fija. Orden canónico
invariable: loops → fences → tokens → guardia (`_validar_sin_huerfanos`).

**Precedentes cerrados `quote` (#121) y `breaking` (#123)** — mismo patrón a replicar,
confirmado dos veces ya:
- Snapshot nuevo en `templates/stories/encuesta.html`, reutilizando verbatim el andamiaje de
  marca (fuentes locales `templates/stories/fonts/*.woff2`, footer estándar
  `@grupointeligencia` + `grupointeligencia.com` + disclaimer CFD, paleta base
  `#0D0D1A`/`#F5F3F7`) ya presente en `alerta.html`, `quote.html` y `breaking.html`.
- **Patrón de campo opcional confirmado en `quote.html`** (`autor_sub`, líneas ~127 y 164):
  token siempre presente (payload trae `""` si el director no completa el campo) + CSS
  `.clase:empty { display:none }`. Es la vía correcta para campos opcionales de plantillas
  nuevas — **nunca** agregar un nombre a la tupla fija `_FENCES` del motor.
- `.claude/commands/story.md` PASO 0 tiene hoy la lista dura de `[tipo]` soportados (`alerta`,
  `quote`, `breaking`, líneas 6-32) y el patrón de "Ruta `<tipo>`" — un bloque de recolección
  propio que reemplaza los PASO 1-5 de `alerta` cuando el tipo no necesita `get_asset_levels`.
  El bloque "Ruta `quote`" (líneas 43-108) y "Ruta `breaking`" (líneas 110-192) son el molde
  directo para el futuro bloque "Ruta `encuesta`".
- `tests/test_story_render.py` tiene el patrón de tests de mapeo puros contra el snapshot real
  (`build_context`/`build_html`), sin fixture nuevo, sin tocar `conftest.py` — mismo patrón a
  replicar para `encuesta.html`.
- `CLAUDE.md` sección "Stories GI" enumera los tipos soportados hoy (`alerta`, `quote`,
  `breaking`) — se actualiza en el mismo Change si `encuesta` se agrega.

**Contrato de `encuesta` (catálogo, fila 09,
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` línea 67)**:
- Campos del payload: `kicker`, `pregunta`, `opcion_a`, `opcion_b`, `nota_cierre` — sin campos
  array, sin gráfico (columna "Gráfico" = "no").
- Fondo **oscuro/azul** — misma etiqueta de la fila 04 `idea` (Trading Idea, tema azul
  `#1E3A5F`) pero sin las 3 tarjetas de esa plantilla; línea 24-26 del mismo doc registra los
  acentos de marca ya observados en el canvas GI: `#3E91AF` y `#53C1AB` (neutros), distintos
  del rojo `#E84040`/`#2A1220` usado en `alerta`/`quote`/`breaking`. Estos son los candidatos
  de paleta azul a fijar en Design — no hay un snapshot de plantilla ya renderizada en azul en
  el repo hoy (todas las Fase A/B existentes son oscuro/rojo).
- Fuente de datos: **editorial**, criterio de `/encuesta` — pieza 100% de sentimiento, sin
  precios ni dato del motor (contrato editorial de `/encuesta`, CLAUDE.md: "3 tipos sin
  precios ni educación"). No llama a `get_asset_levels` ni a ninguna tool de mercado.

**Convenciones duras que siguen aplicando sin cambios**:
- Regla "solo lectura" del canvas Claude Design compartido de GI: el snapshot `encuesta.html`
  se autora en el repo, nunca se sincroniza ni se sube nada hacia el canvas.
- `/story` no soporta el flag `ejecutivo` (`.claude/shared/modo_ejecutivo.md`, "No elegibles")
  — `encuesta` no cambia esto.
- Flujo de aprobación: preview de texto antes de renderizar/guardar cualquier PNG.
- `scripts/ruta_story.ps1` ya acepta `-Plantilla` genérico — sin cambios necesarios; por
  analogía con `quote`/`breaking` (ambos sin activo protagonista claro → `_general`),
  `encuesta` probablemente también se guarda bajo `_general` salvo que la pregunta nombre un
  activo específico (a decidir en Design, ver "Preguntas abiertas").
- "1 plantilla = 1 Change": `encuesta` no arrastra `edu` (la última plantilla "Simple" de
  Fase B) — Change aparte.

## Hipótesis de solución

Alcance 100% aditivo, sin tocar el motor (`scripts/story_render.py`) ni los contratos de
`alerta`/`quote`/`breaking`:

1. **`templates/stories/encuesta.html`** (nuevo, snapshot 1920×1080): esqueleto GI equivalente
   al de `quote.html`/`breaking.html` (fuentes locales, footer estándar), reemplazando el
   acento rojo (`#E84040`, radial `#2A1220`) por el azul de la paleta GI (candidatos `#1E3A5F`
   / `#3E91AF` / `#53C1AB`, a confirmar en Design). Cuerpo: `kicker` (chip, OPCIONAL) +
   `pregunta` (texto destacado, núcleo obligatorio) + `opcion_a`/`opcion_b` (dos bloques
   comparativos tipo "A vs B", núcleo obligatorio) + `nota_cierre` (línea de cierre, OPCIONAL).
   Sin gráfico, sin fences `IF`/`FOR` — 5 tokens escalares incondicionales, mismo criterio que
   `quote`/`breaking`.
2. **Campos opcionales vía patrón `:empty` confirmado**: `kicker` y `nota_cierre` son tokens
   siempre presentes en el payload (`""` si no aplican) con su clase CSS colapsando por
   `:empty { display:none }` — igual que `autor_sub` en `quote.html`. Núcleo obligatorio real:
   `pregunta` + `opcion_a` + `opcion_b`.
3. **`.claude/commands/story.md`**: agregar `encuesta` a la lista dura de `[tipo]` en PASO 0
   (junto a `alerta`, `quote`, `breaking`) y un nuevo bloque "Ruta `encuesta`" — recolección
   editorial con el criterio de sentimiento puro de `/encuesta` (pregunta + dos opciones, sin
   precios ni datos de mercado), sin llamar a `get_asset_levels`. Conserva el flujo preview →
   aprobación → render → guardado (`ruta_story.ps1 -Plantilla "encuesta"`).
4. **`tests/test_story_render.py`**: tests de mapeo puros para `encuesta.html`
   (`build_context`/`build_html` contra el snapshot real), análogos a los de
   `quote.html`/`breaking.html` — sin fixture nuevo, sin tocar `conftest.py`.
5. **`CLAUDE.md`**: actualizar la enumeración de `[tipo]` soportados en la sección "Stories GI"
   para incluir `encuesta`.
6. El motor y los contratos de `alerta`/`quote`/`breaking` **no se tocan** — este Change solo
   agrega el cuarto contrato de datos y snapshot, consumiendo el motor genérico tal cual quedó
   en Fase A.

## Preguntas abiertas

- Paleta azul exacta: el design doc menciona `#1E3A5F` (tema de la fila 04 `idea`, que sí trae
  tarjetas) y los neutros `#3E91AF`/`#53C1AB`, pero ninguna plantilla ya renderizada en el repo
  usa hoy un fondo azul (todas son oscuro/rojo). Design debe fijar los valores hex exactos del
  degradado/acento azul de `encuesta` antes de codificar el CSS.
- ¿`kicker` en `encuesta` cumple el mismo rol que `kicker_tema` en `breaking` (etiqueta de
  categoría/tema) o es distinto (ej. "Encuesta del día", fijo)? Definir en Design si el
  contenido de `kicker` es libre o semi-fijo por convención editorial de `/encuesta`.
- Layout de `opcion_a`/`opcion_b`: ¿se presentan como dos tarjetas simétricas lado a lado (tipo
  "A vs B"), o como lista vertical de dos líneas? El catálogo no especifica el tratamiento
  visual — a definir en Design junto con el eventual layout de `nota_cierre` (¿pie de página
  discreto o bloque destacado?).
- ¿`encuesta` se guarda con `-Activo` cuando la pregunta nombra un activo específico (ej. "¿Cuál
  creen que será la tendencia hoy del oro?") o siempre bajo `_general` como `quote`/`breaking`?
  A diferencia de `quote` (100% sin activo), una encuesta de tendencia sí suele nombrar un
  activo — definir el criterio de `ruta_story.ps1 -Activo` en Design.
- `docs/design/stories-gi/plantillas-stories-gi.md` no tiene todavía una sección de mapeo
  campo-por-campo dedicada a `encuesta` (solo la fila del catálogo) — igual situación que tenía
  `breaking` antes de su Change. Definir en Design si esta Fase agrega esa sección.
- ¿El bloque "Ruta `encuesta`" de `story.md` debe distinguir entre los 3 tipos de `/encuesta`
  (`posicion`, `tendencia`, `movimiento`) para adaptar el texto de `pregunta`/opciones, o la
  Story siempre usa el mismo layout binario (`opcion_a`/`opcion_b`) sin importar el tipo de
  encuesta origen? Revisar contra `templates/encuesta_posicion.txt` y
  `templates/encuesta_tendencia.txt` (ambos con cambios pendientes en el working tree actual,
  no relacionados con este Change).

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), catálogo de las 12 plantillas; fila 09 `encuesta` (línea 67): payload
  `kicker, pregunta, opcion_a, opcion_b, nota_cierre`, sin gráfico, fondo oscuro/azul, fuente
  `/encuesta`; línea 24-26 (paleta de acentos de marca); línea 79 (fila 04 `idea`, tema azul
  `#1E3A5F`, referencia de paleta); línea 91 (plan de fases: Fase B = `quote`, `breaking`,
  `encuesta`, `edu`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — sistema visual GI (manual de marca); no
  tiene aún sección dedicada a `encuesta` (ver "Preguntas abiertas").
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; contiene los contratos ya formalizados
  de `story_alerta`, `story_quote` y `story_breaking` como precedente directo de formato a
  replicar para `story_encuesta`.
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/` (idea.md,
  proposal.md, spec.md, design.md, tasks.md) — Change antecedente inmediato (misma Fase B):
  confirma el patrón "1 snapshot + 1 bloque de recolección en `story.md` + tests de mapeo puros
  + actualización de `CLAUDE.md`" y la convención "1 plantilla = 1 Change".
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/` — Change fundacional del
  patrón de campo opcional (token + `:empty` CSS), replicado en `breaking` y a replicar aquí.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/`
  — Change fundacional del motor (decisiones R1-R8 heredadas), no se reabre.
- `scripts/story_render.py` — motor 16:9 ya generalizado, **no se modifica** en este Change.
- `templates/stories/quote.html` y `templates/stories/breaking.html` — moldes estructurales más
  cercanos (plantillas "Simples", sin gráfico ni fences/loops, campo opcional vía `:empty`).
- `templates/stories/alerta.html` — referencia de andamiaje base (fuentes, footer,
  disclaimer CFD) reutilizado verbatim en todas las plantillas Simples.
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `encuesta` a `[tipo]`;
  nuevo bloque "Ruta `encuesta`" análogo a "Ruta `quote`"/"Ruta `breaking`").
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para `encuesta`.
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de tipos soportados.
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin cambios
  esperados en esta Fase).
- Contrato editorial `/encuesta` (CLAUDE.md, sección "Encuestas diarias"; memoria
  `project_encuesta_sentimiento`): sentimiento puro, sin precios ni educación — la Story
  hereda esta restricción, no llama a `get_asset_levels` ni a ninguna tool de mercado.
- Issue madre de esta Fase B · `encuesta` (a vincular en GitHub); issues #121 (quote) y #123
  (breaking) como precedentes cerrados directos.
