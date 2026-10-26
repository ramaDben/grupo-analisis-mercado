# `/seguimiento` con tres mensajes de contexto (noticia 1, noticia 2, análisis técnico)

> Estado: borrador para aprobación del director, 2026-10-25. Lo marcado **[mi decisión]** es una
> suposición del diseñador, no algo que el director haya dicho.

## Intención

Hoy `/seguimiento <activo> [cliente]` entrega al ejecutivo una lámina PNG y **un** texto de WhatsApp
sobre el estado de la simulación del lunes (con, a veces, un párrafo del dato macro del calendario).
El ejecutivo necesita más de un motivo para escribirle a su cliente: la noticia fresca del activo y la
lectura técnica de hoy. Por eso `/seguimiento` suma un **HTML** con tres mensajes de WhatsApp
**independientes**, listos para copiar, de modo que el ejecutivo elija con cuál abre la conversación:

1. **Noticia 1**: la nota más fresca del activo.
2. **Noticia 2**: la segunda nota, de otra fuente o con otro ángulo.
3. **Análisis técnico**: la lectura de hoy de la estrategia.

No hay un cuarto mensaje que "junte todo". Cada mensaje se sostiene solo y lleva contexto al día.

## Qué se entrega

- Lo de hoy no cambia: lámina `lamina.png` y el texto de seguimiento de `seguimiento.redactar`.
- Se agrega `mensajes.html` (un archivo, sin dependencias externas, abre en el celular) con las tres
  tarjetas y un botón **Copiar** por tarjeta. Llega por Telegram junto a la lámina y se copia a Drive
  con el mismo `_a_drive` que usa la lámina.
- Una tarjeta sin material (no hay segunda noticia fresca, por ejemplo) **no se rellena**: aparece
  como «Hoy no hay una segunda noticia directa de <activo>» con el motivo. Nunca se inventa una nota.

## Fuentes de noticias

- **FXStreet** (RSS en español, ya leído por `noticia.candidatas_fxstreet`, filtrado por titular con
  `config/noticias_fxstreet.json`).
- **Investing.com** (RSS en español, responde 200 el 2026-10-25 pero con feeds generales y chicos).
  **[mi decisión]** se filtra por titular con los mismos patrones del activo.
- «etc.» del director: otras fuentes se agregan al mismo mecanismo (lista de feeds + dominios
  permitidos de `fu.cargar_lista`). El diseño no cierra la lista a dos; la primera entrega usa estas dos.
- Ventana de frescura: 3 días (`noticia.VENTANA_DIAS`), con la fecha siempre a la vista en el mensaje.
- Dos noticias distintas: no se repite la misma URL, y **[mi decisión]** se prefiere que la segunda
  sea de otro medio que la primera si hay opción.

## Cómo se redacta

**Siempre con agy** (director, 2026-10-25: «más lento con agy siempre»). Python junta las candidatas y
las valida; agy elige y redacta en español chileno; Python depura lo que agy devolvió.

- Python sella en la pieza `datos.noticias_candidatas` (de todas las fuentes) y los hechos técnicos de
  hoy (la `Lectura` de la estrategia: dirección, estado, nivel que se vigila, qué lo invalida, objetivo).
- agy escribe los tres textos en `editorial` (titular traducido, bajada simple, mensaje). Nada de lo
  que el ejecutivo escribió en Telegram llega al prompt (mismo contrato de `agy.escribir_textos`).
- Python depura con las reglas ya existentes: `noticia._motivo` por cada noticia (cifras solo si
  Python leyó la nota y las encontró; con muro de pago, sin cifras; URL del dominio de la fuente;
  fecha en ventana) y `esquema.errores_texto_*` (sin guion largo, sin voseo, siglas explicadas).
- Una noticia que no pasa se descarta con su motivo y su tarjeta queda vacía; no se reintenta
  ni tira abajo el análisis técnico.
- **Análisis técnico**: las cifras, niveles y dirección **salen de `get_lectura`/`Lectura`, nunca de
  agy** (Regla 1). agy solo pone las palabras alrededor; el despacho reemplaza los precios por los
  del terminal justo antes de armar el HTML, como hace la oportunidad.

## Reglas de contenido

- Español chileno, tuteo, sin guion largo ni medio, sin «hawkish/dovish» sin traducir.
- Cada mensaje abre con el saludo del ejecutivo (`[[SALUDO]]` / `seguimiento.con_saludo`) y cierra con
  una pregunta concreta al cliente, no con «consulta a tu analista».
- Cada noticia nombra su medio y su fecha; el titular va traducido; el enlace es el de la nota.
- El mensaje técnico dice hacia dónde va el activo (alcista, bajista o lateral) y el escenario que lo
  invalida, y cierra con la temporalidad en rango cuantificado.
- Sin avisos legales dentro del mensaje (los lleva la lámina), igual que el seguimiento de hoy.

## Costo y cupo

- Hoy el seguimiento es instantáneo, no usa agy y se reusa 30 minutos. **Esto cambia:** los tres
  mensajes con agy tardan entre 5 y 25 minutos (medido en `agy.py`).
- **[mi decisión]** La lámina y el texto de hoy salen **de inmediato** como siempre; el HTML llega
  **después**, en un segundo mensaje de Telegram, cuando agy termina. Así el ejecutivo no queda
  esperando para lo que ya tenía.
- **[mi decisión]** El HTML se reusa 30 minutos igual que la lámina (misma clave), y gasta **una**
  pieza del cupo diario, no tres.
- Si agy falla o vence, el ejecutivo recibe un aviso corto y el seguimiento de siempre queda intacto.

## Aprobación del director (2026-10-25)

El director aprobó este diseño y **extendió a `/seguimiento` la excepción de la Regla 1 sobre cifras de
una nota** (antes solo valía para el titular y la bajada de la noticia de apertura de `/oportunidad`):
una cifra solo vale si Python leyó la nota y la encontró en su texto; con muro de pago, sin cifras. Hay
que dejar esta extensión escrita en `CLAUDE.md` junto a la excepción original.

## Resuelto tras la revisión del constructor

- **Precios en el mensaje técnico [mi decisión]:** agy no escribe ningún dígito de precio. Deja marcas
  (`[[NIVEL_VIGILA]]`, `[[NIVEL_INVALIDA]]`, `[[OBJETIVO]]`) y Python las reemplaza con los valores de la
  `Lectura`, formateados a los `digits` del activo. El test de contrato falla si la salida de agy trae un
  número de precio escrito.
- **Tarjeta técnica sin datos [mi decisión]:** sale vacía con su motivo (terminal caído, lectura rota, sin
  líneas trazables). Solo depende de la `Lectura` de hoy: no exige referencia semanal ni aplica el blackout
  del escáner, porque el mensaje no publica nada, lo copia un ejecutivo.
- **Activos sin filtro de noticias [mi decisión]:** se buscan por el nombre del catálogo, como hoy en
  `_patrones`. Si no hay nota, tarjeta vacía con motivo; no se agregan patrones a los 38 tickers en esta entrega.
- **Segundo envío [mi decisión]:** el bot ya trabaja con una cola y un hilo (`Telegram.trabajador`), así que
  el HTML se encola como trabajo aparte. Un segundo `/seguimiento` del mismo activo mientras agy trabaja no
  lanza otro agy: responde que el HTML viene en camino.
- **Fallos [mi decisión]:** un fallo o vencimiento de agy no gasta cupo ni se reusa los 30 minutos; el
  ejecutivo puede volver a pedirlo.

## Metas, no metas, antimetas

- **Metas:** tres mensajes independientes y listos; noticias de más de una fuente; contexto técnico
  al día; el seguimiento de hoy sin cambios.
- **No metas:** no se envía nada a WhatsApp ni a clientes desde el bot (el ejecutivo copia y pega);
  no hay mensaje "todo en uno"; no se toca el escáner ni el carrusel; no se agrega una plantilla de
  Story.
- **Antimetas (fracasos aunque funcione):** una noticia inventada o vieja presentada como de hoy; una
  cifra que no está en la nota; un precio escrito por agy; un seguimiento de hoy que ahora demora
  minutos o que falla porque agy falló.

## Dónde se hace

- Módulo nuevo `scripts/analista/mensajes_contexto.py` (candidatas multi‑fuente, orden, vacíos) y
  `scripts/analista/mensajes_html.py` (el HTML). Se reusan `noticia.py`, `fuentes.py`, `esquema.py` y `agy.py`.
- Extensión de `preparar_seguimiento` (sellar candidatas y hechos técnicos) y de `Bot._seguimiento`
  (segundo envío). `/analista` (la skill de agy) aprende la pieza de seguimiento con contexto.
- Pruebas: una por regla de depuración, una por tarjeta vacía, una de contrato que impida que agy
  escriba precios, y una del HTML (tres tarjetas, botón de copiar, sin recursos externos).

## Lo que queda al constructor

El diseño visual del HTML (debe leerse en el celular y seguir el brand kit de `templates/`), los
nombres de campos de `editorial`, y el detalle del segundo envío de Telegram.
