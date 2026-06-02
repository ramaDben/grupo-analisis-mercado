Genera el cierre semanal del viernes por la tarde para aprobación.

Este comando se ejecuta por la tarde (después del cierre de mercados en NY) para cerrar la semana del grupo.

## SETUP
Hoy es viernes por la tarde. El mercado de EE.UU. cerró. Es momento del resumen semanal.

---

## PIEZA ÚNICA — Cierre semanal

Recopila qué pasó esta semana con nuestros activos:
- Con `WebSearch` obtén el resumen de eventos de la semana (últimos ~5 días) sobre investing.com + fuentes oficiales.
- Llama `mcp__market-data__get_asset_levels` para cada activo principal y obtén la variación semanal (comparar price con apertura semanal).
- Si `get_asset_levels` retorna `"error"` MT5_UNAVAILABLE: mostrar "⚠️ [message]" y DETENER. Si no hay eventos de la semana: continuar con lo disponible.

Estructura el mensaje así:

```
📊 *CIERRE SEMANAL — [FECHA]*
━━━━━━━━━━━━━━━━━━━
🎯 Esta semana: [1 frase clave que resume lo más importante]
━━━━━━━━━━━━━━━━━━━

🗓️ *Qué pasó esta semana*
[Resumen en 3-4 líneas del contexto macro general: qué datos salieron, qué sorprendió, qué fue el tema central]

━━━━━━━━━━━━━━━━━━━
📈 *Cómo cerraron los activos*

🇨🇱 *USD/CLP* | [precio cierre] | [variación semana %]
[1 línea: qué lo movió esta semana]

🥇 *Oro (XAU/USD)* | $[precio] | [variación %]
[1 línea: qué lo movió esta semana]

⛽ *WTI* | $[precio] | [variación %]
[1 línea: qué lo movió esta semana]

📱 *US100* | [precio] | [variación %]
[1 línea: qué lo movió esta semana]

📊 *US500* | [precio] | [variación %]
[1 línea: qué lo movió esta semana]

🏭 *US30* | [precio] | [variación %]
[1 línea: qué lo movió esta semana]

━━━━━━━━━━━━━━━━━━━
🔮 *Qué esperar la próxima semana*
[2-3 líneas: eventos clave del calendario, decisiones pendientes, niveles a vigilar]

🟢 Escenario positivo: [qué activaría rally la próxima semana]
🟡 Escenario base: [qué se espera si no hay sorpresas]
🔴 Escenario de riesgo: [qué podría presionar a la baja]

_Que tengan buen fin de semana 📈_
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart (resumen semanal de algún activo)? ¿Enviar al grupo WhatsApp?**
Si aprueba: llama MCP WhatsApp. Si no disponible: muestra texto listo para copiar.

---

## REGLAS
- Hora en hora Chile.
- Lenguaje simple: el cliente entiende "subió 2%" mejor que tecnicismos.
- Si hay earnings importantes que salieron esta semana, mencionarlos brevemente.
- Tono positivo de cierre: la semana terminó, se vienen oportunidades.
