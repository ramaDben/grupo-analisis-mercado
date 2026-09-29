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
import story_render  # noqa: E402

LUNES = date(2026, 9, 28)
MARTES = date(2026, 9, 29)


@pytest.fixture(autouse=True)
def _jornada_sin_datos(monkeypatch):
    """Ningún test lee el calendario real: la mañana se prepara solo sin datos
    fuertes (spec §13.2), y el de hoy decidiría por el test."""
    monkeypatch.setattr(pa, "leer_jornada", lambda ahora: ([], []))


def test_feriado_nyse_no_es_habil():
    assert pa.es_dia_habil(date(2026, 11, 26)) is False  # Acción de Gracias


def test_sabado_no_es_habil_y_martes_si():
    assert pa.es_dia_habil(date(2026, 10, 3)) is False
    assert pa.es_dia_habil(MARTES) is True


def test_la_tarde_es_agenda_el_lunes_y_balance_el_resto():
    assert pa.formato_del_momento("avisos_tarde", LUNES) == "agenda"
    assert pa.formato_del_momento("avisos_tarde", MARTES) == "balance"
    assert pa.formato_del_momento("avisos_manana", MARTES) == "cita"
    assert pa.formato_del_momento("avisos_agenda", MARTES) == "agenda_dia"
    assert pa.formato_del_momento("avisos_resultado", MARTES) == "resultado"


def test_el_mediodia_ya_no_es_un_momento():
    """Spec §13.2: con la agenda y los resultados, el carrusel de mediodía salió."""
    with pytest.raises(SystemExit, match="avisos_agenda"):
        pa.formato_del_momento("avisos_mediodia", MARTES)


def test_momento_desconocido_se_detiene_nombrando_las_opciones():
    with pytest.raises(SystemExit, match="avisos_manana"):
        pa.formato_del_momento("avisos_noche", MARTES)


def test_laminas_con_voz_numeran_sobre_cuatro():
    laminas = pa.laminas_de("cita", con_voz=True)
    assert [lam["stem"] for lam in laminas] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert laminas[1]["posicion"] == "2/4 · La voz del banco"
    assert laminas[2]["plantilla"] == "avisos_datos"


def test_laminas_sin_voz_renumeran_sobre_tres():
    laminas = pa.laminas_de("meta", con_voz=False)
    assert [lam["stem"] for lam in laminas] == ["1_portada", "2_datos", "3_lectura"]
    assert laminas[2]["posicion"] == "3/3 · Nuestra lectura"


def test_la_agenda_no_lleva_voz_ni_alerta():
    assert [lam["clave"] for lam in pa.laminas_de("agenda", con_voz=True)] == ["portada", "semana", "lectura"]


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


def test_entre_iguales_gana_el_activo_con_imagen(monkeypatch):
    # Ruling de revisión: con cobertura igual, el desempate alfabético ciego
    # podía elegir un activo sin `imagen` (fuera de la rotación diaria, como
    # BRENT.spot). "SINFOTO" es alfabéticamente menor y no tiene imagen.
    monkeypatch.setattr("screener_gi.gate_feriado", lambda t, f: None)
    monkeypatch.setattr(pa.pl, "_catalogo", lambda: {
        "SINFOTO": {"ticker": "SINFOTO", "imagen": None},
        "USDCLP": {"ticker": "USDCLP", "imagen": "assets/activos/usdclp.jpg"},
    })
    assert pa.elegir("cita", MARTES, {}, [], ["SINFOTO", "USDCLP"]) == ("USDCLP", None)


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


# ---------------------------------------------------------------- disco, frenos y render


def _tanda(tmp_path, formato="cita", con_vision=True, lec=None):
    momento = {"cita": "avisos_manana", "meta": "avisos_mediodia", "balance": "avisos_tarde"}.get(formato, "avisos_tarde")
    v = vision("v") if con_vision else None
    meta, laminas = pa.armar_tanda(momento, formato, AHORA, lec or lectura_falsa(), v, [])
    dir_canal = tmp_path / "2026-09-29_11-30_avisos_x" / pa.CANAL
    dir_canal.mkdir(parents=True)
    pa.escribir_meta(dir_canal, meta)
    pa.escribir_laminas(dir_canal, formato, laminas)
    return dir_canal, {"v": v} if v else {}


def _escribir_todo(dir_canal, pie="El dólar mantiene un sesgo alcista sobre su promedio de 50 horas."):
    for stem, payload in pa.leer_laminas(dir_canal):
        for campo in ("kicker", "titular", "parrafo"):
            if campo in payload:
                payload[campo] = "Texto de prueba suficientemente largo para el freno"
        if "pie" in payload:
            payload["pie"] = pie
        for lista in ("claves", "puntos"):
            for item in payload.get(lista, []):
                for k in ("texto", "titulo_punto"):
                    if k in item:
                        item[k] = "Punto de prueba"
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_escribir_laminas_numera_y_pone_el_pie_de_posicion(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    stems = [s for s, _ in pa.leer_laminas(dir_canal)]
    assert stems == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    portada = dict(pa.leer_laminas(dir_canal))["1_portada"]
    assert portada["posicion"] == "1/4 · Portada" and portada["total_laminas"] == "4 LÁMINAS"


def test_una_tanda_sin_escribir_no_se_rinde(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    errores = pa.validar_tanda(dir_canal, AHORA, visiones)
    assert any("sin escribir" in e for e in errores)


def test_una_tanda_escrita_pasa_los_frenos(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert pa.validar_tanda(dir_canal, AHORA, visiones) == []


def test_el_pie_sin_direccion_se_detiene(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie="El dólar se mueve hoy entre dos niveles claros del día.")
    assert any("dirección" in e for e in pa.validar_tanda(dir_canal, AHORA, visiones))


def test_una_cifra_sin_respaldo_se_detiene(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie="El dólar tiene sesgo alcista y apunta a $951,00 hoy.")
    assert any("$951,00" in e for e in pa.validar_tanda(dir_canal, AHORA, visiones))


def test_la_frescura_vence_a_los_121_minutos(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert pa.validar_tanda(dir_canal, AHORA + timedelta(minutes=119), visiones) == []
    assert any("--refrescar" in e for e in pa.validar_tanda(dir_canal, AHORA + timedelta(minutes=121), visiones))


def test_una_vision_que_ya_no_esta_en_el_registro_se_detiene(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert any("registro" in e for e in pa.validar_tanda(dir_canal, AHORA, {}))


def test_el_pie_de_la_portada_lleva_cierre_y_aviso_y_es_estable(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    meta = pa.leer_meta(dir_canal)
    portada = dict(pa.leer_laminas(dir_canal))["1_portada"]
    msg = pa.mensaje_de(portada, meta)
    assert msg.startswith("El dólar mantiene un sesgo alcista")
    assert pa.AVISO_LEGAL in msg and msg.rstrip().endswith("1/4 · Portada")
    assert any(c in msg for c in pa.pc.CIERRES_ALERTA)
    assert pa.mensaje_de(portada, meta) == msg


def test_la_portada_de_avisos_no_cierra_con_el_analista():
    """Director, 2026-09-29: en Avisos ese cierre se lee ordinario."""
    assert pa.CIERRES_AVISOS and not any("analista" in c for c in pa.CIERRES_AVISOS)
    assert set(pa.CIERRES_AVISOS) < set(pa.pc.CIERRES_ALERTA)


def test_las_demas_laminas_llevan_solo_su_posicion(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    voz = dict(pa.leer_laminas(dir_canal))["2_voz"]
    assert pa.mensaje_de(voz, pa.leer_meta(dir_canal)) == "2/4 · La voz del banco"


def test_rendir_escribe_png_y_mensaje_por_lamina_y_usa_el_freno_del_despacho(tmp_path, monkeypatch):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    llamadas = []
    monkeypatch.setattr(pa.pc, "exigir_texto_editorial", lambda pares: llamadas.append(len(pares)))

    def render_falso(tokens, plantilla, salida, formato="horizontal"):
        assert "{{" not in story_render.build_html(tokens, plantilla)
        salida.write_bytes(b"png")
        return salida

    def grafico_falso(payload, destino):
        destino.write_bytes(b"png")
        return destino

    pngs = pa.rendir_tanda(dir_canal, AHORA, visiones, render=render_falso, grafico=grafico_falso)
    assert [p.name for p in pngs] == ["1_portada.png", "2_voz.png", "3_datos.png", "4_lectura.png"]
    assert all((dir_canal / f"{p.stem}_mensaje.txt").exists() for p in pngs)
    assert llamadas == [4]


def _render_que_guarda(vistos):
    def render(tokens, plantilla, salida, formato="horizontal"):
        vistos[salida.stem] = (tokens, story_render.build_html(tokens, plantilla))
        salida.write_bytes(b"png")
        return salida
    return render


def test_los_datos_llevan_el_grafico_tradingview_embebido(tmp_path):
    """El estándar de gráficos de alerta es el motor TradingView, no la línea SVG."""
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    pedidos, vistos = [], {}

    def grafico_falso(payload, destino):
        pedidos.append((payload["_procedencia"]["ticker"], destino.name))
        destino.write_bytes(b"png")
        return destino

    pa.rendir_tanda(dir_canal, AHORA, visiones, render=_render_que_guarda(vistos), grafico=grafico_falso)
    assert pedidos == [("USDCLP", "3_datos_grafico.png")]
    tokens, html = vistos["3_datos"]
    assert tokens["chart_png"].endswith("3_datos_grafico.png")
    assert 'id="img-alerta"' in html and "<svg" not in html.split("contenedor-grafico")[-1].split("footer")[0]
    # El payload en disco no cambia: el gráfico es de presentación.
    assert dict(pa.leer_laminas(dir_canal))["3_datos"].get("chart_png") is None


def test_sin_motor_tradingview_sale_el_svg_de_respaldo_y_lo_avisa(tmp_path, capsys):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    vistos = {}

    def roto(payload, destino):
        raise RuntimeError("Chromium no está")

    pa.rendir_tanda(dir_canal, AHORA, visiones, render=_render_que_guarda(vistos), grafico=roto)
    tokens, html = vistos["3_datos"]
    assert not tokens.get("chart_png") and 'id="img-alerta"' not in html
    assert "SVG de respaldo" in capsys.readouterr().err


def test_rendir_no_llama_al_render_si_los_frenos_fallan(tmp_path, monkeypatch):
    dir_canal, visiones = _tanda(tmp_path)
    # No se escribe nada: la tanda queda en `[[ESCRIBIR]]` y `validar_tanda` la detiene.
    llamadas = []

    def render_falso(tokens, plantilla, salida, formato="horizontal"):
        llamadas.append(1)
        salida.write_bytes(b"png")
        return salida

    with pytest.raises(SystemExit):
        pa.rendir_tanda(dir_canal, AHORA, visiones, render=render_falso)
    assert llamadas == []


def test_una_cifra_de_activos_extra_se_acepta_solo_si_se_declara(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie="El dólar tiene sesgo alcista y apunta a $951,00 hoy.")
    assert any("$951,00" in e for e in pa.validar_tanda(dir_canal, AHORA, visiones))
    extra = {"USDCLP": {"digits": 2, "price": 951.0}}
    assert pa.validar_tanda(dir_canal, AHORA, visiones, activos_extra=extra) == []


def test_reescribir_sin_voz_borra_las_laminas_viejas_y_renumera(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    for stem, _ in pa.leer_laminas(dir_canal):
        (dir_canal / f"{stem}.png").write_bytes(b"png")
        (dir_canal / f"{stem}_mensaje.txt").write_text("x", encoding="utf-8")

    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    pa.escribir_meta(dir_canal, meta)
    pa.escribir_laminas(dir_canal, "cita", laminas)

    restantes = sorted(p.name for p in dir_canal.iterdir())
    assert restantes == ["1_portada.json", "2_datos.json", "3_lectura.json", "_avisos.json"]
    laminas_nuevas = dict(pa.leer_laminas(dir_canal))
    assert laminas_nuevas["1_portada"]["posicion"] == "1/3 · Portada"
    assert laminas_nuevas["2_datos"]["posicion"] == "2/3 · Nuestros datos"
    assert laminas_nuevas["3_lectura"]["posicion"] == "3/3 · Nuestra lectura"


def test_tokens_de_traduce_titular_y_parrafo_por_plantilla(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    laminas = dict(pa.leer_laminas(dir_canal))
    assert "bajada" in pa.tokens_de(laminas["1_portada"])
    assert "remate" in pa.tokens_de(laminas["2_voz"])
    t = pa.tokens_de(laminas["4_lectura"])
    assert "titulo" in t and "conclusion" in t
    assert not any(k.startswith("_") for k in t)


# ---------------------------------------------------------------- preparar, refrescar, CLI


def _preparar(tmp_path, momento="avisos_manana", ahora=AHORA, visiones=None, lector=None, agenda=None):
    hist = tmp_path / "hist.json"
    if not hist.exists():
        hist.write_text("[]", encoding="utf-8")
    return pa.preparar(
        momento, ahora,
        lector=lector or (lambda t, a: lectura_falsa(t)),
        lector_agenda=lambda a: (agenda or AGENDA, []),
        visiones=visiones if visiones is not None else {"v": vision("v")},
        historial_ruta=hist, dir_base=tmp_path / "carrusel",
    ), hist


def test_feriado_no_prepara_nada(tmp_path):
    feriado = datetime(2026, 11, 26, 10, 30, tzinfo=pa.SANTIAGO)
    ruta, hist = _preparar(tmp_path, ahora=feriado)
    assert ruta is None and json.loads(hist.read_text(encoding="utf-8")) == []


def test_preparar_escribe_la_tanda_y_anota_el_historial(tmp_path):
    ruta, hist = _preparar(tmp_path)
    assert ruta.name == pa.CANAL and ruta.parent.name.endswith("_avisos_avisos_manana")
    assert (ruta / "_avisos.json").exists() and (ruta / "2_voz.json").exists()
    tipos = [e["tipo"] for e in json.loads(hist.read_text(encoding="utf-8"))]
    assert tipos == ["vision", "avisos"]


def test_preparar_dos_veces_el_mismo_momento_no_duplica(tmp_path):
    primera, hist = _preparar(tmp_path)
    antes = hist.read_text(encoding="utf-8")
    segunda, _ = _preparar(tmp_path, ahora=AHORA + timedelta(minutes=10))
    assert segunda == primera
    assert hist.read_text(encoding="utf-8") == antes
    # Review Focus 1: la segunda corrida no crea una carpeta de tanda nueva.
    carpetas = sorted(p.name for p in (tmp_path / "carrusel").iterdir())
    assert len(carpetas) == 1


def test_sin_vision_la_tanda_sale_marcada(tmp_path):
    ruta, _ = _preparar(tmp_path, visiones={})
    assert pa.leer_meta(ruta)["_falta_vision"] is True
    assert not (ruta / "2_voz.json").exists()


def test_una_falla_de_terminal_es_falla_de_datos(tmp_path):
    def roto(t, a):
        raise pa.LecturaFallidaError("MT5 no conectó")
    with pytest.raises(pa.LecturaFallidaError):
        _preparar(tmp_path, lector=roto)
    # Ni la tanda ni el historial se escriben: una falla de datos no deja
    # rastro a medio hacer.
    dir_base = tmp_path / "carrusel"
    assert not dir_base.exists() or not any(dir_base.iterdir())
    assert json.loads((tmp_path / "hist.json").read_text(encoding="utf-8")) == []


def test_el_balance_retoma_el_activo_y_la_voz_de_la_manana_sin_gastarla(tmp_path):
    _preparar(tmp_path, momento="avisos_manana")
    tarde = datetime(2026, 9, 29, 15, 30, tzinfo=pa.SANTIAGO)
    ruta, hist = _preparar(tmp_path, momento="avisos_tarde", ahora=tarde)
    meta = pa.leer_meta(ruta)
    assert meta["formato"] == "balance" and meta["activo"] == "USDCLP" and meta["vision"] == "v"
    visiones_gastadas = [e for e in json.loads(hist.read_text(encoding="utf-8")) if e["tipo"] == "vision"]
    assert len(visiones_gastadas) == 1


def test_el_balance_a_pedido_usa_el_activo_y_la_voz_del_director(tmp_path):
    """El día sin cita en la mañana el respaldo saldría sin voz: el director la elige."""
    hist = tmp_path / "hist.json"
    hist.write_text("[]", encoding="utf-8")
    tarde = datetime(2026, 9, 29, 15, 30, tzinfo=pa.SANTIAGO)
    visiones = {"c": vision("c", activo="BTCUSD", fecha="2026-09-28")}
    ruta = pa.preparar("avisos_tarde", tarde, lector=lambda t, a: lectura_falsa(t, nombre="Bitcoin"),
                       visiones=visiones, historial_ruta=hist, dir_base=tmp_path / "carrusel",
                       activo_pedido="BTCUSD", vision_pedida="c")
    meta = pa.leer_meta(ruta)
    assert meta["formato"] == "balance" and meta["activo"] == "BTCUSD" and meta["vision"] == "c"
    assert meta["_falta_vision"] is False
    # Es una voz nueva, no la de la mañana: se gasta.
    assert [e["tipo"] for e in json.loads(hist.read_text(encoding="utf-8"))] == ["vision", "avisos"]


@pytest.mark.parametrize("visiones, motivo", [
    ({}, "no está en el registro"),
    ({"c": vision("c", activo="XAUUSD")}, "es de XAUUSD"),
    ({"c": vision("c", activo="BTCUSD", fecha="2026-06-01")}, "no califica"),
])
def test_una_voz_pedida_que_no_sirve_se_dice_y_no_escribe(tmp_path, visiones, motivo):
    hist = tmp_path / "hist.json"
    hist.write_text("[]", encoding="utf-8")
    with pytest.raises(pa.VisionPedidaError, match=motivo):
        pa.preparar("avisos_tarde", AHORA, lector=lambda t, a: lectura_falsa(t), visiones=visiones,
                    historial_ruta=hist, dir_base=tmp_path / "carrusel",
                    activo_pedido="BTCUSD", vision_pedida="c")
    assert not (tmp_path / "carrusel").exists()


def test_la_agenda_del_lunes_no_lee_el_terminal(tmp_path):
    def no_llamar(t, a):
        raise AssertionError("la agenda no tiene activo")
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    ruta, _ = _preparar(tmp_path, momento="avisos_tarde", ahora=lunes, lector=no_llamar)
    assert [s for s, _ in pa.leer_laminas(ruta)] == ["1_portada", "2_semana", "3_lectura"]


def test_completar_vision_arma_la_voz_sin_cambiar_el_activo(tmp_path):
    # El catálogo real trae más candidatos que USDCLP (p. ej. BRENT.spot, alfabéticamente
    # antes): se marcan ya cubiertos hoy para que el único candidato libre sea USDCLP y el
    # test no dependa del orden real del catálogo, solo de que completar_vision no lo cambie.
    hist = tmp_path / "hist.json"
    hist.write_text(json.dumps([
        uso(AHORA.date().isoformat(), t) for t in ("BRENT.spot", "COPPER", "US100.spot", "WTI.spot", "XAUUSD")
    ]), encoding="utf-8")
    ruta, hist = _preparar(tmp_path, visiones={})
    visiones = {"n": vision("n", fecha="2026-09-27")}
    pa.completar_vision(ruta, "n", AHORA, visiones=visiones, historial_ruta=hist)
    meta = pa.leer_meta(ruta)
    assert meta["activo"] == "USDCLP" and meta["vision"] == "n" and meta["_falta_vision"] is False
    assert [s for s, _ in pa.leer_laminas(ruta)] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert any(e["tipo"] == "vision" and e["clave"] == "n" for e in json.loads(hist.read_text(encoding="utf-8")))


def test_completar_vision_de_otro_activo_se_niega(tmp_path):
    ruta, hist = _preparar(tmp_path, visiones={})
    with pytest.raises(SystemExit, match="activo"):
        pa.completar_vision(ruta, "x", AHORA, visiones={"x": vision("x", activo="XAUUSD")}, historial_ruta=hist)


def test_refrescar_conserva_texto_y_vision_y_mueve_la_hora(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    despues = AHORA + timedelta(minutes=40)
    pa.refrescar_tanda(ruta, despues, lector=lambda t, a: lectura_falsa(t, precio=936.80))
    meta = pa.leer_meta(ruta)
    laminas = dict(pa.leer_laminas(ruta))
    assert meta["leido_en"].startswith("2026-09-29T12:10") and meta["vision"] == "v"
    assert laminas["1_portada"]["pie"].startswith("El dólar mantiene")
    assert laminas["1_portada"]["dato_precio"].endswith("936,80")
    assert laminas["3_datos"]["precio_actual"] == "936,80"
    # Ruling 2 (pre-flight): el refresco de la portada conserva la procedencia.
    assert laminas["1_portada"]["_procedencia"]["ticker"] == "USDCLP"


def test_refrescar_con_divergencia_no_escribe_sin_reescribir(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    antes = (ruta / "3_datos.json").read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="reescribir"):
        pa.refrescar_tanda(ruta, AHORA, lector=lambda t, a: lectura_falsa(t, precio=945.0))
    assert (ruta / "3_datos.json").read_text(encoding="utf-8") == antes


def test_refrescar_con_reescribir_vacia_tambien_el_texto_de_las_listas(tmp_path):
    # Hallazgo de revisión: el reseteo solo tocaba los campos de nivel de
    # lámina; `claves[*].texto` (portada) y `puntos[*].texto`/`titulo_punto`
    # (lectura) quedaban con el texto escrito para la dirección que el
    # mercado ya invalidó.
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    pa.refrescar_tanda(ruta, AHORA, lector=lambda t, a: lectura_falsa(t, precio=945.0), reescribir=True)
    textos = pa.textos_de(pa.leer_laminas(ruta))
    assert textos  # hay campos que revisar
    assert all(valor == pa.MARCA for _, valor in textos)


def test_la_tabla_de_refresco_cubre_toda_plantilla_que_se_escribe():
    assert set(pa.REFRESCOS) == set(pa.PLANTILLAS)
    assert pa.REFRESCOS["avisos_lectura"] is None and pa.REFRESCOS["avisos_agenda"] is None


def test_pipeline_avisos_usa_los_tres_frenos_compartidos():
    import inspect
    fuente = inspect.getsource(pa.validar_tanda)
    for freno in ("validar_textos", "validar_cifras", "validar_frescura"):
        assert f"pl.{freno}" in fuente
    assert "exigir_texto_editorial" in inspect.getsource(pa.rendir_tanda)


def test_mensaje_preparar_dice_si_la_tanda_es_nueva_o_ya_existia(tmp_path):
    ruta, _ = _preparar(tmp_path)
    meta = pa.leer_meta(ruta)
    nuevo = pa._mensaje_preparar(ruta, meta, ya_existia=False)
    assert any(str(ruta.parent) in linea for linea in nuevo)
    assert not any("ya estaba preparada" in linea for linea in nuevo)

    repetido = pa._mensaje_preparar(ruta, meta, ya_existia=True)
    assert repetido == [f"La tanda de este momento ya estaba preparada: {ruta.parent}"]


# ---------------------------------------------------------------- revisión final del Hito 1


def test_el_balance_trae_la_vision_completada_en_la_manana(tmp_path):
    # Hallazgo 1: `completar_vision` solo anotaba la entrada "vision" y la
    # entrada "avisos" de la mañana seguía con `vision: None`, que es la única
    # que lee `activo_del_balance`: el balance salía sin voz.
    hist = tmp_path / "hist.json"
    hist.write_text(json.dumps([
        uso(AHORA.date().isoformat(), t) for t in ("BRENT.spot", "COPPER", "US100.spot", "WTI.spot", "XAUUSD")
    ]), encoding="utf-8")
    ruta, hist = _preparar(tmp_path, visiones={})
    visiones = {"n": vision("n", fecha="2026-09-27")}
    pa.completar_vision(ruta, "n", AHORA, visiones=visiones, historial_ruta=hist)
    usos = [e for e in json.loads(hist.read_text(encoding="utf-8"))
            if e["tipo"] == "avisos" and e["momento"] == "avisos_manana" and e["clave"] == "USDCLP"]
    assert [e["vision"] for e in usos] == ["n"]

    tarde = datetime(2026, 9, 29, 15, 30, tzinfo=pa.SANTIAGO)
    ruta_tarde, _ = _preparar(tmp_path, momento="avisos_tarde", ahora=tarde, visiones=visiones)
    meta = pa.leer_meta(ruta_tarde)
    # La regla de 14 días no la rechaza: es la misma visión del mismo día.
    assert meta["formato"] == "balance" and meta["activo"] == "USDCLP" and meta["vision"] == "n"
    assert (ruta_tarde / "2_voz.json").exists()


def test_reescribir_renueva_los_activos_de_preparacion(tmp_path):
    # Hallazgo 2: tras `--refrescar --reescribir` los textos vuelven a
    # escribirse contra la lectura nueva, así que la lectura de preparación
    # también tiene que ser la nueva.
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    pa.refrescar_tanda(ruta, AHORA, lector=lambda t, a: lectura_falsa(t, precio=945.0), reescribir=True)
    meta = pa.leer_meta(ruta)
    assert meta["activos_preparacion"] == meta["activos"]
    assert meta["activos_preparacion"]["USDCLP"]["price"] == 945.0


def test_refrescar_sin_divergencia_conserva_los_activos_de_preparacion(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    pa.refrescar_tanda(ruta, AHORA + timedelta(minutes=40), lector=lambda t, a: lectura_falsa(t, precio=936.80))
    meta = pa.leer_meta(ruta)
    assert meta["activos_preparacion"]["USDCLP"]["price"] == 936.32
    assert meta["activos"]["USDCLP"]["price"] == 936.80


def test_los_cierres_de_agenda_no_hablan_de_niveles_ni_precios():
    # Hallazgo 3: la agenda cerraba con CIERRES_ALERTA, que hablan de bordes y
    # del precio que ese carrusel no tiene.
    import re
    assert len(pa.CIERRES_AGENDA) >= 3
    for cierre in pa.CIERRES_AGENDA:
        bajo = cierre.lower()
        for palabra in ("nivel", "borde", "precio"):
            assert palabra not in bajo, cierre
        assert not re.search(r"\d", cierre), cierre
        assert "—" not in cierre and "–" not in cierre, cierre


def test_la_agenda_cierra_con_un_cierre_de_agenda_estable(tmp_path):
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    ruta, _ = _preparar(tmp_path, momento="avisos_tarde", ahora=lunes)
    _escribir_todo(ruta)
    meta = pa.leer_meta(ruta)
    portada = dict(pa.leer_laminas(ruta))["1_portada"]
    msg = pa.mensaje_de(portada, meta)
    assert any(c in msg for c in pa.CIERRES_AGENDA)
    assert not any(c in msg for c in pa.pc.CIERRES_ALERTA)
    assert pa.mensaje_de(portada, meta) == msg


@pytest.mark.parametrize("pie", [
    "El dólar tiene sesgo alcista y cotiza en $936,32 esta mañana.",
    "El dólar tiene sesgo alcista y cotiza en 936,32 esta mañana.",
])
def test_el_texto_que_cita_el_precio_actual_se_detiene(tmp_path, pie):
    # Hallazgo 5: el despacho acepta los niveles de preparación pero no su
    # precio, así que un texto con el spot pasaba --validar y se frenaba al
    # primer tick.
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie=pie)
    errores = pa.validar_tanda(dir_canal, AHORA, visiones)
    assert any("936,32" in e and "precio actual" in e for e in errores), errores


def test_el_texto_que_cita_el_soporte_publicado_pasa(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    fila = pa.leer_meta(dir_canal)["activos"]["USDCLP"]
    soporte = pa._fmt(fila["soporte_publicado"], fila["digits"])
    _escribir_todo(dir_canal, pie=f"El dólar tiene sesgo alcista mientras respete ${soporte}.")
    assert pa.validar_tanda(dir_canal, AHORA, visiones) == []


DISCLAIMER_TEMATICO = "Información con fines educativos y de análisis técnico cuantitativo. No constituye asesoría financiera."


def test_la_lamina_de_datos_lleva_el_aviso_legal_de_avisos():
    # Hallazgo 6: alerta.html traía su propio aviso fijo; la lámina de datos
    # tiene que mostrar el aviso legal literal de Avisos.
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    datos = {**laminas["datos"], "titular": "Titular", "parrafo": "Párrafo"}
    assert datos["disclaimer"] == pa.AVISO_LEGAL
    html = story_render.build_html(pa.tokens_de(datos), pa.DIR_PLANTILLAS / "alerta.html")
    assert pa.AVISO_LEGAL in html and DISCLAIMER_TEMATICO not in html


def test_la_alerta_tematica_conserva_su_aviso_por_defecto():
    from story_grafico import enriquecer
    fixture = json.loads((RAIZ / "tests/fixtures/stories/payloads/alerta.json").read_text(encoding="utf-8"))
    assert "disclaimer" not in fixture
    html = story_render.build_html(enriquecer(fixture), pa.DIR_PLANTILLAS / "alerta.html")
    assert DISCLAIMER_TEMATICO in html


def test_el_aviso_de_la_alerta_mide_al_menos_20px():
    import re
    css = (pa.DIR_PLANTILLAS / "alerta.html").read_text(encoding="utf-8")
    regla = re.search(r"\.footer-disclaimer\s*\{([^}]*)\}", css).group(1)
    assert int(re.search(r"font-size:\s*(\d+)px", regla).group(1)) >= 20
