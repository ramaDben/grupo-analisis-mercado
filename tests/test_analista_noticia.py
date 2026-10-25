"""La noticia de apertura del correo: lo que no pasa se descarta con su motivo y la pieza sigue."""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
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


def test_cifra_corta_con_muro_de_pago_descarta():
    """«8 %» o «50 puntos base» también son cifras: con muro de pago no pueden salir (revisión final)."""
    assert _cayo(_noticia(titular="El oro cae 8 % tras el dato", bajada="Según Reuters, el metal retrocede."),
                 estado="sin_verificar", pagina=None)


def test_cifra_corta_ausente_de_la_pagina_descarta():
    assert _cayo(_noticia(bajada="Según Reuters, la Fed recortó 50 puntos base."))


def test_la_coma_decimal_no_se_confunde_con_el_punto():
    """«4.200 dólares» no se respalda con «$42.00 per gram»: se comparan valores, no dígitos."""
    assert _cayo(_noticia(bajada="Según Reuters, el oro llegó a 4.200 dólares."), pagina="Gold at $42.00 per gram.")


def test_el_mismo_valor_en_notacion_inglesa_pasa():
    pieza, _ = _depurar(_noticia(bajada="Según Reuters, el oro subió a 4.100,50 dólares y ganó 3,67 % en 8 días."),
                        pagina="Spot gold rose to $4,100.50, a 3.67% gain over 8 sessions.")
    assert pieza["editorial"]["noticia"] is not None


# ── Candidatas de FXStreet (director, 2026-10-25): Python lee el RSS y sella las notas del activo ──

AHORA_FX = datetime(2026, 10, 25, 15, 0, tzinfo=ZoneInfo("America/Santiago"))
NOTA_FX = "https://www.fxstreet.es/news/el-oro-cae-por-debajo-de-4000-mientras-el-repunte-del-petroleo-202610231819"


def _item(titulo, url, pub, desc="El Oro cotiza en 4.000$ tras caer un 3.2%."):
    return (f"<item><title><![CDATA[{titulo}]]></title><link>{url}</link>"
            f"<pubDate>{pub}</pubDate><description><![CDATA[{desc}]]></description></item>")


def _rss(*items):
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{"".join(items)}</channel></rss>'


NOTICIAS_FX = _rss(
    _item("El Oro cae por debajo de 4.000$ mientras el repunte del petróleo profundiza la debacle", NOTA_FX,
          "Fri, 23 Oct 2026 18:19:00 GMT"),
    _item("Pronóstico del Precio del USD/JPY: El martillo señala riesgo de rebote",
          "https://www.fxstreet.es/news/usd-jpy-martillo-202610232325", "Fri, 23 Oct 2026 23:25:41 GMT"),
    _item("El oro sube con fuerza", "https://www.fxstreet.es/news/oro-viejo-202610201000",
          "Tue, 20 Oct 2026 10:00:00 GMT"),
    _item("El decoro del mercado", "https://www.fxstreet.es/news/decoro-202610241000", "Sat, 24 Oct 2026 10:00:00 GMT"),
)
ANALISIS_FX = _rss(
    _item("El Oro cae por debajo de 4.000$ mientras el repunte del petróleo profundiza la debacle", NOTA_FX,
          "Fri, 23 Oct 2026 18:19:00 GMT"),
    _item("Pronóstico del Oro: XAU/USD busca soporte", "https://www.fxstreet.es/analysis/xau-usd-soporte-202610240251",
          "Sat, 24 Oct 2026 02:51:00 GMT"),
)


def _feeds(url):
    return {nt.FEEDS_FX[0]: NOTICIAS_FX, nt.FEEDS_FX[1]: ANALISIS_FX}[url]


def test_candidatas_del_activo_dentro_de_la_ventana_y_sin_repetir():
    lista, aviso = nt.candidatas_fxstreet("XAUUSD", "Oro", AHORA_FX, leer=_feeds)
    assert aviso is None
    # La nota que aparece en los dos feeds va una vez; la del 20/10 queda fuera de los 3 días;
    # «decoro» no es «oro» y el USD/JPY no es del activo. La más reciente primero.
    assert [c["url"] for c in lista] == ["https://www.fxstreet.es/analysis/xau-usd-soporte-202610240251", NOTA_FX]
    assert set(lista[0]) == {"medio", "fecha", "url", "titular_original"}  # sin la descripción: trae precios y %
    assert lista[1]["medio"] == "FXStreet" and lista[1]["titular_original"].startswith("El Oro cae")


def test_la_fecha_de_la_candidata_es_la_de_chile():
    # 02:51 GMT del sábado 24 son las 23:51 del viernes 23 en Santiago (CLST, UTC-3).
    lista, _ = nt.candidatas_fxstreet("XAUUSD", "Oro", AHORA_FX, leer=_feeds)
    assert lista[0]["fecha"] == "2026-10-23"


def test_un_activo_sin_patron_busca_por_su_nombre():
    feed = _rss(_item("Apple supera las previsiones", "https://www.fxstreet.es/news/apple-202610241200",
                      "Sat, 24 Oct 2026 12:00:00 GMT"))
    lista, _ = nt.candidatas_fxstreet("#AAPL", "Apple", AHORA_FX, leer=lambda url: feed)
    assert [c["url"] for c in lista] == ["https://www.fxstreet.es/news/apple-202610241200"]


def test_fxstreet_caido_avisa_y_no_bota_la_pieza():
    def caido(url):
        raise OSError("sin red")

    lista, aviso = nt.candidatas_fxstreet("XAUUSD", "Oro", AHORA_FX, leer=caido)
    assert lista == [] and "FXStreet" in aviso


def test_un_feed_ilegible_no_tapa_al_otro():
    lista, aviso = nt.candidatas_fxstreet("XAUUSD", "Oro", AHORA_FX,
                                          leer=lambda url: ANALISIS_FX if url == nt.FEEDS_FX[1] else "<html>403")
    assert len(lista) == 2 and aviso is None


PAGINA_FX = ("El par cotiza en 156.85 mientras se forma un patrón de vela martillo, con pérdidas "
             "superiores al 0.74% semanal.")


def test_cifra_de_fxstreet_en_notacion_chilena_pasa():
    n = _noticia(medio="FXStreet", url=NOTA_FX, titular="El USD/JPY cotiza en 156,85 tras caer 0,74 % en la semana",
                 bajada="Según FXStreet, el par forma un patrón de vela martillo.")
    pieza, descartes = nt.depurar_noticia(_pieza(n), HOY, verificar=lambda url: "ok", leer=lambda url: PAGINA_FX)
    assert descartes == [] and pieza["editorial"]["noticia"]["titular"].startswith("El USD/JPY")


def test_cifra_de_fxstreet_copiada_en_notacion_inglesa_se_descarta():
    n = _noticia(medio="FXStreet", url=NOTA_FX, titular="El USD/JPY cotiza en 156.85",
                 bajada="Según FXStreet, el par forma un patrón de vela martillo.")
    pieza, descartes = nt.depurar_noticia(_pieza(n), HOY, verificar=lambda url: "ok", leer=lambda url: PAGINA_FX)
    assert pieza["editorial"]["noticia"] is None and "156.85" in descartes[0]
