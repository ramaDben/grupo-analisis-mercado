# Carruseles de Avisos: la visión de los bancos contra nuestros datos, tres veces al día

**Fecha:** 2026-09-28 · **Rama:** `feat/pieza-avisos-vision`, que parte de `feat/linkedin-pipeline` (PR #241, se mergea primero)
**Estado:** diseño aprobado por el director. Reemplaza al spec de una pieza diaria
(`2026-09-28-pieza-avisos-vision-design.md`, en el historial git), que ya había pasado una
revisión de AGY; esos hallazgos siguen incorporados (sección 10). Pendiente: revisión de AGY de
esta versión.

## 1. Objetivo

Llevar al grupo de Avisos (`01_macro_y_apertura`) el formato de los carruseles de LinkedIn de la
primera versión: **varias láminas que ponen lado a lado lo que dice un banco y lo que dicen
nuestros datos del terminal**, cerradas con nuestra lectura. Salen **tres carruseles al día**,
uno por momento, cada uno con un tema propio y comprensible por sí solo.

**Criterio de éxito:** cada día hábil, el reloj deja preparados los tres carruseles a su hora. El
director corre `/avisos`, el comando completa la visión si falta, escribe, rinde y le muestra el
carrusel; el director lo aprueba o lo ajusta y lo despacha. Nada sale sin su aprobación. Un
carrusel con una cifra sin respaldo, una cita vieja o datos de más de 2 horas no se rinde, y uno
que el cupo del día no alcanza a cubrir entero no empieza.

### Decisiones del director (2026-09-28)

| Pregunta | Decisión |
|---|---|
| Canal | Solo el grupo de Avisos |
| Reparto | Un carrusel completo por momento, no láminas sueltas repartidas |
| Cuántos | Tres al día |
| Formatos | Mañana: cita del experto contra nuestro dato. Mediodía: meta del banco contra el precio. Tarde: agenda de la semana el lunes; balance del día de martes a viernes |
| Visiones | Las busca el comando cuando el reloj deja un carrusel sin visión fresca |
| Sin visión | Sale el carrusel sin la lámina del banco |
| Quién escribe | El reloj prepara los datos; el comando busca, escribe y rinde |

## 2. El día

| Momento | Hora NY | Chile (hoy) | Formato | Láminas |
|---|---|---|---|---|
| `avisos_manana` | 10:30 | 11:30 | `cita` | portada · voz del banco · nuestros datos · nuestra lectura |
| `avisos_mediodia` | 12:30 | 13:30 | `meta` | ídem, con la voz en la variante meta contra precio |
| `avisos_tarde` | 14:30 | 15:30 | `agenda` (lunes) o `balance` (martes a viernes) | ver 3.4 |

- **10:30** queda a 30 minutos del momento de índices (10:00), fuera de la tolerancia de 20. A esa
  hora la bolsa ya abrió y los índices tienen precio del día. **14:30** va antes del cierre de la
  bolsa (16:00) y del informe de cierre (16:45).
- La hora de Chile se mueve dos veces al año (invariante 3 del reloj); el ancla es Nueva York.
- **El balance de la tarde no gasta una visión nueva**: retoma el activo y la visión de la mañana
  ("el banco decía X, hoy el precio hizo Y"). La demanda de visiones queda en unas 10 por semana.

**Cupo.** Un carrusel son 3 o 4 envíos. Tres al día suman hasta 12, contra un tope de 40 diarios
compartido con todos los canales (hubo días de 20 a 22). Por eso el despacho verifica el cupo del
carrusel entero antes de empezarlo (3.7).

## 3. Componentes

### 3.1 Frenos compartidos: refactor de `pipeline_linkedin`

`pipeline_linkedin.validar` no se puede reutilizar tal como está: la frescura es una constante
(`FRESCURA_MAX_HORAS = 24`) y `_textos` solo recorre la estructura editorial de LinkedIn. Con otro
payload no vería ningún texto y no frenaría nada.

Se separa en tres funciones públicas que reciben datos genéricos:

| Función | Recibe | Revisa |
|---|---|---|
| `validar_textos(textos)` | `[(donde, texto), …]` | `[[ESCRIBIR]]` o vacío, guion largo o medio, voseo, marcadores sin completar |
| `validar_cifras(textos, activos, visiones, cifras_citadas)` | Lo anterior, más las filas medidas, las visiones usadas y las cifras declaradas | Cifras con `$` sin respaldo y cifras a menos de 3% de un precio medido que no coinciden con ninguno |
| `validar_frescura(leido, ahora, max_horas)` | Dos `datetime` y el máximo | Datos vencidos |

`validar_vision` ya es genérica. `pipeline_linkedin.validar` pasa a componer las tres y **su
comportamiento no cambia** (sus 37 tests lo prueban). Un test de contrato verifica que
`pipeline_avisos` las llama.

### 3.2 Las láminas

Todas en horizontal 1920×1080, para que el álbum se vea parejo. Colores solo por `var(--rol)` de
`marca.css`; el cromo va en el acento y solo el dato lleva color. Cada una con fixture en
`tests/fixtures/stories/payloads/`.

| Lámina | Plantilla | Qué lleva |
|---|---|---|
| 1 · Portada | `avisos_portada.html` (nueva) | Chip `AVISOS · <ACTIVO>`, titular, bajada, precio del terminal y hora de lectura, número de láminas |
| 2 · La voz del banco | `vision.html` (nueva) | Variante `cita`: la frase grande con firma (persona · institución · fuente y fecha), "traducción nuestra" si es `traduccion`. Variante `meta`: "Meta del banco" (cifra y plazo) contra "Precio hoy" (terminal y hora) |
| 3 · Nuestros datos | `alerta.html` (existe) | El payload de `pipeline_carrusel.construir_payload`: gráfico, niveles dibujados, dirección técnica |
| 4 · Nuestra lectura | `avisos_lectura.html` (nueva) | Titular y texto con dirección clara, firma de GI, aviso legal |

- Las variantes de `vision.html` se resuelven con dos bucles `FOR` (`bloque_cita`, `bloque_meta`):
  el script llena uno y deja el otro vacío. No se usan fences porque `story_render` solo acepta
  cuatro fijos (`_FENCES`).
- **Los precios solo viven en las láminas 1, 2 (variante meta) y 3**, que se redibujan al
  refrescar. La lámina 4 puede citar cifras, pero pasan por `validar_cifras` igual que el resto.
- Todo nivel citado va dibujado: por eso los niveles del carrusel salen en la lámina 3, que es la
  alerta con su gráfico, y no se repiten sueltos en las demás.

### 3.3 `scripts/pipeline_avisos.py`

| Modo | Qué hace |
|---|---|
| `--preparar --momento <m>` | Si hoy no es hábil (3.6), termina con código 0 y "hoy no corresponde". Si no, elige el activo y la visión (3.5), lee el terminal y escribe la tanda (3.4) con los huecos en `[[ESCRIBIR]]`. Anota lo usado en el historial |
| `--refrescar <dir>` | Relee el terminal para el mismo activo y redibuja los datos. **Conserva** la visión y todo el texto. No toca el historial |
| `--rendir <dir>` | Aplica los frenos (sección 4) y rinde cada lámina con `render_story` |
| `--validar <dir>` | Informa qué falta, sin escribir nada |

**Códigos de `--preparar`** (el reloj decide con ellos):
- **0**: tanda preparada, o resultado válido sin tanda (no toca hoy). El reloj anota el disparo.
  Una tanda **sin visión** también es código 0: lleva la marca `_falta_vision` y la completa el
  comando.
- **1**: falla de datos (MT5 no conecta, el activo no se pudo leer). El reloj no anota y el
  momento sigue pendiente para el siguiente latido.

### 3.4 La tanda: el formato que el despacho ya entiende

```
data/carrusel/<fecha>_<hora>_avisos_<momento>/01_macro_y_apertura/
  1_portada.json     1_portada.png     1_portada_mensaje.txt
  2_voz.json         2_voz.png         2_voz_mensaje.txt        (falta si no hay visión)
  3_datos.json       3_datos.png       3_datos_mensaje.txt
  4_lectura.json     4_lectura.png     4_lectura_mensaje.txt
  _avisos.json       (activo, momento, formato, id de visión, _falta_vision)
```

- Se escribe bajo `pipeline_carrusel.DIR_TRABAJO` y con la carpeta del canal, así
  `piezas_del_grupo` y `despachar` la recorren sin cambios de estructura.
- **Cada payload declara `_plantilla`** (`avisos_portada`, `vision`, `alerta`, `avisos_lectura`).
- **Cada lámina lleva texto.** El despacho detiene una imagen sin mensaje
  (`PiezaSinMensajeError`), y con razón. La lámina 1 lleva el pie completo; las demás, uno corto de
  posición (*"2/4 · La voz del banco"*), que además le dice al cliente el orden si WhatsApp no
  agrupa el álbum.
- Sin visión, `2_voz` no existe y las posiciones se numeran sobre 3.

**Formatos de la tarde:**
- `agenda` (lunes): portada · la semana (plantilla `calendario`, con los eventos de alto impacto
  de `obtener_calendario_macro` para los cinco días) · nuestra lectura de qué mirar. Sin lámina
  de alerta: la agenda no es de un activo. **La plantilla `calendario` espera tokens que hoy nadie
  arma** (`numero`, `dia`, `esperado`, `impacto`); `pipeline_avisos` los construye a partir del
  calendario y un test lo cubre (hallazgo de AGY de la revisión anterior).
- `balance` (martes a viernes): el activo de la mañana. Portada · la voz de la mañana (se
  vuelve a citar: la regla de 14 días no aplica dentro del mismo día) · nuestros datos
  releídos · nuestra lectura del día. Si la mañana no tuvo tanda, el balance toma el activo de
  mediodía; si tampoco, se elige como en 3.5 y sale sin voz.

### 3.5 Elección del activo y de la visión

**Candidatos:** `pipeline_informe.ACTIVOS_INFORME` ∪ `screener_gi.cobertura_fija()` (USD/CLP, oro,
WTI, Brent, US100, cobre), sin los que Avisos ya cubrió hoy y sin los que tienen feriado de su
bolsa (`screener_gi.gate_feriado`).

**Orden:**
1. Primero, los activos con una visión fresca de la variante del momento: menos de 45 días
   (`ANTIGUEDAD_MAX_DIAS`), que no haya salido a Avisos en 14 días. `meta` exige un `horizonte`
   registrado, porque la lámina muestra el plazo.
2. Entre ellos, el menos cubierto en Avisos en los últimos 7 días; después, el ticker en orden
   alfabético, para que el resultado sea determinista.
3. Si ningún activo tiene visión fresca, el menos cubierto en 7 días, con `_falta_vision`.

**Esto no usa el `Score_GI`** (cambio respecto de lo conversado): el score mide espacio para una
operación intradía, y lo que hace valer un carrusel de Avisos es que haya una voz de banco que
contrastar. Ordenar primero por visión disponible también reduce las búsquedas del comando.

**Variante de la visión:** `parafrasis` con una cifra de proyección da `meta`; `textual` o
`traduccion` da `cita`. Una `parafrasis` sin cifra sirve para `cita`.

**Historial:** `data/historial_suplementos.json`, con dos tipos de entrada que se anotan **al
preparar** (mismo criterio del suplemento: una tanda descartada gasta la ventana, hacia el lado
seguro):
- `tipo: "vision"` con `canal`, `id` y `fecha` (ventana de 14 días);
- `tipo: "avisos"` con `canal`, `activo`, `momento` y `fecha` (activos cubiertos hoy y en 7 días).

Cuando el comando registra una visión nueva para una tanda con `_falta_vision`, `--preparar` no
se vuelve a correr: el comando llama a `pipeline_avisos.py --completar-vision <dir> <id>`, que
arma la lámina 2, renumera y anota la visión. Así la tanda no cambia de activo.

### 3.6 Días hábiles

Un día hábil es de lunes a viernes y hábil en la bolsa de Nueva York según
`config/feriados_bolsa.json`, el calendario que usa el escáner. Un feriado no produce tandas
(código 0). El feriado de la bolsa de un activo lo saca de los candidatos (3.5), no del día.

### 3.7 El despacho se extiende, no se duplica

`pipeline_carrusel.py --despachar <tanda>` sigue siendo el único camino al cliente. Duplicarlo
para Avisos sería repetir el defecto de siempre: dos implementaciones del mismo freno divergen.

Tres cambios:

1. **El refresco elige por `_plantilla`.** Hoy `_refrescar_y_rendir` supone que toda pieza
   numerada es una alerta y la rinde con la plantilla fija, así que una portada saldría dibujada
   como alerta. Pasa a buscar la función de refresco en una tabla por plantilla
   (`alerta` → `refrescar_payload`, la de hoy; las de Avisos → funciones de `pipeline_avisos`,
   importadas en forma perezosa para no crear una importación circular). **Una pieza sin
   `_plantilla` se trata exactamente como hoy**, y un test lo fija: el carrusel temático no
   cambia.
2. **El cupo se verifica por canal antes de empezar.** El sender comprueba el cupo por acción, así
   que un carrusel podría salir hasta la lámina 2 y cortarse. Antes del primer envío de un canal,
   el despacho compara las piezas pendientes contra el cupo restante y, si no alcanza, no envía
   ninguna y lo informa. Un carrusel a medias es peor que ninguno.
3. **Una divergencia frena el canal entero.** Si al refrescar el precio cruzó un nivel o la
   dirección dio vuelta (`divergencia_editorial`), o si una cifra del texto dejó de coincidir con
   la medida (`validar_cifras`), no sale **ninguna** lámina del carrusel: la portada y la lectura
   citan el mismo precio que la alerta. Para el carrusel temático sigue valiendo pieza a pieza.

La bitácora (`data/historial_despachos.json`), la cadencia de 45 s y la reanudación quedan como
están.

### 3.8 Momentos del reloj

En `config/agenda_mercado.json`, tres momentos con `clases: []`, `pieza: "avisos"` y un campo
`formato` (`cita`, `meta`, `tarde`), y sus nombres acentuados porque salen en el aviso de cambio
de horario.

**Cambios en `reloj_gi.py`:**
- `PIEZAS = {"avisos": {"script": "pipeline_avisos.py", "canal_alias": "avisos"}}`.
- `_correr_preparar` recibe la pieza: con pieza corre `pipeline_avisos.py --preparar --momento
  <nombre>`; sin pieza, el carrusel como hoy.
- `canales_del_momento`: un momento con `pieza` resuelve su canal con
  `pipeline_carrusel.resolver_grupo_solicitado`, el índice de alias que usa el despacho. Nada del
  sender: `test_el_reloj_no_puede_enviar_nada_a_whatsapp` sigue verde.

**Extensión documentada del invariante 4:** un momento con `pieza` no tiene activos, así que su
canal se deriva del mapeo real de alias a grupo. Se actualiza "El reloj de sucesos" en
`CLAUDE.md` y se regenera `.agents/rules/proyecto.md`.

### 3.9 Comando `/avisos`

`.claude/commands/avisos.md`, expuesto a AGY en `agy_workflows.COMANDOS`. Pasos:
1. Localizar las tandas de Avisos de hoy sin despachar, o correr `--preparar --momento` si el
   director pide una fuera de hora.
2. Si la tanda tiene `_falta_vision`: buscar una visión reciente del activo (búsqueda web, lectura
   de la nota, Playwright solo si la fuente bloquea; nunca recorrer LinkedIn; ante un muro de
   pago, solo lo que la fuente muestra abierta), registrarla en `data/visiones_expertos.json` con
   fecha, URL, tipo y horizonte si es meta, y correr `--completar-vision`. Si no encuentra nada,
   sigue sin la lámina.
3. Escribir los textos con la herramienta de edición del runner o con Python, nunca por
   PowerShell.
4. `--rendir` y mirar cada PNG (tildes, ¿, ·, emoji). Si la frescura venció, `--refrescar`.
5. Mostrar el carrusel y los pies al director.
6. Al aprobar, despachar con `pipeline_carrusel.py --despachar <tanda>` (con `--with
   MetaTrader5`, para que el refresco opere).

## 4. Frenos de `--rendir`

- `validar_textos` sobre todos los textos editoriales de todas las láminas y sus mensajes.
- `validar_cifras` con el activo medido, la visión usada y `cifras_citadas`.
- `validar_vision` sobre la visión (y sobre la de la mañana, en el balance).
- `validar_frescura(leido, ahora, max_horas=2)`: se publica el mismo día y lleva precio.
- El pie de la lámina 1 nombra la dirección técnica (alcista o bajista), salvo en la agenda.
- **El cierre y el aviso los agrega el script**: el pie de la lámina 1 termina con un cierre de
  `CIERRES_ALERTA` elegido con `elegir_variante(CIERRES_ALERTA, activo, momento, fecha)` y "Análisis
  informativo. No constituye recomendación de inversión." Estable por tanda, para que el despacho
  no vea un texto distinto al aprobado.
- `exigir_texto_editorial` sigue corriendo en las dos rutas de render, como exige su test de
  contrato.

## 5. Errores

| Caso | Comportamiento |
|---|---|
| MT5 no conecta al preparar | Código 1. El momento queda pendiente |
| Ningún activo con visión fresca | Tanda con `_falta_vision` (código 0); el comando busca |
| La búsqueda no encuentra visión | Carrusel de 3 láminas |
| Feriado NYSE | Código 0, "hoy no corresponde" |
| Datos de más de 2 h al rendir | Se detiene y pide `--refrescar` |
| El cupo no alcanza para el carrusel | No sale ninguna lámina; se informa |
| Divergencia al despachar | No sale ninguna lámina; las piezas quedan `.divergente` |
| Falla de envío a mitad | La bitácora registra lo entregado; al reanudar no se repite |

## 6. Pruebas

- **Frenos compartidos:** las tres funciones con casos propios; los 37 tests de LinkedIn verdes.
- **Contrato:** `pipeline_avisos` llama a los tres frenos; toda `_plantilla` que escribe tiene su
  función de refresco en la tabla del despacho.
- **Stories:** `avisos_portada`, `vision` (dos variantes) y `avisos_lectura` con fixture, sin tokens
  huérfanos y con `marca_tokens --check`; `calendario` rinde con los tokens que arma el script.
- **`pipeline_avisos`:** feriado sin tanda; orden de candidatos (visión fresca primero, 7 días,
  alfabético, feriado del activo fuera, cubierto hoy fuera); `meta` sin horizonte no califica;
  `_falta_vision`; numeración con y sin voz; balance que retoma la mañana y cae a mediodía;
  agenda del lunes; `--completar-vision` no cambia el activo; `--refrescar` conserva texto y
  visión; frescura a los 121 min; pie sin dirección se detiene; cierre estable.
- **Despacho:** una pieza sin `_plantilla` se refresca y rinde como hoy; una portada se rinde con
  su plantilla; cupo insuficiente no envía nada; una divergencia en la lámina 3 frena las cuatro;
  el carrusel temático sigue pieza a pieza.
- **Reloj:** los tres momentos fuera de la tolerancia de todos los demás en las tres
  configuraciones de desfase; `PIEZAS` y la agenda coinciden; el alias resuelve a un grupo; un
  momento con pieza corre `pipeline_avisos.py --momento`; el reloj nunca envía.
- **Comando:** `/avisos` documenta los modos que existen; `agy_workflows --check` pasa.
- **Prueba real:** preparar los tres momentos contra el terminal, completar, rendir y despachar
  con `--dry-run`, sin enviar.

## 7. Fuera de esta etapa

- Los canales temáticos: los carruseles van solo a Avisos.
- La búsqueda de visiones desde el reloj: el reloj corre solo Python; busca el comando.
- El envío automático: el director aprueba cada carrusel.
- El formato "problema → solución" de LinkedIn (captación de leads).

## 8. Archivos

| Archivo | Cambio |
|---|---|
| `scripts/pipeline_linkedin.py` | Tres frenos públicos |
| `scripts/pipeline_avisos.py` | Nuevo |
| `templates/stories/avisos_portada.html`, `vision.html`, `avisos_lectura.html` | Nuevas |
| `tests/fixtures/stories/payloads/` | Fixtures de las tres |
| `scripts/pipeline_carrusel.py` | Refresco por `_plantilla`, cupo por canal, divergencia por canal en tandas de Avisos |
| `scripts/reloj_gi.py` | `PIEZAS`, `_correr_preparar` con pieza, canal por alias |
| `config/agenda_mercado.json` | Tres momentos |
| `data/visiones_expertos.json` | `horizonte` en las visiones de meta |
| `.claude/commands/avisos.md` | Nuevo |
| `scripts/agy_workflows.py` | `avisos` en `COMANDOS` |
| `CLAUDE.md` | Invariante 4, comando `/avisos`, conteo de comandos, despacho por plantilla |
| `.agents/rules/proyecto.md`, `.agents/workflows/avisos.md` | Regenerados |
| `tests/test_pipeline_avisos.py`, `test_pipeline_carrusel.py`, `test_reloj_gi.py`, `test_agenda_mercado.py`, `test_pipeline_linkedin.py`, `test_story_render.py` | Casos nuevos |

## 9. Riesgo principal

El cambio 3.7 toca el único camino que llega al cliente. Se acota con tres cosas: una pieza sin
`_plantilla` sigue exactamente el camino de hoy, con test; el comportamiento por canal (cupo y
divergencia) solo se activa para las tandas con `_avisos.json`; y la prueba real termina en
`--dry-run`.

## 10. Revisión de AGY del spec anterior, vigente

| Hallazgo | Dónde quedó |
|---|---|
| Con `clases: []`, `canales_del_momento` devuelve `[]` | 3.8: canal por alias |
| `_correr_preparar` tiene `pipeline_carrusel.py` escrito adentro | 3.8: `PIEZAS` |
| `validar` de LinkedIn no frena con otro payload | 3.1 |
| La plantilla `calendario` espera tokens que nadie arma | 3.4: los arma `pipeline_avisos` |
| Volver a preparar quemaba la visión por la regla de 14 días | 3.3 y 3.5: `--refrescar` y `--completar-vision` conservan |
