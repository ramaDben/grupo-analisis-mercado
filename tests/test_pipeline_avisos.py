"""Carruseles de Avisos (spec 2026-09-28-carruseles-avisos-design.md)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pipeline_avisos as pa  # noqa: E402

LUNES = date(2026, 9, 28)
MARTES = date(2026, 9, 29)


def test_feriado_nyse_no_es_habil():
    assert pa.es_dia_habil(date(2026, 11, 26)) is False  # Acción de Gracias


def test_sabado_no_es_habil_y_martes_si():
    assert pa.es_dia_habil(date(2026, 10, 3)) is False
    assert pa.es_dia_habil(MARTES) is True


def test_la_tarde_es_agenda_el_lunes_y_balance_el_resto():
    assert pa.formato_del_momento("avisos_tarde", LUNES) == "agenda"
    assert pa.formato_del_momento("avisos_tarde", MARTES) == "balance"
    assert pa.formato_del_momento("avisos_manana", MARTES) == "cita"
    assert pa.formato_del_momento("avisos_mediodia", MARTES) == "meta"


def test_momento_desconocido_se_detiene_nombrando_las_opciones():
    with pytest.raises(SystemExit, match="avisos_manana"):
        pa.formato_del_momento("avisos_noche", MARTES)


def test_laminas_con_voz_numeran_sobre_cuatro():
    laminas = pa.laminas_de("cita", con_voz=True)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert laminas[1]["posicion"] == "2/4 · La voz del banco"
    assert laminas[2]["plantilla"] == "avisos_datos"


def test_laminas_sin_voz_renumeran_sobre_tres():
    laminas = pa.laminas_de("meta", con_voz=False)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_datos", "3_lectura"]
    assert laminas[2]["posicion"] == "3/3 · Nuestra lectura"


def test_la_agenda_no_lleva_voz_ni_alerta():
    assert [l["clave"] for l in pa.laminas_de("agenda", con_voz=True)] == ["portada", "semana", "lectura"]


def test_toda_plantilla_de_lamina_existe_en_disco():
    for plantilla, archivo in pa.PLANTILLAS.items():
        assert (pa.DIR_PLANTILLAS / archivo).exists(), f"{plantilla}: falta {archivo}"


def test_ninguna_secuencia_pasa_del_tope():
    assert all(len(s) <= pa.MAX_LAMINAS for s in pa.SECUENCIAS.values())


def test_etiqueta_hora_nombra_el_horario_chileno():
    verano = datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO)
    invierno = datetime(2026, 7, 1, 11, 30, tzinfo=pa.SANTIAGO)
    assert pa.etiqueta_hora(verano) == "11:30 CLST"
    assert pa.etiqueta_hora(invierno) == "11:30 CLT"
    assert pa.fecha_hora(verano) == "MARTES 29 SEP · 11:30 CLST"


# ---------------------------------------------------------------- elección


def vision(id_, activo="USDCLP", tipo="textual", cita="El dólar se mueve por datos.", fecha="2026-09-20", **extra):
    return {"id": id_, "quien": "Ana Pérez", "institucion": "Banco X", "activo": activo, "tipo": tipo,
            "cita": cita, "fecha": fecha, "fuente": "Diario", "url": "https://ejemplo.cl/nota", **extra}


def uso(fecha, activo, momento="avisos_manana", vid=None):
    return {"fecha": fecha, "canal": pa.CANAL, "tipo": "avisos", "clave": activo, "momento": momento, "vision": vid}


UNIVERSO = ["USDCLP", "XAUUSD", "WTI.spot"]


def test_variante_por_tipo_y_cifra():
    assert pa.variante_de(vision("a")) == "cita"
    assert pa.variante_de(vision("b", tipo="traduccion")) == "cita"
    assert pa.variante_de(vision("c", tipo="parafrasis", cita="Sin cifras, postura prudente.")) == "cita"
    assert pa.variante_de(vision("d", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.")) == "meta"


def test_meta_exige_horizonte():
    v = vision("m", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.", meta="US$6.000")
    assert not pa.vision_califica(v, "meta", MARTES, [])
    assert pa.vision_califica({**v, "horizonte": "promedio del 4T 2026"}, "meta", MARTES, [])


def test_meta_que_no_figura_en_la_cita_no_califica():
    v = vision("m", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.", meta="US$6.500", horizonte="4T 2026")
    assert not pa.vision_califica(v, "meta", MARTES, [])


def test_vision_vieja_o_reciente_en_avisos_no_califica():
    assert not pa.vision_califica(vision("v", fecha="2026-08-01"), "cita", MARTES, [])
    hist = [{"fecha": "2026-09-20", "canal": pa.CANAL, "tipo": "vision", "clave": "v"}]
    assert not pa.vision_califica(vision("v"), "cita", MARTES, hist)
    hist_viejo = [{"fecha": "2026-09-10", "canal": pa.CANAL, "tipo": "vision", "clave": "v"}]
    assert pa.vision_califica(vision("v"), "cita", MARTES, hist_viejo)


def test_candidatos_sacan_lo_cubierto_hoy_y_los_feriados(monkeypatch):
    monkeypatch.setattr("screener_gi.gate_feriado", lambda t, f: "feriado de NYSE" if t == "WTI.spot" else None)
    hist = [uso(MARTES.isoformat(), "USDCLP")]
    assert pa.candidatos(MARTES, hist, UNIVERSO) == ["XAUUSD"]


def test_primero_el_activo_con_vision_fresca():
    visiones = {"v": vision("v", activo="XAUUSD")}
    hist = [uso("2026-09-25", "XAUUSD"), uso("2026-09-26", "XAUUSD")]
    assert pa.elegir("cita", MARTES, visiones, hist, UNIVERSO) == ("XAUUSD", "v")


def test_entre_iguales_el_menos_cubierto_y_luego_alfabetico():
    visiones = {"a": vision("a", activo="XAUUSD"), "b": vision("b", activo="USDCLP")}
    assert pa.elegir("cita", MARTES, visiones, [uso("2026-09-25", "USDCLP")], UNIVERSO) == ("XAUUSD", "a")
    assert pa.elegir("cita", MARTES, visiones, [], UNIVERSO) == ("USDCLP", "b")


def test_sin_vision_gana_el_menos_cubierto_sin_voz():
    hist = [uso("2026-09-25", "USDCLP"), uso("2026-09-26", "WTI.spot")]
    assert pa.elegir("cita", MARTES, {}, hist, UNIVERSO) == ("XAUUSD", None)


def test_sin_candidatos_se_informa():
    hist = [uso(MARTES.isoformat(), t) for t in UNIVERSO]
    with pytest.raises(pa.SinCandidatosError):
        pa.elegir("cita", MARTES, {}, hist, UNIVERSO)


def test_balance_retoma_la_manana():
    hist = [uso(MARTES.isoformat(), "XAUUSD", "avisos_manana", "v"), uso(MARTES.isoformat(), "USDCLP", "avisos_mediodia")]
    assert pa.activo_del_balance(hist, MARTES) == ("XAUUSD", "v")


def test_balance_cae_a_mediodia():
    hist = [uso(MARTES.isoformat(), "USDCLP", "avisos_mediodia", "m")]
    assert pa.activo_del_balance(hist, MARTES) == ("USDCLP", "m")


def test_balance_sin_manana_ni_mediodia_sale_sin_voz():
    assert pa.activo_del_balance([uso("2026-09-28", "USDCLP")], MARTES) == (None, None)


def test_registrar_uso_anota_al_preparar(tmp_path):
    ruta = tmp_path / "hist.json"
    ruta.write_text("[]", encoding="utf-8")
    pa.registrar_uso(MARTES, "avisos_manana", "USDCLP", "v", gastar_vision=True, ruta=ruta)
    pa.registrar_uso(MARTES, "avisos_tarde", "USDCLP", "v", gastar_vision=False, ruta=ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert [e["tipo"] for e in datos] == ["vision", "avisos", "avisos"]
    assert datos[2]["momento"] == "avisos_tarde"
