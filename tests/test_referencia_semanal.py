"""La referencia semanal: guardar, leer y cuándo reemplazarla (spec §4)."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import referencia_semanal as rs  # noqa: E402
from estrategia.contrato import SCL, Escenario, Lectura, Linea, Referencia  # noqa: E402


def _linea(rol="seguridad", puntos=((100, 10.0), (200, 11.0))):
    return Linea(rol=rol, tipo="diagonal", puntos=puntos, marco="H4", toques=3,
                 calidad="A+", valor_actual=11.5)


def _lectura(estado="TENDENCIA", lineas=None):
    lineas = lineas if lineas is not None else (_linea(), _linea("accion", ((150, 13.0), (250, 12.0))))
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker="XAUUSD", marco="H4", precio=12.0, direccion="ALCISTA", estado=estado,
                   lineas=lineas, en_prueba=None, vigilar=Referencia(11.5, "línea alcista de control"),
                   invalidacion=None, objetivo=None, escenarios=esc, salida="s", conceptos=(),
                   avisos=(), metricas={"atr": 1.0}, vela=250)


def test_la_semana_es_la_iso_de_la_fecha_de_santiago():
    # Domingo 2026-10-11 23:30 en Santiago es todavía la semana 41.
    assert rs.semana_de(datetime(2026, 10, 11, 23, 30, tzinfo=SCL)) == "2026-W41"
    assert rs.semana_de(datetime(2026, 10, 12, 0, 5, tzinfo=SCL)) == "2026-W42"


def test_el_slug_saca_sufijos_del_broker():
    assert rs.slug("WTI.spot") == "wti"
    assert rs.slug("#NVDA") == "nvda"
    assert rs.slug("USDCLP") == "usdclp"


def test_guardar_y_cargar_devuelven_la_misma_lectura(tmp_path):
    lec = _lectura()
    ruta = rs.guardar(lec, "2026-W42", "semanal", datetime(2026, 10, 12, 9, 0, tzinfo=SCL), base=tmp_path)
    assert ruta == tmp_path / "2026-W42" / "xauusd.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["motivo"] == "semanal" and datos["ticker"] == "XAUUSD"
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) == lec


def test_sin_archivo_no_hay_referencia(tmp_path):
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) is None
    assert rs.manifiesto("2026-W42", base=tmp_path) is None


def test_una_referencia_en_prueba_no_se_guarda(tmp_path):
    import pytest
    from estrategia.contrato import Prueba
    lec = _lectura()
    prueba = replace(lec, estado="PRUEBA",
                     en_prueba=Prueba(_linea(), 11.6, datetime(2026, 10, 12, 13, 0, tzinfo=SCL)))
    with pytest.raises(ValueError, match="PRUEBA"):
        rs.guardar(prueba, "2026-W42", "semanal", datetime.now(SCL), base=tmp_path)


def test_el_manifiesto_se_guarda_y_se_lee(tmp_path):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["XAUUSD"]}, base=tmp_path)
    assert rs.manifiesto("2026-W42", base=tmp_path)["elegidos"] == ["XAUUSD"]


def test_la_misma_estructura_no_se_reemplaza_aunque_cambie_el_valor_de_hoy():
    ref = _lectura()
    hoy = replace(ref, lineas=tuple(replace(x, valor_actual=99.0) for x in ref.lineas), precio=13.0)
    assert not rs.debe_reemplazar(ref, hoy)


def test_tendencia_y_rebote_no_reemplazan():
    ref = _lectura()
    assert not rs.debe_reemplazar(ref, replace(ref, estado="REBOTE"))


def test_roles_reasignados_por_una_ruptura_reemplazan():
    ref = _lectura()
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),
                                                   replace(ref.lineas[1], rol="seguridad")))
    assert rs.debe_reemplazar(ref, rota)


def test_anclas_nuevas_reemplazan():
    ref = _lectura()
    retrazada = replace(ref, lineas=(_linea(puntos=((120, 10.0), (220, 11.0))), ref.lineas[1]))
    assert rs.debe_reemplazar(ref, retrazada)


def test_pasar_a_ruptura_reemplaza_aunque_las_lineas_no_cambien():
    ref = _lectura(estado="RANGO", lineas=())
    assert rs.debe_reemplazar(ref, replace(ref, estado="RUPTURA"))


def test_una_referencia_en_ruptura_que_sigue_igual_no_se_reemplaza():
    ref = _lectura(estado="RUPTURA")
    assert not rs.debe_reemplazar(ref, replace(ref, precio=13.5))


class _Falsa:
    """Una estrategia mínima que registra con qué la llamaron."""

    def __init__(self, seguida, leida, falla_seguir=False):
        from estrategia.contrato import Etiqueta, Marcos
        self.marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                             {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})
        self.seguida, self.leida, self.falla_seguir = seguida, leida, falla_seguir
        self.llamadas: list[tuple] = []

    def seguir(self, referencia, velas, digits, en_curso=None):
        self.llamadas.append(("seguir", en_curso))
        if self.falla_seguir:
            raise ValueError("las anclas ya no caben en la ventana")
        return self.seguida

    def leer(self, ticker, velas, digits, en_curso=None):
        self.llamadas.append(("leer", en_curso))
        return self.leida


def _lector(pedidos):
    def lector(ticker, marcos, extra):
        pedidos.append(extra)
        return {"H4": "velas"}, "vela-en-curso"
    return lector


def test_sin_referencia_levanta(tmp_path):
    import pytest
    with pytest.raises(rs.SinReferencia):
        rs.lectura_del_dia(_Falsa(None, None), "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)


def test_la_diaria_sigue_la_referencia_con_velas_extra_y_la_vela_en_curso(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    hoy = replace(ref, precio=13.0)
    pedidos: list[int] = []
    est = _Falsa(hoy, None)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector(pedidos), base=tmp_path)
    assert d.lectura == hoy and d.reemplazo is None and d.avisos == ()
    assert pedidos == [rs.EXTRA] and est.llamadas == [("seguir", "vela-en-curso")]


def test_una_ruptura_trae_el_reemplazo_leido_sin_vela_en_curso(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),))
    nueva = replace(ref, estado="RUPTURA", vela=300)
    est = _Falsa(rota, nueva)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)
    assert d.lectura == rota and d.reemplazo == nueva
    assert ("leer", None) in est.llamadas
    assert "nueva referencia" in d.avisos[0]


def test_si_seguir_no_puede_evaluar_se_lee_de_nuevo_y_se_avisa(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    nueva = replace(ref, vela=400)
    est = _Falsa(None, nueva, falla_seguir=True)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)
    assert d.lectura == nueva and d.reemplazo == nueva
    assert est.llamadas[-2:] == [("leer", "vela-en-curso"), ("leer", None)]
    assert "anclas" in d.avisos[0]


def test_cambiar_el_objetivo_no_es_cambiar_la_estructura():
    ref = _lectura()
    obj = Linea(rol="objetivo", tipo="horizontal", puntos=((300, 14.0),), marco="D1", toques=2,
                calidad="", valor_actual=14.0)
    assert not rs.debe_reemplazar(ref, replace(ref, lineas=ref.lineas + (obj,)))


def test_la_diaria_dice_contra_que_referencia_se_leyo(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),))
    d = rs.lectura_del_dia(_Falsa(rota, replace(ref, vela=300)), "XAUUSD", 2, "2026-W42",
                           _lector([]), base=tmp_path)
    assert d.referencia == ref  # la del lunes, no el reemplazo


def test_lectura_actual_sigue_la_referencia_o_lee_de_nuevo(tmp_path):
    ref = _lectura()
    est = _Falsa(replace(ref, precio=13.0), replace(ref, precio=14.0))
    momento = datetime(2026, 10, 12, 9, tzinfo=SCL)
    sin_ref, _ = rs.lectura_actual(est, "XAUUSD", 2, _lector([]), momento, base=tmp_path)
    assert sin_ref.precio == 14.0  # sin referencia: leer()
    rs.guardar(ref, "2026-W42", "semanal", momento, base=tmp_path)
    con_ref, _ = rs.lectura_actual(est, "XAUUSD", 2, _lector([]), momento, base=tmp_path)
    assert con_ref.precio == 13.0  # con referencia: seguir()


def test_estado_semanal_dice_que_activo_espera_el_cierre_por_una_linea_a_mas_en_prueba(tmp_path):
    """Spec §4, "La vela abierta": la pieza semanal no sale con una línea A+ en PRUEBA."""
    from estrategia.contrato import Prueba

    momento = datetime(2026, 10, 12, 9, tzinfo=SCL)
    ref = _lectura()
    for t in ("XAUUSD", "USDCLP"):
        rs.guardar(replace(ref, ticker=t), "2026-W42", "semanal", momento, base=tmp_path)
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["XAUUSD", "USDCLP"]}, base=tmp_path)
    cierre = datetime(2026, 10, 12, 13, 0, tzinfo=SCL)

    class Est(_Falsa):
        def seguir(self, referencia, velas, digits, en_curso=None):
            if referencia.ticker == "XAUUSD":
                return replace(referencia, estado="PRUEBA", en_prueba=Prueba(_linea(), 11.6, cierre))
            return referencia

    filas = rs.estado_semanal(Est(None, None), "2026-W42", _lector([]), momento,
                              digits={"XAUUSD": 2, "USDCLP": 2}, base=tmp_path)
    por = {f["ticker"]: f for f in filas}
    assert por["XAUUSD"]["espera_hasta"] == cierre and por["USDCLP"]["espera_hasta"] is None
    assert por["USDCLP"]["referencia"].ticker == "USDCLP"


def test_sin_analisis_semanal_no_hay_estado(tmp_path):
    assert rs.estado_semanal(_Falsa(None, None), "2026-W42", _lector([]),
                             datetime(2026, 10, 12, 9, tzinfo=SCL), digits={}, base=tmp_path) == []
