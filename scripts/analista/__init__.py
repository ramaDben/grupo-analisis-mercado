"""Bot de Telegram para analistas: piezas a pedido en HTML, con versión por trader.

Spec: docs/superpowers/specs/2026-10-08-bot-telegram-analistas-design.md.

Los módulos hermanos de `scripts/` (screener_gi, pipeline_avisos, guardrails...) se
importan por nombre, igual que cuando se corren como script. Por eso el paquete
pone `scripts/` y `src/` en el path al importarse: `pipeline_datos` importa
`guardrails.cuenta` de forma perezosa y fallaba desde cualquier otro punto de entrada.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "src", RAIZ / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
