"""Textos de la lámina, nota semanal y mensaje de WhatsApp para el seguimiento de un solo suceso.

Plan: docs/superpowers/plans/2026-10-21-seguimiento-suceso-unico.md (Task 3).
"""
from __future__ import annotations

from analista.seguimiento import MARCA_SALUDO, _activo_con_articulo, _fmt
from analista.suceso import Resumen


def lamina(r: Resumen, digits: int) -> tuple[str, str, str]:
    """Devuelve (flecha, titular, linea_chica) para la lámina de seguimiento diario."""
    if r.estado == "sin_direccion":
        return ("↔️", "Hoy el precio se mueve en rango", "Esperamos que salga de la zona antes de marcar un nivel")
    if r.estado == "cerrado":
        return ("↔️", "El mercado está cerrado", "El seguimiento de hoy parte con la apertura")

    nivel_str = _fmt(r.nivel, digits) if r.nivel is not None else ""
    obj_str = _fmt(r.objetivo, digits) if r.objetivo is not None else ""
    sig_str = _fmt(r.siguiente, digits) if r.siguiente is not None else ""

    if r.estado == "semana":
        bajista = r.sentido == "BAJISTA"
        rumbo, lado = ("a la baja", "sobre") if bajista else ("al alza", "bajo")
        titular = f"La semana sigue {rumbo}: el precio consolida {'bajo' if bajista else 'sobre'} {nivel_str}"
        linea_chica = (f"Mientras no cierre {lado} {nivel_str}, el objetivo es {obj_str}. "
                       "Esperamos una señal clara de hoy para el punto de entrada"
                       if r.objetivo is not None
                       else f"Mientras no cierre {lado} {nivel_str}, la tendencia de la semana sigue vigente")
        return ("⬇️" if bajista else "⬆️", titular, linea_chica)

    if r.sentido == "BAJISTA":
        if r.estado == "esperando":
            titular = f"Esperamos los {nivel_str} para un rechazo a la baja"
            linea_chica = (
                f"Si se da, el siguiente paso es {obj_str}"
                if r.objetivo is not None
                else "Lo confirma una vela de 5 minutos que rechace bajo la línea"
            )
            return ("⬇️", titular, linea_chica)

        if r.estado == "en_nivel":
            return (
                "⬇️",
                f"El precio está en los {nivel_str}: aquí se define el rechazo",
                "Lo confirma una vela de 5 minutos que cierre bajo la línea",
            )

        if r.estado == "rebotando":
            titular = (
                f"Se devolvió en los {nivel_str} y va camino a {obj_str}"
                if r.objetivo is not None
                else f"Se devolvió en los {nivel_str}: la presión sigue a la baja"
            )
            return ("⬇️", titular, f"La línea de control sigue en {nivel_str}")

        if r.estado == "cumplido":
            return (
                "✅",
                f"Se devolvió en los {nivel_str} y llegó a {obj_str}",
                "Lectura cumplida",
            )

        if r.estado == "ruptura":
            linea_chica = (
                f"El siguiente nivel a vigilar es {sig_str}"
                if r.siguiente is not None
                else "Esperamos que el precio defina antes de leer otro nivel"
            )
            return (
                "⬆️",
                f"Superó los {nivel_str}: ahora la fuerza es al alza",
                linea_chica,
            )

    # Alcista (por defecto)
    if r.estado == "esperando":
        titular = f"Esperamos los {nivel_str} para un rebote al alza"
        linea_chica = (
            f"Si se da, el siguiente paso es {obj_str}"
            if r.objetivo is not None
            else "Lo confirma una vela de 5 minutos que rebote sobre la línea"
        )
        return ("⬆️", titular, linea_chica)

    if r.estado == "en_nivel":
        return (
            "⬆️",
            f"El precio está en los {nivel_str}: aquí se define el rebote",
            "Lo confirma una vela de 5 minutos que cierre sobre la línea",
        )

    if r.estado == "rebotando":
        titular = (
            f"Rebotó en los {nivel_str} y va camino a {obj_str}"
            if r.objetivo is not None
            else f"Rebotó en los {nivel_str}: la fuerza sigue al alza"
        )
        return ("⬆️", titular, f"La línea de control sigue en {nivel_str}")

    if r.estado == "cumplido":
        return (
            "✅",
            f"Rebotó en los {nivel_str} y llegó a {obj_str}",
            "Lectura cumplida",
        )

    if r.estado == "ruptura":
        linea_chica = (
            f"El siguiente nivel a vigilar es {sig_str}"
            if r.siguiente is not None
            else "Esperamos que el precio defina antes de leer otro nivel"
        )
        return (
            "⬇️",
            f"Perdió los {nivel_str}: ahora la presión es a la baja",
            linea_chica,
        )

    raise ValueError(f"Estado desconocido para lámina: {r.estado!r}")


def nota_semana(sentido: str | None, direccion_semana: str | None, reemplazada: bool) -> str:
    """Texto opcional que complementa la lámina o el WhatsApp cuando el marco semanal lo amerita."""
    dir_sem = (direccion_semana or "").upper()
    sen = (sentido or "").upper()

    if reemplazada:
        if dir_sem == "ALCISTA":
            return "Ojo: lo que vimos el lunes cambió. La semana ahora se lee al alza."
        if dir_sem == "BAJISTA":
            return "Ojo: lo que vimos el lunes cambió. La semana ahora se lee a la baja."
        return "La semana ahora no marca dirección."

    if dir_sem in ("ALCISTA", "BAJISTA") and sen and dir_sem != sen:
        rumbo = "al alza" if dir_sem == "ALCISTA" else "a la baja"
        return f"Es un retroceso de hoy: la tendencia de la semana sigue {rumbo}."

    return ""


def whatsapp(r: Resumen, nombre: str) -> str:
    """Mensaje breve de WhatsApp para el cliente: con saludo, sin precios y con CFD una sola vez."""
    el, _ = _activo_con_articulo(nombre)
    activo_cfd = f"{el} (CFD)"

    if r.estado == "sin_direccion":
        cuerpo = f"hoy {activo_cfd} se mueve en rango, así que esperamos que salga de la zona antes de tomar un nivel. Te aviso apenas lo haga."
    elif r.estado == "cerrado":
        cuerpo = f"{activo_cfd} todavía no abre. Apenas cotice te mando el nivel del día."
    elif r.estado == "semana":
        rumbo = "a la baja" if r.sentido == "BAJISTA" else "al alza"
        cuerpo = (f"la tendencia de la semana en {activo_cfd} sigue {rumbo} y hoy el precio está consolidando. "
                  "Te dejé la lámina con el nivel que la sostiene y el objetivo, ¿lo revisamos?")
    elif r.sentido == "BAJISTA":
        if r.estado == "esperando":
            cuerpo = f"hoy estamos esperando que {activo_cfd} llegue a su nivel del día para un rechazo a la baja. Te dejé la lámina con el punto exacto, ¿lo revisamos cuando llegue?"
        elif r.estado == "en_nivel":
            cuerpo = f"{activo_cfd} está justo en su nivel del día y ahí se define el rechazo a la baja. Te dejé la lámina con el punto exacto, ¿lo miramos juntos?"
        elif r.estado == "rebotando":
            cuerpo = f"{activo_cfd} se devolvió en su nivel del día y va a la baja. En la lámina está el punto al que apunta, ¿lo seguimos?"
        elif r.estado == "cumplido":
            cuerpo = f"lo que esperábamos hoy se cumplió: {activo_cfd} se devolvió en su nivel y llegó al objetivo. Te dejé la lámina para que lo veas."
        elif r.estado == "ruptura":
            cuerpo = f"{activo_cfd} superó su nivel del día y ahora la fuerza es al alza. Te dejé la lámina con lo que viene, ¿lo conversamos?"
        else:
            raise ValueError(f"Estado desconocido para WhatsApp bajista: {r.estado!r}")
    else:  # Alcista
        if r.estado == "esperando":
            cuerpo = f"hoy estamos esperando que {activo_cfd} llegue a su nivel del día para un rebote al alza. Te dejé la lámina con el punto exacto, ¿lo revisamos cuando llegue?"
        elif r.estado == "en_nivel":
            cuerpo = f"{activo_cfd} está justo en su nivel del día y ahí se define el rebote al alza. Te dejé la lámina con el punto exacto, ¿lo miramos juntos?"
        elif r.estado == "rebotando":
            cuerpo = f"{activo_cfd} rebotó en su nivel del día y va al alza. En la lámina está el punto al que apunta, ¿lo seguimos?"
        elif r.estado == "cumplido":
            cuerpo = f"lo que esperábamos hoy se cumplió: {activo_cfd} rebotó en su nivel y llegó al objetivo. Te dejé la lámina para que lo veas."
        elif r.estado == "ruptura":
            cuerpo = f"{activo_cfd} perdió su nivel del día y ahora la presión es a la baja. Te dejé la lámina con lo que viene, ¿lo conversamos?"
        else:
            raise ValueError(f"Estado desconocido para WhatsApp alcista: {r.estado!r}")

    mensaje = f"{MARCA_SALUDO} {cuerpo}"
    if r.nota_semana:
        mensaje = f"{mensaje} {r.nota_semana}"
    return mensaje
