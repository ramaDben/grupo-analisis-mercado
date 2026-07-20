# Design: Stories GI · Fase C — plantilla Flash (cierre multi-activo) 16:9

> Plan técnico del Change #129. Formaliza cómo se implementan los requisitos de `spec.md`
> (R1-R11, AC1-AC12) de forma **aditiva** sobre el motor de Fase A (`scripts/story_render.py`),
> que NO se toca. Molde estructural directo: `design.md` de #127 (edu) y el snapshot
> `templates/stories/edu.html` (andamiaje de marca verbatim + patrón FOR real). Novedad de este
> Change: es la **primera plantilla de Fase C** y el primer FOR que itera **múltiples tokens
> escalares por fila** (edu iteraba un solo `{{texto}}`).

## Technical Approach

Se agrega la 1ª plantilla "con listas" de Fase C: `flash`. Cuatro archivos, todo aditivo:
1. `templates/stories/flash.html` (nuevo snapshot 1920×1080).
2. `.claude/commands/story.md` (PASO 0 + bloque "Ruta `flash`").
3. `tests/test_story_render.py` (tests de mapeo puros + loop `filas` 0/1/N).
4. `CLAUDE.md` § "Stories GI" (enumera `flash`).

El motor resuelve el HTML en orden canónico **loops → fences → tokens → guardia** (`build_html`,
`scripts/story_render.py:280-294`). Para `flash`:
- **loops**: `resolver_loops` expande `<!-- FOR:filas -->…<!-- ENDFOR:filas -->` una vez por objeto
  de `payload["filas"]`, resolviendo `{{nombre}}`/`{{tipo}}`/`{{valor}}`/`{{variacion}}`/
  `{{direccion}}` por objeto (`_expandir_elemento`).
- **fences**: `flash` no usa ninguno de los 4 `_FENCES` → no-op. (El nombre por-fila
  `{{variacion}}` NO colisiona con el fence top-level `variacion`: `_resolver_fences` solo busca
  bloques `<!-- IF:variacion -->`, que `flash.html` no contiene.)
- **tokens**: `build_context` recorre las claves escalares top-level del payload (`kicker`,
  `titulo`, `fecha`) y sustituye sus `{{token}}`. `filas` (list) se salta aquí. Ningún helper de
  derivación se dispara (no hay `sesgo`/`impacto`/`chart_png`/`variacion` top-level).
- **guardia**: `_validar_sin_huerfanos` garantiza que no queda ningún `{{token}}` sin resolver.

### D1 — Andamiaje de marca reutilizado verbatim
`flash.html` copia el andamiaje de `edu.html:16-59,197-220` (los 4 `@font-face` locales —Syne 800,
DM Sans 400/700, Space Grotesk 600—, el `html,body` 1920×1080, `.story` en columna y el `.footer`
con marca + disclaimer CFD). No se cambia ninguna fuente, medida de viewport ni el footer. Sólo
cambian: el gradiente de fondo (acento estructural, D2) y el bloque de cuerpo `.flash-*` propio.

### D2 — Paleta: fondo oscuro + acento estructural **teal `#3E91AF`**  ← DECISIÓN A APROBAR
Fondo base oscuro `#0D0D1A` (idéntico a todas las plantillas). `flash` es un **tablero de cierre**:
sus filas ya llevan **verde `#00DC82` (alcista) y rojo `#E84040` (bajista)** con carga semántica
(R6). Para no diluir ese verde/rojo, el acento **estructural** (chip `kicker`, rótulos de columna,
línea/borde del título) es un **teal institucional `#3E91AF`** (candidato del design doc, tono de
"dashboard de datos", distinto de los ya usados: alerta=rojo, quote/breaking=rojo/rojizo,
encuesta=azul/teal `#1E3A5F`, edu=verde). Derivación concreta:
- Gradiente de fondo (mismo patrón que edu, con teal en lugar de verde):
  ```css
  background-image:
    radial-gradient(90% 120% at 0% 20%, #10222B 0%, #0D0D1A 55%),
    linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #10222B 100%);
  ```
  (`#10222B` = teal muy oscuro derivado de `#3E91AF` sobre la base, análogo al `#123A2A` que edu
  derivó del verde y al `#1E3A5F` de encuesta.)
- Chip `kicker`: `background: rgba(62,145,175,0.14)`, `border: 1px solid rgba(62,145,175,0.5)`,
  `color: #3E91AF`.
- Rótulos de columna del `<thead>` + borde inferior del encabezado: teal `#3E91AF`.
- **Celda de variación** (R6, semántica, NO estructural): verde `#00DC82` ▲ / rojo `#E84040` ▼ /
  gris `#A9A5B4` → (lateral).
- Textos: blanco `#FFFFFF` (título + nombre de activo), `#F5F3F7` (valores), `#C9C5D4` (tipo/fecha),
  `#A9A5B4` (rótulos secundarios), `#6E6A7A` (disclaimer) — idénticos a edu/encuesta.

**Alternativa** (por si preferís un tablero más neutro): acento estructural **grafito/gris azulado
`#5A6472`** dejando el teal fuera, para que verde/rojo dominen aún más. Se decide en la PAUSA.

### D3 — `variacion` por fila aplanada a escalar; `direccion` como slug de clase CSS
`_expandir_elemento` (`story_render.py:182-210`) sólo convierte en token las claves de cada objeto
de la lista cuyo valor **no** es `dict` ni `list`. Un `variacion` anidado (`{pct, direccion}`)
sería ignorado y `{{variacion}}` quedaría huérfano → error de guardia; además los helpers de
flecha/color (`_aplicar_helper_flecha_direccion`, `_aplicar_helper_slug_color`) sólo corren sobre
claves **top-level** del payload, no dentro del FOR. Por eso cada fila lleva:
- `variacion`: escalar con el pct **ya formateado** (signo + `%`, ej. `"+0,42%"`).
- `direccion`: escalar slug (`alcista`/`bajista`/`lateral`), que el snapshot inserta en la **clase
  CSS** de la celda (`class="flash-var flash-var--{{direccion}}"`), no como texto visible.
El comando (R7) aplana `variacion` y deriva `direccion` al recolectar. Mismo patrón exacto de
aplanado que `edu` (#127) con `ejemplo` → `valor_a`/`operador`/`valor_b`. Los tests usan
directamente el payload aplanado.

### D4 — `filas` como array de objetos escalares + `<tr>` dentro del FOR, `<table>`/`<thead>` fuera
`resolver_loops` (`story_render.py:213-243`) exige que `payload["filas"]` sea una `list`; por cada
objeto llama `_expandir_elemento`, que resuelve `{{campo}}` desde los **escalares del objeto**. El
`<table>`, el `<thead>` con los rótulos de columna y el `<tbody>` van **fuera** de las marcas
`FOR`/`ENDFOR` (regla R4/CB del motor) para no desaparecer con las filas; sólo el `<tr>` de datos
se repite:
```html
<table class="flash-tabla">
  <thead>
    <tr>
      <th class="flash-th flash-th--nombre">Activo</th>
      <th class="flash-th">Tipo</th>
      <th class="flash-th flash-th--num">Último</th>
      <th class="flash-th flash-th--num">Var. día</th>
    </tr>
  </thead>
  <tbody>
    <!-- FOR:filas --><tr class="flash-fila"><td class="flash-td flash-nombre">{{nombre}}</td><td class="flash-td flash-tipo">{{tipo}}</td><td class="flash-td flash-valor">{{valor}}</td><td class="flash-td flash-var flash-var--{{direccion}}">{{variacion}}</td></tr><!-- ENDFOR:filas -->
  </tbody>
</table>
```
Con `filas == []` → `resolver_loops` reemplaza el bloque (incluidas las marcas) por cadena vacía →
`<tbody>` queda vacío y ningún `<tr>` de datos aparece; el `<thead>` persiste (AC5). Con N → N
`<tr>` en orden.

> **Nota de implementación**: el bloque interno del FOR se deja en **una sola línea** (sin saltos
> entre `<!-- FOR:filas -->` y `<!-- ENDFOR:filas -->`) para que cada repetición no introduzca
> indentación/espacios espurios entre filas; mismo criterio que el `<li>` en una línea de
> `edu.html:240`.

### D5 — `kicker` opcional por CSS `:empty` (no motor)
Igual patrón que `.edu-kicker:empty` / `.encuesta-kicker:empty` / `.breaking-kicker:empty`.
`kicker` es token escalar siempre presente (el comando pasa `""` si no aplica);
`.flash-kicker:empty { display: none; }` colapsa el chip cuando llega vacío. No se toca `_FENCES`.

### D6 — Color y flecha de variación por CSS (R6)
Tres clases estáticas en el snapshot, seleccionadas por el slug `{{direccion}}` de cada fila:
```css
.flash-var--alcista { color: #00DC82; }
.flash-var--alcista::before { content: "\25B2\00A0"; }   /* ▲ + espacio fijo */
.flash-var--bajista { color: #E84040; }
.flash-var--bajista::before { content: "\25BC\00A0"; }   /* ▼ */
.flash-var--lateral { color: #A9A5B4; }
.flash-var--lateral::before { content: "\2192\00A0"; }   /* → */
```
La flecha se inyecta con `::before` (texto fijo del CSS, no token). Un `direccion` fuera de los tres
no matchea ninguna regla (degradación limpia, CB-5); el comando siempre normaliza (R7.2).

### D7 — Estructura del cuerpo
Una sola columna centrada (como edu), en orden vertical: `kicker` (chip teal) → `titulo` (Syne 800,
~52px) → `fecha` (Space Grotesk, gris) → tabla de activos (rótulos teal + filas con var verde/rojo)
→ footer estándar.

## Snapshot propuesto — `templates/stories/flash.html`

```html
<!--
Snapshot de marca "Flash" (Stories GI · Fase C, issue #129). Cierre multi-activo — kicker + título
+ fecha + tabla de N activos (nombre, tipo, último valor, variación del día con dirección), sin
gráfico ni dato en vivo embebido (los valores los recolecta /story vía get_asset_levels). PRIMERA
plantilla de Fase C (listas). Reutiliza verbatim el andamiaje de marca (fuentes/footer) de
`templates/stories/edu.html`, con dos diferencias: paleta con acento ESTRUCTURAL teal (#3E91AF) y
el bloque `filas` vía el mecanismo loop FOR del motor (el marcador real vive en el `<tbody>` más
abajo; NO escribir el literal del marcador aquí en el comentario, porque `resolver_loops` lo
tomaría como marca de apertura). El verde/rojo de las celdas de variación es SEMÁNTICO (dirección
alcista/bajista), no decorativo. Campo opcional `kicker` por CSS :empty (no
motor). NO cambiar nombres de tokens sin actualizar scripts/story_render.py y
tests/test_story_render.py.
-->
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Flash — Story GI</title>
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
      radial-gradient(90% 120% at 0% 20%, #10222B 0%, #0D0D1A 55%),
      linear-gradient(180deg, #0D0D1A 0%, #0D0D1A 60%, #10222B 100%);
    color: #F5F3F7;
    font-family: "DM Sans", sans-serif;
    overflow: hidden;
  }

  .story { width: 1920px; height: 1080px; padding: 56px 72px 40px; display: flex; flex-direction: column; }

  /* ---- Cuerpo: una sola columna centrada ---- */
  .flash-cuerpo { flex: 1; min-height: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }

  /* ---- Kicker (chip acento teal) ---- */
  .flash-kicker {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 20px;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 10px 22px; border-radius: 999px;
    background: rgba(62, 145, 175, 0.14); border: 1px solid rgba(62, 145, 175, 0.5); color: #3E91AF;
  }
  .flash-kicker:empty { display: none; }

  .flash-titulo { font-family: "Syne", sans-serif; font-weight: 800; font-size: 52px; line-height: 1.15; color: #FFFFFF; margin: 26px 0 0; max-width: 1500px; }

  .flash-fecha { font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 22px; letter-spacing: 0.03em; color: #C9C5D4; margin: 14px 0 0; text-transform: uppercase; }

  /* ---- Tabla de activos (contenedor y encabezado FUERA del FOR) ---- */
  .flash-tabla { margin-top: 46px; width: 1280px; border-collapse: collapse; }

  .flash-th {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 18px;
    letter-spacing: 0.05em; text-transform: uppercase; color: #3E91AF;
    text-align: right; padding: 0 26px 16px; border-bottom: 2px solid rgba(62, 145, 175, 0.5);
  }
  .flash-th--nombre { text-align: left; }

  .flash-fila { border-bottom: 1px solid rgba(245, 243, 247, 0.08); }

  .flash-td { font-size: 30px; padding: 22px 26px; text-align: right; vertical-align: middle; }

  .flash-nombre { font-family: "Syne", sans-serif; font-weight: 800; color: #FFFFFF; text-align: left; }
  .flash-tipo { font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 24px; color: #A9A5B4; text-align: left; }
  .flash-valor { font-family: "Space Grotesk", sans-serif; font-weight: 600; color: #F5F3F7; }

  /* ---- Celda de variación: color + flecha SEMÁNTICOS por dirección (D6/R6) ---- */
  .flash-var { font-family: "Space Grotesk", sans-serif; font-weight: 600; }
  .flash-var--alcista { color: #00DC82; }
  .flash-var--alcista::before { content: "\25B2\00A0"; }
  .flash-var--bajista { color: #E84040; }
  .flash-var--bajista::before { content: "\25BC\00A0"; }
  .flash-var--lateral { color: #A9A5B4; }
  .flash-var--lateral::before { content: "\2192\00A0"; }

  /* ---- Footer ---- */
  .footer { margin-top: 28px; display: flex; flex-direction: column; gap: 6px; }
  .footer-marca { display: flex; justify-content: space-between; font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 20px; color: #F5F3F7; }
  .footer-disclaimer { font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 13px; color: #6E6A7A; line-height: 1.35; }
</style>
</head>
<body class="flash">
  <div class="story">

    <div class="flash-cuerpo">
      <span class="flash-kicker">{{kicker}}</span>
      <h1 class="flash-titulo">{{titulo}}</h1>
      <p class="flash-fecha">{{fecha}}</p>

      <table class="flash-tabla">
        <thead>
          <tr>
            <th class="flash-th flash-th--nombre">Activo</th>
            <th class="flash-th">Tipo</th>
            <th class="flash-th">Último</th>
            <th class="flash-th">Var. día</th>
          </tr>
        </thead>
        <tbody>
          <!-- FOR:filas --><tr class="flash-fila"><td class="flash-td flash-nombre">{{nombre}}</td><td class="flash-td flash-tipo">{{tipo}}</td><td class="flash-td flash-valor">{{valor}}</td><td class="flash-td flash-var flash-var--{{direccion}}">{{variacion}}</td></tr><!-- ENDFOR:filas -->
        </tbody>
      </table>
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

- **PASO 0**: agregar `flash` a la lista dura de `[tipo]` (hoy `alerta`, `quote`, `breaking`,
  `encuesta`, `edu`) y al mensaje CB-9/CB-1; enrutar a "Ruta `flash`" cuando el tipo confirmado sea
  `flash`.
- **Nuevo bloque "Ruta `flash`"** (espejo de "Ruta `edu`" con recolección de datos del motor):
  recolección de la lista de activos + `titulo` + `kicker` opcional; por cada activo,
  `get_asset_levels` para último valor + variación del día (fallback manual patrón `apertura.md`
  PASO 4A), formateo de `valor` por `digits` de `config/activos.json`, derivación de `direccion`;
  `fecha` desde el reloj de Chile; preview que lista las filas antes de aprobar; render/guardado
  bajo `-Activo "_general" -Plantilla "flash"`. El payload que se pasa a `story_render.py` lleva
  `filas` como array de objetos escalares aplanados (D3) con `variacion` ya formateada y
  `direccion` slug (D3/D6).

## Cambios en `CLAUDE.md`

Sección "Stories GI": actualizar la enumeración de `[tipo]` soportados para incluir `flash`
(arranque de Fase C: `alerta`, `quote`, `breaking`, `encuesta`, `edu`, `flash`), sin tocar el resto.

## Validation Strategy

`tests/test_story_render.py` (patrón `test_edu_*`/`test_resolver_loops_*`):
- Constante `FLASH_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "flash.html"` y fixture
  `PAYLOAD_FLASH` (payload de R2 con 3 filas aplanadas: alcista/bajista/lateral).
- `test_flash_no_placeholders`: `build_html(PAYLOAD_FLASH, FLASH_TEMPLATE)` contiene `kicker`,
  `titulo`, `fecha` y, por fila, `nombre`/`tipo`/`valor`/`variacion` + la clase
  `flash-var--<direccion>`; sin `{{`/`}}` (AC3).
- `test_flash_kicker_vacio`: payload con `kicker=""` → sin placeholders huérfanos (AC4).
- `test_flash_filas_vacio`: payload con `filas=[]` → HTML sin `FOR:filas`/`ENDFOR:filas` ni
  `{{nombre}}` (AC5, caso 0); el `<thead>`/rótulo "Activo" persiste.
- `test_flash_filas_uno`: `filas` de 1 → el `nombre` aparece exactamente 1 vez (AC5, caso 1).
- `test_flash_filas_n`: `filas` de 3 → los 3 `nombre` aparecen y en orden (AC5, caso N).
- `test_flash_render_dimensiones` (`skipif` sin Chromium): PNG IHDR `(1920,1080)` y > 5 KB (AC6).
Sin fixture nuevo en `tests/fixtures/stories/`; sin tocar `conftest.py`.

## Trazabilidad spec → design

| Spec | Cubierto por |
|------|--------------|
| R1 snapshot | Snapshot propuesto (`flash.html`), D1/D7 |
| R2 payload / filas objetos escalares | D3 (aplanado `variacion`/`direccion`), D4 (`filas` objetos) |
| R3 FOR sin IF | Bloque `<!-- FOR:filas -->` único, sin `IF` (D4) |
| R4 colapso FOR vacío | D4 (`<table>`/`<thead>` fuera del FOR) |
| R5 kicker `:empty` | D5 (`.flash-kicker:empty`) |
| R6 color/flecha por dirección | D6 (`.flash-var--*` + `::before`) |
| R7 recolección con motor | Bloque "Ruta `flash`" en `story.md` |
| R8 guardado `_general` | `ruta_story.ps1 -Activo "_general"` |
| R9 límites longitud | Documentados en "Ruta `flash`" |
| R10 tests | Sección "Validation Strategy" |
| R11 CLAUDE.md | Sección "Cambios en CLAUDE.md" |
| AC1-AC12 | Snapshot + tests + `git diff` (motor intacto) |

## Riesgos (heredados de spec)

- **B (acento exacto)**: resuelto en este design con teal `#3E91AF` estructural (+ alternativa
  grafito); verde/rojo reservados a la semántica de fila; se confirma en la PAUSA con el director.
- **A (fidelidad visual sin golden PNG)** y **C/D (longitudes / nº filas)**: mitigados por la
  aprobación visual en la primera corrida de `/story flash` y por los límites editoriales de R9.

## Referencias

- `templates/stories/edu.html:16-59,197-220` — andamiaje de marca reutilizado + patrón FOR real.
- `scripts/story_render.py:141-179` (`build_context`), `:182-243` (`_expandir_elemento`,
  `resolver_loops`), `:280-294` (`build_html`, orden canónico) — motor, no se toca.
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` fila 05; plan de fases
  (líneas 91-93).
- `.pulse/changes/129-…/spec.md` (R1-R11, AC1-AC12); `idea.md`, `proposal.md`.
- Precedentes: `.pulse/changes/archive/{119,121,123,125,127}-…/design.md`.
- `.claude/commands/apertura.md`, `.claude/commands/actualizacion.md` — criterio de recolección
  `get_asset_levels` + fallback manual.
