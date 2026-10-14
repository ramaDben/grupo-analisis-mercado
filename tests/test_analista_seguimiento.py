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
    assert "descart" in texto and "—" not in texto and "–" not in texto


def test_el_precio_vivo_que_cruza_la_entrada_la_activa():
    ev = sg.evaluar(RANGO, [v(14550, 14500, cierre=14540)], 14580.0)
    assert ev["estado"] == "en_curso"


def test_el_mensaje_no_habla_en_pesos_ni_de_lo_que_se_habria_ganado():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    texto = sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", ALZA, ev, 4075.0, fx.lectura(), False, 2)
    assert "$" not in texto and "CLP" not in texto and "ganarías" not in texto and "hubieras" not in texto
    assert "—" not in texto and "–" not in texto
    assert texto.startswith("[[SALUDO]] ") and "oro" in texto
    assert not any(c.isdigit() for c in texto)  # sin precios (director, 2026-10-13)


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
    "avance_mucho": (ALZA, [v(4120, 3995)], 4120.0),
    "objetivo": (ALZA, [v(4040, 3990), v(4151, 4100)], 4120.0),
    "stop": (ALZA, [v(4040, 3990), v(4000, 3949)], 3960.0),
    "rango_roto": (RANGO, [v(14557, 14537), v(14668, 14544), v(14666, 14595)], 14593.0),
}
PROHIBIDAS = ("hubieras", "ganarías", "recomend", "oportunidad", "cartera", "garantiz", "seguro", "rentabil")


def _mensaje(esc, velas, precio, estado=None, fecha="miércoles 14-10"):
    ev = ({"estado": "sin_simulacion", "avance_pct": None, "motivo": "no hay línea trazable"}
          if estado == "sin_simulacion" else sg.evaluar(esc, velas, precio))
    return sg.mensaje("Oro", fecha, "lunes 12-10", esc, ev, precio, fx.lectura(), False, 2)


def _todas_las_redacciones():
    """Cada plantilla de cada estado, ya armada: el contenido que puede llegar a un cliente."""
    for estado, opciones in sg.PLANTILLAS.items():
        for i, plantilla in enumerate(opciones):
            for el, del_, accion in (("el oro", "del oro", "venta"), ("Bitcoin", "de Bitcoin", "compra")):
                yield estado, i, plantilla.format(el=el, accion=accion, dia="lunes", **{"del": del_})


def test_el_mensaje_es_un_parrafo_corto_que_cierra_con_una_pregunta():
    casos = [_mensaje(*c) for c in ESTADOS_EJEMPLO.values()] + [_mensaje(ALZA, [], 4000.0, "sin_simulacion")]
    for t in casos:
        assert t.startswith("[[SALUDO]] ") and "\n" not in t, t
        assert 150 <= len(t) <= 420 and t.endswith("?"), t
        assert not any(c.isdigit() for c in t), t  # sin precios ni porcentajes (director, 2026-10-13)


def test_ninguna_redaccion_rompe_las_reglas_de_cliente_ni_suena_a_plantilla():
    for estado, i, t in _todas_las_redacciones():
        bajo = t.lower()
        donde = f"{estado}[{i}]"
        assert "$" not in t and "—" not in t and "–" not in t and "«" not in t and "»" not in t, donde
        assert not any(p in bajo for p in PROHIBIDAS), donde
        assert "1:3" not in t and "⏰" not in t and "sesgo" not in bajo and "instrucción de inversión" not in bajo, donde
        assert t.count("CFD") <= 1 and bajo.count("plan") <= 1, donde  # sin repetir las mismas palabras
        assert t.endswith("?") and "\n" not in t and not any(c.isdigit() for c in t), donde
        assert "cambiamos de lado" not in bajo and "nos damos vuelta" not in bajo, donde  # solo se «revisa»
        assert "de el " not in bajo, donde


def test_cada_estado_tiene_tres_redacciones_distintas_y_ninguna_se_repite_entre_estados():
    todas = [t for opciones in sg.PLANTILLAS.values() for t in opciones]
    assert all(len(o) == 3 for o in sg.PLANTILLAS.values()) and len(set(todas)) == len(todas)
    primeras = [t.split(". ")[0] for t in todas]
    assert len(set(primeras)) == len(primeras)  # ni siquiera la primera frase


def test_cada_estado_dice_lo_que_le_paso_al_plan_sin_dramatizar():
    assert "a favor de la compra" in _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"]) or \
        "viene a favor" in _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"]) or \
        "va a favor" in _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"])
    en_contra = _mensaje(*ESTADOS_EJEMPLO["en_curso_en_contra"]).lower()
    assert "contra" in en_contra and "stop" in en_contra
    assert "todavía" in _mensaje(*ESTADOS_EJEMPLO["entrada_pendiente"]) or "aún" in _mensaje(*ESTADOS_EJEMPLO["entrada_pendiente"])
    assert "objetivo" in _mensaje(*ESTADOS_EJEMPLO["objetivo"])
    assert "stop" in _mensaje(*ESTADOS_EJEMPLO["stop"]) and "otro lado" in _mensaje(*ESTADOS_EJEMPLO["stop"])
    assert "descart" in _mensaje(*ESTADOS_EJEMPLO["rango_roto"])
    assert "no tiene un plan definido" in _mensaje(ALZA, [], 4000.0, "sin_simulacion") or \
        "no quedó con un plan definido" in _mensaje(ALZA, [], 4000.0, "sin_simulacion")


def test_el_lado_sale_de_la_direccion_de_la_simulacion():
    assert all("compra" in _mensaje(*ESTADOS_EJEMPLO["en_curso_a_favor"], fecha=f"día {n}") for n in range(9))
    venta = sg.mensaje("Cobre", "miércoles 14/10", "lunes 12-10", dict(RANGO, entrada_pendiente=False),
                       {"estado": "en_curso", "avance_pct": 3}, 14500.0, fx.lectura(), False, 0)
    assert "venta" in venta and "compra" not in venta


def test_dice_de_que_lado_se_opera_con_cfd_y_el_otro_lado_solo_se_revisa():
    for t in (_mensaje(*ESTADOS_EJEMPLO[k]) for k in ("en_curso_a_favor", "en_curso_en_contra", "stop")):
        assert "CFD" in t and "otro lado" in t or "ambos" in t or "dos lados" in t or "al alza o a la baja" in t, t


def test_el_articulo_del_activo_se_conjuga_bien():
    assert sg._activo_con_articulo("Oro") == ("el oro", "del oro")
    assert sg._activo_con_articulo("Bitcoin") == ("Bitcoin", "de Bitcoin")
    assert sg._activo_con_articulo("USD/CLP") == ("el USD/CLP", "del USD/CLP")


def test_la_redaccion_varia_entre_dias_pero_es_estable_el_mismo_dia():
    esc, velas, precio = ESTADOS_EJEMPLO["en_curso_a_favor"]
    ev = sg.evaluar(esc, velas, precio)

    def dia(fecha):
        return sg.mensaje("Oro", fecha, "12/10", esc, ev, precio, fx.lectura(), False, 2)

    assert dia("martes 13/10") == dia("martes 13/10")
    assert len({dia(f"día {n}") for n in range(12)}) == 3


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
    assert sg.con_saludo(t, "Juan").startswith("Hola Juan, ") and "oro" in sg.con_saludo(t, "Juan")
    assert sg.MARCA_SALUDO not in sg.con_saludo(t)
    assert sg.con_saludo("Texto viejo sin marca", "Juan") == "Texto viejo sin marca"


def test_el_seguimiento_se_ata_al_mensaje_del_dia_de_la_foto():
    """El día de la foto sale de la pieza: una foto de miércoles dice «miércoles», no «lunes»."""
    esc, velas, precio = ESTADOS_EJEMPLO["en_curso_a_favor"]
    ev = sg.evaluar(esc, velas, precio)
    for dia in ("lunes", "miércoles"):
        textos = [sg._armar("Oro", f"día {n}", esc, ev, precio, "", 2, None, dia) for n in range(9)]
        assert all(f"del {dia}" in t or f"el {dia}" in t for t in textos), dia
