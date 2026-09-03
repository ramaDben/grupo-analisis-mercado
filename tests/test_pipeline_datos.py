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


# --- El umbral de confianza, visible antes de publicar ---

def test_una_confianza_bajo_el_umbral_deja_los_datos_no_utilizables(base):
    """Frescura y confianza son cosas distintas, pero ninguna de las dos sola
    alcanza para publicar.

    El estado decía "Datos frescos" con la confianza en 54,7 % y dos drivers
    rotos. Técnicamente cierto -los archivos eran de hace minutos- y
    operativamente inútil: el modelo estaba avisando que no veía.
    """
    _escribir(base / "DATA DRIVERS USDCLP" / "macro_bias_output.json", {
        "as_of_utc": _hace(1),
        "confianza_general": {"confianza_total_pct": 54.6},
        "activos": {},
    })
    est = pd_.estado_datos(base)

    assert est.confianza_pct == pytest.approx(54.6)
    assert not est.confianza_suficiente
    assert not est.listo, "relojes frescos no bastan si el modelo no ve"


def test_una_confianza_sobre_el_umbral_no_bloquea(base):
    est = pd_.estado_datos(base)   # la fixture trae 91 %
    assert est.confianza_suficiente
    assert est.listo


def test_el_umbral_del_estado_es_el_mismo_del_escaner():
    """Dos umbrales distintos para la misma decisión es el error del ATR otra
    vez: el estado diría que se puede publicar y el escáner excluiría igual."""
    import sys
    from pathlib import Path as _P
    raiz = _P(__file__).resolve().parents[1]
    if str(raiz / "scripts") not in sys.path:
        sys.path.insert(0, str(raiz / "scripts"))
    import screener_gi

    assert pd_.UMBRAL_CONFIANZA_PCT == screener_gi.UMBRAL_CONFIANZA_PCT


def test_sin_confianza_declarada_no_se_asume_que_alcanza(tmp_path):
    """Un snapshot sin `confianza_general` no puede pasar por defecto: sería
    exactamente la puerta de atrás que el umbral existe para cerrar."""
    _escribir(tmp_path / "DATA AGENDA" / "estado_ejecucion.json", {
        "ultima_ejecucion_utc": _hace(1), "status_por_fuente": {}, "errores_por_fuente": {},
    })
    _escribir(tmp_path / "DATA PRECIOS OHLC" / "latest_prices_summary.json", {"as_of_utc": _hace(1)})
    _escribir(tmp_path / "DATA DRIVERS USDCLP" / "macro_bias_output.json", {"as_of_utc": _hace(1)})

    est = pd_.estado_datos(tmp_path)
    assert est.confianza_pct is None
    assert not est.confianza_suficiente


# --- El fallback a yfinance tiene que anunciarse ---

def _precios_con_fuentes(base, fuentes: dict[str, str], as_of_h: float = 1.0):
    _escribir(base / "DATA PRECIOS OHLC" / "latest_prices_summary.json", {
        "as_of_utc": _hace(as_of_h),
        "activos": {
            act: {"H1": {"close": 1.0}, "H1_fuente": f, "D1": {"close": 1.0}, "D1_fuente": f}
            for act, f in fuentes.items()
        },
    })


def test_los_precios_declaran_de_donde_vienen(base):
    est = pd_.estado_datos(base)
    precios = next(r for r in est.relojes if r.nombre == "precios")
    assert precios.fuentes == {}, "la fixture base no declara fuentes"


def test_un_fallback_a_yfinance_se_reporta_aunque_los_relojes_esten_frescos(base):
    """El 2026-09-02 el terminal estaba en otra cuenta y el extractor cayó a
    yfinance en cinco de seis activos. La cadena reportó `[OK] precios` y
    `Datos frescos`, porque los archivos eran de hace minutos.

    El campo `broker: YFINANCE` quedaba registrado en cada archivo, así que era
    auditable, pero **nada lo decía en voz alta**. Costó una hora de diagnóstico
    y los stops del Playbook quedaron calculados sobre futuros de yfinance en vez
    de los CFD del broker.

    Es el mismo defecto que el `status: "OK"` regalado del extractor de
    commodities: un fallback que hace su trabajo y no se anuncia.
    """
    _precios_con_fuentes(base, {
        "USDCLP": "MT5", "XAUUSD": "YFINANCE", "WTI": "YFINANCE",
        "BRENT": "YFINANCE", "US100": "YFINANCE", "COPPER": "YFINANCE",
    })
    est = pd_.estado_datos(base)
    precios = next(r for r in est.relojes if r.nombre == "precios")

    assert precios.antiguedad_h is not None, "sigue siendo un reloj fresco"
    assert not precios.fresco, "un fallback masivo no es una lectura utilizable"
    assert "5 de 6" in precios.error
    assert "YFINANCE" in precios.error.upper()
    assert not est.listo


def test_todo_desde_mt5_no_genera_aviso(base):
    """La contraparte: sin esto, "siempre avisa" y "avisa cuando corresponde"
    serían indistinguibles."""
    _precios_con_fuentes(base, {
        "USDCLP": "MT5", "XAUUSD": "MT5", "WTI": "MT5",
        "BRENT": "MT5", "US100": "MT5", "COPPER": "MT5",
    })
    est = pd_.estado_datos(base)
    precios = next(r for r in est.relojes if r.nombre == "precios")

    assert precios.fresco
    assert precios.fuentes == {"MT5": 6}
    assert est.listo


def test_un_solo_activo_en_fallback_tambien_se_nombra(base):
    """No hay umbral de tolerancia: el Playbook cubre cinco activos y un stop
    calculado sobre otra fuente de precio es un stop de otro mercado."""
    _precios_con_fuentes(base, {
        "USDCLP": "MT5", "XAUUSD": "MT5", "WTI": "YFINANCE",
        "BRENT": "MT5", "US100": "MT5", "COPPER": "MT5",
    })
    est = pd_.estado_datos(base)
    precios = next(r for r in est.relojes if r.nombre == "precios")

    assert not precios.fresco
    assert "1 de 6" in precios.error
    assert "WTI" in precios.error
