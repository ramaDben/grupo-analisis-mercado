
<!-- change:109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi -->
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

<!-- change:119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta -->
# Specification: Stories GI · Fase A — motor de render 16:9 + migrar plantilla Alerta

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #119). Fuente
> canónica del alcance: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (PR #118, diseño aprobado). Este documento **no reabre** el contrato de datos `story_alerta`
> heredado del Change #109 (`.pulse/specs/stories-gi/spec.md`, R1-R10/CB-1..CB-8/AC1-AC9) — lo
> hereda y solo migra su **layout y viewport**. Resuelve las 7 preguntas abiertas de `idea.md`/
> `proposal.md` como requisitos verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Generalizar `scripts/story_render.py` (issue #109) para que deje de estar atado a un único
formato (9:16) y a una única plantilla (Alerta): viewport único **1920×1080**, tokens
escalares derivados dinámicamente del payload (no una lista fija por plantilla), un mecanismo
nuevo de repetición `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` y un catálogo cerrado de
helpers de derivación reutilizables — usando la migración de `templates/stories/alerta.html`
a un layout horizontal 16:9 como caso de prueba end-to-end de la generalización. Este Change
es el cimiento arquitectónico del que dependen las Fases B/C/D (11 plantillas restantes, cada
una su propio Change).

## Alcance IN/OUT

### IN
- Cambiar `render_png` (`scripts/story_render.py:168-211`, viewport hardcodeado en la línea 206)
  de `1080×1920` a **`1920×1080`** como único default — se elimina el 9:16, sin modo dual ni
  parámetro de tamaño.
- Reemplazar `_TOKENS_ESCALARES` (tupla fija, `scripts/story_render.py:33-46`) por un recorrido
  dinámico de las claves escalares top-level del payload en `build_context`.
- Nueva función `resolver_loops(html, payload)`: expande bloques
  `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` repitiendo su contenido interno una vez por objeto
  de `payload[clave]` (array), resolviendo los tokens propios de cada objeto en su iteración.
  Un solo nivel de anidamiento (ver R4 y "Preguntas abiertas — resueltas").
- Reordenar `build_html` (`scripts/story_render.py:153-165`) al orden canónico: **loops →
  fences → tokens → guardia** (hoy es fences → tokens → guardia).
- Conservar `_resolver_fences`/`_fence_presente`/`_validar_sin_huerfanos` en su lógica; solo
  cambia su posición relativa a `resolver_loops`.
- Fijar ya en esta Fase el catálogo cerrado de 4 helpers de derivación reutilizables
  (dirección→flecha, dirección/sesgo→color, impacto→badge, chart→URI), aunque hoy solo los
  primeros dos y el último tengan consumidor real en Alerta (ver R5).
- Migrar `templates/stories/alerta.html` (hoy 1080×1920, `templates/stories/alerta.html:48-65`)
  a un rediseño horizontal 1920×1080 que conserve el sistema visual GI (colores, tipografías,
  footer) y **los mismos nombres de tokens/fences** del contrato `story_alerta` vigente.
- Sincronizar 3 documentos que mencionan literalmente `1080×1920` o `9:16`: `CLAUDE.md:249` y
  `CLAUDE.md:322` (sección "Stories GI" y tabla de comandos), `.claude/commands/story.md:1`, y
  `docs/design/stories-gi/plantillas-stories-gi.md:32` (intro del catálogo de plantillas).
- Adaptar `tests/test_story_render.py` in-place: tokens dinámicos, `resolver_loops` (array
  vacío/1/N), assert de dimensiones `(1080, 1920)` → `(1920, 1080)`.

### OUT (explícitamente diferido — no se reabre)
- El contrato de payload específico de las 11 plantillas restantes (Fase B: `quote`,
  `breaking`, `encuesta`, `edu`; Fase C: `flash`, `calendario`, `semanal`, `earnings`; Fase D:
  `market`, `idea`, `macro`) — cada una su propio Change, según el plan de fases de la spec
  canónica (PR #118).
- Modo dual 9:16/16:9 o parámetro de tamaño en `render_png` — decisión ya tomada, no se discute.
- Anidamiento de `resolver_loops` (`FOR` dentro de `FOR`) — un solo nivel alcanza para el
  catálogo completo de las 12 plantillas (ninguna lo necesita); si una plantilla futura lo
  necesitara, es extensión de un Change aparte.
- Cambios al contrato de datos `story_alerta` (nombres de campos, tipos, obligatoriedad
  semántica) — solo cambian layout/viewport, no el payload que ya construye `story.md` PASO 5.
- `scripts/ruta_story.ps1` — confirmado sin cambios (ver "Preguntas abiertas — resueltas", Q8).
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles"
  (`.claude/shared/modo_ejecutivo.md:22`); no se reabre ese criterio en esta Fase.
- El PNG de `/chart` (`data/mt5_command.json`, EA `GI_ChartExporter`) — ya se genera en
  `1920×1080` (`.claude/commands/chart.md:61`); no requiere cambios (ver R6).
- Los 6 archivos ajenos al director (`.claude/commands/apertura.md`,
  `data/glosario_siglas.json`, `data/historial_encuestas.json`,
  `templates/encuesta_posicion.txt`, `templates/encuesta_tendencia.txt`, `uv.lock`) — fuera de
  alcance de este Change, no tocar.

## Requisitos funcionales

### R1 — Viewport único 1920×1080
`render_png` abre la página con `viewport={"width": 1920, "height": 1080}` como único valor
— sin parámetro de tamaño ni modo dual. El PNG resultante tiene esas dimensiones exactas
(IHDR). Mapea al punto 1 de la hipótesis de `idea.md`/`proposal.md`.

### R2 — Tokens escalares dinámicos derivados del payload
`build_context(payload)` recorre **todas** las claves escalares top-level del payload (valores
no-`dict`/no-`list`, incluidos `None`/booleanos/números convertidos a `str`) y las expone como
candidatas de sustitución `{{clave}}`, en vez de iterar `_TOKENS_ESCALARES` (lista fija,
obligatoria). Ya no existe una noción de "campo obligatorio del payload" a nivel de
`build_context`: si el HTML de la plantilla usa un `{{token}}` que el payload no provee (ni
como escalar ni como derivado de un helper), el error surge en la guardia
`_validar_sin_huerfanos` (fase 4 de `build_html`, post-sustitución) — mismo criterio fail-fast
que hoy, aplicado de forma genérica en vez de ad hoc por plantilla. Mapea al punto 2 de la
hipótesis y resuelve Q1.

### R3 — Claves del payload no usadas en el HTML: no-op silencioso
Si el payload trae una clave escalar que ninguna plantilla referencia como `{{clave}}`, esa
clave se calcula en el contexto pero simplemente no encuentra ocurrencia que sustituir en el
HTML — no es error, no se advierte, no se loguea. `build_context` no valida "¿esta clave se
usa en algún lado?"; solo la guardia posterior valida la dirección opuesta (¿quedó algún
`{{token}}` sin resolver?). Resuelve la segunda mitad de Q1.

### R4 — `resolver_loops`: expansión de bloques `<!-- FOR:clave -->`
Nueva función que:
1. Se ejecuta **antes** de `_resolver_fences` (orden canónico: loops → fences → tokens →
   guardia).
2. Para cada bloque `<!-- FOR:clave -->…<!-- ENDFOR:clave -->`, si `payload[clave]` es un
   array de N objetos, reemplaza el bloque completo por la concatenación de N repeticiones del
   contenido interno, sustituyendo dentro de cada repetición los tokens propios del objeto
   correspondiente (`{{campo}}` → `objeto[i]["campo"]`).
3. **Array vacío** (`payload[clave] == []`): el bloque se reemplaza por una cadena vacía (0
   repeticiones) — desaparece por completo, sin dejar contenido dentro de las marcas
   `FOR`/`ENDFOR`. Los contenedores/headers que deban persistir siempre (incluso sin filas)
   deben ubicarse en el HTML **fuera** de las marcas `<!-- FOR -->`/`<!-- ENDFOR -->` —
   convención documentada para las plantillas de Fase C (`flash`, `calendario`, `semanal`,
   `earnings`), que sí usan este mecanismo.
4. Soporta un único nivel: `resolver_loops` no resuelve un `<!-- FOR -->` anidado dentro de
   otro `<!-- FOR -->` (queda fuera de alcance explícito, ver OUT).
Mapea al punto 3 de la hipótesis y resuelve Q3/Q4.

### R5 — Catálogo cerrado de 4 helpers de derivación
Se fija ya en esta Fase el conjunto (más chico que "todas las claves") de nombres de clave
conocidos que disparan lógica propia en `build_context`, aunque no todos tengan consumidor
real en Alerta hoy:
1. **Flecha de dirección**: disparada por un objeto con clave `direccion` (ej. `variacion.
   direccion`) → deriva `<contenedor>_flecha` = `▲` (alcista) / `▼` (bajista) / `""` (otro
   valor). Consumidor real hoy: `variacion_flecha` en Alerta.
2. **Slug de color direccional**: disparada por `sesgo` o `variacion.direccion` → deriva
   `sesgo_slug` (prioriza `variacion.direccion` sobre `sesgo`, igual que hoy) para la clase CSS
   de color verde `#00DC82`/rojo `#E84040`. Consumidor real hoy: `sesgo_slug` en Alerta.
3. **Badge de impacto**: disparada por `impacto` (valores `alto`/`medio`, case-insensitive) →
   deriva `impacto_badge` (`ALTO`/`MEDIO` en mayúsculas). Sin consumidor real en Alerta; su
   primer consumidor será `calendario` (Fase C) — se fija el helper ahora para que Fase C no
   requiera tocar el motor.
4. **Chart embebido**: disparada por `chart_png` → deriva `chart_src` (URI `file:///`,
   validación de existencia — CB-8 se conserva sin cambios). Consumidor real hoy en Alerta.
Mapea al punto 2 de la hipótesis y resuelve Q2.

### R6 — Migración de `templates/stories/alerta.html` a 1920×1080
El snapshot se redimensiona a horizontal (`html, body { width: 1920px; height: 1080px; }` y
`.story` equivalente), reorganizando el layout existente (chips, titular, párrafo, tarjeta de
precio con borde rojo, stats soporte/resistencia/vol, bloque de gráfico, footer) en una
composición horizontal que conserve el sistema visual GI (paleta, tipografías Syne/DM
Sans/Space Grotesk, footer estándar). **Los nombres de tokens y fences no cambian**
(`{{titular}}`, `{{soporte}}`, `<!-- IF:variacion -->`, etc. — mismo contrato `story_alerta`).
El PNG que embebe `chart_png` (generado por `/chart`, ya en `1920×1080` según
`.claude/commands/chart.md:61`) encaja nativamente en el nuevo viewport horizontal — no
requiere recorte ni lógica nueva; el ajuste visual fino, si hace falta, se resuelve con
`object-fit` en el CSS del snapshot (mismo mecanismo que hoy usa `#img-alerta`). Mapea al
punto 5 de la hipótesis y resuelve Q5.

### R7 — Sincronización de documentación
Actualizar las 3 referencias literales a `1080×1920`/9:16 identificadas por búsqueda
exhaustiva del repo (`rg` sobre `*.md`, excluidos `.pulse/changes/**` que son historial):
`CLAUDE.md:249` y `CLAUDE.md:322` (sección "Stories GI" + tabla de comandos Capa 2),
`.claude/commands/story.md:1` (descripción del comando), y
`docs/design/stories-gi/plantillas-stories-gi.md:32` (intro del catálogo de piezas del
canvas). Ningún otro `.md` del repo (README, `docs/architecture.md`,
`docs/commands-reference.md`, `docs/setup-guide.md`) menciona estas dimensiones — confirmado
por búsqueda, no requieren cambios. Resuelve Q7.

### R8 — Estrategia de migración de tests: reescritura in-place
`tests/test_story_render.py` se reescribe **in-place** (no conviven versiones paralelas 9:16 y
16:9): no existe modo dual que justifique mantener ambas, y el motor generalizado debe seguir
produciendo el contrato observable equivalente para Alerta. Concretamente:
- `test_build_html_contract` y `test_alerta_no_placeholders`/`test_alerta_chart_embebido`
  siguen validando el mismo contrato de tokens/fences de Alerta (sin cambios de aserciones de
  contenido, solo de layout implícito).
- `test_render_dimensiones_1080x1920` se renombra a `test_render_dimensiones_1920x1080` y su
  assert pasa de `(1080, 1920)` a `(1920, 1080)`.
- Se agregan tests puros nuevos de `resolver_loops` (array vacío, 1 elemento, N elementos),
  aislados con un fixture propio (no dependen de ninguna plantilla real de Fase B/C/D).
- `tests/fixtures/stories/fixture_template.html` **no necesita cambiar sus dimensiones**: es un
  HTML mínimo sin CSS de viewport (`build_html`/`resolver_loops` son puros y no dependen del
  tamaño — solo `render_png` usa el viewport). Se le pueden agregar bloques `<!-- FOR -->` para
  aislar el test de `resolver_loops` del snapshot de marca real, igual que ya aísla fences/
  tokens hoy.
Resuelve Q6.

## Casos borde

- **CB-1 (payload con clave no usada en el HTML)**: no-op silencioso, no es error (R3).
- **CB-2 (HTML usa un `{{token}}` sin origen en el payload ni en ningún helper)**: falla en la
  guardia `_validar_sin_huerfanos`, mismo mensaje accionable de hoy listando los huérfanos (R2).
- **CB-3 (`FOR` con array vacío)**: el bloque desaparece sin rastro; el header/contenedor que
  deba persistir se ubica fuera del bloque `FOR`/`ENDFOR` (R4).
- **CB-4 (`FOR` anidado)**: no soportado; si el HTML lo intentara, `resolver_loops` no lo
  resuelve (el `<!-- FOR -->` interno queda como texto literal y cae en la guardia si contiene
  tokens sin resolver) — comportamiento aceptado, no se implementa detección explícita en esta
  Fase (R4, OUT).
- **CB-5 (`impacto` con valor fuera de `alto`/`medio`)**: mismo criterio que hoy con
  `direccion` fuera de `alcista`/`bajista` — el helper no reconoce el valor y deriva cadena
  vacía o el propio valor sin badge (a definir en Design, no bloqueante para Specify).
- **CB-6 (`chart_png` con ruta inexistente)**: se conserva `StoryRenderError` accionable — sin
  cambios respecto al CB-8 heredado de `.pulse/specs/stories-gi/spec.md`.
- **CB-7 (Chromium ausente)**: se conserva el CB-7 heredado sin cambios (mensaje con
  `uv sync --extra stories && python -m playwright install chromium`).

## Criterios de aceptación

**AC1 — viewport y dimensiones exactas (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de ejemplo `story_alerta` (sin `variacion`, sin `vol_pct`, `chart_png: null`),
CUANDO se ejecuta `render_story` contra `templates/stories/alerta.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB.
_(Reemplaza AC3 del contrato heredado #109; mismo umbral de tamaño.)_

**AC2 — tokens dinámicos: payload con clave extra no usada (ejecutable, `pytest`)**
DADO un payload que incluye una clave escalar adicional que ninguna plantilla referencia (ej.
`"nota_interna": "solo para QA"`),
CUANDO se ejecuta `build_html` sobre un fixture mínimo,
ENTONCES el render se completa sin error y el HTML resultante no contiene `nota_interna` en
ninguna parte (no-op silencioso, R3/CB-1).

**AC3 — tokens dinámicos: HTML con token sin origen (ejecutable, `pytest`)**
DADO un fixture HTML con un `{{token_inventado}}` que no existe en el payload ni es derivado
de ningún helper conocido,
CUANDO se ejecuta `build_html`,
ENTONCES se lanza `StoryRenderError` mencionando `token_inventado` (guardia de huérfanos,
R2/CB-2). _(Ya cubierto en espíritu por `test_build_html_token_huerfano_lanza_error` existente
— se conserva.)_

**AC4 — `resolver_loops` con array vacío (ejecutable, `pytest`)**
DADO un payload `{"filas": []}` y un fixture con
`<!-- FOR:filas -->{{nombre}}<!-- ENDFOR:filas -->`,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado no contiene ninguna ocurrencia de `{{nombre}}` ni del contenido interno
del bloque, y las marcas `FOR`/`ENDFOR` desaparecen (R4/CB-3).

**AC5 — `resolver_loops` con 1 elemento (ejecutable, `pytest`)**
DADO un payload `{"filas": [{"nombre": "USD/CLP"}]}` y el mismo fixture,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado contiene exactamente una ocurrencia de `USD/CLP` y ninguna marca
`FOR`/`ENDFOR` ni `{{nombre}}` sin resolver (R4).

**AC6 — `resolver_loops` con N elementos (ejecutable, `pytest`)**
DADO un payload `{"filas": [{"nombre": "USD/CLP"}, {"nombre": "Oro"}, {"nombre": "WTI"}]}` y el
mismo fixture,
CUANDO se ejecuta `resolver_loops`,
ENTONCES el resultado contiene `USD/CLP`, `Oro` y `WTI`, en ese orden, cada uno exactamente una
vez, y ninguna marca `FOR`/`ENDFOR` sin resolver (R4).

**AC7 — helper de badge de impacto disponible aunque sin consumidor en Alerta (ejecutable,
`pytest`)**
DADO un payload con `"impacto": "alto"` y un fixture con `{{impacto_badge}}`,
CUANDO se ejecuta `build_context`,
ENTONCES el contexto resultante contiene `impacto_badge == "ALTO"` (R5, helper 3 fijado ya en
esta Fase).

**AC8 — orden canónico `loops → fences → tokens → guardia` (ejecutable, `pytest`)**
DADO un fixture que combina un bloque `<!-- FOR:filas -->` que a su vez contiene un fence
`<!-- IF:x -->` interno a cada fila,
CUANDO se ejecuta `build_html`,
ENTONCES el resultado resuelve primero el `FOR` (produciendo N copias del fence interno) y
luego cada fence según los datos de su propia fila — verificable inspeccionando que el fence se
evalúa **por elemento**, no una sola vez sobre el payload completo (R4).

**AC9 — contrato de Alerta preservado tras la migración (ejecutable, `pytest`)**
DADO el payload de ejemplo `story_alerta` (mismo de AC1, más la variante con `chart_png`
apuntando a un fixture existente),
CUANDO se ejecuta `build_html` contra el `templates/stories/alerta.html` migrado,
ENTONCES el HTML contiene `titular`, `parrafo`, `precio_actual`, `soporte`, `resistencia` y
`tag_riesgo` correctamente inyectados, NO contiene placeholders sin resolver, omite los slots
de variación/volumen cuando el payload no los trae, y el chart embebido/SVG decorativo se
comporta exactamente igual que hoy (AC2/AC9 heredados de `.pulse/specs/stories-gi/spec.md`,
sin regresión).

**AC10 — sincronización de documentación (estructural, `rg`)**
`rg "1080.?1920" CLAUDE.md '.claude/commands/story.md' 'docs/design/stories-gi/plantillas-stories-gi.md'`
→ 0 matches (todas las referencias migradas a `1920×1080`); `rg "1920.?1080" CLAUDE.md` → ≥2
matches (línea de la sección "Stories GI" y la fila de `/story` en la tabla de comandos).

**AC11 — `resolver_loops` no soporta anidamiento, documentado (estructural)**
El docstring/comentario de `resolver_loops` en `scripts/story_render.py` menciona
explícitamente "un solo nivel" o equivalente — verificable con
`rg -i "nivel" scripts/story_render.py` ≥1 match tras la implementación (Design/Apply).
_(Criterio de documentación, no de comportamiento — el comportamiento lo cubre AC4-AC6.)_

**AC12 — sin regresión en `ruta_story.ps1` (estructural, `rg`)**
`git diff master -- scripts/ruta_story.ps1` (o equivalente al cerrar el Change) no muestra
cambios — confirma que Q8 se resolvió sin tocar el helper.

## Riesgos

- **Riesgo A — fidelidad visual del rediseño horizontal**: migrar el layout vertical de Alerta
  a horizontal implica reorganizar densidad de información (chips, titular, tarjeta, gráfico,
  footer) en un viewport más ancho y más bajo; no hay "golden PNG" de referencia del canvas
  para 16:9 de esta plantilla específica (el canvas expone el maestro en 4 tamaños, pero el
  snapshot de este repo se autora localmente). Mitigación: aprobación visual manual del
  director en la primera corrida real, igual que el piloto #109 (sin comparación pixel-a-pixel
  automatizada, ya aceptado como riesgo residual R-2 en el contrato heredado).
- **Riesgo B — helpers "adelantados" sin consumidor (badge de impacto)**: fijar el helper de
  `impacto` ya en esta Fase, sin que Alerta lo use, implica testear una pieza sin caso de uso
  real hasta Fase C. Mitigación: AC7 lo cubre con un fixture aislado (no depende de una
  plantilla real), y el criterio ya está explícitamente decidido por el director (ver
  "Decisiones ya tomadas" del prompt de este Change) — no es una apuesta especulativa del
  agente.
- **Riesgo C — deriva de `build_context` sin lista fija**: al eliminar la validación de
  "campos obligatorios" (`_TOKENS_ESCALARES` fijo), un payload incompleto para Alerta ya no
  falla temprano en `build_context` con un mensaje "campo ausente: X" — falla más tarde, en la
  guardia de huérfanos, con un mensaje distinto (lista de tokens sin resolver en el HTML, no de
  claves del payload). Mitigación: el mensaje de la guardia ya es accionable (lista los
  nombres de token exactos); documentar el cambio de comportamiento en el docstring de
  `build_context` para que quien depure no busque el mensaje antiguo.

## Preguntas abiertas — resueltas

Las 7 preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Alcance de tokens dinámicos** → R2/R3: se recorren *todas* las claves escalares del
   payload; una clave del payload no usada en el HTML es no-op silencioso (R3/CB-1); un
   `{{token}}` del HTML sin origen en el payload sigue siendo error vía la guardia (R2/CB-2).
2. **Lista de helpers especiales** → R5: se fija ya el catálogo cerrado de 4 (flecha, color,
   badge de impacto, chart), aunque el badge de impacto no tenga consumidor real hasta Fase C.
3. **Anidamiento de `resolver_loops`** → R4: un solo nivel; anidamiento explícitamente fuera de
   alcance (OUT, CB-4).
4. **Array vacío en `FOR`** → R4/CB-3: el bloque desaparece por completo (0 repeticiones);
   contenedores persistentes van fuera de las marcas `FOR`/`ENDFOR`.
5. **Aspect ratio del chart embebido** → R6: sin cambio de contrato; `/chart` ya genera PNG en
   `1920×1080` (`.claude/commands/chart.md:61`), por lo que el nuevo viewport horizontal calza
   nativamente — ajuste fino, si hiciera falta, vía `object-fit` en CSS, no en Python.
6. **Estrategia de migración de tests** → R8: reescritura in-place (no hay versiones
   paralelas); `fixture_template.html` no necesita cambiar dimensiones porque `build_html`/
   `resolver_loops` son puros y no dependen del viewport.
7. **Alcance de "sincronizar docs"** → R7: exactamente 3 archivos (`CLAUDE.md` ×2 líneas,
   `story.md`, `plantillas-stories-gi.md`); confirmado por búsqueda exhaustiva que ningún otro
   `.md` del repo menciona estas dimensiones.
8. **`scripts/ruta_story.ps1`** → confirmado sin cambios (AC12): el helper ya es agnóstico al
   tamaño/aspecto de la imagen, solo arma la ruta por fecha/activo/plantilla/hora.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec/diseño
  aprobado (PR #118), fuente canónica del alcance de esta Fase A.
- `docs/design/stories-gi/plantillas-stories-gi.md:32` — línea a sincronizar (R7).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  R1-R10/CB-1..CB-8/AC1-AC9), no se reabre salvo AC3 (dimensiones) y AC2/AC9 (verificación de
  no-regresión, ver AC1/AC9 de este documento).
- `.pulse/changes/archive/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/design.md`
  — decisiones D1-D7 heredadas (mecanismo de inyección, estructura de `story_render.py`).
- `scripts/story_render.py:29-46,58-68,71-116,119-165,168-221` — motor actual a generalizar.
- `templates/stories/alerta.html:48-65` — snapshot 9:16 a migrar.
- `.claude/commands/story.md:1` — comando a sincronizar.
- `CLAUDE.md:249,322` — sección "Stories GI" y tabla de comandos a sincronizar.
- `.claude/commands/chart.md:61` — confirma que `/chart` ya genera PNG en `1920×1080` (R6).
- `.claude/shared/modo_ejecutivo.md:22` — confirma `/story` en "No elegibles", sin cambios.
- `tests/test_story_render.py` + `tests/fixtures/stories/` — suite a extender in-place (R8).
- `scripts/ruta_story.ps1` — helper de guardado, confirmado sin cambios (AC12).
- `idea.md`, `proposal.md` de este mismo Change #119 — base de este documento.
- Issue #119 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase A.
