# Correo con noticia de apertura · Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El correo de `/oportunidad` abre con una noticia de prensa (titular-premisa, bajada, imagen ilustrativa, fuente), sigue con el dato de tasas del banco del activo y deja el análisis técnico firmado al pie, antes de la simulación.

**Architecture:** agy encuentra y redacta la noticia en el mismo encargo `/analista` (`editorial.noticia`). Python la depura en un módulo nuevo (`noticia.py`, mismo patrón que `fuentes.depurar_pieza`/`descartar_tesis_rotas`: lo que no pasa se descarta con su motivo y la pieza sigue). Las imágenes salen de un banco por motivo (`ilustracion.py`) y las genera agy solo cuando faltan; se guardan en la clave nueva **no sellada** `pieza["ilustraciones"]`, que escribe Python después de validar. El dato de tasas lo lee Python y se sella en `datos.tasa` al preparar.

**Tech Stack:** Python 3 + uv, pytest, `requests`, el HTML de correo compatible con Outlook de `oportunidad_html.py`, agy (Gemini Flash 3.8) vía `scripts/agy_encargo.py`.

**Spec:** `docs/superpowers/specs/2026-10-24-correo-noticia-de-apertura-design.md`

**Ejecución mixta (director, 2026-10-24).** Cada tarea dice **[agy]** o **[Claude]**. Las [agy] se mandan como encargo con `scripts/agy_encargo.py delegar docs/agy/encargos/<archivo>.md`, cuyo frontmatter fija `archivos` y `verificar`, y su cuerpo copia el bloque **Interfaces** de la tarea tal cual. El "verde" de agy no cuenta: Claude revisa el diff y vuelve a correr la verificación (`agy_encargo.py verificar`) antes del commit.

## Global Constraints

- Ventana de la noticia: a lo sumo **3 días** entre `noticia.fecha` y `hoy` al preparar; pasada esa ventana en una reutilización, sale igual con la fecha en palabras.
- Largos: `noticia.titular` ≤ **90** caracteres, `noticia.bajada` ≤ **200**.
- Cifras de la noticia: solo si `verificar_url(url) == "ok"` **y** cada cifra significativa (`es._significativo`) aparece, normalizada con `es._plano_numero`, en el texto descargado de la página. Con `sin_verificar`: titular y bajada **sin** cifras significativas. Con `muerta`: se descarta.
- `%` permitido **solo** en `noticia.titular` y `noticia.bajada`; en el resto de la pieza sigue prohibido.
- Los demás controles de texto (`es._errores_de_texto` sin el control de cifras ni el de `%`) aplican a la noticia: sin guion largo, sin "operar"/"comprar"/"oportunidad", sin HTML.
- Medios válidos: los de `config/fuentes_prestigio.json` (dominio del medio, ruta de artículo), vía `fuentes.py`.
- Prompts de imagen: Python agrega siempre "sin logos, sin marcas, sin texto ni números legibles, sin banderas, sin sellos de país, sin personas reconocibles; fotografía sobria, luz cálida, formato horizontal 16:9".
- Cooldown de imagen: una imagen del banco no repite en otra pieza antes de **7 días**; se elige una vez por pieza.
- Rótulo bajo cada imagen ilustrativa: exactamente `Imagen ilustrativa`.
- Firma del análisis: `Realizado por Benjamín Bravo Soza · Departamento de Estudios GI`, **al pie** del bloque del análisis técnico (el cargo ya cambió, commit d8a7e5d).
- Tasa: nombre real de la serie y fecha del dato; nunca "la tasa de la Fed"; sin fecha de última decisión.
- Correo compatible con Outlook: colores hex, tablas, sin `var()` ni `rgba()` (comentario de `oportunidad_html.py:176-185`).
- Texto de cliente en español de Chile, tuteo, sin guion largo como inciso.

## Review Focus

1. **Cifra escrita en otro formato que la fuente** (fuente "20.06B", texto "20.060 millones"): se descarta la noticia con motivo y la pieza sale. Test en Task 3.
2. **agy deja `noticia` sin escribir (`[[ESCRIBIR]]`), vacía o `null`**: el correo sale sin la sección y sin error. Test en Task 3 y Task 6.
3. **Pieza anterior al spec reutilizada** (sin `editorial.noticia`, sin `datos.tasa`, sin `ilustraciones`): `armar()` no levanta y el correo sale con el orden nuevo sin esas secciones. Test en Task 6.
4. **Fecha de noticia futura o malformada** (`"2026-13-01"`, `"ayer"`, fecha posterior a hoy): se descarta. Test en Task 3.
5. **Generador de imágenes falla y el banco del motivo está vacío**: la noticia sale **sin imagen** con aviso al ejecutivo, sin tirar la pieza ya cobrada. Antes de eso se usa una imagen del motivo aunque esté en cooldown. *Llamada de Claude* (el spec dice "siempre imagen"; esto es el último recurso). Test en Task 2 y Task 5.

---

### Task 1 [Claude]: Medir la generación de imágenes y fijar el generador

**Files:**
- Create: `scripts/analista/generador_imagen.py`
- Test: `tests/test_analista_generador_imagen.py`
- Modify: `docs/superpowers/specs/2026-10-24-correo-noticia-de-apertura-design.md` (§2, resultado de la medición)

**Interfaces:**
- Produces: `Generador = Callable[[str, Path], Path]`; `generar_con_agy(prompt: str, destino: Path, tier: str = "flash", timeout: str = "10m") -> Path`; `class ImagenNoGenerada(RuntimeError)`. Si la medición dice que agy headless no genera, en su lugar `generar_con_gemini(prompt: str, destino: Path) -> Path` con la misma firma, y la clave en `.env` (`GEMINI_API_KEY`), nunca en el repo.

- [ ] **Step 1: Medir.** Correr a mano `agy` headless (vía `agy_encargo.invocar`) con un prompt "genera una imagen de lingotes de oro… y guárdala en `<scratchpad>/prueba.png`". Anotar: si genera, cuánto tarda, el tamaño y si el archivo queda donde se pidió. Si no genera, probar la API de imágenes de Gemini (consultar context7 para el SDK vigente antes de escribir la llamada).
- [ ] **Step 2: Escribir el resultado** en §2 del spec (una línea con lo medido y la vía elegida).
- [ ] **Step 3: Test que falla** `test_generar_levanta_si_no_queda_el_archivo`: con `invocar` reemplazado por un doble que no escribe nada, `generar_con_agy` levanta `ImagenNoGenerada`. `test_generar_devuelve_el_destino`: el doble escribe un PNG válido en `destino` → devuelve `destino`.
- [ ] **Step 4: Correr** `uv run pytest tests/test_analista_generador_imagen.py -q` → FAIL.
- [ ] **Step 5: Implementar** la vía elegida. Verifica que el archivo exista y empiece con la firma PNG o JPEG; si no, levanta.
- [ ] **Step 6: Correr** el test → PASS.
- [ ] **Step 7: Commit** `feat(analista): generador de imágenes ilustrativas medido`.

### Task 2 [agy]: Catálogo de motivos y banco de imágenes

**Files:**
- Create: `config/motivos_imagen.json`, `scripts/analista/ilustracion.py`
- Modify: `.gitignore` (agrega `data/imagenes_ilustrativas/`)
- Test: `tests/test_analista_ilustracion.py`

**Interfaces:**
- Consumes: `Generador`, `ImagenNoGenerada` (Task 1).
- Produces:
  - `config/motivos_imagen.json`: `{"_nota": str, "prohibiciones": str, "motivos": {<id>: {"descripcion": str, "prompt": str}}}` con los ids `oro_lingotes`, `banco_central`, `billetes_dolar`, `peso_chileno`, `cobre`, `petroleo`, `bolsa_pantallas`, `tecnologia`, `acciones_generico`. `prohibiciones` es el texto exacto de Global Constraints.
  - `BANCO = RAIZ / "data" / "imagenes_ilustrativas"`; `USO = BANCO / "uso.json"` (`{"<motivo>/<archivo>": "AAAA-MM-DD"}`).
  - `motivos() -> dict[str, dict[str, str]]`
  - `prompt_de(motivo: str) -> str`: prompt del motivo + `prohibiciones`; `KeyError` si el motivo no está.
  - `elegir(motivo: str, hoy: date, generar: Generador | None, banco: Path = BANCO) -> tuple[Path | None, str | None]`: devuelve `(ruta, aviso)`. Orden: imagen del motivo sin uso en los últimos 7 días → si no hay y `generar` existe, genera una nueva en `banco/<motivo>/<AAAAMMDD-HHMMSS>.png` → si la generación falla, la de uso más antiguo del motivo, con aviso → si no hay ninguna, `(None, aviso)`. Anota el uso en `USO` al devolver una ruta.

- [ ] **Step 1: Tests que fallan:**
  - `test_prompt_lleva_las_prohibiciones`: `"sin logos" in prompt_de("oro_lingotes")`.
  - `test_motivo_desconocido_levanta`: `pytest.raises(KeyError)` con `prompt_de("bandera_chile")`.
  - `test_elige_una_sin_uso_reciente`: banco en `tmp_path` con `a.png` usada hace 2 días y `b.png` hace 9 → devuelve `b.png`, aviso `None`, y `uso.json` queda con `b.png` en `hoy`.
  - `test_genera_si_todas_estan_en_cooldown`: las dos usadas hace 1 día, `generar` doble que escribe un PNG → devuelve la nueva.
  - `test_si_falla_la_generacion_usa_la_mas_antigua`: `generar` levanta `ImagenNoGenerada` → devuelve la de uso más antiguo y un aviso no vacío.
  - `test_sin_banco_ni_generador_devuelve_none`: banco vacío, `generar=None` → `(None, aviso)`.
- [ ] **Step 2: Correr** `uv run pytest tests/test_analista_ilustracion.py -q` → FAIL.
- [ ] **Step 3: Implementar** `ilustracion.py` y el JSON. Escritura de `uso.json` con `Path.write_text(..., encoding="utf-8")`.
- [ ] **Step 4: Correr** → PASS. `uv run ruff check scripts/analista/ilustracion.py`.
- [ ] **Step 5 [Claude]: Revisar el diff y correr de nuevo** `agy_encargo.py verificar`; mirar los nueve prompts (que ninguno pida marca, bandera ni texto).
- [ ] **Step 6: Commit** `feat(analista): catálogo de motivos y banco de imágenes ilustrativas`.

### Task 3 [Claude]: La noticia en el esquema y su depuración

**Files:**
- Create: `scripts/analista/noticia.py`
- Modify: `scripts/analista/esquema.py` (`CAMPOS["oportunidad"]`, `textos`, `errores`)
- Test: `tests/test_analista_noticia.py`, `tests/test_analista_esquema.py`

**Interfaces:**
- Consumes: `fuentes.verificar_url`, `fuentes._host`, `fuentes._dominios_de`, `fuentes._con_ruta_de_articulo`, `fuentes.cargar_lista`; `esquema._errores_de_texto`, `_NUMERO`, `_plano_numero`, `_significativo`, `MARCA`; `ilustracion.motivos()` (Task 2).
- Produces:
  - `esquema.CAMPOS["oportunidad"] == ("titular", "bajada", "fuentes", "noticia")`. `esquema.textos()` **omite** `noticia`. `esquema.errores()` acepta `editorial["noticia"]` igual a `None`, `MARCA` o un dict con `noticia.CAMPOS`; cualquier otra forma es error.
  - `noticia.CAMPOS = ("medio", "fecha", "url", "titular_original", "extracto", "titular", "bajada", "motivo")`
  - `noticia.VENTANA_DIAS = 3`; `noticia.LARGOS = {"titular": 90, "bajada": 200}`
  - `noticia.leer_texto(url: str, timeout: int = 10) -> str | None`: descarga la página y devuelve el texto visible (sin etiquetas); `None` si no responde.
  - `noticia.depurar_noticia(pieza: dict, hoy: date, verificar: Callable[[str], str] = fu.verificar_url, leer: Callable[[str], str | None] = leer_texto) -> tuple[dict, list[str]]`: deja `editorial["noticia"]` válido o en `None`, y devuelve los motivos de descarte (uno por noticia caída, empezando con `"Noticia de apertura: "`).
  - `noticia.vigente(n: dict, hoy: date) -> bool` (fecha dentro de la ventana).

- [ ] **Step 1: Tests que fallan** (`tests/test_analista_noticia.py`, con `verificar` y `leer` dobles):
  - `test_noticia_valida_pasa`: Reuters, fecha = hoy − 1, `verificar → "ok"`, la página trae `"4,100.50"` y el titular dice "4.100,50" → la noticia queda y `descartes == []`.
  - `test_cifra_ausente_de_la_pagina_descarta`: el titular dice "4.200" y la página no → `editorial["noticia"] is None` y el motivo nombra `4.200`.
  - `test_cifra_en_otro_formato_descarta` (Review Focus 1): página con `"$20.06B"`, bajada con "20.060 millones" → descartada.
  - `test_muro_de_pago_sin_cifras_pasa`: `verificar → "sin_verificar"`, titular sin cifras → queda.
  - `test_muro_de_pago_con_cifras_descarta`: `verificar → "sin_verificar"`, titular con "4.100" → descartada.
  - `test_url_muerta_descarta`, `test_medio_fuera_de_lista_descarta`, `test_dominio_distinto_del_medio_descarta`.
  - `test_fecha_vieja_descarta`: hoy − 4 → descartada.
  - `test_fecha_futura_o_malformada_descarta` (Review Focus 4): `"2026-13-01"`, `"ayer"` y hoy + 1, cada una descartada.
  - `test_porcentaje_permitido_si_esta_en_la_fuente`: "cae 3,67 %" con la página "-3.67%" → queda.
  - `test_guion_largo_descarta` y `test_invitacion_a_operar_descarta` ("conviene comprar").
  - `test_titular_largo_descarta`: 91 caracteres.
  - `test_motivo_fuera_de_catalogo_descarta`.
  - `test_sin_escribir_o_nula_no_es_error` (Review Focus 2): `MARCA`, `None` y `{}` → `editorial["noticia"] is None`, sin descartes para `MARCA`/`None`.
  - En `tests/test_analista_esquema.py`: `test_errores_acepta_noticia_nula_o_valida` y `test_errores_rechaza_noticia_con_forma_rara` (una lista).
- [ ] **Step 2: Correr** `uv run pytest tests/test_analista_noticia.py tests/test_analista_esquema.py -q` → FAIL.
- [ ] **Step 3: Implementar.** Los controles de texto reutilizan `es._errores_de_texto(donde, texto, "oportunidad", None)` filtrando los mensajes de `%` y de cifra: un solo freno, no dos copias. Cifras: `{_plano_numero(t) for t in _NUMERO.findall(texto_pagina) }` contra las significativas de titular + bajada.
- [ ] **Step 4: Correr** los tests → PASS. Correr también `uv run pytest tests/test_analista_*.py -q` (la única falla esperada es la previa `test_seguimiento_mide_la_simulacion_y_entrega_el_suceso`).
- [ ] **Step 5: Commit** `feat(analista): noticia de apertura en el esquema, con su depuración`.

### Task 4 [Claude]: El dato de tasas, sellado al preparar

**Files:**
- Create: `config/tasa_por_activo.json`, `scripts/analista/tasa_banco.py`
- Modify: `scripts/analista/preparar.py` (`preparar_oportunidad`: sella `datos["tasa"]`)
- Test: `tests/test_analista_tasa_banco.py`, `tests/test_analista_preparar.py`

**Interfaces:**
- Produces:
  - `config/tasa_por_activo.json`: `{"bancos": {"fed": {"nombre": "Reserva Federal (Fed)", "archivo": "data central/DATA USA/raw/treasury_fed_data.json", "ruta": ["curva_rendimientos_yields", "DFF"], "serie": "Tasa efectiva de fondos federales", "linea": str}, "bcch": {... ["series","TPM"], "serie": "Tasa de Política Monetaria (TPM)"}, "bce": {... ["series","BCE_DFR"], "serie": "Tasa de depósito del BCE"}}, "por_ticker": {"USDCLP": "bcch", "COPPER": "bcch", "EURUSD": "bce", "GER40.spot": "bce"}, "por_clase": {"indices": "fed", "acciones": "fed", "etfs": "fed", "crypto": "fed", "forex_commodities": "fed"}}`. `linea` es la frase pedagógica fija por banco (Fed: "Una tasa alta en EE.UU. hace más atractivo el dólar frente al oro y las acciones.", BCCh: "Una TPM más baja que la de la Fed suele empujar el dólar al alza frente al peso.", BCE: "Una tasa del BCE más alta sostiene al euro frente al dólar."). Revisar con el director antes del merge.
  - `tasa_banco.leer(ticker: str, clase: str, hoy: date) -> tuple[dict | None, str | None]`: devuelve `({"banco": "fed", "nombre": ..., "serie": ..., "valor": "3,88", "fecha": "23/10", "linea": ..., "motivo_imagen": "banco_central"}, None)` o `(None, aviso)`. El valor es el último del `historico` con 2 decimales y coma decimal; la frescura se juzga con `market_data_mcp.frescura` sobre el `as_of` del archivo.
  - `datos["tasa"]` (sellado): ese dict o `None`.

- [ ] **Step 1: Tests que fallan:** `test_oro_lee_la_fed`, `test_usdclp_lee_el_bcch`, `test_activo_sin_banco_devuelve_none` (clase no mapeada), `test_archivo_vencido_devuelve_aviso` (con un `as_of` viejo en `tmp_path`), `test_valor_con_coma_y_dos_decimales`; en `test_analista_preparar.py`, `test_oportunidad_sella_la_tasa` (con el lector reemplazado vía `Lectores`).
- [ ] **Step 2: Correr** → FAIL.
- [ ] **Step 3: Implementar.** `preparar_oportunidad` agrega un lector `tasa` a `Lectores` (mismo patrón que `_agenda`/`_curva`) y su aviso a `Preparada.avisos`.
- [ ] **Step 4: Correr** → PASS.
- [ ] **Step 5: Commit** `feat(analista): dato de tasas del banco del activo`.

### Task 5 [Claude]: Integración en el bot

**Files:**
- Modify: `scripts/analista/bot.py` (`_redactar_y_validar`, `_oportunidad`, `Bot` con un campo `generar_imagen`)
- Test: `tests/test_analista_bot.py`

**Interfaces:**
- Consumes: `noticia.depurar_noticia` (Task 3), `ilustracion.elegir` (Task 2), `generador_imagen` (Task 1).
- Produces: `pieza["ilustraciones"] = {"noticia": "<archivo>", "tasa": "<archivo>"}`, con los archivos copiados a `dir_pedido` (cada clave presente solo si hay imagen). Esa clave **no** entra en `_huella`. Avisos nuevos al ejecutivo: el motivo de la noticia descartada y "La noticia salió sin imagen…".

- [ ] **Step 1: Tests que fallan:**
  - `test_noticia_rota_no_bota_la_pieza`: agy doble que escribe una noticia con cifra ausente → la respuesta trae el HTML y un aviso que empieza con "Noticia de apertura".
  - `test_ilustraciones_se_eligen_una_vez`: una pieza nueva con noticia y tasa → `pieza.json` trae `ilustraciones.noticia` y `ilustraciones.tasa`, y los archivos existen en `dir_pedido`.
  - `test_reuso_no_genera_imagenes`: segunda petición del mismo activo por otro ejecutivo → el generador doble no se llama.
  - `test_sin_imagen_avisa` (Review Focus 5): banco vacío y generador que levanta → la pieza sale y el aviso dice que va sin imagen.
- [ ] **Step 2: Correr** `uv run pytest tests/test_analista_bot.py -q` → FAIL.
- [ ] **Step 3: Implementar.** `depurar_noticia` va justo después de `fu.depurar_pieza` en `_redactar_y_validar`, y sus descartes se suman a los demás. La elección de imágenes va en `_oportunidad` después de `_con_fuente_directa` y antes de `rg.anotar`, solo en la rama sin reúso.
- [ ] **Step 4: Correr** → PASS, más `tests/test_analista_*.py`.
- [ ] **Step 5: Commit** `feat(analista): el bot depura la noticia y elige las imágenes`.

### Task 6 [agy, revisión de Claude]: La maqueta del correo

**Files:**
- Modify: `scripts/analista/oportunidad_html.py` (`_bloque_correo`, `_hero_activo`, `_marco_correo`, `armar`, `asunto_sugerido`/`preheader_sugerido` de cara a la noticia)
- Test: `tests/test_analista_oportunidad_html.py`

**Interfaces:**
- Consumes: `editorial["noticia"]` (Task 3), `datos["tasa"]` (Task 4), `pieza["ilustraciones"]` (Task 5), `noticia.vigente` (Task 3).
- Produces (funciones nuevas en `oportunidad_html.py`):
  - `_apertura_noticia(n: dict, a: dict, imagen: Path | None, hoy: date, c: dict) -> str`: fondo oscuro de marca con logo; imagen a 558 px de ancho con el rótulo `Imagen ilustrativa`; kicker `MERCADO HOY · {NOMBRE} ({TICKER_VISIBLE})`; `<h1 data-ed="titular">` con `n["titular"]`; bajada; línea de fuente `Fuente: {medio} · {fecha en palabras} →` con enlace a `n["url"]`. Si `not noticia.vigente(n, hoy)`, la línea empieza con `Noticia del {día de la semana} {d} de {mes}`.
  - `_tasa_correo(t: dict, imagen: Path | None, c: dict) -> str`: rótulo `{nombre del banco}`, `{serie}: {valor} por ciento al {fecha}`, la `linea` y la imagen con su rótulo.
  - `_analisis_tecnico_correo(a, ..., autor, c) -> str`: rótulo del análisis, snapshot de 4 cifras (sale de `_hero_activo`), gráfico de la lectura, tres escenarios, temporalidad y al pie `Realizado por {nombre} · {cargo} GI`.
  - Orden en `_bloque_correo`: apertura (noticia; sin noticia, `_tasa_correo` va en la apertura oscura) → tasa → continuidad, contexto, hechos, dólar, días clave, noticia directa (omitida si su `url` es la de la noticia), voces → análisis técnico → simulación → cierre consultivo.
  - Asunto, preheader y `editable_activos[t]["titular"]`: con noticia, `n["titular"]` y `n["bajada"]`; sin ella, lo de hoy.
  - Las imágenes de `ilustraciones` entran en `rutas` de `_enlazar_imagenes`.

- [ ] **Step 1: Tests que fallan:**
  - `test_correo_abre_con_la_noticia`: el índice de `n["titular"]` en el HTML es menor que el de la tasa, y este menor que el de `Los tres escenarios`, y este menor que el de `Simulación realizada por`.
  - `test_firma_al_pie_del_analisis`: `Realizado por Benjamín Bravo Soza · Departamento de Estudios GI` aparece después de `Los tres escenarios` y antes de `Simulación realizada por`.
  - `test_rotulo_imagen_ilustrativa`: aparece una vez por imagen presente.
  - `test_noticia_vencida_dice_su_fecha`: `hoy` = fecha + 5 → la línea trae `Noticia del`.
  - `test_directa_repetida_no_se_duplica`: misma URL en `fuentes` y en `noticia` → la URL aparece una sola vez.
  - `test_asunto_sigue_a_la_noticia` y `test_asunto_sin_noticia_es_el_de_hoy`.
  - `test_pieza_vieja_se_arma` (Review Focus 3): pieza del fixture actual sin `noticia`, `tasa` ni `ilustraciones` → `armar` no levanta y el HTML trae `Los tres escenarios`.
  - `test_tasa_con_nombre_real`: el HTML trae `Tasa efectiva de fondos federales` y no `tasa de la Fed`.
  - `test_correo_sin_var_ni_rgba` sobre el `<template class="correo-activo">`.
- [ ] **Step 2: Correr** `uv run pytest tests/test_analista_oportunidad_html.py -q` → FAIL.
- [ ] **Step 3: Implementar** con las firmas de arriba.
- [ ] **Step 4: Correr** → PASS, más `tests/test_analista_*.py`.
- [ ] **Step 5 [Claude]: Revisar.** Diff completo; armar el HTML con un fixture y mirarlo renderizado (Playwright, captura a 600 px y a 375 px), en claro y oscuro; buscar `—` y `–` en el texto de cliente.
- [ ] **Step 6: Commit** `feat(analista): el correo abre con la noticia y cierra con el análisis firmado`.

### Task 7 [Claude]: Reglas, encargo de agy y documentación

**Files:**
- Modify: `CLAUDE.md` (Regla 0 y Regla 1 en GUARDRAILS, sección Stories), `docs/gobernanza_guias_educativas_captacion.md`, `.claude/commands/analista.md`, `docs/bot-analistas.md`
- Regenerar: `.agents/rules/proyecto.md` (`uv run python scripts/agy_reglas.py`), workflows (`uv run python scripts/agy_workflows.py`)

- [ ] **Step 1:** En `CLAUDE.md`, a la Regla 0 y a la Regla 1, una excepción de una línea cada una, acotada a "la noticia de apertura del correo de `/oportunidad`" y remitiendo al spec. Lo mismo en la gobernanza.
- [ ] **Step 2:** En `analista.md`, documentar `editorial.noticia`: sus campos (`noticia.CAMPOS`), la preferencia por notas en español, la ventana de 3 días, copiar las cifras **tal como aparecen en la fuente**, sin cifras si la nota tiene muro de pago, `motivo` de `config/motivos_imagen.json`, y `null` si no hay noticia. Agregar `ilustraciones` a la lista de claves que no se tocan.
- [ ] **Step 3:** En `docs/bot-analistas.md`, el orden nuevo del correo y los avisos nuevos.
- [ ] **Step 4: Regenerar y verificar** `uv run python scripts/agy_reglas.py`, `uv run python scripts/agy_workflows.py --check` y la suite completa `uv run pytest -q` (la única falla esperada es la previa).
- [ ] **Step 5: Commit** `docs: excepciones de imagen y cifras para la noticia de apertura`.

### Task 8 [Claude, con el director]: Prueba real

- [ ] **Step 1:** Con el director, un `/oportunidad oro` forzado. Gasta agy y unos 10 minutos.
- [ ] **Step 2:** Abrir el HTML y el correo. Revisar: la noticia (vigente, medio de la lista, cifras), la imagen (sin marca ni texto), la tasa, la firma al pie y la simulación. Mirar `agy_salida_1.json` para ver qué buscó.
- [ ] **Step 3:** Ajustes de texto o de prompts que pida el director, con su commit; luego PR a `master`.
