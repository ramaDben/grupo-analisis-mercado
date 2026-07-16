# Design — Stories GI · Fase B: plantilla Breaking 16:9 (#123)

> Diseño técnico de `spec.md` (Change #123, dominio `stories-gi`). Implementa exactamente
> R1-R10, CB-1..CB-7 y AC1-AC11. **Hereda** el motor generalizado de Fase A (#119, `master`
> v0.2.0) **sin reabrirlo** — `scripts/story_render.py` no se toca — y el patrón de campo
> opcional (token + `:empty`) validado en Fase B/`quote` (#121) **sin reabrirlo**. Alcance
> 100% aditivo: un snapshot HTML nuevo, un `[tipo]` nuevo en el comando, tests de mapeo puros
> y una línea de `CLAUDE.md`. **No contiene código de aplicación** — solo el plan técnico +
> tareas.

## Nota sobre invariantes de arquitectura

Este Change **no toca ninguna capa hexagonal** ni el motor. El MCP `src/market_data_mcp/`
queda intacto. Lo que se agrega es: un snapshot HTML+CSS estático
(`templates/stories/breaking.html`), tres tests puros (`tests/test_story_render.py`), un
bloque de prompt (`.claude/commands/story.md`) y una frase de doc (`CLAUDE.md`). El motor sigue
siendo un renderer "tonto" (payload → HTML → PNG) sin lógica de negocio; la recolección
editorial vive en el prompt. **No se agregan dependencias** (Playwright ya es opcional
`[project.optional-dependencies] stories`). `breaking` es el segundo consumidor del motor
**sin** fences `IF`/`FOR` ni loops (tras `quote`) — con un único campo opcional (`kicker_tema`)
resuelto por CSS, no por el motor.

---

## Technical Approach

### 0. Por qué el motor no necesita ni un solo cambio (R3 · AC2/AC11)

`build_html` (Fase A) es `loops → fences → tokens → guardia`. Para `breaking`:
- **Loops** (`resolver_loops`): `breaking.html` no tiene `<!-- FOR -->` → no-op, el HTML pasa
  igual (mismo comportamiento validado en `quote`).
- **Fences** (`_resolver_fences`/`_fence_presente`): `breaking.html` no tiene `<!-- IF -->` →
  no-op. `_FENCES` sigue fija en `("variacion","vol","chart_img","chart_svg")`
  (`scripts/story_render.py:33`); ninguno aplica a `breaking`. El fence genérico por-clave
  (`_expandir_elemento`) solo existe **dentro** de un bloque `FOR`, que `breaking` no usa →
  no hay forma de condicionar `kicker_tema` vía fence sin tocar el motor (fuera de alcance).
- **Tokens** (`build_context` + `_sustituir_tokens`): `build_context` recorre `payload.items()`
  y agrega `contexto[clave] = str(valor)` por cada escalar. Con el payload de R2 produce
  `{"kicker_tema": "...", "titular": "...", "valor": "...", "contexto": "...",
  "parrafo_reaccion": "..."}` (más `plantilla`, no referenciado en el HTML → no-op silencioso,
  CB-1 heredado). Los 4 helpers de derivación de Fase A (flecha, `sesgo_slug`, `impacto_badge`,
  `chart_src`) **no se disparan** porque `breaking` no trae `variacion`/`sesgo`/`impacto`/
  `chart_png` (R2). `_sustituir_tokens` reemplaza los cinco `{{...}}` por sus valores.
- **Guardia** (`_validar_sin_huerfanos`): tras sustituir, no queda ningún `{{...}}` → pasa.

**Punto crítico de diseño (`kicker_tema == ""`, R2/R4)**: `str("") == ""`, entonces
`contexto["kicker_tema"] == ""` y `_sustituir_tokens` reemplaza `{{kicker_tema}}` por cadena
vacía. El token **se resuelve** (no queda huérfano) → la guardia pasa. El colapso visual es
responsabilidad exclusiva del CSS (`:empty`), no del motor — patrón idéntico a
`.quote-cargo:empty` de `quote` R4.

**Punto crítico de diseño (`{{sesgo_slug}}` prohibido en `breaking.html`)**: en `alerta.html`
el `<body class="sesgo-{{sesgo_slug}}">` funciona porque el helper 2 puebla `sesgo_slug` desde
`sesgo`. `breaking` **no** trae `sesgo` → el helper no se dispara → `sesgo_slug` no existe en el
contexto. Por tanto `breaking.html` **no debe** referenciar `{{sesgo_slug}}` ni ningún token de
Alerta (`{{precio_actual}}`, `{{variacion_flecha}}`, `{{soporte}}`, `{{resistencia}}`,
`{{vol_pct}}`, `{{chart_src}}`, `{{fuente}}`, `{{fecha_hora}}`, etc.): sería huérfano y la
guardia abortaría. El `<body>` de `breaking` lleva una clase estática (`class="breaking"`), sin
token de color direccional. La dirección del evento se comunica **en el texto**
(titular/contexto/reacción, R7.3), no con una clase CSS de sesgo.

### 1. Snapshot `templates/stories/breaking.html` (R1/R3/R4/R5 · AC1/AC2/AC4/AC6)

Archivo nuevo, viewport 1920×1080. Reutiliza **verbatim** el andamiaje de marca de
`alerta.html:14-58`: los cuatro `@font-face` (Syne 800 / DM Sans 400·700 / Space Grotesk 600
desde `fonts/*.woff2`), `* { box-sizing }`, y el bloque `html, body` con `width: 1920px;
height: 1080px;`, fondo `#0D0D1A` con los **mismos degradados radiales/lineales** de
`alerta.html:51-54` (radial `#2A1220`→`#0D0D1A` + linear `#0D0D1A`/`#120A12`/`#0D0D1A`),
`color: #F5F3F7`, `font-family: "DM Sans"`, `overflow: hidden`. El comentario de cabecera
advierte "NO cambiar nombres de tokens sin actualizar tests" (igual criterio que
`alerta.html:1-7` y `quote.html:1-7`).

**Estructura de bloques** (contenedor raíz `.story` en columna: cuerpo + footer a lo ancho,
mismo patrón `flex-direction: column` que Alerta y Quote; **una sola columna** editorial, sin
`.columna-grafico`):

```
<body class="breaking">                        (clase estática, SIN {{sesgo_slug}})
  <div class="story">
    <div class="breaking-cuerpo">               (flex:1; columna, centrado vertical)
      <span class="breaking-kicker">{{kicker_tema}}</span>   chip acento rojo, colapsa :empty
      <h1 class="breaking-titular">{{titular}}</h1>          Syne 800, jerarquía de titular
      <div class="breaking-cifra">              tarjeta acento rojo — NO es tarjeta de precio
        <span class="breaking-cifra-rotulo">CIFRA CLAVE</span>   TEXTO ESTÁTICO (no token, R5)
        <span class="breaking-cifra-valor">{{valor}}</span>     Syne 800, grande
      </div>
      <p class="breaking-contexto">{{contexto}}</p>          línea secundaria bajo la cifra
      <p class="breaking-reaccion">{{parrafo_reaccion}}</p>  DM Sans, párrafo de cierre
    </div>
    <div class="footer">                         (idéntico a alerta/quote, SIN {{fuente}})
      <div class="footer-marca">
        <span>@grupointeligencia</span><span>grupointeligencia.com</span>
      </div>
      <p class="footer-disclaimer">Los CFD son instrumentos complejos … no constituye asesoría financiera.</p>
    </div>
  </div>
</body>
```

**Tokens exactos del snapshot** (los únicos cinco `{{...}}` del archivo):

| Token | Elemento | Origen | Notas |
|---|---|---|---|
| `{{kicker_tema}}` | `<span class="breaking-kicker">` | escalar `kicker_tema` | Único opcional; admite `""` → colapsa por `:empty` (R2/R4). |
| `{{titular}}` | `<h1 class="breaking-titular">` | escalar `titular` | Siempre no vacío; Syne, jerarquía de titular de Alerta. |
| `{{valor}}` | `<span class="breaking-cifra-valor">` | escalar `valor` | Cifra editorial de la noticia; NO precio del motor, sin `digits`. |
| `{{contexto}}` | `<p class="breaking-contexto">` | escalar `contexto` | Siempre no vacío; línea secundaria de apoyo. |
| `{{parrafo_reaccion}}` | `<p class="breaking-reaccion">` | escalar `parrafo_reaccion` | Siempre no vacío; párrafo de cierre, DM Sans. |

**Acentos rojos reutilizados de `alerta.html` (R1)**: el chip `.breaking-kicker` replica el
tratamiento del `.chip-categoria` de Alerta (`background: rgba(232,64,64,0.14)`, `border: 1px
solid rgba(232,64,64,0.5)`, `color: #F5A3A3`, `border-radius: 999px`, Space Grotesk mayúsculas);
la tarjeta `.breaking-cifra` replica el `border: 2px solid #E84040` + `background:
rgba(232,64,64,0.08)` + `border-radius: 22px` de `.tarjeta-precio` de Alerta
(`alerta.html:145-152`), **pero con layout distinto**: rótulo estático "CIFRA CLAVE" + valor,
sin `.tarjeta-cabecera`, sin `.precio-linea`, sin `.variacion`, sin `.stats`
(soporte/resistencia/vol). El rótulo `.breaking-cifra-rotulo` usa el estilo `.stat-label`
(Space Grotesk, mayúsculas, `letter-spacing`, `#A9A5B4`).

**Rotulado fijo "CIFRA CLAVE" (R5 · AC6)**: es texto estático del snapshot (nunca un token),
inmediatamente junto al valor. Se omite deliberadamente todo elemento de dato de mercado en
vivo: sin flecha `▲/▼`, sin color verde/rojo condicional por dirección, sin fila de
soporte/resistencia/vol, sin rótulo de ticker/activo, sin las clases `sesgo-alcista`/
`sesgo-bajista`. Verificable con `rg -i "CIFRA CLAVE" breaking.html` ≥1 y `rg
"soporte|resistencia|variacion_flecha|precio_actual" breaking.html` → 0 (AC6).

**Colapso de `kicker_tema` vacío (R4 · AC4)**: regla CSS sobre el contenedor del token:
```css
.breaking-kicker:empty { display: none; }
```
Con `kicker_tema` no vacío se muestra el chip sobre el titular. Con `kicker_tema == ""` el
`<span class="breaking-kicker"></span>` queda vacío → `:empty` lo saca del flujo (`display:
none`, colapsa el espacio, no solo el texto) → el titular sube sin hueco en blanco donde estaría
el chip. Patrón exacto validado en `quote` R4 (`.quote-cargo:empty`). Verificable con
`rg ":empty" breaking.html` ≥1 match.

**Layout**: `.breaking-cuerpo` es una sola columna centrada verticalmente (no dos columnas como
Alerta — no hay `.columna-grafico`, no hay `#img-*`/`#svg-*`/`.contenedor-grafico`,
`.rotulo-grafico`). No hay `{{fecha_hora}}` ni `{{fuente}}`. `overflow: hidden` se conserva. El
detalle fino de `font-size`/`padding`/espaciados → se resuelve al autorar el CSS en `apply`
(Riesgo B/C), no bloquea Design.

### 2. Contrato de payload `story_breaking` (R2 · AC3)

```json
{
  "plantilla": "breaking",
  "kicker_tema": "BANCOS CENTRALES",
  "titular": "La Fed sorprende con una pausa más larga de lo esperado",
  "valor": "5,50%",
  "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
  "parrafo_reaccion": "El mercado ajusta expectativas hacia un primer recorte más tardío, presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
}
```

- Claves del payload: `plantilla` (ruteo, no tokenizada), `kicker_tema`, `titular`, `valor`,
  `contexto`, `parrafo_reaccion`. **Sin** campos array, `chart_png`, `variacion`, `sesgo`,
  `impacto`, `activo` ni dato del motor.
- `kicker_tema` **siempre presente** (nunca ausente ni `None`); admite `""` (R2/R4, resuelve
  Q1 — único opcional, sin fence).
- `titular`, `valor`, `contexto`, `parrafo_reaccion` **siempre no vacíos** — el comando (R7)
  nunca los construye como `""`; si el director no puede dar contexto/reacción, el comando
  insiste o usa una redacción editorial mínima, nunca cadena vacía en estos cuatro.
- `valor` es la cifra editorial de la noticia (dato macro, porcentaje, nivel mencionado) —
  **no** un precio en vivo del motor; **no** lleva formateo `digits` de `config/activos.json`
  (eso es exclusivo de precios vía `get_asset_levels`). Se recolecta ya formateado con su
  unidad si aplica (CB-6, guía de redacción: `"5,50%"`, `"US$ 2.318"`).
- Variante `kicker_tema == ""` (mismo payload, chip vacío): renderiza titular + cifra +
  contexto + reacción, con el chip colapsado por CSS.

### 3. Comando `.claude/commands/story.md` (R6/R7/R8 · AC7/AC8/AC9)

Cambios acotados, aditivos, replicando el patrón con que hoy se registran `alerta` y `quote`:

1. **PASO 0 — lista de `[tipo]`** (hoy `story.md:6-8,17-29`): agregar `breaking` a los tipos
   soportados. La validación pasa de "soportados: `alerta`, `quote`" a "soportados: `alerta`,
   `quote`, `breaking`". El mensaje de tipos disponibles (`story.md:20-25`) lista los tres. Si
   el tipo confirmado es `breaking`, saltar al bloque "Ruta `breaking`" (los PASO 1-7 son de
   `alerta`; el bloque "Ruta `quote`" es de `quote`). El flag `ejecutivo` sigue avisado-y-
   continúa (CB-4, sin cambios).

2. **Bloque de recolección editorial nuevo** ("Ruta `breaking`", hermano de "Ruta `quote`"):
   `breaking` **no** llama a `get_asset_levels` ni a ningún comando/tool de datos de mercado, y
   **no ejecuta su propia búsqueda de evento** (no reusa el WebSearch de `/alerta` PASO 1 ni su
   mecanismo de detección de noticias — R7.2, AC9, resuelve Q4). El flujo es:
   - **Fuente editorial (R7.1)**: preguntar si el director ya corrió `/noticia` o `/alerta` en
     la misma sesión (o tiene el evento/cifra ya redactado) → si es así, reutiliza esos textos
     como base. Si no, pide que dicte directamente los campos. **CB-5**: no bloquea ni exige
     corrida previa; el atajo es opcional.
   - **Dirección explícita (R7.3, regla de oro)**: el titular/contexto/reacción deben dejar
     clara la lectura direccional del evento (qué activo/mercado se afecta y hacia dónde), con
     registro profesional del repo (énfasis sin dramatización, `CLAUDE.md` "Registro y tono").
   - **Límites editoriales (R6 · AC8)**: documentar en el comando `kicker_tema ≤ 30`,
     `titular ≤ 70`, `contexto ≤ 100`, `parrafo_reaccion ≤ 280` caracteres. Guía de redacción
     del comando, **no** validación del motor (CB-2: el motor no trunca ni aborta por longitud).
     Si algún campo excede, el comando ajusta la redacción antes del preview.
   - **Payload (R7.4)**: construir con `kicker_tema` **siempre presente** — si el director no da
     tema/categoría claro, `"kicker_tema": ""` (nunca omitir la clave, CB-1). Los otros cuatro
     campos siempre no vacíos.
   - **Guardado con o sin `-Activo` (R8 · resuelve Q5)**: preguntar si la noticia tiene un
     activo protagonista claro (decisión **editorial** del director, no regla automática nueva
     ni del motor ni de `ruta_story.ps1`):
     - **Sí** → `-Activo [TICKER_MT5]` (normalizado contra `config/activos.json`, mismo criterio
       que `/chart` PASO 1).
     - **No / ambiguo / múltiples activos (CB-7)** → `-Activo "_general"` (igual que `quote`).
   - Reusar el flujo compartido preview → aprobación (CB-3: si no aprueba, no se renderiza ni
     guarda nada en `data/stories/`) → render → guardado con:
     ```powershell
     scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5 o _general]" -Plantilla "breaking" -Hora "[HH-mm]"
     ```
     y `uv run python scripts/story_render.py --template templates/stories/breaking.html --out
     "[ruta]"` (payload `story_breaking` por stdin). `[Hora]` sale del reloj de Chile (regla
     canónica). Mismo manejo de éxito/error que el PASO 7 de `alerta`.

Verificación: `rg "breaking" .claude/commands/story.md` ≥2 (AC7 — uno en PASO 0, otro en el
bloque "Ruta `breaking`"); `rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30" story.md` ≥1 (AC8); `rg -i "no
ejecuta su propia búsqueda|no busca por cuenta propia|no reusa" story.md` ≥1 dentro del bloque
(AC9).

### 4. `CLAUDE.md` sección "Stories GI" (R10 · AC10)

Una sola edición: la enumeración de `[tipo]` soportados (hoy `alerta`, `quote`) pasa a incluir
`breaking` (ej. "`[tipo]` soportados hoy: `alerta`, `quote`, `breaking`"). No se toca el resto
del párrafo ni de la sección (regla "solo lectura" del canvas, guardado, gitignore, etc. quedan
igual). Verificación: `rg "breaking" CLAUDE.md` ≥1 match en la sección "Stories GI".

---

## Casos borde (mapa CB → diseño)

| CB | Situación | Comportamiento diseñado |
|---|---|---|
| CB-1 | `kicker_tema` ausente del payload (no `""`) | El comando (R7.4) siempre construye la clave, aunque sea `""`. Si por error se omitiera, `{{kicker_tema}}` queda huérfano → guardia `_validar_sin_huerfanos` → `StoryRenderError` (fail-fast heredado), no colapso silencioso distinto al de R4. |
| CB-2 | Algún campo excede el límite editorial (R6) | El comando ajusta la redacción antes del preview; el motor no valida longitud — no aborta ni trunca. |
| CB-3 | Director rechaza el preview | No se renderiza ni guarda nada en `data/stories/` (criterio heredado de `.pulse/specs/stories-gi/spec.md`). |
| CB-4 | `/story breaking ejecutivo` | Avisa que `/story` no soporta el flag y continúa la Story normal (criterio ya vigente para `alerta`/`quote`, sin cambios). |
| CB-5 | Sin corrida previa de `/noticia`/`/alerta` ni evento claro | El comando pide dictar directamente los 5 campos; no bloquea ni exige corrida previa (R7 es atajo, no dependencia dura). |
| CB-6 | `valor` sin unidad clara (solo un número) | Guía de redacción: `valor` se recolecta ya formateado con su unidad (`"5,50%"`, `"US$ 2.318"`). No es validación del motor. |
| CB-7 | Activo protagonista ambiguo / múltiples activos | El director decide al responder R8; sin activo único claro → `_general` (igual que `quote`). |

---

## Tratamiento de riesgos

- **Riesgo A — fidelidad visual sin golden PNG** (heredado R-2 de Fase A/#109 y de `quote`/#121):
  no hay export de referencia 16:9 del canvas GI para `breaking`. *Mitigación*: aprobación
  visual manual del director en la primera corrida real de `/story breaking`. Los tests **no**
  asertan estética, solo contrato (tokens inyectados, sin huérfanos) + dimensiones IHDR
  `(1920, 1080)`.
- **Riesgo B — rotulado "CIFRA CLAVE" es decisión editorial de este documento**, no verificada
  visualmente contra el manual de marca. Si el layout final necesita otro texto/tratamiento, el
  copy se ajusta en `apply` al autorar el CSS real — no bloquea `specify`/`design` (mismo
  criterio que Fase A/`quote` dejaron el detalle CSS fino para `apply`).
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir golden
  PNG, los caracteres exactos pueden requerir ajuste tras la primera corrida visual; se
  documentan como guía editorial del comando, no como validación dura del motor (mismo criterio
  que Riesgo B de `quote`).

---

## Validation Strategy (EDD/TDD) — mapa AC → verificación

Test-first: los tests de mapeo se escriben/ajustan antes de dar el snapshot por bueno.
`breaking.html` produce tokens 100% escalares → `build_html` es puro y testeable **sin
Chromium**; solo AC5 usa render real (`@pytest.mark.skipif(not _chromium_disponible())`). Sin
fixture nuevo en `tests/fixtures/stories/`, sin tocar `conftest.py` (se reusa el patrón contra
el snapshot real `breaking.html`, igual que los tests de `alerta.html`/`quote.html`).

| AC | Tipo | Verificación | Test |
|---|---|---|---|
| AC1 | `rg` (estructural) | `breaking.html` contiene `width: 1920px` y `height: 1080px` | manual/gate |
| AC2 | `rg` (estructural) | `rg "<!-- (IF\|FOR):" templates/stories/breaking.html` → 0 matches | manual/gate |
| AC3 | `pytest` puro | `build_html(PAYLOAD_BREAKING, breaking.html)`: contiene `kicker_tema`/`titular`/`valor`/`contexto`/`parrafo_reaccion`, sin `{{`/`}}` | `test_breaking_no_placeholders` (nuevo) |
| AC4 | `pytest` puro | `build_html` con `kicker_tema == ""`: sin `{{`/`}}` (token resuelto a vacío); `:empty` presente en el CSS | `test_breaking_kicker_vacio` (nuevo) + `rg ":empty"` |
| AC5 | `pytest` `skipif` | `render_story(PAYLOAD_BREAKING, breaking.html)` → PNG existe, IHDR `(1920,1080)`, `> 5 KB` | `test_breaking_render_dimensiones` (nuevo) |
| AC6 | `rg` (estructural) | `rg -i "CIFRA CLAVE" breaking.html` ≥1; `rg "soporte\|resistencia\|variacion_flecha\|precio_actual" breaking.html` → 0 | manual/gate |
| AC7 | `rg` (estructural) | `rg "breaking" .claude/commands/story.md` ≥2 | manual/gate |
| AC8 | `rg` (estructural) | `rg "≤ ?70\|≤ ?100\|≤ ?280\|≤ ?30" .claude/commands/story.md` ≥1 | manual/gate |
| AC9 | `rg` (estructural) | `rg -i "no ejecuta su propia búsqueda\|no busca por cuenta propia\|no reusa" story.md` ≥1 en el bloque | manual/gate |
| AC10 | `rg` (estructural) | `rg "breaking" CLAUDE.md` ≥1 en sección "Stories GI" | manual/gate |
| AC11 | `git diff` (estructural) | `git diff master -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html scripts/ruta_story.ps1` → vacío | manual/gate |

Constante de test propuesta (análoga a `PAYLOAD_QUOTE`), a agregar tras `PAYLOAD_QUOTE`
(`tests/test_story_render.py:60-65`) y su ruta de snapshot tras `QUOTE_TEMPLATE`
(`test_story_render.py:29`):

```python
BREAKING_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "breaking.html"

PAYLOAD_BREAKING: dict = {
    "plantilla": "breaking",
    "kicker_tema": "BANCOS CENTRALES",
    "titular": "La Fed sorprende con una pausa más larga de lo esperado",
    "valor": "5,50%",
    "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
    "parrafo_reaccion": (
        "El mercado ajusta expectativas hacia un primer recorte más tardío, "
        "presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
    ),
}
```
El caso vacío usa `{**PAYLOAD_BREAKING, "kicker_tema": ""}`.

---

## Estructura de archivos afectados

```
NUEVOS (en Apply — este design.md NO edita código)
  templates/stories/breaking.html    R1/R3/R4/R5 — snapshot 1920×1080; tokens {{kicker_tema}}/
                                      {{titular}}/{{valor}}/{{contexto}}/{{parrafo_reaccion}};
                                      chip acento rojo + tarjeta "CIFRA CLAVE"; .breaking-kicker:empty
                                      {display:none}; SIN fences IF/FOR, SIN {{sesgo_slug}}, SIN bloque
                                      gráfico ni tarjeta de precio (sin variación/soporte/resistencia/vol).

MODIFICADOS
  .claude/commands/story.md          R6/R7/R8 — PASO 0: agregar `breaking` a [tipo]; bloque "Ruta
                                      `breaking`" (sin búsqueda propia de evento, límites 30/70/100/280,
                                      kicker_tema siempre presente, guardado -Activo o _general).
  tests/test_story_render.py         R9 — 3 tests nuevos (AC3/AC4/AC5) contra breaking.html; sin fixture nuevo.
  CLAUDE.md                          R10 — sección "Stories GI": enumerar `breaking` junto a `alerta`, `quote`.

SIN CAMBIOS (confirmado — AC11)
  scripts/story_render.py            motor intacto (build_context/resolver_loops/_resolver_fences/_FENCES/render_png)
  templates/stories/alerta.html      contrato de Alerta intacto
  templates/stories/quote.html       contrato de Quote intacto
  scripts/ruta_story.ps1             ya acepta -Plantilla y -Activo genéricos
  tests/conftest.py                  no se toca (sys.path vive en el propio test)
  tests/fixtures/stories/*           no se agrega fixture; se reusa el patrón contra snapshot real
  .claude/shared/modo_ejecutivo.md   /story sigue en "No elegibles"
  src/market_data_mcp/**             ninguna capa hexagonal tocada
  docs/design/stories-gi/plantillas-stories-gi.md   sin sección de mapeo dedicada a breaking (OUT del spec)
  pyproject.toml / uv.lock           sin nuevas dependencias

PROHIBIDO TOCAR (6 archivos ajenos del director, ya modificados en el working tree)
  .claude/commands/apertura.md · data/glosario_siglas.json · data/historial_encuestas.json
  templates/encuesta_posicion.txt · templates/encuesta_tendencia.txt · uv.lock
```

---

## Decisiones para el gate humano DESIGN → APPLY

Ninguna decisión bloqueante nueva: el motor no cambia y todas las Q1-Q5 quedaron resueltas en
`spec.md`. Se elevan al director tres confirmaciones de bajo riesgo:

1. **[CONFIRMAR] `breaking.html` no lleva clase de color direccional (`{{sesgo_slug}}`).** A
   diferencia de `alerta.html`, el `<body>` de `breaking` usa `class="breaking"` estática porque
   `breaking` no trae `sesgo`/`variacion` y el helper 2 no puebla `sesgo_slug` (referenciarlo
   dejaría un token huérfano). La dirección se comunica en el texto. *Recomendación*: **aceptar**
   — coherente con que la cifra es editorial, no un dato de mercado en vivo.
2. **[CONFIRMAR] rótulo estático "CIFRA CLAVE" y tarjeta sin variación/flecha/soporte/
   resistencia/vol** (R5), para no sugerir un dato en vivo del motor. Copy y tratamiento sujetos
   a ajuste visual en `apply` (Riesgo B). *Recomendación*: **aceptar** el copy provisional.
3. **[CONFIRMAR] límites editoriales `kicker_tema ≤ 30`, `titular ≤ 70`, `contexto ≤ 100`,
   `parrafo_reaccion ≤ 280`** como guía del comando (no validación del motor), sujetos a ajuste
   visual en `apply` (Riesgo C). *Recomendación*: **aceptar** los valores provisionales.

---

## Desglose de implementación (tareas)

> Ordenadas por dependencia. Cada tarea que toca código/plantilla ejecutable lleva su criterio de
> aceptación mapeado a `spec.md`. TDD: escribir/ajustar el test antes de cerrar la tarea. Este
> desglose deja el Change listo para `break-to-tasks` (`tasks.md`); **no** se escribe `tasks.md`
> en esta fase.

### 1. Snapshot — `templates/stories/breaking.html` (nuevo)

- [ ] **1.1 Andamiaje de marca.** Copiar el bloque `@font-face` + `html, body` de `alerta.html`
  (fuentes locales `fonts/*.woff2`, fondo `#0D0D1A` con degradados `alerta.html:51-54`, viewport
  1920×1080, `overflow: hidden`) y el footer estándar (`@grupointeligencia` + disclaimer CFD,
  **sin** `{{fuente}}`). Comentario de cabecera "NO cambiar nombres de tokens sin actualizar
  tests". `<body class="breaking">` estático (SIN `{{sesgo_slug}}` ni tokens de Alerta).
  *Criterios (AC1/AC2)*: `rg "width: 1920px"` y `rg "height: 1080px"` en `breaking.html` ≥1 c/u;
  `rg "<!-- (IF|FOR):" breaking.html` → 0.
- [ ] **1.2 Cuerpo editorial y tokens.** `.breaking-cuerpo` en columna centrada:
  `<span class="breaking-kicker">{{kicker_tema}}</span>` (chip rojo estilo `.chip-categoria`),
  `<h1 class="breaking-titular">{{titular}}</h1>` (Syne), tarjeta `.breaking-cifra` con rótulo
  estático "CIFRA CLAVE" + `<span class="breaking-cifra-valor">{{valor}}</span>` (borde/acento
  rojo estilo `.tarjeta-precio`, SIN variación/soporte/resistencia/vol), `<p
  class="breaking-contexto">{{contexto}}</p>`, `<p
  class="breaking-reaccion">{{parrafo_reaccion}}</p>`. *Criterios (AC3/AC6)*:
  `test_breaking_no_placeholders` verde; `rg -i "CIFRA CLAVE" breaking.html` ≥1;
  `rg "soporte|resistencia|variacion_flecha|precio_actual" breaking.html` → 0. *(depende de 1.1)*
- [ ] **1.3 Colapso `:empty` de `kicker_tema`.** `.breaking-kicker:empty { display: none; }`.
  *Criterios (AC4)*: `rg ":empty" breaking.html` ≥1; `test_breaking_kicker_vacio` verde.
  *(depende de 1.2)*

### 2. Tests — `tests/test_story_render.py` (aditivo, R9)

- [ ] **2.1 Constante y test de mapeo con kicker.** Agregar `BREAKING_TEMPLATE = _REPO_ROOT /
  "templates" / "stories" / "breaking.html"` + `PAYLOAD_BREAKING`.
  `test_breaking_no_placeholders`: `build_html(PAYLOAD_BREAKING, BREAKING_TEMPLATE)` contiene
  `kicker_tema`/`titular`/`valor`/`contexto`/`parrafo_reaccion`, sin `{{`/`}}`. *Criterio (AC3)*.
  *(depende de 1.2)*
- [ ] **2.2 Test de colapso `kicker_tema == ""`.** `test_breaking_kicker_vacio`:
  `build_html({**PAYLOAD_BREAKING, "kicker_tema": ""}, BREAKING_TEMPLATE)` no contiene `{{`/`}}`
  (token resuelto a vacío, no omitido). *Criterio (AC4)*. *(depende de 1.3)*
- [ ] **2.3 Test de render real.** `test_breaking_render_dimensiones` con
  `@pytest.mark.skipif(not _chromium_disponible())`: `render_story(PAYLOAD_BREAKING,
  BREAKING_TEMPLATE, salida)` → PNG existe, `> 5 KB`, `_png_size == (1920, 1080)`. **No tocar**
  `conftest.py`. *Criterio (AC5)*; *Criterio suite*: `uv run pytest tests/test_story_render.py`
  verde. *(depende de 1.2)*

### 3. Comando — `.claude/commands/story.md` (R6/R7/R8)

- [ ] **3.1 Registrar `[tipo]` `breaking` en PASO 0.** Actualizar la lista dura y el mensaje de
  tipos disponibles para incluir `breaking` junto a `alerta`, `quote`; ruteo al bloque "Ruta
  `breaking`". *Criterio (AC7)*: `rg "breaking" story.md` ≥2.
- [ ] **3.2 Bloque "Ruta `breaking`" de recolección editorial.** Sin datos de mercado y **sin
  búsqueda propia de evento** (fuente `/noticia`·`/alerta` o dictado directo, CB-5); dirección
  explícita obligatoria; límites `kicker_tema ≤ 30`/`titular ≤ 70`/`contexto ≤ 100`/
  `parrafo_reaccion ≤ 280` (guía, no validación); `kicker_tema` siempre presente (`""` si no hay
  tema); guardado `-Activo [TICKER]` o `_general` según decisión editorial (R8); reuso preview →
  render → `ruta_story.ps1 -Plantilla "breaking"` / `--template templates/stories/breaking.html`.
  *Criterios (AC7/AC8/AC9)*: `rg "breaking" story.md` ≥2; `rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30"
  story.md` ≥1; `rg -i "no ejecuta su propia búsqueda|no busca por cuenta propia|no reusa"
  story.md` ≥1. *(depende de 3.1)*

### 4. Documentación — `CLAUDE.md` (R10)

- [ ] **4.1 Enumerar `breaking` en la sección "Stories GI".** Cambiar "`[tipo]` soportados hoy:
  `alerta`, `quote`" por "`alerta`, `quote`, `breaking`", sin tocar el resto. *Criterio (AC10)*:
  `rg "breaking" CLAUDE.md` ≥1 en la sección.

### 5. No-regresión (AC11)

- [ ] **5.1 Confirmar motor/Alerta/Quote/helper intactos.** *Criterio (AC11)*: `git diff master
  -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html
  scripts/ruta_story.ps1` → vacío.

---

## Referencias

- `spec.md` (#123 — R1-R10, CB-1..CB-7, AC1-AC11, Q1-Q5 resueltas, riesgos A/B/C).
- `proposal.md` / `idea.md` (#123 — contexto y preguntas originales).
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/design.md` — molde directo
  de este documento; patrón de campo opcional (token + `:empty`) reutilizado sin cambios.
- `.pulse/changes/archive/119-.../spec.md` — contrato del motor generalizado (no reabierto).
- `scripts/story_render.py:33,55-179` — `_FENCES`, `build_context` (escalares + 4 helpers),
  `_fence_presente`; **no se modifican**.
- `templates/stories/alerta.html:14-58,92-115,145-231,398-409` — andamiaje de marca (fuentes/
  paleta/footer), chip `.chip-categoria` y tarjeta `.tarjeta-precio` (acentos rojos `#E84040`)
  que `breaking` reutiliza para chip y tarjeta de cifra (con layout distinto).
- `templates/stories/quote.html` — molde más cercano de plantilla simple sin fences/loops, con
  campo opcional resuelto vía `:empty` CSS (`.quote-cargo:empty`).
- `tests/test_story_render.py:29,60-65,295-326` — patrón de `PAYLOAD_QUOTE`, tests de mapeo de
  `quote` y test de render con `skipif`, base de los 3 tests nuevos.
- `.claude/commands/story.md:6-8,17-104` — comando a extender (PASO 0 + bloque "Ruta `quote`"
  como molde del bloque "Ruta `breaking`").
- `CLAUDE.md` sección "Stories GI" — enumeración de `[tipo]`.
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 12 `breaking`
  (contrato de campos canónico).
- Issue #123 (`bbenja11/grupo-analisis-mercado`) — issue madre; #121 (quote) y #119 (motor)
  precedentes.
</content>
