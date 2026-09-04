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
        ACTIVO, [evento], delta_ust_bps=None, sesgos={},
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
        ACTIVO, [evento], None, {}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert sum(f["max"] for f in res["factores"].values()) == 100


def test_el_impulso_proyectado_es_una_vez_y_media_el_atr_de_h1():
    """Es el número que alimenta el bloque "Volatilidad típica" de la Story."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert res["impulso_adc_atr"] == pytest.approx(3.0)  # 1,5 x ATR 2,0


# ─────────────────────────────────────────────────────────────────────────────
# Los gates: prohibiciones, no puntos
# ─────────────────────────────────────────────────────────────────────────────
def test_un_setup_prohibido_por_el_playbook_queda_fuera_aunque_puntue_alto():
    """La segunda corrección al plan.

    El Playbook §2 es prohibitivo: en R1/R3 no se abren cortos en Oro "aun con
    RSI sobrecomprado en 80". Con scoring puro, ese corto puntúa alto y gana la
    tanda. El gate va antes de puntuar.
    """
    h1_bajista = h1_perfecto()
    h1_bajista.update(price=100.0, ema_20=101.0, ema_50=102.0, ema_100=103.0,
                      rsi_14=40.0, macd_hist=-0.3, s1=96.0, r1=101.0)
    sesgo = {
        "regimen_macro_global": {"codigo": "R1_RIESGO_INFLACION"},
        # `gate_confianza` corre antes y es fail-closed: un payload sin el campo
        # queda excluido por otro motivo y este test dejaria de probar lo suyo.
        "confianza_general": {"confianza_total_pct": 90.0},
        "activo": {"setups_prohibidos": ["SHORT_AGRESIVO"], "setups_permitidos": []},
    }
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": sesgo}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_bajista, d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "SHORT_AGRESIVO" in res["excluido"]
    assert "R1_RIESGO_INFLACION" in res["excluido"]


def test_una_prohibicion_de_la_direccion_contraria_no_bloquea():
    """Que esté prohibido comprar agresivamente no impide comunicar una subida
    bien fundada: la prohibición solo aplica si apunta al mismo lado."""
    sesgo = {
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO"},
        "confianza_general": {"confianza_total_pct": 90.0},
        "activo": {"setups_prohibidos": ["SHORT_AGRESIVO"], "setups_permitidos": []},
    }
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": sesgo}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),  # alcista
    )
    assert "excluido" not in res
    assert res["direccion"] == "ALCISTA"


def test_un_activo_sin_ficha_de_playbook_no_se_bloquea_por_falta_de_sesgo():
    """Entrar al catálogo técnico no es entrar al Playbook: un ETF no tiene
    régimen ni setups y no se le inventan."""
    etf = {**ACTIVO, "ticker": "QQQ.US", "nombre": "Invesco QQQ"}
    res = sc.evaluar_activo(
        etf, [], None, {}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res


def test_el_blackout_del_calendario_excluye_al_activo():
    """La tercera corrección: el plan ignora las ventanas de bloqueo de la skill
    §4 y su factor catalizador premia justo al activo que recibe el dato."""
    # NFP a las 09:30 hora Chile, ventana -15/+30 -> 09:15 a 10:00.
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 09:30"}
    dentro = datetime(2026, 8, 25, 9, 40, tzinfo=sc.SANTIAGO)
    res = sc.evaluar_activo(
        ACTIVO, [evento], None, {}, dentro,
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
        ACTIVO, [evento], None, {}, fuera,
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res
    assert res["factores"]["catalizador"]["puntos"] == 25


def test_un_blackout_de_alcance_local_no_toca_a_los_demas_activos():
    """Un Imacec bloquea al peso, no al Oro."""
    evento = {"nombre": "Imacec (YoY)", "pais": "Chile", "hora_servidor": "2026-08-25 08:30"}
    dentro = datetime(2026, 8, 25, 8, 35, tzinfo=sc.SANTIAGO)
    analizador = analizador_falso(h1_perfecto(), d1_con_consumo(0.30))

    peso = sc.evaluar_activo({**ACTIVO, "ticker": "USDCLP"}, [evento], None, {}, dentro, analizador)
    oro = sc.evaluar_activo(ACTIVO, [evento], None, {}, dentro, analizador)

    assert "excluido" in peso and "blackout" in peso["excluido"]
    assert "excluido" not in oro


def test_el_agotamiento_del_atr_diario_excluye_en_vez_de_dar_cero_puntos():
    """El plan le pone 0 puntos al factor Espacio, pero 0 de 20 todavía deja 80
    disponibles: un activo sin recorrido puede ganar la tanda por técnica y
    catalizador. Agotado es agotado."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {}, AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.95)),
    )
    assert "excluido" in res
    assert "95%" in res["excluido"]


def test_un_error_del_motor_excluye_con_su_codigo_y_no_revienta():
    """Contrato de error del MCP: nunca lanza, siempre explica."""
    def analizador_roto(ticker: str, timeframe: str) -> dict:
        return {"error": "MT5_UNAVAILABLE", "message": "MT5 no esta conectado."}

    res = sc.evaluar_activo(ACTIVO, [], None, {}, AHORA.astimezone(sc.SANTIAGO), analizador_roto)
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
    assert all(a["imagen"] for a in renderizable)
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


def test_el_modo_matriz_cubre_cada_grupo_que_tenga_con_que():
    """Modo matriz: cobertura de TODOS los grupos, hasta `top` piezas cada uno.

    El test anterior exigía que ningún grupo se repitiera, porque la matriz
    tomaba el Top 1 fijo. Ese contrato se cambió el 2026-09-03: con un solo
    activo por canal el carrusel de un grupo con cinco elegibles quedaba en una
    pieza. Lo que sí se conserva, porque es el propósito de este modo, es que
    **ningún grupo con candidatos quede fuera**: la matriz reparte antes de
    profundizar, y es lo que la distingue de un Top N global.
    """
    import pipeline_carrusel as pc

    def fake_analizador(ticker, tf):
        res = dict(h1_perfecto() if tf == "H1" else d1_con_consumo(0.30))
        res["ticker"] = ticker
        return res

    resultado = sc.escanear(
        tanda=1,
        top=1,
        solo_renderizables=True,
        analizador=fake_analizador,
        modo_matriz=True,
    )
    seleccion = resultado["seleccion"]
    assert len(seleccion) > 0

    grupos_sel = [pc.obtener_grupo_whatsapp(s["clase"], s["ticker"]) for s in seleccion]
    assert len(grupos_sel) == len(set(grupos_sel)), (
        "con --top 1 la matriz sigue siendo un activo por grupo"
    )

    # Con el tope por defecto, un grupo puede repetirse: eso es lo que se busca.
    amplio = sc.escanear(
        tanda=1, top=3, solo_renderizables=True,
        analizador=fake_analizador, modo_matriz=True,
    )["seleccion"]
    grupos_amplio = {pc.obtener_grupo_whatsapp(s["clase"], s["ticker"]) for s in amplio}
    assert len(amplio) >= len(seleccion), "subir el tope no puede dar menos piezas"
    assert grupos_amplio >= set(grupos_sel), (
        "al subir el tope se perdió la cobertura de algún grupo, que es justo lo "
        "que este modo existe para garantizar"
    )



# ─────────────────────────────────────────────────────────────────────────────
# Vocabulario de prohibiciones: el gate tiene que conocer TODOS los tokens
# ─────────────────────────────────────────────────────────────────────────────

def _sesgo_con(prohibidos, regimen="R0_CALMA_RANGO", confianza=90.0):
    """La confianza va en la fixture porque un payload real siempre la trae, y
    `gate_confianza` corre antes que el del Playbook."""
    return {
        "regimen_macro_global": {"codigo": regimen},
        "confianza_general": {"confianza_total_pct": confianza},
        "activo": {"setups_prohibidos": list(prohibidos), "setups_permitidos": []},
    }


def test_gate_bloquea_breakout_chase_long_en_lectura_alcista():
    """La violación que estaba viva el 2026-09-02.

    En R0 el Playbook y la skill §4 coinciden: prohibido perseguir quiebres
    tendenciales. El motor lo emitía bien (`BREAKOUT_CHASE_LONG` en USD/CLP) y el
    vocabulario del escáner no lo reconocía, así que el gate lo dejaba pasar y la
    tanda podía publicar el quiebre alcista que el Playbook prohíbe.
    """
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con(["BREAKOUT_CHASE_LONG"])},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),  # alcista
    )
    assert "excluido" in res
    assert "BREAKOUT_CHASE_LONG" in res["excluido"]


def test_gate_bloquea_fade_top_resistance_en_lectura_bajista():
    """El otro hueco. Estaba citado literalmente en el comentario del módulo como
    ejemplo del vocabulario que el gate sí capturaba, y no lo capturaba."""
    h1_bajista = h1_perfecto()
    h1_bajista.update(price=100.0, ema_20=101.0, ema_50=102.0, ema_100=103.0,
                      rsi_14=40.0, macd_hist=-0.3, s1=96.0, r1=101.0)
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con(["FADE_TOP_RESISTANCE"])},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_bajista, d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "FADE_TOP_RESISTANCE" in res["excluido"]


@pytest.mark.parametrize("token", ["BREAKOUT_CHASE", "GRID_SIN_STOP",
                                   "MEAN_REVERSION_RSI_H1", "FADE_SUPPORT_RESISTANCE_M15"])
def test_gate_no_bloquea_tokens_sin_direccion(token):
    """Estos prohíben una FORMA de operar, no un lado del mercado. Bloquear con
    ellos dejaría al escáner sin universo por una prohibición que no se opone a
    la lectura técnica."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con([token])},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res, f"{token} no tiene dirección y no debería bloquear"


def test_gate_bloquea_token_desconocido_en_vez_de_ignorarlo():
    """Un token sin clasificar es más probable que sea una prohibición real a que
    sea inocuo. No publicar un activo cuesta una pieza; publicar contra el
    Playbook cuesta el método. Ante la duda el gate bloquea y dice por qué."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con(["SETUP_QUE_NADIE_CLASIFICO"])},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "SETUP_QUE_NADIE_CLASIFICO" in res["excluido"]


def test_todo_token_del_motor_esta_clasificado_en_el_escaner():
    """El contrato que impide repetir el error.

    Si alguien agrega un `setups_prohibidos` nuevo al motor y no lo clasifica
    acá, este test falla. Sin él, el token entra al snapshot, el gate no lo
    reconoce y la omisión no se nota hasta que sale una pieza que no debía salir
    — que es exactamente cómo llegamos acá, y el mismo patrón de los filtros de
    calendario escritos en español contra una fuente en inglés.
    """
    import re

    fuente = (RAIZ / "scripts" / "macro_bias_engine.py").read_text(encoding="utf-8")
    emitidos = {
        token
        for bloque in re.findall(r"setups_prohibidos\s*=\s*\[(.*?)\]", fuente, re.S)
        for token in re.findall(r'"([^"]+)"', bloque)
    }
    assert emitidos, "no se pudo leer ningún token del motor: el patrón quedó obsoleto"

    sin_clasificar = sorted(emitidos - set(sc._DIRECCION_PROHIBIDA))
    assert not sin_clasificar, (
        f"el motor emite tokens que el gate no conoce: {sin_clasificar}. "
        "Agrégalos a _DIRECCION_PROHIBIDA con su dirección, o None si prohíben "
        "una forma de operar y no un lado del mercado."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate 5: el modelo no comunica cuando no ve
# ─────────────────────────────────────────────────────────────────────────────
# El umbral es 65 % y no es una preferencia: es el piso algebraico de la norma
# que el Playbook §3 ya escribió. Si frescura y cobertura valen 1,0 -la condición
# que ese párrafo llama "operación normal"- el puntaje arrastra 0,40 + 0,25 =
# 0,65 antes de que la antigüedad aporte nada. Bajo 65 % es ARITMÉTICAMENTE
# IMPOSIBLE que ambas sean 1,0: no significa "datos algo viejos", significa que
# falta un driver o está roto.
#
# 80 % habría sido un error: el techo real de la escala es ~89 %, porque el campo
# `fecha` de cada driver no trae hora y se parsea como medianoche, así que la
# antigüedad nunca aporta sus 35 puntos completos.

def _sesgo_con_confianza(pct, prohibidos=()):
    return {
        "regimen_macro_global": {"codigo": "R3_ESTANFLACION_SHOCK"},
        "confianza_general": {"confianza_total_pct": pct},
        "activo": {"setups_prohibidos": list(prohibidos), "setups_permitidos": []},
    }


def test_el_umbral_de_confianza_sale_del_config_del_playbook():
    """Hardcodearlo lo dejaría fuera del `config_hash`, así que un cambio de
    criterio no quedaría registrado en la trazabilidad del snapshot."""
    import yaml

    cfg = yaml.safe_load((RAIZ / "config" / "playbook_config.yaml").read_text(encoding="utf-8"))
    assert cfg["confidence_weights"]["umbral_minimo_pct"] == 65.0
    assert sc.UMBRAL_CONFIANZA_PCT == 65.0


def test_una_confianza_insuficiente_excluye_el_activo():
    """El caso real del 2026-09-02 por la mañana: 54,6 %, con la clave de la TPM
    rota y el petróleo detenido ocho días. El activo no debía comunicarse y nada
    lo detenía."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con_confianza(54.6)},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "54.6" in res["excluido"] or "54,6" in res["excluido"]
    assert "65" in res["excluido"], "el motivo tiene que decir contra qué umbral"


def test_la_confianza_justo_en_el_umbral_no_excluye():
    """65,0 es el valor que da frescura y cobertura en 1,0. Excluirlo dejaría
    fuera la propia condición que el Playbook llama operación normal."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": _sesgo_con_confianza(65.0)},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res


def test_el_gate_de_confianza_no_alcanza_a_los_activos_sin_ficha():
    """La confianza mide los drivers macro que alimentan el régimen, y el régimen
    solo entra al sesgo de los 5 activos con ficha. Los otros 33 del catálogo se
    puntúan con técnica y calendario, sin insumo macro: bloquearlos por una
    confianza que no usan dejaría al escáner sin universo por nada."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {},  # sin entrada de sesgo: no es activo del Playbook
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert "excluido" not in res


def test_un_sesgo_con_error_no_se_confunde_con_confianza_baja():
    """`cargar_macro_bias` devuelve `{"error": ...}` cuando el snapshot está
    vencido o ilegible. Ese caso ya lo informa `_sesgos_playbook` como aviso, y
    fabricar acá un motivo de confianza sobre un payload que no la trae sería
    reportar dos veces la misma falla con nombres distintos."""
    assert sc.gate_confianza({"error": "STALE_DATA"}) is None
    assert sc.gate_confianza(None) is None


def test_un_payload_sin_confianza_declarada_bloquea():
    """Fail-closed, y por consistencia con `pipeline_datos.confianza_suficiente`.

    La primera versión de este gate dejaba pasar el campo ausente mientras el
    estado lo bloqueaba: dos comportamientos para el mismo caso. Un payload
    válido de `cargar_macro_bias` SIEMPRE trae `confianza_general`, así que su
    ausencia es un esquema viejo o un dict armado a mano, no una lectura buena.
    Asumir que alcanza sería la puerta de atrás que el umbral existe para cerrar.
    """
    motivo = sc.gate_confianza({"regimen_macro_global": {}, "activo": {}})
    assert motivo is not None
    assert "no declara" in motivo


# ─────────────────────────────────────────────────────────────────────────────
# La vigencia del sesgo viaja con la seleccion
# ─────────────────────────────────────────────────────────────────────────────
def test_la_seleccion_arrastra_la_vigencia_del_playbook():
    """El escaner ya tiene las dos piezas en la mano: el H1 con las anclas del
    Chandelier y el sesgo del activo. Resolverlo aca sale gratis y evita que el
    carrusel vuelva a pedir los mismos datos al terminal."""
    h1 = h1_perfecto()
    h1.update(chandelier_max=104.5, chandelier_min=94.0, chandelier_lookback=22)
    sesgo = {
        "regimen_macro_global": {"codigo": "R2_GOLDILOCKS_EXPANSION"},
        "confianza_general": {"confianza_total_pct": 90.0},
        "activo": {
            "sesgo_score": 1.80, "sesgo_etiqueta": "ALCISTA",
            "setups_permitidos": ["PULLBACK_EMA20_H1"], "setups_prohibidos": [],
            "parametros_riesgo": {
                "take_profit_tipo": "TRAILING_STOP_ASYMMETRIC",
                "trailing_stop_mult_atr": 3.0, "trailing_stop_lookback": 22,
            },
        },
    }

    res = sc.evaluar_activo(
        ACTIVO, [], None, {"XAUUSD": sesgo},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1, d1_con_consumo(0.30)),
    )

    assert "excluido" not in res, res.get("excluido")
    assert res["vigencia"]["gramatica"] == "NIVEL"
    assert res["vigencia"]["nivel"] == pytest.approx(104.5 - 3.0 * 2.0, abs=0.01)


def test_un_activo_sin_ficha_de_playbook_sale_sin_vigencia_y_no_se_cae():
    """Los 33 activos del catalogo sin ficha son la mayoria del universo. Su
    seleccion tiene que existir igual, con el campo en `None`."""
    res = sc.evaluar_activo(
        ACTIVO, [], None, {},
        AHORA.astimezone(sc.SANTIAGO),
        analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )

    assert "excluido" not in res
    assert res["vigencia"] is None


def test_el_modo_matriz_respeta_el_tope_por_grupo():
    """La matriz daba UNA pieza por grupo e ignoraba `--top`, asi que un canal
    con cinco activos elegibles recibia un carrusel de una sola pieza.

    El tope editorial del proyecto es de 3 piezas de activo por canal, y es el
    default de `--top`: la matriz tiene que llegar hasta ahi cuando hay con que,
    sin tocar los gates.
    """
    universo = sc.cargar_universo(solo_renderizables=False)
    cripto = [a for a in universo if a["categoria"] == "crypto"]
    assert len(cripto) >= 3, "el catalogo dejo de tener criptos suficientes para la prueba"

    h1 = h1_perfecto()
    d1 = d1_con_consumo(0.30)

    def escanear_con(top):
        res = sc.escanear(
            top=top, solo_renderizables=False, modo_matriz=True,
            analizador=analizador_falso(h1, d1),
        )
        return [s["ticker"] for s in res["seleccion"]
                if s["ticker"] in {a["ticker"] for a in cripto}]

    con_uno = escanear_con(1)
    con_tres = escanear_con(3)

    assert len(con_uno) == 1, f"con --top 1 la matriz dio {con_uno}"
    assert len(con_tres) == 3, (
        f"con --top 3 la matriz sigue dando {len(con_tres)} pieza(s) de cripto: {con_tres}"
    )
    assert con_tres[0] == con_uno[0], "el mejor del grupo cambio al subir el tope"


# ─────────────────────────────────────────────────────────────────────────────
# El gate de agotamiento no se apaga en silencio
# ─────────────────────────────────────────────────────────────────────────────
def test_un_gate_apagado_lo_dice_en_los_avisos():
    """Un gate inerte que no se anuncia es peor que no tenerlo.

    `--grupo` apagaba el de agotamiento sin decirlo, y el 2026-09-03 eso habria
    publicado el USD/JPY con el 290% de su rango diario consumido y EUR/USD con
    el 93%. El escaner informaba "0 exclusiones" cuando en realidad no habia
    mirado, que es exactamente el defecto que su propio modulo denuncia para el
    calendario.
    """
    res = sc.escanear(
        top=3, solo_renderizables=False, ignorar_agotamiento=True,
        analizador=analizador_falso(h1_perfecto(), d1_con_consumo(0.95)),
    )
    avisos = " ".join(res["avisos"]).lower()

    assert "agotamiento" in avisos, f"el gate apagado no aparece en los avisos: {res['avisos']}"
    assert "forzar" in avisos, "el aviso no dice como se apago"


def test_con_el_gate_encendido_no_hay_aviso_que_dar():
    """El aviso es de excepcion: en la corrida normal no ensucia la salida."""
    res = sc.escanear(
        top=3, solo_renderizables=False,
        analizador=analizador_falso(h1_perfecto(), d1_con_consumo(0.30)),
    )
    assert not any("agotamiento" in a.lower() for a in res["avisos"])


def test_pedir_un_grupo_ya_no_apaga_el_gate_de_agotamiento():
    """La decision del director: `--grupo` acotaba el universo Y apagaba el gate,
    dos cosas sin relacion. Ahora solo `--forzar` lo apaga, y lo dice.

    El manual del comando ya exigia esto: "una tanda de 2 piezas bien elegidas es
    mejor que una de 3 con un relleno". Apagar un gate para llenar cupos es
    justamente el relleno.
    """
    import inspect

    import pipeline_carrusel as pc

    fuente = inspect.getsource(pc.preparar)
    assert "ignorar_agotamiento=forzar," in fuente or "ignorar_agotamiento=forzar\n" in fuente, (
        "preparar sigue apagando el gate cuando se pide un grupo"
    )
    assert "grupo is not None" not in fuente.split("ignorar_agotamiento")[1][:80]


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
        eventos=[], delta_ust_bps=0.0, sesgos={},
        ahora_santiago=datetime(2026, 9, 4, 10, 0, tzinfo=sc.SANTIAGO),
        analizador=analizador_falso(h1, d1_con_consumo(0.30)),
    )
    assert "excluido" in res
    assert "score" not in res


def test_la_zona_de_aviso_llega_a_los_avisos_del_escaner():
    """Un aviso que se calcula y no se publica no sirve de nada.

    La zona de 0,70x a 1,00x no excluye: la pieza sale. Lo que no puede pasar es
    que salga sin que nadie sepa que sus bordes son estrechos para lo que ese
    activo se mueve.
    """
    res = sc.escanear(
        top=3, solo_renderizables=False,
        analizador=analizador_falso(
            h1_con_banda(banda=41.20, vela=33.00), d1_con_consumo(0.30)
        ),
    )
    avisos = " ".join(res["avisos"]).lower()
    assert "estrechos para su volatilidad" in avisos, res["avisos"]
    assert "0,80" in avisos, res["avisos"]


def test_una_banda_holgada_no_genera_aviso():
    res = sc.escanear(
        top=3, solo_renderizables=False,
        analizador=analizador_falso(
            h1_con_banda(banda=60.00, vela=33.00), d1_con_consumo(0.30)
        ),
    )
    assert not any("estrechos" in a for a in res["avisos"]), res["avisos"]
