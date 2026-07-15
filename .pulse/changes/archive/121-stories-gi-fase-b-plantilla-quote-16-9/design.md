# Design — Stories GI · Fase B: plantilla Quote 16:9 (#121)

> Diseño técnico de `spec.md` (Change #121, dominio `stories-gi`). Implementa exactamente
> R1-R9, CB-1..CB-5 y AC1-AC10. **Hereda** el motor generalizado de Fase A (#119, `master`
> v0.2.0) **sin reabrirlo** — `scripts/story_render.py` no se toca. Alcance 100% aditivo:
> un snapshot HTML nuevo, un `[tipo]` nuevo en el comando, tests de mapeo puros y una línea
> de `CLAUDE.md`. **No contiene código de aplicación** — solo el plan técnico + tareas.

## Nota sobre invariantes de arquitectura

Este Change **no toca ninguna capa hexagonal** ni el motor. El MCP `src/market_data_mcp/`
queda intacto. Lo que se agrega es: un snapshot HTML+CSS estático (`templates/stories/quote.html`),
tres tests puros (`tests/test_story_render.py`), un bloque de prompt (`.claude/commands/story.md`)
y una frase de doc (`CLAUDE.md`). El motor sigue siendo un renderer "tonto" (payload → HTML → PNG)
sin lógica de negocio; la recolección editorial vive en el prompt. **No se agregan dependencias**
(Playwright ya es opcional `[project.optional-dependencies] stories`). `quote` es el primer
consumidor del motor **sin** fences `IF`/`FOR` ni loops — valida que el pipeline funciona con
tokens 100% escalares incondicionales.

---

## Technical Approach

### 0. Por qué el motor no necesita ni un solo cambio

`build_html` (Fase A) es `loops → fences → tokens → guardia`. Para `quote`:
- **Loops** (`resolver_loops`): `quote.html` no tiene `<!-- FOR -->` → no-op, el HTML pasa igual.
- **Fences** (`_resolver_fences`/`_fence_presente`): `quote.html` no tiene `<!-- IF -->` →
  no-op. `_FENCES` sigue fija en `("variacion","vol","chart_img","chart_svg")`
  (`scripts/story_render.py:29`); ninguno aplica a `quote`.
- **Tokens** (`build_context` + `_sustituir_tokens`): `build_context` recorre `payload.items()`
  y agrega `contexto[clave] = str(valor)` por cada escalar (`story_render.py:169-172`). Con el
  payload de R2 produce `{"cita": "...", "autor": "...", "autor_sub": "..."}` (más `plantilla`,
  no referenciado en el HTML → no-op silencioso, CB-1 heredado). Los 4 helpers de derivación
  (flecha, `sesgo_slug`, `impacto_badge`, `chart_src`) **no se disparan** porque `quote` no trae
  `variacion`/`sesgo`/`impacto`/`chart_png` (R2). `_sustituir_tokens` reemplaza `{{cita}}`,
  `{{autor}}`, `{{autor_sub}}` por sus valores.
- **Guardia** (`_validar_sin_huerfanos`): tras sustituir, no queda ningún `{{...}}` → pasa.

**Punto crítico de diseño (`autor_sub == ""`, R2/R4)**: `str("") == ""`, entonces
`contexto["autor_sub"] == ""` y `_sustituir_tokens` reemplaza `{{autor_sub}}` por cadena vacía.
El token **se resuelve** (no queda huérfano) → la guardia pasa. El colapso visual es
responsabilidad exclusiva del CSS (`:empty`), no del motor.

**Punto crítico de diseño (`{{sesgo_slug}}` prohibido en `quote.html`)**: en `alerta.html` el
`<body class="sesgo-{{sesgo_slug}}">` funciona porque el helper 2 puebla `sesgo_slug` desde
`sesgo`. `quote` **no** trae `sesgo` → el helper no se dispara → `sesgo_slug` no existe en el
contexto. Por tanto `quote.html` **no debe** referenciar `{{sesgo_slug}}` (ni ningún token de
Alerta): sería huérfano y la guardia abortaría. El `<body>` de `quote` lleva una clase estática
(ej. `class="quote"`), sin token de color direccional. Es una pieza editorial sin sesgo de mercado.

### 1. Snapshot `templates/stories/quote.html` (R1/R4/R6 · AC1/AC2/AC4/AC6)

Archivo nuevo, viewport 1920×1080. Reutiliza **verbatim** el andamiaje de marca de
`alerta.html:14-58`: los cuatro `@font-face` (Syne 800 / DM Sans 400·700 / Space Grotesk 600
desde `fonts/*.woff2`), `* { box-sizing }`, y el bloque `html, body` con `width: 1920px;
height: 1080px;`, fondo `#0D0D1A` con los mismos degradados radiales/lineales, `color: #F5F3F7`,
`font-family: "DM Sans"`, `overflow: hidden`. El comentario de cabecera advierte "NO cambiar
nombres de tokens sin actualizar tests" (igual criterio que `alerta.html:1-7`).

**Estructura de bloques** (contenedor raíz `.story` en columna: cuerpo centrado + footer a lo
ancho, mismo patrón `flex-direction: column` que Alerta):

```
<body class="quote">                         (clase estática, SIN {{sesgo_slug}})
  <div class="story">
    <div class="quote-cuerpo">                (flex:1; centrado vertical + horizontal)
      <blockquote class="quote-texto">        comillas decorativas vía ::before / ::after
        {{cita}}
      </blockquote>
      <div class="quote-atribucion">
        <p class="quote-autor">{{autor}}</p>
        <p class="quote-cargo">{{autor_sub}}</p>
      </div>
    </div>
    <div class="footer">                      (idéntico a alerta.html:398-409, SIN {{fuente}})
      <div class="footer-marca">
        <span>@grupointeligencia</span><span>grupointeligencia.com</span>
      </div>
      <p class="footer-disclaimer">Los CFD son instrumentos complejos … no constituye asesoría financiera.</p>
    </div>
  </div>
</body>
```

**Tokens exactos del snapshot** (los únicos tres `{{...}}` del archivo):

| Token | Elemento | Origen | Notas |
|---|---|---|---|
| `{{cita}}` | `<blockquote class="quote-texto">` | escalar `cita` | Texto plano, sin comillas propias (R6). |
| `{{autor}}` | `<p class="quote-autor">` | escalar `autor` | Siempre presente. |
| `{{autor_sub}}` | `<p class="quote-cargo">` | escalar `autor_sub` | Siempre presente en payload; admite `""` (R2/R4). |

**Comillas decorativas (R6 · AC6)**: glifos tipográficos **estáticos** como pseudo-elementos
CSS sobre `.quote-texto` (`::before { content: "\201C"; }` = `“` y `::after { content: "\201D"; }`
= `”`), en tipografía Syne, color de acento GI. **Nunca** forman parte del valor de `{{cita}}`.
Verificable con `rg "::before|::after|“|”|\\201C" templates/stories/quote.html` ≥1 match.

**Colapso de `autor_sub` vacío (R4 · AC4)**: regla CSS sobre el contenedor del token:
```css
.quote-cargo:empty { display: none; }
```
Con `autor_sub` no vacío se muestra la línea de cargo bajo `autor`. Con `autor_sub == ""` el
`<p class="quote-cargo"></p>` queda vacío → `:empty` lo saca del flujo (`display: none`, colapsa
el espacio vertical, no solo el texto) → el bloque de atribución permanece centrado sin hueco.
Verificable con `rg ":empty" templates/stories/quote.html` ≥1 match.

**Layout**: `.quote-cuerpo` centra la cita a un solo tamaño de fuente grande (Syne, sin bajada de
apoyo). No hay chips de categoría, tarjeta de precio, `stats`, columna de gráfico, `#img-*`,
`#svg-*` ni `{{fuente}}` — se omiten todos respecto a `alerta.html`. `overflow: hidden` se
conserva. El detalle fino de `font-size`/`padding`/posición de comillas → se resuelve al autorar
el CSS en `apply` (Riesgo B), no bloquea Design.

### 2. Contrato de payload `story_quote` (R2 · AC3)

```json
{
  "plantilla": "quote",
  "cita": "El mercado premia la paciencia más que la predicción.",
  "autor": "Nombre Analista",
  "autor_sub": "Head of Trading, Grupo Inteligencia"
}
```

- Claves del payload: `plantilla` (ruteo, no tokenizada), `cita`, `autor`, `autor_sub`. **Sin**
  campos array, `chart_png`, `variacion`, `sesgo`, `impacto` ni dato del motor.
- `autor_sub` **siempre presente** (nunca ausente ni `None`); admite `""` (R2/R3, resuelve Q2 —
  sin fence).
- Variante `autor_sub == ""` (mismo payload, cargo vacío): renderiza la cita + autor centrados,
  con la línea de cargo colapsada por CSS.

### 3. Comando `.claude/commands/story.md` (R5/R7 · AC7/AC8)

Cambios acotados, aditivos, replicando el patrón con que hoy se registra `alerta`:

1. **PASO 0 — lista de `[tipo]`** (hoy `story.md:6-8,18-26`): agregar `quote` a los tipos
   soportados. La validación pasa de "único soportado: `alerta`" a "soportados: `alerta`,
   `quote`". El mensaje de tipos disponibles (`story.md:20-24`) lista ambos. Sigue sin asumir
   tipo por defecto; el flag `ejecutivo` sigue avisado-y-continúa (CB-5, sin cambios).

2. **Bloque de recolección editorial nuevo** (ruta `quote`, hermano de los PASO 1-5 de `alerta`):
   `quote` **no** llama a `get_asset_levels` ni a ningún comando de datos de mercado. El flujo es:
   - Preguntar la cita: el director la dicta, **o** el modelo redacta una propuesta con criterio
     editorial (ej. resumiendo una idea de mercado de la semana, mismo espíritu que `/concepto`)
     y el director la aprueba/ajusta (R7, resuelve Q4).
   - **Límite editorial (R5 · AC8)**: documentar en el comando `cita ≤ 220 caracteres` (más corto
     que el `parrafo ≤ 280` de Alerta porque `quote` se lee a un solo tamaño grande). Es guía de
     redacción del comando, **no** validación del motor (CB-2: el motor no trunca ni aborta por
     longitud). Si la cita excede, el comando ajusta la redacción antes del preview.
   - **Comillas (R6 · CB-3)**: guía de redacción — la cita se recolecta **sin** comillas propias;
     las comillas visuales las pone el snapshot.
   - Preguntar `autor` y `autor_sub`; construir el payload con `autor_sub` **siempre presente**
     (si el director no da cargo, `autor_sub: ""`, nunca omitir la clave — CB-1).
   - Reusar el flujo compartido preview → aprobación (CB-4: si no aprueba, no se renderiza ni
     guarda nada) → render → guardado con:
     ```powershell
     scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[slug o _general]" -Plantilla "quote" -Hora "[HH-mm]"
     ```
     y `uv run python scripts/story_render.py --template templates/stories/quote.html --out "[ruta]"`
     (payload por stdin). `quote` es editorial sin activo protagonista → puede guardarse bajo
     `_general` (criterio `ruta_story.ps1`/`ruta_mensaje.ps1`); el comando lo indica en su prompt.

Verificación: `rg "quote" .claude/commands/story.md` ≥2 matches (AC7); `rg "220"
.claude/commands/story.md` ≥1 match (AC8).

### 4. `CLAUDE.md` sección "Stories GI" (R9 · AC9)

Una sola edición: la frase "Único `[tipo]` soportado hoy: `alerta`" pasa a enumerar también
`quote` (ej. "`[tipo]` soportados hoy: `alerta`, `quote`"). No se toca el resto del párrafo ni
de la sección (regla "solo lectura" del canvas, guardado, gitignore, etc. quedan igual).
Verificación: `rg "quote" CLAUDE.md` ≥1 match en la sección.

---

## Casos borde (mapa CB → diseño)

| CB | Situación | Comportamiento diseñado |
|---|---|---|
| CB-1 | `autor_sub` ausente del payload (no `""`) | El comando (R7) siempre construye la clave, aunque sea `""`. Si por error se omitiera, `{{autor_sub}}` queda huérfano → guardia `_validar_sin_huerfanos` → `StoryRenderError` (fail-fast heredado), no colapso silencioso. |
| CB-2 | `cita` > 220 caracteres | El comando ajusta la redacción antes del preview (R5); el motor no valida longitud — no aborta ni trunca. |
| CB-3 | `cita` con comillas literales | Guía de redacción del comando: se recolecta sin comillas propias (R6). No es validación del motor. |
| CB-4 | Director rechaza el preview | No se renderiza ni guarda nada en `data/stories/` (criterio heredado). |
| CB-5 | `/story quote ejecutivo` | Avisa que `/story` no soporta el flag y continúa la Story normal (criterio ya vigente para `alerta`, sin cambios). |

---

## Tratamiento de riesgos

- **Riesgo A — fidelidad visual sin golden PNG** (heredado R-2 de Fase A/#109): no hay export de
  referencia 16:9 del canvas GI para `quote`. *Mitigación*: aprobación visual manual del director
  en la primera corrida real de `/story quote`. Los tests **no** asertan estética, solo contrato
  (tokens inyectados, sin huérfanos) + dimensiones IHDR `(1920, 1080)`.
- **Riesgo B — límite de 220 caracteres es estimación editorial**: si el layout final desborda o
  admite más, el valor se ajusta en `apply` al autorar el CSS real (junto con `font-size` de la
  cita). No bloquea `specify`/`design` (mismo criterio que Fase A dejó el CSS fino para `apply`).

---

## Estrategia de validación (EDD/TDD) — mapa AC → verificación

Test-first: los tests de mapeo se escriben/ajustan antes de dar el snapshot por bueno.
`quote.html` produce tokens 100% escalares → `build_html` es puro y testeable **sin Chromium**;
solo AC5 usa render real (`@pytest.mark.skipif(not _chromium_disponible())`). Sin fixture nuevo
en `tests/fixtures/stories/`, sin tocar `conftest.py` (se reusa el patrón contra el snapshot real
`quote.html`, igual que los tests de `alerta.html`).

| AC | Tipo | Verificación | Test |
|---|---|---|---|
| AC1 | `rg` (estructural) | `quote.html` contiene `width: 1920px` y `height: 1080px` | manual/gate |
| AC2 | `rg` (estructural) | `rg "<!-- (IF\|FOR):" templates/stories/quote.html` → 0 matches | manual/gate |
| AC3 | `pytest` puro | `build_html(PAYLOAD_QUOTE, quote.html)`: contiene `cita`/`autor`/`autor_sub`, sin `{{` ni `}}` | `test_quote_no_placeholders` (nuevo) |
| AC4 | `pytest` puro | `build_html` con `autor_sub == ""`: sin `{{`/`}}` (token resuelto a vacío); `:empty` presente en el CSS | `test_quote_autor_sub_vacio` (nuevo) + `rg ":empty"` |
| AC5 | `pytest` `skipif` | `render_story(PAYLOAD_QUOTE, quote.html)` → PNG existe, IHDR `(1920,1080)`, `> 5 KB` | `test_quote_render_dimensiones` (nuevo) |
| AC6 | `rg` (estructural) | comillas decorativas estáticas en CSS/HTML (`::before`/`::after`/glifo), no token | manual/gate |
| AC7 | `rg` (estructural) | `rg "quote" .claude/commands/story.md` ≥2 | manual/gate |
| AC8 | `rg` (estructural) | `rg "220" .claude/commands/story.md` ≥1 | manual/gate |
| AC9 | `rg` (estructural) | `rg "quote" CLAUDE.md` ≥1 en sección "Stories GI" | manual/gate |
| AC10 | `git diff` (estructural) | `git diff master -- scripts/story_render.py templates/stories/alerta.html scripts/ruta_story.ps1` → vacío | manual/gate |

Constante de test propuesta (análoga a `PAYLOAD_EJEMPLO`):
`PAYLOAD_QUOTE = {"plantilla": "quote", "cita": "El mercado premia la paciencia más que la
predicción.", "autor": "Nombre Analista", "autor_sub": "Head of Trading, Grupo Inteligencia"}`.
El caso vacío usa `{**PAYLOAD_QUOTE, "autor_sub": ""}`.

---

## Estructura de archivos afectados

```
NUEVOS (en Apply — este design.md NO edita código)
  templates/stories/quote.html       R1/R4/R6 — snapshot 1920×1080; tokens {{cita}}/{{autor}}/{{autor_sub}};
                                      comillas ::before/::after estáticas; .quote-cargo:empty{display:none};
                                      SIN fences IF/FOR, SIN {{sesgo_slug}}, SIN bloque gráfico/precio.

MODIFICADOS
  .claude/commands/story.md          R5/R7 — PASO 0: agregar `quote` a [tipo]; bloque de recolección
                                      editorial (cita ≤220, sin comillas propias, autor_sub siempre presente).
  tests/test_story_render.py         R8 — 3 tests nuevos (AC3/AC4/AC5) contra quote.html; sin fixture nuevo.
  CLAUDE.md                          R9 — sección "Stories GI": enumerar `quote` junto a `alerta`.

SIN CAMBIOS (confirmado — AC10)
  scripts/story_render.py            motor intacto (build_context/resolver_loops/_resolver_fences/_FENCES/render_png)
  templates/stories/alerta.html      contrato de Alerta intacto
  scripts/ruta_story.ps1             ya acepta -Plantilla genérico
  tests/conftest.py                  no se toca (sys.path vive en el propio test)
  tests/fixtures/stories/*           no se agrega fixture; se reusa el patrón contra snapshot real
  .claude/shared/modo_ejecutivo.md   /story sigue en "No elegibles"
  src/market_data_mcp/**             ninguna capa hexagonal tocada
  pyproject.toml / uv.lock           sin nuevas dependencias

PROHIBIDO TOCAR (6 archivos ajenos del director)
  .claude/commands/apertura.md · data/glosario_siglas.json · data/historial_encuestas.json
  templates/encuesta_posicion.txt · templates/encuesta_tendencia.txt · uv.lock
```

---

## Decisiones para el gate humano DESIGN → APPLY

Ninguna decisión bloqueante nueva: el motor no cambia y todas las Q1-Q6 quedaron resueltas en
`spec.md`. Se elevan al director dos confirmaciones de bajo riesgo:

1. **[CONFIRMAR] `quote.html` no lleva clase de color direccional (`{{sesgo_slug}}`).** A
   diferencia de `alerta.html`, el `<body>` de `quote` usa una clase estática porque `quote` no
   trae `sesgo`/`variacion` y el helper 2 no puebla `sesgo_slug` (referenciarlo dejaría un token
   huérfano). *Recomendación*: **aceptar** — es coherente con que `quote` es una pieza editorial
   sin sesgo de mercado.
2. **[CONFIRMAR] límite editorial `cita ≤ 220 caracteres`** como guía del comando (no validación
   del motor), sujeto a ajuste visual en `apply` (Riesgo B). *Recomendación*: **aceptar** el valor
   provisional; se afina contra el layout real al autorar el CSS.

---

## Desglose de implementación (tareas)

> Ordenadas por dependencia. Cada tarea que toca código/plantilla ejecutable lleva su criterio de
> aceptación mapeado a `spec.md`. TDD: escribir/ajustar el test antes de cerrar la tarea. Este
> desglose deja el Change listo para `break-to-tasks` (`tasks.md`); **no** se escribe `tasks.md`
> en esta fase.

### 1. Snapshot — `templates/stories/quote.html` (nuevo)

- [ ] **1.1 Andamiaje de marca.** Copiar el bloque `@font-face` + `html, body` de `alerta.html`
  (fuentes locales `fonts/*.woff2`, fondo `#0D0D1A` con degradados, viewport 1920×1080,
  `overflow: hidden`) y el footer estándar (`@grupointeligencia` + disclaimer CFD, **sin**
  `{{fuente}}`). Comentario de cabecera "NO cambiar nombres de tokens". *Criterio (AC1)*:
  `rg "width: 1920px"` y `rg "height: 1080px"` en `quote.html` ≥1 match c/u.
- [ ] **1.2 Cuerpo editorial y tokens.** `<blockquote class="quote-texto">{{cita}}</blockquote>`
  + `.quote-atribucion` con `<p class="quote-autor">{{autor}}</p>` y
  `<p class="quote-cargo">{{autor_sub}}</p>`, centrado vertical/horizontal. `<body class="quote">`
  estático (SIN `{{sesgo_slug}}` ni tokens de Alerta). Sin fences `IF`/`FOR`. *Criterios (AC2/AC3)*:
  `rg "<!-- (IF|FOR):" quote.html` → 0; `test_quote_no_placeholders` verde. *(depende de 1.1)*
- [ ] **1.3 Comillas decorativas estáticas + colapso `:empty`.** `.quote-texto::before/::after`
  con glifos `“`/`”` (Syne); `.quote-cargo:empty { display: none; }`. *Criterios (AC6/AC4)*:
  `rg "::before|::after|“|”" quote.html` ≥1; `rg ":empty" quote.html` ≥1; `test_quote_autor_sub_vacio`
  verde. *(depende de 1.2)*

### 2. Tests — `tests/test_story_render.py` (aditivo, R8)

- [ ] **2.1 Constante y test de mapeo con cargo.** Agregar `PAYLOAD_QUOTE` +
  `QUOTE_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "quote.html"`. `test_quote_no_placeholders`:
  `build_html(PAYLOAD_QUOTE, QUOTE_TEMPLATE)` contiene `cita`/`autor`/`autor_sub`, sin `{{`/`}}`.
  *Criterio (AC3)*. *(depende de 1.2)*
- [ ] **2.2 Test de colapso `autor_sub == ""`.** `test_quote_autor_sub_vacio`:
  `build_html({**PAYLOAD_QUOTE, "autor_sub": ""}, QUOTE_TEMPLATE)` no contiene `{{`/`}}` (token
  resuelto a vacío, no omitido). *Criterio (AC4)*. *(depende de 1.3)*
- [ ] **2.3 Test de render real.** `test_quote_render_dimensiones` con
  `@pytest.mark.skipif(not _chromium_disponible())`: `render_story(PAYLOAD_QUOTE, QUOTE_TEMPLATE,
  salida)` → PNG existe, `> 5 KB`, `_png_size == (1920, 1080)`. *Criterio (AC5)*. **No tocar**
  `conftest.py`. *Criterio suite*: `uv run pytest tests/test_story_render.py` verde. *(depende de 1.2)*

### 3. Comando — `.claude/commands/story.md` (R5/R7)

- [ ] **3.1 Registrar `[tipo]` `quote` en PASO 0.** Actualizar la lista dura y el mensaje de tipos
  disponibles para incluir `quote` junto a `alerta`. *Criterio (AC7)*: `rg "quote" story.md` ≥2.
- [ ] **3.2 Bloque de recolección editorial.** Ruta `quote` sin datos de mercado: dictar/redactar
  la cita, `cita ≤ 220` (guía, no validación), sin comillas propias, `autor` + `autor_sub`
  (siempre presente, `""` si no hay cargo), reuso de preview → render → `ruta_story.ps1
  -Plantilla "quote"` / `--template templates/stories/quote.html`. *Criterios (AC7/AC8)*:
  `rg "quote" story.md` ≥2; `rg "220" story.md` ≥1.

### 4. Documentación — `CLAUDE.md` (R9)

- [ ] **4.1 Enumerar `quote` en la sección "Stories GI".** Cambiar "único `[tipo]` soportado hoy:
  `alerta`" por "`alerta`, `quote`", sin tocar el resto. *Criterio (AC9)*: `rg "quote" CLAUDE.md` ≥1.

### 5. No-regresión (AC10)

- [ ] **5.1 Confirmar motor/Alerta/helper intactos.** *Criterio (AC10)*: `git diff master --
  scripts/story_render.py templates/stories/alerta.html scripts/ruta_story.ps1` → vacío.

---

## Referencias

- `spec.md` (#121 — R1-R9, CB-1..CB-5, AC1-AC10, Q1-Q6 resueltas, riesgos A/B).
- `proposal.md` / `idea.md` (#121 — contexto y preguntas originales).
- `.pulse/changes/archive/119-.../design.md` — molde de este documento y contrato del motor
  generalizado (no reabierto).
- `scripts/story_render.py:55-179` — `build_context` (escalares dinámicos + 4 helpers) y
  `_fence_presente`/`_FENCES`, **no se modifican**.
- `templates/stories/alerta.html:14-58,398-409` — andamiaje de marca (fuentes/paleta/footer),
  base de `quote.html`.
- `tests/test_story_render.py:35-55,83-104,266-277` — patrón de `PAYLOAD_EJEMPLO`, tests de
  mapeo de `alerta` y test de render con `skipif`, base de los 3 tests nuevos.
- `.claude/commands/story.md:6-8,16-26` — comando a extender (PASO 0 + recolección).
- `CLAUDE.md` sección "Stories GI" — enumeración de `[tipo]`.
- Issue #121 (`bbenja11/grupo-analisis-mercado`).
</content>
