# Metodología de líneas de tendencia (doctrina)

> **Estado: borrador para revisión del director (2026-10-09).** No cambia todavía ninguna pieza
> ni ningún cálculo. Cuando se apruebe, alimenta dos trabajos con su propio spec: el motor que
> traza las líneas (subproyecto 2) y los textos y gráficos del carrusel, el informe, Avisos y la
> pieza semanal (subproyecto 3).

## De dónde sale

Del canal de YouTube de Tori Trades (swing trading con líneas de tendencia). Se documentaron
**57 videos**: 44 de método y 13 de desglose de operaciones reales. Cada video tiene una ficha
con el minuto de cada afirmación, y de las fichas se extrajeron **496 reglas** que acá se fusionan.
La evidencia completa está en `docs/investigacion/tori-trades/`.

**Cómo leer la fuerza de cada regla.** El número entre corchetes es en cuántos videos distintos
aparece la regla. Lleva cuatro etiquetas:

- **Núcleo**: aparece en 10 videos o más. Es el método.
- **Firme**: aparece en 4 a 9 videos.
- **Aislada**: aparece en 1 a 3 videos. Se adopta solo si no choca con el núcleo.
- **Dudosa**: solo la respaldan fichas de modelos débiles, o choca con el núcleo.

El conteo es aproximado. Los lotes no comparten videos, pero dentro de cada lote junté a mano
reglas casi iguales, así que un video puede haber quedado contado dos veces. Las etiquetas aguantan
ese margen; el número exacto no.

Las fichas marcadas con `*` en la evidencia son de `gemini-2.5-flash` o `flash-lite`. Esos modelos
leen peor el gráfico, así que esas fichas pesan menos como evidencia.

**Lo verificado contra el video.** Las fichas son lo que leyó un modelo, no el video. Las reglas
que deciden algo programable o resuelven una contradicción llevan una marca **[V#]**. Esa marca
remite a una de las 20 consultas sobre el tramo exacto del video, todas hechas (§6). El resto de
las reglas se sostiene por el conteo de fichas.

**Lo que dice la teoría clásica.** Cada regla del método tiene su respaldo en Murphy y en la
Teoría de Dow, o la declaración honesta de que no lo tiene, en §7.

La evidencia se cita como `ID [mm:ss]`, donde `ID` son los primeros caracteres del video.

---

## 1. El método en diez reglas

1. **Solo líneas diagonales y precio.** No usa indicadores. Los soportes y resistencias
   horizontales sirven de confluencia, de objetivo y para delimitar un rango, pero no generan
   entradas.
2. **Cómo se traza.** La línea es una semirrecta que parte del pivote más extremo a la vista: el
   mínimo más bajo para la alcista y el máximo más alto para la bajista. Se ancla en la **mecha**,
   y el segundo punto se busca para tocar la mayor cantidad de pivotes **sin que ninguna vela
   cruce la línea** entre el ancla y el precio actual.
3. **Cuándo una línea vale.** Con 3 toques o más y al menos una semana de datos es una línea A+.
   Con 2 toques se puede operar, pero es un setup de menor calidad. Una línea de temporalidad
   mayor pesa más que una de temporalidad menor.
4. **Las líneas se encadenan.** El último toque de una línea es el primer punto de la siguiente.
   Cuando el precio acelera, se traza una línea más empinada (un abanico) sin borrar la principal.
5. **Primero el contexto, después la entrada.** El análisis va de arriba hacia abajo: mensual,
   semanal, diario y 4H. El swing se opera en **4H**, y se baja a 1H cuando la volatilidad es
   alta.
6. **Qué es una ruptura.** Ella entra cuando el precio **cruza** la línea, y esperar el **cierre**
   de la vela le parece igual de válido. El sistema publica con el cierre (ver 2.4). Una mecha que
   cruza y vuelve no cuenta. El retesteo es otra confirmación posible, no un requisito.
7. **La entrada.** Va a mercado y en la dirección de la ruptura. La línea rota es la **línea de
   acción**; la opuesta, que queda a favor de la operación, es la **línea de seguridad**. El setup
   es de bajo riesgo cuando el precio está cerca de la línea de seguridad.
8. **El stop y la gestión.** El stop va **al otro lado de la línea de seguridad**, con un margen,
   y nunca es un stop fijo en puntos. Se arrastra a lo largo de esa línea: primero a break-even y
   después a ganancia.
9. **La salida.** Se cierra la posición completa cuando una vela cierra al otro lado de la línea
   de seguridad. No hay take profit fijo ni parciales. La alternativa válida es cerrar en un
   soporte o resistencia horizontal mayor.
10. **Cuándo no se opera.** En consolidación o rango lateral, y cuando el precio quedó lejos de
    la línea de seguridad. Con la operación abierta no se mueven las líneas ni se baja de
    temporalidad.

---

## 2. Las reglas por tema

### 2.1 Trazado

| Regla | Fuerza | Evidencia |
|---|---|---|
| Se ancla en el **extremo de la mecha** del pivote, no en el cuerpo. | Núcleo [27] | LpXZB [03:06], OjZ8d [02:51], qLtq7 [04:00] (lo dice), ipUbs [04:10], Y8efW [17:05], xMNO4 [07:43], E6dUU [04:38] |
| Se traza con la herramienta **semirrecta** (Ray de TradingView), proyectada hacia la derecha. | Firme [9] | LpXZB [03:00], PnIkS [02:51], ipUbs [03:45], qLtq7 [01:10], Y8efW [16:59], ZMIDT [07:50] |
| El primer punto es el **extremo visible**: el mínimo más bajo para la alcista y el máximo más alto para la bajista. | Firme [8] | LpXZB [03:06], PnIkS [08:00], TuXOg [01:29], ipUbs [04:08], qLtq7 [01:42], gokPl [02:33], xRxUo [00:42] |
| El segundo punto se elige para **tocar la mayor cantidad de pivotes sin que el precio cruce la línea**. | Firme [9] | LpXZB [03:06], PnIkS [09:03], TuXOg [01:23], Y8efW [31:27], gokPl [02:33], yHAC0* [03:38] |
| **No intersección:** ninguna vela, ni su cuerpo ni su mecha, puede cruzar la línea entre el ancla y el precio actual. Si no se puede trazar limpia, no se traza. Verificado en [V10]: "if you have a trend line that is going through wicks or going through bodies, that is an incorrect trend line". | Núcleo [13] | qLtq7 [01:33], qLtq7 [01:43], ipUbs [04:26], LpXZB [03:08], PnIkS [08:34], xMNO4 [07:50], Y8efW [32:15] |
| Si al extender la línea esta corta una vela intermedia, el segundo punto se mueve al toque limpio anterior. | Aislada [1] | qLtq7 [06:47] |
| Una línea **nunca es horizontal**. Si al ajustarla queda plana, pasa a leerse como nivel horizontal; si se le invierte la pendiente, se elimina. | Aislada [2] | OjZ8d [03:52], OjZ8d [04:22], PnIkS [08:29] |
| Un pivote vale cuando el precio llega, respeta la línea y se aleja con claridad. Un impulso de 1 o 2 velas sin retroceso no cuenta como toque. No da un umbral numérico. | Aislada [3] | OjZ8d [06:13], cTecm [11:00], xRxUo [03:19] |
| No se traza ni se mueve un ancla sobre una **vela abierta**: "We do not want to move a line or draw a line on an open candle" [06:00]. Se espera el cierre y un máximo o mínimo nuevo y claro. **[V15] verificado** | Aislada [1] | OjZ8d [06:03] |
| La línea se traza "a ojo", con grosor, sin exigir precisión al centavo. Implica una tolerancia de toque. | Aislada [1] | Kffx9 [14:40] |

**Contradicción resuelta (mecha o cuerpo).** En 6 videos se ven líneas que tocan cuerpos además
de mechas (rTHLR [01:54], rxleX [03:26], WUv5q [01:23], Y_Ney* [04:08], E_m8L [05:34]). En 27
la línea va por la mecha, y en qLtq7 [04:00] ella lo dice explícitamente. **Doctrina: mecha.** Los
toques de cuerpo se leen como la tolerancia de la regla anterior.

### 2.2 Calidad de la línea

| Regla | Fuerza | Evidencia |
|---|---|---|
| Con **3 toques o más** la línea es A+ (setup "3 Touchpoint Break"), y más toques le dan más peso. | Núcleo [22] | E6dUU [02:28], Kffx9 [03:44], qLtq7 [27:48], oq8nF [02:48], qsjLm [12:44], xRxUo [00:58], ZMIDT [04:32], cTecm [10:42] |
| Con **2 toques** la línea se puede operar, pero es un setup de menor calidad ("2 Touchpoint Break"). **[V4] [V5] [V6]** | Firme [9] | xRxUo [00:52], Y_Ney* [05:27], Rz92U* [04:03], SQeaH* [05:47], E_m8L [02:23], oq8nF [01:30], qsjLm [12:44] |
| La línea tiene que abarcar **al menos una semana de datos**. | Núcleo [14] | 5xiHa [02:01], H8B5u [02:27], cTecm [10:46], oq8nF [04:01], 17WoZ* [04:43], lR9pp* [07:31], yZfj6* [05:54] |
| Tres toques concentrados en una sola semana restan peso: los toques separados por semanas o meses "hold so much more weight". **[V14] verificado** | Aislada [1] | E6dUU [03:13] |
| Una línea cuyo segundo punto es **muy reciente**, sin un Punto B claro en el pasado, merece poca confianza: la califica "one out of four". **[V16] verificado** | Aislada [1] | xRxUo [05:28] |
| Una línea de **temporalidad mayor pesa más**, y su ruptura también. Una línea trazada solo en temporalidad baja, sin conexión con las mayores, es mala. | Núcleo [12] | ZMIDT [04:19], eJ0_E [06:18], gokPl [04:14], OjZ8d [01:28], ipUbs [00:48], Kffx9 [12:01] |
| Para la línea de decisión se prefieren **pendientes moderadas**: una línea muy empinada tiende a cruzarse sin que cambie la tendencia. La verificación mostró que xRxUo [05:38] **no habla de pendiente** sino de datos recientes (fila anterior), así que se quitó de la evidencia. La regla la sostiene Murphy (p. 103, §7). | Firme [4] | ZMIDT [07:05], xMNO4 [07:33], WUv5q [09:55], 17WoZ* [06:44] |

**Contradicción resuelta (2 toques o 3).**
- **Lo que choca:** Kffx9 [05:51] dice que no opera rupturas de 2 toques, mientras que 9 videos las
  aceptan como setup menor y qsjLm [12:44] llega a llamarlo "A-" de riesgo bajo.
- **Doctrina:** la línea de 3 toques o más con una semana de datos es la que se comunica como
  **línea principal**. La de 2 toques se dibuja y se usa como contexto, pero no se presenta como
  señal.
- **Verificado:** [V4] a [V6]. En V11 se ve además una operación real suya de +$24.276 en
  platino con el setup "2 Touchpoint Break" (Y_Ney [12:48]): el setup de 2 toques lo opera.

**Contradicción resuelta (líneas empinadas).** Las líneas empinadas no se contradicen con la
regla anterior porque cumplen **otro papel**. La línea de decisión, cuya ruptura da la entrada,
tiene que ser moderada. Las líneas empinadas aparecen después, como **líneas de seguimiento** para
arrastrar el stop (ver 2.3 y 2.7).

### 2.3 Ajuste y líneas nuevas

| Regla | Fuerza | Evidencia |
|---|---|---|
| **Encadenar:** el último toque (Punto B) de una línea es el primer punto (Punto A) de la siguiente. Vale también al bajar de temporalidad. | Firme [9] | ipUbs [05:14], qLtq7 [04:26], PnIkS [10:01], TuXOg [03:53], Y8efW [32:47], gokPl [06:11], yHAC0* [04:10] |
| Cuando el precio acelera y deja un retroceso claro, se traza una línea **más empinada** sin borrar la anterior (abanico). | Núcleo [15] | Y8efW [32:44], eJ0_E [12:00], ipUbs [07:23], qLtq7 [46:20], E6dUU [05:08], Kffx9 [14:31], 5xiHa [01:04], OjZ8d [09:54] |
| Las líneas principales y las de temporalidad mayor **no se borran**: quedan como estructura de referencia. | Núcleo [15] | Y8efW [32:21], ZMIDT [07:15], cTecm [21:00], eJ0_E [08:45], LpXZB [04:44], PnIkS [10:58], qLtq7 [04:30], pasWN [04:54] |
| Las líneas **secundarias** que el precio ya rompió se borran, y la siguiente se rota al nuevo extremo: "delete this downward trend line that's already been crossed... rotate this one to this new high" [14:43]. **[V13] verificado** | Firme [6] | eJ0_E [15:24], qsjLm [14:43], xMNO4 [07:33], xRxUo [07:55], rxleX [08:23], 17WoZ* [07:04] |
| Ante una penetración sin ruptura limpia, primero se mueve el Punto B al nuevo extremo cerrado, antes de trazar otra línea. | Aislada [3] | OjZ8d [02:22], PnIkS [26:55], xRxUo [10:06] |
| Al bajar de temporalidad, las anclas se reajustan al extremo exacto de la mecha que muestra el marco menor. | Firme [5] | ipUbs [06:44], qLtq7 [44:00], Y8efW [33:34], gokPl [09:22], PnIkS [12:34] |
| Tras romperse una línea alcista se traza una bajista nueva, desde el máximo absoluto hasta el siguiente máximo menor, para la tendencia nueva. | Aislada [3] | LpXZB [03:52], 17WoZ* [06:37], Y_Ney* [04:08] |

**Contradicción resuelta (borrar o conservar).** No son dos reglas opuestas, sino dos tipos de
línea: **se conserva la principal** (la de temporalidad mayor o la que sostiene la tendencia) y
**se borra la secundaria rota**.

### 2.4 Ruptura

| Regla | Fuerza | Evidencia |
|---|---|---|
| La ruptura se toma cuando el precio **cruza** la línea; esperar el **cierre** de la vela es una opción igual de válida. Verificado: [V1] [V2] [V3]. | Núcleo [20 + 8] | LpXZB [03:30], W_zXs [00:58], ZMIDT [04:34], eJ0_E [04:23], xRxUo [15:43], yZfj6* [07:35], Y_Ney* [05:07], q4t71* [16:16] |
| Una **mecha** que cruza la línea, o un toque o un asomo leve, **no es ruptura**. | Firme [6] | TuXOg [14:59], gokPl [16:18], pasWN [08:50], WUv5q [05:05], G29Lb* [03:32] |
| **El retesteo no es obligatorio:** se opera la ruptura directa. El "break and retest" y el cierre de la vela son dos herramientas de confirmación que se pueden usar por separado (G29Lb [02:35]-[03:05]). Lo que critica es entrar **sin ninguna** confirmación: "they'll enter without a break, they'll enter without a retest" (YROta [02:50]). Como el sistema publica con el cierre, ya cumple. **[V12] [V19] verificado** | Núcleo [12] | Y8efW [35:52], ZMIDT [04:37], cTecm [07:11], PnIkS [16:43], oq8nF [01:30], E6dUU [00:08], Kffx9 [04:07], qLtq7 [28:44] |
| La ruptura gana peso con **doble confirmación**: que a la vez se rompa un nivel horizontal, señal de que se sale de una consolidación. Es una herramienta para ganar confianza y evitar el "chop", **no un requisito** (qsjLm [02:14]). **[V17] verificado** | Firme [5] | qsjLm [02:00], eQzvi [04:39], 17WoZ* [06:05], G29Lb* [05:04], ZMIDT [05:13] |
| En crudo, los primeros intentos de salir de una consolidación suelen ser falsos y hay que pedir más confirmación. | Aislada [2] | eQzvi [13:54], PYBSQ* [04:27] |
| Las falsas rupturas vienen de operar contra la tendencia de las temporalidades mayores. | Aislada [1] | ipUbs [00:36] |

**Cruce o cierre: lo que mostró la verificación.**

El conteo de fichas inclinaba la balanza hacia el cierre de vela, por 20 videos contra 8. El video
dice otra cosa:
- **V1:** en qLtq7 [51:00] compra mientras la vela de 5 minutos todavía está perforando la línea.
- **V2:** en q4t71 [16:53] la ruptura es cuando el precio "crosses".
- **V3:** en cTecm [07:19] lo dice explícito: "You can do either one... waiting for the candle to
  close is an option", pero en mercados rápidos esperar el cierre de 1H puede hacerte perder el
  movimiento, y entra a mercado [07:55].

Las fichas de "cierre" estaban leyendo velas que, una vez terminado el movimiento, ya se veían
cerradas al otro lado.

**Doctrina para el sistema: la lectura declara la ruptura con el cierre de la vela del marco
operativo.** Es una de las dos formas que ella valida, así que no nos sale del método. Y es la única
que el sistema puede publicar: una pieza no puede afirmar que una línea se rompió con la vela
todavía abierta, porque la vela puede volver, y la regla de "sin mirar el futuro" del enchufe
exige trabajar con velas cerradas.

Lo que **no** podemos decir es que esa sea "la" regla de Tori. Ella entra al cruce. En el texto
de cliente, la ruptura se describe como "cerró al otro lado de la línea".

### 2.5 Entrada

| Regla | Fuerza | Evidencia |
|---|---|---|
| La entrada va **en la dirección de la ruptura**: si rompe una bajista, largo; si rompe una alcista, corto. | Núcleo [28] | E6dUU [05:32], Kffx9 [07:34], WUv5q [04:59], PnIkS [16:18], ZMIDT [05:27], cTecm [07:11], xMNO4 [08:17], 5xiHa [00:49] |
| La línea rota es la **línea de acción**; la opuesta, que queda sosteniendo la operación, es la **línea de seguridad**, y tiene que estar trazada al entrar. "An action line is the line that was broken" [11:35]; "The safety line is the opposite line... This line tells us how long to stay in our trade" [12:30]. **[V18] verificado** | Firme [9] | l0Ino* [03:10], qLtq7 [12:00], PnIkS [17:06], WoY_t* [07:17], Y8efW [36:01], 5xiHa [00:39], E_m8L [02:37] |
| La orden es **a mercado**. | Firme [9] | Y8efW [36:43], ZMIDT [10:41], cTecm [07:55], gokPl [15:24], oq8nF [01:30], qLtq7 [51:05], rxleX [05:30] |
| El setup es de **bajo riesgo** cuando, en la ruptura, el precio está **cerca de la línea de seguridad**; si está lejos, el riesgo es alto y se pasa. No da un umbral de distancia. | Núcleo [12] | 5xiHa [04:23], H8B5u [01:51], xRxUo [04:32], yZfj6* [06:13], lR9pp* [07:12], kBmtk* [08:21], cTecm [11:10], TuXOg [10:42], oq8nF [07:03] |
| **Setup secundario de rebote:** a favor de la tendencia, se entra cuando el precio toca la línea y la rechaza sin cerrar al otro lado. **[V7]** | Firme [7] | gokPl [13:06], TuXOg [10:42], q4t71* [21:12], qLtq7 [30:50], rTHLR [01:58], yHAC0* [08:02] |
| No se entra en corto justo después de una caída fuerte: hay que esperar un máximo más bajo y trazar desde ahí una línea más empinada. | Aislada [1] | oq8nF [07:08] |

**Contradicción resuelta (qué es la "action line").** En TuXOg [11:42] la línea de acción es
aquella donde el precio **rebota**; en PnIkS [16:37], WoY_t* [06:17] y qLtq7 [12:00] es la que se
**rompe**. Son dos setups distintos. **Doctrina:** la ruptura es el setup principal y el rebote,
el secundario.

### 2.6 Stop

| Regla | Fuerza | Evidencia |
|---|---|---|
| El stop va **al otro lado de la línea de seguridad**: debajo de la alcista en un largo y encima de la bajista en un corto. | Núcleo [30] | E6dUU [05:58], Kffx9 [07:39], WUv5q [06:23], PnIkS [17:15], pasWN [07:44], qLtq7 [16:17], qsjLm [11:38], ZMIDT [05:37], rxleX [05:39] |
| **No hay stop fijo** en puntos, en porcentaje ni en monto: el riesgo es dinámico y lo define la línea. | Núcleo [19] | E6dUU [05:54], Kffx9 [07:46], WUv5q [11:50], eQzvi [12:05], ZMIDT [15:28], cTecm [08:00], oq8nF [02:38], pasWN [01:05], H8B5u [03:06] |
| El stop va **con margen** detrás de la línea, nunca sobre ella, para que una mecha o un testeo normal no lo active. Ella **no da un tamaño**: dice que la posición tiene que ser lo bastante chica para permitirse ese margen (verificado, pasWN [14:33], [15:30]). El margen numérico que use el sistema es **un parámetro nuestro**, no de ella. | Aislada [2] | pasWN [14:48], qLtq7 [17:16] |
| **No se usan soportes o resistencias horizontales** para ubicar el stop. | Aislada [3] | pasWN [01:21], qsjLm [11:34], ZqC6W* [06:38] |
| Un stop sobre una línea demasiado empinada puede saltarlo una vela de noticias; en ese caso conviene la línea opuesta de temporalidad mayor. | Aislada [1] | E6dUU [09:43] |

**Contradicciones menores.** En ZMIDT [06:00] y 17WoZ* [07:11] el stop va detrás de un nivel
horizontal. Además, ella dice que cierra a mano (gokPl [15:24]) pero también que "siempre" tiene
un stop puesto (bWrOP [04:47], 1dQ0d [05:28]).

**Doctrina:** la ubicación técnica es la línea de seguridad. Si el stop queda cargado en el
broker o se cierra a mano es ejecución de cada operador y no entra en lo que comunicamos.

### 2.7 Gestión de la operación abierta

| Regla | Fuerza | Evidencia |
|---|---|---|
| El stop **se arrastra a lo largo de la línea de seguridad**: primero a break-even y después a ganancia. | Núcleo [17] | l0Ino* [02:10], pasWN [10:41], qLtq7 [53:15], qsjLm [11:43], zT2hS* [01:47], cTecm [14:17], eJ0_E [01:44], SQeaH* [11:07], eQzvi [12:15] |
| El stop se sube **solo cuando se confirma un nuevo mínimo** que respeta la línea, no vela a vela. | Aislada [2] | cTecm [12:48], TuXOg [14:35] |
| La operación se gestiona **en la misma temporalidad de la entrada**. No se baja a temporalidades menores a buscar motivos para salir. | Firme [5] | rTHLR [00:48], yHAC0* [06:31], zT2hS* [00:59], lg0pb [06:44] |
| Con la operación abierta **no se mueven las líneas** que la originaron. | Aislada [1] | OjZ8d [01:07] |
| Mientras el precio respete la línea, los retrocesos y el drawdown no son motivo para salir. | Firme [6] | 5xiHa [00:53], H8B5u [03:39], TuXOg [14:49], gokPl [17:26], oq8nF [02:38], qLtq7 [53:38] |

### 2.8 Salida

| Regla | Fuerza | Evidencia |
|---|---|---|
| Se sale **cuando una vela cierra al otro lado de la línea de seguridad** (o de la línea de seguimiento más empinada), también en ganancia. | Núcleo [30] | LpXZB [04:45], PnIkS [17:34], W_zXs [01:46], oq8nF [02:46], qLtq7 [09:43], E6dUU [15:24], WUv5q [11:45], ZMIDT [09:02], yHAC0* [10:34] |
| **No hay take profit fijo** ni ratio R:R predefinido: se deja correr mientras la línea se respete. | Núcleo [19] | HiEDX [02:53], PnIkS [17:24], W_zXs [01:11], qLtq7 [51:58], qsjLm [10:08], eJ0_E [17:28], rxleX [13:00] |
| **Alternativa válida:** cerrar en un **soporte o resistencia horizontal mayor** donde el precio giró antes. Es la salida para quien no quiere sostener semanas o para asegurar ganancia. **[V11]** | Núcleo [16] | qsjLm [10:30], cTecm [16:07], E6dUU [12:24], Kffx9 [15:15], kBmtk* [07:37], 5xiHa [01:18], H8B5u [04:21] |
| Se cierra la **posición completa** de una vez, sin parciales. | Firme [5] | cTecm [18:41], eJ0_E [14:45], gokPl [17:38], H8B5u [04:37], E6dUU [13:53] |
| Una línea de tendencia de temporalidad mayor también sirve de objetivo. | Aislada [2] | l0Ino* [00:50], yZfj6* [11:29] |

**Contradicción resuelta (línea de seguridad o nivel horizontal).** La verificación V11 (Y_Ney
[12:49]-[13:33]) la deja clara: en la práctica, "most of my exits, if not all, were based on a
level of support and resistance", y lo atribuye a la presión psicológica de los montos grandes.
Pero la salida que ella considera la del método es la otra: "my strategic sells when I can hold
the trade out for its entirety, wait for the safety line to get crossed". En 5xiHa [02:46]
reconoce que cerrar en el horizontal le dejó ganancia sobre la mesa. **Doctrina:** la salida es la línea de seguridad, y el
horizontal mayor se comunica como **objetivo probable** del movimiento. En las piezas esto encaja
con los escenarios: el horizontal es el 🎯 y la línea de seguridad, el ⚠️.

### 2.9 Temporalidades

| Regla | Fuerza | Evidencia |
|---|---|---|
| El swing **se analiza y se opera en 4H**. | Núcleo [29] | E6dUU, Kffx9, WUv5q, eQzvi, g_SG1 (lote 6, 11 videos), rTHLR [00:48], xMNO4, HiEDX, LpXZB, W_zXs, ZMIDT, ipUbs [02:53], oq8nF |
| El análisis va **de arriba hacia abajo**: mensual (con todo el historial), semanal, diario, 4H y luego la temporalidad de entrada. | Núcleo [12] | Y8efW, YROta*, eJ0_E, gokPl, ipUbs, qLtq7, q4t71*, oq8nF, qsjLm, PnIkS [03:33], TuXOg [02:33], yHAC0*, zT2hS* |
| Cada línea de temporalidad menor **tiene que conectar** con las de las temporalidades mayores. | Aislada [2] | YROta* [02:38], gokPl [03:45] |
| En **alta volatilidad** se baja de 4H a 1H para entrar y salir, y se vuelve a 4H cuando el mercado se normaliza. | Firme [5] | ZqC6W* [04:47], eJ0_E, cTecm [03:29], gokPl [12:18], rTHLR [01:58] |
| Duración: en diario, semanas; en 4H, de una a dos semanas; en 1H, entre 8 y 10 horas. | Firme [9] | 1dQ0d, E_m8L, H8B5u, HiEDX, LpXZB, rxleX, xMNO4, oq8nF, qsjLm |
| Para el **swing**, 1 y 5 minutos se descartan por ruido. En **day trading** sí opera 5 minutos, incluso con líneas de 2 toques (verificado en [V8]: xRxUo [00:47]). | Aislada [3] | rTHLR [01:03], xMNO4 [11:08], q4t71* [17:23] |
| **Nunca baja de temporalidad para entrar antes:** "I do not ever go to a lower timeframe to look for a sooner entry"; entrada, salida y gestión van en 4H. **[V20] verificado** | Aislada [1] | q4t71 [17:47], [18:01] |

**Contradicción resuelta (5 minutos).** La verificación lo aclaró:
- **xRxUo [00:47]:** es day trading real, en su evaluación de Apex.
- **qLtq7 [51:00]:** es una demostración en replay.

El método es el mismo en cualquier marco, y el marco lo define el estilo. **Doctrina:** como el
grupo hace swing, el marco operativo es 4H, la excepción por volatilidad es 1H, y no se baja de
ahí.

**V20 matiza la excepción de 1H.** Ella nunca baja de temporalidad para **adelantar** una
entrada. La bajada a 1H de la fila de alta volatilidad es otra cosa: cambia el marco operativo
completo mientras dura el régimen. No es buscar una entrada más fina. El spec del enchufe deja esa
bajada fuera de la v1 porque ella no da un umbral de volatilidad.

### 2.10 Soportes y resistencias horizontales

| Regla | Fuerza | Evidencia |
|---|---|---|
| Son **confluencia, no el núcleo**. No generan entradas: sirven de objetivo de salida, de doble confirmación y para delimitar un rango. | Núcleo [15] | lg0pb [07:27], oq8nF [01:39], qLtq7 [13:25], qsjLm [00:28], cTecm [16:07], eJ0_E [13:54], E6dUU [13:14], Rz92U* [03:41], rxleX [07:42] |
| Se marcan en máximos y mínimos **obvios** donde el precio reaccionó varias veces, eligiendo el nivel que **más toques** junta. | Firme [7] | Kffx9 [15:15], kBmtk* [15:55], tU2dL* [11:29], cTecm [16:25], eJ0_E [14:14], qsjLm [04:07] |
| Se marcan **solo los cercanos** al precio, sin saturar el gráfico. Quien opera en 1H los marca más cerca que en 4H. | Aislada [1] | qsjLm [03:27], qsjLm [07:52] |
| Cuando el mercado consolida y no se pueden trazar líneas limpias, se marcan horizontales en el **máximo y el mínimo del rango** y se espera a que lo rompa. | Aislada [2] | xMNO4 [08:52], Y8efW [20:30] |
| Se tratan como **zona**, con una línea gruesa. No da un ancho en precio. | Aislada [1] | qsjLm [08:52] |

### 2.11 Cuándo no se opera

| Regla | Fuerza | Evidencia |
|---|---|---|
| **En consolidación o rango lateral no se opera.** Se espera a que el precio rompa los extremos. No da una definición numérica de tendencia. | Núcleo [18] | 17WoZ* [04:08], E6dUU [02:52], SQeaH* [06:16], 5xiHa [05:13], ipUbs [08:06], qsjLm [01:17], Y8efW [13:28], cTecm [01:34], xMNO4 [08:29] |
| Si el precio **oscila entre las dos líneas sin romper ninguna**, no se entra. | Aislada [2] | qLtq7 [41:13], xMNO4 [08:05] |
| No se opera **contra la secuencia** de las temporalidades mayores. | Aislada [1] | ipUbs [01:11] |
| No se opera un setup que no cumpla al 100 % los criterios. La frecuencia baja (1 a 3 operaciones al mes) es parte del método. | Firme [6] | g_SG1 [26:47], g_SG1 [27:18], OuwJO* [19:08], lg0pb [02:14], YROta* [01:03] |
| Si con el tamaño mínimo el stop detrás de la línea igual excede el riesgo permitido, se deja pasar la operación. | Aislada [2] | cTecm [08:47], pasWN [08:18] |

---

## 3. Lo que no se adopta

- **El tamaño de posición y el riesgo por operación.** Varía entre 1 % y 15 % según el video y el
  momento de su carrera, sus contratos estándar no coinciden entre videos, y no es algo que el
  grupo comunique. Para eso rige el manual de operaciones del repo.
- **Los instrumentos.** Ella opera futuros (platino, crudo, oro, Nasdaq), y el método dice
  aplicarse a cualquier activo. Nos quedamos con el principio y operamos nuestro catálogo.
- **La mentalidad y el diario** (47 reglas). Es buen material para el contenido educativo, pero
  no es una regla de análisis.
- **Las alertas de TradingView y los vencimientos de futuros.** Son la mecánica de su plataforma.
- **Las cifras de sus operaciones.** Hay operaciones que se cuentan con fechas y montos distintos
  en distintos videos: el platino de +$49.961 aparece con fecha de 2024 y de 2025, y el PLN24 con
  dos riesgos y dos salidas. Sirven como ilustración, nunca como estadística.

---

## 4. Frente a lo que ya hacemos

Hoy el sistema tiene dos motores que no se hablan:
- **Los niveles del texto** (`_get_support_resistance` en `src/market_data_mcp/analisis.py`), que
  son horizontales.
- **La estructura del gráfico** (`calcular_estructura` en `scripts/tradingview_grafico.py`), que
  traza canales, pero solo se dibuja.

| Hoy | Dónde | Veredicto | Por qué |
|---|---|---|---|
| Soportes y resistencias horizontales de pivotes fractales (±5 velas), agrupados al 0,15 %, con respaldo por ATR | `analisis._get_support_resistance` | **Se queda, con otro papel** | Ella los usa como objetivo, doble confirmación y borde del rango. Dejan de ser el eje del mensaje, y el respaldo por ATR ya se declara aparte (`niveles_origen`). |
| Canal por **regresión de cierres**, bordes en percentil 97/3, rectas paralelas | `tradingview_grafico._canal` | **Cambia** | Ella ancla en las mechas de los pivotes, la línea no puede cortar velas y las dos líneas no son paralelas: son la línea de acción y la de seguridad, cada una con su pendiente. |
| La serie se parte en el **extremo absoluto** de la ventana | `calcular_estructura` | **Se queda** | Coincide con su regla: el primer punto es el máximo más alto o el mínimo más bajo visible. |
| Pivotes por **zigzag de 3 × ATR** | `tradingview_grafico._zigzag` | **Se queda como candidato** | Da los pivotes candidatos al segundo punto. Falta la prueba de no intersección y la cuenta de toques. |
| Canal válido desde **24 velas** | `_canal` | **Cambia** | Su mínimo es **una semana de datos** entre toques, que en 4H son unas 30 velas y en 1H unas 120. |
| Proyección de 14 velas a la derecha | `calcular_estructura` | **Se queda** | Es su semirrecta. |
| Ventana de 60 velas de H1 en el gráfico de la pieza | `generar_grafico_tv` | **Cambia** | La línea necesita una semana de datos y contexto de temporalidad mayor. |
| **Dirección = precio contra la EMA 50** | `screener_gi.direccion_tecnica` | **En conflicto: decide el director** | Ella no usa indicadores. Su dirección es qué línea está vigente y cuál se rompió. |
| Rango: "si rompe un borde y vuelve a entrar, es falso quiebre y el objetivo es el borde contrario" | cierre canónico de las piezas | **En conflicto: decide el director** | Ella no opera dentro de la consolidación: espera la ruptura del rango. |
| Salida **Chandelier (22; 3,0)** sin objetivo fijo | `scripts/analista/plan.py` y la doctrina de salida del 2026-09-07 | **En conflicto: decide el director** | Coinciden en no tener objetivo fijo ni parciales, pero ella arrastra el stop por la línea de seguridad y no por ATR. |
| Gates del escáner (feriado, blackout, agotamiento, banda) | `screener_gi` | **Se queda** | Son filtros de cuándo publicar y no chocan con el método. |

**Lo que se agrega:**
- **La línea de acción y la de seguridad** como pareja, que reemplaza al canal paralelo.
- **La calidad de la línea:** toques, semanas de datos y temporalidad. Decide qué línea se
  comunica.
- **La ruptura por cierre de vela** y su lectura direccional.
- **"Precio cerca de la línea de seguridad"** como criterio de bajo riesgo.
- **El filtro de consolidación:** dentro del rango no hay señal de línea.

### Reglas programables (entrada del spec del subproyecto 2)

1. **Pivotes:** los candidatos del zigzag, cada uno con su extremo de mecha.
2. **Primer punto:** el máximo más alto o el mínimo más bajo de la ventana.
3. **Segundo punto:** el pivote posterior que maximiza los toques sin que ninguna vela cruce la
   línea, con una tolerancia de toque a definir (por ejemplo, una fracción del ATR).
4. **Calidad:** número de toques, semanas de datos entre el primer y el último toque, y
   temporalidad. Es **A+** con 3 toques o más y al menos una semana; con 2 toques, **B**. Una línea
   cuyo segundo punto es muy reciente baja de calidad (V16), con un umbral a calibrar. Las anclas
   solo se ponen en velas cerradas (V15), que es la regla de "sin mirar el futuro" del enchufe.
5. **Pendiente:** la línea no puede ser horizontal y se marca la que sea "muy empinada", con un
   umbral a calibrar.
6. **Ruptura:** el cierre de la vela al otro lado de la línea. La mecha no cuenta.
7. **Línea de seguridad:** la línea opuesta vigente que no se ha roto.
8. **Distancia a la línea de seguridad** en ATR, que mide el riesgo del setup.
9. **Encadenamiento:** el último toque de una línea es el primer punto de la siguiente.
10. **Abanico:** una línea más empinada después de un retroceso confirmado.
11. **Consolidación:** el precio oscila entre las dos líneas, o entre los horizontales, sin romper
    ninguno.
12. **Top-down:** las líneas de diario y 4H dan contexto a la de 1H.

---

## 5. Preguntas para el director

1. **Dirección de la pieza.** ¿La dirección deja de salir de la EMA 50 y pasa a salir de la
   estructura de líneas (qué línea se rompió y cuál sostiene)? Ella no usa indicadores, y que
   convivan las dos lecturas permite que el chip diga una cosa y la línea otra.
2. **Rango.** El cierre canónico enseña a operar el falso quiebre dentro del rango (decisión del
   2026-09-28). En su método, dentro de la consolidación no se opera y se espera la ruptura. ¿Se
   mantiene el falso quiebre o se cambia?
3. **Salida.** ¿La pieza semanal y el plan del analista pasan del Chandelier a la línea de
   seguridad, que es lo que el cliente va a ver dibujado? ¿O el Chandelier se queda como regla
   numérica y la línea como lectura visual?
4. **Temporalidad.** Su swing es en 4H. El carrusel publica H1. ¿La línea principal se traza en
   4H y la pieza la muestra en H1, se pasa la pieza a 4H, o H1 se queda como "alta volatilidad"?
5. **Líneas de 2 toques.** La propuesta es dibujarlas, pero comunicar como línea principal solo la
   A+ (3 toques o más y una semana de datos). ¿De acuerdo?

## 6. Verificación

El resultado está en `docs/investigacion/tori-trades/verificacion.md`.

**Sesión 1, V1 a V10, hecha el 2026-10-09.**
- **Cambió la doctrina:** la ruptura (V1 a V3) es cruce o cierre, según 2.4.
- **Matizó:**
  - Los 5 minutos son de day trading (V8).
  - El margen del stop no tiene número (V9).
- **Confirmó:**
  - Las líneas de 2 toques son un setup menor (V4 a V6).
  - El rebote es un setup aparte (V7).
  - La no intersección (V10).

**Sesión 2, V11 a V20, hecha el 2026-10-09.**
- **Cambió la doctrina:**
  - El retesteo es una confirmación opcional, como el cierre. Lo que ella critica es entrar sin
    ninguna confirmación (V12, V19).
  - xRxUo [05:38] no respaldaba la regla de las líneas empinadas, sino una regla nueva: el Punto B
    muy reciente da poca confianza (V16).
- **Matizó:**
  - En la práctica, ella sale casi siempre en horizontales. La salida del método es la línea de
    seguridad (V11).
  - No baja de temporalidad para adelantar una entrada (V20).
- **Confirmó:**
  - Borrar la secundaria rota y rotar la siguiente (V13).
  - Los toques repartidos en semanas pesan más (V14).
  - No anclar sobre una vela abierta (V15).
  - La doble confirmación es opcional (V17).
  - Las definiciones de acción y seguridad (V18).

---

## 7. Fundamentos citables

Cada regla del método va con su **pilar canónico** (la teoría clásica que la formula) y su
**pilar empírico** (la evidencia medida). Cuando no hay evidencia, se dice. Es la disciplina de
admisión del proyecto Genesis aplicada a nuestra doctrina, y es lo que permite escribir en una
pieza "según la Teoría de Dow..." sin inventar nada.

Fuentes, con su estado de verificación y sus citas literales:
`docs/investigacion/fundamentos/fuentes.md`. Las páginas de Murphy son de la edición en español
(*Análisis técnico de los mercados financieros*, Gestión 2000, 2000). La Teoría de Dow se cita a
través de Murphy, cap. 2.

| Regla (§1) | Pilar canónico | Pilar empírico | Lo que no está probado |
|---|---|---|---|
| 1. Precio y líneas, sin indicadores | Premisa del análisis técnico: "Los precios se mueven por tendencias" (Murphy p. 28). | Lo, Mamaysky y Wang (2000): los patrones gráficos "may have some practical value". | Que las líneas diagonales en sí predigan algo (ver abajo). |
| 2. Ancla en la mecha, sin cruzar velas | Trazar "por encima o por debajo del alcance de los precios de todo el día" (Murphy p. 96). Las líneas internas son "muy subjetivas" (p. 117). | No hay. | Es una convención de trazado. |
| 3. 3 toques = A+; 2 = setup menor | "se necesitan dos puntos para trazar la línea de tendencia y un tercero para transformarla en una línea de tendencia válida" (Murphy p. 94). La importancia la dan "el tiempo que se ha mantenido intacta y el número de veces que se ha puesto a prueba" (p. 94). | No hay para diagonales. | Que una A+ rinda más que una de 2 toques. |
| 4. Encadenar y abanico | Las líneas "se deben ajustar para que se acomoden a una tendencia que se enlentece o se acelera" (Murphy p. 104). | No hay. | Ojo con el nombre: el "principio abanico" de Murphy (p. 101) son líneas cada vez **más planas**, y la rotura de la tercera anuncia el **giro**. El abanico de Tori son líneas **más empinadas** cuando el precio acelera. En Murphy, eso es el ajuste de la p. 104. |
| 5. Top-down, 4H operativo | Dow: tres tendencias, primaria de más de un año, secundaria de 3 semanas a 3 meses, menor de menos de 3 semanas (Murphy pp. 51-52). Líneas distintas para grados distintos (pp. 105-106). | Momentum de series de tiempo a 12 meses (Moskowitz, Ooi y Pedersen 2012; Hurst, Ooi y Pedersen 2017). | Que 4H sea el marco óptimo. La evidencia es de horizonte mensual, no intradía. |
| 6. La ruptura se publica con el cierre | "Dow no consideraba válidas las penetraciones intradía" (Murphy p. 56). "un cierre más allá de la línea de tendencia es más significativo que una simple penetración intradía" (p. 97). | Brock, Lakonishok y LeBaron (1992): la ruptura de rango **horizontal** tiene poder predictivo, aunque las ganancias quizás no cubran los costos (según Osler 2000, p. 54). | La ruptura de una diagonal. Costo conocido de esperar: Dow "pierde de un 20 al 25 por ciento de un movimiento antes de generar una señal" (p. 57). |
| 7. Entrar a favor de la ruptura | "Se presume que una tendencia está en vigor hasta que da señales definitivas de que ha retrocedido" (Murphy p. 54). "una tendencia en movimiento es más probable que continúe que retroceda" (p. 29). | Hurst, Ooi y Pedersen (2017): el seguimiento de tendencia fue rentable en una muestra de 1880 a 2016. | Que la ruptura de **una línea** sea el mejor disparador. |
| 8. Stop tras la línea de seguridad | La línea "proporciona un límite de apoyo por debajo del mercado" (Murphy p. 94). | No hay. | El margen del stop. Es parámetro nuestro (§2.6). |
| 9. Salida al cerrar al otro lado | "la violación de la línea de tendencia indica un cambio en la tendencia que aconseja la liquidación de todas las posiciones" (Murphy p. 94). | No hay específica. | Que salir por la línea rinda más que salir en el horizontal. Es lo que V11 deja abierto. |
| 10. No operar en consolidación | "cuando el mercado se mueve lateralmente, la tercera opción —mantenerse fuera del mercado— es generalmente la más sensata" (Murphy p. 78). Los precios están en lateral "una tercera parte del tiempo" (pp. 76-77). Las "líneas" de Dow son consolidaciones (p. 57). | **AQR:** las peores rachas del seguimiento de tendencia "tend to be associated with periods of sharp reversals across multiple markets or prolonged periods in which many markets exhibit a lack of clear trends" (Hurst, Ooi y Pedersen 2017). | Una definición numérica de consolidación. Ni Tori ni Murphy la dan. |
| Horizontales (§2.10) | Inversión de roles: "un nivel de resistencia se transforma en un nivel de apoyo" tras una penetración "significativa" (Murphy p. 85). La fuerza la dan el tiempo, el volumen y lo **reciente** (p. 86). | **Osler (2000):** los soportes y resistencias publicados predicen dónde se **interrumpe** la tendencia intradía en divisas, y su efecto dura al menos cinco días hábiles. | Osler no examina si el precio sigue al romper el nivel. Respalda el horizontal como **objetivo** (🎯), que es justamente su papel en la doctrina. |

**Lo que hay que decir siempre: la parte diagonal no tiene evidencia académica propia.** No se
encontró ningún estudio que pruebe rupturas de líneas de tendencia diagonales. Ver la fila F11 de
`fuentes.md`. El método se apoya en dos cosas: la tradición (Dow y Murphy) y la evidencia general
del seguimiento de tendencia (AQR) y de los niveles horizontales (Osler). No habrá backtesting
(decisión del director, 2026-10-10), así que la parte diagonal queda sin medir. Por eso:
- **En las piezas de cliente:** se puede enseñar con la fuente ("según la Teoría de Dow, una
  tendencia alcista son picos y valles cada vez más altos"). Nunca se dice que el método "está
  probado" ni se da una tasa de acierto.
- **Una diferencia de vocabulario:** la edición en español de Murphy dice "apoyo". En las piezas
  se dice "soporte" (regla de terminología del proyecto). En las citas textuales se respeta el
  libro.
