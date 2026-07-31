# Solicitud de plantillas al equipo de Marketing — Stories GI

> Documento doble: el **cuerpo del correo** para Rodrigo Bartierra y el **anexo** con lo que
> aprendimos conectando plantillas a datos reales. El correo se pega en el cuerpo del mail;
> el anexo va como documento aparte.
>
> **Tono del anexo (decisión del director, 2026-07-30)**: está escrito como *hallazgos
> nuestros*, no como especificación que marketing deba acatar. El diseño es su oficio; lo
> nuestro es la operativa y lo que descubrimos al llevar el diseño a producción. Mantener
> esa voz en cualquier edición futura.
>
> **Atribución (decisión del director, 2026-07-31)**: el documento distingue explícitamente el
> origen de cada parte. La **operativa y el marco normativo** son aporte del director; los
> **hallazgos de plantillas y diseño**, y el anexo completo, se atribuyen al asistente de IA con
> el que se desarrolló el generador. El director pidió esta transparencia de forma expresa. Dos
> lugares la declaran: la introducción de los hallazgos en el correo y la nota de procedencia al
> inicio del anexo. Mantenerla en cualquier edición futura y no diluirla — además de honestidad,
> guarda coherencia con la declaración de apoyo automatizado que le pedimos a las piezas.
>
> **Reparto normativo (decisión del director, 2026-07-31)**: el marco normativo lo asume
> **nuestra área**, no marketing y no el director a título personal — él no es la jefatura del
> área, aunque sí el único con la acreditación de conocimientos del mercado de valores (CMV), y
> actúa como contraparte técnica. Marketing recibe requisitos ya resueltos. Ninguna edición
> futura debe pedirle a marketing que defina el encuadre normativo ni atribuir la decisión
> formal al director a título individual.
>
> **Calificación adoptada (2026-07-31, tras investigación documental)**: **la señal operativa se
> trata como asesoría de inversión.** Fundamento: la definición chilena alcanza servicios
> prestados "por cualquier medio, al público general o a sectores específicos de él" y **no
> exige personalización** —un grupo cerrado de clientes es un sector específico—; y el criterio
> internacional es de sustancia sobre forma, así que renombrar "señal" como "idea de trading" no
> altera la calificación. Consecuencia para las plantillas: son obligatorios el nombre del
> analista que firma, los fundamentos técnicos, la declaración de conflictos de interés, la
> declaración de apoyo automatizado y —en piezas de resultado— la advertencia de resultados
> pasados. Base: Ley 21.314 art. 3° (derogado y reemplazado por la Ley Fintec 21.521), NCG 472 y
> NCG 412. **Pendiente de verificación por el director**: situación registral de GI SpA y quién
> figura como emisor acreditado.
>
> Mantener sincronizado con `templates/stories/` y `scripts/story_render.py`.

---

## CUERPO DEL CORREO

**Asunto:** Plantillas para señales — propuesta de trabajo con el Grupo de Análisis de Mercado

Hola Rodrigo,

Te escribo para proponerte una forma de trabajo entre tu equipo y el nuestro, y para
pedirte dos plantillas concretas que hoy nos están frenando.

**Dónde estamos**

Tenemos funcionando un generador de piezas gráficas que toma datos reales del mercado
—precios, niveles técnicos, resultados de operaciones, calendario económico— y produce
imágenes listas para publicar en segundos, sin que nadie edite nada a mano.

Ese generador ya se apoya en el trabajo de ustedes: el lenguaje visual que usamos —la
paleta, las tipografías, la estructura de las piezas— lo tomamos de tu proyecto de Claude
Design, y sobre esa base fuimos armando siete plantillas para poder conectarlas a nuestros
datos.

Y ahí está la asimetría que quiero plantearte: **el lenguaje visual es de ustedes, pero la
implementación la venimos haciendo nosotros.** Las plantillas funcionan, pero cada decisión
de composición que tomamos —cuánto pesa un titular, cómo respira un bloque, qué jerarquía
tiene un dato— la estamos tomando desde el lado equivocado del equipo. El diseño no es
nuestro oficio. Es el de ustedes.

No te propongo empezar algo nuevo, entonces, sino formalizar en la dirección correcta algo
que ya está pasando.

**La división que propongo**

- **Ustedes** diseñan la plantilla: composición, jerarquía visual, tipografía, color,
  respiración. Dueños de cómo se ve la marca.
- **Nosotros** conectamos los datos: de dónde sale cada número, con cuántos decimales, en
  qué unidad y con qué criterio operativo.
- **El contrato entre ambos** son marcadores dentro del archivo. Donde ustedes hoy
  escribirían un precio de ejemplo, escriben `{{precio_entrada}}`, y nuestro motor pone el
  dato real al generar la pieza.

Una vez conectada, la plantilla se usa indefinidamente sin volver a pasar por diseño.
Ustedes la tocan cuando quieran evolucionar la marca, no cada vez que publicamos.

---

**Sobre el marco normativo: lo tomamos nosotros**

Antes de entrar en las piezas quiero despejarte lo que probablemente sea lo primero que te
inquiete al leer que vamos a publicar operaciones y sus resultados: **el marco normativo lo
asumimos desde nuestra área, y a ustedes les llegan los requisitos ya resueltos.**

Te comparto primero la conclusión a la que llegamos, porque define todo lo demás: **tratamos
la señal operativa como asesoría de inversión.** No es una postura conservadora nuestra, es lo
que se desprende de la normativa vigente:

- La definición chilena de asesoría de inversión alcanza la prestación de servicios "por
  cualquier medio, al público general **o a sectores específicos de él**" relacionados con la
  inversión en instrumentos financieros. **No exige que la recomendación sea personalizada**,
  de modo que un grupo cerrado de clientes es un sector específico del público.
- **El rótulo no cambia la calificación.** Llamarlo "idea de trading" en vez de "señal" no
  altera nada: lo que se evalúa es si la comunicación puede entenderse como un llamado a
  operar un instrumento determinado. Con entrada, objetivo, stop y volumen, lo es.

Así que no buscamos una etiqueta que lo evite: cumplimos. Y eso se traduce en elementos
concretos que la plantilla tiene que incorporar, que te adelanto porque son campos de diseño y
no letra chica:

1. **El nombre de quien elabora la recomendación** debe estar visible. La pieza la firma una
   persona identificable, no "el equipo".
2. **Los fundamentos técnicos que la sustentan** deben acompañarla. Por eso los tres puntos de
   análisis dejan de ser un adorno editorial: son obligatorios.
3. **Los potenciales conflictos de interés** deben declararse cuando la recomendación se
   distribuye ampliamente.
4. **Si el análisis se apoya en procesos automatizados** —y el nuestro usa un motor que calcula
   niveles e indicadores— hay que declararlo e indicar quién lo desarrolló.
5. **Los datos cuantitativos deben ir contextualizados** y las advertencias tienen que ser
   legibles y prominentes, con tamaño apropiado al medio.

Fíjate que los puntos 4 y 5 son exactamente los dos hallazgos de diseño que te menciono más
abajo —el capital de referencia y el contraste del aviso de riesgo—. Los descubrimos por el
lado del oficio y resultaron ser requisitos normativos. Buena señal de que vamos bien
encaminados.

**Y una razón que quizás les interese más que el cumplimiento en sí.** La CMF está publicando
alertas sobre plataformas no reguladas que operan justamente por WhatsApp y Telegram
prometiendo ganancias rápidas. Nosotros hablamos por el mismo canal y al mismo cliente. Lo
único que nos distingue de eso, a ojos de esa persona, es el cumplimiento visible: el analista
que firma, los fundamentos declarados, las advertencias legibles, los resultados
contextualizados. Dicho de otro modo: **los elementos normativos no son lastre que haya que
disimular en el diseño — son nuestro principal diferenciador y conviene que se vean.** Ahí hay
una oportunidad de marca que me gustaría que exploraran.

Sobre mi rol: cuento con la acreditación de conocimientos del mercado de valores (CMV) y soy
quien lleva este tema en nuestra área, así que cuenten conmigo como contraparte directa para
cualquier duda del tipo "¿esto se puede decir?" o "¿esto se puede mostrar?" — la respondo en el
momento y sin que tengan que escalarla. La validación formal la gestionamos por nuestro lado
con quien corresponda en GI; ustedes reciben los requisitos ya resueltos y se concentran en el
diseño.

---

**Lo que necesitamos primero: la señal y su resultado**

De todo el conjunto, hay dos piezas que necesitamos con prioridad real, y son
complementarias entre sí.

**1. La señal operativa.** Hoy la enviamos por escrito, en texto. Es la pieza más
importante que produce el equipo y la que más se reenvía. Lo que lleva:

- **Nombre del activo**, legible y en español ("Dólar / Yen japonés"). Cuando el tipo de
  contrato importe —un CFD y no el activo subyacente, por ejemplo— nos interesa poder decirlo
  en palabras, porque cambia costos y comportamiento para el cliente.
- **El número de operación (ticket).** Este es el que te quiero explicar con detalle, porque
  visualmente parece un dato prescindible y cumple una función que ningún otro elemento
  cubre. Es el identificador que la terminal de la mesa operativa le asigna a la orden cuando
  se ejecuta. **Funciona como comprobante: es la prueba de que lo que estamos comunicando es
  una orden real ejecutada, y no una simulación, un ejemplo didáctico ni un escenario
  hipotético.**

  Su valor no depende de que el cliente lo consulte —él no tiene acceso a la terminal de la
  mesa—, igual que el folio de una boleta no vale porque uno lo verifique, sino porque *es
  verificable si hiciera falta*. Y le da a post-venta una herramienta concreta: si un cliente
  cuestiona un resultado, hay un número que cruzar contra el registro real de la mesa en vez
  de una explicación.

  Con una condición de diseño que nos parece importante: **el número tiene que ir acompañado
  de la vía para consultarlo.** Como el cliente no puede llegar por su cuenta, mostrar un
  identificador sin decir a quién preguntar es peor que no mostrarlo —insinúa una
  verificación que no puede completar—. Basta que quede junto al contacto del analista
  designado, que ya es el cierre habitual de nuestras piezas. Puede ir en jerarquía
  secundaria y cuerpo chico; lo que necesitamos es que esté, que se pueda leer y que no quede
  huérfano del canal.
- Dirección: compra o venta
- Precio de entrada
- Volumen de la operación
- Objetivo de toma de ganancia y stop de protección
- **Lo que se gana y lo que se arriesga, traducido a pesos chilenos** — el cliente no debería
  tener que calcular nada
- **El capital de referencia sobre el que están calculados esos pesos.** Este campo es
  obligatorio y necesita un lugar propio en el diseño. Un monto suelto no es interpretable:
  "+$657.000" puede parecer extraordinario o modesto según el capital que el lector imagine,
  y en ambos casos lo estaríamos induciendo a una conclusión que no dimos. Declarando el
  capital, la cifra se vuelve proporcional, verificable y además accionable —el cliente puede
  escalarla a lo suyo—. Nos importa tanto por transparencia como por precisión: es la
  diferencia entre informar un resultado y sugerir una expectativa.
- **La temporalidad y su horizonte**, que para nosotros es información crítica y hoy se
  pierde en el texto. Manejamos cuatro y cada una implica un compromiso de tiempo distinto
  para el cliente:
  - *Scalper* — de minutos a un par de horas
  - *Intradía* — dentro de la jornada
  - *Swing de jornada* — de uno a tres días
  - *Posicional* — de días a semanas
- **Los fundamentos técnicos**: hasta tres puntos de análisis que sustentan la operación. Como
  te decía arriba, son obligatorios por normativa, así que necesitan un lugar asegurado en la
  composición y no un espacio que se sacrifique cuando el resto crece.
- **La firma del analista**: nombre de quien elabora la recomendación. También obligatorio, y
  además creemos que suma —una pieza firmada por una persona pesa más que una pieza
  institucional—.
- **La declaración de apoyo automatizado**: nuestro análisis se apoya en un motor que calcula
  niveles e indicadores, y eso debe declararse. Puede ser una línea en el pie.
- **La declaración de conflictos de interés** y **el aviso de riesgo**: textos fijos que les
  entregamos redactados.

Ese bloque de temporalidad y horizonte es donde más nos gustaría su criterio visual. Un
cliente que entra a una operación de minutos y una que compromete semanas necesitan
entender la diferencia **antes** de entrar, y en un texto corrido eso se diluye. En una
imagen bien jerarquizada, no.

**2. La pieza complemento: el resultado de esa señal.** Cuando la operación cierra,
comunicamos qué pasó. Es la pieza que construye credibilidad, porque cierra el círculo de
lo que prometimos.

Acá necesitamos su criterio más que en ninguna otra, y por varias razones:

- **El nombre y el encuadre comunicacional son de ustedes; los requisitos normativos se los
  entregamos resueltos.** Cómo se llama la pieza, cómo se estructura, qué jerarquía tiene cada
  dato y cómo se ve, es terreno suyo. Qué se puede afirmar, qué advertencias son obligatorias y
  cómo evitamos que se lea como promesa de rendimiento futuro, lo llevamos nosotros. Aportamos
  además la operativa: qué se operó, a qué precio, con qué resultado y en cuánto tiempo.
- **Lleva los mismos elementos normativos que la señal** —analista que firma, fundamentos,
  conflictos de interés, declaración de apoyo automatizado— más la advertencia de que
  resultados pasados no garantizan resultados futuros, que en esta pieza es ineludible.
- **Esta es la pieza donde más van a necesitar consultarnos, y está bien que sea así.**
  Comunicar resultados es lo más sensible del conjunto. Preferimos que nos pregunten diez veces
  durante el diseño a descubrir un problema con la pieza ya publicada.
- **Nos gustaría que post-venta la vea antes de que salga.** No como aprobadores, sino como
  consultados: son los que van a recibir las preguntas que genere la pieza —"si ganaron eso,
  ¿por qué yo no?"— y en dos minutos pueden señalar qué frase se malinterpreta. Si no
  participan del diseño, la pieza les crea trabajo evitable.
- **La necesitamos en dos variantes: operación ganadora y operación perdedora.** Y esto es lo
  que más nos importa de todo el encargo, así que te lo argumento. Publicar solo los cierres
  en ganancia hace que cada pieza sea verdadera y el conjunto comunique algo falso: es sesgo
  de selección, y es exactamente lo que la publicidad financiera vigila —no la veracidad de
  cada dato, sino la representatividad del conjunto—. La consecuencia de diseño es concreta:
  **si la variante perdedora se ve rota o desprolija, nadie va a querer mandarla, y en la
  práctica vamos a publicar solo verdes sin habértelo propuesto nunca.** El diseño termina
  determinando la conducta. Lo que les pedimos es que la operación en pérdida tenga el mismo
  cuidado y el mismo peso visual que la ganadora, con la misma dignidad. Eso es lo que
  sostiene la credibilidad a doce meses.
- **El capital de referencia también va acá**, por lo mismo que en la señal: un resultado en
  pesos sin el capital sobre el que se calculó no es interpretable.
- **Tenemos un prototipo, y justamente por eso queremos que lo hagan ustedes.** Armamos una
  versión funcional de esta pieza y la iteramos varias veces con datos reales: incluye la
  operación, su resultado en pesos y un gráfico del recorrido del precio con los hitos
  marcados. Funciona, pero se nota que la hizo un equipo técnico —y, dicho sea de paso, nunca
  la probamos en su variante perdedora, que es el punto anterior mordiéndonos a nosotros
  mismos—. Se lo puedo mostrar en la reunión como punto de partida, o como ejemplo de lo que
  no hay que hacer si su criterio es otro.

---

**El horizonte, para que vean hacia dónde va esto**

El objetivo de fondo es simple de enunciar: **todo lo que hoy comunicamos por escrito en
WhatsApp debería poder salir en imagen.** Ese es el trabajo diario del equipo, y hoy vive
en mensajes de texto que compiten con todo lo demás en el teléfono del cliente.

El mapa completo, además de las dos anteriores:

| Pieza | Qué comunica |
|---|---|
| Niveles del día | Soportes, resistencias y sesgo del activo |
| Dato económico | Un indicador macro: qué se esperaba, qué salió y a quién afecta |
| Noticia relevante | El hecho del día que mueve un activo |
| Alerta | Algo que está pasando ahora y requiere atención |
| Actualización de mercado | Cómo evolucionó el precio frente a los niveles que dimos |
| Concepto educativo | Un concepto explicado para quien recién aprende |
| Encuesta | Sentimiento del grupo sobre un activo |
| Cierre semanal | Resumen de la semana |
| Calendario semanal | Los eventos que vienen |
| Resultados de empresas | Calendario de reportes corporativos |

No las necesitamos todas ahora. Las menciono para que cuando diseñen las dos primeras
sepan que van a ser parte de un sistema, y que conviene que compartan estructura entre
ellas.

---

**Lo que aprendimos llevando su diseño a producción**

Antes de entrar, quiero ser transparente sobre de dónde viene cada parte de este correo. El
marco normativo, la calificación de la señal como asesoría y todo lo relativo a la operativa lo
aporto yo desde nuestra área. **Los hallazgos sobre las plantillas y el diseño que siguen —y
todo el anexo— no son míos**: salieron del trabajo con el asistente de inteligencia artificial
con el que desarrollamos el generador, iterando las piezas y detectando los problemas al
renderizarlas con datos reales.

Lo aclaro por dos razones. La primera es simple honestidad: no me voy a atribuir un trabajo de
diseño que no hice, y ustedes merecen saber con qué criterio se formaron esas conclusiones. La
segunda es de coherencia — si les estamos pidiendo que declaremos en las piezas que nuestro
análisis se apoya en procesos automatizados, lo mínimo es aplicar el mismo estándar acá.

Dicho eso, el espíritu de los hallazgos, porque probablemente para ustedes varios sean obvios
—pero a nosotros nos costaron correcciones—:

1. **Una tipográfica display no aguanta cifras.** Estábamos usando Syne 800 —la de los
   titulares— también para los precios. A tamaño grande sus contornos internos casi se
   cierran y los dígitos se empastan: `163.444` se volvía difícil de leer. Nos lo hizo notar
   una persona externa diciendo que la fuente "se perdía como en un agujero negro".
   Terminamos separando: Syne solo en titulares, y todas las cifras en una tipográfica de
   datos.

2. **Un recurso visual puede volver ambiguo un número.** Marcábamos con tachado los niveles
   que el precio ya había superado, y el tachado cruzaba los dígitos: `163.501` se leía
   `463.504`. En una pieza que publica precios eso deja de ser un detalle estético.

3. **El espacio vacío conviene que comunique algo.** En una versión nos quedaron unos 700
   píxeles de aire que no decían nada. Lo resolvimos haciendo que la distancia entre los
   niveles del gráfico fuera proporcional a la distancia real de precio: el espacio pasó de
   relleno a información.

4. **Es fácil repetir sin darse cuenta.** Una de nuestras piezas terminó afirmando cuatro
   veces el mismo hecho en cuatro lugares distintos, y mostrando los mismos dos precios en
   dos componentes. No estaba cargada de datos: estaba cargada de repetición.

5. **Un texto legal ilegible no cumple su función.** Nuestro aviso de riesgo por
   apalancamiento estaba en un gris que no alcanzaba el mínimo de contraste accesible.

El resto del anexo es de la misma naturaleza, más algunas restricciones que vienen de cómo
funciona nuestro generador y no de criterio de diseño: el archivo se renderiza sin conexión
a internet, así que no puede depender de fuentes o imágenes externas; y como el texto lo
escribe el mercado y no el diseñador, el largo real varía más que en una maqueta.

---

**Cómo nos lo pueden entregar**

En una línea: **un archivo HTML autocontenido por plantilla, con los datos variables
marcados, que sirva en horizontal y en vertical.**

Entiendo que si trabajan en Figma o Canva, entregar HTML puede no ser parte de su flujo.
Hay dos caminos y ninguno es problema:

- **Camino A (el que preferimos):** nos entregan el archivo HTML armado. Se conecta en horas
  y ustedes mantienen control del resultado final hasta el píxel. Si les acomoda, puede
  vivir en tu propio proyecto de Claude Design —seguimos trabajando donde ya estamos— y
  desde ahí lo tomamos.
- **Camino B:** nos entregan el diseño más su documentación exacta —paleta con códigos,
  escala tipográfica, grillas, espaciados, estados de color— y nosotros implementamos el
  archivo. Es lo que venimos haciendo hasta hoy, así que sabemos que funciona; la diferencia
  sería que la documentación viniera completa de entrada en vez de que la dedujéramos del
  canvas. Requiere que validen el resultado antes de publicar.

Dinos cuál les acomoda y adaptamos el anexo.

---

**Mi propuesta para arrancar**

**Hagamos solo la señal.** La diseñan, la conectamos de punta a punta y les mostramos la
pieza generada con datos reales de una operación. Con eso van a ver exactamente qué
controlan ustedes y qué controlamos nosotros, y ajustamos el contrato antes de escalar al
resto. Es media hora de reunión y una plantilla.

Con la señal funcionando, la pieza de resultado sale casi sola, porque comparte casi todos
los datos.

Quedo atento a lo que les acomode.

Saludos,

---
---

## ANEXO — Lo que aprendimos conectando plantillas a datos reales

> Esto no es una especificación que haya que acatar: es la lista de cosas que nos fallaron o
> nos sorprendieron al llevar plantillas a producción con datos reales, más las
> restricciones que impone nuestro generador. Lo compartimos para ahorrarles el camino que
> ya hicimos. Donde el criterio de diseño de ustedes diga otra cosa, manda el suyo — salvo
> en los puntos que marcamos como restricción técnica, que son los que harían que la pieza
> no se pueda generar.
>
> **Procedencia**: este anexo lo elaboró el asistente de inteligencia artificial con el que
> desarrollamos el generador de piezas, a partir de iterar las plantillas y detectar los
> problemas al renderizarlas con datos reales. No es trabajo de diseño de nuestra área ni
> pretende serlo; lo revisamos y lo hacemos nuestro como pedido, pero corresponde que sepan con
> qué criterio se formó. Los requisitos normativos que aparecen en las secciones 7 y 11 sí
> provienen de nuestra área.

### 0. Cómo se usa lo que nos entreguen

El archivo se abre en un navegador sin interfaz (Chromium automatizado) que lo carga
localmente desde el disco, **sin acceso a internet**, y le toma una captura del tamaño exacto
del lienzo. Antes de la captura, nuestro motor reemplaza los marcadores por datos reales. No
hay servidor ni proceso de compilación.

De ahí sale la prueba más simple: **si el archivo se ve bien al abrirlo con doble clic en un
navegador y sin conexión, se va a ver bien en la pieza final.**

---

### 1. El archivo — restricciones de nuestro generador

Esta sección sí es técnica: son las condiciones para que la pieza se pueda generar.

| Condición | Por qué |
|---|---|
| Un archivo `.html` autocontenido por plantilla | Es la unidad que nuestro motor procesa |
| CSS embebido en un `<style>` del `<head>` | No cargamos archivos `.css` externos |
| Sin JavaScript | La captura es estática; nada que dependa de scripts va a ejecutarse |
| Sin recursos externos | No hay red al renderizar: un CDN, Google Fonts o una imagen por URL quedan en blanco |
| Fuentes como `.woff2` locales en una carpeta `fonts/` | Misma razón |
| Imágenes fijas embebidas como `data:` URI o archivo local | Misma razón |

Un detalle que nos costó descubrir: conviene `font-display: block` en cada `@font-face`. Con
el valor por defecto, la captura puede dispararse antes de que la fuente termine de cargar y
la pieza sale con la tipografía de reemplazo.

```css
@font-face {
  font-family: "Syne";
  src: url("fonts/syne-800.woff2") format("woff2");
  font-weight: 800;
  font-display: block;
}
```

---

### 2. Los marcadores de datos

Donde va un dato que cambia en cada pieza, un marcador en lugar del texto de ejemplo.

**Dato simple** — `{{nombre}}`, minúsculas con guion bajo:

```html
<h1 class="titular">{{titular}}</h1>
<span class="precio">{{precio_entrada}}</span>
```

**Lista de largo variable** — para tablas o enumeraciones:

```html
<!-- FOR:filas -->
<div class="fila">
  <span class="fila-activo">{{activo}}</span>
  <span class="fila-valor">{{valor}}</span>
</div>
<!-- ENDFOR:filas -->
```

Lo que está entre las marcas se repite una vez por elemento; lo que deba aparecer una sola
vez —el encabezado de una tabla— va fuera. Soporta un nivel: sin listas dentro de listas.

**Bloque opcional** — algo que a veces aparece:

```html
<!-- IF:variacion -->
<span class="variacion">{{variacion_pct}}%</span>
<!-- ENDIF:variacion -->
```

**Cuatro cosas que aprendimos sobre esto:**

1. **Los nombres son el contrato.** `{{precio_entrada}}` y no `{{texto_3}}`. Si el nombre
   cambia después, hay que cambiar código de nuestro lado.
2. **Ningún dato variable puede quedar fijo.** Si en la maqueta queda `4.539,72`, ese número
   sale en todas las piezas para siempre.
3. **Si un marcador queda sin dato, la generación falla.** Es a propósito: preferimos que
   falle a publicar una pieza con un hueco. Por eso conviene no dejar marcadores "por si
   acaso".
4. **La sintaxis de los marcadores no puede aparecer dentro de comentarios HTML.** Esto nos
   rompió una plantilla completa: documentamos un `FOR` de ejemplo en un comentario de
   cabecera y nuestro motor —que busca las marcas por texto en todo el archivo— abrió ahí la
   lista y la cerró al final del documento, tragándose la página entera. Si van a documentar
   algo dentro del archivo, mejor describirlo en palabras.

Para campos que pueden llegar vacíos, nos funcionó que el contenedor colapse solo:

```css
.subtitulo:empty { display: none; }
```

---

### 3. Un archivo para los dos formatos

Necesitamos cada plantilla en **horizontal 1920×1080** y **vertical 1080×1920**. La vertical
es la que se ve en el teléfono y hoy es la más usada.

Empezamos con dos archivos separados y no funcionó: se desfasan. Se corrige un texto en uno
y se olvida en el otro. Lo que nos resultó es **un archivo que se adapta**:

```css
/* Base: horizontal */
html, body {
  width: 100vw;              /* y no 1920px fijo */
  height: 100vh;
}

/* Vertical: se activa cuando el lienzo es más alto que ancho */
@media (max-aspect-ratio: 1/1) {
  .titular { font-size: 54px; }
}
```

Dos cosas de nuestra experiencia:

- **Fijar el tamaño en píxeles en `html`/`body` rompe el mecanismo.** El tamaño lo impone el
  lienzo.
- **La tipografía sube bastante en vertical, y no de forma proporcional.** Un cuerpo que
  funciona en 1920 de ancho queda diminuto en 1080, porque el vertical se mira en un
  teléfono a un tamaño físico mucho menor.

---

### 4. Tipografía y cifras

Lo que terminamos adoptando fueron dos roles separados:

| Rol | Dónde | Qué nos resultó |
|---|---|---|
| **Display** | Titulares, y solo titulares | Acá va la personalidad de marca |
| **Datos** | Todo número: precios, montos, porcentajes, horas | Dígitos inequívocos y `font-variant-numeric: tabular-nums` |

`tabular-nums` hace que todos los dígitos ocupen el mismo ancho. Sin eso, dos precios en
columna no se alinean y una cifra que se actualiza "baila" entre piezas.

**Lo que nos falló concretamente:**

- Una display en cifras. Si a 100px un `0` y un `8` se parecen, en la pieza final se
  confunden.
- `text-decoration: line-through` sobre un número. Para marcar algo como superado nos
  funcionó color u opacidad, nunca tachado.
- Tracking negativo agresivo en cifras.

La jerarquía con la que terminamos decidiendo: **un número mal leído es peor que un número
ausente.**

---

### 5. El texto real es más largo que el de la maqueta

Este es el que más nos ha mordido, y es propio de nuestro caso: los textos los genera el
análisis del día, no el diseñador.

Lo que nos ayudaría:

1. **Que nos digan el rango.** Por cada campo de texto, con qué largo funciona el diseño:
   "el titular se ve bien entre 25 y 55 caracteres". Nos ajustamos a ese rango, pero
   necesitamos conocerlo.
2. **Probar con el caso más largo.** A nosotros nos pasó que un titular de tres líneas se
   dibujó encima del logo y del aviso legal en la versión vertical, y solo apareció al
   generar con datos reales.
3. Lo que usamos para contenerlo: que el bloque de contenido recorte su excedente en vez de
   desbordarse, con el pie de marca **fuera** de ese bloque para que nada lo pise.

```css
.contenido { flex: 1; min-height: 0; overflow: hidden; }
```

---

### 6. Color con significado

En nuestras piezas los colores de dirección de mercado no son decorativos:

| Significado | Uso |
|---|---|
| Verde | Alza, ganancia, objetivo cumplido |
| Rojo | Baja, pérdida, riesgo |
| Ámbar o neutro | Espera, sin confirmación |
| Gris | Dato inactivo o ya superado |

Lo que necesitamos para poder conectarlos: **que vengan como clases aplicables** y no como
color fijo del componente, porque el mismo elemento muestra verde o rojo según el dato del
día.

```css
.sesgo-alcista .variacion { color: #00DC82; }
.sesgo-bajista .variacion { color: #E84040; }
```

Nuestro motor pone la clase en el elemento raíz. Si el color está fijo en el componente, la
plantilla sirve para la mitad de los casos.

---

### 7. Accesibilidad y avisos obligatorios

- **Contraste de 4,5:1 hacia arriba** en todo texto. Nos importa especialmente en los textos
  chicos, porque en estas piezas los chicos son los legales.
- **El aviso de riesgo por apalancamiento (CFD)** va en toda pieza dirigida a clientes y
  tiene que poder leerse. Ya lo tuvimos que corregir una vez por quedar bajo el mínimo de
  contraste.
- **Pie de marca**: handle, dominio y el aviso legal.
- Las piezas de **uso interno** llevan un distintivo visible de "no reenviar al cliente" y no
  llevan pie de marca comercial. Si alguna plantilla es interna, se lo indicamos.

**Bloque normativo en piezas de recomendación.** Las piezas de señal y de resultado llevan
además cuatro elementos que la normativa exige y que conviene tratar como un bloque de diseño
con identidad propia, en vez de resolverlos como letra chica dispersa:

| Elemento | Nota |
|---|---|
| Analista que firma | Nombre de la persona que emite la recomendación |
| Fundamentos técnicos | Los puntos de análisis que la sustentan |
| Declaración de apoyo automatizado | Nuestro análisis usa un motor que calcula niveles e indicadores |
| Conflictos de interés | Texto fijo que entregamos redactado |

Nuestra sugerencia —y es una invitación, no un requisito—: en vez de esconderlos, **tratarlos
como sello de respaldo**. En un canal donde circulan plataformas no reguladas prometiendo
ganancias rápidas, una pieza que muestra quién firma y en qué se basa es un diferenciador de
marca, no una carga.

En la pieza de **resultado de operaciones** este punto es el más sensible. Dos cosas que para
nosotros no son negociables, y que fijamos como criterio propio:

- **Todo monto en pesos va acompañado de su capital de referencia.** Un resultado sin la base
  sobre la que se calculó no informa: sugiere.
- **La variante de operación en pérdida tiene que verse tan bien como la ganadora**, porque de
  eso depende que se publique, y de que se publique depende que el conjunto de lo que
  mostramos sea representativo.

El resto de los requisitos normativos de esa pieza —qué se puede afirmar, qué advertencias son
obligatorias, cómo se califica lo que estamos comunicando— los entrega nuestro lado ya
resueltos, junto con el diseño. La pregunta de si algo se puede decir o mostrar tiene una vía
directa y se responde en el momento; no hace falta escalarla.

---

### 8. Lo que en nuestra experiencia no llega a la pieza final

- JavaScript, animaciones, transiciones, estados hover: la captura es una imagen fija.
- Datos verosímiles como texto fijo. Nos confunde el contrato: no sabemos si un número es un
  ejemplo o algo que debe quedar.
- Copy que interprete un dato de mercado. Tenemos reglas propias sobre tono, sobre no
  prometer resultados y sobre cómo se nombra un hecho no confirmado —de hecho tuvimos que
  corregir una pieza que afirmaba en indicativo algo que aún no estaba confirmado
  oficialmente—. Ustedes definen el espacio y la jerarquía del texto; el texto lo escribimos
  nosotros con ese filtro.
- Gráficos con datos dibujados a mano. Si la pieza lleva un gráfico, nos basta el
  **contenedor** con su estilo: el trazado lo genera nuestro motor con datos reales. Un
  detalle si lo hacen en SVG: conviene declarar la proporción del contenedor, porque un SVG
  cuya proporción no calza con su caja deja franjas vacías arriba y abajo. Nos pasó.

---

### 9. El checklist que usamos nosotros

No es un criterio de aprobación de ustedes hacia nosotros: es la lista con la que nosotros
revisamos una pieza antes de darla por lista. La compartimos por si les sirve.

- [ ] Se abre con doble clic en un navegador, **sin conexión**, y se ve completa
- [ ] Ningún recurso externo
- [ ] Cero JavaScript
- [ ] Todo dato variable es un marcador con nombre semántico
- [ ] Ningún dato de ejemplo quedó fijo
- [ ] Correcta en **1920×1080** y **1080×1920**, mismo archivo
- [ ] Probada con el texto más largo del rango, sin desbordes
- [ ] Ninguna cifra en tipográfica display ni con tachado
- [ ] Cifras con `tabular-nums`
- [ ] Todo texto sobre 4,5:1 de contraste, incluido el legal
- [ ] Pie de marca presente y sin nada que lo pise
- [ ] Rangos de caracteres documentados por campo
- [ ] Colores semánticos como clases aplicables
- [ ] Número de operación presente, legible y junto a la vía de consulta
- [ ] Símbolo de plataforma solo en la variante interna, no en la de cliente
- [ ] Todo monto en pesos acompañado de su capital de referencia
- [ ] En piezas de resultado: la variante en pérdida se ve tan cuidada como la de ganancia
- [ ] En piezas de recomendación: analista que firma, fundamentos técnicos, declaración de
      apoyo automatizado y conflictos de interés, todos presentes y legibles
- [ ] En piezas de resultado: advertencia de que resultados pasados no garantizan resultados
      futuros

---

### 10. Qué les devolvemos

1. La **pieza generada con datos reales** en los dos formatos, para que la validen contra su
   diseño.
2. La **lista final de marcadores** con qué dato entra en cada uno, así diseñan las
   siguientes sin preguntarnos.
3. Si al conectar aparece un problema —de los que solo salen con datos reales— se lo
   reportamos con la captura y la causa, no como "no funciona".

---

### 11. Las dos primeras plantillas, en detalle

#### 11.1 Señal operativa — prioridad 1

| Dato | Formato | Nota |
|---|---|---|
| Activo | Nombre legible en español | Ej. "Dólar / Yen japonés". Si el tipo de contrato importa, poder decirlo en palabras |
| **Número de operación (ticket)** | Identificador de la orden | **Funciona como comprobante**: prueba que es una orden real ejecutada y no un ejemplo. El cliente no accede a la terminal de la mesa, así que **debe ir junto a la vía de consulta** (el contacto del analista) — un identificador sin canal insinúa una verificación que el cliente no puede completar. Jerarquía secundaria, cuerpo chico, pero legible |
| Símbolo de plataforma | Ej. `USDJPY`, `WTI.spot` | **Solo en la variante interna.** Es operativo para la mesa y los ejecutivos; para el cliente sin terminal no cumple función y además no es universal fuera de nuestro broker |
| Dirección | Compra o venta | Color semántico |
| Precio de entrada | Decimales fijos por activo | La cantidad de decimales la define el activo y no se puede alterar ni redondear |
| Volumen | Lotes | Ej. "0.62 lotes" |
| Objetivo | Precio | |
| Stop de protección | Precio | |
| Ganancia potencial | Pesos chilenos | El cliente no debería calcular nada |
| Pérdida potencial | Pesos chilenos | |
| **Capital de referencia** | Pesos chilenos | **Obligatorio siempre que se muestre un monto o proyección en pesos.** Necesita lugar propio: sin él, la cifra no es interpretable y puede inducir a una expectativa que no dimos |
| Temporalidad | Una de cuatro | Scalper / intradía / swing de jornada / posicional |
| Horizonte | Rango de tiempo | Minutos a 1-2 h / la jornada / 1-3 días / días a semanas |
| **Fundamentos técnicos** | Hasta 3 puntos breves | **Obligatorios por normativa.** Necesitan lugar asegurado, no un espacio que se sacrifique cuando el resto crece |
| **Analista que firma** | Nombre de la persona | **Obligatorio por normativa**: la recomendación la emite una persona identificable, no "el equipo" |
| **Apoyo automatizado** | Texto fijo | **Obligatorio por normativa** cuando el análisis se apoya en procesos automatizados, como es nuestro caso. Puede ser una línea en el pie |
| **Conflictos de interés** | Texto fijo | **Obligatorio por normativa** en recomendaciones de distribución amplia. Se los entregamos redactado |
| Aviso de riesgo | Texto fijo | |

Dos bloques donde más nos interesa su criterio:

- **Temporalidad y horizonte.** Un cliente tiene que entender antes de entrar si la operación
  le compromete dos horas o tres semanas. En texto corrido eso se pierde; en una imagen bien
  jerarquizada, no.
- **Monto en pesos junto a su capital de referencia.** Van juntos o no van. La tentación de
  diseño es agrandar el monto y esconder el capital, porque el monto es más atractivo; para
  nosotros eso es justamente lo que hay que evitar.

#### 11.2 Resultado de la operación — prioridad 2

Comparte casi todos los datos de la señal —incluidos el **número de operación** y el
**capital de referencia**, y acá el número pesa todavía más: es la pieza que afirma un
resultado, así que el comprobante de que la orden existió es parte del argumento— y agrega:

| Dato | Formato | Nota |
|---|---|---|
| Precio de cierre | Decimales del activo | |
| Resultado | Pesos chilenos | Siempre acompañado del capital de referencia |
| Recorrido capturado | En la moneda del par | Ojo: la distancia entre precios va en la moneda del par (en USD/JPY, yenes); los pesos son solo para el resultado. Mezclarlas confunde, y ya nos costó una corrección pública |
| Tiempo hasta el cierre | Ej. "menos de 14 horas" | |
| Si el stop se activó o no | | |
| Gráfico del recorrido | Contenedor; el trazado lo generamos nosotros | |
| **Resultados pasados** | Texto fijo | Advertencia de que no garantizan resultados futuros. En esta pieza es ineludible |

**Dos variantes del mismo diseño, con el mismo cuidado:**

| Variante | Cuándo | Requisito |
|---|---|---|
| Operación en ganancia | El objetivo se alcanzó | |
| **Operación en pérdida** | El stop se activó | **Mismo peso visual y misma prolijidad que la ganadora.** Si esta variante se ve rota, en la práctica no se publica, y publicar solo las ganadoras vuelve engañoso al conjunto aunque cada pieza sea verdadera |

**El nombre y la estructura de esta pieza los definen ustedes; el criterio normativo lo entrego
yo resuelto** (ver el bloque correspondiente en el correo). Nosotros aportamos qué se operó, a
qué precio, con qué resultado y en cuánto tiempo, más los requisitos concretos que la pieza
tenga que cumplir. Sugerimos además que post-venta la revise como consultado: son los que
reciben las preguntas que la pieza genera y detectan en dos minutos qué frase se malinterpreta.
