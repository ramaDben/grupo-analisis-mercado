# GI Risk Cockpit EA — Manual Operativo y Técnico (MT5)

**Grupo Inteligencia — Centro de Mando y Gestión de Riesgo en Subventana**  
*Control de capital activo, asignación de SL/TP a directrices de TV y proyección gráfica en tiempo real.*

---

## 1. Visión General

`GI_Risk_Cockpit` (versión 1.20) es un **Asesor Experto (EA)** de alta precisión diseñado para transformar la subventana inferior de MetaTrader 5 (subventana 1) en un centro de mando operativo institucional limpio y sin fricciones.

En lugar de ocupar espacio en el gráfico de precios con paneles flotantes intrusivos o mantener un oscilador pasivo, este EA:
1. Se conecta en vivo con las directrices de [`GI_Canales_Seguridad`](file:///C:/Users/bbrav/grupo-analisis-mercado/mql5/GI_Canales_Seguridad.mq5).
2. Lee los precios en tiempo real de cada directriz y nivel estructural (`OBJ_TREND`, `OBJ_HLINE`).
3. **Proyecta visualmente en el gráfico de velas principal (ventana 0)** las líneas dinámicas de **Stop Loss (rojo coral)**, **Take Profit (verde esmeralda)** y **Entrada estimada**, acompañadas por un **badge flotante con el desglose de métricas**: precio, distancia en puntos, riesgo/beneficio en USD y ratio R:R.
4. **Detección Geométrica Natural (Sin Toggles)**: Si el nivel seleccionado para Stop Loss se encuentra por debajo del precio actual, el sistema lo interpreta naturalmente como **COMPRA (BUY)**; si se encuentra por encima, lo interpreta naturalmente como **VENTA (SELL)**.
5. Permite **agrandar libremente la subventana hacia arriba** arrastrando el divisor horizontal sin límites artificiales de escala ni alturas fijas.
6. **Espaciado Holgado Superior (Padding-Top 44px)**: La barra superior y las tarjetas cuentan con un respiro vertical generoso para evitar solapamientos con el divisor del gráfico o los rótulos nativos de MT5.
7. Calcula automáticamente el **tamaño exacto de lote institucional** para arriesgar únicamente el capital deseado ($0.5\%$, $1.0\%$, $2.0\%$ o $\$ \text{Fijo}$).
8. Aplica un **colchón dinámico proporcional al spread real del símbolo** ($(\text{Ask} - \text{Bid}) \times 1.5$), adaptándose con precisión milimétrica a Forex, Oro (XAUUSD), Bitcoin (BTCUSD) o Índices bursátiles.

---

## 2. Mapa de Botones y Directrices de la Estrategia

Cada botón de la subventana inferior refleja el rol y color oficial de la estrategia de Grupo Inteligencia con su cotización real en vivo:

| Línea / Botón | Color Oficial | Código HEX | Rol Operativo Principal |
| :--- | :--- | :--- | :--- |
| **🟢 Seguridad** | Verde Esmeralda | `#26C6A0` | Piso dinámico alcista o techo dinámico bajista (Stop Loss principal). |
| **🟡 Soporte / Resist. S/R** | Amarillo Ámbar | `#FFD54F` | Barreras estructurales horizontales (Soporte en compras, Resistencia en ventas). |
| **🟢 Seguimiento** | Verde Menta | `#9BE7C4` | Abanico acelerado de velocidad (Trailing ceñido o salida rápida). |
| **🔴 Acción** | Rojo Coral | `#FF4D5E` | Gatillo de ruptura o retroceso / quiebre de directriz contraria. |
| **🟣 Contexto D1** | Lavanda | `#B39DDB` | Directriz de marco temporal mayor (D1 / W1). |
| **⚪ Piso / Techo Rango** | Gris Pizarra | `#CBD5E1` | Mínimo y máximo del canal lateral semanal. |
| **🔵 Ratio Fijo 1:2** | Azul Cielo | `#38BDF8` | Objetivo matemático a 2 veces la distancia del Stop Loss. |

---

## 3. Arquitectura del Cockpit (4 Columnas)

```text
┌─────────────────────────┬───────────────────────────────┬───────────────────────────────┬──────────────────────────────────────┐
│ 1. CUENTA & SIZING      │ 2. ASIGNAR STOP LOSS (SL)     │ 3. ASIGNAR TAKE PROFIT (TP)   │ 4. ÓPTICA R:R & EJECUCIÓN            │
│                         │                               │                               │                                      │
│  Balance y Equidad      │  [🟢 Seguridad: 2.650,40]     │  [🟡 Resist. S/R: 2.685,00]   │  Ratio R:R: 1 : 2.15 (ÓPTIMO)        │
│  PnL Sesión en tiempo r.│  [🟡 Soporte S/R: 2.642,10]   │  [🔴 Acción Q.: 2.678,20]     │                                      │
│  Botones: 0.5%, 1%, 2%  │  [🟢 Seguimiento: 2.654,20]   │  [🟣 Contexto D1: 2.710,00]   │  [ ▲ BUY MARKET ]  [ ▼ SELL MARKET ] │
│  Lote Calculado exacto  │  [🔴 Acción: 2.668,50]        │  [⚪ Techo Rango: 2.695,00]   │      0.45 Lots         0.45 Lots     │
│                         │  [🟣 Contexto D1: 2.620,00]   │  [🟢 Proyección: 2.705,00]    │                                      │
│  Límite Drawdown Día    │  [⚪ Piso Rango: 2.635,00]    │  [🔵 Ratio 1:2: 2.682,50]     │  [ BE ]  [ Trail Seg. ]  [ Cerrar ]  │
│  Colchón Spread Dinámico│  SL con Colchón 1.5x Spread   │  TP Seleccionado + Proyección │  Ejecución instantánea con CTrade    │
└─────────────────────────┴───────────────────────────────┴───────────────────────────────┴──────────────────────────────────────┘
```

---

## 4. Proyección Visual en el Gráfico Principal (Ventana 0)

Al seleccionar cualquier botón de SL o TP, se dibujan instantáneamente en las velas principales:
- **Línea Roja Punteada (`GI_RC_PREV_LINE_SL`)**: Nivel exacto donde se colocará el Stop Loss con el colchón de spread incorporado.
- **Línea Verde Punteada (`GI_RC_PREV_LINE_TP`)**: Nivel exacto del Take Profit objetivo.
- **Línea Azul Punteada (`GI_RC_PREV_LINE_ENTRY`)**: Precio de entrada en vivo (`Ask` para Buy, `Bid` para Sell).
- **Badge Informativo Flotante**: Panel compacto en la esquina superior derecha que desglosa:
  - Estructura geométrica (`COMPRA (BUY)` o `VENTA (SELL)`).
  - Stop Loss: precio, distancia en puntos y tamaño de lote asignado.
  - Take Profit: precio, distancia en puntos y ratio R:R resultante.
  - Riesgo monetario ($) y valor del colchón dinámico.

---

## 5. Failsafe contra Errores de Broker

1. **Protección `SYMBOL_TRADE_STOPS_LEVEL`**:
   - Tanto para órdenes de compra (`BUY`) como de venta (`SELL`), el EA garantiza que la distancia del Stop Loss y del Take Profit respete la distancia mínima impuesta por el servidor del broker, evitando el error `10016: TRADE_RETCODE_INVALID_STOPS`.
2. **Alertas Emergentes**:
   - Si una orden es rechazada por el broker (por ejemplo, margen insuficiente o mercado cerrado), se emite un `Alert()` sonoro y visual en pantalla con el código y descripción literal.
3. **Limpieza Rigurosa**:
   - Al remover el EA del gráfico (`OnDeinit`), se eliminan todos los objetos proyectados (`GI_RC_PREV_*`) y los objetos de la subventana (`GI_RC_*`), dejando el gráfico completamente limpio.
