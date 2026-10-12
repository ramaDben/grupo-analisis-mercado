"""Bitácora de los planes entregados: el rastro de lo que el equipo recibió ante un reclamo.

Se versiona: es historia de lo que el equipo recibió, no estado generado, mismo
criterio que la bitácora de envíos del carrusel. Una entrada por informe con plan.

Ya no mide desenlaces: se medían con el Chandelier, que se borró con el enchufe de
estrategia, y una tasa de acierto es justo lo que el director descartó (spec §8.4).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "bitacora_planes_analistas.json"


def _leer(ruta: Path) -> list[dict[str, Any]]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def anotar(pieza: dict[str, Any], html: Path, analista: str, ahora: datetime, ruta: Path = RUTA) -> bool:
    """Una entrada por informe con plan. Devuelve False si la pieza no trae plan."""
    plan = pieza["datos"].get("plan") or {}
    if not plan.get("hay_plan"):
        return False
    entradas = _leer(ruta)
    entradas.append({
        "creada": ahora.isoformat(),
        "tipo": pieza["orden"]["pieza"],
        "ticker": pieza["datos"]["ticker"],
        "alcista": plan["sesgo"] == "Alcista",
        "gatillo": plan["niveles"]["gatillo"],
        "invalidacion": plan["niveles"]["invalidacion"],
        "vela": plan["niveles"]["vela"],
        "analista": analista,
        "huella_html": hashlib.sha256(html.read_bytes()).hexdigest(),
    })
    _escribir(ruta, entradas)
    return True
