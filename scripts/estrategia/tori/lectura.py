"""Lectura de Tori: de las líneas trazadas a la Lectura del contrato (spec §5, lectura.py).

Las velas cerradas mandan: líneas, toques, calidad, dirección y RUPTURA salen
solo de ellas. La vela en curso, si llega, solo puede poner el estado PRUEBA
encima (spec §4, "La vela abierta"); lo agrega la Task S3-2.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from estrategia.contrato import Lectura, Linea, Marcos, Prueba, Referencia, VelaEnCurso, exigir_velas
from estrategia.tori import textos
from estrategia.tori.calidad import calificar
from estrategia.tori.horizontales import Horizontal, bordes_rango, detectar
from estrategia.tori.lineas import Trazo, seguimiento, trazar
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, serie_de


@dataclass(frozen=True)
class _Estructura:
    estado: str
    direccion: str
    accion: Trazo | None
    seguridad: Trazo | None
    rango: tuple[Trazo, ...]
    velas_desde_ruptura: int | None


def _serie(velas: dict[str, pd.DataFrame], marco: str, marcos: Marcos) -> Serie:
    return serie_de(velas[marco].tail(marcos.velas[marco]).reset_index(drop=True))


def _peso(t: Trazo, s: Serie, p: Parametros) -> tuple[bool, int, float]:
    c = calificar(t, s, p)
    return (c.calidad == "A+", len(t.toques), c.semanas)


def _sigue_afuera(s: Serie, t: Trazo) -> bool:
    ultimo = len(s) - 1
    linea = t.valor(ultimo)
    return s.closes[ultimo] < linea if t.sentido == "alcista" else s.closes[ultimo] > linea


def _estructura(s: Serie, alc: Trazo | None, baj: Trazo | None, p: Parametros) -> _Estructura:
    ultimo = len(s) - 1
    rotas = [t for t in (alc, baj) if t is not None and not t.vigente]
    vigentes = [t for t in (alc, baj) if t is not None and t.vigente]
    reciente = max(rotas, key=lambda t: t.i_ruptura, default=None)
    desde = None if reciente is None else ultimo - reciente.i_ruptura
    # Sin límite de velas: la ruptura dura mientras el cierre siga afuera (huecos, punto 5).
    if reciente is not None and _sigue_afuera(s, reciente):
        direccion = "BAJISTA" if reciente.sentido == "alcista" else "ALCISTA"
        opuesta = next((t for t in vigentes if t.sentido != reciente.sentido), None)
        return _Estructura("RUPTURA", direccion, reciente, opuesta, (), desde)
    if not vigentes:
        return _Estructura("RANGO", "LATERAL", None, None, (), desde)
    if len(vigentes) == 2 and all(calificar(t, s, p).calidad != "A+" for t in vigentes):
        return _Estructura("RANGO", "LATERAL", None, None, tuple(vigentes), desde)
    principal = max(vigentes, key=lambda t: _peso(t, s, p))
    contraria = next((t for t in vigentes if t is not principal), None)
    direccion = "ALCISTA" if principal.sentido == "alcista" else "BAJISTA"
    return _Estructura("TENDENCIA", direccion, contraria, principal, (), desde)


def _linea(t: Trazo, s: Serie, rol: str, marco: str, p: Parametros, digits: int) -> Linea:
    c = calificar(t, s, p)
    return Linea(rol=rol, tipo="diagonal",
                 puntos=((s.times[t.i_a], round(t.p_a, digits)), (s.times[t.i_b], round(t.p_b, digits))),
                 marco=marco, toques=len(t.toques), calidad=c.calidad,
                 valor_actual=round(t.valor(len(s) - 1), digits), empinada=c.empinada)


def _horizontal(h: Horizontal, s: Serie, rol: str, marco: str, digits: int) -> Linea:
    return Linea(rol=rol, tipo="horizontal", puntos=((s.times[h.i_primero], round(h.precio, digits)),),
                 marco=marco, toques=h.toques, calidad="", valor_actual=round(h.precio, digits))


def _contexto(velas, marcos: Marcos, direccion: str, p: Parametros,
              digits: int) -> tuple[list[Linea], float, bool]:
    """Líneas vigentes de los marcos de contexto, qué parte va a favor y si todos van en contra.

    Doctrina 2.9 y 2.11: las falsas rupturas vienen de operar contra la secuencia de los
    marcos mayores (ipUbs [00:36], [01:11]).
    """
    lineas: list[Linea] = []
    votos: list[float] = []
    for marco in marcos.contexto:
        sc = _serie(velas, marco, marcos)
        if sc.atr <= 0:
            continue
        vigentes = [t for t in (trazar(sc, "alcista", p), trazar(sc, "bajista", p))
                    if t is not None and t.vigente]
        lineas += [_linea(t, sc, "contexto", marco, p, digits) for t in vigentes]
        if vigentes and direccion != "LATERAL":
            principal = max(vigentes, key=lambda t: _peso(t, sc, p))
            votos.append(1.0 if (principal.sentido == "alcista") == (direccion == "ALCISTA") else 0.0)
    a_favor = sum(votos) / len(votos) if votos else 0.0
    return lineas, a_favor, bool(votos) and a_favor == 0.0


def _horizontales(velas, marcos: Marcos, p: Parametros) -> list[tuple[Horizontal, Serie, str]]:
    salida = []
    for marco in (marcos.operativo, *marcos.contexto):
        sm = _serie(velas, marco, marcos)
        salida += [(h, sm, marco) for h in detectar(sm, p)]
    return salida


def _objetivo(horizontales, direccion: str, precio: float, tol: float, digits: int,
              operativo: str) -> Linea | None:
    """El horizontal MAYOR más cercano en la dirección (doctrina 2.8, V11).

    Primero los de los marcos de contexto; los del marco operativo solo si no hay
    ninguno mayor en la dirección.
    """
    if direccion == "LATERAL":
        return None
    mayores = [x for x in horizontales if x[2] != operativo]
    menores = [x for x in horizontales if x[2] == operativo]
    for grupo in (mayores, menores):
        if direccion == "ALCISTA":
            cand = [x for x in grupo if x[0].precio > precio + tol]
            elegido = min(cand, key=lambda x: x[0].precio, default=None)
        else:
            cand = [x for x in grupo if x[0].precio < precio - tol]
            elegido = max(cand, key=lambda x: x[0].precio, default=None)
        if elegido is not None:
            h, sm, marco = elegido
            return _horizontal(h, sm, "objetivo", marco, digits)
    return None


def _prueba(vivas: list[tuple[Linea, float]], cierre: float, en_curso: VelaEnCurso | None,
            tol: float, digits: int) -> Prueba | None:
    """Lo completa la Task S3-2."""
    return None


def _rebote(s, valor: float, sentido: str, tol: float) -> bool:
    """La última vela cerrada tocó la línea de seguridad y cerró a favor (doctrina 2.5, V7)."""
    i = len(s) - 1
    if sentido == "alcista":
        return s.lows[i] - valor <= tol and s.closes[i] > valor
    return valor - s.highs[i] <= tol and s.closes[i] < valor


def _vigilar(prueba, estado, accion, seguridad, rango, precio) -> Referencia:
    if prueba is not None:
        return Referencia(prueba.valor_ahora, f"línea {textos.sentido(prueba.linea)} en prueba", prueba.linea)
    if estado == "REBOTE":
        # Lo que se mira es la línea que sostuvo el rebote.
        return Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
    if estado in ("RUPTURA", "TENDENCIA"):
        x = accion if accion is not None else seguridad
        return Referencia(x.valor_actual, f"línea {textos.sentido(x)}", x)
    cercana = min(rango, key=lambda x: abs(x.valor_actual - precio))
    techo = max(x.valor_actual for x in rango)
    etiqueta = "resistencia del rango" if cercana.valor_actual == techo else "soporte del rango"
    return Referencia(cercana.valor_actual, etiqueta, cercana)


def leer(ticker: str, velas: dict[str, pd.DataFrame], digits: int,
         en_curso: VelaEnCurso | None, marcos: Marcos, p: Parametros) -> Lectura:
    exigir_velas(velas, marcos)
    op = marcos.operativo
    s = _serie(velas, op, marcos)
    if s.atr <= 0:
        raise ValueError(f"{ticker}: las velas de {op} no tienen rango (ATR 0); no hay nada que leer")
    e = _estructura(s, trazar(s, "alcista", p), trazar(s, "bajista", p), p)
    avisos: list[str] = []
    siguiente = len(s)  # índice de la vela abierta

    accion = _linea(e.accion, s, "accion", op, p, digits) if e.accion else None
    seguridad = _linea(e.seguridad, s, "seguridad", op, p, digits) if e.seguridad else None
    lineas: list[Linea] = [x for x in (accion, seguridad) if x is not None]
    vivas: list[tuple[Linea, float]] = []
    if accion is not None and e.accion.vigente:
        vivas.append((accion, e.accion.valor(siguiente)))
    linea_seguimiento: Linea | None = None
    if seguridad is not None:
        vivas.append((seguridad, e.seguridad.valor(siguiente)))
        seg = seguimiento(s, e.seguridad, p)
        if seg is not None:
            linea_seguimiento = _linea(seg, s, "seguimiento", op, p, digits)
            lineas.append(linea_seguimiento)
    rango: list[Linea] = []
    for t in e.rango:
        x = _linea(t, s, "rango", op, p, digits)
        rango.append(x)
        vivas.append((x, t.valor(siguiente)))
    if e.estado == "RANGO" and not rango:
        for h in bordes_rango(s, p):
            x = _horizontal(h, s, "rango", op, digits)
            rango.append(x)
            vivas.append((x, x.valor_actual))
        avisos.append("sin línea diagonal vigente: se lee como rango entre el máximo y el mínimo de la última semana")
    lineas += rango

    contexto, a_favor, contra = _contexto(velas, marcos, e.direccion, p, digits)
    lineas += contexto
    if contra:
        avisos.append("la lectura va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas")

    cierre = s.closes[-1]
    precio = en_curso.precio if en_curso is not None else cierre
    tol = p.tolerancia_toque_atr * s.atr
    prueba = _prueba(vivas, cierre, en_curso, tol, digits)
    rebote = e.estado == "TENDENCIA" and e.seguridad is not None and \
        _rebote(s, e.seguridad.valor(len(s) - 1), e.seguridad.sentido, tol)
    base = "REBOTE" if rebote else e.estado
    estado = "PRUEBA" if prueba is not None else base

    horizontales = _horizontales(velas, marcos, p)
    objetivo_linea = _objetivo(horizontales, e.direccion, precio, tol, digits, op)
    if objetivo_linea is not None:
        lineas.append(objetivo_linea)

    vigilar = _vigilar(prueba, base, accion, seguridad, rango, precio)
    invalidacion = (Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
                    if seguridad is not None else None)
    objetivo = Referencia(objetivo_linea.valor_actual, "objetivo", objetivo_linea) if objetivo_linea else None
    if e.estado == "RUPTURA" and seguridad is None:
        avisos.append("la ruptura no tiene línea de seguridad trazable: el riesgo no se puede medir")
    if seguridad is not None and seguridad.empinada:
        avisos.append("la línea de seguridad es muy empinada: una vela de noticias puede cruzarla sin que cambie la tendencia")

    atr_d1 = _serie(velas, "D1", marcos).atr if "D1" in marcos.todos else 0.0
    atr_d1 = atr_d1 if atr_d1 > 0 else s.atr
    metricas = {"atr": s.atr, "atr_d1": atr_d1, "confluencia": a_favor,
                "dist_vigilar_atr_d1": abs(precio - vigilar.precio) / atr_d1}
    if seguridad is not None:
        metricas["dist_seguridad_atr_d1"] = abs(precio - seguridad.valor_actual) / atr_d1
        metricas["semanas_principal"] = calificar(e.seguridad, s, p).semanas
    if accion is not None:
        metricas["dist_accion_atr_d1"] = abs(precio - accion.valor_actual) / atr_d1
    if objetivo is not None:
        metricas["dist_objetivo_atr_d1"] = abs(precio - objetivo.precio) / atr_d1
    if e.velas_desde_ruptura is not None:
        metricas["velas_desde_ruptura"] = float(e.velas_desde_ruptura)
    zona = p.tolerancia_horizontal_atr * s.atr
    metricas["doble_confirmacion"] = 1.0 if any(abs(h.precio - vigilar.precio) <= zona
                                                for h, _, _ in horizontales) else 0.0
    metricas["contra_secuencia"] = 1.0 if contra else 0.0

    return Lectura(
        ticker=ticker, marco=op, precio=precio, direccion=e.direccion, estado=estado,
        lineas=tuple(lineas), en_prueba=prueba, vigilar=vigilar, invalidacion=invalidacion,
        objetivo=objetivo,
        escenarios=textos.escenarios(estado, e.direccion, op, digits, precio, vigilar,
                                     invalidacion, objetivo, prueba, rango),
        salida=textos.salida(estado, op, invalidacion, digits, linea_seguimiento),
        conceptos=textos.conceptos(estado), avisos=tuple(avisos), metricas=metricas,
        vela=s.times[-1],
    )
