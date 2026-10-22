"""Tests para el suceso único del seguimiento intradía (Task 2).

Plan: docs/superpowers/plans/2026-10-21-seguimiento-suceso-unico.md §Task 2.
Todos los datos son sintéticos, sin MetaTrader 5 ni acceso a la red.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista.suceso import Suceso, del_dia, elegir, evaluar, valor_en  # noqa: E402
from estrategia.contrato import Escenario, Lectura, Linea, Referencia  # noqa: E402
from estrategia.tori.parametros import Parametros  # noqa: E402

SCL = ZoneInfo("America/Santiago")

_ESCENARIOS_DUMMY = (
    Escenario("⬆️", "Prueba", "Escenario alcista"),
    Escenario("↔️", "Rango", "Escenario lateral"),
    Escenario("⬇️", "Ruptura", "Escenario bajista"),
)


def _crear_linea(
    tipo: str = "horizontal",
    puntos: tuple[tuple[int, float], ...] = ((1000, 100.0),),
    calidad: str = "A+",
    valor_actual: float = 100.0,
) -> Linea:
    return Linea(
        rol="seguridad",
        tipo=tipo,  # type: ignore[arg-type]
        puntos=puntos,
        marco="M15",
        toques=3,
        calidad=calidad,
        valor_actual=valor_actual,
    )


def _crear_lectura(
    ticker: str = "XAUUSD",
    direccion: str = "ALCISTA",
    estado: str = "TENDENCIA",
    linea: Linea | None = None,
    objetivo: float | None = 110.0,
    precio: float = 100.0,
    atr: float = 2.0,
    invalidacion: float | None = None,
) -> Lectura:
    vig = Referencia(precio=linea.valor_actual if linea else precio, etiqueta="línea de control", linea=linea)
    obj = Referencia(precio=objetivo, etiqueta="objetivo") if objetivo is not None else None
    return Lectura(
        ticker=ticker,
        marco="M15",
        precio=precio,
        direccion=direccion,  # type: ignore[arg-type]
        estado=estado,  # type: ignore[arg-type]
        lineas=(linea,) if linea else (),
        en_prueba=None,
        vigilar=vig,
        invalidacion=Referencia(precio=invalidacion, etiqueta="línea de control") if invalidacion is not None else None,
        objetivo=obj,
        escenarios=_ESCENARIOS_DUMMY,
        salida="Salida de prueba",
        conceptos=(),
        avisos=(),
        metricas={"atr": atr},
        vela=1000,
    )


def _vela_5m(time: int, open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {"time": float(time), "open": open_, "high": high, "low": low, "close": close}


# --- Tests de elegir ---


def test_elegir_lateral_o_rango_es_none() -> None:
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    linea = _crear_linea()

    # 1. Dirección LATERAL
    lec_lateral = _crear_lectura(direccion="LATERAL", linea=linea)
    assert elegir(lec_lateral, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00") is None

    # 2. Estado RANGO
    lec_rango = _crear_lectura(estado="RANGO", linea=linea)
    assert elegir(lec_rango, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00") is None

    # 3. Sin línea a vigilar
    lec_sin_linea = _crear_lectura(linea=None)
    assert elegir(lec_sin_linea, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00") is None


def test_elegir_diagonal_calcula_pendiente_por_vela() -> None:
    # Anclas en los índices 10 y 40 con precios 100 y 130 -> pendiente == 1.0
    tiempos_m15 = [1000 + i * 900 for i in range(50)]
    t1, p1 = tiempos_m15[10], 100.0
    t2, p2 = tiempos_m15[40], 130.0
    linea = _crear_linea(
        tipo="diagonal",
        puntos=((t1, p1), (t2, p2)),
        calidad="A+",
        valor_actual=139.0,
    )
    p = Parametros(tolerancia_toque_atr=0.25)
    lec = _crear_lectura(direccion="ALCISTA", linea=linea, invalidacion=134.0, atr=4.0)

    suceso = elegir(lec, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00", p=p)

    assert suceso is not None
    assert suceso.ticker == "XAUUSD"
    assert suceso.fecha == "2026-10-21"
    assert suceso.fijado == "2026-10-21T10:00"
    assert suceso.sentido == "ALCISTA"
    assert suceso.t_ref == tiempos_m15[-1]
    assert suceso.valor_ref == 139.0
    assert suceso.pendiente == 1.0  # (130 - 100) / (40 - 10) = 30 / 30 = 1.0
    assert suceso.objetivo == 149.0  # 1:2: riesgo 139 - 134 = 5, objetivo 139 + 10
    assert suceso.calidad == "A+"
    assert suceso.tolerancia == 1.0  # 0.25 * 4.0


# --- Tests de valor_en ---


def test_valor_en_no_avanza_en_hueco() -> None:
    # Hay un hueco de 3600 s entre dos velas M15, y el valor a mitad del hueco es igual al de la
    # vela siguiente menos una pendiente.
    t0 = 10000
    t1 = t0 + 900 + 3600  # 14500 (hueco de 3600s entre 10900 y 14500)
    t2 = t1 + 900  # 15400
    tiempos_m15 = [t0, t1, t2]

    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t0,
        valor_ref=100.0,
        pendiente=2.0,
        objetivo=120.0,
        calidad="A+",
        tolerancia=1.0,
    )

    mitad_hueco = t0 + 900 + 1800  # 12700
    cierre_vela_siguiente = t1 + 900  # 15400

    v_mitad = valor_en(s, tiempos_m15, mitad_hueco)
    v_siguiente = valor_en(s, tiempos_m15, cierre_vela_siguiente)

    assert v_mitad == v_siguiente - s.pendiente


def test_valor_en_antes_de_la_ventana_levanta() -> None:
    tiempos_m15 = [10000, 10900, 11800]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=10000,
        valor_ref=100.0,
        pendiente=1.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=1.0,
    )
    with pytest.raises(ValueError):
        valor_en(s, tiempos_m15, 9999)


# --- Tests de evaluar ---


def test_evaluar_esperando() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Velas de 5m con precios lejos de la línea (low > 102.0)
    velas = [
        _vela_5m(t_ref + 900, open_=105.0, high=106.0, low=104.0, close=105.0),
        _vela_5m(t_ref + 1200, open_=105.0, high=107.0, low=104.5, close=106.0),
    ]
    # Precio vivo lejos del nivel (106.0)
    av = evaluar(s, velas, precio=106.0, tiempos_m15=tiempos_m15)
    assert av.estado == "esperando"
    assert av.valor_linea == 100.0


def test_evaluar_en_nivel() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Ninguna vela tocó aún
    velas = [
        _vela_5m(t_ref + 900, open_=105.0, high=106.0, low=103.0, close=104.0),
    ]
    # Precio vivo está en 101.5 (a <= tolerancia 2.0 de la línea 100.0)
    av = evaluar(s, velas, precio=101.5, tiempos_m15=tiempos_m15)
    assert av.estado == "en_nivel"


def test_evaluar_rebotando() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Vela 1: tocó la línea (low=101.0 <= 102.0) y cerró por encima (close=103.0 >= 100.0)
    velas = [
        _vela_5m(t_ref + 900, open_=104.0, high=104.0, low=101.0, close=103.0),
    ]
    # Precio vivo se aleja al alza fuera de tolerancia (105.0 > 102.0), sin llegar a objetivo (110.0)
    av = evaluar(s, velas, precio=105.0, tiempos_m15=tiempos_m15)
    assert av.estado == "rebotando"


def test_evaluar_cumplido() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Vela 1: toca la línea. Vela 2: alcanza objetivo (high >= 110.0)
    velas = [
        _vela_5m(t_ref + 900, open_=104.0, high=104.0, low=101.0, close=103.0),
        _vela_5m(t_ref + 1200, open_=103.0, high=110.5, low=103.0, close=109.0),
    ]
    av = evaluar(s, velas, precio=109.0, tiempos_m15=tiempos_m15)
    assert av.estado == "cumplido"


def test_evaluar_ruptura_por_cierre_5m() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Vela de 5m con close un tick bajo la línea (99.99 < 100.0)
    velas = [
        _vela_5m(t_ref + 900, open_=102.0, high=102.0, low=99.5, close=99.99),
    ]
    av = evaluar(s, velas, precio=99.99, tiempos_m15=tiempos_m15)
    assert av.estado == "ruptura"


def test_evaluar_toca_y_cierra_al_otro_lado_es_ruptura() -> None:
    # Review Focus 3: Una vela de 5m que toca la línea y cierra al otro lado cuenta como ruptura
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Low toca la zona (99.5 <= 102.0), pero close cierra bajo la línea (99.8 < 100.0)
    velas = [
        _vela_5m(t_ref + 900, open_=101.0, high=101.5, low=99.5, close=99.8),
    ]
    av = evaluar(s, velas, precio=99.8, tiempos_m15=tiempos_m15)
    assert av.estado == "ruptura"


def test_evaluar_cumplido_antes_de_ruptura_sigue_cumplido() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Vela 1: toca
    # Vela 2: llega al objetivo
    # Vela 3: cierra bajo la línea (ruptura posterior)
    velas = [
        _vela_5m(t_ref + 900, open_=104.0, high=104.0, low=101.0, close=103.0),
        _vela_5m(t_ref + 1200, open_=103.0, high=111.0, low=103.0, close=109.0),
        _vela_5m(t_ref + 1500, open_=105.0, high=105.0, low=98.0, close=98.5),
    ]
    av = evaluar(s, velas, precio=98.5, tiempos_m15=tiempos_m15)
    assert av.estado == "cumplido"


def test_evaluar_sin_objetivo_nunca_cumplido() -> None:
    # Review Focus 4: sin objetivo, el estado nunca llega a cumplido
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=None,  # sin objetivo
        calidad="A+",
        tolerancia=2.0,
    )
    velas = [
        _vela_5m(t_ref + 900, open_=104.0, high=104.0, low=101.0, close=103.0),
        _vela_5m(t_ref + 1200, open_=103.0, high=200.0, low=103.0, close=195.0),
    ]
    av = evaluar(s, velas, precio=195.0, tiempos_m15=tiempos_m15)
    assert av.estado == "rebotando"
    assert av.estado != "cumplido"


def test_evaluar_bajista_espejo() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="BAJISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=90.0,
        calidad="A+",
        tolerancia=2.0,
    )

    # 1. Esperando: lejos de la línea hacia abajo
    velas_esp = [
        _vela_5m(t_ref + 900, open_=95.0, high=96.0, low=94.0, close=95.0),
    ]
    assert evaluar(s, velas_esp, precio=95.0, tiempos_m15=tiempos_m15).estado == "esperando"

    # 2. En nivel: precio cerca de la línea (abs(98.5 - 100.0) <= 2.0)
    assert evaluar(s, velas_esp, precio=98.5, tiempos_m15=tiempos_m15).estado == "en_nivel"

    # 3. Ruptura: close por encima de la línea (100.05 > 100.0)
    velas_rup = [
        _vela_5m(t_ref + 900, open_=99.0, high=100.5, low=98.5, close=100.05),
    ]
    assert evaluar(s, velas_rup, precio=100.05, tiempos_m15=tiempos_m15).estado == "ruptura"

    # 4. Toca y cierra al otro lado es ruptura
    velas_toca_rup = [
        _vela_5m(t_ref + 900, open_=98.0, high=100.2, low=98.0, close=100.1),
    ]
    assert evaluar(s, velas_toca_rup, precio=100.1, tiempos_m15=tiempos_m15).estado == "ruptura"

    # 5. Rebotando: tocó la resistencia (high >= 100 - 2 = 98.0) y cerró bajo la línea, precio cae
    velas_reb = [
        _vela_5m(t_ref + 900, open_=97.0, high=99.0, low=97.0, close=98.0),
    ]
    assert evaluar(s, velas_reb, precio=95.0, tiempos_m15=tiempos_m15).estado == "rebotando"

    # 6. Cumplido: tocó y luego low <= objetivo (90.0)
    velas_cump = [
        _vela_5m(t_ref + 900, open_=97.0, high=99.0, low=97.0, close=98.0),
        _vela_5m(t_ref + 1200, open_=98.0, high=98.0, low=89.5, close=91.0),
    ]
    assert evaluar(s, velas_cump, precio=91.0, tiempos_m15=tiempos_m15).estado == "cumplido"


def test_evaluar_ignora_velas_anteriores_a_la_fijacion() -> None:
    t_ref = 10000
    tiempos_m15 = [t_ref, t_ref + 900]
    s = Suceso(
        ticker="XAUUSD",
        fecha="2026-10-21",
        fijado="2026-10-21T10:00",
        sentido="ALCISTA",
        t_ref=t_ref,
        valor_ref=100.0,
        pendiente=0.0,
        objetivo=110.0,
        calidad="A+",
        tolerancia=2.0,
    )
    # Velas con time < t_ref + 900: una vela anterior cerró en 90.0 (ruptura si se leyera)
    velas = [
        _vela_5m(t_ref + 300, open_=95.0, high=96.0, low=89.0, close=90.0),
        _vela_5m(t_ref + 600, open_=95.0, high=96.0, low=89.0, close=90.0),
        _vela_5m(t_ref + 900, open_=105.0, high=106.0, low=104.0, close=105.0),
    ]
    av = evaluar(s, velas, precio=105.0, tiempos_m15=tiempos_m15)
    assert av.estado == "esperando"  # la ruptura de velas anteriores fue ignorada


# --- Tests de del_dia y persistencia ---


def test_del_dia_fija_una_vez_y_reutiliza(tmp_path: Path) -> None:
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    linea1 = _crear_linea(valor_actual=100.0)
    lec1 = _crear_lectura(linea=linea1, invalidacion=90.0)

    ahora = datetime(2026, 10, 21, 10, 30, tzinfo=SCL)

    # Primera llamada: fija y guarda
    s1 = del_dia(lec1, tiempos_m15, "XAUUSD", ahora, base=tmp_path)
    assert s1 is not None
    assert s1.valor_ref == 100.0
    assert s1.objetivo == 120.0  # riesgo 10, objetivo 1:2

    # Segunda llamada el mismo día con otra lectura distinta: debe devolver el del primero
    linea2 = _crear_linea(valor_actual=200.0)
    lec2 = _crear_lectura(linea=linea2, invalidacion=150.0)

    s2 = del_dia(lec2, tiempos_m15, "XAUUSD", ahora, base=tmp_path)
    assert s2 is not None
    assert s2.valor_ref == 100.0
    assert s2.objetivo == 120.0
    assert s2 == s1


def test_del_dia_otro_dia_fija_nuevo(tmp_path: Path) -> None:
    # Review Focus 2: Si la fecha cambió, se fija uno nuevo y el de ayer se ignora
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    linea1 = _crear_linea(valor_actual=100.0)
    lec1 = _crear_lectura(linea=linea1, invalidacion=90.0)

    dia1 = datetime(2026, 10, 21, 10, 30, tzinfo=SCL)
    s1 = del_dia(lec1, tiempos_m15, "XAUUSD", dia1, base=tmp_path)
    assert s1 is not None
    assert s1.fecha == "2026-10-21"

    # Al día siguiente con lectura nueva
    linea2 = _crear_linea(valor_actual=105.0)
    lec2 = _crear_lectura(linea=linea2, invalidacion=95.0)
    dia2 = datetime(2026, 10, 22, 9, 30, tzinfo=SCL)

    s2 = del_dia(lec2, tiempos_m15, "XAUUSD", dia2, base=tmp_path)
    assert s2 is not None
    assert s2.fecha == "2026-10-22"
    assert s2.valor_ref == 105.0
    assert s2.objetivo == 125.0  # riesgo 10, objetivo 1:2


def test_del_dia_sin_direccion_no_escribe(tmp_path: Path) -> None:
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    linea = _crear_linea()
    lec_lateral = _crear_lectura(direccion="LATERAL", linea=linea)

    ahora = datetime(2026, 10, 21, 10, 30, tzinfo=SCL)
    res = del_dia(lec_lateral, tiempos_m15, "XAUUSD", ahora, base=tmp_path)

    assert res is None
    # No debe haber creado ningún archivo ni carpeta
    archivos = list(tmp_path.rglob("*.json"))
    assert len(archivos) == 0


def test_elegir_bajista_pone_el_objetivo_a_dos_veces_el_riesgo_hacia_abajo() -> None:
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    lec = _crear_lectura(direccion="BAJISTA", linea=_crear_linea(valor_actual=100.0), invalidacion=104.0)
    s = elegir(lec, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00")
    assert s is not None and s.objetivo == 92.0


def test_elegir_sin_invalidacion_deja_el_suceso_sin_objetivo() -> None:
    tiempos_m15 = [1000 + i * 900 for i in range(10)]
    lec = _crear_lectura(linea=_crear_linea(valor_actual=100.0), objetivo=130.0)
    s = elegir(lec, tiempos_m15, "XAUUSD", "2026-10-21", "2026-10-21T10:00")
    assert s is not None and s.objetivo is None  # no se hereda el objetivo de la lectura
