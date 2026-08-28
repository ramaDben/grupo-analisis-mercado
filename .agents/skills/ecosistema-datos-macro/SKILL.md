---
name: ecosistema-datos-macro
description: Gestiona la agenda macroeconómica oficial y automatiza la extracción de datos desde fuentes soberanas oficiales (Tesoro EE.UU., FRED, BCCh, BCE, BoE, Ministerio de Finanzas de Japón - MOF, Statistics Bureau - MIC y Banco de Japón - BoJ) hacia data central/.
---

# Flujo de Trabajo: Ecosistema de Datos Macroeconómicos y Agenda Oficial

Esta skill formaliza la ingesta de datos, la gestión de calendarios oficiales y el control de novedades para alimentar los reportes editoriales y cuantitativos de Grupo Inteligencia.

---

## 1. Principio Rector: Soberanía de Fuentes Oficiales Primarias

> [!IMPORTANT]
> Los datos macroeconómicos y curvas soberanas de cada país deben extraerse **100% de su organismo gubernamental emisor primario**, evitando agregadores secundarios extranjeros desfasados (como series mensuales de FRED para bonos internacionales):
> 
> * 🇺🇸 **EE.UU.:** U.S. Department of the Treasury (*Fiscal Data*) & FRED (series oficiales diarias).
> * 🇨🇱 **Chile:** Banco Central de Chile (*BCCh* - API SIED).
> * 🇪🇺 🇬🇧 **Europa y UK:** Banco Central Europeo (*BCE SDMX*) & Bank of England (*BoE IADB*).
> * 🇯🇵 **Japón:**
>   - **Curva Soberana JGB (1Y a 40Y):** Ministerio de Finanzas de Japón (*Ministry of Finance - MOF* vía `jgbcm.csv`).
>   - **Inflación e IPC:** Oficina de Estadísticas del Ministerio de Asuntos Internos (*Statistics Bureau - MIC* vía `stat.go.jp` y `e-stat.go.jp`).
>   - **Política Monetaria:** Banco de Japón (*Bank of Japan - BOJ* vía `boj.or.jp` y `stat-search.boj.or.jp`).
> * 🛢️ **Commodities:** U.S. Energy Information Administration (*EIA* para WTI/Brent), LME / COMEX / MT5 (*Cobre en USD/t*) y LBMA/Spot (*Oro*).

---

## 2. Consulta de Agenda y Zonas Horarias Oficiales
Cuando el usuario pida "ver agenda", "qué hay hoy", "revisar calendario" o "actualizar datos":
- Ejecuta en PowerShell:
  `python .agents/skills/ecosistema-datos-macro/scripts/agenda.py`
- Salida estructurada JSON:
  `python .agents/skills/ecosistema-datos-macro/scripts/agenda.py --json`
- **Gestión de Cruce de Día:** Los eventos asiáticos (ej. IPC de Japón a las 08:30 JST) se procesan con su huso nativo (`Asia/Tokyo`) y se mapean a su ventana de Chile (`America/Santiago`, 19:30 o 01:00 AM).

---

## 3. Ingesta y Detección de Novedades (Zero-Spam)
- Ejecuta el pipeline maestro de ingesta:
  `python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py`
- Para forzar la actualización:
  `python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py --force`
- El pipeline consulta los 5 extractores nativos:
  1. `extractor_usa.py` (Tesoro + Fed)
  2. `extractor_chile.py` (BCCh)
  3. `extractor_europa_uk.py` (BCE + BoE)
  4. `extractor_commodities.py` (EIA + Metales)
  5. `extractor_japon.py` (MOF + MIC + BOJ)

---

## 4. Modelo de Pronóstico de Inflación y Desglose por Componentes
- Previo a las publicaciones de inflación (ej. Japón):
  `python scripts/pronostico_inflacion_japon.py`
- Pondera los 4 componentes de la canasta oficial del MIC (energía, alimentos procesados, salarios Shunto en servicios, manufacturas) y emite la matriz de 3 escenarios en `data central/DATA JAPON/raw/pronostico_inflacion_japon.json`.

---

## 5. Validación de Estado y Snapshot de Drivers
- Verifica que se haya actualizado:
  - `data central/DATA DRIVERS USDCLP/latest_drivers.json` (con frescura `as_of` y banderas `is_stale`).
  - `data central/DATA AGENDA/estado_ejecucion.json` (con `hay_novedades: bool`).

---

## 6. Encadenamiento con Reportes y Análisis
- **Si `hay_novedades == False`:** Informa educadamente que los datos ya están al día y no requiere reescritura para evitar reportes duplicados.
- **Si `hay_novedades == True`:** Invoca automáticamente la skill correspondiente (`generar-reporte-editorial` para PDF o kit de WhatsApp con gráfico didáctico).
