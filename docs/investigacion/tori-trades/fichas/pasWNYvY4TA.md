# Stop Losses DON�T Work (Use This Instead)

- Video: https://www.youtube.com/watch?v=pasWNYvY4TA
- Tipo esperado: metodo
- Duración: 17 min
- Modelo: gemini-3.8-flash
- Tokens de entrada: 60491

## Tipo y resumen
**Tipo:** Enseñanza del método (gestión de riesgo dinámica y colocación de stop loss con líneas de tendencia).  
**Resumen:**  
Tori Trades explica que utilizar stops fijos en soportes/resistencias horizontales o en pivotes previos suele provocar salidas prematuras al operar con líneas de tendencia [01:21, 01:35]. Presenta el concepto de *Safety Line* (línea de seguridad), una gestión de riesgo dinámica donde la línea de tendencia actúa como referencia móvil para el stop [02:15, 16:04]. Demuestra en un gráfico de Bitcoin cómo colocar el stop al otro lado de la línea con margen de maniobra (*wiggle room*) y moverlo progresivamente conforme avanza el precio [07:44, 10:41, 16:09].

---

## 1. Trazado de la línea
- **Anclas:** En el gráfico se observa que conecta los puntos máximos decrecientes con una línea diagonal roja sobre las mechas/extremos de las velas [04:54, 14:59].
- **Cuántos puntos:** En el gráfico se observan al menos 2 toques iniciales para proyectar la línea descendente [04:54, 14:59].
- **Qué hace válido un pivote:** No lo trata a nivel teórico en este video; remite al espectador a su clase magistral de 17 minutos y al video de análisis *top-down* [04:36].
- **Vela cerrada:** Menciona que algunos operadores esperan el cierre de la vela para confirmar la entrada tras la ruptura de la línea previa [05:11, 06:16].

---

## 2. Validez y calidad de una línea
- **Toques:** Muestra líneas trazadas con múltiples toques previos respetados (se observan líneas verdes y rojas en el gráfico de Bitcoin) [04:21, 04:54].
- **Pendiente/ángulo:** No lo trata.
- **Separación entre toques:** No lo trata.
- **Jerarquización:** No lo trata en detalle; solo menciona que el análisis *top-down* ya estaba realizado siguiendo sus reglas previas [04:31].

---

## 3. Ajuste de la línea vs línea nueva
- **Cuándo mueve el ancla / traza otra:** No explica la mecánica de redibujado de anclas en este video; muestra que ante la ruptura de la línea alcista verde previa, traza una nueva línea directriz bajista roja [04:54, 05:04].
- **Qué hace con la línea vieja:** En el gráfico se VE que mantiene la línea verde rota visible en la pantalla como referencia histórica de la estructura quebrada [04:54, 05:08].

---

## 4. Ruptura, confirmación y falsas rupturas
- **Qué cuenta como ruptura:** Explica que una ruptura real (*violation*) ocurre cuando el precio supera claramente la línea; no basta con tocarla o que una mecha traspase momentáneamente [08:50, 14:53, 16:15].
- **Retesteo:** Menciona y muestra que el precio frecuentemente regresa a probar o consolidar cerca de la línea de tendencia antes de continuar [08:37, 14:53, 16:21].
- **Cómo evita fakeouts:** Evita salidas en falso no colocando el stop exactamente sobre la línea de tendencia, sino dejándole margen detrás (*breathing room* / *wiggle room*) para tolerar mechas (*wicks*) o testeos [14:54, 15:26, 16:09].

---

## 5. Entrada
- **Gatillo exacto:** Explica que se puede entrar directamente ante la ruptura de una línea previa de contratendencia o esperando el cierre de la vela [05:08, 05:12, 06:16].
- **Tipo de orden:** No lo trata explícitamente (se asume mercado o stop en la ruptura, pero no detalla tipo de orden).
- **Temporalidad:** En el ejemplo del gráfico utiliza la temporalidad de 1 hora (1h) en TradingView [04:20, 04:54].

---

## 6. Stop / invalidación
- **Dónde y por qué:** El stop loss se sitúa al otro lado de la línea de tendencia opuesta (la *Safety Line*), no en la línea misma ni en soportes/resistencias horizontales [07:44, 10:16, 16:08]. Se coloca detrás con espacio suficiente para que fluctuaciones normales o mechas no lo activen [14:54, 16:09].
- **Uso de stop fijo vs dinámico:** Rechaza el stop fijo estático basado en dinero arbitrario o niveles horizontales para esta estrategia [01:05, 01:43]. Utiliza un stop dinámico (*dynamic risk* / *Safety Line*) que avanza con la línea de tendencia [02:16, 10:55].

---

## 7. Salida y objetivo
- **Criterio de salida:** La salida por invalidación/cierre se ejecuta cuando el precio viola y rompe formalmente la línea de tendencia que servía de guía [08:48, 14:00, 14:14].
- **Toma parcial:** No lo trata.
- **Cómo deja correr la ganancia:** Va deslizando (*trailing*) el stop loss a lo largo de la línea de tendencia a medida que el precio crea nuevos movimientos y oscilaciones a su favor, pasando de riesgo inicial a *breakeven* y finalmente protegiendo beneficios [10:41, 11:13, 13:58].

---

## 8. Gestión durante la operación
- **Qué toca:** Modifica manualmente el nivel del stop loss a lo largo de la línea de tendencia según avanzan las velas o pivotes [03:32, 10:43].
- **Qué no toca:** No permite que el miedo intervenga para mover el stop de forma prematura o arbitraria; el stop solo se mueve guiado estrictamente por la línea de tendencia y la estructura del precio [03:41, 03:49].

---

## 9. Temporalidades
- **Tendencia / entrada:** En el gráfico de demostración muestra temporalidad de 1 hora (1h) [04:20, 04:54].
- **Duración de operaciones:** Menciona que según la temporalidad del operador se puede ajustar el stop cada 5 minutos, cada 1 hora o cada 4 horas [03:20].

---

## 10. Soportes y resistencias horizontales
- **Uso y combinación:** DICE que los soportes y resistencias horizontales (o zonas de oferta y demanda) son válidos en el análisis técnico, pero NO se complementan bien como stop loss cuando se opera una estrategia basada en líneas de tendencia [01:21, 01:35, 05:59]. En el gráfico se VE que dibuja una línea horizontal amarilla (69.368) solo para ilustrar cómo ese stop horizontal fue barrido por un retroceso natural antes de que el precio cayera [05:46, 06:58].

---

## 11. Cuándo NO operar
- **Condiciones y filtros:** Si el tamaño de posición mínimo posible (1 contrato, 1 lote, 1 acción) excede el 1% o 2% de la cuenta debido a la distancia que requiere el stop detrás de la línea de tendencia con su respectivo margen, la operación DEBE dejarse pasar (*pass up*) [08:18, 08:27].
- **Noticias / rangos laterales:** No lo trata.

---

## 12. Riesgo y tamaño de posición
- Recomienda un riesgo inicial del 1% al 2% del capital [00:48, 08:24, 16:50].
- El tamaño de posición debe calcularse de forma dinámica: debe ser lo suficientemente reducido como para permitir la distancia necesaria entre el punto de entrada y la zona detrás de la línea de tendencia (*Safety Line*) sin sobrepasar el porcentaje de riesgo [08:08, 08:33, 15:23].

---

## 13. Instrumentos que opera
- Muestra explícitamente Bitcoin frente al dólar estadounidense (**BTCUSD** en Bitstamp) [04:20]. Menciona también aplicabilidad general en contratos, lotes o acciones [08:16].

---

## 14. Operaciones concretas mostradas
- **Operación 1:**
  - **Instrumento:** Bitcoin (BTCUSD / Bitstamp) [04:20].
  - **Temporalidad:** 1 hora (1h) [04:20].
  - **Líneas trazadas:** Línea verde de soporte ascendente rota; nueva línea de resistencia descendente roja (*Safety Line*) trazada sobre los máximos decrecientes [04:54, 05:03].
  - **Entrada:** En corto tras la ruptura/cierre por debajo de la línea verde en la zona de ~68.800 [05:25, 06:30].
  - **Stop tradicional vs Stop Safety Line:** El stop horizontal en 69.368 fue sacado en 69.500 [05:46, 06:58]. El stop con *Safety Line* se ubicó por encima de la línea roja descendente en ~70.518 [07:56, 10:16].
  - **Salida:** Se mantiene abierta y se va bajando el stop progresivamente a ~70.550, ~70.023, ~69.545 y ~69.820 conforme la línea y el precio descienden, cerrando únicamente cuando el precio viola la línea roja [10:44, 14:00].
  - **Resultado:** Operación ganadora con trailing stop en beneficios [10:29, 11:24].
  - **Lección:** Poner el stop en un nivel horizontal anterior te saca en el retroceso; colocarlo dinámicamente detrás de la directriz y darle holgura te permite capturar toda la tendencia [07:01, 09:16, 11:10].

---

## 15. Reglas verificables
1. **Regla de incompatibilidad de stops:** No utilizar niveles horizontales de soporte/resistencia ni pivotes anteriores estáticos como stop loss si la entrada y la tesis se basan en una línea de tendencia [01:31, 05:38].
2. **Regla de colocación de la Safety Line:** El stop loss debe situarse siempre al lado opuesto de la línea de tendencia que guía la operación [07:51, 10:10, 16:08].
3. **Regla de separación del stop (*Wiggle room*):** La línea de tendencia es el punto de referencia, nunca el lugar exacto del stop; el stop debe tener una distancia de amortiguación detrás de la línea para permitir mechas y testeos [14:48, 15:24, 16:04].
4. **Regla de filtro de riesgo / descarte de operación:** Si al usar el tamaño mínimo de posición (1 contrato/lote/acción) el stop detrás de la línea de tendencia supera el 1-2% del capital de la cuenta, la operación se debe descartar obligatoriamente [08:18, 08:27].
5. **Regla de trailing del stop:** A medida que el precio avanza en la dirección proyectada, el stop loss debe moverse siguiendo la pendiente de la línea de tendencia (de riesgo inicial a breakeven, y luego a beneficio) [10:41, 11:18].
6. **Regla de invalidación y salida:** La posición solo se cierra cuando el precio viola claramente la línea de tendencia de referencia [08:48, 14:00, 14:14].

---

## 16. Citas textuales clave
- [01:33] *"If you were trading a trend line strategy and you were implementing a support and resistance style stop loss, they do not complement each other."*
- [02:18] *"The Safety Line is not a static, fixed stop."*
- [08:49] *"It's got to clearly violate this downward trend line in order for a stop to get hit."*
- [16:03] *"The trend line is not your stop. It is your reference point. The stop loss should be on the other side of the trend line."*