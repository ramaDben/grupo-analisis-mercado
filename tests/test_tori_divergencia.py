"""divergencia(): la pieza no sale si el texto quedó escrito para otra lectura (spec §4)."""
from __future__ import annotations

from dataclasses import replace

import test_tori_lectura as tl

from estrategia.tori.lectura import divergencia


def test_la_misma_lectura_no_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    assert divergencia(lec, lec) is None


def test_una_prueba_que_ya_cerro_diverge():
    h4 = tl.vs.desde_vertices(tl.ALCISTA, 12)
    preparada = tl.leer(h4, tl._vela(h4, 90.0))
    actual = tl.leer(h4)
    assert preparada.estado == "PRUEBA"
    assert "cerró" in divergencia(preparada, actual)


def test_el_precio_que_cruza_la_referencia_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    cruzada = replace(lec, precio=lec.invalidacion.precio - 10)
    assert divergencia(lec, cruzada) is not None


def test_pasar_de_tendencia_a_rebote_no_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    assert divergencia(lec, replace(lec, estado="REBOTE")) is None
    assert divergencia(replace(lec, estado="REBOTE"), lec) is None


def test_un_cambio_de_direccion_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    bajista = tl.leer(tl.vs.desde_vertices(tl.BAJISTA, 12))
    assert bajista.direccion == "BAJISTA"
    assert "dirección" in divergencia(lec, bajista)
