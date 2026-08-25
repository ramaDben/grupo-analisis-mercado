# Reglas del proyecto — Grupo de Análisis de Mercado

Antigravity no lee `CLAUDE.md`, así que este archivo trae las reglas que
**cualquier** pieza tiene que cumplir. No las reemplaza: `CLAUDE.md` sigue siendo
la fuente completa y, ante cualquier duda o contradicción, manda `CLAUDE.md`.

Léelo antes de ejecutar cualquier workflow de `.agents/workflows/`.

---

## 1. Los datos no se inventan

Precios, niveles, indicadores, calendario económico y operaciones abiertas salen
**siempre** del MCP `market-data`. Nunca de tu memoria, nunca de una búsqueda web,
nunca deducidos de otro número, **y NUNCA delegados a un subagente que pueda alucinar el resultado**. 
Para asegurar fidelidad, extrae el precio y los niveles ejecutando tú mismo los scripts del MCP (ej. llamando a `mt5_client.get_rates` vía Python) en lugar de depender de resúmenes de subagentes.

Si el MCP falla, **detente y dilo**. Una pieza con un precio inventado es peor que
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

## 2. La hora sale del reloj, no de la web

Nunca uses búsqueda web para saber la fecha o la hora. Para la hora de Chile:

```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$now.ToString('yyyy-MM-dd HH:mm')
```

Para convertir la hora de un dato económico extranjero, usa
`scripts\hora_chile.ps1` — nunca offsets fijos, que producen desfases de una hora
cuando cambia el horario de verano.

## 3. Los decimales de cada precio están definidos

Todo precio respeta el campo `digits` de `config/activos.json` para ese activo.
Nunca truncar ceros al final ni redondear a entero.

| Activo | Digits | Correcto |
|---|---|---|
| USDCLP | 2 | $889.60 |
| USDJPY | 3 | 163.731 |
| XAUUSD | 2 | $4,539.72 |
| WTI.spot | 3 | $90.181 |
| US100.spot | 2 | 30,350.01 |
| Acciones | 2 | $192.50 |

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
voseo argentino.

**Nunca el guion largo como inciso.** En texto de cliente (mensajes, pies de
Story, textos dentro de las piezas) no se usa `—` ni `–` para abrir un inciso:
"el stop en 1.758,09 — para eso está" se escribe "el stop en 1.758,09. Para eso
está". Punto seguido, coma o dos puntos según el caso. Es una marca reconocible
de texto generado por IA y el material se firma con el nombre de un analista
real: si se lee como escrito por una máquina, la firma pierde credibilidad. El
punto medio `·` sí se mantiene, porque es separador del kit de marca
(`ORO · XAU/USD`) y no puntuación de frase.

## 5. Terminología de niveles e Indicadores

Siempre "soporte" y "resistencia". Nunca "techo" ni "suelo".

### Modelo ADC (Ancho Dinámico de Canal) y Volatilidad ATR
El análisis técnico e intradía utiliza formalmente el **Modelo ADC + ATR**:
1. **ADC (Ancho Dinámico de Canal)**: Mide la amplitud técnica del canal operativo (Donchian 50 o distancia entre Bandas de Bollinger: $\text{Superior} - \text{Inferior}$) para determinar si el activo se encuentra en fase de compresión (acumulación / rango estrecho) o fase de expansión.
2. **Proyección de Impulso por ATR**: Para establecer recorridos y zonas objetivo tras el quiebre o rebote de un nivel clave, se utiliza el impulso proyectado de $1.5 \times \text{ATR}_{14}\text{ (H1)}$ (calibrado con la lectura de tendencia del ADX).
3. **Validación contra ATR Restante Diario**: Toda proyección intradía debe validarse contra el ATR restante diario ($\text{ATR}_{14}\text{ D1} - \text{Rango Hoy}$), asegurando que el recorrido estimado quepa holgadamente dentro de la volatilidad esperada de la jornada sin sobreextender el movimiento.

## 6. Nada se envía sin aprobación (Piezas públicas limpias)

Todo contenido se genera, se muestra al director y **espera su aprobación**. Al
aprobar, se guarda con `scripts\ruta_mensaje.ps1` (mensajes) o
`scripts\ruta_story.ps1` (imágenes) — nunca armes la ruta a mano.

**Piezas públicas 100% limpias para clientes**: Los flujos y comandos públicos (`/alerta`, `/apertura`, `/dato_macro`, `/noticia`, `/señal`, `/oportunidad`, `/story`) generan **exclusivamente material para el cliente final** (mensaje de WhatsApp + Story visual de marca). Queda terminantemente excluida la generación automática de guiones o piezas internas para ejecutivos en estos flujos. Las herramientas internas quedan reservadas exclusivamente a los comandos dedicados `/ventas` y `/postventa`.

El envío a WhatsApp lo hace el director copiando el texto. Tú no envías nada.

### La pieza se entrega completa

Varios comandos producen **imagen y texto**, no una sola cosa. `/oportunidad`
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

---

## Dónde está el resto

- `CLAUDE.md` — las reglas completas del proyecto.
- `.claude/commands/<nombre>.md` — la definición canónica de cada comando.
- `docs/architecture.md` — cómo encaja todo.

## 8. Pipeline de Generación de Gráficos (El Gold Standard)

El pipeline de gráficos (`serie_mt5.py` -> `story_grafico.py` -> `story_render.py`) es extremadamente delicado. Para garantizar su funcionamiento, debes seguir estrictamente estas reglas empíricas de renderización:

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
