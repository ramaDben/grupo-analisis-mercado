# Tasks: Stories GI · Fase B — plantilla Edu (concepto educativo) 16:9

> Desglose de implementación del Change #127. Todo aditivo, motor intacto. Deriva de
> `design.md` (D1-D6, snapshot propuesto, estrategia de validación) y `spec.md` (R1-R11,
> AC1-AC12).

## 1. Snapshot HTML
- [ ] 1.1 Crear `templates/stories/edu.html` (1920×1080) copiando el andamiaje de marca de
  `templates/stories/encuesta.html` (4 `@font-face`, `html,body`, `.story`, `.footer` con
  marca + disclaimer CFD) — verbatim salvo la paleta (R1, D1).
- [ ] 1.2 Aplicar la paleta con acento **verde educativo `#00DC82`** + teal `#53C1AB` en
  rótulos: gradiente de fondo `#0D0D1A`/`#123A2A`, chip `kicker` verde (D2).
- [ ] 1.3 Maquetar el cuerpo `.edu-*` en columna centrada: `{{kicker}}` (chip) +
  `{{titulo_concepto}}` (Syne) + `{{definicion}}` (DM Sans) + bloque ejemplo
  (`{{valor_a}}` / `{{operador}}` / `{{valor_b}}`) (R1/R6, D6).
- [ ] 1.4 Agregar el bloque bullets: rótulo estático "EN LA PRÁCTICA" y `<ul>` **fuera** de
  las marcas FOR, con `<!-- FOR:bullets --><li class="edu-bullet">{{texto}}</li><!-- ENDFOR:bullets -->`
  dentro (R3/R4, D4).
- [ ] 1.5 Declarar `.edu-kicker:empty { display: none; }` para el opcional `kicker` (R5, D5);
  verificar que NO hay ningún `<!-- IF: -->` en el archivo (AC2).

## 2. Comando `/story`
- [ ] 2.1 `.claude/commands/story.md` PASO 0: agregar `edu` a la lista dura de `[tipo]` y al
  mensaje CB-1/CB-7; enrutar a "Ruta `edu`" (R7, AC7/CB-7).
- [ ] 2.2 Nuevo bloque "Ruta `edu`" (espejo de "Ruta `encuesta`"): recolección editorial
  (título, definición, ejemplo, N bullets, kicker opcional), 100% editorial (sin
  `get_asset_levels` ni WebSearch), límites de longitud de R9, preview que lista bullets,
  render/guardado `ruta_story.ps1 -Activo "_general" -Plantilla "edu"` (R7/R8/R9, AC8/AC9/AC10).
- [ ] 2.3 Documentar en la "Ruta `edu`" el aplanado de `ejemplo` a `valor_a`/`operador`/
  `valor_b` y `bullets` como `[{"texto": "…"}]` en el payload al motor (D3/D4).

## 3. Tests
- [ ] 3.1 `tests/test_story_render.py`: constante `EDU_TEMPLATE` y fixture `PAYLOAD_EDU`
  (payload aplanado, 3 bullets) (R10).
- [ ] 3.2 `test_edu_no_placeholders` (AC3), `test_edu_kicker_vacio` (AC4).
- [ ] 3.3 `test_edu_bullets_vacio` / `_uno` / `_n` — loop bullets 0/1/N (AC5).
- [ ] 3.4 `test_edu_render_dimensiones` con `skipif` sin Chromium — PNG (1920,1080) > 5 KB (AC6).
- [ ] 3.5 Correr `uv run pytest tests/test_story_render.py` → verde (hilo principal verifica).

## 4. Documentación
- [ ] 4.1 `CLAUDE.md` § "Stories GI": enumerar `edu` entre los `[tipo]` soportados
  (alerta, quote, breaking, encuesta, edu) (R11, AC11).

## 5. Sin regresión
- [ ] 5.1 Confirmar `git diff master` sin cambios en `scripts/story_render.py`,
  `templates/stories/{alerta,quote,breaking,encuesta}.html`, `scripts/ruta_story.ps1` (AC12).
