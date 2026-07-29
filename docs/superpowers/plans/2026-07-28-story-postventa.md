# Plantilla de Story "Post-Venta" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear `templates/stories/postventa.html`, el snapshot de marca propio del parte de post-venta — footer interno, rojo/verde semántico en los niveles y dos listas independientes — y exponerlo como tipo `postventa` de `/story`.

**Architecture:** Snapshot HTML estático que el motor `scripts/story_render.py` mapea desde un payload JSON. **El motor no se modifica**: ya soporta varios `<!-- FOR -->` por archivo y ya deriva `sesgo_slug` desde la clave `sesgo` (verificado contra el motor real antes de escribir este plan). El andamiaje de marca (fuentes, fondo, reset) se hereda verbatim de `templates/stories/edu.html`; lo nuevo es el CSS del cuerpo y el footer interno.

**Tech Stack:** HTML/CSS estático + Playwright headless vía `scripts/story_render.py`. Tests con pytest en `tests/test_story_render.py` (patrón ya establecido por las 6 plantillas existentes). Design de referencia: `docs/design/stories-gi/2026-07-28-plantilla-postventa-design.md`. Rama: `feat/story-postventa`, salida de `master`.

## Global Constraints

Valores copiados literalmente del design doc:

- **Chip `🔒 INTERNO · POST-VENTA` literal en el HTML**, nunca como token. Ningún payload puede suprimirlo.
- **Footer sin marca pública**: prohibido `@grupointeligencia`, `grupointeligencia.com` y el disclaimer de CFD.
- **Color semántico, nunca decorativo**: soporte `#00DC82`, resistencia `#E84040`, sesgo según `--alcista`/`--bajista`/`--lateral`. Flechas ▲▼→ por CSS `::before`, no por texto del payload.
- **Acento estructural** teal `#3E91AF` (chip y rótulos).
- **Paleta heredada**: fondo `#0D0D1A`, texto `#F5F3F7`, secundario `#A9A5B4`, apagado `#6E6A7A`.
- **Fuentes heredadas**: Syne 800, DM Sans 400/700, Space Grotesk 600 (mismos `@font-face` y rutas `fonts/` que el resto de los snapshots).
- **Rótulos de columna fuera de las marcas FOR**, para que persistan con lista vacía.
- **Dimensiones**: 1920×1080 exactos.
- **Precios** con los `digits` de `config/activos.json`.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `templates/stories/postventa.html` | Snapshot de marca del parte de post-venta | Crear |
| `tests/test_story_render.py` | Tests del mapeo y del render de la plantilla nueva | Modificar (agregar bloque `postventa`) |
| `.claude/commands/story.md` | Ruta de recolección del tipo `postventa` | Modificar |
| `.claude/commands/postventa.md` | Ofrecimiento de encadenar la Story tras guardar el parte | Modificar (PASO 8) |
| `CLAUDE.md` | `postventa` entre los tipos de `/story` (sección "Stories GI" y tabla de comandos) | Modificar |

No se toca `scripts/story_render.py` ni ningún otro snapshot.

---

## Task 1: Snapshot y tests

**Files:**
- Create: `templates/stories/postventa.html`
- Modify: `tests/test_story_render.py`

**Interfaces:**
- Consumes: `story_render.build_html(payload, template_path)` y `story_render.render_story(...)`, ya existentes.
- Produces: el snapshot con estos tokens escalares — `fecha_hora`, `consulta`, `respuesta`, `activo_nombre`, `soporte`, `precio`, `resistencia`, `sesgo`, `sesgo_slug` (derivado por el motor), `fuente` — y dos loops, `respuestas` y `no_promesas`, cada uno con la clave `texto` por elemento.

- [ ] **Step 1: Escribir los tests (fallan: el snapshot aún no existe)**

Agregar al final de `tests/test_story_render.py`. La constante `POSTVENTA_TEMPLATE` va junto a las otras constantes de template del encabezado del archivo (`_REPO_ROOT / "templates" / "stories" / "postventa.html"`).

```python
# ---------------------------------------------------------------------------
# snapshot templates/stories/postventa.html — pieza INTERNA: chip no
# suprimible, color semántico en niveles y DOS loops independientes.
# ---------------------------------------------------------------------------

PAYLOAD_POSTVENTA = {
    "plantilla": "postventa",
    "fecha_hora": "28 JUL 2026 · 19:23",
    "consulta": "¿Me afecta que no bajen la tasa?",
    "respuesta": "No, ya estaba en el precio. Mañana manda la Fed.",
    "activo_nombre": "USD/CLP",
    "soporte": "$923.90",
    "precio": "$930.50",
    "resistencia": "$930.80",
    "sesgo": "Bajista",
    "respuestas": [
        {"texto": "¿Cierro? → Depende del plazo, no del dato de hoy"},
        {"texto": "¿Por qué no bajan? → Inflación 4,3% contra la meta de 3%"},
        {"texto": "Con la posición en contra: explica el nivel"},
    ],
    "no_promesas": [
        {"texto": "Que el dólar siga bajando: mañana define la Fed"},
        {"texto": "Que el Banco Central baje pronto"},
    ],
    "fuente": "MT5 · GRUPO INTELIGENCIA",
}


def test_postventa_no_placeholders():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    assert PAYLOAD_POSTVENTA["consulta"] in html
    assert PAYLOAD_POSTVENTA["respuesta"] in html
    assert PAYLOAD_POSTVENTA["soporte"] in html
    assert PAYLOAD_POSTVENTA["precio"] in html
    assert PAYLOAD_POSTVENTA["resistencia"] in html
    for item in PAYLOAD_POSTVENTA["respuestas"]:
        assert item["texto"] in html
    for item in PAYLOAD_POSTVENTA["no_promesas"]:
        assert item["texto"] in html
    assert "{{" not in html
    assert "}}" not in html


def test_postventa_chip_interno_no_suprimible():
    """El chip de INTERNO es literal del snapshot: ningún payload lo quita.

    Los asserts comparan contra el texto tal como está escrito en el HTML
    fuente ("Interno · Post-venta"). Las mayúsculas que se ven en el PNG las
    aplica el CSS con `text-transform: uppercase`, que no altera el HTML.
    """
    payload = {**PAYLOAD_POSTVENTA, "kicker": "", "chip": ""}

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert "Interno" in html
    assert "Post-venta" in html


def test_postventa_footer_sin_marca_publica():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    assert "@grupointeligencia" not in html
    assert "grupointeligencia.com" not in html
    assert "apalancamiento" not in html
    assert "No reenviar" in html


def test_postventa_sesgo_slug_bajista():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    assert "pv-sesgo--bajista" in html
    assert "pv-sesgo--alcista" not in html


def test_postventa_sesgo_slug_alcista():
    payload = {**PAYLOAD_POSTVENTA, "sesgo": "Alcista"}

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert "pv-sesgo--alcista" in html
    assert "pv-sesgo--bajista" not in html


def test_postventa_sesgo_slug_lateral():
    payload = {**PAYLOAD_POSTVENTA, "sesgo": "Lateral"}

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert "pv-sesgo--lateral" in html


def test_postventa_listas_vacias_conservan_rotulos():
    payload = {**PAYLOAD_POSTVENTA, "respuestas": [], "no_promesas": []}

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert "FOR:respuestas" not in html
    assert "ENDFOR:respuestas" not in html
    assert "FOR:no_promesas" not in html
    assert "ENDFOR:no_promesas" not in html
    # Texto tal como está en el HTML: el uppercase lo aplica el CSS.
    assert "Qué responder" in html
    assert "Qué NO prometer" in html
    assert "{{texto}}" not in html
    assert "{{" not in html


def test_postventa_listas_independientes():
    """Una lista con N y la otra con 1 no se contaminan entre sí."""
    payload = {
        **PAYLOAD_POSTVENTA,
        "no_promesas": [{"texto": "Único límite del día"}],
    }

    html = story_render.build_html(payload, POSTVENTA_TEMPLATE)

    assert html.count("Único límite del día") == 1
    for item in PAYLOAD_POSTVENTA["respuestas"]:
        assert html.count(item["texto"]) == 1
    assert "{{texto}}" not in html


def test_postventa_orden_de_respuestas():
    html = story_render.build_html(PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE)

    textos = [item["texto"] for item in PAYLOAD_POSTVENTA["respuestas"]]
    assert html.index(textos[0]) < html.index(textos[1]) < html.index(textos[2])


@pytest.mark.skipif(
    not _chromium_disponible(), reason="Chromium de Playwright no instalado"
)
def test_postventa_render_dimensiones(tmp_path):
    salida = tmp_path / "story_postventa_test.png"

    resultado = story_render.render_story(
        PAYLOAD_POSTVENTA, POSTVENTA_TEMPLATE, salida
    )

    assert resultado == salida
    assert salida.exists()
    assert salida.stat().st_size > 5 * 1024
    assert _png_size(salida) == (1920, 1080)
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `uv run --frozen pytest tests/test_story_render.py -k postventa -q`
Expected: FAIL — `FileNotFoundError` en `templates/stories/postventa.html` (el snapshot todavía no existe).

Usar siempre `--frozen`: `uv.lock` tiene cambios del director que no deben tocarse.

- [ ] **Step 3: Crear `templates/stories/postventa.html`**

**Andamiaje heredado verbatim de `templates/stories/edu.html`**: el comentario de cabecera adaptado, `<!DOCTYPE html>`, `<html lang="es">`, los cuatro bloques `@font-face` (Syne 800, DM Sans 400, DM Sans 700, Space Grotesk 600 con las mismas rutas `fonts/*.woff2`), el reset `* { box-sizing: border-box; }` y el bloque `html, body` con `width/height: 1920px/1080px`, `background: #0D0D1A`, `color: #F5F3F7`, `font-family: "DM Sans", sans-serif`, `overflow: hidden`. Copiar esos bloques sin cambios — son el contrato de marca compartido.

**CSS propio de esta plantilla** (agregar tras el bloque `html, body`):

```css
  .story {
    width: 1920px; height: 1080px;
    padding: 52px 80px 36px;
    display: flex; flex-direction: column;
  }

  /* ---- Encabezado ---- */
  .pv-head { display: flex; align-items: center; justify-content: space-between; }

  .pv-chip {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 19px;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 9px 22px; border-radius: 999px;
    background: rgba(62, 145, 175, 0.14);
    border: 1px solid rgba(62, 145, 175, 0.5);
    color: #3E91AF;
  }

  .pv-fecha {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 20px;
    letter-spacing: 0.03em; text-transform: uppercase; color: #A9A5B4;
  }

  /* ---- Consulta ---- */
  .pv-rotulo {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 18px;
    letter-spacing: 0.07em; text-transform: uppercase; color: #3E91AF;
    margin: 40px 0 14px;
  }

  .pv-consulta {
    font-family: "Syne", sans-serif; font-weight: 800; font-size: 52px;
    line-height: 1.12; color: #FFFFFF; margin: 0; max-width: 1560px;
  }

  .pv-respuesta {
    font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 28px;
    line-height: 1.4; color: #C9C5D4; margin: 18px 0 0; max-width: 1560px;
  }

  /* ---- Franja de niveles: color SEMANTICO ---- */
  .pv-niveles {
    margin: 38px 0 0; padding: 24px 0;
    border-top: 1px solid rgba(245, 243, 247, 0.10);
    border-bottom: 1px solid rgba(245, 243, 247, 0.10);
    display: grid; grid-template-columns: 1fr 1fr 1fr; align-items: center;
  }

  .pv-nivel-rotulo {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 15px;
    letter-spacing: 0.08em; text-transform: uppercase; color: #A9A5B4;
    margin-bottom: 6px;
  }

  .pv-nivel-valor {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 40px;
  }

  .pv-nivel--soporte .pv-nivel-valor { color: #00DC82; }
  .pv-nivel--resistencia { text-align: right; }
  .pv-nivel--resistencia .pv-nivel-valor { color: #E84040; }
  .pv-nivel--centro { text-align: center; }
  .pv-nivel--centro .pv-nivel-valor { color: #F5F3F7; }

  .pv-sesgo {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 21px;
    margin-top: 4px;
  }
  .pv-sesgo--alcista { color: #00DC82; }
  .pv-sesgo--alcista::before { content: "\25B2\00A0"; }
  .pv-sesgo--bajista { color: #E84040; }
  .pv-sesgo--bajista::before { content: "\25BC\00A0"; }
  .pv-sesgo--lateral { color: #A9A5B4; }
  .pv-sesgo--lateral::before { content: "\2192\00A0"; }

  /* ---- Dos columnas ---- */
  .pv-cuerpo {
    flex: 1; min-height: 0; margin-top: 34px;
    display: grid; grid-template-columns: 1fr 1fr; gap: 72px;
  }

  .pv-col-titulo {
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 18px;
    letter-spacing: 0.07em; text-transform: uppercase;
    padding-bottom: 12px; margin-bottom: 8px;
  }
  .pv-col--responder .pv-col-titulo {
    color: #00DC82; border-bottom: 2px solid rgba(0, 220, 130, 0.45);
  }
  .pv-col--prometer .pv-col-titulo {
    color: #E84040; border-bottom: 2px solid rgba(232, 64, 64, 0.45);
  }

  .pv-item {
    font-family: "DM Sans", sans-serif; font-weight: 400; font-size: 23px;
    line-height: 1.35; color: #F5F3F7;
    padding: 15px 0 15px 26px; position: relative;
  }
  .pv-item::before {
    content: "\25B8"; position: absolute; left: 0; color: #3E91AF;
  }

  /* ---- Footer interno ---- */
  .pv-footer {
    margin-top: 20px; display: flex; justify-content: space-between;
    font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 15px;
    letter-spacing: 0.05em; text-transform: uppercase; color: #6E6A7A;
  }
```

**Body** (íntegro — los marcadores `FOR`/`ENDFOR` van en una sola línea con su contenido, igual que en `edu.html` y `flash.html`):

```html
<body class="postventa">
  <div class="story">

    <div class="pv-head">
      <span class="pv-chip">🔒 Interno · Post-venta</span>
      <span class="pv-fecha">{{fecha_hora}}</span>
    </div>

    <div class="pv-rotulo">La consulta de hoy</div>
    <h1 class="pv-consulta">{{consulta}}</h1>
    <p class="pv-respuesta">{{respuesta}}</p>

    <div class="pv-niveles">
      <div class="pv-nivel pv-nivel--soporte">
        <div class="pv-nivel-rotulo">Soporte</div>
        <div class="pv-nivel-valor">{{soporte}}</div>
      </div>
      <div class="pv-nivel pv-nivel--centro">
        <div class="pv-nivel-rotulo">{{activo_nombre}}</div>
        <div class="pv-nivel-valor">{{precio}}</div>
        <div class="pv-sesgo pv-sesgo--{{sesgo_slug}}">{{sesgo}}</div>
      </div>
      <div class="pv-nivel pv-nivel--resistencia">
        <div class="pv-nivel-rotulo">Resistencia</div>
        <div class="pv-nivel-valor">{{resistencia}}</div>
      </div>
    </div>

    <div class="pv-cuerpo">
      <div class="pv-col pv-col--responder">
        <div class="pv-col-titulo">✅ Qué responder</div>
        <!-- FOR:respuestas --><div class="pv-item">{{texto}}</div><!-- ENDFOR:respuestas -->
      </div>
      <div class="pv-col pv-col--prometer">
        <div class="pv-col-titulo">⚠️ Qué NO prometer</div>
        <!-- FOR:no_promesas --><div class="pv-item">{{texto}}</div><!-- ENDFOR:no_promesas -->
      </div>
    </div>

    <div class="pv-footer">
      <span>Uso interno · No reenviar al cliente</span>
      <span>Fuente: {{fuente}}</span>
    </div>

  </div>
</body>
</html>
```

Cerrar el `<style>` y el `<head>` antes del `<body>`, igual que los otros snapshots.

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `uv run --frozen pytest tests/test_story_render.py -k postventa -q`
Expected: PASS — 10 tests (9 de mapeo + 1 de render, este último se salta si no hay Chromium).

- [ ] **Step 5: Correr la suite completa**

Run: `uv run --frozen pytest -q`
Expected: los 101 tests previos siguen en verde, más los nuevos.

- [ ] **Step 6: Commit**

```bash
git add templates/stories/postventa.html tests/test_story_render.py
git commit -m "feat(stories): snapshot postventa con footer interno y color semantico"
```

---

## Task 2: Tipo `postventa` en `/story`

**Files:**
- Modify: `.claude/commands/story.md`

**Interfaces:**
- Consumes: el snapshot y su contrato de datos (Task 1).
- Produces: el tipo `postventa` invocable como `/story postventa`.

- [ ] **Step 1: Agregar `postventa` a la lista de tipos válidos**

En `.claude/commands/story.md`, el PASO 0 valida el tipo contra la lista `alerta`, `quote`, `breaking`, `encuesta`, `edu`, `flash`. Agregar `postventa` a esa enumeración en los tres lugares donde aparece: el bloque de argumentos del encabezado, el mensaje de error CB-1 y la instrucción de salto a la ruta correspondiente.

- [ ] **Step 2: Agregar la ruta de recolección**

Insertar tras el bloque "Ruta `flash`" y antes del PASO 1:

```markdown
---

## Ruta `postventa` — parte interno (atajo desde `/postventa`)

`postventa` es la Story del parte de post-venta: pieza **interna**, con chip no suprimible y
footer sin marca pública. Reemplaza los PASO 1-4 de `alerta`; el preview/render final reusa el
patrón de PASO 6-7 adaptado.

1. **Atajo opcional**: abrir preguntando
   ```
   ¿Ya corriste /postventa hoy? Si sí, reuso la consulta, los niveles y los puntos
   de ese parte. Si no, dime el activo y los recolecto del motor.
   ```
   - **Con parte previo** → reusar consulta, respuesta, niveles y puntos ya redactados. **No**
     volver a llamar a `get_asset_levels`.
   - **En frío** → pedir el activo (normalizado contra `config/activos.json`, mismo criterio que
     `/chart` PASO 1) y llamar `mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]",
     "timeframe": "H1"})`, tomando precio y el soporte/resistencia más próximos. Si retorna
     `{"error": ...}`, pedirlos manualmente (patrón `apertura.md` PASO 4A).

   El atajo no bloquea ni exige corrida previa.

2. **Límites editoriales** (guía de redacción — el motor no valida longitud ni trunca):
   `fecha_hora` ≤ 28 · `consulta` ≤ 60 · `respuesta` ≤ 90 · `activo_nombre` ≤ 14 ·
   `soporte`/`precio`/`resistencia` ≤ 12 cada uno · `sesgo` ≤ 10 · cada `respuestas[].texto` ≤ 62
   (4 a 6 entradas) · cada `no_promesas[].texto` ≤ 62 (2 a 3 entradas) · `fuente` ≤ 30.

3. **Payload `story_postventa`**: `sesgo` es una de `Alcista` / `Bajista` / `Lateral` — el motor
   deriva de ahí `sesgo_slug` para la clase de color. Precios con los `digits` de
   `config/activos.json`.
   ```json
   {
     "plantilla": "postventa",
     "fecha_hora": "[D MES YYYY · HH:MM]",
     "consulta": "[consulta ≤60 car.]",
     "respuesta": "[respuesta ≤90 car.]",
     "activo_nombre": "[nombre corto ≤14 car.]",
     "soporte": "[precio con digits]",
     "precio": "[precio con digits]",
     "resistencia": "[precio con digits]",
     "sesgo": "Alcista|Bajista|Lateral",
     "respuestas": [ { "texto": "[≤62 car.]" } ],
     "no_promesas": [ { "texto": "[≤62 car.]" } ],
     "fuente": "MT5 · GRUPO INTELIGENCIA"
   }
   ```

4. **Preview y aprobación** (ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Post-Venta (INTERNA)*
   ━━━━━━━━━━━━━━━━━━━
   Consulta: [consulta]
   Respuesta: [respuesta]
   Niveles: S [soporte] · [activo_nombre] [precio] ([sesgo]) · R [resistencia]
   Qué responder: [n] puntos
   Qué NO prometer: [n] puntos
   ━━━━━━━━━━━━━━━━━━━
   ⚠️ Pieza interna: el chip y el footer la marcan como no reenviable.
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada. Terminar el comando ahí.

5. **Render y guardado** (solo tras aprobar). Lleva activo protagonista, a diferencia de `edu`:
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5]" -Plantilla "postventa" -Hora "[HH-mm]"
   ```
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/postventa.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_postventa del paso 3... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.
```

- [ ] **Step 3: Verificar**

Run:
```bash
grep -c 'postventa' .claude/commands/story.md
```
Expected: al menos `8` (tres de la lista de tipos, el encabezado de la ruta y los del payload/render).

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/story.md
git commit -m "feat(stories): tipo postventa en /story con atajo desde el parte"
```

---

## Task 3: Puente desde `/postventa` y documentación

**Files:**
- Modify: `.claude/commands/postventa.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: el tipo `postventa` de `/story` (Task 2).
- Produces: nada que otra tarea consuma.

- [ ] **Step 1: Ofrecer la Story al final de `/postventa`**

En `.claude/commands/postventa.md`, tras el bloque del PASO 8 (Guardado), agregar:

```markdown
## PASO 9 — Story de marca (opcional)

Tras guardar el parte, ofrecer la versión imagen:
```
🖼️ ¿Genero también la Story de marca del parte? (pieza interna 1920×1080)
```
Si acepta, ejecutar el flujo de `/story postventa` reusando lo que ya está en memoria — la
consulta y su respuesta, los niveles del activo protagonista y los puntos de los bloques 2 y 7.
**No** volver a llamar a `get_asset_levels`.

Si responde que no, terminar sin generar imagen.
```

- [ ] **Step 2: Actualizar el conteo de PASOS en la verificación heredada**

El plan del comando `/postventa` documentaba 8 pasos. Con el PASO 9 la verificación cambia.

Run:
```bash
grep -c '^## PASO' .claude/commands/postventa.md
```
Expected: `9`

- [ ] **Step 3: Agregar `postventa` a los tipos de `/story` en `CLAUDE.md`**

Dos lugares mencionan los tipos soportados de `/story`:

1. La sección **"Stories GI"**, donde dice que los tipos soportados hoy son `alerta`, `quote`, `breaking`, `encuesta`, `edu` y `flash`. Agregar `postventa` con una frase: pieza **interna** para el equipo de post-venta (chip no suprimible, footer sin marca pública, color semántico en niveles y dos listas), que consume los datos del parte de `/postventa`.
2. La fila de `/story [tipo]` en la tabla de comandos de Capa 2, que enumera los mismos tipos.

- [ ] **Step 4: Verificar coherencia**

Run:
```bash
grep -c 'postventa' CLAUDE.md
```
Expected: al menos `6` (los 4 del comando `/postventa` ya existentes más los 2 nuevos de `/story`).

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/postventa.md CLAUDE.md
git commit -m "docs(stories): encadena la Story de post-venta y documenta el tipo"
```

---

## Task 4: Render real y validación visual

**Files:**
- Test (manual): render con los datos reales de la jornada
- Modify (si el render lo exige): `templates/stories/postventa.html`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: el PNG validado y, si hubo ajustes, las correcciones al snapshot.

- [ ] **Step 1: Renderizar con datos reales**

Escribir el payload en el scratchpad de la sesión (nunca en el repo) y renderizar a una ruta construida con `ruta_story.ps1`. Usar los datos de la jornada real del parte ya generado.

- [ ] **Step 2: Inspeccionar el PNG y verificar los criterios visuales**

Abrir el PNG y confirmar, uno por uno:

1. El chip `🔒 INTERNO · POST-VENTA` se ve arriba a la izquierda.
2. El soporte se ve **verde** y la resistencia **roja**, en el mismo render.
3. El sesgo muestra la flecha correcta y su color (▼ rojo para `Bajista`).
4. Las dos columnas muestran sus rótulos y sus puntos, sin desbordarse ni solaparse.
5. El footer dice `Uso interno · No reenviar al cliente` y **no** aparece ni `@grupointeligencia` ni el disclaimer de CFD.
6. Ningún texto se sale del lienzo ni queda cortado.

- [ ] **Step 3: Corregir lo que la inspección revele**

Ajustar tamaños de fuente, `padding` o `gap` del CSS si algún texto desborda. Repetir el Step 1 hasta que los seis puntos pasen.

- [ ] **Step 4: Correr la suite completa**

Run: `uv run --frozen pytest -q`
Expected: todo en verde.

- [ ] **Step 5: Commit (si hubo ajustes) y PR**

```bash
git add templates/stories/postventa.html
git commit -m "fix(stories): ajustes visuales del snapshot postventa"
git push -u origin feat/story-postventa
gh pr create --base master --title "feat(stories): plantilla de Story para post-venta" --body "Implementa la plantilla segun docs/design/stories-gi/2026-07-28-plantilla-postventa-design.md"
```

---

## Notas de ejecución

- **Rama**: `feat/story-postventa`, ya creada desde `master` con el design doc commiteado.
- **`--frozen` siempre**: `uv.lock` tiene cambios del director. Correr `uv run --frozen pytest`, nunca `uv sync` a secas.
- **Working tree**: `data/historial_encuestas.json` y `uv.lock` están modificados y **no pertenecen a este trabajo**. Los `git add` son explícitos por archivo para que no se cuelen.
- **El motor no se toca**: si algún paso parece exigir cambios en `scripts/story_render.py`, detenerse y revisar — el design verificó que no hacen falta.
