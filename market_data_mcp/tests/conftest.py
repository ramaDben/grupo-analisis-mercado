"""Configuración de tests para el MCP market-data.

Los tests cubren la lógica de las tools (matemática técnica, contratos de error
y el contrato DEPRECATED) sin necesitar el stack completo de runtime:

- **Stub de `fastmcp`**: las tools hacen `from fastmcp import FastMCP` a nivel de
  módulo, pero `FastMCP` solo se usa como anotación de tipo en `register(mcp)` y
  como instancia en `server.py`. Si `fastmcp` no está instalado, se inyecta un
  stub mínimo para que los módulos importen. Si `fastmcp` SÍ está instalado, se
  usa el real (test más fuerte).
- **sys.path**: se inserta la raíz del proyecto para poder `import market_data_mcp`.
- **Fixture `collector`**: captura las funciones decoradas con `@mcp.tool` sin
  depender del framework, para invocarlas directamente.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

# Raíz del proyecto (…/grupo-analisis-mercado) para importar el paquete.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# Stub mínimo de fastmcp solo si no está disponible en el entorno.
try:  # pragma: no cover - depende del entorno de ejecución
    import fastmcp  # noqa: F401
except ModuleNotFoundError:
    _stub = types.ModuleType("fastmcp")

    class FastMCP:  # placeholder: cubre el uso como tipo y como instancia
        def __init__(self, *args, **kwargs):
            self._kwargs = kwargs

        def tool(self, fn=None, **kwargs):
            # Soporta tanto @mcp.tool como @mcp.tool(...)
            if fn is None:
                return lambda f: f
            return fn

        def run(self, *args, **kwargs):  # no se ejecuta en tests
            raise RuntimeError("FastMCP.run() no debe invocarse en tests")

    _stub.FastMCP = FastMCP
    sys.modules["fastmcp"] = _stub


class _ToolCollector:
    """Reemplaza al objeto FastMCP dentro de `register()`: captura las funciones
    decoradas con `@mcp.tool` para poder invocarlas directamente en los tests."""

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, fn):  # uso en el código: @mcp.tool (sin paréntesis)
        self.tools[fn.__name__] = fn
        return fn


@pytest.fixture
def collector() -> _ToolCollector:
    return _ToolCollector()
