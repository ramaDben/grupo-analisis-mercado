Lista todos los datos económicos del día y genera la pieza WhatsApp del que elija el director: si el dato ya publicó, una Story de marca con su pie de foto; si todavía no sale, el mensaje de anticipación completo.

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

## PASO 1C — Filtrado por país (OBLIGATORIO, antes de presentar la lista)

Aplica estos filtros al set de eventos obtenido. El filtro aplica **tanto a la lista del PASO 2 como al desarrollo del PASO 3**:

- **Zona Euro**: conservar **solo la decisión de tasas del BCE**. Descartar el resto de datos de la Zona Euro (IPC euro, PMI euro, etc.).
- **Estados Unidos**: conservar **solo eventos de 3 estrellas (★★★, alto impacto)**. Descartar los de 2★. Cada evento de EE.UU. se enmarca en la narrativa de la **decisión de tasas de la Fed** (¿el dato empuja las tasas al alza o a la baja?) y se traduce a impacto en **índices bursátiles** (US100 / US30 suben o bajan).
- **Chile**: conservar **solo la balanza comercial**. Descartar exportaciones de cobre, producción manufacturera y ventas minoristas.
- **Otros países** (ej. China): sin cambios respecto al filtro de impacto medio/alto ya aplicado.

Si tras el filtrado no queda ningún evento → muestra "📅 Sin datos macro relevantes para hoy (según filtros de cobertura)" y DETÉN.

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

**Bloque "🔤 Diccionario rápido" (OBLIGATORIO en Modo anticipación)**: por cada sigla/abreviatura que aparezca en el mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), agrega al final una línea explicativa en voz novata tomada de `data/glosario_siglas.json`. Si la sigla **no está** en el glosario, explícala al vuelo (1-2 líneas) y **añádela a `data/glosario_siglas.json`** para reutilizarla en adelante. Ninguna abreviatura puede quedar sin explicación ese día.

En **Modo resultado** el mensaje es el pie de una imagen y no hay espacio para el bloque: la sigla se explica **en línea**, dentro de la frase (ver "Reglas del modo resultado"). El deber de no dejar abreviaturas sin explicar se mantiene; cambia el dónde, no el si. Alimentar `data/glosario_siglas.json` con siglas nuevas sigue siendo obligatorio en ambos modos.

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
⏱️ Temporalidad del impacto: [scalper (minutos a 1-2 h) / intradía (la jornada) / swing de jornada (1-3 días) / posicional (días a semanas)]
━━━━━━━━━━━━━━━━━━━
🔤 Diccionario rápido
• [Sigla]: [explicación de 1 línea en español, voz novata]
[una línea por cada sigla que aparezca en el mensaje]
━━━━━━━━━━━━━━━━━━━
📅 Calendario completo: https://es.investing.com/economic-calendar/
💬 ¿Quieres profundizar este tema? Escríbele a tu analista designado.
```

**Modo resultado** (dato ya publicó, tiene valor "actual" — **la pieza es la Story, este texto es su pie de foto**):

En este modo el entregable al grupo son **dos cosas que viajan juntas**: la imagen generada por
`/story dato_macro` (que lleva el veredicto, las cifras, el "qué significa", el gráfico de la serie
y el impacto por activo) y este pie corto. **El desarrollo largo ya no se manda como texto** — está
en la imagen, y repetirlo obliga al cliente a leer dos veces lo mismo.

1. **Generar primero la Story** con la ruta `dato_macro` de `/story` (ver `.claude/commands/story.md`).
   El pie se escribe **después**, a partir del mismo payload, para que veredicto y cifras coincidan
   exactamente entre imagen y texto.
2. **Escribir el pie** con esta plantilla:

```
📊 *DATO MACRO · [PAÍS]*
🕐 Publicado hoy [Hora CLT]

🎯 *[Indicador en español (SIGLA)] de [periodo]: [actual]*
[🔴/🟢/🟡] *[PEOR / MEJOR / EN LÍNEA] de lo esperado* — el mercado calculaba [esperado]
⚡ [1 línea: qué implica y hacia dónde empuja — dirección explícita, regla de oro]

⏱️ Impacto [scalper (minutos a 1-2 h) / intradía (dentro de la jornada) / swing de jornada (1-3 días) / posicional (días a semanas)]
━━━━━━━━━━━━━━━━━━━
📅 Calendario completo del día: https://es.investing.com/economic-calendar/
💬 ¿Cómo aprovechar este dato en tus operaciones? Escríbele a tu analista designado.
```

**Reglas del modo resultado**:
- **Por qué el pie repite el veredicto que ya está en la imagen**: no es duplicación ociosa. Es lo
  que se ve en la **notificación** de WhatsApp antes de abrir el chat, y lo único legible si el
  cliente no descarga la imagen o tiene los datos justos. Un adjunto sin pie llega mudo.
- **Above the fold**: con imagen adjunta WhatsApp corta el pie **antes** que en un mensaje suelto —
  el veredicto completo va en las primeras 3 líneas, nunca el contexto.
- **Emoji del veredicto**: 🔴 peor · 🟢 mejor · 🟡 en línea. Es frente al **consenso**, no una
  dirección de mercado — un dato "mejor" puede ser bajista para un activo, y esa distinción la
  desarrolla la imagen en su bloque de impacto por activo.
- **Siglas explicadas en línea**: en este modo no va el bloque "🔤 Diccionario rápido" (no cabe en
  un pie y la imagen tampoco lo lleva). La regla del issue #46 se cumple explicando la sigla dentro
  de la propia frase, una sola vez: "vacantes de empleo (JOLTS)", "Reserva Federal (Fed)". Si el
  pie necesitara más de dos siglas, es señal de que está mal redactado — reescríbelo.
- **Temporalidad**: obligatoria acá porque **no** está en la imagen (se sacó por desborde del
  lienzo vertical). Es la única pieza del desarrollo largo que sobrevive en el texto.
- **Qué se dejó de mandar**: sub-lecturas, "🧠 ¿Qué significa esto?", "⚠️ PERO ojo con el detalle",
  "💡 Impacto esperado por activo" y el diccionario. Todo eso vive en la Story. Las plantillas
  anteriores (la breve del issue #93 y la larga que la sucedió) quedan en el historial git por si
  se decide volver a ellas.
- **Modo anticipación no cambia**: `/story dato_macro` cubre solo datos ya publicados —la pieza se
  organiza alrededor del veredicto y un dato que no ha salido no tiene veredicto—, así que ahí el
  mensaje completo sigue siendo el entregable, con su diccionario y todo.

## PASO 4 — Aprobación y envío

Pregunta al director: "¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?"

En **Modo resultado**, lo que se aprueba son las **dos piezas juntas** — la Story y su pie —, porque
se envían juntas y una sin la otra queda coja. Al aprobar, muestra la ruta del PNG y el pie listo
para copiar.

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

## Modo ejecutivo (flag `ejecutivo`)

Si `ejecutivo` aparece en los argumentos, además del mensaje de cliente genera el **guion de venta interno** siguiendo `.claude/shared/modo_ejecutivo.md` (formato, banner `🔒 INTERNO · NO ENVIAR AL CLIENTE`, flujo de aprobación y guardrails). Para esta pieza:
- **Tipo de guion**: `guion_dato_macro`.
- **`-Activo`**: el ticker del activo más impactado por el dato.
- Mismo `-Hora` que el mensaje de cliente.

Muestra ambas salidas rotuladas `📤 MENSAJE CLIENTE` y `🔒 GUION EJECUTIVO`; al aprobar, guarda el guion con `scripts\ruta_mensaje.ps1`.

## REGLAS
- Sin límite de veces al día (cada dato relevante merece su propio mensaje).
- Hora: en fuente MT5 nativa, la hora es la del servidor MT5 (broker actual = hora Chile, se muestra tal cual). En fallback WebSearch, convertir a hora Chile con `scripts\hora_chile.ps1`.
- Lenguaje simple: el cliente debe entender qué mide el indicador en 10 segundos.
- **Indicadores en español** con la sigla original entre paréntesis una sola vez (issue #46). Minimizar términos en otro idioma en el cuerpo.
- **Ninguna abreviatura sin explicar**: en Modo anticipación, vía el bloque "🔤 Diccionario rápido"; en Modo resultado, explicada en línea dentro del pie. Fuente canónica: `data/glosario_siglas.json` (alimentarla con siglas nuevas en ambos modos).
- **Modo resultado = imagen + pie**: la pieza principal es la Story de `/story dato_macro` y el mensaje es su pie de foto. El desarrollo largo no se manda como texto.
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
- **Filtro de cobertura por país (PASO 1C)**: Zona Euro = solo decisión de tasas BCE; EE.UU. = solo 3★ enmarcados en la narrativa de tasas Fed e impacto en índices bursátiles (US100/US30); Chile = solo balanza comercial.
- **Temporalidad del impacto obligatoria**: todo mensaje indica si el efecto es scalper / intradía / swing de jornada / posicional (alineado con las 4 etiquetas canónicas de temporalidad de CLAUDE.md).
- **Alto impacto**: las sub-lecturas (anual + mensual, normal + subyacente según corresponda) viven ahora en la Story del Modo resultado, no en el texto; las demás no se incluyen en ninguna de las dos.
- **Bloque de cierre obligatorio**: todo mensaje de `/dato_macro` (ambos modos) cierra, después del último separador, con el link al calendario completo (`https://es.investing.com/economic-calendar/`) y el CTA genérico al analista designado. El link y el CTA van siempre juntos como pie del mensaje.
