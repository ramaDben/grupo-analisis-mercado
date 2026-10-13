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
    assert "Sin simulación esta semana: el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop" in html
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
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


def test_el_nombre_del_archivo_no_dice_oportunidad(tmp_path):
    ruta = oh.guardar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert ruta.name == "analisis-semanal_2026-W42_camila-rojas.html"


def test_un_activo_sin_simulacion_igual_entra_al_correo(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"]["motivo"] = "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
    assert 'name="incluir"' in bloque and 'name="perdida"' not in bloque
    datos = json.loads(re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1))
    assert datos["activos"][0]["motivo"] == "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"
    assert "Sin simulación esta semana: " in html


def test_sin_contrato_el_cliente_ve_los_niveles_y_el_ejecutivo_el_aviso(tmp_path):
    """Sin contrato falta el volumen, no la simulación: el correo lleva los niveles sin montos."""
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
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


def test_la_semana_se_lee_con_fechas_y_no_con_la_etiqueta_iso(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "semana del 12 al 16 de octubre" in html.lower()
    visible = re.sub(r'(src|href)="data:[^"]*"|<style>.*?</style>', "", html.split('<script id="datos"')[0], flags=re.S)
    assert "W42" not in visible


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


def test_los_cuadros_parten_con_capital_y_perdida_por_defecto_y_el_saludo_admite_nombre(tmp_path):
    """El comercial no tiene que escribir nada: 2 millones de capital, 100.000 de pérdida y nombre opcional."""
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
    assert 'name="perdida" min="0" step="1000" value="100000"' in bloque
    assert 'name="capital" min="0" step="10000" value="2000000"' in bloque
    assert 'id="cliente"' in html and 'Hola<span class="cliente-nombre"></span>:' in html


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
        assert "Los 2 activos con escenarios clave para operar esta semana" in v.inner_text()
        pg.locator("[name=incluir]").first.uncheck()
        assert "El activo con escenarios clave para operar esta semana" in v.inner_text()
        pg.fill("#cliente", "Juan")
        assert "Hola Juan:" in v.inner_text()
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
