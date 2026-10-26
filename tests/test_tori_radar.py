"""Radar de Tori: eventos sobre las diagonales de un marco (spec del radar §5)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori import radar  # noqa: E402
from estrategia.tori.lectura import _estructura  # noqa: E402
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
