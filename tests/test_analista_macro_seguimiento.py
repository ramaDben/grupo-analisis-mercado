"""La agenda macro dentro del seguimiento: qué dato se menciona, cuándo, y qué se promete (nada)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import analista_fixtures as fx  # noqa: E402
from analista import macro_seguimiento as mac  # noqa: E402
from analista import seguimiento as sg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 13, 18, 0, tzinfo=SCL)  # martes por la tarde
EFECTO = {"orden": "primero", "lectura": "inflación más alta de lo esperado en EE.UU.",
          "dolar": "sube", "oro": "baja", "indices": "baja", "usdclp": "sube"}


def evento(hora="2026-10-14 09:30", actual="", forecast="0.2%", impacto="alto", pais="United States",
           nombre="CPI (MoM) (Sep)", efecto=EFECTO, tier=1):
    ev = {"nombre": nombre, "pais": pais, "impacto": impacto, "hora_servidor": hora, "forecast": forecast,
          "previo": "0.3%", "actual": actual, "fuente": "investing"}
    if efecto is None:
        ev["glosario_pendiente"] = True
    else:
        ev["diccionario"] = {"nombre_es": "Índice de precios al consumidor (IPC)", "tier": tier,
                             "si_sale_sobre_consenso": efecto}
    return ev


def a(h, m=0, dia=14):
    return datetime(2026, 10, dia, h, m, tzinfo=SCL)


# ───────────────────────────────────────────── qué dato se elige


@pytest.mark.parametrize("ahora,estado", [
    (AHORA, "proximo"),                  # mañana a las 09:30
    (a(7, 0), "pendiente"),              # hoy, falta rato
    (a(9, 10), "ventana"),               # faltan 20 minutos
    (a(9, 0), "ventana"),               # faltan justo 30 minutos
    (a(8, 59), "pendiente"),            # 31 minutos: todavía no
])
def test_estados_de_un_dato_que_todavia_no_sale(ahora, estado):
    assert mac.contexto("XAUUSD", ahora, [evento()])["estado"] == estado


def test_un_dato_publicado_hace_poco_cuenta_y_uno_viejo_no():
    ev = evento(actual="0.4%")
    assert mac.contexto("XAUUSD", a(10, 0), [ev])["estado"] == "publicado"
    assert mac.contexto("XAUUSD", a(12, 31), [ev]) is None  # más de 3 horas: ya no es noticia


def test_pasada_la_hora_sin_resultado_no_se_afirma_nada():
    assert mac.contexto("XAUUSD", a(9, 45), [evento()]) is None


@pytest.mark.parametrize("ticker", ["COPPER", "BRENT.spot", "BTCUSD", "USDJPY", "ETHUSD"])
def test_sin_reaccion_declarada_no_hay_parrafo_macro(ticker):
    assert mac.contexto(ticker, a(7, 0), [evento()]) is None


def test_solo_cuenta_lo_que_el_glosario_declara_para_ese_activo_y_de_alto_impacto():
    assert mac.contexto("XAUUSD", a(7), [evento(efecto=None)]) is None            # sin glosario
    assert mac.contexto("XAUUSD", a(7), [evento(impacto="medio")]) is None
    assert mac.contexto("XAUUSD", a(7), [evento(efecto={"dolar": "sube"})]) is None  # nada para el oro
    assert mac.contexto("USDCLP", a(7), [evento(efecto={"dolar": "sube"})]) is None
    assert mac.contexto("USDCLP", a(7), [evento()])["verbo"] == "sube"


def test_un_dato_a_mas_de_una_semana_no_se_menciona():
    assert mac.contexto("XAUUSD", AHORA, [evento(hora="2026-10-25 09:30")]) is None


def test_manda_el_dato_mas_urgente():
    cerca, lejos = evento(hora="2026-10-14 09:30"), evento(hora="2026-10-14 15:00", nombre="PPI (MoM) (Sep)")
    assert mac.contexto("XAUUSD", a(9, 10), [lejos, cerca])["evento"] is cerca  # ventana gana a pendiente
    assert mac.contexto("XAUUSD", a(7), [lejos, cerca])["evento"] is cerca      # el más cercano


def test_un_calendario_caido_no_rompe_nada(monkeypatch):
    import market_data_mcp.tools.calendar as calendario

    monkeypatch.setattr(calendario, "cargar_calendario", lambda **kw: {"error": "NO_CALENDAR_FEEDS"})
    assert mac.eventos_de_la_semana(AHORA) == []
    monkeypatch.setattr(calendario, "cargar_calendario", lambda **kw: (_ for _ in ()).throw(OSError("sin red")))
    assert mac.eventos_de_la_semana(AHORA) == []


# ───────────────────────────────────────────── qué se dice


def _texto(ahora, ev=None, alcista=False, estado_sim="en_curso", digits=2, ticker="XAUUSD", variante=0):
    ctx = mac.contexto(ticker, ahora, [ev or evento()])
    esc = {"direccion": "ALCISTA" if alcista else "BAJISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0}
    return mac.redactar(ctx, "Oro", esc, estado_sim, ahora, digits, variante)


@pytest.mark.parametrize("variante", [0, 1])
def test_el_dato_pendiente_se_dice_como_se_habla_y_ata_el_resultado_al_plan(variante):
    c = _texto(a(7), variante=variante)["cuerpo"]
    assert "hoy a las 09:30" in c and "el dato del IPC de EE.UU. (índice de precios al consumidor)" in c
    assert "suele mover el oro" in c and "la venta del lunes" in c
    # Oro baja con un IPC alto: para una venta, sobre lo esperado juega a favor.
    assert "sobre lo esperado juega a favor" in c
    assert c.count("CFD") == 1 and c.endswith("?") and "⏰" not in c and "«" not in c


@pytest.mark.parametrize("variante", [0, 1])
def test_en_una_compra_los_resultados_se_dan_vuelta(variante):
    c = _texto(a(7), alcista=True, variante=variante)["cuerpo"]
    assert "la compra del lunes" in c and "sobre lo esperado juega en contra" in c


def test_sin_plan_vivo_dice_hacia_donde_tiende_el_activo_y_no_lo_ata_a_nada():
    c = _texto(a(7), estado_sim="stop")["cuerpo"]
    assert "tiende a bajar" in c and "lo contrario si sale bajo" in c and "venta" not in c


def test_el_dato_del_dia_siguiente_o_de_la_semana_se_dice_con_su_dia():
    assert _texto(AHORA)["cuerpo"].startswith("mañana a las 09:30")
    c = _texto(AHORA, evento(hora="2026-10-16 09:30"))["cuerpo"]
    assert c.startswith("el viernes a las 09:30") and c.endswith("?")


@pytest.mark.parametrize("variante", [0, 1])
def test_en_la_ventana_dice_la_cautela_y_nombra_el_plan(variante):
    c = _texto(a(9, 10), variante=variante)["cuerpo"]
    assert "a las 09:30" in c and "saltos" in c and "la venta del lunes" in c and c.endswith("?")
    assert "CFD" not in c


@pytest.mark.parametrize("actual,lado,tendencia,juega", [("0.4%", "sobre lo esperado", "bajar", "a favor"),
                                                         ("0.1%", "bajo lo esperado", "subir", "en contra"),
                                                         ("0.2%", "en línea con lo esperado", None, None)])
@pytest.mark.parametrize("variante", [0, 1])
def test_el_dato_publicado_dice_el_resultado_y_lo_que_significa_para_el_plan(actual, lado, tendencia, juega, variante):
    c = _texto(a(10), evento(actual=actual), variante=variante)["cuerpo"]
    assert f"{actual.replace('.', ',').replace('%', ' %')} frente a 0,2 % esperado, {lado}" in c
    assert (f"tiende a {tendencia}" in c) == (tendencia is not None)
    assert (f"juega {juega} de la venta del lunes" in c) == (juega is not None) and c.endswith("?")


def test_el_aviso_al_ejecutivo_dice_que_volver_a_pedir():
    assert "/seguimiento oro" in _texto(a(7))["aparte"] and "09:30" in _texto(a(7))["aparte"]
    assert "/seguimiento dolar" in _texto(a(7), ticker="USDCLP")["aparte"]
    assert _texto(AHORA)["aparte"] == "" and _texto(a(10), evento(actual="0.4%"))["aparte"] == ""


def test_nada_de_lo_que_se_dice_promete_ni_recomienda_ni_suena_a_espejo():
    import re

    for ahora, ev in ((a(7), evento()), (a(9, 10), evento()), (a(10), evento(actual="0.4%")), (AHORA, evento())):
        for estado_sim in ("en_curso", "stop"):
            for variante in (0, 1):
                m = _texto(ahora, ev, estado_sim=estado_sim, variante=variante)
                todo = (m["cuerpo"] + " " + m["aparte"]).lower()
                assert "$" not in todo and "—" not in todo and "–" not in todo and "«" not in todo
                for prohibido in ("recomend", "oportunidad", "cartera", "hubieras", "ganarías", "aprovecha", "seguro"):
                    assert prohibido not in todo
                assert not re.search(r"si sale sobre lo esperado[^.]*[,;] (y )?si sale bajo lo esperado", todo)
                assert "ese movimiento se puede operar" not in todo and "cambiamos de lado" not in todo


# ───────────────────────────────────────────── el mensaje completo


def test_con_un_dato_pendiente_el_mensaje_abre_con_el_dato_y_es_un_parrafo(tmp_path):
    datos = fx.pieza_seguimiento(tmp_path)["datos"]
    ctx = mac.contexto(datos["ticker"], a(7), [evento()])
    texto, aparte = sg.redactar(datos, "Hari", ctx, a(7))
    assert texto.startswith("Hola Hari, hoy a las 09:30 sale el dato del IPC de EE.UU.")
    assert "\n" not in texto and texto.endswith("?") and "compra" in texto or "venta" in texto
    assert "/seguimiento oro" in aparte


def test_sin_dato_el_mensaje_es_un_parrafo_corto_con_el_plan(tmp_path):
    datos = fx.pieza_seguimiento(tmp_path)["datos"]
    texto, aparte = sg.redactar(datos, "", None, a(7))
    assert texto.startswith("Hola, ") and "CFD" in texto and "\n" not in texto and aparte == ""


def test_el_mensaje_se_arma_desde_los_datos_y_no_desde_el_texto_guardado(tmp_path):
    datos = dict(fx.pieza_seguimiento(tmp_path)["datos"], whatsapp="TEXTO DE UNA VERSION ANTERIOR")
    texto, _ = sg.redactar(datos, "")
    assert "VERSION ANTERIOR" not in texto and "oro" in texto
