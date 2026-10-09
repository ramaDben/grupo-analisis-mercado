# Everyone is trading Crude Oil, here�s why:

- Video: https://www.youtube.com/watch?v=cTecm-uk8FA
- Tipo esperado: metodo
- Duración: 26 min
- Modelo: gemini-3.7-flash
- Tokens de entrada: 93159

## Tipo y resumen
**Tipo:** Enseñanza de método y desglose de operación (backtesting y revisión paso a paso de setup A+).  
**Resumen:**  
Tori Trades desglosa una operación swing/intradía en futuros de Petróleo Crudo (MCL/CL) en gráfico de 1 hora, explicando su configuración "3+ Touchpoint Trendline Break".  
Muestra cómo alinea el contexto de alta volatilidad y momentum geopolítico con sus reglas técnicas de entrada por ruptura a mercado y control de riesgo mediante una directriz dinámica ("safety line").  
Modela dos formas de gestión y salida: toma de beneficios en resistencia horizontal previa al fin de semana, o seguimiento de tendencia mediante trailing stop dinámico sobre la directriz ascendente hasta su ruptura.

---

## 1. Trazado de la línea
- **Puntos de anclaje:** Utiliza los extremos de las mechas/pivotes del gráfico [11:00-11:05]. Se observa en pantalla cómo une los máximos decrecientes con una directriz bajista roja [06:46-06:50].
- **Cantidad de puntos:** Exige un mínimo estricto de 3 puntos de contacto ("3+ touchpoints") para validar la línea de tendencia antes del quiebre [10:42-10:45], [10:54-11:05].
- **Criterio de pivote válido:** El pivote debe respetar la línea de forma limpia sin perforaciones confusas y mostrar rechazo claro [11:00-11:06], [11:25-11:31].
- **Vela cerrada:** No exige vela cerrada para trazar la línea; los pivotes se identifican a posteriori sobre la estructura consolidada [11:00-11:05].

---

## 2. Validez y calidad de una línea
- **Número de toques:** Debe tener al menos 3 toques claros; los cuenta explícitamente en el gráfico: toque 1, toque 2 y toque 3 [11:00-11:05].
- **Separación temporal / cantidad de datos:** Regla explícita en su checklist: la directriz debe contar con más de una semana de datos históricos ("over a week's worth of data") [10:46], [11:21-11:24]. En el ejemplo, el toque 1 data del 8 de marzo y el quiebre ocurre el 27 de marzo [11:31-11:37].
- **Pendiente / Ángulo:** Requiere que exista una directriz de soporte ascendente o estructura complementaria bien definida para medir la cercanía y riesgo respecto a la entrada [08:15-08:21], [11:10-11:19].
- **Jerarquía:** Un setup A+ exige: mercado en tendencia, directriz con 3+ toques, precio cercano a la línea de seguridad (bajo riesgo) y más de una semana de información previa [10:47-11:45].

---

## 3. Ajuste de la línea vs línea nueva
- **Cuándo ajusta:** Cuando el precio rompe al alza, se extiende y luego hace una corrección profunda/consolidación, redibuja y reajusta la directriz bajista original para abarcar el nuevo swing de máximos [20:57-21:03].
- **Cuándo traza una nueva:** Traza una nueva directriz alcista ascendente ("safety line") conectando los nuevos mínimos crecientes que se forman tras el impulso [21:04-21:07].
- **Qué hace con la línea vieja:** Mantiene las líneas de soporte/resistencia mayores o directrices previas como referencia visual de niveles clave en el gráfico [21:00-21:08].

---

## 4. Ruptura, confirmación y falsas rupturas
- **Criterio de ruptura:** Al ser una "breakout trader" [07:11-07:12], opera el traspaso de la directriz. 
- **Espera de vela vs entrada directa:** Plantea el dilema de esperar al cierre de la vela de 1h o entrar en la ruptura [07:15-07:20]. Afirma que en mercados con fuerte volatilidad e impulso, esperar al cierre de una vela de 1 hora puede hacer que el precio avance demasiado lejos y se pierda el movimiento completo [07:33-07:45].
- **Retesteo:** No exige retesteo para su gatillo principal de ruptura de 3 toques [07:11-07:13], aunque en la checklist de TradeZella reconoce "Break & Retest" como una estrategia alternativa separada [10:41-10:44], [21:26-21:32].
- **Falsas rupturas:** Filtra los fakeouts asegurándose de que el mercado esté en un entorno de tendencia con momentum y volatilidad a favor, y no en rangos erráticos [01:34-01:38], [10:52-10:54], [23:24-23:31].

---

## 5. Entrada
- **Gatillo exacto:** Cruce/ruptura de la línea de tendencia bajista de 3 toques con el precio cotizando muy cerca de la línea de seguridad alcista ("low-risk setup") [07:11-07:13], [10:59-11:15].
- **Tipo de orden:** Orden a mercado ("market order") [07:55-07:57].
- **Temporalidad:** Gráfico de 1 hora (1h) [03:29-03:30], [06:48-06:50], [07:22-07:23].

---

## 6. Stop / invalidación
- **Ubicación:** No utiliza un stop de puntos fijos arbitrario; lo ancla a la estructura de mercado utilizando la directriz ascendente de soporte ("safety line") [08:00-08:05], [09:27-09:34].
- **Punto exacto inicial:** Sitúa la orden de stop loss justo debajo de la directriz alcista donde el precio violaría dicha estructura (en el ejemplo, colocado en 93.54 / 93.62 con entrada en 95.09) [09:59-10:22].
- **Stop fijo vs dinámico:** El stop es dinámico desde el diseño: comienza protegiendo el riesgo inicial y luego se va moviendo conforme avanza la estructura [09:37-09:50], [14:17-14:26].

---

## 7. Salida y objetivo
- **Criterio de salida:** Ofrece dos opciones válidas bajo su plan:
  1. **Salida por nivel clave horizontal:** Cerrar la posición al alcanzar una resistencia horizontal mayor donde el precio históricamente ha rebotado o rechazado (ej. 101.35 / 101.42) [16:07-16:11], [16:25-16:40], [18:41-18:50].
  2. **Salida por rotura de Safety Line:** Mantener la posición abierta hasta que una vela vulnere la directriz ascendente de seguimiento [18:16-18:21], [20:04-20:07].
- **Toma parcial:** En este desglose no ejecuta toma parcial; cierra el contrato completo o lo deja correr entero [18:41-18:49].
- **Cómo deja correr ganancias:** Mediante trailing stop basado en los nuevos mínimos crecientes (swing lows) que tocan o respetan la "safety line" [12:43-12:56], [13:03-13:26].

---

## 8. Gestión durante la operación
- **Qué toca:** Toca exclusivamente el nivel de stop loss para arrastrarlo hacia arriba (trailing stop) [12:43-12:56], [14:43-14:55].
- **Progresión del Stop:**
  1. Riesgo inicial ($155 de riesgo inicial en 93.54) [10:24-10:26].
  2. Ajuste a ganancia garantizada ($88 en 95.97) tras la formación del primer swing low [13:10-13:26].
  3. Ajuste a mayor beneficio ($178 en 96.87) tras el segundo swing low [14:50-14:57].
  4. Ajuste a $349 de beneficio asegurado en 98.58 tras el siguiente avance [15:56-16:01].
- **Frecuencia de ajuste:** No mueve el stop vela a vela; espera la confirmación de un swing low o retroceso respetado, lo que toma entre 3 y 5 velas de 1 hora entre ajustes [15:33-15:54].

---

## 9. Temporalidades
- **Temporalidad de análisis y entrada:** 1 hora (1h) tanto para trazar la estructura como para la ejecución [03:29-03:30], [06:48-06:50].
- **Duración de la operación:** Swing trading multihonorario a intradía prolongado; la operación mostrada transcurre a lo largo de varias horas durante la sesión del viernes 27 de marzo y se extiende hasta la apertura del domingo 29 de marzo [12:30-12:35], [17:27-17:34], [19:20-19:28].

---

## 10. Soportes y resistencias horizontales
- **Uso:** Sí los usa. Los proyecta a partir de niveles clave donde el precio ha pivotado y rechazado agresivamente en el pasado [16:25-17:07].
- **Combinación con líneas de tendencia:** Utiliza la línea de tendencia para la entrada/quiebre inicial y para el stop dinámico ("safety line"), y utiliza la resistencia horizontal previa (101.35) como objetivo potencial de recogida de beneficios o área de alerta por posible rechazo [16:07-16:45].

---

## 11. Cuándo NO operar
- **Riesgo excesivo por distancia:** Si la distancia entre el precio de ruptura y la línea de invalidación/safety line es demasiado amplia y no se puede reducir el tamaño de posición (ej. ya operando el mínimo de 1 micro contrato), la regla es dejar pasar la operación ("pass up on the trade") [08:47-08:58], [09:10-09:23].
- **Falta de condiciones de mercado:** No operar rupturas si el mercado carece de tendencia o volatilidad clara, ya que las rupturas tienden a fallar en consolidaciones estrechas sin momentum [01:34-01:38], [10:52-10:54], [23:24-23:31].

---

## 12. Riesgo y tamaño de posición
- **Porcentaje de riesgo:** Arriesga típicamente entre el 1% y el 2% del capital de la cuenta [14:21-14:23].
- **Cálculo del tamaño:** Si la distancia entre la entrada y la safety line es grande, se debe reducir el tamaño de la posición (bajar cantidad de contratos) para mantener la pérdida monetaria fija [08:44-08:47], [09:00-09:08].
- **Trade mostrado:** 1 contrato de Micro Crude Oil (MCL), con un riesgo monetario inicial calculado en $155 [10:24-10:26].

---

## 13. Instrumentos que opera
- **Futuros de Petróleo:** 
  - Micro Crude Oil Futures (ticker: MCL) [06:21], [06:48].
  - Light Crude Oil Futures estándar (ticker: CL) [10:41], [19:08], [25:51-26:15].
- Menciona que el modelo también se aplica a CFDs adaptando el lotaje [08:52-08:56].

---

## 14. Operaciones concretas mostradas
- **Operación principal desglosada (MCL / CL):**
  - **Instrumento:** Futuros de Micro Petróleo Crudo (MCL) en TradeZella y TradingView [06:48], [19:08].
  - **Temporalidad:** 1 hora (1h) [03:29], [06:48].
  - **Líneas trazadas:** Directriz bajista roja de 3 toques conectando máximos desde el 8 de marzo hasta el 27 de marzo de 2024 [11:00-11:37]; directriz alcista verde ("safety line") conectando mínimos crecientes [08:18-08:21], [09:27-09:34].
  - **Entrada:** Orden de compra a mercado tras la ruptura de la directriz bajista en 95.09 [09:54-09:55], [10:20-10:23].
  - **Stop inicial:** Stop en 93.54 (debajo de la safety line), con riesgo inicial de $155 [10:20-10:26].
  - **Gestión:** Trail stop a 95.97 (+ $88 garantizados) [13:14-13:26], luego a 96.87 (+ $178) [14:50-14:57], y luego a 98.58 (+ $349) [15:56-16:01].
  - **Salida Escenario A (mostrado en TradeZella):** Cierre manual en la resistencia horizontal de 101.35 el viernes antes del cierre semanal [18:41-18:50].
  - **Resultado Escenario A:** Ganancia de $629 (+4.05R sobre el riesgo inicial de $155) [18:45-18:47].
  - **Salida Escenario B (mostrado en TradingView Replay):** Mantiene la posición durante el fin de semana, el precio abre con gap alcista el domingo y sale cuando el precio cruza la safety line en la zona de 101.40 [20:02-20:10].
  - **Lección:** No arrepentirse de cerrar en una resistencia antes del cierre semanal si el plan lo contempla, ya que el mercado consolidó durante horas justo después de dicho nivel [22:27-22:45].

---

## 15. Reglas verificables
1. **Regla del número de toques:** Una directriz sólo es válida para operar su ruptura si tiene un mínimo de 3 puntos de contacto previos comprobados [10:42-10:45], [10:54-10:56].
2. **Regla de historial de la directriz:** La directriz debe abarcar al menos una semana entera de datos acumulados antes de la ruptura ("over a week's worth of data") [10:46], [11:21-11:24].
3. **Regla de proximidad al soporte (Safety Line):** La entrada solo se ejecuta si el precio se encuentra inmediatamente cercano a la línea de seguridad alcista para garantizar un riesgo acotado [11:10-11:15].
4. **Regla de descarte por exceso de riesgo:** Si la distancia a la safety line supera el límite de riesgo de la cuenta y no es posible fraccionar la posición por debajo de 1 contrato, la orden no se ejecuta y se descarta el trade [08:48-08:58], [09:10-09:23].
5. **Regla de trailing stop por swing lows:** El stop loss únicamente se actualiza al alza cuando el precio genera un nuevo swing low o retroceso confirmado que respete la directriz de seguridad ascendente [12:48-12:56], [14:36-14:43].
6. **Regla de salida dual obligatoria:** El cierre de la posición se ejecuta obligatoriamente bajo uno de dos desencadenantes: llegada y testeo de resistencia horizontal mayor, o perforación del precio a través de la safety line [16:20-16:35], [18:16-18:21].

---

## 16. Citas textuales clave
- [07:11] *"I'm a breakout trader. This is signaling an entry for me."*
- [07:33] *"If we're waiting for an entire candle to close, an entire one-hour candle to close, price could move so fast, so far from your entry that you might miss the entire move..."*
- [08:00] *"I use market structure to help me identify where to place my stop."*
- [09:10] *"Second thing you can do: pass up on the trade. Hardest thing to do, not many traders can do it."*
- [14:17] *"So you just have to understand that the risk is incredibly dynamic. It moves from that initial 1 to 2% of risk and then, as price progresses, you get to move it to break even, then you get to move it in profit."*