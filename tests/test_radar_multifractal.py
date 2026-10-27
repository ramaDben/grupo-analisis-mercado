"""Orquestador del radar multifractal (spec del radar §4, §6, §8), con un MT5 falso.

Ningún test toca el terminal real: el `mt5` es un objeto de mentira y las velas las
entrega un `leer_velas` inyectado.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import radar_multifractal as rm  # noqa: E402
from estrategia.fuente import DURACION  # noqa: E402
from estrategia.tori.radar import (  # noqa: E402
    Evento, HistoriaInsuficiente, LecturaMarco, RADAR_MARCOS)

SANTIAGO = ZoneInfo("America/Santiago")
INICIO = datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO)
FULL = 4


class MT5Falso:
    """Lo mínimo del módulo MetaTrader5 que usa el radar."""

    SYMBOL_TRADE_MODE_FULL = FULL

    def __init__(self, simbolos=(), login=51257, sin_tick=(), reloj_visible=True):
        self._simbolos = list(simbolos)
        self._login = login
        self._sin_tick = set(sin_tick)        # tickers sin cotización ("*" = ninguno cotiza)
        self._reloj_visible = reloj_visible
        self.selecciones: list[tuple[str, bool]] = []
        self.ticks_pedidos: list[str] = []

    def symbols_get(self):
        return self._simbolos

    def symbol_info(self, ticker):
        return SimpleNamespace(name=ticker, visible=self._reloj_visible)

    def symbol_select(self, ticker, activo):
        self.selecciones.append((ticker, activo))
        return True

    def symbol_info_tick(self, ticker):
        # Qué estaba seleccionado cuando se pidió el tick: el orden importa.
        self.ticks_pedidos.append((ticker, tuple(self.selecciones)))
        if "*" in self._sin_tick or ticker in self._sin_tick:
            return None
        return SimpleNamespace(time=int(time.time()))

    def account_info(self):
        return SimpleNamespace(login=self._login)


def _sym(nombre, trade_mode=FULL, path="Forex\\Majors\\X", digits=5, visible=True):
    return SimpleNamespace(name=nombre, trade_mode=trade_mode, path=path,
                           digits=digits, visible=visible)


def _lectura(marco: str, vela: int | None = None) -> LecturaMarco:
    """Una lectura de mentira. Sin `vela`, la última cerrada es fresca contra el reloj real
    (el `MT5Falso` cotiza a `time.time()`), para que la guarda de frescura no la descarte."""
    if vela is None:
        vela = int(time.time()) - 2 * DURACION[marco]
    ev = Evento(marco, "seguridad", "toco", None, 0.1, 1.2345, "A+", "rebote")
    return LecturaMarco(marco, "TENDENCIA", "ALCISTA", (), (ev,), (), vela, 0.01)


def _velas_cortas(ticker, marcos):
    """Diez velas por marco cuya última cerrada es fresca contra el reloj real: la guarda
    de frescura mira las velas crudas, y unas de 2023 serían vencidas en todos los tests."""
    ahora = int(time.time())

    def df(marco):
        ultima = ahora - DURACION[marco] - 60
        return pd.DataFrame({"time": [ultima - (9 - i) * DURACION[marco] for i in range(10)],
                             "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0,
                             "tick_volume": 1})

    return {m: df(m) for m in marcos.todos}, None


def _reloj():
    return INICIO


def test_universo_filtra_trade_mode_full_y_toma_categoria_del_path():
    mt5 = MT5Falso([
        _sym("EURUSD", path="Forex\\Majors\\EURUSD", digits=5, visible=True),
        _sym("#AAPL", path="Stocks\\US\\AAPL", digits=2, visible=False),
        _sym("CERRADO", trade_mode=0),
        _sym("SOLOCIERRE", trade_mode=3),
    ])
    u = rm.universo(mt5)
    assert u == [
        rm.Simbolo("EURUSD", 5, "Forex", True),
        rm.Simbolo("#AAPL", 2, "Stocks", False),
    ]


def test_un_simbolo_que_falla_no_corta_el_escaneo(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))

    def leer_velas(ticker, marcos):
        if ticker == "MALO":
            raise RuntimeError("MT5 no entregó datos")
        return _velas_cortas(ticker, marcos)

    simbolos = [rm.Simbolo("MALO", 2, "Forex", True), rm.Simbolo("BUENO", 4, "Forex", True)]
    e = rm.escanear(simbolos, MT5Falso(), leer_velas=leer_velas, ahora=_reloj)
    assert e.leidos == 2
    assert [f.ticker for f in e.filas] == ["BUENO"]
    assert set(e.filas[0].marcos) == set(RADAR_MARCOS)
    assert set(e.filas[0].cierres) == set(RADAR_MARCOS)
    assert all(c.tzinfo is not None for c in e.filas[0].cierres.values())
    [falla] = e.fallas
    assert (falla.ticker, falla.marco) == ("MALO", None)
    assert "MT5 no entregó datos" in falla.motivo
    assert e.cuenta == 51257


def test_historia_insuficiente_queda_como_falla_del_marco():
    simbolos = [rm.Simbolo("CORTO", 2, "Forex", True)]
    e = rm.escanear(simbolos, MT5Falso(), leer_velas=_velas_cortas, ahora=_reloj)
    assert e.filas == ()
    assert {(f.ticker, f.marco) for f in e.fallas} == {("CORTO", m) for m in RADAR_MARCOS}
    # El texto de HistoriaInsuficiente, no el de un marco ausente: "H1: 10 velas de 600".
    for f in e.fallas:
        assert f.motivo == f"{f.marco}: 10 velas de {rm.MARCOS_RADAR.velas[f.marco]}"


def test_reloj_invisible_se_abre_para_leerlo_y_se_restaura():
    mt5 = MT5Falso(reloj_visible=False)
    rm.escanear([rm.Simbolo("X", 2, "Forex", True)], mt5, leer_velas=_velas_cortas, ahora=_reloj)
    [seleccion_al_pedir] = [sel for t, sel in mt5.ticks_pedidos if t == rm.RELOJ]
    assert seleccion_al_pedir == ((rm.RELOJ, True),)
    assert mt5.selecciones[-1] == (rm.RELOJ, False)


def test_sin_tick_del_reloj_usa_el_del_primer_simbolo_que_cotiza(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))
    mt5 = MT5Falso(sin_tick={rm.RELOJ, "A"})
    simbolos = [rm.Simbolo("A", 2, "Forex", True), rm.Simbolo("B", 2, "Forex", True)]
    e = rm.escanear(simbolos, mt5, leer_velas=_velas_cortas, ahora=_reloj)
    assert e.fallas == () and e.paridad == ()
    # La hora de cierre sale para todos, también para A, que se leyó antes de medir el reloj.
    assert all(set(f.cierres) == set(RADAR_MARCOS) for f in e.filas)
    # Y el encabezado dice con qué símbolo se midió: B, el primero que cotizó.
    assert e.avisos == ("reloj del servidor medido con B: revisa las horas",)


def test_un_desfase_sustituto_de_mas_de_14_horas_se_descarta(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))

    class TickViejo(MT5Falso):
        def symbol_info_tick(self, ticker):
            if ticker == rm.RELOJ:
                return None
            # Un mercado cerrado desde hace dos días: su último tick no es la hora del servidor.
            return SimpleNamespace(time=int(time.time()) - 2 * 86400)

    e = rm.escanear([rm.Simbolo("A", 2, "Forex", True)], TickViejo(),
                    leer_velas=_velas_cortas, ahora=_reloj)
    assert e.avisos == (rm.AVISO_SIN_RELOJ,)
    assert e.filas[0].cierres == {}


def test_con_el_reloj_propio_no_hay_aviso_de_reloj(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))
    e = rm.escanear([rm.Simbolo("A", 2, "Forex", True)], MT5Falso(),
                    leer_velas=_velas_cortas, ahora=_reloj)
    assert e.avisos == () and e.paridad == ()


def test_sin_ningun_tick_es_aviso_y_no_falla(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))
    mt5 = MT5Falso(sin_tick={"*"})
    e = rm.escanear([rm.Simbolo("A", 2, "Forex", True)], mt5, leer_velas=_velas_cortas, ahora=_reloj)
    assert e.fallas == ()
    assert [f.ticker for f in e.filas] == ["A"] and e.filas[0].cierres == {}
    # Es un aviso del escaneo, no de la paridad: va en el encabezado de la página.
    assert e.avisos == ("no se pudo medir el reloj del servidor: las horas de cierre no se muestran",)
    assert e.paridad == ()


def test_la_cuenta_verificada_se_pasa_y_no_se_vuelve_a_leer():
    class SinCuenta(MT5Falso):
        def account_info(self):
            raise AssertionError("la cuenta ya se verificó en main")

    e = rm.escanear([], SinCuenta(), leer_velas=_velas_cortas, ahora=_reloj, cuenta=51257)
    assert e.cuenta == 51257


def test_una_falla_inesperada_escribe_pagina_de_error(tmp_path, monkeypatch):
    monkeypatch.setattr(rm, "_terminal", lambda: MT5Falso([_sym("EURUSD")]))
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)

    def rota(*a, **k):
        raise TypeError("algo inesperado")

    monkeypatch.setattr(rm, "escanear", rota)
    assert rm.main(["--sin-abrir", "--salida", str(tmp_path)]) == 1
    pagina = (tmp_path / "ultimo.html").read_text(encoding="utf-8")
    assert "El radar falló" in pagina and "TypeError: algo inesperado" in pagina
    assert len(list(tmp_path.glob("*/radar_*.html"))) == 1


def test_un_marco_ausente_o_sin_rango_es_falla_del_marco_y_no_del_simbolo(monkeypatch):
    def leer_marco(velas, marco, digits, p=None):
        if marco == "D1":
            return velas["NO_EXISTE"]  # KeyError, como un marco que MT5 no entregó
        if marco == "H4":
            raise ValueError("las velas de H4 no tienen rango (ATR 0)")
        return _lectura(marco)

    monkeypatch.setattr(rm, "leer_marco", leer_marco)
    e = rm.escanear([rm.Simbolo("X", 2, "Forex", True)], MT5Falso(),
                    leer_velas=_velas_cortas, ahora=_reloj)
    assert set(e.filas[0].marcos) == {"H1"}
    assert {f.marco for f in e.fallas} == {"D1", "H4"}


def test_restaura_observacion_de_mercado_aunque_haya_excepcion():
    # leer_velas lanza a mitad -> symbol_select(t, False) se llamó para los visible=False
    mt5 = MT5Falso()
    simbolos = [rm.Simbolo("A", 2, "Forex", False), rm.Simbolo("B", 2, "Forex", True),
                rm.Simbolo("C", 2, "Forex", False)]

    def leer_velas(ticker, marcos):
        if ticker == "B":
            raise KeyboardInterrupt  # no la atrapa el escaneo: tiene que restaurar igual
        return _velas_cortas(ticker, marcos)

    with pytest.raises(KeyboardInterrupt):
        rm.escanear(simbolos, mt5, leer_velas=leer_velas, ahora=_reloj)
    assert ("A", False) in mt5.selecciones
    assert ("C", False) in mt5.selecciones
    assert ("B", False) not in mt5.selecciones


def test_cuenta_distinta_escribe_pagina_de_error_y_no_escanea(tmp_path, monkeypatch):
    mt5 = MT5Falso([_sym("EURUSD")], login=11111)
    monkeypatch.setattr(rm, "_terminal", lambda: mt5)
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)

    def no_escanear(*a, **k):
        raise AssertionError("con la cuenta equivocada no se escanea")

    monkeypatch.setattr(rm, "escanear", no_escanear)
    codigo = rm.main(["--sin-abrir", "--salida", str(tmp_path)])
    assert codigo == 1
    ultimo = (tmp_path / "ultimo.html").read_text(encoding="utf-8")
    assert "Cuenta MT5 inesperada" in ultimo
    assert "11111" in ultimo
    assert len(list(tmp_path.glob("*/radar_*.html"))) == 1


def test_mt5_que_no_responde_escribe_pagina_de_error(tmp_path, monkeypatch):
    monkeypatch.setattr(rm, "_terminal", lambda: MT5Falso())

    def connect():
        raise RuntimeError("MT5 initialize() falló")

    monkeypatch.setattr(rm.mt5_client, "connect", connect)
    assert rm.main(["--sin-abrir", "--salida", str(tmp_path)]) == 1
    assert "MT5 no responde" in (tmp_path / "ultimo.html").read_text(encoding="utf-8")


def test_corrida_completa_escribe_la_matriz_y_la_paridad_no_la_corta(tmp_path, monkeypatch):
    mt5 = MT5Falso([_sym("EURUSD"), _sym("GBPUSD")])
    monkeypatch.setattr(rm, "_terminal", lambda: mt5)
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))
    monkeypatch.setattr(rm, "velas_mt5", _velas_cortas)

    def ruta_rota():
        raise OSError("disco ausente")

    monkeypatch.setattr(rm, "ruta_objetos", ruta_rota)
    abiertos = []
    monkeypatch.setattr(rm.webbrowser, "open", abiertos.append)
    assert rm.main(["--simbolos", "EURUSD", "--salida", str(tmp_path)]) == 0
    pagina = (tmp_path / "ultimo.html").read_text(encoding="utf-8")
    assert "EURUSD" in pagina and "GBPUSD" not in pagina
    assert "no se pudo verificar la paridad: disco ausente" in pagina
    assert len(abiertos) == 1


class SinUniversoMT5(MT5Falso):
    def symbols_get(self):
        return None


@pytest.mark.parametrize("mt5", [SinUniversoMT5(), MT5Falso([])])
def test_un_universo_vacio_es_pagina_de_error_y_no_matriz_vacia(tmp_path, monkeypatch, mt5):
    monkeypatch.setattr(rm, "_terminal", lambda: mt5)
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)
    assert rm.main(["--sin-abrir", "--salida", str(tmp_path)]) == 1
    pagina = (tmp_path / "ultimo.html").read_text(encoding="utf-8")
    assert "MT5 no entregó el universo" in pagina and "symbols_get()" in pagina
    assert "Qué mirar hoy" not in pagina


def test_simbolos_que_no_existen_es_pagina_de_error(tmp_path, monkeypatch):
    monkeypatch.setattr(rm, "_terminal", lambda: MT5Falso([_sym("EURUSD")]))
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)
    assert rm.main(["--sin-abrir", "--salida", str(tmp_path), "--simbolos", "NOEXISTE,OTRO"]) == 1
    pagina = (tmp_path / "ultimo.html").read_text(encoding="utf-8")
    assert "MT5 no entregó el universo" in pagina
    assert "--simbolos" in pagina and "NOEXISTE, OTRO" in pagina


def test_con_archivo_fresco_la_paridad_siempre_resume(tmp_path, monkeypatch):
    import json
    mt5 = MT5Falso([_sym("EURUSD")])
    monkeypatch.setattr(rm, "_terminal", lambda: mt5)
    monkeypatch.setattr(rm.mt5_client, "connect", lambda: None)
    monkeypatch.setattr(rm, "leer_marco", lambda velas, marco, digits, p=None: _lectura(marco))
    monkeypatch.setattr(rm, "velas_mt5", _velas_cortas)
    archivo = tmp_path / "chart_objects.json"
    archivo.write_text(json.dumps({"generated_at": INICIO.strftime("%Y-%m-%d %H:%M"),
                                   "charts": [{"symbol": "GBPUSD", "timeframe": "H4"}]}),
                       encoding="utf-8")
    monkeypatch.setattr(rm, "ruta_objetos", lambda: archivo)
    monkeypatch.setattr(rm, "_ahora_santiago", lambda: INICIO)
    assert rm.main(["--sin-abrir", "--salida", str(tmp_path / "out")]) == 0
    pagina = (tmp_path / "out" / "ultimo.html").read_text(encoding="utf-8")
    assert "paridad: ningún gráfico abierto coincide con un activo leído" in pagina


# --- Frescura y sincronización (medido en vivo el 2026-10-26) ---------------------------
# Reloj controlado: UTC fijo y un servidor 3 h adelante. El desfase distinto de cero es a
# propósito: con 0, un signo invertido en `utc + offset` pasaría igual.
DESFASE = 3 * 3600
UTC_AHORA = int(datetime(2026, 10, 26, 22, 0, tzinfo=ZoneInfo("UTC")).timestamp())


def _servidor(*args) -> int:
    """Una hora del servidor como la entrega MT5: el reloj de pared del broker como epoch."""
    return int(datetime(*args, tzinfo=ZoneInfo("UTC")).timestamp())


HOY = {"H1": _servidor(2026, 10, 27, 0, 0), "H4": _servidor(2026, 10, 26, 20, 0),
       "D1": _servidor(2026, 10, 26, 0, 0)}   # frescas contra el servidor (27-10 01:00)
MAYO = {m: _servidor(2026, 5, 29, 15, 0) for m in RADAR_MARCOS}   # la caché local


class MT5Reloj(MT5Falso):
    """Cotiza con el reloj controlado, con el servidor `DESFASE` adelante de UTC."""

    def __init__(self, *a, utc=UTC_AHORA, ticks=None, **k):
        super().__init__(*a, **k)
        self._utc = utc
        self._ticks = dict(ticks or {})   # último tick (hora del servidor) por símbolo

    def symbol_info_tick(self, ticker):
        self.ticks_pedidos.append((ticker, tuple(self.selecciones)))
        if ticker in self._ticks:
            t = self._ticks[ticker]
            return None if t is None else SimpleNamespace(time=t)
        return SimpleNamespace(time=self._utc + DESFASE)


def _vela_de_las_velas(velas, marco, digits, p=None):
    """`leer_marco` falso: la última vela cerrada es la que entregó `leer_velas`."""
    return _lectura(marco, int(velas[marco]["time"].iloc[-1]))


def _lector(*secuencia):
    """`leer_velas` que entrega una tanda distinta por llamada y cuenta las llamadas."""
    llamadas = []

    def leer_velas(ticker, marcos):
        tanda = secuencia[min(len(llamadas), len(secuencia) - 1)]
        llamadas.append(ticker)
        return {m: pd.DataFrame({"time": [tanda[m]]}) for m in RADAR_MARCOS}, None

    return leer_velas, llamadas


def _escanear_con_reloj(simbolos, mt5, leer_velas, utc=UTC_AHORA):
    dormidas = []
    e = rm.escanear(simbolos, mt5, leer_velas=leer_velas, ahora=_reloj,
                    dormir=dormidas.append, utc=lambda: utc)
    return e, dormidas


def test_oculto_vencido_y_despues_fresco_entra_a_la_matriz_con_un_reintento(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    mt5 = MT5Reloj()
    leer_velas, llamadas = _lector(MAYO, HOY)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#NVDA", 2, "Stocks", False)], mt5, leer_velas)
    assert llamadas == ["#NVDA", "#NVDA"]
    assert dormidas == [rm.ESPERA_SINCRONIZACION_S]
    assert e.fallas == ()
    [fila] = e.filas
    assert {m: lm.vela for m, lm in fila.marcos.items()} == HOY
    assert ("#NVDA", True) in mt5.selecciones and mt5.selecciones[-1] == ("#NVDA", False)


def test_oculto_que_sigue_vencido_es_falla_por_marco_con_la_fecha(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    mt5 = MT5Reloj()
    leer_velas, llamadas = _lector(MAYO)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#AAL", 2, "Stocks", False)], mt5, leer_velas)
    # Los intentos de la primera pasada y la relectura de la segunda, que no espera.
    assert len(llamadas) == rm.INTENTOS_SINCRONIZACION + 1
    assert dormidas == [rm.ESPERA_SINCRONIZACION_S] * (rm.INTENTOS_SINCRONIZACION - 1)
    assert e.filas == ()
    assert {(f.ticker, f.marco) for f in e.fallas} == {("#AAL", m) for m in RADAR_MARCOS}
    h1 = next(f for f in e.fallas if f.marco == "H1")
    # Abre 29-05 15:00 servidor, cierra 16:00 servidor = 13:00 UTC = 09:00 en Santiago.
    assert h1.motivo == "velas desactualizadas en MT5: la última vela cerrada es del 29-05 09:00"
    assert mt5.selecciones[-1] == ("#AAL", False)


def test_visible_con_velas_vencidas_es_falla_sin_reintentos(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    mt5 = MT5Reloj()
    leer_velas, llamadas = _lector(MAYO)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("EURUSD", 5, "Forex", True)], mt5, leer_velas)
    # Sin reintentos ni esperas en la primera pasada; solo la relectura de la segunda.
    assert llamadas == ["EURUSD", "EURUSD"] and dormidas == []
    assert e.filas == ()
    assert all("velas desactualizadas" in f.motivo for f in e.fallas)
    assert ("EURUSD", True) not in mt5.selecciones


def test_accion_el_lunes_a_las_0730_con_la_vela_del_viernes_es_fresca(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    # Lunes 26-10 07:30 Santiago = 10:30 UTC; la bolsa cerró el viernes.
    lunes = int(datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO).timestamp())
    viernes = {"H1": _servidor(2026, 10, 23, 16, 0), "H4": _servidor(2026, 10, 23, 16, 0),
               "D1": _servidor(2026, 10, 23, 0, 0)}
    # El último tick de la acción es el del cierre del viernes, 16:59 del servidor: cae
    # dentro de la hora que sigue a la H1 de las 16:00, así que no pide reintento.
    mt5 = MT5Reloj(utc=lunes, ticks={"#AAPL": _servidor(2026, 10, 23, 16, 59)})
    leer_velas, llamadas = _lector(viernes)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#AAPL", 2, "Stocks", False)], mt5,
                                      leer_velas, utc=lunes)
    assert e.fallas == () and dormidas == [] and llamadas == ["#AAPL"]
    assert set(e.filas[0].marcos) == set(RADAR_MARCOS)


def test_el_borde_de_frescura_se_mide_en_hora_del_servidor(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    ahora_servidor = UTC_AHORA + DESFASE
    limite = rm.DURACION["H1"] + rm.HOLGURA_FRESCURA_S
    # Una H1 que cerró justo en el límite sigue fresca; una hora más vieja, ya no. Con el
    # signo del desfase invertido (servidor 6 h antes), la vencida pasaría como fresca.
    justa = ahora_servidor - limite - rm.DURACION["H1"]
    for vela, vencida in ((justa, False), (justa - 3600, True)):
        tanda = dict(HOY, H1=vela)
        leer_velas, _ = _lector(tanda)
        e, _ = _escanear_con_reloj([rm.Simbolo("X", 2, "Forex", True)], MT5Reloj(), leer_velas)
        assert (("X", "H1") in {(f.ticker, f.marco) for f in e.fallas}) is vencida


# La caché que deja el propio radar: deselecciona al terminar, así que al día siguiente la
# primera lectura de un oculto trae las velas de ayer. Pasan la guarda de cuatro días.
AYER = {m: v - 86400 for m, v in HOY.items()}


def test_oculto_con_cache_de_un_dia_y_tick_fresco_se_reintenta(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    # Ninguna vela de ayer la detecta la guarda de cuatro días: el reintento es del tick.
    assert not any(rm._vencida(AYER[m], m, UTC_AHORA + DESFASE) for m in RADAR_MARCOS)
    mt5 = MT5Reloj()
    leer_velas, llamadas = _lector(AYER, HOY)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#NVDA", 2, "Stocks", False)], mt5, leer_velas)
    assert llamadas == ["#NVDA", "#NVDA"]
    assert dormidas == [rm.ESPERA_SINCRONIZACION_S]
    assert e.fallas == ()
    [fila] = e.filas
    assert {m: lm.vela for m, lm in fila.marcos.items()} == HOY


def test_oculto_con_cache_de_un_dia_que_no_se_repone_es_falla_por_marco(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    leer_velas, llamadas = _lector(AYER)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#AAL", 2, "Stocks", False)], MT5Reloj(),
                                      leer_velas)
    assert len(llamadas) == rm.INTENTOS_SINCRONIZACION + 1
    assert dormidas == [rm.ESPERA_SINCRONIZACION_S] * (rm.INTENTOS_SINCRONIZACION - 1)
    assert e.filas == ()
    # Exactamente una falla por marco: sin duplicados.
    assert len(e.fallas) == len(RADAR_MARCOS)
    assert {f.marco for f in e.fallas} == set(RADAR_MARCOS)
    assert all(f.motivo.startswith("velas desactualizadas en MT5") for f in e.fallas)


def test_visible_con_cache_de_un_dia_no_se_reintenta(monkeypatch):
    # El disparo por tick es solo para ocultos: uno visible ya estaba sincronizando.
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    leer_velas, llamadas = _lector(AYER, HOY)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("EURUSD", 5, "Forex", True)], MT5Reloj(),
                                      leer_velas)
    assert llamadas == ["EURUSD"] and dormidas == [] and e.fallas == ()


def _motor_que_rechaza(viejas):
    """`leer_marco` falso: con velas de la caché, historia insuficiente, como una caché corta."""
    def leer_marco(velas, marco, digits, p=None):
        vela = int(velas[marco]["time"].iloc[-1])
        if vela == viejas[marco]:
            raise HistoriaInsuficiente(f"{marco}: 1 velas de {rm.MARCOS_RADAR.velas[marco]}")
        return _lectura(marco, vela)
    return leer_marco


def test_cache_corta_se_reintenta_en_vez_de_ser_historia_insuficiente(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _motor_que_rechaza(AYER))
    leer_velas, llamadas = _lector(AYER, HOY)
    e, dormidas = _escanear_con_reloj([rm.Simbolo("#ABT", 2, "Stocks", False)], MT5Reloj(),
                                      leer_velas)
    assert llamadas == ["#ABT", "#ABT"] and dormidas == [rm.ESPERA_SINCRONIZACION_S]
    assert e.fallas == ()
    assert {m: lm.vela for m, lm in e.filas[0].marcos.items()} == HOY


def test_cache_corta_que_no_se_repone_dice_desactualizadas_y_no_historia(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _motor_que_rechaza(AYER))
    leer_velas, _ = _lector(AYER)
    e, _ = _escanear_con_reloj([rm.Simbolo("#ABT", 2, "Stocks", False)], MT5Reloj(), leer_velas)
    assert e.filas == ()
    assert len(e.fallas) == len(RADAR_MARCOS)
    assert all(f.motivo.startswith("velas desactualizadas en MT5") for f in e.fallas)


def test_sin_desfase_la_guarda_no_usa_el_tick_viejo_del_simbolo(monkeypatch):
    # El reloj no cotiza y el tick del símbolo es de mayo (el sustituto se rechaza). Antes
    # la guarda medía contra ese tick y las velas de mayo pasaban como frescas.
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    mt5 = MT5Reloj(ticks={rm.RELOJ: None, "EURUSD": MAYO["H1"] + 3599})
    leer_velas, _ = _lector(MAYO)
    e, _ = _escanear_con_reloj([rm.Simbolo("EURUSD", 5, "Forex", True)], mt5, leer_velas)
    assert e.avisos == (rm.AVISO_SIN_RELOJ,)
    assert e.filas == ()
    assert {f.marco for f in e.fallas} == set(RADAR_MARCOS)
    assert all(f.motivo.endswith("(hora del servidor)") for f in e.fallas)


def test_preselecciona_todos_los_ocultos_antes_de_leer_y_los_cierra_aunque_falle():
    mt5 = MT5Falso()
    simbolos = [rm.Simbolo("A", 2, "Forex", False), rm.Simbolo("B", 2, "Forex", True),
                rm.Simbolo("C", 2, "Forex", False)]
    seleccion_al_leer = []

    def leer_velas(ticker, marcos):
        seleccion_al_leer.append(tuple(mt5.selecciones))
        raise KeyboardInterrupt   # el primero ya corta: igual tiene que restaurar todo

    with pytest.raises(KeyboardInterrupt):
        rm.escanear(simbolos, mt5, leer_velas=leer_velas, ahora=_reloj, dormir=lambda s: None)
    # Antes de la primera lectura, los dos ocultos ya estaban seleccionados.
    [antes] = seleccion_al_leer
    assert ("A", True) in antes and ("C", True) in antes and ("B", True) not in antes
    assert ("A", False) in mt5.selecciones and ("C", False) in mt5.selecciones
    assert ("B", False) not in mt5.selecciones


def test_viejo_en_la_primera_pasada_y_fresco_en_la_segunda_entra_a_la_matriz(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    # Un oculto lento: sus intentos de la primera pasada traen la caché; al final, hoy.
    secuencia = [MAYO] * rm.INTENTOS_SINCRONIZACION + [HOY]
    leer_velas, llamadas = _lector(*secuencia)
    otro, _ = _lector(HOY)

    def leer(ticker, marcos):
        return leer_velas(ticker, marcos) if ticker == "#LENTO" else otro(ticker, marcos)

    simbolos = [rm.Simbolo("#LENTO", 2, "Stocks", False), rm.Simbolo("EURUSD", 5, "Forex", True)]
    e, dormidas = _escanear_con_reloj(simbolos, MT5Reloj(), leer)
    assert len(llamadas) == rm.INTENTOS_SINCRONIZACION + 1
    # La segunda pasada no duerme: solo las esperas de la primera.
    assert dormidas == [rm.ESPERA_SINCRONIZACION_S] * (rm.INTENTOS_SINCRONIZACION - 1)
    assert e.fallas == ()
    assert [f.ticker for f in e.filas] == ["#LENTO", "EURUSD"]
    assert {m: lm.vela for m, lm in e.filas[0].marcos.items()} == HOY


def test_la_segunda_pasada_que_sigue_vieja_deja_la_primera(monkeypatch):
    monkeypatch.setattr(rm, "leer_marco", _vela_de_las_velas)
    # Primera pasada: H1 viejo y el resto fresco. Segunda: todo viejo. Queda la primera.
    parcial = dict(HOY, H1=MAYO["H1"])
    leer_velas, llamadas = _lector(*([parcial] * rm.INTENTOS_SINCRONIZACION + [MAYO]))
    e, _ = _escanear_con_reloj([rm.Simbolo("#X", 2, "Stocks", False)], MT5Reloj(), leer_velas)
    assert len(llamadas) == rm.INTENTOS_SINCRONIZACION + 1
    assert set(e.filas[0].marcos) == {"H4", "D1"}
    assert [f.marco for f in e.fallas] == ["H1"]


def test_el_radar_no_puede_enviar_nada():
    fuente = (RAIZ / "scripts" / "radar_multifractal.py").read_text(encoding="utf-8")
    for prohibido in ("enviar_whatsapp", "whatsapp_sender", "despachar"):
        assert prohibido not in fuente
