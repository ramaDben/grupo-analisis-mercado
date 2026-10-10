"""Toda estrategia registrable pasa la batería de conformidad (spec §4)."""
from __future__ import annotations

import pytest

import estrategia_conformidad as conf
import estrategia_juguete

FABRICAS = {"juguete": estrategia_juguete.crear}
CON_SEGUIR = {"juguete"}  # S3-6 agrega "tori" cuando Tori implementa seguir()

VERIFICACIONES = (
    conf.verificar_sin_futuro, conf.verificar_escenarios,
    conf.verificar_prueba_solo_con_vela_en_curso, conf.verificar_procedencia,
    conf.verificar_marco_y_puntaje, conf.verificar_divergencia_propia,
)
VERIFICACIONES_SEGUIR = (
    conf.verificar_seguir_misma_lectura, conf.verificar_seguir_sin_futuro,
    conf.verificar_seguir_anclas_fijas,
)


@pytest.mark.parametrize("nombre", sorted(FABRICAS))
@pytest.mark.parametrize("verificar", VERIFICACIONES, ids=lambda f: f.__name__)
def test_conformidad(nombre, verificar):
    verificar(FABRICAS[nombre])


@pytest.mark.parametrize("nombre", sorted(CON_SEGUIR))
@pytest.mark.parametrize("verificar", VERIFICACIONES_SEGUIR, ids=lambda f: f.__name__)
def test_conformidad_seguir(nombre, verificar):
    verificar(FABRICAS[nombre])


def test_la_bateria_pilla_una_estrategia_con_memoria():
    with pytest.raises(AssertionError, match="futuro"):
        conf.verificar_sin_futuro(estrategia_juguete.crear_con_memoria)


def test_el_juguete_entra_en_prueba_con_la_vela_fuera_del_rango():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from estrategia.contrato import VelaEnCurso

    e = estrategia_juguete.crear()
    velas = conf.velas_de(e)
    cierre = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))
    lectura = e.leer("X", velas, 2, VelaEnCurso(0, 10_000.0, cierre))
    assert lectura.estado == "PRUEBA" and lectura.en_prueba.linea.valor_actual == lectura.vigilar.precio
