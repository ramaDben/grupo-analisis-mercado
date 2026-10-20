"""Config de segmentos, resolver de ancla y consultas (spec 2026-10-20, Task 2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

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
