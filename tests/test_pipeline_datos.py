"""Contrato de la cadena de datos: un punto de entrada y un solo reloj.

Hasta ahora la cadena eran tres invocaciones manuales (`pipeline_ingesta.py`,
`extractor_precios.py`, `macro_bias_engine.py`) con un orden implícito, y tres
archivos de fecha que ningún consumidor miraba juntos. El modo de falla era el
peor: `ticket_engine.cargar_serie_h1_archivo` devuelve `None` en silencio si
falta la serie, así que el motor no revienta, deja de emitir tickets.

Todo con corredor inyectado y rutas temporales: la suite no puede depender de
MT5 abierto ni de que existan los datos reales.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import pipeline_datos as pd_  # noqa: E402


def _escribir(ruta: Path, payload: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(payload), encoding="utf-8")


def _hace(horas: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()


@pytest.fixture
def base(tmp_path):
    """Las tres fuentes de fecha, todas frescas."""
    _escribir(tmp_path / "DATA AGENDA" / "estado_ejecucion.json", {
        "ultima_ejecucion_utc": _hace(1),
        "status_por_fuente": {"usa": "OK", "chile": "OK"},
        "errores_por_fuente": {},
    })
    _escribir(tmp_path / "DATA PRECIOS OHLC" / "latest_prices_summary.json", {
        "as_of_utc": _hace(1), "activos": {"USDCLP": {}},
    })
    _escribir(tmp_path / "DATA DRIVERS USDCLP" / "macro_bias_output.json", {
        "as_of_utc": _hace(1),
        "confianza_general": {"confianza_total_pct": 91.0},
        "activos": {"USDCLP": {}},
    })
    return tmp_path


# --- Estado: un solo lugar donde leer la frescura ---

def test_estado_reporta_los_tres_relojes(base):
    est = pd_.estado_datos(base)
    assert [r.nombre for r in est.relojes] == ["ingesta", "precios", "sesgo"]
    assert all(r.fresco for r in est.relojes)
    assert est.listo


def test_un_archivo_ausente_se_reporta_y_no_revienta(tmp_path):
    """Contrato de error del repo: nunca None silencioso, siempre motivo explícito.
    Es justo el modo de falla que hoy deja al motor sin emitir tickets sin avisar."""
    est = pd_.estado_datos(tmp_path)
    assert not est.listo
    for r in est.relojes:
        assert not r.fresco
        assert r.error, f"{r.nombre} debe explicar por qué no está disponible"
        assert r.antiguedad_h is None


def test_un_reloj_vencido_deja_la_cadena_no_lista(base):
    _escribir(base / "DATA PRECIOS OHLC" / "latest_prices_summary.json", {
        "as_of_utc": _hace(200), "activos": {},
    })
    est = pd_.estado_datos(base)
    precios = next(r for r in est.relojes if r.nombre == "precios")
    assert not precios.fresco
    assert precios.antiguedad_h > 100
    assert not est.listo


def test_la_confianza_del_modelo_viaja_en_el_estado(base):
    """El 2026-09-02 el motor reportaba 54,7 % y nada lo miraba: `confianza_total_pct`
    solo se imprimía en consola. Para poder bloquear por confianza, primero hay
    que poder leerla desde un solo lugar."""
    _escribir(base / "DATA DRIVERS USDCLP" / "macro_bias_output.json", {
        "as_of_utc": _hace(1),
        "confianza_general": {"confianza_total_pct": 54.7},
        "activos": {},
    })
    est = pd_.estado_datos(base)
    assert est.confianza_pct == pytest.approx(54.7)


def test_una_fuente_con_error_en_la_ingesta_se_reporta(base):
    _escribir(base / "DATA AGENDA" / "estado_ejecucion.json", {
        "ultima_ejecucion_utc": _hace(1),
        "status_por_fuente": {"usa": "OK", "chile": "ERROR"},
        "errores_por_fuente": {"chile": "timeout del BCCh"},
    })
    est = pd_.estado_datos(base)
    ingesta = next(r for r in est.relojes if r.nombre == "ingesta")
    assert not ingesta.fresco
    assert "chile" in ingesta.error


# --- Cadena: un punto de entrada, en orden, que aborta ---

def test_la_cadena_corre_los_pasos_en_orden():
    corridos = []
    resultados = pd_.ejecutar_cadena(pd_.PASOS, lambda paso: (corridos.append(paso.nombre), (True, ""))[1])
    assert corridos == ["ingesta", "precios", "sesgo"]
    assert all(r.ok for r in resultados)


def test_la_cadena_aborta_al_primer_fallo_y_no_sigue():
    """Correr el motor sobre precios que no se actualizaron produce un sesgo que
    parece fresco y no lo es. Peor que fallar: falla convincente."""
    corridos = []

    def corredor(paso):
        corridos.append(paso.nombre)
        return (False, "MT5 no responde") if paso.nombre == "precios" else (True, "")

    resultados = pd_.ejecutar_cadena(pd_.PASOS, corredor)
    assert corridos == ["ingesta", "precios"], "no debe intentar el sesgo"
    assert [r.nombre for r in resultados] == ["ingesta", "precios"]
    assert resultados[-1].ok is False
    assert "MT5 no responde" in resultados[-1].detalle
