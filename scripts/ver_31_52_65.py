#!/usr/bin/env python3
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    pos31 = text.find("3.1 · La regla de los dos días")
    print("=== 3.1 ===")
    print(repr(text[pos31:pos31+400]))

    pos52 = text.find("## 5.2 · Retroceso al promedio")
    print("\n=== 5.2 ===")
    print(repr(text[pos52:pos52+700]))

    pos65 = text.find("## 6.5 · Cuando la operación ya va ganando")
    print("\n=== 6.5 ===")
    print(repr(text[pos65:pos65+400]))

if __name__ == "__main__":
    main()
