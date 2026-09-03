"""`get_rates` tiene que seleccionar el símbolo antes de pedirle velas.

MT5 solo sirve `copy_rates_from_pos` para símbolos presentes en el Market Watch
del terminal. Sin `symbol_select` previo, la tool funciona para lo que el
director tenga abierto y falla para el resto, con un mensaje que no dice por qué:

    MT5_UNAVAILABLE: No se pudieron obtener datos para XAUUSD H1:
                     (-1, 'Terminal: Call failed')

Medido el 2026-09-02 desde un proceso nuevo: USDCLP respondió y XAUUSD, US100 y
WTI dieron ese error los tres. No es que el terminal estuviera caído —USDCLP
salió del mismo terminal en la misma llamada— sino que los otros tres no estaban
seleccionados.

Importa porque el sesgo del Playbook cubre cinco activos y la pieza que publica
«vigente hasta X» necesita la serie H1 de cada uno. Una dependencia invisible
del Market Watch deja piezas sin salir sin explicar la causa.

El fake de MetaTrader5 se inyecta en `sys.modules` porque `mt5_client` lo importa
de forma perezosa dentro de la función, justamente para no exigirlo en CI.
"""
from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from market_data_mcp import mt5_client


def _velas(n: int = 200):
    """El dtype estructurado que devuelve `copy_rates_from_pos`."""
    return np.array(
        [(1_700_000_000 + i * 3600, 100.0, 101.0, 99.0, 100.5, 10, 1, 0) for i in range(n)],
        dtype=[
            ("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
            ("close", "f8"), ("tick_volume", "u8"), ("spread", "i4"), ("real_volume", "u8"),
        ],
    )


@pytest.fixture
def mt5_falso(monkeypatch):
    """Un MetaTrader5 de mentira que registra el orden de las llamadas."""
    llamadas: list[str] = []
    fake = types.ModuleType("MetaTrader5")
    fake.TIMEFRAME_H1 = 16385
    fake.TIMEFRAME_D1 = 16408
    fake.seleccionable = True

    def symbol_select(ticker, habilitar):
        llamadas.append(f"symbol_select({ticker})")
        return fake.seleccionable

    def copy_rates_from_pos(ticker, tf, desde, n):
        llamadas.append(f"copy_rates_from_pos({ticker})")
        return _velas(n)

    fake.symbol_select = symbol_select
    fake.copy_rates_from_pos = copy_rates_from_pos
    fake.last_error = lambda: (-1, "Terminal: Call failed")
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    return fake, llamadas


def test_get_rates_selecciona_el_simbolo_antes_de_pedir_velas(mt5_falso):
    fake, llamadas = mt5_falso

    df = mt5_client.get_rates("XAUUSD", "H1", n_bars=200)

    assert len(df) == 200
    assert llamadas == ["symbol_select(XAUUSD)", "copy_rates_from_pos(XAUUSD)"], (
        f"orden incorrecto: {llamadas}"
    )


def test_un_simbolo_que_no_se_puede_seleccionar_lo_dice(mt5_falso):
    """`Terminal: Call failed` no orienta a nadie. El error tiene que nombrar la
    causa real y qué hacer, que es agregarlo al Market Watch."""
    fake, _ = mt5_falso
    fake.seleccionable = False

    with pytest.raises(RuntimeError, match="Market Watch"):
        mt5_client.get_rates("SIMBOLO_RARO", "H1")
