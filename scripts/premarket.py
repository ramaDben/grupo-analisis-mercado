#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
premarket.py
Generador CLI de Briefings Pre-Market y Calculadora de Lotaje Institucional (Playbook V2).
Consume de forma estrictamente de solo lectura el módulo bias_reader.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Bootstrap sys.path para importar market_data_mcp
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from market_data_mcp.bias_reader import cargar_macro_bias, calcular_lote_riesgo, VALID_SYMBOLS


def render_briefing_activo(activo_data: dict, metricas: dict, regimen: dict, capital: float, riesgo_pct: float) -> str:
    """Renderiza una ficha ejecutiva de pre-market para un activo específico."""
    nombre = activo_data.get("nombre", "")
    tipo = activo_data.get("tipo", "")
    sesgo = activo_data.get("sesgo_score", 0.0)
    etiqueta = activo_data.get("sesgo_etiqueta", "")
    riesgo_params = activo_data.get("parametros_riesgo", {})
    spot = riesgo_params.get("precio_spot", 0.0)
    sl_h1 = riesgo_params.get("distancia_sl_h1_puntos", 0.0)
    sl_d1 = riesgo_params.get("distancia_sl_d1_puntos", 0.0)
    atr_h1 = riesgo_params.get("atr_h1", 0.0)
    atr_d1 = riesgo_params.get("atr_d1", 0.0)
    tp_tipo = riesgo_params.get("take_profit_tipo", "")
    trailing = riesgo_params.get("trailing_stop_mult_atr")

    # Cálculo de lote
    symbol_id = activo_data.get("symbol_id", "USDCLP")
    lotes, riesgo_usd, tick_val = calcular_lote_riesgo(capital, riesgo_pct, sl_h1, symbol_id, spot)

    lines = []
    lines.append(f"📌 ACTIVO: {nombre} ({tipo})")
    lines.append(f"  • Precio Spot Actual : ${spot:,.2f}")
    lines.append(f"  • Sesgo Cuantitativo : {sesgo:+.2f} -> {etiqueta}")
    lines.append(f"  • Volatilidad ATR    : H1 = {atr_h1:.2f} pts | D1 = {atr_d1:.2f} pts")
    lines.append(f"  • Stop Loss Sugerido : H1 (1.5x ATR) = {sl_h1:.2f} pts | D1 (2.5x ATR) = {sl_d1:.2f} pts")
    lines.append(f"  • Estrategia Salida  : {tp_tipo}" + (f" (Trailing Chandelier: {trailing}x ATR)" if trailing else ""))
    lines.append(f"  • Dimensionamiento   : Capital ${capital:,.2f} USD @ {riesgo_pct:.1f}% -> Riesgo ${riesgo_usd:,.2f} USD")
    lines.append(f"  👉 TAMAÑO DE LOTE    : {lotes} Lotes (Tick Value: ${tick_val:.2f} USD/pt)")

    permitidos = activo_data.get("setups_permitidos", [])
    prohibidos = activo_data.get("setups_prohibidos", [])
    lines.append(f"  🟢 SETUPS PERMITIDOS : {', '.join(permitidos)}")
    lines.append(f"  🔴 SETUPS PROHIBIDOS : {', '.join(prohibidos)}")

    justif = activo_data.get("justificacion_vectores", [])
    if justif:
        lines.append("  🔍 DRIVERS / TESIS:")
        for j in justif:
            lines.append(f"     - {j}")

    return "\n".join(lines)


def ejecutar_premarket(symbol: str = "USDCLP", all_assets: bool = False, capital: float = 10000.0, risk: float = 1.0, json_output: bool = False) -> None:
    """Ejecuta la consulta y presentación del briefing pre-market."""
    target_sym = "ALL" if all_assets else symbol.upper().strip()
    data = cargar_macro_bias(symbol=target_sym)

    if "error" in data:
        if json_output:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("\n" + "=" * 75)
            print(f"❌ ERROR AL GENERAR PRE-MARKET: [{data.get('error')}]")
            print(f"   {data.get('message')}")
            if "antiguedad_horas" in data:
                print(f"   Antigüedad: {data.get('antiguedad_horas')}h | Umbral: {data.get('umbral_horas')}h")
            print("=" * 75)
        sys.exit(1)

    if json_output:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    regimen = data.get("regimen_macro_global", {})
    metricas = data.get("metricas_clave", {})
    confianza = data.get("confianza_general", {})
    as_of = data.get("as_of_utc", "")
    config_hash = data.get("config_hash", "")

    print("\n" + "=" * 80)
    print("🌅 BRIEFING PRE-MARKET CUANTITATIVO — GRUPO DE ANÁLISIS DE MERCADO")
    print(f"⏰ As Of UTC: {as_of} | Config Hash: {config_hash}")
    print("=" * 80)
    print(f"🏛️  RÉGIMEN MACRO GLOBAL : [{regimen.get('codigo')}] -> {regimen.get('nombre')}")
    print(f"📌 Estado Histéresis    : {'CONFIRMADO' if regimen.get('confirmado_por_historesis') else 'EN OBSERVACIÓN'} ({regimen.get('lecturas_consecutivas')} lecturas)")
    print(f"🎯 Confianza Modelo     : {confianza.get('confianza_total_pct', 0.0):.1f}% (Frescura: {confianza.get('score_frescura_pct', 0):.0f}%, Antigüedad: {confianza.get('score_antiguedad_pct', 0):.1f}%)")
    print("-" * 80)
    print("📊 DRIVERS MACRO VIVOS:")
    print(f"  • Curva 2s10s: {metricas.get('spread_2s10s_pct', 0):+.2f}% | TIPS Real 10Y: {metricas.get('tasa_real_tips10y_pct', 0):.2f}% | Breakeven 10Y: {metricas.get('breakeven_inflacion_10y_pct', 0):.2f}%")
    print(f"  • Cobre COMEX: ${metricas.get('cobre_spot_comex', 0):.2f} ({metricas.get('cobre_variacion_5d_pct', 0):+.1f}% 5D) | Petróleo Max 5D: {metricas.get('petroleo_shock_max_5d_pct', 0):+.1f}%")
    print("=" * 80)

    if all_assets:
        activos = data.get("activos", {})
        for s_id, a_data in activos.items():
            a_data_copy = dict(a_data)
            a_data_copy["symbol_id"] = s_id
            print("\n" + render_briefing_activo(a_data_copy, metricas, regimen, capital, risk))
            print("-" * 80)
    else:
        activo = data.get("activo", {})
        activo_copy = dict(activo)
        activo_copy["symbol_id"] = target_sym
        print("\n" + render_briefing_activo(activo_copy, metricas, regimen, capital, risk))
        print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Briefing Pre-Market Cuantitativo Intermercado")
    parser.add_argument("--symbol", type=str, default="USDCLP", help="Símbolo a consultar (USDCLP, XAUUSD, WTI, BRENT, US100)")
    parser.add_argument("--all", action="store_true", help="Generar briefing de todos los activos monitoreados")
    parser.add_argument("--capital", type=float, default=10000.0, help="Capital de la cuenta en USD (default: 10,000)")
    parser.add_argument("--risk", type=float, default=1.0, help="Porcentaje de riesgo por operacion (default: 1.0 por ciento)")
    parser.add_argument("--json", action="store_true", help="Emitir salida en formato JSON puro")
    args = parser.parse_args()

    ejecutar_premarket(symbol=args.symbol, all_assets=args.all, capital=args.capital, risk=args.risk, json_output=args.json)
