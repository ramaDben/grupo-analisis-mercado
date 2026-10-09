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
    pieza = fx.oportunidad(dir_pedido) if orden.pieza == "oportunidad" else fx.activo(dir_pedido)
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


def pdf_falso(html):
    # Copia el HTML con sufijo .pdf: el test puede leer qué informe se imprimió.
    destino = html.with_suffix(".pdf")
    destino.write_bytes(html.read_bytes())
    return destino


@pytest.fixture
def armado(tmp_path):
    config = {
        "analistas": {CAMILA: {**fx.ANALISTA, "cupo_diario": 2}},
        "reuso_minutos": {"activo": 30}, "tier": "flash",
        "ruta_drive": str(tmp_path / "drive"),
    }
    llamadas = []
    reloj = Reloj()
    at = b.Atendedor(config, b.Estado.cargar(tmp_path / "estado.json"), autor=fx.AUTOR, preparar=preparar_falso,
                     redactar=redactor(llamadas), rendir_laminas=lambda p, d: None, reloj=reloj,
                     dir_pedidos=tmp_path / "pedidos", bitacora=tmp_path / "bitacora.json",
                     vigencia=lambda pieza, ahora: True, a_pdf=pdf_falso)
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


def test_pieza_nueva_se_entrega_en_pdf_y_solo_el_pdf_va_a_drive(armado):
    _, final = pedir(armado, "/activo oro")
    assert len(final.archivos) == 1 and final.archivos[0].suffix == ".pdf"
    assert "aviso de prueba" in final.texto
    assert len(armado.llamadas) == 1
    en_drive = list((armado.tmp / "drive" / "GI Informes").rglob("*.*"))
    assert [p.suffix for p in en_drive] == [".pdf"]
    # El HTML queda como fuente junto a la pieza, pero no circula.
    assert final.archivos[0].with_suffix(".html").exists()


def test_pieza_reusada_tambien_sale_en_pdf(armado):
    pedir(armado, "/activo oro")
    armado.reloj.ahora += timedelta(minutes=10)
    _, final = pedir(armado, "/activo oro")
    assert "vigente" in final.texto and final.archivos[0].suffix == ".pdf"


def test_si_el_pdf_falla_va_el_html_solo_por_telegram(armado):
    from analista import pdf

    def pdf_roto(html):
        raise pdf.PdfFallido("Chromium no generó el PDF: TimeoutError")

    armado.bot.atendedor.a_pdf = pdf_roto
    _, final = pedir(armado, "/activo oro")
    assert [p.suffix for p in final.archivos] == [".html"]
    assert "No pude generar el PDF" in final.texto and "navegador" in final.texto
    assert not (armado.tmp / "drive").exists() or not list((armado.tmp / "drive").rglob("*.*"))


@pytest.mark.parametrize("nombre,tipo", [("informe.pdf", "application/pdf"), ("informe.html", "text/html")])
def test_telegram_manda_el_tipo_segun_el_archivo(tmp_path, nombre, tipo):
    ruta = tmp_path / nombre
    ruta.write_bytes(b"x")
    tg = b.Telegram("token")
    enviados = []
    tg._post = lambda metodo, **kw: enviados.append(kw["files"]["document"])
    tg.documento(1, ruta)
    assert enviados[0][0] == nombre and enviados[0][2] == tipo


def test_segundo_pedido_reusa_la_pieza_sin_agy_ni_cupo(armado):
    pedir(armado, "/activo oro")
    armado.reloj.ahora += timedelta(minutes=10)
    _, final = pedir(armado, "/activo oro")
    assert len(armado.llamadas) == 1
    assert "vigente" in final.texto
    assert armado.bot.estado.usados(CAMILA, armado.reloj.ahora) == 1


def test_pedido_con_para_no_gasta_agy_ni_cupo(armado):
    from analista import orden as od

    r, final = pedir(armado, "/activo oro para Juan Pérez")
    assert r[0].texto == od.PERSONALIZACION_RETIRADA and final is None
    assert armado.llamadas == [] and armado.bot.estado.usados(CAMILA, armado.reloj.ahora) == 0


def test_pieza_reusada_usa_la_fecha_del_pedido(armado):
    armado.reloj.ahora = datetime(2028, 3, 31, 23, 50, tzinfo=SCL)
    _, primero = pedir(armado, "/activo oro")
    assert "A-32915" in primero.archivos[0].read_text(encoding="utf-8")
    armado.reloj.ahora = datetime(2028, 4, 1, 0, 5, tzinfo=SCL)
    _, segundo = pedir(armado, "/activo oro")
    assert "vigente" in segundo.texto and len(armado.llamadas) == 1
    assert "A-32915" not in segundo.archivos[0].read_text(encoding="utf-8")
    assert "venció" in segundo.texto


def test_activo_nuevo_queda_en_la_bitacora_y_el_reusado_no(armado):
    pedir(armado, "/activo oro")
    armado.reloj.ahora += timedelta(minutes=5)
    pedir(armado, "/activo oro")
    entradas = json.loads((armado.tmp / "bitacora.json").read_text(encoding="utf-8"))
    assert len(entradas) == 1 and entradas[0]["analista"] == CAMILA


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
    from analista import autor as au

    assert au.cargar(config, RAIZ).nombre
    json.dumps(config)


def test_config_anterior_al_foco_recibe_su_ventana(tmp_path):
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps({"reuso_minutos": {"activo": 45}}), encoding="utf-8")
    cfg = b.cargar_config(ruta)
    assert cfg["reuso_minutos"]["activo"] == 45 and cfg["reuso_minutos"]["oportunidad"] == 60


# ───────────────────────────────────────────────────────────── foco técnico


def test_foco_se_entrega_con_la_regla_de_compartir_y_sin_la_palabra_en_el_archivo(armado):
    r, final = pedir(armado, "/oportunidad")
    assert final is not None, [x.texto for x in r]
    assert final.archivos, final.texto
    nombre = final.archivos[0].name
    assert nombre.startswith("foco-tecnico_xauusd") and "oportunidad" not in nombre
    assert "Compártelo tal cual: es análisis general, no una instrucción." in final.texto


@pytest.mark.parametrize("error", [pr.SinFocoError("El escáner no encontró una configuración clara entre los 10 activos."),
                                   pr.MercadoIlegibleError("No puedo leer el mercado ahora (MT5). Prueba en unos minutos.")])
def test_sin_foco_o_mercado_ilegible_no_gastan_agy_ni_cupo(armado, error):
    def falla(orden, d, a):
        raise error

    armado.bot.atendedor.preparar = falla
    _, final = pedir(armado, "/oportunidad")
    assert final.texto == f"❌ {error}" and not final.archivos
    assert armado.llamadas == [] and armado.bot.estado.usados(CAMILA, AHORA) == 0


def test_foco_vigente_se_reusa_con_su_hora(armado):
    pedir(armado, "/oportunidad")
    armado.reloj.ahora += timedelta(minutes=20)
    _, final = pedir(armado, "/oportunidad")
    assert len(armado.llamadas) == 1 and "Ya está: es el foco de las 10:40." in final.texto


def test_foco_cuyo_plan_cambio_se_rehace(armado):
    pedir(armado, "/oportunidad")
    armado.bot.atendedor.vigencia = lambda pieza, ahora: False
    armado.reloj.ahora += timedelta(minutes=20)
    pedir(armado, "/oportunidad")
    assert len(armado.llamadas) == 2


def test_bitacora_marca_el_tipo(armado):
    pedir(armado, "/oportunidad")
    pedir(armado, "/activo oro")
    entradas = json.loads((armado.tmp / "bitacora.json").read_text(encoding="utf-8"))
    assert [e["tipo"] for e in entradas] == ["oportunidad", "activo"]
