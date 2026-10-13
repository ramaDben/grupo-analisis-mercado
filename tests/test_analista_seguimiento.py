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


def test_el_rango_roto_descarta_la_simulacion():
    """El cobre de la W41: la vela que cruzó el borde llegó también al stop. Es una ruptura del
    rango, no el falso quiebre que se simula: la simulación queda descartada, nunca «tocó el
    stop» ni «pendiente» de un precio que ya no vale (director, 2026-10-12)."""
    velas = [v(14557, 14537), v(14668, 14544), v(14666, 14595), v(14622, 14587)]
    ev = sg.evaluar(RANGO, velas, 14593.0)
    assert ev == {"estado": "rango_roto", "avance_pct": None}
    texto = sg.texto_simulacion(RANGO, ev, 14593.0, 0)
    assert "stop" not in texto and "objetivo" not in texto and "pendiente" not in texto
    assert "rompió el rango" in texto and "descartada" in texto and "14593" in texto


def test_el_rango_roto_no_se_reactiva_si_el_precio_vuelve_al_borde():
    ev = sg.evaluar(RANGO, [v(14668, 14544), v(14600, 14550)], 14550.0)
    assert ev["estado"] == "rango_roto"


def test_el_precio_vivo_que_rompe_el_rango_lo_descarta():
    assert sg.evaluar(RANGO, [v(14550, 14500, cierre=14540)], 14615.0)["estado"] == "rango_roto"


def test_el_rango_roto_tiene_sello_y_mensaje():
    from analista.comercial import SELLOS

    ev = {"estado": "rango_roto", "avance_pct": None}
    assert SELLOS["rango_roto"] == "RANGO ROTO"
    texto = sg.mensaje("Cobre", "miércoles 14/10", "12/10", RANGO, ev, 14620.0, fx.lectura(), False, 0)
    assert "se descartó" in texto and "—" not in texto and "–" not in texto


def test_el_precio_vivo_que_cruza_la_entrada_la_activa():
    ev = sg.evaluar(RANGO, [v(14550, 14500, cierre=14540)], 14580.0)
    assert ev["estado"] == "en_curso"


def test_el_mensaje_no_habla_en_pesos_ni_de_lo_que_se_habria_ganado():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    texto = sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", ALZA, ev, 4075.0, fx.lectura(), False, 2)
    assert "$" not in texto and "CLP" not in texto and "ganarías" not in texto and "hubieras" not in texto
    assert "—" not in texto and "–" not in texto
    assert texto.startswith("[[SALUDO]] ") and "Oro" in texto.splitlines()[0]
    assert not any(c.isdigit() for c in texto.split("\n\n", 1)[1])  # sin precios (director, 2026-10-13)


def test_la_lectura_reemplazada_se_dice():
    texto = sg.texto_lectura(fx.lectura(), True, 2)
    assert "cambió" in texto


def test_la_lectura_en_prueba_da_la_hora_del_cierre():
    texto = sg.texto_lectura(fx.lectura(estado="PRUEBA"), False, 2)
    assert "13:00" in texto


# ───────────────────────────────────────────── el mensaje personal, estado por estado

PENDIENTE = dict(ALZA, entrada_pendiente=True, entrada=4000.0)
ESTADOS_EJEMPLO = {
    "entrada_pendiente": (PENDIENTE, [v(3990, 3960)], 3975.0),
    "en_curso_a_favor": (ALZA, [v(4040, 3990)], 4075.0),
    "en_curso_en_contra": (ALZA, [v(4010, 3970)], 3975.0),
    "objetivo": (ALZA, [v(4040, 3990), v(4151, 4100)], 4120.0),
    "stop": (ALZA, [v(4040, 3990), v(4000, 3949)], 3960.0),
    "rango_roto": (RANGO, [v(14557, 14537), v(14668, 14544), v(14666, 14595)], 14593.0),
}


def _mensaje(esc, velas, precio, estado=None):
    ev = ({"estado": "sin_simulacion", "avance_pct": None, "motivo": "no hay línea trazable"}
          if estado == "sin_simulacion" else sg.evaluar(esc, velas, precio))
    return sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", esc, ev, precio, fx.lectura(), False, 2)


def test_cada_estado_dice_el_suyo_en_el_plan():
    planes = {}
    for nombre, (esc, velas, precio) in ESTADOS_EJEMPLO.items():
        t = _mensaje(esc, velas, precio)
        assert t.startswith("[[SALUDO]] ") and "Oro" in t.splitlines()[0]
        planes[nombre] = t.split("\n\n")[1]
    planes["sin"] = _mensaje(ALZA, [], 4000.0, "sin_simulacion").split("\n\n")[1]
    assert len(set(planes.values())) == len(planes)


def test_el_mensaje_es_corto_y_cumple_las_reglas_en_todos_los_estados():
    casos = [_mensaje(*c) for c in ESTADOS_EJEMPLO.values()] + [_mensaje(ALZA, [], 4000.0, "sin_simulacion")]
    for t in casos:
        bajo = t.lower()
        assert "$" not in t and "clp" not in bajo and "—" not in t and "–" not in t
        for prohibido in ("hubieras", "ganarías", "recomend", "oportunidad", "cartera"):
            assert prohibido not in bajo
        assert "instrucción de inversión" not in bajo and "━" not in t and "*" not in t and "1:3" not in t
        assert "«" not in t and len(t.split("\n\n")) == 3 and len(t) < 330 and "lámina" in bajo
        assert not any(c.isdigit() for c in t.split("\n\n", 1)[1])  # sin precios


def test_dice_de_que_lado_se_opera_con_cfd_y_que_si_se_invalida_se_cambia_de_lado():
    alza = _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    assert "operar al alza con CFD" in alza and "nos cambiamos de lado y operamos a la baja" in alza
    baja = sg.mensaje("Cobre", "miércoles 14/10", "12/10", dict(RANGO, entrada_pendiente=False),
                      {"estado": "en_curso", "avance_pct": 3}, 14500.0, fx.lectura(), False, 0)
    assert "operar a la baja con CFD" in baja and "nos cambiamos de lado y operamos al alza" in baja


def test_cada_estado_cuenta_lo_que_paso_sin_dramatizar():
    assert "hoy va a favor" in _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    assert "va en contra, pero sigue vigente" in _mensaje(*ESTADOS_EJEMPLO["en_curso_en_contra"])
    assert "se activa cuando el precio confirme la entrada" in _mensaje(*ESTADOS_EJEMPLO["entrada_pendiente"])
    assert "llegó a su objetivo" in _mensaje(*ESTADOS_EJEMPLO["objetivo"])
    stop = _mensaje(*ESTADOS_EJEMPLO["stop"])
    assert "se invalidó, y ahí nos cambiamos de lado" in stop and "operar a la baja" in stop
    assert "se descartó antes de activarse" in _mensaje(*ESTADOS_EJEMPLO["rango_roto"])
    assert "no hay un plan definido" in _mensaje(ALZA, [], 4000.0, "sin_simulacion")


def test_la_apertura_y_el_cierre_varian_entre_dias_pero_son_estables_el_mismo_dia():
    esc, velas, precio = ESTADOS_EJEMPLO["en_curso_a_favor"]
    ev = sg.evaluar(esc, velas, precio)

    def dia(fecha):
        return sg.mensaje("Oro", fecha, "12/10", esc, ev, precio, fx.lectura(), False, 2)

    assert dia("martes 13/10") == dia("martes 13/10")
    dias = [f"día {n}" for n in range(12)]
    assert len({dia(d).splitlines()[0] for d in dias}) > 1
    assert len({dia(d).splitlines()[-1] for d in dias}) > 1


def test_saludo_de_usa_lo_que_escribio_el_ejecutivo():
    assert sg.saludo_de("") == "Hola,"
    assert sg.saludo_de("Juan") == "Hola Juan,"
    assert sg.saludo_de("Estimado Sr. Pérez") == "Estimado Sr. Pérez,"
    assert sg.saludo_de("Estimada Camila:") == "Estimada Camila:"
    # Un nombre escrito todo en minúscula se capitaliza.
    assert sg.saludo_de("hari") == "Hola Hari," and sg.saludo_de("juan pérez") == "Hola Juan Pérez,"
    assert sg.saludo_de("estimado sr. pérez") == "Estimado Sr. Pérez,"


def test_con_saludo_no_deja_la_marca_y_respeta_piezas_viejas_sin_ella():
    t = _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    assert sg.con_saludo(t, "Juan").startswith("Hola Juan, ") and "Oro" in sg.con_saludo(t, "Juan")
    assert sg.MARCA_SALUDO not in sg.con_saludo(t)
    assert sg.con_saludo("Texto viejo sin marca", "Juan") == "Texto viejo sin marca"


def test_el_seguimiento_se_ata_al_mensaje_del_dia_de_la_foto():
    """Sin dato macro lo hace la apertura; con dato macro, el plan. Nunca las dos (se repetiría)."""
    sin = _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    assert "te compartí el lunes" in sin.split("\n\n")[0] and "Con sesgo" not in sin.split("\n\n")[0]
    con = sg._armar("Oro", "mié", ALZA, {"estado": "en_curso", "avance_pct": 40}, 4075.0, "", 2,
                    {"apertura": "hoy hay un dato que puede mover el oro."}, "lunes", "bajista")
    assert "El lunes te compartí el análisis de Oro (sesgo bajista): el plan es operar" in con
    assert con.count("te compartí") == 1
    # La foto de otro día se nombra con su día, no con «lunes».
    assert "te compartí el miércoles" in sg._armar("Oro", "jue", ALZA, {"estado": "en_curso", "avance_pct": 40},
                                                     4075.0, "", 2, None, "miércoles")
