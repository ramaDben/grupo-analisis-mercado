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


# .env propio del paquete (gitignored) con las credenciales MT5.
ENV_PATH = Path(__file__).resolve().parent / ".env"


def cargar_env(env_path: Path | None = None) -> None:
    """Carga el .env propio al entorno, sin pisar lo que ya esté definido.

    Vive acá y no en `server.py` porque **quien necesita las credenciales es
    `connect()`**, y hasta el 2026-09-07 solo el servidor MCP cargaba el archivo.
    Los siete scripts que llaman `connect()` directo (`extractor_precios`,
    `screener_gi`, `serie_mt5`, `pipeline_informe`…) nunca veían esas variables,
    así que las credenciales del .env no tenían efecto **justo en el camino de la
    corrida automática**, que es el que las necesita: el del reloj, con el
    terminal cerrado, donde `initialize()` sin credenciales se engancha a
    cualquier cuenta.

    `setdefault` y no asignación directa: una variable exportada en el entorno
    manda sobre el archivo, que es lo que permite apuntar a otra cuenta en una
    corrida puntual sin editar nada.
    """
    ruta = env_path or ENV_PATH
    if not ruta.exists():
        return
    for line in ruta.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def connect() -> None:
    """Inicializa la conexión con MT5 usando credenciales del entorno si existen.

    Lee MT5_LOGIN / MT5_PASSWORD / MT5_SERVER / MT5_PATH del entorno, cargando
    antes el .env propio del paquete. Idempotente: si el terminal ya está
    conectado, no hace nada.
    """
    import MetaTrader5 as mt5

    if mt5.terminal_info() is not None:
        return  # Ya conectado

    # Antes de leer el entorno, no después: si el .env es la única fuente de las
    # credenciales, leerlas primero deja `login` en 0 y cae al initialize() sin
    # credenciales, que es exactamente el camino no determinista que esto evita.
    cargar_env()

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

    # MT5 solo sirve `copy_rates_from_pos` para símbolos presentes en el Market
    # Watch del terminal. Sin esta línea la tool funcionaba para lo que el
    # director tuviera abierto y fallaba para el resto con "Terminal: Call
    # failed", un mensaje que no nombra la causa. Medido el 2026-09-02 desde un
    # proceso nuevo: USDCLP respondió y XAUUSD, US100 y WTI fallaron los tres,
    # del mismo terminal y en la misma corrida.
    if not mt5.symbol_select(ticker, True):
        raise RuntimeError(
            f"MT5 no pudo seleccionar '{ticker}': no está en el Market Watch del "
            f"terminal o el broker no lo ofrece. Agrégalo desde la ventana de "
            f"Observación de mercado. Detalle: {mt5.last_error()}"
        )

    rates = mt5.copy_rates_from_pos(ticker, tf, 0, n_bars)
    if rates is None or len(rates) == 0:
        raise RuntimeError(
            f"No se pudieron obtener datos para {ticker} {timeframe}: {mt5.last_error()}"
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def get_symbol_info(ticker: str):
    """Envuelve `MetaTrader5.symbol_info(ticker)` — specs estáticas del contrato.

    Import perezoso de `MetaTrader5` (mismo patrón que `get_rates`), para que
    este módulo sea importable y mockeable en tests sin el terminal instalado.

    Retorna el objeto `SymbolInfo` de MT5 (namedtuple-like, con `trade_mode`,
    `digits`, `volume_min`, `volume_step`, `trade_contract_size`, `time`, ...)
    o `None` si el símbolo no existe o no hay datos disponibles.
    """
    import MetaTrader5 as mt5

    return mt5.symbol_info(ticker)


def get_positions(ticker: str):
    """Envuelve `MetaTrader5.positions_get(symbol=ticker)` — operaciones abiertas.

    Import perezoso de `MetaTrader5` (mismo patrón que `get_rates`).

    Retorna la tupla de `TradePosition` de MT5 (con `ticket`, `type`, `volume`,
    `price_open`, `sl`, `tp`, `price_current`, `profit`, `swap`, `time`,
    `comment`, ...), una tupla vacía si el símbolo no tiene posiciones abiertas,
    o `None` si MT5 no pudo responder. La distinción entre `()` y `None` es
    deliberada: la primera es "sin operaciones", la segunda es un fallo.
    """
    import MetaTrader5 as mt5

    return mt5.positions_get(symbol=ticker)


def get_account_currency() -> str | None:
    """Moneda de la cuenta MT5 (la que expresa el resultado de las posiciones).

    Import perezoso de `MetaTrader5`. Retorna el código ISO (ej. "CLP", "USD")
    o `None` si el terminal no reporta la cuenta.
    """
    import MetaTrader5 as mt5

    info = mt5.account_info()
    return info.currency if info is not None else None


def get_session(ticker: str, day_of_week: int, index: int, tipo: str):
    """Envuelve `symbol_info_session_quote`/`symbol_info_session_trade` de MT5.

    Import perezoso de `MetaTrader5` (mismo patrón que `get_rates`).

    Args:
        ticker: símbolo MT5.
        day_of_week: convención MT5 (0=domingo, 1=lunes, ..., 6=sábado).
        index: índice de la ventana de sesión dentro del día (0, 1, 2, ...),
            para símbolos con más de una ventana (ej. pre-market/regular).
        tipo: `"quote"` o `"trade"`.

    Retorna una tupla `(apertura, cierre)` de `datetime.time` en hora del
    servidor del broker, o `None` si no hay sesión configurada para ese
    índice/día.
    """
    import MetaTrader5 as mt5

    if tipo == "quote":
        funcion = mt5.symbol_info_session_quote
    elif tipo == "trade":
        funcion = mt5.symbol_info_session_trade
    else:
        raise ValueError(f"tipo de sesión '{tipo}' inválido. Opciones: 'quote', 'trade'.")

    return funcion(ticker, day_of_week, index)


def ema(series: pd.Series, period: int) -> pd.Series:
    """Media móvil exponencial."""
    return series.ewm(span=period, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (suavizado Welles Wilder RMA, alpha=1/period)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index (suavizado Welles Wilder RMA, alpha=1/period)."""
    high = df["high"]
    low = df["low"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr = pd.concat([
        high - low,
        (high - df["close"].shift(1)).abs(),
        (low - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)

    alpha = 1.0 / period
    smoothed_tr = tr.ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False).mean() / smoothed_tr
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False).mean() / smoothed_tr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=alpha, adjust=False).mean()


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


def donchian(df: pd.DataFrame, period: int = 50) -> tuple[float, float, float]:
    """Canal de Donchian (50). Retorna (high, low, mid) del último bar.

    El Playbook lo usa como gatillo de quiebre (canales de 50 períodos en H1 con
    banda `0.3 x ATR14`) y `CLAUDE.md` lo admite como una de las dos definiciones
    del ADC (Ancho Dinámico de Canal); la amplitud es `high - low`, que se deja al
    consumidor igual que con las bandas de Bollinger.

    Misma fórmula que `scripts/extractor_precios.py`, que ya lo persiste para 6
    activos: máximo móvil del `high`, mínimo móvil del `low`, y `mid` como promedio
    de ambos extremos. Se replica en vez de importarse porque ese script vive fuera
    del paquete y trae dependencias (yfinance) que el MCP no tiene.
    """
    high = df["high"].rolling(period).max()
    low = df["low"].rolling(period).min()
    mid = (high + low) / 2.0
    return float(high.iloc[-1]), float(low.iloc[-1]), float(mid.iloc[-1])


