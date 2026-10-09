# Breaking Down My SIMPLE Trading Strategy (step by step)

- Video: https://www.youtube.com/watch?v=qLtq73bTPBA
- Tipo esperado: metodo
- Duración: 55 min
- Modelo: gemini-3.8-flash
- Tokens de entrada: 194892

## Tipo y resumen
* **Tipo de video:** Enseñanza del método (clase teórica de estrategia combinada con demostración práctica de análisis *top-down* y simulación de ejecución en TradingView).
* **Resumen:** 
Tori Trades expone su metodología técnica basada exclusivamente en la acción del precio y líneas de tendencia trazadas con la herramienta semirrecta (*Ray tool*) [01:10]. Enseña un análisis jerárquico *top-down* (desde mensual hasta 5 minutos), donde cada nueva línea debe nacer del pivote más reciente (*Punto B*) de la línea anterior sin ser atravesada por el precio [04:26, 45:15]. El sistema opera rupturas o rebotes definiendo una "Línea de Acción" (detonante de entrada) y una "Línea de Seguridad" (guía de invalidación/stop loss y salida) [11:28, 12:28].

---

## 1. Trazado de la línea
* **Herramienta:** En TradingView utiliza la herramienta *Ray* (semirrecta), aunque ella la llama línea de tendencia [01:10].
* **Anclas y mechas:** Dice explícitamente a los operadores experimentados que ella **incluye las mechas** (*wicks*) completas de las velas dentro de la acción del precio; no corta cuerpos ni mechas [04:00 - 04:25].
* **Regla estricta de no intersección:** Dice y muestra que la línea no puede ser cortada ni atravesada por velas: el precio no puede cruzarla ni asomarse a través de ella (*cannot break through, cross through or poke through*) [01:33 - 01:40, 03:44 - 03:51]. Muestra un gráfico con una línea que corta velas y recalca enfáticamente que es un error [01:43 - 01:53].
* **Línea bajista:** Se coloca por encima del precio, inclinada hacia abajo, conectando máximos descendentes sin que el precio la penetre [01:24 - 01:42].
* **Línea alcista:** Se coloca por debajo del precio, inclinada hacia arriba, sosteniendo los mínimos crecientes sin intersecciones [01:42 - 02:01].
* **Puntos de anclaje (Punto A y Punto B):**
  * *Punto A:* El punto de origen o pivote maestro [10:08].
  * *Punto B:* El segundo toque donde se fija o ajusta el ángulo de la línea [10:12 - 10:45].
* **Conexión entre líneas en el Top-Down:** Cada línea de una temporalidad menor debe comenzar obligatoriamente en el *Punto B* (el toque más reciente) de la línea de la temporalidad superior precedente [04:26 - 04:55, 45:15 - 45:26, 46:40 - 46:49].
* **Vela cerrada:** No exige explícitamente esperar un cierre de vela para el anclaje inicial de los pivotes; busca los puntos extremos visuales históricos en el gráfico [05:49 - 06:05].

---

## 2. Validez y calidad de una línea
* **Número de toques:**
  * Mínimo técnico para trazarla: 2 toques (Punto A y Punto B) [10:03 - 10:45].
  * En el gráfico de platino mensual muestra una línea bajista válida con solo 2 toques porque no había más sin cortar velas [05:59].
* **Jerarquía de calidad (2 vs 3 toques):**
  * *2 Touchpoint Break:* Requiere 2 toques claros previos a la ruptura; la clasifica como de mayor riesgo relativo (*higher risk setup*) porque el precio puede estar más alejado de la línea de seguridad [25:42 - 26:49].
  * *3 Touchpoint Break:* Línea con al menos 3 toques claros antes de romper; la define como un setup de menor riesgo (*lower risk setup*) debido a que suele romper más cerca de la línea de seguridad y acumula mayor confirmación estructural [27:48 - 28:09].
* **Pendiente / Ángulo:** Debe acompañar la dirección clara del movimiento sin cortar velas [01:28, 01:59]. En temporalidades menores va trazando líneas progresivamente más empinadas (*steeper*) a medida que el precio acelera [46:20, 47:24, 50:06].
* **Separación entre toques:** No establece una regla numérica fija de distancia o barras; selecciona visualmente los valles o crestas limpios que no impliquen atravesar el precio [05:50 - 06:04, 46:40 - 46:58].

---

## 3. Ajuste de la línea vs línea nueva
* **Cuándo mueve o ajusta la línea:** Al descender en las temporalidades (*Top-Down* de 1D a 4H, 1H, 30m o 5m), el aumento de detalle visual revela que velas pueden estar tocando o traspasando milimétricamente la línea. En ese instante ajusta ligeramente el Punto B para mantener la regla de no intersección [44:00 - 44:12, 46:13 - 46:18, 47:19 - 47:22].
* **Cuándo traza una línea nueva:** Traza una línea nueva más empinada cuando el precio se aleja de las líneas mayores y crea un nuevo tramo de aceleración dentro de la estructura [46:30, 47:25, 50:06].
* **Qué hace con la línea vieja:** La mantiene en el gráfico. Todas las líneas coexisten conectadas entre sí para proporcionar el contexto estructural completo [04:30 - 04:55, 43:37 - 43:47, 50:30 - 50:35].
* **Ajuste por ruptura prematura:** Si al extender la línea esta atraviesa una mecha o vela intermedia, se debe reubicar el Punto B en el toque anterior limpio para evitar que corte el precio [06:47 - 06:53, 48:48 - 49:15].

---

## 4. Ruptura, confirmación y falsas rupturas
* **Qué cuenta como ruptura:** La ruptura ocurre en el momento en que el precio traspasa físicamente la línea trazada (la perfora hacia afuera) [11:28 - 11:40, 51:00 - 51:22]. No menciona exigir un porcentaje de distancia ni margen específico; la línea actuaba como contención y al ser rebasada se considera rota [51:00].
* **Vela cerrada vs en desarrollo:** En la simulación en vivo [51:00 - 51:23], ejecuta la orden de compra directamente mientras la vela de 5 minutos perfora la línea bajista, tratándolo como el gatillo activo.
* **Retesteo (*Break and Retest*):** Explica el setup específico donde el precio rompe la línea de acción, retrocede para tocarla por el lado opuesto (retesteo) y luego continúa [29:20 - 30:05]. Destaca que este patrón ofrece una entrada con el menor riesgo posible porque se produce pegado a la línea [28:44].
* **Cómo evita *fakeouts* (falsas rupturas):** No utiliza filtros de volatilidad ni indicadores externos [23:12, 33:30]. Su mecanismo de protección contra falsas rupturas no es predecirlas, sino situar de inmediato el stop loss al otro lado de la Línea de Seguridad opuesta [16:17 - 16:53].

---

## 5. Entrada
* **Gatillo exacto:**
  1. *Trendline Break:* Ruptura de la línea que contenía el precio (Línea de Acción) [11:28 - 11:40, 51:00 - 51:22].
  2. *Break and Retest:* El toque o respeto sobre la línea rota desde el lado opuesto [29:26 - 29:39].
  3. *Bounce (Rebote):* El toque y rechazo sobre una línea de tendencia activa sin que esta se rompa [30:50 - 31:02, 31:44 - 31:58].
* **Tipo de orden:** En la plataforma ejecuta órdenes a mercado cuando el precio rompe la línea en tiempo real [51:05, 52:16].
* **Temporalidad de entrada:** Desciende progresivamente hasta la temporalidad operativa baja, demostrada en el gráfico de **5 minutos** para ejecutar la entrada [47:53 - 47:57, 49:47 - 50:00, 51:00].

---

## 6. Stop / invalidación
* **Ubicación del Stop Loss:** Se coloca obligatoriamente **del otro lado de la Línea de Seguridad** (*on the other side of your safety line*) [16:17 - 16:20, 16:59 - 17:04].
* **Regla estricta:** El stop loss **nunca** debe situarse exactamente *sobre* la línea de seguridad, sino con un margen detrás de ella, porque se anticipa que el precio respetará dicha línea [17:16 - 17:36].
* **Función del Stop Loss:** Lo compara con un "extintor de incendios" o mecanismo de seguridad (*failsafe*) que corta la pérdida si el mercado no respeta la estructura [16:18 - 16:53].
* **Línea de Seguridad:** Es la línea opuesta a la línea de acción que fue rota. Si se rompe una línea bajista (acción), la línea alcista que sostiene el avance es la línea de seguridad [12:28 - 12:45].

---

## 7. Salida y objetivo
* **Criterio de salida:** Se mantiene la operación hasta que el precio **rompa la Línea de Seguridad** [09:43 - 09:47, 53:45 - 54:06]. En ese instante se cierra la posición completa [54:04].
* **Toma parcial de beneficios:** En la demostración de la boleta de orden desactiva la casilla de Take Profit (*TP*) [51:58 - 52:01]. No enseña salidas parciales fijas; deja correr la ganancia mientras el precio siga rebotando y respetando la Línea de Seguridad [53:13 - 53:44].
* **Relación Riesgo/Beneficio:** Busca que la ganancia potencial sea significativamente mayor que la pérdida predefinida al entrar cerca del origen de la ruptura [15:19 - 15:38].

---

## 8. Gestión durante la operación
* **Ajuste del Stop / Trail:** Muestra visualmente que a medida que el precio avanza a lo largo de la Línea de Seguridad, la condición de salida se desplaza junto con dicha línea: si el precio rompe la línea de seguridad más arriba, se asegura la ganancia [53:15 - 53:47].
* **Intervención:** Dice que mientras el precio respete la línea de seguridad no se sale de la posición; únicamente se actúa cuando el precio cruza la línea [53:38 - 54:06].

---

## 9. Temporalidades
* **Análisis Top-Down (de arriba hacia abajo):**
  * Temporalidad macro de contexto inicial: **Mensual (1M)** [04:56 - 05:00, 42:21 - 42:29].
  * Secuencia completa descendente: **Mensual $\rightarrow$ Semanal $\rightarrow$ Diario $\rightarrow$ 4 Horas $\rightarrow$ 1 Hora $\rightarrow$ 30 Minutos $\rightarrow$ 5 Minutos** [42:21 - 48:09].
* **Temporalidad de entrada:** **5 minutos (5M)** para la búsqueda del quiebre y ejecución operativa [47:53 - 47:57, 49:47].
* **Duración de las operaciones:** No lo trata (muestra la dinámica en simulador sin definir un horizonte temporal cerrado en días o semanas).

---

## 10. Soportes y resistencias horizontales
* **Uso:** Son opcionales; los describe expresamente como un "extra" o "bono" de confirmación [13:25 - 13:40, 21:36 - 21:45].
* **Relevancia:** Enfatiza que los niveles horizontales **no son el núcleo ni la base** de su estrategia (*it is not the meat of the strategy*) [13:54 - 13:56, 14:23 - 14:35].
* **Definición:** Zonas donde el precio llegó y giró múltiples veces (soporte/resistencia, oferta/demanda o niveles clave) [13:25, 14:07 - 14:22]. Solo se utilizan para dar confirmación adicional al confluir con las líneas de tendencia [13:52, 22:03 - 22:09].

---

## 11. Cuándo NO operar
* **Condición de línea atravesada:** No se puede operar ni trazar si las líneas no pueden colocarse limpiamente sin cortar velas [01:43 - 01:52, 06:47 - 06:53].
* **Sin ruptura confirmada:** Mientras el precio se encuentre oscilando entre las líneas sin romper ninguna, se prohíbe entrar; se debe esperar pacientemente [41:13 - 41:19, 50:35 - 50:47].
* **Filtros de noticias o rangos:** No lo trata en detalle de forma teórica; su único filtro demostrado es que el precio no perfore las líneas antes de tiempo y esperar a que el precio decida la ruptura [50:41 - 50:48].

---

## 12. Riesgo y tamaño de posición
* **Regla general de riesgo de capital:** Arriesgar del **1% al 2% del capital total** por operación [17:38 - 17:42, 18:15 - 18:20, 18:55].
* **Fórmula de pérdida monetaria:** 
  $$\text{Capital} \times 0.02 = \text{Riesgo por operación (su "comisión/tarifa" o fee)}$$
  * Con cuenta de $\$10,000$, riesgo = $\$200$ [17:42].
  * Con cuenta de $\$5,000$, riesgo = $\$100$ [17:43].
  * Con cuenta de $\$3,000$, riesgo = $\$60$ [17:44, 19:16].
* **Cálculo del tamaño:** En la boleta de orden ajusta visualmente el stop arrastrándolo hasta que la pérdida calculada en dólares coincida con el riesgo permitido según el capital [52:16 - 52:45].
* **Traders experimentados:** Menciona que con 10 años de experiencia ella llega a arriesgar entre 4% y 7% según su intuición y calidad del setup, pero para novatos la regla inquebrantable es 1-2% [18:31 - 18:49].
* **Concepto de "Fee" (tarifa):** Enseña a ver la pérdida del stop no como un fracaso emocional, sino como el costo o tarifa operativa inevitable de hacer el negocio [18:00 - 18:15].
* **Ratio de supervivencia:** Con el 1% al 2%, se necesitarían 100 pérdidas seguidas para quebrar la cuenta [20:25 - 20:30].

---

## 13. Instrumentos que opera
* **Futuros de Platino (*Platinum Futures - PL1!*):** Empleado para la demostración del análisis *top-down* paso a paso [04:56 - 07:05].
* **Futuros de Petróleo Crudo (*Light Crude Oil Futures - CL1!*):** Empleado para la sesión de análisis técnico *top-down* completo y ejecución simulada de la operación [42:11, 48:48, 51:00].
* **Universalidad:** Afirma que la estrategia funciona de forma idéntica en cualquier activo o mercado financiero (acciones como Apple, materias primas, futuros) porque se fundamenta puramente en la acción del precio sin indicadores [24:30 - 25:35, 38:00 - 38:06].

---

## 14. Operaciones concretas mostradas

### Operación en simulación: Petróleo Crudo (*Light Crude Oil Futures - CL1!*)
* **Instrumento:** Futuros de Petróleo Crudo (*CL1!*) en TradingView / NYMEX [48:48, 51:00].
* **Temporalidad:** Análisis desde 1M hasta 5M; ejecución en **5 minutos** [48:09, 51:00].
* **Líneas trazadas:** 
  * Línea bajista (roja) trazada desde el máximo del impulso en 5 minutos [50:11 - 50:19].
  * Línea alcista (verde) de soporte que acompaña los mínimos crecientes [50:25 - 50:30].
* **Entrada:** Compra a mercado cuando la vela rompe hacia arriba la línea bajista (que se convierte en la Línea de Acción) [51:00 - 51:22].
* **Stop:** Colocado por debajo de la línea alcista opuesta (Línea de Seguridad) con un riesgo fijado en $\$100$ [52:16 - 53:12].
* **Salida:** Se produce cuando el precio, tras avanzar a favor del trade, se gira y quiebra la línea alcista de seguridad [54:00 - 54:06].
* **Resultado:** Operación positiva con ganancia acumulada durante el recorrido alcista antes de la ruptura final [53:28 - 53:40, 54:05].
* **Lección:** No intentar predecir el techo ni usar targets fijos arbitrarios; la salida técnica objetiva la determina la ruptura de la línea de seguridad [53:45 - 54:06].

---

## 15. Reglas verificables
1. **Regla de no intersección:** Una línea de tendencia jamás puede atravesar el cuerpo ni la mecha de ninguna vela intermedia entre sus puntos de toque [01:33 - 01:53].
2. **Inclusión de mechas:** Los puntos de anclaje de las líneas deben trazarse tomando los extremos de las mechas (*wicks*) y no los cuerpos [04:13 - 04:18].
3. **Regla de encadenamiento Top-Down:** Al bajar de temporalidad, cada nueva línea debe nacer forzosamente en el último toque (*Punto B*) de la línea previa de temporalidad superior [04:28 - 04:45, 45:15 - 45:26, 46:40 - 46:49].
4. **Regla del detonante de entrada (Línea de Acción):** La entrada a mercado solo se autoriza cuando el precio rompe la línea de tendencia que lo confinaba [11:28 - 11:40, 51:00 - 51:22].
5. **Regla de asignación de roles post-ruptura:** La línea rota pasa a llamarse *Línea de Acción* y la línea opuesta no rota se convierte automáticamente en la *Línea de Seguridad* [12:00 - 12:45].
6. **Regla de colocación del Stop Loss:** El stop loss debe situarse siempre al otro lado exterior de la Línea de Seguridad, nunca exactamente sobre ella [16:17 - 16:20, 17:16 - 17:36].
7. **Regla de dimensionamiento de riesgo:** El riesgo máximo por operación debe ser estrictamente del 1% al 2% del balance de la cuenta [17:38 - 17:42, 18:15 - 18:20].
8. **Regla de salida técnica definitiva:** La posición abierta se cierra en su totalidad de forma inmediata cuando el precio perfora la Línea de Seguridad [09:43 - 09:47, 53:45 - 54:06].
9. **Exclusión de indicadores:** No se permite el uso de indicadores técnicos para filtrar entradas o salidas; el sistema se rige al 100% por acción del precio pura y líneas [23:12, 33:30 - 33:45].

---

## 16. Citas textuales clave
* **[01:33]:** *"And then the third most important key here is it cannot break through. Price can't cross through, it cannot poke through."*
* **[04:13]:** *"I include the wicks... When I do the top-down analysis, I am including price action. This is my system and this is the way that I've been able to repeat my process over and over again."*
* **[04:28]:** *"As we move down to lower timeframes, we always want to connect our previous higher timeframe trend lines. All trend lines are going to connect to one another."*
* **[14:23]:** *"It is not the meat of the strategy... I am a trendline trader. I only use support and resistance as added confirmations."*
* **[17:17]:** *"Your rule of thumb is that the stop loss should never be on the safety line. Because we anticipate price to respect the safety line."*
* **[33:32]:** *"We do not use indicators for our entries or exits or for this trendline break setup... We will just purely use our trend lines and price action."*