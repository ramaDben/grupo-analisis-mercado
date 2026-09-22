#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    pos04 = text.find("0.4 · Expectativas")
    posM1 = text.find("# 🕯️ MÓDULO 1")
    print("=== 0.4 ===")
    print(text[pos04:posM1])

    pos83 = text.find("8.3 · Filtro de noticias")
    pos84 = text.find("## 8.4 · Filtro de confirmación")
    print("=== 8.3 ===")
    print(text[pos83:pos84])

    pos12 = text.find("MÓDULO 12")
    posA1 = text.find("# 📚 ANEXO A1")
    print("=== M12 ===")
    print(text[pos12:posA1])

if __name__ == "__main__":
    main()
