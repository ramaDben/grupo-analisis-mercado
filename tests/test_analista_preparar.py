"""Preparación de las piezas del bot: datos del terminal en la carpeta del pedido."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import registro_semanal as rg  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista.orden import Orden  # noqa: E402
import referencia_semanal as rs  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)


def test_no_usa_los_preparar_de_produccion():
    fuente = (RAIZ / "scripts" / "analista" / "preparar.py").read_text(encoding="utf-8")
    for prohibido in ("pc.preparar(", "pa.preparar(", "pi.preparar(", "escanear(", "registrar_uso",
                      "escribir_suplementos", "_preparar_resultado", "DIR_TRABAJO"):
        assert prohibido not in fuente, prohibido


# ───────────────────────────────────────────────────────────── la foto semanal

SEMANA = "2026-W42"
AHORA_LUNES = datetime(2026, 10, 12, 9, 30, tzinfo=SCL)


class EstrategiaFalsa:
    nombre = "tori"

    class marcos:
        operativo = "H4"
        etiquetas = {"H4": SimpleNamespace(nombre="swing", duracion="de una a dos semanas")}


def _sembrar(base, lecturas, puntajes):
    for lec in lecturas:
        rs.guardar(lec, SEMANA, "semanal", AHORA_LUNES, base=base)
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": [l.ticker for l in lecturas],
                                   "puntajes": puntajes, "excluidos": []}, base=base)


GRAFICOS: list[dict] = []


def _grafico_falso(ticker, nombre, lectura, destino, **kw):
    GRAFICOS.append({"ticker": ticker, "destino": destino, **kw})
    destino.write_bytes(fx.PNG)
    return destino


def _lectores(base, filas_estado=None, **kw):
    def estado(_est, semana, _lector, _ahora, _digits, base=base):
        if filas_estado is not None:
            return filas_estado
        return [{"ticker": t, "espera_hasta": None} for t in rs.manifiesto(semana, base)["elegidos"]]
    por_defecto = dict(
        base_referencias=base, estado_semanal=estado, estrategia=lambda: EstrategiaFalsa(),
        contrato=lambda t, p: {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
        grafico_lectura=_grafico_falso,
        catalogo=lambda t: {"ticker": t, "nombre": {"XAUUSD": "Oro", "COPPER": "Cobre"}[t],
                            "digits": {"XAUUSD": 2, "COPPER": 0}[t], "unidad": "USD"},
        drivers=lambda t: ["Dollar Index"], agenda=lambda a: ([], []), curva=lambda: ({}, []),
        cuenta=lambda: None,
        # Nunca el registro real: con una foto de la semana en disco, el test la reusaría.
        registro=base.parent / "registro.json")
    return pr.Lectores(**{**por_defecto, **kw})


def test_sin_analisis_semanal_no_hay_pieza(tmp_path):
    with pytest.raises(pr.SinSemanaError, match="análisis semanal"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(tmp_path / "ref"))


def test_con_una_linea_a_mas_en_prueba_espera_el_cierre(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    filas = [{"ticker": "XAUUSD", "espera_hasta": datetime(2026, 10, 12, 13, 0, tzinfo=SCL)}]
    with pytest.raises(pr.EsperaVelaError, match="13:00"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base, filas))


def test_la_foto_trae_los_activos_en_orden_de_puntaje(tmp_path):
    base = tmp_path / "ref"
    cobre = fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                       rango=(14567.0, 14206.0), atr=85.86)
    _sembrar(base, [cobre, fx.lectura()], {"XAUUSD": 90.0, "COPPER": 5.0})
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    activos = hecha.pieza["datos"]["activos"]
    assert [a["ticker"] for a in activos] == ["XAUUSD", "COPPER"]
    oro = activos[0]
    assert oro["escenario"]["objetivo"] == 4150.0 and oro["fmt"]["objetivo"] == "4.150,00"
    assert oro["contrato"]["clp_unidad"] == 950.0
    assert oro["temporalidad"] == "4H · swing (de una a dos semanas)"
    assert (tmp_path / "p" / oro["grafico"]).exists()
    assert hecha.pieza["anidados"] == {"titulares": ["XAUUSD", "COPPER"], "contexto": ["XAUUSD", "COPPER"]}
    assert hecha.pieza["datos"]["curva"] == []


def test_una_foto_sin_activos_no_se_arma(tmp_path):
    """Sin ninguna referencia guardada, la foto quedaría vacía y congelada toda la semana."""
    base = tmp_path / "ref"
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": ["XAUUSD"], "puntajes": {"XAUUSD": 90.0},
                                   "excluidos": []}, base=base)
    with pytest.raises(pr.FotoVaciaError, match="ningún activo"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert not (tmp_path / "p" / "pieza.json").exists()


def test_un_elegido_sin_referencia_queda_fuera_y_se_anota(tmp_path):
    base = tmp_path / "ref"
    rs.guardar(fx.lectura(), SEMANA, "semanal", AHORA_LUNES, base=base)
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": ["XAUUSD", "COPPER"],
                                   "puntajes": {"XAUUSD": 90.0, "COPPER": 5.0}, "excluidos": []}, base=base)
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert [a["ticker"] for a in hecha.pieza["datos"]["activos"]] == ["XAUUSD"]
    assert hecha.pieza["datos"]["fuera"] == ["COPPER"]
    assert any("COPPER" in a and "pide /oportunidad de nuevo" in a for a in hecha.avisos)
    assert pr.fuera_con_referencia(hecha.pieza, base) == []


def test_rehacer_la_foto_suma_el_que_faltaba_y_conserva_los_precios_de_los_demas(tmp_path):
    """Los clientes ya recibieron los precios del oro: aunque su referencia cambie a mitad de
    semana, la foto rehecha los conserva y /seguimiento sigue midiendo contra ellos."""
    base, registro = tmp_path / "ref", tmp_path / "registro.json"
    rs.guardar(fx.lectura(), SEMANA, "semanal", AHORA_LUNES, base=base)
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": ["XAUUSD", "COPPER"],
                                   "puntajes": {"XAUUSD": 90.0, "COPPER": 5.0}, "excluidos": []}, base=base)
    primera = pr.preparar(Orden("oportunidad"), tmp_path / "p1", AHORA_LUNES, _lectores(base), registro=registro)
    rg.anotar_foto(SEMANA, tmp_path / "p1", AHORA_LUNES, ["XAUUSD"], registro)
    rs.guardar(fx.lectura(precio=4100.0), SEMANA, "ruptura", AHORA_LUNES, base=base)
    rs.guardar(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                          rango=(14567.0, 14206.0), atr=85.86), SEMANA, "semanal", AHORA_LUNES, base=base)
    assert pr.fuera_con_referencia(primera.pieza, base) == ["COPPER"]
    rehecha = pr.preparar(Orden("oportunidad"), tmp_path / "p2", AHORA_LUNES, _lectores(base), registro=registro)
    activos = {a["ticker"]: a for a in rehecha.pieza["datos"]["activos"]}
    assert set(activos) == {"XAUUSD", "COPPER"} and rehecha.pieza["datos"]["fuera"] == []
    assert activos["XAUUSD"] == pr.cargar_pieza(tmp_path / "p1")["datos"]["activos"][0]
    assert (tmp_path / "p2" / activos["XAUUSD"]["grafico"]).exists()


def test_la_curva_va_sin_porcentajes(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    curva = ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}, [])
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base, curva=lambda: curva))
    filas = hecha.pieza["datos"]["curva"]
    assert filas and "%" not in json.dumps(filas, ensure_ascii=False)


def test_la_foto_no_toca_los_directorios_de_produccion(tmp_path, monkeypatch):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    antes = {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()}
    pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()} == antes


# ───────────────────────────────────────────────────────────── seguimiento


def _foto(tmp_path, base, activos):
    """Una foto ya armada en el registro, como la deja /oportunidad."""
    d = tmp_path / "foto"
    d.mkdir()
    p = es.nueva_pieza("oportunidad", {"semana": SEMANA}, {"semana": SEMANA, "activos": activos}, {},
                       extra_campos={"titulares": [a["ticker"] for a in activos],
                                     "contexto": [a["ticker"] for a in activos]})
    pr.guardar_pieza(p, d)
    rg.anotar_foto(SEMANA, d, AHORA_LUNES, [a["ticker"] for a in activos], tmp_path / "registro.json")


def _lectores_seg(tmp_path, base, velas, precio):
    def lector(ticker, marcos, extra=0):
        return {"H4": velas}, None
    lec = _lectores(base, registro=tmp_path / "registro.json", velas=lector)
    lec.lectura_del_dia = lambda est, t, d, sem, lector, base=None: rs.Diaria(
        fx.lectura(precio=precio), None, (), {"H4": velas}, fx.lectura())
    return lec


def test_seguimiento_lee_la_foto_del_registro_que_se_le_pasa(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    _foto(tmp_path, base, [fx.activo_semanal()])
    lec = _lectores_seg(tmp_path, base, pd.DataFrame(columns=["time", "high", "low"]), 4124.0)
    lec.registro = None  # sin registro en los lectores, manda el que pasa el bot
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES, lec,
                        registro=tmp_path / "registro.json")
    assert hecha.pieza["datos"]["ticker"] == "XAUUSD"


def test_seguimiento_de_un_activo_fuera_de_la_foto_lista_los_que_si(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    _foto(tmp_path, base, [fx.activo_semanal()])
    with pytest.raises(pr.FueraDeLaFotoError, match="Oro"):
        pr.preparar(Orden("seguimiento", {"ticker": "USDCLP"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, base, pd.DataFrame(), 4000.0))


def test_seguimiento_sin_foto_de_la_semana(tmp_path):
    with pytest.raises(pr.SinFotoError, match="/oportunidad"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, tmp_path / "ref", pd.DataFrame(), 4000.0))


def test_seguimiento_informa_simulacion_y_lectura_por_separado(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    oro = fx.activo_semanal()
    _foto(tmp_path, base, [oro])
    foto_vela = oro["lectura"]["vela"]
    velas = pd.DataFrame([{"time": foto_vela, "open": 1, "high": 4300, "low": 3000, "close": 1},  # anterior: no cuenta
                          {"time": foto_vela + 14400, "open": 4180, "high": 4190, "low": 4150, "close": 4160}])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL), _lectores_seg(tmp_path, base, velas, 4124.0))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "en_curso"
    # La simulación (precios fijos del lunes) y la lectura de hoy, en párrafos separados.
    assert "El plan de Oro" in d["whatsapp"] and "La lectura de la semana cambió" in d["lectura_hoy"]
    assert not any(c.isdigit() for c in d["whatsapp"].split("\n\n", 1)[1])  # el texto no lleva precios
    assert "$" not in d["whatsapp"] and "instrucción de inversión" not in d["whatsapp"]


def test_seguimiento_sin_simulacion_entrega_la_lectura_de_hoy(tmp_path):
    """Un activo de la foto sin simulación (solo sin volatilidad medida) es un estado válido."""
    from analista import oportunidad as op

    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    oro = fx.activo_semanal()
    oro["escenario"] = op.escenario(fx.lectura(atr=0.0), 2).a_dict()
    oro["contrato"] = None
    _foto(tmp_path, base, [oro])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                        _lectores_seg(tmp_path, base, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "sin_simulacion"
    assert "no tiene un plan definido" in d["whatsapp"]
    assert "ahora se vigila" in d["lectura_hoy"] or "sigue en pie" in d["lectura_hoy"]
    assert "No pude leer" not in d["whatsapp"]
    assert "Stop" not in d["whatsapp"] and "Las cifras de la simulación" not in d["whatsapp"]


def test_el_grafico_semanal_traza_los_niveles_de_la_lamina(tmp_path):
    GRAFICOS.clear()
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura(direccion="BAJISTA", precio=4186.17, invalidacion=4227.32, objetivo=4149.96)],
             {"XAUUSD": 90.0})
    pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    precios = [p for p, _ in GRAFICOS[-1]["niveles"]]
    assert 4227.32 in precios and 4149.96 in precios and GRAFICOS[-1]["digits"] == 2


def test_el_grafico_del_seguimiento_traza_la_simulacion_y_la_linea_de_hoy(tmp_path):
    GRAFICOS.clear()
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    oro = fx.activo_semanal()
    _foto(tmp_path, base, [oro])
    pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                _lectores_seg(tmp_path, base, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
    precios = {p for p, _ in GRAFICOS[-1]["niveles"]}
    esc = oro["escenario"]
    assert {esc["entrada"], esc["stop"], esc["objetivo"], fx.lectura().vigilar.precio} <= precios


def test_el_grafico_real_pide_velas_suficientes_para_las_diagonales(tmp_path, monkeypatch):
    """Con 60 velas el ancla de la línea de seguridad del oro quedaba fuera y no se dibujaba."""
    pytest.importorskip("PIL")  # extra `stories`: el CI corre sin él
    import pipeline_carrusel as pc
    import tradingview_grafico as tg

    pedido = {}
    monkeypatch.setattr(tg, "generar_grafico_tv", lambda **kw: pedido.update(kw) or kw["destino"])
    pr._grafico_lectura("XAUUSD", "Oro", fx.lectura(), tmp_path / "g.png", digits=2, niveles=[(1.0, "X")])
    assert pedido["n_velas"] >= pc.VELAS_GRAFICO_TV and pedido["digits"] == 2
    assert pedido["niveles"] == [(1.0, "X")]


def test_la_fecha_corta_no_lleva_guion():
    """En la lámina, «11-10» con Plus Jakarta Sans se ve como un guion medio (prueba real, W41)."""
    assert pr.fecha_corta(datetime(2026, 10, 11, 12, 0, tzinfo=SCL)) == "domingo 11/10"
