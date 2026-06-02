# Arquitectura del sistema

## Visión general

El sistema conecta a Claude Code (agente IA) con el flujo de trabajo diario del director de trading. En lugar de escribir mensajes manualmente, el director invoca un comando y el agente genera el contenido formateado para WhatsApp, lo muestra para aprobación, y luego el director lo copia al grupo.

```
┌─────────────────────────────────────────────────────────────┐
│                     DIRECTOR DE TRADING                      │
│                  invoca /lunes, /alerta, etc.                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE (agente)                    │
│                                                              │
│  Lee config/ → llama MCPs → genera mensaje → muestra draft  │
└──────┬───────────────────────────┬──────────────────────────┘
       │                           │
       ▼                           ▼
┌─────────────┐           ┌────────────────────┐
│ MCP          │           │ Archivos locales    │
│ market-data  │           │ config/activos.json │
│ (activo)     │           │ config/agenda...    │
│              │           │ data/historial...   │
│ • get_asset_ │           └────────────────────┘
│   levels     │
│              │  + WebSearch (calendario
│              │    y noticias, investing.com)
│              │
└─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                  APROBACIÓN DEL DIRECTOR                     │
│         ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?        │
└───────────────────────────┬─────────────────────────────────┘
                            │
          ┌─────────────────┴──────────────────┐
          ▼                                     ▼
┌─────────────────┐                   ┌────────────────────┐
│ Modo actual:     │                   │ Modo futuro:        │
│ texto en pantalla│                   │ Evolution API       │
│ → director copia │                   │ → envío automático  │
│ → pega en WA     │                   │   al grupo WA       │
└─────────────────┘                   └────────────────────┘
```

## MCPs (Model Context Protocol)

Los comandos de Claude Code usan herramientas externas via MCP. El estado actual:

| MCP | Estado | Herramientas clave |
|-----|--------|--------------------|
| **market-data** | ✅ Activo | `get_asset_levels` (análisis técnico MT5) |
| **WebSearch (investing.com + fuentes oficiales)** | ✅ Activo | Calendario económico y noticias |
| **WhatsApp (Evolution API)** | ⏳ Pendiente Docker | `send_message` al grupo |
| **TrendRadar / Firecrawl / Finnhub** | ❌ No activos | Reemplazados por market-data (MT5) + WebSearch |

### MCP market-data — herramientas

| Herramienta | Parámetros principales | Retorna |
|-------------|----------------------|---------|
| `get_asset_levels` | `ticker`, `timeframe` | Precio, soportes/resistencias, sesgo, RSI, ATR |
| `get_economic_events` | — | **Deprecada** → `{"error": "DEPRECATED"}` (usar WebSearch) |
| `get_market_context` | — | **Deprecada** → `{"error": "DEPRECATED"}` (usar WebSearch) |

> **Calendario y noticias vía WebSearch**: el calendario económico y las noticias relevantes ya **no** se obtienen desde un MCP. Se obtienen con la herramienta `WebSearch` sobre **investing.com + fuentes oficiales** (Fed, BCCh, OPEP+, EIA, BLS) directamente en los comandos `/dato_macro` y `/noticia` (y los comandos de día). Las tools `get_economic_events` / `get_market_context` del MCP `market-data` quedaron **deprecadas** (devuelven `{"error": "DEPRECATED"}`). Motivo: Finnhub producía errores de temporalidad y atingencia. Solo el análisis técnico MT5 (`get_asset_levels`) sigue activo en el MCP. Ver `docs/design/websearch-calendario-noticias.design.md`.

## Flujo de aprobación semi-automático

Este flujo aplica a **todos** los comandos sin excepción:

1. El comando genera el borrador del mensaje.
2. Claude lo muestra en pantalla con formato WhatsApp.
3. Pregunta: *¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?*
4. Si hay ajustes: el director los indica y Claude regenera.
5. Al aprobar: Claude guarda el mensaje en `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt`.
6. El director copia el texto y lo pega en el grupo.

**Regla de guardado**: el archivo se crea con Write directamente, sin bash. Formato de nombre: `2026-05-31_14-30_apertura.txt`.

## Gestión de señales operativas

Las señales tienen un límite duro de **3 por semana**. El archivo `data/historial_senales.json` registra todas las señales y es consultado por `scripts/senal_manager.py` antes de generar una nueva.

Campos obligatorios de una señal:
- ticker, nombre activo, dirección (BUY/SELL)
- entrada, TP, SL (en puntos y en CLP)
- volumen, tipo (swing / scalper)
- hasta 3 bullets de análisis

Los clientes siempre ven cuánto ganan y cuánto pierden en pesos chilenos, sin calcular nada.

## Rotación de activos

Cada día se cubren 2-3 activos (3 los viernes), rotando para que todos reciban atención durante la semana:

| Día | Ejemplo de rotación |
|-----|---------------------|
| Lunes | USD/CLP · XAU/USD |
| Martes | WTI · US100 |
| Miércoles | USD/CLP · WTI (prioridad EIA) |
| Jueves | XAU/USD · US100 |
| Viernes | USD/CLP · XAU/USD · WTI |

La configuración real se lee de `config/agenda_semanal.json` y puede ajustarse según el contexto de la semana.

## Temporalidades y tipo de operativa

| Temporalidad | Tipo de operativa | Descripción |
|---|---|---|
| 15M | Scalper | Movimientos muy cortos dentro del día, alta rotación |
| 1H | Intradía corto | Movimientos del día, confirmación de entradas |
| 4H | Intradía / swing corto | Tendencia del día, operativas de varias horas |
| 1D | Swing | Lectura general, operaciones de días |

Cada análisis indica explícitamente su temporalidad. Ejemplo: *"Niveles en 4H — operativa intradía/swing corto"*.

## Indicadores técnicos — regla de uno

Un aviso = un indicador. NUNCA mezclar múltiples señales técnicas en el mismo mensaje:

- **ATR** → volatilidad (especialmente útil en USD/CLP)
- **RSI** → aviso cuando cruza zona de sobrecompra/sobreventa
- **MACD** → aviso en cruces relevantes
- **Medias móviles** → aviso en cruces de MA50/MA200
