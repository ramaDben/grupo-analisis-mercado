"""Postura conjunta entre la referencia semanal y el plan intradía de hoy.

Capa de narrativa pura (sin MT5, sin disco): recibe dos Lectura (contrato)
y decide el caso y los textos.
Spec encargo C.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from analista.seguimiento import texto_lectura
from estrategia.contrato import Lectura
import pipeline_carrusel as pc

CasoPostura = Literal["coinciden", "contra", "semana_cambio", "sin_plan_hoy"]


@dataclass(frozen=True)
class Postura:
    caso: CasoPostura
    marco_semana: str
    plan_hoy: str
    puente: str
    calidad_hoy: str


def _fmt(valor: float, digits: int) -> str:
    return pc.formatear_precio(valor, digits)


def _limpiar_texto(texto: str) -> str:
    """Sustituye términos o puntuación contrarios a las reglas de cliente."""
    return (
        texto.replace("—", ", ")
        .replace("–", ", ")
        .replace("techo", "resistencia")
        .replace("Techo", "Resistencia")
        .replace("suelo", "soporte")
        .replace("Suelo", "Soporte")
        .replace("stop", "línea de control")
        .replace("Stop", "Línea de control")
        .replace("entrada", "nivel a vigilar")
        .replace("Entrada", "Nivel a vigilar")
        .replace("oportunidad", "lectura")
        .replace("Oportunidad", "Lectura")
        .replace("señal", "lectura")
        .replace("Señal", "Lectura")
    )


def _extraer_calidad_hoy(hoy: Lectura | None) -> str:
    """Obtiene la calidad ('A+', 'B' o '') de la línea operativa de hoy."""
    if hoy is None:
        return ""
    for ref in (hoy.vigilar, hoy.invalidacion):
        if ref is not None and ref.linea is not None and ref.linea.calidad in ("A+", "B"):
            return ref.linea.calidad
    for linea in hoy.lineas:
        if linea.rol in ("seguridad", "accion", "seguimiento") and linea.calidad in ("A+", "B"):
            return linea.calidad
    for linea in hoy.lineas:
        if linea.calidad in ("A+", "B"):
            return linea.calidad
    return ""


def _determinar_caso(
    semanal: Lectura, hoy: Lectura | None, reemplazada: bool
) -> CasoPostura:
    if reemplazada:
        return "semana_cambio"
    if hoy is None:
        return "sin_plan_hoy"
    if hoy.estado == "RANGO":
        rango_lines = [x for x in hoy.lineas if x.rol == "rango"]
        if len(rango_lines) < 2:
            return "sin_plan_hoy"
    if hoy.direccion == "LATERAL" or semanal.direccion == "LATERAL":
        return "sin_plan_hoy"
    if hoy.direccion == semanal.direccion and hoy.direccion in ("ALCISTA", "BAJISTA"):
        return "coinciden"
    if (semanal.direccion == "ALCISTA" and hoy.direccion == "BAJISTA") or (
        semanal.direccion == "BAJISTA" and hoy.direccion == "ALCISTA"
    ):
        return "contra"
    return "sin_plan_hoy"


def postura_conjunta(
    semanal: Lectura,
    hoy: Lectura | None,
    digits: int,
    reemplazada: bool = False,
) -> Postura:
    """Evalúa la postura conjunta semanal e intradía y redacta su narrativa.

    Recibe dos Lectura y devuelve una Postura con caso, textos y calidad.
    """
    caso = _determinar_caso(semanal, hoy, reemplazada)
    calidad_hoy = _extraer_calidad_hoy(hoy)

    if caso == "coinciden":
        assert hoy is not None
        marco_semana = _limpiar_texto(texto_lectura(semanal, False, digits))
        puente = "Para hoy, el día confirma la semana:"
        flecha = "⬆️" if hoy.direccion == "ALCISTA" else "⬇️"
        etiqueta_vigilar = _limpiar_texto(hoy.vigilar.etiqueta)

        if hoy.estado == "PRUEBA" and hoy.en_prueba is not None:
            plan_hoy = (
                f"El plan de hoy confirma la dirección de la semana {flecha}, "
                f"probando {etiqueta_vigilar} en {_fmt(hoy.en_prueba.valor_ahora, digits)} "
                f"al cierre de la vela de las {hoy.en_prueba.cierre_vela:%H:%M}."
            )
        elif hoy.objetivo is not None and hoy.invalidacion is not None:
            plan_hoy = (
                f"El plan de hoy acompaña la dirección de la semana {flecha} "
                f"con objetivo en {_fmt(hoy.objetivo.precio, digits)} "
                f"y línea de control en {_fmt(hoy.invalidacion.precio, digits)}."
            )
        elif hoy.objetivo is not None:
            plan_hoy = (
                f"El plan de hoy acompaña la dirección de la semana {flecha} "
                f"vigilando {etiqueta_vigilar} en {_fmt(hoy.vigilar.precio, digits)}, "
                f"con objetivo en {_fmt(hoy.objetivo.precio, digits)}."
            )
        else:
            plan_hoy = (
                f"El plan de hoy acompaña la dirección de la semana {flecha} "
                f"vigilando {etiqueta_vigilar} en {_fmt(hoy.vigilar.precio, digits)}."
            )

    elif caso == "contra":
        assert hoy is not None
        texto_base = _limpiar_texto(texto_lectura(semanal, False, digits))
        marco_semana = (
            f"{texto_base} La lectura de la semana sigue vigente mientras no se rompa su línea."
        )
        puente = "Para hoy hay un movimiento más corto (8 a 10 horas) en sentido contrario:"
        flecha = "⬆️" if hoy.direccion == "ALCISTA" else "⬇️"

        if hoy.invalidacion is not None:
            control_str = _fmt(hoy.invalidacion.precio, digits)
        else:
            control_str = _fmt(hoy.vigilar.precio, digits)

        if hoy.objetivo is not None:
            plan_hoy = (
                f"El plan de hoy busca un movimiento {hoy.direccion.lower()} {flecha} "
                f"hacia el objetivo en {_fmt(hoy.objetivo.precio, digits)} "
                f"con línea de control en {control_str}. "
                "Si pierde la línea de control de hoy, se retoma el marco de la semana."
            )
        else:
            etiqueta_vigilar = _limpiar_texto(hoy.vigilar.etiqueta)
            plan_hoy = (
                f"El plan de hoy busca un movimiento {hoy.direccion.lower()} {flecha} "
                f"vigilando {etiqueta_vigilar} en {_fmt(hoy.vigilar.precio, digits)} "
                f"con línea de control en {control_str}. "
                "Si pierde la línea de control de hoy, se retoma el marco de la semana."
            )

    elif caso == "semana_cambio":
        etiqueta_vig = _limpiar_texto(semanal.vigilar.etiqueta)
        marco_semana = (
            "La referencia semanal fue reemplazada por ruptura o cambio de estructura: "
            f"la lectura de la semana cambió y ahora se vigila {etiqueta_vig} "
            f"en {_fmt(semanal.vigilar.precio, digits)}."
        )
        puente = "El plan de hoy se lee desde este cambio de estructura:"

        if hoy is None:
            plan_hoy = (
                "Por ahora no hay un plan intradía propio; "
                "la lectura se sigue directamente desde la nueva referencia semanal."
            )
        else:
            flecha = (
                "⬆️"
                if hoy.direccion == "ALCISTA"
                else "⬇️"
                if hoy.direccion == "BAJISTA"
                else "↔️"
            )
            etiqueta_hoy = _limpiar_texto(hoy.vigilar.etiqueta)
            if hoy.objetivo is not None:
                plan_hoy = (
                    f"El plan de hoy se alinea con la nueva referencia {flecha} "
                    f"vigilando {etiqueta_hoy} en {_fmt(hoy.vigilar.precio, digits)}, "
                    f"con objetivo en {_fmt(hoy.objetivo.precio, digits)}."
                )
            else:
                plan_hoy = (
                    f"El plan de hoy se alinea con la nueva referencia {flecha} "
                    f"vigilando {etiqueta_hoy} en {_fmt(hoy.vigilar.precio, digits)}."
                )

    else:  # sin_plan_hoy
        marco_semana = _limpiar_texto(texto_lectura(semanal, False, digits))
        puente = "Para hoy manda la semana y no hay un plan propio:"

        if hoy is None:
            plan_hoy = (
                "Hoy no tenemos un plan intradía propio; "
                "manda el marco de la semana mientras el precio no marque una nueva estructura."
            )
        elif hoy.estado == "RANGO":
            plan_hoy = (
                "Hoy el precio está en rango sin un borde claro para definir un plan propio; "
                "manda la lectura de la semana."
            )
        elif hoy.direccion == "LATERAL":
            plan_hoy = (
                "Hoy el precio se mueve lateral sin una tendencia clara para estructurar un plan propio; "
                "manda la lectura de la semana."
            )
        else:
            plan_hoy = (
                "Hoy no tenemos un plan intradía propio; "
                "manda el marco de la semana mientras el activo define su movimiento."
            )

    return Postura(
        caso=caso,
        marco_semana=marco_semana,
        plan_hoy=plan_hoy,
        puente=puente,
        calidad_hoy=calidad_hoy,
    )
