# Respuesta de Arquitectura Cuantitativa & Especificación Motor GI v3.0
## De Screener de Convicción a Emisor Determinista de Tickets de Ejecución

**Destinatario:** Mesa de Dinero, Research Cuantitativo — Grupo Inteligencia & Auditoría Externa (Grok 4.6)  
**Emisor:** Arquitectura de Sistemas Cuantitativos — Grupo Inteligencia  
**Fecha:** 28 de agosto de 2026  
**Documentos de Referencia:**  
* `auditoria_motor_gi_entradas_salidas.md` (Grok 4.6)  
* `PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md` v2.0.0 ([`docs/PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md`](./PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md))  
* `playbook_config.yaml` ([`config/playbook_config.yaml`](../config/playbook_config.yaml))  
* `funcionamiento_motor_gi.md` v2.4 ([`docs/funcionamiento_motor_gi.md`](./funcionamiento_motor_gi.md))  

---

## 1. Dictamen General del Arquitecto

La auditoría cuantitativa emitida por **Grok 4.6** es recibida por este equipo con la máxima consideración técnica: es **quirúrgica, metodológicamente sólida y sumamente oportuna**. 

En finanzas cuantitativas, la arrogancia destruye capital. Un arquitecto no defiende con retórica lo que es inconsistente en código. La versión 2.4 del Motor GI resolvió con rigor matemático la modelación de series y volatilidad (suavizado RMA de Welles Wilder, Donchian sobre velas cerradas, presupuesto ADC+ATR y piso de sesión activa), pero incurrió en una **falla conceptual en su Sección 6**: **afirmar que definía "con exactitud" puntos de entrada y salida, cuando en realidad entregaba disyunciones lógicas (`OR`) y un Score generalista.**

Un operador (humano o algorítmico) **no puede ejecutar un `OR`**. Si el sistema emite *"entrada por Donchian o pullback EMA20 con stop a 1 ATR o bajo EMA50"*, no está emitiendo una orden; está transfiriendo la discrecionalidad al operador.

Por ende, **la postura oficial de la Arquitectura es de adopción total de los principios de ejecución determinista propuestos por la auditoría**, evolucionando formalmente el sistema hacia el **Motor GI v3.0**.

---

## 2. Aclaración Estructural: Lo que la Auditoría Externa no pudo ver (El Playbook V2 ya existe y es 100% determinista)

En los puntos **2.6** y **9** de su dictamen, Grok 4.6 señala:
> *"Régimen sin umbral: R1 compra oro y Nasdaq a la vez; R2 compra oro y dólar. Sin reglas numéricas (Δ UST, Δ DXY, VIX, cobre) el gate_playbook es discrecional. Un régimen mal etiquetado invalida todas las entradas del día."*

### Aclaración Técnica:
Grok 4.6 evaluó únicamente el manual general `funcionamiento_motor_gi.md` v2.4 (que resume los regímenes conceptualmente en una tabla de 5 filas para difusión) y **no tuvo acceso al documento maestro ni a la configuración del sistema**:
* [`docs/PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md`](./PLAYBOOK_TRADING_CUANTITATIVO_INTERMERCADO.md)
* [`config/playbook_config.yaml`](../config/playbook_config.yaml)
* [`scripts/macro_bias_engine.py`](../scripts/macro_bias_engine.py)

El motor macro del Grupo Inteligencia **no es discrecional ni carece de umbrales**. Opera bajo una **Máquina de Estados Finita (FSM)** gobernada por fórmulas matemáticas duras e histéresis temporal sobre datos oficiales:

### A. Jerarquía de Precedencia Matemática
$$\mathcal{R}_3 \text{ (Estanflación / Shock Petróleo)} \succ \mathcal{R}_1 \text{ (Shock Inflación / Breakeven)} \succ \mathcal{R}_4 \text{ (Recesión / Bull Steepener)} \succ \mathcal{R}_2 \text{ (Goldilocks)} \succ \mathcal{R}_0 \text{ (Calma / Rango)}$$

### B. Umbrales Cuantitativos de Activación (Implementados en `playbook_config.yaml`)

```yaml
# Umbrales vigentes en config/playbook_config.yaml
regime_thresholds:
  # R3: Estanflación / Turbulencia Geopolítica
  oil_shock_pct_5d: 3.5                      # max(|Δ%WTI_5D|, |Δ%Brent_5D|) ≥ 3.5%
  oil_extreme_shock_pct: 5.25               # Override por shock extremo (> 150%)
  us10y_shock_bps_5d: 10.0                  # Δy_10Y ≥ 10 bps
  tips10y_shock_bps_5d: 8.0                 # ΔDFII10 ≥ 8 bps

  # R1: Shock Inflacionario / Cost-Push
  breakeven_shock_bps_5d: 10.0              # ΔT10YIE_5D ≥ 10 bps
  curve_flat_threshold_bps: 20.0            # Spread 2s10s ≤ 0.20%

  # R4: Recesión / Vuelo a la Calidad
  curve_inversion_threshold: 0.0            # Spread 2s10s < 0.0%
  bull_steepener_dgs2_drop_bps: -15.0       # ΔDGS2_5D ≤ -15 bps (recorte agresivo)
  bull_steepener_spread_expansion_bps: 10.0 # ΔSpread 2s10s ≥ +10 bps
  copper_recession_pct_5d: -2.5             # Δ%Cobre_5D ≤ -2.5%

  # R2: Expansión / Desinflación (Goldilocks)
  copper_goldilocks_pct_5d: 1.5             # Δ%Cobre_5D ≥ +1.5%
  us10y_stable_bandwidth_bps: 6.0           # |Δy_10Y| ≤ 6 bps

  # Histéresis Anti-Parpadeo (Anti-Whipsaw)
  hysteresis_required_confirmations: 2      # Exige 2 lecturas D1 consecutivas
  extreme_shock_override_ratio: 1.5         # Salto inmediato solo si shock > 150%
```

### C. Índice Matemático de Confianza del Régimen
$$\text{Confianza}_t = 100 \times \left( 0.40 \cdot \mathcal{S}_{\text{frescura}} + 0.35 \cdot \mathcal{S}_{\text{antigüedad}} + 0.25 \cdot \mathcal{S}_{\text{cobertura}} \right)$$

### D. Implementación Python Exacta en Producción (`scripts/macro_bias_engine.py`)

A continuación se adjunta el extracto de código fuente en Python que ejecuta esta lógica en tiempo real para determinar el régimen de mercado:

```python
# Extracto de scripts/macro_bias_engine.py (Líneas 88-136)

def evaluar_regimen_candidato(deltas: dict, cfg: dict) -> tuple[str, str, bool, str]:
    """
    Evalúa el régimen candidato aplicando el orden de precedencia estricto:
    R3 (Estanflación) ≻ R1 (Inflación Cost-Push) ≻ R4 (Recesión/Bull Steepener) ≻ R2 (Goldilocks) ≻ R0 (Calma)
    """
    rt = cfg["regime_thresholds"]

    oil_shock = deltas.get("oil_max_pct_5d") or 0.0
    us10y_diff_bps = (deltas.get("us10y_diff_5d") or 0.0) * 100.0
    tips10y_diff_bps = (deltas.get("tips10y_diff_5d") or 0.0) * 100.0
    breakeven_diff_bps = (deltas.get("breakeven_diff_5d") or 0.0) * 100.0
    copper_pct_5d = deltas.get("copper_pct_5d") or 0.0
    dgs2_diff_bps = (deltas.get("dgs2_diff_5d") or 0.0) * 100.0
    spread_2s10s = deltas.get("spread_2s10s_actual") or 0.0
    spread_diff_bps = (deltas.get("spread_2s10s_diff_5d") or 0.0) * 100.0

    # 1. Prioridad 1: R3 - Estanflación / Turbulencia Geopolítica
    es_shock_petroleo = oil_shock >= rt["oil_shock_pct_5d"]
    es_shock_tasas = (us10y_diff_bps >= rt["us10y_shock_bps_5d"]) or (tips10y_diff_bps >= rt["tips10y_shock_bps_5d"])
    if es_shock_petroleo and es_shock_tasas:
        es_extremo = oil_shock >= rt["oil_extreme_shock_pct"] or us10y_diff_bps >= rt["us10y_extreme_shock_bps"]
        return "R3_ESTANFLACION_SHOCK", "Estanflación / Turbulencia Geopolítica", es_extremo, f"Petróleo disparándose (+{oil_shock:.1f}%) y tasas en tensión (+{us10y_diff_bps:.1f} bps)."

    # 2. Prioridad 2: R1 - Shock Inflacionario / Cost-Push
    es_shock_breakeven = breakeven_diff_bps >= rt["breakeven_shock_bps_5d"]
    es_curva_plana = (spread_2s10s * 100.0) <= rt["curve_flat_threshold_bps"]
    if es_shock_breakeven and (es_curva_plana or us10y_diff_bps > 5.0):
        es_extremo = breakeven_diff_bps >= rt["breakeven_extreme_shock_bps"]
        return "R1_SHOCK_INFLACIONARIO", "Shock Inflacionario / Cost-Push", es_extremo, f"Expectativas de inflación (Breakeven) en alza (+{breakeven_diff_bps:.1f} bps) y curva contenida."

    # 3. Prioridad 3: R4 - Recesión / Vuelo a la Calidad (Curva invertida o Bull Steepener)
    es_curva_invertida = spread_2s10s < rt["curve_inversion_threshold"]
    es_bull_steepener = (dgs2_diff_bps <= rt["bull_steepener_dgs2_drop_bps"]) and (spread_diff_bps >= rt["bull_steepener_spread_expansion_bps"])
    es_cobre_recesion = copper_pct_5d <= rt["copper_recession_pct_5d"]

    if (es_curva_invertida or es_bull_steepener) and es_cobre_recesion:
        es_extremo = copper_pct_5d <= rt["copper_extreme_recession_pct"]
        return "R4_RECESION_VUELO_CALIDAD", "Recesión / Vuelo a la Calidad", es_extremo, f"Curva alertando desaceleración/recortes y Cobre cayendo ({copper_pct_5d:.1f}%)."

    # 4. Prioridad 4: R2 - Expansión / Desinflación (Goldilocks)
    es_cobre_fuerte = copper_pct_5d >= rt["copper_goldilocks_pct_5d"]
    es_tasas_estables = abs(us10y_diff_bps) <= rt["us10y_stable_bandwidth_bps"]
    if es_cobre_fuerte and es_tasas_estables:
        es_extremo = copper_pct_5d >= rt["copper_extreme_goldilocks_pct"]
        return "R2_GOLDILOCKS_EXPANSION", "Expansión Sólida / Goldilocks", es_extremo, f"Cobre en expansión (+{copper_pct_5d:.1f}%) con tasas del Tesoro estables ({us10y_diff_bps:+.1f} bps)."

    # 5. Default: R0 - Calma / Rango / Absorción
    return "R0_CALMA_RANGO", "Calma / Rango / Absorción", False, "Drivers en equilibrio dinámico sin shocks direccionales extremos."
```

**Conclusión de este punto:** La Capa 2 (Macro Bias Engine) es 100% matemática, objetiva y reproducible en Python. Sin embargo, la crítica de Grok sigue siendo válida en el sentido de que **esta precisión macro no estaba conectada a un ticket determinista en la capa de salida**.

---

## 3. Especificación del Motor GI v3.0: Adopción y Reingeniería

Para subsanar todas las observaciones de la auditoría, se define el estándar formal de la versión 3.0:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MOTOR GI v3.0 ARCHITECTURE                      │
├────────────────────────────────────────────────────────────────────────┤
│ 1. INGESTA MACRO SOBERANA    ► FRED, Tesoro US, BCCh, Agenda Oficial   │
│ 2. CLASIFICADOR FSM R0-R4    ► Playbook V2 (Umbrales numéricos duros)  │
│ 3. SCREENER INTERNO          ► Score 0-100 (Uso exclusivo de Research) │
│ 4. FILTROS & GATES CFD       ► Fricción, Remanente, Blackout, Feriado  │
│ 5. GENERADOR DE TICKETS      ► 1 Setup, 1 Entry, 1 SL, TP1 R:R ≥ 1.0   │
│ 6. FIRMA DOW INTERMERCADO    ► Confirmación cruzada obligatoria        │
│ 7. MÁQUINA DE ESTADOS H1     ► ARMED -> READY -> OPEN -> TP1/BE -> END │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 El Contrato del Ticket Cuantitativo (Estructura de Datos Estricta)

Se prohíbe la emisión de alertas basadas en "Score" en canales operativos. El único objeto emitido por el subsistema táctico es el **`Ticket` determinista**:

```python
@dataclass(frozen=True)
class QuantitativeTicket:
    ticket_id: str                   # UUID único del ticket
    symbol: str                      # Ej: "XAUUSD", "USDCLP", "US100"
    regime: str                      # "R0", "R1", "R2", "R3", "R4"
    setup: str                       # "BREAKOUT_ADC" | "PULLBACK_EMA" | "MEANREV_R0"
    side: str                        # "BUY" | "SELL"
    trigger_time: datetime           # Timestamp de la vela H1 CERRADA
    entry_type: str                  # "BUY_STOP" | "SELL_STOP" | "BUY_LIMIT" | "SELL_LIMIT"
    entry_price: float               # Precio exacto de gatillo
    entry_valid_until: datetime      # Caducidad (máx. 2 velas H1 o session_kill)
    stop_loss: float                 # Nivel único (Estructural + 1 spread)
    take_profit_1: float             # Meta técnica inmediata (R:R a TP1 ≥ 1.0)
    take_profit_2: Optional[float]   # Techo de presupuesto (máx. 1.5x ATR táctico)
    rr_to_tp1: float                 # Ratio Recompensa/Riesgo a TP1 (debe ser ≥ 1.0)
    spread_atr_ratio: float          # Spread actual / ATR_14(H1)
    confirm_symbol: str              # Activo del driver intermercado (Dow)
    confirm_status: bool             # True si la firma intermercado es válida
    remaining_d1_atr: float          # Presupuesto diario remanente
    invalidation_rule: str           # Condición matemática de aborto
    session_kill_time: time          # Hora de cierre forzado de sesión
    lot_size: float                  # Sizing por Volatility Targeting
    status: str                      # "ARMED" | "READY" | "OPEN" | "EXPIRED" | "INVALIDATED"
```

> **Regla de Producto:** Si `rr_to_tp1 < 1.0` o `confirm_status == False` o `spread_atr_ratio > c_i`, **el ticket no se instancia (Score táctico = 0)**.

---

### 3.2 Tres Setups Técnicos Mutuamente Excluyentes

Queda estrictamente prohibido evaluar múltiples lógicas sobre un mismo activo. Cada activo clasifica en **exactamente un setup** según su régimen y estructura:

```
                                  ¿Régimen R0 Y ADX < 20?
                                             │
                             ┌───────────────┴───────────────┐
                            SÍ                               NO
                             │                               │
                             ▼                               ▼
                     [MEANREV_R0]             ¿Alineación EMA 20>50>100 Y ADX ≥ 20?
                                                             │
                                             ┌───────────────┴───────────────┐
                                            SÍ                               NO
                                             │                               │
                                             ▼                               ▼
                                      [PULLBACK_EMA]                  ¿Ancho Canal Donchian ≤ 2.5x ATR?
                                                                                     │
                                                                     ┌───────────────┴───────────────┐
                                                                    SÍ                               NO
                                                                     │                               │
                                                                     ▼                               ▼
                                                             [BREAKOUT_ADC]                  [SIN SETUP / WAIT]
```

#### 1. `BREAKOUT_ADC` (Compresión $\to$ Expansión)
* **Condición de Armado:** Ancho del Canal Donchian 50 barras en H1 $\le 2.5 \times \text{ATR}_{14}\text{ (H1)}$ (compresión real). Dirección coherente con Régimen.
* **Trigger (Vela Cerrada):** 
  * Largo: `close[-1] > donchian_high` con cuerpo de vela $\ge 50\%$ del rango total ($TR$).
  * Filtro de momentum: $TR / \text{ATR}_{14} \ge 1.0$ en la vela de ruptura. **No se exige $ADX > 25$** (evita llegar tarde).
  * Veto: $RSI > 75$ (bloquea quiebres sobre-extendidos).
* **Entrada:** `BUY_STOP` 1 tick por encima del *high* de la vela trigger. Válida por 2 velas H1.
* **Stop Loss:** Mínimo de las últimas 20 velas H1 (`sl_struct`) $+ 1\text{ spread}$. Restricción: $0.5 \times \text{ATR} \le |\text{entry} - \text{sl}| \le 1.5 \times \text{ATR}$.
* **Metas:**
  * $TP_1$: Primer nivel $R_1$ o $\text{entry} + 1.0 \times \text{ATR}$, el que sea más cercano.
  * $TP_2$: Siguiente nivel $R_2$ o $\text{entry} + 1.5 \times \text{ATR}$.
  * Validación: $(\text{TP}_1 - \text{entry}) / |\text{entry} - \text{SL}| \ge 1.0$.

#### 2. `PULLBACK_EMA` (Tendencia Estable Previa)
* **Condición de Armado:** Alineación estricta $\text{EMA}_{20} > \text{EMA}_{50} > \text{EMA}_{100}$ en H1 cerrado. $ADX_{14} \ge 20$ (tendencia confirmada).
* **Trigger (Vela Cerrada):** `low[-1]` perfora o toca la $\text{EMA}_{20}$ y `close[-1]` cierra nuevamente por encima de la $\text{EMA}_{20}$.
* **Entrada:** `BUY_STOP` sobre el máximo de la vela de rechazo.
* **Stop Loss:** Detrás del último mínimo de swing local $+ 1\text{ spread}$.
* **Metas:** $TP_1 =$ Último máximo de swing. $TP_2 = \text{entry} + 1.5 \times \text{ATR}$.

#### 3. `MEANREV_R0` (Exclusivo Régimen de Rango)
* **Condición de Armado:** Régimen $\mathcal{R}_0$ **y** $ADX_{14} < 20$. Prohibido si $ADX \ge 20$.
* **Trigger:** Vela cierra fuera de Bandas de Bollinger $(20, 2\sigma)$ y la vela siguiente cierra dentro con $RSI < 35$ (largos) o $RSI > 65$ (cortos).
* **Stop Loss:** Extremo de la vela que perforó la banda $+ 1\text{ spread}$.
* **Metas:** $TP_1 = \text{Banda Media (SMA 20)}$. **Prohibido usar $1.5\times\text{ATR}$** (este setup no busca expansión).

---

### 3.3 Catálogo de Gates Cuantitativos v3.0

Se actualiza la batería de gates de exclusión binaria:

| Gate | Condición Matemática de Veto | Justificación Microestructural |
|---|---|---|
| **`gate_friccion`** | $\frac{\text{Spread}}{\text{ATR}_{14}\text{ (H1)}} > c_i$ | Protege contra la degradación de expectativa matemática por costo de broker. |
| **`gate_remanente`** | $\text{ATR}_{20}\text{ (D1)} - \text{Rango\_Hoy} < \text{Distancia\_SL}$ | Evita entrar cuando el presupuesto diario de recorrido está agotado a las 10:30. |
| **`gate_rr`** | $\frac{|TP_1 - \text{Entry}|}{|\text{Entry} - \text{SL}|} < 1.0$ | Prohíbe tickets donde el primer escalón de toma de beneficios no paga el riesgo. |
| **`gate_confirmacion`** | $\text{Firma Dow Intermercado} == \text{False}$ | Sustituye el volumen no disponible en CFDs mediante correlación cruzada. |
| **`gate_calendario`** | $\text{Hora Actual} \notin \text{Sesión}(CalendarSpec)$ | Anula señales fuera de ventana de liquidez y aplica `session_kill`. |
| **`gate_blackout`** | $t \in [T_{\text{evento}} - 30\text{m}, T_{\text{evento}} + 30\text{m}]$ o $\text{Spread} > 1.5\times\text{Media}$ | Bloqueo por iliquidez/slippage ante noticias macro Tier-1. |

#### Techos de Fricción Calibrados ($c_i$):
* **FX G10:** $c_i = 0.08$
* **XAUUSD / WTI:** $c_i = 0.10$
* **Índices US (US100, US500):** $c_i = 0.12$
* **USD/CLP (Sesión Local):** $c_i = 0.15$
* **Cripto (BTC, ETH):** $c_i = 0.20$

---

### 3.4 Matriz de Confirmación Cruzada (Dow Soberano)

Para emitir un ticket, el activo principal debe contar con la firma confirmatoria de su par intermercado en la misma vela H1 cerrada o tendencia D1:

```
┌─────────────────┬──────────────────────────────────────────┬────────────────────────────────────────┐
│ Activo Ticket   │ Firma Exigida (Al menos una True)        │ Veto Duro Inmediato                    │
├─────────────────┼──────────────────────────────────────────┼────────────────────────────────────────┤
│ US500 (Largo)   │ US100 en la misma dirección H1           │ DXY marcando nuevo máximo H1           │
│ US100 (Largo)   │ US500 en la misma dirección H1           │ DXY marcando nuevo máximo H1           │
│ XAUUSD (Largo)  │ DXY a la baja H1  Ó  UST 10Y a la baja   │ Régimen R4 activo o DXY en nuevo max H1│
│ WTI (Largo)     │ Régimen R3 activo Ó Brent mismo signo H1 │ Ruptura bajista de commodities         │
│ USD/CLP (Largo) │ DXY al alza H1    Ó Cobre a la baja H1   │ Fuera de horario 09:00 - 14:00 CLT     │
│ BTCUSD (Largo)  │ US100 alcista en H1 (solo Régimen R1)    │ Régimen R2 o R4 activo                 │
│ USDJPY (Largo)  │ UST 10Y al alza en D1/H1                 │ Intervención verbal MoF / BoJ          │
└─────────────────┴──────────────────────────────────────────┴────────────────────────────────────────┘
```

---

### 3.5 Especificación de Calendarios (`CalendarSpec`)

El cálculo de Donchian y ATR táctico no puede mezclar sesiones heterogéneas:

```
┌───────────────┬──────────────────────┬─────────────────────────┬──────────────────┐
│ Escenario     │ Ventana Operativa    │ Base ATR / Donchian H1  │ session_kill     │
├───────────────┼──────────────────────┼─────────────────────────┼──────────────────┤
│ USD/CLP       │ 09:00 - 14:00 CLT    │ H1 solo sesión local    │ 13:45 CLT        │
│ Índices US    │ 09:30 - 16:00 NY     │ H1 Regular Trading Hrs  │ 15:45 NY         │
│ FX G10        │ 24 horas (5 días)    │ H1 24h continuo         │ 16:50 NY         │
│ XAU / WTI     │ 24 horas + Pico US   │ H1 24h continuo         │ 16:50 NY         │
│ Cripto        │ 24/7 continuo        │ H1 24h continuo         │ 21:00 UTC (D1)   │
└───────────────┴──────────────────────┴─────────────────────────┴──────────────────┘
```

---

### 3.6 Máquina de Estados del Ciclo de Vida del Ticket

A partir de las 10:30 CLT, los tickets no quedan abandonados; entran en un motor de seguimiento intradiario en velas H1 cerradas:

```
    [ ARMED ] ────(Vela H1 cierra confirmando Trigger)────► [ READY ]
        │                                                       │
        │ (No cumple en 2 velas H1)              (Precio toca Entry)
        ▼                                                       ▼
   [ EXPIRED ]                                              [ OPEN ]
                                                                │
                   ┌────────────────────────────────────────────┼───────────────────────────┐
                   ▼                                            ▼                           ▼
        (Precio toca TP1)                            (Precio toca SL)            (Cierre < donchian_mid
                   │                                            │                 o session_kill)
                   ▼                                            ▼                           │
        • Cerrar 50% Posición                              [ CLOSED_SL ]                    ▼
        • Mover SL a Breakeven + 1 spread                                            [ INVALIDATED ]
                   │
                   ▼
        (Precio toca TP2)
                   │
                   ▼
            [ CLOSED_TP2 ]
```

---

## 4. Dualidad de Producto: Research Editorial vs. Canal de Ejecución

Para mantener la coherencia institucional del Grupo Inteligencia, se establece una **separación estricta de canales y formatos de salida**:

```
                               ┌────────────────────────────────────────┐
                               │             MOTOR GI v3.0              │
                               └──────────────────┬─────────────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
        ┌───────────────────────────────────┐             ┌───────────────────────────────────┐
        │        CANAL RESEARCH & BI        │             │      CANAL TÁCTICO / WHATSAPP     │
        │    (Stories 16:9 / 9:16 / PDF)    │             │      (Mesa de Dinero & Clientes)  │
        ├───────────────────────────────────┤             ├───────────────────────────────────┤
        │ • Score GI (0 - 100) visible      │             │ • Score GI OCULTO (solo interno)  │
        │ • Top 3 de Activos por Convicción │             │ • SOLO Fichas de Tickets READY    │
        │ • Contexto Macro y Volatilidad    │             │ • 1 Setup, 1 Entry, 1 SL, 1 TP1   │
        │ • Gráficos H1 con 60 velas        │             │ • R:R exacto y firma Dow visible  │
        │ • Presupuesto ADC+ATR Típico      │             │ • Alertas de Breakeven y Aborto   │
        └───────────────────────────────────┘             └───────────────────────────────────┘
```

### Formato Estándar de Alerta Táctica (WhatsApp):

```text
🎯 TICKET GI: XAUUSD BUY | BREAKOUT_ADC | Régimen R2
────────────────────────────────────────
• Entrada (STOP): 2,514.50 (Válida hasta 12:00 CLT)
• Stop Loss: 2,504.20 (Estructural + spread)
• Meta 1 (TP1): 2,525.00 | R:R 1.02
• Meta 2 (TP2): 2,530.00 (Presupuesto 1.5x ATR)
• Fricción: Spread/ATR 6.8% [OK]
• Firma Dow: DXY a la baja [CONFIRMADO]
• Aborto: Cierre H1 < 2,508.00 o 16:50 NY
────────────────────────────────────────
```

---

## 5. Plan de Implementación y Calendario Técnico

| Sprint | Hito Técnico | Módulos Involucrados | Estado |
|:---:|---|---|:---:|
| **S1 (P0)** | Implementación de `QuantitativeTicket` y lógica de 1 solo SL/TP con $R:R \ge 1.0$ | `src/market_data_mcp/analisis.py` | 🔨 En curso |
| **S1 (P0)** | Desacople de setups (`BREAKOUT_ADC`, `PULLBACK_EMA`, `MEANREV_R0`) y corrección de $ADX$ | `scripts/screener_gi.py` | 🔨 En curso |
| **S1 (P0)** | Incorporación de `gate_friccion` y `gate_remanente` | `scripts/screener_gi.py` | 🔨 En curso |
| **S2 (P1)** | Implementación de `gate_confirmacion` (Matriz Dow Soberana) | `src/market_data_mcp/tools/macro_bias.py` | 📅 Programado |
| **S2 (P1)** | Creación de `CalendarSpec` y motor `session_kill` | `src/market_data_mcp/mt5_client.py` | 📅 Programado |
| **S2 (P1)** | Bucle de seguimiento de estados intradiarios H1 | `scripts/state_machine_tickets.py` | 📅 Programado |
| **S3 (P2)** | Calibración empírica de techos $c_i$ con 40 sesiones de MT5 | `data central/DATA MOTOR GI/` | 📅 Programado |

---

## 6. Conclusión de la Dirección de Arquitectura

El dictamen de **Grok 4.6** ha sido el catalizador necesario para formalizar la frontera entre **el análisis macroeconómico de convicción** y **la ingeniería de ejecución en mesa de dinero**.

La versión 3.0 del Motor GI no renuncia a su esencia soberana Top-Down ni a la elegancia del modelo ADC+ATR; por el contrario, los dota de una **armadura determinista**: un contrato de datos estricto, setups sin ambigüedades, protección de fricción en CFDs y una gestión rigurosa del ciclo de vida del trade.

*Agradecemos a la auditoría externa por su rigor técnico. El estándar institucional no se negocia; se codifica y se ejecuta.*

---
*Fin del Documento de Respuesta de Arquitectura.*
