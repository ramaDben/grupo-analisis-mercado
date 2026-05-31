# Guía de instalación y configuración

## Requisitos previos

| Requisito | Versión mínima | Para qué se usa |
|-----------|---------------|-----------------|
| Claude Code | última | Invocar los 18 slash commands |
| Python | 3.10+ | Scripts auxiliares (señal_manager, formatter) |
| git | cualquiera | Control de versiones |
| gh CLI | cualquiera | Crear issues/PRs (opcional) |
| Docker Desktop | cualquiera | Evolution API para WhatsApp (futuro) |
| MetaTrader 5 | cualquiera | Si se usa el script legacy `mt5_integration.py` |

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/bbenja11/grupo-analisis-mercado
cd grupo-analisis-mercado
```

### 2. Instalar dependencias Python

```bash
pip install MetaTrader5 pandas requests
```

> `MetaTrader5` solo es necesario si se usa el script `scripts/mt5_integration.py` (integración legacy). Los comandos actuales usan el MCP `reporte-flash` en su lugar.

### 3. Configurar el MCP reporte-flash

El MCP `reporte-flash` es el motor del sistema. Provee análisis técnico desde MT5, calendario macro y noticias de mercado.

Verificar que esté instalado con:
```bash
claude mcp list
```

Si no aparece `reporte-flash`, contactar al equipo técnico para obtener el server y las instrucciones de instalación.

### 4. Configurar MCPs opcionales (WhatsApp)

```bash
# Copiar plantilla de configuración
cp mcp/mcp_config.example.json mcp/mcp_config.json
```

Editar `mcp/mcp_config.json` con las credenciales reales:
- `WHATSAPP_API_KEY`: API key de Evolution API
- `WHATSAPP_GROUP_ID`: ID del grupo de WhatsApp

> `mcp/mcp_config.json` está en `.gitignore` — nunca se commitea al repositorio.

### 5. Verificar la estructura de datos

Confirmar que existen estos archivos:
```
data/historial_señales.json    ← debe existir (puede estar vacío: [])
config/activos.json            ← catálogo de activos
config/agenda_semanal.json     ← estructura diaria L-V
```

Si `data/historial_señales.json` no existe, crearlo con:
```bash
echo "[]" > data/historial_señales.json
```

### 6. Primera ejecución

Abrir Claude Code en el directorio del proyecto:
```bash
cd grupo-analisis-mercado
claude
```

Probar el dashboard del sistema:
```
/estado
```

Debería mostrar: señales de la semana, activos del día, estado de MCPs.

---

## Configuración de Evolution API (WhatsApp — pendiente)

Cuando la conexión WhatsApp/Baileys esté lista, el flujo pasará a ser automático. Pasos:

```bash
# 1. Levantar Evolution API
docker run -d --name evolution-api -p 8080:8080 atendai/evolution-api

# 2. Conectar WhatsApp
# Abrir http://localhost:8080 en el navegador
# Escanear el QR con el teléfono del número del grupo

# 3. Obtener credenciales
# - API Key: en la interfaz de Evolution API
# - Group ID: copiar el ID del grupo de la interfaz

# 4. Actualizar mcp_config.json con las credenciales
```

Ver documentación oficial: https://doc.evolution-api.com/

---

## Variables de entorno

No hay variables de entorno que configurar directamente. Las API keys van en `mcp/mcp_config.json` (gitignored).

Si se usa el MCP `reporte-flash` con autenticación adicional, las credenciales se configuran en el cliente MCP (`.claude.json` del usuario), no en este repositorio.

---

## Estructura de datos persistentes

### `data/historial_señales.json`
Registro de todas las señales enviadas. Consultado antes de cada `/señal` para verificar el límite de 3/semana. Formato:

```json
[
  {
    "fecha": "2026-05-28",
    "ticker": "XAUUSD",
    "nombre": "Oro",
    "direccion": "BUY",
    "entrada": 2320.50,
    "tp": 2345.00,
    "sl": 2305.00,
    "tipo": "swing",
    "enviada": true
  }
]
```

### `data/mensajes/` (gitignored)
Mensajes aprobados guardados con el nombre `YYYY-MM-DD_HH-MM_[tipo].txt`. Se regeneran cada día; no son relevantes para el control de versiones.

### `data/charts/` (gitignored)
PNGs generados desde MT5. Se regeneran bajo demanda con `/chart`.

---

## Troubleshooting

**MCP reporte-flash no responde**
- Verificar con `claude mcp list` que aparezca como conectado
- Reiniciar la sesión de Claude Code
- Si el servidor cachea módulos Python, editarlo y reiniciarlo

**`/señal` dice que se superó el límite**
- Revisar `data/historial_señales.json` y verificar las fechas de la semana actual
- Si hay registros con fecha antigua que bloquean incorrectamente, limpiar solo los de semanas pasadas

**Archivos con `ñ` se corrompen en git**
- Problema de doble codificación UTF-8 en Windows (ANSI → UTF-8 → Git)
- Solución: usar PowerShell para renombrar, nunca bash en Windows para archivos con `ñ`

**Evolution API no conecta**
- Verificar que Docker Desktop esté corriendo
- El contenedor `evolution-api` debe estar en estado `Up`
- El QR expira cada 30-60 segundos: escanear rápido
