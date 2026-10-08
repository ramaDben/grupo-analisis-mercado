"""El bot de analistas con Telegram, agy y el terminal simulados."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import bot as b  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import preparar as pr  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)
CAMILA = "111"


class Reloj:
    def __init__(self):
        self.ahora = AHORA

    def __call__(self):
        return self.ahora


class TgFalso:
    def __init__(self):
        self.mensajes, self.documentos = [], []

    def mensaje(self, chat, texto):
        self.mensajes.append((chat, texto))

    def documento(self, chat, ruta):
        self.documentos.append((chat, Path(ruta).name))


def preparar_falso(orden, dir_pedido, ahora):
    dir_pedido.mkdir(parents=True, exist_ok=True)
    pieza = fx.activo(dir_pedido)
    pieza["editorial"] = {k: es.MARCA for k in pieza["editorial"]}
    pr.guardar_pieza(pieza, dir_pedido)
    return pr.Preparada(pieza, ["aviso de prueba"])


def redactor(llamadas, codigo="ok"):
    def redactar(ruta, tier):
        llamadas.append(ruta)
        if codigo != "ok":
            return SimpleNamespace(codigo=codigo, detalle="algo")
        dir_pedido = ruta.parent
        pieza = pr.cargar_pieza(dir_pedido)
        pieza["editorial"].update(fx.activo(dir_pedido)["editorial"])
        pr.guardar_pieza(pieza, dir_pedido)
        return SimpleNamespace(codigo="ok", detalle="")
    return redactar


@pytest.fixture
def armado(tmp_path):
    config = {
        "analistas": {CAMILA: {**fx.ANALISTA, "cupo_diario": 2}},
        "reuso_minutos": {"activo": 30}, "tier": "flash",
        "ruta_drive": str(tmp_path / "drive"),
    }
    llamadas = []
    reloj = Reloj()
    at = b.Atendedor(config, b.Estado.cargar(tmp_path / "estado.json"), preparar=preparar_falso,
                     redactar=redactor(llamadas), rendir_laminas=lambda p, d: None, reloj=reloj,
                     dir_pedidos=tmp_path / "pedidos")
    bot = b.Bot(TgFalso(), at)
    return SimpleNamespace(bot=bot, llamadas=llamadas, reloj=reloj, tmp=tmp_path)


def update(texto, usuario=CAMILA, chat=500):
    return {"update_id": 1, "message": {"chat": {"id": chat}, "from": {"id": int(usuario)}, "text": texto}}


def pedir(a, texto, usuario=CAMILA):
    respuestas = a.bot.recibir(update(texto, usuario))
    if a.bot.cola.empty():
        return respuestas, None
    return respuestas, a.bot.procesar_uno(a.bot.cola.get())


def test_desconocido_recibe_su_id_una_sola_vez(armado):
    r1 = armado.bot.recibir(update("/activo oro", usuario="999"))
    r2 = armado.bot.recibir(update("/activo oro", usuario="999"))
    assert "999" in r1[0].texto and r2 == []
    assert armado.bot.cola.empty()


def test_pedido_invalido_responde_el_motivo(armado):
    r, final = pedir(armado, "/activo pizza")
    assert "pizza" in r[0].texto and final is None


def test_pieza_nueva_genera_generica_y_dedicada_y_copia_a_drive(armado):
    _, final = pedir(armado, "/activo oro para María José Núñez")
    nombres = [p.name for p in final.archivos]
    assert nombres[0].endswith("_maria_jose_nunez.html") and len(nombres) == 2
    assert "María José Núñez" in final.texto and "aviso de prueba" in final.texto
    assert len(armado.llamadas) == 1
    assert len(list((armado.tmp / "drive" / "GI Informes").rglob("*.html"))) == 2


def test_otro_trader_reusa_la_pieza_sin_agy_ni_cupo(armado):
    pedir(armado, "/activo oro para Juan Pérez")
    armado.reloj.ahora += timedelta(minutes=10)
    _, final = pedir(armado, "/activo oro para Ana Soto")
    assert len(armado.llamadas) == 1
    assert "vigente" in final.texto
    assert armado.bot.estado.usados(CAMILA, armado.reloj.ahora) == 1


def test_pieza_vencida_se_vuelve_a_redactar(armado):
    pedir(armado, "/activo oro")
    armado.reloj.ahora += timedelta(minutes=31)
    pedir(armado, "/activo oro")
    assert len(armado.llamadas) == 2


def test_cupo_diario(armado):
    pedir(armado, "/activo oro")
    pedir(armado, "/activo usdclp")
    _, final = pedir(armado, "/activo wti")
    assert "cupo" in final.texto and not final.archivos
    assert len(armado.llamadas) == 2


def test_agy_falla_no_gasta_cupo_ni_entrega(armado):
    armado.bot.atendedor.redactar = redactor(armado.llamadas, codigo="timeout")
    _, final = pedir(armado, "/activo oro")
    assert "timeout" in final.texto and not final.archivos
    assert armado.bot.estado.usados(CAMILA, AHORA) == 0


def test_texto_invalido_de_agy_no_sale(armado):
    def redactar_mal(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.activo(ruta.parent)["editorial"])
        pieza["editorial"]["lectura"] = "El objetivo es 4.500,00 — <b>seguro</b>"
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.bot.atendedor.redactar = redactar_mal
    _, final = pedir(armado, "/activo oro")
    assert "controles" in final.texto and not final.archivos


def test_datos_que_no_estan_no_gastan_agy(armado):
    def sin_datos(orden, d, a):
        raise pr.PreparacionFallida("el terminal no entregó XAUUSD")

    armado.bot.atendedor.preparar = sin_datos
    _, final = pedir(armado, "/activo oro")
    assert "XAUUSD" in final.texto and armado.llamadas == []


def test_estado_muestra_el_cupo(armado):
    pedir(armado, "/activo oro")
    r, _ = pedir(armado, "/estado")
    assert "1 de 2" in r[0].texto


def test_cola_avisa_la_posicion(armado):
    armado.bot.recibir(update("/activo oro"))
    r = armado.bot.recibir(update("/activo wti"))
    assert "1 pedido" in r[0].texto


def test_el_bot_no_puede_publicar_en_whatsapp():
    """Mismo criterio que el reloj (tests/test_reloj_gi.py): es interno del equipo."""
    fuentes = [*(RAIZ / "scripts" / "analista").glob("*.py"), RAIZ / "scripts" / "bot_analistas.py"]
    for ruta in fuentes:
        texto = ruta.read_text(encoding="utf-8")
        for prohibido in ("enviar_whatsapp", "whatsapp_sender", "--despachar", "despachar(",
                          "bitacora_despachos", "historial_despachos"):
            assert prohibido not in texto, f"{ruta.name} toca el envío: {prohibido}"


def test_config_de_ejemplo_es_valida():
    config = b.cargar_config(RAIZ / "config" / "analistas_telegram.example.json")
    for datos in config["analistas"].values():
        assert {"nombre", "cargo", "contacto", "cupo_diario"} <= set(datos)
    assert set(config["reuso_minutos"]) == set(es.CAMPOS)
    json.dumps(config)
