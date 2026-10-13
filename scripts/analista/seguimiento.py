"""El avance de la simulación de la semana contra la foto, y la lectura de hoy, por separado.

Dos cosas distintas, con el mismo peso (spec §6): la simulación se mide contra sus precios
FIJOS del lunes; la lectura de la estrategia sigue la línea en movimiento. Nunca en pesos
(dependen del volumen de cada ejecutivo) y nunca «si hubieras entrado ganarías X».
"""
from __future__ import annotations

from typing import Any

ESTADOS = ("entrada_pendiente", "en_curso", "objetivo", "stop", "rango_roto", "descartada", "sin_simulacion")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def _retesteo_fuera_de_rango(esc: dict[str, Any]) -> bool:
    return esc.get("condicion") == "retesteo" and esc.get("estado") != "RANGO"


def evaluar(esc: dict[str, Any], velas: list[dict[str, Any]], precio_vivo: float) -> dict[str, Any]:
    """Recorre las velas 4H cerradas desde la foto y termina en el precio vivo.

    Si una misma vela toca el stop y el objetivo, cuenta stop: sin datos dentro de la vela
    no se sabe qué pasó primero, y se cuenta lo prudente.

    Con la entrada pendiente (el falso quiebre del rango) la entrada se activa en una vela que
    pasa por su precio **sin llegar al stop**. Una vela que cruza el borde y sigue hasta el stop
    es una ruptura del rango, no el falso quiebre que se simula: la simulación queda descartada
    («rango_roto»), nunca «stop tocado» de una entrada que no se activó ni «pendiente» de un
    precio que ya no vale (director, 2026-10-12, tras la prueba real de la W41, cobre). En la
    vela que activa tampoco cuenta el objetivo: dentro de ella no se sabe qué tocó primero. El
    precio vivo se mide como un tramo desde el último cierre.

    La entrada por quiebre (`condicion == "quiebre"`) se activa con el CIERRE de una vela 4H al
    otro lado del nivel, y antes de eso el stop no cuenta: el precio viene justamente de ese
    lado. El tramo vivo no activa, porque todavía no cerró. Un retesteo que no es de rango y se
    rompe sin activar queda «descartada».
    """
    alcista = esc["direccion"] == "ALCISTA"
    entrada, stop, obj = float(esc["entrada"]), float(esc["stop"]), float(esc["objetivo"])
    activa = not esc.get("entrada_pendiente")
    quiebre = esc.get("condicion") == "quiebre"
    roto = "descartada" if _retesteo_fuera_de_rango(esc) else "rango_roto"
    previo = float(velas[-1]["close"]) if velas else precio_vivo
    tramos = [(float(x["high"]), float(x["low"]), float(x["close"])) for x in velas]
    tramos.append((max(previo, precio_vivo), min(previo, precio_vivo), None))
    for alto, bajo, cierre in tramos:
        toca_stop = (bajo <= stop) if alcista else (alto >= stop)
        if not activa:
            if quiebre:
                activa = cierre is not None and ((cierre > entrada) if alcista else (cierre < entrada))
                continue
            if toca_stop:
                return {"estado": roto, "avance_pct": None}
            if bajo <= entrada <= alto:
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
    if estado == "entrada_pendiente" and esc.get("condicion") == "quiebre":
        return (f"La simulación se activa si una vela de 4 horas cierra "
                f"{'sobre' if esc['direccion'] == 'ALCISTA' else 'bajo'} {f(esc['entrada'])}: "
                f"el precio va en {f(precio_vivo)}.")
    if estado == "entrada_pendiente" and _retesteo_fuera_de_rango(esc):
        return f"La simulación se activa si el precio vuelve a {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "descartada":
        return (f"El precio rompió {f(esc['entrada'])} sin activar la entrada y va en {f(precio_vivo)}: "
                "la simulación de esta semana queda descartada.")
    if estado == "entrada_pendiente":
        if paso_la_entrada(esc, precio_vivo):
            return (f"El precio salió del rango y va en {f(precio_vivo)}: la simulación se activa si "
                    f"vuelve a la entrada de {f(esc['entrada'])}.")
        return f"El precio todavía no llega a la entrada de {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "rango_roto":
        return (f"El precio rompió el rango y va en {f(precio_vivo)}: la simulación de esta semana "
                "queda descartada.")
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


MARCA_SALUDO = "[[SALUDO]]"
SALUDO_POR_DEFECTO = "Hola,"
CIERRE = "Si quieres, lo conversamos."


def saludo_de(texto: str) -> str:
    """Cómo abre el mensaje: lo que el ejecutivo escribió, o un saludo neutro.

    «Estimado Sr. Pérez» se usa tal cual (con su puntuación); un nombre suelto queda «Hola Juan,».
    """
    texto = (texto or "").strip()
    if not texto:
        return SALUDO_POR_DEFECTO
    if not texto.lower().startswith(("estimad", "apreciad")):
        texto = f"Hola {texto}"
    return texto if texto[-1] in ":,;." else texto + ","


def con_saludo(whatsapp: str, saludo: str = "") -> str:
    """Pone el saludo del ejecutivo donde la pieza guardada dejó la marca.

    La pieza se reusa entre ejecutivos, así que el saludo no se guarda con ella.
    """
    return whatsapp.replace(MARCA_SALUDO, saludo_de(saludo))


def _arranque(nombre: str, esc: dict[str, Any], ev: dict[str, Any]) -> str:
    """La primera línea: dice el estado, para que dos mensajes de dos días no abran igual."""
    estado = ev["estado"]
    cabeza = f"te cuento cómo va {nombre}"
    if estado == "sin_simulacion":
        return f"{cabeza}: esta semana no tiene simulación, y te dejo la lectura de hoy."
    frase = {
        "entrada_pendiente": "todavía espera su entrada",
        "objetivo": "llegó a su objetivo",
        "stop": "tocó su stop",
        "rango_roto": "quedó descartada",
        "descartada": "quedó descartada",
    }.get(estado)
    if estado == "en_curso":
        frase = "avanza a favor" if ev["avance_pct"] >= 0 else "va en contra por ahora, sin tocar el stop"
    return f"{cabeza}: la simulación de esta semana {frase}."


def mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict[str, Any], ev: dict[str, Any],
            precio_vivo: float, actual, reemplazada: bool, digits: int) -> str:
    """El texto de WhatsApp del seguimiento, escrito como quien retoma una conversación.

    Abre con la marca del saludo (`con_saludo` la reemplaza al responder), dice el estado en las
    dos primeras líneas y después informa por separado, con el mismo peso, la simulación fijada el
    lunes y la lectura de hoy.
    """
    from analista.comercial import AVISO_PIEZA

    f = lambda x: _fmt(x, digits)  # noqa: E731
    sin = ev["estado"] == "sin_simulacion"
    simulacion = [] if sin else [
        f"🎯 *Simulación de la semana* (precios del {fecha_foto})",
        f"Entrada {f(esc['entrada'])} · Stop {f(esc['stop'])} · Objetivo 1:3 {f(esc['objetivo'])}",
        SEPARADOR]
    return "\n".join([
        f"{MARCA_SALUDO} {_arranque(nombre, esc, ev)}",
        texto_simulacion(esc, ev, precio_vivo, digits),
        SEPARADOR,
        *simulacion,
        f"📈 *Lectura técnica hoy* ({fecha_hoy})",
        texto_lectura(actual, reemplazada, digits),
        SEPARADOR,
        CIERRE,
        SEPARADOR,
        AVISO_PIEZA,
    ])
