# Tasks — Stories GI · Fase B: plantilla Quote 16:9 (#121)

> Desglose de implementación de `design.md` (Change #121, dominio `stories-gi`). Formaliza las
> tareas 1.1–5.1 del design, cada una mapeada a su requisito (`R1-R9`) y a su criterio de
> aceptación **ejecutable** (`AC1-AC10`, definidos en `spec.md`). Ordenadas por dependencia.
> **TDD**: escribir/ajustar el test antes de dar la tarea por cerrada. Toda la implementación se
> ejecuta en la fase **Apply** — este documento no contiene ni escribe código.

## Contrato heredado (no se reabre)

- Motor generalizado de Fase A (#119, `master` v0.2.0): `scripts/story_render.py`
  (`build_context`/`resolver_loops`/`_resolver_fences`/`_FENCES`/`render_png`) **intacto**. `quote`
  es su primer consumidor **sin** fences `IF`/`FOR` ni loops — tokens 100% escalares
  incondicionales.
- Contrato de datos `story_alerta` (`.pulse/specs/stories-gi/spec.md`) y snapshot
  `templates/stories/alerta.html`: **sin cambios** (AC10).
- Fuente canónica de alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
  (fila 10, `quote`, líneas 55-110).

## Archivos afectados (todos en Apply)

| Archivo | Requisitos | Grupo | Naturaleza |
|---|---|---|---|
| `templates/stories/quote.html` (**nuevo**) | R1/R4/R6 | 1 | snapshot 1920×1080 |
| `tests/test_story_render.py` (aditivo; **no** tocar `conftest.py`) | R8 | 2 | 3 tests nuevos |
| `.claude/commands/story.md` | R5/R7 | 3 | PASO 0 + recolección editorial |
| `CLAUDE.md` (sección "Stories GI") | R9 | 4 | enumerar `quote` |
| — (no-regresión, confirmación) | AC10 | 5 | `git diff` vacío |

## Grafo de dependencias (orden de ejecución)

```
1.1 ──> 1.2 ──> 1.3 ──(validación visual manual del director · Riesgo A)
                 │
2.1 (cubre 1.2) ─┤     2.1 depende de 1.2 · 2.2 depende de 1.3 · 2.3 depende de 1.2
2.2 (cubre 1.3) ─┤
2.3 (cubre 1.2) ─┘
3.1 (indep.) ──> 3.2
4.1 (indep.)
5.1 (indep., confirmación final)
```

- **1.1 → 1.2 → 1.3**: el snapshot se autora incrementalmente (andamiaje → cuerpo/tokens →
  comillas/colapso).
- Los tests del grupo 2 se escriben **antes** de cerrar la tarea de snapshot que cubren (TDD):
  2.1/2.3 cubren 1.2; 2.2 cubre 1.3.
- **3.1 → 3.2**: registrar el `[tipo]` antes del bloque de recolección editorial en `story.md`.
- **4.1** y **5.1** son independientes del resto.

---

## 1. Snapshot — `templates/stories/quote.html` (nuevo, R1/R4/R6)

- [x] **1.1 Andamiaje de marca (R1).**
  Copiar **verbatim** el bloque `@font-face` + `html, body` de `alerta.html:14-58` (fuentes
  locales `fonts/*.woff2`: Syne 800 / DM Sans 400·700 / Space Grotesk 600; `* { box-sizing }`;
  fondo `#0D0D1A` con degradados; viewport 1920×1080; `color: #F5F3F7`; `overflow: hidden`) y el
  footer estándar (`@grupointeligencia` + `grupointeligencia.com` + disclaimer CFD,
  `alerta.html:398-409`, **sin** `{{fuente}}`). Comentario de cabecera "NO cambiar nombres de
  tokens sin actualizar tests".
  - *Depende de*: —
  - *Criterio ejecutable (AC1)*: `rg "width: 1920px" templates/stories/quote.html` ≥1 y
    `rg "height: 1080px" templates/stories/quote.html` ≥1.

- [x] **1.2 Cuerpo editorial y tokens (R1/R2).**
  Contenedor raíz `.story` en columna (cuerpo centrado + footer a lo ancho). `<body class="quote">`
  estático — **SIN** `{{sesgo_slug}}` ni ningún token de Alerta (referenciarlo dejaría un huérfano:
  `quote` no trae `sesgo`, el helper 2 no puebla `sesgo_slug`). Cuerpo `.quote-cuerpo` (centrado
  vertical/horizontal) con `<blockquote class="quote-texto">{{cita}}</blockquote>` +
  `.quote-atribucion` conteniendo `<p class="quote-autor">{{autor}}</p>` y
  `<p class="quote-cargo">{{autor_sub}}</p>`. Los **únicos** tres tokens `{{...}}` del archivo son
  `{{cita}}`, `{{autor}}`, `{{autor_sub}}`. Sin chips, sin tarjeta de precio, sin `stats`, sin
  columna de gráfico, sin `#img-*`/`#svg-*`, sin `{{fuente}}`. Sin fences `IF`/`FOR`.
  - *Depende de*: **1.1**
  - *Criterios ejecutables (AC2/AC3)*: `rg "<!-- (IF|FOR):" templates/stories/quote.html` → **0
    matches**; `uv run pytest tests/test_story_render.py::test_quote_no_placeholders` verde.

- [x] **1.3 Comillas decorativas estáticas + colapso `:empty` (R4/R6).**
  Comillas tipográficas **estáticas** como pseudo-elementos CSS sobre `.quote-texto`
  (`::before { content: "\201C"; }` = `“`, `::after { content: "\201D"; }` = `”`), en Syne, color
  de acento GI — **nunca** parte del valor de `{{cita}}`. Colapso del cargo vacío:
  `.quote-cargo:empty { display: none; }` (saca del flujo el `<p>` vacío cuando `autor_sub == ""`,
  colapsa el espacio vertical, no solo el texto — el bloque de atribución queda centrado sin hueco).
  - *Depende de*: **1.2**
  - *Criterios ejecutables (AC6/AC4)*: `rg "::before|::after|“|”|\\201C" templates/stories/quote.html`
    ≥1; `rg ":empty" templates/stories/quote.html` ≥1;
    `uv run pytest tests/test_story_render.py::test_quote_autor_sub_vacio` verde.
  - *Validación visual manual del director* (Riesgo A, no automatizada): aprobación en la primera
    corrida real de `/story quote` (font-size/padding/posición de comillas se afinan en Apply,
    Riesgo B). Los tests no asertan estética.

---

## 2. Tests — `tests/test_story_render.py` (aditivo, R8)

> No se toca `conftest.py` (el `sys.path.insert` de `scripts/` vive en el propio test). Sin fixture
> nuevo en `tests/fixtures/stories/` — se reusa el patrón contra el snapshot real `quote.html`,
> igual que los tests de `alerta.html`. `build_html` es puro → testeable **sin Chromium**; solo AC5
> usa render real con `skipif`. TDD: escribir el test antes de cerrar la tarea de snapshot que cubre.
> Constante propuesta: `PAYLOAD_QUOTE = {"plantilla": "quote", "cita": "El mercado premia la
> paciencia más que la predicción.", "autor": "Nombre Analista", "autor_sub": "Head of Trading,
> Grupo Inteligencia"}` + `QUOTE_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "quote.html"`.

- [x] **2.1 Constante `PAYLOAD_QUOTE` + test de mapeo con cargo (AC3).**
  Agregar `PAYLOAD_QUOTE` y `QUOTE_TEMPLATE`. `test_quote_no_placeholders`:
  `build_html(PAYLOAD_QUOTE, QUOTE_TEMPLATE)` contiene el texto de `cita`/`autor`/`autor_sub`
  inyectado y **no** contiene ningún `{{` ni `}}`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC3)*: `uv run pytest tests/test_story_render.py::test_quote_no_placeholders`
    verde.

- [x] **2.2 Test de colapso `autor_sub == ""` (AC4).**
  `test_quote_autor_sub_vacio`: `build_html({**PAYLOAD_QUOTE, "autor_sub": ""}, QUOTE_TEMPLATE)`
  no contiene ningún `{{` ni `}}` (el token se sustituyó por cadena vacía, no se omitió el campo —
  CB-1). Complementa la aserción `rg ":empty"` de la tarea 1.3.
  - *Depende de*: **1.3** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC4)*: `uv run pytest tests/test_story_render.py::test_quote_autor_sub_vacio`
    verde.

- [x] **2.3 Test de render real con dimensiones (AC5).**
  `test_quote_render_dimensiones` con `@pytest.mark.skipif(not _chromium_disponible())`:
  `render_story(PAYLOAD_QUOTE, QUOTE_TEMPLATE, salida)` → el PNG existe, `> 5 KB` y
  `_png_size(...) == (1920, 1080)`. **No tocar** `conftest.py`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC5)*: `uv run pytest tests/test_story_render.py::test_quote_render_dimensiones`
    verde (o `skipped` sin Chromium). *Criterio suite*: `uv run pytest tests/test_story_render.py`
    verde en su totalidad.

---

## 3. Comando — `.claude/commands/story.md` (R5/R7)

- [x] **3.1 Registrar `[tipo]` `quote` en PASO 0 (R7).**
  Actualizar la lista dura de `[tipo]` (`story.md:6-8,18-26`) y el mensaje de tipos disponibles
  (`story.md:20-24`): de "único soportado: `alerta`" a "soportados: `alerta`, `quote`". Sin asumir
  tipo por defecto; el flag `ejecutivo` sigue avisado-y-continúa (CB-5, sin cambios).
  - *Depende de*: —
  - *Criterio ejecutable (AC7)*: `rg "quote" .claude/commands/story.md` ≥2 matches.

- [x] **3.2 Bloque de recolección editorial `quote` (R5/R7).**
  Ruta `quote` **sin** datos de mercado (no llama a `get_asset_levels` ni a comandos fuente):
  el director dicta la cita **o** el modelo redacta una propuesta editorial que el director
  aprueba/ajusta; `cita ≤ 220 caracteres` documentado como **guía de redacción** (no validación del
  motor — CB-2: no trunca ni aborta); cita recolectada **sin** comillas propias (R6/CB-3 — las pone
  el snapshot); preguntar `autor` y `autor_sub`, construir el payload con `autor_sub` **siempre
  presente** (`""` si no hay cargo, nunca omitir la clave — CB-1). Reusar el flujo compartido
  preview → aprobación (CB-4: si rechaza, no se renderiza ni guarda nada) → render →
  `scripts\ruta_story.ps1 ... -Plantilla "quote"` (activo `_general` al ser editorial sin activo
  protagonista) + `uv run python scripts/story_render.py --template templates/stories/quote.html
  --out "[ruta]"` (payload por stdin).
  - *Depende de*: **3.1**
  - *Criterios ejecutables (AC7/AC8)*: `rg "quote" .claude/commands/story.md` ≥2;
    `rg "220" .claude/commands/story.md` ≥1.

---

## 4. Documentación — `CLAUDE.md` (R9)

- [x] **4.1 Enumerar `quote` en la sección "Stories GI".**
  Cambiar la frase "Único `[tipo]` soportado hoy: `alerta`" por una que enumere también `quote`
  (ej. "`[tipo]` soportados hoy: `alerta`, `quote`"), sin tocar el resto del párrafo ni de la
  sección (regla "solo lectura" del canvas, guardado, gitignore quedan igual).
  - *Depende de*: —
  - *Criterio ejecutable (AC9)*: `rg "quote" CLAUDE.md` ≥1 match en la sección "Stories GI".

---

## 5. No-regresión (AC10)

- [x] **5.1 Confirmar motor / Alerta / helper intactos.**
  El motor, el snapshot de Alerta y el helper de guardado no se tocan (alcance 100% aditivo).
  - *Depende de*: — (confirmación final, no edición)
  - *Criterio ejecutable (AC10)*: `git diff master -- scripts/story_render.py
    templates/stories/alerta.html scripts/ruta_story.ps1` → **vacío**.

---

## Decisiones a elevar al gate humano DESIGN → APPLY

> Registradas en `design.md` §"Decisiones para el gate humano". El diseño ya fue aprobado por el
> director; se dejan trazadas como confirmaciones de bajo riesgo (los subagentes **nunca** aprueban
> el gate).

1. **[CONFIRMADA — bajo riesgo] `quote.html` sin clase de color direccional (`{{sesgo_slug}}`).**
   El `<body>` de `quote` usa clase estática (`class="quote"`): `quote` no trae `sesgo`/`variacion`,
   el helper 2 no puebla `sesgo_slug`, y referenciarlo dejaría un token huérfano que abortaría la
   guardia. Coherente con que `quote` es una pieza editorial sin sesgo de mercado.
2. **[CONFIRMADA — bajo riesgo] límite editorial `cita ≤ 220 caracteres`** como guía del comando
   (no validación del motor), sujeto a ajuste visual en `apply` (Riesgo B) al autorar el CSS real.

No hay preguntas bloqueantes abiertas: Q1-Q6 quedaron resueltas en `spec.md`.

---

## Restricciones duras (Apply)

- **NO tocar el motor** `scripts/story_render.py` ni el snapshot `templates/stories/alerta.html` ni
  `scripts/ruta_story.ps1` (AC10 exige `git diff master` vacío en esos tres).
- **NO tocar ni commitear** los 6 archivos ajenos del director: `.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
  `templates/encuesta_tendencia.txt`, `uv.lock`.
- **NUNCA** `git add -A` / `git add .` — solo los archivos de los grupos 1-4.
- **No** agregar dependencias (`pyproject.toml`/`uv.lock` sin cambios; Playwright ya opcional).
  **No** tocar `conftest.py`, agregar fixtures en `tests/fixtures/stories/*`, `src/market_data_mcp/**`
  ni `.claude/shared/modo_ejecutivo.md`.
- Regla "solo lectura" del canvas: `quote.html` se autora en el repo; no se sube nada al proyecto
  Claude Design.

## Verificación global (cierre del Change)

```
uv run pytest tests/test_story_render.py                       # AC3/AC4/AC5 (AC5 skipif sin Chromium)
rg "width: 1920px" templates/stories/quote.html                # AC1 → ≥1
rg "height: 1080px" templates/stories/quote.html               # AC1 → ≥1
rg "<!-- (IF|FOR):" templates/stories/quote.html               # AC2 → 0
rg ":empty" templates/stories/quote.html                       # AC4 → ≥1
rg "::before|::after|“|”|\\201C" templates/stories/quote.html  # AC6 → ≥1
rg "quote" .claude/commands/story.md                           # AC7 → ≥2
rg "220" .claude/commands/story.md                             # AC8 → ≥1
rg "quote" CLAUDE.md                                           # AC9 → ≥1 (sección Stories GI)
git diff master -- scripts/story_render.py templates/stories/alerta.html scripts/ruta_story.ps1  # AC10 → vacío
```

---

## Referencias

- `spec.md` (#121 — R1-R9, CB-1..CB-5, AC1-AC10, Q1-Q6 resueltas, riesgos A/B).
- `design.md` (#121 — technical approach, casos borde, mapa AC → verificación, desglose 1.1-5.1).
- `.pulse/changes/archive/119-.../tasks.md` — molde de este documento y motor generalizado (no
  reabierto).
- `templates/stories/alerta.html:14-58,398-409` — andamiaje de marca (fuentes/paleta/footer), base
  de `quote.html`.
- `tests/test_story_render.py` — patrón de `PAYLOAD_EJEMPLO` y tests de mapeo/render de `alerta`,
  base de los 3 tests nuevos.
- `.claude/commands/story.md:6-8,16-26` — comando a extender (PASO 0 + recolección).
- Issue #121 (`bbenja11/grupo-analisis-mercado`).
