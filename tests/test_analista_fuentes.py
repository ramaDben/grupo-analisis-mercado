"""Validación de las fuentes que agy cita: lista cerrada, dominio, frescura, URL y discrepancia."""
from __future__ import annotations

import json
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


# ───────────────────────────────────────────── la redirección se revalida (fix final)

ARTICULO = "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/"


def _get_que_termina_en(destino, status=200):
    from types import SimpleNamespace

    def get(url, **kw):
        return SimpleNamespace(status_code=status, url=destino, close=lambda: None)
    return get


def test_una_redireccion_a_la_portada_cuenta_como_muerta(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", _get_que_termina_en("https://www.reuters.com/"))
    assert fu.verificar_url(ARTICULO) == "muerta"


def test_una_redireccion_a_otro_dominio_cuenta_como_muerta(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", _get_que_termina_en("https://spam.example.com/markets/nota"))
    assert fu.verificar_url(ARTICULO) == "muerta"


def test_una_redireccion_a_otro_articulo_del_medio_pasa(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", _get_que_termina_en("https://www.reuters.com/markets/oro-nota-final/"))
    assert fu.verificar_url(ARTICULO) == "ok"


# ───────────────────────────────────────────── bancos obligatorios (spec 2026-10-17 §5)


def test_la_lista_declara_que_grupos_cuentan_como_banco():
    assert fu.cargar_lista()["cuentan_como_banco"] == ["bancos_de_inversion", "chile"]


def test_cuentan_los_bancos_de_inversion_y_los_de_chile_y_no_los_organismos():
    fuentes = [{"entidad": "JPMorgan"}, {"entidad": "World Gold Council"}, {"entidad": "Banchile"}, "basura"]
    assert [f["entidad"] for f in fu.bancos(fuentes)] == ["JPMorgan", "Banchile"]


def test_falta_banco_lo_dice_y_calla_si_hay_uno():
    sin = {"editorial": {"fuentes": [{"entidad": "Fed"}]}}
    con = {"editorial": {"fuentes": [{"entidad": "Fed"}, {"entidad": "UBS"}]}}
    errs = fu.falta_banco(sin)
    assert errs and "falta al menos una voz de banco" in errs[0] and "14 días" in errs[0]
    assert fu.falta_banco(con) == []
    assert fu.falta_banco({"editorial": {"fuentes": "[[ESCRIBIR]]"}}) == []  # eso lo dice esquema.errores


def test_el_intento_guarda_las_validas_y_las_urls_descartadas(tmp_path):
    valida = {"entidad": "Fed", "url": "https://www.federalreserve.gov/newsevents/x.htm"}
    crudas = [valida, {"entidad": "Un Blog", "url": "https://blog.example.com/nota"}, "basura"]
    ruta = fu.guardar_intento(tmp_path, [valida], ["Un Blog: la entidad no está en la lista"], crudas)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert ruta.name == fu.INTENTO and datos["validas"] == [valida]
    assert datos["descartadas"] == ["https://blog.example.com/nota"] and datos["motivos"]


# ───────────────────────────────────────────── bancos correo: a lo sumo 1 y 1 (2026-10-19)


def test_seleccionar_bancos_correo_uno_a_favor_y_uno_en_contra():
    """Con varios bancos y organismos, toma exactamente 1 a favor y 1 en contra, priorizando el más reciente."""
    fuentes = [
        {"entidad": "World Gold Council", "fecha": "2026-10-15", "postura": "alcista"},
        {"entidad": "UBS", "fecha": "2026-10-13", "postura": "bajista"},
        {"entidad": "JPMorgan", "fecha": "2026-10-11", "postura": "bajista"},
        {"entidad": "Goldman Sachs", "fecha": "2026-10-14", "postura": "alcista"},
        {"entidad": "Morgan Stanley", "fecha": "2026-10-10", "postura": "alcista"},
    ]
    # Para dirección BAJISTA: UBS y JPMorgan son a favor (UBS más reciente); Goldman y Morgan son en contra (Goldman más reciente).
    sel = fu.seleccionar_bancos_correo(fuentes, "BAJISTA")
    assert len(sel) == 2
    assert sel[0]["entidad"] == "UBS"
    assert sel[1]["entidad"] == "Goldman Sachs"


def test_seleccionar_bancos_correo_banco_unico():
    """Si solo hay bancos de una postura (o uno solo), retorna una lista con ese único banco sin tarjetas vacías."""
    solo_alcista = [
        {"entidad": "Goldman Sachs", "fecha": "2026-10-14", "postura": "alcista"},
        {"entidad": "World Gold Council", "fecha": "2026-10-15", "postura": "alcista"},
    ]
    sel_bajista = fu.seleccionar_bancos_correo(solo_alcista, "BAJISTA")
    assert len(sel_bajista) == 1
    assert sel_bajista[0]["entidad"] == "Goldman Sachs"

    sel_alcista = fu.seleccionar_bancos_correo(solo_alcista, "ALCISTA")
    assert len(sel_alcista) == 1
    assert sel_alcista[0]["entidad"] == "Goldman Sachs"


def test_seleccionar_bancos_correo_sin_bancos():
    """Sin bancos calificados (solo organismos o vacía), retorna lista vacía."""
    organismos = [{"entidad": "World Gold Council", "fecha": "2026-10-15", "postura": "alcista"}]
    assert fu.seleccionar_bancos_correo(organismos, "BAJISTA") == []
    assert fu.seleccionar_bancos_correo([], "BAJISTA") == []

