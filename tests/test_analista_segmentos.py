"""Config de segmentos, resolver de ancla y consultas (spec 2026-10-20, Task 2)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from datetime import date

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from analista import fuentes as fu  # noqa: E402
from analista import segmentos as sg  # noqa: E402


def test_usdchf_fuera_del_catalogo_se_infiere_fx_con_el_snb():
    segmento, ancla = sg.segmento_y_ancla("USDCHF")
    assert segmento == "fx" and "Banco Nacional Suizo" in ancla["entidades"] and "snb.ch" in ancla["dominios"]


def test_un_par_con_divisa_del_mapa_se_infiere_fx(tmp_path):
    segs = {"fx": {"divisas": {"CHF": {"nombre": "Suiza", "entidades": ["Banco Nacional Suizo"],
                                      "dominios": ["snb.ch"], "terminos_ancla": ["Suiza"]}}}}
    ruta = tmp_path / "activos.json"
    ruta.write_text("{}", encoding="utf-8")
    seg, ancla = sg.segmento_y_ancla("USDCHF", ruta_activos=ruta, segmentos=segs)
    assert seg == "fx" and ancla["dominios"] == ["snb.ch"]
    seg, _ = sg.segmento_y_ancla("CHFUSD", ruta_activos=ruta, segmentos=segs)
    assert seg == "fx"


def test_un_simbolo_que_no_es_un_par_ni_esta_en_el_catalogo_no_tiene_ancla():
    assert sg.segmento_y_ancla("XYZ123") is None and sg.segmento_y_ancla("EURXXX") is None


def test_el_activo_del_catalogo_con_segmento_usa_su_ancla(tmp_path):
    ancla = {"nombre": "Oro", "entidades": ["World Gold Council"], "dominios": ["gold.org"],
             "terminos_ancla": ["oro"]}
    ruta = tmp_path / "activos.json"
    ruta.write_text(json.dumps({"forex_commodities": [{"ticker_mt5": "XAUUSD", "segmento": "commodities",
                                                       "ancla": ancla}],
                                "activos_complementarios": {"x": [{"ticker_mt5": "COPPER", "segmento": "commodities",
                                                                    "ancla": ancla}]}}), encoding="utf-8")
    assert sg.segmento_y_ancla("XAUUSD", ruta_activos=ruta, segmentos={}) == ("commodities", ancla)
    assert sg.segmento_y_ancla("COPPER", ruta_activos=ruta, segmentos={})[0] == "commodities"


def test_las_consultas_salen_del_ancla_y_no_pasan_de_cuatro():
    q = sg.consultas({"nombre": "Suiza", "entidades": ["Banco Nacional Suizo"],
                      "dominios": ["snb.ch", "nzz.ch"], "terminos_ancla": ["Suiza"]})
    assert q[0] == "Banco Nacional Suizo Suiza" and "site:snb.ch Suiza" in q and len(q) <= 4
    muchas = sg.consultas({"nombre": "N", "entidades": list("abcdef"), "dominios": list("uvwxyz"),
                           "terminos_ancla": ["t"]})
    assert len(muchas) == 4


def test_todo_ancla_declarada_esta_dentro_de_la_lista_cerrada_de_su_segmento():
    for ticker, (seg, ancla) in sg.anclas_del_catalogo().items():
        lista = fu.lista_del_segmento(seg)
        nombres = {e for g in lista["entidades"].values() for e in g}
        dominios = {d for ds in lista["medios"].values() for d in ds}
        assert set(ancla["entidades"]) <= nombres, ticker
        assert set(ancla["dominios"]) <= dominios, ticker
        assert ancla["terminos_ancla"] and ancla["nombre"], ticker


def test_toda_divisa_del_config_esta_dentro_de_la_lista_cerrada_de_fx():
    lista = fu.lista_del_segmento("fx")
    nombres = {e for g in lista["entidades"].values() for e in g}
    dominios = {d for ds in lista["medios"].values() for d in ds}
    divisas = fu.cargar_segmentos()["fx"]["divisas"]
    assert set(divisas) >= {"CHF", "JPY", "GBP", "EUR", "CLP"}
    for divisa, ancla in divisas.items():
        assert set(ancla["entidades"]) <= nombres, divisa
        assert set(ancla["dominios"]) <= dominios, divisa
        assert ancla["nombre"] and ancla["terminos_ancla"], divisa
        assert ancla["banco_central"] in ancla["entidades"], divisa


def test_cada_par_fx_del_catalogo_resuelve_a_su_banco_central():
    esperado = {"USDCLP": "Banco Central de Chile", "USDJPY": "Banco de Japón", "EURUSD": "BCE",
                "GBPUSD": "Banco de Inglaterra", "USDCHF": "Banco Nacional Suizo"}
    for ticker, banco in esperado.items():
        segmento, ancla = sg.segmento_y_ancla(ticker)
        assert segmento == "fx" and ancla["banco_central"] == banco and banco in ancla["entidades"], ticker


def test_usdclp_no_pierde_su_cobertura():
    segmento, ancla = sg.segmento_y_ancla("USDCLP")
    nota = {"entidad": "Banco Central de Chile", "url": "https://www.bcentral.cl/contenido/-/detalle/x",
            "tesis": "El peso chileno se apreció tras la reunión."}
    assert fu.fuentes_directas([nota], segmento, ancla) == [nota]
    assert "Fed" not in ancla["entidades"] and "federalreserve.gov" not in ancla["dominios"]


def test_un_par_con_la_misma_divisa_en_las_dos_patas_no_lanza():
    assert sg.segmento_y_ancla("USDUSD") is None


def test_el_aviso_sin_ancla_no_lleva_guion_largo_y_dice_que_no_gasto_cupo():
    t = sg.aviso_sin_ancla("XYZ123")
    assert "XYZ123" in t and "No gasté tu cupo" in t and "—" not in t and "–" not in t


def test_cargar_segmentos_sin_archivo_da_vacio_y_con_json_corrupto_propaga(tmp_path):
    assert fu.cargar_segmentos(tmp_path / "no_existe.json") == {}
    mala = tmp_path / "mala.json"
    mala.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError):
        fu.cargar_segmentos(mala)


def test_el_config_real_declara_las_seis_claves_de_segmento():
    cfg = fu.cargar_segmentos()
    assert set(fu.SEGMENTOS) <= set(cfg) and "divisas" in cfg["fx"]


# ───────────────────────────────────────────── Task 6: commodities
def _nota(entidad, url, tesis):
    return {"entidad": entidad, "url": url, "tesis": tesis}


def test_una_nota_de_la_opep_que_nombra_el_petroleo_es_directa_del_wti_y_no_del_oro():
    nota = _nota("OPEP", "https://www.opec.org/pr-detail/12-oct-2026.html",
                 "La OPEP+ mantiene su producción de petróleo sin cambios.")
    seg, wti = sg.segmento_y_ancla("WTI.spot")
    assert seg == "commodities" and fu.fuentes_directas([nota], seg, wti) == [nota]
    _, oro = sg.segmento_y_ancla("XAUUSD")
    assert fu.fuentes_directas([nota], "commodities", oro) == []


def test_tasas_y_dxy_solos_no_son_directa_del_oro():
    nota = _nota("Fed", "https://www.federalreserve.gov/newsevents/pressreleases/monetary20261008a.htm",
                 "La Fed analiza las tasas reales y el dólar.")
    seg, oro = sg.segmento_y_ancla("XAUUSD")
    assert fu.fuentes_directas([nota], seg, oro) == []
    assert "Fed" not in oro["entidades"] and "federalreserve.gov" not in oro["dominios"]


def test_cada_commodity_del_catalogo_tiene_ancla_con_su_voz_propia():
    esperado = {"XAUUSD": "World Gold Council", "XAGUSD": "World Gold Council", "WTI.spot": "OPEP",
                "BRENT.spot": "OPEP", "COPPER": "Cochilco"}
    for ticker, entidad in esperado.items():
        seg, ancla = sg.segmento_y_ancla(ticker)
        assert seg == "commodities" and entidad in ancla["entidades"], ticker
        assert ancla["nombre"] and ancla["terminos_ancla"], ticker


def test_las_anclas_de_commodities_no_citan_dominios_fuera_de_la_lista_cerrada():
    lista = fu.lista_del_segmento("commodities")
    dominios = {d for ds in lista["medios"].values() for d in ds}
    for ticker in ("XAUUSD", "XAGUSD", "WTI.spot", "BRENT.spot", "COPPER"):
        _, ancla = sg.segmento_y_ancla(ticker)
        assert set(ancla["dominios"]) <= dominios, ticker


# ───────────────────────────────────────────── Task 7: acciones
ACCIONES = ("#AAPL", "#MSFT", "#NVDA", "#AMZN", "#AMD", "#MELI", "#JPM", "#BAC", "#GS", "#MS", "#BA", "#CAT",
            "#GE", "#DE")


def test_las_14_acciones_tienen_ancla_con_ticker_cik_y_sitio_ir():
    for t in ACCIONES:
        seg, ancla = sg.segmento_y_ancla(t)
        assert seg == "acciones", t
        assert ancla["ticker"] == t.lstrip("#") and re.fullmatch(r"\d{10}", ancla["cik"]), t
        assert ancla["sitio_ir"].startswith("https://") and "sec.gov" in ancla["dominios"], t
        assert ancla["nombre"] and ancla["terminos_ancla"] and ancla["entidades"], t
        host = ancla["sitio_ir"].split("/")[2]
        assert any(host == d or host.endswith("." + d) for d in ancla["dominios"]), t


def test_las_anclas_de_acciones_no_citan_dominios_ni_entidades_fuera_de_la_lista_cerrada():
    lista = fu.lista_del_segmento("acciones")
    dominios = {d for ds in lista["medios"].values() for d in ds}
    entidades = {e for g in lista["entidades"].values() for e in g}
    for t in ACCIONES:
        _, ancla = sg.segmento_y_ancla(t)
        assert set(ancla["dominios"]) <= dominios, t
        assert set(ancla["entidades"]) <= entidades, t


def test_la_fecha_de_earnings_solo_no_habilita_la_publicacion():
    seg, apple = sg.segmento_y_ancla("#AAPL")
    # Solo "Apple reportara el jueves", de un medio, sin comunicado de la empresa: no pasa.
    medio = _nota("Reuters", "https://www.reuters.com/markets/apple-reportara-resultados-2026-10-29/",
                  "Apple reportará sus resultados el jueves.")
    assert fu.fuentes_directas([medio], seg, apple) == []
    # Entidad del ancla, pero la nota no nombra ningun termino: no pasa.
    sin_termino = _nota("Apple", "https://investor.apple.com/newsroom/2026/10/resultados.html",
                        "La empresa publicará sus cifras.")
    assert fu.fuentes_directas([sin_termino], seg, apple) == []
    # Comunicado de investor.apple.com que nombra a Apple: pasa.
    comunicado = _nota("Apple", "https://investor.apple.com/newsroom/2026/10/apple-anuncia-fecha.html",
                       "Apple anuncia la fecha de su conferencia de resultados.")
    assert fu.fuentes_directas([comunicado], seg, apple) == [comunicado]
    # La nota de Apple no sirve de directa para Microsoft.
    _, msft = sg.segmento_y_ancla("#MSFT")
    assert fu.fuentes_directas([comunicado], "acciones", msft) == []


# ───────────────────────────────────────────── Task 8: etfs
ETFS = ("QQQ.US", "SPY.US", "GLD.US", "IWM.US", "SOXX.US")


def test_un_comunicado_del_emisor_fechado_y_con_url_es_directo():
    seg, qqq = sg.segmento_y_ancla("QQQ.US")
    nota = _nota("Invesco", "https://www.invesco.com/qqq-etf/es/about/news/2026-10-qqq-distribucion.html",
                 "Invesco QQQ Trust anuncia su distribucion trimestral.")
    assert seg == "etfs" and fu.fuentes_directas([nota], seg, qqq) == [nota]
    _, iwm = sg.segmento_y_ancla("IWM.US")
    iw = _nota("BlackRock", "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf",
               "iShares Russell 2000 ETF (IWM) actualiza su documento.")
    assert fu.fuentes_directas([iw], "etfs", iwm) == [iw]
    assert fu.fuentes_directas([iw], "etfs", sg.segmento_y_ancla("SOXX.US")[1]) == []


def test_un_titular_generico_del_subyacente_no_es_directo_de_gld():
    seg, gld = sg.segmento_y_ancla("GLD.US")
    generica = _nota("World Gold Council", "https://www.gold.org/goldhub/research/gold-demand-trends-q3-2026",
                     "La demanda de oro de los bancos centrales sube en el tercer trimestre.")
    assert fu.fuentes_directas([generica], seg, gld) == []
    propia = _nota("World Gold Council", "https://www.gold.org/goldhub/data/gold-etfs-holdings-2026",
                   "Las tenencias del fondo GLD suben en octubre.")
    assert fu.fuentes_directas([propia], seg, gld) == [propia]


def test_gld_hereda_los_drivers_del_oro_pero_no_sus_fuentes():
    import analista.hechos as hc

    assert hc.signos("GLD.US") == hc.signos("XAUUSD")
    _, gld = sg.segmento_y_ancla("GLD.US")
    assert "OPEP" not in gld["entidades"] and "LBMA" not in gld["entidades"]
    assert not {"oro", "xau", "onza"} & {t.lower() for t in gld["terminos_ancla"]}
    assert "GLD" in gld["terminos_ancla"]


def test_los_flujos_de_pagina_no_habilitan():
    lista = fu.lista_del_segmento("etfs")
    entidades = {e for g in lista["entidades"].values() for e in g}
    dominios = {d for ds in lista["medios"].values() for d in ds}
    medios_sector = {"etf.com", "etfdb.com", "morningstar.com"}
    for t in ETFS:
        seg, ancla = sg.segmento_y_ancla(t)
        assert seg == "etfs" and ancla["nombre"] and ancla["terminos_ancla"], t
        assert ancla["emisor"] and ancla["indice"] and "subyacente" in ancla, t
        assert set(ancla["entidades"]) <= entidades and set(ancla["dominios"]) <= dominios, t
        assert not medios_sector & set(ancla["dominios"]), t
        # un medio del sector que nombra al fondo NO es fuente directa: solo cuentan el emisor y su dominio
        medio = _nota("Reuters", "https://www.etf.com/sections/features/" + ancla["terminos_ancla"][0].lower(),
                      f"{ancla['terminos_ancla'][0]} registra flujos de entrada.")
        assert fu.fuentes_directas([medio], seg, ancla) == [], t


# ───────────────────────────────────────────── Task 9: indices
INDICES = ("US100.spot", "US500.spot", "US30.spot", "GER40.spot")


def test_cada_indice_tiene_ancla_con_proveedor_y_bolsa_dentro_de_la_lista_cerrada():
    lista = fu.lista_del_segmento("indices")
    entidades = {e for g in lista["entidades"].values() for e in g}
    dominios = {d for ds in lista["medios"].values() for d in ds}
    for t in INDICES:
        seg, ancla = sg.segmento_y_ancla(t)
        assert seg == "indices", t
        assert ancla["nombre"] and ancla["proveedor"] and ancla["bolsa"] and ancla["terminos_ancla"], t
        assert set(ancla["entidades"]) <= entidades and set(ancla["dominios"]) <= dominios, t


def test_los_earnings_de_un_constituyente_no_son_directa_del_indice():
    seg, ndx = sg.segmento_y_ancla("US100.spot")
    apple = _nota("Nasdaq", "https://www.nasdaq.com/articles/apple-resultados-trimestrales",
                  "Apple supera las expectativas de ganancias del trimestre.")
    assert fu.fuentes_directas([apple], seg, ndx) == []
    propia = _nota("Nasdaq", "https://www.nasdaq.com/articles/nasdaq-100-reconstitucion",
                   "El Nasdaq 100 anuncia su reconstitucion anual.")
    assert fu.fuentes_directas([propia], seg, ndx) == [propia]


def test_wall_street_cae_sin_nombrar_el_indice_no_es_directa():
    seg, spx = sg.segmento_y_ancla("US500.spot")
    nota = _nota("NYSE", "https://www.nyse.com/article/wall-street-cae",
                 "Wall Street cae al cierre de la sesion.")
    assert fu.fuentes_directas([nota], seg, spx) == []
    _, dow = sg.segmento_y_ancla("US30.spot")
    assert fu.fuentes_directas([nota], seg, dow) == []
    ok = _nota("S&P Dow Jones Indices", "https://www.spglobal.com/spdji/es/indices/equity/sp-500/",
               "El S&P 500 cambia su metodologia de calculo.")
    assert fu.fuentes_directas([ok], seg, spx) == [ok]
    assert fu.fuentes_directas([ok], seg, dow) == []


def test_un_precio_objetivo_de_un_banco_sobre_el_indice_suma_pero_no_habilita():
    seg, spx = sg.segmento_y_ancla("US500.spot")
    banco = _nota("Goldman Sachs", "https://www.goldmansachs.com/insights/s-p-500-target",
                  "Goldman Sachs sube su precio objetivo del S&P 500.")
    assert fu.fuentes_directas([banco], seg, spx) == []
    assert "Goldman Sachs" not in spx["entidades"] and "goldmansachs.com" not in spx["dominios"]


def test_los_terminos_de_ancla_de_indices_no_son_genericos():
    prohibidos = {"dow", "ndx", "wall street", "nasdaq", "us"}
    for t in INDICES:
        _, ancla = sg.segmento_y_ancla(t)
        assert not prohibidos & {x.lower() for x in ancla["terminos_ancla"]}, t
    assert "DAX" in sg.segmento_y_ancla("GER40.spot")[1]["terminos_ancla"]


# ───────────────────────────────────────────── Task 10: cripto
CRIPTOS = ("BTCUSD", "ETHUSD", "SOLUSD", "LTCUSD", "ADAUSD", "DOGUSD")


def test_la_fundacion_de_la_red_es_directa_de_su_cripto_y_no_de_otra():
    seg, eth = sg.segmento_y_ancla("ETHUSD")
    nota = _nota("Ethereum Foundation", "https://blog.ethereum.org/2026/10/14/protocol-update",
                 "La Ethereum Foundation publica el avance de la proxima actualizacion de Ethereum.")
    assert seg == "cripto" and fu.fuentes_directas([nota], seg, eth) == [nota]
    _, sol = sg.segmento_y_ancla("SOLUSD")
    assert fu.fuentes_directas([nota], seg, sol) == []


def test_cada_cripto_tiene_ancla_dentro_de_la_lista_cerrada_y_sin_terminos_genericos():
    lista = fu.lista_del_segmento("cripto")
    entidades = {e for g in lista["entidades"].values() for e in g}
    dominios = {d for ds in lista["medios"].values() for d in ds}
    prohibidos = {"bitcoin", "btc", "eth", "sol", "ada", "ltc", "doge", "cripto", "crypto", "criptomonedas"}
    for t in CRIPTOS:
        seg, ancla = sg.segmento_y_ancla(t)
        assert seg == "cripto" and ancla["nombre"] and ancla["red"] and "fundacion" in ancla, t
        assert set(ancla["entidades"]) <= entidades and set(ancla["dominios"]) <= dominios, t
        assert not prohibidos & {x.lower() for x in ancla["terminos_ancla"]}, t
        # una bolsa que nombra la cripto no es directa: solo cuentan la fundacion, el emisor y el regulador
        assert not {"Coinbase", "Kraken", "Binance"} & set(ancla["entidades"]), t
        aviso = _nota("Coinbase", "https://www.coinbase.com/blog/listado-de-" + ancla["terminos_ancla"][0].lower(),
                      f"Coinbase anuncia nuevos servicios para {ancla['terminos_ancla'][0]}.")
        assert fu.fuentes_directas([aviso], seg, ancla) == [], t


def test_un_portal_cripto_fuera_de_la_lista_no_cuenta():
    lista = fu.lista_del_segmento("cripto")
    portal = {"entidad": "CoinDesk", "medio": "CoinDesk", "fecha": "2026-10-19", "postura": "neutral",
              "url": "https://www.coindesk.com/markets/2026/10/19/ether-sube/",
              "tesis": "Ether sube en la sesion."}
    validas, descartes = fu.depurar([portal], date(2026, 10, 20), lista=lista, verificar=lambda u: "ok")
    assert validas == [] and "lista de fuentes de prestigio" in descartes[0]


def test_un_blog_de_fundacion_cuenta_solo_con_url_propia_y_fecha():
    lista = fu.lista_del_segmento("cripto")
    base = {"entidad": "Ethereum Foundation", "medio": "Ethereum Foundation", "fecha": "2026-10-19",
            "postura": "neutral", "tesis": "La fundacion detalla la actualizacion de Ethereum.",
            "url": "https://blog.ethereum.org/"}
    validas, descartes = fu.depurar([base], date(2026, 10, 20), lista=lista, verificar=lambda u: "ok")
    assert validas == [] and "portada" in descartes[0]
    ok = {**base, "url": "https://blog.ethereum.org/2026/10/19/actualizacion"}
    validas, _ = fu.depurar([ok], date(2026, 10, 20), lista=lista, verificar=lambda u: "ok")
    assert len(validas) == 1
    viejo = {**ok, "fecha": "2026-08-01"}
    assert fu.depurar([viejo], date(2026, 10, 20), lista=lista, verificar=lambda u: "ok")[0] == []


def test_la_cripto_no_inventa_correlaciones_macro():
    import analista.hechos as hc

    for t in CRIPTOS:
        assert set(hc.signos(t).values()) == {0}, t


# ───────────────────────────────────────────── Task 11: cierre

# DXY (ticker del broker USDIDX) es una referencia del dólar, no un activo publicable. COBRE (COPPER)
# no se excluye: es un commodity y tiene ancla propia.
REFERENCIAS_SIN_VOZ = {"USDIDX"}


def test_todo_activo_del_catalogo_tiene_segmento_y_ancla():
    catalogo = json.loads(sg.ACTIVOS.read_text(encoding="utf-8"))
    tickers = [e["ticker_mt5"] for e in sg._entradas(catalogo)]
    assert tickers
    sin_voz = [t for t in tickers if t not in REFERENCIAS_SIN_VOZ and sg.segmento_y_ancla(t) is None]
    assert sin_voz == [], f"activos del catalogo sin segmento o ancla: {sin_voz}"


# ───────────────────────────────────────────── revisión final: un banco no es directa de su acción


def test_una_nota_de_research_del_banco_no_es_directa_de_su_accion():
    seg, gs = sg.segmento_y_ancla("#GS")
    research = _nota("Goldman Sachs", "https://www.goldmansachs.com/insights/articles/gold-outlook",
                     "Goldman Sachs eleva su objetivo para el oro.")
    assert fu.fuentes_directas([research], seg, gs) == []
    # La misma opinión del banco citada por un medio tampoco: la entidad banco no habilita sola.
    wire = _nota("Goldman Sachs", "https://www.reuters.com/markets/goldman-sachs-eleva-objetivo-oro/",
                 "Goldman Sachs eleva su objetivo para el oro.")
    assert fu.fuentes_directas([wire], seg, gs) == []
    for ticker, entidad, url in (
            ("#MS", "Morgan Stanley", "https://www.morganstanley.com/ideas/perspectivas-2027"),
            ("#BAC", "Bank of America", "https://www.reuters.com/markets/bank-of-america-ve-oro-al-alza/")):
        _, ancla = sg.segmento_y_ancla(ticker)
        nota = _nota(entidad, url, f"{entidad} eleva su objetivo para el oro.")
        assert fu.fuentes_directas([nota], "acciones", ancla) == [], ticker


def test_el_comunicado_propio_del_banco_si_es_directa_de_su_accion():
    seg, gs = sg.segmento_y_ancla("#GS")
    ir = _nota("Goldman Sachs", "https://www.goldmansachs.com/investor-relations/financials/3q26-earnings",
               "Goldman Sachs publica sus resultados del tercer trimestre.")
    sec = _nota("SEC", "https://www.sec.gov/Archives/edgar/data/886982/000088698226000010/gs-10q.htm",
                "Goldman Sachs presenta su informe trimestral 10-Q.")
    assert fu.fuentes_directas([ir, sec], seg, gs) == [ir, sec]
    _, bac = sg.segmento_y_ancla("#BAC")
    propio = _nota("Bank of America", "https://investor.bankofamerica.com/quarterly-earnings/3q26",
                   "Bank of America publica sus resultados del tercer trimestre.")
    assert fu.fuentes_directas([propio], "acciones", bac) == [propio]


def test_el_sitio_de_la_empresa_cuenta_solo_en_sus_rutas_propias():
    _, msft = sg.segmento_y_ancla("#MSFT")
    blog = _nota("Microsoft", "https://www.microsoft.com/en-us/research/blog/microsoft-nuevo-modelo",
                 "Microsoft presenta un nuevo modelo de investigación.")
    assert fu.fuentes_directas([blog], "acciones", msft) == []
    ir = _nota("Microsoft", "https://www.microsoft.com/en-us/investor/earnings/fy-2027-q1/press-release-webcast",
               "Microsoft publica sus resultados del primer trimestre fiscal.")
    assert fu.fuentes_directas([ir], "acciones", msft) == [ir]
    # La nota de un medio que cita el anuncio de la empresa sigue contando (no es un banco).
    wire = _nota("Microsoft", "https://www.reuters.com/technology/microsoft-anuncia-recompra/",
                 "Microsoft anuncia un programa de recompra de acciones.")
    assert fu.fuentes_directas([wire], "acciones", msft) == [wire]
    for ticker, url in (("#DE", "https://www.deere.com/en/agriculture/tractores-deere"),
                        ("#GE", "https://www.geaerospace.com/propulsion/commercial/ge-aerospace-motor")):
        _, ancla = sg.segmento_y_ancla(ticker)
        nota = _nota(ancla["nombre"], url, f"{ancla['nombre']} muestra su catálogo.")
        assert fu.fuentes_directas([nota], "acciones", ancla) == [], ticker


def test_las_rutas_propias_caen_dentro_de_los_dominios_del_ancla():
    for t in ACCIONES:
        _, ancla = sg.segmento_y_ancla(t)
        for ruta in ancla.get("rutas_propias", []):
            host = ruta.split("/")[0]
            assert any(host == d or host.endswith("." + d) for d in ancla["dominios"]), (t, ruta)
    for t in ("#GS", "#MS", "#JPM", "#MSFT", "#DE", "#GE"):
        assert sg.segmento_y_ancla(t)[1].get("rutas_propias"), t
