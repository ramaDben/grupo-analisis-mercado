# Guía de instalación y configuración

## Requisitos previos

| Requisito | Versión mínima | Para qué se usa |
|-----------|---------------|-----------------|
| Claude Code | última | Invocar los 21 slash commands |
| Python | 3.10+ | Script auxiliar senal_manager (límite de señales) |
| git | cualquiera | Control de versiones |
| gh CLI | cualquiera | Crear issues/PRs (opcional) |
| Docker Desktop | cualquiera | Evolution API para WhatsApp (futuro) |
| MetaTrader 5 | cualquiera | Requerido por el MCP market-data (`get_asset_levels`) |

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

> `MetaTrader5` lo requiere el MCP `market-data` (`get_asset_levels`), que corre en la máquina del director con MT5 abierto. Los comandos obtienen los niveles técnicos a través de ese MCP.

### 3. Configurar el MCP market-data

El MCP `market-data` (`market_data_mcp/`) es la capa de datos técnicos del sistema. Provee análisis técnico desde MT5 con la tool `get_asset_levels` (precio, soportes/resistencias, sesgo, RSI, ATR).

> El calendario económico y las noticias **no** pasan por el MCP: se obtienen con `WebSearch` sobre investing.com + fuentes oficiales (Fed, BCCh, OPEP+, EIA, BLS). Las tools `get_economic_events` / `get_market_context` quedaron **deprecadas** (devuelven `{"error": "DEPRECATED"}`).

El cliente MT5 (`market_data_mcp/mt5_client.py`) está **vendorizado dentro del repo** — el MCP es autocontenido y no depende de ninguna carpeta externa (ver issue #30).

**Credenciales MT5** — copiar la plantilla y rellenar:
```bash
cp market_data_mcp/.env.example market_data_mcp/.env
```

| Variable | Para qué sirve | ¿Obligatoria? |
|----------|----------------|---------------|
| `MT5_LOGIN` | Número de cuenta del broker | No, si MT5 ya está logueado en el terminal |
| `MT5_PASSWORD` | Contraseña de la cuenta | No, idem |
| `MT5_SERVER` | Servidor del broker | No, idem |
| `MT5_PATH` | Ruta a `terminal64.exe` | No, si MT5 ya corre |

> `market_data_mcp/.env` está en `.gitignore` (patrón `.env`) — nunca se commitea. Si MT5 ya está abierto y logueado en el terminal, el MCP funciona sin rellenar ninguna variable.

**Para Antigravity CLI:**
Agrega el MCP al entorno global usando el siguiente comando (ajustando la ruta a tu proyecto):
```bash
antigravity --add-mcp '{"name":"market-data","command":"python","args":["C:\Ruta\Absoluta\grupo-analisis-mercado\market_data_mcp\server.py"]}'
```

**Para Claude Code:**
Verificar que esté instalado con:
```bash
claude mcp list
```

Si no aparece `market-data`, revisar el registro del server `market_data_mcp/server.py` en la configuración de MCPs (`.claude.json` del usuario).

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
data/historial_senales.json    ← debe existir (puede estar vacío: [])
config/activos.json            ← catálogo de activos
config/agenda_semanal.json     ← estructura diaria L-V
```

Si `data/historial_senales.json` no existe, crearlo con:
```bash
echo "[]" > data/historial_senales.json
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

### 7. Ejecutar los tests del MCP market-data (opcional)

La lógica técnica del MCP (`get_asset_levels`) y los contratos de error tienen
cobertura de tests que corre sin MT5 ni `fastmcp` instalados (el stack pesado se
sustituye por un stub en `market_data_mcp/tests/conftest.py`):

```bash
pip install pytest pandas
python -m pytest market_data_mcp/tests -v
```

Cubren: matemática técnica (RSI, clustering, soportes/resistencias), el contrato
`{"error": CÓDIGO, "message": ...}` de `get_asset_levels`, el contrato
`DEPRECATED` de calendario/noticias y el smoke test de import del server.

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

Si el MCP `market-data` requiere autenticación adicional, las credenciales se configuran en el cliente MCP (`.claude.json` del usuario), no en este repositorio.

---

## Estructura de datos persistentes

### `data/historial_senales.json`
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

**MCP market-data no responde**
- Verificar con `claude mcp list` que aparezca como conectado
- Reiniciar la sesión de Claude Code
- Si el servidor cachea módulos Python, editarlo y reiniciarlo

**`/señal` dice que se superó el límite**
- Revisar `data/historial_senales.json` y verificar las fechas de la semana actual
- Si hay registros con fecha antigua que bloquean incorrectamente, limpiar solo los de semanas pasadas

**Archivos con `ñ` se corrompen en git**
- Problema de doble codificación UTF-8 en Windows (ANSI → UTF-8 → Git)
- Solución: usar PowerShell para renombrar, nunca bash en Windows para archivos con `ñ`

**Evolution API no conecta**
- Verificar que Docker Desktop esté corriendo
- El contenedor `evolution-api` debe estar en estado `Up`
- El QR expira cada 30-60 segundos: escanear rápido
