"""La noticia de apertura del correo: lo que no pasa se descarta con su motivo y la pieza sigue."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import esquema as es  # noqa: E402
from analista import noticia as nt  # noqa: E402

HOY = date(2026, 10, 24)
URL = "https://www.reuters.com/markets/commodities/gold-recovers-2026-10-23/"


def _noticia(**cambios):
    n = {
        "medio": "Reuters", "fecha": (HOY - timedelta(days=1)).isoformat(), "url": URL,
        "titular_original": "Gold recovers from two-month low as dollar rally stalls",
        "extracto": "Spot gold rose to $4,100.50 per ounce.",
        "titular": "El oro se recupera de su mínimo de dos meses",
        "bajada": "Según Reuters, el oro subió a 4.100,50 dólares la onza mientras el dólar pierde impulso.",
        "motivo": "oro_lingotes",
    }
    n.update(cambios)
    return n


def _pieza(n):
    return {"editorial": {"noticia": n}}


def _depurar(n, estado="ok", pagina="Spot gold rose to $4,100.50 per ounce, a 3.67% gain."):
    return nt.depurar_noticia(_pieza(n), HOY, verificar=lambda url: estado, leer=lambda url: pagina)


def _cayo(n, **kw):
    pieza, descartes = _depurar(n, **kw)
    return pieza["editorial"]["noticia"] is None and len(descartes) == 1


def test_noticia_valida_pasa():
    pieza, descartes = _depurar(_noticia())
    assert pieza["editorial"]["noticia"]["titular"].startswith("El oro")
    assert descartes == []


def test_cifra_ausente_de_la_pagina_descarta():
    pieza, descartes = _depurar(_noticia(bajada="Según Reuters, el oro subió a 4.200 dólares."))
    assert pieza["editorial"]["noticia"] is None
    assert descartes[0].startswith("Noticia de apertura: ") and "4.200" in descartes[0]


def test_cifra_en_otro_formato_descarta():
    assert _cayo(_noticia(bajada="Según Reuters, facturó 20.060 millones."), pagina="Revenue of $20.06B")


def test_muro_de_pago_sin_cifras_pasa():
    pieza, _ = _depurar(_noticia(bajada="Según Reuters, el oro sube mientras el dólar pierde impulso."),
                        estado="sin_verificar", pagina=None)
    assert pieza["editorial"]["noticia"] is not None


def test_muro_de_pago_con_cifras_descarta():
    assert _cayo(_noticia(), estado="sin_verificar", pagina=None)


def test_pagina_ilegible_con_cifras_descarta():
    assert _cayo(_noticia(), estado="ok", pagina=None)


def test_url_muerta_descarta():
    assert _cayo(_noticia(), estado="muerta")


def test_medio_fuera_de_lista_descarta():
    assert _cayo(_noticia(medio="Investing.com", url="https://www.investing.com/news/gold-123"))


def test_dominio_distinto_del_medio_descarta():
    assert _cayo(_noticia(url="https://www.bloomberg.com/news/articles/2026-10-23/gold"))


def test_portada_descarta():
    assert _cayo(_noticia(url="https://www.reuters.com/"))


def test_fecha_vieja_descarta():
    assert _cayo(_noticia(fecha=(HOY - timedelta(days=4)).isoformat()))


@pytest.mark.parametrize("fecha", ["2026-13-01", "ayer", (HOY + timedelta(days=1)).isoformat()])
def test_fecha_futura_o_malformada_descarta(fecha):
    assert _cayo(_noticia(fecha=fecha))


def test_porcentaje_permitido_si_esta_en_la_fuente():
    pieza, _ = _depurar(_noticia(bajada="Según Reuters, el oro ganó 3,67 % en la sesión."))
    assert pieza["editorial"]["noticia"] is not None


def test_guion_largo_descarta():
    assert _cayo(_noticia(titular="El oro se recupera — y el dólar frena"))


def test_invitacion_a_operar_descarta():
    assert _cayo(_noticia(titular="El oro se recupera y conviene comprar"))


def test_titular_largo_descarta():
    assert _cayo(_noticia(titular="a" * 91))


def test_bajada_larga_descarta():
    assert _cayo(_noticia(bajada="a" * 201))


def test_motivo_fuera_de_catalogo_descarta():
    assert _cayo(_noticia(motivo="bandera_chile"))


def test_campo_faltante_descarta():
    n = _noticia()
    del n["extracto"]
    assert _cayo(n)


@pytest.mark.parametrize("vacia", [es.MARCA, None, {}])
def test_sin_escribir_o_nula_no_es_error(vacia):
    pieza, descartes = _depurar(vacia)
    assert pieza["editorial"]["noticia"] is None
    assert descartes == ([] if vacia in (es.MARCA, None) else descartes)


def test_pieza_sin_campo_noticia_no_cambia():
    pieza, descartes = nt.depurar_noticia({"editorial": {}}, HOY, verificar=lambda u: "ok", leer=lambda u: "")
    assert "noticia" not in pieza["editorial"] and descartes == []


def test_vigente_cuenta_tres_dias():
    assert nt.vigente(_noticia(fecha="2026-10-21"), HOY)
    assert not nt.vigente(_noticia(fecha="2026-10-20"), HOY)
