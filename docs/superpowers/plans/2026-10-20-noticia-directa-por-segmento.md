# Noticia directa por segmento Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que toda `/oportunidad` salga con al menos una fuente directa del activo (o no salga), repartida en seis segmentos: fx, commodities, acciones, etfs, indices y cripto.

**Architecture:** Cada activo resuelve a un `(segmento, ancla)`. El ancla (entidades, dominios, `terminos_ancla`) viaja sellada en `datos.fuente_directa`. Python valida: `fuentes_directas` filtra por entidad o dominio del ancla Y por término del ancla en la `tesis` o en la URL; `falta_fuente_directa` reemplaza a `falta_banco`. La lista cerrada `fuentes_prestigio.json` se conserva; `segmentos_fuentes.json` la extiende por segmento.

**Tech Stack:** Python 3, pytest (`uv run pytest`), JSON de config, yfinance y SEC EDGAR (solo acciones).

**Spec:** `docs/superpowers/specs/2026-10-20-noticia-directa-por-segmento-design.md` (aprobado por el director el 2026-10-20).

## Global Constraints

- Regla 1: precios y cifras de MT5 o de la ingesta en tiempo de ejecución, nunca escritos a mano.
- Texto de cliente sin guion largo (`—`) ni medio (`–`); español chileno, sin voseo.
- Horas en hora Chile con `scripts\hora_chile.ps1`; eventos asiáticos con cruce de día.
- `.agents/workflows/analista.md` se regenera con `uv run python scripts/agy_workflows.py` y se verifica con `--check`; no se edita a mano. La fuente es `.claude/commands/analista.md`.
- Ramas `feat/...` y PR; nunca commit directo a master. Commits con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Los tests que fijan el comportamiento actual se actualizan, no se borran para pasar.
- Sin noticia directa la oportunidad no se publica, se avisa el motivo y no se gasta cupo.
- Frescura de 14 días en los seis segmentos. AUD, CAD, NZD, MXN y gas natural quedan fuera.
- La fecha de earnings de yfinance NO habilita sola una acción (P1). La voz de banco YA NO es requisito (P2).
- Un dominio que no responde (`scripts/verificar_dominios_fuentes.py`) no entra a la lista cerrada. Los dominios del spec marcados como suposición se verifican antes de cerrar cada segmento.
- Nunca editar los tests para forzar un pase ni parchar paquetes instalados.

## Review Focus

1. **Término del ancla dentro de otra palabra** ("CHF" en "CHFX", "oro" en "Cenicero", "NDX" suelto): no cuenta. Hay que respetar límites de palabra y tildes ("Suiza" = "suiza"). Test en Task 1.
2. **Nota del dominio del ancla que no nombra el ancla** (un medio suizo hablando de otra cosa; "Wall Street cae" para US100): no es directa. Test en Task 1 y Task 9.
3. **Pieza anterior sin `datos.fuente_directa`** (reuso o `--validar` de una vieja): no debe romper, se rearma como antes. Test en Task 3.
4. **Fuente directa que discrepa de nuestra lectura:** sigue siendo directa (la postura no la filtra) y aparece en el correo sin etiqueta de postura. Test en Task 1 y Task 4.
5. **Activo sin ancla** (símbolo del terminal que no es un par FX): no publica y no consume cupo. Test en Task 3.

---

## Reparto de la ejecución

Tasks 0 a 4 las hace Claude: son el contrato y de ellas depende todo. Tasks 5 a 10 (un segmento cada una) se delegan a agy en tier flash, una a la vez, con esta tarea como prompt. Tras cada entrega Claude corre la suite, mira el diff y corre el verificador de dominios, sin confiar en el "VERIFICADO" de agy. Task 11 la cierra Claude.

Estructura de archivos:

| Archivo | Responsabilidad |
|---|---|
| `config/segmentos_fuentes.json` (nuevo) | Por segmento: `entidades` y `medios` que extienden la lista cerrada; en `fx`, el mapa `divisas` |
| `scripts/analista/segmentos.py` (nuevo) | Resolver `(segmento, ancla)` de un ticker y armar las consultas |
| `scripts/analista/fuentes.py` | Lista del segmento, `fuentes_directas`, `falta_fuente_directa`, `directa_de` |
| `scripts/verificar_dominios_fuentes.py` (nuevo) | CLI de red que revisa cada dominio del config |
| `config/activos.json` | `segmento` y `ancla` por activo |

---

### Task 0: Rama y documento de diseño

**Files:**
- Commit: `docs/superpowers/specs/2026-10-20-noticia-directa-por-segmento-design.md`, este plan

- [ ] **Step 1:** `git switch -c feat/noticia-directa-por-segmento` desde master. No agregar los archivos de datos modificados (`data central/...`, `grafico.png`, `mql5/*.log`).
- [ ] **Step 2:** `git add` solo el spec y este plan; commit `docs: diseño y plan de noticia directa por segmento`.

---

### Task 1: Reglas de fuente directa en `fuentes.py`

**Files:**
- Modify: `scripts/analista/fuentes.py` (agregar tras `falta_banco`; borrar `falta_banco`)
- Test: `tests/test_analista_fuentes.py` (reemplazar `test_falta_banco_*`, líneas ~158-208)

**Interfaces:**
- Produces:
  - `SEGMENTOS = ("fx", "commodities", "acciones", "etfs", "indices", "cripto")`
  - `CONFIG_SEGMENTOS: Path` (`config/segmentos_fuentes.json`)
  - `lista_del_segmento(segmento: str, base: dict | None = None, segmentos: dict | None = None) -> dict`: misma forma que `cargar_lista()`; suma las `entidades` del segmento como grupo `segmento_<seg>` y une los `medios` (si un medio ya existe, une dominios). Segmento desconocido: `ValueError`.
  - `nombra_ancla(fuente: dict, ancla: dict) -> bool`: algún `terminos_ancla` aparece en `tesis` o en la ruta de la URL, sin tildes, sin mayúsculas, con límites de palabra.
  - `fuentes_directas(fuentes: Any, segmento: str, ancla: dict, lista: dict | None = None) -> list[dict]`: la fuente cuya `entidad` está en `ancla["entidades"]` o cuyo host está en `ancla["dominios"]`, Y `nombra_ancla`, Y su `entidad` está en la lista del segmento. No mira la postura.
  - `falta_fuente_directa(pieza: dict, segmento: str, ancla: dict, lista: dict | None = None) -> list[str]`: `[]` si hay una o si `editorial.fuentes` aún no es lista; si no, un error que nombra `ancla["nombre"]`, sus entidades y los días de frescura.
  - `directa_de(pieza: dict) -> tuple[str, dict] | None`: `(segmento, ancla)` desde `pieza["datos"]["fuente_directa"]`, o `None` si la pieza no lo trae.
- Conserva: `bancos`, `seleccionar_bancos_correo`, `discrepa` (el banco sigue sumando al correo).

- [ ] **Step 1: Write the failing tests**

```python
ANCLA_CHF = {"nombre": "Suiza", "entidades": ["Banco Nacional Suizo"], "dominios": ["snb.ch", "nzz.ch"],
             "terminos_ancla": ["Suiza", "franco suizo", "CHF", "SNB"]}
SEG = {"fx": {"entidades": ["Banco Nacional Suizo"], "medios": {"Banco Nacional Suizo": ["snb.ch"], "NZZ": ["nzz.ch"]}}}

def _f(entidad, url, tesis, medio="NZZ", postura="neutral", fecha="2026-10-19"):
    return {"entidad": entidad, "medio": medio, "fecha": fecha, "url": url, "postura": postura, "tesis": tesis}

def test_nota_del_snb_que_nombra_suiza_es_directa():
    f = _f("Banco Nacional Suizo", "https://www.snb.ch/es/noticia-1", "El SNB mantiene su tasa y vigila el franco suizo.", medio="Banco Nacional Suizo")
    assert fu.fuentes_directas([f], "fx", ANCLA_CHF, lista=fu.lista_del_segmento("fx", segmentos=SEG)) == [f]

def test_una_directa_que_discrepa_de_la_lectura_sigue_siendo_directa():
    f = _f("Banco Nacional Suizo", "https://www.snb.ch/a", "El SNB ve debilidad del franco suizo.", postura="bajista")
    assert fu.fuentes_directas([f], "fx", ANCLA_CHF, lista=fu.lista_del_segmento("fx", segmentos=SEG)) == [f]

def test_un_banco_de_inversion_o_el_dxy_no_cuentan_como_directa():
    jp = _f("JPMorgan", "https://www.reuters.com/x", "JPMorgan ve un dólar más fuerte por las tasas de la Fed.", medio="Reuters")
    assert fu.fuentes_directas([jp], "fx", ANCLA_CHF) == []

def test_el_dominio_del_ancla_sin_nombrar_el_ancla_no_cuenta():
    f = _f("UBS", "https://www.nzz.ch/otra-cosa", "UBS opina sobre el mercado inmobiliario alemán.")
    assert fu.fuentes_directas([f], "fx", ANCLA_CHF) == []

def test_el_termino_respeta_limites_de_palabra_y_tildes():
    ancla = {**ANCLA_CHF, "terminos_ancla": ["CHF", "Suiza"]}
    assert not fu.nombra_ancla(_f("UBS", "https://nzz.ch/a", "El CHFX sube"), ancla)
    assert fu.nombra_ancla(_f("UBS", "https://nzz.ch/a", "SUIZA sube"), ancla)

def test_falta_fuente_directa_lo_dice_y_calla_si_hay_una():
    sin = {"editorial": {"fuentes": []}}
    errs = fu.falta_fuente_directa(sin, "fx", ANCLA_CHF)
    assert errs and "Suiza" in errs[0] and "14 días" in errs[0]
    assert fu.falta_fuente_directa({"editorial": {"fuentes": "[[ESCRIBIR]]"}}, "fx", ANCLA_CHF) == []

def test_directa_de_lee_el_sello_y_calla_en_una_pieza_vieja():
    assert fu.directa_de({"datos": {"fuente_directa": {"segmento": "fx", "ancla": ANCLA_CHF}}}) == ("fx", ANCLA_CHF)
    assert fu.directa_de({"datos": {}}) is None

def test_lista_del_segmento_extiende_la_lista_cerrada():
    l = fu.lista_del_segmento("fx", segmentos=SEG)
    assert "Banco Nacional Suizo" in {e for g in l["entidades"].values() for e in g}
    assert "Goldman Sachs" in {e for g in l["entidades"].values() for e in g} and l["medios"]["NZZ"] == ["nzz.ch"]
```

- [ ] **Step 2:** `uv run pytest tests/test_analista_fuentes.py -q` → FAIL (`AttributeError: ... fuentes_directas`).
- [ ] **Step 3:** Implementar las funciones de Interfaces en `scripts/analista/fuentes.py`. Normalizar con `esquema._plano` si está al alcance sin importar circular; si no, `unicodedata.normalize("NFD")` quitando marcas. Los términos se buscan con `(?<!\w)término(?!\w)`.
- [ ] **Step 4:** Reemplazar los tres tests de `falta_banco` (`:158`, `:201`) por los de arriba; los de `seleccionar_bancos_correo` y `bancos` quedan. Borrar `falta_banco`.
- [ ] **Step 5:** `uv run pytest tests/test_analista_fuentes.py -q` → PASS (fallan aún `bot_analistas` y bot: se arreglan en Task 3).
- [ ] **Step 6: Commit** `feat(analista): reglas de fuente directa por ancla`.

---

### Task 2: Config de segmentos, resolver de ancla y verificador de dominios

**Files:**
- Create: `config/segmentos_fuentes.json`, `scripts/analista/segmentos.py`, `scripts/verificar_dominios_fuentes.py`
- Modify: `scripts/analista/fuentes.py` (cargador `cargar_segmentos`)
- Test: `tests/test_analista_segmentos.py` (nuevo)

**Interfaces:**
- Consumes: `fuentes.lista_del_segmento`, `fuentes.SEGMENTOS`.
- Produces:
  - `fuentes.cargar_segmentos(ruta: Path = CONFIG_SEGMENTOS) -> dict`
  - `segmentos.segmento_y_ancla(ticker: str, ruta_activos: Path = ACTIVOS, segmentos: dict | None = None) -> tuple[str, dict] | None`:
    1. Si el activo está en `activos.json` (recorrer todo el árbol buscando `ticker_mt5`, incluido `activos_complementarios`) y trae `segmento`: en `fx` el ancla sale de `segmentos["fx"]["divisas"][<pata no dólar>]`; en los demás, de `entry["ancla"]`.
    2. Si no está en el catálogo y es un par de 6 letras con `USD` y una divisa del mapa, `("fx", ancla de esa divisa)`.
    3. Si no, `None`.
    El ancla devuelta lleva siempre `nombre`, `entidades`, `dominios`, `terminos_ancla`.
  - `segmentos.consultas(ancla: dict) -> list[str]`: hasta 4 consultas armadas desde el ancla: `"{entidad} {terminos_ancla[0]}"` por entidad y `"site:{dominio} {nombre}"` por los primeros 3 dominios.
  - `segmentos.aviso_sin_ancla(ticker: str) -> str`: texto de cliente para el bot, con "No gasté tu cupo", sin guion largo.
- `scripts/verificar_dominios_fuentes.py`: CLI que recorre `segmentos_fuentes.json` y los anclas de `activos.json`, hace `GET https://<dominio>` con el User-Agent de `verificar_url` y reporta `ok`, `sin_verificar` (401/403/429/timeout) o `muerta` (error o 4xx/5xx). Sale con código 1 si hay `muerta`. No corre en la suite (red).

- [ ] **Step 1: Write the failing tests**

```python
def test_usdchf_fuera_del_catalogo_se_infiere_fx_con_el_snb(tmp_path):
    segmento, ancla = sg.segmento_y_ancla("USDCHF")
    assert segmento == "fx" and "Banco Nacional Suizo" in ancla["entidades"] and "snb.ch" in ancla["dominios"]

def test_un_simbolo_que_no_es_un_par_ni_esta_en_el_catalogo_no_tiene_ancla():
    assert sg.segmento_y_ancla("XYZ123") is None and sg.segmento_y_ancla("EURXXX") is None

def test_las_consultas_salen_del_ancla_y_no_pasan_de_cuatro():
    q = sg.consultas({"nombre": "Suiza", "entidades": ["Banco Nacional Suizo"], "dominios": ["snb.ch", "nzz.ch"], "terminos_ancla": ["Suiza"]})
    assert q[0] == "Banco Nacional Suizo Suiza" and "site:snb.ch Suiza" in q and len(q) <= 4

def test_todo_ancla_declarada_esta_dentro_de_la_lista_cerrada_de_su_segmento():
    for ticker, (seg, ancla) in sg.anclas_del_catalogo().items():
        lista = fu.lista_del_segmento(seg)
        nombres = {e for g in lista["entidades"].values() for e in g}
        dominios = {d for ds in lista["medios"].values() for d in ds}
        assert set(ancla["entidades"]) <= nombres, ticker
        assert set(ancla["dominios"]) <= dominios, ticker
        assert ancla["terminos_ancla"], ticker

def test_el_aviso_sin_ancla_no_lleva_guion_largo_y_dice_que_no_gasto_cupo():
    t = sg.aviso_sin_ancla("XYZ123")
    assert "XYZ123" in t and "No gasté tu cupo" in t and "—" not in t and "–" not in t
```

(`segmentos.anclas_del_catalogo() -> dict[str, tuple[str, dict]]` es parte de Produces: recorre `activos.json` y resuelve cada `ticker_mt5` con `segmento`.)

- [ ] **Step 2:** `uv run pytest tests/test_analista_segmentos.py -q` → FAIL (`ModuleNotFoundError: analista.segmentos`).
- [ ] **Step 3:** Crear `config/segmentos_fuentes.json` con la clave `_nota` y las seis claves de segmento, cada una `{"entidades": [], "medios": {}}`; `fx` suma `"divisas": {}`. Se llenan en Tasks 5 a 10, salvo la divisa CHF, que entra en Task 5 (el test de USDCHF queda marcado `xfail` hasta ahí, con motivo escrito).
- [ ] **Step 4:** Implementar `segmentos.py` y `cargar_segmentos`.
- [ ] **Step 5:** Escribir `scripts/verificar_dominios_fuentes.py` y correrlo sobre el config vacío (debe salir 0).
- [ ] **Step 6:** `uv run pytest tests/test_analista_segmentos.py -q` → PASS (xfail incluido).
- [ ] **Step 7: Commit** `feat(analista): config de segmentos, resolver de ancla y verificador de dominios`.

---

### Task 3: Cableado en preparar, bot, `--validar` y las instrucciones de agy

**Files:**
- Modify: `scripts/analista/preparar.py` (`Lectores`, `preparar_oportunidad`), `scripts/analista/bot.py` (`SIN_BANCO` → `SIN_NOTICIA_DIRECTA`, `_con_banco`, `_redactar_y_validar`, aviso del reintento), `scripts/bot_analistas.py` (`validar`), `.claude/commands/analista.md`, `tests/analista_fixtures.py`
- Test: `tests/test_analista_preparar.py`, `tests/test_analista_bot.py` (`:271`, `:590-633`), `tests/test_analista_instrucciones.py`
- Regenerar: `.agents/workflows/analista.md`

**Interfaces:**
- Consumes: `segmentos.segmento_y_ancla`, `segmentos.consultas`, `segmentos.aviso_sin_ancla`, `fuentes.lista_del_segmento`, `fuentes.fuentes_directas`, `fuentes.falta_fuente_directa`, `fuentes.directa_de`.
- Produces:
  - `Lectores.ancla: Callable[[str], tuple[str, dict] | None] = segmentos.segmento_y_ancla`
  - `datos["fuente_directa"] = {"segmento": str, "ancla": dict, "consultas": list[str]}` en la pieza `oportunidad`, sellado en la huella.
  - `bot.SIN_NOTICIA_DIRECTA` con `{dias}`, `{voz}` (nombre del ancla) y `{nombre}`; conserva "No gasté tu cupo".
  - `Atendedor._con_fuente_directa(dir_pedido, hoy) -> tuple[dict, list[str], bool]` (mismo contrato que `_con_banco`: dos intentos y `FalloPedido`).

- [ ] **Step 1: Write the failing tests**
  - `test_preparar_sella_la_fuente_directa_del_activo`: con `Lectores(ancla=lambda t: ("fx", ANCLA))`, `pieza["datos"]["fuente_directa"]["segmento"] == "fx"` y trae `consultas`.
  - `test_un_activo_sin_ancla_no_se_prepara`: `Lectores(ancla=lambda t: None)` levanta `PreparacionFallida` con "No gasté tu cupo".
  - `test_sin_ancla_no_consume_cupo` (en `test_analista_bot.py`): el estado de cupo del usuario no cambia tras el `FalloPedido`.
  - `test_sin_noticia_directa_no_publica_y_no_gasta_cupo`: sin fuente directa en dos intentos, `FalloPedido` con "noticia directa" y "No gasté tu cupo"; reemplaza las aserciones de "ninguna voz de banco" (`:271`, `:624`, `:633`).
  - `test_una_voz_de_banco_sola_ya_no_habilita`: una fuente de Goldman Sachs sin término del ancla no evita el segundo intento.
  - `test_validar_calla_en_una_pieza_sin_fuente_directa_sellada` (en el test de `bot_analistas`): una pieza vieja sin `datos.fuente_directa` valida `OK`.
  - `test_las_instrucciones_exigen_una_fuente_directa` (reemplaza `test_exige_un_banco_y_explica_el_segundo_intento`): el texto contiene `datos.fuente_directa`, "al menos una directa" y `fuentes_intento_1.json`, y no contiene "al menos una de un banco".
- [ ] **Step 2:** `uv run pytest tests/test_analista_preparar.py tests/test_analista_bot.py tests/test_analista_instrucciones.py -q` → FAIL.
- [ ] **Step 3:** `preparar_oportunidad` resuelve `lec.ancla(ticker)` al principio, antes de leer referencias o dibujar nada; sin ancla levanta `PreparacionFallida(segmentos.aviso_sin_ancla(ticker))`. Con ancla, agrega `fuente_directa` a `datos`. `tests/analista_fixtures.py` inyecta un ancla por defecto en los `Lectores` de prueba.
- [ ] **Step 4:** En `bot.py`, `_redactar_y_validar` llama `fu.depurar_pieza(pieza, hoy, lista=fu.lista_del_segmento(segmento), verificar=...)`, con el segmento leído de `fu.directa_de(pieza)`. `_con_fuente_directa` reemplaza a `_con_banco` y usa `fu.fuentes_directas`; el aviso del reintento pasa a "La primera búsqueda no trajo ninguna noticia directa: hice un segundo intento y ese sí la trajo.". Una pieza sin `directa_de` conserva el camino anterior sin exigir directa (reuso).
- [ ] **Step 5:** `bot_analistas.validar` usa `fu.directa_de` y `fu.falta_fuente_directa` en lugar de `falta_banco`.
- [ ] **Step 6:** Reescribir en `.claude/commands/analista.md`: la sección `fuentes` (una lista de 1 a 3 voces; **al menos una directa** de `datos.fuente_directa`: entidad de `ancla.entidades` o dominio de `ancla.dominios`, y la `tesis` nombra un término de `terminos_ancla`; usar `datos.fuente_directa.consultas` como punto de partida de la búsqueda; el banco de inversión es opcional y suma al correo si coincide con nuestra lectura), el segundo intento y la línea final de validación. Conservar la lista de bancos como "voz de banco opcional" y todas las reglas de tesis. Luego `uv run python scripts/agy_workflows.py` y `--check`.
- [ ] **Step 7:** Los tres módulos de test → PASS; luego `uv run pytest tests/ -q -x -k analista` → PASS.
- [ ] **Step 8: Commit** `feat(analista): la oportunidad exige una noticia directa del activo`.

---

### Task 4: El correo muestra la noticia directa

**Files:**
- Modify: `scripts/analista/oportunidad_html.py` (junto a `_voces_correo`, `:502`; llamada en `:890`)
- Test: `tests/test_analista_oportunidad_html.py` (junto a `:478`)

**Interfaces:**
- Consumes: `fuentes.fuentes_directas`, `fuentes.directa_de`.
- Produces: `_noticia_directa_correo(fuentes: list[dict], voz: tuple[str, dict] | None, c: dict[str, str]) -> str`: un bloque con la directa más reciente (entidad, medio, fecha, `tesis`, enlace), titulado "Lo último de {ancla['nombre']}", **sin** etiqueta de postura. Vacío si no hay directa o la pieza es vieja. Va antes del bloque de bancos.

**Llamado de plan (a revisar por el director):** la directa se muestra aunque contradiga nuestra lectura, porque es contexto del activo y no confirmación. El banco sigue como confirmación, como hoy.

- [ ] **Step 1: Write the failing tests**
  - `test_el_correo_lleva_la_noticia_directa_con_enlace_y_sin_etiqueta_de_postura`: fuente del SNB, `postura="bajista"` contra lectura alcista; el correo contiene la entidad, la URL y el título, y no contiene "Coincide con nuestra lectura" para ella.
  - `test_sin_fuente_directa_sellada_el_correo_sale_como_antes`.
  - `test_el_correo_cita_un_banco_y_la_directa_a_la_vez`.
- [ ] **Step 2:** `uv run pytest tests/test_analista_oportunidad_html.py -q -k directa` → FAIL.
- [ ] **Step 3:** Implementar `_noticia_directa_correo` y llamarla desde donde se arma el correo (`:890`); escapar todo con `ih.e`.
- [ ] **Step 4:** `uv run pytest tests/test_analista_oportunidad_html.py -q` → PASS.
- [ ] **Step 5: Commit** `feat(analista): el correo muestra la noticia directa`.

---

### Task 5: Segmento FX (delegable a agy)

**Files:**
- Modify: `config/segmentos_fuentes.json` (`fx`), `config/activos.json` (`"segmento": "fx"` en USDCLP, USDJPY, EURUSD, GBPUSD), `config/drivers.json`, `scripts/analista/hechos.py` (`CLAVE_DRIVERS`), `scripts/analista/agenda.py` (`PAISES`)
- Test: `tests/test_analista_segmentos.py`, `tests/test_analista_hechos.py`, `tests/test_analista_agenda.py`

**Interfaces:**
- Produces: `segmentos_fuentes.json["fx"]["divisas"]`: clave = divisa, valor = `{"pais", "banco_central", "nombre", "entidades", "dominios", "terminos_ancla"}`.
  Semilla: CHF (Banco Nacional Suizo `snb.ch`, gobierno `admin.ch`; NZZ `nzz.ch`, Le Temps `letemps.ch`, Handelszeitung `handelszeitung.ch`; términos Suiza, franco suizo, CHF, SNB); JPY (Banco de Japón `boj.or.jp`, Ministerio de Finanzas de Japón `mof.go.jp`; yen, Japón, BoJ, JPY); GBP (Banco de Inglaterra `bankofengland.co.uk`; libra esterlina, Reino Unido, BoE, GBP); EUR (`BCE`, `ecb.europa.eu`; euro, Zona Euro, BCE, EUR); CLP (`Banco Central de Chile`, `bcentral.cl`; peso chileno, Chile, BCCh, CLP). Las entidades existentes conservan su nombre exacto de `fuentes_prestigio.json`.

- [ ] **Step 1: Write the failing tests**
  - `test_cada_par_fx_del_catalogo_resuelve_a_su_banco_central`: USDCLP→"Banco Central de Chile", USDJPY→"Banco de Japón", EURUSD→"BCE", GBPUSD→"Banco de Inglaterra", USDCHF→"Banco Nacional Suizo" (se quita el `xfail` de Task 2).
  - `test_usdclp_no_pierde_su_cobertura` (llamado 10): una nota de `bcentral.cl` que nombra "peso chileno" es directa; el ancla de USDCLP no trae a la Fed.
  - `test_usdchf_tiene_ficha_de_drivers_y_no_cae_en_generales_sin_signo`: `hc.signos("USDCHF")` devuelve los medibles de su ficha con signo; el test de COPPER como "sin ficha" (`test_analista_hechos.py:98-100`) pasa a un activo que siga sin ficha (por ejemplo `BTCUSD` hasta Task 10; luego un ticker inventado).
  - `test_agenda_nombra_suiza_japon_y_reino_unido`: `ag.PAISES["Switzerland"] == "Suiza"`, `["Japan"] == "Japón"`, `["United Kingdom"] == "Reino Unido"`.
- [ ] **Step 2:** Correr los tres módulos → FAIL.
- [ ] **Step 3:** Llenar las divisas y las `entidades`/`medios` de `fx`; correr `uv run python scripts/verificar_dominios_fuentes.py` y quitar lo que salga `muerta`. Agregar fichas de drivers para USD/CHF y GBP/USD (nombres de driver del esquema real: `dollar_index`, `rendimientos_treasury`; un driver cuya correlación no esté confirmada va **sin signo**, para que se describa y no se interprete) y sumarlas a `CLAVE_DRIVERS`. Sumar los tres países a `PAISES` (nota: el calendario solo entrega cuatro países; esto es nominal hasta que se amplíe, fuera de alcance).
- [ ] **Step 4:** `uv run pytest tests/test_analista_segmentos.py tests/test_analista_hechos.py tests/test_analista_agenda.py -q` → PASS.
- [ ] **Step 5: Commit** `feat(analista): segmento fx con banco central, ministerio y medios locales`.

---

### Task 6: Segmento commodities (delegable a agy)

**Files:**
- Modify: `config/segmentos_fuentes.json` (`commodities`), `config/activos.json` (`segmento` y `ancla` en XAUUSD, XAGUSD, WTI.spot, BRENT.spot, COPPER), `config/drivers.json`, `scripts/analista/hechos.py`
- Test: `tests/test_analista_segmentos.py`, `tests/test_analista_hechos.py`

**Interfaces:**
- Produces: anclas con `mercado`. Semilla: oro y plata (World Gold Council `gold.org`, LBMA, bancos centrales; términos oro, XAU, onza); petróleo (OPEP `opec.org`, EIA `eia.gov`, Agencia Internacional de Energía `iea.org`; petróleo, crudo, WTI, Brent, OPEP+); cobre (Cochilco `cochilco.cl`, Codelco, LME, ICSG; cobre). `OPEP`, `EIA`, `World Gold Council`, `Agencia Internacional de Energía` ya están en el grupo `organismos` de la lista cerrada y habilitan para su propio mercado vía el ancla.

- [ ] **Step 1: Write the failing tests**
  - `test_una_nota_de_la_opep_que_nombra_el_petroleo_es_directa_del_wti_y_no_del_oro`.
  - `test_tasas_y_dxy_solos_no_son_directa_del_oro`: nota de la Fed sobre tasas reales, entidad "Fed", no cuenta.
  - `test_brent_cobre_y_plata_tienen_ficha_de_drivers`: `hc.signos` de cada uno trae medibles con signo o, si no está confirmado, sin signo.
  - `test_los_inventarios_eia_calculan_su_hora_con_el_helper`: la hora de EIA en el texto o config se construye con `scripts\hora_chile.ps1` (test sobre el helper o el config; ninguna hora escrita a mano).
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Config, anclas y fichas. Verificar dominios con el CLI y dejar fuera los que fallen (LBMA, ICSG y Codelco se verifican, eran suposición).
- [ ] **Step 4:** Tests de los dos módulos → PASS.
- [ ] **Step 5: Commit** `feat(analista): segmento commodities con las voces de su mercado`.

---

### Task 7: Segmento acciones, con ingesta (delegable a agy)

**Files:**
- Create: `scripts/ingesta_acciones.py`, `data central/DATA ACCIONES/` (generado, gitignorear si pesa)
- Modify: `scripts/pipeline_datos.py` (`PASOS`), `config/activos.json` (`segmento`, `ancla` con `ticker`, `cik`, `sitio_ir` en las 14 acciones), `config/segmentos_fuentes.json` (`acciones`), `scripts/analista/preparar.py` (`Lectores.empresa`), `config/gitignore` si aplica
- Test: `tests/test_ingesta_acciones.py` (nuevo), `tests/test_pipeline_datos.py`, `tests/test_analista_preparar.py`

**Interfaces:**
- Produces:
  - `ingesta_acciones.fechas_earnings(tickers: list[str], descargar: Callable) -> dict[str, dict]`: por ticker `{"fecha": "AAAA-MM-DD" | None, "fuente": "yfinance (no oficial)"}`.
  - `ingesta_acciones.informes_sec(cik: str, descargar: Callable) -> list[dict]`: últimos informes (`forma` 10-K, 10-Q u 8-K, `fecha`, `periodo`, `url`) de `data.sec.gov`, con el `User-Agent` que SEC exige. Sin cifras en el primer corte: no se cita ninguna cifra de resultados.
  - Escribe `data central/DATA ACCIONES/earnings_calendar.json` y `estados_financieros.json`, con sello de hora de ingesta.
  - `Paso("acciones", RAIZ / "scripts" / "ingesta_acciones.py", ...)` en `pipeline_datos.PASOS`, después de `precios`.
  - `Lectores.empresa: Callable[[str, dict], dict]`: devuelve `{"proxima_earnings": "miércoles 29/10" | None, "fuente_fecha": "yfinance (no oficial)", "ultimo_informe": {...} | None}`; levanta `PreparacionFallida` si el archivo falta o está vencido con el umbral de `market_data_mcp.frescura`. Va en `datos["empresa"]`, solo para segmento `acciones`.

- [ ] **Step 1: Write the failing tests**
  - `test_la_fecha_de_earnings_solo_no_habilita_la_publicacion` (P1): una fuente que es solo "Apple reportará el jueves" sin comunicado, entidad fuera del ancla o sin término, no pasa; con un comunicado de `investor.apple.com` que nombra "Apple" sí.
  - `test_las_14_acciones_tienen_ancla_con_ticker_cik_y_sitio_ir`.
  - `test_la_ingesta_marca_la_fecha_como_no_oficial_y_no_inventa_si_yfinance_falla` (con `descargar` falso que levanta): `fecha` es `None`.
  - `test_sin_ingesta_o_vencida_la_accion_no_publica_y_el_bot_lo_dice`.
  - `test_la_fecha_futura_va_en_modo_anticipacion`: el dato de `datos.empresa` trae la fecha como `proxima_earnings`; la instrucción de `analista.md` pide modo anticipación (test de texto).
  - `test_pipeline_datos_corre_acciones_despues_de_precios`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar la ingesta con descargadores inyectables (yfinance y `requests`), enganchar el paso, definir las anclas (sitios IR y `sec.gov`, verificar dominios) y `Lectores.empresa`. Agregar a `analista.md` una línea sobre `datos.empresa` y modo anticipación.
- [ ] **Step 4:** Tests → PASS; `uv run python scripts/agy_workflows.py --check` → OK.
- [ ] **Step 5: Commit** `feat(analista): segmento acciones con ingesta de earnings e informes SEC`.

---

### Task 8: Segmento ETF (delegable a agy)

**Files:**
- Modify: `config/segmentos_fuentes.json` (`etfs`), `config/activos.json` (`segmento` y `ancla` con `emisor`, `indice`, `subyacente` en QQQ.US, SPY.US, GLD.US, IWM.US, SOXX.US), `config/drivers.json`
- Test: `tests/test_analista_segmentos.py`

**Interfaces:**
- Produces: emisores de la semilla: QQQ.US Invesco; SPY.US State Street (`spdrs.com`); GLD.US World Gold Trust y World Gold Council con State Street (`spdrgoldshares.com`, `gold.org`); IWM.US y SOXX.US BlackRock/iShares (`ishares.com`, `blackrock.com`). Medios del sector: etf.com, etfdb.com, Morningstar. `spdrs.com` y `spdrgoldshares.com` eran suposición: se verifican.

- [ ] **Step 1: Write the failing tests**
  - `test_un_comunicado_del_emisor_fechado_y_con_url_es_directo`.
  - `test_un_titular_generico_del_subyacente_no_es_directo_de_gld`: nota del oro con entidad "World Gold Council" pero sin nombrar "GLD" ni el fideicomiso, no cuenta (herencia partida: drivers del subyacente, fuentes propias).
  - `test_gld_hereda_los_drivers_del_oro_pero_no_sus_fuentes`: `hc.signos("GLD.US")` igual a los del oro; el ancla de GLD no incluye a la OPEP ni los términos `oro` solos.
  - `test_los_flujos_de_pagina_no_habilitan`: el ancla no admite entidades fuera de los emisores; no hay camino de código donde un flujo cuente como fuente (test sobre `fuentes_directas`, que solo mira `fuentes`).
- [ ] **Step 2:** Correr → FAIL. **Step 3:** Config y anclas; `CLAVE_DRIVERS` para ETF apunta a la ficha del subyacente. **Step 4:** PASS. **Step 5: Commit** `feat(analista): segmento etfs anclado en su emisor`.

---

### Task 9: Segmento índices (delegable a agy)

**Files:**
- Modify: `config/segmentos_fuentes.json` (`indices`), `config/activos.json` (US100.spot, US500.spot, US30.spot; GER40.spot en `activos_complementarios` con `segmento` y `ancla`), `config/drivers.json`, `config/feriados_bolsa.json` (agregar `XETRA`), `scripts/analista/agenda.py`
- Test: `tests/test_analista_segmentos.py`, `tests/test_analista_hechos.py`, tests de feriados existentes

**Interfaces:**
- Produces: anclas con `proveedor`, `bolsa` y `terminos_ancla`: US100 (Nasdaq; "Nasdaq 100", "NDX", "Nasdaq"), US500 y US30 (S&P Dow Jones Indices, NYSE; "S&P 500", "Dow Jones", "Dow", "US30"), GER40 (Deutsche Börse, STOXX, Xetra; "DAX", "GER40"). Fichas de drivers de US500, US30 y GER40: nombres de driver del esquema real (`tasas_fed`, `rendimientos_treasury`, `earnings_...` según `US100`); un driver sin correlación confirmada va sin signo. Abrir antes `feriados_bolsa.json` y `scripts/` que lo consumen para ver cómo se declara una bolsa nueva. `cboe.com`, `dowjones.com`, `indexes.nasdaqomx.com` y los de Deutsche Börse/STOXX/Xetra eran suposición: se verifican.

- [ ] **Step 1: Write the failing tests**
  - `test_los_earnings_de_un_constituyente_no_son_directa_del_indice` (llamado 11): nota de Apple que no nombra "Nasdaq 100" ni "NDX" no cuenta para US100; si el titular o la tesis nombra "Nasdaq 100", sí.
  - `test_wall_street_cae_sin_nombrar_el_indice_no_es_directa`.
  - `test_cada_indice_tiene_ficha_y_no_cae_en_generales`: `hc.signos` de US500, US30 y GER40.
  - `test_xetra_tiene_feriados_y_alemania_esta_en_la_agenda`: `feriados_bolsa.json["XETRA"]` existe y el consumidor del archivo lo reconoce; `ag.PAISES["Germany"] == "Alemania"`.
  - `test_un_precio_objetivo_de_un_banco_sobre_el_indice_suma_pero_no_habilita`: una nota de Goldman Sachs sin término del ancla no cuenta como directa.
- [ ] **Step 2:** Correr → FAIL. **Step 3:** Config, anclas, fichas, bolsa y país. **Step 4:** PASS. **Step 5: Commit** `feat(analista): segmento indices con proveedor y bolsa como voz`.

---

### Task 10: Segmento cripto (delegable a agy)

**Files:**
- Modify: `config/segmentos_fuentes.json` (`cripto`), `config/activos.json` (BTCUSD, ETHUSD, SOLUSD, LTCUSD, ADAUSD, DOGUSD; viven en `forex_commodities` con `categoria: crypto`, confirmarlo abriendo el archivo), `config/drivers.json`, `.claude/commands/analista.md`
- Test: `tests/test_analista_segmentos.py`, `tests/test_analista_instrucciones.py`

**Interfaces:**
- Produces: anclas con `red` y `fundacion`. Semilla: Ethereum Foundation, Solana Foundation, Cardano con IOG, Litecoin Foundation, Dogecoin Foundation (verificar `litecoin.org` y los demás). BTC, LTC y DOGE, sin entidad central: emisores de ETF spot (iShares/BlackRock, Fidelity, Grayscale), bolsas (Coinbase, Kraken, Binance), reguladores (SEC, CFTC) y datos on-chain (Glassnode). Mercado 24/7: la agenda sale vacía sin catalizador fechado, sin inventar correlaciones macro.

- [ ] **Step 1: Write the failing tests**
  - `test_la_fundacion_de_la_red_es_directa_de_su_cripto_y_no_de_otra`: nota de la Ethereum Foundation que nombra "Ethereum" cuenta para ETHUSD y no para SOLUSD.
  - `test_un_portal_cripto_fuera_de_la_lista_no_cuenta`: dominio no listado, descartado por `depurar` con motivo.
  - `test_las_instrucciones_piden_que_el_comunicado_de_un_emisor_traiga_datos_y_no_promocion` (llamado de plan: cuenta solo si trae datos del fondo o del mercado). Es una regla del prompt de agy y no se puede verificar por código: se dice en `analista.md` y queda anotado en el documento como límite conocido.
  - `test_un_blog_de_fundacion_cuenta_solo_con_url_propia_y_fecha`: URL de portada del blog se descarta por `_con_ruta_de_articulo`.
- [ ] **Step 2:** Correr → FAIL. **Step 3:** Config, anclas, fichas (BTCUSD ya tiene; ETH, SOL, LTC, ADA, DOGE según corresponda), línea en `analista.md`, regenerar workflows. **Step 4:** PASS. **Step 5: Commit** `feat(analista): segmento cripto con la voz de cada red`.

---

### Task 11: Cierre

**Files:**
- Modify: `docs/bot-analistas.md`, `CLAUDE.md` (una línea en la sección del bot si corresponde), `docs/superpowers/specs/2026-10-20-noticia-directa-por-segmento-design.md` (estado)
- Test: `tests/test_analista_segmentos.py`

- [ ] **Step 1: Write the failing test** `test_todo_activo_del_catalogo_tiene_segmento_y_ancla`: recorre `activos.json` (forex_commodities, indices, etfs, acciones, GER40) y exige `segmentos.segmento_y_ancla(ticker)` no nulo; excluye solo `DXY` y `COBRE` (referencias, no activos publicables), declarado en el test con su motivo.
- [ ] **Step 2:** Correr el test → debe pasar si Tasks 5 a 10 están completas; si falla, nombra el ticker que quedó sin voz.
- [ ] **Step 3:** `uv run pytest tests/ -q` completo → PASS; `uv run python scripts/agy_workflows.py --check` → OK; `uv run python scripts/verificar_dominios_fuentes.py` sin `muerta`.
- [ ] **Step 4:** Documentar en `docs/bot-analistas.md` el contrato de fuente directa, las seis anclas y cómo editar `segmentos_fuentes.json`. Prueba manual: `--una` con `USDCHF` sin red devuelve el aviso sin gastar cupo.
- [ ] **Step 5:** `omega_store` con las decisiones clave (directa obligatoria, P1, P2, correo muestra la directa, ancla por activo).
- [ ] **Step 6: Commit** `docs(analista): noticia directa por segmento` y abrir el PR (la lista de llamados del plan va en la descripción).

---

## Self-review

- **Cobertura del spec:** contrato común (Tasks 1 a 3), seis segmentos (5 a 10), P1 (Task 1 y 7), P2 (Task 3: `falta_banco` borrado, banco opcional), herencia partida (Task 8), USD/CLP (Task 5), llamado 9 (Task 7), llamado 11 (Task 9), `analista.md` regenerado (Tasks 3, 7, 10), tests a actualizar (Tasks 1, 3, 5). Se sumó la Task 4 (el correo), que el spec no nombraba y sin la cual la nota directa no llega al cliente.
- **Consistencia de nombres:** `segmento_y_ancla`, `consultas`, `aviso_sin_ancla`, `anclas_del_catalogo` (segmentos.py); `lista_del_segmento`, `nombra_ancla`, `fuentes_directas`, `falta_fuente_directa`, `directa_de`, `cargar_segmentos` (fuentes.py); `datos["fuente_directa"]` y `datos["empresa"]`.
- **Límites declarados:** el calendario no cubre Suiza, Japón ni Reino Unido (`PAISES` es nominal); la ingesta de acciones no trae cifras de resultados; la regla de "marketing" de cripto vive solo en el prompt.
