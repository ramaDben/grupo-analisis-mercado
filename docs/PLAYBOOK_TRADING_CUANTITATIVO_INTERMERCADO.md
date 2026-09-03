# Playbook Maestro de Trading Cuantitativo Intermercado
**Grupo de Análisis de Mercado — Dirección de Trading**  
*Versión*: 2.0.0 | *Hash Configuración*: [`config/playbook_config.yaml`](../config/playbook_config.yaml)

---

## 1. Fundamento y Filosofía Cuantitativa

Este Playbook establece el **Manual de Operaciones Cuantitativo y Determinista** del Desk de Inversiones. Su propósito es fusionar el análisis macroeconómico intermercado con la microestructura técnica en MetaTrader 5 (MT5), apoyándose en **13 investigaciones empíricas institucionales de arbitraje, momentum y gestión de volatilidad**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITECTURA DE 5 CAPAS                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. INGESTA OFICIAL      ► data central/ (FRED, BCCh, BCE, BoE, COMEX, Fiscal Data)      │
│ 2. PRECIOS OHLC         ► MT5 + yfinance -> ATR_14(H1), ATR_20(D1), EMAs, Donchian_50   │
│ 3. CONMUTADOR RÉGIMEN   ► Máquina de Estados R0-R4 con Precedencia e Histéresis         │
│ 4. MATRIZ DE PERMISOS   ► Sesgo Direccional [-2, +2], Setups Permitidos y Prohibidos    │
│ 5. SIZING & RISK ENGINE ► Volatility Targeting: Lote = (Capital * R%) / (1.5*ATR * Tick)│
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> **Adopción de Parámetros Institucionales**:
> Los parámetros operativos (multiplicadores de ATR, bandas de filtro y ponderadores de volatilidad) son adoptados formalmente de la literatura cuantitativa institucional (*Man AHL, CFM, AQR, MIT, Harvard, Banco Central de Chile*), sujetos a calibración continua *walk-forward* sobre datos propios.

---

## 2. Máquina de Estados Determinista (Regímenes R0 – R4)

Para eliminar la discrecionalidad y evitar el parpadeo (*whipsaws*) por lecturas marginales de los drivers, el régimen macroeconómico global se gobierna por una **Máquina de Estados Finita con Jerarquía de Precedencia e Histéresis Temporal**.

### A. Jerarquía de Precedencia
Ante señales mixtas o divergencias entre mercados, el motor aplica la regla de dominancia por severidad de riesgo de cola:

$$\mathcal{R}_3 \text{ (Estanflación / Shock Geopolítico)} \succ \mathcal{R}_1 \text{ (Inflación / Cost-Push)} \succ \mathcal{R}_4 \text{ (Recesión / Bull Steepener)} \succ \mathcal{R}_2 \text{ (Goldilocks)} \succ \mathcal{R}_0 \text{ (Calma / Rango)}$$

```
                               ┌──────────────────────────────────────────────┐
                               │             EVALUACIÓN DIARIA (D1)           │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                       ¿Shock Petróleo (|Δ%Oil| ≥ 3.5%) Y Tensión en Tasas?
                                       │
                      ┌────────────────┴────────────────┐
                     SÍ                                 NO
                      │                                 │
                      ▼                                 ▼
             [R3: ESTANFLACIÓN]         ¿Breakeven (T10YIE) sube ≥ 10 bps Y Curva Plana?
                                                        │
                                       ┌────────────────┴────────────────┐
                                      SÍ                                 NO
                                       │                                 │
                                       ▼                                 ▼
                             [R1: SHOCK INFLACIÓN]        ¿Curva Invertida / Bull Steepener Y Cobre < -2.5%?
                                                                         │
                                                        ┌────────────────┴────────────────┐
                                                       SÍ                                 NO
                                                        │                                 │
                                                        ▼                                 ▼
                                              [R4: RECESIÓN / VUELO]       ¿Cobre ≥ +1.5% Y Tasas Estables?
                                                                                          │
                                                                         ┌────────────────┴────────────────┐
                                                                        SÍ                                 NO
                                                                         │                                 │
                                                                         ▼                                 ▼
                                                                 [R2: GOLDILOCKS]                 [R0: CALMA / RANGO]
```

### B. Umbrales Cuantitativos y Condiciones de Transición

| Código | Régimen Macroeconómico | Condición Matemática de Activación | Drivers en `data central/` |
| :--- | :--- | :--- | :--- |
| **$\mathcal{R}_3$** | **Estanflación / Turbulencia Geopolítica** | $\max(|\Delta\%\text{WTI}_{5\text{D}}|, |\Delta\%\text{Brent}_{5\text{D}}|) \ge 3.5\% \ \land \ (\Delta y^{10\text{Y}}_{5\text{D}} \ge 10\text{ bps} \ \lor \ \Delta \text{DFII10}_{5\text{D}} \ge 8\text{ bps})$ | Petróleo en rally, tasas del Tesoro al alza, aversión al riesgo global (*Kilian, 2009*). |
| **$\mathcal{R}_1$** | **Shock Inflacionario / Cost-Push** | $\Delta \text{T10YIE}_{5\text{D}} \ge 10\text{ bps} \ \land \ (\text{Spread}_{2s10s} \le 0.20\% \ \lor \ \Delta y^{10\text{Y}}_{5\text{D}} > 5\text{ bps})$ | Expectativas de inflación del mercado desancladas con aplanamiento de curva (*Neville et al., 2021*). |
| **$\mathcal{R}_4$** | **Recesión / Vuelo a la Calidad** | $(\text{Spread}_{2s10s} < 0.0\% \ \lor \ \text{Bull Steepener}) \ \land \ \Delta\%\text{Cobre}_{5\text{D}} \le -2.5\%$ | $\text{Bull Steepener} \equiv (\Delta \text{DGS2}_{5\text{D}} \le -15\text{ bps} \ \land \ \Delta \text{Spread}_{2s10s} \ge +10\text{ bps})$. Cobre colapsa (*Estrella-Mishkin*). |
| **$\mathcal{R}_2$** | **Expansión Sólida / Goldilocks** | $\Delta\%\text{Cobre}_{5\text{D}} \ge +1.5\% \ \land \ |\Delta y^{10\text{Y}}_{5\text{D}}| \le 6\text{ bps} \ \land \ \Delta \text{DFII10} \le 0$ | Cobre en expansión, tasas del Tesoro y rendimientos reales estables (*Bridgewater All Weather*). |
| **$\mathcal{R}_0$** | **Calma / Rango / Absorción** | No se satisface ningún umbral de shock ($\Delta \text{Drivers}$ en banda muerta) | Variables macro en equilibrio dinámico (*Brock et al., 1992*). |

### C. Filtro de Histéresis y Regla de Shock Extremo
1. **Histéresis Estándar**: Una transición de régimen $\mathcal{R}_{\text{previo}} \to \mathcal{R}_{\text{candidato}}$ solo se confirma y pasa a estado activo si las condiciones se mantienen durante **2 lecturas consecutivas (días D1)**.
2. **Override por Evento de Cola (> 150%)**: Si la magnitud del shock excede el **150% del umbral base** (ej. Petróleo $\ge +5.25\%$, Tasa 10Y $\ge +15\text{ bps}$, Cobre $\le -3.75\%$), el sistema **conmuta instantáneamente en la 1ª lectura**, protegiendo el capital ante cisnes negros.

---

## 3. Índice Matemático de Confianza del Modelo

La credibilidad del sesgo emitido por el motor se audita mediante la función de calidad y frescura:

$$\text{Confianza}_t = 100 \times \left( 0.40 \cdot \mathcal{S}_{\text{frescura}} + 0.35 \cdot \mathcal{S}_{\text{antigüedad}} + 0.25 \cdot \mathcal{S}_{\text{cobertura}} \right)$$

Donde:
* $\mathcal{S}_{\text{frescura}} = \frac{N_{\text{drivers no stale}}}{N_{\text{drivers requeridos}}}$ (debe ser $1.0$ en operación normal).
* $\mathcal{S}_{\text{antigüedad}} = \exp\left( -\frac{\text{Horas desde el driver más antiguo}}{48.0} \right)$ (decaimiento exponencial con vida media de 48 horas).
* $\mathcal{S}_{\text{cobertura}} = \frac{\text{Vectores disponibles del activo}}{\text{Vectores teóricos del modelo}}$.

> [!IMPORTANT]
> **Umbral operativo: 65 %.** Bajo esa cifra el activo con ficha **no se comunica**, y el
> escáner informa el motivo. No es una preferencia calibrada a gusto: es el piso algebraico
> de la norma que este mismo párrafo escribe. Si $\mathcal{S}_{\text{frescura}} = 1.0$ y
> $\mathcal{S}_{\text{cobertura}} = 1.0$ (la condición que aquí se llama *operación normal*),
> el puntaje ya arrastra $0.40 + 0.25 = 0.65$ antes de que la antigüedad aporte nada.
>
> Por lo tanto **bajo 65 % es aritméticamente imposible que ambas valgan 1,0**. Un puntaje
> inferior no significa "datos algo viejos": significa que **falta un driver o está roto**.
> Es una identidad, no un juicio de tolerancia.
>
> **Un umbral de 80 % habría sido un error.** El techo real de la escala es ~89 %, porque el
> campo `fecha` de cada driver no trae hora y se parsea como medianoche UTC, así que
> $\mathcal{S}_{\text{antigüedad}}$ nunca aporta sus 35 puntos completos:
>
> | Escenario medido el 2026-09-02 | Frescura | Cobertura | Antigüedad | Total |
> |---|---:|---:|---:|---:|
> | Clave de la TPM rota y petróleo detenido 8 días | 83,3 % | 83,3 % | 1,3 % | **54,6 %** |
> | Solo corrigiendo la clave de la TPM | 100 % | 100 % | 1,3 % | **65,4 %** |
> | Todo al día desde el terminal correcto | 100 % | 100 % | 38,9 % | **77,5 %** |
> | Techo aritmético (todo fechado hoy) | 100 % | 100 % | 68,4 % | **88,9 %** |
>
> El parámetro vive en `confidence_weights.umbral_minimo_pct`, dentro del YAML que este
> Playbook hashea, para que un cambio de criterio quede registrado en el `config_hash` del
> snapshot. Lo aplican `screener_gi.gate_confianza` (quinto gate, y corre **antes** del gate
> del Playbook: si el modelo no ve, sus setups permitidos y prohibidos tampoco son de fiar) y
> `pipeline_datos --estado`, que **importa** la constante en vez de copiarla.
>
> **Solo alcanza a los 5 activos con ficha.** La confianza mide los drivers macro que
> alimentan el régimen, y el régimen solo entra al sesgo de esos cinco. Los otros 33 del
> catálogo técnico se puntúan con técnica y calendario, sin insumo macro.
>
> **Ausencia de dato = bloqueo.** Un snapshot que no declara su confianza no pasa: asumir que
> alcanza sería la puerta de atrás que el umbral existe para cerrar.

---

## 4. Fichas Operativas por Activo

### 💵 Activo 1: Dólar / Peso Chileno (`USD/CLP`)
* **Modelo Econométrico**: Caputo, Núñez & Valdés (BCCh DT 434) + Carreño & Cox (BCCh DT 722) + Menkhoff et al. (2012).
* **Vectores de Transmisión**:
  1. Cobre COMEX (`HG`): Elasticidad $\beta \approx -0.48$. Un shock alcista en Cobre presiona a la baja el tipo de cambio.
  2. Spread de Tasas ($\text{TPM} - \text{FedFunds}$): Diferencial de *carry trade*.
  3. Posición Neta Forward de Extranjeros: Flujo offshore en T-2.
* **Reglas Operativas**:
  * **En Régimen $\mathcal{R}_0$ (Calma)**: Operativa de rango en M15/H1. Comprar en soporte $S_1$ / Vender en resistencia $R_1$. TP al nivel opuesto del canal.
  * **En Régimen $\mathcal{R}_3 / \mathcal{R}_4$ (Turbulencia)**: Prohibido operar contratendencia. Activar exclusivamente *Breakouts* direccionales en H1 sobre canales Donchian de 50 períodos con banda $b = 0.3 \times \text{ATR}_{14}$.
* **Gestión de Riesgo**: Stop Loss obligatorio a **$1.5 \times \text{ATR}_{14}(\text{H1})$** (intradía) o **$2.5 \times \text{ATR}_{20}(\text{D1})$** (swing).

---

### 🪙 Activo 2: Oro Spot (`XAU/USD`)
* **Modelo Econométrico**: World Gold Council (GRAM) + Erb & Harvey (NBER, 2013) + Baur & Lucey (2010).
* **Vectores de Transmisión**:
  1. Rendimiento Real TIPS 10Y (`DFII10`): Driver dominante de costo de oportunidad ($\beta \approx -1.5$).
  2. Compensación por Inflación (`T10YIE`): Cobertura de pérdida de poder adquisitivo.
  3. Petróleo y Tensión Geopolítica: Prima de riesgo y convexidad positiva.
* **Reglas Operativas**:
  * **En Régimen $\mathcal{R}_3 / \mathcal{R}_1$**: Sesgo **Fuerte Alcista (+1.80 a +2.00)**. **Prohibido abrir posiciones cortas (Short)** aun con RSI sobrecomprado en 80.
  * **Gatillos Permitidos**: Compras en retroceso (*Pullbacks*) hacia EMA 20 en H1 o roturas del canal Donchian de 50 en H1.
  * **Salida Asimétrica**: Prohibido Take Profit rígido; salida obligatoria por *Chandelier Trailing Stop*:

$$\text{Stop}_{\text{largo}} = \max(\text{High}_{22}) - 3.0 \times \text{ATR}_{14}(\text{H1}) \qquad \text{Stop}_{\text{corto}} = \min(\text{Low}_{22}) + 3.0 \times \text{ATR}_{14}(\text{H1})$$

    El stop es **monótono** (*ratchet*): solo se mueve a favor de la posición, nunca en contra.

---

### 🛢️ Activos 3 y 4: Petróleo Crudo (`WTI` y `BRENT`)
* **Modelo Econométrico**: Lutz Kilian (American Economic Review, 2009) + Neville et al. (2021).
* **Descomposición Estructural**:
  1. **Shock de Demanda Agregada** (Cobre sube + Renta Variable sube + Crudo sube): Seguir tendencia alcista con posición completa.
  2. **Shock Precautorio / Geopolítico** (Bolsas caen + Oro sube + Crudo explota): Operar con apalancamiento reducido al 50% y Trailing Stop ceñido a $2.0 \times \text{ATR}$.
  3. **Shock de Oferta Transitorio** (Titular OPEP sin respaldo en fletes ni cobre): *Fade the spike* en resistencias Donchian.

> [!IMPORTANT]
> **El discriminador operativo es el Cobre.** El hallazgo que da título a Kilian (2009) es que
> los tres shocks **tienen efectos distintos**, así que el trato de riesgo no puede ser uno solo.
> El motor los separa con el cobre, que es el proxy del propio paper para la demanda global de
> commodities industriales y el que esta ficha ya nombra en su caso 3:
>
> | Condición medida | Shock identificado | Trailing | Apalancamiento |
> |---|---|---:|---:|
> | Crudo al alza **y** $\Delta\%\text{Cobre}_{5\text{D}} \ge +1.5\%$ | Demanda agregada (caso 1) | $3.0 \times \text{ATR}$ | 100 % |
> | Crudo al alza **sin** confirmación del cobre | Precautorio u oferta (casos 2 y 3) | $2.0 \times \text{ATR}$ | **50 %** |
>
> El umbral de confirmación **no es nuevo**: es `copper_goldilocks_pct_5d`, el mismo que la
> máquina de estados usa para declarar "cobre en expansión" en $\mathcal{R}_2$. Un segundo
> umbral de cobre sería el mismo error que tener dos fórmulas de ATR.
>
> **Corregido el 2026-09-02.** El config tenía una sola constante de trailing (3,0) y la
> justificación emitida decía *"Shock Precautorio/Demanda"*, juntando en una barra las dos
> cosas que el paper existe para separar. Ese mismo día el caso se presentó real: crudo
> **+9,03 %** con el cobre en **+0,19 %**, bolsas a la baja y Oro en fuerte alcista. Las tres
> patas del shock precautorio, y el sistema lo estaba tratando como tendencia con posición
> completa.
>
> **Nota sobre la EMA 16.** El motor emitía `PULLBACK_EMA16_H1` como setup permitido del crudo
> en shock. Esa media no aparece en este Playbook —que usa EMA 20 y EMA 50— ni la devuelve
> `get_asset_levels`, que expone 20, 50 y 100: era una instrucción que nadie podía ejecutar.
> Se reemplazó por `PULLBACK_EMA20_H1`, el gatillo de retroceso que este documento sí define.

---

### 💻 Activo 5: Nasdaq 100 (`US100`)
* **Modelo Econométrico**: Asness et al. (AQR, 2013) + Brock et al. (1992) + Lo et al. (MIT, 2000).
* **Vectores de Transmisión**:
  1. Tasa Nominal 10Y (`DGS10`): Tasa de descuento de flujos de caja futuros. $\text{DGS10} > 4.70\%$ comprime múltiplos P/E.
  2. Pendiente Curva 2s10s: Disponibilidad de crédito bancario.
* **Reglas Operativas**:
  * Si $\text{DGS10}$ sube aceleradamente: Prohibido *Buy the Dip* sin confirmación de reversión sobre EMA 50.
  * Si Tasas se estabilizan y Cobre sube ($\mathcal{R}_2$): Operar compras tendenciales sobre EMA 20 en H1.

---

## 5. Protocolo de Gestión de Riesgo y Dimensionamiento Institucional

Siguiendo el principio de **Volatility Targeting** (*Harvey et al., Duke / Man AHL, 2018*), el riesgo monetario se mantiene constante por trade desvinculándose de lotajes fijos:

$$L_t = \frac{\text{Capital de la Cuenta} \times \text{Riesgo\%}}{\text{Distancia Stop Loss en Puntos} \times \text{Valor del Punto por Lote}}$$

Donde:
* $\text{Distancia Stop Loss (Intradía H1)} = 1.5 \times \text{ATR}_{14}(\text{H1})$
* $\text{Distancia Stop Loss (Swing D1)} = 2.5 \times \text{ATR}_{20}(\text{D1})$
* $\text{Chandelier Trailing (posición sostenida)} = \max(\text{High}_{22}) - 3.0 \times \text{ATR}_{14}(\text{H1})$

> [!IMPORTANT]
> **El Chandelier son dos parámetros, no uno.** El múltiplo $k = 3.0$ y la ventana $N = 22$
> son el par calibrado de LeBeau y no se separan. Fijar solo el múltiplo deja el nivel
> indeterminado, y la indeterminación no es teórica: medido el 2026-09-02 sobre el Oro, el
> mismo activo el mismo día daba **vigente** con $N=22$ (nivel 4.312,40) e **invalidado** con
> $N=50$ (nivel 4.400,90 sobre un precio de 4.370,35).
>
> **Calibración *walk-forward* (2026-09-02)** sobre las series H1 propias de los 5 activos con
> ficha, 9.800 barras cada una, entrando en cruce sobre EMA 50 y arrastrando con *ratchet*:
>
> | $N$ | Nivel publicable | Distancia mediana | **Distancia p10** | Mediana sostenida |
> |---:|---:|---:|---:|---:|
> | 14 | 95,2 % | 2,02 ATR | +0,52 | 14,0 h |
> | **22** | **92,6 %** | **1,86 ATR** | **+0,22** | **9,7 h** |
> | 33 | 89,6 % | 1,68 ATR | −0,03 ❌ | 4,7 h |
> | 50 | 82,6 % | 1,39 ATR | −0,56 ❌ | 1,0 h |
>
> El criterio de descarte es el **percentil 10 de la distancia**: en $N=33$ y $N=50$ se vuelve
> negativo, es decir el "stop" queda *sobre* el precio en un estado alcista normal. Eso no es
> un stop ceñido, es un nivel incoherente. La banda viable es $\{14, 22\}$ y se adopta el valor
> de la literatura, que cae dentro de ella.
>
> **Contra la intuición**: un lookback más largo **aprieta** el stop, no lo suelta, porque
> $\max(\text{High}_N)$ crece con $N$ y el nivel resultante sube. Por eso $N=50$ liquida la
> posición en una hora mediana.
* **Regla Anti-Colapso**: Si la volatilidad del activo se duplica ($\text{ATR}$ se duplica), el lotaje $L_t$ se reduce automáticamente al 50%, manteniendo la pérdida máxima en dólares estrictamente acotada al 1.0% del capital.

---

## 6. Protocolo de Blackout por Calendario Económico

El sistema consulta dinámicamente [`data central/DATA AGENDA/calendario_{YYYY}.json`](../data%20central/DATA%20AGENDA/):
1. **Ventana de Bloqueo (Blackout Window)**: 15 minutos antes y 15 minutos después de anuncios de **Decisión de Tasas de la Fed (FOMC)**, **NFP (Non-Farm Payrolls)**, **IPC USA** o **Reunión de Política Monetaria del BCCh (RPM)**.
2. **Acción Automática**: Prohibida la apertura de nuevas órdenes a mercado; las órdenes límite pendientes cerca del precio spot deben ser canceladas para evitar *slippage* institucional.

---

## 7. Referencias Académicas de la Biblioteca

1. **Murphy, John J. (1991)**. *Intermarket Technical Analysis*. John Wiley & Sons.
2. **Bridgewater Associates (2012)**. *The All Weather Story*. Global Macro Research.
3. **Kritzman, M., Page, S., & Turkington, D. (2012)**. *Regime Shifts: Implications for Dynamic Asset Allocation*. Financial Analysts Journal, 68(3), 22–39.
4. **Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012)**. *Time Series Momentum*. Journal of Financial Economics, 104(2), 228–250.
5. **Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013)**. *Value and Momentum Everywhere*. The Journal of Finance, 68(3), 929–985.
6. **Harvey, C. R., Hoyle, E., Korgaonkar, R., Rattray, S., Sargaison, M., & Van Hemert, O. (2018)**. *The Impact of Volatility Targeting*. The Journal of Portfolio Management, 45(1), 14–33.
7. **Lempérière, Y., Deremble, C., Seager, P., Potters, M., & Bouchaud, J. P. (2014)**. *Two Centuries of Trend Following*. Journal of Investment Strategies, 3(3), 41–61.
8. **Lo, A. W., Mamaysky, H., & Wang, J. (2000)**. *Foundations of Technical Analysis*. The Journal of Finance, 55(4), 1705–1765.
9. **Brock, W., Lakonishok, J., & LeBaron, B. (1992)**. *Simple Technical Trading Rules*. The Journal of Finance, 47(5), 1731–1764.
10. **Erb, C. B., & Harvey, C. R. (2013)**. *The Golden Dilemma*. Financial Analysts Journal, 69(4), 10–42.
11. **Estrella, A., & Mishkin, F. S. (1998)**. *The Yield Curve as a Predictor of U.S. Recessions*. Review of Economics and Statistics, 80(1), 45–61.
12. **Kilian, L. (2009)**. *Not All Oil Price Shocks Are Alike*. American Economic Review, 99(3), 1053–1069.
13. **Caputo, R., Núñez, M., & Valdés, R. (2007)**. *Análisis del Tipo de Cambio en la Práctica*. Banco Central de Chile, DT N° 434.
14. **Carreño, G., & Cox, P. (2014)**. *Carry Trade y Turbulencias Cambiarias*. Banco Central de Chile, DT N° 722.
15. **Menkhoff, L., Sarno, L., Schmeling, M., & Schrimpf, A. (2012)**. *Carry Trades and Global FX Volatility*. The Journal of Finance, 67(2), 681–718.
16. **LeBeau, C., & Lucas, D. W. (1992)**. *Technical Traders Guide to Computer Analysis of the Futures Markets*. McGraw-Hill. — Origen del *Chandelier Exit*; fuente del par $(N = 22,\ k = 3.0)$ adoptado en §5.
