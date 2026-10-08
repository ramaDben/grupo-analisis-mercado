"""Preparación de las piezas del bot: datos del terminal en la carpeta del pedido."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import informe_html as ih  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista.orden import Orden  # noqa: E402
from test_pipeline_carrusel import ACTIVO, CIERRES, SELECCION  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)

JORNADA = [
    {"fecha": "2026-10-08", "hora": "09:30", "pais": "United States", "evento": "Initial Jobless Claims",
     "nombre_es": "Peticiones de subsidio por desempleo", "explicacion": "", "consenso": "200K",
     "anterior": "199K", "actual": "197K", "resultado": "mejor"},
    {"fecha": "2026-10-08", "hora": "14:00", "pais": "United States", "evento": "FOMC Minutes",
     "nombre_es": "Minutas de la Fed", "explicacion": "", "consenso": "", "anterior": "",
     "actual": "", "resultado": ""},
]


def _png(destino: Path) -> Path:
    destino.write_bytes(fx.PNG)
    return destino


def lectores(**cambios) -> pr.Lectores:
    base = dict(
        terminal=lambda t, a: {"ticker": t, "activo": ACTIVO, "seleccion": SELECCION, "cierres": CIERRES},
        grafico_tv=lambda payload, destino: _png(destino),
        jornada=lambda a: (list(JORNADA), []),
        agenda=lambda a: (list(JORNADA), []),
        movimiento=lambda t, d, a: {"desde": 951.2, "ahora": 952.1, "digits": 2, "banda": 0.1},
        activos_jornada=lambda destino: ({
            "USDCLP": {"nombre": "Dólar / Peso Chileno", "digits": 2,
                       "d1": {"price": 951.2, "s1": 945.0, "r1": 958.4, "ema_50": 960.0},
                       "grafico": "graficos/usdclp.png"},
        }, []),
        curva=lambda: ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}, []),
        cuenta=lambda: None,
    )
    base.update(cambios)
    return pr.Lectores(**base)


def test_activo_trae_los_numeros_del_payload_de_whatsapp(tmp_path):
    hecha = pr.preparar(Orden("activo", {"ticker": "XAGUSD"}), tmp_path, AHORA, lectores())
    d = hecha.pieza["datos"]
    assert d["precio"] == "68,716" and d["soporte"] == "68,394" and d["resistencia"] == "68,974"
    assert d["direccion"] == "Alcista"
    assert d["nivel_vigilar"] == "68,974"
    assert d["escenarios"][0].startswith("⬆️ Sobre 68,974")
    assert d["chip"].startswith("NOTA DE MERCADO")
    assert (tmp_path / "grafico.png").exists() and (tmp_path / "pieza.json").exists()
    assert set(hecha.pieza["editorial"]) == set(es.CAMPOS["activo"])


def test_activo_sin_cuenta_correcta_no_lee_el_terminal(tmp_path):
    def no_llamar(*_):
        raise AssertionError("leyó el terminal con la cuenta equivocada")

    with pytest.raises(pr.PreparacionFallida, match="51492"):
        pr.preparar(Orden("activo", {"ticker": "XAGUSD"}), tmp_path, AHORA,
                    lectores(cuenta=lambda: "el dato salió de la cuenta 51492", terminal=no_llamar))


def test_calendario_hoy(tmp_path):
    hecha = pr.preparar(Orden("calendario", {"alcance": "hoy"}), tmp_path, AHORA, lectores())
    eventos = hecha.pieza["datos"]["eventos"]
    assert [e["estado"] for e in eventos] == ["salio", "proximo"]
    assert eventos[0]["actual"] == "197K"
    assert set(hecha.pieza["editorial"]["explicaciones"]) == {"01", "02"}
    assert "calendario.png" in hecha.pieza["laminas"]


def test_calendario_sin_datos_sugiere_la_semana(tmp_path):
    with pytest.raises(pr.PreparacionFallida, match="semana"):
        pr.preparar(Orden("calendario", {"alcance": "hoy"}), tmp_path, AHORA, lectores(jornada=lambda a: ([], [])))


def test_calendario_semana(tmp_path):
    hecha = pr.preparar(Orden("calendario", {"alcance": "semana"}), tmp_path, AHORA, lectores())
    assert len(hecha.pieza["datos"]["eventos"]) == 2


def test_dato_ultimo_con_resultado_y_movimiento(tmp_path):
    hecha = pr.preparar(Orden("dato", {"busqueda": "ultimo"}), tmp_path, AHORA, lectores())
    d = hecha.pieza["datos"]
    assert d["modo"] == "resultado"
    assert d["eventos"][0]["veredicto"] == "MEJOR"
    assert d["movimientos"] and d["movimientos"][0]["desde"] == "951,20"
    assert d["referencia"] == "197K"


def test_dato_por_nombre_que_no_salio_es_anticipacion(tmp_path):
    hecha = pr.preparar(Orden("dato", {"busqueda": "minutas"}), tmp_path, AHORA, lectores())
    assert hecha.pieza["datos"]["modo"] == "anticipacion"
    assert hecha.pieza["datos"]["movimientos"] == []


def test_dato_desconocido(tmp_path):
    with pytest.raises(pr.PreparacionFallida, match="pib"):
        pr.preparar(Orden("dato", {"busqueda": "pib"}), tmp_path, AHORA, lectores())


def test_jornada(tmp_path):
    def activos(destino):
        _png((destino / "graficos").mkdir(parents=True, exist_ok=True) or destino / "graficos" / "usdclp.png")
        return lectores().activos_jornada(destino)

    hecha = pr.preparar(Orden("jornada", {"momento": None}), tmp_path, AHORA, lectores(activos_jornada=activos))
    d = hecha.pieza["datos"]
    assert d["momento"] == "apertura" and d["activos"][0]["precio"] == "951,20"
    assert d["activos"][0]["direccion"] == "Bajista"
    assert d["curva"] == [["Bono del Tesoro a 2 años", "3,61%", "+2 pb", "sin dato"]]
    assert hecha.pieza["imagenes"] == {"USDCLP": "graficos/usdclp.png"}


def test_rendir_laminas_pone_el_texto_validado(tmp_path):
    hecha = pr.preparar(Orden("calendario", {"alcance": "hoy"}), tmp_path, AHORA, lectores())
    pieza = hecha.pieza
    pieza["editorial"].update({"titular": "Empleo y Fed", "bajada": "Dos citas para el dólar",
                               "lectura": "Texto de lectura suficiente.",
                               "explicaciones": {"01": "Explicación uno larga.", "02": "Explicación dos larga."}})
    vistos = {}

    def render(tokens, plantilla, destino, formato):
        vistos.update(tokens)
        return _png(destino)

    pr.rendir_laminas(pieza, tmp_path, render=render)
    assert vistos["titulo"] == "Empleo y Fed" and vistos["subtitulo"] == "Dos citas para el dólar"
    assert (tmp_path / "calendario.png").exists()
    # La pieza completa se arma en HTML.
    assert "Empleo y Fed" in ih.armar(pieza, tmp_path, fx.ANALISTA)


def test_preparar_escribe_solo_en_la_carpeta_del_pedido(tmp_path):
    pedido = tmp_path / "pedido"
    pr.preparar(Orden("activo", {"ticker": "XAGUSD"}), pedido, AHORA, lectores())
    assert {p.relative_to(tmp_path).parts[0] for p in tmp_path.rglob("*")} == {"pedido"}


def test_no_usa_los_preparar_de_produccion():
    fuente = (RAIZ / "scripts" / "analista" / "preparar.py").read_text(encoding="utf-8")
    for prohibido in ("pc.preparar(", "pa.preparar(", "pi.preparar(", "escanear(", "registrar_uso",
                      "escribir_suplementos", "_preparar_resultado", "DIR_TRABAJO"):
        assert prohibido not in fuente, prohibido
