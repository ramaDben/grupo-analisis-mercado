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


def _f(deltas: dict, key: str) -> float | None:
    """Extrae un valor numérico de deltas o devuelve None si no existe."""
    v = deltas.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _shock_petroleo_con_signo(wti_pct: float | None, brent_pct: float | None) -> tuple[float, float]:
    """Devuelve (max_abs, signed_of_that_leg). Rally >0, crash <0."""
    cands = [x for x in (wti_pct, brent_pct) if x is not None]
    if not cands:
        return 0.0, 0.0
    chosen = max(cands, key=lambda x: abs(x))
    return abs(chosen), chosen


def evaluar_regimen_candidato(deltas: dict, cfg: dict) -> tuple[str, str, bool, str]:
    """
    Evalúa el régimen candidato aplicando el orden de precedencia estricto:
    R3 (Estanflación) ≻ R1 (Inflación Cost-Push) ≻ R4 (Recesión/Bull Steepener) ≻ R2 (Goldilocks) ≻ R0 (Calma)
    """
    rt = cfg["regime_thresholds"]

    # oil_signed es estricto: no fallback unsigned
    oil_signed = _f(deltas, "oil_signed_pct_5d")

    us10y_diff = _f(deltas, "us10y_diff_5d")
    if us10y_diff is None:
        us10y_diff = _f(deltas, "dgs10_diff_5d")
    us10y_diff_bps = None if us10y_diff is None else us10y_diff * 100.0

    tips10y_diff = _f(deltas, "tips10y_diff_5d")
    tips10y_diff_bps = None if tips10y_diff is None else tips10y_diff * 100.0

    breakeven_diff = _f(deltas, "breakeven_diff_5d")
    breakeven_diff_bps = None if breakeven_diff is None else breakeven_diff * 100.0

    copper_pct_5d = _f(deltas, "copper_pct_5d")
    dgs2_diff = _f(deltas, "dgs2_diff_5d")
    dgs2_diff_bps = None if dgs2_diff is None else dgs2_diff * 100.0

    spread_2s10s = _f(deltas, "spread_2s10s_actual")
    spread_diff = _f(deltas, "spread_2s10s_diff_5d")
    spread_diff_bps = None if spread_diff is None else spread_diff * 100.0

    # 1. Prioridad 1: R3 - Estanflación / Turbulencia Geopolítica
    # Solo rally en petróleo (oil_signed >= umbral) Y alza en tasas del Tesoro o TIPS
    es_shock_petroleo = (oil_signed is not None) and (oil_signed >= rt["oil_shock_pct_5d"])
    es_shock_tasas = False
    if us10y_diff_bps is not None and us10y_diff_bps >= rt["us10y_shock_bps_5d"]:
        es_shock_tasas = True
    if tips10y_diff_bps is not None and tips10y_diff_bps >= rt["tips10y_shock_bps_5d"]:
        es_shock_tasas = True

    if es_shock_petroleo and es_shock_tasas:
        es_extremo = (oil_signed >= rt["oil_extreme_shock_pct"]) or (
            us10y_diff_bps is not None and us10y_diff_bps >= rt["us10y_extreme_shock_bps"]
        )
        return "R3_ESTANFLACION_SHOCK", "Estanflación / Turbulencia Geopolítica", es_extremo, f"Petróleo en rally (+{oil_signed:.1f}%) y tasas en tensión (+{(us10y_diff_bps or 0.0):.1f} bps)."

    # 2. Prioridad 2: R1 - Shock Inflacionario / Cost-Push
    es_shock_breakeven = (breakeven_diff_bps is not None) and (breakeven_diff_bps >= rt["breakeven_shock_bps_5d"])
    es_curva_plana = (spread_2s10s is not None) and ((spread_2s10s * 100.0) <= rt["curve_flat_threshold_bps"])
    tasas_alza = (us10y_diff_bps is not None) and (us10y_diff_bps > 5.0)
    if es_shock_breakeven and (es_curva_plana or tasas_alza):
        es_extremo = breakeven_diff_bps >= rt["breakeven_extreme_shock_bps"]
        return "R1_SHOCK_INFLACIONARIO", "Shock Inflacionario / Cost-Push", es_extremo, f"Expectativas de inflación (Breakeven) en alza (+{breakeven_diff_bps:.1f} bps) y curva contenida."

    # 3. Prioridad 3: R4 - Recesión / Vuelo a la Calidad (Curva invertida o Bull Steepener Y Cobre colapsa)
    es_curva_invertida = (spread_2s10s is not None) and (spread_2s10s < rt["curve_inversion_threshold"])
    es_bull_steepener = (
        (dgs2_diff_bps is not None and dgs2_diff_bps <= rt["bull_steepener_dgs2_drop_bps"])
        and (spread_diff_bps is not None and spread_diff_bps >= rt["bull_steepener_spread_expansion_bps"])
    )
    es_cobre_recesion = (copper_pct_5d is not None) and (copper_pct_5d <= rt["copper_recession_pct_5d"])

    if (es_curva_invertida or es_bull_steepener) and es_cobre_recesion:
        es_extremo = copper_pct_5d <= rt["copper_extreme_recession_pct"]
        return "R4_RECESION_VUELO_CALIDAD", "Recesión / Vuelo a la Calidad", es_extremo, f"Curva alertando desaceleración/recortes y Cobre cayendo ({copper_pct_5d:.1f}%)."

    # 4. Prioridad 4: R2 - Expansión / Desinflación (Goldilocks)
    es_cobre_fuerte = (copper_pct_5d is not None) and (copper_pct_5d >= rt["copper_goldilocks_pct_5d"])
    es_tasas_estables = (us10y_diff_bps is not None) and (abs(us10y_diff_bps) <= rt["us10y_stable_bandwidth_bps"])
    if es_cobre_fuerte and es_tasas_estables:
        es_extremo = copper_pct_5d >= rt["copper_extreme_goldilocks_pct"]
        return "R2_GOLDILOCKS_EXPANSION", "Expansión Sólida / Goldilocks", es_extremo, f"Cobre en expansión (+{copper_pct_5d:.1f}%) con tasas del Tesoro estables ({us10y_diff_bps:+.1f} bps)."

    # 5. Default: R0 - Calma / Rango / Absorción
    return "R0_CALMA_RANGO", "Calma / Rango / Absorción", False, "Drivers en equilibrio dinámico sin shocks direccionales extremos."


def aplicar_histeresis(
    prev_reg: dict | None,
    cand_cod: str,
    cand_nom: str,
    es_extremo: bool,
    desc_cand: str,
    cfg: dict
) -> dict:
    """
    Aplica la máquina de estados de histéresis temporal.
    Garantiza que una transición no extrema requiera 2 lecturas D1 consecutivas.
    """
    req_confirm = cfg["regime_thresholds"].get("hysteresis_required_confirmations", 2)
    prev = prev_reg or {}
    prev_cod = prev.get("codigo")
    prev_consec = prev.get("lecturas_consecutivas", 0)
    prev_cand_cod = prev.get("candidato_codigo")
    prev_cand_lec = prev.get("candidato_lecturas", 0)

    # 1. Caso extremo -> Activación inmediata
    if es_extremo:
        return {
            "codigo": cand_cod,
            "nombre": cand_nom,
            "confirmado_por_historesis": True,
            "lecturas_consecutivas": 1,
            "candidato_codigo": None,
            "candidato_lecturas": 0,
            "descripcion": desc_cand + " [EVENTO EXTREMO: Conmutación Inmediata]"
        }

    # 2. Sin estado previo -> Activa con 1 lectura pero sin confirmar (salvo que sea R0)
    if not prev_cod:
        return {
            "codigo": cand_cod,
            "nombre": cand_nom,
            "confirmado_por_historesis": (cand_cod == "R0_CALMA_RANGO"),
            "lecturas_consecutivas": 1,
            "candidato_codigo": None,
            "candidato_lecturas": 0,
            "descripcion": desc_cand
        }

    # 3. Candidato igual al régimen activo previo -> Incrementa lecturas y confirma
    if cand_cod == prev_cod:
        nueva_consec = prev_consec + 1
        return {
            "codigo": cand_cod,
            "nombre": cand_nom,
            "confirmado_por_historesis": (nueva_consec >= req_confirm or cand_cod == "R0_CALMA_RANGO"),
            "lecturas_consecutivas": nueva_consec,
            "candidato_codigo": None,
            "candidato_lecturas": 0,
            "descripcion": desc_cand
        }

    # 4. Candidato distinto al régimen activo previo
    if cand_cod == prev_cand_cod:
        nueva_cand_lec = prev_cand_lec + 1
    else:
        nueva_cand_lec = 1

    if nueva_cand_lec >= req_confirm:
        # Transición confirmada tras cumplir confirmaciones requeridas
        return {
            "codigo": cand_cod,
            "nombre": cand_nom,
            "confirmado_por_historesis": True,
            "lecturas_consecutivas": req_confirm,
            "candidato_codigo": None,
            "candidato_lecturas": 0,
            "descripcion": f"Transición confirmada a {cand_nom} tras {req_confirm} observaciones consecutivas."
        }
    else:
        # Se mantiene el régimen previo; conserva su confirmación si ya cumplía req_confirm
        prev_nom = prev.get("nombre", prev_cod)
        prev_confirmado = prev_consec >= req_confirm
        return {
            "codigo": prev_cod,
            "nombre": prev_nom,
            "confirmado_por_historesis": prev_confirmado,
            "lecturas_consecutivas": prev_consec,
            "candidato_codigo": cand_cod,
            "candidato_lecturas": nueva_cand_lec,
            "descripcion": f"Régimen previo {prev_nom} activo. Nuevo candidato {cand_nom} en observación ({nueva_cand_lec}/{req_confirm})."
        }


def calcular_confianza(
    drivers_info: list[dict], cfg: dict, ahora: datetime | None = None
) -> tuple[float, float, float, float]:
    """Calcula el índice de confianza matemático auditable."""
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
    rt = cfg["regime_thresholds"]
    activos_res = {}

    cobre_spot = drivers_data.get("copper_spot")
    copper_pct_5d = drivers_data.get("copper_pct_5d")
    tpm_chile = drivers_data.get("tpm_chile")
    fed_funds = drivers_data.get("fed_funds")
    spread_tasas = (tpm_chile - fed_funds) if (tpm_chile is not None and fed_funds is not None) else None
    fwd_ext = drivers_data.get("fwd_extranjeros")
    if fwd_ext is not None:
        fwd_sentido = "vendedora" if fwd_ext < 0 else "compradora"
    else:
        fwd_sentido = "N/A"
    tips_10y = drivers_data.get("tips_10y")
    breakeven_10y = drivers_data.get("breakeven_10y")
    dgs10 = drivers_data.get("dgs10")
    oil_signed = drivers_data.get("oil_signed_pct_5d")

    for asset_cfg in cfg["assets_monitored"]:
        asset_id = asset_cfg["id"]
        precio_info = precios_summary.get("activos", {}).get(asset_id, {})
        h1_info = precio_info.get("H1") or {}
        d1_info = precio_info.get("D1") or {}

        spot = h1_info.get("close") or d1_info.get("close")
        atr_h1_raw = h1_info.get("atr_14")
        atr_d1_raw = d1_info.get("atr_20")

        atr_h1 = float(atr_h1_raw) if (atr_h1_raw is not None and atr_h1_raw > 0) else None
        atr_d1 = float(atr_d1_raw) if (atr_d1_raw is not None and atr_d1_raw > 0) else None

        # Solo el crudo en shock precautorio lo baja (Kilian #1 y #3, Playbook §4).
        # Se declara para TODOS: un consumidor que lo lea con `.get()` y no lo
        # encuentre dimensiona al 100 % sin enterarse.
        factor_apalancamiento = 1.0
        sl_dist_h1 = round(rp["stop_loss_mult_intraday"] * atr_h1, asset_cfg["digits"]) if atr_h1 is not None else None
        sl_dist_d1 = round(rp["stop_loss_mult_daily"] * atr_d1, asset_cfg["digits"]) if atr_d1 is not None else None

        # Lógica de Sesgo y Permisos por Activo
        if asset_id == "USDCLP":
            copper_recession_pct = rt.get("copper_recession_pct_5d", -2.5)
            copper_goldilocks_pct = rt.get("copper_goldilocks_pct_5d", 1.5)

            if cobre_spot is None or copper_pct_5d is None:
                sesgo_score = 0.0
                sesgo_etiqueta = "DATOS_INCOMPLETOS"
                setups_permitidos = []
                setups_prohibidos = []
                tp_tipo = "NIVEL_OPUESTO_CANAL"
                trailing_mult = None
                justificacion = ["Datos de Cobre incompletos o ausentes en data central/"]
            elif regimen_activo == "R4_RECESION_VUELO_CALIDAD":
                sesgo_score = 1.20
                sesgo_etiqueta = "ALCISTA USD (PESO DÉBIL POR RECESIÓN/VUELO A CALIDAD)"
                setups_permitidos = ["BREAKOUT_DONCHIAN_H1", "PULLBACK_EMA20_H1"]
                setups_prohibidos = ["FADE_SUPPORT_RESISTANCE_M15", "LONG_INVERTIDO", "GRID_SIN_STOP"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Régimen {regimen_activo} debilita al peso chileno por aversión al riesgo global",
                    "Flujos de refugio fortalecen al dólar estadounidense"
                ]
            elif regimen_activo == "R3_ESTANFLACION_SHOCK":
                sesgo_score = 0.80
                sesgo_etiqueta = "ALCISTA MODERADO USD (ESTANFLACION GLOBAL)"
                setups_permitidos = ["BREAKOUT_DONCHIAN_H1", "PULLBACK_EMA20_H1"]
                setups_prohibidos = ["MEAN_REVERSION_RSI_H1", "FADE_SUPPORT_RESISTANCE_M15"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    "Shock petrolero y presiones inflacionarias fortalecen al dólar global frente a emergentes"
                ]
            elif regimen_activo == "R1_SHOCK_INFLACIONARIO":
                sesgo_score = 0.60
                sesgo_etiqueta = "ALCISTA MODERADO USD (SHOCK INFLACION US)"
                setups_permitidos = ["BREAKOUT_DONCHIAN_H1", "PULLBACK_EMA20_H1"]
                setups_prohibidos = ["FADE_TOP_RESISTANCE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    "Expectativas de inflación US al alza mantienen fortaleza en el dólar"
                ]
            elif regimen_activo == "R2_GOLDILOCKS_EXPANSION":
                sesgo_score = -1.20
                sesgo_etiqueta = "BAJISTA USD (PESO FUERTE POR GOLDILOCKS)"
                setups_permitidos = ["PULLBACK_SHORT_EMA20", "BREAKDOWN_DONCHIAN_H1"]
                setups_prohibidos = ["BREAKOUT_CHASE_LONG", "LONG_SWING_FADE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Régimen {regimen_activo} favorece al peso chileno por apetito por riesgo y desinflación",
                    "Presión vendedora estructural sobre el tipo de cambio USD/CLP"
                ]
            else:  # solo R0_CALMA_RANGO (el cobre desempata)
                if copper_pct_5d <= copper_recession_pct:
                    sesgo_score = 1.00
                    sesgo_etiqueta = "ALCISTA USD (CAIDA COBRE EN R0)"
                    setups_permitidos = ["BREAKOUT_DONCHIAN_H1", "PULLBACK_EMA20_H1"]
                    setups_prohibidos = ["FADE_SUPPORT_RESISTANCE_M15", "LONG_INVERTIDO", "GRID_SIN_STOP"]
                    tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                    trailing_mult = rp["trailing_stop_mult_trend"]
                    justificacion = [f"Caída de 5 días en Cobre ({copper_pct_5d:+.1f}%) debilita al peso chileno"]
                elif copper_pct_5d >= copper_goldilocks_pct:
                    sesgo_score = -1.00
                    sesgo_etiqueta = "BAJISTA USD (RALLY COBRE EN R0)"
                    setups_permitidos = ["PULLBACK_SHORT_EMA20", "BREAKDOWN_DONCHIAN_H1"]
                    setups_prohibidos = ["BREAKOUT_CHASE_LONG", "LONG_SWING_FADE"]
                    tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                    trailing_mult = rp["trailing_stop_mult_trend"]
                    justificacion = [f"Rally de 5 días en Cobre ({copper_pct_5d:+.1f}%) fortalece al peso chileno"]
                else:
                    sesgo_score = 0.0
                    sesgo_etiqueta = "NEUTRAL / RANGO (S1 - R1)"
                    setups_permitidos = ["FADE_SUPPORT_RESISTANCE_H1", "MEAN_REVERSION_RSI_H1"]
                    setups_prohibidos = ["BREAKOUT_CHASE_LONG", "GRID_SIN_STOP"]
                    tp_tipo = "NIVEL_OPUESTO_CANAL"
                    trailing_mult = None
                    justificacion = [
                        f"Variables macro en equilibrio relativo (Cobre ${cobre_spot:.2f} USD/lb)",
                        f"Diferencial de tasas en {spread_tasas:+.2f}%" if spread_tasas is not None else "Diferencial de tasas N/A",
                        f"Posición forward no residentes {fwd_sentido} ({fwd_ext:+.0f}M USD)" if fwd_ext is not None else "Forward no residentes N/A"
                    ]

        elif asset_id == "XAUUSD":
            if regimen_activo in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"] or (tips_10y is not None and tips_10y < 2.20):
                sesgo_score = 1.80
                sesgo_etiqueta = "FUERTE ALCISTA"
                setups_permitidos = ["PULLBACK_EMA20_H1", "BREAKOUT_DONCHIAN_50_H1"]
                setups_prohibidos = ["SHORT_FADE_OVERBOUGHT", "VENTA_CONTRA_TENDENCIA"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                just_tips = f"Tasa Real TIPS 10Y (DFII10 en {tips_10y:.2f}%) y Breakeven ({breakeven_10y:.2f}%) impulsan demanda refugio" if (tips_10y is not None and breakeven_10y is not None) else f"Régimen macro {regimen_activo} impulsa demanda refugio"
                justificacion = [
                    just_tips,
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
            if oil_signed is not None and (regimen_activo == "R3_ESTANFLACION_SHOCK" or oil_signed > 2.0):
                sesgo_score = 1.50
                sesgo_etiqueta = "ALCISTA POR SHOCK"
                setups_prohibidos = ["FADE_TOP_RESISTANCE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"

                # Kilian (2009): el crudo sube por razones distintas y cada una
                # exige un manejo distinto. La justificación anterior decía
                # "Shock Precautorio/Demanda", juntando en una barra las dos
                # cosas que el paper existe para separar.
                #
                # El cobre es el proxy de la demanda industrial global. Si sube
                # con el crudo, el alza es demanda agregada (Kilian #2) y se
                # sigue la tendencia con posición completa. Si el crudo se
                # dispara solo, es demanda precautoria por temor a faltantes o
                # un shock de oferta (Kilian #3 y #1): ahí el Playbook manda
                # ceñir el trailing y operar al 50 %.
                cobre_confirma = (
                    copper_pct_5d is not None
                    and copper_pct_5d >= rt["copper_goldilocks_pct_5d"]
                )
                if cobre_confirma:
                    setups_permitidos = ["BREAKOUT_VOLATILITY_H1", "PULLBACK_EMA20_H1"]
                    trailing_mult = rp["trailing_stop_mult_trend"]
                    factor_apalancamiento = 1.0
                    justificacion = [
                        f"Rally de 5 días en crudo ({oil_signed:+.1f}%) CON respaldo del cobre "
                        f"({copper_pct_5d:+.1f}%): shock de demanda agregada (Kilian 2009)",
                        "Se sigue la tendencia con posición completa y trailing amplio",
                    ]
                else:
                    # `PULLBACK_EMA20_H1` y no EMA16: la media de 16 no existe en el
                    # Playbook —que usa 20 y 50— ni la devuelve `get_asset_levels`.
                    # Era un setup permitido que nadie podía ejecutar.
                    setups_permitidos = ["BREAKOUT_VOLATILITY_H1", "PULLBACK_EMA20_H1"]
                    trailing_mult = rp["trailing_stop_mult_precautorio"]
                    factor_apalancamiento = rp["factor_apalancamiento_precautorio"]
                    cobre_txt = f"{copper_pct_5d:+.1f}%" if copper_pct_5d is not None else "N/A"
                    justificacion = [
                        f"Rally de 5 días en crudo ({oil_signed:+.1f}%) SIN respaldo del cobre "
                        f"({cobre_txt}): shock precautorio o de oferta (Kilian 2009)",
                        "Trailing ceñido y apalancamiento al 50 %: el alza no la sostiene la demanda real",
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
            if dgs10 is None and regimen_activo == "R0_CALMA_RANGO":
                sesgo_score = 0.0
                sesgo_etiqueta = "DATOS_INCOMPLETOS"
                setups_permitidos = []
                setups_prohibidos = []
                tp_tipo = "NIVEL_OPUESTO_CANAL"
                trailing_mult = None
                justificacion = ["Dato de tasa DGS10 ausente en data central/"]
            elif (dgs10 is not None and dgs10 > 4.70) or regimen_activo in ["R3_ESTANFLACION_SHOCK", "R1_SHOCK_INFLACIONARIO"]:
                sesgo_score = -1.20
                sesgo_etiqueta = "BAJISTA / PRESIÓN EN MÚLTIPLOS"
                setups_permitidos = ["SELL_PULLBACK_EMA50_H1", "BREAKDOWN_DONCHIAN_H1"]
                setups_prohibidos = ["BUY_THE_DIP_AGGRESSIVE", "COMPRA_SIN_CONFIRMACION"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Rendimiento UST 10Y en {dgs10:.2f}% comprime múltiplos de valuación en tecnológicas" if dgs10 is not None else "Régimen macro restrictivo penaliza múltiplos tecnológicos",
                    "Régimen de tasas elevadas penaliza activos de alta duración"
                ]
            else:
                sesgo_score = 0.80
                sesgo_etiqueta = "ALCISTA / EXPANSION"
                setups_permitidos = ["PULLBACK_EMA20_H1", "BREAKOUT_DONCHIAN_H1"]
                setups_prohibidos = ["SHORT_FADE"]
                tp_tipo = "TRAILING_STOP_ASYMMETRIC"
                trailing_mult = rp["trailing_stop_mult_trend"]
                justificacion = [
                    f"Tasas 10Y ({dgs10:.2f}%) y liquidez favorable para renta variable" if dgs10 is not None else "Liquidez favorable para renta variable"
                ]
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
                "atr_h1": round(atr_h1, asset_cfg["digits"]) if atr_h1 is not None else None,
                "atr_d1": round(atr_d1, asset_cfg["digits"]) if atr_d1 is not None else None,
                "stop_loss_mult_intraday": rp["stop_loss_mult_intraday"],
                "distancia_sl_h1_puntos": sl_dist_h1,
                "stop_loss_mult_daily": rp["stop_loss_mult_daily"],
                "distancia_sl_d1_puntos": sl_dist_d1,
                "take_profit_tipo": tp_tipo,
                "trailing_stop_mult_atr": trailing_mult,
                "factor_apalancamiento": factor_apalancamiento,
                # El Chandelier son dos parametros, no uno. Viajan juntos o el
                # consumidor no puede calcular el nivel y lo inventa.
                "trailing_stop_lookback": (
                    rp["trailing_stop_lookback_period"] if trailing_mult is not None else None
                ),
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
    dgs2_diff, _, dgs2_fecha = _delta_n_dias(dgs2_cron, 5)
    tips_diff, _, tips_fecha = _delta_n_dias(dfii10_cron, 5)
    breakeven_diff, _, breakeven_fecha = _delta_n_dias(t10yie_cron, 5)

    _, wti_pct_5d, wti_fecha = _delta_n_dias(wti_cron, 5)
    _, brent_pct_5d, brent_fecha = _delta_n_dias(brent_cron, 5)
    _, copper_pct_5d, copper_fecha = _delta_n_dias(copper_cron, 5)

    oil_max_pct, oil_signed_pct = _shock_petroleo_con_signo(wti_pct_5d, brent_pct_5d)

    dgs10_actual = dgs10_cron[-1][1] if dgs10_cron else None
    dgs2_actual = dgs2_cron[-1][1] if dgs2_cron else None
    spread_2s10s_actual = (dgs10_actual - dgs2_actual) if (dgs10_actual is not None and dgs2_actual is not None) else None
    spread_2s10s_diff = (dgs10_diff - dgs2_diff) if (dgs10_diff is not None and dgs2_diff is not None) else None

    tips_actual = dfii10_cron[-1][1] if dfii10_cron else None
    breakeven_actual = t10yie_cron[-1][1] if t10yie_cron else None

    # Chile data
    chile_series = chile_data.get("series", {})
    # La serie se llama "TPM" en bcch_macro_data.json, no "TPM_CHILE". Con la clave
    # equivocada esto devolvia lista vacia, el spread de carry salia null ("Diferencial
    # de tasas N/A" en la justificacion) y TPM_CHILE contaba como MISSING en el indice
    # de confianza, dejandolo en 54,6% en vez de 65,4%. 665 observaciones en disco sin usar.
    tpm_cron = _obtener_serie_cronologica(chile_series.get("TPM", {}).get("historico", {}))
    _, _, tpm_fecha = _delta_n_dias(tpm_cron, 5)
    tpm_actual = tpm_cron[-1][1] if tpm_cron else None
    fed_funds_actual = dff_cron[-1][1] if dff_cron else None
    fwd_cron = _obtener_serie_cronologica(chile_series.get("POSICION_FORWARD_EXTRANJEROS", {}).get("historico", {}))
    fwd_actual = fwd_cron[-1][1] if fwd_cron else None

    copper_actual = copper_cron[-1][1] if copper_cron else None

    deltas_payload = {
        "dgs10_actual": dgs10_actual,
        "dgs10_diff_5d": dgs10_diff,
        "us10y_diff_5d": dgs10_diff,  # Alias obligatorio para compatibilidad FSM
        "dgs2_diff_5d": dgs2_diff,
        "spread_2s10s_actual": spread_2s10s_actual,
        "spread_2s10s_diff_5d": spread_2s10s_diff,
        "tips10y_diff_5d": tips_diff,
        "breakeven_diff_5d": breakeven_diff,
        "oil_max_pct_5d": oil_max_pct,
        "oil_signed_pct_5d": oil_signed_pct,
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
    regimen_dict = aplicar_histeresis(prev_reg, cand_cod, cand_nom, es_extremo, desc_cand, cfg)
    regimen_activo_cod = regimen_dict["codigo"]

    # 4. Cálculo de Confianza con fechas independientes por driver
    drivers_audit = [
        {"nombre": "DGS10", "fecha": dgs10_fecha, "status": yields.get("DGS10", {}).get("status", "OK") if dgs10_cron else "MISSING", "cobertura": 1.0 if dgs10_cron else 0.0},
        {"nombre": "DFII10", "fecha": tips_fecha, "status": yields.get("DFII10", {}).get("status", "OK") if dfii10_cron else "MISSING", "cobertura": 1.0 if dfii10_cron else 0.0},
        {"nombre": "T10YIE", "fecha": breakeven_fecha, "status": yields.get("T10YIE", {}).get("status", "OK") if t10yie_cron else "MISSING", "cobertura": 1.0 if t10yie_cron else 0.0},
        {"nombre": "TPM_CHILE", "fecha": tpm_fecha, "status": chile_series.get("TPM", {}).get("status", "OK") if tpm_cron else "MISSING", "cobertura": 1.0 if tpm_cron else 0.0},
        {"nombre": "COBRE", "fecha": copper_fecha, "status": comm_series.get("COBRE_COMEX", {}).get("status", "OK") if copper_cron else "MISSING", "cobertura": 1.0 if copper_cron else 0.0},
        {"nombre": "PETROLEO", "fecha": wti_fecha or brent_fecha, "status": comm_series.get("PETROLEO_WTI", {}).get("status", "OK") if wti_cron else "MISSING", "cobertura": 1.0 if wti_cron else 0.0}
    ]
    conf_global, f_frescura, f_antiguedad, f_cobertura = calcular_confianza(drivers_audit, cfg)

    # Si la confianza es muy baja o faltan drivers clave, desconfirmar
    if conf_global < 50.0 or any(d["status"] == "MISSING" for d in drivers_audit if d["nombre"] in ["DGS10", "COBRE", "PETROLEO"]):
        regimen_dict["confirmado_por_historesis"] = False

    # 5. Evaluación por activo
    activos_evaluados = evaluar_activos(regimen_activo_cod, deltas_payload, precios_summary, cfg)

    # 6. Estructura de salida
    ahora_iso = datetime.now(timezone.utc).isoformat()
    resultado_final = {
        "schema_version": cfg.get("schema_version", "2.0.0"),
        "config_hash": config_hash,
        "as_of_utc": ahora_iso,
        "regimen_macro_global": regimen_dict,
        "metricas_clave": {
            "spread_2s10s_pct": round(spread_2s10s_actual, 4) if spread_2s10s_actual is not None else None,
            "tasa_real_tips10y_pct": round(tips_actual, 2) if tips_actual is not None else None,
            "breakeven_inflacion_10y_pct": round(breakeven_actual, 2) if breakeven_actual is not None else None,
            "spread_tasas_chile_fed_pct": round(tpm_actual - fed_funds_actual, 2) if (tpm_actual is not None and fed_funds_actual is not None) else None,
            "cobre_spot_comex": round(copper_actual, 4) if copper_actual is not None else None,
            "cobre_variacion_5d_pct": round(copper_pct_5d, 2) if copper_pct_5d is not None else None,
            "petroleo_shock_max_5d_pct": round(oil_max_pct, 2) if oil_max_pct is not None else None,
            "petroleo_shock_signed_5d_pct": round(oil_signed_pct, 2) if oil_signed_pct is not None else None
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
    s_2s10s = f"{metricas['spread_2s10s_pct']:+.2f}%" if metricas['spread_2s10s_pct'] is not None else "N/A"
    s_tips = f"{metricas['tasa_real_tips10y_pct']:.2f}%" if metricas['tasa_real_tips10y_pct'] is not None else "N/A"
    s_bk = f"{metricas['breakeven_inflacion_10y_pct']:.2f}%" if metricas['breakeven_inflacion_10y_pct'] is not None else "N/A"
    s_spr_tpm = f"{metricas['spread_tasas_chile_fed_pct']:+.2f}%" if metricas['spread_tasas_chile_fed_pct'] is not None else "N/A"
    s_cu_5d = f"{metricas['cobre_variacion_5d_pct']:+.1f}%" if metricas['cobre_variacion_5d_pct'] is not None else "N/A"
    s_cu_spot = f"${metricas['cobre_spot_comex']:.2f}" if metricas['cobre_spot_comex'] is not None else "N/A"
    s_oil_5d = f"{metricas['petroleo_shock_signed_5d_pct']:+.1f}%" if metricas['petroleo_shock_signed_5d_pct'] is not None else "N/A"

    print(f"  • Curva 2s10s: {s_2s10s} | TIPS 10Y: {s_tips} | Breakeven 10Y: {s_bk}")
    print(f"  • Spread TPM-Fed: {s_spr_tpm} | Cobre 5D: {s_cu_5d} ({s_cu_spot}) | Petróleo 5D: {s_oil_5d}")
    print("-" * 80)
    print("🎯 MATRIZ DE PERMISOS TÉCNICOS Y GESTIÓN DE RIESGO MT5:")

    for sym, val in data["activos"].items():
        rp = val["parametros_riesgo"]
        print(f"\n[{sym}] - {val['nombre']} ({val['tipo']})")
        print(f"  • Sesgo Score  : {val['sesgo_score']:+.2f} -> {val['sesgo_etiqueta']}")
        print(f"  • Spot / ATR   : Spot ${rp['precio_spot']} | ATR H1: {rp['atr_h1']} | ATR D1: {rp['atr_d1']}")
        print(f"  • Stop Loss    : H1 = {rp['stop_loss_mult_intraday']}x ATR ({rp['distancia_sl_h1_puntos']} pts) | D1 = {rp['stop_loss_mult_daily']}x ATR ({rp['distancia_sl_d1_puntos']} pts)")
        print(f"  • Salida TP    : {rp['take_profit_tipo']} (Trailing: {rp['trailing_stop_mult_atr']}x ATR)" if rp['trailing_stop_mult_atr'] else f"  • Salida TP    : {rp['take_profit_tipo']}")
        print(f"  • PERMITIDOS   : {', '.join(val['setups_permitidos']) if val['setups_permitidos'] else 'NINGUNO'}")
        print(f"  • PROHIBIDOS   : {', '.join(val['setups_prohibidos']) if val['setups_prohibidos'] else 'NINGUNO'}")
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
