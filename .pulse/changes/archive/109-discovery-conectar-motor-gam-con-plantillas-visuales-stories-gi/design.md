# Design — Comando `/story alerta`: render de Stories GI (#109)

> Diseño técnico de `spec.md` (**versión enmendada 2026-07-13** — piloto "03 Alerta de Mercado",
> ver nota de enmienda en `spec.md` y comentario en issue #109). Implementa exactamente R1-R10,
> RNF1-RNF5, CB-1..CB-8 y AC1-AC9. Decide: mecanismo de inyección de campos, estructura interna
> de `scripts/story_render.py`, invocación desde `.claude/commands/story.md`, y plan de testing.
> **No** contiene código de aplicación.

## Nota sobre invariantes de arquitectura

Este Change no toca ninguna capa hexagonal: el MCP `src/market_data_mcp/` no se modifica (RNF1).
El código nuevo es un utilitario de nivel `scripts/` (`story_render.py`) + helper PowerShell
(`ruta_story.ps1`) + un prompt de comando (`story.md`). El módulo de render **no contiene lógica
de negocio**: la recolección (niveles vía `get_asset_levels`, narrativa con criterio `/alerta`,
formateo `digits`) vive en el prompt del comando; el script solo mapea payload→HTML→PNG.

---

## 1. Enfoque de la solución

### 1.1 Vista de conjunto — flujo de datos

```
/story alerta  (.claude/commands/story.md — prompt, sin lógica Python)
   │
   │ R1  valida [tipo] == "alerta" (único soportado); rechaza otro / vacío (CB-1)
   │ R7  flag `ejecutivo`: avisa que no aplica y continúa (CB-6)
   │
   ├─ R2  Recolección HÍBRIDA (1 activo):
   │        a) activo + temporalidad del gráfico (etiquetas canónicas)
   │        b) precio + soporte + resistencia más próximos ← get_asset_levels
   │           (fallback manual CB-2, patrón apertura PASO 4A)
   │        c) narrativa: ¿evento real reciente? (criterio /alerta PASO 1, WebSearch)
   │           SÍ → titular/párrafo noticioso · NO → lectura técnica (CB-5)
   │        d) variación % / vol % del motor si existen; si no, se omiten (CB-4)
   │        e) ¿embeber chart de /chart? (opcional: ruta PNG de data/charts/)
   │
   ├─ R3  Payload `story_alerta` (JSON): precios por `digits` con coma decimal,
   │        tag_riesgo por contexto, fecha_hora reloj de Chile
   │
   ├─ R5  Preview (TEXTO, sin render): titular, párrafo, niveles, tag, chart sí/no +
   │        "¿Apruebas esta Story? ¿Generar y guardar el PNG final?"
   │        └─ NO aprueba → CB-3/AC5: no renderiza ni guarda. FIN.
   │
   └─ (aprobado) ─────────────────────────────────────────────────────────────
        │ R6  ruta = scripts\ruta_story.ps1 -Fecha .. -Activo TICKER
        │        -Plantilla alerta -Hora HH-MM
        │
        │ R4  uv run python scripts/story_render.py
        │        --template templates/stories/alerta.html --out <ruta>  (payload por stdin)
        │        │
        │        ├─ build_html(payload, template) ──── (PURO, sin Playwright)
        │        │     fences (variacion/vol/chart) + {{tokens}} → HTML final
        │        │
        │        └─ render_png(html, out) ──────────── (Playwright headless)
        │              viewport 1080×1920 → PNG exacto
        │
        └─ R6  muestra <ruta> lista para adjuntar manualmente en WhatsApp
```

### 1.2 Piezas y responsabilidades

| Pieza | Tipo | Responsabilidad única | Qué NO hace |
|---|---|---|---|
| `.claude/commands/story.md` | prompt | Orquestar R1-R7: recolectar (motor + narrativa), payload, preview, aprobar, invocar script, mostrar ruta | No renderiza; no inventa precios (motor o manual) |
| `scripts/story_render.py` | Python | Único renderer: `payload + template → PNG 1080×1920` | Ninguna lógica de negocio |
| `templates/stories/alerta.html` | snapshot HTML+CSS | Layout estático "03 Alerta" con los slots del contrato D1 | No corre React del canvas; no accede a red |
| `scripts/ruta_story.ps1` | PowerShell | Ruta canónica bajo `data/stories/` + crear carpetas | No escribe el PNG |
| `tests/test_story_render.py` | pytest | Mapeo (puro) + dimensiones (`skipif`) + chart embed | No compara pixel-a-pixel |

RNF5: agregar una plantilla (#111-#115) = nuevo snapshot HTML + nuevo `[tipo]` + su mapeo — sin
segundo renderer, sin tocar `render_png`.

---

## 2. Decisiones de implementación

### D1 — Inyección: micro-plantilla stdlib con tokens `{{campo}}` + fences `<!-- IF -->`

**Sustitución de placeholders `{{token}}` + fences `<!-- IF:x -->…<!-- ENDIF:x -->`, resueltos
con `str`/`re` de la stdlib. Sin Jinja2** (dependencia innecesaria; las llaves `{}` del CSS
embebido chocan con `str.format`). Consistente con el patrón `{{...}}` que ya usa `apertura.md`.

**Importante (hallazgo del canvas)**: el canvas real NO tiene tokens de contenido — todo el texto
es ejemplo estático. Los tokens de abajo los define **este repo** al escribir el snapshot
`alerta.html`; el HTML del snapshot DEBE usar exactamente estos nombres.

Tokens escalares (siempre presentes):

| Token en el HTML | Origen en el payload |
|---|---|
| `{{chip_categoria}}` | `chip_categoria` (ej. `COMMODITIES · ORO`) |
| `{{fecha_hora}}` | `fecha_hora` (ej. `13 JUL 2026 · 11:15`) |
| `{{titular}}` | `titular` |
| `{{parrafo}}` | `parrafo` |
| `{{rotulo_activo}}` | `rotulo_activo` (ej. `ORO · XAU/USD`) |
| `{{tag_riesgo}}` | `tag_riesgo` (ej. `RIESGO ALTO`) |
| `{{precio_actual}}` | `precio_actual` (coma decimal, punto miles) |
| `{{soporte}}` | `soporte` |
| `{{resistencia}}` | `resistencia` |
| `{{rotulo_grafico}}` | `rotulo_grafico` (ej. `XAU/USD · VELAS 4H`) |
| `{{fuente}}` | `fuente` (ej. `COMEX`) |
| `{{sesgo_slug}}` | derivado: `variacion.direccion` o `sesgo.lower()` → clase CSS de color (presentación) |

Bloques opcionales (fences que se eliminan enteros si el dato está ausente):

| Fence | Se conserva si… | Tokens internos |
|---|---|---|
| `<!-- IF:variacion -->…<!-- ENDIF:variacion -->` | clave `variacion` presente | `{{variacion_pct}}`, `{{variacion_flecha}}` (▲/▼ derivada de `direccion`) |
| `<!-- IF:vol -->…<!-- ENDIF:vol -->` | `vol_pct` presente | `{{vol_pct}}` |
| `<!-- IF:chart_img -->…<!-- ENDIF:chart_img -->` | `chart_png` presente y el archivo existe | `{{chart_src}}` (URI `file:///` derivada) |
| `<!-- IF:chart_svg -->…<!-- ENDIF:chart_svg -->` | `chart_png` ausente/`null` | (SVG decorativo de velas, estático) |

`chart_img`/`chart_svg` son **fences complementarios**: exactamente uno sobrevive según la
presencia de `chart_png` (equivalente local del par `chartImg`/`chartDraw` del canvas). Si
`chart_png` apunta a una ruta inexistente → `StoryRenderError` accionable (CB-8), nunca imagen
rota.

Algoritmo de `build_html` (tres fases, orden fijo):
1. **Fences**: presente → quitar solo los marcadores; ausente → quitar bloque completo. Regex
   multiline no-greedy anclada al nombre.
2. **Sustitución escalar** de cada `{{token}}` conocido.
3. **Guardia**: cualquier `{{` restante → `StoryRenderError` listando tokens huérfanos (AC2).

### D2 — Estructura interna de `scripts/story_render.py`

- `class StoryRenderError(RuntimeError)` — mensajes en español, accionables (CB-7, CB-8).
- `build_context(payload: dict) -> dict[str, str]` — dict plano de tokens (deriva
  `variacion_flecha`, `sesgo_slug`, `chart_src` como URI `file:///`; valida existencia de
  `chart_png` si viene). **Puro.**
- `build_html(payload: dict, template_path: Path) -> str` — fences → sustitución → guardia.
  **Puro** (objeto de AC2/AC9).
- `render_png(html: str, output_path: Path, *, template_dir: Path) -> Path` — headless (AC3).
- `render_story(payload, template_path, output_path) -> Path` — orquestador público.
- CLI `main()` — ver D4.

Import de Playwright **perezoso** (dentro de `render_png`), patrón `MetaTrader5`: los tests puros
importan el módulo sin exigir Playwright (R8).

### D3 — Render headless (Playwright) — decisiones finas

1. **Assets relativos**: HTML resuelto se escribe a un temporal **dentro del dir del template**
   (`templates/stories/`) y se navega con `page.goto("file://…", wait_until="networkidle")` —
   no `set_content` (rompería assets relativos). Temporal eliminado en `finally`. El `<img>` del
   chart usa URI absoluta `file:///`, así no depende del dir del template.
2. **Viewport exacto**: `new_page(viewport={"width":1080,"height":1920})` +
   `page.screenshot(path=out)` sin `full_page`; `device_scale_factor` 1.
3. **Fuentes listas**: `page.evaluate("document.fonts.ready")` antes del screenshot. Nota: el
   canvas usa Google Fonts (Syne/DM Sans/Space Grotesk) vía red — el snapshot debe decidir en
   Apply entre (a) `<link>` a Google Fonts (requiere internet al renderizar) o (b) descargar los
   woff2 a `templates/stories/fonts/` y `@font-face` local. **Se elige (b): fuentes locales**,
   para que el render sea determinista y offline (consistente con "snapshot estático").
4. **CB-7**: `launch()` envuelto — ejecutable ausente → `StoryRenderError` con
   `uv sync --extra stories && python -m playwright install chromium`; `ModuleNotFoundError` →
   mismo error con `uv sync --extra stories`.
5. `browser.close()` en `finally`.

### D4 — Invocación desde `story.md`

Payload por **stdin** (heredoc JSON), CLI con `--template` y `--out`:

```bash
uv run python scripts/story_render.py \
  --template templates/stories/alerta.html \
  --out "data/stories/2026-07-13/xauusd/alerta/11-45_alerta.png" <<'STORY_PAYLOAD'
{ ...payload story_alerta... }
STORY_PAYLOAD
```

- Éxito → ruta del PNG en stdout, exit 0. `StoryRenderError` → mensaje en stderr, exit 1 (el
  comando lo muestra tal cual).
- La ruta `--out` la produce `ruta_story.ps1` antes (R6); la carpeta ya existe.
- El PNG se renderiza **una sola vez, post-aprobación** (el preview de R5 es solo texto).

### D5 — `scripts/ruta_story.ps1` (hermano de `ruta_mensaje.ps1`)

Copia estructural con exactamente cuatro diferencias, sin tocar el original (RNF1):

| Aspecto | `ruta_mensaje.ps1` | `ruta_story.ps1` (nuevo) |
|---|---|---|
| Raíz | `data/mensajes` | `data/stories` |
| Parámetro | `-Tipo` | `-Plantilla` |
| Extensión | `.txt` | `.png` |
| Salida | `…/<Tipo>/<Hora>_<Tipo>.txt` | `…/<Plantilla>/<Hora>_<Plantilla>.png` |

Reutiliza idéntica la lógica de slug (`lowercase(ticker_mt5)` sin `.spot`/`#`/`/`, `_general` si
vacío). Ejemplo:

```powershell
scripts\ruta_story.ps1 -Fecha "2026-07-13" -Activo "XAUUSD" -Plantilla "alerta" -Hora "11-45"
# -> data/stories/2026-07-13/xauusd/alerta/11-45_alerta.png
```

### D6 — `pyproject.toml`: dependencia opcional (R8/AC8)

```toml
[project.optional-dependencies]
stories = ["playwright"]
```

- `playwright` NO entra en `[project].dependencies`.
- deptry: añadir `playwright` junto a `MetaTrader5` en `DEP001` (verificar rule exacto al correr
  el gate en Apply).
- `scripts/` está fuera de ruff/ty (issue #79) — `story_render.py` lo cubre `pytest`, consistente
  con `senal_manager.py`. Aceptado.

### D7 — Documentación (R9/R10/AC7)

- **`CLAUDE.md`**: sección "Stories GI" **inmediatamente después de "MCP Servers integrados"**
  (confirmado por el director). Contiene el literal "solo lectura" + la regla completa + fila
  `/story` en la tabla Capa 2 + conteo 24→25 del encabezado.
- **`.claude/shared/modo_ejecutivo.md`**: `/story` en **No elegibles**, razón igual a `/chart`.
- **`.gitignore`**: `data/stories/*.png`.

---

## 3. Estructura de archivos afectados

```
NUEVOS
  .claude/commands/story.md                      (R1-R7)
  scripts/story_render.py                         (R4 — único renderer)
  scripts/ruta_story.ps1                          (R6/D5)
  templates/stories/alerta.html                   (snapshot; slots = contrato D1)
  templates/stories/fonts/*.woff2                 (Syne/DM Sans/Space Grotesk locales, D3.3)
  tests/test_story_render.py                      (AC2, AC3, AC9)
  tests/fixtures/stories/fixture_template.html    (contrato mínimo para test de motor)
  tests/fixtures/stories/fixture_chart.png        (PNG mínimo para AC9)

MODIFICADOS
  pyproject.toml            (+ optional-dependencies stories; deptry)
  .gitignore                (+ data/stories/*.png)
  CLAUDE.md                 (+ sección "Stories GI" tras "MCP Servers integrados"; /story; 24→25)
  .claude/shared/modo_ejecutivo.md   (+ /story en "No elegibles")

NO SE TOCAN (RNF1)
  .claude/commands/alerta.md · .claude/commands/apertura.md · .claude/commands/chart.md
  scripts/ruta_mensaje.ps1  ·  src/market_data_mcp/**  ·  data/charts/**
```

---

## 4. Riesgos y mitigaciones (a nivel Design)

| Riesgo | Mitigación |
|---|---|
| Desalineamiento payload↔template | Contrato de tokens D1 fijo (canvas ya leído íntegro — sin pendientes); fase-guardia falla en test ante `{{}}` huérfano. |
| Chromium ausente / entorno cambia | `StoryRenderError` accionable; render `skipif` en gate; fallback Pillow documentado en spec. |
| Webfonts: red en render | Fuentes woff2 locales en `templates/stories/fonts/` (D3.3) — render offline determinista. |
| Chart embebido roto | Validación de existencia en `build_context` → `StoryRenderError` (CB-8). |
| `story_render.py` fuera de ruff/ty | Cubierto por pytest; consistente con `scripts/` existentes. |
| Fuga de datos al canvas (RNF4) | Solo lectura de snapshot local; ningún paso hace red hacia claude.ai. Regla en `CLAUDE.md` (R9). |

---

## 5. Estrategia de validación (mapa AC → verificación)

Test-first: los tests de AC2/AC3/AC9 se escriben antes de dar por buena la implementación.

| AC | Tipo | Verificación |
|---|---|---|
| AC1 | estructural | `story.md` contiene pasos R1-R7 en orden + "un solo activo por corrida". |
| AC2 | pytest puro | `build_html(payload_sin_variacion_ni_vol_ni_chart, alerta.html)` → escalares inyectados; sin `{{`; sin slots de variación/vol; SVG decorativo presente, sin `<img>`. |
| AC2-motor | pytest puro | Test sobre `fixture_template.html` (contrato mínimo, aísla el motor del snapshot de marca). |
| AC3 | pytest `skipif` | PNG existe, IHDR == (1080, 1920), > 5 KB. |
| AC9 | pytest puro | Con `chart_png` → `<img>` con URI `file:///` y sin SVG; ruta inexistente → `StoryRenderError`. |
| AC4/AC5/AC6 | ejecución guiada | Walkthrough con el director (camino feliz / rechazo / flag ejecutivo). |
| AC7 | `rg` | "solo lectura" en `CLAUDE.md`; `/story` en `modo_ejecutivo.md`. |
| AC8 | `rg` | grupo `stories` con `playwright`; ausente del core. |

Detalles de test (contrato para Apply):
- Import del módulo bajo `scripts/`: insertar `<repo>/scripts` en `sys.path` desde el test (no
  tocar `conftest.py`).
- `_png_size(path)`: width/height big-endian uint32 en offsets 16/20 del PNG (sin Pillow).
- `_chromium_disponible()`: import + localizar ejecutable; cualquier excepción → skip.
- Payload de ejemplo: el de `spec.md` §"Contrato de datos" con `variacion`/`vol_pct` omitidos y
  `chart_png: null` (ejerce CB-4 y el fence `chart_svg` en un solo caso).

---

## 6. Decisiones ya confirmadas por el director

1. ~~Lectura completa del canvas~~ — **HECHA** (2026-07-13, DesignSync solo-lectura). Contrato de
   campos verificado; sin pendientes del canvas.
2. Ubicación de la sección "Stories GI" en `CLAUDE.md`: **después de "MCP Servers integrados"**.
3. Piloto: **03 Alerta de Mercado**, fuente híbrida (niveles motor + narrativa `/alerta`).
4. Detalle de gate (confirmable en Apply): `playwright` junto a `MetaTrader5` en deptry `DEP001`.

Gate DESIGN → APPLY: aprobado por el director el 2026-07-13 (`design_approved_by: bbenja11`).
La enmienda de piloto fue igualmente aprobada por el director en sesión (comentario en #109).

---

## 7. Desglose de tareas

Ver `tasks.md` (espejo actualizado con la piloto "alerta").

---

## 8. Referencias

- `spec.md` (enmendada 2026-07-13 — contrato `story_alerta`, R1-R10, CB-1..8, AC1-9)
- `proposal.md` (9 decisiones del director) + comentario de re-alcance en issue #109
- `docs/design/stories-gi/plantillas-stories-gi.md` (campos verificados de "03 Alerta")
- `.claude/commands/alerta.md` (criterio editorial) · `.claude/commands/apertura.md` (fallback
  MT5→manual) · `.claude/commands/chart.md` (PNG fuente de `chart_png`)
- `scripts/ruta_mensaje.ps1` · `pyproject.toml` · `.gitignore` · `tests/conftest.py`
- Issues #110-#115 (roadmap de plantillas restantes)
