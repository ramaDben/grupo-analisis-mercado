import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mt5_integration import (
    conectar_mt5, desconectar_mt5, obtener_precio_actual,
    obtener_velas, calcular_indicadores, identificar_niveles,
)

PLAN = {
    "USD/CLP": ["4H", "1H", "15M"],
    "XAU/USD": ["4H", "1H", "15M"],
    "WTI": ["4H", "1H"],
}

if not conectar_mt5():
    raise SystemExit(1)

salida = {}
try:
    for ticker, tfs in PLAN.items():
        precio = obtener_precio_actual(ticker)
        salida[ticker] = {"precio": precio, "temporalidades": {}}
        for tf in tfs:
            df = obtener_velas(ticker, tf, 200)
            if df.empty:
                salida[ticker]["temporalidades"][tf] = {"error": "sin datos"}
                continue
            df = calcular_indicadores(df, ["rsi", "atr"])
            niveles = identificar_niveles(df)
            ultimo = df.iloc[-1]
            rsi = round(float(ultimo["RSI"]), 1) if "RSI" in df.columns else None
            atr = round(float(ultimo["ATR"]), 4) if "ATR" in df.columns else None
            salida[ticker]["temporalidades"][tf] = {
                "niveles": niveles, "rsi": rsi, "atr": atr,
            }
finally:
    desconectar_mt5()

out = Path(__file__).parent.parent / "data" / "datos_entregables.json"
out.write_text(json.dumps(salida, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps(salida, ensure_ascii=False, indent=2, default=str))
