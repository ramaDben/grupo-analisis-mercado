Genera una Story de marca GI (imagen 1920×1080, formato horizontal 16:9) combinando niveles reales del motor con una narrativa de alerta. Único renderer del repo para Stories — ver `scripts/story_render.py` y la regla "solo lectura" del canvas en `CLAUDE.md` sección "Stories GI".

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [ejecutivo?]`

- `[tipo]`: **`alerta`, `breaking`, `calendario`, `dato_macro`** — y solo esos: son las
  cuatro plantillas que existen en `templates/stories/`. El resto del catálogo se retiró
  cuando el estándar de diseño pasó a estar comandado por el brand kit
  (`brand_atomic_system/`). Un tipo que no tiene plantilla no se inventa: se detiene y se
  reporta.
- `[ejecutivo]` (opcional): `/story` **no soporta el flag ejecutivo** (ver PASO 0).

`/story alerta` genera **un solo activo por corrida** (exactamente 1 Story para 1 activo). Para
varios activos, se ejecuta el comando una vez por activo.

`/story breaking` es 100% editorial (noticia urgente: kicker + titular + cifra clave + contexto +
reacción), sin datos de mercado ni búsqueda propia de evento — ver bloque "Ruta `breaking`" más
abajo.

`/story dato_macro` cubre un dato económico que ya publicó y se organiza alrededor del veredicto
frente al consenso — ver bloque "Ruta `dato_macro`" más abajo.

`/story calendario` es el calendario macro de la semana: una selección editorial de 3 a 6 eventos
(no un volcado íntegro del calendario), sin activo protagonista, así que cae al acento de marca
porque no hay un solo activo al que pintarle color. **Sí** consume datos reales del motor
(`obtener_calendario_macro`), pero **no** ejecuta búsqueda editorial de evento propia — ver bloque
"Ruta `calendario`" más abajo.

---

## PASO 0 — Validar `[tipo]`

`/story` **no pregunta nada**: el tipo, el activo y la temporalidad llegan como argumentos.
Si falta alguno, se detiene y lo dice; nunca asume un valor por defecto ni abre un menú.

Tipos válidos, que son las cuatro plantillas que existen en `templates/stories/`:

| tipo | qué es | necesita |
|---|---|---|
| `alerta` | niveles del día de un activo | activo + temporalidad |
| `dato_macro` | un dato económico que ya publicó | el evento |
| `breaking` | noticia urgente, 100% editorial | el titular y su cifra |
| `calendario` | 3 a 6 eventos macro de la semana | nada (los trae el motor) |

Cualquier otro tipo **se rechaza**:

```
❌ "<tipo>" no existe. El catálogo se redujo a alerta, dato_macro, breaking y calendario
   cuando el estándar de diseño pasó al brand kit (brand_atomic_system/).
```

No lo inventes ni lo sustituyas por el más parecido: publicar una pieza que el director no
pidió es peor que no publicar.

Despacho: `dato_macro` → bloque "Ruta `dato_macro`"; `breaking` → "Ruta `breaking`";
`calendario` → "Ruta `calendario`". Los PASO 1-7 son exclusivos de `alerta`.

---

## Ruta `dato_macro` — un dato económico que ya publicó

Es la **pieza 1 de la agenda diaria** (orden canónico del issue #43: el dato del calendario va
primero, mientras se cargan los niveles en MT5). En el **Modo resultado** de esta ruta, la
Story **es** el entregable al grupo, y el mensaje de texto quedó reducido a su pie de foto: el
desarrollo largo (sub-lecturas, "qué significa", impacto por activo) vive acá dentro y no se manda
además como texto. No cubre el modo anticipación, porque la pieza se organiza alrededor del
veredicto y un dato que todavía no sale no tiene veredicto — ahí el mensaje completo sigue siendo
el entregable.

**No busca el evento por su cuenta.** El indicador y sus cifras llegan en la invocación, o se leen
de `obtener_calendario_macro`; nunca inventarlas ni
salir a buscarlas acá.

1. Recolectar del mensaje ya aprobado (o preguntar):
   - `indicador` en español con la sigla entre paréntesis una sola vez, y `periodo`.
   - `actual`, `esperado` y `anterior`. **`anterior` puede ir como cadena vacía** si el indicador no
     publica comparable: el bloque desaparece entero, rótulo incluido.
   - `veredicto` (`Mejor` / `En línea` / `Peor`) y `veredicto_slug` (`mejor` / `en-linea` / `peor`).
2. Escribir `titular` y `significado` con el criterio editorial del proyecto: voz novata, regla
   de los 30 segundos, sin siglas sin explicar. El bloque "🔤 Diccionario rápido" **no va en la
   imagen** y tampoco va ya en el mensaje, que quedó reducido al pie: cada sigla se explica **en
   línea**, dentro de la frase donde aparece, una sola vez ("vacantes de empleo (JOLTS)"). Si el
   titular y el `significado` necesitan más de dos siglas, están mal redactados.
3. Armar `activos`: 3 filas con `nombre`, `direccion` (`sube` / `baja` / `lateral`), `etiqueta` y
   `porque` en una línea. Incluir cuando corresponda un activo **sin efecto**: decirle al cliente qué
   *no* lo afecta vale tanto como decirle qué sí.

La **temporalidad del impacto no va en esta Story**: desbordaba el lienzo vertical y la etiqueta
sirve poco sin su explicación. Sigue siendo obligatoria en el pie del mensaje (ambos
modos) — en el Modo resultado, dentro del pie de esta imagen, que es la única pieza del desarrollo
largo que sobrevive en el texto.

⚠️ `veredicto_slug` es frente al **consenso**, no una dirección de mercado. Un dato "mejor" puede ser
bajista para un activo — y esa distinción es lo que la pieza enseña, así que cada fila de `activos`
lleva su propia dirección.

Payload → `templates/stories/dato_macro.html`. Seguir con PASO 6 (aprobación) y PASO 7 (render).
`ruta_story.ps1` sin activo protagonista: la pieza es del dato, no de un activo.

---

## Ruta `breaking` — recolección editorial (sin datos de mercado)

`breaking` es una pieza editorial de noticia urgente (kicker + titular + cifra clave + contexto
+ reacción): **no** llama a `get_asset_levels` ni a ningún comando/tool de datos de mercado, y
**no ejecuta su propia búsqueda de evento** — no ejecuta el WebSearch de la ruta `alerta` ni su
mecanismo de detección de noticias; no busca por cuenta propia. Reemplaza los PASO 1-4 de
`alerta`; el preview/render final reusa el mismo patrón de PASO 6-7 adaptado a `breaking` (ver
abajo).

1. **Fuente editorial**: el titular y la cifra llegan en la invocación. Si no vinieron
   sesión (o si ya tiene el evento/cifra redactado):
   ```
   ❌ Falta el titular y la cifra del evento. No los busco por mi cuenta.
   Si no, dime directamente: tema, titular, cifra clave, contexto y reacción del mercado.
   ```
   Se detiene ahí: inventar una noticia urgente es el peor error posible de esta pieza; si el
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
     criterio del catálogo de activos).
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

## Ruta `calendario` — el calendario macro de la semana (datos del motor, selección editorial)

`calendario` señala los eventos económicos más relevantes de la semana para los activos del
catálogo. **Sí** consume datos reales del motor (`mcp__market-data__obtener_calendario_macro`),
pero la **selección es editorial**: no es un volcado íntegro del calendario, es un recorte de 3 a 6
eventos (mismo criterio que "el driver que domina hoy" en los mensajes de niveles — curar, no
enumerar). No hay activo protagonista ni gráfico: usa la piel de `oportunidad` (sello con pulso,
CTA, disclaimer) pero cae al acento de marca (`--activo: var(--acento)`, el mismo fallback que un
activo sin color propio en `alerta`/`recomendacion`).

1. **Datos del motor (obligatorio)**: llama
   ```
   mcp__market-data__obtener_calendario_macro({"min_impact": "medium", "solo_hoy": false})
   ```
   para traer la semana completa (no solo hoy). Si devuelve `{"error": "NO_CALENDAR_FEEDS", ...}`,
   cae a WebSearch sobre investing.com como fallback; nunca
   inventar un evento ni una cifra de consenso/previo.

2. **Selección editorial de 3 a 6 eventos**: de los eventos devueltos, elige los de mayor
   relevancia para el catálogo (Oro, WTI, USD/CLP, US100, acciones) dentro de la semana en curso
   (lunes a viernes desde hoy). Prioriza `impacto: "alto"` y los que tengan `forecast`/`previo`
   (un dato sin consenso publicado aporta poco a una pieza que mira hacia adelante). Pregunta al
   director si quiere ajustar la selección antes de armar el payload:
   ```
   📅 Candidatos de la semana (impacto alto/medio):
      1. [dia] [hora] — [evento] ([pais]) · antes [previo] · se espera [forecast]
      2. [...]
   ¿Con cuáles seguimos (3 a 6)? ¿Alguno que agregar o sacar?
   ```

3. **Título y subtítulo**: pregunta o propone un título corto (ej. "Lo que mueve la semana") y un
   subtítulo de una frase que nombre los activos que tocan estos datos (ej. "Los 5 datos de mayor
   impacto para Oro, WTI, USD/CLP y US100").

4. **Límites editoriales** (guía de redacción — el motor no valida longitud): `titulo ≤ 40
   caracteres`, `subtitulo ≤ 140 caracteres`; por evento `evento ≤ 70 caracteres`, `referencia ≤ 40
   caracteres`. Con 6 eventos y textos en el límite superior la tabla queda ajustada — si el
   director pide más de 6, avisar que la pieza pierde margen contra el CTA (ver comentario del
   snapshot) y sugerir recortar la selección en vez de forzarla.

5. **Payload `story_calendario`**: `sello` y `fecha_hora` siempre presentes (`fecha_hora` describe
   el rango de la semana, ej. "SEMANA DEL 11 AL 15 DE AGOSTO", en hora Chile). `eventos` es un
   **array de objetos** de claves escalares; cada evento nombra el país/divisa y trae `impacto`
   como etiqueta visible (no como color semántico — el impacto no es una dirección de mercado).
   ```json
   {
     "plantilla": "calendario",
     "sello": "CALENDARIO SEMANAL · GI",
     "fecha_hora": "SEMANA DEL 11 AL 15 DE AGOSTO",
     "titulo": "Lo que mueve la semana",
     "subtitulo": "Los 5 datos de mayor impacto para Oro, WTI, USD/CLP y US100.",
     "eventos": [
       {
         "dia": "MIÉRCOLES 12", "hora": "08:30 CLT",
         "evento": "Índice de precios al consumidor (IPC) de EE.UU., interanual",
         "pais": "EE.UU. · USD", "referencia": "Antes 3,5% · Se espera 3,4%",
         "impacto": "Alto impacto"
       }
     ],
     "cta": "¿Quieres seguir esta semana en detalle?",
     "cta_sub": "Habla hoy con tu analista"
   }
   ```

6. **Guardado bajo `_general`**: sin activo protagonista único → se guarda siempre bajo
   `-Activo "_general"` (mismo criterio que `quote`/`edu`/`flash`), no se pregunta por activo.

7. **Preview y aprobación** (mismo criterio que PASO 6, ANTES de renderizar o guardar nada):
   ```
   📖 *PREVIEW — Story Calendario (semana)*
   ━━━━━━━━━━━━━━━━━━━
   Título: [titulo]
   Subtítulo: [subtitulo]
   Eventos:
     • [dia] [hora] — [evento] ([pais]) · [referencia] · [impacto]
     • [...]
   ━━━━━━━━━━━━━━━━━━━
   ¿Apruebas esta Story? ¿Generar y guardar el PNG final?
   ```
   Si el director **no** aprueba: no renderizar ni guardar nada en `data/stories/`. Terminar el
   comando ahí.

8. **Render y guardado** (solo tras aprobar, mismo patrón que PASO 7):
   ```powershell
   scripts\ruta_story.ps1 -Fecha "[YYYY-MM-DD]" -Activo "_general" -Plantilla "calendario" -Hora "[HH-mm]"
   ```
   La `[Hora]` sale del reloj de Chile (regla canónica).
   ```bash
   uv run python scripts/story_render.py \
     --template templates/stories/calendario.html \
     --out "[ruta devuelta por ruta_story.ps1]" <<'STORY_PAYLOAD'
   { ...payload story_calendario del paso 5... }
   STORY_PAYLOAD
   ```
   Mismo manejo de éxito/error que PASO 7.3-7.4.

---

## PASO 1 — Activo y temporalidad (de los argumentos, no de una pregunta)

`alerta` cubre **un solo activo por corrida**. El activo y la temporalidad vienen en la
invocación (`/story alerta USDCLP 1H`); el activo se normaliza contra `config/activos.json`
en cualquier formato (ticker, nombre, `#TICKER`).

Temporalidades válidas, con las etiquetas canónicas del repo:

| | |
|---|---|
| `15M` | scalper (minutos a 1-2 h) |
| `1H` | intradía (dentro de la jornada) |
| `4H` | swing de jornada (1-3 días) |
| `1D` | posicional (días a semanas) |

Si el activo no está en el catálogo o falta la temporalidad, **detente y dilo**, nombrando lo
que recibiste. No elijas por el director.

---

## PASO 2 — Niveles y precio (del motor, o no hay pieza)

Llama **una sola vez**:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"})
```

- Con éxito: toma `price` y deriva **un soporte y una resistencia**, los más próximos al precio.
- Si la respuesta trae `"error"`, **detente y reporta el código exacto**:

```
❌ El motor no entregó niveles para [ACTIVO]: [CÓDIGO] — [mensaje].
   No genero la pieza. Revisa que MT5 esté abierto y vuelve a pedirla.
```

No hay fallback manual y no se piden precios por teclado. Es la REGLA 1 del proyecto: un
precio que nadie verificó dentro de una pieza que invita a operar es el peor resultado
posible, y el error del motor es una respuesta, no un obstáculo que rodear.

`variacion_pct` y `volumen_relativo` son opcionales: si vienen en la respuesta del motor se
usan, y si no, se omiten. Tampoco se preguntan.

Formatea `precio_actual`/`soporte`/`resistencia` según `digits` de `config/activos.json`, con
**coma decimal y punto de miles** (`2.318,40`, nunca `2318.4`).

---

## PASO 3 — Narrativa (criterio editorial de la alerta de mercado — R2.3/CB-5)

Detecta si hay un evento real de las últimas horas que afecte al activo, con el mismo criterio
y las mismas fuentes de siempre (`WebSearch` sobre investing.com +
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

## PASO 4 — Chart embebido (opcional, por argumento)

Si la invocación trae la ruta de un PNG ya generado en `data/charts/`, se embebe. Si no viene,
la Story sale sin chart y se sigue adelante. **No se pregunta**: una pieza sin chart es una
pieza válida, y detener el flujo por eso convierte un opcional en un bloqueo.

Si la ruta viene pero el archivo no existe, **detente y dilo** en vez de rendir la pieza sin él:
el renderer falla ante una imagen inexistente y ese fallo es la garantía de que nadie publica
una Story a la que le falta lo que prometió.

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
  "activo_slug": "[slug de identidad o \"\"]",
  "activo_imagen": "[assets/activos/<slug>.jpg o \"\"]",
  "fecha_hora": "[D MES YYYY · HH:MM]",
  "titular": "[titular ≤70 car.]",
  "parrafo": "[párrafo ≤280 car.]",
  "rotulo_activo": "[NOMBRE · TICKER]",
  "precio_actual": "[precio con digits]",
  "variacion": { "pct": "[valor]", "direccion": "alcista|bajista" },
  "soporte": "[soporte con digits]",
  "resistencia": "[resistencia con digits]",
  "vol_pct": "[impulso proyectado en puntos, ej. '150,69 pts' para Impulso ADC/ATR]",
  "rotulo_grafico": "[TICKER · CIERRES H1 · ÚLTIMAS 60 VELAS]",
  "chart_png": "[ruta o null]",
  "fuente": "[COMEX/INVESTING/MT5 · GRUPO INTELIGENCIA]",
  "sesgo": "Alcista|Bajista|Lateral",
  "recorrido": {
    "serie": "[array de 60 cierres H1 reales]",
    "marcadores": [ { "indice": 59, "precio": "[spot]", "clase": "actual", "etiqueta": "[spot con digits]", "rol": "AHORA" } ],
    "niveles": [
      { "precio": "[resistencia]", "clase": "resistencia", "etiqueta": "[resistencia con digits]", "rol": "RESISTENCIA" },
      { "precio": "[soporte]", "clase": "soporte", "etiqueta": "[soporte con digits]", "rol": "SOPORTE" }
    ],
    "lienzo": "alto"
  }
}
```

**Geometría y Proporción del Gráfico:**
- Usar siempre `"lienzo": "alto"` en el bloque `recorrido` de `alerta` para maximizar la altura vertical del gráfico y la legibilidad de las etiquetas de precios (`22px`).
- El campo `vol_pct` alimenta la columna **`Impulso ADC/ATR`** en la tarjeta de estadísticas de la Story.

Si el director omitió variación/vol en el PASO 2, **omite esas claves por completo** del JSON
(no las dejes en `null` ni vacías) — así el template no deja hueco visual (CB-4).

⚠️ **`variacion.direccion` y `sesgo` deben ser coherentes.** El color de la píldora sale de
`sesgo_slug`, y el motor lo deriva de `variacion.direccion` **con prioridad** sobre `sesgo`. Si se
envía una variación `alcista` junto a un sesgo `Lateral`, la píldora dirá "LATERAL" pintada de
verde. Cuando ambos campos viajen, que apunten en la misma dirección.

`fuente`: si la narrativa nace de una noticia, usa la fuente de esa noticia (ej. `COMEX`,
`INVESTING`); si es lectura técnica, usa `MT5 · GRUPO INTELIGENCIA`.

| Campo | Qué lleva |
|---|---|
| `activo_slug` | Identidad cromática. **Mapeo explícito**, no derivado del ticker — son los cuatro activos con color en `templates/stories/marca.css`: Oro (`XAUUSD`) → `oro` · Petróleo WTI (`WTI.spot`) → `wti` · Nasdaq 100 (`US100.spot`) → `us100` · USD/CLP (`USDCLP`) → `usdclp`. Cualquier otro activo va **vacío** y la pieza sale en el acento de marca. Derivarlo con `lowercase(ticker_mt5)` produce `xauusd` para el Oro, que `marca.css` no define: la pieza sale en teal de marca sin ningún error visible. **No confundir con el slug de la ruta de guardado**: `ruta_story.ps1` sí usa `lowercase(ticker_mt5)` sin `.spot`/`#`/`/` (el Oro ahí es `xauusd`), y es otra cosa. |
| `activo_imagen` | `assets/activos/<slug>.jpg` si existe la imagen; cadena vacía si no. Nunca inventar una ruta: un `src` roto deja un ícono de imagen rota en la pieza. |

**Identidad del activo (plantillas `alerta`, `recomendacion` y `oportunidad`)**:
`activo_slug` pinta el escenario y `activo_imagen` lo ilustra. Son identidad, no
dirección — el sesgo lo sigue pintando `sesgo_slug` con `--sube`/`--baja`. Si se
colapsaran, una pieza dorada bajista se leería como alcista dorada.

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
