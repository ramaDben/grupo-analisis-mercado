# Enchufe de estrategia, fase 4: purga y documentación (S8)

Spec: `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md`, §6 y §7 fase 4.
Mapa de sesiones: `docs/superpowers/plans/2026-10-09-enchufe-sesiones.md`.

**Entra:** S7 (`feat/enchufe-s7-analista`, PR #262). La rama de S8 se apila sobre ella
porque los merges de S4-S7 los hace el director en orden; el plan se escribió con el código
de S7 delante, que es la condición del mapa de sesiones.

**Sale:** ningún pipeline de producción decide con la lectura vieja, un test lo impide, y la
documentación que leen los dos runners describe la estrategia y no el `Score_GI`.

## Lo que se midió al empezar (2026-10-12)

Barrido de `scripts/`, `src/` y `tests/` sobre la rama de S7:

| Pieza de la §6 | Consumidores de producción | Decisión |
|---|---|---|
| `screener_gi.evaluar_activo`, `factor_*`, `direccion_tecnica` | ninguno | se borran |
| `gate_agotamiento`, `gate_banda`, `banda_estrecha`, `_banda_y_vela`, `UMBRAL_BANDA_*` | ninguno | se borran |
| `_RECEPTORES_POR_PAIS`, `_PATRONES_SEGUNDO_ORDEN` | solo `factor_catalizador` | se borran |
| `screener_gi._contexto_macro` | `pipeline_carrusel.preparar`, `analista/foco` | **se queda** (ver abajo) |
| `pipeline_carrusel.construir_payload` (el viejo) | ninguno, solo tests | se borra |
| rama vieja de `lectura_operativa` | ninguno: todo payload trae `lectura` | se borra; la función queda como la de la estrategia |
| aviso de `banda_estrecha` en `construir_mensaje_alerta` | ninguno | se borra |
| `MARCOS_CANONICOS`, `TIMEFRAME_GRAFICO` | `guardrails/nombres`, defaults de gráfico | se borran; las etiquetas salen de `Marcos.etiquetas` |
| categorías del suplemento `ATR diario consumido`, `la vela tipica cubre la banda`, `niveles de respaldo por ATR` | ningún motivo las emite ya | se borran |
| `direccion_gi.py`, `medir_direccion.py`, `analista/estadistica.py` | — | ya borrados en S4-S7 |

**`_contexto_macro` se queda, y no es una excepción a la §6 sino una lectura de ella.** La spec
la nombra junto a los factores porque alimentaba al catalizador. Lo que hace hoy es otra cosa:
trae el calendario del día para el **blackout** y para el contexto macro de cada canal, y avisa
cuando el calendario no respondió. Borrarla dejaría al gate de blackout sin datos. Pierde solo
la mención al factor catalizador en su aviso.

**`get_asset_levels` y `analizar_activo` se quedan en el MCP** como dato crudo (spec §6). El
guardián impide que un pipeline los use para decidir.

## Tareas

### S8-1 · Purga del escáner
- Borrar de `screener_gi.py` lo de la tabla y el import de `analizar_activo`.
- Borrar sus tests en `tests/test_screener_gi.py` (factores, banda, agotamiento, `evaluar_activo`).
- Corregir el docstring del módulo, que todavía dice que los factores siguen vivos.

### S8-2 · Purga del carrusel y del suplemento
- Borrar `construir_payload`, la rama vieja de `lectura_operativa`, el aviso de banda estrecha,
  `MARCOS_CANONICOS` y `TIMEFRAME_GRAFICO` (los defaults pasan a `marco_operativo()`).
- Migrar o borrar los tests de `test_pipeline_carrusel.py` que construyen el payload viejo.
- Borrar las tres categorías muertas de `suplemento_canal.CATEGORIAS` y sus tests.

### S8-3 · Temporalidades desde la estrategia
- `guardrails.nombres.marco_canonico` valida contra las etiquetas cortas de los marcos de la
  estrategia activa, no contra una tabla propia.
- Se borra la tabla de cuatro etiquetas de `.claude/commands/story.md`: el marco lo dice la
  estrategia y la tabla ya solo la usaban las piezas del analista, que salieron en S7.
- **Las notas que se publican son las de `notas_marco`.** Al empezar parecía que 12 de las 37
  `nota_volatilidad` había que reescribirlas porque no nombraban 4H. Al medir resultó que ya no
  las leía nadie: desde S4 el payload toma `notas_marco.<marco>`, y las ocho que existen nombran
  su marco. Se borró `nota_volatilidad` del catálogo y del escáner, y los tests pasan a exigir
  `notas_marco` del marco operativo en todo activo publicable de un canal cubierto.

### S8-4 · Test guardián
`tests/test_guardian_estrategia.py` lee la fuente de `scripts/` (salvo `scripts/estrategia/`) y
falla si aparece:
- `direccion_tecnica`;
- `ema_50` usada para decidir dirección (comparación contra el precio o un `if` con ella);
- `analizar_activo` importado o llamado en un pipeline;
- un import de `_get_support_resistance`.

Lleva una lista de excepciones **con motivo por entrada**, vacía si se puede: una excepción sin
motivo es la puerta por la que vuelve la lectura vieja.

### S8-5 · Documentación
- `CLAUDE.md`: se reescriben **Indicadores técnicos**, **El `Score_GI` y sus gates** (pasa a
  "El ranking de la estrategia y sus gates"), la parte del Playbook que fija la EMA 50, la regla
  de formato 6 y las reglas de temporalidad, apuntando a la doctrina
  (`docs/metodologia-tendencias.md`). Sin crecer: el techo del test de tamaño no se sube.
- `.claude/commands/*.md`: se quitan las menciones al `Score_GI`, a los factores, a la banda y
  al agotamiento.
- Se regeneran `.agents/rules/proyecto.md` (`scripts/agy_reglas.py`) y los workflows
  (`scripts/agy_workflows.py`).

## Verificación
- `uv run pytest`: verde salvo los 4 fallos de fecha conocidos de `test_despacho_avisos.py`.
- `uv run python scripts/agy_workflows.py --check` y la verificación de `agy_reglas.py`.
- Un `--preparar --matriz` real con MT5 para ver que el carrusel sigue armando piezas.
