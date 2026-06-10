"""market-data MCP — Capa de datos confiable para Grupo de Análisis de Mercado.

Tools con contratos de error explícitos. Nunca retorna arrays vacíos ni None silencioso.
Si el dato no está disponible, retorna {"error": "CÓDIGO", "message": "..."}.
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Directorio src/ (parent del paquete market_data_mcp), para el bootstrap de sys.path.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Bootstrap: cuando se corre como script, Python pone el dir del script en
# sys.path[0], no su padre — market_data_mcp necesita el padre para importar.
_pkg_parent = str(PROJECT_DIR)
if _pkg_parent not in sys.path:
    sys.path.insert(0, _pkg_parent)

# .env propio del repo (gitignored) con las credenciales MT5.
# Reemplaza la dependencia de la ruta de un proyecto ajeno (issue #30).
_ENV_PATH = Path(__file__).resolve().parent / ".env"

from fastmcp import FastMCP  # noqa: E402


def _load_env(env_path: Path) -> None:
    """Carga variables del .env propio al entorno (sin pisar las ya definidas)."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


@asynccontextmanager
async def lifespan(server: FastMCP):
    # Cargar credenciales desde el .env propio del repo
    _load_env(_ENV_PATH)

    mt5_ready = False
    try:
        from market_data_mcp.mt5_client import connect
        connect()
        mt5_ready = True
    except Exception as exc:
        print(f"WARN: MT5 no disponible al inicio: {exc}", file=sys.stderr)

    yield {"mt5_ready": mt5_ready, "project_dir": PROJECT_DIR}

    if mt5_ready:
        try:
            from market_data_mcp.mt5_client import disconnect
            disconnect()
        except Exception:  # nosec B110 — shutdown best-effort: si MT5 ya cayó, no hay nada que limpiar
            pass


mcp = FastMCP(
    name="market-data",
    instructions=(
        "Capa de datos confiable para Grupo de Análisis de Mercado. "
        "Tools: get_asset_levels (técnico MT5), obtener_calendario_macro (calendario "
        "macro vía triple feed Fair Economy — ForexFactory + MetalsMine + Energy EXCH; "
        "WebSearch investing.com es fallback si los 3 feeds fallan). "
        "Hora en America/Santiago. Noticias vía WebSearch. "
        "Contrato de error: si el dato no está disponible retorna {'error': 'CÓDIGO', 'message': '...'} "
        "— nunca array vacío, nunca None silencioso."
    ),
    version="1.0.0",
    lifespan=lifespan,
    mask_error_details=False,
)

from market_data_mcp.tools import levels, calendar  # noqa: E402

levels.register(mcp)
calendar.register(mcp)


if __name__ == "__main__":
    mcp.run()
