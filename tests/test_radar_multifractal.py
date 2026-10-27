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
from estrategia.tori.radar import Evento, LecturaMarco, RADAR_MARCOS  # noqa: E402

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


def _lectura(marco: str) -> LecturaMarco:
    ev = Evento(marco, "seguridad", "toco", None, 0.1, 1.2345, "A+", "rebote")
    return LecturaMarco(marco, "TENDENCIA", "ALCISTA", (), (ev,), (), 1_700_000_000, 0.01)


def _velas_cortas(ticker, marcos):
    df = pd.DataFrame({"time": [1_700_000_000 + i * 3600 for i in range(10)],
                       "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0,
                       "tick_volume": 1})
    return {m: df.copy() for m in marcos.todos}, None


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


def test_el_radar_no_puede_enviar_nada():
    fuente = (RAIZ / "scripts" / "radar_multifractal.py").read_text(encoding="utf-8")
    for prohibido in ("enviar_whatsapp", "whatsapp_sender", "despachar"):
        assert prohibido not in fuente
