# -*- coding: utf-8 -*-
"""
test_ecosistema_macro.py
Suite de pruebas automatizadas para el Ecosistema de Ingesta Macro, Agenda y Detección de Novedades.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts"))

import agenda
import extractor_usa
import pipeline_ingesta


@pytest.fixture
def sin_backoff(monkeypatch):
    """Anula la espera entre reintentos de tenacity, no los reintentos.

    Los extractores reintentan 3 veces con backoff exponencial de hasta 10 s.
    Contra un emisor real eso es correcto -una API de gobierno se cae un rato y
    vuelve-, pero en un test contra una funcion falsa la espera no prueba nada
    y son 30 s por corrida. Se anula el `sleep` y no el `stop`, para que el
    test siga ejercitando los 3 intentos de verdad.
    """
    for nombre in ("extraer_buybacks_tesoro", "extraer_serie_fred"):
        fn = getattr(extractor_usa, nombre)
        monkeypatch.setattr(fn.retry, "sleep", lambda _segundos: None)


def test_calculo_hash_canonico_orden_invariante():
    """El hash canonico debe ser identico sin importar el orden de insercion de claves."""
    obj1 = {"a": 1, "b": {"x": 10, "y": 20}, "c": [1, 2, 3]}
    obj2 = {"c": [1, 2, 3], "b": {"y": 20, "x": 10}, "a": 1}
    
    h1 = pipeline_ingesta.calcular_hash_canonico(obj1)
    h2 = pipeline_ingesta.calcular_hash_canonico(obj2)
    assert h1 == h2, "El hash canonico debe ser deterministico e invariante al orden de claves."

def test_deteccion_revisiones_historicas():
    """Valida que una modificacion retroactiva en un dato pasado se detecte como revision."""
    hist_ant = {"2026-05-01": -0.3, "2026-06-01": 2.1}
    hist_nue = {"2026-05-01": -0.3, "2026-06-01": 2.4, "2026-07-01": 1.8}
    
    revisiones = pipeline_ingesta.detectar_revisiones_historicas(hist_ant, hist_nue)
    assert len(revisiones) == 1
    assert "2026-06-01" in revisiones[0]
    assert "2.1" in revisiones[0] and "2.4" in revisiones[0]

def test_conversion_zonas_horarias_y_dst():
    """Valida la conversion horaria precisa entre husos IANA (New York, Berlin, London, Santiago)."""
    # Evento FOMC a las 14:00 ET
    tz_ny = ZoneInfo("America/New_York")
    tz_cl = ZoneInfo("America/Santiago")
    
    dt_ny = datetime(2026, 8, 19, 14, 0, tzinfo=tz_ny)
    dt_cl = dt_ny.astimezone(tz_cl)
    
    # En agosto, NY es UTC-4 y Santiago es UTC-4 (mismo offset en invierno de Chile)
    assert dt_cl.hour == 14, f"En agosto, 14:00 NY debe ser 14:00 Santiago (ambos UTC-4). Obtenido: {dt_cl.hour}"
    
    # Evento BCE a las 14:15 CET (Berlin)
    tz_berlin = ZoneInfo("Europe/Berlin")
    dt_berlin = datetime(2026, 9, 10, 14, 15, tzinfo=tz_berlin) # CEST es UTC+2
    dt_cl_bce = dt_berlin.astimezone(tz_cl) # En sept, Chile pasa a UTC-3 tras cambio de hora de primavera
    assert dt_cl_bce.minute == 15

def test_normalizacion_unidades_cobre():
    """Valida el factor de conversion de USD/libra a USD/tonelada."""
    precio_lb = 4.50
    factor_ton = 2204.62
    precio_ton = round(precio_lb * factor_ton, 2)
    assert precio_ton == 9920.79

def test_agenda_retorno_estructurado():
    """Valida que agenda.py retorne la estructura completa esperada."""
    res = agenda.obtener_agenda(datetime(2026, 8, 20, 10, 0, tzinfo=ZoneInfo("America/Santiago")))
    assert "hay_eventos_hoy" in res
    assert "eventos_hoy" in res
    assert "eventos_proximos_7_dias" in res
    assert isinstance(res["eventos_hoy"], list)


def test_los_buybacks_piden_el_dataset_que_existe(monkeypatch):
    """El extractor pedia `v2/accounting/od/treasury_securities_buybacks`, que la
    API de Fiscal Data no sirve: devolvia 404 en todas sus versiones y el dataset
    no aparece en el catalogo. El real es `v1/accounting/od/buybacks_operations`.

    El fallo era mudo hacia afuera. El extractor capturaba la excepcion, dejaba
    los datos anteriores y seguia imprimiendo "[OK] Ingesta USA completada", asi
    que la unica senal era `usa: ERROR_FALLBACK` en estado_ejecucion.json, sin el
    motivo. Vivio desde que el archivo entro al repo.

    Se verifica el comportamiento -que URL se pide- y no el texto del codigo: un
    assert sobre el fuente pasaria con la URL escrita en un comentario.
    """
    pedidas = {}

    class RespuestaFalsa:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"data": [{"operation_date": "2026-08-25"}]}

    def falsa_get(url, params=None, timeout=None):
        pedidas["url"] = url
        pedidas["params"] = params or {}
        return RespuestaFalsa()

    monkeypatch.setattr(extractor_usa.requests, "get", falsa_get)
    filas = extractor_usa.extraer_buybacks_tesoro()

    assert pedidas["url"].endswith("/v1/accounting/od/buybacks_operations"), (
        f"pide un dataset que la API no sirve: {pedidas['url']}"
    )
    # El campo de fecha de este dataset es `operation_date`. Con `record_date`
    # la API responde 400 "Invalid query parameter", no 404: seria el mismo
    # sintoma por otra causa.
    assert pedidas["params"].get("sort") == "-operation_date"
    assert filas == [{"operation_date": "2026-08-25"}]


def test_una_fuente_degradada_deja_escrito_el_motivo(monkeypatch, tmp_path, sin_backoff):
    """`ERROR_FALLBACK` sin causa es un aviso que nadie puede accionar.

    Asi vivio el 404 de las recompras: el extractor imprimia el error por
    consola, el pipeline corre desatendido y esa salida no queda en ningun
    lado, y hacia afuera solo se veia el estado degradado. El motivo tiene que
    viajar CON el dato para poder leerlo despues.
    """
    def get_que_falla(url, params=None, timeout=None):
        raise ConnectionError("boom en el emisor")

    monkeypatch.setattr(extractor_usa.requests, "get", get_que_falla)
    monkeypatch.setattr(extractor_usa, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_usa, "OUTPUT_FILE", tmp_path / "treasury_fed_data.json")

    resultado = extractor_usa.ejecutar_extraccion_usa()

    assert resultado["tesoro_status"] == "ERROR_FALLBACK"
    assert "boom en el emisor" in resultado["tesoro_error"], (
        "la causa se perdio: queda un estado degradado sin nada que investigar"
    )


def test_sin_fallos_no_hay_motivo_que_reportar(monkeypatch, tmp_path, sin_backoff):
    """La contraparte. Sin esto, "siempre escribe un motivo" y "escribe el
    motivo correcto" serian indistinguibles, y el campo dejaria de significar
    algo: su valor esta en que aparezca SOLO cuando hay algo que contar."""
    class RespuestaFalsa:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"data": [], "observations": []}

    monkeypatch.setattr(extractor_usa.requests, "get",
                        lambda url, params=None, timeout=None: RespuestaFalsa())
    monkeypatch.setattr(extractor_usa, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_usa, "OUTPUT_FILE", tmp_path / "treasury_fed_data.json")

    resultado = extractor_usa.ejecutar_extraccion_usa()

    assert resultado["tesoro_status"] == "OK"
    assert "tesoro_error" not in resultado

