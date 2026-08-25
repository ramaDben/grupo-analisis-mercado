---
name: generar-reporte-editorial
description: Automatiza la lectura de datos económicos desde data central/, gestiona el criterio de canal (PDF institucional vs Chat-First en WhatsApp con gráfico didáctico), redacta informes ciudadanos con fechas exactas y genera visualizaciones de alta resolución.
---

# Flujo de Trabajo: Generación de Reporte Editorial de Mercado y Mensajería

Esta skill formaliza el proceso integral para emitir los informes oficiales y cápsulas de WhatsApp de Grupo Inteligencia dirigidos a clientes finales, inversionistas y traders, garantizando rigor de banca institucional y máxima claridad pedagógica.

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

## 2. Estándar Visual de Gráficos: Estructura "Causa y Efecto" (Auto-Explicativos)

Para que cualquier persona (desde un cliente novato hasta un trader profesional) comprenda un gráfico macro o intermercado:
- **Dimensiones:** Formato banner institucional de **7.2 x 2.8 a 7.2 x 3.2 pulgadas** a **300 DPI** (o `11.2 x 6.2` in para gráficos duales).
- **Paleta Institucional Oficial:**
  - Fondo: Oscuro `#0D0D1A` o Claro `#FFFFFF`.
  - Acento 1 (Línea Principal / Fibo / Menta): `#53C1AB`.
  - Acento 2 (Línea Secundaria / Bonos / Azul Cian): `#3E91AF`.
  - Alerta / Resistencias / Coral: `#E76F51`.
  - Rejilla Suave: `#E9ECEF` (alpha 0.2 a 0.25).
- **Estructura Dual Obligatoria:**
  - **Piso 1 (La Causa):** Muestra los intereses, diferenciales de tasas o drivers macro con **cita explícita al organismo oficial emisor** (ej. *Ministerio de Finanzas de Japón - MOF*, *Tesoro EE.UU.*).
  - **Piso 2 (El Efecto):** Muestra la cotización del par con **cajas de llamada visuales (*callouts*)** que traduzcan caídas históricas y el punto de decisión de hoy.

---

## 3. Pauta de Redacción y Consistencia Semántica de Semáforos

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
   - `USDCLP`: 2 decimales (`$912.37`).
   - `USDJPY`: 3 decimales (`159.618`).
   - `XAUUSD`: 2 decimales (`$4648.39`).
   - `WTI / BRENT`: 2 a 3 decimales (`$85.42`).
   - `US100`: 2 decimales (`29038.03`).
3. **Resumen Above-the-Fold:** Las primeras 3 líneas deben entregar Activo, Nivel Clave y Qué esperar sin obligar a desplegar el texto largo.

---

## 4. Motor de Renderizado PDF ([`generar_pdf.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/.agents/skills/generar-reporte-editorial/scripts/generar_pdf.py))

### Variantes de Edición y Paleta Institucional:
1. **Edición Temática / Macro / Especial (Estándar durante la semana):**
   - **Portada y Disclaimer:** Azul Negro Oscuro (`#0D0D1A`).
   - **Acentos y Badges:** Verde Menta (`#53C1AB`) y Azul Cian (`#3E91AF`).
   - **Badge Superior Inmutable:** `RESEARCH & ESTRATEGIA` (esquina superior derecha junto a `GRUPO INTELIGENCIA`).
   - **Pie de Página:** `RESEARCH Y ESTRATEGIA` (derecha) y `GRUPO INTELIGENCIA` (izquierda).
   - **Comando:** `--theme oscuro`.
2. **Edición Resumen Semanal de Mercados (Friday Weekly Wrap):**
   - **Portada y Disclaimer:** Verde Oscuro Institucional (`#062C22` / `#0F4539`).
   - **Acentos y Badges:** Azul Cian (`#3E91AF`) para el texto superior, barra divisoria y badges.
   - **Badge Superior Inmutable:** `RESEARCH & ESTRATEGIA`.
   - **Comando:** `--theme verde`.

### Jerarquía Editorial de Portada:
- **Título Protagonista (`--title`):** Renderizado a gran escala en **Syne 800** (46px). Debe ser el concepto, activo o sistema protagonista (ej. `Motor GI`, `Minutas del FOMC`, `Monitor USD/CLP`).
- **Pretítulo / Tag Superior (`--tag`):** En Azul Cian/Menta (`#3E91AF`), define la categoría o contexto temático (ej. `DE LOS DATOS A LA DECISIÓN • METODOLOGÍA & ESTRATEGIA` o `REPORTE EJECUTIVO`).
- **Subtítulo (`--subtitle`):** Párrafo explicativo en **Space Grotesk** que traduce el valor práctico del informe.
- **Firma / Emisor (`--analyst`):** `Área de Estudios & Estrategia` o `Dirección de Trading & Research Cuantitativo`.

### Estándar de Fuentes Oficiales Auditables:
Toda sección `05. Fuentes Consultadas` debe utilizar terminología financiera rigurosa y verificable:
1. **MetaTrader 5 Broker Gateway:** *Flujos de precios Spot en tiempo real, profundidad de mercado, spread y series de velas de alta frecuencia (OHLCV).* (Nunca usar "interbancario" para MT5).
2. **Sistemas de Calendario y Consenso Macroeconómico:** *Monitoreo de publicaciones de alta relevancia y medición de desviaciones respecto al consenso.*
3. **U.S. Department of the Treasury & Federal Reserve Bank of St. Louis (FRED):** *Curva de rendimientos soberanos (2Y, 10Y, 30Y) y tasas reales TIPS.*
4. **Banco Central de Chile:** *Estadísticas cambiarias del mercado formal, Tasa de Política Monetaria (TPM) y derivados cambiarios.*
5. **CME Group / ICE:** *Precios oficiales de liquidación para contratos de futuros de Cobre COMEX (HG), Petróleo WTI/Brent y Oro.*

### Reglas de Diseño y Tipografía:
- Tipografía **Syne 800** con altitud estilizada (`scaleY(1.15)`) para títulos y **Space Grotesk** para cuerpo.
- Tablas Markdown estructuradas con `table-layout: auto !important` y `break-inside: avoid`.
- Control anti-cortes (`break-inside: avoid`) en imágenes y encabezados.

---

## 5. Resumen para WhatsApp
- Generar siempre `mensaje_resumen_whatsapp.txt` o `mensaje_presentacion_*.txt` en `reportes_generados/`.
- Consejos de bolsillo rápidos, párrafos cortos y emojis estratégicos (🏛️, 🛢️, 🇨🇱, 💡, 🎯, 🔹).
- Respetar estrictamente la tabla de decimales (`digits`) y la ausencia de guiones largos (`—`) o medios (`–`) según `CLAUDE.md`.
