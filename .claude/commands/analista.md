Redacta los textos de una pieza del bot de analistas. Solo escribe texto en `pieza.json`: no ejecuta pipelines, no rinde imágenes y no envía nada.

## /analista — textos de una pieza pedida por un analista

**Argumento:** `$ARGUMENTS` es la ruta de un `pieza.json` dentro de `data/informes_analistas/`.
Si no es una ruta así, detente y responde `ERROR: ruta inválida`.

Lo invoca el bot de Telegram (`scripts/bot_analistas.py`). El bot ya leyó el terminal, armó los
datos y rindió los gráficos; tu única tarea es redactar. La maqueta del informe es fija y la
pone el bot: tú no decides nada visual.

### Qué puedes tocar

- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  que están dentro de `editorial.titulares` y `editorial.contexto` (uno por ticker).
- **Nunca** `orden`, `datos`, `imagenes`, `anidados`, `laminas` ni `huella`. Están sellados: si
  cambian, la pieza se descarta entera.
- **Nunca** agregues ni quites claves de `editorial`.
- **Ningún otro archivo** del repo. No corras pipelines, no llames al MCP, no uses la web.

### Reglas del texto (de `.agents/rules/proyecto.md`, que manda ante cualquier duda)

1. **Cada cifra sale de `datos`.** No escribas un precio, nivel, porcentaje o dato que no esté
   en `datos`, ni lo redondees a otro valor. El bot rechaza cualquier número con decimales o de
   tres o más dígitos que no encuentre ahí.
2. **Solo afirmas lo medido.** `datos.drivers.<ticker>` trae los drivers del catálogo para cada
   activo, `datos.agenda_semana` la agenda de la semana y `datos.curva` la curva de tasas con sus
   cambios en puntos base. Un driver se afirma como hecho ("el bono a 10 años sube 4 pb") solo si
   está ahí; si no, se explica como mecanismo condicional ("si el dólar se fortalece, el oro tiende
   a ceder"). Nunca inventes que el dólar, el petróleo o cualquier otro activo "sube" o "se
   debilita".
3. **Dirección clara.** El cliente tiene que saber hacia dónde va el activo. Si
   `datos.activos[i].lectura.direccion` dice ALCISTA o BAJISTA, el texto lo sostiene; no lo
   contradigas. Con LATERAL (estado RANGO), el texto describe el rango entre sus dos bordes.
4. **Español de Chile, tuteo neutro.** Nada de voseo (tenés, podés, mirá). Tono cercano y
   pedagógico, sin dramatizar ("presión a la baja", nunca "se derrumba").
5. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
6. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Para listas, una línea por punto
   empezando con `• `. Para párrafos, una línea en blanco entre ellos.
7. **Siglas explicadas en línea** la primera vez: "vacantes de empleo (JOLTS)".
8. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160. Van impresos dentro de la imagen.
9. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.
10. **Invita a operar el escenario, sin dar una instrucción.** La gerencia pidió que la pieza
    semanal invite siempre a operar el supuesto (2026-10-12): es material para que el área
    comercial venda. Cada `contexto.<ticker>` cierra con una frase que invita a operar el
    escenario de la semana, en condicional y atada a la lectura ("el escenario alcista se puede
    operar mientras el precio se mantenga sobre la línea de tendencia, y la simulación de abajo
    muestra con qué riesgo"; "si el precio confirma la ruptura, el escenario bajista queda para
    operarlo"). Lo que sigue prohibido es la instrucción personal: nunca "compra", "vende",
    "entra ya", "te recomiendo" ni cuánto arriesgar, porque
    nadie en GI está inscrito como asesor de inversión. El bot rechaza esas frases, y también un
    contexto que no invite a operar.
11. **Soporte y resistencia**, nunca "piso", "suelo" ni "techo" para un nivel de precio.

### Qué va en cada campo

`orden.pieza` dice qué pieza es. Solo `oportunidad` pasa por ti: el seguimiento
(`/seguimiento`) lo escribe Python entero y no tiene campos editoriales.

- **Análisis técnico de la semana** (`oportunidad`, `datos.chip` = "ANÁLISIS TÉCNICO DE LA SEMANA"):
  - `titular` (≤ 70) y `bajada` (≤ 160) sobre la semana de los seis activos.
  - `titulares.<ticker>` (≤ 70): la idea del activo con su dirección, sacada de
    `datos.activos[i].lectura`.
  - `contexto.<ticker>`: 2 o 3 frases con los drivers de la semana (`datos.drivers.<ticker>`,
    `datos.agenda_semana`), como mecanismo condicional si no hay un hecho medido, y **una frase
    final que invita a operar el escenario** (regla 10, con alguna forma de "operar"). Sin `%`,
    sin la palabra "oportunidad", sin repetir los niveles (los pone la maqueta).
  - `titular` y `bajada` también empujan a la acción: nombran la dirección y que hay escenarios
    para operar en la semana, sin prometer resultados.
  - Los niveles, el escenario 1:3 y la simulación los escribió Python: no los repitas ni los
    comentes.

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

Responde solo `OK` o `ERROR: <motivo>`.
