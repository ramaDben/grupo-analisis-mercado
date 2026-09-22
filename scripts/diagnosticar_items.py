#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    print("--- Checking L-02 (0.4) ---")
    pos = text.find("0.4 · Expectativas")
    print(text[pos:pos+400])

    print("\n--- Checking L-03 (M12) ---")
    pos = text.find("MÓDULO 12")
    print(text[pos:pos+800])

    print("\n--- Checking 1.3 ---")
    pos = text.find("1.3 · Los")
    print(text[pos:pos+200])

    print("\n--- Checking 3.1 ---")
    pos = text.find("3.1 · La regla")
    print(text[pos:pos+400])

    print("\n--- Checking 5.2 ---")
    pos = text.find("5.2 · Retroceso")
    print(text[pos:pos+600])

    print("\n--- Checking 6.4 ---")
    pos = text.find("6.4 · La salida")
    print(text[pos:pos+400])

    print("\n--- Checking 6.5 ---")
    pos = text.find("6.5 · Cuando la")
    print(text[pos:pos+400])

    print("\n--- Checking 8.3 ---")
    pos = text.find("8.3 · Filtro")
    print(text[pos:pos+600])

if __name__ == "__main__":
    main()
