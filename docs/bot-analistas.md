# Bot de Telegram para analistas y ejecutivos

El equipo le pide al bot el análisis técnico de la semana y el seguimiento de un activo. Diseño:
`docs/superpowers/specs/2026-10-12-oportunidad-semanal-design.md`.

## Qué se puede pedir

| Comando | Pieza |
|---|---|
| `/oportunidad` | El análisis técnico de la semana, con los 6 activos y el panel de simulación del ejecutivo |
| `/seguimiento oro` | Cómo va un activo de la foto de la semana: la simulación y la lectura de hoy |

La pieza semanal sale en HTML (herramienta interna con panel); `/seguimiento` entrega lámina PNG y
el texto de WhatsApp en el mensaje. Los comandos `/activo`, `/calendario`, `/dato` y `/jornada`
se retiraron el 2026-10-12 (spec `docs/superpowers/specs/2026-10-12-oportunidad-semanal-design.md`)
y responden con la ayuda. `foco.py`, `plan.py`, `bitacora.py` y `pdf.py` se borraron;
`data/bitacora_planes_analistas.json` queda como historia versionada.

**El informe no se personaliza.** Nadie en GI está inscrito como asesor de inversión, y un
informe con el nombre del cliente se acerca a una recomendación personalizada. Si un pedido trae
`para Nombre`, el bot lo explica y no lo atiende (no gasta agy ni cupo).

`/estado` muestra el cupo del día, `/id` el número de usuario y `/ayuda` la lista.

## Cómo funciona

```
/oportunidad:  pedido → orden.py → preparar.py (foto semanal de los 6 activos, gráficos)
               → agy /analista (solo redacta pieza.json, una vez por semana) → esquema.py (valida)
               → láminas PNG → oportunidad_html.py (HTML con panel) → Telegram + carpeta de Drive
/seguimiento:  pedido → orden.py → preparar.py (simulación y lectura de hoy) → lámina PNG
               + texto de WhatsApp en el mensaje (sin agy)
```

- **La pieza semanal es un HTML** (herramienta interna con panel): el ejecutivo marca los activos,
  escribe la pérdida aceptable y copia el correo. Lleva seis activos y una lámina PNG por activo.
- **La foto de la semana se arma una sola vez** (`registro.json`, clave = semana ISO). Quien
  pide `/oportunidad` después recibe la misma foto, con su nombre en el archivo, sin gastar agy
  ni cupo. Una foto de la semana anterior no se reusa.
- **Un elegido sin análisis guardado queda fuera de la foto, y el analista lo sabe.** El aviso se
  repite cada vez que alguien reusa la foto. Cuando aparece su referencia, el siguiente
  `/oportunidad` **rehace** la foto para sumarlo, y los activos que ya estaban se copian tal cual:
  sus clientes ya recibieron esos precios y `/seguimiento` mide contra ellos (director,
  2026-10-12).
- **`/seguimiento` no usa agy** y se reusa 30 minutos (`reuso_minutos`). Solo acepta activos de la
  foto de la semana; sin foto o con el activo fuera de ella, lo dice.
- **agy solo redacta.** No recibe nada de lo que el analista escribió: recibe la ruta de la
  pieza. Datos, imágenes y láminas van sellados con una huella, y si cambian la pieza se descarta.
- **Toda cifra del texto tiene que estar en los datos del terminal** (Regla 1). El texto tampoco
  puede traer HTML, guion largo, voseo, «oportunidad» ni `%`.
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

## Cuando algo falla

El analista recibe el motivo, y nunca una pieza a medias ni un gráfico de otro día.

| Mensaje | Qué pasó |
|---|---|
| `no uso el terminal: ...` | MT5 cerrado o en otra cuenta que la de `config/cuenta_mt5.json` |
| `La redacción no terminó (timeout ...)` | agy no respondió en 12 minutos. No gasta cupo |
| `El texto no pasó los controles` | agy escribió una cifra ajena, HTML o guion largo. No se entrega |
| `'PlaywrightContextManager' object has no attribute '_playwright'` (en la bitácora) | Un bot huérfano sin consola: hay dos corriendo. `-Reiniciar` |
| `Drive no está configurado` | Falta `ruta_drive`; el archivo igual llega por Telegram |

La bitácora está en `data/logs/bot_telegram.log` y el estado (offset, cupo y piezas vigentes) en
`data/.bot_telegram_estado.json`.
