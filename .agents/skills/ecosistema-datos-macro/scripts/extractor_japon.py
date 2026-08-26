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
import re
import csv
import io
import urllib.request
import requests
import ssl
from pathlib import Path
from datetime import datetime, date
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

# Tasa de politica del BoJ. Se toma del dataset de tasas de politica del BIS y
# no del BoJ directamente porque el BoJ no publica la tasa vigente en ningun
# formato estructurado: vive dentro del PDF de cada declaracion. El BIS la
# compila citando la decision textual en su campo `COMPILATION` -"From 17 Jun
# 2026 onwards: the BOJ encourages the uncollateralized overnight call rate to
# remain at around 1.00 percent"-, que es justamente de donde sale la fecha de
# vigencia que hacia falta para medir la frescura del driver.
BIS_CBPOL_JP_URL = (
    "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/D.JP"
    "?format=csv&lastNObservations=5"
)

# Calendario de reuniones de politica monetaria, del propio BoJ.
BOJ_MPM_URL = "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm"

MESES_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

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
def extraer_tasa_politica_boj() -> dict:
    """Tasa de politica del BoJ y la fecha de la decision que la fijo.

    Estaba escrita a mano en el payload (`tasa_politica_actual: 1.00`), en un
    pipeline cuyo principio rector es "100 % del organismo emisor primario". El
    valor resultaba correcto, y ese es justamente el riesgo de un literal: el
    dia que el BoJ mueva la tasa, el pipeline seguiria informando la vieja sin
    una sola senal de que algo quedo atras.

    La fecha de vigencia se parsea de la glosa del BIS. Sin ella no habia con
    que medir la frescura del driver, y el pipeline terminaba fechandolo con su
    PROXIMA reunion: cuando se va a revisar, no cuando se decidio.
    """
    resp = requests.get(BIS_CBPOL_JP_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
    resp.raise_for_status()
    filas = list(csv.DictReader(io.StringIO(resp.text)))
    if not filas:
        raise ValueError("el BIS no devolvio observaciones para la tasa de Japon")

    ultima = filas[-1]
    tasa = float(ultima["OBS_VALUE"])

    vigente_desde = ""
    m = re.search(r"From (\d{1,2}) (\w+) (\d{4}) onwards", ultima.get("COMPILATION", ""))
    if m:
        dia, mes_txt, anio = m.group(1), m.group(2)[:3].lower(), m.group(3)
        if mes_txt in MESES_EN:
            vigente_desde = f"{int(anio):04d}-{MESES_EN[mes_txt]:02d}-{int(dia):02d}"

    return {
        "tasa": tasa,
        "vigente_desde": vigente_desde,
        "observacion": ultima.get("TIME_PERIOD", ""),
        "glosa": ultima.get("COMPILATION", "")[:200],
    }


def extraer_proxima_reunion_boj(hoy=None) -> str:
    """Primera reunion de politica monetaria que todavia no ocurrio.

    Estaba escrita a mano (`proxima_reunion: "2026-09-17"`). La fecha era
    correcta, y ese es el problema: nadie se entera el dia que deja de serlo.

    El calendario del BoJ lista cada reunion como "Sept. 17 (Thurs.), 18
    (Fri.)": dos dias, y el que importa es el primero. El anio no aparece en la
    fila sino como encabezado de la tabla, asi que se deduce del contexto -si el
    mes ya paso, la reunion es del anio siguiente-.
    """
    hoy = hoy or date.today()
    resp = requests.get(BOJ_MPM_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    texto = re.sub(r"<[^>]+>", " ", resp.text)
    texto = re.sub(r"\s+", " ", texto)

    candidatas = []
    for mes_txt, dia in re.findall(r"\b(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\w*\.? (\d{1,2}) \(", texto):
        mes = MESES_EN.get(mes_txt[:3].lower())
        if not mes:
            continue
        for anio in (hoy.year, hoy.year + 1):
            try:
                fecha = date(anio, mes, int(dia))
            except ValueError:
                continue
            if fecha >= hoy:
                candidatas.append(fecha)
                break

    if not candidatas:
        raise ValueError("no se encontro ninguna reunion futura en el calendario del BoJ")
    return min(candidatas).isoformat()


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
    
    print("[1/4] Conectando con Ministerio de Finanzas de Japón (MOF)...")
    datos_mof = extraer_curva_jgb_mof()
    jgb_10y = datos_mof["jgb_10y_yield"]
    print(f"  [OK] Curva MOF capturada exitosamente. JGB 10Y Oficial = {jgb_10y:.3f}% ({datos_mof['ultima_fecha_oficial']})")
    
    print("[2/4] Obteniendo Rendimiento US 10Y y USD/JPY...")
    us_10y, usdjpy_spot = obtener_us_10y_y_fx()
    spread = us_10y - jgb_10y
    print(f"  [OK] US 10Y = {us_10y:.2f}% | Spread US-JGB = {spread:.2f}% ({spread*100:.0f} bps)")
    
    print("[3/4] Consultando política monetaria del BoJ...")
    try:
        boj = extraer_tasa_politica_boj()
        print(f"  [OK] Tasa de política = {boj['tasa']:.2f}% (vigente desde {boj['vigente_desde'] or 's/f'})")
    except Exception as e:
        print(f"  [WARN] No se pudo obtener la tasa del BoJ ({e})")
        boj = {"tasa": None, "vigente_desde": "", "observacion": "", "glosa": ""}

    try:
        proxima_reunion = extraer_proxima_reunion_boj()
        print(f"  [OK] Próxima reunión de política monetaria: {proxima_reunion}")
    except Exception as e:
        print(f"  [WARN] No se pudo leer el calendario del BoJ ({e})")
        proxima_reunion = ""

    print("[4/4] Estructurando Base Maestra de Japón...")
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
            "tasa_politica_actual": boj["tasa"],
            "vigente_desde": boj["vigente_desde"],
            "glosa_decision": boj["glosa"],
            "fuente_tasa": "BIS, dataset WS_CBPOL (compila la decisión del BoJ)",
            "meta_inflacion": 2.00,
            "proxima_reunion": proxima_reunion,
            "fuente_calendario": BOJ_MPM_URL,
            # El sesgo es lectura editorial, no un dato: no lo publica nadie en
            # ningún formato. Se declara como lo que es en vez de mezclarse con
            # los campos ingestados.
            "sesgo": "Hawkish Gradual / Normalización Activa",
            "sesgo_origen": "declarado a mano"
        },
        # NO ingestado. El Statistics Bureau (MIC) no publica el IPC en ningún
        # formato abierto: exige un appId de e-Stat que el proyecto no tiene, y
        # sus rutas de CSV responden 404. FRED no sirve de reemplazo porque sus
        # series de IPC de Japón están congeladas en junio de 2021.
        #
        # Se deja escrito a mano, pero DECLARADO: un dato manual disfrazado de
        # ingesta es peor que uno manual que lo dice. `is_stale` lo vence a los
        # 95 días, así que el día que quede atrás se nota.
        "inflacion_oficial_mic": {
            "origen": "declarado a mano",
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
