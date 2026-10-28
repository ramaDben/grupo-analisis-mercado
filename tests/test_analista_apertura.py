"""La noticia de apertura baja por escalones: el activo, el sector y el evento de la semana (spec 2026-10-27)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import apertura as ap  # noqa: E402
from analista import noticia as nt  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 27, 11, 40, tzinfo=SANTIAGO)
HOY = AHORA.date()


def _item(titulo, url, pub="Tue, 27 Oct 2026 12:00:00 GMT"):
    return f"<item><title><![CDATA[{titulo}]]></title><link>{url}</link><pubDate>{pub}</pubDate></item>"


def _rss(*items):
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{"".join(items)}</channel></rss>'


VACIO = _rss()
NOTA_GS = "https://www.fxstreet.es/news/goldman-sachs-resultados-202610271200"
NOTA_BANCA = "https://es.investing.com/news/stock-market-news/los-bancos-de-wall-street-suben-3001"
NOTA_CENTRALES = "https://es.investing.com/news/economy/bancos-centrales-en-la-mira-3002"
NOTA_OFICIAL = "https://www.sec.gov/Archives/edgar/data/886982/000088698226000529/0000886982-26-000529-index.htm"


def _lector(fx=VACIO, investing=VACIO):
    def leer(url):
        return fx if url in nt.FEEDS_FX else investing
    return leer


def _sectores(tmp_path):
    ruta = tmp_path / "sectores.json"
    ruta.write_text(json.dumps({"sectores": {"banca_eeuu": {
        "nombre": "la banca de EE.UU.", "tickers": ["#GS", "#JPM"],
        "patrones": [r"\bbancos?\b(?!\s+centrales?)", "JPMorgan"]}}}), encoding="utf-8")
    return ruta



@pytest.fixture(autouse=True)
def _aislar_oficial_en_tests_antiguos(monkeypatch):
    if hasattr(ap.candidatas, "__defaults__") and ap.candidatas.__defaults__:
        defaults = list(ap.candidatas.__defaults__)
        defaults[-1] = lambda t, a: ([], None)
        monkeypatch.setattr(ap.candidatas, "__defaults__", tuple(defaults))


# ── Escalones 1 y 2: candidatas ──

def test_escalon_1_la_nota_del_activo_gana_y_suma_investing(tmp_path):
    fx = _rss(_item("Goldman Sachs supera las previsiones", NOTA_GS))
    inv = _rss(_item("Los bancos de Wall Street suben", NOTA_BANCA))
    lista, aviso = ap.candidatas("#GS", "Goldman Sachs", AHORA, leer=_lector(fx, inv), ruta_sectores=_sectores(tmp_path))
    assert [c["url"] for c in lista] == [NOTA_GS]
    assert lista[0]["escalon"] == "activo" and aviso is None


def test_escalon_1_tambien_lee_investing(tmp_path):
    inv = _rss(_item("Goldman Sachs eleva su dividendo", "https://es.investing.com/news/stock-market-news/gs-3003"))
    lista, _ = ap.candidatas("#GS", "Goldman Sachs", AHORA, leer=_lector(investing=inv), ruta_sectores=_sectores(tmp_path))
    assert lista[0]["medio"] == "Investing.com" and lista[0]["escalon"] == "activo"


def test_escalon_2_sin_nota_del_activo_baja_al_sector(tmp_path):
    inv = _rss(_item("Los bancos de Wall Street suben antes de la Fed", NOTA_BANCA),
               _item("Los bancos centrales en la mira", NOTA_CENTRALES))
    lista, aviso = ap.candidatas("#GS", "Goldman Sachs", AHORA, leer=_lector(investing=inv), ruta_sectores=_sectores(tmp_path))
    # «bancos centrales» no es la banca: el patrón lo excluye
    assert [c["url"] for c in lista] == [NOTA_BANCA]
    assert lista[0]["escalon"] == "sector" and lista[0]["sector"] == "la banca de EE.UU."
    assert aviso is None


def test_un_activo_sin_sector_no_baja_al_sector(tmp_path):
    inv = _rss(_item("Los bancos de Wall Street suben", NOTA_BANCA))
    lista, _ = ap.candidatas("XAUUSD", "Oro", AHORA, leer=_lector(investing=inv), ruta_sectores=_sectores(tmp_path))
    assert lista == []


def test_medios_caidos_avisan_sin_botar_la_pieza(tmp_path):
    def caido(url):
        raise OSError("sin red")
    lista, aviso = ap.candidatas("#GS", "Goldman Sachs", AHORA, leer=caido, ruta_sectores=_sectores(tmp_path))
    assert lista == [] and "FXStreet" in aviso and "Investing.com" in aviso


def test_el_config_real_declara_los_bancos_de_eeuu():
    datos = json.loads(ap.RUTA_SECTORES.read_text(encoding="utf-8"))
    assert "#GS" in {t for s in datos["sectores"].values() for t in s["tickers"]}


def test_el_patron_de_banca_del_config_real_no_toma_los_bancos_centrales():
    pats = ap.patrones_sector("#GS")[1]
    assert any(p.search("Los bancos de Wall Street suben") for p in pats)
    assert any(p.search("Los grandes bancos ganan más de lo esperado") for p in pats)
    for ajeno in ("Los bancos centrales recortan tasas",
                  "Banco de Canadá: Los precios más altos del petróleo respaldan una subida de tipos",
                  "La banca central de Japón mantiene su política"):
        assert not any(p.search(ajeno) for p in pats), ajeno


# ── Escalón 3: el evento central de la semana ──

def _ev(fuente, fecha, hora, pais="EE.UU.", **k):
    return {"fecha": fecha, "dia": "x", "hora": hora, "evento": fuente, "fuente_nombre": fuente, "pais": pais,
            "anterior": k.get("anterior", "4,00 por ciento"), "esperado": k.get("esperado", "4,00 por ciento"),
            "mueve_al_activo": k.get("mueve", False)}


def test_escalon_3_la_decision_de_la_fed_gana_a_los_datos():
    eventos = [_ev("CB Consumer Confidence (Oct)", "2026-10-27", "13:00 CLST"),
               _ev("Core PCE Price Index (MoM) (Sep)", "2026-10-29", "09:30 CLST"),
               _ev("ECB Interest Rate Decision (Oct)", "2026-10-29", "10:15 CLST", pais="Zona Euro"),
               _ev("Fed Interest Rate Decision", "2026-10-28", "15:00 CLST")]
    assert ap.evento_central(eventos, "#GS", AHORA)["fuente_nombre"] == "Fed Interest Rate Decision"


def test_escalon_3_un_evento_que_ya_paso_no_abre():
    eventos = [_ev("Fed Interest Rate Decision", "2026-10-27", "09:00 CLST"),
               _ev("Nonfarm Payrolls (Oct)", "2026-10-30", "09:30 CLST")]
    assert ap.evento_central(eventos, "#GS", AHORA)["fuente_nombre"] == "Nonfarm Payrolls (Oct)"


def test_escalon_3_sin_evento_fuerte_no_hay_apertura():
    eventos = [_ev("CB Consumer Confidence (Oct)", "2026-10-28", "11:00 CLST"),
               _ev("Chicago PMI (Oct)", "2026-10-30", "10:45 CLST")]
    assert ap.evento_central(eventos, "#GS", AHORA) is None


def test_escalon_3_el_dolar_peso_mira_al_banco_central_de_chile():
    eventos = [_ev("Fed Interest Rate Decision", "2026-10-29", "15:00 CLST"),
               _ev("Interest Rate Decision", "2026-10-28", "18:00 CLST", pais="Chile")]
    assert ap.evento_central(eventos, "USDCLP", AHORA)["pais"] == "Chile"


def test_escalon_3_una_decision_ajena_no_abre_una_accion_de_eeuu():
    eventos = [_ev("ECB Interest Rate Decision (Oct)", "2026-10-29", "10:15 CLST", pais="Zona Euro")]
    assert ap.evento_central(eventos, "#GS", AHORA) is None


# ── El escalón de la noticia elegida ──

def test_el_escalon_sale_de_la_candidata_elegida():
    datos = {"noticias_candidatas": [{"url": NOTA_BANCA, "escalon": "sector", "sector": "la banca de EE.UU."}]}
    assert ap.escalon_de({"url": NOTA_BANCA}, datos) == "sector"
    assert ap.escalon_de({"url": NOTA_GS}, datos) == "activo"   # buscada en la web por agy: es del activo
    assert ap.escalon_de({"escalon": "agenda"}, datos) == "agenda"

# ── Escalón 0: candidatas oficiales ──

def test_oficial_gana_sobre_los_demas_escalones(tmp_path):
    candidata_oficial = {
        "medio": "SEC EDGAR",
        "fecha": "2026-10-13",
        "url": NOTA_OFICIAL,
        "titular_original": "Resultados del trimestre",
        "titular_es": "Resultados del trimestre",
        "escalon": "oficial",
        "organismo": "Goldman Sachs",
    }
    fx = _rss(_item("Goldman Sachs supera las previsiones", NOTA_GS))
    lista, aviso = ap.candidatas(
        "#GS",
        "Goldman Sachs",
        AHORA,
        leer=_lector(fx),
        ruta_sectores=_sectores(tmp_path),
        oficial_fn=lambda t, a: ([candidata_oficial], None),
    )
    assert len(lista) == 1
    assert [c["url"] for c in lista] == [NOTA_OFICIAL]
    assert lista[0]["escalon"] == "oficial"
    assert aviso is None


def test_sin_oficial_cae_al_escalon_1(tmp_path):
    fx = _rss(_item("Goldman Sachs supera las previsiones", NOTA_GS))
    lista, aviso = ap.candidatas(
        "#GS",
        "Goldman Sachs",
        AHORA,
        leer=_lector(fx),
        ruta_sectores=_sectores(tmp_path),
        oficial_fn=lambda t, a: ([], None),
    )
    assert [c["url"] for c in lista] == [NOTA_GS]
    assert lista[0]["escalon"] == "activo"
    assert aviso is None


def test_aviso_del_escalon_0_se_conserva(tmp_path):
    fx = _rss(_item("Goldman Sachs supera las previsiones", NOTA_GS))
    lista, aviso = ap.candidatas(
        "#GS",
        "Goldman Sachs",
        AHORA,
        leer=_lector(fx),
        ruta_sectores=_sectores(tmp_path),
        oficial_fn=lambda t, a: ([], "EDGAR no respondió"),
    )
    assert [c["url"] for c in lista] == [NOTA_GS]
    assert lista[0]["escalon"] == "activo"
    assert aviso is not None and "EDGAR no respondió" in aviso


def test_oficial_que_lanza_no_rompe(tmp_path):
    def falla(ticker, ahora):
        raise RuntimeError("falla simulada de EDGAR")

    fx = _rss(_item("Goldman Sachs supera las previsiones", NOTA_GS))
    lista, aviso = ap.candidatas(
        "#GS",
        "Goldman Sachs",
        AHORA,
        leer=_lector(fx),
        ruta_sectores=_sectores(tmp_path),
        oficial_fn=falla,
    )
    assert [c["url"] for c in lista] == [NOTA_GS]
    assert lista[0]["escalon"] == "activo"
    assert aviso is not None and "falla simulada de EDGAR" in aviso


def test_escalon_de_reconoce_oficial():
    datos = {"noticias_candidatas": [{"url": NOTA_OFICIAL, "escalon": "oficial"}]}
    assert ap.escalon_de({"url": NOTA_OFICIAL}, datos) == "oficial"
    assert ap.escalon_de({"escalon": "oficial"}, {}) == "oficial"



# ── Depuración del escalón 3 ──

EVENTO = _ev("Fed Interest Rate Decision", "2026-10-28", "15:00 CLST")
EVENTO["evento"] = "Comité de mercado abierto de la Fed"


def _agenda(**cambios):
    n = {"escalon": "agenda", "titular": "La Fed decide sus tasas y la banca la mira de cerca",
         "bajada": "El mercado aguarda la decisión del miércoles, que define el costo del crédito para los bancos.",
         "motivo": "banco_central"}
    n.update(cambios)
    return {"editorial": {"noticia": n}, "datos": {"evento_apertura": EVENTO, "noticias_candidatas": []}}


def test_la_apertura_de_agenda_valida_pasa_y_lleva_el_evento():
    pieza, desc = nt.depurar_noticia(_agenda(), HOY)
    n = pieza["editorial"]["noticia"]
    assert desc == [] and n["escalon"] == "agenda" and n["evento"]["fuente_nombre"] == "Fed Interest Rate Decision"


def test_la_apertura_de_agenda_no_lleva_cifras():
    pieza, desc = nt.depurar_noticia(_agenda(titular="La Fed decidiría dejar la tasa en 4 por ciento"), HOY)
    assert pieza["editorial"]["noticia"] is None and "cifra" in desc[0]


def test_la_apertura_de_agenda_sin_evento_se_descarta():
    p = _agenda()
    p["datos"]["evento_apertura"] = None
    pieza, desc = nt.depurar_noticia(p, HOY)
    assert pieza["editorial"]["noticia"] is None and "evento" in desc[0]


def test_la_apertura_de_agenda_no_cabe_si_hay_notas():
    p = _agenda()
    p["datos"]["noticias_candidatas"] = [{"url": NOTA_BANCA, "escalon": "sector"}]
    pieza, desc = nt.depurar_noticia(p, HOY)
    assert pieza["editorial"]["noticia"] is None and "notas" in desc[0]


def test_la_apertura_de_agenda_pasa_por_los_controles_de_texto():
    pieza, desc = nt.depurar_noticia(_agenda(bajada="El mercado aguarda la decisión — y conviene comprar antes."), HOY)
    assert pieza["editorial"]["noticia"] is None and desc


def test_la_apertura_de_agenda_con_motivo_fuera_de_catalogo_se_descarta():
    pieza, desc = nt.depurar_noticia(_agenda(motivo="foto_de_powell"), HOY)
    assert pieza["editorial"]["noticia"] is None and "catálogo" in desc[0]


# ── Lo que el bot le dice al ejecutivo ──

from analista import bot  # noqa: E402


def _pieza_bot(noticia, candidatas=(), evento=None):
    return {"editorial": {"noticia": noticia},
            "datos": {"noticias_candidatas": list(candidatas), "evento_apertura": evento}}


def test_el_aviso_nombra_el_escalon_del_sector():
    n = {"url": NOTA_BANCA, "titular": "La banca sube antes de la Fed"}
    aviso = bot._aviso_sin_noticia(_pieza_bot(n, [{"url": NOTA_BANCA, "escalon": "sector"}]), [])
    assert "nota del sector" in aviso and "La banca sube" in aviso


def test_el_aviso_nombra_el_evento_de_la_agenda():
    n = {"escalon": "agenda", "titular": "x", "evento": {"evento": "Comité de la Fed", "dia": "miércoles 28/10"}}
    aviso = bot._aviso_sin_noticia(_pieza_bot(n), [])
    assert "evento de la semana" in aviso and "Comité de la Fed" in aviso


def test_la_nota_del_activo_no_se_avisa():
    n = {"url": NOTA_GS, "titular": "x"}
    assert bot._aviso_sin_noticia(_pieza_bot(n, [{"url": NOTA_GS, "escalon": "activo"}]), []) is None


def test_sin_nada_el_aviso_dice_que_busco_en_los_tres_escalones():
    aviso = bot._aviso_sin_noticia(_pieza_bot(None), [])
    assert "ni de su sector" in aviso and "agenda" in aviso


def test_el_reuso_caduca_cuando_ya_ocurrio_el_evento_que_abre():
    n = {"escalon": "agenda", "evento": {"fecha": "2026-10-27", "hora": "15:00 CLST"}}
    pieza = {"editorial": {"noticia": n}, "datos": {"agenda": {"eventos": []}}}
    assert bot._agenda_pasada(pieza, datetime(2026, 10, 27, 14, 0, tzinfo=SANTIAGO)) is None
    assert "evento" in bot._agenda_pasada(pieza, datetime(2026, 10, 27, 15, 30, tzinfo=SANTIAGO))
