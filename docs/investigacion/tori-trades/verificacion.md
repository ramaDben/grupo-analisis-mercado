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

