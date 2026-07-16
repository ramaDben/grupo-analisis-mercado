
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

<!-- change:121-stories-gi-fase-b-plantilla-quote-16-9 -->
# Specification: Stories GI · Fase B — plantilla Quote 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #121). Fuente
> canónica del contrato de `quote`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 10, líneas 55-110). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo. Resuelve las preguntas abiertas
> de `idea.md`/`proposal.md` como requisitos verificables (sección "Preguntas abiertas —
> resueltas").

## Objetivo

Agregar la plantilla **`quote`** (#10 del catálogo GI) al comando `/story`: una pieza
100% editorial — cita + autor + cargo, sin gráfico, sin listas, sin dato del motor —
consumiendo el motor genérico de Fase A (`scripts/story_render.py`) tal cual quedó, sin
tocarlo. Sirve además como primer caso de prueba del motor sin fences `IF` ni loops `FOR`.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/quote.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, paleta oscura, footer
  `@grupointeligencia` + disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-50`),
  layout centrado sin chips de categoría ni bloque de gráfico/datos numéricos. Tokens
  escalares simples `{{cita}}`, `{{autor}}`, `{{autor_sub}}` — **sin fences `IF`/`FOR`**.
- Nuevo `[tipo]` `quote` en `.claude/commands/story.md` PASO 0 (lista dura hoy solo
  `alerta`, `.claude/commands/story.md:6-8,19-27`) + nuevo bloque de recolección editorial
  (el director dicta la cita o aprueba una redactada por el modelo). Reusa el flujo
  existente (preview → aprobación → render → `ruta_story.ps1 -Plantilla "quote"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `quote.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo el caso
  `autor_sub == ""`. Sin fixture nuevo en `tests/fixtures/stories/`, sin tocar
  `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy dice "único `[tipo]` soportado hoy: `alerta`") para incluir `quote`, sin tocar el
  resto de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `quote`.
- El contrato de payload de `alerta` — sin cambios.
- Las demás plantillas de Fase B (`breaking`, `encuesta`, `edu`) — cada una su propio
  Change (convención "1 plantilla = 1 Change" heredada de Fase A).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` genérico, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fence `<!-- IF:autor_sub -->` — el motor solo resuelve fences top-level para la
  tupla fija `_FENCES` (4 nombres de Alerta); agregar `autor_sub` a ese mecanismo
  requeriría tocar el motor, fuera de alcance. `quote.html` no usa fences.
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `quote` es 100% editorial manual, sin comando fuente de recolección de datos.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin
  cambios a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/quote.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, paleta oscura `#0D0D1A`, footer estándar) sin chips de categoría ni
bloque de gráfico/datos numéricos. Cuerpo central: comillas decorativas (CSS/SVG
estático, no token) + `{{cita}}` + atribución (`{{autor}}`, `{{autor_sub}}`). Mapea al
punto 1 de la hipótesis.

### R2 — Contrato de payload `story_quote`
```json
{
  "plantilla": "quote",
  "cita": "El mercado premia la paciencia más que la predicción.",
  "autor": "Nombre Analista",
  "autor_sub": "Head of Trading, Grupo Inteligencia"
}
```
- `cita`, `autor`, `autor_sub` son las únicas claves del payload (sin campos array, sin
  `chart_png`, sin dato del motor).
- `autor_sub` es un token **siempre presente** en el payload (nunca ausente/`None`) que
  admite string vacío `""` — resuelve Q2 (no hace falta fence).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `quote`.

### R3 — Sin fences `IF`/`FOR` en `quote.html`
`quote.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`. Justificación
(confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences top-level de
`_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de Alerta); el
fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un bloque
`FOR`, que `quote` no usa (sin arrays). Por tanto ningún campo de `quote` puede
condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens de
`quote` son escalares incondicionales. Resuelve Q2.

### R4 — Colapso visual de `autor_sub` vacío (CSS, no motor)
Cuando `autor_sub == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano,
no hay error de guardia. El contenedor HTML del token `autor_sub` (ej.
`<p class="quote-cargo">{{autor_sub}}</p>`) usa la regla CSS `:empty { display: none; }`
sobre ese contenedor, de forma que:
- Con `autor_sub` no vacío: se muestra la línea de cargo bajo `autor`.
- Con `autor_sub == ""`: el contenedor no ocupa espacio (colapsa `display: none`, no
  solo el texto) — el bloque de atribución (`autor` + `autor_sub`) permanece centrado
  sin hueco en blanco. Resuelve Q3/Q5 (colapso de espaciado, no solo de texto).

### R5 — Límite editorial de longitud de `cita`
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), un límite recomendado de **≤ 220 caracteres** para `cita` —
análogo al límite de `parrafo` de Alerta (`≤ ~280 caracteres`, contrato heredado
`.pulse/specs/stories-gi/spec.md:154`) pero más corto porque `quote` se lee a un solo
tamaño de fuente grande sin bajada de apoyo. El comando ajusta la redacción antes del
preview si la cita excede el límite; el motor no valida longitud (mismo criterio que
Alerta: guardia solo valida tokens huérfanos, no longitud de contenido). Resuelve Q1/Q4.

### R6 — Tratamiento tipográfico de comillas
Las comillas decorativas que enmarcan la cita son un elemento gráfico **estático** del
snapshot (glifo CSS o SVG inline en `quote.html`, ej. `“ ”` como pseudo-elemento
`::before`/`::after` con tipografía Syne), **no** parte del valor de `{{cita}}` — el
payload nunca incluye comillas literales alrededor del texto (`cita` es el texto plano
de la cita, sin comillas propias). Resuelve la pregunta de tratamiento tipográfico de
comillas dejada abierta en `proposal.md`.

### R7 — Recolección editorial en `story.md`
`.claude/commands/story.md` PASO 0 agrega `quote` a la lista de `[tipo]` soportados
(junto a `alerta`). Nuevo bloque de recolección: el director dicta la cita
directamente, o el modelo redacta una propuesta con criterio editorial (ej. resumiendo
una idea de mercado de la semana) y el director la aprueba/ajusta antes del preview —
sin delegar en ningún comando fuente de datos de mercado (`/apertura`, `/dato_macro`,
etc.), a diferencia de `alerta`. Resuelve Q4.

### R8 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `alerta.html`:
1. Test de mapeo con `autor_sub` no vacío: `build_html` sobre `quote.html` con el
   payload de R2 produce HTML sin placeholders sin resolver, con `cita`/`autor`/
   `autor_sub` correctamente inyectados.
2. Test de mapeo con `autor_sub == ""`: mismo `build_html`, el HTML resultante no
   contiene ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se
   omitió el campo).
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `quote.html`, igual que `alerta.html`). Sin cambios en `conftest.py`.
Resuelve Q5 (de `idea.md`).

### R9 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la frase "único `[tipo]` soportado hoy: `alerta`"
se actualiza para reflejar que `quote` también está soportado (ej. "`[tipo]` soportados
hoy: `alerta`, `quote`"), sin tocar el resto del párrafo/sección.

## Casos borde

- **CB-1 (`autor_sub` ausente del payload, no `""`)**: el comando (PASO de recolección,
  R7) siempre construye el payload con la clave `autor_sub` presente, aunque sea `""`
  — nunca omite la clave. Si por error se omitiera, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que Alerta), no un
  colapso silencioso distinto al de R4.
- **CB-2 (`cita` supera el límite editorial de 220 caracteres)**: el comando ajusta la
  redacción antes del preview (R5); el motor no aborta ni trunca — no hay validación de
  longitud en `build_html`.
- **CB-3 (`cita` con comillas literales incluidas por error)**: criterio editorial del
  comando: la cita se recolecta sin comillas propias (R6); no es una validación del
  motor, es guía de redacción en `story.md`.
- **CB-4 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-5 (flag `ejecutivo`)**: `/story quote ejecutivo` avisa que `/story` no soporta el
  flag (mismo criterio ya vigente para `alerta`) y continúa generando la Story normal.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/quote.html` existe y contiene `width: 1920px` y `height: 1080px` (o
equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:48-49`.

**AC2 — sin fences en `quote.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/quote.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `autor_sub` no vacío (ejecutable, `pytest`)**
DADO el payload `{"cita": "...", "autor": "Nombre Analista", "autor_sub": "Head of
Trading, Grupo Inteligencia"}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/quote.html`,
ENTONCES el HTML resultante contiene el texto de `cita`, `autor` y `autor_sub`
correctamente inyectados y no contiene ningún placeholder `{{...}}` sin resolver (R2/R8).

**AC4 — colapso de `autor_sub` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"autor_sub": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/quote.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `autor_sub` en el CSS del snapshot
declara `:empty { display: none; }` sobre esa clase/selector (R4/R8) — verificable con
`rg ":empty" templates/stories/quote.html` ≥1 match.

**AC5 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story` o equivalente) contra
`templates/stories/quote.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A).

**AC6 — comillas decorativas no vienen del payload (estructural, `rg`)**
`rg "❝|❞|“|”|::before|::after" templates/stories/quote.html` tiene al menos 1 match
asociado al elemento decorativo de comillas en el CSS/HTML del snapshot, confirmando
que el glifo es estático y no un token sustituible (R6).

**AC7 — `[tipo]` `quote` registrado en el comando (estructural, `rg`)**
`rg "quote" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque de recolección editorial (R7).

**AC8 — límite editorial documentado (estructural, `rg`)**
`rg "220" .claude/commands/story.md` ≥1 match asociado al límite recomendado de
longitud de `cita` (R5).

**AC9 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "quote" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R9).

**AC10 — sin regresión del motor ni de Alerta (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
scripts/ruta_story.ps1` no muestra cambios — confirma que el motor, el snapshot de
Alerta y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `quote` en 16:9 (mismo riesgo residual R-2 heredado de
  Fase A/#109). Mitigación: aprobación visual manual del director en la primera corrida
  real de `/story quote`.
- **Riesgo B — límite de 220 caracteres es una estimación editorial, no verificada
  visualmente contra el manual de marca**: si el layout final desborda con citas más
  cortas o admite más largas, el valor se ajusta en `apply` durante la autoría del CSS
  real — no bloquea `specify` (mismo criterio que Fase A dejó el detalle CSS fino para
  `apply`).

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Límite de longitud de `cita`** → R5: 220 caracteres recomendados, criterio
   editorial del comando, sin validación en el motor (CB-2).
2. **`autor_sub` siempre presente vs. puede faltar / necesita fence** → R2/R3: siempre
   presente en el payload (admite `""`), sin fence `IF:autor_sub` — el motor no lo
   soporta a nivel top-level sin tocarlo (decisión firme heredada del `proposal.md`).
3. **Colapso de espaciado con `autor_sub` vacío** → R4: `:empty { display: none; }`
   colapsa también el espacio vertical, no solo el texto.
4. **Origen del texto de la cita (dictado vs. redactado por el modelo)** → R7: ambas
   vías soportadas en el bloque de recolección de `story.md` — el director dicta o
   aprueba una propuesta del modelo.
5. **Fixture propio para el test de mapeo** → R8: no hace falta; se reusa el patrón de
   test contra el snapshot real `quote.html`, igual que `alerta.html`.
6. **Tratamiento tipográfico de comillas** → R6: elemento decorativo estático del
   snapshot (CSS/SVG), nunca parte del valor de `{{cita}}`.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 10
  `quote` (líneas 55-110): payload `cita, autor, autor_sub`, sin gráfico, fondo oscuro,
  fuente "editorial manual".
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`),
  límite de longitud de `parrafo` (línea 154) usado como referencia análoga para R5.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde de este documento y contrato del motor generalizado (R1-R8, AC1-AC12).
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-50` — única plantilla 16:9 existente, referencia de
  esqueleto/paleta/fuentes para autorar `quote.html`.
- `.claude/commands/story.md:1-27` — comando a extender (PASO 0: agregar `quote` a
  `[tipo]`; nuevo bloque de recolección editorial).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `quote`.
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #121 — base de este documento.
- Issue #121 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B.

<!-- change:123-stories-gi-fase-b-plantilla-breaking-16-9 -->
# Specification: Stories GI · Fase B — plantilla Breaking 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #123). Fuente
> canónica del contrato de `breaking`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 12, línea 70). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo, y el patrón de campo opcional
> (token + `:empty`) validado en Fase B/`quote` (`.pulse/changes/archive/121-.../spec.md`) sin
> reabrirlo. Resuelve las preguntas abiertas de `idea.md`/`proposal.md` como requisitos
> verificables (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`breaking`** (#12 del catálogo GI) al comando `/story`: una pieza de
última hora con cifra (kicker + titular + valor + contexto + reacción), fondo oscuro/rojo, sin
gráfico y sin listas, alimentada por el criterio editorial de `/noticia` · `/alerta` — a
diferencia de `quote` (100% editorial manual, sin fuente de mercado ni de noticia) y de `alerta`
(que sí trae datos en vivo de `get_asset_levels`). Consume el motor genérico de Fase A
(`scripts/story_render.py`) tal cual quedó, sin tocarlo.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/breaking.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` +
  disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-58`), paleta
  oscura/rojiza reutilizando verbatim el degradado de fondo de `alerta.html:51-54`
  (`#0D0D1A` base, radial `#2A1220`→`#0D0D1A`) más los acentos rojos `#E84040` de
  `alerta.html` (chip/tag, borde de tarjeta, líneas SVG) aplicados al chip `kicker_tema` y
  a la tarjeta de `valor` — sin tarjeta de precio completa (sin variación %, sin
  soporte/resistencia/vol, sin gráfico). Tokens escalares `{{kicker_tema}}`,
  `{{titular}}`, `{{valor}}`, `{{contexto}}`, `{{parrafo_reaccion}}` — **sin fences
  `IF`/`FOR`**.
- Nuevo `[tipo]` `breaking` en `.claude/commands/story.md` PASO 0 (lista dura hoy
  `alerta`, `quote`) + nuevo bloque "Ruta `breaking`" — recolección editorial que
  **no ejecuta búsqueda propia de evento** (no reusa el WebSearch de `/alerta` PASO 1):
  estructura la cifra/evento que el director ya dictó o que ya salió de una corrida
  previa de `/noticia`/`/alerta` en la misma sesión. Reusa el flujo existente (preview →
  aprobación → render → `ruta_story.ps1 -Plantilla "breaking"`), con `-Activo` opcional
  según decisión editorial del director (ver R8).
- Tests de mapeo puros en `tests/test_story_render.py` para `breaking.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo el caso
  `kicker_tema == ""`. Sin fixture nuevo en `tests/fixtures/stories/`, sin tocar
  `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy `alerta`, `quote`) para incluir `breaking`, sin tocar el resto de la sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `breaking`.
- El contrato de payload de `alerta` y de `quote` — sin cambios.
- Las demás plantillas de Fase B (`encuesta`, `edu`) — cada una su propio Change
  (convención "1 plantilla = 1 Change" heredada de Fase A/B).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fence `<!-- IF:kicker_tema -->` — el motor solo resuelve fences top-level para la
  tupla fija `_FENCES` (4 nombres de Alerta); agregar `kicker_tema` a ese mecanismo
  requeriría tocar el motor, fuera de alcance. `breaking.html` no usa fences (mismo
  criterio que `quote`).
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `breaking` no delega en ningún dato en vivo del motor; `valor` es la cifra
  editorial de la noticia, no un precio de mercado.
- Búsqueda propia de evento/noticia dentro de `story.md` — `breaking` no reusa el
  mecanismo WebSearch de `/alerta` PASO 1; estructura lo que el director ya tiene (R7).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo
  campo-por-campo dedicada a `breaking` en este Change (decisión firme del `proposal.md`,
  punto 7 de la hipótesis); el contrato de campos vive en el design doc de 2026-07-14
  (fila 12) y en este `spec.md`.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin cambios
  a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/breaking.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, degradado de fondo `alerta.html:51-54`, footer estándar). Cuerpo:
chip `{{kicker_tema}}` (etiqueta de categoría/tema, acento rojo `#E84040`, mismo
tratamiento visual que el chip de categoría de `alerta.html`) + `{{titular}}` (tipografía
Syne, mismo peso jerárquico que el titular de Alerta) + tarjeta de `{{valor}}` con
rotulado fijo **"CIFRA CLAVE"** (texto estático del snapshot, no token) y borde/acento
rojo `#E84040` (mismo color que `.tarjeta-precio` de Alerta, pero sin variación %, sin
soporte/resistencia, sin vol — layout deliberadamente distinto al de la tarjeta de
precio, para no sugerir un dato en vivo del motor) + `{{contexto}}` (línea secundaria de
apoyo bajo la cifra) + `{{parrafo_reaccion}}` (párrafo de cierre, tipografía DM Sans).
Sin gráfico, sin chips de gráfico, sin fences `IF`/`FOR` — todos los tokens escalares
incondicionales (mismo criterio que `quote`, confirmado por la tupla fija `_FENCES` que
no cubre ningún campo de `breaking`). Mapea al punto 1 de la hipótesis.

### R2 — Contrato de payload `story_breaking`
```json
{
  "plantilla": "breaking",
  "kicker_tema": "BANCOS CENTRALES",
  "titular": "La Fed sorprende con una pausa más larga de lo esperado",
  "valor": "5,50%",
  "contexto": "Tasa de referencia sin cambios por tercera reunión consecutiva",
  "parrafo_reaccion": "El mercado ajusta expectativas hacia un primer recorte más tardío, presionando al dólar al alza y a los activos de riesgo a la baja en la sesión."
}
```
- `kicker_tema`, `titular`, `valor`, `contexto`, `parrafo_reaccion` son las únicas claves
  del payload (sin campos array, sin `chart_png`, sin dato del motor).
- `kicker_tema` es un token **siempre presente** en el payload (nunca ausente/`None`)
  que admite string vacío `""` — es el único campo opcional del contrato (resuelve la
  pregunta abierta 1 de `idea.md`/`proposal.md`: el candidato es `kicker_tema`, cuando la
  noticia no cae en una categoría editorial clara).
- `titular`, `valor`, `contexto` y `parrafo_reaccion` son siempre no vacíos — el comando
  (R7) nunca construye el payload con alguno de estos cuatro campos como `""`; si el
  director no puede dar contexto o reacción, el comando insiste o usa una redacción
  editorial mínima, nunca cadena vacía en estos cuatro.
- `valor` es la cifra editorial de la noticia (dato macro, porcentaje, nivel mencionado
  en la nota) — **no** un precio en vivo del motor; no lleva formateo `digits` de
  `config/activos.json` (eso es exclusivo de precios de activos vía `get_asset_levels`).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `breaking`.

### R3 — Sin fences `IF`/`FOR` en `breaking.html`
`breaking.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`.
Justificación (confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences
top-level de `_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de
Alerta); el fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un
bloque `FOR`, que `breaking` no usa (sin arrays). Por tanto ningún campo de `breaking`
puede condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens
son escalares incondicionales, y el único campo opcional (`kicker_tema`) se resuelve vía
CSS (R4), no vía fence. Mismo criterio que `quote` R3.

### R4 — Colapso visual de `kicker_tema` vacío (CSS, no motor)
Cuando `kicker_tema == ""`, el token se sustituye igual (cadena vacía) — no hay huérfano,
no hay error de guardia. El contenedor HTML del token `kicker_tema` (ej.
`<span class="breaking-kicker">{{kicker_tema}}</span>`) usa la regla CSS
`:empty { display: none; }` sobre ese contenedor, de forma que:
- Con `kicker_tema` no vacío: se muestra el chip sobre el titular.
- Con `kicker_tema == ""`: el contenedor no ocupa espacio (colapsa `display: none`, no
  solo el texto) — el titular sube sin hueco en blanco donde estaría el chip. Mismo
  patrón exacto validado en `quote` R4 (`.quote-cargo:empty`).

### R5 — Rotulado fijo de `valor` (distinción de un precio de mercado)
La tarjeta de `{{valor}}` en `breaking.html` incluye la etiqueta estática **"CIFRA
CLAVE"** (texto fijo del snapshot, no un token) inmediatamente junto al valor, y omite
deliberadamente todo elemento visual asociado a un dato de mercado en vivo: sin flecha de
variación (▲/▼), sin color verde/rojo condicional por dirección, sin fila de
soporte/resistencia/vol, sin rótulo de ticker/activo. Resuelve la pregunta abierta 3 de
`idea.md`/`proposal.md` (tratamiento tipográfico/rotulado de `valor` que lo distinga de
un precio del motor).

### R6 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), los límites recomendados:
- `kicker_tema` ≤ 30 caracteres (chip corto, una sola línea).
- `titular` ≤ 70 caracteres (mismo límite que `titular` de Alerta,
  `.pulse/specs/stories-gi/spec.md:154`).
- `contexto` ≤ 100 caracteres (línea secundaria de apoyo bajo la cifra, más corta que un
  párrafo).
- `parrafo_reaccion` ≤ 280 caracteres (mismo límite que `parrafo` de Alerta).
El comando ajusta la redacción antes del preview si algún campo excede su límite; el
motor no valida longitud (mismo criterio que Alerta/`quote`: la guardia solo valida
tokens huérfanos, no longitud de contenido).

### R7 — Recolección editorial en `story.md` sin búsqueda propia de evento
`.claude/commands/story.md` PASO 0 agrega `breaking` a la lista de `[tipo]` soportados
(junto a `alerta`, `quote`). Nuevo bloque "Ruta `breaking`":
1. Pregunta si el director ya corrió `/noticia` o `/alerta` en la misma sesión (o tiene
   ya redactado el evento/cifra) — de ser así, reutiliza esos textos como base editorial.
   Si no, pide al director que dicte directamente `kicker_tema` (opcional), `titular`,
   `valor`, `contexto` y `parrafo_reaccion`.
2. **`breaking` no ejecuta su propia búsqueda de evento** (no invoca WebSearch ni el
   mecanismo de detección de `/alerta` PASO 1) — estructura y valida lo que el director
   ya tiene, sin investigar por cuenta propia. Resuelve la pregunta abierta 4 de
   `idea.md`/proposal.md (decisión firme del `proposal.md`, punto 3 de la hipótesis).
3. Dirección explícita obligatoria (regla de oro del repo): el titular/contexto/reacción
   deben dejar clara la lectura direccional del evento (ej. qué activo o mercado se ve
   afectado y hacia dónde), con registro profesional del repo (énfasis sin
   dramatización, `CLAUDE.md` "Registro y tono").
4. Construye el payload con `kicker_tema` **siempre presente** — si el director no da un
   tema/categoría claro, `"kicker_tema": ""` (nunca omitir la clave).

### R8 — Guardado con o sin `-Activo` (decisión editorial)
A diferencia de `quote` (siempre `_general`), el bloque "Ruta `breaking`" de `story.md`
pregunta al director si la noticia tiene un activo protagonista claro (ej. un dato de la
Fed que mueve XAUUSD):
- **Si lo tiene**: pasa `-Activo [TICKER_MT5]` a `ruta_story.ps1` (normalizado contra
  `config/activos.json`, mismo criterio que `/chart` PASO 1).
- **Si no lo tiene** (cifra macro sin activo protagonista único, ej. IPC general): se
  guarda bajo `-Activo "_general"`, igual que `quote`.
El criterio de decisión es editorial (lo decide el director al responder la pregunta),
no una regla automática nueva del motor ni de `ruta_story.ps1`. Resuelve la pregunta
abierta 5 de `idea.md`/proposal.md (decisión firme del `proposal.md`, punto 4 de la
hipótesis).

### R9 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `quote.html`:
1. Test de mapeo con `kicker_tema` no vacío: `build_html` sobre `breaking.html` con el
   payload de R2 produce HTML sin placeholders sin resolver, con `kicker_tema`,
   `titular`, `valor`, `contexto` y `parrafo_reaccion` correctamente inyectados.
2. Test de mapeo con `kicker_tema == ""`: mismo `build_html`, el HTML resultante no
   contiene ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se
   omitió el campo).
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `breaking.html`, igual que `quote.html`/`alerta.html`). Sin cambios en
`conftest.py`.

### R10 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza
para incluir `breaking` junto a `alerta` y `quote` (ej. "`[tipo]` soportados hoy:
`alerta`, `quote`, `breaking`"), sin tocar el resto del párrafo/sección.

## Casos borde

- **CB-1 (`kicker_tema` ausente del payload, no `""`)**: el comando (PASO de
  recolección, R7) siempre construye el payload con la clave `kicker_tema` presente,
  aunque sea `""` — nunca omite la clave. Si por error se omitiera, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que Alerta/`quote`), no
  un colapso silencioso distinto al de R4.
- **CB-2 (algún campo de longitud excede el límite editorial de R6)**: el comando ajusta
  la redacción antes del preview; el motor no aborta ni trunca — no hay validación de
  longitud en `build_html`.
- **CB-3 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-4 (flag `ejecutivo`)**: `/story breaking ejecutivo` avisa que `/story` no soporta
  el flag (mismo criterio ya vigente para `alerta`/`quote`) y continúa generando la Story
  normal.
- **CB-5 (director no tiene corrida previa de `/noticia`/`/alerta` ni evento claro)**: el
  comando pide que dicte directamente los 5 campos; no bloquea ni exige una corrida
  previa de otro comando (R7 no es una dependencia dura, solo un atajo si ya existe el
  texto).
- **CB-6 (`valor` sin unidad clara, ej. solo un número)**: criterio editorial del
  comando: `valor` se recolecta como texto ya formateado con su unidad si aplica (ej.
  `"5,50%"`, `"US$ 2.318"`) — no es una validación del motor, es guía de redacción en
  `story.md` (mismo criterio que R6 de `quote` para comillas).
- **CB-7 (activo protagonista ambiguo o con múltiples activos afectados)**: el director
  decide, al responder la pregunta de R8, si hay un activo protagonista único; si no lo
  hay con claridad, se guarda bajo `_general` (mismo criterio que `quote`).

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/breaking.html` existe y contiene `width: 1920px` y `height: 1080px`
(o equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:49-50`.

**AC2 — sin fences en `breaking.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/breaking.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `kicker_tema` no vacío (ejecutable, `pytest`)**
DADO el payload `{"kicker_tema": "BANCOS CENTRALES", "titular": "La Fed sorprende con una
pausa más larga de lo esperado", "valor": "5,50%", "contexto": "Tasa de referencia sin
cambios por tercera reunión consecutiva", "parrafo_reaccion": "El mercado ajusta
expectativas hacia un primer recorte más tardío, presionando al dólar al alza y a los
activos de riesgo a la baja en la sesión."}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/breaking.html`,
ENTONCES el HTML resultante contiene el texto de `kicker_tema`, `titular`, `valor`,
`contexto` y `parrafo_reaccion` correctamente inyectados y no contiene ningún
placeholder `{{...}}` sin resolver (R2/R9).

**AC4 — colapso de `kicker_tema` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker_tema": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/breaking.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `kicker_tema` en el CSS del snapshot
declara `:empty { display: none; }` sobre esa clase/selector (R4/R9) — verificable con
`rg ":empty" templates/stories/breaking.html` ≥1 match.

**AC5 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story`) contra
`templates/stories/breaking.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A / AC5 de `quote`).

**AC6 — rotulado fijo "CIFRA CLAVE" y sin elementos de precio en vivo (estructural, `rg`)**
`rg -i "CIFRA CLAVE" templates/stories/breaking.html` ≥1 match (texto estático, R5);
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/breaking.html`
→ 0 matches (confirma que `breaking.html` no reutiliza el layout de tarjeta de precio de
Alerta ni sus tokens).

**AC7 — `[tipo]` `breaking` registrado en el comando (estructural, `rg`)**
`rg "breaking" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque "Ruta `breaking`" (R7).

**AC8 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?70|≤ ?100|≤ ?280|≤ ?30" .claude/commands/story.md` ≥1 match asociado a los
límites recomendados de `titular`/`contexto`/`parrafo_reaccion`/`kicker_tema` (R6).

**AC9 — `story.md` documenta que `breaking` no busca su propio evento (estructural, `rg`)**
`rg -i "no ejecuta su propia búsqueda|no busca por cuenta propia|no reusa" .claude/commands/story.md`
≥1 match dentro del bloque "Ruta `breaking`" (R7, decisión firme del `proposal.md`).

**AC10 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "breaking" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R10).

**AC11 — sin regresión del motor ni de Alerta/`quote` (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html scripts/ruta_story.ps1` no muestra cambios — confirma que
el motor, los snapshots existentes y el helper de guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `breaking` en 16:9 (mismo riesgo residual R-2 heredado
  de Fase A/#109 y de `quote`/#121). Mitigación: aprobación visual manual del director en
  la primera corrida real de `/story breaking`.
- **Riesgo B — rotulado "CIFRA CLAVE" es una decisión editorial de este documento, no
  verificada visualmente contra el manual de marca**: si el layout final necesita otro
  texto/tratamiento, el copy se ajusta en `apply` durante la autoría del CSS real — no
  bloquea `specify` (mismo criterio que Fase A/`quote` dejaron el detalle CSS fino para
  `apply`).
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir
  golden PNG, los límites exactos en caracteres pueden requerir ajuste tras la primera
  corrida visual real; se documentan como guía editorial del comando, no como
  validación dura del motor (mismo criterio que Riesgo B de `quote`).

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **¿Qué campo(s) activan el patrón "token + `:empty`"?** → R2/R4: único campo
   opcional es `kicker_tema` (siempre presente, admite `""`); `titular`, `valor`,
   `contexto` y `parrafo_reaccion` son siempre no vacíos en el payload construido por
   el comando.
2. **Documentación de mapeo campo-por-campo en `plantillas-stories-gi.md`** → fuera de
   alcance de este Change (ver "OUT"), decisión firme heredada del `proposal.md`.
3. **Tratamiento tipográfico/rotulado de `valor` vs. precio de mercado** → R5: etiqueta
   estática "CIFRA CLAVE" junto al valor; sin flecha de variación, sin color
   condicional por dirección, sin fila de soporte/resistencia/vol.
4. **¿El bloque "Ruta `breaking`" reusa el WebSearch de `/alerta` PASO 1?** → R7: no —
   estructura lo que el director ya dictó o ya generó con `/noticia`/`/alerta` en la
   misma sesión; no investiga por cuenta propia.
5. **¿`breaking` se guarda con o sin `-Activo`?** → R8: ambos caminos soportados,
   decisión editorial del director al responder la pregunta de recolección; sin activo
   protagonista claro → `_general` (mismo criterio que `quote`).

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 12
  `breaking` (línea 70): payload `kicker_tema, titular, valor, contexto,
  parrafo_reaccion`, sin gráfico, fondo oscuro/rojo, fuente `/noticia` · `/alerta`.
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  `story_quote`); límite de longitud de `parrafo`/`titular` de Alerta usado como
  referencia análoga para R6.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde del motor generalizado (R1-R8, AC1-AC12), no se reabre.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/spec.md` — molde
  directo de este documento; patrón de campo opcional (token + `:empty`) validado y
  reutilizado sin cambios en R4.
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-58,108,145-202,363-391` — referencia de esqueleto,
  degradado de fondo y acentos rojos (`#E84040`) que `breaking` reutiliza para chip y
  tarjeta de cifra.
- `templates/stories/quote.html` — molde más cercano de plantilla simple sin
  fences/loops, con campo opcional resuelto vía `:empty` CSS (`.quote-cargo:empty`).
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `breaking` a
  `[tipo]` junto a `alerta`, `quote`; nuevo bloque "Ruta `breaking`" análogo a "Ruta
  `quote`", líneas 40-104).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `breaking` (mismo patrón que `test_quote_no_placeholders`/`test_quote_autor_sub_vacio`,
  líneas 295-312).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- `idea.md`, `proposal.md` de este mismo Change #123 — base de este documento.
- Issue #123 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B ·
  `breaking`; issues #121 (quote, precedente cerrado) y #119 (motor, fundacional).

<!-- change:125-stories-gi-fase-b-plantilla-encuesta-16-9 -->
# Specification: Stories GI · Fase B — plantilla Encuesta 16:9

> Formaliza `idea.md` y `proposal.md` (fases explore/propose de este Change #125). Fuente
> canónica del contrato de `encuesta`: `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
> (fila 09, línea 67). Hereda el motor generalizado de la Fase A
> (`.pulse/changes/archive/119-.../spec.md`) sin reabrirlo, y el patrón de campo opcional
> (token + `:empty`) validado en Fase B/`quote` (`.pulse/changes/archive/121-.../spec.md`) y
> replicado en Fase B/`breaking` (`.pulse/changes/archive/123-.../spec.md`) sin reabrirlo.
> Resuelve las preguntas abiertas de `idea.md`/`proposal.md` como requisitos verificables
> (sección "Preguntas abiertas — resueltas").

## Objetivo

Agregar la plantilla **`encuesta`** (#09 del catálogo GI) al comando `/story`: una pieza de
sentimiento binario (kicker + pregunta + dos opciones + nota de cierre), fondo oscuro/azul, sin
gráfico y sin listas, alimentada por el criterio editorial 100% de sentimiento puro de
`/encuesta` (sin precios, sin educación, sin dato del motor) — a diferencia de `alerta` (datos
en vivo de `get_asset_levels`) y en la misma familia editorial que `quote`/`breaking` (100%
manual/editorial). Consume el motor genérico de Fase A (`scripts/story_render.py`) tal cual
quedó, sin tocarlo.

## Alcance IN/OUT

### IN
- Nuevo snapshot `templates/stories/encuesta.html` (1920×1080): esqueleto de marca GI
  (fuentes locales `templates/stories/fonts/*.woff2`, footer `@grupointeligencia` +
  disclaimer CFD, igual criterio que `templates/stories/alerta.html:1-58`), paleta
  **oscura/azul** — reemplaza el acento rojo `#E84040`/radial `#2A1220` (usado en
  `alerta`/`quote`/`breaking`) por un acento azul derivado de la paleta GI ya presente en
  el repo (candidatos del design doc: `#1E3A5F`/`#3E91AF`/`#53C1AB`; el hex exacto se fija
  en `apply`, no en `specify` — ver Riesgo B). Tokens escalares `{{kicker}}`,
  `{{pregunta}}`, `{{opcion_a}}`, `{{opcion_b}}`, `{{nota_cierre}}` — **sin fences
  `IF`/`FOR`**.
- Nuevo `[tipo]` `encuesta` en `.claude/commands/story.md` PASO 0 (lista dura hoy
  `alerta`, `quote`, `breaking`) + nuevo bloque "Ruta `encuesta`" — recolección editorial
  con el criterio de sentimiento puro de `/encuesta` (pregunta + dos opciones, sin
  precios ni datos de mercado), que **no llama a `get_asset_levels`** ni ejecuta
  búsqueda propia de evento. Reusa el flujo existente (preview → aprobación → render →
  `ruta_story.ps1 -Plantilla "encuesta"`).
- Tests de mapeo puros en `tests/test_story_render.py` para `encuesta.html`
  (`build_context`/`build_html` contra el snapshot real), incluyendo los casos
  `kicker == ""` y `nota_cierre == ""`. Sin fixture nuevo en `tests/fixtures/stories/`,
  sin tocar `conftest.py`.
- `CLAUDE.md` sección "Stories GI": actualizar la enumeración de `[tipo]` soportados
  (hoy `alerta`, `quote`, `breaking`) para incluir `encuesta`, sin tocar el resto de la
  sección.

### OUT (explícitamente diferido — no se reabre)
- El motor (`build_context`, `resolver_loops`, `_resolver_fences`, `_FENCES`,
  `render_png`) — no se modifica; `_FENCES` sigue fija en `("variacion", "vol",
  "chart_img", "chart_svg")` (`scripts/story_render.py:29`), ninguno de los 4 aplica a
  `encuesta`.
- El contrato de payload de `alerta`, `quote` y `breaking` — sin cambios.
- La última plantilla de Fase B (`edu`) — su propio Change (convención "1 plantilla = 1
  Change" heredada de Fase A/B).
- `scripts/ruta_story.ps1` — ya acepta `-Plantilla` y `-Activo` genéricos, sin cambios.
- `.claude/shared/modo_ejecutivo.md` — `/story` ya figura en "No elegibles", sin
  cambios.
- Fences `<!-- IF:kicker -->`/`<!-- IF:nota_cierre -->` — el motor solo resuelve fences
  top-level para la tupla fija `_FENCES` (4 nombres de Alerta); agregar `kicker` o
  `nota_cierre` a ese mecanismo requeriría tocar el motor, fuera de alcance.
  `encuesta.html` no usa fences (mismo criterio que `quote`/`breaking`).
- Cualquier fuente de datos de mercado (`get_asset_levels`, `obtener_calendario_macro`,
  etc.) — `encuesta` no delega en ningún dato en vivo del motor; es 100% sentimiento
  editorial, mismo contrato que `/encuesta` (CLAUDE.md: "3 tipos sin precios ni
  educación").
- Distinguir en `story.md` entre los 3 tipos de `/encuesta` (`posicion`, `tendencia`,
  `movimiento`) para adaptar el layout — la Story usa siempre el mismo layout binario
  `opcion_a`/`opcion_b` sin importar el tipo de encuesta de origen (resuelto en
  "Preguntas abiertas — resueltas").
- El hex exacto del acento azul — decisión de `apply` (autoría del CSS real), no
  bloqueante para `specify` (mismo criterio que Riesgo B de `breaking`).
- `docs/design/stories-gi/plantillas-stories-gi.md` — no se agrega sección de mapeo
  campo-por-campo dedicada a `encuesta` en este Change (mismo criterio que `breaking`);
  el contrato de campos vive en el design doc de 2026-07-14 (fila 09) y en este
  `spec.md`.
- Sincronización con el canvas GI (Claude Design compartido) — solo lectura, sin
  cambios a esa regla.

## Requisitos funcionales

### R1 — Snapshot `templates/stories/encuesta.html`
Nuevo archivo, viewport 1920×1080, reutiliza el esqueleto de marca de `alerta.html`
(fuentes locales, footer estándar) con paleta **oscura/azul** en vez de oscura/rojo.
Cuerpo: chip `{{kicker}}` (etiqueta opcional, ej. "ENCUESTA DEL DÍA" o tema libre —
criterio editorial, ver R7) + `{{pregunta}}` (texto destacado, tipografía Syne, núcleo
obligatorio) + `{{opcion_a}}`/`{{opcion_b}}` (dos bloques comparativos tipo "A vs B",
núcleo obligatorio, layout simétrico lado a lado) + `{{nota_cierre}}` (línea de cierre
discreta, opcional). Sin gráfico, sin fences `IF`/`FOR` — 5 tokens escalares
incondicionales (mismo criterio que `quote`/`breaking`, confirmado por la tupla fija
`_FENCES` que no cubre ningún campo de `encuesta`). Mapea al punto 1 de la hipótesis.

### R2 — Contrato de payload `story_encuesta`
```json
{
  "plantilla": "encuesta",
  "kicker": "ENCUESTA DEL DÍA",
  "pregunta": "¿Cuál creen que será la tendencia hoy del Oro?",
  "opcion_a": "Alcista",
  "opcion_b": "Bajista",
  "nota_cierre": "Vota en la encuesta fijada del grupo"
}
```
- `plantilla`, `kicker`, `pregunta`, `opcion_a`, `opcion_b`, `nota_cierre` son las únicas
  claves del payload (sin campos array, sin `chart_png`, sin dato del motor).
- `pregunta`, `opcion_a` y `opcion_b` son siempre no vacíos — el comando (R7) nunca
  construye el payload con alguno de estos tres campos como `""`; son el núcleo mínimo
  de una encuesta binaria.
- `kicker` y `nota_cierre` son tokens **siempre presentes** en el payload (nunca
  ausentes/`None`) que admiten string vacío `""` — son los dos campos opcionales del
  contrato (mismo patrón exacto que `autor_sub` en `quote` y `kicker_tema` en
  `breaking`).
- Sin campo `impacto`/`direccion`/`sesgo`/`chart_png`: ningún helper de derivación de
  Fase A (R5 de `.pulse/changes/archive/119-.../spec.md`) se dispara para `encuesta`.
- `pregunta`/`opcion_a`/`opcion_b` son texto editorial de sentimiento puro (mismo
  criterio que el mensaje WhatsApp de `/encuesta`) — no llevan formateo `digits` de
  `config/activos.json` ni ningún dato en vivo del motor.

### R3 — Sin fences `IF`/`FOR` en `encuesta.html`
`encuesta.html` no contiene ningún bloque `<!-- IF:x -->` ni `<!-- FOR:x -->`.
Justificación (confirmada en código, `scripts/story_render.py:29-39,182-261`): los fences
top-level de `_resolver_fences` solo evalúan la tupla fija `_FENCES` (los 4 nombres de
Alerta); el fence genérico por-clave (`_expandir_elemento`) solo existe **dentro** de un
bloque `FOR`, que `encuesta` no usa (sin arrays). Por tanto ningún campo de `encuesta`
puede condicionarse vía fence sin tocar el motor (fuera de alcance) — todos los tokens
son escalares incondicionales, y los dos campos opcionales (`kicker`, `nota_cierre`) se
resuelven vía CSS (R4), no vía fence. Mismo criterio que `quote` R3 / `breaking` R3.

### R4 — Colapso visual de `kicker` y `nota_cierre` vacíos (CSS, no motor)
Cuando `kicker == ""` o `nota_cierre == ""`, el token se sustituye igual (cadena vacía)
— no hay huérfano, no hay error de guardia. Los contenedores HTML de ambos tokens (ej.
`<span class="encuesta-kicker">{{kicker}}</span>` y
`<p class="encuesta-nota">{{nota_cierre}}</p>`) usan la regla CSS `:empty { display:
none; }` sobre cada contenedor, de forma que:
- Con el campo no vacío: se muestra el elemento (chip sobre la pregunta / línea de
  cierre bajo las opciones).
- Con el campo vacío: el contenedor no ocupa espacio (colapsa `display: none`, no solo
  el texto) — el layout se reacomoda sin hueco en blanco. Mismo patrón exacto validado en
  `quote` R4 (`.quote-cargo:empty`) y `breaking` R4 (`.breaking-kicker:empty`).

### R5 — Layout "A vs B" de `opcion_a`/`opcion_b`
`opcion_a` y `opcion_b` se presentan como dos bloques simétricos lado a lado (tipo
"A vs B"), cada uno con su propio rótulo visual estático (ej. "OPCIÓN A" / "OPCIÓN B" o
un separador central "VS", texto fijo del snapshot, no token) — sin flecha de
variación, sin color condicional por dirección, sin fila de soporte/resistencia/vol
(mismo criterio de distinción de un dato de mercado en vivo que R5 de `breaking`).
Resuelve la pregunta abierta de layout de `idea.md`/`proposal.md`.

### R6 — Límites editoriales de longitud
`.claude/commands/story.md` documenta, como criterio editorial del comando (no como
validación del motor), los límites recomendados:
- `kicker` ≤ 30 caracteres (chip corto, una sola línea, mismo límite que `kicker_tema`
  de `breaking`).
- `pregunta` ≤ 90 caracteres (texto destacado central, ligeramente más largo que
  `titular` de Alerta/`breaking` por incluir la formulación completa de la pregunta).
- `opcion_a`/`opcion_b` ≤ 25 caracteres cada una (etiqueta corta de una sola opción,
  ej. "Alcista", "Bajista", "Sube", "Baja").
- `nota_cierre` ≤ 80 caracteres (línea discreta de cierre, más corta que `contexto` de
  `breaking`).
El comando ajusta la redacción antes del preview si algún campo excede su límite; el
motor no valida longitud (mismo criterio que Alerta/`quote`/`breaking`: la guardia solo
valida tokens huérfanos, no longitud de contenido).

### R7 — Recolección editorial en `story.md` sin datos de mercado
`.claude/commands/story.md` PASO 0 agrega `encuesta` a la lista de `[tipo]` soportados
(junto a `alerta`, `quote`, `breaking`). Nuevo bloque "Ruta `encuesta`":
1. Pregunta la pregunta binaria y sus dos opciones, con el mismo criterio editorial de
   `/encuesta` (sentimiento puro, sin precios ni educación — ver contrato de `/encuesta`
   en `CLAUDE.md` "Encuestas diarias"):
   ```
   ¿Cuál es la pregunta de la encuesta? (ej. "¿Cuál creen que será la tendencia hoy del Oro?")
   ¿Opción A?
   ¿Opción B?
   ¿Kicker/tema del chip? (ej. "ENCUESTA DEL DÍA" — Intro para omitir)
   ¿Nota de cierre? (ej. "Vota en la encuesta fijada del grupo" — Intro para omitir)
   ```
2. **`encuesta` no llama a `get_asset_levels`** ni a ninguna tool de mercado
   (`obtener_calendario_macro`, `get_chart_objects`, `get_symbol_spec`), y **no ejecuta
   su propia búsqueda de evento** (no invoca WebSearch) — es una pieza 100% editorial de
   sentimiento, igual criterio que `quote`/`breaking`, heredado del contrato de
   `/encuesta`.
3. Si el director ya corrió `/encuesta [tipo] [activo]` en la misma sesión, el bloque
   ofrece reutilizar la pregunta/opciones ya redactadas ahí como base editorial (atajo
   opcional, no obligatorio — mismo criterio que R7.1 de `breaking`).
4. La Story usa siempre el mismo layout binario `opcion_a`/`opcion_b`, sin distinguir
   entre los 3 tipos de `/encuesta` (`posicion`, `tendencia`, `movimiento`) — el
   contenido de la pregunta/opciones ya refleja el tipo en su redacción, no en el
   layout (resuelve la pregunta abierta "¿el bloque distingue entre tipos de
   `/encuesta`?" de `idea.md`/`proposal.md`).
5. Construye el payload con `kicker` y `nota_cierre` **siempre presentes** — si el
   director no da alguno, `""` (nunca omitir la clave).

### R8 — Guardado con o sin `-Activo` (decisión editorial)
El bloque "Ruta `encuesta`" de `story.md` pregunta al director si la pregunta nombra un
activo protagonista claro (ej. "¿Cuál creen que será la tendencia hoy del Oro?" → Oro
protagonista; a diferencia de `quote`, que siempre es `_general`):
- **Si lo tiene**: pasa `-Activo [TICKER_MT5]` a `ruta_story.ps1` (normalizado contra
  `config/activos.json`, mismo criterio que `/chart` PASO 1).
- **Si no lo tiene** (pregunta general de sentimiento sin activo único, ej. "¿Suben o
  bajan los mercados esta semana?"): se guarda bajo `-Activo "_general"`, igual que
  `quote`/`breaking` sin activo protagonista.
El criterio de decisión es editorial (lo decide el director al responder la pregunta),
no una regla automática nueva del motor ni de `ruta_story.ps1`. Resuelve la pregunta
abierta de `idea.md`/`proposal.md` sobre `-Activo` vs `_general` en `encuesta`.

### R9 — Tests de mapeo puros
`tests/test_story_render.py` agrega, análogo a los tests existentes de `breaking.html`:
1. Test de mapeo con `kicker` y `nota_cierre` no vacíos: `build_html` sobre
   `encuesta.html` con el payload de R2 produce HTML sin placeholders sin resolver, con
   `kicker`, `pregunta`, `opcion_a`, `opcion_b` y `nota_cierre` correctamente inyectados.
2. Test de mapeo con `kicker == ""`: mismo `build_html`, el HTML resultante no contiene
   ningún `{{token}}` huérfano (el token se sustituyó por cadena vacía, no se omitió el
   campo).
3. Test de mapeo con `nota_cierre == ""`: mismo criterio que el punto 2, para el
   segundo campo opcional.
4. Test de dimensiones del render (`skipif` sin Chromium): PNG con IHDR exactamente
   `(1920, 1080)` y tamaño > 5 KB, mismo umbral que `breaking`/`quote`.
Sin fixture nuevo en `tests/fixtures/stories/` (se reusa el patrón de test contra el
snapshot real `encuesta.html`, igual que `quote.html`/`breaking.html`). Sin cambios en
`conftest.py`.

### R10 — Sincronización de `CLAUDE.md`
Sección "Stories GI" de `CLAUDE.md`: la enumeración de `[tipo]` soportados se actualiza
para incluir `encuesta` junto a `alerta`, `quote` y `breaking` (ej. "`[tipo]` soportados
hoy: `alerta`, `quote`, `breaking`, `encuesta`"), sin tocar el resto del
párrafo/sección.

## Casos borde

- **CB-1 (`kicker`/`nota_cierre` ausentes del payload, no `""`)**: el comando (PASO de
  recolección, R7) siempre construye el payload con ambas claves presentes, aunque sean
  `""` — nunca las omite. Si por error se omitiera alguna, el motor lanzaría
  `StoryRenderError` de token huérfano (mismo criterio fail-fast que
  Alerta/`quote`/`breaking`), no un colapso silencioso distinto al de R4.
- **CB-2 (algún campo de longitud excede el límite editorial de R6)**: el comando
  ajusta la redacción antes del preview; el motor no aborta ni trunca — no hay
  validación de longitud en `build_html`.
- **CB-3 (director rechaza el preview)**: no se renderiza ni guarda nada en
  `data/stories/` (mismo criterio CB-3 heredado de `.pulse/specs/stories-gi/spec.md`).
- **CB-4 (flag `ejecutivo`)**: `/story encuesta ejecutivo` avisa que `/story` no
  soporta el flag (mismo criterio ya vigente para `alerta`/`quote`/`breaking`) y
  continúa generando la Story normal.
- **CB-5 (tipo `/story` inválido, incluyendo un valor de `[tipo]` que no es `alerta`,
  `quote`, `breaking` ni `encuesta`)**: `.claude/commands/story.md` PASO 0 informa la
  lista actualizada de tipos disponibles (`alerta`, `quote`, `breaking`, `encuesta`) y
  vuelve a preguntar — nunca asume un tipo por defecto (mismo criterio CB-1 heredado de
  `.pulse/specs/stories-gi/spec.md`).
- **CB-6 (pregunta nombra un activo protagonista ambiguo o varios activos)**: el
  director decide, al responder la pregunta de R8, si hay un activo protagonista único;
  si no lo hay con claridad, se guarda bajo `_general` (mismo criterio que
  `quote`/`breaking`).
- **CB-7 (opciones no son estrictamente antónimos, ej. "Alcista" vs "Lateral")**: el
  comando no valida que `opcion_a`/`opcion_b` sean opuestos exactos — es criterio
  editorial del director al redactar la encuesta (misma libertad que el mensaje
  WhatsApp de `/encuesta`), la plantilla solo garantiza el layout "A vs B" (R5).
- **CB-8 (director ya corrió `/encuesta [tipo] [activo]` en la misma sesión)**: el
  bloque "Ruta `encuesta`" ofrece reutilizar esa pregunta/opciones como base editorial
  (R7.3); no es una dependencia dura — si el director prefiere redactar de cero, lo
  hace directamente.

## Criterios de aceptación

**AC1 — snapshot existe y respeta el viewport (estructural, `rg`/inspección)**
`templates/stories/encuesta.html` existe y contiene `width: 1920px` y `height: 1080px`
(o equivalente) en su CSS — mismo patrón que `templates/stories/alerta.html:49-50`.

**AC2 — sin fences en `encuesta.html` (estructural, `rg`)**
`rg "<!-- (IF|FOR):" templates/stories/encuesta.html` → 0 matches (R3: ningún fence
`IF`/`FOR` en el snapshot).

**AC3 — mapeo de campos con `kicker`/`nota_cierre` no vacíos (ejecutable, `pytest`)**
DADO el payload `{"kicker": "ENCUESTA DEL DÍA", "pregunta": "¿Cuál creen que será la
tendencia hoy del Oro?", "opcion_a": "Alcista", "opcion_b": "Bajista", "nota_cierre":
"Vota en la encuesta fijada del grupo"}`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante contiene el texto de `kicker`, `pregunta`, `opcion_a`,
`opcion_b` y `nota_cierre` correctamente inyectados y no contiene ningún placeholder
`{{...}}` sin resolver (R2/R9).

**AC4 — colapso de `kicker` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"kicker": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver (el token se
sustituyó por cadena vacía) y el contenedor de `kicker` en el CSS del snapshot declara
`:empty { display: none; }` sobre esa clase/selector (R4/R9) — verificable con
`rg ":empty" templates/stories/encuesta.html` ≥2 matches (uno por cada campo opcional).

**AC5 — colapso de `nota_cierre` vacío (ejecutable, `pytest`)**
DADO el mismo payload con `"nota_cierre": ""`,
CUANDO se ejecuta `build_html` sobre `templates/stories/encuesta.html`,
ENTONCES el HTML resultante no contiene ningún `{{token}}` sin resolver, y el
contenedor de `nota_cierre` declara `:empty { display: none; }` (R4/R9).

**AC6 — dimensiones exactas del render (ejecutable, `pytest`, `skipif` sin Chromium)**
DADO el payload de AC3,
CUANDO se ejecuta el render completo (`render_story`) contra
`templates/stories/encuesta.html`,
ENTONCES el PNG resultante tiene IHDR exactamente `(1920, 1080)` y tamaño > 5 KB (mismo
umbral que AC1 de Fase A / AC5 de `quote`/`breaking`).

**AC7 — layout "A vs B" sin elementos de dato de mercado en vivo (estructural, `rg`)**
`rg "soporte|resistencia|variacion_flecha|precio_actual" templates/stories/encuesta.html`
→ 0 matches (confirma que `encuesta.html` no reutiliza el layout de tarjeta de precio de
Alerta ni sus tokens, R5).

**AC8 — `[tipo]` `encuesta` registrado en el comando (estructural, `rg`)**
`rg "encuesta" .claude/commands/story.md` ≥2 matches: uno en la lista de `[tipo]`
soportados del PASO 0, otro en el bloque "Ruta `encuesta`" (R7).

**AC9 — límites editoriales documentados (estructural, `rg`)**
`rg "≤ ?30|≤ ?90|≤ ?25|≤ ?80" .claude/commands/story.md` ≥1 match asociado a los
límites recomendados de `kicker`/`pregunta`/`opcion_a`/`opcion_b`/`nota_cierre` (R6).

**AC10 — `story.md` documenta que `encuesta` no llama a datos de mercado (estructural,
`rg`)**
`rg -i "no llama a .get_asset_levels.|sentimiento puro|sin precios ni datos de mercado" .claude/commands/story.md`
≥1 match dentro del bloque "Ruta `encuesta`" (R7).

**AC11 — `CLAUDE.md` actualizado (estructural, `rg`)**
`rg "encuesta" CLAUDE.md` ≥1 match dentro de la sección "Stories GI" (R10), sin contar
las menciones ya existentes al comando `/encuesta` de texto plano (distinguir por
contexto: la mención nueva debe estar en la enumeración de `[tipo]` de `/story`).

**AC12 — sin regresión del motor ni de Alerta/`quote`/`breaking` (estructural, `rg`/`git diff`)**
`git diff master -- scripts/story_render.py templates/stories/alerta.html
templates/stories/quote.html templates/stories/breaking.html scripts/ruta_story.ps1` no
muestra cambios — confirma que el motor, los snapshots existentes y el helper de
guardado quedan intactos.

## Riesgos

- **Riesgo A — fidelidad visual del snapshot sin golden PNG**: no hay export de
  referencia del canvas GI para `encuesta` en 16:9 azul (mismo riesgo residual R-2
  heredado de Fase A/#109 y de `quote`/`breaking`). Mitigación: aprobación visual manual
  del director en la primera corrida real de `/story encuesta`.
- **Riesgo B — hex exacto del azul no fijado en `specify`**: el design doc solo da
  candidatos (`#1E3A5F`/`#3E91AF`/`#53C1AB`); ninguna plantilla ya renderizada en el
  repo usa hoy un fondo azul. El valor final se decide en `apply` durante la autoría del
  CSS real, no bloquea `specify` (mismo criterio que Riesgo B de `breaking` para el
  rotulado "CIFRA CLAVE").
- **Riesgo C — límites de longitud (R6) son estimaciones editoriales**: al no existir
  golden PNG, los límites exactos en caracteres pueden requerir ajuste tras la primera
  corrida visual real; se documentan como guía editorial del comando, no como
  validación dura del motor (mismo criterio que Riesgo C de `breaking`).
- **Riesgo D — rol semántico de `kicker` ambiguo**: el design doc no especifica si
  `kicker` es una etiqueta fija ("ENCUESTA DEL DÍA") o libre por tema — se resuelve como
  campo libre editorial (mismo tratamiento que `kicker_tema` de `breaking`), ajustable
  por el director en cada corrida; no bloquea `specify` (ver "Preguntas abiertas —
  resueltas").

## Preguntas abiertas — resueltas

Las preguntas de `idea.md`/`proposal.md` quedan resueltas en esta fase (sin preguntas
bloqueantes pendientes para Design):

1. **Paleta azul exacta** → Riesgo B: candidatos documentados
   (`#1E3A5F`/`#3E91AF`/`#53C1AB`), hex final decidido en `apply` (autoría del CSS),
   sin bloquear `specify`.
2. **¿`kicker` es rol fijo o libre?** → Riesgo D/R7.1: campo libre editorial (mismo
   tratamiento que `kicker_tema` de `breaking`), el director lo redacta o lo omite en
   cada corrida.
3. **Layout de `opcion_a`/`opcion_b`** → R5: dos bloques simétricos lado a lado tipo
   "A vs B", con rótulo estático (no token) que distingue las dos opciones.
4. **¿`encuesta` se guarda con `-Activo` o siempre `_general`?** → R8: ambos caminos
   soportados, decisión editorial del director al responder la pregunta de
   recolección; sin activo protagonista claro → `_general` (mismo criterio que
   `quote`/`breaking`).
5. **Sección de mapeo campo-por-campo en `plantillas-stories-gi.md`** → fuera de
   alcance de este Change (ver "OUT"), mismo criterio que `breaking`.
6. **¿El bloque "Ruta `encuesta`" distingue entre los 3 tipos de `/encuesta`
   (`posicion`, `tendencia`, `movimiento`)?** → R7.4: no — la Story usa siempre el
   mismo layout binario `opcion_a`/`opcion_b`; el tipo de origen se refleja en la
   redacción de la pregunta/opciones, no en el layout.

## Referencias

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 09
  `encuesta` (línea 67): payload `kicker, pregunta, opcion_a, opcion_b, nota_cierre`,
  sin gráfico, fondo oscuro/azul, fuente `/encuesta`; línea 24-26 (paleta de acentos de
  marca); línea 91 (plan de fases: Fase B = `quote`, `breaking`, `encuesta`, `edu`).
- `.pulse/specs/stories-gi/spec.md` — contrato de dominio heredado (`story_alerta`,
  `story_quote`, `story_breaking`) como precedente directo de formato para
  `story_encuesta`.
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/spec.md`
  — molde del motor generalizado (R1-R8, AC1-AC12), no se reabre.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/spec.md` — molde
  fundacional del patrón de campo opcional (token + `:empty`).
- `.pulse/changes/archive/123-stories-gi-fase-b-plantilla-breaking-16-9/spec.md` —
  molde estructural directo de este documento (mismo patrón "1 snapshot + 1 bloque de
  recolección + tests de mapeo puros + `CLAUDE.md`"); dos campos opcionales replicados
  con el mismo criterio que `kicker_tema`.
- `scripts/story_render.py:29-39,182-261` — motor 16:9 (fences top-level fijos a
  `_FENCES`; fence genérico solo dentro de `FOR`), **no se modifica** en este Change.
- `templates/stories/alerta.html:1-58` — referencia de esqueleto de marca (fuentes,
  footer) reutilizado sin los acentos rojos/rojizos.
- `templates/stories/breaking.html:85-99,191` y `templates/stories/quote.html:119-127,164`
  — molde directo del patrón `:empty` para los dos campos opcionales de `encuesta`.
- `.claude/commands/story.md` — comando a extender (PASO 0: agregar `encuesta` a
  `[tipo]` junto a `alerta`, `quote`, `breaking`; nuevo bloque "Ruta `encuesta`" análogo
  a "Ruta `breaking`", líneas 110-196).
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para
  `encuesta` (mismo patrón que `test_breaking_no_placeholders`/
  `test_breaking_kicker_vacio`/`test_breaking_render_dimensiones`, líneas 349-379).
- `CLAUDE.md` sección "Stories GI" — actualizar la enumeración de `[tipo]` soportados.
- Contrato editorial `/encuesta` (`CLAUDE.md` sección "Encuestas diarias"; memoria
  `project_encuesta_sentimiento`): sentimiento puro, sin precios ni educación —
  `encuesta` (Story) hereda esta restricción.
- `idea.md`, `proposal.md` de este mismo Change #125 — base de este documento.
- Issue madre de esta Fase B · `encuesta` (a vincular en GitHub); issues #121 (quote) y
  #123 (breaking) como precedentes cerrados directos.
