"""Resuelve el segmento y el ancla de un activo para la fuente directa (spec 2026-10-20).

El ancla dice quién es la voz propia del activo (banco central, productor, emisor) y qué términos
tiene que nombrar una nota para contar. Vive en `config/activos.json` para los activos de la casa
y, para los pares de divisas fuera del catálogo, se infiere de `config/segmentos_fuentes.json`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import fuentes

ACTIVOS = RAIZ / "config" / "activos.json"
Ancla = dict[str, Any]


def _entradas(nodo: Any):
    """Todo dict con `ticker_mt5` del árbol, sin importar en qué rama del catálogo viva."""
    if isinstance(nodo, dict):
        if "ticker_mt5" in nodo:
            yield nodo
        for v in nodo.values():
            yield from _entradas(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from _entradas(v)


def _ancla_de_divisa(divisa: str, segmentos: dict[str, Any]) -> Ancla | None:
    ancla = ((segmentos.get("fx") or {}).get("divisas") or {}).get(divisa)
    return dict(ancla) if isinstance(ancla, dict) else None


def _del_catalogo(entry: dict[str, Any], segmentos: dict[str, Any]) -> tuple[str, Ancla] | None:
    segmento = entry.get("segmento")
    if segmento not in fuentes.SEGMENTOS:
        return None
    if segmento == "fx":
        patas = [p for p in (entry["ticker_mt5"][:3], entry["ticker_mt5"][3:6]) if p != "USD"]
        ancla = _ancla_de_divisa(patas[0], segmentos) if len(patas) == 1 else None
    else:
        ancla = entry.get("ancla")
    return (segmento, dict(ancla)) if isinstance(ancla, dict) else None


def segmento_y_ancla(ticker: str, ruta_activos: Path = ACTIVOS,
                     segmentos: dict[str, Any] | None = None) -> tuple[str, Ancla] | None:
    segmentos = segmentos if segmentos is not None else fuentes.cargar_segmentos()
    try:
        catalogo = json.loads(Path(ruta_activos).read_text(encoding="utf-8"))
    except FileNotFoundError:
        catalogo = {}
    for entry in _entradas(catalogo):
        if entry["ticker_mt5"] == ticker:
            if entry.get("segmento"):
                return _del_catalogo(entry, segmentos)
            break  # esta en el catalogo pero sin segmento: se resuelve por el par, si lo es
    t = ticker.upper()
    if len(t) == 6 and t.isalpha() and "USD" in (t[:3], t[3:]):
        patas = [p for p in (t[:3], t[3:]) if p != "USD"]
        ancla = _ancla_de_divisa(patas[0], segmentos) if len(patas) == 1 else None
        if ancla:
            return "fx", ancla
    return None


def anclas_del_catalogo(ruta_activos: Path = ACTIVOS,
                        segmentos: dict[str, Any] | None = None) -> dict[str, tuple[str, Ancla]]:
    segmentos = segmentos if segmentos is not None else fuentes.cargar_segmentos()
    catalogo = json.loads(Path(ruta_activos).read_text(encoding="utf-8"))
    salida: dict[str, tuple[str, Ancla]] = {}
    for entry in _entradas(catalogo):
        resuelto = _del_catalogo(entry, segmentos) if entry.get("segmento") else None
        if resuelto:
            salida[entry["ticker_mt5"]] = resuelto
    return salida


def consultas(ancla: Ancla) -> list[str]:
    """Hasta cuatro consultas: una por entidad y una `site:` por cada uno de los tres primeros dominios."""
    termino = (ancla.get("terminos_ancla") or [ancla["nombre"]])[0]
    qs = [f"{e} {termino}" for e in ancla.get("entidades", [])]
    qs += [f"site:{d} {ancla['nombre']}" for d in ancla.get("dominios", [])[:3]]
    return qs[:4]


def aviso_sin_ancla(ticker: str) -> str:
    return (f"No tengo una fuente propia definida para {ticker}, así que no puedo armar el análisis "
            f"con fuente directa. No gasté tu cupo. Si lo necesitas, pídele al director que lo declare "
            f"en el catálogo.")
