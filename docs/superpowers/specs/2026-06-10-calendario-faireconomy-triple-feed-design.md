# Diseño — Calendario macro vía triple feed Fair Economy (ForexFactory + MetalsMine + Energy EXCH)

> **Spec (Fase Discovery/diseño, ciclo Pulse).**
> Fecha: 2026-06-10. Estado: aprobado para pasar a plan de implementación.

## 1. Problema y objetivo

El calendario macroeconómico usa hoy MT5 nativo (`CalendarValueHistory()`) como fuente primaria,
exportado por el Service MQL5 `CalendarExporter.mq5` a `Common/Files/calendario_macro.json`.
Esto tiene tres limitaciones concretas:

1. **Dependencia del terminal**: si el Service MQL5 cae o el terminal no está abierto, el JSON no
   se actualiza y los comandos caen a fallback WebSearch.
2. **Cobertura incompleta**: MT5 no reporta inventarios EIA de WTI (crítico para `/miercoles`) ni
   LME Copper Inventories (activo del catálogo). Los datos de metales y energía requieren fallback
   manual hoy.
3. **Calidad del dato**: MT5 a veces deja `forecast` y `previo` vacíos. Fair Economy entrega esos
   campos con mayor consistencia.

**Objetivo**: reemplazar el pipeline MT5 por tres feeds JSON públicos del CDN de Fair Economy
(`nfs.faireconomy.media`), que cubren los 4 activos del catálogo de forma nativa y sin dependencia
del terminal. MT5 queda exclusivamente para precios y niveles técnicos (`get_asset_levels`).

## 2. Decisiones de diseño

| Decisión | Resolución | Razón |
|---|---|---|
| **Fuente primaria** | Triple feed Fair Economy (`ff` + `mm` + `ee`) | Cubre los 4 activos del catálogo sin dependencia del terminal MT5 |
| **MT5 calendario** | Retirado del flujo | `CalendarExporter.mq5` → `mql5/archive/`; `leer_calendario_json()` eliminado |
| **Fallback** | WebSearch investing.com si los 3 feeds fallan | Conserva la robustez del sistema ante caída del CDN |
| **Zona horaria** | ISO 8601 con offset → `America/Santiago` vía `zoneinfo` (stdlib) | Sin deps extra; correcto para DST de Chile |
| **Deduplicación** | Por `(title, date)` al mergear los 3 feeds | OPEC aparece en `ff` y `ee`; evitar duplicados |
| **Enganche glosario** | Sigla como palabra en el título; luego `titulos_ff`; luego `glosario_pendiente: true` | Reutiliza la infraestructura de issue #46 sin reescritura del glosario |
| **Falla parcial** | Retorna eventos disponibles + campo `feeds_fallidos` | Transparencia al director sin interrumpir el flujo |
| **Caché** | Sin caché en archivo; TTL en memoria opcional en fases siguientes | El calendario se llama 1-2 veces al día — overhead de archivo no justificado |

## 3. Cobertura por feed

| Feed | Endpoint | Activos del catálogo cubiertos | Ejemplo de eventos clave |
|---|---|---|---|
| ForexFactory | `ff_calendar_thisweek.json` | USD/CLP · XAU/USD · US100 | NFP, IPC/CPI, PMI, PCE, Fed, ADP, JOLTS |
| MetalsMine | `mm_calendar_thisweek.json` | COPPER | LME Copper Inventories (diario) |
| Energy EXCH | `ee_calendar_thisweek.json` | WTI | EIA Crude Oil Inventories, OPEC meetings, Natural Gas Storage, Baker Hughes |

## 4. Arquitectura y flujo de datos

```
Fair Economy CDN  (nfs.faireconomy.media)
   ff_calendar_thisweek.json   →  macro USD/EUR/JPY/GBP/CAD/AUD/CNY/NZD
   mm_calendar_thisweek.json   →  metales (LME Copper Inventories)
   ee_calendar_thisweek.json   →  energía (EIA Crude Oil, OPEC, Natural Gas)
            │  _fetch_feed(slug)  ×3  (falla silenciosa → [])
            ▼
   _merge_feeds()
      • merge listas, dedup por (title, date)
      • normaliza campos al schema canónico
      • convierte date ISO 8601 → "YYYY-MM-DD HH:MM" en America/Santiago
      • engancha data/glosario_siglas.json por sigla o titulos_ff
            ▼
   obtener_calendario_macro(solo_hoy, min_impact)
      • filtra por impacto y fecha
      • si merge vacío por fallas → {"error": "NO_CALENDAR_FEEDS", ...}
            ▼
   /dato_macro · /noticia · /miercoles · etc.
   (si error NO_CALENDAR_FEEDS → fallback WebSearch investing.com)
```

## 5. Componentes y responsabilidades

### 5.1 `src/market_data_mcp/tools/calendar.py` — reescritura

**`_fetch_feed(slug: str) -> list[dict]`**
- GET `https://nfs.faireconomy.media/{slug}_calendar_thisweek.json`
- Timeout: 10 s. Si falla (red, 4xx, 5xx, JSON inválido) → retorna `[]`, registra warning con el slug.
- Sin reintentos — la falla parcial es manejada por `_merge_feeds`.

**`_normalizar_evento(ev: dict, slug: str) -> dict`**
- Mapea campos Fair Economy al schema canónico:

| Campo salida | Fuente | Notas |
|---|---|---|
| `nombre` | `title` | tal cual |
| `divisa` | `country` | tal cual |
| `impacto` | `impact` | `High→alto`, `Medium→medio`, `Low→bajo`, `Holiday→festivo` |
| `hora_servidor` | `date` (ISO 8601) | convertido a `"YYYY-MM-DD HH:MM"` en `America/Santiago` |
| `forecast` | `forecast` | tal cual (puede ser `""`) |
| `previo` | `previous` | tal cual (puede ser `""`) |
| `fuente` | slug | `"ff"` / `"mm"` / `"ee"` |

**`_enganchar_glosario(nombre: str, glosario: dict) -> dict | None`**
1. Busca si alguna clave sigla del glosario aparece como palabra en `nombre` (case-insensitive).
   Ej: `"CPI"` en `"Core CPI m/m"` → match.
2. Si no, busca en `titulos_ff` de cada entrada del glosario.
   Ej: `"Nonfarm Payrolls"` → entrada `"NFP"` con `"titulos_ff": ["Nonfarm Payrolls"]`.
3. Si no → retorna `None` (el evento recibe `glosario_pendiente: true`).

**`_merge_feeds() -> tuple[list[dict], list[str]]`**
- Llama `_fetch_feed` para `ff`, `mm`, `ee`.
- Merge las 3 listas; deduplica por `(nombre, hora_servidor)`.
- Retorna `(eventos_normalizados, feeds_fallidos)`.

**`obtener_calendario_macro(solo_hoy, min_impact)`** — misma firma pública
- Llama `_merge_feeds()`.
- Si todos fallaron → `{"error": "NO_CALENDAR_FEEDS", "message": "..."}`.
- Filtra por `min_impact` y `solo_hoy`.
- Engancha glosario evento por evento.
- Resultado incluye `feeds_fallidos` si aplica.

### 5.2 `src/market_data_mcp/mt5_client.py` — eliminar `leer_calendario_json()`

El método queda fuera del cliente. MT5 solo expone funciones de precios/niveles/indicadores.

### 5.3 `mql5/CalendarExporter.mq5` — archivar

Mover a `mql5/archive/CalendarExporter.mq5`. Sin referencias activas en el código.

### 5.4 `data/glosario_siglas.json` — agregar `titulos_ff`

Agregar el campo a las entradas donde la sigla no aparece literalmente en el título de ForexFactory.
Casos confirmados que requieren el campo:

| Sigla | `titulos_ff` a agregar |
|---|---|
| `NFP` | `["Nonfarm Payrolls", "Employment Change"]` |
| `JOLTS` | `["Job Openings"]` |
| `PIB` | `["GDP q/q", "Final GDP q/q", "Prelim GDP q/q", "GDP m/m"]` |
| `IPP` | `["PPI m/m", "Core PPI m/m", "Final PPI m/m"]` |
| `IPC` | `["CPI m/m", "Core CPI m/m", "CPI y/y", "Final CPI m/m"]` |

Entradas que ya hacen match por sigla literal y **no** necesitan `titulos_ff`: `PMI`, `ISM`, `ADP`,
`PCE`, `CPI`, `PPI`, `GDP`, `OPEP`.

## 6. Contrato de error

| Situación | Respuesta de la tool | Acción del comando |
|---|---|---|
| Los 3 feeds fallan | `{"error": "NO_CALENDAR_FEEDS", "message": "..."}` | Fallback WebSearch + avisar al director |
| 1-2 feeds fallan, ≥1 responde | Eventos disponibles + `"feeds_fallidos": ["mm"]` | Transparente — director ve qué fuente faltó |
| Sin eventos tras filtro | `{"eventos": [], "info": "sin eventos de impacto medio/alto hoy", "source": "faireconomy"}` | Caso legítimo, no error |
| `min_impact` inválido | `{"error": "INVALID_IMPACT", ...}` | Igual que hoy |

## 7. Testing

Tests en `tests/test_calendar.py`, mismo patrón que `test_levels.py` — sin requerir red en CI
(feeds mockeados con `monkeypatch` o `unittest.mock`):

| Test | Qué verifica |
|---|---|
| Camino feliz | 3 feeds mockeados → merge + dedup + schema correcto |
| Deduplicación | Mismo evento en `ff` y `ee` → aparece una sola vez |
| Conversión de zona | Fecha ISO con offset EDT → hora Chile correcta |
| Glosario por sigla | `"Core CPI m/m"` → entrada `IPC` enganchada |
| Glosario por `titulos_ff` | `"Nonfarm Payrolls"` → entrada `NFP` enganchada |
| Sin match glosario | Evento desconocido → `glosario_pendiente: true` |
| Falla parcial | 1 feed falla → resultado incluye `feeds_fallidos` |
| Falla total | 3 feeds fallan → `{"error": "NO_CALENDAR_FEEDS", ...}` |
| Filtro `min_impact` | Evento `Low` no aparece con umbral `medium` |
| `solo_hoy=True` | Evento de otra semana no aparece |

## 8. Ajustes de documentación

- **`CLAUDE.md`**: actualizar tabla MCP — `obtener_calendario_macro` ahora usa Fair Economy como
  fuente primaria; quitar mención de `generated_at` / frescura de archivo; WebSearch sigue como
  fallback.
- **`docs/architecture.md`**: actualizar flujo de calendario.
- Retirar cualquier referencia a `CalendarExporter.mq5` y `leer_calendario_json` en docs.

## 9. Fuera de alcance (YAGNI)

- Caché en archivo: innecesario para 1-2 llamadas/día.
- Energy EXCH para criptomonedas o acciones: el catálogo no las incluye.
- Reintentos automáticos por feed: la falla parcial ya es manejada con `feeds_fallidos`.
- Parsing de `actual` en tiempo real: los feeds publican `actual` cuando el dato sale; no se
  necesita lógica extra — llega en el mismo campo.
