"""Índices de referencia del contexto macro: VIX y dólar global (DXY).

Decisión del director, 2026-09-28: los tres canales recibían la misma imagen del
bono a 10 años, y eso se lee repetitivo y mecánico. Cada canal cuelga ahora de un
indicador distinto:

- el de avisos, del **VIX**, la volatilidad que el mercado espera para el S&P 500.
  Es el termómetro de cautela de toda la sesión, no de un activo;
- el de divisas, del **DXY**, el dólar contra una canasta de seis monedas.

Ninguno de los dos es un símbolo del broker, así que no salen de MT5. La fuente
es yfinance, con los tickers oficiales (`^VIX` de Cboe y `DX-Y.NYB` de ICE). Para
estas series yfinance entrega el cierre diario y la barra del día en curso, así
que la última observación es la de hoy mientras el mercado está abierto.

Contrato: **nunca lanza**. Una fuente caída, una respuesta vacía o menos de dos
cierres devuelven [], y el contexto macro cae al bono a 10 años.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from datetime import date
from typing import Any

TICKERS_YF: dict[str, str] = {
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
}


def _descargar(ticker: str) -> list[tuple[date, float]]:
    import yfinance as yf

    hist = yf.Ticker(ticker).history(period="2mo", interval="1d")
    return [(i.date(), float(c)) for i, c in hist["Close"].items()]


def serie_diaria(
    codigo: str,
    n: int = 15,
    *,
    descargar: Callable[[str], list[tuple[date, float]]] | None = None,
) -> list[tuple[date, float]]:
    """Los últimos `n` cierres diarios del índice, del más antiguo al más reciente."""
    ticker = TICKERS_YF.get(codigo)
    if ticker is None:
        return []
    try:
        crudo: Any = (descargar or _descargar)(ticker)
        puntos = sorted(
            (d, round(float(v), 3)) for d, v in crudo
            if v is not None and math.isfinite(float(v))
        )
    except Exception:  # noqa: BLE001 - contrato: nunca lanza
        return []
    return puntos[-n:] if len(puntos) >= 2 else []
