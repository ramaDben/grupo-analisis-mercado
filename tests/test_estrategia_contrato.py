"""Contrato del enchufe: los tipos rechazan una lectura mal formada al construirse."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import (  # noqa: E402
    Escenario, Etiqueta, Lectura, Linea, Marcos, Prueba, Puntaje, Referencia, VelaEnCurso,
    exigir_velas, lectura_a_dict, lectura_de_dict,
)

SCL = ZoneInfo("America/Santiago")
LINEA = Linea("seguridad", "diagonal", ((1, 100.0), (2, 101.0)), "H4", 3, "A+", 105.0)
TRES = (Escenario("⬆️", "Sobre 105", "sube"), Escenario("↔️", "Entre", "espera"),
        Escenario("⬇️", "Bajo 105", "baja"))


def _lectura(**cambios) -> Lectura:
    base = Lectura(
        ticker="XAUUSD", marco="H4", precio=106.0, direccion="ALCISTA", estado="TENDENCIA",
        lineas=(LINEA,), en_prueba=None, vigilar=Referencia(105.0, "línea alcista", LINEA),
        invalidacion=Referencia(105.0, "línea alcista de seguridad", LINEA), objetivo=None,
        escenarios=TRES, salida="sale", conceptos=(), avisos=(),
    )
    return replace(base, **cambios)


def test_una_lectura_bien_formada_se_construye():
    assert _lectura().estado == "TENDENCIA"


def test_exige_exactamente_un_escenario_por_flecha():
    with pytest.raises(ValueError, match="escenario"):
        _lectura(escenarios=TRES[:2])
    with pytest.raises(ValueError, match="escenario"):
        _lectura(escenarios=(TRES[0], TRES[0], TRES[2]))


def test_prueba_va_solo_y_siempre_con_el_estado_prueba():
    prueba = Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0, tzinfo=SCL))
    with pytest.raises(ValueError, match="en_prueba"):
        _lectura(estado="PRUEBA")
    with pytest.raises(ValueError, match="en_prueba"):
        _lectura(en_prueba=prueba)
    assert _lectura(estado="PRUEBA", en_prueba=prueba).en_prueba is prueba


def test_la_hora_de_cierre_exige_zona_horaria():
    with pytest.raises(ValueError, match="zona"):
        Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0))
    with pytest.raises(ValueError, match="zona"):
        VelaEnCurso(10, 100.0, datetime(2026, 10, 9, 13, 0))


def test_una_diagonal_lleva_dos_anclas_y_una_horizontal_una():
    with pytest.raises(ValueError, match="anclas"):
        Linea("accion", "diagonal", ((1, 100.0),), "H4", 2, "B", 100.0)
    with pytest.raises(ValueError, match="anclas"):
        Linea("objetivo", "horizontal", ((1, 100.0), (2, 100.0)), "H4", 2, "", 100.0)


def test_la_calidad_es_a_mas_b_o_vacia():
    with pytest.raises(ValueError, match="calidad"):
        Linea("accion", "diagonal", ((1, 100.0), (2, 101.0)), "H4", 2, "C", 100.0)


def test_el_puntaje_va_de_0_a_100():
    with pytest.raises(ValueError, match="0 y 100"):
        Puntaje(101.0, {}, None)
    assert Puntaje(0.0, {}, "sin líneas").excluido == "sin líneas"


def test_marcos_exige_velas_y_etiqueta_por_marco():
    with pytest.raises(ValueError, match="D1"):
        Marcos(("D1",), "H4", {"H4": 10}, {"H4": Etiqueta("swing", "de una a dos semanas")})


def test_exigir_velas_nombra_lo_que_falta():
    marcos = Marcos((), "H4", {"H4": 10}, {"H4": Etiqueta("swing", "de una a dos semanas")})
    with pytest.raises(ValueError, match="H4"):
        exigir_velas({}, marcos)
    sin_close = pd.DataFrame({"time": [1, 2], "open": [1, 1], "high": [1, 1], "low": [1, 1]})
    with pytest.raises(ValueError, match="close"):
        exigir_velas({"H4": sin_close}, marcos)
    desordenadas = pd.DataFrame({"time": [2, 1], "open": [1, 1], "high": [1, 1], "low": [1, 1],
                                 "close": [1, 1]})
    with pytest.raises(ValueError, match="orden"):
        exigir_velas({"H4": desordenadas}, marcos)


def test_la_lectura_sobrevive_ida_y_vuelta_por_json():
    """Así se guarda la referencia semanal (spec §4)."""
    prueba = Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0, tzinfo=SCL))
    lectura = _lectura(estado="PRUEBA", en_prueba=prueba, vela=1_760_000_000, metricas={"atr": 1.5})
    texto = json.dumps(lectura_a_dict(lectura), ensure_ascii=False)
    assert lectura_de_dict(json.loads(texto)) == lectura
