Lista todos los datos económicos del día y genera el mensaje WhatsApp del que elija el director.

## PASO 1 — Obtener el calendario de hoy (WebSearch sobre investing.com)

Obtén el calendario económico de HOY con la herramienta `WebSearch` (ya no se usa el MCP):

1. Lanza una búsqueda con `WebSearch`, query base:
   `investing.com calendario económico hoy [FECHA] Chile Estados Unidos "Zona Euro" China impacto alto`
   - Países objetivo: **Chile (CL), EE.UU. (US), Zona Euro (EU), China (CN)**.
   - Impacto: **medio y alto** (★★ / ★★★).
2. Si necesitas confirmar horas exactas, usa `WebFetch` sobre `https://es.investing.com/economic-calendar/`. Si la página no renderiza la tabla (es JS-pesada), apóyate en los resultados de `WebSearch` y en **fuentes oficiales** para datos de alto impacto (BCCh, Fed, Eurostat, BLS).
3. **Conversión de hora**: identifica la zona horaria de origen de cada dato y conviértela a **hora Chile (CLT/CLST)**. En eventos de alto impacto (Fed, BCCh, NFP) verifica la hora contra la fuente oficial.

**Contrato sin-resultados**: si la búsqueda no devuelve eventos de impacto medio/alto para hoy → muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN. En fin de semana o feriado es comportamiento esperado.

## PASO 2 — Presentar lista al director

Muestra una lista numerada con los datos del día, ordenados por hora Chile:

```
📅 Datos económicos de hoy — [FECHA]

1. 🔴 [Hora CLT] — [Indicador] ([País], ★★★) | Prev: X | Esp: Y
2. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y
3. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y
...

¿Cuál(es) quieres desarrollar? (escribe el número o "1,3" para varios)
```

Iconos por importancia: 🔴 = 3 estrellas (alto impacto) | 🟡 = 2 estrellas (moderado)

## PASO 3 — Generar mensaje WhatsApp por dato elegido

Por cada dato que elija el director, genera:

**Modo anticipación** (dato aún no ha salido):
```
📅 *DATO MACRO — [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es?
[Explicación simple en 1-2 líneas. Sin tecnicismos.]

🕐 Sale hoy a las [Hora CLT]

📊 Qué se espera:
• Anterior: [valor]
• Consenso del mercado: [valor esperado]

🎯 Escenarios:
• ✅ Sale mejor de lo esperado → [reacción probable en activos, 1 línea]
• ❌ Sale peor de lo esperado → [reacción probable, 1 línea]
• ➡️ En línea con lo esperado → [reacción, 1 línea]

👀 Activos a observar: [lista de activos impactados]
━━━━━━━━━━━━━━━━━━━
```

**Modo resultado** (dato ya publicó, tiene valor "actual"):
```
📊 *[INDICADOR] — Resultado*
━━━━━━━━━━━━━━━━━━━
Salió: *[valor actual]*
Esperado: [valor consenso] | Anterior: [valor previo]

[Sorpresa positiva/negativa/en línea con lo esperado]

¿Cómo reaccionó el mercado?
[1-2 líneas simples de lo que se vio]

[Si aplica: conexión con camino a decisión de tasas — ej: "Este dato confirma/complica el escenario de recorte de la Fed"]
━━━━━━━━━━━━━━━━━━━
```

## PASO 4 — Aprobación y envío

Pregunta al director: "¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp (mcp__whatsapp__send_message).
Si MCP no disponible: muestra el texto listo para copiar.

## PASO 5 — Encadenar encuesta post-evento (reactivo)

Después de que el director apruebe y envíe el dato, registrar el evento y ofrecer la encuesta pedagógica.

1. Escribir/actualizar `data/ultimo_evento.json` con el dato recién enviado:
```json
{
  "tipo": "noticia_macro",
  "activo": "[ticker del activo más impactado, ej: USDCLP]",
  "evento": "[nombre del indicador, ej: IPC USA mayo]",
  "dato_real": "[valor actual si ya salió, o null en modo anticipación]",
  "dato_esperado": "[consenso]",
  "timestamp": "[datetime actual ISO]"
}
```
2. Preguntar al director:
   > "📊 Acabas de enviar *[evento]*. ¿Lanzo la encuesta post-evento para que el grupo razone qué debería pasar con *[activo]*? (s/n)"
3. Si responde que sí → ejecutar el flujo de `/encuesta post_evento [activo] "[descripción del evento]"` (PASO 3 tipo `post_evento` de `encuesta.md`): genera las 3 opciones causa-efecto y guarda en `data/historial_encuestas.json`.
4. Si responde que no → terminar sin generar encuesta.

**Solo aplica en modo resultado o cuando el dato ya tiene dirección clara.** En modo anticipación pura (dato aún no sale), ofrecerla igual pero aclarando que es para que el grupo anticipe el escenario.

## REGLAS
- Sin límite de veces al día (cada dato relevante merece su propio mensaje).
- Hora siempre en hora Chile (CLT/CLST).
- Lenguaje simple: el cliente debe entender qué mide el indicador en 10 segundos.
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
