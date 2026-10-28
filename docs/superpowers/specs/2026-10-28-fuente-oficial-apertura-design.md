# La noticia de apertura parte de la fuente oficial del activo

Fecha: 2026-10-28. Estado: descripción aprobada en chat por el director el 2026-10-28; falta revisión del documento.

## Por qué

El 2026-10-28 el seguimiento de Goldman Sachs salió con las dos noticias vacías ("Hoy no encontré noticias
del Goldman Sachs en FXStreet ni en Investing.com") y el análisis técnico con "El mercado está cerrado".
Dos causas, y la segunda es la de fondo:

1. **`/seguimiento` no usa los escalones del PR #302.** `scripts/analista/contexto.py:preparar` llama directo
   a `noticias_contexto.candidatas` (solo el escalón 1). Los escalones viven en `apertura.py`, que solo usa
   el correo de `/oportunidad` (`preparar._noticias`).
2. **FXStreet e Investing solo traen una acción cuando un medio la nombra.** Medido el 2026-10-27 y el 28-10:
   ni uno ni otro tenían un titular de Goldman Sachs. La empresa, en cambio, publica sus propios comunicados.

Propuesta del director: para cada activo con sitio oficial (empresa, banco central) leer la noticia
directamente de su sitio de prensa. Y, con ventana más holgada, **que el correo siempre lleve el sitio
oficial del activo**.

## Lo medido (2026-10-28)

- `goldmansachs.com/media-relations/press-releases` responde 200 a un GET simple, sin navegador. **No tiene
  RSS** (tres rutas probadas, 404). El HTML trae los datos embebidos (`__NEXT_DATA__`) con `publishDate` y
  la ruta de cada comunicado. El más nuevo era del 22-10 y el anterior del 13-10 (resultados del Q3).
  Conclusión: las empresas publican cada una o dos semanas, así que **con 72 h de frescura el sitio de
  Goldman habría dado lo mismo que hoy: nada**.
- EDGAR (SEC) ofrece un feed Atom de avisos 8-K por empresa, uniforme para todas las acciones de EE.UU.
  `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000886982&type=8-K&owner=include&count=5&output=atom`
  responde con un User-Agent que lleve un correo de contacto (EDGAR lo exige). Últimos de Goldman: 13-10
  (ítem 2.02, resultados), 11-08 (5.03), 27-07 (3.03), 21-07 (9.01), 20-07 (8.01). El título del `<entry>`
  no trae el asunto; el ítem va en el `<summary>`.
- Los bancos centrales ya tienen lector medido: `scripts/noticia_oficial.py` (EIA, BCE, Fed).

## Decisión del director

- La fuente oficial del activo pasa a ser el **escalón 0**, antes de FXStreet/Investing, del sector y de la
  agenda.
- La ventana de frescura del escalón 0 es de **45 días** (no 72 h), con el rótulo y la fecha a la vista.
- **El piso es el enlace**: si no hay nada dentro de la ventana, el correo igual lleva el enlace a la
  página de prensa oficial del activo, sin titular y sin cifras.
- Se extiende a `/seguimiento` (hoy se queda en el escalón 1).

## Metas

- Que el correo de `/oportunidad` y el seguimiento nunca salgan sin una referencia oficial del activo, o la
  nota más reciente o, como mínimo, el enlace a su sitio de prensa.
- Que el cliente sepa **qué lee y de cuándo**: una nota de hace seis días nunca se presenta como novedad.
- Que una fuente oficial caída, lenta o sin datos no rompa nada: se cae al escalón siguiente.

## Antimetas

- Presentar un comunicado viejo como "noticia de hoy". El rótulo del escalón 0 dice "Lo último que publicó
  <empresa>" con la fecha, nunca "noticia".
- Un lector por sitio de empresa que se rompe cuando la empresa rediseña su web. Para acciones de EE.UU.
  se usa EDGAR (uniforme); el raspado de un sitio de empresa queda fuera de esta etapa.
- Inventar una URL. El enlace piso sale de `config/fuentes_oficiales.json`, que edita el director, y un
  test falla si una entrada no trae su URL.
- Tocar el despacho, el envío o los demás canales. Los canales de WhatsApp siguen con `noticia_oficial.py`
  y su ventana de 72 h.

## Diseño

### 1. Configuración: `config/fuentes_oficiales.json`

Una entrada por ticker del catálogo:

```json
{
  "GS": {
    "organismo": "Goldman Sachs",
    "pagina_prensa": "https://www.goldmansachs.com/media-relations/press-releases",
    "lector": "edgar_8k",
    "cik": "0000886982"
  },
  "WTI": {"organismo": "EIA", "pagina_prensa": "https://www.eia.gov/todayinenergy/", "lector": "feed_oficial", "fuente": "eia"}
}
```

`lector` es `edgar_8k` o `feed_oficial` (reutiliza `FUENTES` de `noticia_oficial.py`, sin duplicar URLs de
feeds). Un ticker sin entrada no tiene escalón 0 y sigue como hoy. El ticker de Goldman en el catálogo se
confirma al implementar (no se asume `GS`).

### 2. Lector EDGAR 8-K (acciones de EE.UU.)

- GET al feed Atom con `User-Agent` que incluya el correo de contacto (variable de entorno, no escrito en el
  repo). Reutiliza `descargar_con_cache` de `noticia_oficial.py`.
- Cada `<entry>` se convierte en candidata: fecha de `<updated>`, URL del documento, y un **titular que
  arma Python** desde un diccionario de ítems en español dentro de la config (2.02 "Resultados del
  trimestre", 5.02 "Cambios en la directiva", 1.01 "Acuerdo relevante", 2.01 "Compra o venta de activos",
  7.01 y 8.01 "Aviso de la empresa"). agy no escribe el titular de un 8-K ni ninguna cifra.
- Los avisos de solo ítem 9.01 (anexos) y los de forma societaria (3.03, 5.03) no cuentan como "lo último
  que publicó": se omiten. Es decisión mía; el director la ajusta en la config.
- El 8-K es la fuente de **hechos**; el ítem 2.02 no trae cifras en el titular. Las cifras solo valen si
  Python leyó el documento y las encontró en su texto (Regla 1, excepción del 2026-10-24); sin eso, sin
  cifras.

### 3. El escalón 0 en `apertura.candidatas`

Antes del escalón 1: si el ticker tiene fuente oficial y alguna candidata cae dentro de 45 días, esa es la
candidata (`escalon: "oficial"`, con `organismo`, `fecha` y `url`). Si no hay ninguna, se continúa con los
escalones 1, 2 y 3 **y** el payload lleva `fuente_oficial: {organismo, pagina_prensa}` (el piso) para que el
correo la muestre aparte, sin pretender que es una noticia. Falla del lector = aviso y se continúa; nunca
excepción hacia arriba.

### 4. Rótulos en el correo

| Caso | Rótulo | Contenido |
|---|---|---|
| Escalón 0 con comunicado | "Lo último que publicó <organismo> (fecha)" | titular en español + enlace al documento |
| Piso | "Sitio oficial de <organismo>" | solo el enlace a su página de prensa |

Anti-anacronismo: la fecha va siempre; un comunicado de más de 3 días se redacta en pasado y sin la palabra
"hoy".

### 5. Extensión a `/seguimiento`

`contexto.preparar` recibe el mismo orden de escalones (0, 1, 2) a través de `apertura.candidatas`. El
escalón 3 (agenda) se evalúa si la pieza trae calendario; si no, queda fuera de esta etapa. El motivo
"Hoy no encontré noticias…" solo sale si los escalones vacíos incluyen también el piso del enlace.

## Decisiones de diseño (mi criterio tras la revisión; el director las puede revertir)

1. **Un candidato oficial entra por el camino normal, sin atajo.** Lleva `url`, `titular_original` y, como
   campo extra, `titular_es` ya armado por Python (8-K) o el del feed oficial. agy lo elige y escribe el
   párrafo, pero no traduce ni inventa el titular. `depurar` y `verificar_url` lo validan como a cualquier
   otro. Sin rama especial en el esquema editorial.
2. **El piso no es una noticia.** Es un tercer elemento aparte (`fuente_oficial`) que no ocupa `noticia_1`
   ni `noticia_2`, no cuenta para el motivo "Hoy no encontré noticias…" y no entra al esquema editorial
   cerrado. Lo dibujan los dos renderers del correo (`oportunidad_html.py`) y del seguimiento
   (`mensajes_html.py`) como una línea propia bajo las noticias.
3. **Los contratos no cambian de forma.** `apertura.candidatas` sigue devolviendo `(lista, aviso)`. El piso
   lo resuelve una función aparte, `fuentes_oficiales.piso(ticker)`, que llaman los dos consumidores.
   `contexto.preparar` conserva su parámetro inyectable `candidatas`; su valor por defecto pasa a un
   adaptador sobre `apertura.candidatas` que convierte el aviso en lista.
4. **Primera etapa y activos sin fuente.** Reciben entrada las acciones de EE.UU. del correo (EDGAR) y los
   activos que ya tienen feed oficial medido (EIA: WTI, Brent; BCE: EUR/USD; Fed: USD/CLP, US100, oro).
   Un activo sin entrada sigue como hoy y **no** lleva piso: la meta de "siempre una referencia oficial"
   vale solo para los activos con fuente declarada, y el documento lo dice en vez de prometer más.
5. **8-K con varios ítems.** El titular usa el ítem de mayor prioridad: 2.02, 5.02, 1.01, 2.01, 7.01, 8.01
   (en ese orden). Un ítem fuera de la lista se omite, igual que un 8-K cuyos ítems sean solo 9.01, 3.03 o
   5.03.
6. **La ventana de 45 días es del escalón 0 y se la pasa a ambos lectores**, incluido el de feeds
   oficiales. Dentro de ella **no** se aplica `ya_publicada`: "lo último que publicó" es un estado con
   fecha, no una novedad, y repetirlo entre correos del mismo activo es honesto; con una novedad en cambio
   sí sería un error. Lo que sí se hace en código (no se le deja a agy) es quitar la palabra "hoy" y
   forzar pasado en un comunicado de más de 3 días.
7. **Contacto de EDGAR.** Variable de entorno `GI_EDGAR_CONTACTO`, leída del `.env` del repo (gitignoreado)
   o del entorno del proceso del bot. Si falta, el lector devuelve un aviso y se cae al escalón siguiente;
   nunca lanza. El test de contrato exige el nombre y que el User-Agent lo incluya.

## Reglas que no cambian

Regla 1 (cifras solo si Python las leyó en la nota), Regla 0 (imagen del catálogo cerrado), URL sin ventana
de repetición (`ya_publicada`), flujo de aprobación del director, 45 s y cupo de 40 del sender.

## Fuera de alcance

- Raspado de sitios de empresa sin RSS ni EDGAR (acciones no estadounidenses, p. ej. Codelco, SQM).
- El texto "El mercado está cerrado" del análisis técnico del seguimiento: es otro defecto.
- Un lector del BCCh: se agrega cuando se mida su feed.

## Pruebas

- Con feeds falsos: 8-K de hace 6 días → escalón 0 con fecha; 8-K de hace 60 días → piso (enlace) y
  continúa con el escalón 1; EDGAR caído → aviso, continúa; ticker sin entrada → idéntico a hoy.
- Un 8-K solo 9.01 no genera candidata.
- El titular de un 8-K lo arma Python desde el ítem: ninguna candidata trae texto de agy.
- Toda entrada de `fuentes_oficiales.json` trae `pagina_prensa` con https y un `lector` conocido.
- `contexto.preparar` con `noticias` vacías y piso: no emite "Hoy no encontré noticias".
- Un test de contrato impide que el lector de EDGAR vaya sin User-Agent con contacto.

## Lo que queda al implementador

Nombre exacto del ticker de Goldman en el catálogo y su CIK; qué activos de divisas y materias primas
reciben entrada de `feed_oficial` en la primera etapa; dónde guardar el correo de contacto para EDGAR.
