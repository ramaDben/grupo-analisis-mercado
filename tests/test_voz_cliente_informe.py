"""Guardia de voz: ningún token interno del motor llega a un informe de cliente.

Existe porque ya pasó. La primera versión del informe de apertura volcaba
`setups_permitidos` y `setups_prohibidos` del snapshot directamente a una tabla, y
salieron a un PDF `SHORT_AGRESIVO`, `PULLBACK_EMA50_H1`, `FADE_SUPPORT_RESISTANCE_M15`
y `R2_GOLDILOCKS_EXPANSION`. No son términos técnicos difíciles: son nombres de
variable del motor, escritos para que el motor los compare entre sí.

El repo tiene una cláusula explícita de lenguaje ciudadano (la skill
`generar-reporte-editorial` habla de "informes ciudadanos" y "máxima claridad
pedagógica") y la regla de los 30 segundos en `CLAUDE.md`. Ninguna de las dos se
puede verificar leyendo, porque el defecto entra de a un token por vez.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import pipeline_informe as pi  # noqa: E402

# Un token de máquina: MAYÚSCULAS con guion bajo, de cinco caracteres o más.
# `EE.UU.` no califica (tiene puntos), `PDF` tampoco (corto y sin guion bajo).
_TOKEN_MAQUINA = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]{3,}\b")

SNAPSHOT = {
    "regimen_macro_global": {"codigo": "R2_GOLDILOCKS_EXPANSION", "nombre": "Goldilocks"},
    "as_of_utc": "2026-08-25T21:55:42.222379+00:00",
    "activos": {
        "USDCLP": {
            "nombre": "Dólar / Peso Chileno",
            "sesgo_etiqueta": "NEUTRAL / RANGO (912 - 925)",
            "setups_permitidos": ["FADE_SUPPORT_RESISTANCE_M15", "MEAN_REVERSION_RSI_H1"],
            "setups_prohibidos": ["BREAKOUT_CHASE_LONG", "GRID_SIN_STOP"],
        },
        "XAUUSD": {
            "nombre": "Oro Spot",
            "sesgo_etiqueta": "ALCISTA MODERADO",
            "setups_permitidos": ["PULLBACK_EMA50_H1", "BREAKOUT_DONCHIAN_H1"],
            "setups_prohibidos": ["SHORT_AGRESIVO"],
        },
    },
}


@pytest.fixture
def glosario() -> dict:
    return pi.cargar_glosario_motor()


# ─────────────────────────────────────────────────────────────────────────────
# La guardia principal
# ─────────────────────────────────────────────────────────────────────────────
def test_la_lectura_por_activo_no_deja_pasar_ningun_token_del_motor(glosario):
    salida = pi._lectura_por_activo(SNAPSHOT, glosario)
    fugas = _TOKEN_MAQUINA.findall(salida)
    assert not fugas, (
        "tokens internos del motor en texto de cliente: "
        + ", ".join(sorted(set(fugas)))
        + ". Agregarlos a data/glosario_motor.json."
    )


def test_el_regimen_se_explica_sin_su_codigo_interno(glosario):
    salida = pi._bloque_regimen(SNAPSHOT["regimen_macro_global"], glosario)
    assert "R2_GOLDILOCKS_EXPANSION" not in salida
    assert not _TOKEN_MAQUINA.findall(salida)
    assert "la economía crece" in salida.lower()


def test_todo_el_vocabulario_que_el_motor_puede_emitir_esta_traducido(glosario):
    """Barrido sobre el snapshot REAL, no sobre el de prueba.

    Un token que el motor emite hoy y que nadie tradujo llegaría al informe tal
    cual. Este test lo caza en la suite en vez de en el PDF.
    """
    ruta = RAIZ / "data central" / "DATA DRIVERS USDCLP" / "macro_bias_output.json"
    if not ruta.is_file():
        pytest.skip("no hay snapshot del motor en esta máquina")

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    setups = glosario.get("setups") or {}
    regimenes = glosario.get("regimenes") or {}

    sin_traducir = set()
    for activo in datos.get("activos", {}).values():
        for token in (activo.get("setups_permitidos") or []) + (activo.get("setups_prohibidos") or []):
            if token not in setups:
                sin_traducir.add(token)

    codigo = (datos.get("regimen_macro_global") or {}).get("codigo")
    if codigo and codigo not in regimenes:
        sin_traducir.add(codigo)

    assert not sin_traducir, (
        "el motor emite tokens que glosario_motor.json no traduce: "
        + ", ".join(sorted(sin_traducir))
    )


def test_los_cinco_regimenes_del_playbook_tienen_traduccion(glosario):
    """Si el mercado cambia de régimen un domingo, el informe del lunes no puede
    salir con un código sin traducir."""
    regimenes = glosario.get("regimenes") or {}
    for codigo in ("R0_CALMA_RANGO", "R1_SHOCK_INFLACIONARIO", "R2_GOLDILOCKS_EXPANSION",
                   "R3_ESTANFLACION_SHOCK", "R4_RECESION_VUELO_CALIDAD"):
        assert codigo in regimenes, f"falta el régimen {codigo}"
        entrada = regimenes[codigo]
        assert entrada.get("nombre") and entrada.get("explicacion") and entrada.get("que_implica")
        assert not _TOKEN_MAQUINA.findall(entrada["nombre"] + entrada["explicacion"])


# ─────────────────────────────────────────────────────────────────────────────
# Las tablas, que es donde se coló la taquigrafía de mesa de dinero
# ─────────────────────────────────────────────────────────────────────────────
def test_la_tabla_de_la_curva_no_usa_taquigrafia_de_mesa():
    """`Δ`, `bps` y `2s10s` son estándar del oficio: quien los conoce no los
    necesita, y quien no, se detiene en ellos antes de llegar al número."""
    curva = {
        "series": {"DGS10": {"nombre": "US 10-Year Treasury Yield", "nivel_pct": 4.7,
                             "delta_1d_bps": -4.0, "delta_5d_bps": -2.0,
                             "fecha_dato": "2026-08-24"}},
        "spread_2s10s": {"nivel_pct": 0.46, "delta_1d_bps": -4.0, "delta_5d_bps": -7.0,
                         "fecha_dato": "2026-08-24"},
    }
    salida = pi._tabla_curva(curva)
    for prohibido in ("Δ", "bps", "2s10s", "Treasury Yield"):
        assert prohibido not in salida, f"'{prohibido}' no va en un informe de cliente"
    assert "puntos base" in salida
    assert "Bono del Tesoro a 10 años" in salida


def test_los_porcentajes_van_en_notacion_chilena_y_con_dos_decimales():
    """4.7 y 4.24 en la misma columna se leen como si uno tuviera menos precisión
    que el otro. Y el separador decimal en Chile es la coma."""
    assert pi._pct_es(4.7) == "4,70%"
    assert pi._pct_es(4.24) == "4,24%"
    assert pi._pct_es(None) == "sin dato"


def test_la_agenda_descarta_el_nombre_en_ingles_pero_conserva_el_periodo():
    """Dos filas del mismo indicador tienen que distinguirse, pero por su período
    y no por un nombre en inglés que el cliente no va a leer."""
    anual = pi._nombre_indicador({
        "nombre": "S&P/CS HPI Composite - 20 n.s.a. (YoY) (Jun)",
        "diccionario": {"nombre_es": "Índice de precios de vivienda Case-Shiller"},
    })
    mensual = pi._nombre_indicador({
        "nombre": "S&P/CS HPI Composite - 20 n.s.a. (MoM) (Jun)",
        "diccionario": {"nombre_es": "Índice de precios de vivienda Case-Shiller"},
    })
    assert "S&P/CS" not in anual and "S&P/CS" not in mensual
    assert "variación anual" in anual
    assert "variación mensual" in mensual
    assert anual != mensual, "dos filas identicas no se pueden distinguir"
    assert "junio" in anual


def test_un_indicador_fuera_del_glosario_conserva_su_nombre_de_fuente():
    """Es la señal `glosario_pendiente` funcionando: hay una sigla nueva por
    agregar, no un error que haya que esconder."""
    ev = {"nombre": "Richmond Manufacturing Index (Aug)", "glosario_pendiente": True}
    assert pi._nombre_indicador(ev) == "Richmond Manufacturing Index (Aug)"


# ─────────────────────────────────────────────────────────────────────────────
# Tipografía
# ─────────────────────────────────────────────────────────────────────────────
def test_el_informe_de_cliente_pide_una_escala_de_letra_mayor():
    """El maquetador trae el cuerpo en 7,5-7,9 pt, bajo el piso de legibilidad
    impresa. El informe de apertura lo lee un cliente, así que pasa `--escala`."""
    fuente = (RAIZ / "scripts" / "pipeline_informe.py").read_text(encoding="utf-8")
    assert "--escala" in fuente, "el informe de cliente perdio la escala tipografica"


def test_el_escalado_respeta_los_titulares_de_portada():
    """Multiplicar el titular de 46 px rompería el encuadre de la portada."""
    ruta = RAIZ / ".agents" / "skills" / "generar-reporte-editorial" / "scripts" / "generar_pdf.py"
    sys.path.insert(0, str(ruta.parent))
    try:
        from generar_pdf import _escalar_tipografia  # noqa: PLC0415
    except ImportError:  # pragma: no cover - depende de playwright/markdown
        pytest.skip("generar_pdf necesita playwright y markdown")

    css = "a{font-size: 10px} b{font-size:46px}"
    escalado = _escalar_tipografia(css, 1.4)
    assert "14.0px" in escalado, "el cuerpo tiene que escalar"
    assert "46px" in escalado, "el titular de portada NO escala"
    assert _escalar_tipografia(css, 1.0) == css, "escala 1.0 no cambia nada"
