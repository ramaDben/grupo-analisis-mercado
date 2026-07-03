# Tasks — market-data: `get_symbol_spec` (especificaciones de contrato y sesiones) (#104)

> Desglose de implementación de la fase **break-to-tasks**. Consolida el diseño técnico
> (`design.md`, §9) en tareas atómicas, ordenadas por dependencia, mapeadas a los requisitos
> `R1..R11` / criterios de aceptación `AC1..AC13` de `spec.md`, cada una con su criterio de
> verificación **ejecutable**.
>
> **Contrato de entrada (read-only):** `spec.md` (requisitos + AC), `design.md` (ADR + algoritmo
> feriado-primero §4 + resolución `Q1..Q5` §5 + zona horaria §6).
> **Dominio Pulse:** mcp · **Bump sugerido:** minor (`type:feat`, tool aditiva).
> **Gate `DESIGN → APPLY`:** design aprobado por el director (bbenja11) el 2026-07-03T00:40:33Z
> (`design_approved_at` presente en el ledger). D-GATE-1 y D-GATE-2 aceptados (§10 de `design.md`).

## Invariantes de arquitectura (obligatorias)

- Dependencia unidireccional: **tool/service (`tools/symbol_spec.py`) → adapter (`mt5_client.py`)
  → stdlib**. La tool NUNCA importa `MetaTrader5` directamente; solo el adapter lo toca (import
  perezoso), igual que `levels.py` consume `get_rates` del adapter.
- El módulo `tools/symbol_spec.py` y sus tests deben ser importables **sin** `MetaTrader5`
  instalado (RNF1) — mapeos por entero literal, no por constantes del paquete.
- Toda hora expuesta se convierte con `zoneinfo.ZoneInfo("America/Santiago")`, nunca offsets
  fijos (RNF2). `server_utc_offset_minutes` se expone crudo.
- Idioma español en docstrings, mensajes de error y claves de dominio (RNF3).
- Tool **aditiva**: no toca el comportamiento de las 3 tools existentes; `tests/test_server.py`
  sigue verde sin modificarlo (RNF4, AC13).

## Metodología (EDD + TDD, test-first)

Cada tarea de código lleva su criterio ejecutable como referencia al AC/CB de `spec.md`
(input/fixture/output ya especificados). Los tests de T11 se escriben **antes** de la
implementación de cada tarea, reproduciendo el fixture del AC correspondiente (patrón de
`tests/test_calendar.py`: stub `fastmcp` + fixture `collector` + `monkeypatch` de I/O).

---

## Fase A — Datos y adapter (base, sin dependencias)

- [x] **T1 — Adapter MT5 (I/O)** · `src/market_data_mcp/mt5_client.py` · *(R9)*
  Agregar dos funciones con import perezoso de `MetaTrader5` (patrón `get_rates`,
  `mt5_client.py:75-99`):
  - `get_symbol_info(ticker: str)` — envuelve `MetaTrader5.symbol_info(ticker)`.
  - `get_session(ticker: str, day_of_week: int, index: int, tipo: str)` — envuelve
    `symbol_info_session_quote` / `symbol_info_session_trade` según `tipo`.
  **Verificación:** funciones mockeables sin terminal; cubierto indirectamente por AC10
  (`ImportError` → `MT5_UNAVAILABLE`) y AC11 (`None` → `SESSION_UNAVAILABLE`).

- [x] **T2 — Dato de feriados versionado** · `config/feriados_bolsa.json` (nuevo) · *(R6)*
  Crear el JSON con clave `_meta` (`actualizado`, `fuente`, `proceso_actualizacion`) + clave
  `NYSE` = las 10 fechas ISO 2026 (`spec.md` R6), ordenadas ascendente, sin duplicados.
  **Verificación (AC12):** `rg -n '"NYSE"' config/feriados_bolsa.json` + parseo JSON → existe
  `_meta.actualizado` y `NYSE` tiene ≥9 fechas incluyendo `"2026-01-01"` y `"2026-12-25"`.
  **⛔ Bloquea Apply (D-GATE-2 / R-2):** verificar las 10 fechas contra
  `nyse.com/markets/hours-calendars` antes de mergear.

---

## Fase B — Esqueleto de la tool y validaciones (dependen de T1)

- [x] **T3 — Esqueleto de la tool** · `src/market_data_mcp/tools/symbol_spec.py` (nuevo) ·
  *(R1, R2, R5)*
  `register(mcp)` + `@mcp.tool get_symbol_spec(ticker: str, fecha: str | None = None)`.
  Validación de `ticker` contra `catalog.VALID_TICKERS` **como primer paso** (R2/R8, criterio de
  `levels.py:105-112`). Definir constantes de módulo: mapeo `trade_mode` por entero literal 0..4
  (§5.1) con `"UNKNOWN"` para valores inesperados; mapeo `ticker → exchange` (§5.3: 16 tickers =
  `US100.spot`, `US500.spot`, `US30.spot` + 13 acciones → `"NYSE"`, D-GATE-1 aceptado); tupla de
  las 7 claves de día en español sin tilde.
  **Verificación (AC1, AC2):** `rg -n "def register" tools/symbol_spec.py` = 1 coincidencia;
  `get_symbol_spec("NOEXISTE")` → `{"error": "TICKER_NOT_FOUND", "message": <str no vacío>}`.

- [x] **T4 — Validación de fecha (antes de MT5)** · `tools/symbol_spec.py` · *(R7, R8)*
  Parseo ISO **estricto** `YYYY-MM-DD` cuando `fecha is not None`, sin tocar MT5. Rechaza
  `DD-MM-YYYY`, fechas inexistentes (`2026-02-30`) y no-strings → `INVALID_FECHA`.
  **Verificación (AC9 / CB-2):** `get_symbol_spec("US100.spot", fecha="2026-02-30")` y
  `fecha="03-07-2026"` → ambas `{"error": "INVALID_FECHA", "message": <str no vacío>}`.

- [x] **T5 — Errores de MT5 (orden R8)** · `tools/symbol_spec.py` · *(R7, R8)*
  Mapear `ImportError`/fallo de conexión de `get_symbol_info` → `MT5_UNAVAILABLE` (criterio
  `levels.py:130-150`); ausencia de datos de sesión de `get_session` (`None`/error) →
  `SESSION_UNAVAILABLE`. Respetar orden: ticker → fecha → MT5 → sesión → construcción.
  **Verificación (AC10 / CB-7, AC11 / CB-8):** `get_symbol_info` lanza `ImportError` →
  `MT5_UNAVAILABLE`; `get_session` devuelve `None` → `SESSION_UNAVAILABLE`.

---

## Fase C — Construcción del payload (dependen de T3–T5)

- [x] **T6 — Specs estáticas + patrón semanal** · `tools/symbol_spec.py` · *(R3, R3.1, RNF2)*
  Armar las 10 claves de R3: `ticker`, `trade_mode` (via mapeo T3), `digits`, `volume_min`,
  `volume_step`, `contract_size`, `server_time`, `server_utc_offset_minutes`, `sesiones_semana`,
  `fuente="mt5"`. `sesiones_semana` = dict con las 7 claves fijas en orden; cada valor es lista
  de `{"quote":[ap,ci], "trade":[ap,ci]}` (0/1/N ventanas iterando `index=0,1,2,…` hasta que MT5
  devuelve `None`, §5.2); día sin sesión → `[]` (nunca `null`/ausente).
  **Verificación (AC3):** `get_symbol_spec("US100.spot")` sin `"error"`, con las 10 claves R3 y
  `sesiones_semana` con exactamente las 7 claves en español.

- [x] **T7 — Conversión de sesiones a hora Chile** · `tools/symbol_spec.py` · *(RNF2)*
  Helper con `zoneinfo` (§6): derivar offset del servidor MT5 (`server_utc_offset_minutes`),
  anclar cada endpoint (minutos desde medianoche, hora servidor) a fecha de referencia,
  construir `datetime` con `timezone(timedelta(minutes=offset))` y `astimezone(ZoneInfo(
  "America/Santiago"))`, formatear `"%H:%M"`. Sin offsets fijos. Límite documentado: no modela
  corrimiento de día (§6.3).
  **Verificación (AC4):** sesión 09:30-16:00 ET → `horario_chile == {"apertura":"10:30",
  "cierre":"17:00"}` (consistente con `activos.json`).

- [x] **T8 — Resolución determinista de `opera` (algoritmo feriado-primero §4)** ·
  `tools/symbol_spec.py` · *(R4, R4.1)*
  Cuando `fecha` presente, añadir `fecha_consultada`, `opera`, `motivo`, `horario_chile`,
  `calendario_feriados_fuente`. Orden: (1) feriado gana si ticker mapeado y `fecha ∈ feriados`
  → `feriado_bolsa`; (2) sesión vacía → `fin_de_semana` (sáb/dom) o `fuera_de_sesion_recurrente`;
  (3) solo si `fecha == hoy` en Chile y `trade_mode=="DISABLED"` → `trade_mode_disabled`; (4) si
  no → `opera=true`, `motivo=null`, `horario_chile` = primera ventana `trade`.
  `calendario_feriados_fuente` = `"config/feriados_bolsa.json (NYSE)"` si mapeado, si no `null`.
  **Verificación:** **AC5** (viernes feriado NYSE → `feriado_bolsa`, CB-9), **AC6** (sábado →
  `fin_de_semana`, CB-5), **CB-6** (día hábil sin sesión → `fuera_de_sesion_recurrente`),
  **AC7 / CB-3** (`XAUUSD` fecha feriado NYSE → `calendario_feriados_fuente is None`, nunca
  `feriado_bolsa`), **AC8 / CB-4** (`fecha=hoy` + `trade_mode="DISABLED"` → `trade_mode_disabled`).

---

## Fase D — Integración, documentación y tests

- [x] **T9 — Registro en el servidor** · `src/market_data_mcp/server.py` · *(R1, R10)*
  `import` del módulo + `symbol_spec.register(mcp)` (patrón 3 líneas de `server.py:82-86`);
  añadir una frase describiendo `get_symbol_spec` al bloque `instructions` de `FastMCP`
  (`server.py:63-80`).
  **Verificación (AC1 parte server, AC13):** `rg -n "symbol_spec" server.py` ≥ 2 líneas;
  `pytest tests/test_server.py` sigue verde **sin** modificar ese archivo.

- [x] **T10 — Docstring de limitación** · `tools/symbol_spec.py` · *(R11)*
  Documentar en el docstring de `get_symbol_spec` que `USDCLP`/`XAUUSD`/`WTI.spot` no tienen
  calendario de feriados en esta iteración (para ellos `opera` con fecha futura solo se basa en
  patrón semanal MT5; nunca `motivo:"feriado_bolsa"`). Limitación documentada, no bug.
  **Verificación:** docstring menciona los 3 tickers y la limitación; coherente con AC7/CB-3.

- [x] **T11 — Tests BDD (test-first)** · `tests/test_symbol_spec.py` (nuevo) · *(RNF1, RNF5)*
  Patrón `conftest.py` (stub `fastmcp`, fixture `collector`) + `monkeypatch` de
  `mt5_client.get_symbol_info`/`get_session`; helpers `_symbol_info_fake` / `_session_fake`
  (análogos a `_fila()` de `test_calendar.py`). Una prueba por AC/CB:
  `test_registro` (AC1), `test_ticker_invalido` (AC2/CB-1), `test_camino_feliz_sin_fecha` (AC3),
  `test_camino_feliz_con_fecha_habil` (AC4), `test_feriado_nyse` (AC5/CB-9),
  `test_fin_de_semana` (AC6/CB-5), `test_dia_habil_sin_sesion` (CB-6),
  `test_ticker_sin_cobertura_feriados` (AC7/CB-3), `test_trade_mode_disabled_hoy` (AC8/CB-4),
  `test_fecha_invalida` (AC9/CB-2), `test_mt5_no_disponible` (AC10/CB-7),
  `test_sesion_no_disponible` (AC11/CB-8), `test_feriados_bolsa_json` (AC12).
  **Verificación:** `pytest tests/test_symbol_spec.py` verde + `pytest tests/test_server.py`
  verde (AC13). Módulo importable sin `MetaTrader5` (RNF1).

- [ ] **T12 — Doc de cierre (diferible / opcional)** · `CLAUDE.md`, `docs/architecture.md`
  Actualizar la tabla de tools MCP (`market-data` gana la 4.ª tool). Fuera del núcleo del Change;
  puede diferirse a un Change de documentación. No bloquea la suite ni el merge del núcleo.

---

## Orden de ejecución recomendado

`T1, T2` (base) → `T3 → T4 → T5` (esqueleto + validaciones) → `T6 → T7 → T8` (payload) →
`T9, T10` (integración/doc) → `T11` (suite verde, test-first por tarea) → `T12` (opcional).

## Verificación global (Definition of Done)

- [x] `pytest tests/` completo en verde (incluye `tests/test_symbol_spec.py` nuevo y
  `tests/test_server.py` sin cambios — AC13/RNF4).
- [x] Los 13 criterios `AC1..AC13` de `spec.md` verificados por su test correspondiente.
- [x] `config/feriados_bolsa.json` versionado con `_meta` + `NYSE` (AC12) **y sus 10 fechas
  verificadas contra el calendario oficial NYSE** (D-GATE-2, bloquea merge).
- [x] `tools/symbol_spec.py` importable sin `MetaTrader5` (RNF1); tool NUNCA importa
  `MetaTrader5` directamente (invariante hexagonal).
- [x] Sin cambios de comportamiento en `get_asset_levels`/`get_chart_objects`/
  `obtener_calendario_macro` (RNF4).

## Criterios bloqueantes de Apply (elevados al gate humano — ya aceptados en Design)

- **D-GATE-1 (R-1):** mapeo NYSE extendido a los 3 índices US (`US100.spot`, `US500.spot`,
  `US30.spot`) + 13 acciones = 16 tickers. **Aceptado por el director (2026-07-02)** → implementar
  en T3 (§5.3). No requiere nueva aprobación.
- **D-GATE-2 (R-2):** exactitud de las 10 fechas NYSE 2026 de `config/feriados_bolsa.json`.
  **Aceptado como criterio bloqueante de T2 en Apply** — verificar contra
  `nyse.com/markets/hours-calendars` antes de mergear (no bloquea Design; sí bloquea el merge).
  **Estado en Apply (2026-07-02):** las 10 fechas fueron recalculadas de forma independiente
  con las reglas oficiales de feriados NYSE (fijas + "N-ésimo día del mes" + regla de
  observancia cuando el feriado cae sábado, aplicada al 4 de julio → observado el 3 de julio)
  usando aritmética de calendario determinista, y coinciden exactamente con las 10 fechas de
  `spec.md`/R6. **No se pudo contrastar contra `nyse.com/markets/hours-calendars` en vivo**
  (sin herramienta de navegación web disponible en este agente de Apply) — queda pendiente
  una verificación humana final contra la fuente oficial antes de mergear a producción.

## Pendiente de confirmación en Apply (no bloquea la transición a Apply)

- Enteros `SYMBOL_TRADE_MODE_*` (0..4) contra la versión de `MetaTrader5` instalada (§5.1, R-5).
- Si algún ticker real reporta >1 ventana de sesión/día relevante (§5.2, R-3): el contrato no
  cambia; `horario_chile` sigue usando la primera ventana `trade`.
