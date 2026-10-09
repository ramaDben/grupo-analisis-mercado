# This boring trading strategy made me $526,454

- Video: https://www.youtube.com/watch?v=PnIkSLm2yRk
- Tipo esperado: metodo
- Duración: 28 min
- Modelo: gemini-3.7-flash
- Tokens de entrada: 98421

## Tipo y resumen
- **Tipo:** Enseñanza del método (sistema completo de acción del precio basado en líneas de tendencia con análisis *top-down*).
- **Resumen:**
  Tori explica su sistema de trading basado exclusivamente en la acción del precio y líneas de tendencia trazadas con la herramienta semirrecta (*Ray*) [02:51].
  El método utiliza un análisis descendente (*top-down*) desde gráfico mensual hasta temporalidades menores para trazar líneas conectadas que definen la estructura del mercado [03:33, 09:00].
  La operativa se basa en dos conceptos mecánicos: la *Action Line* (línea rota que da la entrada) y la *Safety Line* (línea opuesta que marca el stop loss inicial y el trailing stop de salida) [16:37, 17:05, 20:45].

---

## 1. Trazado de la línea
- **Anclas y puntos:** Utiliza la herramienta *Ray* (semirrecta) de TradingView, fijando dos anclas: Punto A (punto de pivote / inicio) y Punto B (bloquea el ángulo y grado de inclinación) [02:51, 02:58].
- **Cuerpos vs. mechas:**
  - *Lo que dice:* Menciona conectar los puntos más bajos o altos [08:00, 11:42], pero no teoriza explícitamente sobre cuerpos frente a mechas.
  - *Lo que se ve en el gráfico:* Apoya los anclajes y los toques indistintamente en los extremos de las mechas más bajas/altas del precio [06:40, 08:38, 11:48, 14:02].
- **Número de puntos:** Requiere un Punto A y un Punto B para trazarla, intentando atrapar la mayor cantidad de puntos de contacto posibles sin que el precio la atraviese [09:03, 09:44].
- **Validez de un pivote:** Para la primera línea alcista, el Punto A debe ser el mínimo absoluto visible en pantalla [08:00, 08:26]. Para la primera línea bajista, el Punto A es el máximo absoluto visible [11:42]. Las líneas sucesivas deben nacer obligatoriamente donde terminó la anterior: el Punto B de la línea anterior se convierte en el nuevo Punto A [10:01].
- **Vela cerrada:** No lo trata (en las animaciones conceptuales muestra velas completas cruzando la línea [00:03, 16:19]).

---

## 2. Validez y calidad de una línea
- **Toques:** Establece como regla expresa intentar capturar la mayor cantidad de puntos de contacto (*touchpoints*) posibles [09:03, 10:18].
- **Pendiente / ángulo:**
  - Una línea de tendencia jamás puede ser horizontal (ángulo cero); debe tener cierta inclinación angular hacia arriba o hacia abajo [08:29, 08:44].
  - A medida que el precio acelera, traza líneas con pendientes más empinadas (*steeper trendlines*) conectadas a las anteriores para acercarse a la acción del precio actual [10:55, 11:06, 14:00, 14:20].
- **Separación entre toques:** No lo trata.
- **Jerarquización de líneas buenas y malas:**
  - Las líneas de temporalidades mayores tienen más peso y relevancia porque contienen más datos e historial [03:52, 04:10].
  - Una línea es inválida/incorrecta si el precio la corta, atraviesa o asoma a través de ella (*price cannot have intersected or poked through*) [08:34, 09:05, 10:30].

---

## 3. Ajuste de la línea vs línea nueva
- **Cuándo mueve el ancla (ajuste):**
  - Al bajar de temporalidad (por ejemplo, de mensual a semanal o de semanal a diario), el zoom más preciso muestra imperfecciones donde el precio asoma ligeramente a través de la línea; ahí se ajusta levemente el Punto B para que vuelva a respetar los extremos sin ser intersecada [12:34, 13:43, 14:15].
  - En el mantenimiento diario (*ongoing maintenance*): si el precio rompió la línea pero el operador no ejecutó la operación a tiempo, se recoloca el Punto B hacia el nuevo extremo/rebote generado para actualizar el ángulo [26:30, 26:55].
- **Cuándo traza una línea nueva:** Traza una línea nueva cuando la acción del precio se aleja aceleradamente de la anterior; toma el Punto B previo como el nuevo Punto A y busca un nuevo Punto B con pendiente más empinada para acercarse a la cotización actual [10:00, 10:55, 14:00].
- **Qué hace con la línea vieja:** La mantiene dibujada en el gráfico; no la borra, ya que forman una secuencia continua que da estructura y contexto al mercado [10:58, 12:24].

---

## 4. Ruptura, confirmación y falsas rupturas
- **Qué cuenta como ruptura:** Explica que una ruptura ocurre cuando el precio rompe o viola la línea de tendencia (*price breaks/violates the trendline*) [16:18, 16:43]. En los diagramas animados se ilustra como una vela que cruza y cierra al otro lado de la línea [16:19, 16:28, 17:34].
- **Retesteo:** No exige retesteo; opera el quiebre directamente en la dirección de la ruptura [16:43].
- **Cómo evita fakeouts:** Dice explícitamente que no intenta adivinar hacia dónde irá el precio, sino reaccionar mecánicamente a lo que el precio dicta [15:22, 15:41]. Menciona de pasada que existen filtros y criterios adicionales avanzados para ser más selectivos (*picky*), pero en este video presenta el modelo base fundacional [16:50, 17:48].

---

## 5. Entrada
- **Gatillo exacto:** La ruptura de la línea de tendencia activa (*Action Line*) [16:10, 16:37].
  - Si el precio rompe una línea de tendencia alcista, se entra en **Corto (Venta)** porque los compradores perdieron el control [16:18, 16:24].
  - Si el precio rompe una línea de tendencia bajista, se entra en **Largo (Compra)** porque los vendedores perdieron el control [16:27, 16:34].
- **Tipo de orden:** No lo trata formalmente (en la explicación dice "entramos al romper" [16:43]).
- **En qué temporalidad:** En la temporalidad menor designada por el operador para ejecutar (en el ejemplo del video utiliza 1 hora, pero aclara que puede ser 5 minutos, etc.) [03:48, 14:31, 14:43].

---

## 6. Stop / invalidación
- **Dónde y por qué:** El stop loss se coloca al otro lado de la *Safety Line* (la línea de tendencia opuesta a la *Action Line*) [19:07, 19:10].
  - Para un corto: stop loss por encima de la *Safety Line* bajista [17:15, 19:08].
  - Para un largo: stop loss por debajo de la *Safety Line* alcista [17:21, 19:10].
- **Stop fijo vs dinámico:** No se deja como un stop fijo pasivo; es un nivel precalculado inicialmente que luego se convierte en dinámico siguiendo la *Safety Line* [18:49, 20:45].

---

## 7. Salida y objetivo
- **Criterio de salida:** Salida completa cuando el precio cruza o viola la *Safety Line* [17:34, 17:38].
- **Toma parcial:** No lo trata (explica cerrar la posición cuando se invalida la *Safety Line* [17:38]).
- **Cómo deja correr la ganancia:** Deja correr el trade indefinidamente mientras el precio respete la *Safety Line* y continúe a favor de la posición [17:24, 20:49].

---

## 8. Gestión durante la operación
- **Gestión activa:** Se utiliza un *Trailing Stop Loss* manual que se desplaza continuamente a lo largo de la *Safety Line* a medida que el precio avanza [20:45, 21:11, 21:20].
- **Qué no toca:** No cierra la posición prematuramente por objetivo fijo mientras el precio se mantenga respetando la *Safety Line* [17:28, 20:55].

---

## 9. Temporalidades
- **Temporalidad de la tendencia (contexto):** Comienza en Mensual (1M), pasa a Semanal (1W), luego Diario (1D) y 4 Horas (4h) [03:40, 06:34, 12:15, 13:42, 14:13].
- **Temporalidad de entrada:** Temporalidad operativa elegida por el trader; en el video aterriza en 1 Hora (1h) [14:31], y menciona que si se opera en 5 minutos se debe bajar 1h -> 30m -> 15m -> 10m -> 5m [14:45].
- **Duración de las operaciones:** No lo trata numéricamente.

---

## 10. Soportes y resistencias horizontales
- *Lo que dice:* Al trazar líneas de tendencia recalca específicamente que **no** pueden ser líneas horizontales [08:33, 08:44]. Muestra el gráfico de Bitcoin completamente "desnudo" sin líneas de soporte/resistencia horizontales [06:14].
- No utiliza soportes ni resistencias horizontales en este sistema; se basa estrictamente en líneas de tendencia diagonales [08:33].

---

## 11. Cuándo NO operar
- Menciona que no se opera en contra del quiebre ni cuando no se ha roto una *Action Line* [16:43].
- En cuanto a filtros adicionales, noticias o rangos laterales específicos: No lo trata (hace mención genérica de que existen capas de filtros para ser más selectivo, pero no las desglosa en este video [16:50, 17:48]).

---

## 12. Riesgo y tamaño de posición
- **Regla de riesgo:** Nunca arriesgar más del **1% al 2%** del capital total de la cuenta en una sola operación [19:46].
- **Cálculo del tamaño:** El tamaño de la posición (contratos, acciones, lotes) se calcula en función de la distancia hasta el stop loss y la pérdida monetaria máxima tolerada (1-2%) [18:23, 19:41].
  - Ejemplo dado: Para una cuenta de $10,000, el 1-2% equivale a una pérdida máxima de $100 a $200 por operación [19:54, 20:01].
- **Propósito:** Mantener el riesgo bajo permite absorber rachas de 10 pérdidas seguidas sin dañar gravemente la cuenta y permitir que la probabilidad juegue a favor [20:16].

---

## 13. Instrumentos que opera
- En su trayectoria personal menciona haber convertido una cuenta de futuros de $5,000 a más de $471k-$500k [00:48, 00:50].
- Afirma que el sistema funciona para cualquier instrumento: Bitcoin / criptomonedas [06:06], petróleo crudo (*Crude Oil*) [07:20], oro (*Gold*) [07:21], Nasdaq [07:22], Dow Jones [07:22], acciones individuales como Tesla [07:23], futuros [18:28] y pares de Forex [18:29].

---

## 14. Operaciones concretas mostradas
- El video **no muestra una operación en vivo ejecutada de principio a fin**, sino un ejemplo estructurado de análisis y simulación pedagógica sobre Bitcoin:
  - **Instrumento:** Bitcoin (BTCUSD en TradingView) [06:07].
  - **Temporalidad:** Análisis desde 1M, 1W, 1D, 4h hasta 1h [06:34 - 14:55].
  - **Líneas trazadas:** Secuencia de líneas alcistas verdes encadenadas (Punto B -> Punto A) y líneas bajistas rojas [11:13, 11:58, 14:24].
  - **Entrada:** Ilustrada en diagramas conceptuales tras romper la *Action Line* [16:24, 16:34].
  - **Stop:** Colocado al otro lado de la *Safety Line* opuesta [19:10].
  - **Salida:** Al perforar la *Safety Line* de vuelta [17:38].
  - **Resultado:** No aplica (ejemplo educativo de configuración).
  - **Lección:** Las líneas de tendencia proporcionan un mapa objetivo donde el precio determina la entrada, el stop y la salida sin necesidad de adivinar [15:22, 17:43].

---

## 15. Reglas verificables
1. **[02:51] Selección de herramienta:** Utilizar la herramienta *Ray* (semirrecta) en TradingView fijando Punto A (pivote) y Punto B (ángulo) para proyectar la línea indefinidamente.
2. **[03:33] Análisis Top-Down obligatorio:** Iniciar el trazado en gráfico mensual (1M) e ir descendiendo sucesivamente (1W -> 1D -> 4h -> 1h).
3. **[08:00, 08:26] Ancla inicial alcista:** La primera línea alcista debe tener su Punto A anclado en el punto más bajo visible de la pantalla del activo.
4. **[08:29, 08:44] Prohibición de líneas horizontales:** Toda línea de tendencia debe tener un ángulo de inclinación; una línea con pendiente cero (horizontal) es inválida.
5. **[09:01] Conexión encadenada:** Cada nueva línea de tendencia debe conectarse a la anterior: el Punto B de la línea precedente se convierte obligatoriamente en el Punto A de la nueva línea [10:01].
6. **[09:03] Maximización de toques:** Se debe orientar el Punto B para tocar la mayor cantidad de puntos de contacto (*touchpoints*) posibles.
7. **[09:06] Integridad de la línea:** El precio no puede haber cruzado, intersecado ni asomado a través de la línea de tendencia trazada.
8. **[11:42] Ancla inicial bajista:** La primera línea bajista debe originarse con su Punto A en el máximo más alto visible en pantalla.
9. **[16:18, 16:24] Regla de entrada en Corto:** Si el precio rompe una línea de tendencia alcista (*Action Line*), abrir posición corta.
10. **[16:27, 16:34] Regla de entrada en Largo:** Si el precio rompe una línea de tendencia bajista (*Action Line*), abrir posición larga.
11. **[17:07, 19:10] Definición de Safety Line e Invalidación:** La *Safety Line* es la línea opuesta a la *Action Line*; el stop loss inicial se ubica inmediatamente detrás de ella.
12. **[17:34, 17:38] Regla de salida:** Cerrar la posición inmediatamente en el momento en que el precio vulnere o atraviese la *Safety Line*.
13. **[19:46] Límite de riesgo:** Jamás arriesgar más del 1% al 2% del capital de la cuenta en una sola operación.
14. **[20:45, 21:11] Trailing Stop:** A medida que el precio avanza favorablemente, ajustar manualmente el stop loss siguiendo la trayectoria de la *Safety Line*.
15. **[26:55, 27:01] Mantenimiento diario:** Si una línea es vulnerada por el precio sin que se haya tomado la operación, reajustar el Punto B hacia el nuevo extremo/rebote respetando las 3 reglas de trazado.

---

## 16. Citas textuales clave
- **[09:00]** *"One, every trendline has to connect to one another. Two, we try to capture as many touchpoints as possible. Three, price cannot have intersected or poked through the trendline."*
- **[10:01]** *"When connecting trendlines, the previous point B will always be the new point A."*
- **[15:22]** *"We don't ever have to guess where price is going next... Our entire job in this whole system and this whole strategy is to simply follow the price."*
- **[16:37]** *"The line that price broke is our action line. And the direction that price broke will tell us which direction to trade."*
- **[17:06]** *"The safety line will always be the opposing trendline to the action line... As soon as price violates the safety line, we are no longer safe in our trade, it is time to close our position."*
- **[19:46]** *"Never risk more than 1 to 2% of your capital on a single trade."*