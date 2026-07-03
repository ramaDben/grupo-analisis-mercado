# Diseño técnico — market-data: `get_symbol_spec` (especificaciones de contrato y sesiones) (#104)

> Formaliza el diseño de los requisitos fijados en `spec.md` (fases explore/propose/specify ya
> cerradas). Este documento **no contiene código de implementación**: fija decisiones
> arquitectónicas (ADR), el contrato observable de la tool, la resolución de las preguntas
> abiertas `Q1..Q5` del `spec.md` y el desglose de tareas mapeado a los requisitos `R1..R11` y a
> los criterios de aceptación `AC1..AC13`.
>
> **Dominio Pulse:** market-data · **Bump sugerido:** minor (`type:feat`, tool aditiva) ·
> **Gate:** las dos decisiones del gate humano `DESIGN → APPLY` (§10, D-GATE-1 y D-GATE-2)
> fueron **aceptadas por el director el 2026-07-02** según la recomendación del diseñador.

---

## 1. Contexto y decisión (ADR)

### Estado
Aceptado — aprobado por el director el 2026-07-02. D-GATE-1 y D-GATE-2 aceptados como los
recomienda el diseñador (ver §10).

### Contexto
El MCP `market-data` no puede responder de forma determinista "¿opera el activo X en la fecha Y y
en qué horario (hora Chile)?". Hoy solo existe `horario_mercado` como string libre y estático en
`config/activos.json`, sin fuente en el broker y sin noción de feriados. Esto obligó (2026-07-02) a
redactar el aviso de `/dato_macro` del feriado NYSE del 3 de julio con lenguaje de cobertura en vez
de una afirmación verificada (`data/mensajes/2026-07-02/us100/dato_macro/16-59_dato_macro.txt`),
violando la regla de oro de análisis accionable y sin ambigüedad.

La API Python de MetaTrader5 separa **specs estáticas** (`symbol_info`) de **sesiones recurrentes
por día de semana** (`symbol_info_session_quote/trade`), y **no tiene noción nativa de feriado
puntual por fecha**: un feriado de un solo día no altera la tabla de sesión recurrente del broker
por adelantado. Por eso responder "¿opera el 3-jul-2026?" exige cruzar tres señales, no una.

### Decisión
Agregar **una** tool nueva `get_symbol_spec(ticker, fecha=None)` al MCP `market-data`, siguiendo
exactamente el patrón hexagonal de las 3 tools existentes:

- **Adapter MT5** (`mt5_client.py`): dos funciones nuevas de I/O con import perezoso de
  `MetaTrader5` — `get_symbol_info(ticker)` y `get_session(ticker, day_of_week, index, tipo)`.
- **Service/tool** (`tools/symbol_spec.py`): un módulo con `register(mcp)` que orquesta las tres
  señales (patrón semanal MT5 · calendario de feriados versionado · `trade_mode` en vivo),
  convierte a hora Chile y arma el payload / contrato de error.
- **Dato versionado** (`config/feriados_bolsa.json`): calendario NYSE 2026 (solo cierres totales).
- **Mapeo ticker → exchange**: constante en `symbol_spec.py` (no en `activos.json`).

Se combinan **tres señales complementarias** en vez de depender de una sola fuente, resolviendo el
caso que originó el issue (acciones + US100) sin añadir dependencias nuevas.

### Consecuencias
- **Positivas**: contrato determinista para el 90%+ de los avisos de feriado que necesita
  `/dato_macro`; refuerza `catalog.py` (expone `digits`, `volume_min/step`, `contract_size` desde
  la fuente viva); cero dependencias nuevas; cero cambios en consumidores existentes (aditivo).
- **Negativas / límites aceptados**: `USDCLP`, `XAUUSD`, `WTI.spot` no tienen calendario de
  feriados esta iteración (limitación documentada, R11); el calendario NYSE se mantiene a mano (~10
  fechas/año); no se modela cierre parcial / medio día.

---

## 2. Arquitectura propuesta (encaje hexagonal)

Dependencia unidireccional respetada: **tool (application/service) → adapter MT5 → stdlib**. El
adapter (`mt5_client.py`) es el único que toca `MetaTrader5`; la tool nunca importa `MetaTrader5`
directamente (igual que `levels.py` importa `get_rates` desde el adapter).

```
server.py                      # composición: import symbol_spec + symbol_spec.register(mcp)  (R1, R10)
  └─ tools/symbol_spec.py      # SERVICE: orquesta señales, convierte a Chile, arma payload/error
        ├─ catalog.VALID_TICKERS        # validación de ticker (R2) — fuente única existente
        ├─ mt5_client.get_symbol_info   # ADAPTER I/O (R9) — import perezoso de MetaTrader5
        ├─ mt5_client.get_session       # ADAPTER I/O (R9) — import perezoso de MetaTrader5
        ├─ config/feriados_bolsa.json   # DATO versionado (R6) — leído con json + pathlib
        └─ zoneinfo.ZoneInfo("America/Santiago")   # conversión determinista (RNF2)
```

**Archivos afectados**
| Archivo | Acción | Requisito |
|---|---|---|
| `src/market_data_mcp/tools/symbol_spec.py` | **nuevo** — módulo de la tool | R1–R8, R11 |
| `src/market_data_mcp/mt5_client.py` | editar — 2 funciones nuevas | R9 |
| `src/market_data_mcp/server.py` | editar — import + register + `instructions` | R1, R10 |
| `config/feriados_bolsa.json` | **nuevo** — calendario NYSE 2026 | R6 |
| `tests/test_symbol_spec.py` | **nuevo** — cobertura BDD | AC1–AC13, RNF5 |

**Sin cambios**: `catalog.py`, `config/activos.json` (coexiste `horario_mercado` como fallback
documental), las 3 tools existentes, `tests/test_server.py` (debe seguir verde sin tocarlo, RNF4).

---

## 3. Contrato de la tool `get_symbol_spec`

### 3.1 Firma
`get_symbol_spec(ticker: str, fecha: str | None = None) -> dict[str, Any]`

### 3.2 Respuesta sin `fecha` (specs estáticas + patrón semanal) — R3
Claves mínimas: `ticker`, `trade_mode`, `digits`, `volume_min`, `volume_step`, `contract_size`,
`server_time`, `server_utc_offset_minutes`, `sesiones_semana`, `fuente` (`"mt5"`).

`sesiones_semana` (R3.1): dict con las **7 claves fijas en español sin tilde**, en orden
`lunes, martes, miercoles, jueves, viernes, sabado, domingo`. Cada valor es una **lista** (0/1/N
elementos) de `{"quote": [apertura, cierre], "trade": [apertura, cierre]}`, en `"HH:MM"` 24h **ya
convertidos a `America/Santiago`**. Día sin sesión → lista vacía `[]` (nunca `null` ni clave
ausente).

### 3.3 Respuesta con `fecha` (ISO `YYYY-MM-DD`) — R4
Todas las claves de R3 **más**: `fecha_consultada`, `opera` (bool), `motivo`
(`null | "feriado_bolsa" | "fin_de_semana" | "fuera_de_sesion_recurrente" | "trade_mode_disabled"`),
`horario_chile` (`null` u `{"apertura","cierre"}` de la **primera** ventana `trade` del día),
`calendario_feriados_fuente` (`"config/feriados_bolsa.json (NYSE)"` si el ticker está mapeado; si
no, `null`).

### 3.4 Contrato de error — R7 (uniforme con las 3 tools existentes)
| Código | Cuándo |
|---|---|
| `TICKER_NOT_FOUND` | `ticker` fuera de `catalog.VALID_TICKERS` (mismo criterio que `levels.py:105`) |
| `INVALID_FECHA` | `fecha` no `None` y no parsea como ISO `YYYY-MM-DD` estricto (incl. `2026-02-30`, `DD-MM-YYYY`, no-string) |
| `MT5_UNAVAILABLE` | `MetaTrader5` no instalado (`ImportError`) o sin conexión/terminal (mismo criterio que `levels.py:130-150`) |
| `SESSION_UNAVAILABLE` | MT5 disponible pero `symbol_info_session_*` no devuelve datos de sesión para el símbolo |

Forma: `{"error": "CÓDIGO", "message": <str no vacío>}`. Nunca `None` ni array vacío silencioso.

### 3.5 Orden de validación observable — R8
1. `ticker` contra catálogo → `TICKER_NOT_FOUND`.
2. Si `fecha is not None`: parseo ISO estricto **sin tocar MT5** → `INVALID_FECHA`.
3. Import/conexión MT5 (`get_symbol_info`) → `MT5_UNAVAILABLE`.
4. Datos de sesión del símbolo (`get_session`) → `SESSION_UNAVAILABLE`.
5. Construcción de la respuesta (R3, y R4 si aplica `fecha`).

---

## 4. Algoritmo determinista de `opera` (resuelve R4.1 sin ambigüedad)

R4.1 lista el orden `patrón semanal → feriado → trade_mode` pero además exige que **el feriado
gane** cuando ambas señales aplican (CB-9). Para eliminar toda ambigüedad, la implementación evalúa
la **precedencia del feriado primero**, lo que satisface todos los AC/CB simultáneamente:

```
Precondición: se resolvió sesiones_semana (R3) y el día-de-semana de `fecha`.

1. FERIADO (máxima prioridad):
   si ticker está mapeado a un exchange cubierto  Y  fecha ∈ feriados[exchange]:
       → opera=false, motivo="feriado_bolsa"        # CB-9, AC5 (viernes feriado gana)
2. PATRÓN SEMANAL:
   si sesiones_semana[<dia>] == []:
       → opera=false
         motivo = "fin_de_semana" si <dia> ∈ {sabado, domingo}   # AC6, CB-5
                  "fuera_de_sesion_recurrente" en otro caso        # CB-6
3. TRADE_MODE EN VIVO (solo si fecha == hoy en America/Santiago):
   si trade_mode == "DISABLED":
       → opera=false, motivo="trade_mode_disabled"   # CB-4, AC8
   (para fecha ≠ hoy esta señal NO se evalúa — no se puede anticipar trade_mode futuro)
4. En otro caso:
       → opera=true, motivo=null,
         horario_chile = primera ventana `trade` de sesiones_semana[<dia>]  # AC4
```

Justificación de poner el feriado primero: es la única forma de honrar "el feriado siempre gana
sobre el patrón semanal" (R4.1 §2 y CB-9) manteniendo determinismo; en la práctica los feriados
NYSE caen en día hábil con sesión, así que el reordenamiento no altera ningún otro AC. Un ticker no
mapeado nunca entra al paso 1 y `calendario_feriados_fuente` queda `null` (CB-3, AC7).

**Mapeo día-de-semana**: `datetime.fromisoformat(fecha).weekday()` (0=lunes…6=domingo) indexa las
7 claves en español. Para llamar a MT5 se traduce a la convención MT5 (`day_of_week` 0=domingo…
6=sábado) en el adapter/service (ver Q2 §5.2).

---

## 5. Resolución de las preguntas abiertas del `spec.md`

### 5.1 Q1 — Mapeo `SYMBOL_TRADE_MODE_*` → 5 strings legibles (R3 `trade_mode`)
Constante cerrada y exhaustiva en `symbol_spec.py`, indexada por el valor entero que devuelve
`symbol_info(...).trade_mode`:

| Entero MT5 | Constante `MetaTrader5` | String expuesto |
|---|---|---|
| 0 | `SYMBOL_TRADE_MODE_DISABLED` | `"DISABLED"` |
| 1 | `SYMBOL_TRADE_MODE_LONGONLY` | `"LONGONLY"` |
| 2 | `SYMBOL_TRADE_MODE_SHORTONLY` | `"SHORTONLY"` |
| 3 | `SYMBOL_TRADE_MODE_CLOSEONLY` | `"CLOSEONLY"` |
| 4 | `SYMBOL_TRADE_MODE_FULL` | `"FULL"` |

Se mapea por **entero literal** (no importando las constantes de `MetaTrader5`) para que
`symbol_spec.py` sea importable y testeable sin el paquete (RNF1). Un valor fuera de {0..4}
(improbable) se trata como dato de sesión/símbolo inválido → se documenta como caída a
`SESSION_UNAVAILABLE` o `trade_mode` = string crudo `"UNKNOWN"`; **decisión de diseño: exponer
`"DISABLED"` solo para el 0 y `"UNKNOWN"` para valores inesperados, nunca romper el contrato**.
> Verificar los enteros contra la versión de `MetaTrader5` instalada en la máquina del director
> antes de Apply (son estables desde hace años, pero se confirma en Apply, no bloquea Design).

### 5.2 Q2 — Múltiples sub-sesiones por día (R3.1, Riesgo R-3)
`get_session(ticker, day_of_week, index, tipo)` se itera con `index = 0, 1, 2, …` **hasta que MT5
devuelve `None`/error** para ese índice; cada ventana válida se agrega a la lista del día. Así
`sesiones_semana[<dia>]` soporta 0/1/N ventanas sin cambiar el contrato. `horario_chile` (R4) usa
**la primera ventana `trade`** del día (índice 0). El mapeo Python→MT5 de día de semana:
`mt5_dow = (python_weekday + 1) % 7` (Python 0=lunes→MT5 1; Python 6=domingo→MT5 0).
> Confirmar contra 2-3 tickers reales (ej. `US100.spot`, `#AAPL`, `USDCLP`) si algún símbolo
> reporta >1 ventana/día relevante; si así fuera, `horario_chile` seguiría usando la primera
> ventana `trade` (no cambia el contrato). Confirmación en Apply.

### 5.3 Q3 — Ubicación del mapeo ticker → exchange (R5)
**Constante módulo-nivel en `symbol_spec.py`** (no campo nuevo en `activos.json`). Razón: no acoplar
el catálogo de activos a la lógica de feriados; el mapeo es lógica de esta tool, cambia con el
alcance de feriados, y mantenerlo junto al código que lo consume es más simple de testear. Forma:
un `dict[str, str]` (o `set` por exchange) `{"US100.spot": "NYSE", "#AAPL": "NYSE", …}` con **16
tickers**: los 14 de R5 más `US500.spot` y `US30.spot` (D-GATE-1 aceptado, §10). Consultar el
mapeo es O(1) y no requiere leer `activos.json`.

### 5.4 Q4 — Caché de `get_symbol_info`/sesiones (Riesgo/Alcance)
**Sin caché en esta iteración (YAGNI).** A diferencia de `calendar.py` (fetch HTTP a Investing.com,
TTL 1h justificado), `symbol_info`/`symbol_info_session_*` son llamadas IPC locales al terminal MT5
(baratas) y el `trade_mode` en vivo **requiere** lectura fresca para CB-4/AC8. Cachear introduciría
riesgo de servir `trade_mode` obsoleto sin beneficio de rendimiento medible. Se documenta como
diferible si en el futuro se detecta costo.

### 5.5 Q5 — Extender mapeo NYSE a `US500.spot`/`US30.spot` (Riesgo R-1) → **RESUELTO: SÍ**
D-GATE-1 aceptado por el director (2026-07-02): el mapeo NYSE cubre los **3 índices US**
(`US100.spot`, `US500.spot`, `US30.spot`) más las 13 acciones — 16 tickers en total (§5.3, §10).

---

## 6. Manejo de zona horaria (RNF2) — decisión de diseño

Las sesiones MT5 vienen en **hora del servidor del broker** (no UTC, no Chile). Conversión
determinista con `zoneinfo`, nunca offsets fijos (mismo principio que `calendar.py:132-135`):

1. Derivar el **offset del servidor** (`server_utc_offset_minutes`, R3) comparando el tiempo del
   servidor MT5 (p. ej. `symbol_info(...).time`, epoch, o `mt5.symbol_info_tick`) contra
   `datetime.now(timezone.utc)`, redondeado a la resolución de minutos. Se expone **crudo** para
   trazabilidad (RNF2).
2. Cada endpoint de sesión (minutos desde medianoche en hora servidor) se ancla a una **fecha de
   referencia** (para `sesiones_semana`: hoy; para R4: la `fecha` consultada), se construye como
   `datetime` con `timezone(timedelta(minutes=offset))` y se `astimezone(ZoneInfo("America/Santiago"))`;
   se formatea `"%H:%M"`.
3. **Límite conocido documentado**: si tras convertir, una ventana cruza la medianoche o cambia de
   día de semana (posible con offsets grandes), esta iteración conserva el `HH:MM` de pared bajo la
   **misma clave de día** que reporta MT5 y **no** modela el corrimiento de día (coherente con el
   OUT "cierre parcial / medio día"). Para los tickers del caso motivador (US100/acciones NYSE, ET
   ≈ Chile ±1h) las ventanas quedan el mismo día (AC4: 09:30-16:00 ET → 10:30-17:00 CLT).

`server_time` (R3) = hora del servidor MT5 en el momento de la consulta, `"YYYY-MM-DD HH:MM:SS"`.

---

## 7. Alternativas consideradas

Heredadas de `proposal.md` (§Alternativas) y confirmadas en Design:
1. **Solo patrón semanal MT5 (inferir feriados de sesión vacía)** — descartada: no anticipa
   feriados puntuales (el caso que originó el issue).
2. **Dependencia `pandas_market_calendars`** — descartada: dependencia nueva; su cobertura puede no
   coincidir con las sesiones reales del broker; mantener ~10 fechas/año a mano es trivial.
3. **Cruzar con `obtener_calendario_macro` (Investing.com) para feriados** — descartada: Investing
   no tiene campo fiable de "bolsa cerrada por feriado"; sería frágil e indirecto.
4. **Exponer como MCP resource** — descartada: rompe la consistencia con las 3 tools existentes sin
   beneficio para los consumidores (comandos que ya invocan tools).
5. **Separar en dos tools (`get_contract_specs` + `get_trading_sessions`)** — descartada: la
   pregunta "¿opera X en fecha Y?" necesita cruzar specs + sesiones + feriados en una respuesta;
   separar duplicaría la lógica de negocio en los comandos.

Decisiones nuevas de Design (§5): feriado-primero en el algoritmo (§4); mapeo `trade_mode` por
entero literal (§5.1); mapeo exchange como constante en el módulo (§5.3); sin caché (§5.4);
conversión anclada a fecha de referencia (§6).

---

## 8. Impacto en tests (RNF1, RNF5, AC1–AC13)

Nuevo `tests/test_symbol_spec.py` con el patrón `conftest.py` (stub de `fastmcp`, fixture
`collector`) y `monkeypatch` de `mt5_client.get_symbol_info`/`get_session` (equivalente a cómo
`test_calendar.py` monkeypatchea `_fetch_calendario`). El módulo debe importar sin `MetaTrader5`
(RNF1). Se recomienda un helper local `_symbol_info_fake(...)` y `_session_fake(...)` análogo a
`_fila()` de `test_calendar.py`.

Cobertura mínima (una prueba por AC/CB):
- `test_registro` → AC1 (estructural: `def register`; `server.py` importa+registra).
- `test_ticker_invalido` → AC2 / CB-1 (`TICKER_NOT_FOUND`).
- `test_camino_feliz_sin_fecha` → AC3 (10 claves R3 + 7 días R3.1).
- `test_camino_feliz_con_fecha_habil` → AC4 (`opera`, `horario_chile` 10:30-17:00).
- `test_feriado_nyse` → AC5 / CB-9 (`feriado_bolsa` gana sobre viernes hábil).
- `test_fin_de_semana` → AC6 / CB-5 (`fin_de_semana`).
- `test_dia_habil_sin_sesion` → CB-6 (`fuera_de_sesion_recurrente`).
- `test_ticker_sin_cobertura_feriados` → AC7 / CB-3 (`calendario_feriados_fuente is None`,
  nunca `feriado_bolsa`).
- `test_trade_mode_disabled_hoy` → AC8 / CB-4 (`trade_mode_disabled`; requiere `fecha=hoy`).
- `test_fecha_invalida` → AC9 / CB-2 (`INVALID_FECHA` para `2026-02-30` y `03-07-2026`).
- `test_mt5_no_disponible` → AC10 / CB-7 (`get_symbol_info` lanza `ImportError` →
  `MT5_UNAVAILABLE`).
- `test_sesion_no_disponible` → AC11 / CB-8 (`get_session` devuelve `None` →
  `SESSION_UNAVAILABLE`).
- `test_feriados_bolsa_json` → AC12 (estructural: `_meta.actualizado`, ≥9 fechas NYSE incl.
  `2026-01-01` y `2026-12-25`).
- `tests/test_server.py` sin cambios sigue verde → AC13 / RNF4.

**Nota EDD/TDD**: cada tarea de código del §9 lleva su criterio ejecutable como referencia al AC
correspondiente (input/fixture/output ya especificados en `spec.md` §Criterios de aceptación). Los
tests se escriben antes de la implementación (test-first) reproduciendo el fixture del AC.

---

## 9. Desglose de tareas (mapeado a requisitos / AC)

Ordenadas por dependencia. Cada tarea de código cita su criterio de aceptación ejecutable.

- [ ] **T1 — Adapter MT5**: agregar `get_symbol_info(ticker)` y `get_session(ticker, day_of_week,
  index, tipo)` en `mt5_client.py` con import perezoso de `MetaTrader5` (patrón `get_rates`).
  *(R9)* · Criterio: mockeables en tests sin terminal; cubierto indirectamente por AC10/AC11
  (`ImportError` → `MT5_UNAVAILABLE`; `None` → `SESSION_UNAVAILABLE`).
- [ ] **T2 — Dato de feriados**: crear `config/feriados_bolsa.json` con `_meta`
  (`actualizado`,`fuente`,`proceso_actualizacion`) + `NYSE` = 10 fechas 2026 ordenadas, sin
  duplicados. *(R6)* · Criterio: **AC12** + verificar las 10 fechas contra
  `nyse.com/markets/hours-calendars` (bloquea Apply, ver R-2).
- [ ] **T3 — Esqueleto de la tool**: `tools/symbol_spec.py` con `register(mcp)`, `@mcp.tool`
  `get_symbol_spec(ticker, fecha=None)`, validación de ticker contra `catalog.VALID_TICKERS`,
  constantes (mapeo `trade_mode` §5.1, mapeo exchange §5.3, claves de días §3.2). *(R1,R2,R5)* ·
  Criterio: **AC1, AC2**.
- [ ] **T4 — Validación de fecha**: parseo ISO estricto `YYYY-MM-DD` antes de tocar MT5
  (`INVALID_FECHA`). *(R7,R8)* · Criterio: **AC9** (`2026-02-30`, `03-07-2026`).
- [ ] **T5 — Errores MT5**: mapear `ImportError`/fallo de conexión → `MT5_UNAVAILABLE`; ausencia de
  datos de sesión → `SESSION_UNAVAILABLE` (orden R8). *(R7,R8)* · Criterio: **AC10, AC11**.
- [ ] **T6 — Specs estáticas + patrón semanal**: armar `trade_mode`, `digits`, `volume_min/step`,
  `contract_size`, `server_time`, `server_utc_offset_minutes`, `sesiones_semana` (7 días, N
  ventanas/día, hora Chile), `fuente`. *(R3,R3.1,RNF2)* · Criterio: **AC3** (+ conversión §6).
- [ ] **T7 — Conversión de sesiones a Chile**: helper con `zoneinfo` anclado a fecha de referencia
  (§6), sin offsets fijos. *(RNF2)* · Criterio: **AC4** (10:30-17:00 CLT).
- [ ] **T8 — Resolución de `opera`**: implementar el algoritmo feriado-primero (§4) con
  `fecha_consultada`, `opera`, `motivo`, `horario_chile`, `calendario_feriados_fuente`. *(R4,R4.1)*
  · Criterio: **AC4, AC5, AC6, AC7, AC8** + CB-3..CB-9.
- [ ] **T9 — Registro en server**: import + `symbol_spec.register(mcp)` + actualizar `instructions`
  con una frase describiendo la tool. *(R1,R10)* · Criterio: **AC1** (parte `server.py`), **AC13**
  (smoke test sigue verde).
- [ ] **T10 — Docstring de limitación**: documentar en el docstring de `get_symbol_spec` que
  `USDCLP`/`XAUUSD`/`WTI.spot` no tienen calendario de feriados (limitación, no bug). *(R11)*
- [ ] **T11 — Tests**: `tests/test_symbol_spec.py` cubriendo AC1–AC12 (§8), test-first. *(RNF5)* ·
  Criterio: suite verde + AC13.
- [ ] **T12 — Doc de cierre** (post-Apply, opcional en este Change): tabla MCP en `CLAUDE.md` gana
  la 4.ª tool. *(fuera del núcleo; puede diferirse a un Change de doc)*

---

## 10. Decisiones para el gate humano `DESIGN → APPLY`

- **D-GATE-1 (Riesgo R-1 del spec) — extender o no el mapeo NYSE a `US500.spot` y `US30.spot`.**
  `config/activos.json` define tres índices US con horario NYSE idéntico
  (`US100.spot`, `US500.spot`, `US30.spot`), pero el alcance aprobado en propose solo mapea
  `US100.spot`. No hay razón declarada para excluir los otros dos (a diferencia de
  `USDCLP`/`XAUUSD`/`WTI.spot`, cuya exclusión sí está justificada). Es un cambio de **una línea**
  en el mapeo de §5.3, sin impacto en el resto del diseño.
  **Recomendación del diseñador**: extender a los 3 índices US (consistencia; mismo exchange).
  ✅ **ACEPTADA por el director (2026-07-02)**: el mapeo NYSE cubre los 3 índices US + 13 acciones
  (16 tickers, §5.3).
- **D-GATE-2 (verificación de dato, bloquea Apply no Design) — R-2**: las 10 fechas NYSE 2026 de T2
  deben verificarse contra el calendario oficial (`nyse.com/markets/hours-calendars`) antes de
  mergear. La mecánica de la tool no depende de las fechas exactas (no bloquea Design).
  ✅ **ACEPTADA por el director (2026-07-02)**: la verificación queda como criterio bloqueante de
  T2 en la fase Apply (antes del merge).

---

## 11. Riesgos

- **R-1 → D-GATE-1** (arriba): alcance del mapeo NYSE. **Resuelto**: extendido a los 3 índices US
  por decisión del director (2026-07-02).
- **R-2 → D-GATE-2**: exactitud del calendario NYSE 2026. Mitigación: verificación en Apply
  (aceptada como criterio bloqueante de T2).
- **R-3 (múltiples sub-sesiones/día)**: `sesiones_semana` ya soporta listas variables (§5.2);
  `horario_chile` usa la primera ventana `trade`. Mitigación: confirmar contra tickers reales en
  Apply; el contrato no cambia.
- **R-4 (offset del servidor MT5)**: derivar `server_utc_offset_minutes` de forma robusta y su
  interacción con DST en la conversión (§6). Mitigación: anclar la conversión a fecha de referencia
  con `zoneinfo`; exponer el offset crudo para depuración; cubrir con AC4.
- **R-5 (enteros `SYMBOL_TRADE_MODE_*`)**: se mapean por entero literal (§5.1). Mitigación:
  verificar contra la versión instalada en Apply; valores inesperados → `"UNKNOWN"` sin romper el
  contrato.

---

## 12. Referencias
- `spec.md`, `proposal.md`, `idea.md` (mismo Change) · Issue #104 (bbenja11/grupo-analisis-mercado)
- `src/market_data_mcp/server.py`, `catalog.py`, `mt5_client.py`,
  `tools/levels.py`, `tools/calendar.py`, `tools/chart_objects.py`
- `config/activos.json` · `tests/conftest.py`, `tests/test_calendar.py`, `tests/test_levels.py`,
  `tests/test_server.py`
- `data/mensajes/2026-07-02/us100/dato_macro/16-59_dato_macro.txt` (contexto motivador)
</content>
</invoke>
