# Proposal: Stories GI · Fase A — motor de render 16:9 + migrar plantilla Alerta

## Problema

El motor de Stories GI (`scripts/story_render.py`, issue #109) nació para **un solo
formato** (vertical 9:16, 1080×1920) y **una sola plantilla** (Alerta), con listas de
campos codificadas a mano en el propio motor:

- `render_png` abre la página con `viewport={"width": 1080, "height": 1920}`
  hardcodeado (línea ~206), sin parámetro para cambiarlo.
- `_TOKENS_ESCALARES` (línea ~33) es una tupla fija de 12 nombres específicos del
  contrato `story_alerta` (`chip_categoria`, `titular`, `rotulo_activo`, `tag_riesgo`,
  `soporte`, `resistencia`, …). `build_context` itera esa tupla literal — no las claves
  del payload — y **lanza error si falta cualquiera** de esos 12 campos, aunque la
  plantilla que se esté renderizando no los use.
- `_FENCES` (línea ~29) es una tupla fija de 4 nombres (`variacion`, `vol`,
  `chart_img`, `chart_svg`) resuelta por un `if/elif` hardcodeado en `_fence_presente`
  — agregar una plantilla con fences distintos obliga a tocar esa función.
- No existe ningún mecanismo de repetición: el catálogo de las 12 plantillas
  aprobadas (spec PR #118) incluye varias con arrays (`filas[]` en Flash y
  Calendario, `ganadores[]`/`perdedores[]` en el cierre semanal, `bullets[]` en el
  concepto educativo) que el motor actual no puede expresar.

El director quiere producir contenido visual de marca GI en **16:9 (1920×1080)** para
el equipo de ejecutivos, cubriendo las 12 plantillas del canvas maestro de GI. Sin
generalizar primero el motor, cada plantilla nueva forzaría a duplicar o parchear
`story_render.py` ad hoc, acumulando deuda y arriesgando romper Alerta (el único caso
en producción hoy). Esta Fase A (issue #119) es el **cambio arquitectónico base** —
sin él, ninguna de las 11 plantillas restantes (Fases B/C/D) puede empezar.

## Contexto observado

**Motor actual** (`scripts/story_render.py`, 259 líneas):
- Pipeline puro y ya bien separado: `build_context(payload)` → `build_html(payload,
  template_path)` (fences → tokens → guardia `_validar_sin_huerfanos`) →
  `render_png(html, out, template_dir)` con import perezoso de Playwright. Este
  patrón se conserva; el cambio es *qué* recorre `build_context`/`_resolver_fences`,
  no la forma del pipeline.
- `render_story` es el orquestador público (`build_html` + `render_png`); el CLI
  (`main`) recibe el payload por stdin y `--template`/`--out` — sin cambios de
  interfaz previstos.
- Derivaciones especiales ya existen inline en `build_context`: `variacion_flecha`
  (▲/▼ según `variacion.direccion`), `sesgo_slug` (prioriza `variacion.direccion`,
  cae a `sesgo`), `chart_src` (URI `file:///` con verificación de existencia — CB-8,
  nunca renderiza con imagen rota).

**Snapshot de marca** (`templates/stories/alerta.html`):
- HTML+CSS estático, 1080×1920 hardcodeado en `html, body { width: 1080px; height:
  1920px; ... }` y `.story { width: 1080px; height: 1920px; ... }`, con fuentes
  locales (`templates/stories/fonts/*.woff2`: Syne 800, DM Sans 400/700, Space
  Grotesk 600) y un SVG decorativo de velas como fallback cuando no hay
  `chart_png`. El comentario de cabecera ya advierte: "NO cambiar nombres [de
  tokens/fences] sin actualizar `scripts/story_render.py` y
  `tests/test_story_render.py`".

**Comando** (`.claude/commands/story.md`): PASO 0 valida `[tipo]` == `alerta`
(único soportado); el resto (PASOS 1-7) ya sigue el patrón de recolección → preview
→ aprobación → render vía `ruta_story.ps1` + `story_render.py` que las 12 plantillas
reutilizarán sin cambios de forma.

**Tests** (`tests/test_story_render.py`, 177 líneas): cubren `build_html` contra un
`fixture_template.html` minimalista (aísla el motor del snapshot real) y contra
`alerta.html` real; validan fences ausentes/presentes, guardia de huérfanos, chart
embebido con URI `file:///`, y un test de render (`skipif` sin Chromium) que
verifica dimensiones exactas **1080×1920** vía el chunk IHDR del PNG (sin Pillow) —
este assert deberá pasar a **1920×1080**.

**Spec canónica aprobada** (PR #118,
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`): fija la
tabla comparativa "hoy vs. generalizado" (viewport, tokens, fences, `FOR`,
derivaciones), el catálogo completo de las 12 plantillas con campos/gráfico/fondo/
fuente de datos, el plan de fases A→D por complejidad creciente, y la decisión ya
tomada de que el layout 16:9 de Alerta **se autora en el repo** (no se sincroniza
del canvas). El orden canónico ya decidido para `build_html` es **loops → fences →
tokens → guardia**.

**Mapeo campo-por-campo** (`docs/design/stories-gi/plantillas-stories-gi.md`):
confirma que el canvas de GI no tiene tokens de contenido (todo texto es ejemplo
estático) — los placeholders `{{...}}` los define este repo al escribir cada
snapshot.

**Precedente heredado, no reinventado** (Change #109 archivado):
`.pulse/changes/archive/109-.../design.md` documenta las decisiones D1-D7 que esta
Fase A extiende: mecanismo de inyección (tokens + fences, stdlib `re`/`str`, sin
Jinja2 por choque de `{}` con el CSS embebido), estructura del motor, invocación
desde `story.md`, patrón de testing (mapeo puro + render `skipif`).
`.pulse/specs/stories-gi/spec.md` conserva el contrato `story_alerta` original
(R1-R10, CB-1..CB-8, AC1-AC9) que esta Fase migra de layout/viewport sin reabrir el
contrato de datos.

**Convenciones duras sin cambios**: regla "solo lectura" del canvas compartido
(`CLAUDE.md` § Stories GI); flujo de aprobación (preview de texto antes de
renderizar/guardar cualquier PNG); `/story` no soporta el flag `ejecutivo` (mismo
criterio que `/chart`, listado en `.claude/shared/modo_ejecutivo.md` bajo "No
elegibles"); reglas transversales de marca (decimales por `digits`, hora Chile,
dirección explícita, registro profesional sin dramatización).

**Estado del working tree**: rama `feat/119-stories-gi-motor-16-9`. Hay 6 archivos
modificados sin commitear, **ajenos a este Change y fuera de alcance**
(`.claude/commands/apertura.md`, `data/glosario_siglas.json`,
`data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
`templates/encuesta_tendencia.txt`, `uv.lock`) — no tocar. Todavía no hay ningún
cambio de código propio de esta Fase A.

## Hipótesis de solución

Generalizar `scripts/story_render.py` conservando su forma actual (funciones puras
+ `render_png` con Playwright perezoso), usando la migración de Alerta a 16:9 como
caso de prueba end-to-end de la generalización — no se reabre su contrato de datos,
solo layout y viewport:

1. **Viewport**: `render_png` pasa de `1080×1920` a **`1920×1080`** como único
   default del motor (se abandona 9:16 por completo, decisión ya tomada en la spec
   — sin modo dual ni parámetro de tamaño).
2. **Tokens escalares dinámicos**: reemplazar la iteración sobre `_TOKENS_ESCALARES`
   (tupla fija, obligatoria) por un recorrido de las claves escalares del payload
   (valores no-`dict`/no-`list`), inyectando `{{clave}}` por cada una que la
   plantilla use. Las derivaciones especiales existentes (`variacion_flecha`,
   `sesgo_slug`, `chart_src`) se conservan como helpers puros, ahora disparados por
   un conjunto (más chico) de nombres de clave conocidos, ya no acoplados a que
   esas sean *las únicas* claves del payload.
3. **`resolver_loops` (nuevo)**: función que expande bloques
   `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` repitiendo el contenido interno una
   vez por objeto de `payload[clave]` (array), resolviendo los tokens propios de
   cada objeto dentro de su propia iteración. Se ejecuta **antes** de fences —
   orden canónico ya fijado por la spec: **loops → fences → tokens → guardia**.
4. **Fences y guardia**: `_resolver_fences`/`_fence_presente` y
   `_validar_sin_huerfanos` se conservan tal cual en su lógica; solo cambia su
   posición relativa a `resolver_loops` dentro de `build_html`.
5. **Migrar `templates/stories/alerta.html`** a un rediseño horizontal 1920×1080
   que conserve el sistema visual GI (colores, tipografías, footer) y **los mismos
   nombres de tokens/fences** del contrato `story_alerta` vigente. Sirve como
   validador de que el motor generalizado sigue produciendo el mismo resultado
   observable para el caso conocido, sin tocar `spec.md`/el contrato de datos de
   Alerta.
6. **Sincronizar** `.claude/commands/story.md` (PASO 0 y menciones de tamaño),
   `CLAUDE.md` § "Stories GI" (→ 1920×1080) y, donde corresponda,
   `docs/design/stories-gi/plantillas-stories-gi.md`.
7. **Tests**: adaptar `tests/test_story_render.py` a tokens dinámicos (incluida la
   aserción de dimensiones, que pasa a `(1920, 1080)`); agregar tests puros nuevos
   de `resolver_loops` (array vacío, 1 elemento, N elementos); mantener el patrón
   mapeo-puro + render-`skipif`.
8. El contrato de payload específico de las 11 plantillas restantes **no se
   aborda** en esta Fase — queda para Fases B/C/D, cada una su propio Change
   pequeño, según ya está decidido en la spec de referencia (PR #118).

## Preguntas abiertas

- **Alcance de "tokens dinámicos"**: ¿`build_context` recorre *todas* las claves
  escalares top-level del payload y las expone como candidatas a `{{token}}`
  (ignorando en silencio las que el HTML no use), o solo materializa las que
  aparecen literalmente en la plantilla? ¿Una clave del payload que el HTML no usa
  es un no-op o debería advertirse? Define el diseño de `build_context` y sus
  tests — a resolver en `specify`.
- **Lista de "nombres especiales" con lógica propia**: hoy son 3 (`variacion` →
  flecha, `sesgo`/`variacion.direccion` → slug de color, `chart_png` → `chart_src`).
  El catálogo de las 12 plantillas menciona además `impacto` (badge ALTO/MEDIO,
  plantilla `calendario`) y posiblemente `direccion` a secas (sin envolver en
  `variacion`, en plantillas fuera de Alerta). ¿Se fija ya en esta Fase la lista
  cerrada de helpers reutilizables con sus nombres de disparo, aunque solo
  `variacion`/`sesgo`/`chart_png` tengan consumidor real en Alerta, o se agregan
  helpers nuevos recién cuando su plantilla (Fase B/C/D) los necesite?
- **Anidamiento de `resolver_loops`**: ¿un solo nivel alcanza (el catálogo con
  listas — Flash, Calendario, cierre semanal, Earnings — no parece necesitar `FOR`
  dentro de `FOR`), y se documenta explícitamente como fuera de alcance el
  anidamiento, o el diseño debe dejar la puerta abierta sin implementarlo?
- **Array vacío en un `FOR`**: si `payload[clave]` es `[]`, ¿el bloque completo
  desaparece (mismo comportamiento que una fence ausente, sin contenedor/header
  visible) o se renderiza el contenedor vacío (headers de tabla sin filas)? Esto
  condiciona los acceptance criteria de test y debe quedar explícito en `specify`.
- **Aspect ratio del chart embebido**: `chart_png` (fence `chart_img`/`chart_svg`)
  ¿mantiene el mismo contrato de imagen que hoy, o el rediseño horizontal de
  Alerta 16:9 espera un PNG de `/chart` con proporción distinta a la usada en el
  layout vertical actual? Si cambia, ¿quién recorta/ajusta el PNG — el comando
  `story.md` o el CSS del snapshot vía `object-fit`?
- **Estrategia de migración de tests**: ¿se reescriben in-place
  `test_build_html_contract`/`test_render_dimensiones_1080x1920` (y el resto de la
  suite) para reflejar 1920×1080 + tokens dinámicos, o conviven versiones
  paralelas durante la transición? ¿`fixture_template.html` (usado para aislar el
  motor del snapshot real) también pasa a 16:9, o el motor es agnóstico al tamaño
  para los tests puros (dado que `build_html` no depende del viewport, solo
  `render_png` lo usa)?
- **Alcance exacto de "sincronizar docs"**: además de `story.md` y `CLAUDE.md`,
  ¿hay que tocar la intro de `docs/design/stories-gi/plantillas-stories-gi.md`
  (menciona "1080×1920") u otros docs/README con referencias al formato anterior?
- **`scripts/ruta_story.ps1`**: la spec dice que no necesita cambios (ya es
  agnóstico a tamaño/aspecto, solo arma la ruta por fecha/activo/plantilla/hora).
  ¿Confirmar en `specify` que no hace falta ningún ajuste, o hay algún caso borde
  (ej. nombre de archivo que insinúe el aspect ratio) que sí lo requiera?

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` —
  spec/diseño aprobado (PR #118), fuente canónica del alcance de esta Fase A
  (tabla comparativa, catálogo de 12 plantillas, plan de fases A→D, orden canónico
  `build_html`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — mapeo campo-por-campo,
  catálogo de las 12 plantillas, roadmap por issues (#109-#115).
- `.pulse/specs/stories-gi/spec.md` — spec del dominio heredada del Change #109
  (contrato `story_alerta` original: R1-R10, CB-1..CB-8, AC1-AC9), no se reabre en
  esta Fase.
- `.pulse/changes/archive/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/design.md`
  — decisiones D1-D7 heredadas (mecanismo de inyección, estructura de
  `story_render.py`).
- `.pulse/heuristics/stories-gi.md` — heurística de cierre del Change #109.
- `scripts/story_render.py` — motor actual a generalizar (`_TOKENS_ESCALARES`
  línea ~33, `_FENCES` línea ~29, viewport hardcodeado línea ~206).
- `templates/stories/alerta.html` + `templates/stories/fonts/` — snapshot 9:16 a
  migrar a 16:9.
- `.claude/commands/story.md` — comando a sincronizar (PASO 0: tipo único
  `alerta`, tamaño mencionado en la descripción).
- `CLAUDE.md` sección "Stories GI" — a actualizar (1920×1080).
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin
  cambios esperados en esta Fase).
- `tests/test_story_render.py` + `tests/fixtures/stories/` — suite a extender
  (incluye assert de dimensiones `(1080, 1920)` → `(1920, 1080)`).
- `scripts/ruta_story.ps1` — helper de guardado (ya soporta `-Plantilla`, sin
  cambios previstos).
- `.pulse/changes/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/idea.md`
  — idea-doc de la fase Explore de este mismo Change (base de esta propuesta).
- Issue #119 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta
  Fase A.
