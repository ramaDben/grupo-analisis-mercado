#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generar_graficos.py
Motor modular de generacion de graficos editoriales para Grupo Inteligencia.
Estandar de diseno estricto: Formato banner compacto (7.2 x 2.5 in), 300 DPI,
paleta corporativa institucional y exportacion automatica sin desbordes.
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
    """Aplica el tema visual limpio de Grupo Inteligencia a los ejes."""
    ax.set_facecolor(COLOR_BG)
    ax.grid(True, linestyle="--", linewidth=0.6, color=COLOR_GRID, alpha=0.9)
    for spine in ax.spines.values():
        spine.set_color("#D0D7DE")
        spine.set_linewidth(0.7)
    ax.tick_params(colors=COLOR_MUTED, labelsize=8)

def crear_figura_banner(ancho=7.2, alto=2.5, dpi=300):
    """Crea una figura calibrada para fluir sin cortes en hojas A4."""
    fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)
    fig.patch.set_facecolor(COLOR_BG)
    estilizar_ejes(ax)
    return fig, ax

def exportar_grafico(fig, target_path: Path):
    """Guarda el grafico con resolucion de impresion 300 DPI."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(target_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Grafico editorial exportado -> {target_path}")

def main():
    print("Motor de graficos editoriales de Grupo Inteligencia listo y calibrado a 7.2x2.5 in.")

if __name__ == "__main__":
    main()
