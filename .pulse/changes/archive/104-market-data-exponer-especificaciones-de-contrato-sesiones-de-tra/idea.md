<idea-doc>

## Problema

El MCP `market-data` no expone información de **sesiones de trading ni feriados de contrato**. Las 3 tools actuales (`get_asset_levels`, `get_chart_objects`, `obtener_calendario_macro`) cubren precio/técnico, niveles dibujados a mano y calendario económico — ninguna responde "¿opera el activo X mañana y en qué horario?". `config/activos.json` solo guarda un `horario_mercado` en texto libre, estático, sin ajuste por feriados y sin fuente en el broker (ej. `"09:30-16:00 ET (10:30-17:00 CLT)"` para acciones/índices US).

Esto se detectó el 2026-07-02 al preparar el aviso de `/dato_macro` sobre el feriado de EE.UU. del viernes 3 de julio: el mensaje final (`data/mensajes/2026-07-02/us100/dato_macro/16-59_dato_macro.txt`) tuvo que redactarse con lenguaje de cobertura ("confirma en tu plataforma el horario real... los feriados pueden cambiar las sesiones según el bróker") en vez de una afirmación determinista, porque no hay ninguna fuente fiable para confirmarlo. Esto viola el principio del proyecto de que el análisis debe ser accionable y sin ambigüedad para el cliente.

## Contexto observado

**Arquitectura del MCP** (`src/market_data_mcp/`):
- `server.py` — registra tools vía `<módulo>.register(mcp)`; instancia `FastMCP` única con `mask_error_details=False`. Cada tool nueva sigue el patrón: módulo en `tools/`, función `register(mcp)` con `@mcp.tool` interno, importado y registrado en `server.py` (3 líneas: import, `X.register(mcp)`).
- `catalog.py` — fuente única de tickers válidos: `VALID_TICKERS: dict[ticker_mt5, digits]`, cargado una vez desde `config/activos.json`. Toda tool nueva que reciba `ticker` debe validar contra este catálogo primero (`TICKER_NOT_FOUND` si no está).
- `mt5_client.py` — cliente MT5 vendorizado, minimalista (conexión, velas, EMA/ATR/MACD/Bollinger). `MetaTrader5` se importa **de forma perezosa** dentro de cada función — nunca a nivel de módulo — para que el paquete sea importable en CI sin MT5 instalado (`DEP001` en `pyproject.toml` ya declara `MetaTrader5` como dependencia intencionalmente no instalada/no resuelta). Una tool de especificación de contrato necesitaría una función nueva aquí, ej. `get_symbol_info(ticker)` / `get_session(ticker, day, index)`, con el mismo patrón de import perezoso.
- **Contrato de error uniforme** en las 3 tools existentes: `{"error": "CÓDIGO_MAYUSCULAS", "message": "texto explicativo"}` — nunca `None` ni array vacío silencioso. Códigos ya usados: `TICKER_NOT_FOUND`, `MT5_UNAVAILABLE`, `INVALID_TIMEFRAME`, `INSUFFICIENT_DATA`, `MT5_COMMON_FILES_UNSET`, `NO_OBJECTS_FILE`, `OBJECTS_UNREADABLE`, `OBJECTS_STALE`, `CHART_NOT_FOUND`, `NO_CALENDAR_FEEDS`, `INVALID_IMPACT`.
- **Sin `resources` MCP**: el issue ya verificó (`ListMcpResources`) que market-data no publica ninguno; esta feature encajaría igual de bien como tool (consistente con las 3 existentes) o como resource de solo-lectura — a decidir en Design.
- **Regla de decimales** (`digits` de `config/activos.json`, vía `catalog.py`) se aplica en todas las tools que devuelven precios; una tool de spec de contrato también expondría `digits`, `volume_min/step`, `contract_size`, reforzando ese catálogo en vez de duplicarlo.

**`config/activos.json`**:
- Estructura: `forex_commodities[]`, `indices[]`, `acciones{sector: {componentes[]}}`, `activos_complementarios{}`.
- Cada activo trae `horario_mercado` como **string libre**, ej. `"09:00-16:00 CLT"`, `"24h (principal: sesión NY)"`, `"09:30-16:00 ET (10:30-17:00 CLT)"` — sin estructura, sin fuente en broker, sin noción de feriados ni de día de la semana.
- Ya trae un comentario embebido ("Verificar con `symbol_info('TICKER').digits` en MT5 si hay dudas" — mencionado en el issue) que anticipa exactamente este hueco.

**Limitación técnica clave de MT5 (riesgo central para Design)**:
- La API Python de MetaTrader5 separa `symbol_info(symbol)` (specs estáticas: `trade_mode`, `digits`, `volume_min/max/step`, `trade_contract_size`, etc.) de `symbol_info_session_quote(symbol, day_of_week, session_index)` y `symbol_info_session_trade(symbol, day_of_week, session_index)`, que devuelven horarios **por día de la semana recurrente** (0=domingo…6=sábado), no un calendario con fechas concretas.
- Esto significa que MT5 puede confirmar el horario **habitual** de un día de la semana, pero **no** tiene una noción nativa de "feriado puntual" (ej. 4 de julio trasladado a un viernes específico de 2026): un feriado de bolsa de un solo día normalmente no cambia la sesión recurrente de "viernes" en el broker — el broker simplemente no cotiza ese día concreto sin que la tabla de sesiones lo refleje de antemano. La opción "inferir feriados de que la sesión venga vacía" (mencionada en el issue) solo cubre patrones recurrentes (fines de semana, día sin sesión estructural), **no** feriados puntuales de calendario bursátil (NYSE/NASDAQ).
- Confirmar de forma determinista y anticipada "¿opera el activo X mañana [fecha concreta]?" para un feriado puntual probablemente requiera **cruzar con un calendario de feriados de bolsa mantenido aparte** (NYSE/NASDAQ para acciones/US100, SSE para el proxy chino si aplica, feriados BCCh/bancarios para USD/CLP) — no hay ninguna librería de este tipo entre las dependencias actuales (`pyproject.toml` solo lista `fastmcp`, `pandas`; nada como `pandas_market_calendars` o similar).

**Patrones de test** (`tests/conftest.py`, `tests/test_levels.py`, `tests/test_calendar.py`, `tests/test_chart_objects.py`):
- Fixture `collector` (stub de `mcp.tool` que captura funciones para invocarlas directo, sin runtime real) — usado en los 3 test files existentes para probar el contrato de error sin depender de MT5 ni red.
- `test_server.py` es un smoke test de import/bootstrap; toda tool nueva registrada en `server.py` seguiría cubierta ahí sin cambios.
- Ausencia de MT5 en CI: los tests actuales de `get_asset_levels` verifican que, sin MT5, la tool retorna `{"error": "MT5_UNAVAILABLE", ...}` en vez de lanzar — el mismo patrón aplicaría a la tool nueva.

**Docs relevantes**:
- `docs/superpowers/specs/2026-06-05-calendario-macro-nativo-mt5-design.md` y `docs/superpowers/plans/2026-06-05-calendario-macro-nativo-mt5.md` — precedente de diseño/plan para una tool nativa MT5 con contrato de error explícito; útil como plantilla de estructura para el design-doc de esta feature.
- `docs/design/websearch-calendario-noticias.design.md` — precedente de manejo de "sin eventos" (fin de semana/feriado) como resultado esperado, no error.
- No existe hoy ningún doc sobre sesiones/feriados de contrato — este sería el primer diseño del tema.

## Hipótesis de solución

Agregar una tool nueva (`get_symbol_spec(ticker)` o nombre equivalente) al MCP `market-data`, siguiendo el patrón exacto de las 3 tools existentes:
1. **Módulo nuevo** `src/market_data_mcp/tools/symbol_spec.py` con `register(mcp)`, validación de ticker contra `catalog.VALID_TICKERS` (mismo error `TICKER_NOT_FOUND`), e import perezoso de `MetaTrader5` dentro de una función nueva en `mt5_client.py` (ej. `get_symbol_info(ticker)`, `get_session_quote/trade(ticker, day, index)`).
2. **Payload mínimo**: `trade_mode`, `digits`, `volume_min/step`, `contract_size`, sesiones de quote/trade por día de semana (0-6), y algún indicador de zona horaria/offset del servidor MT5.
3. **Feriados puntuales**: dado que MT5 no los expone de forma nativa por fecha, evaluar en Design entre (a) cruzar con un calendario de feriados de bolsa mantenido aparte en el repo (dato estático versionado, ej. JSON con fechas NYSE/NASDAQ por año) vs (b) exponer solo el patrón recurrente semanal y dejar la detección de feriados puntuales fuera del alcance de esta tool (cubierta en otro momento, quizás cruzando con `obtener_calendario_macro` si Investing.com marca el día como feriado). Ninguna opción es obviamente superior sin decidir el trade-off de mantenimiento vs cobertura — es la decisión de diseño central de este cambio.
4. **Contrato de error**: reutilizar `TICKER_NOT_FOUND`, `MT5_UNAVAILABLE` (mismos códigos que `get_asset_levels`); agregar código(s) nuevos específicos si la sesión no está disponible para ese símbolo/día (ej. `SESSION_NOT_FOUND` o similar — nombre exacto a definir en Design).
5. Documentar la nueva tool en `mcp.instructions` de `server.py` (bloque descriptivo, igual que las 3 actuales) y en el `CLAUDE.md` (tabla de MCP Servers) una vez cerrado el ciclo.

## Preguntas abiertas

1. **Nombre y forma de la tool**: ¿`get_symbol_spec(ticker)` de propósito general (specs + sesiones) o separar en dos tools (`get_contract_specs` + `get_trading_sessions`)? ¿O exponerlo como MCP resource dado que hoy no hay ninguno?
2. **Estrategia de feriados puntuales**: ¿mantener un calendario de feriados de bolsa aparte en el repo (qué exchanges cubrir: NYSE/NASDAQ para US100/acciones, ¿algo para XAUUSD/WTI/USDCLP?), inferir solo patrones recurrentes vía MT5, o combinar con `obtener_calendario_macro`? ¿Quién actualiza ese calendario cada año?
3. **Consulta por fecha concreta**: la tool ¿acepta un parámetro `fecha` (ej. "mañana", una fecha ISO) para responder "¿opera el día X?", o solo devuelve el patrón semanal crudo y el comando (`/dato_macro`) hace el cruce con la fecha?
4. **Cobertura de zona horaria**: `symbol_info_session_*` de MT5 devuelve horas en zona horaria del **servidor del broker**, no en hora Chile. ¿Se convierte dentro del MCP (siguiendo la convención `hora_chile.ps1` / `zoneinfo` ya usada en `calendar.py`) o se deja crudo con un campo de offset para que el comando decida? La regla `project_hora_servidor_mt5` de memoria dice que el calendario nativo MT5 (#53) usa hora de servidor tal cual — ¿aplica igual aquí o esta tool sí necesita conversión porque alimenta un mensaje de cliente en hora Chile?
5. **Relación con `config/activos.json`**: ¿el campo `horario_mercado` (texto libre) se deprecia/reemplaza una vez que la tool esté disponible, o coexisten (uno como fallback documental, otro como fuente viva)?
6. **Alcance de "trade_mode"**: MT5 puede reportar un símbolo como `SYMBOL_TRADE_MODE_DISABLED` temporalmente (ej. exactamente en un feriado) — ¿eso es suficiente señal de "no opera hoy" en el momento de la consulta, o solo sirve para confirmar en tiempo real (no para anticipar "mañana")?
7. **Testabilidad sin MT5**: igual que `get_asset_levels`/`get_chart_objects`, se necesita definir qué mockear para cubrir el camino feliz sin depender del terminal — ¿se vendoriza una función `get_symbol_info`/`get_session` en `mt5_client.py` mockeable como `get_rates`?

## Referencias

- Issue #104 (bbenja11/grupo-analisis-mercado): "market-data: exponer especificaciones de contrato (sesiones de trading y feriados) vía symbol_info"
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\server.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\catalog.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\mt5_client.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\tools\levels.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\tools\calendar.py`
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\tools\chart_objects.py`
- `C:\Users\bbrav\grupo-analisis-mercado\config\activos.json` (campo `horario_mercado`)
- `C:\Users\bbrav\grupo-analisis-mercado\tests\conftest.py`, `tests\test_levels.py`, `tests\test_calendar.py`, `tests\test_chart_objects.py`, `tests\test_server.py`
- `C:\Users\bbrav\grupo-analisis-mercado\pyproject.toml` (DEP001 exime `MetaTrader5` — import perezoso, no instalado en CI)
- `C:\Users\bbrav\grupo-analisis-mercado\src\market_data_mcp\.env.example`
- `C:\Users\bbrav\grupo-analisis-mercado\docs\superpowers\specs\2026-06-05-calendario-macro-nativo-mt5-design.md`
- `C:\Users\bbrav\grupo-analisis-mercado\docs\design\websearch-calendario-noticias.design.md`
- Mensaje de contexto inmediato: `C:\Users\bbrav\grupo-analisis-mercado\data\mensajes\2026-07-02\us100\dato_macro\16-59_dato_macro.txt` (aviso de feriado que motivó el issue)

</idea-doc>
