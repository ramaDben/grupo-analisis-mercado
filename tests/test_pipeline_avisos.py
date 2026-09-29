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


# ---------------------------------------------------------------- láminas


AHORA = datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO)


def lectura_falsa(ticker="USDCLP", precio=936.32, digits=2, nombre="Dólar / Peso chileno"):
    activo = {"ticker": ticker, "nombre": nombre, "clase": "forex_commodities", "categoria": "forex",
              "digits": digits, "unidad": "CLP", "imagen": "assets/activos/usdclp.jpg", "volatilidad": "media",
              "nota_volatilidad": "en 1H se lee el movimiento del día sin el ruido de 15M; 4H confirma la tendencia"}
    sel = {"ticker": ticker, "nombre": nombre, "clase": "forex_commodities", "direccion": "ALCISTA", "score": 60,
           "precio": precio, "soporte": precio - 3, "resistencia": precio + 3, "atr_h1": 1.2, "atr_d1": 6.0,
           "impulso_adc_atr": 1.8, "banda_estrecha": None, "factores": {}}
    h1 = {"price": precio, "s1": precio - 3, "r1": precio + 3, "s2": precio - 6, "r2": precio + 6,
          "ema_50": precio - 1, "donchian_50_high": precio + 8, "donchian_50_low": precio - 8, "atr_14": 1.2}
    cierres = [round(precio - (59 - i) * 0.01, 6) for i in range(60)]
    return {"ticker": ticker, "activo": activo, "seleccion": sel, "h1": h1, "cierres": cierres}


def test_tanda_de_cita_con_voz_tiene_cuatro_laminas_y_todas_con_titular_y_parrafo():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), vision("v"), [])
    assert list(laminas) == ["portada", "voz", "datos", "lectura"]
    for payload in laminas.values():
        assert "titular" in payload and "parrafo" in payload
        assert payload["_plantilla"] in pa.PLANTILLAS
    assert meta["activo"] == "USDCLP" and meta["vision"] == "v" and meta["_falta_vision"] is False
    assert meta["direccion"] == "Alcista"


def test_tanda_sin_vision_queda_marcada_y_sin_voz():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    assert meta["_falta_vision"] is True
    assert "voz" not in laminas


def test_la_portada_trae_el_precio_del_terminal_y_la_hora():
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    assert laminas["portada"]["dato_precio"].endswith("936,32")
    assert laminas["portada"]["dato_hora"] == "LEÍDO 11:30 CLST"
    assert laminas["portada"]["sello"] == "AVISOS · DÓLAR / PESO CHILENO"


def test_portada_del_cobre_escribe_el_precio_como_la_alerta():
    lec = lectura_falsa("COPPER", 14197.0, 0, "Cobre")
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lec, None, [])
    assert laminas["portada"]["dato_precio"].endswith(laminas["datos"]["precio_actual"])
    assert laminas["datos"]["precio_actual"] == "14197"


def test_portada_con_precio_sin_ticker_lanza():
    with pytest.raises(ValueError):
        pa.lamina_portada("Dólar / Peso chileno", "936,32", AHORA, AHORA, agenda=False, ticker=None)


def test_portada_de_agenda_no_exige_ticker():
    portada = pa.lamina_portada(None, "", AHORA, AHORA, agenda=True)
    assert portada["_procedencia"] == {"ticker": None}


def test_la_voz_meta_muestra_la_meta_y_el_precio_de_hoy():
    v = vision("m", tipo="parafrasis", cita="Proyecta $980 a fin de año.", meta="$980", horizonte="fin de 2026")
    _, laminas = pa.armar_tanda("avisos_mediodia", "meta", AHORA, lectura_falsa(), v, [])
    voz = laminas["voz"]
    assert voz["bloque_cita"] == []
    assert voz["bloque_meta"][0]["meta"] == "$980"
    assert voz["bloque_meta"][0]["precio_hoy"] == "936,32"


def test_la_voz_de_una_traduccion_lo_dice():
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), vision("t", tipo="traduccion"), [])
    assert laminas["voz"]["bloque_cita"][0]["etiqueta"] == "Traducción nuestra"


def test_la_fila_medida_incluye_los_niveles_publicados():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    fila = meta["activos"]["USDCLP"]
    niveles = {n["rol"]: n["precio"] for n in laminas["datos"]["recorrido"]["niveles"]}
    assert fila["soporte_publicado"] == niveles["SOPORTE"]
    assert fila["price"] == 936.32 and fila["digits"] == 2


AGENDA = [
    {"fecha": "2026-10-02", "hora": "08:30", "pais": "United States", "evento": "Nonfarm Payrolls",
     "nombre_es": "Nóminas no agrícolas", "consenso": "98K", "anterior": "162K"},
    {"fecha": "2026-09-30", "hora": "10:30", "pais": "United States", "evento": "Crude Oil Inventories",
     "nombre_es": "", "consenso": "", "anterior": "-1.2M"},
    {"fecha": "2026-10-05", "hora": "09:00", "pais": "Chile", "evento": "Imacec", "nombre_es": "Imacec",
     "consenso": "", "anterior": "0,5%"},
]


def test_la_agenda_arma_los_tokens_de_calendario_en_orden_y_solo_esta_semana():
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    eventos = pa.eventos_calendario(AGENDA, lunes)
    assert [e["numero"] for e in eventos] == ["01", "02"]
    assert eventos[0]["dia"] == "MIÉRCOLES 30" and eventos[0]["evento"] == "Crude Oil Inventories"
    assert eventos[1]["evento"] == "Nóminas no agrícolas" and eventos[1]["pais"] == "EE.UU."
    assert eventos[1]["esperado"] == "98K" and eventos[1]["tiene_esperado"] is True
    assert eventos[0]["tiene_esperado"] is False
    assert eventos[0]["hora"] == "10:30 CLST" and eventos[0]["impacto_slug"] == "alto"


def test_la_tanda_de_agenda_no_tiene_activo_ni_alerta():
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    meta, laminas = pa.armar_tanda("avisos_tarde", "agenda", lunes, None, None, AGENDA)
    assert list(laminas) == ["portada", "semana", "lectura"]
    assert meta["activo"] is None and meta["_falta_vision"] is False
    assert laminas["portada"]["dato_precio"] == ""
    assert laminas["portada"]["sello"] == "AVISOS · AGENDA DE LA SEMANA"
