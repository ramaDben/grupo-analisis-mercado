# Bot de Telegram para analistas y ejecutivos

El equipo le pide al bot el análisis de un activo del terminal y su seguimiento. Diseño:
`docs/superpowers/specs/2026-10-16-oportunidad-por-activo-design.md` (reemplaza a la foto semanal
de seis activos del spec `2026-10-12-oportunidad-semanal-design.md`).

## Qué se puede pedir

| Comando | Pieza |
|---|---|
| `/oportunidad <activo>` | El análisis de un activo: técnico (estrategia activa), fundamental (drivers, agenda, curva) y las voces de bancos y prensa, con el panel de simulación del ejecutivo |
| `/seguimiento <activo>` | Cómo va el análisis vigente de ese activo: la simulación y la lectura de hoy |

El análisis sale en HTML (herramienta interna con panel); `/seguimiento` entrega lámina PNG y el
texto de WhatsApp en el mensaje. Los comandos `/activo`, `/calendario`, `/dato` y `/jornada` se
retiraron el 2026-10-12 y responden con la ayuda. `foco.py`, `plan.py`, `bitacora.py` y `pdf.py` se
borraron; `data/bitacora_planes_analistas.json` queda como historia versionada.

**El informe no se personaliza.** Nadie en GI está inscrito como asesor de inversión, y un
informe con el nombre del cliente se acerca a una recomendación personalizada. Si un pedido trae
`para Nombre`, el bot lo explica y no lo atiende (no gasta agy ni cupo).

`/estado` muestra el cupo del día, `/id` el número de usuario y `/ayuda` la lista.

## Cómo funciona

```
/oportunidad <activo>:
   pedido -> orden.py -> registro_semanal (¿hay uno vigente?)
      si lo hay -> vigencia.verificar (¿la lectura se rompió?) -> si sigue vigente, se reusa (sin agy)
      si no     -> preparar.py (lectura, hechos del día, agenda de 7 días + calendario PNG, curva, gráficos)
                -> agy /analista (redacta pieza.json citando los hechos y busca los bancos)
                -> fuentes.depurar + esquema.py (validan) -> sin banco: segundo intento solo de fuentes
                -> lámina PNG -> oportunidad_html.py
                -> Telegram + carpeta de Drive -> registro_semanal
/seguimiento <activo>:
   pedido -> orden.py -> preparar.py (simulación y lectura de hoy, contra el análisis vigente)
      -> lámina PNG + texto de WhatsApp en el mensaje (sin agy)
```

### Qué lleva el análisis

- **Técnico:** la lectura de la estrategia activa (dirección, líneas, invalidación, objetivo).
- **Lo que pasa hoy** (`hechos.py`): el estado real de los drivers medibles del activo (Dollar Index
  de MT5 `USDIDX`, tasa real, bono a 10 años y tasa de la Fed de la curva, cobre y petróleo de MT5), con
  su fecha, su cambio en 5 sesiones, su efecto sobre el activo y si acompaña nuestra lectura. Qué se mide
  y con qué signo lo dice `config/drivers.json`.
- **Días clave** (`agenda.py`): los datos de alto impacto de los 7 días de vigencia (las pestañas
  `thisWeek` y `nextWeek` de Investing.com), con la lámina del calendario. Sin datos, la ficha dice la
  ventana completa con sus fechas; con el calendario caído, se avisa al ejecutivo y el correo omite el
  bloque.
- **Voces:** hasta 1 banco a favor y 1 en contra (los más recientes) con entidad, medio, fecha y enlace. Si solo hay uno, se despliega limpio al 100% de ancho sin tarjeta vacía ni avisos. **Sin al menos un banco vigente el análisis no sale.**
- **Panel de simulación** para que el ejecutivo trabaje con su cliente.

El correo que copia el ejecutivo lleva todo eso: lo que pasa hoy, los días clave con la imagen del
calendario y lo que dicen los bancos con el enlace a cada nota (como máximo 1 a favor y 1 en contra).

### Símbolos

Vale cualquier símbolo del terminal MT5 (`simbolos.py`). Los activos del catálogo
(`config/activos.json`) aportan nombre y `digits`; uno fuera del catálogo se acepta con el
`description` que trae MT5, sin traducirlo, y con un marco genérico. Si el terminal no responde,
el bot lo dice en lugar de afirmar que el símbolo no existe.

### Vigencia y reúso

- Un análisis vale **7 días corridos** (`registro_semanal.VIGENCIA`), queda **a nombre de quien lo
  generó** y cualquiera que pida ese activo lo recibe **sin gastar agy ni cupo**.
- **Caducidad anticipada** (`vigencia.py`): al reusarlo, Python vuelve a seguir su referencia contra
  el mercado de hoy. Caduca antes de los 7 días si la estructura de la lectura cambió, si el precio
  tocó la invalidación o si alcanzó el objetivo técnico. Entonces se rehace.
- El análisis caducado **queda en `data/semanal/registro.json`** con su motivo y fecha
  (`caducada`). El registro se versiona; las entradas del formato antiguo (una por semana) se
  conservan como historia de solo lectura.
- Si ya hay un análisis vigente y falla la verificación de vigencia (terminal caído), no se rehace:
  se entrega el vigente con el aviso «No pude verificar si sigue vigente». Sin análisis vigente y
  con el terminal caído, el pedido falla (ver «Cuando algo falla»).

### Fuentes de prestigio

- `config/fuentes_prestigio.json` es una **lista cerrada que edita el director**: entidades
  (bancos de inversión, Chile, organismos), medios con sus dominios y `frescura_dias` (14).
- agy busca en la web y entrega las fuentes; Python las valida (`fuentes.py`) y descarta las que
  fallan: entidad en la lista, postura alcista, bajista o neutral, medio en la lista, URL `https`
  del dominio de ese medio y con ruta de artículo (no portada), fecha dentro de 14 días, URL que
  responde a un GET (una respuesta 401, 403 o 429 queda «sin verificar», no descartada) y sin
  URL repetida. Se entrega solo lo que pasa, y cada descarte llega al analista con su motivo.
- **Cifras de terceros:** la regla 1 sigue (toda cifra del texto sale de los datos del terminal),
  con una excepción: la cifra que aparece en la tesis de una fuente validada y se atribuye a esa
  entidad en la misma frase («Goldman Sachs ve el oro en 4.800»).
- **Un banco o nada (spec 2026-10-17 §5; correo editorial 2026-10-19):** `cuentan_como_banco` de la lista dice qué grupos cumplen
  (hoy los bancos de inversión y los de Chile; los organismos suman pero no cumplen). Se exige al menos un banco calificado para
  validar y emitir la pieza (`--validar` falla sin banco). En el correo institucional se exhibe como máximo 1 banco a favor y 1
  en contra (los más recientes según su fecha); si solo hay uno calificado, se despliega limpio al 100% de ancho sin tarjeta
  vacía ni avisos de que falta el otro. Si agy no encuentra banco, el bot hace **un segundo intento solo de fuentes** (reabre
  `fuentes`, deja `fuentes_intento_1.json` con lo válido y lo descartado) y, si tampoco, responde que no encontró ninguna voz de
  banco, sin gastar cupo ni registrar el análisis.
- Cada llamada a agy deja `agy_salida_<n>.json` (código, segundos y respuesta) en la carpeta del pedido.

### Invitación comercial

Por regulación (director, 2026-10-16) la pieza de `/oportunidad` (ficha y texto reenviable) **no invita a operar**: invita a **revisar la
plataforma MT5 con el cliente**. El bloque «Para revisar con tu cliente en MT5» se quitó (director, 2026-10-18: no llegaba al cliente); el mensaje
breve para el cliente propone mirar el gráfico y los escenarios en MT5, y el panel de simulación
lleva el rótulo «Ejemplo ilustrativo para revisar en MT5». `esquema.py` rechaza un texto que
invite a operar.

**Decidido por el director (2026-10-17): se mantiene tal como está.** La lámina de `/seguimiento`
lleva `comercial.INVITACION_ACTIVA` («¿Te interesa operar este escenario?…»), y esa invitación
queda fuera de la regla de `/oportunidad`.

### Seguimiento

`/seguimiento <activo>` mide contra el **análisis vigente de ese activo** y lo anota en su
entrada del registro. Sin análisis vigente responde «pide primero /oportunidad <activo>». No usa
agy y se reusa 30 minutos (`reuso_minutos`).

### Candado por activo y timeout

- Mientras se genera el análisis de un activo, otro pedido del mismo activo no entra a la cola: el
  bot responde que ya se está generando y que lo pida de nuevo en unos minutos (`generando` en
  `bot.py`). Así dos personas no gastan agy dos veces por lo mismo.
- agy tiene **25 minutos** para redactar (`agy.TIMEOUT`) y **15** para el segundo intento de fuentes
  (`agy.TIMEOUT_REINTENTO`). Un encargo con búsqueda web de 3 a 5 fuentes se midió en 424 s y 652 s el
  2026-10-16; los hechos del día no suman búsquedas porque los mide Python.

### Reglas que se mantienen

- **agy solo redacta.** No recibe nada de lo que el analista escribió: recibe la ruta de la
  pieza. Datos, imágenes y láminas van sellados con una huella, y si cambian la pieza se descarta.
- **Toda cifra del texto tiene que estar en los datos del terminal** (Regla 1), salvo la
  excepción de terceros atribuidos. El texto tampoco puede traer HTML, guion largo, voseo,
  «oportunidad» ni `%`.
- **Candados de lenguaje.** `esquema.frases_prohibidas` rechaza frases de instrucción, de
  recomendación y de dimensionamiento ("es momento de comprar", "te recomiendo", "lotes").
- **No toca la producción.** Trabaja en `data/informes_analistas/` y no usa los `preparar()` de
  los pipelines, que escriben en `data/carrusel/`, `data/screener/` y los historiales. Un test
  impide que el bot importe el envío a WhatsApp o la bitácora de despachos.

## Firma y acreditación

El informe lo firma el director: nombre, cargo, foto, firma escaneada si existe, la acreditación
tal como figura en el certificado (sin enlace: el de la CMV no reconocía el certificado) y la frase *"Análisis general de
mercado, idéntico para todos sus destinatarios. No es asesoría de inversión ni considera el perfil
de quien lo lee."* El informe **no menciona a la CMF** (decisión del director).

- Todo sale del bloque `autor` de `config/analistas_telegram.json`. Sin ese bloque el bot no
  arranca: un informe sin firma no es el producto.
- La foto y la firma van en `config/autor/`, fuera de git porque son datos personales. Si el config
  las declara y no están, el informe sale sin ellas y el bot lo avisa.
- **La vigencia se decide con la fecha del pedido**, no la de creación: desde el día siguiente a
  `vigente_hasta`, la acreditación deja de imprimirse (también en una pieza reusada) y el bot avisa
  en cada respuesta que hay que renovarla.
- Nada de fotos generadas o retocadas con IA: la foto acompaña una credencial.

## Puesta en marcha

1. Crear el bot con @BotFather y poner `TELEGRAM_BOT_TOKEN=...` en `.env`.
2. `uv run python scripts/bot_analistas.py --probar-token`
3. Copiar `config/analistas_telegram.example.json` a `config/analistas_telegram.json`
   (gitignoreado) y agregar a cada persona por su número de usuario. Quien no está, recibe su
   número al escribirle al bot y se lo pasa al director. Completar también el bloque `autor` y
   poner la foto en `config/autor/foto.png`.
4. `ruta_drive`: la carpeta de Google Drive para escritorio donde se entrega (por ejemplo
   `G:\Mi unidad`). El bot crea `GI Informes/<fecha>/` adentro. Una carpeta **compartida** se
   alcanza por `<unidad>:\.shortcut-targets-by-id\<id de la carpeta>\<nombre>`, y la cuenta de
   esa unidad necesita permiso de Editor. `url_carpeta_drive` es opcional y va en la respuesta.
5. Probar sin Telegram, con MT5 abierto:
   `uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/seguimiento oro"`
6. Dejarlo corriendo: `scripts\instalar_bot_telegram.ps1 -Instalar` (sin `-Instalar` solo muestra
   qué haría). La tarea corre bajo `conhost --headless`: sin ventana, y lo que el bot lanza
   (agy, git, el render) hereda esa consola oculta.
   **Para reiniciarlo** (tras traer master o tocar `config/analistas_telegram.json`):
   `scripts\instalar_bot_telegram.ps1 -Reiniciar`. **Nunca `Stop-ScheduledTask` solo**: cierra
   `conhost` y deja vivos `uv` y `python`. El 2026-10-09 eso dejó dos bots repartiéndose los
   pedidos, y el huérfano, sin consola, no podía lanzar Chromium: la mitad de los pedidos fallaba
   al dibujar el gráfico. Ahora además el bot toma un candado (`data/.bot_analistas.lock`) y un
   segundo no arranca mientras el primero escucha; el sistema lo suelta al morir el proceso.
7. Mantener `data central` fresco: `scripts\instalar_ingesta.ps1 -Instalar`. Sin esa tarea, la
   ingesta solo corre al abrir Claude Code, y un día sin sesión deja la curva de tasas vencida:
   las piezas salen con el aviso «contexto sin curva de tasas». Late cada hora y solo baja datos
   si la última ingesta tiene más de 6 h.

## La alerta de la semana (spec 2026-10-18)

El bot le avisa al ejecutivo de qué trata la semana, sin que lo pida. Es **material interno**: no pasa
por la aprobación de WhatsApp ni por `reloj_gi.py`, y un test impide que `avisos_semana.py` toque el
envío.

| Aviso | Cuándo (Santiago) | Qué trae |
|---|---|---|
| **Mapa** | lunes 07:45 a 08:15 | El tema («Semana de inflación», «Semana tranquila»…), hasta 5 datos fuertes con día y hora CLT/CLST, una línea para conversar y el aviso de riesgo. Teclado «Útil» / «No me sirve» |
| **Víspera** | 16:00 a 16:30 del día hábil anterior a un dato de tier 1 | 5 líneas: cuándo sale, qué suele hacer, qué conversar, qué no decir y el aviso. Botón que pide el `/oportunidad` del activo más afectado |

- **Todo sale de lo que ya existe, sin IA.** Eventos del calendario (`agenda.ventana_cruda`, hora ya en
  Santiago), efecto del glosario (`si_sale_sobre_consenso`, solo de EE.UU. o de Chile con entrada
  chilena) y la guía de `config/guia_eventos.json`, que edita el director. Antes de abrirla a todos los
  ejecutivos conviene que la revise cumplimiento.
- **El tema** lo decide el dato de menor tier; en empate, tasas > inflación > empleo > actividad >
  petróleo. Las series que se repiten cada semana (subsidios por desempleo, inventarios de crudo) solo
  mandan si no hay otra cosa.
- **Modo prueba:** `avisos_semana.modo` en `config/analistas_telegram.json`. `prueba` (por defecto) manda
  solo al rol `director`; `todos` abre a los registrados. La primera semana va en prueba.
- **Tope de 2 por ejecutivo por día**; ganan los de menor tier. Un envío que falló sigue pendiente. Un
  calendario caído no manda nada: avisa una vez al director y reintenta en el siguiente latido.
- **Medición** (decide a las 3 semanas si se suman la reacción y el cierre del viernes): el estado
  `data/semanal/avisos_semana.json` (gitignoreado) guarda por aviso los clics del botón, el voto y si el
  ejecutivo pidió después `/oportunidad` del mismo activo dentro de 24 h (el pedido del propio botón no
  cuenta ahí). Se lee a mano, sin identificar a nadie:

```powershell
uv run python -c "from datetime import date; from analista import avisos_semana as a; print(a.resumen_interaccion(date(2026,10,19), date(2026,11,6), a.Estado()))"
```

(con `PYTHONPATH=scripts`).

## Cuando algo falla

El analista recibe el motivo, y nunca una pieza a medias ni un gráfico de otro día.

| Mensaje | Qué pasó |
|---|---|
| `no uso el terminal: ...` | MT5 cerrado o en otra cuenta que la de `config/cuenta_mt5.json` |
| `La redacción no terminó (timeout ...)` | agy no respondió en 25 minutos. No gasta cupo |
| `El texto no pasó los controles` | agy escribió una cifra ajena, HTML o guion largo. No se entrega |
| `'PlaywrightContextManager' object has no attribute '_playwright'` (en la bitácora) | Un bot huérfano sin consola: hay dos corriendo. `-Reiniciar` |
| `Drive no está configurado` | Falta `ruta_drive`; el archivo igual llega por Telegram |
| `No encontré ninguna voz de banco…` | Dos búsquedas seguidas no trajeron un banco con nota de los últimos 14 días. No se gastó cupo; se puede volver a pedir. La carpeta del pedido guarda `fuentes_intento_1.json` y las salidas de agy para ver qué se descartó |

La bitácora está en `data/logs/bot_telegram.log` y el estado (offset, cupo y piezas vigentes) en
`data/.bot_telegram_estado.json`.
