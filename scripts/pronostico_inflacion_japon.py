#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pronostico_inflacion_japon.py
Puntero y CLI directo para el Motor de Pronóstico de Inflación de Japón (BoJ y USD/JPY).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPT = BASE_DIR / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts" / "pronostico_inflacion_japon.py"

if str(SKILL_SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPT.parent))

from pronostico_inflacion_japon import construir_pronostico_inflacion, imprimir_resumen_pronostico

if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Construcción Pronóstico Inflación Japón")
    parser.add_argument("--json", action="store_true", help="Salida pura en JSON")
    args = parser.parse_args()

    res = construir_pronostico_inflacion()
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        imprimir_resumen_pronostico(res)
