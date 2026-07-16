# Proposal: Stories GI · Fase B — plantilla Encuesta 16:9

## Problema

El catálogo GI de 12 plantillas 16:9 tiene hoy tres plantillas reales en el repo: `alerta`
(Fase A, #119), `quote` (Fase B, #121, v0.3.0) y `breaking` (Fase B, #123, v0.4.0, ya archivado
y promovido). Este Change agrega la cuarta de Fase B — **`encuesta`** (fila 09 del catálogo) —
una pieza de sentimiento binario (kicker + pregunta + dos opciones + nota de cierre), fondo
oscuro/azul, **sin gráfico y sin listas**, alimentada por el criterio editorial 100% de
sentimiento puro de `/encuesta` (sin precios, sin educación, sin dato del motor). Sigue el
patrón "1 plantilla = 1 Change": no reabre el motor ni `quote`/`breaking`, solo agrega el cuarto
snapshot + su `[tipo]` en `/story` + sus tests de mapeo.

## Contexto observado

**Mecanismo de fences del motor** (`scripts/story_render.py`, verificado en código, no se
modifica en este Change): `_resolver_fences`/`_fence_presente` recorren una tupla **fija**
`_FENCES = ("variacion", "vol", "chart_img", "chart_svg")` — los 4 nombres de Alerta. Ninguno
aplica a `encuesta`, y el catálogo no le asigna ningún campo array, así que `resolver_loops`
(`<!-- FOR -->`) tampoco aplica. Esto confirma, por tercera vez ya (`quote`, `breaking`,
`encuesta`), que **ningún campo de `encuesta` puede condicionarse vía fence sin tocar el
motor** (fuera de alcance) — los 5 tokens son escalares incondicionales.

**Patrón de campo opcional ya validado dos veces** (`quote` #121: `autor_sub`; `breaking` #123:
patrón replicado): token siempre presente en el payload (`""` si no aplica) + CSS
`.clase:empty { display: none; }` sobre su contenedor — nunca una fence nueva en `_FENCES`. Es
el único mecanismo válido para campos opcionales de plantillas nuevas.

**Contrato de `encuesta`** (catálogo, fila 09, línea 67 del design doc de 2026-07-14): payload
`kicker`, `pregunta`, `opcion_a`, `opcion_b`, `nota_cierre` — sin campos array, sin gráfico;
fondo oscuro/azul (familia visual distinta de `alerta`/`quote`/`breaking`, que son oscuro/rojo);
fuente editorial: criterio de `/encuesta` (sentimiento puro, CLAUDE.md "3 tipos sin precios ni
educación") — no llama a `get_asset_levels` ni a ninguna tool de mercado, no busca eventos por
cuenta propia. Núcleo obligatorio real: `pregunta` + `opcion_a` + `opcion_b`; `kicker` y
`nota_cierre` son los dos candidatos a campo opcional vía `:empty`.

**Convenciones heredadas sin cambios** (ya citadas en `idea.md`): regla "solo lectura" del canvas
GI; `/story` fuera del flag `ejecutivo`; flujo de aprobación (preview antes de render/guardado);
`ruta_story.ps1` ya acepta `-Plantilla` genérico; "1 plantilla = 1 Change" (`encuesta` no
arrastra `edu`).

## Hipótesis de solución

Alcance 100% aditivo, motor sin cambios, contrato de `alerta`/`quote`/`breaking` sin cambios:

1. **`templates/stories/encuesta.html`** (nuevo, snapshot 1920×1080): esqueleto de marca GI
   equivalente al de `quote.html`/`breaking.html` (fuentes locales `templates/stories/fonts/`,
   footer estándar `@grupointeligencia` + `grupointeligencia.com` + disclaimer CFD verbatim),
   reemplazando el acento rojo (`#E84040`, radial `#2A1220`) por el azul de la paleta GI ya
   presente en `templates/stories/alerta.html` — el hex exacto lo fija Design (no se inventa
   acá; criterio: derivarlo de los acentos ya usados en `alerta.html`, evaluando también los
   candidatos `#1E3A5F`/`#3E91AF`/`#53C1AB` del design doc). Cuerpo: `kicker` (chip, OPCIONAL) +
   `pregunta` (texto destacado, núcleo obligatorio) + `opcion_a`/`opcion_b` (dos bloques
   comparativos tipo "A vs B", núcleo obligatorio) + `nota_cierre` (línea de cierre, OPCIONAL).
   Todos los tokens escalares incondicionales, ningún fence `IF`/`FOR`, mismo criterio que
   `quote`/`breaking`.
2. **Campos opcionales vía patrón `:empty` ya confirmado**: `kicker` y `nota_cierre` son tokens
   siempre presentes en el payload (`""` si no aplican) con su clase CSS colapsando por
   `:empty { display: none; }` — igual que `autor_sub` en `quote.html`. Ningún cambio al motor
   ni a `_FENCES`.
3. **`.claude/commands/story.md`**: agregar `encuesta` a la lista dura de `[tipo]` en PASO 0
   (junto a `alerta`, `quote`, `breaking`) y un nuevo bloque "Ruta `encuesta`", espejo de "Ruta
   `breaking`" — recolección editorial con el criterio de sentimiento puro de `/encuesta`
   (pregunta + dos opciones, sin precios ni datos de mercado, sin llamar a `get_asset_levels` ni
   ejecutar búsqueda propia de evento). Conserva el flujo preview → aprobación → render →
   guardado (`ruta_story.ps1 -Plantilla "encuesta"`).
4. **Guardado**: por defecto `-Activo "_general"`, igual criterio que `quote`/`breaking`; si el
   director indica un activo protagonista claro (ej. encuesta de tendencia sobre un activo
   específico), el bloque de recolección pasa ese ticker a `ruta_story.ps1 -Activo`. Criterio
   editorial, decidido por el director al aprobar, no una regla automática nueva del motor.
5. **`tests/test_story_render.py`**: tests de mapeo puros para `encuesta.html`
   (`build_context`/`build_html` contra el snapshot real, incluyendo los casos de `kicker`/
   `nota_cierre` vacíos), análogos a los de `quote.html`/`breaking.html`. Sin fixture nuevo, sin
   tocar `conftest.py`.
6. **`CLAUDE.md`** § "Stories GI": actualizar la enumeración de `[tipo]` soportados (hoy
   `alerta`, `quote`, `breaking`) para incluir `encuesta`.
7. Motor (`build_context`, `resolver_loops`, `_FENCES`, `render_png`) y contratos de `alerta`/
   `quote`/`breaking` **no se tocan**.

## Criterios de aceptación (alto nivel)

- `templates/stories/encuesta.html` renderiza a 1920×1080 vía `scripts/story_render.py` sin
  modificar el motor.
- El HTML resultante no contiene placeholders `{{`/`}}` sin resolver para ningún caso de payload
  válido (con y sin `kicker`/`nota_cierre`).
- `kicker` y `nota_cierre` colapsan visualmente (vía `:empty` CSS) cuando el payload los trae en
  `""`; el núcleo `pregunta` + `opcion_a` + `opcion_b` siempre se renderiza.
- `encuesta` queda registrado como `[tipo]` válido en `.claude/commands/story.md` (PASO 0 + bloque
  "Ruta `encuesta`").
- `tests/test_story_render.py` pasa en verde incluyendo los nuevos tests de mapeo de `encuesta`.
- `CLAUDE.md` § "Stories GI" enumera `encuesta` entre los tipos soportados.

## Alternativas descartadas

- **Tocar el motor para condicionar `kicker`/`nota_cierre` con un fence `IF` nuevo**: descartado
  por el hallazgo firme confirmado tres veces ya (`quote`, `breaking`, `encuesta`) de que
  `_FENCES` es una tupla fija y el motor de Fase A queda intacto; el patrón token + `:empty` CSS
  ya resuelve el mismo problema sin abrir el motor ni arriesgar los contratos de `alerta`/
  `quote`/`breaking`.
- **Agrupar `encuesta` con `edu` en el mismo Change** (última plantilla "Simple" pendiente de
  Fase B): descartado por la convención "1 plantilla = 1 Change" ya aplicada consistentemente en
  `quote` y `breaking`.
- **Reutilizar el snapshot rojo de `alerta`/`quote`/`breaking` sin variante azul**: descartado
  porque el catálogo (fila 09) fija explícitamente fondo oscuro/azul para `encuesta`, distinto de
  la familia rojiza ya usada en las tres plantillas previas.

## Referencias

- `.pulse/changes/125-stories-gi-fase-b-plantilla-encuesta-16-9/idea.md` — idea-doc base de esta
  propuesta (contexto completo, 5 preguntas originales).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 09 `encuesta`:
  payload `kicker, pregunta, opcion_a, opcion_b, nota_cierre`, sin gráfico, fondo oscuro/azul,
  fuente `/encuesta`.
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; contratos ya formalizados de
  `story_alerta`, `story_quote` y `story_breaking` como precedente directo de formato.
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/` (idea.md, proposal.md,
  spec.md, design.md, tasks.md) — Change antecedente inmediato (misma Fase B): confirma el
  patrón "1 snapshot + 1 bloque de recolección + tests de mapeo puros + `CLAUDE.md`" y la
  convención "1 plantilla = 1 Change".
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/` — Change fundacional del
  patrón de campo opcional (token + `:empty` CSS).
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/` —
  Change fundacional del motor, no se reabre.
- `scripts/story_render.py` — motor 16:9 generalizado, no se modifica.
- `templates/stories/quote.html` y `templates/stories/breaking.html` — moldes estructurales más
  cercanos (plantillas simples, sin gráfico ni fences/loops, campo opcional vía `:empty`).
- `templates/stories/alerta.html` — referencia de andamiaje base y acentos de marca a derivar
  para la variante azul.
- `.claude/commands/story.md` — comando a extender (PASO 0 + nuevo bloque "Ruta `encuesta`").
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para `encuesta`.
- `CLAUDE.md` § "Stories GI" — actualizar la enumeración de tipos soportados.
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles", sin cambios.
- Contrato editorial `/encuesta` (CLAUDE.md, sección "Encuestas diarias"; memoria
  `project_encuesta_sentimiento`): sentimiento puro, sin precios ni educación.
- Issue madre de esta Fase B · `encuesta` (a vincular en GitHub); issues #121 (quote) y #123
  (breaking) como precedentes cerrados directos.
