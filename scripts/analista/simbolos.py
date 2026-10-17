"""Símbolos del terminal MT5: el universo del bot es lo que el broker ofrece.

El catálogo (`config/activos.json`) aporta nombre y `digits` de los activos de la casa; un
símbolo fuera de él se acepta con lo que dice el terminal (spec 2026-10-16 §3). El nombre es el
`description` del terminal tal como viene: traducirlo es peligroso («Target» pasa a «Blanco»)
y pedírselo a agy lo haría cambiar entre corridas.
"""
from __future__ import annotations

from typing import Any

NOMBRE_MAX = 60


class TerminalNoDisponible(RuntimeError):
    """MT5 no responde: no se puede confirmar si el símbolo existe."""


def limpiar(texto: str) -> str:
    """Solo caracteres imprimibles y espacios simples; recorta a `NOMBRE_MAX`."""
    imprimible = "".join(c if c.isprintable() else " " for c in texto)
    return " ".join(imprimible.split())[:NOMBRE_MAX]


def buscar(texto: str, mt5: Any = None) -> dict[str, Any] | None:
    """El símbolo del terminal que se llama `texto` (sin distinguir mayúsculas), o None."""
    try:
        if mt5 is None:
            from market_data_mcp import mt5_client

            mt5_client.connect()
            import MetaTrader5 as mt5  # noqa: PLC0415
        simbolos = mt5.symbols_get()
    except Exception as exc:  # noqa: BLE001
        raise TerminalNoDisponible(f"MT5 no respondió ({exc.__class__.__name__})") from exc
    quiero = texto.strip().lower()
    for s in simbolos or ():
        if s.name.lower() == quiero:
            return {"ticker": s.name, "descripcion": limpiar(s.description or s.name), "digits": int(s.digits)}
    return None
