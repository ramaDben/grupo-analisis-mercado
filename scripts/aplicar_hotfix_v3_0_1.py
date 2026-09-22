#!/usr/bin/env python3
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""
scripts/aplicar_hotfix_v3_0_1.py
Aplica los 7 parches técnicos y las directrices editoriales del brief_hotfix_v3_0_1.md
sobre el Manual de Operaciones de Trading Cuantitativo Intermercado.
"""

import sys
import re

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    input_file = "docs/MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    print("Aplicando HOTFIX v3.0.1 (Edición Pública Inicial v1.0)...")

    # =========================================================================
    # 1. DECISIÓN EDITORIAL §2: RETIRO DE CONTROL DE VERSIONES PÚBLICO
    # =========================================================================
    header_v1_pub = """# Manual de Operaciones · Trading Cuantitativo Intermercado
### De la macroeconomía real a tu plataforma MetaTrader 5
**Grupo Inteligencia · Departamento de Estudios y Research**  
*Manual formativo modular para el trader cuantitativo · Edición Pública Inicial · Versión 1.0 · Octubre 2026*

---

> [!CAUTION]"""
    
    # Remover bloque de gobernanza
    text = re.sub(
        r"# Manual de Operaciones · Trading Cuantitativo Intermercado.*?(?=> \[!CAUTION\])",
        header_v1_pub + "\n",
        text,
        flags=re.DOTALL
    )

    # Neutralizar nota del caso M4.4
    text = re.sub(
        r">\s*\*\*Verificado contra reglas v[0-9\.]+\s*—\s*pasa 6/6\*\*\..*?(?=\n\n---)",
        "> **Verificado contra las reglas de este manual — pasa 6/6 filtros**. La pérdida quedó contenida exactamente dentro de los límites del presupuesto institucional.",
        text,
        flags=re.DOTALL
    )

    # =========================================================================
    # 2. HF-01 · BUG DE RENDER: DEDUPLICAR TEXTO EN M7.4
    # =========================================================================
    dup_pattern = r"\*\*Siempre se redondea hacia abajo y con buffer de fricción\.\s*(?:Todos los ejemplos de pérdida del manual usan lote post-redondeo \(ver Caso M4\.4\)\.\s*)+\*\*"
    single_sentence = "**Siempre se redondea hacia abajo y con buffer de fricción.** Todos los ejemplos de pérdida del manual usan lote post-redondeo (ver Caso M4.4)."
    text = re.sub(dup_pattern, single_sentence, text)

    # Limpieza adicional por si quedó fuera del bold
    text = re.sub(
        r"(Todos los ejemplos de pérdida del manual usan lote post-redondeo \(ver Caso M4\.4\)\.\s*){2,}",
        "Todos los ejemplos de pérdida del manual usan lote post-redondeo (ver Caso M4.4). ",
        text
    )

    # =========================================================================
    # 3. HF-03 · D3: SLIPPAGE CAP REGLA ÚNICA
    # =========================================================================
    # En M5.1
    m51_slip_old = r"\* \*\*Regla de Tolerancia de Deslizamiento \(Slippage Cap\)\*\*: Al activarse la orden `BUY_STOP` o `SELL_STOP`.*?(?=\n\n---|\n\n## 5\.2)"
    m51_slip_new = """* **Regla de Tolerancia de Deslizamiento (Slippage Cap)**: Al activarse la orden `BUY_STOP` o `SELL_STOP`, verifica el precio real de llenado (*fill price*). Si el deslizamiento desfavorable del fill supera **0,2 × ATR**, la operación se cancela/cierra de inmediato a mercado sin abrir la posición (cuando el stop es 1,5 × ATR, 0,2 × ATR equivale aproximadamente al 13 % de la distancia al stop). Un deslizamiento excesivo distorsiona la relación riesgo/beneficio y amplifica la pérdida real fuera de presupuesto."""
    text = re.sub(m51_slip_old, m51_slip_new, text, flags=re.DOTALL)

    # En A2 (tabla microestructura)
    text = text.replace(
        "| **Tolerancia máxima de slippage** | **0,2 × ATR (máx 15 % del stop)** | Límite de desfase en órdenes pendientes; cancelar si se supera |",
        "| **Tolerancia máxima de slippage** | **0,2 × ATR** | Límite de deslizamiento en órdenes pendientes; cancelar de inmediato si se supera (equivale a ~13 % de un stop de 1,5×ATR) |"
    )

    # =========================================================================
    # 4. HF-04 · D5: CONFIRMACIÓN CRUZADA WTI NO TAUTOLÓGICA (Δ5d ≥ +1,00%)
    # =========================================================================
    # En M8.4
    text = text.replace(
        "| **WTI y Brent** | Crudo Físico / WTI | El clima es Tormenta, **o** el crudo sube en 5 días (Δ 5d > 0,00 %) | Umbral R3 |",
        "| **WTI y Brent** | Crudo Físico / WTI | Petróleo Δ 5d ≥ +1,00 % (tendencia material, no ruido), **o** el clima es Tormenta (R3) | Umbral R3 |"
    )
    # En A2
    text = text.replace(
        "| **WTI y Brent** | Crudo Físico WTI | Petróleo Δ 5d > 0,00 % (alcista) | Clima Tormenta (R3) |",
        "| **WTI y Brent** | Crudo Físico WTI | Petróleo Δ 5d ≥ +1,00 % (tendencia material confirmada; un umbral > 0 es tautológico al auto-confirmar la señal) | Clima Tormenta (R3) |"
    )

    # =========================================================================
    # 5. HF-05 · M7.3: TABLA DE VALORES Y NOTA DE DÍGITOS MT5
    # =========================================================================
    m73_block_old = r"## 7\.3 · Valor de una unidad por lote, por activo\n\n.*?(?=\n\n## 7\.4)"
    m73_block_new = """## 7.3 · Valor de una unidad por lote, por activo

Medido contra una cuenta en pesos chilenos con tipo de cambio de referencia de **935,60 CLP/USD** (snapshot del 2026-09-04):

| Activo | Contrato | Decimales típicos de cotización | Valor de 1 último decimal por lote (CLP) | Valor de 1 unidad entera por lote (CLP) |
|---|---|---|---|---|
| **USD/CLP** | 100.000 USD | 2 decimales (0,01 CLP) | $1.000 CLP | **$100.000 CLP** |
| **Oro (XAU/USD)** | 100 onzas troy | 2 decimales (0,01 USD) | $935,60 CLP | **$93.560 CLP** |
| **WTI** | 1.000 barriles (o 100 s/broker) | 3 decimales (0,001 USD) | $94 CLP (con 2 dec: $936 CLP) | **$935.600 CLP** (o $93.560 CLP) |
| **Brent** | 1.000 barriles (o 100 s/broker) | 3 decimales (0,001 USD) | $94 CLP (con 2 dec: $936 CLP) | **$935.600 CLP** (o $93.560 CLP) |
| **Nasdaq 100** | Multiplicador 1 | 2 decimales (0,01 pts) | $9,36 CLP | **$935,60 CLP** |

*Nota obligatoria de verificación de dígitos*: Estos valores asumen 2 decimales en USD/CLP y Oro, 3 en WTI/Brent y 2 en Nasdaq 100. Tu broker puede cotizar distinto: verifica en MT5 → click derecho sobre el símbolo → Especificación → Dígitos, y recalcula. Un dígito de diferencia cambia el valor por factor 10."""
    text = re.sub(m73_block_old, m73_block_new, text, flags=re.DOTALL)

    # =========================================================================
    # 6. HF-06 · ELIMINAR PARÁMETRO INVENTADO DE BOLLINGER EN A2
    # =========================================================================
    text = text.replace(
        "| **5.3 Rango** | Ancho de Bandas Bollinger (20,2) | $\\le 2,0 \\times \\text{ATR}$ en H1 | Rechazar setup (bandas en expansión) |\n",
        ""
    )
    text = text.replace(
        "| **5.3 Rango** | Ancho de Bandas Bollinger (20,2) | $\le 2,0 \times \text{ATR}$ en H1 | Rechazar setup (bandas en expansión) |\n",
        ""
    )

    # =========================================================================
    # 7. HF-07 · BORRADOR FINO (PAQUETE MENOR)
    # =========================================================================
    # HF-07.1: M1.3 seis indicadores
    text = text.replace(
        "El método completo se lee con estos cinco.",
        "El método completo se lee con estos seis."
    )

    # HF-07.2: M11 punto 1 confianza inclusive
    text = text.replace(
        "¿Confirmado por 2 días y la confianza ≥ 51,0 % (Umbral maestro Anexo A2 / SSOT)?",
        "¿Confirmado por 2 días y la confianza de 51,0 % o más (mínimo de Anexo A2, inclusive)?"
    )

    # HF-07.3: M5.3 cuerpo vencimiento y colocabilidad
    m53_target = "* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó. Es orden límite y no a mercado."
    m53_replacement = """* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó. Es orden límite y no a mercado.
* **Vencimiento y colocabilidad en MT5**: Vencimiento: 2 velas H1. Si el nivel queda por encima del precio actual, MT5 no permite colocar la BUY_LIMIT: trátala como no colocable y espera la siguiente vela elegible."""
    if "Vencimiento y colocabilidad en MT5" not in text:
        text = text.replace(m53_target, m53_replacement)

    # HF-07.4: M12 fila 7b ganancia neta
    text = text.replace(
        "| **7b. Resultado (Ejemplo Ganador)** | PnL liquidado en dinero y % cuenta | +$9.640 CLP (+0,96 % de la cuenta) |",
        "| **7b. Resultado (Ejemplo Ganador)** | PnL liquidado neto en dinero y % cuenta | +$8.580 CLP (+0,86 % de la cuenta; neto de $1.060 CLP de fricción) |"
    )

    # HF-07.5: M0.4 concordancia nota Oro
    text = text.replace(
        "compensando holgadamente las pérdidas controladas.",
        "que buscan compensar las pérdidas controladas."
    )
    text = text.replace(
        "buscan compensar las pérdidas controladas.",
        "que buscan compensar las pérdidas controladas."
    )

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Hotfix v3.0.1 aplicado exitosamente a {input_file}")

if __name__ == "__main__":
    main()
