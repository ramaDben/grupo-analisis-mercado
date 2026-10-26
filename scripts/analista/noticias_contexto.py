"""Candidatas de noticias multi-fuente (FXStreet e Investing.com) para contexto de seguimiento."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from analista import noticia as nt

FEEDS_INVESTING: tuple[str, ...] = (
    "https://es.investing.com/rss/news.rss",
    "https://es.investing.com/rss/market_overview.rss",
)
MAX_CANDIDATAS = 6


def candidatas(ticker: str, nombre: str, ahora: datetime,
               leer: Callable[[str], str] = nt.leer_feed,
               ruta_patrones: Path = nt.PATRONES_FX) -> tuple[list[dict[str, Any]], list[str]]:
    """Junta notas del activo de FXStreet e Investing.com de los últimos 3 días.

    Alterna fuentes para dar diversidad, deduplica por URL y corta en MAX_CANDIDATAS.
    """
    fx_lista, caidos_fx = nt.candidatas_de_feeds(
        nt.FEEDS_FX, "FXStreet", ticker, nombre, ahora, leer=leer, ruta_patrones=ruta_patrones
    )
    inv_lista, caidos_inv = nt.candidatas_de_feeds(
        FEEDS_INVESTING, "Investing.com", ticker, nombre, ahora, leer=leer, ruta_patrones=ruta_patrones
    )

    avisos: list[str] = []
    if caidos_fx == len(nt.FEEDS_FX):
        avisos.append("No pude leer FXStreet: el medio no respondió.")
    if caidos_inv == len(FEEDS_INVESTING):
        avisos.append("No pude leer Investing.com: el medio no respondió.")

    # Alternar listas para dar diversidad de fuentes
    combinadas: list[dict[str, Any]] = []
    max_len = max(len(fx_lista), len(inv_lista))
    for i in range(max_len):
        if i < len(fx_lista):
            combinadas.append(fx_lista[i])
        if i < len(inv_lista):
            combinadas.append(inv_lista[i])

    # Deduplicar por URL respetando el orden
    vistas: set[str] = set()
    unicas: list[dict[str, Any]] = []
    for c in combinadas:
        if c["url"] not in vistas:
            vistas.add(c["url"])
            unicas.append(c)

    return unicas[:MAX_CANDIDATAS], avisos
