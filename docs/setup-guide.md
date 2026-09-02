# Guía de instalación y configuración

## Requisitos previos

| Requisito | Versión mínima | Para qué se usa |
|-----------|---------------|-----------------|
| Claude Code | última | Invocar los 25 slash commands |
| Python | 3.10+ | MCP `market-data` (`src/market_data_mcp/`) |
| git | cualquiera | Control de versiones |
| gh CLI | cualquiera | Crear issues/PRs (opcional) |
| Chromium (vía Playwright) | el que instala `playwright install` | Render de Stories y envío a WhatsApp Web |
| MetaTrader 5 | cualquiera | Requerido por el MCP market-data (`get_asset_levels`, `get_chart_objects`, `get_symbol_spec`) |
| Playwright (opcional) | cualquiera | Extra `stories` — render de Stories GI (`/story`), instalar con `uv sync --extra stories && python -m playwright install chromium` |

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/ramaDben/grupo-analisis-mercado
cd grupo-analisis-mercado
```

### 2. Instalar dependencias Python

```bash
pip install MetaTrader5 pandas requests
```

> `MetaTrader5` lo requiere el MCP `market-data` (`get_asset_levels`), que corre en la máquina del director con MT5 abierto. Los comandos obtienen los niveles técnicos a través de ese MCP.

### 3. Configurar el MCP market-data

El MCP `market-data` (`src/market_data_mcp/`) es la capa de datos técnicos del sistema. Expone 5 tools: `get_asset_levels` (precio, soportes/resistencias, sesgo, RSI, ATR), `get_chart_objects` (niveles dibujados a mano por el director en MT5 + screenshot), `obtener_calendario_macro` (calendario económico Investing.com — Chile/EE.UU./China/Zona Euro), `get_symbol_spec` (especificaciones de contrato y sesiones de trading) y `get_open_positions` (operaciones abiertas en el terminal MT5). Las noticias se obtienen con `WebSearch` sobre investing.com + fuentes oficiales (Fed, BCCh, OPEP+, EIA, BLS); `WebSearch` también actúa de fallback si `obtener_calendario_macro` falla.

El cliente MT5 (`src/market_data_mcp/mt5_client.py`) está **vendorizado dentro del repo** — el MCP es autocontenido y no depende de ninguna carpeta externa (ver issue #30).

**Credenciales MT5** — copiar la plantilla y rellenar:
```bash
cp src/market_data_mcp/.env.example src/market_data_mcp/.env
```

| Variable | Para qué sirve | ¿Obligatoria? |
|----------|----------------|---------------|
| `MT5_LOGIN` | Número de cuenta del broker | No, si MT5 ya está logueado en el terminal |
| `MT5_PASSWORD` | Contraseña de la cuenta | No, idem |
| `MT5_SERVER` | Servidor del broker | No, idem |
| `MT5_PATH` | Ruta a `terminal64.exe` | No, si MT5 ya corre |

> `market_data_mcp/.env` está en `.gitignore` (patrón `.env`) — nunca se commitea. Si MT5 ya está abierto y logueado en el terminal, el MCP funciona sin rellenar ninguna variable.

**Para Antigravity (AGY):**
Antigravity detecta y carga automáticamente la configuración del MCP desde `.agents/mcp.json` en la raíz del repositorio. Ese archivo **no está en git** porque lleva la ruta absoluta de cada máquina: copia `.agents/mcp.example.json` a `.agents/mcp.json` y reemplaza `<RUTA_ABSOLUTA_AL_REPO>`. También puedes agregarlo manualmente con:
```bash
agy --add-mcp '{"name":"market-data","command":"uv","args":["run","python","src/market_data_mcp/server.py"]}'
```

### Comandos del proyecto en Antigravity

Antigravity ejecuta comandos como **workflows**: archivos markdown en
`.agents/workflows/` que se invocan con `/nombre`, igual que los slash commands de
Claude Code. Estos **sí** están en git.

Hoy hay seis expuestos —`/story`, `/oportunidad`, `/alerta`, `/dato_macro`,
`/apertura` y `/chart`—, los que generan piezas visuales y los datos que las
alimentan. Los comandos de día, los educativos y los internos siguen siendo de
Claude Code.

Cada workflow es un **puntero** al comando canónico de `.claude/commands/`, no una
copia. Por dos razones: mantener una sola definición de cada comando, y porque
**Antigravity corta los workflows en 12.000 caracteres** — `story.md` tiene más de
43.000 y no cabría de ninguna manera.

Antigravity tampoco lee `CLAUDE.md`, así que las reglas transversales del proyecto
—de dónde salen los datos, cómo se obtiene la hora, los decimales de cada precio,
el tono, el flujo de aprobación— viven en `.agents/rules/proyecto.md`, y cada
workflow manda leerlo antes de ejecutar.

Para exponer un comando nuevo, agrégalo al diccionario `COMANDOS` de
`scripts/agy_workflows.py` y regenera:

```bash
uv run python scripts/agy_workflows.py           # genera los workflows
uv run python scripts/agy_workflows.py --check   # verifica que estén al día
```

No edites los archivos de `.agents/workflows/` a mano: el `--check` los marcaría
como desactualizados, y ese check es lo que evita que AGY se quede atrás cuando se
toca un comando. `tests/test_agy_workflows.py` lo corre en la suite.

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
- (el envío a WhatsApp no usa API keys: va con la sesión vinculada en `.whatsapp_session/`)
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

## Series de precios (prerrequisito del motor)

Las series OHLC **no se versionan**: las regenera `scripts/extractor_precios.py`
desde MT5 (10.000 velas por símbolo). En un clon nuevo hay que producirlas antes de
correr el motor, o `macro_bias_engine.py` y `ticket_engine.py` trabajan sin datos de
precio.

```bash
# Con MetaTrader 5 abierto:
uv run --with MetaTrader5 python scripts/extractor_precios.py
```

Quedan versionadas solo las semanales (`*_W1.json`) y `latest_prices_summary.json`,
que son livianas y sirven de referencia cuando no hay terminal.

---

## Configuración del envío a WhatsApp

El envío va por **WhatsApp Web con Playwright**, sobre una sesión vinculada una sola
vez. Evolution API quedó descartada: no requiere Docker ni credenciales.

```bash
# 1. Instalar el extra que trae Playwright
uv sync --extra stories && python -m playwright install chromium

# 2. Vincular la sesión (una vez): abre Chromium y muestra el QR
python scripts/enviar_whatsapp.py --login

# 3. Comprobar que la sesión sigue viva
python scripts/enviar_whatsapp.py --status

# 4. Ver los canales y sus alias
python scripts/enviar_whatsapp.py --listar-grupos
```

La sesión queda en `.whatsapp_session/` (gitignored: contiene credenciales). Los
canales y sus alias viven en `config/whatsapp_grupos.json`.

> **Automatizar WhatsApp Web va contra sus términos de servicio.** El sender impone
> 45 s mínimos entre envíos y un cupo de 40 al día para que el sistema no pueda
> comportarse como un bot. No subas esos límites ni lo metas en un bucle.

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

**El envío a WhatsApp falla**
- `python scripts/enviar_whatsapp.py --status` dice si la sesión sigue vinculada; si pide
  QR, re-vincular con `--login` (el QR expira en 30-60 segundos: escanear rápido)
- "No se encontró la barra de búsqueda": WhatsApp cambió su interfaz. Hay que volver a
  medir los selectores de `src/whatsapp_sender.py` contra el DOM real, **nunca** relajar
  la verificación de entrega
- "El adjunto no apareció en la conversación": el envío **no** se completó. Revisar si la
  pieza llegó antes de reintentar, o se duplica en el grupo
- "Se alcanzó el cupo de N envíos para hoy": es intencional. Retomar mañana
