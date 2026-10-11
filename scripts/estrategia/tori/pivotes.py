"""Pivotes candidatos y ATR del marco (doctrina §4, regla 1).

El zigzag se mudó acá desde `tradingview_grafico._zigzag` (spec §5): es parte
de la estrategia, y el gráfico lo importa de este módulo mientras siga
dibujando su canal (hasta S5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from estrategia.contrato import COLUMNAS_VELAS


@dataclass(frozen=True)
class Serie:
    filas: tuple[dict[str, Any], ...]
    times: tuple[int, ...]
    highs: tuple[float, ...]
    lows: tuple[float, ...]
    closes: tuple[float, ...]
    atr: float

    def __len__(self) -> int:
        return len(self.times)


def _atr(highs, lows, closes, periodo: int) -> float:
    """Media simple del rango verdadero de las últimas `periodo` velas."""
    if not highs:
        return 0.0
    rangos = [highs[0] - lows[0]] + [
        max(h - lo, abs(h - c0), abs(lo - c0))
        for h, lo, c0 in zip(highs[1:], lows[1:], closes[:-1])
    ]
    ultimos = rangos[-periodo:]
    return sum(ultimos) / len(ultimos)


def serie_de(df: pd.DataFrame, periodo_atr: int = 14) -> Serie:
    filas = tuple(df[list(COLUMNAS_VELAS)].to_dict("records"))
    times = tuple(int(f["time"]) for f in filas)
    highs = tuple(float(f["high"]) for f in filas)
    lows = tuple(float(f["low"]) for f in filas)
    closes = tuple(float(f["close"]) for f in filas)
    return Serie(filas, times, highs, lows, closes, _atr(highs, lows, closes, periodo_atr))


def inicio_tras_salto(df: pd.DataFrame, factor: float) -> int:
    """Primera vela después del último salto de la serie; 0 si no hay ninguno.

    Un salto es un hueco entre el cierre anterior y la apertura de más de `factor` veces
    el rango mediano de las velas: no es un movimiento del mercado sino un cambio de nivel
    de los datos (COPPER, gate del director del 2026-10-11). Una línea anclada antes del
    salto mediría la pendiente a través de él.
    """
    if len(df) < 2:
        return 0
    mediana = float((df["high"] - df["low"]).median())
    if mediana <= 0:
        return 0
    huecos = (df["open"] - df["close"].shift()).abs().to_numpy()
    saltos = [i for i in range(1, len(df)) if huecos[i] > factor * mediana]
    return saltos[-1] if saltos else 0


def zigzag(rows: list[dict[str, Any]], umbral: float) -> list[tuple[int, float, str]]:
    """Pivotes mayores: un giro cuenta cuando el precio retrocede `umbral` desde el extremo.

    Devuelve `(indice, precio, 'H'|'L')` en orden temporal. Es el mismo criterio que
    usa quien traza a mano: un máximo es máximo cuando el precio ya se alejó de él.
    """
    if not rows or umbral <= 0:
        return []
    pivotes: list[tuple[int, float, str]] = []
    dir_ = 0
    ext_i, ext_h, ext_l = 0, rows[0]["high"], rows[0]["low"]
    ext_hi_i, ext_lo_i = 0, 0
    for i, r in enumerate(rows):
        if dir_ >= 0:
            if r["high"] >= ext_h:
                ext_h, ext_hi_i = r["high"], i
            if dir_ == 1 and ext_h - r["low"] >= umbral:
                pivotes.append((ext_hi_i, ext_h, "H"))
                dir_, ext_l, ext_lo_i = -1, r["low"], i
                continue
        if dir_ <= 0:
            if r["low"] <= ext_l:
                ext_l, ext_lo_i = r["low"], i
            if dir_ == -1 and r["high"] - ext_l >= umbral:
                pivotes.append((ext_lo_i, ext_l, "L"))
                dir_, ext_h, ext_hi_i = 1, r["high"], i
                continue
        if dir_ == 0:
            if ext_h - r["low"] >= umbral and ext_hi_i < i:
                pivotes.append((ext_hi_i, ext_h, "H"))
                dir_, ext_l, ext_lo_i = -1, r["low"], i
            elif r["high"] - ext_l >= umbral and ext_lo_i < i:
                pivotes.append((ext_lo_i, ext_l, "L"))
                dir_, ext_h, ext_hi_i = 1, r["high"], i
    return pivotes

