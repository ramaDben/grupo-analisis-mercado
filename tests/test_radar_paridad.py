"""Tests del control de paridad entre el radar y el indicador de MT5."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.tori.parametros import PARAMETROS as P
from estrategia.tori.radar import LecturaMarco, LineaRadar
from scripts.radar_paridad import (
    NOMBRES_INDICADOR,
    comparar,
    leer_objetos,
    ruta_objetos,
)

SANTIAGO = ZoneInfo("America/Santiago")
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "radar" / "chart_objects.json"


def _lectura(
    marco: str = "H4",
    lineas: tuple[LineaRadar, ...] = (),
    atr: float = 10.0,
) -> LecturaMarco:
    return LecturaMarco(
        marco=marco,
        estado="TENDENCIA",
        direccion="ALCISTA",
        lineas=lineas,
        eventos=(),
        avisos=(),
        vela=1700000000,
        atr=atr,
    )


def test_sin_archivo_devuelve_el_motivo(tmp_path: Path):
    ahora = datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO)
    msg_esperado = "no se pudo verificar la paridad: falta chart_objects.json (¿corre ChartObjectsExporter?)"
    assert leer_objetos(None, ahora) == msg_esperado
    assert leer_objetos(tmp_path / "inexistente.json", ahora) == msg_esperado


def test_archivo_viejo_devuelve_el_motivo(tmp_path: Path):
    # Generado a las 06:00, ahora a las 07:35 -> 95 minutos de antigüedad (> 60 min)
    archivo = tmp_path / "chart_objects.json"
    data = {
        "generated_at": "2026-10-26 06:00",
        "charts": [],
    }
    archivo.write_text(json.dumps(data), encoding="utf-8")
    ahora = datetime(2026, 10, 26, 7, 35, tzinfo=SANTIAGO)
    res = leer_objetos(archivo, ahora)
    assert res == "no se pudo verificar la paridad: chart_objects.json tiene 95 min"


def test_lineas_que_coinciden_no_emiten_nada():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # El fixture tiene XAUUSD H4 con seguridad=2650.10, accion=2670.50, soporte=2630.00, resistencia=2680.00
    lineas = (
        LineaRadar("seguridad", valor_actual=2649.00, valor_abierta=2650.10),
        LineaRadar("accion", valor_actual=2669.00, valor_abierta=2670.50),
        LineaRadar("soporte", valor_actual=2630.00, valor_abierta=2630.00),
        LineaRadar("resistencia", valor_actual=2680.00, valor_abierta=2680.00),
    )
    lecturas = {("XAUUSD", "H4"): _lectura("H4", lineas, atr=10.0)}
    digits = {"XAUUSD": 2}
    discrepancias = comparar(data, lecturas, digits, P)
    # Todo coincide: queda solo el resumen, que dice que sí se comparó.
    assert discrepancias == ["paridad: 1 gráfico comparado, 0 diferencias"]


def test_diferencia_mayor_que_la_tolerancia_se_informa_con_digits():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # Seguridad en el indicador: 2650.10.
    # En el motor: 2655.00. Diferencia 4.90 > 0.25 * 10 = 2.5 ATR
    lineas = (
        LineaRadar("seguridad", valor_actual=2649.00, valor_abierta=2655.00),
        LineaRadar("accion", valor_actual=2669.00, valor_abierta=2670.50),
        LineaRadar("soporte", valor_actual=2630.00, valor_abierta=2630.00),
        LineaRadar("resistencia", valor_actual=2680.00, valor_abierta=2680.00),
    )
    lecturas = {("XAUUSD", "H4"): _lectura("H4", lineas, atr=10.0)}
    digits = {"XAUUSD": 2}
    discrepancias = comparar(data, lecturas, digits, P)
    # El precio con el formato de la matriz (separador de miles) y el rol con su nombre visible.
    assert discrepancias == [
        "paridad: 1 gráfico comparado, 1 diferencia",
        "XAUUSD H4: indicador y motor difieren en la línea de control: 2,650.10 vs 2,655.00",
    ]


def test_linea_presente_en_un_solo_lado_se_informa():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # En motor falta acción, y tiene una línea que no está en indicador?
    # Probamos ambos casos:
    # 1. Indicador tiene acción (2670.50), motor no la tiene:
    lineas_sin_accion = (
        LineaRadar("seguridad", valor_actual=2649.00, valor_abierta=2650.10),
        LineaRadar("soporte", valor_actual=2630.00, valor_abierta=2630.00),
        LineaRadar("resistencia", valor_actual=2680.00, valor_abierta=2680.00),
    )
    lecturas = {("XAUUSD", "H4"): _lectura("H4", lineas_sin_accion, atr=10.0)}
    discrepancias = comparar(data, lecturas, {"XAUUSD": 2}, P)
    assert "XAUUSD H4: la línea de acción solo está en el indicador" in discrepancias

    # 2. Indicador no tiene acción (data sin GI_TV_DIAG_ACCION), motor sí la tiene:
    data_sin_accion = {
        "charts": [
            {
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "trendlines": [
                    {"name": "GI_TV_DIAG_SEGURIDAD", "valor_actual": 2650.10},
                    {"name": "GI_TV_LINE_SOPORTE", "valor_actual": 2630.00},
                    {"name": "GI_TV_LINE_RESISTENCIA", "valor_actual": 2680.00},
                ],
            }
        ]
    }
    lineas_con_accion = (
        LineaRadar("seguridad", valor_actual=2649.00, valor_abierta=2650.10),
        LineaRadar("accion", valor_actual=2669.00, valor_abierta=2670.50),
        LineaRadar("soporte", valor_actual=2630.00, valor_abierta=2630.00),
        LineaRadar("resistencia", valor_actual=2680.00, valor_abierta=2680.00),
    )
    lecturas2 = {("XAUUSD", "H4"): _lectura("H4", lineas_con_accion, atr=10.0)}
    discrepancias2 = comparar(data_sin_accion, lecturas2, {"XAUUSD": 2}, P)
    assert "XAUUSD H4: la línea de acción solo está en el motor" in discrepancias2


def test_graficos_sin_lectura_del_radar_se_ignoran():
    data = {
        "charts": [
            {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "trendlines": [
                    {"name": "GI_TV_DIAG_SEGURIDAD", "valor_actual": 1.0850},
                ],
            }
        ]
    }
    # lecturas no tiene ("EURUSD", "H1")
    lecturas = {
        ("XAUUSD", "H4"): _lectura(
            "H4",
            (LineaRadar("seguridad", 2650.10, 2650.10),),
            atr=10.0,
        )
    }
    discrepancias = comparar(data, lecturas, {"EURUSD": 4, "XAUUSD": 2}, P)
    assert discrepancias == ["paridad: ningún gráfico abierto coincide con un activo leído"]


def test_el_texto_de_paridad_nunca_dice_seguridad():
    # Una línea en un solo lado de cada rol, y una diferencia: recorre todos los mensajes.
    data = {"charts": [{"symbol": "XAUUSD", "timeframe": "H4", "trendlines": [
        {"name": "GI_TV_DIAG_SEGURIDAD", "valor_actual": 2650.10},
    ]}, {"symbol": "XAUUSD", "timeframe": "H1", "trendlines": []}]}
    lecturas = {
        ("XAUUSD", "H4"): _lectura("H4", (LineaRadar("seguridad", 2600.0, 2600.0),), atr=10.0),
        ("XAUUSD", "H1"): _lectura("H1", (LineaRadar("seguridad", 2600.0, 2600.0),), atr=10.0),
    }
    mensajes = comparar(data, lecturas, {"XAUUSD": 2}, P)
    assert mensajes[0] == "paridad: 2 gráficos comparados, 2 diferencias"
    assert any("línea de control" in m for m in mensajes)
    assert not any("seguridad" in m.lower() for m in mensajes)


def test_archivo_sin_fecha_no_se_compara(tmp_path: Path):
    ahora = datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO)
    archivo = tmp_path / "chart_objects.json"
    for data in ({"charts": []}, {"generated_at": "ayer", "charts": []}):
        archivo.write_text(json.dumps(data), encoding="utf-8")
        assert leer_objetos(archivo, ahora) == (
            "no se pudo verificar la paridad: chart_objects.json sin fecha")
    archivo.write_text(json.dumps({"generated_at": "2026-10-26 07:10", "charts": []}),
                       encoding="utf-8")
    assert leer_objetos(archivo, ahora) == {"generated_at": "2026-10-26 07:10", "charts": []}


def test_ruta_objetos(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MT5_COMMON_FILES", str(tmp_path))
    ruta = ruta_objetos()
    assert ruta == tmp_path / "chart_objects.json"

    monkeypatch.delenv("MT5_COMMON_FILES", raising=False)
    # Sin la variable de entorno y si .env no la define o la vaciamos
    monkeypatch.setenv("MT5_COMMON_FILES", "")
    assert ruta_objetos() is None
