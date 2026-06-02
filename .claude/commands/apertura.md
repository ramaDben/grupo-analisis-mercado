Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Sin enfoque de señal.

## SETUP
1. Lee `config/agenda_semanal.json` y `config/activos.json`.
2. Los niveles (precio, S1, S2, R1, R2) los ingresa el director manualmente. Los indicadores (RSI/ATR) se obtienen vía `mcp__market-data__get_asset_levels` solo si aplica.

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
1. 15M — scalper / muy rápida
2. 1H  — intradía corto
3. 4H  — intradía / swing corto
4. 1D  — lectura general
```

Mapeo a timeframe MT5: 15M→`M15`, 1H→`H1`, 4H→`H4`, 1D→`D1`.

---

## PASO 3 — Indicador por activo

Para CADA activo, pregunta:

```
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI    — sobrecompra/sobreventa
2. ATR    — volatilidad (útil en USD/CLP)
3. Limpio — solo niveles, sin indicador
— Próximamente (requiere ampliar el MCP): MACD · SMA 50+200 · Bollinger
```

Si el director elige una opción "Próximamente" (MACD/SMA/Bollinger), responde:
`Ese indicador aún no está en el MCP. Por ahora elige RSI, ATR o Limpio.` y vuelve a preguntar. No falles.

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

### 4B — Niveles S/R (ingreso manual del director)

Para CADA activo, solicitar solo los niveles de soporte y resistencia:

```
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Resistencia 1 (R1):
  Resistencia 2 (R2):   ← opcional, escribe "–" para omitir
  Soporte 1 (S1):
  Soporte 2 (S2):       ← opcional, escribe "–" para omitir
```

Reglas de parsing:
- Aceptar valores con o sin `$`, coma de miles o espacios (ej: `$889.60`, `4,539.72`, `889.60`).
- Formatear según el campo `digits` del activo en `config/activos.json`. Nunca truncar ceros.
- Si R2 o S2 se dejan en blanco o contienen `"–"` / `"-"`: omitir esas líneas del mensaje final.
- Si un valor obligatorio no es numérico: mostrar `⚠️ Valor inválido. Ingresa solo el número.` y volver a pedir ese campo.

### 4C — Indicador (reutiliza resultado de 4A)

Solo si el director eligió **RSI** o **ATR** en el PASO 3:

- Si el resultado de 4A fue exitoso: extraer `rsi_14` (RSI) o `atr_14` (ATR) de ese mismo resultado. **No hacer un segundo call al MCP.**
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
| 15M | `_Lectura en 15M — marco scalper (movimientos rápidos del día)_` |
| 1H  | `_Lectura en 1H — marco intradía corto_` |
| 4H  | `_Lectura en 4H — marco intradía / swing corto_` |
| 1D  | `_Lectura en 1D — lectura general del activo_` |

Línea de indicador `{{lectura_indicador}}` (omitir si "Limpio"):
- RSI → `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]`
- ATR → `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco`

Plantilla del mensaje:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en [TEMPORALIDAD]
{{lectura_temporalidad}}

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]
{{lectura_indicador}}

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [R1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [S1] y [R1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [S1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

**Decimales**: respeta el campo `digits` de `config/activos.json` por activo (regla MT5 de CLAUDE.md). Nunca truncar ceros.

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
Al aprobar: guarda en `data/mensajes/YYYY-MM-DD_HH-MM_niveles.txt` (usar Write) y muestra el texto listo para copiar. Si WhatsApp MCP no disponible: solo texto + ruta de imagen.

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar en el mismo mensaje).
- **NO es una señal**: nunca uses "operativa recomendada", "entrada", "TP/SL" en la apertura. La etiqueta temporal es marco de lectura educativo.
- **Dirección explícita** en escenarios: usa `*Alcista* 🟢` / `*Bajista* 🔴`, nunca "fuerza compradora" ni "presión vendedora".
- Si WhatsApp MCP no disponible: mostrar texto listo para copiar.
