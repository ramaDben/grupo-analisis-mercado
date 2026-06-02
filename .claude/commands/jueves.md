Genera la operativa diaria del jueves pieza por pieza para aprobación.

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

📊 *APERTURA DE MERCADO — JUEVES [FECHA]*
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
Si aprueba: llama MCP WhatsApp. Si no disponible: muestra texto listo para copiar + ruta imagen.

---

## PIEZA 2 — Dato macro del día

Obtén el calendario económico de hoy:
- Obtén el calendario de hoy con `WebSearch` sobre investing.com (Chile, EE.UU., Zona Euro, China; impacto medio y alto), como en el PASO 1 de `/dato_macro`. Convierte las horas a Chile (CLT/CLST).
- Si no hay eventos de impacto medio/alto hoy → continuar.

**NOTA JUEVES**: Los jueves suelen publicarse solicitudes de desempleo semanal (Jobless Claims) de EE.UU. (~9:30 CLT). Si aparece, recomendarlo al director como dato para desarrollar (afecta DXY, USD/CLP, US100, US500).

Lista numerada con los datos del día. Pregunta al director cuál(es) desarrollar.

Al generar el mensaje WhatsApp:
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

Si el dato ya tiene valor "actual" (ya salió), modo resultado:
```
📊 Salió: [valor] vs Esperado: [valor] → [Sorpresa/En línea]
[Cómo reaccionó el mercado en 1-2 líneas]
[Conexión con camino a decisión de tasas si aplica]
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de tendencia (jueves = tendencia AM)

El jueves la encuesta es de TENDENCIA.

Genera 2 bloques:

**Bloque A — Contexto previo**:
```
🎯 *ANÁLISIS RÁPIDO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, dato clave del día o de la semana]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de tendencia**:
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿Cuál creen que será la tendencia del *[activo]* hoy?

📈 Alcista
📉 Bajista
➡️ Lateral

Voten y veamos si acertamos 👇
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
