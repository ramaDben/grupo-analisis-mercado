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
from analista import fuentes as fu  # noqa: E402
from analista import orden as od  # noqa: E402
from analista import pdf  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista import simbolos as sm  # noqa: E402
from analista import registro_semanal as rg  # noqa: E402
from analista import segmentos as sg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)
CAMILA = "111"
OTRO = "222"
ORO = od.Orden("oportunidad", {"ticker": "XAUUSD"})


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
        self.caduca: str | None = None
        self.aviso_vigencia: str | None = None
        self.eventos: list[dict] = []  # el calendario falso: vacío salvo que la prueba lo llene
        self.registro = tmp_path / "registro.json"
        self.reintentos: list = []
        self.tasa: dict | None = None  # `datos.tasa` sellado por el preparar falso
        self.generadas: list = []
        self.generar_falla = False
        self.atendedor = b.Atendedor(
            config, b.Estado.cargar(tmp_path / "estado.json"), autor=fx.AUTOR, preparar=self.preparar_falso,
            redactar=redactor(self.llamadas), redactar_fuentes=self.redactar_fuentes_falso, rendir_lamina=self.rendir_falso, a_pdf=self.pdf_falso, reloj=self.reloj,
            dir_pedidos=tmp_path / "pedidos", registro=self.registro,
            calendario=lambda ahora: self.eventos,
            verificar_vigencia=lambda pieza, ahora: (self.caduca, self.aviso_vigencia),
            simbolo=lambda t: {"ticker": "XAUUSD", "descripcion": "Gold", "digits": 2} if t.lower() == "xauusd" else None,
            verificar_url=lambda url: "ok", publicar_imagen=None,
            leer_nota=lambda url: "", generar_imagen=self.generar_falso, banco_imagenes=tmp_path / "banco")
        self.candidatas_contexto = list(CANDIDATAS_CONTEXTO_FALSO)
        self.atendedor.noticias_contexto = lambda t, n, ah: (list(self.candidatas_contexto), [])
        self.bot = b.Bot(TgFalso(), self.atendedor)
        self.estado = self.atendedor.estado

    def generar_falso(self, prompt, destino):
        if self.generar_falla:
            raise b.gi.ImagenNoGenerada("sin agy")
        self.generadas.append(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(fx.PNG)
        return destino

    def redactar_fuentes_falso(self, ruta, tier):
        """Por defecto el segundo intento no escribe nada: cada prueba que lo usa lo reemplaza."""
        self.reintentos.append(ruta)
        return SimpleNamespace(codigo="ok", detalle="")

    def preparar_falso(self, orden, dir_pedido, ahora, **kw):
        self.preparaciones += 1
        self.kwargs = kw
        dir_pedido.mkdir(parents=True, exist_ok=True)
        if orden.pieza == "oportunidad":
            pieza = fx.pieza_oportunidad(dir_pedido)
            pieza["editorial"] = {k: ({t: es.MARCA for t in v} if isinstance(v, dict) else es.MARCA)
                                  for k, v in pieza["editorial"].items()}
            if self.tasa is not None:
                pieza["datos"]["tasa"] = self.tasa
                pieza["huella"] = es._huella(pieza)
        else:
            pieza = fx.pieza_seguimiento(dir_pedido)
            pieza["datos"]["suceso"] = {
                "estado": "en_nivel",
                "sentido": "ALCISTA",
                "nivel": 4150.0,
                "objetivo": 4200.0,
                "siguiente": None,
                "calidad": "A+",
                "nota_semana": "",
            }
        pr.guardar_pieza(pieza, dir_pedido)
        return pr.Preparada(pieza, ["aviso de prueba"])

    @staticmethod
    def pdf_falso(html):
        destino = html.with_suffix(".pdf")
        destino.write_bytes(b"%PDF-1.4 falso")
        return destino

    @staticmethod
    def rendir_falso(payload, plantilla, destino):
        destino.write_bytes(fx.PNG)
        return destino


CANDIDATAS_CONTEXTO_FALSO = [
    {
        "medio": "FXStreet",
        "fecha": "2026-10-07",
        "url": "https://www.fxstreet.es/markets/oro-sube-1",
        "titular_original": "El oro sube con fuerza",
    },
    {
        "medio": "Investing.com",
        "fecha": "2026-10-07",
        "url": "https://es.investing.com/news/oro-en-maximos-2",
        "titular_original": "Oro alcanza nuevos máximos",
    },
]

def redactor(llamadas, codigo="ok"):
    def redactar(ruta, tier):
        llamadas.append(ruta)
        if codigo != "ok":
            return SimpleNamespace(codigo=codigo, detalle="algo")
        dir_pedido = ruta.parent
        pieza = pr.cargar_pieza(dir_pedido)
        if pieza.get("orden", {}).get("pieza") == "contexto":
            pieza["editorial"]["noticia_1"] = {
                "medio": "FXStreet",
                "fecha": "2026-10-07",
                "url": "https://www.fxstreet.es/markets/oro-sube-1",
                "titular_original": "El oro sube con fuerza",
                "titular": "El oro sube con fuerza",
                "mensaje": "[[SALUDO]] El oro mantiene tendencia alcista. ¿Cómo ves tu posición?",
            }
            pieza["editorial"]["noticia_2"] = {
                "medio": "Investing.com",
                "fecha": "2026-10-07",
                "url": "https://es.investing.com/news/oro-en-maximos-2",
                "titular_original": "Oro alcanza nuevos máximos",
                "titular": "Oro alcanza nuevos máximos",
                "mensaje": "[[SALUDO]] La demanda por refugio impulsa al oro. ¿Te interesa?",
            }
            pieza["editorial"]["tecnico"] = (
                "[[SALUDO]] El oro mantiene sesgo alcista vigilando [[NIVEL]] con objetivo en [[OBJETIVO]]. "
                "¿Ajustamos la orden?"
            )
        else:
            pieza["editorial"].update(fx.pieza_oportunidad(dir_pedido)["editorial"])
            # La fuente del ejemplo es posterior al reloj de estas pruebas: con su fecha, depurar la descarta.
            pieza["editorial"]["fuentes"] = [dict(fx.DIRECTA_ORO), {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}]
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
    r, final = pedir(armado, "/seguimiento")
    assert r[0].texto and final is None and armado.bot.cola.empty()


def test_un_activo_desconocido_se_resuelve_en_el_trabajador(armado):
    r, final = pedir(armado, "/seguimiento pizza")
    assert "Recibido" in r[0].texto and "pizza" in final.texto and armado.llamadas == []


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


def test_oportunidad_se_arma_una_vez_y_el_segundo_ejecutivo_lo_reusa(armado):
    r1 = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    r2 = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert len(armado.llamadas) == 1 and armado.preparaciones == 1  # agy una sola vez
    assert r1.archivos[1].name.startswith("analisis_xauusd_")
    assert r2.archivos[1].name.endswith("_pedro-soto.html")  # el HTML lleva al ejecutivo que lo pidió
    assert "Camila Rojas" in r2.aparte and "Ya existía" in r2.aparte
    assert armado.estado.usados(CAMILA, AHORA) == 1 and armado.estado.usados(OTRO, AHORA) == 0


def test_el_analisis_queda_a_nombre_de_quien_lo_genero_y_anota_el_reuso(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    e = rg.vigente("XAUUSD", AHORA, armado.registro)
    assert e["creado_por"] == {"nombre": "Camila Rojas", "id": CAMILA}
    assert [x["nombre"] for x in e["reusos"]] == ["Pedro Soto"]


def test_a_los_8_dias_se_rehace(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.reloj.ahora += timedelta(days=8)
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 2 and len(armado.llamadas) == 2


def test_a_los_6_dias_se_reusa(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.reloj.ahora += timedelta(days=6)
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 1


def test_pasado_un_dia_clave_de_su_agenda_el_analisis_no_se_reusa(armado):
    """Su agenda se redactó en modo anticipación: con un dato ya pasado diría «pendiente» lo que ya salió."""
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))  # su único día clave es el 14/10
    armado.reloj.ahora = AHORA + timedelta(days=6)  # 14/10: el día clave es hoy, aún no pasó
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 1
    armado.reloj.ahora = AHORA + timedelta(days=6, hours=23)  # 15/10 10:00: el registro sigue vigente, el dato no
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 3, ORO))
    assert armado.preparaciones == 2 and "caducó" in r.aparte and "días clave" in r.aparte
    assert "Ya existía" not in r.aparte


def test_una_lectura_rota_caduca_el_analisis_y_se_rehace_con_el_motivo(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.caduca = "el precio tocó la invalidación"
    r = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 2 and "caducó" in r.aparte and "invalidación" in r.aparte
    assert json.loads(armado.registro.read_text(encoding="utf-8"))[0]["caducada"]["motivo"]


def test_con_el_terminal_caido_se_entrega_el_vigente_con_aviso(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.aviso_vigencia = "No pude verificar si sigue vigente (el terminal no respondió): te lo entrego tal cual."
    r = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 1 and "No pude verificar si sigue vigente" in r.aparte


def test_el_texto_reenviable_invita_a_revisar_mt5_con_el_saludo(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "XAUUSD"}, "Juan")))
    assert r.texto.startswith("Hola Juan, ") and "MT5" in r.texto and "operar" not in r.texto.lower()


def test_las_fuentes_malas_se_descartan_y_se_avisan_sin_botar_la_pieza(armado):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        buena = {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}  # la del ejemplo es posterior al reloj del test
        pieza["editorial"]["fuentes"] = [dict(fx.DIRECTA_ORO), buena, {**buena, "entidad": "Un Blog",
                                                 "url": "https://www.reuters.com/otra/nota-larga"}]
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "Un Blog" in r.aparte and r.archivos
    assert len(pr.cargar_pieza(next((armado.tmp / "pedidos").rglob("pieza.json")).parent)["editorial"]["fuentes"]) == 2


def test_sin_voces_validas_ni_en_el_reintento_no_sale_ni_gasta_cupo(armado):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["fuentes"] = "no sé"
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and "noticia directa" in r.texto and "No gasté tu cupo" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 0 and rg.vigente("XAUUSD", AHORA, armado.registro) is None
    assert len(armado.reintentos) == 1


def test_un_simbolo_libre_se_canoniza_contra_el_terminal(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "xauusd", "libre": True})))
    assert rg.vigente("XAUUSD", AHORA, armado.registro) is not None


def test_un_simbolo_que_no_existe_no_gasta_cupo_ni_agy(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "orro", "libre": True})))
    assert "orro" in r.texto and armado.llamadas == [] and armado.estado.usados(CAMILA, AHORA) == 0


def test_un_terminal_caido_al_confirmar_el_simbolo_se_dice_y_no_gasta_cupo(armado):
    def caido(texto):
        raise sm.TerminalNoDisponible("MT5 no respondió")

    armado.atendedor.simbolo = caido
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "xauusd", "libre": True})))
    assert "No pude consultar el terminal" in r.texto and armado.estado.usados(CAMILA, AHORA) == 0


def test_el_mismo_activo_pedido_dos_veces_a_la_vez_dice_que_ya_se_esta_generando(armado):
    r1 = armado.bot.recibir(update("/oportunidad oro"))
    r2 = armado.bot.recibir(update("/oportunidad oro", usuario=OTRO))
    assert "Armando el análisis" in r1[0].texto and "ya se está generando" in r2[0].texto.lower()
    assert armado.bot.cola.qsize() == 1
    armado.bot.procesar_uno(armado.bot.cola.get())  # al terminar, el candado se suelta
    assert "ya se está generando" not in armado.bot.recibir(update("/oportunidad oro"))[0].texto.lower()


def test_oportunidad_va_a_drive_por_sector_activo_y_fecha(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    dia = armado.tmp / "drive" / "GI Informes" / "Commodities" / "Oro (XAUUSD)" / AHORA.date().isoformat()
    assert sorted(p.suffix for p in dia.iterdir()) == [".html", ".pdf"]


def test_oportunidad_entrega_html_y_pdf(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert sorted(p.suffix for p in r.archivos) == [".html", ".pdf"]


def test_sin_pdf_igual_entrega_el_html_y_avisa(armado):
    def falla(html):
        raise pdf.PdfFallido("Chromium no generó el PDF")
    armado.atendedor.a_pdf = falla
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert [p.suffix for p in r.archivos] == [".html"] and "No pude generar el PDF" in r.aparte
    assert armado.estado.usados(CAMILA, AHORA) == 1  # el cupo se gasta una sola vez


def test_un_fallo_inesperado_del_pdf_igual_entrega_el_html(armado):
    def falla(html):
        raise RuntimeError("algo raro")
    armado.atendedor.a_pdf = falla
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert [p.suffix for p in r.archivos] == [".html"] and "No pude generar el PDF" in r.aparte
    assert armado.estado.usados(CAMILA, AHORA) == 1


def test_seguimiento_deja_su_lamina_en_drive(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    dia = armado.tmp / "drive" / "GI Informes" / "Commodities" / "Oro (XAUUSD)" / AHORA.date().isoformat()
    assert f"seguimiento_xauusd_{AHORA:%H%M}.png" in [p.name for p in dia.iterdir()]


def test_oportunidad_rinde_la_lamina_antes_del_html(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "Descargar lámina" in r.archivos[1].read_text(encoding="utf-8")
    assert (r.archivos[0].parent / "lamina_xauusd.png").exists()


def test_oportunidad_sin_analisis_de_datos_no_gasta_agy(armado):
    armado.atendedor.preparar = lambda o, d, a, **kw: (_ for _ in ()).throw(
        pr.PreparacionFallida("el terminal no entregó XAUUSD"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "XAUUSD" in r.texto and armado.llamadas == []


def test_agy_sin_responder_no_gasta_cupo(armado):
    armado.atendedor.redactar = redactor([], codigo="timeout")
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
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
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "controles" in r.texto and not r.archivos
    assert armado.estado.usados(CAMILA, AHORA) == 0


def test_cupo_diario(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "COPPER"})))
    assert "cupo" in r.texto and not r.archivos
    assert armado.preparaciones == 2


# ───────────────────────────────────────────────────────────── /seguimiento


def test_seguimiento_entrega_lamina_y_texto_sin_agy(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.llamadas == [] and r.texto.startswith("Hola, ") and "CFD" in r.texto
    assert "[[SALUDO]]" not in r.texto
    assert r.archivos[0].suffix == ".png"


def test_el_saludo_se_aplica_al_responder_y_no_se_hereda_entre_ejecutivos(armado):
    """La pieza se reusa 30 minutos entre ejecutivos: cada uno recibe SU saludo."""
    a = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"}, "Juan")))
    c = armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("seguimiento", {"ticker": "XAUUSD"}, "Estimado Sr. Pérez")))
    d = armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert a.texto.startswith("Hola Juan, ") and c.texto.startswith("Estimado Sr. Pérez, ")
    assert d.texto.startswith("Hola, ") and armado.llamadas == []


@pytest.mark.parametrize("orden", [ORO, od.Orden("seguimiento", {"ticker": "XAUUSD"})])
def test_preparar_usa_el_registro_del_bot(armado, orden):
    """Con un registro inyectado, preparar no puede mirar el real (`rg.RUTA`)."""
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, orden))
    assert armado.kwargs == {"registro": armado.registro}


def test_seguimiento_se_reusa_30_minutos(armado):
    o = od.Orden("seguimiento", {"ticker": "XAUUSD"})
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    armado.reloj.ahora += timedelta(minutes=20)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 1
    armado.reloj.ahora += timedelta(minutes=15)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 2


def test_seguimiento_queda_anotado_en_el_analisis_vigente(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    seg = rg.vigente("XAUUSD", AHORA, armado.registro)["seguimientos"]
    assert [(s["ticker"], s["estado"], s["ejecutivo"]) for s in seg] == [("XAUUSD", "en_curso", OTRO)]


def test_seguimiento_sin_analisis_no_gasta_cupo(armado):
    error = pr.SinAnalisisError("No hay un análisis vigente de XAUUSD: pide primero /oportunidad XAUUSD.")

    def falla(orden, d, a, **kw):
        raise error

    armado.atendedor.preparar = falla
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert r.texto == f"❌ {error}" and armado.estado.usados(CAMILA, AHORA) == 0


def test_mt5_caido_en_seguimiento_lo_dice(armado):
    armado.atendedor.preparar = lambda o, d, a, **kw: (_ for _ in ()).throw(
        pr.PreparacionFallida("no uso el terminal: MT5 no conectó"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert "MT5" in r.texto
    assert "sigue disponible con /oportunidad" in r.texto  # spec §8


def test_un_registro_danado_se_dice_claro(armado):
    armado.registro.write_text("{no es json", encoding="utf-8")
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "registro de análisis está dañado" in r.texto and "inesperado" not in r.texto


def test_el_recibido_dice_cuanto_demora(armado):
    r = armado.bot.recibir(update("/oportunidad oro"))
    assert "unos 10 minutos y te aviso cuando esté" in r[0].texto
    assert "unos 10 minutos" in b.AYUDA


def test_un_fallo_al_enviar_el_pdf_no_impide_enviar_el_html():
    class TgFallaPdf(TgFalso):
        def documento(self, chat, ruta):
            if str(ruta).endswith(".pdf"):
                raise RuntimeError("Telegram rechazó el PDF")
            super().documento(chat, ruta)

    tg = TgFallaPdf()
    r = b.Respuesta(1, "hola", [Path("a.pdf"), Path("a.html")], "aparte")
    b.entregar(tg, r)
    assert tg.documentos == [(1, "a.html")]
    assert any("a.pdf" in t for _, t in tg.mensajes)
    assert tg.mensajes[-1][1] == "aparte"


def test_la_ayuda_nombra_solo_los_dos_comandos():
    assert "/oportunidad oro" in b.AYUDA and "/seguimiento oro" in b.AYUDA
    for retirado in ("/activo", "/calendario", "/dato", "/jornada"):
        assert retirado not in b.AYUDA
    assert "—" not in b.AYUDA and "–" not in b.AYUDA


def _dato_hoy(hora="2026-10-08 15:00"):
    return {"nombre": "CPI (MoM) (Sep)", "pais": "United States", "impacto": "alto", "hora_servidor": hora,
            "forecast": "0.2%", "previo": "0.3%", "actual": "", "fuente": "investing",
            "diccionario": {"nombre_es": "Índice de precios al consumidor (IPC)", "tier": 1,
                            "si_sale_sobre_consenso": {"oro": "baja", "usdclp": "sube"}}}


def test_con_un_dato_pendiente_el_seguimiento_lo_usa_y_avisa_aparte_al_ejecutivo(armado):
    """Con el suceso único, el texto de WhatsApp ya no incluye datos macro ni precios."""
    armado.eventos = [_dato_hoy()]
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"}, "Hari")))
    assert r.texto.startswith("Hola Hari, ") and "CFD" in r.texto
    assert "a las 15:00" not in r.texto
    tg = TgFalso()
    b.entregar(tg, r)
    assert tg.mensajes and tg.documentos


def test_el_dato_macro_se_evalua_al_responder_y_no_queda_guardado_con_la_pieza(armado):
    o = od.Orden("seguimiento", {"ticker": "XAUUSD"})
    armado.eventos = [_dato_hoy()]
    con = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    armado.eventos = []
    sin = armado.bot.procesar_uno(b.Pedido(OTRO, 2, o))
    assert "CFD" in con.texto and "CFD" in sin.texto
    assert sin.aparte == "" and armado.preparaciones == 1


def test_si_el_calendario_falla_el_seguimiento_sale_igual(armado):
    def roto(ahora):
        raise OSError("sin red")

    armado.atendedor.calendario = roto
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert r.texto.startswith("Hola, ") and "CFD" in r.texto and r.aparte == ""


def test_el_menu_de_telegram_solo_ofrece_comandos_que_existen():
    import analista.orden as od_
    conocidos = set(od_.PIEZAS) | set(od_.SERVICIO)
    for comando, descripcion in b.MENU:
        assert comando in conocidos and 3 <= len(descripcion) <= 256
        assert "—" not in descripcion and "–" not in descripcion
    assert {"oportunidad", "seguimiento"} <= {c for c, _ in b.MENU}


def test_la_ayuda_es_corta_y_trae_ejemplos_para_copiar():
    assert len(b.AYUDA.splitlines()) <= 28 and len(b.AYUDA) <= 1500  # dos pantallas de celular
    assert "/seguimiento oro" in b.AYUDA and "/seguimiento oro Juan" in b.AYUDA


def test_estado_muestra_el_cupo(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
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


# ───────────────────────────────────────────── fix final de la rama


def _redactor_con_fuentes(fuentes):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["fuentes"] = fuentes
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")
    return redactar


def test_una_tesis_con_porcentaje_descarta_solo_esa_fuente_y_la_pieza_sale(armado):
    buena = {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}
    rota = {**buena, "entidad": "UBS", "url": "https://www.reuters.com/markets/otra-nota-ubs/",
            "tesis": "UBS ve un alza de 5% en el oro."}
    armado.atendedor.redactar = _redactor_con_fuentes([dict(fx.DIRECTA_ORO), buena, rota])
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "Descarté una fuente: UBS" in r.aparte
    fuentes = pr.cargar_pieza(next((armado.tmp / "pedidos").rglob("pieza.json")).parent)["editorial"]["fuentes"]
    assert [f["entidad"] for f in fuentes] == ["World Gold Council", "Goldman Sachs"]


def test_una_tesis_limpia_sigue_en_la_pieza(armado):
    buena = {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}
    armado.atendedor.redactar = _redactor_con_fuentes([dict(fx.DIRECTA_ORO), buena])
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "Descarté" not in r.aparte


def test_el_reuso_propio_no_se_anota(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert rg.vigente("XAUUSD", AHORA, armado.registro)["reusos"] == []
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert [x["id"] for x in rg.vigente("XAUUSD", AHORA, armado.registro)["reusos"]] == [OTRO]


# ───────────────────────────────────────────── una noticia directa o nada (spec 2026-10-20)

BANCO = {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}
WGC = {"entidad": "World Gold Council", "medio": "World Gold Council", "fecha": "2026-10-06",
       "url": "https://www.gold.org/goldhub/research/demanda-octubre", "postura": "alcista",
       "tesis": "El WGC ve demanda firme de los bancos centrales.", "verificacion": "ok"}
# WGC es del ancla por entidad, pero su tesis no nombra el oro: no es directa.


def test_con_fuente_directa_al_primer_intento_no_hay_reintento(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and armado.reintentos == [] and "segundo intento" not in r.aparte
    carpeta = next((armado.tmp / "pedidos").rglob("pieza.json")).parent
    assert (carpeta / "agy_salida_1.json").exists() and not (carpeta / fu.INTENTO).exists()


def test_sin_directa_el_reintento_solo_reabre_las_fuentes_y_la_pieza_sale(armado):
    vistos = []

    def fuentes_falso(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        vistos.append(json.loads(json.dumps(pieza["editorial"])))
        pieza["editorial"]["fuentes"] = [dict(fx.DIRECTA_ORO), BANCO]
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="", respuesta="OK", segundos=61.0)

    armado.atendedor.redactar = _redactor_con_fuentes([WGC])
    armado.atendedor.redactar_fuentes = fuentes_falso
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "segundo intento" in r.aparte
    assert vistos[0]["fuentes"] == es.MARCA and vistos[0]["contexto"]["XAUUSD"] != es.MARCA
    carpeta = next((armado.tmp / "pedidos").rglob("pieza.json")).parent
    intento = json.loads((carpeta / fu.INTENTO).read_text(encoding="utf-8"))
    assert [f["entidad"] for f in intento["validas"]] == ["World Gold Council"]
    salida = json.loads((carpeta / "agy_salida_2.json").read_text(encoding="utf-8"))
    assert salida["segundos"] == 61.0 and salida["respuesta"] == "OK"
    assert [f["entidad"] for f in pr.cargar_pieza(carpeta)["editorial"]["fuentes"]] == ["World Gold Council", "Goldman Sachs"]
    assert "noticia directa" in r.aparte


def test_sin_noticia_directa_no_publica_y_no_gasta_cupo(armado):
    roto = {**BANCO, "url": "https://blog.example.com/oro"}  # dominio que no es de Reuters
    armado.atendedor.redactar = _redactor_con_fuentes([WGC, roto])
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and "noticia directa" in r.texto and "No gasté tu cupo" in r.texto
    assert "Goldman Sachs: el dominio" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 0


def test_una_voz_de_banco_sola_ya_no_habilita(armado):
    armado.atendedor.redactar = _redactor_con_fuentes([dict(BANCO)])
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and "noticia directa" in r.texto
    assert len(armado.reintentos) == 1  # el banco solo no evita el segundo intento


def test_sin_ancla_no_consume_cupo(armado):
    def sin_ancla(orden, dir_pedido, ahora, **kw):
        raise pr.PreparacionFallida(sg.aviso_sin_ancla("XAUUSD"))

    armado.atendedor.preparar = sin_ancla
    antes = armado.estado.usados(CAMILA, AHORA)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and "No gasté tu cupo" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == antes and armado.llamadas == []


def test_validar_exige_una_fuente_directa(tmp_path, capsys):
    import bot_analistas

    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path, fuentes=[WGC]), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 1
    assert "fuente directa" in capsys.readouterr().out
    # Una voz de banco sola tampoco alcanza.
    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 1
    assert "fuente directa" in capsys.readouterr().out
    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path, fuentes=[dict(fx.DIRECTA_ORO), *fx.FUENTES_EJEMPLO]), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 0


def test_validar_calla_en_una_pieza_sin_fuente_directa_sellada(tmp_path, capsys):
    import bot_analistas

    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path, fuentes=[WGC], sello=False), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 0
    assert "OK" in capsys.readouterr().out


def test_validar_contexto_dice_que_noticia_cae_y_por_que(tmp_path, capsys, monkeypatch):
    import bot_analistas
    from analista import contexto as ctx
    from analista import fuentes as fu
    from analista import noticia as nt

    monkeypatch.setattr(fu, "verificar_url", lambda url, *a, **k: "ok")
    monkeypatch.setattr(nt, "leer_texto", lambda url, *a, **k: "texto")
    seg = fx.pieza_seguimiento(tmp_path)["datos"]
    seg["suceso"] = {"estado": "esperando", "sentido": "ALCISTA", "nivel": 4050.5, "objetivo": 4120.0,
                     "siguiente": None, "calidad": "A+", "nota_semana": ""}
    cand = [{"medio": "FXStreet", "fecha": "2026-10-24", "url": "https://www.fxstreet.es/a", "titular_original": "Oro sube"}]
    pieza = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, lambda *a: (cand, [])).pieza
    pieza["editorial"]["noticia_1"] = {"medio": "FXStreet", "fecha": "2026-10-24", "url": "https://otro.example/x",
                                      "titular_original": "Oro sube", "titular": "El oro sube", "mensaje": "[[SALUDO]] ¿Lo vemos?"}
    pieza["editorial"]["noticia_2"] = None
    pieza["editorial"]["tecnico"] = "[[SALUDO]] el oro sigue al alza sobre [[NIVEL]]. ¿La vemos?"
    pr.guardar_pieza(pieza, tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 1
    salida = capsys.readouterr().out
    assert "noticia_1" in salida and "candidatas" in salida


# ───────────────────────────────────────────────────────── /recrear (solo el director)


def _con_director(a):
    a.atendedor.config["admins"] = [CAMILA]
    return a


def test_recrear_no_existe_para_un_ejecutivo(armado):
    _con_director(armado)
    r, final = pedir(armado, "/recrear oro", usuario=OTRO)
    assert r[0].texto == b.SIN_COMANDO and final is None and armado.preparaciones == 0
    r, _ = pedir(armado, "/recrear todas", usuario=OTRO)
    assert r[0].texto == b.SIN_COMANDO and not armado.bot.por_confirmar


def test_recrear_rehace_aunque_haya_uno_vigente_y_no_gasta_cupo(armado):
    _con_director(armado)
    pedir(armado, "/oportunidad oro", usuario=OTRO)
    assert armado.preparaciones == 1
    r, final = pedir(armado, "/recrear oro")
    assert armado.preparaciones == 2 and "❌" not in final.texto
    assert armado.estado.usados(CAMILA, armado.reloj.ahora) == 0
    assert rg.vigente("XAUUSD", armado.reloj.ahora, armado.registro)["creado_por"]["id"] == CAMILA
    anteriores = [e for e in json.loads(armado.registro.read_text(encoding="utf-8")) if e["caducada"]]
    assert anteriores[0]["caducada"]["motivo"] == "recreado por el director"


def test_recrear_todas_pide_si_y_rehace_solo_los_vigentes(armado):
    _con_director(armado)
    pedir(armado, "/oportunidad oro", usuario=OTRO)
    r, _ = pedir(armado, "/recrear todas")
    assert "XAUUSD" in r[0].texto and "sí" in r[0].texto and armado.bot.cola.empty()
    r, final = pedir(armado, "sí")
    assert armado.preparaciones == 2 and final is not None and not armado.bot.por_confirmar


def test_recrear_todas_sin_si_no_hace_nada(armado):
    _con_director(armado)
    pedir(armado, "/oportunidad oro", usuario=OTRO)
    pedir(armado, "/recrear todas")
    r, final = pedir(armado, "no")
    assert final is None and armado.preparaciones == 1 and not armado.bot.por_confirmar


def test_recrear_no_aparece_en_el_menu():
    assert "recrear" not in {c for c, _ in b.MENU}


# ───────────────────────────────────────────── revisión final: avisos de cara al ejecutivo


def _texto_al_pedir(armado, error):
    def falla(orden, dir_pedido, ahora, **kw):
        raise error

    armado.atendedor.preparar = falla
    antes = armado.estado.usados(CAMILA, AHORA)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and armado.estado.usados(CAMILA, AHORA) == antes
    return r.texto


def test_el_aviso_sin_ancla_sale_sin_el_prefijo_de_falla_de_lectura(armado):
    with pytest.raises(pr.PreparacionFallida) as exc:  # el error tal como lo levanta preparar
        pr.preparar(od.Orden("oportunidad", {"ticker": "XAUUSD"}), armado.tmp / "sin_ancla", AHORA,
                    pr.Lectores(ancla=lambda t: None, cuenta=lambda: None))  # sin terminal real (CI)
    texto = _texto_al_pedir(armado, exc.value)
    assert "No pude leer los datos" not in texto
    assert "No tengo una fuente propia definida para XAUUSD" in texto


def test_el_aviso_de_ingesta_de_acciones_es_para_el_ejecutivo(armado, tmp_path):
    import ingesta_acciones as ia

    hoy = datetime(2026, 10, 20, 15, 0, tzinfo=ZoneInfo("UTC"))
    for preparar_falla in ("sin_ingesta", "vencida"):
        base = tmp_path / preparar_falla
        if preparar_falla == "vencida":
            anclas = {"#AAPL": ("acciones", {"ticker": "AAPL", "cik": "0000320193"})}
            ia.ingestar(anclas, base, ahora=hoy - timedelta(days=10), descargar_fecha=lambda t: None,
                        descargar_sec=lambda u, headers: {"filings": {"recent": {
                            "form": [], "filingDate": [], "reportDate": [], "accessionNumber": [],
                            "primaryDocument": []}}})
        with pytest.raises(pr.PreparacionFallida) as exc:
            ia.leer_empresa("#AAPL", base, ahora=hoy)
        texto = _texto_al_pedir(armado, exc.value)
        assert "No gasté tu cupo" in texto and "director" in texto, preparar_falla
        for prohibido in ("uv run", "pipeline_datos", "scripts/", "No pude leer los datos", "—", "–"):
            assert prohibido not in texto, (preparar_falla, prohibido)
        # Español chileno sin voseo.
        assert not any(v in texto for v in ("corré", "pedí", "avisale", "tenés", "podés")), preparar_falla

def test_bot_repara_pieza_vieja_sin_suceso(armado):
    """Review Focus 5: si la pieza reusada no trae suceso, se prepara de nuevo."""
    dir_viejo = (armado.atendedor.dir_pedidos / AHORA.strftime("%Y-%m-%d")
                 / f"{AHORA:%H%M%S}_seguimiento_xauusd")
    dir_viejo.mkdir(parents=True, exist_ok=True)
    pieza_vieja = fx.pieza_seguimiento(dir_viejo)
    pr.guardar_pieza(pieza_vieja, dir_viejo)
    armado.estado.registrar_pieza("seguimiento_XAUUSD", dir_viejo, AHORA, fija=False)

    armado.preparaciones = 0
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.preparaciones == 1
    assert "CFD" in r.texto


def test_la_ayuda_incluye_instrucciones_completas_analista():
    a = b.AYUDA
    for comando in ("/oportunidad", "/seguimiento", "/estado", "/id"):
        assert comando in a
    assert "10 pedidos" in a  # el cupo diario
    assert "No constituye asesoría financiera personalizada" in a
    assert "director" in a  # a quién escribir si falla
    assert "jornada hábil" in a  # el bot vive en el PC del director
    assert "—" not in a and "–" not in a


NOTICIA_ORO = {"medio": "Reuters", "fecha": "2026-10-07",
               "url": "https://www.reuters.com/markets/commodities/gold-recovers-2026-10-07/",
               "titular_original": "Gold recovers as dollar rally stalls", "extracto": "Gold rose.",
               "titular": "El oro se recupera mientras el dólar pierde impulso",
               "bajada": "Según Reuters, el metal gana terreno frente a un dólar sin fuerza.", "motivo": "oro_lingotes"}
TASA_FED = {"banco": "fed", "nombre": "Reserva Federal (Fed)", "serie": "Tasa efectiva de fondos federales",
            "valor": "3,88", "fecha": "07/10", "linea": "x", "motivo_imagen": "banco_central"}


def _con_noticia(armado, noticia):
    base = redactor(armado.llamadas)

    def redactar(ruta, tier):
        base(ruta, tier)
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"]["noticia"] = noticia
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")
    armado.atendedor.redactar = redactar


def _pieza_guardada(armado):
    return pr.cargar_pieza(next((armado.tmp / "pedidos").rglob("pieza.json")).parent)


def test_noticia_rota_no_bota_la_pieza(armado):
    _con_noticia(armado, {**NOTICIA_ORO, "bajada": "Según Reuters, el oro subió a 4.200 dólares."})
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "⚠️ Noticia de apertura: " in r.aparte
    assert "Descarté una fuente: Noticia" not in r.aparte
    assert _pieza_guardada(armado)["editorial"]["noticia"] is None


def test_sin_noticia_avisa_que_el_correo_abre_con_el_analisis(armado):
    _con_noticia(armado, None)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and r.aparte.count("sin noticia de apertura") == 1


def test_noticia_descartada_avisa_una_sola_vez(armado):
    _con_noticia(armado, {**NOTICIA_ORO, "bajada": "Según Reuters, el oro subió a 4.200 dólares."})
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "Noticia de apertura: " in r.aparte and "sin noticia de apertura" not in r.aparte


def test_con_noticia_no_avisa_que_falta(armado):
    _con_noticia(armado, NOTICIA_ORO)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "sin noticia de apertura" not in r.aparte


def test_ilustraciones_se_eligen_una_vez(armado):
    armado.tasa = TASA_FED
    _con_noticia(armado, NOTICIA_ORO)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    pieza = _pieza_guardada(armado)
    ilu = pieza["ilustraciones"]
    assert r.archivos and set(ilu) == {"noticia", "tasa"}
    dir_pedido = next((armado.tmp / "pedidos").rglob("pieza.json")).parent
    assert all((dir_pedido / f).exists() for f in ilu.values())
    assert es.errores(pieza) == []  # `ilustraciones` no rompe la huella


def test_la_imagen_de_la_noticia_es_del_activo_de_la_pieza(armado):
    """Una noticia de oro marcada con el motivo de plata no puede salir con lingotes de plata, ni al revés."""
    _con_noticia(armado, {**NOTICIA_ORO, "motivo": "plata"})
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert [d.parent.name for d in armado.generadas] == ["oro_lingotes"]


def test_reuso_no_genera_imagenes(armado):
    armado.tasa = TASA_FED
    _con_noticia(armado, NOTICIA_ORO)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    antes = len(armado.generadas)
    armado.bot.procesar_uno(b.Pedido(OTRO, 1, ORO))
    assert antes == 2 and len(armado.generadas) == antes


def test_sin_imagen_avisa(armado):
    armado.generar_falla = True
    _con_noticia(armado, NOTICIA_ORO)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "sin imagen" in r.aparte
    assert "noticia" not in _pieza_guardada(armado).get("ilustraciones", {})


def test_un_error_inesperado_de_imagen_no_bota_la_pieza(armado):
    def generar_roto(prompt, destino):
        raise OSError("disco lleno")
    armado.atendedor.generar_imagen = generar_roto
    _con_noticia(armado, NOTICIA_ORO)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "sin imagen" in r.aparte


def test_ilustraciones_escritas_por_agy_se_pisan(armado):
    base = redactor(armado.llamadas)

    def redactar(ruta, tier):
        base(ruta, tier)
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["ilustraciones"] = {"noticia": "../../secreto.png"}
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")
    armado.atendedor.redactar = redactar
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert _pieza_guardada(armado).get("ilustraciones", {}) == {}


# ───────────────────────────────────────────────────────────── /contexto (mensajes)

def test_contexto_entrega_el_html_con_tres_tarjetas(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"}, "Juan")))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("contexto", {"ticker": "XAUUSD"}, "Juan")))
    assert len(r.archivos) == 1
    html_path = r.archivos[0]
    assert html_path.name == "mensajes.html"
    contenido = html_path.read_text(encoding="utf-8")
    assert 'data-tarjeta="Noticia 1"' in contenido
    assert 'data-tarjeta="Noticia 2"' in contenido
    assert 'data-tarjeta="Análisis técnico"' in contenido
    assert "Hola Juan," in contenido
    assert "[[NIVEL]]" not in contenido
    assert "[[OBJETIVO]]" not in contenido
    assert "4.150,00" in contenido or "4,150.00" in contenido or "4150" in contenido


def test_contexto_gasta_una_pieza_del_cupo(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.estado.usados(CAMILA, AHORA) == 1
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("contexto", {"ticker": "XAUUSD"})))
    assert len(r.archivos) == 1
    assert armado.estado.usados(CAMILA, AHORA) == 2


def test_contexto_se_reusa_30_minutos_sin_gastar_cupo_ni_agy_y_con_el_saludo_de_quien_pide(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"}, "Juan")))
    r1 = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("contexto", {"ticker": "XAUUSD"}, "Juan")))
    llamadas_iniciales = len(armado.llamadas)

    armado.reloj.ahora += timedelta(minutes=10)
    r2 = armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("contexto", {"ticker": "XAUUSD"}, "Estimado Pedro")))
    assert len(armado.llamadas) == llamadas_iniciales
    assert armado.estado.usados(OTRO, armado.reloj.ahora) == 0
    assert len(r2.archivos) == 1
    contenido2 = r2.archivos[0].read_text(encoding="utf-8")
    assert "Estimado Pedro," in contenido2
    assert "Hola Juan," not in contenido2


def test_contexto_si_agy_falla_no_gasta_cupo_ni_se_registra(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.estado.usados(CAMILA, AHORA) == 1
    armado.atendedor.redactar = redactor([], codigo="timeout")
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("contexto", {"ticker": "XAUUSD"})))
    assert "No gasté tu cupo" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 1
    assert "contexto|ticker=XAUUSD" not in armado.estado.datos["piezas"]


def test_contexto_con_cupo_agotado_avisa_y_no_lanza_agy(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "COPPER"})))
    assert armado.estado.usados(CAMILA, AHORA) == 2
    llamadas_antes = len(armado.llamadas)
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("contexto", {"ticker": "XAUUSD"})))
    assert "cupo" in r.texto and not r.archivos
    assert len(armado.llamadas) == llamadas_antes


def test_seguimiento_exitoso_encola_un_contexto(armado):
    import threading, time
    hilo = threading.Thread(target=armado.bot.trabajador, daemon=True)
    hilo.start()
    armado.bot.recibir(update("/seguimiento oro Juan", usuario=CAMILA))
    for _ in range(50):
        if len(armado.bot.tg.documentos) >= 2:
            break
        time.sleep(0.05)
    docs = [d[1] for d in armado.bot.tg.documentos]
    assert "lamina.png" in docs
    assert "mensajes.html" in docs


def test_seguimiento_fallido_no_encola_contexto(armado):
    import threading, time
    error = pr.SinAnalisisError("No hay un análisis vigente de XAUUSD: pide primero /oportunidad XAUUSD.")
    armado.atendedor.preparar = lambda o, d, a, **kw: (_ for _ in ()).throw(error)
    hilo = threading.Thread(target=armado.bot.trabajador, daemon=True)
    hilo.start()
    armado.bot.recibir(update("/seguimiento oro Juan", usuario=CAMILA))
    time.sleep(0.15)
    docs = [d[1] for d in armado.bot.tg.documentos]
    assert docs == []
    assert armado.bot.cola.empty()


def test_segundo_seguimiento_mientras_genera_no_encola_otro_contexto(armado):
    orden_ctx = od.Orden("contexto", {"ticker": "XAUUSD"})
    armado.bot.generando.add(orden_ctx.clave_base().lower())
    pedido_seg = b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"}))
    armado.bot._encolar_contexto(pedido_seg)
    assert armado.bot.cola.empty()
    assert any("ya se están preparando" in m[1] for m in armado.bot.tg.mensajes)


def test_el_usuario_no_puede_pedir_contexto_por_telegram(armado):
    r = armado.bot.recibir(update("/contexto oro", usuario=CAMILA))
    assert len(r) == 1
    assert "Ese comando no existe" in r[0].texto or "/ayuda" in r[0].texto
    assert armado.bot.cola.empty()


def test_el_seguimiento_ya_entregado_no_cambia(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.llamadas == []
    assert r.texto.startswith("Hola, ")
    assert "CFD" in r.texto
    assert len(r.archivos) == 1
    assert r.archivos[0].suffix == ".png"
