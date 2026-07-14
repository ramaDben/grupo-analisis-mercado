# Diseño — Calendario macro nativo MT5 vía puente MQL5→Python

> **Spec (Fase Discovery/diseño, ciclo Pulse).** Referencia: issue #53 y documento Discovery #54.
> Fecha: 2026-06-05. Estado: aprobado para pasar a plan de implementación.

## 1. Problema y objetivo

El calendario macroeconómico depende hoy de `WebSearch` sobre investing.com (las tools `get_economic_events` / `get_market_context` quedaron deprecadas). Esto genera dos problemas:

1. **Fragilidad de fuente:** la tabla de investing.com a veces no renderiza y obliga a fallbacks manuales.
2. **Asincronía temporal:** la hora de la noticia y el reloj del precio (servidor del broker, `TimeTradeServer()`) pueden desfasarse, lo que afecta la precisión al clasificar eventos `✅ YA SALIÓ` / `🕐 PRÓXIMO`.

**Objetivo:** que **MT5 sea la única fuente de verdad temporal**. Extraer el calendario nativo de MT5 (`CalendarValueHistory()`) y exponerlo como una nueva tool del MCP `market-data`, alineado al mismo reloj que las velas de precio. Esto, además, hace el sistema **multi-broker / multi-país** de forma natural (la hora y el idioma del calendario siguen al terminal).

## 2. Decisiones de diseño (cerradas en brainstorming)

| Decisión | Resolución | Razón |
|---|---|---|
| **Rol del calendario nativo** | Fuente **primaria**; WebSearch investing.com queda como **fallback** | Robustez sin perder lo ya construido |
| **Conversión horaria** | **Sin conversiones** — se trabaja en hora del servidor MT5 tal cual | Multi-broker/multi-país; broker actual ya está en hora Chile, sin discrepancia para el cliente hoy |
| **Transporte MQL5→Python** | **Opción A: archivo JSON** en `Common/Files`, refresh cada 1 h | El calendario es diario/semanal, no necesita baja latencia; sobrevive si el Service muere; sin dependencia ZeroMQ |
| **Idioma de los eventos** | Nombres **tal cual los da MT5** (español, por config del terminal) | MT5 localiza `MqlCalendarEvent` según idioma del terminal → cero capa de traducción |
| **Diccionario rápido (siglas)** | `data/glosario_siglas.json` conserva solo las **explicaciones novatas**, enganchadas por `event_id` | El valor educativo (issue #46) no lo trae MT5; el texto es propio del proyecto |
| **Llave de enganche glosario** | `event_id` de MT5 (no el texto) | Estable entre versiones e idiomas |
| **Frescura** | Refresh 1 h / **stale si `generated_at` > 3 h** | El calendario macro casi no cambia intradía; menos I/O |

## 3. Arquitectura y flujo de datos

```
Terminal MT5 (broker en hora Chile, terminal en español)
   │  CalendarValueHistory()  → nombres ya en español
   ▼
Service MQL5  mql5/CalendarExporter.mq5  (refresh cada 1 h)
   │  filtra por impacto (medio/alto), escribe
   ▼
Common/Files/calendario_macro.json
   { generated_at, server_tz_note, eventos:[ {event_id, nombre, pais, impacto, hora_servidor, previo, forecast, actual} ] }
   │  lee
   ▼
market_data_mcp · obtener_calendario_macro()
   • valida frescura (stale si generated_at > 3 h)
   • engancha glosario_siglas.json por event_id → explicación novata
   • hora = hora servidor MT5 tal cual (sin conversiones)
   • contrato error: {error: NO_CALENDAR_FILE | STALE_CALENDAR | BAD_CALENDAR_JSON}
   ▼
/dato_macro · /noticia
   MT5 = fuente primaria; si la tool devuelve {error:…} → fallback WebSearch investing.com
```

## 4. Componentes y responsabilidades

### 4.1 `mql5/CalendarExporter.mq5` (nuevo — Service)
- **Qué hace:** corre en segundo plano en el terminal; cada 1 h llama `CalendarValueHistory()` para el rango del día, filtra por impacto (medio/alto) y escribe `Common/Files/calendario_macro.json`.
- **Output JSON:**
  ```json
  {
    "generated_at": "2026-06-05 09:00",
    "server_tz_note": "hora servidor MT5 (broker actual = hora Chile)",
    "eventos": [
      {
        "event_id": 840030016,
        "nombre": "Nóminas no agrícolas",
        "pais": "Estados Unidos",
        "divisa": "USD",
        "impacto": "alto",
        "hora_servidor": "2026-06-05 09:30",
        "periodo": "Mayo 2026",
        "previo": "175K",
        "forecast": "190K",
        "actual": null
      }
    ]
  }
  ```
- **Depende de:** API nativa de calendario de MT5. Nada más.

### 4.2 `market_data_mcp/tools/calendar.py` (reemplaza el stub DEPRECATED)
- **Qué hace:** registra `obtener_calendario_macro()`. Lee el JSON vía el cliente, valida frescura, engancha el glosario por `event_id`, devuelve eventos o `{error: …}`.
- **Interfaz:** `obtener_calendario_macro(solo_hoy: bool = True, min_impact: str = "medium")`.
- **Depende de:** `mt5_client.leer_calendario_json()`, `data/glosario_siglas.json`.
- Si un `event_id` no tiene entrada en el glosario, marca `glosario_pendiente: true` para que el agente lo explique al vuelo y se añada al JSON.

### 4.3 `market_data_mcp/mt5_client.py` (extender)
- **Qué hace:** añade `leer_calendario_json()` — localiza `Common/Files`, parsea, expone `generated_at`. Aislado para poder mockear en tests.

### 4.4 `market_data_mcp/server.py` (registrar)
- Registrar la nueva tool junto a `levels`. Actualizar el campo `instructions` del MCP (ya no describe "3 tools deprecadas").

### 4.5 `data/glosario_siglas.json` (reusar)
- Llave de enganche: `event_id` de MT5 → `{nombre_es, explicacion}`.

### 4.6 Comandos `/dato_macro` y `/noticia` (ajustar flujo)
- **Primero** `obtener_calendario_macro()`; **solo si** devuelve `{error:…}`, caen a WebSearch investing.com (el flujo actual queda como fallback documentado).

## 5. Manejo de errores (contrato explícito — nunca array vacío)

| Situación | Respuesta de la tool | Acción del comando |
|---|---|---|
| JSON no existe en `Common/Files` | `{error: "NO_CALENDAR_FILE", message: "…ejecutar CalendarExporter en MT5"}` | Fallback WebSearch + avisar al director |
| `generated_at` > 3 h | `{error: "STALE_CALENDAR", message: "calendario viejo, ¿Service caído?"}` | Fallback WebSearch + avisar |
| JSON corrupto / no parseable | `{error: "BAD_CALENDAR_JSON", message: "…"}` | Fallback WebSearch + avisar |
| Sin eventos del día tras filtro | `{eventos: [], info: "sin eventos de impacto medio/alto hoy"}` | Caso legítimo, **no** error |

## 6. Testing

- Tests de `calendar.py` con JSON **mockeado** (mismo patrón que `test_levels.py`, sin requerir MT5 en CI):
  - camino feliz (eventos + glosario enganchado),
  - `STALE_CALENDAR`,
  - `NO_CALENDAR_FILE`,
  - `BAD_CALENDAR_JSON`,
  - evento sin glosario → `glosario_pendiente: true`,
  - enganche correcto por `event_id`,
  - caso legítimo sin eventos (array vacío con `info`).
- El Service MQL5 **no** se testea en CI (requiere terminal); se valida manualmente. El formato del JSON es el contrato entre ambos lados y se documenta.

## 7. Ajustes de documentación (parte del entregable)

- **`CLAUDE.md`:**
  - Actualizar la regla canónica de hora → la hora pasa a ser **la del servidor MT5** (hoy = hora Chile).
  - Marcar `scripts\hora_chile.ps1` como ya **no obligatorio** para el calendario nativo (queda solo para el fallback WebSearch de origen extranjero).
  - Quitar `get_economic_events` de la lista de tools deprecadas y describir `obtener_calendario_macro`.
- **`docs/design/websearch-calendario-noticias.design.md`:** anotar que WebSearch pasa de fuente primaria a **fallback**.
- **Setup:** instrucción de compilar/instalar el Service MQL5 y activarlo en el terminal (Fase 5 operativa), incluyendo cómo verificar que está vivo (frescura del JSON).

## 8. Fuera de alcance (YAGNI)

- ZeroMQ / sockets (Opción B): descartado por sobreingeniería para un calendario diario.
- Conversión de zonas horarias en Python: eliminada por decisión de trabajar en hora servidor MT5.
- Noticias de mercado (`get_market_context`): este spec cubre solo el **calendario**; las noticias siguen por WebSearch.
