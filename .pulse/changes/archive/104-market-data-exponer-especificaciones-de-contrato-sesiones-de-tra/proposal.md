# Propuesta — market-data: exponer especificaciones de contrato y sesiones de trading (#104)

## Problema

El MCP `market-data` no tiene forma de responder, de manera determinista, "¿opera el activo X en la fecha Y y en qué horario?". Las 3 tools actuales (`get_asset_levels`, `get_chart_objects`, `obtener_calendario_macro`) cubren precio/técnico, niveles manuales y calendario económico — ninguna expone sesiones de trading ni especificaciones de contrato del símbolo. El único dato disponible hoy es `horario_mercado` en `config/activos.json`, un string libre y estático (ej. `"09:30-16:00 ET (10:30-17:00 CLT)"`) sin fuente en el broker y sin noción de feriados.

Esto se evidenció el 2026-07-02: al preparar el aviso de `/dato_macro` sobre el feriado de EE.UU. del 3 de julio, el mensaje final tuvo que usar lenguaje de cobertura ("confirma en tu plataforma el horario real...") en vez de una afirmación verificada, violando la regla de oro del proyecto de que el análisis debe ser accionable y sin ambigüedad.

## Propuesta de solución concreta

Agregar una tool nueva al MCP `market-data`, siguiendo exactamente el patrón de las 3 existentes (módulo en `tools/`, `register(mcp)`, validación contra `catalog.VALID_TICKERS`, import perezoso de `MetaTrader5`, contrato de error uniforme).

### Tool: `get_symbol_spec(ticker: str, fecha: str | None = None)`

**Sin `fecha`** — specs estáticas del contrato + patrón semanal recurrente de sesiones:

```json
{
  "ticker": "US100.spot",
  "trade_mode": "FULL",
  "digits": 2,
  "volume_min": 1.0,
  "volume_step": 1.0,
  "contract_size": 1.0,
  "server_time": "2026-07-02 16:59:00",
  "server_utc_offset_minutes": -180,
  "sesiones_semana": {
    "lunes":    [{"quote": ["09:30", "16:00"], "trade": ["09:30", "16:00"]}],
    "martes":   [{"quote": ["09:30", "16:00"], "trade": ["09:30", "16:00"]}],
    "...": "...",
    "sabado":   [],
    "domingo":  []
  },
  "fuente": "mt5"
}
```

- `trade_mode` traduce el código MT5 (`SYMBOL_TRADE_MODE_*`) a un string legible (`FULL`, `DISABLED`, `CLOSEONLY`, etc.).
- `sesiones_semana` viene de `symbol_info_session_quote/trade(ticker, day_of_week, index)` iterando los 7 días; las horas se convierten a `America/Santiago` (consistente con `calendar.py`), y se expone `server_utc_offset_minutes` para trazabilidad/depuración.
- `digits`, `volume_min/step`, `contract_size` de `symbol_info(ticker)`.

**Con `fecha` (ISO `YYYY-MM-DD`)** — responde la pregunta determinista central del issue:

```json
{
  "...specs anteriores...": "...",
  "fecha_consultada": "2026-07-03",
  "opera": false,
  "motivo": "feriado_bolsa",
  "horario_chile": null,
  "calendario_feriados_fuente": "config/feriados_bolsa.json (NYSE)"
}
```

- `opera` se calcula cruzando tres fuentes, en este orden:
  1. **Patrón semanal MT5** para el día de semana de `fecha` (¿hay sesión de trade definida ese día?). Si no la hay → `motivo: "fin_de_semana"` o `"fuera_de_sesion_recurrente"`.
  2. **Calendario de feriados de bolsa versionado en el repo** (`config/feriados_bolsa.json`) — solo para tickers mapeados a un exchange cubierto (ver Alcance). Si `fecha` está en la lista → `opera: false`, `motivo: "feriado_bolsa"`, aunque el patrón semanal diga que sí hay sesión.
  3. **`trade_mode` en tiempo real** — señal complementaria, solo aplicable cuando `fecha` es "hoy": si MT5 reporta `SYMBOL_TRADE_MODE_DISABLED` en el momento de la consulta, se refleja en `motivo: "trade_mode_disabled"` aunque no haya feriado programado (cobertura de suspensiones no calendarizadas).
- Si `opera: true`, `horario_chile` trae `{"apertura": "...", "cierre": "..."}` de la sesión de ese día convertida a Chile.

### Nueva función en `mt5_client.py`

`get_symbol_info(ticker)` y `get_session(ticker, day_of_week, index)`, con el mismo patrón de import perezoso de `MetaTrader5` que `get_rates` — mockeables en tests sin depender del terminal.

### Contrato de error

Reutiliza `TICKER_NOT_FOUND` y `MT5_UNAVAILABLE` (mismos códigos que `get_asset_levels`). Agrega:
- `INVALID_FECHA` — `fecha` no parsea como ISO `YYYY-MM-DD`.
- `SESSION_UNAVAILABLE` — MT5 no devuelve datos de sesión para el símbolo (símbolo sin sesiones configuradas en el broker).

### Nuevo archivo versionado: `config/feriados_bolsa.json`

```json
{
  "NYSE": ["2026-01-01", "2026-01-19", "2026-02-16", "2026-07-03", "2026-11-26", "2026-12-25"]
}
```

Mapeo ticker → calendario dentro del propio módulo `symbol_spec.py` (no en `activos.json`, para no acoplar el catálogo de activos a la lógica de feriados): `US100.spot` y todos los `#TICKER` de acciones → `NYSE`. El resto de los activos del catálogo (USDCLP, XAUUSD, WTI.spot) no tiene entrada de calendario en esta iteración (ver Postura sobre feriados).

## Alternativas consideradas

1. **Solo patrón semanal MT5, sin calendario de feriados** (opción original "inferir feriados de sesión vacía" del issue). Descartada como única solución: no resuelve el caso que originó el issue — un feriado puntual de un solo día (4 de julio trasladado a viernes) normalmente **no** aparece reflejado en la sesión recurrente de "viernes" del broker antes de tiempo. Deja sin resolver el criterio de aceptación central ("confirmar de forma anticipada si opera mañana").
2. **Dependencia de librería de calendarios bursátiles** (ej. `pandas_market_calendars`). Descartada para esta iteración: agrega una dependencia nueva al proyecto (hoy solo `fastmcp` + `pandas`), su cobertura de exchanges no necesariamente coincide con las sesiones reales que expone el broker MT5, y el mantenimiento real (9-10 fechas/año de NYSE) es trivial de versionar a mano. Queda como opción a revisar si se necesita cobertura de más exchanges.
3. **Cruzar con `obtener_calendario_macro` (Investing.com) para detectar feriados**. Descartada: el calendario económico de Investing.com no tiene un campo dedicado y confiable de "mercado cerrado por feriado" — mezclar ambas fuentes para inferir cierre de bolsa sería frágil e indirecto comparado con una lista de fechas explícita y versionada.
4. **Exponer como MCP resource en vez de tool**. Descartada por consistencia: las 3 tools existentes ya cubren datos de mercado con el mismo patrón (`register(mcp)` + `@mcp.tool`); introducir el primer resource del servidor para este caso puntual añade una superficie de API distinta sin beneficio claro para los consumidores actuales (comandos de día que ya invocan tools).
5. **Separar en dos tools** (`get_contract_specs` + `get_trading_sessions`). Descartada: la pregunta que motiva el issue ("¿opera X en fecha Y?") necesita combinar specs (`trade_mode`) + sesiones + feriados en una sola respuesta; separar obligaría a los comandos a hacer dos llamadas y reconciliar el cruce ellos mismos, duplicando la lógica de negocio que debería vivir en el MCP.

## Alcance

**Incluido en esta iteración:**
- Tool `get_symbol_spec(ticker, fecha=None)` con el shape descrito arriba.
- Funciones nuevas en `mt5_client.py`: `get_symbol_info`, `get_session`.
- `config/feriados_bolsa.json` con calendario **NYSE únicamente**, cubriendo `US100.spot` y las 13 acciones del catálogo.
- Conversión de horas de sesión a `America/Santiago` (consistente con `calendar.py`).
- Tests con MT5 mockeado (patrón `conftest.py` / fixture `collector`) para camino feliz y contrato de error.
- Documentar la tool en `mcp.instructions` de `server.py`.

**Fuera de alcance (explícitamente diferido):**
- Calendario de feriados para USDCLP, XAUUSD, WTI.spot — estos activos no tienen un "feriado de bolsa" único y bien definido de la misma forma que NYSE/NASDAQ (USD/CLP depende de feriados bancarios CL/US, oro y petróleo cotizan en CME casi continuamente con ventanas de baja liquidez, no cierres de bolsa). Se documenta como limitación conocida; para estos activos la tool solo garantiza patrón semanal MT5 + `trade_mode` en tiempo real.
- Días de cierre parcial / medio día (ej. día después de Thanksgiving en NYSE). El calendario de esta iteración solo modela cierre total (`opera: false`); no modela `horario_reducido`.
- Migrar o deprecar el campo `horario_mercado` de `config/activos.json` — coexiste como fallback documental hasta que se confirme la adopción de la tool en los comandos.
- Cambiar `/dato_macro` u otros comandos de día para consumir la tool nueva — queda para un change de Apply posterior (o un issue de seguimiento) una vez que la tool exista y esté probada.
- Cobertura de exchanges fuera de NYSE/NASDAQ (ej. SSE para el proxy chino, si existiera en el catálogo).

## Postura sobre feriados (decisión central)

- **Lo que MT5 puede garantizar de forma nativa**: patrón de sesión **recurrente por día de semana** (`symbol_info_session_quote/trade`) y el estado de `trade_mode` **en el momento de la consulta**. Esto es suficiente para responder "¿en qué horario opera un lunes típico?" y para confirmar en tiempo real si un símbolo está deshabilitado ahora mismo — pero **no** para anticipar un feriado puntual de calendario antes de que ocurra, porque el broker no expone una tabla de excepciones por fecha vía esta API.
- **Lo que requiere una fuente externa**: confirmar por adelantado "¿opera NYSE/NASDAQ el 3 de julio de 2026?" exige un calendario de fechas de feriados de bolsa mantenido aparte de MT5.
- **Decisión para esta iteración**: mantener un archivo estático versionado en el repo (`config/feriados_bolsa.json`), con el calendario público y estable de NYSE (9-10 fechas fijas/año, cambia poco y con años de anticipación conocidos), actualizado manualmente una vez al año por quien mantenga el repo. Se combina con el patrón semanal de MT5 y con `trade_mode` en tiempo real como tres señales complementarias (ver shape de respuesta arriba), en vez de depender de una sola fuente. Esto resuelve el caso concreto que motivó el issue (acciones + US100, el 90%+ de los casos donde `/dato_macro` necesita avisar un feriado) sin agregar una dependencia nueva ni sobre-diseñar cobertura para activos (USD/CLP, oro, petróleo) donde el concepto de "feriado de bolsa" no aplica igual.

## Impacto en consumidores

- **`/dato_macro`**: puede citar el resultado de `get_symbol_spec(ticker, fecha=mañana)` para redactar avisos de feriado con lenguaje determinista ("El Nasdaq 100 no opera el viernes 3 de julio por feriado de EE.UU.") en vez de lenguaje de cobertura, para los tickers cubiertos por `feriados_bolsa.json`. Para USD/CLP, oro y WTI, el aviso debe seguir usando lenguaje de patrón semanal + confirmación en tiempo real (limitación documentada, no un blocker de este cambio).
- **Comandos de día** (`/martes`, `/miercoles`, `/jueves`, `/viernes_am`, etc.): consumo opcional, no forzado en esta iteración — la integración en los comandos queda fuera de alcance (ver arriba); el impacto inmediato es que la tool queda disponible para que un cambio posterior la use.
- **`config/activos.json`**: sin cambios de estructura; `horario_mercado` se mantiene como está, coexistiendo con la tool.
- **Ningún consumidor existente se rompe**: es una tool nueva, aditiva; no modifica el comportamiento de `get_asset_levels`, `get_chart_objects` ni `obtener_calendario_macro`.

## Criterios de aceptación refinados

1. Nueva tool `get_symbol_spec(ticker, fecha=None)` registrada en `market-data`, siguiendo el patrón de módulo `tools/<nombre>.py` + `register(mcp)` + validación contra `catalog.VALID_TICKERS`.
2. Sin `fecha`: retorna `trade_mode`, `digits`, `volume_min/step`, `contract_size`, `sesiones_semana` (7 días, horas en `America/Santiago`) y `server_utc_offset_minutes`.
3. Con `fecha` ISO válida: retorna `opera: bool` determinista, `motivo` (uno de `feriado_bolsa` / `fin_de_semana` / `fuera_de_sesion_recurrente` / `trade_mode_disabled` / ninguno si opera) y `horario_chile` si `opera: true`.
4. Errores explícitos: `TICKER_NOT_FOUND` (ticker fuera de catálogo), `MT5_UNAVAILABLE` (MT5 no instalado/conectado), `INVALID_FECHA` (formato de fecha inválido), `SESSION_UNAVAILABLE` (MT5 no devuelve datos de sesión para el símbolo). Nunca `None` ni array vacío silencioso.
5. `config/feriados_bolsa.json` creado y documentado (fuente NYSE, fecha de última actualización, proceso de actualización anual) — cubre `US100.spot` y las 13 acciones del catálogo.
6. Tests unitarios (patrón `conftest.py` / fixture `collector`) cubren: camino feliz sin `fecha`, camino feliz con `fecha` en día hábil normal, `fecha` de feriado NYSE (`opera: false, motivo: feriado_bolsa`), `fecha` de fin de semana, y los 4 códigos de error — todo con MT5 mockeado, sin depender del terminal real.
7. `mt5_client.py` gana `get_symbol_info(ticker)` y `get_session(ticker, day_of_week, index)` con import perezoso de `MetaTrader5`, mockeables igual que `get_rates`.
8. `server.py` documenta la tool nueva en `mcp.instructions` (bloque descriptivo, igual que las 3 tools actuales).
9. Queda explícitamente documentado (en el design-doc o en comentario de código) que USD/CLP, XAUUSD y WTI.spot no tienen calendario de feriados en esta iteración — es una limitación conocida, no un bug.

## Preguntas que quedan para Design

1. Nombre exacto y forma canónica de traducir los códigos `SYMBOL_TRADE_MODE_*` de MT5 a los strings legibles del payload (`FULL`, `DISABLED`, etc.) — mapeo completo a definir.
2. Formato exacto de `sesiones_semana` cuando un símbolo tiene múltiples sub-sesiones por día (algunos brokers reportan 2 ventanas por día, ej. pre-market/regular) — confirmar con `symbol_info_session_*` real contra al menos 2-3 tickers del catálogo antes de fijar el shape final.
3. Ubicación exacta del mapeo ticker→exchange de feriados (¿constante en `symbol_spec.py`, o un campo nuevo opcional en `config/activos.json`, ej. `"exchange_feriados": "NYSE"`, para no hardcodear la lista de acciones en el código?).
4. Si conviene cachear `get_symbol_info`/sesiones (como hace `calendar.py` con TTL de 1h) dado que estos datos cambian con muy poca frecuencia, o consultarlos siempre en vivo dado que la llamada a MT5 es barata comparada con el fetch HTTP de Investing.com.

## Referencias

- Issue #104 (bbenja11/grupo-analisis-mercado)
- `C:\Users\bbrav\grupo-analisis-mercado\.pulse\changes\104-market-data-exponer-especificaciones-de-contrato-sesiones-de-tra\idea.md`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\server.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\catalog.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\mt5_client.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\tools\levels.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\tools\calendar.py`
- `C:\Users\bbrav\grupo-analisis-mercado\config\activos.json`
- `C:\Users\bbrav\grupo-analisis-mercado\pyproject.toml` (DEP001 exime `MetaTrader5`)
- `C:\Users\bbrav\grupo-analisis-mercado\tests\conftest.py`, `tests\test_levels.py`, `tests\test_calendar.py`
- `C:\Users\bbrav\grupo-analisis-mercado\data\mensajes\2026-07-02\us100\dato_macro\16-59_dato_macro.txt`
