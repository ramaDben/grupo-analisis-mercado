"""Radar multifractal de Tori: qué líneas tocó la última vela cerrada y cuáles va a tocar.

Spec del radar §5. Un marco se lee como operativo con las mismas líneas y los mismos
roles de `lectura._estructura`: el radar no traza nada propio, solo mide la distancia
de la última vela cerrada a esas líneas. La vela en curso no entra; solo se informa
dónde estará cada línea en ella (`valor_abierta`), para compararla con el gráfico.

No se importa desde `estrategia.tori.__init__`: este módulo importa de ahí los
marcos intradía, y el import circular quedaría a un paso.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal

import pandas as pd

from estrategia.tori import MARCOS_INTRADIA
from estrategia.tori.calidad import calificar
from estrategia.tori.horizontales import Horizontal, detectar
from estrategia.tori.lectura import AVISO_SALTO, _estructura, _serie
from estrategia.tori.lineas import Trazo, trazar
from estrategia.tori.parametros import PARAMETROS, Parametros
from estrategia.tori.pivotes import Serie, inicio_tras_salto

Linea_ = Literal["seguridad", "accion", "rango", "soporte", "resistencia"]

# Las ventanas de las piezas (W1 156, D1 250, H4 180, H1 600): con otra ventana el ancla A
# puede ser otra y el radar mostraría líneas que ninguna pieza publica (spec §7).
MARCOS_RADAR = MARCOS_INTRADIA
RADAR_MARCOS: tuple[str, ...] = ("H1", "H4", "D1")


class HistoriaInsuficiente(ValueError):
    """MT5 devolvió menos velas que la ventana del marco: nunca se traza sobre historia parcial."""


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
    # La vela que rompió la línea es el toque aunque no la roce: con un salto de precio
    # (gap) el rango entero queda al otro lado, y llamarla "por tocar · retesteo" diría
    # que el precio todavía no llegó a una línea que acaba de cruzar.
    rompio_ahora = not t.vigente and t.i_ruptura == i
    # El rango de la vela, con el grosor de la línea, contiene a la línea (spec §5).
    if rompio_ahora or s.lows[i] - tol <= v <= s.highs[i] + tol:
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


def _par(niveles: list[Horizontal], cierre: float) -> list[tuple[Linea_, Horizontal]]:
    """El soporte más cercano bajo `cierre` y la resistencia más cercana sobre él, si existen."""
    bajo = [h for h in niveles if h.precio < cierre]
    sobre = [h for h in niveles if h.precio > cierre]
    return ([("soporte", max(bajo, key=lambda h: h.precio))] if bajo else []) +            ([("resistencia", min(sobre, key=lambda h: h.precio))] if sobre else [])


def zonas(s: Serie, p: Parametros, marco: str, digits: int) -> tuple[list[LineaRadar], list[Evento]]:
    """(lineas, eventos) sobre el soporte y la resistencia horizontales más cercanos (spec §5).

    Un horizontal es una zona de ancho `media_zona_atr` ATR a cada lado, no una línea.
    "Toco" elige el par con el cierre ANTERIOR: una vela que cruza el nivel y cierra al otro
    lado sigue midiéndose contra el soporte que tenía debajo. "Por tocar" lo elige con el
    último cierre y mide contra el borde de la zona; un nivel que ya tocó no repite.
    """
    if s.atr <= 0:
        raise ValueError(f"las velas de {marco} no tienen rango (ATR 0); no hay nada que medir")
    i = len(s) - 1
    cierre = s.closes[i]
    m = p.media_zona_atr * s.atr
    niveles = detectar(s, p)
    eventos: list[Evento] = []
    tocados: set[float] = set()
    for rol, h in _par(niveles, s.closes[i - 1]):
        if s.lows[i] <= h.precio + m and s.highs[i] >= h.precio - m:
            tocados.add(h.precio)
            eventos.append(Evento(marco, rol, "toco", None, abs(cierre - h.precio) / s.atr,
                                  round(h.precio, digits), "", ""))
    vigentes = _par(niveles, cierre)
    for rol, h in vigentes:
        if h.precio in tocados:
            continue
        d = max(0.0, abs(cierre - h.precio) - m)
        # El epsilon evita que 1,0000000002 por ruido de coma flotante cuente como 2 velas.
        n = ceil(d / (p.radar_k_atr * s.atr) - 1e-9)
        if 1 <= n <= p.radar_velas_max:
            eventos.append(Evento(marco, rol, "por_tocar", n, abs(cierre - h.precio) / s.atr,
                                  round(h.precio, digits), "", ""))
    lineas = [LineaRadar(rol, round(h.precio, digits), round(h.precio, digits)) for rol, h in vigentes]
    return lineas, eventos


@dataclass(frozen=True)
class LecturaMarco:
    marco: str
    estado: str
    direccion: str
    lineas: tuple[LineaRadar, ...]
    eventos: tuple[Evento, ...]
    avisos: tuple[str, ...]  # AVISO_SALTO si la ventana se cortó por un salto de datos
    vela: int  # apertura (hora servidor) de la última vela cerrada
    atr: float


def leer_marco(velas: dict[str, pd.DataFrame], marco: str, digits: int,
               p: Parametros = PARAMETROS) -> LecturaMarco:
    """El marco leído como operativo, con la misma ventana y el mismo corte que `leer()`.

    La historia se cuenta sobre las velas crudas, antes del corte por salto (spec §6): un
    salto de datos se acepta y queda en los avisos, igual que en las piezas, pero MT5
    devolviendo menos velas que la ventana es una lectura que no se hace. Solo entran las
    líneas propias del marco; las de contexto que adjunta `leer()` las aporta cada marco
    cuando le toca ser el operativo.
    """
    if marco not in RADAR_MARCOS:
        raise ValueError(f"el radar no lee {marco}: sus marcos son {', '.join(RADAR_MARCOS)}")
    req = MARCOS_RADAR.velas[marco]
    n = len(velas[marco])
    if n < req:
        raise HistoriaInsuficiente(f"{marco}: {n} velas de {req}")
    s = _serie(velas, marco, MARCOS_RADAR, p)
    if s.atr <= 0:
        raise ValueError(f"las velas de {marco} no tienen rango (ATR 0); no hay nada que leer")
    avisos = ((AVISO_SALTO.format(marco=marco),)
              if inicio_tras_salto(velas[marco].tail(req), p.salto_max_rango) else ())
    estado, direccion, l_diag, e_diag = diagonales(s, p, marco, digits)
    l_zona, e_zona = zonas(s, p, marco, digits)
    return LecturaMarco(marco, estado, direccion, tuple(l_diag + l_zona), tuple(e_diag + e_zona),
                        avisos, s.times[-1], s.atr)
