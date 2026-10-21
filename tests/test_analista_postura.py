"""Tests de postura conjunta (semana + hoy) y sus textos narrativos.

Capa de narrativa pura: recibe dos Lectura (contrato) y decide el caso y los textos.
Spec encargo C.
"""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import postura as pos  # noqa: E402

PROHIBIDAS = ("stop", "entrada", "oportunidad", "señal", "senal", "techo", "suelo")
GUIONES_PROHIBIDOS = ("—", "–")


def test_caso_coinciden_alcista():
    semanal = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)
    hoy = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4020.0, invalidacion=3980.0, objetivo=4100.0, calidad_prueba="A+")

    p = pos.postura_conjunta(semanal, hoy, digits=2)

    assert p.caso == "coinciden"
    assert p.calidad_hoy == "A+"
    assert "confirma la semana" in p.puente.lower()
    assert "4.000,00" in p.marco_semana or "3.950,00" in p.marco_semana
    assert "4.100,00" in p.plan_hoy or "3.980,00" in p.plan_hoy
    assert "⬆️" in p.plan_hoy or "⬆️" in p.puente


def test_caso_coinciden_bajista():
    semanal = fx.lectura(direccion="BAJISTA", estado="TENDENCIA", precio=2000.0, invalidacion=2050.0, objetivo=1900.0)
    hoy = fx.lectura(direccion="BAJISTA", estado="TENDENCIA", precio=1990.0, invalidacion=2020.0, objetivo=1930.0, calidad_prueba="B")

    p = pos.postura_conjunta(semanal, hoy, digits=2)

    assert p.caso == "coinciden"
    assert p.calidad_hoy == "B"
    assert "confirma la semana" in p.puente.lower()
    assert "⬇️" in p.plan_hoy or "⬇️" in p.puente


def test_caso_contra_alcista_vs_bajista():
    semanal = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)
    hoy = fx.lectura(direccion="BAJISTA", estado="REBOTE", precio=4020.0, invalidacion=4050.0, objetivo=3980.0, calidad_prueba="A+")

    p = pos.postura_conjunta(semanal, hoy, digits=2)

    assert p.caso == "contra"
    assert p.calidad_hoy == "A+"
    assert "8 a 10 horas" in p.puente.lower() or "8 a 10 horas" in p.plan_hoy.lower()
    assert "sentido contrario" in p.puente.lower() or "sentido contrario" in p.plan_hoy.lower()
    assert "vigente mientras no se rompa su línea" in p.marco_semana.lower() or "sigue vigente mientras" in p.marco_semana.lower()
    assert "retoma el marco de la semana" in p.plan_hoy.lower()
    assert "línea de control" in p.plan_hoy.lower()


def test_caso_contra_bajista_vs_alcista():
    semanal = fx.lectura(direccion="BAJISTA", estado="TENDENCIA", precio=2000.0, invalidacion=2050.0, objetivo=1900.0)
    hoy = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=1980.0, invalidacion=1950.0, objetivo=2010.0, calidad_prueba="B")

    p = pos.postura_conjunta(semanal, hoy, digits=2)

    assert p.caso == "contra"
    assert p.calidad_hoy == "B"
    assert "retoma el marco de la semana" in p.plan_hoy.lower()


def test_caso_semana_cambio():
    semanal = fx.lectura(direccion="BAJISTA", estado="RUPTURA", precio=4000.0, invalidacion=4050.0, objetivo=3900.0)
    hoy = fx.lectura(direccion="BAJISTA", estado="TENDENCIA", precio=3990.0, invalidacion=4030.0, objetivo=3920.0, calidad_prueba="A+")

    p = pos.postura_conjunta(semanal, hoy, digits=2, reemplazada=True)

    assert p.caso == "semana_cambio"
    assert "reemplazada" in p.marco_semana.lower() or "cambió" in p.marco_semana.lower()
    assert "nueva referencia" in p.plan_hoy.lower() or "nueva estructura" in p.plan_hoy.lower() or "cambio" in p.puente.lower()


def test_caso_semana_cambio_sin_hoy():
    semanal = fx.lectura(direccion="BAJISTA", estado="RUPTURA", precio=4000.0, invalidacion=4050.0, objetivo=3900.0)

    p = pos.postura_conjunta(semanal, None, digits=2, reemplazada=True)

    assert p.caso == "semana_cambio"
    assert p.calidad_hoy == ""
    assert "reemplazada" in p.marco_semana.lower() or "cambió" in p.marco_semana.lower()


def test_caso_sin_plan_hoy_none():
    semanal = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)

    p = pos.postura_conjunta(semanal, None, digits=2)

    assert p.caso == "sin_plan_hoy"
    assert p.calidad_hoy == ""
    assert "manda" in p.puente.lower() or "manda" in p.plan_hoy.lower()
    assert "no hay plan propio" in p.plan_hoy.lower() or "no tenemos un plan" in p.plan_hoy.lower() or "sin un plan" in p.plan_hoy.lower()


def test_caso_sin_plan_hoy_rango_sin_borde_claro():
    semanal = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)
    # Rango sin 2 líneas de rango
    hoy_rango = replace(fx.lectura(estado="RANGO", rango=(4050.0, 3950.0)), lineas=())

    p = pos.postura_conjunta(semanal, hoy_rango, digits=2)

    assert p.caso == "sin_plan_hoy"
    assert "manda" in p.puente.lower() or "manda" in p.plan_hoy.lower()


def test_caso_sin_plan_hoy_direccion_lateral():
    semanal = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)
    hoy_lat = replace(fx.lectura(direccion="LATERAL", estado="TENDENCIA"), direccion="LATERAL")

    p = pos.postura_conjunta(semanal, hoy_lat, digits=2)

    assert p.caso == "sin_plan_hoy"


def test_contrato_todos_los_textos_limpios_de_palabras_y_guiones_prohibidos():
    """Recorre todos los textos que el módulo puede emitir en los cuatro casos por direcciones."""
    alc = fx.lectura(direccion="ALCISTA", estado="TENDENCIA", precio=4000.0, invalidacion=3950.0, objetivo=4150.0)
    baj = fx.lectura(direccion="BAJISTA", estado="TENDENCIA", precio=4000.0, invalidacion=4050.0, objetivo=3850.0)
    rango_sin_borde = replace(fx.lectura(estado="RANGO", rango=(4050.0, 3950.0)), lineas=())
    rango_con_borde = fx.lectura(estado="RANGO", rango=(4050.0, 3950.0))

    combinaciones = [
        # coinciden
        (alc, alc, False),
        (baj, baj, False),
        # contra
        (alc, baj, False),
        (baj, alc, False),
        # semana_cambio
        (alc, alc, True),
        (alc, baj, True),
        (baj, alc, True),
        (baj, baj, True),
        (alc, None, True),
        (baj, None, True),
        # sin_plan_hoy
        (alc, None, False),
        (baj, None, False),
        (alc, rango_sin_borde, False),
        (baj, rango_sin_borde, False),
        (alc, rango_con_borde, False),
    ]

    for sem, hoy, reemplazada in combinaciones:
        postura = pos.postura_conjunta(sem, hoy, digits=2, reemplazada=reemplazada)
        textos = [postura.marco_semana, postura.puente, postura.plan_hoy]

        for texto in textos:
            for g in GUIONES_PROHIBIDOS:
                assert g not in texto, f"Guion prohibido '{g}' en texto: {texto!r}"

            texto_bajo = texto.lower()
            for palabra in PROHIBIDAS:
                assert palabra not in texto_bajo, f"Palabra prohibida '{palabra}' en texto: {texto!r}"


def test_ningun_precio_escrito_a_mano_en_codigo_fuente():
    """Verifica que scripts/analista/postura.py no contenga precios hardcodeados."""
    ruta_postura = RAIZ / "scripts" / "analista" / "postura.py"
    contenido = ruta_postura.read_text(encoding="utf-8")
    arbol = ast.parse(contenido, filename=str(ruta_postura))

    for nodo in ast.walk(arbol):
        # Constantes numéricas
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
            val = nodo.value
            # Prohibido cualquier float en el código fuente de postura (todos los precios son floats de las lecturas)
            assert not isinstance(val, float), f"Float hardcodeado encontrado en postura.py: {val}"
            # Los enteros solo pueden ser estructurales pequeños (ej: 0, 1, 2 para índices/longitudes, 8, 10 para horas)
            assert val <= 24, f"Entero sospechoso de precio hardcodeado en postura.py: {val}"
