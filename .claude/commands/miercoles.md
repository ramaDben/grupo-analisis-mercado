Genera la operativa diaria del miércoles pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. Los datos técnicos se obtienen via `mcp__reporte-flash__analyze_ticker` en cada pieza.
3. **NOTA MIÉRCOLES**: Si hoy hay publicación de inventarios EIA de petróleo, priorizarlo en la pieza de dato macro.

---

## PIEZA 1 — Apertura de mercado

Para cada activo del día:
- Llama `mcp__reporte-flash__analyze_ticker` con `{"ticker": "[TICKER_MT5]", "timeframe": "H4"}`
- Extrae: precio actual, soportes, resistencias, sesgo, RSI, ATR del resultado
- Fallback: web search para precio actual + análisis manual con drivers de `config/drivers.json`

Genera un mensaje por activo:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — MIÉRCOLES [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en 4H
_Operativa intradía / swing corto_

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [R1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [S1] y [R1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [S1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
_Niveles en 4H — operativa intradía/swing corto_
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?**

---

## PIEZA 2 — Dato macro del día (con prioridad EIA si corresponde)

Verifica si hoy es miércoles con publicación de inventarios EIA de petróleo (normalmente cada miércoles ~10:30 CLT durante sesión NY).

**Preferencia**: Llama `mcp__reporte-flash__get_economic_calendar` con `{"days_ahead": 0, "min_impact": "medium"}` para el calendario de hoy (Chile, EE.UU., Zona Euro, China; impacto medio y alto).
**Fallback**: Usa web search buscando "calendario económico hoy [fecha] investing.com".

Lista numerada con los datos del día. Si hay EIA marcarlo con ⛽ al inicio.

Cuando el director elige el dato a desarrollar, genera:
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

Si los inventarios EIA están en el calendario, generar también este mensaje específico:
```
⛽ *INVENTARIOS EIA — Petróleo*
━━━━━━━━━━━━━━━━━━━
¿Qué mide? Cuánto petróleo tienen almacenado en EE.UU. esta semana.

🕐 Sale hoy a las ~10:30 CLT

📊 Anterior: [X] millones de barriles
• Baja → WTI *Alcista* 🟢 (impacto inmediato, ~1-2h)
• Sube → WTI *Bajista* 🔴 (impacto inmediato, ~1-2h)
• Tendencia del día: depende de la magnitud de la sorpresa y el sesgo técnico 4H

👀 Activo clave: *WTI* (Petróleo)
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart (ej: WTI si es EIA)? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de tendencia (miércoles = tendencia AM)

El miércoles la encuesta es de TENDENCIA.

Genera 2 bloques:

**Bloque A — Contexto previo**:
```
🎯 *ANÁLISIS RÁPIDO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, dato clave del día]
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
