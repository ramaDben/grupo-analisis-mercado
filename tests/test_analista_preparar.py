"""Preparación de las piezas del bot: datos del terminal en la carpeta del pedido."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
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
from analista import agenda as ag  # noqa: E402
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


# ───────────────────────────────────────────────────────────── el análisis de un activo

SEMANA = "2026-W42"
AHORA_LUNES = datetime(2026, 10, 12, 9, 30, tzinfo=SCL)


class EstrategiaFalsa:
    nombre = "tori"

    class marcos:
        operativo = "H4"
        etiquetas = {"H4": SimpleNamespace(nombre="swing", duracion="de una a dos semanas")}


GRAFICOS: list[dict] = []


def _grafico_falso(ticker, nombre, lectura, destino, **kw):
    GRAFICOS.append({"ticker": ticker, "destino": destino, **kw})
    destino.write_bytes(fx.PNG)
    return destino


def _dolar_falso(destino):
    destino.write_bytes(fx.PNG)
    return destino


CALENDARIOS: list[dict] = []


def _calendario_falso(payload, destino):
    CALENDARIOS.append(payload)
    destino.write_bytes(fx.PNG)
    return destino


EVENTO = {"fecha": "2026-10-14", "dia": "miércoles 14/10", "hora": "09:30 CLST", "evento": "IPC",
          "fuente_nombre": "CPI (MoM) (Sep)", "pais": "EE.UU.", "anterior": "0,4%", "esperado": "0,3%",
          "explicacion": "", "efecto": "Si sale sobre lo esperado, el oro tiende a bajar; si sale bajo lo esperado, lo contrario.",
          "mueve_al_activo": True}
HECHO = {"id": "dxy", "driver": "Dollar Index (DXY)", "fecha": "viernes 09/10", "en_curso": False, "nivel": "101,560",
         "cambio_1d": "0,193", "cambio_5d": "0,288", "unidad_cambio": "puntos", "sentido": "bajó",
         "sentido_1d": "bajó", "fuente": "MT5 (USDIDX)", "efecto": "juega a favor del alza del oro",
         "con_la_lectura": "va en contra de nuestra lectura"}


def _lectores(base, **kw):
    por_defecto = dict(
        base_referencias=base, estrategia=lambda: EstrategiaFalsa(),
        referencia=lambda est, t, d, semana, ahora, b: (fx.lectura(ticker=t), AHORA_LUNES, "semanal"),
        contrato=lambda t, p: {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
        grafico_lectura=_grafico_falso, grafico_dolar=_dolar_falso,
        catalogo=lambda t: {"ticker": t, "nombre": {"XAUUSD": "Oro", "COPPER": "Cobre"}[t],
                            "digits": {"XAUUSD": 2, "COPPER": 0}[t], "unidad": "USD"},
        drivers=lambda t: ["Dollar Index"], agenda=lambda ahora, t, n: ag.Agenda("lunes 12/10", "lunes 19/10", "vacia"),
        hechos=lambda t, n, direccion, curva, eventos, ahora: ([], []),
        rendir_calendario=_calendario_falso, curva=lambda: ({}, []),
        ancla=lambda t: fx.SELLO_ORO, cuenta=lambda: None, registro=base.parent / "registro_no_usado.json",
        # La referencia semanal se verifica contra el mercado de hoy: por defecto, sigue igual.
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (
            referencia or fx.lectura(ticker=t), {"H4": pd.DataFrame(columns=["time", "high", "low"])}))
    return pr.Lectores(**{**por_defecto, **kw})


def test_el_analisis_trae_un_solo_activo_con_su_vigencia(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    d = hecha.pieza["datos"]
    assert [a["ticker"] for a in d["activos"]] == ["XAUUSD"] and hecha.pieza["orden"]["args"] == {"ticker": "XAUUSD"}
    assert d["vigencia"] == {"desde": "lunes 12/10", "hasta": "lunes 19/10"}
    assert d["fundamental"] == {"fuera_catalogo": False, "sin_drivers": False, "referencia": "semanal"}
    assert set(hecha.pieza["editorial"]) == {"titular", "bajada", "titulares", "contexto", "fuentes"}


def test_preparar_sella_la_fuente_directa_del_activo(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref", ancla=lambda t: ("fx", fx.ANCLA_ORO)))
    sello = hecha.pieza["datos"]["fuente_directa"]
    assert sello["segmento"] == "fx" and sello["ancla"] == fx.ANCLA_ORO and sello["consultas"]


def test_un_activo_sin_ancla_no_se_prepara(tmp_path):
    with pytest.raises(pr.PreparacionFallida, match="No gasté tu cupo"):
        pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                    _lectores(tmp_path / "ref", ancla=lambda t: None))


def test_sin_referencia_semanal_se_lee_de_nuevo_y_se_anota_como_propia(tmp_path):
    lec = _lectores(tmp_path / "ref", referencia=lambda est, t, d, s, a, b: (fx.lectura(ticker=t), a, "propia"))
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert hecha.pieza["datos"]["fundamental"]["referencia"] == "propia"


def test_una_referencia_semanal_ya_caducable_se_reemplaza_por_una_lectura_propia(tmp_path):
    """La referencia del lunes con el objetivo ya alcanzado no puede ser la base de un análisis nuevo:
    el siguiente pedido lo caducaría y lo rehace sobre la misma referencia, en bucle."""
    vacias = pd.DataFrame(columns=["time", "high", "low"])
    propia = fx.lectura(precio=4120.0, invalidacion=4050.0, objetivo=4200.0)
    lec = _lectores(tmp_path / "ref",
                    lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4120.0),
                                                                                     {"H4": vacias}),
                    propia=lambda est, t, d, ahora: (propia, ahora))
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA, lec)
    d = hecha.pieza["datos"]
    assert d["fundamental"]["referencia"] == "propia"
    assert d["activos"][0]["lectura"]["precio"] == 4120.0
    assert any("objetivo" in a and "semanal" in a for a in hecha.avisos)


def test_una_referencia_semanal_vigente_se_usa_sin_aviso(tmp_path):
    def propia(*a):
        raise AssertionError("no tenía que leer de nuevo")
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA,
                        _lectores(tmp_path / "ref", propia=propia))
    assert hecha.pieza["datos"]["fundamental"]["referencia"] == "semanal"
    assert not any("semanal" in a for a in hecha.avisos)


def test_un_simbolo_fuera_del_catalogo_usa_el_nombre_del_terminal_y_lo_avisa(tmp_path):
    fuera = {"ticker": "TGT.US", "nombre": "Target Corp", "ticker_visible": "TGT.US", "digits": 2,
             "unidad": "", "notas_marco": {}, "fuera_catalogo": True}
    lec = _lectores(tmp_path / "ref", catalogo=lambda t: fuera, drivers=lambda t: [])
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "TGT.US"}), tmp_path / "p", AHORA_LUNES, lec)
    d = hecha.pieza["datos"]
    assert d["activos"][0]["nombre"] == "Target Corp"
    assert d["fundamental"]["fuera_catalogo"] is True and d["fundamental"]["sin_drivers"] is True
    assert any("fuera del catálogo" in a for a in hecha.avisos)


def test_el_analisis_no_escribe_en_las_referencias_semanales(tmp_path):
    base = tmp_path / "ref"
    pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert not base.exists()


def test_la_curva_va_sin_porcentajes(tmp_path):
    curva = {"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref", curva=lambda: (curva, [])))
    filas = hecha.pieza["datos"]["curva"]
    assert filas and "%" not in json.dumps(filas, ensure_ascii=False)


def _con_agenda(estado, eventos=()):
    return lambda ahora, t, n: ag.Agenda("lunes 12/10", "lunes 19/10", estado, [dict(e) for e in eventos],
                                         ["el calendario no respondió (X)"] if estado == "sin_calendario" else [])


def test_con_eventos_rinde_el_calendario_y_pide_dias_clave(tmp_path):
    CALENDARIOS.clear()
    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]))
    p = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec).pieza
    assert p["imagenes"]["calendario"] == "calendario_xauusd.png" and (tmp_path / "p" / "calendario_xauusd.png").exists()
    assert p["anidados"]["dias_clave"] == ["XAUUSD"] and p["editorial"]["dias_clave"] == {"XAUUSD": es.MARCA}
    assert "%" not in json.dumps(p["datos"]["agenda"], ensure_ascii=False)
    assert "%" not in json.dumps(CALENDARIOS[-1], ensure_ascii=False)
    assert p["datos"]["agenda"]["eventos"][0]["esperado"] == "0,3 por ciento"
    assert CALENDARIOS[-1]["eventos"][0]["dia"] == "MIÉRCOLES 14/10" and "agenda_semana" not in p["datos"]


def test_la_ventana_vacia_avisa_sus_fechas_y_no_pide_dias_clave(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    assert "dias_clave" not in hecha.pieza["anidados"] and "calendario" not in hecha.pieza["imagenes"]
    assert any("lunes 12/10" in a and "lunes 19/10" in a for a in hecha.avisos)


def test_sin_calendario_avisa_con_el_enlace(tmp_path):
    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("sin_calendario"))
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert any("investing.com/economic-calendar" in a for a in hecha.avisos)
    assert any("no respondió" in a for a in hecha.avisos)


def test_los_hechos_se_miden_con_la_direccion_y_la_agenda_y_quedan_sellados(tmp_path):
    llamadas = []

    def hechos(t, n, direccion, curva, eventos, ahora):
        llamadas.append((t, n, direccion, eventos))
        return [dict(HECHO)], ["sin dato de Tasa real"]

    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]), hechos=hechos)
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert hecha.pieza["datos"]["hechos"] == [HECHO]
    assert llamadas[0][:3] == ("XAUUSD", "Oro", "ALCISTA") and llamadas[0][3][0]["dia"] == "miércoles 14/10"
    assert any("Tasa real" in a for a in hecha.avisos)


def test_el_grafico_del_dolar_se_dibuja_solo_si_el_dolar_es_un_driver_medido(tmp_path):
    con = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "con", AHORA_LUNES,
                      _lectores(tmp_path / "ref", hechos=lambda *a: ([dict(HECHO)], [])))
    assert con.pieza["imagenes"]["dolar"] == "grafico_usdidx.png" and (tmp_path / "con" / "grafico_usdidx.png").exists()
    sin_dxy = dict(HECHO, id="tasa_real")
    sin = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "sin", AHORA_LUNES,
                      _lectores(tmp_path / "ref", hechos=lambda *a: ([sin_dxy], [])))
    assert "dolar" not in sin.pieza["imagenes"]


def test_si_el_grafico_del_dolar_falla_la_pieza_sale_sin_el_y_se_avisa(tmp_path):
    def roto(destino):
        raise RuntimeError("sin terminal")

    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref", hechos=lambda *a: ([dict(HECHO)], []), grafico_dolar=roto))
    assert "dolar" not in hecha.pieza["imagenes"] and any("gráfico del dólar" in a for a in hecha.avisos)


def test_sin_ningun_hecho_se_avisa(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    assert hecha.pieza["datos"]["hechos"] == [] and any("No medí ningún driver" in a for a in hecha.avisos)


def test_si_el_calendario_no_rinde_la_pieza_sale_con_la_tabla(tmp_path):
    def roto(payload, destino):
        raise RuntimeError("sin chromium")

    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]), rendir_calendario=roto)
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert "calendario" not in hecha.pieza["imagenes"] and hecha.pieza["datos"]["agenda"]["eventos"]
    assert any("imagen del calendario" in a for a in hecha.avisos)


# ───────────────────────────────────────────────────────────── seguimiento


def _foto(tmp_path, activos):
    """Un análisis vigente en el registro, como lo deja /oportunidad."""
    d = tmp_path / "foto"
    d.mkdir()
    a = activos[0]
    p = es.nueva_pieza("oportunidad", {"ticker": a["ticker"]}, {"ticker": a["ticker"], "activos": activos}, {},
                       extra_campos={"titulares": [a["ticker"]], "contexto": [a["ticker"]]})
    pr.guardar_pieza(p, d)
    rg.anotar(a["ticker"], d, AHORA_LUNES, "BAJISTA", {"nombre": "Camila Rojas", "id": "111"},
              tmp_path / "registro.json")


def _lectores_seg(tmp_path, velas, precio, hoy=None):
    def lector(ticker, marcos, extra=0):
        return {"H4": velas}, None
    lec = _lectores(tmp_path / "ref", registro=tmp_path / "registro.json", velas=lector)
    lec.lectura_actual = lambda est, t, d, lector, ahora, referencia=None: (hoy or fx.lectura(precio=precio),
                                                                           {"H4": velas})
    return lec


def test_seguimiento_lee_el_analisis_del_registro_que_se_le_pasa(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    lec = _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0)
    lec.registro = None  # sin registro en los lectores, manda el que pasa el bot
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES, lec,
                        registro=tmp_path / "registro.json")
    assert hecha.pieza["datos"]["ticker"] == "XAUUSD"


def test_seguimiento_sin_analisis_vigente_dice_que_pida_oportunidad(tmp_path):
    with pytest.raises(pr.SinAnalisisError, match=r"/oportunidad XAUUSD"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))


def test_seguimiento_de_otro_activo_no_usa_el_analisis_de_uno_vigente(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    with pytest.raises(pr.SinAnalisisError, match="USDCLP"):
        pr.preparar(Orden("seguimiento", {"ticker": "USDCLP"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))


def test_seguimiento_con_el_analisis_vencido_pide_uno_nuevo(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    with pytest.raises(pr.SinAnalisisError):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                    AHORA_LUNES + rg.VIGENCIA + timedelta(minutes=1), _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))


def test_seguimiento_informa_simulacion_y_lectura_por_separado(tmp_path):
    oro = fx.activo_semanal()
    _foto(tmp_path, [oro])
    foto_vela = oro["lectura"]["vela"]
    velas = pd.DataFrame([{"time": foto_vela, "open": 1, "high": 4300, "low": 3000, "close": 1},  # anterior: no cuenta
                          {"time": foto_vela + 14400, "open": 4180, "high": 4190, "low": 4150, "close": 4160}])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL), _lectores_seg(tmp_path, velas, 4124.0,
                                                           hoy=fx.lectura(precio=4124.0, invalidacion=4300.0)))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "en_curso"
    # La simulación (precios fijos del lunes) y la lectura de hoy, en párrafos separados.
    assert "CFD" in d["whatsapp"] and "La lectura de la semana cambió" in d["lectura_hoy"]
    assert not any(c.isdigit() for c in d["whatsapp"])  # el texto no lleva precios
    assert "$" not in d["whatsapp"] and "instrucción de inversión" not in d["whatsapp"]


def test_seguimiento_sin_simulacion_entrega_la_lectura_de_hoy(tmp_path):
    """Un activo de la foto sin simulación (solo sin volatilidad medida) es un estado válido."""
    from analista import oportunidad as op

    oro = fx.activo_semanal()
    oro["escenario"] = op.escenario(fx.lectura(atr=0.0), 2).a_dict()
    oro["contrato"] = None
    _foto(tmp_path, [oro])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                        _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "sin_simulacion"
    assert "plan definido" in d["whatsapp"]
    assert "ahora se vigila" in d["lectura_hoy"] or "sigue en pie" in d["lectura_hoy"]
    assert "No pude leer" not in d["whatsapp"]
    assert "Stop" not in d["whatsapp"] and "Las cifras de la simulación" not in d["whatsapp"]


def test_preparar_no_toca_los_directorios_de_produccion(tmp_path):
    """Ni el análisis ni el seguimiento escriben en data/carrusel/ (verificado por mtime)."""
    def huella():
        d = RAIZ / "data" / "carrusel"
        return sorted((str(f), f.stat().st_mtime_ns) for f in d.rglob("*")) if d.exists() else []

    antes = huella()
    pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, _lectores(tmp_path / "ref"))
    _foto(tmp_path, [fx.activo_semanal()])
    pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
    assert huella() == antes


def test_el_grafico_del_analisis_traza_los_niveles_de_la_lamina(tmp_path):
    GRAFICOS.clear()
    lectura = fx.lectura(direccion="BAJISTA", precio=4186.17, invalidacion=4227.32, objetivo=4149.96)
    lec = _lectores(tmp_path / "ref", referencia=lambda est, t, d, s, a, b: (lectura, a, "semanal"))
    pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    precios = [p for p, _ in GRAFICOS[-1]["niveles"]]
    assert 4227.32 in precios and 4149.96 in precios and GRAFICOS[-1]["digits"] == 2


def test_el_grafico_del_seguimiento_traza_la_simulacion_y_la_linea_de_hoy(tmp_path):
    GRAFICOS.clear()
    oro = fx.activo_semanal()
    _foto(tmp_path, [oro])
    pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
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


def _registro_con(tmp_path, direccion, motivo=None):
    ruta = tmp_path / "registro.json"
    d = tmp_path / "previo"
    d.mkdir()
    (d / "pieza.json").write_text("{}", encoding="utf-8")
    rg.anotar("XAUUSD", d, AHORA_LUNES - timedelta(days=9), direccion, {"nombre": "Camila", "id": "1"}, ruta)
    if motivo:
        rg.caducar("XAUUSD", motivo, AHORA_LUNES - timedelta(days=3), ruta)
    return ruta


def test_si_la_lectura_cambio_de_direccion_la_pieza_lleva_la_anterior(tmp_path):
    hoy = fx.lectura(ticker="XAUUSD").direccion
    previa = "ALCISTA" if hoy != "ALCISTA" else "BAJISTA"
    ruta = _registro_con(tmp_path, previa, "el precio tocó la invalidación")
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref", registro=ruta))
    ant = hecha.pieza["datos"]["anterior"]
    assert ant["direccion"] == previa and ant["motivo"] == "el precio tocó la invalidación"
    assert ant["fecha"] == pr.fecha_corta(AHORA_LUNES - timedelta(days=9))


def test_si_la_direccion_es_la_misma_o_no_hay_historia_no_hay_anterior(tmp_path):
    hoy = fx.lectura(ticker="XAUUSD").direccion
    ruta = _registro_con(tmp_path, hoy)
    igual = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p1", AHORA_LUNES,
                        _lectores(tmp_path / "ref", registro=ruta))
    assert "anterior" not in igual.pieza["datos"]
    sin = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p2", AHORA_LUNES,
                      _lectores(tmp_path / "ref2", registro=tmp_path / "vacio.json"))
    assert "anterior" not in sin.pieza["datos"]


def test_seguimiento_comunica_la_oportunidad_de_hoy_e_invalida_la_del_lunes(tmp_path):
    oro = fx.activo_semanal()  # la foto del lunes es BAJISTA
    _foto(tmp_path, [oro])
    hoy = fx.lectura(precio=4124.0, direccion="ALCISTA", invalidacion=4060.0)
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                        _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0, hoy=hoy))
    d = hecha.pieza["datos"]
    assert d["oportunidad_hoy"]["cambia_direccion"] and d["oportunidad_hoy"]["ratio"] == "1:3"
    assert "invalidada" in d["whatsapp"] and "oportunidad de hoy es una compra" in d["whatsapp"]


def test_seguimiento_con_entrada_real_fuera_del_stop_lo_dice(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    with pytest.raises(pr.SinAnalisisError, match="stop"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD", "entrada": 9999.0}), tmp_path / "s",
                    datetime(2026, 10, 14, 11, 0, tzinfo=SCL),
                    _lectores_seg(tmp_path, pd.DataFrame(columns=["time", "high", "low"]), 4124.0))
