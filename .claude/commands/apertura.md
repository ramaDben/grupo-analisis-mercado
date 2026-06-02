Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Sin enfoque de señal.

## SETUP
1. Lee `config/agenda_semanal.json` y `config/activos.json`.
2. Los datos técnicos se obtienen vía `mcp__market-data__get_asset_levels`.

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

## PASO 4 — Datos técnicos por activo

Para cada activo, llama `mcp__market-data__get_asset_levels` con `{"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"}` (el timeframe mapeado en el PASO 2).

- Extrae: `price, s1, s2, r1, r2, rsi_14, atr_14, trend`.
- Si el resultado contiene `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y **omite ese activo** (continúa con el resto; NO abortes toda la apertura).

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
