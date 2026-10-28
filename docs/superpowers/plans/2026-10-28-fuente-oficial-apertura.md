# Fuente oficial como escalón 0 de la noticia de apertura: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que el correo de `/oportunidad` y el seguimiento abran con lo último que publicó la fuente oficial del activo (45 días, fecha a la vista) y, si no hay nada, lleven el enlace a su página de prensa.

**Architecture:** un módulo `scripts/analista/oficial.py` resuelve la fuente de cada activo (acciones por su `ancla.cik`, el resto por `noticia_oficial.FUENTES`) y entrega candidatas con `escalon: "oficial"`; `apertura.candidatas` las prueba antes que FXStreet/Investing. Las candidatas viajan por el camino normal de validación, que gana una ventana por escalón. El piso (enlace) viaja aparte en `datos.fuente_oficial`.

**Tech Stack:** Python 3, pytest (`uv run pytest`), `xml.etree`, `urllib` (vía `noticia_oficial.descargar`), sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-10-28-fuente-oficial-apertura-design.md`

## Desviaciones de la spec (se corrigen en la Task 1)

- No se crea `config/fuentes_oficiales.json`: la fuente de una acción sale de `ancla.cik` y `ancla.sitio_ir` de `config/activos.json` (ya existen para GS y BAC), y la de divisas y materias primas de `noticia_oficial.FUENTES`, al que se le agrega `pagina_prensa`. Una sola fuente de verdad.
- La línea de §5 "el motivo 'Hoy no encontré noticias…' solo sale si…" queda sin efecto: manda la decisión 2 (el piso no cuenta como noticia y el motivo sale igual).
- Los titulares de los feeds oficiales vienen en inglés: los traduce agy como en el escalón 1. Solo el 8-K trae `titular_es` armado por Python.

## Global Constraints

- Ventana del escalón 0: **45 días** (`VENTANA_OFICIAL_DIAS = 45`); el resto de los escalones conserva `VENTANA_DIAS = 3`.
- Rótulo del escalón 0: "Lo último que publicó <organismo>" con la fecha a la vista; nunca la palabra "noticia".
- Regla 1: ninguna cifra la escribe agy; el titular de un 8-K lo arma Python desde el ítem.
- Un fallo de una fuente oficial (red, 403, XML roto, falta de contacto) es un **aviso** y se continúa con los escalones siguientes; nunca excepción hacia arriba.
- EDGAR exige `User-Agent` con contacto: variable `GI_EDGAR_CONTACTO`; sin ella el lector avisa y no consulta.
- Prioridad de ítems del 8-K: `2.02`, `5.02`, `1.01`, `2.01`, `7.01`, `8.01`. Se omiten los 8-K cuyos ítems no estén en esa lista (incluye solo `9.01`, `3.03`, `5.03`).
- Los tests nunca tocan la red: todo lector recibe `descargar` inyectable.
- No se toca el despacho, el sender ni los canales de WhatsApp (`noticia_oficial.noticia_para_canal` conserva su ventana de 72 h).
- Texto de cliente: sin guion largo `—` ni `–`, tuteo chileno neutro.

## Review Focus

1. Un 8-K con varios ítems (`2.02` + `9.01`) usa `2.02`; uno con solo `9.01` no genera candidata.
2. EDGAR devuelve 403, HTML en vez de XML, un feed vacío o no hay `GI_EDGAR_CONTACTO`: aviso, lista vacía, el correo sigue con los escalones de hoy.
3. Una `<entry>` con fecha mal formada o futura se ignora sin romper las demás.
4. Borde de ventana: un comunicado de 45 días exactos entra y uno de 46 no.
5. Tickers con sufijo o prefijo (`WTI.spot`, `#GS`) resuelven su fuente; un activo sin fuente (BTC, cobre) queda idéntico a hoy y sin piso.
6. Una pieza guardada con un comunicado oficial de más de 3 días se rinde con la fecha en palabras y sin "hoy" ni "noticia".

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `scripts/analista/oficial.py` (nuevo) | `fuente_de`, `piso`, `candidatas`, ventana; resuelve la fuente por ticker y delega en `edgar` o en los feeds |
| `scripts/analista/edgar.py` (nuevo) | contacto, parseo del Atom de 8-K, tabla de ítems, `candidatas_8k` |
| `scripts/noticia_oficial.py` | `_FUENTES_BASE` gana `pagina_prensa` |
| `scripts/analista/noticia.py` | `_motivo` y `motivo_de_contexto` aceptan `ventana_dias`; `depurar_noticia` la elige por escalón |
| `scripts/analista/apertura.py` | escalón 0 en `candidatas` |
| `scripts/analista/preparar.py` | sella `datos.fuente_oficial` en la oportunidad |
| `scripts/analista/contexto.py` | candidatas por escalones, `datos.fuente_oficial`, ventana en `depurar` |
| `scripts/analista/oportunidad_html.py`, `mensajes_html.py` | rótulo, línea de fuente y línea del piso |
| `config/fuentes_prestigio.json` | medios `SEC EDGAR`, `EIA`, `BCE`, `Fed` (los que falten) |
| `tests/test_analista_oficial.py`, `tests/test_analista_edgar.py` (nuevos) y los de apertura, noticia, contexto, preparar | |

---

### Task 1: Resolver la fuente oficial de cada activo

**Files:**
- Create: `scripts/analista/oficial.py`
- Modify: `scripts/noticia_oficial.py` (`_FUENTES_BASE`: agregar `pagina_prensa`)
- Modify: `docs/superpowers/specs/2026-10-28-fuente-oficial-apertura-design.md` (aplicar las tres desviaciones)
- Test: `tests/test_analista_oficial.py`

**Interfaces:**
- Produces: `VENTANA_OFICIAL_DIAS: int = 45`; `fuente_de(ticker: str) -> dict[str, Any] | None` con claves `organismo: str`, `pagina_prensa: str`, `lector: Literal["edgar_8k", "feed_oficial"]` y `cik: str` o `fuente: str` según el lector; `piso(ticker: str) -> dict[str, str] | None` con `{"organismo", "pagina_prensa"}`.
- `pagina_prensa` de los feeds: EIA `https://www.eia.gov/todayinenergy/`, BCE `https://www.ecb.europa.eu/press/pr/html/index.en.html`, Fed `https://www.federalreserve.gov/newsevents/pressreleases.htm`.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_oficial.py`:
  - `test_accion_resuelve_por_su_ancla`: `fuente_de("#GS")` == `{"organismo": "Goldman Sachs", "pagina_prensa": "https://www.goldmansachs.com/investor-relations/", "lector": "edgar_8k", "cik": "0000886982"}`.
  - `test_feed_oficial_por_activo_con_sufijo`: `fuente_de("WTI.spot")["lector"] == "feed_oficial"` y `["fuente"] == "eia"`; `fuente_de("USDCLP")["fuente"] == "fed"`.
  - `test_activo_sin_fuente`: `fuente_de("BTCUSD") is None` y `piso("COPPER") is None`.
  - `test_piso_trae_organismo_y_enlace_https`: `piso("#GS")["pagina_prensa"].startswith("https://")`.
  - `test_toda_fuente_de_feeds_tiene_pagina_prensa`: para cada entrada de `noticia_oficial.FUENTES`, `pagina_prensa` empieza con `https://`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_oficial.py -q`. Expected: FAIL (`ModuleNotFoundError: analista.oficial`).
- [ ] **Step 3: Implement** `fuente_de` y `piso` en `scripts/analista/oficial.py`. La clave de un activo se normaliza quitando el sufijo `.spot` (los activos de `FUENTES` van sin él). Las acciones se resuelven con `segmentos.segmento_y_ancla(ticker)` y solo valen si el ancla trae `cik`; el `organismo` es `ancla["nombre"]` y la `pagina_prensa` es `ancla["sitio_ir"]`. Agregar `pagina_prensa` a las tres entradas de `_FUENTES_BASE`.
- [ ] **Step 4: Run** el mismo comando. Expected: PASS.
- [ ] **Step 5: Aplicar las tres desviaciones a la spec** (borrar la config nueva de §1, corregir la línea de §5 y la nota del titular del feed) y commit:

```bash
git add scripts/analista/oficial.py scripts/noticia_oficial.py tests/test_analista_oficial.py docs/superpowers/specs/2026-10-28-fuente-oficial-apertura-design.md
git commit -m "feat(oficial): resolver la fuente oficial de cada activo"
```

---

### Task 2: Lector EDGAR 8-K

**Files:**
- Create: `scripts/analista/edgar.py`, `tests/fixtures/edgar_gs_8k.atom`
- Test: `tests/test_analista_edgar.py`

**Interfaces:**
- Consumes: `noticia_oficial.descargar(url, timeout) -> str`.
- Produces: `ENV_CONTACTO = "GI_EDGAR_CONTACTO"`; `ITEMS: dict[str, str]` (ítem → titular en español: `2.02` "Resultados del trimestre", `5.02` "Cambios en la directiva", `1.01` "Acuerdo relevante", `2.01` "Compra o venta de activos", `7.01` y `8.01` "Aviso de la empresa"); `parsear_8k(xml: str) -> list[dict]` con `fecha: datetime` (con zona), `url: str`, `items: list[str]`; `titular_de(items: list[str]) -> str | None`; `candidatas_8k(cik: str, organismo: str, ahora: datetime, descargar: Callable[[str], str] | None = None, ventana_dias: int = 45) -> tuple[list[dict], str | None]` (`edgar.py` no importa `oficial.py`; la Task 3 le pasa `VENTANA_OFICIAL_DIAS`). Cada candidata: `{"medio": "SEC EDGAR", "fecha": "AAAA-MM-DD", "url", "titular_original": <titular_es>, "titular_es": <titular_es>, "escalon": "oficial", "organismo": organismo}`.

- [ ] **Step 1: Capturar el fixture** con `curl` al feed `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000886982&type=8-K&owner=include&count=10&output=atom` usando como `User-Agent` el contacto de `GI_EDGAR_CONTACTO` (si no está definida, pedírsela al director; no inventarla). Guardarlo en `tests/fixtures/edgar_gs_8k.atom`.
- [ ] **Step 2: Write the failing tests** en `tests/test_analista_edgar.py`, con el fixture y `descargar` falso:
  - `test_parsear_extrae_fecha_url_e_items`: la primera entrada del fixture da `items` que incluye `"2.02"`.
  - `test_titular_usa_el_item_de_mayor_prioridad`: `titular_de(["9.01", "2.02"]) == "Resultados del trimestre"`; `titular_de(["8.01", "5.02"]) == "Cambios en la directiva"`.
  - `test_8k_sin_items_publicables_no_genera_candidata`: `titular_de(["9.01"]) is None`, `titular_de(["3.03", "5.03"]) is None`.
  - `test_candidatas_dentro_de_45_dias`: con `ahora` 2026-10-28 y el fixture, la candidata del 13-10 sale con `escalon == "oficial"` y `fecha == "2026-10-13"`; con `ahora` 2026-12-30 la lista es vacía.
  - `test_borde_de_ventana`: un 8-K a exactamente 45 días entra y a 46 no (entrada sintética).
  - `test_sin_contacto_avisa_y_no_consulta`: sin `GI_EDGAR_CONTACTO` devuelve `([], aviso)` y `descargar` no se llama.
  - `test_feed_roto_no_lanza`: `descargar` devuelve `"<html>403</html>"` y también lanza `OSError`: ambos dan `([], aviso)`.
  - `test_entry_con_fecha_mala_se_ignora`: una entrada con `<updated>` ilegible no tumba a las demás.
  - `test_user_agent_lleva_el_contacto`: el `descargar` real se arma con un `User-Agent` que contiene el contacto (probar la función que construye el pedido).
- [ ] **Step 3: Run** `uv run pytest tests/test_analista_edgar.py -q`. Expected: FAIL.
- [ ] **Step 4: Implement** `edgar.py`. El ítem sale del `<summary>` (viene escapado: `Item 2.02: …`), la URL del `<link rel="alternate">` y la fecha de `<updated>`. El feed se pide con `count=10`. El contacto se lee con `os.environ` (si el repo ya tiene un cargador de `.env` para el bot, usar ese). La ventana es el parámetro `ventana_dias`.
- [ ] **Step 5: Run** el mismo comando. Expected: PASS. Commit:

```bash
git add scripts/analista/edgar.py tests/test_analista_edgar.py tests/fixtures/edgar_gs_8k.atom
git commit -m "feat(oficial): lector de avisos 8-K de EDGAR"
```

---

### Task 3: Lector de feeds oficiales (bancos centrales y EIA)

**Files:**
- Modify: `scripts/analista/oficial.py`
- Test: `tests/test_analista_oficial.py`

**Interfaces:**
- Consumes: `noticia_oficial.parsear_feed`, `noticia_oficial.FUENTES`, `noticia_oficial.activos_del_titular(titulo) -> list[str]`, `noticia_oficial.es_fresca(fecha, ahora, horas)`, `edgar.candidatas_8k`, `fuente_de`.
- Produces: `candidatas(ticker: str, ahora: datetime, descargar: Callable[[str], str] | None = None) -> tuple[list[dict], str | None]`: despacha según `fuente_de(ticker)["lector"]`. Candidata de feed: `{"medio": <"EIA"|"BCE"|"Fed">, "fecha", "url", "titular_original": <titular en inglés>, "escalon": "oficial", "organismo"}`.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_oficial.py` con un RSS de juguete:
  - `test_feed_oficial_filtra_por_relevancia_del_titular`: un ítem cuyo titular nombra petróleo entra para `WTI.spot` y uno de sanciones bancarias no.
  - `test_feed_oficial_usa_45_dias`: un ítem de 30 días entra; uno de 50 no.
  - `test_candidatas_despacha_a_edgar_para_acciones`: con `#GS` y un `descargar` que sirve el fixture, sale la candidata de EDGAR.
  - `test_activo_sin_fuente_devuelve_vacio_sin_aviso`: `candidatas("BTCUSD", ahora) == ([], None)`.
  - `test_feed_caido_da_aviso`: `descargar` lanza `OSError` y se devuelve `([], aviso)` sin excepción.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_oficial.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** `candidatas` en `oficial.py`. Para feeds, la relevancia es `clave_del_activo in activos_del_titular(titulo)` (decisión del titular, no del cuerpo) y la frescura `es_fresca(fecha, ahora, VENTANA_OFICIAL_DIAS * 24)`. Cada fuente se descarga con `descargar_con_cache` para no repetir el feed de la Fed.
- [ ] **Step 4: Run** el mismo comando. Expected: PASS. Commit:

```bash
git add scripts/analista/oficial.py tests/test_analista_oficial.py
git commit -m "feat(oficial): candidatas de feeds oficiales con ventana de 45 dias"
```

---

### Task 4: La validación acepta la ventana del escalón 0

**Files:**
- Modify: `scripts/analista/noticia.py` (`vigente`, `_motivo`, `motivo_de_contexto`, `depurar_noticia`)
- Modify: `config/fuentes_prestigio.json` (agregar a `medios` los que falten: `SEC EDGAR` → `["sec.gov"]`, `EIA` → `["eia.gov"]`, `BCE` → `["ecb.europa.eu"]`, `Fed` → `["federalreserve.gov"]`)
- Test: `tests/test_analista_noticia.py`

**Interfaces:**
- Produces: `vigente(n, hoy, ventana_dias: int = VENTANA_DIAS) -> bool`; `_motivo(..., ventana_dias: int = VENTANA_DIAS)` y `motivo_de_contexto(..., ventana_dias: int = VENTANA_DIAS)` con el mismo parámetro; `ventana_de(candidata: dict | None) -> int` que devuelve `VENTANA_OFICIAL_DIAS` si `candidata["escalon"] == "oficial"` y `VENTANA_DIAS` en otro caso. `depurar_noticia` busca la candidata por URL en `pieza["datos"]["noticias_candidatas"]` y pasa su ventana.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_noticia.py`:
  - `test_noticia_oficial_de_20_dias_pasa_la_ventana`: una noticia de `medio: "SEC EDGAR"` fechada 20 días antes, con candidata `escalon: "oficial"` en la pieza, no cae por "fuera de la ventana".
  - `test_noticia_comun_de_20_dias_sigue_cayendo`: la misma fecha con candidata de FXStreet cae con el motivo actual.
  - `test_url_de_8k_no_es_portada`: una URL `https://www.sec.gov/Archives/edgar/data/886982/000088698226000529/0000886982-26-000529-index.htm` pasa `fu._con_ruta_de_articulo` y `fu._del_dominio` con la lista real.
  - `test_medios_oficiales_estan_en_la_lista`: `fu.cargar_lista()["medios"]` contiene `SEC EDGAR`, `EIA`, `BCE` y `Fed`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_noticia.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** el parámetro `ventana_dias` y `ventana_de`; el mensaje de rechazo usa la ventana efectiva. Agregar los medios a `config/fuentes_prestigio.json` sin tocar `cuentan_como_banco`.
- [ ] **Step 4: Run** el archivo completo `tests/test_analista_noticia.py` y `tests/test_analista_contexto.py`. Expected: PASS (nada existente cambia de comportamiento). Commit:

```bash
git add scripts/analista/noticia.py config/fuentes_prestigio.json tests/test_analista_noticia.py
git commit -m "feat(oficial): la validacion acepta la ventana de 45 dias del escalon 0"
```

---

### Task 5: Escalón 0 en `apertura.candidatas`

**Files:**
- Modify: `scripts/analista/apertura.py` (docstring del módulo y `candidatas`)
- Test: `tests/test_analista_apertura.py`

**Interfaces:**
- Consumes: `oficial.candidatas(ticker, ahora, descargar=None) -> tuple[list[dict], str | None]`.
- Produces: `candidatas(ticker, nombre, ahora, leer=..., ruta_patrones=..., ruta_sectores=..., oficial_fn: Callable = oficial.candidatas) -> tuple[list[dict], str | None]` (el contrato `(lista, aviso)` no cambia). Si `oficial_fn` trae candidatas, devuelve esas (máx. `MAX_CANDIDATAS`) y no consulta FXStreet ni Investing. Si no, sigue como hoy y suma el aviso del escalón 0 al aviso final.

- [ ] **Step 1: Write the failing tests** en `tests/test_analista_apertura.py` (la suite ya inyecta feeds falsos):
  - `test_oficial_gana_sobre_los_demas_escalones`: con `oficial_fn` devolviendo una candidata `escalon: "oficial"` y feeds que también traen nota del activo, el resultado es solo la oficial.
  - `test_sin_oficial_cae_al_escalon_1`: `oficial_fn` devuelve `([], None)` y el resultado es idéntico al de hoy.
  - `test_aviso_del_escalon_0_se_conserva`: `oficial_fn` devuelve `([], "EDGAR no respondió")` y el aviso aparece en el retorno aunque el escalón 1 encuentre notas.
  - `test_oficial_que_lanza_no_rompe`: `oficial_fn` lanza `RuntimeError`; el resultado es el de hoy más un aviso.
  - `test_escalon_de_reconoce_oficial`: `escalon_de` de una noticia cuya URL está en `noticias_candidatas` con `escalon: "oficial"` devuelve `"oficial"`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_apertura.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** la llamada al escalón 0 al inicio de `candidatas`, envuelta en `try/except Exception` que la convierte en aviso. Actualizar el docstring del módulo (ahora son cuatro escalones: 0 oficial, 1 activo, 2 sector, 3 agenda).
- [ ] **Step 4: Run** el archivo y `tests/test_analista_preparar.py`. Expected: PASS. Commit:

```bash
git add scripts/analista/apertura.py tests/test_analista_apertura.py
git commit -m "feat(apertura): la fuente oficial es el escalon 0"
```

---

### Task 6: Piso en la oportunidad y en el seguimiento

**Files:**
- Modify: `scripts/analista/preparar.py` (`preparar_oportunidad`, cerca de la línea 481)
- Modify: `scripts/analista/contexto.py` (`preparar`, `depurar`)
- Test: `tests/test_analista_preparar.py`, `tests/test_analista_contexto.py`

**Interfaces:**
- Consumes: `oficial.piso(ticker)`, `apertura.candidatas`, `noticia.ventana_de`.
- Produces: `datos["fuente_oficial"]` (`{"organismo", "pagina_prensa"}` o ausente) en ambas piezas; `contexto.preparar` con el parámetro `candidatas` por defecto igual a un adaptador `_candidatas_por_escalones(ticker, nombre, ahora) -> tuple[list[dict], list[str]]` que llama `apertura.candidatas` y convierte el aviso `str | None` en lista. El parámetro sigue siendo inyectable.

- [ ] **Step 1: Write the failing tests:**
  - En `tests/test_analista_preparar.py`: `test_oportunidad_sella_el_piso_de_una_accion` (para `#GS`, `datos["fuente_oficial"]["pagina_prensa"]` es el `sitio_ir` del ancla) y `test_oportunidad_sin_fuente_no_lleva_piso` (BTC: la clave no está).
  - En `tests/test_analista_contexto.py`: `test_seguimiento_usa_los_escalones` (con `candidatas` inyectado devolviendo una oficial, `datos["noticias_candidatas"]` la trae), `test_seguimiento_sella_el_piso`, `test_depurar_acepta_oficial_de_20_dias` (noticia oficial de 20 días con su candidata pasa `depurar`), y `test_el_motivo_sin_noticias_sale_igual_con_piso` (con piso y sin candidatas, `motivos["noticia_1"] == "Hoy no encontré noticias de Goldman Sachs en FXStreet ni en Investing.com."`).
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_preparar.py tests/test_analista_contexto.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** el sello del piso y el adaptador; `depurar` calcula `ventana_de(cand)` y la pasa a `nt.motivo_de_contexto`. La aviso de EDGAR sin contacto se suma a los `avisos` de `Preparada`.
- [ ] **Step 4: Run** los dos archivos. Expected: PASS. Commit:

```bash
git add scripts/analista/preparar.py scripts/analista/contexto.py tests/test_analista_preparar.py tests/test_analista_contexto.py
git commit -m "feat(oficial): piso del enlace oficial y escalones en el seguimiento"
```

---

### Task 7: Rótulos y piso en el correo y en el seguimiento

**Files:**
- Modify: `scripts/analista/oportunidad_html.py` (`ROTULOS_APERTURA` ~línea 847, `_apertura_noticia`, y una función nueva `_piso_oficial`)
- Modify: `scripts/analista/mensajes_html.py` (la tarjeta de noticia y la línea del piso)
- Test: `tests/test_analista_oportunidad_html.py`, `tests/test_analista_mensajes_html.py`

**Interfaces:**
- Consumes: `datos["fuente_oficial"]`, `apt.escalon_de(n, datos)`.
- Produces: `ROTULOS_APERTURA["oficial"] = "LO ÚLTIMO QUE PUBLICÓ"`; `_piso_oficial(d: dict | None, c: dict[str, str]) -> str` que devuelve el HTML de una línea "Sitio oficial de <organismo>" con el enlace, o `""` si no hay piso o si la noticia elegida ya es `oficial`.

- [ ] **Step 1: Write the failing tests** (HTML como string, con las fixtures del módulo):
  - `test_kicker_oficial`: una noticia de escalón `oficial` rinde el kicker `LO ÚLTIMO QUE PUBLICÓ · GOLDMAN SACHS (GS)`.
  - `test_fuente_oficial_lleva_fecha_y_no_dice_noticia_ni_hoy`: el HTML contiene `Publicado el` con la fecha en palabras y no contiene `Noticia del` ni `hoy`, incluso con una fecha de hace 6 días y con una de hace 20.
  - `test_piso_aparece_sin_noticia_oficial`: sin noticia elegida de escalón `oficial` y con `fuente_oficial`, el HTML trae `Sitio oficial de Goldman Sachs` y el enlace a `pagina_prensa`.
  - `test_piso_no_se_repite_si_la_noticia_ya_es_oficial`.
  - `test_sin_fuente_oficial_el_html_es_identico_al_de_hoy` (comparación con el HTML rendido sin la clave).
  - Equivalentes en `mensajes_html` para el seguimiento: el piso aparece bajo las noticias y no ocupa `noticia_1` ni `noticia_2`.
- [ ] **Step 2: Run** `uv run pytest tests/test_analista_oportunidad_html.py tests/test_analista_mensajes_html.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** el rótulo, la línea de fuente para `oficial` (`Publicado el {fecha_en_palabras(con_dia=True)} · Fuente: {medio} →`, siempre con fecha, aunque sea vigente) y `_piso_oficial`. Sin guion largo en ningún texto nuevo.
- [ ] **Step 4: Run** los dos archivos. Expected: PASS. Commit:

```bash
git add scripts/analista/oportunidad_html.py scripts/analista/mensajes_html.py tests/test_analista_oportunidad_html.py tests/test_analista_mensajes_html.py
git commit -m "feat(oficial): rotulo, fecha y piso del enlace oficial en las piezas"
```

---

### Task 8: Verificación de punta a punta y documentación

**Files:**
- Modify: `docs/bot-analistas.md` (sección corta: cómo funciona el escalón 0, `GI_EDGAR_CONTACTO` y el piso)
- Test: la suite completa

**Interfaces:** ninguna nueva.

- [ ] **Step 1: Documentar** en `docs/bot-analistas.md` el escalón 0, la variable `GI_EDGAR_CONTACTO` (sin ella EDGAR no se consulta y se avisa), la ventana de 45 días y que el bot corre del checkout principal: tras mergear hay que traer master ahí y reiniciar con `-Reiniciar`.
- [ ] **Step 2: Correr la suite** `uv run pytest -q`. Expected: todo en verde; si falla algo ajeno a esta rama, compararlo con `master` antes de tocarlo.
- [ ] **Step 3: Prueba real con red**, una sola vez y sin enviar nada: con `GI_EDGAR_CONTACTO` definida, `uv run python -c "from datetime import datetime; from zoneinfo import ZoneInfo; from analista import oficial; print(oficial.candidatas('#GS', datetime.now(ZoneInfo('America/Santiago'))))"` desde `scripts/`. Expected: una candidata con `escalon: "oficial"` del 2026-10-13 (ítem 2.02) mientras no haya un 8-K más nuevo, o la lista vacía con aviso si falta el contacto.
- [ ] **Step 4: Commit**:

```bash
git add docs/bot-analistas.md
git commit -m "docs(oficial): escalon 0, contacto de EDGAR y reinicio del bot"
```
