# DISEÑO TÉCNICO — Apertura de Mercado interactiva (`/apertura`)

## Contexto

Hoy la PIEZA 1 "Apertura de mercado" de los comandos de día **hardcodea**:
- `timeframe: "H4"` en la llamada a `mcp__market-data__get_asset_levels`.
- La etiqueta fija `_Operativa intradía / swing corto_`, que enmarca los niveles como si fueran una **señal/recomendación de operativa**.

El director quiere que la apertura pase a ser **interactiva**, igual que ya hace `/chart`: que el sistema **siempre pregunte** activo, temporalidad e indicador, y que se **elimine el enfoque de señal** ("swing corto", etc.). La temporalidad se sigue explicando (lo exige `CLAUDE.md`), pero como **marco de lectura educativo**, no como recomendación de operativa.

Decisiones del director (brainstorming):
- **Estructura**: comando reusable `/apertura` que los comandos de día invocan (no editar cada PIEZA 1 con lógica duplicada).
- **Activos**: rotación de `agenda_semanal.json` **con override** (el director confirma/cambia/agrega).
- **Indicador**: **lectura en el texto** (no necesariamente chart).
- **Granularidad**: temporalidad e indicador **por activo**.
- **Operativa**: **etiqueta dinámica neutral** derivada de la temporalidad elegida.
- **Indicadores v1**: solo **RSI** y **ATR** (lo que devuelve el MCP). MACD/SMA/Bollinger se agregarán luego al MCP.

`mcp__market-data__get_asset_levels` (técnico MT5) **NO se toca**.

---

## Hallazgos clave

- `get_asset_levels(ticker, timeframe)` devuelve: `price, s1, s2, r1, r2, rsi_14, atr_14, trend, timestamp`. Los **únicos indicadores** disponibles son **RSI(14)** y **ATR(14)**; `trend` se deriva de EMA100. MACD/SMA/Bollinger NO vienen del MCP (solo por la vía chart de `scripts/mt5_integration.py`).
- El contrato de error del MCP ya existe: `{"error": "CÓDIGO", "message": "..."}` (TICKER_NOT_FOUND, MT5_UNAVAILABLE, INVALID_TIMEFRAME, INSUFFICIENT_DATA).
- `/chart` ya tiene el patrón interactivo de selección (activo → indicador → temporalidad) que `/apertura` debe replicar para los niveles en texto.
- Puntos de integración (PIEZA "Apertura de mercado" con `timeframe: "H4"` + `swing corto` hardcodeados):
  - `.claude/commands/martes.md` (PIEZA 1)
  - `.claude/commands/miercoles.md` (PIEZA 1)
  - `.claude/commands/jueves.md` (PIEZA 1)
  - `.claude/commands/viernes_am.md` (PIEZA 1, 3 activos)
  - `.claude/commands/lunes.md` (bloque de apertura, líneas ~116-146)
  - `domingo.md` queda **fuera** (su PIEZA 1 es noticias de fin de semana).

---

## Componentes

### Nuevo: `.claude/commands/apertura.md`

Comando interactivo reusable. Estructura por pasos (estilo `/chart`):

- **PASO 1 — Activos del día**: leer `config/agenda_semanal.json` + `config/activos.json`, proponer los 2-3 activos rotados de hoy y preguntar: *"Estos son los activos de hoy: [...]. ¿Confirmas, cambias o agregas alguno?"* (rotación + override). Normalizar al `ticker_mt5` con `config/activos.json`.
- **PASO 2 — Por cada activo (temporalidad)**:
  ```
  ¿Qué temporalidad para [ACTIVO]?
  1. 15M — scalper / muy rápida
  2. 1H — intradía corto
  3. 4H — intradía / swing corto
  4. 1D — lectura general
  ```
  Mapear a timeframe MT5: 15M→`M15`, 1H→`H1`, 4H→`H4`, 1D→`D1`.
- **PASO 3 — Por cada activo (indicador)**:
  ```
  ¿Qué indicador en la lectura de [ACTIVO]?
  1. RSI (sobrecompra/sobreventa)
  2. ATR (volatilidad — útil en USD/CLP)
  3. Limpio (solo niveles, sin indicador)
  — Próximamente (requiere ampliar el MCP): MACD · SMA 50+200 · Bollinger
  ```
  Si el director elige uno "próximamente" → responder *"Ese indicador aún no está en el MCP. Por ahora elige RSI, ATR o Limpio."* y re-preguntar (no fallar).
- **PASO 4 — Datos técnicos**: por activo, llamar `mcp__market-data__get_asset_levels {"ticker": "[TICKER_MT5]", "timeframe": "[MAPEADO]"}`. Si devuelve `"error"` → mostrar `⚠️ [message] — Verificar que MT5 esté abierto` y **omitir ese activo** (no abortar toda la apertura).
- **PASO 5 — Render del mensaje** (sección siguiente) + aprobación + guardado.

### Modificado: `templates/apertura_mercado.txt`

- Reemplazar la línea fija de operativa por placeholder `{{lectura_temporalidad}}`.
- Agregar línea opcional `{{lectura_indicador}}` (vacía si "Limpio").
- Quitar cualquier rastro hardcodeado de "swing corto" / "operativa".

### Modificados: comandos de día

`martes.md`, `miercoles.md`, `jueves.md`, `viernes_am.md` y el bloque de `lunes.md`: su PIEZA 1 deja de hardcodear `timeframe: "H4"` + `swing corto` y **delega en la lógica de `/apertura`** (referenciando sus PASOS para no duplicar). El resto de las piezas de cada día (dato macro, encuesta, etc.) **no se tocan**.

---

## Mensaje sin "enfoque de señal" + etiqueta dinámica neutral

La línea fija `_Operativa intradía / swing corto_` se reemplaza por una etiqueta **educativa** derivada de la temporalidad elegida — describe el **marco de lectura**, no una operativa recomendada:

| Temporalidad | `{{lectura_temporalidad}}` |
|---|---|
| 15M | `_Lectura en 15M — marco scalper (movimientos rápidos del día)_` |
| 1H | `_Lectura en 1H — marco intradía corto_` |
| 4H | `_Lectura en 4H — marco intradía / swing corto_` |
| 1D | `_Lectura en 1D — lectura general del activo_` |

Cumple la regla de `CLAUDE.md` (siempre indicar temporalidad + qué permite) sin convertir los niveles en señal. El bloque de cierre con escenarios 🟢/🟡/🔴 y la dirección explícita (`*Alcista*`/`*Bajista*`) **se mantienen** — eso es lectura de escenarios, no una señal operativa con entrada/TP/SL.

### Lectura del indicador en texto (`{{lectura_indicador}}`)

- **RSI** → `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]`.
- **ATR** → `📐 ATR [TF]: [atr_14] — volatilidad [alta/normal] (rango esperado del marco)`.
- **Limpio** → sin línea (placeholder vacío).

Decimales: respetar el campo `digits` de `config/activos.json` por activo (regla MT5 de `CLAUDE.md`).

---

## Manejo de errores

| Situación | Comportamiento |
|-----------|----------------|
| `get_asset_levels` → `{"error": ...}` | Mostrar `⚠️ [message] — Verificar que MT5 esté abierto` y **omitir ese activo** (seguir con el resto). |
| Indicador "próximamente" (MACD/SMA/Bollinger) | "Aún no está en el MCP, elige RSI/ATR/Limpio" + re-preguntar. |
| Ticker fuera de catálogo | Mostrar lista de activos válidos de `config/activos.json` y re-preguntar. |
| Timeframe inválido | No debería ocurrir (selección guiada 1-4); si pasa, re-preguntar. |

---

## Flujo de aprobación → WhatsApp

Sin cambios respecto al flujo estándar del proyecto:
1. `/apertura` genera el mensaje por activo.
2. Muestra al director: *"¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?"*
3. Al aprobar → guardar en `data/mensajes/YYYY-MM-DD_HH-MM_niveles.txt` (tipo `niveles`) y mostrar texto listo para copiar.
4. Nada se envía sin aprobación explícita.

---

## Verificación (fase apply)

- Correr `/apertura` con 2 activos en **temporalidades distintas** (ej. Oro 4H, WTI 15M) e indicadores distintos (RSI y ATR).
- Confirmar que el texto generado:
  - **No** contiene "señal", ni `_Operativa intradía / swing corto_` hardcodeado.
  - La `{{lectura_temporalidad}}` coincide con la temporalidad elegida por activo.
  - La `{{lectura_indicador}}` refleja el valor real (`rsi_14`/`atr_14`) con los decimales del activo.
- Elegir un indicador "próximamente" (MACD) → confirmar que re-pregunta sin fallar.
- Provocar error MT5 (cerrar MT5) → confirmar que omite el activo con el aviso y no aborta toda la apertura.
- Invocar un comando de día (ej. `/martes`) → confirmar que su PIEZA 1 ahora pregunta en vez de asumir H4.

---

## Fuera de alcance

- Agregar MACD/SMA/Bollinger al MCP `market-data` (el director lo hará después; el selector ya los deja preparados como "próximamente").
- Generación de chart adjunto dentro de `/apertura` (se mantiene `/chart` por separado; la apertura es lectura en texto).
- Conexión WhatsApp/Evolution API.
- `domingo.md` (no tiene apertura de niveles).

---

## Plan de implementación (fase apply)

1. Crear `.claude/commands/apertura.md` con los 5 PASOS (selección interactiva + render + aprobación).
2. Actualizar `templates/apertura_mercado.txt` (placeholders `{{lectura_temporalidad}}` y `{{lectura_indicador}}`, quitar "swing corto" fijo).
3. Reemplazar la PIEZA 1 de `martes.md`, `miercoles.md`, `jueves.md`, `viernes_am.md` y el bloque de apertura de `lunes.md` para delegar en `/apertura`.
4. Actualizar `CLAUDE.md` (tabla de slash commands → agregar `/apertura`; estructura diaria → reflejar selección interactiva).
5. Verificación manual según la sección anterior.
