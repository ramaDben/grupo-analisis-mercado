---
name: trading-cuantitativo-intermercado
description: Evalúa y audita operaciones de trading cuantitativo en USD/CLP, USD/JPY, Oro, Petróleo y Nasdaq contra el Playbook V2, calcula lotajes por Volatility Targeting y gestiona blackouts por calendario macro.
---

# Skill: Trading Cuantitativo Intermercado & Auditoría de Operaciones (Playbook V2)

Esta skill dota al agente de la inteligencia operativa para asesorar, validar y auditar las decisiones de trading de la mesa de dinero, aplicando estrictamente el [Playbook Maestro de Trading Cuantitativo](../../../docs/PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md).

---

## 1. Protocolo de Auditoría Pre-Trade (3 Pasos Obligatorios)

Cuando el usuario proponga o pregunte por una operación (ej. *"¿Puedo comprar USD/CLP?"*, *"¿Qué nivel vigilar en USD/JPY?"* o *"Quiero meter una venta en Oro"*):

### Paso 1: Consultar el Snapshot de Sesgo (Tool MCP o Bias Reader)
- Consulta la herramienta `get_macro_bias(symbol="<ACTIVO>")` o ejecuta `python scripts/premarket.py --symbol <ACTIVO>`.
- Revisa el **Régimen Macro Global** ($\mathcal{R}_0$ a $\mathcal{R}_4$), el **Sesgo Score** $[-2.0, +2.0]$ y el **Índice de Confianza**.
- Si la tool retorna `STALE_DATA` (>24h en días hábiles o >80h en fin de semana), indica al usuario que debe ejecutar primero la **cadena completa**: `uv run --with MetaTrader5 python scripts/pipeline_datos.py`. La ingesta sola es el paso 1 de 3 y dejaría el sesgo igual de vencido, porque `macro_bias_output.json` lo produce el paso 3.

### Paso 2: Validar la Dirección y el Régimen
- **En Régimen $\mathcal{R}_0$ (Calma/Rango)**: Solo se permite operar reversión a la media entre soportes y resistencias ($S_1/R_1$) o canales Donchian. Prohibido perseguir quiebres tendenciales (*Breakout Chase*).
- **En Regímenes $\mathcal{R}_1 / \mathcal{R}_3$ (Inflación / Estanflación)**: Solo compras en Oro y Petróleo. Prohibido abrir posiciones cortas (*Shorts*) aun con osciladores sobrecomprados.
- **En Régimen $\mathcal{R}_4$ (Recesión / Vuelo a la Calidad)**: Prohibido comprar activos cíclicos (Cobre, Renta Variable) sin confirmación de piso.

### Paso 3: Validar Setups Permitidos vs. Prohibidos
- Revisa la lista `setups_permitidos` y `setups_prohibidos` del activo.
- Si el trade propuesto pertenece a los prohibidos, emite una advertencia de riesgo explícita citando la justificación macroeconómica del Playbook.

---

## 2. Calculadora de Lotaje Institucional (Volatility Targeting)

Para garantizar que cada operación arriesgue exactamente el **1.0% del capital de la cuenta** (independiente de la volatilidad del mercado):

$$\text{Lotaje} = \frac{\text{Capital}_{\text{USD}} \times \text{Riesgo\%}}{\text{Distancia Stop Loss en Puntos} \times \text{TickValue}_{\text{USD}}}$$

### Conversión Multidivisa de Tick Value:
* **Para `USD/CLP`** (Cuenta en USD, cotización en CLP):
  $$\text{TickValue}_{\text{USD}} = \frac{100.000 \text{ USD} \times 1.0 \text{ CLP}}{\text{Precio Spot}_{\text{USDCLP}}}$$
* **Para `USD/JPY`** (Cuenta en USD, cotización en JPY a 3 decimales):
  $$\text{TickValue}_{\text{USD}} = \frac{100.000 \text{ USD} \times 0.01 \text{ JPY}}{\text{Precio Spot}_{\text{USDJPY}}}$$
  *(Ejemplo: Con Spot 159.200, 1 pip / 0.01 JPY $\approx 6.28\text{ USD por lote estándar}$)*.
* **Para `XAU/USD` (Oro)**: $\text{TickValue} = 100\text{ USD por punto}$ ($1\text{ lote} = 100\text{ oz}$).
* **Para `COPPER` (Cobre)**: $\text{TickValue} = 1.0\text{ USD por punto}$ ($1\text{ lote} = 1\text{ tonelada métrica, cotizado en USD/t}$).
* **Para `WTI / BRENT` (Petróleo)**: $\text{TickValue} = 1.000\text{ USD por punto}$ ($1\text{ lote} = 1.000\text{ barriles}$).
* **Para `US100` (Nasdaq)**: $\text{TickValue} = 20\text{ USD por punto}$ ($1\text{ lote estándar CFD}$).

---

## 3. Protocolo de Gestión de Salidas por Régimen

* **En Régimen de Rango ($\mathcal{R}_0$)**:
  - Salida de beneficio obligatoria por **Nivel Opuesto de Canal** o Resistencia/Soporte clave. Prohibido dejar correr indefinidamente.
* **En Regímenes de Tendencia ($\mathcal{R}_1, \mathcal{R}_2, \mathcal{R}_3, \mathcal{R}_4$)**:
  - Prohibido Take Profit rígido.
  - Salida obligatoria por **Chandelier Trailing Stop** a **$3.0 \times \text{ATR}_{14}(\text{H1})$** para capturar la asimetría de retornos (*Crisis Alpha*).

---

## 3 bis. Modelo ADC (Ancho Dinámico de Canal) & Volatilidad ATR

El dimensionamiento de objetivos y recorridos se apoya en el **Modelo ADC + ATR**:
* **ADC (Ancho Dinámico de Canal)**: Amplitud de canal entre extremos de Donchian 50 o Bandas de Bollinger ($\text{Superior} - \text{Inferior}$) para determinar si el activo está comprimiendo o expandiendo volatilidad.
* **Recorrido por Impulso Intradía**: Calculado como $1.5 \times \text{ATR}_{14}(\text{H1})$ tras quiebres de $S_1/R_1$.
* **Validación de Capacidad Diaria**: Comparación contra el **ATR Restante Diario** ($\text{ATR}_{14}\text{ D1} - \text{Rango Hoy}$) con piso del 30% del ATR diario.

---

## 3 ter. Filosofía Operativa: Autonomía del Trader y Piezas Públicas Limpias

1. **Autonomía y Cero Operativa Delegada:**
   El Motor GI **no emite señales a ciegas ni opera por nadie**. Su propósito institucional es entregar **claridad matemática, niveles técnicos objetivos ($S_1/R_1$) y fundamentos de riesgo**, permitiendo que cada trader, inversionista o empresa tome sus propias decisiones informadas.
2. **Piezas Públicas 100% Limpias:**
   Los flujos y comandos públicos (`/alerta`, `/apertura`, `/dato_macro`, `/noticia`, `/story`) entregan **exclusivamente material para el cliente final** (Mensaje WhatsApp + Story visual de marca). Queda excluida la generación automática de guiones o piezas internas en canales públicos.

---

## 4. Protocolo de Blackouts por Calendario Económico

Antes de validar la entrada inmediata a mercado, consulta `obtener_calendario_macro` para verificar si estamos en ventana de restricción:

| Evento Macroeconómico | Timezone Nativa | Ventana Pre | Ventana Post | Acción Operativa |
| :--- | :--- | :---: | :---: | :--- |
| **FOMC / Decisión Fed** | `America/New_York` | **-30 min** | **+75 min** | Bloqueo total de nuevas órdenes a mercado y cancelación de órdenes límite cercanas. |
| **NFP / IPC EE.UU.** | `America/New_York` | **-15 min** | **+30 min** | Bloqueo por dispersión de spreads interbancarios. |
| **RPM Banco Central Chile** | `America/Santiago` | **-15 min** | **+45 min** | Esperar publicación del comunicado (18:00 CLT) y absorción. |
| **Imacec / IPC Chile** | `America/Santiago` | **-15 min** | **+20 min** | Esperar absorción de la apertura (08:30 CLT). |
| **Decisión Tasas Banco de Japón (BoJ)** | `Asia/Tokyo` | **-30 min** | **+60 min** | Bloqueo por alta volatilidad en pares con Yen (USD/JPY). |
| **IPC Nacional Japón (MIC)** | `Asia/Tokyo` (08:30 JST) | **-15 min** | **+30 min** | Ventana nocturna en Chile (01:00 AM) de absorción de spreads. |

---

## 5. Comandos y Herramientas Rápidas

* **Generar Plan Pre-Market para un Activo**:
  ```powershell
  python scripts/premarket.py --symbol USDCLP --capital 25000 --risk 1.0
  ```
* **Generar Briefing de Todos los Activos**:
  ```powershell
  python scripts/premarket.py --all
  ```
* **Consultar Sesgo en Python**:
  ```python
  from market_data_mcp.bias_reader import cargar_macro_bias
  res = cargar_macro_bias("USDCLP")
  ```
