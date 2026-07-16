# Idea: Stories GI · Fase B — plantilla Breaking 16:9

## Problema

El catálogo GI de 12 plantillas 16:9 (spec/diseño aprobado, PR #118) tiene hoy **dos**
plantillas reales en `master`: `alerta` (Fase A, #119, motor generalizado) y `quote` (Fase B,
#121, cerrada 2026-07-15 v0.3.0, PR #122 pendiente de merge). Esta Fase B suma la tercera:
**`breaking`** (#12 del catálogo, fila 70 del diseño) — una pieza de última hora con cifra
(kicker + titular + valor + contexto + reacción), fondo oscuro/rojo, **sin gráfico y sin
listas**, alimentada por el criterio editorial de `/noticia` · `/alerta` (a diferencia de
`quote`, que es 100% editorial manual sin fuente de mercado). Sigue el patrón "1 plantilla = 1
Change" ya fijado en Fase A/B: no reabre el motor, no reabre `quote`, solo agrega el tercer
snapshot + su `[tipo]` en `/story` + sus tests de mapeo.

## Contexto observado

**Motor (Fase A, ya en `master`, NO se toca en este Change)** — `scripts/story_render.py`:
viewport único `1920×1080`; `build_context` deriva tokens escalares dinámicamente de las
claves top-level del payload (no hay lista fija por plantilla); `resolver_loops`
(`<!-- FOR:clave -->`) para arrays — **no aplica a `breaking`**, que no tiene ningún campo
array según el catálogo; fences top-level (`_resolver_fences`) solo evalúan la tupla fija
`_FENCES = ("variacion", "vol", "chart_img", "chart_svg")` — los 4 nombres de Alerta, ninguno
aplica a `breaking`; orden canónico invariable: loops → fences → tokens → guardia
(`_validar_sin_huerfanos`).

**Precedente inmediato `quote` (Fase B, Change #121, ya cerrado)** — mismo patrón a replicar:
- Snapshot nuevo en `templates/stories/<tipo>.html`, reutilizando verbatim el andamiaje de
  marca de `alerta.html` (fuentes locales `templates/stories/fonts/*.woff2`: `syne-800`,
  `dm-sans-400`, `dm-sans-700`, `space-grotesk-600`; footer estándar `@grupointeligencia` +
  `grupointeligencia.com` + disclaimer CFD) sin chips/gráfico si la plantilla no los necesita.
  `quote.html` (leído íntegro) es el ejemplo más reciente y el molde más cercano a `breaking`:
  layout centrado, solo tokens escalares, sin fences ni loops, con un campo opcional
  (`autor_sub`) resuelto vía **token siempre presente + CSS `:empty { display:none }`** en vez
  de fence — patrón confirmado como la vía correcta para "campo opcional" en plantillas nuevas
  (NO tocar el motor para agregar el nombre a `_FENCES`).
- `.claude/commands/story.md` PASO 0 ya tiene la lista dura de `[tipo]` soportados
  (`alerta`, `quote`, líneas 6-8, 19-29) y ya demuestra el patrón de "Ruta `<tipo>`" — un
  bloque de recolección propio que reemplaza los PASO 1-N de `alerta` cuando el tipo no
  necesita niveles de mercado vía `get_asset_levels` (ver bloque "Ruta `quote`", líneas 40-104:
  preguntas de recolección → payload → preview/aprobación → render/guardado con
  `ruta_story.ps1 -Plantilla "<tipo>"`).
- `tests/test_story_render.py` ya tiene el patrón de tests de mapeo puros contra el snapshot
  real de `quote.html` (sin fixture nuevo, sin tocar `conftest.py`) — mismo patrón a replicar
  para `breaking.html`.
- `CLAUDE.md` sección "Stories GI" enumera los tipos soportados hoy (`alerta`, `quote`); si
  `breaking` se agrega, esa enumeración se actualiza en el mismo Change.

**Contrato de `breaking` (catálogo, fila 12 de
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`, línea 70; y
`docs/design/stories-gi/plantillas-stories-gi.md` no tiene aún una sección de mapeo dedicada
para `breaking` — solo existe la fila del catálogo, a diferencia de `alerta` que sí tiene su
mapeo campo-por-campo; ver "Preguntas abiertas")**:
- Campos del payload: `kicker_tema`, `titular`, `valor`, `contexto`, `parrafo_reaccion` — sin
  campos array, sin `chart_png`.
- Sin gráfico (columna "Gráfico" = "no").
- Fondo **oscuro/rojo** — misma familia visual que `alerta` (columna "Fondo" = "oscuro/rojo",
  igual codificación que Alerta), a diferencia de `quote` (oscuro sin rojo) y de `macro` (el
  único fondo claro del catálogo, fuera de esta Fase).
- Fuente de datos: **editorial**, criterio de `/noticia` · `/alerta` — es decir, esta plantilla
  SÍ nace de un evento/noticia real (a diferencia de `quote`, 100% manual sin fuente), pero NO
  delega en `get_asset_levels` ni en ningún dato numérico de mercado (a diferencia de `alerta`,
  que sí trae soporte/resistencia/precio del motor). El campo `valor` es la "cifra" editorial
  de la noticia (ej. un dato macro, un porcentaje, un nivel mencionado en la noticia), no un
  precio en vivo del motor.

**Convenciones duras que siguen aplicando sin cambios**:
- Regla "solo lectura" del canvas Claude Design compartido de GI (`CLAUDE.md` sección
  "Stories GI"): el snapshot `breaking.html` se autora en el repo, nunca se sincroniza
  automáticamente ni se sube nada hacia el canvas.
- `/story` no soporta el flag `ejecutivo` (`.claude/shared/modo_ejecutivo.md`, "No elegibles")
  — `breaking` no cambia esto.
- Flujo de aprobación: preview de texto antes de renderizar/guardar cualquier PNG (CB-3
  heredado).
- `scripts/ruta_story.ps1` ya acepta `-Plantilla` genérico — sin cambios necesarios.
- "1 plantilla = 1 Change": `breaking` no arrastra `encuesta` ni `edu` (las otras dos
  plantillas "Simples" de Fase B), cada una su propio Change/PR.

## Hipótesis de solución

Alcance 100% aditivo, sin tocar el motor (`scripts/story_render.py`) ni el contrato de `alerta`
o `quote`:

1. **`templates/stories/breaking.html`** (nuevo, snapshot 1920×1080): esqueleto GI equivalente
   al de `alerta.html`/`quote.html` (fuentes locales, footer estándar), con paleta
   oscura/rojiza reutilizando los acentos ya usados en `alerta.html` (`#0D0D1A` de fondo,
   `#E84040` de acento rojo — el mismo degradado rojizo que ya existe en `alerta.html:52-54` y
   que el prompt indica reutilizar). Cuerpo: `kicker_tema` (chip/etiqueta) + `titular` +
   `valor` (cifra destacada, tratamiento visual similar a `precio_actual`/`quote-texto` pero
   sin tarjeta de precio completa) + `contexto` + `parrafo_reaccion`. Sin gráfico, sin fences
   `IF`/`FOR` — todos los tokens escalares incondicionales (mismo criterio que `quote`,
   confirmado por la tupla fija `_FENCES` que no cubre ningún campo de `breaking`).
2. **`.claude/commands/story.md`**: agregar `breaking` a la lista dura de `[tipo]` en PASO 0
   (junto a `alerta`, `quote`) y un nuevo bloque "Ruta `breaking`" — recolección editorial con
   criterio de `/noticia`/`/alerta` (detecta o recibe el evento/cifra, redacta
   titular/contexto/reacción con dirección explícita y registro profesional del repo), sin
   llamar a `get_asset_levels`. Conserva el flujo preview → aprobación → render → guardado
   (`ruta_story.ps1 -Plantilla "breaking"`).
3. **`tests/test_story_render.py`**: tests de mapeo puros para `breaking.html`
   (`build_context`/`build_html` contra el snapshot real), análogos a los de `quote.html` —
   sin fixture nuevo, sin tocar `conftest.py`.
4. **`CLAUDE.md`**: actualizar la enumeración de `[tipo]` soportados en la sección "Stories GI"
   para incluir `breaking` (hoy enumera `alerta`, `quote` tras el merge de #122).
5. El motor y los contratos de `alerta`/`quote` **no se tocan** — Fase B solo agrega el tercer
   contrato de datos y snapshot, consumiendo el motor genérico tal cual quedó en Fase A.

## Preguntas abiertas

- ¿`breaking.html` necesita algún campo opcional (ej. `kicker_tema` ausente en breaking sin
  categoría clara, o un `valor` que no siempre aplique)? El catálogo lista los 5 campos como
  aparentemente obligatorios, pero conviene confirmar contra el criterio editorial de
  `/noticia`/`/alerta` si alguno puede venir vacío — de ser así, aplicar el patrón ya validado
  de `quote` (token siempre presente + `:empty` CSS), nunca una fence nueva en el motor.
- `docs/design/stories-gi/plantillas-stories-gi.md` no tiene todavía una sección de mapeo
  campo-por-campo dedicada a `breaking` (solo la fila del catálogo en el design doc de
  2026-07-14) — a diferencia de `alerta`, que sí tiene su mapeo documentado. Definir en Design
  si esta Fase agrega esa sección de documentación (mismo criterio que Fase A dejó para
  `alerta`) o si se considera fuera de alcance por ahora.
- ¿Cómo se distingue visualmente `valor` (la "cifra" de la noticia) de un precio de mercado,
  para que el layout no sugiera erróneamente que es un dato en vivo del motor (`breaking` no
  llama a `get_asset_levels`)? Definir en Design el tratamiento tipográfico/rotulado exacto.
- ¿El bloque "Ruta `breaking`" de `story.md` debe reusar el mismo mecanismo de detección de
  evento reciente que ya existe en `/alerta` PASO 1 / en el PASO 3 de la ruta `alerta` de
  `story.md` (WebSearch investing.com + fuentes oficiales), o el director puede dictar la
  noticia/cifra manualmente sin buscarla? El catálogo dice fuente `/noticia` · `/alerta` pero
  no aclara si `/story breaking` busca el evento por sí mismo o solo estructura lo que el
  director ya tiene.
- ¿`breaking` necesita guardarse con `-Activo` (si la noticia tiene un activo protagonista,
  como XAUUSD ante un dato de la Fed) o siempre bajo `_general` (como `quote`)? A diferencia de
  `quote` (100% sin activo), `breaking` puede nacer de una noticia con activo protagonista
  claro — definir el criterio de `ruta_story.ps1 -Activo` en Design.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), catálogo de las 12 plantillas; fila 12 `breaking` (línea 70): payload
  `kicker_tema, titular, valor, contexto, parrafo_reaccion`, sin gráfico, fondo oscuro/rojo,
  fuente `/noticia` · `/alerta`; plan de fases (línea 91: Fase B = simples `quote`, `breaking`,
  `encuesta`, `edu`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — sistema visual GI (manual de marca,
  esqueleto de chips/footer); no tiene aún sección dedicada a `breaking` (ver "Preguntas
  abiertas").
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; contiene los contratos ya formalizados
  de `story_alerta` (Change #109/#119) y `story_quote` (Change #121) como precedente directo de
  formato a replicar para `story_breaking`.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/idea.md`,
  `proposal.md`, `design.md` — Change antecedente inmediato (misma Fase B): confirma el patrón
  "1 snapshot + 1 bloque de recolección en `story.md` + tests de mapeo puros + actualización de
  `CLAUDE.md`", el patrón de campo opcional (token + `:empty`) y la convención "1 plantilla = 1
  Change".
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/`
  — Change fundacional: generalización del motor (decisiones R1-R8 heredadas), no se reabre.
- `scripts/story_render.py` — motor 16:9 ya generalizado, **no se modifica** en este Change.
- `templates/stories/alerta.html` — referencia de paleta oscura/rojiza (`#0D0D1A`, `#E84040`,
  degradado radial líneas 52-54) que `breaking` reutiliza.
- `templates/stories/quote.html` — patrón más reciente de plantilla simple sin fences/loops,
  con campo opcional resuelto vía `:empty` CSS; molde más cercano a `breaking`.
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `breaking` a `[tipo]`
  junto a `alerta`, `quote`; nuevo bloque "Ruta `breaking`" análogo a "Ruta `quote`", líneas
  40-104).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para `breaking`.
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de tipos soportados.
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin cambios
  esperados en esta Fase).
- Issue #123 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B ·
  `breaking`; issues #121 (quote, precedente cerrado) y #119 (motor, fundacional).
