"""Foco técnico del día: qué activo se elige, cuándo no hay, y cuándo no se puede saber."""
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

from analista import foco as fo  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 9, 12, 0, tzinfo=SCL)


def activo(ticker, clase="forex_commodities"):
    return {"ticker": ticker, "nombre": ticker, "clase": clase, "digits": 2}


def plan(sesgo="Alcista", gatillo=100.0, estado="Armado: x", hay=True, recorrido=3.0):
    if not hay:
        return {"hay_plan": False, "sesgo": sesgo, "motivo": "sin estructura"}
    return {"hay_plan": True, "sesgo": sesgo, "estado": estado, "gatillo": "g", "invalidacion": "i",
            "recorrido": "r", "niveles": {"gatillo": gatillo, "invalidacion": 90.0,
                                          "recorrido": recorrido, "vela": "2026-10-09 11:00:00"}}


def pf(precio, velas=None, **kw):
    return fo.PlanFoco(plan=plan(**kw), velas_desde_ruptura=velas, precio=precio, atr14=2.0)


# ───────────────────────────────────────────────────────────── elegible


def test_armado_cerca_del_gatillo_entra():
    assert fo.elegible(pf(98.5)) is None


def test_armado_lejos_del_gatillo_no_entra():
    assert "lejos" in fo.elegible(pf(97.0))


def test_activado_hace_3_velas_no_entra():
    assert "hace más de" in fo.elegible(pf(100.5, velas=2, estado="Activado: x"))


def test_activado_reciente_con_poco_avance_entra():
    assert fo.elegible(pf(100.5, velas=1, estado="Activado: x")) is None


def test_activado_con_mas_de_la_mitad_del_recorrido_no_entra():
    # recorrido 3,0: avanzar 1,8 desde el gatillo es el 60 %.
    assert "mitad" in fo.elegible(pf(101.8, velas=0, estado="Activado: x"))


def test_bajista_mide_el_avance_hacia_abajo():
    assert fo.elegible(pf(99.5, velas=0, sesgo="Bajista", estado="Activado: x")) is None
    assert "mitad" in fo.elegible(pf(98.0, velas=0, sesgo="Bajista", estado="Activado: x"))


def test_invalidado_y_sin_estructura_no_entran():
    assert "invalidado" in fo.elegible(pf(95.0, velas=0, estado="Invalidado: x"))
    assert "estructura" in fo.elegible(pf(95.0, hay=False))


# ───────────────────────────────────────────────────────────── universo e índices


def test_universo_de_ventas_suma_us100_y_brent_y_respeta_lo_apagado():
    tickers = {a["ticker"] for a in fo.universo_ventas()}
    assert {"US100.spot", "BRENT.spot", "XAUUSD", "USDCLP"} <= tickers
    # Índices, acciones y cripto están apagados: solo entra el US100 agregado a mano.
    assert not tickers & {"US500.spot", "US30.spot", "BTCUSD", "QQQ.US"}


@pytest.mark.parametrize("dia", ["2026-01-15", "2026-04-15", "2026-10-09"])
def test_indice_solo_desde_la_apertura_de_nueva_york(dia):
    # Las tres configuraciones del desfase Chile / Nueva York del año.
    ny = ZoneInfo("America/New_York")
    a, m, d = (int(x) for x in dia.split("-"))
    antes = datetime(a, m, d, 9, 59, tzinfo=ny).astimezone(SCL)
    despues = datetime(a, m, d, 10, 0, tzinfo=ny).astimezone(SCL)
    us100 = activo("US100.spot", "indices")
    assert not fo.indice_habilitado(us100, antes)
    assert fo.indice_habilitado(us100, despues)
    assert fo.indice_habilitado(activo("XAUUSD"), antes)


# ───────────────────────────────────────────────────────────── seleccionar


def evaluacion(tecnico, momentum, direccion="ALCISTA", espacio=0):
    return {"direccion": direccion, "factores": {
        "tecnico": {"puntos": tecnico}, "momentum": {"puntos": momentum},
        "espacio": {"puntos": espacio}, "catalizador": {"puntos": 25}}}


def lectores(evals, planes, edades=None, conectar=(), contexto=None, analizador=None):
    def evaluar(a, eventos, delta, ahora, analizador):
        analizador(a["ticker"], "H1")
        analizador(a["ticker"], "D1")
        return evals[a["ticker"]]

    return fo.LectoresFoco(
        conectar=lambda: list(conectar),
        contexto_macro=lambda ahora: contexto or ([], None, []),
        analizador=analizador or (lambda t, m: {"price": 1.0}),
        evaluar=evaluar,
        edad_tick=lambda t: (edades or {}).get(t, 1.0),
        serie=lambda t: None,
        armar_plan=lambda df, h1, a, sesgo: planes[a["ticker"]],
    )


def test_gana_el_cercano_al_gatillo_aunque_el_otro_tenga_mas_espacio():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    evals = {"XAUUSD": evaluacion(30, 20), "EURUSD": evaluacion(10, 10, espacio=20)}
    planes = {"XAUUSD": pf(97.0), "EURUSD": pf(99.5)}  # el oro está lejos de su gatillo
    r = fo.seleccionar(univ, AHORA, lectores(evals, planes))
    assert isinstance(r, fo.Seleccion) and r.elegido.activo["ticker"] == "EURUSD"
    assert r.evaluados == 2


def test_ordena_por_tecnico_y_momentum_no_por_catalizador_ni_espacio():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    evals = {"XAUUSD": evaluacion(20, 20), "EURUSD": evaluacion(10, 10, espacio=20)}
    planes = {"XAUUSD": pf(99.0), "EURUSD": pf(99.5)}
    assert fo.seleccionar(univ, AHORA, lectores(evals, planes)).elegido.activo["ticker"] == "XAUUSD"


def test_empate_desempata_por_distancia_y_despues_por_ticker():
    univ = [activo("GBPUSD"), activo("EURUSD"), activo("USDJPY")]
    evals = {t: evaluacion(20, 10) for t in ("GBPUSD", "EURUSD", "USDJPY")}
    planes = {"GBPUSD": pf(99.0), "EURUSD": pf(99.0), "USDJPY": pf(98.0)}
    assert fo.seleccionar(univ, AHORA, lectores(evals, planes)).elegido.activo["ticker"] == "EURUSD"


def test_mercado_cerrado_no_entra():
    univ = [activo("XAUUSD")]
    r = fo.seleccionar(univ, AHORA, lectores({"XAUUSD": evaluacion(30, 20)}, {"XAUUSD": pf(99.5)},
                                             edades={"XAUUSD": 40.0}))
    assert isinstance(r, fo.SinFoco) and "mercado cerrado" in r.texto()


def test_sin_elegibles_explica_los_motivos_agrupados():
    univ = [activo("XAUUSD"), activo("EURUSD"), activo("GBPUSD")]
    evals = {"XAUUSD": {"excluido": "ATR diario consumido al 95%"},
             "EURUSD": {"excluido": "blackout por NFP (09:15-10:00 hora Chile)"},
             "GBPUSD": evaluacion(20, 10)}
    r = fo.seleccionar(univ, AHORA, lectores(evals, {"GBPUSD": pf(90.0)}))
    assert isinstance(r, fo.SinFoco)
    texto = r.texto()
    assert "3 activos" in texto and "sin recorrido" in texto and "dato económico" in texto and "lejos" in texto


def test_mt5_caido_es_ilegible_y_no_sin_foco():
    r = fo.seleccionar([activo("XAUUSD")], AHORA, lectores({}, {}, conectar=["MT5 no conectó"]))
    assert isinstance(r, fo.MercadoIlegible)


def test_todos_con_error_del_terminal_es_ilegible():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    evals = {t: {"excluido": "MT5_ERROR: sin datos"} for t in ("XAUUSD", "EURUSD")}
    r = fo.seleccionar(univ, AHORA, lectores(evals, {}, analizador=lambda t, m: {"error": "MT5_ERROR"}))
    assert isinstance(r, fo.MercadoIlegible)


def test_calendario_caido_es_ilegible():
    ctx = ([], None, ["calendario no disponible (TIMEOUT): no se pudieron verificar blackouts"])
    r = fo.seleccionar([activo("XAUUSD")], AHORA,
                       lectores({"XAUUSD": evaluacion(30, 20)}, {"XAUUSD": pf(99.5)}, contexto=ctx))
    assert isinstance(r, fo.MercadoIlegible) and "calendario" in r.motivo


def test_el_aviso_de_calendario_caido_coincide_con_el_del_escaner(monkeypatch):
    # Contrato de nombres: el foco reconoce el calendario caído por el texto del escáner.
    import screener_gi as sc
    from market_data_mcp.tools import calendar

    monkeypatch.setattr(calendar, "cargar_calendario", lambda **kw: {"error": "TIMEOUT"})
    _, _, avisos = sc._contexto_macro(AHORA)
    assert fo.calendario_caido(avisos)


def test_el_analizador_lee_una_vez_por_marco():
    llamadas = []
    memo = fo.AnalizadorMemo(lambda t, m: llamadas.append((t, m)) or {"price": 1.0})
    memo("XAUUSD", "H1"), memo("XAUUSD", "H1"), memo("XAUUSD", "D1")
    assert llamadas == [("XAUUSD", "H1"), ("XAUUSD", "D1")]


def test_el_elegido_trae_la_lectura_que_lo_eligio():
    univ = [activo("XAUUSD")]
    r = fo.seleccionar(univ, AHORA, lectores({"XAUUSD": evaluacion(30, 20)}, {"XAUUSD": pf(99.5)},
                                             analizador=lambda t, m: {"price": 7.0, "marco": m}))
    assert r.elegido.h1["marco"] == "H1" and r.elegido.d1["marco"] == "D1"


def test_plan_foco_real_no_trae_estadistica_y_cuenta_las_velas():
    import numpy as np
    import pandas as pd
    from analista import estadistica as est

    rng = np.random.default_rng(7)
    c = list(100 + (rng.standard_normal(1200) + 0.05).cumsum())
    df = pd.DataFrame({"time": pd.date_range("2025-01-01", periods=len(c), freq="h"), "open": c,
                       "close": c, "high": [x + 0.5 for x in c], "low": [x - 0.5 for x in c]})
    ultimo = est.eventos(df, 2, alcista=True)[-1]
    corte = df.iloc[: ultimo + 2].reset_index(drop=True)  # la ruptura es la penúltima vela
    h1 = {"atr_14": 1.0, "r1": 999.0, "price": 150.0, "niveles_origen": {"r1": "swing"}}
    r = fo.plan_foco(corte, h1, {"digits": 2, "nombre": "X"}, "Alcista")
    assert "estadistica" not in r.plan and r.velas_desde_ruptura == 1


# ───────────────────────────────────────────────────────────── vigencia del reuso


def pieza_foco(gatillo=100.0, estado="Armado: x", sesgo="Alcista"):
    return {"datos": {"ticker": "XAUUSD", "nombre": "Oro",
                      "plan": plan(sesgo=sesgo, gatillo=gatillo, estado=estado)}}


def lectores_vigencia(pf_nuevo, h1=None, edad=1.0, contexto=None, conectar=()):
    return fo.LectoresFoco(
        conectar=lambda: list(conectar),
        contexto_macro=lambda ahora: contexto or ([], None, []),
        analizador=lambda t, m: h1 or {"price": 99.5, "ema_50": 98.0},
        edad_tick=lambda t: edad,
        serie=lambda t: None,
        armar_plan=lambda df, h, a, s: pf_nuevo,
        activo=lambda t: activo(t),
    )


def test_vigente_si_el_plan_sigue_igual():
    assert fo.sigue_vigente(pieza_foco(), AHORA, lectores_vigencia(pf(99.5)))


def test_no_vigente_si_cambio_el_gatillo_o_el_estado():
    assert not fo.sigue_vigente(pieza_foco(gatillo=101.0), AHORA, lectores_vigencia(pf(99.5)))
    assert not fo.sigue_vigente(pieza_foco(), AHORA,
                                lectores_vigencia(pf(100.2, velas=0, estado="Activado: x")))


def test_no_vigente_si_la_tendencia_dio_vuelta():
    h1 = {"price": 97.0, "ema_50": 98.0}
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores_vigencia(pf(99.5), h1=h1))


def test_no_vigente_con_mercado_cerrado_calendario_caido_o_blackout():
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores_vigencia(pf(99.5), edad=40.0))
    caido = ([], None, ["calendario no disponible (X): blackouts sin verificar"])
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores_vigencia(pf(99.5), contexto=caido))
    nfp = [{"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
            "hora_servidor": AHORA.strftime("%Y-%m-%d %H:%M")}]
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores_vigencia(pf(99.5), contexto=(nfp, None, [])))


def test_si_algo_revienta_no_se_reusa():
    def revienta(t, m):
        raise RuntimeError("MT5")

    lec = lectores_vigencia(pf(99.5))
    lec.analizador = revienta
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lec)


# ───────────────────────────────────────────────────────────── revisión final


def test_activado_con_el_precio_de_vuelta_tras_el_gatillo_no_entra():
    # Diría "Activado: cruzó sobre el gatillo" con el precio bajo él.
    assert "volvió" in fo.elegible(pf(99.8, velas=0, estado="Activado: x"))


def test_un_activo_que_revienta_no_tumba_la_seleccion():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    evals = {"XAUUSD": evaluacion(30, 20), "EURUSD": evaluacion(10, 10)}
    lec = lectores(evals, {"EURUSD": pf(99.5)})

    def armar(df, h1, a, sesgo):
        if a["ticker"] == "XAUUSD":
            raise TypeError("atr_14 None")
        return pf(99.5)

    lec.armar_plan = armar
    r = fo.seleccionar(univ, AHORA, lec)
    assert isinstance(r, fo.Seleccion) and r.elegido.activo["ticker"] == "EURUSD"


def test_si_todos_revientan_es_ilegible():
    lec = lectores({"XAUUSD": evaluacion(30, 20)}, {})
    lec.serie = lambda t: (_ for _ in ()).throw(RuntimeError("No se pudieron obtener datos"))
    assert isinstance(fo.seleccionar([activo("XAUUSD")], AHORA, lec), fo.MercadoIlegible)


def test_evaluados_cuenta_solo_los_que_compitieron():
    univ = [activo("XAUUSD"), activo("USDCLP"), activo("US100.spot", "indices")]
    antes_de_ny = datetime(2026, 10, 9, 8, 0, tzinfo=SCL)
    r = fo.seleccionar(univ, antes_de_ny, lectores({"XAUUSD": evaluacion(30, 20)}, {"XAUUSD": pf(99.5)},
                                                   edades={"USDCLP": 600.0}))
    assert r.evaluados == 1


def test_la_distancia_se_mide_con_el_precio_vivo():
    import numpy as np
    import pandas as pd

    c = list(100 + np.zeros(400))
    df = pd.DataFrame({"time": pd.date_range("2025-01-01", periods=400, freq="h"), "open": c,
                       "close": c, "high": [x + 0.5 for x in c], "low": [x - 0.5 for x in c]})
    h1 = {"atr_14": 1.0, "r1": 103.0, "price": 101.7, "niveles_origen": {"r1": "swing"}}
    assert fo.plan_foco(df, h1, {"digits": 2, "nombre": "X"}, "Alcista").precio == 101.7


def test_edad_tick_selecciona_los_simbolos(monkeypatch):
    # Un símbolo fuera del Market Watch devuelve None en symbol_info_tick hasta seleccionarlo.
    from types import SimpleNamespace

    visibles = set()
    falso = SimpleNamespace(
        symbol_select=lambda s, v=True: visibles.add(s) or True,
        symbol_info_tick=lambda s: SimpleNamespace(time=1000 if s == "BTCUSD" else 940) if s in visibles else None,
    )
    monkeypatch.setitem(sys.modules, "MetaTrader5", falso)
    assert fo._edad_tick("XAUUSD") == 1.0
