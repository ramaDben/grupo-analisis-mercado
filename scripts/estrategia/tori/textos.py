"""Textos de cliente de Tori: escenarios, salida y conceptos (spec §5, textos.py).

Reglas de texto de cliente: sin guion largo, tuteo chileno sin voseo, flechas,
precios con los digits del activo. La ruptura se describe como "cerró al otro
lado de la línea" (doctrina 2.4).
"""
from __future__ import annotations

from estrategia.contrato import Escenario, Linea, Prueba, Referencia

VELA = {"H1": "una vela de 1 hora", "H4": "una vela de 4 horas", "D1": "una vela diaria",
        "W1": "una vela semanal"}
LA_VELA = {"H1": "la vela de 1 hora", "H4": "la vela de 4 horas", "D1": "la vela diaria",
           "W1": "la vela semanal"}


def _p(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc  # el formato de precio es infraestructura (spec §3)

    return pc.formatear_precio(valor, digits)


def sentido(linea: Linea) -> str:
    """Pendiente de la línea leída de sus precios, que vienen redondeados a los digits.

    Con pocos decimales una línea poco inclinada puede redondear sus dos anclas al mismo
    precio: entonces la pendiente se lee contra el valor de hoy, que está más lejos. Si
    también empata, a esa precisión la línea es horizontal.
    """
    if linea.tipo == "horizontal":
        return "horizontal"
    (_, a), (_, b) = linea.puntos
    if a == b:
        b = linea.valor_actual
    if a == b:
        return "horizontal"
    return "alcista" if b > a else "bajista"


def borde(arriba: bool) -> str:
    """El borde horizontal de un rango, en la terminología de niveles (soporte/resistencia)."""
    return "resistencia del rango" if arriba else "soporte del rango"


def rota(linea: Linea | None, sube: bool) -> str:
    """Cómo se nombra la línea que el precio cruzó al romper, según la línea misma.

    Un borde horizontal es la resistencia o el soporte del rango (nunca una "línea
    bajista"); una diagonal se nombra por su pendiente.
    """
    if linea is None:
        return f"la línea {'bajista' if sube else 'alcista'}"
    if linea.tipo == "horizontal":
        return f"{'la' if sube else 'el'} {borde(sube)}"
    return f"la línea {sentido(linea)}"


def conceptos(estado: str) -> tuple[str, ...]:
    return {
        "TENDENCIA": ("linea-de-tendencia", "linea-de-seguridad"),
        "REBOTE": ("linea-de-tendencia", "linea-de-seguridad", "rebote"),
        "RUPTURA": ("linea-de-tendencia", "ruptura-por-cierre", "linea-de-seguridad"),
        "PRUEBA": ("linea-de-tendencia", "ruptura-por-cierre"),
        "RANGO": ("rango", "falso-quiebre"),
    }[estado]


def salida(estado: str, direccion: str, marco: str, invalidacion: Referencia | None, digits: int,
           seguimiento: Linea | None = None, objetivo: Referencia | None = None) -> str:
    """La regla de salida de Tori (doctrina 2.8): vela que cierra contra la línea de control.

    Nombra la operación y el sentido ("En compras, sal si cierra bajo"), porque "al otro lado"
    obligaba al cliente a deducir de qué lado estaba el riesgo. La falta de objetivo fijo se dice
    en positivo: se sale por la vela y no por un precio, así que la ganancia corre mientras la
    línea aguante. PRUEBA no lleva texto propio: se lee con la dirección de la lectura.
    """
    if estado == "RANGO" or direccion not in ("ALCISTA", "BAJISTA"):
        return ("En rango se opera el falso quiebre hacia el borde opuesto: sal si "
                f"{VELA.get(marco, marco)} vuelve a cerrar fuera del rango, porque ahí el quiebre "
                "no era falso.")
    if invalidacion is None:
        return ("Todavía no hay línea de control trazada, así que no hay salida que medir: "
                "conviene esperar a que se trace antes de entrar.")
    sube = direccion == "ALCISTA"
    operacion = "compras" if sube else "ventas"
    contra = "bajo" if sube else "sobre"
    por = " por ruptura" if estado == "RUPTURA" else ""
    texto = (f"En {operacion}{por}, sal si {VELA.get(marco, marco)} cierra {contra} la línea de "
             f"control (la que vigila tu operación), hoy en {_p(invalidacion.precio, digits)}. ")
    if objetivo is not None:
        texto += (f"Mientras no pase, mantén la posición; el objetivo en {_p(objetivo.precio, digits)} "
                  "es una referencia, no una orden de salida.")
    else:
        texto += "Mientras no pase, mantén la posición y deja correr la ganancia."
    if seguimiento is not None:
        texto += (f" Como el precio aceleró, también puedes asegurar ganancia si esa vela cierra "
                  f"{contra} la línea de seguimiento, hoy en {_p(seguimiento.valor_actual, digits)}.")
    return texto


def escenarios(estado: str, direccion: str, marco: str, digits: int, precio: float,
               vigilar: Referencia, invalidacion: Referencia | None,
               objetivo: Referencia | None, prueba: Prueba | None,
               rango: list[Linea]) -> tuple[Escenario, Escenario, Escenario]:
    vela = VELA.get(marco, marco)
    if prueba is not None:
        return _en_prueba(prueba, precio, marco, digits)
    if estado == "RANGO":
        techo = max(x.valor_actual for x in rango)
        piso = min(x.valor_actual for x in rango)
        t, b = _p(techo, digits), _p(piso, digits)
        return (Escenario("⬆️", f"Cierre sobre {t}", f"Si {vela} cierra sobre {t}, el precio sale del rango hacia arriba."),
                Escenario("↔️", f"Entre {b} y {t}", "Si rompe un borde y vuelve a entrar, es falso quiebre y el objetivo pasa a ser el borde contrario."),
                Escenario("⬇️", f"Cierre bajo {b}", f"Si {vela} cierra bajo {b}, el precio sale del rango hacia abajo."))
    sube = direccion == "ALCISTA"
    a_favor, en_contra = ("sobre", "bajo") if sube else ("bajo", "sobre")
    x = _p(vigilar.precio, digits)
    z = f" con objetivo en {_p(objetivo.precio, digits)}" if objetivo else ""
    if estado == "RUPTURA":
        cruzada = rota(vigilar.linea, sube)
        primero = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {x}",
                            f"{LA_VELA.get(marco, marco).capitalize()} ya cerró {a_favor} {cruzada}: mientras siga {a_favor} {x}, la ruptura sigue vigente{z}.")
        medio = Escenario("↔️", f"Vuelta a {x}",
                          f"Si el precio vuelve a {x} y la respeta, es un retesteo y la ruptura se confirma.")
        if invalidacion is not None:
            y = _p(invalidacion.precio, digits)
            ultimo = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {y}",
                               f"Si {vela} cierra {en_contra} {y}, la línea de control se rompe y la lectura deja de valer.")
        else:
            ultimo = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {x}",
                               f"Si {vela} vuelve a cerrar {en_contra} {x}, la ruptura fue falsa.")
        return (primero, medio, ultimo) if sube else (ultimo, medio, primero)
    # TENDENCIA y REBOTE
    tendencia = "alcista" if sube else "bajista"
    y = _p(invalidacion.precio, digits)
    rompe = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {y}",
                      f"Si {vela} cierra {en_contra} {y}, la línea {tendencia} se rompe y la tendencia deja de valer.")
    if estado == "REBOTE":
        # Es un hecho de la vela que cerró (doctrina 2.5, V7): se cuenta en pasado.
        sigue = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {y}",
                          f"{LA_VELA.get(marco, marco).capitalize()} tocó la línea {tendencia} y cerró {a_favor} {y}: "
                          f"rebotó, y mientras el precio cierre {a_favor} {y}, la tendencia sigue{z}.")
        medio = Escenario("↔️", f"Vuelta a {y}",
                          f"Si el precio vuelve a {y}, la línea se pone a prueba otra vez: otro cierre {a_favor} confirma el rebote.")
        return (sigue, medio, rompe) if sube else (rompe, medio, sigue)
    if vigilar.linea is not None and vigilar.linea.rol == "accion":
        contraria = "bajista" if sube else "alcista"
        sigue = Escenario("⬆️" if sube else "⬇️", f"Cierre {a_favor} {x}",
                          f"Si {vela} cierra {a_favor} {x}, se rompe la línea {contraria} del retroceso y la tendencia retoma{z}.")
        medio = Escenario("↔️", f"Entre {y} y {x}" if sube else f"Entre {x} y {y}",
                          f"Mientras el precio siga entre las dos líneas, la tendencia {tendencia} sigue en pie, pero todavía no hay ruptura que operar.")
    else:
        sigue = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {y}",
                          f"Mientras el precio cierre {a_favor} {y}, la tendencia {tendencia} sigue{z}.")
        medio = Escenario("↔️", f"Vuelta a {y}",
                          f"Si el precio vuelve a {y} y la respeta, la línea suma un toque y gana fuerza.")
    return (sigue, medio, rompe) if sube else (rompe, medio, sigue)


def _en_prueba(prueba: Prueba, precio: float, marco: str, digits: int) -> tuple[Escenario, Escenario, Escenario]:
    """Siempre como condición, nunca como hecho (spec §4, "Cómo se comunica")."""
    x = _p(prueba.valor_ahora, digits)
    hora = prueba.cierre_vela.strftime("%H:%M")
    la_vela = LA_VELA.get(marco, marco)
    abajo = precio < prueba.valor_ahora
    rompe = Escenario("⬇️" if abajo else "⬆️", f"Cierre {'bajo' if abajo else 'sobre'} {x} a las {hora}",
                      f"Si {la_vela} cierra {'bajo' if abajo else 'sobre'} {x} a las {hora}, la línea se considera rota y la lectura pasa a {'bajista' if abajo else 'alcista'}.")
    espera = Escenario("↔️", f"Hasta las {hora}",
                       f"Con la línea en {x}, hasta el cierre de las {hora} (hora de Chile) es una prueba, no una ruptura: la vela todavía puede volver.")
    vuelve = Escenario("⬆️" if abajo else "⬇️", f"Cierre {'sobre' if abajo else 'bajo'} {x}",
                       f"Si vuelve a cerrar {'sobre' if abajo else 'bajo'} {x}, fue solo una mecha y la lectura no cambia.")
    return (vuelve, espera, rompe) if abajo else (rompe, espera, vuelve)
