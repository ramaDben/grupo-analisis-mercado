"""La referencia semanal: guardar, leer y cuándo reemplazarla (spec §4)."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
from dataclasses import replace
from datetime import datetime

from estrategia.contrato import SCL, Escenario, Lectura, Linea, Referencia  # noqa: E402
import referencia_semanal as rs  # noqa: E402


def _linea(rol="seguridad", puntos=((100, 10.0), (200, 11.0))):
    return Linea(rol=rol, tipo="diagonal", puntos=puntos, marco="H4", toques=3,
                 calidad="A+", valor_actual=11.5)


def _lectura(estado="TENDENCIA", lineas=None):
    lineas = lineas if lineas is not None else (_linea(), _linea("accion", ((150, 13.0), (250, 12.0))))
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker="XAUUSD", marco="H4", precio=12.0, direccion="ALCISTA", estado=estado,
                   lineas=lineas, en_prueba=None, vigilar=Referencia(11.5, "línea alcista de seguridad"),
                   invalidacion=None, objetivo=None, escenarios=esc, salida="s", conceptos=(),
                   avisos=(), metricas={"atr": 1.0}, vela=250)


def test_la_semana_es_la_iso_de_la_fecha_de_santiago():
    # Domingo 2026-10-11 23:30 en Santiago es todavía la semana 41.
    assert rs.semana_de(datetime(2026, 10, 11, 23, 30, tzinfo=SCL)) == "2026-W41"
    assert rs.semana_de(datetime(2026, 10, 12, 0, 5, tzinfo=SCL)) == "2026-W42"


def test_el_slug_saca_sufijos_del_broker():
    assert rs.slug("WTI.spot") == "wti"
    assert rs.slug("#NVDA") == "nvda"
    assert rs.slug("USDCLP") == "usdclp"


def test_guardar_y_cargar_devuelven_la_misma_lectura(tmp_path):
    lec = _lectura()
    ruta = rs.guardar(lec, "2026-W42", "semanal", datetime(2026, 10, 12, 9, 0, tzinfo=SCL), base=tmp_path)
    assert ruta == tmp_path / "2026-W42" / "xauusd.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["motivo"] == "semanal" and datos["ticker"] == "XAUUSD"
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) == lec


def test_sin_archivo_no_hay_referencia(tmp_path):
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) is None
    assert rs.manifiesto("2026-W42", base=tmp_path) is None


def test_una_referencia_en_prueba_no_se_guarda(tmp_path):
    import pytest
    from estrategia.contrato import Prueba
    lec = _lectura()
    prueba = replace(lec, estado="PRUEBA",
                     en_prueba=Prueba(_linea(), 11.6, datetime(2026, 10, 12, 13, 0, tzinfo=SCL)))
    with pytest.raises(ValueError, match="PRUEBA"):
        rs.guardar(prueba, "2026-W42", "semanal", datetime.now(SCL), base=tmp_path)


def test_el_manifiesto_se_guarda_y_se_lee(tmp_path):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["XAUUSD"]}, base=tmp_path)
    assert rs.manifiesto("2026-W42", base=tmp_path)["elegidos"] == ["XAUUSD"]


def test_la_misma_estructura_no_se_reemplaza_aunque_cambie_el_valor_de_hoy():
    ref = _lectura()
    hoy = replace(ref, lineas=tuple(replace(x, valor_actual=99.0) for x in ref.lineas), precio=13.0)
    assert not rs.debe_reemplazar(ref, hoy)


def test_tendencia_y_rebote_no_reemplazan():
    ref = _lectura()
    assert not rs.debe_reemplazar(ref, replace(ref, estado="REBOTE"))


def test_roles_reasignados_por_una_ruptura_reemplazan():
    ref = _lectura()
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),
                                                   replace(ref.lineas[1], rol="seguridad")))
    assert rs.debe_reemplazar(ref, rota)


def test_anclas_nuevas_reemplazan():
    ref = _lectura()
    retrazada = replace(ref, lineas=(_linea(puntos=((120, 10.0), (220, 11.0))), ref.lineas[1]))
    assert rs.debe_reemplazar(ref, retrazada)


def test_pasar_a_ruptura_reemplaza_aunque_las_lineas_no_cambien():
    ref = _lectura(estado="RANGO", lineas=())
    assert rs.debe_reemplazar(ref, replace(ref, estado="RUPTURA"))


def test_una_referencia_en_ruptura_que_sigue_igual_no_se_reemplaza():
    ref = _lectura(estado="RUPTURA")
    assert not rs.debe_reemplazar(ref, replace(ref, precio=13.5))
