# Proposal: Comando `/story` — piloto "Market Update" con render Playwright del template Claude Design

Issue: [bbenja11/grupo-analisis-mercado#109](https://github.com/bbenja11/grupo-analisis-mercado/issues/109)

## Why

El equipo de diseño de GI entregó 6 plantillas visuales de Stories (1080×1920,
formato WhatsApp/Instagram) documentadas en
`docs/design/stories-gi/plantillas-stories-gi.md`, pero el motor GAM hoy solo
produce dos tipos de salida: texto plano WhatsApp (`data/mensajes/`) y
screenshots crudos de MT5 sin marca (`/chart` → `data/charts/`). No existe
ningún mecanismo para inyectar datos reales del motor (niveles, calendario,
alertas, señales) en una pieza visual con la identidad de marca de GI. El
antecedente directo es el issue #107 (`/ventas`), que excluyó explícitamente
la generación de infografías de su alcance ("la plantilla de infografía la
entregará otro equipo posteriormente y se conectará después"). El director no
puede hoy ofrecer al cliente una Story reenviable de marca — solo texto o un
chart sin capa visual.

El director ya resolvió las 9 preguntas abiertas dejadas por Discovery
(`idea.md`). Este Change entrega la primera conexión end-to-end del motor
GAM con el sistema de plantillas de GI, acotada a **una** plantilla piloto,
como base reutilizable para las 5 restantes en Changes futuros.

## What Changes

### Alcance propuesto

1. **Comando nuevo `/story [tipo]`** (Capa 2) — punto de entrada dedicado,
   no un flag dentro de `/apertura`/`/dato_macro`/`/alerta`/`/señal`.
   - Primer y único `[tipo]` soportado en este Change: `market_update`
     (↔ plantilla "Market Update" de GI, mapeada a `/apertura`).
   - El comando **reutiliza** internamente la lógica de recolección de
     datos de `/apertura` (activo, temporalidad, indicador, niveles) en
     lugar de duplicarla — invoca/re-ejecuta el mismo flujo de preguntas
     (PASOS 1-4 de `apertura.md`) o recibe como input el resultado ya
     aprobado de una corrida de `/apertura` en la misma sesión, a definir en
     Specify el detalle exacto de "reutilizar" (import de lógica vs.
     re-preguntar).
   - El renderer (Playwright) vive centralizado en un solo lugar del
     comando `/story`, no replicado por cada comando de origen — así
     cuando se agreguen las otras 5 plantillas, cada una solo aporta su
     mapeo de campos, no su propio pipeline de render.

2. **Mecanismo de render: Playwright headless** sobre una copia adaptada
   del template HTML/CSS del canvas de Claude Design ("Market Update").
   - Prioriza fidelidad visual de marca sobre peso de dependencias — el
     manual de marca PDF (`Manual Plantilla Stories - Grupo Inteligencia.pdf`)
     se respeta reutilizando el layout real, no reimplementándolo a mano
     en Pillow.
   - Nueva dependencia en `pyproject.toml` (Playwright + su navegador
     Chromium). **Pendiente para Specify**: validar viabilidad de instalar
     Chromium en la máquina local del director (no hay server; hoy
     `pyproject.toml` solo declara `fastmcp`/`pandas` en runtime — sin
     precedente de dependencias pesadas de este tipo).
   - La copia adaptada del template vive dentro de este repo (no se
     importa el runtime del canvas `support.js`/`image-slot.js` — ya
     descartado en Discovery); solo se toma el layout/CSS estático como
     snapshot de referencia.

3. **Plantilla piloto única: "Market Update"** (↔ `/apertura`).
   - Elegida por mayor frecuencia de uso (niveles técnicos, 2-3 activos
     casi diarios) y por tener los campos ya maduros y estables:
     `precio actual`, `Resistencia más próxima/siguiente`, `Soporte más
     próximo/siguiente`, `Zona de interés`, `Sesgo del equipo`, indicador
     elegido (RSI/ATR/EMA/MACD/Bollinger), chip de activo+precio.
   - Las otras 5 plantillas (Indicador Macro, Alerta, Trading Idea,
     Reporte Flash, Calendario) quedan **fuera de alcance** de este
     Change.

4. **Convención de guardado: `data/stories/`** (nueva carpeta,
   gitignored — mismo régimen que `data/charts/*.png` y `data/mensajes/`).
   - Misma lógica día → activo → tipo que `scripts/ruta_mensaje.ps1`, pero
     adaptada a binarios. Se extiende el helper (o se crea un helper
     hermano) con un tipo de salida `.png` para Stories, sin mezclar con
     `data/charts/` (esa carpeta es exclusivamente para screenshots crudos
     de MT5 vía EA `GI_ChartExporter`/`ChartObjectsExporter`).
   - Nombre canónico exacto (¿`<activo_slug>_story_market_update_<fecha_hora>.png`
     o variante?) queda para Specify, siguiendo el mismo patrón de
     `<activo_slug>` ya establecido (`lowercase(ticker_mt5)` sin
     `.spot`/`#`/`/`).

5. **Flujo de aprobación idéntico al resto del repo**: preview (texto de
   los datos que se inyectarán + posible thumbnail) → "¿Apruebas? ¿Enviar
   la Story al grupo?" → solo tras aprobación explícita se genera/guarda
   el PNG final. Sin envío automático (Evolution API sigue sin conectar).

6. **`/story` NO es elegible para el flag `ejecutivo`** — mismo criterio
   que `/chart` ("genera un PNG, no texto"). Si `/story market_update`
   envuelve datos de `/apertura`, el guion interno (si se necesita) ya lo
   produce `/apertura ejecutivo` por su lado; no se duplica ni se define
   un `guion_story`.

7. **Formalizar la regla "solo lectura" del canvas Claude Design en
   `CLAUDE.md`**. Hoy vive únicamente en
   `docs/design/stories-gi/plantillas-stories-gi.md`. Este Change agrega
   una sección/regla explícita en `CLAUDE.md` (candidata: junto a las
   reglas de MCP Servers o en una nueva sección "Stories GI") que
   establece: el proyecto Claude Design compartido (dueño: Rodrigo, GI) es
   **solo lectura** — este repo nunca sube datos, lógica ni configuración
   propia hacia allá; el render final se produce y aprueba enteramente
   dentro de este repo.

8. **Sincronización con GI: snapshot manual**. Sin mecanismo automático de
   refresco. Cuando GI notifique un cambio de plantilla o del manual de
   marca, el director confirma y el snapshot del template (HTML/CSS
   adaptado + PDF de marca) se actualiza a mano en el repo, en un commit
   explícito — no hay polling ni sync periódico contra el canvas
   compartido.

9. **Independencia confirmada de "motor como cerebro hub GI"**. Este
   Change no referencia `docs/design/motor-como-cerebro-hub-gi.*` como
   dependencia ni bloqueante. Avanza y entrega valor
   (una Story real de marca con datos reales) sin importar si la visión
   más amplia de hub/API en la nube es aprobada por GI.

### Enfoque de solución (alto nivel)

```
/story market_update
   │
   ├─ 1. Recolecta datos (reutiliza flujo de /apertura: activo, TF,
   │      indicador, niveles ya aprobados)
   ├─ 2. Mapea los datos al contrato de campos de la plantilla
   │      "Market Update" (chip activo+precio, soporte, resistencia,
   │      sesgo, zona de interés)
   ├─ 3. Inyecta esos campos en la copia adaptada del template HTML
   │      (snapshot local, sin runtime del canvas)
   ├─ 4. Renderiza con Playwright headless → PNG 1080×1920
   ├─ 5. Muestra preview (texto/ruta) → "¿Apruebas? ¿Enviar?"
   └─ 6. Al aprobar: guarda en data/stories/... (helper dedicado) y
          muestra ruta lista para adjuntar en WhatsApp
```

Reutiliza el patrón ya validado en el repo de "proceso externo genera →
función del repo copia/recibe con nombre canónico" (precedente: `/chart` +
EA MT5; `get_chart_objects` + Service `ChartObjectsExporter`), aplicado
aquí a un proceso de render local (Playwright) en lugar de un proceso MT5.

### Criterios de éxito

- `/story market_update` produce un PNG 1080×1920 con datos reales de un
  activo (no placeholders), visualmente fiel al template de GI, guardado
  en `data/stories/` con nombre canónico y ruta reproducible.
- El flujo de aprobación bloquea cualquier guardado/envío sin confirmación
  explícita del director (mismo principio que el resto del repo).
- `CLAUDE.md` contiene la regla "solo lectura" del canvas Claude Design de
  forma explícita y descubrible (no solo en el doc de referencia).
- Ningún dato real del motor (activos, drivers, niveles) se sube al
  proyecto Claude Design compartido en ningún punto del flujo.
- El pipeline es reutilizable: agregar una segunda plantilla (Change
  futuro) no debería requerir un segundo renderer, solo un segundo mapeo
  de campos.

### Riesgos / trade-offs

- **Dependencia pesada nueva (Playwright + Chromium)** en una máquina
  local sin infraestructura de servidor — riesgo de instalación/tamaño y
  de fricción en el entorno del director. Mitigación: Specify valida
  viabilidad antes de comprometer la dependencia; si falla, la alternativa
  (b) descartada en Discovery (Pillow/HTML-to-image nativo) queda como
  fallback documentado, no como plan B silencioso.
- **Drift de marca**: al ser un snapshot manual (decisión 8), si GI
  actualiza el template en el canvas compartido y el director no se
  entera o demora en confirmar, la Story generada localmente puede quedar
  visualmente desactualizada respecto al canvas vigente. Mitigación:
  ninguna automática en este Change — riesgo aceptado explícitamente por
  el director al elegir snapshot manual sobre sync automático.
- **Mapeo de campos parcial conocido**: el propio doc de referencia
  advierte que la extracción de campos fue liviana (grep dirigido, no
  parseo completo del HTML ~90 KB). Es posible que aparezcan campos no
  detectados en la plantilla "Market Update" real al construir la copia
  adaptada — Specify debe validar el contrato de campos completo antes de
  Design.
- **Acoplamiento con `/apertura`**: si el contrato de datos de
  `/apertura` cambia (ver `apertura.md` PROHIBIDO/reglas de formato), el
  mapeo de campos de `/story market_update` puede romperse silenciosamente
  si no hay un contrato explícito compartido entre ambos comandos —
  Specify debe decidir si `/story` consume el mensaje de texto ya
  renderizado o una estructura de datos intermedia antes del render de
  texto.
- **Sin precedente de tests de render visual** en el repo (los tests
  actuales cubren `src/market_data_mcp` con pytest, no output visual/PNG)
  — Specify debe decidir el criterio de verificación (¿comparación de
  snapshot? ¿revisión manual del director únicamente?).

### Qué queda fuera de este Change

- Las 5 plantillas restantes (Indicador Macro, Alerta, Trading Idea,
  Reporte Flash, Calendario) y su mapeo campo-por-campo.
- El carrusel de 4 slides de "Calendario" — decisión de diseño ya fijada
  para cuando se aborde (4 PNGs separados `_1de4`...`_4de4`, no una pieza
  compuesta), pero **no se implementa** en este Change.
- Modo ejecutivo/guion interno para `/story` (no aplica, decisión 6).
- Cualquier mecanismo automático de sincronización con el canvas Claude
  Design compartido (decisión 8: snapshot manual únicamente).
- La visión "motor como cerebro hub GI" (`docs/design/motor-como-cerebro-hub-gi.*`)
  — sin relación de dependencia con este Change (decisión 9).
- Envío automático a WhatsApp (Evolution API sigue sin conectar en todo el
  repo) — el flujo termina en "PNG aprobado, listo para adjuntar
  manualmente".

## Referencias

- `docs/design/stories-gi/plantillas-stories-gi.md`
- `docs/design/stories-gi/Manual Plantilla Stories - Grupo Inteligencia.pdf`
- `.claude/commands/apertura.md` (PASOS 1-5, plantilla "Market Update"
  piloto)
- `.claude/commands/chart.md` (precedente de pipeline binario:
  comando → proceso externo genera → copia con nombre canónico)
- `src/market_data_mcp/tools/chart_objects.py` (`get_chart_objects`,
  segundo precedente de "recibir" un binario generado externamente)
- `scripts/ruta_mensaje.ps1` (convención de nombres a extender con tipo
  binario `story`)
- `config/activos.json` (`ticker_mt5`, `digits`, `volatilidad`,
  `nota_volatilidad`)
- `.claude/shared/modo_ejecutivo.md` (contrato de referencia para
  justificar por qué `/story` NO es elegible)
- `pyproject.toml` (dependencias runtime actuales — sin Playwright/Pillow
  hoy)
- `.gitignore` (régimen de `data/charts/*.png`, `data/mensajes/` — a
  extender con `data/stories/`)
- `.pulse/changes/109-discovery-conectar-motor-gam-con-plantillas-visuales-stories-gi/idea.md`
  (Discovery — 9 preguntas abiertas, resueltas por el director como input
  fijo de este proposal)
- GitHub issue: `bbenja11/grupo-analisis-mercado#109`
- Issue relacionado: `bbenja11/grupo-analisis-mercado#107` (excluyó
  infografías de su alcance; precedente directo)
