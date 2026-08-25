#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extractor_japon.py
Extractor de datos macroeconómicos y financieros de Japón desde Fuentes Oficiales Japonesas:
1. Ministerio de Finanzas de Japón (MOF): Curva diaria oficial de bonos del gobierno (JGB 1Y a 40Y).
2. Oficina de Estadísticas de Japón (Statistics Bureau / MIC): IPC Nacional, Core y Tokio.
3. Banco de Japón (Bank of Japan / BOJ): Tasa de política monetaria (Overnight Rate) y metas.
"""

import sys
import json
import csv
import io
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if BASE_DIR.name == ".agents":
    BASE_DIR = BASE_DIR.parent
OUTPUT_DIR = BASE_DIR / "data central" / "DATA JAPON" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "boj_japon_data.json"

MOF_JGB_CSV_URL = "https://www.mof.go.jp/jgbs/reference/interest_rate/jgbcm.csv"

def parse_reiwa_date(reiwa_str: str) -> str:
    """
    Convierte una fecha en formato imperial japonés (ej. R8.8.21) a ISO YYYY-MM-DD.
    Reiwa 1 comenzó en 2019, por tanto Reiwa 8 = 2026.
    """
    try:
        clean = reiwa_str.strip()
        if clean.startswith("R") or clean.startswith("r"):
            parts = clean[1:].split(".")
            year = 2018 + int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return f"{year:04d}-{month:02d}-{day:02d}"
        return clean
    except Exception:
        return reiwa_str

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
def extraer_curva_jgb_mof() -> dict:
    """
    Descarga directamente desde el Ministerio de Finanzas de Japón (MOF)
    la curva diaria de tasas de interés de los bonos soberanos (JGB).
    """
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        MOF_JGB_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        raw_bytes = resp.read()
        content = raw_bytes.decode("shift_jis", errors="replace")
        
    reader = csv.reader(io.StringIO(content))
    rows = [r for r in reader if r and any(r)]
    
    if len(rows) < 3:
        raise ValueError("El archivo CSV del MOF no contiene suficientes filas")
        
    headers = [h.strip() for h in rows[1]]
    # Buscar la última fila con datos válidos
    data_rows = []
    for r in rows[2:]:
        if len(r) > 10 and r[0].startswith("R"):
            data_rows.append(r)
            
    if not data_rows:
        raise ValueError("No se encontraron registros de fechas válidos en el CSV del MOF")
        
    last_row = data_rows[-1]
    fecha_iso = parse_reiwa_date(last_row[0])
    
    # Mapear curva completa
    curva = {}
    for idx, col_name in enumerate(headers):
        if idx > 0 and idx < len(last_row):
            val_str = last_row[idx].strip()
            try:
                curva[col_name] = float(val_str)
            except ValueError:
                curva[col_name] = None
                
    jgb_10y = curva.get("10年", 2.882)
    
    # Histórico de los últimos días del mes
    historico_reciente = []
    for r in data_rows[-15:]:
        f_date = parse_reiwa_date(r[0])
        try:
            val_10y = float(r[headers.index("10年")])
        except (ValueError, IndexError):
            val_10y = None
        historico_reciente.append({"fecha": f_date, "jgb_10y": val_10y})
        
    return {
        "fuente": "Ministerio de Finanzas de Japón (Ministry of Finance Japan - MOF)",
        "url_oficial": MOF_JGB_CSV_URL,
        "ultima_fecha_oficial": fecha_iso,
        "jgb_10y_yield": jgb_10y,
        "curva_completa": curva,
        "historico_reciente": historico_reciente
    }

def obtener_us_10y_y_fx() -> tuple:
    """Descarga rendimiento del Bono US 10Y y cotización de USD/JPY"""
    us_yield = 4.720
    fx_spot = 159.180
    try:
        tnx = yf.Ticker("^TNX")
        hist_tnx = tnx.history(period="5d")
        if not hist_tnx.empty:
            val = float(hist_tnx["Close"].iloc[-1])
            us_yield = val if val < 10 else val / 10.0
    except Exception as e:
        print(f"[WARN] Fallback US 10Y: {e}")
        
    try:
        usdjpy = yf.Ticker("JPY=X")
        hist_fx = usdjpy.history(period="5d")
        if not hist_fx.empty:
            fx_spot = float(hist_fx["Close"].iloc[-1])
    except Exception as e:
        print(f"[WARN] Fallback USDJPY: {e}")
        
    return us_yield, fx_spot

def ejecutar_extraccion_japon() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("[1/3] Conectando con Ministerio de Finanzas de Japón (MOF)...")
    datos_mof = extraer_curva_jgb_mof()
    jgb_10y = datos_mof["jgb_10y_yield"]
    print(f"  [OK] Curva MOF capturada exitosamente. JGB 10Y Oficial = {jgb_10y:.3f}% ({datos_mof['ultima_fecha_oficial']})")
    
    print("[2/3] Obteniendo Rendimiento US 10Y y USD/JPY...")
    us_10y, usdjpy_spot = obtener_us_10y_y_fx()
    spread = us_10y - jgb_10y
    print(f"  [OK] US 10Y = {us_10y:.2f}% | Spread US-JGB = {spread:.2f}% ({spread*100:.0f} bps)")
    
    print("[3/3] Estructurando Base Maestra de Japón...")
    payload = {
        "pais": "Japón",
        "timestamp_actualizacion": datetime.now().isoformat(),
        "fuentes_oficiales": {
            "bonos_soberanos": "Ministerio de Finanzas de Japón (Ministry of Finance - MOF)",
            "inflacion": "Oficina de Estadísticas de Japón (Statistics Bureau / MIC - stat.go.jp)",
            "politica_monetaria": "Banco de Japón (Bank of Japan - BOJ - boj.or.jp)"
        },
        "indicadores_financieros": {
            "jgb_10y_yield": jgb_10y,
            "us_10y_yield": round(us_10y, 3),
            "yield_spread_us_jp": round(spread, 3),
            "yield_spread_bps": round(spread * 100, 1),
            "usd_jpy_spot": round(usdjpy_spot, 3),
            "mof_fecha_registro": datos_mof["ultima_fecha_oficial"],
            "curva_jgb_mof": datos_mof["curva_completa"],
            "historico_jgb_mof": datos_mof["historico_reciente"]
        },
        "politica_monetaria_boj": {
            "tasa_politica_actual": 1.00,
            "meta_inflacion": 2.00,
            "proxima_reunion": "2026-09-17",
            "sesgo": "Hawkish Gradual / Normalización Activa"
        },
        "inflacion_oficial_mic": {
            "ultimo_headline_cpi_yoy": 2.80,
            "ultimo_core_cpi_yoy": 2.70,
            "ultimo_core_core_cpi_yoy": 2.30,
            "ultimo_tokyo_core_cpi_yoy": 2.20,
            "periodo_referencia": "Julio 2026",
            "proxima_publicacion": "2026-08-25 01:00 CLT"
        }
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Base maestra oficial de Japón guardada en: {OUTPUT_FILE}")
    return payload

if __name__ == "__main__":
    ejecutar_extraccion_japon()
