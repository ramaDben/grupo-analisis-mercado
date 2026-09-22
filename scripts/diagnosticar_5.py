#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    print("1.3:", "seis indicadores (ocho líneas en pantalla: 3 EMA)" in text)
    if not ("seis indicadores (ocho líneas en pantalla: 3 EMA)" in text):
        pos = text.find("1.3")
        print("   Actual 1.3:", repr(text[pos:pos+100]))

    print("3.1:", "shock extremo aplica a la magnitud en la dirección" in text)
    if not ("shock extremo aplica a la magnitud en la dirección" in text):
        pos = text.find("3.1")
        print("   Actual 3.1:", repr(text[pos:pos+350]))

    print("5.2:", "Retroceso a EMA 50" in text)
    if not ("Retroceso a EMA 50" in text):
        pos = text.find("5.2")
        print("   Actual 5.2:", repr(text[pos:pos+500]))

    print("6.5:", ("Entrada + 0,5" in text and "Break-Even" in text))
    if not ("Entrada + 0,5" in text and "Break-Even" in text):
        pos = text.find("6.5")
        print("   Actual 6.5:", repr(text[pos:pos+300]))

    print("L-03:", ("MÓDULO 12" in text and "Ejemplo ilustrativo" in text.lower() and "7a" in text))
    if not ("MÓDULO 12" in text and "Ejemplo ilustrativo" in text.lower() and "7a" in text):
        pos = text.find("MÓDULO 12")
        print("   Actual M12:", repr(text[pos:pos+800]))

if __name__ == "__main__":
    main()
