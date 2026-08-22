---
name: ecosistema-datos-macro
description: Gestiona la agenda macroeconómica oficial y automatiza la extracción de datos desde el Tesoro de EE.UU., FRED, Banco Central de Chile, BCE, BoE y Commodities hacia data central/.
---

# Flujo de Trabajo: Ecosistema de Datos Macroeconómicos y Agenda Oficial

Esta skill formaliza la ingesta de datos, la gestión de calendarios oficiales y el control de novedades para alimentar los reportes editoriales de Grupo Inteligencia.

## 1. Consulta de Agenda (Modo Interactivo)
Cuando el usuario pida "ver agenda", "qué hay hoy", "revisar calendario" o "actualizar datos":
- Ejecuta en PowerShell:
  `python .agents/skills/ecosistema-datos-macro/scripts/agenda.py`
- Para obtener la salida estructurada en pipelines:
  `python .agents/skills/ecosistema-datos-macro/scripts/agenda.py --json`
- Presenta al usuario los eventos de hoy con sus estados (`PENDIENTE`, `EN_VENTANA`, `PUBLICADO`), las horas locales (Chile) y los eventos de los próximos 7 días.

## 2. Ingesta y Detección de Novedades (Zero-Spam)
- Ejecuta el pipeline maestro de ingesta:
  `python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py`
- Si el usuario solicita forzar la actualización:
  `python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py --force`
- El pipeline consulta los 4 módulos:
  - `extractor_usa.py` (Tesoro Fiscal Data + Curva DGS y Fed Funds de FRED)
  - `extractor_chile.py` (BCCh: Imacec, TPM, Posición Forward T-2)
  - `extractor_europa_uk.py` (BCE SDMX REST + BoE IADB)
  - `extractor_commodities.py` (WTI/Brent EIA, Cobre COMEX en USD/lb, Oro Spot)

## 3. Validación de Estado y Snapshot de Drivers
- Verifica que se haya actualizado:
  - `data central/DATA DRIVERS USDCLP/latest_drivers.json` (con frescura `as_of` y banderas `is_stale`).
  - `data central/DATA AGENDA/estado_ejecucion.json` (con `hay_novedades: bool`).

## 4. Encadenamiento con Reportes Editoriales
- **Si `hay_novedades == False`:** Informa educadamente que los datos ya están al día y no se requiere compilar un nuevo informe para evitar reportes duplicados.
- **Si `hay_novedades == True`:** Invoca automáticamente la skill `generar-reporte-editorial` para redactar y renderizar el PDF oficial correspondiente al evento.

## 5. Mantenimiento del Calendario Anual
- Para refrescar las fechas de los eventos y validar las zonas horarias IANA:
  `python .agents/skills/ecosistema-datos-macro/scripts/actualizar_calendario.py 2026`
