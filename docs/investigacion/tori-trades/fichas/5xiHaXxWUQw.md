# My exact playbook to review and journal my trades

- Video: https://www.youtube.com/watch?v=5xiHaXxWUQw
- Tipo esperado: metodo
- Duración: 16 min
- Modelo: AGY gemini-3.5-flash
- Tokens de entrada: 54662

Aquí tienes el análisis detallado del método de trading de Tori Trades basado de forma exclusiva en el video proporcionado.

---

## Tipo y resumen
* **Tipo**: Desglose de operación (trade breakdown) combinado con enseñanza de bitácora y registro de operaciones (*journaling*).
* **Resumen**: Tori analiza una operación histórica personal de $30,000 en futuros de Platino utilizando su estrategia de ruptura de línea de contratendencia de 3 toques. Detalla cómo registra la operación en TradeZella a través de su "Playbook", analizando criterios de entrada, salida, gestión del riesgo y errores cometidos. Enfatiza que llevar un registro simple de las operaciones es indispensable para identificar patrones repetitivos, corregir la indisciplina emocional (como el FOMO) y mejorar la consistencia.

---

## 1. Trazado de la línea
* **DICE**: Menciona que traza una línea de tendencia bajista ("downward trendline") que requiere tres puntos de contacto o pivotes: "punto A, punto B, punto C" [00:42]. También traza una línea de tendencia alcista de seguridad ("safety line") [00:47].
* **VE**: En el gráfico de TradingView de la plataforma [00:39], se observa que Tori traza la línea rosa bajista uniendo los máximos (utilizando las mechas superiores de las velas de 4 horas). La línea de seguridad verde (alcista) se traza uniendo de forma consecutiva los mínimos ascendentes (mechas inferiores) formados a partir de la ruptura del precio.

---

## 2. Validez y calidad de una línea
* **DICE**: Para que la línea de tendencia de ruptura de su playbook sea válida, debe cumplir de manera estricta con dos condiciones: tener al menos 3 puntos de contacto ("has to have 3 touchpoints") [04:14] y acumular más de una semana de datos de movimiento de precio detrás de ella ("over a week's worth of data behind this line") [02:01, 04:46].
* **VE**: En el gráfico de TradingView se observa que los tres puntos de contacto en la línea de contratendencia rosa están claramente definidos y separados por varios días a lo largo del mes de marzo de 2024, lo que le da validez temporal e histórica a la línea. No se especifican ni se miden ángulos o pendientes matemáticas concretas.

---

## 3. Ajuste de la línea vs línea nueva
* **DICE**: Explica que a medida que el precio se acelera y se aleja de la línea de tendencia de seguridad original, el trader puede optar por trazar una línea más empinada para rastrear el precio de cerca y asegurar la mayor cantidad de ganancia posible ("could have came in and tracked this real steep and capitalized on as much of that profit as I could") [01:08].
* **VE**: Muestra visualmente en el gráfico cómo dibuja una línea verde alternativa más empinada ajustada a los últimos mínimos ascendentes generados durante la aceleración del precio [01:04, 02:50].

---

## 4. Ruptura, confirmación y falsas rupturas
* **DICE**: El sistema busca la ruptura ("break") de la línea de contratendencia de 3 toques [01:14]. Tras la ruptura, el precio puede volver a entrar en pérdidas temporales ("drawdown"), pero la posición sigue siendo válida siempre y cuando el precio respete la línea de tendencia de seguridad alcista ("it's still respecting my safety line") [00:53, 00:56].
* **VE**: La ruptura se confirma visualmente cuando el cuerpo de una vela de 4 horas cierra por encima de la línea rosa bajista [00:46]. No requiere un retesteo perfecto en el gráfico para validar la entrada.

---

## 5. Entrada
* **DICE**: La entrada se ejecuta tras confirmarse la ruptura de la línea de contratendencia ("we've got an entry here") [00:49]. Su playbook estipula que, para que sea una entrada de bajo riesgo, el precio de entrada debe estar lo más cerca posible de la línea de seguridad alcista ("low risk setup - price close to safetyline") [04:23, 10:13].
* **VE**: En el gráfico se observa que la entrada (marcada con un círculo azul) se realiza inmediatamente después de la vela de ruptura, apoyándose prácticamente sobre la línea de seguridad verde recién proyectada [00:49]. No se especifica en el video si utiliza órdenes de tipo *limit* o *market*.

---

## 6. Stop / invalidación
* **DICE**: La invalidadación lógica de la estructura ocurre cuando el precio cruza o rompe la línea de tendencia de seguridad alcista ("safety line") [10:01]. Aclara que ella gestiona la operación con stops dinámicos a medida que el precio avanza a su favor para mitigar el riesgo ("since we trade trailing stops and as price progresses, our risk gets mitigated") [06:53]. No obstante, para registrar el peor escenario posible en TradeZella (en caso de que el trade se fuera inmediatamente en su contra), introduce un Stop Loss inicial fijo [07:14].
* **VE**: En la plataforma TradeZella se muestra un "Stop Loss" inicial fijo configurado en el nivel de 904.0 [06:36, 07:22].

---

## 7. Salida y objetivo
* **DICE**: El criterio de salida ideal según las reglas de su playbook es cuando el precio cruza y rompe la línea de tendencia de seguridad ("safetyline crossed") [04:52]. Sin embargo, en esta operación específica, Tori decidió salir manualmente al tocar un nivel clave de soporte y resistencia horizontal debido al agotamiento de la operación y al ver una suma récord de dinero en ganancias ("resorted to exiting based on a key level / support resistance due to trade exhaustion and record dollar amounts") [10:41]. Cerró la operación en torno al nivel 946 - 947 [01:13, 02:49]. No se menciona la toma de ganancias parciales en este video.
* **VE**: En el gráfico se observa que cierra manualmente la operación completa al interactuar con una resistencia horizontal (línea amarilla) antes de que el precio tocara o rompiera la línea de seguridad verde.

---

## 8. Gestión durante la operación
* **DICE**: Mientras la operación esté abierta, no se toca el stop a menos que sea para reducir el riesgo de manera dinámica a favor del precio ("our risk gets reduced as price continues in our favor") [07:00]. El precio puede experimentar fluctuaciones o drawdowns repetidos hacia la línea de seguridad, pero la posición debe mantenerse abierta si dicha línea no se quiebra [00:53, 01:01].
* **VE**: El precio retrocede en tres ocasiones hacia la línea de seguridad verde [00:53, 00:58, 01:01], pero Tori no altera la posición hasta su salida manual definitiva en la resistencia horizontal.

---

## 9. Temporalidades
* **DICE**: No define una regla general de temporalidades en el video, pero explica que este trade específico se ejecutó y analizó en la temporalidad de 4 horas.
* **VE**: En la parte superior izquierda de la pantalla de TradingView se visualiza "Platinum Futures • 4h • NYMEX" [00:39]. En TradeZella se observa que la operación duró aproximadamente del 25 de marzo al 3 o 4 de abril de 2024 [03:22].

---

## 10. Soportes y resistencias horizontales
* **DICE**: Sí los utiliza y los integra en su diario de trading. Salió de la operación en un nivel horizontal clave donde el precio del Platino había rebotado y cambiado de dirección múltiples veces en el pasado ("where the price of platinum had hit multiple times in the past and then turned around") [01:18, 10:33]. Combina este concepto con su playbook en TradeZella bajo el criterio de salida "S/R hit" (Soporte/Resistencia tocado) [04:54].
* **VE**: En TradingView se muestra una línea horizontal amarilla gruesa trazada exactamente en el nivel de 946.1 [00:40], la cual actúa como la resistencia que detona su salida manual.

---

## 11. Cuándo NO operar
* **DICE**: Tori establece que se debe evitar operar cuando el mercado se encuentra en un periodo de consolidación o rango lateral en lugar de una tendencia clara [05:13]. De hecho, registra la etiqueta "consolidation" (consolidación) dentro de la sección de errores en su bitácora [08:13].
* **VE**: En el gráfico de TradeZella, muestra una zona de oscilación plana que identifica como consolidación, señalando que allí no se debió abrir ninguna operación [05:22, 05:39].

---

## 12. Riesgo y tamaño de posición
* **DICE**: Explica que entrar al mercado con 20 contratos de Platino para este trade representó un setup de riesgo muy elevado [02:13], mientras que operar con su tamaño estándar de 10 contratos habría constituido un setup de riesgo bajo ideal ("with 10 contracts this would have been an A+ setup across the board") [02:19, 04:29]. El riesgo inicial asumido fue de $14,730.00 para ir en busca de un beneficio neto de más de $30,000.00 [06:41].
* **VE**: En la interfaz de TradeZella se documenta lo siguiente: "Contracts traded: 20", "Net P&L: $30,121.00" y "Trade Risk: -$14,730.00" [03:22, 06:40].

---

## 13. Instrumentos que opera
* **DICE**: Menciona explícitamente "Platinum" (Platino) [02:14].
* **VE**: En el gráfico de TradingView se observa el ticker de futuros de Platino "PL1!" (NYMEX) [00:39] y en TradeZella se muestra el ticker del contrato "PLN24" [03:22].

---

## 14. Operaciones concretas mostradas
* **Operación 1**:
    * **Instrumento**: Futuros de Platino (PL1! / PLN24) [00:39, 03:22].
    * **Temporalidad**: 4 horas (4h) [00:39].
    * **Líneas trazadas**: Una línea de contratendencia bajista rosa con tres puntos de toque (A, B, C); una línea de tendencia de seguridad alcista verde ("safety line"); y una línea de resistencia horizontal amarilla en 946.1 [00:40, 00:42].
    * **Entrada**: Ejecutada entre el 25 y 26 de marzo de 2024 tras la ruptura de la línea bajista rosa [00:49, 11:44]. (Tori menciona que tuvo que reingresar tras cometer el error de abrir la posición en un contrato de Platino que estaba por vencer [11:34]).
    * **Stop**: Stop Loss inicial fijo registrado en 904.0 [06:36, 07:22].
    * **Salida**: Salida manual en el nivel de resistencia horizontal de 946.0 - 947.0 el 3 de abril de 2024 [01:13, 03:22].
    * **Resultado**: Ganancia neta de $30,121.00 con un R-múltiple realizado de 2.04 [03:22, 07:44].
    * **Lección**: Operar con un tamaño de posición excesivo (20 contratos en vez de 10) elevó innecesariamente el riesgo [02:11]. Asimismo, salir prematuramente en una resistencia horizontal en lugar de esperar a que se rompiera la línea de seguridad alcista le impidió obtener más ganancias [02:46]. Adicionalmente, aprendió a verificar siempre la fecha de vencimiento del contrato antes de operar [11:18].

---

## 15. Reglas verificables
1. Para que una línea de contratendencia sea considerada válida en el playbook de rupturas, debe poseer obligatoriamente un mínimo de 3 puntos de contacto ("touchpoints") [04:14].
2. La línea de contratendencia a operar debe acumular como mínimo más de una semana de datos de movimiento de precio detrás de ella para poder ser trazada [02:01].
3. Un setup se define como "bajo riesgo" únicamente si el tamaño de la posición no excede los 10 contratos (en Platino) y el precio se ubica cerca de la línea de seguridad al momento de entrar [02:19, 04:23].
4. En el diario de trading, a cualquier operación que se cierre con ganancias netas se le asignan de manera obligatoria y automática 2 estrellas de calificación iniciales ("Profit is profit... two stars right off the bat") [10:59].
5. Cualquier operación que se inicie mientras el mercado se encuentra en una fase de rango lateral o consolidación debe ser etiquetada bajo la categoría de error del sistema ("Mistakes: consolidation") [08:18].

---

## 16. Citas textuales clave
* `[01:08]` "Could have came in and tracked this real steep and capitalized on as much of that profit as I could."
* `[01:59]` "We've got over a week's worth of data here... over a week's worth of price movement behind this line."
* `[02:13]` "I went in 20 contracts in platinum and created a higher risk setup."
* `[06:53]` "Since we trade trailing stops and as as price progresses, our risk gets mitigated..."
* `[10:59]` "Profit is profit, even if you made a crummy trade, profit is profit."
* `[12:44]` "Especially for the newbies... I think it's an incredibly resourceful tool regardless of whatever journal you use."
