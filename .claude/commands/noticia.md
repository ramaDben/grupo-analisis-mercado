Busca noticias relevantes del mercado y genera el mensaje WhatsApp de la que elija el director.

## PASO 1: Buscar noticias relevantes (WebSearch + fuentes oficiales)

**Fuente de calendario**: si la noticia requiere un dato del calendario, consulta primero `obtener_calendario_macro` (MT5 nativo, hora del servidor sin conversión). Solo si devuelve error, cae a WebSearch investing.com.

Busca con la herramienta `WebSearch` noticias recientes que impacten nuestros activos:
- Fuentes: **investing.com + fuentes oficiales** (Fed, BoJ, BCCh, OPEP+, EIA, MOF Japón, BLS).
- **Frescura**: prioriza noticias de las últimas ~4 a 24 h; descarta lo antiguo.
- Lanza una búsqueda por cada nivel de prioridad hasta reunir 3-5 noticias relevantes.

**Activos a cubrir**:
- Forex/commodities: USD/CLP, USD/JPY, Oro (XAU/USD), WTI (Petróleo)
- Índices: US100 (Nasdaq), US500 (S&P 500), US30 (Dow Jones)
- Acciones: #AAPL, #MSFT, #NVDA, #AMZN, #JPM, #BAC, #GS, #MS, #BA, #CAT, #GE, #DE

**Orden de prioridad para filtrar**:
1. Bancos centrales (Fed, BoJ, BCCh, BCE: decisiones de tasas, discursos)
2. Datos macro sorpresivos (IPC, NFP, PCE, PMI fuera de consenso)
3. Geopolítica (tensiones que afecten commodities)
4. Earnings tech (Nvidia, Apple, Microsoft, Amazon)
5. OPEP+ (decisiones de producción que afecten WTI)
6. Flujos de capital o movimientos de divisa relevantes

## PASO 2: Presentar 3-5 opciones al director

Lista las opciones ETIQUETADAS por activo y sector:

```
📰 Noticias relevantes: [FECHA/HORA CLT]

1. 💻 *Nvidia anuncia nuevo chip de AI*
   Afecta: #NVDA, US100, sector tech

2. 🏦 *Fed: Powell habla hoy a las 14:00 CLT*
   Afecta: USD/CLP, Oro, US100, US500, US30

3. ⛽ *OPEP+ analiza recorte adicional de producción*
   Afecta: WTI

4. ✈️ *Boeing recibe pedido récord de 200 aviones*
   Afecta: #BA, US30, sector industrial

5. 🇯🇵 *Banco de Japón / MOF: Declaraciones sobre tasas e inflación*
   Afecta: USD/JPY, Bonos globales

¿Cuál quieres desarrollar? (número)
```

## PASO 3: Generar mensaje WhatsApp

**Regla de traducción**: todo indicador o dato macro mencionado se nombra en **español**, con la sigla original entre paréntesis una sola vez.

**Bloque "🔤 Diccionario rápido"**: si la noticia contiene siglas/abreviaturas macro (NFP, PMI, PCE, IPC, ISM…), agrega antes del último separador una línea explicativa por sigla en voz novata, tomada de `data/glosario_siglas.json`.

**Para acciones individuales** (ej: #NVDA):
```
💻 *[EMPRESA]: [TÍTULO NOTICIA]*
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
🔤 Diccionario rápido (solo si hay siglas)
• [Sigla]: [explicación de 1 línea en español, voz novata]
━━━━━━━━━━━━━━━━━━━
```

**Para forex/commodity/índice**:
```
[EMOJI] *[ACTIVO]: [TÍTULO NOTICIA]*
━━━━━━━━━━━━━━━━━━━
¿Qué pasó?
[2-3 líneas simples]

¿Por qué importa para [activo]?
[Cómo impacta según sus drivers]

[Si hay niveles técnicos relevantes, mencionarlos brevemente con formato exacto de decimales]
━━━━━━━━━━━━━━━━━━━
🔤 Diccionario rápido (solo si hay siglas)
• [Sigla]: [explicación de 1 línea en español, voz novata]
━━━━━━━━━━━━━━━━━━━
```

## PASO 4: Aprobación y envío
Pregunta al director: "¿Apruebas? ¿Enviar al grupo WhatsApp?"
Al aprobar, muestra el texto listo para copiar.

## REGLAS
- Cero guiones largos (`—` y `–`) en todo texto de WhatsApp.
- Formato exacto de decimales según `config/activos.json` (USD/JPY: 3 decimales, USD/CLP: 2 decimales).
- Lenguaje cliente: claro, accesible para novatos y accionable para traders.
