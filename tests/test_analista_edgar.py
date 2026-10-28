"""Pruebas del lector EDGAR 8-K (spec 2026-10-28, Task 2)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from analista.edgar import (  # noqa: E402
    ENV_CONTACTO,
    ITEMS,
    PRIORIDAD_ITEMS,
    candidatas_8k,
    construir_pedido,
    parsear_8k,
    titular_de,
)

FIXTURE_8K = RAIZ / "tests" / "fixtures" / "edgar_gs_8k.atom"


def test_constantes_declaradas():
    assert ENV_CONTACTO == "GI_EDGAR_CONTACTO"
    assert ITEMS["2.02"] == "Resultados del trimestre"
    assert ITEMS["5.02"] == "Cambios en la directiva"
    assert PRIORIDAD_ITEMS == ["2.02", "5.02", "1.01", "2.01", "7.01", "8.01"]


def test_parsear_extrae_fecha_url_e_items():
    xml = FIXTURE_8K.read_text(encoding="utf-8")
    entradas = parsear_8k(xml)
    assert len(entradas) >= 5

    primera = entradas[0]
    assert isinstance(primera["fecha"], datetime)
    assert primera["fecha"].tzinfo is not None
    assert primera["fecha"].strftime("%Y-%m-%d") == "2026-10-13"
    assert primera["url"].startswith("https://www.sec.gov/Archives/edgar/data/")
    assert "2.02" in primera["items"]
    assert "7.01" in primera["items"]
    assert "9.01" in primera["items"]


def test_titular_usa_el_item_de_mayor_prioridad():
    assert titular_de(["9.01", "2.02"]) == "Resultados del trimestre"
    assert titular_de(["8.01", "5.02"]) == "Cambios en la directiva"
    assert titular_de(["1.01", "7.01"]) == "Acuerdo relevante"


def test_8k_sin_items_publicables_no_genera_candidata():
    assert titular_de(["9.01"]) is None
    assert titular_de(["3.03", "5.03"]) is None
    assert titular_de([]) is None


def test_candidatas_dentro_de_45_dias(monkeypatch):
    monkeypatch.setenv(ENV_CONTACTO, "test@example.com")
    xml = FIXTURE_8K.read_text(encoding="utf-8")

    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    candidatas, aviso = candidatas_8k(
        cik="0000886982",
        organismo="Goldman Sachs",
        ahora=ahora,
        descargar=lambda _url: xml,
        ventana_dias=45,
    )

    assert aviso is None
    assert len(candidatas) == 1
    c = candidatas[0]
    assert c["escalon"] == "oficial"
    assert c["fecha"] == "2026-10-13"
    assert c["medio"] == "SEC EDGAR"
    assert c["organismo"] == "Goldman Sachs"
    assert c["titular_es"] == "Resultados del trimestre"
    assert c["titular_original"] == "Resultados del trimestre"
    assert c["url"].startswith("https://www.sec.gov/")

    # Si ahora es 2026-12-30 (78 días después del 13-10), no entra ninguna
    ahora_lejos = datetime(2026, 12, 30, 12, 0, tzinfo=timezone.utc)
    candidatas_lejos, aviso_lejos = candidatas_8k(
        cik="0000886982",
        organismo="Goldman Sachs",
        ahora=ahora_lejos,
        descargar=lambda _url: xml,
        ventana_dias=45,
    )
    assert candidatas_lejos == []
    assert aviso_lejos is None


def _feed_sintetico(fecha_iso: str, items_str: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <updated>{fecha_iso}</updated>
    <link href="https://www.sec.gov/test-8k" rel="alternate" />
    <summary type="html">&lt;b&gt;Filed:&lt;/b&gt; 2026-09-13&lt;br&gt;{items_str}</summary>
  </entry>
</feed>"""


def test_borde_de_ventana(monkeypatch):
    monkeypatch.setenv(ENV_CONTACTO, "test@example.com")
    ahora = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)

    # Exactamente a 45 días
    fecha_45 = (ahora - timedelta(days=45)).isoformat()
    feed_45 = _feed_sintetico(fecha_45, "Item 2.02: Results of Operations")
    cands_45, aviso_45 = candidatas_8k(
        "0000886982", "Goldman Sachs", ahora, descargar=lambda _: feed_45, ventana_dias=45
    )
    assert aviso_45 is None
    assert len(cands_45) == 1

    # A 46 días (fuera de ventana)
    fecha_46 = (ahora - timedelta(days=46)).isoformat()
    feed_46 = _feed_sintetico(fecha_46, "Item 2.02: Results of Operations")
    cands_46, aviso_46 = candidatas_8k(
        "0000886982", "Goldman Sachs", ahora, descargar=lambda _: feed_46, ventana_dias=45
    )
    assert aviso_46 is None
    assert len(cands_46) == 0


def test_sin_contacto_avisa_y_no_consulta(monkeypatch):
    monkeypatch.delenv(ENV_CONTACTO, raising=False)
    descargado = False

    def descargar_espia(_url: str) -> str:
        nonlocal descargado
        descargado = True
        return ""

    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    candidatas, aviso = candidatas_8k(
        "0000886982", "Goldman Sachs", ahora, descargar=descargar_espia
    )

    assert candidatas == []
    assert aviso is not None
    assert ENV_CONTACTO in aviso
    assert not descargado


def test_feed_roto_no_lanza(monkeypatch):
    monkeypatch.setenv(ENV_CONTACTO, "test@example.com")
    ahora = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)

    # 1. Contenido no Atom / 403
    cands_403, aviso_403 = candidatas_8k(
        "0000886982", "Goldman Sachs", ahora, descargar=lambda _: "<html>403</html>"
    )
    assert cands_403 == []
    assert aviso_403 is not None
    assert "Error consultando EDGAR para Goldman Sachs" in aviso_403

    # 2. OSError / fallo de red
    def descargar_error(_url: str) -> str:
        raise OSError("Connection refused")

    cands_err, aviso_err = candidatas_8k(
        "0000886982", "Goldman Sachs", ahora, descargar=descargar_error
    )
    assert cands_err == []
    assert aviso_err is not None
    assert "Error consultando EDGAR para Goldman Sachs" in aviso_err


def test_entry_con_fecha_mala_se_ignora():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <updated>FECHA_INVALIDA_XYZ</updated>
    <link href="https://www.sec.gov/test-1" rel="alternate" />
    <summary type="html">Item 2.02: Results</summary>
  </entry>
  <entry>
    <updated>2026-10-13T07:32:56-04:00</updated>
    <link href="https://www.sec.gov/test-2" rel="alternate" />
    <summary type="html">Item 5.02: Departure of Directors</summary>
  </entry>
</feed>"""
    entradas = parsear_8k(xml)
    assert len(entradas) == 1
    assert entradas[0]["items"] == ["5.02"]
    assert entradas[0]["url"] == "https://www.sec.gov/test-2"


def test_user_agent_lleva_el_contacto():
    req = construir_pedido("https://www.sec.gov/test", "test@example.com")
    ua = req.get_header("User-agent")
    assert ua is not None
    assert "test@example.com" in ua
    assert ua.startswith("GrupoInteligencia/1.0")
