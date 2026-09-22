#!/usr/bin/env python3
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    items = [
        'seis indicadores',
        'shock extremo',
        '65 %',
        'garantizadamente',
        'Retroceso a EMA 50',
        'BUY_LIMIT no es colocable',
        'Incompatibilidad de Rama B',
        'Chandelier',
        'mitad del camino',
        'presupuesto NO acota',
        'blackout',
        'Exposición agregada a tasas',
        'Racha (drawdown)',
        '1,00'
    ]
    for item in items:
        found = item in text
        print(f'{item}: {found}')
        if not found:
            words = item.split()
            for w in words:
                pos = text.find(w)
                if pos != -1:
                    snippet = text[max(0, pos-30):min(len(text), pos+60)].replace('\n', ' ')
                    print(f'   found partial "{w}": ...{snippet}...')
                    break

if __name__ == "__main__":
    main()
