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
    }


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


def test_escanear_con_modo_matriz_selecciona_un_activo_por_grupo():
    """Modo matriz de cobertura total: debe seleccionar hasta 1 activo por grupo."""
    def fake_analizador(ticker, tf):
        res = dict(h1_perfecto() if tf == "H1" else d1_con_consumo(0.30))
        res["ticker"] = ticker
        return res

    resultado = sc.escanear(
        tanda=1,
        solo_renderizables=True,
        analizador=fake_analizador,
        modo_matriz=True,
    )
    seleccion = resultado["seleccion"]
    assert len(seleccion) > 0
    # Ningún grupo debe estar repetido en la selección
    import pipeline_carrusel as pc
    grupos_sel = [pc.obtener_grupo_whatsapp(s["clase"], s["ticker"]) for s in seleccion]
    assert len(grupos_sel) == len(set(grupos_sel)), "El modo matriz no debe repetir grupos"



# ─────────────────────────────────────────────────────────────────────────────
# Vocabulario de prohibiciones: el gate tiene que conocer TODOS los tokens
# ─────────────────────────────────────────────────────────────────────────────

def _sesgo_con(prohibidos, regimen="R0_CALMA_RANGO"):
    return {
        "regimen_macro_global": {"codigo": regimen},
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
