"""La agenda del día manda en Avisos (spec 2026-09-28-carruseles-avisos-design.md §13)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pipeline_avisos as pa  # noqa: E402
import story_render  # noqa: E402
from test_pipeline_avisos import AGENDA, lectura_falsa, vision  # noqa: E402


def evento_jornada(hora, evento, nombre_es, consenso="89.2", anterior="89.4", actual="", resultado="",
                   pais="United States", explicacion="Mide algo que importa."):
    return {"fecha": "2026-09-29", "hora": hora, "pais": pais, "evento": evento, "nombre_es": nombre_es,
            "explicacion": explicacion, "consenso": consenso, "anterior": anterior,
            "actual": actual, "resultado": resultado}


CONFIANZA = evento_jornada("11:00", "CB Consumer Confidence (Sep)", "Confianza del consumidor")
JOLTS = evento_jornada("11:00", "JOLTS Job Openings (Aug)", "Vacantes de empleo",
                       consenso="7.230M", anterior="7.335M")
EFECTO = {"orden": "primero", "dolar": "sube", "usdclp": "sube", "oro": "baja"}
SIETE_45 = datetime(2026, 9, 29, 7, 45, tzinfo=pa.SANTIAGO)
ONCE_10 = datetime(2026, 9, 29, 11, 10, tzinfo=pa.SANTIAGO)


def cedio(t, d, a):
    return {"desde": 970.80, "ahora": 968.97, "digits": 2}


def preparar(tmp_path, momento, ahora, jornada, efecto=lambda ev: EFECTO, mov=cedio):
    hist = tmp_path / "hist.json"
    if not hist.exists():
        hist.write_text("[]", encoding="utf-8")
    return pa.preparar(
        momento, ahora,
        lector=lambda t, a: lectura_falsa(t),
        lector_agenda=lambda a: (AGENDA, []),
        lector_jornada=lambda a: (jornada, []),
        lector_movimiento=mov,
        efecto_de=efecto,
        visiones={"v": vision("v")}, historial_ruta=hist, dir_base=tmp_path / "carrusel",
    )


# ---------------------------------------------------------------- agenda del día


def test_con_datos_la_agenda_del_dia_tiene_portada_agenda_y_lectura(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [CONFIANZA, JOLTS])
    meta = pa.leer_meta(ruta)
    assert meta["formato"] == "agenda_dia" and meta["activo"] is None
    laminas = dict(pa.leer_laminas(ruta))
    assert list(laminas) == ["1_portada", "2_dia", "3_lectura"]
    assert laminas["1_portada"]["sello"] == "AVISOS · AGENDA DEL DÍA"
    assert [e["esperado"] for e in laminas["2_dia"]["eventos"]] == ["89,2", "7,230M"]
    assert laminas["2_dia"]["eventos"][0]["dia"] == "HOY 29"


def test_la_lectura_de_la_agenda_toma_la_reaccion_del_glosario(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [CONFIANZA])
    punto = dict(pa.leer_laminas(ruta))["3_lectura"]["puntos"][0]
    assert punto["titulo_punto"] == "11:00 · Confianza del consumidor"
    assert "el dólar y el USD/CLP a subir" in punto["texto"]
    assert "el oro a bajar" in punto["texto"] and "al revés" in punto["texto"]


def test_con_el_glosario_real_la_reaccion_de_jolts_sale_sola(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [JOLTS], efecto=None)
    texto = dict(pa.leer_laminas(ruta))["3_lectura"]["puntos"][0]["texto"]
    assert "a subir" in texto and texto != pa.MARCA


def test_un_dato_sin_reaccion_declarada_deja_la_lectura_por_escribir(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [CONFIANZA], efecto=lambda ev: None)
    assert dict(pa.leer_laminas(ruta))["3_lectura"]["puntos"][0]["texto"] == pa.MARCA
    assert any("3_lectura" in e for e in pa.validar_tanda(ruta, SIETE_45, {}))


def test_sin_datos_en_la_jornada_la_agenda_es_la_de_la_semana(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [])
    assert pa.leer_meta(ruta)["formato"] == "agenda"


def test_la_agenda_solo_lista_lo_que_falta_por_salir(tmp_path):
    temprano = evento_jornada("08:00", "Imacec", "Imacec", pais="Chile")
    nueve = datetime(2026, 9, 29, 9, 0, tzinfo=pa.SANTIAGO)
    ruta = preparar(tmp_path, "avisos_agenda", nueve, [temprano, CONFIANZA])
    eventos = dict(pa.leer_laminas(ruta))["2_dia"]["eventos"]
    assert [e["hora"] for e in eventos] == ["11:00 CLST"]


def test_la_jornada_cierra_a_las_18_30():
    assert pa.CIERRE_JORNADA.strftime("%H:%M") == "18:30"
    assert pa.INICIO_JORNADA.strftime("%H:%M") == "07:45"


def test_la_agenda_del_dia_cierra_con_un_cierre_del_dia(tmp_path):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [CONFIANZA])
    laminas = dict(pa.leer_laminas(ruta))
    portada = dict(laminas["1_portada"], pie="Hoy manda el consumo de EE.UU.")
    texto = pa.mensaje_de(portada, pa.leer_meta(ruta))
    assert any(c in texto for c in pa.CIERRES_DIA)


# ---------------------------------------------------------------- mañana y tarde


def test_la_cita_de_la_manana_no_sale_un_dia_con_datos(tmp_path):
    with pytest.raises(pa.HoyNoCorresponde, match="agenda del día"):
        preparar(tmp_path, "avisos_manana", datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO), [CONFIANZA])


def test_el_lunes_sin_datos_la_semana_sale_en_la_manana_y_la_tarde_es_balance(tmp_path):
    lunes = datetime(2026, 9, 28, 7, 45, tzinfo=pa.SANTIAGO)
    assert pa.leer_meta(preparar(tmp_path, "avisos_agenda", lunes, []))["formato"] == "agenda"
    tarde = preparar(tmp_path, "avisos_tarde", datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO), [])
    assert pa.leer_meta(tarde)["formato"] == "balance"


def test_el_lunes_con_datos_la_tarde_sigue_siendo_la_semana(tmp_path):
    lunes = datetime(2026, 9, 28, 7, 45, tzinfo=pa.SANTIAGO)
    preparar(tmp_path, "avisos_agenda", lunes, [dict(CONFIANZA, fecha="2026-09-28")])
    tarde = preparar(tmp_path, "avisos_tarde", datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO), [])
    assert pa.leer_meta(tarde)["formato"] == "agenda"


# ---------------------------------------------------------------- resultado


PUBLICADOS = [dict(CONFIANZA, actual="81.9", resultado="peor"), dict(JOLTS, actual="7.079M", resultado="peor")]


def test_resultado_de_la_misma_hora_es_una_sola_pieza(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS)
    laminas = pa.leer_laminas(ruta)
    assert [stem for stem, _ in laminas] == ["1_resultado"]
    lamina = laminas[0][1]
    assert lamina["titular"] == "Datos más débiles de lo esperado"
    assert [e["actual"] for e in lamina["eventos"]] == ["81,9", "7,079M"]
    assert [e["impacto_slug"] for e in lamina["eventos"]] == ["peor", "peor"]
    assert lamina["movimiento"].startswith("Desde las 11:00 el USD/CLP cede de 970,80 a 968,97")


def test_un_dato_de_eeuu_mide_el_dolar_y_el_oro():
    assert pa.monedas_de([CONFIANZA]) == ["USDCLP", "XAUUSD"]
    assert pa.monedas_de([dict(CONFIANZA, pais="China")]) == ["COPPER", "USDCLP"]


def test_resultado_con_veredictos_opuestos_dice_senales_mixtas():
    eventos = [dict(CONFIANZA, resultado="peor"), dict(JOLTS, resultado="mejor")]
    assert pa.titular_resultado(eventos) == "Señales mixtas en los datos de las 11:00"


def test_resultado_sin_cifra_todavia_es_falla_de_datos(tmp_path):
    with pytest.raises(pa.LecturaFallidaError, match="todavía no traen cifra"):
        preparar(tmp_path, "avisos_resultado", ONCE_10, [CONFIANZA, JOLTS])


def test_resultado_con_un_solo_dato_publicado_espera_al_otro(tmp_path):
    parcial = [dict(CONFIANZA, actual="81.9", resultado="peor"), JOLTS]
    with pytest.raises(pa.LecturaFallidaError, match="falta la cifra"):
        preparar(tmp_path, "avisos_resultado", datetime(2026, 9, 29, 11, 5, tzinfo=pa.SANTIAGO), parcial)


def test_un_resultado_no_se_prepara_dos_veces(tmp_path):
    preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS)
    with pytest.raises(pa.HoyNoCorresponde):
        preparar(tmp_path, "avisos_resultado", ONCE_10 + timedelta(minutes=15), PUBLICADOS)


def test_sin_datos_publicados_el_resultado_no_corresponde(tmp_path):
    with pytest.raises(pa.HoyNoCorresponde):
        preparar(tmp_path, "avisos_resultado", SIETE_45, [CONFIANZA])


def test_el_pie_del_resultado_lleva_veredicto_movimiento_y_temporalidad(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS[:1])
    _, payload = pa.leer_laminas(ruta)[0]
    payload["parrafo"] = "Las familias están menos optimistas y eso le resta fuerza al dólar."
    texto = pa.mensaje_de(payload, pa.leer_meta(ruta))
    assert "*Confianza del consumidor*: 81,9 frente a 89,2 esperado → *PEOR*" in texto
    assert "⬇️ *Dólar*: El USD/CLP cede de 970,80 a 968,97 desde las 11:00." in texto
    assert "*Oro*: Cede de 970,80 a 968,97" in texto  # el doble de la prueba mide igual las dos
    assert "⏱️ *Temporalidad del impacto*" in texto
    assert "—" not in texto and "–" not in texto


def test_un_resultado_sin_escribir_no_se_rinde_y_escrito_si(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS)
    assert pa.validar_tanda(ruta, ONCE_10, {})
    stem, payload = pa.leer_laminas(ruta)[0]
    payload["parrafo"] = "Un empleo que se enfría le da a la Fed más espacio para bajar tasas."
    (ruta / f"{stem}.json").write_text(__import__("json").dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert pa.validar_tanda(ruta, ONCE_10, {}) == []


def test_refrescar_un_resultado_que_dio_vuelta_no_sale_sin_reescribir(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS[:1])

    def subio(t, d, a):
        return {"desde": 970.80, "ahora": 972.10, "digits": 2}

    with pytest.raises(SystemExit, match="dio vuelta"):
        pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=5), lector_movimiento=subio)
    motivos = pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=5), lector_movimiento=subio, reescribir=True)
    assert "párrafo vuelto a [[ESCRIBIR]]" in motivos
    assert pa.leer_laminas(ruta)[0][1]["parrafo"] == pa.MARCA


def test_refrescar_un_resultado_estable_mueve_las_cifras(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS[:1])

    def sigue(t, d, a):
        return {"desde": 970.80, "ahora": 967.50, "digits": 2}

    pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=5), lector_movimiento=sigue)
    assert "967,50" in pa.leer_laminas(ruta)[0][1]["movimiento"]


def test_la_imagen_del_resultado_rinde_sin_tokens_huerfanos(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS)
    _, payload = pa.leer_laminas(ruta)[0]
    html = story_render.build_html(pa.tokens_de(payload),
                                   pa.DIR_PLANTILLAS / pa.PLANTILLAS["avisos_resultado"])
    assert "{{" not in html and "RESULTADO" in html.upper() and "970,80" in html


# ------------------------------------------- banda de ruido (2026-09-30, EIA)
# El resultado de los inventarios de la EIA se frenó dos veces con el WTI
# moviéndose 0,04, 0,07 y 0,00 desde las 11:30, bajo el 10 % de su vela
# típica: sin banda muerta, un solo tick daba vuelta la dirección.


def _wti(ahora, banda=0.18):
    def lector(t, d, a):
        return {"desde": 93.792, "ahora": ahora, "digits": 3, "banda": banda}
    return lector


def test_el_ruido_dentro_de_la_banda_no_da_vuelta_el_resultado(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS[:1], mov=_wti(93.752))
    stem, payload = pa.leer_laminas(ruta)[0]
    payload["parrafo"] = "El precio casi no reaccionó al dato."
    (ruta / f"{stem}.json").write_text(__import__("json").dumps(payload, ensure_ascii=False), encoding="utf-8")
    pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=5), lector_movimiento=_wti(93.862))
    pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=9), lector_movimiento=_wti(93.792))
    lamina = pa.leer_laminas(ruta)[0][1]
    assert lamina["parrafo"] != pa.MARCA
    assert "93,792" in lamina["movimiento"]


def test_una_vuelta_que_supera_la_banda_frena_el_resultado(tmp_path):
    ruta = preparar(tmp_path, "avisos_resultado", ONCE_10, PUBLICADOS[:1], mov=_wti(93.400))
    with pytest.raises(SystemExit, match="dio vuelta"):
        pa.refrescar_tanda(ruta, ONCE_10 + timedelta(minutes=5), lector_movimiento=_wti(94.100))


def test_dentro_de_la_banda_el_movimiento_se_narra_como_estable():
    frase = pa.frase_movimiento({"WTI.spot": {"desde": 93.792, "ahora": 93.752, "digits": 3, "banda": 0.18}},
                                "11:30")
    assert frase == "Desde las 11:30 el WTI se mantiene cerca de 93,752."


def test_la_banda_es_un_cuarto_del_atr_de_m15():
    velas = [{"high": 10.8, "low": 10.0, "close": 10.4}] * 20
    assert pa.banda_de_ruido(velas) == pytest.approx(0.2)
