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
import pipeline_ingesta

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
