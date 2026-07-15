# Idea: Stories GI · Fase A — motor de render 16:9 + migrar plantilla Alerta

## Problema

Hoy el motor de Stories GI (`scripts/story_render.py` + `templates/stories/alerta.html`,
issue #109) está atado a **un solo formato** (vertical 9:16, 1080×1920) y a **una sola
plantilla** (Alerta), con una lista fija de tokens escalares (`_TOKENS_ESCALARES`) y un
conjunto fijo de fences (`_FENCES`) codificados a mano para el contrato de payload de
Alerta. No existe ningún mecanismo para repetir bloques a partir de un array del payload
(filas de una tabla, lista de ganadores/perdedores, bullets), porque Alerta no lo necesita.

El director quiere producir **contenido visual de marca GI en 16:9 (1920×1080)** para el
equipo de ejecutivos (presentaciones, pantallas, feed interno), cubriendo las **12
plantillas** del canvas maestro compartido de GI (issues #111-#115 + esta Fase A). Para que
eso sea viable sin duplicar o parchear el renderer en cada plantilla nueva, primero hace
falta **generalizar el motor**: viewport 16:9, tokens derivados dinámicamente del payload
(no una lista fija por plantilla), un mecanismo nuevo de repetición (`<!-- FOR -->`) y
helpers de derivación reutilizables (flecha ▲/▼, color por dirección/sesgo, badge de
impacto) en vez de lógica inline dispersa.

Esta Fase A (issue #119) es el **cambio arquitectónico base** del que dependen las Fases
B/C/D (11 plantillas restantes, cada una su propio Change). Se valida generalizando el
motor y usando la migración de Alerta a 16:9 como plantilla end-to-end de esa
generalización — sin este Change, ninguna plantilla nueva puede empezar.

## Contexto observado

**Estado actual del motor** (`scripts/story_render.py`):
- `render_png` abre la página con `viewport={"width": 1080, "height": 1920}` hardcodeado
  (línea ~206) — no hay parámetro para cambiarlo.
- `_TOKENS_ESCALARES` es una tupla fija de 12 nombres de campo, todos específicos del
  contrato `story_alerta` (`chip_categoria`, `titular`, `rotulo_activo`, `tag_riesgo`,
  `soporte`, `resistencia`, etc.). `build_context` itera esa tupla literal, no las claves
  del payload.
- `_FENCES` es una tupla fija de 4 nombres (`variacion`, `vol`, `chart_img`, `chart_svg`) y
  `_fence_presente` tiene un `if/elif` hardcodeado por nombre — agregar una plantilla nueva
  con fences distintos requeriría tocar esta función.
- No existe `resolver_loops` ni ningún mecanismo `<!-- FOR -->`/`<!-- ENDFOR -->`: el orden
  actual de `build_html` es solo fences → tokens → guardia (`_validar_sin_huerfanos`).
- `templates/stories/alerta.html` es un snapshot estático 1080×1920 con CSS embebido,
  fuentes locales (`templates/stories/fonts/*.woff2`: Syne 800, DM Sans 400/700, Space
  Grotesk 600) y un SVG decorativo de velas como fallback cuando no hay `chart_png`.
- `.claude/commands/story.md` valida `[tipo]` == `alerta` (único soportado, PASO 0);
  menciona el flujo completo R1-R7 de la spec original (`/story alerta ejecutivo` → avisa y
  continúa sin flag, igual que `/chart`).
- `tests/test_story_render.py` cubre `build_html` puro contra un `fixture_template.html`
  minimalista (aísla el motor del snapshot de marca) y contra el `alerta.html` real, más un
  test de render con `@pytest.mark.skipif` cuando no hay Chromium instalado
  (`_chromium_disponible()`); valida dimensiones exactas vía IHDR del PNG (sin Pillow).
- `scripts/ruta_story.ps1` (hermano de `ruta_mensaje.ps1`, #45) ya acepta `-Plantilla` como
  parámetro genérico — no está atado a `alerta` y no debería necesitar cambios para 16:9.
- `pyproject.toml` tiene `playwright` como dependencia opcional
  (`[project.optional-dependencies] stories`), fuera de `[project.dependencies]` — patrón a
  conservar.

**Spec de referencia aprobada (fuente canónica de esta Fase A, PR #118)**:
`docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` fija, entre otras
cosas: la tabla comparativa "hoy vs. generalizado" (viewport, tokens, fences, `FOR`,
derivaciones, snapshots, contrato de payload); el catálogo completo de las 12 plantillas con
sus campos, si llevan gráfico, color de fondo y fuente de datos en el repo; el plan de fases
A→D por complejidad creciente (A: motor + Alerta; B: simples sin gráfico/listas; C: con
`FOR`; D: con gráfico embebido); y la decisión ya tomada de que **el layout 16:9 de Alerta
se autora en el repo** (no se sincroniza del canvas).

**Mapeo campo-por-campo**: `docs/design/stories-gi/plantillas-stories-gi.md` confirma que el
canvas real de GI **no tiene tokens de contenido** (todo el texto es ejemplo estático) — los
placeholders `{{...}}` los define este repo al escribir cada snapshot. También documenta el
roadmap de piezas verificadas (01 Market Update, 02 Indicador Macro, 03 Alerta, 04 Trading
Idea, 06 Calendario, Carrusel 4 slides) — 05 Reporte Flash queda fuera del proyecto ajeno
`flash_mcp` y se re-implementa con datos propios del repo (`get_asset_levels` multi-activo).

**Precedente directo (Change #109, ya archivado y mergeado)**:
`.pulse/changes/archive/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/design.md`
documenta las decisiones D1-D7 que esta Fase A hereda y extiende, no reinventa: mecanismo de
inyección (tokens `{{campo}}` + fences `<!-- IF -->`, stdlib `re`/`str`, sin Jinja2 por
choque con `{}` del CSS embebido), estructura de `story_render.py` (`build_context` →
`build_html` puro → `render_png` con Playwright perezoso → `render_story` orquestador →
CLI), invocación desde `story.md` (payload por stdin, `--template`/`--out`), y el patrón de
testing (mapeo puro + render `skipif`). `.pulse/specs/stories-gi/spec.md` conserva el
contrato de payload `story_alerta` original (R1-R10, CB-1..CB-8, AC1-AC9) tal como quedó
para el piloto 9:16.

**Convenciones duras del repo que siguen aplicando sin cambios**:
- Regla "solo lectura" del canvas Claude Design compartido (`CLAUDE.md` sección "Stories
  GI"): nunca se sube nada del repo hacia allá; el render final se produce y aprueba
  siempre localmente.
- Flujo de aprobación: preview en texto antes de renderizar/guardar cualquier PNG (nunca se
  genera sin aprobación explícita del director).
- `/story` no soporta el flag `ejecutivo` (mismo criterio que `/chart`: genera imagen, no
  mensaje de cliente reenviable) — está listado en `.claude/shared/modo_ejecutivo.md` bajo
  "No elegibles".
- Reglas transversales de marca (`CLAUDE.md`): decimales por `digits` de
  `config/activos.json`, hora Chile, dirección explícita (regla de oro), registro
  profesional sin dramatización.

**Estado del working tree**: rama `feat/119-stories-gi-motor-16-9`. Hay 6 archivos
modificados sin commitear, ajenos a este Change (`.claude/commands/apertura.md`,
`data/glosario_siglas.json`, `data/historial_encuestas.json`,
`templates/encuesta_posicion.txt`, `templates/encuesta_tendencia.txt`, `uv.lock`) — no
tocar. Aún no hay ningún cambio de código para el issue #119 (`git diff master --stat` solo
muestra esos 6 archivos ajenos).

## Hipótesis de solución

Generalizar `scripts/story_render.py` conservando su forma actual (funciones puras +
`render_png` con Playwright perezoso) y usando la migración de Alerta como caso de prueba
end-to-end:

1. **Viewport**: cambiar `render_png` de `1080×1920` a `1920×1080` como nuevo default del
   motor (se abandona 9:16 por completo, según decisión ya tomada — no hace falta un modo
   dual ni parámetro de tamaño).
2. **Tokens escalares dinámicos**: reemplazar la iteración sobre `_TOKENS_ESCALARES` (lista
   fija) por un recorrido de las claves escalares del payload (valores no-`dict`/no-`list`),
   generando `{{token}}` para cada una. Las derivaciones especiales (`variacion_flecha`,
   `sesgo_slug`/color, badge de impacto) se mantienen como helpers puros invocados cuando el
   motor detecta las claves conocidas que las disparan (`variacion.direccion`, `sesgo`,
   `impacto`), igual que hoy pero ya no atado a que esas claves sean *las únicas* del
   payload.
3. **`resolver_loops` (nuevo)**: función que expande bloques
   `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` repitiendo el contenido interno una vez por
   objeto de `payload[clave]` (array), resolviendo los tokens propios de cada objeto dentro
   de su iteración. Se ejecuta **antes** de fences (orden canónico fijado por la spec:
   loops → fences → tokens → guardia).
4. **Fences y guardia**: se conservan tal cual (`_resolver_fences`, `_validar_sin_huerfanos`)
   — solo cambia su posición relativa a `resolver_loops` en `build_html`.
5. **Migrar `templates/stories/alerta.html`** a un rediseño horizontal 1920×1080 que
   conserve el sistema visual GI (colores, tipografías, footer estándar) y **los mismos
   nombres de tokens/fences** del contrato `story_alerta` actual (no se reabre el contrato
   de datos en esta Fase, solo el layout y el viewport). Sirve como validador de que el
   motor generalizado sigue produciendo el mismo resultado observable para el caso conocido.
6. **Sincronizar** `.claude/commands/story.md`, `CLAUDE.md` (sección "Stories GI" →
   1920×1080) y `docs/design/stories-gi/plantillas-stories-gi.md` donde corresponda.
7. **Tests**: adaptar `tests/test_story_render.py` a los tokens dinámicos; agregar tests
   puros de `resolver_loops` (array vacío, 1 elemento, N elementos); mantener el test de
   render con `skipif` sin Chromium, ahora verificando IHDR 1920×1080.
8. El contrato de payload específico de las 11 plantillas restantes **no se aborda** en esta
   Fase — eso es Fase B/C/D, cada una su propio Change pequeño, según ya está decidido en la
   spec de referencia.

## Preguntas abiertas

- ¿Los "tokens escalares dinámicos" recorren *todas* las claves escalares top-level del
  payload, o solo las que efectivamente aparecen como `{{token}}` en el HTML de la
  plantilla? ¿Qué pasa si el payload trae una clave que el HTML no usa: se ignora en
  silencio, o es un error? (Afecta el diseño de `build_context` y sus tests.)
- Los "helpers de derivación reutilizables" (flecha, color, badge) siguen disparándose por
  nombres de clave conocidos (`direccion`, `impacto`, `sesgo`), igual que hoy. ¿Confirmar que
  esto no contradice el objetivo de "generalizar" — es decir, generalizar significa que el
  motor ya no asume que *solo* existen los campos de Alerta, pero sigue teniendo una lista
  fija (más chica) de nombres especiales con lógica propia?
- ¿`resolver_loops` soporta anidamiento (`FOR` dentro de `FOR`) o alcanza con un solo nivel?
  El catálogo de plantillas con listas (`flash`, `calendario`, `semanal`, `earnings`) parece
  necesitar solo un nivel — ¿se puede confirmar y dejarlo fuera de alcance explícitamente si
  no se necesita en Fase A/B/C?
- Si `payload[clave]` de un `FOR` es un array vacío, ¿el bloque completo desaparece (se
  comporta como una fence ausente) o se renderiza vacío (sin iteraciones, pero deja
  contenedores/headers)? Necesita definirse explícitamente porque condiciona los AC de test.
- ¿El chart embebido (`chart_png`, fence `chart_img`/`chart_svg`) mantiene el mismo
  contrato, o el rediseño horizontal de Alerta cambia el aspect ratio esperado del PNG
  embebido (el chart de `/chart` se genera hoy pensando en un layout vertical)?
- ¿Se reescriben in-place los tests de mapeo existentes (`test_build_html_contract`, etc.)
  para reflejar 1920×1080 y tokens dinámicos, o se agregan tests nuevos en paralelo durante
  la transición? ¿El `fixture_template.html` también pasa a 16:9, o el motor es agnóstico al
  tamaño para los tests puros (dado que `build_html` no depende del viewport)?
- Alcance exacto de "sincronizar docs": ¿además de `story.md` y `CLAUDE.md`, hay que tocar
  `docs/design/stories-gi/plantillas-stories-gi.md` (menciona "1080×1920" en su intro) u
  otros docs/README?
- ¿Hace falta algún ajuste en `scripts/ruta_story.ps1` por el cambio de formato, o queda
  igual (la spec de referencia dice "sin cambios" porque el helper ya es agnóstico al
  tamaño/aspecto de la imagen)?

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), fuente canónica del alcance de esta Fase A.
- `docs/design/stories-gi/plantillas-stories-gi.md` — mapeo campo-por-campo, catálogo de las
  12 plantillas, roadmap por issues (#109-#115).
- `.pulse/specs/stories-gi/spec.md` — spec del dominio heredada del Change #109 (contrato
  `story_alerta` original: R1-R10, CB-1..CB-8, AC1-AC9).
- `.pulse/changes/archive/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/design.md`
  — decisiones D1-D7 heredadas (mecanismo de inyección, estructura de `story_render.py`).
- `.pulse/heuristics/stories-gi.md` — heurística de cierre del Change #109.
- `scripts/story_render.py` — motor actual a generalizar.
- `templates/stories/alerta.html` + `templates/stories/fonts/` — snapshot 9:16 a migrar.
- `.claude/commands/story.md` — comando a sincronizar (viewport, tipo único `alerta`).
- `CLAUDE.md` sección "Stories GI" — a actualizar (1920×1080).
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles" (sin cambios
  esperados en esta Fase).
- `tests/test_story_render.py` + `tests/fixtures/stories/` — suite a extender.
- `scripts/ruta_story.ps1` — helper de guardado (ya soporta `-Plantilla`).
- Issue #119 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase A.
