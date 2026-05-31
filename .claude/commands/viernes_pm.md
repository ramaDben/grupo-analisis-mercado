Genera el cierre semanal del viernes por la tarde para aprobación.

Este comando se ejecuta por la tarde (después del cierre de mercados en NY) para cerrar la semana del grupo.

## SETUP
Hoy es viernes por la tarde. El mercado de EE.UU. cerró. Es momento del resumen semanal.

---

## PIEZA ÚNICA — Cierre semanal

Recopila qué pasó esta semana con nuestros activos:
- **Preferencia**: Llama `mcp__reporte-flash__get_market_news` con `{"category": "general", "min_hours_old": 120}` para obtener el resumen de eventos y movimientos de la semana en forex/commodities e índices.
- **Complemento**: Llama `mcp__reporte-flash__analyze_ticker` para cada activo principal y obtén la variación semanal.
- **Fallback** (si MCP no responde): Usa web search buscando "resumen semanal mercados [semana actual]" + variaciones individuales de cada activo.

Estructura el mensaje así:

```
📊 *CIERRE SEMANAL — [FECHA]*
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
