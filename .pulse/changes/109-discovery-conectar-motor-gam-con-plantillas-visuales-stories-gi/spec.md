# Spec — Comando `/story alerta`: piloto de render de Stories GI (#109)

> Formaliza `idea.md` y `proposal.md` (fases explore/propose aprobadas). **ENMIENDA 2026-07-13**
> (aprobada por el director, ver comentario en issue #109): tras la lectura íntegra del canvas
> real (`Plantillas Stories GI.dc.html`, vía DesignSync solo-lectura) se constató que los campos
> soporte/resistencia asumidos en Discovery pertenecen a la plantilla **"03 Alerta de Mercado"**,
> no a "Market Update" (que es noticia + snapshot de precio, ahora issue #113). La piloto de este
> Change pasa a ser **03 Alerta de Mercado** con fuente de datos híbrida. El resto del alcance
> (motor de render, helpers, docs, dependencia opcional) se mantiene. La conversión de las demás
> plantillas quedó en el roadmap #110-#115.
>
> Esta spec fija el comportamiento observable del nuevo slash command `/story alerta`, su contrato
> de datos, el mecanismo de render y la convención de guardado. No decide implementación interna
> de detalle: eso queda para `design.md`.

## Objetivo

Dar al director un comando nuevo, `/story alerta`, que combine niveles reales del motor
(soporte/resistencia/precio vía `get_asset_levels`) con una narrativa de alerta (titular +
párrafo, mismo criterio editorial de `/alerta`) y produzca la Story de marca GI
(PNG 1080×1920, plantilla "03 Alerta de Mercado") con el mismo flujo de aprobación del resto del
repo, sin subir nunca datos propios al proyecto Claude Design compartido (issue #109).

## Alcance

### IN
- Nuevo archivo `.claude/commands/story.md` (Capa 2), invocable como `/story alerta`.
- Nuevo módulo de render `scripts/story_render.py`: recibe un payload de datos (ver "Contrato de
  datos") y produce el PNG vía Playwright headless. Es el **único** lugar del repo que sabe
  renderizar Stories — reutilizable por las plantillas futuras (#111-#115) sin duplicar pipeline.
- Nuevo snapshot de template `templates/stories/alerta.html` (+ CSS embebido o archivo hermano):
  reimplementación estática del layout "03 Alerta de Mercado" del canvas, fiel a la identidad
  observada (fondo `#0D0D1A`/degradado rojizo, acentos `#00DC82`/`#E84040`, tipografías
  Syne/DM Sans/Space Grotesk, footer estándar `@grupointeligencia` + fuente + disclaimer CFD),
  sin el runtime React del canvas (`support.js`/`image-slot.js` quedan fuera).
- **Soporte de gráfico embebido**: el slot de gráfico acepta opcionalmente un PNG ya generado por
  `/chart` (equivalente local del `chartImg` del canvas); si no se aporta, el template muestra el
  gráfico decorativo SVG de velas del snapshot (equivalente del `chartDraw`).
- Nuevo helper `scripts/ruta_story.ps1` (hermano de `scripts/ruta_mensaje.ps1`, no lo modifica).
- Nueva dependencia **opcional** en `pyproject.toml`: `playwright` en
  `[project.optional-dependencies] stories` (ver R8).
- `.gitignore`: nueva entrada `data/stories/*.png`.
- `CLAUDE.md`: nueva sección "Stories GI" **inmediatamente después de "MCP Servers integrados"**
  (ubicación confirmada por el director) con la regla "solo lectura" del canvas + fila `/story`
  en la tabla de Capa 2.
- `.claude/shared/modo_ejecutivo.md`: `/story` en la lista de **no elegibles** (criterio `/chart`).
- `tests/test_story_render.py`: tests del mapeo (puros) + test de render `skipif` sin Chromium.

### OUT (explícitamente diferido — no se reabre)
- Las demás plantillas y el carrusel: roadmap #110 (contratos), #111 (Indicador Macro), #112
  (Trading Idea), #113 (Market Update), #114 (Calendario), #115 (carrusel Oportunidades).
- Modo ejecutivo/guion interno para `/story` (decisión 6 del proposal).
- Sincronización automática con el canvas (snapshot manual, decisión 8).
- La visión "motor como cerebro hub GI" (decisión 9).
- Envío automático a WhatsApp — el flujo termina en "PNG aprobado, listo para adjuntar".
- Comparación pixel-a-pixel contra un "golden PNG" (no existe export de referencia de GI).
- Modificar `alerta.md`, `apertura.md`, `chart.md`, `scripts/ruta_mensaje.ps1` o `data/charts/`.

## Riesgos resueltos

### Riesgo 1 — Viabilidad de Playwright + Chromium (RESUELTO: viable)
Validado empíricamente en la máquina real del director (Windows 11, sin admin, ~690 MB en
`%LOCALAPPDATA%\ms-playwright\`, render headless 1080×1920 verificado por header IHDR). Se usa
Playwright; el fallback Pillow/HTML-to-image queda documentado como plan B formal, no se
implementa.

### Riesgo 2 — Contrato de campos (RESUELTO TOTAL, 2026-07-13)
La lectura **íntegra** del canvas real ya se hizo (DesignSync, solo lectura) — no queda ninguna
verificación pendiente del canvas. Hallazgos que gobiernan esta spec:
- El canvas **no tiene tokens de contenido**: todo el texto es ejemplo estático; los `{{ }}` son
  de control del propio canvas (`frameStyle`, `vis.*`, `chartDraw`/`chartImg`, `disc`). Los
  placeholders los define **este repo** en su snapshot local.
- Campos reales de "03 Alerta de Mercado" (ver
  `docs/design/stories-gi/plantillas-stories-gi.md`): chips (`ALERTA DE MERCADO` + categoría) ·
  fecha-hora · titular · párrafo · tarjeta de precio (rótulo activo, tag de riesgo, precio,
  variación % ▼/▲, stats **Soporte / Resistencia / Vol %** — un solo soporte y una sola
  resistencia) · gráfico (velas SVG con soporte rotulado, o captura) · footer con fuente y
  disclaimer.

### Riesgo 3 — Fuente de datos híbrida, nunca texto renderizado (RESUELTO)
`/story alerta` **no parsea** el texto WhatsApp de ningún comando. Construye su payload desde:
- **Niveles y precio**: `get_asset_levels` del motor (fallback manual si MT5 no disponible,
  mismo patrón que `apertura.md` PASO 4A). Un solo soporte y una sola resistencia (los más
  próximos al precio).
- **Narrativa (titular + párrafo)**: generada en el momento con el criterio editorial de
  `/alerta` PASO 1 — si hay evento real de las últimas horas (WebSearch investing.com + fuentes
  oficiales), la alerta es noticiosa; si no, es una lectura técnica ("el activo se aproxima a su
  soporte clave"). Registro del repo: dirección explícita, énfasis sin dramatización.
- **Variación % y Vol %**: del motor si están disponibles; si no, se omiten (campos opcionales).

### Riesgo 4 — Convención de guardado (RESUELTO)
`data/stories/<Fecha>/<activo_slug>/<plantilla>/<Hora>_<plantilla>.png` vía nuevo helper
`scripts/ruta_story.ps1`. Ejemplo: `data/stories/2026-07-13/xauusd/alerta/11-45_alerta.png`.
No se toca `ruta_mensaje.ps1` ni `data/charts/`.

### Riesgo 5 — Verificación de output visual (RESUELTO)
1. Tests deterministas del mapeo (puros, sin Playwright, siempre corren en el gate).
2. Test de integración de render `skipif` sin Chromium: PNG existe, IHDR == 1080×1920, > 5 KB.
3. Fidelidad de marca pixel-perfecta: revisión manual del director en la aprobación.

## Contrato de datos — payload `story_alerta`

Estructura que `/story alerta` construye y pasa a `scripts/story_render.py`:

```json
{
  "plantilla": "alerta",
  "activo": {
    "ticker_mt5": "XAUUSD",
    "nombre": "Oro",
    "digits": 2
  },
  "chip_categoria": "COMMODITIES · ORO",
  "fecha_hora": "13 JUL 2026 · 11:15",
  "titular": "El Oro rompe soporte clave y activa señal de riesgo bajista",
  "parrafo": "El metal perdió la zona de 2.320 con volumen creciente, confirmando presión vendedora. Un cierre bajo el soporte abriría espacio hacia nuevos mínimos; se recomienda gestión estricta del riesgo.",
  "rotulo_activo": "ORO · XAU/USD",
  "tag_riesgo": "RIESGO ALTO",
  "precio_actual": "2.318,40",
  "variacion": {
    "pct": "1,86",
    "direccion": "bajista"
  },
  "soporte": "2.300,00",
  "resistencia": "2.360,00",
  "vol_pct": "+21%",
  "rotulo_grafico": "XAU/USD · VELAS 4H",
  "chart_png": null,
  "fuente": "COMEX",
  "sesgo": "Bajista"
}
```

Reglas de mapeo:
- `digits`, `precio_actual`, `soporte`, `resistencia`: valores según `config/activos.json`
  (regla MT5 de `CLAUDE.md`, nunca truncar ceros), presentados con **coma decimal y punto de
  miles** (formato del canvas: `2.318,4`).
- `variacion`: opcional — si el motor no entrega variación del día, se omite la clave completa
  (el template omite ese slot sin hueco). `direccion` ∈ `alcista`/`bajista` (elige flecha ▲/▼ y
  color verde/rojo).
- `vol_pct`: opcional — se omite la clave si no hay dato de volumen confiable.
- `chart_png`: opcional — ruta a un PNG existente de `data/charts/` (generado por `/chart`). Si
  está presente, el template incrusta esa imagen en el slot de gráfico; si es `null`/ausente,
  muestra el SVG decorativo de velas del snapshot. Si la ruta no existe →
  `StoryRenderError` accionable (nunca render con imagen rota).
- `tag_riesgo`: texto corto (`RIESGO ALTO` / `RIESGO MEDIO`), decidido por el comando según el
  contexto (ruptura de nivel/evento → ALTO; aproximación sin ruptura → MEDIO).
- `sesgo`: `Alcista`/`Bajista`/`Lateral` — dirección explícita obligatoria (regla de oro del
  repo); alimenta la coherencia del titular/párrafo, no un slot visual propio.
- `fuente`: texto del footer (ej. `COMEX`, `INVESTING`, `MT5`); si la narrativa nace de una
  noticia, la fuente de la noticia; si es lectura técnica, `MT5 · GRUPO INTELIGENCIA`.
- `titular` ≤ ~70 caracteres y `parrafo` ≤ ~280 caracteres (límites visuales del layout; el
  comando ajusta la redacción antes del preview).

## Alcance de activo por corrida

`/story alerta` genera **exactamente 1 Story para 1 activo** por corrida. Para varios activos,
se ejecuta una vez por activo.

## Requisitos funcionales

### R1 — Registro e invocación del comando
`.claude/commands/story.md` existe (Capa 2), invocable como `/story alerta`. Es el único `[tipo]`
soportado en este Change (los demás llegan con #111-#115). Si se invoca `/story` sin tipo o con
tipo no soportado, responde con la lista de tipos disponibles (hoy solo `alerta`) y vuelve a
preguntar — nunca asume un tipo por defecto.

### R2 — Recolección híbrida de datos
1. Pregunta el activo (uno solo) y la temporalidad del gráfico (etiquetas canónicas del repo).
2. Obtiene precio actual, soporte y resistencia más próximos vía `get_asset_levels`; fallback
   manual si MT5 no está disponible (mismo patrón que `apertura.md` PASO 4A).
3. Detecta si hay evento real reciente que afecte al activo (criterio de `/alerta` PASO 1,
   WebSearch); si lo hay, la narrativa es noticiosa; si no, lectura técnica del precio frente a
   sus niveles. En ambos casos: dirección explícita (sesgo) y registro profesional del repo.
4. Variación % del día y volumen: del motor si están disponibles; si no, se omiten.

### R3 — Construcción del payload
Construye el payload `story_alerta` (ver "Contrato de datos"), incluyendo formateo de precios por
`digits` con coma decimal, `tag_riesgo` según contexto y `fecha_hora` con el reloj de Chile
(regla canónica de `CLAUDE.md`).

### R4 — Render (Playwright headless, centralizado)
Invoca `scripts/story_render.py` con el payload y `templates/stories/alerta.html`. El script:
1. Inyecta los campos en el HTML (mapeo campo-por-campo, sin lógica de negocio).
2. Si `chart_png` está presente, incrusta la imagen en el slot de gráfico; si no, conserva el
   SVG decorativo.
3. Renderiza con Playwright headless (viewport 1080×1920) → PNG con esas dimensiones exactas.
4. Es el único punto de render del repo para Stories — reutilizable por #111-#115.

### R5 — Preview y aprobación (antes de guardar)
Antes de guardar cualquier archivo, el comando muestra un resumen en texto (activo, titular,
párrafo, niveles, tag de riesgo, si lleva chart embebido) y pregunta: **"¿Apruebas esta Story?
¿Generar y guardar el PNG final?"**. Sin aprobación explícita, NO renderiza ni guarda nada.

### R6 — Guardado con nombre canónico
Tras aprobar: `scripts\ruta_story.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Plantilla alerta
-Hora [HH-MM]` y guarda el PNG ahí. Muestra la ruta lista para adjuntar manualmente.

### R7 — Rechazo explícito del flag `ejecutivo`
`/story alerta ejecutivo` → avisa que `/story` no soporta el flag (criterio `/chart`) y continúa
generando la Story normalmente.

### R8 — Dependencia opcional, no forzada
`playwright` en `[project.optional-dependencies] stories`, NO en `[project.dependencies]`.
Instalación: `uv sync --extra stories` + `python -m playwright install chromium` (paso manual
único documentado). El gate no requiere esta dependencia (patrón `MetaTrader5`, deptry `DEP001`).

### R9 — Regla "solo lectura" formalizada en `CLAUDE.md`
Sección "Stories GI" inmediatamente después de "MCP Servers integrados": el proyecto Claude
Design compartido (dueño: Rodrigo, GI) es **solo lectura** — este repo nunca sube datos, lógica
ni configuración hacia allá; el render final se produce y aprueba dentro de este repo.

### R10 — `/story` documentado como no elegible para `ejecutivo`
`.claude/shared/modo_ejecutivo.md` agrega `/story` a "No elegibles", razón igual a `/chart`.

## Requisitos no funcionales

### RNF1 — No rompe comandos existentes
`/story` es aditivo: no modifica `alerta.md`, `apertura.md`, `chart.md`,
`scripts/ruta_mensaje.ps1` ni `data/charts/`.

### RNF2 — Formato de precios consistente
Todo precio respeta `digits` de `config/activos.json`.

### RNF3 — Idioma
Todo el contenido en español (textos fijos de marca del canvas se conservan tal cual).

### RNF4 — Ninguna fuga hacia el canvas compartido
Ningún paso del flujo escribe/sube/postea hacia el proyecto Claude Design — solo se lee el
snapshot local estático (`templates/stories/`).

### RNF5 — Reutilizable para futuras plantillas
Agregar una plantilla (#111-#115) requiere solo: nuevo snapshot HTML, nuevo mapeo payload→HTML y
nuevo `[tipo]` en `story.md`. Sin segundo renderer.

## Casos borde

- **CB-1 (tipo no soportado)**: `/story market_update` → informa que solo `alerta` está
  disponible en este Change (los demás: issues #111-#115) y no continúa (R1).
- **CB-2 (MT5 no disponible)**: fallback manual de precio/niveles, mismo patrón `apertura.md`
  PASO 4A (R2).
- **CB-3 (director rechaza)**: no se renderiza ni guarda nada en `data/stories/` (R5).
- **CB-4 (sin variación/volumen)**: el payload omite `variacion`/`vol_pct`; el template omite
  esos slots sin hueco visual.
- **CB-5 (sin evento noticioso)**: la narrativa es lectura técnica del precio frente a sus
  niveles — el comando NO aborta ni exige noticia (R2.3).
- **CB-6 (flag `ejecutivo`)**: avisa que no aplica y continúa (R7); nunca genera guion.
- **CB-7 (Chromium no instalado)**: `StoryRenderError` con el comando de instalación exacto,
  nunca traceback críptico.
- **CB-8 (`chart_png` con ruta inexistente)**: `StoryRenderError` accionable indicando la ruta
  no encontrada — nunca un render con imagen rota.

## Criterios de aceptación

**AC1 — estructura del comando (estructural)**
`.claude/commands/story.md` contiene, en orden, pasos equivalentes a R1-R7 y menciona
explícitamente "un solo activo por corrida".

**AC2 — mapeo de campos determinista (ejecutable, `pytest`)**
DADO un payload de ejemplo sin `variacion`, sin `vol_pct` y con `chart_png` en `null`,
CUANDO se ejecuta la función de mapeo sobre `templates/stories/alerta.html`,
ENTONCES el HTML resultante contiene `titular`, `parrafo`, `precio_actual`, `soporte`,
`resistencia` y `tag_riesgo` correctamente inyectados, NO contiene placeholders sin resolver,
NO contiene los slots de variación/volumen, y conserva el gráfico SVG decorativo (no `<img>`).

**AC3 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
El render completo produce un PNG con IHDR exactamente 1080×1920 y tamaño > 5 KB.

**AC4 — camino feliz (ejecución guiada)**
`/story alerta` + aprobación → un único PNG en
`data/stories/<Fecha>/<activo_slug>/alerta/<Hora>_alerta.png` y ruta mostrada.

**AC5 — rechazo (ejecución guiada)**
Sin aprobación → ningún archivo en `data/stories/` (CB-3).

**AC6 — flag `ejecutivo` (ejecución guiada)**
`/story alerta ejecutivo` → avisa y genera Story normal, sin guion.

**AC7 — documentación (estructural, `rg`)**
`rg -i "solo lectura" CLAUDE.md` ≥1 match; `rg "/story" .claude/shared/modo_ejecutivo.md` ≥1
match.

**AC8 — dependencia opcional (estructural, `rg`)**
`[project.optional-dependencies]` tiene grupo `stories` con `playwright`; `playwright` NO está
en `[project.dependencies]`.

**AC9 — chart embebido (ejecutable, `pytest`)**
DADO el mismo payload de AC2 pero con `chart_png` apuntando a un PNG de fixture existente,
CUANDO se ejecuta la función de mapeo,
ENTONCES el HTML contiene el `<img>` del chart (URI `file:///` válida) y NO contiene el SVG
decorativo; y con ruta inexistente → `StoryRenderError` (CB-8).

## Riesgos residuales

- **R-1 (drift de marca)**: snapshot manual — riesgo aceptado por el director (decisión 8).
- **R-2 (fidelidad visual del snapshot)**: el snapshot HTML se reimplementa desde la lectura del
  canvas + manual de marca PDF; la fidelidad final la valida el director en la primera
  aprobación real (no hay golden PNG).
- **R-3 (footprint Chromium)**: ~700 MB por versión; verificado con 60 GB libres.

## Preguntas abiertas

Ninguna bloqueante. (La lectura del canvas —antes T0.1— se completó el 2026-07-13; la ubicación
de la sección en `CLAUDE.md` quedó confirmada; el sufijo de carrusel es asunto del issue #115.)

## Referencias

- Issue #109 + comentario de re-alcance (2026-07-13) · issues #110-#115 (roadmap)
- `idea.md`, `proposal.md` de este Change
- `docs/design/stories-gi/plantillas-stories-gi.md` (mapeo verificado 2026-07-13)
- `docs/design/stories-gi/Manual Plantilla Stories - Grupo Inteligencia.pdf`
- `.claude/commands/alerta.md` (criterio editorial PASO 1, tono, dirección explícita)
- `.claude/commands/apertura.md` (patrón fallback MT5→manual PASO 4A)
- `.claude/commands/chart.md` (PNG fuente para `chart_png` + criterio no-elegible `ejecutivo`)
- `scripts/ruta_mensaje.ps1`, `config/activos.json`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`
- Validación empírica Playwright 1080×1920 (Riesgo 1)
