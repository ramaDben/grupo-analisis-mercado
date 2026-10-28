"""Pruebas de la pieza contexto: preparar, depurar, sustituir marcas y tarjetas."""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import contexto as ctx  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import seguimiento as sg  # noqa: E402
from analista.suceso import Resumen  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 25, 12, 0, tzinfo=SANTIAGO)
HOY = date(2026, 10, 25)

CANDIDATAS_EJEMPLO = [
    {
        "medio": "FXStreet",
        "fecha": "2026-10-25",
        "url": "https://www.fxstreet.es/news/oro-al-alza-20261025",
        "titular_original": "El oro sube con fuerza",
    },
    {
        "medio": "Investing.com",
        "fecha": "2026-10-24",
        "url": "https://es.investing.com/news/commodities-news/oro-rompe-resistencia-123456",
        "titular_original": "Oro supera resistencia clave",
    },
]

NOTICIA_1_OK = {
    "medio": "FXStreet",
    "fecha": "2026-10-25",
    "url": "https://www.fxstreet.es/news/oro-al-alza-20261025",
    "titular_original": "El oro sube con fuerza",
    "titular": "El oro sube con fuerza por la demanda global",
    "mensaje": "[[SALUDO]] te comparto esta nota: el oro sube con fuerza ante el retroceso del dólar. ¿Cómo lo ves?",
}

NOTICIA_2_OK = {
    "medio": "Investing.com",
    "fecha": "2026-10-24",
    "url": "https://es.investing.com/news/commodities-news/oro-rompe-resistencia-123456",
    "titular_original": "Oro supera resistencia clave",
    "titular": "Oro supera resistencia clave tras compras técnicas",
    "mensaje": "[[SALUDO]] mira esta otra noticia: el oro superó su nivel técnico clave en la jornada de hoy. ¿Revisamos?",
}

TECNICO_OK = (
    "[[SALUDO]] la lectura técnica del oro se mantiene alcista sobre [[NIVEL]]. "
    "El escenario busca el objetivo de [[OBJETIVO]] y se invalida si pierde esa línea. "
    "Temporalidad: 4H, marco swing de una a dos semanas. ¿Lo revisamos?"
)


def seg_ejemplo(tmp_path: Path, estado: str = "rebotando", sentido: str = "ALCISTA",
                nivel: float = 4100.0, objetivo: float = 4200.0,
                siguiente: float | None = None) -> dict:
    p = fx.pieza_seguimiento(tmp_path)
    datos = p["datos"]
    resumen = Resumen(
        estado=estado,
        sentido=sentido,
        nivel=nivel,
        objetivo=objetivo,
        siguiente=siguiente,
        calidad="A+",
        nota_semana="",
    )
    datos["suceso"] = {
        "estado": resumen.estado,
        "sentido": resumen.sentido,
        "nivel": resumen.nivel,
        "objetivo": resumen.objetivo,
        "siguiente": resumen.siguiente,
        "calidad": resumen.calidad,
        "nota_semana": resumen.nota_semana,
    }
    return datos


def test_preparar_sella_candidatas_y_tecnico(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    assert p["orden"]["pieza"] == "contexto"
    assert p["datos"]["noticias_candidatas"] == CANDIDATAS_EJEMPLO
    assert p["datos"]["tecnico"] == {
        "nombre": "Oro",
        "sentido": "ALCISTA",
        "estado": "rebotando",
        "nivel": 4100.0,
        "objetivo": 4200.0,
        "siguiente": None,
        "calidad": "A+",
        "digits": 2,
    }
    assert p["datos"]["tecnico_motivo"] == ""
    assert p["editorial"]["noticia_1"] == es.MARCA
    assert p["editorial"]["noticia_2"] == es.MARCA
    assert p["editorial"]["tecnico"] == es.MARCA
    assert (tmp_path / "pieza.json").is_file()


def test_preparar_sin_candidatas_deja_noticias_en_none(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: ([], ["sin noticias"]))
    p = prep.pieza
    assert p["editorial"]["noticia_1"] is None
    assert p["editorial"]["noticia_2"] is None
    assert p["editorial"]["tecnico"] == es.MARCA
    assert "sin noticias" in prep.avisos[0]


@pytest.mark.parametrize("estado_sin_dir", ["sin_direccion", "cerrado"])
def test_preparar_sin_direccion_deja_tecnico_en_none_con_motivo(tmp_path, estado_sin_dir):
    seg = seg_ejemplo(tmp_path, estado=estado_sin_dir, sentido=None, nivel=None, objetivo=None)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    assert p["editorial"]["tecnico"] is None
    assert bool(p["datos"]["tecnico_motivo"]) is True


def test_depurar_acepta_las_tres_tarjetas_buenas(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": TECNICO_OK,
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["noticia_1"] is not None
    assert depurada["editorial"]["noticia_2"] is not None
    assert depurada["editorial"]["tecnico"] is not None
    assert depurada.get("motivos") == {}


def test_depurar_cae_noticia_con_url_fuera_de_candidatas(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    n_fuera = dict(NOTICIA_1_OK, url="https://www.fxstreet.es/news/otra-nota-distinta")
    p["editorial"] = {
        "noticia_1": n_fuera,
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": TECNICO_OK,
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["noticia_1"] is None
    assert "noticias candidatas" in depurada["motivos"]["noticia_1"].lower()
    assert depurada["editorial"]["noticia_2"] is not None


def test_depurar_cae_noticia_2_con_url_repetida(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_1_OK),  # misma URL y titular
        "tecnico": TECNICO_OK,
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["noticia_1"] is not None
    assert depurada["editorial"]["noticia_2"] is None
    assert "repite" in depurada["motivos"]["noticia_2"].lower()


def test_depurar_marca_escribir_pasa_a_none_con_motivo(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": es.MARCA,
        "noticia_2": es.MARCA,
        "tecnico": es.MARCA,
    }
    depurada, avisos = ctx.depurar(p, HOY)
    assert depurada["editorial"]["noticia_1"] is None
    assert depurada["editorial"]["noticia_2"] is None
    assert depurada["editorial"]["tecnico"] is None
    assert depurada["motivos"]["noticia_1"] == "No alcancé a redactar este mensaje: vuelve a pedir el contexto."
    assert depurada["motivos"]["noticia_2"] == "No alcancé a redactar este mensaje: vuelve a pedir el contexto."
    assert depurada["motivos"]["tecnico"] == "No alcancé a redactar este mensaje: vuelve a pedir el contexto."


@pytest.mark.parametrize("precio_escrito", ["4.100,50", "1.2345"])
def test_depurar_tecnico_con_precio_escrito_cae(tmp_path, precio_escrito):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": f"[[SALUDO]] el oro va en {precio_escrito} y busca el nivel clave.",
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["tecnico"] is None
    assert any(w in depurada["motivos"]["tecnico"].lower() for w in ("precio", "cifra", "número", "numero"))


def test_depurar_tecnico_con_marca_sin_valor_cae(tmp_path):
    seg = seg_ejemplo(tmp_path, siguiente=None)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": "[[SALUDO]] el oro vigila [[NIVEL]] y si rompe va a [[SIGUIENTE]]. ¿Lo vemos?",
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["tecnico"] is None
    assert "[[SIGUIENTE]]" in depurada["motivos"]["tecnico"]


def test_depurar_tecnico_sin_saludo_cae(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": "El oro vigila [[NIVEL]] y busca [[OBJETIVO]]. ¿Lo vemos?",
    }
    lista = {"medios": {"FXStreet": ["fxstreet.es"], "Investing.com": ["investing.com"]}}
    depurada, avisos = ctx.depurar(p, HOY, lista=lista, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["tecnico"] is None
    assert "[[SALUDO]]" in depurada["motivos"]["tecnico"]


def test_sustituir_marcas_usa_los_digits_del_activo():
    tecnico = {
        "digits": 2,
        "nivel": 4000.0,
        "objetivo": 4150.5,
        "siguiente": None,
    }
    texto = "Vigila [[NIVEL]] con objetivo en [[OBJETIVO]]."
    esperado_nivel = sg._fmt(4000.0, 2)
    esperado_obj = sg._fmt(4150.5, 2)
    resultado = ctx.sustituir_marcas(texto, tecnico)
    assert resultado == f"Vigila {esperado_nivel} con objetivo en {esperado_obj}."


def test_tarjetas_siempre_tres_y_vacias_llevan_motivo(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": None,
        "tecnico": None,
    }
    p["motivos"] = {
        "noticia_2": "Hoy no hay una segunda noticia directa de Oro",
        "tecnico": "El mercado está cerrado",
    }
    tarjetas = ctx.tarjetas(p)
    assert len(tarjetas) == 3
    assert [t.titulo for t in tarjetas] == ["Noticia 1", "Noticia 2", "Análisis técnico"]

    assert tarjetas[0].texto is not None
    assert tarjetas[0].motivo == ""
    assert tarjetas[0].medio == "FXStreet"
    assert tarjetas[0].url == NOTICIA_1_OK["url"]

    assert tarjetas[1].texto is None
    assert tarjetas[1].motivo == "Hoy no hay una segunda noticia directa de Oro"

    assert tarjetas[2].texto is None
    assert tarjetas[2].motivo == "El mercado está cerrado"


def test_tarjetas_aplican_el_saludo_del_ejecutivo(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": dict(NOTICIA_1_OK),
        "noticia_2": dict(NOTICIA_2_OK),
        "tecnico": TECNICO_OK,
    }
    tarjetas = ctx.tarjetas(p, saludo="Juan")
    assert len(tarjetas) == 3
    assert tarjetas[0].texto.startswith("Hola Juan,")
    assert "Fuente: FXStreet, 25-10" in tarjetas[0].texto
    assert tarjetas[1].texto.startswith("Hola Juan,")
    assert "Fuente: Investing.com, 24-10" in tarjetas[1].texto
    assert tarjetas[2].texto.startswith("Hola Juan,")


@pytest.mark.parametrize("mensaje, saludo, esperado", [
    ("[[SALUDO]] Según FXStreet, la plata se mantiene estable.", "", "Hola, según FXStreet, la plata se mantiene estable."),
    ("[[SALUDO]] En la lectura técnica para la plata vigilamos el soporte.", "Juan", "Hola Juan, en la lectura técnica"),
    ("[[SALUDO]] FXStreet informa que el oro sube.", "", "Hola, FXStreet informa"),
    ("[[SALUDO]] Powell habló ayer.", "", "Hola, Powell habló"),
    ("[[SALUDO]] Según FXStreet, el oro sube.", "Estimado Sr. Pérez:", "Estimado Sr. Pérez: Según FXStreet"),
])
def test_lo_que_sigue_al_saludo_continua_la_frase(mensaje, saludo, esperado):
    assert ctx._con_saludo(mensaje, saludo).startswith(esperado)


def test_la_tarjeta_separa_la_pregunta_final_y_la_fuente(tmp_path):
    seg = seg_ejemplo(tmp_path)
    p = ctx.preparar("XAUUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, [])).pieza
    p["editorial"] = {"noticia_1": dict(NOTICIA_1_OK), "noticia_2": None, "tecnico": TECNICO_OK}
    n1, _, tec = ctx.tarjetas(p, saludo="Juan")
    assert n1.pregunta == "¿Cómo lo ves?"
    assert n1.cuerpo.endswith("ante el retroceso del dólar.")
    assert n1.pie == "Fuente: FXStreet, 25-10"
    assert n1.texto == f"{n1.cuerpo} {n1.pregunta}\n\n{n1.pie}"
    assert tec.pregunta == "¿Lo revisamos?" and tec.pie == ""


def test_la_noticia_vacia_dice_por_que_en_palabras_del_ejecutivo(tmp_path):
    seg = seg_ejemplo(tmp_path)
    p = ctx.preparar("XAGUSD", tmp_path, AHORA, seg, candidatas=lambda *_: (CANDIDATAS_EJEMPLO, [])).pieza
    p["datos"]["nombre"] = "Plata"
    p["editorial"] = {"noticia_1": dict(NOTICIA_1_OK), "noticia_2": None, "tecnico": TECNICO_OK}
    depurada, _ = ctx.depurar(p, HOY, verificar=lambda u: "ok", leer=lambda u: "")
    assert depurada["motivos"]["noticia_2"] == "No hay otra noticia de los últimos 3 días que trate de la plata."

    p["datos"]["noticias_candidatas"] = []
    p["editorial"] = {"noticia_1": None, "noticia_2": None, "tecnico": TECNICO_OK}
    depurada, _ = ctx.depurar(p, HOY, verificar=lambda u: "ok", leer=lambda u: "")
    assert depurada["motivos"]["noticia_1"] == "Hoy no encontré noticias de la plata en FXStreet ni en Investing.com."

def test_seguimiento_usa_los_escalones(tmp_path):
    seg = seg_ejemplo(tmp_path)
    cand_oficial = {
        "medio": "SEC EDGAR",
        "fecha": "2026-10-20",
        "url": "https://www.sec.gov/Archives/edgar/data/886982/000088698226000529/0000886982-26-000529-index.htm",
        "titular_original": "Goldman Sachs 8-K",
        "escalon": "oficial",
    }
    prep = ctx.preparar("#GS", tmp_path, AHORA, seg, candidatas=lambda *_: ([cand_oficial], []))
    assert prep.pieza["datos"]["noticias_candidatas"] == [cand_oficial]


def test_seguimiento_sella_el_piso(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep_gs = ctx.preparar("#GS", tmp_path / "gs", AHORA, seg, candidatas=lambda *_: ([], []))
    datos_gs = prep_gs.pieza["datos"]
    assert "fuente_oficial" in datos_gs
    assert datos_gs["fuente_oficial"]["organismo"] == "Goldman Sachs"
    assert datos_gs["fuente_oficial"]["pagina_prensa"] == "https://www.goldmansachs.com/investor-relations/"

    prep_btc = ctx.preparar("BTCUSD", tmp_path / "btc", AHORA, seg, candidatas=lambda *_: ([], []))
    datos_btc = prep_btc.pieza["datos"]
    assert "fuente_oficial" not in datos_btc


def test_depurar_acepta_oficial_de_20_dias(tmp_path):
    seg = seg_ejemplo(tmp_path)
    url_edgar = "https://www.sec.gov/Archives/edgar/data/886982/000088698226000529/0000886982-26-000529-index.htm"
    cand_oficial = {
        "medio": "SEC EDGAR",
        "fecha": "2026-10-05",
        "url": url_edgar,
        "titular_original": "Goldman Sachs 8-K",
        "escalon": "oficial",
    }
    prep = ctx.preparar("#GS", tmp_path, AHORA, seg, candidatas=lambda *_: ([cand_oficial], []))
    p = prep.pieza
    p["editorial"] = {
        "noticia_1": {
            "medio": "SEC EDGAR",
            "fecha": "2026-10-05",
            "url": url_edgar,
            "titular_original": "Goldman Sachs 8-K",
            "titular": "Goldman Sachs presenta su informe trimestral",
            "mensaje": "[[SALUDO]] te comparto el comunicado de Goldman Sachs ante la SEC. ¿Cómo lo ves?",
        },
        "noticia_2": None,
        "tecnico": TECNICO_OK,
    }
    depurada, avisos = ctx.depurar(p, HOY, verificar=lambda u: "ok", leer=lambda u: "texto ok")
    assert depurada["editorial"]["noticia_1"] is not None
    assert depurada["editorial"]["noticia_1"]["url"] == url_edgar
    assert "noticia_1" not in depurada.get("motivos", {})


def test_el_motivo_sin_noticias_sale_igual_con_piso(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar("#GS", tmp_path, AHORA, seg, candidatas=lambda *_: ([], []))
    p = prep.pieza
    p["datos"]["nombre"] = "Goldman Sachs"
    assert "fuente_oficial" in p["datos"]
    assert p["datos"]["noticias_candidatas"] == []
    p["editorial"] = {"noticia_1": None, "noticia_2": None, "tecnico": TECNICO_OK}
    depurada, _ = ctx.depurar(p, HOY, verificar=lambda u: "ok", leer=lambda u: "")
    assert depurada["motivos"]["noticia_1"] == "Hoy no encontré noticias de Goldman Sachs en FXStreet ni en Investing.com."


def test_candidatas_por_escalones_convierte_aviso_en_lista(monkeypatch):
    from analista import apertura as apt

    monkeypatch.setattr(apt, 'candidatas', lambda t, n, a: ([], 'aviso edgar'))
    lista, avisos = ctx._candidatas_por_escalones('#GS', 'Goldman Sachs', AHORA)
    assert lista == []
    assert avisos == ['aviso edgar']

    monkeypatch.setattr(apt, 'candidatas', lambda t, n, a: ([], None))
    lista, avisos = ctx._candidatas_por_escalones('#GS', 'Goldman Sachs', AHORA)
    assert avisos == []


def test_seguimiento_aviso_de_candidatas_se_suma_a_preparada(tmp_path):
    seg = seg_ejemplo(tmp_path)
    prep = ctx.preparar('#GS', tmp_path, AHORA, seg, candidatas=lambda *_: ([], ['EDGAR sin contacto']))
    assert 'EDGAR sin contacto' in prep.avisos
