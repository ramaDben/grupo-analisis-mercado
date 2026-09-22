#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    pos52 = text.find("## 5.2 · Retroceso al promedio")
    print("=== 5.2 ===")
    print(text[pos52:pos52+700])

    posM12 = text.find("### Estructura Estándar del Registro")
    print("\n=== M12 ===")
    print(text[posM12:posM12+900])

if __name__ == "__main__":
    main()
