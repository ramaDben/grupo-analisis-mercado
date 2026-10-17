"""El techo de espera de agy para redactar una pieza."""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import agy  # noqa: E402


def test_el_timeout_alcanza_para_la_busqueda_web():
    minutos = int(re.fullmatch(r"(\d+)m", agy.TIMEOUT).group(1))
    assert minutos >= 12  # nunca bajo lo que ya medía un encargo real
