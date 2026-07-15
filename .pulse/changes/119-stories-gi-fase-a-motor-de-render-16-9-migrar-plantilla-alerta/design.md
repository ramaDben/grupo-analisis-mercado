# Design — Stories GI · Fase A: motor de render 16:9 + migrar plantilla Alerta (#119)

> Diseño técnico de `spec.md` (Change #119, dominio `stories-gi`). Implementa exactamente
> R1-R8, CB-1..CB-7 y AC1-AC12. **Hereda** el precedente #109 (D1-D7,
> `.pulse/changes/archive/109-.../design.md`) y su contrato de datos `story_alerta`
> (`.pulse/specs/stories-gi/spec.md`) — no lo reabre; solo generaliza el motor y migra
> layout/viewport. Fuente canónica del alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (PR #118). **No contiene código de aplicación** — solo el plan técnico + desglose de tareas.

## Nota sobre invariantes de arquitectura

Este Change **no toca ninguna capa hexagonal**. El repo no tiene un `src/pulse/` ni un paquete
de dominio afectado: el MCP `src/market_data_mcp/` queda intacto. El código a generalizar es un
utilitario de nivel `scripts/` (`story_render.py`, fuera de ruff/ty por #79, cubierto por
`pytest` — igual que `senal_manager.py`), un snapshot HTML+CSS (`templates/stories/alerta.html`),
tests (`tests/test_story_render.py`) y documentación (`CLAUDE.md`, `story.md`,
`plantillas-stories-gi.md`). `story_render.py` sigue siendo un **motor "tonto"** sin lógica de
negocio (payload → HTML → PNG); la recolección editorial/numérica vive en el prompt
`.claude/commands/story.md`. **No se agregan dependencias**: sigue con `re`/`json`/`argparse`/
`pathlib`/`tempfile` de la stdlib + Playwright con import perezoso (dependencia opcional
`[project.optional-dependencies] stories`, sin cambios). La dirección de dependencia
(prompt → script puro → Playwright perezoso) se conserva.

---

## Technical Approach

### 0. Vista de conjunto — el pipeline `build_html` reordenado

El pipeline actual (`scripts/story_render.py:153-165`) es `fences → tokens → guardia`. Se
reordena al orden canónico **loops → fences → tokens → guardia** insertando `resolver_loops`
como primera fase, sin cambiar la forma del pipeline ni la interfaz pública:

```
build_html(payload, template_path) -> str          (PURO — objeto de AC2/AC3/AC7/AC8/AC9)
   html      = read_text(template_path)
   contexto  = build_context(payload)               # R2/R3/R5 — dict plano de tokens escalares
   html      = resolver_loops(html, payload)         # R4  (NUEVO)  <-- fase 1
   html      = _resolver_fences(html, payload)        # sin cambios  <-- fase 2
   html      = _sustituir_tokens(html, contexto)      # sin cambios  <-- fase 3
   _validar_sin_huerfanos(html)                       # sin cambios  <-- fase 4 (gate de huérfanos)
   return html

render_png(html, out, *, template_dir) -> Path        (Playwright headless)
   viewport = {"width": 1920, "height": 1080}          # R1  (era 1080×1920)
```

Firmas y responsabilidad de cada pieza:

| Función | Firma | Responsabilidad | Cambio en Fase A |
|---|---|---|---|
| `build_context` | `(payload: dict[str, Any]) -> dict[str, str]` | Deriva el dict plano `{token: valor_str}`: recorre escalares top-level + aplica el catálogo cerrado de 4 helpers | **Reescrita internamente** (R2/R3/R5); firma intacta |
| `resolver_loops` | `(html: str, payload: dict[str, Any]) -> str` | Expande cada bloque `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` (R4) | **Nueva** (pública: la testean AC4-6 directamente) |
| `_resolver_fences` | `(html: str, payload: dict[str, Any]) -> str` | Conserva/elimina cada fence top-level según `_fence_presente` | **Sin cambios** de lógica; solo baja de posición |
| `_fence_presente` | `(nombre: str, payload: dict) -> bool` | Regla de presencia de los 4 fences de Alerta (`variacion`/`vol`/`chart_img`/`chart_svg`) | **Sin cambios** (Riesgo C: mitigación por docstring, ver §5) |
| `_sustituir_tokens` | `(html: str, contexto: dict[str, str]) -> str` | `str.replace("{{tok}}", valor)` por cada token del contexto | **Sin cambios** |
| `_validar_sin_huerfanos` | `(html: str) -> None` | Gate: cualquier `{{token}}` restante → `StoryRenderError` listando los huérfanos | **Sin cambios** — es el gate genérico de R2/R3/CB-2 |
| `render_png` | `(html, output_path, *, template_dir) -> Path` | HTML resuelto → PNG con Playwright | **Solo el viewport** (R1) |
| `render_story` / `main` | (sin cambios) | Orquestador público + CLI (payload por stdin, `--template`/`--out`) | **Sin cambios de interfaz** |

Se **elimina** la tupla fija `_TOKENS_ESCALARES` (`story_render.py:33-46`). `_FENCES`
(`story_render.py:29`) se **conserva** (sigue gobernando los 4 fences top-level de Alerta).

### 1. `build_context` — tokens escalares dinámicos (R2/R3) + helpers (R5)

`build_context` deja de iterar la tupla fija y pasa a dos etapas:

**Etapa A — recorrido dinámico de escalares top-level (R2/R3).** Recorre `payload.items()` y,
por cada clave cuyo valor **no** es `dict` ni `list`, agrega `contexto[clave] = str(valor)`.
`None`, `bool` y números se convierten con `str()` tal cual manda R2 (p.ej. `chart_png: None`
→ `contexto["chart_png"] = "None"`). No hay noción de "campo obligatorio": si una clave del
payload no aparece como `{{clave}}` en el HTML, simplemente no encuentra ocurrencia que sustituir
(no-op silencioso, R3/CB-1); si un `{{token}}` del HTML no tiene origen ni en escalares ni en
helpers, cae en la guardia (R2/CB-2). `build_context` **nunca** valida "¿esta clave se usa?" —
solo la guardia valida la dirección opuesta ("¿quedó algún `{{token}}` sin resolver?").

**Etapa B — catálogo cerrado de 4 helpers de derivación (R5).** Tras poblar los escalares, se
aplican, cada uno disparado por su clave conocida:

| # | Helper | Disparo | Deriva (token → valor) | Punto de invocación | Consumidor real en Alerta |
|---|---|---|---|---|---|
| 1 | **Flecha de dirección** | clave top-level cuyo valor es un `dict` con `direccion` (ej. `variacion`) | `{contenedor}_flecha` = `▲` (`alcista`) / `▼` (`bajista`) / `""` (otro) **y** aplana los escalares del objeto a `{contenedor}_{sub}` (→ `variacion_pct`, `variacion_direccion`) | tras Etapa A | `variacion_flecha` + `variacion_pct` |
| 2 | **Slug de color direccional** | `variacion.direccion` (prioridad) → si no, `sesgo` | `sesgo_slug` = `str(direccion o sesgo).lower()` (clase CSS: verde `#00DC82` / rojo `#E84040`) | tras helper 1 | `sesgo_slug` |
| 3 | **Badge de impacto** | clave escalar `impacto` (`alto`/`medio`, case-insensitive) | `impacto_badge` = `"ALTO"` / `"MEDIO"` / `""` (valor no reconocido, CB-5) | tras helper 2 | — (primer consumidor: `calendario`, Fase C) |
| 4 | **Chart embebido** | clave `chart_png` con valor truthy | `chart_src` = URI `file:///` de `Path(chart_png).resolve()`; valida existencia → `StoryRenderError` accionable si no existe (CB-6, ex-CB-8) | tras helper 3 | `chart_src` |

Notas de diseño de los helpers:
- **Helper 1** generaliza el bloque `variacion` inline de hoy (`story_render.py:90-94`). El
  aplanado `{contenedor}_{sub}` es lo que mantiene vivo `{{variacion_pct}}` del contrato de
  Alerta (necesario para AC9) sin re-hardcodear el nombre `variacion`. El nombre del contenedor
  sale de la clave del payload, no de una constante.
- **Helper 2** conserva **exactamente** la prioridad de hoy (`variacion.direccion` sobre `sesgo`)
  y solo se dispara cuando existe alguno de los dos (antes se seteaba siempre; ahora es
  condicional — irrelevante para Alerta, que siempre trae `sesgo`).
- **Helper 3** se fija ya en esta Fase aunque Alerta no lo use (Riesgo B; lo cubre AC7 con
  fixture aislado). CB-5: valor de `impacto` fuera de `alto`/`medio` → `impacto_badge = ""`
  (mismo criterio "no reconocido → vacío" que el helper 1 con `direccion`).
- **Helper 4** conserva la validación de existencia intacta (CB-6): nunca renderiza con imagen
  rota. Único helper que toca disco; el resto es puro.

### 2. `resolver_loops` — expansión de bloques `<!-- FOR -->` (R4)

Función nueva y pública (la invocan directamente AC4-AC6). Un solo nivel de anidamiento
(documentado en el docstring — "un solo nivel", satisface AC11). Diseño:

**Regex/parseo.** Un único patrón con backreference que ancla `FOR`/`ENDFOR` a la misma clave:

```
<!--\s*FOR:(\w+)\s*-->(.*?)<!--\s*ENDFOR:\1\s*-->      con re.DOTALL, no-greedy
```

- `group(1)` = `clave`; `group(2)` = `bloque_interno`.
- La backreference `\1` garantiza que el `ENDFOR` cierra la **misma** clave (evita cruces).
- `re.sub` con función de reemplazo recorre todos los bloques `FOR` distintos y múltiples
  ocurrencias.

**Expansión por elemento.** Para cada bloque:
1. `datos = payload.get(clave)`.
2. Si `datos` **no existe** o **no es `list`** → `StoryRenderError` accionable
   (`"FOR:{clave} requiere un array en el payload"`) — fail-fast, coherente con la guardia.
3. Si `datos == []` (array vacío, CB-3) → el bloque se reemplaza por cadena vacía (0
   repeticiones): desaparece por completo, sin dejar contenido ni marcas. **Convención
   documentada**: headers/contenedores que deban persistir sin filas van **fuera** de las marcas
   `FOR`/`ENDFOR` (relevante para las plantillas de Fase C).
4. Si `datos` tiene N objetos → se concatena N veces `_expandir_elemento(bloque_interno,
   objeto_i)`, en orden de array.

**Resolución por elemento (`_expandir_elemento`, helper interno nuevo).** Cada repetición
resuelve, con el objeto de esa iteración como contexto local, en orden **fences → tokens** (sin
loops: el anidamiento está fuera de alcance):
1. **Fences genéricos por elemento**: `<!-- IF:clave -->…<!-- ENDIF:clave -->` se conserva sii
   `bool(objeto.get(clave))` (regla genérica de *truthy*), sino se elimina el bloque. Esto es lo
   que hace que el fence se evalúe **por elemento** y no una sola vez sobre el payload completo
   (AC8). Es un mecanismo **distinto** de `_fence_presente` (que sigue gobernando solo los 4
   fences top-level de Alerta) — ver decisión al gate en §6.
2. **Tokens por elemento**: por cada campo escalar del objeto, `{{campo}}` → `str(valor)`. Un
   `{{campo}}` referenciado que el objeto no provee queda sin resolver y cae en la guardia final
   (mismo fail-fast).

Con esto, tras `resolver_loops` los bloques `FOR` quedan totalmente expandidos y resueltos
(fences + tokens propios); las fases 2-4 de `build_html` operan solo sobre el HTML restante
(top-level). En Fase A **ningún** template real usa `FOR` (Alerta no tiene listas); el mecanismo
se valida con fixtures aislados (AC4-AC8). Las derivaciones por elemento (p.ej. flecha dentro de
`filas[]` de `flash`) son extensión explícita de Fase C — el punto de extensión es
`_expandir_elemento`, que en el futuro podrá reutilizar el catálogo de helpers por objeto.

**CB-4 (anidamiento).** `resolver_loops` no recursa: un `<!-- FOR -->` interno queda como texto
literal; si contiene `{{tokens}}`, la guardia final los detecta. No se implementa detección
explícita del anidado (aceptado, OUT del spec).

### 3. Migración de `templates/stories/alerta.html` a 16:9 (R6)

**Qué cambia** (solo CSS de canvas y disposición):
- `html, body { width: 1080px; height: 1920px; }` → `width: 1920px; height: 1080px;`
  (`alerta.html:45-57`), e igual en `.story` (`alerta.html:59-65`).
- `.story` pasa de columna vertical única a **layout horizontal de dos columnas** (CSS grid o
  flex row): **columna izquierda** = editorial (chips → fecha/hora → titular → párrafo → tarjeta
  de precio con `stats` soporte/resistencia/vol); **columna derecha** = bloque de gráfico
  (`#img-alerta` / `#svg-alerta`); **footer** a lo ancho, abajo. Se reajustan `font-size`,
  `padding`, `gap` y proporciones para llenar 1920×1080 sin desbordes (`overflow: hidden` se
  conserva).
- El chart embebido (`chart_png`, PNG de `/chart` **ya en 1920×1080**, confirmado
  `.claude/commands/chart.md:61`) calza nativo en el nuevo viewport horizontal. El ajuste fino,
  si hiciera falta, se resuelve con `object-fit` en `#img-alerta` (mismo mecanismo de hoy) —
  **no** en Python, **no** en `story.md`, **no** recortando el PNG (Q5/R6).
- El SVG decorativo (`#svg-alerta`, `viewBox="0 0 400 220"`, ya apaisado) escala con
  `width/height: 100%` — sin cambios de contenido.

**Qué NO cambia** (contrato de datos intacto — no se reabre `story_alerta`):
- Los **nombres de todos los tokens y fences**: `{{sesgo_slug}}` (clase `<body>`),
  `{{chip_categoria}}`, `{{fecha_hora}}`, `{{titular}}`, `{{parrafo}}`, `{{rotulo_activo}}`,
  `{{tag_riesgo}}`, `{{precio_actual}}`, `{{soporte}}`, `{{resistencia}}`, `{{rotulo_grafico}}`,
  `{{fuente}}`, y los fences `<!-- IF:variacion -->` (`{{variacion_flecha}}`/`{{variacion_pct}}`),
  `<!-- IF:vol -->` (`{{vol_pct}}`), `<!-- IF:chart_img -->` (`{{chart_src}}`),
  `<!-- IF:chart_svg -->`.
- El sistema visual GI: paleta (`#0D0D1A`, `#E84040`, `#00DC82`), degradados de fondo, fuentes
  locales `templates/stories/fonts/*.woff2` (Syne 800 / DM Sans 400·700 / Space Grotesk 600) y el
  footer estándar (`@grupointeligencia` + `grupointeligencia.com` + `FUENTE:` + disclaimer CFD).
- El comentario de cabecera (`alerta.html:1-7`) que advierte "NO cambiar nombres sin actualizar
  `story_render.py` y `tests/test_story_render.py`" — se conserva/actualiza, no se borra.
- Regla "solo lectura" del canvas: el rediseño se **autora en el repo** (decisión ya tomada en
  la spec canónica), no se sincroniza ni se sube nada al proyecto Claude Design.

### 4. `render_png` — viewport 1920×1080 (R1)

Único cambio funcional: `new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)`
(`story_render.py:205-208`). Todo lo demás del contrato de render se conserva: temporal dentro de
`template_dir` + `page.goto("file://…", wait_until="networkidle")` (no `set_content`),
`page.evaluate("document.fonts.ready")` antes del screenshot, `screenshot` sin `full_page`,
`browser.close()` en `finally`, CB-7 (Chromium ausente → `StoryRenderError` con
`uv sync --extra stories && python -m playwright install chromium`). El PNG resultante tiene IHDR
exactamente `(1920, 1080)`. Se actualizan las menciones "1080x1920" en el docstring del módulo
(`story_render.py:5`) y de `render_png` (`story_render.py:169`) a "1920x1080".

### 5. Sincronización de documentación (R7)

Exactamente **3 archivos** con referencias literales a `1080×1920`/9:16 (confirmados por
búsqueda; ningún otro `.md` del repo las menciona):

| Archivo:línea | Texto actual | Cambio |
|---|---|---|
| `CLAUDE.md:249` | "…genera Stories de marca (imagen **1080×1920**," | → `1920×1080` (sección "Stories GI") |
| `CLAUDE.md:322` | "\| `/story [tipo]` \| …(imagen **1080×1920**)…" | → `1920×1080` (fila `/story`, tabla Capa 2) |
| `.claude/commands/story.md:1` | "…(imagen **1080×1920**, formato Instagram/WhatsApp Status)…" | → `1920×1080` (y reformular "formato" si aplica a horizontal/16:9) |
| `docs/design/stories-gi/plantillas-stories-gi.md:32` | "**6 plantillas** de Story (**1080×1920**)…" | → `1920×1080` (intro del catálogo) |

Verificación (AC10):
`rg "1080.?1920" CLAUDE.md '.claude/commands/story.md' 'docs/design/stories-gi/plantillas-stories-gi.md'`
→ **0 matches**; `rg "1920.?1080" CLAUDE.md` → **≥2 matches**. (Nota: `CLAUDE.md` **no** es uno
de los 6 archivos ajenos del director; es editable en Apply.)

---

## Casos borde (mapa CB → diseño)

| CB | Situación | Comportamiento diseñado |
|---|---|---|
| CB-1 | Payload trae clave escalar no usada en el HTML | No-op silencioso: se calcula en el contexto, no encuentra `{{clave}}` que sustituir, no se advierte (R3, Etapa A). |
| CB-2 | HTML usa `{{token}}` sin origen (ni escalar ni helper) | Guardia `_validar_sin_huerfanos` → `StoryRenderError` listando los huérfanos (R2). |
| CB-3 | `FOR` con array `[]` | Bloque reemplazado por cadena vacía; header/contenedor persistente va fuera de las marcas (R4, §2). |
| CB-4 | `FOR` anidado | No soportado; `FOR` interno queda literal; sus `{{tokens}}` caen en la guardia. Sin detección explícita (R4, OUT). |
| CB-5 | `impacto` fuera de `alto`/`medio` | `impacto_badge = ""` (helper 3, §1). |
| CB-6 | `chart_png` con ruta inexistente | `StoryRenderError` accionable en el helper 4 (sin cambios respecto al CB-8 heredado). |
| CB-7 | Chromium ausente | `StoryRenderError` con instrucción `uv sync --extra stories && python -m playwright install chromium` (sin cambios). |

---

## Tratamiento de los 3 riesgos (A/B/C)

- **Riesgo A — fidelidad visual del rediseño horizontal.** No hay "golden PNG" 16:9 del canvas
  para esta plantilla (el snapshot se autora localmente). *Mitigación*: aprobación visual manual
  del director en la primera corrida real (igual que el piloto #109), sin comparación pixel-a-pixel
  automatizada. Los tests **no** asertan estética, solo contrato (tokens/fences inyectados,
  ausencia de huérfanos) + dimensiones IHDR `(1920, 1080)`. Riesgo residual aceptado.

- **Riesgo B — helper de impacto "adelantado" sin consumidor en Alerta.** *Mitigación*: AC7 lo
  cubre con un fixture aislado (`{{impacto_badge}}` + `impacto: "alto"` → `build_context` →
  `impacto_badge == "ALTO"`), sin depender de ninguna plantilla real. Decisión ya tomada por el
  director (spec R5/Q2) — no es apuesta especulativa del agente.

- **Riesgo C — deriva de `build_context` sin lista fija (cambio de mensaje de error).** Al
  eliminar `_TOKENS_ESCALARES`, un payload de Alerta que omita un campo (p.ej. `titular`) **ya
  no** falla temprano en `build_context` con `"Campo obligatorio ausente en el payload: 'titular'"`;
  falla más tarde, en la guardia, con `"Tokens huérfanos sin resolver en el template: titular"`
  (distinta etapa, distinto texto: lista **tokens del HTML**, no **claves del payload**).
  *Mitigación*: la guardia ya es accionable (nombra los tokens exactos); se **documenta el cambio
  de comportamiento en el docstring de `build_context`** para que quien depure no busque el
  mensaje antiguo. **Decisión a elevar al gate humano DESIGN → APPLY** (ver §6, decisión 1).

---

## Estrategia de validación (EDD/TDD) — mapa AC → verificación

Test-first: los tests se escriben/ajustan antes de dar por buena la implementación.
`tests/test_story_render.py` se **reescribe in-place** (R8, sin versiones paralelas 9:16/16:9).
No se toca `conftest.py` (el `sys.path.insert` de `scripts/` vive en el propio test).
`resolver_loops` y `build_context` son puros → testeables **sin Chromium**; solo AC1 usa render
real con `@pytest.mark.skipif(not _chromium_disponible())`.

| AC | Tipo | Verificación | Test |
|---|---|---|---|
| AC1 | `pytest` `skipif` | `render_story(PAYLOAD_EJEMPLO, alerta.html)` → PNG existe, `_png_size == (1920, 1080)`, `> 5 KB` | `test_render_dimensiones_1920x1080` (renombrado, assert `(1080,1920)`→`(1920,1080)`) |
| AC2 | `pytest` puro | payload con clave extra `"nota_interna"` → `build_html(fixture)` sin error, `"nota_interna" not in html` | `test_build_context_escalar_extra_no_op` (nuevo) |
| AC3 | `pytest` puro | fixture con `{{token_inventado}}` → `StoryRenderError` que menciona `token_inventado` | `test_build_html_token_huerfano_lanza_error` (se conserva) |
| AC4 | `pytest` puro | `resolver_loops("<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->", {"filas": []})` → sin `{{nombre}}`, sin marcas `FOR`/`ENDFOR` | `test_resolver_loops_vacio` (nuevo) |
| AC5 | `pytest` puro | idem con `{"filas":[{"nombre":"USD/CLP"}]}` → exactamente 1 `USD/CLP`, sin marcas ni `{{nombre}}` | `test_resolver_loops_uno` (nuevo) |
| AC6 | `pytest` puro | idem con 3 objetos → `USD/CLP`,`Oro`,`WTI` en ese orden, 1 vez c/u, sin marcas | `test_resolver_loops_n` (nuevo) |
| AC7 | `pytest` puro | `build_context({..., "impacto":"alto"})` → `contexto["impacto_badge"] == "ALTO"` | `test_build_context_impacto_badge` (nuevo) |
| AC8 | `pytest` puro | fixture (tmp_path) con `FOR:filas` conteniendo `<!-- IF:x -->` por fila → `build_html` evalúa el fence **por elemento** (N copias, cada una según su fila) | `test_orden_canonico_loops_fences` (nuevo) |
| AC9 | `pytest` puro | `build_html(PAYLOAD_EJEMPLO, alerta.html)` (y variante con `chart_png` a `fixture_chart.png`): `titular`/`parrafo`/`precio_actual`/`soporte`/`resistencia`/`tag_riesgo` inyectados; sin `{{`; omite variación/vol cuando faltan; chart embebido/SVG como hoy | `test_alerta_no_placeholders` + `test_alerta_chart_embebido` + `test_alerta_chart_png_inexistente_lanza_error` + `test_build_html_contract` (se conservan, sin cambios de aserción de contenido) |
| AC10 | `rg` (estructural) | `rg "1080.?1920" …` → 0; `rg "1920.?1080" CLAUDE.md` → ≥2 | manual/gate |
| AC11 | `rg` (estructural) | `rg -i "nivel" scripts/story_render.py` → ≥1 (docstring de `resolver_loops` dice "un solo nivel") | manual/gate |
| AC12 | `rg` / `git diff` (estructural) | `git diff master -- scripts/ruta_story.ps1` → sin cambios (Q8) | manual/gate |

**Fixtures** (R8): `resolver_loops` recibe `html: str`, por lo que AC4-AC6 pasan el HTML **inline**
(sin archivo). AC8 usa `tmp_path` (patrón del test de huérfanos). `tests/fixtures/stories/fixture_template.html`
**no cambia dimensiones** (no tiene CSS de viewport; `build_html`/`resolver_loops` son puros).
`fixture_chart.png` (68 bytes, ya existe) se reutiliza para la variante con chart de AC9.

---

## Estructura de archivos afectados

```
MODIFICADOS (todos en Apply — este Change design.md NO edita código)
  scripts/story_render.py            R1/R2/R3/R4/R5 — elimina _TOKENS_ESCALARES; build_context dinámico;
                                     + resolver_loops (+ _expandir_elemento); reordena build_html; viewport 1920×1080;
                                     docstrings (módulo + build_context[Riesgo C] + resolver_loops["un solo nivel", AC11])
  templates/stories/alerta.html      R6 — layout 16:9 (mismos tokens/fences)
  tests/test_story_render.py         R8 — reescritura in-place (AC1-AC9)
  CLAUDE.md                          R7 — líneas 249 y 322 → 1920×1080
  .claude/commands/story.md          R7 — línea 1 → 1920×1080
  docs/design/stories-gi/plantillas-stories-gi.md   R7 — línea 32 → 1920×1080

SIN CAMBIOS (confirmado)
  scripts/ruta_story.ps1             AC12/Q8 — agnóstico al tamaño
  tests/conftest.py                  R8/D2 — no se toca
  tests/fixtures/stories/*           dimensiones intactas (motor puro)
  .claude/shared/modo_ejecutivo.md   /story sigue en "No elegibles"
  src/market_data_mcp/**             ninguna capa hexagonal tocada
  pyproject.toml                     sin nuevas dependencias (Playwright ya opcional)

PROHIBIDO TOCAR (6 archivos ajenos del director)
  .claude/commands/apertura.md · data/glosario_siglas.json · data/historial_encuestas.json
  templates/encuesta_posicion.txt · templates/encuesta_tendencia.txt · uv.lock
```

---

## Decisiones para el gate humano DESIGN → APPLY

1. **[ELEVAR] Riesgo C — cambio de mensaje de error de campo faltante.** Un payload de Alerta
   incompleto ya no falla con `"Campo obligatorio ausente en el payload: X"` sino con
   `"Tokens huérfanos sin resolver en el template: X"` (guardia, más tarde). *Recomendación del
   agente*: **aceptar** el cambio (mensaje sigue accionable, es la consecuencia buscada de los
   tokens dinámicos R2) y documentarlo en el docstring de `build_context`. Requiere OK del
   director.

2. **[ELEVAR] Fences genéricos por elemento dentro de `FOR`.** `_expandir_elemento` introduce una
   regla de presencia genérica (`bool(objeto.get(clave))`) **distinta** del `_fence_presente`
   especializado de Alerta (que se conserva intacto). Es necesaria para AC8 y para las plantillas
   de Fase C; en Fase A solo la ejercita el fixture de AC8 (ningún template real). *Recomendación*:
   **aceptar** (riesgo bajo, aislado por test). Confirmar que no contradice "conservar
   `_fence_presente` en su lógica" del spec (se conserva; la regla genérica es un mecanismo aparte).

3. **[ELEVAR] `str(None) → "None"` en escalares dinámicos.** R2 manda convertir todo escalar con
   `str()`, incluido `None`. Implica que `{{clave}}` con `clave: None` renderiza el literal
   `"None"`. En Alerta el único `None` posible es `chart_png` (no tokenizado directo → inofensivo).
   *Recomendación*: **aceptar** tal como lo fija R2; anotarlo en el docstring como matiz conocido.

Todo lo demás quedó resuelto en `spec.md` (Q1-Q8) — no hay preguntas bloqueantes abiertas para
Design.

---

## Desglose de implementación (tareas)

> Ordenadas por dependencia. Cada tarea que toca código ejecutable lleva su criterio de
> aceptación **ejecutable** (test/`rg`) mapeado a `spec.md`. TDD: escribir/ajustar el test antes
> de dar la tarea por cerrada. Este desglose deja el Change listo para `break-to-tasks`
> (`tasks.md`); **no** se escribe `tasks.md` en esta fase (acción del hilo principal tras la
> aprobación humana).

### 1. Motor — `scripts/story_render.py`

- [ ] **1.1 Tokens escalares dinámicos en `build_context` (Etapa A).** Eliminar
  `_TOKENS_ESCALARES`; recorrer `payload.items()` agregando `str(valor)` por cada escalar
  (no-`dict`/no-`list`, incl. `None`). *Criterio (AC2)*: `test_build_context_escalar_extra_no_op`
  — payload con `"nota_interna"` → `build_html` sin error y `"nota_interna" not in html`.
- [ ] **1.2 Catálogo de 4 helpers en `build_context` (Etapa B).** Helper 1 (flecha + aplanado
  `{contenedor}_{sub}`), helper 2 (`sesgo_slug`, prioridad `variacion.direccion`), helper 3
  (`impacto_badge`), helper 4 (`chart_src` con validación de existencia). Documentar en el
  docstring el cambio de comportamiento del Riesgo C y el matiz `str(None)`. *Criterio (AC7)*:
  `test_build_context_impacto_badge` — `impacto:"alto"` → `impacto_badge == "ALTO"`. *(depende de 1.1)*
- [ ] **1.3 `resolver_loops` + `_expandir_elemento`.** Regex con backreference; array vacío →
  bloque vacío; N objetos → N copias; por elemento resolver fences genéricos (truthy) + tokens.
  Docstring con "un solo nivel". *Criterios (AC4/AC5/AC6/AC11)*: `test_resolver_loops_vacio` /
  `_uno` / `_n`; `rg -i "nivel" scripts/story_render.py` ≥1. *(independiente de 1.1/1.2)*
- [ ] **1.4 Reordenar `build_html` a loops → fences → tokens → guardia.** Insertar
  `resolver_loops` como fase 1; conservar `_resolver_fences`/`_sustituir_tokens`/
  `_validar_sin_huerfanos`. *Criterio (AC8)*: `test_orden_canonico_loops_fences` — `FOR` con
  `IF:x` interno se evalúa por elemento. *(depende de 1.2 y 1.3)*
- [ ] **1.5 Viewport `1920×1080` en `render_png`.** Cambiar el dict `viewport`; actualizar
  docstrings del módulo y de `render_png` ("1080x1920"→"1920x1080"). *Criterio (AC1)*:
  `test_render_dimensiones_1920x1080` (renombrado) — IHDR `(1920, 1080)`, `> 5 KB` (`skipif` sin
  Chromium). *(independiente)*

### 2. Snapshot — `templates/stories/alerta.html`

- [ ] **2.1 Migrar layout a 16:9.** `html/body/.story` → 1920×1080; disposición horizontal de
  dos columnas (editorial | gráfico) + footer a lo ancho; conservar paleta, fuentes locales,
  footer y **todos** los tokens/fences (`object-fit` para el chart si hace falta). No tocar el
  contrato de datos. *Criterio (AC9)*: `test_alerta_no_placeholders` + `test_alerta_chart_embebido`
  + `test_alerta_chart_png_inexistente_lanza_error` verdes sin cambiar sus aserciones de
  contenido. *(depende de 1.1-1.4; validación visual manual del director = Riesgo A)*

### 3. Tests — `tests/test_story_render.py` (reescritura in-place, R8)

- [ ] **3.1 Renombrar/ajustar dimensiones.** `test_render_dimensiones_1080x1920` →
  `_1920x1080`, assert `(1080,1920)`→`(1920,1080)`. *(cubre AC1)*
- [ ] **3.2 Tests nuevos de tokens dinámicos y helper.** `test_build_context_escalar_extra_no_op`
  (AC2), `test_build_context_impacto_badge` (AC7). *(cubren 1.1/1.2)*
- [ ] **3.3 Tests nuevos de `resolver_loops`.** `_vacio`/`_uno`/`_n` con HTML inline (AC4-AC6) +
  `test_orden_canonico_loops_fences` con `tmp_path` (AC8). *(cubren 1.3/1.4)*
- [ ] **3.4 Conservar** `test_build_html_contract`, `test_build_html_token_huerfano_lanza_error`,
  `test_alerta_no_placeholders`, `test_alerta_chart_embebido`,
  `test_alerta_chart_png_inexistente_lanza_error` (AC3/AC9, sin regresión). **No tocar**
  `conftest.py`. *Criterio*: suite completa verde con `uv run pytest tests/test_story_render.py`.

### 4. Documentación (R7)

- [ ] **4.1 Sincronizar 3 archivos.** `CLAUDE.md:249,322`, `.claude/commands/story.md:1`,
  `docs/design/stories-gi/plantillas-stories-gi.md:32` → `1920×1080`. *Criterio (AC10)*:
  `rg "1080.?1920"` en los 3 → 0 matches; `rg "1920.?1080" CLAUDE.md` → ≥2.
- [ ] **4.2 Confirmar `ruta_story.ps1` sin cambios.** *Criterio (AC12)*:
  `git diff master -- scripts/ruta_story.ps1` → vacío.

---

## Validation Strategy

Resumen operativo (detalle en "Estrategia de validación" arriba):
- **Unidad/contrato (sin Chromium)**: `uv run pytest tests/test_story_render.py` cubre AC2-AC9
  (mapeo puro `build_context`/`resolver_loops`/`build_html`).
- **Render real (con Chromium)**: AC1 vía `@pytest.mark.skipif` — IHDR `(1920, 1080)`.
- **Estructural (`rg`/`git`)**: AC10 (docs), AC11 (docstring "un solo nivel"), AC12
  (`ruta_story.ps1` intacto).
- **Visual (manual)**: aprobación del director en la primera corrida real de `/story alerta`
  (Riesgo A) — no automatizada, coherente con el piloto #109.

---

## Referencias

- `spec.md` (#119 — R1-R8, CB-1..CB-7, AC1-AC12, Q1-Q8 resueltas, riesgos A/B/C).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` (PR #118 — alcance canónico).
- `.pulse/changes/archive/109-.../design.md` (D1-D7 heredadas) · `.pulse/specs/stories-gi/spec.md`
  (contrato `story_alerta`, no reabierto).
- `scripts/story_render.py:29-46,58-116,119-165,168-221` (motor a generalizar).
- `templates/stories/alerta.html:45-65` (viewport/`.story` a migrar) + `templates/stories/fonts/`.
- `tests/test_story_render.py` + `tests/fixtures/stories/` · `.claude/commands/chart.md:61`
  (chart ya en 1920×1080) · `.claude/commands/story.md:1` · `CLAUDE.md:249,322` ·
  `docs/design/stories-gi/plantillas-stories-gi.md:32`.
- Issue #119 (`bbenja11/grupo-analisis-mercado`).
