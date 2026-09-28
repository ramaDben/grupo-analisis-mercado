"""Rendimientos del Tesoro de EE.UU. en vivo, al contado.

Existe porque la curva de FRED llega con uno a cuatro días hábiles de rezago:
el 2026-09-28, un lunes con el mercado moviéndose, el carrusel publicaba
"+24 bps en 5 días (dato al 24 Sep)". El director pidió datos frescos del día
(decisión del 2026-09-28).

La fuente es la cotización al contado de CNBC, que también cotiza en el
premercado. El índice de CBOE que da yfinance (`^TNX`) solo se calcula en
sesión regular, así que antes de las 09:30 NY entrega el cierre de ayer.

Se rescató de la cuarentena de AGY (`4204c60`) quitando lo que no se usa: la
tasa real TIPS (el director la sacó del carrusel), la paridad de Fisher y la
consulta a la Fed de Nueva York. Una diferencia de fondo con aquel código es que
este hace **una** consulta para todas las series, no una por serie.

Contrato: **nunca lanza**. Si la fuente se cae o responde algo que no se puede
leer, devuelve {} y el consumidor cae a FRED con la fecha del dato a la vista.
Una cotización sin valor se omite, y una sin cierre previo trae la variación en
`None`, nunca en 0: cero significa "no se movió" y None significa "no sé".
"""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

SIMBOLOS_CNBC: dict[str, str] = {
    "DGS2": "US2Y",
    "DGS5": "US5Y",
    "DGS10": "US10Y",
    "DGS30": "US30Y",
}

FUENTE = "CNBC · rendimiento al contado"
_URL = (
    "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    "?symbols={simbolos}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json"
)


def _descargar(url: str, timeout: float = 4.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - URL fija
        return resp.read()


def _porcentaje(texto: Any) -> float | None:
    limpio = str(texto or "").replace("%", "").strip()
    if not limpio:
        return None
    try:
        return round(float(limpio), 3)
    except ValueError:
        return None


def rendimientos_en_vivo(
    series: Iterable[str] = ("DGS2", "DGS10"),
    *,
    descargar: Callable[[str], bytes] | None = None,
) -> dict[str, dict[str, Any]]:
    """El último rendimiento de cada serie, con su cierre previo y la variación del día."""
    por_simbolo = {SIMBOLOS_CNBC[s]: s for s in series if s in SIMBOLOS_CNBC}
    if not por_simbolo:
        return {}
    url = _URL.format(simbolos="|".join(por_simbolo))
    try:
        crudo = (descargar or _descargar)(url)
        quotes = json.loads(crudo.decode("utf-8"))["FormattedQuoteResult"]["FormattedQuote"]
    except Exception:  # noqa: BLE001 - contrato: nunca lanza
        return {}

    resultado: dict[str, dict[str, Any]] = {}
    for q in quotes if isinstance(quotes, list) else []:
        codigo = por_simbolo.get(str(q.get("symbol", "")))
        valor = _porcentaje(q.get("last"))
        if codigo is None or valor is None:
            continue
        try:
            momento = datetime.fromisoformat(str(q.get("last_time", "")).replace(".000", ""))
        except ValueError:
            continue
        previo = _porcentaje(q.get("previous_day_closing"))
        resultado[codigo] = {
            "valor": valor,
            "cierre_previo": previo,
            "delta_1d_bps": round((valor - previo) * 100, 1) if previo is not None else None,
            "momento": momento,
            "fecha": momento.date().isoformat(),
            "fuente": FUENTE,
        }
    return resultado
