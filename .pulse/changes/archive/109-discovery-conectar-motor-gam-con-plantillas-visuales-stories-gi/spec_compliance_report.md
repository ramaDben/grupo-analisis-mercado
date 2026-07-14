# Spec-Compliance Report — Change #109 (`/story alerta`)

Gate 1 de Two-Stage Review. Auditado contra `proposal.md` -> `spec.md` (enmendado 2026-07-13,
piloto "03 Alerta de Mercado") -> `design.md` -> `tasks.md` vs. el delta implementado en
`feat/comando-story-alerta-109` (commit `855f432`, 24 archivos, no mergeado a master).

## Método
- Lectura íntegra de `proposal.md`, `spec.md`, `design.md`, `tasks.md`.
- `git diff --stat master feat/comando-story-alerta-109` + diff completo de cada archivo modificado
  (`.gitignore`, `pyproject.toml`, `CLAUDE.md`, `.claude/shared/modo_ejecutivo.md`).
- Lectura completa de los archivos nuevos: `.claude/commands/story.md`, `scripts/story_render.py`,
  `scripts/ruta_story.ps1`, `tests/test_story_render.py`, `templates/stories/alerta.html` (tokens/
  fences extraídos con grep y comparados 1:1 contra la tabla D1 de `design.md`).

## Requisitos funcionales (R1-R10) — verificación

| Req | Estado | Evidencia |
|---|---|---|
| R1 (registro/invocación) | ✅ | `story.md` PASO 0 valida `[tipo]==alerta`, rechaza vacío/otro tipo sin asumir default (CB-1) |
| R2 (recolección híbrida) | ✅ | PASOS 1-4: activo+TF, `get_asset_levels` con fallback manual (CB-2), narrativa criterio `/alerta` (CB-5), variación/vol opcionales (CB-4), chart opcional |
| R3 (payload) | ✅ | PASO 5 arma el payload exacto de `spec.md` §Contrato de datos |
| R4 (render centralizado) | ✅ | `story_render.py`: `build_context`/`build_html`/`render_png`/`render_story`/`main()` — idéntico a D2 |
| R5 (preview/aprobación) | ✅ | PASO 6, bloquea antes de renderizar/guardar (CB-3) |
| R6 (guardado canónico) | ✅ | `ruta_story.ps1` produce `data/stories/<Fecha>/<slug>/alerta/<Hora>_alerta.png`, idéntico al ejemplo de spec/design |
| R7 (rechazo `ejecutivo`) | ✅ | PASO 0.2 avisa y continúa (CB-6) |
| R8 (dependencia opcional) | ✅ | `[project.optional-dependencies] stories = ["playwright"]`, ausente de `[project].dependencies`; `deptry` `DEP001` incluye `playwright` junto a `MetaTrader5` |
| R9 (regla solo lectura) | ✅ | Sección "Stories GI" en `CLAUDE.md` inmediatamente después de "MCP Servers integrados", contiene literal "solo lectura" |
| R10 (no elegible ejecutivo) | ✅ | `.claude/shared/modo_ejecutivo.md` agrega `/story` a "No elegibles", mismo criterio que `/chart` |

## RNF1-RNF5 — verificación
- RNF1: `git diff --stat` confirma que `alerta.md`, `apertura.md`, `chart.md`, `ruta_mensaje.ps1`,
  `src/market_data_mcp/**`, `data/charts/**` **no aparecen** en el diff. ✅
- RNF2: formateo por `digits` presente en PASO 2 de `story.md` y en el payload de ejemplo
  (`2.318,40`, coma decimal/punto de miles). ✅
- RNF3: todo el contenido de `story.md`/docstrings en español. ✅
- RNF4: `story_render.py` no hace ninguna llamada de red; solo lee `templates/stories/` local. ✅
- RNF5: agregar plantilla futura = nuevo snapshot + nuevo mapeo + nuevo `[tipo]`, sin tocar
  `render_png`/`build_html` (ambos genéricos, no acoplados a "alerta" salvo por el path del
  template que se pasa como argumento). ✅

## Casos borde (CB-1..CB-8) y criterios de aceptación (AC1-AC9)
- Los 8 casos borde están codificados explícitamente en `story.md` y/o `story_render.py` (ver tabla
  R1-R10 arriba; CB-7/CB-8 cubiertos por `StoryRenderError` con mensajes accionables en
  `_MSG_CHROMIUM_AUSENTE` y la validación de `chart_png` en `build_context`).
- AC2/AC9: tokens y fences de `templates/stories/alerta.html` extraídos por grep coinciden
  exactamente con la tabla D1 de `design.md` (12 tokens escalares + 4 fences, ni uno de más ni de
  menos). `tests/test_story_render.py` ejercita ambos con el payload de `spec.md`.
- AC3: `test_render_dimensiones_1080x1920` verificado en vivo por el orquestador (PNG 1080×1920,
  Chromium instalado en esta máquina) — pasó.
- AC7: `CLAUDE.md` contiene "solo lectura"; `modo_ejecutivo.md` contiene `/story`. Confirmado por
  lectura directa (no solo `rg`).
- AC8: confirmado en `pyproject.toml` (ver tabla R8).

## Desviación encontrada — `.gitignore` con líneas fuera del alcance declarado

El diff de `.gitignore` en el commit `855f432` contiene, además de la línea especificada por
`spec.md`/`design.md` (`data/stories/*.png` — implementada como el patrón recursivo
`data/stories/**/*.png`, funcionalmente equivalente y más correcto, corregido por el orquestador
durante el walkthrough), **tres líneas no mencionadas en ningún artefacto de este Change**:

```diff
+# El ledger sqlite vive en el volumen Docker pulse-gam-ledger (ver .claude/plugins/pulse/.mcp.json)
 .pulse/state.sqlite
 ...
+.pulse/*.bak
 ...
+# Brainstorming visual companion (superpowers)
+.superpowers/
```

`design.md` §3 (MODIFICADOS) declara únicamente `.gitignore (+ data/stories/*.png)`. Estas tres
líneas son higiene de repo genuina y de bajo riesgo (ignorar backups del ledger Pulse y una carpeta
de una skill de brainstorming), pero no están autorizadas por ningún requisito de #109 — es scope
creep menor, probablemente arrastrado de trabajo paralelo en la rama al momento de commitear.

**Veredicto sobre esta desviación**: no bloquea el gate. No hay riesgo funcional, no toca ningún
AC, no introduce comportamiento nuevo observable, y es aditiva a un archivo de configuración de
higiene (nunca ejecuta lógica). Recomendación: el director puede aceptarlo tal cual (documentado
aquí) o pedir que se recorte a un commit `chore:` separado antes de mergear. **No se recortó** en
esta fase de Review porque Two-Stage Review no hace edits funcionales de código — se deja explícito
para que el director decida en la aprobación del PR.

## Veredicto

**SPEC_COMPLIANCE: ✅**

Ningún requisito de `tasks.md` quedó sin implementar. Ninguna feature implementada excede el
alcance de `design.md`/`tasks.md` de forma material (única excepción: 3 líneas de higiene en
`.gitignore`, documentadas arriba, sin riesgo). La implementación no diverge de `design.md` — los
nombres de función, el algoritmo de 3 fases de `build_html`, el CLI, la convención de guardado y la
estructura de archivos son un calco de las secciones D1-D7.
