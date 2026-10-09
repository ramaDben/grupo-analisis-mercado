# Bot de Telegram para analistas y ejecutivos

El equipo le pide al bot las mismas piezas que el director le pide a Claude Code, y recibe un
**informe PDF** general, firmado por el director, que comparte tal cual con su trader. Diseño:
`docs/superpowers/specs/2026-10-08-bot-telegram-analistas-design.md` y
`docs/superpowers/specs/2026-10-08-informe-general-firmado-y-plan-design.md`.

## Qué se puede pedir

| Comando | Pieza |
|---|---|
| `/activo oro` | Niveles, dirección, drivers, escenarios y el gráfico TradingView del carrusel |
| `/calendario hoy` · `/calendario semana` | Agenda de alto impacto en hora de Chile, con la lámina de Avisos |
| `/dato` · `/dato ipc` | El último dato con cifra (o el pedido): veredicto y movimiento del dólar y el oro. Si todavía no sale, en modo anticipación |
| `/jornada apertura` · `/jornada cierre` | Los cinco activos base con sus gráficos diarios y la curva de tasas |
| `/oportunidad` | El **foco técnico del día** para ventas: el activo que el escáner elige, sin estadística. Ver abajo |
| `/semanal oro` · `/semanal usdclp` · `/semanal indices` · `/semanal etf` · `/semanal acciones` | La **pieza semanal comercial**: imagen, texto de WhatsApp y correo para Outlook. Ver abajo |
| `/seguimiento oro` (o la misma temática) | Cómo va ese escenario hoy: vigente, avanzando, completado o invalidado |

**El informe no se personaliza.** Nadie en GI está inscrito como asesor de inversión, y un
informe con el nombre del cliente se acerca a una recomendación personalizada. Si un pedido trae
`para Nombre`, el bot lo explica y no lo atiende (no gasta agy ni cupo).

`/estado` muestra el cupo del día, `/id` el número de usuario y `/ayuda` la lista.

## Cómo funciona

```
pedido → orden.py (gramática cerrada) → preparar.py (datos + gráficos, carpeta propia)
       → agy /analista (solo redacta pieza.json) → esquema.py (valida) → láminas
       → informe_html.py (maqueta fija) → pdf.py (Chromium, hoja de celular) → Telegram + carpeta de Drive
```

- **Circula el PDF, no el HTML** (director, 2026-10-09). Google Drive no muestra HTML, en el
  celular cuesta abrirlo, y un documento firmado no debe circular en un formato que se edita con
  el Bloc de notas sin tocar la firma. El HTML se sigue armando, porque es la fuente del PDF, y
  queda en la carpeta del pedido en `data/informes_analistas/`: de ahí sale la huella de la
  bitácora y ahí se audita. Si Chromium falla, el HTML va **solo por Telegram** con el aviso, y
  Drive no recibe un archivo que no puede mostrar.
- **El PDF se lee en el teléfono** (director, 2026-10-09). La hoja mide 108 x 192 mm, la
  proporción de una pantalla: el visor la encaja a lo ancho y el cuerpo de 13 pt se lee sin zoom.
  Una sola columna, las tablas como tarjetas y ningún bloque cortado entre páginas. No se fuerza
  un salto por sección: se probó y dejaba hojas con dos líneas. El gráfico va a todo el ancho, en
  alta resolución, y **se amplía con los dedos** («Pellizca para ampliar»). **Sin enlaces
  internos**: hasta el 2026-10-09 tocar el gráfico saltaba a una lámina apaisada al final, y los
  visores de teléfono (Drive, Telegram) no siguen esos enlaces: tocarlo daba error y la lámina
  quedaba como una hoja horizontal suelta. Se distribuye solo por la carpeta de Drive: el director
  descartó publicar páginas web, links o envíos automáticos.

- **agy solo redacta.** No recibe nada de lo que el analista escribió: recibe la ruta de la
  pieza. Datos, imágenes y láminas van sellados con una huella, y si cambian la pieza se descarta.
- **Toda cifra del texto tiene que estar en los datos del terminal** (Regla 1). El texto tampoco
  puede traer HTML, guion largo ni voseo.
- **La maqueta es nuestra**: cabecera y lema del evergreen GI, cuerpo con la legibilidad de la
  guía USD/CLP, colores de `marca.css` (sección "Documento claro").
- **Reusar no cuesta agy.** La pieza se reusa mientras está vigente (`reuso_minutos`; un dato ya
  publicado vale todo el día).
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

## Plan de escenarios (solo `/activo`)

Es lo que el informe trae y WhatsApp no. Lo escribe Python (`scripts/analista/plan.py`), queda
sellado en `datos.plan` y agy no lo redacta ni lo repite.

| Fila | Qué dice | De dónde sale |
|---|---|---|
| Gatillo | Cierre de vela de 1 hora sobre R1 (o bajo S1), a favor del sesgo | `analizar_activo` H1 |
| Invalidación | Chandelier de 22 velas y 3 ATR, que se arrastra a favor | serie H1 |
| Recorrido | 1,5 veces la volatilidad típica de una hora, **como distancia** | ATR 14 H1 |
| Qué dice la historia | Cuántas veces se dio la condición y qué porcentaje recorrió antes de invalidarse, contra una hora cualquiera **con la misma tendencia** | `estadistica.py` sobre 10.000 velas H1 |
| Estado | Armado, activado o invalidado según el último cierre | serie H1 |

Tres decisiones que no conviene revertir:

1. **Sin objetivo de precio.** En septiembre se midió que ningún objetivo fijo tenía expectativa
   positiva; la salida del director es el Chandelier.
2. **La línea base es de la misma tendencia, no de todas las horas.** Contra todas las horas, el
   oro mostraba 53 % contra 33 %: veinte puntos de ventaja que eran solo el filtro de tendencia.
   Contra las horas sobre la EMA 50 la base es 49 %, y el informe dice que no hay ventaja (menos de
   5 puntos). Con menos de 30 casos no publica porcentaje.
3. **Los niveles históricos salen de la misma función que los de hoy** (`_get_support_resistance`
   con las 300 velas anteriores, sin mirar el futuro). Medir la estadística con otra definición de
   resistencia mediría otra cosa.

Si R1 o S1 son de respaldo ATR (no salen de swings), no hay plan y el informe lo dice. La
estadística tarda unos 13 s por pedido de activo; no se cachea.

**Candados de lenguaje.** `esquema.frases_prohibidas` rechaza frases de instrucción, de
recomendación y de dimensionamiento ("es momento de comprar", "te recomiendo", "lotes", "de tu
capital"). Son frases y no palabras sueltas: "gerentes de compra (PMI)" tiene que pasar.

## Foco técnico del día (`/oportunidad`)

Lo piden los ejecutivos de ventas para un prospecto. Spec:
`docs/superpowers/specs/2026-10-09-foco-tecnico-del-dia-design.md`; pauta para el equipo:
`docs/pauta-ventas-foco-tecnico.md`.

- **Lo elige una regla** (`scripts/analista/foco.py`), entre el forex y commodities del carrusel
  más el US100 (solo desde las 10:00 de Nueva York) y el Brent. Entra un plan armado a 1 ATR o
  menos del gatillo, o activado en las 2 últimas velas con menos de la mitad del recorrido hecho.
  Se ordena por técnico + momentum: **no** por el `Score_GI` entero, porque su factor de espacio
  mide contra el R1 como objetivo (y aquí es el gatillo) y su catalizador no mira la dirección.
- **Sin estadística**, ni en los datos que recibe agy: sin su línea base, "53 %" insinúa una
  ventaja que no hay. En su lugar va una frase fija sin cifras. Los candados del foco rechazan
  frases de captación, de acierto y cualquier `%`; la palabra "oportunidad" no se imprime, ni
  siquiera en el nombre del archivo (`foco-tecnico_*`).
- **"No hay foco" es una respuesta**, con los motivos agrupados. Distinta de "no puedo leer el
  mercado" (MT5 o el calendario caídos): ninguna de las dos gasta agy ni cupo.
- **Se reusa 60 minutos, pero se vuelve a leer el activo antes**: si cambió el plan, la
  tendencia, o hay blackout o mercado cerrado, se rehace.
- La bitácora lo anota con `"tipo": "oportunidad"`.

## Pieza semanal comercial (`/semanal`) y su seguimiento (`/seguimiento`)

Lo pidió el área comercial: cinco plantillas que se renuevan cada lunes (oro, USD/CLP, índices,
ETF y acciones), cada una con **imagen** (1920×1080, se entrega como foto para reenviarla a
WhatsApp), **texto de WhatsApp** (mensaje aparte, para copiarlo entero) y **correo para
Outlook** (HTML con panel de edición, formato de la referencia MasQueUF).

- **Visión diaria.** El escenario se arma con velas D1 (`semanal.escenario`): gatillo (resistencia
  o soporte medidos, o la ruptura de los últimos 5 días), invalidación por Chandelier 22/3 y
  recorrido de 1,5 ATR diario. Sin objetivo de precio: el recorrido es una distancia.
- **Lo que mueve al activo es de esta semana.** agy recibe la agenda de lunes a viernes con sus
  resultados, la curva con su cambio a 5 días y la variación semanal, y no puede afirmar otra cosa.
- **Dos autores visibles.** El análisis es del director; la simulación (monto y volumen) la hace
  el ejecutivo en el panel del correo y sale rotulada «Simulación realizada por …», con la pérdida
  a la invalidación del mismo tamaño y al lado de lo que vale el recorrido. El panel recalcula en
  JavaScript con la misma fórmula que `semanal.simular` (un test corre las dos).
- **Índices, ETF y acciones** eligen su activo cada semana con `semanal.elegir`: puntos técnicos
  más momentum en diario, y a igualdad el más cerca de su gatillo. El correo dice entre cuántos se
  eligió.
- **Reúso semanal**: `data/semanal/registro.json` (versionado) guarda la foto del lunes de cada
  pieza; pedirla otra vez en la semana no redacta ni gasta cupo. El correo sí se rearma para cada
  ejecutivo, porque lleva su nombre.
- **Seguimiento**: compara la foto del lunes con las velas diarias cerradas desde entonces y el
  precio de ahora. Activa y anula un **cierre** diario; el recorrido se cuenta apenas se toca; en
  empate gana la invalidación. Si se invalidó, la pieza queda retirada en el registro y la próxima
  `/semanal` arma la versión 2. Los cuatro estados se cuentan con el mismo peso y nunca «si
  hubieras entrado».
- **Prohibido en el texto**: «oportunidad», «recomendada», «aprovecha», «si hubieras»,
  «ganarías», «garantizado» (`esquema.FRASES_PROHIBIDAS_COMERCIAL`).
- **Drive**: `GI Semanal/<lunes>/<activo o temática>/` con la imagen, el texto y el correo; los
  seguimientos en la misma carpeta como `seguimiento_<fecha>_<hora>.png/.txt`.

El lote del lunes arma las cinco de una vez (no envía nada a ningún canal):

```bash
uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --semanal-lote
```

Pendiente: conectarlo al latido `GI-Reloj` del lunes, la plantilla de correo definitiva de
marketing y la validación de cumplimiento de GI.

## Bitácora de planes

`data/bitacora_planes_analistas.json` se versiona: es historia de lo que el equipo recibió. Una
entrada por informe de activo con plan (una pieza reusada no se re-anota), con los niveles, la
estadística publicada, quién lo pidió y la huella del HTML.

```bash
uv run --with MetaTrader5 python scripts/bot_analistas.py --desenlaces
```

completa el desenlace de los planes de más de 24 h (`activado_recorrido`,
`activado_invalidacion`, `activado_sin_definicion`, `no_se_activo`), medido desde la vela
posterior a la que se usó al preparar.

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
   `uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/activo oro"`
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

## Cuando algo falla

El analista recibe el motivo, y nunca una pieza a medias ni un gráfico de otro día.

| Mensaje | Qué pasó |
|---|---|
| `no uso el terminal: ...` | MT5 cerrado o en otra cuenta que la de `config/cuenta_mt5.json` |
| `La redacción no terminó (timeout ...)` | agy no respondió en 12 minutos. No gasta cupo |
| `El texto no pasó los controles` | agy escribió una cifra ajena, HTML o guion largo. No se entrega |
| `No pude generar el PDF ...` | Chromium no imprimió el informe. Llega el HTML (ábrelo en el navegador) y no se copia a Drive |
| `'PlaywrightContextManager' object has no attribute '_playwright'` (en la bitácora) | Un bot huérfano sin consola: hay dos corriendo. `-Reiniciar` |
| `Drive no está configurado` | Falta `ruta_drive`; el archivo igual llega por Telegram |

La bitácora está en `data/logs/bot_telegram.log` y el estado (offset, cupo y piezas vigentes) en
`data/.bot_telegram_estado.json`.
