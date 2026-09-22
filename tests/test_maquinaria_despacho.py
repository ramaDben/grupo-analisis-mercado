"""Tests unitarios y de integración para la Maquinaria Automatizada de Despacho Multi-Canal (Desk GI).

Verifica que los 7 canales temáticos generen sus mensajes con datos reales del motor,
sin guiones prohibidos, con la debida precisión decimal y con el enrutamiento correcto.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

from scripts.maquinaria_despacho import MaquinariaDespacho, formatear_num_es, formatear_pct_es

SANTIAGO = ZoneInfo("America/Santiago")


@pytest.fixture
def maquinaria():
    return MaquinariaDespacho()


@pytest.fixture
def ahora_fijo():
    return datetime(2026, 9, 21, 8, 30, tzinfo=SANTIAGO)


def test_generacion_completa_7_canales(maquinaria, ahora_fijo):
    """Verifica que se generen exactamente los 7 canales temáticos oficiales."""
    paquetes = maquinaria.generar_todos_los_mensajes(ahora=ahora_fijo)

    esperados = [
        "01_macro_y_apertura",
        "02_forex_divisas",
        "03_commodities_materias_primas",
        "04_indices_bursatiles",
        "05_acciones_etfs",
        "06_criptoactivos",
        "07_oportunidades_cuantitativas",
    ]

    for esp in esperados:
        assert esp in paquetes, f"Falta el canal esperado: {esp}"
        item = paquetes[esp]
        assert item["texto"], f"El texto del canal {esp} está vacío"
        assert Path(item["ruta_txt"]).is_file(), f"No se guardó el archivo txt para {esp}"


def test_compliance_whatsapp_cero_guiones_prohibidos(maquinaria, ahora_fijo):
    """Verifica que ningún mensaje de los 7 canales contenga guión largo '—' o medio '–'."""
    paquetes = maquinaria.generar_todos_los_mensajes(ahora=ahora_fijo)
    for slug, item in paquetes.items():
        texto = item["texto"]
        assert "—" not in texto, f"Guión largo prohibido encontrado en {slug}"
        assert "–" not in texto, f"Guión medio prohibido encontrado en {slug}"


def test_canal_01_macro_contiene_auditoria_y_matriz(maquinaria, ahora_fijo):
    """Verifica estructura y elementos clave del Canal 01."""
    playbook = maquinaria.cargar_datos_motor()
    eventos = maquinaria.cargar_eventos_calendario(ahora_fijo)
    msg = maquinaria.generar_canal_01_macro(playbook, eventos, ahora_fijo)

    assert "CLIMA MACRO GI" in msg
    assert "AUDITORÍA DE DATOS MACRO" in msg
    assert "PERMISOS DE TRADING H1" in msg
    assert "DRIVERS MAESTROS DE CONFIRMACIÓN" in msg
    assert "Tu ejecución en MT5" in msg
    assert "1,0% NETO" in msg

    # Presencia de los 5 activos
    for sym in ["USD/CLP", "ORO SPOT", "PETRÓLEO WTI", "PETRÓLEO BRENT", "NASDAQ 100"]:
        assert sym in msg


def test_canal_02_forex_zoom_usdclp(maquinaria, ahora_fijo):
    """Verifica zoom especializado de USD/CLP en Canal 02."""
    playbook = maquinaria.cargar_datos_motor()
    msg = maquinaria.generar_canal_02_forex(playbook, ahora_fijo)

    assert "DÓLAR & FX" in msg
    assert "FICHA CUANTITATIVA USD/CLP" in msg
    assert "Cobre COMEX" in msg
    assert "Diferencial de Tasas" in msg
    assert "MATRIZ DE PERMISOS H1" in msg
    assert "[+] AUTORIZADO" in msg
    assert "[-] PROHIBIDO" in msg


def test_canal_03_commodities_zoom_oro_y_crudo(maquinaria, ahora_fijo):
    """Verifica zoom especializado de Oro y Petróleo en Canal 03."""
    playbook = maquinaria.cargar_datos_motor()
    msg = maquinaria.generar_canal_03_commodities(playbook, ahora_fijo)

    assert "METALES & ENERGÍA" in msg
    assert "ORO SPOT (XAU/USD)" in msg
    assert "TIPS 10Y" in msg
    assert "PETRÓLEO (WTI & BRENT)" in msg
    assert "Shock Petróleo" in msg
    assert "Regla Co-Riesgo" in msg


def test_canal_04_indices_zoom_nasdaq(maquinaria, ahora_fijo):
    """Verifica zoom especializado de Nasdaq 100 en Canal 04."""
    playbook = maquinaria.cargar_datos_motor()
    msg = maquinaria.generar_canal_04_indices(playbook, ahora_fijo)

    assert "WALL STREET & ÍNDICES" in msg
    assert "NASDAQ 100 (US100" in msg
    assert "Bono US10Y" in msg
    assert "Curva 2s10s" in msg
    assert "[+] AUTORIZADO" in msg
    assert "[-] PROHIBIDO" in msg


def test_filtros_por_canal_en_ejecutar_despacho(maquinaria):
    """Verifica que el filtrado por slug o alias funcione en modo dry-run."""
    res_forex = maquinaria.ejecutar_despacho(modo="dry_run", canal_filtrado="forex")
    assert res_forex["status"] == "ok"
    assert res_forex["canales_procesados"] == 1

    res_all = maquinaria.ejecutar_despacho(modo="dry_run")
    assert res_all["status"] == "ok"
    assert res_all["canales_procesados"] == 7
