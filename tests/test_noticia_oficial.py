"""La noticia de fuente oficial que suplementa a un canal vacio.

**Oficial no es relevante, y la medicion del 2026-09-03 lo demuestra.** Ese dia
la EIA publico "Weekly average load in ERCOT continues near record high": carga
electrica en Texas, fresca, oficial, y sin ninguna relacion con el petroleo. Un
filtro de frescura sin filtro de relevancia la habria mandado al canal de
metales y energia justo el dia en que ese canal necesitaba suplemento.

Por eso el nucleo de este modulo no es descargar: es DESCARTAR.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for _p in (RAIZ / "scripts", RAIZ / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import noticia_oficial as no  # noqa: E402
import suplemento_canal as sup  # noqa: E402

EST = timezone(timedelta(hours=-5))

# El feed real de la EIA, recortado. Se conservan los tres casos que importan:
# la nota de hoy que NO es relevante, una relevante reciente, y una relevante
# vieja. El doble espacio en la fecha del tercer item esta en el feed real.
FEED_EIA = """<?xml version="1.0" encoding="ISO-8859-1" ?>
<rss version="2.0"><channel>
<title>Today in Energy</title>
<item>
<title>Weekly average load in ERCOT continues near record high</title>
<link>https://www.eia.gov/todayinenergy/detail.php?id=68084</link>
<pubDate>Thu, 03 Sep 2026 09:00:00 EST</pubDate>
<description>Sustained high temperatures have contributed to persistently high
electricity demand in the Electric Reliability Council of Texas.</description>
</item>
<item>
<title>Longer wells boost Permian crude oil and natural gas production</title>
<link>https://www.eia.gov/todayinenergy/detail.php?id=68000</link>
<pubDate>Tue, 01 Sep 2026 09:00:00 EST</pubDate>
<description>Horizontal wells in the Permian Basin got longer.</description>
</item>
<item>
<title>Dangote refinery drives increase in petroleum shipments from Nigeria</title>
<link>https://www.eia.gov/todayinenergy/detail.php?id=67900</link>
<pubDate>Mon, 24 Aug 2026  09:00:00 EST</pubDate>
<description>Shipments rose.</description>
</item>
</channel></rss>"""

AHORA = datetime(2026, 9, 3, 12, 0, tzinfo=EST)


def _feed(_url: str) -> str:
    return FEED_EIA


def _sin_red(_url: str) -> str:
    raise OSError("la red no respondio")


# ─────────────────────────────────────────────────────────────────────────────
# Leer el feed
# ─────────────────────────────────────────────────────────────────────────────
def test_el_feed_se_lee_con_titulo_link_y_fecha():
    items = no.parsear_feed(FEED_EIA)
    assert len(items) == 3
    primero = items[0]
    assert primero["titulo"].startswith("Weekly average load in ERCOT")
    assert primero["url"] == "https://www.eia.gov/todayinenergy/detail.php?id=68084"
    assert primero["fecha"].year == 2026
    assert primero["fecha"].tzinfo is not None


def test_la_fecha_con_doble_espacio_del_feed_real_no_rompe():
    # `Mon, 24 Aug 2026  09:00:00 EST` viene asi en el feed de la EIA.
    items = no.parsear_feed(FEED_EIA)
    assert items[2]["fecha"].day == 24


def test_un_feed_ilegible_no_lanza_devuelve_vacio():
    assert no.parsear_feed("<html>esto no es rss</html>") == []


# ─────────────────────────────────────────────────────────────────────────────
# El filtro que da sentido a todo esto
# ─────────────────────────────────────────────────────────────────────────────
def test_la_nota_de_carga_electrica_no_es_relevante_para_el_petroleo():
    """El caso medido: oficial, fresca, y sin nada que ver con el activo."""
    assert no.activos_del_titular(
        "Weekly average load in ERCOT continues near record high"
    ) == []


def test_una_nota_de_crudo_si_mapea_a_los_activos_de_petroleo():
    activos = no.activos_del_titular(
        "Longer wells boost Permian crude oil and natural gas production"
    )
    assert "WTI" in activos and "BRENT" in activos


def test_el_discurso_de_un_banquero_central_es_relevante_por_quien_habla():
    """En los bancos centrales la relevancia la da el orador, no un commodity."""
    assert no.activos_del_titular(
        "Christine Lagarde: Panel remarks about the European economy"
    )


def test_el_cuerpo_no_alcanza_la_relevancia_se_decide_en_el_titular():
    """Buscar en la descripcion deja pasar cualquier nota con una linea de contexto."""
    items = no.parsear_feed(FEED_EIA)
    ercot = items[0]
    assert "electricity" in ercot["resumen"]
    assert no.activos_del_titular(ercot["titulo"]) == []


# ─────────────────────────────────────────────────────────────────────────────
# Frescura
# ─────────────────────────────────────────────────────────────────────────────
def test_una_nota_vieja_no_es_noticia_por_mas_relevante_que_sea():
    items = no.parsear_feed(FEED_EIA)
    dangote = items[2]                       # 24 de agosto: diez dias atras
    assert no.activos_del_titular(dangote["titulo"])
    assert not no.es_fresca(dangote["fecha"], AHORA)


def test_la_ventana_de_frescura_esta_declarada_y_es_corta():
    assert no.VENTANA_FRESCURA_HORAS <= 72


# ─────────────────────────────────────────────────────────────────────────────
# La eleccion para un canal
# ─────────────────────────────────────────────────────────────────────────────
def test_el_canal_de_energia_recibe_la_nota_de_crudo_y_no_la_de_electricidad():
    n = no.noticia_para_canal(
        "03_commodities_materias_primas", ahora=AHORA, historial=[], descargar=_feed
    )
    assert n is not None
    assert "Permian crude oil" in n["titulo"]
    assert n["organismo"].startswith("EIA")
    assert n["url"].endswith("68000")


def test_un_canal_sin_fuente_declarada_no_recibe_noticia():
    assert no.noticia_para_canal(
        "06_criptoactivos", ahora=AHORA, historial=[], descargar=_feed
    ) is None


def test_una_noticia_ya_publicada_no_se_repite_nunca():
    """El URL no tiene ventana: republicar la misma nota es un error, no un olvido."""
    historial = [{
        "tipo": "noticia",
        "clave": "https://www.eia.gov/todayinenergy/detail.php?id=68000",
        "canal": "03_commodities_materias_primas",
        "fecha": "2026-09-01",
    }]
    assert no.noticia_para_canal(
        "03_commodities_materias_primas", ahora=AHORA, historial=historial,
        descargar=_feed,
    ) is None


def test_si_la_red_falla_no_hay_noticia_y_no_se_cae_la_tanda():
    n = no.noticia_para_canal(
        "03_commodities_materias_primas", ahora=AHORA, historial=[],
        descargar=_sin_red,
    )
    assert n is None


# ─────────────────────────────────────────────────────────────────────────────
# El bloque de texto
# ─────────────────────────────────────────────────────────────────────────────
def _noticia():
    return no.noticia_para_canal(
        "03_commodities_materias_primas", ahora=AHORA, historial=[], descargar=_feed
    )


def test_el_bloque_atribuye_la_fuente_fecha_y_link():
    b = no.bloque_noticia(_noticia(), "Pozos mas largos impulsan la produccion de crudo")
    assert "EIA" in b
    assert "https://www.eia.gov/todayinenergy/detail.php?id=68000" in b
    assert "septiembre" in b.lower()


def test_el_bloque_publica_el_titular_en_espanol_no_el_original_en_ingles():
    b = no.bloque_noticia(_noticia(), "Pozos mas largos impulsan la produccion de crudo")
    assert "Pozos mas largos" in b
    assert "Longer wells" not in b


def test_sin_titular_en_espanol_el_bloque_se_niega_a_existir():
    """Mismo contrato que el resto del pipeline: un campo editorial vacio detiene."""
    with pytest.raises(ValueError):
        no.bloque_noticia(_noticia(), "")


def test_el_bloque_no_trae_precios_la_regla_1_manda():
    b = no.bloque_noticia(_noticia(), "Pozos mas largos impulsan la produccion")
    assert "$" not in b


def test_el_bloque_no_usa_guion_largo():
    b = no.bloque_noticia(_noticia(), "Pozos mas largos impulsan la produccion")
    assert "—" not in b and "–" not in b


# ─────────────────────────────────────────────────────────────────────────────
# Contratos de nombres: el defecto recurrente del repo
# ─────────────────────────────────────────────────────────────────────────────
def test_todo_canal_de_una_fuente_existe_en_el_mapa_de_canales():
    for nombre, fuente in no.FUENTES.items():
        for canal in fuente["canales"]:
            assert canal in sup.NOMBRE_CANAL, f"{nombre} apunta a un canal inexistente"


def test_todo_activo_del_vocabulario_existe_en_el_catalogo():
    catalogo = json.loads(
        (RAIZ / "config" / "activos.json").read_text(encoding="utf-8")
    )
    tickers: set[str] = set()

    def _recorrer(nodo):
        if isinstance(nodo, dict):
            if "ticker_mt5" in nodo:
                tickers.add(str(nodo.get("ticker") or ""))
                tickers.add(str(nodo["ticker_mt5"]).replace(".spot", ""))
            for v in nodo.values():
                _recorrer(v)
        elif isinstance(nodo, list):
            for v in nodo:
                _recorrer(v)

    _recorrer(catalogo)
    for activo in no.VOCABULARIO:
        assert activo in tickers, f"{activo} no esta en config/activos.json"


def test_todo_activo_del_vocabulario_llega_a_algun_canal():
    """Un activo sin canal es vocabulario muerto: nunca se publicaria."""
    con_canal = {a for f in no.FUENTES.values() for a in f["activos"]}
    assert set(no.VOCABULARIO) == con_canal


# ─────────────────────────────────────────────────────────────────────────────
# Integración con el pipeline
# ─────────────────────────────────────────────────────────────────────────────
def test_una_sola_descarga_por_feed_aunque_lo_pidan_varios_canales():
    """Cinco canales por tres fuentes son quince descargas, y bloquean el prepare.

    El feed de la Fed sirve a divisas y a índices: sin caché se baja dos veces.
    """
    pedidos: list[str] = []

    def _contar(url: str) -> str:
        pedidos.append(url)
        return FEED_EIA

    bajar = no.descargar_con_cache(_contar)
    for canal in ("02_forex_divisas", "04_indices_bursatiles"):
        no.noticia_para_canal(canal, ahora=AHORA, historial=[], descargar=bajar)
    assert len(pedidos) == len(set(pedidos))


def test_el_pipeline_escribe_la_noticia_en_su_json_y_la_registra(tmp_path):
    """`--preparar` no traduce, así que deja el candidato y el comando lo redacta."""
    import pipeline_carrusel as pc

    historial = tmp_path / "historial.json"
    historial.write_text("[]", encoding="utf-8")

    excluidos = [{
        "ticker": "WTI", "nombre": "Petróleo WTI", "clase": "commodities",
        "excluido": "ATR diario consumido al 140%",
    }]
    pc.escribir_suplementos(
        tmp_path, excluidos, set(), {}, ruta_historial=historial,
        buscar_noticia=lambda canal: no.noticia_para_canal(
            canal, ahora=AHORA, historial=[], descargar=_feed
        ),
    )

    ruta = tmp_path / "03_commodities_materias_primas" / "_noticia.json"
    assert ruta.exists(), "el candidato tiene que quedar en disco para el comando"
    guardado = json.loads(ruta.read_text(encoding="utf-8"))
    assert "Permian crude oil" in guardado["titulo"]

    anotado = json.loads(historial.read_text(encoding="utf-8"))
    assert any(e["tipo"] == "noticia" and e["clave"] == guardado["url"] for e in anotado)


def test_sin_noticia_el_canal_conserva_su_suplemento_de_estado(tmp_path):
    """La noticia es aditiva: si no hay, el piso confiable sigue en pie."""
    import pipeline_carrusel as pc

    excluidos = [{
        "ticker": "WTI", "nombre": "Petróleo WTI", "clase": "commodities",
        "excluido": "ATR diario consumido al 140%",
    }]
    pc.escribir_suplementos(
        tmp_path, excluidos, set(), {},
        ruta_historial=tmp_path / "h.json",
        buscar_noticia=lambda _canal: None,
    )
    carpeta = tmp_path / "03_commodities_materias_primas"
    assert (carpeta / "0_suplemento.txt").exists()
    assert not (carpeta / "_noticia.json").exists()
