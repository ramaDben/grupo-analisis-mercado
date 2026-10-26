# Radar multifractal — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Una página HTML diaria (07:30 Santiago, L-V) con la matriz activo × marco (1H/4H/1D) de los símbolos del terminal que tocaron o están por tocar su línea de seguridad, de acción o una zona S/R del motor Tori.

**Architecture:** La detección vive dentro del motor (`scripts/estrategia/tori/radar.py`) y reutiliza `_estructura`, `trazar`, `detectar` y `_serie`, así los roles y las ventanas son los mismos que publican las piezas. Un orquestador (`scripts/radar_multifractal.py`) lee el universo de MT5, las velas con `estrategia.fuente.velas_mt5`, llama al motor por marco, compara con los objetos del indicador (`scripts/radar_paridad.py`) y rinde el HTML (`scripts/radar_html.py`). Una tarea propia del Programador de tareas (`GI-Radar`) lo dispara.

**Tech Stack:** Python 3 + pandas, paquete `MetaTrader5` (vía `uv run --with MetaTrader5`), pytest, PowerShell para el instalador.

**Spec:** `docs/superpowers/specs/2026-10-26-radar-multifractal-design.md`

## Global Constraints

- ATR: el simple de 14 de `pivotes._atr` (`Serie.atr`). Nunca Wilder.
- Tolerancia de toque diagonal: `Parametros.tolerancia_toque_atr` (0,25 ATR).
- Parámetros nuevos en `Parametros`: `radar_velas_max: int = 3`, `radar_k_atr: float = 1.0`, `media_zona_atr: float = 0.18`.
- Ventanas por marco = `MARCOS_INTRADIA.velas`: W1 156, D1 250, H4 180, H1 600. Marcos del radar: `("H1", "H4", "D1")`.
- Solo velas cerradas: la vela en curso la separa `estrategia.fuente.velas_mt5` (`partir_velas`).
- Cuenta: `mt5.account_info().login` contra `guardrails.cuenta.cuenta_correcta`; si no aprueba, no se escanea.
- El radar **nunca envía nada**: ningún import ni texto `enviar_whatsapp`, `whatsapp_sender`, `despachar`.
- Fuera de `scripts/estrategia/` no usar `direccion_tecnica`, `analizar_activo`, `_get_support_resistance`, `get_asset_levels` ni comparar contra `ema_50` (lo impone `tests/test_guardian_estrategia.py`).
- Precios: siempre del terminal, redondeados a `mt5.symbol_info(t).digits`. Ningún precio escrito a mano.
- Horas visibles en hora de Santiago (`estrategia.fuente.cierre_santiago`).
- Archivos de texto con acentos: `Path.write_text(..., encoding="utf-8")`. Nada de texto por la consola de PowerShell.
- Salida en `data/radar/` (gitignoreado). No se toca `mql5/GI_Canales_Seguridad.mq5`.
- Rama: `feat/radar-multifractal`. Nombres, docstrings y comentarios en español, con la densidad de comentarios del motor.

## Review Focus

1. **Símbolo con menos velas que la ventana** (listado nuevo, cripto reciente): va a fallas con el motivo, nunca se traza sobre historia parcial (test en Task 3).
2. **MT5 caído o en otra cuenta**: página de error que lo dice, no una matriz vacía (test en Task 6).
3. **ATR 0 o velas sin rango** (símbolo suspendido): falla de ese marco, el escaneo sigue (test en Task 3).
4. **`chart_objects.json` ausente o viejo**: la paridad lo informa al pie y el escaneo no se cae (test en Task 4).
5. **Excepción a mitad del escaneo**: los símbolos que no estaban en Observación de Mercado se restauran igual (test en Task 6).

---

### Task 1: Eventos sobre las diagonales

**Files:**
- Modify: `scripts/estrategia/tori/parametros.py` (agregar los tres campos de Global Constraints)
- Create: `scripts/estrategia/tori/radar.py`
- Test: `tests/test_tori_radar.py` (mismo encabezado de `sys.path` que `tests/test_tori_lineas.py`; usa `tests/velas_sinteticas.py`)

**Interfaces:**
- Consumes: `lineas.trazar`, `lectura._estructura`, `calidad.calificar`, `pivotes.Serie`.
- Produces:

```python
Linea_ = Literal["seguridad", "accion", "rango", "soporte", "resistencia"]

@dataclass(frozen=True)
class Evento:
    marco: str               # "H1" | "H4" | "D1"
    linea: Linea_
    tipo: Literal["toco", "por_tocar"]
    velas: int | None        # n de "por_tocar"; None en "toco"
    distancia_atr: float     # |último cierre − línea| / ATR (en "por_tocar", contra la línea proyectada a n)
    valor: float             # precio de la línea en la última vela cerrada, redondeado a digits
    calidad: str             # "A+" | "B" | ""
    detalle: str             # "rebote" | "rompió" | "retesteo" | ""

@dataclass(frozen=True)
class LineaRadar:
    rol: Linea_
    valor_actual: float      # en la última vela cerrada
    valor_abierta: float     # proyectada a la vela en curso (índice len(s)); para comparar con el gráfico

def diagonales(s: Serie, p: Parametros, marco: str, digits: int
               ) -> tuple[str, str, list[LineaRadar], list[Evento]]:
    """(estado, direccion, lineas, eventos) del marco, con los roles de `_estructura`."""
```

Reglas (spec §5, ya decididas):
- Líneas: `e.seguridad` → "seguridad"; `e.accion` → "accion"; cada `e.rango` → "rango". Estado y dirección son los de `_estructura` (`TENDENCIA`/`RUPTURA`/`RANGO`, `ALCISTA`/`BAJISTA`/`LATERAL`).
- **toco**: con `i = len(s) − 1`, `v = t.valor(i)`, `tol = p.tolerancia_toque_atr * s.atr`: `s.lows[i] − tol <= v <= s.highs[i] + tol`. `detalle`: `"retesteo"` si la línea es la rota de un `RUPTURA` (`not t.vigente`); si no, `"rebote"` cuando el cierre quedó del lado de la línea (sobre la alcista, bajo la bajista), y `"rompió"` en otro caso.
- **por_tocar** (solo si esa línea no generó "toco"): menor `n` en `1..p.radar_velas_max` con `abs(s.closes[i] − t.valor(i + n)) <= p.radar_k_atr * s.atr * n`.
- Una línea no vigente fuera de `RUPTURA` no genera eventos (`_estructura` ya no la devuelve).
- `calidad` de `calificar(t, s, p).calidad`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_toque_alcista_con_rebote_es_evento_de_seguridad(): ...
    # serie que termina con la última vela tocando la alcista principal y cerrando arriba
    # → un Evento(linea="seguridad", tipo="toco", detalle="rebote", velas=None)
def test_toque_que_cierra_al_otro_lado_es_rompio(): ...
def test_por_tocar_reporta_el_menor_numero_de_velas(): ...
    # cierre a ~1,5 ATR de la línea → velas == 2
def test_a_mas_de_tres_velas_no_hay_evento(): ...
def test_una_linea_que_toco_no_repite_por_tocar(): ...
def test_la_linea_rota_en_ruptura_se_marca_retesteo(): ...
    # reutilizar BAJISTA_ROTA de test_tori_lineas.py con un retroceso final hacia la línea
def test_los_roles_son_los_de_estructura():
    # para la misma serie, linea "seguridad" de diagonales() == e.seguridad de _estructura()
```

- [ ] **Step 2:** `uv run pytest tests/test_tori_radar.py -v` → FAIL (`ModuleNotFoundError: estrategia.tori.radar`).
- [ ] **Step 3:** Implementar `Evento`, `LineaRadar` y `diagonales` en `scripts/estrategia/tori/radar.py`, y los tres campos en `Parametros`.
- [ ] **Step 4:** `uv run pytest tests/test_tori_radar.py tests/test_tori_lineas.py tests/test_tori_lectura.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(radar): eventos sobre las diagonales de Tori`.

### Task 2: Eventos sobre las zonas S/R

**Files:**
- Modify: `scripts/estrategia/tori/radar.py`
- Test: `tests/test_tori_radar.py`

**Interfaces:**
- Consumes: `horizontales.detectar`, `Evento`, `LineaRadar` (Task 1).
- Produces: `def zonas(s: Serie, p: Parametros, marco: str, digits: int) -> tuple[list[LineaRadar], list[Evento]]`

Reglas (spec §5): `m = p.media_zona_atr * s.atr`. Solo **el soporte más cercano bajo el cierre y la resistencia más cercana sobre él**, entre los de `detectar(s, p)`.
- **toco**: el par se elige con el cierre **anterior** (`s.closes[-2]`); evento si `[low, high]` de la última vela intersecta `[nivel − m, nivel + m]`. `calidad=""`, `detalle=""`.
- **por_tocar**: el par se elige con el último cierre; `d = max(0, abs(cierre − nivel) − m)`; `n = ceil(d / (p.radar_k_atr * s.atr))`, evento si `1 <= n <= p.radar_velas_max`. Un nivel que ya dio "toco" no repite.
- `LineaRadar` del par vigente (con el último cierre), `valor_abierta = valor_actual`.

- [ ] **Step 1: Tests que fallan**

```python
def test_vela_que_entra_a_la_zona_de_soporte_es_toco(): ...
def test_zona_cruzada_en_la_ultima_vela_cuenta_como_toco(): ...
    # el cierre anterior estaba sobre el soporte y el último bajo él → toco "soporte"
def test_solo_cuentan_el_soporte_y_la_resistencia_mas_cercanos(): ...
    # tres niveles bajo el precio → como mucho un evento "soporte"
def test_por_tocar_mide_contra_el_borde_de_la_zona(): ...
    # cierre a 1,18 ATR del nivel → d = 1,0 ATR → velas == 1
```

- [ ] **Step 2:** `uv run pytest tests/test_tori_radar.py -v` → FAIL (`zonas` no existe).
- [ ] **Step 3:** Implementar `zonas`.
- [ ] **Step 4:** `uv run pytest tests/test_tori_radar.py tests/test_tori_horizontales.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(radar): eventos sobre las zonas de soporte y resistencia`.

### Task 3: Lectura de un marco desde las velas, y paridad con `leer()`

**Files:**
- Modify: `scripts/estrategia/tori/radar.py`
- Test: `tests/test_tori_radar.py`

**Interfaces:**
- Consumes: `diagonales`, `zonas`, `lectura._serie`, `pivotes.inicio_tras_salto`, `MARCOS_INTRADIA`, `AVISO_SALTO` (de `estrategia.tori.lectura`).
- Produces:

```python
MARCOS_RADAR = MARCOS_INTRADIA            # W1 156, D1 250, H4 180, H1 600
RADAR_MARCOS: tuple[str, ...] = ("H1", "H4", "D1")

class HistoriaInsuficiente(ValueError): ...

@dataclass(frozen=True)
class LecturaMarco:
    marco: str
    estado: str
    direccion: str
    lineas: tuple[LineaRadar, ...]
    eventos: tuple[Evento, ...]
    avisos: tuple[str, ...]   # AVISO_SALTO si la ventana se cortó por un salto de datos
    vela: int                 # apertura (hora servidor) de la última vela cerrada
    atr: float

def leer_marco(velas: dict[str, pd.DataFrame], marco: str, digits: int,
               p: Parametros = PARAMETROS) -> LecturaMarco:
```

- Si `len(velas[marco]) < MARCOS_RADAR.velas[marco]` → `HistoriaInsuficiente(f"{marco}: {n} velas de {req}")`, **antes** del corte por salto (spec §6). El corte por salto se acepta y deja `AVISO_SALTO`.
- ATR 0 → `ValueError` con el mismo texto que `lectura.leer`.
- Solo las líneas propias del marco; las de contexto no se agregan.

- [ ] **Step 1: Tests que fallan**

```python
def test_historia_corta_lanza_historia_insuficiente(): ...
def test_velas_sin_rango_lanzan_valueerror(): ...
def test_el_salto_de_datos_deja_aviso_y_no_falla(): ...
def test_paridad_con_leer_en_4h():
    # mismas velas sintéticas (W1, D1, H4): crear().leer(...) y leer_marco(velas, "H4", ...)
    # → misma direccion, y el valor_actual de seguridad/accion de leer_marco
    #   == el de las Linea con rol "seguridad"/"accion" de la Lectura
def test_paridad_con_leer_en_1h():
    # idem con crear_intradia() y "H1"
```

- [ ] **Step 2:** `uv run pytest tests/test_tori_radar.py -v` → FAIL.
- [ ] **Step 3:** Implementar `MARCOS_RADAR`, `RADAR_MARCOS`, `HistoriaInsuficiente`, `LecturaMarco`, `leer_marco`.
- [ ] **Step 4:** `uv run pytest tests/test_tori_radar.py tests/test_guardian_estrategia.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(radar): lectura por marco con la ventana que publican las piezas`.

### Task 4: Paridad con el indicador de MT5

**Files:**
- Create: `scripts/radar_paridad.py`
- Test: `tests/test_radar_paridad.py` (fixture JSON en `tests/fixtures/radar/chart_objects.json`)

**Interfaces:**
- Consumes: `LecturaMarco`, `LineaRadar` (Task 3).
- Produces:

```python
NOMBRES_INDICADOR: dict[str, str]   # nombre de objeto del indicador -> rol
def ruta_objetos() -> Path | None:   # $MT5_COMMON_FILES/chart_objects.json; carga antes mt5_client.cargar_env()
def leer_objetos(ruta: Path | None, ahora: datetime) -> dict | str   # dict, o el motivo por el que no se pudo
def comparar(objetos: dict, lecturas: dict[tuple[str, str], LecturaMarco],
             digits: dict[str, int], p: Parametros) -> list[str]
```

- Antes de fijar `NOMBRES_INDICADOR`, confirmar con `grep -n "GI_TV_" mql5/GI_Canales_Seguridad.mq5` los nombres exactos de seguridad, acción, soporte y resistencia. `GI_Risk_Cockpit.mq5:233-261` los cita como `GI_TV_DIAG_SEGURIDAD`, `GI_TV_DIAG_ACCION`, `GI_TV_LINE_SOPORTE`, `GI_TV_LINE_RESISTENCIA`.
- `leer_objetos`: si `ruta` es None o falta el archivo → `"no se pudo verificar la paridad: falta chart_objects.json (¿corre ChartObjectsExporter?)"`. Si `generated_at` tiene más de 3600 s → `"no se pudo verificar la paridad: chart_objects.json tiene N min"`. Mismo umbral que `tools/chart_objects._STALE_SECONDS`.
- `comparar`: por cada gráfico (`symbol`, `timeframe`) con lectura del radar y cada `trendlines[].name` de `NOMBRES_INDICADOR`, compara `valor_actual` del indicador (que está en la vela en curso) contra `LineaRadar.valor_abierta` del mismo rol. Si la diferencia es mayor que `p.tolerancia_toque_atr * lectura.atr`, emite `"XAUUSD H4: indicador y motor difieren en la línea de seguridad: <a> vs <b>"`, con los `digits` del símbolo. Si el rol existe en un solo lado, emite `"... la línea de acción solo está en el indicador/motor"`.

- [ ] **Step 1: Tests que fallan**

```python
def test_sin_archivo_devuelve_el_motivo(): ...
def test_archivo_viejo_devuelve_el_motivo(): ...
def test_lineas_que_coinciden_no_emiten_nada(): ...
def test_diferencia_mayor_que_la_tolerancia_se_informa_con_digits(): ...
def test_linea_presente_en_un_solo_lado_se_informa(): ...
def test_graficos_sin_lectura_del_radar_se_ignoran(): ...
```

- [ ] **Step 2:** `uv run pytest tests/test_radar_paridad.py -v` → FAIL.
- [ ] **Step 3:** Implementar `scripts/radar_paridad.py`.
- [ ] **Step 4:** `uv run pytest tests/test_radar_paridad.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(radar): control de paridad con el indicador de MT5`.

### Task 5: Orden de filas y página HTML

**Files:**
- Create: `scripts/radar_html.py`
- Test: `tests/test_radar_html.py`

**Interfaces:**
- Consumes: `LecturaMarco`, `Evento`, `RADAR_MARCOS`.
- Produces:

```python
@dataclass(frozen=True)
class Fila:
    ticker: str
    categoria: str                       # primer tramo de symbol_info.path
    digits: int
    marcos: dict[str, LecturaMarco]      # solo los marcos que se pudieron leer
    cierres: dict[str, datetime]         # marco -> cierre de la última vela, en Santiago

@dataclass(frozen=True)
class Falla:
    ticker: str
    marco: str | None                    # None: falló el símbolo entero
    motivo: str

@dataclass(frozen=True)
class Escaneo:
    inicio: datetime                     # Santiago
    duracion_s: float
    cuenta: int
    leidos: int
    filas: tuple[Fila, ...]
    fallas: tuple[Falla, ...]
    paridad: tuple[str, ...]

def ordenar(filas: Iterable[Fila]) -> list[Fila]
def render(e: Escaneo) -> str
def render_error(titulo: str, motivo: str, inicio: datetime) -> str
```

- `ordenar` deja fuera las filas sin eventos. Ordena por: número de marcos con al menos un evento (desc), luego si tiene algún "toco" (primero), luego el menor `velas` de sus "por_tocar".
- `render` sigue el boceto aprobado (`.superpowers/brainstorm/*/content/radar-v2.html`):
  - Encabezado: fecha y hora en Santiago, `leidos`, cuántos con actividad, cuántos fallaron, `cuenta`, duración.
  - Columnas: Confluencia, 1H, 4H, 1D.
  - Flecha de dirección del marco mayor con lectura (D1 > H4 > H1): ⬆️ ALCISTA, ⬇️ BAJISTA, ↔️ LATERAL.
  - Por celda, el evento más urgente ("toco" antes que el de menos velas), con la franja de color: seguridad `#26C6A0`, acción `#FF4D5E`, S/R `#FFD54F`, rango gris `#CBD5E1`. El texto dice "✅ tocó <línea>" o "<línea> a N velas", el `valor` formateado con `digits` y calidad o detalle. El resto de los eventos va en un `<details>`.
  - Cada celda muestra la hora de cierre de su vela.
  - Al pie: fallas con motivo, paridad, leyenda.
  - Si `len(fallas) > leidos / 2`, va arriba de todo el aviso "Lectura incompleta: no confíes en la ausencia de un activo".
  - Todo CSS inline, sin dependencias externas. Usar `html.escape` para los textos.

- [ ] **Step 1: Tests que fallan**

```python
def test_las_filas_sin_eventos_no_aparecen(): ...
def test_tres_marcos_van_antes_que_dos_y_toco_antes_que_por_tocar(): ...
def test_el_valor_respeta_digits_sin_truncar_ceros(): ...   # digits=2, 1.5 -> "1.50"
def test_mas_de_la_mitad_de_fallas_muestra_aviso_de_lectura_incompleta(): ...
def test_cero_actividad_dice_cuantos_se_leyeron(): ...      # "137 leídos · 0 con actividad"
def test_la_celda_muestra_la_hora_de_su_vela(): ...
```

- [ ] **Step 2:** `uv run pytest tests/test_radar_html.py -v` → FAIL.
- [ ] **Step 3:** Implementar `scripts/radar_html.py`.
- [ ] **Step 4:** `uv run pytest tests/test_radar_html.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(radar): matriz HTML ordenada por confluencia`.

### Task 6: Orquestador: universo, cuenta, escaneo y CLI

**Files:**
- Create: `scripts/radar_multifractal.py`
- Modify: `.gitignore` (agregar `data/radar/`)
- Test: `tests/test_radar_multifractal.py`

**Interfaces:**
- Consumes: `leer_marco`, `HistoriaInsuficiente`, `MARCOS_RADAR`, `RADAR_MARCOS` (Task 3), `comparar`/`leer_objetos`/`ruta_objetos` (Task 4), `Fila`/`Falla`/`Escaneo`/`ordenar`/`render`/`render_error` (Task 5), `estrategia.fuente.velas_mt5`, `offset_servidor`, `cierre_santiago`, `RELOJ`, `guardrails.cuenta.cuenta_correcta`.
- Produces:

```python
@dataclass(frozen=True)
class Simbolo:
    ticker: str
    digits: int
    categoria: str
    visible: bool             # estaba en Observación de Mercado antes de empezar

def universo(mt5) -> list[Simbolo]            # symbols_get() con trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
def escanear(simbolos: list[Simbolo], mt5, leer_velas=velas_mt5,
             ahora: Callable[[], datetime] = ...) -> Escaneo
def main(argv: list[str] | None = None) -> int
```

- `escanear` hace una sola llamada `leer_velas(ticker, MARCOS_RADAR)` por símbolo, que trae W1/D1/H4/H1 cerradas. Después corre `leer_marco` por cada uno de `RADAR_MARCOS`:
  - `HistoriaInsuficiente` o `ValueError` de un marco van a `Falla(ticker, marco, str(exc))`.
  - Una excepción de `leer_velas` va a `Falla(ticker, None, ...)`.
  - El símbolo siguiente se lee igual.
- Los cierres visibles se calculan con `cierre_santiago(lectura.vela, marco, offset)`. El `offset` se mide una vez con `offset_servidor(symbol_info_tick(RELOJ).time, time.time())`.
- **Restauración**: en un `finally`, `mt5.symbol_select(t, False)` para cada `Simbolo` con `visible=False`.
- `main` acepta `--simbolos A,B`, `--sin-abrir` y `--salida <ruta>`:
  1. Llama a `mt5_client.connect()`. Si falla, escribe `render_error("MT5 no responde", ...)`.
  2. Llama a `cuenta_correcta(mt5.account_info().login)`. Si no aprueba, escribe `render_error("Cuenta MT5 inesperada", veredicto.motivo)` sin escanear.
  3. Escanea, compara la paridad y rinde.
  4. Escribe en `data/radar/<AAAA-MM-DD>/radar_<HH-MM>.html` y copia a `data/radar/ultimo.html` con `encoding="utf-8"`.
  5. Si no hay `--sin-abrir`, abre la página con `webbrowser.open`.
  6. Imprime la ruta y devuelve 0. Devuelve 1 si escribió una página de error.
- Usar `getattr(veredicto, ...)` según la API real de `guardrails/veredicto.py`: leerla antes de implementar.

- [ ] **Step 1: Tests que fallan** (con un `mt5` falso, sin terminal)

```python
def test_universo_filtra_trade_mode_full_y_toma_categoria_del_path(): ...
def test_un_simbolo_que_falla_no_corta_el_escaneo(): ...
def test_historia_insuficiente_queda_como_falla_del_marco(): ...
def test_restaura_observacion_de_mercado_aunque_haya_excepcion():
    # leer_velas lanza a mitad → symbol_select(t, False) se llamó para los visible=False
def test_cuenta_distinta_escribe_pagina_de_error_y_no_escanea(tmp_path): ...
def test_el_radar_no_puede_enviar_nada():
    fuente = (RAIZ / "scripts" / "radar_multifractal.py").read_text(encoding="utf-8")
    for prohibido in ("enviar_whatsapp", "whatsapp_sender", "despachar"):
        assert prohibido not in fuente
```

- [ ] **Step 2:** `uv run pytest tests/test_radar_multifractal.py -v` → FAIL.
- [ ] **Step 3:** Implementar `scripts/radar_multifractal.py` y agregar `data/radar/` al `.gitignore`.
- [ ] **Step 4:** `uv run pytest tests/test_radar_multifractal.py tests/test_guardian_estrategia.py -v` → PASS. Después la suite completa: `uv run pytest -q` → sin fallas nuevas respecto de `master`. Si hay fallas previas, anotarlas sin taparlas.
- [ ] **Step 5:** Commit `feat(radar): orquestador del escaneo multifractal`.

### Task 7: Tarea programada `GI-Radar`

**Files:**
- Create: `scripts/instalar_radar.ps1`

Mismo esqueleto que `scripts/instalar_reloj.ps1`: `-Instalar` y `-Quitar`; sin parámetros solo muestra la vista previa. Usa `uvw.exe` y el directorio del repo. Diferencias:
- `$Tarea = "GI-Radar"`.
- Argumentos: `run --with MetaTrader5 python scripts/radar_multifractal.py --sin-abrir`.
- Disparador: `New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 07:30`. 07:30 siempre existe en Santiago, porque el cambio de horario ocurre a medianoche.
- Settings: los mismos del reloj, `-StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew`, con `-ExecutionTimeLimit (New-TimeSpan -Minutes 30)`.
- En la cabecera, un comentario de por qué no es un momento del reloj (spec §4.3).

- [ ] **Step 1:** `powershell -File scripts/instalar_radar.ps1` → imprime la vista previa (tarea, comando, días, 07:30) y **no registra nada**. Verificar con `Get-ScheduledTask -TaskName GI-Radar`, que no debe existir.
- [ ] **Step 2:** Commit `feat(radar): instalador de la tarea GI-Radar`.
- [ ] **Step 3:** **No registrar la tarea** sin la aprobación explícita del director. Ofrecerle `scripts\instalar_radar.ps1 -Instalar`.

### Task 8: Verificación en vivo

Sin código nuevo, salvo correcciones que resulten de la corrida.

- [ ] **Step 1:** Con MT5 abierto en la cuenta 51257, corre `uv run --with MetaTrader5 python scripts/radar_multifractal.py --simbolos XAUUSD,USDCLP,#NVDA --sin-abrir`. Tiene que terminar con código 0 y dejar la página escrita. Ábrela y revisa a ojo:
  - que las tildes, el `·` y las flechas se vean bien;
  - que las horas estén en Santiago;
  - que los precios tengan los `digits` correctos.
- [ ] **Step 2:** Con los gráficos de XAUUSD H4 y USDCLP H1 abiertos con `GI_Canales_Seguridad` y el Service `ChartObjectsExporter` corriendo, corre la misma línea. Revisa la sección de paridad y anota si el exportador entrega los objetos `GI_TV_*`. Esto confirma o descarta la verificación pendiente del spec §7.
- [ ] **Step 3:** Corrida completa sin `--simbolos`. Anota la duración que muestra la página y cuántos símbolos fallaron, con sus motivos. Si tarda más de 5 minutos, repórtalo al director antes de optimizar (spec §8).
- [ ] **Step 4:** Lleva al director la página, la duración, las fallas y el resultado de la paridad.
