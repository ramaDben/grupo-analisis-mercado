"""Soportes y resistencias horizontales de Tori (doctrina §2.10).

Son confluencia, objetivo y borde del rango, nunca entrada. Hacen lo mismo que
`analisis._get_support_resistance`, pero son de la estrategia (spec §5).
"""
from __future__ import annotations

from dataclasses import dataclass

from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, zigzag


@dataclass(frozen=True)
class Horizontal:
    precio: float
    toques: int
    i_primero: int


def _contar_toques(valores: tuple[float, ...], nivel: float, tol: float, lejos: float) -> int:
    toques, alejado = 0, True
    for v in valores:
        distancia = abs(v - nivel)
        if distancia <= tol:
            if alejado:
                toques += 1
                alejado = False
        elif distancia >= lejos:
            alejado = True
    return toques


def detectar(s: Serie, p: Parametros) -> list[Horizontal]:
    """Niveles con 2 toques o más, cercanos al precio, el más cercano primero."""
    if s.atr <= 0:
        return []
    pivotes = sorted((precio, i) for i, precio, _ in zigzag(list(s.filas), p.zigzag_horizontal_atr * s.atr))
    tol = p.tolerancia_horizontal_atr * s.atr
    grupos: list[list[tuple[float, int]]] = []
    for precio, i in pivotes:
        if grupos and precio - grupos[-1][0][0] <= tol:
            grupos[-1].append((precio, i))
        else:
            grupos.append([(precio, i)])
    actual = s.closes[-1]
    niveles = [Horizontal(sum(x for x, _ in g) / len(g), len(g), min(i for _, i in g))
               for g in grupos if len(g) >= 2]
    cercanos = [h for h in niveles if abs(h.precio - actual) <= p.horizontal_max_atr * s.atr]
    return sorted(cercanos, key=lambda h: abs(h.precio - actual))


def bordes_rango(s: Serie, p: Parametros) -> tuple[Horizontal, Horizontal]:
    """Máximo y mínimo de la última semana del marco (doctrina 2.10, xMNO4 [08:52])."""
    ini = max(0, len(s) - p.velas_rango)
    altos, bajos = s.highs[ini:], s.lows[ini:]
    techo, piso = max(altos), min(bajos)
    tol = p.tolerancia_horizontal_atr * s.atr
    lejos = p.separacion_toque_atr * s.atr
    return (
        Horizontal(techo, _contar_toques(altos, techo, tol, lejos), ini + altos.index(techo)),
        Horizontal(piso, _contar_toques(bajos, piso, tol, lejos), ini + bajos.index(piso)),
    )
