Muestra el dashboard completo del sistema. NO envía nada a WhatsApp.

## Dashboard del Sistema — Grupo Análisis de Mercado

Compila y muestra toda la información de estado del sistema en un solo informe.

### 1. Plan del día
Obtén la fecha/hora actual de Chile con el reloj del sistema (regla canónica de CLAUDE.md, NUNCA con `WebSearch`), lee `config/agenda_semanal.json` y calcula el día de la semana a partir de esa fecha. Muestra:
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
- Ej: "Faltan 30 min para el dato del IPC → el carrusel lo va a recoger en la próxima tanda"
- Ej: "Hora de apertura de Wall Street → ejecuta /informe apertura"
- Ej: "Cierre en 45 min → ejecuta /informe cierre"

### 6. Estado de los MCPs
Informa el estado de cada MCP relevante:
- ✅ **market-data**: activo — expone 5 tools: `get_asset_levels` (técnico MT5), `get_chart_objects` (marcado manual MT5), `obtener_calendario_macro` (calendario económico), `get_symbol_spec` (especificaciones/sesiones de contrato) y `get_open_positions` (operaciones abiertas). Las noticias se obtienen vía WebSearch.
- ✅ **WhatsApp Web (Playwright)**: activo — `scripts/enviar_whatsapp.py`. Reportar la sesión con
  `--status` y, si existe `data/.whatsapp_envios.json`, cuántos envíos van hoy contra el cupo diario.
- ❌ **TrendRadar / Firecrawl / Finnhub**: no activos — reemplazados por market-data (MT5) + WebSearch

### 7. Sugerencias del sistema

Basado en el estado actual, sugiere acciones:
- Si no hay análisis enviado hoy: "→ Ejecuta /[dia_semana] para la operativa del día"
- Si faltan señales disponibles (< 3): "→ [N] señal(es) disponible(s) esta semana"
- Si la sesión de WhatsApp no está vinculada: "→ Re-vincular con enviar_whatsapp.py --login"
- Si el cupo diario de envíos va alto: decir cuántos quedan antes del tope

---

## Formato de salida

Mostrar todo esto como un reporte en terminal, sin formato WhatsApp.
NO mostrar credenciales, API keys ni mensajes de error técnico al director.
Si hay errores internos (MT5 no conectado, archivo no encontrado), reportarlos con mensaje amigable.

Puede ejecutarse N veces al día. Los datos se actualizan cada vez.
