# Grupo de Análisis de Mercado — Sistema Automatizado

Sistema que automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El director de trading invoca comandos en Claude Code y el sistema genera contenido listo para pegar en el grupo.

## Cómo funciona

```
Director (Claude Code) → genera contenido → aprueba → guarda en data/mensajes/ → copia al grupo WhatsApp
                                                ↓
                              (futuro: Evolution API lo envía directo)
```

Todo el contenido pasa por aprobación explícita del director antes de enviarse. Nunca se envía nada automáticamente sin confirmación. Al aprobar, cada mensaje se guarda en `data/mensajes/` con estructura **día → activo → tipo**.

> **Modo ejecutivo**: los comandos que producen un mensaje de cliente aceptan el flag `ejecutivo` (ej. `/noticia ejecutivo`). Además del mensaje de cliente generan un **guion de venta privado** para el grupo interno de ejecutivos, marcado `🔒 INTERNO · NO ENVIAR AL CLIENTE`.

## Requisitos

- **Claude Code** (CLI o Desktop) con suscripción activa
- **MCP market-data** instalado y configurado — capa de datos técnicos MT5 + calendario económico
- **Python 3.11+** para el MCP `market-data` (`src/market_data_mcp/`) y `scripts/story_render.py`
- **MetaTrader 5** abierto en la máquina del director (el MCP lee de MT5 en vivo)
- **uv** para la toolchain de desarrollo y el gate de calidad (opcional)
- **Playwright** para renderizar Stories GI (opcional, extra `stories`)
- **Evolution API en Docker** para envío directo WhatsApp (instalada y lista; conexión pendiente)
- **gh CLI** para gestión de issues/PRs (opcional)

## Instalación rápida

```bash
git clone https://github.com/bbenja11/grupo-analisis-mercado
cd grupo-analisis-mercado

# Copiar config de MCPs y completar con tus credenciales
cp mcp/mcp_config.example.json mcp/mcp_config.json
# Editar mcp_config.json con tus API keys

# Dependencias del MCP market-data (máquina del director, con MT5 abierto)
uv sync                    # fastmcp · pandas (core) + ruff · ty · pytest (dev)
# MetaTrader5 se importa de forma perezosa: solo en la máquina del director

# (Opcional) Stories GI: render de imágenes de marca con Playwright headless
uv sync --extra stories && python -m playwright install chromium
```

Ver [docs/setup-guide.md](docs/setup-guide.md) para instrucciones detalladas.

## 25 Slash Commands

Invocar desde Claude Code con `/nombre`. Organizados en 3 capas:

### Capa 1 — Comandos de día (paquete completo, lunes a domingo)

| Comando | Propósito |
|---------|-----------|
| `/domingo` | Paquete dominical: noticias fin de semana + preview + sesgo lunes + encuesta semana |
| `/lunes` | Paquete del lunes: resumen semanal + earnings + concepto + apertura + encuesta |
| `/martes` | Operativa martes: apertura + dato macro + encuesta precio |
| `/miercoles` | Operativa miércoles + prioridad EIA de petróleo |
| `/jueves` | Operativa jueves + alerta Jobless Claims |
| `/viernes_am` | AM viernes: 3 activos + NFP si aplica + encuesta precio del lunes |
| `/viernes_pm` | Cierre semanal por la tarde |

### Capa 2 — Comandos de tarea (ad hoc)

| Comando | Propósito |
|---------|-----------|
| `/apertura` | Niveles técnicos interactivos (activo + temporalidad + indicador por activo) |
| `/actualizacion` | Evolución del precio y reacción frente a los niveles de la apertura |
| `/dato_macro` | Calendario del día → director elige dato a desarrollar (modo anticipación / resultado) |
| `/noticia` | 3-5 noticias relevantes → director elige |
| `/alerta` | Detecta qué mueve el mercado ahora y genera alerta urgente |
| `/señal` | Señal operativa (verifica límite 3/semana) |
| `/encuesta [tipo] [activo]` | Encuesta de sentimiento puro (3 tipos: posicion, tendencia, movimiento) |
| `/rencuesta` | Desarrolla el tema de una encuesta y construye la malla de conceptos |
| `/curriculo` | Planifica el currículo educativo y despacha conceptos en orden |
| `/concepto` | Concepto educativo conectado a lo que pasó esta semana |
| `/pregunta` | Pregunta abierta para fomentar el razonamiento del grupo |
| `/respuesta` | Responde una pregunta/comentario de cliente de forma didáctica |
| `/chart` | Screenshot MT5 con indicador y temporalidad a elección |
| `/story [tipo]` | Story de marca GI (imagen 1920×1080). Tipos: alerta, quote, breaking, encuesta, edu |
| `/ventas` | Oportunidad del Día para el equipo de ventas interno (email + WhatsApp) |
| `/estado` | Dashboard del sistema (señales, charts, plan del día, MCPs) — no envía nada |

### Capa 3 — Acciones individuales

| Comando | Propósito |
|---------|-----------|
| `/accion [TICKER]` | Análisis completo de una de las 13 acciones del catálogo |
| `/earnings` | Calendario de earnings de las 13 acciones para la semana |

## Activos cubiertos

**Forex / Commodities**: USD/CLP · XAU/USD (Oro) · WTI (Petróleo)

**Índices**: US100 (Nasdaq 100) · US500 (S&P 500) · US30 (Dow Jones)

**Acciones (13)**:
- _Tecnológico_: #AAPL · #MSFT · #NVDA · #AMZN · #AMD
- _Bancario_: #JPM · #BAC · #GS · #MS
- _Industrial_: #BA · #CAT · #GE · #DE

**Complementarios** (drivers, no se operan): cobre (COPPER) · Dollar Index (USDIDX) · DAX 40 (GER40)

La rotación diaria cubre 2-3 activos: los 4 base (USD/CLP, Oro, WTI, US100) más 1-2 acciones del catálogo elegidas por análisis previo.

## MCP integrado: market-data

El MCP `market-data` (`src/market_data_mcp/`) es la capa de datos confiable del sistema. Expone **cuatro** tools:

| Tool | Qué entrega |
|------|-------------|
| `get_asset_levels` | Análisis técnico automático MT5: precio, soportes/resistencias (S1/S2/R1/R2), RSI14, ATR14 y sesgo |
| `get_chart_objects` | Niveles dibujados a mano por el director en MT5 (soportes/resistencias, trendlines, canales, rectángulos) + screenshot, vía el Service MQL5 `ChartObjectsExporter` |
| `obtener_calendario_macro` | Calendario económico Investing.com (Chile + EE.UU. + China + Zona Euro) con resultado real `actual` y clasificación mejor/peor/en_línea vs consenso |
| `get_symbol_spec` | Especificaciones de contrato (trade_mode, digits, volumen mínimo/paso, tamaño de contrato) y sesiones de trading en hora Chile; con `fecha` responde si el activo opera ese día |

Las **noticias** se obtienen vía WebSearch (investing.com + fuentes oficiales: Fed, BCCh, OPEP+, EIA, BLS), que también es el fallback del calendario si la fuente falla. Contrato de error: si un dato no está disponible, la tool retorna `{"error": "CÓDIGO", "message": "..."}` — nunca array vacío ni `None` silencioso.

## Stories GI

Comando `/story [tipo]` (piloto, issue #109): genera **Stories de marca** en formato imagen 16:9 (1920×1080) para los ejecutivos. Tipos soportados hoy (Fase B completa, v0.6.0):

- **alerta** — niveles reales del motor (`get_asset_levels`) + narrativa de alerta de mercado
- **quote** — cita / visión de marca (100% editorial)
- **breaking** — noticia urgente: kicker + titular + cifra clave + contexto + reacción
- **encuesta** — sentimiento binario "A vs B"
- **edu** — concepto educativo (definición + ejemplo + bullets de aplicación)

Renderer único: `scripts/story_render.py` (payload JSON → HTML → PNG con Playwright headless). Los snapshots de marca viven en `templates/stories/`. El proyecto Claude Design compartido con GI es **solo lectura** — este repo nunca sube datos ni lógica propia hacia allá.

## Estructura del proyecto

```
grupo-analisis-mercado/
├── README.md
├── CLAUDE.md                    ← instrucciones para Claude Code
├── pyproject.toml               ← toolchain uv (ruff · ty · pytest) del gate de calidad
├── .claude/
│   ├── commands/                ← 25 slash commands (.md)
│   └── shared/modo_ejecutivo.md ← contrato del flag `ejecutivo`
├── src/
│   └── market_data_mcp/         ← MCP market-data (4 tools: get_asset_levels, get_chart_objects, obtener_calendario_macro, get_symbol_spec)
├── tests/                       ← tests del MCP (pytest)
├── agents/                      ← prompts de sub-agents (recolector · analista · redactor)
├── config/
│   ├── activos.json             ← forex + commodities + índices + 13 acciones + complementarios
│   ├── agenda_semanal.json      ← estructura L-V: contenido, encuesta, horarios
│   ├── drivers.json · drivers_indices_sectores.json
│   ├── glosario_siglas.json     ← SIGLA → {nombre_es, explicacion} (diccionario rápido)
│   └── feriados_bolsa.json      ← calendario de feriados NYSE (usado por get_symbol_spec)
├── scripts/
│   ├── story_render.py          ← renderer de Stories GI (payload JSON → HTML → PNG)
│   └── hora_chile.ps1 · ruta_mensaje.ps1 · ruta_story.ps1  ← helpers deterministas (hora, ruta de guardado)
├── templates/                   ← plantillas de mensajes WhatsApp + stories/ (snapshot de marca GI)
├── conceptos/                   ← notas canónicas de conceptos educativos (malla /rencuesta)
├── data/
│   ├── historial_senales.json · historial_encuestas.json · historial_ventas.json
│   ├── curriculo.json · mapa_conceptos.json · entregas_educativas.json · metricas_educativas.json
│   └── charts/ · mensajes/ · stories/   ← generados (gitignored)
├── mql5/                        ← Service MQL5 (ChartObjectsExporter) + archive/
├── docs/                        ← documentación del sistema
│   ├── architecture.md · commands-reference.md
│   ├── setup-guide.md · activos-y-drivers.md
│   ├── design/                  ← diseños vigentes (ciclo Pulse), incluye stories-gi/
│   └── archive/                 ← docs históricos de features ya implementadas
└── mcp/
    ├── mcp_config.example.json  ← template sin credenciales (en git)
    └── mcp_config.json          ← config real con API keys (gitignored)
```

## Documentación

- [Arquitectura del sistema](docs/architecture.md)
- [Referencia de comandos](docs/commands-reference.md)
- [Guía de instalación](docs/setup-guide.md)
- [Activos y drivers](docs/activos-y-drivers.md)

## Principio fundamental

> **Regla de oro**: el cliente debe entender siempre hacia dónde se dirige el activo (alcista / bajista / lateral), para saber qué operar. Un análisis que no deja clara la dirección está incompleto.
>
> **Criterio de claridad** (subordinado a la regla de oro): si un cliente nuevo sin experiencia no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple — pero "más simple" nunca significa "sin dirección".

Análisis técnico simple y directo, con tono profesional y gancho operativo: énfasis direccional sí, dramatización no. El contenido se redacta para clientes que están aprendiendo, no para traders profesionales — y a la vez debe ser accionable para quien ya opera.
