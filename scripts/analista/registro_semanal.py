"""Registro de la foto semanal: qué análisis circuló cada semana y qué seguimientos se informaron.

Se versiona, como la bitácora de despachos: es historia de lo que el equipo comercial le
mandó a sus clientes. Cumple dos funciones (spec 2026-10-12-oportunidad-semanal §5):

1. **Reúso semanal.** El estado del bot solo guarda el día en curso, y la foto vale toda la
   semana: el segundo pedido entrega la misma, para todos los ejecutivos.
2. **La foto del lunes.** `/seguimiento` mide contra los precios de esta foto, no contra una
   lectura recalculada.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "semanal" / "registro.json"


class RegistroDanado(ValueError):
    """El registro no se puede leer: no se sigue, para no pisarlo."""


def _leer(ruta: Path) -> list[dict[str, Any]]:
    """Solo un archivo ausente es un registro vacío. Un JSON corrupto levanta: si se
    tratara como vacío, la próxima escritura borraría toda la historia."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        raise RegistroDanado(f"registro semanal corrupto, no se sobrescribe: {ruta}") from e


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def foto(semana: str, ruta: Path = RUTA) -> dict[str, Any] | None:
    """La foto de la semana, si su carpeta sigue en disco."""
    for e in reversed(_leer(ruta)):
        if e["semana"] == semana:
            return e if (Path(e["dir"]) / "pieza.json").exists() else None
    return None


def anotar_foto(semana: str, dir_pedido: Path, creada: datetime, tickers: list[str],
                ruta: Path = RUTA) -> dict[str, Any]:
    entradas = _leer(ruta)
    nueva = {"semana": semana, "dir": str(dir_pedido), "creada": creada.isoformat(),
             "tickers": list(tickers), "seguimientos": []}
    entradas.append(nueva)
    _escribir(ruta, entradas)
    return nueva


def anotar_seguimiento(semana: str, ticker: str, seguimiento: dict[str, Any],
                       ruta: Path = RUTA) -> None:
    """Suma un seguimiento a la última foto de la semana: qué se informó, a quién y cuándo."""
    entradas = _leer(ruta)
    for e in reversed(entradas):
        if e["semana"] == semana:
            e.setdefault("seguimientos", []).append({"ticker": ticker, **seguimiento})
            break
    _escribir(ruta, entradas)
