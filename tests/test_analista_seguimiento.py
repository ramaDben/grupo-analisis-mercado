"""El seguimiento de la simulación semanal contra la foto del lunes."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import seguimiento as sg  # noqa: E402

ALZA = {"direccion": "ALCISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0, "entrada_pendiente": False}
RANGO = {"direccion": "BAJISTA", "entrada": 14567.0, "stop": 14610.0, "objetivo": 14438.0, "entrada_pendiente": True}


def v(alto, bajo, cierre=None):
    return {"high": alto, "low": bajo, "close": cierre if cierre is not None else (alto + bajo) / 2}


def test_en_curso_con_el_avance_hacia_el_objetivo():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    assert ev == {"estado": "en_curso", "avance_pct": 50}


def test_en_curso_en_contra_da_avance_negativo():
    assert sg.evaluar(ALZA, [v(4010, 3970)], 3975.0)["avance_pct"] == -17


def test_objetivo_alcanzado():
    assert sg.evaluar(ALZA, [v(4040, 3990), v(4151, 4100)], 4120.0)["estado"] == "objetivo"


def test_stop_tocado():
    assert sg.evaluar(ALZA, [v(4010, 3949)], 3990.0)["estado"] == "stop"


def test_una_vela_que_toca_las_dos_puntas_cuenta_stop():
    assert sg.evaluar(ALZA, [v(4160, 3940)], 4100.0)["estado"] == "stop"


def test_el_precio_vivo_cuenta_aunque_la_vela_no_haya_cerrado():
    assert sg.evaluar(ALZA, [], 3949.0)["estado"] == "stop"
    assert sg.evaluar(ALZA, [], 4150.0)["estado"] == "objetivo"


def test_rango_sin_llegar_al_borde_es_entrada_pendiente():
    assert sg.evaluar(RANGO, [v(14550, 14480)], 14520.0) == {"estado": "entrada_pendiente", "avance_pct": None}


def test_rango_que_toca_el_borde_queda_en_curso():
    ev = sg.evaluar(RANGO, [v(14570, 14500)], 14524.0)
    assert ev["estado"] == "en_curso" and ev["avance_pct"] == 33


def test_la_vela_que_activa_la_entrada_no_cuenta_el_objetivo():
    """Dentro de la vela no se sabe qué tocó primero: se cuenta lo prudente (M2 de la revisión)."""
    pendiente_alza = {**ALZA, "entrada_pendiente": True}
    ev = sg.evaluar(pendiente_alza, [v(4160, 3990)], 4100.0)
    assert ev["estado"] == "en_curso"


def test_con_entrada_pendiente_no_hay_stop_ni_objetivo():
    """El cobre de la W41: la vela que cruzó el borde llegó también al stop. Es una ruptura del
    rango, no el falso quiebre que se simula: la entrada sigue pendiente, nunca «tocó el stop»."""
    velas = [v(14557, 14537), v(14668, 14544), v(14666, 14595), v(14622, 14587)]
    ev = sg.evaluar(RANGO, velas, 14593.0)
    assert ev["estado"] == "entrada_pendiente"
    texto = sg.texto_simulacion(RANGO, ev, 14593.0, 0)
    assert "stop" not in texto and "objetivo" not in texto
    assert "14593" in texto and "14567" in texto and "todavía no llega" not in texto


def test_la_entrada_pendiente_se_activa_cuando_el_precio_vuelve_al_borde():
    ev = sg.evaluar(RANGO, [v(14668, 14544), v(14600, 14550)], 14550.0)
    assert ev["estado"] == "en_curso"


def test_el_precio_vivo_que_cruza_la_entrada_la_activa():
    ev = sg.evaluar(RANGO, [v(14550, 14500, cierre=14540)], 14580.0)
    assert ev["estado"] == "en_curso"


def test_el_mensaje_no_habla_en_pesos_ni_de_lo_que_se_habria_ganado():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    texto = sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", ALZA, ev, 4075.0, fx.lectura(), False, 2)
    assert "$" not in texto and "CLP" not in texto and "ganarías" not in texto and "hubieras" not in texto
    assert "—" not in texto and "–" not in texto
    assert "te envío una actualización" in texto.lower()
    assert "4.075,00" in texto and "50 %" in texto


def test_la_lectura_reemplazada_se_dice():
    texto = sg.texto_lectura(fx.lectura(), True, 2)
    assert "cambió" in texto


def test_la_lectura_en_prueba_da_la_hora_del_cierre():
    texto = sg.texto_lectura(fx.lectura(estado="PRUEBA"), False, 2)
    assert "13:00" in texto
