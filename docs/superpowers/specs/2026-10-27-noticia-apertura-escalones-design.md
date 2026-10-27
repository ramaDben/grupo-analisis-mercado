# La noticia de apertura baja por escalones hasta encontrar de qué hablar

Fecha: 2026-10-27. Estado: aprobado por el director el 2026-10-27; implementado en `feat/noticia-apertura-escalones`.

## Por qué

El correo de `/oportunidad` de Goldman Sachs del 2026-10-27 salió **sin noticia de apertura**:
"no encontré una nota del activo de los últimos 3 días". La única búsqueda es el RSS de FXStreet en
español (`preparar._noticias` → `noticia.candidatas_fxstreet`), que es de divisas y materias primas:
para una acción de EE.UU. casi nunca trae nada. Ese mismo día, la Fed decidía tasas al día siguiente
(28/10), un evento que mueve directamente a un banco. Como dijo el director: "siempre hay algo de qué
hablar en los mercados financieros".

Medido el 2026-10-27 a las 11:40: ni FXStreet ni los cuatro feeds de Investing.com en español
tenían un titular que nombrara a Goldman Sachs. **Sumar fuentes del activo no basta**; hace falta
un respaldo que no dependa de que la prensa nombre a la acción.

## Decisión del director (2026-10-27)

"Noticia más amplia": buscar también en Investing.com y, si no hay nada, abrir con lo que mueve al
sector o con el evento de la semana que lo mueve (ej. la Fed del 28/10 para los bancos).

Esto **revisa una antimeta** de la spec del 2026-10-24 ("rellenar con una noticia genérica para que
la sección salga"). Las nuevas aperturas no son genéricas. Cada escalón está atado al activo por una
relación declarada, y el correo dice **qué es** lo que abre: una nota del activo, una del sector o
la agenda.

## Los escalones (el primero que encuentra algo, gana)

| # | Qué abre | Fuente | Cifras permitidas | Rótulo en el correo |
|---|---|---|---|---|
| 1 | Nota que nombra al activo | FXStreet + Investing.com (`noticias_contexto.candidatas`, ya usado en `/seguimiento`) | Las que Python leyó en la nota (Regla 1, excepción del 24-10) | Fuente y fecha, como hoy |
| 2 | Nota del sector o del driver | Mismos feeds, con los patrones del **sector** del activo (`config/noticias_sector.json`, junto a `noticias_fxstreet.json`: lo edita el director y cubre también acciones fuera del catálogo; p. ej. bancos de EE.UU.: "bancos" sin "bancos centrales", "Wall Street", "banca", "JPMorgan", "Morgan Stanley") | Las que Python leyó en la nota | "Lo que mueve al sector" + fuente y fecha |
| 3 | El evento central de la semana | El calendario que la pieza ya trae (`dias_clave`), solo un evento fuerte y futuro del país del activo: una decisión de tasas antes que un dato de inflación, empleo o crecimiento (`apertura.evento_central`) | **Solo** previo y esperado del calendario. agy no escribe ninguna cifra | "En la agenda" + día y hora en Chile |

Solo si los tres escalones vienen vacíos el correo abre con el análisis, como hoy. El aviso al
ejecutivo nombra el escalón que se usó ("abrí con una nota del sector: …"), para que sepa qué recibe
el cliente.

## Reglas que no cambian

- **Regla 1**: en los escalones 1 y 2 una cifra solo vale si Python leyó la nota y la encontró en su
  texto; con muro de pago va sin cifras. En el escalón 3 las únicas cifras son las del calendario.
- **Regla 0**: la imagen ilustrativa sale del catálogo cerrado (`config/motivos_imagen.json`). El
  escalón 3 usa el motivo de banco central.
- **Anti-anacronismo**: el escalón 3 se redacta en modo anticipación ("el mercado aguarda…").
- La relación del escalón 2 se valida en el **titular**, igual que la noticia oficial: buscar en el
  cuerpo vuelve el filtro decorativo.

## Fuera de alcance

- Las columnas "sin efecto atribuido / sin efecto declarado" del correo y los drivers de las
  acciones (en inglés y no medibles en `config/activos.json`). Van en un diseño aparte.

## Pruebas

- Con feeds falsos: nota del activo → escalón 1; solo nota del sector → escalón 2; sin notas y con
  Fed en `dias_clave` → escalón 3; todo vacío → abre con el análisis y avisa.
- Un titular de sector con una cifra que el cuerpo de la nota no trae: la cifra se rechaza.
- El escalón 3 nunca lleva una cifra que no esté en el evento del calendario.

## Implementación (2026-10-27)

- `scripts/analista/apertura.py`: candidatas por escalón (cada una con su `escalon`), `evento_central` y `escalon_de`.
- El escalón de la noticia elegida lo deduce Python de la candidata, no lo declara agy; la de agenda se marca
  `escalon: "agenda"` y `noticia.depurar_noticia` la valida aparte (sin cifras, solo con evento sellado y sin notas).
- El reúso de un análisis que abre con la agenda caduca cuando el evento ya ocurrió (`bot._agenda_pasada`).
