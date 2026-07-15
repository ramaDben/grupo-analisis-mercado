Genera una Story de marca GI (imagen 1920×1080, formato horizontal 16:9) combinando niveles reales del motor con una narrativa de alerta. Único renderer del repo para Stories — ver `scripts/story_render.py` y la regla "solo lectura" del canvas en `CLAUDE.md` sección "Stories GI".

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [ejecutivo?]`

- `[tipo]`: **soportados en este Change: `alerta`, `quote`**. Las demás plantillas del canvas
  (Market Update, Indicador Macro, Trading Idea, Calendario, Carrusel) llegan con los issues
  #111-#115 — todavía no existen como `[tipo]` de este comando.
- `[ejecutivo]` (opcional): `/story` **no soporta el flag ejecutivo** (ver PASO 0).

`/story alerta` genera **un solo activo por corrida** (exactamente 1 Story para 1 activo). Para
varios activos, se ejecuta el comando una vez por activo. `/story quote` es 100% editorial (sin
activo protagonista) — ver bloque de recolección propio más abajo.

---

## PASO 0 — Validar `[tipo]` y el flag `ejecutivo`

1. Si `$ARGUMENTS` viene vacío o `[tipo]` no es `alerta` ni `quote` (CB-1):
   ```
   📖 Tipos de Story disponibles hoy: alerta, quote
   (Las demás plantillas del canvas — Market Update, Indicador Macro, Trading Idea,
   Calendario, Carrusel — llegan con los issues #111-#115.)

   ¿Generamos la Story de tipo "alerta" o "quote"?
   ```
   No continuar hasta que el director confirme `alerta` o `quote`. Nunca asumir un tipo por
   defecto. Si el tipo confirmado es `quote`, saltar directamente al bloque "Ruta `quote`" (los
   PASO 1-5 de abajo son exclusivos de `alerta`).

2. Si el argumento `ejecutivo` está presente (CB-6/R7):
   ```
   ℹ️ /story no soporta el flag "ejecutivo" (mismo criterio que /chart — genera una imagen,
   no un mensaje de cliente reenviable). Continúo generando la Story normal.
   ```
   Avisar y **continuar** con el flujo normal (no detener, no generar guion).

---

## Ruta `quote` — recolección editorial (sin datos de mercado)

`quote` es una pieza 100% editorial (cita + autor + cargo): **no** llama a
`get_asset_levels` ni a ningún comando fuente de datos de mercado (`/apertura`,
`/dato_macro`, etc.). Reemplaza los PASO 1-4 de `alerta`; el preview/render final
reusa el mismo patrón de PASO 6-7 adaptado a `quote` (ver abajo).

1. **Cita**: pregunta al director si quiere dictarla él mismo o que el modelo redacte
   una propuesta editorial (ej. resumiendo una idea de mercado de la semana, mismo
   criterio que `/concepto`) para que la apruebe/ajuste:
   ```
   ¿Dictas tú la cita o prefieres que redacte una propuesta?
   ```
   - **Límite editorial**: `cita ≤ 220 caracteres` — guía de redacción de este comando
     (el motor de render no valida longitud, no trunca ni aborta). Si la cita excede el
     límite, ajusta la redacción antes del preview.
   - Recolecta la cita **sin comillas propias** — las comillas decorativas las pone el
     snapshot (`templates/stories/quote.html`), nunca el texto del payload.

2. **Autor y cargo**: pregunta ambos campos:
   ```
   ¿Nombre del autor de la cita?
   ¿Cargo/rol del autor? (Intro para omitir)
   ```
   Construye el payload con `autor_sub` **siempre presente** — si el director no da
   cargo, `"autor_sub": ""` (nunca omitir la clave).

3. **Payload `story_quote`**:
   ```json
   {
     "plantilla": "quote",
     "cita": "[cita ≤220 car., sin comillas propias]",
     "autor": "[nombre del autor]",
     "autor_sub": "[cargo o \"\"]"
   }
   ```

4. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar
   nada):
   ```
   📖 *PREVIEW — Story Quote*
   ━━━━━━━━━━━━━━━━━━━
   Cita: [cita]
   Autor: [autor] — [autor_sub o "(sin cargo)"]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`.
   Terminar el comando ahí.

5. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "_general" -Plantilla "quote" -Hora "[HH-mm]"
   ```
   (`quote` es editorial sin activo protagonista → se guarda bajo `_general`.) La
   `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/quote.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_quote del paso 3... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## PASO 1 — Preguntar activo y temporalidad del gráfico

Pregunta al director **un solo activo** (acepta cualquier formato — ticker, nombre, `#TICKER` —
normaliza contra `config/activos.json`, mismo criterio que `/chart` PASO 1) y la temporalidad
del gráfico usando las etiquetas canónicas del repo:

```
¿Qué activo genera la Alerta? (uno solo por corrida)

¿Qué temporalidad usamos para el gráfico?
1. 15M — scalper (minutos a 1-2 h)
2. 1H  — intradía (dentro de la jornada)
3. 4H  — swing de jornada (1-3 días)
4. 1D  — posicional (días a semanas)
```

Si no reconoces el activo, muestra la lista de disponibles (igual que `/chart` PASO 1) y vuelve
a preguntar.

---

## PASO 2 — Niveles y precio (motor, con fallback manual — R2.2/CB-2)

Llama **una sola vez**:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"})
```

- Si responde con éxito: extrae `price` (precio actual) y deriva **un solo soporte y una sola
  resistencia** — los más próximos al precio actual.
- Si el resultado contiene `"error"` (mismo patrón `apertura.md` PASO 4A):
  ```
  ⚠️ No se pudo obtener niveles desde MT5. Ingresa manualmente:
  Precio actual:
  Soporte más próximo:
  Resistencia más próxima:
  ```
  Pedir los 3 valores manualmente. Aceptar valores con o sin `$`, coma de miles o espacios.

Formatea `precio_actual`/`soporte`/`resistencia` según `digits` de `config/activos.json`, con
**coma decimal y punto de miles** (regla del contrato de datos: `2.318,40`, nunca `2318.4`).

Pregunta también, de forma opcional (CB-4 — si no hay dato confiable, se omiten sin pedirlos
de nuevo):
```
¿Variación % del día? (Intro para omitir)
¿Volumen % relativo? (Intro para omitir)
```

---

## PASO 3 — Narrativa (criterio editorial de `/alerta` PASO 1 — R2.3/CB-5)

Detecta si hay un evento real de las últimas horas que afecte al activo, con el mismo criterio
y las mismas fuentes de `.claude/commands/alerta.md` PASO 1 (`WebSearch` sobre investing.com +
fuentes oficiales: Fed, BCCh, BCE, OPEP+, EIA, BLS, geopolítica, earnings tech):

- **Si HAY evento reciente**: la narrativa es noticiosa — titular tipo noticia + párrafo de
  contexto (qué pasó, por qué mueve al activo).
- **Si NO hay evento reciente** (CB-5): la narrativa es una lectura técnica del precio frente a
  sus niveles (ej. "el activo se aproxima a su soporte clave, con presión vendedora reciente").
  **No abortar ni exigir noticia** — es un camino válido y esperado.

En ambos casos, **dirección explícita obligatoria** (regla de oro del repo): el titular y el
párrafo deben dejar claro el sesgo (`Alcista`/`Bajista`/`Lateral`). Registro profesional: énfasis
direccional sí, dramatización no (ver "Registro y tono" de `CLAUDE.md`).

Límites visuales del layout: `titular` ≤ ~70 caracteres, `parrafo` ≤ ~280 caracteres. Ajusta la
redacción antes de pasar al preview.

Decide `tag_riesgo` según contexto:
- Ruptura de nivel o evento de alto impacto → `RIESGO ALTO`.
- Aproximación al nivel sin ruptura confirmada → `RIESGO MEDIO`.

---

## PASO 4 — Chart embebido (opcional)

Pregunta:
```
¿Quieres embeber un chart de /chart en esta Story? (s/n)
```
- Si **sí**: pide la ruta del PNG ya generado en `data/charts/` (o invoca `/chart` primero si
  aún no existe). Verifica que el archivo exista antes de continuar — si no existe, avisa y
  vuelve a preguntar (el motor de render también valida esto y falla con error accionable si la
  ruta es inválida, CB-8).
- Si **no**: continúa sin `chart_png` — el template usa el gráfico decorativo SVG del snapshot.

---

## PASO 5 — Construir el payload `story_alerta`

Arma el payload exacto (ver `spec.md` §"Contrato de datos"), con `fecha_hora` usando el reloj
de Chile (regla canónica de `CLAUDE.md`, nunca `WebSearch` para la hora):

```json
{
  "plantilla": "alerta",
  "activo": {
    "ticker_mt5": "[TICKER_MT5]",
    "nombre": "[nombre del activo]",
    "digits": [digits]
  },
  "chip_categoria": "[CATEGORÍA · ACTIVO]",
  "fecha_hora": "[D MES YYYY · HH:MM]",
  "titular": "[titular ≤70 car.]",
  "parrafo": "[párrafo ≤280 car.]",
  "rotulo_activo": "[NOMBRE · TICKER]",
  "tag_riesgo": "RIESGO ALTO | RIESGO MEDIO",
  "precio_actual": "[precio con digits]",
  "variacion": { "pct": "[valor]", "direccion": "alcista|bajista" },
  "soporte": "[soporte con digits]",
  "resistencia": "[resistencia con digits]",
  "vol_pct": "[valor u omitir la clave]",
  "rotulo_grafico": "[TICKER · VELAS TF]",
  "chart_png": "[ruta o null]",
  "fuente": "[COMEX/INVESTING/MT5 · GRUPO INTELIGENCIA]",
  "sesgo": "Alcista|Bajista|Lateral"
}
```

Si el director omitió variación/vol en el PASO 2, **omite esas claves por completo** del JSON
(no las dejes en `null` ni vacías) — así el template no deja hueco visual (CB-4).

`fuente`: si la narrativa nace de una noticia, usa la fuente de esa noticia (ej. `COMEX`,
`INVESTING`); si es lectura técnica, usa `MT5 · GRUPO INTELIGENCIA`.

---

## PASO 6 — Preview y aprobación (R5/CB-3 — ANTES de renderizar o guardar nada)

Muestra un resumen de texto (nunca el PNG todavía):

```
📖 *PREVIEW — Story Alerta de Mercado*
━━━━━━━━━━━━━━━━━━━
Activo: [nombre] ([ticker_mt5])
Titular: [titular]
Párrafo: [parrafo]
Soporte: [soporte] · Resistencia: [resistencia]
Riesgo: [tag_riesgo]
Chart embebido: [sí/no]
━━━━━━━━━━━━━━━━━━━
¿Apruebas esta Story? ¿Generar y guardar el PNG final?
```

- **Si el director NO aprueba** (CB-3): no renderizar ni guardar absolutamente nada en
  `data/stories/`. Terminar el comando ahí.
- **Si aprueba**: continuar al PASO 7.

---

## PASO 7 — Render y guardado (solo tras aprobar)

1. Construir la ruta de salida con el helper determinista (NUNCA armarla a mano):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5]" -Plantilla "alerta" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica). El helper crea las carpetas.

2. Invocar el script de render (único renderer del repo) pasando el payload por **stdin**:
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/alerta.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_alerta del PASO 5... }
   STORY_PAYLOAD
   ```

3. **Éxito** (exit 0): el script imprime la ruta del PNG. Mostrar al director:
   ```
   ✅ Story generada: [ruta]
   Ábrela y adjúntala manualmente en WhatsApp Status / el canal correspondiente.
   ```
4. **Error** (`StoryRenderError`, exit 1, ej. Chromium ausente o `chart_png` inexistente):
   mostrar el mensaje de stderr **tal cual** al director (ya viene accionable, ej.
   `uv sync --extra stories && python -m playwright install chromium`) — nunca un traceback
   crudo. No reintentar automáticamente.

---

## NOTAS

- Este comando **nunca** sube datos propios (config, drivers, mensajes reales) al proyecto
  Claude Design compartido — solo lee los snapshots locales `templates/stories/alerta.html` y
  `templates/stories/quote.html` (regla "solo lectura", ver `CLAUDE.md`).
- No hay envío automático a WhatsApp: el flujo termina en "PNG aprobado, listo para adjuntar".
- `scripts/story_render.py` es el único punto de render del repo para Stories — las plantillas
  futuras (#111-#115) reutilizan el mismo script, solo agregan su propio snapshot HTML y su
  propio `[tipo]` aquí.
