# Enchufe de estrategia, fase 3: informe, Avisos, `/story`, analista y semanal

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que el informe, Avisos, la ruta `alerta` de `/story`, el bot de analistas, LinkedIn y el cierre semanal tomen la lectura técnica de la estrategia activa, y que nadie fuera de `scripts/estrategia/` vuelva a decidir dirección o niveles.

**Architecture:** una sola función de infraestructura, `referencia_semanal.lectura_actual`, entrega la `Lectura` del día de cualquier activo (contra la referencia de la semana si la tiene; si no, `leer()`). Todos los consumidores la usan, y la tool MCP `get_lectura` la expone. Lo que fase 2 dejó vivo "hasta S6/S7" se borra a medida que su último consumidor pasa a la `Lectura`.

**Tech Stack:** Python 3.12, pandas, matplotlib (informe), Lightweight Charts (piezas), fastmcp, pytest.

**Spec:** `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md` (§6, §7 fase 3, §8). Fase 2: `docs/superpowers/plans/2026-10-11-enchufe-fase-2.md`.

## Global Constraints

- Lo mismo que la fase 2: nada macro en la estrategia, texto de cliente sin guion largo ni voseo, precios con `digits`, `git add` explícito, TDD.
- **Las ramas se apilan** (S6 sobre S5, S7 sobre S6): el merge de cada PR lo hace el director, en orden. Instrucción del director del 2026-10-11: completar todas las fases y dejar los ajustes visuales para el final.
- `get_asset_levels` se queda como dato crudo (spec §6). Ningún pipeline de producción decide con ella.

## Decisiones de este plan

- **Una sola lectura del día**: `lectura_actual(estrategia, ticker, digits, lector, ahora, base, referencia=None)` vive en `referencia_semanal` (se muda desde `pipeline_carrusel.lectura_para_despacho`, que queda como alias). No guarda reemplazos: eso es solo del escáner.
- **El informe usa la lectura operativa (4H)** y su gráfico diario (matplotlib, banner del PDF) dibuja como horizontales los niveles que el texto nombra: el que se vigila, el que invalida y el objetivo. Sin medias: serían una segunda lectura en la imagen. La frase técnica sale del estado y la dirección de la lectura.
- **Avisos** arma la lámina de datos con `construir_payload_lectura` y la refresca con `refrescar_payload_lectura`; su gráfico se pide en el marco de la lectura y con sus líneas. El guardia de cifras de Avisos deja de usar `CAMPOS_PRECIO` de LinkedIn (`s1`, `r1`, `ema_50`, Donchian) y mide contra los niveles de la lectura.
- **`get_lectura(ticker)`** devuelve `lectura_a_dict` de la estrategia activa más `estrategia` y `semana`, o el contrato de error `{"error", "message"}`.
- **`/story alerta`** pide `get_lectura` en vez de `get_asset_levels` para dirección, niveles y escenarios.
- **S7** (analista, pieza semanal, LinkedIn, cierre semanal) se detalla al empezar S7, con el código de S6 en la rama: describir hoy funciones de S6 que todavía no existen es el error que el mapa de sesiones prohíbe.

## Sesión S6

### Task S6-1: `lectura_actual` en infraestructura
- Move `pipeline_carrusel.lectura_para_despacho` a `referencia_semanal.lectura_actual`; `pipeline_carrusel.lectura_para_despacho = rs.lectura_actual` para no romper el despacho.
- Test: los de `test_pipeline_carrusel` sobre `lectura_para_despacho` siguen pasando, y uno nuevo en `test_referencia_semanal` llama `lectura_actual` directo.

### Task S6-2: Tool MCP `get_lectura`
- Create: `src/market_data_mcp/tools/lectura.py` con `register(mcp)` y la función pura `obtener_lectura(ticker, estrategia=None, lector=None, ahora=None, base=None) -> dict`.
- Ticker fuera del catálogo → `{"error": "TICKER_INVALIDO", ...}`; MT5 o la estrategia fallan → `{"error": "LECTURA_NO_DISPONIBLE", ...}`.
- Registrar en `server.py` y nombrarla en `instructions`.
- Test: `tests/test_tool_lectura.py` con estrategia y lector falsos.

### Task S6-3: El informe pasa a la `Lectura`
- `pipeline_informe.leer_activos` lee con `lectura_actual`; `_frase_tecnica(lectura)`; `_lectura_por_activo` nombra precio, nivel a vigilar, soporte y resistencia de `niveles_publicados`.
- `grafico_informe.construir_grafico(..., niveles=None, horizontales=None, medias=True)`: con `horizontales=[(precio, rótulo, rol)]` y `medias=False` dibuja los niveles de la lectura y no las EMA.
- Tests en `tests/test_pipeline_informe.py` / `tests/test_grafico_informe.py` / `tests/test_voz_cliente_informe.py`.

### Task S6-4: Avisos pasa a la `Lectura`
- `leer_terminal` devuelve `{"ticker", "activo", "seleccion", "cierres", "precios"}`, con `seleccion` del mismo formato que el escáner (`lectura`, `marco`, `volatilidad_tipica`, `score`, `puntaje`, `gates_omitidos`, `referencia`) y `precios` = `{"price", "vigilar", "invalidacion", "objetivo"}`.
- `lamina_datos` usa `construir_payload_lectura`; `direccion` sale de la lectura; `grafico_tradingview` pide el marco de la lectura y sus líneas; `refrescar_datos` usa `refrescar_payload_lectura` con la referencia de la pieza; `fila_medida` y `CAMPOS_AVISOS` usan los niveles de la lectura.
- Se borran `pipeline_carrusel.refrescar_payload`, `divergencia_editorial` y `direccion_publicada` (su último consumidor era Avisos).
- Tests: `tests/test_pipeline_avisos.py` reescribe `lectura_falsa` con una `Lectura`.

### Task S6-5: `/story alerta`
- `.claude/commands/story.md`, ruta `alerta`: dirección, niveles y escenarios de `get_lectura`; `get_asset_levels` solo como dato crudo. Se regeneran los workflows de AGY.

### Task S6-6: Suite, verificación real y PR
- `uv run pytest` verde salvo los 4 conocidos; `--preparar` real de Avisos y del informe con MT5; PR apilado sobre S5.
