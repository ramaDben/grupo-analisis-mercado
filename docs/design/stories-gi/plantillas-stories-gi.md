# Plantillas Stories GI — referencia de estructura

> Doc de referencia. **No** se importó el runtime del canvas de diseño (`support.js`,
> `image-slot.js`, el `.dc.html` completo) — es scaffolding generado del entorno de diseño de
> Claude ("GENERATED... do not edit"), pensado para renderizar dentro de ese canvas, no para
> correr en este repo (Python/PowerShell/markdown, sin stack web). Este documento resume la
> **estructura observable** (tipos de plantilla + campos de contenido), que es el contrato útil
> para la integración con el motor GAM.
>
> Fuente: proyecto Claude Design "Plantilla contenido de marca" (dueño: Rodrigo),
> `https://claude.ai/design/p/05b3bfe8-d8ad-4f83-b7b0-e8de4d77a3cf`. **Solo lectura** — este repo
> nunca escribe de vuelta a ese proyecto compartido, y ninguna lógica/dato propio de este repo
> (config, drivers, mensajes reales) se sube hacia allá.
>
> **2026-07-13**: mapeo campo-por-campo COMPLETO verificado con lectura íntegra del
> `Plantillas Stories GI.dc.html` (~117 KB) vía DesignSync (solo lectura). Reemplaza la
> extracción liviana anterior (grep dirigido) que dejaba el mapeo como pendiente.

## Manual de marca

`Manual Plantilla Stories - Grupo Inteligencia.pdf` (en esta misma carpeta) — guía de marca
(colores, tipografías, layout) provista por el equipo de diseño.

Identidad observada en el canvas: fondo oscuro `#0D0D1A`/`#1A1A2E` (02 Indicador Macro usa tema
claro `#E8F5F0`), acentos `#00DC82` (alcista/positivo), `#E84040` (bajista/riesgo), `#3E91AF` y
`#53C1AB` (neutros de marca). Tipografías Google Fonts: **Syne** (titulares 800), **DM Sans**
(cuerpo), **Space Grotesk** (chips/etiquetas 600). Footer estándar en todas las piezas:
`@grupointeligencia` + `grupointeligencia.com` + `FUENTE: [origen]` + disclaimer CFD opcional.

## Piezas del canvas (verificadas)

El archivo expone **6 plantillas** de Story (1080×1920) más un **carrusel de 4 slides** que es
una pieza independiente (NO pertenece a "06 Calendario", como se asumió en la primera versión de
este doc):

| # | Plantilla | Comando GAM que conversa | Calce |
|---|---|---|---|
| 01 | Market Update | `/noticia` + precio del motor | Parcial — falta snapshot precio/máx/mín/vol |
| 02 | Indicador Macro | `/dato_macro` (modo resultado) | Casi perfecto |
| 03 | Alerta de Mercado | `/alerta` + niveles del motor (híbrido) | Parcial — `/alerta` es multi-activo narrativo, la tarjeta es mono-activo con niveles |
| 04 | Trading Idea | `/señal` | Casi perfecto (ratio R/B se calcula de entrada/TP/SL) |
| 05 | Reporte Flash | — proyecto ajeno (`flash_mcp`) | Fuera de alcance |
| 06 | Calendario Económico | `obtener_calendario_macro` + `/lunes` | Directo |
| C1-C4 | Carrusel "Oportunidades de la semana" | `/domingo` + `/ventas` + `/earnings` | Parcial |

## Campos de contenido por plantilla (verificados)

Nota transversal: en el canvas **no hay tokens de contenido** — todo el texto es ejemplo
estático. Los únicos `{{ }}` son de control del propio canvas (`frameStyle`, `vis.*` para el
selector, `chartDraw`/`chartImg` para alternar gráfico SVG vs. captura pegada, `disc` para el
disclaimer). La integración con el motor decide qué strings se convierten en placeholders.

### 01 Market Update (tema oscuro)
- Chips: `MARKET UPDATE` + categoría (ej. `MERCADOS`) · fecha-hora (`13 JUL 2026 · 09:30`)
- Titular tipo noticia (ej. "Nasdaq marca nuevo máximo histórico...") + párrafo de contexto
- Tarjeta de precio: nombre activo, categoría/país, **precio**, **variación % con ▲/▼**, y 3
  stats: **Máx / Mín / Vol %**
- Gráfico: sparkline SVG (`chartDraw`) o slot para captura (`chartImg`, `id="img-market"`)
- Footer: `FUENTE: [ej. NASDAQ]`

### 02 Indicador Macro (tema claro — única con fondo `#E8F5F0`)
- Chips: `MACRO REPORT` + categoría (ej. `ECONOMÍA · CHILE`) · fecha-hora
- Titular + párrafo de contexto
- Tarjeta del dato: nombre indicador (ej. `IPC MENSUAL · JUNIO`), organismo (ej. `INE CHILE`),
  **valor principal**, **valor interanual**, y 3 stats: **Esperado / Anterior / Meta BCCh**
- Gráfico: barras de últimos 8 meses (mes actual destacado en verde, futuros punteados) o
  slot captura (`id="img-macro"`)
- Footer: `FUENTE: [ej. INE CHILE]`

### 03 Alerta de Mercado (tema oscuro con degradado rojizo)
- Chips: `ALERTA DE MERCADO` (fondo rojo) + categoría (ej. `COMMODITIES · ORO`) · fecha-hora
- Titular + párrafo de contexto
- Tarjeta de precio (borde rojo): activo, tag **RIESGO ALTO**, **precio**, **variación % ▼/▲**,
  y 3 stats: **Soporte / Resistencia / Vol %** (un solo soporte y una sola resistencia)
- Gráfico: velas SVG con línea de soporte rotulada (`SOPORTE 2.300`) o slot captura
  (`id="img-alerta"`) — rótulo del bloque indica temporalidad (ej. `XAU/USD · VELAS 4H`)
- Footer: `FUENTE: [ej. COMEX]`

### 04 Trading Idea (tema azul `#1E3A5F`)
- Chips: `TRADING IDEA` + categoría (ej. `FOREX · USDCLP`) · fecha-hora
- Titular + párrafo con la tesis de la operación
- **3 tarjetas grandes: ENTRADA / OBJETIVO / STOP** (precio en cada una, colores azul/verde/rojo)
- 2 stats: **Riesgo/Beneficio** (ej. `1 : 2,4`) y **Horizonte** (ej. `Intradía`)
- Gráfico: línea con los 3 niveles rotulados y proyección punteada, o slot captura
  (`id="img-idea"`) — rótulo indica temporalidad (ej. `USDCLP · GRÁFICO 1H`)
- Footer: `ANÁLISIS SMARTEXPERTS`

### 06 Calendario Económico (tema oscuro azulado)
- Chips: `CALENDARIO ECONÓMICO` + `AGENDA SEMANAL` · rango de semana (`14 – 18 JUL 2026`)
- Titular + párrafo
- **5 filas de evento** (LUN a VIE): día, hora + país (`09:00 US`), nombre del evento, tag de
  impacto **ALTO** (rojo) / **MEDIO** (azul)
- Footer: `FUENTE: INVESTING`

### Carrusel "Oportunidades de la semana" (4 slides, pieza independiente)
- **1/4 Portada**: chip `OPORTUNIDADES DE LA SEMANA`, indicador `01 / 04`, rango de semana,
  titular, párrafo, y 2 tarjetas-resumen de oportunidad (activo, subtítulo, tag de riesgo
  `RIESGOSO`/`MODERADO`, stats Actual/Objetivo o Temporada/Foco)
- **2/4 Detalle oportunidad 1** (ej. WTI): chips `OPORTUNIDAD · RIESGOSO` + categoría, titular,
  párrafo con el catalizador, tarjeta de precio (**precio**, **% potencial**, tag
  `SESGO ALCISTA/BAJISTA`, stats Objetivo/contexto/Catalizador), gráfico de proyección o slot
  captura (`id="img-c2"`), línea de advertencia de riesgo
- **3/4 Detalle oportunidad 2** (ej. earnings bancos): chips, titular, párrafo, tickers
  destacados (`JPM BAC GS`), tarjeta **ESTRATEGIA** (frase grande), 3 bullets de análisis
- **4/4 Setups**: titular, y **3 tarjetas por acción**: nombre + ticker, tag de escenario
  (`ALCISTA · +4,4%` / `FAVORABLE`), párrafo corto, stats Objetivo/Volumen

## Integración con el motor GAM (roadmap por issues)

La conversión se aborda como **fusión de arquitecturas**: los comandos existentes (productores
de datos) definen payloads estructurados y una capa visual única los renderiza. Roadmap:

1. **#109** (fundación, en curso) — motor de render compartido (`story_render.py` + Playwright
   + `data/stories/` + regla solo-lectura en `CLAUDE.md`) con piloto **03 Alerta de Mercado**
   (fuente híbrida: niveles del motor + narrativa `/alerta`) y soporte de gráfico embebido
   (PNG de `/chart` en el slot `chartImg`).
2. Contratos de datos por comando (convención transversal del payload JSON).
3. 02 Indicador Macro ↔ `/dato_macro`.
4. 04 Trading Idea ↔ `/señal`.
5. 01 Market Update ↔ `/noticia` + precio del motor.
6. 06 Calendario ↔ `/lunes` + `obtener_calendario_macro`.
7. Carrusel Oportunidades ↔ `/domingo` + `/ventas` + `/earnings`.

Reglas permanentes (aplican a todos los issues):
- Flujo de aprobación del repo: nunca se genera/envía sin aprobación explícita del director.
- Una sola vía: los datos reales del motor **nunca** se suben al proyecto de Claude Design
  compartido — el render final se produce y se aprueba dentro de este repo.
- Sincronización con GI por snapshot manual (sin polling): cuando GI actualice plantillas o
  manual de marca, el director confirma y el snapshot se actualiza a mano en un commit.
