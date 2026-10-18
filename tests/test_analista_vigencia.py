"""La caducidad anticipada: un análisis con la invalidación rota no se reusa (spec 2026-10-16 §2)."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista import vigencia as vg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 14, 11, 0, tzinfo=SCL)
VELA = fx.lectura().vela


def _velas(altos_bajos):
    return pd.DataFrame([{"time": VELA + 14400 * (i + 1), "high": h, "low": l} for i, (h, l) in enumerate(altos_bajos)])


def test_sin_novedad_el_analisis_sigue_vigente():
    ref = fx.lectura(direccion="ALCISTA", precio=4000.0, invalidacion=3950.0, objetivo=4100.0)
    assert vg.motivo_caducidad(ref, fx.lectura(precio=4020.0), _velas([(4030, 3990)])) is None


def test_el_precio_que_toca_la_invalidacion_caduca_alcista():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert "invalidación" in vg.motivo_caducidad(ref, fx.lectura(precio=3990.0), _velas([(4030, 3949)]))


def test_el_objetivo_alcanzado_caduca():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert "objetivo" in vg.motivo_caducidad(ref, fx.lectura(precio=4090.0), _velas([(4101, 4000)]))


def test_bajista_es_el_espejo():
    ref = fx.lectura(direccion="BAJISTA", precio=4000.0, invalidacion=4050.0, objetivo=3900.0)
    def actual(precio):
        return fx.lectura(direccion="BAJISTA", precio=precio, invalidacion=4050.0, objetivo=3900.0)

    assert "invalidación" in vg.motivo_caducidad(ref, actual(4010.0), _velas([(4051, 3990)]))
    assert "objetivo" in vg.motivo_caducidad(ref, actual(3950.0), _velas([(4010, 3899)]))


def test_el_precio_actual_cuenta_aunque_no_haya_velas_nuevas():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert vg.motivo_caducidad(ref, fx.lectura(precio=3940.0), pd.DataFrame(columns=["time", "high", "low"]))


def test_un_cambio_de_estructura_caduca():
    ref = fx.lectura(invalidacion=3950.0)
    assert "estructura" in vg.motivo_caducidad(ref, fx.lectura(invalidacion=3900.0), _velas([(4010, 3990)]))


def _pieza():
    return {"datos": {"activos": [fx.activo_semanal()]}}


def _lectores(actual, velas, falla=False):
    def lectura(est, t, d, lector, ahora, referencia=None):
        if falla:
            raise OSError("MT5 cerrado")
        return actual, {"H4": velas}
    return pr.Lectores(estrategia=lambda: object(), lectura_actual=lectura)


def test_verificar_devuelve_el_motivo_para_caducar():
    ref_activo = fx.activo_semanal()["lectura"]
    from estrategia.contrato import lectura_de_dict

    ref = lectura_de_dict(ref_activo)  # bajista, invalidación 4227,32
    motivo, aviso = vg.verificar(_pieza(), AHORA, _lectores(fx.lectura(direccion="BAJISTA", precio=4230.0,
                                                                       invalidacion=4227.32), _velas([(4231, 4180)])))
    assert motivo and aviso is None


def test_con_el_terminal_caido_se_entrega_con_aviso_y_sin_rehacer():
    motivo, aviso = vg.verificar(_pieza(), AHORA, _lectores(None, None, falla=True))
    assert motivo is None and "no pude verificar si sigue vigente" in aviso.lower()
