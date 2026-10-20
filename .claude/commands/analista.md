Redacta los textos del análisis de un activo del bot de analistas. Escribe texto en `pieza.json`: no ejecuta pipelines, no rinde imágenes y no envía nada. La única herramienta externa que usas es la búsqueda web, solo para encontrar las fuentes de `fuentes`.

## /analista — textos del análisis de un activo

**Argumento:** `$ARGUMENTS` es la ruta de un `pieza.json` dentro de `data/informes_analistas/`.
Si no es una ruta así, detente y responde `ERROR: ruta inválida`.

Lo invoca el bot de Telegram (`scripts/bot_analistas.py`). El bot ya leyó el terminal, armó los
datos y rindió el gráfico; tu tarea es redactar y encontrar voces de prestigio. La maqueta es fija
y la pone el bot: tú no decides nada visual.

### Qué puedes tocar

- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  de `editorial.titulares`, `editorial.contexto` y `editorial.dias_clave` (uno por ticker; `dias_clave`
  existe solo si la agenda trae datos) y `editorial.fuentes`.
- **Segundo intento.** Si `editorial.fuentes` es lo único que dice `[[ESCRIBIR]]` y junto a la pieza
  existe `fuentes_intento_1.json`, el primer intento no trajo ninguna voz de banco. Vuelve a incluir
  tal cual las fuentes de `validas`, no repitas ninguna URL de `descartadas` (sus `motivos` dicen por
  qué cayeron) y agrega al menos una de un banco. No toques los demás textos: ya pasaron los controles.
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
2. **Solo afirmas lo medido, y lo medido se cita.** `datos.hechos` trae el estado real de los drivers
   del activo, ya medido por el bot: `driver`, `nivel`, `fecha`, `sentido` y `cambio_5d` (cinco
   sesiones), `efecto` sobre el activo y `con_la_lectura` (si acompaña o va en contra de nuestra
   lectura). `datos.agenda` trae los datos de alto impacto de los 7 días de vigencia, con `dia`, `hora`,
   `esperado`, `anterior` y su `efecto` sobre el activo. `datos.curva` trae la curva de tasas.
   `datos.drivers.<ticker>` es la lista del catálogo: un driver que no está en `datos.hechos` no se
   afirma como hecho. Nunca inventes que el dólar, una tasa o cualquier otro activo "sube" o "baja": el
   `sentido` y el `efecto` ya vienen calculados, úsalos con sus palabras. Di la `fecha` de cada dato: si
   `en_curso` es falso, el dato es de ese día y no de hoy (un sábado, el último cierre es del viernes).
   Si `en_curso` es verdadero, la vela de hoy es parcial: no cites su `cambio_1d` como si fuera un cierre.
3. **Nuestra lectura manda.** La dirección sale de `datos.activos[0].lectura.direccion` (ALCISTA, BAJISTA
   o LATERAL) y el texto la sostiene. Si citas un banco, es uno que coincide con ella: preséntalo como
   confirmación externa. El texto es claro y propone una idea central que el prospecto retiene en segundos:
   una cifra por frase, sin tecnicismos sin traducir y sin tono de organigrama.
4. **Español de Chile, tuteo neutro.** Nada de voseo. Tono cercano y pedagógico, sin dramatizar.
5. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
6. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Listas con `• `, párrafos separados por una línea en blanco.
7. **Siglas explicadas en línea** la primera vez.
8. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160; `titulares.<ticker>` hasta 70.
9. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.
10. **Nunca invites a operar.** Por regulación, nadie en GI está inscrito como asesor de inversión.
    No escribas "opera", "operar", "operable", "comprar", "vender", "entrar", "aprovechar", "se puede comprar"
    ni "conviene vender", ni "oportunidad" ni "recomendación", ni ninguna instrucción personal ni cuánto
    arriesgar. El bot rechaza las formas de "operar", el infinitivo "comprar", "vender" o "entrar" (también
    "comprarlo" o "venderlo"), "aprovechar" y sus formas, "puede/conviene comprar o vender", "oportunidad"
    y las frases de recomendación. No rechaza "compra", "vende" o "entra" sueltos porque aparecen en texto
    legítimo ("gerentes de compra", "entra en vigor"), pero tampoco los uses para empujar a operar: un
    "el mercado vende el dólar" o "el precio entra en zona" se lee como instrucción. El cierre comercial
    (revisar la plataforma MT5 con el cliente) lo agrega el bot; tú no lo escribes.
11. **Soporte y resistencia**, nunca "piso", "suelo" ni "techo" para un nivel de precio.

### Qué va en cada campo

`orden.pieza` dice qué pieza es. Solo `oportunidad` pasa por ti: el seguimiento lo escribe Python.

- `titular` y `bajada`: el activo, su dirección y la idea central, sin prometer resultados ni la
  palabra "oportunidad".
- `titulares.<ticker>`: la idea del activo con su dirección.
- `contexto.<ticker>`: de 3 a 5 frases, en este orden.
  1. Una frase por cada uno de **solo 2** hechos de `datos.hechos`: siempre **1 y 1**, el driver que respalda
     nuestra lectura primero y el que la tensiona después (si no hay de un lado, los dos de movimiento más
     reciente; si eliges otro par, el bot lo rechaza y te dice cuáles), con su cifra tal como viene (`nivel` o `cambio_5d`),
     su fecha y su efecto. Ejemplo: «El Dollar Index (DXY) cerró el viernes 16/10 en 101,560, 0,288
     puntos bajo su nivel de cinco sesiones antes, y eso juega a favor del alza del oro.» Si `efecto` es
     `null`, describe el dato sin atribuirle dirección sobre el activo. Si `con_la_lectura` dice que va
     en contra de nuestra lectura, dilo.
  2. Una frase que jerarquice cuál de esos drivers pesa más hoy y por qué.
  3. Una frase final que cierre con la lectura: qué se vigila y qué la invalida (están en
     `datos.activos[0].lectura`).
  El bot rechaza un `contexto` que no cite la cifra de al menos dos hechos de `datos.hechos` (o del único,
  si hay uno). Sin `%` (las tasas se escriben "2,78 por ciento") y sin repetir los niveles técnicos (los
  pone la maqueta).
- `dias_clave.<ticker>` (solo si existe): de 1 a 3 frases en modo anticipación con los días clave de la
  ventana de `datos.agenda`. Nombra cada día exactamente como viene en `dia` ("miércoles 21/10"), con la
  hora, qué se publica y qué hace con el activo según su `efecto`. Si hay una decisión de tasas, va
  primera; después los que tienen `mueve_al_activo`. Hasta 420 caracteres. El bot rechaza un
  `dias_clave` que no nombre ningún `dia` de la agenda.
- `fuentes`: **una lista** de 1 a 2 voces sobre este activo, exclusivamente de bancos de inversión o bancos
  de Chile de la lista cerrada. **Al menos un banco debe coincidir con nuestra lectura técnica**
  (director, 2026-10-19): el correo, que lee un prospecto, cita solo un banco, el más reciente que la respalda,
  y no muestra a los que ven distinto. Busca primero notas de bancos cuya postura coincide con la nuestra.
  La `postura` y la `tesis` son las que la nota dice de verdad: no estires ni reinterpretes una nota para que
  coincida. Si ningún banco coincide, el análisis no sale. Los organismos (Fed, BCE, EIA, OPEP, FMI, BIS, World Gold Council, Agencia Internacional
  de Energía) no cuentan como banco. Búscalas en la web. Cada elemento es un objeto con estos campos de texto:
  - `entidad`: quién opina. **Solo** bancos de inversión o bancos de Chile de la lista cerrada: Goldman Sachs, JPMorgan, Morgan Stanley, Bank of America, Citi, UBS, Barclays, Standard Chartered, Jefferies, Deutsche Bank, HSBC, ING, Commerzbank, Banco Central de Chile, Cochilco, Banchile, BCI Estudios, Santander Chile, Itaú Chile. (Los organismos no cuentan como banco ni se incluyen).
  - `medio`: dónde se publicó. **Prefiere siempre una nota en español** (el cliente la abre y la lee):
    Bloomberg Línea, Diario Financiero, La Tercera, Emol, Ámbito, Expansión, Cinco Días, El Economista,
    Infobae, Europa Press, o la página en español de la propia entidad (Banchile, Santander Chile, BCI
    Estudios, Banco Central de Chile, Cochilco). Si no hay en español, solo vale un medio muy conocido en
    inglés: Reuters, Bloomberg, Financial Times, WSJ, CNBC o MarketWatch, o el sitio de la propia entidad.
    Antes de citar una nota en inglés, busca si hay una versión en español. Investing.com no vale.
  - `fecha`: AAAA-MM-DD, de los últimos 14 días.
  - `url`: https y de un artículo concreto (no una portada), del dominio del `medio`.
  - `postura`: `alcista`, `bajista` o `neutral`, la de la entidad frente al activo.
  - `tesis`: una frase en español con lo que la entidad sostiene. Sin `%`, sin guion largo ni medio, sin la palabra "oportunidad" y sin "comprar", "vender" ni "recomienda": pasa por los mismos controles que el resto del texto, y la fuente cuya tesis no los pasa se descarta.
  No inventes URLs ni fuentes: el bot abre cada URL y descarta lo que no responde. Sin al menos una de un banco
  válida el análisis no sale, así que busca hasta encontrarla (notas de los últimos 14 días en los medios de la
  lista). No rellenes con voces que no hablan de este activo.

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

La validación también falla si `fuentes` no trae ninguna voz de banco: sigue buscando hasta que diga `OK`.

Responde solo `OK` o `ERROR: <motivo>`.
