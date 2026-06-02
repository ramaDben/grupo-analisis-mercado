"""Smoke test del server: importa y verifica el bootstrap de sys.path.

server.py inserta la raíz del proyecto en sys.path[0] cuando se corre como
script (para que `market_data_mcp` sea importable). Este test congela ese
comportamiento y confirma que el módulo carga y registra el objeto MCP sin
ejecutar el lifespan (que requiere MT5).
"""
from __future__ import annotations

import importlib
import sys


def test_server_importa_y_expone_mcp():
    server = importlib.import_module("market_data_mcp.server")
    assert server.mcp is not None
    # El bootstrap deja la raíz del proyecto disponible en sys.path.
    assert str(server.PROJECT_DIR) in sys.path
