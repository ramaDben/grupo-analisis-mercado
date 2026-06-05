Busca noticias relevantes del mercado y genera el mensaje WhatsApp de la que elija el director.

## PASO 1 — Buscar noticias relevantes (WebSearch + fuentes oficiales)

**Fuente de calendario**: si la noticia requiere un dato del calendario, consulta primero `obtener_calendario_macro` (MT5 nativo, hora del servidor sin conversión). Solo si devuelve `{"error": ...}`, cae a WebSearch investing.com.

Busca con la herramienta `WebSearch` noticias recientes que impacten nuestros activos (ya no se usa el MCP):

- Fuentes: **investing.com + fuentes oficiales** (Fed, BCCh, OPEP/OPEP+, EIA, BLS) para máxima atingencia y frescura.
- **Frescura**: prioriza noticias de las últimas ~4–24 h; descarta lo antiguo (revisa la fecha de cada resultado).
- Lanza una búsqueda por cada nivel de prioridad hasta reunir 3-5 noticias relevantes.

**Contrato sin-resultados**: si no hay noticias relevantes recientes para el catálogo → informa al director "📰 Sin noticias relevantes recientes" y DETÉN. En fin de semana o mercados cerrados es comportamiento esperado.

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

**Regla de traducción (OBLIGATORIO, issue #46)**: todo indicador o dato macro mencionado se nombra en **español**, con la sigla original entre paréntesis una sola vez (ej. "nóminas no agrícolas (NFP)"). Minimiza los términos en otro idioma en el cuerpo.

**Bloque "🔤 Diccionario rápido" (OBLIGATORIO cuando aparezcan siglas)**: si la noticia contiene siglas/abreviaturas macro (NFP, PMI, PCE, IPC, ISM…), agrega antes del último separador una línea explicativa por sigla en voz novata, tomada de `data/glosario_siglas.json`. Si la sigla no está en el glosario, explícala al vuelo y **añádela al JSON** para reutilizarla.

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
🔤 Diccionario rápido (solo si hay siglas)
• [Sigla]: [explicación de 1 línea en español, voz novata]
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
🔤 Diccionario rápido (solo si hay siglas)
• [Sigla]: [explicación de 1 línea en español, voz novata]
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
- **Indicadores en español** con la sigla entre paréntesis una sola vez; ninguna abreviatura macro queda sin explicación (Diccionario rápido). Fuente: `data/glosario_siglas.json` (issue #46).
- Siempre conectar acciones con su índice.
- Hora siempre en hora Chile si mencionas horarios.
