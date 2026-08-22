# 📘 Guía de Uso: Sistema Impulso de Alexander Elder

> [!NOTE]
> **El Sistema Impulso no es un sistema automático de compra y venta**, sino un **Sistema de Censura**. Su propósito principal es mantenerte fuera de problemas prohibiéndote operar en contra del momentum del mercado. 

Esta guía detalla cómo utilizar el indicador `Sistema_Impulso_Elder.mq5` basándose estrictamente en las reglas descritas por el Dr. Alexander Elder en su libro *"El Nuevo Vivir del Trading"*.

---

## 🎨 Los 3 Colores del Sistema

El indicador colorea las velas basándose en dos fuerzas principales: la **Inercia** (Media Móvil Exponencial rápida de 13 períodos) y la **Potencia** (Pendiente del Histograma MACD 12,26,9).

| Color | Comportamiento Técnico | Control | Regla de Censura |
| :--- | :--- | :--- | :--- |
| 🟢 **Verde** | EMA 13 sube + MACD-H sube | **Toros** (Alcistas) | **PROHIBIDO VENDER EN CORTO.** Permitido comprar o mantenerse al margen. |
| 🔴 **Rojo** | EMA 13 baja + MACD-H baja | **Osos** (Bajistas) | **PROHIBIDO COMPRAR (LARGOS).** Permitido vender en corto o mantenerse al margen. |
| 🔵 **Azul** | EMA y MACD-H se contradicen | **Neutral** | **Sin prohibiciones.** El mercado está indeciso, permitido operar en ambas direcciones. |

---

## 🚀 Cómo Buscar Entradas (Setup)

Alexander Elder recomienda encarecidamente utilizar el **Sistema de Triple Pantalla** (revisar múltiples marcos temporales).

1. **La Decisión Estratégica (Marco Mayor):** 
   Revisa tu gráfico a largo plazo (por ejemplo, Semanal). Identifica la tendencia. Si el semanal es Verde, solo buscarás compras. Si es Rojo, solo buscarás cortos.
2. **La Decisión Táctica (Marco Menor):**
   Vuelve a tu gráfico operativo (por ejemplo, Diario). 
   - **Para Comprar:** Si el Semanal es alcista (Verde/Azul), espera a que el Diario sufra una retirada y se ponga Rojo (prohibido comprar). Cuando el Diario pierda su color Rojo y pase a **Azul o Verde**, se activa el "gatillo" de entrada en largo. Estarás comprando una corrección a favor de la tendencia mayor.
   - **Para Vender en Corto:** Si el Semanal es bajista (Rojo/Azul), espera a que el Diario repunte y se ponga Verde (prohibido vender). Cuando el Diario pase de Verde a **Azul o Rojo**, se activa el gatillo para entrar en corto.

> [!TIP]
> Nunca persigas una vela verde enorme que ya ha despegado. Las mejores compras suceden cuando el mercado pasa de Rojo (miedo) a Azul (estabilización) o Verde (inicio del repunte).

---

## 🚪 Cuándo Salir y Recoger Beneficios

Tu horizonte temporal define cuándo salir:

*   **Swing Traders (Corto Plazo):** Cierra tu posición tan pronto como el Sistema Impulso deje de apoyar la dirección de tu operación. Si estás en largo (comprado) y la vela verde cambia a azul, es momento de recoger beneficios. No esperes a que se vuelva roja.
*   **Traders de Posición (Largo Plazo):** Si atrapas una gran tendencia, puedes aguantar durante las barras azules (pausas). Sin embargo, si tienes una posición larga y aparece una barra **Roja**, debes salir o, como mínimo, ajustar tu Stop Loss de forma muy ceñida, porque los bajistas han tomado el control absoluto.

---

## 🛡️ Gestión del Riesgo: El Triángulo de Hierro

> [!WARNING]
> Un buen análisis no sirve de nada si un solo "mordisco de tiburón" (una mala operación sin protección) acaba con tu cuenta. 

Aplica siempre la **Regla del 2%**. Nunca expongas más del 2% del capital total de tu cuenta en una sola operación.

### Pasos para definir tu tamaño de posición:
1.  **Riesgo Máximo de la Cuenta ($A):** Calcula el 2% del total de tu capital (Ej: Si tienes $10.000, tu riesgo máximo son $200).
2.  **Riesgo por Acción/Lote ($B):** Define la distancia entre tu Precio de Entrada y tu Stop Loss (Ej: Compras a $50 y pones stop en $48. Riesgo = $2 por acción).
3.  **Tamaño de la Posición ($C):** Divide el Riesgo Máximo entre el Riesgo por Acción ($A / $B = $200 / $2 = 100 acciones). **Este es el tamaño exacto con el que debes operar.**

### 🛑 Colocación de Stops (Stops de Nic)
Nunca pongas stops en niveles "obvios" (números redondos como $50.00 o justo debajo del último mínimo visible de todos), ya que el mercado suele barrerlos. Utiliza la táctica de buscar el *segundo mínimo más reciente* o utiliza un margen de seguridad basado en el ATR (Average True Range) para evitar que el "ruido" del mercado te saque prematuramente de una buena operación.

---

> [!IMPORTANT]
> **Resumen del Flujo de Trabajo:**
> 1. Analiza el marco mayor para la tendencia.
> 2. Usa el Sistema Impulso en el marco menor para filtrar tu entrada.
> 3. Calcula tu riesgo (2%) y define tu Stop Loss antes de entrar.
> 4. Entra al mercado y gestiona (sal de la operación cuando el color se oponga a tu trade).
