# Tasks — Stories GI · Fase B: plantilla Encuesta 16:9 (#125)

> Desglose de implementación de `design.md` (Change #125, dominio `stories-gi`). Formaliza las
> tareas 1.1–5.1 del design, cada una mapeada a su requisito (`R1-R10`) y a su criterio de
> aceptación **ejecutable** (`AC1-AC12`, definidos en `spec.md`). Ordenadas por dependencia.
> **TDD**: escribir/ajustar el test antes de dar la tarea por cerrada. Toda la implementación se
> ejecuta en la fase **Apply** — este documento no contiene ni escribe código.

## Contrato heredado (no se reabre)

- Motor generalizado de Fase A (#119, `master` v0.2.0): `scripts/story_render.py`
  (`build_context`/`resolver_loops`/`_resolver_fences`/`_FENCES`/`render_png`) **intacto**.
  `encuesta` es su **cuarto** consumidor **sin** fences `IF`/`FOR` ni loops (tras `quote` y
  `breaking`) — tokens 100% escalares incondicionales, con **dos** campos opcionales
  (`kicker`, `nota_cierre`) resueltos por CSS `:empty`, no por el motor. `_FENCES` sigue fija en
  `("variacion","vol","chart_img","chart_svg")` (`scripts/story_render.py:29`); ninguno aplica a
  `encuesta`.
- Contrato de datos `story_alerta`, `story_quote` y `story_breaking`
  (`.pulse/specs/stories-gi/spec.md`) y los snapshots `templates/stories/alerta.html`,
  `templates/stories/quote.html` y `templates/stories/breaking.html`: **sin cambios** (AC12).
- Patrón de campo opcional (token + `:empty`) validado en Fase B/`quote` (#121, `.quote-cargo`) y
  replicado en Fase B/`breaking` (#123, `.breaking-kicker`): **reutilizado sin cambios** — ahora
  por partida doble (`kicker` y `nota_cierre`).
- `encuesta` es 100% sentimiento editorial, mismo contrato que `/encuesta` (`CLAUDE.md`
  "Encuestas diarias": sentimiento puro, sin precios ni educación) — **no** delega en ningún dato
  en vivo del motor (`get_asset_levels`, `obtener_calendario_macro`, etc.) ni ejecuta búsqueda de
  evento (WebSearch).
- Fuente canónica de alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
  (fila 09, `encuesta`, línea 67): payload `kicker, pregunta, opcion_a, opcion_b, nota_cierre`,
  sin gráfico, fondo oscuro/**azul**, fuente `/encuesta`.

## Archivos afectados (todos en Apply)

| Archivo | Requisitos | Grupo | Naturaleza |
|---|---|---|---|
| `templates/stories/encuesta.html` (**nuevo**) | R1/R3/R4/R5 | 1 | snapshot 1920×1080, paleta azul |
| `tests/test_story_render.py` (aditivo; **no** tocar `conftest.py`) | R9 | 2 | 4 tests nuevos |
| `.claude/commands/story.md` | R6/R7/R8 | 3 | PASO 0 + recolección editorial |
| `CLAUDE.md` (sección "Stories GI") | R10 | 4 | enumerar `encuesta` |
| — (no-regresión, confirmación) | AC12 | 5 | `git diff` vacío |

## Grafo de dependencias (orden de ejecución)

```
1.1 ──> 1.2 ──> 1.3 ──(validación visual manual del director · Riesgos A/B/C/D)
                 │
2.1 (cubre 1.2) ─┤     2.1 depende de 1.2 · 2.2 depende de 1.3 · 2.3 depende de 1.3 · 2.4 depende de 1.2
2.2 (cubre 1.3) ─┤
2.3 (cubre 1.3) ─┤
2.4 (cubre 1.2) ─┘
3.1 (indep.) ──> 3.2
4.1 (indep.)
5.1 (indep., confirmación final)
```

- **1.1 → 1.2 → 1.3**: el snapshot se autora incrementalmente (andamiaje + paleta azul → cuerpo
  editorial "A vs B" + tokens → doble colapso `:empty` de `kicker` y `nota_cierre`).
- Los tests del grupo 2 se escriben **antes** de cerrar la tarea de snapshot que cubren (TDD):
  2.1/2.4 cubren 1.2; 2.2/2.3 cubren 1.3.
- **3.1 → 3.2**: registrar el `[tipo]` antes del bloque de recolección editorial en `story.md`.
- **4.1** y **5.1** son independientes del resto.

---

## 1. Snapshot — `templates/stories/encuesta.html` (nuevo, R1/R3/R4/R5)

- [x] **1.1 Andamiaje de marca + paleta azul FIJADA (R1).**
  Copiar **verbatim** el bloque `@font-face` + `html, body` + `.story` de `breaking.html:20-72`
  (fuentes locales `fonts/*.woff2`: Syne 800 / DM Sans 400·700 / Space Grotesk 600;
  `* { box-sizing }`; viewport 1920×1080; `color: #F5F3F7`; `font-family: "DM Sans"`;
  `overflow: hidden`; `.story { padding: 56px 72px 40px; display:flex; flex-direction:column }`) y
  el footer estándar (`@grupointeligencia` + `grupointeligencia.com` + disclaimer CFD **verbatim**,
  **sin** `{{fuente}}`). **Única diferencia con `breaking.html`**: sustituir el degradado rojizo por
  la variante **azul FIJADA** (todos los neutros idénticos):
  ```css
  html, body {
    background: #0D0D1A;
    background-image:
      radial-gradient(90% 120% at 0% 20%, #1E3A5F 0%, #0D0D1A 55%),
      linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #1E3A5F 100%);
    color: #F5F3F7;
  }
  ```
  Comentario de cabecera "NO cambiar nombres de tokens sin actualizar tests". `<body
  class="encuesta">` estático — **SIN** `{{sesgo_slug}}` ni ningún token de Alerta (referenciarlo
  dejaría un huérfano: `encuesta` no trae `sesgo`, el helper de `sesgo_slug` no se dispara).
  - *Depende de*: —
  - *Criterios ejecutables (AC1/AC2)*: `rg "width: 1920px" templates/stories/encuesta.html` ≥1 y
    `rg "height: 1080px" templates/stories/encuesta.html` ≥1;
    `rg "<!-- (IF|FOR):" templates/stories/encuesta.html` → **0 matches**.

- [x] **1.2 Cuerpo editorial "A vs B" y tokens (R1/R2/R3/R5).**
  Contenedor raíz `.story` en columna (cuerpo + footer). `.encuesta-cuerpo` en **una sola columna**
  centrada (`flex:1; align-items:center; justify-content:center; text-align:center`; sin
  `.columna-grafico`, sin `#img-*`/`#svg-*`, sin `.contenedor-grafico`):
  - `<span class="encuesta-kicker">{{kicker}}</span>` — chip acento **azul** estilo
    `.chip-categoria` de Alerta pero en azul (`color: #53C1AB`, `background:
    rgba(62,145,175,0.14)`, `border: 1px solid rgba(62,145,175,0.5)`, `border-radius: 999px`,
    Space Grotesk mayúsculas, `letter-spacing: 0.06em`).
  - `<h1 class="encuesta-pregunta">{{pregunta}}</h1>` — Syne 800, `#FFFFFF`, jerarquía de titular
    (`~56px`, `line-height: 1.2`, `max-width: 1400px`), núcleo obligatorio.
  - `<div class="encuesta-opciones">` (flex row, `gap`, `align-items:stretch;
    justify-content:center`) con **dos** `.encuesta-opcion` gemelas simétricas y un separador
    estático `<span class="encuesta-vs">VS</span>` (Space Grotesk 600, `#3E91AF`) al centro. Cada
    `.encuesta-opcion` es tarjeta estilo `.tarjeta-precio`/`.breaking-cifra` en azul (`border: 2px
    solid #3E91AF`, `background: rgba(62,145,175,0.08)`, `border-radius: 22px`), con layout "rótulo
    estático + valor": `<span class="encuesta-opcion-rotulo">OPCIÓN A</span>` / `OPCIÓN B` (texto
    fijo del snapshot, **nunca** un token, estilo `.stat-label`, `#A9A5B4`) + `<span
    class="encuesta-opcion-valor">{{opcion_a}}</span>` / `{{opcion_b}}` (Syne 800, `#FFFFFF`,
    `~44px`). **SIN** `.tarjeta-cabecera`, `.precio-linea`, `.variacion`, `.stats`, flecha `▲/▼`,
    color condicional por dirección, fila de soporte/resistencia/vol ni rótulo de ticker/activo.
  - `<p class="encuesta-nota">{{nota_cierre}}</p>` — DM Sans 400, `#C9C5D4`, `~21px`.
  Los **únicos** cinco tokens `{{...}}` del archivo son `{{kicker}}`, `{{pregunta}}`,
  `{{opcion_a}}`, `{{opcion_b}}`, `{{nota_cierre}}`. Sin fences `IF`/`FOR`.
  - *Depende de*: **1.1**
  - *Criterios ejecutables (AC3/AC7)*:
    `uv run pytest tests/test_story_render.py::test_encuesta_no_placeholders` verde;
    `rg -i "OPCIÓN A" templates/stories/encuesta.html` ≥1 y `rg -i "OPCIÓN B" …` ≥1 y
    `rg "VS" …` ≥1;
    `rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/encuesta.html` → **0
    matches**.

- [x] **1.3 Doble colapso `:empty` de `kicker` y `nota_cierre` (R4).**
  Dos reglas CSS, una por campo opcional:
  ```css
  .encuesta-kicker:empty { display: none; }
  .encuesta-nota:empty   { display: none; }
  ```
  Con el campo no vacío se muestra el elemento (chip sobre la pregunta / línea bajo las opciones).
  Con el campo `== ""` el contenedor queda vacío → `:empty` lo saca del flujo (`display: none`,
  colapsa el espacio, no solo el texto) → el layout se reacomoda sin hueco en blanco. Patrón exacto
  validado en `quote` R4 (`.quote-cargo:empty`) y `breaking` R4 (`.breaking-kicker:empty`).
  - *Depende de*: **1.2**
  - *Criterios ejecutables (AC4/AC5)*: `rg ":empty" templates/stories/encuesta.html` **≥2**;
    `uv run pytest tests/test_story_render.py::test_encuesta_kicker_vacio` y
    `uv run pytest tests/test_story_render.py::test_encuesta_nota_vacio` verdes.
  - *Validación visual manual del director* (Riesgos A/B/C/D, no automatizada): aprobación en la
    primera corrida real de `/story encuesta` (paleta azul FIJADA `#1E3A5F`/`#3E91AF`/`#53C1AB`,
    copy "OPCIÓN A"/"OPCIÓN B"/"VS", font-size/padding/anchos y límites de longitud se afinan en
    Apply). Los tests no asertan estética.

---

## 2. Tests — `tests/test_story_render.py` (aditivo, R9)

> No se toca `conftest.py` (el `sys.path.insert` de `scripts/` vive en el propio test). Sin fixture
> nuevo en `tests/fixtures/stories/` — se reusa el patrón contra el snapshot real `encuesta.html`,
> igual que los tests de `alerta.html`/`quote.html`/`breaking.html`. `build_html` es puro (tokens
> 100% escalares) → testeable **sin Chromium**; solo AC6 usa render real con `skipif`. TDD:
> escribir el test antes de cerrar la tarea de snapshot que cubre. Los cuatro tests se
> **append**-ean al final del archivo, tras el bloque de `breaking` (`test_story_render.py:382`),
> con su propio separador de sección
> (`# --- AC3/AC4/AC5/AC6 (#125): snapshot templates/stories/encuesta.html ---`). Constantes
> propuestas, tras `PAYLOAD_BREAKING` (`test_story_render.py:71-81`) y su ruta de snapshot tras
> `BREAKING_TEMPLATE` (`test_story_render.py:30`):
>
> ```python
> ENCUESTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "encuesta.html"
>
> PAYLOAD_ENCUESTA: dict = {
>     "plantilla": "encuesta",
>     "kicker": "ENCUESTA DEL DÍA",
>     "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
>     "opcion_a": "Alcista",
>     "opcion_b": "Bajista",
>     "nota_cierre": "Vota en la encuesta fijada del grupo",
> }
> ```
> Los casos vacíos usan `{**PAYLOAD_ENCUESTA, "kicker": ""}` y
> `{**PAYLOAD_ENCUESTA, "nota_cierre": ""}`.

- [x] **2.1 Constantes `ENCUESTA_TEMPLATE`/`PAYLOAD_ENCUESTA` + test de mapeo completo (AC3).**
  Agregar `ENCUESTA_TEMPLATE` y `PAYLOAD_ENCUESTA`. `test_encuesta_no_placeholders`:
  `build_html(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE)` contiene el texto de
  `kicker`/`pregunta`/`opcion_a`/`opcion_b`/`nota_cierre` inyectado y **no** contiene ningún `{{`
  ni `}}`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC3)*:
    `uv run pytest tests/test_story_render.py::test_encuesta_no_placeholders` verde.

- [x] **2.2 Test de colapso `kicker == ""` (AC4).**
  `test_encuesta_kicker_vacio`: `build_html({**PAYLOAD_ENCUESTA, "kicker": ""}, ENCUESTA_TEMPLATE)`
  no contiene ningún `{{` ni `}}` (el token se sustituyó por cadena vacía, no se omitió el campo —
  CB-1). Complementa la aserción `rg ":empty"` de la tarea 1.3.
  - *Depende de*: **1.3** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC4)*:
    `uv run pytest tests/test_story_render.py::test_encuesta_kicker_vacio` verde.

- [x] **2.3 Test de colapso `nota_cierre == ""` (AC5).**
  `test_encuesta_nota_vacio`: `build_html({**PAYLOAD_ENCUESTA, "nota_cierre": ""},
  ENCUESTA_TEMPLATE)` no contiene ningún `{{` ni `}}` (segundo campo opcional, mismo criterio que
  2.2 — CB-1).
  - *Depende de*: **1.3** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC5)*:
    `uv run pytest tests/test_story_render.py::test_encuesta_nota_vacio` verde.

- [x] **2.4 Test de render real con dimensiones (AC6).**
  `test_encuesta_render_dimensiones` con `@pytest.mark.skipif(not _chromium_disponible())`:
  `render_story(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE, salida)` → el PNG existe, `> 5 KB` y
  `_png_size(...) == (1920, 1080)`. **No tocar** `conftest.py`.
  - *Depende de*: **1.2** (código) — se escribe antes (TDD).
  - *Criterio ejecutable (AC6)*:
    `uv run pytest tests/test_story_render.py::test_encuesta_render_dimensiones` verde (o `skipped`
    sin Chromium). *Criterio suite*: `uv run pytest tests/test_story_render.py` verde en su
    totalidad.

---

## 3. Comando — `.claude/commands/story.md` (R6/R7/R8)

- [x] **3.1 Registrar `[tipo]` `encuesta` en PASO 0 (R7).**
  Actualizar la lista dura de `[tipo]` (`story.md:6-8,21-32`) y el mensaje de tipos disponibles: de
  "soportados: `alerta`, `quote`, `breaking`" a "soportados: `alerta`, `quote`, `breaking`,
  `encuesta`". Si el tipo confirmado es `encuesta`, rutear al bloque "Ruta `encuesta`" (los PASO
  1-7 son de `alerta`; los bloques "Ruta `quote`"/"Ruta `breaking`" son de esos tipos). Sin asumir
  tipo por defecto; el mensaje de tipo inválido (CB-5) lista los cuatro; el flag `ejecutivo` sigue
  avisado-y-continúa (CB-4, sin cambios).
  - *Depende de*: —
  - *Criterio ejecutable (AC8)*: `rg "encuesta" .claude/commands/story.md` ≥2 matches (uno en la
    lista de PASO 0, otro en el bloque "Ruta `encuesta`").

- [x] **3.2 Bloque de recolección editorial "Ruta `encuesta`" (R6/R7/R8).**
  Hermano de "Ruta `breaking`", tras `story.md:195`. Ruta `encuesta` **sin** datos de mercado (no
  llama a `get_asset_levels` ni a ninguna tool de mercado — `obtener_calendario_macro`,
  `get_chart_objects`, `get_symbol_spec`) y **sin búsqueda propia de evento** (no invoca WebSearch)
  — es una pieza 100% editorial de **sentimiento puro**, mismo contrato que `/encuesta` (R7.2,
  resuelve AC10). Flujo:
  - **Recolección editorial (R7.1)**: preguntar la pregunta binaria y sus dos opciones con el
    criterio de sentimiento puro de `/encuesta` (sin precios ni educación):
    ```
    ¿Cuál es la pregunta de la encuesta? (ej. "¿Cuál creen que será la tendencia hoy del Oro?")
    ¿Opción A?
    ¿Opción B?
    ¿Kicker/tema del chip? (ej. "ENCUESTA DEL DÍA" — Intro para omitir)
    ¿Nota de cierre? (ej. "Vota en la encuesta fijada del grupo" — Intro para omitir)
    ```
  - **Atajo opcional (R7.3 · CB-8)**: si el director ya corrió `/encuesta [tipo] [activo]` en la
    misma sesión, ofrecer reutilizar esa pregunta/opciones ya redactadas como base editorial — no
    bloquea ni exige corrida previa; si prefiere redactar de cero, lo hace directamente.
  - **Layout binario único (R7.4)**: la Story usa siempre el mismo layout `opcion_a`/`opcion_b` sin
    distinguir entre los 3 tipos de `/encuesta` (`posicion`/`tendencia`/`movimiento`) — el tipo de
    origen se refleja en la **redacción** de la pregunta/opciones, no en el layout.
  - **Límites editoriales (R6)**: documentar `kicker ≤ 30`, `pregunta ≤ 90`, `opcion_a ≤ 25`,
    `opcion_b ≤ 25`, `nota_cierre ≤ 80` caracteres como **guía de redacción** del comando, **no**
    validación del motor (CB-2: no trunca ni aborta por longitud); si algún campo excede, el comando
    ajusta la redacción antes del preview.
  - **Payload (R7.5 · CB-1)**: construir con `kicker` y `nota_cierre` **siempre presentes** — si el
    director no da alguno, `""` (nunca omitir la clave). Los otros tres campos
    (`pregunta`/`opcion_a`/`opcion_b`) siempre no vacíos; si el director no puede dar alguno, el
    comando insiste, nunca cadena vacía en esos tres.
  - **Guardado con o sin `-Activo` (R8 · CB-6)**: preguntar si la pregunta nombra un activo
    protagonista claro (decisión **editorial** del director, no regla automática nueva ni del motor
    ni de `ruta_story.ps1`):
    ```
    ¿La pregunta tiene un activo protagonista claro? (ticker, o "no" si es general/ambigua)
    ```
    **Sí** (ej. "…tendencia hoy del Oro" → Oro) → `-Activo [TICKER_MT5]` (normalizado contra
    `config/activos.json`, mismo criterio que `/chart` PASO 1); **No / ambiguo / múltiples activos**
    (ej. "¿Suben o bajan los mercados esta semana?") → `-Activo "_general"` (igual que
    `quote`/`breaking`).
  - Reusar el flujo compartido preview → aprobación (CB-3: si rechaza, no se renderiza ni guarda
    nada en `data/stories/`) → render → guardado con:
    ```powershell
    scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5 o _general]" -Plantilla "encuesta" -Hora "[HH-mm]"
    ```
    y `uv run python scripts/story_render.py --template templates/stories/encuesta.html --out
    "[ruta]"` (payload `story_encuesta` por stdin). `[Hora]` sale del reloj de Chile (regla
    canónica). Mismo manejo de éxito/error que el PASO 7 de `alerta`.
  - **Preview específico** (espejo del preview de `breaking`):
    ```
    📖 *PREVIEW — Story Encuesta*
    ━━━━━━━━━━━━━━━━━━━
    Kicker: [kicker o "(sin kicker)"]
    Pregunta: [pregunta]
    Opción A: [opcion_a]   |   Opción B: [opcion_b]
    Nota: [nota_cierre o "(sin nota)"]
    ━━━━━━━━━━━━━━━━━━━
    ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
    ```
  - *Depende de*: **3.1**
  - *Criterios ejecutables (AC8/AC9/AC10)*: `rg "encuesta" .claude/commands/story.md` ≥2;
    `rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" .claude/commands/story.md` ≥1;
    `rg -i "no llama a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado" .claude/commands/story.md`
    ≥1 dentro del bloque "Ruta `encuesta`".

---

## 4. Documentación — `CLAUDE.md` (R10)

- [x] **4.1 Enumerar `encuesta` en la sección "Stories GI".**
  Cambiar la enumeración de `[tipo]` soportados (hoy "`alerta`, `quote`, `breaking` (Fase B, issues
  #121/#123)") por una que incluya también `encuesta` (ej. "…`alerta`, `quote`, `breaking`,
  `encuesta` (Fase B, issues #121/#123/#125)"), sin tocar el resto del párrafo ni de la sección
  (regla "solo lectura" del canvas, guardado, gitignore quedan igual). (Opcional, consistencia — no
  exigido por AC11) refrescar la fila `/story [tipo]` de la tabla "Slash Commands", desactualizada
  desde #121/#123, a "`[tipo]` soportados hoy: `alerta`, `quote`, `breaking`, `encuesta`".
  - *Depende de*: —
  - *Criterio ejecutable (AC11)*: `rg "encuesta" CLAUDE.md` ≥1 match en la sección "Stories GI"
    (distinguible por contexto de las menciones ya existentes al comando `/encuesta` de texto plano).

---

## 5. No-regresión (AC12)

- [x] **5.1 Confirmar motor / Alerta / Quote / Breaking / helper intactos.**
  El motor, los snapshots de Alerta, Quote y Breaking y el helper de guardado no se tocan (alcance
  100% aditivo).
  - *Depende de*: — (confirmación final, no edición)
  - *Criterio ejecutable (AC12)*: `git diff master -- scripts/story_render.py
    templates/stories/alerta.html templates/stories/quote.html templates/stories/breaking.html
    scripts/ruta_story.ps1` → **vacío**.

---

## Decisiones a elevar al gate humano DESIGN → APPLY

> Registradas en `design.md` §"Decisiones para el gate humano". El diseño ya fue aprobado por el
> director; se dejan trazadas como confirmaciones de bajo riesgo (los subagentes **nunca** aprueban
> el gate; el gate `DESIGN → APPLY` requiere aprobación humana explícita).

1. **[CONFIRMAR — único material] Paleta azul FIJADA sin render azul de referencia.** `alerta.html`
   **no tiene azul** (Hallazgo previo del design); este design fija, desde los candidatos
   repo-present de `spec.md`/`idea.md`: `#1E3A5F` (fondo/tinte radial), `#3E91AF` (acento sólido:
   borde de tarjetas, "VS", `rgba` de chip) y `#53C1AB` (realce claro del texto del chip). Neutros
   idénticos a `breaking`/`quote`. Ajustables visualmente en `apply` (Riesgo B). *Recomendación*:
   **aceptar**.
2. **[CONFIRMAR — bajo riesgo] Rótulos estáticos "OPCIÓN A" / "OPCIÓN B" + separador "VS"** (R5),
   texto del snapshot (no tokens), sin flecha/color condicional/soporte/resistencia/vol — para no
   sugerir un dato de mercado en vivo. Copy provisional ajustable en `apply`. *Recomendación*:
   **aceptar**.
3. **[CONFIRMAR — bajo riesgo] Dos campos opcionales (`kicker`, `nota_cierre`) por CSS `:empty`**,
   núcleo obligatorio `pregunta` + `opcion_a` + `opcion_b`; `kicker` como campo libre editorial
   (Riesgo D). `<body class="encuesta">` estático (SIN `{{sesgo_slug}}`: referenciarlo dejaría un
   huérfano que abortaría la guardia). *Recomendación*: **aceptar**.
4. **[CONFIRMAR — bajo riesgo] Límites editoriales `kicker≤30`, `pregunta≤90`, `opcion_a≤25`,
   `opcion_b≤25`, `nota_cierre≤80`** como guía del comando (no validación del motor), sujetos a
   ajuste visual en `apply` (Riesgo C). *Recomendación*: **aceptar** los valores provisionales.

No hay preguntas bloqueantes abiertas: las 6 preguntas de `idea.md`/`proposal.md` quedaron
resueltas en `spec.md` ("Preguntas abiertas — resueltas").

---

## Restricciones duras (Apply)

- **NO tocar el motor** `scripts/story_render.py` ni los snapshots `templates/stories/alerta.html`,
  `templates/stories/quote.html` y `templates/stories/breaking.html` ni `scripts/ruta_story.ps1`
  (AC12 exige `git diff master` vacío en esos cinco).
- **NO tocar ni commitear** los 6 archivos ajenos del director: `.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`, `templates/encuesta_posicion.txt`,
  `templates/encuesta_tendencia.txt`, `uv.lock`.
- **NUNCA** `git add -A` / `git add .` — solo los archivos de los grupos 1-4.
- **No** agregar dependencias (`pyproject.toml`/`uv.lock` sin cambios; Playwright ya opcional).
  **No** tocar `conftest.py`, agregar fixtures en `tests/fixtures/stories/*`,
  `src/market_data_mcp/**` ni `.claude/shared/modo_ejecutivo.md`. **No** agregar sección de mapeo
  dedicada a `encuesta` en `docs/design/stories-gi/plantillas-stories-gi.md` (OUT del spec).
- **No** usar fences `IF`/`FOR` en `encuesta.html`; los dos campos opcionales (`kicker`,
  `nota_cierre`) se resuelven por CSS `:empty`, no por el motor.
- Regla "solo lectura" del canvas: `encuesta.html` se autora en el repo; no se sube nada al
  proyecto Claude Design.

## Verificación global (cierre del Change)

```
uv run pytest tests/test_story_render.py                             # AC3/AC4/AC5/AC6 (AC6 skipif sin Chromium)
rg "width: 1920px" templates/stories/encuesta.html                  # AC1 → ≥1
rg "height: 1080px" templates/stories/encuesta.html                 # AC1 → ≥1
rg "<!-- (IF|FOR):" templates/stories/encuesta.html                 # AC2 → 0
rg ":empty" templates/stories/encuesta.html                         # AC4/AC5 → ≥2
rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/encuesta.html  # AC7 → 0
rg "encuesta" .claude/commands/story.md                             # AC8 → ≥2
rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" .claude/commands/story.md              # AC9 → ≥1
rg -i "no llama a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado" .claude/commands/story.md  # AC10 → ≥1
rg "encuesta" CLAUDE.md                                             # AC11 → ≥1 (sección Stories GI)
git diff master -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html templates/stories/breaking.html scripts/ruta_story.ps1  # AC12 → vacío
```

---

## Referencias

- `spec.md` (#125 — R1-R10, CB-1..CB-8, AC1-AC12, preguntas resueltas, riesgos A/B/C/D).
- `design.md` (#125 — technical approach, casos borde, mapa AC → verificación, desglose 1.1-5.1,
  paleta azul FIJADA, boceto del DOM, tabla de tokens).
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/tasks.md` — molde directo de
  este documento; segundo campo opcional replicado con el mismo criterio.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/tasks.md` — patrón fundacional
  del campo opcional (token + `:empty`).
- `.pulse/changes/archive/119-.../spec.md` — contrato del motor generalizado (no reabierto).
- `templates/stories/breaking.html:20-72,84-159,161-213` — molde más cercano (plantilla simple sin
  fences/loops, campo opcional `.breaking-kicker:empty`, tarjeta `.breaking-cifra`, footer); base
  estructural de `encuesta.html` en **azul**.
- `templates/stories/alerta.html:14-58,92-115,145-231,398-409` — andamiaje de marca
  (fuentes/paleta/footer), chip `.chip-categoria` y tarjeta `.tarjeta-precio` (acentos **rojos**
  `#E84040`; **no hay azul** en el archivo) que `encuesta` reutiliza como plantilla estructural.
- `templates/stories/quote.html:127-129` — `.quote-cargo:empty` (segundo precedente `:empty`).
- `tests/test_story_render.py:30,71-81,349-381` — `BREAKING_TEMPLATE`, `PAYLOAD_BREAKING` y los tres
  tests de `breaking` (base de los cuatro tests nuevos de `encuesta`).
- `.claude/commands/story.md:6-8,21-32,110-195` — comando a extender (PASO 0 + bloque "Ruta
  `breaking`" como molde del bloque "Ruta `encuesta`").
- `CLAUDE.md` sección "Stories GI" — enumeración de `[tipo]` (+ fila `/story` de la tabla, refresco
  opcional).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 09 `encuesta`
  (línea 67: contrato de campos canónico, fondo oscuro/azul).
- Contrato editorial `/encuesta` (`CLAUDE.md` "Encuestas diarias"; memoria
  `project_encuesta_sentimiento`): sentimiento puro, sin precios ni educación.
- Issue madre de esta Fase B · `encuesta` (a vincular en GitHub); #121 (quote) y #123 (breaking)
  precedentes cerrados directos.
