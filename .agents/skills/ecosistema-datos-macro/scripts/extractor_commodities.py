#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extractor_commodities.py
Extractor oficial para Commodities: Petróleo (EIA/FRED), Cobre (COMEX HG) y Oro (LBMA / Yahoo).
Normalización estricta: Cobre en USD/lb y Petróleo en USD/bbl.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
import yfinance as yf

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "data central" / "DATA ORO Y COMMODITIES" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "commodities_data.json"
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_fred_petroleo(series_id: str) -> dict:
    """Extrae serie diaria de Petroleo WTI o Brent de la EIA via FRED API oficial."""
    if FRED_API_KEY and FRED_API_KEY != "tu_api_key_de_fred_aqui":
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
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
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        obs = {}
        lines = resp.text.strip().split("\n")
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) == 2 and parts[1] != ".":
                try:
                    obs[parts[0]] = float(parts[1])
                except ValueError:
                    pass
        fechas_ordenadas = sorted(obs.keys(), reverse=True)[:30]
        return {k: obs[k] for k in fechas_ordenadas}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def extraer_oro_lbma() -> dict:
    """Precio de referencia del Oro desde LBMA, el emisor primario del metal.

    Reemplaza a Stooq, que dejo de servir el CSV: responde HTTP 200 con una
    pagina que exige JavaScript, asi que `raise_for_status()` no dispara y el
    codigo parseaba HTML como si fueran filas. El fallo se notaba recien al
    quedar con cero observaciones, un sintoma a dos pasos de la causa.

    LBMA es ademas la fuente que declara el principio rector de esta skill para
    el Oro. Publica el fixing PM del dia -un precio de referencia acordado en
    subasta, no el spot continuo-, que es lo que corresponde para lectura macro.
    Su JSON trae `v` como [USD, GBP, EUR]: se toma el dolar.
    """
    url = "https://prices.lbma.org.uk/json/gold_pm.json"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    resp.raise_for_status()
    obs = {}
    for fila in resp.json():
        fecha, valores = fila.get("d"), fila.get("v") or []
        if not fecha or not valores or valores[0] in (None, ""):
            continue
        try:
            obs[fecha] = float(valores[0])
        except (ValueError, TypeError):
            continue
    ultimas = sorted(obs, reverse=True)[:30]
    return {k: obs[k] for k in ultimas}


def extraer_oro_stooq() -> dict:
    """Extrae precios diarios de Oro Spot XAU/USD desde Stooq (fuente primaria)."""
    url = "https://stooq.com/q/d/l/?s=xauusd&i=d"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    obs = {}
    lines = resp.text.strip().split("\n")
    if len(lines) > 1:
        # Date,Open,High,Low,Close
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 5:
                try:
                    fecha = parts[0]
                    close_val = float(parts[4])
                    obs[fecha] = close_val
                except ValueError:
                    pass
    fechas_ordenadas = sorted(obs.keys(), reverse=True)[:30]
    return {k: obs[k] for k in fechas_ordenadas}

def extraer_oro_fallback() -> dict:
    """Fallback con yfinance para Oro Spot si Stooq falla."""
    ticker = yf.Ticker("GC=F")
    hist = ticker.history(period="1mo")
    obs = {}
    for idx, row in hist.iterrows():
        fecha = idx.strftime("%Y-%m-%d")
        obs[fecha] = round(float(row["Close"]), 2)
    return obs

def extraer_cobre_hg() -> dict:
    """Extrae Cobre COMEX (HG=F) normalizado en USD/libra."""
    ticker = yf.Ticker("HG=F")
    hist = ticker.history(period="1mo")
    obs = {}
    for idx, row in hist.iterrows():
        fecha = idx.strftime("%Y-%m-%d")
        obs[fecha] = round(float(row["Close"]), 4)
    return obs

def ejecutar_extraccion_commodities() -> dict:
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
        "commodities": {
            "PETROLEO_WTI": {
                "nombre": "Crudo WTI (Cushing, Oklahoma)",
                "unidad": "USD/barril",
                "fuente": "U.S. Energy Information Administration (EIA / FRED DCOILWTICO)",
                "historico": existente.get("commodities", {}).get("PETROLEO_WTI", {}).get("historico", {}),
                # NO_DATA es el estado inicial y "OK" se gana con una observacion
                # recibida. Estaba al reves: arrancaba en "OK" y solo se degradaba
                # ante excepcion, asi que una descarga vacia sin error dejaba el
                # semaforo verde sobre la serie de la semana pasada.
                "status": "NO_DATA"
            },
            "PETROLEO_BRENT": {
                "nombre": "Crudo Brent Europeo",
                "unidad": "USD/barril",
                "fuente": "U.S. Energy Information Administration (EIA / FRED DCOILBRENTEU)",
                "historico": existente.get("commodities", {}).get("PETROLEO_BRENT", {}).get("historico", {}),
                "status": "NO_DATA"
            },
            "COBRE_COMEX": {
                "nombre": "Cobre Grado Alto COMEX (HG)",
                "unidad": "USD/libra",
                "factor_conversion_tonelada": 2204.62,
                "fuente": "COMEX / CME Group",
                "historico": existente.get("commodities", {}).get("COBRE_COMEX", {}).get("historico", {}),
                "status": "NO_DATA"
            },
            "ORO_SPOT": {
                "nombre": "Oro Spot (XAU/USD)",
                "unidad": "USD/onza_troy",
                "fuente": "LBMA Gold Price PM (Primaria) / Yahoo Finance (Fallback)",
                "historico": existente.get("commodities", {}).get("ORO_SPOT", {}).get("historico", {}),
                "status": "NO_DATA"
            }
        }
    }
    
    # 1. Extraer Petroleo WTI
    try:
        wti = extraer_fred_petroleo("DCOILWTICO")
        if wti:
            resultado["commodities"]["PETROLEO_WTI"]["historico"].update(wti)
            resultado["commodities"]["PETROLEO_WTI"]["status"] = "OK"
        else:
            raise ValueError("la fuente no devolvio observaciones")
    except Exception as e:
        print(f"[WARN] Error extrayendo WTI: {e}")
        resultado["commodities"]["PETROLEO_WTI"]["status"] = "ERROR_STALE"
        
    # 2. Extraer Petroleo Brent
    try:
        brent = extraer_fred_petroleo("DCOILBRENTEU")
        if brent:
            resultado["commodities"]["PETROLEO_BRENT"]["historico"].update(brent)
            resultado["commodities"]["PETROLEO_BRENT"]["status"] = "OK"
        else:
            raise ValueError("la fuente no devolvio observaciones")
    except Exception as e:
        print(f"[WARN] Error extrayendo Brent: {e}")
        resultado["commodities"]["PETROLEO_BRENT"]["status"] = "ERROR_STALE"
        
    # 3. Extraer Cobre HG
    try:
        cobre = extraer_cobre_hg()
        if cobre:
            resultado["commodities"]["COBRE_COMEX"]["historico"].update(cobre)
            resultado["commodities"]["COBRE_COMEX"]["status"] = "OK"
        else:
            raise ValueError("la fuente no devolvio observaciones")
    except Exception as e:
        print(f"[WARN] Error extrayendo Cobre HG: {e}")
        resultado["commodities"]["COBRE_COMEX"]["status"] = "ERROR_STALE"
        
    # 4. Extraer Oro Spot (Stooq con fallback a yfinance)
    try:
        oro = extraer_oro_lbma()
        if oro:
            resultado["commodities"]["ORO_SPOT"]["historico"].update(oro)
            resultado["commodities"]["ORO_SPOT"]["status"] = "OK"
        else:
            raise ValueError("LBMA no devolvio datos")
    except Exception as e:
        print(f"[WARN] Error extrayendo Oro de LBMA ({e}), intentando fallback...")
        try:
            oro_fb = extraer_oro_fallback()
            if oro_fb:
                resultado["commodities"]["ORO_SPOT"]["historico"].update(oro_fb)
                resultado["commodities"]["ORO_SPOT"]["status"] = "OK_FALLBACK"
        except Exception as e2:
            print(f"[WARN] Fallback de Oro tambien fallo: {e2}")
            resultado["commodities"]["ORO_SPOT"]["status"] = "ERROR_STALE"
            
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Ingesta Commodities completada -> {OUTPUT_FILE}")
    return resultado

if __name__ == "__main__":
    ejecutar_extraccion_commodities()
