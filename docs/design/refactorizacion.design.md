# DISEÑO TÉCNICO — Refactorización grupo-analisis-mercado

## Contexto
Basado en `docs/ideas/refactorizacion-proyecto.idea.md`.
Diagnóstico confirmado tras leer todos los slash commands y scripts.

---

## Hallazgos clave (correcciones al spec)

- `config/activos.json` SÍ tiene US500 y US30 — área #6 del spec eliminada
- `/domingo.md` ya usa `mcp__reporte-flash__` correctamente — es el modelo a seguir
- El problema de encoding en nombres de archivo es solo visual en el listado de Windows; los archivos reales son UTF-8 válido (leer el contenido funciona)

---

## Cambios por área (diseño técnico)

---

### ÁREA A — Migrar comandos a `mcp__reporte-flash__`

**Problema**: 16 de 17 comandos usan una mezcla de `scripts/mt5_integration.py`, TrendRadar, Firecrawl o web search. Solo `/domingo` usa `mcp__reporte-flash__` de forma nativa.

**Decisión de diseño**: usar `/domingo` como plantilla. Los 3 datos reales que los comandos necesitan son:

| Necesidad | Tool actual | Tool nuevo |
|-----------|-------------|------------|
| Precio actual + niveles técnicos + RSI/ATR | `mt5_integration.py analisis_completo_activo()` | `mcp__reporte-flash__analyze_ticker` |
| Calendario económico | Firecrawl → Investing.com | `mcp__reporte-flash__get_economic_calendar` |
| Noticias / breaking news | TrendRadar | `mcp__reporte-flash__get_market_news` |

**Comandos a actualizar** (orden por impacto):

#### Grupo 1 — Comandos de día (L-V): 6 archivos
Todos tienen Pieza "Apertura de mercado" que llama a MT5 y una sección de calendario.

| Archivo | Qué cambiar |
|---------|-------------|
| `.claude/commands/lunes.md` | SETUP: quitar `python scripts/orquestador.py`. PIEZA 1: reemplazar Firecrawl por `get_economic_calendar`. PIEZA 4: reemplazar `analisis_completo_activo()` por `analyze_ticker`. |
| `.claude/commands/martes.md` | Igual estructura que lunes |
| `.claude/commands/miercoles.md` | Igual + referencia específica a datos EIA petróleo |
| `.claude/commands/jueves.md` | Igual + referencia a Jobless Claims |
| `.claude/commands/viernes_am.md` | Igual + NFP si aplica |
| `.claude/commands/viernes_pm.md` | Sección de cierre: reemplazar MT5 por `analyze_ticker` para precios de cierre |

**Patrón de reemplazo para Pieza apertura** (aplicar en todos):
```
ANTES:
- Conéctate a MT5 con `scripts/mt5_integration.py`
- Ejecuta `analisis_completo_activo(ticker, "4H")` por cada activo

DESPUÉS:
- Llama `mcp__reporte-flash__analyze_ticker` con `{"ticker": "[TICKER_MT5]", "timeframe": "H4"}`
- Extrae: precio actual, soportes, resistencias, sesgo, RSI, ATR del resultado
- Si el MCP no responde: usar web search para precio actual + análisis manual con drivers de config/drivers.json
```

**Patrón de reemplazo para sección calendario** (aplicar en todos):
```
ANTES:
- Usa Firecrawl para extraer el calendario completo de Investing.com
- Fallback: web search "investing.com calendario..."

DESPUÉS:
- Llama `mcp__reporte-flash__get_economic_calendar` con `{"days_ahead": 1, "min_impact": "medium"}`
- Fallback: web search con los términos de siempre
```

#### Grupo 2 — Comandos ad hoc: 3 archivos

| Archivo | Qué cambiar |
|---------|-------------|
| `.claude/commands/alerta.md` | PASO 1: reemplazar TrendRadar por `mcp__reporte-flash__get_market_news` con `{"category": "general", "min_hours_old": 2}` |
| `.claude/commands/noticia.md` | Misma lógica que alerta |
| `.claude/commands/estado.md` | SECCIÓN 1: quitar `python scripts/orquestador.py`; construir el plan del día leyendo directamente `config/agenda_semanal.json` y `data/historial_señales.json`. SECCIÓN 6: actualizar lista MCPs (marcar WhatsApp/TrendRadar/Firecrawl como "no activo"). |

#### Grupo 3 — Comandos ya correctos: sin cambios
- `.claude/commands/domingo.md` ✅
- `.claude/commands/señal.md` ✅ (no llama MCPs externos, lógica propia)
- `.claude/commands/encuesta.md` ✅ (sin dependencias externas)
- `.claude/commands/concepto.md` — revisar si usa TrendRadar
- `.claude/commands/pregunta.md` — sin dependencias
- `.claude/commands/chart.md` — depende de MT5 EA; lógica propia
- `.claude/commands/dato_macro.md` — usa Firecrawl → migrar a `get_economic_calendar`
- `.claude/commands/earnings.md` — usa Firecrawl → migrar a `get_economic_calendar`
- `.claude/commands/accion.md` — usa MT5 → migrar a `analyze_ticker`

---

### ÁREA B — Limpiar archivos huérfanos

**Archivos a eliminar**:

```
ampliacion-mercado/                   ← carpeta completa (ya absorbida en raíz)
MASTER_SPEC_FINAL.md                  ← supersedido por CLAUDE.md
SPECS_17_COMANDOS.md                  ← supersedido por CLAUDE.md
docs/spec-refactorizacion.md          ← absorbido en docs/ideas/ y docs/design/
```

**Archivos a conservar (no tocar)**:
- `scripts/mt5_integration.py` — útil como fallback manual, pero no llamado desde comandos
- `scripts/orquestador.py` — útil como referencia, pero no llamado desde comandos
- `mcp/mcp_config.json` — conservar con comentario indicando estado de cada MCP

---

### ÁREA C — Actualizar CLAUDE.md

**Cambio 1**: Agregar `/domingo` a la tabla de comandos y a "Slash Commands disponibles":

```markdown
| `/domingo` | Paquete dominical: noticias fin de semana + preview semana + sesgo lunes + encuesta |
```

**Cambio 2**: Actualizar descripción de MCPs integrados — reemplazar "TrendRadar", "Firecrawl" y "WhatsApp" como MCPs activos, agregar `reporte-flash` como el MCP principal de datos:

```markdown
| **reporte-flash** | Análisis técnico MT5 + calendario macro + noticias | TODOS los comandos |
| **WhatsApp (Evolution API)** | Envío directo al grupo (pendiente conexión Docker) | Flujo manual por ahora |
```

**Cambio 3**: Corregir tabla de Agenda semanal — agregar fila Domingo:

```markdown
| Domingo | Noticias fin de semana + preview semana + sesgo lunes | Encuesta semana | No aplica |
```

---

### ÁREA D — Actualizar `mcp/mcp_config.json`

Agregar campo `"estado"` a cada MCP para documentar cuál está activo:

```json
{
  "mcpServers": {
    "whatsapp": {
      "estado": "PENDIENTE — requiere Evolution API en Docker conectado a WhatsApp/Baileys",
      ...
    },
    "trendradar": {
      "estado": "NO ACTIVO — reemplazado por mcp__reporte-flash__get_market_news",
      ...
    },
    "firecrawl": {
      "estado": "NO ACTIVO — reemplazado por mcp__reporte-flash__get_economic_calendar",
      ...
    }
  }
}
```

---

## Orden de ejecución

1. **Área B primero** (limpieza) — sin riesgo, no rompe nada
2. **Área C** (CLAUDE.md) — documentación, sin riesgo
3. **Área D** (mcp_config.json) — solo adds comentarios
4. **Área A - Grupo 2** (`alerta`, `noticia`, `estado`) — comandos simples, fácil de verificar
5. **Área A - Grupo 1** (`lunes`–`viernes_pm`) — comandos de día, cambio masivo pero patrón repetitivo
6. **Área A - Grupo 3 pendientes** (`dato_macro`, `earnings`, `accion`, `concepto`)

---

## Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| `mcp__reporte-flash__analyze_ticker` no disponible durante el día | Mantener fallback a web search en cada comando |
| Formato de respuesta de `analyze_ticker` diferente a lo que los comandos esperan | Testar con `/estado` antes del día operativo |
| Eliminar `MASTER_SPEC_FINAL.md` y perder context histórico | Conservar en `docs/archive/` si el director lo prefiere |

---

## Qué NO cambia

- Contenido y formato de los mensajes WhatsApp
- Estructura de `data/historial_señales.json`
- Lógica de `/señal` (funciona sin dependencias externas)
- Scripts Python en `scripts/` (quedan como utilidades manuales)
- Agenda semanal y rotación de activos
