# Imágenes por activo — generación con IA

La foto de lingotes que el equipo aprobó define el estándar. Este documento traduce ese look a
parámetros repetibles y a un prompt por activo, para producir material **propio** en vez de
depender de bancos de imágenes.

Por qué generar y no buscar: se revisaron Openverse, Wikimedia y los bancos de dominio público.
Lo que hay con licencia limpia es pobre (barriles de época, salas de servidores de oficina) y lo
que sirve está en CC BY-SA, que obliga a licenciar la pieza derivada bajo la misma licencia —
inaceptable para material de marca.

---

## El look, en seis parámetros

Extraídos de la foto que ya funciona en la pieza:

| Parámetro | Valor |
|---|---|
| **Encuadre** | Plano cerrado. El motivo llena el cuadro; no se ve el objeto entero ni su entorno. |
| **Composición** | Diagonal, nunca frontal. Las líneas entran por una esquina y se pierden en la otra. |
| **Profundidad** | Foco corto: el primer plano nítido y el fondo disuelto. Da escala y deja aire visual. |
| **Luz** | Lateral cálida desde arriba a la izquierda, con caída rápida a negro. Alto contraste. |
| **Fondo** | Negro o casi. Sin cielo, sin pared clara, sin superficie que refleje luz. |
| **Color** | Monocromo alrededor del tono del activo. Nada de escenas policromas. |

El tercio izquierdo del encuadre **va a quedar bajo el texto**, así que ahí no debe haber detalle
que importe. Es el único requisito de composición que impone la plantilla.

---

## Prompt base

Se antepone o concatena a cada motivo:

```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
dramatic warm side lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, 16:9 --no text, watermark, logo, people, hands, faces
```

**Herramienta recomendada: Adobe Firefly.** Está entrenado con stock propio y licencia
explícitamente el uso comercial del resultado, que es lo que necesita una pieza que va a
clientes. Midjourney sirve igual con plan de pago. Canva Magic Media es la opción si ya tienen
Canva. En Midjourney añadir `--ar 16:9 --style raw`.

---

## Prompt por activo

### Oro — XAUUSD
```
stacked gold bullion bars inside a dark bank vault, rows receding into shadow,
warm golden specular reflections on the top faces, dust-free polished metal
```

### Petróleo — WTI.spot
```
row of dark steel oil drums in an industrial storage yard at dusk, amber rim light
along the ribs, oily reflective metal, one drum in sharp focus and the rest dissolving
```

### Nasdaq 100 — US100.spot
```
close-up of server rack GPUs in a dark data center, cyan and violet indicator LEDs,
fiber cables in bokeh, cold blue key light instead of warm
```
Es el único activo donde la luz va **fría**: el motivo es tecnología, no materia prima. El resto
de los parámetros no cambia.

### Dólar / Peso — USDCLP
```
macro close-up of overlapping banknote texture, intaglio engraving detail, warm and cool
split lighting, extreme shallow focus, abstract, no readable text or denomination
```
⚠️ **Dos cuidados en este activo.** La IA escribe texto ilegible sobre los billetes, y una imagen
que parezca moneda real reproducida entra en terreno legal delicado en varios países. Pedir
textura abstracta de grabado, sin cifras ni retratos reconocibles. Si igual sale con texto, se
descarta: no se retoca.

### Cobre — driver del USDCLP
```
stacked polished copper cathode sheets, warm orange-brown reflections,
industrial warehouse dissolving into darkness
```

### Bitcoin — BTCUSD
```
abstract macro of etched circuit-board tracery on a dark metallic surface,
warm amber and orange specular highlights catching the raised lines,
extreme shallow focus, no coins, no symbols, no readable text
```
⚠️ **No pedir una moneda.** Es la trampa de este activo: Bitcoin no existe como objeto
físico, y las "monedas de Bitcoin" son souvenirs. Peor aún para el generador, que llena
el canto de texto grabado y lo saca deformado — la primera imagen que llegó a este repo
traía "BFW MOIACIRY DIETAI S" alrededor del borde y se descartó por eso (además de por
origen desconocido). El motivo correcto es el **circuito**, que es lo que la cosa
realmente es, y comparte lenguaje visual con `tech-circuito.jpg` sin repetirlo: acá la
luz va cálida y ámbar, no fría.

---

## Ampliación para el escaneo del universo (11 imágenes)

Las tandas diarias puntúan las 7 clases de activos, así que la selección puede caer en cualquiera
de ellas. Cada activo que pueda ganar una tanda necesita su imagen. Estas 11 cubren lo que falta.

**Dos reglas que gobiernan esta tanda de prompts:**

1. **Nada de repetir el motivo del vecino.** `us100.jpg` ya es un rack de GPUs, así que ningún
   otro índice puede ser tecnología; `bitcoin.jpg` ya es circuito ámbar, así que ninguna cripto
   puede ser circuito. Si dos piezas comparten motivo, el color por activo deja de servir para
   distinguirlas y se pierde lo único que hace reconocible la pieza antes de leerla.
2. **Un ETF que replica un índice comparte su imagen.** `SPY.US` usa `us500.jpg`, igual que
   `QQQ.US` ya usa `us100.jpg` y `GLD.US` usa `oro.jpg`. Son 11 archivos para 12 activos.

**El nombre del archivo es el `activo_slug`**, sin excepción: `usdjpy` → `usdjpy.jpg` →
`body.activo-usdjpy`. Es lo que permite que el pipeline derive imagen y color del mismo dato.

### Divisas

El prompt de `USDCLP` es textura de billete, y repetirlo tres veces daría cuatro piezas iguales.
Estos tres motivos se apartan del billete a propósito: retratan **el material del dinero o la
herramienta que lo fabrica**, que es igual de honesto y esquiva por completo el riesgo legal de
reproducir moneda circulante.

**USD/JPY** → `usdjpy.jpg`
```
macro of dark lacquered wood surface with inlaid gold leaf seams, deep urushi black,
warm specular highlights following the gold veins, extreme shallow focus
```

**EUR/USD** → `eurusd.jpg`
```
macro of a cold-rolled steel bank vault door mechanism, concentric brushed circular grain,
heavy locking bolts receding into shadow, cool steel-blue key light
```
⚠️ Es el único de los tres con **luz fría**. El motivo es acero, no materia noble. Si sale cálido
se confunde con `gbpusd` y con `us30`.

**GBP/USD** → `gbpusd.jpg`
```
macro of an engraved copperplate intaglio printing die, fine hand-cut line work in bronze metal,
warm raking light across the incised lines, no readable letters or numerals
```
⚠️ La trampa acá es la misma del billete: pedir **líneas grabadas abstractas**, nunca una plancha
con cifras o retratos legibles. Si sale con texto se descarta, no se retoca.

### Índices y ETF de índice

**S&P 500** → `us500.jpg` · sirve también para `SPY.US`
```
macro of a glass curtain wall facade at dusk, receding diagonal grid of dark panels,
cool blue glass with sparse warm interior lights deep in the bokeh
```

**Dow Jones** → `us30.jpg`
```
macro of a forged steel crankshaft and gear train in a dark machine shop,
oiled metal surfaces, warm tungsten side light, heavy industrial mass
```

**Russell 2000** → `iwm.jpg`
```
macro of steel pallet racking in a distribution warehouse, rows receding into darkness,
cool sodium-grey light from above, no boxes with labels
```
El motivo es la empresa mediana doméstica, que es lo que el índice mide. ⚠️ Sin etiquetas ni
cajas rotuladas: es donde el generador inventa texto.

### Criptomonedas

⚠️ **Ninguna lleva moneda**, por la razón que este documento ya explica en Bitcoin: no existen
como objeto físico y el generador llena el canto de texto deformado. Cada una toma el motivo de
**lo que la cosa realmente es o dice ser**, con un tono dominante distinto para que las cinco no
se confundan entre sí ni con `bitcoin.jpg`, que es circuito ámbar.

**Ethereum** → `eth.jpg`
```
macro cluster of faceted obsidian and smoked glass prisms, sharp geometric edges,
cool violet and indigo rim light refracting through the facets, deep black background
```

**Solana** → `sol.jpg`
```
macro of a bundled fiber-optic strand end face, hundreds of lit fiber tips,
magenta and cyan light bleeding from the cores, extreme shallow focus
```

**Litecoin** → `ltc.jpg`
```
macro of a machined silver-grey metal plate, fine parallel tooling grooves catching light,
cool neutral key light, industrial precision surface
```

**Cardano** → `ada.jpg`
```
macro of stacked translucent cobalt blue glass plates seen edge-on, layered depth,
cool blue internal glow along the edges, dark surroundings
```

**Dogecoin** → `doge.jpg`
```
macro of warm amber resin with suspended gold flakes caught mid-swirl,
honey-toned translucency, strong warm side light, abstract
```
⚠️ **Sin perros.** El Shiba Inu es la marca del meme, no el activo, y una imagen de mascota
fecha la pieza y compite con el mensaje igual que una persona. El motivo elegido comunica el
carácter especulativo sin ilustrar el chiste.

### Cuándo se activa un activo

**No rellenar el campo `imagen` de `config/activos.json` hasta que el `.jpg` exista en disco.**
El renderer falla fuerte ante una imagen declarada que no está (es su comportamiento deseado, no
un defecto), y `tests/test_story_render.py` verifica que toda imagen del catálogo exista. Eso
convierte al campo en el interruptor del activo: `imagen` presente ⟺ archivo en disco ⟺ el
escáner de tandas lo considera renderizable. Agregar la línea es el único paso que hace falta
cuando la imagen llega.

---

### Acciones del catálogo
No usar el logo de la empresa (marca registrada de un tercero). Generar el **sector**: chips para
semiconductoras, aviones para aerolíneas, góndolas para retail. Mismo prompt base.

---

## Qué revisar antes de aceptar una imagen

1. **Tercio izquierdo oscuro y sin detalle.** Ahí va el titular.
2. **Cero texto.** Los modelos inventan letras en etiquetas, cajas y billetes. Una imagen con
   texto falso se descarta entera.
3. **Sin personas ni manos.** Fechan la pieza y compiten con el mensaje.
4. **Dedos, reflejos y repeticiones.** Revisar bordes: los patrones repetidos (filas de lingotes,
   racks) son donde los modelos fallan.
5. **El tono dominante coincide con el `--activo`** de la plantilla. Si la imagen sale rosada, no
   sirve por más bonita que esté.

## Sobre "replicar" una foto

Usar la foto de referencia para fijar **estilo** —encuadre, luz, color— es legítimo: un estilo no
se protege. Reproducir una fotografía concreta hasta que sea reconocible, no. Los prompts de este
documento describen el estilo, no la imagen: por eso están escritos en términos de luz y
composición y no de "una foto igual a esta".

## Dónde dejarlas

`templates/stories/assets/activos/<slug>.jpg`, y anotar la procedencia en el README de esa
carpeta. Para las generadas: herramienta, fecha y prompt, que es lo que permite reproducirlas o
defenderlas.
