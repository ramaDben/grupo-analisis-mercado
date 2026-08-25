#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_grafico_usdjpy_cpi.py
Generador institucional de gráfico técnico para USD/JPY (D1)
con confluencia de Retrocesos de Fibonacci (38.2%, 50.0%, 61.8%) y EMAs 50 / 100 / 200.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import yfinance as yf

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data central" / "DATA JAPON" / "reportes_generados"
OUTPUT_FILE = OUTPUT_DIR / "chart_usdjpy_cpi.png"

def generar_chart_usdjpy():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Descargar histórico diario de USD/JPY
    df = yf.download("JPY=X", period="5mo", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_100"] = df["Close"].ewm(span=100, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()
    
    # Últimas 75 sesiones para lectura limpia
    sub = df.tail(75).copy()
    
    recent_high = sub["High"].max()
    recent_low = sub["Low"].min()
    
    fibo_382 = recent_high - (recent_high - recent_low) * 0.382
    fibo_500 = recent_high - (recent_high - recent_low) * 0.500
    fibo_618 = recent_high - (recent_high - recent_low) * 0.618
    
    last_close = float(sub["Close"].iloc[-1])
    last_ema50 = float(sub["EMA_50"].iloc[-1])
    last_ema100 = float(sub["EMA_100"].iloc[-1])
    
    # 2. Configuración de Estilo Institucional Oscuro
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=300)
    fig.patch.set_facecolor("#0D0D1A")
    ax.set_facecolor("#0D0D1A")
    
    dates = sub.index
    
    # Curva de Precio y Sombras
    ax.plot(dates, sub["Close"], label="USD/JPY Cierre D1", color="#FFFFFF", linewidth=2.0, zorder=5)
    ax.fill_between(dates, sub["Low"], sub["High"], color="#3E91AF", alpha=0.15, zorder=2)
    
    # EMAs Diarias
    ax.plot(dates, sub["EMA_50"], label=f"EMA 50 D1 ({last_ema50:.3f})", color="#E76F51", linewidth=1.6, linestyle="--", alpha=0.9, zorder=4)
    ax.plot(dates, sub["EMA_100"], label=f"EMA 100 D1 ({last_ema100:.3f})", color="#53C1AB", linewidth=1.8, linestyle="-", alpha=0.95, zorder=4)
    ax.plot(dates, sub["EMA_200"], label="EMA 200 D1", color="#F4A261", linewidth=1.4, linestyle=":", alpha=0.8, zorder=3)
    
    # Líneas de Fibonacci
    ax.axhline(fibo_500, color="#53C1AB", linestyle="-.", linewidth=1.5, alpha=0.9, label=f"Fibo 50.0% ({fibo_500:.3f}) — Nivel Clave")
    ax.axhline(fibo_382, color="#E76F51", linestyle=":", linewidth=1.2, alpha=0.75, label=f"Fibo 38.2% ({fibo_382:.3f}) — Resistencia")
    ax.axhline(fibo_618, color="#3E91AF", linestyle=":", linewidth=1.2, alpha=0.75, label=f"Fibo 61.8% ({fibo_618:.3f}) — Soporte")
    
    # Zona de Confluencia Destacada (Fibo 50% + EMA 100)
    ax.axhspan(min(fibo_500, last_ema100) - 0.15, max(fibo_500, last_ema100) + 0.15, color="#53C1AB", alpha=0.18, label="Zona Confluencia Decisión")
    
    # Marcador de Precio Actual
    last_date = dates[-1]
    ax.scatter([last_date], [last_close], color="#53C1AB", s=90, zorder=6, edgecolors="#FFFFFF")
    ax.annotate(
        f" Actual: {last_close:.3f}\n Test Fibo 50% / EMA 100",
        xy=(last_date, last_close),
        xytext=(last_date - pd.Timedelta(days=12), last_close - 1.8),
        color="#FFFFFF",
        fontsize=9.5,
        fontweight="bold",
        arrowprops=dict(facecolor="#53C1AB", edgecolor="#53C1AB", arrowstyle="->", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#16162A", edgecolor="#53C1AB", lw=1.2)
    )
    
    # Formato de Ejes
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.grid(True, linestyle=":", alpha=0.25, color="#E9ECEF")
    
    # Títulos y Etiquetas
    plt.title("USD/JPY (Dólar / Yen Japonés) — Temporalidad Diaria (D1)\nConfluencia Técnica: 50.0% Fibonacci & EMA 100 previo al IPC de Japón", 
              fontsize=12.5, fontweight="bold", color="#FFFFFF", pad=14, loc="left")
    
    ax.set_ylabel("Cotización (JPY)", color="#E9ECEF", fontsize=10, fontweight="bold")
    ax.tick_params(colors="#E9ECEF", labelsize=9)
    
    for spine in ax.spines.values():
        spine.set_color("#2A2A40")
        
    ax.legend(loc="lower left", fontsize=8.2, facecolor="#16162A", edgecolor="#3A3A55", framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    
    print(f"[OK] Gráfico generado exitosamente en: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    generar_chart_usdjpy()
