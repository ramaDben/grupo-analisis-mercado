"""Umbrales que Tori no da en números. Todos son NUESTROS (doctrina §2, §4).

Quedan declarados en la procedencia como `no_probado`: no habrá backtesting que
los mida. Los valores son provisionales y se revisan en el gate del director con
la medición del universo real (scripts/tori_revision.py).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametros:
    zigzag_atr: float = 2.0  # pivote candidato al segundo punto: giro de 2 ATR del marco
    tolerancia_toque_atr: float = 0.25  # la línea se traza "a ojo, con grosor" (Kffx9 [14:40])
    separacion_toque_atr: float = 1.0  # entre toques el precio "se aleja con claridad" (OjZ8d [06:13])
    pendiente_min_atr: float = 0.02  # bajo esto la línea es horizontal (OjZ8d [03:52])
    pendiente_empinada_atr: float = 0.5  # "muy empinada" (Murphy p. 103)
    velas_punto_b_reciente: int = 6  # V16: Punto B dentro del último día de 4H
    zigzag_horizontal_atr: float = 1.5
    tolerancia_horizontal_atr: float = 0.5  # el horizontal es una zona (qsjLm [08:52])
    horizontal_max_atr: float = 8.0  # "solo los cercanos" (qsjLm [03:27])
    velas_rango: int = 30  # bordes del rango sin diagonales: una semana de 4H
    cerca_atr_d1: float = 1.0  # spec §5: "a menos de un ATR diario"
    lejos_atr_d1: float = 2.0  # precio lejos de la línea de seguridad (doctrina 2.5)
    tope_adicionales: float = 24.0  # lo que suma dentro de una banda de situación


PARAMETROS = Parametros()
