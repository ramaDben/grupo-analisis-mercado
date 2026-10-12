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
    activos = [fx.activo_semanal(), fx.activo_semanal(rango=True)]
    for a in activos:
        (tmp_path / a["grafico"]).write_bytes(fx.PNG)
        (tmp_path / f"lamina_{a['ticker'].lower()}.png").write_bytes(fx.PNG)
    tickers = [a["ticker"] for a in activos]
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"},
                       {"semana": "2026-W42", "chip": "ANÁLISIS TÉCNICO DE LA SEMANA", "edicion": "lunes 12-10 · 09:30",
                        "activos": activos, "drivers": {}, "agenda_semana": []},
                       {a["ticker"]: a["grafico"] for a in activos},
                       extra_campos={"titulares": tickers, "contexto": tickers})
    p["editorial"] = {"titular": "La semana técnica en seis activos", "bajada": "Lectura de cada activo.",
                      "titulares": {t: f"Titular de {t}" for t in tickers},
                      "contexto": {t: f"Contexto de {t}." for t in tickers}}
    return p


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
    p["datos"]["activos"][0]["escenario"]["motivo"] = "la lectura no trae nivel de invalidación"
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Sin simulación esta semana: la lectura no trae nivel de invalidación" in html
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
