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
- **MCP reporte-flash** instalado y configurado (análisis técnico MT5 + calendario macro)
- **Python 3.10+** para scripts auxiliares (senal_manager, formatter)
- **Evolution API en Docker** para envío directo WhatsApp (opcional, pendiente)
- **gh CLI** para gestión de issues/PRs (opcional)

## Instalación rápida

```bash
git clone https://github.com/bbenja11/grupo-analisis-mercado
cd grupo-analisis-mercado

# Copiar config de MCPs y completar con tus credenciales
cp mcp/mcp_config.example.json mcp/mcp_config.json
# Editar mcp_config.json con tus API keys

# Instalar dependencias Python
pip install MetaTrader5 pandas requests
```

Ver [docs/setup-guide.md](docs/setup-guide.md) para instrucciones detalladas.

## 18 Slash Commands

Invocar desde Claude Code con `/nombre`:

| Comando | Propósito |
|---------|-----------|
| `/domingo` | Noticias fin de semana + preview semana + sesgo lunes |
| `/lunes` | Resumen semanal + earnings + concepto + apertura + encuesta |
| `/martes` | Apertura + dato macro + encuesta precio |
| `/miercoles` | Apertura + dato macro + encuesta tendencia (prioridad EIA) |
| `/jueves` | Apertura + dato macro + alerta Jobless Claims |
| `/viernes_am` | 3 activos + NFP si aplica + encuesta precio del lunes |
| `/viernes_pm` | Cierre semanal |
| `/encuesta` | Encuesta de tendencia o precio para cualquier activo |
| `/dato_macro` | Calendario del día → director elige dato a desarrollar |
| `/noticia` | 3-5 noticias relevantes → director elige |
| `/chart` | Screenshot MT5 con indicador y temporalidad a elección |
| `/señal` | Señal operativa (verifica límite 3/semana) |
| `/alerta` | Detecta qué mueve el mercado y genera alerta urgente |
| `/concepto` | Concepto educativo conectado a lo que pasó esta semana |
| `/pregunta` | Pregunta abierta para fomentar razonamiento del grupo |
| `/estado` | Dashboard del sistema (señales, plan del día, MCPs) |
| `/accion [TICKER]` | Análisis completo de una de las 12 acciones |
| `/earnings` | Calendario de earnings de las 12 acciones para la semana |

## Activos cubiertos

**Forex / Commodities**: USD/CLP · XAU/USD (Oro) · WTI (Petróleo)

**Índices**: US100 (Nasdaq) · US500 (S&P 500) · US30 (Dow Jones)

**Acciones** (12): #AAPL · #MSFT · #NVDA · #AMZN · #JPM · #BAC · #GS · #MS · #BA · #CAT · #GE · #DE

## Estructura del proyecto

```
grupo-analisis-mercado/
├── README.md
├── CLAUDE.md                    ← instrucciones para Claude Code
├── .claude/commands/            ← 18 slash commands (.md)
├── config/
│   ├── activos.json             ← 20 activos con tickers MT5 y drivers
│   ├── agenda_semanal.json      ← estructura L-V: contenido, encuesta, horarios
│   ├── drivers.json             ← drivers fundamentales por activo
│   ├── drivers_indices_sectores.json
│   └── plantilla_señal.json     ← campos obligatorios de una señal
├── scripts/
│   ├── senal_manager.py         ← gestión historial señales (límite 3/semana)
│   ├── formatter_whatsapp.py    ← formato texto → WhatsApp
│   └── mt5_integration.py       ← integración MetaTrader5 (legacy)
├── templates/                   ← plantillas de mensajes WhatsApp
├── data/
│   └── historial_senales.json   ← registro de señales enviadas
├── docs/                        ← documentación del sistema
│   ├── architecture.md
│   ├── commands-reference.md
│   ├── setup-guide.md
│   └── activos-y-drivers.md
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
