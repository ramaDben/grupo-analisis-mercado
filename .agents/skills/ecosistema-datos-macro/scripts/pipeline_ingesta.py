#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pipeline_ingesta.py
Orquestador maestro de ingesta macroeconomica, deduplicacion canonica,
deteccion de revisiones historicas y consolidacion de drivers para USD/CLP.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
DATA_CENTRAL = BASE_DIR / "data central"
DATA_AGENDA = DATA_CENTRAL / "DATA AGENDA"
DATA_DRIVERS = DATA_CENTRAL / "DATA DRIVERS USDCLP"
ESTADO_FILE = DATA_AGENDA / "estado_ejecucion.json"
LATEST_DRIVERS_FILE = DATA_DRIVERS / "latest_drivers.json"

# Importar extractores
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extractor_usa
import extractor_chile
import extractor_europa_uk
import extractor_commodities
import extractor_japon

def calcular_hash_canonico(payload: dict) -> str:
    """Calcula un hash SHA-256 sobre un payload serializado con claves ordenadas."""
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

def detectar_revisiones_historicas(hist_anterior: dict, hist_nuevo: dict) -> list:
    """Compara observaciones previas para detectar revisiones retroactivas."""
    revisiones = []
    # Comparar claves comunes
    for fecha in set(hist_anterior.keys()).intersection(hist_nuevo.keys()):
        val_ant = hist_anterior[fecha]
        val_nue = hist_nuevo[fecha]
        if val_ant != val_nue:
            revisiones.append(f"Fecha {fecha}: revisado de {val_ant} a {val_nue}")
    return revisiones

def _extraer_ultimo_valido(hist: dict):
    """Obtiene la fecha más reciente y el valor numérico válido (ignora NaNs y ordena cronológicamente)."""
    if not hist:
        return None, None
    valid_items = []
    for k, v in hist.items():
        if v is not None and v == v:  # Check not NaN
            try:
                # Normalizar clave a ISO YYYY-MM-DD para ordenamiento cronológico correcto
                k_str = str(k).strip()
                if len(k_str) == 10 and k_str[2] == "-" and k_str[5] == "-":
                    k_sort = f"{k_str[6:10]}-{k_str[3:5]}-{k_str[0:2]}"
                else:
                    k_sort = k_str
                valid_items.append((k_sort, k_str, float(v)))
            except (ValueError, TypeError):
                pass
    if not valid_items:
        return None, None
    valid_items.sort(key=lambda x: x[0])
    _, orig_fecha, val = valid_items[-1]
    return orig_fecha, val

def consolidar_latest_drivers(usa_data: dict, chile_data: dict, eu_data: dict, comm_data: dict, japon_data: dict = None) -> dict:
    """Genera el snapshot de drivers con frescura (as_of) y flag is_stale."""
    ahora_utc = datetime.now(timezone.utc).isoformat()
    if japon_data is None:
        japon_data = {}
    
    # Curva US 10Y
    d10_hist = usa_data.get("curva_rendimientos_yields", {}).get("DGS10", {}).get("historico", {})
    ult_d10_fecha, ult_d10_val = _extraer_ultimo_valido(d10_hist)
    
    # Fed Funds
    dff_hist = usa_data.get("curva_rendimientos_yields", {}).get("DFF", {}).get("historico", {})
    ult_dff_fecha, ult_dff_val = _extraer_ultimo_valido(dff_hist)
    
    # Imacec Chile
    imc_hist = chile_data.get("series", {}).get("IMACEC_12M_VAR", {}).get("historico", {}) or chile_data.get("series", {}).get("IMACEC_TOTAL", {}).get("historico", {})
    ult_imc_fecha, ult_imc_val = _extraer_ultimo_valido(imc_hist)
    
    # TPM Chile
    tpm_hist = chile_data.get("series", {}).get("TPM", {}).get("historico", {})
    ult_tpm_fecha, ult_tpm_val = _extraer_ultimo_valido(tpm_hist)
    
    # Posicion Fwd
    fwd_hist = chile_data.get("series", {}).get("POSICION_FORWARD_EXTRANJEROS", {}).get("historico", {})
    ult_fwd_fecha, ult_fwd_val = _extraer_ultimo_valido(fwd_hist)
    
    # Cobre COMEX USD/lb
    cu_hist = comm_data.get("commodities", {}).get("COBRE_COMEX", {}).get("historico", {})
    ult_cu_fecha, ult_cu_val = _extraer_ultimo_valido(cu_hist)
    
    # Brent
    brent_hist = comm_data.get("commodities", {}).get("PETROLEO_BRENT", {}).get("historico", {})
    ult_brent_fecha, ult_brent_val = _extraer_ultimo_valido(brent_hist)
    
    # Oro Spot
    oro_hist = comm_data.get("commodities", {}).get("ORO_SPOT", {}).get("historico", {})
    ult_oro_fecha, ult_oro_val = _extraer_ultimo_valido(oro_hist)
    
    # Japón: Tasa BoJ, IPC Core, JGB 10Y, USD/JPY
    boj_tasa_val = japon_data.get("politica_monetaria_boj", {}).get("tasa_politica_overnight", {}).get("valor_actual", 1.00)
    boj_tasa_fecha = japon_data.get("politica_monetaria_boj", {}).get("tasa_politica_overnight", {}).get("ultima_decision", "")
    
    cpi_core_hist = japon_data.get("inflacion_japon", {}).get("cpi_core_yoy", {}).get("historico", {})
    ult_cpi_fecha, ult_cpi_val = _extraer_ultimo_valido(cpi_core_hist)
    
    jgb_hist = japon_data.get("politica_monetaria_boj", {}).get("rendimiento_jgb_10y", {}).get("historico", {})
    ult_jgb_fecha, ult_jgb_val = _extraer_ultimo_valido(jgb_hist)
    
    usdjpy_hist = japon_data.get("mercado_divisas", {}).get("usdjpy", {}).get("historico", {})
    ult_usdjpy_fecha, ult_usdjpy_val = _extraer_ultimo_valido(usdjpy_hist)

    return {
        "timestamp_consolidacion": ahora_utc,
        "drivers": {
            "US_10Y_TREASURY": {
                "valor": ult_d10_val,
                "unidad": "%",
                "fecha_dato": ult_d10_fecha,
                "is_stale": usa_data.get("curva_rendimientos_yields", {}).get("DGS10", {}).get("status") != "OK"
            },
            "FED_FUNDS_RATE": {
                "valor": ult_dff_val,
                "unidad": "%",
                "fecha_dato": ult_dff_fecha,
                "is_stale": usa_data.get("curva_rendimientos_yields", {}).get("DFF", {}).get("status") != "OK"
            },
            "COBRE_HG": {
                "valor": ult_cu_val,
                "unidad": "USD/lb",
                "fecha_dato": ult_cu_fecha,
                "is_stale": comm_data.get("commodities", {}).get("COBRE_COMEX", {}).get("status") != "OK"
            },
            "PETROLEO_BRENT": {
                "valor": ult_brent_val,
                "unidad": "USD/bbl",
                "fecha_dato": ult_brent_fecha,
                "is_stale": comm_data.get("commodities", {}).get("PETROLEO_BRENT", {}).get("status") != "OK"
            },
            "ORO_SPOT": {
                "valor": ult_oro_val,
                "unidad": "USD/oz",
                "fecha_dato": ult_oro_fecha,
                "is_stale": "OK" not in comm_data.get("commodities", {}).get("ORO_SPOT", {}).get("status", "")
            },
            "CHILE_IMACEC_12M": {
                "valor": ult_imc_val,
                "unidad": "%",
                "fecha_dato": ult_imc_fecha,
                "is_stale": chile_data.get("series", {}).get("IMACEC_TOTAL", {}).get("status") != "OK"
            },
            "CHILE_TPM": {
                "valor": ult_tpm_val,
                "unidad": "%",
                "fecha_dato": ult_tpm_fecha,
                "is_stale": chile_data.get("series", {}).get("TPM", {}).get("status") != "OK"
            },
            "POSICION_FORWARD_EXTRANJEROS_USD": {
                "valor": ult_fwd_val,
                "unidad": "millones_USD",
                "fecha_dato": ult_fwd_fecha,
                "is_stale": chile_data.get("series", {}).get("POSICION_FORWARD_EXTRANJEROS", {}).get("status") != "OK"
            },
            "BOJ_POLICY_RATE": {
                "valor": boj_tasa_val,
                "unidad": "%",
                "fecha_dato": boj_tasa_fecha,
                "is_stale": japon_data.get("politica_monetaria_boj", {}).get("tasa_politica_overnight", {}).get("status") != "OK"
            },
            "JAPAN_CORE_CPI_YOY": {
                "valor": ult_cpi_val,
                "unidad": "%",
                "fecha_dato": ult_cpi_fecha,
                "is_stale": japon_data.get("inflacion_japon", {}).get("cpi_core_yoy", {}).get("status") != "OK"
            },
            "JGB_10Y_YIELD": {
                "valor": ult_jgb_val,
                "unidad": "%",
                "fecha_dato": ult_jgb_fecha,
                "is_stale": japon_data.get("politica_monetaria_boj", {}).get("rendimiento_jgb_10y", {}).get("status") != "OK"
            },
            "USD_JPY": {
                "valor": ult_usdjpy_val,
                "unidad": "JPY",
                "fecha_dato": ult_usdjpy_fecha,
                "is_stale": "OK" not in japon_data.get("mercado_divisas", {}).get("usdjpy", {}).get("status", "")
            }
        }
    }

def ejecutar_pipeline(forzar: bool = False) -> dict:
    print("=" * 70)
    print(" 🚀 INICIANDO PIPELINE DE INGESTA MACROECONÓMICA Y DETECCIÓN")
    print("=" * 70)
    
    # 1. Cargar estado previo
    estado_previo = {}
    if ESTADO_FILE.exists():
        try:
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                estado_previo = json.load(f)
        except Exception:
            estado_previo = {}
            
    hashes_previos = estado_previo.get("hashes_canonicos", {})
    
    # 2. Ejecutar extractores
    print("\n[1/5] Ejecutando Extractor USA...")
    usa_data = extractor_usa.ejecutar_extraccion_usa()
    
    print("\n[2/5] Ejecutando Extractor Chile...")
    chile_data = extractor_chile.ejecutar_extraccion_chile()
    
    print("\n[3/5] Ejecutando Extractor Europa y UK...")
    eu_data = extractor_europa_uk.ejecutar_extraccion_europa_uk()
    
    print("\n[4/5] Ejecutando Extractor Commodities...")
    comm_data = extractor_commodities.ejecutar_extraccion_commodities()

    print("\n[5/5] Ejecutando Extractor Japón (BoJ / Inflación)...")
    japon_data = extractor_japon.ejecutar_extraccion_japon()
    
    # 3. Calcular hashes canonicos de datos puros (excluyendo 'as_of')
    puro_usa = {k: v for k, v in usa_data.items() if k != "as_of"}
    puro_chile = {k: v for k, v in chile_data.items() if k != "as_of"}
    puro_eu = {k: v for k, v in eu_data.items() if k != "as_of"}
    puro_comm = {k: v for k, v in comm_data.items() if k != "as_of"}
    puro_japon = {k: v for k, v in japon_data.items() if k != "as_of"}
    
    hash_usa = calcular_hash_canonico(puro_usa)
    hash_chile = calcular_hash_canonico(puro_chile)
    hash_eu = calcular_hash_canonico(puro_eu)
    hash_comm = calcular_hash_canonico(puro_comm)
    hash_japon = calcular_hash_canonico(puro_japon)
    
    nuevos_hashes = {
        "usa": hash_usa,
        "chile": hash_chile,
        "europa_uk": hash_eu,
        "commodities": hash_comm,
        "japon": hash_japon
    }
    
    # 4. Detectar cambios y revisiones
    novedades_detalle = []
    
    if hash_usa != hashes_previos.get("usa"):
        novedades_detalle.append("Datos actualizados en USA (Curva Treasuries / Buybacks / Fed Funds)")
    if hash_chile != hashes_previos.get("chile"):
        novedades_detalle.append("Datos actualizados en Chile (Imacec / TPM / Posición Forward)")
    if hash_eu != hashes_previos.get("europa_uk"):
        novedades_detalle.append("Datos actualizados en Europa/UK (Tasas BCE / Bank Rate)")
    if hash_comm != hashes_previos.get("commodities"):
        novedades_detalle.append("Datos actualizados en Commodities (Cobre / WTI / Brent / Oro)")
    if hash_japon != hashes_previos.get("japon"):
        novedades_detalle.append("Datos actualizados en Japón (Banco de Japón / IPC / JGB / USD-JPY)")
        
    hay_novedades = (len(novedades_detalle) > 0) or forzar
    if forzar and len(novedades_detalle) == 0:
        novedades_detalle.append("Ejecución forzada por el usuario (--force)")
        
    # 5. Consolidar latest_drivers.json
    DATA_DRIVERS.mkdir(parents=True, exist_ok=True)
    latest_drivers = consolidar_latest_drivers(usa_data, chile_data, eu_data, comm_data, japon_data)
    with open(LATEST_DRIVERS_FILE, "w", encoding="utf-8") as f:
        json.dump(latest_drivers, f, indent=2, ensure_ascii=False)
        
    # 6. Actualizar estado_ejecucion.json
    DATA_AGENDA.mkdir(parents=True, exist_ok=True)
    ahora_iso = datetime.now(timezone.utc).isoformat()
    nuevo_estado = {
        "ultima_ejecucion_utc": ahora_iso,
        "hay_novedades": hay_novedades,
        "novedades_detalle": novedades_detalle,
        "status_por_fuente": {
            "usa": usa_data.get("tesoro_status", "OK"),
            "chile": chile_data.get("series", {}).get("IMACEC_TOTAL", {}).get("status", "OK"),
            "europa_uk": eu_data.get("series", {}).get("BCE_DFR", {}).get("status", "OK"),
            "commodities": comm_data.get("commodities", {}).get("COBRE_COMEX", {}).get("status", "OK"),
            "japon": japon_data.get("politica_monetaria_boj", {}).get("tasa_politica_overnight", {}).get("status", "OK")
        },
        "hashes_canonicos": nuevos_hashes
    }
    
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(nuevo_estado, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 70)
    print(" 🏁 RESULTADO DE LA EJECUCIÓN MACRO")
    print("=" * 70)
    print(f" • Hay Novedades: {'🟢 SÍ' if hay_novedades else '☕ NO (Datos al día)'}")
    if novedades_detalle:
        for nov in novedades_detalle:
            print(f"   - {nov}")
    print(f" • Snapshot Drivers: {LATEST_DRIVERS_FILE}")
    print(f" • Estado Guardado:  {ESTADO_FILE}")
    print("=" * 70)

    # 7. Disparo aislado del Motor Cuantitativo y Precios OHLC
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    try:
        from scripts.extractor_precios import ejecutar_extraccion_precios
        print("\n[HOOK] Ejecutando extractor de precios OHLC...")
        ejecutar_extraccion_precios()
    except Exception as exc:
        print(f"[WARN HOOK] Extractor de precios OHLC falló de forma aislada: {exc}")

    try:
        from scripts.macro_bias_engine import ejecutar_motor_sesgo
        print("\n[HOOK] Ejecutando Motor Cuantitativo Intermercado (Playbook V2)...")
        ejecutar_motor_sesgo(verbose=True)
    except Exception as exc:
        print(f"[WARN HOOK] Motor Cuantitativo falló de forma aislada: {exc}")

    try:
        from scripts.pronostico_inflacion_japon import construir_pronostico_inflacion
        print("\n[HOOK] Actualizando Modelo de Pronóstico de Inflación Japón...")
        construir_pronostico_inflacion()
    except Exception as exc:
        print(f"[WARN HOOK] Modelo de Pronóstico de Japón falló de forma aislada: {exc}")
    
    return nuevo_estado

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Ingesta Macro")
    parser.add_argument("--force", action="store_true", help="Forzar marca de novedades")
    args = parser.parse_args()
    ejecutar_pipeline(forzar=args.force)
