# SPEC — Refactorización del proyecto grupo-analisis-mercado

## Estado actual (fase: cerrada — ver cierre al final)
Fecha de apertura: 2026-05-31 · Cierre: 2026-06-02 · Continúa en issue #25

## Problema
El proyecto acumula deuda técnica y estructural que dificulta la operativa diaria. Los slash commands referencian scripts Python, MCPs y archivos que no están conectados o están duplicados. Hay deriva entre la documentación y la implementación real.

## Áreas de refactorización identificadas

### 1. Limpieza de archivos huérfanos y duplicados
- `ampliacion-mercado/` contiene copias de `config/activos.json` y `config/drivers_indices_sectores.json` ya absorbidas en la raíz → eliminar carpeta
- `MASTER_SPEC_FINAL.md` y `SPECS_17_COMANDOS.md` están desactualizados vs `CLAUDE.md` → unificar o eliminar
- `scripts/_datos_entregables.py` y `data/datos_entregables.json` con propósito poco claro → revisar si se usan

### 2. Corrección de encoding en nombres de archivo
- `scripts/señal_manager.py` y `data/historial_señales.json` muestran encoding corrupto (`seÃ±al`) en algunas vistas → verificar y normalizar encoding UTF-8 en todo el proyecto

### 3. Desacoplamiento de scripts Python de los slash commands
Los comandos (ej: `/lunes`) piden `python scripts/orquestador.py` como SETUP, pero Claude Code ya no necesita ese intermediario: la lógica de rotación de activos, señales y plan diario está mejor expresada directamente en los `.md` de los comandos o en config JSON.
- **Decisión**: los scripts quedan como utilidades opcionales (ejecutables manualmente), no como dependencia de los comandos
- Los comandos deben funcionar sin ejecutar Python

### 4. Integración real del MCP reporte-flash
El sistema ya tiene instalado `mcp__reporte-flash__` con tools funcionales:
- `analyze_ticker` → reemplaza el rol de `mt5_integration.py` para análisis técnico
- `get_economic_calendar` → reemplaza el rol de Firecrawl para calendario macro
- `get_market_news` → reemplaza el rol de TrendRadar para noticias
- `scan_sector` / `scan_sectors` → nuevo poder: análisis sectorial

Los slash commands deben actualizarse para llamar estos tools en lugar de scripts Python o MCPs no conectados.

### 5. Eliminación de MCPs no conectados de los comandos
WhatsApp (Evolution API), TrendRadar y Firecrawl están definidos en `mcp/mcp_config.json` pero **ninguno está activo**. Los comandos tienen flujo optimista que asume que están disponibles.
- **Decisión**: simplificar a flujo único: generar contenido → mostrar para copiar → guardar en `data/mensajes/`
- Eliminar referencias a `mcp__whatsapp__send_message` hasta que Evolution API esté conectada

### 6. Consolidación del catálogo de activos
`config/activos.json` tiene los 4 activos principales del grupo (USD/CLP, Oro, WTI, US100).
Los slash commands mencionan US500 y US30 que no están en el catálogo.
- **Decisión**: alinear catálogo con lo que realmente se cubre

### 7. Comando `/domingo` sin documentar
Existe `.claude/commands/domingo.md` pero no está en el CLAUDE.md ni en la tabla de comandos.
- **Decisión**: documentar o eliminar

## Alcance de la refactorización (fuera de scope)
- NO cambiar la lógica de contenido (formato WhatsApp, estructura de mensajes)
- NO modificar `data/historial_señales.json` ni `data/mensajes/`
- NO modificar la agenda semanal ni los drivers

## Criterios de aceptación
- [ ] Todos los slash commands funcionan sin depender de `python scripts/`
- [ ] Los comandos usan `mcp__reporte-flash__` para datos técnicos y macro
- [ ] Sin carpetas duplicadas ni docs desactualizados en la raíz
- [ ] `/estado` muestra estado real del sistema (señales, MCPs activos)
- [ ] Encoding UTF-8 consistente en todos los archivos

## Archivos a tocar (estimado)
- `.claude/commands/*.md` — todos los 17 comandos (actualizar dependencias)
- `CLAUDE.md` — agregar `/domingo`, actualizar tabla de comandos
- `config/activos.json` — alinear con cobertura real
- `mcp/mcp_config.json` — marcar MCPs inactivos con comentario
- Eliminar: `ampliacion-mercado/`, docs duplicados

---

## Cierre (2026-06-02)

Esta idea se cierra. El trabajo restante se gestiona en **issue #25** (Nivel 1/2/3 de higiene).

**Criterios cumplidos:**
- ✅ Los slash commands ya no dependen de `python scripts/...` (verificado: 0 referencias en `.claude/commands/`).
- ✅ Sin carpetas duplicadas: `ampliacion-mercado/` ya no existe.
- ✅ `/domingo` documentado en `CLAUDE.md`.
- ✅ `COMANDOS.md` alineado (banner + se quitó `orquestador.py` como paso obligatorio).
- ✅ Conteo de comandos unificado a 21 en `CLAUDE.md` y `docs/setup-guide.md`.

**Decisiones revisadas vs. el plan original:**
- ❌ El punto 4 ("integrar MCP reporte-flash") quedó **obsoleto**: `reporte-flash`/`flash_mcp/` es código de **otro proyecto** y se sacó del repo (issue #25). El MCP canónico es `market_data_mcp/` ("market-data").
- ⚠️ Encoding `ñ` en nombres de archivo: pendiente y acotado. Los nombres user-facing (`/señal`, `templates/señal_operativa.txt`, `config/plantilla_señal.json`) **conservan `ñ` por diseño**; solo se evalúa renombrar infraestructura (`scripts/señal_manager.py`, `data/historial_señales.json`) en issue #25.
