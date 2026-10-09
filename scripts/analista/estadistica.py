"""Qué tan seguido se cumplió, en el pasado del mismo activo, el plan que el informe arma hoy.

Dos decisiones que no conviene revertir:

1. **Los niveles históricos salen de la misma función que los de hoy**
   (`_get_support_resistance` sobre las 300 velas previas). Una segunda
   definición de "resistencia" para la estadística mediría otra cosa.
2. **Siempre contra una línea base.** La invalidación queda a unos 3 ATR y el
   recorrido a 1,5 ATR, así que el recorrido sale primero muchas veces por pura
   geometría. "Lo logró el 70 %" sin la cifra de una hora cualquiera engaña.

Recibe un DataFrame con `time, open, high, low, close` y solo velas cerradas,
en orden. No lee nada: los tests corren sin terminal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from market_data_mcp.analisis import _get_support_resistance
from market_data_mcp.mt5_client import atr, ema

VENTANA, HORIZONTE = 300, 24
MULT_RECORRIDO, CHANDELIER_N, CHANDELIER_K = 1.5, 22, 3.0
MUESTRA_MINIMA, VENTAJA_MINIMA = 30, 5

Desenlace = Literal["recorrido", "invalidacion", "sin_definicion"]


@dataclass(frozen=True)
class Estadistica:
    casos: int
    pct_condicion: int | None
    pct_base: int | None
    desde: str
    hasta: str


def indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """ATR 14 (recorrido), ATR 22 y extremos de 22 velas (Chandelier) y EMA 50 (sesgo)."""
    out = pd.DataFrame(index=df.index)
    out["atr14"] = atr(df, 14)
    out["atr22"] = atr(df, CHANDELIER_N)
    out["ema50"] = ema(df["close"], 50)
    out["hh"] = df["high"].rolling(CHANDELIER_N, min_periods=1).max()
    out["ll"] = df["low"].rolling(CHANDELIER_N, min_periods=1).min()
    return out


def _chandelier(ind: pd.DataFrame, j: int, alcista: bool) -> float:
    if alcista:
        return float(ind["hh"].iat[j]) - CHANDELIER_K * float(ind["atr22"].iat[j])
    return float(ind["ll"].iat[j]) + CHANDELIER_K * float(ind["atr22"].iat[j])


def desenlace(df: pd.DataFrame, i: int, alcista: bool, ind: pd.DataFrame | None = None) -> Desenlace:
    """Entrando al cierre de la vela `i`: ¿qué toca primero en las 24 velas siguientes?"""
    ind = indicadores(df) if ind is None else ind
    entrada = float(df["close"].iat[i])
    paso = MULT_RECORRIDO * float(ind["atr14"].iat[i])
    objetivo = entrada + paso if alcista else entrada - paso
    stop = _chandelier(ind, i, alcista)
    for j in range(i + 1, min(i + 1 + HORIZONTE, len(df))):
        alto, bajo = float(df["high"].iat[j]), float(df["low"].iat[j])
        toca_stop = bajo <= stop if alcista else alto >= stop
        toca_obj = alto >= objetivo if alcista else bajo <= objetivo
        # Empate en la misma vela: sin datos intravela no se sabe qué pasó
        # primero, y se cuenta lo que perjudica a la estadística.
        if toca_stop:
            return "invalidacion"
        if toca_obj:
            return "recorrido"
        # El Chandelier se arrastra: solo se mueve a favor.
        nuevo = _chandelier(ind, j, alcista)
        stop = max(stop, nuevo) if alcista else min(stop, nuevo)
    return "sin_definicion"


def _ruptura(df: pd.DataFrame, i: int, digits: int, alcista: bool, ind: pd.DataFrame) -> float | None:
    """El nivel que cruzó el cierre de la vela `i`, o None.

    El nivel se calcula con las 300 velas ANTERIORES a `i` (misma función que los
    niveles de hoy), así que nada posterior a `i` puede cambiarlo. Cuenta solo un
    R1 (o S1) medido sobre swings y con el cierre a favor de la EMA 50.
    """
    clave = "r1" if alcista else "s1"
    previo = float(df["close"].iat[i - 1])
    niveles = _get_support_resistance(df.iloc[i - VENTANA:i], previo, float(ind["atr14"].iat[i - 1]), digits)
    if niveles["origen"][clave] != "swing":
        return None
    nivel = niveles[clave]
    cierre = float(df["close"].iat[i])
    media = float(ind["ema50"].iat[i])
    cruza = (cierre > nivel >= previo) if alcista else (cierre < nivel <= previo)
    a_favor = cierre > media if alcista else cierre < media
    return nivel if cruza and a_favor else None


def eventos(df: pd.DataFrame, digits: int, alcista: bool, ind: pd.DataFrame | None = None) -> list[int]:
    """Velas con ruptura (ver `_ruptura`). Un mismo nivel cuenta una sola vez."""
    ind = indicadores(df) if ind is None else ind
    salida: list[int] = []
    ultimo: float | None = None
    for i in range(VENTANA, len(df)):
        nivel = _ruptura(df, i, digits, alcista, ind)
        if nivel is not None and nivel != ultimo:
            salida.append(i)
            ultimo = nivel
    return salida


def ultima_ruptura(df: pd.DataFrame, digits: int, alcista: bool,
                   ind: pd.DataFrame | None = None) -> tuple[float, int] | None:
    """El nivel y la vela de la última ruptura dentro de las últimas 24 velas, o None."""
    ind = indicadores(df) if ind is None else ind
    for i in range(len(df) - 1, max(VENTANA, len(df) - HORIZONTE) - 1, -1):
        nivel = _ruptura(df, i, digits, alcista, ind)
        if nivel is not None:
            return nivel, i
    return None


def activacion_reciente(df: pd.DataFrame, digits: int, alcista: bool,
                        ind: pd.DataFrame | None = None) -> float | None:
    """El nivel de la última ruptura dentro de las últimas 24 velas, o None.

    El R1 de ahora no sirve para saber si el plan se activó: apenas el precio
    rompe una resistencia, `analizar_activo` pasa a mostrar la siguiente. El
    estado se decide con la misma definición de evento que mide la estadística.
    """
    hallada = ultima_ruptura(df, digits, alcista, ind)
    return hallada[0] if hallada else None


def _pct(resultados: list[Desenlace]) -> int | None:
    return round(100 * resultados.count("recorrido") / len(resultados)) if resultados else None


def medir(df: pd.DataFrame, digits: int, alcista: bool) -> Estadistica:
    # El período empieza donde hay 300 velas previas: antes no se mide nada.
    desde = str(df["time"].iat[min(VENTANA, len(df) - 1)])[:10] if len(df) else ""
    hasta = str(df["time"].iat[-1])[:10] if len(df) else ""
    if len(df) <= VENTANA + HORIZONTE:
        return Estadistica(0, None, None, desde, hasta)
    ind = indicadores(df)
    limite = len(df) - HORIZONTE  # sin horizonte completo, el caso no cuenta
    idx = [i for i in eventos(df, digits, alcista, ind) if i < limite]
    # La base son las horas con la MISMA tendencia (cierre del mismo lado de la
    # EMA 50), no todas: contra todas, la condición sumaba ~20 puntos de ventaja
    # que eran solo el filtro de tendencia (oro, 2026-10-08: 53 % contra 33 % de
    # todas las horas y 49 % de las horas a favor). Lo que se mide es el gatillo.
    cierres, media = df["close"].to_numpy(), ind["ema50"].to_numpy()
    base = [desenlace(df, i, alcista, ind) for i in range(VENTANA, limite)
            if (cierres[i] > media[i] if alcista else cierres[i] < media[i])]
    cond = [desenlace(df, i, alcista, ind) for i in idx]
    pct_c = _pct(cond) if len(cond) >= MUESTRA_MINIMA else None
    return Estadistica(len(cond), pct_c, _pct(base), desde, hasta)
