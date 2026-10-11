"""Los textos de Tori cumplen las reglas de texto de cliente (CLAUDE.md)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_tori_lectura as tl  # noqa: E402
import test_tori_seguir as ts  # noqa: E402

VOSEO = re.compile(r"\b(ten[ée]s|pod[ée]s|sab[ée]s|mir[áa]|fijate|and[áa])\b", re.IGNORECASE)
CASOS = {
    "tendencia": lambda: tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12)),
    "ruptura": lambda: tl.leer(tl.rota()),
    "ruptura de rango": lambda: _ruptura_de_rango(),
    "rango": lambda: tl.leer(tl.vs.desde_vertices(tl.RANGO, 10)),
    "rebote": lambda: tl.leer(tl.vs.desde_vertices(tl.REBOTE, 12)),
    "prueba": lambda: tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12),
                              tl._vela(tl.vs.desde_vertices(tl.ALCISTA, 12), 90.0)),
}



def _ruptura_de_rango():
    """Referencia en RANGO con bordes horizontales y una vela que cierra sobre el de arriba."""
    h4 = tl.vs.desde_vertices(tl.RANGO, 10)
    return ts.seguir(tl.leer(h4), ts.extender(h4, [105, 125], 4))


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_sin_guion_largo_ni_voseo(caso):
    lec = CASOS[caso]()
    textos = [lec.salida] + [e.texto for e in lec.escenarios] + [e.condicion for e in lec.escenarios]
    for t in textos:
        assert "—" not in t and "–" not in t, t
        assert not VOSEO.search(t), t


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_cada_escenario_nombra_un_precio_en_notacion_chilena(caso):
    lec = CASOS[caso]()
    for e in lec.escenarios:
        assert re.search(r"\d+,\d{2}", e.condicion + e.texto), e


def test_la_ruptura_se_describe_como_cierre():
    lec = CASOS["ruptura"]()
    assert any("cerró" in e.texto for e in lec.escenarios)


def test_la_ruptura_de_un_borde_horizontal_nombra_el_borde_y_no_una_linea_diagonal():
    lec = CASOS["ruptura de rango"]()
    assert lec.estado == "RUPTURA"
    textos = [e.texto for e in lec.escenarios] + [e.condicion for e in lec.escenarios]
    assert not any("línea bajista" in t or "línea alcista" in t for t in textos), textos
    assert any("resistencia del rango" in t for t in textos), textos
    # El aviso de rango del lunes ya no describe la lectura de hoy.
    assert not any("se lee como rango" in a for a in lec.avisos), lec.avisos


def test_el_sentido_no_depende_de_que_las_anclas_redondeadas_empaten():
    # Con digits 0 una línea poco inclinada puede redondear sus dos anclas al mismo precio:
    # eso no la vuelve bajista. La pendiente se lee entonces contra el valor de hoy.
    from estrategia.contrato import Linea
    from estrategia.tori.textos import sentido

    def linea(valor_actual):
        return Linea("seguridad", "diagonal", ((0, 100.0), (14400, 100.0)), "H4", 3, "A+", valor_actual)

    assert sentido(linea(101.0)) == "alcista"
    assert sentido(linea(99.0)) == "bajista"
    assert sentido(linea(100.0)) == "horizontal"


def test_en_rango_se_opera_el_falso_quiebre():
    # Decisión del director (2026-09-28), confirmada en el gate del PR #258: la zona media se
    # opera con el falso quiebre, de vuelta al borde contrario; nunca "no hay operación".
    lec = CASOS["rango"]()
    assert lec.estado == "RANGO"
    medio = next(e for e in lec.escenarios if e.flecha == "↔️")
    assert "falso quiebre" in medio.texto and "borde contrario" in medio.texto, medio.texto
    assert "no hay operación" not in medio.texto
    assert "falso quiebre" in lec.salida and "no hay posición" not in lec.salida, lec.salida
    assert "falso-quiebre" in lec.conceptos
