"""Registro de las piezas semanales: qué escenario circuló cada semana y en qué versión.

Se versiona, como la bitácora de planes: es historia de lo que el equipo
comercial le mandó a sus clientes. Cumple dos funciones:

1. **Reúso semanal.** El estado del bot solo guarda el día en curso; la pieza
   semanal vale hasta el lunes siguiente, así que la vigencia se lee de acá.
2. **La foto del lunes.** Cada entrada guarda el escenario con sus niveles: es
   contra lo que el seguimiento diario mide si el escenario avanza, sigue
   vigente o se invalidó.

Una pieza invalidada no se borra: queda marcada, deja de entregarse y la
siguiente petición de la semana arma la versión 2.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "semanal" / "registro.json"


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


def _de(entradas: list[dict[str, Any]], semana: str, ticker: str) -> list[dict[str, Any]]:
    return [e for e in entradas if e["semana"] == semana and e["ticker"] == ticker]


def vigente(semana: str, ticker: str, ruta: Path = RUTA) -> dict[str, Any] | None:
    """La última versión vigente del activo esa semana, si su carpeta sigue en disco."""
    for e in reversed(_de(_leer(ruta), semana, ticker)):
        if e.get("estado") == "vigente":
            return e if (Path(e["dir"]) / "pieza.json").exists() else None
    return None


def anotar(entrada: dict[str, Any], ruta: Path = RUTA) -> dict[str, Any]:
    """Agrega la pieza como la versión siguiente de su semana y activo."""
    entradas = _leer(ruta)
    previas = _de(entradas, entrada["semana"], entrada["ticker"])
    nueva = {**entrada, "version": len(previas) + 1, "estado": "vigente", "seguimientos": []}
    entradas.append(nueva)
    _escribir(ruta, entradas)
    return nueva


def marcar(semana: str, ticker: str, version: int, estado: str, ruta: Path = RUTA) -> None:
    entradas = _leer(ruta)
    for e in _de(entradas, semana, ticker):
        if e["version"] == version:
            e["estado"] = estado
    _escribir(ruta, entradas)


def anotar_seguimiento(semana: str, ticker: str, version: int, seguimiento: dict[str, Any],
                       ruta: Path = RUTA) -> None:
    """Suma un seguimiento a la historia de la pieza: qué estado se le informó a quién y cuándo."""
    entradas = _leer(ruta)
    for e in _de(entradas, semana, ticker):
        if e["version"] == version:
            e.setdefault("seguimientos", []).append(seguimiento)
    _escribir(ruta, entradas)


def vigente_tematica(semana: str, tematica: str, ruta: Path = RUTA) -> dict[str, Any] | None:
    """La pieza vigente de una temática (índices, ETF, acciones), sea cual sea su activo."""
    for e in reversed([e for e in _leer(ruta) if e["semana"] == semana and e.get("tematica") == tematica]):
        if e.get("estado") == "vigente":
            return e if (Path(e["dir"]) / "pieza.json").exists() else None
    return None
