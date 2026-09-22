#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        text = f.read()

    for pattern in [r'v[0-9]\.', r'versión\s+[0-9]', r'version\s+[0-9]', r'\bv2\b', r'\bv3\b']:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        print(f"{pattern}: {len(matches)} matches")
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            print(f"   ...{text[start:end].replace(chr(10), ' ')}...")

if __name__ == "__main__":
    main()
