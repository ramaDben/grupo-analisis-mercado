"""Búsqueda de un símbolo en el terminal, sin MT5 real."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import simbolos as sm  # noqa: E402


class Mt5Falso:
    def __init__(self, simbolos):
        self._s = simbolos

    def symbols_get(self):
        return self._s


def _s(name, description, digits=2):
    return SimpleNamespace(name=name, description=description, digits=digits)


def test_busca_sin_importar_mayusculas_y_devuelve_el_nombre_exacto():
    mt5 = Mt5Falso([_s("US100.spot", "US Tech 100", 2), _s("TGT.US", "Target Corp", 2)])
    assert sm.buscar("us100.SPOT", mt5=mt5) == {"ticker": "US100.spot", "descripcion": "US Tech 100", "digits": 2}


def test_un_simbolo_que_no_existe_devuelve_none():
    assert sm.buscar("pizza", mt5=Mt5Falso([_s("XAUUSD", "Gold")])) is None


def test_el_nombre_del_terminal_se_limpia_sin_traducirlo():
    assert sm.limpiar("  Target \x00 Corp\n") == "Target Corp"
    assert sm.limpiar("x" * 200) == "x" * 60


def test_sin_terminal_se_dice():
    class Roto:
        def symbols_get(self):
            raise OSError("sin IPC")

    with pytest.raises(sm.TerminalNoDisponible):
        sm.buscar("oro", mt5=Roto())


def test_un_listado_none_es_terminal_caido_y_no_simbolo_inexistente():
    class SinListado:
        def symbols_get(self):
            return None

    with pytest.raises(sm.TerminalNoDisponible):
        sm.buscar("oro", mt5=SinListado())
