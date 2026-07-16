# Tasks: Stories GI · Fase C — plantilla Flash (cierre multi-activo) 16:9

> Desglose de implementación del Change #129. Todo aditivo (motor `scripts/story_render.py`
> intacto). Orden: snapshot → tests (fallan) → registro comando → docs → verde. Commits con
> `git add` EXPLÍCITO (nunca `-A`); no tocar los archivos sin commitear del director.

## 1. Snapshot de marca
- [ ] 1.1 Crear `templates/stories/flash.html` (1920×1080) según el snapshot de `design.md`:
  andamiaje de marca de `edu.html` (4 `@font-face` locales, `.story`, footer + disclaimer CFD),
  fondo oscuro con gradiente teal `#10222B`, acento estructural teal `#3E91AF` (D2). Cuerpo:
  `{{kicker}}` (chip, `.flash-kicker:empty{display:none}`) + `{{titulo}}` (Syne) + `{{fecha}}` +
  `<table>` con `<thead>` (rótulos Activo/Tipo/Último/Var. día) **fuera** del FOR y un único bloque
  `<!-- FOR:filas --><tr>…{{nombre}}…{{tipo}}…{{valor}}…flash-var--{{direccion}}…{{variacion}}…</tr><!-- ENDFOR:filas -->`
  (R1/R3/R4/D4). Celda de variación con clases `.flash-var--alcista/bajista/lateral` (color +
  `::before` flecha, D6/R6). Sin fences `IF`, sin gráfico/`<img>`/`<svg>` (AC2/AC7).

## 2. Tests de mapeo (aditivos)
- [ ] 2.1 En `tests/test_story_render.py`: agregar `FLASH_TEMPLATE` y el fixture `PAYLOAD_FLASH`
  (payload de R2 con 3 filas aplanadas alcista/bajista/lateral).
- [ ] 2.2 Agregar tests análogos a `test_edu_*`: `test_flash_no_placeholders` (AC3),
  `test_flash_kicker_vacio` (AC4), `test_flash_filas_vacio`/`_uno`/`_n` (AC5, loop 0/1/N),
  `test_flash_render_dimensiones` (`skipif` sin Chromium, AC6). Sin fixture nuevo en
  `tests/fixtures/stories/`; sin tocar `conftest.py`.

## 3. Registro del comando
- [ ] 3.1 `.claude/commands/story.md` PASO 0: agregar `flash` a la lista dura de `[tipo]` y a los
  mensajes CB-1/CB-9; enrutar a "Ruta `flash`" (R7/AC8).
- [ ] 3.2 `.claude/commands/story.md`: nuevo bloque "Ruta `flash`" (espejo de "Ruta `edu`", con
  recolección de datos del motor): lista de activos + `titulo` + `kicker` opcional; por activo,
  `get_asset_levels` (fallback manual patrón `apertura.md` PASO 4A) → `valor` formateado por
  `digits` + `variacion` con signo/`%` + `direccion` derivada; `fecha` del reloj de Chile; preview
  que lista las filas; render/guardado `-Activo "_general" -Plantilla "flash"`; límites editoriales
  R9 (AC9/AC10).

## 4. Documentación
- [ ] 4.1 `CLAUDE.md` sección "Stories GI": enumerar `flash` entre los `[tipo]` de `/story`
  soportados (R11/AC11), sin tocar el resto.

## 5. Verificación
- [ ] 5.1 `uv run pytest tests/test_story_render.py` verde (mapeo + loop 0/1/N; render `skipif` si
  no hay Chromium).
- [ ] 5.2 Chequeos estructurales `rg` de AC1/AC2/AC7/AC8/AC9/AC10/AC11 y `git diff master` sobre
  motor + snapshots previos + `ruta_story.ps1` sin cambios (AC12).
- [ ] 5.3 `mark_tests_passed` + commit con `git add` EXPLÍCITO de los archivos del Change
  (`templates/stories/flash.html`, `tests/test_story_render.py`, `.claude/commands/story.md`,
  `CLAUDE.md`, artefactos `.pulse/`). NUNCA `git add -A`.
