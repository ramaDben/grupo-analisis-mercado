"""Estrategia de juguete: solo horizontales. Prueba que el contrato no tiene la forma de Tori.

Vive en tests/ y no se registra en producción (spec §4).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from dataclasses import replace  # noqa: E402

from estrategia.contrato import (  # noqa: E402
    Escenario, Etiqueta, Fundamento, Lectura, Linea, Marcos, Procedencia, Prueba, Puntaje,
    Referencia, exigir_velas,
)


class Juguete:
    nombre = "juguete"
    marcos = Marcos((), "H4", {"H4": 40}, {"H4": Etiqueta("swing", "de una a dos semanas")})
    procedencia = Procedencia(
        "docs/metodologia-tendencias.md", "docs/investigacion/fundamentos/fuentes.md",
        (Fundamento("en lateral no se opera", ("estrategia de juguete de los tests",),
                    ("F3 p. 78",), (), "es un juguete: no mide nada"),),
        ("cualquier tendencia: solo mira el rango",),
    )

    def leer(self, ticker, velas, digits, en_curso=None):
        exigir_velas(velas, self.marcos)
        df = velas["H4"].tail(20)
        alto, bajo = round(float(df["high"].max()), digits), round(float(df["low"].min()), digits)
        t0 = int(df["time"].iloc[0])
        techo = Linea("rango", "horizontal", ((t0, alto),), "H4", 1, "", alto)
        piso = Linea("rango", "horizontal", ((t0, bajo),), "H4", 1, "", bajo)
        cierre = float(df["close"].iloc[-1])
        medio = (alto + bajo) / 2
        direccion = "ALCISTA" if cierre > medio else "BAJISTA" if cierre < medio else "LATERAL"
        estado, prueba = "RANGO", None
        if en_curso is not None and not bajo <= en_curso.precio <= alto:
            linea = techo if en_curso.precio > alto else piso
            estado, prueba = "PRUEBA", Prueba(linea, linea.valor_actual, en_curso.cierre)
        return Lectura(
            ticker=ticker, marco="H4", precio=en_curso.precio if en_curso else cierre,
            direccion=direccion, estado=estado, lineas=(techo, piso), en_prueba=prueba,
            vigilar=Referencia(alto, "techo del rango", techo), invalidacion=None, objetivo=None,
            escenarios=(Escenario("⬆️", f"Sobre {alto}", "sale por arriba"),
                        Escenario("↔️", "Dentro", "espera"),
                        Escenario("⬇️", f"Bajo {bajo}", "sale por abajo")),
            salida="dentro del rango no hay posición", conceptos=("rango",), avisos=(),
            vela=int(df["time"].iloc[-1]),
        )

    def seguir(self, referencia, velas, digits, en_curso=None):
        """Mide las velas de hoy contra el techo y el piso de la referencia, sin recalcularlos."""
        exigir_velas(velas, self.marcos)
        if referencia.estado == "PRUEBA":
            raise ValueError("una referencia no puede quedar en PRUEBA")
        techo, piso = referencia.lineas
        df = velas["H4"]
        despues = df[df["time"] > referencia.vela]
        rompio = bool(((despues["close"] > techo.valor_actual)
                       | (despues["close"] < piso.valor_actual)).any())
        cierre = float(df["close"].iloc[-1])
        estado, prueba = ("RUPTURA" if rompio else referencia.estado), None
        if en_curso is not None and not rompio and \
                not piso.valor_actual <= en_curso.precio <= techo.valor_actual:
            linea = techo if en_curso.precio > techo.valor_actual else piso
            estado, prueba = "PRUEBA", Prueba(linea, linea.valor_actual, en_curso.cierre)
        return replace(referencia, estado=estado, en_prueba=prueba,
                       precio=en_curso.precio if en_curso else cierre,
                       vela=int(df["time"].iloc[-1]))

    def puntuar(self, lectura, horizonte):
        return Puntaje(50.0, {"base": 50.0}, None)

    def divergencia(self, preparada, actual):
        return None if preparada.direccion == actual.direccion else "cambió la dirección"


class ConMemoria(Juguete):
    """Tramposa: devuelve la primera lectura de cada activo. La batería tiene que pillarla."""

    def __init__(self):
        self._vistas = {}

    def leer(self, ticker, velas, digits, en_curso=None):
        return self._vistas.setdefault(ticker, super().leer(ticker, velas, digits, en_curso))


def crear() -> Juguete:
    return Juguete()


def crear_con_memoria() -> ConMemoria:
    return ConMemoria()
