"""Pruebas del resolutor de fuentes oficiales por activo (spec 2026-10-28, Task 1)."""
from __future__ import annotations

import email.utils
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import noticia_oficial  # noqa: E402
from analista.oficial import VENTANA_OFICIAL_DIAS, candidatas, fuente_de, piso  # noqa: E402


def test_ventana_oficial_son_45_dias():
    assert VENTANA_OFICIAL_DIAS == 45


def test_accion_resuelve_por_su_ancla():
    assert fuente_de("#GS") == {
        "organismo": "Goldman Sachs",
        "pagina_prensa": "https://www.goldmansachs.com/investor-relations/",
        "lector": "edgar_8k",
        "cik": "0000886982",
    }


def test_feed_oficial_por_activo_con_sufijo():
    f_wti = fuente_de("WTI.spot")
    assert f_wti is not None
    assert f_wti["lector"] == "feed_oficial"
    assert f_wti["fuente"] == "eia"

    f_usdclp = fuente_de("USDCLP")
    assert f_usdclp is not None
    assert f_usdclp["fuente"] == "fed"


def test_activo_sin_fuente():
    assert fuente_de("BTCUSD") is None
    assert piso("COPPER") is None


def test_piso_trae_organismo_y_enlace_https():
    p = piso("#GS")
    assert p is not None
    assert p["organismo"] == "Goldman Sachs"
    assert p["pagina_prensa"].startswith("https://")


def test_toda_fuente_de_feeds_tiene_pagina_prensa():
    assert len(noticia_oficial.FUENTES) >= 3
    for nombre, datos in noticia_oficial.FUENTES.items():
        assert "pagina_prensa" in datos, f"Falta pagina_prensa en {nombre}"
        assert isinstance(datos["pagina_prensa"], str), f"pagina_prensa no es str en {nombre}"
        assert datos["pagina_prensa"].startswith("https://"), (
            f"pagina_prensa en {nombre} debe empezar con https://: {datos['pagina_prensa']}"
        )


def test_feed_oficial_filtra_por_relevancia_del_titular():
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    feed_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Permian Basin crude oil production increases</title>
    <link>https://www.eia.gov/petroleo-1</link>
    <pubDate>{email.utils.format_datetime(ahora - timedelta(days=2))}</pubDate>
  </item>
  <item>
    <title>Federal Reserve announces enforcement actions and banking sanctions</title>
    <link>https://www.eia.gov/sanciones-2</link>
    <pubDate>{email.utils.format_datetime(ahora - timedelta(days=1))}</pubDate>
  </item>
</channel></rss>"""
    candidatas_res, aviso = candidatas("WTI.spot", ahora, descargar=lambda _: feed_xml)
    assert aviso is None
    assert len(candidatas_res) == 1
    assert candidatas_res[0]["titular_original"] == "Permian Basin crude oil production increases"
    assert candidatas_res[0]["medio"] == "EIA"
    assert candidatas_res[0]["escalon"] == "oficial"


def test_feed_oficial_usa_45_dias():
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    feed_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Crude oil refinery capacity report</title>
    <link>https://www.eia.gov/nota-30-dias</link>
    <pubDate>{email.utils.format_datetime(ahora - timedelta(days=30))}</pubDate>
  </item>
  <item>
    <title>Petroleum market outlook analysis</title>
    <link>https://www.eia.gov/nota-50-dias</link>
    <pubDate>{email.utils.format_datetime(ahora - timedelta(days=50))}</pubDate>
  </item>
</channel></rss>"""
    candidatas_res, aviso = candidatas("WTI.spot", ahora, descargar=lambda _: feed_xml)
    assert aviso is None
    assert len(candidatas_res) == 1
    assert candidatas_res[0]["url"] == "https://www.eia.gov/nota-30-dias"


def test_candidatas_despacha_a_edgar_para_acciones(monkeypatch):
    monkeypatch.setenv("GI_EDGAR_CONTACTO", "test@example.com")
    fixture_8k = RAIZ / "tests" / "fixtures" / "edgar_gs_8k.atom"
    xml_8k = fixture_8k.read_text(encoding="utf-8")
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)

    candidatas_res, aviso = candidatas("#GS", ahora, descargar=lambda _: xml_8k)
    assert aviso is None
    assert len(candidatas_res) >= 1
    c = candidatas_res[0]
    assert c["escalon"] == "oficial"
    assert c["organismo"] == "Goldman Sachs"
    assert c["medio"] == "SEC EDGAR"


def test_activo_sin_fuente_devuelve_vacio_sin_aviso():
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    assert candidatas("BTCUSD", ahora) == ([], None)


def test_feed_caido_da_aviso():
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)

    def descargar_error(_url: str) -> str:
        raise OSError("feed no disponible")

    candidatas_res, aviso = candidatas("WTI.spot", ahora, descargar=descargar_error)
    assert candidatas_res == []
    assert aviso is not None
    assert "Error consultando feed eia" in aviso

