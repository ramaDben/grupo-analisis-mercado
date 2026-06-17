"""Tool get_chart_objects — lee los objetos dibujados a mano en MT5.

El Service MQL5 `ChartObjectsExporter.mq5` exporta los objetos de todos los
charts abiertos (líneas horizontales, trendlines, canales, rectángulos) más un
screenshot a `Common/Files/chart_objects.json`. Esta tool localiza ese archivo
(vía la env var `MT5_COMMON_FILES`), valida frescura, filtra por símbolo +
timeframe y clasifica las líneas horizontales en soporte/resistencia respecto
al precio actual. Contrato de error explícito; nunca array vacío silencioso.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from market_data_mcp.catalog import VALID_TICKERS

_SANTIAGO = ZoneInfo("America/Santiago")
_OBJECTS_FILE = "chart_objects.json"
# El Service refresca cada ~60 s; si el dato supera este umbral, lo damos por
# obsoleto (terminal cerrado o Service caído). generated_at viene en hora del
# servidor MT5, que en el broker actual coincide con hora Chile.
_STALE_SECONDS = 3600

# Destino de los screenshots: el repo `data/charts/` (gitignored, convención #81).
# El Service MQL5 está sandboxed y solo puede escribir en Common/Files; esta tool
# copia el PNG vigente desde ahí a data/charts para "recibirlo" en el repo. Ruta
# derivada del repo (src/market_data_mcp/tools/chart_objects.py -> raíz), sobre-
# escribible con la env var MT5_CHARTS_DIR.
_REPO_CHARTS_DIR = Path(__file__).resolve().parents[3] / "data" / "charts"


def _common_files_dir() -> str | None:
    """Directorio Common/Files de MT5 desde la env var. None si no está seteada."""
    return os.environ.get("MT5_COMMON_FILES") or None


def _charts_output_dir() -> Path:
    """Directorio donde se reciben los screenshots (data/charts del repo por defecto)."""
    return Path(os.environ["MT5_CHARTS_DIR"]) if os.environ.get("MT5_CHARTS_DIR") else _REPO_CHARTS_DIR


def _recibir_screenshot(common_dir: str, nombre: str) -> str | None:
    """Copia el PNG desde Common/Files a data/charts y devuelve la ruta destino.

    Si el PNG aún no existe en Common/Files (el Service no lo escribió este ciclo)
    o la copia falla, cae a la ruta en Common/Files para no perder la referencia.
    """
    origen = Path(common_dir) / nombre
    if not origen.exists():
        return str(origen)
    destino_dir = _charts_output_dir()
    try:
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / nombre
        shutil.copy2(origen, destino)
        return str(destino)
    except OSError:
        return str(origen)


def _parse_generado(generated_at: str) -> datetime | None:
    """'YYYY-MM-DD HH:MM' (hora servidor MT5 = Chile) a datetime con tz Santiago."""
    try:
        return datetime.strptime(generated_at, "%Y-%m-%d %H:%M").replace(tzinfo=_SANTIAGO)
    except (ValueError, TypeError):
        return None


def _clasificar_hlines(hlines: list[dict], current: float, digits: int) -> tuple[list[float], list[float]]:
    """Separa las líneas horizontales en soportes (< precio) y resistencias (> precio)."""
    soportes = sorted(
        (round(float(h["price"]), digits) for h in hlines if float(h["price"]) < current),
        reverse=True,  # soporte más cercano al precio primero
    )
    resistencias = sorted(
        round(float(h["price"]), digits) for h in hlines if float(h["price"]) > current
    )
    return soportes, resistencias


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_chart_objects(ticker: str, timeframe: str = "H4") -> dict[str, Any]:
        """Niveles dibujados a mano en MT5 + screenshot del gráfico.

        Lee los objetos que el director trazó en el terminal (no los calcula):
        líneas horizontales (clasificadas en soporte/resistencia), trendlines,
        canales y rectángulos de zona. Requiere el Service MQL5
        `ChartObjectsExporter` corriendo y el gráfico del activo abierto en MT5.

        Args:
            ticker: Símbolo MT5 del catálogo (ej: XAUUSD, USDCLP, WTI.spot, #AAPL).
            timeframe: Marco temporal MT5 (M15, H1, H4, D1, …) del gráfico abierto.

        Returns:
            Dict con: ticker, timeframe, current_price, soportes, resistencias,
            trendlines, channels, rectangles, screenshot (ruta absoluta o None),
            generated_at, source. O {"error": "CÓDIGO", "message": "..."} si el
            dato no está disponible.
        """
        if ticker not in VALID_TICKERS:
            return {
                "error": "TICKER_NOT_FOUND",
                "message": (
                    f"'{ticker}' no está en el catálogo de activos. "
                    f"Tickers válidos: {', '.join(sorted(VALID_TICKERS.keys()))}"
                ),
            }

        common_dir = _common_files_dir()
        if not common_dir:
            return {
                "error": "MT5_COMMON_FILES_UNSET",
                "message": (
                    "MT5_COMMON_FILES no está configurado en el .env del MCP. "
                    "Apúntalo a la carpeta Common/Files de MT5 (menú 'Abrir carpeta de datos común')."
                ),
            }

        archivo = Path(common_dir) / _OBJECTS_FILE
        if not archivo.exists():
            return {
                "error": "NO_OBJECTS_FILE",
                "message": (
                    f"No existe {_OBJECTS_FILE} en Common/Files. "
                    "Ejecutar el Service ChartObjectsExporter en MT5."
                ),
            }

        try:
            data = json.loads(archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return {
                "error": "OBJECTS_UNREADABLE",
                "message": f"No se pudo leer/parsear {_OBJECTS_FILE}: {exc}",
            }

        generado = _parse_generado(data.get("generated_at", ""))
        if generado is not None:
            antiguedad = (datetime.now(tz=_SANTIAGO) - generado).total_seconds()
            if antiguedad > _STALE_SECONDS:
                return {
                    "error": "OBJECTS_STALE",
                    "message": (
                        f"chart_objects.json tiene {int(antiguedad // 60)} min de antigüedad "
                        f"(umbral {_STALE_SECONDS // 60} min). ¿El Service ChartObjectsExporter "
                        "sigue corriendo en MT5?"
                    ),
                }

        tf = timeframe.upper()
        chart = next(
            (c for c in data.get("charts", []) if c.get("symbol") == ticker and c.get("timeframe") == tf),
            None,
        )
        if chart is None:
            return {
                "error": "CHART_NOT_FOUND",
                "message": (
                    f"No hay objetos exportados para {ticker} {tf}. "
                    f"Abre el gráfico de {ticker} en {tf} en MT5 y espera al próximo refresco del Service."
                ),
            }

        digits = VALID_TICKERS[ticker]
        current = float(chart.get("current_price", 0.0))
        soportes, resistencias = _clasificar_hlines(chart.get("hlines", []), current, digits)

        screenshot_name = chart.get("screenshot") or ""
        screenshot = _recibir_screenshot(common_dir, screenshot_name) if screenshot_name else None

        return {
            "ticker": ticker,
            "timeframe": tf,
            "current_price": round(current, digits),
            "soportes": soportes,
            "resistencias": resistencias,
            "trendlines": chart.get("trendlines", []),
            "channels": chart.get("channels", []),
            "rectangles": chart.get("rectangles", []),
            "screenshot": screenshot,
            "generated_at": data.get("generated_at"),
            "source": "mt5_objects",
        }
