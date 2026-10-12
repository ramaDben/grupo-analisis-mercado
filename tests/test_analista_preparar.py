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
from estrategia.contrato import lectura_a_dict  # noqa: E402
from test_pipeline_carrusel import ORO, _lectura_alcista, _sel  # noqa: E402

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


ACTIVO = {**ORO, "clase": "forex_commodities"}
SELECCION = _sel(_lectura_alcista())
CIERRES = [4119.0, 4120.0]


def lectores(**cambios) -> pr.Lectores:
    base = dict(
        terminal=lambda t, a: {"ticker": t, "activo": ACTIVO, "seleccion": SELECCION, "cierres": CIERRES},
        grafico_tv=lambda payload, destino: _png(destino),
        jornada=lambda a: (list(JORNADA), []),
        agenda=lambda a: (list(JORNADA), []),
        movimiento=lambda t, d, a: {"desde": 951.2, "ahora": 952.1, "digits": 2, "banda": 0.1},
        activos_jornada=lambda destino: ({
            "USDCLP": {"nombre": "Dólar / Peso Chileno", "digits": 2,
                       "lectura": lectura_a_dict(_lectura_alcista()),
                       "grafico": "graficos/usdclp.png"},
        }, []),
        curva=lambda: ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}, []),
        cuenta=lambda: None,
    )
    base.update(cambios)
    return pr.Lectores(**base)


def test_activo_trae_los_numeros_del_payload_de_whatsapp(tmp_path):
    hecha = pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), tmp_path, AHORA, lectores())
    d = hecha.pieza["datos"]
    assert d["precio"] == "4.120,00" and d["soporte"] == "4.080,00" and d["resistencia"] == "4.200,00"
    assert d["direccion"] == "Alcista"
    assert d["nivel_vigilar"] == "4.080,00 (línea alcista de seguridad)"
    assert d["escenarios"][0].startswith("⬆️ Mientras el precio cierre sobre 4.080,00")
    assert d["chip"] == "NOTA DE MERCADO · COMMODITIES"
    assert "velas de 4 horas" in d["pie_imagen"] and d["lectura"]["ticker"] == "XAUUSD"
    ctx = d["contexto"]
    assert ctx["drivers_del_activo"]  # XAUUSD tiene drivers en el catálogo real
    assert ctx["curva_tasas"][0][0] == "Bono del Tesoro a 2 años"
    assert ctx["agenda_hoy"][0].startswith("09:30") and "salió 197K" in ctx["agenda_hoy"][0]
    assert (tmp_path / "grafico.png").exists() and (tmp_path / "pieza.json").exists()
    assert set(hecha.pieza["editorial"]) == set(es.CAMPOS["activo"])


def test_activo_trae_el_plan_sellado_desde_la_lectura(tmp_path):
    hecha = pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), tmp_path, AHORA, lectores())
    plan = hecha.pieza["datos"]["plan"]
    assert plan["hay_plan"] and "4.080,00" in plan["invalidacion"]
    assert "estadistica" not in plan and "recorrido" not in plan
    assert plan["niveles"]["vela"] == 200
    hecha.pieza["datos"]["plan"]["gatillo"] = "otra cosa"
    assert any("cambiaron" in x for x in es.errores(hecha.pieza))


def test_activo_sin_lectura_de_la_estrategia_falla_con_motivo(tmp_path):
    sin = lambda t, a: {"ticker": t, "activo": ACTIVO, "seleccion": {**SELECCION, "lectura": None},  # noqa: E731
                        "cierres": CIERRES}
    with pytest.raises(pr.PreparacionFallida):
        pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), tmp_path, AHORA, lectores(terminal=sin))


def test_activo_sin_cuenta_correcta_no_lee_el_terminal(tmp_path):
    def no_llamar(*_):
        raise AssertionError("leyó el terminal con la cuenta equivocada")

    with pytest.raises(pr.PreparacionFallida, match="51492"):
        pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), tmp_path, AHORA,
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
    assert d["momento"] == "apertura" and d["activos"][0]["precio"] == "4.120,00"
    assert d["activos"][0]["direccion"] == "Alcista" and d["activos"][0]["soporte"] == "4.080,00"
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
    assert "Empleo y Fed" in ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, AHORA.date())


def test_preparar_escribe_solo_en_la_carpeta_del_pedido(tmp_path):
    pedido = tmp_path / "pedido"
    pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), pedido, AHORA, lectores())
    assert {p.relative_to(tmp_path).parts[0] for p in tmp_path.rglob("*")} == {"pedido"}


def test_no_usa_los_preparar_de_produccion():
    fuente = (RAIZ / "scripts" / "analista" / "preparar.py").read_text(encoding="utf-8")
    for prohibido in ("pc.preparar(", "pa.preparar(", "pi.preparar(", "escanear(", "registrar_uso",
                      "escribir_suplementos", "_preparar_resultado", "DIR_TRABAJO"):
        assert prohibido not in fuente, prohibido


# ───────────────────────────────────────────────────────────── foco técnico


def _seleccion(evaluados: int = 10):
    from analista import foco as fo
    from analista import plan as plan_mod

    plan = plan_mod.armar(_lectura_alcista(), 2, "Oro")
    el = fo.Elegido({"ticker": "XAUUSD", "nombre": "Oro", "clase": "forex_commodities", "digits": 2},
                    SELECCION, plan)
    return fo.Seleccion(el, evaluados, AHORA)


def _no_llamar(*_):
    raise AssertionError("el foco no vuelve a leer el terminal: usa la lectura que lo eligió")


def lectores_foco(resultado):
    return lectores(foco=lambda ahora: resultado, catalogo=lambda t: ACTIVO, cierres=lambda t, m=None: CIERRES,
                    terminal=_no_llamar)


def test_foco_usa_la_lectura_que_lo_eligio_y_no_trae_estadistica(tmp_path):
    hecha = pr.preparar(Orden("oportunidad"), tmp_path, AHORA, lectores_foco(_seleccion()))
    p = hecha.pieza
    assert p["orden"]["pieza"] == "oportunidad" and p["orden"]["args"] == {"ticker": "XAUUSD"}
    assert "estadistica" not in p["datos"]["plan"] and "4.080,00" in p["datos"]["plan"]["invalidacion"]
    assert p["datos"]["seleccion"]["evaluados"] == 10
    assert p["datos"]["chip"].startswith("FOCO TÉCNICO DEL DÍA")
    assert set(p["editorial"]) == set(es.CAMPOS["oportunidad"])


def test_sin_foco_y_mercado_ilegible_fallan_con_su_texto(tmp_path):
    from analista import foco as fo

    with pytest.raises(pr.SinFocoError, match="configuración clara entre los 10"):
        pr.preparar(Orden("oportunidad"), tmp_path, AHORA, lectores_foco(fo.SinFoco(10, {"lejos del gatillo": 3})))
    with pytest.raises(pr.MercadoIlegibleError, match="No puedo leer el mercado"):
        pr.preparar(Orden("oportunidad"), tmp_path, AHORA, lectores_foco(fo.MercadoIlegible("MT5 no responde")))
    assert issubclass(pr.SinFocoError, pr.PreparacionFallida)


def test_foco_no_lleva_porcentajes_en_sus_datos(tmp_path):
    # La curva de tasas y los resultados de la agenda traen "%": en el foco no van, porque
    # se imprimirían al prospecto y agy, al citarlos, haría rechazar la pieza.
    import json

    lec = lectores_foco(_seleccion())
    lec.curva = lambda: ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": 1}}}, [])
    lec.jornada = lambda a: ([{**JORNADA[0], "actual": "0,3%", "consenso": "0,2%"}], [])
    hecha = pr.preparar(Orden("oportunidad"), tmp_path, AHORA, lec)
    assert "%" not in json.dumps(hecha.pieza["datos"], ensure_ascii=False)
    assert not hecha.pieza["datos"]["contexto"].get("curva_tasas")
