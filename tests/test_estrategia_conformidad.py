"""Toda estrategia registrable pasa la batería de conformidad (spec §4)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import estrategia_conformidad as conf  # noqa: E402
import estrategia_juguete  # noqa: E402

from estrategia import tori  # noqa: E402

FABRICAS = {"juguete": estrategia_juguete.crear, "tori": tori.crear}
CON_SEGUIR = {"juguete", "tori"}

VERIFICACIONES = (
    conf.verificar_sin_futuro, conf.verificar_escenarios,
    conf.verificar_prueba_solo_con_vela_en_curso, conf.verificar_procedencia,
    conf.verificar_marco_y_puntaje, conf.verificar_divergencia_propia,
    conf.verificar_vela_cerrada, conf.verificar_json_plano,
    conf.verificar_divergencia_prueba_cerrada,
)
VERIFICACIONES_SEGUIR = (
    conf.verificar_seguir_misma_lectura, conf.verificar_seguir_sin_futuro,
    conf.verificar_seguir_anclas_fijas, conf.verificar_seguir_ruptura_y_prueba,
    conf.verificar_seguir_ruptura_falsa,
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


# --- Pruebas negativas: cada verificación tiene que fallar ante su incumplimiento ---

class SeguirConMemoria(estrategia_juguete.Juguete):
    def __init__(self):
        self._vistas = {}

    def seguir(self, referencia, velas, digits, en_curso=None):
        return self._vistas.setdefault(
            referencia.ticker, super().seguir(referencia, velas, digits, en_curso))


class SeguirRetraza(estrategia_juguete.Juguete):
    def seguir(self, referencia, velas, digits, en_curso=None):
        return self.leer(referencia.ticker, velas, digits, en_curso)


class VelaAbiertaMueveLinea(estrategia_juguete.Juguete):
    def leer(self, ticker, velas, digits, en_curso=None):
        lectura = super().leer(ticker, velas, digits, en_curso)
        if en_curso is None:
            return lectura
        return replace(lectura, lineas=tuple(
            replace(x, valor_actual=x.valor_actual + 1.0) for x in lectura.lineas))


class NuncaEntraEnPrueba(estrategia_juguete.Juguete):
    def leer(self, ticker, velas, digits, en_curso=None):
        return super().leer(ticker, velas, digits, None)


class PuntuarSinPuntaje(estrategia_juguete.Juguete):
    def puntuar(self, lectura, horizonte):
        return 50


class DivergenciaNunca(estrategia_juguete.Juguete):
    def divergencia(self, preparada, actual):
        return None


class VelaCero(estrategia_juguete.Juguete):
    def leer(self, ticker, velas, digits, en_curso=None):
        return replace(super().leer(ticker, velas, digits, en_curso), vela=0)


class VelaNumpy(estrategia_juguete.Juguete):
    def leer(self, ticker, velas, digits, en_curso=None):
        lectura = super().leer(ticker, velas, digits, en_curso)
        return replace(lectura, vela=np.int64(lectura.vela))


class DivergenciaSoloDireccion(estrategia_juguete.Juguete):
    def divergencia(self, preparada, actual):
        return None if preparada.direccion == actual.direccion else "cambió la dirección"


class SeguirSinRuptura(estrategia_juguete.Juguete):
    def seguir(self, referencia, velas, digits, en_curso=None):
        hoy = super().seguir(referencia, velas, digits, en_curso)
        return replace(hoy, estado=referencia.estado) if hoy.estado == "RUPTURA" else hoy


class SeguirSinPrueba(estrategia_juguete.Juguete):
    def seguir(self, referencia, velas, digits, en_curso=None):
        return super().seguir(referencia, velas, digits, None)


class SeguirRupturaSinVuelta(estrategia_juguete.Juguete):
    """Cuenta como ruptura cualquier cierre afuera, aunque el precio haya vuelto."""

    def seguir(self, referencia, velas, digits, en_curso=None):
        hoy = super().seguir(referencia, velas, digits, en_curso)
        techo, piso = referencia.lineas
        despues = velas["H4"][velas["H4"]["time"] > referencia.vela]["close"]
        if ((despues > techo.valor_actual) | (despues < piso.valor_actual)).any():
            return replace(hoy, estado="RUPTURA", en_prueba=None)
        return hoy


class ProcedenciaNoVerificada(estrategia_juguete.Juguete):
    procedencia = replace(
        estrategia_juguete.Juguete.procedencia,
        fundamentos=(replace(estrategia_juguete.Juguete.procedencia.fundamentos[0],
                             canonico=("F999 p. 1",)),),
    )


MUTANTES = (
    (SeguirConMemoria, conf.verificar_seguir_sin_futuro),
    (SeguirRetraza, conf.verificar_seguir_anclas_fijas),
    (VelaAbiertaMueveLinea, conf.verificar_prueba_solo_con_vela_en_curso),
    (NuncaEntraEnPrueba, conf.verificar_prueba_solo_con_vela_en_curso),
    (PuntuarSinPuntaje, conf.verificar_marco_y_puntaje),
    (DivergenciaNunca, conf.verificar_divergencia_propia),
    (ProcedenciaNoVerificada, conf.verificar_procedencia),
    (VelaCero, conf.verificar_vela_cerrada),
    (VelaNumpy, conf.verificar_json_plano),
    (DivergenciaSoloDireccion, conf.verificar_divergencia_prueba_cerrada),
    (SeguirSinRuptura, conf.verificar_seguir_ruptura_y_prueba),
    (SeguirSinPrueba, conf.verificar_seguir_ruptura_y_prueba),
    (SeguirRupturaSinVuelta, conf.verificar_seguir_ruptura_falsa),
)


@pytest.mark.parametrize("mutante,verificar", MUTANTES,
                         ids=lambda x: getattr(x, "__name__", str(x)))
def test_la_bateria_pilla_cada_incumplimiento(mutante, verificar):
    with pytest.raises(AssertionError):
        verificar(mutante)
