# Documentos largos: manual, cierre semanal, capacitación y folleto

Cuatro entregables de varias páginas que **no cambian lo que sale hoy a un canal**, y por eso
viven acá y no en `CLAUDE.md`: cada uno tiene su propia maqueta, su compilador y sus trampas
medidas. Lo que sí está en `CLAUDE.md` es que existen y dónde buscarlos.

| Documento | Destinatario | Compilador |
|---|---|---|
| Manual de Operaciones | miembros, por el grupo de avisos | `scripts/compilar_manual_pdf.py` |
| Cierre semanal | el canal, semanal | `scripts/compilar_informe_cierre_semanal.py` |
| Capacitación fundamental (PPTX) | equipo comercial e IBS | `scripts/capacitacion_fundamental_ppt.py` |
| Guía rápida (folleto) | ejecutivos, consulta al teléfono | `scripts/folleto_fundamental.py` |

Todo lo de este archivo se midió contra el resultado real y cada punto costó un defecto: el
manual llegó a tener tres versiones conviviendo, el cierre semanal perdió una ficha entera por
un desborde dentro de una página, y el PPTX se rompía en el PC del destinatario por declarar
fuentes que solo existen como `.woff2`.

---

## Capacitaciones internas (PPTX)

Material formativo para el equipo comercial y los IBS, generado por código para que el
contenido sea versionable y regenerable. Vive en `docs/capacitacion/`.

- **Generador**: `scripts/capacitacion_fundamental_ppt.py` (motor de maqueta) +
  `capacitacion_fundamental_contenido.py` (criterio editorial). La separación es
  deliberada: editar un texto no debe obligar a tocar el dibujo, ni al revés.
  ```bash
  uv run --with python-pptx --with pillow python scripts/capacitacion_fundamental_ppt.py
  ```
  `python-pptx` y `pillow` **no** son dependencias del proyecto: se inyectan con
  `uv run --with` para no alterar el `.venv`.
- **Autoría**: el retrato del autor va en la portada y en el cierre, junto al nombre y
  las credenciales — es material que circula entre equipos, así que quién lo firma se ve
  de entrada. La foto se toma de `docs/capacitacion/assets/autor.png` (o de `--foto
  <ruta>`) y se recorta en círculo con Pillow, porque PowerPoint no aplica máscaras. El
  recorte se hace desde el tercio superior, no del centro geométrico, para no cortar la
  cabeza. Si el archivo no existe, la maqueta cae al diseño sin retrato en vez de fallar.
- **Tipografía**: Segoe UI + Consolas para cifras, **no** las fuentes de marca. Syne /
  DM Sans / Space Grotesk solo existen en el repo como `.woff2` (formato web) y no están
  instaladas en los equipos: declararlas hace que PowerPoint las sustituya y rompa la
  maqueta en el PC de cada destinatario. Consolas preserva el alineado tabular del kit.
- **Medición de texto**: PowerPoint no expone métricas de fuente, así que el motor
  estima el alto de cada bloque antes de dibujar (`_n_lineas` / `_alto_texto`) y reduce
  el tamaño hasta que quepa. Sin eso el layout falla de dos formas ya observadas: un
  título de dos líneas se superpone con el párrafo siguiente, y una tabla larga se
  expande por debajo del pie —PowerPoint ignora `row.height` si el texto no cabe—.
- **Verificación obligatoria**: con decenas de slides la inspección visual no basta.
  ```bash
  uv run --with python-pptx python scripts/verificar_capacitacion.py
  ```
  Detecta desbordes sobre el pie y solapamientos entre bloques de texto. Complementarlo
  exportando a PNG vía COM (`$pres.Export($ruta,"PNG",1600,900)`) para revisar el
  resultado real. **Ojo**: si el director tiene el `.pptx` abierto, `prs.save()` falla
  con `PermissionError` y COM rechaza la conexión con `0x80048240` — generar entonces a
  una ruta temporal y nunca llamar a `$app.Quit()`, que cerraría su sesión.

### Guía rápida (folleto de consulta)

Complemento de la capacitación, para quien no va a estudiar las 55 láminas pero necesita
resolver una pregunta con el cliente al teléfono. No es un resumen: es una **herramienta
de respuesta** —tabla dato → dirección de cada activo, frases listas para el cliente,
qué no decir, y dónde se detiene la respuesta porque pasa a ser asesoría—.

- **Fuente**: `templates/capacitacion/folleto.html` · **Generador**:
  `scripts/folleto_fundamental.py`
  ```bash
  uv run --extra stories python scripts/folleto_fundamental.py
  ```
- **Dos salidas del mismo HTML**: un **HTML autónomo** (fuentes incrustadas en base64,
  se manda por correo o WhatsApp y funciona solo) y un **PDF A4 de 6 páginas** para
  imprimir. Bajo 820 px las hojas A4 se rompen en una columna y las tablas anchas pasan
  a fichas apiladas vía `td[data-rot]::before`, para consultarlo en el teléfono sin
  hacer zoom.
- **Tipografía: DM Sans en todo, también en los títulos.** Las fuentes del repo se
  pueden usar acá y no en el PPTX porque en HTML los `.woff2` funcionan nativamente,
  pero **Syne queda fuera**: en peso 800 sus contraformas se cierran y cansa la vista en
  un documento de consulta (es el mismo defecto que motivó el rediseño de la Story). El
  cuerpo va a 11 pt y no a 9,8 por legibilidad — el material lo usa gente que no lee
  cómodo a tamaños chicos. Space Grotesk queda solo para cifras y siglas.
- **Paleta adaptada al soporte claro**: el verde y el rojo de marca están pensados para
  fondo oscuro y sobre blanco no alcanzan el contraste mínimo para texto (mismo problema
  del footer de las Stories, #145). Se usan versiones oscurecidas para tipografía y los
  originales solo en filetes y fondos.
- **La escala está calibrada al alto útil de una A4** (1123 px a 96 dpi). Si una hoja se
  pasa, Chromium la parte en dos y el PDF duplica páginas —pasó de 3 a 6 sin aviso—. Al
  agregar contenido hay que **medir**, no estimar:
  ```js
  Array.from(document.querySelectorAll('section.hoja')).map(s => s.getBoundingClientRect().height)
  ```
  con `emulate_media("print")`. Y no poner `font-size` dentro de `@media print`: cambia
  la escala justo en el PDF y descuadra la calibración.

## Manual de Operaciones (el que va a los miembros)

`docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md` es un **manual de trading autónomo**,
no una guía de lectura de nuestras piezas. Su propósito (director, 2026-09-04) es que un
miembro **ejecute sus propias operaciones** con el Playbook de guía. Son 12 módulos
autocontenidos y 3 anexos, y sale en PDF A4 al grupo de avisos.

```bash
uv run --extra stories --with markdown-it-py --with pypdf python scripts/compilar_manual_pdf.py
```

**El markdown es la fuente única, y eso hubo que arreglarlo.** El 2026-09-04 había **tres**
documentos: el markdown de 10 secciones, un PDF en disco **truncado a mitad de la sección 6**
(sin riesgo, lotaje, filtros, checklist ni glosario, con el pie numerado sobre 11 páginas y 6
renderizadas), y `compilar_manual_pdf.py` con un cuarto documento escrito adentro en una
constante `HTML_PAGES`, con secciones que el markdown no tenía. Corregir uno no tocaba a los
otros.

Tres reglas del compilador que conviene no revertir:

1. **La paginación es por flujo, no por páginas fijas.** El diseño anterior maquetaba
   `div.a4-page` de 794×1123 con `overflow: hidden`, así que **el contenido que no cabía
   desaparecía sin aviso**. Es el mismo modo de falla del `@media print` del folleto, pero
   silencioso. Ahora Chromium pagina y cada módulo abre página con `break-before`.
2. **El compilador cuenta las páginas y falla bajo `PAGINAS_MINIMAS`.** Un manual al que le
   faltan secciones **se lee como completo**, igual que el mensaje de WhatsApp al que le
   faltaban renglones: nadie lo nota desde afuera, y eso lo hace peor.
3. **Ojo con `hr + h1` en el CSS.** CSS no tiene selector de hermano anterior, y esa regla
   (puesta para ocultar el separador que precede a cada título) **ocultó los 15 títulos de
   módulo** en la primera compilación. El `h1` abre página, así que el `hr` anterior queda al
   final de la anterior y no molesta: solo hace falta `h1 + hr`.

### Lo que el manual afirma tiene que coincidir con el motor

**El manual es el tercer lugar donde viven los umbrales**, después del YAML y el Playbook, y
es el único que un miembro va a usar para arriesgar dinero. La revisión del 2026-09-04 encontró
cinco discrepancias que ya están corregidas, y las tres primeras costaban plata:

| Lo que decía | Lo que hace el motor |
|---|---|
| "Valor Punto (1 lote): $100.000 CLP" | **$100.000 es el valor de 1 PESO** (100 puntos). El punto vale $1.000. Cruzar distancia en pesos con valor del punto da un lote **100 veces mayor** |
| "Spread sobre 15 % del SL bloquea" (3 veces) | `friction_caps` tiene **cinco topes**: 0,15 USDCLP · 0,12 US100 · 0,10 Oro, WTI y Brent |
| "Stop estrictamente 1 tick bajo el mínimo de la vela" | Mínimo de **20 velas** si su distancia cae entre 0,5 y 1,5 ATR; si no, **1,5 × ATR** |
| "TP1 = ganancia 1R" | **1,0 × ATR** (y hay un TP2 a 1,5 × ATR que el manual no mencionaba) |
| Blackout FOMC −30/+60 | **−30/+75** (`screener_gi._BLACKOUTS`) |

Y omitía los gates que de verdad deciden: ancho Donchian ≤ 2,5 ATR, ADX (≥ 20 para pullback,
< 20 para reversión), alineación EMA 20/50/100, rango de vela ≥ 1,0 ATR, RSI no extremo, y
sobre todo **la firma Dow**, que es la confirmación intermercado y le da el nombre al método.

**El protocolo de rachas es criterio de mesa, no salida del motor**, y el módulo 9 lo declara
así en su primer aviso: esos límites (2,5 % simultáneo, 2 pérdidas diarias, 4 % semanal, 0,5 %
tras 3 pérdidas) **no están en el YAML ni en el código**. Presentarlos como cálculo del modelo
era la quinta discrepancia.

> [!CAUTION]
> **`scripts/ticket_engine.py` no lo consume nadie.** Su única mención en el repo es un
> comentario en la docstring de `pipeline_datos.py`. Es el módulo que emitiría la ficha
> completa (entrada, SL, TP, R:R, estado READY/ARMED/BLOCKED/WAIT), y **no está conectado a
> ningún pipeline ni comando**. Lo que sí publicamos es `get_macro_bias`: régimen, sesgo,
> setups permitidos y prohibidos, y distancia de SL.
>
> Por eso el manual enseña al miembro a **construir su propia ficha** y el semáforo es un
> estado que él determina, no uno que recibe. La versión anterior decía "el sistema publica
> fichas de operación" y "la ficha autoriza", prometiendo un producto que no existe.


---

## El manual y el cierre semanal: reglas de maqueta

Dos piezas institucionales de varias páginas, con reglas propias. Todo lo de abajo
se midió el 2026-09-04 y cada punto costó un defecto real, así que conviene leerlo
antes de tocar la maqueta.

### Una sola fuente por documento. Siempre.

| Documento | Fuente del contenido | Compilador | Salida |
|---|---|---|---|
| Manual de Operaciones | `docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md` | `scripts/compilar_manual_pdf.py` | PDF A4, 35 páginas |
| Cierre semanal | `scripts/cierre_semanal_contenido.py` (texto) + `cierre_semanal_datos.py` (cifras) | `scripts/compilar_informe_cierre_semanal.py` | PDF A4, 6 páginas |

**Los dos tenían el documento escrito adentro del compilador y hubo que sacarlo.**
El manual llegó a tener tres versiones distintas conviviendo (el markdown, un PDF
truncado en disco, y un cuarto documento dentro del script). El cierre semanal
tenía las rutas clavadas a una fecha, así que correrlo una semana después
regeneraba el informe anterior.

Si necesitas cambiar un texto, cambia la fuente. **Nunca escribas contenido dentro
del compilador**: a la segunda copia una queda atrás y nadie se entera hasta que
sale una pieza mal.

### El manual pagina por FLUJO. No lo vuelvas a páginas fijas.

`compilar_manual_pdf.py` deja que Chromium pagine, y cada módulo abre página con
`break-before: page`. El diseño anterior maquetaba `div.a4-page` de 794×1123 con
`overflow: hidden`, y **el contenido que no cabía desaparecía sin aviso**: así el
PDF que estaba en disco perdió la mitad operativa (riesgo, lotaje, filtros,
checklist y glosario) mostrando su pie numerado sobre 11 páginas con solo 6
renderizadas.

Tres reglas del CSS que no se tocan:

1. **`main h1 + hr` sí, `hr + h1` NO.** CSS no tiene selector de hermano anterior.
   La regla `hr + h1 { display: none }` parece razonable para ocultar el separador
   que precede a cada título y en realidad **oculta el título**: se comió los 15
   encabezados de módulo en la primera compilación. El `h1` abre página, así que el
   `hr` anterior queda al final de la anterior y no molesta.
2. **`break-inside: avoid`** en tablas, avisos, bloques de código y los envoltorios
   de los diagramas (`div[style*="justify-content: center"]`). Un diagrama partido
   entre dos páginas es ilegible.
3. **El compilador cuenta las páginas y falla bajo `PAGINAS_MINIMAS`.** No bajes ese
   número para que pase: un manual al que le faltan secciones **se lee como
   completo**, y nadie lo nota desde afuera.

### Los ejemplos de cada clima se derivan, no se escriben

La sección 3.5 fecha cuándo ocurrió cada uno de los cinco climas, con sus cifras y un
gráfico de dos líneas. **Nada de eso está escrito a mano**, y no podría estarlo: un
gráfico con la serie inventada tendría aspecto institucional y números que nadie midió,
que es el defecto de `generar_graficos_drivers.py`.

La cadena tiene tres pasos y cada uno es reproducible:

```bash
# 1. una vez: la historia larga de las series (queda en su propio archivo)
uv run python .agents/skills/ecosistema-datos-macro/scripts/extractor_usa.py --historico
uv run python .agents/skills/ecosistema-datos-macro/scripts/extractor_commodities.py --historico
# 2. corre el clasificador DEL MOTOR sobre esa historia
uv run python scripts/regimenes_historicos.py
# 3. dibuja los gráficos y reescribe la sección del manual entre sus marcas
uv run python scripts/grafico_regimen_svg.py --escribir
```

Cuatro decisiones que conviene no revertir:

1. **El relleno histórico va a archivos aparte** (`curva_fred_historico.json`,
   `commodities_historico.json`). Los archivos de la ingesta diaria se reescriben enteros
   y se commitean con cada corrida, así que meterles medio siglo de historia dejaría un
   blob de megabytes por día en el repo. Mismo criterio que las series intradía
   gitignoreadas de `DATA PRECIOS OHLC`: lo que se reescribe seguido tiene que ser
   liviano.
2. **La clasificación no se reimplementa.** `regimenes_historicos.py` importa
   `evaluar_regimen_candidato` y `aplicar_histeresis` del motor. Una segunda
   implementación de los umbrales sería un cuarto lugar donde viven.
3. **Para clasificar el día D solo se miran datos anteriores o iguales a D.** El motor
   calcula sus deltas sobre los últimos 5 registros *disponibles*, no sobre días de
   calendario, así que el recorte tiene que ser por fecha. Mirar el dato de mañana para
   clasificar el ayer es el anacronismo que el proyecto persigue en los textos, cometido
   con números.
4. **La elección del episodio es editorial y está declarada con su motivo** en
   `EPISODIOS`; las cifras son medidas. Cada clima tiene decenas de episodios y se
   publica uno por criterio de enseñanza.

**El límite es la tasa real.** `DFII10` y `T10YIE` empiezan en FRED el 2003-01-02, así que
la corrida cubre 5.951 días hábiles hasta hoy. Ahí salió además una cifra que el manual
usa: el clima Calma es el **64,8 %** de los días, lo que respalda que "no hay operación"
sea el resultado más frecuente del método.

### Los diagramas no llevan líneas en blanco adentro. Nunca.

Los 8 diagramas son SVG escritos a mano en el markdown, y **una línea en blanco
adentro de un `<svg>` cierra el bloque de HTML crudo de CommonMark**. Lo que
decide entonces si el diagrama sobrevive es qué hay en el renglón siguiente, y
ahí está lo que engaña: si es una etiqueta que se cierra sola y ocupa la línea
entera (`<line/>`, `<rect/>`), markdown-it abre otro bloque, el navegador ve
marcado contiguo y el dibujo se salva **de pura suerte**. Cualquier otra cosa cae
en un párrafo, y ese `<p>` cierra el `<svg>`: los rótulos se dibujan como texto
corriente al costado de una tarjeta muda.

Medido el 2026-09-07: **2 de los 8 diagramas partidos** (la vela H1 del módulo 1
y el setup 5.1), con **18 de los 87 rótulos** derramados. El compilador terminaba
en código 0 y contaba bien sus páginas; se descubrió mirando el PDF. Es el mismo
modo de falla del `overflow: hidden` de la maqueta vieja.

Lo sanea `compactar_svg` en el compilador, y no en el markdown, para que la
fuente siga siendo legible. Lo impone `tests/test_manual_diagramas.py`.

**Ojo al diagnosticarlo**: buscar `"<p"` dentro del bloque da un falso positivo
en cada `<polygon>` y cada `<path>`. La condición se prueba con la etiqueta
cerrada (`</?p>`).

### El cierre semanal sí usa páginas fijas, y por eso mide su alto.

Acá `.a4-page` es de 1123 px con `overflow: hidden`, que es el diseño aprobado. El
riesgo es el mismo de siempre y se controla midiendo: `_medir_desbordes` calcula el
alto natural de cada página en el DOM y **aborta si alguna se pasa**.

Sin esa medición, el primer armado puso cuatro fichas en una página y **la ficha del
yen desapareció entera**. El control de "salieron las páginas esperadas" no lo
detectó, porque el desborde fue *dentro* de una página.

- **Máximo dos fichas de activo por página** (`PAGINAS_ACTIVOS`). Si agregas
  contenido, corre el compilador y mira la línea `Altos:`; el margen actual ronda
  los 300 px por página.
- **Ojo con `scrollHeight` del contenedor**: `.a4-page` es flex con
  `space-between`, así que los hijos se comprimen y el valor queda clavado en el
  alto de la página. Hay que medir el alto natural de cada hijo, filtrando los
  `position: absolute` porque la portada lleva una capa de brillo que falsea la suma.

### El brand kit existe y estos dos documentos todavía NO lo usan.

`brand_atomic_system/agent/visual/` tiene los tokens CSS, las especificaciones de
componentes, los specimens, la tipografía y los assets. Medido: `compilar_manual_pdf.py`
y `cierre_semanal_estilo.py` tienen **cero referencias** al kit. Su paleta y su
tipografía están escritas a mano.

Eso es deuda conocida, no una decisión. Al trabajar la parte visual, **el kit manda**:
alinea los colores y la tipografía a sus tokens en vez de conservar los valores
escritos a mano. Si un token del kit contradice lo que hay, gana el kit; si el kit no
cubre un caso, dilo en vez de inventar un valor.

Dos cosas que no son negociables aunque el kit no las mencione:

- **Verde arriba y rojo abajo** en variaciones de precio. Es una convención que el
  cliente lee sin pensar, no una decisión de marca.
- **Contraste real sobre cada fondo.** El rojo y el verde de marca están pensados para
  fondo claro: sobre la portada oscura no alcanzan y el texto se pierde. Ya pasó con el
  rótulo "AVISO DE RIESGO" de la portada del manual y con el encabezado de una tabla,
  donde el `strong` global pintaba oscuro sobre fondo oscuro.

### Cómo verificar antes de dar por bueno

```bash
# Manual: 31 paginas, y falla si perdio secciones
uv run --extra stories --with markdown-it-py --with pypdf python scripts/compilar_manual_pdf.py

# Cierre semanal: 6 paginas, informa el alto de cada una y aborta si desborda
uv run --extra informe --extra stories --with MetaTrader5 --with pypdf \
    python scripts/compilar_informe_cierre_semanal.py

# La suite completa
uv run pytest -q
```

**Los dos compiladores abortan solos si algo se rompió.** Si uno falla, la salida
dice qué medir; no bajes el umbral para que pase.

Y revisa el PDF resultante, no solo que compile: abre un par de páginas y mira que
los títulos estén, que ningún bloque quede partido y que el texto se lea sobre su
fondo.

### Reglas de texto que aplican a los dos

Son las mismas reglas de tono y de decimales del proyecto, y acá se verifican así:

- **Cero guiones largos** (`—`) y medios (`–`) como inciso. El punto medio `·` sí se
  mantiene: es separador visual de marca, no puntuación de frase.
- **Notación chilena** en toda cifra: miles con punto, decimales con coma.
- **El Cobre se escribe entero**, sin separador de miles (`$14386 USD/t`), porque es
  el único con `digits = 0` y el punto se confundiría con el decimal inglés.
- **Toda sigla se explica** la primera vez que aparece.

---

