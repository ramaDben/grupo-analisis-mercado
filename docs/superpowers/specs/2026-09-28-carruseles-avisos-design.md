# Carruseles de Avisos: la visión de los bancos contra nuestros datos, tres veces al día

**Fecha:** 2026-09-28 · **Rama:** `feat/pieza-avisos-vision`, que parte de `feat/linkedin-pipeline` (PR #241, se mergea primero)
**Estado:** diseño aprobado por el director. Reemplaza al spec de una pieza diaria
(`2026-09-28-pieza-avisos-vision-design.md`, en el historial git), que ya había pasado una
revisión de AGY; esos hallazgos siguen incorporados (sección 12). Esta versión la revisó AGY y sus
hallazgos están incorporados (sección 11).

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
| Decisiones de tasas (2026-09-28) | Se cubren sí o sí, con el resultado y su impacto (formato `tasas`, 3.4). Fed: reemplaza a `avisos_tarde`. BCE: reemplaza a `avisos_manana`. Banco Central de Chile: momento propio `avisos_bcch` a las 18:30 de Santiago |

## 2. El día

| Momento | Hora NY | Chile (hoy) | Formato | Láminas |
|---|---|---|---|---|
| `avisos_manana` | 10:30 | 11:30 | `cita`, o `tasas` el día de decisión del BCE | portada · voz del banco · nuestros datos · nuestra lectura |
| `avisos_mediodia` | 12:30 | 13:30 | `meta` | ídem, con la voz en la variante meta contra precio |
| `avisos_tarde` | 14:30 | 15:30 | `agenda` (lunes), `balance` (martes a viernes) o `tasas` (día de decisión de la Fed) | ver 3.4 |
| `avisos_bcch` | anclado a Santiago: 18:30 | 18:30 | `tasas`, solo el día de Reunión de Política Monetaria del BCCh; los demás días no produce tanda | ver 3.4 |

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
- `tasas` (decisión del director del 2026-09-28): la decisión de tasas de la Fed, del BCE y del
  Banco Central de Chile se cubre sí o sí, con el resultado y su impacto. Las tres comparten
  formato y frenos; cambia el momento en que salen (abajo).

  **Fed.** Reemplaza a la agenda o al balance de ese día. La Fed publica la decisión a las 14:00 NY y
  la conferencia del presidente empieza a las 14:30 NY, así que el momento de la tarde (14:30 NY,
  15:30 Chile hoy) cae media hora después del resultado, con la primera reacción del mercado ya
  medible. El ancla sigue siendo Nueva York: en noviembre, cuando cambia el desfase, el carrusel
  sigue saliendo media hora después de la decisión aunque en Chile sean las 16:30.

  **BCE.** Reemplaza al carrusel de la mañana (`cita`) de ese día. El BCE publica a las 14:15 de
  Fráncfort y la conferencia de Lagarde empieza a las 14:45: eso es 08:15 o 09:15 NY según el
  desfase (10:15 Chile el 29 de octubre de 2026, medido con `hora_chile.ps1`). El momento de la
  mañana (10:30 NY) cae entre 1 h 15 y 2 h 15 después, con el resultado y la conferencia ya
  conocidos. **No se crea un momento propio** porque la invariante del reloj lo impide: 30 minutos
  después de la decisión (14:45 Fráncfort) cae a las 08:45 NY, a 15 minutos de `premercado_fx`
  (08:30) y de `cripto` (09:00), y en las semanas de desfase a las 09:45 NY, a 15 minutos de
  `apertura_indices` (10:00). Siempre dentro de la tolerancia de 20, y el decisor perdería uno de
  los dos en silencio.

  **Banco Central de Chile.** Momento propio, `avisos_bcch`, anclado a Santiago (`zona`) a las
  18:30: el comunicado de la Reunión de Política Monetaria sale a las 18:00 hora de Chile y ningún
  momento del día cae después. Los días sin reunión `--preparar` termina con código 0 sin escribir
  nada ("hoy no corresponde"), el mismo contrato de los feriados. Con la tarde en 14:30 NY
  (entre 14:30 y 16:30 Chile en el año), queda al menos dos horas de cualquier otro momento en las
  tres configuraciones del desfase, que es lo que exige el test del reloj.
  **A las 18:30 el mercado formal del dólar en Chile ya cerró**, así que el impacto en el USD/CLP no
  se puede medir esa tarde: medirlo sobre cotizaciones sin mercado formado sería publicar ruido.
  Esa lámina pasa a ser el **impacto esperado** para la apertura (hacia dónde debería abrir el
  USD/CLP según el veredicto), rotulado como anticipación. Al día hábil siguiente, el carrusel de
  la mañana toma el USD/CLP como activo (salta la elección de 3.5) y muestra la reacción medida
  ya con mercado abierto.

  - **Cuándo:** el día lo marca el calendario (`obtener_calendario_macro`: decisión de tasas de la
    Fed, del BCE y la RPM del BCCh; los nombres vienen en inglés como los entrega la fuente), no
    una lista de fechas escrita a mano.
  - **Láminas:** portada (la decisión en una línea: sube, baja o mantiene, y la tasa nueva) · el
    resultado (tasa decidida contra la esperada y la anterior, con veredicto en línea / más dura /
    más suave que lo esperado) · el impacto (cuánto se movieron desde la decisión hasta la lectura
    los activos que mueve ese banco, leído del terminal: Fed → USD/CLP, oro y US100; BCE → oro y
    USD/CLP por el dólar global; BCCh → impacto esperado en USD/CLP, ver arriba) · nuestra lectura
    (qué significa para el bolsillo y qué mirar en la conferencia o en la apertura).
  - **El impacto no publica soporte ni resistencia.** Media hora o dos después de una decisión rige
    el blackout del escáner (FOMC −30/+75 min, BoJ y RPM de Chile): los niveles tácticos son
    ruido. Lo que se publica es el movimiento medido desde la decisión, que es justo lo que el
    blackout no invalida.
  - **Sin resultado no hay carrusel a medias.** Si a la hora de preparar el calendario todavía no
    trae el valor `actual`, `--preparar` no escribe la tanda y sale con falla de datos (código 1):
    el momento queda pendiente y el reloj reintenta en el siguiente latido, dentro de la
    tolerancia de 20 minutos. Publicar la decisión sin el número sería inventarlo.
  - **"Sí o sí" no salta la aprobación.** El reloj prepara y el comando escribe; el director
    aprueba antes del envío, como todo lo demás. Lo que cambia es que ese día el formato no se
    elige ni se omite. Si el cupo no alcanza para el carrusel entero (3.7), el despacho lo dice
    en vez de saltarlo en silencio.

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
2. **El cupo se verifica por canal antes de empezar.** El sender comprueba el cupo por acción
   (`_esperar_turno` dentro del bucle de `enviar_lote`), así que un carrusel podría salir hasta la
   lámina 2 y cortarse. El sender gana un método público de solo lectura, `cupo_restante()`, que
   lee el mismo contador que `_esperar_turno`; antes del primer envío de un canal de Avisos, el
   despacho compara las piezas pendientes (descontando las ya anotadas en la bitácora) contra ese
   cupo y, si no alcanza, no envía ninguna y lo informa. Un carrusel a medias es peor que ninguno.
   El freno por acción del sender queda intacto: este se suma, no lo reemplaza.
3. **Una divergencia frena el canal entero.** Si al refrescar el precio cruzó un nivel o la
   dirección dio vuelta (`divergencia_editorial`), o si una cifra del texto dejó de coincidir con
   la medida (`validar_cifras`), no sale **ninguna** lámina del carrusel: la portada y la lectura
   citan el mismo precio que la alerta. Para el carrusel temático sigue valiendo pieza a pieza.

4. **Un refresco fallido no deja salir un carrusel viejo.** Hoy, si `analizar_activo` falla en el
   refresco, la pieza "sale con los datos de la preparación", y una pieza sin ticker en
   `_procedencia` "se despacha tal cual". Para una alerta suelta es un aviso aceptable; para un
   carrusel con frescura de 2 h deja pasar precios viejos. En una tanda de Avisos: un refresco
   fallido frena el canal si la lectura de la preparación tiene más de 2 h
   (`validar_frescura`), y toda lámina con precio lleva `_procedencia.ticker`. Las láminas sin
   precio (la agenda del lunes, la lectura) declaran en la tabla de refresco una función nula
   explícita, no una ausencia: así ninguna pieza cae en el camino "tal cual" sin que alguien lo
   haya decidido.

La bitácora (`data/historial_despachos.json`), la cadencia de 45 s y la reanudación quedan como
están. **Al reanudar un carrusel cortado a mitad**, solo salen las láminas que faltan y WhatsApp
puede no agruparlas con las primeras; el pie de posición (*"3/4 · Nuestros datos"*) es lo que le
conserva el contexto al lector, y por eso es obligatorio en toda lámina.

**El orden de las láminas** lo da `sorted(glob("*.png"))`, que ordena como texto: vale mientras
un carrusel tenga menos de 10 láminas (con 10, `10_` iría antes que `2_`). Hoy son 4 como
máximo; `pipeline_avisos` rechaza armar más de 9.

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

## 9. Entrega en dos hitos

Por sugerencia de AGY, el trabajo se parte en dos PR, cada uno con su plan:

| Hito | Contenido | Toca el camino al cliente |
|---|---|---|
| 1 | Frenos compartidos (3.1), las tres plantillas (3.2), `pipeline_avisos.py` completo con sus tests (3.3 a 3.6) | No: produce tandas y PNG en disco |
| 2 | Despacho extendido (3.7) y `cupo_restante` del sender, momentos del reloj (3.8), comando `/avisos` (3.9), documentación | Sí |

El hito 1 se puede probar entero contra el terminal (preparar, completar, rendir y mirar las
láminas) sin que exista ningún camino de envío. El reloj va en el hito 2 para que no deje tandas
en disco que nadie puede despachar.

## 10. Riesgo principal

El cambio 3.7 toca el único camino que llega al cliente. Se acota con tres cosas: una pieza sin
`_plantilla` sigue exactamente el camino de hoy, con test; el comportamiento por canal (cupo y
divergencia) solo se activa para las tandas con `_avisos.json`; y la prueba real termina en
`--dry-run`.

## 11. Revisión de AGY de esta versión (2026-09-28)

Veredicto: aprobar con cambios. Ningún hallazgo alto.

| Hallazgo | Verificado | Dónde quedó |
|---|---|---|
| El sender cobra el cupo por acción; el "todo o nada" necesita leer su estado antes | Sí | 3.7.2: `cupo_restante()` |
| Al reanudar a mitad, las láminas restantes pueden no agruparse | Opinión razonable | 3.7: pie de posición obligatorio |
| El orden por texto falla desde 10 láminas | Sí | 3.7: tope de 9 |
| Una visión registrada con datos malos la frena `validar_cifras` | Sí | Sin cambio: el freno es la protección |
| Partir el alcance | Coincido | 9: dos hitos |
| (Propio, no lo vio AGY) Un refresco fallido o sin ticker deja salir la pieza con datos viejos | Sí, `_refrescar_y_rendir` | 3.7.4 |

## 12. Revisión de AGY del spec anterior, vigente

| Hallazgo | Dónde quedó |
|---|---|
| Con `clases: []`, `canales_del_momento` devuelve `[]` | 3.8: canal por alias |
| `_correr_preparar` tiene `pipeline_carrusel.py` escrito adentro | 3.8: `PIEZAS` |
| `validar` de LinkedIn no frena con otro payload | 3.1 |
| La plantilla `calendario` espera tokens que nadie arma | 3.4: los arma `pipeline_avisos` |
| Volver a preparar quemaba la visión por la regla de 14 días | 3.3 y 3.5: `--refrescar` y `--completar-vision` conservan |

## 13. Cambios del 2026-09-29: la agenda del día manda en Avisos

Decisiones del director del 2026-09-29, tomadas después de que una tanda de solo WTI reenviara a
Avisos el contexto macro con el VIX. Este apartado **prevalece** sobre las secciones anteriores
donde se contradicen.

### 13.1 Por qué pasó el envío de más

`pipeline_carrusel.canales_con_contexto_macro` agrega Avisos a **toda** tanda (regla 3, decisión
del 2026-09-03), y la bitácora deduplica por `(tanda, canal, pieza)`. Una tanda nueva del mismo
día es, para la bitácora, contenido nuevo: el contexto de Avisos salió a las 09:55 y otra vez a las
10:05, esta segunda en el formato viejo.

### 13.2 El día de Avisos

| Momento | Hora | Cuándo sale | Formato |
|---|---|---|---|
| `avisos_agenda` | **07:45 Santiago** (`zona`) | Todo día hábil | `agenda_dia` si hay datos de alto impacto entre esa hora y las 18:30 Chile; si no, `agenda` (lo que queda de la semana) |
| `avisos_resultado` | Por suceso, no por hora | Cuando un dato de la agenda del día ya trae `actual` | `resultado` (una pieza) o `tasas` (carrusel, decisiones de la Fed, el BCE y el BCCh, ver 3.4) |
| `avisos_manana` | 10:30 NY | **Solo los días sin datos de alto impacto** | `cita` |
| `avisos_mediodia` | — | **Se elimina** | — |
| `avisos_tarde` | 14:30 NY | Todo día hábil | `balance`, o `tasas` el día de la Fed; el lunes, `balance` (la semana ya salió en la agenda) |
| `avisos_bcch` | 18:30 Santiago | Día de RPM | `tasas` |

- **Por qué 07:45 Santiago y no una hora de Nueva York.** Los datos de EE.UU. salen a las 08:30 NY,
  que en Chile cae entre las 08:30 y las 10:30 según el desfase, y el IPC de Chile sale a las
  08:00 Santiago. La agenda tiene que llegar antes de todos. Con desfase +0 queda a 45 minutos de
  `premercado_fx`, fuera de la tolerancia de 20.
- **La ventana de la jornada cierra a las 18:30 Chile**, la hora de la última noticia local (el
  comunicado de la RPM). Un dato asiático de la noche queda fuera: le toca a la agenda del día
  siguiente, que es cuando mueve el precio.
- **Cupo.** Día con datos: agenda (3) + uno o dos resultados + balance (3 o 4), unos 8 envíos. Día
  sin datos: semana (3) + cita (4) + balance (3 o 4). Antes el diseño llegaba a 12 más los
  contextos.

### 13.3 Formato `agenda_dia`: tres láminas

1. **Portada** (`avisos_portada`): el dato que manda hoy, y cuántos datos hay.
2. **La agenda** (`calendario`): solo los datos de alto impacto de la ventana, con hora Chile,
   previo, esperado y la etiqueta de impacto. Con uno o dos eventos la plantilla agranda las
   filas para llenar el lienzo (hecho el 2026-09-29).
3. **Nuestra lectura** (`avisos_lectura`): por cada dato, qué mide y qué pasa con el dólar
   (USD/CLP), el oro y el petróleo si sale sobre o bajo lo esperado, más una línea de "si sale en
   línea".

**Las reacciones salen de `data/glosario_siglas.json`** (`explicacion` y `si_sale_sobre_consenso`).
Un dato de la agenda sin `si_sale_sobre_consenso` deja la lectura en `[[ESCRIBIR]]` y `--rendir`
se detiene: no se publica una reacción inventada ni una a medias. Sin precios en ninguna de las
tres láminas, así que no hay nada que refrescar al despachar (función nula explícita, 3.7.4).

### 13.4 Formato `resultado`: una pieza con imagen

La plantilla es `dato_macro`: resultado contra lo esperado y lo anterior, veredicto (mejor / peor /
en línea) y el impacto en la moneda que el dato mueve, medido en el terminal desde la hora del dato
hasta la lectura:

| País del dato | Moneda que se mide |
|---|---|
| EE.UU. | USD/CLP (y el dólar global si su serie está fresca) |
| Chile | USD/CLP |
| Zona Euro | EUR/USD |
| China | Cobre y USD/CLP |

- **Sin `actual` no hay pieza.** Mismo contrato que las decisiones de tasas: código 1 y el latido
  reintenta.
- **Sin soporte ni resistencia.** Tras un dato rige el blackout del escáner; se publica el
  movimiento medido, no niveles tácticos.
- **Datos a la misma hora van en una sola pieza** (decisión del director: lo más ordenado y
  legible). Una fila por dato y un solo bloque de impacto, porque la moneda se movió una vez por
  los dos. El titular lleva el veredicto común; si los veredictos se contradicen, el titular dice
  "señales mixtas" y lo que manda es el movimiento medido.
- **El texto es el pie de la imagen** (Modo resultado, issue #93): chip del país, veredicto, una
  línea de impacto direccional, la temporalidad y el cierre.
- Un dato que es una decisión de tasas no usa `resultado`: sale como carrusel `tasas` (3.4).

### 13.5 Lo que se retira o cambia en el carrusel temático

1. **`pipeline_carrusel` deja de generar contexto macro para Avisos.** Se revierte la regla 3 de
   `canales_con_contexto_macro`: Avisos es ahora de `pipeline_avisos`. Un test falla si una tanda del
   carrusel escribe en `01_macro_y_apertura`.
2. **Avisos se deduplica por día.** La agenda y cada resultado se anotan en la bitácora con su
   fecha y su tipo (`agenda`, `resultado:<hora>`), y ninguna tanda posterior del mismo día los
   vuelve a mandar, aunque sea otra tanda.
3. **Los canales temáticos no llevan agenda** (hecho el 2026-09-29): abren con la imagen de su
   driver y siguen con gráfico y niveles.
4. **Flechas en vez de colores** en el cierre de niveles: ⬆️ sobre la resistencia, ↔️ entre los
   bordes, ⬇️ bajo el soporte (hecho el 2026-09-29 en el mensaje de alerta). Se actualiza la
   regla 6 de formato de `CLAUDE.md` y se regenera `.agents/rules/proyecto.md`.
5. **El banco de pruebas va primero** en `/carrusel` y `/avisos`: el comando despacha con
   `--pruebas`, muestra el resultado y solo después pide la aprobación para los canales reales.

### 13.6 Pruebas nuevas

- La tanda del carrusel no escribe en `01_macro_y_apertura`.
- Una segunda tanda del mismo día no reenvía la agenda ni un resultado ya entregado.
- `agenda_dia` con cero eventos cae a `agenda`; con eventos después de las 18:30, los excluye.
- Un dato sin `si_sale_sobre_consenso` frena el rendir.
- Dos datos con la misma `hora_servidor` producen una pieza; veredictos opuestos dan "señales
  mixtas".
- `resultado` sin `actual` sale con código 1.
- `avisos_agenda` fuera de la tolerancia de todos los momentos en las tres configuraciones del
  desfase; `avisos_mediodia` ya no existe.
