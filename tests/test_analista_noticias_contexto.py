"""Pruebas para candidatas de noticias multi-fuente (FXStreet e Investing.com)."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import noticia as nt  # noqa: E402
from analista import noticias_contexto as nctx  # noqa: E402

AHORA = datetime(2026, 10, 25, 15, 0, tzinfo=ZoneInfo("America/Santiago"))


def _item(titulo: str, url: str, pub: str, desc: str = "Descripción") -> str:
    return (f"<item><title><![CDATA[{titulo}]]></title><link>{url}</link>"
            f"<pubDate>{pub}</pubDate><description><![CDATA[{desc}]]></description></item>")


def _rss(*items: str) -> str:
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{"".join(items)}</channel></rss>'


def test_junta_fxstreet_e_investing_sin_repetir_url():
    url_comun = "https://www.reuters.com/markets/commodities/oro-comun-20261024"
    fx_rss = _rss(
        _item("El Oro sube con fuerza ante debilidad del dólar", url_comun, "Sat, 24 Oct 2026 12:00:00 GMT"),
        _item("El Oro busca consolidar soporte clave", "https://www.fxstreet.es/news/oro-2", "Sat, 24 Oct 2026 10:00:00 GMT"),
    )
    inv_rss = _rss(
        _item("El Oro marca máximos de la semana", url_comun, "Sat, 24 Oct 2026 14:00:00 GMT"),
        _item("Perspectivas del Oro tras declaraciones de la Fed", "https://es.investing.com/news/oro-3", "Sat, 24 Oct 2026 11:00:00 GMT"),
    )

    def fake_leer(url: str) -> str:
        if "investing.com" in url:
            return inv_rss
        return fx_rss

    lista, avisos = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert len(lista) == 3
    assert len({c["url"] for c in lista}) == 3
    assert avisos == []
    medios = {c["medio"] for c in lista}
    assert medios == {"FXStreet", "Investing.com"}


def test_alterna_fuentes_para_dar_diversidad():
    fx_rss = _rss(
        _item("El Oro sube 1", "https://www.fxstreet.es/news/oro-1", "Sat, 24 Oct 2026 14:00:00 GMT"),
        _item("El Oro sube 2", "https://www.fxstreet.es/news/oro-2", "Sat, 24 Oct 2026 13:00:00 GMT"),
        _item("El Oro sube 3", "https://www.fxstreet.es/news/oro-3", "Sat, 24 Oct 2026 12:00:00 GMT"),
        _item("El Oro sube 4", "https://www.fxstreet.es/news/oro-4", "Sat, 24 Oct 2026 11:00:00 GMT"),
    )
    inv_rss = _rss(
        _item("El Oro avanza A", "https://es.investing.com/news/oro-a", "Sat, 24 Oct 2026 15:00:00 GMT"),
        _item("El Oro avanza B", "https://es.investing.com/news/oro-b", "Sat, 24 Oct 2026 10:00:00 GMT"),
    )

    def fake_leer(url: str) -> str:
        if "investing.com" in url:
            return inv_rss
        return fx_rss

    lista, _ = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert len(lista) >= 2
    assert lista[0]["medio"] != lista[1]["medio"]


def test_respeta_ventana_de_3_dias_y_patrones_del_activo():
    fx_rss = _rss(
        _item("El Oro cotiza estable", "https://www.fxstreet.es/news/oro-hoy", "Sat, 24 Oct 2026 12:00:00 GMT"),
        _item("El Oro hace 5 días", "https://www.fxstreet.es/news/oro-viejo", "Tue, 20 Oct 2026 10:00:00 GMT"),
        _item("El USD/JPY bajo presión", "https://www.fxstreet.es/news/usdjpy", "Sat, 24 Oct 2026 11:00:00 GMT"),
    )
    inv_rss = _rss(
        _item("Petróleo sube por tensiones geopolíticas", "https://es.investing.com/news/crude", "Sat, 24 Oct 2026 12:00:00 GMT"),
    )

    def fake_leer(url: str) -> str:
        if "investing.com" in url:
            return inv_rss
        return fx_rss

    lista, _ = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert len(lista) == 1
    assert lista[0]["url"] == "https://www.fxstreet.es/news/oro-hoy"
    assert lista[0]["fecha"] >= "2026-10-22"


def test_tope_de_6_candidatas():
    items_fx = [_item(f"Oro noticia FX {i}", f"https://www.fxstreet.es/news/fx-{i}", "Sat, 24 Oct 2026 12:00:00 GMT") for i in range(5)]
    items_inv = [_item(f"Oro noticia Inv {i}", f"https://es.investing.com/news/inv-{i}", "Sat, 24 Oct 2026 12:00:00 GMT") for i in range(5)]
    fx_rss = _rss(*items_fx)
    inv_rss = _rss(*items_inv)

    def fake_leer(url: str) -> str:
        if "investing.com" in url:
            return inv_rss
        return fx_rss

    lista, _ = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert len(lista) == nctx.MAX_CANDIDATAS
    assert nctx.MAX_CANDIDATAS == 6


def test_feed_bloqueado_da_cero_candidatas_y_aviso():
    def fake_leer(url: str) -> str:
        return "<html>blocked</html>"

    lista, avisos = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert lista == []
    assert len(avisos) > 0
    assert all(isinstance(a, str) and a.strip() for a in avisos)


def test_un_feed_caido_no_bota_al_otro():
    fx_rss = _rss(
        _item("El Oro se sostiene sobre soporte", "https://www.fxstreet.es/news/oro-soporte", "Sat, 24 Oct 2026 12:00:00 GMT"),
    )

    def fake_leer(url: str) -> str:
        if "investing.com" in url:
            raise OSError("Investing caído")
        return fx_rss

    lista, avisos = nctx.candidatas("XAUUSD", "Oro", AHORA, leer=fake_leer)
    assert len(lista) == 1
    assert lista[0]["medio"] == "FXStreet"
    assert any("investing" in a.lower() for a in avisos)


def test_lee_la_fecha_de_los_feeds_de_noticias_de_investing():
    """Investing escribe «2026-10-24 14:33:13» (UTC) y no el formato del RSS: se botaban todas sus notas."""
    inv_rss = _rss(
        _item("Futuros de la plata en canal bajista", "https://es.investing.com/news/commodities-news/plata-1",
              "2026-10-24 14:33:13"),
    )

    def fake_leer(url: str) -> str:
        return inv_rss if "investing.com" in url else _rss()

    lista, avisos = nctx.candidatas("XAGUSD", "Plata", AHORA, leer=fake_leer)
    assert [c["url"] for c in lista] == ["https://es.investing.com/news/commodities-news/plata-1"]
    assert lista[0]["medio"] == "Investing.com" and lista[0]["fecha"] == "2026-10-24"
    assert avisos == []


def test_investing_incluye_el_feed_de_commodities():
    assert "https://es.investing.com/rss/news_11.rss" in nctx.FEEDS_INVESTING
