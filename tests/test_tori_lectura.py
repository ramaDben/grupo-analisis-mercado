"""Lectura de Tori sobre velas sintéticas (spec §5, doctrina §1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from datetime import datetime  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from estrategia.contrato import Etiqueta, Marcos, VelaEnCurso  # noqa: E402
from estrategia.tori import lectura as lt  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402

MARCOS = Marcos(("W1", "D1"), "H4", {"W1": 156, "D1": 250, "H4": 180},
                {"W1": Etiqueta("contexto", "de meses"), "D1": Etiqueta("posicional", "de semanas"),
                 "H4": Etiqueta("swing", "de una a dos semanas")})
ALCISTA = [100, 112, 106, 118, 112, 124, 119]
BAJISTA = [124, 112, 118, 106, 112, 100, 105]  # espejo de ALCISTA
BAJISTA_ROTA = [124, 112, 118, 106, 112, 100]
RANGO = [100, 110, 100, 110, 100, 110, 100, 105]
# Sigue a ALCISTA hasta 130 y vuelve a la línea alcista. La línea pasa por las mechas
# (99,8 + 0,25 por vela) y en la última vela (la 95) vale 123,55: esa vela baja a 123,65
# (mecha de 0,2) y cierra en 123,85, sobre la línea.
REBOTE = ALCISTA + [130, 123.85]


def velas(h4: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"H4": h4, "D1": vs.agregar(h4, 6), "W1": vs.agregar(h4, 30)}


def rota() -> pd.DataFrame:
    df = vs.desde_vertices(BAJISTA_ROTA, 12)
    subida = vs.desde_vertices([100, 118], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    return pd.concat([df, subida], ignore_index=True)


def leer(h4, en_curso=None):
    return lt.leer("XAUUSD", velas(h4), 2, en_curso, MARCOS, P)


def test_tendencia_alcista_con_la_linea_de_seguridad_a_mas():
    lec = leer(vs.desde_vertices([130, *ALCISTA], 12))
    assert (lec.estado, lec.direccion) == ("TENDENCIA", "ALCISTA")
    seguridad = next(x for x in lec.lineas if x.rol == "seguridad")
    assert seguridad.calidad == "A+" and seguridad.tipo == "diagonal"
    assert lec.invalidacion.linea == seguridad
    assert lec.precio > seguridad.valor_actual


def test_ruptura_por_cierre_de_la_bajista():
    lec = leer(rota())
    assert (lec.estado, lec.direccion) == ("RUPTURA", "ALCISTA")
    accion = next(x for x in lec.lineas if x.rol == "accion")
    assert lec.vigilar.linea == accion
    assert "velas_desde_ruptura" in lec.metricas
    assert any("seguridad" in a for a in lec.avisos)  # la serie no tiene alcista que la sostenga


def test_tocar_la_seguridad_y_cerrar_a_favor_es_rebote():
    lec = leer(vs.desde_vertices(REBOTE, 12))
    assert (lec.estado, lec.direccion) == ("REBOTE", "ALCISTA")
    seguridad = next(x for x in lec.lineas if x.rol == "seguridad")
    assert lec.vigilar.linea == seguridad and lec.invalidacion.linea == seguridad
    assert "rebote" in lec.conceptos and any("rebotó" in e.texto for e in lec.escenarios)


def test_rango_sin_diagonales():
    lec = leer(vs.desde_vertices(RANGO, 10))
    assert (lec.estado, lec.direccion) == ("RANGO", "LATERAL")
    bordes = [x for x in lec.lineas if x.rol == "rango"]
    assert len(bordes) == 2 and all(x.tipo == "horizontal" for x in bordes)


def test_sin_vela_en_curso_el_precio_es_el_ultimo_cierre():
    h4 = vs.desde_vertices(ALCISTA, 12)
    assert leer(h4).precio == float(h4["close"].iloc[-1])


def test_velas_sin_rango_fallan_con_mensaje():
    plano = pd.DataFrame({"time": [i * 14400 for i in range(40)], "open": [1.0] * 40,
                          "high": [1.0] * 40, "low": [1.0] * 40, "close": [1.0] * 40})
    with pytest.raises(ValueError, match="XAUUSD.*H4"):
        leer(plano)


def test_con_pocas_velas_lee_lo_que_hay():
    lec = leer(vs.desde_vertices([100, 104, 101], 10))
    assert lec.estado in ("RANGO", "TENDENCIA")


CIERRE = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))


def _vela(h4, precio):
    return VelaEnCurso(int(h4["time"].iloc[-1]) + 4 * 3600, precio, CIERRE)


def test_el_precio_vivo_bajo_la_seguridad_es_prueba_y_no_ruptura():
    h4 = vs.desde_vertices(ALCISTA, 12)
    base = leer(h4)
    seguridad = next(x for x in base.lineas if x.rol == "seguridad")
    lec = leer(h4, _vela(h4, seguridad.valor_actual - 5))
    assert lec.estado == "PRUEBA" and lec.direccion == "ALCISTA"
    assert lec.en_prueba.linea == seguridad and lec.en_prueba.cierre_vela == CIERRE
    assert any("13:00" in e.texto for e in lec.escenarios)


def test_un_precio_vivo_dentro_de_la_tolerancia_es_toque_no_prueba():
    h4 = vs.desde_vertices(ALCISTA, 12)
    seguridad = next(x for x in leer(h4).lineas if x.rol == "seguridad")
    lec = leer(h4, _vela(h4, seguridad.valor_actual + 0.25))  # la línea sube 0,25 en la vela abierta
    assert lec.estado == "TENDENCIA"


def test_la_vela_abierta_no_mueve_ninguna_linea():
    h4 = vs.desde_vertices(ALCISTA, 12)
    base = leer(h4)
    lec = leer(h4, _vela(h4, 90.0))
    sin_objetivo = lambda l: [x for x in l.lineas if x.rol != "objetivo"]  # noqa: E731
    assert sin_objetivo(lec) == sin_objetivo(base)


def test_en_rango_salir_del_borde_en_vivo_es_prueba():
    h4 = vs.desde_vertices(RANGO, 10)
    lec = leer(h4, _vela(h4, 125.0))
    assert lec.estado == "PRUEBA" and lec.en_prueba.linea.rol == "rango"
