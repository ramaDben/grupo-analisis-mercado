"""El plan de escenarios del informe de activo, escrito por Python y no por agy.

Es lo que el informe trae y WhatsApp no: la condición, dónde se anula y qué tan
seguido funcionó antes, siempre contra una hora cualquiera con la misma
tendencia. Habla en condicional e impersonal: describe un escenario, no le dice
a nadie qué hacer, porque el informe es general y nadie en GI está inscrito como
asesor de inversión.

Sin objetivo de precio, a propósito: medido en septiembre, ningún objetivo fijo
tuvo expectativa positiva y la salida del director es el Chandelier. El
recorrido se da como distancia, nunca sumado al precio.
"""
from __future__ import annotations

from typing import Any

from analista.estadistica import CHANDELIER_K, MULT_RECORRIDO, VENTAJA_MINIMA, Estadistica


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def _fecha(iso: str) -> str:
    """AAAA-MM-DD a la notación chilena DD-MM-AAAA."""
    a, m, d = iso[:10].split("-")
    return f"{d}-{m}-{a}"


def _frase_estadistica(est: Estadistica | None, nombre: str) -> str:
    if est is None or est.pct_base is None:
        return "Sin historia suficiente del activo para medir esta condición."
    if est.pct_condicion is None:
        return f"Muestra insuficiente para una estadística ({est.casos} casos desde el {_fecha(est.desde)})."
    texto = (
        f"Desde el {_fecha(est.desde)}, esta condición se dio {est.casos} veces en {nombre}. El precio "
        f"recorrió 1,5 veces la volatilidad típica de una hora antes de tocar la invalidación en el "
        f"{est.pct_condicion} % de los casos. Desde una hora cualquiera del mismo período con la "
        f"misma tendencia, la misma regla se cumplió en el {est.pct_base} %."
    )
    if est.pct_condicion - est.pct_base < VENTAJA_MINIMA:
        texto += " En este activo la condición no ha mostrado ventaja frente a una hora cualquiera."
    return texto


def armar(h1: dict[str, Any], digits: int, sesgo: str, nombre: str,
          est: Estadistica | None, ultima_vela: dict[str, Any],
          activacion: float | None = None) -> dict[str, Any]:
    """Plan a favor del sesgo. `ultima_vela` trae close, hh22, ll22, atr22 y vela (su hora).

    `activacion` es el nivel de una ruptura ocurrida en las últimas 24 velas
    (`estadistica.activacion_reciente`). Cuando existe, ESE es el gatillo: el R1
    de ahora ya es la resistencia siguiente, y mostrarla diría "armado" justo
    después del evento que la estadística mide.
    """
    alcista = sesgo == "Alcista"
    clave = "r1" if alcista else "s1"
    if activacion is None and h1.get("niveles_origen", {}).get(clave) != "swing":
        return {
            "hay_plan": False, "sesgo": sesgo,
            "motivo": "Hoy el activo no tiene una estructura de precio medible a favor de su "
                      "tendencia: sin ese nivel no hay plan que proponer.",
        }
    gatillo = float(activacion) if activacion is not None else float(h1[clave])
    k_atr = CHANDELIER_K * float(ultima_vela["atr22"])
    invalidacion = float(ultima_vela["hh22"]) - k_atr if alcista else float(ultima_vela["ll22"]) + k_atr
    recorrido = MULT_RECORRIDO * float(h1["atr_14"])
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    cierre = float(ultima_vela["close"])
    anulado = cierre < invalidacion if alcista else cierre > invalidacion
    if activacion is None:
        estado = "Armado: el precio todavía no cruza el gatillo."
    elif anulado:
        estado = "Invalidado: tras activarse, el último cierre de 1 hora quedó del otro lado de la invalidación."
    else:
        estado = f"Activado: un cierre de 1 hora de las últimas 24 cruzó {lado} el gatillo."
    return {
        "hay_plan": True,
        "sesgo": sesgo,
        "gatillo": f"El escenario {sesgo.lower()} se activa con un cierre de vela de 1 hora "
                   f"{lado} {_fmt(gatillo, digits)}.",
        "invalidacion": f"El escenario se anula {borde} {_fmt(invalidacion, digits)}. Es una salida por "
                        "volatilidad, que se ajusta a favor a medida que el precio avanza.",
        "recorrido": f"Recorrido de referencia: 1,5 veces la volatilidad típica de una hora, unos "
                     f"{_fmt(recorrido, digits)}. Es una distancia, no un objetivo de precio.",
        "estadistica": _frase_estadistica(est, nombre),
        "estado": estado,
        "niveles": {"gatillo": gatillo, "invalidacion": round(invalidacion, digits),
                    "recorrido": round(recorrido, digits), "vela": str(ultima_vela["vela"])},
    }
