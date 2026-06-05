Lista todos los datos económicos del día y genera el mensaje WhatsApp del que elija el director.

## PASO 1 — Obtener la hora actual de Chile y el calendario de hoy

**1A — Hora actual Chile (OBLIGATORIO, hacer PRIMERO)**:
Obtén el timestamp actual de Chile con el **reloj del sistema** (regla canónica de CLAUDE.md, NUNCA con `WebSearch`):
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
([System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)).ToString('yyyy-MM-dd HH:mm')
```
Guarda la hora como `hora_actual_chile` (ej: `09:47`) y la fecha como `[FECHA]`. Lo necesitas para marcar eventos pasados/futuros en PASO 2. Maneja CLT/CLST automáticamente.

**1B — Calendario económico (MT5 nativo primero, WebSearch fallback)**:

1. **Fuente primaria — MT5 nativo**: invoca la tool MCP `obtener_calendario_macro(min_impact="medium")`.
   - Si devuelve `{"eventos": [...]}`: usa esos eventos. La hora ya viene en **hora del servidor MT5** (broker actual = hora Chile) — **no conviertas nada**.
   - Cada evento trae `nombre` (ya en español), `pais`, `divisa`, `impacto`, `hora_servidor`, `periodo`, `previo`, `forecast`, `actual`. Si trae `diccionario`, úsalo para el bloque Diccionario rápido; si trae `glosario_pendiente: true`, explica la sigla al vuelo y añádela a `data/glosario_siglas.json` por su `event_id`.
   - Si devuelve `{"eventos": []}` con `info`: es fin de semana/feriado → muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN.

2. **Fallback — WebSearch**: solo si la tool devuelve `{"error": ...}` (NO_CALENDAR_FILE / STALE_CALENDAR / BAD_CALENDAR_JSON / INVALID_IMPACT), avisa al director ("⚠️ calendario nativo MT5 no disponible, uso WebSearch") y usa el flujo WebSearch sobre investing.com:
   - Query: `investing.com calendario económico hoy [FECHA] Chile Estados Unidos "Zona Euro" China impacto alto`.
   - En este fallback (origen extranjero) sí conviertes la hora con `scripts\hora_chile.ps1` desde la zona del organismo emisor.

**Contrato sin-resultados**: si la búsqueda no devuelve eventos de impacto medio/alto para hoy → muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN. En fin de semana o feriado es comportamiento esperado.

## PASO 2 — Presentar lista al director

Muestra una lista numerada con los datos del día, ordenados por hora Chile. Para cada evento, compara su hora contra `hora_actual_chile` obtenida en PASO 1A:
- Si la hora del evento **ya pasó** → agregar `✅ YA SALIÓ`
- Si la hora del evento **aún no llegó** → agregar `🕐 PRÓXIMO`

```
📅 Datos económicos de hoy — [FECHA]

1. 🔴 [Hora CLT] — [Indicador] ([País], ★★★) | Prev: X | Esp: Y  ✅ YA SALIÓ
2. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y  🕐 PRÓXIMO
3. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y  🕐 PRÓXIMO
...

¿Cuál(es) quieres desarrollar? (escribe el número o "1,3" para varios)
```

Iconos por importancia: 🔴 = 3 estrellas (alto impacto) | 🟡 = 2 estrellas (moderado)

**Selección de modo automático**: cuando el director elija un evento marcado `✅ YA SALIÓ`, usar directamente el **Modo resultado** en PASO 3 (sin preguntar). Si elige uno `🕐 PRÓXIMO`, usar **Modo anticipación**.

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
📅 Calendario completo: https://es.investing.com/economic-calendar/
💬 ¿Quieres profundizar este tema? Escríbele a tu analista designado.
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
📅 Calendario completo: https://es.investing.com/economic-calendar/
💬 ¿Quieres profundizar este tema? Escríbele a tu analista designado.
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
- Hora: en fuente MT5 nativa, la hora es la del servidor MT5 (broker actual = hora Chile, se muestra tal cual). En fallback WebSearch, convertir a hora Chile con `scripts\hora_chile.ps1`.
- Lenguaje simple: el cliente debe entender qué mide el indicador en 10 segundos.
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
- **Bloque de cierre obligatorio**: todo mensaje de `/dato_macro` (ambos modos) cierra, después del último separador, con el link al calendario completo (`https://es.investing.com/economic-calendar/`) y el CTA genérico al analista designado. El link y el CTA van siempre juntos como pie del mensaje.
