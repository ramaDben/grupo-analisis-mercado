#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("--- Searching for 65 % ---")
    for i, line in enumerate(lines):
        if "65" in line:
            print(f"L{i+1}: {line.strip()}")

    print("\n--- Searching for garantiza / jamás / garantizadamente ---")
    for i, line in enumerate(lines):
        if any(w in line.lower() for w in ["garantiza", "jamás", "jamas", "garantizadamente"]):
            print(f"L{i+1}: {line.strip()}")

if __name__ == "__main__":
    main()
