Genera el paquete completo del lunes pieza por pieza para aprobación.

## Contexto
Hoy es lunes. Ejecuta cada pieza en orden, mostrándola al director para aprobación antes de continuar con la siguiente.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.

---

## PIEZA 1 — Resumen semanal del calendario económico

Obtén el calendario económico de toda esta semana:
- Obtén con `WebSearch` sobre investing.com los datos de **alto impacto** de la semana (próximos 7 días; Chile, EE.UU., Zona Euro, China). Convierte las horas a Chile (CLT/CLST).
- Si no encuentras eventos de alto impacto para la semana → informar al director y DETENER el comando.

Lista cada dato con:
- Día y hora en hora Chile (CLT/CLST)
- Indicador (IPC, PMI, NFP, tasas, etc.)
- País
- Impacto posible en nuestros activos (USD/CLP, Oro, WTI, US100, US500, US30)

Marca con 🔴 los días de alta volatilidad (NFP, decisiones de tasas, IPC EE.UU.).

Formato WhatsApp:
```
📅 *SEMANA DEL [FECHA]*
━━━━━━━━━━━━━━━━━━━
📌 Calendario de la semana

[Lunes] [Hora CLT] • [Dato] ([País]) → impacta [activo]
[Martes] ...
🔴 [Viernes] • NFP / Decisión tasas → ALTA VOLATILIDAD
━━━━━━━━━━━━━━━━━━━
_Los horarios son en hora Chile (CLT/CLST)_
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart MT5? ¿Enviar al grupo WhatsApp?**
Si aprueba envío WhatsApp: llama al MCP WhatsApp (mcp__whatsapp__send_message) con el texto.
Si MCP WhatsApp no disponible: muestra el texto listo para copiar y avisa.

---

## PIEZA 2 — Earnings de la semana

Ejecuta la lógica de /earnings:
- Con `WebSearch` busca el calendario de earnings de las 12 acciones del catálogo para esta semana (investing.com + fuentes oficiales de cada empresa). Confirma fechas/horas.

Por empresa que reporta esta semana, incluye:
- Día y hora Chile (BMO=antes de apertura, AMC=después del cierre)
- EPS esperado e ingresos esperados
- Foco del mercado
- Conexión con su índice (US100 para tech, US30 para bancario/industrial)

Si ninguna reporta esta semana, dilo y menciona el próximo earning relevante.

Formato WhatsApp:
```
📊 *EARNINGS DE LA SEMANA*
━━━━━━━━━━━━━━━━━━━
💼 Empresas que reportan:

🍎 *#AAPL* — [Día] [Hora CLT] (BMO/AMC)
• EPS esperado: $X.XX
• Foco: [qué mira el mercado]
• Afecta: US100

[Repetir por cada empresa]
━━━━━━━━━━━━━━━━━━━
_Los earnings pueden mover fuerte el activo y su índice_
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 3 — Concepto de la semana

Ejecuta la lógica de /concepto:
- Analiza los datos publicados esta semana y los activos que se cubren.
- Sugiere 3 conceptos educativos relevantes con "por qué" conectado a algo real.
- El director elige uno.

Tipos de concepto: macro (IPC, PMI, tasas) / técnico (RSI, MACD, ATR, medias) / conceptual (tendencia, rango, canal).

Genera el mensaje con esta estructura:
```
📚 *CONCEPTO DE LA SEMANA*
━━━━━━━━━━━━━━━━━━━
🎯 *[Nombre del concepto]*

¿Qué es?
[Explicación simple, 2 líneas máximo]

¿Para qué sirve?
[Utilidad práctica, 1-2 líneas]

Ejemplo real:
[Algo que pasó esta semana o que aplica a nuestros activos]

Cómo lo usamos:
[Cómo aplicarlo al seguimiento del mercado]

💡 Esta semana presta atención a [activo] porque [conexión con el concepto]
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart (ej: RSI en gráfico)? ¿Enviar al grupo?**

---

## PIEZA 4 — Apertura de mercado

Ejecuta `/apertura` (ver `.claude/commands/apertura.md`).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**

---

## PIEZA 5 — Encuesta de tendencia

Genera la encuesta del lunes (tipo: tendencia AM).

Elige el activo principal del día. Genera 2 bloques consecutivos:

**Bloque A — Contexto previo** (para que el cliente vote con información):
```
🎯 *ANÁLISIS RÁPIDO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con lo más relevante del activo hoy: precio, sesgo, dato clave]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta**:
```
📊 *ENCUESTA DEL DÍA*

¿Cuál creen que será la tendencia del *[activo]* hoy?
Voten y veamos si acertamos 👇

📈 Alcista
📉 Bajista
➡️ Lateral
```

**→ Muestra al director ambos bloques. Pregunta: ¿Apruebas? ¿Enviar al grupo?**

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar RSI + MACD + ATR en el mismo mensaje).
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar + ruta de imagen si hay chart.
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar.
