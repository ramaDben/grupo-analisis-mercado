#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_graficos_drivers.py
Genera graficos de banner editorial ultra-nitidos (300 DPI) para el reporte de Drivers USD/CLP.
Formato compacto (7.2 x 2.7 in) para flujo perfecto de pagina en PDF.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data central" / "DATA DRIVERS USDCLP" / "graficos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Paleta oficial Grupo Inteligencia
COLOR_BG = "#FFFFFF"
COLOR_TEXT = "#0D0D1A"
COLOR_TEAL = "#53C1AB"
COLOR_CYAN = "#3E91AF"
COLOR_CORAL = "#E76F51"
COLOR_GRID = "#E9ECEF"
COLOR_MUTED = "#737373"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]

def estilizar_ejes(ax):
    ax.set_facecolor(COLOR_BG)
    ax.grid(True, linestyle="--", linewidth=0.6, color=COLOR_GRID, alpha=0.9)
    for spine in ax.spines.values():
        spine.set_color("#D0D7DE")
        spine.set_linewidth(0.7)
    ax.tick_params(colors=COLOR_MUTED, labelsize=8)

# -------------------------------------------------------------
# GRAFICO 1: Treasury 10Y Yield vs DXY (Agosto 2026)
# -------------------------------------------------------------
def generar_grafico_trsy_dxy():
    fechas = pd.date_range(start="2026-08-01", end="2026-08-20", freq="D")
    yield_10y = [4.45, 4.48, 4.52, 4.50, 4.55, 4.58, 4.60, 4.62, 4.65, 4.64,
                 4.66, 4.67, 4.68, 4.68, 4.67, 4.66, 4.67, 4.68, 4.64, 4.63]
    dxy = [97.8, 98.0, 98.2, 98.1, 98.4, 98.6, 98.9, 99.1, 99.3, 99.2,
           99.4, 99.5, 99.6, 99.5, 99.4, 99.3, 99.2, 99.4, 98.9, 98.87]

    fig, ax1 = plt.subplots(figsize=(7.2, 2.5), dpi=300)
    fig.patch.set_facecolor(COLOR_BG)
    
    ax2 = ax1.twinx()
    estilizar_ejes(ax1)
    
    l1 = ax1.plot(fechas, yield_10y, color=COLOR_CYAN, linewidth=2.0, label="US Treasury 10Y (%)", marker="o", markersize=2.5)
    ax1.set_ylabel("Yield 10Y (%)", color=COLOR_CYAN, fontsize=8.5, fontweight="bold")
    ax1.set_ylim(4.35, 4.75)
    
    l2 = ax2.plot(fechas, dxy, color=COLOR_TEAL, linewidth=2.0, linestyle="-", label="DXY Index", marker="s", markersize=2.5)
    ax2.set_ylabel("DXY", color=COLOR_TEAL, fontsize=8.5, fontweight="bold")
    ax2.set_ylim(97.0, 100.0)
    ax2.grid(False)
    ax2.tick_params(colors=COLOR_MUTED, labelsize=8)
    for spine in ax2.spines.values():
        spine.set_color("#D0D7DE")
        
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    
    plt.title("Evolución US 10-Year Treasury Yield vs DXY (Agosto 2026)", fontsize=10, fontweight="bold", color=COLOR_TEXT, pad=8, loc="left")
    
    fecha_evento = pd.Timestamp("2026-08-19")
    ax1.axvline(x=fecha_evento, color=COLOR_CORAL, linestyle=":", linewidth=1.2, alpha=0.9)
    ax1.annotate("Buybacks Tesoro ($4.000M)",
                 xy=(fecha_evento, 4.64), xytext=(pd.Timestamp("2026-08-10"), 4.40),
                 arrowprops=dict(arrowstyle="->", color=COLOR_CORAL, lw=1.0),
                 fontsize=7.5, fontweight="bold", color=COLOR_CORAL,
                 bbox=dict(boxstyle="round,pad=0.2", fc="#FFF3EE", ec=COLOR_CORAL, lw=0.6))

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", frameon=True, facecolor=COLOR_BG, edgecolor="#D0D7DE", fontsize=7.5)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "grafico_trsy10_dxy.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[OK] Generado: {out_path}")

# -------------------------------------------------------------
# GRAFICO 2: Petroleo Brent vs Cobre COMEX (Agosto 2026)
# -------------------------------------------------------------
def generar_grafico_commodities():
    fechas = pd.date_range(start="2026-08-01", end="2026-08-20", freq="D")
    brent = [84.5, 84.8, 85.2, 85.0, 85.9, 86.5, 87.2, 88.0, 88.7, 89.2,
             89.8, 90.4, 91.1, 91.8, 92.5, 93.1, 92.8, 93.5, 92.2, 91.7]
    cobre = [6.65, 6.68, 6.72, 6.70, 6.68, 6.62, 6.58, 6.55, 6.52, 6.50,
             6.48, 6.45, 6.42, 6.40, 6.43, 6.45, 6.42, 6.40, 6.38, 6.40]

    fig, ax1 = plt.subplots(figsize=(7.2, 2.5), dpi=300)
    fig.patch.set_facecolor(COLOR_BG)
    
    ax2 = ax1.twinx()
    estilizar_ejes(ax1)
    
    l1 = ax1.plot(fechas, brent, color=COLOR_CORAL, linewidth=2.0, label="Brent (USD/bbl)", marker="o", markersize=2.5)
    ax1.set_ylabel("Brent (USD/bbl)", color=COLOR_CORAL, fontsize=8.5, fontweight="bold")
    ax1.set_ylim(80.0, 96.0)
    
    l2 = ax2.plot(fechas, cobre, color=COLOR_TEAL, linewidth=2.0, linestyle="--", label="Cobre HG (USD/lb)", marker="^", markersize=2.5)
    ax2.set_ylabel("Cobre (USD/lb)", color=COLOR_TEAL, fontsize=8.5, fontweight="bold")
    ax2.set_ylim(6.20, 6.85)
    ax2.grid(False)
    ax2.tick_params(colors=COLOR_MUTED, labelsize=8)
    for spine in ax2.spines.values():
        spine.set_color("#D0D7DE")
        
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    
    plt.title("Divergencia de Commodities: Petróleo Brent vs Cobre HG (Agosto 2026)", fontsize=10, fontweight="bold", color=COLOR_TEXT, pad=8, loc="left")
    
    ax1.annotate("Sanciones Irán & Ormuz (Brent > $91)",
                 xy=(pd.Timestamp("2026-08-16"), 93.0), xytext=(pd.Timestamp("2026-08-03"), 92.5),
                 arrowprops=dict(arrowstyle="->", color=COLOR_CORAL, lw=1.0),
                 fontsize=7.5, fontweight="bold", color=COLOR_CORAL,
                 bbox=dict(boxstyle="round,pad=0.2", fc="#FFF3EE", ec=COLOR_CORAL, lw=0.6))

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="lower left", frameon=True, facecolor=COLOR_BG, edgecolor="#D0D7DE", fontsize=7.5)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "grafico_commodities_divergencia.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[OK] Generado: {out_path}")

# -------------------------------------------------------------
# GRAFICO 3: Imacec Chile vs Posicion Forward Extranjeros
# -------------------------------------------------------------
def generar_grafico_chile_drivers():
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
    imacec = [-0.8, -0.5, -0.4, -0.6, -0.3, 2.4]
    
    dias_fwd = ["04-Ago", "07-Ago", "11-Ago", "14-Ago", "18-Ago"]
    fwd_pos = [3800, 3950, 4100, 4200, 4450]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.5), dpi=300)
    fig.patch.set_facecolor(COLOR_BG)
    
    estilizar_ejes(ax1)
    colores_barras = [COLOR_CORAL if v < 0 else COLOR_TEAL for v in imacec]
    barras = ax1.bar(meses, imacec, color=colores_barras, width=0.5, edgecolor="#D0D7DE", linewidth=0.6)
    ax1.axhline(0, color="#333333", linewidth=0.6)
    ax1.set_ylabel("Var. Anual (%)", color=COLOR_TEXT, fontsize=8, fontweight="bold")
    ax1.set_title("Imacec H1-2026 (PIB Sem: -0,3%)", fontsize=9, fontweight="bold", color=COLOR_TEXT, loc="left")
    ax1.set_ylim(-1.5, 3.2)
    
    for bar in barras:
        yval = bar.get_height()
        va = "bottom" if yval >= 0 else "top"
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + (0.1 if yval >= 0 else -0.25), f"{yval:+.1f}%",
                 ha="center", va=va, fontsize=7, fontweight="bold", color=COLOR_TEXT)

    estilizar_ejes(ax2)
    ax2.plot(dias_fwd, fwd_pos, color=COLOR_CYAN, marker="o", linewidth=1.8, markersize=3.5)
    ax2.fill_between(dias_fwd, fwd_pos, color=COLOR_CYAN, alpha=0.12)
    ax2.set_ylabel("MM USD", color=COLOR_CYAN, fontsize=8, fontweight="bold")
    ax2.set_title("Compras Netas Forward Extranjeros", fontsize=9, fontweight="bold", color=COLOR_TEXT, loc="left")
    ax2.set_ylim(3500, 4800)
    
    for x, y in zip(dias_fwd, fwd_pos):
        ax2.text(x, y + 60, f"${y:,.0f}M", ha="center", va="bottom", fontsize=7, fontweight="bold", color=COLOR_CYAN)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "grafico_forward_extranjeros_imacec.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[OK] Generado: {out_path}")

def main():
    generar_grafico_trsy_dxy()
    generar_grafico_commodities()
    generar_grafico_chile_drivers()
    print("[SUCCESS] Graficos compactos generados exitosamente.")

if __name__ == "__main__":
    main()
