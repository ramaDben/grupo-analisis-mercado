"""El avance de la simulación de la semana contra la foto, y la lectura de hoy, por separado.

Dos cosas distintas, con el mismo peso (spec §6): la simulación se mide contra sus precios
FIJOS del lunes; la lectura de la estrategia sigue la línea en movimiento. Nunca en pesos
(dependen del volumen de cada ejecutivo) y nunca «si hubieras entrado ganarías X».
"""
from __future__ import annotations

from typing import Any

ESTADOS = ("entrada_pendiente", "en_curso", "objetivo", "stop", "sin_simulacion")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def evaluar(esc: dict[str, Any], velas: list[dict[str, Any]], precio_vivo: float) -> dict[str, Any]:
    """Recorre las velas 4H cerradas desde la foto y termina en el precio vivo.

    Si una misma vela toca el stop y el objetivo, cuenta stop: sin datos dentro de la vela
    no se sabe qué pasó primero, y se cuenta lo prudente.

    Con la entrada pendiente (el falso quiebre del rango) la entrada se activa en una vela que
    pasa por su precio **sin llegar al stop**. Una vela que cruza el borde y sigue hasta el stop
    es una ruptura del rango, no el falso quiebre que se simula: la entrada sigue pendiente y
    nunca se informa «stop tocado» de una entrada que no se activó (prueba real de la W41,
    cobre). En la vela que activa tampoco cuenta el objetivo: dentro de ella no se sabe qué
    tocó primero. El precio vivo se mide como un tramo desde el último cierre.
    """
    alcista = esc["direccion"] == "ALCISTA"
    entrada, stop, obj = float(esc["entrada"]), float(esc["stop"]), float(esc["objetivo"])
    activa = not esc.get("entrada_pendiente")
    previo = float(velas[-1]["close"]) if velas else precio_vivo
    tramos = [(float(x["high"]), float(x["low"])) for x in velas]
    tramos.append((max(previo, precio_vivo), min(previo, precio_vivo)))
    for alto, bajo in tramos:
        toca_stop = (bajo <= stop) if alcista else (alto >= stop)
        if not activa:
            if bajo <= entrada <= alto and not toca_stop:
                activa = True
            continue
        if toca_stop:
            return {"estado": "stop", "avance_pct": None}
        if (alto >= obj) if alcista else (bajo <= obj):
            return {"estado": "objetivo", "avance_pct": 100}
    if not activa:
        return {"estado": "entrada_pendiente", "avance_pct": None}
    avance = (precio_vivo - entrada) / (obj - entrada) * 100
    return {"estado": "en_curso", "avance_pct": int(avance + 0.5) if avance >= 0 else -int(-avance + 0.5)}


def paso_la_entrada(esc: dict[str, Any], precio: float) -> bool:
    """Con la entrada pendiente, si el precio está del lado del stop (fuera del rango)."""
    entrada = float(esc["entrada"])
    return precio < entrada if esc["direccion"] == "ALCISTA" else precio > entrada


def texto_simulacion(esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    estado = ev["estado"]
    if estado == "sin_simulacion":
        return f"Esta semana este activo no tiene simulación: {ev['motivo']}."
    if estado == "entrada_pendiente":
        if paso_la_entrada(esc, precio_vivo):
            return (f"El precio salió del rango y va en {f(precio_vivo)}: la simulación se activa si "
                    f"vuelve a la entrada de {f(esc['entrada'])}.")
        return f"El precio todavía no llega a la entrada de {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "stop":
        return f"El precio tocó el stop de {f(esc['stop'])}."
    if estado == "objetivo":
        return f"El precio alcanzó el objetivo 1:3 de {f(esc['objetivo'])}."
    pct = ev["avance_pct"]
    if pct >= 0:
        return f"En curso: el precio va en {f(precio_vivo)}, un {pct} % del recorrido hacia el objetivo."
    return (f"En curso: el precio va en {f(precio_vivo)}, un {-pct} % del recorrido en contra, "
            "sin tocar el stop.")


def texto_lectura(actual, reemplazada: bool, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    if reemplazada:
        return (f"La lectura de la semana cambió: ahora se vigila {actual.vigilar.etiqueta} "
                f"en {f(actual.vigilar.precio)}.")
    if actual.estado == "PRUEBA" and actual.en_prueba is not None:
        return (f"El precio está probando {actual.vigilar.etiqueta} en {f(actual.en_prueba.valor_ahora)}: "
                f"se define al cierre de la vela de las {actual.en_prueba.cierre_vela:%H:%M}.")
    return (f"La lectura del lunes sigue en pie: {actual.estado.lower()} "
            f"{actual.direccion.lower()}, con {actual.vigilar.etiqueta} en {f(actual.vigilar.precio)}.")


def mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict[str, Any], ev: dict[str, Any],
            precio_vivo: float, actual, reemplazada: bool, digits: int) -> str:
    """El texto de WhatsApp del seguimiento: las dos cosas, con el mismo peso."""
    from analista.comercial import AVISO_PIEZA

    f = lambda x: _fmt(x, digits)  # noqa: E731
    if ev["estado"] == "sin_simulacion":
        simulacion = ["🎯 *Simulación de la semana*", texto_simulacion(esc, ev, precio_vivo, digits)]
    else:
        simulacion = [f"🎯 *Simulación de la semana* (precios del {fecha_foto})",
                      texto_simulacion(esc, ev, precio_vivo, digits),
                      f"Entrada {f(esc['entrada'])} · Stop {f(esc['stop'])} · Objetivo 1:3 {f(esc['objetivo'])}"]
    return "\n".join([
        f"📊 *{nombre}* · actualización del {fecha_hoy}",
        "Te envío una actualización del análisis de la semana.",
        SEPARADOR,
        *simulacion,
        SEPARADOR,
        "📈 *Lectura técnica hoy*",
        texto_lectura(actual, reemplazada, digits),
        SEPARADOR,
        AVISO_PIEZA,
    ])
