# Reglas del proyecto — Grupo de Análisis de Mercado

Antigravity no lee `CLAUDE.md`, así que este archivo trae las reglas que
**cualquier** pieza tiene que cumplir. No las reemplaza: `CLAUDE.md` sigue siendo
la fuente completa y, ante cualquier duda o contradicción, manda `CLAUDE.md`.

Léelo antes de ejecutar cualquier workflow de `.agents/workflows/`.

---

## 1. Los datos no se inventan (Cero Hardcoding)

Precios, cotizaciones, niveles, indicadores, calendario económico y operaciones abiertas salen
**siempre y en tiempo de ejecución** del MCP `market-data`. Nunca de tu memoria, nunca de una búsqueda web,
nunca deducidos de otro número, **nunca escritos a mano en strings de plantillas o markdowns**, y NUNCA delegados a un subagente que pueda alucinar el resultado. 

Para asegurar fidelidad:
- Extrae el precio y los niveles ejecutando tú mismo las tools del MCP (ej. `get_asset_levels`, `get_curva_tasas`, o `latest_prices_summary.json`).
- **Mapeo estricto de tickers del broker:** Para índices, commodities y activos con cotización spot en MT5, utiliza siempre el símbolo exacto del catálogo: `US100.spot`, `US500.spot`, `US30.spot`, `WTI.spot`, `BRENT.spot`, `GER40.spot`, `COPPER`, `USDCLP`, `XAUUSD`, `USDJPY`.
- **Prohibición de Truncado de Símbolos de Dólar ($):** Al guardar mensajes en archivos `.txt`, queda prohibido usar strings con comillas dobles en PowerShell (`@"..."@`), ya que PowerShell interpreta `$931` o `$14` como variables nulas y borra el precio. Toda persistencia de textos con cotizaciones se debe realizar mediante Python (`Path.write_text(..., encoding="utf-8")`) o bloques no interpolados.

Si el MCP falla, **detente y dilo**. Una pieza con un precio inventado o hardcodeado es peor que
ninguna pieza: el cliente opera con ella.

### Qué hacer cuando el motor dice que no

El MCP devuelve `{"error": "CÓDIGO", "message": "..."}` cuando no puede darte el
dato. Ese error es una respuesta, no un obstáculo: **detente y repórtaselo al
director con el código exacto**. Él decide.

Lo que está prohibido, sin excepción:

- Completar el dato faltante con una estimación, un recuerdo o un número
  plausible. Un precio que nadie verificó dentro de una pieza que invita a
  operar es el peor resultado posible de este proyecto.
- **Modificar la configuración del proyecto para sortear el error.** Si el activo
  no está en `config/activos.json`, no lo agregues; si falta un color en
  `marca.css`, no lo inventes; si falta una imagen en
  `templates/stories/assets/`, no la descargues. Propónselo al director y espera.
  Puede que el activo no esté a propósito.

`TICKER_NOT_FOUND` merece una aclaración: el catálogo se carga cuando arranca el
servidor MCP, así que un activo agregado después aparece como inexistente hasta
reconectar. Si sospechas de eso, dilo — no lo resuelvas por tu cuenta.

### "Mejor/peor de lo esperado" exige un consenso publicado

El chip de veredicto compara un dato contra lo que el mercado **esperaba**. Solo se
puede usar cuando existe esa cifra de consenso y la tienes a la vista: la trae el
calendario económico junto al dato.

Un número sin consenso —flujos de ETFs, un volumen, una cifra de una noticia— puede
ir en la pieza como evidencia, pero **sin veredicto**. Ponerle "mejor de lo
esperado" a algo que nadie pronosticó es afirmar una comparación que no existe, y
el cliente la lee como un hecho verificado.

## 1 bis. Escribe los archivos en UTF-8 y CUIDADO con las tuberías (`|`)

En Windows, `Set-Content` y `Out-File` de PowerShell usan por defecto la
codificación ANSI del sistema. Además, **usar tuberías (`|`) en PowerShell (ej: `Get-Content payload.json | python script.py`) corromperá irremediablemente los caracteres UTF-8 (tildes, eñes, y el punto medio `·`) inyectando signos de interrogación (`?`)**, ya que PowerShell transforma los bytes en Strings y los envía usando `$OutputEncoding` en US-ASCII.

Para ejecutar los pipelines encadenados (como `serie_mt5 | story_grafico | story_render`), **NUNCA uses la consola de PowerShell conectando comandos con `|` o `Get-Content`**. Escribe un pequeño script puente en Python que lea el JSON en bytes y utilice `subprocess` para ejecutar el pipeline de forma segura y binaria.

Un payload JSON mal escrito llega al renderer con los acentos rotos, y la pieza sale con `AN?LISIS`, `inversi?n`, `?Quieres`.

Usa siempre UTF-8 explícito:

```powershell
$json | Out-File -FilePath payload.json -Encoding utf8
```

o escribe el archivo con la herramienta de escritura del agente en vez de por
consola. **Antes de dar una pieza por buena, mira el PNG y verifica que los
acentos y los signos `¿` `¡` `·` se vean correctos.** Si aparece un `?` donde
debería haber una tilde, el problema es este y la pieza no se puede publicar.

## 2. La fecha y hora salen del reloj, no de la web (Guardrail de Consistencia Temporal)

Nunca uses búsqueda web para saber la fecha o la hora. Para la hora de Chile:

```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$now.ToString('yyyy-MM-dd HH:mm')
```

Para convertir la hora de un dato económico extranjero, usa `scripts\hora_chile.ps1` — nunca offsets fijos, que producen desfases de una hora cuando cambia el horario de verano.

### Regla Estricta Anti-Anacronismos (Eventos Futuros vs Pasados)
Queda **terminantemente prohibido** redactar eventos futuros en tiempo pasado (ej. "tras la asimilación de los discursos de Jackson Hole", "luego del dato de inflación") si dicho evento aún no ha ocurrido según el reloj real de Chile.
- **Eventos Futuros / Próximos:** Se redactan exclusivamente en **Modo Anticipación** ("en la antesala de...", "a la espera de los discursos previstos para mañana...", "el mercado aguarda la publicación...").
- **Validador Automático:** `generar_pdf.py` y `pipeline_informe.py` ejecutan automáticamente `scripts/validar_consistencia_temporal.py`. Si detectan discrepancia de fecha o anacronismos en el texto, el proceso aborta inmediatamente (*Fail-Fast*).

## 3. Los decimales de cada precio están definidos

Todo precio respeta el campo `digits` de `config/activos.json` para ese activo.
Nunca truncar ceros al final ni redondear a entero.

| Activo | Digits | Correcto |
|---|---|---|
| USDCLP | 2 | $889.60 |
| USDJPY | 3 | 163.731 |
| XAUUSD | 2 | $4,539.72 |
| WTI.spot | 2-3 | $90.18 |
| US100.spot | 2 | 30,350.01 |
| Acciones | 2 | $192.50 |
| COPPER | 1 | $14274.0 USD/t |

*El Cobre se analiza y cotiza siempre por su valor por tonelada métrica (`USD/t`) disponible en el terminal MT5.*

## 4. Tono: profesional con gancho, nunca dramático

El cliente tiene que entender **hacia dónde va el activo**. Un análisis sin
dirección clara está incompleto: esa es la regla de oro.

Se toma postura direccional y se redacta para que dé ganas de operar. Lo que está
prohibido es el lenguaje extremo o coloquial:

| Evitar | Usar |
|---|---|
| "el oro se va a derrumbar" | "sesgo bajista" |
| "esto se va a disparar" | "impulso comprador" |
| "el mercado tiene una sensación pésima" | "presión vendedora" |

Toda sigla se explica en español la primera vez que aparece. Nada de jerga sin
traducir: el mensaje lo lee tanto un trader como alguien que recién empieza.

Si el texto va a un cliente, va en español chileno neutro, con tuteo. Nunca
voseo argentino. La firma institucional oficial es **Área de Research & Estrategia**.

**Nunca el guion largo como inciso.** En texto de cliente (mensajes, pies de
Story, textos dentro de las piezas) no se usa `—` ni `–` para abrir un inciso:
"el stop en 1.758,09 — para eso está" se escribe "el stop en 1.758,09. Para eso
está". Punto seguido, coma o dos puntos según el caso. Es una marca reconocible
de texto generado por IA y el material se firma con el nombre de un analista
real: si se lee como escrito por una máquina, la firma pierde credibilidad. El
punto medio `·` sí se mantiene, porque es separador del kit de marca
(`ORO · XAU/USD`) y no puntuación de frase.

## 5. Terminología de niveles, Trazado Horizontal Obligatorio e Indicadores

Siempre "soporte" y "resistencia". Nunca "techo" ni "suelo".

### Regla de Oro de Trazado Horizontal Obligatorio en Gráficos e Inyección en Stories
Todo nivel numérico citado en el texto ($S_1, S_2, R_1, R_2$, Fibonacci 50%, medias o niveles tácticos), así como **barreras macroeconómicas de intervención soberana** (ej. nivel de intervención MOF 160.000 en USD/JPY, techos cambiarios del BCCh, metas de inflación) **deben estar obligatoriamente trazados como líneas horizontales explícitas y etiquetas de precios en el gráfico**.
- **En Gráficos de Informe (Matplotlib):** Se trazan con `ax.axhline` y sus anotaciones de texto.
- **En Gráficos de Stories (SVG / Playwright):** Queda **estrictamente prohibido** enviar payloads con gráficos mudos (solo curva de velas). Todo payload para `alerta.html`, `recomendacion.html` u otras plantillas con gráfico DEBE incluir obligatoriamente:
  1. `hitos`: Marcador del punto `actual` con guía y precio formateado (`"clase": "actual"`, `"rol": "SPOT"`).
  2. `niveles`: Lista de niveles horizontales que cruzan todo el gráfico (`"clase": "meta" | "resistencia" | "soporte" | "nivel"`), con `"etiqueta"` (precio formateado a sus `digits`) y `"rol"` explícito (ej. `"MOF INTERVENCIÓN"`, `"RESISTENCIA R1"`, `"SOPORTE S1"`).
Nunca dejar un nivel mencionado en la prosa sin su correspondiente línea visual y etiqueta numérica en el gráfico.

### Embudo Técnico / Zona de Compresión
Cuando múltiples medias móviles (EMAs 50/100) y retrocesos de Fibonacci colisionan en una franja estrecha, se sombrea el área y se explica en el análisis como un *embudo de decisión previo a una expansión de volatilidad*.

### Criterio de Estado de Mercado (USD/CLP Mercado Cerrado)
Durante la sesión asiática / nocturna, el mercado formal chileno permanece cerrado. La narrativa sobre el USD/CLP se aborda como **Radar de Madrugada**, monitoreando el Cobre en LME/Shanghái ($14.274,0 USD/t) y el DXY para proyectar la apertura formal de las 08:30 CLT.

### Modelo ADC (Ancho Dinámico de Canal) y Volatilidad ATR
El análisis técnico e intradía utiliza formalmente el **Modelo ADC + ATR**:
1. **ADC (Ancho Dinámico de Canal)**: Mide la amplitud técnica del canal operativo (Donchian 50 o distancia entre Bandas de Bollinger: $\text{Superior} - \text{Inferior}$) para determinar si el activo se encuentra en fase de compresión (acumulación / rango estrecho) o fase de expansión.
2. **Proyección de Impulso por ATR**: Para establecer recorridos y zonas objetivo tras el quiebre o rebote de un nivel clave, se utiliza el impulso proyectado de $1.5 \times \text{ATR}_{14}\text{ (H1)}$ (calibrado con la lectura de tendencia del ADX).
3. **Validación contra ATR Restante Diario**: Toda proyección intradía debe validarse contra el ATR restante diario ($\text{ATR}_{14}\text{ D1} - \text{Rango Hoy}$), asegurando que el recorrido estimado quepa holgadamente dentro de la volatilidad esperada de la jornada sin sobreextender el movimiento.

## 6. Nada se envía sin aprobación (Piezas públicas limpias)

Todo contenido se genera, se muestra al director y **espera su aprobación**. Al
aprobar, se guarda con `scripts\ruta_mensaje.ps1` (mensajes) o
`scripts\ruta_story.ps1` (imágenes) — nunca armes la ruta a mano.

**Piezas públicas 100% limpias para clientes**: Los flujos y comandos públicos (`/alerta`, `/apertura`, `/dato_macro`, `/noticia`, `/story`) generan **exclusivamente material para el cliente final** (mensaje de WhatsApp + Story visual de marca). Queda terminantemente excluida la generación automática de guiones o piezas internas para ejecutivos en estos flujos. Las herramientas internas quedan reservadas exclusivamente a los comandos dedicados `/ventas` y `/postventa`.

### El envío a WhatsApp sí se ejecuta, y solo después del "sí"

El envío está automatizado (`scripts/enviar_whatsapp.py`, WhatsApp Web vía
Playwright) y **lo puedes ejecutar tú**, con una condición que no admite atajos:
**solo después de que el director apruebe explícitamente esa pieza**. Generar no
es aprobar, y "se ve bien" no es aprobar. Si no hay un sí, no se envía.

La tanda completa se despacha canal por canal con un solo comando:

```bash
uv run --extra stories python scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda>
```

**Cada canal sale en UNA acción con todas sus piezas.** El editor de medios acepta
varias imágenes y cada una conserva su propio pie (medido contra el DOM real el
2026-09-02). No mandes las piezas de a una: cuatro envíos espaciados 45 s son
cuatro veces más exposición que un lote, y llegan con el precio viejo.

Cada canal además **se rinde justo antes de salir**, no al principio de la tanda.
Si el precio cruzó un soporte o una resistencia que el texto daba por vigentes,
esa pieza **no sale** (se renombra a `.divergente`) y el despacho lo informa.

Si se corta a la mitad, `--desde N` retoma en el canal N sin duplicar lo enviado.

Para una pieza suelta o un canal concreto:

```bash
uv run --extra stories python scripts/enviar_whatsapp.py \
  --grupo metales \
  --lote "data/carrusel/<tanda>/03_commodities_materias_primas"

# o un archivo solo:
uv run --extra stories python scripts/enviar_whatsapp.py \
  --grupo metales \
  --adjunto "<ruta a la imagen>" \
  --mensaje-archivo "<ruta al texto>"
```

- Un **lote tiene que ser del mismo tipo**: el menú Adjuntar entra por "Fotos y
  videos" o por "Documento", no por ambas. Un PDF no viaja con las Stories.
- `--grupo` acepta los alias de `config/whatsapp_grupos.json` (`metales`, `oro`,
  `forex`, `indices`, `acciones`, `cripto`, `senales`, `macro`, o el nombre del
  canal). Un alias que no se reconoce **aborta**: nunca elijas un canal "parecido".
- El comando **verifica que el mensaje aparezca en la conversación** antes de
  reportar éxito, y compara la cabecera del chat contra el destinatario de forma
  exacta. Si aborta, **no se envió**: revisa si llegó antes de reintentar, porque
  repetir a ciegas duplica la pieza en el grupo.
- Comprobar la sesión antes de una tanda: `--status`. Si pide vinculación, el QR
  lo escanea el director con `--login`; eso no lo puedes hacer tú.

**El ritmo no es negociable.** Automatizar WhatsApp Web va contra sus términos de
servicio y el número es el del negocio. El comando impone 45 s mínimos entre
acciones de envío y un cupo de 40 mensajes al día, y **espera** cuando toca. Un
lote es UNA acción pero N mensajes: la cadencia se aplica una vez, el cupo se
descuenta por pieza. No subas esos límites, no metas el envío en un bucle, y no lo
lances en paralelo: el perfil de sesión no admite dos procesos a la vez.

> [!CAUTION]
> **Un solo dueño de la sesión a la vez.** El perfil de Chromium
> (`.whatsapp_session/`) admite un único proceso. Si Claude Code y tú abrís el
> navegador a la vez, uno de los dos termina creando un perfil paralelo, y ese
> patrón desvinculó la sesión dos veces el 2026-09-01 y el 2026-09-02. Antes de
> despachar, confirma con el director que nadie más la está usando.

### La pieza se entrega completa

Varios comandos producen **imagen y texto**, no una sola cosa. `/alerta`
entrega la Story más el mensaje de WhatsApp que la acompaña; `/dato_macro` en
Modo resultado entrega la Story más su pie. Una imagen sin su texto llega muda al
grupo: el pie es lo único que se ve en la notificación de WhatsApp antes de abrir
el chat, y lo único legible si el cliente no descarga la imagen.

Antes de dar un comando por terminado, revisa qué entregables define su archivo
en `.claude/commands/` y confirma que produjiste **todos**, cada uno guardado con
el helper que le corresponde.

**Los nombres de archivo salen de los helpers, no de tu criterio.**
`ruta_story.ps1` devuelve la ruta completa y ya resuelve el nombre; no le agregues
sufijos como `_horizontal` ni `_v2`. Si necesitas guardar los dos formatos de una
misma pieza, pregúntale al director cómo quiere distinguirlos en vez de inventar
una convención nueva.

## 7. Color en las Stories

Si generas una imagen, los colores salen de `templates/stories/marca.css` vía
`var(--rol)`. Nunca escribas un hex.

Dos roles que no se mezclan: `--activo` es la identidad del activo (pinta el
escenario) y `--sube`/`--baja` es la dirección del mercado. Si se colapsaran, una
pieza dorada bajista se leería como alcista dorada.

Verifica con `uv run python scripts/marca_tokens.py --check`.

## 7.1. Norma de Formatos de Stories (Horizontal 16:9 vs Vertical 9:16)

El formato del lienzo es obligatorio según el tipo de contenido y su carga técnica:

1. **Horizontal 16:9 (`1920×1080`) — Exclusivo para Alertas con Gráficos**:
   - Se utiliza **únicamente para `alerta` y piezas que incluyan gráficos técnicos MT5** (series temporales de velas H1), donde la horizontalidad es indispensable para proyectar la acción del precio y las líneas de soporte/resistencia sin aplastar el eje temporal.
2. **Vertical 9:16 (`1080×1920`) — Obligatorio para Carga Textual sin Gráficos**:
   - Se utiliza **obligatoriamente para calendarios, agendas, guías pedagógicas, conceptos didácticos y breaking news** (todas las piezas que lleven carga textual y no incluyan gráfico de mercado).
   - **Criterio de Ultra-Legibilidad Móvil (Brandkit)**: Las piezas verticales 9:16 se diseñan para lectura nativa en celular (WhatsApp) sin necesidad de zoom. Deben usar tipografía a escala grande (titulares en Goldman 700 a 64px, tarjetas a 38px, cuerpo en 28-32px peso 600/700) y márgenes estrechos (~44px) para ocupar el 100% del ancho útil.

---

## Dónde está el resto

- `CLAUDE.md` — las reglas completas del proyecto.
- `.claude/commands/<nombre>.md` — la definición canónica de cada comando.
- `docs/architecture.md` — cómo encaja todo.

## 8. Pipeline de Generación de Gráficos e Imágenes (El Gold Standard)

El pipeline de gráficos e imágenes institucionales (`serie_mt5.py` -> `story_grafico.py` -> `story_render.py` o plantillas HTML de `templates/stories/` + Playwright) es la **única vía autorizada** para generar piezas visuales en este repositorio:

0. **Prohibición Total de Modelos de Difusión / IA Text-to-Image (`generate_image`)**: Queda **terminantemente prohibido** utilizar la herramienta `generate_image` o modelos de generación de imágenes por difusión de IA para crear piezas, terminales, infografías o gráficos en este proyecto. Todo el contenido visual DEBE ser maquetado en HTML/CSS estructurado y renderizado vía Playwright/Chromium siguiendo el Brandkit oficial.
1. **Uso de Clases Exactas en el Payload**: En los comandos de operaciones (como `/recomendacion`), NUNCA inventes clases para los `hitos` o `niveles`. Debes usar EXCLUSIVAMENTE las clases soportadas por el CSS del snapshot (`meta`, `entrada`, `stop`, `actual`). Usar clases como `"origen"` o `"soporte"` hará que el nivel desaparezca por completo, arruinando la imagen.
2. **Uso de H1 Estricto**: Por requerimiento corporativo, las operaciones (incluso las Posicionales de semanas) DEBEN renderizarse con `--timeframe H1 --velas 60`. El motor gráfico (`story_grafico.py`) cuenta con matemáticas de *clamping* (anclaje) que evitarán que el gráfico se aplaste si el Take Profit o Stop Loss están demasiado lejos, garantizando la correcta lectura visual de la volatilidad sin sacrificar el encuadre.
3. **Cuidado con el CSS**: Si en algún momento debes editar o inspeccionar los archivos `.css` de las plantillas (como `marca.css` o `recomendacion.html`), NUNCA dejes comentarios truncos (`*/` sueltos). Playwright usa un motor de render estricto que invisibilizará variables y elementos completos si detecta sintaxis CSS rota.


## 9. Producción diaria en tandas (`/carrusel` y `/informe`)

Estos dos comandos funcionan distinto a los demás y conviene entender **por qué**
antes de correrlos, porque las reglas que siguen no son preferencias de estilo: sin
ellas el sistema deja de servir para lo que existe.

### 9.1. No elijes los activos. El escáner elige.

`scripts/screener_gi.py` recorre el catálogo, puntúa cada activo sobre 100 y
selecciona. **Tu trabajo empieza después de eso.**

La razón es que la selección tiene que ser auditable: si un cliente pregunta por qué
se habló del Oro y no del Nasdaq, la respuesta tiene que ser un número y no una
opinión. En el momento en que el agente ajusta la lista "porque queda mejor", el
sistema completo pierde su sentido y volvemos a elegir a dedo con más pasos.

Si el resultado no te convence, **se discute el criterio del escáner**, no la corrida
del día. Y si selecciona menos de 3 activos, o ninguno, **ese es el resultado**: una
tanda de 2 piezas bien elegidas es mejor que una de 3 con un relleno.

### 9.2. El script calcula, tú escribes.

Los dos pipelines tienen dos pasos, y la separación es deliberada:

- `--preparar` arma los payloads (o el markdown del informe) con **todos los datos
  resueltos** y los campos editoriales vacíos.
- `--rendir` **se detiene** si alguno quedó en blanco.

Lo que tú aportas es el titular, el párrafo y el análisis, que es lo único que un
script no puede producir. Lo que **no** aportas son cifras: precio, soporte,
resistencia e impulso ya vienen en el payload y salieron del motor. Si necesitas un
dato que no está, lo pides al MCP; nunca lo deduces.

El freno de `--rendir` es hermano del fail-fast de imagen: una pieza a medias que
sale sin avisar llega al cliente.

### 9.3. Ningún nombre interno del motor llega a un texto de cliente.

`SHORT_AGRESIVO`, `PULLBACK_EMA50_H1`, `R2_GOLDILOCKS_EXPANSION` y similares **no son
términos técnicos difíciles: son nombres de variable**, escritos para que el motor los
compare entre sí. Nadie los pensó para que un lector los viera.

La traducción vive en **`data/glosario_motor.json`** (regímenes, setups, sesgos,
matices y conceptos). Cuando aparezca un token que no está ahí, **se agrega al JSON**,
no se parafrasea en la pieza: ese glosario lo consumen también otros comandos, y una
traducción improvisada en un solo lugar se contradice con la del siguiente.

Lo mismo vale para la taquigrafía de mesa de dinero. En texto de cliente no se
escribe `Δ` como encabezado, ni `bps`, ni `2s10s`. Se escriben completos: "Cambio en
1 día", "puntos base", "Diferencia entre 10 y 2 años". Y los porcentajes van en
notación chilena con dos decimales siempre (`4,70%` y `4,24%`): en una columna, `4.7`
junto a `4.24` se lee como si uno tuviera menos precisión que el otro.

Hay una guardia que lo verifica, `tests/test_voz_cliente_informe.py`. Si la rompes,
te está diciendo que un token se escapó, no que el test esté mal.

### 9.4. El dato viejo se refresca, no se fuerza.

El informe de apertura **no se emite** si el snapshot del motor está vencido. El
remedio es siempre el mismo y en este orden: `pipeline_ingesta.py` y después
`macro_bias_engine.py`.

`--con-datos-viejos` existe para cuando el director decide publicar igual, y en ese
caso el documento sale con el aviso impreso en la primera página. **No es un atajo
para saltarse el error**: es una decisión que deja constancia.

Dos consecuencias del mismo principio: una cifra que no se puede calcular se informa
como **ausente y nunca como cero** (cero significa "no se movió", que es distinto de
"no sé"), y cada cifra con rezago lleva **su fecha al lado**, en la tabla y no al pie.

### 9.5. El horario sale de Nueva York, no del reloj chileno.

Las tandas se anclan a la sesión estadounidense: 10:30, 14:30 y 16:45 hora de Nueva
York. Chile y Estados Unidos cambian de horario en sentido opuesto, así que el
desfase se mueve dos veces al año. Un cronograma escrito en hora chilena describe en
enero un mercado que ya cerró. El script deriva la tanda solo y comunica en hora de
Chile; no la calcules a mano.

### 9.6. Cuatro filtros que ningún puntaje compensa.

Antes de puntuar, el escáner excluye por feriado de bolsa, por ventana de bloqueo
alrededor de un dato macro, por prohibición del modelo de régimen, y por agotamiento
del recorrido diario. Son **prohibiciones, no penalizaciones**: un setup prohibido
puede puntuar alto, y sin el filtro ganaría la tanda.

Lee siempre los avisos que imprime. Si dice que el calendario no respondió, el gate de
blackout **no se pudo verificar** y la decisión de publicar pasa a ser manual. El
escáner nunca reporta "cero exclusiones" cuando en realidad no pudo mirar.

### 9.7. Estándares Cuantitativos del Modelo ADC + ATR y Motor GI (Auditoría 2026-08-28).

1. **Suavizado de Volatilidad Welles Wilder RMA:** `atr()` y `adx()` en `mt5_client.py` usan estrictamente `alpha = 1.0 / period` (`adjust=False`) para paridad 1:1 con MetaTrader 5 y Bloomberg (evitar `span=period` que otorga 86,7% de sobrepeso reactivo).
2. **Indicadores de Estado sobre Velas Cerradas:** Canales Donchian, ATR, ADX, MACD, Bollinger y niveles S/R se calculan sobre `df.iloc[:-1]` para evitar que Donchian se autoanule y que la barra abierta contamine el cálculo. El spot en vivo se evalúa contra estos niveles congelados (`rango_hoy` en D1 conserva la barra viva).
3. **Piso de Actividad en Consumo Diario:** `factor_espacio` en `screener_gi.py` exige que la sesión tenga al menos 15% de consumo realizado para otorgar los 20 puntos, eliminando falsos positivos por simple reloj en la apertura.
4. **Multiplicador de Impulso Discreto por Régimen:** $k$ no se modula por función continua de ADX (en compresión el ADX es bajo por diseño). Se calibra por régimen $R_0-R_4$ y clase de activo.
5. **Documentación Oficial:** Consultar `docs/auditoria_modelo_adc_atr.md`, `docs/dictamen_auditoria_adc_atr.md` y `docs/funcionamiento_motor_gi.md`.

### 9.8. Composición Obligatoria de Informes PDF Institucionales.

Todo informe PDF de análisis de mercado debe seguir la arquitectura canónica de **`pipeline_informe.py`** y **`generar_pdf.py`**:
1. **Gráficos Panorámicos a 300 DPI (`grafico_informe.py`):** Cada activo del informe debe incluir su gráfico de 7.2 × 2.82 pulgadas con las 60 velas D1/H1 de MT5, medias móviles (50 y 100) y líneas de niveles técnicos. Queda prohibido compilar PDFs con tablas planas sin gráficos de terminal.
2. **Estructura Pedagógica de 3 Capas por Activo:** Cada sección debe desglosar qué pasa, qué significa para el lector y qué NO operar hoy (setups prohibidos).
3. **Tabla de Curva Soberana Estructurada:** Con variaciones en puntos base a 1D y 5D en notación chilena (`_tabla_curva`).
4. **Dimensionamiento de Riesgo y Lote:** Cálculo explícito de lotaje por Volatility Targeting según el ATR del día.
