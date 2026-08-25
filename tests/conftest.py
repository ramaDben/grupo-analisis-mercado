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

# Raíz del proyecto para importar scripts y src.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _PROJECT_ROOT / "src"

if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Ruta del repositorio Genesis para pruebas de integración del puente
_GENESIS_SRC = Path("C:/Users/bbrav/genesis/src")
if _GENESIS_SRC.exists() and str(_GENESIS_SRC) not in sys.path:
    sys.path.insert(0, str(_GENESIS_SRC))


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

    _stub.FastMCP = FastMCP  # ty: ignore[unresolved-attribute]  (stub dinámico de fastmcp)
    sys.modules["fastmcp"] = _stub


class _ToolCollector:
    """Reemplaza al objeto FastMCP dentro de `register()`: captura las funciones
    decoradas con `@mcp.tool` para poder invocarlas directamente en los tests.

    Soporta las dos formas que usa el repo:

    - `@mcp.tool` (sin paréntesis): levels, calendar, chart_objects, positions,
      symbol_spec. La descripción sale del docstring.
    - `@mcp.tool(name=..., description=...)`: macro_bias, curva_tasas. La descripción
      se escribe explícita para que el modelo la lea sin tener que inferirla.

    Antes solo soportaba la primera, así que las tools del segundo estilo no se
    podían invocar desde un test y había que llamar a su lector por debajo,
    dejando el registro sin cubrir.
    """

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}
        self.metadata: dict[str, dict] = {}

    def tool(self, fn=None, **kwargs):
        if fn is not None:  # @mcp.tool (sin paréntesis)
            self.tools[fn.__name__] = fn
            self.metadata[fn.__name__] = {}
            return fn

        def decorador(func):  # @mcp.tool(name=..., description=...)
            nombre = kwargs.get("name", func.__name__)
            self.tools[nombre] = func
            self.metadata[nombre] = kwargs
            return func

        return decorador


@pytest.fixture
def collector() -> _ToolCollector:
    return _ToolCollector()
