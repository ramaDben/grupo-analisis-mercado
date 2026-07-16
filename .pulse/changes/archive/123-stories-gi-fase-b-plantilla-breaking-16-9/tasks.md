# Tasks — Stories GI · Fase B: plantilla Breaking 16:9 (#123)

> Desglose de implementación de `design.md` (Change #123, dominio `stories-gi`). Formaliza las
> tareas 1.1–5.1 del design, cada una mapeada a su requisito (`R1-R10`) y a su criterio de
> aceptación **ejecutable** (`AC1-AC11`, definidos en `spec.md`). Ordenadas por dependencia.
> **TDD**: escribir/ajustar el test antes de dar la tarea por cerrada. Toda la implementación se
> ejecuta en la fase **Apply** — este documento no contiene ni escribe código.

## Contrato heredado (no se reabre)

- Motor generalizado de Fase A (#119, `master` v0.2.0): `scripts/story_render.py`
  (`build_context`/`resolver_loops`/`_resolver_fences`/`_FENCES`/`render_png`) **intacto**.
  `breaking` es su segundo consumidor **sin** fences `IF`/`FOR` ni loops (tras `quote`) — tokens
  100% escalares incondicionales, con un único campo opcional (`kicker_tema`) resuelto por CSS,
  no por el motor. `_FENCES` sigue fija en `("variacion","vol","chart_img","chart_svg")`
  (`scripts/story_render.py:33`); ninguno aplica a `breaking`.
- Contrato de datos `story_alerta` y `story_quote` (`.pulse/specs/stories-gi/spec.md`) y los
  snapshots `templates/stories/alerta.html` y `templates/stories/quote.html`: **sin cambios**
  (AC11).
- Patrón de campo opcional (token + `:empty`) validado en Fase B/`quote` (#121): **reutilizado
  sin cambios** para `kicker_tema`.
- Fuente canónica de alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
  (fila 12, `breaking`, línea 70): payload `kicker_tema, titular, valor, contexto,
  parrafo_reaccion`, sin gráfico, fondo oscuro/rojo, fuente `/noticia` · `/alerta`.

## Archivos afectados (todos en Apply)

| Archivo | Requisitos | Grupo | Naturaleza |
|---|---|---|---|
| `templates/stories/breaking.html` (**nuevo**) | R1/R3/R4/R5 | 1 | snapshot 1920×1080 |
| `tests/test_story_render.py` (aditivo; **no** tocar `conftest.py`) | R9 | 2 | 3 tests nuevos |
| `.claude/commands/story.md` | R6/R7/R8 | 3 | PASO 0 + recolección editorial |
| `CLAUDE.md` (sección "Stories GI") | R10 | 4 | enumerar `breaking` |
| — (no-regresión, confirmación) | AC11 | 5 | `git diff` vacío |

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
  colapso `:empty` del chip).
- Los tests del grupo 2 se escriben **antes** de cerrar la tarea de snapshot que cubren (TDD):
  2.1/2.3 cubren 1.2; 2.2 cubre 1.3.
- **3.1 → 3.2**: registrar el `[tipo]` antes del bloque de recolección editorial en `story.md`.
- **4.1** y **5.1** son independientes del resto.

---

## 1. Snapshot — `templates/stories/breaking.html` (nuevo, R1/R3/R4/R5)

- [x] **1.1 Andamiaje de marca (R1).**
  Copiar **verbatim** el bloque `@font-face` + `html, body` de `alerta.html:14-58` (fuentes
  locales `fonts/*.woff2`: Syne 800 / DM Sans 400·700 / Space Grotesk 600; `* { box-sizing }`;
  fondo `#0D0D1A` con los mismos degradados radiales/lineales de `alerta.html:51-54` — radial
  `#2A1220`→`#0D0D1A` + linear `#0D0D1A`/`#120A12`/`#0D0D1A`; viewport 1920×1080;
  `color: #F5F3F7`; `font-family: "DM Sans"`; `overflow: hidden`) y el footer estándar
  (`@grupointeligencia` + `grupointeligencia.com` + disclaimer CFD, `alerta.html:398-409`,
  **sin** `{{fuente}}`). Comentario de cabecera "NO cambiar nombres de tokens sin actualizar
  tests". `<body class="breaking">` estático — **SIN** `{{sesgo_slug}}` ni ningún token de
  Alerta (referenciarlo dejaría un huérfano: `breaking` no trae `sesgo`, el helper 2 no puebla
  `sesgo_slug`).
  - *Depende de*: —
  - *Criterios ejecutables (AC1/AC2)*: `rg "width: 1920px" templates/stories/breaking.html` ≥1 y
    `rg "height: 1080px" templates/stories/breaking.html` ≥1;
    `rg "<!-- (IF|FOR):" templates/stories/breaking.html` → **0 matches**.

- [x] **1.2 Cuerpo editorial y tokens (R1/R2/R3/R5).**
  Contenedor raíz `.story` en columna (cuerpo + footer a lo ancho). `.breaking-cuerpo` en **una
  sola columna** centrada verticalmente (sin `.columna-grafico`, sin `#img-*`/`#svg-*`, sin
  `.contenedor-grafico`/`.rotulo-grafico`): `<span class="breaking-kicker">{{kicker_tema}}</span>`
  (chip acento rojo estilo `.chip-categoria` de Alerta — `background: rgba(232,64,64,0.14)`,
  `border: 1px solid rgba(232,64,64,0.5)`, `color: #F5A3A3`, `border-radius: 999px`, Space Grotesk
  mayúsculas), `<h1 class="breaking-titular">{{titular}}</h1>` (Syne 800, jerarquía del titular de
  Alerta), tarjeta `.breaking-cifra` con **rótulo estático "CIFRA CLAVE"** (`<span
  class="breaking-cifra-rotulo">CIFRA CLAVE</span>`, texto fijo del snapshot, **nunca** un token,
  estilo `.stat-label`) + `<span class="breaking-cifra-valor">{{valor}}</span>` (Syne 800 grande;
  borde/acento rojo estilo `.tarjeta-precio` — `border: 2px solid #E84040`, `background:
  rgba(232,64,64,0.08)`, `border-radius: 22px` — pero layout distinto: **SIN** `.tarjeta-cabecera`,
  `.precio-linea`, `.variacion`, `.stats`, flecha `▲/▼`, color condicional por dirección, fila de
  soporte/resistencia/vol ni rótulo de ticker/activo), `<p class="breaking-contexto">{{contexto}}</p>`,
  `<p class="breaking-reaccion">{{parrafo_reaccion}}</p>` (DM Sans). Los **únicos** cinco tokens
  `{{...}}` del archivo son `{{kicker_tema}}`, `{{titular}}`, `{{valor}}`, `{{contexto}}`,
  `{{parrafo_reaccion}}`. Sin fences `IF`/`FOR`.
  - *Depende de*: **1.1**
  - *Criterios ejecutables (AC3/AC6)*:
    `uv run pytest tests/test_story_render.py::test_breaking_no_placeholders` verde;
    `rg -i "CIFRA CLAVE" templates/stories/breaking.html` ≥1;
    `rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/breaking.html` → **0
    matches**.

- [x] **1.3 Colapso `:empty` de `kicker_tema` (R4).**
  Regla CSS sobre el contenedor del token: `.breaking-kicker:empty { display: none; }`. Con
  `kicker_tema` no vacío se muestra el chip sobre el titular. Con `kicker_tema == ""` el
  `<span class="breaking-kicker"></span>` queda vacío → `:empty` lo saca del flujo (`display: none`,
  colapsa el espacio, no solo el texto) → el titular sube sin hueco en blanco donde estaría el chip.
  Patrón exacto validado en `quote` R4 (`.quote-cargo:empty`).
  - *Depende de*: **1.2**
  - *Criterios ejecutables (AC4)*: `rg ":empty" templates/stories/breaking.html` ≥1;
    `uv run pytest tests/test_story_render.py::test_breaking_kicker_vacio` verde.
  - *Validación visual manual del director* (Riesgo A/B/C, no automatizada): aprobación en la primera
    corrida real de `/story breaking` (font-size/padding/espaciados, copy "CIFRA CLAVE" y límites de
    longitud se afinan en Apply). Los tests no asertan estética.

---

## 2. Tests — `tests/test_story_render.py` (aditivo, R9)

> No se toca `conftest.py` (el `sys.path.insert` de `scripts/` vive en el propio test). Sin fixture
> nuevo en `tests/fixtures/stories/` — se reusa el patrón contra el snapshot real `breaking.html`,
> igual que los tests de `alerta.html`/`quote.html`. `build_html` es puro (tokens 100% escalares) →
> testeable **sin Chromium**; solo AC5 usa render real con `skipif`. TDD: escribir el test antes de
> cerrar la tarea de snapshot que cubre. Constante propuesta, tras `PAYLOAD_QUOTE`
> (`tests/test_story_render.py:60-65`) y su ruta de snapshot tras `QUOTE_TEMPLATE`
> (`test_story_render.py:29`):
>
> ```python
> BREAKING_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "breaking.html"
>
> PAYLOAD_BREAKING: dict = {
>     "plantilla": "breaking",
>     "kicker_tema": "BANCOS CENTRALES",
>     "titular": "La Fed sorprende con una pausa más larga de lo esperado",
>     "valor": "5,50%",
>     "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
>     "parrafo_reaccion": (
>         "El mercado ajusta expectativas hacia un primer recorte más tardío, "
>         "presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
>     ),
> }
> ```
> El caso vacío usa `{**PAYLOAD_BREAKING, "kicker_tema": ""}`.

- [x] **2.1 Constante `PAYLOAD_BREAKING`/`BREAKING_TEMPLATE` + test de mapeo con kicker (AC3).**
  Agregar `BREAKING_TEMPLATE` y `PAYLOAD_BREAKING`. `test_breaking_no_placeholders`:
  `build_html(PAYLOAD_BREAKING, BREAKING_TEMPLATE)` contiene el texto de
  `kicker_tema`/`titular`/`valor`/`contexto`/`parrafo_reaccion` inyectado y **no** contiene ningún
  `{{` ni `}}`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC3)*:
    `uv run pytest tests/test_story_render.py::test_breaking_no_placeholders` verde.

- [x] **2.2 Test de colapso `kicker_tema == ""` (AC4).**
  `test_breaking_kicker_vacio`: `build_html({**PAYLOAD_BREAKING, "kicker_tema": ""},
  BREAKING_TEMPLATE)` no contiene ningún `{{` ni `}}` (el token se sustituyó por cadena vacía, no
  se omitió el campo — CB-1). Complementa la aserción `rg ":empty"` de la tarea 1.3.
  - *Depende de*: **1.3** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC4)*:
    `uv run pytest tests/test_story_render.py::test_breaking_kicker_vacio` verde.

- [x] **2.3 Test de render real con dimensiones (AC5).**
  `test_breaking_render_dimensiones` con `@pytest.mark.skipif(not _chromium_disponible())`:
  `render_story(PAYLOAD_BREAKING, BREAKING_TEMPLATE, salida)` → el PNG existe, `> 5 KB` y
  `_png_size(...) == (1920, 1080)`. **No tocar** `conftest.py`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC5)*:
    `uv run pytest tests/test_story_render.py::test_breaking_render_dimensiones` verde (o `skipped`
    sin Chromium). *Criterio suite*: `uv run pytest tests/test_story_render.py` verde en su
    totalidad.

---

## 3. Comando — `.claude/commands/story.md` (R6/R7/R8)

- [x] **3.1 Registrar `[tipo]` `breaking` en PASO 0 (R7).**
  Actualizar la lista dura de `[tipo]` (`story.md:6-8,17-29`) y el mensaje de tipos disponibles
  (`story.md:20-25`): de "soportados: `alerta`, `quote`" a "soportados: `alerta`, `quote`,
  `breaking`". Si el tipo confirmado es `breaking`, rutear al bloque "Ruta `breaking`" (los PASO
  1-7 son de `alerta`; el bloque "Ruta `quote`" es de `quote`). Sin asumir tipo por defecto; el
  flag `ejecutivo` sigue avisado-y-continúa (CB-4, sin cambios).
  - *Depende de*: —
  - *Criterio ejecutable (AC7)*: `rg "breaking" .claude/commands/story.md` ≥2 matches (uno en la
    lista de PASO 0, otro en el bloque "Ruta `breaking`").

- [x] **3.2 Bloque de recolección editorial "Ruta `breaking`" (R6/R7/R8).**
  Hermano de "Ruta `quote`". Ruta `breaking` **sin** datos de mercado (no llama a `get_asset_levels`
  ni a ningún comando/tool de datos) y **sin búsqueda propia de evento** (no reusa el WebSearch de
  `/alerta` PASO 1 ni su mecanismo de detección de noticias — R7.2, resuelve Q4). Flujo:
  - **Fuente editorial (R7.1 · CB-5)**: preguntar si el director ya corrió `/noticia`/`/alerta` en
    la misma sesión (o tiene el evento/cifra redactado) → si es así, reutiliza esos textos como
    base; si no, pide que dicte directamente los campos. No bloquea ni exige corrida previa (atajo
    opcional, no dependencia dura).
  - **Dirección explícita (R7.3, regla de oro)**: titular/contexto/reacción dejan clara la lectura
    direccional del evento (qué activo/mercado se afecta y hacia dónde), con registro profesional
    del repo (énfasis sin dramatización, `CLAUDE.md` "Registro y tono").
  - **Límites editoriales (R6)**: documentar `kicker_tema ≤ 30`, `titular ≤ 70`, `contexto ≤ 100`,
    `parrafo_reaccion ≤ 280` caracteres como **guía de redacción** del comando, **no** validación
    del motor (CB-2: no trunca ni aborta por longitud); si algún campo excede, el comando ajusta la
    redacción antes del preview.
  - **Payload (R7.4 · CB-1)**: construir con `kicker_tema` **siempre presente** — si no hay
    tema/categoría claro, `"kicker_tema": ""` (nunca omitir la clave). Los otros cuatro campos
    (`titular`/`valor`/`contexto`/`parrafo_reaccion`) siempre no vacíos. `valor` recolectado ya
    formateado con su unidad si aplica (`"5,50%"`, `"US$ 2.318"`, CB-6); **no** lleva `digits` de
    `config/activos.json` (no es un precio del motor).
  - **Guardado con o sin `-Activo` (R8 · resuelve Q5 · CB-7)**: preguntar si la noticia tiene un
    activo protagonista claro (decisión **editorial** del director, no regla automática nueva ni del
    motor ni de `ruta_story.ps1`): **Sí** → `-Activo [TICKER_MT5]` (normalizado contra
    `config/activos.json`, mismo criterio que `/chart` PASO 1); **No / ambiguo / múltiples activos**
    → `-Activo "_general"` (igual que `quote`).
  - Reusar el flujo compartido preview → aprobación (CB-3: si rechaza, no se renderiza ni guarda
    nada en `data/stories/`) → render → guardado con:
    ```powershell
    scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5 o _general]" -Plantilla "breaking" -Hora "[HH-mm]"
    ```
    y `uv run python scripts/story_render.py --template templates/stories/breaking.html --out
    "[ruta]"` (payload `story_breaking` por stdin). `[Hora]` sale del reloj de Chile (regla
    canónica). Mismo manejo de éxito/error que el PASO 7 de `alerta`.
  - *Depende de*: **3.1**
  - *Criterios ejecutables (AC7/AC8/AC9)*: `rg "breaking" .claude/commands/story.md` ≥2;
    `rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30" .claude/commands/story.md` ≥1;
    `rg -i "no ejecuta su propia búsqueda|no busca por cuenta propia|no reusa" .claude/commands/story.md`
    ≥1 dentro del bloque "Ruta `breaking`".

---

## 4. Documentación — `CLAUDE.md` (R10)

- [x] **4.1 Enumerar `breaking` en la sección "Stories GI".**
  Cambiar la enumeración de `[tipo]` soportados (hoy `alerta`, `quote`) por una que incluya también
  `breaking` (ej. "`[tipo]` soportados hoy: `alerta`, `quote`, `breaking`"), sin tocar el resto del
  párrafo ni de la sección (regla "solo lectura" del canvas, guardado, gitignore quedan igual).
  - *Depende de*: —
  - *Criterio ejecutable (AC10)*: `rg "breaking" CLAUDE.md` ≥1 match en la sección "Stories GI".

---

## 5. No-regresión (AC11)

- [x] **5.1 Confirmar motor / Alerta / Quote / helper intactos.**
  El motor, los snapshots de Alerta y Quote y el helper de guardado no se tocan (alcance 100%
  aditivo).
  - *Depende de*: — (confirmación final, no edición)
  - *Criterio ejecutable (AC11)*: `git diff master -- scripts/story_render.py
    templates/stories/alerta.html templates/stories/quote.html scripts/ruta_story.ps1` → **vacío**.

---

## Decisiones a elevar al gate humano DESIGN → APPLY

> Registradas en `design.md` §"Decisiones para el gate humano". El diseño ya fue aprobado por el
> director; se dejan trazadas como confirmaciones de bajo riesgo (los subagentes **nunca** aprueban
> el gate; el gate `DESIGN → APPLY` requiere aprobación humana explícita).

1. **[CONFIRMADA — bajo riesgo] `breaking.html` sin clase de color direccional (`{{sesgo_slug}}`).**
   El `<body>` de `breaking` usa clase estática (`class="breaking"`): `breaking` no trae
   `sesgo`/`variacion`, el helper 2 no puebla `sesgo_slug`, y referenciarlo dejaría un token
   huérfano que abortaría la guardia. La dirección se comunica en el texto (R7.3). Coherente con que
   la cifra es editorial, no un dato de mercado en vivo.
2. **[CONFIRMADA — bajo riesgo] rótulo estático "CIFRA CLAVE" y tarjeta sin
   variación/flecha/soporte/resistencia/vol** (R5), para no sugerir un dato en vivo del motor. Copy
   y tratamiento sujetos a ajuste visual en `apply` (Riesgo B).
3. **[CONFIRMADA — bajo riesgo] límites editoriales `kicker_tema ≤ 30`, `titular ≤ 70`,
   `contexto ≤ 100`, `parrafo_reaccion ≤ 280`** como guía del comando (no validación del motor),
   sujetos a ajuste visual en `apply` (Riesgo C).

No hay preguntas bloqueantes abiertas: Q1-Q5 quedaron resueltas en `spec.md`.

---

## Restricciones duras (Apply)

- **NO tocar el motor** `scripts/story_render.py` ni los snapshots `templates/stories/alerta.html`
  y `templates/stories/quote.html` ni `scripts/ruta_story.ps1` (AC11 exige `git diff master` vacío
  en esos cuatro).
- **NO tocar ni commitear** los 6 archivos ajenos del director: `.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
  `templates/encuesta_tendencia.txt`, `uv.lock`.
- **NUNCA** `git add -A` / `git add .` — solo los archivos de los grupos 1-4.
- **No** agregar dependencias (`pyproject.toml`/`uv.lock` sin cambios; Playwright ya opcional).
  **No** tocar `conftest.py`, agregar fixtures en `tests/fixtures/stories/*`, `src/market_data_mcp/**`
  ni `.claude/shared/modo_ejecutivo.md`. **No** agregar sección de mapeo dedicada a `breaking` en
  `docs/design/stories-gi/plantillas-stories-gi.md` (OUT del spec).
- **No** usar fences `IF`/`FOR` en `breaking.html`; el único campo opcional (`kicker_tema`) se
  resuelve por CSS `:empty`, no por el motor.
- Regla "solo lectura" del canvas: `breaking.html` se autora en el repo; no se sube nada al proyecto
  Claude Design.

## Verificación global (cierre del Change)

```
uv run pytest tests/test_story_render.py                             # AC3/AC4/AC5 (AC5 skipif sin Chromium)
rg "width: 1920px" templates/stories/breaking.html                  # AC1 → ≥1
rg "height: 1080px" templates/stories/breaking.html                 # AC1 → ≥1
rg "<!-- (IF|FOR):" templates/stories/breaking.html                 # AC2 → 0
rg ":empty" templates/stories/breaking.html                         # AC4 → ≥1
rg -i "CIFRA CLAVE" templates/stories/breaking.html                 # AC6 → ≥1
rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/breaking.html  # AC6 → 0
rg "breaking" .claude/commands/story.md                             # AC7 → ≥2
rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30" .claude/commands/story.md            # AC8 → ≥1
rg -i "no ejecuta su propia búsqueda|no busca por cuenta propia|no reusa" .claude/commands/story.md  # AC9 → ≥1
rg "breaking" CLAUDE.md                                             # AC10 → ≥1 (sección Stories GI)
git diff master -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html scripts/ruta_story.ps1  # AC11 → vacío
```

---

## Referencias

- `spec.md` (#123 — R1-R10, CB-1..CB-7, AC1-AC11, Q1-Q5 resueltas, riesgos A/B/C).
- `design.md` (#123 — technical approach, casos borde, mapa AC → verificación, desglose 1.1-5.1).
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/tasks.md` — molde directo de
  este documento; patrón de campo opcional (token + `:empty`) reutilizado sin cambios.
- `.pulse/changes/archive/119-.../spec.md` — contrato del motor generalizado (no reabierto).
- `templates/stories/alerta.html:14-58,92-115,145-231,398-409` — andamiaje de marca
  (fuentes/paleta/footer), chip `.chip-categoria` y tarjeta `.tarjeta-precio` (acentos rojos
  `#E84040`), base de `breaking.html` para chip y tarjeta de cifra (con layout distinto).
- `templates/stories/quote.html` — molde más cercano de plantilla simple sin fences/loops, con campo
  opcional resuelto vía `:empty` CSS (`.quote-cargo:empty`).
- `tests/test_story_render.py:29,60-65,295-326` — patrón de `PAYLOAD_QUOTE`, tests de mapeo de
  `quote` y test de render con `skipif`, base de los 3 tests nuevos.
- `.claude/commands/story.md:6-8,17-104` — comando a extender (PASO 0 + bloque "Ruta `quote`" como
  molde del bloque "Ruta `breaking`").
- `CLAUDE.md` sección "Stories GI" — enumeración de `[tipo]`.
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 12 `breaking`
  (contrato de campos canónico).
- Issue #123 (`bbenja11/grupo-analisis-mercado`) — issue madre; #121 (quote) y #119 (motor)
  precedentes.
