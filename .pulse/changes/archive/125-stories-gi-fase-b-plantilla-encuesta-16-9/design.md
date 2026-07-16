# Design — Stories GI · Fase B: plantilla Encuesta 16:9 (#125)

> Diseño técnico de `spec.md` (Change #125, dominio `stories-gi`). Implementa exactamente
> R1-R10, CB-1..CB-8 y AC1-AC12. **Hereda** el motor generalizado de Fase A (#119, `master`
> v0.2.0) **sin reabrirlo** — `scripts/story_render.py` no se toca — y el patrón de campo
> opcional (token + `:empty`) validado en Fase B/`quote` (#121) y replicado en Fase B/`breaking`
> (#123) **sin reabrirlos**. Alcance 100% aditivo: un snapshot HTML nuevo, un `[tipo]` nuevo en
> el comando, tests de mapeo puros y una línea de `CLAUDE.md`. **No contiene código de
> aplicación** — solo el plan técnico + tareas. `encuesta` es el **cuarto** consumidor del motor
> **sin** fences `IF`/`FOR` ni loops (tras `quote` y `breaking`) — con **dos** campos opcionales
> (`kicker`, `nota_cierre`) resueltos por CSS, no por el motor — y el **primero** con paleta
> **oscura/azul** (las tres previas son oscura/rojo).

## Nota sobre invariantes de arquitectura

Este Change **no toca ninguna capa hexagonal** ni el motor. El MCP `src/market_data_mcp/`
queda intacto. Lo que se agrega es: un snapshot HTML+CSS estático
(`templates/stories/encuesta.html`), cuatro tests puros/`skipif` (`tests/test_story_render.py`),
un bloque de prompt (`.claude/commands/story.md`) y una frase de doc (`CLAUDE.md`). El motor
sigue siendo un renderer "tonto" (payload → HTML → PNG) sin lógica de negocio; la recolección
editorial vive en el prompt. **No se agregan dependencias** (Playwright ya es opcional
`[project.optional-dependencies] stories`). `encuesta` no delega en ningún dato en vivo del
motor (`get_asset_levels`, `obtener_calendario_macro`, etc.): es 100% sentimiento editorial,
mismo contrato que `/encuesta` (CLAUDE.md: "3 tipos sin precios ni educación").

---

## Hallazgo previo — no hay azul en `alerta.html` (lectura obligada del insumo)

`templates/stories/alerta.html` **no contiene ningún hex azul**. Verificado leyendo el archivo
completo: sus únicos acentos son **rojo** `#E84040`, **verde** `#00DC82` y **rojo claro**
`#F5A3A3`; la sensación "oscuro/rojo" nace de los **tintes rojizos del degradado** —
`#2A1220` (radial, `alerta.html:53`) y `#120A12` (stop medio del linear, `alerta.html:54`) —
sobre la base neutra `#0D0D1A`. Lo mismo en `quote.html` y `breaking.html` (misma paleta base +
acento rojo). **No existe hoy en el repo ninguna plantilla ya renderizada en azul de la cual
copiar el hex** (registrado también como Riesgo B del `spec.md` y de `idea.md`).

Consecuencia de diseño: "derivar el azul de `alerta.html`" no es literalmente posible. La única
paleta azul **presente en el repo** (no en el canvas Claude Design de solo lectura) son los tres
candidatos documentados en `spec.md` (líneas 30-32, 71, 336-340, 356) e `idea.md` (líneas
57-60): `#1E3A5F` (tema azul de la fila 04 `idea` del design doc), `#3E91AF` y `#53C1AB`
(acentos de marca GI observados). Estos hexes viven en **docs commiteados del repo**, no en el
canvas; usarlos **no** es "inventar un azul nuevo" ni "sacarlo del canvas". Este design **fija**
el mapeo azul 1:1 sobre el uso del rojo de `alerta.html` a partir de esos tres candidatos
(sección 1) y lo eleva como la **única** confirmación material del gate DESIGN → APPLY (Riesgo B),
con el resto de neutros (base/grises/blancos) **idénticos byte-a-byte** a `breaking`/`quote`.

---

## Technical Approach

### 0. Por qué el motor no necesita ni un solo cambio (R3 · AC2/AC12)

`build_html` (Fase A) es `loops → fences → tokens → guardia`. Para `encuesta`:
- **Loops** (`resolver_loops`): `encuesta.html` no tiene `<!-- FOR -->` → no-op, el HTML pasa
  igual (mismo comportamiento validado en `quote`/`breaking`; `encuesta` no tiene ningún campo
  array).
- **Fences** (`_resolver_fences`/`_fence_presente`): `encuesta.html` no tiene `<!-- IF -->` →
  no-op. `_FENCES` sigue fija en `("variacion","vol","chart_img","chart_svg")`
  (`scripts/story_render.py:29`); ninguno aplica a `encuesta`. El fence genérico por-clave
  (`_expandir_elemento`) solo existe **dentro** de un bloque `FOR`, que `encuesta` no usa → no
  hay forma de condicionar `kicker`/`nota_cierre` vía fence sin tocar el motor (fuera de
  alcance). Ambos campos opcionales se resuelven por CSS `:empty` (sección 1, R4).
- **Tokens** (`build_context` + `_sustituir_tokens`): `build_context` recorre `payload.items()`
  y agrega `contexto[clave] = str(valor)` por cada escalar. Con el payload de R2 produce
  `{"kicker": "...", "pregunta": "...", "opcion_a": "...", "opcion_b": "...",
  "nota_cierre": "..."}` (más `plantilla`, no referenciado en el HTML → no-op silencioso, CB-1
  heredado). Los 4 helpers de derivación de Fase A (flecha por `direccion`, `sesgo_slug` por
  `sesgo`, `impacto_badge` por `impacto`, `chart_src` por `chart_png`) **no se disparan** porque
  `encuesta` no trae ninguna de esas claves (R2). `_sustituir_tokens` reemplaza los cinco
  `{{...}}` por sus valores.
- **Guardia** (`_validar_sin_huerfanos`): tras sustituir, no queda ningún `{{...}}` → pasa.

**Punto crítico de diseño (`kicker == ""` / `nota_cierre == ""`, R2/R4)**: `str("") == ""`,
entonces `contexto["kicker"] == ""` (ídem `nota_cierre`) y `_sustituir_tokens` reemplaza el
`{{...}}` por cadena vacía. El token **se resuelve** (no queda huérfano) → la guardia pasa. El
colapso visual es responsabilidad exclusiva del CSS (`:empty`), no del motor — patrón idéntico a
`.quote-cargo:empty` (#121) y `.breaking-kicker:empty` (#123).

**Punto crítico de diseño (ningún token de Alerta en `encuesta.html`)**: en `alerta.html` el
`<body class="sesgo-{{sesgo_slug}}">` funciona porque el helper puebla `sesgo_slug` desde
`sesgo`. `encuesta` **no** trae `sesgo`/`variacion`/`impacto`/`chart_png` → esos tokens no
existen en el contexto. Por tanto `encuesta.html` **no debe** referenciar `{{sesgo_slug}}`,
`{{precio_actual}}`, `{{variacion_flecha}}`, `{{soporte}}`, `{{resistencia}}`, `{{vol_pct}}`,
`{{chart_src}}`, `{{fuente}}`, `{{fecha_hora}}` ni ningún token de Alerta: sería huérfano y la
guardia abortaría. El `<body>` de `encuesta` lleva una clase **estática** (`class="encuesta"`),
sin token de color direccional. La direccionalidad de la encuesta vive **en el texto** de la
pregunta/opciones (redactadas con criterio de `/encuesta`), no en una clase CSS de sesgo.

### 1. Snapshot `templates/stories/encuesta.html` (R1/R3/R4/R5 · AC1/AC2/AC4/AC6/AC7)

Archivo nuevo, viewport 1920×1080. Reutiliza **verbatim** el andamiaje de marca de
`alerta.html:14-58` = `breaking.html:20-72`: los cuatro `@font-face` (Syne 800 / DM Sans 400·700
/ Space Grotesk 600 desde `fonts/*.woff2`), `* { box-sizing }`, el bloque `html, body` con
`width: 1920px; height: 1080px; overflow: hidden`, y `.story { width:1920; height:1080;
padding: 56px 72px 40px; display:flex; flex-direction:column }`. Footer **idéntico** a
`quote`/`breaking` (`.footer` + `.footer-marca` `@grupointeligencia` / `grupointeligencia.com` +
`.footer-disclaimer` con el disclaimer CFD **verbatim**, **sin** `{{fuente}}`). El comentario de
cabecera advierte "NO cambiar nombres de tokens sin actualizar tests" (igual criterio que
`alerta.html:1-7`, `quote.html:1-7`, `breaking.html:1-12`).

**La ÚNICA diferencia con `breaking.html` es la paleta**: se sustituyen los tintes rojizos del
degradado y el acento rojo por la variante **azul** (tabla "Paleta azul FIJADA"). Todos los
neutros quedan idénticos.

**Boceto del DOM** (contenedor raíz `.story` en columna: cuerpo + footer; **una sola columna**
editorial centrada, sin `.columna-grafico`, mismo patrón `flex-direction: column` que
`quote`/`breaking`):

```
<body class="encuesta">                          (clase estática, SIN {{sesgo_slug}})
  <div class="story">
    <div class="encuesta-cuerpo">                 (flex:1; columna; align-items:center; justify-content:center; text-align:center)
      <span class="encuesta-kicker">{{kicker}}</span>       chip acento AZUL — colapsa :empty (opcional)
      <h1 class="encuesta-pregunta">{{pregunta}}</h1>       Syne 800, jerarquía de titular (núcleo)
      <div class="encuesta-opciones">             (flex row; gap; align-items:stretch; justify-content:center)
        <div class="encuesta-opcion">             tarjeta simétrica, borde AZUL (estilo .tarjeta-precio/.breaking-cifra)
          <span class="encuesta-opcion-rotulo">OPCIÓN A</span>   TEXTO ESTÁTICO (no token, R5)
          <span class="encuesta-opcion-valor">{{opcion_a}}</span>   Syne 800, grande (núcleo)
        </div>
        <span class="encuesta-vs">VS</span>        TEXTO ESTÁTICO separador central (no token, R5)
        <div class="encuesta-opcion">             tarjeta simétrica gemela, borde AZUL
          <span class="encuesta-opcion-rotulo">OPCIÓN B</span>   TEXTO ESTÁTICO (no token, R5)
          <span class="encuesta-opcion-valor">{{opcion_b}}</span>   Syne 800, grande (núcleo)
        </div>
      </div>
      <p class="encuesta-nota">{{nota_cierre}}</p>          línea secundaria — colapsa :empty (opcional)
    </div>
    <div class="footer">                            (idéntico a quote/breaking, SIN {{fuente}})
      <div class="footer-marca">
        <span>@grupointeligencia</span><span>grupointeligencia.com</span>
      </div>
      <p class="footer-disclaimer">Los CFD son instrumentos complejos … no constituye asesoría financiera.</p>
    </div>
  </div>
</body>
```

**Tokens → elemento → clase → estilo** (los únicos cinco `{{...}}` del archivo):

| Token | Elemento HTML | Clase CSS | Fuente/peso · tamaño · color | Notas |
|---|---|---|---|---|
| `{{kicker}}` | `<span>` | `.encuesta-kicker` | Space Grotesk 600 · 20px · texto `#53C1AB`, fondo `rgba(62,145,175,0.14)`, borde `1px solid rgba(62,145,175,0.5)`, `border-radius:999px`, mayúsculas, `letter-spacing:0.06em`, `padding:10px 22px` | **Opcional**; admite `""` → colapsa por `:empty` (R2/R4). Réplica del `.chip-categoria` de Alerta en azul. |
| `{{pregunta}}` | `<h1>` | `.encuesta-pregunta` | Syne 800 · ~56px · `#FFFFFF`, `line-height:1.2`, `max-width:1400px`, `margin-top:28px` | Núcleo obligatorio; jerarquía de titular (entre `.quote-texto` 56px y `.breaking-titular` 64px). |
| `{{opcion_a}}` | `<span>` | `.encuesta-opcion-valor` (dentro de la 1ª `.encuesta-opcion`) | Syne 800 · ~44px · `#FFFFFF` | Núcleo obligatorio; etiqueta corta de sentimiento (ej. "Alcista"). Sin flecha, sin color condicional. |
| `{{opcion_b}}` | `<span>` | `.encuesta-opcion-valor` (dentro de la 2ª `.encuesta-opcion`) | Syne 800 · ~44px · `#FFFFFF` | Núcleo obligatorio; tarjeta gemela simétrica de `opcion_a`. |
| `{{nota_cierre}}` | `<p>` | `.encuesta-nota` | DM Sans 400 · 21px · `#C9C5D4`, `line-height:1.45`, `margin-top:32px` | **Opcional**; admite `""` → colapsa por `:empty` (R2/R4). Línea discreta de cierre. |

Rótulos y separador **estáticos** (nunca tokens): `.encuesta-opcion-rotulo` ("OPCIÓN A" /
"OPCIÓN B", Space Grotesk 600 · 16px · `#A9A5B4`, mayúsculas, `letter-spacing:0.05em`, réplica de
`.stat-label`/`.breaking-cifra-rotulo`); `.encuesta-vs` ("VS", Space Grotesk 600 · ~26px ·
`#3E91AF`, `align-self:center`). Tarjetas `.encuesta-opcion`: `border:2px solid #3E91AF;
background:rgba(62,145,175,0.08); border-radius:22px; padding:26px 34px; display:flex;
flex-direction:column; gap:12px; align-items:center; flex:1 1 0` (o ancho fijo ~360px) — réplica
del tratamiento de `.tarjeta-precio` (`alerta.html:145-152`) / `.breaking-cifra`
(`breaking.html:113-124`), **pero** con layout "rótulo estático + valor", **sin**
`.tarjeta-cabecera`, `.precio-linea`, `.variacion`, `.stats`, `.tag-riesgo` ni fila de
soporte/resistencia/vol. Contenedor `.encuesta-opciones`: `display:flex; flex-direction:row;
gap:40px; align-items:stretch; justify-content:center; margin-top:44px`.

**Paleta azul FIJADA** (decisión de este design; todos los hexes son repo-present — ver
"Hallazgo previo"; se elevan como confirmación de gate, Riesgo B):

| Rol visual | `alerta.html` (rojo, línea) | `encuesta.html` (azul FIJADO) | Procedencia del hex azul |
|---|---|---|---|
| Base de fondo | `#0D0D1A` (`alerta.html:51`) | `#0D0D1A` (**sin cambio**) | Neutro compartido por las 3 plantillas existentes. |
| Tinte radial | `#2A1220` (`alerta.html:53`) | **`#1E3A5F`** | `spec.md:30` / `idea.md:58` — tema azul de la fila 04 `idea` del design doc. |
| Stop medio del linear | `#120A12` (`alerta.html:54`) | **`#0D0D1A`** (neutralizado) + `#1E3A5F` al 100% | Se quita el cast rojizo; el degradado usa solo `#0D0D1A` + `#1E3A5F` (cero invención). |
| Acento sólido (borde tarjeta, "VS", `rgba` de chip/tarjeta) | `#E84040` (`alerta.html:108,148,176`) | **`#3E91AF`** → `rgba(62,145,175,·)` | `spec.md:30` / `idea.md:58` — acento de marca GI. |
| Texto/realce claro del chip | `#F5A3A3` (`alerta.html:114`) | **`#53C1AB`** | `spec.md:30` / `idea.md:58` — acento de marca GI (candidato claro; evita inventar un tinte). |

Regla exacta del degradado (única línea que cambia vs. `breaking.html:56-59`):
```css
html, body {
  background: #0D0D1A;
  background-image:
    radial-gradient(90% 120% at 0% 20%, #1E3A5F 0%, #0D0D1A 55%),
    linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #1E3A5F 100%);
  color: #F5F3F7;   /* neutro, sin cambio */
}
```

Neutros **idénticos** a `breaking`/`quote` (no se tocan): `#FFFFFF` (pregunta / valores de
opción), `#F5F3F7` (`html/body` color base + `.footer-marca`), `#C9C5D4` (`.encuesta-nota`),
`#A9A5B4` (rótulos estáticos "OPCIÓN A/B"), `#6E6A7A` (`.footer-disclaimer`).

**Los dos colapsos `:empty`** (R4 · AC4/AC5) — dos reglas CSS, una por campo opcional:
```css
.encuesta-kicker:empty { display: none; }
.encuesta-nota:empty   { display: none; }
```
Con el campo no vacío se muestra el elemento (chip sobre la pregunta / línea bajo las opciones).
Con el campo `== ""` el contenedor queda vacío → `:empty` lo saca del flujo (`display:none`,
colapsa el espacio, no solo el texto) → el layout se reacomoda sin hueco en blanco. Patrón exacto
validado en `quote` R4 (`.quote-cargo:empty`) y `breaking` R4 (`.breaking-kicker:empty`).
Verificable con `rg ":empty" templates/stories/encuesta.html` ≥2 matches (AC4).

**Layout "A vs B" sin dato de mercado en vivo (R5 · AC7)**: dos tarjetas simétricas gemelas lado
a lado con separador estático "VS"; se omite deliberadamente todo elemento de dato en vivo — sin
flecha `▲/▼`, sin color verde/rojo condicional por dirección, sin fila de
soporte/resistencia/vol, sin `{{precio_actual}}`/`{{variacion_flecha}}`, sin clases
`sesgo-alcista`/`sesgo-bajista`. Verificable con
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/encuesta.html` → 0
(AC7). El detalle fino de `font-size`/`padding`/anchos exactos → se afina al autorar el CSS en
`apply` (Riesgo C), no bloquea Design.

### 2. Contrato de payload `story_encuesta` (R2 · AC3)

```json
{
  "plantilla": "encuesta",
  "kicker": "ENCUESTA DEL DÍA",
  "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
  "opcion_a": "Alcista",
  "opcion_b": "Bajista",
  "nota_cierre": "Vota en la encuesta fijada del grupo"
}
```

- Claves del payload: `plantilla` (ruteo, no tokenizada), `kicker`, `pregunta`, `opcion_a`,
  `opcion_b`, `nota_cierre`. **Sin** campos array, `chart_png`, `variacion`, `sesgo`, `impacto`,
  `activo` ni dato del motor.
- `kicker` y `nota_cierre` **siempre presentes** en el payload (nunca ausentes ni `None`);
  admiten `""` (R2/R4) — son los **dos** campos opcionales, sin fence (mismo patrón que
  `autor_sub` en `quote` y `kicker_tema` en `breaking`).
- `pregunta`, `opcion_a`, `opcion_b` **siempre no vacíos** — el comando (R7) nunca los construye
  como `""`; son el núcleo mínimo de una encuesta binaria. Si el director no puede dar alguno, el
  comando insiste, nunca cadena vacía en estos tres.
- `pregunta`/`opcion_a`/`opcion_b` son texto editorial de **sentimiento puro** (mismo criterio
  que el mensaje WhatsApp de `/encuesta`) — no llevan formateo `digits` de `config/activos.json`
  ni dato en vivo del motor.
- Variante `kicker == ""` (mismo payload, chip vacío) y variante `nota_cierre == ""` (nota
  vacía): renderizan pregunta + dos opciones, con el contenedor respectivo colapsado por CSS.

### 3. Comando `.claude/commands/story.md` (R6/R7/R8 · AC8/AC9/AC10)

Cambios acotados, aditivos, replicando el patrón con que hoy se registran `alerta`, `quote` y
`breaking`:

1. **PASO 0 — lista de `[tipo]`** (`story.md:6-8,21-32`): agregar `encuesta` a los tipos
   soportados. La validación pasa de "soportados: `alerta`, `quote`, `breaking`" a "…, `encuesta`"
   (líneas 6, 21, 23, 27, 30). El mensaje de tipos disponibles del PASO 0 lista los cuatro. Si el
   tipo confirmado es `encuesta`, saltar al bloque "Ruta `encuesta`" (los PASO 1-7 son de
   `alerta`; los bloques "Ruta `quote`"/"Ruta `breaking`" son de esos tipos). El flag `ejecutivo`
   sigue avisado-y-continúa (CB-4, sin cambios).

2. **Bloque de recolección editorial nuevo** ("Ruta `encuesta`", hermano de "Ruta `breaking`",
   tras `story.md:195`): `encuesta` **no llama a `get_asset_levels`** ni a ninguna tool de mercado
   (`obtener_calendario_macro`, `get_chart_objects`, `get_symbol_spec`), y **no ejecuta su propia
   búsqueda de evento** (no invoca WebSearch) — es una pieza 100% editorial de **sentimiento
   puro**, mismo contrato que `/encuesta` (R7.2, AC10). El flujo es:
   - **Recolección editorial (R7.1)**: preguntar la pregunta binaria y sus dos opciones con el
     criterio de sentimiento puro de `/encuesta` (sin precios ni educación):
     ```
     ¿Cuál es la pregunta de la encuesta? (ej. "¿Cuál creen que será la tendencia hoy del Oro?")
     ¿Opción A?
     ¿Opción B?
     ¿Kicker/tema del chip? (ej. "ENCUESTA DEL DÍA" — Intro para omitir)
     ¿Nota de cierre? (ej. "Vota en la encuesta fijada del grupo" — Intro para omitir)
     ```
   - **Atajo opcional (R7.3, CB-8)**: si el director ya corrió `/encuesta [tipo] [activo]` en la
     misma sesión, ofrecer reutilizar esa pregunta/opciones ya redactadas como base editorial —
     no bloquea ni exige corrida previa; si prefiere redactar de cero, lo hace directamente.
   - **Layout único (R7.4)**: la Story usa siempre el mismo layout binario `opcion_a`/`opcion_b`
     sin distinguir entre los 3 tipos de `/encuesta` (`posicion`/`tendencia`/`movimiento`) — el
     tipo de origen se refleja en la **redacción** de la pregunta/opciones, no en el layout.
   - **Límites editoriales (R6 · AC9)**: documentar en el comando `kicker ≤ 30`, `pregunta ≤ 90`,
     `opcion_a ≤ 25`, `opcion_b ≤ 25`, `nota_cierre ≤ 80` caracteres. Guía de redacción del
     comando, **no** validación del motor (CB-2: el motor no trunca ni aborta por longitud). Si
     algún campo excede, el comando ajusta la redacción antes del preview.
   - **Payload (R7.5)**: construir con `kicker` y `nota_cierre` **siempre presentes** — si el
     director no da alguno, `""` (nunca omitir la clave, CB-1). Los otros tres campos siempre no
     vacíos.
   - **Guardado con o sin `-Activo` (R8 · CB-6)**: preguntar si la pregunta nombra un activo
     protagonista claro (decisión **editorial** del director, no regla automática nueva ni del
     motor ni de `ruta_story.ps1`):
     ```
     ¿La pregunta tiene un activo protagonista claro? (ticker, o "no" si es general/ambigua)
     ```
     - **Sí** (ej. "…tendencia hoy del Oro" → Oro) → `-Activo [TICKER_MT5]` (normalizado contra
       `config/activos.json`, mismo criterio que `/chart` PASO 1).
     - **No / ambiguo / varios activos** (ej. "¿Suben o bajan los mercados esta semana?") →
       `-Activo "_general"` (igual que `quote`/`breaking`).
   - Reusar el flujo compartido preview → aprobación (CB-3: si no aprueba, no se renderiza ni
     guarda nada en `data/stories/`) → render → guardado con:
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

Verificación: `rg "encuesta" .claude/commands/story.md` ≥2 (AC8 — al menos una en PASO 0, otra en
el bloque "Ruta `encuesta`"); `rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" story.md` ≥1 (AC9); `rg -i "no llama
a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado" story.md` ≥1 dentro del
bloque (AC10). Nota: el PASO 0 hoy referencia CB-1 del `.pulse/specs/stories-gi/spec.md` para
tipo inválido — se mantiene, ahora con la lista de cuatro tipos (CB-5).

### 4. `CLAUDE.md` sección "Stories GI" (R10 · AC11)

Edición principal (requerida por AC11): la enumeración de `[tipo]` soportados en el **párrafo de
la sección "Stories GI"** (hoy: "`[tipo]` soportados hoy: `alerta`, `quote`, `breaking` (Fase B,
issues #121/#123)") pasa a incluir `encuesta` (ej. "…`alerta`, `quote`, `breaking`, `encuesta`
(Fase B, issues #121/#123/#125)"). No se toca el resto del párrafo ni de la sección (regla "solo
lectura" del canvas, guardado, gitignore, etc. quedan igual).

Edición secundaria **recomendada** (consistencia, no exigida por AC11): la fila `/story [tipo]`
de la tabla "Slash Commands" dice hoy "Único `[tipo]` soportado hoy: `alerta`…" — quedó
**desactualizada** desde #121/#123 (no menciona `quote`/`breaking`). Refrescarla a "`[tipo]`
soportados hoy: `alerta`, `quote`, `breaking`, `encuesta`" es una corrección de bajo riesgo que
alinea la tabla con la sección; **no bloqueante** y se marca como opcional para no exceder el
alcance de R10 (el precedente #123 dejó esa fila estancada). Verificación:
`rg "encuesta" CLAUDE.md` ≥1 match en la sección "Stories GI" (AC11), distinguible por contexto de
las menciones ya existentes al comando `/encuesta` de texto plano.

---

## Casos borde (mapa CB → diseño)

| CB | Situación | Comportamiento diseñado |
|---|---|---|
| CB-1 | `kicker`/`nota_cierre` ausentes del payload (no `""`) | El comando (R7.5) siempre construye ambas claves, aunque sean `""`. Si por error se omitiera alguna, el `{{...}}` queda huérfano → guardia `_validar_sin_huerfanos` → `StoryRenderError` (fail-fast heredado), no colapso silencioso distinto al de R4. |
| CB-2 | Algún campo excede el límite editorial (R6) | El comando ajusta la redacción antes del preview; el motor no valida longitud — no aborta ni trunca. |
| CB-3 | Director rechaza el preview | No se renderiza ni guarda nada en `data/stories/` (criterio heredado de `.pulse/specs/stories-gi/spec.md`). |
| CB-4 | `/story encuesta ejecutivo` | Avisa que `/story` no soporta el flag y continúa la Story normal (criterio ya vigente para `alerta`/`quote`/`breaking`, sin cambios). |
| CB-5 | `[tipo]` inválido (ni `alerta`/`quote`/`breaking`/`encuesta`) | PASO 0 informa la lista actualizada de cuatro tipos y vuelve a preguntar; nunca asume un tipo por defecto. |
| CB-6 | Activo protagonista ambiguo / varios activos | El director decide al responder R8; sin activo único claro → `_general` (igual que `quote`/`breaking`). |
| CB-7 | `opcion_a`/`opcion_b` no son antónimos exactos (ej. "Alcista" vs "Lateral") | El comando no valida oposición; es criterio editorial del director. La plantilla solo garantiza el layout "A vs B" (R5). |
| CB-8 | Director ya corrió `/encuesta [tipo] [activo]` en la sesión | El bloque ofrece reutilizar esa pregunta/opciones como base editorial (R7.3); no es dependencia dura. |

---

## Tratamiento de riesgos

- **Riesgo A — fidelidad visual sin golden PNG** (heredado R-2 de Fase A/#109 y de
  `quote`/`breaking`): no hay export de referencia 16:9 azul del canvas GI para `encuesta`.
  *Mitigación*: aprobación visual manual del director en la primera corrida real de
  `/story encuesta`. Los tests **no** asertan estética, solo contrato (tokens inyectados, sin
  huérfanos) + dimensiones IHDR `(1920, 1080)`.
- **Riesgo B — hex azul FIJADO desde candidatos repo-present, no desde un render azul existente**:
  `alerta.html` no tiene azul (ver "Hallazgo previo"); este design fija `#1E3A5F` (tinte
  radial/fondo), `#3E91AF` (acento sólido/borde) y `#53C1AB` (realce claro del chip) desde los
  candidatos de `spec.md`/`idea.md`. Sujeto a ajuste visual/confirmación del director en el gate y
  al autorar el CSS en `apply` — no bloquea Design (mismo criterio que Riesgo B de `breaking`).
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir golden PNG,
  los caracteres exactos (`kicker≤30`, `pregunta≤90`, `opcion_*≤25`, `nota_cierre≤80`) pueden
  requerir ajuste tras la primera corrida visual; se documentan como guía editorial del comando,
  no como validación dura del motor (mismo criterio que Riesgo C de `breaking`).
- **Riesgo D — rol semántico de `kicker`**: el design doc no fija si `kicker` es etiqueta fija
  ("ENCUESTA DEL DÍA") o libre por tema → se resuelve como **campo libre editorial** (mismo
  tratamiento que `kicker_tema` de `breaking`), el director lo redacta o lo omite (`""`) en cada
  corrida. No bloquea Design.

---

## Validation Strategy (EDD/TDD) — mapa AC → verificación

Test-first: los tests de mapeo se escriben/ajustan antes de dar el snapshot por bueno.
`encuesta.html` produce tokens 100% escalares → `build_html` es puro y testeable **sin Chromium**;
solo AC6 usa render real (`@pytest.mark.skipif(not _chromium_disponible())`). Sin fixture nuevo en
`tests/fixtures/stories/`, sin tocar `conftest.py` (se reusa el patrón contra el snapshot real
`encuesta.html`, igual que los tests de `alerta.html`/`quote.html`/`breaking.html`).

| AC | Tipo | Verificación | Test |
|---|---|---|---|
| AC1 | `rg` (estructural) | `encuesta.html` contiene `width: 1920px` y `height: 1080px` | manual/gate |
| AC2 | `rg` (estructural) | `rg "<!-- (IF\|FOR):" templates/stories/encuesta.html` → 0 matches | manual/gate |
| AC3 | `pytest` puro | `build_html(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE)`: contiene `kicker`/`pregunta`/`opcion_a`/`opcion_b`/`nota_cierre`, sin `{{`/`}}` | `test_encuesta_no_placeholders` (nuevo) |
| AC4 | `pytest` puro + `rg` | `build_html` con `kicker == ""`: sin `{{`/`}}`; `rg ":empty" encuesta.html` ≥2 | `test_encuesta_kicker_vacio` (nuevo) |
| AC5 | `pytest` puro + `rg` | `build_html` con `nota_cierre == ""`: sin `{{`/`}}`; `:empty` de `.encuesta-nota` presente | `test_encuesta_nota_vacio` (nuevo) |
| AC6 | `pytest` `skipif` | `render_story(PAYLOAD_ENCUESTA, ENCUESTA_TEMPLATE)` → PNG existe, IHDR `(1920,1080)`, `> 5 KB` | `test_encuesta_render_dimensiones` (nuevo) |
| AC7 | `rg` (estructural) | `rg "soporte\|resistencia\|variacion_flecha\|precio_actual" encuesta.html` → 0 | manual/gate |
| AC8 | `rg` (estructural) | `rg "encuesta" .claude/commands/story.md` ≥2 | manual/gate |
| AC9 | `rg` (estructural) | `rg "≤ ?30\|≤ ?90\|≤ ?25\|≤ ?80" .claude/commands/story.md` ≥1 | manual/gate |
| AC10 | `rg` (estructural) | `rg -i "no llama a .get_asset_levels.\|sentimiento puro\|sin precios ni datos de mercado" story.md` ≥1 en el bloque | manual/gate |
| AC11 | `rg` (estructural) | `rg "encuesta" CLAUDE.md` ≥1 en sección "Stories GI" | manual/gate |
| AC12 | `git diff` (estructural) | `git diff master -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html templates/stories/breaking.html scripts/ruta_story.ps1` → vacío | manual/gate |

Constante de test propuesta (análoga a `PAYLOAD_BREAKING`), a agregar tras `PAYLOAD_BREAKING`
(`tests/test_story_render.py:71-81`) y su ruta de snapshot tras `BREAKING_TEMPLATE`
(`test_story_render.py:30`):

```python
ENCUESTA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "encuesta.html"

PAYLOAD_ENCUESTA: dict = {
    "plantilla": "encuesta",
    "kicker": "ENCUESTA DEL DÍA",
    "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
    "opcion_a": "Alcista",
    "opcion_b": "Bajista",
    "nota_cierre": "Vota en la encuesta fijada del grupo",
}
```
Los casos vacíos usan `{**PAYLOAD_ENCUESTA, "kicker": ""}` y
`{**PAYLOAD_ENCUESTA, "nota_cierre": ""}`. Los cuatro tests nuevos se **append**-ean al final del
archivo, tras el bloque de `breaking` (`test_story_render.py:382`), con su propio separador de
sección (`# --- AC3/AC4/AC5/AC6 (#125): snapshot templates/stories/encuesta.html ---`).

---

## Estructura de archivos afectados

```
NUEVOS (en Apply — este design.md NO edita código)
  templates/stories/encuesta.html    R1/R3/R4/R5 — snapshot 1920×1080; tokens {{kicker}}/{{pregunta}}/
                                      {{opcion_a}}/{{opcion_b}}/{{nota_cierre}}; paleta oscura/AZUL
                                      (#1E3A5F fondo/radial, #3E91AF acento/borde, #53C1AB realce chip);
                                      chip azul + 2 tarjetas "A vs B" simétricas (rótulos estáticos
                                      "OPCIÓN A"/"OPCIÓN B" + "VS"); .encuesta-kicker:empty y
                                      .encuesta-nota:empty {display:none}; SIN fences IF/FOR,
                                      SIN {{sesgo_slug}}, SIN bloque gráfico ni tarjeta de precio
                                      (sin variación/soporte/resistencia/vol).

MODIFICADOS
  .claude/commands/story.md          R6/R7/R8 — PASO 0: agregar `encuesta` a [tipo]; bloque "Ruta
                                      `encuesta`" (sin datos de mercado ni búsqueda de evento; sentimiento
                                      puro; límites 30/90/25/25/80; kicker/nota_cierre siempre presentes;
                                      layout binario único; guardado -Activo o _general).
  tests/test_story_render.py         R9 — 4 tests nuevos (AC3/AC4/AC5/AC6) contra encuesta.html; ENCUESTA_TEMPLATE
                                      + PAYLOAD_ENCUESTA; sin fixture nuevo, sin tocar conftest.py.
  CLAUDE.md                          R10 — sección "Stories GI": enumerar `encuesta` junto a `alerta`,
                                      `quote`, `breaking` (+ refresco opcional de la fila /story de la tabla).

SIN CAMBIOS (confirmado — AC12)
  scripts/story_render.py            motor intacto (build_context/resolver_loops/_resolver_fences/_FENCES/render_png)
  templates/stories/alerta.html      contrato de Alerta intacto
  templates/stories/quote.html       contrato de Quote intacto
  templates/stories/breaking.html    contrato de Breaking intacto
  scripts/ruta_story.ps1             ya acepta -Plantilla y -Activo genéricos
  tests/conftest.py                  no se toca (sys.path vive en el propio test)
  tests/fixtures/stories/*           no se agrega fixture; se reusa el patrón contra snapshot real
  .claude/shared/modo_ejecutivo.md   /story sigue en "No elegibles"
  src/market_data_mcp/**             ninguna capa hexagonal tocada
  docs/design/stories-gi/plantillas-stories-gi.md   sin sección de mapeo dedicada a encuesta (OUT del spec)
  pyproject.toml / uv.lock           sin nuevas dependencias

PROHIBIDO TOCAR (archivos ajenos del director, ya modificados en el working tree)
  .claude/commands/apertura.md · data/glosario_siglas.json · data/historial_encuestas.json
  templates/encuesta_posicion.txt · templates/encuesta_tendencia.txt · uv.lock
```

---

## Decisiones para el gate humano DESIGN → APPLY

Ninguna decisión bloqueante nueva de motor: no cambia, y todas las preguntas de `idea.md`/
`proposal.md` quedaron resueltas en `spec.md`. Se elevan al director cuatro confirmaciones de
bajo riesgo (la primera es la única con contenido nuevo material):

1. **[CONFIRMAR — único material] Paleta azul FIJADA sin render azul de referencia.** `alerta.html`
   **no tiene azul**; este design fija, desde los candidatos repo-present de `spec.md`/`idea.md`:
   `#1E3A5F` (fondo/tinte radial), `#3E91AF` (acento sólido: borde de tarjetas, "VS", `rgba` de
   chip) y `#53C1AB` (realce claro del texto del chip). Neutros idénticos a `breaking`/`quote`.
   *Recomendación*: **aceptar** los tres hexes; ajustables visualmente en `apply` (Riesgo B).
2. **[CONFIRMAR] Rótulos estáticos "OPCIÓN A" / "OPCIÓN B" + separador "VS"** (R5), texto del
   snapshot (no tokens), sin flecha/color condicional/soporte/resistencia/vol — para no sugerir un
   dato de mercado en vivo. *Recomendación*: **aceptar** el copy provisional (ajustable en `apply`).
3. **[CONFIRMAR] Dos campos opcionales (`kicker`, `nota_cierre`) por CSS `:empty`**, núcleo
   obligatorio `pregunta` + `opcion_a` + `opcion_b`; `kicker` como campo libre editorial (Riesgo
   D). *Recomendación*: **aceptar**.
4. **[CONFIRMAR] Límites editoriales `kicker≤30`, `pregunta≤90`, `opcion_a≤25`, `opcion_b≤25`,
   `nota_cierre≤80`** como guía del comando (no validación del motor), sujetos a ajuste visual en
   `apply` (Riesgo C). *Recomendación*: **aceptar** los valores provisionales.

---

## Desglose de implementación (tareas)

> Ordenadas por dependencia. Cada tarea que toca código/plantilla ejecutable lleva su criterio de
> aceptación mapeado a `spec.md`. TDD: escribir/ajustar el test antes de cerrar la tarea. Este
> desglose deja el Change listo para `break-to-tasks` (`tasks.md`); **no** se escribe `tasks.md`
> en esta fase.

### 1. Snapshot — `templates/stories/encuesta.html` (nuevo)

- [ ] **1.1 Andamiaje de marca + paleta azul.** Copiar el bloque `@font-face` + `html, body` +
  `.story` de `breaking.html:20-72` (fuentes locales `fonts/*.woff2`, viewport 1920×1080,
  `overflow: hidden`, `padding: 56px 72px 40px`) y el footer estándar (`.footer`/`.footer-marca`
  `@grupointeligencia`/`grupointeligencia.com` + `.footer-disclaimer` CFD verbatim, **sin**
  `{{fuente}}`). Sustituir SOLO el degradado por la variante azul FIJADA: `radial-gradient(… #1E3A5F
  0%, #0D0D1A 55%)` + `linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #1E3A5F 100%)`. Comentario
  de cabecera "NO cambiar nombres de tokens sin actualizar tests". `<body class="encuesta">`
  estático (SIN `{{sesgo_slug}}` ni tokens de Alerta). *Criterios (AC1/AC2)*: `rg "width: 1920px"`
  y `rg "height: 1080px"` en `encuesta.html` ≥1 c/u; `rg "<!-- (IF|FOR):" encuesta.html` → 0.
- [ ] **1.2 Cuerpo editorial y tokens.** `.encuesta-cuerpo` (columna centrada) con:
  `<span class="encuesta-kicker">{{kicker}}</span>` (chip azul estilo `.chip-categoria`, acento
  `#3E91AF`/`#53C1AB`), `<h1 class="encuesta-pregunta">{{pregunta}}</h1>` (Syne 800), contenedor
  `.encuesta-opciones` (flex row) con **dos** `.encuesta-opcion` gemelas — cada una con rótulo
  estático (`OPCIÓN A`/`OPCIÓN B`, `.encuesta-opcion-rotulo`) + `<span
  class="encuesta-opcion-valor">{{opcion_a}}</span>` / `{{opcion_b}}` (Syne 800, borde/acento
  `#3E91AF`, `background: rgba(62,145,175,0.08)`, SIN variación/soporte/resistencia/vol) — y
  separador estático `<span class="encuesta-vs">VS</span>`; luego
  `<p class="encuesta-nota">{{nota_cierre}}</p>`. *Criterios (AC3/AC7)*:
  `test_encuesta_no_placeholders` verde; `rg "soporte|resistencia|variacion_flecha|precio_actual"
  encuesta.html` → 0. *(depende de 1.1)*
- [ ] **1.3 Doble colapso `:empty`.** `.encuesta-kicker:empty { display: none; }` y
  `.encuesta-nota:empty { display: none; }`. *Criterios (AC4/AC5)*: `rg ":empty" encuesta.html`
  ≥2; `test_encuesta_kicker_vacio` y `test_encuesta_nota_vacio` verdes. *(depende de 1.2)*

### 2. Tests — `tests/test_story_render.py` (aditivo, R9)

- [ ] **2.1 Constante y test de mapeo completo.** Agregar `ENCUESTA_TEMPLATE = _REPO_ROOT /
  "templates" / "stories" / "encuesta.html"` (tras `BREAKING_TEMPLATE`) + `PAYLOAD_ENCUESTA` (tras
  `PAYLOAD_BREAKING`). `test_encuesta_no_placeholders`: `build_html(PAYLOAD_ENCUESTA,
  ENCUESTA_TEMPLATE)` contiene `kicker`/`pregunta`/`opcion_a`/`opcion_b`/`nota_cierre`, sin
  `{{`/`}}`. *Criterio (AC3)*. *(depende de 1.2)*
- [ ] **2.2 Test de colapso `kicker == ""`.** `test_encuesta_kicker_vacio`:
  `build_html({**PAYLOAD_ENCUESTA, "kicker": ""}, ENCUESTA_TEMPLATE)` no contiene `{{`/`}}`.
  *Criterio (AC4)*. *(depende de 1.3)*
- [ ] **2.3 Test de colapso `nota_cierre == ""`.** `test_encuesta_nota_vacio`:
  `build_html({**PAYLOAD_ENCUESTA, "nota_cierre": ""}, ENCUESTA_TEMPLATE)` no contiene `{{`/`}}`.
  *Criterio (AC5)*. *(depende de 1.3)*
- [ ] **2.4 Test de render real.** `test_encuesta_render_dimensiones` con
  `@pytest.mark.skipif(not _chromium_disponible())`: `render_story(PAYLOAD_ENCUESTA,
  ENCUESTA_TEMPLATE, salida)` → PNG existe, `> 5 KB`, `_png_size == (1920, 1080)`. **No tocar**
  `conftest.py`. *Criterio (AC6)*; *Criterio suite*: `uv run pytest tests/test_story_render.py`
  verde. *(depende de 1.2)*

### 3. Comando — `.claude/commands/story.md` (R6/R7/R8)

- [ ] **3.1 Registrar `[tipo]` `encuesta` en PASO 0.** Actualizar la lista dura y el mensaje de
  tipos disponibles para incluir `encuesta` junto a `alerta`, `quote`, `breaking`; ruteo al bloque
  "Ruta `encuesta`". *Criterio (AC8)*: `rg "encuesta" story.md` ≥2.
- [ ] **3.2 Bloque "Ruta `encuesta`" de recolección editorial.** Sin datos de mercado
  (**sentimiento puro**, no llama a `get_asset_levels` ni tools de mercado) y **sin búsqueda de
  evento** (no WebSearch); atajo opcional a `/encuesta` previo (CB-8); layout binario único (R7.4);
  límites `kicker≤30`/`pregunta≤90`/`opcion_a≤25`/`opcion_b≤25`/`nota_cierre≤80` (guía, no
  validación); `kicker`/`nota_cierre` siempre presentes (`""` si no hay); guardado `-Activo
  [TICKER]` o `_general` según decisión editorial (R8); preview específico; reuso preview → render →
  `ruta_story.ps1 -Plantilla "encuesta"` / `--template templates/stories/encuesta.html`.
  *Criterios (AC8/AC9/AC10)*: `rg "encuesta" story.md` ≥2; `rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" story.md`
  ≥1; `rg -i "no llama a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado"
  story.md` ≥1. *(depende de 3.1)*

### 4. Documentación — `CLAUDE.md` (R10)

- [ ] **4.1 Enumerar `encuesta` en la sección "Stories GI".** Cambiar "`[tipo]` soportados hoy:
  `alerta`, `quote`, `breaking`" por "…, `encuesta`", sin tocar el resto; (opcional) refrescar la
  fila `/story` de la tabla de comandos por consistencia. *Criterio (AC11)*: `rg "encuesta"
  CLAUDE.md` ≥1 en la sección.

### 5. No-regresión (AC12)

- [ ] **5.1 Confirmar motor/Alerta/Quote/Breaking/helper intactos.** *Criterio (AC12)*: `git diff
  master -- scripts/story_render.py templates/stories/alerta.html templates/stories/quote.html
  templates/stories/breaking.html scripts/ruta_story.ps1` → vacío.

---

## Referencias

- `spec.md` (#125 — R1-R10, CB-1..CB-8, AC1-AC12, preguntas resueltas, riesgos A/B/C/D).
- `proposal.md` / `idea.md` (#125 — contexto y preguntas originales; candidatos azules
  `#1E3A5F`/`#3E91AF`/`#53C1AB`).
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/design.md` — molde
  estructural directo de este documento; segundo campo opcional replicado con el mismo criterio.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/design.md` — patrón
  fundacional de campo opcional (token + `:empty`).
- `.pulse/changes/archive/119-.../spec.md` — contrato del motor generalizado (no reabierto).
- `scripts/story_render.py:29,55-179` — `_FENCES`, `build_context` (escalares + 4 helpers),
  `_fence_presente`; **no se modifican**.
- `templates/stories/alerta.html:14-58,92-115,145-231,398-409` — andamiaje de marca
  (fuentes/paleta/footer), chip `.chip-categoria` y tarjeta `.tarjeta-precio` (acentos **rojos**
  `#E84040`; **no hay azul** en el archivo) que `encuesta` reutiliza como plantilla estructural en
  **azul**.
- `templates/stories/breaking.html:20-72,84-159,161-213` — molde más cercano (plantilla simple
  sin fences/loops, campo opcional `.breaking-kicker:empty`, tarjeta `.breaking-cifra`, footer).
- `templates/stories/quote.html:127-129` — `.quote-cargo:empty` (segundo precedente `:empty`).
- `tests/test_story_render.py:30,71-81,349-381` — `BREAKING_TEMPLATE`, `PAYLOAD_BREAKING` y los
  tres tests de `breaking` (base de los cuatro tests nuevos de `encuesta`).
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
</content>
