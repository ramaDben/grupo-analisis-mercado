"""La alerta semanal dentro del bot: el hilo, los botones y lo que se mide de cada toque."""
from __future__ import annotations

import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import avisos_semana as av  # noqa: E402
from analista import bot as b  # noqa: E402
from test_analista_bot import CAMILA, OTRO, TgFalso, armado, update  # noqa: E402,F401

SCL = ZoneInfo("America/Santiago")
LUNES = datetime(2026, 10, 19, 7, 45, tzinfo=SCL)
MARTES = datetime(2026, 10, 20, 16, 0, tzinfo=SCL)


class TgConBotones(TgFalso):
    def __init__(self):
        super().__init__()
        self.con_teclado, self.sin_teclado, self.callbacks = [], [], []

    def mensaje_con_teclado(self, chat, texto, teclado):
        self.con_teclado.append((chat, texto, teclado))
        return 900 + len(self.con_teclado)

    def quitar_teclado(self, chat, message_id):
        self.sin_teclado.append((chat, message_id))

    def responder_callback(self, id_, texto=""):
        self.callbacks.append((id_, texto))


def aviso(tipo="mapa", fecha="2026-10-19", activo=None, evento=None):
    evento = evento or ("mapa" if tipo == "mapa" else "IPC|2026-10-21")
    return av.Aviso(tipo, fecha, evento, 0 if tipo == "mapa" else 1, "texto", activo, av._id(tipo, fecha, evento))


def callback(data, usuario=CAMILA, chat=500, message_id=901):
    return {"update_id": 2, "callback_query": {"id": "cb1", "from": {"id": int(usuario)}, "data": data,
                                                "message": {"message_id": message_id, "chat": {"id": chat}}}}


@pytest.fixture
def con_avisos(armado, tmp_path):
    armado.bot.tg = TgConBotones()
    armado.bot.avisos = av.Estado(tmp_path / "avisos.json")
    return armado


# ───────────────────────────────────────────── el hilo


def test_el_hilo_no_arranca_si_no_hay_agendador(armado):
    assert armado.bot.iniciar_avisos() is None


def test_un_latido_que_falla_no_tumba_el_hilo(armado):
    llamadas = []

    class Agendador:
        def latido(self):
            llamadas.append(1)
            if len(llamadas) == 1:
                raise RuntimeError("calendario roto")

    armado.bot.agendador = Agendador()
    hilo = armado.bot.iniciar_avisos(pausa=0.01)
    for _ in range(200):
        if len(llamadas) >= 3:
            break
        time.sleep(0.01)
    armado.bot.parar.set()
    hilo.join(2)
    assert len(llamadas) >= 3 and hilo.daemon


# ───────────────────────────────────────────── enviar el aviso con su teclado


def test_el_mapa_lleva_util_y_no_me_sirve(con_avisos):
    a = aviso("mapa")
    mid = con_avisos.bot.enviar_aviso(CAMILA, a)
    chat, texto, teclado = con_avisos.bot.tg.con_teclado[0]
    assert chat == int(CAMILA) and mid == 901 and texto == "texto"
    assert [x["callback_data"] for x in teclado["inline_keyboard"][0]] == [f"sw:util:{a.id}", f"sw:no:{a.id}"]


def test_la_vispera_lleva_el_boton_del_activo(con_avisos):
    a = aviso("vispera", activo="USDCLP")
    con_avisos.bot.enviar_aviso(CAMILA, a)
    boton = con_avisos.bot.tg.con_teclado[0][2]["inline_keyboard"][0][0]
    assert boton["callback_data"] == f"sw:ped:{a.id}" and "dólar" in boton["text"]


def test_la_vispera_sin_activo_va_sin_botones(con_avisos):
    assert con_avisos.bot.enviar_aviso(CAMILA, aviso("vispera", activo=None)) is None
    assert con_avisos.bot.tg.con_teclado == [] and con_avisos.bot.tg.mensajes[0][1] == "texto"


def test_los_ids_de_callback_caben_en_los_64_bytes_de_telegram():
    assert len(f"sw:util:{aviso('mapa').id}".encode()) <= 64


# ───────────────────────────────────────────── votos


def test_el_voto_se_anota_y_quita_el_teclado(con_avisos):
    a = aviso("mapa")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, LUNES, 901)
    con_avisos.bot.recibir_callback(callback(f"sw:util:{a.id}"))
    assert con_avisos.bot.avisos.registro(CAMILA, a.id)["votos"][0]["voto"] == "util"
    assert con_avisos.bot.tg.sin_teclado == [(500, 901)]
    assert con_avisos.bot.tg.callbacks[0][0] == "cb1"


def test_el_segundo_voto_no_cuenta_y_el_teclado_se_quita_una_vez(con_avisos):
    a = aviso("mapa")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, LUNES, 901)
    con_avisos.bot.recibir_callback(callback(f"sw:util:{a.id}"))
    con_avisos.bot.recibir_callback(callback(f"sw:no:{a.id}"))
    assert [v["voto"] for v in con_avisos.bot.avisos.registro(CAMILA, a.id)["votos"]] == ["util"]
    assert len(con_avisos.bot.tg.sin_teclado) == 1


def test_un_callback_de_alguien_no_autorizado_se_ignora(con_avisos):
    a = aviso("mapa")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, LUNES, 901)
    assert con_avisos.bot.recibir_callback(callback(f"sw:util:{a.id}", usuario="999")) == []
    assert con_avisos.bot.avisos.registro(CAMILA, a.id)["votos"] == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_ajeno_o_viejo_no_rompe(con_avisos):
    assert con_avisos.bot.recibir_callback(callback("otra:cosa")) == []
    assert con_avisos.bot.tg.callbacks == []
    assert con_avisos.bot.recibir_callback(callback("sw:util:inexistente")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "Ese aviso ya no está disponible")]


def test_un_callback_ped_sin_activo_responde_vacio(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo=None)
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)
    assert con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]
    assert con_avisos.bot.cola.qsize() == 0


def test_un_callback_con_avisos_desactivados_responde_vacio(con_avisos):
    con_avisos.bot.avisos = None
    assert con_avisos.bot.recibir_callback(callback("sw:util:inexistente")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_sw_malformado_responde_vacio(con_avisos):
    assert con_avisos.bot.recibir_callback(callback("sw:invalido")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_sin_id_o_prefijo_ajeno_no_responde(con_avisos):
    sin_id = {"update_id": 2, "callback_query": {"from": {"id": int(CAMILA)}, "data": "sw:util:123"}}
    assert con_avisos.bot.recibir_callback(sin_id) == []
    assert con_avisos.bot.tg.callbacks == []


# ───────────────────────────────────────────── el botón de la víspera


def test_el_boton_pide_la_oportunidad_del_activo_y_cuenta_un_clic(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo="USDCLP")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)
    respuestas = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    pedido = con_avisos.bot.cola.get_nowait()
    assert pedido.usuario == CAMILA and pedido.chat == 500
    assert pedido.orden.pieza == "oportunidad" and pedido.orden.args["ticker"] == "USDCLP"
    assert "Recibido" in respuestas[0].texto
    reg = con_avisos.bot.avisos.registro(CAMILA, a.id)
    assert reg["clics_boton"] == 1 and reg["oportunidad_24h"] is False   # el botón no cuenta dos veces


def test_un_pedido_propio_del_mismo_activo_marca_oportunidad_24h(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo="XAUUSD")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, datetime(2026, 10, 8, 9, 0, tzinfo=SCL), 901)
    con_avisos.bot.recibir(update("/oportunidad oro"))     # el reloj de la prueba es el 8/10 a las 11:00
    assert con_avisos.bot.avisos.registro(CAMILA, a.id)["oportunidad_24h"] is True


def test_el_boton_respeta_el_candado_de_un_solo_analisis_por_activo(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo="USDCLP")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)
    con_avisos.bot.avisos.anotar_envio(OTRO, a, MARTES, 902)
    con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    segunda = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}", usuario=OTRO, chat=501))
    assert "Ya se está generando" in segunda[0].texto and con_avisos.bot.cola.qsize() == 1


def test_el_doble_toque_del_boton_responde_al_usuario_y_no_infla_clics(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo="USDCLP")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)

    # Primer toque: se encola y cuenta 1 clic
    resp1 = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    assert "Recibido" in resp1[0].texto
    assert con_avisos.bot.cola.qsize() == 1

    # Segundo toque inmediato (mismo segundo): bot responde informando que ya se genera
    resp2 = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    assert "Ya se está generando" in resp2[0].texto
    assert con_avisos.bot.cola.qsize() == 1

    # La medición solo cuenta 1 clic
    reg = con_avisos.bot.avisos.registro(CAMILA, a.id)
    assert reg["clics_boton"] == 1



# ───────────────────────────────────────────── Telegram real (sin red)


def test_telegram_manda_el_teclado_y_devuelve_el_id_del_mensaje(monkeypatch):
    tg = b.Telegram("token")
    envios = []
    monkeypatch.setattr(tg, "_post", lambda metodo, **kw: envios.append((metodo, kw)) or {"message_id": 42})
    assert tg.mensaje_con_teclado(7, "hola", {"inline_keyboard": []}) == 42
    assert envios[0][0] == "sendMessage" and envios[0][1]["json"]["reply_markup"] == {"inline_keyboard": []}
    tg.quitar_teclado(7, 42)
    assert envios[1][0] == "editMessageReplyMarkup" and envios[1][1]["json"]["message_id"] == 42
    tg.responder_callback("cb", "gracias")
    assert envios[2][0] == "answerCallbackQuery"


def test_el_polling_atiende_los_callbacks(con_avisos):
    a = aviso("mapa")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, LUNES, 901)
    con_avisos.bot.atender_update(callback(f"sw:util:{a.id}"))
    assert con_avisos.bot.avisos.registro(CAMILA, a.id)["votos"]


def test_un_registro_de_avisos_danado_no_bota_el_pedido_de_oportunidad(con_avisos, tmp_path):
    con_avisos.bot.avisos.ruta.write_text("{corrupto", encoding="utf-8")
    respuestas = con_avisos.bot.recibir(update("/oportunidad oro"))
    assert "Recibido" in respuestas[0].texto and con_avisos.bot.cola.qsize() == 1


def test_el_boton_dice_petroleo_con_tilde(con_avisos):
    con_avisos.bot.enviar_aviso(CAMILA, aviso("vispera", activo="WTI.spot"))
    assert "petróleo" in con_avisos.bot.tg.con_teclado[0][2]["inline_keyboard"][0][0]["text"]
