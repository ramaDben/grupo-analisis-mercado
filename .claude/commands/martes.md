Genera la operativa diaria del martes pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. Los datos técnicos se obtienen via `mcp__market-data__get_asset_levels` en cada pieza.

---

## PIEZA 1 — Apertura de mercado

Para cada activo del día:
- Llama `mcp__market-data__get_asset_levels` con `{"ticker": "[TICKER_MT5]", "timeframe": "H4"}`
- Extrae: price, s1, s2, r1, r2, rsi_14, atr_14, trend del resultado
- Si el resultado contiene `"error"`: mostrar al director "⚠️ [message] — Verificar que MT5 esté abierto." y DETENER el comando.

Genera un mensaje por activo:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — MARTES [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en 4H
_Operativa intradía / swing corto_

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [R1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [S1] y [R1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [S1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
_Niveles en 4H — operativa intradía/swing corto_
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?**
Si aprueba envío: llama MCP WhatsApp. Si no disponible: muestra texto listo para copiar + ruta imagen.

---

## PIEZA 2 — Dato macro del día

Ejecuta la lógica de /dato_macro:
- Llama `mcp__market-data__get_economic_events` con `{"days_ahead": 0, "min_impact": "medium"}` para obtener el calendario de hoy (Chile, EE.UU., Zona Euro, China; impacto medio y alto).
- Si el resultado contiene `"error"`: mostrar al director "⚠️ [message]" — si es NO_EVENTS_FOUND continuar (domingo/feriado); si es FINNHUB_UNAVAILABLE DETENER.

Lista numerada con los datos del día:
```
1. 🔴 [Hora CLT] — [Indicador] ([País], ★★★) | Prev: X | Esp: Y
2. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y
...
```

Pregunta al director: "¿Cuál(es) quieres desarrollar? (escribe el número o números separados por coma)"

Cuando el director elige, genera el mensaje WhatsApp:
```
📅 *DATO MACRO — [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es?
[Explicación simple en 1-2 líneas]

🕐 Sale hoy a las [Hora CLT]

📊 Qué se espera:
• Anterior: [valor]
• Consenso: [valor esperado]

🎯 Escenarios:
• Si sale mejor → [ACTIVO] *Alcista* 🟢 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• Si sale peor  → [ACTIVO] *Bajista* 🔴 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• En línea      → [ACTIVO] *Esperar confirmación* 🟡 → observar nivel [S1/R1] para definir sesgo

👀 Activos a observar: [lista]
━━━━━━━━━━━━━━━━━━━
```

Si el dato ya salió (tiene valor "actual"), usar modo resultado:
```
📊 Salió: [valor actual] vs Esperado: [valor] → [Sorpresa positiva/negativa/en línea]
[Cómo reaccionó el mercado en 1-2 líneas]
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de precio de apertura (martes = precio)

El martes la encuesta es de PRECIO, no tendencia.

Genera 2 bloques consecutivos:

**Bloque A — Contexto previo**:
```
🎯 *CONTEXTO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, evento relevante del día]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de precio**:
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿A qué precio crees que abrirá *[activo]* mañana?

💬 Comenta tu precio abajo 👇

(Precio actual: [precio])
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director ambos bloques. Pregunta: ¿Apruebas? ¿Enviar al grupo?**

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar en el mismo mensaje).
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar.
- **Dirección explícita**: SIEMPRE usar `*Alcista* 🟢` o `*Bajista* 🔴` en escenarios — nunca "puede subir", "podría bajar", "fuerza compradora" ni "presión vendedora".
- **Temporalidad obligatoria**: cada reacción a dato macro lleva `(impacto inmediato, ~1-2h)` o `(tendencia del día, intra-day)`. Si no hay certeza de dirección: `*Esperar confirmación* 🟡`.
