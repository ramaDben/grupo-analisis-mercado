## 01. El problema que resuelve

Hoy la decisión de qué activo comunicarle al grupo se toma a criterio, activo por activo y día
por día. Funciona, pero tiene tres costos que se acumulan:

- **Cobertura desigual.** La rotación diaria cubre cuatro activos base. El terminal ofrece 148
  instrumentos y el catálogo técnico ya cubre 38, así que la mayor parte del universo no se
  mira nunca.
- **No queda registro de por qué.** Si un cliente pregunta por qué se habló del Oro y no del
  Nasdaq, la respuesta es una opinión. No hay número que la respalde.
- **El volumen depende de las horas de un analista.** Escalar la operación significa contratar,
  no configurar.

La propuesta es un sistema que **escanea el universo completo, puntúa cada activo con una
fórmula auditable y produce las piezas del día**, dejando el criterio editorial y la aprobación
donde corresponde: en el analista.

## 02. Qué produce, y cuándo

Cuatro entregas diarias, ancladas a la sesión de Nueva York y no al reloj local:

| Hora (Nueva York) | Entrega | Formato |
|---|---|---|
| Antes de la apertura | Marco de apertura | PDF institucional A4 + mensaje |
| 10:30 (apertura + 1 h) | Tanda 1 | Hasta 3 imágenes + mensaje índice |
| 14:30 | Tanda 2 | Hasta 3 imágenes + mensaje índice |
| 16:45 (cierre + 45 min) | Cierre de la sesión | Mensaje con gráfico |

**Por qué el ancla es Nueva York.** Chile y Estados Unidos cambian de horario en sentido
opuesto, así que el desfase se mueve dos veces al año: la bolsa de Nueva York abre a las 09:30
de Chile en agosto y a las 11:30 en diciembre. Un cronograma escrito en hora chilena describiría
en enero un mercado que ya cerró.

**Por qué un solo PDF al día.** El criterio de canal de la operación reserva el documento
descargable para los hitos de alta densidad: dos PDF diarios generan fatiga de descargas y el
cliente deja de abrirlos. El cierre va como mensaje con gráfico adjunto.

**Por qué tres imágenes y no cinco.** WhatsApp muestra tres adjuntos con previsualización; del
cuarto en adelante los agrupa detrás de un botón. Una cuarta pieza no se ve.

## 03. Cómo elige los activos

Cada activo del catálogo recibe un puntaje sobre 100, compuesto por cuatro factores medidos
contra el terminal:

| Factor | Máximo | Qué mide |
|---|---|---|
| Técnico | 35 pts | Quiebre de la media de 20 horas con estructura detrás, rebote en media diaria, o quiebre de nivel horizontal |
| Catalizador macro | 25 pts | Si el activo recibe un dato de **alto** impacto del día, o si la tasa del Tesoro a 10 años se movió 3 puntos base o más |
| Espacio disponible | 20 pts | Distancia al objetivo medida en volatilidad horaria, validada contra el recorrido que le queda al día |
| Momentum | 20 pts | Fuerza de tendencia (ADX) con el oscilador en zona de expansión |

Los cuatro se suman. La escala es real: un activo que dispara los cuatro máximos da exactamente
100, y el desglose queda guardado junto a la pieza que produjo.

## 04. Los controles, que es lo que hace confiable al sistema

Un escáner que solo puntúa produce piezas técnicamente correctas y operativamente irresponsables.
Antes de puntuar, cuatro filtros **excluyen** al activo, y ninguno se puede compensar con
puntaje:

1. **Feriado de bolsa.** Si el mercado del activo no opera ese día, queda fuera.
2. **Ventana de bloqueo por dato macro.** Alrededor de los datos de alto impacto los spreads se
   abren y el precio no es representativo. Las ventanas están definidas por evento: 30 minutos
   antes y 75 después de una decisión de la Reserva Federal, 15 y 30 alrededor del dato de empleo
   o de inflación de Estados Unidos, y las propias del Banco Central de Chile.
3. **Prohibición del modelo cuantitativo.** El marco de régimen macro define, para cada estado
   del mercado, qué operaciones no se abren. Una venta agresiva de Oro prohibida por régimen no
   se comunica **aunque puntúe alto**.
4. **Agotamiento del recorrido diario.** Si el activo ya consumió más del 90 por ciento de su
   rango típico del día, no tiene espacio para el movimiento que la pieza anunciaría.

A esto se suman dos reglas de honestidad del dato:

- **El informe de apertura no se emite con datos vencidos.** Si el modelo cuantitativo no se
  refrescó, el sistema se detiene y pide refrescarlo. Se puede forzar, y en ese caso el documento
  lleva el aviso impreso en la primera página.
- **Una cifra que no se puede calcular se informa como ausente, nunca como cero.** Cero significa
  "no se movió", que es una afirmación distinta de "no lo sé".

## 05. Evidencia: la corrida real de esta tarde

El sistema corrió hoy, 25 de agosto, a las 17:40 de Chile, sobre los activos con material visual
disponible. Los números son del terminal, no de un ejemplo:

| Activo | Puntaje | Resultado |
|---|---|---|
| Nasdaq 100 | 80 / 100 | Seleccionado |
| ETF de oro | 80 / 100 | Seleccionado |
| Plata | 70 / 100 | Seleccionado |
| Oro | 70 / 100 | Elegible |
| ETF de semiconductores | 45 / 100 | Elegible |
| Dólar / peso chileno | Excluido | Recorrido diario consumido al 96 por ciento |
| Bitcoin | Excluido | Recorrido diario consumido al 105 por ciento |
| MercadoLibre | Excluido | Recorrido diario consumido al 97 por ciento |
| Petróleo WTI | Excluido | Recorrido diario consumido al 179 por ciento |

**Las cuatro exclusiones son el dato más importante de esta tabla.** A las 17:40 el dólar había
movido 6,53 pesos con un promedio de 6,77 para catorce días, y el petróleo casi había duplicado
su rango habitual. Un sistema que solo puntuara habría publicado los cuatro. Este dice que no
hay espacio, y explica por qué.

También muestra el límite de horario: las piezas de la tarde salen sobre lo que quedó vivo. El
momento natural de una tanda es la mañana, con el recorrido del día por delante.

## 06. Qué falta para operar en régimen

Tres cosas, en orden de importancia:

1. **Material visual para el resto del universo.** Cada activo aporta su imagen y su color a la
   pieza. Hay nueve archivos en uso y once especificados y pendientes de producir. Mientras
   falten, el escáner se limita a los activos que sí pueden rendir una pieza completa, y así el
   universo se amplía a medida que el material llega.
2. **Automatización del disparo.** Hoy las cuatro entregas se invocan a mano, que es lo correcto
   mientras se calibra: el analista ve cada pieza antes de que exista. Programarlas es un paso
   breve una vez que la salida sea confiable, y el envío al grupo seguirá pasando por aprobación.
3. **Fichas del modelo cuantitativo para más activos.** Hoy cinco activos tienen régimen, sesgo
   y matriz de operaciones permitidas. El resto del catálogo tiene niveles e indicadores, pero no
   marco de régimen, y no se le improvisa: cada ficha cita literatura y elasticidades medidas.

## 07. Sobre los adjuntos

Las siete imágenes cubren una clase de activo cada una, para mostrar el alcance del sistema. Tres
salen de la corrida real de esta tarde con sus niveles del terminal; la de agenda macro
corresponde a la séptima clase, que no tiene activo protagonista porque lo que comunica es la
curva de tasas y el calendario.

## 08. Fuentes de los datos

- Precios, niveles e indicadores técnicos: terminal MetaTrader 5, cuenta Grupo Inteligencia SpA.
- Curva soberana de Estados Unidos y tasa real: Reserva Federal (FRED).
- Calendario económico y consensos: Investing.com.
- Marco de régimen macro y matriz de operaciones: modelo cuantitativo propio.
