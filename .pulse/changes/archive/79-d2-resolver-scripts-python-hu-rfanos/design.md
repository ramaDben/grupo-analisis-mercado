# Diseño — D2 (#79): Resolver scripts Python huérfanos

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Inventario verificado de `scripts/` (2026-06-07)

| Script | Qué hace | Estado real | Disposición |
|---|---|---|---|
| `orquestador.py` | Orquestador diario viejo (rotación, plan del día) | Reemplazado por slash commands | **Eliminar** |
| `market_data.py` | Precios vía Yahoo Finance (`yfinance`) | Reemplazado por MCP market-data (MT5); `yfinance` ya no es dependencia | **Eliminar** |
| `setup.py` | Instalador pip legacy | Superado por uv + `pyproject.toml` (D5) | **Eliminar** |
| `_datos_entregables.py` | Dump one-off; `import` de `mt5_integration` | Script desechable, sin invocación | **Eliminar** |
| `guardar_mensaje.py` | Guardado viejo de mensajes (plano) | Superado por `ruta_mensaje.ps1` + Write (#45) | **Eliminar** |
| `mt5_integration.py` | Integración MT5 legacy + `generar_grafico()` | Datos → MCP; fallback de `/chart` que no corre (faltan deps) | **Eliminar** |
| `formatter_whatsapp.py` | Rellena templates → texto WhatsApp | Ningún comando lo invoca; depende de `orquestador.py` | **Eliminar** |
| `senal_manager.py` | Historial de señales, límite 3/semana | **Vigente** (flujo `/señal`, `architecture.md`); autocontenido | **Conservar** sin tocar |
| `hora_chile.ps1`, `ruta_mensaje.ps1` | Helpers deterministas (hora, ruta de guardado) | **Vigentes** (reglas canónicas CLAUDE.md) | **Conservar** |

## Decisiones del checkpoint (resueltas 2026-06-07)
1. **`mt5_integration.py` → Eliminar.** El EA `GI_ChartExporter` (vía primaria de `/chart`) es **ajeno** (otro proyecto), y el fallback Python no corre. Se borra como legacy.
2. **Contaminación de `chart.md` por EA ajeno → issue aparte.** D2 NO rediseña el pipeline de `/chart`. Se abre un issue nuevo: *"definir pipeline de charts propio (sin EA ajeno GI_ChartExporter)"*. En D2 solo se limpia la **referencia colgada** al script borrado (línea 65), sin tocar el mecanismo del EA (líneas 49/61/62), que queda documentado en el issue nuevo.
3. **`formatter_whatsapp.py` → Eliminar también.** Es deuda muerta (no lo invoca ningún comando). Al borrarlo, `orquestador.py` cae sin necesidad de inline de `obtener_fecha_formateada`.

## Dependencias verificadas
- `formatter_whatsapp.py:45` → `from scripts.orquestador import obtener_fecha_formateada` (perezoso) — ambos se borran, sin dep colgada.
- `_datos_entregables.py` → `import mt5_integration` — ambos se borran.
- `senal_manager.py`: sin imports a scripts a borrar. Limpio.

## Cambios

### Núcleo — eliminar 7 scripts
`orquestador.py`, `market_data.py`, `setup.py`, `_datos_entregables.py`, `guardar_mensaje.py`, `mt5_integration.py`, `formatter_whatsapp.py`.

### Sincronización de referencias vivas (comandos + docs de usuario)
1. **`.claude/commands/chart.md:65`**: quitar la referencia colgada a `scripts/mt5_integration.py` (fallback). Mecanismo del EA (PASO 4) intacto → issue nuevo.
2. **`CLAUDE.md`** (árbol "Estructura del proyecto"): el bloque `scripts/` deja solo `senal_manager.py`, `formatter_whatsapp.py`→fuera, `market_data.py`/`mt5_integration.py`→fuera; reflejar `hora_chile.ps1`/`ruta_mensaje.ps1`.
3. **`README.md`** (líneas 19, 86-88): quitar `formatter` y `mt5_integration.py` del listado; "scripts auxiliares (senal_manager, formatter)" → "senal_manager".
4. **`docs/setup-guide.md`** (líneas 8, 12, 31): quitar refs a `formatter` y al script legacy `mt5_integration.py`.
5. **`docs/design/apertura-interactiva.design.md:25`**: corregir la afirmación "vía chart de `scripts/mt5_integration.py`" (capacidad actual stale).

### Issue nuevo (decisión 2)
Crear issue: *"[chart] Definir pipeline de charts propio — /chart depende del EA ajeno GI_ChartExporter"*, vinculado al contexto (el código propio `mt5_integration.py` se removió en D2; el protocolo `mt5_command.json`/`mt5_response.json` es del EA ajeno).

### Fuera de alcance (constancia)
- `COMANDOS.md` (refs a `orquestador`/`setup`/`mt5_integration`/`senal_manager`): se resuelve en **D3 (#80)**.
- `docs/design/conversion-hora-eventos.design.md:80-81`: registro histórico de auditoría; no se reescribe.

## Verificación
- `grep` post-cambio: 0 referencias vivas a scripts borrados en `.claude/commands/` y docs de usuario (excepto `COMANDOS.md`, diferido a D3).
- Gate Pulse verde (6 linters exit 0) — ninguno targetea `scripts/`.
- `pytest` verde (tests en `tests/`, no importan `scripts/`).

## Criterios de aceptación (#79)
- [ ] Cada script huérfano resuelto (eliminado).
- [ ] Ningún comando ni doc de usuario apunta a un script inexistente (COMANDOS.md diferido a D3).
