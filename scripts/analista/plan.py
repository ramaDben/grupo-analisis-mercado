"""El plan de escenarios del informe de activo, escrito por Python y no por agy.

Sale de la `Lectura` de la estrategia activa (enchufe de estrategia, S7): el gatillo es lo
que la estrategia vigila, con su escenario a favor tal cual; la invalidación es su línea de
seguridad; la salida es su regla. Habla en condicional e impersonal: describe un
escenario, no le dice a nadie qué hacer, porque el informe es general y nadie en GI está
inscrito como asesor de inversión.

Sin estadística, sin objetivo fijo y sin recorrido (spec §8.4): no habrá backtesting, y
ninguna pieza da una tasa de acierto. El Chandelier y su medición se borraron.
"""
from __future__ import annotations

from typing import Any

ESTADO = {
    "TENDENCIA": "Armado: el precio todavía no cruza el gatillo.",
    "REBOTE": "Armado: la última vela tocó la línea de seguridad y cerró a favor.",
    "RUPTURA": "Activado: una vela cerró al otro lado de la línea que se vigilaba.",
}


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def armar(lectura, digits: int, nombre: str) -> dict[str, Any]:
    """El plan a favor de la dirección de la lectura, o el motivo por el que no hay plan."""
    sesgo = {"ALCISTA": "Alcista", "BAJISTA": "Bajista"}.get(lectura.direccion, "Lateral")
    if lectura.estado == "RANGO" or lectura.direccion == "LATERAL":
        return {"hay_plan": False, "sesgo": sesgo,
                "motivo": f"Hoy {nombre} se mueve en rango, sin una tendencia que seguir: el escenario "
                          "es esperar que el precio salga por uno de los bordes."}
    if lectura.invalidacion is None:
        return {"hay_plan": False, "sesgo": sesgo,
                "motivo": f"Hoy {nombre} no tiene una línea de seguridad trazable: sin ella no se puede "
                          "decir dónde se anula el escenario, y no hay plan que proponer."}
    flecha = "⬆️" if lectura.direccion == "ALCISTA" else "⬇️"
    a_favor = next(e for e in lectura.escenarios if e.flecha == flecha)
    lado = "bajo" if lectura.direccion == "ALCISTA" else "sobre"
    inv = lectura.invalidacion
    if lectura.estado == "PRUEBA":
        hora = lectura.en_prueba.cierre_vela.strftime("%H:%M")
        estado = (f"En prueba: el precio está al otro lado de una línea y se resuelve con el cierre de "
                  f"la vela de las {hora} (hora de Chile).")
    elif lectura.estado == "TENDENCIA" and lectura.vigilar.precio == inv.precio:
        # Lo que se vigila es la propia línea de seguridad: no hay gatillo pendiente, la
        # tendencia sigue mientras la respete.
        estado = "Vigente: la tendencia sigue mientras el precio respete su línea de seguridad."
    else:
        estado = ESTADO[lectura.estado]
    return {
        "hay_plan": True,
        "sesgo": sesgo,
        "gatillo": a_favor.texto,
        "invalidacion": f"El escenario se anula con un cierre {lado} {_fmt(inv.precio, digits)}, "
                        f"la {inv.etiqueta}.",
        "salida": lectura.salida,
        "estado": estado,
        "niveles": {"gatillo": lectura.vigilar.precio, "invalidacion": inv.precio, "vela": lectura.vela},
    }
