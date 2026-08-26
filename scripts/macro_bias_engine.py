#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
macro_bias_engine.py
Motor Cuantitativo de Sesgo Intermercado y Conmutador de Regímenes (Playbook V2).
Consume datos de data central/, clasifica el régimen determinista con histéresis y
emite la matriz de permisos técnicos y dimensionamiento por ATR para MT5.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "playbook_config.yaml"

DATA_CENTRAL = BASE_DIR / "data central"
USA_DATA_FILE = DATA_CENTRAL / "DATA USA" / "raw" / "treasury_fed_data.json"
CHILE_DATA_FILE = DATA_CENTRAL / "DATA CHILE" / "raw" / "bcch_macro_data.json"
COMMODITIES_FILE = DATA_CENTRAL / "DATA ORO Y COMMODITIES" / "raw" / "commodities_data.json"
PRICES_SUMMARY_FILE = DATA_CENTRAL / "DATA PRECIOS OHLC" / "latest_prices_summary.json"
PRICES_DIR = DATA_CENTRAL / "DATA PRECIOS OHLC"
AGENDA_DIR = DATA_CENTRAL / "DATA AGENDA"

OUTPUT_DIR = DATA_CENTRAL / "DATA DRIVERS USDCLP"
OUTPUT_FILE = OUTPUT_DIR / "macro_bias_output.json"


def calcular_hash_config(config_path: Path) -> str:
    """Genera hash SHA256 de la configuración para trazabilidad y auditoría."""
    if not config_path.exists():
        return "CONFIG_NOT_FOUND"
    with open(config_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def cargar_config() -> dict:
    """Carga la configuración YAML maestra."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _obtener_serie_cronologica(historico: dict) -> list[tuple[str, float]]:
    """Ordena un diccionario {fecha_iso: valor} cronológicamente."""
    if not historico:
        return []
    items = []
    for k, v in historico.items():
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            try:
                items.append((k, float(v)))
            except (ValueError, TypeError):
                pass
    items.sort(key=lambda x: x[0])
    return items


def _delta_n_dias(serie_cronologica: list[tuple[str, float]], n_dias: int = 5) -> tuple[float | None, float | None, str | None]:
    """Calcula el cambio absoluto (o porcentual) en los últimos N registros disponibles."""
    if not serie_cronologica or len(serie_cronologica) < 2:
        return None, None, None
    ultimo_val = serie_cronologica[-1][1]
    ultima_fecha = serie_cronologica[-1][0]
    idx_prev = max(0, len(serie_cronologica) - 1 - n_dias)
    prev_val = serie_cronologica[idx_prev][1]

    diff_abs = ultimo_val - prev_val
    diff_pct = ((ultimo_val - prev_val) / prev_val) * 100.0 if prev_val != 0 else 0.0
    return diff_abs, diff_pct, ultima_fecha


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


def calcular_confianza(
    drivers_info: list[dict], cfg: dict, ahora: datetime | None = None
) -> tuple[float, float, float, float]:
    """Calcula el índice de confianza matemático auditable.

    `ahora` se inyecta para poder testear la ponderación sin depender del reloj
    de la máquina, igual que `cargar_calendario` con su filtro de hoy. El factor
    de antigüedad se mide contra el momento actual, así que un test con fechas
    fijas no comprueba una fórmula: comprueba qué día se ejecutó. El de esta
    función pasaba cuando se escribió y fallaba desde una semana después, con las
    mismas entradas y la misma fórmula.
    """
    cw = cfg["confidence_weights"]
    total = len(drivers_info)
    if total == 0:
        return 50.0, 0.0, 0.0, 0.0

    # 1. Frescura
    frescos = sum(1 for d in drivers_info if d.get("status") == "OK" and not d.get("is_stale", False))
    s_frescura = frescos / float(total)

    # 2. Antigüedad (basada en el driver más antiguo)
    ahora = ahora or datetime.now(timezone.utc)
    max_horas = 0.0
    for d in drivers_info:
        fecha_str = d.get("fecha")
        if fecha_str:
            try:
                # Soporta YYYY-MM-DD y ISO
                if len(fecha_str) == 10:
                    dt = datetime.strptime(fecha_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                horas = (ahora - dt).total_seconds() / 3600.0
                if horas > max_horas:
                    max_horas = horas
            except Exception:
                pass
    halflife = cw.get("age_decay_halflife_hours", 48.0)
    s_antiguedad = math.exp(-max_horas / halflife)

    # 3. Cobertura
    cobertura_promedio = sum(d.get("cobertura", 1.0) for d in drivers_info) / float(total)
    s_cobertura = min(1.0, max(0.0, cobertura_promedio))

    confianza_pct = 100.0 * (
        cw["weight_freshness"] * s_frescura +
        cw["weight_age"] * s_antiguedad +
        cw["weight_coverage"] * s_cobertura
    )
    return round(confianza_pct, 1), round(s_frescura * 100, 1), round(s_antiguedad * 100, 1), round(s_cobertura * 100, 1)


def evaluar_activos(regimen_activo: str, drivers_data: dict, precios_summary: dict, cfg: dict) -> dict:
    """Evalúa para cada activo su sesgo direccional, setups permitidos/prohibidos y parámetros de riesgo."""
    rp = cfg["risk_parameters"]
    activos_res = {}

    # Drivers extraídos
    cobre_spot = drivers_data.get("copper_spot", 6.45)
    cobre_pct_5d = drivers_data.get("copper_pct_5d", 0.0)
    tpm_chile = drivers_data.get("tpm_chile", 4.50)
    fed_funds = drivers_data.get("fed_funds", 3.63)
    spread_tasas = tpm_chile - fed_funds
    fwd_ext = drivers_data.get("fwd_extranjeros", 4450.0)
    tips_10y = drivers_data.get("tips_10y", 2.35)
    breakeven_10y = drivers_data.get("breakeven_10y", 2.34)
    dgs10 = drivers_data.get("dgs10", 4.65)
    oil_shock = drivers_data.get("oil_max_pct_5d", 0.0)

    for asset_cfg in cfg["assets_monitored"]:
        asset_id = asset_cfg["id"]
        precio_info = precios_summary.get("activos", {}).get(asset_id, {})
        h1_info = precio_info.get("H1") or {}
        d1_info = precio_info.get("D1") or {}

        spot = h1_info.get("close") or d1_info.get("close") or 0.0
        atr_h1 = h1_info.get("atr_14") or (spot * 0.008)
        atr_d1 = d1_info.get("atr_20") or (spot * 0.018)

        sl_dist_h1 = round(rp["stop_loss_mult_intraday"] * atr_h1, asset_cfg["digits"])
        sl_dist_d1 = round(rp["stop_loss_mult_daily"] * atr_d1, asset_cfg["digits"])

        # Lógica de Sesgo y Permisos por Activo
        if asset_id == "USDCLP":
            # Si Cobre está fuerte y FWD no residentes elevado -> Rango / Rebote en soportes
            if cobre_spot > 6.0 and spread_tasas < 1.5:
                sesgo_score = 0.10
                sesgo_etiqueta = "NEUTRAL / RANGO (912 - 925)"
                setups_permitidos = ["FADE_SUPPORT_RESISTANCE_M15", "MEAN_REVERSION_RSI_H1"]
                setups_prohibidos = ["BREAKOUT_CHASE_LONG", "GRID_SIN_STOP"]
                tp_tipo = "NIVEL_OPUESTO_CANAL"
                trailing_mult = None
                justificacion = [
                    f"Cobre en ${cobre_spot:.2f} USD/lb frena alzas violentas (Elasticidad beta=-0.48)",
                    f"Diferencial de tasas comprimido ({spread_tasas:+.2f}%) limita caídas estructurales",
                    f"Posición forward no residentes compradora (+{fwd_ext:.0f}M USD) actúa como soporte"
                ]
            else:
                sesgo_score = -0.50
                sesgo_etiqueta = "BAJISTA MODERADO"
                setups_permitidos = ["PULLBACK_SHORT_EMA20", "BREAKDOWN_DONCHIAN_H1"]
                setups_prohibidos = ["LONG_SWING_FADE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = ["Presión vendedora por términos de intercambio favorables"]

        elif asset_id == "XAUUSD":
            # Oro favorecido en R3 (Estanflación), R1 (Inflación) o cuando TIPS caen
            if regimen_activo in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"] or tips_10y < 2.20:
                sesgo_score = 1.80
                sesgo_etiqueta = "FUERTE ALCISTA"
                setups_permitidos = ["PULLBACK_EMA20_H1", "BREAKOUT_DONCHIAN_50_H1"]
                setups_prohibidos = ["SHORT_FADE_OVERBOUGHT", "VENTA_CONTRA_TENDENCIA"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Tasa Real TIPS 10Y (DFII10 en {tips_10y:.2f}%) y Breakeven ({breakeven_10y:.2f}%) impulsan demanda refugio",
                    f"Régimen macro {regimen_activo} otorga convexidad positiva y asimetría de retorno",
                    "Prohibido vender en sobrecompra según regla de Moskowitz-Harvey"
                ]
            else:
                sesgo_score = 0.40
                sesgo_etiqueta = "ALCISTA MODERADO"
                setups_permitidos = ["PULLBACK_EMA50_H1", "BREAKOUT_DONCHIAN_H1"]
                setups_prohibidos = ["SHORT_AGRESIVO"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = ["Estructura de mediano plazo constructiva con tasas reales estables"]

        elif asset_id in ["WTI", "BRENT"]:
            if regimen_activo == "R3_ESTANFLACION_SHOCK" or oil_shock > 2.0:
                sesgo_score = 1.50
                sesgo_etiqueta = "ALCISTA POR SHOCK"
                setups_permitidos = ["BREAKOUT_VOLATILITY_H1", "PULLBACK_EMA16_H1"]
                setups_prohibidos = ["FADE_TOP_RESISTANCE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Impulso de 5 días en crudo (+{oil_shock:.1f}%) bajo modelo Kilian (Shock Precautorio/Demanda)",
                    "Uso obligatorio de Trailing Stop por ATR para captura de colas derechas"
                ]
            else:
                sesgo_score = 0.0
                sesgo_etiqueta = "NEUTRAL / CONSOLIDACIÓN"
                setups_permitidos = ["RANGE_DONCHIAN_FADE"]
                setups_prohibidos = ["BREAKOUT_CHASE"]
                tp_tipo = "NIVEL_OPUESTO_CANAL"
                trailing_mult = None
                justificacion = ["Mercado energético en rango sin desbalances de inventario"]

        elif asset_id == "US100":
            if dgs10 > 4.70 or regimen_activo in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"]:
                sesgo_score = -1.20
                sesgo_etiqueta = "BAJISTA / PRESIÓN EN MÚLTIPLOS"
                setups_permitidos = ["SELL_PULLBACK_EMA50_H1", "BREAKDOWN_DONCHIAN_H1"]
                setups_prohibidos = ["BUY_THE_DIP_AGGRESSIVE", "COMPRA_SIN_CONFIRMACION"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Rendimiento UST 10Y en {dgs10:.2f}% comprime múltiplos de valuación en tecnológicas",
                    "Régimen de tasas elevadas penaliza activos de alta duración"
                ]
            else:
                sesgo_score = 0.80
                sesgo_etiqueta = "ALCISTA / EXPANSION"
                setups_permitidos = ["PULLBACK_EMA20_H1", "BREAKOUT_DONCHIAN_H1"]
                setups_prohibidos = ["SHORT_FADE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = ["Tasas 10Y estables y liquidez favorable para renta variable"]
        else:
            sesgo_score = 0.0
            sesgo_etiqueta = "NEUTRAL"
            setups_permitidos = ["RANGE_TRADING"]
            setups_prohibidos = []
            tp_tipo = "NIVEL_OPUESTO_CANAL"
            trailing_mult = None
            justificacion = ["Sin drivers directos"]

        activos_res[asset_id] = {
            "nombre": asset_cfg["nombre"],
            "tipo": asset_cfg["tipo"],
            "sesgo_score": sesgo_score,
            "sesgo_etiqueta": sesgo_etiqueta,
            "setups_permitidos": setups_permitidos,
            "setups_prohibidos": setups_prohibidos,
            "parametros_riesgo": {
                "precio_spot": spot,
                "atr_h1": round(atr_h1, asset_cfg["digits"]),
                "atr_d1": round(atr_d1, asset_cfg["digits"]),
                "stop_loss_mult_intraday": rp["stop_loss_mult_intraday"],
                "distancia_sl_h1_puntos": sl_dist_h1,
                "stop_loss_mult_daily": rp["stop_loss_mult_daily"],
                "distancia_sl_d1_puntos": sl_dist_d1,
                "take_profit_tipo": tp_tipo,
                "trailing_stop_mult_atr": trailing_mult
            },
            "justificacion_vectores": justificacion
        }

    return activos_res


def ejecutar_motor_sesgo(verbose: bool = True) -> dict:
    """Ejecuta el cálculo completo del Playbook Cuantitativo Intermercado."""
    cfg = cargar_config()
    config_hash = calcular_hash_config(CONFIG_PATH)

    # 1. Cargar datos macro de data central/
    usa_data = {}
    if USA_DATA_FILE.exists():
        with open(USA_DATA_FILE, "r", encoding="utf-8") as f:
            usa_data = json.load(f)

    chile_data = {}
    if CHILE_DATA_FILE.exists():
        with open(CHILE_DATA_FILE, "r", encoding="utf-8") as f:
            chile_data = json.load(f)

    comm_data = {}
    if COMMODITIES_FILE.exists():
        with open(COMMODITIES_FILE, "r", encoding="utf-8") as f:
            comm_data = json.load(f)

    precios_summary = {}
    if PRICES_SUMMARY_FILE.exists():
        with open(PRICES_SUMMARY_FILE, "r", encoding="utf-8") as f:
            precios_summary = json.load(f)

    # Cargar estado previo de histéresis
    estado_previo = {}
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                estado_previo = json.load(f)
        except Exception:
            estado_previo = {}

    # 2. Extracción de series cronológicas y deltas
    yields = usa_data.get("curva_rendimientos_yields", {})
    dgs2_cron = _obtener_serie_cronologica(yields.get("DGS2", {}).get("historico", {}))
    dgs10_cron = _obtener_serie_cronologica(yields.get("DGS10", {}).get("historico", {}))
    dfii10_cron = _obtener_serie_cronologica(yields.get("DFII10", {}).get("historico", {}))
    t10yie_cron = _obtener_serie_cronologica(yields.get("T10YIE", {}).get("historico", {}))
    dff_cron = _obtener_serie_cronologica(yields.get("DFF", {}).get("historico", {}))

    comm_series = comm_data.get("commodities") or comm_data.get("series") or {}
    wti_cron = _obtener_serie_cronologica(comm_series.get("PETROLEO_WTI", {}).get("historico", {}))
    brent_cron = _obtener_serie_cronologica(comm_series.get("PETROLEO_BRENT", {}).get("historico", {}))
    copper_cron = _obtener_serie_cronologica(comm_series.get("COBRE_COMEX", {}).get("historico", {}))

    # Deltas a 5 días
    dgs10_diff, _, dgs10_fecha = _delta_n_dias(dgs10_cron, 5)
    dgs2_diff, _, _ = _delta_n_dias(dgs2_cron, 5)
    tips_diff, _, _ = _delta_n_dias(dfii10_cron, 5)
    breakeven_diff, _, _ = _delta_n_dias(t10yie_cron, 5)

    _, wti_pct_5d, _ = _delta_n_dias(wti_cron, 5)
    _, brent_pct_5d, _ = _delta_n_dias(brent_cron, 5)
    _, copper_pct_5d, _ = _delta_n_dias(copper_cron, 5)

    oil_max_pct = max(abs(wti_pct_5d or 0.0), abs(brent_pct_5d or 0.0))
    copper_pct_5d = copper_pct_5d or 0.0

    dgs10_actual = dgs10_cron[-1][1] if dgs10_cron else 4.65
    dgs2_actual = dgs2_cron[-1][1] if dgs2_cron else 4.19
    spread_2s10s_actual = dgs10_actual - dgs2_actual
    spread_2s10s_diff = (dgs10_diff or 0.0) - (dgs2_diff or 0.0)

    tips_actual = dfii10_cron[-1][1] if dfii10_cron else (dgs10_actual - 2.30)
    breakeven_actual = t10yie_cron[-1][1] if t10yie_cron else 2.34

    # Chile data
    chile_series = chile_data.get("series", {})
    tpm_cron = _obtener_serie_cronologica(chile_series.get("TPM_CHILE", {}).get("historico", {}))
    tpm_actual = tpm_cron[-1][1] if tpm_cron else 4.50
    fed_funds_actual = dff_cron[-1][1] if dff_cron else 3.63
    fwd_cron = _obtener_serie_cronologica(chile_series.get("POSICION_FORWARD_EXTRANJEROS", {}).get("historico", {}))
    fwd_actual = fwd_cron[-1][1] if fwd_cron else 4450.0

    copper_actual = copper_cron[-1][1] if copper_cron else 6.45

    deltas_payload = {
        "dgs10_actual": dgs10_actual,
        "dgs10_diff_5d": dgs10_diff,
        "dgs2_diff_5d": dgs2_diff,
        "spread_2s10s_actual": spread_2s10s_actual,
        "spread_2s10s_diff_5d": spread_2s10s_diff,
        "tips10y_diff_5d": tips_diff,
        "breakeven_diff_5d": breakeven_diff,
        "oil_max_pct_5d": oil_max_pct,
        "copper_pct_5d": copper_pct_5d,
        "copper_spot": copper_actual,
        "tpm_chile": tpm_actual,
        "fed_funds": fed_funds_actual,
        "fwd_extranjeros": fwd_actual,
        "tips_10y": tips_actual,
        "breakeven_10y": breakeven_actual,
        "dgs10": dgs10_actual
    }

    # 3. Evaluación de Régimen con Histéresis
    cand_cod, cand_nom, es_extremo, desc_cand = evaluar_regimen_candidato(deltas_payload, cfg)

    prev_reg = estado_previo.get("regimen_macro_global", {})
    prev_cod = prev_reg.get("codigo", "R0_CALMA_RANGO")
    prev_consec = prev_reg.get("lecturas_consecutivas", 1)

    req_confirm = cfg["regime_thresholds"]["hysteresis_required_confirmations"]

    if es_extremo:
        regimen_activo_cod = cand_cod
        regimen_activo_nom = cand_nom
        confirmado_hist = True
        consecutivas = 1
        desc_final = desc_cand + " [EVENTO EXTREMO: Conmutación Inmediata]"
    elif cand_cod == prev_cod:
        regimen_activo_cod = cand_cod
        regimen_activo_nom = cand_nom
        confirmado_hist = True
        consecutivas = prev_consec + 1
        desc_final = desc_cand
    else:
        # Candidato distinto del previo sin shock extremo -> Requiere 2 lecturas
        if prev_consec >= req_confirm:
            # Transición en evaluación
            regimen_activo_cod = prev_cod
            regimen_activo_nom = prev_reg.get("nombre", prev_cod)
            confirmado_hist = False
            consecutivas = 1
            desc_final = f"Régimen previo {prev_cod} activo. Nuevo candidato {cand_cod} en observación (1/{req_confirm})."
        else:
            regimen_activo_cod = cand_cod
            regimen_activo_nom = cand_nom
            confirmado_hist = True
            consecutivas = 1
            desc_final = desc_cand

    # 4. Cálculo de Confianza
    drivers_audit = [
        {"nombre": "DGS10", "fecha": dgs10_fecha, "status": yields.get("DGS10", {}).get("status", "OK"), "cobertura": 1.0},
        {"nombre": "DFII10", "fecha": dgs10_fecha, "status": yields.get("DFII10", {}).get("status", "OK"), "cobertura": 1.0},
        {"nombre": "T10YIE", "fecha": dgs10_fecha, "status": yields.get("T10YIE", {}).get("status", "OK"), "cobertura": 1.0},
        {"nombre": "TPM_CHILE", "fecha": dgs10_fecha, "status": chile_series.get("TPM_CHILE", {}).get("status", "OK"), "cobertura": 1.0},
        {"nombre": "COBRE", "fecha": dgs10_fecha, "status": comm_series.get("COBRE_COMEX", {}).get("status", "OK"), "cobertura": 1.0},
        {"nombre": "PETROLEO", "fecha": dgs10_fecha, "status": comm_series.get("PETROLEO_WTI", {}).get("status", "OK"), "cobertura": 1.0}
    ]
    conf_global, f_frescura, f_antiguedad, f_cobertura = calcular_confianza(drivers_audit, cfg)

    # 5. Evaluación por activo
    activos_evaluados = evaluar_activos(regimen_activo_cod, deltas_payload, precios_summary, cfg)

    # 6. Estructura de salida
    ahora_iso = datetime.now(timezone.utc).isoformat()
    resultado_final = {
        "schema_version": cfg.get("schema_version", "2.0.0"),
        "config_hash": config_hash,
        "as_of_utc": ahora_iso,
        "regimen_macro_global": {
            "codigo": regimen_activo_cod,
            "nombre": regimen_activo_nom,
            "confirmado_por_historesis": confirmado_hist,
            "lecturas_consecutivas": consecutivas,
            "descripcion": desc_final
        },
        "metricas_clave": {
            "spread_2s10s_pct": round(spread_2s10s_actual, 4),
            "tasa_real_tips10y_pct": round(tips_actual, 2),
            "breakeven_inflacion_10y_pct": round(breakeven_actual, 2),
            "spread_tasas_chile_fed_pct": round(tpm_actual - fed_funds_actual, 2),
            "cobre_spot_comex": round(copper_actual, 4),
            "cobre_variacion_5d_pct": round(copper_pct_5d, 2),
            "petroleo_shock_max_5d_pct": round(oil_max_pct, 2)
        },
        "confianza_general": {
            "confianza_total_pct": conf_global,
            "score_frescura_pct": f_frescura,
            "score_antiguedad_pct": f_antiguedad,
            "score_cobertura_pct": f_cobertura
        },
        "activos": activos_evaluados
    }

    # Guardar en JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=False)

    if verbose:
        imprimir_reporte_consola(resultado_final)

    return resultado_final


def imprimir_reporte_consola(data: dict) -> None:
    """Renderiza el reporte ejecutivo en consola para el Director de Trading."""
    reg = data["regimen_macro_global"]
    conf = data["confianza_general"]
    metricas = data["metricas_clave"]

    print("\n" + "=" * 80)
    print(f"📊 MOTOR DE SESGO CUANTITATIVO INTERMERCADO — PLAYBOOK V2 (v{data['schema_version']})")
    print(f"⏰ As Of UTC: {data['as_of_utc']} | Config Hash: {data['config_hash']}")
    print("=" * 80)
    print(f"🏛️  RÉGIMEN MACRO GLOBAL : [{reg['codigo']}] -> {reg['nombre']}")
    print(f"📌 Estado de Histéresis : {'CONFIRMADO' if reg['confirmado_por_historesis'] else 'EN EVALUACIÓN'} (Lecturas: {reg['lecturas_consecutivas']})")
    print(f"📝 Justificación       : {reg['descripcion']}")
    print(f"🎯 Confianza Modelo     : {conf['confianza_total_pct']}% (Frescura: {conf['score_frescura_pct']}%, Antigüedad: {conf['score_antiguedad_pct']}%, Cobertura: {conf['score_cobertura_pct']}%)")
    print("-" * 80)
    print("📈 DRIVERS CUANTITATIVOS:")
    print(f"  • Curva 2s10s: {metricas['spread_2s10s_pct']:+.2f}% | TIPS 10Y: {metricas['tasa_real_tips10y_pct']:.2f}% | Breakeven 10Y: {metricas['breakeven_inflacion_10y_pct']:.2f}%")
    print(f"  • Spread TPM-Fed: {metricas['spread_tasas_chile_fed_pct']:+.2f}% | Cobre 5D: {metricas['cobre_variacion_5d_pct']:+.1f}% (${metricas['cobre_spot_comex']:.2f}) | Petróleo 5D: {metricas['petroleo_shock_max_5d_pct']:+.1f}%")
    print("-" * 80)
    print("🎯 MATRIZ DE PERMISOS TÉCNICOS Y GESTIÓN DE RIESGO MT5:")

    for sym, val in data["activos"].items():
        rp = val["parametros_riesgo"]
        print(f"\n[{sym}] - {val['nombre']} ({val['tipo']})")
        print(f"  • Sesgo Score  : {val['sesgo_score']:+.2f} -> {val['sesgo_etiqueta']}")
        print(f"  • Spot / ATR   : Spot ${rp['precio_spot']} | ATR H1: {rp['atr_h1']} | ATR D1: {rp['atr_d1']}")
        print(f"  • Stop Loss    : H1 = {rp['stop_loss_mult_intraday']}x ATR ({rp['distancia_sl_h1_puntos']} pts) | D1 = {rp['stop_loss_mult_daily']}x ATR ({rp['distancia_sl_d1_puntos']} pts)")
        print(f"  • Salida TP    : {rp['take_profit_tipo']} (Trailing: {rp['trailing_stop_mult_atr']}x ATR)" if rp['trailing_stop_mult_atr'] else f"  • Salida TP    : {rp['take_profit_tipo']}")
        print(f"  • PERMITIDOS   : {', '.join(val['setups_permitidos'])}")
        print(f"  • PROHIBIDOS   : {', '.join(val['setups_prohibidos'])}")
        print(f"  • Drivers      : {val['justificacion_vectores'][0]}")

    print("\n" + "=" * 80)
    print(f"[OK] Matriz persistida exitosamente en -> {OUTPUT_FILE}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de Sesgo Cuantitativo Intermercado")
    parser.add_argument("--json", action="store_true", help="Imprime solo salida JSON en stdout")
    args = parser.parse_args()

    res = ejecutar_motor_sesgo(verbose=not args.json)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
