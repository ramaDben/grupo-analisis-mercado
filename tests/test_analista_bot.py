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
from analista import orden as od  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista import registro_semanal as rg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)
CAMILA = "111"
OTRO = "222"


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


class Armado:
    """Lo que las pruebas necesitan del bot: sus piezas y los contadores de lo que hizo."""

    def __init__(self, tmp_path, config):
        self.llamadas, self.reloj, self.tmp = [], Reloj(), tmp_path
        self.preparaciones = 0
        self.registro = tmp_path / "registro.json"
        self.atendedor = b.Atendedor(
            config, b.Estado.cargar(tmp_path / "estado.json"), autor=fx.AUTOR, preparar=self.preparar_falso,
            redactar=redactor(self.llamadas), rendir_lamina=self.rendir_falso, reloj=self.reloj,
            dir_pedidos=tmp_path / "pedidos", registro=self.registro)
        self.bot = b.Bot(TgFalso(), self.atendedor)
        self.estado = self.atendedor.estado

    def preparar_falso(self, orden, dir_pedido, ahora):
        self.preparaciones += 1
        dir_pedido.mkdir(parents=True, exist_ok=True)
        if orden.pieza == "oportunidad":
            pieza = fx.pieza_oportunidad(dir_pedido)
            pieza["editorial"] = {k: ({t: es.MARCA for t in v} if isinstance(v, dict) else es.MARCA)
                                  for k, v in pieza["editorial"].items()}
        else:
            pieza = fx.pieza_seguimiento(dir_pedido)
        pr.guardar_pieza(pieza, dir_pedido)
        return pr.Preparada(pieza, ["aviso de prueba"])

    @staticmethod
    def rendir_falso(payload, plantilla, destino):
        destino.write_bytes(fx.PNG)
        return destino


def redactor(llamadas, codigo="ok"):
    def redactar(ruta, tier):
        llamadas.append(ruta)
        if codigo != "ok":
            return SimpleNamespace(codigo=codigo, detalle="algo")
        dir_pedido = ruta.parent
        pieza = pr.cargar_pieza(dir_pedido)
        pieza["editorial"].update(fx.pieza_oportunidad(dir_pedido)["editorial"])
        pr.guardar_pieza(pieza, dir_pedido)
        return SimpleNamespace(codigo="ok", detalle="")
    return redactar


@pytest.fixture
def armado(tmp_path):
    config = {
        "analistas": {CAMILA: {**fx.ANALISTA, "cupo_diario": 2},
                      OTRO: {"nombre": "Pedro Soto", "cargo": "Ejecutivo comercial", "contacto": "+56 9 3333 4444",
                             "cupo_diario": 2}},
        "reuso_minutos": {"seguimiento": 30}, "tier": "flash",
        "ruta_drive": str(tmp_path / "drive"),
    }
    return Armado(tmp_path, config)


def update(texto, usuario=CAMILA, chat=500):
    return {"update_id": 1, "message": {"chat": {"id": chat}, "from": {"id": int(usuario)}, "text": texto}}


def pedir(a, texto, usuario=CAMILA):
    respuestas = a.bot.recibir(update(texto, usuario))
    if a.bot.cola.empty():
        return respuestas, None
    return respuestas, a.bot.procesar_uno(a.bot.cola.get())


def test_desconocido_recibe_su_id_una_sola_vez(armado):
    r1 = armado.bot.recibir(update("/seguimiento oro", usuario="999"))
    r2 = armado.bot.recibir(update("/seguimiento oro", usuario="999"))
    assert "999" in r1[0].texto and r2 == []
    assert armado.bot.cola.empty()


def test_pedido_invalido_responde_el_motivo(armado):
    r, final = pedir(armado, "/seguimiento pizza")
    assert "pizza" in r[0].texto and final is None


def test_pedido_con_para_no_gasta_agy_ni_cupo(armado):
    r, final = pedir(armado, "/oportunidad para Juan Pérez")
    assert r[0].texto == od.PERSONALIZACION_RETIRADA and final is None
    assert armado.llamadas == [] and armado.estado.usados(CAMILA, armado.reloj.ahora) == 0


@pytest.mark.parametrize("retirado", ["/activo oro", "/calendario hoy", "/dato ipc", "/jornada apertura"])
def test_los_comandos_retirados_responden_con_la_ayuda(armado, retirado):
    r, final = pedir(armado, retirado)
    assert r[0].texto == b.AYUDA and final is None


@pytest.mark.parametrize("nombre,tipo", [("a.pdf", "application/pdf"), ("a.html", "text/html"),
                                         ("a.png", "image/png")])
def test_telegram_manda_el_tipo_segun_el_archivo(tmp_path, nombre, tipo):
    ruta = tmp_path / nombre
    ruta.write_bytes(b"x")
    tg = b.Telegram("token")
    enviados = []
    tg._post = lambda metodo, **kw: enviados.append(kw["files"]["document"])
    tg.documento(1, ruta)
    assert enviados[0][0] == nombre and enviados[0][2] == tipo


# ───────────────────────────────────────────────────────────── /oportunidad


def test_oportunidad_arma_la_foto_una_sola_vez_por_semana(armado):
    r1 = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    r2 = armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("oportunidad")))
    assert len(armado.llamadas) == 1  # AGY una sola vez
    assert r1.archivos[0].name.startswith("analisis-semanal_")
    assert r2.archivos[0].name.endswith("_pedro-soto.html")  # el HTML lleva al ejecutivo que lo pidió
    assert "Ya está" in r2.texto
    # El cupo se gasta al armar la foto, no al reusarla.
    assert armado.estado.usados(CAMILA, AHORA) == 1 and armado.estado.usados(OTRO, AHORA) == 0


def test_oportunidad_rinde_las_laminas_antes_del_html(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    html = r.archivos[0].read_text(encoding="utf-8")
    assert html.count("Descargar lámina") >= 2
    assert (r.archivos[0].parent / "lamina_xauusd.png").exists()


def test_la_lamina_del_wti_aparece_en_el_html(armado):
    def con_wti(orden, dir_pedido, ahora, **kw):
        dir_pedido.mkdir(parents=True, exist_ok=True)
        pieza = fx.pieza_oportunidad(dir_pedido, wti=True)
        pr.guardar_pieza(pieza, dir_pedido)
        return pr.Preparada(pieza, [])

    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"] = fx.pieza_oportunidad(ruta.parent, wti=True)["editorial"]
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.preparar, armado.atendedor.redactar = con_wti, redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    html = r.archivos[0].read_text(encoding="utf-8")
    assert 'download="lamina_wti_spot.png"' in html


def test_oportunidad_solo_va_a_drive_el_html(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    en_drive = list((armado.tmp / "drive" / "GI Informes").rglob("*.*"))
    assert [p.suffix for p in en_drive] == [".html"]


def test_oportunidad_sin_semana_responde_claro_y_no_gasta_cupo(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(
        pr.SinSemanaError("La semana 2026-W42 todavía no tiene análisis semanal"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert r.texto.startswith("❌ La semana") and armado.estado.usados(CAMILA, AHORA) == 0


def test_oportunidad_en_espera_da_la_hora_del_cierre(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(
        pr.EsperaVelaError("se publica al cierre de la vela de las 13:00"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "13:00" in r.texto and armado.llamadas == []


def test_agy_sin_responder_no_gasta_cupo(armado):
    armado.atendedor.redactar = redactor([], codigo="timeout")
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "No gasté tu cupo" in r.texto and not r.archivos
    assert armado.estado.usados(CAMILA, AHORA) == 0
    assert not armado.registro.exists()  # sin foto anotada, el próximo pedido vuelve a intentar


def test_texto_invalido_de_agy_no_sale(armado):
    def redactar_mal(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["contexto"]["XAUUSD"] = "El objetivo es 9.999,00, una oportunidad con 3 %"
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar_mal
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "controles" in r.texto and not r.archivos
    assert armado.estado.usados(CAMILA, AHORA) == 0


def test_datos_que_no_estan_no_gastan_agy(armado):
    def sin_datos(orden, d, a):
        raise pr.PreparacionFallida("el terminal no entregó XAUUSD")

    armado.atendedor.preparar = sin_datos
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "XAUUSD" in r.texto and armado.llamadas == []


def test_cupo_diario(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "COPPER"})))
    assert "cupo" in r.texto and not r.archivos
    assert armado.preparaciones == 2


# ───────────────────────────────────────────────────────────── /seguimiento


def test_seguimiento_entrega_lamina_y_texto_sin_agy(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.llamadas == [] and "Te envío una actualización" in r.texto
    assert r.archivos[0].suffix == ".png"


def test_seguimiento_se_reusa_30_minutos(armado):
    o = od.Orden("seguimiento", {"ticker": "XAUUSD"})
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    armado.reloj.ahora += timedelta(minutes=20)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 1
    armado.reloj.ahora += timedelta(minutes=15)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 2


def test_seguimiento_queda_anotado_en_la_foto_de_la_semana(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    import referencia_semanal as rs

    semana = rs.semana_de(AHORA)
    seg = rg.foto(semana, armado.registro)["seguimientos"]
    assert [(s["ticker"], s["estado"], s["ejecutivo"]) for s in seg] == [("XAUUSD", "en_curso", OTRO)]


@pytest.mark.parametrize("error", [pr.SinFotoError("Esta semana todavía no hay análisis publicado."),
                                   pr.FueraDeLaFotoError("Ese activo no está en el análisis de esta semana.")])
def test_seguimiento_sin_foto_o_fuera_de_ella_no_gasta_cupo(armado, error):
    def falla(orden, d, a):
        raise error

    armado.atendedor.preparar = falla
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert r.texto == f"❌ {error}" and armado.estado.usados(CAMILA, AHORA) == 0


def test_mt5_caido_en_seguimiento_lo_dice(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(
        pr.PreparacionFallida("no uso el terminal: MT5 no conectó"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert "MT5" in r.texto


def test_la_ayuda_nombra_solo_los_dos_comandos():
    assert "/oportunidad" in b.AYUDA and "/seguimiento" in b.AYUDA
    for retirado in ("/activo", "/calendario", "/dato", "/jornada"):
        assert retirado not in b.AYUDA
    assert "—" not in b.AYUDA and "–" not in b.AYUDA


def test_estado_muestra_el_cupo(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    r, _ = pedir(armado, "/estado")
    assert "1 de 2" in r[0].texto


def test_cola_avisa_la_posicion(armado):
    armado.bot.recibir(update("/seguimiento oro"))
    r = armado.bot.recibir(update("/seguimiento wti"))
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
    assert set(config["reuso_minutos"]) == {"seguimiento"}
    from analista import autor as au

    assert au.cargar(config, RAIZ).nombre
    json.dumps(config)


def test_config_anterior_recibe_su_ventana(tmp_path):
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps({"reuso_minutos": {"activo": 45}}), encoding="utf-8")
    assert b.cargar_config(ruta)["reuso_minutos"]["seguimiento"] == 30
    ruta.write_text(json.dumps({"reuso_minutos": {"seguimiento": 45}}), encoding="utf-8")
    assert b.cargar_config(ruta)["reuso_minutos"]["seguimiento"] == 45


def _tomar_en_otro_proceso(ruta: Path) -> bool:
    """El candado es por proceso: la segunda instancia tiene que ser otro proceso."""
    import subprocess

    codigo = (f"import sys; sys.path.insert(0, {str(RAIZ / 'scripts')!r}); "
              "from pathlib import Path; from analista import bot; "
              f"print(bot.tomar_instancia(Path({str(ruta)!r})) is not None)")
    salida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=True)
    return salida.stdout.strip() == "True"


def test_un_segundo_bot_no_arranca_mientras_el_primero_escucha(tmp_path):
    # Un reinicio que dejó vivo al bot anterior armaba dos bots tomando los pedidos
    # al azar, y el huérfano sin consola no podía dibujar el gráfico.
    ruta = tmp_path / ".bot_analistas.lock"
    primero = b.tomar_instancia(ruta)
    assert primero is not None
    assert _tomar_en_otro_proceso(ruta) is False
    primero.close()
    # Cerrado (o muerto) el primero, el candado queda libre: no hay candados huérfanos.
    assert _tomar_en_otro_proceso(ruta) is True
