Lista todos los datos económicos del día y genera el mensaje WhatsApp del que elija el director.

## PASO 1 — Obtener la hora actual de Chile y el calendario de hoy

**1A — Hora actual Chile (OBLIGATORIO, hacer PRIMERO)**:
Obtén el timestamp actual de Chile con el **reloj del sistema** (regla canónica de CLAUDE.md, NUNCA con `WebSearch`):
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
([System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)).ToString('yyyy-MM-dd HH:mm')
```
Guarda la hora como `hora_actual_chile` (ej: `09:47`) y la fecha como `[FECHA]`. Lo necesitas para marcar eventos pasados/futuros en PASO 2. Maneja CLT/CLST automáticamente.

**1B — Calendario económico**:
Obtén el calendario de HOY con `WebSearch` (ya no se usa el MCP):

1. Lanza una búsqueda con `WebSearch`, query base:
   `investing.com calendario económico hoy [FECHA] Chile Estados Unidos "Zona Euro" China impacto alto`
   - Países objetivo: **Chile (CL), EE.UU. (US), Zona Euro (EU), China (CN)**.
   - Impacto: **medio y alto** (★★ / ★★★).
2. **Lectura del calendario (OBLIGATORIO, issue #46)**: usa `WebFetch` sobre `https://es.investing.com/economic-calendar/` como fuente principal para tener el panorama completo del día (no solo snippets). Si la página no renderiza la tabla (es JS-pesada), recién ahí cae al fallback: resultados de `WebSearch` + **fuentes oficiales** para datos de alto impacto (BCCh, Fed, Eurostat, BLS). El objetivo es no dejar fuera ningún dato de impacto medio/alto.
3. **Conversión de hora (DETERMINISTA, OBLIGATORIO)**: nunca conviertas "a mano" ni asumas offsets fijos (`UTC-5`, `GMT-3`) — esa asunción causa desfases de ±1h (ver issue #38). Por cada evento:
   - Toma la hora **oficial en la zona de su organismo emisor** (no la hora "ya convertida" que muestre investing.com: su zona es ambigua y variable).
   - Mapea el país a su zona de Windows: **EE.UU.** (BLS/ISM/ADP/EIA/Fed) → `Eastern Standard Time` · **Zona Euro** (Eurostat/BCE) → `W. Europe Standard Time` · **China** (NBS/Caixin) → `China Standard Time` · **Chile** (BCCh/INE) → `Pacific SA Standard Time` · **Reino Unido** (BoE) → `GMT Standard Time`.
   - Convierte con el helper (devuelve hora + etiqueta CLT/CLST ya correcta):
     ```powershell
     scripts\hora_chile.ps1 -Hora "08:15" -ZonaOrigen "Eastern Standard Time" -Fecha "[FECHA]"
     # -> "08:15 CLT"
     ```
   - En eventos de alto impacto (Fed, BCCh, NFP) verifica además la hora oficial contra la fuente del organismo.

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

**Regla de traducción (OBLIGATORIO, issue #46)**: todo indicador se nombra en **español**, con la sigla original entre paréntesis **una sola vez** (ej. "Índice de gerentes de compra manufacturero (PMI manufacturero)"). En el resto del cuerpo se usa el nombre en español; minimiza al máximo los términos en otro idioma.

**Bloque "🔤 Diccionario rápido" (OBLIGATORIO)**: por cada sigla/abreviatura que aparezca en el mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), agrega al final una línea explicativa en voz novata tomada de `data/glosario_siglas.json`. Si la sigla **no está** en el glosario, explícala al vuelo (1-2 líneas) y **añádela a `data/glosario_siglas.json`** para reutilizarla en adelante. Ninguna abreviatura puede quedar sin explicación ese día.

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
🔤 Diccionario rápido
• [Sigla]: [explicación de 1 línea en español, voz novata]
[una línea por cada sigla que aparezca en el mensaje]
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
🔤 Diccionario rápido
• [Sigla]: [explicación de 1 línea en español, voz novata]
[una línea por cada sigla que aparezca en el mensaje]
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
- Hora siempre en hora Chile (CLT/CLST).
- Lenguaje simple: el cliente debe entender qué mide el indicador en 10 segundos.
- **Indicadores en español** con la sigla original entre paréntesis una sola vez (issue #46). Minimizar términos en otro idioma en el cuerpo.
- **Diccionario rápido obligatorio**: ninguna abreviatura puede quedar sin su explicación en español ese día. Fuente canónica: `data/glosario_siglas.json` (alimentarla con siglas nuevas).
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
- **Bloque de cierre obligatorio**: todo mensaje de `/dato_macro` (ambos modos) cierra, después del último separador, con el link al calendario completo (`https://es.investing.com/economic-calendar/`) y el CTA genérico al analista designado. El link y el CTA van siempre juntos como pie del mensaje.
