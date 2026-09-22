#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('scripts/compilar_manual_pdf.py', 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace(
        '<div class="cover-badge">SISTEMA CUANTITATIVO V2.1</div>',
        '<div class="cover-badge">SISTEMA CUANTITATIVO · EDICIÓN PÚBLICA</div>'
    )
    text = text.replace(
        '<div>Manual Oficial para el Trader Cuantitativo · Versi&oacute;n 2.1</div>',
        '<div>Manual Oficial para el Trader Cuantitativo · Edici&oacute;n P&uacute;blica Inicial · Versi&oacute;n 1.0</div>'
    )
    text = text.replace(
        'Manual de Operaciones v2.1 compilado a 300 DPI.',
        'Manual de Operaciones (Edición Pública Inicial v1.0) compilado a 300 DPI.'
    )

    with open('scripts/compilar_manual_pdf.py', 'w', encoding='utf-8') as f:
        f.write(text)

    print("compilar_manual_pdf.py actualizado para Edición Pública v1.0 exitosamente.")

if __name__ == "__main__":
    main()
