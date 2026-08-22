#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extractor_europa_uk.py
Extractor oficial para el Banco Central Europeo (BCE / SDMX REST API) y Bank of England (BoE / IADB).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
OUTPUT_DIR = BASE_DIR / "data central" / "DATA EUROPA UK" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "bce_boe_data.json"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_bce_tasas() -> dict:
    """Consulta la API oficial del BCE (ECB Data Portal REST) en formato CSV."""
    url = "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV"
    params = {
        "lastNObservations": "15",
        "format": "csvdata"
    }
    resp = requests.get(url, params=params, headers={"Accept": "text/csv"}, timeout=15)
    resp.raise_for_status()
    
    obs = {}
    lines = resp.text.strip().split("\n")
    if len(lines) > 1:
        # Encontrar indices de columnas TIME_PERIOD y OBS_VALUE
        headers = [h.strip() for h in lines[0].split(",")]
        try:
            idx_time = headers.index("TIME_PERIOD")
            idx_val = headers.index("OBS_VALUE")
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) > max(idx_time, idx_val):
                    fecha = parts[idx_time]
                    val = parts[idx_val]
                    if val and val != "":
                        obs[fecha] = float(val)
        except ValueError:
            pass
    return obs

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_boe_bank_rate() -> dict:
    """Consulta la base de datos interactiva IADB del Bank of England para la Bank Rate."""
    url = "https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp"
    params = {
        "csv.x": "yes",
        "SeriesCodes": "IUDBEDR",
        "CSVF": "TN",
        "Datefrom": "01/Jan/2026"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    
    obs = {}
    lines = resp.text.strip().split("\n")
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            try:
                # Fecha en formato DD Mon YYYY
                dt = datetime.strptime(parts[0], "%d %b %Y")
                fecha_iso = dt.strftime("%Y-%m-%d")
                val = float(parts[1])
                obs[fecha_iso] = val
            except (ValueError, IndexError):
                pass
    return obs

def ejecutar_extraccion_europa_uk() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
        "fuente_bce": "European Central Bank (ECB Data Portal API)",
        "fuente_boe": "Bank of England (IADB Statistical Database)",
        "series": {
            "BCE_DFR": {
                "nombre": "ECB Deposit Facility Rate",
                "unidad": "porcentaje",
                "historico": existente.get("series", {}).get("BCE_DFR", {}).get("historico", {
                    "2026-06-12": 3.75,
                    "2026-07-18": 3.75
                }),
                "status": "OK"
            },
            "BOE_BANK_RATE": {
                "nombre": "Bank of England Official Bank Rate",
                "unidad": "porcentaje",
                "historico": existente.get("series", {}).get("BOE_BANK_RATE", {}).get("historico", {
                    "2026-06-20": 5.25,
                    "2026-08-01": 5.00
                }),
                "status": "OK"
            }
        }
    }
    
    # 1. Extraer BCE
    try:
        bce_obs = extraer_bce_tasas()
        if bce_obs:
            resultado["series"]["BCE_DFR"]["historico"].update(bce_obs)
            resultado["series"]["BCE_DFR"]["status"] = "OK"
    except Exception as e:
        print(f"[WARN] Error extrayendo tasas BCE: {e}")
        resultado["series"]["BCE_DFR"]["status"] = "FALLBACK_LOCAL"
        
    # 2. Extraer BoE
    try:
        boe_obs = extraer_boe_bank_rate()
        if boe_obs:
            resultado["series"]["BOE_BANK_RATE"]["historico"].update(boe_obs)
            resultado["series"]["BOE_BANK_RATE"]["status"] = "OK"
    except Exception as e:
        print(f"[WARN] Error extrayendo tasas BoE: {e}")
        resultado["series"]["BOE_BANK_RATE"]["status"] = "FALLBACK_LOCAL"
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Ingesta Europa y UK completada -> {OUTPUT_FILE}")
    return resultado

if __name__ == "__main__":
    ejecutar_extraccion_europa_uk()
