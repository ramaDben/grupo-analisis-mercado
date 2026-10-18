"""La agenda de la ventana de un análisis: dos pestañas, tres estados y el efecto del glosario."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import agenda as ag  # noqa: E402
from analista import preparar as pr  # noqa: E402

SCL = ZoneInfo("America/Santiago")
SABADO = datetime(2026, 10, 17, 11, 7, tzinfo=SCL)


def ev(hora, nombre="CPI (MoM) (Sep)", impacto="alto", efecto_oro="baja", forecast="0.3%", previo="0.4%"):
    dic = {"nombre_es": "Índice de precios al consumidor (IPC)", "explicacion": "Mide la inflación."}
    if efecto_oro:
        dic["si_sale_sobre_consenso"] = {"oro": efecto_oro}
    return {"nombre": nombre, "pais": "United States", "impacto": impacto, "hora_servidor": hora,
            "forecast": forecast, "previo": previo, "diccionario": dic}


def cargador(por_pestana):
    pedidas = []

    def cargar(solo_hoy, min_impact, ahora, pestanas):
        pedidas.append((pestanas, min_impact))
        res = por_pestana[pestanas[0]]
        return res if isinstance(res, dict) else {"source": "investing", "eventos": res}

    cargar.pedidas = pedidas
    return cargar


def test_un_sabado_la_ventana_sale_de_la_semana_siguiente():
    cargar = cargador({
        "thisWeek": [ev("2026-10-16 09:30"), ev("2026-10-17 08:00", impacto="bajo")],
        "nextWeek": [ev("2026-10-21 09:30"), ev("2026-10-26 09:30"), ev("2026-10-20 10:00", impacto="medio")],
    })
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "ok" and (a.desde, a.hasta) == ("sábado 17/10", "sábado 24/10")
    assert [e["dia"] for e in a.eventos] == ["miércoles 21/10"]
    e = a.eventos[0]
    assert e["hora"] == "09:30 CLST" and e["evento"] == "Índice de precios al consumidor (IPC)"
    assert e["pais"] == "EE.UU." and e["anterior"] == "0,4%" and e["esperado"] == "0,3%"
    assert [p for p, _ in cargar.pedidas] == [("thisWeek",), ("nextWeek",)]
    assert all(m == "low" for _, m in cargar.pedidas)  # todo el calendario: así se detecta la copia vieja


def test_el_efecto_sale_del_glosario():
    cargar = cargador({"thisWeek": [], "nextWeek": [ev("2026-10-21 09:30"),
                                                     ev("2026-10-22 09:30", nombre="X", efecto_oro=None)]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    con, sin = a.eventos
    assert "el oro tiende a bajar" in con["efecto"] and con["mueve_al_activo"] is True
    assert sin["efecto"] == "" and sin["mueve_al_activo"] is False


def test_sin_datos_de_alto_impacto_la_ventana_queda_vacia_con_sus_fechas():
    cargar = cargador({"thisWeek": [ev("2026-10-17 12:00", impacto="bajo")],
                       "nextWeek": [ev("2026-10-21 09:30", impacto="medio")]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "vacia" and a.eventos == []
    texto = ag.texto_vacia(a.a_dict())
    assert "sábado 17/10" in texto and "sábado 24/10" in texto and "—" not in texto


def test_una_copia_vieja_de_la_semana_siguiente_no_cuenta():
    """`_fetch_calendario` devuelve la caché vencida sin avisar: se reconoce por sus fechas."""
    cargar = cargador({"thisWeek": [ev("2026-10-16 09:30")], "nextWeek": [ev("2026-10-07 09:30")]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "sin_calendario" and any("copia vieja" in x for x in a.avisos)


def test_el_calendario_caido_se_dice():
    caido = {"error": "NO_CALENDAR_FEEDS", "message": "x"}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": caido, "nextWeek": caido}))
    assert a.estado == "sin_calendario" and len(a.avisos) == 2


def test_con_una_semana_caida_y_datos_en_la_otra_sale_con_aviso():
    caido = {"error": "NO_CALENDAR_FEEDS", "message": "x"}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": caido,
                                                                 "nextWeek": [ev("2026-10-21 09:30")]}))
    assert a.estado == "ok" and a.avisos


def test_una_ventana_parcial_se_marca_y_declara_hasta_donde_cubre():
    caido = {"error": "NO_CALENDAR_FEEDS", "message": "x"}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": caido,
                                                                 "nextWeek": [ev("2026-10-21 09:30")]}))
    d = a.a_dict()
    assert d["estado"] == "ok" and d["parcial"] is True and d["cubierto_hasta"] == "miércoles 21/10"
    assert d["hasta"] == "sábado 24/10"  # la ventana pedida no cambia


def test_una_ventana_completa_no_es_parcial():
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": [ev("2026-10-21 09:30")]}))
    d = a.a_dict()
    assert d["parcial"] is False and d["cubierto_hasta"] == d["hasta"]


def test_dia_corto_es_el_formato_de_preparar():
    assert ag.dia_corto(SABADO) == pr.fecha_corta(SABADO) == "sábado 17/10"


def test_la_lamina_pone_primero_lo_que_mueve_al_activo_y_rinde_sin_huerfanos():
    from story_render import build_html

    eventos = [ev(f"2026-10-{d} 09:30", nombre=f"E{d}", efecto_oro=None) for d in range(19, 24)]
    eventos += [ev("2026-10-23 12:00", nombre="CPI A"), ev("2026-10-24 08:00", nombre="CPI B")]
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": eventos}))
    payload = ag.payload_lamina(a.a_dict())
    # Siete eventos y caben seis: entran los dos que mueven al oro (23 y 24) y cae el último de los
    # otros (E23); después van en orden de calendario.
    assert [e["dia"] for e in payload["eventos"]] == [
        "LUNES 19/10", "MARTES 20/10", "MIÉRCOLES 21/10", "JUEVES 22/10", "VIERNES 23/10", "SÁBADO 24/10"]
    assert [e["evento"] for e in payload["eventos"]][-2:] == [
        "Índice de precios al consumidor (IPC) (6)", "Índice de precios al consumidor (IPC) (7)"]  # mismo nombre: se numeran
    html = build_html(payload, RAIZ / "templates" / "stories" / "calendario.html")
    assert "Los días clave de este análisis" in html and "{{" not in html
    for texto in (payload["titulo"], payload["subtitulo"], payload["cta"]):
        assert "—" not in texto and "oportunidad" not in texto.lower() and "operar" not in texto.lower()


def test_dos_datos_con_el_mismo_nombre_del_glosario_se_distinguen():
    pmi = {"nombre_es": "Índice de gerentes de compra", "explicacion": "Mide la actividad."}
    manu = {**ev("2026-10-23 10:45", nombre="S&P Global Manufacturing PMI (Oct)"), "diccionario": pmi}
    serv = {**ev("2026-10-23 10:45", nombre="S&P Global Services PMI (Oct)"), "diccionario": pmi}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": [manu, serv]}))
    assert [e["evento"] for e in a.eventos] == ["Índice de gerentes de compra (manufacturero)",
                                                "Índice de gerentes de compra (servicios)"]
    sin = {**ev("2026-10-23 10:45", nombre="Otro A"), "diccionario": pmi}
    con = {**ev("2026-10-23 10:45", nombre="Otro B"), "diccionario": pmi}
    b = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": [sin, con]}))
    etiquetas = [e["evento"] for e in b.eventos]
    assert len(set(etiquetas)) == 2 and all(e.startswith("Índice de gerentes de compra") for e in etiquetas)


def test_un_dato_solo_conserva_su_nombre_simple():
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": [ev("2026-10-21 09:30")]}))
    assert a.eventos[0]["evento"] == "Índice de precios al consumidor (IPC)"
