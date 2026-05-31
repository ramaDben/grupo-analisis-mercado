"""
Integración con MetaTrader 5.
Extrae precios en tiempo real, calcula indicadores técnicos
y genera imágenes de gráficos profesionales listas para WhatsApp.

Requisitos (instalar en PowerShell):
    pip install MetaTrader5 pandas mplfinance pandas_ta matplotlib

MT5 debe estar abierto y logueado en tu broker antes de ejecutar.
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path

# --- Imports con manejo de errores ---
try:
    import MetaTrader5 as mt5
    MT5_DISPONIBLE = True
except ImportError:
    MT5_DISPONIBLE = False
    print("⚠️  MetaTrader5 no instalado. Ejecuta: pip install MetaTrader5")

try:
    import pandas as pd
    PANDAS_TA_DISPONIBLE = True  # Indicadores implementados en pandas puro (sin pandas_ta)
except ImportError:
    PANDAS_TA_DISPONIBLE = False
    print("⚠️  pandas no instalado. Ejecuta: pip install pandas")


# ═══════════════════════════════════════════════════════════════
# Indicadores técnicos en pandas puro
# (reemplaza pandas_ta, que requiere numba y no soporta Python 3.14)
# Los nombres de columna replican los de pandas_ta para mantener
# compatibilidad con el resto del código (gráficos, MACD, Bollinger).
# ═══════════════════════════════════════════════════════════════

def _sma(serie: "pd.Series", length: int) -> "pd.Series":
    return serie.rolling(window=length).mean()


def _ema(serie: "pd.Series", length: int) -> "pd.Series":
    return serie.ewm(span=length, adjust=False).mean()


def _rsi(serie: "pd.Series", length: int = 14) -> "pd.Series":
    delta = serie.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    # Suavizado de Wilder (equivalente a pandas_ta por defecto)
    avg_ganancia = ganancia.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_perdida = perdida.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_ganancia / avg_perdida
    return 100 - (100 / (1 + rs))


def _atr(high: "pd.Series", low: "pd.Series", close: "pd.Series", length: int = 14) -> "pd.Series":
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Suavizado de Wilder (RMA), igual que pandas_ta
    return tr.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def _macd(serie: "pd.Series", fast: int = 12, slow: int = 26, signal: int = 9) -> "pd.DataFrame":
    macd_line = _ema(serie, fast) - _ema(serie, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({
        f"MACD_{fast}_{slow}_{signal}": macd_line,
        f"MACDh_{fast}_{slow}_{signal}": hist,
        f"MACDs_{fast}_{slow}_{signal}": signal_line,
    })


def _bbands(serie: "pd.Series", length: int = 20, std: float = 2.0) -> "pd.DataFrame":
    media = serie.rolling(window=length).mean()
    desv = serie.rolling(window=length).std()
    std_str = f"{float(std):.1f}"
    return pd.DataFrame({
        f"BBL_{length}_{std_str}": media - std * desv,
        f"BBM_{length}_{std_str}": media,
        f"BBU_{length}_{std_str}": media + std * desv,
    })

try:
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")  # Backend sin GUI para generar imágenes
    MPLFINANCE_DISPONIBLE = True
except ImportError:
    MPLFINANCE_DISPONIBLE = False
    print("⚠️  mplfinance no instalado. Ejecuta: pip install mplfinance matplotlib")


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"

# Mapeo de tickers internos a símbolos del broker en MT5
# AJUSTAR según tu broker (cada broker puede tener nombres distintos)
TICKER_MAP_MT5 = {
    # Forex / Commodities
    "USD/CLP":  "USDCLP",       # Broker Grupo Inteligencia SpA (cuenta 51142)
    "XAU/USD":  "XAUUSD",       # Broker Grupo Inteligencia SpA
    "WTI":      "WTI.spot",     # Broker Grupo Inteligencia SpA
    "COBRE":    "COPPER",       # Broker Grupo Inteligencia SpA
    "DXY":      "USDIDX",       # Dollar Index en Grupo Inteligencia SpA
    # Índices
    "US100":    "US100.spot",   # Nasdaq 100 — Broker Grupo Inteligencia SpA
    "US500":    "US500.spot",   # S&P 500 — Broker Grupo Inteligencia SpA
    "US30":     "US30.spot",    # Dow Jones — Broker Grupo Inteligencia SpA
    # Acciones tecnológicas (US100)
    "#AAPL":    "#AAPL",        # Apple Inc.
    "#MSFT":    "#MSFT",        # Microsoft Corp.
    "#NVDA":    "#NVDA",        # NVIDIA Corp.
    "#AMZN":    "#AMZN",        # Amazon.com Inc.
    # Acciones bancarias (US30)
    "#JPM":     "#JPM",         # JPMorgan Chase
    "#BAC":     "#BAC",         # Bank of America
    "#GS":      "#GS",          # Goldman Sachs
    "#MS":      "#MS",          # Morgan Stanley
    # Acciones industriales (US30)
    "#BA":      "#BA",          # Boeing Co.
    "#CAT":     "#CAT",         # Caterpillar Inc.
    "#GE":      "#GE",          # GE Aerospace
    "#DE":      "#DE",          # Deere & Co.
}

# Mapeo de temporalidades del organigrama a timeframes de MT5
TIMEFRAME_MAP = {
    "15M":  mt5.TIMEFRAME_M15 if MT5_DISPONIBLE else None,
    "1H":   mt5.TIMEFRAME_H1  if MT5_DISPONIBLE else None,
    "4H":   mt5.TIMEFRAME_H4  if MT5_DISPONIBLE else None,
    "1D":   mt5.TIMEFRAME_D1  if MT5_DISPONIBLE else None,
}


# ═══════════════════════════════════════════════════════════════
# 1. CONEXIÓN A MT5
# ═══════════════════════════════════════════════════════════════

def conectar_mt5(ruta_terminal: str = None) -> bool:
    """
    Inicializa la conexión con el terminal MT5.
    MT5 debe estar abierto y logueado.

    Args:
        ruta_terminal: Ruta al terminal64.exe (opcional, MT5 lo detecta automáticamente)

    Returns:
        True si la conexión fue exitosa.
    """
    if not MT5_DISPONIBLE:
        print("❌ MetaTrader5 no está instalado")
        return False

    params = {}
    if ruta_terminal:
        params["path"] = ruta_terminal

    if not mt5.initialize(**params):
        error = mt5.last_error()
        print(f"❌ No se pudo conectar a MT5: {error}")
        print("   Asegúrate de que MT5 esté abierto y logueado.")
        return False

    info = mt5.terminal_info()
    print(f"✅ Conectado a MT5")
    print(f"   Broker: {info.company}")
    print(f"   Servidor: {info.name}")
    print(f"   Build: {info.build}")
    return True


def desconectar_mt5():
    """Cierra la conexión con MT5."""
    if MT5_DISPONIBLE:
        mt5.shutdown()
        print("🔌 Desconectado de MT5")


def listar_simbolos_broker():
    """
    Lista todos los símbolos disponibles en tu broker.
    Útil para encontrar los nombres correctos de los activos.
    """
    simbolos = mt5.symbols_get()
    if simbolos is None:
        print("❌ No se pudieron obtener los símbolos")
        return []

    nombres = [s.name for s in simbolos]
    print(f"📋 {len(nombres)} símbolos disponibles en el broker")
    return nombres


def buscar_simbolo(texto: str) -> list:
    """
    Busca símbolos que contengan el texto dado.
    Útil para encontrar el nombre exacto de un activo en tu broker.

    Ejemplo: buscar_simbolo("CLP") → ["USDCLP", "USDCLPm", ...]
    """
    todos = listar_simbolos_broker()
    encontrados = [s for s in todos if texto.upper() in s.upper()]
    if encontrados:
        print(f"🔍 Símbolos que contienen '{texto}': {encontrados}")
    else:
        print(f"❌ No se encontraron símbolos con '{texto}'")
    return encontrados


# ═══════════════════════════════════════════════════════════════
# 2. EXTRACCIÓN DE PRECIOS
# ═══════════════════════════════════════════════════════════════

def obtener_precio_actual(ticker_interno: str) -> dict:
    """
    Obtiene el precio actual (tick) de un activo desde MT5.

    Args:
        ticker_interno: Ticker interno (ej: "USD/CLP", "XAU/USD")

    Returns:
        Dict con bid, ask, spread, último precio, hora.
    """
    simbolo = TICKER_MAP_MT5.get(ticker_interno)
    if not simbolo:
        return {"error": f"Ticker '{ticker_interno}' no mapeado. Revisa TICKER_MAP_MT5."}

    # Asegurar que el símbolo está habilitado
    if not mt5.symbol_select(simbolo, True):
        return {"error": f"Símbolo '{simbolo}' no disponible en tu broker. Usa buscar_simbolo() para encontrar el nombre correcto."}

    tick = mt5.symbol_info_tick(simbolo)
    if tick is None:
        return {"error": f"No se pudo obtener tick de {simbolo}"}

    info = mt5.symbol_info(simbolo)

    return {
        "ticker": ticker_interno,
        "simbolo_mt5": simbolo,
        "bid": tick.bid,
        "ask": tick.ask,
        "last": tick.last if tick.last > 0 else tick.bid,
        "spread": round(tick.ask - tick.bid, info.digits if info else 4),
        "volumen": tick.volume,
        "hora_servidor": datetime.fromtimestamp(tick.time).strftime("%Y-%m-%d %H:%M:%S"),
        "hora_local": datetime.now().strftime("%H:%M CLT"),
        "error": None
    }


def obtener_velas(ticker_interno: str, temporalidad: str = "4H",
                   cantidad: int = 200) -> pd.DataFrame:
    """
    Obtiene datos OHLCV (velas) de MT5.

    Args:
        ticker_interno: "USD/CLP", "XAU/USD", etc.
        temporalidad: "15M", "1H", "4H", "1D"
        cantidad: Número de velas a obtener

    Returns:
        DataFrame con columnas Open, High, Low, Close, Volume, datetime index.
    """
    simbolo = TICKER_MAP_MT5.get(ticker_interno)
    if not simbolo:
        print(f"❌ Ticker '{ticker_interno}' no mapeado")
        return pd.DataFrame()

    mt5.symbol_select(simbolo, True)

    timeframe = TIMEFRAME_MAP.get(temporalidad)
    if timeframe is None:
        print(f"❌ Temporalidad '{temporalidad}' no válida. Usa: 15M, 1H, 4H, 1D")
        return pd.DataFrame()

    rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, cantidad)
    if rates is None or len(rates) == 0:
        print(f"❌ No se obtuvieron datos para {simbolo} en {temporalidad}")
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    # Renombrar columnas para compatibilidad con mplfinance
    df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "tick_volume": "Volume"
    }, inplace=True)

    # Eliminar columnas extra de MT5
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    return df


def obtener_todos_precios_mt5(tickers: list = None) -> dict:
    """Obtiene precios actuales de todos los activos principales."""
    if tickers is None:
        tickers = ["USD/CLP", "XAU/USD", "WTI", "US100"]

    resultado = {
        "fecha": date.today().isoformat(),
        "hora_consulta": datetime.now().strftime("%H:%M CLT"),
        "fuente": "MetaTrader 5",
        "precios": {}
    }

    for ticker in tickers:
        resultado["precios"][ticker] = obtener_precio_actual(ticker)

    return resultado


# ═══════════════════════════════════════════════════════════════
# 3. CÁLCULO DE INDICADORES
# ═══════════════════════════════════════════════════════════════

def calcular_indicadores(df: pd.DataFrame, indicadores: list = None) -> pd.DataFrame:
    """
    Calcula indicadores técnicos sobre un DataFrame OHLCV.

    Args:
        df: DataFrame con columnas Open, High, Low, Close, Volume
        indicadores: Lista de indicadores a calcular.
            Opciones: "sma_50", "sma_200", "ema_20", "rsi", "macd", "atr", "bollinger"
            Si es None, calcula todos.

    Returns:
        DataFrame original con columnas de indicadores agregadas.
    """
    if not PANDAS_TA_DISPONIBLE:
        print("❌ pandas_ta no disponible")
        return df

    if indicadores is None:
        indicadores = ["sma_50", "sma_200", "ema_20", "rsi", "macd", "atr"]

    df = df.copy()

    if "sma_50" in indicadores:
        df["SMA_50"] = _sma(df["Close"], length=50)

    if "sma_200" in indicadores:
        df["SMA_200"] = _sma(df["Close"], length=200)

    if "ema_20" in indicadores:
        df["EMA_20"] = _ema(df["Close"], length=20)

    if "rsi" in indicadores:
        df["RSI"] = _rsi(df["Close"], length=14)

    if "macd" in indicadores:
        macd = _macd(df["Close"], fast=12, slow=26, signal=9)
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

    if "atr" in indicadores:
        df["ATR"] = _atr(df["High"], df["Low"], df["Close"], length=14)

    if "bollinger" in indicadores:
        bbands = _bbands(df["Close"], length=20, std=2)
        if bbands is not None:
            df = pd.concat([df, bbands], axis=1)

    return df


def identificar_niveles(df: pd.DataFrame) -> dict:
    """
    Identifica soportes y resistencias básicos a partir del precio.
    Usa máximos/mínimos recientes y niveles de pivote.

    Returns:
        Dict con soportes, resistencias y sesgo.
    """
    if df.empty:
        return {}

    close = df["Close"].iloc[-1]
    high_reciente = df["High"].tail(20).max()
    low_reciente = df["Low"].tail(20).min()
    high_50 = df["High"].tail(50).max()
    low_50 = df["Low"].tail(50).min()

    # Pivote clásico
    high_ayer = df["High"].iloc[-2]
    low_ayer = df["Low"].iloc[-2]
    close_ayer = df["Close"].iloc[-2]
    pivot = (high_ayer + low_ayer + close_ayer) / 3
    r1 = 2 * pivot - low_ayer
    s1 = 2 * pivot - high_ayer
    r2 = pivot + (high_ayer - low_ayer)
    s2 = pivot - (high_ayer - low_ayer)

    # Determinar sesgo
    if close > pivot and close > df["Close"].tail(10).mean():
        sesgo = "alcista"
    elif close < pivot and close < df["Close"].tail(10).mean():
        sesgo = "bajista"
    else:
        sesgo = "lateral"

    # ── Validación de coherencia ──────────────────────────────────
    # Un soporte SOLO es válido si está por DEBAJO del precio actual,
    # y una resistencia SOLO si está por ENCIMA. Si un pivote calculado
    # cae del lado equivocado (p. ej. el precio rompió todos los soportes
    # clásicos), se descarta y se usa el siguiente nivel válido del
    # universo de candidatos (pivotes + máximos/mínimos recientes).
    candidatos = {pivot, r1, r2, s1, s2,
                  high_reciente, low_reciente, high_50, low_50}

    soportes = sorted((n for n in candidatos if n < close), reverse=True)
    resistencias = sorted(n for n in candidatos if n > close)

    # Fallback: si no hay 2 niveles válidos de un lado, derivarlos
    # extendiendo con un paso proporcional al rango reciente.
    rango = high_reciente - low_reciente
    paso = rango * 0.5 if rango > 0 else max(abs(close) * 0.005, 1e-6)

    while len(soportes) < 2:
        base = soportes[-1] if soportes else close
        soportes.append(base - paso)
    while len(resistencias) < 2:
        base = resistencias[-1] if resistencias else close
        resistencias.append(base + paso)

    soporte_1, soporte_2 = soportes[0], soportes[1]
    resistencia_1, resistencia_2 = resistencias[0], resistencias[1]

    return {
        "precio_actual": round(close, 4),
        "pivot": round(pivot, 4),
        "resistencia_1": round(resistencia_1, 4),
        "resistencia_2": round(resistencia_2, 4),
        "soporte_1": round(soporte_1, 4),
        "soporte_2": round(soporte_2, 4),
        "maximo_20_velas": round(high_reciente, 4),
        "minimo_20_velas": round(low_reciente, 4),
        "sesgo": sesgo,
        "zona_interes": {
            "desde": round(soporte_1, 4),
            "hasta": round(resistencia_1, 4)
        }
    }


# ═══════════════════════════════════════════════════════════════
# 4. GENERACIÓN DE GRÁFICOS (IMÁGENES)
# ═══════════════════════════════════════════════════════════════

# Estilo personalizado para los gráficos del grupo
ESTILO_GRUPO = {
    "base_mpl_style": "dark_background",
    "marketcolors": mpf.make_marketcolors(
        up="#26a69a",       # Verde para velas alcistas
        down="#ef5350",     # Rojo para velas bajistas
        edge="inherit",
        wick="inherit",
        volume="in",
        ohlc="inherit"
    ) if MPLFINANCE_DISPONIBLE else None,
    "facecolor": "#1e222d",    # Fondo oscuro tipo TradingView
    "edgecolor": "#1e222d",
    "figcolor": "#1e222d",
    "gridcolor": "#2a2e39",
    "gridstyle": "--",
    "gridwidth": 0.5,
}


def _crear_estilo():
    """Crea el estilo de gráfico personalizado."""
    if not MPLFINANCE_DISPONIBLE:
        return None
    return mpf.make_mpf_style(
        base_mpl_style="dark_background",
        marketcolors=ESTILO_GRUPO["marketcolors"],
        facecolor=ESTILO_GRUPO["facecolor"],
        edgecolor=ESTILO_GRUPO["edgecolor"],
        figcolor=ESTILO_GRUPO["figcolor"],
        gridcolor=ESTILO_GRUPO["gridcolor"],
        gridstyle=ESTILO_GRUPO["gridstyle"],
        y_on_right=True,
    )


def generar_grafico(ticker_interno: str, temporalidad: str = "4H",
                     cantidad_velas: int = 100,
                     indicadores: list = None,
                     soportes: list = None,
                     resistencias: list = None,
                     titulo: str = None,
                     guardar: bool = True) -> str:
    """
    Genera un gráfico de velas profesional con indicadores y niveles.

    Args:
        ticker_interno: "USD/CLP", "XAU/USD", etc.
        temporalidad: "15M", "1H", "4H", "1D"
        cantidad_velas: Número de velas a mostrar
        indicadores: Lista de indicadores a incluir.
            Opciones: "sma_50", "sma_200", "ema_20", "rsi", "macd", "atr", "bollinger"
        soportes: Lista de precios de soporte para dibujar líneas horizontales
        resistencias: Lista de precios de resistencia para dibujar líneas horizontales
        titulo: Título personalizado del gráfico
        guardar: Si True, guarda la imagen como archivo PNG

    Returns:
        Ruta del archivo PNG generado.
    """
    if not MPLFINANCE_DISPONIBLE:
        print("❌ mplfinance no disponible")
        return ""

    # Obtener datos
    df = obtener_velas(ticker_interno, temporalidad, cantidad_velas + 50)
    if df.empty:
        return ""

    # Calcular indicadores
    if indicadores is None:
        indicadores = ["sma_50", "sma_200"]

    df = calcular_indicadores(df, indicadores)

    # Tomar solo las últimas N velas para el gráfico
    df = df.tail(cantidad_velas)

    # Construir plots adicionales.
    # Orden fijo de paneles: 0 = velas (+SMAs/niveles), 1 = volumen,
    # 2 = RSI (si se usa), 3 = MACD (si se usa). El volumen ocupa el
    # panel 1 explícitamente (volume_panel=1) para que RSI/MACD no
    # colisionen con él.
    addplots = []
    PANEL_VOLUMEN = 1
    panel_rsi = None
    panel_macd = None
    proximo_panel = 2  # 0 = velas, 1 = volumen

    # Medias móviles en el panel principal
    # (solo se grafican si tienen al menos un valor válido; p. ej. la SMA 200
    #  queda toda en NaN si no hay suficientes velas)
    if "SMA_50" in df.columns and df["SMA_50"].notna().any():
        addplots.append(mpf.make_addplot(
            df["SMA_50"], panel=0, color="#ff9800", width=1.2,
            linestyle="-", label="SMA 50"
        ))
    if "SMA_200" in df.columns and df["SMA_200"].notna().any():
        addplots.append(mpf.make_addplot(
            df["SMA_200"], panel=0, color="#2196f3", width=1.2,
            linestyle="-", label="SMA 200"
        ))
    if "EMA_20" in df.columns and df["EMA_20"].notna().any():
        addplots.append(mpf.make_addplot(
            df["EMA_20"], panel=0, color="#ab47bc", width=1.0,
            linestyle="--", label="EMA 20"
        ))

    # Bollinger Bands
    if "BBU_20_2.0" in df.columns and df["BBU_20_2.0"].notna().any():
        addplots.append(mpf.make_addplot(df["BBU_20_2.0"], panel=0, color="#78909c", width=0.7))
        addplots.append(mpf.make_addplot(df["BBL_20_2.0"], panel=0, color="#78909c", width=0.7))

    # RSI en panel separado (panel 2, después del volumen)
    if "RSI" in df.columns and "rsi" in indicadores and df["RSI"].notna().any():
        panel_rsi = proximo_panel
        proximo_panel += 1
        addplots.append(mpf.make_addplot(
            df["RSI"], panel=panel_rsi, color="#ab47bc",
            ylabel="RSI", width=1.0
        ))
        # Líneas de sobrecompra/sobreventa
        addplots.append(mpf.make_addplot(
            pd.Series([70] * len(df), index=df.index),
            panel=panel_rsi, color="#ef5350", width=0.5, linestyle="--"
        ))
        addplots.append(mpf.make_addplot(
            pd.Series([30] * len(df), index=df.index),
            panel=panel_rsi, color="#26a69a", width=0.5, linestyle="--"
        ))

    # MACD en panel separado (panel 3, después del RSI)
    macd_col = [c for c in df.columns if "MACD_12" in c and "MACDs" not in c and "MACDh" not in c]
    signal_col = [c for c in df.columns if "MACDs" in c]
    hist_col = [c for c in df.columns if "MACDh" in c]

    if macd_col and "macd" in indicadores and df[macd_col[0]].notna().any():
        panel_macd = proximo_panel
        proximo_panel += 1
        addplots.append(mpf.make_addplot(
            df[macd_col[0]], panel=panel_macd, color="#2196f3",
            ylabel="MACD", width=1.0
        ))
        if signal_col:
            addplots.append(mpf.make_addplot(
                df[signal_col[0]], panel=panel_macd, color="#ff9800", width=0.8
            ))
        if hist_col:
            colors_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in df[hist_col[0]]]
            addplots.append(mpf.make_addplot(
                df[hist_col[0]], panel=panel_macd, type="bar",
                color=colors_hist, width=0.7
            ))

    # Líneas horizontales de soportes y resistencias
    hlines = {}
    if soportes:
        hlines["hlines"] = hlines.get("hlines", []) + soportes
        hlines["colors"] = hlines.get("colors", []) + ["#26a69a"] * len(soportes)
        hlines["linestyle"] = hlines.get("linestyle", []) + ["--"] * len(soportes)
        hlines["linewidths"] = hlines.get("linewidths", []) + [1.0] * len(soportes)
    if resistencias:
        hlines["hlines"] = hlines.get("hlines", []) + resistencias
        hlines["colors"] = hlines.get("colors", []) + ["#ef5350"] * len(resistencias)
        hlines["linestyle"] = hlines.get("linestyle", []) + ["--"] * len(resistencias)
        hlines["linewidths"] = hlines.get("linewidths", []) + [1.0] * len(resistencias)

    # Título
    if titulo is None:
        titulo = f"{ticker_interno} — {temporalidad}"

    # Crear estilo
    estilo = _crear_estilo()

    # Determinar tamaño y proporciones de paneles.
    # panel_ratios debe tener un valor por panel existente, en orden:
    # [velas, volumen, (RSI), (MACD)]. El panel de velas es el más alto.
    panel_ratios = [3.2, 1.0]  # velas, volumen
    if panel_rsi is not None:
        panel_ratios.append(1.3)
    if panel_macd is not None:
        panel_ratios.append(1.3)

    n_paneles = len(panel_ratios)
    alto = 6 + (n_paneles - 1) * 2.5

    # Configuración de guardado
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"{ticker_interno.replace('/', '_')}_{temporalidad}_{date.today().isoformat()}.png"
    ruta_salida = CHARTS_DIR / nombre_archivo

    # Generar gráfico
    kwargs = {
        "type": "candle",
        "style": estilo,
        "title": f"\n{titulo}",
        "volume": True,
        "volume_panel": PANEL_VOLUMEN,   # volumen siempre en el panel 1
        "panel_ratios": tuple(panel_ratios),
        "figsize": (14, alto),
        "tight_layout": True,
        "warn_too_much_data": 500,
    }

    if addplots:
        kwargs["addplot"] = addplots
    if hlines.get("hlines"):
        kwargs["hlines"] = dict(
            hlines=hlines["hlines"],
            colors=hlines["colors"],
            linestyle="--",
            linewidths=1.0
        )

    if guardar:
        kwargs["savefig"] = dict(fname=str(ruta_salida), dpi=150, bbox_inches="tight")
        mpf.plot(df, **kwargs)
        plt.close("all")
        print(f"📊 Gráfico guardado: {ruta_salida}")
        return str(ruta_salida)
    else:
        mpf.plot(df, **kwargs)
        plt.show()
        return ""


def generar_graficos_dia(activos_hoy: list, temporalidad: str = "4H",
                          indicadores: list = None) -> list:
    """
    Genera gráficos para todos los activos del día.

    Args:
        activos_hoy: Lista de tickers internos ["USD/CLP", "XAU/USD"]
        temporalidad: Temporalidad principal
        indicadores: Lista de indicadores

    Returns:
        Lista de rutas de archivos PNG generados.
    """
    rutas = []

    for ticker in activos_hoy:
        print(f"\n📈 Generando gráfico de {ticker} en {temporalidad}...")

        # Obtener niveles primero
        df = obtener_velas(ticker, temporalidad, 200)
        if df.empty:
            print(f"  ⚠️ Sin datos para {ticker}")
            continue

        niveles = identificar_niveles(df)
        soportes = [niveles["soporte_1"], niveles["soporte_2"]]
        resistencias = [niveles["resistencia_1"], niveles["resistencia_2"]]

        # Generar gráfico con niveles
        ruta = generar_grafico(
            ticker_interno=ticker,
            temporalidad=temporalidad,
            cantidad_velas=100,
            indicadores=indicadores or ["sma_50", "sma_200", "rsi"],
            soportes=soportes,
            resistencias=resistencias,
            titulo=f"{ticker} — {temporalidad} | Sesgo: {niveles['sesgo'].upper()}"
        )

        if ruta:
            rutas.append({
                "ticker": ticker,
                "temporalidad": temporalidad,
                "ruta_imagen": ruta,
                "niveles": niveles
            })

    return rutas


# ═══════════════════════════════════════════════════════════════
# 5. ANÁLISIS COMPLETO (todo junto)
# ═══════════════════════════════════════════════════════════════

def analisis_completo_activo(ticker_interno: str, temporalidad: str = "4H") -> dict:
    """
    Genera el análisis completo de un activo: precio, indicadores, niveles y gráfico.
    Este es el flujo que se ejecuta para cada activo del día.

    Returns:
        Dict con toda la información lista para el agente redactor.
    """
    print(f"\n{'='*50}")
    print(f"📊 Análisis completo: {ticker_interno} en {temporalidad}")
    print(f"{'='*50}")

    # 1. Precio actual
    precio = obtener_precio_actual(ticker_interno)
    print(f"  💰 Precio: {precio.get('bid', 'N/A')}")

    # 2. Obtener velas
    df = obtener_velas(ticker_interno, temporalidad, 200)
    if df.empty:
        return {"error": f"Sin datos para {ticker_interno}"}

    # 3. Calcular indicadores
    df = calcular_indicadores(df, ["sma_50", "sma_200", "rsi", "macd", "atr"])

    # 4. Identificar niveles
    niveles = identificar_niveles(df)
    print(f"  📐 Sesgo: {niveles['sesgo']}")
    print(f"  📈 R1: {niveles['resistencia_1']} | R2: {niveles['resistencia_2']}")
    print(f"  📉 S1: {niveles['soporte_1']} | S2: {niveles['soporte_2']}")

    # 5. Últimos valores de indicadores
    ultimo = df.iloc[-1]
    indicadores_actuales = {}
    if "RSI" in df.columns and pd.notna(ultimo.get("RSI")):
        rsi = round(ultimo["RSI"], 1)
        indicadores_actuales["RSI"] = {
            "valor": rsi,
            "estado": "sobrecompra" if rsi > 70 else "sobreventa" if rsi < 30 else "neutral"
        }
        print(f"  📊 RSI: {rsi} ({indicadores_actuales['RSI']['estado']})")

    if "ATR" in df.columns and pd.notna(ultimo.get("ATR")):
        atr = round(ultimo["ATR"], 4)
        indicadores_actuales["ATR"] = {"valor": atr}
        print(f"  📊 ATR: {atr}")

    macd_cols = [c for c in df.columns if "MACD_12" in c and "MACDs" not in c and "MACDh" not in c]
    if macd_cols and pd.notna(ultimo.get(macd_cols[0])):
        indicadores_actuales["MACD"] = {"valor": round(ultimo[macd_cols[0]], 4)}

    # 6. Generar gráfico
    ruta_grafico = generar_grafico(
        ticker_interno=ticker_interno,
        temporalidad=temporalidad,
        indicadores=["sma_50", "sma_200", "rsi"],
        soportes=[niveles["soporte_1"], niveles["soporte_2"]],
        resistencias=[niveles["resistencia_1"], niveles["resistencia_2"]],
        titulo=f"{ticker_interno} — {temporalidad} | Sesgo: {niveles['sesgo'].upper()}"
    )

    return {
        "ticker": ticker_interno,
        "temporalidad": temporalidad,
        "precio": precio,
        "niveles": niveles,
        "indicadores": indicadores_actuales,
        "ruta_grafico": ruta_grafico,
        "timestamp": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════
# 6. EJECUCIÓN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🔌 INTEGRACIÓN MT5 — Grupo de Análisis de Mercado")
    print("=" * 60)

    if not conectar_mt5():
        print("\n💡 Pasos para solucionar:")
        print("   1. Abre MetaTrader 5 y logueate en tu broker")
        print("   2. Ejecuta: pip install MetaTrader5 pandas pandas_ta mplfinance matplotlib")
        print("   3. Ajusta los tickers en TICKER_MAP_MT5 según tu broker")
        print("   4. Vuelve a ejecutar este script")
        exit(1)

    try:
        # Buscar los símbolos de tu broker (descomentar para primera vez)
        # buscar_simbolo("CLP")
        # buscar_simbolo("XAU")
        # buscar_simbolo("OIL")
        # buscar_simbolo("NAS")

        # Test: análisis completo de USD/CLP
        resultado = analisis_completo_activo("USD/CLP", "4H")

        if resultado.get("error"):
            print(f"\n❌ Error: {resultado['error']}")
            print("\n💡 Usa buscar_simbolo('CLP') para encontrar el nombre correcto en tu broker")
        else:
            print(f"\n✅ Análisis completo generado")
            print(f"   Gráfico: {resultado.get('ruta_grafico', 'N/A')}")

            # Guardar resultado
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DATA_DIR / "ultimo_analisis.json", "w", encoding="utf-8") as f:
                # Eliminar ruta_grafico que no es serializable limpiamente
                resultado_json = {k: v for k, v in resultado.items() if k != "ruta_grafico"}
                resultado_json["ruta_grafico"] = resultado.get("ruta_grafico", "")
                json.dump(resultado_json, f, ensure_ascii=False, indent=2, default=str)

    finally:
        desconectar_mt5()
