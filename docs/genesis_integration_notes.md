# Notas de Integración y Análisis de Arquitectura: Motor Genesis (Fase 0)

> **Documento de Evidencia Técnica y Mapeo de Interfaces**  
> **Repositorio Genesis**: `git@github.com:ramaDben/genesis.git` (commit local verificado)  
> **Repositorio Desk**: `git@github.com:ramaDben/grupo-analisis-mercado.git`  
> **Fecha**: 2026-08-20  
> **Propósito**: Responder de forma empírica y respaldada por código las 10 preguntas de integración requeridas por el Brief V2 antes de la construcción del puente `genesis_bridge`.

---

## 1. Firma exacta y ciclo de vida de `genesis/strategy/contract.py`

### Definición del Contrato (`genesis.strategy.contract`)
* **Versión del Contrato**: `CONFIG_VERSION = "genesis-strategy/1"`
* **Dirección**: `Direction(StrEnum)` con valores `"long"` y `"short"`.
* **Intención de Entrada**: `@dataclass(frozen=True, slots=True)`
  ```python
  @dataclass(frozen=True, slots=True)
  class EntryIntent:
      direction: Direction
      sizing_hint: float
      candidate_id: str
      config_version: str
  ```
* **Protocolo de Candidato**:
  ```python
  @runtime_checkable
  class StrategyCandidate(Protocol):
      candidate_id: str
      def on_bar(self, bar: AnnotatedBar) -> list[EntryIntent]: ...
  ```
* **Protocolo de Niveles de Riesgo** (`genesis.backtest.simulator`):
  ```python
  @runtime_checkable
  class RiskLevelsProvider(Protocol):
      def risk_levels(self, intent: EntryIntent) -> tuple[float, float]: ...
  ```
  *(Satisfecho mediante duck typing en la misma clase del candidato, sin acoplamiento circular de imports).*

### Ciclo de Vida de Simulación
1. `iter_bars(frame, symbol, profile)` genera secuencias forward-only de `AnnotatedBar` (barras ya cerradas con `timestamp_utc`, `trading_day`, `session_open_utc`, `session_close_utc`, `in_session`).
2. `Simulator._process_bar(bar)`:
   - Avanza el reloj `SimulationClock` (lanza `LookaheadError` si el tiempo retrocede).
   - Resuelve fills de salida de posiciones vivas contra SL/TP (usando ticks o fallback intrabar).
   - Evalúa límites de breach de riesgo diario/total en línea.
   - Aplica cierre forzado de sesión al alcanzar `session_close_utc`.
   - Si no está agotada la cuenta, invoca `candidate.on_bar(bar)` -> recibe `list[EntryIntent]`.
   - Para cada intención, invoca `candidate.risk_levels(intent)` -> pasa por `inspector.inspect(...)` (filtro de noticias, R:R y tamaño de lote). Si es autorizado, se abre la posición y se registra `FillRecord` en el `Ledger`.

---

## 2. Schema real de salida de `genesis/validation/verdict.py`

### Taxonomía de Veredictos (`VerdictKind`)
```python
class VerdictKind(StrEnum):
    GO = "go"
    GO_ENSEMBLE = "go-ensemble"
    GO_PARCIAL = "go-parcial"
    NO_GO = "no-go"
```

### Dataclass Principal (`VerdictResult`)
```python
@dataclass(frozen=True, slots=True)
class VerdictResult:
    verdict: VerdictKind
    winning_candidate_id: str | None
    candidate_summaries: Mapping[str, CandidateGateSummary]
    t1_dsr: float | None
    t1_dsr_pre_deflation: float | None
    n_candidatos_torneo: int
    n_trials_deflactado: int | None
    ensemble: EnsembleResult | None
    economics_confirmed: bool
    no_go_iteration_used: bool = False
```

### Gates Evaluados por Candidato (`CandidateGateSummary` y `SymbolGateOutcome`)
* **Gates G (por símbolo)**:
  * **G1**: $\text{trades\_oos\_total} \ge 300$
  * **G2**: $\text{WFE} \ge 0.5$ (Walk-Forward Efficiency)
  * **G3**: $\text{Profit Factor} \ge 1.3$
  * **G4**: $\text{DSR} \ge 0.95$ (Deflated Sharpe Ratio)
  * **G5**: $\text{PBO} < 0.25$ (Probability of Backtest Overfitting via CSCV)
  * **G6**: $\text{MaxDD}_{95\%} \le 50\%$ del límite de pérdida
  * **G7**: Probabilidad de breach a 12 meses $< 5\%$
  * **G8**: Sin acantilados de sensibilidad y degradación máxima $< 30\%$
  * **G9**: $\text{Profit Factor con estrés de costos } 1.5\times \ge 1.15$
* **Gates C (Consistencia de Universo)**:
  * **C1**: Al menos el 60% de los símbolos del universo pasan todos los gates G.
  * **C2**: Los símbolos no pasantes mantienen $\text{Profit Factor} \ge 0.8$.
* **Gates P (Prop Challenge via `prop_sim`)**:
  * **P1**: $P(\text{pass}) \ge 50\%$
  * **P2**: Intentos esperados $\le 2.0$
  * **P3**: Probabilidad de breach diario mensual $< 2\%$
  * **P4**: Supervivencia mediana fondeada $\ge 6$ meses
  * **P5**: Payout percentil 25 a 12 meses $> \$0$
  * **P6**: Cero breaches duros registrados en los ledgers OOS

### Serialización Oficial
`write_verdict_artifacts(result, output_dir, ...)` serializa:
1. `manifest.json`: JSON determinista byte a byte (`sort_keys=True`) con todos los hashes criptográficos y resultados.
2. `tearsheet.md`: Reporte ejecutivo en Markdown puro.

---

## 3. API y semántica de `dsr_pbo.py`, `wfa.py`, `purged_cv.py`, `montecarlo.py`, `prop_sim.py`

| Módulo | Función Principal | Semántica y Algoritmo |
|---|---|---|
| `wfa.py` | `run_wfa(...) -> WfaResult` | Walk-forward rolling IS/OOS. Grid IS exhaustivo (27 combos de ejecución / 9 de señal). Selección por DSR-IS. Cosido cronológico de ledgers OOS (`oos_ledger_cosido`). |
| `dsr_pbo.py` | `build_signal_trial_matrix(...)`<br>`run_dsr_pbo(...) -> DsrPboResult` | Reconstruye matriz DSR-IS. DSR normativo sobre trades OOS. PBO mediante Combinatorial Symmetric Cross-Validation (CSCV) con combinatoria pura $C(S, S/2)$ sobre bloques contiguos. |
| `purged_cv.py` | `run_purged_cv(...) -> PurgedCvResult` | K-Fold Cross Validation con purgado y embargo de trades correlacionados en tiempo (diagnóstico informativo para manifest). |
| `montecarlo.py` | `run_montecarlo_symbol(...)`<br>`run_montecarlo_portfolio(...)` | Block bootstrap circular de series de P&L para calcular $\text{MaxDD}_{95\%}$ y probabilidad de breach a 12 meses. |
| `sensitivity.py` | `run_sensitivity(...) -> SensitivityResult` | Perturbación de parámetros ($\pm 10\%$, $\pm 20\%$) y estrés de costos ($1.5\times$). |
| `prop_sim.py` | `run_prop_sim(...) -> PropSimResult` | Simulación Monte Carlo del challenge Prop Firm (fases de evaluación, consistencia, días mínimos, límites de pérdida y retiros quincenales). |

---

## 4. Formato esperado por `mt5_export.py` y compatibilidad con el store canónico

* **Almacenamiento en Genesis**: `RawParquetStore` organiza los archivos como:
  ```text
  data/raw/<SYMBOL>/<granularity>/<YYYY>/<YYYY-MM>.parquet
  data/raw/<SYMBOL>/<granularity>/<YYYY>/<YYYY-MM>.parquet.meta.json
  data/raw/_manifest.json
  ```
* **Columnas Canónicas**: `["timestamp", "open", "high", "low", "close", "tick_volume", "bid", "ask", "last"]` con `timestamp` en UTC.
* **Store Canónico del Desk**: `data central/DATA PRECIOS OHLC/<SYMBOL>_<TF>.json`.
* **Compatibilidad**: El adaptador `data_adapter.py` convierte los JSONs del desk a DataFrames y estructuras `RawParquetStore` de Genesis calculando hashes SHA-256 idénticos sobre el contenido tabular normalizado.

---

## 5. Soporte de temporalidades (M15 / H1 / D1) y resampleo

* Genesis opera fundamentalmente sobre secuencias de barras M1 (`AnnotatedBar`).
* Para evaluar candidatos formulados en H1 o M15 (como `S3_BREAKOUT_DONCHIAN_H1`):
  - El candidato mantiene buffers de agregación intrabar forward-only (ej. acumula barras de 60 minutos para cerrar velas H1) o bien se sintetiza el frame con resolución adecuada garantizando que nunca se observe el cierre de una vela antes de su tiempo de confirmación.
  - Se garantiza que `LookaheadError` se dispare si se consulta información futura.

---

## 6. Forma correcta de incluir costos, fills y slippage

* **Configuración Obligatoria**: `CostsConfig(spread_points, slippage_points, commission, swap_long, swap_short, swap_rollover_day)`.
* **Regla R40**: "Sin costos no hay reporte". Si `costs_config` es nulo o cero por omisión, el simulador y los gates fallan inmediatamente (`BacktestConfigError`).
* **Mecánica de Fills**:
  - Entrada: primer tick disponible o `bar.open`, aplicando spread y slippage monetizados vía `tick_value`.
  - Salida: tick a tick si hay tick coverage; o fallback geométrico de peor caso (si en la misma barra se tocan SL y TP, el SL tiene prioridad adversa).

---

## 7. Entry point oficial para ejecutar un torneo

El torneo se ejecuta invocando:
```python
verdict_result = run_verdict(
    candidates={"S3": candidate_bundle},
    starting_balance=10000.0,
    firm_profile=firm_profile,
    risk_profile=risk_profile,
    prop_economics_profile=prop_economics_profile,
    ensemble_prop_sim_config=prop_sim_config,
    no_go_iteration_used=False
)
manifest_path, tearsheet_path = write_verdict_artifacts(
    verdict_result, output_dir=Path("out/verdicts"), ...
)
```

---

## 8. Semántica real del ledger y conteo de trials fallidos

* En WFA (`wfa.py`), cada ventana evalúa exhaustivamente las combinaciones de la grilla ($N_{\text{signal}} = 9$, $N_{\text{exec}} = 27$).
* Si una combinación genera $< 10$ trades en IS, recibe DSR-IS $= -\infty$, pero **se contabiliza obligatoriamente** en `n_trials_signal_total` y `n_trials_execution_total`.
* En la deflación de torneo T1:
  $$N_{\text{trials\_deflactado}} = N_{\text{trials\_signal\_ganador}} + (N_{\text{candidatos}} - 1) + [1 \text{ si hubo NO\_GO}]$$
* Ningún trial negativo o fallido se borra ni se oculta del denominador.

---

## 9. Representación del régimen Point-in-Time sin leakage

* `regime_filter.py` consume `macro_bias_history.jsonl` (archivo append-only).
* Para cualquier barra en timestamp $t$, se consulta estrictamente:
  $$\text{Snapshot}(t) = \max \{ \text{row} \mid \text{row.as\_of\_utc} \le t \}$$
* Si no existe ningún snapshot previo a $t$, el filtro actúa en modo **fail-closed** y no emite intenciones de trading.
* Queda prohibido usar el snapshot $T_{\text{actual}}$ para retroceder en el tiempo.

---

## 10. Condiciones para emitir un veredicto reproducible

1. Registro de **hashes SHA-256 obligatorios**:
   - `catalogue_hash` (SHA-256 de `propuesta_catalogo_estrategias_ssrn.md`).
   - `dataset_hash` (SHA-256 del contenido normalizado de precios).
   - `regime_snapshot_id` / `regime_hash`.
   - `firm_profile_hash` y `risk_profile_hash`.
   - `git_commit` del repositorio Genesis y del Desk.
2. **Semillas deterministas**: Seeds explícitos inyectados en Monte Carlo y PropSim.
3. **Certificado en tres fases**:
   - Fase 1: `GATE_ESTADISTICO_APROBADO` (`operational_status: "BLOQUEADO"`).
   - Fase 2: `VALIDADO_GENESIS` (`human_review: "APPROVED"`, `operational_status: "PAPER_ONLY"`).
   - Fase 3: `APROBADO_LIMITADO` (`operational_status: "LIVE_LIMITED"`).
