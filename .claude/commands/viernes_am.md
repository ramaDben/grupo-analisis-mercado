Genera la operativa de la mañana del viernes pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. Los datos técnicos se obtienen via `mcp__reporte-flash__analyze_ticker` en cada pieza.
3. **NOTA VIERNES**: Los viernes cubrir 3 activos (en vez de 2). El primer viernes del mes publicación de NFP (Non-Farm Payrolls) — si es hoy, destacarlo especialmente.

---

## PIEZA 1 — Apertura de mercado (3 activos el viernes)

Para los 3 activos del día (rotar: USD/CLP, Oro, WTI, US100, US500, US30):
- Llama `mcp__reporte-flash__analyze_ticker` con `{"ticker": "[TICKER_MT5]", "timeframe": "H4"}` para cada uno
- Extrae: precio actual, soportes, resistencias, sesgo, RSI, ATR del resultado
- Fallback: web search para precio actual + análisis manual con drivers de `config/drivers.json`

Genera un mensaje por activo:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — VIERNES [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en 4H
_Operativa intradía / swing corto_

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]

🔎 ¿Qué lo mueve hoy?
[Drivers en 2-3 líneas simples]

━━━━━━━━━━━━━━━━━━━
🟢 Sobre [R1] → fuerza compradora
🟡 Entre [S1] y [R1] → esperar confirmación
🔴 Bajo [S1] → presión vendedora
━━━━━━━━━━━━━━━━━━━
_Niveles en 4H — operativa intradía/swing corto_
```

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 2 — Dato macro del día

Verifica si hoy es el **primer viernes del mes** (= NFP day).

**Si es NFP day**: Genera este mensaje especial ANTES de la lista del calendario:
```
⚠️ *HOY ES DÍA DE NFP*
━━━━━━━━━━━━━━━━━━━
Non-Farm Payrolls — el dato de empleo más importante de EE.UU.

🕐 Sale hoy a las 9:30 CLT

¿Por qué importa?
El NFP mide cuántos trabajos se crearon en EE.UU. el mes pasado.
Si sale fuerte → la Fed puede no bajar tasas → DXY sube → Oro puede bajar, USD/CLP puede subir.
Si sale débil → la Fed podría recortar → DXY cae → Oro puede subir.

📊 Anterior: [X]K | Consenso: [Y]K
━━━━━━━━━━━━━━━━━━━
```

**Independientemente**, obtén el calendario completo de hoy:
- **Preferencia**: Llama `mcp__reporte-flash__get_economic_calendar` con `{"days_ahead": 0, "min_impact": "medium"}` (Chile, EE.UU., Zona Euro, China; impacto medio y alto).
- **Fallback**: Web search "calendario económico hoy [fecha] investing.com".

Lista numerada. Director elige cuál(es) desarrollar.

Genera el mensaje WhatsApp estándar para el dato elegido:
```
📅 *DATO MACRO — [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es? [1-2 líneas]
🕐 Sale hoy a las [Hora CLT]
📊 Anterior: [X] | Esperado: [Y]
🎯 Escenarios: [mejor/peor/en línea]
👀 Activos a observar: [lista]
━━━━━━━━━━━━━━━━━━━
```

**→ ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de precio de apertura del lunes

El viernes la encuesta pregunta por el precio de APERTURA DEL LUNES.

Genera 2 bloques:

**Bloque A — Contexto previo** (¿qué dejó la semana para el lunes?):
```
🎯 *CIERRE DE SEMANA — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas: qué pasó esta semana con el activo, dato clave del viernes, qué viene el lunes]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de precio apertura lunes**:
```
📊 *ENCUESTA DE CIERRE*
━━━━━━━━━━━━━━━━━━━
¿A qué precio crees que abrirá *[activo]* el lunes?

💬 Comenta tu precio abajo 👇

(Precio actual del viernes: [precio])
━━━━━━━━━━━━━━━━━━━
```

**→ ¿Apruebas? ¿Enviar al grupo?**

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso.
- Los viernes 3 activos (no 2).
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar.
