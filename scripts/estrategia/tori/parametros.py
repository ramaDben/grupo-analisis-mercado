"""Umbrales que Tori no da en números. Todos son NUESTROS (doctrina §2, §4).

Quedan declarados en la procedencia como `no_probado`: no habrá backtesting que
los mida. Los valores son provisionales y se revisan en el gate del director con
la medición del universo real (scripts/tori_revision.py).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametros:
    zigzag_atr: float = 2.0  # pivote candidato al segundo punto: giro de 2 ATR del marco
    tolerancia_toque_atr: float = 0.25  # la línea se traza "a ojo, con grosor" (Kffx9 [14:40])
    separacion_toque_atr: float = 1.0  # entre toques el precio "se aleja con claridad" (OjZ8d [06:13])
    pendiente_min_atr: float = 0.02  # bajo esto la línea es horizontal (OjZ8d [03:52])
    pendiente_empinada_atr: float = 0.5  # "muy empinada" (Murphy p. 103)
    velas_punto_b_reciente: int = 6  # V16: Punto B dentro del último día de 4H
    velas_ab_min: int | None = None  # None: regla semanal; int: velas mínimas entre ancla y punto B (A+)
    zigzag_horizontal_atr: float = 1.5
    tolerancia_horizontal_atr: float = 0.5  # el horizontal es una zona (qsjLm [08:52])
    horizontal_max_atr: float = 8.0  # "solo los cercanos" (qsjLm [03:27])
    velas_rango: int = 30  # bordes del rango sin diagonales: una semana de 4H
    salto_max_rango: float = 8.0  # hueco entre velas que es un salto de datos (medido: COPPER 9,1 y 17,4; el resto <= 5,8)
    velas_ruptura_max: int = 30  # la ruptura caduca a la semana de 4H (gate del director, 2026-10-11)
    cerca_atr_d1: float = 1.0  # spec §5: "a menos de un ATR diario"
    lejos_atr_d1: float = 2.0  # precio lejos de la línea de control (doctrina 2.5)
    tope_adicionales: float = 24.0  # lo que suma dentro de una banda de situación
    # Puntaje (spec §5): piso de cada situación por horizonte, sobre 100.
    bandas_sesion: tuple[tuple[str, float], ...] = (
        ("ruptura", 75.0), ("a_punto", 50.0), ("tendencia", 25.0), ("rango", 0.0))
    bandas_semana: tuple[tuple[str, float], ...] = (
        ("a_punto", 75.0), ("ruptura", 50.0), ("tendencia", 25.0), ("rango", 0.0))
    toques_calidad: int = 4  # la línea principal suma calidad con 4 toques o más
    semanas_calidad: float = 3.0  # y otra vez si cubre 3 semanas o más
    espacio_factor: float = 2.0  # hay espacio si el objetivo está al doble de la seguridad o más
    peso_calidad: float = 5.0  # cada uno de los dos adicionales de calidad
    peso_confluencia_sesion: float = 5.0  # confluencia con los marcos mayores, para la sesión
    peso_confluencia_semana: float = 10.0  # y para la semana, donde el contexto pesa más
    peso_doble_confirmacion: float = 5.0  # un horizontal junto a la línea que se vigila
    peso_espacio: float = 5.0  # espacio hasta el objetivo
    resta_lejos: float = 30.0  # precio lejos de la seguridad: baja de banda (doctrina 2.5)

    def __post_init__(self) -> None:
        # La histéresis de toques supone que alejarse exige más que tocar.
        if self.separacion_toque_atr <= self.tolerancia_toque_atr:
            raise ValueError("separacion_toque_atr debe ser mayor que tolerancia_toque_atr")


PARAMETROS = Parametros()
