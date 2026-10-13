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


def _texto(ahora, ev=None, alcista=False, estado_sim="en_curso", digits=2, ticker="XAUUSD"):
    ctx = mac.contexto(ticker, ahora, [ev or evento()])
    esc = {"direccion": "ALCISTA" if alcista else "BAJISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0}
    return mac.redactar(ctx, "Oro", esc, estado_sim, ahora, digits)


def test_el_dato_pendiente_da_los_dos_caminos_con_el_mismo_peso_en_una_venta():
    m = _texto(a(7))
    assert m["apertura"].startswith("hoy a las 09:30 (hora de Chile) se publica el dato «Índice de precios al "
                                    "consumidor (IPC)» de EE.UU.")
    assert ("Si sale sobre lo esperado, el oro tiende a bajar, lo que iría a favor de la venta; si sale bajo lo "
            "esperado, tiende a subir, lo que lo acercaría al stop de 3.950,00.") in m["reaccion"]
    assert "Son los dos caminos, y el stop del lunes es el límite en ambos." in m["reaccion"]


def test_en_una_compra_los_caminos_se_dan_vuelta():
    m = _texto(a(7), alcista=True)
    assert "tiende a bajar, lo que lo acercaría al stop" in m["reaccion"]
    assert "tiende a subir, lo que iría a favor de la compra" in m["reaccion"]


def test_sin_simulacion_viva_solo_da_la_reaccion_sin_atarla_a_stop_ni_objetivo():
    m = _texto(a(7), estado_sim="entrada_pendiente")
    assert "stop" not in m["reaccion"] and "Si sale sobre lo esperado, el oro tiende a bajar" in m["reaccion"]


def test_con_un_dato_por_salir_se_quita_la_invitacion_a_tomar_posicion():
    assert _texto(a(7))["quita_espacio"] and _texto(a(9, 10))["quita_espacio"]
    assert _texto(AHORA)["quita_espacio"]                                            # mañana: menos de 24 h
    assert not _texto(AHORA, evento(hora="2026-10-16 09:30"))["quita_espacio"]       # en 3 días: no
    assert not _texto(a(10), evento(actual="0.4%"))["quita_espacio"]                 # ya salió


def test_en_la_ventana_no_hay_reaccion_y_si_cautela_factual():
    m = _texto(a(9, 10))
    assert "en unos minutos (09:30)" in m["apertura"] and "a saltos" in m["apertura"]
    assert m["reaccion"] == "" and m["cierre"] == mac.CIERRE_VENTANA


def test_el_dia_de_un_dato_lejano_se_dice_con_el_dia_de_la_semana():
    m = _texto(AHORA, evento(hora="2026-10-16 09:30"))
    assert m["apertura"].startswith("el viernes a las 09:30 (hora de Chile)")


@pytest.mark.parametrize("actual,lado,verbo", [("0.4%", "sobre lo esperado", "bajar"),
                                               ("0.1%", "bajo lo esperado", "subir"),
                                               ("0.2%", "en línea con lo esperado", None)])
def test_el_dato_publicado_dice_el_resultado_y_la_tendencia_del_glosario(actual, lado, verbo):
    m = _texto(a(10), evento(actual=actual))
    assert m["apertura"].startswith("ya se publicó el dato «Índice de precios al consumidor (IPC)» de EE.UU.: ")
    assert f"{actual.replace('.', ',').replace('%', ' %')} frente a 0,2 % esperado, es decir, {lado}." in m["apertura"]
    assert (f"tiende a {verbo}" in m["apertura"]) == (verbo is not None)
    assert m["reaccion"] == "" and not m["quita_espacio"] and m["aparte"] == ""


def test_el_aviso_al_ejecutivo_dice_que_volver_a_pedir():
    assert "/seguimiento oro" in _texto(a(7))["aparte"] and "09:30" in _texto(a(7))["aparte"]
    assert "/seguimiento dolar" in _texto(a(7), ticker="USDCLP")["aparte"]
    assert _texto(AHORA)["aparte"] == ""  # mañana: todavía no hay nada que reenviar


def test_nada_de_lo_que_se_dice_promete_ni_recomienda():
    for ahora, ev in ((a(7), evento()), (a(9, 10), evento()), (a(10), evento(actual="0.4%")), (AHORA, evento())):
        m = _texto(ahora, ev)
        todo = " ".join(m[k] or "" for k in ("apertura", "reaccion", "cierre", "aparte")).lower()
        assert "$" not in todo and "—" not in todo and "–" not in todo
        for prohibido in ("recomend", "oportunidad", "cartera", "hubieras", "ganarías", "aprovecha", "seguro"):
            assert prohibido not in todo


# ───────────────────────────────────────────── el mensaje completo


def _datos():
    from analista import preparar as pr  # noqa: F401

    pieza = fx.pieza_seguimiento(Path("."))
    return pieza["datos"]


def test_con_un_dato_pendiente_el_mensaje_abre_con_el_dato_y_no_invita_a_tomar_posicion(tmp_path):
    datos = fx.pieza_seguimiento(tmp_path)["datos"]
    ctx = mac.contexto(datos["ticker"], a(7), [evento()])
    texto, aparte = sg.redactar(datos, "Hari", ctx, a(7))
    primera = texto.split("\n\n")[0]
    assert primera.startswith("Hola Hari, hoy a las 09:30 (hora de Chile) se publica el dato")
    assert "espacio para tomar posición" not in texto and "Las cifras de la simulación" in texto
    assert "La lectura" in texto or "lectura" in texto.lower()
    assert texto.rstrip().endswith(mac.CIERRES_PENDIENTE[0]) or texto.rstrip().endswith(mac.CIERRES_PENDIENTE[1])
    assert "/seguimiento oro" in aparte


def test_sin_dato_el_mensaje_es_el_de_siempre_y_conserva_la_invitacion(tmp_path):
    datos = fx.pieza_seguimiento(tmp_path)["datos"]
    texto, aparte = sg.redactar(datos, "", None, a(7))
    assert texto.startswith("Hola, ") and "todavía queda espacio para tomar posición" in texto and aparte == ""


def test_el_mensaje_se_arma_desde_los_datos_y_no_desde_el_texto_guardado(tmp_path):
    datos = dict(fx.pieza_seguimiento(tmp_path)["datos"], whatsapp="TEXTO DE UNA VERSION ANTERIOR")
    texto, _ = sg.redactar(datos, "")
    assert "VERSION ANTERIOR" not in texto and "simulación de Oro" in texto
