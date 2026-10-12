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


def test_sin_contrato_y_sin_motivo_se_trata_como_sin_simulacion(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
    assert "no tenemos los datos de la cuenta para calcular el tamaño de la operación" in bloque
    assert 'name="perdida"' not in bloque and 'name="incluir"' in bloque


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
