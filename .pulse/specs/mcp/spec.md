
<!-- change:104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra -->
# Spec — market-data: exponer especificaciones de contrato y sesiones de trading (#104)

> Formaliza `idea.md` y `proposal.md` (fases explore/propose ya aprobadas). Esta spec fija el
> comportamiento observable de la nueva tool `get_symbol_spec` y el archivo
> `config/feriados_bolsa.json`. No decide implementación interna (mapeos exactos de constantes
> MT5, estrategia de caché, ubicación del mapeo ticker→exchange): esas decisiones quedan para
> `design.md`.

## Objetivo

Permitir que el MCP `market-data` responda de forma **determinista** "¿opera el activo X en
la fecha Y, y en qué horario (hora Chile)?", cerrando el hueco documentado en `idea.md` (líneas
5-7): hoy solo existe `horario_mercado` como string libre en `config/activos.json`, sin fuente
en el broker y sin noción de feriados puntuales, lo que obligó a redactar el aviso de
`/dato_macro` del feriado NYSE del 2026-07-03 con lenguaje de cobertura en vez de una afirmación
verificada (`data/mensajes/2026-07-02/us100/dato_macro/16-59_dato_macro.txt`).

## Alcance

### IN
- Tool nueva `get_symbol_spec(ticker: str, fecha: str | None = None)` registrada en el servidor
  `market-data` (`src/market_data_mcp/server.py:82-86`), siguiendo el patrón de
  `get_asset_levels`/`get_chart_objects`/`obtener_calendario_macro`: módulo propio en
  `src/market_data_mcp/tools/`, función `register(mcp)`, validación de `ticker` contra
  `catalog.VALID_TICKERS` (`src/market_data_mcp/catalog.py:40`), import perezoso de
  `MetaTrader5`, contrato de error uniforme.
- Dos funciones nuevas en `src/market_data_mcp/mt5_client.py` (junto a `get_rates` en
  `mt5_client.py:75-99`): una que envuelve `symbol_info(ticker)` y otra que envuelve
  `symbol_info_session_quote/trade(ticker, day_of_week, index)`, con el mismo patrón de import
  perezoso ya usado en todo el módulo (`mt5_client.py:9-11`).
- Archivo nuevo versionado `config/feriados_bolsa.json` con el calendario de feriados NYSE 2026,
  mapeado (en código, no en `activos.json`) a `US100.spot` y a las 13 acciones del catálogo
  (`config/activos.json`, sección `acciones`, ver `catalog.py:29-31`).
- Conversión de horas de sesión a `America/Santiago` con `zoneinfo`, consistente con
  `src/market_data_mcp/tools/calendar.py:20,132-135` (nunca offsets fijos).
- Tests con MT5 mockeado, mismo patrón que `tests/conftest.py` (fixture `collector`,
  `tests/test_calendar.py`), cubriendo camino feliz y los 4 códigos de error.
- Documentar la tool nueva en el bloque `instructions` de `FastMCP` en `server.py:63-80`.

### OUT (explícitamente diferido — YAGNI de esta iteración)
- Calendario de feriados para `USDCLP`, `XAUUSD`, `WTI.spot` (proposal.md, sección "Alcance /
  Fuera de alcance", líneas 99-104): estos activos no tienen un feriado de bolsa único y bien
  definido (USD/CLP depende de feriados bancarios CL/US; oro y petróleo cotizan casi
  continuamente en CME). Para ellos la tool solo garantiza patrón semanal MT5 +
  `trade_mode` en tiempo real — limitación conocida, documentada, no un bug.
- Días de cierre parcial / medio día (ej. día después de Thanksgiving en NYSE). Esta iteración
  solo modela cierre total (`opera: false`); no existe noción de `horario_reducido`.
- Deprecar o migrar el campo `horario_mercado` de `config/activos.json` — coexiste como fallback
  documental.
- Integrar la tool en `/dato_macro` o en los comandos de día (`/martes`, `/miercoles`, etc.) —
  queda para un Change de Apply posterior o un issue de seguimiento.
- Cobertura de exchanges fuera de NYSE (ej. SSE, si existiera un proxy chino en el catálogo).
- Caché de `get_symbol_info`/sesiones (pregunta abierta de `proposal.md` línea 136, para Design).

## Requisitos funcionales

### R1 — Registro de la tool
`get_symbol_spec(ticker: str, fecha: str | None = None)` se registra en `market-data` vía
`register(mcp)` en un módulo nuevo `src/market_data_mcp/tools/symbol_spec.py`, importado y
llamado en `server.py` con el mismo patrón de 3 líneas que las tools existentes
(`server.py:82-86`).

### R2 — Validación de ticker (sin cambios de contrato)
Si `ticker` no está en `catalog.VALID_TICKERS`, la tool retorna
`{"error": "TICKER_NOT_FOUND", "message": "..."}` — mismo código y mismo criterio que
`get_asset_levels` (`tools/levels.py:105-112`). Esta validación ocurre **antes** de cualquier
otra validación o llamada a MT5.

### R3 — Respuesta sin `fecha` (specs estáticas + patrón semanal)
Si `fecha` es `None`, la respuesta exitosa contiene, como mínimo, estas claves:

| Clave | Tipo | Origen / semántica |
|---|---|---|
| `ticker` | `str` | eco del ticker validado |
| `trade_mode` | `str` | uno de `"DISABLED"`, `"LONGONLY"`, `"SHORTONLY"`, `"CLOSEONLY"`, `"FULL"` (conjunto cerrado y exhaustivo sobre `SYMBOL_TRADE_MODE_*` de MT5) |
| `digits` | `int` | `symbol_info(ticker).digits` |
| `volume_min` | `float` | `symbol_info(ticker).volume_min` |
| `volume_step` | `float` | `symbol_info(ticker).volume_step` |
| `contract_size` | `float` | `symbol_info(ticker).trade_contract_size` |
| `server_time` | `str` | hora del servidor MT5 en el momento de la consulta, formato `"YYYY-MM-DD HH:MM:SS"` |
| `server_utc_offset_minutes` | `int` | offset del servidor MT5 respecto a UTC, para trazabilidad/depuración |
| `sesiones_semana` | `dict[str, list[dict]]` | ver R3.1 |
| `fuente` | `str` | `"mt5"` |

**R3.1 — forma de `sesiones_semana`.** Claves fijas en español, en este orden y ortografía
exacta: `lunes, martes, miercoles, jueves, viernes, sabado, domingo` (sin tildes, para evitar
ambigüedad de encoding). El valor de cada clave es una **lista** (puede tener 0, 1 o más
elementos) de objetos `{"quote": [apertura, cierre], "trade": [apertura, cierre]}`, con
`apertura`/`cierre` en formato `"HH:MM"` de 24h, **ya convertidos a `America/Santiago`**. Un día
sin sesión configurada en el broker para ese ticker (ej. fin de semana típico) se representa
con lista vacía `[]` — nunca `null` ni la clave ausente.

### R4 — Respuesta con `fecha` (pregunta determinista "¿opera?")
Si `fecha` es un string ISO `YYYY-MM-DD` válido, la respuesta exitosa incluye **todas** las
claves de R3 más:

| Clave | Tipo | Semántica |
|---|---|---|
| `fecha_consultada` | `str` | eco normalizado de `fecha` (`YYYY-MM-DD`) |
| `opera` | `bool` | resultado determinista del cruce de 3 señales (R4.1) |
| `motivo` | `str \| null` | `null` si `opera: true`; si `opera: false`, uno de `"feriado_bolsa"`, `"fin_de_semana"`, `"fuera_de_sesion_recurrente"`, `"trade_mode_disabled"` |
| `horario_chile` | `object \| null` | `null` si `opera: false`; si `opera: true`, `{"apertura": "HH:MM", "cierre": "HH:MM"}` de la primera ventana de sesión `trade` de ese día de semana, hora Chile |
| `calendario_feriados_fuente` | `str \| null` | `"config/feriados_bolsa.json (NYSE)"` si el ticker está mapeado a un exchange cubierto (R5); `null` si no tiene cobertura de feriados (ver Casos borde, CB-3) |

**R4.1 — orden de evaluación de `opera` (determinista, sin ambigüedad).** Se evalúa en este
orden; la primera señal que determine `opera: false` fija también `motivo` y detiene la
evaluación:

1. **Patrón semanal MT5** para el día de semana de `fecha`: si `sesiones_semana[<día>]` (R3.1)
   es una lista vacía → `opera: false`, `motivo: "fin_de_semana"` si el día de semana es sábado
   o domingo, `motivo: "fuera_de_sesion_recurrente"` en cualquier otro caso (ej. broker sin
   sesión configurada un día hábil).
2. **Calendario de feriados versionado** (R5): si el ticker está mapeado a un exchange cubierto
   y `fecha` aparece en la lista de feriados de ese exchange → `opera: false`,
   `motivo: "feriado_bolsa"` — **esta señal tiene prioridad sobre el resultado del patrón
   semanal si ambas aplicaran** (un feriado puntual siempre gana sobre "normalmente hay sesión
   ese día de la semana").
3. **`trade_mode` en tiempo real** — señal complementaria, **solo evaluada si `fecha` es la
   fecha de hoy en `America/Santiago`**: si `trade_mode == "DISABLED"` en el momento de la
   consulta → `opera: false`, `motivo: "trade_mode_disabled"`, incluso sin feriado programado.
   Para `fecha` distinta de hoy, esta señal no se evalúa (no hay forma de anticipar
   `trade_mode` futuro).
4. Si ninguna señal anterior determina `false` → `opera: true`, `motivo: null`,
   `horario_chile` poblado desde la sesión `trade` de ese día de semana.

### R5 — Cobertura del calendario de feriados
`config/feriados_bolsa.json` cubre únicamente el exchange `NYSE`. El mapeo ticker → exchange
vive en código (no en `config/activos.json`, para no acoplar el catálogo de activos a la
lógica de feriados) y cubre, en esta iteración: `US100.spot` y los 13 tickers de acciones del
catálogo (`#AAPL, #MSFT, #NVDA, #AMZN, #AMD, #JPM, #BAC, #GS, #MS, #BA, #CAT, #GE, #DE`).
Cualquier ticker fuera de este mapeo (incluyendo `USDCLP`, `XAUUSD`, `WTI.spot`, y —ver
Riesgo R-1— `US500.spot`, `US30.spot`) nunca produce `motivo: "feriado_bolsa"`;
`calendario_feriados_fuente` es `null` para ellos.

### R6 — Formato de `config/feriados_bolsa.json`
```json
{
  "_meta": {
    "actualizado": "2026-07-02",
    "fuente": "https://www.nyse.com/markets/hours-calendars",
    "proceso_actualizacion": "manual, una vez al año, por quien mantenga el repo"
  },
  "NYSE": [
    "2026-01-01",
    "2026-01-19",
    "2026-02-16",
    "2026-04-03",
    "2026-05-25",
    "2026-06-19",
    "2026-07-03",
    "2026-09-07",
    "2026-11-26",
    "2026-12-25"
  ]
}
```
- Clave `_meta` obligatoria con `actualizado` (fecha ISO de última revisión), `fuente` (URL o
  referencia del calendario oficial) y `proceso_actualizacion` (texto libre).
- Una clave por exchange cubierto (solo `NYSE` en esta iteración); valor = lista de fechas ISO
  `YYYY-MM-DD`, ordenadas ascendentemente, sin duplicados.
- El listado de 10 fechas arriba es el calendario completo NYSE 2026 (Año Nuevo, MLK Day,
  Washington's Birthday, Good Friday, Memorial Day, Juneteenth, Independence Day observado,
  Labor Day, Thanksgiving, Navidad) — **debe verificarse contra el calendario oficial vigente
  de NYSE antes de mergear** (ver Riesgo R-2); no basta con las 6 fechas de ejemplo que trae
  `proposal.md:75`.

### R7 — Contrato de error
Reutiliza `TICKER_NOT_FOUND` y `MT5_UNAVAILABLE` (mismos criterios que `get_asset_levels`,
`tools/levels.py:105-150`). Agrega:
- `INVALID_FECHA` — `fecha` no es `None` y no parsea como ISO `YYYY-MM-DD` estricto (incluye
  formatos alternativos como `DD-MM-YYYY`, fechas de calendario inexistentes como
  `2026-02-30`, o valores no-string). Se valida **antes** de tocar MT5.
- `SESSION_UNAVAILABLE` — MT5 está disponible pero `symbol_info_session_quote/trade` no
  devuelve datos de sesión para el símbolo (broker sin sesiones configuradas para ese ticker
  específico). Distinto de `MT5_UNAVAILABLE` (que es "no hay terminal/conexión") y de "sesión
  vacía para ese día" (que es un resultado válido, no un error — ver R3.1 y R4.1.1).

Nunca `None` ni array vacío silencioso como respuesta de error — mismo principio que las 3
tools existentes (`server.py:3-4`).

### R8 — Orden de validación observable
1. `ticker` contra catálogo (R2) → `TICKER_NOT_FOUND`.
2. Si `fecha is not None`: formato de fecha (R7) → `INVALID_FECHA`. Se valida sin llamar a MT5.
3. Disponibilidad de MT5 (import perezoso / conexión) → `MT5_UNAVAILABLE`.
4. Disponibilidad de datos de sesión para el símbolo → `SESSION_UNAVAILABLE`.
5. Construcción de la respuesta (R3, y R4 si aplica `fecha`).

### R9 — Nuevas funciones en `mt5_client.py`
- `get_symbol_info(ticker: str) -> ...` — envuelve `MetaTrader5.symbol_info(ticker)`, import
  perezoso de `MetaTrader5` dentro de la función (mismo patrón que `get_rates`,
  `mt5_client.py:75-82`), mockeable en tests sin depender del terminal.
- `get_session(ticker: str, day_of_week: int, index: int) -> ...` — envuelve
  `MetaTrader5.symbol_info_session_quote`/`symbol_info_session_trade`, mismo patrón de import
  perezoso.

### R10 — Documentación en `server.py`
El bloque `instructions` de `FastMCP` (`server.py:63-80`) se actualiza para mencionar
`get_symbol_spec` con la misma estructura descriptiva que las 3 tools existentes (una frase
por tool).

### R11 — Limitación documentada (no bug)
Debe quedar documentado —en docstring de `get_symbol_spec` y/o en `design.md`— que `USDCLP`,
`XAUUSD` y `WTI.spot` no tienen calendario de feriados en esta iteración: para ellos, `opera`
con `fecha` futura solo puede basarse en patrón semanal MT5 (nunca en `motivo: "feriado_bolsa"`).

## Requisitos no funcionales

### RNF1 — Testabilidad sin MT5 (CI)
Igual que `get_asset_levels`/`obtener_calendario_macro`: el módulo `symbol_spec.py` debe ser
importable sin `MetaTrader5` instalado. Los tests usan el patrón `tests/conftest.py`
(stub de `fastmcp`, fixture `collector`) para invocar la función registrada directamente,
mockeando `get_symbol_info`/`get_session` (equivalente a como `test_levels.py`/`test_calendar.py`
mockean sus dependencias externas).

### RNF2 — Zona horaria determinista
Toda hora expuesta en `sesiones_semana` y `horario_chile` se convierte con `zoneinfo`
(`ZoneInfo("America/Santiago")`), nunca con offsets fijos hardcodeados — mismo principio que
`tools/calendar.py:132-135` y la regla canónica de `CLAUDE.md` ("Fecha y hora actual").
`server_utc_offset_minutes` se expone crudo (sin convertir) para trazabilidad/depuración.

### RNF3 — Idioma
Docstrings, mensajes de error y nombres de claves de dominio (`sesiones_semana`, `motivo`,
`opera`, días de la semana) en español, consistente con el resto del MCP.

### RNF4 — No rompe consumidores existentes
Tool aditiva: no modifica el comportamiento de `get_asset_levels`, `get_chart_objects` ni
`obtener_calendario_macro`. El smoke test `tests/test_server.py` (`test_server_importa_y_expone_mcp`)
debe seguir pasando sin cambios tras registrar la tool nueva.

### RNF5 — Cobertura de tests mínima
Ver Criterios de aceptación (BDD) — camino feliz sin `fecha`, camino feliz con `fecha` en día
hábil, `fecha` de feriado NYSE, `fecha` de fin de semana, ticker sin cobertura de feriados con
`fecha` futura, `trade_mode` deshabilitado con `fecha = hoy`, y los 4 códigos de error.

## Formato del archivo de feriados — ver R6

## Casos borde

- **CB-1 (ticker inválido)**: `get_symbol_spec("NOEXISTE")` → `{"error": "TICKER_NOT_FOUND", ...}`.
- **CB-2 (fecha inválida)**: `get_symbol_spec("US100.spot", fecha="03-07-2026")` y
  `get_symbol_spec("US100.spot", fecha="2026-02-30")` → ambos `{"error": "INVALID_FECHA", ...}`.
- **CB-3 (ticker sin cobertura de feriados)**: `get_symbol_spec("XAUUSD", fecha="2026-07-03")`
  (feriado NYSE, pero XAUUSD no está mapeado a NYSE) → `opera` se decide solo por patrón semanal
  + `trade_mode` en tiempo real; `motivo` nunca es `"feriado_bolsa"`;
  `calendario_feriados_fuente: null`.
- **CB-4 (símbolo deshabilitado en tiempo real)**: `fecha` = hoy y `trade_mode == "DISABLED"`
  en el momento de la consulta → `opera: false`, `motivo: "trade_mode_disabled"`, incluso si
  hoy no es feriado ni fin de semana según las otras dos señales.
- **CB-5 (sesión vacía / fin de semana)**: `fecha` cae en sábado o domingo para cualquier
  ticker → `sesiones_semana[<día>] == []` → `opera: false`, `motivo: "fin_de_semana"`.
- **CB-6 (sesión vacía en día hábil)**: `sesiones_semana[<día>] == []` para un día de semana
  que no es sábado/domingo (broker sin sesión configurada ese día) → `opera: false`,
  `motivo: "fuera_de_sesion_recurrente"`.
- **CB-7 (MT5 no disponible)**: sin `MetaTrader5` instalado o sin conexión → `{"error": "MT5_UNAVAILABLE", ...}`,
  tanto con `fecha` como sin ella (las specs estáticas también requieren `symbol_info`).
- **CB-8 (sin datos de sesión para el símbolo)**: MT5 disponible pero
  `symbol_info_session_quote/trade` retorna `None`/error para el ticker → `{"error": "SESSION_UNAVAILABLE", ...}`.
- **CB-9 (feriado vs patrón semanal en conflicto)**: `fecha` es un viernes (normalmente con
  sesión según patrón semanal) pero está en `config/feriados_bolsa.json["NYSE"]` → el feriado
  gana: `opera: false`, `motivo: "feriado_bolsa"` (no `"fuera_de_sesion_recurrente"` ni
  `opera: true`).

## Criterios de aceptación (evals ejecutables)

Ubicación esperada de los tests: `tests/test_symbol_spec.py` (nuevo), siguiendo el patrón de
`tests/test_calendar.py` (fixture `collector`, monkeypatch de las funciones de I/O).

**AC1 — registro de la tool (estructural)**
DADO el repo tras aplicar el Change,
CUANDO se ejecuta `rg -n "def register" src/market_data_mcp/tools/symbol_spec.py`,
ENTONCES existe exactamente una coincidencia; y `rg -n "symbol_spec" src/market_data_mcp/server.py`
retorna al menos 2 líneas (import + `symbol_spec.register(mcp)`).

**AC2 — ticker inválido**
DADO el catálogo `catalog.VALID_TICKERS`,
CUANDO se invoca `get_symbol_spec("NOEXISTE")`,
ENTONCES el resultado es `{"error": "TICKER_NOT_FOUND", "message": <str no vacío>}`.

**AC3 — camino feliz sin `fecha`**
DADO `get_symbol_info`/`get_session` mockeados con datos válidos de `"US100.spot"`,
CUANDO se invoca `get_symbol_spec("US100.spot")`,
ENTONCES el resultado no contiene `"error"`, contiene las 10 claves de R3, y
`sesiones_semana` tiene exactamente las 7 claves en español de R3.1.

**AC4 — camino feliz con `fecha` en día hábil normal**
DADO un `"US100.spot"` con sesión de lunes a viernes 09:30-16:00 y sin feriado ese día,
CUANDO se invoca `get_symbol_spec("US100.spot", fecha=<martes cualquiera fuera de feriados>)`,
ENTONCES `opera == True`, `motivo is None`, y `horario_chile == {"apertura": "10:30", "cierre": "17:00"}`
(conversión ET→Chile consistente con `config/activos.json` línea del índice: `"09:30-16:00 ET (10:30-17:00 CLT)"`).

**AC5 — `fecha` de feriado NYSE**
DADO `config/feriados_bolsa.json["NYSE"]` contiene `"2026-07-03"`,
CUANDO se invoca `get_symbol_spec("US100.spot", fecha="2026-07-03")`,
ENTONCES `opera == False` y `motivo == "feriado_bolsa"`, aunque el 3 de julio de 2026 sea
viernes (día con sesión en el patrón semanal).

**AC6 — `fecha` de fin de semana**
CUANDO se invoca `get_symbol_spec("US100.spot", fecha=<un sábado>)`,
ENTONCES `opera == False` y `motivo == "fin_de_semana"`.

**AC7 — ticker sin cobertura de feriados**
CUANDO se invoca `get_symbol_spec("XAUUSD", fecha="2026-07-03")` (feriado NYSE, pero XAUUSD
no mapea a NYSE),
ENTONCES `calendario_feriados_fuente is None`, y `motivo` (si `opera == False`) nunca es
`"feriado_bolsa"`.

**AC8 — `trade_mode` deshabilitado en tiempo real**
DADO `fecha` == fecha de hoy en `America/Santiago` y `get_symbol_info` mockeado con
`trade_mode == "DISABLED"`,
CUANDO se invoca `get_symbol_spec(<ticker>, fecha=<hoy>)`,
ENTONCES `opera == False` y `motivo == "trade_mode_disabled"`.

**AC9 — `fecha` inválida**
CUANDO se invoca `get_symbol_spec("US100.spot", fecha="2026-02-30")` y con
`fecha="03-07-2026"`,
ENTONCES ambas invocaciones retornan `{"error": "INVALID_FECHA", "message": <str no vacío>}`.

**AC10 — MT5 no disponible**
DADO que `get_symbol_info` lanza `ImportError` (MetaTrader5 no instalado, patrón de
`tools/levels.py:130-139`),
CUANDO se invoca `get_symbol_spec("US100.spot")`,
ENTONCES el resultado es `{"error": "MT5_UNAVAILABLE", "message": <str no vacío>}`.

**AC11 — sesión no disponible para el símbolo**
DADO `get_session` retorna `None`/vacío para un ticker con MT5 disponible,
CUANDO se invoca `get_symbol_spec(<ticker>)`,
ENTONCES el resultado es `{"error": "SESSION_UNAVAILABLE", "message": <str no vacío>}`.

**AC12 — archivo de feriados versionado (estructural)**
DADO el repo tras aplicar el Change,
CUANDO se ejecuta `rg -n "\"NYSE\"" config/feriados_bolsa.json` y se parsea el JSON,
ENTONCES existe la clave `_meta.actualizado` y la lista `NYSE` contiene al menos 9 fechas
ISO del año en curso de la publicación, incluyendo `"2026-01-01"` y `"2026-12-25"`.

**AC13 — smoke test del server no se rompe**
CUANDO se ejecuta `pytest tests/test_server.py`,
ENTONCES sigue pasando en verde sin modificaciones a ese archivo.

## Riesgos

- **R-1 (gap de alcance a elevar al humano)**: `config/activos.json` define **tres** índices
  US con idéntico horario NYSE (`US100.spot`, `US500.spot`, `US30.spot`, todos
  `"09:30-16:00 ET (10:30-17:00 CLT)"`), pero `proposal.md` (líneas 79, 94, 125) solo incluye
  `US100.spot` en el mapeo a `NYSE` de `config/feriados_bolsa.json`. No hay ninguna razón
  declarada para excluir `US500.spot`/`US30.spot` (a diferencia de `USDCLP`/`XAUUSD`/`WTI.spot`,
  cuya exclusión sí está justificada explícitamente). Esta spec **respeta el alcance literal
  aprobado en propose** (solo `US100.spot` + 13 acciones, R5), pero recomienda que el humano
  confirme en el gate `DESIGN → APPLY` si se debe extender el mapeo a los 3 índices US (cambio
  de una línea en la tabla de mapeo, sin impacto en el resto del diseño).
- **R-2 (exactitud del calendario NYSE 2026)**: las 10 fechas de R6 fueron derivadas por reglas
  conocidas de feriados NYSE (fijas + "N-ésimo lunes/jueves del mes"), pero no se verificaron
  contra el calendario oficial publicado por NYSE en esta fase (sin acceso a WebSearch en este
  subagente). Debe confirmarse contra `nyse.com/markets/hours-calendars` antes de mergear
  `config/feriados_bolsa.json` — la mecánica de la tool no depende de las fechas exactas, así
  que este riesgo no bloquea Design, pero sí bloquea Apply.
- **R-3 (múltiples sub-sesiones por día)**: `proposal.md` línea 134 deja abierto si algún
  broker reporta más de una ventana de sesión por día (ej. pre-market/regular). R3.1 ya
  contempla listas de largo variable por día; R4's `horario_chile` usa la primera ventana
  `trade` del día — si en Design se confirma que hay más de una ventana relevante para algún
  ticker del catálogo, puede requerir ajustar qué ventana se expone en `horario_chile` (detalle
  de Design, no cambia el contrato de `sesiones_semana`).

## Preguntas abiertas (para Design)

1. Mapeo completo `SYMBOL_TRADE_MODE_*` (MT5) → los 5 strings legibles de R3 — confirmar los
   valores enteros exactos de la librería `MetaTrader5` instalada.
2. Confirmar contra al menos 2-3 tickers reales del catálogo si `symbol_info_session_quote/trade`
   devuelve más de una ventana por día (ver Riesgo R-3).
3. Ubicación exacta del mapeo ticker→exchange de feriados: ¿constante en `symbol_spec.py`, o
   campo opcional nuevo en `config/activos.json` (ej. `"exchange_feriados": "NYSE"`)? No cambia
   el contrato observable de la tool, solo la implementación.
4. Si conviene cachear `get_symbol_info`/sesiones (TTL, igual que `calendar.py`) — dato de baja
   frecuencia de cambio vs. costo de la llamada MT5 (probablemente barata comparada con el
   fetch HTTP de `calendar.py`).
5. Resolución de Riesgo R-1 (extender o no el mapeo NYSE a `US500.spot`/`US30.spot`) —
   requiere confirmación humana antes de cerrar Design.

## Referencias

- Issue #104 (bbenja11/grupo-analisis-mercado)
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/idea.md`
- `.pulse/changes/104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra/proposal.md`
- `src/market_data_mcp/server.py`
- `src/market_data_mcp/catalog.py`
- `src/market_data_mcp/mt5_client.py`
- `src/market_data_mcp/tools/levels.py`, `tools/calendar.py`, `tools/chart_objects.py`
- `config/activos.json`
- `tests/conftest.py`, `tests/test_calendar.py`, `tests/test_levels.py`, `tests/test_server.py`
- `data/mensajes/2026-07-02/us100/dato_macro/16-59_dato_macro.txt`
