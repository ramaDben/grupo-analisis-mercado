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
        "Tools: get_asset_levels (técnico MT5 auto), get_chart_objects (niveles "
        "dibujados a mano por el director en MT5: soportes/resistencias, trendlines, "
        "canales, rectángulos, retrocesos de Fibonacci con el precio de cada nivel "
        "+ screenshot, vía Service ChartObjectsExporter), "
        "get_open_positions (operaciones abiertas del terminal: entrada, stop, take "
        "profit, volumen y resultado flotante tal como están en la caja de "
        "herramientas — no se recalculan), "
        "obtener_calendario_macro (calendario "
        "económico Investing.com — Chile + EE.UU. + China + Zona Euro, con resultado "
        "real `actual` y clasificación mejor/peor/en_linea; WebSearch es fallback si la fuente falla), "
        "get_symbol_spec (especificaciones de contrato de un símbolo — trade_mode, "
        "digits, volumen mínimo/paso, tamaño de contrato — y sesiones de trading "
        "semanales en hora Chile; con `fecha` responde de forma determinista si el "
        "activo opera ese día, cruzando patrón semanal MT5 + calendario de feriados "
        "NYSE versionado + trade_mode en vivo), "
        "get_curva_tasas (curva soberana de EE.UU. desde data central/: rendimientos "
        "del Tesoro 2Y/10Y/30Y, tasa efectiva de fondos federales, tasa real TIPS 10Y "
        "y compensación por inflación, con variación en puntos base a 1 y 5 días, más "
        "la pendiente 2s10s; incluye procedencia y frescura, y un delta que no se "
        "puede calcular viene null y nunca 0). "
        "Hora en America/Santiago. Noticias vía WebSearch. "
        "Contrato de error: si el dato no está disponible retorna {'error': 'CÓDIGO', 'message': '...'} "
        "— nunca array vacío, nunca None silencioso."
    ),
    version="1.0.0",
    lifespan=lifespan,
    mask_error_details=False,
)

from market_data_mcp.tools import levels, calendar, chart_objects, positions, symbol_spec, macro_bias, curva_tasas  # noqa: E402

levels.register(mcp)
calendar.register(mcp)
chart_objects.register(mcp)
positions.register(mcp)
symbol_spec.register(mcp)
macro_bias.register(mcp)
curva_tasas.register(mcp)


if __name__ == "__main__":
    mcp.run()
