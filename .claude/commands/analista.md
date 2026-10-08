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
2. **Dirección clara.** El cliente tiene que saber hacia dónde va el activo. Si `datos.direccion`
   dice Alcista o Bajista, el texto lo sostiene; no lo contradigas.
3. **Español de Chile, tuteo neutro.** Nada de voseo (tenés, podés, mirá). Tono cercano y
   pedagógico, sin dramatizar ("presión a la baja", nunca "se derrumba").
4. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
5. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Para listas, una línea por punto
   empezando con `• `. Para párrafos, una línea en blanco entre ellos.
6. **Siglas explicadas en línea** la primera vez: "vacantes de empleo (JOLTS)".
7. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160. Van impresos dentro de la imagen.
8. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.

### Qué va en cada campo

`datos.chip` dice qué pieza es.

- **Activo** (`NOTA DE MERCADO`):
  - `titular`: la idea principal con la dirección.
  - `bajada`: qué la sostiene.
  - `lectura`: 2 párrafos cortos con qué pasa y qué significa para quien opera.
  - `empuja_alza` y `empuja_baja`: 2 o 3 puntos cada uno, con los drivers del día y su efecto
    (analizados, no enumerados).
  - `que_no_hacer`: un error concreto a evitar hoy.
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

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

Responde solo `OK` o `ERROR: <motivo>`.
