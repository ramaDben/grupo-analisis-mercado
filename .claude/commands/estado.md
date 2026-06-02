Muestra el dashboard completo del sistema. NO envía nada a WhatsApp.

## Dashboard del Sistema — Grupo Análisis de Mercado

Compila y muestra toda la información de estado del sistema en un solo informe.

### 1. Plan del día
Lee directamente `config/agenda_semanal.json` y calcula el día de la semana (hora Chile). Muestra:
- Día de la semana y fecha actual (hora Chile)
- Activos asignados para hoy según la rotación de `config/activos.json`
- Tipo de encuesta del día (tendencia o precio según la agenda)
- Contenido planificado según la agenda del día

### 2. Señales de la semana
Lee `data/historial_senales.json`:
- Señales enviadas esta semana ISO: **N / 3**
- Por cada señal abierta:
  - Ticker + nombre + BUY/SELL
  - Entrada | TP | SL
  - Precio actual (conéctate a MT5 si está disponible)
  - Estado: abierta / cerrada / en ganancia / en pérdida (estimado)

Si MT5 no disponible: muestra los niveles sin precio actual.

### 3. Charts disponibles
Lista todos los archivos en `data/charts/`:
- Nombre del archivo (ticker + temporalidad + fecha)
- Fecha de generación
- Nota si tiene < 4 horas de antigüedad (reutilizable)

### 4. Contenido pendiente
Lista cualquier contenido generado en la sesión actual que NO se haya enviado todavía al grupo.

### 5. Próximas tareas
Basado en el plan del día y la hora actual (hora Chile), sugiere qué corresponde hacer ahora:
- Ej: "Faltan 30 min para el dato del IPC → ejecuta /dato_macro"
- Ej: "Hora de apertura del mercado → ejecuta /martes"
- Ej: "NFP sale en 1 hora → prepara análisis previo con /dato_macro"

### 6. Estado de los MCPs
Informa el estado de cada MCP relevante:
- ✅ **market-data**: activo — get_asset_levels (MT5). `get_economic_events` y `get_market_context` están **deprecados** (devuelven DEPRECATED): calendario y noticias ahora vía WebSearch (investing.com + fuentes oficiales) en /dato_macro y /noticia.
- ⏳ **reporte-flash**: en transición — se mantiene hasta validar market-data completamente
- ⏳ **WhatsApp (Evolution API)**: pendiente — requiere Docker conectado a WhatsApp/Baileys
- ❌ **TrendRadar**: no activo — reemplazado por market-data
- ❌ **Firecrawl**: no activo — reemplazado por market-data

### 7. Sugerencias del sistema

Basado en el estado actual, sugiere acciones:
- Si no hay análisis enviado hoy: "→ Ejecuta /[dia_semana] para la operativa del día"
- Si faltan señales disponibles (< 3): "→ [N] señal(es) disponible(s) esta semana"
- Si hay chart antiguo del activo de hoy: "→ Generar chart actualizado con /chart"
- Si es viernes PM: "→ Recuerda ejecutar /viernes_pm para el cierre semanal"

---

## Formato de salida

Mostrar todo esto como un reporte en terminal, sin formato WhatsApp.
NO mostrar credenciales, API keys ni mensajes de error técnico al director.
Si hay errores internos (MT5 no conectado, archivo no encontrado), reportarlos con mensaje amigable.

Puede ejecutarse N veces al día. Los datos se actualizan cada vez.
