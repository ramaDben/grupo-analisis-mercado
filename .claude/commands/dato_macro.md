Lista todos los datos económicos del día y genera la pieza WhatsApp del que elija el director: si el dato ya publicó, una Story de marca con su pie de foto; si todavía no sale, el mensaje de anticipación completo.

## PASO 1: Obtener la hora actual de Chile y el calendario de hoy

**1A: Hora actual Chile (OBLIGATORIO, hacer PRIMERO)**:
Obtén el timestamp actual de Chile con el **reloj del sistema** (regla canónica de CLAUDE.md, NUNCA con `WebSearch`):
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
([System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)).ToString('yyyy-MM-dd HH:mm')
```
Guarda la hora como `hora_actual_chile` (ej: `09:47`) y la fecha como `[FECHA]`. Lo necesitas para marcar eventos pasados/futuros en PASO 2. Maneja CLT/CLST automáticamente.

**1B: Calendario económico e Ingesta Soberana (data central/ y MT5 nativo primero, WebSearch fallback)**:

1. **Fuente primaria: Base Soberana data central/ y MT5 nativo**:
   - Consulta `obtener_calendario_macro(min_impact="medium")` y verifica si existen datos actualizados en `data central/DATA AGENDA/calendario_2026.json` o `data central/DATA [PAIS]/raw/`.
   - Si devuelve `{"eventos": [...]}`: usa esos eventos. La hora ya viene en **hora del servidor MT5** (broker actual = hora Chile): **no conviertas nada**.
   - Cada evento trae `nombre` (ya en español), `pais`, `divisa`, `impacto`, `hora_servidor`, `periodo`, `previo`, `forecast`, `actual`. Si trae `diccionario`, úsalo para el bloque Diccionario rápido; si trae `glosario_pendiente: true`, explica la sigla al vuelo y añádela a `data/glosario_siglas.json` por su `event_id`.
   - Si devuelve `{"eventos": []}` con `info`: es fin de semana/feriado: muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN.

2. **Fallback: WebSearch**: solo si la tool devuelve error o falta de archivo, avisa al director ("⚠️ calendario nativo no disponible, uso WebSearch") y usa el flujo WebSearch sobre investing.com:
   - Query: `investing.com calendario económico hoy [FECHA] Chile Estados Unidos Japón "Zona Euro" China impacto alto`.
   - En este fallback extranjero sí conviertes la hora con `scripts\hora_chile.ps1` desde la zona del organismo emisor (ej. Asia/Tokyo para Japón).

**Contrato sin-resultados**: si la búsqueda no devuelve eventos de impacto medio/alto para hoy: muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN.

## PASO 1C: Filtrado por país (OBLIGATORIO, antes de presentar la lista)

Aplica estos filtros al set de eventos obtenido. El filtro aplica **tanto a la lista del PASO 2 como al desarrollo del PASO 3**:

- **Estados Unidos**: conservar **solo eventos de 3 estrellas (★★★, alto impacto)**. Descartar los de 2★. Cada evento de EE.UU. se enmarca en la narrativa de la **decisión de tasas de la Fed** y se traduce a impacto en **índices bursátiles** (US100 / US30).
- **Japón**: conservar **la decisión de tasas del Banco de Japón (BoJ)** y el **Índice de Precios al Consumidor (IPC Nacional y de Tokio)**. Descartar el resto de datos secundarios (PMI, producción industrial). Enmarcar en el diferencial de tasas con EE.UU., los rendimientos de bonos del Ministerio de Finanzas (MOF) y el impacto en **USD/JPY**.
- **Chile**: conservar **la balanza comercial, Imacec e IPC**. Descartar exportaciones secundarias y manufacturas.
- **Zona Euro**: conservar **solo la decisión de tasas del BCE**. Descartar el resto de datos secundarios.
- **Otros países** (ej. China): sin cambios respecto al filtro de impacto medio/alto ya aplicado.

Si tras el filtrado no queda ningún evento: muestra "📅 Sin datos macro relevantes para hoy (según filtros de cobertura)" y DETÉN.

## PASO 2: Presentar lista al director

Muestra una lista numerada con los datos del día, ordenados por hora Chile. Para cada evento, compara su hora contra `hora_actual_chile` obtenida en PASO 1A:
- Si la hora del evento **ya pasó** -> agregar `✅ YA SALIÓ`
- Si la hora del evento **aún no llegó** -> agregar `🕐 PRÓXIMO`

```
📅 Datos económicos de hoy: [FECHA]

1. 🔴 [Hora CLT] : [Indicador] ([País], ★★★) | Prev: X | Esp: Y  ✅ YA SALIÓ
2. 🟡 [Hora CLT] : [Indicador] ([País], ★★) | Prev: X | Esp: Y  🕐 PRÓXIMO
3. 🟡 [Hora CLT] : [Indicador] ([País], ★★) | Prev: X | Esp: Y  🕐 PRÓXIMO
...

¿Cuál(es) quieres desarrollar? (escribe el número o "1,3" para varios)
```

Iconos por importancia: 🔴 = 3 estrellas (alto impacto) | 🟡 = 2 estrellas (moderado)

**Selección de modo automático**: cuando el director elija un evento marcado `✅ YA SALIÓ`, usar directamente el **Modo resultado** en PASO 3. Si elige uno `🕐 PRÓXIMO`, usar **Modo anticipación**.

## PASO 3: Generar mensaje WhatsApp por dato elegido

**Regla de traducción**: todo indicador se nombra en **español**, con la sigla original entre paréntesis **una sola vez** (ej. "Índice de precios al consumidor (IPC)"). En el resto del cuerpo se usa el nombre en español; minimiza al máximo los términos en otro idioma.

**Bloque "🔤 Diccionario rápido" (OBLIGATORIO en Modo anticipación)**: por cada sigla/abreviatura que aparezca en el mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), agrega al final una línea explicativa en voz novata tomada de `data/glosario_siglas.json`. Si la sigla **no está** en el glosario, explícala al vuelo (1-2 líneas) y **añádela a `data/glosario_siglas.json`**.

Por cada dato que elija el director, genera:

**Modo anticipación** (dato aún no ha salido):
```
📅 *DATO MACRO: [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es?
[Explicación simple en 1-2 líneas. Sin tecnicismos.]

🕐 Sale hoy a las [Hora CLT]

📊 Qué se espera:
• Anterior: [valor]
• Consenso del mercado: [valor esperado]

🎯 Escenarios:
• 🟢 Escenario Alcista: [qué tendría que pasar y activos favorecidos, 1 línea]
• 🟡 Escenario Lateral: [en línea con lo esperado, rango de oscilación, 1 línea]
• 🔴 Escenario Bajista: [qué activaría corrección o caída, 1 línea]

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

**Modo resultado** (dato ya publicó, tiene valor "actual": la pieza es la Story, este texto es su pie de foto):

En este modo el entregable al grupo son **dos cosas que viajan juntas**: la imagen generada por `/story dato_macro` (que lleva el veredicto, las cifras, el "qué significa", el gráfico de la serie y el impacto por activo) y este pie corto.

1. **Generar primero la Story** con la ruta `dato_macro` de `/story` (ver `.claude/commands/story.md`).
2. **Escribir el pie** con esta plantilla:

```
📊 *DATO MACRO · [PAÍS]*
🕐 Publicado hoy [Hora CLT]

🎯 *[Indicador en español (SIGLA)] de [periodo]: [actual]*
[🔴/🟢/🟡] *[PEOR / MEJOR / EN LÍNEA] de lo esperado*: el mercado calculaba [esperado]
⚡ [1 línea: qué implica y hacia dónde empuja: dirección explícita, regla de oro]

⏱️ Impacto [scalper (minutos a 1-2 h) / intradía (dentro de la jornada) / swing de jornada (1-3 días) / posicional (días a semanas)]
━━━━━━━━━━━━━━━━━━━
📅 Calendario completo del día: https://es.investing.com/economic-calendar/
💬 ¿Cómo aprovechar este dato en tus operaciones? Escríbele a tu analista designado.
```

**Reglas del modo resultado**:
- **Above the fold**: el veredicto completo va en las primeras 3 líneas.
- **Emoji del veredicto**: 🔴 peor · 🟢 mejor · 🟡 en línea frente al consenso.
- **Siglas explicadas en línea**: dentro de la propia frase, una sola vez.
- **Cero guiones largos**: Prohibido el uso de `—` o `–` en el texto.
- **Formato decimales**: Precios y niveles respetando `config/activos.json` (USDJPY: 3 decimales, USDCLP: 2 decimales).

## PASO 4: Aprobación y envío
Pregunta al director: "¿Apruebas? ¿Adjuntar chart o Story? ¿Enviar al grupo WhatsApp?"
Al aprobar, muestra el texto listo para copiar.

## REGLAS
- Sin límite de veces al día (cada dato relevante merece su propio mensaje).
- Hora: en fuente MT5 nativa, la hora es la del servidor MT5 (broker actual = hora Chile, se muestra tal cual). En fallback WebSearch, convertir a hora Chile con `scripts\hora_chile.ps1`.
- Lenguaje simple: el cliente debe entender qué mide el indicador en 10 segundos.
- **Indicadores en español** con la sigla original entre paréntesis una sola vez.
- **Cero guiones largos ni medios** en todo texto para WhatsApp.
- **Semáforo Canónico de Precios**: 🟢 Sobre (Alcista), 🟡 Entre (Rango), 🔴 Bajo (Bajista).
