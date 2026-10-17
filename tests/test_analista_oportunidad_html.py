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


def _pieza(tmp_path):
    return fx.pieza_oportunidad(tmp_path, laminas=True)


def test_el_analisis_va_firmado_y_la_simulacion_rotulada(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Dirección de Análisis Técnico" in html
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
    """Logo de GI arriba, cuadros rojo y verde del mismo tamaño y las dos firmas (director, 2026-10-12)."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    marco = re.search(r'<template id="correo-marco">(.*?)</template>', html, re.S).group(1)
    assert 'alt="Grupo Inteligencia"' in marco and "<!--ACTIVOS-->" in marco
    assert "Te lo envía" in marco and "Camila Rojas" in marco
    c = oh.paleta()
    bloque = re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)
    assert f'border:2px solid {c["baja"]}' in bloque and f'border:2px solid {c["sube"]}' in bloque
    assert 'class="sim-perdida"' in bloque and 'class="sim-ganancia"' in bloque
    assert "var(" not in marco + bloque and "rgba(" not in marco + bloque


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


def test_el_correo_parte_con_el_saludo_a_la_persona_antes_del_titulo(tmp_path):
    """Gerencia: un correo que abre con afiche y titular se lee como spam; debe partir con el nombre."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = html.split('id="correo-root"')[1]
    assert correo.index('class="saludo-cliente"') < correo.index("<!--TITULO-->")
    assert "Te escribo para compartirte" in correo


def test_el_titulo_del_correo_cuenta_los_activos_incluidos_y_no_dice_igual_para_todos(tmp_path):
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
        assert "El activo con escenarios clave para revisar en MT5" in v.inner_text()
        pg.locator("[name=incluir]").first.uncheck()
        assert "Marca al menos un activo" in v.inner_text()
        pg.locator("[name=incluir]").first.check()
        pg.fill("#cliente", "Estimado Sr. Pérez")
        assert "Estimado Sr. Pérez:" in v.inner_text()
        b.close()


def test_el_autor_nunca_firma_la_simulacion(tmp_path):
    """Si pide el propio autor, la simulación queda con un campo por completar y no con su nombre."""
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


def test_la_ficha_cierra_con_el_bloque_de_revision_en_mt5(tmp_path):
    h = _html(tmp_path)
    assert h.count(cm.REVISION_MT5_TITULO) >= 2  # en la ficha y en el correo
    for punto in cm.REVISION_MT5_PUNTOS:
        assert punto in h


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
    assert "Escenario del análisis" in html and "Análisis técnico vigente" in html
    p["datos"]["activos"][0]["escenario"]["motivo"] = "sin nivel claro"
    p["huella"] = es._huella(p)
    assert "Sin simulación esta semana" not in oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
