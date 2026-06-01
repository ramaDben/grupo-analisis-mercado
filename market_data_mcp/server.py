"""market-data MCP — Capa de datos confiable para Grupo de Análisis de Mercado.

3 tools con contratos de error explícitos. Nunca retorna arrays vacíos ni None silencioso.
Si el dato no está disponible, retorna {"error": "CÓDIGO", "message": "..."}.
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Directorio de este proyecto (grupo-analisis-mercado/)
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Directorio donde vive mt5_client.py y el .env con credenciales
_REPORTE_FLASH_DIR = Path(r"C:\Users\bbrav\Reporte Flash Claude\report_generator")

from fastmcp import FastMCP  # noqa: E402


@asynccontextmanager
async def lifespan(server: FastMCP):
    # Cargar credenciales desde el .env de reporte-flash
    env_path = _REPORTE_FLASH_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    # Inyectar src/ de reporte-flash para que mt5_client sea importable
    src_path = str(_REPORTE_FLASH_DIR / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    mt5_ready = False
    try:
        from mt5_client import connect
        connect()
        mt5_ready = True
    except Exception as exc:
        print(f"WARN: MT5 no disponible al inicio: {exc}", file=sys.stderr)

    yield {"mt5_ready": mt5_ready, "project_dir": PROJECT_DIR}

    if mt5_ready:
        try:
            from mt5_client import disconnect
            disconnect()
        except Exception:
            pass


mcp = FastMCP(
    name="market-data",
    instructions=(
        "Capa de datos confiable para Grupo de Análisis de Mercado. "
        "3 tools: get_asset_levels (técnico MT5), get_economic_events (Finnhub calendario), "
        "get_market_context (Finnhub noticias). "
        "Contrato de error: si el dato no está disponible retorna {'error': 'CÓDIGO', 'message': '...'} "
        "— nunca array vacío, nunca None silencioso."
    ),
    version="1.0.0",
    lifespan=lifespan,
    mask_error_details=False,
)

from market_data_mcp.tools import levels, calendar, context  # noqa: E402

levels.register(mcp)
calendar.register(mcp)
context.register(mcp)


if __name__ == "__main__":
    mcp.run()
