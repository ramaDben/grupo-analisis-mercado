"""Radar de Tori: eventos sobre las diagonales de un marco (spec del radar §5)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori import crear, crear_intradia, radar  # noqa: E402
from estrategia.tori.horizontales import Horizontal  # noqa: E402
from estrategia.tori.lectura import AVISO_SALTO, _estructura  # noqa: E402
from estrategia.tori.lineas import trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402
from test_tori_lineas import ALCISTA, BAJISTA_ROTA  # noqa: E402

DIGITS = 3
# La alcista principal de ALCISTA vale 117,55 en la última vela (índice 83) con el tramo final
# de 12 velas que agregan estos casos.


def _alcista_con_final(fin: float) -> pd.DataFrame:
    return vs.desde_vertices([130, *ALCISTA[:-1], fin], 12)


def _bajista_rota_con_retroceso(fin: float):
    """La bajista de BAJISTA_ROTA se rompe al alza y el precio vuelve hacia ella."""
    df = vs.desde_vertices([100, *BAJISTA_ROTA], 12)
    sub = vs.desde_vertices([100, 118, fin], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    return serie_de(pd.concat([df, sub], ignore_index=True))


def _de(eventos, linea):
    return [e for e in eventos if e.linea == linea]


def test_toque_alcista_con_rebote_es_evento_de_seguridad():
    s = serie_de(_alcista_con_final(117.8))  # el mínimo final llega a la línea y cierra arriba
    estado, direccion, _, eventos = radar.diagonales(s, P, "H4", DIGITS)
    assert (estado, direccion) == ("TENDENCIA", "ALCISTA")
    [ev] = _de(eventos, "seguridad")
    assert (ev.marco, ev.tipo, ev.detalle, ev.velas) == ("H4", "toco", "rebote", None)
    assert ev.valor == round(117.55, DIGITS)
    assert abs(ev.distancia_atr - abs(s.closes[-1] - 117.55) / s.atr) < 1e-9
    assert ev.calidad in ("A+", "B")


def test_toque_que_cierra_al_otro_lado_es_rompio():
    df = _alcista_con_final(117.8)
    # El cierre queda bajo la línea pero dentro de la tolerancia: la línea sigue vigente.
    df.loc[83, ["low", "close"]] = [117.40, 117.45]
    s = serie_de(df)
    t = trazar(s, "alcista", P)
    assert t is not None and t.vigente and s.closes[-1] < t.valor(len(s) - 1)
    [ev] = _de(radar.diagonales(s, P, "H4", DIGITS)[3], "seguridad")
    assert (ev.tipo, ev.detalle) == ("toco", "rompió")


def test_la_vela_que_rompe_la_linea_es_toco_rompio_y_no_retesteo():
    df = _alcista_con_final(119)
    df.loc[83, ["low", "close"]] = [116.5, 116.7]  # cierra bajo la línea por más que la tolerancia
    s = serie_de(df)
    estado, _, _, eventos = radar.diagonales(s, P, "H4", DIGITS)
    assert estado == "RUPTURA"
    [ev] = _de(eventos, "accion")
    assert (ev.tipo, ev.detalle) == ("toco", "rompió")


def test_por_tocar_reporta_el_menor_numero_de_velas():
    s = serie_de(_alcista_con_final(119))  # cierre a ~1,6 ATR sobre la línea
    [ev] = _de(radar.diagonales(s, P, "H4", DIGITS)[3], "seguridad")
    assert (ev.tipo, ev.velas, ev.detalle) == ("por_tocar", 2, "")
    t = trazar(s, "alcista", P)
    assert abs(ev.distancia_atr - abs(s.closes[-1] - t.valor(len(s) + 1)) / s.atr) < 1e-9
    assert ev.valor == round(t.valor(len(s) - 1), DIGITS)


def test_a_mas_de_tres_velas_no_hay_evento():
    s = serie_de(_alcista_con_final(124))  # a ~12 ATR de la línea
    assert radar.diagonales(s, P, "H4", DIGITS)[3] == []
    # Con más velas de alcance la misma línea sí aparece: el tope es el parámetro.
    assert _de(radar.diagonales(s, replace(P, radar_velas_max=40), "H4", DIGITS)[3], "seguridad")


def test_una_linea_que_toco_no_repite_por_tocar():
    s = serie_de(_alcista_con_final(117.8))
    eventos = _de(radar.diagonales(s, P, "H4", DIGITS)[3], "seguridad")
    assert [e.tipo for e in eventos] == ["toco"]


def test_la_linea_rota_en_ruptura_se_marca_retesteo():
    s = _bajista_rota_con_retroceso(107)  # el mínimo final vuelve a la bajista rota
    estado, direccion, _, eventos = radar.diagonales(s, P, "H4", DIGITS)
    assert (estado, direccion) == ("RUPTURA", "ALCISTA")
    [ev] = _de(eventos, "accion")
    assert (ev.tipo, ev.detalle) == ("toco", "retesteo")


def test_el_retesteo_tambien_vale_para_por_tocar():
    s = _bajista_rota_con_retroceso(110)
    [ev] = _de(radar.diagonales(s, P, "H4", DIGITS)[3], "accion")
    assert (ev.tipo, ev.velas, ev.detalle) == ("por_tocar", 2, "retesteo")


def test_la_linea_de_rango_rebota_si_el_cierre_no_cambia_de_lado(monkeypatch):
    # La regla de lado no depende del sentido: se fuerza una estructura de RANGO con la alcista.
    def con_rango(s, alc, baj, p):
        return replace(_estructura(s, alc, baj, p), estado="RANGO", direccion="LATERAL",
                       accion=None, seguridad=None, rango=(alc,))

    monkeypatch.setattr(radar, "_estructura", con_rango)
    s = serie_de(_alcista_con_final(117.8))
    estado, _, lineas, eventos = radar.diagonales(s, P, "H4", DIGITS)
    assert estado == "RANGO" and [x.rol for x in lineas] == ["rango"]
    [ev] = eventos
    assert (ev.linea, ev.tipo, ev.detalle) == ("rango", "toco", "rebote")

    df = _alcista_con_final(117.8)
    df.loc[83, ["low", "close"]] = [117.40, 117.45]  # el cierre cruza la línea
    [ev] = radar.diagonales(serie_de(df), P, "H4", DIGITS)[3]
    assert (ev.linea, ev.tipo, ev.detalle) == ("rango", "toco", "rompió")


def test_los_roles_son_los_de_estructura():
    for s in (serie_de(_alcista_con_final(119)), _bajista_rota_con_retroceso(110)):
        e = _estructura(s, trazar(s, "alcista", P), trazar(s, "bajista", P), P)
        estado, direccion, lineas, _ = radar.diagonales(s, P, "H4", DIGITS)
        assert (estado, direccion) == (e.estado, e.direccion)
        esperadas = [(rol, t) for rol, t in (("seguridad", e.seguridad), ("accion", e.accion))
                     if t is not None] + [("rango", t) for t in e.rango]
        assert [x.rol for x in lineas] == [rol for rol, _ in esperadas]
        for x, (_, t) in zip(lineas, esperadas):
            assert x.valor_actual == round(t.valor(len(s) - 1), DIGITS)
            assert x.valor_abierta == round(t.valor(len(s)), DIGITS)


# --- zonas de soporte y resistencia (spec §5) ---------------------------------------------------

def _rango(fin: float = 105):
    """Rango 100-110 con soporte en 99,8 y resistencia en 110,2; la última vela se edita en cada caso."""
    return vs.desde_vertices([100, 110, 100, 110, 100, 110, 100, fin], 10)


def test_vela_que_entra_a_la_zona_de_soporte_es_toco():
    df = _rango()
    df.loc[df.index[-1], "low"] = 99.9  # dentro de 99,8 ± 0,18 ATR
    s = serie_de(df)
    lineas, eventos = radar.zonas(s, P, "H1", DIGITS)
    [ev] = _de(eventos, "soporte")
    assert (ev.marco, ev.tipo, ev.velas, ev.calidad, ev.detalle) == ("H1", "toco", None, "", "")
    assert ev.valor == round(99.8, DIGITS)
    assert abs(ev.distancia_atr - abs(s.closes[-1] - 99.8) / s.atr) < 1e-9
    assert [(x.rol, x.valor_actual, x.valor_abierta) for x in lineas] == [
        ("soporte", 99.8, 99.8), ("resistencia", 110.2, 110.2)]


def test_zona_cruzada_en_la_ultima_vela_cuenta_como_toco():
    df = _rango()
    # El cierre anterior estaba sobre el soporte y el último quedó bajo él.
    df.loc[df.index[-1], ["high", "low", "close"]] = [104.5, 98.0, 99.0]
    s = serie_de(df)
    assert s.closes[-2] > 99.8 > s.closes[-1]
    [ev] = _de(radar.zonas(s, P, "H1", DIGITS)[1], "soporte")
    assert (ev.tipo, ev.valor) == ("toco", round(99.8, DIGITS))


def test_solo_cuentan_el_soporte_y_la_resistencia_mas_cercanos(monkeypatch):
    s = serie_de(_rango())  # cierre anterior 104,5; la última vela va de 104,3 a 105,2
    bajo = [Horizontal(104.4, 2, 0), Horizontal(104.2, 2, 0), Horizontal(104.0, 2, 0)]
    monkeypatch.setattr(radar, "detectar", lambda *_: bajo)
    lineas, eventos = radar.zonas(s, P, "H1", DIGITS)
    # Las zonas de 104,4 y 104,2 intersectan la vela, pero solo el más cercano cuenta.
    [ev] = eventos
    assert (ev.linea, ev.tipo, ev.valor) == ("soporte", "toco", 104.4)
    assert [x.rol for x in lineas] == ["soporte"]


def test_por_tocar_mide_contra_el_borde_de_la_zona(monkeypatch):
    s = serie_de(_rango())
    nivel = s.closes[-1] - 1.18 * s.atr  # d = 1,18 − 0,18 = 1,0 ATR al borde de la zona
    monkeypatch.setattr(radar, "detectar", lambda *_: [Horizontal(nivel, 2, 0)])
    [ev] = radar.zonas(s, P, "H1", DIGITS)[1]
    assert (ev.linea, ev.tipo, ev.velas) == ("soporte", "por_tocar", 1)
    assert abs(ev.distancia_atr - 1.18) < 1e-9
    # Con el doble de distancia hacen falta dos velas.
    monkeypatch.setattr(radar, "detectar", lambda *_: [Horizontal(s.closes[-1] - 2.18 * s.atr, 2, 0)])
    [ev] = radar.zonas(s, P, "H1", DIGITS)[1]
    assert ev.velas == 2


def test_un_nivel_que_toco_no_repite_por_tocar_y_lejos_no_hay_evento():
    df = _rango()
    df.loc[df.index[-1], "low"] = 99.9
    eventos = radar.zonas(serie_de(df), P, "H1", DIGITS)[1]
    assert [e.tipo for e in _de(eventos, "soporte")] == ["toco"]
    assert _de(eventos, "resistencia") == []  # 110,2 queda a ~5 ATR


def test_zonas_sin_rango_lanza():
    df = _rango()
    df[["open", "high", "low", "close"]] = 100.0
    try:
        radar.zonas(serie_de(df), P, "H1", DIGITS)
    except ValueError:
        return
    raise AssertionError("debía lanzar ValueError con ATR 0")


# --- lectura de un marco desde las velas, y paridad con leer() (spec §6-§7) ----------------------

def _velas_h4(h4: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"H4": h4, "D1": vs.agregar(h4, 6), "W1": vs.agregar(h4, 30)}


def _velas_h1(h1: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"H1": h1, "H4": vs.agregar(h1, 4), "D1": vs.agregar(h1, 24), "W1": vs.agregar(h1, 120)}


def test_los_marcos_del_radar_son_los_intradia():
    assert radar.MARCOS_RADAR.velas == {"W1": 156, "D1": 250, "H4": 180, "H1": 600}
    assert radar.RADAR_MARCOS == ("H1", "H4", "D1")


def test_historia_corta_lanza_historia_insuficiente():
    h4 = vs.desde_vertices([130, *ALCISTA], 12)  # 84 velas, la ventana de 4H es de 180
    with pytest.raises(radar.HistoriaInsuficiente, match="H4: 84 velas de 180"):
        radar.leer_marco(_velas_h4(h4), "H4", DIGITS)
    assert issubclass(radar.HistoriaInsuficiente, ValueError)


def test_velas_sin_rango_lanzan_valueerror():
    h4 = vs.desde_vertices([100, 100], 200, mecha=0.0)
    with pytest.raises(ValueError, match="no tienen rango") as e:
        radar.leer_marco(_velas_h4(h4), "H4", DIGITS)
    assert not isinstance(e.value, radar.HistoriaInsuficiente)


def test_el_salto_de_datos_deja_aviso_y_no_falla():
    # 120 velas antes del salto y 84 después: la historia cruda alcanza (204 ≥ 180) aunque
    # la ventana que se lee quede en las 84 posteriores al salto.
    antes = vs.desde_vertices([60, 50, 56, 52], 40)
    despues = vs.desde_vertices([130, *ALCISTA], 12, t0=int(antes["time"].iloc[-1]) + 4 * 3600)
    h4 = pd.concat([antes, despues], ignore_index=True)
    lec = radar.leer_marco(_velas_h4(h4), "H4", DIGITS)
    assert AVISO_SALTO.format(marco="H4") in lec.avisos
    assert (lec.estado, lec.direccion) == ("TENDENCIA", "ALCISTA")
    assert lec.vela == int(h4["time"].iloc[-1])


def _paridad(lectura, lm, marco):
    assert lm.marco == marco and lm.direccion == lectura.direccion
    propias = {x.rol: x.valor_actual for x in lectura.lineas
               if x.marco == marco and x.rol in ("seguridad", "accion")}
    radar_ = {x.rol: x.valor_actual for x in lm.lineas if x.rol in ("seguridad", "accion")}
    assert propias and radar_ == propias
    # Solo las líneas propias del marco: las de contexto de leer() no se agregan.
    assert {x.rol for x in lm.lineas} <= {"seguridad", "accion", "rango", "soporte", "resistencia"}
    assert lm.vela == lectura.vela and lm.atr == lectura.metricas["atr"]


def test_paridad_con_leer_en_4h():
    for vertices in ([130, *ALCISTA], [100, *BAJISTA_ROTA, 118]):
        velas = _velas_h4(vs.desde_vertices(vertices, 30))
        assert len(velas["H4"]) >= 180
        lectura = crear().leer("XAUUSD", velas, DIGITS)
        _paridad(lectura, radar.leer_marco(velas, "H4", DIGITS), "H4")


def test_paridad_con_leer_en_1h():
    velas = _velas_h1(vs.desde_vertices([130, *ALCISTA], 90, paso=3600))
    assert len(velas["H1"]) >= 600
    lectura = crear_intradia().leer("XAUUSD", velas, DIGITS)
    _paridad(lectura, radar.leer_marco(velas, "H1", DIGITS), "H1")
