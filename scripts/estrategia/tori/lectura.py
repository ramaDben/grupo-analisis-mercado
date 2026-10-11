"""Lectura de Tori: de las líneas trazadas a la Lectura del contrato (spec §5, lectura.py).

Las velas cerradas mandan: líneas, toques, calidad, dirección y RUPTURA salen
solo de ellas. La vela en curso, si llega, solo puede poner el estado PRUEBA
encima (spec §4, "La vela abierta"); lo agrega la Task S3-2.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from estrategia.contrato import Lectura, Linea, Marcos, Prueba, Referencia, VelaEnCurso, exigir_velas
from estrategia.tori import textos
from estrategia.tori.calidad import calificar
from estrategia.tori.horizontales import Horizontal, bordes_rango, detectar
from estrategia.tori.lineas import Trazo, seguimiento, trazar
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, serie_de


AVISO_RANGO = "sin línea diagonal vigente: se lee como rango entre el máximo y el mínimo de la última semana"
AVISO_CONTRA = "la lectura va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas"
AVISO_SIN_SEGURIDAD = "la ruptura no tiene línea de seguridad trazable: el riesgo no se puede medir"
AVISO_EMPINADA = ("la línea de seguridad es muy empinada: una vela de noticias puede cruzarla sin que "
                  "cambie la tendencia")


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
    """El precio vivo al otro lado de una línea vigente, por más que la tolerancia.

    Cuenta el precio vivo y no el extremo de la vela: una mecha que ya volvió no
    activa la prueba (spec §4). El orden de `vivas` (acción, seguridad, rango) es
    la prioridad.
    """
    if en_curso is None:
        return None
    for linea, valor_ahora in vivas:
        antes = cierre - linea.valor_actual
        ahora = en_curso.precio - valor_ahora
        if antes * ahora < 0 and abs(ahora) > tol:
            return Prueba(linea, round(valor_ahora, digits), en_curso.cierre)
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
        if x.tipo == "horizontal":
            # Un borde de rango que el precio dejó atrás: abajo era la resistencia.
            return Referencia(x.valor_actual, textos.borde(x.valor_actual < precio), x)
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
        avisos.append(AVISO_RANGO)
    lineas += rango

    contexto, a_favor, contra = _contexto(velas, marcos, e.direccion, p, digits)
    lineas += contexto
    if contra:
        avisos.append(AVISO_CONTRA)

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
        avisos.append(AVISO_SIN_SEGURIDAD)
    if seguridad is not None and seguridad.empinada:
        avisos.append(AVISO_EMPINADA)

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


def divergencia(preparada: Lectura, actual: Lectura) -> str | None:
    """Motivo por el que el texto preparado ya no vale, o None (spec §4)."""
    if preparada.estado == "PRUEBA" and (
        actual.estado != "PRUEBA" or actual.en_prueba.cierre_vela != preparada.en_prueba.cierre_vela
    ):
        return "la vela que estaba en prueba ya cerró: el texto se escribió para una condición que se resolvió"
    if actual.direccion != preparada.direccion:
        return f"la dirección cambió de {preparada.direccion.lower()} a {actual.direccion.lower()}"
    # Entre TENDENCIA y REBOTE la estructura es la misma: el texto sigue valiendo (hueco 13).
    if actual.estado != preparada.estado and {actual.estado, preparada.estado} != {"TENDENCIA", "REBOTE"}:
        return f"el estado cambió de {preparada.estado.lower()} a {actual.estado.lower()}"
    for campo in ("vigilar", "invalidacion"):
        antes, ahora = getattr(preparada, campo), getattr(actual, campo)
        if antes is not None and ahora is not None and \
                (preparada.precio - antes.precio) * (actual.precio - ahora.precio) < 0:
            return f"el precio cruzó la {ahora.etiqueta}, que hoy está en {ahora.precio}"
    return None


def _valorador(velas: dict[str, pd.DataFrame], marcos: Marcos, ticker: str):
    """Valor de una línea fija en cualquier vela de su marco, contado en velas desde sus anclas.

    Usa todas las velas recibidas y no la ventana de `leer()`: las anclas del lunes tienen
    que seguir dentro aunque la ventana haya avanzado.
    """
    indices = {m: {int(ts): i for i, ts in enumerate(velas[m]["time"])} for m in marcos.todos}

    def valor(linea: Linea, i: float) -> float:
        if linea.tipo == "horizontal":
            return linea.puntos[0][1]
        (t1, p1), (t2, p2) = linea.puntos
        try:
            i1, i2 = indices[linea.marco][t1], indices[linea.marco][t2]
        except KeyError:
            raise ValueError(
                f"{ticker}: las anclas de una línea {linea.rol} de {linea.marco} ya no caben en la "
                "ventana de velas; hay que pedir velas desde la referencia"
            ) from None
        return p1 + (p2 - p1) / (i2 - i1) * (i - i1)

    return valor, indices


def seguir(ticker: str, referencia: Lectura, velas: dict[str, pd.DataFrame], digits: int,
           en_curso: VelaEnCurso | None, marcos: Marcos, p: Parametros) -> Lectura:
    """La lectura de hoy contra la referencia del lunes, sin volver a trazar (spec §4).

    Las anclas no se mueven: una diagonal avanza por su pendiente y un horizontal vale lo
    mismo toda la semana. Una línea que cerró al otro lado por más que la tolerancia deja el
    estado en RUPTURA; el consumidor reemplaza entonces la referencia por la `leer()` de ese
    cierre (decisión del director, 2026-10-10).

    En una referencia en RUPTURA, la línea rota ya no sostiene nada: volver a cerrar al
    otro lado de ella no es otra ruptura, es la ruptura falsa ("la ruptura deja de serlo
    cuando el precio vuelve a cerrar adentro", hueco 5). La referencia caduca y se
    devuelve la `leer()` de hoy. Lo mismo vale para una línea que se rompe después de la
    referencia: si el precio vuelve a cerrar adentro, la ruptura fue falsa y la referencia
    caduca (no se informa una RUPTURA con el precio de vuelta). La ruptura falsa gana sobre
    la ruptura de otra línea sin importar cuál ocurrió primero, y entrega anclas nuevas
    (`leer()`) en vez de reasignar roles: el consumidor reemplaza la referencia en los dos
    casos.
    """
    exigir_velas(velas, marcos)
    if referencia.estado == "PRUEBA":
        raise ValueError(f"{ticker}: una referencia no puede quedar en PRUEBA; se guarda con la vela cerrada")
    op = marcos.operativo
    s = serie_de(velas[op].reset_index(drop=True))
    if s.atr <= 0:
        raise ValueError(f"{ticker}: las velas de {op} no tienen rango (ATR 0); no hay nada que leer")
    valor, indices = _valorador(velas, marcos, ticker)
    if referencia.vela not in indices[op]:
        raise ValueError(f"{ticker}: la vela de la referencia ya no cabe en la ventana de {op}")
    i_ref = indices[op][referencia.vela]
    ultimo = len(s) - 1
    tol = p.tolerancia_toque_atr * s.atr
    lineas = [replace(x, valor_actual=round(valor(x, len(indices[x.marco]) - 1), digits))
              for x in referencia.lineas]

    rota_ref = (next((x for x in lineas if x.rol == "accion" and x.marco == op), None)
                if referencia.estado == "RUPTURA" else None)

    def sostiene(x: Linea) -> bool:
        return x.marco == op and x.rol in ("accion", "seguridad", "rango") and x is not rota_ref

    def cruce(x: Linea) -> int | None:
        """Primera vela posterior a la referencia que cierra al otro lado por más que la tolerancia."""
        lado = s.closes[i_ref] - valor(x, i_ref)
        for i in range(i_ref + 1, len(s)):
            ahora = s.closes[i] - valor(x, i)
            if lado * ahora < 0 and abs(ahora) > tol:
                return i
        return None

    def volvio(x: Linea, i: int) -> bool:
        """Tras romper en la vela i, el precio volvió a cerrar adentro (hueco 5).

        Vuelve si un cierre posterior cruza de regreso por más que la tolerancia, o si el
        último cierre ya no queda afuera por más que la tolerancia.
        """
        afuera = s.closes[i] - valor(x, i)
        if any(afuera * (s.closes[j] - valor(x, j)) < 0 and abs(s.closes[j] - valor(x, j)) > tol
               for j in range(i + 1, len(s))):
            return True
        final = s.closes[ultimo] - valor(x, ultimo)
        return not (afuera * final > 0 and abs(final) > tol)

    def falsa() -> Lectura:
        nueva = leer(ticker, velas, digits, en_curso, marcos, p)
        return replace(nueva, avisos=nueva.avisos + (
            "la ruptura del análisis semanal fue falsa: el precio volvió a cerrar al otro lado de "
            "la línea rota y la lectura de este cierre pasa a ser la nueva referencia",))

    if rota_ref is not None and cruce(rota_ref) is not None:
        return falsa()

    ruptura: tuple[int, Linea] | None = None
    for x in lineas:
        i = cruce(x) if sostiene(x) else None
        if i is not None and (ruptura is None or i < ruptura[0]):
            ruptura = (i, x)
    # Una línea que se rompió después de la referencia y a la que el precio volvió es la
    # misma ruptura falsa que la de la línea rota del lunes: la referencia caduca.
    if ruptura is not None and volvio(ruptura[1], ruptura[0]):
        return falsa()

    # El rebote se vuelve a medir con la última vela de hoy: dura una vela (hueco 13).
    estado = "TENDENCIA" if referencia.estado == "REBOTE" else referencia.estado
    direccion = referencia.direccion
    avisos = list(referencia.avisos)
    objetivo = referencia.objetivo
    if ruptura is not None:
        i, rota = ruptura
        estado = "RUPTURA"
        direccion = "ALCISTA" if s.closes[i] > valor(rota, i) else "BAJISTA"
        if direccion != referencia.direccion:
            objetivo = None  # el objetivo del lunes era para la otra dirección
        sube = direccion == "ALCISTA"
        nuevas = []
        for x in lineas:
            if x is rota:
                nuevas.append(replace(x, rol="accion"))
            elif (sostiene(x) or x is rota_ref) and x.tipo == "diagonal":
                # La opuesta queda a favor de la operación: bajo el precio en una compra (V18).
                a_favor = x.valor_actual < s.closes[ultimo] if sube else x.valor_actual > s.closes[ultimo]
                nuevas.append(replace(x, rol="seguridad" if a_favor else "contexto"))
            else:
                nuevas.append(x)
        lineas = nuevas
        # Los avisos del lunes que describen un estado que ya no rige se caen: el de rango,
        # el de la seguridad (se vuelve a medir abajo) y el de la secuencia si la dirección dio
        # vuelta, porque se midió para la otra dirección.
        avisos = [a for a in avisos if a == AVISO_CONTRA and direccion == referencia.direccion]
        avisos.append(f"{textos.rota(rota, sube)} del análisis semanal se rompió por cierre: "
                      "la lectura de este cierre pasa a ser la nueva referencia")

    accion = next((x for x in lineas if x.rol == "accion" and x.marco == op), None)
    seguridad = next((x for x in lineas if x.rol == "seguridad" and x.marco == op), None)
    rango = [x for x in lineas if x.rol == "rango"]
    if ruptura is not None:
        if seguridad is None:
            avisos.append(AVISO_SIN_SEGURIDAD)
        elif seguridad.empinada:
            avisos.append(AVISO_EMPINADA)
    linea_seguimiento = next((x for x in lineas if x.rol == "seguimiento"), None)
    cierre = s.closes[-1]
    precio = en_curso.precio if en_curso is not None else cierre
    if estado == "TENDENCIA" and seguridad is not None and \
            _rebote(s, valor(seguridad, ultimo), textos.sentido(seguridad), tol):
        estado = "REBOTE"
    vivas = [(x, valor(x, len(s))) for x in lineas
             if sostiene(x) and not (estado == "RUPTURA" and x.rol == "accion")]
    prueba = _prueba(vivas, cierre, en_curso, tol, digits)
    vigilar = _vigilar(prueba, estado, accion, seguridad, rango, precio)
    invalidacion = (Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
                    if seguridad is not None else None)

    atr_d1 = serie_de(velas["D1"]).atr if "D1" in marcos.todos else 0.0
    atr_d1 = atr_d1 if atr_d1 > 0 else s.atr
    fijas = ("confluencia", "contra_secuencia", "doble_confirmacion", "semanas_principal")
    metricas = {k: v for k, v in referencia.metricas.items() if k in fijas}
    metricas.update({"atr": s.atr, "atr_d1": atr_d1,
                     "dist_vigilar_atr_d1": abs(precio - vigilar.precio) / atr_d1})
    if seguridad is not None:
        metricas["dist_seguridad_atr_d1"] = abs(precio - seguridad.valor_actual) / atr_d1
    if accion is not None:
        metricas["dist_accion_atr_d1"] = abs(precio - accion.valor_actual) / atr_d1
    if objetivo is not None:
        metricas["dist_objetivo_atr_d1"] = abs(precio - objetivo.precio) / atr_d1
    if ruptura is not None:
        metricas["velas_desde_ruptura"] = float(ultimo - ruptura[0])

    final = "PRUEBA" if prueba is not None else estado
    return Lectura(
        ticker=ticker, marco=op, precio=precio, direccion=direccion, estado=final,
        lineas=tuple(lineas), en_prueba=prueba, vigilar=vigilar, invalidacion=invalidacion,
        objetivo=objetivo,
        escenarios=textos.escenarios(final, direccion, op, digits, precio, vigilar, invalidacion,
                                     objetivo, prueba, rango),
        salida=textos.salida(final, op, invalidacion, digits, linea_seguimiento),
        conceptos=textos.conceptos(final), avisos=tuple(avisos), metricas=metricas,
        vela=s.times[-1],
    )
