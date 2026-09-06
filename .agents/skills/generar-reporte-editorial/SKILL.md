---
name: generar-reporte-editorial
description: Automatiza la lectura de datos económicos desde data central/, gestiona el criterio de canal (PDF institucional vs Chat-First en WhatsApp con gráfico didáctico), redacta informes ciudadanos con fechas exactas y genera visualizaciones de alta resolución.
---

# Flujo de Trabajo: Generación de Reporte Editorial de Mercado y Mensajería

Esta skill formaliza el proceso integral para emitir los informes oficiales y cápsulas de WhatsApp de Grupo Inteligencia dirigidos a clientes finales, inversionistas y traders, traduciendo problemas macroeconómicos complejos a un lenguaje cercano, cotidiano y con máxima claridad pedagógica.

---

## 1. Criterio de Canal y Prevención de Spam (PDF vs Chat-First)

> [!IMPORTANT]
> **Para evitar la fatiga de descargas y la percepción de "spam de archivos" en los grupos de clientes:**
> 
> * 📄 **Documento PDF Oficial:** Reservado estrictamente para hitos macro de alta densidad:
>   - *Resumen Semanal de Mercados (Friday Weekly Wrap)*.
>   - *Informes Especiales IPoM del Banco Central de Chile*.
>   - *Decisiones Mayores de Política Monetaria (Fed / BCCh / BCE / BoE)*.
>   - *Dossiers y Manuales de Capacitación Comercial*.
> 
> * 💬 **Formato Chat-First (Mensaje WhatsApp + Gráfico Adjunto Directo):** Obligatorio para:
>   - Eventos tácticos intradía o de madrugada (ej. *IPC de Japón*, datos de inventarios WTI).
>   - Cobertura puntual de activos fuera de rotación (ej. *USD/JPY*).
>   - Cápsulas de seguimiento donde el cliente necesita entender la dirección en **menos de 30 segundos** sin salir de la app ni descargar documentos pesados.

---

## 2. Estándar Visual de Gráficos: Estructura "Causa y Efecto" y Ajuste Borde a Borde

Para que cualquier persona (desde un cliente novato hasta un trader profesional) comprenda un gráfico macro o intermercado:
- **Dimensiones Exactas Anti-Franjas:** Formato banner institucional calibrado a **`7.2 × 2.82` pulgadas a 300 DPI** (`2160 × 846 px`, ratio $\approx 2.55:1$). Esta relación matemática exacta llena el 100% del contenedor imprimible A4 ($612.6 \times 240\text{ px}$) con **cero franjas vacías laterales ni verticales**.
- **Regla de Oro de Trazado Horizontal Obligatorio:** Todo nivel de precio numérico citado en la prosa ($S_1, S_2, R_1, R_2$, Fibonacci 50%, medias o niveles tácticos) **debe estar obligatoriamente trazado como línea horizontal explícita (`ax.axhline`) en el gráfico respectivo**.
- **Regla del Embudo Técnico / Zona de Compresión:** Cuando múltiples medias (EMAs 50/100) y retrocesos de Fibonacci colisionan en un rango estrecho (ej. franja de 30-40 pips en USD/JPY), el área debe sombreadarse con `axhspan` y explicarse pedagógicamente en el texto como un *embudo de decisión previo a una expansión de volatilidad*.
- **Regla del Cobre Institucional por Tonelada:** Todo análisis de Cobre debe expresarse y graficarse en **valor por tonelada métrica (`USD/t`)** con el ticker `COPPER` de MT5, con 1 decimal en mensajes (`$14274.0 USD/t`).
- **Paleta Institucional Oficial:**
  - Fondo: Oscuro `#0D0D1A` o Claro `#FFFFFF` (para páginas A4 fluidas).
  - Acento 1 (Línea Principal / Fibo / Menta): `#53C1AB`.
  - Acento 2 (Línea Secundaria / Bonos / Azul Cian): `#3E91AF`.
  - Alerta / Resistencias / Coral: `#E76F51`.
  - Rejilla Suave: `#E9ECEF` (alpha 0.2 a 0.25).
- **Estructura Causa y Efecto:**
  - **La Causa (Trayectoria Soberana o Drivers):** Rendimientos oficiales de bonos (ej. *JGB 10Y del MOF*, *Treasury 10Y*) con cita explícita al organismo emisor.
  - **El Efecto:** Cotización real del activo en MT5 con cajas de llamada (*callouts*) que traduzcan hitos y puntos de decisión.

---

## 3. Pauta de Redacción, Consistencia Semántica y Estado de Mercado

### Criterio de Estado de Mercado (Narrativa de Mercado Cerrado):
Durante sesiones nocturnas o asiáticas donde el mercado formal chileno está inactivo, el par USD/CLP no se analiza como un activo táctico en vivo, sino como **"Mercado Cerrado · Radar de Madrugada"**, monitoreando el Cobre asiático (nivel leído del terminal en el momento, entero y sin separador de miles porque `COPPER` tiene `digits = 0`) y el DXY para proyectar el punto de equilibrio de la apertura formal a las 08:30 CLT.

### Regla Semántica Estricta de Colores en Precios:
En los mensajes de WhatsApp y resúmenes de cierre, **los colores miden siempre la dirección del precio del activo en el gráfico**, nunca la fuerza del dato macro:
* 🟢 **Verde = ALCISTA / Sobre Resistencia:** Impulso comprador y subida de precio (`🟢 Sobre [Nivel]`).
* 🟡 **Amarillo = RANGO / Neutral:** Zona de espera, oscilación y absorción (`🟡 Entre [Soporte] y [Resistencia]`).
* 🔴 **Rojo = BAJISTA / Bajo Soporte:** Presión vendedora y caída de precio (`🔴 Bajo [Nivel]`).

> [!CAUTION]
> **Prohibición:** Queda estrictamente prohibido invertir los colores en función del sesgo del dato (ej. poner verde en una caída de precio porque el IPC salió alto).

### Reglas de Formato Auditadas para Clientes:
1. **Cero Guiones Largos:** Prohibido el uso de guiones largos (`—`) y medios (`–`) en textos de WhatsApp. Sustituir por dos puntos, puntos o comas.
2. **Tabla de Decimales Estricta:**
   - `USDCLP`: 2 decimales (`$926.15`).
   - `USDJPY`: 3 decimales (`159.363`).
   - `XAUUSD`: 2 decimales (`$4585.24`).
   - `WTI / BRENT`: 2 decimales (`$83.49` / `$90.10`).
   - `US100`: 2 decimales (`29604.07`).
   - `COPPER`: 1 decimal en USD/t (`$14274.0 USD/t`).
3. **Resumen Above-the-Fold:** Las primeras 3 líneas deben entregar Activo, Nivel Clave y Qué esperar sin obligar a desplegar el texto largo.

---

## 4. Motor de Renderizado PDF ([`generar_pdf.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/.agents/skills/generar-reporte-editorial/scripts/generar_pdf.py))

### Estándar Tipográfico Oficial Inmutable:
* **Títulos Protagonistas, Logotipo y Cabeceras H1:** **Goldman (700 Bold / 400 Regular)** (`font-family: 'Goldman', sans-serif`).
* **Cuerpo, Subtítulos H2/H3, Badges, Párrafos, Tablas y Metadatos:** **Plus Jakarta Sans (400, 600, 700)** (`font-family: 'Plus Jakarta Sans', sans-serif`).

### Los Perfiles de Informe Oficiales:
1. **Informe Diario de Apertura / Cierre de Mercado:**
   * **Tag / Badges:** `--tag "REPORTE DIARIO"` o `--tag "SESIÓN ASIÁTICA"` · `--badge "RESEARCH & ESTRATEGIA"`
   * **Tema:** `--theme verde` o `--theme oscuro`
   * **Contenido:** Clima de la sesión en lenguaje cotidiano, tabla de niveles spot ($S_1/R_1$), gráficos MT5 del activo del día y agenda de horarios locales.
2. **Reporte Macroeconómico Temático / Sesión Nocturna:**
   * **Tag / Badges:** `--tag "SESIÓN ASIÁTICA"` o `--tag "REPORTE MACROECONÓMICO"` · `--badge "RESEARCH & ESTRATEGIA"`
   * **Tema:** `--theme oscuro` (`#0D0D1A`)
   * **Contenido:** Análisis de deuda soberana (MOF JGB 10Y, Curva US Treasury FRED), política monetaria (BoJ, Fed), embudos técnicos, Cobre en USD/t y sección auditada de *Fuentes Consultadas*.
3. **Manual de Estrategias:**
   * **Tag / Badges:** `--tag "MANUAL DE ESTRATEGIAS"` · `--badge "RESEARCH & ESTRATEGIA"`
   * **Tema:** `--theme verde` o `--theme oscuro`
   * **Contenido:** Guías operativas, Playbook de trading, 5 Regímenes Cuantitativos ($\mathcal{R}_0$ a $\mathcal{R}_4$), gráficos MT5 reales ($7.2 \times 2.82\text{ in}$), cajas verdes (`.box-permitido`) y rojas (`.box-prohibido`), módulo de Volatility Targeting (1.0%) y checklist de 3 pasos.
4. **Resumen Semanal de Mercados (Friday Weekly Wrap):**
   * **Tag / Badges:** `--tag "RESUMEN SEMANAL"` · `--badge "RESEARCH & ESTRATEGIA"`
   * **Tema:** `--theme verde` (`#06231C`)
   * **Contenido:** Ganadores y perdedores de la semana, tabla consolidada de 38 activos, gráficos semanales y radar de la próxima semana.

### Jerarquía Editorial de Portada:
* **Logotipo Superior:** `GRUPO INTELIGENCIA` en **Goldman 700**.
* **Título Protagonista (`--title`):** Renderizado a gran escala en **Goldman 700** (38px).
* **Pretítulo / Tag Superior (`--tag`):** En **Plus Jakarta Sans 700** mayúsculas (`#3E91AF` / `#82E0CE`).
* **Subtítulo (`--subtitle`):** Párrafo explicativo en **Plus Jakarta Sans 400** que traduce el valor práctico del informe.
* **Firma / Emisor (`--analyst`):** `Área de Research & Estrategia`.

### Estándar de Fuentes Oficiales Auditables:
Toda sección `05. Fuentes Consultadas` debe utilizar terminología financiera rigurosa y verificable:
1. **MetaTrader 5 Broker Gateway:** *Flujos de precios Spot en tiempo real, profundidad de mercado, spread y series de velas de alta frecuencia (OHLCV).*
2. **Ministerio de Finanzas de Japón (Ministry of Finance - MOF):** *Curva soberana oficial de Bonos del Gobierno de Japón (JGB de 1 a 40 años) y registros cambiarios.*
3. **Oficina de Estadísticas de Japón (Statistics Bureau / MIC):** *Índices oficiales de Precios al Consumidor (IPC General, Core y Tokio).*
4. **Banco de Japón (Bank of Japan - BoJ):** *Tasa de Política Monetaria (Uncollateralized Overnight Call Rate) y minutas oficiales.*
5. **U.S. Department of the Treasury & Federal Reserve Bank of St. Louis (FRED):** *Curva de rendimientos soberanos (2Y, 10Y, 30Y) y tasas reales TIPS.*
6. **Banco Central de Chile:** *Estadísticas cambiarias del mercado formal, Tasa de Política Monetaria (TPM) y derivados cambiarios.*
7. **CME Group / ICE / LME:** *Precios oficiales de liquidación para contratos de futuros de Cobre LME/COMEX (USD/t), Petróleo WTI/Brent y Oro.*

---

## 5. Resumen para WhatsApp
- Generar siempre `mensaje_resumen_whatsapp.txt` en `reportes_generados/` o en la carpeta del informe.
- Consejos de bolsillo rápidos, párrafos cortos y emojis estratégicos (🏛️, 🛢️, 🇨🇱, 🇯🇵, 💡, 🎯, 🔹).
- Respetar estrictamente la tabla de decimales (`digits`), el Cobre en USD/t, y la ausencia de guiones largos (`—`) o medios (`–`).
