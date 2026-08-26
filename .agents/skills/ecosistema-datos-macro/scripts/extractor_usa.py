#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extractor_usa.py
Extractor oficial para el Tesoro de EE.UU. (Fiscal Data API) y Reserva Federal (FRED API).
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "data central" / "DATA USA" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "treasury_fed_data.json"

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_buybacks_tesoro() -> list:
    """Extrae las operaciones de recompra de bonos del dataset oficial de Fiscal Data.

    El dataset es `buybacks_operations` y vive en v1. `treasury_securities_buybacks`
    no existe en la API: devuelve 404 en v1 y en v2, y no figura en el catalogo.
    Su campo de fecha es `operation_date` y no `record_date`, que es el nombre
    generico de otros datasets de Fiscal Data; con ese nombre la API responde 400
    "Invalid query parameter", o sea el mismo fallo por otra causa.
    """
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/buybacks_operations"
    params = {
        "sort": "-operation_date",
        "page[size]": "20"
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_serie_fred(series_id: str, api_key: str) -> dict:
    """Extrae una serie de FRED usando la API oficial si hay key, o endpoint publico."""
    if api_key and api_key != "tu_api_key_de_fred_aqui":
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 30
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        obs = {}
        for item in data.get("observations", []):
            val = item.get("value")
            if val and val != ".":
                try:
                    obs[item["date"]] = float(val)
                except ValueError:
                    pass
        return obs
    else:
        # Fallback a descarga de CSV publico de FRED
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        obs = {}
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) == 2 and parts[1] != ".":
                try:
                    obs[parts[0]] = float(parts[1])
                except ValueError:
                    pass
        # Retornar ultimos 30 ordenados
        fechas_ordenadas = sorted(obs.keys(), reverse=True)[:30]
        return {k: obs[k] for k in fechas_ordenadas}

def ejecutar_extraccion_usa() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Cargar existente si existe
    existente = {}
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existente = json.load(f)
        except Exception:
            existente = {}
            
    ahora_utc = datetime.now(timezone.utc).isoformat()
    resultado = {
        "as_of": ahora_utc,
        "fuente_tesoro": "U.S. Department of the Treasury (Fiscal Data API)",
        "fuente_fed": "Federal Reserve Bank of St. Louis (FRED)",
        "buybacks_operaciones": [],
        "curva_rendimientos_yields": {
            "DGS2": {"nombre": "US 2-Year Treasury Yield", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("DGS2", {}).get("historico", {})},
            "DGS10": {"nombre": "US 10-Year Treasury Yield", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("DGS10", {}).get("historico", {})},
            "DGS30": {"nombre": "US 30-Year Treasury Yield", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("DGS30", {}).get("historico", {})},
            "DFF": {"nombre": "Federal Funds Effective Rate", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("DFF", {}).get("historico", {})},
            "DFII10": {"nombre": "10-Year Treasury Inflation-Indexed Security (TIPS Real Yield)", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("DFII10", {}).get("historico", {})},
            "T10YIE": {"nombre": "10-Year Breakeven Inflation Rate", "unidad": "porcentaje", "historico": existente.get("curva_rendimientos_yields", {}).get("T10YIE", {}).get("historico", {})}
        }
    }
    
    # 1. Extraer Buybacks del Tesoro
    try:
        buybacks = extraer_buybacks_tesoro()
        resultado["buybacks_operaciones"] = buybacks
        resultado["tesoro_status"] = "OK"
    except Exception as e:
        print(f"[WARN] Error extrayendo Buybacks Tesoro: {e}")
        resultado["buybacks_operaciones"] = existente.get("buybacks_operaciones", [])
        resultado["tesoro_status"] = "ERROR_FALLBACK"
        # El motivo viaja con el dato. Imprimirlo por consola no alcanza: el
        # pipeline corre desatendido y esa salida no queda en ningun lado, asi
        # que el fallo se lee despues como un "ERROR_FALLBACK" sin causa.
        resultado["tesoro_error"] = f"{type(e).__name__}: {e}"

    # 2. Extraer Series FRED (Curva y Tasas)
    series_map = {
        "DGS2": "curva_rendimientos_yields",
        "DGS10": "curva_rendimientos_yields",
        "DGS30": "curva_rendimientos_yields",
        "DFF": "curva_rendimientos_yields",
        "DFII10": "curva_rendimientos_yields",
        "T10YIE": "curva_rendimientos_yields"
    }
    
    for sid in series_map.keys():
        try:
            obs = extraer_serie_fred(sid, FRED_API_KEY)
            # UPSERT
            resultado["curva_rendimientos_yields"][sid]["historico"].update(obs)
            resultado["curva_rendimientos_yields"][sid]["status"] = "OK"
        except Exception as e:
            print(f"[WARN] Error extrayendo serie FRED {sid}: {e}")
            resultado["curva_rendimientos_yields"][sid]["status"] = "ERROR_STALE"
            
    # Guardar
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Ingesta USA completada -> {OUTPUT_FILE}")
    return resultado

if __name__ == "__main__":
    ejecutar_extraccion_usa()
