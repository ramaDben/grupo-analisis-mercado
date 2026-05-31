# Grupo de Análisis de Mercado — Sistema Automatizado

## Contexto
Este proyecto automatiza la operativa semanal del Grupo de Análisis de Mercado para envío vía WhatsApp. El usuario es el director de trading. Los sub-agents actúan como analistas de mercado y recolectores de información.

## Principio fundamental
100% orientado al CLIENTE FINAL. Si un cliente nuevo sin experiencia no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple. El contenido nunca se redacta para traders profesionales — se redacta para clientes que están aprendiendo.

Regla de oro: si un cliente nuevo (sin experiencia) no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple.

## Activos cubiertos (rotación diaria, 2-3 por día)
- **USD/CLP**: drivers → cobre, Dollar Index, tasas BCCh vs Fed, flujos
- **Oro (XAU/USD)**: drivers → Dollar Index, tasas reales, decisiones Fed, coberturas bancos centrales, geopolítica
- **WTI (Petróleo)**: drivers → inventarios EIA, decisiones OPEP+, demanda China, geopolítica
- **US100 (Nasdaq 100)**: drivers → tasas Fed, earnings tech, rendimientos Treasury

## Estructura diaria obligatoria (lunes a viernes)

### 1. Niveles técnicos del día
- Enviar niveles en temporalidades 4H, 1H o 15M
- Cubrir 2 o 3 activos por día (rotar entre USD/CLP, Oro, WTI, US100)
- Indicar: soportes, resistencias, zona de interés y posible sesgo

### 2. Noticia relevante del calendario económico
- 1 noticia o dato del día que impacte directamente a alguno de los activos
- Explicar simple: qué es, a qué hora sale, qué se espera y cómo podría reaccionar el activo
- Fuente oficial: calendario de Investing.com
- Hora siempre en hora Chile (CLT/CLST)

### 3. Drivers del activo
- Explicación corta de los drivers que están moviendo al activo
- Si hay información relevante durante el día (declaraciones, datos sorpresivos, eventos geopolíticos), informar de inmediato

## Reglas de temporalidad
Cada análisis indica explícitamente su temporalidad y tipo de operativa:
- **15M** → scalper / muy rápida — operaciones cortas dentro del día, alta rotación
- **1H** → intradía corto — movimientos del día, confirmar entradas finas
- **4H** → intradía / swing corto — tendencia del día y operativas de varias horas
- **1D** → intraday / swing — lectura general del activo y operaciones de días

Ejemplo obligatorio: "Niveles en 15M — operativa scalper, movimientos rápidos dentro del día"

## Agenda semanal

| Día | Contenido principal | Encuesta | Señales |
|-----|---------------------|----------|---------|
| Domingo | Noticias fin de semana + preview semana + sesgo lunes | Encuesta semana | No aplica |
| Lunes | Resumen calendario semanal + concepto de la semana | Tendencia AM | Según oportunidad |
| Martes | Niveles + noticia + drivers | Precio apertura | Según oportunidad |
| Miércoles | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Jueves | Niveles + noticia + drivers | Tendencia AM | Según oportunidad |
| Viernes | Niveles + noticia + drivers + cierre semanal | Precio apertura lunes | Según oportunidad |

## Señales operativas
- **Máximo 3 por semana** (hard limit, verificar en data/historial_señales.json)
- Tipo: swing (varios días) o scalper (intradía cortas)
- Campos obligatorios: ticker, nombre activo, BUY/SELL, entrada, volumen, acciones, TP, SL
- **TP y SL traducidos a pesos chilenos (CLP)** — el cliente debe ver cuánto gana y cuánto pierde sin calcular nada
- Máximo 3 bullets de análisis (técnico + fundamental)
- Siempre usar plantilla oficial
- Las señales son complementarias, NO el foco principal del grupo

## Encuestas diarias (lunes a viernes)
- **3 días (L, X, J)** → Encuesta de tendencia AM: "¿Cuál creen que será la tendencia hoy del [activo]?" → Alcista / Bajista / Lateral
- **2 días (M, V)** → Encuesta de precio de apertura: "¿A qué precio creen que abrirá el [activo] mañana / el lunes?"
- **IMPORTANTE**: siempre enviar previamente una noticia, evento o análisis para que el cliente vote con base en información, no en intuición

## Indicadores técnicos
Un aviso = un indicador. NUNCA mezclar múltiples señales técnicas al mismo tiempo:
- **ATR** → recalcar su uso en USD/CLP como indicador de volatilidad
- **RSI** → avisar cuando esté sobrecomprado o sobrevendido
- **MACD** → avisar cruces relevantes
- **Medias móviles** → avisar cruces de medias (ej: cruce de la 50 con la 200)

## Formato de mensajes WhatsApp
- Emojis con moderación: 📊 📈 📉 🔴 🟢 ⚠️ 🕐 🎯 📚 📅
- Formato WhatsApp: *negrita*, _cursiva_
- Bullets: •
- Separadores: ━━━━━━━━━━━━━━━━━━━
- Horas siempre en hora Chile (CLT/CLST)
- Estructura formal, consistente y repetible cada día

## Eventos de alto impacto (decisiones de tasas)
Cuando hay decisión de tasas (Fed, BCCh, BCE):
1. Anticipar la reunión con varios días de antelación
2. Conectar datos previos (IPC, PCE, PMI, empleo) con el escenario de tasas
3. Explicar probabilidades de recorte/alza según el mercado
4. Día de la decisión: análisis previo + monitoreo en vivo + explicación posterior

Objetivo: que el cliente entienda que los datos económicos son piezas que van armando el camino hacia la decisión de tasas.

## Contenido educativo
- **Concepto de la semana** (lunes): un concepto que se refuerza durante la semana
- **Pregunta del día** (1x semana): pregunta abierta tipo "¿Por qué creen que el oro subió tras el dato de inflación?"
- **Glosario fijado**: mensaje fijo en el grupo con conceptos clave (IPC, PMI, PCE, NFP, Dollar Index, ATR, RSI, etc.)
- Temas: tendencias, canales, rangos, indicadores (uno a la vez)

## Rol paralelo del grupo
Aunque el grupo es para clientes, sirve como espacio de alineación interna:
- **Ejecutivos**: se mantienen al tanto del mercado, refuerzan conceptos, replican el lenguaje simple con sus carteras
- **Analistas**: observan cómo se comunica al cliente, aseguran consistencia y aportan profundidad

## Misión
Mejorar indicadores de satisfacción del cliente, retención, NPS y reducir churn. Pasar de un modelo de señales a un modelo de análisis + educación donde el cliente aprende a leer el mercado.

## MCP Servers integrados

| MCP | Estado | Propósito | Usado en |
|-----|--------|-----------|----------|
| **reporte-flash** | ✅ Activo | Análisis técnico MT5 + calendario macro + noticias | TODOS los comandos de datos |
| **WhatsApp (Evolution API)** | ⏳ Pendiente conexión Docker | Envío directo al grupo | Flujo manual por ahora |
| **TrendRadar** | ❌ Reemplazado por reporte-flash | — | — |
| **Firecrawl** | ❌ Reemplazado por reporte-flash | — | — |

**Flujo actual**: los comandos generan contenido → muestran para copiar → guardan en `data/mensajes/`. Cuando Evolution API esté conectada a WhatsApp/Baileys, el envío pasará a ser automático.

**Setup WhatsApp**: requiere Evolution API en Docker (`docker run -d --name evolution-api -p 8080:8080 atendai/evolution-api`). Ver instrucciones en `mcp/mcp_config.json`.

## Flujo de aprobación → WhatsApp (modo semi-automático activo)

Todo contenido pasa por este flujo antes de enviarse:
1. El comando genera el contenido.
2. Lo muestra al director para aprobación.
3. Pregunta: "¿Adjuntar chart de MT5?"
4. El director aprueba o pide ajustes.
5. **Al aprobar**: guardar automáticamente en `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt` y mostrar el texto listo para copiar.
6. El director copia y pega el texto en el grupo de WhatsApp.

**Regla de guardado**: después de cada aprobación, SIEMPRE guardar el mensaje final en `data/mensajes/` con el formato de nombre `YYYY-MM-DD_HH-MM_[tipo].txt` (ej: `2026-05-31_14-30_alerta.txt`). Usar la herramienta Write para crearlo directamente.

**Tipos de archivo**: alerta, apertura, concepto, encuesta, señal, noticia, dato_macro, cierre, pregunta, niveles.

**Nunca se envía nada al grupo sin aprobación explícita del director.**

**Nota**: Evolution API (Docker) está instalada y lista en `mcp/docker-compose.yml`. Cuando se resuelva la conexión WhatsApp/Baileys, el envío pasará a ser automático sin cambios adicionales.

## Slash Commands disponibles (18)

Invocar con `/nombre` desde Claude Code:

### Capa 1 — Comandos de día
| Comando | Cuándo usarlo |
|---------|---------------|
| `/domingo` | Paquete dominical: noticias fin de semana + preview semana + sesgo lunes + encuesta semana |
| `/lunes` | Paquete completo del lunes (resumen semanal + earnings + concepto + apertura + encuesta) |
| `/martes` | Operativa estándar martes (apertura + dato macro + encuesta precio) |
| `/miercoles` | Operativa miércoles + prioridad EIA de petróleo |
| `/jueves` | Operativa jueves + alerta Jobless Claims |
| `/viernes_am` | AM del viernes: 3 activos + NFP si aplica + encuesta precio del lunes |
| `/viernes_pm` | Cierre semanal por la tarde |

### Capa 2 — Comandos de tarea (ad hoc)
| Comando | Cuándo usarlo |
|---------|---------------|
| `/encuesta [tipo] [activo]` | Encuesta de tendencia o precio para cualquier activo |
| `/dato_macro` | Calendario del día → director elige dato a desarrollar |
| `/noticia` | Busca 3-5 noticias relevantes → director elige |
| `/chart` | Genera screenshot de MT5 con indicador y temporalidad a elección |
| `/señal` | Señal operativa (verifica límite 3/semana automáticamente) |
| `/alerta` | Detecta qué mueve el mercado ahora y genera alerta urgente |
| `/concepto` | Concepto educativo conectado a lo que pasó esta semana |
| `/pregunta` | Pregunta abierta para fomentar razonamiento del grupo |
| `/estado` | Dashboard del sistema (señales, charts, plan del día, MCPs) |

### Capa 3 — Acciones individuales
| Comando | Cuándo usarlo |
|---------|---------------|
| `/accion [TICKER]` | Análisis completo de una de las 12 acciones del catálogo |
| `/earnings` | Calendario de earnings de las 12 acciones para la semana |

## Estructura del proyecto
```
grupo-analisis-mercado/
├── CLAUDE.md              ← este archivo
├── COMANDOS.md            ← referencia histórica de comandos manuales
├── docs/
│   ├── ideas/             ← specs de features (ciclo Pulse)
│   └── design/            ← diseños técnicos (ciclo Pulse)
├── .claude/
│   └── commands/          ← 18 slash commands (invocar con /nombre)
│       ├── domingo.md
│       ├── lunes.md · martes.md · miercoles.md · jueves.md
│       ├── viernes_am.md · viernes_pm.md
│       ├── encuesta.md · dato_macro.md · noticia.md · chart.md
│       ├── señal.md · alerta.md · concepto.md · pregunta.md · estado.md
│       ├── accion.md · earnings.md
├── agents/                ← prompts de sub-agents
│   ├── recolector.md · analista.md · redactor.md
├── config/                ← configuración del sistema
│   ├── activos.json       ← 20 activos: forex + índices + 12 acciones
│   ├── drivers.json · drivers_indices_sectores.json
│   ├── agenda_semanal.json · plantilla_señal.json
├── scripts/               ← scripts de ejecución
│   ├── mt5_integration.py ← MT5: precios, niveles, gráficos (20 tickers)
│   ├── orquestador.py · market_data.py
│   ├── formatter_whatsapp.py · señal_manager.py
├── templates/             ← templates de mensajes WhatsApp
│   ├── apertura_mercado.txt · resumen_semanal.txt · cierre_semanal.txt
│   ├── encuesta_tendencia.txt · encuesta_precio.txt
│   ├── concepto_semana.txt · señal_operativa.txt
├── data/                  ← datos persistentes
│   ├── historial_señales.json
│   └── charts/            ← PNGs generados desde MT5
└── mcp/                   ← configuración MCP
    └── mcp_config.json    ← WhatsApp + TrendRadar + Firecrawl
```
