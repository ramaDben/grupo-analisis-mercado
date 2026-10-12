"""Foco técnico del día: qué activo se elige, cuándo no hay, y cuándo no se puede saber.

Desde el enchufe de estrategia (S7) el foco elige con el puntaje de sesión de la estrategia
y arma el plan desde su lectura.
"""
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
from estrategia.contrato import Escenario, Lectura, Linea, Referencia, lectura_a_dict  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 9, 12, 0, tzinfo=SCL)


def activo(ticker, clase="forex_commodities"):
    return {"ticker": ticker, "nombre": ticker, "clase": clase, "digits": 2}


def lectura(ticker="XAUUSD", estado="TENDENCIA", direccion="ALCISTA", vigilar=101.0, seguridad=True):
    seg = Linea("seguridad", "diagonal", ((100, 97.0), (200, 98.0)), "H4", 3, "A+", 98.0)
    esc = (Escenario("⬆️", "c", "Si cierra sobre 101,00, la tendencia retoma."),
           Escenario("↔️", "c", "Entre las dos líneas."),
           Escenario("⬇️", "c", "Si cierra bajo 98,00, la tendencia deja de valer."))
    return Lectura(ticker=ticker, marco="H4", precio=100.0, direccion=direccion, estado=estado,
                   lineas=(seg,), en_prueba=None, vigilar=Referencia(vigilar, "línea bajista"),
                   invalidacion=Referencia(98.0, "línea alcista de seguridad", seg) if seguridad else None,
                   objetivo=None, escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


def sel(score=60.0, **kw):
    lec = lectura(**kw)
    return {"ticker": lec.ticker, "score": score, "lectura": lectura_a_dict(lec), "marco": "H4",
            "volatilidad_tipica": 1.0, "puntaje": {"desglose": {}, "excluido": None}, "gates_omitidos": []}


def lectores(selecciones, edades=None, conectar=(), contexto=None, gates=None, divergencia=None):
    def seleccion(a, ahora):
        s = selecciones[a["ticker"]]
        if isinstance(s, Exception):
            raise s
        return s

    return fo.LectoresFoco(
        conectar=lambda: list(conectar),
        contexto_macro=lambda ahora: contexto or ([], None, []),
        seleccion=seleccion,
        gate=lambda t, ev, ahora: (gates or {}).get(t),
        edad_tick=lambda t: (edades or {}).get(t, 1.0),
        activo=lambda t: activo(t),
        divergencia=divergencia or (lambda a, b: None),
    )


# ───────────────────────────────────────────────────────────── elegible


def test_una_ruptura_o_un_a_punto_entran():
    assert fo.elegible(sel(score=75.0), {"hay_plan": True}) is None
    assert fo.elegible(sel(score=50.0), {"hay_plan": True}) is None


def test_una_tendencia_sin_evento_no_entra():
    assert "ruptura" in fo.elegible(sel(score=30.0), {"hay_plan": True})


def test_sin_plan_no_entra():
    assert "línea de seguridad" in fo.elegible(sel(), {"hay_plan": False})


# ───────────────────────────────────────────────────────────── universo e índices


def test_universo_de_ventas_suma_us100_y_brent_y_respeta_lo_apagado():
    tickers = {a["ticker"] for a in fo.universo_ventas()}
    assert {"US100.spot", "BRENT.spot", "XAUUSD", "USDCLP"} <= tickers
    assert not tickers & {"US500.spot", "US30.spot", "BTCUSD", "QQQ.US"}


@pytest.mark.parametrize("dia", ["2026-01-15", "2026-04-15", "2026-10-09"])
def test_indice_solo_desde_la_apertura_de_nueva_york(dia):
    ny = ZoneInfo("America/New_York")
    a, m, d = (int(x) for x in dia.split("-"))
    antes = datetime(a, m, d, 9, 59, tzinfo=ny).astimezone(SCL)
    despues = datetime(a, m, d, 10, 0, tzinfo=ny).astimezone(SCL)
    us100 = activo("US100.spot", "indices")
    assert not fo.indice_habilitado(us100, antes)
    assert fo.indice_habilitado(us100, despues)
    assert fo.indice_habilitado(activo("XAUUSD"), antes)


# ───────────────────────────────────────────────────────────── seleccionar


def test_gana_el_mayor_puntaje_de_la_estrategia():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    r = fo.seleccionar(univ, AHORA, lectores({"XAUUSD": sel(60.0), "EURUSD": sel(80.0, ticker="EURUSD")}))
    assert isinstance(r, fo.Seleccion) and r.elegido.activo["ticker"] == "EURUSD"
    assert r.evaluados == 2 and r.elegido.plan["hay_plan"]
    assert r.elegido.seleccion["lectura"]["ticker"] == "EURUSD"  # trae la lectura que lo eligió


def test_empate_desempata_por_ticker():
    univ = [activo("GBPUSD"), activo("EURUSD")]
    r = fo.seleccionar(univ, AHORA, lectores({"GBPUSD": sel(60.0), "EURUSD": sel(60.0)}))
    assert r.elegido.activo["ticker"] == "EURUSD"


def test_mercado_cerrado_no_entra():
    r = fo.seleccionar([activo("XAUUSD")], AHORA, lectores({"XAUUSD": sel()}, edades={"XAUUSD": 40.0}))
    assert isinstance(r, fo.SinFoco) and "mercado cerrado" in r.texto()


def test_sin_elegibles_explica_los_motivos_agrupados():
    univ = [activo("XAUUSD"), activo("EURUSD"), activo("GBPUSD")]
    selecciones = {"XAUUSD": {"excluido": "va contra la secuencia de los marcos mayores"},
                   "EURUSD": sel(), "GBPUSD": sel(score=25.0)}
    r = fo.seleccionar(univ, AHORA, lectores(selecciones, gates={"EURUSD": "blackout por NFP"}))
    assert isinstance(r, fo.SinFoco)
    texto = r.texto()
    assert "3 activos" in texto and "marcos mayores" in texto and "dato económico" in texto
    assert "ruptura reciente" in texto


def test_un_rango_no_es_foco():
    r = fo.seleccionar([activo("XAUUSD")], AHORA,
                       lectores({"XAUUSD": sel(estado="RANGO", direccion="LATERAL")}))
    assert isinstance(r, fo.SinFoco) and "línea de seguridad" in r.texto()


def test_mt5_caido_es_ilegible_y_no_sin_foco():
    r = fo.seleccionar([activo("XAUUSD")], AHORA, lectores({}, conectar=["MT5 no conectó"]))
    assert isinstance(r, fo.MercadoIlegible)


def test_calendario_caido_es_ilegible():
    ctx = ([], None, ["calendario no disponible (TIMEOUT): no se pudieron verificar blackouts"])
    r = fo.seleccionar([activo("XAUUSD")], AHORA, lectores({"XAUUSD": sel()}, contexto=ctx))
    assert isinstance(r, fo.MercadoIlegible) and "calendario" in r.motivo


def test_el_aviso_de_calendario_caido_coincide_con_el_del_escaner(monkeypatch):
    import screener_gi as sc
    from market_data_mcp.tools import calendar

    monkeypatch.setattr(calendar, "cargar_calendario", lambda **kw: {"error": "TIMEOUT"})
    _, _, avisos = sc._contexto_macro(AHORA)
    assert fo.calendario_caido(avisos)


def test_un_activo_que_revienta_no_tumba_la_seleccion():
    univ = [activo("XAUUSD"), activo("EURUSD")]
    r = fo.seleccionar(univ, AHORA, lectores({"XAUUSD": RuntimeError("MT5"), "EURUSD": sel()}))
    assert isinstance(r, fo.Seleccion) and r.elegido.activo["ticker"] == "EURUSD"


def test_si_todos_revientan_es_ilegible():
    r = fo.seleccionar([activo("XAUUSD")], AHORA, lectores({"XAUUSD": RuntimeError("MT5")}))
    assert isinstance(r, fo.MercadoIlegible)


def test_evaluados_cuenta_solo_los_que_compitieron():
    univ = [activo("XAUUSD"), activo("USDCLP"), activo("US100.spot", "indices")]
    antes_de_ny = datetime(2026, 10, 9, 8, 0, tzinfo=SCL)
    r = fo.seleccionar(univ, antes_de_ny, lectores({"XAUUSD": sel()}, edades={"USDCLP": 600.0}))
    assert r.evaluados == 1


def test_edad_tick_selecciona_los_simbolos(monkeypatch):
    from types import SimpleNamespace

    visibles = set()
    falso = SimpleNamespace(
        symbol_select=lambda s, v=True: visibles.add(s) or True,
        symbol_info_tick=lambda s: SimpleNamespace(time=1000 if s == "BTCUSD" else 940) if s in visibles else None,
    )
    monkeypatch.setitem(sys.modules, "MetaTrader5", falso)
    assert fo._edad_tick("XAUUSD") == 1.0


# ───────────────────────────────────────────────────────────── vigencia del reuso


def pieza_foco():
    s = sel()
    return {"datos": {"ticker": "XAUUSD", "nombre": "Oro", "lectura": s["lectura"],
                      "plan": fo.plan_de(s, activo("XAUUSD"))}}


def test_vigente_si_la_lectura_sigue_igual():
    assert fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel()}))


def test_no_vigente_si_la_estrategia_dice_que_divergio():
    lec = lectores({"XAUUSD": sel()}, divergencia=lambda a, b: "la dirección cambió")
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lec)


def test_no_vigente_si_cambio_el_gatillo_o_dejo_de_ser_foco():
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel(vigilar=102.0)}))
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel(score=25.0)}))


def test_no_vigente_con_mercado_cerrado_calendario_caido_o_blackout():
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel()}, edades={"XAUUSD": 40.0}))
    caido = ([], None, ["calendario no disponible (X): blackouts sin verificar"])
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel()}, contexto=caido))
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": sel()}, gates={"XAUUSD": "blackout"}))


def test_si_algo_revienta_no_se_reusa():
    assert not fo.sigue_vigente(pieza_foco(), AHORA, lectores({"XAUUSD": RuntimeError("MT5")}))


def test_el_plan_del_foco_sale_de_la_lectura_y_no_trae_estadistica():
    plan = fo.plan_de(sel(), activo("XAUUSD"))
    assert plan["hay_plan"] and "estadistica" not in plan and plan["niveles"]["gatillo"] == 101.0


def test_un_fijo_excluido_no_se_cuela_como_foco():
    """El foco respeta las exclusiones: la cobertura fija es del carrusel, no del prospecto."""
    r = fo.seleccionar([activo("XAUUSD")], AHORA,
                       lectores({"XAUUSD": {"excluido": "sin líneas trazables"}}))
    assert isinstance(r, fo.SinFoco) and "estructura" in r.texto()

