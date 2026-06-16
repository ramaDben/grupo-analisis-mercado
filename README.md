# Grupo de Análisis de Mercado — Sistema Automatizado

Sistema que automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El director de trading invoca comandos en Claude Code y el sistema genera contenido listo para pegar en el grupo.

## Cómo funciona

```
Director (Claude Code) → genera contenido → aprueba → copia al grupo WhatsApp
                                                ↓
                              (futuro: Evolution API lo envía directo)
```

Todo el contenido pasa por aprobación explícita del director antes de enviarse. Nunca se envía nada automáticamente sin confirmación.

## Requisitos

- **Claude Code** (CLI o Desktop) con suscripción activa
- **MCP market-data** instalado y configurado (análisis técnico MT5: `get_asset_levels`)
- **Python 3.10+** para el script auxiliar `senal_manager` (límite de señales)
- **Evolution API en Docker** para envío directo WhatsApp (opcional, pendiente)
- **gh CLI** para gestión de issues/PRs (opcional)

## Instalación rápida

```bash
git clone https://github.com/bbenja11/grupo-analisis-mercado
cd grupo-analisis-mercado

# Copiar config de MCPs y completar con tus credenciales
cp mcp/mcp_config.example.json mcp/mcp_config.json
# Editar mcp_config.json con tus API keys

# Dependencias del MCP market-data (máquina del director, con MT5 abierto)
pip install fastmcp pandas MetaTrader5

# (Opcional) Toolchain de desarrollo y gate de calidad
uv sync   # ruff · ty · pytest, definidos en pyproject.toml
```

Ver [docs/setup-guide.md](docs/setup-guide.md) para instrucciones detalladas.

## 21 Slash Commands

Invocar desde Claude Code con `/nombre`:

| Comando | Propósito |
|---------|-----------|
| `/domingo` | Paquete dominical: noticias fin de semana + preview + sesgo lunes + encuesta semana |
| `/lunes` | Paquete del lunes: resumen semanal + earnings + concepto + apertura + encuesta |
| `/martes` | Operativa martes: apertura + dato macro + encuesta precio |
| `/miercoles` | Operativa miércoles + prioridad EIA de petróleo |
| `/jueves` | Operativa jueves + alerta Jobless Claims |
| `/viernes_am` | AM viernes: 3 activos + NFP si aplica + encuesta precio del lunes |
| `/viernes_pm` | Cierre semanal por la tarde |
| `/apertura` | Niveles técnicos interactivos (activo + temporalidad + indicador por activo) |
| `/encuesta [tipo] [activo]` | Encuesta de sentimiento puro (3 tipos: posicion, tendencia, movimiento) |
| `/rencuesta` | Desarrolla el tema de una encuesta y construye la malla de conceptos |
| `/curriculo` | Planifica el currículo educativo y despacha conceptos en orden |
| `/dato_macro` | Calendario del día → director elige dato a desarrollar |
| `/noticia` | 3-5 noticias relevantes → director elige |
| `/chart` | Screenshot MT5 con indicador y temporalidad a elección |
| `/señal` | Señal operativa (verifica límite 3/semana) |
| `/alerta` | Detecta qué mueve el mercado y genera alerta urgente |
| `/concepto` | Concepto educativo conectado a lo que pasó esta semana |
| `/pregunta` | Pregunta abierta para fomentar razonamiento del grupo |
| `/estado` | Dashboard del sistema (señales, charts, plan del día, MCPs) |
| `/accion [TICKER]` | Análisis completo de una de las 13 acciones |
| `/earnings` | Calendario de earnings de las 13 acciones para la semana |

## Activos cubiertos

**Forex / Commodities**: USD/CLP · XAU/USD (Oro) · WTI (Petróleo)

**Índices**: US100 (Nasdaq) · US500 (S&P 500) · US30 (Dow Jones)

**Acciones** (12): #AAPL · #MSFT · #NVDA · #AMZN · #JPM · #BAC · #GS · #MS · #BA · #CAT · #GE · #DE

## MCP integrado: market-data

El MCP `market-data` (`src/market_data_mcp/`) es la capa de datos técnicos: expone **una** tool, `get_asset_levels` (precio, soportes/resistencias S1/S2/R1/R2, RSI14, ATR14 y sesgo desde MT5). El calendario económico y las noticias **no** vienen del MCP — se obtienen vía WebSearch (investing.com + fuentes oficiales) directamente en los comandos.

## Estructura del proyecto

```
grupo-analisis-mercado/
├── README.md
├── CLAUDE.md                    ← instrucciones para Claude Code
├── pyproject.toml               ← toolchain uv (ruff · ty · pytest) del gate de calidad
├── .claude/commands/            ← 21 slash commands (.md)
├── src/
│   └── market_data_mcp/         ← MCP market-data (get_asset_levels: análisis técnico MT5)
├── tests/                       ← tests del MCP (pytest)
├── agents/                      ← prompts de sub-agents (recolector · analista · redactor)
├── config/
│   ├── activos.json             ← 20 activos con tickers MT5 y drivers
│   ├── agenda_semanal.json      ← estructura L-V: contenido, encuesta, horarios
│   ├── drivers.json · drivers_indices_sectores.json
│   └── plantilla_señal.json     ← campos obligatorios de una señal
├── scripts/
│   ├── senal_manager.py         ← gestión historial señales (límite 3/semana)
│   └── hora_chile.ps1 · ruta_mensaje.ps1  ← helpers deterministas (hora, ruta de guardado)
├── templates/                   ← plantillas de mensajes WhatsApp
├── conceptos/                   ← notas canónicas de conceptos educativos (malla /rencuesta)
├── data/
│   ├── historial_senales.json   ← registro de señales enviadas
│   ├── curriculo.json · mapa_conceptos.json · entregas_educativas.json · metricas_educativas.json
│   └── charts/                  ← PNGs generados (gitignored)
├── docs/                        ← documentación del sistema
│   ├── architecture.md · commands-reference.md
│   ├── setup-guide.md · activos-y-drivers.md
│   └── ideas/ · design/         ← specs y diseños (ciclo Pulse)
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

> Si un cliente nuevo (sin experiencia) no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple.

El contenido nunca se redacta para traders profesionales — se redacta para clientes que están aprendiendo.
