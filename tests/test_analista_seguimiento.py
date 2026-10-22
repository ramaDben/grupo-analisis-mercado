"""El seguimiento de la simulación semanal contra la foto del lunes."""
from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import seguimiento as sg  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
import estrategia_conformidad as conf  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista.orden import Orden  # noqa: E402
from analista import suceso  # noqa: E402
from analista.suceso import Resumen  # noqa: E402
from analista import registro_semanal as rg  # noqa: E402
from analista import esquema as es  # noqa: E402
from estrategia import tori  # noqa: E402
from estrategia.contrato import VelaEnCurso  # noqa: E402
conf.PASO.update({"M5": 300, "M15": 900})

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


def test_vela_viva_cobre_activa_en_el_tramo_vivo_sin_contar_objetivo():
    """Caso real COPPER W42: la vela H4 en formación toca la entrada sin llegar al stop.

    (a) activa en el tramo vivo y el objetivo NO cuenta en la vela que activa -> en_curso.
    """
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14643.0, 14580.0, cierre=14600.0)]
    ev = sg.evaluar(cobre, velas, 14525.0, vela_viva={"high": 14678.0, "low": 14482.0})
    assert ev["estado"] == "en_curso"


def test_vela_viva_cobre_que_toca_stop_es_rango_roto():
    """(b) misma vela_viva pero high 14715 (supera el stop) -> rango_roto."""
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14643.0, 14580.0, cierre=14600.0)]
    ev = sg.evaluar(cobre, velas, 14525.0, vela_viva={"high": 14715.0, "low": 14482.0})
    assert ev["estado"] == "rango_roto"


def test_sin_vela_viva_cobre_mantiene_entrada_pendiente():
    """(c) sin vela_viva -> entrada_pendiente como antes."""
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14643.0, 14580.0, cierre=14600.0)]
    ev = sg.evaluar(cobre, velas, 14525.0)
    assert ev["estado"] == "entrada_pendiente"


def test_tolerancia_activa_venta_cobre_con_toque_incompleto():
    """(a) venta entrada 14668/stop 14709/obj 14545, una vela cerrada high 14643 low 14600,
    precio_vivo 14610, tolerancia 28.4 -> estado 'en_curso'."""
    assert sg.TOLERANCIA_ATR == 0.35
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14643.0, 14600.0)]
    ev = sg.evaluar(cobre, velas, 14610.0, tolerancia=28.4)
    assert ev["estado"] == "en_curso"


def test_tolerancia_cero_mantiene_venta_cobre_pendiente():
    """(b) mismo caso tolerancia 0.0 -> 'entrada_pendiente'."""
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14643.0, 14600.0)]
    ev = sg.evaluar(cobre, velas, 14610.0, tolerancia=0.0)
    assert ev["estado"] == "entrada_pendiente"


def test_tolerancia_con_vela_que_toca_stop_descarta_rango():
    """(c) vela con high 14643 pero tambien high >= 14709 (toca stop), tolerancia 28.4 -> 'rango_roto'."""
    cobre = {"direccion": "BAJISTA", "entrada": 14668.0, "stop": 14709.0, "objetivo": 14545.0,
             "entrada_pendiente": True}
    velas = [v(14710.0, 14600.0)]
    ev = sg.evaluar(cobre, velas, 14610.0, tolerancia=28.4)
    assert ev["estado"] == "rango_roto"


def test_tolerancia_alcista_simetrico_activa_con_low_por_encima():
    """(d) alcista simetrico con entrada cuyo low queda 25 pts por encima, tolerancia 28.4 -> activa."""
    alcista = {"direccion": "ALCISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0,
               "entrada_pendiente": True}
    velas = [v(4060.0, 4025.0)]
    ev = sg.evaluar(alcista, velas, 4030.0, tolerancia=28.4)
    assert ev["estado"] == "en_curso"
    assert sg.evaluar(alcista, velas, 4030.0, tolerancia=0.0)["estado"] == "entrada_pendiente"


def test_modo_quiebre_con_vela_viva_no_activa_sin_cierre():
    """En modo quiebre el tramo vivo no cambia (no activa: exige CIERRE)."""
    quiebre = {"direccion": "ALCISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0,
               "condicion": "quiebre", "entrada_pendiente": True}
    velas = [v(3980.0, 3960.0, cierre=3970.0)]
    ev = sg.evaluar(quiebre, velas, 3990.0, vela_viva={"high": 4050.0, "low": 3965.0})
    assert ev["estado"] == "entrada_pendiente"


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


# ───────────────────────────────────────── la oportunidad de hoy (gerencia, 2026-10-19)


def _hoy(direccion="ALCISTA", motivo=None):
    return {"direccion": direccion, "entrada": 4124.0, "stop": 4074.0, "objetivo": 4274.0, "motivo": motivo,
            "entrada_pendiente": False, "estado": "TENDENCIA", "condicion": None}


def test_la_oportunidad_de_hoy_contraria_a_la_foto_invalida_lo_anterior():
    hoy = sg.oportunidad_de_hoy(_hoy("ALCISTA"), {"direccion": "BAJISTA"}, {"estado": "en_curso"}, 20.0, 2, "XAUUSD")
    assert hoy["invalida"] and hoy["cambia_direccion"]
    assert hoy["ratio"] == "1:3" and hoy["atr"] == "20,00" and hoy["plazo"] == "1 a 2 días"


def test_la_oportunidad_de_hoy_en_el_mismo_sentido_no_invalida():
    hoy = sg.oportunidad_de_hoy(_hoy("BAJISTA"), {"direccion": "BAJISTA"}, {"estado": "en_curso"}, 20.0, 2, "XAUUSD")
    assert not hoy["invalida"]


def test_con_la_foto_cerrada_en_stop_el_plan_anterior_ya_no_vale():
    hoy = sg.oportunidad_de_hoy(_hoy("BAJISTA"), {"direccion": "BAJISTA"}, {"estado": "stop"}, 20.0, 2, "XAUUSD")
    assert hoy["invalida"] and not hoy["cambia_direccion"]


def test_sin_niveles_hoy_no_hay_oportunidad_que_comunicar():
    assert sg.oportunidad_de_hoy(_hoy(motivo="sin atr"), None, {"estado": "en_curso"}, 0.0, 2, "XAUUSD") is None


def test_las_acciones_tienen_hasta_una_semana():
    assert sg.plazo_esperado("#AAPL") == "hasta 1 semana" and sg.plazo_esperado("QQQ.US") == "hasta 1 semana"
    assert sg.plazo_esperado("USDCLP") == "1 a 2 días"


def test_entrada_real_fuera_de_stop_y_objetivo_se_rechaza():
    import pytest

    sg.validar_entrada_real(ALZA, 3962.0)  # el ejemplo de gerencia: entró en 962 con stop en 960
    for fuera in (3949.0, 4150.0, 4200.0):
        with pytest.raises(ValueError):
            sg.validar_entrada_real(ALZA, fuera)


def test_el_texto_dice_que_lo_anterior_queda_invalidado_y_no_lleva_precios():
    hoy = sg.oportunidad_de_hoy(_hoy("ALCISTA"), {"direccion": "BAJISTA"}, {"estado": "en_curso"}, 20.0, 2, "XAUUSD")
    t = sg.texto_oportunidad_hoy("Oro", {"direccion": "BAJISTA"}, hoy, "lunes")
    assert "invalidada" in t and "compra" in t and not any(c.isdigit() for c in t)


def test_el_texto_del_mismo_sentido_comunica_la_oportunidad_como_propia():
    hoy = sg.oportunidad_de_hoy(_hoy("BAJISTA"), {"direccion": "BAJISTA"}, {"estado": "en_curso"}, 20.0, 2, "XAUUSD")
    t = sg.texto_oportunidad_hoy("Oro", {"direccion": "BAJISTA"}, hoy, "lunes")
    assert "oportunidad de venta" in t and "invalidada" not in t
    assert sg.texto_oportunidad_hoy("Oro", {"direccion": "BAJISTA"}, None, "lunes") == ""


POSTURA = {"caso": "contra", "marco_semana": "m", "plan_hoy": "p", "puente": "b", "calidad_hoy": "B"}


def test_el_texto_de_la_postura_cubre_los_cuatro_casos_sin_precios_ni_palabras_vetadas():
    hoy = {"direccion": "ALCISTA"}
    assert set(sg.CASOS_POSTURA) == {"coinciden", "contra", "semana_cambio", "sin_plan_hoy"}
    for caso in sg.CASOS_POSTURA:
        for con_hoy in (hoy, None):
            t = sg.texto_postura({**POSTURA, "caso": caso}, con_hoy, "lunes")
            assert not any(c.isdigit() for c in t.replace("8 a 10", "")), t
            assert not any(v in t.lower() for v in ("—", "–", "stop", "entrada", "oportunidad", "señal", "techo", "suelo")), t


def test_la_postura_contra_la_semana_no_dice_que_la_semana_queda_invalidada():
    t = sg.texto_postura(POSTURA, {"direccion": "ALCISTA"}, "lunes")
    assert "sigue vigente" in t and "invalid" not in t and "línea B" in t
    assert "línea B" not in sg.texto_postura({**POSTURA, "caso": "sin_plan_hoy"}, None, "lunes")


# ───────────────────────────────────────────────────────────── suceso único (Task 4)

SCL = ZoneInfo("America/Santiago")
AHORA_MIERC = datetime(2026, 10, 21, 11, 0, tzinfo=SCL)


def _setup_analisis_vigente(tmp_path, ticker="XAUUSD", direccion="BAJISTA"):
    d = tmp_path / "foto"
    d.mkdir(parents=True, exist_ok=True)
    a = fx.activo_semanal()
    a["ticker"] = ticker
    a["nombre"] = "Oro" if ticker == "XAUUSD" else ticker
    p = es.nueva_pieza("oportunidad", {"ticker": ticker}, {"ticker": ticker, "activos": [a]}, {})
    pr.guardar_pieza(p, d)
    reg = tmp_path / "registro.json"
    ahora_lunes = datetime(2026, 10, 19, 10, 0, tzinfo=SCL)
    rg.anotar(ticker, d, ahora_lunes, direccion, {"nombre": "Camila", "id": "1"}, reg)
    return reg, a


def test_redactar_usa_suceso():
    resumen = asdict(Resumen(
        estado="en_nivel",
        sentido="ALCISTA",
        nivel=4150.0,
        objetivo=4200.0,
        siguiente=None,
        calidad="A+",
        nota_semana="",
    ))
    datos = {"nombre": "Oro", "suceso": resumen}
    texto, aparte = sg.redactar(datos, "Camila")
    assert texto.startswith("Hola Camila, ")
    assert "el oro (CFD)" in texto
    assert "4150" not in texto
    assert aparte == ""


def test_preparar_seguimiento_mercado_cerrado(tmp_path):
    """Review Focus 1: mercado cerrado o sin vela en curso da 'cerrado' y no escribe archivo."""
    reg, a = _setup_analisis_vigente(tmp_path)
    base_suc = tmp_path / "sucesos"
    lec = pr.Lectores(
        registro=reg,
        base_sucesos=base_suc,
        catalogo=lambda t: a,
        grafico_lectura=lambda *args, **kw: tmp_path / "grafico.png",
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4000.0, direccion="BAJISTA"), {"H4": pd.DataFrame()}),
        velas=lambda ticker, marcos, extra=0: (conf.velas_de(tori.crear_m15(), semilla=11), None)
    )
    dir_pedido = tmp_path / "pedido"
    dir_pedido.mkdir(parents=True, exist_ok=True)
    hecha = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir_pedido, AHORA_MIERC, lec)
    suc = hecha.pieza["datos"]["suceso"]
    assert suc["estado"] == "cerrado"
    assert not base_suc.exists() or list(base_suc.rglob("*.json")) == []


def test_preparar_seguimiento_fija_suceso_y_lo_reutiliza(tmp_path):
    """Fija el suceso en la primera llamada y lo reusa en llamadas posteriores."""
    reg, a = _setup_analisis_vigente(tmp_path)
    base_suc = tmp_path / "sucesos"
    velas_m15 = conf.velas_de(tori.crear_m15(), semilla=11)
    t_ult = int(velas_m15["M15"]["time"].iloc[-1])
    velas_m5 = pd.DataFrame([{"time": t_ult + 300, "open": 4000.0, "high": 4010.0, "low": 3995.0, "close": 4005.0}])
    en_curso = VelaEnCurso(t_ult + 900, 4005.0, datetime.fromtimestamp(t_ult + 1800, tz=SCL))

    def lector(ticker, marcos, extra=0):
        if "M5" in marcos.todos:
            return {"M5": velas_m5}, None
        return velas_m15, en_curso

    lec = pr.Lectores(
        registro=reg,
        base_sucesos=base_suc,
        catalogo=lambda t: a,
        grafico_lectura=lambda *args, **kw: tmp_path / "grafico.png",
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4005.0, direccion="BAJISTA"), {"H4": pd.DataFrame()}),
        velas=lector
    )
    dir1 = tmp_path / "pedido1"
    dir1.mkdir(parents=True, exist_ok=True)
    hecha1 = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir1, AHORA_MIERC, lec)
    suc1 = hecha1.pieza["datos"]["suceso"]
    assert suc1["sentido"] in ("ALCISTA", "BAJISTA")
    archivos = list(base_suc.rglob("*.json"))
    assert len(archivos) == 1

    # Segunda llamada: reutiliza el suceso guardado
    dir2 = tmp_path / "pedido2"
    dir2.mkdir(parents=True, exist_ok=True)
    hecha2 = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir2, AHORA_MIERC, lec)
    suc2 = hecha2.pieza["datos"]["suceso"]
    assert suc2["sentido"] == suc1["sentido"]
    assert suc2["calidad"] == suc1["calidad"]


def test_preparar_seguimiento_sin_direccion(tmp_path, monkeypatch):
    """Si la lectura de M15 no marca dirección, el suceso queda 'sin_direccion'."""
    reg, a = _setup_analisis_vigente(tmp_path)
    base_suc = tmp_path / "sucesos"
    velas_m15 = conf.velas_de(tori.crear_m15(), semilla=11)
    t_ult = int(velas_m15["M15"]["time"].iloc[-1])
    en_curso = VelaEnCurso(t_ult + 900, 4000.0, datetime.fromtimestamp(t_ult + 1800, tz=SCL))

    lec = pr.Lectores(
        registro=reg,
        base_sucesos=base_suc,
        catalogo=lambda t: a,
        grafico_lectura=lambda *args, **kw: tmp_path / "grafico.png",
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4000.0, direccion="BAJISTA"), {"H4": pd.DataFrame()}),
        velas=lambda ticker, marcos, extra=0: (velas_m15, en_curso)
    )
    monkeypatch.setattr(suceso, "elegir", lambda *args, **kw: None)

    dir_pedido = tmp_path / "pedido"
    dir_pedido.mkdir(parents=True, exist_ok=True)
    hecha = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir_pedido, AHORA_MIERC, lec)
    assert hecha.pieza["datos"]["suceso"]["estado"] == "sin_direccion"
    assert not base_suc.exists() or list(base_suc.rglob("*.json")) == []


def test_preparar_seguimiento_nota_semana_solo_si_contraria(tmp_path, monkeypatch):
    """La nota semanal se muestra si el suceso va en contra de la semana."""
    monkeypatch.setattr("referencia_semanal.debe_reemplazar", lambda *args, **kw: False)
    reg, a = _setup_analisis_vigente(tmp_path, direccion="BAJISTA")
    base_suc = tmp_path / "sucesos"
    velas_m15 = conf.velas_de(tori.crear_m15(), semilla=11)
    t_ult = int(velas_m15["M15"]["time"].iloc[-1])
    velas_m5 = pd.DataFrame([{"time": t_ult + 300, "open": 4000.0, "high": 4010.0, "low": 3995.0, "close": 4005.0}])
    en_curso = VelaEnCurso(t_ult + 900, 4005.0, datetime.fromtimestamp(t_ult + 1800, tz=SCL))

    def lector(ticker, marcos, extra=0):
        if "M5" in marcos.todos:
            return {"M5": velas_m5}, None
        return velas_m15, en_curso

    lec = pr.Lectores(
        registro=reg,
        base_sucesos=base_suc,
        catalogo=lambda t: a,
        grafico_lectura=lambda *args, **kw: tmp_path / "grafico.png",
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4005.0, direccion="BAJISTA"), {"H4": pd.DataFrame()}),
        velas=lector
    )
    dir_pedido = tmp_path / "pedido"
    dir_pedido.mkdir(parents=True, exist_ok=True)
    hecha = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir_pedido, AHORA_MIERC, lec)
    suc = hecha.pieza["datos"]["suceso"]
    if suc["sentido"] == "ALCISTA":
        assert "tendencia de la semana sigue a la baja" in suc["nota_semana"]
    else:
        assert suc["nota_semana"] == ""


def test_preparar_seguimiento_traza_la_linea_fijada_y_no_la_de_ahora(tmp_path, monkeypatch):
    """El gráfico dibuja la línea guardada en la mañana, aunque la lectura de ahora vea otra."""
    monkeypatch.setattr("referencia_semanal.debe_reemplazar", lambda *args, **kw: False)
    reg, a = _setup_analisis_vigente(tmp_path, direccion="BAJISTA")
    base_suc = tmp_path / "sucesos"
    velas_m15 = conf.velas_de(tori.crear_m15(), semilla=11)
    tiempos = velas_m15["M15"]["time"].tolist()
    t_ult = tiempos[-1]
    suceso.guardar(suceso.Suceso("XAUUSD", "2026-10-21", "2026-10-21T09:00-03:00", "ALCISTA", t_ult, 3990.0,
                                 1.0, 4100.0, "A+", 2.0), base_suc)
    velas_m5 = pd.DataFrame([{"time": t_ult + 900, "open": 4000.0, "high": 4010.0, "low": 3995.0, "close": 4005.0}])
    en_curso = VelaEnCurso(t_ult + 900, 4005.0, datetime.fromtimestamp(t_ult + 1800, tz=SCL))
    graficos = []

    def lector(ticker, marcos, extra=0):
        return ({"M5": velas_m5}, None) if "M5" in marcos.todos else (velas_m15, en_curso)

    lec = pr.Lectores(
        registro=reg, base_sucesos=base_suc, catalogo=lambda t: a,
        grafico_lectura=lambda ticker, nombre, lectura, destino, **kw: graficos.append((lectura, kw)) or destino,
        lectura_actual=lambda est, t, d, lector, ahora, referencia=None: (fx.lectura(precio=4005.0, direccion="BAJISTA"), {"H4": pd.DataFrame()}),
        velas=lector,
    )
    dir_pedido = tmp_path / "pedido"
    dir_pedido.mkdir()
    suc = pr.preparar_seguimiento(Orden("seguimiento", {"ticker": "XAUUSD"}), dir_pedido, AHORA_MIERC, lec).pieza["datos"]["suceso"]
    assert suc["estado"] == "esperando" and suc["sentido"] == "ALCISTA" and suc["calidad"] == "A+"
    assert suc["nivel"] == pytest.approx(3990.0 + 1200 / 900)  # la línea en el cierre de la vela de 5m
    assert suc["nota_semana"] == "Es un retroceso de hoy: la tendencia de la semana sigue a la baja."
    lectura, kw = graficos[-1]
    (linea,) = lectura.lineas
    assert linea.marco == "M15" and linea.puntos == ((tiempos[-2], 3989.0), (t_ult, 3990.0))
    assert [n for _, n in kw["niveles"]] == ["NIVEL DEL DÍA", "OBJETIVO"]
