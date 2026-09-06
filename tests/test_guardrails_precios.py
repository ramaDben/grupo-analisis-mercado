"""Tests para scripts/guardrails/precios.py.

Cubre las reglas de decimales de broker y la prohibición de hardcodear precios (Regla 1).
Cada regla y excepción cuenta con pruebas explícitas que documentan y previenen
los modos de falla históricos del proyecto.
"""

import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from guardrails.precios import (  # noqa: E402
    decimales_correctos,
    digits_de,
    formatear,
    revisar_texto,
    sin_precio_literal,
)


# =============================================================================
# 1. Tests para digits_de
# =============================================================================


def test_digits_de_activos_conocidos():
    """Verifica los digits canónicos declarados en config/activos.json."""
    assert digits_de("USDCLP") == 2
    assert digits_de("COPPER") == 0
    assert digits_de("XAUUSD") == 2
    assert digits_de("USDJPY") == 3
    assert digits_de("EURUSD") == 5
    assert digits_de("WTI.spot") == 3
    assert digits_de("BRENT.spot") == 3
    assert digits_de("US100.spot") == 2


def test_digits_de_variantes_de_simbolo():
    """Verifica que reconozca variantes con barra, sin barra, o clave complementaria."""
    assert digits_de("USD/CLP") == 2
    assert digits_de("XAU/USD") == 2
    assert digits_de("COBRE") == 0
    assert digits_de("US100") == 2
    assert digits_de("#AAPL") == 2
    assert digits_de("AAPL") == 2


def test_digits_de_activo_inexistente():
    """Activos no registrados en el catálogo deben devolver None."""
    assert digits_de("ACTIVO_INVENTADO") is None
    assert digits_de("") is None


def test_digits_de_case_insensitive():
    """Tolera minúsculas al consultar activos del catálogo."""
    assert digits_de("usdclp") == 2
    assert digits_de("copper") == 0


# =============================================================================
# 2. Tests para formatear
# =============================================================================


def test_formatear_conserva_ceros_finales():
    """Nunca trunca ceros al final: 889.60 no debe transformarse en 889.6."""
    assert formatear(889.6, "USDCLP") == "889.60"
    assert formatear(163.7, "USDJPY") == "163.700"
    assert formatear(192.5, "AAPL") == "192.50"


def test_formatear_cobre_redondea_entero():
    """El Cobre es el único con digits = 0 y se formatea a entero."""
    assert formatear(14197.0, "COPPER") == "14197"
    assert formatear(14197.4, "COPPER") == "14197"
    assert formatear(14197.8, "COPPER") == "14198"


def test_formatear_otros_activos():
    """Formatea respetando los digits específicos de commodities y divisas."""
    assert formatear(4539.72, "XAUUSD") == "4539.72"
    assert formatear(90.181, "WTI.spot") == "90.181"
    assert formatear(1.08500, "EURUSD") == "1.08500"


def test_formatear_activo_desconocido_retorna_none():
    """Si el ticker no existe en el catálogo, devuelve None para evitar adivinaciones."""
    assert formatear(100.5, "ACTIVO_FANTASMA") is None


# =============================================================================
# 3. Tests para decimales_correctos
# =============================================================================


def test_decimales_usdclp_falta_cero_falla():
    """USDCLP con $889.6 falla (digits = 2, falta un cero)."""
    v = decimales_correctos("El tipo de cambio cerró en $889.6 tras la sesión.", "USDCLP")
    assert not v.ok
    assert v.motivo == "decimales_incorrectos"
    assert v.ubicacion is not None
    assert "USDCLP" in v.ubicacion
    assert "$889.6" in v.ubicacion


def test_decimales_usdclp_correcto_pasa():
    """USDCLP con $889.60 pasa."""
    v = decimales_correctos("El tipo de cambio cerró en $889.60 tras la sesión.", "USDCLP")
    assert v.ok


def test_decimales_copper_entero_pasa_y_con_decimal_falla():
    """COPPER con $14197 pasa y con $14.197 falla: es el único con digits = 0."""
    v_ok = decimales_correctos("El Cobre Grado A cotiza en $14197 USD/t en terminal.", "COPPER")
    assert v_ok.ok

    v_err = decimales_correctos("El Cobre Grado A cotiza en $14.197 USD/t en terminal.", "COPPER")
    assert not v_err.ok
    assert v_err.motivo == "decimales_incorrectos"
    assert v_err.ubicacion is not None
    assert "COPPER" in v_err.ubicacion
    assert "$14.197" in v_err.ubicacion


def test_decimales_xauusd_separador_miles_pasa():
    """XAUUSD con $4,539.72 pasa: la coma es separador de miles, no decimal."""
    v = decimales_correctos("El oro al contado avanza hasta los $4,539.72 la onza.", "XAUUSD")
    assert v.ok


def test_decimales_us100_separador_miles_sin_dolar_pasa():
    """US100 con 30,350.01 pasa: punto decimal con coma de miles."""
    v = decimales_correctos("El índice Nasdaq cotiza en 30,350.01 puntos.", "US100.spot")
    assert v.ok


def test_decimales_entero_con_dolar_en_activo_con_decimales_falla():
    """Escribir $889 en USDCLP falla porque omite los dos decimales obligatorios (.00)."""
    v = decimales_correctos("USDCLP cotiza en $889 cerrado.", "USDCLP")
    assert not v.ok
    assert v.motivo == "decimales_incorrectos"
    assert "$889" in (v.ubicacion or "")


def test_decimales_porcentaje_no_se_confunde_con_precio():
    """Las variaciones porcentuales (ej. 0.5% o 4.70%) no son precios y no deben falsear el veredicto."""
    v = decimales_correctos("USDCLP sube 0.5% en la jornada y alcanza $889.60.", "USDCLP")
    assert v.ok


def test_decimales_activo_desconocido_aprueba():
    """Un ticker que no está en el catálogo aprueba (la validación de ticker pertenece a nombres.py)."""
    v = decimales_correctos("SIMBOLO_X cotiza en $123.456.", "SIMBOLO_X")
    assert v.ok


# =============================================================================
# 4. Tests para revisar_texto
# =============================================================================


def test_revisar_texto_linea_sin_ticker_no_se_juzga():
    """Una línea sin ningún ticker no se juzga en revisar_texto."""
    texto = "Hoy el mercado abrió con calma en la sesión asiática.\nLas tasas se mantienen estables."
    v = revisar_texto(texto)
    assert v.ok


def test_revisar_texto_multilinea_con_precios_correctos():
    """Texto de varios párrafos con tickers y precios correctos aprueba."""
    texto = (
        "Panorama de la mañana:\n"
        "USDCLP cotiza en $889.60 con sesgo comprador.\n"
        "En materias primas, XAUUSD se mantiene en $4,539.72.\n"
        "El Cobre consolida en $14197 USD/t."
    )
    v = revisar_texto(texto)
    assert v.ok


def test_revisar_texto_detecta_linea_infractora():
    """Detecta la línea infractora y falla con decimales_incorrectos."""
    texto = (
        "Apertura general.\n"
        "USDCLP opera en $889.6 por presión externa.\n"
        "XAUUSD avanza en $4,539.72."
    )
    v = revisar_texto(texto)
    assert not v.ok
    assert v.motivo == "decimales_incorrectos"
    assert "USDCLP" in (v.ubicacion or "")
    assert "$889.6" in (v.ubicacion or "")


def test_revisar_texto_dos_tickers_distintos_digits_pasa_si_coincide_con_alguno():
    """Si la línea nombra dos tickers con digits distintos, la cifra pasa si coincide con alguno."""
    # USDCLP tiene 2 digits, USDJPY tiene 3 digits
    # Con precio de 2 decimales (USDCLP)
    linea_2dec = "Monitoreamos la correlación entre USDCLP y USDJPY en torno a $889.60."
    assert revisar_texto(linea_2dec).ok

    # Con precio de 3 decimales (USDJPY)
    linea_3dec = "Monitoreamos la correlación entre USDCLP y USDJPY en 163.731."
    assert revisar_texto(linea_3dec).ok

    # Con precio que no coincide con ninguno (1 decimal)
    linea_invalida = "Monitoreamos USDCLP y USDJPY en $100.5."
    v = revisar_texto(linea_invalida)
    assert not v.ok
    assert v.motivo == "decimales_incorrectos"


def test_revisar_texto_vacio_aprueba():
    """Un texto vacío no contiene infracciones."""
    assert revisar_texto("").ok


# =============================================================================
# 5. Tests para sin_precio_literal
# =============================================================================


def test_sin_precio_literal_comentario_no_dispara():
    """Un precio dentro de un comentario no dispara precio_literal."""
    codigo = (
        "# USDCLP cotiza en $889.60 según el último snapshot\n"
        "simbolo = 'USDCLP'  # precio de referencia: 889.60\n"
        "def procesar():\n"
        "    pass\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_docstring_no_dispara():
    """Las líneas dentro de un docstring están exentas de precio_literal."""
    codigo = '''"""Módulo de análisis de USDCLP.

El soporte clave se observó en $889.60 y la resistencia en $895.00.
"""

def analizar(ticker: str):
    return ticker
'''
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_archivo_test_no_dispara():
    """Los archivos de test están exentos: sus fixtures requieren precios literales."""
    codigo_pytest = (
        "import pytest\n"
        "def test_levels():\n"
        "    USDCLP_PRICE = 889.60\n"
        "    assert USDCLP_PRICE > 0\n"
    )
    assert sin_precio_literal(codigo_pytest).ok

    codigo_def_test = (
        "def test_precio_cobre():\n"
        "    precio = 14197\n"
        "    assert precio == 14197\n"
    )
    assert sin_precio_literal(codigo_def_test).ok


def test_sin_precio_literal_excepcion_digits():
    """La declaración o asignación de digits no constituye precio literal."""
    codigo = (
        "USDCLP_DIGITS = 2\n"
        "config = {'ticker': 'USDCLP', 'digits': 2}\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_excepcion_indices():
    """El uso de índices numéricos junto a un ticker no es infracción."""
    codigo = (
        "fila = matriz_datos['USDCLP'][0]\n"
        "primer_item = lista_copper['COPPER'][1]\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_excepcion_anos():
    """Los años calendarios (ej. 2026) junto a un ticker no son precios."""
    codigo = (
        "YEAR_USDCLP = 2026\n"
        "fecha = f'USDCLP_{2026}_09_03'\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_excepcion_versiones():
    """Números de versión de modelos o APIs no son precios literales."""
    codigo = (
        "USDCLP_API_VERSION = '1.0'\n"
        "version = 2.0  # USDCLP modelo\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_excepcion_timeouts():
    """Timeouts o tiempos de espera en llamadas de datos no son precios."""
    codigo = (
        "client.fetch_data('USDCLP', timeout=30)\n"
        "wait_seconds = 5.0  # USDCLP polling\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_excepcion_entero_sin_dolar_digits_mayor_cero():
    """Cualquier número entero sin $ cuando el activo tiene digits > 0 no es precio."""
    codigo = (
        "lotes = 100  # orden USDCLP\n"
        "velas = 60  # USDCLP H1\n"
        "factor_espacio = 20  # USDCLP\n"
    )
    assert sin_precio_literal(codigo).ok


def test_sin_precio_literal_detecta_precio_flotante():
    """Detecta un precio flotante hardcodeado en código y falla con precio_literal."""
    codigo = "USDCLP_PRECIO = 889.60\n"
    v = sin_precio_literal(codigo)
    assert not v.ok
    assert v.motivo == "precio_literal"
    assert "USDCLP" in (v.ubicacion or "")
    assert "889.60" in (v.ubicacion or "")


def test_sin_precio_literal_detecta_precio_con_dolar():
    """Detecta un string con $ hardcodeado en código junto a un ticker."""
    codigo = "data = {'ticker': 'USDCLP', 'precio': '$889.60'}\n"
    v = sin_precio_literal(codigo)
    assert not v.ok
    assert v.motivo == "precio_literal"


def test_sin_precio_literal_detecta_cobre_entero():
    """Detecta el precio spot de Cobre ($14197 o 14197) hardcodeado en código."""
    codigo_con_dolar = "COPPER_VALOR = '$14197'\n"
    v1 = sin_precio_literal(codigo_con_dolar)
    assert not v1.ok
    assert v1.motivo == "precio_literal"

    codigo_entero = "COPPER_SPOT = 14197\n"
    v2 = sin_precio_literal(codigo_entero)
    assert not v2.ok
    assert v2.motivo == "precio_literal"


def test_sin_precio_literal_codigo_limpio_aprueba():
    """Código que consume el MCP o terminal en tiempo de ejecución pasa sin objeciones."""
    codigo = (
        "from market_data_mcp import get_asset_levels\n"
        "levels = get_asset_levels(ticker='USDCLP', timeframe='H1')\n"
        "spot = levels['actual']\n"
    )
    assert sin_precio_literal(codigo).ok


# =============================================================================
# 6. Tests para error_interno
# =============================================================================


def test_error_interno_si_falla_lectura_catalogo():
    """Si el catálogo de activos no se puede cargar, emite error_interno (fail-closed)."""
    with patch("guardrails.precios._cargar_catalogo", return_value=None):
        v1 = decimales_correctos("$889.60", "USDCLP")
        assert not v1.ok
        assert v1.motivo == "error_interno"

        v2 = revisar_texto("USDCLP cotiza en $889.60")
        assert not v2.ok
        assert v2.motivo == "error_interno"

        v3 = sin_precio_literal("USDCLP = 889.60")
        assert not v3.ok
        assert v3.motivo == "error_interno"
