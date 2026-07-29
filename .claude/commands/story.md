Genera una Story de marca GI (imagen 1920×1080, formato horizontal 16:9) combinando niveles reales del motor con una narrativa de alerta. Único renderer del repo para Stories — ver `scripts/story_render.py` y la regla "solo lectura" del canvas en `CLAUDE.md` sección "Stories GI".

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [ejecutivo?]`

- `[tipo]`: **soportados en este Change: `alerta`, `quote`, `breaking`, `encuesta`, `edu`,
  `flash`, `postventa`**. Las demás plantillas del canvas (Market Update, Indicador Macro, Trading Idea,
  Calendario, Semanal, Carrusel) llegan con los issues #111-#115 — todavía no existen como `[tipo]`
  de este comando.
- `[ejecutivo]` (opcional): `/story` **no soporta el flag ejecutivo** (ver PASO 0).

`/story alerta` genera **un solo activo por corrida** (exactamente 1 Story para 1 activo). Para
varios activos, se ejecuta el comando una vez por activo. `/story quote` es 100% editorial (sin
activo protagonista) — ver bloque de recolección propio más abajo. `/story breaking` también es
100% editorial (noticia urgente: kicker + titular + cifra clave + contexto + reacción), sin datos
de mercado ni búsqueda propia de evento — ver bloque "Ruta `breaking`" más abajo. `/story encuesta`
también es 100% editorial (sentimiento binario: kicker + pregunta + dos opciones + nota de
cierre), sin datos de mercado ni búsqueda propia de evento — ver bloque "Ruta `encuesta`" más
abajo. `/story edu` también es 100% editorial (concepto educativo: kicker + título + definición +
ejemplo comparativo + lista de bullets de aplicación), sin datos de mercado ni búsqueda propia de
evento — ver bloque "Ruta `edu`" más abajo. `/story flash` **sí** consume datos reales del motor
(cierre multi-activo: tabla de N activos con último valor y variación del día), recolectados vía
`get_asset_levels` × N activos con fallback manual, pero **sin gráfico embebido** (eso es Fase D) y
sin búsqueda editorial de evento — ver bloque "Ruta `flash`" más abajo. `/story postventa` es la
única pieza **interna** (no publicable): guion operativo del parte de post-venta, con chip de
INTERNO no suprimible y footer sin marca pública; reusa los datos de `/postventa` si ya se corrió,
o los toma del motor en frío — ver bloque "Ruta `postventa`" más abajo.

---

## PASO 0 — Validar `[tipo]` y el flag `ejecutivo`

1. Si `$ARGUMENTS` viene vacío o `[tipo]` no es `alerta`, `quote`, `breaking`, `encuesta`, `edu`,
   `flash` ni `postventa` (CB-1):
   ```
   📖 Tipos de Story disponibles hoy: alerta, quote, breaking, encuesta, edu, flash, postventa
   (Las demás plantillas del canvas — Market Update, Indicador Macro, Trading Idea,
   Calendario, Semanal, Carrusel — llegan con los issues #111-#115.)

   ¿Generamos la Story de tipo "alerta", "quote", "breaking", "encuesta", "edu", "flash"
   o "postventa"?
   ```
   No continuar hasta que el director confirme `alerta`, `quote`, `breaking`, `encuesta`, `edu`,
   `flash` o `postventa`. Nunca asumir un tipo por defecto. Si el tipo confirmado es `quote`, saltar directamente
   al bloque "Ruta `quote`"; si es `breaking`, saltar al bloque "Ruta `breaking`"; si es `encuesta`,
   saltar al bloque "Ruta `encuesta`"; si es `edu`, saltar al bloque "Ruta `edu`"; si es `flash`,
   saltar al bloque "Ruta `flash`"; si es `postventa`, saltar al bloque "Ruta `postventa`" (los
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

## Ruta `breaking` — recolección editorial (sin datos de mercado)

`breaking` es una pieza editorial de noticia urgente (kicker + titular + cifra clave + contexto
+ reacción): **no** llama a `get_asset_levels` ni a ningún comando/tool de datos de mercado, y
**no ejecuta su propia búsqueda de evento** — no reusa el WebSearch de `/alerta` PASO 1 ni su
mecanismo de detección de noticias; no busca por cuenta propia. Reemplaza los PASO 1-4 de
`alerta`; el preview/render final reusa el mismo patrón de PASO 6-7 adaptado a `breaking` (ver
abajo).

1. **Fuente editorial**: pregunta si el director ya corrió `/noticia` o `/alerta` en la misma
   sesión (o si ya tiene el evento/cifra redactado):
   ```
   ¿Ya corriste /noticia o /alerta con este evento, o tienes el titular y la cifra listos?
   Si no, dime directamente: tema, titular, cifra clave, contexto y reacción del mercado.
   ```
   No bloquea ni exige una corrida previa de `/noticia`/`/alerta` — es un atajo opcional; si el
   director no corrió nada antes, pide que dicte los cinco campos directamente.

2. **Campos y límites editoriales** (guía de redacción de este comando — el motor de render
   **no** valida longitud, no trunca ni aborta):
   ```
   ¿Tema/categoría del kicker? (≤ 30 caracteres — Intro para omitir)
   ¿Titular? (≤ 70 caracteres)
   ¿Cifra clave? (con su unidad, ej. "5,50%", "US$ 2.318")
   ¿Contexto? (≤ 100 caracteres — línea secundaria de apoyo)
   ¿Párrafo de reacción del mercado? (≤ 280 caracteres)
   ```
   Si algún campo excede el límite, ajusta la redacción antes del preview.

   **Dirección explícita (regla de oro)**: el titular/contexto/reacción deben dejar clara la
   lectura direccional del evento (qué activo/mercado se afecta y hacia dónde), con registro
   profesional del repo (énfasis sin dramatización, ver "Registro y tono" de `CLAUDE.md`).

3. **Payload `story_breaking`**: construye `kicker_tema` **siempre presente** — si el director no
   da tema/categoría claro, `"kicker_tema": ""` (nunca omitir la clave). Los otros cuatro campos
   siempre no vacíos. `valor` se recolecta ya formateado con su unidad si aplica — no es un
   precio del motor, no lleva `digits` de `config/activos.json`.
   ```json
   {
     "plantilla": "breaking",
     "kicker_tema": "[tema ≤30 car. o \"\"]",
     "titular": "[titular ≤70 car.]",
     "valor": "[cifra clave con unidad]",
     "contexto": "[contexto ≤100 car.]",
     "parrafo_reaccion": "[párrafo ≤280 car.]"
   }
   ```

4. **Guardado con o sin `-Activo`**: pregunta si la noticia tiene un activo protagonista claro
   (decisión editorial del director, no regla automática nueva ni del motor ni de
   `ruta_story.ps1`):
   ```
   ¿Esta noticia tiene un activo protagonista claro? (ticker o "no" si es ambigua/general)
   ```
   - **Sí** → usa `-Activo [TICKER_MT5]` (normalizado contra `config/activos.json`, mismo
     criterio que `/chart` PASO 1).
   - **No / ambiguo / múltiples activos** → usa `-Activo "_general"` (igual que `quote`).

5. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Breaking*
   ━━━━━━━━━━━━━━━━━━━
   Kicker: [kicker_tema o "(sin kicker)"]
   Titular: [titular]
   Cifra clave: [valor]
   Contexto: [contexto]
   Reacción: [parrafo_reaccion]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

6. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5 o _general]" -Plantilla "breaking" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/breaking.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_breaking del paso 3... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## Ruta `encuesta` — recolección editorial (sin datos de mercado)

`encuesta` es una pieza 100% editorial de sentimiento binario (kicker + pregunta + dos opciones
+ nota de cierre): **no llama a `get_asset_levels`** ni a ninguna otra tool de mercado
(`obtener_calendario_macro`, `get_chart_objects`, `get_symbol_spec`), y **no ejecuta su propia
búsqueda de evento** (no invoca WebSearch) — es **sentimiento puro, sin precios ni datos de
mercado**, mismo contrato que `/encuesta` (sin precios ni educación). Reemplaza los PASO 1-4 de
`alerta`; el preview/render final reusa el mismo patrón de PASO 6-7 adaptado a `encuesta` (ver
abajo).

1. **Recolección editorial**: pregunta la pregunta binaria y sus dos opciones con el mismo
   criterio de sentimiento puro de `/encuesta`:
   ```
   ¿Cuál es la pregunta de la encuesta? (ej. "¿Cuál creen que será la tendencia hoy del Oro?")
   ¿Opción A?
   ¿Opción B?
   ¿Kicker/tema del chip? (ej. "ENCUESTA DEL DÍA" — Intro para omitir)
   ¿Nota de cierre? (ej. "Vota en la encuesta fijada del grupo" — Intro para omitir)
   ```

2. **Atajo opcional**: si el director ya corrió `/encuesta [tipo] [activo]` en la misma sesión,
   ofrece reutilizar esa pregunta/opciones ya redactadas como base editorial — no bloquea ni
   exige corrida previa; si prefiere redactar de cero, lo hace directamente.

3. **Layout binario único**: la Story usa siempre el mismo layout `opcion_a`/`opcion_b` sin
   distinguir entre los 3 tipos de `/encuesta` (`posicion`/`tendencia`/`movimiento`) — el tipo de
   origen se refleja en la **redacción** de la pregunta/opciones, no en el layout.

4. **Límites editoriales** (guía de redacción de este comando — el motor de render **no** valida
   longitud, no trunca ni aborta): `kicker ≤ 30 caracteres`, `pregunta ≤ 90 caracteres`,
   `opcion_a ≤ 25 caracteres`, `opcion_b ≤ 25 caracteres`, `nota_cierre ≤ 80 caracteres`. Si algún
   campo excede el límite, ajusta la redacción antes del preview.

5. **Payload `story_encuesta`**: construye `kicker` y `nota_cierre` **siempre presentes** — si el
   director no da alguno, `""` (nunca omitir la clave). Los otros tres campos
   (`pregunta`/`opcion_a`/`opcion_b`) siempre no vacíos; si el director no puede dar alguno, el
   comando insiste, nunca cadena vacía en esos tres.
   ```json
   {
     "plantilla": "encuesta",
     "kicker": "[kicker ≤30 car. o \"\"]",
     "pregunta": "[pregunta ≤90 car.]",
     "opcion_a": "[opción A ≤25 car.]",
     "opcion_b": "[opción B ≤25 car.]",
     "nota_cierre": "[nota ≤80 car. o \"\"]"
   }
   ```

6. **Guardado con o sin `-Activo`**: pregunta si la pregunta nombra un activo protagonista claro
   (decisión editorial del director, no regla automática nueva ni del motor ni de
   `ruta_story.ps1`):
   ```
   ¿La pregunta tiene un activo protagonista claro? (ticker, o "no" si es general/ambigua)
   ```
   - **Sí** (ej. "…tendencia hoy del Oro" → Oro) → usa `-Activo [TICKER_MT5]` (normalizado
     contra `config/activos.json`, mismo criterio que `/chart` PASO 1).
   - **No / ambiguo / múltiples activos** (ej. "¿Suben o bajan los mercados esta semana?") → usa
     `-Activo "_general"` (igual que `quote`/`breaking`).

7. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Encuesta*
   ━━━━━━━━━━━━━━━━━━━
   Kicker: [kicker o "(sin kicker)"]
   Pregunta: [pregunta]
   Opción A: [opcion_a]   |   Opción B: [opcion_b]
   Nota: [nota_cierre o "(sin nota)"]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

8. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5 o _general]" -Plantilla "encuesta" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/encuesta.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_encuesta del paso 5... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## Ruta `edu` — recolección editorial (sin datos de mercado)

`edu` es una pieza 100% editorial de concepto educativo (kicker + título del concepto +
definición + ejemplo comparativo + lista de bullets de aplicación): **no llama a
`get_asset_levels`** ni a ninguna otra tool de mercado (`obtener_calendario_macro`,
`get_chart_objects`, `get_symbol_spec`), y **no ejecuta su propia búsqueda de evento** (no invoca
WebSearch) — es contenido **educativo, sin datos de mercado**, mismo criterio editorial que
`/concepto` y `/rencuesta` (definición + ejemplo real + puntos de aplicación en voz novata).
Reemplaza los PASO 1-4 de `alerta`; el preview/render final reusa el mismo patrón de PASO 6-7
adaptado a `edu` (ver abajo).

1. **Recolección editorial**: pregunta el concepto con el criterio de `/concepto`/`/rencuesta`:
   ```
   ¿Nombre del concepto? (ej. "Cruce de medias móviles")
   ¿Definición en una o dos líneas (voz novata)?
   Ejemplo comparativo — ¿valor A? ¿operador/relación? ¿valor B? (ej. "Media 50" / "cruza sobre" / "Media 200")
   ¿Bullets de aplicación? (uno por línea; 2 a 4 recomendados)
   ¿Kicker/tema del chip? (ej. "CONCEPTO DE LA SEMANA" — Intro para omitir)
   ```

2. **Atajo opcional**: si el director ya corrió `/concepto` o `/rencuesta` en la misma sesión,
   ofrece reutilizar ese concepto/definición/ejemplo ya redactados como base editorial — no
   bloquea ni exige corrida previa; si prefiere redactar de cero, lo hace directamente.

3. **Límites editoriales** (guía de redacción de este comando — el motor de render **no** valida
   longitud, no trunca ni aborta): `kicker ≤ 30 caracteres`, `titulo_concepto ≤ 45 caracteres`,
   `definicion ≤ 160 caracteres`, `valor_a`/`operador`/`valor_b ≤ 24 caracteres` cada uno, cada
   `bullet ≤ 70 caracteres` (2 a 4 bullets recomendados). Si algún campo excede el límite, ajusta
   la redacción antes del preview.

4. **Payload `story_edu`**: construye `kicker` **siempre presente** — si el director no lo da, `""`
   (nunca omitir la clave). `titulo_concepto`, `definicion` y los tres campos del ejemplo siempre
   no vacíos. El ejemplo se recolecta como objeto editorial pero se **aplana** a las tres claves
   escalares `valor_a`/`operador`/`valor_b` en el payload al motor (el motor solo resuelve claves
   escalares top-level, no `ejemplo.valor_a`). `bullets` es un **array de objetos** `[{"texto": "…"}]`
   (una entrada por bullet dictado); si el director no dicta ninguno, `bullets: []` (la lista
   colapsa limpio en el render).
   ```json
   {
     "plantilla": "edu",
     "kicker": "[kicker ≤30 car. o \"\"]",
     "titulo_concepto": "[nombre ≤45 car.]",
     "definicion": "[definición ≤160 car.]",
     "valor_a": "[valor A ≤24 car.]",
     "operador": "[operador ≤24 car.]",
     "valor_b": "[valor B ≤24 car.]",
     "bullets": [
       { "texto": "[bullet ≤70 car.]" }
     ]
   }
   ```

5. **Guardado bajo `_general`**: `edu` es una pieza educativa sin activo protagonista único → se
   guarda siempre bajo `-Activo "_general"` (mismo criterio que `quote`), no se pregunta por
   activo.

6. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Edu*
   ━━━━━━━━━━━━━━━━━━━
   Kicker: [kicker o "(sin kicker)"]
   Concepto: [titulo_concepto]
   Definición: [definicion]
   Ejemplo: [valor_a] [operador] [valor_b]
   En la práctica:
     • [bullet 1]
     • [bullet 2]
     • [...]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

7. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "_general" -Plantilla "edu" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/edu.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_edu del paso 4... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## Ruta `flash` — cierre multi-activo (datos del motor, sin gráfico)

`flash` es una pieza de **cierre multi-activo**: una tabla de N activos (2 a 6 recomendados) con su
último valor y su variación del día. **Sí** consume datos reales del motor
(`mcp__market-data__get_asset_levels` por activo, con fallback manual), pero **no** lleva gráfico
embebido (eso es Fase D) y **no** ejecuta búsqueda editorial de evento (no invoca WebSearch) — la
narrativa la da la propia tabla, con dirección explícita por fila (regla de oro). Reemplaza los
PASO 1-4 de `alerta`; el preview/render final reusa el mismo patrón de PASO 6-7 adaptado a `flash`
(ver abajo).

1. **Recolección del encabezado**: pregunta el título del cierre, la lista de activos y
   opcionalmente el kicker:
   ```
   ¿Título del cierre? (ej. "Así cerró el mercado hoy")
   ¿Qué activos incluimos? (2 a 6 — tickers o nombres; o "rotación de hoy")
   ¿Kicker/tema del chip? (ej. "CIERRE DE MERCADO" — Intro para omitir)
   ```
   Normaliza cada activo contra `config/activos.json` (mismo criterio que `/chart` PASO 1).

2. **Datos por activo (motor, con fallback manual)**: para **cada activo**, llama una vez
   ```
   mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
   ```
   y extrae el último precio (`valor`) y la variación del día. Si el resultado contiene `"error"`
   (mismo patrón `apertura.md` PASO 4A), pide manualmente el último valor y la variación del día de
   ese activo (no aborta toda la tabla, solo esa fila). Por cada activo arma:
   - `valor`: precio formateado según los `digits` de `config/activos.json` (regla MT5 — coma
     decimal y punto de miles, nunca truncar ceros).
   - `variacion`: pct del día con signo y `%` (ej. `+0,42%`, `-1,86%`, `0,00%`).
   - `direccion`: `alcista` si la variación es > 0, `bajista` si < 0, `lateral` si ≈ 0. **No** se
     escribe como texto: el snapshot la usa como clase CSS (`flash-var--<direccion>`) para el color
     y la flecha ▲/▼/→.
   - `tipo`: clase del activo en voz simple (ej. "Divisa", "Metal", "Energía", "Índice", "Acción").

3. **Sin búsqueda editorial de evento**: `flash` no invoca WebSearch ni reusa la detección de
   noticias de `/alerta` — es un tablero de cierre, no una alerta noticiosa.

4. **Límites editoriales** (guía de redacción de este comando — el motor de render **no** valida
   longitud, no trunca ni aborta): `kicker ≤ 30 caracteres`, `titulo ≤ 45 caracteres`,
   `fecha ≤ 40 caracteres`; por fila `nombre ≤ 16`, `tipo ≤ 14`, `valor ≤ 14`, `variacion ≤ 10`
   caracteres; 2 a 6 filas recomendadas. Si algún campo excede el límite, ajusta la redacción antes
   del preview.

5. **Payload `story_flash`**: construye `kicker` **siempre presente** — si el director no lo da,
   `"kicker": ""` (nunca omitir la clave). `titulo` y `fecha` siempre no vacíos; `fecha` sale del
   reloj de Chile (regla canónica, nunca `WebSearch` para la hora). `filas` es un **array de
   objetos** de claves escalares (una entrada por activo); si el director no da ningún activo, el
   comando insiste (una tabla vacía no aporta).
   ```json
   {
     "plantilla": "flash",
     "kicker": "[kicker ≤30 car. o \"\"]",
     "titulo": "[título ≤45 car.]",
     "fecha": "[D MES YYYY · HH:MM]",
     "filas": [
       { "nombre": "USD/CLP", "tipo": "Divisa", "valor": "889,60", "variacion": "+0,42%", "direccion": "alcista" }
     ]
   }
   ```

6. **Guardado bajo `_general`**: `flash` es una pieza multi-activo sin activo protagonista único →
   se guarda siempre bajo `-Activo "_general"` (mismo criterio que `quote`/`edu`), no se pregunta
   por activo.

7. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Flash (cierre multi-activo)*
   ━━━━━━━━━━━━━━━━━━━
   Kicker: [kicker o "(sin kicker)"]
   Título: [titulo]
   Fecha: [fecha]
   Activos:
     • [nombre] · [tipo] · [valor] · [variacion] ([direccion])
     • [...]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

8. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "_general" -Plantilla "flash" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/flash.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_flash del paso 5... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## Ruta `postventa` — parte interno (atajo desde `/postventa`)

`postventa` es la Story del parte de post-venta: pieza **interna**, no publicable. El chip
`🔒 Interno · Post-venta` está escrito en el snapshot (no es un token, ningún payload puede
suprimirlo) y el footer no lleva handle, dominio ni disclaimer de CFD. Reemplaza los PASO 1-4 de
`alerta`; el preview/render final reusa el patrón de PASO 6-7 adaptado.

1. **Atajo opcional**: abrir preguntando
   ```
   ¿Ya corriste /postventa hoy? Si sí, reuso la consulta, los niveles y los puntos
   de ese parte. Si no, dime el activo y los recolecto del motor.
   ```
   - **Con parte previo** → reusar consulta, respuesta, niveles y puntos ya redactados. **No**
     volver a llamar a `get_asset_levels`.
   - **En frío** → pedir el activo (normalizado contra `config/activos.json`, mismo criterio que
     `/chart` PASO 1) y llamar
     `mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})`, tomando
     el precio y el soporte/resistencia más próximos. Si retorna `{"error": ...}`, pedirlos
     manualmente (mismo patrón que `apertura.md` PASO 4A).

   El atajo no bloquea ni exige corrida previa.

2. **Límites editoriales** (guía de redacción de este comando — el motor **no** valida longitud,
   no trunca ni aborta): `fecha_hora` ≤ 28 · `consulta` ≤ 60 · `respuesta` ≤ 90 ·
   `activo_nombre` ≤ 14 · `soporte`/`precio`/`resistencia` ≤ 12 cada uno · `sesgo` ≤ 10 · cada
   `respuestas[].texto` ≤ 62 (4 a 6 entradas) · cada `no_promesas[].texto` ≤ 62 (2 a 3 entradas) ·
   `fuente` ≤ 30. Si algún campo excede el límite, ajusta la redacción antes del preview.

3. **Payload `story_postventa`**: `sesgo` es exactamente una de `Alcista` / `Bajista` / `Lateral`
   — el motor deriva de ahí `sesgo_slug`, que el snapshot usa como clase CSS de color y flecha
   (▲ verde / ▼ rojo / → gris). Los precios van formateados con los `digits` de
   `config/activos.json`. Las dos listas son arrays de objetos con la clave `texto`; si una llega
   vacía (`[]`), su columna colapsa y el rótulo persiste.
   ```json
   {
     "plantilla": "postventa",
     "fecha_hora": "[D MES YYYY · HH:MM]",
     "consulta": "[consulta ≤60 car.]",
     "respuesta": "[respuesta ≤90 car.]",
     "activo_nombre": "[nombre corto ≤14 car.]",
     "soporte": "[precio con digits]",
     "precio": "[precio con digits]",
     "resistencia": "[precio con digits]",
     "sesgo": "Alcista|Bajista|Lateral",
     "respuestas": [ { "texto": "[≤62 car.]" } ],
     "no_promesas": [ { "texto": "[≤62 car.]" } ],
     "fuente": "MT5 · GRUPO INTELIGENCIA"
   }
   ```

4. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Post-Venta (INTERNA)*
   ━━━━━━━━━━━━━━━━━━━
   Consulta: [consulta]
   Respuesta: [respuesta]
   Niveles: S [soporte] · [activo_nombre] [precio] ([sesgo]) · R [resistencia]
   Qué responder: [n] puntos
   Qué NO prometer: [n] puntos
   ━━━━━━━━━━━━━━━━━━━
   ⚠️ Pieza interna: el chip y el footer la marcan como no reenviable al cliente.
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

5. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7). A diferencia de `edu`,
   esta pieza **sí** lleva activo protagonista:
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "[TICKER_MT5]" -Plantilla "postventa" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/postventa.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_postventa del paso 3... }
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

La píldora de la tarjeta muestra el **sesgo**, no un tag de riesgo. Se alimenta del campo `sesgo`
del payload (`Alcista`/`Bajista`/`Lateral`) y el snapshot le pone el color semántico y la flecha
(▲ verde / ▼ rojo / → gris). No hay que decidir ni redactar nada extra para ese espacio.

> El antiguo `tag_riesgo` (`RIESGO ALTO`/`RIESGO MEDIO`) quedó **fuera del contrato** por decisión
> del director: era una etiqueta sin criterio visible para el cliente, ocupando el lugar más
> valioso de la tarjeta. Si un payload heredado todavía trae la clave, el motor la ignora en
> silencio (clave no referenciada por ningún token).

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

⚠️ **`variacion.direccion` y `sesgo` deben ser coherentes.** El color de la píldora sale de
`sesgo_slug`, y el motor lo deriva de `variacion.direccion` **con prioridad** sobre `sesgo`. Si se
envía una variación `alcista` junto a un sesgo `Lateral`, la píldora dirá "LATERAL" pintada de
verde. Cuando ambos campos viajen, que apunten en la misma dirección.

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
Sesgo: [sesgo]
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
