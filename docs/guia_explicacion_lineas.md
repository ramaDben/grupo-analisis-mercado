# Guía Visual y Práctica: Cómo se Traza e Interpreta Cada Línea del Gráfico

Esta guía está diseñada para **explicar de forma simple, visual y didáctica a cualquier persona** (analista, cliente o trader) cómo se construye cada línea y zona en los gráficos de TradingView despachados a WhatsApp y en el indicador de MetaTrader 5 (`GI_Canales_Seguridad`).

---

## 1. La Filosofía Base: ¿Por qué trazamos así?

1. **No usamos medias móviles ni osciladores retrasados**: Las líneas nacen directamente de la **geometría del precio** y de la volatilidad real del mercado (**ATR de 14 periodos**).
2. **Las líneas son semirrectas proyectadas**: Parten de un extremo en el pasado y se extienden hacia el futuro donde el precio aún no ha llegado.
3. **Se anclan siempre en las mechas**: El extremo de la mecha representa el punto de máxima liquidez y rechazo del mercado.
4. **Regla de oro (No-Intersección)**: Una directriz válida **no puede cortar velas por el medio** entre el inicio y el precio actual. Si corta velas, la línea está mal trazada y se descarta.

---

## 2. Mapa de Colores y Roles de Cada Línea

| Línea / Zona                       | Color en Gráfico                       | Rol Principal                         | ¿Cómo se explica a alguien?                                                                                        |
| :--------------------------------- | :------------------------------------- | :------------------------------------ | :----------------------------------------------------------------------------------------------------------------- |
| **Línea de Seguridad**             | 🟢 **Verde Esmeralda** (`#26C6A0`)     | Soporte o Resistencia Dinámica (Stop) | *"Es el piso o techo que sostiene la tendencia actual. Mientras no cierre al otro lado, la operación sigue viva."* |
| **Línea de Acción**                | 🔴 **Rojo Coral** (`#FF4D5E`)          | Gatillo de Ruptura o Prueba           | *"Es la barrera contraria. Cuando el precio la perfora y cierra afuera, se activa la entrada a mercado."*          |
| **Línea de Seguimiento**           | 🟢 **Verde Menta** (`#9BE7C4`)         | Abanico Acelerado (Trailing)          | *"Cuando el precio toma velocidad, trazamos una línea más empinada para proteger ganancias más cerca."*            |
| **Zonas de Soporte y Resistencia** | 🟡 **Amarillo Ámbar** (`#FFD54F`)      | Barreras Estructurales Horizontales   | *"Franjas donde rebotó el precio en el pasado (mínimo 2 veces). Representan objetivos o zonas de llegada."*        |
| **Líneas de Contexto**             | 🟣 **Lavanda Discontinua** (`#B39DDB`) | Tendencia Mayor (D1 / W1)             | *"La dirección de fondo de los gráficos diarios o semanales. Evita que operemos contra la corriente mayor."*       |
| **Bordes de Rango**                | ⚪ **Gris Pizarra** (`#CBD5E1`)         | Techo y Piso Lateral                  | *"Cuando el mercado no tiene tendencia diagonal, delimita el canal horizontal entre el máximo y mínimo semanal."*  |

---

## 3. Explicación Detallada Línea por Línea

### 🟢 1. Línea de Seguridad (Verde Esmeralda `#26C6A0`)
* **Qué es:** Es la directriz más importante del sistema. En una compra es la directriz alcista que pasa por los mínimos; en una venta es la directriz bajista que pasa por los máximos.
* **Cómo se traza paso a paso:**
  1. **Punto A (Origen):** Busca el mínimo más bajo visible (para tendencia alcista) o el máximo más alto (para bajista) que esté confirmado. Ancla la semirrecta en la punta de la mecha.
  2. **Punto B (Segundo toque):** Busca un segundo pivote posterior del mismo tipo. Traza la recta de tal forma que conecte con el Punto B **sin atravesar ninguna vela intermedia**.
  3. **Conteo de toques:** Cada vez que el precio baja a tocar la línea (tolerancia de contacto) y luego rebota con fuerza, suma un toque.
     - **Línea A+ (Alta calidad):** 3 toques o más y al menos 1 semana de datos.
     - **Línea B (Estándar):** 2 toques.
* **Función Operativa:** 
  - Fija el **Stop Loss dinámico**: el stop no se pone a un número fijo de pips, sino unos puntos detrás de esta línea verde.
  - Si una vela completa cierra al otro lado de la línea verde, **la posición se cierra de inmediato** (salida técnica por invalidación).

---

### 🔴 2. Línea de Acción (Rojo Coral `#FF4D5E`)
* **Qué es:** Es la directriz que el precio acaba de romper o que está testeando.
* **Cómo se explica:**
  - Si veníamos cayendo y el precio rompe hacia arriba la directriz bajista, esa directriz rota pasa a llamarse **Línea de Acción**.
  - Marca la ruptura que da el **gatillo de entrada** a favor del nuevo movimiento.
  - Visualmente en el gráfico aparece sólida si está en prueba activa, o con trazo discontinuo/rojo una vez que fue superada, para recordar de dónde nació la oportunidad.

---

### 🟢 3. Línea de Seguimiento (Verde Menta `#9BE7C4`)
* **Qué es:** Es una línea de abanico acelerada.
* **Cuándo y cómo se dibuja:**
  - Cuando el precio despega con fuerza a favor de la operación, la Línea de Seguridad original queda muy lejos.
  - Para no regalar ganancias acumuladas en un retroceso profundo, se ancla una nueva semirrecta en el **último toque confirmado de la línea de control** y se une con el siguiente mínimo más alto.
  - Esta línea tiene una **pendiente más empinada**. Si el precio rompe esta línea rápida, el trader puede asegurar ganancias anticipadamente (trailing stop ajustado).

---

### 🟡 4. Zonas de Soporte y Resistencia (Amarillo Ámbar `#FFD54F`)
* **Qué son:** No son líneas finas de un solo centavo, sino **franjas o zonas de liquidez**.
* **Cómo se calculan y dibujan:**
  1. Se buscan pivotes donde el precio giró en el pasado y se agrupan aquellos niveles que estén a menos de medio ATR de distancia (clusters).
  2. Se exige al menos **2 toques históricos** para considerarse un nivel válido.
  3. **Espesor de la Zona:** Se le da un semiancho de $\pm 0,18 \times \text{ATR}_{14}$ arriba y abajo del precio central.
  4. **Filtro de Espacio Operativo ($\ge 1,0 \times \text{ATR}$):** Para que una zona sea publicada y dibujada como Soporte o Resistencia táctica, debe estar a una distancia prudente del precio spot (mínimo 1 ATR). Esto evita que la zona quede montada sobre la vela actual y garantiza espacio para ganar.

---

### 🟣 5. Líneas de Contexto (Lavanda Discontinua `#B39DDB`)
* **Qué son:** Son directrices de temporalidad superior (Gráfico Diario **D1** o Semanal **W1**).
* **Para qué sirven:**
  - Resuelven la regla clásica de mercado: *"Nunca operes contra la tendencia del marco mayor"*.
  - Si en H4 vemos una señal de compra pero justo arriba pasa una línea de contexto lavanda de D1, el operador sabe que esa línea actuará como un freno institucional potente.

---

### ⚪ 6. Bordes de Rango (Gris Pizarra `#CBD5E1`)
* **Qué son:** Se activan únicamente cuando el mercado está en consolidación lateral (sin directrices diagonales válidas).
* **Cómo se trazan:**
  - Techo: El precio más alto alcanzado en la última semana.
  - Piso: El precio más bajo alcanzado en la última semana.
  - Indican que el activo está "encerrado en una caja" y que hay que esperar a que salga de los bordes para volver a operar tendencias.

---

## 4. Guion Rápido de 30 Segundos para Explicárselo a un Cliente

> *"En nuestros gráficos no usamos indicadores mágicos ni medias que se retrasan. Todo se basa en 2 líneas principales:*
>
> 1. *La **línea roja (Acción)** es el muro que el mercado acaba de romper para darnos la señal de entrada.*
> 2. *La **línea verde (Seguridad)** es el piso que cuida tu dinero: ahí se arrastra el stop y te dice exactamente cuándo salir si el mercado cambia.*
> 3. *Las **franjas amarillas** son los techos y pisos horizontales mayores donde el precio buscará frenar para tomar ganancias.*
>
> *Si el precio se mantiene sobre la línea verde y avanza hacia la franja amarilla, la operación está sana y tiene espacio para correr."*
