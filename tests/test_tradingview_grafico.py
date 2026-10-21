"""El gráfico de la pieza dibuja las líneas de la `Lectura` (enchufe, fase 2, S5)."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest  # noqa: E402

pytest.importorskip("PIL")  # extra `stories`: el CI corre sin él
import tradingview_grafico as tg  # noqa: E402
from estrategia.contrato import Linea  # noqa: E402

H4 = 4 * 3600
TIEMPOS = [1_000_000 + i * H4 for i in range(40)]


def _rows():
    return [{"time": t, "open": 10.0 + i * 0.1, "high": 10.5 + i * 0.1, "low": 9.5 + i * 0.1,
             "close": 10.2 + i * 0.1}
            for i, t in enumerate(TIEMPOS)]


SEGURIDAD = Linea("seguridad", "diagonal", ((TIEMPOS[5], 9.5), (TIEMPOS[15], 10.5)), "H4", 3, "A+", 12.9)
OBJETIVO = Linea("objetivo", "horizontal", ((TIEMPOS[0], 15.0),), "D1", 2, "", 15.0)


def test_una_diagonal_se_dibuja_desde_su_ancla_y_se_proyecta_por_su_pendiente():
    series, omitidas = tg.series_de_lineas((SEGURIDAD,), TIEMPOS, proyeccion=5)
    assert omitidas == []
    puntos = series[0]["puntos"]
    assert puntos[0] == {"time": TIEMPOS[5], "value": 9.5}
    assert len(puntos) == (len(TIEMPOS) - 1 + 5) - 5 + 1  # del ancla al final proyectado
    assert abs(puntos[10]["value"] - 10.5) < 1e-9  # la pendiente es en velas
    assert puntos[-1]["time"] == TIEMPOS[-1] + 5 * H4


def test_una_diagonal_con_el_ancla_fuera_de_la_ventana_se_omite_y_se_dice():
    vieja = Linea("contexto", "diagonal", ((1, 9.0), (TIEMPOS[3], 9.4)), "H4", 2, "B", 10.0)
    series, omitidas = tg.series_de_lineas((vieja,), TIEMPOS, proyeccion=5)
    assert series == [] and omitidas[0]["rol"] == "contexto"


def test_un_horizontal_es_un_precio():
    series, _ = tg.series_de_lineas((OBJETIVO,), TIEMPOS, proyeccion=5)
    assert series[0]["precio"] == 15.0 and series[0]["tipo"] == "horizontal"


def test_con_lineas_el_grafico_dibuja_la_lectura_y_no_las_medias():
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, OBJETIVO))
    assert "Línea de control" in html and "Objetivo" in html
    assert "EMA 50" not in html


def test_las_lineas_de_otro_marco_solo_entran_si_son_horizontales():
    contexto_d1 = Linea("contexto", "diagonal", ((TIEMPOS[0], 9.0), (TIEMPOS[2], 9.4)), "D1", 2, "B", 10.0)
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, contexto_d1, OBJETIVO))
    assert "Línea de contexto" not in html


def test_sin_lineas_tampoco_hay_medias():
    """Decisión del director 2026-10-12: ninguna imagen trae una segunda lectura técnica."""
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4")
    assert "EMA" not in html and "ema50" not in html


def _datos(html: str) -> dict:
    import json

    inicio = html.index("const D = ") + len("const D = ")
    return json.loads(html[inicio:html.index("\n", inicio)].rstrip(";"))


def test_un_horizontal_en_el_precio_de_una_zona_se_funde_con_ella():
    """2026-10-12: el objetivo del oro y el soporte en 4149,96 pintaban dos etiquetas
    apiladas que empujaban a las demás sobre el eje."""
    objetivo = Linea("objetivo", "horizontal", ((TIEMPOS[0], 12.5),), "D1", 2, "", 12.5)
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, objetivo),
                                         soporte=12.5, resistencia=14.0)
    d = _datos(html)
    assert [x["rol"] for x in d["lineas"]] == ["seguridad"]
    assert [z["rol"] for z in d["zonas"]] == ["RESISTENCIA", "SOPORTE · OBJETIVO"]
    assert "Objetivo" in html  # la leyenda lo sigue nombrando


def test_los_niveles_citados_van_en_el_eje_y_se_funden_si_coinciden():
    """Todo nivel que cita el texto de la lámina va trazado con su precio (oro W41: el 4.227,32
    del texto no estaba en el gráfico). Dos con el mismo precio son una etiqueta."""
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, OBJETIVO),
                                         niveles=[(12.9, "NIVEL A VIGILAR"), (12.9, "INVALIDACIÓN"),
                                                  (15.0, "OBJETIVO")])
    d = _datos(html)
    assert [x["rol"] for x in d["lineas"]] == ["seguridad"]
    assert [(z["precio"], z["rol"]) for z in d["zonas"]] == [(12.9, "NIVEL A VIGILAR · INVALIDACIÓN"),
                                                              (15.0, "OBJETIVO")]


def test_un_horizontal_lejos_de_las_zonas_se_dibuja_aparte():
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, OBJETIVO),
                                         soporte=12.5, resistencia=14.0)
    assert [x["rol"] for x in _datos(html)["lineas"]] == ["seguridad", "objetivo"]


def test_las_velas_ya_no_traen_medias():
    velas = [{"time": t, "open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1} for t in TIEMPOS]
    assert all(set(r) == {"time", "open", "high", "low", "close", "atr"}
               for r in tg.calcular_indicadores(velas))


class _Df:
    def __init__(self, n):
        self.filas = [{"time": TIEMPOS[0] + i * H4, "open": 10.0, "high": 10.5, "low": 9.5,
                       "close": 10.2} for i in range(n)]

    def __len__(self):
        return len(self.filas)

    def to_dict(self, orient):
        return self.filas


def _sin_terminal(monkeypatch, vistos):
    from market_data_mcp import mt5_client

    monkeypatch.setattr(mt5_client, "connect", lambda: None)

    def rates(ticker, tf, n):
        vistos["rates"] = (tf, n)
        return _Df(n)

    monkeypatch.setattr(mt5_client, "get_rates", rates)
    monkeypatch.setattr(tg, "renderizar_png", lambda html, destino, **kw: destino)

    def html(rows, simbolo, timeframe, **kw):
        vistos["html"] = {"timeframe": timeframe, **kw}
        return ""

    monkeypatch.setattr(tg, "construir_html_tradingview", html)


def test_sin_lineas_el_grafico_lee_la_lectura_del_activo(monkeypatch, tmp_path):
    """Las piezas ad-hoc y el CLI dibujan la misma lectura que el carrusel."""
    import pipeline_carrusel as pc

    from test_cierre_semanal_datos import _lectura

    lect = _lectura("XAUUSD", 4100.0, 4050.0, 4000.0, 4200.0)
    monkeypatch.setattr(tg, "leer_lectura", lambda ticker, digits: lect)
    vistos: dict = {}
    _sin_terminal(monkeypatch, vistos)
    tg.generar_grafico_tv("XAUUSD", "Oro", tmp_path / "g.png", timeframe=None, n_velas=60, digits=2)
    assert vistos["html"]["timeframe"] == "H4"
    assert vistos["html"]["lineas"] == lect.lineas
    assert (vistos["html"]["soporte"], vistos["html"]["resistencia"]) == pc.niveles_publicados(lect)
    assert vistos["rates"][1] >= pc.VELAS_GRAFICO_TV  # las anclas tienen que caer adentro


def test_niveles_explicitos_ganan_a_los_de_la_lectura(monkeypatch, tmp_path):
    from test_cierre_semanal_datos import _lectura

    lect = _lectura("XAUUSD", 4100.0, 4050.0, 4000.0, 4200.0)
    monkeypatch.setattr(tg, "leer_lectura", lambda ticker, digits: lect)
    vistos: dict = {}
    _sin_terminal(monkeypatch, vistos)
    tg.generar_grafico_tv("XAUUSD", "Oro", tmp_path / "g.png", timeframe="H1",
                          digits=2, soporte=4010.0, resistencia=4150.0)
    assert vistos["html"]["timeframe"] == "H1"
    assert (vistos["html"]["soporte"], vistos["html"]["resistencia"]) == (4010.0, 4150.0)


def test_sin_lectura_sale_sin_lineas_y_lo_avisa(monkeypatch, tmp_path, capsys):
    def falla(ticker, digits):
        raise RuntimeError("la estrategia no cubre este activo")

    monkeypatch.setattr(tg, "leer_lectura", falla)
    vistos: dict = {}
    _sin_terminal(monkeypatch, vistos)
    tg.generar_grafico_tv("MELI", "MercadoLibre", tmp_path / "g.png", timeframe=None, digits=2)
    assert vistos["html"]["lineas"] is None and vistos["html"]["timeframe"] == "H1"
    assert "sin la lectura" in capsys.readouterr().err


def test_el_canal_de_regresion_ya_no_existe():
    """Spec §6: el gráfico dibuja `Lectura.lineas`; el canal calculado aparte se borra."""
    assert not hasattr(tg, "_canal") and not hasattr(tg, "calcular_estructura")


def test_la_ventana_enmarca_a_la_diagonal_y_no_muestra_todas_las_velas():
    tiempos = list(range(0, 320 * 14400, 14400))
    corta = {"tipo": "diagonal", "puntos": [{"time": tiempos[295], "value": 1.0}]}
    assert tg.ventana_visible([corta], tiempos) == tg.VENTANA_MIN
    larga = {"tipo": "diagonal", "puntos": [{"time": tiempos[100], "value": 1.0}]}
    assert tg.ventana_visible([larga], tiempos) == 320
    assert tg.ventana_visible([], tiempos) == tg.VENTANA_SIN_DIAGONAL
