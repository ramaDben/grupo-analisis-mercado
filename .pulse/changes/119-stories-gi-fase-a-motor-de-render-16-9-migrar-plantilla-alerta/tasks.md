# Tasks — Stories GI · Fase A: motor de render 16:9 + migrar plantilla Alerta (#119)

> Desglose de implementación de `design.md` (Change #119, dominio `stories-gi`). Formaliza las
> tareas 1.1–4.2 del design, cada una mapeada a su requisito (`R1-R8`) y a su criterio de
> aceptación **ejecutable** (`AC1-AC12`, definidos en `spec.md`). Ordenadas por dependencia.
> **TDD**: escribir/ajustar el test antes de dar la tarea por cerrada. Toda la implementación se
> ejecuta en la fase **Apply** — este documento no contiene ni escribe código.

## Contrato heredado (no se reabre)

- Contrato de datos `story_alerta` (`.pulse/specs/stories-gi/spec.md`) y decisiones D1-D7 del
  Change #109 (`.pulse/changes/archive/109-.../design.md`): **intactos**. Solo se generaliza el
  motor y se migran layout/viewport.
- Fuente canónica de alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
  (PR #118).

## Archivos afectados (todos en Apply)

| Archivo | Requisitos | Grupo |
|---|---|---|
| `scripts/story_render.py` | R1/R2/R3/R4/R5 | 1 |
| `templates/stories/alerta.html` | R6 | 2 |
| `tests/test_story_render.py` (reescritura in-place; **no** tocar `conftest.py`) | R8 | 3 |
| `CLAUDE.md` · `.claude/commands/story.md` · `docs/design/stories-gi/plantillas-stories-gi.md` | R7 | 4 |
| `scripts/ruta_story.ps1` | AC12 (confirmar **sin cambios**) | 4 |

## Grafo de dependencias (orden de ejecución)

```
1.1 ─┐
     ├─> 1.2 ─┐
1.3 ─┴────────┼─> 1.4 ──> 2.1 ──(validación visual manual del director · Riesgo A)
             │
1.5 (indep.) ┘
3.1 (cubre 1.5) · 3.2 (cubre 1.1/1.2) · 3.3 (cubre 1.3/1.4) · 3.4 (conservar, no regresión)
4.1 (indep.) · 4.2 (indep., confirmación)
```

- **1.1** y **1.3** son independientes entre sí.
- **1.2** depende de **1.1** (Etapa B se aplica tras poblar escalares de Etapa A).
- **1.4** depende de **1.2** y **1.3** (reordena `build_html` insertando `resolver_loops`).
- **2.1** depende de **1.1–1.4** (el snapshot migrado debe pasar por el motor generalizado).
- **1.5**, **4.1**, **4.2** son independientes del resto.
- Los tests del grupo 3 se escriben **antes** de cerrar la tarea de código que cubren (TDD).

---

## 1. Motor — `scripts/story_render.py`

- [x] **1.1 Tokens escalares dinámicos en `build_context` (Etapa A) — R2/R3.**
  Eliminar la tupla fija `_TOKENS_ESCALARES` (`story_render.py:33-46`). En `build_context`,
  recorrer `payload.items()` y, por cada clave cuyo valor **no** sea `dict` ni `list`, agregar
  `contexto[clave] = str(valor)` (incluye `None`/`bool`/números vía `str()` tal cual manda R2;
  ej. `chart_png: None` → `"None"`). Sin noción de "campo obligatorio": una clave del payload no
  referenciada en el HTML es no-op silencioso (R3/CB-1); un `{{token}}` del HTML sin origen cae
  en la guardia (R2/CB-2). Firma pública de `build_context` intacta.
  - *Depende de*: —
  - *Criterio ejecutable (AC2)*: `uv run pytest tests/test_story_render.py::test_build_context_escalar_extra_no_op`
    — payload con clave extra `"nota_interna"` → `build_html(fixture)` sin error y
    `"nota_interna" not in html`.

- [x] **1.2 Catálogo cerrado de 4 helpers en `build_context` (Etapa B) — R5.**
  Tras poblar escalares, aplicar en orden, cada uno disparado por su clave:
  1. **Flecha de dirección** — dict top-level con `direccion` (ej. `variacion`): deriva
     `{contenedor}_flecha` = `▲`(`alcista`)/`▼`(`bajista`)/`""`(otro) **y** aplana escalares del
     objeto a `{contenedor}_{sub}` (mantiene vivo `{{variacion_pct}}` sin re-hardcodear el nombre
     `variacion`).
  2. **Slug de color** — `variacion.direccion` (prioridad) → si no, `sesgo`: deriva `sesgo_slug`
     = `str(direccion o sesgo).lower()`. Condicional (solo si existe alguno de los dos);
     conserva **exactamente** la prioridad actual (`story_render.py:100-104`).
  3. **Badge de impacto** — clave escalar `impacto` (`alto`/`medio`, case-insensitive): deriva
     `impacto_badge` = `"ALTO"`/`"MEDIO"`/`""` (valor no reconocido → vacío, CB-5). Sin consumidor
     en Alerta (Riesgo B; se fija ya para Fase C).
  4. **Chart embebido** — clave `chart_png` truthy: deriva `chart_src` = `Path(chart_png).resolve().as_uri()`;
     valida existencia → `StoryRenderError` accionable si no existe (CB-6, sin cambios respecto
     al CB-8 heredado). Único helper que toca disco.

  Documentar en el docstring de `build_context`: (a) el **cambio de mensaje de error** del
  Riesgo C (ya no "Campo obligatorio ausente…"; ahora falla en la guardia con "Tokens
  huérfanos…"), y (b) el matiz `str(None) → "None"` como comportamiento conocido.
  - *Depende de*: **1.1**
  - *Criterio ejecutable (AC7)*: `uv run pytest tests/test_story_render.py::test_build_context_impacto_badge`
    — `build_context({..., "impacto": "alto"})` → `contexto["impacto_badge"] == "ALTO"`.

- [x] **1.3 `resolver_loops` + `_expandir_elemento` (nuevas) — R4/CB-3/CB-4.**
  Función pública `resolver_loops(html, payload) -> str`. Un único patrón regex con backreference
  que ancla `FOR`/`ENDFOR` a la misma clave:
  `<!--\s*FOR:(\w+)\s*-->(.*?)<!--\s*ENDFOR:\1\s*-->` con `re.DOTALL`, no-greedy; `re.sub` con
  función de reemplazo. Por bloque:
  - `payload.get(clave)` ausente o no-`list` → `StoryRenderError` accionable (fail-fast).
  - `[]` (CB-3) → bloque reemplazado por cadena vacía (0 repeticiones, sin marcas).
  - N objetos → concatenar N veces `_expandir_elemento(bloque_interno, objeto_i)` en orden.

  `_expandir_elemento` (helper interno nuevo) resuelve **por elemento** en orden fences → tokens:
  fences genéricos `<!-- IF:clave -->…<!-- ENDIF:clave -->` conservados sii `bool(objeto.get(clave))`
  (regla *truthy* genérica, **distinta** de `_fence_presente`); luego `{{campo}}` → `str(valor)`
  por cada escalar del objeto. Sin recursión (CB-4: `FOR` anidado queda literal y cae en la
  guardia). Docstring debe decir explícitamente **"un solo nivel"** (AC11).
  - *Depende de*: — (independiente de 1.1/1.2)
  - *Criterios ejecutables*:
    - (AC4) `uv run pytest tests/test_story_render.py::test_resolver_loops_vacio`
    - (AC5) `uv run pytest tests/test_story_render.py::test_resolver_loops_uno`
    - (AC6) `uv run pytest tests/test_story_render.py::test_resolver_loops_n`
    - (AC11) `rg -i "nivel" scripts/story_render.py` → ≥1 match.

- [x] **1.4 Reordenar `build_html` a `loops → fences → tokens → guardia`.**
  Insertar `resolver_loops(html, payload)` como **fase 1**, antes de `_resolver_fences`
  (`story_render.py:161-163`). Conservar `_resolver_fences` / `_sustituir_tokens` /
  `_validar_sin_huerfanos` en su lógica; solo cambia su posición relativa. Firma e interfaz
  pública de `build_html` intactas. `_FENCES` se conserva (sigue gobernando los 4 fences
  top-level de Alerta).
  - *Depende de*: **1.2** y **1.3**
  - *Criterio ejecutable (AC8)*: `uv run pytest tests/test_story_render.py::test_orden_canonico_loops_fences`
    — fixture con `FOR:filas` conteniendo un `IF:x` interno por fila → `build_html` produce N
    copias y evalúa el fence **por elemento**, no una sola vez sobre el payload completo.

- [x] **1.5 Viewport `1920×1080` en `render_png` — R1.**
  Cambiar el dict viewport a `{"width": 1920, "height": 1080}` (`story_render.py:205-208`).
  Actualizar las menciones "1080x1920" → "1920x1080" en el docstring del módulo
  (`story_render.py:5`) y de `render_png` (`story_render.py:169`). Todo lo demás del contrato de
  render intacto (temporal en `template_dir`, `page.goto(file://…, wait_until="networkidle")`,
  `document.fonts.ready`, screenshot sin `full_page`, `browser.close()` en `finally`, CB-7).
  - *Depende de*: — (independiente)
  - *Criterio ejecutable (AC1)*: `uv run pytest tests/test_story_render.py::test_render_dimensiones_1920x1080`
    (`@pytest.mark.skipif` sin Chromium) — PNG existe, `_png_size == (1920, 1080)`, `> 5 KB`.

---

## 2. Snapshot — `templates/stories/alerta.html`

- [x] **2.1 Migrar layout a 16:9 — R6.**
  `html, body` y `.story` (`alerta.html:45-65`): `1080×1920` → `1920×1080`. Pasar `.story` de
  columna vertical única a **layout horizontal de dos columnas**: izquierda = editorial (chips →
  fecha/hora → titular → párrafo → tarjeta de precio con `stats` soporte/resistencia/vol);
  derecha = bloque de gráfico (`#img-alerta` / `#svg-alerta`); footer a lo ancho abajo. Reajustar
  `font-size`/`padding`/`gap`/proporciones para llenar 1920×1080 sin desbordes (`overflow: hidden`
  se conserva). Chart `chart_png` (ya 1920×1080) calza nativo; ajuste fino vía `object-fit` en
  `#img-alerta` si hace falta — **no** en Python/`story.md`/recorte del PNG.
  **NO cambiar el contrato de datos**: conservar todos los nombres de tokens/fences
  (`{{sesgo_slug}}`, `{{chip_categoria}}`, `{{fecha_hora}}`, `{{titular}}`, `{{parrafo}}`,
  `{{rotulo_activo}}`, `{{tag_riesgo}}`, `{{precio_actual}}`, `{{soporte}}`, `{{resistencia}}`,
  `{{rotulo_grafico}}`, `{{fuente}}`; fences `IF:variacion`/`IF:vol`/`IF:chart_img`/`IF:chart_svg`
  con `{{variacion_flecha}}`/`{{variacion_pct}}`/`{{vol_pct}}`/`{{chart_src}}`). Conservar paleta
  GI (`#0D0D1A`/`#E84040`/`#00DC82`), degradados, fuentes locales `fonts/*.woff2`, footer estándar
  y el comentario de cabecera (`alerta.html:1-7`). Regla "solo lectura" del canvas: se autora en
  el repo, no se sube nada.
  - *Depende de*: **1.1–1.4**
  - *Criterio ejecutable (AC9)*: `uv run pytest tests/test_story_render.py::test_alerta_no_placeholders tests/test_story_render.py::test_alerta_chart_embebido tests/test_story_render.py::test_alerta_chart_png_inexistente_lanza_error`
    verdes **sin cambiar sus aserciones de contenido** (`titular`/`parrafo`/`precio_actual`/
    `soporte`/`resistencia`/`tag_riesgo` inyectados; sin `{{`; omite variación/vol cuando faltan;
    `<img>`/`<svg>` según `chart_png`).
  - *Validación visual manual del director* (Riesgo A, no automatizada): aprobación en la primera
    corrida real de `/story alerta`, igual que el piloto #109. Los tests no asertan estética.

---

## 3. Tests — `tests/test_story_render.py` (reescritura in-place, R8)

> No se toca `conftest.py` (el `sys.path.insert` de `scripts/` vive en el propio test, D2/§5).
> `build_context`/`resolver_loops`/`build_html` son puros → testeables **sin Chromium**; solo AC1
> usa render real con `skipif`. TDD: escribir el test antes de cerrar la tarea de código que cubre.

- [x] **3.1 Renombrar/ajustar test de dimensiones.**
  `test_render_dimensiones_1080x1920` → `test_render_dimensiones_1920x1080`; assert
  `_png_size(...) == (1080, 1920)` → `== (1920, 1080)` (`test_story_render.py:168,176`).
  - *Depende de*: **1.5** (código) — se escribe antes (TDD).
  - *Cubre*: AC1.

- [x] **3.2 Tests nuevos de tokens dinámicos y helper.**
  `test_build_context_escalar_extra_no_op` (AC2, payload con `"nota_interna"` sobre un fixture
  mínimo) y `test_build_context_impacto_badge` (AC7, `impacto:"alto"` → `impacto_badge == "ALTO"`).
  - *Depende de*: **1.1** y **1.2** (código) — se escriben antes (TDD).
  - *Cubre*: AC2, AC7.

- [x] **3.3 Tests nuevos de `resolver_loops` y orden canónico.**
  `test_resolver_loops_vacio` / `_uno` / `_n` con HTML **inline** (`resolver_loops` recibe `str`;
  AC4-AC6) + `test_orden_canonico_loops_fences` con `tmp_path` (AC8, fixture con `FOR:filas`
  conteniendo `IF:x` por fila).
  - *Depende de*: **1.3** y **1.4** (código) — se escriben antes (TDD).
  - *Cubre*: AC4, AC5, AC6, AC8.

- [x] **3.4 Conservar tests existentes (sin regresión).**
  Mantener `test_build_html_contract`, `test_build_html_token_huerfano_lanza_error`,
  `test_alerta_no_placeholders`, `test_alerta_chart_embebido`,
  `test_alerta_chart_png_inexistente_lanza_error` sin cambiar sus aserciones de contenido.
  `fixture_template.html` **no** cambia dimensiones (motor puro); `fixture_chart.png` se reutiliza.
  - *Depende de*: **2.1** (el snapshot migrado debe pasar estos tests) — cierre final del grupo.
  - *Criterio ejecutable (AC3/AC9)*: suite completa verde con `uv run pytest tests/test_story_render.py`.

---

## 4. Documentación y confirmaciones (R7)

- [x] **4.1 Sincronizar 3 archivos a `1920×1080`.**
  - `CLAUDE.md:249` (sección "Stories GI") y `CLAUDE.md:322` (fila `/story`, tabla Capa 2).
  - `.claude/commands/story.md:1` (y reformular "formato Instagram/WhatsApp Status" si aplica a
    horizontal/16:9).
  - `docs/design/stories-gi/plantillas-stories-gi.md:32` (intro del catálogo).
  - `CLAUDE.md` **no** es archivo ajeno del director; es editable en Apply.
  - *Depende de*: — (independiente)
  - *Criterio ejecutable (AC10)*:
    `rg "1080.?1920" CLAUDE.md '.claude/commands/story.md' 'docs/design/stories-gi/plantillas-stories-gi.md'`
    → **0 matches**; `rg "1920.?1080" CLAUDE.md` → **≥2 matches**.

- [x] **4.2 Confirmar `ruta_story.ps1` sin cambios.**
  El helper es agnóstico al tamaño/aspecto (solo arma ruta por fecha/activo/plantilla/hora).
  - *Depende de*: — (confirmación, no edición)
  - *Criterio ejecutable (AC12)*: `git diff master -- scripts/ruta_story.ps1` → **vacío**.

---

## Decisiones a elevar al gate humano DESIGN → APPLY

> Registradas en `design.md` §"Decisiones para el gate humano". Requieren OK explícito del
> director antes de Apply (los subagentes **nunca** aprueban el gate).

1. **[ELEVAR] Riesgo C — cambio de mensaje de error de campo faltante.** Al eliminar
   `_TOKENS_ESCALARES`, un payload de Alerta incompleto ya no falla con
   `"Campo obligatorio ausente en el payload: X"` sino, más tarde, en la guardia con
   `"Tokens huérfanos sin resolver en el template: X"` (lista tokens del HTML, no claves del
   payload). *Recomendación del agente*: **aceptar** (sigue accionable; consecuencia buscada de
   R2) y documentarlo en el docstring de `build_context` (tarea 1.2).

2. **[ELEVAR] Fences genéricos por elemento dentro de `FOR`.** `_expandir_elemento` introduce una
   regla de presencia genérica `bool(objeto.get(clave))`, **distinta** del `_fence_presente`
   especializado de Alerta (que se conserva intacto). Necesaria para AC8 y para Fase C; en Fase A
   solo la ejercita el fixture de AC8. *Recomendación*: **aceptar** (riesgo bajo, aislado por
   test; no contradice "conservar `_fence_presente`").

3. **[ELEVAR] `str(None) → "None"` en escalares dinámicos.** R2 manda convertir todo escalar con
   `str()`, incluido `None` → `{{clave}}` con `clave: None` renderiza el literal `"None"`. En
   Alerta el único `None` posible es `chart_png` (no tokenizado directo → inofensivo).
   *Recomendación*: **aceptar** tal como fija R2; anotarlo en el docstring (tarea 1.2).

Fuera de estas tres, no hay preguntas bloqueantes abiertas: Q1-Q8 quedaron resueltas en `spec.md`.

---

## Restricciones duras (Apply)

- **NO tocar ni commitear** los 6 archivos ajenos del director: `.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
  `templates/encuesta_tendencia.txt`, `uv.lock`.
- **NUNCA** `git add -A` / `git add .` — solo los archivos del grupo 1-4.
- **No** agregar dependencias (`pyproject.toml` sin cambios; Playwright ya opcional). **No** tocar
  `conftest.py`, `tests/fixtures/stories/*` (dimensiones), `src/market_data_mcp/**`,
  `.claude/shared/modo_ejecutivo.md`.
- Regla "solo lectura" del canvas: el rediseño se autora en el repo; no se sube nada al proyecto
  Claude Design.

## Verificación global (cierre del Change)

```
uv run pytest tests/test_story_render.py            # AC1(skipif)/AC2-AC9
rg "1080.?1920" CLAUDE.md '.claude/commands/story.md' 'docs/design/stories-gi/plantillas-stories-gi.md'  # AC10 → 0
rg "1920.?1080" CLAUDE.md                            # AC10 → ≥2
rg -i "nivel" scripts/story_render.py                # AC11 → ≥1
git diff master -- scripts/ruta_story.ps1            # AC12 → vacío
```
