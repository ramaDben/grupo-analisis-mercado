# Design: Stories GI · Fase B — plantilla Edu (concepto educativo) 16:9

> Plan técnico del Change #127. Formaliza cómo se implementan los requisitos de `spec.md`
> (R1-R11, AC1-AC12) de forma **aditiva** sobre el motor de Fase A (`scripts/story_render.py`),
> que NO se toca. Molde estructural directo: `design.md` de #125 (encuesta) y el snapshot
> `templates/stories/encuesta.html` (andamiaje de marca verbatim). Novedad de este Change: es el
> **primer snapshot real que usa el mecanismo `FOR`** (`resolver_loops`), ya implementado y
> testeado en Fase A.

## Resumen

Se agrega la 5ª y última plantilla "Simple" de Fase B: `edu`. Cuatro archivos, todo aditivo:
1. `templates/stories/edu.html` (nuevo snapshot 1920×1080).
2. `.claude/commands/story.md` (PASO 0 + bloque "Ruta `edu`").
3. `tests/test_story_render.py` (tests de mapeo puros + loop bullets 0/1/N).
4. `CLAUDE.md` § "Stories GI" (enumera `edu`).

El motor resuelve el HTML en orden canónico **loops → fences → tokens → guardia** (`build_html`,
`scripts/story_render.py:280-294`). Para `edu`:
- **loops**: `resolver_loops` expande `<!-- FOR:bullets -->…<!-- ENDFOR:bullets -->` una vez por
  objeto de `payload["bullets"]`, resolviendo `{{texto}}` por objeto (`_expandir_elemento`).
- **fences**: `edu` no usa ninguno de los 4 `_FENCES` → no-op.
- **tokens**: `build_context` recorre las claves escalares top-level del payload
  (`kicker`, `titulo_concepto`, `definicion`, `valor_a`, `operador`, `valor_b`) y sustituye sus
  `{{token}}`. `bullets` (list) y `ejemplo` (dict, si viniera) se saltan aquí — por eso el
  comando **aplana** `ejemplo` a las tres claves escalares (D3).
- **guardia**: `_validar_sin_huerfanos` garantiza que no queda ningún `{{token}}` sin resolver.

## Decisiones de diseño

### D1 — Andamiaje de marca reutilizado verbatim
`edu.html` copia el andamiaje de `encuesta.html:13-71,174-232` (los 4 `@font-face` locales
—Syne 800, DM Sans 400/700, Space Grotesk 600—, el `html,body` 1920×1080, `.story` en columna
y el `.footer` con marca + disclaimer CFD). No se cambia ninguna fuente, medida de viewport ni
el footer. Sólo cambian: el gradiente de fondo (acento educativo, D2) y el bloque de cuerpo
`.edu-*` propio.

### D2 — Paleta: fondo oscuro + acento **verde educativo** `#00DC82`  ← DECISIÓN A APROBAR
Fondo base oscuro `#0D0D1A` (idéntico a todas las plantillas). Para diferenciar `edu` de las
piezas previas (alerta = rojo; quote/breaking = rojo/rojizo; encuesta = azul/teal) y darle una
identidad **educativa/de aprendizaje**, el acento propuesto es el **verde de marca `#00DC82`**
(el mismo hex "positivo/alcista" ya commiteado en la paleta GI, `plantillas-stories-gi.md:24-28`),
con teal `#53C1AB` como acento secundario para rótulos. Derivación concreta:
- Gradiente de fondo (mismo patrón que encuesta, con verde en lugar de azul):
  ```css
  background-image:
    radial-gradient(90% 120% at 0% 20%, #123A2A 0%, #0D0D1A 55%),
    linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #123A2A 100%);
  ```
  (`#123A2A` = verde muy oscuro derivado de `#00DC82` sobre la base, análogo al `#1E3A5F` que
  encuesta derivó del azul.)
- Chip `kicker`: `background: rgba(0, 220, 130, 0.14)`, `border: 1px solid rgba(0,220,130,0.5)`,
  `color: #00DC82`.
- Rótulos/acentos estructurales (rótulo del ejemplo, viñetas de bullets): teal `#53C1AB`.
- Textos: blanco `#FFFFFF` (título), `#F5F3F7` (base), `#C9C5D4` (definición/bullets),
  `#A9A5B4` (rótulos secundarios), `#6E6A7A` (disclaimer) — idénticos a encuesta.

**Alternativa** (por si preferís no repetir el verde "alcista"): teal `#53C1AB` como acento
primario, dejando el verde solo para las viñetas. Se decide en la PAUSA.

### D3 — `ejemplo` se aplana a `valor_a`/`operador`/`valor_b` top-level
`build_context` (`story_render.py:141-179`) sólo convierte en token las claves del payload cuyo
valor **no** es `dict` ni `list`. Un `ejemplo` anidado (dict) sería ignorado y sus tokens
`{{valor_a}}`/`{{operador}}`/`{{valor_b}}` quedarían huérfanos → error de guardia. Por eso el
**payload que consume `build_html` lleva las tres claves aplanadas al top-level**:
```json
{ "plantilla": "edu", "kicker": "…", "titulo_concepto": "…", "definicion": "…",
  "valor_a": "Media 50", "operador": "cruza sobre", "valor_b": "Media 200",
  "bullets": [ { "texto": "…" }, … ] }
```
El objeto `ejemplo` es la representación **editorial** en `story.md` (más legible al recolectar);
el comando lo aplana antes de invocar el render. Los tests usan directamente el payload aplanado.

### D4 — `bullets` como array de objetos `[{"texto": "…"}]` + `<li>` dentro del FOR, contenedor fuera
`resolver_loops` (`story_render.py:213-243`) exige que `payload["bullets"]` sea una `list`;
por cada objeto llama `_expandir_elemento`, que resuelve `{{campo}}` desde los **escalares del
objeto**. Por eso cada bullet es `{"texto": "…"}` y el bloque interno referencia `{{texto}}`.
El `<ul>` contenedor y el rótulo estático de la lista van **fuera** de las marcas `FOR`/`ENDFOR`
(regla R4/CB del motor) para no desaparecer con la lista; sólo el `<li>` se repite:
```html
<div class="edu-como">
  <span class="edu-como-rotulo">EN LA PRÁCTICA</span>
  <ul class="edu-bullets">
    <!-- FOR:bullets --><li class="edu-bullet">{{texto}}</li><!-- ENDFOR:bullets -->
  </ul>
</div>
```
Con `bullets == []` → `resolver_loops` reemplaza el bloque (incluidas las marcas) por cadena
vacía → `<ul>` queda vacío y el `<li>` no aparece (AC5). Con N → N `<li>` en orden.

### D5 — `kicker` opcional por CSS `:empty` (no motor)
Igual patrón que `.encuesta-kicker:empty` / `.quote-cargo:empty` / `.breaking-kicker:empty`.
`kicker` es token escalar siempre presente (el comando pasa `""` si no aplica);
`.edu-kicker:empty { display: none; }` colapsa el chip cuando llega vacío. No se toca `_FENCES`.

### D6 — Estructura del cuerpo
Una sola columna editorial centrada (como encuesta), en orden vertical:
`kicker` (chip) → `titulo_concepto` (Syne 800, ~54px) → `definicion` (DM Sans, ~26px, gris claro)
→ bloque `ejemplo` (tarjeta comparativa `valor_a` | `operador` | `valor_b`) → bloque
`EN LA PRÁCTICA` con la lista de bullets → footer estándar.

## Snapshot propuesto — `templates/stories/edu.html`

```html
<!--
Snapshot de marca "Edu" (Stories GI · Fase B, issue #127). Pieza 100% editorial educativa —
kicker + título de concepto + definición + ejemplo comparativo + lista de bullets de aplicación,
sin gráfico ni dato en vivo del motor. Reutiliza verbatim el andamiaje de marca (fuentes/footer)
de `templates/stories/encuesta.html:13-71,174-232`, con dos diferencias: paleta con acento VERDE
educativo (#00DC82) y el bloque `bullets` vía loop <!-- FOR:bullets -->. PRIMER snapshot real que
usa el mecanismo FOR del motor. Campo opcional `kicker` por CSS :empty (no motor). NO cambiar
nombres de tokens sin actualizar scripts/story_render.py y tests/test_story_render.py.
-->
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Edu — Story GI</title>
<style>
  @font-face { font-family: "Syne"; src: url("fonts/syne-800.woff2") format("woff2"); font-weight: 800; font-style: normal; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/dm-sans-400.woff2") format("woff2"); font-weight: 400; font-style: normal; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/dm-sans-700.woff2") format("woff2"); font-weight: 700; font-style: normal; font-display: block; }
  @font-face { font-family: "Space Grotesk"; src: url("fonts/space-grotesk-600.woff2") format("woff2"); font-weight: 600; font-style: normal; font-display: block; }

  * { box-sizing: border-box; }

  html, body {
    margin: 0; padding: 0;
    width: 1920px; height: 1080px;
    background: #0D0D1A;
    background-image:
      radial-gradient(90% 120% at 0% 20%, #123A2A 0%, #0D0D1A 55%),
      linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #123A2A 100%);
    color: #F5F3F7;
    font-family: "DM Sans", sans-serif;
    overflow: hidden;
  }

  .story { width: 1920px; height: 1080px; padding: 56px 72px 40px; display: flex; flex-direction: column; }

  .edu-cuerpo { flex: 1; min-height: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }

  .edu-kicker {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 20px;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 10px 22px; border-radius: 999px;
    background: rgba(0, 220, 130, 0.14); border: 1px solid rgba(0, 220, 130, 0.5); color: #00DC82;
  }
  .edu-kicker:empty { display: none; }

  .edu-titulo { font-family: "Syne", sans-serif; font-weight: 800; font-size: 54px; line-height: 1.15; color: #FFFFFF; margin: 26px 0 0; max-width: 1500px; }

  .edu-definicion { font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 26px; line-height: 1.45; color: #C9C5D4; margin: 22px 0 0; max-width: 1300px; }

  /* ---- Ejemplo comparativo (valor_a  operador  valor_b) ---- */
  .edu-ejemplo { margin-top: 40px; display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 26px; }
  .edu-ejemplo-valor {
    font-family: "Syne", sans-serif; font-weight: 800; font-size: 38px; color: #FFFFFF;
    border: 2px solid #00DC82; background: rgba(0, 220, 130, 0.08); border-radius: 18px; padding: 20px 30px;
  }
  .edu-ejemplo-op { font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 24px; color: #53C1AB; text-transform: uppercase; letter-spacing: 0.04em; }

  /* ---- Bullets "en la práctica" (contenedor y rótulo FUERA del FOR) ---- */
  .edu-como { margin-top: 44px; display: flex; flex-direction: column; align-items: center; gap: 14px; }
  .edu-como-rotulo { font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 16px; letter-spacing: 0.05em; text-transform: uppercase; color: #A9A5B4; }
  .edu-bullets { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; max-width: 1400px; }
  .edu-bullet {
    font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 23px; line-height: 1.4; color: #F5F3F7;
    padding-left: 30px; position: relative; text-align: left;
  }
  .edu-bullet::before { content: "▸"; position: absolute; left: 0; color: #00DC82; }

  /* ---- Footer ---- */
  .footer { margin-top: 28px; display: flex; flex-direction: column; gap: 6px; }
  .footer-marca { display: flex; justify-content: space-between; font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 20px; color: #F5F3F7; }
  .footer-disclaimer { font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 13px; color: #6E6A7A; line-height: 1.35; }
</style>
</head>
<body class="edu">
  <div class="story">

    <div class="edu-cuerpo">
      <span class="edu-kicker">{{kicker}}</span>
      <h1 class="edu-titulo">{{titulo_concepto}}</h1>
      <p class="edu-definicion">{{definicion}}</p>

      <div class="edu-ejemplo">
        <span class="edu-ejemplo-valor">{{valor_a}}</span>
        <span class="edu-ejemplo-op">{{operador}}</span>
        <span class="edu-ejemplo-valor">{{valor_b}}</span>
      </div>

      <div class="edu-como">
        <span class="edu-como-rotulo">EN LA PRÁCTICA</span>
        <ul class="edu-bullets">
          <!-- FOR:bullets --><li class="edu-bullet">{{texto}}</li><!-- ENDFOR:bullets -->
        </ul>
      </div>
    </div>

    <div class="footer">
      <div class="footer-marca">
        <span>@grupointeligencia</span>
        <span>grupointeligencia.com</span>
      </div>
      <p class="footer-disclaimer">
        Los CFD son instrumentos complejos y presentan un riesgo elevado de perder dinero
        rápidamente debido al apalancamiento. Este contenido es educativo/informativo, no
        constituye asesoría financiera.
      </p>
    </div>

  </div>
</body>
</html>
```

## Cambios en `.claude/commands/story.md`

- **PASO 0**: agregar `edu` a la lista dura de `[tipo]` (hoy `alerta`, `quote`, `breaking`,
  `encuesta`) y al mensaje CB-1/CB-7; enrutar a "Ruta `edu`" cuando el tipo confirmado sea `edu`.
- **Nuevo bloque "Ruta `edu`"** (espejo de "Ruta `encuesta`"): recolección editorial
  (título + definición + ejemplo valor_a/operador/valor_b + N bullets + kicker opcional), 100%
  editorial —sin `get_asset_levels` ni WebSearch—, límites de longitud de R9, preview que lista
  los bullets antes de aprobar, y render/guardado bajo `-Activo "_general" -Plantilla "edu"`.
  El payload que se pasa a `story_render.py` lleva `valor_a`/`operador`/`valor_b` **aplanados**
  (D3) y `bullets` como array de objetos `[{"texto": "…"}]` (D4).

## Cambios en `CLAUDE.md`

Sección "Stories GI": actualizar la enumeración de `[tipo]` soportados para incluir `edu`
(cierre de Fase B: `alerta`, `quote`, `breaking`, `encuesta`, `edu`), sin tocar el resto.

## Estrategia de validación (tests)

`tests/test_story_render.py` (patrón `test_quote_*`/`test_breaking_*`/`test_resolver_loops_*`):
- Constante `EDU_TEMPLATE = TEMPLATES_DIR / "edu.html"` y fixture `PAYLOAD_EDU` (payload aplanado
  de D3 con 3 bullets).
- `test_edu_no_placeholders`: `build_html(PAYLOAD_EDU, EDU_TEMPLATE)` contiene kicker,
  titulo_concepto, definicion, valor_a, operador, valor_b y el `texto` de los 3 bullets; sin
  `{{`/`}}` (AC3).
- `test_edu_kicker_vacio`: payload con `kicker=""` → sin placeholders huérfanos (AC4).
- `test_edu_bullets_vacio`: payload con `bullets=[]` → HTML sin `FOR:bullets`/`ENDFOR:bullets`
  ni `{{texto}}` (AC5, caso 0).
- `test_edu_bullets_uno`: `bullets` de 1 → `texto` aparece exactamente 1 vez (AC5, caso 1).
- `test_edu_bullets_n`: `bullets` de 3 → los 3 `texto` aparecen y en orden (AC5, caso N).
- `test_edu_render_dimensiones` (`skipif` sin Chromium): PNG IHDR `(1920,1080)` y > 5 KB (AC6).
Sin fixture nuevo en `tests/fixtures/stories/`; sin tocar `conftest.py`.

## Trazabilidad spec → design

| Spec | Cubierto por |
|------|--------------|
| R1 snapshot | Snapshot propuesto (`edu.html`), D1/D6 |
| R2 payload / R2 bullets objetos | D3 (aplanado `ejemplo`), D4 (`bullets` objetos) |
| R3 FOR sin IF | Bloque `<!-- FOR:bullets -->` único, sin `IF` (D4) |
| R4 colapso FOR vacío | D4 (`<ul>` fuera del FOR) |
| R5 kicker `:empty` | D5 (`.edu-kicker:empty`) |
| R6 ejemplo comparativo | `.edu-ejemplo` (D6), rótulos estáticos |
| R7 recolección | Bloque "Ruta `edu`" en `story.md` |
| R8 guardado `_general` | `ruta_story.ps1 -Activo "_general"` |
| R9 límites longitud | Documentados en "Ruta `edu`" |
| R10 tests | Sección "Estrategia de validación" |
| R11 CLAUDE.md | Sección "Cambios en CLAUDE.md" |
| AC1-AC12 | Snapshot + tests + `git diff` (motor intacto) |

## Riesgos (heredados de spec)

- **B (acento exacto)**: resuelto en este design con `#00DC82` verde (+ alternativa teal); se
  confirma en la PAUSA con el director.
- **A (fidelidad visual sin golden PNG)** y **C/D (longitudes / nº bullets)**: mitigados por la
  aprobación visual en la primera corrida de `/story edu` y por los límites editoriales de R9.

## Referencias

- `templates/stories/encuesta.html:13-71,174-232` — andamiaje de marca reutilizado.
- `scripts/story_render.py:141-179` (`build_context`), `:182-243` (`_expandir_elemento`,
  `resolver_loops`), `:280-294` (`build_html`, orden canónico) — motor, no se toca.
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` fila 07; paleta
  `docs/design/stories-gi/plantillas-stories-gi.md:24-28`.
- `.pulse/changes/127-…/spec.md` (R1-R11, AC1-AC12); `idea.md`, `proposal.md`.
- Precedentes: `.pulse/changes/archive/{121,123,125}-…/design.md`.
