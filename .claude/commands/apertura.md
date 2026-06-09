Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Sin enfoque de señal.

## SETUP
1. Lee `config/agenda_semanal.json` y `config/activos.json`.
2. Los niveles (precio, T1, T2, Su1, Su2) los ingresa el director manualmente. Los indicadores (RSI/ATR/EMA/MACD/Bollinger) se obtienen vía `mcp__market-data__get_asset_levels` solo si aplica.

---

## PASO 1 — Activos del día (rotación + override)

Determina los activos rotados de hoy según `config/agenda_semanal.json` (2-3 activos; los viernes 3). Propón al director:

```
Activos sugeridos para hoy: [ACTIVO A] · [ACTIVO B] (· [ACTIVO C])
¿Confirmas, cambias o agregas alguno?
```

El director puede confirmar, reemplazar o agregar. Normaliza cada activo a su `ticker_mt5` consultando `config/activos.json`. Si un activo no está en el catálogo, muestra la lista de activos válidos y vuelve a preguntar.

---

## PASO 2 — Temporalidad por activo

Para CADA activo seleccionado, pregunta:

```
¿Qué temporalidad para [ACTIVO]?
1. 15M — scalper (minutos a 1-2 h)
2. 1H  — intradía (dentro de la jornada)
3. 4H  — swing de jornada (1-3 días)
4. 1D  — posicional (días a semanas)
```

Mapeo a timeframe MT5: 15M→`M15`, 1H→`H1`, 4H→`H4`, 1D→`D1`.

---

## PASO 3 — Indicador por activo

Para CADA activo, pregunta:

```
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI        — sobrecompra/sobreventa
2. ATR        — volatilidad del marco
3. EMA 50/100 — tendencia por medias móviles
4. MACD       — momentum y cruces
5. Bollinger  — volatilidad y bandas de precio
6. Limpio     — solo niveles, sin indicador
```

---

## PASO 4 — Precio, niveles e indicadores por activo

### 4A — Precio actual (fetch automático MT5)

Para CADA activo, llamar **una sola vez**:

```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"})
```

Guardar el resultado completo (se reutiliza en 4C). Extraer el campo `price` y mostrarlo:

```
💰 Precio actual obtenido desde MT5: [precio formateado según digits]
   ¿Correcto? (Intro para confirmar · escribe un valor para corregir)
```

El director puede confirmar con Enter o escribir un valor distinto. Formatear siempre según `digits` de `config/activos.json`.

Si el resultado contiene `"error"`:
```
⚠️ No se pudo obtener el precio desde MT5. Ingresa el precio actual manualmente:
Precio actual:
```
En ese caso pedir el valor manualmente (mismas reglas de parsing que 4B). Guardar `resultado = null` para que 4C sepa que tampoco hay indicador disponible.

⚠️ **IMPORTANTE — qué usar del resultado del MCP**: solo se extraen `price` (precio actual) y los campos de indicador (`rsi_14`, `atr_14`). Cualquier campo de soporte o resistencia que devuelva el MCP se **ignora completamente**. Los niveles del mensaje los ingresa siempre el director en PASO 4B.

### 4B — Techos y suelos (ingreso manual del director — OBLIGATORIO)

**OBLIGATORIO**: preguntar siempre al director, sin excepción, aunque el MCP haya devuelto campos de soporte/resistencia. Los niveles del mensaje son los que ingresa el director aquí.

Para CADA activo, solicitar los niveles:

```
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Techo 1 (T1):
  Techo 2 (T2):   ← opcional, escribe "–" para omitir
  Suelo 1 (Su1):
  Suelo 2 (Su2):  ← opcional, escribe "–" para omitir
```

Reglas de parsing:
- Aceptar valores con o sin `$`, coma de miles o espacios (ej: `$889.60`, `4,539.72`, `889.60`).
- Formatear según el campo `digits` del activo en `config/activos.json`. Nunca truncar ceros.
- Si T2 o Su2 se dejan en blanco o contienen `"–"` / `"-"`: omitir esas líneas del mensaje final.
- Si un valor obligatorio no es numérico: mostrar `⚠️ Valor inválido. Ingresa solo el número.` y volver a pedir ese campo.

### 4C — Indicador (reutiliza resultado de 4A)

Solo si el director eligió **RSI**, **ATR**, **EMA 50/100**, **MACD** o **Bollinger** en el PASO 3:

- Si el resultado de 4A fue exitoso: extraer del resultado según el indicador elegido:
  - RSI → `rsi_14`
  - ATR → `atr_14`
  - EMA 50/100 → `ema_50`, `ema_100`
  - MACD → `macd_line`, `macd_signal`, `macd_hist`
  - Bollinger → `bb_upper`, `bb_mid`, `bb_lower`
  **No hacer un segundo call al MCP.**
- Si el resultado de 4A fue `null` (error de MT5): mostrar:
  ```
  ⚠️ No se pudo obtener [RSI/ATR] desde MT5. ¿Qué deseas hacer?
  1. Ingresar el valor manualmente
  2. Continuar sin indicador (mensaje "Limpio")
  ```

Si el director eligió **Limpio** en PASO 3: omitir por completo.

---

## PASO 5 — Render del mensaje (por activo)

Genera un mensaje por activo. La etiqueta de marco temporal es **neutral** (lectura educativa, no operativa recomendada):

| Temporalidad | Línea `{{lectura_temporalidad}}` |
|---|---|
| 15M | `_Lectura en 15M — marco scalper (minutos a 1-2 h)_` |
| 1H  | `_Lectura en 1H — marco intradía (dentro de la jornada)_` |
| 4H  | `_Lectura en 4H — marco swing de jornada (1-3 días)_` |
| 1D  | `_Lectura en 1D — marco posicional (días a semanas)_` |

Línea `{{por_que_temporalidad}}` (justifica la TF elegida según la volatilidad del activo — OBLIGATORIA):
- Se arma combinando el campo `nota_volatilidad` del activo (en `config/activos.json`) con la TF que eligió el director.
- Formato: `💡 Por qué [TEMPORALIDAD] aquí: [explicación cliente derivada de nota_volatilidad].`
- Lenguaje novato (regla de 30 s), español chileno neutro, una sola línea. Ejemplos:
  - USD/CLP en 1H → `💡 Por qué 1H aquí: el dólar se mueve poco dentro del día, así la lectura sale más limpia y con menos ruido.`
  - WTI en 15M → `💡 Por qué 15M aquí: el petróleo se mueve fuerte y rápido, en este marco verás señales veloces pero con más ruido.`

Línea de indicador `{{lectura_indicador}}` (omitir si "Limpio"):
| Indicador | Línea generada |
|---|---|
| RSI | `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]` |
| ATR | `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco` |
| EMA 50/100 | Ver reglas abajo |
| MACD | Ver reglas abajo |
| Bollinger | `📐 Bollinger [TF]: banda alta [bb_upper] \| media [bb_mid] \| baja [bb_lower] — precio [tocando banda alta / baja / en el centro]` |
| Limpio | *(omitir línea completa)* |

**Reglas EMA 50/100:**
- Precio > ema_50 Y precio > ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio sobre ambas → *Alcista* 🟢`
- Precio < ema_50 Y precio < ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio bajo ambas → *Bajista* 🔴`
- Precio entre ema_50 y ema_100 → `📐 EMA 50 [TF]: [val] | EMA 100 [TF]: [val] — precio entre ambas → *Esperar confirmación* 🟡`

**Reglas MACD:**
- macd_hist > 0 → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — momentum *Alcista* 🟢`
- macd_hist < 0 → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — momentum *Bajista* 🔴`
- abs(macd_hist) < 0.0001 × precio → `📐 MACD [TF]: línea [val] | señal [val] | hist [val] — *Sin señal clara* 🟡`

Plantilla del mensaje:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [T1 o Su1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — [D de mes de YYYY]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en [TEMPORALIDAD]
{{lectura_temporalidad}}
{{por_que_temporalidad}}

💰 Precio actual: [precio]
• Techo más próximo: [T1]
• Techo siguiente: [T2]          ← solo si el director ingresó T2; si no, omitir esta línea
• Suelo más próximo: [Su1]
• Suelo siguiente: [Su2]         ← solo si el director ingresó Su2; si no, omitir esta línea
• Zona de interés: [Su1] – [T1]
{{lectura_indicador}}

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [T1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [Su1] y [T1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [Su1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

**Reglas de render (OBLIGATORIAS — esta plantilla es la única salida válida):**
- **Fecha** `[D de mes de YYYY]`: hora Chile, formato `2 de junio de 2026`. NUNCA con día de la semana (`martes 2 de junio`), NUNCA abreviada, NUNCA sustituida por el nombre del activo.
- **Terminología de niveles**: siempre `Techo más próximo` / `Suelo más próximo`; los segundos niveles son `Techo siguiente` / `Suelo siguiente`.
- **Orden de niveles**: primero todos los techos (más próximo → siguiente), luego todos los suelos (más próximo → siguiente), luego `Zona de interés`. La zona usa siempre los "más próximos": `[Suelo más próximo] – [Techo más próximo]`.
- **T2/Su2 opcionales**: si el director NO ingresó T2 (o Su2) en PASO 4B, se **omite por completo** esa línea (sin dejar línea en blanco).
- **Precio**: siempre `💰 Precio actual: [precio]`.
- **Indicador**: siempre `📐 [INDICADOR] [TF]:` según la tabla `{{lectura_indicador}}` arriba. Omitir si "Limpio".
- **Justificación de temporalidad**: siempre la línea `💡 Por qué [TF] aquí:` (ver `{{por_que_temporalidad}}` arriba), derivada de `nota_volatilidad` del activo. Nunca omitir ni usar la palabra "corto" sin cuantificar.

**Decimales**: respeta el campo `digits` de `config/activos.json` por activo (regla MT5 de CLAUDE.md). Nunca truncar ceros.

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
Al aprobar: construye la ruta con `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Tipo niveles -Hora [HH-MM]` y guarda ahí con Write. Muestra el texto listo para copiar. Si WhatsApp MCP no disponible: solo texto + ruta de imagen.

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar en el mismo mensaje).
- **NO es una señal**: nunca uses "operativa recomendada", "entrada", "TP/SL" en la apertura. La etiqueta temporal es marco de lectura educativo.
- **Dirección explícita** en escenarios: usa `*Alcista* 🟢` / `*Bajista* 🔴`, nunca "fuerza compradora" ni "presión vendedora".
- Si WhatsApp MCP no disponible: mostrar texto listo para copiar.

## PROHIBIDO (cierra el drift de formato — issue #35)

El mensaje de niveles tiene **una sola** forma válida (la plantilla del PASO 5). NUNCA generes estas variantes:

- ❌ `Resistencia 1/2` · `Soporte 1/2` → usa `Techo/Suelo más próximo` y `siguiente`.
- ❌ `Techo objetivo` · `Techo inmediato` · `Suelo fuerte` → usa `más próximo` / `siguiente`.
- ❌ `📊 *Precio actual*` · `📌 Precio actual` como rótulo de precio → usa `💰 Precio actual`.
- ❌ `⚠️ *RSI 1H*: ...` · `• RSI: ...` inline → usa `📐 RSI/ATR/EMA/MACD/Bollinger [TF]:` (línea `{{lectura_indicador}}`).
- ❌ Día de la semana en la fecha (`martes 2 de junio`) → usa `2 de junio de 2026`.
- ❌ Línea extra `Sesgo: ...` o `🟢 *Sesgo del día*` → el sesgo va implícito en el bloque de escenarios `🟢/🟡/🔴`.
- ❌ Bloque de escenarios con orden invertido o emoji duplicado (`🟢 Sobre X → *Alcista* 🟢 → siguiente objetivo`) → orden canónico: `🟢 *Alcista* — Precio sobre X → tendencia compradora (intra-day)`.
- ❌ `🔎 *¿Qué lo está moviendo?*` (en negrita / otra redacción) → usa `🔎 ¿Qué lo mueve hoy?` sin negrita.

Cualquier comando de día que invoque la pieza de apertura **delega 100%** en esta plantilla; no redefine formato propio de niveles.
