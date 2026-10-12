"""Tool get_lectura — la `Lectura` de la estrategia activa (enchufe de estrategia, fase 3).

Es la lectura técnica con la que se publica: dirección, estado, líneas con su papel, el
nivel que se vigila, el que invalida, el objetivo, los tres escenarios y la regla de
salida. Sale de la estrategia nombrada en `config/estrategia.json`, comparada contra la
referencia de la semana si el activo la tiene (`scripts/referencia_semanal.py`).

`get_asset_levels` queda como dato crudo (indicadores y pivotes) para auditoría: ningún
pipeline de producción decide con ella (spec §6).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from market_data_mcp.catalog import VALID_TICKERS

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

SANTIAGO = ZoneInfo("America/Santiago")


def obtener_lectura(ticker: str, estrategia=None, lector=None, ahora: datetime | None = None,
                    base: Path | None = None) -> dict[str, Any]:
    """La lectura del día de `ticker`, o el contrato de error. Nunca lanza."""
    import referencia_semanal as rs
    from estrategia import registro
    from estrategia.contrato import lectura_a_dict

    if ticker not in VALID_TICKERS:
        return {"error": "TICKER_INVALIDO",
                "message": f"{ticker} no está en el catálogo (config/activos.json)"}
    ahora = ahora or datetime.now(tz=SANTIAGO)
    try:
        estrategia = estrategia or registro.activa()
        if lector is None:
            from estrategia.fuente import velas_mt5 as lector
        lectura, _ = rs.lectura_actual(estrategia, ticker, VALID_TICKERS[ticker], lector, ahora,
                                       base=base)
    except Exception as exc:  # noqa: BLE001 - el contrato es devolver el error, no lanzarlo
        return {"error": "LECTURA_NO_DISPONIBLE", "message": f"{type(exc).__name__}: {exc}"}
    return {"ticker": ticker, "estrategia": estrategia.nombre, "semana": rs.semana_de(ahora),
            "lectura": lectura_a_dict(lectura)}


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_lectura(ticker: str) -> dict[str, Any]:
        """La lectura técnica con que se publica un activo, de la estrategia activa.

        Usar esta tool, y no get_asset_levels, para afirmar dirección, niveles o escenarios
        en una pieza. Compara el precio de hoy contra la referencia que fijó el análisis
        semanal; si el activo no tiene referencia esta semana, lee de nuevo.

        Args:
            ticker: Símbolo MT5 del catálogo (ej: XAUUSD, USDCLP, WTI.spot).

        Returns:
            {"ticker", "estrategia", "semana", "lectura"}, con `lectura`: marco, precio,
            direccion (ALCISTA/BAJISTA/LATERAL), estado (TENDENCIA/REBOTE/PRUEBA/RUPTURA/
            RANGO), lineas (rol, tipo, puntos, valor_actual, calidad, toques), vigilar,
            invalidacion, objetivo, escenarios (exactamente tres: ⬆️ ↔️ ⬇️), salida,
            conceptos y avisos. Una diagonal cambia de precio con cada vela: el número que
            se publica es `valor_actual`. O {"error": "CÓDIGO", "message": "..."}.
        """
        return obtener_lectura(ticker)
