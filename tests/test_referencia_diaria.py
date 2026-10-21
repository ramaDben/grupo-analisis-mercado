"""Tests para la referencia diaria intradía (Encargo A)."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import referencia_diaria as rd  # noqa: E402
from estrategia.contrato import Escenario, Lectura, Linea, Prueba, Referencia, VelaEnCurso  # noqa: E402

SCL = ZoneInfo("America/Santiago")


def _linea(rol="seguridad", puntos=((100, 10.0), (200, 11.0)), marco="H1"):
    return Linea(rol=rol, tipo="diagonal", puntos=puntos, marco=marco, toques=3,
                 calidad="A+", valor_actual=11.5)


def _lectura(estado="TENDENCIA", lineas=None, ticker="XAUUSD", marco="H1", vela=250, precio=12.0):
    lineas = lineas if lineas is not None else (_linea(marco=marco), _linea("accion", ((150, 13.0), (250, 12.0)), marco=marco))
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker=ticker, marco=marco, precio=precio, direccion="ALCISTA", estado=estado,
                   lineas=lineas, en_prueba=None, vigilar=Referencia(11.5, "línea alcista de control"),
                   invalidacion=None, objetivo=None, escenarios=esc, salida="s", conceptos=(),
                   avisos=(), metricas={"atr": 1.0}, vela=vela)


class _EstrategiaFalsa:
    """Estrategia mínima configurable para pruebas de referencia diaria."""

    def __init__(self, lectura_a_devolver: Lectura, lectura_seguir: Lectura | None = None):
        from estrategia.contrato import Etiqueta, Marcos
        self.marcos = Marcos(("W1", "D1", "H4"), "H1",
                             {"W1": 5, "D1": 5, "H4": 5, "H1": 10},
                             {"W1": Etiqueta("c", "m"), "D1": Etiqueta("p", "s"),
                              "H4": Etiqueta("s", "u"), "H1": Etiqueta("i", "d")})
        self.lectura_leer = lectura_a_devolver
        self.lectura_seguir = lectura_seguir or lectura_a_devolver
        self.llamadas: list[str] = []

    def leer(self, ticker, velas, digits, en_curso=None):
        self.llamadas.append("leer")
        return self.lectura_leer

    def seguir(self, referencia, velas, digits, en_curso=None):
        self.llamadas.append("seguir")
        return self.lectura_seguir


def _velas_de_hoy(ahora: datetime, n: int = 10) -> dict[str, pd.DataFrame]:
    ts_base = int(ahora.astimezone(timezone.utc).timestamp())
    filas = []
    for i in range(n):
        ts = ts_base - (n - 1 - i) * 3600
        filas.append({"time": ts, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0})
    return {"H1": pd.DataFrame(filas)}


def _velas_cerrado_hoy(ahora: datetime, n: int = 10) -> dict[str, pd.DataFrame]:
    # Última vela hace 2 días (fin de semana o mercado cerrado)
    ts_base = int((ahora - timedelta(days=2)).astimezone(timezone.utc).timestamp())
    filas = []
    for i in range(n):
        ts = ts_base - (n - 1 - i) * 3600
        filas.append({"time": ts, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0})
    return {"H1": pd.DataFrame(filas)}


def _en_curso(ahora: datetime) -> VelaEnCurso:
    return VelaEnCurso(int(ahora.timestamp()), 11.0, ahora + timedelta(hours=1))


def test_fecha_de_santiago():
    dt_noche = datetime(2026, 10, 21, 23, 45, tzinfo=SCL)
    dt_madrugada = datetime(2026, 10, 22, 0, 15, tzinfo=SCL)
    assert rd.fecha_de(dt_noche) == "2026-10-21"
    assert rd.fecha_de(dt_madrugada) == "2026-10-22"

    # En UTC las 01:00 del 22 de octubre son las 22:00 del 21 en Santiago (UTC-3)
    dt_utc = datetime(2026, 10, 22, 1, 0, tzinfo=timezone.utc)
    assert rd.fecha_de(dt_utc) == "2026-10-21"


def test_slug_y_ruta(tmp_path):
    p = rd.ruta("2026-10-21", "US100.spot", base=tmp_path)
    assert p == tmp_path / "2026-10-21" / "us100.json"

    p_accion = rd.ruta("2026-10-21", "#NVDA", base=tmp_path)
    assert p_accion == tmp_path / "2026-10-21" / "nvda.json"


def test_guardar_y_cargar_ida_y_vuelta(tmp_path):
    lec = _lectura(ticker="EURUSD")
    ahora = datetime(2026, 10, 21, 10, 30, tzinfo=SCL)
    destino = rd.guardar("2026-10-21", "EURUSD", lec, base=tmp_path, ahora=ahora)
    assert destino == tmp_path / "2026-10-21" / "eurusd.json"
    assert destino.exists()

    datos = json.loads(destino.read_text(encoding="utf-8"))
    assert datos["ticker"] == "EURUSD"
    assert datos["fecha"] == "2026-10-21"

    cargada = rd.cargar("2026-10-21", "EURUSD", base=tmp_path)
    assert cargada == lec


def test_cargar_inexistente_devuelve_none(tmp_path):
    assert rd.cargar("2026-10-21", "INEXISTENTE", base=tmp_path) is None


def test_guardar_en_prueba_levanta_error(tmp_path):
    lec = _lectura()
    prueba = replace(lec, estado="PRUEBA",
                     en_prueba=Prueba(_linea(), 11.6, datetime(2026, 10, 21, 13, 0, tzinfo=SCL)))
    with pytest.raises(ValueError, match="PRUEBA"):
        rd.guardar("2026-10-21", "XAUUSD", prueba, base=tmp_path)


def test_mercado_cerrado_devuelve_none(tmp_path):
    ahora = datetime(2026, 10, 21, 14, 0, tzinfo=SCL)
    velas_cerrado = _velas_cerrado_hoy(ahora)
    est = _EstrategiaFalsa(_lectura())
    # Sin velas nuevas hoy, no se debe inventar referencia: devuelve None
    ref = rd.referencia_del_dia(est, "XAUUSD", 2, ahora, base=tmp_path, velas=velas_cerrado, en_curso=None)
    assert ref is None
    # Tampoco debe guardar nada en disco
    assert rd.cargar("2026-10-21", "XAUUSD", base=tmp_path) is None


def test_mismo_dia_reutiliza_referencia(tmp_path):
    ahora_mañana = datetime(2026, 10, 21, 9, 30, tzinfo=SCL)
    velas_mañana = _velas_de_hoy(ahora_mañana)
    primera_lectura = _lectura(precio=100.0)
    est1 = _EstrategiaFalsa(primera_lectura)

    # 1. Primera consulta de la mañana: lee y guarda
    ref1 = rd.referencia_del_dia(est1, "XAUUSD", 2, ahora_mañana, base=tmp_path, velas=velas_mañana,
                                en_curso=_en_curso(ahora_mañana))
    assert ref1 == primera_lectura
    assert "leer" in est1.llamadas

    # 2. Segunda consulta a media tarde el mismo día:
    ahora_tarde = datetime(2026, 10, 21, 15, 45, tzinfo=SCL)
    velas_tarde = _velas_de_hoy(ahora_tarde)
    lectura_tarde = _lectura(precio=105.0)  # precio cambió pero estructura intacta
    est2 = _EstrategiaFalsa(lectura_a_devolver=lectura_tarde, lectura_seguir=primera_lectura)

    ref2 = rd.referencia_del_dia(est2, "XAUUSD", 2, ahora_tarde, base=tmp_path, velas=velas_tarde)
    # Debe reutilizar la primera referencia guardada
    assert ref2 == primera_lectura
    assert "leer" not in est2.llamadas


def test_otro_dia_no_reutiliza_referencia(tmp_path):
    ahora_dia1 = datetime(2026, 10, 21, 10, 0, tzinfo=SCL)
    velas_dia1 = _velas_de_hoy(ahora_dia1)
    lec_dia1 = _lectura(precio=100.0, vela=1000)
    est_dia1 = _EstrategiaFalsa(lec_dia1)

    ref1 = rd.referencia_del_dia(est_dia1, "XAUUSD", 2, ahora_dia1, base=tmp_path, velas=velas_dia1,
                                en_curso=_en_curso(ahora_dia1))
    assert ref1 == lec_dia1

    # Día siguiente
    ahora_dia2 = datetime(2026, 10, 22, 10, 0, tzinfo=SCL)
    velas_dia2 = _velas_de_hoy(ahora_dia2)
    lec_dia2 = _lectura(precio=110.0, vela=2000)
    est_dia2 = _EstrategiaFalsa(lec_dia2)

    ref2 = rd.referencia_del_dia(est_dia2, "XAUUSD", 2, ahora_dia2, base=tmp_path, velas=velas_dia2,
                                en_curso=_en_curso(ahora_dia2))
    # No reutiliza la del día 1, fija una nueva para el día 2
    assert ref2 == lec_dia2
    assert rd.cargar("2026-10-21", "XAUUSD", base=tmp_path) == lec_dia1
    assert rd.cargar("2026-10-22", "XAUUSD", base=tmp_path) == lec_dia2


def test_reemplazo_por_ruptura(tmp_path):
    ahora = datetime(2026, 10, 21, 9, 30, tzinfo=SCL)
    velas = _velas_de_hoy(ahora)
    ref_inicial = _lectura(estado="TENDENCIA")
    rd.guardar("2026-10-21", "XAUUSD", ref_inicial, base=tmp_path, ahora=ahora)

    # Durante el día ocurre una ruptura
    lectura_rota = replace(ref_inicial, estado="RUPTURA", lineas=(replace(ref_inicial.lineas[0], rol="accion"),))
    nueva_ref = replace(ref_inicial, estado="RUPTURA", vela=999)
    est_ruptura = _EstrategiaFalsa(lectura_a_devolver=nueva_ref, lectura_seguir=lectura_rota)

    ref_actualizada = rd.referencia_del_dia(est_ruptura, "XAUUSD", 2, ahora + timedelta(hours=3),
                                            base=tmp_path, velas=velas)
    assert ref_actualizada == nueva_ref
    # Verifica que en disco se actualizó con la nueva referencia
    assert rd.cargar("2026-10-21", "XAUUSD", base=tmp_path) == nueva_ref
