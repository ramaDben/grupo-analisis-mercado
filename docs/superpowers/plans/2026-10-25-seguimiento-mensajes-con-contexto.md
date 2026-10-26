# `/seguimiento` con tres mensajes de contexto: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Después de la lámina y el texto de `/seguimiento`, el bot entrega un `mensajes.html` con tres mensajes de WhatsApp independientes (noticia 1, noticia 2, análisis técnico), redactados por agy y depurados por Python.

**Architecture:** Un trabajo nuevo `contexto` encolado en la misma cola del bot, después de entregar el seguimiento. Python junta noticias candidatas (FXStreet e Investing.com) y los hechos técnicos del seguimiento ya preparado, y sella todo en un `pieza.json` de tipo `contexto`. agy (`/analista <ruta>`) solo elige y redacta; Python valida, reemplaza las marcas de precio por valores del terminal y arma el HTML.

**Tech Stack:** Python 3 con `uv`, pytest, el módulo `scripts/analista/` existente, agy vía `agy_encargo.invocar`, Telegram.

**Spec:** `docs/superpowers/specs/2026-10-25-seguimiento-mensajes-con-contexto-design.md` (aprobado por el director el 2026-10-25, incluida la extensión de la excepción de cifras de la Regla 1 a `/seguimiento`).

## Global Constraints

- Todo texto de cliente en español chileno, tuteo, **sin `—` ni `–`** como inciso, sin voseo ni «hawkish/dovish» sin traducir.
- **Regla 1:** ningún precio lo escribe agy. Los precios salen de las marcas `[[NIVEL]]`, `[[OBJETIVO]]`, `[[SIGUIENTE]]` que Python reemplaza con el valor formateado a los `digits` del activo.
- **Cifras de una noticia:** solo valen si Python leyó la nota y las encontró en su texto; con muro de pago, sin cifras (`noticia._motivo`, mismo criterio que `/oportunidad`).
- Frescura de noticias: 3 días (`noticia.VENTANA_DIAS`). Nunca se inventa una noticia: una tarjeta sin material sale vacía con su motivo.
- El HTML es un solo archivo, sin recursos externos, legible en celular, con botón **Copiar** por tarjeta.
- Fallos de agy: no gastan cupo, no se reusan 30 minutos y no tocan el seguimiento ya entregado.
- Reuso: `contexto|ticker=<T>` vale 30 minutos (`reuso_minutos`); el saludo del ejecutivo se aplica al responder, no se guarda en la pieza.
- Texto con precios o acentos se escribe con la herramienta Write o con Python (`Path.write_text(..., encoding="utf-8")`), nunca por la consola de PowerShell.
- Trabajar en una rama `feat/seguimiento-contexto` desde `master` (regla del repo: nunca commitear a master). agy **no** hace commit: lo hace Claude después de correr la prueba de cada tarea.
- Ejecutar pruebas con `uv run pytest <archivo> -q` desde la raíz del repo.

## Review Focus

1. Un feed que devuelve 200 con una página de bloqueo o XML roto: cero candidatas y aviso, sin excepción.
2. agy elige una URL que no está en `datos.noticias_candidatas` o repite la misma URL en las dos noticias: la tarjeta cae con su motivo.
3. Nota con muro de pago: con cifras en el texto cae; sin cifras pasa.
4. El texto técnico trae un precio escrito (`4.100,50`, `1.2345`) o una marca de un valor que no existe (`[[SIGUIENTE]]` sin siguiente): el texto cae.
5. Un segundo `/seguimiento` del mismo activo mientras agy trabaja no lanza otro agy; si el seguimiento falla no se encola contexto.
6. Texto de agy con `<`, `&` o comillas: el HTML lo escapa y el botón Copiar entrega el texto literal.
7. Dos ejecutivos piden en 30 minutos: el segundo reusa la pieza, recibe el HTML con su propio saludo y no gasta cupo ni agy.

---

## File Structure

- Create `scripts/analista/noticias_contexto.py`: candidatas de varias fuentes (FXStreet e Investing.com).
- Create `scripts/analista/contexto.py`: la pieza `contexto` (preparar, depurar, marcas, tarjetas).
- Create `scripts/analista/mensajes_html.py`: el HTML.
- Modify `scripts/analista/noticia.py`: `_motivo` parametrizable; helper compartido de feeds.
- Modify `scripts/analista/esquema.py`: tipo de pieza `contexto`.
- Modify `scripts/analista/bot.py`: trabajo `contexto`, encolado, dedupe, entrega.
- Modify `config/fuentes_prestigio.json`: medio `Investing.com`.
- Modify `.claude/commands/analista.md` y regenerar `.agents/workflows/` (`scripts/agy_workflows.py`).
- Modify `CLAUDE.md` y regenerar `.agents/rules/proyecto.md` (`scripts/agy_reglas.py`): la extensión de la excepción de cifras. **Lo hace Claude, no agy.**
- Tests: `tests/test_analista_noticias_contexto.py`, `tests/test_analista_contexto.py`, `tests/test_analista_mensajes_html.py`, y casos nuevos en `tests/test_analista_noticia.py`, `tests/test_analista_esquema.py`, `tests/test_analista_bot.py`.

---

### Task 1: Candidatas de varias fuentes

**Files:**
- Create: `scripts/analista/noticias_contexto.py`
- Modify: `scripts/analista/noticia.py` (extraer el cuerpo de `candidatas_fxstreet` a un helper compartido sin cambiar su comportamiento), `config/fuentes_prestigio.json` (agregar `"Investing.com": ["investing.com"]` a `medios`)
- Test: `tests/test_analista_noticias_contexto.py`

**Interfaces:**
- Produces:
  - `noticias_contexto.FEEDS_INVESTING: tuple[str, ...] = ("https://es.investing.com/rss/news.rss", "https://es.investing.com/rss/market_overview.rss")`
  - `noticias_contexto.MAX_CANDIDATAS = 6`
  - `noticias_contexto.candidatas(ticker: str, nombre: str, ahora: datetime, leer: Callable[[str], str] = noticia.leer_feed, ruta_patrones: Path = noticia.PATRONES_FX) -> tuple[list[dict[str, Any]], list[str]]`. Cada candidata trae `medio`, `fecha` (AAAA-MM-DD), `url`, `titular_original`. Devuelve también los avisos.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_noticias_contexto.py`, con un `leer` falso que responde un RSS por URL:
  - `test_junta_fxstreet_e_investing_sin_repetir_url`: dos notas del oro de FXStreet y una de Investing, una URL repetida entre fuentes; esperado: 3 candidatas, URLs únicas.
  - `test_alterna_fuentes_para_dar_diversidad`: con 4 de FXStreet y 2 de Investing, las dos primeras candidatas son de medios distintos.
  - `test_respeta_ventana_de_3_dias_y_patrones_del_activo`: una nota de hace 5 días y una de otro activo no entran.
  - `test_tope_de_6_candidatas`.
  - `test_feed_bloqueado_da_cero_candidatas_y_aviso`: `leer` devuelve `"<html>blocked</html>"` en todos los feeds; esperado `([], [aviso])` con aviso no vacío, sin excepción.
  - `test_un_feed_caido_no_bota_al_otro`: `leer` lanza `OSError` para Investing; las de FXStreet salen y el aviso nombra Investing.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_noticias_contexto.py -q`. Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** `candidatas` reusando `noticia._items`, `noticia._patrones` y la ventana de `candidatas_fxstreet`: extraer de esta un helper `noticia.candidatas_de_feeds(feeds, medio, ticker, nombre, ahora, leer, ruta_patrones) -> tuple[list[dict], int]` (candidatas ordenadas más reciente primero y cantidad de feeds caídos) y que `candidatas_fxstreet` lo use. `candidatas` llama al helper por fuente, alterna las dos listas, deduplica por URL y corta en `MAX_CANDIDATAS`.
- [ ] **Step 4: Run** `uv run pytest tests/test_analista_noticias_contexto.py tests/test_analista_noticia.py -q`. Expected: PASS (las pruebas existentes de `candidatas_fxstreet` siguen verdes).
- [ ] **Step 5:** Claude revisa el diff y commitea: `feat(analista): candidatas de noticias de FXStreet e Investing.com`.

### Task 2: Validación de una noticia de contexto

**Files:**
- Modify: `scripts/analista/noticia.py` (`_motivo` recibe `campos`, `textos` y `largos`; el default conserva el comportamiento actual)
- Test: `tests/test_analista_noticia.py`

**Interfaces:**
- Produces: `noticia.CAMPOS_CONTEXTO = ("medio", "fecha", "url", "titular_original", "titular", "mensaje")`, `noticia.LARGOS_CONTEXTO = {"titular": 90, "mensaje": 600}` y `noticia.motivo_de_contexto(n: Any, hoy: date, lista: dict[str, Any], verificar: Callable[[str], str], leer: Callable[[str], str | None]) -> str | None` (el motivo por el que no sale; `None` si pasa). No exige `motivo` de imagen ni `extracto`. Los textos que valida son `titular` y `mensaje`, con `es.errores_texto_noticia`.

- [ ] **Step 1: Write the failing tests** (en `tests/test_analista_noticia.py`, reusando el helper `_noticia` del archivo):
  - `test_contexto_valida_una_noticia_buena` → `None`.
  - `test_contexto_cae_si_falta_un_campo`, `..._si_el_mensaje_pasa_de_600`, `..._si_la_fecha_esta_fuera_de_ventana`, `..._si_la_url_no_es_del_dominio_del_medio`.
  - `test_contexto_con_cifra_y_muro_de_pago_cae`: `leer` devuelve `None`, el mensaje trae `4.100`; motivo contiene «cifras».
  - `test_contexto_sin_cifras_y_muro_de_pago_pasa`.
  - `test_contexto_cifra_ausente_de_la_nota_cae`.
  - `test_contexto_con_guion_largo_cae`: `mensaje` con `—` cae.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_noticia.py -q -k contexto`. Expected: FAIL.
- [ ] **Step 3: Implement** parametrizando `_motivo` (nuevos argumentos con valores por defecto iguales a los de hoy) y definiendo `motivo_de_contexto` como llamada con los campos de contexto. El chequeo de `motivo` de imagen solo corre si `"motivo"` está en `campos`.
- [ ] **Step 4: Run** `uv run pytest tests/test_analista_noticia.py -q`. Expected: PASS completo (sin romper `/oportunidad`).
- [ ] **Step 5:** commit `feat(analista): validación de noticias de contexto`.

### Task 3: La pieza `contexto` (esquema, preparar, depurar, marcas, tarjetas)

**Files:**
- Create: `scripts/analista/contexto.py`
- Modify: `scripts/analista/esquema.py` (`CAMPOS["contexto"] = ("noticia_1", "noticia_2", "tecnico")`; sumar los tres a `OPCIONALES`; `textos()` ya los omite; `errores()` acepta el tipo)
- Test: `tests/test_analista_contexto.py`, `tests/test_analista_esquema.py`

**Interfaces:**
- Consumes: `noticias_contexto.candidatas` (Task 1), `noticia.motivo_de_contexto` y `noticia.leer_texto` (Task 2), `preparar.Preparada`, `seguimiento._fmt`, `seguimiento.MARCA_SALUDO`, `seguimiento.con_saludo`.
- Produces (en `contexto.py`):
  - `MARCAS = {"[[NIVEL]]": "nivel", "[[OBJETIVO]]": "objetivo", "[[SIGUIENTE]]": "siguiente"}`
  - `preparar(ticker: str, dir_pedido: Path, ahora: datetime, seg: dict[str, Any], candidatas: Callable[[str, str, datetime], tuple[list[dict[str, Any]], list[str]]]) -> Preparada`. `seg` son los `datos` de la pieza de seguimiento. La pieza sella `datos.noticias_candidatas`, `datos.tecnico` y `datos.tecnico_motivo`. Todo `editorial` parte en `es.MARCA`, salvo `tecnico`, que queda en `None` cuando `suceso.estado in ("sin_direccion", "cerrado")` (con `tecnico_motivo` en palabras) y `noticia_1`/`noticia_2` que quedan en `None` si no hay candidatas.
  - `datos.tecnico` = `{"nombre", "sentido", "estado", "nivel", "objetivo", "siguiente", "calidad", "digits"}` copiado de `seg["suceso"]` y `seg["activo"]["digits"]`.
  - `depurar(pieza: dict[str, Any], hoy: date, lista: dict[str, Any] | None = None, verificar=fu.verificar_url, leer=nt.leer_texto) -> tuple[dict[str, Any], list[str]]`: deja cada campo de `editorial` válido o en `None`, guarda los motivos en `pieza["motivos"]` (clave por campo) y devuelve los avisos. Reglas, en este orden:
    1. Un campo en `es.MARCA` pasa a `None` con motivo «agy no lo redactó».
    2. La `url` de una noticia debe estar en `datos.noticias_candidatas` y su `titular_original` debe coincidir con el de la candidata; si no, cae.
    3. La noticia 2 cae si repite la `url` de la 1.
    4. Cada noticia pasa por `noticia.motivo_de_contexto`.
    5. `tecnico`: debe empezar con `[[SALUDO]]`, no puede traer ningún número significativo (`es._significativo`) fuera de las marcas, y solo puede usar marcas cuyo valor en `datos.tecnico` no sea `None`; si no, cae.
  - `sustituir_marcas(texto: str, tecnico: dict[str, Any]) -> str`: reemplaza cada marca con `seguimiento._fmt(valor, tecnico["digits"])`.
  - `@dataclass Tarjeta: titulo: str; texto: str | None; motivo: str; medio: str; fecha: str; url: str`
  - `tarjetas(pieza: dict[str, Any], saludo: str = "") -> list[Tarjeta]`: siempre tres, en orden «Noticia 1», «Noticia 2», «Análisis técnico». El texto final aplica `con_saludo`; en las noticias agrega al final una línea `Fuente: <medio>, <dd-mm>` (sin URL, la URL viaja en la tarjeta); en el técnico aplica `sustituir_marcas`. Una tarjeta vacía lleva `texto=None` y su motivo.
- Esquema: `es.errores(pieza)` no marca error por `noticia_1`, `noticia_2` ni `tecnico` en `None`, y sí por un valor `es.MARCA` que sobreviva.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_contexto.py` (pieza armada con `preparar` y un `seg` de ejemplo basado en `tests/analista_fixtures.py`):
  - `test_preparar_sella_candidatas_y_tecnico`, `test_preparar_sin_candidatas_deja_noticias_en_none`, `test_preparar_sin_direccion_deja_tecnico_en_none_con_motivo`.
  - `test_depurar_acepta_las_tres_tarjetas_buenas`.
  - `test_depurar_cae_noticia_con_url_fuera_de_candidatas`, `test_depurar_cae_noticia_2_con_url_repetida`, `test_depurar_marca_escribir_pasa_a_none_con_motivo`.
  - `test_depurar_tecnico_con_precio_escrito_cae` (`4.100,50` y `1.2345`), `test_depurar_tecnico_con_marca_sin_valor_cae`, `test_depurar_tecnico_sin_saludo_cae`.
  - `test_sustituir_marcas_usa_los_digits_del_activo` (`[[NIVEL]]` con `digits=2` y valor `4000.0` → `4,000.00` o el formato de `_fmt`; copiar el formato de `_fmt`, no inventarlo).
  - `test_tarjetas_siempre_tres_y_vacias_llevan_motivo`, `test_tarjetas_aplican_el_saludo_del_ejecutivo`.
  - En `tests/test_analista_esquema.py`: `test_contexto_none_no_es_error` y `test_contexto_con_marca_sobreviviente_es_error`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_contexto.py tests/test_analista_esquema.py -q -k "contexto"`. Expected: FAIL.
- [ ] **Step 3: Implement** `contexto.py` y los cambios de `esquema.py` como dice Interfaces. Los controles de texto de `tecnico` usan `es._errores_de_texto(donde, texto, "contexto", datos, cifras=False)` (solo las reglas base: guion largo, HTML, CMF, frases de recomendación) más los dos controles propios (sin números, marcas válidas).
- [ ] **Step 4: Run** `uv run pytest tests/test_analista_contexto.py tests/test_analista_esquema.py -q`. Expected: PASS completo.
- [ ] **Step 5:** commit `feat(analista): pieza de contexto con noticias y análisis técnico`.

### Task 4: El HTML de mensajes

**Files:**
- Create: `scripts/analista/mensajes_html.py`
- Test: `tests/test_analista_mensajes_html.py`

**Interfaces:**
- Consumes: `contexto.tarjetas`, `contexto.Tarjeta`.
- Produces: `render(pieza: dict[str, Any], saludo: str = "") -> str` y `guardar(pieza: dict[str, Any], dir_pedido: Path, saludo: str = "") -> Path` (escribe `dir_pedido / "mensajes.html"` en UTF-8 y devuelve la ruta).

- [ ] **Step 1: Write the failing tests:**
  - `test_html_trae_tres_tarjetas_con_su_boton_copiar`: tres `data-tarjeta`, tres botones.
  - `test_html_no_carga_recursos_externos`: ni `http://` ni `https://` en `src=`, `href=` de recursos, `<link>` ni `@import` (los `href` de la nota de la fuente sí pueden estar).
  - `test_html_escapa_el_texto`: un mensaje con `<script>` y `&` sale escapado, y el texto a copiar vive en un atributo escapado (`data-copiar`) que devuelve el literal.
  - `test_tarjeta_vacia_muestra_el_motivo_y_no_tiene_boton`.
  - `test_html_aplica_el_saludo_del_ejecutivo` (`"Juan"` → `Hola Juan,`).
  - `test_guardar_escribe_utf8_con_acentos` (`¿`, `·`, tildes se leen de vuelta).
  - `test_html_sin_guion_largo` (ni `—` ni `–` en la plantilla).
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_mensajes_html.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** con `html.escape`, estilos en línea y un `<script>` mínimo con `navigator.clipboard.writeText` y respaldo con `textarea` para navegadores sin permiso. Diseño: una columna, legible en celular; el enlace a la nota va como un `<a>` aparte en la tarjeta (no dentro del texto copiado). Seguir los colores de `templates/stories/marca.css` solo si aplica; sin hex nuevos duplicados si ya existe el token.
- [ ] **Step 4: Run** `uv run pytest tests/test_analista_mensajes_html.py -q`. Expected: PASS.
- [ ] **Step 5:** commit `feat(analista): html de mensajes de contexto`.

### Task 5: El trabajo `contexto` en el bot

**Files:**
- Modify: `scripts/analista/bot.py`
- Test: `tests/test_analista_bot.py`

**Interfaces:**
- Consumes: `contexto.preparar`, `contexto.depurar`, `mensajes_html.guardar`, `noticias_contexto.candidatas`.
- Produces:
  - `Atendedor.noticias_contexto: Callable[[str, str, datetime], tuple[list[dict[str, Any]], list[str]]] = nctx.candidatas` (campo inyectable, junto a los demás).
  - `Atendedor._contexto(self, pedido: Pedido, ahora: datetime) -> Respuesta`: despacha desde `atender` cuando `orden.pieza == "contexto"`. Flujo: reusa `estado.vigente(orden.clave_base(), ahora, minutos)` o prepara una pieza nueva en `dir_pedidos/<día>/<HHMMSS>_contexto_<slug>`; exige cupo antes de agy (`_exigir_cupo`); llama `self.redactar` y `_guardar_salida_agy`; un código distinto de `ok` levanta `FalloPedido` sin gastar cupo ni registrar la pieza; luego `contexto.depurar`, `pr.guardar_pieza` y `es.errores` (error levanta `FalloPedido`); solo con éxito: `estado.consumir`, `registrar_pieza(..., fija=False)` y `estado.guardar`. Devuelve `Respuesta(chat, texto, [mensajes.html], aparte)` con el HTML armado con el saludo de quien pide. El `aparte` lista los motivos de las tarjetas vacías y los avisos de fuentes.
  - La pieza `seguimiento` se lee de `estado.vigente("seguimiento|ticker=<T>", ...)`; si no existe (caducó), el trabajo responde «El seguimiento ya no está vigente: pídelo de nuevo».
  - `Bot._encolar_contexto(self, pedido: Pedido) -> None`: crea `Orden("contexto", {"ticker": ticker}, pedido.orden.saludo)`, deduplica con `self.generando` y `self.candado` (clave `clave_base().lower()`); si ya hay uno generando, manda «Los mensajes de contexto de <ticker> ya vienen en camino.»; si no, manda «Te preparo los tres mensajes con noticias y análisis técnico: llegan en unos minutos.» y pone el `Pedido` en la cola.
  - `Bot.trabajador` llama `_encolar_contexto` después de `entregar` cuando `pedido.orden.pieza == "seguimiento"` y `respuesta.archivos` no está vacío. `procesar_uno` libera `generando` también para `contexto`.
  - La gramática de `orden.py` **no** cambia: un usuario no puede pedir `contexto` por Telegram.

- [ ] **Step 1: Write the failing tests** (con el fixture `armado` del archivo, un `redactar` falso que escribe los tres campos y un `noticias_contexto` falso):
  - `test_contexto_entrega_el_html_con_tres_tarjetas`.
  - `test_contexto_gasta_una_pieza_del_cupo`.
  - `test_contexto_se_reusa_30_minutos_sin_gastar_cupo_ni_agy_y_con_el_saludo_de_quien_pide`.
  - `test_contexto_si_agy_falla_no_gasta_cupo_ni_se_registra`.
  - `test_contexto_con_cupo_agotado_avisa_y_no_lanza_agy`.
  - `test_seguimiento_exitoso_encola_un_contexto` y `test_seguimiento_fallido_no_encola_contexto`.
  - `test_segundo_seguimiento_mientras_genera_no_encola_otro_contexto`.
  - `test_el_usuario_no_puede_pedir_contexto_por_telegram` (`/contexto oro` responde la ayuda).
  - `test_el_seguimiento_ya_entregado_no_cambia`: la respuesta del seguimiento sigue siendo lámina más texto, como en `test_seguimiento_entrega_lamina_y_texto_sin_agy`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_bot.py -q -k "contexto"`. Expected: FAIL.
- [ ] **Step 3: Implement** lo descrito en Interfaces, siguiendo el estilo de `_oportunidad` y `_seguimiento` y el patrón de dedupe que ya usa `_encolar` para `oportunidad`.
- [ ] **Step 4: Run** `uv run pytest tests/test_analista_bot.py tests/test_analista_contexto.py tests/test_analista_mensajes_html.py -q`. Expected: PASS completo.
- [ ] **Step 5:** commit `feat(analista): el seguimiento encola los mensajes de contexto`.

### Task 6: La instrucción de agy para la pieza `contexto`

**Files:**
- Modify: `.claude/commands/analista.md` (nueva sección «Pieza `contexto`»); regenerar con `uv run python scripts/agy_workflows.py`
- Test: `tests/test_analista_instrucciones.py` (leerlo antes: ya valida el contenido de `analista.md`)

**Interfaces:**
- Consumes: el contrato de editorial de Task 3 (`noticia_1`, `noticia_2`, `tecnico`).

- [ ] **Step 1: Write the failing test** en `tests/test_analista_instrucciones.py`: `test_analista_documenta_la_pieza_contexto` verifica que `analista.md` menciona `noticia_1`, `noticia_2`, `tecnico`, `[[NIVEL]]`, `[[OBJETIVO]]`, `[[SIGUIENTE]]`, `[[SALUDO]]` y `datos.noticias_candidatas`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_instrucciones.py -q`. Expected: FAIL.
- [ ] **Step 3: Escribir la sección** (con la herramienta Write o Edit, no por consola). Debe decir: que solo se toca `editorial.noticia_1`, `noticia_2` y `tecnico`; que las noticias se **eligen de `datos.noticias_candidatas`** (la URL y el `titular_original` se copian tal cual, sin búsqueda web nueva para esta pieza) y se leen abriendo la URL; la forma de cada noticia (`medio`, `fecha`, `url`, `titular_original`, `titular` traducido de hasta 90 caracteres, `mensaje` de un párrafo de hasta 600 que empieza con `[[SALUDO]]` y cierra con una pregunta concreta al cliente); que la noticia 2 debe ser distinta de la 1 y, si hay opción, de otro medio; que una cifra solo se cita si está en el texto de la nota y que con muro de pago no se cita ninguna; que `tecnico` nunca lleva un precio escrito y usa solo las marcas permitidas según `datos.tecnico`, empieza con `[[SALUDO]]`, dice hacia dónde va el activo (alcista, bajista o lateral) y qué lo invalida, y cierra con la temporalidad en rango cuantificado; que si no hay noticia que sirva, se deja `null` en vez de inventar. Regla de tono: español chileno, sin guion largo.
- [ ] **Step 4: Run** `uv run python scripts/agy_workflows.py --check` y `uv run pytest tests/test_analista_instrucciones.py -q`. Expected: ambos PASS.
- [ ] **Step 5:** commit `feat(analista): instrucción de agy para los mensajes de contexto`.

### Task 7: Documentación de reglas (la hace Claude, no agy)

**Files:**
- Modify: `CLAUDE.md` (Regla 1: la excepción de cifras de una noticia vale también para `/seguimiento`, con la misma condición; mención breve de la pieza `contexto` en la sección del bot), `scripts/analista` AYUDA del bot (`/seguimiento` ahora termina con un HTML de tres mensajes)
- Regenerar: `uv run python scripts/agy_reglas.py` y `uv run python scripts/agy_reglas.py --check` si existe la bandera
- Test: `uv run pytest tests/test_agy_reglas.py -q` (o el que valide `proyecto.md`)

- [ ] **Step 1:** Claude edita `CLAUDE.md` y el texto `AYUDA` de `bot.py`.
- [ ] **Step 2:** regenerar `.agents/rules/proyecto.md` y correr la prueba de reglas. Expected: PASS.
- [ ] **Step 3:** suite completa `uv run pytest -q`. Expected: sin fallas nuevas.
- [ ] **Step 4:** commit `docs: extensión de la excepción de cifras a /seguimiento`.

---

## Self-review

- **Cobertura del spec:** tres tarjetas independientes (T3, T4); fuentes FXStreet e Investing.com con frescura de 3 días (T1); agy siempre redacta y Python depura (T3, T5, T6); marcas de precio (T3); tarjeta vacía con motivo (T3, T4); segundo envío en la cola, dedupe, cupo y fallos (T5); excepción de cifras documentada (T7); lo de hoy no cambia (prueba en T5).
- **Consistencia de nombres:** `contexto.preparar/depurar/sustituir_marcas/tarjetas/Tarjeta`, `noticias_contexto.candidatas`, `noticia.motivo_de_contexto`, `mensajes_html.render/guardar` y `Atendedor.noticias_contexto` se definen una vez y se usan igual abajo.
- **Decisiones del plan que el director puede revisar:** la noticia copiada al cliente no lleva URL (va en la tarjeta aparte, porque una URL despliega una tarjeta que tapa el texto); la tarjeta técnica sale vacía cuando el estado del día es `sin_direccion` o `cerrado`; agy elige solo entre las candidatas selladas, sin búsqueda web propia; los controles de texto de las noticias son los estrictos de `/oportunidad` y los del técnico, los base.
