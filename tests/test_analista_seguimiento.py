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
    assert "descartada" in texto and "—" not in texto and "–" not in texto


def test_el_precio_vivo_que_cruza_la_entrada_la_activa():
    ev = sg.evaluar(RANGO, [v(14550, 14500, cierre=14540)], 14580.0)
    assert ev["estado"] == "en_curso"


def test_el_mensaje_no_habla_en_pesos_ni_de_lo_que_se_habria_ganado():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    texto = sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", ALZA, ev, 4075.0, fx.lectura(), False, 2)
    assert "$" not in texto and "CLP" not in texto and "ganarías" not in texto and "hubieras" not in texto
    assert "—" not in texto and "–" not in texto
    assert texto.startswith("[[SALUDO]] ") and "simulación de Oro" in texto.splitlines()[0]
    assert "4.075,00" in texto and "50 %" in texto


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


def test_cada_estado_dice_el_suyo_en_la_primera_linea():
    titulares = {}
    for nombre, (esc, velas, precio) in ESTADOS_EJEMPLO.items():
        t = _mensaje(esc, velas, precio)
        assert t.startswith("[[SALUDO]] ") and "simulación de Oro: " in t.splitlines()[0]
        titulares[nombre] = t.splitlines()[0].split(": ", 1)[1]
    titulares["sin"] = _mensaje(ALZA, [], 4000.0, "sin_simulacion").splitlines()[0].split(": ", 1)[1]
    assert len(set(titulares.values())) == len(titulares)


def test_el_mensaje_cumple_las_reglas_en_todos_los_estados():
    casos = [_mensaje(*c) for c in ESTADOS_EJEMPLO.values()] + [_mensaje(ALZA, [], 4000.0, "sin_simulacion")]
    for t in casos:
        bajo = t.lower()
        assert "$" not in t and "clp" not in bajo and "—" not in t and "–" not in t
        for prohibido in ("hubieras", "ganarías", "recomend", "oportunidad", "cartera"):
            assert prohibido not in bajo
        # Sin aviso legal ni encabezados de boletín (gerencia, 2026-10-13): es una conversación.
        assert "instrucción de inversión" not in bajo and "━" not in t and "*" not in t
        assert "Lectura técnica hoy" not in t and "1:3" not in t
        assert "La lectura del lunes sigue en pie" in t and "lámina" in bajo


def test_dice_la_direccion_y_pesa_igual_el_stop_y_el_objetivo():
    alza = _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    assert "Es una compra, porque la tendencia es alcista." in alza
    baja = sg.mensaje("Cobre", "miércoles 14/10", "12/10", dict(RANGO, entrada_pendiente=False), {"estado": "en_curso", "avance_pct": 3},
                      14500.0, fx.lectura(), False, 0)
    assert "Es una venta, porque la tendencia es bajista." in baja
    # La misma frase trae stop y objetivo, cada uno con lo que significa.
    assert ("stop en 3.950,00 (si el precio llega ahí, se da por fallida) y objetivo en 4.150,00 "
            "(si llega ahí, se da por cumplida)") in alza


def test_solo_dice_que_hay_espacio_cuando_es_cierto():
    con = ("entrada_pendiente", "en_curso_a_favor")
    for nombre, (esc, velas, precio) in ESTADOS_EJEMPLO.items():
        t = _mensaje(esc, velas, precio)
        assert ("aún hay espacio para tomar posición" in t or "todavía queda espacio para tomar posición" in t)             == (nombre in con), nombre
    poco = _mensaje(ALZA, [v(4010, 3995)], 4005.0)
    assert "muy poco a favor" in poco and "casi todo el recorrido" in poco
    mucho = _mensaje(ALZA, [v(4120, 3995)], 4120.0)
    assert "queda poco espacio" in mucho


def test_el_stop_y_el_objetivo_se_dan_por_cerrados_sin_dramatizar():
    assert "se da por cerrada" in _mensaje(*ESTADOS_EJEMPLO["stop"]) and "limitar la pérdida" in _mensaje(*ESTADOS_EJEMPLO["stop"])
    assert "se da por cumplida" in _mensaje(*ESTADOS_EJEMPLO["objetivo"])


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
    assert sg.con_saludo(t, "Juan").startswith("Hola Juan, ") and "simulación de Oro" in sg.con_saludo(t, "Juan")
    assert sg.MARCA_SALUDO not in sg.con_saludo(t)
    assert sg.con_saludo("Texto viejo sin marca", "Juan") == "Texto viejo sin marca"
