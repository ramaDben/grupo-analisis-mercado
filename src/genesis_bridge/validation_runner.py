"""
genesis_bridge.validation_runner
Orquestador del pipeline de validación estadística institucional entre el catálogo y Genesis.
Ejecuta backtests con costos reales, evaluación de gates, ledger append-only y emisión de certificados.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

# Asegurar import de genesis
GENESIS_SRC = Path("C:/Users/bbrav/genesis/src")
if GENESIS_SRC.exists() and str(GENESIS_SRC) not in sys.path:
    sys.path.insert(0, str(GENESIS_SRC))

from genesis.backtest.ledger import FillRecord
from genesis.backtest.metrics import _running_equity_deltas, ledger_metrics_summary
from genesis.backtest.risk_profile import load_risk_profile
from genesis.backtest.simulator import Simulator
from genesis.strategy.inspector import InspectorFunnelConfig
from genesis.validation._dsr import deflated_sharpe_ratio
from genesis_bridge.candidate_factory import create_candidate_from_spec
from genesis_bridge.certificate import (
    GenesisCertificate,
    issue_statistical_gate_certificate,
)
from genesis_bridge.data_adapter import (
    get_costs_config,
    get_firm_profile,
    get_symbol_figure,
    load_ohlc_as_dataframe,
    to_genesis_symbol,
)
from genesis_bridge.errors import PromotionGateError
from genesis_bridge.hypothesis_loader import load_catalogue, load_hypothesis
from genesis_bridge.regime_filter import RegimeHistoryManager
from genesis_bridge.search_plan import AppendOnlyTrialLedger, build_search_plan


def is_full_git_sha(commit: str) -> bool:
    """Verifica si una cadena es un commit hash SHA-1/SHA-256 completo de Git."""
    return (len(commit) in (40, 64)) and all(c in "0123456789abcdefABCDEF" for c in commit)


@dataclass(frozen=True, slots=True)
class ValidationExecutionResult:
    """Resultado estructurado de la ejecución del pipeline de validación."""
    trial_id: str
    status: str
    operational_status: str
    n_trials_declared: int
    n_trials_executed: int
    trades_is: int
    trades_oos: int
    sharpe_is: float
    sharpe_oos: float
    dsr: float | None
    pbo: float | None
    max_drawdown_oos: float
    profit_factor_oos: float
    winning_params: Mapping[str, Any]
    failure_reason: str | None = None
    certificate: GenesisCertificate | None = None
    certificate_path: Path | None = None


def split_is_oos_dataframe(df: Any, is_ratio: float = 0.70) -> tuple[Any, Any]:
    """Divide un DataFrame OHLC cronológicamente en In-Sample (IS) y Out-Of-Sample (OOS)."""
    n = len(df)
    split_idx = int(n * is_ratio)
    df_is = df.iloc[:split_idx].reset_index(drop=True)
    df_oos = df.iloc[split_idx:].reset_index(drop=True)
    return df_is, df_oos


def execute_validation_pipeline(
    trial_id: str,
    output_cert_dir: Path | str = "data/validation_certificates",
    ledger_path: Path | str = "data/validation_ledger/trial_ledger.jsonl",
    genesis_commit: str = "0123456789abcdef0123456789abcdef01234567",
    run_full_grid: bool = True,
    max_trials_to_run: int = 1,
) -> ValidationExecutionResult:
    """Núcleo de ejecución del pipeline de validación institucional fail-closed."""
    # 1. Validar commit inmutable obligatorio
    if not is_full_git_sha(genesis_commit):
        return ValidationExecutionResult(
            trial_id=trial_id,
            status="VALIDATION_INCOMPLETE",
            operational_status="BLOQUEADO",
            n_trials_declared=0,
            n_trials_executed=0,
            trades_is=0,
            trades_oos=0,
            sharpe_is=0.0,
            sharpe_oos=0.0,
            dsr=None,
            pbo=None,
            max_drawdown_oos=0.0,
            profit_factor_oos=0.0,
            winning_params={},
            failure_reason="Genesis commit must be a full 40-character immutable SHA",
        )

    # 2. Parsear setup_id y símbolo desde el trial_id
    parts = trial_id.split("__")
    setup_id = parts[0] if len(parts) >= 2 else "S3_BREAKOUT_DONCHIAN_H1"
    symbol = parts[1] if len(parts) >= 2 else "XAUUSD"

    # 3. Cargar especificación de la hipótesis y catálogo
    spec, catalogue_hash = load_hypothesis(setup_id)
    canonical_symbol = to_genesis_symbol(symbol)
    _, matrix_ssot, _ = load_catalogue()

    # 4. Cargar datos OHLC limpios y su hash criptográfico
    df_ohlc, data_hash = load_ohlc_as_dataframe(symbol, timeframe="H1")
    data_snapshot_id = f"SNAP-{symbol}-H1-{data_hash[:8]}"

    # 5. Obtener perfil de costos y figuras del activo
    costs = get_costs_config(symbol)
    figure = get_symbol_figure(symbol)
    firm_profile = get_firm_profile()
    reference_balance = 10000.0
    risk_profile = load_risk_profile()
    funnel_config = InspectorFunnelConfig(min_rr=1.0, min_lot=0.01, max_lot=50.0)

    # 6. Cargar y aplicar régimen Point-in-Time REAL sobre las barras
    regime_mgr = RegimeHistoryManager()
    regime_snapshot_id = f"REG-{regime_mgr.history_hash[:8]}" if regime_mgr.history_hash else "REG-DEFAULT"

    df_filtered = regime_mgr.apply_point_in_time_filter(df_ohlc, setup_id, symbol, matrix_ssot)

    # 7. Separar datos explícitamente en IS (70%) y OOS (30%)
    df_is, df_oos = split_is_oos_dataframe(df_filtered, is_ratio=0.70)

    # 8. Espacio de búsqueda y plan de ensayos
    search_plan = build_search_plan(spec, symbol)
    n_trials_declared = search_plan.n_trials_total

    # Regla: Si no se corre la grilla completa, es un smoke test que no puede certificar
    if not run_full_grid:
        return ValidationExecutionResult(
            trial_id=trial_id,
            status="VALIDATION_INCOMPLETE",
            operational_status="BLOQUEADO",
            n_trials_declared=n_trials_declared,
            n_trials_executed=max_trials_to_run,
            trades_is=0,
            trades_oos=0,
            sharpe_is=0.0,
            sharpe_oos=0.0,
            dsr=None,
            pbo=None,
            max_drawdown_oos=0.0,
            profit_factor_oos=0.0,
            winning_params={},
            failure_reason="Smoke test cannot issue statistical certificate. Full grid required.",
        )

    trial_ledger = AppendOnlyTrialLedger(ledger_path)
    trials_to_execute = list(search_plan.trials)
    n_trials_executed = len(trials_to_execute)

    best_trial_params: Mapping[str, Any] = trials_to_execute[0].params if trials_to_execute else {}
    best_sharpe_is = -999.0
    best_is_trades = 0

    # 9. Ejecutar fase In-Sample (IS) sobre todos los trials de la grilla
    for trial_cfg in trials_to_execute:
        cand_is = create_candidate_from_spec(
            spec=spec,
            figure=figure,
            reference_balance=reference_balance,
            params=trial_cfg.params,
        )
        sim_is = Simulator(
            candidate=cand_is,
            symbol=canonical_symbol,
            firm_profile=firm_profile,
            risk_profile=risk_profile,
            figure=figure,
            funnel_config=funnel_config,
            costs_config=costs,
            news_events=(),
            tick_store=None,
            starting_balance=reference_balance,
            dataset_hash=data_hash,
        )
        ledger_is = sim_is.run(df_is)
        summary_is = ledger_metrics_summary(ledger_is)
        exit_fills_is = [e.payload for e in ledger_is.entries if isinstance(e.payload, FillRecord) and e.payload.is_exit]
        trades_is_count = len(exit_fills_is)

        # Asentar cada trial en el ledger inmutable
        trial_ledger.record_trial(
            trial_id=trial_id,
            trial_index=trial_cfg.trial_index,
            params=dict(trial_cfg.params),
            success=True,
            metrics={
                "sharpe_is": float(summary_is.sharpe_pointwise),
                "profit_factor_is": float(summary_is.profit_factor) if summary_is.profit_factor != float("inf") else 0.0,
                "trades_is": trades_is_count,
            },
            commit_hash=genesis_commit,
            dataset_hash=data_hash,
        )

        if float(summary_is.sharpe_pointwise) > best_sharpe_is:
            best_sharpe_is = float(summary_is.sharpe_pointwise)
            best_trial_params = trial_cfg.params
            best_is_trades = trades_is_count

    # 10. Ejecutar fase Out-Of-Sample (OOS) congelada con el ganador IS
    cand_oos = create_candidate_from_spec(
        spec=spec,
        figure=figure,
        reference_balance=reference_balance,
        params=best_trial_params,
    )
    sim_oos = Simulator(
        candidate=cand_oos,
        symbol=canonical_symbol,
        firm_profile=firm_profile,
        risk_profile=risk_profile,
        figure=figure,
        funnel_config=funnel_config,
        costs_config=costs,
        news_events=(),
        tick_store=None,
        starting_balance=reference_balance,
        dataset_hash=data_hash,
    )
    ledger_oos = sim_oos.run(df_oos)
    summary_oos = ledger_metrics_summary(ledger_oos)
    exit_fills_oos = [e.payload for e in ledger_oos.entries if isinstance(e.payload, FillRecord) and e.payload.is_exit]
    trades_oos = len(exit_fills_oos)  # CONTEO OOS ESTRICTAMENTE REAL (SIN PADDING)

    # Reconstrucción de deltas de retornos por trade en OOS
    running_oos = _running_equity_deltas(ledger_oos)
    exit_deltas_oos = [delta for fill, delta in running_oos if fill.is_exit]
    trade_returns_oos = [delta / reference_balance for delta in exit_deltas_oos]

    # Cálculo matemático de DSR (Bailey & López de Prado, 2014)
    if len(trade_returns_oos) >= 2:
        dsr_real = float(deflated_sharpe_ratio(trade_returns_oos, n_trials=n_trials_declared))
    else:
        dsr_real = 0.0

    sharpe_oos = float(summary_oos.sharpe_pointwise)
    max_dd_oos = float(summary_oos.max_drawdown) / reference_balance if summary_oos.max_drawdown > 0 else 0.0
    pf_oos = float(summary_oos.profit_factor) if summary_oos.profit_factor != float("inf") else 0.0

    # PBO: Si no hay matriz CSCV multi-ventana completa, pbo es None (NUNCA constante)
    pbo_real = None

    metrics_summary = {
        "dsr": dsr_real,
        "pbo": pbo_real,
        "sharpe_is": best_sharpe_is if best_sharpe_is != -999.0 else 0.0,
        "sharpe_oos": sharpe_oos,
        "max_drawdown_oos": max_dd_oos,
        "trades_is": best_is_trades,
        "trades_oos": trades_oos,
        "profit_factor_oos": pf_oos,
        "wfe": (sharpe_oos / best_sharpe_is) if (best_sharpe_is > 0 and sharpe_oos > 0) else 0.0,
    }

    # REGLA FAIL-CLOSED: Si trades_oos < 30, rechazar
    min_trades_oos = 30
    if trades_oos < min_trades_oos:
        reason = f"Insufficient OOS sample: {trades_oos} trades; minimum is {min_trades_oos}"
        trial_ledger.record_trial(
            trial_id=trial_id,
            trial_index=0,
            params=dict(best_trial_params),
            success=False,
            metrics=metrics_summary,
            failure_reason=reason,
            commit_hash=genesis_commit,
            dataset_hash=data_hash,
        )
        return ValidationExecutionResult(
            trial_id=trial_id,
            status="REJECTED",
            operational_status="BLOQUEADO",
            n_trials_declared=n_trials_declared,
            n_trials_executed=n_trials_executed,
            trades_is=best_is_trades,
            trades_oos=trades_oos,
            sharpe_is=best_sharpe_is,
            sharpe_oos=sharpe_oos,
            dsr=dsr_real,
            pbo=pbo_real,
            max_drawdown_oos=max_dd_oos,
            profit_factor_oos=pf_oos,
            winning_params=best_trial_params,
            failure_reason=reason,
        )

    # REGLA FAIL-CLOSED: Si PBO no fue calculado con CSCV real, la validación queda incompleta
    if pbo_real is None:
        reason = "PBO could not be calculated without CSCV multi-window trial matrix"
        return ValidationExecutionResult(
            trial_id=trial_id,
            status="VALIDATION_INCOMPLETE",
            operational_status="BLOQUEADO",
            n_trials_declared=n_trials_declared,
            n_trials_executed=n_trials_executed,
            trades_is=best_is_trades,
            trades_oos=trades_oos,
            sharpe_is=best_sharpe_is,
            sharpe_oos=sharpe_oos,
            dsr=dsr_real,
            pbo=pbo_real,
            max_drawdown_oos=max_dd_oos,
            profit_factor_oos=pf_oos,
            winning_params=best_trial_params,
            failure_reason=reason,
        )

    # 11. Emisión del Certificado Inmutable Hito 1 sólo si supera todos los gates
    cert = issue_statistical_gate_certificate(
        trial_id=trial_id,
        genesis_commit=genesis_commit,
        catalogue_hash=catalogue_hash,
        strategy_code_version=spec.strategy_code_version,
        data_snapshot_id=data_snapshot_id,
        data_hash=data_hash,
        regime_snapshot_id=regime_snapshot_id,
        config_hash=search_plan.search_plan_hash[:16],
        n_trials_total=n_trials_declared,
        metrics=metrics_summary,
    )

    out_dir = Path(output_cert_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cert_file = out_dir / f"{cert.certificate_id}.json"
    with open(cert_file, "w", encoding="utf-8") as f:
        json.dump(cert.to_dict(), f, indent=2, ensure_ascii=False)

    return ValidationExecutionResult(
        trial_id=trial_id,
        status="GATE_ESTADISTICO_APROBADO",
        operational_status="BLOQUEADO",
        n_trials_declared=n_trials_declared,
        n_trials_executed=n_trials_executed,
        trades_is=best_is_trades,
        trades_oos=trades_oos,
        sharpe_is=best_sharpe_is,
        sharpe_oos=sharpe_oos,
        dsr=dsr_real,
        pbo=pbo_real,
        max_drawdown_oos=max_dd_oos,
        profit_factor_oos=pf_oos,
        winning_params=best_trial_params,
        certificate=cert,
        certificate_path=cert_file,
    )


def run_single_trial_validation(
    trial_id: str,
    output_cert_dir: Path | str = "data/validation_certificates",
    ledger_path: Path | str = "data/validation_ledger/trial_ledger.jsonl",
    genesis_commit: str = "0123456789abcdef0123456789abcdef01234567",
    run_full_grid: bool = True,
    max_trials_to_run: int = 1,
) -> tuple[GenesisCertificate, Path]:
    """Wrapper que lanza PromotionGateError si la validación falla o no está completa."""
    res = execute_validation_pipeline(
        trial_id=trial_id,
        output_cert_dir=output_cert_dir,
        ledger_path=ledger_path,
        genesis_commit=genesis_commit,
        run_full_grid=run_full_grid,
        max_trials_to_run=max_trials_to_run,
    )

    if res.status != "GATE_ESTADISTICO_APROBADO" or res.certificate is None or res.certificate_path is None:
        raise PromotionGateError(res.failure_reason or f"Validation failed with status {res.status}")

    return res.certificate, res.certificate_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Genesis Validation Runner CLI")
    parser.add_argument("--trial", default="S3_BREAKOUT_DONCHIAN_H1__XAUUSD__v1", help="Trial ID a validar")
    parser.add_argument("--out", default="data/validation_certificates", help="Directorio de salida para certificados")
    parser.add_argument("--commit", default="0123456789abcdef0123456789abcdef01234567", help="Git Commit SHA inmutable")
    args = parser.parse_args()

    print(f"[INFO] Iniciando validación institucional Genesis para {args.trial}...")
    res = execute_validation_pipeline(trial_id=args.trial, output_cert_dir=args.out, genesis_commit=args.commit)
    print(f"[STATUS] Veredicto: {res.status} | operational_status: {res.operational_status}")
    print(f"[METRICS] Trades IS: {res.trades_is} | Trades OOS: {res.trades_oos} | Sharpe OOS: {res.sharpe_oos:.4f} | DSR: {res.dsr} | PBO: {res.pbo}")
    if res.failure_reason:
        print(f"[REASON] {res.failure_reason}")
    if res.certificate_path:
        print(f"[CERTIFICATE] Generado: {res.certificate_path}")


if __name__ == "__main__":
    main()
