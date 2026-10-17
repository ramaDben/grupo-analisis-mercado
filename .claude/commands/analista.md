Redacta los textos del análisis de un activo del bot de analistas. Escribe texto en `pieza.json`: no ejecuta pipelines, no rinde imágenes y no envía nada. La única herramienta externa que usas es la búsqueda web, solo para encontrar las fuentes de `fuentes`.

## /analista — textos del análisis de un activo

**Argumento:** `$ARGUMENTS` es la ruta de un `pieza.json` dentro de `data/informes_analistas/`.
Si no es una ruta así, detente y responde `ERROR: ruta inválida`.

Lo invoca el bot de Telegram (`scripts/bot_analistas.py`). El bot ya leyó el terminal, armó los
datos y rindió el gráfico; tu tarea es redactar y encontrar voces de prestigio. La maqueta es fija
y la pone el bot: tú no decides nada visual.

### Qué puedes tocar

- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  de `editorial.titulares` y `editorial.contexto` (uno por ticker) y `editorial.fuentes`.
- **Nunca** `orden`, `datos`, `imagenes`, `anidados`, `laminas` ni `huella`. Están sellados: si
  cambian, la pieza se descarta entera.
- **Nunca** agregues ni quites claves de `editorial`.
- **Ningún otro archivo** del repo. No corras pipelines ni llames al MCP. Usa la web solo para `fuentes`.

### Reglas del texto (de `.agents/rules/proyecto.md`, que manda ante cualquier duda)

1. **Cada cifra sale de `datos`.** No escribas un precio, nivel, porcentaje o dato que no esté en
   `datos`, ni lo redondees a otro valor. El bot rechaza cualquier número con decimales o de tres o
   más dígitos que no encuentre ahí. **Única excepción:** una cifra de un banco o medio que
   aparezca en la `tesis` de una de tus fuentes y que atribuyas a esa entidad en la misma frase
   («Goldman Sachs ve el oro en 4.800 dólares»). Una cifra de tercero sin atribución se rechaza.
2. **Solo afirmas lo medido.** `datos.drivers.<ticker>` trae los drivers del catálogo, `datos.agenda_semana`
   la agenda y `datos.curva` la curva de tasas con sus cambios en puntos base. Un driver se afirma
   como hecho solo si está ahí; si no, se explica como mecanismo condicional. Nunca inventes que el
   dólar, el petróleo o cualquier otro activo "sube" o "se debilita".
3. **Nuestra lectura manda.** La dirección sale de `datos.activos[0].lectura.direccion` (ALCISTA, BAJISTA
   o LATERAL) y el texto la sostiene. Si un banco ve distinto, lo dices abiertamente ("Goldman Sachs ve
   alza; nuestra lectura de los gráficos apunta a la baja"), sin ablandar nuestra lectura.
4. **Español de Chile, tuteo neutro.** Nada de voseo. Tono cercano y pedagógico, sin dramatizar.
5. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
6. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Listas con `• `, párrafos separados por una línea en blanco.
7. **Siglas explicadas en línea** la primera vez.
8. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160; `titulares.<ticker>` hasta 70.
9. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.
10. **Nunca invites a operar.** Por regulación, nadie en GI está inscrito como asesor de inversión.
    No escribas "opera", "operar", "operable", "compra", "vende", "entra" ni "aprovecha", ni "oportunidad" ni "recomendación", ni ninguna
    instrucción personal ni cuánto arriesgar. El bot rechaza esas formas. El cierre comercial
    (revisar la plataforma MT5 con el cliente) lo agrega el bot; tú no lo escribes.
11. **Soporte y resistencia**, nunca "piso", "suelo" ni "techo" para un nivel de precio.

### Qué va en cada campo

`orden.pieza` dice qué pieza es. Solo `oportunidad` pasa por ti: el seguimiento lo escribe Python.

- `titular` y `bajada`: el activo, su dirección y la idea central, sin prometer resultados ni la
  palabra "oportunidad".
- `titulares.<ticker>`: la idea del activo con su dirección.
- `contexto.<ticker>`: 2 o 3 frases con los drivers (`datos.drivers`, `datos.agenda_semana`), como
  mecanismo condicional si no hay un hecho medido, y una frase final que cierre con la lectura:
  qué se vigila y qué la invalida (están en `datos.activos[0].lectura`). Sin `%`, sin repetir los
  niveles (los pone la maqueta).
- `fuentes`: **una lista** (puede ir vacía) de 3 a 5 voces de prestigio sobre este activo. Búscalas en
  la web. Cada elemento es un objeto con estos campos de texto:
  - `entidad`: quién opina. **Solo** de la lista cerrada: Goldman Sachs, JPMorgan, Morgan Stanley, Bank of America, Citi, UBS, Barclays, Standard Chartered, Jefferies, Deutsche Bank, HSBC, ING, Commerzbank, Banco Central de Chile, Cochilco, Banchile, BCI Estudios, Santander Chile, Itaú Chile, Fed, BCE, EIA, OPEP, FMI, BIS, World Gold Council, Agencia Internacional de Energía.
  - `medio`: dónde se publicó. Reuters, Bloomberg, Financial Times, WSJ, CNBC, MarketWatch, Kitco, FXStreet,
    Diario Financiero, La Tercera, o el nombre de la propia entidad si es su sitio. Investing.com no vale.
  - `fecha`: AAAA-MM-DD, de los últimos 14 días.
  - `url`: https y de un artículo concreto (no una portada), del dominio del `medio`.
  - `postura`: `alcista`, `bajista` o `neutral`, la de la entidad frente al activo.
  - `tesis`: una frase en español con lo que la entidad sostiene.
  No inventes URLs ni fuentes: el bot abre cada URL y descarta lo que no responde. Si no encuentras nada
  atingente, deja `fuentes` como lista vacía `[]`. No rellenes.

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

Responde solo `OK` o `ERROR: <motivo>`.
