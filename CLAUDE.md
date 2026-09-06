# Grupo de Análisis de Mercado — Sistema Automatizado

## Contexto
Este proyecto automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El usuario es el director de trading. Los sub-agents actúan como analistas de mercado y recolectores de información.

> [!CRITICAL]
> **GUARDRAILS DE INTEGRIDAD DE DATOS Y COMPOSICIÓN EDITORIAL:**
> 1. **CERO HARDCODING DE PRECIOS Y COTIZACIONES (REGLA 1):** Queda estrictamente prohibido escribir números de precios, cotizaciones, variaciones porcentuales o niveles técnicos "a mano" o calculados mentalmente en scripts de Stories, HTMLs o informes Markdown. Todos los precios deben ser leídos en tiempo de ejecución desde MetaTrader 5 / MCP `market-data` (`get_asset_levels`, `latest_prices_summary.json`). Para tickers con sufijo del broker, usar siempre el símbolo exacto del catálogo (`US100.spot`, `US500.spot`, `US30.spot`, `WTI.spot`, `BRENT.spot`, `GER40.spot`, `COPPER`, `USDCLP`, `XAUUSD`, `USDJPY`).
> 2. **PROHIBICIÓN DE TRUNCADO DE DÓLARES EN SHELL (REGLA DE ESCRITURA):** Al generar o guardar archivos `.txt` o mensajes con símbolos de moneda (`$`), queda prohibido usar double-quotes o here-strings `@"..."@` en PowerShell porque la shell interpreta `$931` o `$4` como variables vacías y trunca el precio. Toda escritura de archivos de texto con precios DEBE realizarse mediante Python (`Path.write_text(..., encoding="utf-8")`) o single-quoted here-strings `@'...'@`.
> 3. **COMPOSICIÓN OBLIGATORIA DE INFORMES PDF (REGLA 2):** Queda estrictamente prohibido generar PDFs institucionales a partir de markdowns planos improvisados. Todo informe PDF DEBE seguir la arquitectura canónica (`pipeline_informe.py` + `grafico_informe.py` + `generar_pdf.py`), incluyendo los banners gráficos vectoriales a 300 DPI por activo, la tabla de curva soberana de 4 columnas en notación chilena y la estructura pedagógica de 3 capas (qué pasa, qué significa, qué NO hacer).
> 4. **PROHIBICIÓN TOTAL DE MODELOS DE DIFUSIÓN (REGLA 0):** Prohibido usar `generate_image` o modelos de difusión. Toda pieza visual es código HTML + CSS + Playwright.

El grupo es para clientes y a la vez alinea al equipo: los ejecutivos se mantienen al tanto del
mercado y replican el lenguaje simple con sus carteras, y los analistas verifican que lo que se
comunica sea consistente. La meta de fondo es pasar de un modelo de señales a uno de análisis y
educación, donde el cliente aprende a leer el mercado: eso es lo que mueve satisfacción,
retención y NPS, y lo que reduce churn.

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
- **Acciones (rotación por análisis previo)**: además de los 4 activos base, la rotación diaria puede incluir 1-2 acciones del catálogo elegidas por análisis previo. Las elige el `Score_GI` del escáner como a cualquier otro activo del universo.

### El catálogo técnico es más amplio que la rotación diaria
`config/activos.json` cubre 38 tickers, e incluye desde el 2026-08-25 cinco ETF (`QQQ.US`, `SPY.US`, `GLD.US`, `IWM.US`, `SOXX.US`) y cinco criptos nuevas (`ETHUSD`, `SOLUSD`, `LTCUSD`, `ADAUSD`, `DOGUSD`). Todos entran con `rotacion_diaria: false`: **la rotación diaria de 2-3 activos no cambia**, y estos existen para que `get_asset_levels` y `get_symbol_spec` puedan responder por ellos cuando el director los pida.

Tres cosas que conviene no volver a averiguar:
- **Los ETF llevan sufijo `.US`, no prefijo `#`** (el `#` es de las acciones). El broker **no ofrece** `TLT` ni `SMH`: `SOXX.US` es el equivalente de SMH, y la duración de deuda se lee de la curva con `get_curva_tasas`, no como activo operable.
- **La cripto de Dogecoin es `DOGUSD`**, no `DOGEUSD`. `ADAUSD` y `DOGUSD` cotizan con 4 decimales.
- **Entrar al catálogo técnico no es entrar al Playbook.** Un ETF tiene niveles, indicadores y especificaciones de contrato, pero no tiene ficha operativa, régimen R0-R4, sesgo score ni setups permitidos: ese conjunto sigue siendo el de `bias_reader.VALID_SYMBOLS` (`USDCLP`, `XAUUSD`, `WTI`, `BRENT`, `US100`), porque cada ficha del Playbook cita literatura académica y elasticidades medidas.

El universo completo del terminal (32 pares FX, 86 acciones, 13 ETF, 6 criptos) está capturado en `calculadoras excel/Simulador GI Real.xlsx`, hoja `Datos`, que genera `scripts/simulador_gi.py` con `mt5.symbols_get()`. Es la fuente para verificar si un instrumento existe y con qué `digits`, sin abrir MT5.

## Estructura diaria obligatoria (lunes a viernes)

> **Orden canónico (issue #43)**: el dato/noticia del calendario va PRIMERO y los niveles después. Lo cumple `contexto_macro_grupos.py`, que arma el mensaje de cada canal con la agenda del día arriba y la lectura técnica debajo.

### 1. Noticia relevante del calendario económico
- 1 noticia o dato del día que impacte directamente a alguno de los activos
- Explicar simple: qué es, a qué hora sale, qué se espera y cómo podría reaccionar el activo
- Fuente oficial: calendario de Investing.com
- Hora siempre en hora Chile (CLT/CLST)

### 2. Niveles técnicos del día
- Enviar niveles en temporalidades 4H, 1H o 15M
- Cubrir 2 o 3 activos por día (rotar entre USD/CLP, Oro, WTI, US100)
- Indicar: soportes, resistencias, zona de interés y posible sesgo
- La temporalidad se elige por activo según su volatilidad (nunca se asume 4H fijo). Los niveles se presentan como **lectura/marco temporal**, no como señal de operativa.

### 3. Drivers del activo
- Explicación corta de los drivers que están moviendo al activo
- Si hay información relevante durante el día (declaraciones, datos sorpresivos, eventos geopolíticos), informar de inmediato

## Reglas de temporalidad
Cada análisis indica explícitamente su temporalidad con un rango cuantificado (prohibido usar "corto" sin número — issue #44):
- **15M** → scalper (minutos a 1-2 h) — alta rotación, movimientos rápidos del día
- **1H** → intradía (dentro de la jornada) — movimientos del día, confirmar entradas finas
- **4H** → swing de jornada (1-3 días) — tendencia del día y operativas de varias horas
- **1D** → posicional (días a semanas) — lectura general del activo

**La fuente única de las 4 etiquetas es `pipeline_carrusel.MARCOS_CANONICOS`**, y un test de contrato la compara contra la tabla de `.claude/commands/story.md`. Hasta el 2026-09-04 este párrafo declaraba fuente única a `.claude/commands/apertura.md`, **que ya no existe**: ese comando se retiró y la tabla quedó viviendo solo en markdown, en dos copias, justo antes de que el código necesitara una tercera.

**Justificar la temporalidad por la volatilidad del activo (OBLIGATORIO)**: cada activo tiene `volatilidad` y `nota_volatilidad` en `config/activos.json`, y el mensaje de niveles cierra con `⏱️ *Temporalidad*` más la línea `💡 Por qué [TF] acá: …`, que explica en lenguaje novato por qué ese marco encaja con lo que ese activo se mueve.

**Esto estuvo declarado y sin implementar desde el issue #44.** El 2026-09-04 se descubrió que el token `por_que_temporalidad` existía en **un solo lugar del repo: este archivo**, y que dos piezas habían salido sin el bloque. Faltaban tres cosas a la vez: los campos no estaban en las 14 acciones, `cargar_universo` no los copiaba (así que el generador nunca los veía) y el mensaje no emitía la línea.

Tres reglas que salieron de arreglarlo, y que imponen tests:

1. **Toda nota nombra el marco que el carrusel publica.** Nueve notas recomendaban otro marco o ninguno, y publicadas se contradecían solas: *"Por qué 1H acá: … 4H da la lectura más limpia"*. Pueden (y deben) nombrar el marco más amplio, pero tienen que explicar también el que sale.
2. **Toda nota habla de marcos, no de drivers.** Tres notas (GBP/USD, cobre, bitcoin) eran descripciones de lo que mueve al activo, sin nombrar ninguna temporalidad: la línea prometía una justificación y entregaba otra cosa.
3. **El carrusel publica H1 y eso no se toca acá.** La selección de marco por activo es otro trabajo; lo que corresponde es que el texto justifique el marco que de verdad sale. Prometer selección por activo sin implementarla sería repetir el defecto de esta sección.

Ejemplo obligatorio: "Niveles en 15M, marco scalper (minutos a 1-2 h)"

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

### Guardrail Anti-Anacronismos y Modo Anticipación (OBLIGATORIO)
Queda **estrictamente prohibido** redactar eventos futuros en tiempo pasado (ej. "tras la asimilación de los discursos de Jackson Hole", "luego del dato de IPC") si dicho evento aún no ha ocurrido según el reloj real de Chile.
- **Eventos Futuros / Próximos:** Se redactan exclusivamente en **Modo Anticipación** ("en la antesala de...", "a la espera de los discursos previstos para mañana...", "el mercado aguarda la publicación...").
- **Validador Automático:** `generar_pdf.py` y `pipeline_informe.py` ejecutan automáticamente `scripts/validar_consistencia_temporal.py`. Si detectan discrepancia de fecha o anacronismos en el texto, el proceso aborta inmediatamente (*Fail-Fast*).

## Cadencia

No hay agenda por día de la semana ni comandos de día: la producción se rige por **el carrusel y
el informe**, que detectan la sesión y la hora reales. El carrusel se puede correr en cualquier
momento; el informe tiene dos momentos (apertura y cierre). Las encuestas se mandan cuando el
director lo decide, siempre después de que el canal recibió contexto para votar informado.

## Producción diaria en 3 tandas (escáner + carrusel + informe)

Sistema de producción estructurado que **complementa** la agenda de arriba, no la reemplaza:
la rotación diaria de 2-3 activos y las piezas de la estructura obligatoria siguen igual. Lo
que agrega es una selección **objetiva** del universo completo, para que la elección de qué
activo comunicar no dependa de a quién se le ocurrió primero.

### Producción diaria responsiva (escáner + carrusel + informe)

| Momento / Sesión | Ventana (Nueva York) | Comando | Salida |
|---|---|---|---|
| Apertura | 08:30 aprox. | `/informe apertura` | PDF institucional A4 + mensaje |
| Responsivo 24h | Cualquier hora | `/carrusel` | Hasta 3 Stories + mensaje índice (detección automática de sesión y hora real) |
| Pre-cierre | 16:45 (cierre + 45 min) | `/informe cierre` | Mensaje con gráfico, **sin PDF** |

**El ancla es la hora de Nueva York y se comunica en hora real de Chile.** El escáner detecta
automáticamente la sesión activa (Asiática, Europea, Apertura Wall Street, Rotación de Tarde,
Cierre o Fin de Semana), permitiendo ejecutar `/carrusel` en cualquier momento. La hora real
de ejecución queda estampada con fidelidad en los payloads y en el mensaje índice. Adicionalmente,
el escáner excluye activos publicados en corridas previas de hoy para evitar redundancia.

**El informe de apertura lleva un gráfico por activo.** `scripts/grafico_informe.py`
dibuja la serie real del terminal (cierres de `serie_mt5.py`, niveles de `analizar_activo`)
con sus medias de 50 y 100 días en formato banner institucional de **7.2 × 2.82 pulgadas a 300 DPI**, trazando obligatoriamente como líneas horizontales todo nivel de soporte/resistencia o Fibo mencionado en el texto, y el pipeline lo referencia bajo el bloque de cada activo.
Nunca se dibuja un sustituto: sin terminal, el informe sale sin imágenes y lo dice en los
avisos. Es la diferencia con `scripts/generar_graficos_drivers.py`, que tiene las series
escritas a mano y produce piezas de aspecto institucional a partir de números que nadie
midió. Requiere `uv sync --extra informe` (matplotlib es opcional, mismo criterio que
`stories`). Brent **sí** tiene ticker (`BRENT.spot`, verificado contra la cuenta 51492 el
2026-09-02): el mapeo lo apuntaba a `None` afirmando que el broker no lo ofrecía, y
no era cierto. Lo que Brent no tiene es `brent.jpg`, así que queda fuera del escáner
hasta que exista la imagen, pero ya recibe niveles y gráfico. El mapeo
Playbook → ticker MT5 vive en `bias_reader.TICKER_MT5`, que es también el que usa el
escáner.

**Un PDF al día, no dos.** La skill `generar-reporte-editorial` reserva el PDF
"estrictamente" para hitos de alta densidad y manda chat-first para piezas tácticas, por
fatiga de descargas. La apertura sí va en PDF; el cierre es mensaje con gráfico.

### Un solo reloj: `config/agenda_mercado.json`

Las ventanas de sesión, los anclajes de tanda y los **momentos del día** viven en un solo
archivo y se leen con `scripts/agenda_mercado.py`. Antes las ventanas estaban en una cadena
de `elif` dentro de `detectar_sesion`, con los minutos sumados a mano, y los anclajes en otra
tabla del mismo módulo. El reloj de sucesos habría agregado un tercer lugar declarando el
mismo hecho, y **dos relojes divergen siempre**: es el defecto recurrente del repo.

Tres invariantes las imponen tests, no la buena intención:

1. **Cada minuto del día hábil pertenece a exactamente una sesión.** Un hueco deja al escáner
   sin sesión; un solape hace que el resultado dependa del orden del JSON, que es un
   accidente esperando a que alguien reordene el archivo.
2. **Las ventanas no pueden volver al código del escáner.** Un test lee su fuente y falla si
   aparecen los minutos escritos a mano.
3. **El desfase con Chile no está escrito en ninguna parte.** El ancla es Nueva York y la hora
   se comunica en hora real de Chile. Chile y EE.UU. cambian de horario en sentido opuesto,
   así que el desfase se mueve dos veces al año: hoy es +0 h y **desde el 2026-09-06 pasa a
   +1 h**. Un offset fijo es el error de ±1 h del issue #38.

**Los momentos separan por clase de activo, y esa es la decisión de fondo.**

| Momento | Hora (NY) | Clases | Por qué |
|---|---|---|---|
| `premercado_fx` | 08:30 | `forex_commodities` | Es la hora del dato de empleo e inflación de EE.UU. Divisas, oro y petróleo cotizan 24 h, así que ya tienen precio formado y el nivel es real. |
| `cripto` | 09:00 | `crypto` | **Medido**, no supuesto. Ver abajo. |
| `apertura_indices` | 10:00 | `indices`, `acciones`, `etfs` | La bolsa abre 09:30 y la primera media hora es el barrido de órdenes de apertura, donde el rango del día todavía no existe. |

Publicar niveles de índices a las 08:30 es **publicar el cierre de ayer con fecha de hoy**:
esos activos no tienen precio hasta que abre la bolsa. Por eso la separación no es una
preferencia editorial, es una condición del dato.

La tolerancia es de **20 minutos y solo hacia adelante**. El disparo del sistema operativo,
la lectura de precios y el render se llevan minutos, así que sin ventana de gracia un momento
se pierde por llegar dos minutos tarde; y disparar el de las 08:30 a las 08:15 publicaría
niveles anteriores al dato que motiva la hora.

**La cripto se mueve en la mañana americana, no en Asia.** Se midió el 2026-09-04 sobre 90
días de velas H1 en BTC, ETH, SOL y LTC (mediana del rango por hora, solo días hábiles):

| Bloque (hora NY) | BTC | ETH | SOL | LTC |
|---|---|---|---|---|
| Asia 18–02 | 1,01x | 0,98x | 0,94x | 0,97x |
| Europa 03–08 | 0,98x | 0,96x | 0,90x | 0,98x |
| **NY mañana 08–12** | **1,80x** | **1,65x** | **1,52x** | **1,49x** |
| NY tarde 12–16 | 1,23x | 1,17x | 1,16x | 1,14x |

El máximo está en 09:00–10:00, donde BTC llega a **2,09x** su mediana diaria. La sesión
asiática está plana y Europa también: **la hipótesis del rollover asiático era falsa.** Va a
las 09:00 y no a las 10:00 solo para no chocar con el momento de los índices, porque cada
momento produce su propia tanda.

Dos cosas más que salieron de esa medición y conviene no volver a averiguar:

1. **MT5 devuelve las marcas de tiempo en hora del SERVIDOR, empaquetadas como si fueran un
   timestamp UTC.** Interpretarlas como UTC desplaza la serie entera por el offset del broker.
   La primera corrida de esta medición dio el máximo en las 06:00 de Nueva York, que habría
   apuntado a la apertura de Londres; el servidor corre en **UTC−4** y el máximo real está
   cuatro horas después. El offset se mide comparando `symbol_info_tick().time` contra
   `datetime.now(timezone.utc)`, y `tools/symbol_spec.py` ya lo trata correctamente como
   `server_naive`.
2. **El fin de semana la cripto está más quieta, no más activa**: 0,76x a 0,85x del día hábil.
   La sesión `fin_de_semana` existía en parte pensando en ella, y el dato no respalda esa idea.

`clases_sin_momento` queda vacía, y la lista se conserva porque un test exige que toda clase
del universo esté asignada a un momento **o** declarada ahí. Es lo que impide que una clase
nueva se quede fuera del reloj en silencio.

> **Ojo, no confundir con `config/agenda_semanal.json`**, que es la agenda por día de la
> semana de antes del rediseño y describe una cadencia que ya no existe (`apertura_mercado`,
> `resumen_semanal`, los comandos de día). `/estado` y `docs/architecture.md` todavía la
> citan. `agenda_mercado.json` es la vigente.

### El reloj de sucesos: latido del sistema, decisión en Python

`scripts/reloj_gi.py` es quien decide si a alguna clase de activo le toca salir.
`scripts/instalar_reloj.ps1` registra el latido en el Programador de tareas (cada 15 min, sin
parámetros muestra qué haría y **no instala nada**).

**La trampa que esto evita.** El Programador de tareas dispara en hora **local**. Una tarea a
las 08:30 de Chile es 08:30 de Nueva York hoy y **06:30 de Nueva York en noviembre**: dos
horas antes del dato que justifica la hora. La tarea seguiría corriendo puntual y publicando
el cierre de ayer. Por eso **el agendador no sabe nada de mercados**: late, y Python decide
leyendo la agenda y convirtiendo en ese instante.

Cuatro decisiones que lo sostienen:

1. **Idempotencia por momento y por día**, en `data/.reloj_disparos.json` (gitignoreado: es
   estado generado, no historia editorial). El latido puede pasar cuatro veces por la ventana
   de gracia de 20 min y la pieza sale una sola vez. Y hace **recuperable** la noche en que
   Chile entra en horario de verano, donde una hora local simplemente no existe: una tarea
   anclada a esa hora no dispararía nunca, y acá el momento sale en el siguiente latido.
2. **Un momento que falló sigue pendiente.** MT5 puede no estar conectado en ese latido;
   anotar el disparo igual perdería la pieza por el día entero. Solo se anota si al menos una
   corrida terminó bien.
3. **El reloj solo prepara.** Corre `pipeline_carrusel.py --preparar --grupo <canal>` y nada
   más. Que un proceso automático pueda publicar en un canal es justamente lo que el flujo de
   aprobación prohíbe, y **hay un test que falla si alguien conecta el envío ahí**.
4. **Los canales de un momento se derivan del mapeo real** de activo a canal, recorriendo el
   universo del escáner. Una lista de canales por momento sería otro contrato por nombre.

**Anclado al mercado, con el cambio narrado** (decisión del director, 2026-09-04). La hora
sigue al mercado y la hora chilena drifta; cuando el desfase cambia, el reloj levanta el aviso
y deja el mensaje listo para que el director lo revise y lo mande. Se descartó anclar a hora
chilena fija **midiéndolo**: la pieza de índices habría salido en noviembre a las 08:00 de
Nueva York, hora y media antes de la campana, publicando el cierre de ayer con fecha de hoy.

| Fecha | Desfase | premercado_fx | cripto | índices |
|---|---|---|---|---|
| hasta el 5 sep 2026 | NY+0 | 08:30 CL | 09:00 CL | 10:00 CL |
| 6 sep 2026 | NY+1 | 09:30 CL | 10:00 CL | 11:00 CL |
| 1 nov 2026 | NY+2 | 10:30 CL | 11:00 CL | 12:00 CL |
| mar 2027 | NY+1 | 09:30 CL | 10:00 CL | 11:00 CL |
| abr 2027 | NY+0 | 08:30 CL | 09:00 CL | 10:00 CL |

**El aviso nombra al país que de verdad movió su reloj.** En septiembre es Chile entrando en
su horario de verano; en noviembre es **Estados Unidos saliendo del suyo**. Decir "horario de
verano de Chile" en noviembre sería contarle al cliente algo que no pasó, así que
`quien_cambio` lo deduce comparando el desplazamiento de cada zona con el de una semana antes.

Y como el aviso lo lee el cliente, se le aplican las reglas de texto de cliente: los nombres
de los momentos van **acentuados** en el config porque salen publicados, los momentos se
listan en **orden de reloj** y no en el del archivo, y no lleva guion largo ni cifras de precio.

**El campo `zona` por momento** permite que un momento se ancle al reloj del mercado que lo
mueve. Hoy los tres van a Nueva York. Un premercado del USD/CLP tendría que ir anclado a
Santiago, porque con el desfase en su máximo las 08:30 de Nueva York caen hora y media
**después** de que Santiago abrió, y dejaría de ser premercado. El invariante que lo hace
seguro: **un test verifica que ningún par de momentos caiga dentro de la tolerancia uno del
otro, en las tres configuraciones de desfase del año** (si se pisaran, el decisor dispararía
uno y perdería el otro en silencio).

### El `Score_GI` y sus gates

`scripts/screener_gi.py` puntúa cada activo del catálogo sobre 100:

| Factor | Tope | De dónde sale |
|---|---|---|
| Técnico (quiebre) | 35 | `ema_20`, `ema_50/100`, `s1/r1` de `get_asset_levels` |
| Catalizador macro | 25 | `obtener_calendario_macro` (impacto **alto**) + `get_curva_tasas` |
| Espacio ADC+ATR | 20 | `atr_14` de H1 contra `rango_hoy` / `atr_restante_14` de D1 |
| Momentum | 20 | `adx_14`, `rsi_14`, `macd_hist` |

Los rangos de puntos **son** la ponderación: `Score = T + M + C + F`. No se multiplican por
pesos, porque los factores ya vienen escalados a su máximo y hacerlo dejaría el techo real en
26,5 sobre una escala de 100.

**Seis gates se aplican ANTES de puntuar, y son prohibiciones, no puntos:**

1. **Feriado de la bolsa** del activo (`config/feriados_bolsa.json`).
2. **Blackout por calendario** (skill cuantitativa §4: FOMC −30/+75 min, NFP e IPC de EE.UU.
   −15/+30, RPM y Imacec de Chile, BoJ). Ojo: `obtener_calendario_macro` ya entrega la hora en
   America/Santiago, así que la ventana se compara directo — volver a convertir produce el
   desfase de ±1 h del issue #38.
3. **Prohibición del Playbook** para los 5 activos con ficha, leída de `setups_prohibidos`.
   Solo bloquea si apunta en la misma dirección que la lectura técnica: que esté prohibido
   comprar agresivamente no impide comunicar una caída.
4. **Agotamiento**: ATR diario consumido sobre 90%.
5. **Confianza del modelo** (`gate_confianza`): estuvo sin documentar hasta el 2026-09-04, así
   que la cuenta de "cuatro gates" llevaba tiempo desactualizada. Es el único con
   `publicable: False` en el suplemento junto al del snapshot: un problema nuestro de datos no
   es contenido para el cliente.
6. **Banda contra vela típica** (`gate_banda`): excluye cuando la vela típica cubre la banda
   entre soporte y resistencia. Ver abajo.

**El gate de banda, y por qué el agotamiento no lo cubría.** Tener recorrido disponible no dice
nada sobre si los bordes se sostienen: son dos preguntas distintas y el 2026-09-04 hubo que
aplicar esta a mano cuatro veces. Litecoin cubría **3,2 veces** su banda, Dogecoin 1,8 y el
S&P 500 1,03, con banda de 16,54 puntos contra una vela típica de 17,00. Publicar esos niveles
es entregar ruido con forma de estructura, y el cierre canónico de la pieza los presenta como si
el precio fuera a respetarlos.

Umbrales fijados por el director el 2026-09-04: **excluye desde 1,00x y avisa entre 0,70x y
1,00x**. La zona de aviso no detiene la pieza, viaja en la selección como `banda_estrecha` y sale
en los avisos del escáner. La "vela típica" es `1,5 × ATR(H1)`, **la misma cifra** que la pieza
publica como "Volatilidad típica": juzgar con otro número dejaría al gate midiendo distinto de lo
que el cliente lee.

**El respaldo por ATR se trata aparte, y esa es la parte que no era obvia.**
`_get_support_resistance` cae a `precio ± ATR` cuando no encuentra swings del lado que necesita.
Es una red de seguridad correcta, pero ese borde **no es un nivel**: es una distancia calculada
con nombre de soporte. Y cuando ambos lados caen, la banda vale **2 ATR exactos por
construcción**, así que el ratio da siempre 0,75 y no mide nada: un gate que no lo distinguiera
avisaría siempre y siempre por la misma razón artificial. Por eso `analizar_activo` declara
`niveles_origen` por lado (`swing` o `atr`) y el gate le da su propio motivo. Los cuatro lados
caen por separado: se puede tener una resistencia real con un soporte sintético.

Un setup prohibido puede puntuar alto, y con scoring puro ganaría la tanda. Por eso el filtro
va antes.

**El escáner informa el motivo de cada exclusión y arrastra sus avisos.** Si el calendario no
respondió, dice que no pudo verificar blackouts en vez de reportar cero exclusiones. Un
escáner que descarta en silencio no es auditable.

**Y un gate apagado también lo dice.** El de agotamiento es el único que se puede desactivar,
y solo con `--forzar`: el escáner entonces estampa el aviso de que el espacio proyectado no
está verificado. **`--grupo` acota el universo y nada más.** Hasta el 2026-09-03 también
apagaba ese gate sin decirlo, y por eso el canal de forex salió con tres piezas cuyo
recorrido diario estaba consumido al 93 %, 290 % y 115 %, con el escáner reportando cero
exclusiones porque no las hubo. Con el gate encendido ese mismo canal devuelve
**"ningún activo puntuó sobre 0: no hay tanda que publicar. Es un resultado válido, no una
falla"**, que es la respuesta correcta y la que el manual del comando ya exigía.

### Un canal vacío se suplementa con el motivo por el que quedó vacío

**El motivo ya es contenido.** El 2026-09-03 el canal de divisas quedó en cero porque sus
cuatro activos habían consumido su recorrido del día, con el USD/JPY al 290 %. Eso es una
lectura de mercado, no un premio de consuelo, y explica algo que el cliente necesita
entender: que no operar también es una decisión.

Y hay una razón **estructural** para que esto haga falta: el recorrido disponible es
`ATR − rango_hoy`, una función que **solo baja** con el día. Por construcción, un sistema
cuyo criterio de selección exige espacio tiene su mejor momento al abrir y se apaga solo.
A las 10:24 de ese día había 4 activos de forex entre 93 % y 290 %; a las 12:11 había 15
excluidos en todo el universo. **El gate está bien y lo que falta es otro eje de contenido
para la tarde.**

`scripts/suplemento_canal.py` lo resuelve leyendo las exclusiones que el escáner ya
escribió, no generando contenido:

| Motivo del gate | Categoría | Concepto que enseña |
|---|---|---|
| ATR diario consumido | `recorrido_agotado` | `volatilidad-atr` |
| Blackout por calendario | `dato_en_curso` | `precio-descontado` |
| Prohibición del Playbook | `setup_prohibido` | `riesgo` |
| Feriado de bolsa | `mercado_cerrado` | `temporalidades` |

**El concepto lo elige el motivo, no el azar**, así la parte educativa queda pegada a lo que
de verdad pasó en vez de ser una cápsula suelta. Hay contrato de nombres: todo motivo que el
escáner pueda emitir tiene categoría, o está declarado `publicable: False`.

Cuatro reglas que lo mantienen del lado del contenido y no del relleno:

1. **Solo cubre canales VACÍOS.** Un suplemento junto a piezas de activo sería exactamente
   el relleno que el manual prohíbe. Su valor está en aparecer cuando no hay nada más.
2. **Un problema nuestro de datos no es contenido.** La confianza baja del modelo o un fallo
   del analizador dejan al canal **sin** suplemento: publicar "no pudimos leer el activo" no
   le sirve a nadie y suena a excusa.
3. **No promete niveles.** El cierre canónico de tres escenarios necesita soporte y
   resistencia; sin ellos, prometerlos sería inventarlos. Cierra con el CTA al analista.
4. **Es solo texto, por fase.** Las plantillas educativas se retiraron y el estándar sale del
   brand kit, así que primero se mide si el canal engancha y solo después se le pide una
   pieza visual. El despacho lo manda con `enviar()` porque `piezas_del_grupo` recorre los
   PNG y el suplemento no tiene.

**La ventana anti repetición.** Un concepto no vuelve al mismo canal antes de **14 días**,
y el historial vive en `data/historial_suplementos.json`, **versionado** igual que
`historial_senales.json`: es historia editorial de lo que el cliente ya leyó, no un archivo
generado. Tres decisiones que conviene no revertir:

- **La ventana es por canal**, porque cada uno tiene su propia audiencia.
- **Si el concepto está en cooldown se cae el concepto, no la pieza.** La cifra del estado
  ES la novedad: hoy el USD/JPY al 290 % y mañana otra. Lo que se gasta con la repetición es
  la parte educativa.
- **Se anota al preparar, no al despachar.** Una tanda preparada y descartada gasta la
  ventana igual, y ese error va hacia el lado seguro: repetir de menos, no de más.

Catorce días porque hay seis conceptos técnicos aplicables: con menos, un canal que se vacía
seguido agota el repertorio antes de que nadie lo haya olvidado.

### La noticia oficial: oficial no es relevante

Sobre el suplemento se apoya un escalón más, **estrictamente aditivo**:
`scripts/noticia_oficial.py` busca la última nota de una fuente oficial que toque un activo
del canal. Si la encuentra, `--preparar` la deja en `<canal>/_noticia.json` y el **comando**
la traduce y la antepone al rendir; si no la encuentra, el canal conserva su suplemento de
estado y no se pierde nada.

**El núcleo del módulo es descartar, no descargar.** El 2026-09-03 la nota más fresca de la
EIA era *"Weekly average load in ERCOT continues near record high"*: carga eléctrica en
Texas. Oficial, del día, y sin ninguna relación con el petróleo. Un filtro de frescura sin
filtro de relevancia la habría mandado al canal de metales y energía justo el día en que ese
canal quedó vacío. Tres reglas salen de ahí:

1. **La relevancia se decide en el TITULAR, no en el cuerpo.** La descripción de casi
   cualquier nota trae una línea de contexto donde cabe la palabra *oil* o *inflation*:
   buscar ahí vuelve el filtro decorativo.
2. **En los bancos centrales la relevancia la da quién habla.** Un discurso de Lagarde mueve
   el euro aunque el titular no nombre ningún activo, así que el vocabulario incluye a los
   oradores del directorio.
3. **El URL no tiene ventana.** Que un concepto vuelva a los 14 días es refuerzo; que vuelva
   la misma noticia es un error visible desde afuera. Se comparte
   `data/historial_suplementos.json` con `tipo: "noticia"`.

Ventana de frescura: **72 h**, con la fecha siempre a la vista en el mensaje. Es lo que hace
honesto publicar algo de anteayer; a una semana ya no es noticia.

**Las fuentes que responden, medidas el 2026-09-03:**

| Fuente | Feed | Cadencia | Canal |
|---|---|---|---|
| EIA | `rss/todayinenergy.xml` | ~3/semana, 3 de 12 tocan crudo | metales y energía |
| BCE | `rss/press.html` | ~4/semana, discursos del directorio | divisas |
| Fed | `feeds/press_monetary.xml` | ~2/mes | divisas, índices |

El feed general de la Fed (`press_all.xml`) **queda fuera a propósito**: sus últimas piezas
eran sanciones y aprobaciones bancarias, que no le importan a nadie acá. Y tres fuentes no
se pueden leer: el Tesoro de EE.UU. responde 404, la BLS y la OPEP responden 403 al bot, y
el Banco Central de Chile devuelve HTML en la ruta de su RSS.

**El flujo relevante combinado es de una nota cada dos o tres días, y eso está bien.** Esto
no cubre los canales todos los días ni pretende hacerlo: el piso confiable sigue siendo el
suplemento de estado más concepto. Si algún día hace falta cobertura diaria de noticias, la
fuente no puede ser RSS oficial, y ahí ya no sería "fuente oficial".

**El titular es un campo editorial.** Viene en inglés y `--preparar` es Python puro, así que
`bloque_noticia(noticia, titular_es)` **lanza** con el titular vacío, mismo contrato que el
resto del pipeline. Y ninguna cifra sale de la noticia: los precios y niveles salen del
terminal (regla 1), siempre.

### El reparto entre script y comando

Los pipelines producen los **datos**; el texto lo escribe el comando. `pipeline_carrusel.py`
y `pipeline_informe.py` tienen dos pasos (`--preparar` y `--rendir`) y el segundo **se
detiene** si un campo editorial quedó vacío, por la misma razón que el renderer falla ante
una imagen inexistente: una pieza a medias que sale sin avisar llega al cliente.

**Y el freno vale para las DOS rutas de render, que es lo que no era obvio.** El despacho
vuelve a rendir justo antes de enviar, y esa ruta no tenía el guardia: `_refrescar_y_rendir`
hacía `pop("_pendiente_editorial")`, **descartando la marca que existe justamente para
frenar**. Así que el único camino sin freno era el que llega al cliente. Se descubrió el
2026-09-04 en un `--dry-run`, con la pieza de Solana rindiéndose con titular y párrafo
vacíos y el despacho reportando dos piezas listas.

La fuente única es `exigir_texto_editorial`, que reciben ambas rutas, y **hay un test de
contrato que falla si alguna deja de llamarla**: dos implementaciones del mismo freno
divergen, y eso ya es el defecto recurrente del repo. El guardia del despacho corre **antes**
de leer el mercado, porque el payload en disco ya dice lo que falta y gastar una lectura del
terminal para descubrirlo es trabajo perdido.

**Lo que el guardia no hace es validar la tanda entera al empezar.** Aborta en el canal donde
encuentra el hueco, así que los canales anteriores ya salieron. El daño queda acotado por la
bitácora de despachos, que es exactamente para eso: al arreglar el texto y reanudar, lo
entregado no se repite.

### El despacho: un lote por canal, rendido justo antes de salir

`pipeline_carrusel.py --despachar <tanda>` cierra el ciclo. Dos decisiones lo definen:

**Una pieza por acción, y el texto SIEMPRE antes del adjunto.** El campo de pie del
editor de medios **tope en 1.024 caracteres**, y `insert_text` de una línea que no cabe
se rechaza **entera** mientras el salto de línea que la sigue sí entra. Así que el
mensaje no llega cortado al final: llega con **renglones ausentes** y su espacio en
blanco, y con las líneas cortas posteriores intactas porque todavía cabían. El
2026-09-03 el canal recibió el contexto macro sin la línea del Imacec ni las dos de
tasas, pero con el link del BCCh que iba en medio, y el despacho reportó éxito.

Escribir el texto en el cuadro de conversación y adjuntar **después** no tiene ese tope.
Medido contra el DOM real ese día con un texto de 2.016 caracteres:

| Orden | Pie resultante |
|---|---|
| adjuntar primero, pie en el editor | **1.029** de 2.016 |
| texto en el cuadro, adjuntar después | **2.042** de 2.016 (completo) |

> **Esto revirtió el despacho por lote** (decisión del director, 2026-09-03). Antes cada
> canal salía en UNA acción con todas sus piezas, porque el editor acepta varias imágenes
> y cada una conserva su pie. Pero el truco del cuadro solo puede llenar el pie de **una**
> imagen, la que el editor abre seleccionada: con dos o más, las demás se escriben dentro
> del editor y vuelven a cortarse. Las dos cosas eran incompatibles y manda el mensaje
> completo. Se paga con una espera de cadencia por pieza y más aperturas del menú.

**El guardia compara el texto, no solo que haya algo escrito.** Esa era la falla que dejó
pasar el mensaje mutilado: `_verificar_pie_completo` contrasta la huella sin espacios de
lo que se quiso escribir contra lo que quedó, y aborta si faltan caracteres. Un mensaje
al que le faltan renglones **se lee como completo**, así que nadie lo nota desde afuera:
eso lo hace peor, no menor.

**Cada canal se rinde justo antes de despacharse.** Rendir todo al principio hacía que la
última pieza llegara con el precio de hacía veinte minutos. El refresco (1-3 s de datos +
5-15 s de render) cabe entero dentro de la espera de cadencia de 45 s, así que no cuesta
tiempo. Si el movimiento **invalidó el texto** —el precio cruzó un soporte o una
resistencia que el párrafo daba por vigentes, o perdió el nivel de vigencia del
sesgo— la pieza no sale: se renombra a `.divergente` y el despacho lo informa.
**La reanudación la manda la bitácora, no `--desde`.**
`data/historial_despachos.json` anota **una entrada por pieza entregada** (fecha, hora,
tanda, canal, pieza y la huella del texto), y `despachar` la consulta antes de cada canal
para saltar lo que ya salió. Se versiona, igual que `historial_senales.json` y
`historial_suplementos.json`: es historia de lo que el cliente recibió, y un clon nuevo sin
ella reenviaría la tanda del día.

Dos cosas que la hacen confiable:

- **Se anota DENTRO del bucle de piezas**, vía el callback `al_entregar` que el sender
  invoca tras confirmar cada entrega contra el DOM. `enviar_lote` levanta ante un fallo y
  su `return` no ocurre, así que anotar al final perdería justamente el registro de lo que
  **sí** salió. Si el anotado falla, la pieza ya salió y abortar no la devuelve: se avisa
  fuerte en vez de romper el despacho.
- **La identidad de una pieza es (tanda, canal, pieza)**, no el activo. Una tanda nueva del
  mismo activo es contenido legítimo con niveles nuevos; la misma pieza de la misma tanda es
  una repetición.

`--desde N` queda como control manual del director. **Ojo con lo que medía**: cuenta
**canales** mientras el envío cuenta **piezas** desde el 2026-09-03, así que por sí solo
reenviaba las primeras piezas de un canal que falló a la mitad.

### Un PDF adjunto SÍ lleva su pie, pero hay que esperar la carga

Medido contra el DOM real el 2026-09-04, corrigiendo una conclusión apresurada
del mismo día.

**El truco del cuadro de conversación funciona igual con documentos.** Se
escribe el texto en el cuadro del chat, se adjunta, y el editor hereda el texto
completo: se envió un pie de **1.222 caracteres** con un PDF de 2 MB y llegó
entero. **No hay tope de 1.024 para el texto heredado**, ni en imágenes ni en
documentos. El contador negativo que muestra el editor (`-197` con ese pie) no
impide enviar.

**Lo que sí cambia es el tiempo.** El campo de pie aparece cuando el editor
termina de procesar el archivo, y eso escala con el peso. Había una pausa fija
de 2 s y **una sola** búsqueda del campo: con un PNG de 500 KB alcanzaba y con el
PDF de 2 MB no. El sender abortaba con "no apareció el campo de pie de foto", y
ese mensaje me llevó a concluir que el editor de documento imponía un tope. No
era el tope: **era que el archivo seguía cargando**. Ahora la espera es activa y
proporcional (`espera_confirmacion_s`).

**El estado de entrega NO es un `data-icon`.** Una burbuja de documento entregada
trae `['document-PDF-icon']` y ningún `msg-check`; el estado vive en el
`aria-label` (`"... 20:08 Enviado"`). Lo lee `burbuja_entregada`, y `Pendiente`
gana sobre cualquier otra marca de la fila.

> [!CAUTION]
> **Un falso negativo duplica igual que un falso positivo miente.** Ese mismo día
> pasaron los dos. Primero `_adjunto_confirmado` devolvió `True` sin pie apenas
> vio `media`, el proceso cerró el navegador y la subida quedó a medias: el PDF
> se reportó entregado y quedó **"Pendiente"**, invisible para el canal. Después,
> con la espera corregida pero leyendo el tic donde no estaba, abortó envíos que
> **sí** habían llegado. El primero da por entregado lo que no salió; el segundo
> induce el reenvío manual, y así el canal de clientes terminó con dos copias del
> mismo informe.
>
> La confirmación exige ahora las tres cosas: que la última burbuja sea **este**
> archivo (por nombre, cuando no hay pie), que su etiqueta diga entregada, y una
> espera que alcance para la subida.

### El "hasta dónde" del sesgo tiene dos gramáticas, no una

El Playbook no emite señales: emite **sesgo con su vigencia**. Y ese "hasta dónde" no
se dice igual en los dos casos que el motor distingue, porque no son la misma lectura.
La traducción vive en un solo lugar, `bias_reader.resolver_vigencia`, y la consume el
escáner (que ya tiene el H1 y el sesgo en la mano) para que viaje en la selección:

| `take_profit_tipo` | Gramática | Qué se publica |
|---|---|---|
| `TRAILING_STOP_ASYMMETRIC` | **NIVEL** | Un borde: *"el sesgo alcista sigue vigente hasta 933,44"*. Es el Chandelier, y se mueve con cada vela cerrada. |
| `NIVEL_OPUESTO_CANAL` | **RANGO** | Dos bordes: *"sin sesgo direccional, el activo rota entre S1 y R1"*. |

Decir "vigente hasta X" en un activo neutral le inventa una dirección; decir "rota
entre S1 y R1" en uno sostenido le borra la que tiene.

**El informe de apertura lo lleva también**, con la misma aritmética y su propia voz: un
bloque "Hasta dónde vale esta lectura" con **una línea por activo**, no por grupo. WTI y
Brent siguen agrupados porque su lectura es palabra por palabra la misma, pero cada uno
tiene su borde, y un solo nivel para los dos publicaría el del vecino. Lo resuelve
`resolver_vigencias`, que no lanza nunca: sin terminal el informe sale sin el bloque y lo
dice en los avisos, mismo criterio que los gráficos.

**Hay un tercer caso, y es el que no era obvio.** `DATOS_INCOMPLETOS` sale del motor
con `NIVEL_OPUESTO_CANAL` y score cero, **idéntico a un rango genuino**, porque ese es
el valor neutro de esos campos y no una lectura de canal. Publicarlo como rango
afirmaría que el activo rota entre dos niveles cuando en realidad el modelo no lo pudo
leer. Se distingue por la **lista de setups permitidos vacía** (criterio estructural, no
por el texto de la etiqueta: eso sería otro contrato por nombre de los que ya costaron
caro) y esa pieza sale **sin** bloque de vigencia. El cierre canónico de tres escenarios
va igual, así que el mensaje nunca queda sin lectura práctica.

Dos reglas más que se decidieron mirando el resultado:

1. **Un sesgo ya invalidado lo dice, no lo esconde.** `vigente` compara el precio contra
   el borde. Brent el 2026-09-02 llevaba sesgo +1,50 con el precio ya bajo su Chandelier,
   y el USD/CLP estaba igual el 2026-09-03: publicar "sigue vigente" ahí dice lo
   contrario de lo que pasa. Si se rompe **entre preparar y despachar**, la pieza además
   no sale.
2. **Ante direcciones contrarias se calla la vigencia, no la lectura técnica.** Si el
   signo del score macro contradice la lectura de medias de la pieza, el bloque se omite
   y el motivo queda en `_procedencia.vigencia_omitida`. El gate del Playbook ya bloquea
   la mayoría de esos casos, pero "la mayoría" no alcanza: dos direcciones opuestas en el
   mismo mensaje cuestan la credibilidad del mensaje entero.

Cuatro reglas que se pagaron caro:

1. **La cadencia y el cupo se cuentan por pieza.** Cada pieza es su propia acción, espera
   sus 45 s y descuenta su unidad del cupo. Contar un canal como un solo envío relajaría
   el freno por la puerta de atrás.
2. **Un lote sigue teniendo que ser homogéneo.** El menú Adjuntar entra por "Fotos y
   videos" o por "Documento", no por ambas: un PDF de informe no viaja con las Stories.
   Con una pieza por acción esto ya no es una restricción técnica, pero la validación se
   mantiene porque mezclar tipos en un mismo canal no es una decisión editorial que
   convenga tomar por accidente.
3. **Un solo dueño de la sesión a la vez.** El perfil de Chromium admite un proceso. Claude
   Code y Antigravity abriéndolo a la vez crean un perfil paralelo, y ese patrón desvinculó
   la sesión el 2026-09-01 y el 2026-09-02.
4. **El barrido de payloads mide en la unidad del preparado.** El directorio de tanda se
   nombra por **minuto** y `--preparar --grupo` opera por **canal**, así que dos corridas en
   el mismo minuto natural comparten carpeta. `limpiar_payloads` hacía `rglob` sobre la
   tanda entera y la segunda se llevaba los payloads de la primera: pasó el 2026-09-04 con
   doce de commodities, y el escáner reportó "barridos 12 payload(s)" sin que eso se leyera
   como un problema. Ahora recibe `solo_canales`; sin ese argumento el barrido sigue siendo
   global, que es lo correcto para `--matriz`.

### Dos condiciones de frescura que conviene no descubrir en vivo

- El **informe de apertura** no se emite si `macro_bias_output.json` está vencido. La salida
  explícita es `--con-datos-viejos`, que estampa el aviso en la primera página.
- El escáner limita el universo a los activos con campo `imagen` en `config/activos.json`
  (`--todos` lo desactiva). Ese campo es el **interruptor del activo**: se rellena solo cuando
  el `.jpg` existe en disco, porque el renderer detiene la pieza sin él. Los prompts de las
  imágenes que faltan están en `docs/design/stories-gi/imagenes-por-activo.md`.

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
- **ADC (Ancho Dinámico de Canal)** → medir la amplitud del canal operativo (Donchian 50 / distancia entre Bandas de Bollinger: Superior - Inferior) para evaluar compresión de volatilidad vs. fases de expansión
- **Modelo ADC + ATR** → modelo cuantitativo estándar para proyectar recorridos:
  1. *Amplitud de canal (ADC)*: define los límites y la zona de compresión/rango del precio
  2. *Impulso intradía proyectado*: se calcula como $1.5 \times \text{ATR}_{14}(\text{H1})$ tras la ruptura o rebote de un nivel clave
  3. *Validación de volatilidad diaria*: se contrasta con el ATR restante diario ($\text{ATR}_{14}\text{ D1} - \text{Rango Hoy}$) para asegurar que el movimiento quepa dentro del espacio disponible de la sesión sin forzar la lectura
- **ATR** → recalcar su uso en USD/CLP como indicador de volatilidad y recorridos proyectados
- **RSI** → avisar cuando esté sobrecomprado o sobrevendido
- **MACD** → avisar cruces relevantes
- **Medias móviles** → avisar cruces y niveles de soporte/resistencia dinámicos (ej: cruce o rebote en EMA 50 y EMA 100)

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

### Registro y tono — cercano, cotidiano, pedagógico y con gancho operativo (OBLIGATORIO)
El propósito editorial de Grupo Inteligencia es **traducir lo complejo a un lenguaje cotidiano, cercano y comprensible para cualquier persona**, como un profesor que explica con paciencia y claridad. Los análisis transmiten confianza y claridad, generando apetito por comprender y operar el mercado. **Se permite y se busca** enfatizar la dirección, tomar postura clara y explicar los problemas macroeconómicos de forma sencilla y aplicable. Lo que sigue **prohibido** es el lenguaje extremo, catastrófico o la jerga acartonada/distante (dramatizar el movimiento, atribuir "sensaciones" al mercado, vaticinar catástrofes, tecnicismos vacíos sin traducción). En una frase: **claridad pedagógica y énfasis direccional sí, dramatización ni jerga impenetrable no**.

| ❌ Evitar (extremo/emocional/jerga oscura) | ✅ Usar (cercano/cotidiano/objetivo) |
|---|---|
| "el oro se va a derrumbar" | "presión a la baja" / "espacio de corrección" |
| "el mercado tiene una sensación pésima" | "más vendedores que compradores" / "debilidad" |
| "esto se va a disparar / explotar" | "impulso comprador" / "fuerza al alza" |
| "está volando / por las nubes" | "movimiento rápido" / "alta volatilidad" |
| "pánico" / "euforia" / "terror" | "cautela en el mercado" / "búsqueda de refugio" |

Reglas:
- Traducir siempre lo macro a la vida cotidiana: explicar por qué un dato de inflación, tasas o petróleo afecta el bolsillo o la decisión de inversión de forma simple.
- Enfatizar con dirección, sin dramatizar: hablar con claridad de **sesgo, tendencia, fuerza, freno, rebote, piso y techo**, nombrando hacia dónde se inclina la mayor probabilidad.
- Tomar postura pedagógica: cada análisis nombra el escenario más probable (`🟢 sobre X → …`, `🔴 bajo Y → …`) sin rodeos ni ambigüedades, pero sin prometer certezas mágicas.
- Si aparece un concepto técnico o sigla, **siempre** se explica en lenguaje simple (Regla de oro: si hay duda entre complicar o simplificar, siempre simplificar). Profesional = accesible y claro.

### Prohibido el guion largo como inciso (OBLIGATORIO en texto de cliente)
En todo texto que lea un cliente —mensajes de WhatsApp, pies de Story, textos dentro de las piezas, guiones de venta— **nunca** se usa el guion largo `—` ni el medio `–` para abrir un inciso o una aposición ("el stop en 1.758,09 — para eso está"). Se reescribe con puntuación corriente: punto seguido, coma o dos puntos.

**Por qué**: ese guion es una marca reconocible de texto generado por IA, y el material se firma con el nombre y las credenciales de un analista real. Un mensaje que se lee como redactado por una máquina daña la credibilidad de la firma, que es justamente lo que la sostiene.

**Cómo aplicarlo**: antes de guardar cualquier pieza de cliente, buscar `—` y `–` en el texto final y reemplazarlos. El punto medio `·` **sí** se mantiene: es separador visual del kit de marca (`ORO · XAU/USD`), no puntuación de frase. La restricción es de redacción y no alcanza al código ni a la documentación interna del repo (este archivo incluido).

### Formato base (aplica a todos los mensajes)
- Formato WhatsApp: *negrita*, _cursiva_
- Bullets: •
- Horas siempre en hora Chile (CLT/CLST)
- Estructura formal, consistente y repetible cada día
- Emojis con moderación: 📊 📈 📉 ⚠️ 🕐 📚 📅 (más 🟢🔴🟡🎯 del sistema de escenarios)

## Datos macro en español + Diccionario rápido (OBLIGATORIO — issue #46)
- **Indicadores en español**: todo dato macro se nombra en español, con la sigla original entre paréntesis **una sola vez** (ej. "Índice de gerentes de compra manufacturero (PMI manufacturero)"). Minimizar términos en otro idioma en el cuerpo del mensaje.
- **Bloque "🔤 Diccionario rápido"**: obligatorio en toda pieza donde aparezcan siglas. Por cada abreviatura del mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), una línea explicativa en voz novata. **Ninguna abreviatura puede quedar sin explicación en español ese día.** En el **Modo resultado** el mensaje es el pie de una imagen y el bloque no cabe: la sigla se explica **en línea**, dentro de la frase, una sola vez ("vacantes de empleo (JOLTS)"). Cambia el dónde, no el si.
- **Fuente canónica**: `data/glosario_siglas.json` (`SIGLA → {nombre_es, explicacion}`). Si aparece una sigla nueva, explicarla al vuelo y **añadirla al JSON** para reutilizarla.
- La fuente principal del panorama del día es la tool MCP `obtener_calendario_macro` (calendario Investing.com — Chile/EE.UU./China/Zona Euro, con resultado real `actual` y clasificación mejor/peor/en_linea); WebSearch sobre investing.com + fuentes oficiales son fallback solo si la tool devuelve `{"error": ...}`.

### Dos modos de la pieza de dato macro (issue #93)
La pieza de un dato económico se arma en uno de **dos modos**, según la hora del evento vs. la hora actual de Chile:
- **Modo anticipación** (dato `🕐 PRÓXIMO`, aún no sale): qué es + hora CLT + anterior/consenso + 3 escenarios (mejor/peor/en línea) + activos a observar + temporalidad del impacto.
- **Modo resultado** (dato `✅ YA SALIÓ`, ya tiene valor `actual`): **la pieza es la Story, el texto es su pie de foto** (decisión del director, 2026-08-04). El desarrollo largo —sub-lecturas, "🧠 ¿Qué significa esto?", "⚠️ PERO ojo con el detalle", "💡 Impacto esperado por activo" y el diccionario— vive dentro de la imagen de `/story dato_macro` y **ya no se manda además como texto**: mandar ambos obliga al cliente a leer dos veces lo mismo, y con imagen adjunta WhatsApp corta el pie antes que un mensaje suelto. Reglas:
  - **Orden**: primero la Story, después el pie escrito desde el mismo payload — veredicto y cifras tienen que coincidir entre imagen y texto.
  - **Pie**: chip `📊 DATO MACRO · [PAÍS]` + hora de publicación + indicador con cifra + veredicto *PEOR / MEJOR / EN LÍNEA* frente al consenso + una línea de implicancia direccional + la temporalidad + el cierre canónico.
  - **El pie repite el veredicto de la imagen a propósito**: es lo que se ve en la notificación de WhatsApp antes de abrir el chat, y lo único legible si el cliente no descarga la imagen. Un adjunto sin pie llega mudo.
  - **⏱️ Temporalidad del impacto** (OBLIGATORIA, ambos modos): scalper / intradía / swing de jornada / posicional (mismas 4 etiquetas canónicas). Va en el pie porque **no** está en la imagen — es la única pieza del desarrollo largo que sobrevive en el texto.
  - La plantilla larga del issue #93 queda en el historial git por si se decide volver a ella.
- **Cierre obligatorio (ambos modos)**: tras el último separador, link al calendario completo (`https://es.investing.com/economic-calendar/`) + CTA genérico al analista designado, siempre juntos como pie.
- Tras aprobar y enviar, se registra `data/ultimo_evento.json` para poder encadenar la **encuesta post-evento** pedagógica.

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
| COPPER | 0 | $14197 USD/t | $14.197 / $14197.0 |

*El Cobre se analiza y cotiza siempre por su valor por tonelada métrica (`USD/t`) disponible en el terminal MT5.*
Nunca truncar ceros al final (89.60, no 89.6). Nunca redondear a enteros salvo que digits = 0.

> [!NOTE]
> **El Cobre es el único con `digits = 0`, y por eso se escribe entero** (`$14197 USD/t`). El
> broker lo cotiza así: `symbol_info("COPPER").digits` devuelve 0 (verificado el 2026-09-03).
> Estuvo declarado con 1 en dos bloques distintos de `activos.json` y con 4 en
> `extractor_precios.py`, tres valores para el mismo símbolo. **Decisión del director el
> 2026-09-03: manda el terminal.**
>
> No confundir esa serie con `COBRE_COMEX` de `commodities_data.json`, que es el precio COMEX
> en **USD/libra** (6,602) y sí lleva 4 decimales. Son dos series del mismo metal en dos
> unidades, y solo la de MT5 es el símbolo operable.
>
> Ojo con el catálogo: `COPPER` figura en `forex_commodities` **y** en
> `activos_complementarios`, y `catalog.load_valid_tickers` recorre el segundo al final, así que
> su valor sobrescribe. Los dos tienen que coincidir, y un test lo impone.

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

## Antigravity (AGY) — el segundo runner

El repo lo ejecutan **dos** agentes: Claude Code y Antigravity. Antigravity llama
*workflows* a lo que Claude Code llama slash commands: archivos markdown en
`.agents/workflows/`, invocables igual con `/nombre`.

**Los seis comandos están expuestos a AGY**, sin distinción: `/carrusel`, `/informe`,
`/story`, `/encuesta`, `/rencuesta` y `/estado`. El flujo es ejecutable igual por los dos
runners, envío incluido, siempre después de la aprobación explícita del director.

**Cada workflow es un puntero, no una copia.** Dos runners leyendo dos carpetas
distintas con la misma definición duplicada es el problema que ya conocemos: a la
segunda copia una queda atrás y nadie se entera hasta que sale una pieza mal. Hay
además un límite duro: **Antigravity corta los workflows en 12.000 caracteres**, y
`story.md` tiene más de 43.000 — copiarlo es imposible, no solo indeseable.

**Antigravity no lee `CLAUDE.md`.** Por eso las reglas transversales —los datos
salen del MCP y nunca se inventan, la hora sale del reloj, los decimales salen de
`digits`, el tono, el flujo de aprobación— están en `.agents/rules/proyecto.md`, y
cada workflow manda leerlo primero. Ese archivo es un extracto: ante cualquier
contradicción manda `CLAUDE.md`.

Para exponer un comando nuevo se agrega al diccionario `COMANDOS` de
`scripts/agy_workflows.py` y se regenera; los archivos de `.agents/workflows/` no
se editan a mano.

```bash
uv run python scripts/agy_workflows.py           # genera
uv run python scripts/agy_workflows.py --check   # verifica (lo corre la suite)
```

Se versionan `.agents/workflows/` y `.agents/rules/`; queda fuera
`.agents/mcp.json`, que lleva la ruta absoluta de cada máquina — mismo criterio
que `mcp/mcp_config.json` frente a su `.example`.

## MCP Servers integrados

| MCP | Estado | Propósito | Usado en |
|-----|--------|-----------|----------|
| **market-data** | ✅ Activo | Análisis técnico MT5 (`get_asset_levels`) + niveles dibujados a mano por el director en MT5 (`get_chart_objects`) + calendario económico Investing.com (`obtener_calendario_macro`) + especificaciones de contrato y sesiones (`get_symbol_spec`) + operaciones abiertas del terminal (`get_open_positions`). Noticias vía WebSearch. | Comandos de datos de mercado y operativas |
| **WebSearch (investing.com + fuentes oficiales)** | ✅ Activo | Calendario económico y noticias relevantes | Contexto macro de cada canal y piezas de dato macro |
| **WhatsApp Web (Playwright)** | ✅ Activo | Envío directo a los 7 canales (`scripts/enviar_whatsapp.py`), con verificación de entrega contra el DOM y frenos de cadencia | Tras la aprobación del director |
| **TrendRadar / Firecrawl / Finnhub** | ❌ No activos | Reemplazados por market-data (MT5) + WebSearch | — |

**Nota**: el MCP `market-data` expone **siete** tools:
- `get_asset_levels` — análisis técnico MT5 automático (soportes/resistencias, indicadores). Devuelve `ema_20`, `ema_50`, `ema_100`, RSI, ATR, ADX, MACD, Bollinger y el canal `donchian_50_high/low/mid`. Ojo: `ema_20` es media **exponencial** (el gatillo que manda el Playbook en H1) y `bb_mid` es la media **simple** de 20 de las Bandas de Bollinger — no son lo mismo, y confundirlas cambia el indicador.
- `get_chart_objects` — niveles dibujados a mano por el director en MT5 (soportes/resistencias, trendlines, canales, rectángulos) más screenshot, vía el Service `ChartObjectsExporter` (sub-proyecto A, #98).
- `obtener_calendario_macro` — calendario económico Investing.com (Chile/EE.UU./China/Zona Euro con campo `actual` y `resultado`, issue #91; WebSearch es fallback si la fuente falla).
- `get_symbol_spec` — especificaciones de contrato de un símbolo (trade_mode, digits, volumen mínimo/paso, tamaño de contrato) y sesiones de trading semanales en hora Chile; con `fecha` responde de forma determinista si el activo opera ese día (issue #104).
- `get_open_positions` — operaciones abiertas en el terminal MT5 (ticket, tipo BUY/SELL, volumen, entrada, SL, TP, precio actual, resultado flotante y swap en la moneda de la cuenta).
- `get_macro_bias` — sesgo cuantitativo del Playbook: régimen macro R0-R4, sesgo score `[-2,+2]`, SL dinámico por ATR y matriz de permisos técnicos. Solo para los 5 activos con ficha (`USDCLP`, `XAUUSD`, `WTI`, `BRENT`, `US100`); lee el snapshot que emite `scripts/macro_bias_engine.py`.
- `get_curva_tasas` — curva soberana de EE.UU. desde `data central/`: rendimientos del Tesoro 2Y/10Y/30Y, tasa efectiva de fondos federales, tasa real TIPS 10Y (`DFII10`) y compensación por inflación (`T10YIE`), con **variación en puntos base a 1 y 5 días** y la pendiente 2s10s. La curva no es un símbolo de mercado, así que no se puede pedir con `get_asset_levels`. Cada serie informa su `frecuencia_publicacion` (`DFF` publica los siete días porque es un promedio diario; las yields solo días hábiles), y **un delta que no se puede calcular viene `null` y nunca `0`** — cero significa "no se movió", que es distinto de "no sé". La tasa real es `DFII10`: el CSV `US_TIPS_Real_Rates_ETF_*` es el precio de un ETF (~105), no una tasa.

Contrato de error común: si el dato no está disponible retorna `{'error': 'CÓDIGO', 'message': '...'}` — nunca array vacío ni `None` silencioso. La antigua `get_economic_events` fue reemplazada por la tool nativa (#53); `get_market_context` (noticias Finnhub) quedó deprecada y se purgó del registro — las **noticias** se obtienen vía `WebSearch` (investing.com + fuentes oficiales: Fed, BCCh, OPEP+, EIA, BLS). Ver `docs/archive/superpowers/specs/2026-06-05-calendario-macro-nativo-mt5-design.md`.

**Flujo actual**: los comandos generan el contenido → lo muestran al director → **al aprobar**, se guarda en
`data/mensajes/` y se envía con `scripts/enviar_whatsapp.py`. Evolution API quedó descartada: el envío va por
WhatsApp Web con Playwright sobre una sesión vinculada (`--login`, una vez).

**Los siete canales temáticos**: el contenido ya no va a un grupo único. `config/whatsapp_grupos.json` mapea
cada carpeta (`01_macro_y_apertura` … `07_oportunidades_cuantitativas`) al nombre real del canal en WhatsApp, y
resuelve alias en lenguaje natural (`metales`, `oro`, `forex`, `cripto`…), y cada canal temático recibe además
su propia lectura macro.

**`01_macro_y_apertura` es el grupo de AVISOS de la comunidad**, no un canal temático aparte. Decisión del
director el 2026-09-03: **no se crea un canal temático propio para el macro**. Ahí figuraba un nombre
aspiracional que prometía un canal inexistente en WhatsApp, y el síntoma fue que el macro parecía no llegar
cuando en realidad llegaba a Avisos.

**El nombre inventado se borró del repo entero el 2026-09-04, y este párrafo no lo repite a propósito.**
Quitarlo del config no alcanzó: sobrevivió en `CONFIG_MACRO_GRUPOS`, que es el módulo que **redacta texto de
cliente**, y en la ficha del canal y el índice de `docs/grupos_whatsapp/`. Así llegó a un grupo real, que
recibió una pieza preguntando qué significaba el dato *"para"* un canal que nadie puede abrir. Lo impide ahora
un test de contrato que barre `scripts/`, `src/`, `config/`, `templates/`, `docs/grupos_whatsapp/`,
`.claude/commands/` y `.agents/`. Dejar el nombre escrito en la explicación de por qué no existe es
exactamente de dónde se copiaba de vuelta.

**Ese grupo no lleva apellido temático, y el mensaje lo refleja**: su encabezado es `CONTEXTO MACRO DIARIO`
sin sufijo, porque su lectura macro *es* el panorama general. Y como la pregunta de cierre necesita un sujeto
("¿qué significa para X?"), los canales temáticos usan su propio tema y este usa **el mercado**: eso es lo que
hace el campo `sujeto` de `CONFIG_MACRO_GRUPOS`, que existe solo para él.

> **Ojo al buscar un canal en WhatsApp Web**: en la lista de chats **todos los grupos de la comunidad se
> muestran con el nombre de la comunidad como título**, y el nombre real del grupo aparece en la primera línea
> del preview. Por eso siete chats distintos se ven iguales al buscarlos, y por eso `nombre_oficial` del grupo
> padre coincide con el de la comunidad.

> [!CAUTION]
> **Automatizar WhatsApp Web va contra sus términos de servicio** y el número es el del negocio. El sender
> impone 45 s mínimos entre envíos y un cupo de 40 al día (`seguridad` en `config/whatsapp_grupos.json`,
> contador en `data/.whatsapp_envios.json`). No subas esos límites, no metas el envío en un bucle y no lo
> lances en paralelo: el perfil de sesión no admite dos procesos a la vez.

## Series de precios: en disco, no en git

`data central/DATA PRECIOS OHLC/` lo llena `scripts/extractor_precios.py` desde MT5 y
lo leen `macro_bias_engine.py` y `ticket_engine.py`. Las series intradía y diarias
(`*_M15`, `*_H1`, `*_D1`) **están gitignoradas**: pesan ~5 MB cada una y se
regeneran, así que versionarlas sumaba ~66 MB a la historia por cada ingesta sin
aportar nada que MT5 no devuelva. Las semanales y `latest_prices_summary.json` sí se
versionan: son livianas y sirven de referencia sin terminal.

**En un clon nuevo hay que correr el extractor antes que el motor.** Ojo con esto:
`ticket_engine.cargar_serie_h1_archivo` devuelve `None` en silencio cuando el archivo
no está, así que sin las series el motor no falla, simplemente deja de emitir
tickets. Si el resultado sale vacío, lo primero que hay que descartar es que falten
las series.

### La cadena de datos tiene un solo punto de entrada

`scripts/pipeline_datos.py` corre los tres pasos **en orden y aborta al primer fallo**:

```bash
uv run --with MetaTrader5 python scripts/pipeline_datos.py   # ingesta → precios → sesgo
uv run python scripts/pipeline_datos.py --estado             # solo reporta, no ejecuta
```

Abortar es deliberado. Saltarse un paso o invertirlos no rompe nada de forma visible,
y ese es el problema: correr el motor sobre precios que no se actualizaron produce un
sesgo que **parece** fresco. Peor que fallar es fallar de forma convincente.

`--estado` lee los **tres relojes** que antes nadie miraba juntos
(`estado_ejecucion.json`, `latest_prices_summary.json`, `macro_bias_output.json`) y
aplica el mismo umbral de staleness del Playbook vía `bias_reader` — inventar una
segunda regla de vencimiento sería el mismo error que tener dos fórmulas de ATR.

**Avisa cuando los precios no vienen de MT5.** El extractor cae a yfinance si el
terminal no le sirve un símbolo, y ese fallback es correcto pero **no es equivalente**:
son futuros (`GC=F`, `CL=F`, `NQ=F`) y no los CFD del broker. El 2026-09-02 el terminal
quedó conectado a otra cuenta y cinco de seis activos salieron de yfinance mientras la
cadena reportaba `[OK] precios` y `Datos frescos`. El campo `broker: YFINANCE` sí quedaba
escrito en cada archivo, así que era auditable, pero nada lo decía en voz alta: costó una
hora de diagnóstico y los stops del Playbook quedaron calculados sobre otro instrumento.
Ahora `--estado` nombra cada activo caído y el veredicto pasa a no utilizable, sin umbral
de tolerancia: un stop calculado sobre otra fuente de precio es un stop de otro mercado.

Informa además la **confianza del modelo**, que hasta ahora solo se imprimía en
consola del motor y no la leía nadie. **Ese número todavía no bloquea**: qué umbral
corresponde es una decisión de método pendiente del director. Lo que sí cambia es que
deja de estar enterrado en un JSON.

### La ingesta se engancha al arranque de sesión (Claude Code)

`scripts/hook_ingesta_macro.py` conecta la ingesta macro al evento `SessionStart`, y
está registrado en `.claude/settings.json` (versionado, así lo hereda cualquier clon).
Son **dos hooks del mismo módulo** y esa división es la decisión de fondo:

| Modo | Cómo corre | Qué hace |
|---|---|---|
| `--estado` | bloqueante, solo stdlib, < 1 s | Lee `estado_ejecucion.json` e inyecta al contexto la última ingesta en hora Chile, el status por fuente, los errores y las novedades. |
| `--refrescar` | `async`, sin bloquear | Si esa misma lectura está vencida, corre `pipeline_ingesta.py` y deja la bitácora en `data/logs/`. |

**La ingesta completa tarda ~55 s medidos el 2026-09-05**, y dispara además el motor de
sesgo y el pronóstico de inflación de Japón. Bloquear cada arranque con eso cuesta un
minuto por sesión y en un día se abren varias; pero un hook `async` **no le puede contar
nada al modelo**, porque su salida no entra al contexto. De ahí los dos.

Cuatro reglas que lo sostienen:

1. **El umbral de vencimiento vive en `esta_vencida` y lo consultan los dos modos.** Son
   6 h: los emisores publican una vez al día (FRED en T+1 hábil, el BCCh en T-2), así que
   refrescar más seguido golpea las APIs sin traer un dato nuevo. Dos umbrales para la
   misma decisión dejarían al contexto afirmando que el dato está fresco mientras el otro
   hook lo está bajando, que es el defecto recurrente del repo.
2. **El aviso al modelo dice que los datos van a cambiar durante la sesión.** Cuando el
   refresco se lanza, los JSON de `data central/` y `macro_bias_output.json` cambian bajo
   los pies de la conversación: citar una cifra leída antes del refresco es publicar el
   dato de anoche con fecha de hoy.
3. **Un lock (`data/.ingesta_macro.lock`) impide dos ingestas simultáneas**, porque dos
   ventanas abiertas a la vez escribirían sobre los mismos archivos. Un lock de más de 15
   min se ignora: un proceso que murió sin limpiarlo no puede dejar la ingesta bloqueada
   para siempre.
4. **El hook nunca aborta la sesión.** Todo error se traga y se reporta como texto: un
   fallo de red del BCCh no puede impedir abrir Claude Code.

El lock y la bitácora están gitignoreados, mismo criterio que `data/.reloj_disparos.json`:
son estado generado, no historia editorial.

## Stories GI y Generación de Imágenes

> [!CRITICAL]
> **Prohibición total de modelos de difusión (`generate_image`)**: toda pieza visual se maqueta
> en HTML/CSS (`templates/stories/`) y se rinde con Playwright sobre datos reales. Nunca se
> genera una imagen con un modelo de difusión.

**El estándar de diseño lo comanda el brand kit** (`brand_atomic_system/`, layout v2, consumido
por su MCP). El catálogo de plantillas del repo se redujo a **cuatro**, que son las que existen
en `templates/stories/`:

| Plantilla | Qué es | Datos |
|---|---|---|
| `alerta` | Niveles del día de un activo | `get_asset_levels` |
| `dato_macro` | Un dato económico que ya publicó, con su veredicto frente al consenso | calendario + series de `data central/` |
| `breaking` | Noticia urgente (kicker, titular, cifra, contexto, reacción) | 100% editorial |
| `calendario` | 3 a 6 eventos macro de la semana, selección editorial | `obtener_calendario_macro` |

Las demás (`recomendacion`, `quote`, `encuesta`, `edu`, `flash`, `postventa`, `oportunidad`,
`operacion`) **se retiraron**. No las reconstruyas por tu cuenta: si hace falta una pieza nueva,
el estándar sale del brand kit.

Único renderer: `scripts/story_render.py` (payload JSON → HTML → PNG con Playwright headless).

**Formato del lienzo**: horizontal `1920×1080` para piezas con gráfico técnico; vertical
`1080×1920` para piezas de carga textual sin gráfico. El formato viaja por el CLI
(`--formato horizontal|vertical`), **nunca** por el payload: el payload es contrato de
contenido y el formato es presentación, así el mismo payload rinde ambos.

**Paleta y color (una sola fuente).** Los colores viven en `templates/stories/marca.css` y las
plantillas los consumen con `var(--rol)`; ningún hex se escribe a mano. Los tokens se nombran
por **rol y no por color** (`--acento`, no `--teal`). `scripts/marca_tokens.py --check` falla si
una plantilla vuelve a hardcodear un color, que es lo único que mantiene la fuente única siendo
única.

Dos reglas de color que se pagaron caro:

1. **El cromo no opina.** Marco, chip, borde y degradado van siempre en el acento de marca. Solo
   se colorea lo que ES un dato: la píldora de dirección, la variación, el veredicto. Una pieza
   bajista bañada en rojo se lee como alarma y contradice la regla de tono del proyecto.
2. **`--sube` / `--baja` no se reskinean.** Verde arriba y rojo abajo es una convención que el
   cliente lee sin pensar, no una decisión de marca.

El acento es `#50C0A8`, el extremo verde del degradado del logo, medido sobre los assets.

**Serie real para los gráficos.** `scripts/serie_mt5.py` trae los cierres del terminal y arma el
bloque `recorrido` que consume `story_grafico.py`, que traduce serie e hitos al SVG del token
`{{grafico}}`. Los marcadores se anclan por ROL, no por proximidad de precio: `actual` y `meta`
van al extremo derecho por definición. Anclar por precio parece razonable y no lo es, porque el
precio oscila y el cierre más parecido puede caer en cualquier punto de la serie.

**Revisión y protección.** Cada plantilla tiene su payload en
`tests/fixtures/stories/payloads/<plantilla>.json`, y esas mismas fixtures alimentan el render
completo y el test de contrato:

```bash
uv run --extra stories python scripts/rendir_todas.py
uv run pytest tests/test_story_render.py
```

El test exige que toda plantilla tenga fixture y resuelva sin tokens huérfanos. **Ojo con su
límite**: compara el conjunto de plantillas contra el de fixtures, así que si ambas se borran en
pareja el test sigue verde. No detecta que el catálogo encogió, solo que quedó descuadrado.

**Guardado**: `data/stories/<Fecha>/<activo_slug>/<plantilla>/<Hora>_<plantilla>.png` vía
`scripts\ruta_story.ps1`. Los `data/stories/*.png` están gitignored. `playwright` es dependencia
**opcional** (`stories`): `uv sync --extra stories && python -m playwright install chromium`.

## Documentos largos
<!-- ambito: ambos -->

El manual de operaciones, el cierre semanal, la capacitación en PPTX y la guía rápida: qué es
cada uno, con qué comando se compila y qué trampa de maqueta tiene medida, en
`docs/documentos-largos.md`. El manual va al grupo de avisos en PDF; el cierre semanal sale
semanal al canal; los otros dos circulan entre equipos.

## Flujo de aprobación → WhatsApp (modo semi-automático activo)

Todo contenido pasa por este flujo antes de enviarse:
1. El comando genera el contenido.
2. Lo muestra al director para aprobación.
3. Pregunta: "¿Adjuntar chart de MT5?"
4. El director aprueba o pide ajustes.
5. **Al aprobar**: guardar automáticamente en `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt`.
6. Enviar al canal que corresponda con `scripts/enviar_whatsapp.py --grupo <alias> [--adjunto ...] --mensaje-archivo ...`.
   El comando verifica que la pieza aparezca en la conversación antes de reportar éxito; si aborta, **no se envió**,
   y hay que revisar si llegó antes de reintentar para no duplicarla.

**Regla de guardado**: después de cada aprobación, SIEMPRE guardar el mensaje final en `data/mensajes/` con la estructura **día → activo → tipo** (issue #45). Construir la ruta con el helper determinista `scripts\ruta_mensaje.ps1` (NUNCA armarla a mano):
```powershell
scripts\ruta_mensaje.ps1 -Fecha "2026-06-04" -Activo "USDCLP" -Tipo "dato_macro" -Hora "09-01"
# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt
```
El helper crea las carpetas y devuelve la ruta lista para `Write`. Si la pieza no tiene un activo protagonista (concepto, pregunta, cierre semanal, encuesta de la semana, earnings, paquete dominical), omitir `-Activo` y el helper la guarda en `_general/`. La hora `HH-mm` sale del reloj de Chile (regla canónica). Usar luego la herramienta Write sobre la ruta devuelta.

**Tipos de archivo** (carpeta `<tipo>`): niveles, dato_macro, alerta, encuesta, cierre.

**Piezas públicas limpias**: `/carrusel`, `/informe` y `/story` entregan **exclusivamente material para el cliente final** (mensaje de WhatsApp + pieza visual de marca). Queda excluida la generación automática de guiones internos o piezas para ejecutivos: ese material salió del repo junto con `/ventas` y `/postventa`.

**Convención de nombres de chart (issue #81)**: los PNG de `data/charts/` siguen el patrón único `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`, con el mismo `<activo_slug>` de `ruta_mensaje.ps1` (#45) — `lowercase(ticker_mt5)` sin `.spot`/`#`/`/` — y `<TF>` en mayúscula MT5 (`M15`/`H1`/`H4`/`D1`). Ej: `usdclp_H4_2026-06-07_11-45.png`. Los `data/charts/*.png` están gitignored.

**Nunca se envía nada al grupo sin aprobación explícita del director.**

**Nota**: los selectores del sender están medidos contra el DOM real de WhatsApp Web y comentados en
`src/whatsapp_sender.py`. WhatsApp cambia su interfaz sin avisar: si un envío empieza a fallar, el primer paso es
volver a medir esos selectores, **nunca** relajar la verificación de entrega.

## Slash Commands disponibles (6)

El catálogo se redujo a seis. Todo lo demás se retiró cuando la producción pasó a regirse por
el carrusel y el informe: los siete comandos de día, las piezas sueltas que ellos orquestaban
(`/apertura`, `/alerta`, `/dato_macro`, `/noticia`, `/actualizacion`, `/accion`, `/earnings`,
`/señal`), lo educativo satélite (`/concepto`, `/pregunta`, `/respuesta`, `/curriculo`),
`/chart`, y los internos `/ventas` y `/postventa`. Los seis que quedan están expuestos por
igual a Claude Code y a Antigravity.

| Comando | Cuándo usarlo |
|---------|---------------|
| `/carrusel` | **La producción diaria.** El escáner detecta la sesión y la hora real, puntúa el universo con el `Score_GI`, elige el Top 3 y arma las piezas por canal, con su contexto macro. Acepta `--grupo <alias>` para un canal concreto y `--matriz` para cubrirlos todos. |
| `/informe [apertura\|cierre]` | El informe de la jornada. Apertura en PDF institucional A4; cierre chat-first (mensaje con gráfico). |
| `/story [tipo]` | Una pieza suelta, cuando hace falta fuera de la tanda. Tipos: `alerta`, `dato_macro`, `breaking`, `calendario` — las cuatro plantillas que existen. No pregunta nada: todo va por argumento. |
| `/encuesta [tipo] [activo]` | Encuesta de sentimiento (`posicion`, `tendencia`, `movimiento`). |
| `/rencuesta` | Desarrolla didácticamente el tema de una encuesta y construye la malla de conceptos. |
| `/estado` | Dashboard del sistema: sesión de WhatsApp, cupo de envíos del día, frescura del motor, MCPs. No envía nada. |

## Notas de implementación
<!-- ambito: ambos -->

El árbol del proyecto y las decisiones técnicas ya aplicadas que no hace falta re-decidir (el
CSS embebido en las plantillas de Stories, entre otras): `docs/notas-implementacion.md`.

