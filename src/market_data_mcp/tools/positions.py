"""Tool get_open_positions — lee las operaciones abiertas del terminal MT5.

Extrae la operación tal como está en la caja de herramientas del terminal
(entrada, stop, take profit, volumen y resultado flotante), sin derivarla ni
recalcularla. Es la fuente para las piezas que comunican una operación del
equipo al grupo: los precios los pone el terminal, no el analista.

Los precios se redondean a los `digits` del catálogo (regla MT5 de CLAUDE.md) y
el resultado viene en la moneda de la cuenta (la reporta MT5, no se asume).
Contrato de error explícito; nunca array vacío silencioso.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastmcp import FastMCP

from market_data_mcp.catalog import VALID_TICKERS

# Constantes de MT5: POSITION_TYPE_BUY == 0, POSITION_TYPE_SELL == 1. Se mapean
# por valor para no importar MetaTrader5 en este módulo (mismo criterio de
# import perezoso que mt5_client, que mantiene el paquete importable en CI).
_TIPO_POSICION = {0: "BUY", 1: "SELL"}

# MT5 usa 0.0 para "sin stop/objetivo definido", no None.
_SIN_DEFINIR = 0.0


def _hora_servidor(epoch: int) -> str:
    """Epoch de MT5 a 'YYYY-MM-DD HH:MM' en hora del servidor, sin conversiones.

    El terminal entrega los tiempos en la hora de su servidor; se formatean tal
    cual (el broker actual coincide con hora Chile). Se usa `timezone.utc` solo
    para que el formateo no aplique el offset de la máquina local.
    """
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def _serializar(pos: Any, digits: int) -> dict[str, Any]:
    """Una posición de MT5 al dict de salida, con precios a los digits del activo."""
    return {
        "ticket": int(pos.ticket),
        "tipo": _TIPO_POSICION.get(int(pos.type), f"TIPO_{int(pos.type)}"),
        "volumen": float(pos.volume),
        "entrada": round(float(pos.price_open), digits),
        "sl": round(float(pos.sl), digits) if float(pos.sl) != _SIN_DEFINIR else None,
        "tp": round(float(pos.tp), digits) if float(pos.tp) != _SIN_DEFINIR else None,
        "precio_actual": round(float(pos.price_current), digits),
        "resultado_flotante": round(float(pos.profit), 2),
        "swap": round(float(pos.swap), 2),
        "abierta_en": _hora_servidor(int(pos.time)),
        "comentario": str(pos.comment or ""),
    }


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_open_positions(ticker: str) -> dict[str, Any]:
        """Operaciones abiertas en el terminal MT5 para un símbolo.

        Lee la posición tal como está en la caja de herramientas (no la calcula):
        entrada, stop loss, take profit, volumen, precio actual y resultado
        flotante en la moneda de la cuenta. Requiere el terminal MT5 abierto y
        conectado.

        Args:
            ticker: Símbolo MT5 del catálogo (ej: EURUSD, USDCLP, XAUUSD, #AAPL).

        Returns:
            Dict con: ticker, total, moneda, posiciones (lista con ticket, tipo,
            volumen, entrada, sl, tp, precio_actual, resultado_flotante, swap,
            abierta_en, comentario), tz_note, source. O {"error": "CÓDIGO",
            "message": "..."} si el dato no está disponible.
        """
        if ticker not in VALID_TICKERS:
            return {
                "error": "TICKER_NOT_FOUND",
                "message": (
                    f"'{ticker}' no está en el catálogo de activos. "
                    f"Tickers válidos: {', '.join(sorted(VALID_TICKERS.keys()))}"
                ),
            }

        from market_data_mcp.mt5_client import get_account_currency, get_positions

        try:
            posiciones = get_positions(ticker)
        except Exception as exc:  # noqa: BLE001 — MT5 lanza excepciones no tipadas
            return {
                "error": "MT5_UNAVAILABLE",
                "message": f"No se pudo consultar las posiciones de {ticker} en MT5: {exc}",
            }

        if posiciones is None:
            return {
                "error": "MT5_UNAVAILABLE",
                "message": (
                    f"MT5 no respondió a la consulta de posiciones de {ticker}. "
                    "¿El terminal está abierto y conectado?"
                ),
            }

        if len(posiciones) == 0:
            return {
                "error": "NO_OPEN_POSITIONS",
                "message": (
                    f"No hay operaciones abiertas para {ticker} en el terminal. "
                    "Verifica el símbolo o la pestaña Operaciones de la caja de herramientas."
                ),
            }

        digits = VALID_TICKERS[ticker]
        return {
            "ticker": ticker,
            "total": len(posiciones),
            "moneda": get_account_currency(),
            "posiciones": [_serializar(p, digits) for p in posiciones],
            "tz_note": "hora servidor MT5 (broker actual = hora Chile)",
            "source": "mt5_terminal",
        }
