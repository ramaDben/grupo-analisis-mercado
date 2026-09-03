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
    regimenes = glosario.get("regimenes") or {}

    # Se pregunta por la TRADUCCIÓN y no por la clave exacta: el glosario ya no
    # lleva la temporalidad pegada, así que exigir la clave literal volvería a
    # obligar a una entrada por marco.
    sin_traducir = set()
    for activo in datos.get("activos", {}).values():
        for token in (activo.get("setups_permitidos") or []) + (activo.get("setups_prohibidos") or []):
            if not pi._setup_traducible(token, glosario):
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
def test_un_setup_se_traduce_en_cualquier_temporalidad(glosario):
    """El motor mira la temporalidad que necesita. Si el glosario obliga a una
    clave por marco, el primer H4 que emita llega al cliente como token."""
    for tf in ("M15", "H1", "H4", "D1"):
        token = f"FADE_SUPPORT_RESISTANCE_{tf}"
        texto = pi._traducir_setup(token, glosario)
        assert texto != token, f"{token} quedó sin traducir"
        assert not _TOKEN_MAQUINA.findall(texto), texto


def test_el_periodo_de_una_media_se_expresa_en_la_unidad_de_su_temporalidad(glosario):
    """EMA20 en 1 hora son 20 horas; en 15 minutos son 20 velas de 15 minutos.
    La cifra es la misma, la unidad no."""
    assert "20 horas" in pi._traducir_setup("PULLBACK_EMA20_H1", glosario)
    assert "20 velas de 15 minutos" in pi._traducir_setup("PULLBACK_EMA20_M15", glosario)


def test_un_setup_inventado_sigue_sin_traducirse(glosario):
    """La tolerancia por temporalidad no puede tapar un setup que nadie escribió."""
    assert pi._traducir_setup("SETUP_QUE_NO_EXISTE_H1", glosario) == "SETUP_QUE_NO_EXISTE_H1"


def test_la_unidad_del_periodo_concuerda_en_genero_con_la_frase(glosario):
    """Los textos dicen "las últimas N {periodos}": una unidad masculina deja
    "las últimas 20 días", que se lee como un error de redacción."""
    for tf in ("M1", "M5", "M15", "M30", "H1", "H4", "H12", "D1", "W1", "MN1"):
        texto = pi._traducir_setup(f"PULLBACK_EMA20_{tf}", glosario)
        assert "las últimas" in texto, texto
        for masculino in ("días", "meses", "minutos", "segundos"):
            assert f"últimas 20 {masculino}" not in texto, texto


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


def test_la_lectura_por_activo_dice_hasta_donde_vale_cada_sesgo(glosario):
    """El informe decia el sesgo sin su borde: "lo vemos alcista" y nada mas. El
    director pidio sesgo CON su vigencia, y el PDF de apertura es donde mas
    sirve."""
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None,
        {"WTI": _VIG_NIVEL_WTI}, _DIGITS,
    )

    assert "Hasta dónde vale" in salida
    assert "91,745" in salida


def test_los_activos_agrupados_conservan_su_nivel_propio(glosario):
    """WTI y Brent se agrupan porque su lectura es palabra por palabra la misma,
    y eso no cambia: lo que cambia es que cada uno tiene SU nivel. Si el bloque
    agrupado publicara uno solo, el otro saldria con el borde del vecino."""
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None,
        {"WTI": _VIG_NIVEL_WTI, "BRENT": _VIG_NIVEL_BRENT}, _DIGITS,
    )

    assert "Petróleo WTI y Petróleo Brent" in salida, "el agrupamiento se mantiene"
    assert "91,745" in salida and "97,135" in salida


def test_un_activo_en_rango_dice_entre_que_bordes_vale(glosario):
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None, {"USDCLP": _VIG_RANGO}, _DIGITS,
    )

    assert "entre 928,90 y 936,20" in salida
    assert "936,20" in salida


def test_un_sesgo_invalidado_lo_dice_en_el_informe(glosario):
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None,
        {"USDCLP": {**_VIG_NIVEL_WTI, "nivel": 932.69, "vigente": False}},
        {"USDCLP": 2},
    )

    assert "ya no vale" in salida
    assert "932,69" in salida


def test_sin_vigencia_el_informe_no_inventa_un_borde(glosario):
    """Compatibilidad hacia atras y fail-closed: sin terminal MT5 no hay anclas
    del Chandelier, y el informe sale sin el bloque en vez de no salir."""
    salida = pi._lectura_por_activo(_SNAP_CRUDO, glosario)

    assert "Hasta dónde vale" not in salida
    assert "Petróleo WTI" in salida, "el resto de la lectura sale igual"


def test_la_vigencia_no_filtra_tokens_del_motor_al_informe(glosario):
    """La misma guardia de voz que el resto de la seccion: `Chandelier`,
    `TRAILING_STOP_ASYMMETRIC` y `LARGO` son vocabulario del motor."""
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None,
        {"WTI": _VIG_NIVEL_WTI, "USDCLP": _VIG_RANGO}, _DIGITS,
    )

    assert not _TOKEN_MAQUINA.findall(salida)
    for jerga in ("Chandelier", "LARGO", "CORTO", "trailing", "ATR"):
        assert jerga not in salida, f"'{jerga}' es vocabulario de mesa, no de cliente"


def test_las_cifras_de_la_vigencia_respetan_los_decimales_del_activo(glosario):
    """El crudo va con 3 decimales y el dolar con 2, igual que en toda pieza del
    proyecto. Y el separador decimal en Chile es la coma."""
    salida = pi._lectura_por_activo(
        _SNAP_CRUDO, glosario, None,
        {"WTI": _VIG_NIVEL_WTI, "USDCLP": _VIG_RANGO}, _DIGITS,
    )

    assert "91,745" in salida and "91.745" not in salida
    assert "928,90" in salida, "no se truncan los ceros finales"


def test_resolver_vigencias_sin_terminal_no_lanza_y_avisa():
    """Mismo criterio que los graficos: un informe sin este bloque sigue siendo
    un informe, mientras que uno que se cae deja al director sin nada a las ocho
    de la manana. Cada ausencia queda dicha en los avisos."""
    vigencias, avisos = pi.resolver_vigencias({"activos": {}})

    assert vigencias == {}
    assert isinstance(avisos, list)


# ─────────────────────────────────────────────────────────────────────────────
# El parentesis de la etiqueta significa dos cosas, no una
# ─────────────────────────────────────────────────────────────────────────────
def test_un_parentesis_de_causa_se_traduce_y_no_se_lee_como_un_rango(glosario):
    """El defecto que salio a la luz al agregar la vigencia, y estaba en el PDF.

    `_frase_sesgo` asumia que todo parentesis de la etiqueta era un rango de
    precios, asi que a `ALCISTA MODERADO USD (ESTANFLACION GLOBAL)` le ponia
    delante la palabra "entre" y publicaba **"lo vemos con mas probabilidad de
    subir, entre ESTANFLACION GLOBAL"**. Seis de las quince etiquetas del motor
    traen la CAUSA entre parentesis, no un rango.
    """
    frase = pi._frase_sesgo(
        {"sesgo_etiqueta": "ALCISTA MODERADO USD (ESTANFLACION GLOBAL)"}, glosario
    )

    assert "entre ESTANFLACION" not in frase
    assert "ESTANFLACION" not in frase, "vocabulario de maquina en texto de cliente"
    assert "más probabilidad de subir" in frase


def test_un_parentesis_de_rango_sigue_diciendo_entre_que_precios(glosario):
    """La otra mitad del contrato: `NEUTRAL / RANGO (912 - 925)` si es un rango y
    los numeros son justo lo que el cliente necesita de ahi. Se reconoce por el
    guion separador, no por tener digitos: `(S1 - R1)` tambien los tiene."""
    frase = pi._frase_sesgo(
        {"sesgo_etiqueta": "NEUTRAL / RANGO (912 - 925)"}, glosario
    )

    assert "entre 912 y 925" in frase


def test_el_usd_de_la_etiqueta_no_llega_al_cliente(glosario):
    """`ALCISTA USD` en la ficha del USD/CLP dice que el sesgo es del dolar, cosa
    que el nombre del par ya dice. Repetirlo suena a sigla sin explicar."""
    frase = pi._frase_sesgo(
        {"sesgo_etiqueta": "BAJISTA USD (PESO FUERTE POR GOLDILOCKS)"}, glosario
    )

    assert "USD" not in frase
    assert "GOLDILOCKS" not in frase


def test_toda_etiqueta_de_sesgo_del_motor_sale_en_voz_de_cliente(glosario):
    """Contrato de nombres sobre las quince etiquetas que el motor puede emitir.

    El barrido de vocabulario que ya existia mira `setups` y el codigo de
    regimen del snapshot de HOY, asi que no veia ni las etiquetas de sesgo ni las
    catorce que hoy no estan activas. Este las saca del codigo del motor, que es
    donde estan todas.
    """
    fuente = (RAIZ / "scripts" / "macro_bias_engine.py").read_text(encoding="utf-8")
    etiquetas = set(re.findall(r'sesgo_etiqueta = "([^"]+)"', fuente))

    assert len(etiquetas) >= 10, "el regex dejo de encontrar las etiquetas"
    gritos = {}
    for etiqueta in etiquetas:
        if etiqueta == "DATOS_INCOMPLETOS":
            continue          # ese caso no se publica: el activo sale sin lectura
        frase = pi._frase_sesgo({"sesgo_etiqueta": etiqueta}, glosario)
        restos = re.findall(r"\b[A-ZÁÉÍÓÚÑ]{4,}\b", frase)
        if restos:
            gritos[etiqueta] = restos

    assert not gritos, (
        "etiquetas que llegan al informe en vocabulario de maquina: "
        + "; ".join(f"{k} -> {v}" for k, v in sorted(gritos.items()))
        + ". Traducir el matiz en data/glosario_motor.json."
    )


def test_un_intensificador_no_se_confunde_con_la_direccion(glosario):
    """`FUERTE ALCISTA` es el sesgo del Oro hoy, y el parser tomaba la primera
    palabra como direccion: salia "Hoy lo vemos fuerte, alcista". La direccion es
    alcista y "fuerte" es su intensidad, no otra direccion."""
    frase = pi._frase_sesgo({"sesgo_etiqueta": "FUERTE ALCISTA"}, glosario)

    assert "fuerte, alcista" not in frase
    assert "más probabilidad de subir" in frase
    assert frase.count(",") == 0, "una direccion con intensidad es una sola frase"


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
