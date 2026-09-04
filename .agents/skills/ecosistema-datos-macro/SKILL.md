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
  `uv run python .agents/skills/ecosistema-datos-macro/scripts/agenda.py`
- Salida estructurada JSON:
  `uv run python .agents/skills/ecosistema-datos-macro/scripts/agenda.py --json`
- **Gestión de Cruce de Día:** Los eventos asiáticos (ej. IPC de Japón a las 08:30 JST) se procesan con su huso nativo (`Asia/Tokyo`) y se mapean a su ventana de Chile (`America/Santiago`, 19:30 o 01:00 AM).

---

## 3. La cadena de datos tiene TRES pasos y un solo punto de entrada

> [!CAUTION]
> **La ingesta es el paso 1 de 3, no la cadena.** Correr solo la ingesta deja los
> precios de MT5 y el sesgo del Playbook con la antigüedad que ya tenían, y el motor
> sobre precios que no se actualizaron produce un sesgo que **parece** fresco. Eso es
> peor que fallar, porque falla de forma convincente.

Ejecuta **siempre** el punto de entrada único, que corre los tres pasos en orden y
**aborta al primer fallo**:

```powershell
uv run --with MetaTrader5 python scripts/pipeline_datos.py
```

| Paso | Script | Produce |
|---|---|---|
| 1. ingesta | `.agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py` | `data central/DATA */raw` + `latest_drivers.json` |
| 2. precios | `scripts/extractor_precios.py` | `data central/DATA PRECIOS OHLC/` |
| 3. sesgo | `scripts/macro_bias_engine.py` | `macro_bias_output.json` |

**Antes de publicar cualquier cosa, verifica el estado con el comando y no a ojo:**

```powershell
uv run python scripts/pipeline_datos.py --estado
```

Lee los tres relojes juntos y aplica el umbral de vencimiento del Playbook. Si dice
**NO utilizable**, no se publica: se arregla lo que marca `[FALLA]`.

> [!IMPORTANT]
> **Si `--estado` nombra activos caídos a `YFINANCE`, detente.** El extractor cae a
> yfinance cuando el terminal no le sirve un símbolo, y eso **no es equivalente**: son
> futuros (`GC=F`, `CL=F`, `NQ=F`) y no los CFD del broker. El 2026-09-02 cinco de seis
> activos salieron de yfinance mientras la cadena reportaba datos frescos, y los stops
> del Playbook quedaron calculados sobre otro instrumento. Sin umbral de tolerancia: un
> stop calculado sobre otra fuente de precio es un stop de otro mercado.

Los 5 extractores nativos que consulta el paso de ingesta, como referencia:

  1. `extractor_usa.py` (Tesoro + Fed)
  2. `extractor_chile.py` (BCCh)
  3. `extractor_europa_uk.py` (BCE + BoE)
  4. `extractor_commodities.py` (EIA + Metales)
  5. `extractor_japon.py` (MOF + MIC + BOJ)

Para forzar solo la ingesta, sin la cadena (caso raro, y deja los otros dos pasos
atrás):
  `uv run python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py --force`

---

## 4. Modelo de Pronóstico de Inflación y Desglose por Componentes
- Previo a las publicaciones de inflación (ej. Japón):
  `uv run python scripts/pronostico_inflacion_japon.py`
- Pondera los 4 componentes de la canasta oficial del MIC (energía, alimentos procesados, salarios Shunto en servicios, manufacturas) y emite la matriz de 3 escenarios en `data central/DATA JAPON/raw/pronostico_inflacion_japon.json`.

---

## 5. Validación de Estado y Snapshot de Drivers
- La verificación canónica es `uv run python scripts/pipeline_datos.py --estado`, que lee
  los **tres** relojes (`estado_ejecucion.json`, `latest_prices_summary.json`,
  `macro_bias_output.json`) y aplica un solo umbral de vencimiento. Mirar un archivo
  suelto deja pasar justamente el caso de la cadena a medias.
- Informa además la **confianza del modelo**. Hoy ese número **no bloquea**: qué umbral
  corresponde es una decisión de método pendiente del director.
- Los archivos, si hace falta inspeccionarlos:
  - `data central/DATA DRIVERS USDCLP/latest_drivers.json` (frescura `as_of`, banderas `is_stale`).
  - `data central/DATA AGENDA/estado_ejecucion.json` (`hay_novedades: bool`).

---

## 6. Encadenamiento con Reportes y Análisis
- **Si `hay_novedades == False`:** Informa educadamente que los datos ya están al día y no requiere reescritura para evitar reportes duplicados.
- **Si `hay_novedades == True`:** Invoca automáticamente la skill correspondiente (`generar-reporte-editorial` para PDF o kit de WhatsApp con gráfico didáctico).
