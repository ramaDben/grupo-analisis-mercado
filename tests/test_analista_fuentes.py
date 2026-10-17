"""Validación de las fuentes que agy cita: lista cerrada, dominio, frescura, URL y discrepancia."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import fuentes as fu  # noqa: E402

HOY = date(2026, 10, 16)


def _f(**cambios):
    base = {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14",
            "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/",
            "postura": "alcista", "tesis": "Goldman Sachs mantiene su visión alcista del oro."}
    return {**base, **cambios}


def _ok(url):
    return "ok"


def test_una_fuente_valida_pasa_y_trae_su_verificacion():
    validas, descartes = fu.depurar([_f()], HOY, verificar=_ok)
    assert [v["entidad"] for v in validas] == ["Goldman Sachs"] and validas[0]["verificacion"] == "ok"
    assert descartes == []


def test_una_entidad_fuera_de_la_lista_se_descarta():
    validas, descartes = fu.depurar([_f(entidad="Un Blog Cualquiera")], HOY, verificar=_ok)
    assert validas == [] and "Un Blog Cualquiera" in descartes[0] and "lista" in descartes[0]


def test_el_dominio_tiene_que_ser_el_del_medio():
    validas, descartes = fu.depurar([_f(url="https://www.otro-sitio.com/articulo-largo")], HOY, verificar=_ok)
    assert validas == [] and "dominio" in descartes[0]


def test_un_subdominio_del_medio_vale():
    validas, _ = fu.depurar([_f(url="https://es.reuters.com/mercados/oro-2026")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_una_portada_no_es_un_articulo():
    validas, descartes = fu.depurar([_f(url="https://www.reuters.com/")], HOY, verificar=_ok)
    assert validas == [] and "artículo" in descartes[0]


def test_la_fecha_vieja_futura_o_mal_escrita_se_descarta():
    for fecha in ("2026-09-20", "2026-10-30", "ayer"):
        validas, descartes = fu.depurar([_f(fecha=fecha)], HOY, verificar=_ok)
        assert validas == [] and "fecha" in descartes[0], fecha


def test_catorce_dias_justos_todavia_valen():
    validas, _ = fu.depurar([_f(fecha="2026-10-02")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_una_url_muerta_se_descarta_y_una_con_muro_queda_sin_verificar():
    validas, descartes = fu.depurar([_f()], HOY, verificar=lambda u: "muerta")
    assert validas == [] and "no responde" in descartes[0]
    validas, _ = fu.depurar([_f()], HOY, verificar=lambda u: "sin_verificar")
    assert validas[0]["verificacion"] == "sin_verificar"


def test_solo_https_y_nada_de_marcado_en_los_campos():
    for malo in (_f(url="http://www.reuters.com/markets/oro-2026"), _f(url="javascript:alert(1)//reuters.com/a/b"),
                 _f(tesis="Goldman <b>ve</b> el oro alcista"), _f(entidad="<script>")):
        validas, _ = fu.depurar([malo], HOY, verificar=_ok)
        assert validas == []


def test_una_postura_fuera_del_vocabulario_se_descarta():
    validas, descartes = fu.depurar([_f(postura="muy alcista")], HOY, verificar=_ok)
    assert validas == [] and "postura" in descartes[0]


def test_falta_un_campo_o_no_es_un_diccionario():
    validas, descartes = fu.depurar([{"entidad": "UBS"}, "texto suelto", None], HOY, verificar=_ok)
    assert validas == [] and len(descartes) == 3


def test_la_misma_url_no_se_repite():
    validas, _ = fu.depurar([_f(), _f(tesis="Otra frase.")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_agy_no_entrego_una_lista():
    pieza = {"editorial": {"fuentes": "[[ESCRIBIR]]"}}
    nueva, descartes = fu.depurar_pieza(pieza, HOY, verificar=_ok)
    assert nueva["editorial"]["fuentes"] == [] and descartes


def test_depurar_pieza_reemplaza_las_fuentes_por_las_validas():
    pieza = {"editorial": {"fuentes": [_f(), _f(entidad="Blog")]}}
    nueva, descartes = fu.depurar_pieza(pieza, HOY, verificar=_ok)
    assert len(nueva["editorial"]["fuentes"]) == 1 and len(descartes) == 1


def test_la_discrepancia_la_calcula_python():
    assert fu.discrepa(_f(postura="alcista"), "BAJISTA") is True
    assert fu.discrepa(_f(postura="bajista"), "BAJISTA") is False
    assert fu.discrepa(_f(postura="neutral"), "LATERAL") is False
    assert fu.discrepa(_f(postura="alcista"), "LATERAL") is True
