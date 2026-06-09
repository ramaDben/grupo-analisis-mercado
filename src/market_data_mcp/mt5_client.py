"""mt5_client — cliente mínimo de MetaTrader 5 vendorizado para el MCP market-data.

Subconjunto autocontenido extraído de la Capa 1 de un proyecto ajeno
(ver issues #30 y #25): solo lo que `get_asset_levels` necesita —conexión,
descarga de velas y dos indicadores (EMA, ATR)—. El calendario/noticias de
Finnhub NO se vendoriza: esas tools quedaron deprecadas y el dato se obtiene
vía WebSearch.

`MetaTrader5` se importa de forma **perezosa** dentro de cada función que lo usa.
Así este módulo es importable en CI (donde no hay MT5 ni el terminal corriendo),
lo que permite mockear `get_rates` y probar el camino feliz de la tool sin MT5.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

# Marcos temporales válidos → nombre del atributo en el módulo MetaTrader5.
# Guardamos el nombre (string) en vez de la constante para no tener que importar
# MetaTrader5 al cargar este módulo. La resolución a la constante real ocurre
# dentro de get_rates(), ya con MT5 disponible.
TIMEFRAME_MAP: dict[str, str] = {
    "M1":  "TIMEFRAME_M1",
    "M5":  "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1":  "TIMEFRAME_H1",
    "H4":  "TIMEFRAME_H4",
    "H12": "TIMEFRAME_H12",
    "D1":  "TIMEFRAME_D1",
    "W1":  "TIMEFRAME_W1",
    "MN1": "TIMEFRAME_MN1",
}


def connect() -> None:
    """Inicializa la conexión con MT5 usando credenciales del entorno si existen.

    Lee MT5_LOGIN / MT5_PASSWORD / MT5_SERVER / MT5_PATH del entorno (cargados
    desde el .env propio del repo en el lifespan del server). Idempotente: si el
    terminal ya está conectado, no hace nada.
    """
    import MetaTrader5 as mt5

    if mt5.terminal_info() is not None:
        return  # Ya conectado

    # `... or 0` cubre tanto la clave ausente como la cadena vacía (p.ej. cuando
    # se copia .env.example sin rellenar): int("") lanzaría ValueError.
    login    = int(os.environ.get("MT5_LOGIN") or 0)
    password = os.environ.get("MT5_PASSWORD", "")
    server   = os.environ.get("MT5_SERVER", "")
    path     = os.environ.get("MT5_PATH", "")

    init_kwargs: dict[str, object] = {}
    if path:
        init_kwargs["path"] = path
    if login:
        init_kwargs["login"] = login
        init_kwargs["password"] = password
        init_kwargs["server"] = server

    if not mt5.initialize(**init_kwargs):
        raise RuntimeError(f"MT5 initialize() falló: {mt5.last_error()}")


def disconnect() -> None:
    """Cierra la conexión con MT5."""
    import MetaTrader5 as mt5

    mt5.shutdown()


def get_rates(ticker: str, timeframe: str, n_bars: int = 200) -> pd.DataFrame:
    """Descarga las últimas n_bars velas de un ticker y timeframe dado.

    Retorna DataFrame con columnas: time, open, high, low, close, tick_volume, ...
    Lanza ValueError si el timeframe no es válido y RuntimeError si MT5 no
    entrega datos (terminal cerrado, ticker desconocido, etc.).
    """
    import MetaTrader5 as mt5

    tf_attr = TIMEFRAME_MAP.get(timeframe.upper())
    if tf_attr is None:
        raise ValueError(
            f"Timeframe '{timeframe}' no reconocido. Opciones: {list(TIMEFRAME_MAP.keys())}"
        )

    tf = getattr(mt5, tf_attr)
    rates = mt5.copy_rates_from_pos(ticker, tf, 0, n_bars)
    if rates is None or len(rates) == 0:
        raise RuntimeError(
            f"No se pudieron obtener datos para {ticker} {timeframe}: {mt5.last_error()}"
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def ema(series: pd.Series, period: int) -> pd.Series:
    """Media móvil exponencial."""
    return series.ewm(span=period, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (suavizado exponencial)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float, float, float]:
    """MACD estándar (12, 26, 9). Retorna (macd_line, signal_line, histogram) del último bar."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


def bollinger(
    series: pd.Series,
    period: int = 20,
    std: int = 2,
) -> tuple[float, float, float]:
    """Bandas de Bollinger (20, 2). Retorna (upper, mid, lower) del último bar."""
    mid = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    upper = mid + std * sigma
    lower = mid - std * sigma
    return float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])


def leer_calendario_json(path: "Path | None" = None) -> dict:
    """Lee y parsea el calendario macro exportado por el Service MQL5.

    El archivo lo escribe CalendarExporter.mq5 en Common/Files de MT5. Si `path`
    es None, se resuelve desde la variable de entorno MT5_COMMON_FILES (directorio
    Common/Files del terminal) + 'calendario_macro.json'.

    Lanza FileNotFoundError si el archivo no existe y json.JSONDecodeError si el
    contenido no es JSON válido. La validación de frescura y el contrato de error
    viven en la tool (tools/calendar.py), no aquí.
    """
    if path is None:
        common = os.environ.get("MT5_COMMON_FILES", "")
        if not common:
            raise FileNotFoundError(
                "MT5_COMMON_FILES no configurado: no se puede localizar calendario_macro.json"
            )
        path = Path(common) / "calendario_macro.json"
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el calendario MT5 en {path}")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="cp1252")
    return json.loads(content)
