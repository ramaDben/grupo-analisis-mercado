"""seguir(): la lectura de hoy contra la referencia del lunes (spec §4, "La referencia semanal")."""
from __future__ import annotations

import pandas as pd
import pytest

import test_tori_lectura as tl

from estrategia.tori.lectura import seguir as _seguir
from estrategia.tori.parametros import PARAMETROS as P

LUNES = tl.vs.desde_vertices(tl.ALCISTA, 12)


def seguir(ref, h4, en_curso=None):
    return _seguir("XAUUSD", ref, tl.velas(h4), 2, en_curso, tl.MARCOS, P)


def extender(h4, vertices, n=6):
    nuevas = tl.vs.desde_vertices(vertices, n, t0=int(h4["time"].iloc[-1]) + 4 * 3600)
    return pd.concat([h4, nuevas], ignore_index=True)


def _rol(lectura, rol):
    return next(x for x in lectura.lineas if x.rol == rol)


def test_con_las_mismas_velas_la_lectura_no_cambia():
    ref = tl.leer(LUNES)
    hoy = seguir(ref, LUNES)
    assert (hoy.estado, hoy.direccion) == (ref.estado, ref.direccion)
    assert [x.valor_actual for x in hoy.lineas] == [x.valor_actual for x in ref.lineas]


def test_las_anclas_no_se_mueven_y_la_diagonal_avanza_por_su_pendiente():
    ref = tl.leer(LUNES)
    h4 = extender(LUNES, [119, 124, 122])  # doce velas que siguen sobre la línea alcista
    hoy = seguir(ref, h4)
    assert _rol(hoy, "seguridad").puntos == _rol(ref, "seguridad").puntos
    assert abs(_rol(hoy, "seguridad").valor_actual - (_rol(ref, "seguridad").valor_actual + 0.25 * 12)) < 0.01
    assert hoy.estado == "TENDENCIA" and hoy.vela == int(h4["time"].iloc[-1])


def test_un_cierre_al_otro_lado_de_la_linea_del_lunes_es_ruptura():
    ref = tl.leer(LUNES)
    hoy = seguir(ref, extender(LUNES, [119, 100]))
    assert (hoy.estado, hoy.direccion) == ("RUPTURA", "BAJISTA")
    assert _rol(hoy, "accion").puntos == _rol(ref, "seguridad").puntos
    assert hoy.objetivo is None  # el objetivo del lunes era para la otra dirección
    assert any("nueva referencia" in a for a in hoy.avisos)


def test_la_vela_en_curso_contra_la_linea_del_lunes_es_prueba():
    ref = tl.leer(LUNES)
    h4 = extender(LUNES, [119, 124, 122])
    hoy = seguir(ref, h4, tl._vela(h4, 100.0))
    assert hoy.estado == "PRUEBA" and hoy.en_prueba.linea.rol == "seguridad"


def test_tocar_la_linea_del_lunes_y_cerrar_a_favor_es_rebote():
    ref = tl.leer(LUNES)
    # En la vela 83 la línea del lunes vale 120,55: la mecha baja a 120,65 y cierra en 120,85.
    hoy = seguir(ref, extender(LUNES, [119, 124, 120.85]))
    assert (hoy.estado, hoy.direccion) == ("REBOTE", "ALCISTA")
    assert _rol(hoy, "seguridad").puntos == _rol(ref, "seguridad").puntos


def test_una_referencia_que_ya_no_cabe_falla_con_mensaje():
    ref = tl.leer(LUNES)
    with pytest.raises(ValueError, match="ventana"):
        seguir(ref, LUNES.iloc[5:].reset_index(drop=True))


def test_una_referencia_en_prueba_no_se_sigue():
    ref = tl.leer(LUNES, tl._vela(LUNES, 90.0))
    with pytest.raises(ValueError, match="PRUEBA"):
        seguir(ref, LUNES)


def test_volver_a_cerrar_al_otro_lado_de_la_linea_rota_es_ruptura_falsa():
    # El lunes la bajista estaba rota al alza; hoy el precio vuelve a cerrar bajo ella.
    ref = tl.leer(tl.rota())
    assert ref.estado == "RUPTURA"
    h4 = extender(tl.rota(), [118, 100])
    hoy = seguir(ref, h4)
    nueva = tl.leer(h4)
    assert (hoy.estado, hoy.direccion, hoy.lineas) == (nueva.estado, nueva.direccion, nueva.lineas)
    assert any("fue falsa" in a and "nueva referencia" in a for a in hoy.avisos)


def test_una_ruptura_que_se_sostiene_conserva_sus_anclas():
    # El precio sigue sobre la bajista rota: la referencia no caduca y no se vuelve a trazar.
    ref = tl.leer(tl.rota())
    hoy = seguir(ref, extender(tl.rota(), [118, 125]))
    assert hoy.estado == "RUPTURA"
    assert sorted(x.puntos for x in hoy.lineas) == sorted(x.puntos for x in ref.lineas)


def test_la_bateria_solo_exime_las_anclas_de_la_ruptura_que_caduco():
    # verificar_seguir_anclas_fijas mide una RUPTURA vigente: solo salta la que volvió.
    import estrategia_conformidad as conf

    ref = tl.leer(tl.rota())
    sigue = tl.velas(extender(tl.rota(), [118, 125]))
    vuelve = tl.velas(extender(tl.rota(), [118, 100]))
    assert not conf.referencia_caducada(ref, sigue, tl.MARCOS.operativo)
    assert conf.referencia_caducada(ref, vuelve, tl.MARCOS.operativo)


def test_romper_la_linea_del_lunes_y_volver_a_cerrar_adentro_es_ruptura_falsa():
    # El precio cierra bajo la alcista del lunes (110) y vuelve a cerrar sobre ella (126):
    # la ruptura dejó de serlo (hueco 5) y la referencia caduca, igual que con la línea rota.
    ref = tl.leer(LUNES)
    h4 = extender(LUNES, [119, 110, 126], 4)
    hoy = seguir(ref, h4)
    nueva = tl.leer(h4)
    assert hoy.estado != "RUPTURA"
    assert (hoy.estado, hoy.direccion, hoy.lineas) == (nueva.estado, nueva.direccion, nueva.lineas)
    assert any("fue falsa" in a and "nueva referencia" in a for a in hoy.avisos)
