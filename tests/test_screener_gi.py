"""Contrato del escáner de tandas: los gates, el anclaje horario y la estrategia.

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


AHORA = datetime(2026, 8, 25, 10, 30, tzinfo=NY)


# ─────────────────────────────────────────────────────────────────────────────
# Los gates: exclusiones, no puntos
# ─────────────────────────────────────────────────────────────────────────────
def test_el_blackout_del_calendario_excluye_al_activo():
    # NFP a las 09:30 hora Chile, ventana -15/+30 -> 09:15 a 10:00.
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 09:30"}
    dentro = datetime(2026, 8, 25, 9, 40, tzinfo=sc.SANTIAGO)
    motivo = sc.gate_blackout("XAUUSD", [evento], dentro)
    assert motivo and "blackout" in motivo
    assert "09:15" in motivo and "10:00" in motivo


def test_fuera_de_la_ventana_el_mismo_evento_no_bloquea():
    """Es la diferencia entre esperar la absorción del dato y no publicar nunca."""
    evento = {"nombre": "Nonfarm Payrolls", "pais": "United States", "impacto": "alto",
              "hora_servidor": "2026-08-25 09:30"}
    fuera = datetime(2026, 8, 25, 11, 0, tzinfo=sc.SANTIAGO)
    assert sc.gate_blackout("XAUUSD", [evento], fuera) is None


def test_un_blackout_de_alcance_local_no_toca_a_los_demas_activos():
    """Un Imacec bloquea al peso, no al Oro."""
    evento = {"nombre": "Imacec (YoY)", "pais": "Chile", "hora_servidor": "2026-08-25 08:30"}
    dentro = datetime(2026, 8, 25, 8, 35, tzinfo=sc.SANTIAGO)
    assert "blackout" in sc.gate_blackout("USDCLP", [evento], dentro)
    assert sc.gate_blackout("XAUUSD", [evento], dentro) is None


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
# La primera versión del escáner tenía estas tablas escritas en español, así que
# ningún blackout se activaba: el escáner informaba "0 exclusiones" cuando en
# realidad no había mirado nada. Un fallo en silencio, que es la peor clase.
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


def test_todo_activo_de_un_canal_cubierto_trae_la_nota_de_su_marco():
    """Contrato: sin la nota, el mensaje no puede justificar su temporalidad.

    `CLAUDE.md` declara esa linea obligatoria desde el issue #44. El marco lo
    decide la estrategia activa, asi que la nota que se publica es la de
    `notas_marco` para ese marco, no una nota generica del activo.
    """
    import pipeline_carrusel as pc

    marco = pc.marco_operativo()
    cubiertos, _ = sc.solo_canales_cubiertos(sc.cargar_universo(solo_renderizables=True))
    sin_nota = [a["ticker"] for a in cubiertos if not a["notas_marco"].get(marco)]
    assert not sin_nota, f"activos de canales cubiertos sin nota de {marco}: {sin_nota}"


def test_la_volatilidad_declarada_es_una_de_las_tres_etiquetas():
    validas = {"baja", "media", "alta"}
    raras = {
        a["ticker"]: a.get("volatilidad")
        for a in sc.cargar_universo(solo_renderizables=False)
        if a.get("volatilidad") not in validas
    }
    assert not raras, raras


def test_toda_nota_nombra_el_marco_que_justifica():
    """La nota se publica detras de "Por que 4H aca:". Si habla de otro marco, o de
    los drivers del activo sin nombrar ninguno, la linea promete una justificacion
    y entrega otra cosa (paso con Solana, GBP/USD, cobre y bitcoin en 2026-09)."""
    import pipeline_carrusel as pc

    sin_el = [
        f"{a['ticker']} {marco}"
        for a in sc.cargar_universo(solo_renderizables=False)
        for marco, nota in a["notas_marco"].items()
        if pc.ETIQUETA_CORTA.get(marco, marco) not in nota
    ]
    assert not sin_el, f"notas que no nombran su marco: {sin_el}"


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
    ref = Referencia(11.5, "línea alcista de control", lin)
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


def test_seleccion_fija_arma_la_entrada_de_un_activo_con_su_lectura(tmp_path):
    activo = next(a for a in sc.cargar_universo(True) if a["ticker"] == "XAUUSD")
    sel = sc.seleccion_fija(activo, NY_LUNES.astimezone(SCL), lector=_lector, estrategia=_Est({}),
                            base=tmp_path)
    assert sel["ticker"] == "XAUUSD" and sel["cobertura_fija"] is True
    assert sel["lectura"]["ticker"] == "XAUUSD" and sel["marco"] == "H4"
