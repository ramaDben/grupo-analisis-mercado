# Seguimiento de un solo suceso (15m / 5m): plan de implementación

> **Para quien ejecuta:** el orquestador es Claude Code y la implementación la hace AGY con un
> subagente propio por tarea (`invoke_subagent`). T1, T2 y T3 corren en paralelo; T4 empieza
> cuando las tres estén verificadas. Los pasos usan casillas (`- [ ]`).

**Objetivo:** que la lámina de `/seguimiento` diga en una frase si hoy la fuerza es alcista o
bajista, a través de **un solo suceso del día** que el ejecutivo puede volver a revisar con su
cliente.

**Arquitectura:** el motor Tori no se reescribe. Lee una línea en velas de 15 minutos con la regla
A+ del indicador del director, la fija como el suceso del día en `data/sucesos_diarios/` y la
evalúa contra el cierre de las velas de 5 minutos. La lámina muestra un titular, una línea chica y,
si hace falta, una nota sobre la semana.

**Stack:** Python 3.12, pandas, pytest, MetaTrader5, plantilla HTML con Playwright (`story_render`).

**Spec:** no hay un documento aparte. Las decisiones del director del 2026-10-21 están copiadas
en *Decisiones* (abajo) y en la memoria `project_seguimiento_suceso_unico.md`.

## Decisiones (la spec)

1. Nada de confluencias ni de análisis técnico a la vista: la lámina lleva un texto fácil y atractivo.
2. **15m es la estructura y 5m es el gatillo.** El suceso ocurre cuando cierra una vela de 5 minutos.
3. **Se muestra un solo desenlace.** Por defecto, el rebote a favor de la línea. Pasa a ruptura solo
   cuando una vela de 5 minutos ya cerró al otro lado.
4. **A+ en 15m:** 3 toques o más, 30 velas o más entre el ancla y el punto B (`.mq5:539`), y un punto
   B que no esté en las últimas 6 velas. Esta última es la regla de Python, que el director pidió
   conservar. La regla de "1 semana" sigue valiendo para 4H.
5. **Si no hay línea A+, se usa la mejor B.** `lectura._peso` ya ordena las líneas así.
6. **Lo semanal se menciona solo si hace falta**, nunca de relleno.
7. **El suceso se fija con el primer pedido del día y no cambia en el resto del día.** Una ruptura no
   lo reemplaza: pasa a ser su estado.

### Pendientes de confirmar por el director (el plan supone lo que está en cursiva)

- Cuándo se menciona la semana: *solo en dos casos. Si va en sentido contrario: "Es un retroceso de
  hoy: la tendencia de la semana sigue al alza". Si la referencia de la semana se reemplazó: "Ojo:
  lo que vimos el lunes cambió. La semana ahora se lee a la baja".*
- *La simulación del lunes, la entrada real y el dato macro dejan de mostrarse en la lámina y en el
  texto.* La simulación se sigue calculando para el registro.
- *El gráfico pasa a velas de 15 minutos y traza solo la línea del suceso y el objetivo.*
- *El texto de WhatsApp mantiene la regla de gerencia: dice "CFD" una vez y no lleva precios.*
- *Etiqueta del marco de 15 minutos: "intradía, de 2 a 6 horas".*

## Restricciones globales

- Regla 1: ningún precio va escrito a mano. Los textos usan `{nivel}` y `{objetivo}`, que se
  formatean con `seguimiento._fmt(valor, digits)`.
- Regla 0: prohibido `generate_image`. La lámina se hace en HTML y CSS.
- Texto de cliente: sin `—` ni `–`, tuteo chileno, "línea de control" (nunca "stop"),
  soporte/resistencia (nunca techo/suelo), flechas ⬆️ ⬇️ ↔️.
- Texto de cliente por Python (`write_text(..., encoding="utf-8")`), nunca por la consola de PowerShell.
- Rama `feat/seguimiento-suceso-unico`. AGY no hace commits: los hace el orquestador después de
  verificar cada tarea.
- Suite: `uv run pytest -q` tiene que terminar verde al cerrar cada tarea.

## Review Focus

1. **Mercado cerrado o fin de semana:** `velas_mt5` no entrega vela en curso. Resultado esperado:
   estado `cerrado`, sin escribir archivo y con la lámina igual (test en T4).
2. **Un suceso fijado ayer:** si la fecha cambió, se fija uno nuevo y el de ayer se ignora (test en T2).
3. **Una vela de 5m que toca la línea y cierra al otro lado:** cuenta como ruptura, no como toque
   (test en T2).
4. **Bajista y sin objetivo:** todo funciona en espejo. Sin objetivo, el estado nunca llega a
   `cumplido` (tests en T2 y T3).
5. **Pieza guardada por el código viejo** (el bot reusa piezas por 30 minutos): si no trae `suceso`,
   se prepara de nuevo en vez de rendir con la plantilla retirada (test en T4).

---

## Archivos

| Archivo | Tarea | Qué hace |
|---|---|---|
| `scripts/estrategia/fuente.py` | T1 | `DURACION` con M5 y M15 |
| `scripts/estrategia/tori/parametros.py`, `calidad.py` | T1 | A+ medido en velas de ancla a punto B |
| `scripts/estrategia/tori/__init__.py`, `procedencia.py` | T1 | `MARCOS_M15`, `MARCOS_GATILLO`, `PARAMETROS_M15`, `crear_m15` |
| `scripts/analista/suceso.py` | T0 (contrato), T2 | Elegir, fijar y evaluar el suceso (lógica pura y disco) |
| `scripts/analista/suceso_texto.py` | T3 | Textos de la lámina, nota semanal, WhatsApp |
| `scripts/analista/comercial.py` | T3 | `payload_suceso` |
| `templates/stories/seguimiento_dia.html` + fixture | T3 | La lámina nueva |
| `scripts/analista/preparar.py`, `seguimiento.py`, `bot.py` | T4 | Integración |

---

### Task 0: contrato (orquestador, antes de despachar)

**Archivos:** crear `scripts/analista/suceso.py` con los dataclasses completos y las funciones con
`raise NotImplementedError`. Crear la rama.

```python
EstadoAvance = Literal["esperando", "en_nivel", "rebotando", "cumplido", "ruptura"]
EstadoResumen = Literal["esperando", "en_nivel", "rebotando", "cumplido", "ruptura", "sin_direccion", "cerrado"]
DIR_SUCESOS = RAIZ / "data" / "sucesos_diarios"
VELA_M15_S, VELA_M5_S = 900, 300

@dataclass(frozen=True)
class Suceso:
    ticker: str
    fecha: str          # AAAA-MM-DD, America/Santiago
    fijado: str         # ISO a minutos, America/Santiago
    sentido: Literal["ALCISTA", "BAJISTA"]
    t_ref: int          # apertura de la última vela M15 cerrada al fijar (época del servidor)
    valor_ref: float    # valor de la línea en esa vela (Linea.valor_actual)
    pendiente: float    # precio por vela de 15 minutos; 0.0 en un horizontal
    objetivo: float | None
    calidad: str        # "A+" o "B"
    tolerancia: float   # Parametros.tolerancia_toque_atr x ATR de 15 minutos

@dataclass(frozen=True)
class Avance:
    estado: EstadoAvance
    valor_linea: float  # valor de la línea en la última vela de 5m evaluada

@dataclass(frozen=True)
class Resumen:          # lo que T4 arma y T3 convierte en texto
    estado: EstadoResumen
    sentido: Literal["ALCISTA", "BAJISTA"] | None
    nivel: float | None
    objetivo: float | None
    siguiente: float | None   # solo en ruptura: el nivel a vigilar de la lectura nueva
    calidad: str
    nota_semana: str          # "" cuando no hace falta

def elegir(lectura: Lectura, tiempos_m15: Sequence[int], ticker: str, fecha: str, fijado: str,
           p: Parametros = PARAMETROS_M15) -> Suceso | None: ...
def valor_en(s: Suceso, tiempos_m15: Sequence[int], ts: int) -> float: ...
def evaluar(s: Suceso, velas_m5: Sequence[Mapping[str, float]], precio: float,
            tiempos_m15: Sequence[int]) -> Avance: ...
def guardar(s: Suceso, base: Path = DIR_SUCESOS) -> Path: ...
def cargar(fecha: str, ticker: str, base: Path = DIR_SUCESOS) -> Suceso | None: ...
def del_dia(lectura: Lectura, tiempos_m15: Sequence[int], ticker: str, ahora: datetime,
            base: Path = DIR_SUCESOS) -> Suceso | None: ...
```

`PARAMETROS_M15` se importa desde `estrategia.tori`, y T1 lo crea. Para que el contrato importe
antes de que T1 termine, en T0 se agrega `PARAMETROS_M15 = PARAMETROS` como marcador en
`tori/__init__.py`, y T1 lo reemplaza.

- [ ] Rama `feat/seguimiento-suceso-unico` desde master, sin los archivos de `data central/` modificados.
- [ ] `uv run python -c "import sys; sys.path.insert(0,'scripts'); import analista.suceso"` no falla.
- [ ] Commit: `chore(seguimiento): contrato del suceso único`.

---

### Task 1: el motor lee 15 minutos con la regla del indicador

**Archivos:** modificar `scripts/estrategia/fuente.py:19`, `tori/parametros.py`, `tori/calidad.py:35-40`,
`tori/__init__.py` y `tori/procedencia.py:68-73`. Tests: `tests/test_tori_calidad.py`,
`tests/test_tori_intradia.py` y `tests/test_estrategia_fuente.py`.

**Interfaces que produce:**
- `fuente.DURACION["M5"] == 300`, `fuente.DURACION["M15"] == 900`.
- `Parametros.velas_ab_min: int | None = None`.
- `tori.PARAMETROS_M15 = dataclasses.replace(PARAMETROS, velas_ab_min=30)`.
- `tori.MARCOS_M15 = Marcos(contexto=("H4", "H1"), operativo="M15", velas={"H4": 180, "H1": 600, "M15": 250}, etiquetas={…H4 y H1 como en MARCOS_INTRADIA…, "M15": Etiqueta("intradía", "de 2 a 6 horas")})`.
- `tori.MARCOS_GATILLO = Marcos(contexto=(), operativo="M5", velas={"M5": 200}, etiquetas={"M5": Etiqueta("gatillo", "de 5 a 30 minutos")})`.
- `tori.crear_m15() -> Tori` = `Tori(parametros=PARAMETROS_M15, marcos=MARCOS_M15)`.

- [ ] **Tests que fallan primero:**
  - `test_a_mas_por_velas_entre_anclas`: un `Trazo` con 3 toques, `i_b - i_a == 30` y el punto B
    fuera de las últimas 6 velas da `"A+"` con `PARAMETROS_M15`. Con `i_b - i_a == 29` da `"B"`.
  - `test_a_mas_por_velas_respeta_punto_b_reciente`: 3 toques, 40 velas, `i_b == len(s) - 3` → `"B"`.
  - `test_sin_velas_ab_min_conserva_regla_semanal`: el mismo trazo con `PARAMETROS` se califica igual
    que antes (regla de semanas).
  - `test_crear_m15_lee_en_m15`: con `conf.velas_de(tori.crear_m15(), semilla=11)`, `leer` devuelve
    `Lectura` con `marco == "M15"`.
  - `test_partir_velas_m15_separa_la_abierta`: con `ahora_servidor = time + 600` sobre la última vela
    M15, `partir_velas(df, "M15", …, True)` la devuelve como abierta.
- [ ] **Implementar:** en `calificar`, `largo = (t.i_b - t.i_a) >= p.velas_ab_min` si
  `p.velas_ab_min is not None`; si es `None`, sigue `semanas >= 1.0`. Lo demás no cambia.
- [ ] **Procedencia:** agregar un `Fundamento` con la regla "El seguimiento intradía busca su línea
  en 15 minutos con 30 velas entre ancla y punto B, y la gatilla con el cierre de 5 minutos", origen
  `("Decisión del director, 2026-10-21", "Indicador mql5/GI_Canales_Seguridad.mq5, EvaluarTrazo")` y
  no_probado "La regla de 30 velas viene del indicador del director, no de la doctrina de Tori; no
  se midió su resultado." Así lo cumple `test_procedencia_declara_decision_director_2026_10_21`.
- [ ] `uv run pytest tests/test_tori_calidad.py tests/test_tori_intradia.py tests/test_estrategia_fuente.py -q` en verde, y después la suite completa.

---

### Task 2: el suceso (lógica pura y disco)

**Archivos:** implementar las funciones de `scripts/analista/suceso.py` (T0). Test:
`tests/test_analista_suceso.py`. Sin MT5: las velas se arman a mano en los tests.

**Interfaces que consume:** `Lectura`, `Linea` y `Referencia` de `estrategia.contrato`;
`PARAMETROS_M15`; `referencia_diaria.fecha_de`; `referencia_semanal.slug`.

**Algoritmos que el plan fija:**

- `elegir`:
  - Devuelve `None` si `lectura.direccion == "LATERAL"`, si `lectura.estado == "RANGO"` o si
    `lectura.vigilar.linea is None`.
  - Si no, toma `linea = lectura.vigilar.linea` y `t_ref = tiempos_m15[-1]`.
  - `valor_ref = linea.valor_actual`.
  - `pendiente`: `0.0` en un horizontal. En una diagonal es `(p2 - p1) / (i2 - i1)`, con `i` el
    índice de cada ancla en `tiempos_m15`. Si una ancla no está, levanta `ValueError`.
  - `objetivo = lectura.objetivo.precio` o `None`.
  - `calidad = linea.calidad`.
  - `tolerancia = p.tolerancia_toque_atr * lectura.metricas["atr"]`.
- `valor_en`:
  - `k = bisect_right(tiempos_m15, ts) - 1`. Si `k < 0`, levanta `ValueError`.
  - `frac = (ts - tiempos[k]) / 900`, topado en `1.0` salvo en la última vela. Un hueco de mercado
    no avanza la línea; después de la última vela, la línea se extrapola.
  - Devuelve `valor_ref + pendiente * (índice(ts) - índice(t_ref))`.
- `evaluar` (alcista; el bajista es el espejo):
  - Usa solo las velas con `time >= t_ref + 900`, en orden.
  - En cada vela calcula `L = valor_en(s, tiempos, time + 300)`.
  - La ruptura se revisa primero: si `close < L`, devuelve `ruptura`.
  - Si `low <= L + tolerancia`, marca que tocó.
  - Si ya tocó, hay objetivo y `high >= objetivo`, devuelve `cumplido`.
  - Al terminar las velas, toma `L` en la última vela evaluada (sin velas, en `t_ref + 900`):
    - `en_nivel` si `abs(precio - L) <= tolerancia`;
    - si no, `rebotando` si tocó;
    - si no, `esperando`.
  - El primer evento que ocurre gana: un `cumplido` anterior a una ruptura sigue siendo `cumplido`.
- `del_dia`:
  - Con `fecha = fecha_de(ahora)`, si `cargar(fecha, ticker)` encuentra el suceso, lo devuelve.
  - Si no, lo arma con `elegir(…)`. Si sale `None`, no escribe nada.
  - Si sale un suceso, lo guarda y lo devuelve.
  - Ruta: `base/<fecha>/<slug(ticker)>.json`, en UTF-8 con `ensure_ascii=False`.

- [ ] **Tests (escribirlos primero, todos con datos sintéticos):**
  - `test_elegir_lateral_o_rango_es_none`.
  - `test_elegir_diagonal_calcula_pendiente_por_vela`: anclas en los índices 10 y 40 con precios 100
    y 130 → `pendiente == 1.0`.
  - `test_valor_en_no_avanza_en_hueco`: hay un hueco de 3600 s entre dos velas M15, y el valor a
    mitad del hueco es igual al de la vela siguiente menos una pendiente.
  - `test_valor_en_antes_de_la_ventana_levanta`.
  - `test_evaluar_esperando`, `test_evaluar_en_nivel`, `test_evaluar_rebotando`, `test_evaluar_cumplido`.
  - `test_evaluar_ruptura_por_cierre_5m`: una vela de 5m con `close` un tick bajo la línea → `ruptura`.
  - `test_evaluar_toca_y_cierra_al_otro_lado_es_ruptura` (Review Focus 3).
  - `test_evaluar_cumplido_antes_de_ruptura_sigue_cumplido`.
  - `test_evaluar_sin_objetivo_nunca_cumplido` (Review Focus 4).
  - `test_evaluar_bajista_espejo`: los mismos casos con el signo invertido.
  - `test_evaluar_ignora_velas_anteriores_a_la_fijacion`.
  - `test_del_dia_fija_una_vez_y_reutiliza` (`tmp_path`): el segundo llamado con otra lectura
    devuelve el suceso del primero.
  - `test_del_dia_otro_dia_fija_nuevo` (Review Focus 2).
  - `test_del_dia_sin_direccion_no_escribe`.
- [ ] `uv run pytest tests/test_analista_suceso.py -q` en verde, y después la suite completa.

---

### Task 3: los textos, la lámina y el payload

**Archivos:** crear `scripts/analista/suceso_texto.py`, `templates/stories/seguimiento_dia.html` y
`tests/fixtures/stories/payloads/seguimiento_dia.json`. Modificar `scripts/analista/comercial.py`
(agregar `payload_suceso`; **no tocar** `payload_seguimiento`). Test: `tests/test_analista_suceso_texto.py`.

**Interfaces que consume:** `Resumen` (T0), `seguimiento._fmt`, `seguimiento.MARCA_SALUDO`,
`seguimiento._activo_con_articulo`, y de `comercial` `firma`, `LOGO_LAMINA` y `AVISO_SEGUIMIENTO`.

**Interfaces que produce:**
- `lamina(r: Resumen, digits: int) -> tuple[str, str, str]` devuelve `(flecha, titular, linea_chica)`.
- `nota_semana(sentido: str, direccion_semana: str, reemplazada: bool) -> str`.
- `whatsapp(r: Resumen, nombre: str) -> str`, que empieza con `MARCA_SALUDO`.
- `comercial.payload_suceso(activo: dict, resumen: dict, datos_al: str, autor, chart: Path) -> dict`.
  Claves: `logo_src`, `chip` (= `"SEGUIMIENTO DE HOY"`), `datos_al`,
  `activo` (`"{nombre} · {ticker_visible}"`), `direccion` (`alcista`/`bajista`/`lateral`), `estado`,
  `flecha`, `titular`, `linea_chica`, `nota_semana`, `chart_png`,
  `pie_imagen` (`"{nombre} · velas de 15 minutos · MetaTrader 5"`), `firma`, `aviso`.

**Textos exactos de la lámina (alcista).** `{nivel}`, `{objetivo}` y `{siguiente}` se formatean con
`_fmt`.

| Estado | Flecha | Titular | Línea chica |
|---|---|---|---|
| esperando | ⬆️ | Esperamos los {nivel} para un rebote al alza | Si se da, el siguiente paso es {objetivo} *(sin objetivo: Lo confirma una vela de 5 minutos que rebote sobre la línea)* |
| en_nivel | ⬆️ | El precio está en los {nivel}: aquí se define el rebote | Lo confirma una vela de 5 minutos que cierre sobre la línea |
| rebotando | ⬆️ | Rebotó en los {nivel} y va camino a {objetivo} *(sin objetivo: Rebotó en los {nivel}: la fuerza sigue al alza)* | La línea de control sigue en {nivel} |
| cumplido | ✅ | Rebotó en los {nivel} y llegó a {objetivo} | Lectura cumplida |
| ruptura | ⬇️ | Perdió los {nivel}: ahora la presión es a la baja | El siguiente nivel a vigilar es {siguiente} *(sin siguiente: Esperamos que el precio defina antes de leer otro nivel)* |
| sin_direccion | ↔️ | Hoy el precio no marca dirección | Esperamos que defina antes de leer un nivel |
| cerrado | ↔️ | El mercado está cerrado | El seguimiento de hoy parte con la apertura |

**Espejo bajista:**
- La flecha ⬆️ pasa a ⬇️, y la de la ruptura pasa a ⬆️.
- "rebote al alza" → "rechazo a la baja"; "se define el rebote" → "se define el rechazo".
- "cierre sobre" → "cierre bajo"; "rebote sobre" → "rechace bajo".
- "Rebotó en" → "Se devolvió en"; "la fuerza sigue al alza" → "la presión sigue a la baja".
- "Perdió los {nivel}: ahora la presión es a la baja" → "Superó los {nivel}: ahora la fuerza es al alza".

**Nota semanal:**
- `reemplazada`: "Ojo: lo que vimos el lunes cambió. La semana ahora se lee {al alza|a la baja}."
  El sentido es `direccion_semana`. Si la semana quedó `LATERAL`: "La semana ahora no marca dirección."
- Si no hubo reemplazo y `direccion_semana` es `ALCISTA` o `BAJISTA` pero distinta de `sentido`:
  "Es un retroceso de hoy: la tendencia de la semana sigue {al alza|a la baja}."
- En cualquier otro caso, `""`.

**WhatsApp:**
- Empieza con `MARCA_SALUDO + " "`.
- `{activo}` lleva artículo (`_activo_con_articulo`) y la marca CFD va una sola vez: `{activo} (CFD)`.
- No lleva precios.
- Si hay nota semanal, se agrega al final como una oración más.

Textos alcistas:
- esperando: "hoy estamos esperando que {activo} (CFD) llegue a su nivel del día para un rebote al alza. Te dejé la lámina con el punto exacto, ¿lo revisamos cuando llegue?"
- en_nivel: "{activo} (CFD) está justo en su nivel del día y ahí se define el rebote al alza. Te dejé la lámina con el punto exacto, ¿lo miramos juntos?"
- rebotando: "{activo} (CFD) rebotó en su nivel del día y va al alza. En la lámina está el punto al que apunta, ¿lo seguimos?"
- cumplido: "lo que esperábamos hoy se cumplió: {activo} (CFD) rebotó en su nivel y llegó al objetivo. Te dejé la lámina para que lo veas."
- ruptura: "{activo} (CFD) perdió su nivel del día y ahora la presión es a la baja. Te dejé la lámina con lo que viene, ¿lo conversamos?"
- sin_direccion: "hoy {activo} (CFD) no marca una dirección clara, así que esperamos que defina antes de tomar un nivel. Te aviso apenas lo haga."
- cerrado: "{activo} (CFD) todavía no abre. Apenas cotice te mando el nivel del día."

El espejo bajista usa las sustituciones de arriba. Además, "rebotó en su nivel" → "se devolvió en
su nivel" y "va al alza" → "va a la baja".

**La lámina** (`seguimiento_dia.html`, 1920×1080):
- Parte de `templates/stories/seguimiento.html`: mismo encabezado, marca de agua, firma, aviso y
  zona del gráfico.
- Saca las dos tarjetas de precio, el sello, el avance, la tarjeta del plan de hoy y la entrada real.
- Debajo del encabezado van la flecha y el titular grande (la jerarquía principal), la línea chica
  debajo, y la nota semanal más chica y solo si no está vacía (`{{nota_semana}}` dentro de un
  bloque que se oculta con `:empty`).
- Los colores salen de `var(--rol)` de `marca.css`. La píldora de dirección usa `--sube`/`--baja`.
- `scripts/marca_tokens.py --check` tiene que quedar limpio.
- **Prohibido `generate_image`.**

- [ ] **Tests (primero):**
  - `test_lamina_cada_estado_alcista_y_bajista`: los 7 estados por sentido devuelven el texto exacto
    de la tabla, con `_fmt` aplicado y `digits=2`.
  - `test_lamina_sin_objetivo_y_sin_siguiente`.
  - `test_nota_semana_tres_casos`.
  - `test_whatsapp_cfd_una_vez_y_sin_cifras`: en cada estado, `texto.count("CFD") == 1` y ningún
    dígito fuera de `MARCA_SALUDO`.
  - `test_textos_sin_guion_largo_ni_voseo`: en ninguna salida aparecen `—`, `–`, "stop", "techo",
    "suelo", "tenés" ni "podés".
  - `test_payload_suceso_claves`: las claves de arriba, sin ninguna de más.
  - `tests/test_story_render.py` en verde con la fixture nueva.
- [ ] Rendir la fixture con `uv run --extra stories python scripts/rendir_todas.py` y **mirar el PNG**:
  que se lean `¿`, `·` y las tildes, y que el titular sea lo primero que se ve.
- [ ] Suite completa en verde.

---

### Task 4: integración en el bot (después de T1, T2 y T3)

**Archivos:** modificar `scripts/analista/preparar.py:157-158`, `:224-232` y `:461-552`,
`scripts/analista/seguimiento.py:373-398` (`redactar`) y `scripts/analista/bot.py:434-470`
(`_seguimiento`). Tests: `tests/test_analista_seguimiento.py` y un `tests/test_analista_bot*.py`
existente que cubra `_seguimiento`.

**Interfaces que consume:** todo lo producido por T1, T2 y T3.

- [ ] **`preparar_seguimiento`:**
  - Conservar todo lo de la semana que alimenta el registro (`ev`, `reemplazada`, `lectura`).
  - Quitar el plan H1: `_intradia`, `postura`, `oportunidad_hoy` y `sg.mensaje`.
  - Agregar, en este orden:
    1. `velas15, en_curso = lec.velas(ticker, MARCOS_M15, 0)`.
    2. `lectura15 = crear_m15().leer(ticker, velas15, digits, en_curso=None)`.
    3. `tiempos = velas15["M15"]["time"].tolist()`.
    4. `s = suceso.cargar(fecha, ticker, base)`. Si es `None` y `en_curso is None`, el estado es
       `cerrado`.
    5. Si no, `s = suceso.del_dia(lectura15, tiempos, ticker, ahora, base)`. Si da `None`, el estado
       es `sin_direccion`.
    6. Con suceso: `m5, _ = lec.velas(ticker, MARCOS_GATILLO, 0)` y
       `av = suceso.evaluar(s, m5["M5"].to_dict("records"), en_curso.precio if en_curso else lectura15.precio, tiempos)`.
       Si `valor_en` levanta `ValueError` (anclas fuera de la ventana), se borra el archivo y se
       vuelve a fijar una vez.
    7. `siguiente = lectura15.vigilar.precio` solo cuando `av.estado == "ruptura"` y
       `lectura15.direccion` no es ni `s.sentido` ni `"LATERAL"`.
    8. `nota = st.nota_semana(s.sentido, lectura.direccion, reemplazada)`.
  - `base` es un campo nuevo de `Lectores`: `base_sucesos: Path | None = None`. Con `None` se usa
    `suceso.DIR_SUCESOS`.
  - Gráfico:
    - `MARCO_GRAFICO_SEGUIMIENTO = "M15"`.
    - Se dibuja `dataclasses.replace(lectura15, lineas=(lectura15.vigilar.linea,))`, con niveles
      `[(av.valor_linea, "NIVEL DEL DÍA")]` más `(s.objetivo, "OBJETIVO")` si hay objetivo.
    - En `cerrado` y en `sin_direccion`, el gráfico va sin niveles.
  - `datos` agrega `"suceso": asdict(Resumen(...))` y deja de llevar `whatsapp`, `lectura_hoy`,
    `oportunidad_hoy`, `postura` y `plan_intradia`.
- [ ] **`redactar`:** si `"suceso" in datos`, devuelve
  `(con_saludo(st.whatsapp(Resumen(**datos["suceso"]), datos["nombre"]), saludo), "")`.
  Si no, sigue el camino de hoy.
- [ ] **`bot._seguimiento`:**
  - Si la pieza reusada no trae `suceso`, se prepara de nuevo (Review Focus 5).
  - El payload es `cm.payload_suceso(d["activo"], d["suceso"], d["edicion"], self.autor, chart)`,
    rendido con la plantilla `"seguimiento_dia"`.
  - `rg.anotar_seguimiento` no cambia.
- [ ] **Tests:**
  - `test_preparar_seguimiento_fija_suceso_y_lo_reutiliza`: con `Lectores` falsos y `tmp_path`.
  - `test_preparar_seguimiento_mercado_cerrado` (Review Focus 1): estado `cerrado` y ningún archivo
    escrito.
  - `test_preparar_seguimiento_sin_direccion`.
  - `test_preparar_seguimiento_nota_semana_solo_si_contraria`.
  - `test_redactar_usa_suceso`.
  - `test_bot_repara_pieza_vieja_sin_suceso`.
- [ ] **Retirar lo que quedó sin uso.**
  - Candidatos: `payload_seguimiento` y sus ayudantes, `templates/stories/seguimiento.html` con su
    fixture, `postura.py`, `oportunidad_de_hoy`, `texto_postura`, y `_intradia` con la base
    `referencias_diarias`.
  - Antes de borrar cada uno, `rg` en `scripts/`, `src/` y `tests/` para confirmar que nadie más lo
    usa. Lo que siga teniendo consumidores se queda y se anota en el informe.
- [ ] Suite completa en verde.

---

## Verificación final (orquestador)

1. Volver a correr la suite completa desde acá. No basta el informe de AGY.
2. `git diff --stat master`: no se tocó nada fuera de la tabla de archivos.
3. Rendir la lámina con datos reales de MT5 para el oro y el cobre, y mirar los PNG.
4. Medición: cuántos de los últimos 20 días hábiles habrían tenido línea A+ en 15m, cuántos solo
   B y cuántos ninguna.
5. Mostrarle al director la lámina, el texto y la medición. El PR se abre solo con su visto bueno.

## Cómo se despacha a AGY

1. **Prueba previa de un minuto.** Los subagentes solo se midieron en `--mode plan`. Antes del
   encargo real hay que comprobar que en `--mode accept-edits` un subagente puede escribir un
   archivo en el scratchpad. Si no puede, el encargo va en dos pasos: plan mode para el reparto y
   `--conversation <id>` en accept-edits para ejecutarlo.
2. **Un solo encargo con este plan entero.** Le pide que lea primero `.agents/rules/proyecto.md` y
   le ordena: "delega T1, T2 y T3 a un subagente propio cada una con `invoke_subagent`, en paralelo;
   T4 la haces tú cuando las tres estén en verde". Fija la rama, prohíbe `generate_image` y los
   commits, y le dice que no toque archivos fuera de la tabla.
3. Flags: `--model gemini-3.8-flash-high`, `--print-timeout 40m` y `--output-format stream-json`.
4. Por cada tarea, el orquestador revisa el diff, corre los tests y hace el commit.
