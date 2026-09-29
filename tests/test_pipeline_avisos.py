"""Carruseles de Avisos (spec 2026-09-28-carruseles-avisos-design.md)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pipeline_avisos as pa  # noqa: E402

LUNES = date(2026, 9, 28)
MARTES = date(2026, 9, 29)


def test_feriado_nyse_no_es_habil():
    assert pa.es_dia_habil(date(2026, 11, 26)) is False  # Acción de Gracias


def test_sabado_no_es_habil_y_martes_si():
    assert pa.es_dia_habil(date(2026, 10, 3)) is False
    assert pa.es_dia_habil(MARTES) is True


def test_la_tarde_es_agenda_el_lunes_y_balance_el_resto():
    assert pa.formato_del_momento("avisos_tarde", LUNES) == "agenda"
    assert pa.formato_del_momento("avisos_tarde", MARTES) == "balance"
    assert pa.formato_del_momento("avisos_manana", MARTES) == "cita"
    assert pa.formato_del_momento("avisos_mediodia", MARTES) == "meta"


def test_momento_desconocido_se_detiene_nombrando_las_opciones():
    with pytest.raises(SystemExit, match="avisos_manana"):
        pa.formato_del_momento("avisos_noche", MARTES)


def test_laminas_con_voz_numeran_sobre_cuatro():
    laminas = pa.laminas_de("cita", con_voz=True)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert laminas[1]["posicion"] == "2/4 · La voz del banco"
    assert laminas[2]["plantilla"] == "avisos_datos"


def test_laminas_sin_voz_renumeran_sobre_tres():
    laminas = pa.laminas_de("meta", con_voz=False)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_datos", "3_lectura"]
    assert laminas[2]["posicion"] == "3/3 · Nuestra lectura"


def test_la_agenda_no_lleva_voz_ni_alerta():
    assert [l["clave"] for l in pa.laminas_de("agenda", con_voz=True)] == ["portada", "semana", "lectura"]


@pytest.mark.xfail(strict=True, reason="vision.html llega en la Tarea 4")
def test_toda_plantilla_de_lamina_existe_en_disco():
    for plantilla, archivo in pa.PLANTILLAS.items():
        assert (pa.DIR_PLANTILLAS / archivo).exists(), f"{plantilla}: falta {archivo}"


def test_ninguna_secuencia_pasa_del_tope():
    assert all(len(s) <= pa.MAX_LAMINAS for s in pa.SECUENCIAS.values())


def test_etiqueta_hora_nombra_el_horario_chileno():
    verano = datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO)
    invierno = datetime(2026, 7, 1, 11, 30, tzinfo=pa.SANTIAGO)
    assert pa.etiqueta_hora(verano) == "11:30 CLST"
    assert pa.etiqueta_hora(invierno) == "11:30 CLT"
    assert pa.fecha_hora(verano) == "MARTES 29 SEP · 11:30 CLST"
