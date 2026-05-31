Genera la operativa diaria del martes pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. Los datos técnicos se obtienen via `mcp__reporte-flash__analyze_ticker` en cada pieza.

---

## PIEZA 1 — Apertura de mercado

Para cada activo del día:
- Llama `mcp__reporte-flash__analyze_ticker` con `{"ticker": "[TICKER_MT5]", "timeframe": "H4"}`
- Extrae: precio actual, soportes, resistencias, sesgo, RSI, ATR del resultado
- Fallback: web search para precio actual + análisis manual con drivers de `config/drivers.json`

Genera un mensaje por activo:

```
📊 *APERTURA DE MERCADO — MARTES [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en 4H
_Operativa intradía / swing corto_

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]
• Sesgo: [alcista/bajista/lateral]

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]
━━━━━━━━━━━━━━━━━━━
_Niveles en 4H — operativa intradía/swing corto_
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?**
Si aprueba envío: llama MCP WhatsApp. Si no disponible: muestra texto listo para copiar + ruta imagen.

---

## PIEZA 2 — Dato macro del día

Ejecuta la lógica de /dato_macro:
- **Preferencia**: Llama `mcp__reporte-flash__get_economic_calendar` con `{"days_ahead": 0, "min_impact": "medium"}` para obtener el calendario de hoy (Chile, EE.UU., Zona Euro, China; impacto medio y alto).
- **Fallback**: Usa web search buscando "calendario económico hoy [fecha] investing.com".

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
• Si sale mejor → [reacción probable en activos]
• Si sale peor → [reacción probable en activos]
• En línea → [reacción probable]

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
