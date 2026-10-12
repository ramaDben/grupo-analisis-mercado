"""El gráfico de la pieza dibuja las líneas de la `Lectura` (enchufe, fase 2, S5)."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tradingview_grafico as tg  # noqa: E402
from estrategia.contrato import Linea  # noqa: E402

H4 = 4 * 3600
TIEMPOS = [1_000_000 + i * H4 for i in range(40)]


def _rows():
    return [{"time": t, "open": 10.0 + i * 0.1, "high": 10.5 + i * 0.1, "low": 9.5 + i * 0.1,
             "close": 10.2 + i * 0.1, "ema50": None, "ema100": None}
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
    assert "Línea de seguridad" in html and "Objetivo" in html
    assert "EMA 50" not in html


def test_las_lineas_de_otro_marco_solo_entran_si_son_horizontales():
    contexto_d1 = Linea("contexto", "diagonal", ((TIEMPOS[0], 9.0), (TIEMPOS[2], 9.4)), "D1", 2, "B", 10.0)
    html = tg.construir_html_tradingview(_rows(), "ORO", "H4", lineas=(SEGURIDAD, contexto_d1, OBJETIVO))
    assert "Línea de contexto" not in html


def test_el_canal_de_regresion_ya_no_existe():
    """Spec §6: el gráfico dibuja `Lectura.lineas`; el canal calculado aparte se borra."""
    assert not hasattr(tg, "_canal") and not hasattr(tg, "calcular_estructura")
