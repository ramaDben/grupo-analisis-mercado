Redacta los textos de una pieza del bot de analistas. Solo escribe texto en `pieza.json`: no ejecuta pipelines, no rinde imágenes y no envía nada.

## /analista — textos de una pieza pedida por un analista

**Argumento:** `$ARGUMENTS` es la ruta de un `pieza.json` dentro de `data/informes_analistas/`.
Si no es una ruta así, detente y responde `ERROR: ruta inválida`.

Lo invoca el bot de Telegram (`scripts/bot_analistas.py`). El bot ya leyó el terminal, armó los
datos y rindió los gráficos; tu única tarea es redactar. La maqueta del informe es fija y la
pone el bot: tú no decides nada visual.

### Qué puedes tocar

- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  que están dentro de `editorial.explicaciones` o `editorial.por_activo`.
- **Nunca** `orden`, `datos`, `imagenes`, `anidados`, `laminas` ni `huella`. Están sellados: si
  cambian, la pieza se descarta entera.
- **Nunca** agregues ni quites claves de `editorial`.
- **Ningún otro archivo** del repo. No corras pipelines, no llames al MCP, no uses la web.

### Reglas del texto (de `.agents/rules/proyecto.md`, que manda ante cualquier duda)

1. **Cada cifra sale de `datos`.** No escribas un precio, nivel, porcentaje o dato que no esté
   en `datos`, ni lo redondees a otro valor. El bot rechaza cualquier número con decimales o de
   tres o más dígitos que no encuentre ahí.
2. **Solo afirmas lo medido.** En la pieza de activo, `datos.contexto` trae los drivers del
   catálogo, la curva de tasas con sus cambios y la agenda de hoy con sus resultados. Un driver
   se afirma como hecho del día ("el bono a 10 años sube 4 pb") solo si está ahí; si no, se explica
   como mecanismo condicional ("si el dólar se fortalece, el oro tiende a ceder"). Nunca inventes
   que el dólar, el petróleo o cualquier otro activo "sube" o "se debilita" hoy.
3. **Dirección clara.** El cliente tiene que saber hacia dónde va el activo. Si `datos.direccion`
   dice Alcista o Bajista, el texto lo sostiene; no lo contradigas.
4. **Español de Chile, tuteo neutro.** Nada de voseo (tenés, podés, mirá). Tono cercano y
   pedagógico, sin dramatizar ("presión a la baja", nunca "se derrumba").
5. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
6. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Para listas, una línea por punto
   empezando con `• `. Para párrafos, una línea en blanco entre ellos.
7. **Siglas explicadas en línea** la primera vez: "vacantes de empleo (JOLTS)".
8. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160. Van impresos dentro de la imagen.
9. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.
10. **Análisis general, nunca una instrucción.** Escribe en impersonal y condicional ("el
    escenario se activa si…", "la presión compradora"). Nunca le digas al lector que compre,
    venda, entre, cierre ni cuánto arriesgar, y no recomiendes: el informe es igual para todos y
    nadie en GI está inscrito como asesor de inversión. El bot rechaza esas frases.
11. **Soporte y resistencia**, nunca "piso", "suelo" ni "techo" para un nivel de precio.

### Qué va en cada campo

`datos.chip` dice qué pieza es.

- **Activo** (`NOTA DE MERCADO`):
  - `titular`: la idea principal con la dirección.
  - `bajada`: qué la sostiene.
  - `lectura`: 2 párrafos cortos con qué pasa y qué significa para quien opera.
  - `empuja_alza` y `empuja_baja`: 2 o 3 puntos cada uno, con los drivers del día y su efecto
    (analizados, no enumerados).
  - `que_no_hacer`: un error concreto a evitar hoy.
  - `datos.plan` (gatillo, invalidación, recorrido, estadística) lo escribió el bot y sale en su
    propia sección: no lo repitas. Si lo nombras en `lectura`, en una frase y con sus mismas cifras.
- **Foco técnico** (`FOCO TÉCNICO DEL DÍA`): los mismos campos que la pieza de activo, pero la
  comparte un ejecutivo con un **prospecto que recién empieza**:
  - Más simple: frases cortas, cada término técnico explicado en la misma frase.
  - Ni un porcentaje, ni cuánto acierta el escenario, ni invitaciones ("aprovecha", "no te lo
    pierdas", "última oportunidad"). Describe el escenario y deja la decisión al lector. El bot
    rechaza esas frases y cualquier `%`.
  - No escribas la palabra "oportunidad": la pieza se llama foco técnico.
- **Calendario**:
  - `titular` y `bajada` sobre la jornada o la semana.
  - `lectura`: qué dato domina y por qué.
  - `explicaciones.<id>`: por cada evento, qué mide en lenguaje novato y qué mueve.
- **Dato** (`DATO MACRO`):
  - `datos.modo` dice si el dato ya salió (`resultado`) o no (`anticipacion`).
  - `que_paso`: el hecho, o qué se espera.
  - `que_significa`: el impacto en la vida cotidiana y en el mercado.
  - `que_no_hacer`.
  - `impacto`: un punto por activo afectado.
- **Jornada** (`INFORME DE APERTURA` o `CIERRE`):
  - `lectura`: el panorama.
  - `por_activo.<ticker>`: 2 o 3 frases con qué pasa, qué significa y qué no hacer.
  - `que_no_hacer`: la regla del día.
- **Escenario de la semana** (`ESCENARIO DE LA SEMANA`): material que un ejecutivo manda a su
  cartera por correo y WhatsApp. Visión **diaria**, para toda la semana.
  - `titular` y `bajada`: la idea de la semana con su dirección (`datos.direccion`).
  - `contexto_semana`: 2 párrafos cortos con **qué está pasando esta semana**, bajado a lo que
    trae `datos.contexto`: la agenda de lunes a viernes (lo que ya salió, con su cifra, y lo que
    falta, en modo anticipación), la curva con su cambio a 5 días y `variacion_semana`. Nada general.
  - `que_lo_mueve`: 2 o 3 puntos, uno por driver **de esta semana**, cada uno con su efecto
    direccional sobre el activo. Analizados, no enumerados.
  - `whatsapp`: 2 o 3 frases (máximo 420 caracteres) que abren el mensaje de WhatsApp. El bot
    agrega debajo el precio, la activación, la invalidación y el recorrido: no los repitas.
  - `datos.escenario` (gatillo, invalidación, recorrido) y la simulación los escribe el bot.
  - Prohibido además: «oportunidad», «recomendada», «aprovecha», «si hubieras entrado»,
    «ganarías», «garantizado». La pieza describe un escenario medible y no invita a nada.
- **Seguimiento** (`SEGUIMIENTO`): la actualización diaria de ese escenario.
  - `hoy`: una o dos frases (máximo 300 caracteres) con **lo de hoy** frente a lo general:
    `datos.contexto.agenda_hoy` (con sus resultados), la curva a 1 día y `variacion_dia`,
    contrastados con `contexto.escenario_semana` y `contexto.contexto_lunes`.
  - El estado (vigente, avanzando, completado o invalidado) y sus cifras ya los escribió el bot:
    no lo repitas ni lo califiques. Los cuatro estados se cuentan igual: nunca celebres uno ni
    digas cuánto habría ganado alguien. Mismas frases prohibidas que la pieza semanal.

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

Responde solo `OK` o `ERROR: <motivo>`.
