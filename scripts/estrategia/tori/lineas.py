"""Trazado de Tori: semirrecta desde el extremo visible, sin que ninguna vela la cruce.

Doctrina §2.1 y §4, reglas 2, 3, 6, 9 y 10. Las líneas se calculan por índice de
vela, como las dibuja TradingView: los fines de semana no ocupan espacio.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, zigzag

Sentido = Literal["alcista", "bajista"]


@dataclass(frozen=True)
class Trazo:
    sentido: Sentido
    i_a: int
    p_a: float
    i_b: int
    p_b: float
    toques: tuple[int, ...]  # índices de las velas que tocan, A incluido
    i_ruptura: int | None  # primera vela que cerró al otro lado

    @property
    def pendiente(self) -> float:
        return (self.p_b - self.p_a) / (self.i_b - self.i_a)

    def valor(self, i: float) -> float:
        return self.p_a + self.pendiente * (i - self.i_a)

    @property
    def vigente(self) -> bool:
        return self.i_ruptura is None


def trazar(s: Serie, sentido: Sentido, p: Parametros, ancla: int | None = None) -> Trazo | None:
    """La mejor línea desde `ancla` (por defecto, el extremo de la ventana).

    El segundo punto es el pivote que junta más toques sin que ninguna vela cruce
    la línea; a igualdad de toques, la más ceñida al precio.
    """
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    if len(s) < 3:
        return None
    if ancla is None:
        ancla = extremos.index(min(extremos) if alcista else max(extremos))
    tipo = "L" if alcista else "H"
    candidatos = [i for i, _, t in zigzag(list(s.filas), p.zigzag_atr * s.atr)
                  if t == tipo and i > ancla]
    mejor: Trazo | None = None
    for b in candidatos:
        pendiente = (extremos[b] - extremos[ancla]) / (b - ancla)
        if (pendiente <= 0) if alcista else (pendiente >= 0):
            continue  # pendiente invertida: se elimina (OjZ8d [04:22])
        if abs(pendiente) < p.pendiente_min_atr * s.atr:
            continue  # plana: se lee como horizontal, no como línea (OjZ8d [03:52])
        trazo = _recorrer(s, sentido, ancla, b, p)
        if trazo is not None and (mejor is None or _orden(trazo) > _orden(mejor)):
            mejor = trazo
    return mejor


def _orden(t: Trazo) -> tuple[int, float]:
    return (len(t.toques), abs(t.pendiente))


def _recorrer(s: Serie, sentido: Sentido, a: int, b: int, p: Parametros) -> Trazo | None:
    """Recorre de A al final. Devuelve None si una vela cruza sin cerrar al otro lado (V10)."""
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    pendiente = (extremos[b] - extremos[a]) / (b - a)
    tol = p.tolerancia_toque_atr * s.atr
    lejos = p.separacion_toque_atr * s.atr
    toques: list[int] = []
    alejado = True
    ruptura = None
    for i in range(a, len(s)):
        linea = extremos[a] + pendiente * (i - a)
        holgura = (s.lows[i] - linea) if alcista else (linea - s.highs[i])
        if holgura < -tol:
            cierre = (s.closes[i] - linea) if alcista else (linea - s.closes[i])
            if i > b and cierre < -tol:
                ruptura = i  # cerró afuera por más que un asomo: ruptura por cierre (doctrina 2.4)
                break
            return None  # cruza y vuelve, o cruza antes de B: la línea no se traza (V10)
        if holgura <= tol:
            if alejado:
                toques.append(i)
                alejado = False
        elif holgura >= lejos:
            alejado = True
    if len(toques) < 2:
        return None  # A y B son el mismo toque: no hay línea
    return Trazo(sentido, a, extremos[a], b, extremos[b], tuple(toques), ruptura)


def seguimiento(s: Serie, principal: Trazo, p: Parametros) -> Trazo | None:
    """Abanico y encadenamiento (doctrina §2.3, reglas 9 y 10).

    Desde el último toque de la principal se busca una línea más empinada. Si ya
    está rota, no se devuelve: la secundaria rota se borra (V13).
    """
    if not principal.vigente:
        return None
    t = trazar(s, principal.sentido, p, ancla=principal.toques[-1])
    if t is None or not t.vigente or abs(t.pendiente) <= abs(principal.pendiente):
        return None
    return t
