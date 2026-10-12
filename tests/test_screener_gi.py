"""Contrato del escáner de tandas: el score, los gates y el anclaje horario.

Todo con datos sintéticos y `analizador` inyectado: la suite no puede depender de
que MT5 esté abierto, y un test que solo pasa con el terminal encendido no
protege nada en CI.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import screener_gi as sc  # noqa: E402

NY = ZoneInfo("America/New_York")


# ─────────────────────────────────────────────────────────────────────────────
# Fábrica de datos sintéticos
# ─────────────────────────────────────────────────────────────────────────────
def h1_perfecto() -> dict:
    """Un H1 que dispara el máximo de los tres factores técnicos internos.

    Precio sobre EMA 20/50/100 (quiebre con estructura), ADX sobre 25, RSI en
    zona de expansión alcista, y R1 a más de 1,5 ATR de distancia.
    """
    return {
        "ticker": "TEST", "timeframe": "H1", "price": 100.0,
        "ema_20": 99.0, "ema_50": 98.0, "ema_100": 97.0,
        "s1": 95.0, "s2": 93.0, "r1": 104.0, "r2": 108.0,
        "atr_14": 2.0, "adx_14": 30.0, "rsi_14": 60.0,
        "macd_line": 0.5, "macd_signal": 0.2, "macd_hist": 0.3,
        "bb_upper": 103.0, "bb_mid": 99.5, "bb_lower": 96.0,
        "donchian_50_high": 105.0, "donchian_50_low": 92.0, "donchian_50_mid": 98.5,
        "trend": "ALCISTA",
        # `analizar_activo` siempre lo devuelve: sin el campo, el gate de banda no
        # puede distinguir un nivel medido de un respaldo por ATR.
        "niveles_origen": {"r1": "swing", "r2": "swing", "s1": "swing", "s2": "swing"},
    }


def h1_con_banda(banda: float, vela: float) -> dict:
    """Un H1 con la banda soporte-resistencia y la vela tipica que se le pidan.

    La vela tipica es `1,5 x ATR(H1)`, la misma cifra que la pieza publica como
    "Volatilidad tipica", asi que se despeja el ATR desde ella.
    """
    h1 = dict(h1_perfecto())
    h1["atr_14"] = vela / 1.5
    h1["s1"] = round(h1["price"] - banda / 2, 4)
    h1["r1"] = round(h1["price"] + banda / 2, 4)
    return h1


def d1_con_consumo(fraccion: float) -> dict:
    """Un D1 donde el rango de hoy consumió `fraccion` del ATR diario."""
    atr = 10.0
    d1 = dict(h1_perfecto())
    d1["timeframe"] = "D1"
    d1["atr_14"] = atr
    d1["rango_hoy"] = round(atr * fraccion, 2)
    d1["atr_restante_14"] = max(atr - atr * fraccion, 0.30 * atr)
    # Las EMA diarias lejos del precio, para que no se gatille el "rebote" de 25
    # puntos y el factor técnico pueda llegar a 35.
    d1["ema_50"] = 60.0
    d1["ema_100"] = 50.0
    return d1


def analizador_falso(h1: dict, d1: dict):
    """Devuelve un analizador que ignora el ticker y responde por timeframe."""
    def _analizar(ticker: str, timeframe: str) -> dict:
        base = dict(d1 if timeframe.upper() == "D1" else h1)
        base["ticker"] = ticker
        return base
    return _analizar


ACTIVO = {
    "ticker": "XAUUSD", "nombre": "Oro Spot", "clase": "forex_commodities",
    "categoria": "commodity", "digits": 2, "imagen": "assets/activos/oro.jpg",
}

AHORA = datetime(2026, 8, 25, 10, 30, tzinfo=NY)


# ─────────────────────────────────────────────────────────────────────────────
# El score y su techo
# ─────────────────────────────────────────────────────────────────────────────
def test_el_score_llega_a_100_y_no_topa_en_26_porque_no_se_multiplican_pesos():
    """La corrección central al plan de AGY.

    El plan multiplica pesos (0,35/0,25/0,20/0,20) por factores ya escalados a su
    máximo (35/25/20/20). Ese producto topa en 26,5 y ningún activo podía pasar
    de un cuarto del puntaje. Un activo que dispara los cuatro factores al máximo
    tiene que dar exactamente 100.
    """
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 23:00"}
    res = sc.evaluar_activo(
        ACTIVO, [evento], delta_ust_bps=None,
        ahora_santiago=AHORA.astimezone(sc.SANTIAGO),
        analizador=analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res, res.get("excluido")
    assert res["score"] == 100
    assert res["factores"]["tecnico"]["puntos"] == 35
    assert res["factores"]["catalizador"]["puntos"] == 25
    assert res["factores"]["espacio"]["puntos"] == 20
    assert res["factores"]["momentum"]["puntos"] == 20


def test_la_suma_de_los_maximos_de_los_factores_es_100():
    """Invariante de la escala: si alguien cambia un tope, el total deja de ser
    sobre 100 y todos los umbrales del plan pierden sentido."""
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 23:00"}
    res = sc.evaluar_activo(
        ACTIVO, [evento], None, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert sum(f["max"] for f in res["factores"].values()) == 100


def test_el_impulso_proyectado_es_una_vez_y_media_el_atr_de_h1():
    """Es el número que alimenta el bloque "Volatilidad típica" de la Story."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert res["impulso_adc_atr"] == pytest.approx(3.0)  # 1,5 x ATR 2,0


# ─────────────────────────────────────────────────────────────────────────────
# Los gates: exclusiones, no puntos
# ─────────────────────────────────────────────────────────────────────────────
def test_el_blackout_del_calendario_excluye_al_activo():
    """La segunda corrección: el plan ignora las ventanas de bloqueo y su factor
    catalizador premia justo al activo que recibe el dato."""
    # NFP a las 09:30 hora Chile, ventana -15/+30 -> 09:15 a 10:00.
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 09:30"}
    dentro = datetime(2026, 8, 25, 9, 40, tzinfo=sc.SANTIAGO)
    res = sc.evaluar_activo(
        ACTIVO, [evento], None, dentro,
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "blackout" in res["excluido"]
    assert "09:15" in res["excluido"] and "10:00" in res["excluido"]


def test_fuera_de_la_ventana_el_mismo_evento_no_bloquea_y_ademas_puntua():
    """El dato del día es catalizador una vez que pasó su ventana de absorción.
    Es la diferencia entre esperar la absorción y no publicar nunca."""
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 09:30"}
    fuera = datetime(2026, 8, 25, 11, 0, tzinfo=sc.SANTIAGO)
    res = sc.evaluar_activo(
        ACTIVO, [evento], None, fuera,
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res
    assert res["factores"]["catalizador"]["puntos"] == 25


def test_un_blackout_de_alcance_local_no_toca_a_los_demas_activos():
    """Un Imacec bloquea al peso, no al Oro."""
    evento = {"nombre": "Imacec (YoY)", "pais": "Chile", "hora_servidor": "2026-08-25 08:30"}
    dentro = datetime(2026, 8, 25, 8, 35, tzinfo=sc.SANTIAGO)
    analizador = analizador_falso(h1_perfecto(), d1_con_consumo(0.30))

    peso = sc.evaluar_activo({**ACTIVO, "ticker": "USDCLP"}, [evento], None, dentro, analizador)
    oro = sc.evaluar_activo(ACTIVO, [evento], None, dentro, analizador)

    assert "excluido" in peso and "blackout" in peso["excluido"]
    assert "excluido" not in oro


def test_el_agotamiento_del_atr_diario_excluye_en_vez_de_dar_cero_puntos():
    """El plan le pone 0 puntos al factor Espacio, pero 0 de 20 todavía deja 80
    disponibles: un activo sin recorrido puede ganar la tanda por técnica y
    catalizador. Agotado es agotado."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.95)),
    )
    assert "excluido" in res
    assert "95%" in res["excluido"]


def test_un_error_del_motor_excluye_con_su_codigo_y_no_revienta():
    """Contrato de error del MCP: nunca lanza, siempre explica."""
    def analizador_roto(ticker: str, timeframe: str) -> dict:
        return {"error": "MT5_UNAVAILABLE", "message": "MT5 no esta conectado."}

    res = sc.evaluar_activo(ACTIVO, [], None, AHORA.astimezone(sc.SANTIAGO), analizador_roto)
    assert "excluido" in res
    assert "MT5_UNAVAILABLE" in res["excluido"]


# ─────────────────────────────────────────────────────────────────────────────
# Anclaje horario: la tanda sale de Nueva York, no del reloj chileno
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("hora_ny, esperada", [
    ((10, 30), 1),
    ((14, 30), 2),
    ((16, 45), 3),
    ((10, 50), 1),   # veinte minutos tarde sigue siendo la tanda 1
    ((16, 0), 3),    # más cerca del pre-cierre (45 min) que de la tarde (90 min)
    ((13, 0), 2),    # a mitad de camino largo, gana la tarde
])
def test_la_tanda_se_deriva_de_la_hora_de_nueva_york(hora_ny, esperada):
    h, m = hora_ny
    assert sc.tanda_vigente(datetime(2026, 8, 25, h, m, tzinfo=NY)) == esperada


def test_la_misma_tanda_cae_a_distinta_hora_de_chile_segun_el_horario_de_verano():
    """El defecto que corrige el anclaje.

    Chile y EE.UU. cambian de horario en sentido opuesto, así que el desfase se
    mueve dos veces al año. La tanda 3 anclada a las 16:45 de Nueva York es
    16:45 en Chile en agosto y 18:45 en enero: un cronograma escrito en hora
    chilena describiría en enero un mercado que ya cerró.
    """
    agosto = sc.hora_chile_de_tanda(3, datetime(2026, 8, 25, 12, 0, tzinfo=NY))
    enero = sc.hora_chile_de_tanda(3, datetime(2027, 1, 15, 12, 0, tzinfo=NY))
    assert agosto != enero, "si coinciden, el anclaje a Nueva York no esta haciendo nada"
    assert agosto == "16:45"
    assert enero == "18:45"


# ─────────────────────────────────────────────────────────────────────────────
# Universo y repeticiones
# ─────────────────────────────────────────────────────────────────────────────
def test_el_universo_renderizable_es_un_subconjunto_del_completo():
    """`--solo-renderizables` filtra por presencia de `imagen`, que es el
    interruptor del activo: sin `.jpg` en disco la Story no se puede rendir."""
    completo = sc.cargar_universo(solo_renderizables=False)
    renderizable = sc.cargar_universo(solo_renderizables=True)

    assert len(renderizable) < len(completo), "hoy faltan imagenes; si no, revisar el filtro"
    fijos = set(sc.cobertura_fija())
    assert all(a["imagen"] or a["ticker"] in fijos for a in renderizable)
    tickers_completo = {a["ticker"] for a in completo}
    assert {a["ticker"] for a in renderizable} <= tickers_completo


def test_el_universo_completo_cubre_las_siete_clases_del_plan():
    """El heptágono del plan: sin las 7 clases el escaneo no es del universo."""
    universo = sc.cargar_universo(solo_renderizables=False)
    clases = {a["clase"] for a in universo}
    assert {"forex_commodities", "indices", "etfs", "acciones", "crypto"} <= clases
    tickers = {a["ticker"] for a in universo}
    for esperado in ("USDCLP", "XAUUSD", "US100.spot", "QQQ.US", "ETHUSD", "#NVDA"):
        assert esperado in tickers, f"falta {esperado} en el universo"


def test_la_tanda_2_no_repite_un_activo_de_la_tanda_1(tmp_path, monkeypatch):
    """Si el cliente recibe el mismo activo tres veces en un día, el carrusel
    deja de ser una selección y pasa a ser insistencia."""
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path)
    (tmp_path / "2026-08-25_10-30_tanda1.json").write_text(
        json.dumps({"tanda": 1, "generado": "2026-08-25 10:30", "seleccion": [{"ticker": "XAUUSD"}, {"ticker": "US100.spot"}]}),
        encoding="utf-8",
    )
    assert sc._publicados_hoy("2026-08-25", tanda=2) == {"XAUUSD", "US100.spot"}
    # La tanda 1 no se filtra a sí misma: solo cuentan las anteriores.
    assert sc._publicados_hoy("2026-08-25", tanda=1) == set()
    # Otro día no arrastra nada.
    assert sc._publicados_hoy("2026-08-26", tanda=2) == set()


def test_desduplicacion_continua_intradia_por_horario_de_ejecucion(tmp_path, monkeypatch):
    """El carrusel responsivo excluye activos de corridas anteriores del mismo día."""
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path)
    (tmp_path / "2026-08-25_10-30_apertura_ny.json").write_text(
        json.dumps({
            "sesion_slug": "apertura_ny",
            "generado": "2026-08-25 10:30",
            "seleccion": [{"ticker": "XAUUSD"}, {"ticker": "US100.spot"}],
        }),
        encoding="utf-8",
    )
    # Corrida a las 14:00 detecta la corrida previa de las 10:30
    assert sc._publicados_hoy("2026-08-25", hora_actual="14:00") == {"XAUUSD", "US100.spot"}
    # Corrida a las 09:00 no ve la de las 10:30
    assert sc._publicados_hoy("2026-08-25", hora_actual="09:00") == set()


@pytest.mark.parametrize("hora, minuto, dia_semana, slug_esperado, tanda_esperada", [
    (21, 0, 1, "asiatica", 3),      # Martes 21:00 NY -> Asia
    (1, 30, 2, "asiatica", 3),      # Miércoles 01:30 NY -> Asia
    (5, 0, 2, "europea", 1),        # Miércoles 05:00 NY -> Europa
    (10, 30, 3, "apertura_ny", 1),  # Jueves 10:30 NY -> Apertura Wall Street
    (14, 0, 3, "tarde_ny", 2),      # Jueves 14:00 NY -> Rotación de Tarde
    (16, 45, 4, "cierre_ny", 3),    # Viernes 16:45 NY -> Cierre Wall Street
    (12, 0, 5, "fin_de_semana", 1), # Sábado 12:00 NY -> Fin de semana
    (15, 0, 6, "fin_de_semana", 1), # Domingo 15:00 NY -> Fin de semana
    (19, 0, 6, "asiatica", 3),      # Domingo 19:00 NY -> Apertura Asia semanal
])
def test_detectar_sesion_cubre_todo_el_ciclo_de_mercado(
    hora, minuto, dia_semana, slug_esperado, tanda_esperada
):
    # 2026-08-24 fue lunes (weekday 0)
    # Lunes=24, Martes=25, Miercoles=26, Jueves=27, Viernes=28, Sabado=29, Domingo=30
    dia = 24 + dia_semana
    dt = datetime(2026, 8, dia, hora, minuto, tzinfo=NY)
    sesion = sc.detectar_sesion(dt)
    assert sesion["slug"] == slug_esperado
    assert sesion["tanda"] == tanda_esperada
    assert "nombre" in sesion
    assert "foco" in sesion
    assert sesion["hora_real_ny"] == f"{hora:02d}:{minuto:02d}"


def test_el_feriado_de_nyse_excluye_a_una_accion_pero_no_a_una_cripto():
    """Las criptos no mapean a ninguna bolsa: operan 24/7 y no tienen calendario
    de feriados, que es la limitación ya documentada en get_symbol_spec."""
    from market_data_mcp.tools.symbol_spec import _cargar_feriados
    feriados = _cargar_feriados().get("NYSE", [])
    if not feriados:
        pytest.skip("el calendario de feriados versionado esta vacio")
    dia = datetime.fromisoformat(feriados[0]).date()

    assert sc.gate_feriado("#NVDA", dia) is not None
    assert sc.gate_feriado("BTCUSD", dia) is None
    assert sc.gate_feriado("XAUUSD", dia) is None


# ─────────────────────────────────────────────────────────────────────────────
# El idioma de la fuente: el bug que dejaba todos los gates inertes
# ─────────────────────────────────────────────────────────────────────────────
# Nombres y países REALES observados en `obtener_calendario_macro` el 2026-08-25.
# La primera versión del escáner tenía estas tablas escritas en español, así que
# ningún blackout se activaba y el factor catalizador daba 0 siempre: el escáner
# informaba "0 exclusiones" cuando en realidad no había mirado nada. Un fallo en
# silencio, que es la peor clase.
EVENTOS_REALES = (
    ("United States", "ADP Employment Change Weekly"),
    ("United States", "Building Permits (Jul)"),
    ("United States", "CB Consumer Confidence (Aug)"),
    ("United States", "New Home Sales (MoM) (Jul)"),
    ("United States", "API Weekly Crude Oil Stock"),
    ("United States", "2-Year Note Auction"),
    ("United States", "Crude Oil Inventories"),
    ("United States", "FOMC Member Barkin Speaks"),
    ("United States", "Unemployment Rate (Jul)"),
    ("United States", "Nonfarm Payrolls"),
    ("United States", "Fed Interest Rate Decision"),
    ("Chile", "Imacec (YoY)"),
    ("China", "Manufacturing PMI"),
    ("Euro Zone", "CPI (YoY)"),
)


def test_los_paises_de_la_fuente_calzan_con_el_mapa_de_receptores():
    """Si un país de la fuente no está en el mapa, su dato nunca puntúa como
    catalizador y el factor M queda en 0 para todo el universo, sin aviso."""
    paises = {sc._normalizar(p) for p, _ in EVENTOS_REALES}
    for pais in paises:
        receptores = next(
            (v for k, v in sc._RECEPTORES_POR_PAIS.items() if k in pais or pais in k), None
        )
        assert receptores, f"'{pais}' no mapea a ningun receptor"


def test_solo_el_dato_de_impacto_alto_da_el_maximo_del_factor_catalizador():
    """En una jornada normal hay nueve eventos de impacto medio o mas. Si
    cualquiera diera +25, todo activo estadounidense sacaria el maximo y el
    factor dejaria de distinguir entre ellos."""
    alto = {"nombre": "CB Consumer Confidence (Aug)", "pais": "United States",
            "impacto": "alto", "hora_servidor": "2026-08-25 10:00"}
    medio = {"nombre": "ADP Employment Change Weekly", "pais": "United States",
             "impacto": "medio", "hora_servidor": "2026-08-25 08:15"}

    assert sc.factor_catalizador("US100.spot", [alto], None)[0] == 25
    assert sc.factor_catalizador("US100.spot", [medio], None)[0] == 15


def test_el_dato_de_ee_uu_no_puntua_para_un_activo_que_no_lo_recibe():
    """Un dato de confianza del consumidor de EE.UU. no le habla al peso chileno
    con la misma fuerza, y darle +25 inflaria su score sin razon."""
    evento = {"nombre": "CB Consumer Confidence (Aug)", "pais": "United States",
              "impacto": "alto", "hora_servidor": "2026-08-25 10:00"}
    puntos, _ = sc.factor_catalizador("USDCLP", [evento], None)
    assert puntos == 0


def test_los_eventos_de_segundo_orden_de_la_fuente_puntuan_15():
    """Inventarios, discursos y subastas son el +15 del plan, y sus nombres
    reales estan en ingles."""
    for nombre in ("Crude Oil Inventories", "FOMC Member Barkin Speaks", "2-Year Note Auction"):
        evento = {"nombre": nombre, "pais": "United States", "impacto": "medio",
                  "hora_servidor": "2026-08-25 10:00"}
        # Un activo que no es receptor directo, para aislar el camino del +15.
        puntos, detalle = sc.factor_catalizador("USDCLP", [evento], None)
        assert puntos == 15, f"{nombre} -> {puntos} ({detalle})"


def test_los_patrones_de_blackout_calzan_con_los_nombres_reales_de_la_fuente():
    """Cada regla de blackout tiene que poder activarse con al menos un nombre
    real. Una regla que nunca calza es una prohibicion que no existe."""
    ahora = datetime(2026, 8, 25, 10, 0, tzinfo=sc.SANTIAGO)
    casos = (
        ("Fed Interest Rate Decision", "United States", "XAUUSD"),
        ("Nonfarm Payrolls", "United States", "XAUUSD"),
        ("CPI (MoM)", "United States", "XAUUSD"),
        ("Imacec (YoY)", "Chile", "USDCLP"),
        ("Interest Rate Decision", "Chile", "USDCLP"),
    )
    for nombre, pais, ticker in casos:
        evento = {"nombre": nombre, "pais": pais, "hora_servidor": "2026-08-25 10:00"}
        motivo = sc.gate_blackout(ticker, [evento], ahora)
        assert motivo, f"'{nombre}' ({pais}) no activo ningun blackout"


def test_el_ipc_de_chile_no_dispara_el_blackout_global_del_ipc_de_ee_uu():
    """Sin acotar por pais, un 'CPI' chileno activaria la regla de alcance TODOS
    que corresponde solo al IPC estadounidense, y bloquearia el universo entero
    por un dato local."""
    evento = {"nombre": "CPI (MoM)", "pais": "Chile", "hora_servidor": "2026-08-25 10:00"}
    ahora = datetime(2026, 8, 25, 10, 5, tzinfo=sc.SANTIAGO)
    assert sc.gate_blackout("USDCLP", [evento], ahora) is not None
    assert sc.gate_blackout("XAUUSD", [evento], ahora) is None
    assert sc.gate_blackout("US100.spot", [evento], ahora) is None


def test_un_evento_sin_hora_valida_no_revienta_el_gate():
    """La fuente es HTML scrapeado: una fila mal formada no puede tumbar el
    escaneo completo."""
    malos = [
        {"nombre": "Nonfarm Payrolls", "pais": "United States"},               # sin hora
        {"nombre": "Nonfarm Payrolls", "pais": "United States", "hora_servidor": "ayer"},
    ]
    ahora = datetime(2026, 8, 25, 10, 0, tzinfo=sc.SANTIAGO)
    assert sc.gate_blackout("XAUUSD", malos, ahora) is None


def test_filtrar_por_grupo_acota_correctamente_el_universo():
    universo = sc.cargar_universo(solo_renderizables=True)

    fx = sc.filtrar_por_grupo(universo, "forex")
    assert all(a["categoria"] == "forex" for a in fx)
    assert any(a["ticker"] == "USDCLP" for a in fx)

    comm = sc.filtrar_por_grupo(universo, "commodities")
    assert any(a["ticker"] == "XAUUSD" for a in comm)
    assert any(a["ticker"] == "WTI.spot" for a in comm)

    indices = sc.filtrar_por_grupo(universo, "indices")
    assert any(a["ticker"] == "US100.spot" for a in indices)

    crypto = sc.filtrar_por_grupo(universo, "crypto")
    assert any(a["ticker"] == "BTCUSD" for a in crypto)
    assert any(a["ticker"] == "ETHUSD" for a in crypto)


# ─────────────────────────────────────────────────────────────────────────────
# El gate de banda contra vela tipica
# ─────────────────────────────────────────────────────────────────────────────
# Las tres mediciones son las de la tanda del 2026-09-04, donde estas piezas se
# descartaron a mano: el S&P 500 con banda de 16,54 puntos y vela de 17,00.
def test_una_vela_que_cubre_la_banda_entera_excluye():
    """Dar esos niveles es entregar ruido como si fuera estructura: el precio
    cruza los dos bordes dentro de una hora normal."""
    motivo = sc.gate_banda(h1_con_banda(banda=16.54, vela=17.00))
    assert motivo is not None
    assert "1,03" in motivo or "1.03" in motivo


def test_una_banda_estrecha_pero_no_cubierta_pasa():
    """0,80x queda en la zona de aviso que fijo el director: la pieza sale, con la
    advertencia de que sus niveles son estrechos para su volatilidad."""
    assert sc.gate_banda(h1_con_banda(banda=41.20, vela=33.00)) is None


def test_una_banda_holgada_pasa_limpia():
    assert sc.gate_banda(h1_con_banda(banda=60.00, vela=33.00)) is None
    assert sc.banda_estrecha(h1_con_banda(banda=60.00, vela=33.00)) is None


def test_la_zona_de_aviso_se_reporta_sin_excluir():
    ratio = sc.banda_estrecha(h1_con_banda(banda=41.20, vela=33.00))
    assert ratio is not None and 0.70 <= ratio < 1.00


def test_unos_niveles_de_respaldo_por_atr_tienen_su_propio_motivo():
    """No es un caso del ratio: cuando los dos lados son sinteticos la banda vale
    2 ATR **exactos por construccion** y el ratio da siempre 0,75. Medir ahi no
    mide nada, y ademas no hay estructura que publicar."""
    h1 = h1_con_banda(banda=4.0, vela=3.0)          # 2 ATR exactos
    h1["niveles_origen"] = {"r1": "atr", "r2": "atr", "s1": "atr", "s2": "atr"}
    motivo = sc.gate_banda(h1)
    assert motivo is not None
    assert "respaldo" in motivo.lower()
    assert "0,75" not in motivo and "0.75" not in motivo


def test_un_solo_lado_sintetico_tambien_tiene_motivo_propio():
    """Se puede tener una resistencia real y un soporte sintetico. Publicar
    "Soporte clave" cuando es el precio menos el ATR es la misma afirmacion sin
    respaldo, aunque el otro borde si exista."""
    h1 = h1_con_banda(banda=60.0, vela=33.0)
    h1["niveles_origen"] = {"r1": "swing", "r2": "swing", "s1": "atr", "s2": "atr"}
    motivo = sc.gate_banda(h1)
    assert motivo is not None and "respaldo" in motivo.lower()


def test_sin_el_campo_de_origen_no_se_excluye_pero_no_se_afirma_nada():
    """Compatibilidad con una respuesta vieja del analizador. El criterio es el
    mismo que con el calendario caido: no se inventa una exclusion, y el escaner
    dice que no pudo verificarlo."""
    h1 = h1_con_banda(banda=60.0, vela=33.0)
    del h1["niveles_origen"]
    assert sc.gate_banda(h1) is None


def test_el_gate_de_banda_excluye_antes_de_puntuar():
    """Un activo con niveles que no aguantan una hora puede puntuar alto: por eso
    el filtro va antes del score, como los otros cuatro."""
    h1 = h1_con_banda(banda=16.54, vela=17.00)
    res = sc.evaluar_activo(
        {"ticker": "TEST", "nombre": "Prueba", "clase": "forex_commodities",
         "categoria": "forex", "digits": 2},
        eventos=[], delta_ust_bps=0.0,
        ahora_santiago=datetime(2026, 9, 4, 10, 0, tzinfo=sc.SANTIAGO),
        analizador=analizador_falso(h1, d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "score" not in res


def test_todo_activo_del_universo_trae_su_nota_de_volatilidad():
    """Contrato: sin la nota, el mensaje no puede justificar su temporalidad.

    `CLAUDE.md` declara esa linea obligatoria desde el issue #44, y los campos
    estaban en `config/activos.json` para 23 de los 37 activos: **las 14 acciones
    no los tenian**, y `cargar_universo` tampoco los copiaba, asi que el generador
    del mensaje nunca los vio.
    """
    sin_nota = [
        a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)
        if not a.get("nota_volatilidad") or not a.get("volatilidad")
    ]
    assert not sin_nota, f"activos sin volatilidad ni nota: {sin_nota}"


def test_la_volatilidad_declarada_es_una_de_las_tres_etiquetas():
    validas = {"baja", "media", "alta"}
    raras = {
        a["ticker"]: a.get("volatilidad")
        for a in sc.cargar_universo(solo_renderizables=False)
        if a.get("volatilidad") not in validas
    }
    assert not raras, raras


def test_toda_nota_de_volatilidad_justifica_un_marco_temporal():
    """La nota se publica detras de "Por que 1H aca:", asi que tiene que hablar de
    marcos y no de drivers.

    Tres notas (GBP/USD, cobre, bitcoin) eran descripciones de lo que mueve al
    activo, sin nombrar ninguna temporalidad: publicadas asi, la linea prometia
    una justificacion y entregaba otra cosa.
    """
    import pipeline_carrusel as pc

    etiquetas = {e for e, _ in pc.MARCOS_CANONICOS.values()}
    sin_marco = [
        a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)
        if not any(e in a["nota_volatilidad"] for e in etiquetas)
    ]
    assert not sin_marco, f"notas que no nombran ningun marco: {sin_marco}"


def test_toda_nota_nombra_el_marco_que_el_carrusel_publica():
    """Si la nota recomienda 4H y la pieza sale en 1H, la linea se contradice sola.

    Paso con Solana: "Por que 1H aca: ... 4H da la lectura mas limpia". Las notas
    pueden (y deben) nombrar el marco mas amplio, pero tienen que explicar tambien
    el que se publica.
    """
    import pipeline_carrusel as pc

    etiqueta = pc.MARCOS_CANONICOS[pc.TIMEFRAME_GRAFICO][0]
    sin_el = [
        a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)
        if etiqueta not in a["nota_volatilidad"]
    ]
    assert not sin_el, f"notas que no justifican {etiqueta}: {sin_el}"


def test_un_indicador_fuera_del_glosario_levanta_aviso(monkeypatch):
    """`glosario_pendiente` se emitia y nadie la leia.

    `calendar.py` la marca en todo evento que no engancha, y ningun consumidor de
    produccion la consultaba: solo tests y docs. Mientras tanto el nombre en
    ingles pasaba al mensaje sin marca, porque el fallback devuelve el titulo de
    la fuente tal cual. Asi salieron cuatro terminos del informe de empleo a cinco
    canales el 2026-09-04.
    """
    import market_data_mcp.tools.calendar as cal

    monkeypatch.setattr(cal, "cargar_calendario", lambda **k: {"eventos": [
        {"nombre": "Richmond Manufacturing Index (Aug)", "glosario_pendiente": True},
        {"nombre": "Nonfarm Payrolls (Aug)"},
    ]})
    _, _, avisos = sc._contexto_macro(datetime(2026, 9, 4, 10, 0, tzinfo=sc.SANTIAGO))
    texto = " ".join(avisos)
    assert "glosario" in texto and "Richmond" in texto, avisos
    assert "Nonfarm Payrolls" not in texto, "el que SI esta en el glosario no se reporta"


# ─────────────────────────────────────────────────────────────────────────────
# Cobertura fija (decisión del director, 2026-09-28)
# ─────────────────────────────────────────────────────────────────────────────
FIJOS = {"USDCLP", "XAUUSD", "WTI.spot", "COPPER"}


def test_la_cobertura_fija_son_los_cuatro_activos_base_y_existen_en_el_catalogo():
    assert set(sc.cobertura_fija()) == FIJOS
    catalogo = {a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)}
    assert FIJOS <= catalogo


def test_los_fijos_entran_al_universo_aunque_no_tengan_imagen():
    """El cobre no tiene foto; su pieza sale con el grafico del motor."""
    renderizable = {a["ticker"] for a in sc.cargar_universo(solo_renderizables=True)}
    assert FIJOS <= renderizable


def test_un_canal_no_cubierto_sale_del_universo_antes_de_puntuar():
    """Director, 2026-09-29: sin índices ni cripto. Filtrar después de elegir le
    quitaría cupos al Top N; por eso sale del universo."""
    universo = sc.cargar_universo(solo_renderizables=False)
    dentro, fuera = sc.solo_canales_cubiertos(universo)
    assert {"BTCUSD", "US100.spot"} <= set(fuera)
    assert {"USDCLP", "XAUUSD", "COPPER"} <= {a["ticker"] for a in dentro}
    assert len(dentro) + len(fuera) == len(universo)


# ─────────────────────────────────────────────────────────────────────────────
# Fase 2 del enchufe: el escáner es de la estrategia (spec §4, §5, §7)
# ─────────────────────────────────────────────────────────────────────────────
from dataclasses import replace as _replace  # noqa: E402

import pandas as pd  # noqa: E402

import referencia_semanal as rs  # noqa: E402
from estrategia.contrato import (  # noqa: E402
    SCL, Escenario, Etiqueta, Lectura, Linea, Marcos, Puntaje, Referencia,
)

NY_LUNES = datetime(2026, 10, 12, 10, 0, tzinfo=NY)  # lunes 12-10, 11:00 en Santiago


def _lec(ticker, estado="TENDENCIA", direccion="ALCISTA"):
    lin = Linea("seguridad", "diagonal", ((100, 10.0), (200, 11.0)), "H4", 3, "A+", 11.5)
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    ref = Referencia(11.5, "línea alcista de seguridad", lin)
    return Lectura(ticker=ticker, marco="H4", precio=12.0, direccion=direccion, estado=estado,
                   lineas=(lin,), en_prueba=None, vigilar=ref, invalidacion=ref, objetivo=None,
                   escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


class _Est:
    """Puntúa por tabla; `excluir` simula las exclusiones de Tori y `ruptura` una ruptura."""

    nombre = "falsa"
    marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                    {"D1": Etiqueta("p", "d"), "H4": Etiqueta("swing", "de una a dos semanas")})

    def __init__(self, puntos, excluir=None, ruptura=()):
        self.puntos, self.excluir, self.ruptura = puntos, excluir or {}, set(ruptura)
        self.lecturas = {"leer": 0, "seguir": 0}

    def leer(self, ticker, velas, digits, en_curso=None):
        self.lecturas["leer"] += 1
        return _lec(ticker)

    def seguir(self, referencia, velas, digits, en_curso=None):
        self.lecturas["seguir"] += 1
        if referencia.ticker in self.ruptura:
            return _replace(referencia, estado="RUPTURA",
                            lineas=tuple(_replace(x, rol="accion") for x in referencia.lineas))
        return referencia

    def puntuar(self, lectura, horizonte):
        motivo = self.excluir.get(lectura.ticker)
        return Puntaje(0.0 if motivo else self.puntos.get(lectura.ticker, 10.0), {}, motivo)

    def divergencia(self, preparada, actual):
        return None


def _velas():
    return pd.DataFrame({"time": [1, 2, 3], "open": [1.0, 1.1, 1.2], "high": [1.2, 1.3, 1.3],
                         "low": [0.9, 1.0, 1.1], "close": [1.1, 1.2, 1.2]})


def _lector(ticker, marcos, extra):
    return {m: _velas() for m in marcos.todos}, None


def _escanear(tmp_path, est, monkeypatch, **kw):
    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path / "screener")
    return sc.escanear(ahora_ny=kw.pop("ahora_ny", NY_LUNES), estrategia=est, lector=_lector,
                       base_referencias=tmp_path / "refs", **kw)


def _fijar(tmp_path, *tickers):
    rs.guardar_manifiesto("2026-W42", {"elegidos": list(tickers)}, base=tmp_path / "refs")
    for t in tickers:
        rs.guardar(_lec(t), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")


def test_sin_semanal_la_primera_diaria_la_corre_y_lo_dice(tmp_path, monkeypatch):
    res = _escanear(tmp_path, _Est({}), monkeypatch, modo_matriz=True)
    man = rs.manifiesto("2026-W42", base=tmp_path / "refs")
    assert man is not None and set(sc.cobertura_fija()) <= set(man["elegidos"])
    assert any("análisis semanal" in a for a in res["avisos"])
    assert res["semana"] == "2026-W42" and res["estrategia"] == "falsa"


def test_la_semanal_corre_una_vez_aunque_la_primera_diaria_pida_un_canal(tmp_path, monkeypatch):
    est = _Est({})
    _escanear(tmp_path, est, monkeypatch, grupo="forex")
    elegidos = rs.manifiesto("2026-W42", base=tmp_path / "refs")["elegidos"]
    assert "XAUUSD" in elegidos  # commodities también quedó fijado
    leidas = est.lecturas["leer"]
    _escanear(tmp_path, est, monkeypatch, grupo="commodities")
    assert est.lecturas["leer"] == leidas  # la segunda corrida no volvió a correr la semanal


def test_la_semanal_elige_por_categoria_los_fijos_y_los_mejores(tmp_path):
    universo = sc.solo_canales_cubiertos(sc.cargar_universo(True))[0]
    puntos = {a["ticker"]: 50.0 for a in universo}
    puntos["GBPUSD"] = 0.0
    res = sc.correr_semanal(_Est(puntos), universo, NY_LUNES.astimezone(SCL), _lector,
                            top=3, base=tmp_path)
    assert "GBPUSD" not in res["elegidos"]
    for fijo in sc.cobertura_fija():
        assert fijo in res["elegidos"]
        assert rs.cargar("2026-W42", fijo, base=tmp_path) is not None


def test_la_semanal_guarda_un_fijo_excluido_y_lo_dice(tmp_path):
    universo = sc.solo_canales_cubiertos(sc.cargar_universo(True))[0]
    res = sc.correr_semanal(_Est({}, excluir={"COPPER": "sin líneas trazables"}), universo,
                            NY_LUNES.astimezone(SCL), _lector, top=3, base=tmp_path)
    assert "COPPER" in res["elegidos"]
    assert any("COPPER" in a and "sin líneas trazables" in a for a in res["avisos"])


def test_las_diarias_solo_cubren_los_activos_de_la_semana(tmp_path, monkeypatch):
    _fijar(tmp_path, "USDCLP")
    res = _escanear(tmp_path, _Est({}), monkeypatch, modo_matriz=True)
    assert [s["ticker"] for s in res["ranking_completo"]] == ["USDCLP"]
    assert any("sin referencia esta semana" in a for a in res["avisos"])


def test_la_diaria_ordena_con_el_puntaje_de_sesion(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD", "GBPUSD")
    res = _escanear(tmp_path, _Est({"EURUSD": 30.0, "GBPUSD": 80.0}), monkeypatch)
    assert [s["ticker"] for s in res["ranking_completo"]] == ["GBPUSD", "EURUSD"]
    elegido = res["ranking_completo"][0]
    assert elegido["score"] == 80.0 and elegido["lectura"]["ticker"] == "GBPUSD"
    assert elegido["marco"] == "H4" and elegido["volatilidad_tipica"] > 0
    assert "factores" not in elegido


def test_una_ruptura_reemplaza_la_referencia_y_la_siguiente_diaria_la_usa(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD")
    est = _Est({}, ruptura={"EURUSD"})
    res = _escanear(tmp_path, est, monkeypatch)
    assert res["ranking_completo"][0]["estado"] == "RUPTURA"
    guardada = json.loads(rs.ruta("2026-W42", "EURUSD", tmp_path / "refs").read_text(encoding="utf-8"))
    assert guardada["motivo"] == "ruptura"
    assert any("nueva referencia" in a for a in res["avisos"])
    # La diaria siguiente sigue la referencia nueva: sin ruptura nueva, no hay reemplazo.
    est.ruptura.clear()
    siguiente = _escanear(tmp_path, est, monkeypatch, ahora_ny=datetime(2026, 10, 13, 10, 0, tzinfo=NY))
    assert siguiente["ranking_completo"][0]["estado"] == "TENDENCIA"
    assert not any("nueva referencia" in a for a in siguiente["avisos"])


def test_un_no_fijo_excluido_por_la_estrategia_queda_fuera_con_su_motivo(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD")
    res = _escanear(tmp_path, _Est({}, excluir={"EURUSD": "va contra la secuencia"}), monkeypatch)
    assert res["excluidos"][0]["excluido"] == "va contra la secuencia"


def test_un_fijo_excluido_por_la_estrategia_sale_igual_y_lo_dice(tmp_path, monkeypatch):
    _fijar(tmp_path, "USDCLP")
    res = _escanear(tmp_path, _Est({}, excluir={"USDCLP": "sin líneas trazables"}), monkeypatch,
                    modo_matriz=True)
    elegido = next(s for s in res["seleccion"] if s["ticker"] == "USDCLP")
    assert elegido["gates_omitidos"] == ["sin líneas trazables"]
    assert any("USDCLP: cobertura fija, sale siempre aunque sin líneas trazables" in a
               for a in res["avisos"])


def test_un_error_de_datos_excluye_con_su_motivo_y_no_revienta(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD")

    def lector_roto(ticker, marcos, extra):
        raise RuntimeError("MT5 no entregó velas")

    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path / "screener")
    res = sc.escanear(ahora_ny=NY_LUNES, estrategia=_Est({}), lector=lector_roto,
                      base_referencias=tmp_path / "refs")
    assert "MT5 no entregó velas" in res["excluidos"][0]["excluido"]


def test_el_modo_matriz_respeta_el_tope_por_grupo(tmp_path, monkeypatch):
    """La matriz llega hasta `top` piezas por canal cuando hay con qué."""
    _fijar(tmp_path, "USDJPY", "EURUSD", "GBPUSD")
    puntos = {"USDJPY": 70.0, "EURUSD": 60.0, "GBPUSD": 50.0}
    con_uno = [s["ticker"] for s in _escanear(tmp_path, _Est(puntos), monkeypatch, top=1,
                                              modo_matriz=True)["seleccion"]]
    con_tres = [s["ticker"] for s in _escanear(tmp_path, _Est(puntos), monkeypatch, top=3,
                                               modo_matriz=True)["seleccion"]]
    assert con_uno == ["USDJPY"]
    assert con_tres == ["USDJPY", "EURUSD", "GBPUSD"]


def test_el_modo_matriz_cubre_cada_canal_con_su_fijo(tmp_path, monkeypatch):
    _fijar(tmp_path, "USDCLP", "XAUUSD", "EURUSD")
    sel = _escanear(tmp_path, _Est({"EURUSD": 90.0}), monkeypatch, top=1, modo_matriz=True)["seleccion"]
    assert [s["ticker"] for s in sel] == ["USDCLP", "XAUUSD"]  # el fijo llena el cupo del canal


def test_un_fijo_no_se_excluye_por_haber_salido_en_otra_corrida(tmp_path, monkeypatch):
    _fijar(tmp_path, *FIJOS, "EURUSD")
    monkeypatch.setattr(sc, "_publicados_hoy", lambda *a, **k: set(FIJOS) | {"EURUSD"})
    res = _escanear(tmp_path, _Est({}), monkeypatch)
    elegidos = {r["ticker"] for r in res["seleccion"]}
    assert FIJOS <= elegidos and "EURUSD" not in elegidos


def test_un_fijo_sigue_fuera_en_feriado_de_su_bolsa(tmp_path, monkeypatch):
    """Mercado cerrado no tiene niveles de hoy: la cobertura fija no inventa precio."""
    _fijar(tmp_path, *FIJOS)
    monkeypatch.setattr(sc, "gate_feriado", lambda t, f: "feriado" if t == "USDCLP" else None)
    res = _escanear(tmp_path, _Est({}), monkeypatch)
    assert "USDCLP" not in {r["ticker"] for r in res["seleccion"]}


def test_un_blackout_excluye_aunque_haya_referencia(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD")
    monkeypatch.setattr(sc, "gate_blackout", lambda t, e, a: "blackout por NFP" if t == "EURUSD" else None)
    res = _escanear(tmp_path, _Est({}), monkeypatch)
    assert res["excluidos"][0]["excluido"] == "blackout por NFP"


def test_todo_activo_cubierto_justifica_el_marco_operativo_de_la_estrategia():
    """Con el enchufe el marco lo decide la estrategia (spec §8.1): la nota tiene que
    justificar ese marco, en `notas_marco`, para cada activo que el carrusel publica."""
    from estrategia import registro

    op = registro.activa().marcos.operativo
    corto = {"H1": "1H", "H4": "4H", "D1": "1D"}[op]
    universo, _ = sc.solo_canales_cubiertos(sc.cargar_universo(True))
    for a in universo:
        nota = (a.get("notas_marco") or {}).get(op, "")
        assert nota, f"{a['ticker']} no trae notas_marco.{op}"
        assert corto in nota, f"{a['ticker']}: la nota de {op} no nombra {corto}"
        assert "—" not in nota and "–" not in nota


def test_una_semanal_sin_datos_no_cierra_la_semana(tmp_path, monkeypatch):
    """Con MT5 caído la semanal no puede dejar escrito un manifiesto vacío: la semana entera
    quedaría sin piezas y nadie la reintentaría."""
    def lector_roto(ticker, marcos, extra):
        raise RuntimeError("MT5 no responde")

    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path / "screener")
    res = sc.escanear(ahora_ny=NY_LUNES, estrategia=_Est({}), lector=lector_roto,
                      base_referencias=tmp_path / "refs")
    assert rs.manifiesto("2026-W42", base=tmp_path / "refs") is None
    assert any("se reintenta" in a for a in res["avisos"])


def test_si_falla_un_fijo_la_semana_queda_abierta(tmp_path):
    universo = sc.solo_canales_cubiertos(sc.cargar_universo(True))[0]

    def lector(ticker, marcos, extra):
        if ticker == "USDCLP":
            raise RuntimeError("sin velas")
        return _lector(ticker, marcos, extra)

    res = sc.correr_semanal(_Est({}), universo, NY_LUNES.astimezone(SCL), lector, base=tmp_path)
    assert rs.manifiesto("2026-W42", base=tmp_path) is None
    assert not res["completa"]


def test_la_semanal_no_hereda_el_todos_ni_el_top_de_quien_llega_primero(tmp_path, monkeypatch):
    vistos = []
    real = sc.correr_semanal

    def espia(est, universo, ahora, lector, top=3, base=None):
        vistos.append((len(universo), top))
        return real(est, universo, ahora, lector, top=top, base=base)

    monkeypatch.setattr(sc, "correr_semanal", espia)
    _escanear(tmp_path, _Est({}), monkeypatch, top=1, solo_renderizables=False)
    cubierto = len(sc.solo_canales_cubiertos(sc.cargar_universo(True))[0])
    assert vistos == [(cubierto, 3)]


def test_un_error_al_puntuar_un_activo_no_tumba_la_tanda(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD", "GBPUSD")

    class Rota(_Est):
        def puntuar(self, lectura, horizonte):
            if lectura.ticker == "EURUSD":
                raise RuntimeError("roto")
            return super().puntuar(lectura, horizonte)

    res = _escanear(tmp_path, Rota({}), monkeypatch)
    assert [s["ticker"] for s in res["ranking_completo"]] == ["GBPUSD"]
    assert "roto" in res["excluidos"][0]["excluido"]


def test_la_seleccion_lleva_la_referencia_contra_la_que_se_leyo(tmp_path, monkeypatch):
    _fijar(tmp_path, "EURUSD")
    res = _escanear(tmp_path, _Est({}), monkeypatch)
    assert res["ranking_completo"][0]["referencia"]["ticker"] == "EURUSD"
