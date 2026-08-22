---
name: generar-reporte-editorial
description: Automatiza la lectura de datos económicos desde data central/, redacta un informe ciudadano con fechas exactas, genera un PDF con diseño oficial (Space Grotesk / Syne con altitud estilizada), integra gráficos de alta resolución y crea el mensaje de WhatsApp.
---

# Flujo de Trabajo: Generación de Reporte Editorial de Mercado

Esta skill formaliza el proceso integral para emitir los informes oficiales de Grupo Inteligencia dirigidos a clientes finales, inversionistas y PYMEs, garantizando un estándar de diseño gráfico y editorial de nivel banca institucional.

---

## 1. Verificación de Estado y Consolidación de Datos
- Lee el archivo de control `data central/DATA AGENDA/estado_ejecucion.json`.
- Si `hay_novedades == False` y no se especificó forzar (`--force`), notifica que los informes están al día y no requiere reescritura innecesaria.
- Lee el consolidado instantáneo:
  `data central/DATA DRIVERS USDCLP/latest_drivers.json`
  así como las series en `data central/DATA [PAIS|TEMA]/raw/*.json`.

---

## 2. Generación e Integración de Gráficos Editoriales (Estándar Estricto)
Para respaldar visualmente el análisis sin romper la paginación ni generar hojas en blanco:
- **Motor Gráfico:** Utilizar siempre [`scripts/generar_graficos.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/.agents/skills/generar-reporte-editorial/scripts/generar_graficos.py) o [`scripts/generar_graficos_drivers.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/scripts/generar_graficos_drivers.py).
- **Dimensiones Obligatorias:** Formato banner compacto de **7.2 x 2.5 pulgadas** (`figsize=(7.2, 2.5)` a **300 DPI**).
- **Paleta Institucional Oficial:**
  - Fondo: Blanco `#FFFFFF`
  - Texto y Títulos: Negro Profundo `#0D0D1A`
  - Línea de Acento 1: Verde Menta `#53C1AB`
  - Línea de Acento 2: Azul Cian `#3E91AF`
  - Alerta / Conflicto: Coral `#E76F51`
  - Rejilla Suave: `#E9ECEF` (alpha 0.9)
- **Embebido en Markdown:** `![Descripción](C:/Users/bbrav/.../graficos/nombre.png)`.

---

## 3. Pauta de Redacción: "Modelo de 3 Capas" (Hecho -> Traducción -> Decisión)
Cada capítulo del informe debe estructurarse obligatoriamente bajo **3 capas de contenido**:
1. 📌 **El Hecho Oficial:** El dato macroeconómico formal con fecha exacta y cifra dura (ej. *"El 19 de agosto, el Tesoro de EE.UU. anunció..."*).
2. 💡 **La Traducción en Simple (¿Qué significa para ti?):** Explicación aterrizada en lenguaje cotidiano, sin jerga innecesaria.
3. 🎯 **La Decisión Financiera (Semáforo de Acción de Bolsillo):**
   - 🟢 **Momento de Invertir / Oportunidad:** Dónde colocar el dinero hoy (Depósitos a Plazo, Fondos en UF, Dólares escalonados, Renta Fija Corta).
   - 🟡 **Momento de Cautela / Esperar:** Qué compras o decisiones postergar.
   - 🔴 **Momento de Evitar:** Riesgos concretos (sobreendeudamiento a crédito, créditos de consumo caros, deudas en moneda extranjera).

**Estructura Obligatoria del Documento:**
- `## 01. ...` a `## 03. ...`: Capítulos temáticos con el modelo de 3 capas y gráficos tipo banner integrados.
- `## 04. Brújula de Decisiones: ¿Qué Hacer con tu Dinero Hoy?`: Tabla ejecutiva por perfiles (Ahorrante/Familia, Inversionista, PYME/Empresa).
- `## 05. Fuentes Consultadas`: Listado formal de entidades oficiales.

---

## 4. Motor de Renderizado PDF ([`generar_pdf.py`](file:///C:/Users/bbrav/grupo-analisis-mercado/.agents/skills/generar-reporte-editorial/scripts/generar_pdf.py))

### Variantes de Edición y Paleta Institucional:
1. **Edición Temática / Macro (Estándar durante la semana):**
   - **Portada y Disclaimer:** Azul Negro Oscuro (`#0D0D1A`).
   - **Acentos y Badges:** Verde Menta (`#53C1AB`) y Azul Cian (`#3E91AF`).
   - **Comando:** `--theme oscuro`.
2. **Edición Resumen Semanal de Mercados (Friday Weekly Wrap):**
   - **Portada y Disclaimer:** Verde Oscuro Institucional (`#062C22` / `#0F4539`).
   - **Acentos y Badges:** Azul Cian (`#3E91AF`) para el texto superior, barra divisoria y badges.
   - **Comando:** `--theme verde`.

### Reglas de Diseño y Tipografía:
1. **Tipografía Syne 800 (Altitud Estilizada y Mayor Legibilidad):**
   - Portada (Título Principal): `display: block; transform: scaleY(1.15); transform-origin: left top; font-size: 46px; margin: 0 0 34px 0;`.
   - Portada y Disclaimer (Marca): `display: inline-block; transform: scaleY(1.18); transform-origin: left center;`.
   - Encabezados `h1`: `display: block; transform: scaleY(1.14); transform-origin: left bottom; font-size: 22px;`.
   - Título Disclaimer: `display: inline-block; transform: scaleY(1.15); transform-origin: left bottom; font-size: 20px;`.
   - Cuerpo de texto, párrafos, tablas y semáforos en **Space Grotesk** (`11.5px` – `12px`, interlineado `1.55 – 1.6`).
2. **Tablas Markdown Estructuradas:**
   - Conversión obligatoria con `markdown.markdown(md_text, extensions=['tables', 'fenced_code'])`.
   - Regla CSS estricta: `table-layout: auto !important` y `white-space: normal !important` para evitar el colapso de columnas.
   - Encabezados oscuros `#0D0D1A` con línea de acento menta `#53C1AB` y filas alternadas en `#F8FAF9`.
3. **Control Anti-Cortes (`break-inside: avoid`):**
   - Imágenes, tablas y encabezados no deben cortarse entre páginas.

---

## 5. Resumen para WhatsApp
- Generar siempre `mensaje_resumen_whatsapp.txt` o `cierre_semanal_whatsapp.txt` en `reportes_generados/`.
- Consejos de bolsillo rápidos, párrafos cortos y emojis estratégicos (🏛️, 🛢️, 🇨🇱, 💡, 🎯).
- Respetar estrictamente la tabla de decimales (`digits`) y la ausencia de guiones largos (`—`) según `CLAUDE.md`.
