# Verificación de afirmaciones sobre Tori Trades

## V1 · qLtq73bTPBA [51:00]

- **Pregunta:** ¿Entra mientras la vela todavía está perforando la línea, o espera a que la vela cierre al otro lado? ¿En qué temporalidad está el gráfico de la entrada?
- **Modelo:** AGY gemini-3-flash-preview

**Respuesta:** Tori entra en la operación en el momento en que la vela está **perforando la línea** (mientras se está rompiendo), sin esperar a que la vela cierre al otro lado. El gráfico de entrada está en una temporalidad de **5 minutos**.

**Cita:** 
* [51:00] "Price moving up, it is breaking through this downward trendline. This is telling us to take action, to place a trade."
* [51:16] "This is indicating an entry because our action line has now been broken."

**Se ve:** 
* **Temporalidad:** En la esquina superior izquierda de TradingView se lee "Light Crude Oil Futures · 5 · NYMEX", donde el "5" indica velas de 5 minutos.
* **Acción del precio:** Se observa una vela verde (alcista) en formación que está atravesando físicamente la línea de tendencia descendente roja superior. Tori hace clic en el botón de "Buy" (Compra) en el panel de Paper Trading en el segundo [51:22], justo cuando la punta de la vela cruza la línea; la vela aún no ha terminado de formarse ni ha cerrado.
* **Herramientas:** Se ven múltiples líneas de tendencia (rojas para resistencia/bajistas y verdes para soporte/alcistas). Se utiliza la función de "Replay" de TradingView para simular el movimiento del mercado.

**Seguridad:** Alta

---

## V2 · q4t71xxbDsY [16:16]

- **Pregunta:** ¿Qué dice que cuenta como ruptura de la línea: el cierre de la vela al otro lado o el simple cruce del precio?
- **Modelo:** AGY gemini-3-flash-preview

Respuesta: Tori Trades indica que la ruptura se produce cuando el precio realiza un movimiento y **cruza** (en inglés, "crosses") las líneas de tendencia en temporalidades mayores. No menciona explícitamente en este tramo que sea necesario esperar al cierre de la vela para validar la ruptura, sino que se refiere específicamente al cruce del precio.

Cita: "And when price makes a move and crosses these trendlines on my higher timeframes, it holds so much more weight." [16:53]

Se ve: 
* **Plataforma:** Interfaz de TradeZella (herramienta de diario de trading).
* **Temporalidad:** El gráfico muestra explícitamente "4h" en la esquina superior izquierda [16:44].
* **Gráfico:** Velas japonesas con una línea de tendencia descendente de color rojo que tiene más de tres puntos de contacto.
* **Herramientas/Marcadores:** Se observa una pequeña flecha o punto verde en el gráfico que marca la entrada ("Long"), situada justo después de que el precio supera la línea roja.
* **Panel de datos:** A la izquierda se ve el resumen de la operación: Ganancia (Net P&L) de $34,721.00, 20 contratos operados y el nombre de la estrategia "3+ Touchpoint Break...".

Seguridad: Alta (basada en el uso literal del verbo "crosses" por parte de la ponente).

---

## V3 · cTecm-uk8FA [07:33]

- **Pregunta:** ¿Qué dice sobre esperar el cierre de la vela de 1 hora antes de entrar en mercados volátiles? ¿Qué hace ella finalmente?
- **Modelo:** AGY gemini-3-flash-preview

**Respuesta:**
Tori explica que esperar al cierre de la vela de 1 hora es una opción válida, pero advierte que en ciertas condiciones de mercado, el precio puede moverse tan rápido y tan lejos del punto de entrada ideal que el trader podría perderse todo el movimiento por el simple hecho de esperar el cierre. Por lo tanto, ella enfatiza la importancia de ser consciente de las condiciones actuales. Finalmente, ella decide entrar "a mercado" (market order) en cuanto se produce la ruptura, sin esperar a que la vela de una hora se complete.

**Cita:**
* [07:19] "You can do either one. This is a one-hour time frame, so waiting for the candle to close is an option, obviously, it's a possibility, you can totally do it. But keep in mind, we need to be very aware of the type of conditions that we are in. If we're waiting for an entire candle to close, an entire one-hour candle to close, price could move so fast, so far from your entry that you might miss the entire move by simply waiting for the candle to close."
* [07:55] "So, I'm going to enter at market..."

**Se ve:**
* **Plataforma:** Interfaz de Tradovate integrada con TradingView.
* **Activo y Temporalidad:** Micro Crude Oil (MCL) en gráfico de 1 hora (1H).
* **Elementos del gráfico:** Una línea de tendencia descendente roja que actúa como resistencia y un canal ascendente delimitado por líneas verdes. Se observa una vela verde rompiendo la línea roja hacia arriba.
* **Acción de trading:** A partir de [07:55], se despliega el panel de órdenes a la derecha. Se muestra seleccionada la opción "Market" y el botón "BUY". En el gráfico aparecen líneas de ejecución: una línea verde de "Profit target" y una línea roja de "Stop-loss" que ella ajusta arrastrándola según la estructura del mercado.

**Seguridad:** Alta

---

## V4 · Kffx9mc_aLY [05:51]

- **Pregunta:** ¿Dice que no opera rupturas de líneas con solo 2 toques? ¿Por qué?
- **Modelo:** AGY gemini-3-flash-preview

Respuesta: Sí, ella afirma que entrar en una ruptura de línea de tendencia con solo 2 puntos de contacto es insuficiente para su estrategia habitual. Explica que no suele hacerlo (o que no debería haberlo hecho en este caso) porque **dos puntos de contacto no proporcionan una confirmación lo suficientemente fuerte** para validar la configuración, lo que reduce su confianza en la operación. En este video específico, califica este comportamiento como un error derivado del FOMO (*miedo a quedarse fuera*).

Cita: 
* "[05:52] I entered on a trendline break but it only had two touchpoints. That was not enough information to provide a strong confirmation for me."
* "[06:01] It didn't really meet all of my requirements, all of my credentials to enter the trade. It didn't give me as much confirmation or confidence. I simply entered with two touchpoints on a trendline."

Se ve: En la pantalla se muestra la interfaz de **TradeZella** (una herramienta de diario de trading). En la sección de "Setup Details" (Detalles de la Configuración), el primer punto de texto indica: *"Trendline Break: Entered on a trendline break that only had two touchpoints—not enough to provide strong confirmation."* El gráfico analizado es del futuro del **Platino (PLJ24)** en una temporalidad de **4 horas (4h)**. Se observa una línea de tendencia descendente de color azul y una serie de velas japonesas que muestran una caída prolongada previa al punto de entrada.

Seguridad: Alta

---

## V5 · Y_Ney-Fp5T4 [05:27]

- **Pregunta:** ¿Qué es el setup "2 Touchpoint Break"? ¿Lo considera válido para operar y cómo lo compara con el de 3 toques?
- **Modelo:** AGY gemini-3-flash-preview

**Respuesta:** El setup "2 Touchpoint Break" consiste en ejecutar una operación (en este caso, una posición en largo) cuando el precio rompe una línea de tendencia que ha sido validada por exactamente dos puntos de contacto previos. Aunque Tori lo considera un setup operable y obtuvo beneficios con él en este ejemplo, no lo considera su ideal. Lo describe como una decisión "apresurada" (rushed decision) motivada por el "FOMO" (miedo a quedarse fuera) al no haber operado en la primera mitad del mes. En comparación, prefiere el setup de 3 toques ("3 touchpoint break") porque considera que tres puntos proporcionan "suficiente información" para validar la tendencia antes de la rotura.

**Cita:** 
* [05:36] "This right here was a two touchpoint break. I went long after the price broke this downward trendline that had two touchpoints."
* [06:21] "This was a little bit of a... I'd say a rushed decision. Ideally, I like a three touchpoint trendline break. I want enough information..."

**Se ve:** 
* **Plataforma:** Interfaz de TradeZella mostrando el seguimiento de una operación en el activo PLJ24 (Futuros de Platino).
* **Temporalidad:** Gráfico de 4 horas (4h) visible en la parte superior izquierda del panel del gráfico.
* **Elementos del gráfico:** 
    * Una línea de tendencia descendente de color rojo con dos círculos rojos que marcan los "touchpoints" (puntos de contacto).
    * Una flecha verde que indica la rotura al alza de dicha línea.
    * Iconos de ejecución: Un círculo verde con el símbolo "play" marca la entrada en 913.99 y un círculo rojo con el símbolo "stop" marca la salida en 935.40.
    * Una línea horizontal amarilla que actúa como resistencia en el nivel de 938.88.
    * Una línea de tendencia alcista verde (etiquetada como "safety line" en el discurso).
* **Panel de estadísticas:** Indica un beneficio neto de $10,688.00, 10 contratos operados y 2141.0 ticks capturados. En la sección "Playbook", se lee claramente "2 Touchpoint Break".

**Seguridad:** Alta

---

## V6 · qsjLmbVNlCc [12:44]

- **Pregunta:** ¿Cómo califica una línea de 2 toques frente a una de 3 toques, y qué papel tiene la semana de datos?
- **Modelo:** AGY gemini-3-flash-preview

Respuesta: Ella califica una configuración con una línea de tendencia de solo 2 puntos de toque como un "A- minus setup" (configuración de grado A-). Explica que el hecho de no tener 3 puntos de toque y no contar con al menos una semana de datos la sitúa en esa categoría inferior (en comparación con un setup A+), a pesar de que sigue siendo un escenario de riesgo increíblemente bajo.

Cita: "This is almost we're going to call this like a... an A- minus setup. No it doesn't have three touch points. I don't even think it's got a week's worth of data. But incredibly low risk scenario here..." [12:44]

Se ve: 
- Una pantalla de TradingView mostrando el gráfico de "Light Crude Oil Futures" (CL1!) en una temporalidad de 4 horas (4h).
- En el gráfico se observa una línea de tendencia bajista de color rojo que une dos máximos decrecientes.
- También se ven líneas horizontales de soporte y resistencia (amarillas y moradas) y una línea de tendencia alcista verde.
- El cursor resalta el periodo de tiempo en el eje X, abarcando desde el jueves 27 de junio hasta el domingo 30 de junio de 2019.
- A la derecha hay un panel de "Watchlist" con varios futuros financieros.

Seguridad: Alta

---

## V7 · gokPlEnlhuE [13:06]

- **Pregunta:** ¿Entra en un rebote sobre la línea, sin que la línea se rompa? ¿Qué condiciones pide para esa entrada?
- **Modelo:** AGY gemini-3-flash-preview

**Respuesta:** Sí, Tori Trades entra en un rebote sobre la línea basándose en el concepto de "rechazo" (rejection). La condición técnica para la entrada es que el precio llegue "a o cerca" de una de las líneas trazadas durante el análisis (que ella denomina "piso" o "techo") y que el precio reaccione rebotando en ella. Específicamente, para una línea de tendencia alcista, la condición es que el precio "respete" la línea y muestre un rechazo alcista para colocar una orden de compra.

**Cita:**
* [13:05] "If it gets at or near one of these lines, it is our indication to take action and to get into a trade."
* [13:11] "Price has just finally made it to one of these lines. That is our indication to take action... it’s time to finally place an order."
* [13:23] "It will all be dependent on the bouncy ball rejecting off of the floor or the ceiling... the upward trendline or the downward trendline."
* [13:43] "We're anticipating that every time the price comes down to this line, it's going to reject... and respect this upward trendline."

**Se ve:** 
En la pantalla de TradingView se muestra el gráfico de Futuros de Oro (**GC1!**) en una **temporalidad de 1 hora (1H)**. El gráfico presenta una estructura de canales con una línea roja superior (resistencia/techo) y una línea verde inferior (soporte/piso). Alrededor del minuto [13:11], el cursor señala exactamente el punto donde una vela japonesa toca la línea de tendencia verde ascendente. Se observa cómo ella identifica ese contacto como el disparador para una "buy order" (orden de compra), asumiendo que la línea no se romperá, sino que el precio "rebotará" como una pelota hacia arriba siguiendo la dirección de la tendencia previa.

**Seguridad:** Alta

---

## V8 · xRxUo3_9XRA [00:52]

- **Pregunta:** ¿Dice que la ruptura de una línea en 5 minutos es una entrada válida? ¿Es la temporalidad que ella opera o un ejemplo?
- **Modelo:** AGY gemini-3-flash-preview

Respuesta: Sí, Tori Trades afirma explícitamente que la ruptura de una línea de tendencia en una temporalidad de 5 minutos es una entrada válida para ella, incluso si solo tiene dos puntos de contacto. No lo presenta como un mero ejemplo, sino que es la temporalidad en la que está operando activamente en ese momento para su evaluación de Apex.

Cita: 
- [00:44] "I took a short position based on the break of this trendline."
- [00:47] "We're in a five-minute timeframe so I am apt to taking trendline breaks on five-minute timeframes with only two touchpoints."

Se ve: En la pantalla se muestra la interfaz de TradingView con el gráfico de futuros de petróleo crudo (CL1!). En la esquina superior izquierda se aprecia claramente seleccionada la temporalidad de 5 minutos ("5m"). En el gráfico hay dibujada una línea de tendencia alcista de color verde con dos puntos de apoyo marcados con círculos blancos. El precio ha roto esa línea hacia abajo y se observa un cuadro rojo de posición corta activa ("-1") con el beneficio/pérdida fluctuando en tiempo real.

Seguridad: Alta

---

## V9 · pasWNYvY4TA [14:48]

- **Pregunta:** ¿Dónde pone el stop respecto de la línea de seguridad y cuánto margen deja? ¿Da algún criterio para el tamaño del margen?
- **Modelo:** AGY gemini-3-flash-preview

**Respuesta:** Tori Trades indica que el stop loss **no debe colocarse ni sobre ni en la misma línea de seguridad**, ya que es probable que el precio la toque o incluso la traspase ligeramente con una mecha ("wick"). Recomienda dejar un margen de maniobra ("wiggle room") para permitir estos toques sin ser sacado del mercado prematuramente. El criterio técnico para determinar este margen es el **tamaño de la posición**: afirma que la posición debe ser lo suficientemente pequeña para que el trader pueda permitirse ese espacio adicional de stop sin comprometer su gestión de riesgo.

**Citas:**
*   **[14:33]:** "Make sure that you are trading small enough position size that you can allow price to actually hit the safety line."
*   **[14:44]:** "If you are placing your stop losses on or at the safety line, that is your issue. We anticipate that the price is going to hit the line and we even anticipate that the price is going to even ever so slightly poke through it."
*   **[15:30]:** "Make sure position sizing is small enough that you can allow wiggle room, price to hit the line, poke through the line, get a small wick here, before getting stopped out of your position."

**Se ve:** 
El gráfico de TradingView muestra el par **BTCUSD (Bitcoin / U.S. Dollar)** en una temporalidad de **1 hora (1h)** del exchange Bitstamp. En la pantalla se aprecian varias líneas de tendencia manuales: una línea roja descendente principal (resistencia) y varias líneas verdes ascendentes que actúan como soporte ("safety lines"). Tori utiliza la herramienta de dibujo (pincel) para trazar movimientos hipotéticos del precio que tocan o sobrepasan ligeramente la línea verde de seguridad, ilustrando por qué un stop loss demasiado ajustado a la línea resultaría en una salida fallida de la operación.

**Seguridad:** Alta. Ella explica explícitamente la relación entre el tamaño de la posición, el margen del stop y la ubicación respecto a la línea de seguridad.

---

## V10 · qLtq73bTPBA [01:33]

- **Pregunta:** ¿Qué dice sobre las velas que cortan o atraviesan la línea entre sus anclas?
- **Modelo:** AGY gemini-3.8-flash

**Respuesta:** Tori Trades establece como una regla cardinal y estricta que **el precio jamás puede cortar, atravesar ni asomarse a través de la línea** (*"cannot break through, cross through or poke through"*). Si una línea de tendencia cruza mechas o cuerpos de velas intermedias entre sus puntos de anclaje, afirma enfáticamente que es una línea incorrecta e inválida (*"an incorrect trend line"*). La línea debe contener la acción del precio limpiamente por el exterior.

**Citas:**
* **[01:33]:** *"And then the third most important key here is it cannot break through. Price can't cross through, it cannot poke through."*
* **[01:43]:** *"So if you have a trend line that is going through wicks or going through bodies, that is an incorrect trend line."*

**Se ve:** 
En la pantalla de TradingView (gráfico de futuros de Petróleo Crudo / NYMEX), dibuja de forma demostrativa una línea de tendencia roja descendente que atraviesa deliberadamente el cuerpo y las mechas de varias velas intermedias. Hace énfasis visual señalando cómo las velas penetran la línea para mostrar el error típico que cometen los principiantes, y luego la borra para colocar la línea correctamente por encima de los extremos de las mechas sin que ninguna vela la corte.

**Seguridad:** Alta

---

## V11 · Y_Ney-Fp5T4 [12:48]

- **Pregunta:** ¿Qué dice sobre salir en un soporte o resistencia horizontal frente a esperar el cruce de la línea de seguridad?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Tori Trades explica que la mayoría de sus salidas de este año se han basado en niveles de soporte y resistencia (niveles horizontales o clave) en lugar de esperar a que se rompa la línea de seguridad (safety line). Comenta que esto se debe a factores psicológicos: al operar con posiciones más grandes y ver ganancias de montos altos en dólares (como $24,000 o $30,000), se siente más inclinada a tomar ganancias de inmediato. No obstante, reconoce que, como trader de líneas de tendencia que utiliza líneas de acción y de seguridad, sus ventas estratégicas ideales deberían ocurrir cuando sostiene la operación por completo y espera a que se cruce la línea de seguridad.

Cita: 
- [12:49] "One thing that I want to start talking about this year because this is something that I've noticed, is that most of my exits, if not all, were based on a level of support and resistance."
- [13:23] "Whereas you guys know that I am a trendline trader, I have action lines and safety lines, and my strategic sells when I can hold the trade out for its entirety, wait for the safety line to get crossed."
- [13:33] "You can see here in almost all of the trades this year, the exits were based on support and resistance or a horizontal level here or a key level, not based on a safety line getting broken. So you can already see this is kind of one of the things I was struggling with this year specifically, psychologically, is the bigger dollar amounts."

Se ve: En la pantalla se observa la plataforma de registro de operaciones TradeZella y la gráfica de TradingView correspondiente al contrato PLN24 (Platino, abril de 2024) en una temporalidad de 4 horas (4h). El gráfico muestra una línea de tendencia bajista de color azul con dos puntos de contacto y la posterior ruptura al alza. Se identifican dos puntos de entrada (círculo verde) y salida (círculo rojo con el número '1' indicando el cierre). A la izquierda se detalla un panel con el "Net P&L" de $24,276.00, de tipo "LONG", operando 20 contratos con el "Playbook" marcado como "2 Touchpoint Break".

Seguridad: alta

---

## V12 · YROta7k11pE [02:55]

- **Pregunta:** ¿Exige un retesteo de la línea rota antes de entrar? ¿O el cierre de la vela?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Ella exige esperar a que se produzca una ruptura ("break") y un retesteo ("retest") antes de entrar al mercado para tener confirmación, criticando a los operadores que se apresuran y entran sin estos elementos. No menciona el cierre de la vela en este tramo del video.

Cita: 
- "A trader who rushes into trades because they're too eager, they don't want to miss the move, they'll enter without a break, they'll enter without a retest, and go outside of their trading rules just to get in early." [02:50]
- "Become "okay" with entering slightly later, but with confirmation." [03:00]

Se ve: Durante el tramo de 02:50 a 03:05, la imagen alterna entre la presentadora hablando ante su micrófono en un estudio decorado con luces de neón y plantas, y pantallas negras con texto en blanco y violeta que dicen "Patience is crucial" [02:47] y "Become “okay” with entering slightly later" [02:59]. Hacia el final del tramo analizado [03:13], se muestra un plano de su computadora portátil donde se observa la plataforma TradingView en la temporalidad de 1 hora ("1h") para el contrato "Platinum Futures" (PL1!), con velas japonesas, líneas de soporte y resistencia dibujadas en rojo y amarillo, mientras ella señala un punto específico de ruptura en la pantalla con su dedo.

Seguridad: alta

---

## V13 · qsjLmbVNlCc [14:43]

- **Pregunta:** Cuando el precio rompe una línea, ¿la borra del gráfico o la conserva? ¿Qué hace con la línea siguiente?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Cuando el precio rompe una línea de tendencia (la cruza), ella la borra del gráfico. Con la siguiente línea de tendencia, la reajusta o rota para conectarla con el nuevo máximo (pico más alto) que ha alcanzado el precio.

Cita: 
- "So what I do is delete this downward trend line that's already been crossed." [14:43-14:45]
- "I'm going to rotate this one to this new high." [14:47-14:49]

Se ve: 
En la pantalla de TradingView, en el gráfico de futuros de petróleo crudo ligero ("Light Crude Oil Futures") en la temporalidad de 4 horas (4h), se observan velas japonesas rojas y verdes, líneas de tendencia verdes (alcistas) y rojas (bajistas), y líneas de soporte/resistencia horizontales amarillas. A las [14:44], la presentadora hace clic sobre la línea de tendencia roja que ya ha sido cruzada/rota por las velas y la elimina del gráfico. Inmediatamente después, selecciona la otra línea de tendencia descendente roja y arrastra su extremo para ajustarla y alinearla con el nuevo máximo de precio en la parte superior del gráfico.

Seguridad: alta

---

## V14 · E6dUUVdzMLE [03:13]

- **Pregunta:** ¿Qué dice sobre una línea con 3 toques concentrados en una sola semana frente a toques separados por semanas o meses?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Ella explica que una línea de tendencia cuyos tres puntos de contacto ocurren dentro de una sola semana tiene menos datos de respaldo (es decir, menos velas, barras o días). Por el contrario, prefiere disponer de semanas o incluso meses de datos, afirmando que los puntos de contacto distribuidos a lo largo de un mes, varias semanas o varios meses tienen mucho más peso ("holds so much more weight") que aquellos concentrados en tan solo una semana de datos.

Cita: "When I say that it doesn't have that much data behind it, it just means that I don't have that many candles, that many bars, that many days behind this trendline. So I did get three touch points, but those three touch points were all within a week. I usually like to see weeks' worth of data, I mean, if not more, months' worth of data. The touchpoints that you get on a trendline over the span of a month, a few weeks, a few months, it holds so much more weight than just simply a week's worth of data with the three touchpoints." [03:18 - 03:43]

Se ve: La pantalla muestra el editor de notas de la plataforma TradeZella titulado "Second Trade of the Year: 3 Touch-point Breakout". El texto detalla los apartados de "Setup Details" ("Trendline Break", "Position Size", "Profit"), las valoraciones con estrellas ("Rating") y los puntos clave ("Key Takeaways"). A la izquierda, se observan métricas financieras de la operación, como el riesgo de la operación ("Trade Risk": -$15,115.90) y el multiplicador R realizado ("Realized R-Multiple": 1.90R). En la toma de cámara, se ve a la presentadora con cabello oscuro, auriculares negros de diadema y una camiseta negra de cuello redondo, hablando frente a un micrófono Shure SM7B montado sobre un brazo articulado Røde.

Seguridad: alta

---

## V15 · OjZ8djwrm4I [06:03]

- **Pregunta:** ¿Qué dice sobre trazar o mover el ancla de una línea mientras la vela todavía está abierta?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Ella explica que bajo ninguna circunstancia se debe trazar, dibujar o mover el punto de anclaje de una línea de tendencia sobre una vela que todavía está abierta. En su lugar, se debe esperar a que la vela cierre por completo para confirmar si se ha establecido un nuevo máximo o mínimo válido, ya que una vela abierta puede fluctuar y violar la línea inmediatamente antes de su cierre.

Cita: 
- [06:00] "We do not want to move a line or draw a line on an open candle. That doesn't make sense because the candle could violate the line immediately within the same candle, so it's not valid. We want a clear, closed, valid pullback or high or low to be presented before we adjust the trendline."
- [06:47] "What I'm not going to do is take this trendline and take this point B and put it on the open candle. No, no. What I'm going to do is keep my line where it was. I'm going to wait for this candle to close and give me a clear newer high."

Se ve: El gráfico muestra la plataforma de TradingView analizando los futuros de petróleo crudo ligero (CL1!, Light Crude Oil Futures) en una temporalidad diaria ("D"). Se observan velas japonesas rojas y verdes, junto con varias líneas de tendencia de soporte de color verde (ascendentes) y una línea de tendencia de resistencia de color rojo (descendente). Tori Trades aparece en un recuadro circular en la esquina inferior derecha con micrófono y auriculares. Activa la herramienta de reproducción ("Replay") para demostrar de forma práctica cómo una vela verde en desarrollo cruza la línea roja de resistencia y explica por qué no se debe reajustar la línea a dicho punto hasta que la vela haya cerrado.

Seguridad: alta

---

## V16 · xRxUo3_9XRA [05:38]

- **Pregunta:** ¿Qué dice sobre las líneas muy empinadas o trazadas con datos muy recientes?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Respecto a las líneas trazadas con datos muy recientes, Tori Trades menciona que no les tiene mucha confianza y les otorga una calificación muy baja (1 de 4). Explica que esto se debe a que no se cuenta con un "punto B" claro en el pasado que proporcione datos históricos con los cuales trabajar, sino que simplemente se está utilizando la información de precios más reciente y "fresca". El tramo de video no hace mención explícita sobre líneas "muy empinadas".

Cita: 
[05:28] "I don't have a lot of confidence in this trendline. One, because the touchpoint that we drew on here is using the most recent data that we have, very very fresh. It's we don't have a very clear point B from the past that's giving us previous data to work with. We are simply just using what price has given us very recently to use this point B... I'm going to give this one a very low rating. I'm going to say one out of four for the trendline here."

Se ve: El gráfico de TradingView para futuros de oro ("Gold Futures - 1h - COMEX") en una temporalidad de 1 hora. En el gráfico se observan líneas de tendencia rojas descendentes y tres líneas de tendencia verdes ascendentes de largo plazo. El cursor interactúa señalando los puntos de contacto de la línea verde inferior. En la esquina inferior izquierda aparece brevemente una notificación de noticia de Reuters. En la esquina superior derecha se muestra la cámara de la presentadora hablando frente a un micrófono.

Seguridad: alta

---

## V17 · qsjLmbVNlCc [02:00]

- **Pregunta:** ¿Qué es la doble confirmación con el rango horizontal? ¿Es obligatoria para entrar?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: La doble confirmación consiste en esperar a que se rompan tanto la línea de tendencia (trendline) como los niveles de soporte y resistencia horizontales (los "techos" y "suelos") antes de tomar una posición. Esto sirve para evitar quedar atrapado en la consolidación lateral ("chop"). Respecto a si es obligatoria para entrar, el tramo analizado no indica explícitamente que sea un requisito obligatorio en el 100% de las operaciones, sino que es una herramienta que ella utiliza para tener mayor seguridad, evitar pérdidas seguidas y sentirse mucho más confiada en su posición.

Cita: 
[02:14] "And that is where double confirmation comes into play when I mark up the ceilings and the floors or the support and resistance, and wait for both of those things to be broken. So now not only am I waiting for the trendline to get broken, but I'm also waiting for support and resistance to be broken. So if I wait for both of those things, it's double confirmation, helps me feel much more confident about my position."

Se ve: Un gráfico en pantalla completa de TradingView correspondiente al NQ1! (NASDAQ 100 E-mini Futures, temporalidad de 4 horas). En él se observa una línea de tendencia alcista dibujada en color verde con un trazo continuo. El gráfico muestra velas japonesas verdes y rojas. Alrededor de las 02:34 el video regresa a la toma de estudio donde se ve a Tori frente a su micrófono y portátil, con auriculares grandes, explicando directamente a la cámara.

Seguridad: alta

---

## V18 · qLtq73bTPBA [12:00]

- **Pregunta:** ¿Cómo define la Action Line y la Safety Line una vez que una línea se rompe?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Tori Trades define la "Action Line" (línea de acción) como aquella línea de tendencia que ha sido rota por el precio, lo cual actúa como el disparador o señal para tomar la decisión de realizar una operación (trade). Por otro lado, define la "Safety Line" (línea de seguridad) como la línea opuesta a la "Action Line". Esta línea es la que mantiene seguro al trader, representando la gestión de riesgo o stop loss, e indicando cuánto tiempo se debe permanecer en la operación.

Cita: 
- [11:35]: "An action line is the line that was broken. This triggers our decision to place a trade."
- [12:30]: "The safety line is the opposite line to the action line. This line keeps us safe. This line tells us how long to stay in our trade."

Se ve: En la interfaz de TradingView se muestra un gráfico de velas japonesas con fechas en el eje horizontal que van desde finales de 2020 hasta principios de 2021. Se aprecian dos líneas de tendencia dibujadas: una línea alcista de color verde ("Upward Line") y una línea bajista de color rojo ("Downward Line"). Cuando una vela rompe la línea verde hacia abajo, se añade una etiqueta de texto que dice "Action Line" sobre la línea verde rota y otra que indica "Break". Acto seguido, la línea roja opuesta se etiqueta como "Safety Line". En la esquina inferior izquierda aparece un recuadro con la cámara de la presentadora explicando los conceptos en lenguaje de señas y gesticulando de forma dinámica.

Seguridad: alta

---

## V19 · G29LbG1Xkvw [02:46]

- **Pregunta:** ¿Qué exige para dar por buena una ruptura: cierre de vela con cuerpo completo, retesteo, o ambas cosas?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Ella no exige ambas cosas simultáneamente de forma obligatoria; las presenta como herramientas o confirmaciones adicionales individuales de su "caja de herramientas" que se pueden implementar por separado. Explica que se puede empezar aplicando algo tan simple como el "rompimiento y retesteo" (break and retest) para evitar falsas rupturas, o bien utilizar la opción de esperar al cierre de la vela (waiting for the candle close) por encima o debajo del nivel para confirmar la intención del movimiento.

Cita: 
- [02:35]: "So the first thing is a break and retest."
- [03:00]: "You could start just implementing something as simple as that, and that right there alone in itself will help you avoid fakeouts."
- [03:05]: "Now the next thing is waiting for the candle close."

Se ve: 
- En [02:42] - [02:45]: Un gráfico animado sobre fondo negro que muestra una línea de tendencia verde alcista. Las velas (rojas y verdes) rompen hacia abajo con una vela roja larga, luego suben a retestear la línea con una vela verde (tocándola desde abajo) y finalmente continúan descendiendo con fuerza.
- En [03:11] - [03:21]: Un gráfico animado sobre fondo negro que muestra una línea de tendencia verde bajista. Se observa una vela verde que rompe con fuerza hacia arriba y cierra su cuerpo completamente por encima de dicha línea, validando la ruptura sin necesidad de mechas largas que indiquen un rechazo.

Seguridad: alta

---

## V20 · q4t71xxbDsY [17:23]

- **Pregunta:** ¿Dice que no baja a temporalidades menores que 4H para entrar antes? ¿Qué temporalidad usa para entrar y salir?
- **Modelo:** AGY gemini-robotics-er-2-preview

Respuesta: Sí, afirma explícitamente que nunca baja a una temporalidad menor para buscar una entrada más rápida (anticipada). Para sus ejecuciones, tanto de entrada como de salida y gestión de operaciones, utiliza exclusivamente la temporalidad de 4 horas (4H).

Cita: 
[17:20] "...do I go lower in time frames for a sooner entry? And the answer is no."
[17:47] "But one thing that I will say is I do not ever go to a lower timeframe to look for a sooner entry."
[18:01] "...then stop at the 4-hour timeframe and that's where I do all of my trade execution, my entries and my exits..."

Se ve: La plataforma TradeZella con la pestaña de "Tracking" del activo "PLJ25" configurado en temporalidad de 4 horas (se lee "PLJ25, 4h" en la parte superior izquierda del gráfico). El gráfico muestra velas japonesas de 4 horas con líneas de tendencia de color verde y rosa, líneas de soporte y resistencia horizontales de color amarillo y verde, y una línea horizontal roja que indica el "Stop Loss". El panel de estadísticas a la izquierda muestra un P&L neto de $34,721.00 en posición larga (LONG).

Seguridad: alta

---

