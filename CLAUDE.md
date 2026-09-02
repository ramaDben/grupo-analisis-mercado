# Grupo de Análisis de Mercado — Sistema Automatizado

## Contexto
Este proyecto automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El usuario es el director de trading. Los sub-agents actúan como analistas de mercado y recolectores de información.

> [!CRITICAL]
> **GUARDRAILS DE INTEGRIDAD DE DATOS Y COMPOSICIÓN EDITORIAL:**
> 1. **CERO HARDCODING DE PRECIOS Y COTIZACIONES (REGLA 1):** Queda estrictamente prohibido escribir números de precios, cotizaciones, variaciones porcentuales o niveles técnicos "a mano" o calculados mentalmente en scripts de Stories, HTMLs o informes Markdown. Todos los precios deben ser leídos en tiempo de ejecución desde MetaTrader 5 / MCP `market-data` (`get_asset_levels`, `latest_prices_summary.json`). Para tickers con sufijo del broker, usar siempre el símbolo exacto del catálogo (`US100.spot`, `US500.spot`, `US30.spot`, `WTI.spot`, `BRENT.spot`, `GER40.spot`, `COPPER`, `USDCLP`, `XAUUSD`, `USDJPY`).
> 2. **PROHIBICIÓN DE TRUNCADO DE DÓLARES EN SHELL (REGLA DE ESCRITURA):** Al generar o guardar archivos `.txt` o mensajes con símbolos de moneda (`$`), queda prohibido usar double-quotes o here-strings `@"..."@` en PowerShell porque la shell interpreta `$931` o `$4` como variables vacías y trunca el precio. Toda escritura de archivos de texto con precios DEBE realizarse mediante Python (`Path.write_text(..., encoding="utf-8")`) o single-quoted here-strings `@'...'@`.
> 3. **COMPOSICIÓN OBLIGATORIA DE INFORMES PDF (REGLA 2):** Queda estrictamente prohibido generar PDFs institucionales a partir de markdowns planos improvisados. Todo informe PDF DEBE seguir la arquitectura canónica (`pipeline_informe.py` + `grafico_informe.py` + `generar_pdf.py`), incluyendo los banners gráficos vectoriales a 300 DPI por activo, la tabla de curva soberana de 4 columnas en notación chilena y la estructura pedagógica de 3 capas (qué pasa, qué significa, qué NO hacer).
> 4. **PROHIBICIÓN TOTAL DE MODELOS DE DIFUSIÓN (REGLA 0):** Prohibido usar `generate_image` o modelos de difusión. Toda pieza visual es código HTML + CSS + Playwright.

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

### El catálogo técnico es más amplio que la rotación diaria
`config/activos.json` cubre 38 tickers, e incluye desde el 2026-08-25 cinco ETF (`QQQ.US`, `SPY.US`, `GLD.US`, `IWM.US`, `SOXX.US`) y cinco criptos nuevas (`ETHUSD`, `SOLUSD`, `LTCUSD`, `ADAUSD`, `DOGUSD`). Todos entran con `rotacion_diaria: false`: **la rotación diaria de 2-3 activos no cambia**, y estos existen para que `get_asset_levels` y `get_symbol_spec` puedan responder por ellos cuando el director los pida.

Tres cosas que conviene no volver a averiguar:
- **Los ETF llevan sufijo `.US`, no prefijo `#`** (el `#` es de las acciones). El broker **no ofrece** `TLT` ni `SMH`: `SOXX.US` es el equivalente de SMH, y la duración de deuda se lee de la curva con `get_curva_tasas`, no como activo operable.
- **La cripto de Dogecoin es `DOGUSD`**, no `DOGEUSD`. `ADAUSD` y `DOGUSD` cotizan con 4 decimales.
- **Entrar al catálogo técnico no es entrar al Playbook.** Un ETF tiene niveles, indicadores y especificaciones de contrato, pero no tiene ficha operativa, régimen R0-R4, sesgo score ni setups permitidos: ese conjunto sigue siendo el de `bias_reader.VALID_SYMBOLS` (`USDCLP`, `XAUUSD`, `WTI`, `BRENT`, `US100`), porque cada ficha del Playbook cita literatura académica y elasticidades medidas.

El universo completo del terminal (32 pares FX, 86 acciones, 13 ETF, 6 criptos) está capturado en `calculadoras excel/Simulador GI Real.xlsx`, hoja `Datos`, que genera `scripts/simulador_gi.py` con `mt5.symbols_get()`. Es la fuente para verificar si un instrumento existe y con qué `digits`, sin abrir MT5.

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

### Guardrail Anti-Anacronismos y Modo Anticipación (OBLIGATORIO)
Queda **estrictamente prohibido** redactar eventos futuros en tiempo pasado (ej. "tras la asimilación de los discursos de Jackson Hole", "luego del dato de IPC") si dicho evento aún no ha ocurrido según el reloj real de Chile.
- **Eventos Futuros / Próximos:** Se redactan exclusivamente en **Modo Anticipación** ("en la antesala de...", "a la espera de los discursos previstos para mañana...", "el mercado aguarda la publicación...").
- **Validador Automático:** `generar_pdf.py` y `pipeline_informe.py` ejecutan automáticamente `scripts/validar_consistencia_temporal.py`. Si detectan discrepancia de fecha o anacronismos en el texto, el proceso aborta inmediatamente (*Fail-Fast*).

## Agenda semanal

| Día | Contenido principal | Encuesta | Señales |
|-----|---------------------|----------|---------|
| Domingo | Noticias fin de semana + preview semana + sesgo lunes | Encuesta semana | No aplica |
| Lunes | Resumen calendario semanal + concepto de la semana | Tendencia AM | Según oportunidad |
| Martes | Niveles + noticia + drivers | Precio apertura | Según oportunidad |
| Miércoles | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Jueves | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Viernes | Niveles + noticia + drivers + cierre semanal | Precio apertura lunes | Según oportunidad |

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
`stories`). Brent no tiene gráfico porque el broker no ofrece el símbolo, y el mapeo
Playbook → ticker MT5 vive en `bias_reader.TICKER_MT5`, que es también el que usa el
escáner.

**Un PDF al día, no dos.** La skill `generar-reporte-editorial` reserva el PDF
"estrictamente" para hitos de alta densidad y manda chat-first para piezas tácticas, por
fatiga de descargas. La apertura sí va en PDF; el cierre es mensaje con gráfico.

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

**Cuatro gates se aplican ANTES de puntuar, y son prohibiciones, no puntos:**

1. **Feriado de la bolsa** del activo (`config/feriados_bolsa.json`).
2. **Blackout por calendario** (skill cuantitativa §4: FOMC −30/+75 min, NFP e IPC de EE.UU.
   −15/+30, RPM y Imacec de Chile, BoJ). Ojo: `obtener_calendario_macro` ya entrega la hora en
   America/Santiago, así que la ventana se compara directo — volver a convertir produce el
   desfase de ±1 h del issue #38.
3. **Prohibición del Playbook** para los 5 activos con ficha, leída de `setups_prohibidos`.
   Solo bloquea si apunta en la misma dirección que la lectura técnica: que esté prohibido
   comprar agresivamente no impide comunicar una caída.
4. **Agotamiento**: ATR diario consumido sobre 90%.

Un setup prohibido puede puntuar alto, y con scoring puro ganaría la tanda. Por eso el filtro
va antes.

**El escáner informa el motivo de cada exclusión y arrastra sus avisos.** Si el calendario no
respondió, dice que no pudo verificar blackouts en vez de reportar cero exclusiones. Un
escáner que descarta en silencio no es auditable.

### El reparto entre script y comando

Los pipelines producen los **datos**; el texto lo escribe el comando. `pipeline_carrusel.py`
y `pipeline_informe.py` tienen dos pasos (`--preparar` y `--rendir`) y el segundo **se
detiene** si un campo editorial quedó vacío, por la misma razón que el renderer falla ante
una imagen inexistente: una pieza a medias que sale sin avisar llega al cliente.

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
- **Bloque "🔤 Diccionario rápido"**: obligatorio en el **Modo anticipación** de `/dato_macro` y en `/noticia` cuando aparezcan siglas. Por cada abreviatura del mensaje (ISM, NFP, JOLTS, PMI, PCE, IPC, ADP…), una línea explicativa en voz novata. **Ninguna abreviatura puede quedar sin explicación en español ese día.** En el **Modo resultado** el mensaje es el pie de una imagen y el bloque no cabe: la sigla se explica **en línea**, dentro de la frase, una sola vez ("vacantes de empleo (JOLTS)"). Cambia el dónde, no el si.
- **Fuente canónica**: `data/glosario_siglas.json` (`SIGLA → {nombre_es, explicacion}`). Si aparece una sigla nueva, explicarla al vuelo y **añadirla al JSON** para reutilizarla.
- En `/dato_macro`, la fuente principal del panorama del día es la tool MCP `obtener_calendario_macro` (calendario Investing.com — Chile/EE.UU./China/Zona Euro, con resultado real `actual` y clasificación mejor/peor/en_linea); WebSearch sobre investing.com + fuentes oficiales son fallback solo si la tool devuelve `{"error": ...}`.

### Dos modos de `/dato_macro` y plantilla del Modo resultado (issue #93)
`/dato_macro` genera el mensaje en uno de **dos modos**, elegidos automáticamente según la hora del evento vs. la hora actual de Chile:
- **Modo anticipación** (dato `🕐 PRÓXIMO`, aún no sale): qué es + hora CLT + anterior/consenso + 3 escenarios (mejor/peor/en línea) + activos a observar + temporalidad del impacto.
- **Modo resultado** (dato `✅ YA SALIÓ`, ya tiene valor `actual`): **la pieza es la Story, el texto es su pie de foto** (decisión del director, 2026-08-04). El desarrollo largo —sub-lecturas, "🧠 ¿Qué significa esto?", "⚠️ PERO ojo con el detalle", "💡 Impacto esperado por activo" y el diccionario— vive dentro de la imagen de `/story dato_macro` y **ya no se manda además como texto**: mandar ambos obliga al cliente a leer dos veces lo mismo, y con imagen adjunta WhatsApp corta el pie antes que un mensaje suelto. Reglas:
  - **Orden**: primero la Story, después el pie escrito desde el mismo payload — veredicto y cifras tienen que coincidir entre imagen y texto.
  - **Pie**: chip `📊 DATO MACRO · [PAÍS]` + hora de publicación + indicador con cifra + veredicto *PEOR / MEJOR / EN LÍNEA* frente al consenso + una línea de implicancia direccional + la temporalidad + el cierre canónico.
  - **El pie repite el veredicto de la imagen a propósito**: es lo que se ve en la notificación de WhatsApp antes de abrir el chat, y lo único legible si el cliente no descarga la imagen. Un adjunto sin pie llega mudo.
  - **⏱️ Temporalidad del impacto** (OBLIGATORIA, ambos modos): scalper / intradía / swing de jornada / posicional (mismas 4 etiquetas canónicas). Va en el pie porque **no** está en la imagen — es la única pieza del desarrollo largo que sobrevive en el texto.
  - La plantilla larga del issue #93 queda en el historial git por si se decide volver a ella.
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
| COPPER | 1 | $14274.0 USD/t | $14.274 / 14274 |

*El Cobre se analiza y cotiza siempre por su valor por tonelada métrica (`USD/t`) disponible en el terminal MT5.*
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

## Antigravity (AGY) — el segundo runner

El repo lo ejecutan **dos** agentes: Claude Code y Antigravity. Antigravity llama
*workflows* a lo que Claude Code llama slash commands: archivos markdown en
`.agents/workflows/`, invocables igual con `/nombre`.

Ocho comandos están expuestos a AGY —`/story`, `/oportunidad`, `/alerta`,
`/carrusel`, `/informe`,
`/dato_macro`, `/apertura` y `/chart`—: los que generan piezas visuales y los
datos que las alimentan. Los de día, los educativos y los internos siguen siendo
solo de Claude Code.

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
| **WebSearch (investing.com + fuentes oficiales)** | ✅ Activo | Calendario económico y noticias relevantes | `/dato_macro`, `/noticia` y comandos de día |
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
resuelve alias en lenguaje natural (`metales`, `oro`, `forex`, `cripto`…). `01_macro_y_apertura` es el **grupo
padre** (comunidad), y cada canal temático recibe además su propia lectura macro.

> [!CAUTION]
> **Automatizar WhatsApp Web va contra sus términos de servicio** y el número es el del negocio. El sender
> impone 45 s mínimos entre envíos y un cupo de 40 al día (`seguridad` en `config/whatsapp_grupos.json`,
> contador en `data/.whatsapp_envios.json`). No subas esos límites, no metas el envío en un bucle y no lo
> lances en paralelo: el perfil de sesión no admite dos procesos a la vez.

## Stories GI y Generación de Imágenes

> [!CRITICAL]
> **Prohibición Total de Modelos de Difusión / IA Text-to-Image (`generate_image`)**: Queda **estrictamente prohibido** utilizar la herramienta `generate_image` o modelos de generación de imágenes por difusión de IA para crear piezas, terminales, infografías o gráficos en este proyecto. Todo el contenido visual DEBE ser maquetado en HTML/CSS estructurado (`templates/stories/`) con datos reales y renderizado vía Playwright/Chromium siguiendo el Brandkit oficial.

Piloto (issue #109): comando `/story [tipo]` genera Stories de marca (imagen 1920×1080 o 1080×1920).
`[tipo]` soportados hoy: `dato_macro`, `alerta`, `recomendacion`, `quote`, `breaking`, `encuesta`,
`edu` (Fase B, issues #121/#123/#125/#127), `flash` (Fase C, issue #129), `postventa` (Fase C) y
`calendario` (fuera de fase, pedido directo del director 2026-08-10). `calendario` señala los
eventos macro más relevantes de la semana (selección editorial de 3 a 6, no un volcado del
calendario completo): usa la piel de `oportunidad` (sello con pulso, CTA, disclaimer) pero sin
activo protagonista, así que cae al acento de marca en vez de a un color por activo — mismo
fallback que ya usan `alerta`/`recomendacion` con un activo sin token de color. Consume
`obtener_calendario_macro` en vez de `get_asset_levels`.
`dato_macro` cubre la **pieza 1 de la agenda diaria** —un dato económico que ya publicó, en el Modo
resultado de `/dato_macro`—, donde **es el entregable principal**: desde 2026-08-04 el mensaje de
texto de ese modo quedó reducido al pie de esta imagen. Se organiza alrededor del veredicto frente
al consenso; su
`veredicto_slug` NO se deriva de `sesgo`, porque mejor/peor es contra lo esperado y no una dirección
de mercado (un dato "mejor" puede ser bajista para un activo). **El veredicto exige un consenso
publicado**: solo se pone cuando existe la cifra que el mercado esperaba y se tiene a la vista —la
trae el calendario junto al dato—. Un número sin consenso (flujos de ETFs, un volumen, una cifra
suelta de una noticia) puede ir como evidencia, pero con el campo de veredicto vacío; etiquetar
"mejor de lo esperado" algo que nadie pronosticó afirma una comparación inexistente y el cliente la
lee como hecho verificado. `recomendacion` es la **única
plantilla con firma acreditada** —una recomendación induce una operación, así que tiene que constar
quién la respalda— y **cuenta para el límite de 3 señales por semana**; obliga a TP y SL en pesos y
tiene campo para el costo de mantención (swap), que es lo que separa una operación comunicada con
honestidad de una que solo muestra la ganancia. `alerta` (plantilla "03 Alerta de Mercado") combina niveles reales del motor
(`get_asset_levels`) con una narrativa de alerta (mismo criterio editorial de `/alerta`). **Regla de Inyección Obligatoria de Niveles en Gráficos de Stories**: el payload DEBE incluir obligatoriamente el array `hitos` (punto `actual` con precio formateado y guía) y el array `niveles` (líneas horizontales con `etiqueta` y `rol`, como $S_1$, $R_1$ o barreras macro/intervenciones soberanas como el nivel MOF 160.000 en USD/JPY). Queda terminantemente prohibido generar gráficos con la serie de velas muda / sin niveles numéricos trazados. `quote`
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
del motor en frío.

`oportunidad` es la pieza que **invita a operar**, y la única que no se invoca desde `/story`: la
genera su propio comando `/oportunidad`, que además redacta el mensaje de WhatsApp que la acompaña.
El protagonista es el **activo operable** —nombre, dirección, precio de ahora y hacia dónde va— y el
dato macro que la origina baja a evidencia lateral, donde arriba va la LECTURA ("menos empleos en
EE.UU.") y abajo la cifra que la prueba: el número solo no le sirve a nadie. **No es una señal y no
debe convertirse en una**: no lleva entrada, TP, SL ni volumen, porque eso exigiría firma acreditada
y contaría para el límite de 3 por semana — para eso está `recomendacion`. Su gráfico es
**escenario a sangre** y no una tarjeta con ejes, así que consume la serie real de MT5 vía
`scripts/serie_mt5.py` y pide `"ajuste": "llenar"` en el `recorrido`; es el único caso donde el SVG
se estira, porque deformar un gráfico que se lee cambiaría la pendiente que el cliente está
midiendo. Cada activo aporta su color (`--activo-*` en `marca.css`) y su imagen
(`templates/stories/assets/activos/<slug>.jpg`, generadas con IA — recetario en
`docs/design/stories-gi/imagenes-por-activo.md`). Identidad del activo y dirección de mercado son
roles de color **distintos**: el activo pinta el escenario y `--sube`/`--baja` la dirección; si se
colapsaran, una pieza dorada bajista se leería como alcista dorada. Diseño completo en
`docs/superpowers/specs/2026-08-04-rediseno-stories-gi-design.md`.

Único renderer: `scripts/story_render.py`
(payload JSON → HTML → PNG con Playwright headless). **Formato del lienzo y Regla de Formatos**:
- **Horizontal 16:9 (`1920×1080`)**: Exclusivo para **`alerta` y piezas con gráficos técnicos MT5**, donde la amplitud temporal de velas es indispensable.
- **Vertical 9:16 (`1080×1920`)**: **Obligatorio para toda imagen con carga textual y sin gráfico** (calendarios, agendas, guías pedagógicas `edu`, conceptos y breaking news). En vertical rige el criterio de ultra-legibilidad móvil del Brandkit: titulares Goldman 700 a 64px, tarjetas a 38px, cuerpo en 28-32px peso 600/700 y márgenes estrechos (~44px) para lectura natural en celular sin zoom.
El formato viaja por el CLI (`--formato horizontal|vertical`) y **nunca** por el payload — el payload es contrato de contenido y el formato es presentación, así el **mismo payload rinde ambos**. Cada snapshot es un único archivo que se adapta con `@media (max-aspect-ratio: 1/1)`. Snapshots de marca vigentes: `templates/stories/alerta.html`, `templates/stories/breaking.html`, `templates/stories/dato_macro.html` y `templates/stories/calendario.html`. Las demás plantillas del canvas llegan con los issues #111-#115.

**Paleta y color (una sola fuente).** Los colores viven en `templates/stories/marca.css` y los
snapshots los consumen con `var(--rol)`; ningún hex se escribe a mano. Los tokens se nombran por
**rol y no por color** (`--acento`, no `--teal`): un nombre de color miente en cuanto se cambia la
paleta. `scripts/marca_tokens.py --check` falla si una plantilla vuelve a hardcodear un color, que
es lo único que mantiene la fuente única siendo única.

Dos reglas de color que se pagaron caro y no conviene volver a discutir:

1. **El cromo no opina.** Marco, chip, borde y degradado van siempre en el acento de marca. Solo se
   colorea lo que ES un dato: la píldora de dirección, la variación, el veredicto, el resultado
   cuando es negativo. Una pieza bajista bañada en rojo se lee como alarma y contradice la regla de
   tono del proyecto (énfasis direccional sí, dramatización no). En una frase: **si un color no está
   comunicando un número, va en el acento**.
2. **`--sube` / `--baja` no se reskinean.** Verde arriba y rojo abajo es una convención que el
   cliente lee sin pensar, no una decisión de marca. Al cambiar la línea visual se cambia
   `--acento`, nunca la semántica de dirección.

El acento es `#50C0A8`, el extremo verde del degradado del logo (el azul `#3C8CAA` es el otro
extremo y queda disponible como `--acento-azul`). Ambos medidos sobre los assets de
`templates/stories/assets/`, no elegidos a ojo.

**Piel compartida.** La línea visual de `oportunidad` —capas de fondo, imagen y
color por activo, sello con pulso, tipografía de titulares en Space Grotesk 800,
CTA y footer— vive en `templates/stories/piel.css`, hermano de `marca.css`. La
consumen `oportunidad`, `alerta` y `recomendacion`; las otras ocho plantillas
migran de a una (misma regla que las Fases B y C: una plantilla por Change).

Se estandariza la **piel**, no la **estructura**. `recomendacion` conserva
entrada, TP, SL, volumen y firma acreditada; `alerta` conserva su tarjeta de
niveles; ambas conservan el gráfico como tarjeta legible, porque ahí los niveles
son contenido y no atmósfera. Con el layout de `oportunidad` esos campos bajarían
a letra chica y se borraría la distinción entre **invitar a operar** y
**recomendar una operación** — la segunda lleva firma y cuenta para el límite de
3 señales por semana.

El orden de carga es `marca.css` → `piel.css` → `<style>` de la plantilla, y
`scripts/marca_tokens.py --check` escanea las hojas propias además de las
plantillas (`marca.css` queda fuera: es donde los hex sí van).

**Revisar y proteger las plantillas.** Cada plantilla tiene su payload de prueba en
`tests/fixtures/stories/payloads/<plantilla>.json`, y esas MISMAS fixtures alimentan dos cosas:

```bash
uv run --extra stories python scripts/rendir_todas.py            # las 10 piezas juntas
uv run --extra stories python scripts/rendir_todas.py --formato vertical
uv run pytest tests/test_story_render.py                          # contrato de las 10
```

El render completo existe porque **los defectos de consistencia no se ven revisando de a una**: un
cambio global de paleta puede dejar piezas sin regenerar, y un color equivocado sobrevive rondas
enteras si la revisión está puesta en otra plantilla. El test exige que toda plantilla de
`templates/stories/` tenga fixture y resuelva sin tokens huérfanos — una plantilla nueva sin payload
falla, que es lo que corresponde, porque tampoco la estaría revisando nadie.

**Serie real para los gráficos.** `scripts/serie_mt5.py` trae los cierres del terminal y arma el
bloque `recorrido` que consume `story_grafico.py`. Los marcadores se anclan por ROL, no
por proximidad de precio: `actual` y `meta` van al extremo derecho por definición, y `origen` se
ancla por tiempo cuando el hito trae fecha. Anclar por precio parece razonable y no lo es —el precio
oscila, así que el cierre más parecido puede caer en cualquier punto de la serie—. Requiere el
terminal abierto y `MetaTrader5`, que no es dependencia del repo: se inyecta con
`uv run --with MetaTrader5`.

**Generación de Gráfico con `story_grafico.py`**: traduce la serie de precios y los hitos/niveles
al SVG del token `{{grafico}}` y se encadena por stdin/stdout:
```bash
uv run python scripts/story_grafico.py < alerta.json \
  | uv run python scripts/story_render.py --template templates/stories/alerta.html \
      --out "$(scripts/ruta_story.ps1 ...)" --formato horizontal
```
El payload de entrada lleva una clave `recorrido` = `{serie, marcadores}`; el script la consume y la
reemplaza por `grafico`. El reparto es estricto: el script calcula **coordenadas** y el snapshot
aporta color/tipografía vía sus clases `.g-*` — si el gráfico se ve mal, se corrige en la plantilla.
**Criterio editorial de la pieza** (impuesto por el director): cada bloque dice algo que ningún otro
bloque dice — chip = qué pasó, titular = por qué, tarjeta = la operación y su resultado, gráfico =
el recorrido (único lugar con precios), cierre = lo que no cabe arriba. El espacio también se
justifica: nada de aire que no comunique. Integrarla como tipo de `/story` queda **pendiente**.

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

## Capacitaciones internas (PPTX)

Material formativo para el equipo comercial y los IBS, generado por código para que el
contenido sea versionable y regenerable. Vive en `docs/capacitacion/`.

- **Generador**: `scripts/capacitacion_fundamental_ppt.py` (motor de maqueta) +
  `capacitacion_fundamental_contenido.py` (criterio editorial). La separación es
  deliberada: editar un texto no debe obligar a tocar el dibujo, ni al revés.
  ```bash
  uv run --with python-pptx --with pillow python scripts/capacitacion_fundamental_ppt.py
  ```
  `python-pptx` y `pillow` **no** son dependencias del proyecto: se inyectan con
  `uv run --with` para no alterar el `.venv`.
- **Autoría**: el retrato del autor va en la portada y en el cierre, junto al nombre y
  las credenciales — es material que circula entre equipos, así que quién lo firma se ve
  de entrada. La foto se toma de `docs/capacitacion/assets/autor.png` (o de `--foto
  <ruta>`) y se recorta en círculo con Pillow, porque PowerPoint no aplica máscaras. El
  recorte se hace desde el tercio superior, no del centro geométrico, para no cortar la
  cabeza. Si el archivo no existe, la maqueta cae al diseño sin retrato en vez de fallar.
- **Tipografía**: Segoe UI + Consolas para cifras, **no** las fuentes de marca. Syne /
  DM Sans / Space Grotesk solo existen en el repo como `.woff2` (formato web) y no están
  instaladas en los equipos: declararlas hace que PowerPoint las sustituya y rompa la
  maqueta en el PC de cada destinatario. Consolas preserva el alineado tabular del kit.
- **Medición de texto**: PowerPoint no expone métricas de fuente, así que el motor
  estima el alto de cada bloque antes de dibujar (`_n_lineas` / `_alto_texto`) y reduce
  el tamaño hasta que quepa. Sin eso el layout falla de dos formas ya observadas: un
  título de dos líneas se superpone con el párrafo siguiente, y una tabla larga se
  expande por debajo del pie —PowerPoint ignora `row.height` si el texto no cabe—.
- **Verificación obligatoria**: con decenas de slides la inspección visual no basta.
  ```bash
  uv run --with python-pptx python scripts/verificar_capacitacion.py
  ```
  Detecta desbordes sobre el pie y solapamientos entre bloques de texto. Complementarlo
  exportando a PNG vía COM (`$pres.Export($ruta,"PNG",1600,900)`) para revisar el
  resultado real. **Ojo**: si el director tiene el `.pptx` abierto, `prs.save()` falla
  con `PermissionError` y COM rechaza la conexión con `0x80048240` — generar entonces a
  una ruta temporal y nunca llamar a `$app.Quit()`, que cerraría su sesión.

### Guía rápida (folleto de consulta)

Complemento de la capacitación, para quien no va a estudiar las 55 láminas pero necesita
resolver una pregunta con el cliente al teléfono. No es un resumen: es una **herramienta
de respuesta** —tabla dato → dirección de cada activo, frases listas para el cliente,
qué no decir, y dónde se detiene la respuesta porque pasa a ser asesoría—.

- **Fuente**: `templates/capacitacion/folleto.html` · **Generador**:
  `scripts/folleto_fundamental.py`
  ```bash
  uv run --extra stories python scripts/folleto_fundamental.py
  ```
- **Dos salidas del mismo HTML**: un **HTML autónomo** (fuentes incrustadas en base64,
  se manda por correo o WhatsApp y funciona solo) y un **PDF A4 de 6 páginas** para
  imprimir. Bajo 820 px las hojas A4 se rompen en una columna y las tablas anchas pasan
  a fichas apiladas vía `td[data-rot]::before`, para consultarlo en el teléfono sin
  hacer zoom.
- **Tipografía: DM Sans en todo, también en los títulos.** Las fuentes del repo se
  pueden usar acá y no en el PPTX porque en HTML los `.woff2` funcionan nativamente,
  pero **Syne queda fuera**: en peso 800 sus contraformas se cierran y cansa la vista en
  un documento de consulta (es el mismo defecto que motivó el rediseño de la Story). El
  cuerpo va a 11 pt y no a 9,8 por legibilidad — el material lo usa gente que no lee
  cómodo a tamaños chicos. Space Grotesk queda solo para cifras y siglas.
- **Paleta adaptada al soporte claro**: el verde y el rojo de marca están pensados para
  fondo oscuro y sobre blanco no alcanzan el contraste mínimo para texto (mismo problema
  del footer de las Stories, #145). Se usan versiones oscurecidas para tipografía y los
  originales solo en filetes y fondos.
- **La escala está calibrada al alto útil de una A4** (1123 px a 96 dpi). Si una hoja se
  pasa, Chromium la parte en dos y el PDF duplica páginas —pasó de 3 a 6 sin aviso—. Al
  agregar contenido hay que **medir**, no estimar:
  ```js
  Array.from(document.querySelectorAll('section.hoja')).map(s => s.getBoundingClientRect().height)
  ```
  con `emulate_media("print")`. Y no poner `font-size` dentro de `@media print`: cambia
  la escala justo en el PDF y descuadra la calibración.

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

**Tipos de archivo** (carpeta `<tipo>`): niveles, dato_macro, noticia, alerta, encuesta, señal, concepto, pregunta, respuesta, cierre, earnings, postventa. La salida de `/apertura` usa tipo `niveles`.

**Piezas públicas limpias (sin guiones internos)**: los comandos y flujos que generan piezas de mercado (`/alerta`, `/apertura`, `/dato_macro`, `/noticia`, `/señal`, `/oportunidad`, `/story`, etc.) entregan **exclusivamente material para el cliente final** (mensaje de WhatsApp + Story visual de marca). Queda estrictamente excluido del flujo la generación automática o paralela de guiones internos o piezas para ejecutivos. El material 100% interno queda reservado única y exclusivamente a los comandos dedicados `/ventas` (para el equipo de ventas) y `/postventa` (para el equipo de post-venta).

**Convención de nombres de chart (issue #81)**: los PNG de `data/charts/` siguen el patrón único `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`, con el mismo `<activo_slug>` de `ruta_mensaje.ps1` (#45) — `lowercase(ticker_mt5)` sin `.spot`/`#`/`/` — y `<TF>` en mayúscula MT5 (`M15`/`H1`/`H4`/`D1`). Ej: `usdclp_H4_2026-06-07_11-45.png`. Los `data/charts/*.png` están gitignored.

**Nunca se envía nada al grupo sin aprobación explícita del director.**

**Nota**: los selectores del sender están medidos contra el DOM real de WhatsApp Web y comentados en
`src/whatsapp_sender.py`. WhatsApp cambia su interfaz sin avisar: si un envío empieza a fallar, el primer paso es
volver a medir esos selectores, **nunca** relajar la verificación de entrega.

## Slash Commands disponibles (29)

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
| `/story [tipo]` | Genera una Story de marca GI (imagen 1920×1080). `[tipo]` soportados hoy: `dato_macro`, `alerta`, `recomendacion`, `quote`, `breaking`, `encuesta`, `edu`, `flash`, `postventa`, `calendario`; demás plantillas en #111-#115. Ver sección "Stories GI". |
| `/oportunidad [activo]` | Pieza que invita a operar: imagen (plantilla `oportunidad`) + mensaje de WhatsApp con contexto, llamado a la acción, fuente y disclaimer. Precios SIEMPRE del motor — si MT5 falla, se detiene, nunca deduce. No es señal: sin entrada, TP ni SL. Máximo 3 al día. |
| `/carrusel` | Carrusel responsivo de alertas de mercado: `screener_gi.py` detecta la sesión activa y hora real, puntúa el universo con el `Score_GI` y elige el Top 3; el comando escribe el texto y rinde las Stories en ambos formatos. Máximo 3 imágenes (WhatsApp corta con `+2` a partir de la cuarta). |
| `/informe [apertura\|cierre]` | Informe de la jornada. Apertura en PDF institucional A4; cierre chat-first (mensaje + gráfico), por el criterio de canal de la skill de reporte editorial. La apertura no se emite con el sesgo del motor vencido salvo `--con-datos-viejos`, que estampa el aviso. |
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
│   ├── commands/          ← 27 slash commands (invocar con /nombre)
│   │   ├── domingo.md
│   │   ├── lunes.md · martes.md · miercoles.md · jueves.md
│   │   ├── viernes_am.md · viernes_pm.md
│   │   ├── encuesta.md · rencuesta.md · curriculo.md
│   │   ├── apertura.md · actualizacion.md · dato_macro.md · noticia.md · chart.md · story.md · oportunidad.md
│   │   ├── carrusel.md · informe.md   ← produccion diaria en 3 tandas
│   │   ├── señal.md · alerta.md · concepto.md · pregunta.md · respuesta.md · ventas.md · postventa.md · estado.md
│   │   └── accion.md · earnings.md
│   └── shared/modo_ejecutivo.md  ← contrato del flag `ejecutivo` (guion_ejecutivo.txt)
├── agents/                ← prompts de sub-agents
│   ├── recolector.md · analista.md · redactor.md
├── config/                ← configuración del sistema
│   ├── activos.json       ← 38 tickers: forex + commodities + 6 criptos + índices + 5 ETF + 14 acciones
│   ├── drivers.json · drivers_indices_sectores.json
│   ├── agenda_semanal.json · feriados_bolsa.json
├── scripts/               ← scripts auxiliares
│   ├── screener_gi.py     ← Score_GI sobre el universo + gates (feriado, blackout, Playbook, ATR)
│   ├── pipeline_carrusel.py ← Top 3 del escaner → 3 Stories (--preparar / --rendir)
│   ├── pipeline_informe.py  ← informe de apertura (PDF) y de cierre (chat-first)
│   ├── sincronizar_css_plantillas.py ← re-embebe marca.css/piel.css en los 12 snapshots
│   ├── story_render.py    ← renderer de Stories GI (payload JSON → HTML → PNG con Playwright)
│   ├── story_grafico.py ← geometría del gráfico de recorrido (paso previo al render)
│   ├── serie_mt5.py       ← serie real de precios desde MT5 → bloque `recorrido`
│   ├── rendir_todas.py    ← rinde las 10 plantillas juntas, para revisión visual
│   ├── marca_tokens.py    ← verifica que ninguna plantilla hardcodee un color
│   ├── capacitacion_fundamental_ppt.py + _contenido.py ← generador del PPTX de capacitación (motor / contenido)
│   └── hora_chile.ps1 · ruta_mensaje.ps1 · ruta_story.ps1  ← helpers deterministas (hora Chile, ruta de guardado)
├── templates/             ← templates de mensajes WhatsApp
│   ├── encuesta_tendencia.txt · encuesta_posicion.txt · encuesta_movimiento.txt
│   ├── concepto_didactico.txt · guion_ejecutivo.txt
│   ├── ruta_curriculo.txt · dashboard_metricas.txt · mapa_conceptos.txt
│   ├── ventas_email.txt · ventas_whatsapp.txt
│   └── stories/           ← snapshots de marca GI (11 plantillas) + marca.css · fonts/ · assets/activos/
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

## Stories GI — CSS embebido (solución Playwright 2026-08-12)

**Problema:** `story_render.py` genera HTML temporal y lo navega con `file://`, pero Playwright no resolvía las rutas relativas `<link href="marca.css">`, causando que los estilos no se cargaran. Resultado: elementos visibles en el HTML (como fecha/hora) no aparecían en el PNG final, sin error visible.

**Solución (IMPLEMENTADA):** Embeber CSS directamente en cada plantilla HTML en bloques `<style>`, eliminando la dependencia de rutas externas.

**Cómo se aplicó:**
- Todas las plantillas (`alerta.html`, `dato_macro.html`, `calendario.html`, etc.) ahora incluyen `marca.css` y `piel.css` (si aplica) incrustados en `<style>` en el `<head>`.
- Script de automatización: `scripts/embeber_css_plantillas_v3.py` (incrusta CSS en cualquier plantilla que lo use).

**Impacto:**
- ✅ Playwright siempre tiene estilos disponibles, sin resolver rutas.
- ✅ Elementos como fecha/hora ahora son visibles en los PNG.
- ✅ No hay cambio en el contrato de tokens `{{campo}}` ni en `build_context`.

**Si agregas una plantilla nueva:**
- Si usa `<link rel="stylesheet" href="marca.css">` o `piel.css`, ejecuta:
  ```bash
  uv run python scripts/embeber_css_plantillas_v3.py
  ```
- O embebe manualmente el CSS en un `<style>` antes del `</head>`.
