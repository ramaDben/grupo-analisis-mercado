"""Batería de conformidad del enchufe (spec §4 y §8).

Toda estrategia que se enchufe pasa estas verificaciones. Reciben una FÁBRICA y
no una instancia, porque la de "sin mirar el futuro" necesita instancias nuevas
para detectar una estrategia que guarda memoria entre lecturas.
"""
from __future__ import annotations

import random
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import FLECHAS, Estrategia, Puntaje, VelaEnCurso  # noqa: E402
from estrategia.procedencia import validar  # noqa: E402

Fabrica = Callable[[], Estrategia]
PASO = {"H1": 3600, "H4": 4 * 3600, "D1": 86400, "W1": 7 * 86400}
T0 = 1_735_689_600  # 2025-01-01 00:00 UTC; las velas son sintéticas
CORTES = (0, 5, 17, 33)
SCL = ZoneInfo("America/Santiago")
TICKER = "SINTETICO"


def serie(n: int, paso: int, semilla: int) -> pd.DataFrame:
    """Caminata con tramos de tendencia: tiene líneas que trazar y rangos."""
    rng = random.Random(semilla)
    precio, tendencia, filas = 100.0, 0.0, []
    for i in range(n):
        if i % 40 == 0:
            tendencia = rng.uniform(-0.6, 0.6)
        apertura = precio
        cierre = max(1.0, apertura + tendencia + rng.gauss(0, 0.8))
        filas.append({
            "time": T0 + i * paso, "open": apertura, "close": cierre,
            "high": max(apertura, cierre) + abs(rng.gauss(0, 0.4)),
            "low": min(apertura, cierre) - abs(rng.gauss(0, 0.4)),
        })
        precio = cierre
    return pd.DataFrame(filas)


def velas_de(estrategia: Estrategia, semilla: int = 11, extra: int = 40) -> dict[str, pd.DataFrame]:
    m = estrategia.marcos
    return {marco: serie(m.velas[marco] + extra, PASO[marco], semilla + k)
            for k, marco in enumerate(m.todos)}


def recortar(velas: dict[str, pd.DataFrame], k: int) -> dict[str, pd.DataFrame]:
    return {m: df.iloc[: len(df) - k].reset_index(drop=True) for m, df in velas.items()}


def verificar_sin_futuro(fabrica: Fabrica) -> None:
    """La lectura del instante t es la misma aunque la estrategia haya visto después."""
    velas = velas_de(fabrica())
    for k in CORTES:
        recorte = recortar(velas, k)
        limpia = fabrica().leer(TICKER, recorte, 2)
        usada = fabrica()
        usada.leer(TICKER, velas, 2)
        assert usada.leer(TICKER, recorte, 2) == limpia, (
            f"recortando {k} velas, la lectura cambia si la estrategia ya vio el futuro"
        )
        for linea in limpia.lineas:
            ultima = int(recorte[linea.marco]["time"].iloc[-1])
            assert all(t <= ultima for t, _ in linea.puntos), (
                f"una línea {linea.rol} de {linea.marco} se ancla después de la última vela cerrada"
            )


def verificar_escenarios(fabrica: Fabrica) -> None:
    e = fabrica()
    velas = velas_de(e)
    for k in CORTES:
        flechas = [x.flecha for x in e.leer(TICKER, recortar(velas, k), 2).escenarios]
        assert sorted(flechas) == sorted(FLECHAS), f"escenarios {flechas} con {k} velas recortadas"


def verificar_prueba_solo_con_vela_en_curso(fabrica: Fabrica) -> None:
    e = fabrica()
    op = e.marcos.operativo
    velas = velas_de(e)
    hubo_prueba = False
    for k in CORTES:
        recorte = recortar(velas, k)
        sin = e.leer(TICKER, recorte, 2)
        assert sin.estado != "PRUEBA" and sin.en_prueba is None, "PRUEBA sin vela en curso"
        df = recorte[op]
        apertura = int(df["time"].iloc[-1]) + PASO[op]
        cierre = datetime.fromtimestamp(apertura + PASO[op], tz=SCL)
        for precio in (float(df["high"].max()) * 1.5, float(df["low"].min()) * 0.5):
            con = e.leer(TICKER, recorte, 2, VelaEnCurso(apertura, precio, cierre))
            estructurales = lambda l: [x for x in l.lineas if x.rol != "objetivo"]  # noqa: E731
            assert estructurales(con) == estructurales(sin), "la vela abierta movió una línea"
            assert con.direccion == sin.direccion, "la vela abierta cambió la dirección"
            if con.estado == "PRUEBA":
                hubo_prueba = True
                assert con.en_prueba.cierre_vela == cierre
    assert hubo_prueba, (
        "con la vela abierta fuera de todo el rango la estrategia nunca entró en PRUEBA: "
        "no se verificó nada de la rama PRUEBA"
    )


def verificar_procedencia(fabrica: Fabrica) -> None:
    errores = validar(fabrica().procedencia)
    assert errores == [], "procedencia incompleta:\n" + "\n".join(errores)


def verificar_marco_y_puntaje(fabrica: Fabrica) -> None:
    e = fabrica()
    lectura = e.leer(TICKER, velas_de(e), 2)
    assert lectura.marco == e.marcos.operativo
    for horizonte in ("sesion", "semana"):
        assert isinstance(e.puntuar(lectura, horizonte), Puntaje)


def verificar_divergencia_propia(fabrica: Fabrica) -> None:
    e = fabrica()
    velas = velas_de(e)
    lectura = e.leer(TICKER, velas, 2)
    assert e.divergencia(lectura, lectura) is None, "una lectura diverge de sí misma"
    opuesta = {"ALCISTA": "BAJISTA", "BAJISTA": "ALCISTA"}
    for k in CORTES:
        base = e.leer(TICKER, recortar(velas, k), 2)
        if base.direccion in opuesta:
            motivo = e.divergencia(base, replace(base, direccion=opuesta[base.direccion]))
            assert isinstance(motivo, str) and motivo, (
                "divergencia() no detecta una lectura de dirección opuesta"
            )
            return
    raise AssertionError("ningún corte dio una lectura no lateral: no se pudo probar divergencia()")


def verificar_seguir_misma_lectura(fabrica: Fabrica) -> None:
    """Con las mismas velas, seguir() no cambia la lectura ni mueve un ancla."""
    e = fabrica()
    velas = velas_de(e)
    ref = e.leer(TICKER, velas, 2)
    misma = e.seguir(ref, velas, 2)
    assert (misma.estado, misma.direccion) == (ref.estado, ref.direccion), (
        "seguir() con las mismas velas cambia la lectura"
    )
    assert [(x.rol, x.puntos) for x in misma.lineas] == [(x.rol, x.puntos) for x in ref.lineas], (
        "seguir() movió un ancla"
    )
    assert misma.vela == ref.vela


def verificar_seguir_sin_futuro(fabrica: Fabrica) -> None:
    """seguir() cumple la misma regla que leer(): lo que vio después no cambia el pasado."""
    e = fabrica()
    op = e.marcos.operativo
    velas = velas_de(e)
    ref = e.leer(TICKER, recortar(velas, 33), 2)
    for k in (0, 5, 17):
        recorte = recortar(velas, k)
        limpia = fabrica().seguir(ref, recorte, 2)
        usada = fabrica()
        usada.seguir(ref, velas, 2)
        assert usada.seguir(ref, recorte, 2) == limpia, (
            f"recortando {k} velas, seguir() cambia si la estrategia ya vio el futuro"
        )
        assert limpia.vela == int(recorte[op]["time"].iloc[-1])


def verificar_seguir_anclas_fijas(fabrica: Fabrica) -> None:
    """Con velas nuevas, las anclas siguen siendo las del lunes (OjZ8d [01:07])."""
    e = fabrica()
    velas = velas_de(e)
    ref = e.leer(TICKER, recortar(velas, 33), 2)
    assert e.leer(TICKER, velas, 2).lineas != ref.lineas, (
        "precondición: con velas nuevas, leer() tendría que trazar anclas distintas; sin eso la prueba no mide nada"
    )
    hoy = e.seguir(ref, velas, 2)
    assert sorted(x.puntos for x in hoy.lineas) == sorted(x.puntos for x in ref.lineas), (
        "seguir() volvió a trazar: las anclas no son las de la referencia"
    )
