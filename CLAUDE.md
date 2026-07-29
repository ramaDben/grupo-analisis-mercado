# Grupo de Análisis de Mercado — Sistema Automatizado

## Contexto
Este proyecto automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El usuario es el director de trading. Los sub-agents actúan como analistas de mercado y recolectores de información.

## Principio fundamental
Análisis técnico simple y directo, con dirección clara, que genere interés y apetito por operar — sin caer en lo coloquial ni en lo catastrófico. El mensaje lo reciben tanto traders expertos como clientes novatos: debe ser comprensible para quien recién aprende y, a la vez, accionable para quien ya opera. Se enfatiza la tendencia y se nombra hacia dónde se dirige el activo, despertando el interés del cliente por operar el mercado.

**Regla de oro**: el cliente debe entender siempre hacia dónde se dirige el activo, para saber qué operar. Un análisis que no deja clara la dirección (alcista / bajista / lateral) está incompleto.

Criterio de claridad (subordinado a la regla de oro): si un cliente nuevo sin experiencia no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple — pero "más simple" nunca significa "sin dirección".

## Activos cubiertos (rotación diaria, 2-3 por día)
- **USD/CLP**: drivers → cobre, Dollar Index, tasas BCCh vs Fed, flujos
- **Oro (XAU/USD)**: drivers → Dollar Index, tasas reales, decisiones Fed, coberturas bancos centrales, geopolítica
- **WTI (Petróleo)**: drivers → inventarios EIA, decisiones OPEP+, demanda China, geopolítica
- **US100 (Nasdaq 100)**: drivers → tasas Fed, earnings tech, rendimientos Treasury
- **USD/JPY (Dólar / Yen japonés)**: cobertura por pedido externo, **fuera de la rotación diaria** de 2-3 activos (se cubre cuando el director lo pide). drivers → diferencial de tasas Fed vs BoJ, decisiones del BoJ, rendimientos Treasury, intervención del Ministerio de Finanzas de Japón, precios de energía, aversión al riesgo
- **Acciones (rotación por análisis previo)**: además de los 4 activos base, la rotación diaria puede incluir 1-2 acciones del catálogo elegidas por análisis previo. Fuente interina: las 2 acciones destacadas por `/earnings` esa semana. Mecanismo definitivo (market screener que recorra las acciones disponibles en MT5 y elija las 2 mejores): **pendiente, issue aparte**.

## Estructura diaria obligatoria (lunes a viernes)

> **Orden canónico (issue #43)**: el dato/noticia del calendario va PRIMERO, para enviar el fundamental del día al cliente mientras se cargan los niveles en MT5 (los niveles requieren input manual y tardan más). Los comandos de día (`/martes`, `/miercoles`, `/jueves`, `/viernes_am`) generan el dato macro como PIEZA 1 y la apertura/niveles como PIEZA 2.

### 1. Noticia relevante del calendario económico
- 1 noticia o dato del día que impacte directamente a alguno de los activos
- Explicar simple: qué es, a qué hora sale, qué se espera y cómo podría reaccionar el activo
- Fuente oficial: calendario de Investing.com
- Hora siempre en hora Chile (CLT/CLST)

### 2. Niveles técnicos del día
- Enviar niveles en temporalidades 4H, 1H o 15M
- Cubrir 2 o 3 activos por día (rotar entre USD/CLP, Oro, WTI, US100)
- Indicar: soportes, resistencias, zona de interés y posible sesgo
- La temporalidad y el indicador se eligen por activo vía `/apertura` (nunca se asume 4H fijo). Los niveles se presentan como **lectura/marco temporal**, no como señal de operativa.

### 3. Drivers del activo
- Explicación corta de los drivers que están moviendo al activo
- Si hay información relevante durante el día (declaraciones, datos sorpresivos, eventos geopolíticos), informar de inmediato

## Reglas de temporalidad
Cada análisis indica explícitamente su temporalidad con un rango cuantificado (prohibido usar "corto" sin número — issue #44):
- **15M** → scalper (minutos a 1-2 h) — alta rotación, movimientos rápidos del día
- **1H** → intradía (dentro de la jornada) — movimientos del día, confirmar entradas finas
- **4H** → swing de jornada (1-3 días) — tendencia del día y operativas de varias horas
- **1D** → posicional (días a semanas) — lectura general del activo

Estas 4 etiquetas son la fuente única y deben ser idénticas en `.claude/commands/apertura.md` (PASO 2 y PASO 5).

**Justificar la temporalidad por la volatilidad del activo (OBLIGATORIO)**: cada activo tiene un nivel de `volatilidad` y una `nota_volatilidad` en `config/activos.json`. El mensaje de niveles incluye la línea `{{por_que_temporalidad}}` (`💡 Por qué [TF] aquí: …`) que explica al cliente, en lenguaje novato, por qué la temporalidad elegida encaja con la volatilidad de ese activo (ej.: USD/CLP es de baja volatilidad → 1H/4H dan lectura más limpia; WTI/Oro son de alta volatilidad → 15M tiene más ruido).

Ejemplo obligatorio: "Niveles en 15M — marco scalper (minutos a 1-2 h)"

## Fecha y hora actual — regla canónica (OBLIGATORIO)
**Nunca** uses `WebSearch` para obtener la fecha o la hora actual: devuelve snippets de búsqueda (cacheados, imprecisos o ausentes), no un reloj, y produce errores al fechar mensajes o marcar eventos pasados/futuros.

**Método único y determinista** — obtén la hora de Chile (CLT/CLST, ajuste de horario de verano automático) con el reloj del sistema:
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$now.ToString('yyyy-MM-dd HH:mm')   # ej: 2026-06-03 12:30
```
- Úsalo siempre que necesites: marcar eventos `✅ YA SALIÓ` / `🕐 PRÓXIMO`, decidir piezas dependientes de la hora, o nombrar archivos `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt`.
- El resultado debe ser consistente con el `currentDate` del contexto. La *hora actual* siempre sale de este reloj.

**Calendario económico Investing.com (fuente primaria)**: la hora del evento se pide en UTC (timeZone=55) y se convierte automáticamente a `America/Santiago` dentro de `obtener_calendario_macro`. El resultado ya está en hora Chile — no se necesita conversión adicional.

**Hora de los datos económicos (origen extranjero) — también determinista (OBLIGATORIO)**: la *hora del evento* se obtiene de la fuente, pero la conversión a Chile **nunca** se hace "a mano" ni con offsets fijos (`UTC-5`, `GMT-3`) — esa asunción causa desfases de ±1h (issue #38). Toma la hora **oficial en la zona del organismo emisor** y conviértela con el helper `scripts\hora_chile.ps1`, que aplica el horario de verano de ambas puntas y devuelve la etiqueta CLT/CLST correcta:
```powershell
scripts\hora_chile.ps1 -Hora "08:15" -ZonaOrigen "Eastern Standard Time" -Fecha "2026-06-03"   # -> "08:15 CLT"
```
Zonas canónicas (IDs Windows): EE.UU. (BLS/ISM/ADP/EIA/Fed) → `Eastern Standard Time` · Zona Euro (Eurostat/BCE) → `W. Europe Standard Time` · China (NBS/Caixin) → `China Standard Time` · Chile (BCCh/INE) → `Pacific SA Standard Time` · Reino Unido (BoE) → `GMT Standard Time` · Japón (BoJ / Ministerio de Finanzas) → `Tokyo Standard Time`.

**Cruce de día en eventos asiáticos (OBLIGATORIO)**: el helper devuelve la hora, **no la fecha**. Japón va 13 h adelante de Chile, así que un evento japonés cae el **día anterior** en nuestro calendario: la decisión del BoJ del viernes 31 a las 12:00 JST ocurre el **jueves 30 a las 23:00 CLT**. Al fechar un evento asiático, calcula también la fecha en Chile y comunícala siempre en hora Chile. Caso especial del BoJ: **no compromete hora exacta** de anuncio (publica entre 11:30 y 12:30 JST), así que la ventana en Chile es 22:30–23:30; la conferencia posterior del gobernador sí tiene hora fija (15:30 JST) y es donde suele estar el movimiento del USD/JPY.

## Agenda semanal

| Día | Contenido principal | Encuesta | Señales |
|-----|---------------------|----------|---------|
| Domingo | Noticias fin de semana + preview semana + sesgo lunes | Encuesta semana | No aplica |
| Lunes | Resumen calendario semanal + concepto de la semana | Tendencia AM | Según oportunidad |
| Martes | Niveles + noticia + drivers | Precio apertura | Según oportunidad |
| Miércoles | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Jueves | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Viernes | Niveles + noticia + drivers + cierre semanal | Precio apertura lunes | Según oportunidad |

## Señales operativas
- **Máximo 3 por semana** (hard limit, verificar en data/historial_senales.json)
- Tipo: swing (varios días) o scalper (intradía cortas)
- Campos obligatorios: ticker, nombre activo, BUY/SELL, entrada, volumen, acciones, TP, SL
- **TP y SL traducidos a pesos chilenos (CLP)** — el cliente debe ver cuánto gana y cuánto pierde sin calcular nada
- Máximo 3 bullets de análisis (técnico + fundamental)
- Siempre usar plantilla oficial
- Las señales son complementarias, NO el foco principal del grupo

## Encuestas diarias (lunes a viernes)
- **3 días (L, X, J)** → Encuesta de tendencia AM: "¿Cuál creen que será la tendencia hoy del [activo]?" → Alcista / Bajista / Lateral
- **2 días (M, V)** → Encuesta de precio de apertura: "¿A qué precio creen que abrirá el [activo] mañana / el lunes?"
- **IMPORTANTE**: siempre enviar previamente una noticia, evento o análisis para que el cliente vote con base en información, no en intuición

## Indicadores técnicos
Un aviso = un indicador. NUNCA mezclar múltiples señales técnicas al mismo tiempo:
- **ATR** → recalcar su uso en USD/CLP como indicador de volatilidad
- **RSI** → avisar cuando esté sobrecomprado o sobrevendido
- **MACD** → avisar cruces relevantes
- **Medias móviles** → avisar cruces de medias (ej: cruce de la 50 con la 200)

## Formato visual de mensajes WhatsApp

### Principio rector: el reporte como mapa rápido
Primero conclusión, después detalle técnico. Las primeras 3-4 líneas deben entregar lo esencial — muchos clientes no abren el "leer más" de WhatsApp (~200 caracteres visibles).

### 6 reglas de formato (OBLIGATORIAS en todos los mensajes)

**1. Resumen al inicio**
Abrir cada mensaje de análisis/niveles con 3 líneas antes de cualquier detalle técnico:
```text
🎯 Activo: [nombre]
📌 Nivel a vigilar: [precio]
⚡ Qué esperar: [1 línea de acción]
```

**2. Sistema de emojis de color para escenarios**
Usar siempre estos códigos visuales — consistentes en todos los mensajes:
- 🟢 Escenario alcista
- 🔴 Escenario bajista
- 🟡 Zona de espera / confirmación
- 🎯 Objetivo (TP o nivel clave)
- ⚠️ Riesgo o advertencia

**3. Separadores entre secciones**
`━━━━━━━━━━━━━━━━━━━` entre cada bloque de contenido — obligatorio.

**4. Negritas solo en jerarquía**
Usar *negrita* ÚNICAMENTE en: título de sección, niveles clave y conclusión. Nunca en el cuerpo del análisis.

**5. Optimización "above the fold"**
Las primeras 3-4 líneas contienen la conclusión práctica. El detalle técnico va después, para quien quiera profundizar.

**6. Cierre con lectura práctica**
Cerrar cada mensaje de niveles/análisis con este bloque:
```text
🟢 Sobre [resistencia] → fuerza compradora
🟡 Entre [soporte] y [resistencia] → esperar confirmación
🔴 Bajo [soporte] → presión vendedora
```

### Registro y tono — profesional, técnico y con gancho operativo (OBLIGATORIO)
Los análisis transmiten seriedad y credibilidad y, a la vez, generan interés y apetito por operar. **Se permite y se busca** enfatizar la tendencia, tomar postura direccional clara y redactar con tono persuasivo que invite a operar. Lo que sigue **prohibido** es el lenguaje extremo, catastrófico o demasiado coloquial (dramatizar el movimiento, atribuir "sensaciones" al mercado, vaticinar catástrofes, jerga de barrio). En una frase: **énfasis direccional sí, dramatización no**. Se describe el mercado con terminología financiera objetiva, comprensible para el cliente y con gancho.

| ❌ Evitar (extremo/emocional/coloquial) | ✅ Usar (técnico/objetivo) |
|---|---|
| "el oro se va a derrumbar" | "sesgo bajista" / "expectativas de corrección" |
| "el mercado tiene una sensación pésima" | "presión vendedora" / "debilidad en el precio" |
| "esto se va a disparar / explotar" | "sesgo alcista" / "impulso comprador" |
| "está volando / por las nubes" | "alta volatilidad" / "momentum alcista" |
| "pánico" / "euforia" / "terror" | "aversión al riesgo" / "apetito por riesgo" |

Reglas:
- Enfatizar con dirección, sin dramatizar: hablar con fuerza de **sesgo, tendencia, momentum, presión, volatilidad, debilidad/fortaleza, corrección** y nombrar hacia dónde se dirige el activo, pero sin emociones atribuidas al mercado ni finales catastróficos.
- Tomar postura: cada análisis nombra el escenario más probable (sesgo). Los escenarios siguen siendo condicionales (`🟢 sobre X → …`, `🔴 bajo Y → …`), nunca certezas absolutas ("se va a derrumbar"), pero sí señalan claramente la dirección de mayor probabilidad.
- Profesional con gancho **≠** neutral sin dirección: un mensaje "objetivo" que no toma postura direccional está incompleto (ver Regla de oro del Principio fundamental).
- Esto **no** habilita jerga sin explicar: si aparece un término técnico o una sigla, sigue siendo obligatorio explicarlo en voz novata (ver [estilo mensajes WhatsApp] y "Datos macro en español + Diccionario rápido"). Profesional ≠ inaccesible.

### Formato base (aplica a todos los mensajes)
- Formato WhatsApp: *negrita*, _cursiva_
- Bullets: •
- Horas siempre en hora Chile (CLT/CLST)
- Estructura formal, consistente y repetible cada día
- Emojis con moderación: 📊 📈 📉 ⚠️ 🕐 📚 📅 (más 🟢🔴🟡🎯 del sistema de escenarios)

## Datos macro en español + Diccionario rápido (OBLIGATORIO — issue #46)
- **Indicadores en español**: todo dato macro se nombra en español, con la sigla original entre paréntesis **una sola vez** (ej. "Índice de gerentes de compra manufacturero (PMI manufacturero)"). Minimizar términos en otro idioma en el cuerpo del mensaje.
- **Bloque "🔤 Diccionario rápido"**: obligatorio en `/dato_macro` (ambos modos) y en `/noticia` cuando aparezcan siglas. Por cada abreviatura del mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), una línea explicativa en voz novata. **Ninguna abreviatura puede quedar sin explicación en español ese día.**
- **Fuente canónica**: `data/glosario_siglas.json` (`SIGLA → {nombre_es, explicacion}`). Si aparece una sigla nueva, explicarla al vuelo y **añadirla al JSON** para reutilizarla.
- En `/dato_macro`, la fuente principal del panorama del día es la tool MCP `obtener_calendario_macro` (calendario Investing.com — Chile/EE.UU./China/Zona Euro, con resultado real `actual` y clasificación mejor/peor/en_linea); WebSearch sobre investing.com + fuentes oficiales son fallback solo si la tool devuelve `{"error": ...}`.

### Dos modos de `/dato_macro` y plantilla del Modo resultado (issue #93)
`/dato_macro` genera el mensaje en uno de **dos modos**, elegidos automáticamente según la hora del evento vs. la hora actual de Chile:
- **Modo anticipación** (dato `🕐 PRÓXIMO`, aún no sale): qué es + hora CLT + anterior/consenso + 3 escenarios (mejor/peor/en línea) + activos a observar + temporalidad del impacto.
- **Modo resultado** (dato `✅ YA SALIÓ`, ya tiene valor `actual` — plantilla issue #93): es la estructura canónica cuando el dato ya publicó. Reglas:
  - **Veredicto above-the-fold**: encabezado + veredicto *EN LÍNEA / MEJOR / PEOR* + primera sub-lectura caben en las primeras 3-4 líneas (~200 caracteres visibles en WhatsApp).
  - **Sub-lecturas**: una línea por sub-lectura (`actual` vs `esperado`), marcando la sorpresa con 🔥. En datos de **alto impacto** limitar a anual + mensual y normal + subyacente según el indicador; nunca volcar todas las filas.
  - **Bloque "⚠️ PERO ojo con el detalle importante"** (OPCIONAL): solo cuando una sub-lectura se desvía del consenso mientras el dato general salió en línea — explica qué mide esa sub-lectura en voz novata y por qué cambia la lectura. Si no hay sorpresa parcial, se omite entero.
  - **🧠 ¿Qué significa esto?**: 2-4 líneas en voz novata. Si salió en línea, explicar que el mercado ya lo tenía descontado.
  - **💡 Impacto esperado por activo**: 3-4 activos con *SUBE ⬆️ / BAJA ⬇️* y el porqué en 1 línea, conectando con el camino a la decisión de tasas cuando aplique.
  - **⏱️ Temporalidad del impacto** (OBLIGATORIA, ambos modos): scalper / intradía / swing de jornada / posicional (mismas 4 etiquetas canónicas de temporalidad).
  - **📌 Resumen simple** de cierre que amarra el dato general + la sorpresa parcial si la hubo.
- **Cierre obligatorio (ambos modos)**: tras el último separador, link al calendario completo (`https://es.investing.com/economic-calendar/`) + CTA genérico al analista designado, siempre juntos como pie.
- Tras aprobar y enviar, `/dato_macro` registra `data/ultimo_evento.json` y ofrece encadenar la **encuesta post-evento** pedagógica.

## Formato de precios — regla de decimales MT5
**OBLIGATORIO**: al mostrar cualquier precio (entrada, TP, SL, soporte, resistencia, precio actual), respetar exactamente los decimales del campo `digits` definido en `config/activos.json` para ese activo.

| Activo | Digits | Ejemplo correcto | Ejemplo incorrecto |
|--------|--------|------------------|--------------------|
| USDCLP | 2 | $889.60 | $889.6 / $890 |
| USDJPY | 3 | 163.731 | 163.73 / 163.7 |
| XAUUSD | 2 | $4,539.72 | $4.539 / $4,540 |
| WTI.spot | 3 | $90.181 | $90.18 / $90.2 |
| US100.spot | 2 | 30,350.01 | 30.350 / 30,350 |
| Acciones | 2 | $192.50 | $192.5 / $193 |
| COPPER | 0 | 13720 | 13.720 / 13720.0 |

Nunca truncar ceros al final (89.60, no 89.6). Nunca redondear a enteros salvo que digits = 0.

## Eventos de alto impacto (decisiones de tasas)
Cuando hay decisión de tasas (Fed, BCCh, BCE):
1. Anticipar la reunión con varios días de antelación
2. Conectar datos previos (IPC, PCE, PMI, empleo) con el escenario de tasas
3. Explicar probabilidades de recorte/alza según el mercado
4. Día de la decisión: análisis previo + monitoreo en vivo + explicación posterior

Objetivo: que el cliente entienda que los datos económicos son piezas que van armando el camino hacia la decisión de tasas.

## Contenido educativo
- **Concepto de la semana** (lunes): un concepto que se refuerza durante la semana
- **Pregunta del día** (1x semana): pregunta abierta tipo "¿Por qué creen que el oro subió tras el dato de inflación?"
- **Glosario fijado**: mensaje fijo en el grupo con conceptos clave (IPC, PMI, PCE, NFP, Dollar Index, ATR, RSI, etc.)
- Temas: tendencias, canales, rangos, indicadores (uno a la vez)

## Rol paralelo del grupo
Aunque el grupo es para clientes, sirve como espacio de alineación interna:
- **Ejecutivos**: se mantienen al tanto del mercado, refuerzan conceptos, replican el lenguaje simple con sus carteras
- **Analistas**: observan cómo se comunica al cliente, aseguran consistencia y aportan profundidad

## Misión
Mejorar indicadores de satisfacción del cliente, retención, NPS y reducir churn. Pasar de un modelo de señales a un modelo de análisis + educación donde el cliente aprende a leer el mercado.

## MCP Servers integrados

| MCP | Estado | Propósito | Usado en |
|-----|--------|-----------|----------|
| **market-data** | ✅ Activo | Análisis técnico MT5 (`get_asset_levels`) + niveles dibujados a mano por el director en MT5 (`get_chart_objects`: soportes/resistencias, trendlines, canales, rectángulos + screenshot) + calendario económico Investing.com (`obtener_calendario_macro`): Chile + EE.UU. + China + Zona Euro, con resultado real (`actual`) y clasificación `mejor`/`peor`/`en_linea` vs consenso. WebSearch es fallback si la fuente falla. Noticias vía WebSearch. | Comandos de niveles técnicos |
| **WebSearch (investing.com + fuentes oficiales)** | ✅ Activo | Calendario económico y noticias relevantes | `/dato_macro`, `/noticia` y comandos de día |
| **WhatsApp (Evolution API)** | ⏳ Pendiente conexión Docker | Envío directo al grupo | Flujo manual por ahora |
| **TrendRadar / Firecrawl / Finnhub** | ❌ No activos | Reemplazados por market-data (MT5) + WebSearch | — |

**Nota**: el MCP `market-data` expone **tres** tools:
- `get_asset_levels` — análisis técnico MT5 automático (soportes/resistencias, indicadores).
- `get_chart_objects` — niveles dibujados a mano por el director en MT5 (soportes/resistencias, trendlines, canales, rectángulos) más screenshot, vía el Service `ChartObjectsExporter` (sub-proyecto A, #98). Permite leer el marcado manual del director en lugar de inferirlo automáticamente.
- `obtener_calendario_macro` — calendario económico Investing.com (Chile/EE.UU./China/Zona Euro con campo `actual` y `resultado`, issue #91; WebSearch es fallback si la fuente falla).
- `get_symbol_spec` — especificaciones de contrato de un símbolo (trade_mode, digits, volumen mínimo/paso, tamaño de contrato) y sesiones de trading semanales en hora Chile; con `fecha` responde de forma determinista si el activo opera ese día (issue #104).

Contrato de error común: si el dato no está disponible retorna `{'error': 'CÓDIGO', 'message': '...'}` — nunca array vacío ni `None` silencioso. La antigua `get_economic_events` fue reemplazada por la tool nativa (#53); `get_market_context` (noticias Finnhub) quedó deprecada y se purgó del registro — las **noticias** se obtienen vía `WebSearch` (investing.com + fuentes oficiales: Fed, BCCh, OPEP+, EIA, BLS). Ver `docs/archive/superpowers/specs/2026-06-05-calendario-macro-nativo-mt5-design.md`.

**Flujo actual**: los comandos generan contenido → muestran para copiar → guardan en `data/mensajes/`. Cuando Evolution API esté conectada a WhatsApp/Baileys, el envío pasará a ser automático.

**Setup WhatsApp**: requiere Evolution API en Docker (`docker run -d --name evolution-api -p 8080:8080 atendai/evolution-api`). Ver instrucciones en `mcp/mcp_config.json`.

## Stories GI

Piloto (issue #109): comando `/story [tipo]` genera Stories de marca (imagen 1920×1080).
`[tipo]` soportados hoy: `alerta`, `quote`, `breaking`, `encuesta`, `edu` (Fase B, issues
#121/#123/#125/#127), `flash` (Fase C, issue #129) y `postventa` (Fase C). `alerta` (plantilla "03 Alerta de Mercado") combina niveles reales del motor
(`get_asset_levels`) con una narrativa de alerta (mismo criterio editorial de `/alerta`); `quote`
es una pieza 100% editorial (cita + autor + cargo, sin dato del motor); `breaking` es una pieza
editorial de noticia urgente (kicker + titular + cifra clave + contexto + reacción, sin dato del
motor ni búsqueda propia de evento); `encuesta` es una pieza editorial de sentimiento binario
(kicker + pregunta + dos opciones "A vs B" + nota de cierre, sin dato del motor ni búsqueda
propia de evento, mismo criterio que `/encuesta`); `edu` es una pieza editorial de concepto
educativo (kicker + título + definición + ejemplo comparativo + lista de bullets de aplicación
vía loop `<!-- FOR:bullets -->`, sin dato del motor ni búsqueda propia de evento, mismo criterio
que `/concepto` y `/rencuesta`); `flash` es una pieza de cierre multi-activo (kicker + título +
fecha + tabla de N activos con último valor y variación del día, vía loop `<!-- FOR:filas -->`),
que **sí** consume datos reales del motor (`get_asset_levels` × N activos, con fallback manual)
pero **sin gráfico embebido** ni búsqueda editorial de evento — es la primera plantilla de Fase C
(plantillas con listas). `postventa` es la **única pieza interna** (no publicable): guion operativo
del parte de post-venta (consulta del día + franja de niveles con color semántico + dos listas
independientes, `<!-- FOR:respuestas -->` y `<!-- FOR:no_promesas -->`). Su chip
`🔒 Interno · Post-venta` va **literal en el snapshot, no como token** — ningún payload puede
suprimirlo — y su footer **no** lleva handle, dominio ni disclaimer de CFD; en su lugar,
"Uso interno · No reenviar al cliente". Reusa los datos de `/postventa` si ya se corrió, o los toma
del motor en frío. Único renderer: `scripts/story_render.py`
(payload JSON → HTML → PNG con Playwright headless). **Formato del lienzo**: el flag
`--formato horizontal|vertical` elige entre 16:9 (1920×1080, por defecto) y 9:16 (1080×1920, para
celular). El formato viaja por el CLI y **nunca** por el payload — el payload es contrato de
contenido y el formato es presentación, así el **mismo payload rinde ambos**. Cada snapshot es un
único archivo que se adapta con `@media (max-aspect-ratio: 1/1)`, en vez de tener un archivo por
formato (evita que la versión vertical se desfase de la horizontal). Migradas a responsive:
`templates/stories/postventa.html` y `templates/stories/alerta.html`; las otras 5 siguen solo en
horizontal — una plantilla por Change, mismo criterio que las Fases B y C. Snapshots de marca:
`templates/stories/alerta.html`, `templates/stories/quote.html`, `templates/stories/breaking.html`,
`templates/stories/encuesta.html`, `templates/stories/edu.html`, `templates/stories/flash.html` y
`templates/stories/postventa.html`. Las demás plantillas del canvas (Market Update, Indicador
Macro, Trading Idea, Calendario, Semanal, Carrusel "Oportunidades de la semana") llegan con los issues
#111-#115 — ver `docs/design/stories-gi/plantillas-stories-gi.md` para el mapeo campo-por-campo.

**Escritura en el proyecto Claude Design de GI (regla actualizada 2026-07-27)**: el proyecto
Claude Design compartido (dueño: Rodrigo, GI) —
`https://claude.ai/design/p/05b3bfe8-d8ad-4f83-b7b0-e8de4d77a3cf` — es de **lectura y escritura**
vía la tool `DesignSync`. La antigua regla "solo lectura" quedó **revocada por decisión del
director**. Se mantienen dos condiciones: (1) el render final se produce y se aprueba **siempre
dentro de este repo** (`scripts/story_render.py` sobre los snapshots de `templates/stories/`), y
(2) **nada se sube sin aprobación explícita del director** — la subida pasa por `finalize_plan`,
que le muestra el listado exacto de rutas antes de escribir. Convención del canvas para las
subidas: piezas como `Story <fecha> <activo>.dc.html` en la raíz y renders en `exports/*.png`.

**Guardado**: `data/stories/<Fecha>/<activo_slug>/<plantilla>/<Hora>_<plantilla>.png` vía
`scripts\ruta_story.ps1` (hermano de `ruta_mensaje.ps1`, no lo modifica). Los `data/stories/*.png`
están gitignored. `playwright` es dependencia **opcional** (`[project.optional-dependencies]
stories`): instalar con `uv sync --extra stories && python -m playwright install chromium`.

## Flujo de aprobación → WhatsApp (modo semi-automático activo)

Todo contenido pasa por este flujo antes de enviarse:
1. El comando genera el contenido.
2. Lo muestra al director para aprobación.
3. Pregunta: "¿Adjuntar chart de MT5?"
4. El director aprueba o pide ajustes.
5. **Al aprobar**: guardar automáticamente en `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt` y mostrar el texto listo para copiar.
6. El director copia y pega el texto en el grupo de WhatsApp.

**Regla de guardado**: después de cada aprobación, SIEMPRE guardar el mensaje final en `data/mensajes/` con la estructura **día → activo → tipo** (issue #45). Construir la ruta con el helper determinista `scripts\ruta_mensaje.ps1` (NUNCA armarla a mano):
```powershell
scripts\ruta_mensaje.ps1 -Fecha "2026-06-04" -Activo "USDCLP" -Tipo "dato_macro" -Hora "09-01"
# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt
```
El helper crea las carpetas y devuelve la ruta lista para `Write`. Si la pieza no tiene un activo protagonista (concepto, pregunta, cierre semanal, encuesta de la semana, earnings, paquete dominical), omitir `-Activo` y el helper la guarda en `_general/`. La hora `HH-mm` sale del reloj de Chile (regla canónica). Usar luego la herramienta Write sobre la ruta devuelta.

**Tipos de archivo** (carpeta `<tipo>`): niveles, dato_macro, noticia, alerta, encuesta, señal, concepto, pregunta, respuesta, cierre, earnings, postventa. La salida de `/apertura` usa tipo `niveles`.

**Modo ejecutivo (flag `ejecutivo`)**: aceptan el argumento `ejecutivo` (ej. `/lunes ejecutivo`, `/noticia ejecutivo`) **todos los comandos que producen un mensaje de cliente reenviable**: los 7 comandos de día, los comandos de tarea de Capa 2 (`/encuesta`, `/rencuesta`, `/apertura`, `/actualizacion`, `/dato_macro`, `/noticia`, `/señal`, `/alerta`, `/concepto`, `/pregunta`, `/respuesta`) y los de acción de Capa 3 (`/accion`, `/earnings`). Por cada pieza/mensaje de cliente generan, además del mensaje de cliente (idéntico, con todas las reglas de oro), un **guion de venta privado** para el grupo interno de ejecutivos (gancho + a quién, qué decir, manejo de objeciones, llamado a la acción), marcado `🔒 INTERNO · NO ENVIAR AL CLIENTE`. El guion se guarda con `ruta_mensaje.ps1` bajo el tipo `guion_<tipo>` (ej. `guion_niveles`, `guion_noticia`, `guion_señal`), mismo activo y hora que el mensaje de cliente. **No elegibles** (ignoran el flag): `/estado` (no envía nada), `/chart` (genera PNG, no texto), `/curriculo` (delega en `/rencuesta`/`/concepto`, que ya generan su guion) `/ventas` (su contenido ya es 100% interno para el equipo de ventas — es el HUB INTERNO por sí mismo, no necesita un guion adicional que lo envuelva) y `/postventa` (su contenido ya es 100% interno para el equipo de post-venta — mismo criterio que `/ventas`). Contrato único en `.claude/shared/modo_ejecutivo.md`.

**Convención de nombres de chart (issue #81)**: los PNG de `data/charts/` siguen el patrón único `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`, con el mismo `<activo_slug>` de `ruta_mensaje.ps1` (#45) — `lowercase(ticker_mt5)` sin `.spot`/`#`/`/` — y `<TF>` en mayúscula MT5 (`M15`/`H1`/`H4`/`D1`). Ej: `usdclp_H4_2026-06-07_11-45.png`. Los `data/charts/*.png` están gitignored.

**Nunca se envía nada al grupo sin aprobación explícita del director.**

**Nota**: Evolution API (Docker) está instalada y lista en `mcp/docker-compose.yml`. Cuando se resuelva la conexión WhatsApp/Baileys, el envío pasará a ser automático sin cambios adicionales.

## Slash Commands disponibles (26)

Invocar con `/nombre` desde Claude Code:

### Capa 1 — Comandos de día
| Comando | Cuándo usarlo |
|---------|---------------|
| `/domingo` | Paquete dominical: noticias fin de semana + preview semana + sesgo lunes + encuesta semana |
| `/lunes` | Paquete completo del lunes (resumen semanal + earnings + concepto + apertura + encuesta) |
| `/martes` | Operativa estándar martes (apertura + dato macro + encuesta precio) |
| `/miercoles` | Operativa miércoles + prioridad EIA de petróleo |
| `/jueves` | Operativa jueves + alerta Jobless Claims |
| `/viernes_am` | AM del viernes: 3 activos + NFP si aplica + encuesta precio del lunes |
| `/viernes_pm` | Cierre semanal por la tarde |

### Capa 2 — Comandos de tarea (ad hoc)
| Comando | Cuándo usarlo |
|---------|---------------|
| `/encuesta [tipo] [activo]` | Encuesta de sentimiento puro (sin precios ni educación). 3 tipos: `posicion`, `tendencia`, `movimiento`. Lo educativo migró fuera de `/encuesta`. |
| `/rencuesta` | Desarrolla didácticamente el tema de una encuesta y construye la malla de conceptos. `/rencuesta` (última encuesta), `/rencuesta [tema]`, `/rencuesta mapa` (vista de repaso). |
| `/curriculo` | Planifica el currículo educativo evolutivo (niveles + prerrequisitos), despacha conceptos en orden reutilizando `/rencuesta`/`/concepto` y mide el avance (4 métricas). Modos: `/curriculo`, `despachar`, `ruta`, `progreso`, `agregar`. |
| `/apertura` | Niveles técnicos interactivos: pregunta activo, temporalidad e indicador (RSI/ATR) por activo. Lo invocan los comandos de día en su PIEZA de apertura. |
| `/actualizacion` | Evolución del precio y reacción frente a niveles de la apertura |
| `/dato_macro` | Calendario del día → director elige dato a desarrollar |
| `/noticia` | Busca 3-5 noticias relevantes → director elige |
| `/chart` | Genera screenshot de MT5 con indicador y temporalidad a elección |
| `/story [tipo]` | Genera una Story de marca GI (imagen 1920×1080). `[tipo]` soportados hoy: `alerta`, `quote`, `breaking`, `encuesta`, `edu`, `flash`, `postventa`; demás plantillas en #111-#115. Ver sección "Stories GI". |
| `/señal` | Señal operativa (verifica límite 3/semana automáticamente) |
| `/alerta` | Detecta qué mueve el mercado ahora y genera alerta urgente |
| `/concepto` | Concepto educativo conectado a lo que pasó esta semana |
| `/pregunta` | Pregunta abierta para fomentar razonamiento del grupo |
| `/respuesta` | Responde una pregunta/comentario de cliente de forma complaciente y didáctica → guarda tipo `respuesta` |
| `/ventas` | Genera la "Oportunidad del Día" para el equipo de ventas interno (no el cliente final): noticia/evento más relevante traducido en entrada/TP/SL, ticket mínimo $5.000.000 CLP y temporalidad, en dos formatos (email + WhatsApp). No genera infografías ni envía automáticamente. |
| `/postventa` | Parte diario para el equipo interno de post-venta (no el cliente final): la consulta que va a generar el evento del día con su respuesta, 3 preguntas frecuentes redactadas para copiar, a quién contactar por segmento, acompañamiento de posiciones abiertas, rendición de lo dicho y límites de lo que no se promete. 100% interno, nunca se reenvía. |
| `/estado` | Dashboard del sistema (señales, charts, plan del día, MCPs) |

### Capa 3 — Acciones individuales
| Comando | Cuándo usarlo |
|---------|---------------|
| `/accion [TICKER]` | Análisis completo de una de las 13 acciones del catálogo |
| `/earnings` | Calendario de earnings de las 13 acciones para la semana |

## Estructura del proyecto
```
grupo-analisis-mercado/
├── README.md              ← introducción y referencia rápida
├── CLAUDE.md              ← este archivo (instrucciones para Claude Code)
├── docs/
│   ├── architecture.md    ← flujo del sistema, MCPs, aprobación, señales
│   ├── commands-reference.md ← referencia detallada de los comandos
│   ├── setup-guide.md     ← instalación paso a paso + troubleshooting
│   ├── activos-y-drivers.md  ← 20 activos con drivers y datos macro
│   ├── design/            ← diseños técnicos vigentes (ciclo Pulse) — incluye stories-gi/ y motor-como-cerebro-hub-gi
│   └── archive/           ← docs históricos de features ya implementadas (design/plan/superpowers)
├── .claude/
│   ├── commands/          ← 25 slash commands (invocar con /nombre)
│   │   ├── domingo.md
│   │   ├── lunes.md · martes.md · miercoles.md · jueves.md
│   │   ├── viernes_am.md · viernes_pm.md
│   │   ├── encuesta.md · rencuesta.md · curriculo.md
│   │   ├── apertura.md · actualizacion.md · dato_macro.md · noticia.md · chart.md · story.md
│   │   ├── señal.md · alerta.md · concepto.md · pregunta.md · respuesta.md · ventas.md · postventa.md · estado.md
│   │   └── accion.md · earnings.md
│   └── shared/modo_ejecutivo.md  ← contrato del flag `ejecutivo` (guion_ejecutivo.txt)
├── agents/                ← prompts de sub-agents
│   ├── recolector.md · analista.md · redactor.md
├── config/                ← configuración del sistema
│   ├── activos.json       ← 22 activos: forex + índices + 13 acciones
│   ├── drivers.json · drivers_indices_sectores.json
│   ├── agenda_semanal.json · feriados_bolsa.json
├── scripts/               ← scripts auxiliares
│   ├── story_render.py    ← renderer de Stories GI (payload JSON → HTML → PNG con Playwright)
│   └── hora_chile.ps1 · ruta_mensaje.ps1 · ruta_story.ps1  ← helpers deterministas (hora Chile, ruta de guardado)
├── templates/             ← templates de mensajes WhatsApp
│   ├── encuesta_tendencia.txt · encuesta_posicion.txt · encuesta_movimiento.txt
│   ├── concepto_didactico.txt · guion_ejecutivo.txt
│   ├── ruta_curriculo.txt · dashboard_metricas.txt · mapa_conceptos.txt
│   ├── ventas_email.txt · ventas_whatsapp.txt
│   └── stories/           ← snapshot de marca GI (alerta.html + fonts/)
├── conceptos/             ← notas canónicas de conceptos educativos (malla /rencuesta)
│   ├── README.md · stop-loss.md
├── data/                  ← datos persistentes
│   ├── historial_senales.json · historial_encuestas.json · historial_ventas.json
│   ├── mapa_conceptos.json · glosario_siglas.json
│   ├── curriculo.json · entregas_educativas.json · metricas_educativas.json
│   └── charts/ · mensajes/ · stories/  ← generados (gitignored)
├── mql5/                  ← Service MQL5 (ChartObjectsExporter) + archive/ (CalendarExporter, deprecado)
└── mcp/
    ├── mcp_config.example.json ← template sin credenciales (en git)
    └── mcp_config.json         ← config real con API keys (gitignored)
```
