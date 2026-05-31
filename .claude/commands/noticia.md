Busca noticias relevantes del mercado y genera el mensaje WhatsApp de la que elija el director.

## PASO 1 — Buscar noticias relevantes

Busca noticias que impacten nuestros activos:
- **Preferencia**: Llama `mcp__reporte-flash__get_market_news` con `{"category": "general", "min_hours_old": 4}` para obtener noticias recientes de forex, commodities e índices.
- **Fallback** (si MCP no responde): Usa web search buscando "[fecha actual] noticias USD/CLP Oro WTI US100 US500 mercados".

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

## REGLAS
- Sin límite de veces al día.
- No repetir la misma noticia en el mismo día.
- Lenguaje simple: explicar qué hace la empresa si el cliente no lo sabe.
- Siempre conectar acciones con su índice.
- Hora siempre en hora Chile si mencionas horarios.
