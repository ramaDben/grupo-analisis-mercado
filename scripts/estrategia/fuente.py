"""Infraestructura: las velas de MT5 que pide la estrategia activa (spec §3, lado derecho).

MT5 entrega las marcas en hora del SERVIDOR empaquetadas como epoch (CLAUDE.md).
Las velas se pasan a la estrategia en esa misma época, porque ella solo mide
diferencias. Lo único que se convierte es la hora de cierre de la vela abierta,
que la pieza le dice al cliente en hora de Chile.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from estrategia.contrato import COLUMNAS_VELAS, Marcos, VelaEnCurso

SANTIAGO = ZoneInfo("America/Santiago")
DURACION = {"H1": 3600, "H4": 4 * 3600, "D1": 86400, "W1": 7 * 86400}
RELOJ = "BTCUSD"  # cotiza todos los días: su último tick es la hora del servidor
COTIZANDO_S = 15 * 60


def offset_servidor(tick_servidor: int, ahora_utc: float) -> int:
    """Segundos que el servidor va adelante de UTC, en la grilla de media hora."""
    return round((tick_servidor - ahora_utc) / 1800) * 1800


def separar_vela_abierta(df: pd.DataFrame, marco: str,
                         ahora_servidor: int) -> tuple[pd.DataFrame, pd.Series | None]:
    ultima = df.iloc[-1]
    if int(ultima["time"]) + DURACION[marco] > ahora_servidor:
        return df.iloc[:-1].reset_index(drop=True), ultima
    return df.reset_index(drop=True), None


def partir_velas(df: pd.DataFrame, marco: str, ahora_servidor: int,
                 cotizando: bool) -> tuple[pd.DataFrame, pd.Series | None]:
    """Las velas cerradas y, si el mercado cotiza, la vela en curso.

    Una vela cuyo período no terminó nunca cuenta como cerrada, cotice o no el mercado:
    fuera de horario la vela diaria o semanal en curso sigue abierta, y anclar una
    referencia en ella sería mirar el futuro.
    """
    cerradas, abierta = separar_vela_abierta(df, marco, ahora_servidor)
    return cerradas, abierta if cotizando else None


def cierre_santiago(apertura_servidor: int, marco: str, offset: int) -> datetime:
    utc = apertura_servidor + DURACION[marco] - offset
    return datetime.fromtimestamp(utc, tz=timezone.utc).astimezone(SANTIAGO)


def _epoch(columna: pd.Series) -> pd.Series:
    """`get_rates` convierte `time` a datetime; acá vuelve a segundos."""
    return (columna - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)


def atr(df: pd.DataFrame, n: int = 14) -> float:
    """El rango verdadero promedio de las últimas `n` velas: cuánto se mueve una vela típica.

    Es un dato de infraestructura para la pieza ("volatilidad típica"), no una decisión de
    la estrategia.
    """
    previo = df["close"].shift(1)
    rango = pd.concat([df["high"] - df["low"], (df["high"] - previo).abs(),
                       (df["low"] - previo).abs()], axis=1).max(axis=1)
    return float(rango.tail(n).mean())


def velas_mt5(ticker: str, marcos: Marcos,
              extra: int = 0) -> tuple[dict[str, pd.DataFrame], VelaEnCurso | None]:
    """Velas cerradas por marco y la vela en curso del operativo, si el mercado cotiza.

    `extra` pide velas de más para `seguir()`: las anclas de la referencia del lunes tienen que
    quedar dentro aunque la ventana de `leer()` haya avanzado.
    """
    import MetaTrader5 as mt5

    from market_data_mcp import mt5_client

    mt5_client.connect()
    ahora = time.time()
    tick = mt5.symbol_info_tick(ticker)
    reloj = mt5.symbol_info_tick(RELOJ) or tick
    if reloj is None:
        raise RuntimeError(f"MT5 no entregó cotización de {RELOJ} ni de {ticker}: no hay reloj del servidor")
    offset = offset_servidor(int(reloj.time), ahora)
    ahora_servidor = int(ahora) + offset
    cotizando = tick is not None and ahora_servidor - int(tick.time) < COTIZANDO_S
    velas: dict[str, pd.DataFrame] = {}
    en_curso: VelaEnCurso | None = None
    for marco in marcos.todos:
        n = marcos.velas[marco] + extra
        df = mt5_client.get_rates(ticker, marco, n + 1)[list(COLUMNAS_VELAS)].copy()
        df["time"] = _epoch(df["time"]).astype("int64")
        cerradas, abierta = partir_velas(df, marco, ahora_servidor, cotizando)
        velas[marco] = cerradas.tail(n).reset_index(drop=True)
        if marco == marcos.operativo and abierta is not None:
            en_curso = VelaEnCurso(int(abierta["time"]), float(abierta["close"]),
                                   cierre_santiago(int(abierta["time"]), marco, offset))
    return velas, en_curso
