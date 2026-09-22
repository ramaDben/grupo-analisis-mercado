# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
import re
from pathlib import Path

p = Path(r"C:\Users\bbrav\grupo-analisis-mercado\docs\MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md")
text = p.read_text(encoding="utf-8")

# Clean LaTeX remnants
text = text.replace(r"$\rightarrow$", "→")
text = text.replace(r"\rightarrow", "→")
text = text.replace(r"\le", "≤")
text = text.replace(r"\ge", "≥")
text = text.replace(r"\times", "×")
text = text.replace(r"\Delta", "Δ")
text = text.replace(r"\rho", "ρ")
text = text.replace(r"\text{ATR}", "ATR")
text = text.replace(r"\text{H1}", "H1")
text = text.replace(r"\text{D1}", "D1")
text = text.replace(r"\text{Capital}", "Capital")
text = text.replace(r"\text{Presupuesto Neto de Precio}", "Presupuesto Neto de Precio")
text = text.replace(r"\text{Buffer de Fricción Reservado}", "Buffer de Fricción Reservado")
text = text.replace("50 \\le 21,5", "50 ≤ 2,5")
text = text.replace("50 ≤ 21,5", "50 ≤ 2,5")
text = text.replace(r"<\$3.163.000", "< $3.163.000")
text = text.replace(r"\$", "$")

# Replace lingering single $
for pat in [
    r"\$1,5 × ATR\(14\) en H1\$",
    r"\$2,5 × ATR\(20\) en D1\$",
    r"\$0,90 %\$",
    r"\$0,10 %\$",
    r"\$1,0 %\$",
    r"\$2,1 × ATR\$",
    r"\$68 %\$",
    r"\$1,5 × ATR\$",
    r"\$3,62\$",
    r"\$0,2 × ATR\$",
    r"\$15 %\$",
    r"\$2,20 %\$",
    r"\$4,70 %\$",
    r"\$4,25 %\$",
    r"\$\+1,8 %\$",
    r"\$3×\$",
    r"\$5×\$",
    r"\$0,25 %\$",
]:
    clean_pat = pat.replace(r"\$", "").replace(r"\(", "(").replace(r"\)", ")")
    text = re.sub(pat, clean_pat, text)

# Final general cleanup for any $word$ that isn't currency
text = re.sub(r"\$([0-9]+,[0-9]+ [^\$]+)\$", r"\1", text)
text = text.replace("$$", "")

p.write_text(text, encoding="utf-8")
print("Cleaned LaTeX residues successfully!")
