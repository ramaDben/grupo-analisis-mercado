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

ACTIVOS = {
    "USDCLP": {
        "nombre": "Dólar / Peso Chileno", "digits": 2,
        "d1": {"price": 931.4, "s1": 925.0, "r1": 938.25, "ema_50": 928.0},
        "grafico": "graficos/usdclp.png",
    },
    "WTI.spot": {
        "nombre": "Petróleo WTI", "digits": 3,
        "d1": {"price": 88.1, "s1": 86.502, "r1": 90.25, "ema_50": 89.0},
    },
    "US100.spot": {"nombre": "Nasdaq 100", "digits": 2},
}


@pytest.fixture
def glosario() -> dict:
    return pi.cargar_glosario_informe()


# ─────────────────────────────────────────────────────────────────────────────
# La guardia principal
# ─────────────────────────────────────────────────────────────────────────────
def test_la_lectura_por_activo_no_deja_pasar_ningun_token_de_maquina():
    salida = pi._lectura_por_activo(ACTIVOS)
    assert not _TOKEN_MAQUINA.findall(salida), _TOKEN_MAQUINA.findall(salida)


def test_la_lectura_por_activo_respeta_los_decimales_y_la_direccion():
    salida = pi._lectura_por_activo(ACTIVOS)
    assert "931,40" in salida and "938,25" in salida, "USD/CLP va con 2 decimales"
    assert "86,502" in salida and "90,250" in salida, "WTI va con 3 decimales"
    assert "Lectura diaria alcista" in salida, "USD/CLP sobre su EMA 50"
    assert "Lectura diaria bajista" in salida, "WTI bajo su EMA 50"
    assert "![Dólar / Peso Chileno" in salida


def test_un_activo_sin_datos_del_terminal_lo_dice_y_no_inventa_cifras():
    salida = pi._lectura_por_activo(ACTIVOS)
    bloque = salida.split("### Nasdaq 100")[1]
    assert "Sin datos del terminal" in bloque
    assert pi.MARCA_EDITORIAL in bloque, "el espacio editorial queda igual"


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


def test_las_cifras_del_calendario_se_pasan_a_notacion_chilena():
    """Investing publica en notacion estadounidense: el punto es decimal y la
    coma es de miles. Copiado tal cual a un informe chileno, `1.600M` se lee como
    mil seiscientos millones cuando es un millon seiscientos mil, y `216,000`
    como doscientos dieciseis.

    Los dos separadores se intercambian en un solo paso: hacerlo en dos pisa el
    trabajo del primero y deja todo con el mismo separador.
    """
    assert pi._cifra_es("1.600M") == "1,600M"
    assert pi._cifra_es("216,000") == "216.000"
    assert pi._cifra_es("1,234.5") == "1.234,5"
    assert pi._cifra_es("-1.314M") == "-1,314M"
    assert pi._cifra_es("") == ""


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


# ─────────────────────────────────────────────────────────────────────────────
# El glosario no puede exigir una entrada por temporalidad
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# El "hasta donde" del sesgo en el informe
# ─────────────────────────────────────────────────────────────────────────────
_SNAP_CRUDO = {
    "regimen_macro_global": {"codigo": "R3_ESTANFLACION_SHOCK", "nombre": "Estanflación"},
    "activos": {
        "WTI": {
            "nombre": "Petróleo WTI", "sesgo_etiqueta": "ALCISTA POR SHOCK",
            "setups_permitidos": ["BREAKOUT_VOLATILITY_H1"], "setups_prohibidos": [],
        },
        "BRENT": {
            "nombre": "Petróleo Brent", "sesgo_etiqueta": "ALCISTA POR SHOCK",
            "setups_permitidos": ["BREAKOUT_VOLATILITY_H1"], "setups_prohibidos": [],
        },
        "USDCLP": {
            "nombre": "Dólar / Peso Chileno", "sesgo_etiqueta": "ALCISTA MODERADO",
            "setups_permitidos": ["PULLBACK_EMA20_H1"], "setups_prohibidos": [],
        },
    },
}

_VIG_NIVEL_WTI = {"gramatica": "NIVEL", "direccion": "LARGO", "nivel": 91.745,
                  "borde_inferior": None, "borde_superior": None, "vigente": True,
                  "multiplo_atr": 2.0, "lookback": 22,
                  "take_profit_tipo": "TRAILING_STOP_ASYMMETRIC"}
_VIG_NIVEL_BRENT = {**_VIG_NIVEL_WTI, "nivel": 97.135}
_VIG_RANGO = {"gramatica": "RANGO", "direccion": None, "nivel": None,
              "borde_inferior": 928.90, "borde_superior": 936.20, "vigente": True,
              "multiplo_atr": None, "lookback": None,
              "take_profit_tipo": "NIVEL_OPUESTO_CANAL"}

_DIGITS = {"WTI": 3, "BRENT": 3, "USDCLP": 2}


# ─────────────────────────────────────────────────────────────────────────────
# El parentesis de la etiqueta significa dos cosas, no una
# ─────────────────────────────────────────────────────────────────────────────
def test_dos_eventos_distintos_de_la_fed_no_salen_como_la_misma_linea(glosario):
    """El 2026-09-03 el calendario traia "Fed Waller Speaks" y "Fed's Balance
    Sheet", y los DOS salieron al canal como la misma linea: "Reserva Federal
    (banco central de EE.UU.)", sin cifra y sin decir que eran.

    El glosario agrupa por sigla, que es correcto para el nombre pero no alcanza
    para el tipo de evento. Una linea de agenda que no distingue un discurso de
    una hoja de balance no informa nada.
    """
    discurso = pi._nombre_indicador({
        "nombre": "Fed Waller Speaks",
        "diccionario": {"nombre_es": "Reserva Federal (banco central de EE.UU.)"},
    })
    balance = pi._nombre_indicador({
        "nombre": "Fed's Balance Sheet",
        "diccionario": {"nombre_es": "Reserva Federal (banco central de EE.UU.)"},
    })

    assert discurso != balance, "los dos eventos siguen saliendo identicos"
    assert "discurso" in discurso
    assert "hoja de balance" in balance


def test_los_tipos_de_evento_se_traducen_y_no_se_acumulan(glosario):
    """Un solo tipo por evento: `break` tras el primer patron. Sin eso, un
    "Fed Chair Powell Testimony Speech" acumularia dos matices contradictorios."""
    for fuente, esperado in (
        ("Fed Chair Powell Testimony", "comparecencia"),
        ("FOMC Meeting Minutes", "acta de la reunión"),
        ("ECB Press Conference", "conferencia de prensa"),
    ):
        salida = pi._nombre_indicador({
            "nombre": fuente,
            "diccionario": {"nombre_es": "Reserva Federal (banco central de EE.UU.)"},
        })
        assert esperado in salida, f"{fuente} no se tradujo: {salida}"
        assert salida.count("·") <= 2, f"se acumularon matices en {salida}"


def test_los_tres_indicadores_que_salian_en_ingles_ya_tienen_nombre():
    """`Trade Balance`, `Nonfarm Productivity` y `Unit Labor Costs` volvian del
    calendario con `glosario_pendiente` y salian tal cual a la agenda."""
    import json

    glosario_siglas = json.loads(
        (RAIZ / "data" / "glosario_siglas.json").read_text(encoding="utf-8")
    )
    for clave, nombre_es in (
        ("Trade Balance", "Balanza comercial"),
        ("Nonfarm Productivity", "Productividad laboral"),
        ("Unit Labor Costs", "Costo laboral unitario"),
    ):
        assert clave in glosario_siglas, f"{clave} sigue sin entrada en el glosario"
        assert glosario_siglas[clave]["nombre_es"] == nombre_es
        assert glosario_siglas[clave]["explicacion"], f"{clave} sin explicacion novata"


# ─────────────────────────────────────────────────────────────────────────────
# Los terminos del informe de empleo, que salieron en ingles a cinco canales
# ─────────────────────────────────────────────────────────────────────────────
TERMINOS_EMPLEO = [
    "Average Hourly Earnings",
    "Participation Rate",
    "Unemployment Rate",
    "U6 Unemployment Rate",
]


@pytest.mark.parametrize("termino", TERMINOS_EMPLEO)
def test_los_terminos_del_informe_de_empleo_se_traducen(termino):
    """El 2026-09-04 estos cuatro salieron en ingles a cinco canales.

    El fallback de `_nombre_indicador` devuelve el titulo de la fuente **sin
    ninguna marca** cuando el termino no esta en el glosario, asi que el ingles
    pasa como si estuviera traducido.
    """
    import json

    glosario = json.loads(
        (RAIZ / "data" / "glosario_siglas.json").read_text(encoding="utf-8")
    )
    encontrado = None
    for clave, entrada in glosario.items():
        if not isinstance(entrada, dict):
            continue
        candidatos = [clave, *entrada.get("titulos_ff", [])]
        if any(c.upper() == termino.upper() for c in candidatos):
            encontrado = entrada
            break
    assert encontrado, f"{termino} no esta en el glosario"
    assert encontrado.get("nombre_es"), f"{termino} sin nombre_es"
    assert encontrado.get("explicacion"), f"{termino} sin explicacion"


def test_el_sufijo_duplicado_de_la_fuente_se_colapsa():
    """El "(YoY) (YoY)" que se publico no lo produce nuestro codigo.

    El titulo crudo de Investing para el evento 1777 es literalmente
    `Average Hourly Earnings (YoY) (YoY)  (Aug)`. Sobrevivia **solo porque el
    termino faltaba en el glosario**: con la entrada presente, el bucle de
    `_SUFIJOS_ES` colapsa el sufijo a "variacion anual" y el duplicado desaparece.
    """
    import json

    glosario = json.loads(
        (RAIZ / "data" / "glosario_siglas.json").read_text(encoding="utf-8")
    )
    entrada = next(
        e for k, e in glosario.items()
        if isinstance(e, dict)
        and "Average Hourly Earnings" in [k, *e.get("titulos_ff", [])]
    )
    ev = {"nombre": "Average Hourly Earnings (YoY) (YoY)  (Aug)", "diccionario": entrada}
    nombre = pi._nombre_indicador(ev)
    assert "(YoY)" not in nombre, nombre
    assert "Average Hourly Earnings" not in nombre, nombre


def test_la_tasa_amplia_no_se_confunde_con_la_tasa_de_desempleo():
    """`Unemployment Rate` es substring de `U6 Unemployment Rate`.

    El matcher desempata por match mas largo (`calendar.py`), asi que un evento
    U6 tiene que resolver a la entrada U6 y no a la general. Es el mismo patron
    de colision que el codigo ya documenta para `Cushing Crude Oil Inventories`.
    """
    from market_data_mcp.tools import calendar as cal

    glosario = cal._cargar_glosario()
    entrada = cal._enganchar_glosario("U6 Unemployment Rate  (Aug)", glosario)
    assert entrada is not None
    assert "amplia" in entrada["nombre_es"].lower() or "U6" in entrada["nombre_es"]
