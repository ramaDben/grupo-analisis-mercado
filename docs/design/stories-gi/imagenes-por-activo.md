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

**USD/JPY** → `usdjpy.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
dramatic warm amber and cool neon lighting, rapid falloff into deep black background,
high contrast, cinematic color grading, Tokyo financial district high-rise towers at night,
illuminated glass architecture reflecting warm city glow, deep shadows, 16:9 --no text, watermark, logo, people, hands, faces
```

**EUR/USD** → `eurusd.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
cool steel-blue and navy lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, European Central Bank modern angular glass and steel architectural facade at twilight,
reflective dark panels, heavy institutional presence, 16:9 --no text, watermark, logo, people, hands, faces
```

**GBP/USD** → `gbpusd.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
dramatic warm amber raking light from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, monumental neoclassical stone fluted pillars and classical cornice facade of the Bank of England at night,
deep shadows, textured Portland stone, 16:9 --no text, watermark, logo, people, hands, faces
```

### Índices y ETF de índice

**S&P 500** → `us500.jpg` · sirve también para `SPY.US`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
rapid falloff into deep black background, high contrast, cinematic color grading,
modern glass curtain wall skyscraper facade at dusk, receding diagonal grid of dark reflective panels,
cool blue glass with sparse warm interior lights deep in the bokeh, 16:9 --no text, watermark, logo, people, hands, faces
```

**Dow Jones** → `us30.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
dramatic warm golden side lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, monumental neoclassical colonnade of the New York Stock Exchange building on Wall Street at night,
textured stone pillars receding into darkness, 16:9 --no text, watermark, logo, people, hands, faces
```

**Russell 2000** → `iwm.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
industrial cool blue and amber LED lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, modern automated logistics distribution hub,
robotic conveyor transport lines in dark warehouse, high tech industrial operations, 16:9 --no text, watermark, logo, people, hands, faces, boxes with labels
```

### Criptomonedas

**Ethereum** → `eth.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
cool violet and deep indigo neon rim lighting from upper left, rapid falloff into pitch black background,
high contrast, cinematic color grading, geometric faceted octahedron crystal prism made of smoked glass and dark titanium,
luminescent ultraviolet glowing edges, abstract digital cryptography motif, 16:9 --no text, watermark, logo, people, hands, faces
```

**Solana** → `sol.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
glowing vibrant cyan and magenta gradient LED lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, ultra high speed microchip processor mounted on dark matte black carbon surface,
glowing neon cyan and purple data bus traces, high tech blockchain engine, 16:9 --no text, watermark, logo, people, hands, faces
```

**Litecoin** → `ltc.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
cool crisp silver and steel rim light from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, solid brushed silver bullion ingot with laser-etched precision cryptographic micro-circuit lines,
polished metallic chamfered edges, dark mirror reflections, 16:9 --no text, watermark, logo, people, hands, faces
```

**Cardano** → `ada.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
intense cobalt blue and royal blue luminescence from upper left, rapid falloff into pure black background,
high contrast, cinematic color grading, 3D interconnected geometric network lattice of glowing cobalt blue nodes and crystal filaments,
abstract blockchain topology, mathematical precision, 16:9 --no text, watermark, logo, people, hands, faces
```

**Dogecoin** → `doge.jpg`
```
photorealistic macro photograph, tight crop, diagonal composition, shallow depth of field,
dramatic warm golden side lighting from upper left, rapid falloff into deep black background,
high contrast, cinematic color grading, heavy solid gold cryptocurrency coin medallion resting on dark textured slate stone,
macro close up of polished gold rim and raised geometric minting relief, warm golden specular sheen, 16:9 --no text, watermark, logo, people, hands, faces
```

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
