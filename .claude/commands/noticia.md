Busca noticias relevantes del mercado y genera el mensaje WhatsApp de la que elija el director.

## PASO 1 — Buscar noticias relevantes

Busca noticias que impacten nuestros activos:
- Llama `mcp__market-data__get_market_context` con `{"within_hours": 4, "category": "general"}` para obtener noticias recientes de forex, commodities e índices.
- Si el resultado contiene `"error"`: mostrar al director "⚠️ [message]" — si es NO_NEWS_FOUND informar y DETENER; si es FINNHUB_UNAVAILABLE DETENER.

**Activos a cubrir**:
- Forex/commodities: USD/CLP, Oro (XAU/USD), WTI (Petróleo)
- Índices: US100 (Nasdaq), US500 (S&P 500), US30 (Dow Jones)
- Acciones: #AAPL, #MSFT, #NVDA, #AMZN, #JPM, #BAC, #GS, #MS, #BA, #CAT, #GE, #DE

**Orden de prioridad para filtrar**:
1. Bancos centrales (Fed, BCCh, BCE, decisiones de tasas, discursos)
2. Datos macro sorpresivos (IPC, NFP, PCE, PMI fuera de consenso)
3. Geopolítica (tensiones, sanciones, guerras que afecten commodities)
4. Earnings tech (Nvidia, Apple, Microsoft, Amazon)
5. OPEP+ (decisiones de producción que afecten WTI)
6. Flujos de capital o movimientos de divisa relevantes

**No repetir** una noticia que ya se envió hoy (mantén contexto de la sesión actual).

## PASO 2 — Presentar 3-5 opciones al director

Lista las opciones ETIQUETADAS por activo y sector:

```
📰 Noticias relevantes — [FECHA/HORA CLT]

1. 💻 *Nvidia anuncia nuevo chip de AI*
   Afecta: #NVDA, US100, sector tech

2. 🏦 *Fed: Powell habla hoy a las 14:00 CLT*
   Afecta: USD/CLP, Oro, US100, US500, US30

3. ⛽ *OPEP+ analiza recorte adicional de producción*
   Afecta: WTI

4. ✈️ *Boeing recibe pedido récord de 200 aviones*
   Afecta: #BA, US30, sector industrial

5. 🌎 *Tensión geopolítica en Oriente Medio escala*
   Afecta: WTI, Oro

¿Cuál quieres desarrollar? (número)
```

## PASO 3 — Generar mensaje WhatsApp

Para el activo/noticia elegido:

**Para acciones individuales** (ej: #NVDA):
```
💻 *[EMPRESA] — [TÍTULO NOTICIA]*
━━━━━━━━━━━━━━━━━━━
¿Qué hace [empresa]?
[1 línea simple: qué produce/vende, para que el cliente entienda el contexto]

¿Qué pasó?
[2-3 líneas simples. Qué anunció, qué salió, qué dijo]

¿Por qué importa?
[Cómo afecta a la acción y por qué es relevante para el precio]

🔗 Conexión con el índice:
[Cómo afecta #TICKER al US100/US30 y al sector]
━━━━━━━━━━━━━━━━━━━
```

**Para forex/commodity/índice**:
```
[EMOJI] *[ACTIVO] — [TÍTULO NOTICIA]*
━━━━━━━━━━━━━━━━━━━
¿Qué pasó?
[2-3 líneas simples]

¿Por qué importa para [activo]?
[Cómo impacta según sus drivers]

[Si hay niveles técnicos relevantes, mencionarlos brevemente]
━━━━━━━━━━━━━━━━━━━
```

## PASO 4 — Aprobación y envío

Pregunta: "¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp.
Si no disponible: muestra texto listo para copiar.

## PASO 5 — Encadenar encuesta post-evento (reactivo)

Después de aprobar y enviar la noticia, registrar el evento y ofrecer la encuesta pedagógica.

1. Escribir/actualizar `data/ultimo_evento.json` con la noticia recién enviada:
```json
{
  "tipo": "noticia",
  "activo": "[ticker del activo más impactado por la noticia]",
  "evento": "[título corto de la noticia]",
  "dato_real": null,
  "dato_esperado": null,
  "timestamp": "[datetime actual ISO]"
}
```
2. Preguntar al director:
   > "📊 Acabas de enviar *[noticia]*. ¿Lanzo la encuesta post-evento para que el grupo razone qué debería pasar con *[activo]*? (s/n)"
3. Si responde que sí → ejecutar el flujo de `/encuesta post_evento [activo] "[título de la noticia]"`: genera las 3 opciones causa-efecto y guarda en `data/historial_encuestas.json`.
4. Si responde que no → terminar sin generar encuesta.

## REGLAS
- Sin límite de veces al día.
- No repetir la misma noticia en el mismo día.
- Lenguaje simple: explicar qué hace la empresa si el cliente no lo sabe.
- Siempre conectar acciones con su índice.
- Hora siempre en hora Chile si mencionas horarios.
