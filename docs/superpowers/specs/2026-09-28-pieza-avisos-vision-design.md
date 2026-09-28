# Pieza diaria de Avisos: la visión de los bancos contra nuestros datos

**Fecha:** 2026-09-28 · **Rama:** `feat/pieza-avisos-vision`, que parte de `feat/linkedin-pipeline` (PR #241, se mergea primero)
**Estado:** diseño aprobado por el director. Revisado por AGY (Gemini pro), con los cinco hallazgos verificados en el código e incorporados (sección 9).

## 1. Objetivo

Producir de martes a viernes, **como imagen para el grupo de Avisos** (`01_macro_y_apertura`),
la pieza de **visión**: lo que dice un banco o un analista al lado de lo que dicen nuestros datos
del terminal, cerrada con nuestra lectura.

Tiene dos variantes:
- `cita`: una frase textual (o traducida) de un experto.
- `meta_precio`: una proyección de un banco (meta o rango) contra el precio de hoy, con el plazo
  de cada una a la vista.

**Criterio de éxito:** cada día hábil de martes a viernes, el reloj deja preparada la pieza. El
director corre `/vision`, revisa la imagen y el pie, y la aprueba o la ajusta. Nada sale sin su
aprobación. Una pieza con una cifra sin respaldo, una cita vieja o datos de más de 2 horas no se
rinde.

### Decisiones del director (2026-09-28)

| Pregunta | Decisión |
|---|---|
| Canal | Solo el grupo de Avisos |
| Días | Martes a viernes: la visión, si hay una fresca. El lunes queda para la agenda |
| Quién escribe | El reloj prepara los datos; el comando busca visiones, escribe y rinde |
| Plantilla | Una nueva, `vision`, con dos variantes |
| Agenda del lunes | **Fuera de este spec.** Hoy existe `/story calendario`; su automatización va en un spec aparte |

## 2. Flujo

```
10:30 NY  reloj_gi ──► pipeline_vision.py --preparar       (martes a viernes)
                         elige la visión: la más fresca (< 45 días) que no haya
                         salido a Avisos en 14 días; lee su activo del terminal
                         sin visión fresca → sin pieza, con aviso (resultado válido)

director  /vision ──► si no hay pieza: busca y registra una visión, y vuelve a preparar
                      escribe el texto: lectura de la imagen + pie de WhatsApp
                      pipeline_vision.py --rendir → PNG + pie.txt, con frenos
                      si pasaron más de 2 h: --refrescar (relee el terminal, conserva visión y texto)
                      muestra al director → aprueba → enviar_whatsapp --grupo avisos
```

## 3. Componentes

### 3.1 Frenos compartidos: refactor de `pipeline_linkedin`

**Por qué:** `pipeline_linkedin.validar` no se puede reutilizar tal como está. La frescura es una
constante (`FRESCURA_MAX_HORAS = 24`) y `_textos` solo recorre la estructura editorial de
LinkedIn (`paginas`, `copy`, `hashtags`). Con otro payload no vería ningún texto y no frenaría
nada, y un freno que no frena es peor que no tenerlo.

Se separa en tres funciones públicas que reciben datos genéricos, sin estructura de payload:

| Función | Recibe | Revisa |
|---|---|---|
| `validar_textos(textos)` | `[(donde, texto), …]` | Marca `[[ESCRIBIR]]` o texto vacío, guion largo o medio, voseo, marcadores sin completar |
| `validar_cifras(textos, activos, visiones, cifras_citadas)` | Lo anterior, más las filas medidas, las visiones usadas y las cifras declaradas | Cifras con `$` sin respaldo y cifras a menos de 3% de un precio medido que no coinciden con ninguno |
| `validar_frescura(leido, ahora, max_horas)` | Dos `datetime` y el máximo | Datos vencidos |

- `validar_vision` ya es genérica y queda igual.
- `pipeline_linkedin.validar` pasa a ser una función que arma los textos de LinkedIn y llama a
  las tres. **Su comportamiento no cambia**, y sus 37 tests lo prueban.
- Un test de contrato verifica que `pipeline_vision` llama a las tres. Dos implementaciones del
  mismo freno terminan divergiendo, y ese es el defecto recurrente del repo.

### 3.2 `templates/stories/vision.html`

- Lienzo horizontal 1920×1080, renderizado por `scripts/story_render.py` como las demás plantillas.
- Colores solo por `var(--rol)` de `marca.css`. El cromo va en el acento de marca; solo el dato
  lleva color (la píldora de dirección, con `--sube` / `--baja`).
- Estructura común:
  - el chip `VISIÓN · <ACTIVO>`;
  - el bloque "Lo que dicen los bancos";
  - el bloque "Lo que dicen nuestros datos": precio, dirección y mapa de niveles 🟢🟡🔴;
  - "Nuestra lectura", en una frase.
- Variante `cita`: la frase va grande, entre comillas, con firma (persona · institución · fuente
  y fecha). Si el tipo es `traduccion`, se rotula "traducción nuestra".
- Variante `meta_precio`: dos columnas, "Meta del banco" (la cifra de la cita y su plazo) y
  "Precio hoy" (la cifra del terminal y la hora de lectura).
- La variante se resuelve con fences sobre el campo `variante`, sin duplicar la plantilla.
- Los niveles citados van dibujados: el payload lleva `niveles` con `clase`, `etiqueta` y `rol`,
  armados por el script a partir de las cifras medidas.
- Fixture: `tests/fixtures/stories/payloads/vision.json`, con las dos variantes.

### 3.3 `scripts/pipeline_vision.py`

Reutiliza de `pipeline_linkedin`: `leer_activos`, `cargar_visiones`, `validar_vision`, los tres
frenos de 3.1, `mapa_niveles` y `formatear`.

| Modo | Qué hace |
|---|---|
| `--preparar` | Si hoy no es martes a viernes hábil (sección 3.6), termina con código 0 y el mensaje "hoy no corresponde". Si no, elige la visión (3.4), lee su activo del terminal y escribe `data/avisos/<fecha>_<hora>_vision/payload.json` con los huecos en `[[ESCRIBIR]]` (`lectura`, `remate`, `pie`). Anota la visión en el historial |
| `--refrescar <dir>` | Relee el terminal para el mismo activo y reemplaza `datos` y `leido_en`. **Conserva** la visión elegida y todo el texto escrito. No elige otra visión ni toca el historial |
| `--rendir <dir>` | Aplica los frenos (sección 4), arma el payload de Story, rinde el PNG con `render_story` y escribe `pie.txt` |
| `--validar <dir>` | Informa qué falta, sin escribir nada |

**Códigos de salida de `--preparar`** (el reloj decide con ellos):
- **0: pieza preparada, o resultado válido sin pieza** (no toca hoy, o no hay visión fresca). El
  reloj anota el disparo. Es el mismo criterio del escáner, que devuelve un canal vacío como
  resultado válido y no como falla.
- **1: falla de datos** (MT5 no conecta, el activo no se pudo leer). El reloj no anota y el
  momento sigue pendiente para el siguiente latido.

### 3.4 Elección de la visión

Candidatas: las visiones del registro que tienen menos de `ANTIGUEDAD_MAX_DIAS` (45), cuyo activo
está en el catálogo y que no salieron a Avisos en los últimos 14 días.

- Gana la más reciente por fecha. Si empatan, gana la que tiene la variante menos usada en los
  últimos 7 días, y después el `id` en orden alfabético, para que el resultado sea determinista.
- La variante sale del tipo: `parafrasis` con una cifra de proyección (`$` o `US$` en la cita)
  da `meta_precio`; `textual` o `traduccion` da `cita`; una `parafrasis` sin cifra da `cita`.
- Una visión cuyo activo no cotiza a las 10:30 NY (un feriado de su bolsa) se salta, y se prueba
  con la siguiente candidata.
- Se anota en `data/historial_suplementos.json` con `tipo: "vision"`, `canal`, `id` y `fecha`
  **al preparar**. Como `--refrescar` conserva la visión, un refresco tardío no la quema dos
  veces ni cae en la regla de 14 días.

### 3.5 Momento del reloj

- En `config/agenda_mercado.json`, un momento `vision_avisos` a las **10:30 de Nueva York**, con
  `clases: []` y un campo nuevo, `pieza: "vision"`.
- A las 10:30 la bolsa ya abrió y los índices tienen precio del día. Queda a 30 minutos del
  momento de las 10:00, fuera de la tolerancia de 20.

**Cambios en `reloj_gi.py`, explícitos:**
- Una tabla `PIEZAS = {"vision": ("pipeline_vision.py", "avisos")}`, que da el script y el alias
  de canal de cada pieza.
- `_correr_preparar` recibe el script y los argumentos en vez de tener `pipeline_carrusel.py`
  escrito adentro. Un momento con `pieza` corre `pipeline_vision.py --preparar`; uno sin
  `pieza` se comporta como hoy.
- `canales_del_momento`: un momento con `pieza` resuelve su canal con el **resolver de alias de
  `enviar_whatsapp`** (`avisos` en `config/whatsapp_grupos.json`), no con una lista escrita.

**Extensión documentada del invariante 4.** El invariante dice que los canales de un momento se
derivan del mapeo real de activo a canal. Un momento con `pieza` no tiene activos, así que su
canal se deriva del mapeo real de alias a grupo, que es el que usa el sender. Se actualiza la
sección "El reloj de sucesos" de `CLAUDE.md` y se regenera `.agents/rules/proyecto.md`.

**Tests que lo sostienen:**
- toda `pieza` de la agenda está en `PIEZAS`, y viceversa;
- el alias de cada pieza resuelve a un grupo existente;
- el test de que el reloj nunca envía sigue verde.

### 3.6 Días hábiles

La pieza sale de martes a viernes, si ese día es hábil en la bolsa de Nueva York según
`config/feriados_bolsa.json`, el mismo calendario que usa el escáner. Un feriado no produce
pieza (código 0, "hoy no corresponde"). La agenda del lunes no es parte de esta pieza.

### 3.7 Comando `/vision`

`.claude/commands/vision.md`, expuesto a AGY en `agy_workflows.COMANDOS`. Sus pasos:
1. Localizar la tanda que dejó el reloj en `data/avisos/`, o correr `--preparar` si no la hay.
2. Si no hay visión fresca, buscar una y registrarla con el procedimiento del PASO 2 de
   `/linkedin` (búsqueda, lectura de la fuente, navegador solo si bloquea, nunca recorrer
   LinkedIn), y volver a preparar.
3. Escribir el texto con la herramienta de edición del runner o con Python, nunca por PowerShell.
4. Rendir y mirar el PNG (tildes, ¿, ·, emoji). Si la frescura venció, `--refrescar`, revisar
   qué cifras marca el freno y volver a rendir.
5. Mostrar la imagen y el pie al director.
6. Al aprobar, guardar el pie con `ruta_mensaje.ps1` y enviar con
   `enviar_whatsapp.py --grupo avisos --adjunto <png> --mensaje-archivo <pie>`.

## 4. Frenos de `--rendir`

**Los compartidos (3.1):**
- `validar_textos` sobre `lectura`, `remate` y `pie`.
- `validar_cifras` con el activo medido, la visión usada y `cifras_citadas`.
- `validar_vision` sobre la visión elegida.
- `validar_frescura(leido, ahora, max_horas=2)`. La imagen se publica el mismo día y lleva
  precio, así que el máximo es 2 horas y no las 24 de LinkedIn.

**Los propios de la pieza:**
- El pie nombra la dirección de la píldora (alcista o bajista).
- El pie lleva el aviso "Análisis informativo. No constituye recomendación de inversión."
- El pie cierra con uno de `CIERRES_ALERTA` (`pipeline_carrusel`) o `CIERRES_MACRO`
  (`contexto_macro_grupos`), elegido por el script de forma estable por pieza y día, como en el
  carrusel, para que el despacho no vea un texto distinto al aprobado.

## 5. Errores

| Caso | Comportamiento |
|---|---|
| MT5 no conecta al preparar | Código 1. El momento queda pendiente para el siguiente latido |
| Sin visión fresca | Código 0 y el aviso "no hay visión fresca para Avisos". `/vision` ofrece buscar una |
| Lunes o feriado | Código 0 y el mensaje "hoy no corresponde" |
| Datos de más de 2 h al rendir | Se detiene y pide `--refrescar` |
| Tras refrescar, el precio del texto ya no es el medido | `validar_cifras` lo marca y se corrige el texto |
| Falla de envío | Manda la verificación de entrega de `enviar_whatsapp`. Si aborta, no se envió: revisar el chat antes de reintentar |

## 6. Pruebas

- **Frenos compartidos:** las tres funciones con casos propios, y los 37 tests de
  `pipeline_linkedin` siguen verdes sin cambios.
- **Contrato:** `pipeline_vision` llama a los tres frenos.
- **Stories:** `vision` tiene fixture con las dos variantes, rinde sin tokens huérfanos y pasa
  `marca_tokens --check`.
- **`pipeline_vision`:**
  - el lunes y un feriado dan código 0 sin payload;
  - la elección de visión (la más fresca, la exclusión por 14 días, el desempate determinista,
    ninguna fresca da código 0 con aviso, un activo sin cotización pasa a la siguiente);
  - la variante según el tipo de la cita;
  - `--refrescar` conserva la visión y el texto, y no toca el historial;
  - la frescura se detiene a los 121 minutos;
  - un pie sin dirección, sin aviso o sin cierre se detiene.
- **Reloj:**
  - `vision_avisos` no cae dentro de la tolerancia de ningún otro momento, en las tres
    configuraciones de desfase del año;
  - `PIEZAS` y la agenda coinciden;
  - el alias resuelve a un grupo existente;
  - un momento con `pieza` corre `pipeline_vision.py` y uno sin `pieza` corre el carrusel como
    hoy;
  - el reloj nunca envía.
- **Comando:** `/vision` documenta los modos que existen en el código; `agy_workflows --check`
  pasa.
- **Prueba real contra el terminal:** preparar, escribir, rendir y mirar el PNG, sin enviar.

## 7. Fuera de esta etapa

- La agenda del lunes. Existe `/story calendario`; su automatización va en un spec aparte.
- Los canales temáticos. La pieza va solo a Avisos.
- La búsqueda automática de visiones. La hace el comando, no el reloj.
- El formato "problema → solución" como imagen. Era para captar desde LinkedIn.

## 8. Archivos

| Archivo | Cambio |
|---|---|
| `scripts/pipeline_linkedin.py` | Refactor de `validar` en tres frenos públicos |
| `scripts/pipeline_vision.py` | Nuevo |
| `templates/stories/vision.html` | Nueva |
| `tests/fixtures/stories/payloads/vision.json` | Nuevo |
| `scripts/reloj_gi.py` | `PIEZAS`, `_correr_preparar` parametrizado, canal por alias |
| `config/agenda_mercado.json` | Momento `vision_avisos` |
| `.claude/commands/vision.md` | Nuevo |
| `scripts/agy_workflows.py` | `vision` en `COMANDOS` |
| `CLAUDE.md` | Extensión del invariante 4, comando `/vision` y conteo de comandos |
| `.agents/rules/proyecto.md` y `.agents/workflows/vision.md` | Regenerados |
| `tests/test_pipeline_vision.py`, `tests/test_reloj_gi.py`, `tests/test_agenda_mercado.py`, `tests/test_pipeline_linkedin.py` | Casos nuevos |

## 9. Revisión de AGY (2026-09-28) y cómo se incorporó

| Hallazgo | Verificado en el código | Incorporado en |
|---|---|---|
| Con `clases: []`, `canales_del_momento` devuelve `[]` y el reloj no prepara nada | Sí | 3.5: canal por alias para los momentos con `pieza` |
| `_correr_preparar` tiene `pipeline_carrusel.py` escrito adentro | Sí | 3.5: tabla `PIEZAS` y script como parámetro |
| `validar` de LinkedIn tiene la frescura fija y `_textos` atado a su estructura: con otro payload no frena nada | Sí | 3.1: tres frenos genéricos |
| La plantilla de agenda espera tokens que `leer_agenda` no entrega | Sí (`numero`, `dia`, `esperado`, `impacto`) | La agenda sale de este spec (7) |
| Si la frescura vence y se vuelve a preparar, la visión ya quedó quemada por la regla de 14 días | Sí, era una traba lógica | 3.3 y 3.4: `--refrescar` conserva la visión |
| Conviene separar la agenda y la visión | Coincido | La agenda sale de este spec |
