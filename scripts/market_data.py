"""
Obtención de datos de mercado usando Yahoo Finance.
Proporciona precios actuales, máximos/mínimos del día y variación porcentual
para los activos cubiertos por el Grupo de Análisis de Mercado.
"""

import json
from datetime import datetime, date
from pathlib import Path

# pip install yfinance
try:
    import yfinance as yf
    YFINANCE_DISPONIBLE = True
except ImportError:
    YFINANCE_DISPONIBLE = False
    print("⚠️ yfinance no instalado. Ejecuta: pip install yfinance")

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

# Mapeo de tickers internos a tickers de Yahoo Finance
TICKER_MAP = {
    "USD/CLP": "USDCLP=X",
    "XAU/USD": "GC=F",
    "WTI": "CL=F",
    "US100": "NQ=F",
    "COBRE": "HG=F",
    "DXY": "DX-Y.NYB",
    "TREASURY_10Y": "^TNX"
}


def obtener_precio(ticker_interno: str) -> dict:
    """
    Obtiene datos de precio actuales para un activo.

    Args:
        ticker_interno: Ticker interno (ej: "USD/CLP", "XAU/USD")

    Returns:
        Dict con precio actual, máximo, mínimo, variación y cierre anterior.
    """
    if not YFINANCE_DISPONIBLE:
        return {"error": "yfinance no disponible", "ticker": ticker_interno}

    ticker_yahoo = TICKER_MAP.get(ticker_interno)
    if not ticker_yahoo:
        return {"error": f"Ticker no mapeado: {ticker_interno}"}

    try:
        activo = yf.Ticker(ticker_yahoo)
        info = activo.fast_info

        # Obtener datos del día
        hist = activo.history(period="2d")

        if hist.empty:
            return {"error": f"Sin datos para {ticker_interno}", "ticker_yahoo": ticker_yahoo}

        ultimo = hist.iloc[-1]
        cierre_anterior = hist.iloc[-2]["Close"] if len(hist) > 1 else ultimo["Open"]
        variacion_pct = ((ultimo["Close"] - cierre_anterior) / cierre_anterior) * 100

        return {
            "ticker": ticker_interno,
            "ticker_yahoo": ticker_yahoo,
            "precio_actual": round(float(ultimo["Close"]), 4),
            "maximo_dia": round(float(ultimo["High"]), 4),
            "minimo_dia": round(float(ultimo["Low"]), 4),
            "apertura": round(float(ultimo["Open"]), 4),
            "cierre_anterior": round(float(cierre_anterior), 4),
            "variacion_pct": round(variacion_pct, 2),
            "volumen": int(ultimo["Volume"]) if ultimo["Volume"] > 0 else None,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

    except Exception as e:
        return {
            "ticker": ticker_interno,
            "error": str(e)
        }


def obtener_todos_precios(tickers: list = None) -> dict:
    """
    Obtiene precios de múltiples activos.

    Args:
        tickers: Lista de tickers internos. Si es None, usa los 4 principales.

    Returns:
        Dict con datos de cada activo.
    """
    if tickers is None:
        tickers = ["USD/CLP", "XAU/USD", "WTI", "US100"]

    resultado = {
        "fecha": date.today().isoformat(),
        "hora_consulta": datetime.now().strftime("%H:%M CLT"),
        "precios": {}
    }

    for ticker in tickers:
        print(f"  Obteniendo {ticker}...")
        resultado["precios"][ticker] = obtener_precio(ticker)

    return resultado


def obtener_tipo_cambio_usdclp() -> float:
    """
    Obtiene el tipo de cambio USD/CLP actual.
    Se usa para convertir TP y SL a pesos chilenos.
    """
    datos = obtener_precio("USD/CLP")
    if datos.get("error"):
        print(f"⚠️ Error obteniendo USD/CLP: {datos['error']}")
        return 950.0  # Fallback conservador
    return datos["precio_actual"]


def obtener_datos_complementarios() -> dict:
    """Obtiene datos de activos complementarios (cobre, DXY, Treasury)."""
    tickers = ["COBRE", "DXY", "TREASURY_10Y"]
    resultado = {}
    for ticker in tickers:
        resultado[ticker] = obtener_precio(ticker)
    return resultado


def guardar_precios(datos: dict) -> Path:
    """Guarda los precios del día en data/niveles_hoy.json."""
    ruta = DATA_DIR / "niveles_hoy.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta


if __name__ == "__main__":
    print("📊 Obteniendo datos de mercado...\n")

    # Precios principales
    datos = obtener_todos_precios()

    print("\n📈 Precios del día:")
    print("-" * 50)
    for ticker, info in datos["precios"].items():
        if info.get("error"):
            print(f"  {ticker}: ❌ {info['error']}")
        else:
            emoji = "📈" if info["variacion_pct"] > 0 else "📉" if info["variacion_pct"] < 0 else "➡️"
            print(f"  {emoji} {ticker}: {info['precio_actual']} ({info['variacion_pct']:+.2f}%)")
            print(f"     Rango: {info['minimo_dia']} - {info['maximo_dia']}")

    # Guardar
    ruta = guardar_precios(datos)
    print(f"\n✅ Datos guardados en {ruta}")

    # Tipo de cambio para conversión CLP
    tc = obtener_tipo_cambio_usdclp()
    print(f"\n💱 Tipo de cambio USD/CLP: {tc}")
