"""Tests del guardrail de nombres (scripts/guardrails/nombres.py).

Verifica los contratos de nomenclatura entre subsistemas:
- Detección precisa de rutas de cliente (data/mensajes/**, data/stories/**/*.json,
  templates/stories/*.html) con separadores POSIX y Windows.
- Validación de tickers contra catalog.load_valid_tickers, sugiriendo el sufijo
  exacto del broker (ej. US100.spot ante US100).
- Validación de temporalidades canónicas contra pipeline_carrusel.MARCOS_CANONICOS
  sin duplicar tablas literales en los tests.
- Resolución de alias de canales oficiales en lenguaje natural según
  config/whatsapp_grupos.json con insensibilidad a mayúsculas y tildes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_SRC_DIR = _REPO_ROOT / "src"

for _dir in (str(_SCRIPTS_DIR), str(_SRC_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import pipeline_carrusel  # noqa: E402
from guardrails import nombres  # noqa: E402
from guardrails.nombres import (  # noqa: E402
    alias_de_canal_valido,
    es_ruta_de_cliente,
    marco_canonico,
    ticker_valido,
)


# ---------------------------------------------------------------------------
# es_ruta_de_cliente
# ---------------------------------------------------------------------------


def test_es_ruta_de_cliente_separadores_windows():
    """Rutas con separadores de Windows ('\\') deben ser reconocidas como de cliente."""
    assert es_ruta_de_cliente(r"data\mensajes\2026-09-06\01_macro.txt")
    assert es_ruta_de_cliente(Path(r"data\mensajes\alerta.txt"))
    assert es_ruta_de_cliente(r"data\stories\tanda_01\01_gold.json")
    assert es_ruta_de_cliente(r"templates\stories\alerta.html")


def test_es_ruta_de_cliente_rutas_validas_posix():
    """Rutas relativas estándar POSIX de insumos y piezas de cliente."""
    assert es_ruta_de_cliente("data/mensajes/2026-09-06/01.txt")
    assert es_ruta_de_cliente("data/stories/tanda/01.json")
    assert es_ruta_de_cliente("templates/stories/alerta.html")
    assert es_ruta_de_cliente("templates/stories/dato_macro.html")


def test_es_ruta_de_cliente_rutas_absolutas():
    """Rutas absolutas del sistema de archivos deben resolverse correctamente."""
    ruta_mensaje = _REPO_ROOT / "data" / "mensajes" / "01.txt"
    ruta_story = _REPO_ROOT / "data" / "stories" / "tanda" / "01.json"
    ruta_template = _REPO_ROOT / "templates" / "stories" / "alerta.html"

    assert es_ruta_de_cliente(ruta_mensaje)
    assert es_ruta_de_cliente(ruta_story)
    assert es_ruta_de_cliente(ruta_template)


def test_es_ruta_de_cliente_rutas_internas_falsas():
    """Rutas fuera del perímetro de cliente deben retornar False."""
    assert not es_ruta_de_cliente("scripts/algo.py")
    assert not es_ruta_de_cliente("data/logs/x.txt")
    assert not es_ruta_de_cliente("config/activos.json")


def test_es_ruta_de_cliente_templates_solo_html():
    """En templates/stories/ solo los archivos .html son piezas de cliente."""
    assert not es_ruta_de_cliente("templates/stories/marca.css")
    assert not es_ruta_de_cliente("templates/stories/assets/logo.png")
    assert not es_ruta_de_cliente("templates/stories/sub/alerta.html")


def test_es_ruta_de_cliente_stories_solo_json():
    """En data/stories/ solo los archivos .json corresponden a payloads de cliente."""
    assert not es_ruta_de_cliente("data/stories/tanda1/grafico.png")
    assert not es_ruta_de_cliente("data/stories/tanda1/resumen.txt")


def test_es_ruta_de_cliente_casos_borde():
    """Casos de ruta vacía, tipos no válidos o carpetas contenedor sin archivo."""
    assert not es_ruta_de_cliente("")
    assert not es_ruta_de_cliente(None)  # ty: ignore[arg-type]
    assert not es_ruta_de_cliente(123)  # ty: ignore[arg-type]
    assert not es_ruta_de_cliente("data/mensajes")
    assert not es_ruta_de_cliente("data/stories")


# ---------------------------------------------------------------------------
# ticker_valido
# ---------------------------------------------------------------------------


def test_ticker_valido_activos_nucleo():
    """Activos del catálogo principal deben ser aprobados."""
    assert ticker_valido("USDCLP").ok
    assert ticker_valido("XAUUSD").ok
    assert ticker_valido("US100.spot").ok
    assert ticker_valido("WTI.spot").ok
    assert ticker_valido("#AAPL").ok


def test_ticker_valido_con_sufijo_broker_sugiere_exacto():
    """Un ticker sin sufijo debe fallar indicando el símbolo exacto del broker."""
    v = ticker_valido("US100")
    assert not v.ok
    assert v.motivo == "ticker_desconocido"
    assert "US100.spot" in v.detalle
    assert v.ubicacion == "US100"

    v_etf = ticker_valido("SPY")
    assert not v_etf.ok
    assert v_etf.motivo == "ticker_desconocido"
    assert "SPY.US" in v_etf.detalle

    v_accion = ticker_valido("AAPL")
    assert not v_accion.ok
    assert v_accion.motivo == "ticker_desconocido"
    assert "#AAPL" in v_accion.detalle


def test_ticker_valido_desconocido_absoluto():
    """Un ticker que no existe en absoluto debe ser rechazado sin sugerencia errónea."""
    v = ticker_valido("INVENTADO")
    assert not v.ok
    assert v.motivo == "ticker_desconocido"
    assert "INVENTADO" in v.detalle
    assert v.ubicacion == "INVENTADO"


def test_ticker_valido_vacio():
    """Un ticker vacío debe fallar como ticker_desconocido."""
    v = ticker_valido("")
    assert not v.ok
    assert v.motivo == "ticker_desconocido"


def test_ticker_valido_error_interno_falla_catalogo():
    """Si la carga del catálogo falla, debe retornar error_interno sin lanzar."""
    with patch.object(nombres, "_catalogo_tickers", side_effect=RuntimeError("catálogo roto")):
        v = ticker_valido("USDCLP")
        assert not v.ok
        assert v.motivo == "error_interno"
        assert "catálogo roto" in v.detalle


# ---------------------------------------------------------------------------
# marco_canonico
# ---------------------------------------------------------------------------


def test_marco_canonico_verifica_contra_import_real():
    """Verifica cada etiqueta canónica contra el import real de pipeline_carrusel."""
    etiquetas_canonicas = [e for e, _ in pipeline_carrusel.MARCOS_CANONICOS.values()]
    assert len(etiquetas_canonicas) == 4

    for etiqueta in etiquetas_canonicas:
        v = marco_canonico(etiqueta)
        assert v.ok, f"La etiqueta {etiqueta} debería ser aprobada"
        assert v.motivo == ""


def test_marco_canonico_no_canonico_falla():
    """Temporalidades no canónicas o claves internas de MT5 deben fallar."""
    v1 = marco_canonico("2H")
    assert not v1.ok
    assert v1.motivo == "marco_no_canonico"
    assert v1.ubicacion == "2H"

    v2 = marco_canonico("H1")  # H1 es la clave MT5, la etiqueta de Story es 1H
    assert not v2.ok
    assert v2.motivo == "marco_no_canonico"

    v3 = marco_canonico("1h")  # Minúscula no permitida
    assert not v3.ok
    assert v3.motivo == "marco_no_canonico"


def test_marco_canonico_vacio():
    """Etiqueta vacía debe fallar como marco_no_canonico."""
    v = marco_canonico("")
    assert not v.ok
    assert v.motivo == "marco_no_canonico"


def test_marco_canonico_error_interno_si_falla_import():
    """Si el módulo de pipeline no está disponible, retorna error_interno sin lanzar."""
    with patch.object(nombres, "pipeline_carrusel", None):
        v = marco_canonico("1H")
        assert not v.ok
        assert v.motivo == "error_interno"


# ---------------------------------------------------------------------------
# alias_de_canal_valido
# ---------------------------------------------------------------------------


def test_alias_de_canal_slug_directo():
    """Los slugs de carpeta declarados en whatsapp_grupos.json son válidos."""
    assert alias_de_canal_valido("01_macro_y_apertura").ok
    assert alias_de_canal_valido("02_forex_divisas").ok
    assert alias_de_canal_valido("03_commodities_materias_primas").ok
    assert alias_de_canal_valido("04_indices_bursatiles").ok
    assert alias_de_canal_valido("05_acciones_etfs").ok
    assert alias_de_canal_valido("06_criptoactivos").ok
    assert alias_de_canal_valido("07_oportunidades_cuantitativas").ok


def test_alias_de_canal_lenguaje_natural_resuelve():
    """Alias en lenguaje natural deben resolver exitosamente."""
    assert alias_de_canal_valido("metales").ok
    assert alias_de_canal_valido("oro").ok
    assert alias_de_canal_valido("forex").ok
    assert alias_de_canal_valido("cripto").ok
    assert alias_de_canal_valido("acciones").ok


def test_alias_de_canal_insensible_mayusculas_y_tildes():
    """La resolución de alias debe ser insensible a mayúsculas y tildes."""
    assert alias_de_canal_valido("METALES").ok
    assert alias_de_canal_valido("energía").ok
    assert alias_de_canal_valido("energia").ok
    assert alias_de_canal_valido("ENERGÍA").ok
    assert alias_de_canal_valido("índices").ok
    assert alias_de_canal_valido("indices").ok
    assert alias_de_canal_valido("ÍNDICES").ok
    assert alias_de_canal_valido("petróleo").ok
    assert alias_de_canal_valido("petroleo").ok
    assert alias_de_canal_valido("señal").ok
    assert alias_de_canal_valido("senal").ok


def test_alias_de_canal_desconocido_falla():
    """Un alias no registrado debe fallar con alias_de_canal_desconocido."""
    v = alias_de_canal_valido("canal_fantasma")
    assert not v.ok
    assert v.motivo == "alias_de_canal_desconocido"
    assert v.ubicacion == "canal_fantasma"


def test_alias_de_canal_vacio():
    """Un alias vacío debe fallar con alias_de_canal_desconocido."""
    v = alias_de_canal_valido("")
    assert not v.ok
    assert v.motivo == "alias_de_canal_desconocido"


def test_alias_de_canal_error_interno_si_falla_lectura():
    """Si la carga del JSON falla, debe devolver error_interno sin lanzar."""
    with patch.object(nombres, "_cargar_alias_canales", side_effect=IOError("disco dañado")):
        v = alias_de_canal_valido("metales")
        assert not v.ok
        assert v.motivo == "error_interno"
        assert "disco dañado" in v.detalle
