# El correo de `/oportunidad` abre con una noticia y una imagen

Fecha: 2026-10-24. Estado: diseño, pendiente de aprobación del director.

## Intención y por qué

El correo que el ejecutivo manda al cliente desde la pieza `/oportunidad` del bot de analistas
(`scripts/analista/oportunidad_html.py`, función del correo, líneas ~960-980) abre hoy con la
apertura oscura del análisis técnico: kicker, titular nuestro, firma y snapshot de 4 cifras. Es
correcto pero frío: el cliente ve un análisis antes de ver por qué le debería importar hoy.

El director quiere que el correo **dé más sensaciones**: que abra con algo que está pasando en el
mercado, en una frase que sostenga una premisa, acompañada **siempre** de una imagen, y que el
análisis técnico llegue después como el respaldo profesional de esa premisa. La referencia de tono
son los posts de cuentas de squawk (LiveSquawk): un hecho simple y concreto ("Los precios del oro se
recuperan del mínimo de dos meses mientras se estanca el repunte del dólar") del que se arma un
titular.

X se descartó como fuente (director, 2026-10-24: "era solo una primera lluvia de ideas"): leerlo
exige API de pago o automatizar contra sus términos, y la web no lo indexa. La misma noticia suele
estar en Reuters, que es de donde la reenvía el squawk.

## Metas, no metas y antimetas

**Metas.**
1. El correo abre con la **noticia de apertura**: titular-premisa, bajada, imagen ilustrativa y
   fuente con fecha y enlace.
2. Le sigue el **dato de tasas** del banco central que mueve al activo, con su imagen.
3. Los bloques actuales quedan **entre la entrada y el análisis** (director).
4. El análisis técnico lo firma **"Benjamín Bravo Soza · Departamento de Estudios GI"**.
5. Cierra la **simulación del ejecutivo**, como hoy.

**No metas.**
- No cambia la lectura técnica ni la dirección (salen de la estrategia activa).
- No cambia el HTML interno del ejecutivo (panel, WhatsApp, lámina) salvo lo que el correo arrastre.
- No se toca X, el carrusel, los canales de WhatsApp ni las Stories.

**Antimetas (fracaso aunque funcione).**
- Una noticia vieja presentada como de hoy.
- Una cifra en la noticia que la fuente no dice.
- Una imagen con logo, marca, bandera o texto que se lea como foto real del hecho o como uso de marca.
- Rellenar con una noticia genérica para que la sección salga.

## Decisiones del director (2026-10-24)

1. **Orden del correo:** noticia de apertura → dato de tasas → bloques actuales (contexto, hechos,
   gráfico del dólar, días clave, noticia directa, voces, escenarios) → análisis técnico firmado →
   simulación del ejecutivo.
2. **La imagen va siempre** con la frase, y la crea agy. Son imágenes **ilustrativas** (oro, banco
   central, billete). Es una **excepción a la Regla 0** de `CLAUDE.md`, acotada a este correo.
3. **Las noticias pueden traer precios.** Es una **excepción a la Regla 1**, acotada a la noticia de
   apertura.
4. **No se copia la imagen de la fuente** (las de Reuters son fotos de agencia con derechos).
5. **Firma:** "Departamento de Estudios GI" en lugar de "Departamento de Análisis Técnico", **en todas
   las piezas** (hecho el 2026-10-24: `config/analistas_telegram.json`, que está gitignoreado, más
   los respaldos duros de `oportunidad_html.py`, los tests y los fixtures).
6. **Cifras con muro de pago:** opción 1a, ver §1.
7. **Reutilización:** la noticia vencida sale con su fecha vieja a la vista (opción 2b), ver §1.

## Diseño

### 1. La noticia de apertura

- **La busca agy**, en el mismo encargo `/analista` que ya busca `fuentes`: un campo editorial nuevo
  `editorial.noticia` con `medio`, `fecha` (AAAA-MM-DD), `url`, `titular_original` (en el idioma de
  la fuente), `extracto` (el párrafo de la nota que sostiene el titular, en su idioma), `titular`
  (premisa en español, hasta 90 caracteres) y `bajada` (español, hasta 200).
- **Medios válidos:** los de prensa de `config/fuentes_prestigio.json` más las fuentes oficiales del
  ancla del activo. Se prefiere la nota más reciente que hable **del activo o de su driver principal**,
  y, como ya ordena `analista.md` para las fuentes, **primero en español** (Bloomberg Línea, Diario
  Financiero, La Tercera…); Reuters, Bloomberg, FT, WSJ, CNBC o MarketWatch solo si no hay una en
  español. *Llamada mía.*
- **Python la valida** con la maquinaria de `fuentes.py` (dominio del medio, ruta de artículo, URL
  que responde o `sin_verificar` por muro de pago). La fecha va siempre a la vista.
- **Ventana de 72 h al preparar.** La noticia tiene que tener a lo sumo 72 h cuando agy la trae.
- **En la reutilización (días 4 a 7) la noticia sigue saliendo con su fecha a la vista** (director,
  2026-10-24, opción 2b). No se vuelve a buscar: reutilizar no cuesta agy. Para que no se lea como de
  hoy, pasadas las 72 h la línea de fuente lo dice en palabras ("Noticia del lunes 19 de octubre")
  además de la fecha. *La redacción exacta, llamada del constructor.*
- **Titular y bajada se sostienen solos**: el cliente no tiene que abrir el enlace (Reuters y
  Bloomberg tienen muro). El enlace va abajo como respaldo: "Fuente: Reuters · 23 de octubre →".
- **Excepción de cifras (Regla 1):** el titular y la bajada pueden traer precios y cifras, con dos
  frenos de Python que la pieza no salta:
  1. **Las cifras solo valen si Python leyó la nota** (director, 2026-10-24, opción 1a). Si la URL
     responde `ok`, Python descarga la página y busca cada cifra del `titular` y la `bajada` en su
     texto real (normalizando separadores de miles y decimales). Si la URL queda `sin_verificar`
     (muro de pago, lo normal en Reuters y Bloomberg), **titular y bajada van sin cifras**. El
     `extracto` de agy no cuenta como respaldo: lo escribe el mismo agy que escribe el titular, y
     **no hay revisión del director antes del envío** (`_oportunidad` entrega el HTML directo al
     ejecutivo). Una cifra que no cuadra **descarta la noticia y la pieza sigue**, al estilo de
     `descartar_tesis_rotas`, con el motivo en el aviso al ejecutivo. *Llamada mía:* coherente con
     "sin noticia válida la sección no sale", y no tira 7 a 25 minutos de agy. Para que la noticia
     no caiga entera, `analista.md` le dice a agy que con muro de pago escriba titular y bajada sin
     cifras.
  2. La cifra va **atribuida y fechada** en la bajada o en la línea de fuente. El precio actual del
     correo (snapshot) sigue saliendo de MT5.
- Pasa por los mismos controles de texto que el resto (sin guion largo, sin "operar"/"comprar"/
  "oportunidad", siglas en línea, tuteo chileno). El `%` **sí** se permite aquí, solo si está en la
  fuente.
- **Si la noticia de apertura es la misma URL que la noticia directa** de "Lo último de …", la tarjeta
  de abajo no se repite.
- **Sin noticia válida** la sección no sale: el correo abre con el dato de tasas y el bot lo avisa al
  ejecutivo en el mensaje de entrega. No se reintenta agy por esto (ya hay un reintento para fuentes
  y cada uno cuesta minutos).

### 2. La imagen ilustrativa

- **Catálogo cerrado de motivos** en `config/motivos_imagen.json`: cada motivo trae un id, para qué
  temas/activos sirve y su prompt base. Arranque propuesto: `oro_lingotes`, `banco_central`
  (edificio genérico con columnas), `billetes_dolar`, `peso_chileno`, `cobre`, `petroleo`,
  `bolsa_pantallas`, `tecnologia` (para US100 y acciones tech), `acciones_generico`.
- **Prompt con prohibiciones fijas**, que Python agrega a cada motivo: sin logos, sin marcas, sin
  texto ni números legibles, sin banderas, sin sellos de país, sin personas reconocibles; estilo
  fotográfico sobrio, luz cálida, formato horizontal.
- **agy elige el motivo** (campo `editorial.noticia.motivo`, de la lista) y **genera la imagen** a
  partir del prompt que arma Python, no de uno propio.
- **Banco de imágenes por motivo** en `data/imagenes_ilustrativas/<motivo>/`. La imagen se elige
  **una vez por pieza, al preparar**, y todas las entregas de esa pieza llevan la misma: la
  reutilización no puede gastar agy. Se toma una del motivo que no haya salido en otra pieza en los
  últimos 7 días; agy genera una nueva solo si no queda ninguna. *Llamada mía: sin cooldown por
  ejecutivo.* Baja el costo y deja los correos parejos. El banco se
  versiona como historia editorial (mismo criterio que `historial_suplementos.json`) si pesa poco;
  si no, gitignoreado con un índice versionado. *Llamada del constructor según el peso real.*
- Se publica con `imagenes_publicas.publicar` (URL pública por hash, como las demás).
- Rótulo pequeño bajo la imagen: **"Imagen ilustrativa"**.
- **Cómo genera agy.** El primer paso del plan es **medir** que `agy` en modo headless puede generar
  una imagen y dejarla en una ruta dada. Si no puede, el respaldo es llamar directo a la API de
  imágenes de Gemini con el mismo prompt desde Python. En ambos casos el prompt lo arma Python.

### 3. El dato de tasas

- Python, sin agy. El banco sale del activo:
  - Fed: XAUUSD, US100, US500, US30, acciones y ETF de EE.UU., WTI, BRENT, cripto, USDJPY.
  - BCCh: USDCLP, COPPER.
  - BCE: EURUSD y GER40.
  - Un activo sin banco mapeado no lleva la sección. *Mapeo inicial: llamada mía; el constructor lo
    deja en config.*
- Datos, sin fuentes nuevas: Fed desde `treasury_fed_data.json` (`DFF`), BCCh desde
  `bcch_macro_data.json` (`TPM`), BCE desde `bce_boe_data.json` (`BCE_DFR`). Se muestra **con su
  nombre real y la fecha del dato**: "Tasa efectiva de fondos federales: 3,88 por ciento al 23/10",
  nunca "la tasa de la Fed", porque `DFF` no es el rango objetivo. **No se muestra la fecha de la
  última decisión**: no está en los datos y deducirla de la serie (DFF cambia un día después del
  anuncio, BCE_DFR tiene huecos) llevaría una fecha errada al cliente. La próxima reunión sale solo
  si está en la agenda de 7 días (`datos.agenda`). *Llamada mía.*
- Una línea pedagógica fija por banco, sin agy: qué hace esa tasa con el activo ("Una tasa alta en
  EE.UU. hace más atractivo el dólar frente al oro").
- Imagen: el motivo `banco_central` del mismo banco de imágenes.
- Sin dato fresco según `config/frescura_datos.json`, la sección no sale y se avisa.

### 4. Firma

- `config/analistas_telegram.json`: el cargo de Benjamín pasa a "Departamento de Estudios".
  `oportunidad_html.py` ya agrega "GI" en la firma de la apertura. El respaldo duro de la línea 787 y
  el pie de la línea 940 pasan a "Departamento de Estudios". Los otros analistas conservan su cargo.
  **Ojo:** el cargo vive en el config, así que el cambio alcanza **todas** las piezas de Benjamín
  (seguimiento, láminas, PDF), no solo el correo. *Llamada mía, vetable por el director.*
- La firma "Benjamín Bravo Soza · Departamento de Estudios GI" va **al pie del bloque del análisis
  técnico** (director: "nuestro análisis técnico con mi nombre abajo").

### 5. Qué va en cada bloque

1. **Apertura (noticia).** Fondo oscuro de marca con el logo de GI; imagen arriba, kicker "MERCADO
   HOY · ORO (XAU/USD)", titular-premisa, bajada y línea de fuente. *Llamada mía.* Sin noticia, la
   apertura muestra el dato de tasas.
2. **Dato de tasas**, con su imagen.
3. **Bloques intermedios (los actuales):** contexto, hechos, gráfico del dólar, días clave, noticia
   directa y voces.
4. **Análisis técnico:** rótulo del análisis, snapshot de 4 cifras de MT5, el gráfico de la lectura
   (hoy va pegado a la apertura y baja acá), los tres escenarios, la temporalidad y, al pie, la firma.
5. **Simulación del ejecutivo** y el cierre consultivo con el botón de WhatsApp, como hoy.

**Asunto, preheader y titular editable** (`asunto_sugerido`, `preheader_sugerido`,
`data-ed="titular"`) siguen a la noticia cuando la hay y vuelven al titular técnico cuando se
descarta. Las cifras del asunto pasan por el mismo freno de §1. *Llamada mía.*

### 6. Reglas del proyecto

- `CLAUDE.md` gana dos excepciones explícitas, acotadas al correo de `/oportunidad`: la Regla 0
  admite imágenes ilustrativas generadas del catálogo; la Regla 1 admite cifras de la noticia de
  apertura con los dos frenos de §1. Se regenera `.agents/rules/proyecto.md` con
  `scripts/agy_reglas.py`. `docs/gobernanza_guias_educativas_captacion.md` también prohíbe
  text-to-image: se anota la excepción.
- `.claude/commands/analista.md` documenta `editorial.noticia` y su motivo; se regeneran los
  workflows de AGY si corresponde.
- `docs/bot-analistas.md` documenta la sección.

## Lo que queda al constructor

- La maqueta exacta de cada bloque, dentro de las restricciones de Outlook ya documentadas en
  `oportunidad_html.py` (hex, tablas, sin `var()`).
- El esquema exacto en `esquema.py` y los mensajes de rechazo.
- La normalización de cifras para el freno 1.
- Los tests: noticia vencida, cifra ausente del extracto, URL repetida con la directa, activo sin
  banco, motivo fuera de catálogo, banco de imágenes vacío y con imágenes en cooldown.
