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
    toques: tuple[int, ...]  # extremo de cada toque (la vela de menor holgura del episodio), A incluido
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
    """La mejor línea desde `ancla` (por defecto, el extremo visible de la ventana).

    El segundo punto es el pivote que junta más toques sin que ninguna vela cruce
    la línea; a igualdad de toques, la más ceñida al precio.

    Sin `ancla`, el primer punto es el extremo visible (regla 2). Si desde ahí no se
    puede trazar una diagonal limpia, o la que sale ya está rota, el ancla pasa al
    extremo de lo que queda a la derecha: encadenar (doctrina 2.3) y rotar la línea
    rota al extremo nuevo (V13). Un doble piso deja así la diagonal en el segundo
    piso, y una estructura nueva reemplaza a la ruptura vieja. Si ninguna ancla da
    una línea vigente, se devuelve la última rota (la ruptura más reciente).
    """
    if len(s) < 3:
        return None
    tipo = "L" if sentido == "alcista" else "H"
    pivotes = [i for i, _, t in zigzag(list(s.filas), p.zigzag_atr * s.atr) if t == tipo]
    if ancla is not None:
        return _desde(s, sentido, p, ancla, pivotes)
    rota: Trazo | None = None
    a = _extremo(s, sentido, p, pivotes, desde=0)
    while a is not None:
        t = _desde(s, sentido, p, a, pivotes)
        if t is not None and t.vigente:
            return t
        if t is not None:
            rota = t
        a = _extremo(s, sentido, p, pivotes, desde=a + 1 if t is None else t.i_ruptura)
    return rota


def _extremo(s: Serie, sentido: Sentido, p: Parametros, pivotes: list[int], desde: int) -> int | None:
    """El extremo visible desde la vela `desde`: el pivote más extremo confirmado a la izquierda.

    Confirmado quiere decir que antes de él el precio estuvo a un giro de zigzag de
    distancia. El mínimo de la primera vela de la ventana no lo está: no se ve de
    dónde venía el precio, y el extremo real puede estar afuera (gate, WTI).
    """
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    giro = p.zigzag_atr * s.atr

    def confirmado(i: int) -> bool:
        if alcista:
            return i > 0 and max(s.highs[:i]) - s.lows[i] >= giro
        return i > 0 and s.highs[i] - min(s.lows[:i]) >= giro

    candidatos = [i for i in pivotes if i >= desde and confirmado(i)]
    if not candidatos:
        return None
    return min(candidatos, key=lambda i: (extremos[i], i)) if alcista else         min(candidatos, key=lambda i: (-extremos[i], i))


def _desde(s: Serie, sentido: Sentido, p: Parametros, ancla: int, pivotes: list[int]) -> Trazo | None:
    mejor: Trazo | None = None
    for b in (i for i in pivotes if i > ancla):
        if not _es_diagonal(s, sentido, ancla, b, p):
            continue
        trazo = _recorrer(s, sentido, ancla, b, p)
        if trazo is not None and (mejor is None or _orden(trazo) > _orden(mejor)):
            mejor = trazo
    return mejor


def _es_diagonal(s: Serie, sentido: Sentido, a: int, b: int, p: Parametros) -> bool:
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    pendiente = (extremos[b] - extremos[a]) / (b - a)
    if (pendiente <= 0) if alcista else (pendiente >= 0):
        return False  # pendiente invertida: se elimina (OjZ8d [04:22])
    return abs(pendiente) >= p.pendiente_min_atr * s.atr  # plana: se lee como horizontal (OjZ8d [03:52])


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
    episodio: tuple[int, float] | None = None  # (vela, holgura) del extremo del toque en curso
    ruptura = None
    for i in range(a, len(s)):
        linea = extremos[a] + pendiente * (i - a)
        holgura = (s.lows[i] - linea) if alcista else (linea - s.highs[i])
        if holgura < -tol:
            cierre = (s.closes[i] - linea) if alcista else (linea - s.closes[i])
            if i > b and cierre < -tol:
                ruptura = i  # cerró afuera por más que un asomo: ruptura por cierre (doctrina 2.4)
                break
            if i > b:
                # Una mecha después de B no es ruptura (2.4): el Punto B se mueve a esa vela
                # y la línea se redibuja desde A (2.3, V10).
                return _recorrer(s, sentido, a, i, p) if _es_diagonal(s, sentido, a, i, p) else None
            return None  # cruza antes de B: la línea no se traza (V10)
        if holgura <= tol:
            if episodio is None or holgura < episodio[1]:
                episodio = (i, holgura)  # el extremo del toque, no la primera vela que entra
        elif holgura >= lejos:
            if episodio is not None:
                toques.append(episodio[0])
                episodio = None
    if episodio is not None:
        toques.append(episodio[0])
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
