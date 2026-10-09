# Unfortunately, trading really is this simple

- Video: https://www.youtube.com/watch?v=gokPlEnlhuE
- Tipo esperado: metodo
- Duración: 19 min
- Modelo: gemini-3.7-flash
- Tokens de entrada: 66871

## Tipo y resumen
**Tipo:** Enseñanza del método (con demostración práctica en modo replay).  
**Resumen:**  
Tori Trades explica su sistema de trading basado en la premisa «la tendencia es tu amiga hasta el final» [00:58]. Enseña a estructurar un abanico de líneas de tendencia conectadas mediante un análisis *top-down* desde el gráfico mensual hasta el horario [04:12, 08:38]. Demuestra cómo ejecutar compras/ventas en el rebote de la línea operativa y mantener la posición hasta que el precio cierre al otro lado de la misma [13:10, 16:22].

---

## 1. Trazado de la línea
- **Herramienta:** Utiliza la herramienta *Ray* (semirrecta) en TradingView [02:29].
- **Anclas:** En tendencia alcista, inicia en el punto más bajo visible como Punto A y busca capturar la mayor cantidad de puntos de contacto (*swing lows*) sin que el precio se corte o interseque [02:33, 05:18]. En tendencia bajista, inicia en el punto más alto visible como Punto A y conecta *swing highs* [03:01, 10:17].
- **Mechas vs. cuerpos:** En el gráfico se observa claramente que ancla las líneas en los extremos exactos de las mechas (*wicks*) de los mínimos y máximos [02:34, 05:13, 09:25, 10:21].
- **Cantidad de puntos:** Requiere un mínimo de 2 puntos (Punto A y Punto B) [05:26, 07:41], buscando conectar la mayor cantidad de toques posibles (ej. 3 toques) [07:06].
- **Qué hace válido un pivote:** No da una definición matemática de pivote; visualmente toma los valles (*swing lows*) y crestas (*swing highs*) prominentes de la estructura [02:14, 04:57].
- **Vela cerrada:** No especifica si espera vela cerrada para trazar el pivote inicial («No lo trata»).

---

## 2. Validez y calidad de una línea
- **Toques:** Cuantos más toques tenga sin ser intersecada, mejor captura la trayectoria del precio [02:36, 05:18]. Muestra líneas con 2 y 3 toques [07:06, 07:41].
- **Pendiente / Ángulo:** Explica que a medida que el precio acelera su movimiento, las líneas se vuelven progresivamente más empinadas (*steeper*), formando un abanico (*fan*) [06:38, 06:47, 07:49].
- **Separación entre toques:** Reconoce que puede haber separaciones temporales cortas o huecos muy amplios entre toques, pero aclara que eso no invalida la línea mientras capture la velocidad e intensidad del movimiento [07:12, 07:16].
- **Jerarquización (buenas vs. malas):** Califica de «malas/aleatorias» las líneas trazadas de forma aislada en un marco temporal menor sin conexión estructural [03:45, 04:04]. Las líneas de alta calidad son aquellas ancladas jerárquicamente desde marcos temporales superiores [04:14, 08:24].

---

## 3. Ajuste de la línea vs. línea nueva
- **Regla para trazar una nueva línea:** La regla general (*rule of thumb*) es que el Punto B previo (el último toque de la línea anterior) se convierte en el Punto A (inicio) de la nueva línea más empinada [06:11, 06:58, 07:27, 07:37].
- **Cuándo ajusta la línea:** Al bajar de temporalidad (de mensual a semanal, diario u horario), la mayor cantidad de velas hace que las líneas se vean desalineadas (*wonky*); en ese momento mueve el Punto B a las mechas exactas de los nuevos mínimos observados para ganar precisión [08:58, 09:22, 11:10, 12:01].
- **Qué hace con la línea vieja:** Mantiene todas las líneas anteriores dibujadas en el gráfico; no las borra, formando un abanico de soporte estructural [08:02, 08:21].

---

## 4. Ruptura, confirmación y falsas rupturas
- **Qué cuenta como ruptura:** Se considera ruptura cuando el precio vulnera la línea y una vela cierra a través de ella (*closes through the line*) [16:23, 16:31, 17:34].
- **Mecha vs. Cuerpo:** Una mecha que solo toca o rebota respeta la línea [16:18]; la violación requiere el cierre de la vela perforándola [16:24, 17:34].
- **Retesteo:** No exige retesteo para confirmar la ruptura; el mero cierre a través de la línea es la señal de salida [16:29, 17:37].
- **Falsas rupturas:** No trata filtros específicos para evitar *fakeouts* («No lo trata»).

---

## 5. Entrada
- **Gatillo exacto:** El precio retrocede hasta la línea de tendencia («Action Line»), la toca/testea y muestra rechazo (*bounce / rejection*) respetando la línea [13:06, 13:12, 14:43].
- **Tipo de orden:** Orden a mercado (*Market Order*) ejecutada en la plataforma [15:24].
- **Temporalidad de entrada:** Gráfico de 1 hora (1h) [12:18, 15:26].

---

## 6. Stop / invalidación
- **Uso de stop loss fijo:** **NO** utiliza una orden de stop loss fija en la boleta de orden [15:24]. Se observa en la pantalla que deja las casillas de *Stop loss* y *Take profit* desactivadas [15:24].
- **Mecanismo de invalidación:** La propia línea de tendencia actúa como «Línea de Seguridad» (*Safety Line*) [15:46, 15:56]. La invalidación es manual y ocurre en el momento en que una vela cierra a través de la línea [16:23, 17:37].

---

## 7. Salida y objetivo
- **Criterio de salida:** Cerrar la posición cuando el precio rompe y cierra al otro lado de la línea de seguridad [16:29, 17:37].
- **Objetivo / Target:** No utiliza objetivos de precio fijos ni ratios R:R predefinidos [15:24].
- **Toma parcial:** No la trata (no realiza cierres parciales; cierra la posición completa al darse la señal) [17:38].
- **Cómo deja correr ganancias:** Mantiene la operación abierta mientras las velas continúen rebotando y haciendo máximos/mínimos más altos por encima de la línea («la tendencia es tu amiga hasta el final») [14:01, 17:10, 17:21].

---

## 8. Gestión durante la operación
- **Qué toca y qué no toca:** No ajusta stops automáticos ni añade contratos [16:38 - 17:40]. Observa vela tras vela cómo fluctúa el flotante (soportando retrocesos de decenas de miles de dólares) [16:55, 17:53], esperando únicamente la condición de cierre de vela fuera de la línea [17:26].

---

## 9. Temporalidades
- **Análisis de tendencia (*top-down*):** Mensual (1M) [04:17], Semanal (1W) [09:05], Diario (1D) [11:00], 4 horas (4h) [11:38].
- **Entrada y gestión:** 1 hora (1h) [12:18]. Menciona que operadores intradía pueden descender a 30m o 5m [08:47, 08:50].
- **Duración de operaciones:** Swing trading multidía (la operación mostrada dura del 1 al 10 de agosto, 9-10 días) [15:26, 17:39].

---

## 10. Soportes y resistencias horizontales
No lo trata. Su metodología en este video se basa exclusivamente en líneas de tendencia diagonales y dinámicas.

---

## 11. Cuándo NO operar
No lo trata. No menciona filtros de noticias, sesiones específicas ni condiciones de mercado lateral que prohíban operar.

---

## 12. Riesgo y tamaño de posición
- Explica que para la demostración usa 1 contrato estándar de futuros de oro (*E-mini/Standard GC*), advirtiendo que genera fluctuaciones monetarias grandes [15:01, 15:09].
- Menciona que operadores con cuentas pequeñas deben utilizar contratos *Micro* (MGC), cuyo valor es 1/10 del contrato grande y reduce la barrera de entrada y el riesgo [15:13, 15:17].
- No especifica porcentaje de cuenta arriesgado por operación («No lo trata»).

---

## 13. Instrumentos que opera
- En pantalla muestra que el sistema aplica a Acciones (*Stocks*), Cripto, Futuros e Índices [00:22].
- En el video opera y analiza:
  - Futuros de Oro (*Gold Futures* / GC1!) [04:17, 15:00].
  - Muestra fugazmente gráficos de Platino (*Platinum Futures*) [03:46] y Bitcoin [08:38].

---

## 14. Operaciones concretas mostradas
- **Instrumento:** Futuros de Oro (*Gold Futures* - GC1! en COMEX) [04:17, 15:26].
- **Temporalidad:** 1 hora (1h) tras análisis mensual, semanal, diario y 4h [12:18].
- **Líneas trazadas:** Abanico de líneas alcistas mensuales y semanales, línea bajista semanal desde el máximo histórico, y línea de tendencia alcista de 4h/1h [10:46, 12:03].
- **Entrada:** Compra a mercado de 1 contrato en el rebote sobre la línea de tendencia alcista de 1h el 1 de agosto [15:24].
- **Stop:** Sin stop físico; invalidación definida por un cierre horario por debajo de la línea de tendencia alcista [15:24, 16:29].
- **Salida:** Cierre manual a mercado tras vela de 1h que rompe y cierra por debajo de la línea el 10 de agosto [17:36 - 17:40].
- **Resultado:** Ganancia de +$27,700 dólares [17:30].
- **Lección:** Entrar cuando el precio valida la línea («Action Line»), tolerar las fluctuaciones del flotante mientras se respete («Safety Line») y ejecutar la salida disciplinadamente en cuanto se produce el cierre fuera [17:42, 18:13].

---

## 15. Reglas verificables
1. **Inicio del análisis en el máximo histórico de datos:** Comenzar el análisis en el gráfico mensual (1M) en el punto de origen más antiguo disponible de los datos [04:26, 04:34].
2. **Primer trazo alcista:** Trazar la primera semirrecta desde el mínimo absoluto visible (Punto A) conectando el siguiente mínimo relevante (Punto B) sin cortar velas intermedias [02:33, 05:27].
3. **Encadenamiento de abanico:** Para trazar una línea más empinada, el Punto B de la línea anterior debe ser obligatoriamente el Punto A de la nueva línea [06:11, 06:58].
4. **Secuencia temporal descendente:** Realizar el análisis en orden estricto: Mensual -> Semanal -> Diario -> 4 Horas -> 1 Hora [08:38 - 08:43].
5. **Ajuste en marcos menores:** Al reducir la temporalidad, ajustar los puntos de anclaje a las mechas exactas de los pivotes si la línea quedó desfasada [09:22, 11:11].
6. **Identificación de la línea de acción:** Marcar como «Action Line» la línea de tendencia activa del marco operativo (1h) hacia la cual retrocede el precio [14:42, 14:50].
7. **Gatillo de entrada en rebote:** Ejecutar orden a mercado en la dirección de la tendencia cuando el precio toque la línea y muestre rechazo sin haber cerrado al otro lado [13:06, 15:24].
8. **Condición de salida obligatoria:** Cerrar la posición a mercado inmediatamente después de que una vela cierre a través de la línea de seguridad [16:23, 17:37].

---

## 16. Citas textuales clave
- [00:58] *"The trend is your friend until the end."*
- [06:11] *"My rule of thumb is the previous swing low or the last touch point that you got on your last trendline will be your starting point for your new trendline."*
- [14:41] *"This line that price is respecting, I like to call an action line... this is my line that's indicating get into a trade, take action."*
- [15:56] *"That is our safety line. Action line, safety line, all the same line when we're doing this bounce scenario."*
- [16:22] *"As soon as price violates and closes through the line, we are no longer safe. That is our indication until the end to close the trade."*