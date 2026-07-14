# Code-Quality Report — Change #109 (`/story alerta`)

Gate 2 de Two-Stage Review (solo corre porque Gate 1 = ✅). Auditado sobre
`feat/comando-story-alerta-109` (commit `855f432`).

## Toolchain real ejecutada

```
uv run ruff check .          -> All checks passed!
uv run ty check              -> All checks passed!
uv run pytest tests/test_story_render.py -v  -> 6 passed
uv run pytest -q             -> 73 passed (suite completa del repo)
uv run deptry .              -> no disponible en este entorno local
                                 ("Failed to spawn: deptry — program not found").
                                 No instalado en `[dependency-groups] dev` de
                                 pyproject.toml; normalmente corre en el gate en
                                 contenedor (memoria del repo). La config de
                                 `[tool.deptry.per_rule_ignores]` fue inspeccionada
                                 manualmente: `DEP001 = ["MetaTrader5", "playwright"]`
                                 es correcta para el patrón de import perezoso.
```

Nota de entorno: Chromium de Playwright SÍ está instalado en esta máquina (validado por el
orquestador en el walkthrough), por lo que `test_render_dimensiones_1080x1920` corrió real (no
`skipped`) y pasó con PNG 1080×1920 > 5 KB. En un contenedor de gate sin Chromium ese test
saldría `skipped` — comportamiento esperado y documentado en spec.md Riesgo 5 / design.md D3, no
es una falla.

## Patrones y arquitectura

- **Invariante hexagonal respetado**: `src/market_data_mcp/**` no se toca (confirmado en el diff).
  El código nuevo vive deliberadamente fuera de la capa hexagonal, en `scripts/` — mismo régimen
  que `senal_manager.py` (excluido de ruff/ty por `extend-exclude = ["scripts", ".pulse"]`,
  issue #79). Consistente con la nota de arquitectura de `design.md`: "el módulo de render no
  contiene lógica de negocio".
- **Separación de responsabilidades**: `story.md` (prompt) hace toda la recolección/decisión de
  negocio; `story_render.py` es puramente `payload -> HTML -> PNG`, sin llamadas a
  `get_asset_levels` ni WebSearch ni criterio editorial. Cumple design.md §1.2.
- **Import perezoso de Playwright**: dentro de `render_png`, con manejo explícito de
  `ModuleNotFoundError` y `PlaywrightError` -> `StoryRenderError` accionable. Mismo patrón que
  `MetaTrader5` en el MCP (precedente ya establecido en el repo).
- **`build_html` puro**: no toca disco salvo para leer el template y (en `build_context`) validar
  la existencia de `chart_png` — efecto secundario mínimo y justificado por CB-8. El algoritmo de
  3 fases (fences -> tokens -> guardia) es determinista y está cubierto por
  `test_build_html_token_huerfano_lanza_error`.
- **`render_png`**: cierra el browser en `finally`, limpia el archivo temporal en `finally`,
  usa `file://` en vez de `set_content` para que los assets relativos (fuentes locales) resuelvan
  — coincide con D3.1. Sin fugas de recursos detectadas.

## Naming y docstrings en español

- Todos los docstrings de `scripts/story_render.py` están en español, describen el porqué (no solo
  el qué) y referencian las decisiones de diseño (D1/D2/D3) — buen nivel de trazabilidad.
- Nombres de función en español donde corresponde al dominio (`_resolver_fences`,
  `_sustituir_tokens`, `_validar_sin_huerfanos`, `_fence_presente`) y en inglés donde es API pública
  idiomática de Python (`build_html`, `build_context`, `render_png`, `main`) — consistente con el
  resto del repo (`senal_manager.py` mezcla igual).
- `scripts/ruta_story.ps1`: comentarios y ayuda (`.SYNOPSIS`/`.DESCRIPTION`) en español, sigue el
  mismo estilo que `ruta_mensaje.ps1`.
- No aplica `SecretStr`: no hay credenciales ni secretos en el flujo de `/story` (Playwright local,
  sin red, sin API keys).

## Calidad y cobertura de tests

- `tests/test_story_render.py`: 6 tests, cubren exactamente los ACs asignados a pytest (AC2, AC9,
  AC3) más un caso adicional no exigido explícitamente pero valioso
  (`test_build_html_token_huerfano_lanza_error`, sobre un fixture aislado del snapshot de marca).
- Aislamiento correcto: `test_build_html_contract`/`test_alerta_no_placeholders` no dependen de
  Playwright; solo `test_render_dimensiones_1080x1920` lo requiere y está marcado `skipif` con una
  detección robusta (`_chromium_disponible` atrapa cualquier excepción, no solo
  `ModuleNotFoundError`).
- `_png_size` reimplementa la lectura de IHDR sin Pillow (dependencia extra evitada), documentado
  y correcto (offsets 16/20, big-endian, según spec PNG).
- Fixtures (`fixture_template.html`, `fixture_chart.png`) aíslan el motor genérico del snapshot de
  marca real, permitiendo testear el contrato sin acoplarse a cambios visuales futuros del HTML de
  "alerta" — buena práctica de test, reduce fragilidad.
- Import de `scripts/` vía `sys.path.insert` dentro del propio archivo de test (no toca
  `conftest.py`), tal como exige design.md §5 — verificado.

## Documentación

- `CLAUDE.md`: sección "Stories GI" bien ubicada (inmediatamente tras "MCP Servers integrados"),
  contiene la regla "solo lectura" en términos claros, actualiza el conteo de comandos 24→25 y
  agrega la fila de `/story` en la tabla de Capa 2 — consistente con el resto del archivo.
- `.claude/shared/modo_ejecutivo.md`: la entrada de `/story` en "No elegibles" usa el mismo
  criterio y tono que las entradas existentes (`/chart`).

## Hallazgos menores (no bloqueantes)

- La desviación de `.gitignore` (3 líneas de higiene no ligadas a #109) ya está documentada en
  `spec_compliance_report.md` — se reitera aquí solo para que quede visible también desde la
  óptica de calidad: es higiene de bajo riesgo, no afecta ningún test ni comportamiento, pero
  idealmente viajaría en un commit `chore:` separado.
- `deptry` no pudo ejecutarse en este entorno local (no instalado); se recomienda confirmarlo en
  el gate real en contenedor antes de mergear, aunque la configuración estática (`per_rule_ignores`)
  ya está correctamente actualizada para `playwright`.

## Veredicto

**CODE_QUALITY: ✅**

Toolchain real (ruff, ty, pytest) en verde; 73/73 tests del repo pasan, incluidos los 6 nuevos de
Stories con el caso AC3 (dimensiones) corriendo real (no `skipped`) en esta máquina. Arquitectura
hexagonal intacta, separación de responsabilidades limpia, docstrings en español con buena
trazabilidad a las decisiones de diseño, tests bien aislados y sin dependencias innecesarias.
