"""
Script de instalación de dependencias.
Ejecutar en PowerShell: python scripts/setup.py
"""

import subprocess
import sys


DEPENDENCIAS = [
    # Core
    ("MetaTrader5", "Conexión con MT5"),
    ("pandas", "Manipulación de datos"),
    ("pandas_ta", "Indicadores técnicos (RSI, MACD, ATR, etc.)"),

    # Gráficos
    ("mplfinance", "Gráficos de velas profesionales"),
    ("matplotlib", "Motor de gráficos"),

    # Datos complementarios
    ("yfinance", "Datos de Yahoo Finance (backup si MT5 no tiene el activo)"),

    # Utilidades
    ("requests", "HTTP requests"),
]


def instalar():
    print("=" * 60)
    print("📦 Instalando dependencias del Grupo de Análisis de Mercado")
    print("=" * 60)

    errores = []

    for paquete, descripcion in DEPENDENCIAS:
        print(f"\n📥 Instalando {paquete} — {descripcion}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", paquete, "--quiet"],
                stdout=subprocess.DEVNULL
            )
            print(f"   ✅ {paquete} instalado")
        except subprocess.CalledProcessError:
            print(f"   ❌ Error instalando {paquete}")
            errores.append(paquete)

    print("\n" + "=" * 60)
    if errores:
        print(f"⚠️  Paquetes con errores: {', '.join(errores)}")
        print("   Intenta instalarlos manualmente: pip install " + " ".join(errores))
    else:
        print("✅ Todas las dependencias instaladas correctamente")

    print("\n📋 Próximos pasos:")
    print("   1. Abre MetaTrader 5 y logueate en tu broker")
    print("   2. Ejecuta: python scripts/mt5_integration.py")
    print("   3. Si los tickers no coinciden, usa buscar_simbolo() para encontrar los correctos")
    print("   4. Ajusta TICKER_MAP_MT5 en scripts/mt5_integration.py con los nombres de tu broker")


if __name__ == "__main__":
    instalar()
