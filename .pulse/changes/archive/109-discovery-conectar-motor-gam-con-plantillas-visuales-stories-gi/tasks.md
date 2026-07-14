# Tasks: Comando `/story alerta` — render de Stories GI (#109)

> Desglose accionable de `design.md` §7 (**versión enmendada 2026-07-13** — piloto "03 Alerta de
> Mercado"; ver nota de enmienda en `spec.md`). Ordenado por dependencia. Cada tarea de código
> lleva su criterio de aceptación ejecutable. Mapeo a requisitos entre paréntesis.

## 0. Prerequisito de Apply (humano / canvas)
- [x] 0.1 ~~(BLOQUEANTE)~~ Lectura completa del canvas Claude Design — **HECHA 2026-07-13** vía
  DesignSync (solo lectura). Hallazgos: el canvas no tiene tokens de contenido (texto estático);
  campos reales de "03 Alerta" documentados en `docs/design/stories-gi/plantillas-stories-gi.md`;
  contrato de tokens fijado en design.md D1. Sin pendientes del canvas.

## 1. Andamiaje de datos y helpers (sin render)
- [x] 1.1 Crear `scripts/ruta_story.ps1`, hermano de `ruta_mensaje.ps1` (raíz `data/stories`,
  `-Plantilla`, extensión `.png`; misma lógica de slug). (R6, D5)
  — *Criterio (AC4-parcial): `ruta_story.ps1 -Fecha "2026-07-13" -Activo "XAUUSD" -Plantilla "alerta" -Hora "11-45"`
  → `data/stories/2026-07-13/xauusd/alerta/11-45_alerta.png` y crea las carpetas;
  `-Activo` omitido → `_general`.*
- [x] 1.2 `.gitignore`: añadir `data/stories/*.png`. (D7)
  — *Criterio: `rg "data/stories" .gitignore` ≥1 match.*
- [x] 1.3 `pyproject.toml`: `[project.optional-dependencies] stories = ["playwright"]` + ignore
  deptry para `playwright` (junto a `MetaTrader5`, rule a confirmar al correr el gate). (R8, D6)
  — *Criterio (AC8): grupo `stories` con `playwright`; `playwright` ausente de `[project].dependencies`.*

## 2. Motor de render (test-first)
- [x] 2.1 Crear `tests/fixtures/stories/fixture_template.html` (tokens escalares + fences
  `IF:variacion`/`IF:vol`/`IF:chart_img`/`IF:chart_svg` de D1) y
  `tests/fixtures/stories/fixture_chart.png` (PNG mínimo válido para AC9). (soporte AC2-motor/AC9)
- [x] 2.2 Escribir `tests/test_story_render.py` **antes** del módulo: helpers `_png_size` (IHDR),
  `_chromium_disponible`; `test_build_html_contract` (fixture), `test_alerta_no_placeholders`
  (HTML real, payload sin variación/vol/chart → SVG decorativo, sin `<img>`),
  `test_alerta_chart_embebido` (AC9: con `chart_png` → `<img> file:///`, sin SVG; ruta
  inexistente → `StoryRenderError`), `test_render_dimensiones_1080x1920` (`skipif`). Insertar
  `scripts/` en `sys.path`; no tocar `conftest.py`. (AC2, AC3, AC9)
- [x] 2.3 Implementar `scripts/story_render.py`: `StoryRenderError`, `build_context` (deriva
  `variacion_flecha`, `sesgo_slug`, `chart_src` URI + validación de existencia CB-8),
  `build_html` (fences→sustitución→guardia, D1, con fences complementarios chart_img/chart_svg),
  `render_png` (Playwright headless, import perezoso, D3), `render_story`, CLI `main()`
  (stdin + `--template` + `--out`, D4). (R4, CB-4, CB-7, CB-8)
  — *Criterio (AC2): `build_html(payload_ejemplo, fixture)` inyecta escalares, elimina bloques
  ausentes y NO deja `{{}}`; token huérfano → `StoryRenderError`.*
  — *Criterio (CB-7): sin Chromium, `render_png` lanza `StoryRenderError` con
  `uv sync --extra stories && python -m playwright install chromium`, nunca un traceback.*

## 3. Snapshot de marca
- [x] 3.1 Escribir `templates/stories/alerta.html` con el layout real de "03 Alerta de Mercado"
  (identidad verificada: fondo `#0D0D1A`/degradado rojizo `#2A1220`, chips, tarjeta de precio con
  Soporte/Resistencia/Vol, SVG de velas decorativo con soporte rotulado, footer
  `@grupointeligencia` + `FUENTE:` + disclaimer CFD), usando exactamente los tokens/fences de D1.
  Descargar Syne/DM Sans/Space Grotesk como woff2 a `templates/stories/fonts/` y referenciarlas
  con `@font-face` local (D3.3 — render offline determinista). (snapshot de marca)
  — *Criterio (AC2 real): `test_alerta_no_placeholders` verde.*
  — *Criterio (AC3): `test_render_dimensiones_1080x1920` produce PNG 1080×1920 y >5 KB con Chromium.*
  — *Criterio (AC9): `test_alerta_chart_embebido` verde.*

## 4. Comando de orquestación
- [x] 4.1 Escribir `.claude/commands/story.md` (R1-R7, D4): validar `[tipo]`==`alerta` (CB-1,
  mencionando que los demás tipos llegan con #111-#115); rechazar flag `ejecutivo` avisando y
  continuando (R7/CB-6); recolección híbrida para **1** activo (R2: niveles vía
  `get_asset_levels` con fallback manual CB-2, narrativa con criterio `/alerta` PASO 1 — evento
  real o lectura técnica CB-5, variación/vol opcionales CB-4, chart embebido opcional); construir
  payload `story_alerta` (R3: `digits` + coma decimal, `tag_riesgo`, reloj de Chile); preview de
  texto + aprobación (R5/CB-3); invocar el script por stdin (D4); guardar vía `ruta_story.ps1` y
  mostrar la ruta (R6).
  — *Criterio (AC1): contiene pasos equivalentes a R1-R7 en orden y menciona "un solo activo por
  corrida". Criterio (AC4/AC5/AC6): walkthrough guiado.*

## 5. Documentación
- [x] 5.1 `CLAUDE.md`: sección "Stories GI" **inmediatamente después de "MCP Servers
  integrados"** (confirmado por el director): regla "solo lectura" (literal) + fila `/story` en
  Capa 2 + conteo de comandos 24→25. (R9, D7)
  — *Criterio (AC7): `rg -i "solo lectura" CLAUDE.md` ≥1 match.*
- [x] 5.2 `.claude/shared/modo_ejecutivo.md`: `/story` en "No elegibles", razón igual a `/chart`. (R10)
  — *Criterio (AC7): `rg "/story" .claude/shared/modo_ejecutivo.md` ≥1 match.*

## 6. Verificación integral
- [x] 6.1 `uv run pytest tests/test_story_render.py` (AC2/AC9 verdes; AC3 verde o `skipped` según
  Chromium). Verificaciones `rg` de AC7/AC8. Walkthrough guiado AC1/AC4/AC5/AC6 con el director.
