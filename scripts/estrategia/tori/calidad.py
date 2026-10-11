"""Calidad de una línea (doctrina §2.2 y §4, reglas 4 y 5)."""
from __future__ import annotations

from dataclasses import dataclass

from estrategia.tori.lineas import Trazo
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie

DIAS_HABILES = 5


@dataclass(frozen=True)
class Calidad:
    calidad: str  # "A+" o "B"
    semanas: float  # del primer al último toque, en semanas de velas del marco
    punto_b_reciente: bool  # V16
    empinada: bool


def velas_por_semana(s: Serie) -> int:
    """Una semana de datos son 5 días hábiles del marco: en 4H, 30 velas (doctrina §4).

    Se cuenta en velas y no en días de calendario, porque el fin de semana no tiene
    velas y en el gráfico de Tori no ocupa espacio. El paso es la mediana entre
    velas, que no se mueve por los huecos del fin de semana.
    """
    pasos = sorted(b - a for a, b in zip(s.times, s.times[1:]))
    if not pasos:
        return 1
    return max(1, round(DIAS_HABILES * 86400 / pasos[len(pasos) // 2]))


def calificar(t: Trazo, s: Serie, p: Parametros) -> Calidad:
    semanas = (t.toques[-1] - t.toques[0]) / velas_por_semana(s)
    reciente = t.i_b >= len(s) - p.velas_punto_b_reciente
    empinada = abs(t.pendiente) > p.pendiente_empinada_atr * s.atr
    a_mas = len(t.toques) >= 3 and semanas >= 1.0 and not reciente
    return Calidad("A+" if a_mas else "B", semanas, reciente, empinada)
