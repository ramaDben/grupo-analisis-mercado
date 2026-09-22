#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    snippets = [
        ("M3.4", text.find("3.4 · Cuando el clima"), 300),
        ("M5.2", text.find("## 5.2 · Retroceso al promedio"), 800),
        ("M5.3", text.find("## 5.3 · Rebote en rango"), 800),
        ("M6.5", text.find("## 6.5 · Cuando la operación"), 400),
        ("M7.1", text.find("## 7.1 · La regla: el 1 %"), 600),
        ("M8.3", text.find("## 8.3 · Filtro de noticias"), 800),
        ("A1", text.find("Racha (drawdown)"), 300),
    ]
    for name, pos, length in snippets:
        print(f"\n--- {name} (pos {pos}) ---")
        if pos != -1:
            print(text[pos:pos+length])

if __name__ == "__main__":
    main()
