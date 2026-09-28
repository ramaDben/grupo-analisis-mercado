"""Índices de referencia para el contexto macro (decisión del director, 2026-09-28).

Los tres canales recibían la misma imagen del bono. Ahora cada uno cuelga de un
indicador distinto: el de avisos del VIX, el de divisas del dólar global (DXY).
El módulo nunca lanza: una fuente caída devuelve [] y el contexto macro cae al
bono a 10 años, que siempre tiene fuente.
"""
from __future__ import annotations

from datetime import date

from market_data_mcp import indices_referencia as ir


def _cierres(n=20):
    return [(date(2026, 9, 1 + i), 15.0 + i / 10) for i in range(n)]


def test_devuelve_los_ultimos_n_cierres_en_orden():
    pedidos = []

    def descargar(ticker):
        pedidos.append(ticker)
        return list(reversed(_cierres()))

    serie = ir.serie_diaria("VIX", 15, descargar=descargar)
    assert pedidos == ["^VIX"]
    assert len(serie) == 15
    assert serie[-1] == (date(2026, 9, 20), 16.9)
    assert [d for d, _ in serie] == sorted(d for d, _ in serie)


def test_el_dxy_se_pide_con_el_indice_oficial_de_ice():
    pedidos = []
    ir.serie_diaria("DXY", 15, descargar=lambda t: pedidos.append(t) or _cierres())
    assert pedidos == ["DX-Y.NYB"]


def test_el_vxn_se_pide_con_el_indice_oficial_de_cboe():
    pedidos = []
    ir.serie_diaria("VXN", 15, descargar=lambda t: pedidos.append(t) or _cierres())
    assert pedidos == ["^VXN"]

def test_una_fuente_caida_devuelve_vacio_y_no_lanza():
    def cae(ticker):
        raise OSError("sin red")

    assert ir.serie_diaria("VIX", 15, descargar=cae) == []


def test_con_menos_de_dos_cierres_no_hay_serie():
    """Sin cierre previo no hay variación que publicar, y un punto no es gráfico."""
    assert ir.serie_diaria("VIX", 15, descargar=lambda t: _cierres(1)) == []


def test_un_codigo_desconocido_no_consulta_nada():
    assert ir.serie_diaria("TIPS", 15, descargar=lambda t: _cierres()) == []


def test_descarta_cierres_no_numericos():
    datos = _cierres(5) + [(date(2026, 9, 30), float("nan"))]
    serie = ir.serie_diaria("VIX", 15, descargar=lambda t: datos)
    assert all(v == v for _, v in serie) and len(serie) == 5
