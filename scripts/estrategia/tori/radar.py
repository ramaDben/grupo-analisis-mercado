"""Radar multifractal de Tori: qué líneas tocó la última vela cerrada y cuáles va a tocar.

Spec del radar §5. Un marco se lee como operativo con las mismas líneas y los mismos
roles de `lectura._estructura`: el radar no traza nada propio, solo mide la distancia
de la última vela cerrada a esas líneas. La vela en curso no entra; solo se informa
dónde estará cada línea en ella (`valor_abierta`), para compararla con el gráfico.

No se importa desde `estrategia.tori.__init__`: este módulo importará de ahí los
marcos intradía, y el import circular quedaría a un paso.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from estrategia.tori.calidad import calificar
from estrategia.tori.lectura import _estructura
from estrategia.tori.lineas import Trazo, trazar
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie

Linea_ = Literal["seguridad", "accion", "rango", "soporte", "resistencia"]


@dataclass(frozen=True)
class Evento:
    marco: str  # "H1" | "H4" | "D1"
    linea: Linea_
    tipo: Literal["toco", "por_tocar"]
    velas: int | None  # n de "por_tocar"; None en "toco"
    distancia_atr: float  # |último cierre − línea| / ATR (en "por_tocar", contra la línea proyectada a n)
    valor: float  # precio de la línea en la última vela cerrada, redondeado a digits
    calidad: str  # "A+" | "B" | ""
    detalle: str  # "rebote" | "rompió" | "retesteo" | ""


@dataclass(frozen=True)
class LineaRadar:
    rol: Linea_
    valor_actual: float  # en la última vela cerrada
    valor_abierta: float  # proyectada a la vela en curso (índice len(s)); para comparar con el gráfico


def _detalle_toque(t: Trazo, s: Serie, rol: str) -> str:
    """Cómo cerró la vela que tocó la línea.

    La línea rota de un RUPTURA es un retesteo, salvo que se haya roto en esta misma
    vela: entonces el toque es la ruptura (spec §5, "tocó · rompió"). Una alcista o
    bajista rebota si el cierre quedó de su lado, con el criterio de `lectura._rebote`.
    Las de rango no tienen un lado a favor (regla del plan del radar): rebota
    si el cierre siguió del mismo lado que el anterior, rompió si la cruzó.
    """
    i = len(s) - 1
    if not t.vigente:
        return "rompió" if t.i_ruptura == i else "retesteo"
    v = t.valor(i)
    if rol == "rango":
        antes = s.closes[i - 1] - t.valor(i - 1)
        return "rebote" if antes * (s.closes[i] - v) > 0 else "rompió"
    a_favor = s.closes[i] > v if t.sentido == "alcista" else s.closes[i] < v
    return "rebote" if a_favor else "rompió"


def _eventos(t: Trazo, rol: Linea_, s: Serie, p: Parametros, marco: str, digits: int) -> list[Evento]:
    """Un "toco" si la última vela llegó a la línea; si no, el "por_tocar" de menor n, o nada."""
    i = len(s) - 1
    v = t.valor(i)
    cierre = s.closes[i]
    calidad = calificar(t, s, p).calidad
    tol = p.tolerancia_toque_atr * s.atr
    # El rango de la vela, con el grosor de la línea, contiene a la línea (spec §5).
    if s.lows[i] - tol <= v <= s.highs[i] + tol:
        return [Evento(marco, rol, "toco", None, abs(cierre - v) / s.atr, round(v, digits), calidad,
                       _detalle_toque(t, s, rol))]
    # "Llega en n velas al ritmo típico": la distancia a la línea proyectada cabe en k ATR por vela.
    for n in range(1, p.radar_velas_max + 1):
        distancia = abs(cierre - t.valor(i + n))
        if distancia <= p.radar_k_atr * s.atr * n:
            return [Evento(marco, rol, "por_tocar", n, distancia / s.atr, round(v, digits), calidad,
                           "" if t.vigente else "retesteo")]
    return []


def diagonales(s: Serie, p: Parametros, marco: str, digits: int
               ) -> tuple[str, str, list[LineaRadar], list[Evento]]:
    """(estado, direccion, lineas, eventos) del marco, con los roles de `_estructura`.

    Una línea no vigente solo llega acá como la rota de un RUPTURA que todavía dura;
    pasada la ruptura `_estructura` ya no la devuelve y no genera eventos.
    """
    if s.atr <= 0:
        raise ValueError(f"las velas de {marco} no tienen rango (ATR 0); no hay nada que medir")
    e = _estructura(s, trazar(s, "alcista", p), trazar(s, "bajista", p), p)
    con_rol: list[tuple[Linea_, Trazo]] = [
        (rol, t) for rol, t in (("seguridad", e.seguridad), ("accion", e.accion)) if t is not None
    ] + [("rango", t) for t in e.rango]
    ultimo = len(s) - 1
    lineas = [LineaRadar(rol, round(t.valor(ultimo), digits), round(t.valor(len(s)), digits))
              for rol, t in con_rol]
    eventos = [ev for rol, t in con_rol for ev in _eventos(t, rol, s, p, marco, digits)]
    return e.estado, e.direccion, lineas, eventos
