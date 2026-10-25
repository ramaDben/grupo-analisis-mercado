"""El HTML de la pieza semanal: análisis firmado, panel del ejecutivo y correo."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import comercial as cm  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import oportunidad as op  # noqa: E402
from analista import oportunidad_html as oh  # noqa: E402

HOY = date(2026, 10, 12)
EJECUTIVO = {"nombre": "Camila Rojas", "cargo": "Ejecutiva comercial", "contacto": "+56 9 1111 2222"}


# La lectura de la fixture es bajista: UBS la respalda y Goldman Sachs (alcista) la contradice.
UBS_A_FAVOR = {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-13",
               "url": "https://www.bloomberg.com/markets/oro-ubs-2026", "postura": "bajista",
               "tesis": "UBS anticipa una consolidación a la baja en el oro.", "verificacion": "ok"}
CON_BANCO = [*fx.FUENTES_EJEMPLO, UBS_A_FAVOR]


def _pieza(tmp_path):
    return fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=CON_BANCO)


def test_el_analisis_va_firmado_y_la_simulacion_rotulada(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Departamento de Estudios" in html
    assert "Objetivo de la simulación (1:3)" in html
    assert "Simulación realizada por Camila Rojas" in html


def test_el_simulador_incrustado_es_el_del_archivo(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert op.SIMULADOR_JS.read_text(encoding="utf-8").strip() in html


def test_los_datos_incrustados_traen_contrato_y_escenario(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    datos = json.loads(crudo)
    assert datos["activos"][0]["escenario"]["objetivo"] == 4062.72
    assert datos["activos"][0]["contrato"]["vol_min"] == 0.01


def test_un_activo_sin_simulacion_muestra_el_motivo_y_no_tiene_inputs(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"]["motivo"] = "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Sin simulación en este análisis: el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop" in html
    bloque = html.split('data-ticker="XAUUSD"')[1].split("</section>")[0]
    assert 'name="perdida"' not in bloque


def test_lo_que_lee_el_cliente_no_dice_oportunidad_ni_recomendacion(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = re.findall(r'<template class="correo-activo"[^>]*>(.*?)</template>', html, re.S)
    assert correo
    for bloque in correo:
        assert "oportunidad" not in bloque.lower() and "recomendaci" not in bloque.lower()
        assert "—" not in bloque and "–" not in bloque
    assert "un escenario puede cumplirse o invalidarse" in html


def test_un_texto_invalido_no_arma_la_pieza(tmp_path):
    p = _pieza(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = es.MARCA
    with pytest.raises(oh.InformeInvalido):
        oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)





def test_un_activo_sin_simulacion_igual_entra_al_correo(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"]["motivo"] = "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split("</section>")[0]
    assert 'name="incluir"' in bloque and 'name="perdida"' not in bloque
    datos = json.loads(re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1))
    assert datos["activos"][0]["motivo"] == "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"
    assert "Sin simulación en este análisis: " in html


def test_sin_contrato_el_cliente_ve_los_niveles_y_el_ejecutivo_el_aviso(tmp_path):
    """Sin contrato falta el volumen, no la simulación: el correo lleva los niveles sin montos."""
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split("</section>")[0]
    assert "No tenemos los datos de la cuenta para calcular el tamaño de la operación" in bloque
    assert 'name="perdida"' not in bloque and 'name="incluir"' in bloque
    correo = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert "Sin simulación" not in correo and "Simulación realizada por Camila Rojas" in correo
    assert "sim-perdida" not in correo


def test_una_simulacion_condicional_dice_cuando_se_activa(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"].update(entrada_pendiente=True, condicion="quiebre")
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert "Se activa si una vela de 4 horas cierra bajo 4.186,17." in correo





def test_el_json_escapa_cierre_de_script_y_la_pagina_no_trae_guiones_largos(tmp_path):
    p = _pieza(tmp_path)
    ejecutivo = {**EJECUTIVO, "cargo": "Ejecutiva </script> comercial"}
    html = oh.armar(p, tmp_path, ejecutivo, fx.AUTOR, HOY)
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(crudo)["cargo"] == "Ejecutiva </script> comercial"
    assert "—" not in html and "–" not in html and "oportunidad" not in html.lower()


def test_la_lamina_de_un_ticker_con_punto_se_puede_descargar(tmp_path):
    """El WTI (`WTI.spot`) sale todas las semanas: su lámina se rinde como `lamina_wti_spot.png`."""
    html = oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, wti=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="WTI.spot"')[1].split("</section>")[0]
    assert 'download="lamina_wti_spot.png"' in bloque


def test_el_correo_lleva_la_maqueta_del_prototipo(tmp_path):
    """Logo de GI arriba, cuadros rojo y verde del mismo tamaño y la firma del ejecutivo (director, 2026-10-18)."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', html, re.S).group(1)
    assert 'alt="Grupo Inteligencia"' in marco and "<!--ACTIVOS-->" in marco and "<!--WA-->" in marco
    assert "Camila Rojas" in marco and "Departamento de Inversiones · GI" in marco
    c = oh.paleta_correo(oh.paleta())
    bloque = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert f'border:2px solid {c["baja"]}' in bloque and f'border:2px solid {c["sube"]}' in bloque
    assert 'class="sim-perdida"' in bloque and 'class="sim-ganancia"' in bloque
    assert "var(" not in marco + bloque and "rgba(" not in marco + bloque


def test_la_firma_lleva_al_ejecutivo_en_grande_y_debajo_al_analista(tmp_path):
    """El ejecutivo firma en grande al pie; Benjamín firma en cabecera hero (Decisión 5)."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', html, re.S).group(1)
    firma = marco[marco.index("<!--WA-->"):]
    assert 'font-size:26px' in firma
    assert "Camila Rojas" in firma
    assert "Departamento de Inversiones · GI" in firma
    assert "Benjamín Bravo Soza" not in firma
    assert "Benjamín Ignacio" not in firma
    assert "Te lo envía" not in marco
    correo = _correo(html)
    assert "Realizado por Benjamín Bravo Soza · Departamento de Estudios GI" in correo


def test_el_analisis_va_rotulado_con_su_autor_como_la_simulacion_con_el_ejecutivo(tmp_path):
    correo = _correo(_html(tmp_path))
    assert "Análisis técnico del Oro" in correo
    assert "Realizado por Benjamín Bravo Soza · Departamento de Estudios GI" in correo
    assert "Benjamín Ignacio" not in correo
    assert correo.index("Análisis técnico del Oro") < correo.index("Simulación realizada por Camila Rojas")


def test_el_titulo_del_analisis_lleva_el_articulo_del_activo():
    assert oh._titulo_analisis("Oro") == "Análisis técnico del Oro"
    assert oh._titulo_analisis("Plata") == "Análisis técnico de la Plata"
    assert oh._titulo_analisis("Bitcoin") == "Análisis técnico de Bitcoin"


def test_el_cuerpo_es_claro_y_solo_la_apertura_del_activo_es_oscura(tmp_path):
    """Outlook invierte los fondos oscuros: el cuerpo va sobre blanco y la apertura del activo es el único bloque oscuro."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    c = oh.paleta_correo(oh.paleta())
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', html, re.S).group(1)
    assert f'bgcolor="{c["fondo_alt"]}"' in marco and c["fondo_alt"] == "#FFFFFF"
    bloque = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert bloque.count(f'bgcolor="{c["hero"]}"') == 1
    assert "Precio de referencia" in bloque and "Escenario del análisis" not in bloque


def test_la_ficha_del_correo_no_lleva_el_boton_si_no_hay_numero(tmp_path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    ruta = tmp_path / "p.html"
    ruta.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(ruta.as_uri())
        v = pg.locator("#vista-correo")
        assert v.locator("a[href^='https://wa.me/']").count() == 0
        pg.fill("#whatsapp", "+56 9 8765 4321")
        enlace = v.locator("a[href^='https://wa.me/']")
        assert enlace.count() == 1
        href = enlace.get_attribute("href")
        assert href.startswith("https://wa.me/56987654321?text=") and "Oro" in __import__("urllib.parse").parse.unquote(href)
        pg.fill("#whatsapp", "987654321")  # un móvil chileno sin el 56 también sirve
        assert v.locator("a[href^='https://wa.me/56987654321']").count() == 1
        pg.fill("#whatsapp", "12345")  # no es un número: sin botón y con aviso
        assert v.locator("a[href^='https://wa.me/']").count() == 0
        assert "no parece válido" in pg.locator("#estado").inner_text()
        pg.fill("#whatsapp", "")
        assert v.locator("a[href^='https://wa.me/']").count() == 0
        b.close()


def test_el_grafico_del_dolar_sale_solo_si_el_dolar_es_un_driver_medido(tmp_path):
    con = _correo(oh.armar(fx.pieza_oportunidad(tmp_path, dolar=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Gráfico del Dollar Index (DXY)" in con
    assert len(re.findall(r'<img src="data:image/png;base64,[^"]+" width="558"', con)) == 3  # oro, dólar y calendario
    (tmp_path / "sin").mkdir()
    sin = _correo(oh.armar(fx.pieza_oportunidad(tmp_path / "sin"), tmp_path / "sin", EJECUTIVO, fx.AUTOR, HOY))
    assert "Gráfico del Dollar Index" not in sin


def test_con_publicador_el_correo_lleva_urls_y_ninguna_imagen_embebida(tmp_path):
    pedidas: list[str] = []

    def publicar(ruta):
        pedidas.append(ruta.name)
        return f"https://ejemplo.test/correos/{ruta.name}"

    html = oh.armar(fx.pieza_oportunidad(tmp_path, dolar=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY, publicar)
    correo = _correo(html)
    assert "data:image" not in correo
    assert len(re.findall(r'<img src="https://ejemplo\.test/correos/[^"]+"', correo)) == 4  # logo del hero, oro, dólar y calendario
    assert "grafico_usdidx.png" in pedidas and "grafico_xauusd.png" in pedidas
    # La página que ve el ejecutivo conserva sus imágenes embebidas: se abre sin red.
    assert "data:image" in html.split('id="correo-root"')[0]


def test_los_drivers_del_correo_van_en_tabla(tmp_path):
    correo = _correo(_html(tmp_path))
    assert "Efecto en el activo" in correo and "<th " in correo
    assert "Dollar Index (DXY)" in correo and "101,560" in correo


def test_en_el_correo_un_activo_sin_simulacion_muestra_el_motivo_sin_cuadros(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"]["motivo"] = "el precio no muestra una dirección clara"
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert "el precio no muestra una dirección clara" in bloque
    assert "sim-perdida" not in bloque


def test_los_cuadros_parten_con_capital_y_perdida_por_defecto_y_el_saludo_es_editable(tmp_path):
    """El comercial no tiene que escribir nada: 2 millones de capital, 100.000 de pérdida y nombre opcional."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split("</section>")[0]
    assert 'name="perdida" min="0" step="1000" value="100000"' in bloque
    assert 'name="capital" min="0" step="10000" value="2000000"' in bloque
    assert 'id="cliente"' in html and 'class="saludo-cliente">Estimado(a):</span>' in html


def test_el_correo_abre_como_el_de_mas_que_uf_con_la_pregunta_y_luego_el_saludo(tmp_path):
    """Director, 2026-10-19: la apertura sigue a Más que UF (cabecera, banda con la pregunta, saludo y texto)."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = html.split('id="correo-root"')[1]
    assert correo.index("<!--TITULO-->") < correo.index('class="saludo-cliente"') < correo.index("<!--ACTIVOS-->")
    assert "En línea con lo que conversamos por teléfono" in correo
    assert "Para continuar nuestra conversación, te comparto el mapa de trabajo" in correo
    assert "Quisiera saber si pudiste revisar" not in correo  # no se le cobra la tarea al prospecto


def test_el_titulo_del_correo_cuenta_los_activos_incluidos_y_no_dice_igual_para_todos(tmp_path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "igual para todos" not in html and "lectura general" not in html
    ruta = tmp_path / "p.html"
    ruta.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(ruta.as_uri())
        v = pg.locator("#vista-correo")
        assert "¿Pudiste revisar la información que te envié?" in v.inner_text()
        pg.locator("[name=incluir]").first.uncheck()
        assert "Marca al menos un activo" in v.inner_text()
        pg.locator("[name=incluir]").first.check()
        pg.fill("#cliente", "Estimado Sr. Pérez")
        assert "Estimado Sr. Pérez:" in v.inner_text()
        b.close()


def test_el_autor_nunca_firma_la_simulacion(tmp_path):
    """Si pide el propio autor, la simulación queda con un campo por completar y no con su nombre."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    director = {"nombre": fx.AUTOR.nombre, "cargo": fx.AUTOR.cargo, "contacto": ""}
    html = oh.armar(_pieza(tmp_path), tmp_path, director, fx.AUTOR, HOY)
    assert "Simulación realizada por [Tu nombre]" in html
    assert "Simulación realizada por " + fx.AUTOR.nombre not in html
    ruta = tmp_path / "p.html"
    ruta.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(ruta.as_uri())
        pg.fill("#ejecutivo", fx.AUTOR.nombre.upper())  # escribir el nombre del autor no sirve
        pg.click("#copiar-correo")
        assert "Escribe tu nombre" in pg.locator("#estado").inner_text()
        pg.fill("#ejecutivo", "Pedro Soto")
        assert "Pedro Soto" in pg.locator("#vista-correo").inner_text()
        b.close()


def test_el_grafico_del_correo_es_una_imagen_con_ancho_y_alto(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert re.search(r'<img src="data:image/png;base64,[^"]+" width="558" height="\d+"', correo)


def _html(tmp_path, **kw):
    kw.setdefault("fuentes", CON_BANCO)
    return oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, **kw), tmp_path, EJECUTIVO, fx.AUTOR, HOY)


def test_la_ficha_tiene_las_tres_secciones(tmp_path):
    h = _html(tmp_path)
    for titulo in ("Lectura técnica", "Fundamental", "Voces de bancos y prensa"):
        assert titulo in h


def test_cada_voz_lleva_entidad_medio_fecha_y_enlace(tmp_path):
    h = _html(tmp_path)
    assert "Goldman Sachs" in h and "Reuters" in h and "2026-10-14" in h
    assert 'href="https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/"' in h and 'rel="noopener' in h


def test_la_discrepancia_con_los_bancos_se_marca(tmp_path):
    h = _html(tmp_path)  # lectura bajista del oro, Goldman alcista
    assert "Discrepa de nuestra lectura" in h and "la nuestra es la que manda" in h.lower()


def test_una_voz_que_coincide_no_lleva_marca_de_discrepancia(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], postura="bajista")
    assert "Discrepa de nuestra lectura" not in _html(tmp_path, fuentes=[f])


def test_una_url_sin_verificar_se_dice(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], verificacion="sin_verificar")
    assert "sin verificar" in _html(tmp_path, fuentes=[f]).lower()


def test_sin_fuentes_avisa_y_no_rellena(tmp_path):
    h = _html(tmp_path, fuentes=[])
    assert "Sin voces de bancos o prensa atingentes esta vez" in h and "Goldman Sachs" not in h


def test_el_html_no_deja_pasar_marcado_de_las_fuentes(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], tesis='Ve el oro <img src=x onerror=alert(1)> alcista.')
    with pytest.raises(oh.InformeInvalido):  # el esquema lo frena antes de armar; la ficha además escapa
        _html(tmp_path, fuentes=[f])


def test_no_hay_bloque_de_revision_en_mt5(tmp_path):
    h = _html(tmp_path)
    assert "Para revisar con tu cliente" not in h
    assert "revision-mt5" not in h


def test_la_simulacion_se_rotula_como_ejemplo_ilustrativo(tmp_path):
    h = _html(tmp_path)
    assert h.count(cm.ROTULO_ILUSTRATIVO) >= 2  # panel del ejecutivo y correo


def test_el_correo_no_invita_a_operar(tmp_path):
    h = _html(tmp_path).lower()
    assert "evaluar tus próximas operaciones" not in h and "se puede operar" not in h
    assert "para operar" not in h


def test_el_archivo_lleva_el_activo_y_el_ejecutivo(tmp_path):
    ruta = oh.guardar(fx.pieza_oportunidad(tmp_path, laminas=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert ruta.name.startswith("analisis_xauusd_") and "oportunidad" not in ruta.name


def test_la_cabecera_muestra_hasta_cuando_vale(tmp_path):
    assert "lunes 19/10" in _html(tmp_path)


def test_la_ficha_no_habla_de_la_semana_con_vigencia_de_7_dias(tmp_path):
    """La vigencia es de 7 días corridos, no de una semana calendario: los rótulos hablan del análisis."""
    p = _pieza(tmp_path)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    for viejo in ("Escenario de la semana", "Análisis técnico de la semana", "Sin simulación esta semana",
                  "de esta semana", "en MT5 esta semana"):
        assert viejo not in html, viejo
    assert "Los tres escenarios" in html and "Seguimiento de nuestra llamada" in html
    p["datos"]["activos"][0]["escenario"]["motivo"] = "sin nivel claro"
    p["huella"] = es._huella(p)
    assert "Sin simulación esta semana" not in oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)


# ───────────────────────────────────────────── texto concreto (spec 2026-10-17 §6)


def _correo(html):
    return re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)


def test_la_ficha_trae_la_tabla_de_hechos(tmp_path):
    h = _html(tmp_path)
    assert "Lo que pasa hoy con sus drivers" in h and "101,560" in h and "viernes 09/10" in h
    assert "bajó 0,288 puntos en 5 sesiones" in h and "va en contra de nuestra lectura" in h
    assert "bajó 14 pb en 5 sesiones" in h  # las tasas no repiten la unidad


def test_el_correo_no_imprime_pb_ni_tips_sin_explicar_ni_sin_dato(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True)
    p["datos"]["hechos"][1]["sentido"] = "sin_dato"
    p["huella"] = es._huella(p)
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert " pb" not in correo and "sin dato" not in correo
    assert "bonos del Tesoro que se ajustan por inflación (TIPS)" in correo
    assert "Dollar Index (DXY)" in correo


def test_el_correo_dice_puntos_base_y_fecha_los_drivers(tmp_path):
    correo = _correo(_html(tmp_path))
    assert "bajó 14 puntos base en 5 sesiones" in correo and " pb" not in correo
    assert "Lo que mueve el precio al viernes 09/10" in correo and "Lo que pasa hoy" not in correo


def test_la_ficha_trae_los_dias_clave_con_imagen_tabla_y_enlace(tmp_path):
    h = _html(tmp_path)
    assert "Días clave del lunes 12/10 al lunes 19/10" in h
    assert "El día clave es el miércoles 14/10" in h and 'alt="Calendario económico del lunes 12/10' in h
    assert "Índice de precios al consumidor (IPC)" in h and "el oro tiende a bajar" in h
    assert 'href="https://es.investing.com/economic-calendar/"' in h


def test_una_ventana_vacia_dice_sus_fechas_en_la_ficha_y_en_el_correo(tmp_path):
    h = _html(tmp_path, agenda="vacia")
    frase = "Sin datos de alto impacto entre el lunes 12/10 y el lunes 19/10"
    assert h.count(frase) >= 2 and frase in _correo(h)  # en la ficha y en el correo


def test_sin_calendario_avisa_al_ejecutivo_y_el_correo_lo_omite(tmp_path):
    h = _html(tmp_path, agenda="sin_calendario")
    assert "No pude leer el calendario económico" in h
    assert "No pude leer" not in _correo(h) and "Días clave" not in _correo(h)


def _parcial(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True)
    p["datos"]["agenda"].update(parcial=True, cubierto_hasta="miércoles 14/10")
    p["huella"] = es._huella(p)
    return oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)


def test_una_agenda_parcial_avisa_en_la_ficha_y_el_correo_no_declara_mas_de_lo_cubierto(tmp_path):
    h = _parcial(tmp_path)
    assert "El calendario respondió a medias" in h
    correo = _correo(h)
    assert "Días clave hasta el miércoles 14/10" in correo and "hasta el lunes 19/10" not in correo


def test_el_correo_lleva_hechos_dias_clave_imagen_y_bancos_con_enlace(tmp_path):
    correo = _correo(_html(tmp_path))
    assert "Lo que mueve el precio al" in correo and "101,560" in correo and "Juega a favor del alza del oro" in correo
    assert "Días clave hasta el lunes 19/10" in correo and "El día clave es el miércoles 14/10" in correo
    assert len(re.findall(r'<img src="data:image/png;base64,[^"]+" width="558" height="\d+"', correo)) == 2
    assert "Qué dice la banca" in correo and "UBS" in correo and "13/10/2026" in correo
    assert 'href="https://www.bloomberg.com/markets/oro-ubs-2026"' in correo
    assert "Coincide con nuestra lectura bajista" in correo
    # Director, 2026-10-19: el banco siempre respalda nuestra lectura; Goldman (alcista) no se muestra.
    assert "Goldman Sachs" not in correo and "ve distinto" not in correo
    assert "var(" not in correo and "rgba(" not in correo and "—" not in correo


def test_una_pieza_anterior_se_rearma_sin_los_bloques_nuevos(tmp_path):
    """Un análisis creado antes del 2026-10-17 se reusa hasta 7 días: no puede romperse."""
    h = oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, legado=True, fuentes=[]), tmp_path, EJECUTIVO,
                 fx.AUTOR, HOY)
    assert "Lo que pasa hoy" not in h and "Días clave" not in h and "Qué dice la banca" not in h


# ───────────────────────────────────────────── tests exhaustivos correo editorial (2026-10-19)


def test_titular_base_armado_por_codigo(tmp_path):
    """Valida fórmula Alt. 3 con cifras de pieza.json y artículo del activo."""
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]
    tit = oh.titular_base(a)
    assert tit == "El oro mantiene su tendencia bajista: mientras respete su línea, la lectura sigue en pie"

    a_alcista = dict(a, nombre="Plata", lectura=dict(a["lectura"], direccion="ALCISTA"))
    tit_alcista = oh.titular_base(a_alcista)
    assert tit_alcista == "La plata mantiene su tendencia alcista: mientras respete su línea, la lectura sigue en pie"

    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = _correo(html)
    assert tit in correo


def test_titular_variante_choque_de_bancos(tmp_path):
    """Valida fórmula Alt. 2 (choque de bancos) con exactamente 1 a favor y 1 en contra con un precio inequívoco."""
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]

    fuentes_exito = [
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-14", "postura": "bajista",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026", "tesis": "Ve caída hacia 3.900"},
        {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14", "postura": "alcista",
         "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/", "tesis": "Proyecta avance a 4.300"},
    ]
    tit_var = oh.titular_variante(a, fuentes_exito)
    assert tit_var == "Entre los 3.900 de UBS y los 4.300 de Goldman Sachs: el gráfico del oro fija su frontera en 4.227,32"

    fuentes_decimales = [
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-14", "postura": "bajista",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026", "tesis": "Ve caída hacia 3.950,50"},
        {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14", "postura": "alcista",
         "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/", "tesis": "Proyecta avance a 4.250,50"},
    ]
    tit_dec = oh.titular_variante(a, fuentes_decimales)
    assert "Entre los 3.950,50 de UBS y los 4.250,50 de Goldman Sachs:" in tit_dec

    fuentes_sin_num = [
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-14", "postura": "bajista",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026", "tesis": "Ve retroceso en el activo sin fijar meta"},
        {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14", "postura": "alcista",
         "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/", "tesis": "Proyecta avance a 4.300"},
    ]
    assert oh.titular_variante(a, fuentes_sin_num) == oh.titular_base(a)

    fuentes_mult_num = [
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-14", "postura": "bajista",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026", "tesis": "Ve rango entre 3.800 y 3.900"},
        {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14", "postura": "alcista",
         "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/", "tesis": "Proyecta avance a 4.300"},
    ]
    assert oh.titular_variante(a, fuentes_mult_num) == oh.titular_base(a)

    fuentes_un_banco = [fuentes_exito[0]]
    assert oh.titular_variante(a, fuentes_un_banco) == oh.titular_base(a)

    assert oh.titular_correo(a, fuentes_exito, variante=True) == tit_var
    assert oh.titular_correo(a, fuentes_exito, variante=False) == oh.titular_base(a)


def test_bancos_correo_solo_uno_y_a_favor_de_la_lectura(tmp_path):
    """Con 3 fuentes (un organismo, un banco que discrepa y uno que coincide), el correo cita solo el que coincide."""
    fuentes_tres = [
        {"entidad": "World Gold Council", "medio": "Reuters", "fecha": "2026-10-15",
         "url": "https://www.reuters.com/markets/wgc-oro-2026", "postura": "alcista",
         "tesis": "Demanda institucional récord sostiene el mercado físico."},
        {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14",
         "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/",
         "postura": "alcista", "tesis": "Goldman Sachs proyecta avance hacia 4.300."},
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-13",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026",
         "postura": "bajista", "tesis": "UBS anticipa consolidación bajista hacia 3.900."},
    ]
    # Sin sello de directa (pieza anterior al spec 2026-10-20) el organismo no sale; con sello sale como noticia directa.
    p = fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=fuentes_tres, sello=False)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = _correo(html)

    assert "World Gold Council" not in correo
    assert "Goldman Sachs" not in correo
    assert "UBS" in correo

    assert "⬇️ Coincide con nuestra lectura bajista" in correo
    assert "En contra" not in correo

    assert "#FF0000" not in correo and "#ff0000" not in correo
    assert "#00FF00" not in correo and "#00ff00" not in correo


def test_banco_unico_sin_tarjeta_vacia_ni_aviso(tmp_path):
    """Verifica que con un solo banco calificado, se renderiza únicamente esa tarjeta al 100% sin tarjetas vacías ni aviso."""
    fuentes_unica = [
        {"entidad": "UBS", "medio": "Bloomberg", "fecha": "2026-10-14",
         "url": "https://www.bloomberg.com/markets/oro-ubs-2026",
         "postura": "bajista", "tesis": "UBS anticipa consolidación bajista hacia 3.900."}
    ]
    p = fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=fuentes_unica)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = _correo(html)

    assert "UBS" in correo
    assert 'width="100%"' in correo
    assert "tarjeta vacía" not in correo.lower()
    assert "falta" not in correo.lower()
    assert "sin banco" not in correo.lower()
    assert "sin contraparte" not in correo.lower()


def test_drivers_correo_exactamente_dos_y_sintesis(tmp_path):
    """Verifica que la tabla de drivers incluye exactamente 2 factores y el recuadro de síntesis de dominancia."""
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    p["datos"]["hechos"].append({
        "id": "wti",
        "driver": "Petróleo WTI",
        "nivel": "72,50 USD/barril",
        "fecha": "viernes 09/10",
        "fuente": "MT5",
        "cambio_5d": "-1,20",
        "sentido": "bajó",
        "unidad_cambio": "USD",
        "efecto": "presiona a la baja los costos energéticos",
        "con_la_lectura": "a favor de nuestra lectura",
    })
    # El texto cita solo los 2 drivers que la tabla muestra (regla del director: solo 2 drivers).
    p["editorial"]["contexto"]["XAUUSD"] = p["editorial"]["contexto"]["XAUUSD"].replace(
        "la tasa real a 10 años quedó en 2,78 por ciento", "el petróleo WTI quedó en 72,50 USD/barril")
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = _correo(html)

    seleccionados, sintesis = oh.seleccionar_drivers_correo(p["datos"]["hechos"])
    assert len(seleccionados) == 2
    assert "Qué pesa más hoy:" in correo
    assert sintesis in correo


def test_saludo_con_marcador_editable(tmp_path):
    """Verifica el saludo editable y el marcador [Nombre del cliente] en la pieza."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert 'id="cliente"' in html
    assert 'class="saludo-cliente"' in html
    assert "Nombre del cliente" in html
    correo_html = html.split('id="correo-root"')[1]
    assert '<span class="saludo-cliente">Estimado(a):</span>' in correo_html

    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    ruta = tmp_path / "p.html"
    ruta.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(ruta.as_uri())
        v = pg.locator("#vista-correo")
        assert "Estimado(a):" in v.inner_text()
        pg.fill("#cliente", "Estimado Carlos")
        assert "Estimado Carlos:" in v.inner_text()
        b.close()


def test_preheader_oculto_y_asunto_sugerido(tmp_path):
    """Verifica asunto_sugerido, preheader_sugerido y el bloque preheader oculto en el HTML."""
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]
    ed = p["editorial"]
    d = p["datos"]

    asunto = oh.asunto_sugerido(a, ed.get("fuentes"))
    assert asunto == "El oro en 4.186,17: el nivel clave que vigila la mesa"  # una sola cifra

    preheader = oh.preheader_sugerido(a, ed.get("fuentes"), d)
    assert preheader == "Nuestra lectura bajista en 4H, el respaldo de UBS y los dos factores que mueven la sesión de hoy."

    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert 'display:none;font-size:1px;color:#EEF2F1;line-height:1px;' in html
    assert '&zwnj;&nbsp;' in html
    assert preheader in html
    assert "Asunto sugerido:" in html
    assert "Preheader:" in html



def test_el_contexto_no_puede_citar_un_tercer_driver(tmp_path):
    """Con 3 hechos citables, el texto que nombra el tercero se rechaza y dice cuáles son los 2 válidos."""
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    p["datos"]["hechos"].append({
        "id": "wti", "driver": "Petróleo WTI", "nivel": "72,50 USD/barril", "fecha": "viernes 09/10",
        "fuente": "MT5", "cambio_5d": "-1,20", "sentido": "bajó", "unidad_cambio": "USD",
        "efecto": "presiona a la baja los costos energéticos", "con_la_lectura": "a favor de nuestra lectura",
    })
    p["editorial"]["contexto"]["XAUUSD"] += " El petróleo WTI quedó en 72,50 USD/barril."
    p["huella"] = es._huella(p)
    errs = es._errores_de_desarrollo(p)
    assert any("solo 2 drivers" in e and "tasa_real" in e for e in errs)


def _con_anterior(tmp_path, direccion="ALCISTA", motivo=""):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    p["datos"]["anterior"] = {"direccion": direccion, "fecha": "17/10", "motivo": motivo}
    p["huella"] = es._huella(p)
    return _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))


def test_si_la_lectura_cambio_el_correo_cuenta_de_donde_venimos_y_por_que(tmp_path):
    correo = _con_anterior(tmp_path, motivo="el precio tocó la invalidación")
    assert "Cambio de lectura:" in correo
    assert "el 17/10 era alcista" in correo
    assert "el precio tocó el nivel que invalidaba la lectura anterior" in correo
    assert correo.index("Cambio de lectura:") < correo.index("Lo que mueve el precio al")


def test_sin_motivo_de_caducidad_dice_que_la_lectura_anterior_cumplio_su_vigencia(tmp_path):
    correo = _con_anterior(tmp_path)
    assert "cumplió su vigencia" in correo


def test_si_la_direccion_no_cambio_no_aparece_la_linea(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    hoy = p["datos"]["activos"][0]["lectura"]["direccion"]
    p["datos"]["anterior"] = {"direccion": hoy, "fecha": "17/10", "motivo": ""}
    p["huella"] = es._huella(p)
    assert "Cambio de lectura:" not in _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Cambio de lectura:" not in _correo(oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True),
                                                        tmp_path, EJECUTIVO, fx.AUTOR, HOY))


def test_el_cambio_de_lectura_dice_lo_que_ve_hoy_en_un_rango(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    a = p["datos"]["activos"][0]
    a["lectura"]["direccion"] = "LATERAL"
    a["fmt"].update(borde_superior="4.195,31", borde_inferior="4.138,40")
    p["datos"]["anterior"] = {"direccion": "BAJISTA", "fecha": "17/10", "motivo": ""}
    p["huella"] = es._huella(p)
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "el 17/10 era bajista y hoy es lateral" in correo
    assert "Hoy el precio se mueve en un rango entre 4.138,40 y 4.195,31, sin una tendencia que lo guíe." in correo


def test_el_cambio_de_lectura_a_tendencia_dice_el_nivel_que_la_anula_y_el_objetivo(tmp_path):
    a = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)["datos"]["activos"][0]
    previa = "LATERAL" if a["lectura"]["direccion"] != "LATERAL" else "BAJISTA"
    correo = _con_anterior(tmp_path, direccion=previa)
    f = a["fmt"]
    assert f"Hoy la tendencia es {a['lectura']['direccion'].lower()}: se anula si cierra" in correo
    assert f["invalidacion"] in correo and f["objetivo_tori"] in correo


def _activo_en_rango(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, dolar=True)
    a = p["datos"]["activos"][0]
    a["lectura"]["direccion"] = "LATERAL"
    a["fmt"].update(invalidacion="", objetivo_tori="", borde_superior="4.195,31", borde_inferior="4.138,40")
    return p, a


def test_un_activo_en_rango_no_arma_titular_ni_preheader_con_huecos(tmp_path):
    p, a = _activo_en_rango(tmp_path)
    assert oh.titular_base(a) == "El oro se mueve en rango y no tiene una tendencia que lo guíe"
    assert oh.titular_correo(a, p["editorial"]["fuentes"], variante=True) == oh.titular_base(a)
    pre = oh.preheader_sugerido(a, p["editorial"]["fuentes"], p["datos"])
    assert pre.startswith("Nuestra lectura en 4H") and "4.138,40" in pre and "línea de ." not in pre


def test_en_rango_la_tira_de_cifras_muestra_los_bordes_y_no_sin_nivel(tmp_path):
    p, a = _activo_en_rango(tmp_path)
    p["huella"] = es._huella(p)
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Soporte del rango" in correo and "Resistencia del rango" in correo
    assert "sin nivel" not in correo


def _hero(tmp_path, activo=None):
    """El HTML de la apertura oscura de un activo, con el activo de la fixture (o el que se pase)."""
    p = _pieza(tmp_path)
    a = activo or p["datos"]["activos"][0]
    c = oh.paleta_correo(oh.paleta())
    return a, oh._hero_activo(a, oh.titular_base(a), c, bajada="Bajada de prueba.", autor=fx.AUTOR, d=p["datos"])


def test_el_titular_del_hero_no_lleva_cifras(tmp_path):
    """Un prospecto novato no procesa tres precios de cinco decimales: la tesis va en el titular y los niveles, en las tarjetas."""
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]
    assert not re.search(r"\d", oh.titular_base(a))
    p2, a2 = _activo_en_rango(tmp_path)
    assert not re.search(r"\d", oh.titular_base(a2))


@pytest.mark.parametrize("estado,direccion,esperado", [
    ("RUPTURA", "ALCISTA", "El oro rompió su línea bajista: la lectura se inclina al alza"),
    ("RUPTURA", "BAJISTA", "El oro rompió su línea alcista: la lectura se inclina a la baja"),
    ("REBOTE", "ALCISTA", "El oro rebota en su línea: la lectura alcista sigue en pie"),
    ("PRUEBA", "BAJISTA", "El oro pone a prueba su línea: ahí se juega la lectura bajista"),
])
def test_el_titular_dice_la_causa_segun_el_estado_de_la_lectura(tmp_path, estado, direccion, esperado):
    """La causa sale del estado que ya trae la lectura (nunca de un motivo inventado) y no lleva cifras."""
    a = _pieza(tmp_path)["datos"]["activos"][0]
    a = dict(a, lectura=dict(a["lectura"], estado=estado, direccion=direccion))
    assert oh.titular_base(a) == esperado
    assert not re.search(r"\d", oh.titular_base(a))


def test_el_hero_traduce_la_jerga_de_las_tarjetas(tmp_path):
    _, hero = _hero(tmp_path)
    for jerga in ("Precio de foto", "· swing", "Invalida el sesgo", "Sesgo técnico", "Proyección técnica"):
        assert jerga not in hero
    assert "Precio de referencia" in hero and "Al momento del análisis" in hero
    assert "Horizonte: de una a dos semanas" in hero


def test_el_hero_pone_las_cifras_de_la_lectura_y_no_otras(tmp_path):
    a, hero = _hero(tmp_path)
    f = a["fmt"]
    for clave in ("precio", "invalidacion", "objetivo_tori"):
        assert f[clave] in hero
    assert "sin nivel" not in hero


def test_sin_linea_de_seguridad_el_hero_muestra_el_nivel_a_vigilar_y_no_sin_nivel(tmp_path):
    """GBPUSD 2026-10-21: la ruptura no trae línea de control trazable (`invalidacion` vacía)."""
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]
    a["fmt"]["invalidacion"] = ""
    _, hero = _hero(tmp_path, a)
    assert "sin nivel" not in hero and "Línea de control" not in hero
    assert "Nivel a vigilar" in hero and a["fmt"]["vigilar"] in hero


def test_sin_objetivo_el_hero_no_imprime_sin_nivel(tmp_path):
    p = _pieza(tmp_path)
    a = p["datos"]["activos"][0]
    a["fmt"]["objetivo_tori"] = ""
    _, hero = _hero(tmp_path, a)
    assert "sin nivel" not in hero and a["fmt"]["vigilar"] in hero


def test_en_rango_el_hero_conserva_los_bordes_y_dice_lateral(tmp_path):
    _, a = _activo_en_rango(tmp_path)
    _, hero = _hero(tmp_path, a)
    assert "Soporte del rango" in hero and "Resistencia del rango" in hero and "LATERAL" in hero
    assert "sin nivel" not in hero


def test_la_linea_de_seguridad_se_explica_segun_el_lado_en_que_esta_el_precio(tmp_path):
    """En una lectura bajista la línea de control queda SOBRE el precio: no se «pierde», se supera."""
    p = _pieza(tmp_path)
    bajista = p["datos"]["activos"][0]
    assert bajista["lectura"]["direccion"] == "BAJISTA"
    _, hero = _hero(tmp_path, bajista)
    assert "Si el precio la supera, la lectura deja de valer" in hero and "la pierde" not in hero
    alcista = dict(bajista, lectura=dict(bajista["lectura"], direccion="ALCISTA"))
    _, hero = _hero(tmp_path, alcista)
    assert "Si el precio cae bajo ella, la lectura deja de valer" in hero


def test_el_objetivo_no_lleva_el_color_de_marca_para_no_leerse_como_ganancia(tmp_path):
    """El cromo no opina: el verde de marca sobre un objetivo bajista se lee como «ganancia»."""
    _, hero = _hero(tmp_path)
    cifra = re.search(r'Primer objetivo</p><p class="hero-cifra"[^>]*color:([^;]+);', hero)
    assert cifra and cifra.group(1).upper() == "#FFFFFF"


def test_la_tarjeta_de_la_linea_no_sugiere_garantia(tmp_path):
    """Director, 2026-10-21: «seguridad» suena a garantía; la tarjeta dice «control» y explica qué pasa si se cruza."""
    _, hero = _hero(tmp_path)
    assert "Línea de control" in hero and "Línea de seguridad" not in hero
    assert "la lectura deja de valer" in hero


def test_la_tarjeta_senala_el_objetivo_como_el_primero(tmp_path):
    """Director, 2026-10-21: el objetivo de la lectura es una referencia, no el destino final."""
    _, hero = _hero(tmp_path)
    assert "Primer objetivo" in hero


def test_el_objetivo_dice_a_cuanto_esta_del_precio_calculado_desde_la_lectura(tmp_path):
    """Sale de `lectura.precio` y `lectura.objetivo.precio` en ejecución: nada escrito a mano (regla 1)."""
    a, hero = _hero(tmp_path)
    lec = a["lectura"]
    pct = abs(lec["objetivo"]["precio"] - lec["precio"]) / lec["precio"] * 100
    assert f"A {pct:.2f}".replace(".", ",") + " % del precio de referencia" in hero


def test_en_rango_la_direccion_y_el_precio_van_en_grande_y_los_bordes_en_chico(tmp_path):
    _, a = _activo_en_rango(tmp_path)
    _, hero = _hero(tmp_path, a)
    assert hero.index("Hacia dónde apunta") < hero.index("Soporte del rango")
    assert hero.index("LATERAL") < hero.index("Soporte del rango") < hero.index("Resistencia del rango")


def test_el_hero_se_acomoda_al_celular(tmp_path):
    """Menos relleno lateral en pantallas angostas: las etiquetas largas no se parten ni quedan 3 líneas enanas."""
    plantilla = (RAIZ / "templates" / "oportunidad" / "pieza.html").read_text(encoding="utf-8")
    assert re.search(r"\.pad-hero\{[^}]*padding", plantilla)
    _, hero = _hero(tmp_path)
    assert "Vigencia del análisis" not in hero and "Vigencia:" in hero


def test_el_hero_lleva_el_logo_de_gi_y_ningun_aviso_legal(tmp_path):
    """Director, 2026-10-21: el hero lleva solo el logo; el aviso legal ya va en el pie del correo."""
    _, hero = _hero(tmp_path)
    assert hero.count('alt="Grupo Inteligencia"') == 1 and "data:image/png;base64," in hero
    assert "asesoría" not in hero and "Prohibida su reproducción" not in hero


def test_el_hero_cierra_con_un_gancho_hacia_el_cuerpo(tmp_path):
    _, hero = _hero(tmp_path)
    assert "Abajo:" in hero


def test_el_microtexto_del_hero_se_lee_en_el_celular_y_el_aviso_legal_en_fondo_claro(tmp_path):
    """El gris más claro del hero no puede heredarlo el aviso legal, que va sobre fondo claro."""
    c = oh.paleta_correo(oh.paleta())
    assert c["hero_rotulo"].upper() == "#A9BBBE"
    p = _pieza(tmp_path)
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY), re.S).group(1)
    legal = re.search(r'<p[^>]*color:([^;]+);[^>]*>Análisis general de mercado', marco)
    assert legal and legal.group(1).strip().upper() != c["hero_rotulo"].upper()


def test_el_hero_no_usa_el_vocabulario_de_senal_ni_el_guion_largo(tmp_path):
    _, hero = _hero(tmp_path)
    texto = re.sub(r"<[^>]+>", " ", hero).lower()
    for vetada in ("stop", "entrada", "oportunidad", "—", "–"):
        assert vetada not in texto


# ───────────────────────────────────────────── tests contrato: textos editables correo (2026-10-19)


def _extraer_texto_marcador(fragmento: str, nombre_ed: str) -> str:
    """Extrae el contenido de texto plano del elemento con data-ed='nombre_ed'."""
    patron = rf'<([a-zA-Z0-9]+)\b[^>]*\bdata-ed=["\']{re.escape(nombre_ed)}["\'][^>]*>(.*?)</\1>'
    m = re.search(patron, fragmento, re.S)
    if not m:
        raise AssertionError(f"No se encontró la etiqueta con data-ed='{nombre_ed}'")
    contenido = m.group(2)
    import html as html_mod
    return html_mod.unescape(re.sub(r'<[^>]+>', '', contenido)).strip()


def test_el_json_de_datos_trae_textos_editables_de_intro_cierre_y_activos(tmp_path):
    """(1) El JSON de #datos trae 'editable' con intro, cierre y, por activo, titular y contexto no vacíos."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    datos = json.loads(crudo)
    assert "editable" in datos, "El JSON de #datos no incluye la clave 'editable'"
    editable = datos["editable"]
    assert isinstance(editable.get("intro"), str) and editable["intro"].strip()
    assert isinstance(editable.get("cierre"), str) and editable["cierre"].strip()
    assert "activos" in editable and isinstance(editable["activos"], dict)

    p = _pieza(tmp_path)
    for a in p["datos"]["activos"]:
        t = a["ticker"]
        assert t in editable["activos"], f"Falta el activo {t} en editable['activos']"
        act_ed = editable["activos"][t]
        assert isinstance(act_ed.get("titular"), str) and act_ed["titular"].strip()
        assert isinstance(act_ed.get("contexto"), str) and act_ed["contexto"].strip()


def test_cada_clave_editable_tiene_su_marcador_data_ed_en_el_html(tmp_path):
    """(2) Cada clave editable tiene su marcador data-ed en el HTML (intro y cierre al menos una vez, titular y contexto una vez por activo)."""
    p = _pieza(tmp_path)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)

    intros = re.findall(r'\bdata-ed=["\']intro["\']', html)
    cierres = re.findall(r'\bdata-ed=["\']cierre["\']', html)
    assert len(intros) >= 1, f"Se esperaba al menos un marcador data-ed='intro', se encontraron {len(intros)}"
    assert len(cierres) >= 1, f"Se esperaba al menos un marcador data-ed='cierre', se encontraron {len(cierres)}"

    for a in p["datos"]["activos"]:
        t = a["ticker"]
        match = re.search(rf'<template class="correo-activo" data-ticker="{re.escape(t)}">(.*?)</template>', html, re.S)
        assert match is not None, f"No se encontró el template para el activo {t}"
        bloque = match.group(1)
        titulares = re.findall(r'\bdata-ed=["\']titular["\']', bloque)
        contextos = re.findall(r'\bdata-ed=["\']contexto["\']', bloque)
        assert len(titulares) == 1, f"El activo {t} debe tener exactamente un data-ed='titular', tiene {len(titulares)}"
        assert len(contextos) == 1, f"El activo {t} debe tener exactamente un data-ed='contexto', tiene {len(contextos)}"


def test_el_texto_por_defecto_del_marcador_coincide_con_datos_editable(tmp_path):
    """(3) El texto por defecto del marcador coincide con DATOS.editable."""
    p = _pieza(tmp_path)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    datos = json.loads(crudo)
    assert "editable" in datos, "Falta la clave 'editable' en #datos"
    editable = datos["editable"]

    texto_intro = _extraer_texto_marcador(html, "intro")
    assert texto_intro == editable["intro"], (
        f"El texto por defecto de data-ed='intro' no coincide con editable['intro']:\n"
        f"HTML: {texto_intro!r}\nJSON: {editable['intro']!r}"
    )

    for a in p["datos"]["activos"]:
        t = a["ticker"]
        match = re.search(rf'<template class="correo-activo" data-ticker="{re.escape(t)}">(.*?)</template>', html, re.S)
        assert match is not None, f"No se encontró el template para el activo {t}"
        bloque = match.group(1)

        texto_cierre = _extraer_texto_marcador(bloque, "cierre")
        assert texto_cierre == editable["cierre"], (
            f"El texto de cierre en {t} no coincide con editable['cierre']:\n"
            f"HTML: {texto_cierre!r}\nJSON: {editable['cierre']!r}"
        )

        act_ed = editable["activos"][t]
        texto_titular = _extraer_texto_marcador(bloque, "titular")
        assert texto_titular == act_ed["titular"], (
            f"El titular en {t} no coincide con editable['activos'][{t}]['titular']:\n"
            f"HTML: {texto_titular!r}\nJSON: {act_ed['titular']!r}"
        )

        texto_contexto = _extraer_texto_marcador(bloque, "contexto")
        assert texto_contexto == act_ed["contexto"], (
            f"El contexto en {t} no coincide con editable['activos'][{t}]['contexto']:\n"
            f"HTML: {texto_contexto!r}\nJSON: {act_ed['contexto']!r}"
        )


def test_la_plantilla_pieza_html_contiene_el_interruptor_y_el_codigo_con_textContent():
    """(4) La plantilla pieza.html contiene el interruptor y el código que usa textContent (no innerHTML) para insertar texto propio."""
    plantilla = oh.PLANTILLA.read_text(encoding="utf-8")

    patron_interruptor = re.compile(r'<input[^>]*type="radio"[^>]*name="modo-redaccion"', re.I)
    assert patron_interruptor.search(plantilla), (
        "La plantilla templates/oportunidad/pieza.html debe contener un interruptor (checkbox o radio) "
        "para que el ejecutivo pueda redactar él mismo los textos."
    )

    bloques = re.findall(r'<script\b[^>]*>(.*?)</script>', plantilla, re.S)
    assert bloques, "La plantilla debe contener un bloque de script"
    script = "\n".join(bloques)

    assert "data-ed" in script, "El script de pieza.html debe buscar o manipular los marcadores data-ed"
    assert "textContent" in script, "El script debe usar textContent para insertar textos"
    assert re.search(r'\btextContent\s*=', script), (
        "El script debe asignar el texto propio a los elementos usando textContent"
    )
    assert not re.search(r'data-ed[^;]+innerHTML\s*=', script), (
        "El script no debe usar innerHTML para insertar texto propio en los marcadores data-ed"
    )


def test_el_texto_de_los_marcadores_no_contiene_guion_largo_ni_medio(tmp_path):
    """(5) El texto de los marcadores no contiene el guion largo ni el medio."""
    import html as html_mod
    p = _pieza(tmp_path)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)

    marcadores = re.findall(r'<[a-zA-Z0-9]+\b[^>]*\bdata-ed=["\'](\w+)["\'][^>]*>(.*?)</[a-zA-Z0-9]+>', html, re.S)
    assert len(marcadores) >= 4, (
        f"Se esperaban marcadores data-ed en el HTML (intro, cierre, titular, contexto), se encontraron {len(marcadores)}"
    )

    for nombre_ed, contenido in marcadores:
        texto = html_mod.unescape(re.sub(r'<[^>]+>', '', contenido)).strip()
        assert "—" not in texto, f"El marcador data-ed='{nombre_ed}' contiene guion largo (—): {texto!r}"
        assert "–" not in texto, f"El marcador data-ed='{nombre_ed}' contiene guion medio (–): {texto!r}"



# ───────────────────────────────────────────── la noticia directa del activo (spec 2026-10-20)


DIRECTA_NOTICIA = {"entidad": "World Gold Council", "medio": "World Gold Council", "fecha": "2026-10-06",
               "url": "https://www.gold.org/goldhub/research/demanda-octubre", "postura": "bajista",
               "tesis": "World Gold Council informa una pausa en las compras de oro de los bancos centrales.",
               "verificacion": "ok"}


def test_el_correo_lleva_la_noticia_directa_con_enlace_y_sin_etiqueta_de_postura(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=[DIRECTA_NOTICIA])
    p["editorial"]["fuentes"][0]["postura"] = "alcista"  # contra la lectura bajista de la fixture
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Lo último de oro" in correo and "World Gold Council" in correo
    assert 'href="https://www.gold.org/goldhub/research/demanda-octubre"' in correo
    assert "pausa en las compras de oro" in correo
    assert "Coincide con nuestra lectura" not in correo and "—" not in correo


def test_sin_fuente_directa_sellada_el_correo_sale_como_antes(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=[DIRECTA_NOTICIA], sello=False)
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Lo último de" not in correo


def test_el_correo_cita_un_banco_y_la_directa_a_la_vez(tmp_path):
    p = fx.pieza_oportunidad(tmp_path, laminas=True, fuentes=[DIRECTA_NOTICIA, UBS_A_FAVOR])
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Lo último de oro" in correo and "Qué dice la banca" in correo
    assert correo.index("Lo último de oro") < correo.index("Qué dice la banca")
    assert correo.count("Coincide con nuestra lectura") == 1


# El correo abre con la noticia y cierra con el análisis firmado (spec 2026-10-24 §5).
NOTICIA = {"medio": "Reuters", "fecha": "2026-10-11",
           "url": "https://www.reuters.com/markets/commodities/gold-dips-2026-10-11/",
           "titular_original": "Gold dips as dollar firms", "extracto": "Gold fell.",
           "titular": "El oro cede terreno mientras el dólar se fortalece",
           "bajada": "Según Reuters, el metal pierde fuerza frente a un dólar más firme.", "motivo": "oro_lingotes"}
TASA = {"banco": "fed", "nombre": "Reserva Federal (Fed)", "serie": "Tasa efectiva de fondos federales",
        "valor": "3,88", "fecha": "09/10", "linea": "Una tasa alta en EE.UU. hace más atractivo el dólar.",
        "motivo_imagen": "banco_central"}


def _con_apertura(tmp_path, noticia=True, tasa=True, imagenes=True, **cambios):
    p = _pieza(tmp_path)
    if noticia:
        p["editorial"]["noticia"] = {**NOTICIA, **cambios}
    if tasa:
        p["datos"]["tasa"] = dict(TASA)
        p["huella"] = es._huella(p)
    if imagenes:
        p["ilustraciones"] = {}
        for clave, activa in (("noticia", noticia), ("tasa", tasa)):
            if activa:
                # Bytes distintos por imagen: dos PNG idénticos comparten URI y el publicador no los distingue.
                (tmp_path / f"ilustracion_{clave}.png").write_bytes(fx.PNG + clave.encode())
                p["ilustraciones"][clave] = f"ilustracion_{clave}.png"
    return p


def test_correo_abre_con_la_noticia(tmp_path):
    correo = _correo(oh.armar(_con_apertura(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    i = [correo.index(x) for x in (NOTICIA["titular"], "Tasa efectiva de fondos federales",
                                   "Los tres escenarios", "Simulación realizada por")]
    assert i == sorted(i)
    assert "MERCADO HOY · ORO (XAU/USD)" in correo


def test_firma_al_pie_del_analisis(tmp_path):
    for p in (_con_apertura(tmp_path), _pieza(tmp_path)):
        correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
        firma = correo.index("Realizado por Benjamín Bravo Soza · Departamento de Estudios GI")
        assert correo.index("Los tres escenarios") < firma < correo.index("Simulación realizada por")


def test_rotulo_imagen_ilustrativa(tmp_path):
    rotulo = ">Imagen ilustrativa</p>"
    assert _correo(oh.armar(_con_apertura(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)).count(rotulo) == 2
    p = _con_apertura(tmp_path, tasa=False)
    assert _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)).count(rotulo) == 1
    p = _con_apertura(tmp_path, imagenes=False)
    assert "Imagen ilustrativa" not in _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))


def test_noticia_vencida_dice_su_fecha(tmp_path):
    p = _con_apertura(tmp_path)
    vigente = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Fuente: Reuters · 11 de octubre" in vigente and "Noticia del" not in vigente
    vieja = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, date(2026, 10, 16)))
    assert "Noticia del domingo 11 de octubre" in vieja


def test_directa_repetida_no_se_duplica(tmp_path):
    p = _con_apertura(tmp_path)
    p["editorial"]["fuentes"] = [*p["editorial"]["fuentes"], dict(fx.DIRECTA_ORO)]
    url = fx.DIRECTA_ORO["url"]
    assert "Lo último de oro" in _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))  # sin repetir, sale
    p["editorial"]["noticia"]["url"] = url
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert correo.count(f'href="{url}"') == 1 and "Lo último de oro" not in correo


def test_asunto_sigue_a_la_noticia(tmp_path):
    html = oh.armar(_con_apertura(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', html, re.S).group(1)
    assert f"Asunto sugerido:</strong> {NOTICIA['titular']}" in marco
    assert f"Preheader:</strong> {NOTICIA['bajada']}" in marco
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(crudo)["editable"]["activos"]["XAUUSD"]["titular"] == NOTICIA["titular"]


def test_asunto_sin_noticia_es_el_de_hoy(tmp_path):
    p = _con_apertura(tmp_path, noticia=False)
    a = p["datos"]["activos"][0]
    marco = re.search(r'<template id="correo-marco">(.*?)</template>',
                      oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY), re.S).group(1)
    assert f"Asunto sugerido:</strong> {oh.ih.e(oh.asunto_sugerido(a, p['editorial']['fuentes']))}" in marco


def test_pieza_vieja_se_arma(tmp_path):
    p = _pieza(tmp_path)
    assert "noticia" not in p["editorial"] and "tasa" not in p["datos"] and "ilustraciones" not in p
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Los tres escenarios" in correo and "Imagen ilustrativa" not in correo


def test_tasa_con_nombre_real(tmp_path):
    for p in (_con_apertura(tmp_path), _con_apertura(tmp_path, noticia=False)):
        correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
        assert "Tasa efectiva de fondos federales: 3,88 por ciento al 09/10" in correo
        assert "tasa de la Fed" not in correo


def test_sin_noticia_la_tasa_va_en_la_apertura_oscura(tmp_path):
    c = oh.paleta_correo(oh.paleta())
    correo = _correo(oh.armar(_con_apertura(tmp_path, noticia=False), tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    hero = correo[correo.index(f'bgcolor="{c["hero"]}"'):correo.index('<td class="pad"')]
    assert "Tasa efectiva de fondos federales" in hero


def test_correo_sin_var_ni_rgba(tmp_path):
    for p in (_con_apertura(tmp_path), _con_apertura(tmp_path, noticia=False)):
        correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
        assert "var(" not in correo and "rgba(" not in correo
        assert "—" not in correo and "–" not in correo


def test_con_publicador_las_ilustraciones_van_por_url(tmp_path):
    html = oh.armar(_con_apertura(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY,
                    publicar=lambda r: f"https://ejemplo.test/correos/{r.name}")
    correo = _correo(html)
    assert "ejemplo.test/correos/ilustracion_noticia.png" in correo
    assert "ejemplo.test/correos/ilustracion_tasa.png" in correo
    assert "data:image" not in correo


def test_con_noticia_el_correo_dice_la_vigencia(tmp_path):
    correo = _correo(oh.armar(_con_apertura(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert "Vigencia: lunes 12/10 al lunes 19/10" in correo


def test_una_ilustracion_con_ruta_ajena_no_se_incrusta(tmp_path):
    p = _con_apertura(tmp_path, imagenes=False)
    afuera = tmp_path.parent / "secreto.png"
    afuera.write_bytes(fx.PNG + b"x")
    p["ilustraciones"] = {"noticia": "../secreto.png"}
    correo = _correo(oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY))
    assert ">Imagen ilustrativa</p>" not in correo


def test_en_el_celular_la_imagen_de_tasas_baja_a_todo_el_ancho(tmp_path):
    # Director, 2026-10-25: el dato de tasas va siempre con su imagen, también en el celular.
    for p in (_con_apertura(tmp_path), _con_apertura(tmp_path, noticia=False)):
        html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
        correo = _correo(html)
        # Las dos celdas se apilan: si solo baja la imagen, el texto queda apretado en una columna angosta.
        assert re.search(r'<td class="stack" valign="top" style="padding:0 16px 0 0;"><p[^>]*>Reserva Federal', correo)
        bloque = correo.split("Tasa efectiva de fondos federales")[1][:3000]
        assert '<td class="stack tasa-img"' in bloque and "hide-m" not in bloque
        estilos = re.search(r'<style id="correo-estilos">(.*?)</style>', html, re.S).group(1)
        assert re.search(r"\.tasa-img img\{[^}]*width:100% !important", estilos)
