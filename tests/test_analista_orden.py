"""Gramática del pedido del bot de analistas (spec 2026-10-08-bot-telegram-analistas)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import orden as od  # noqa: E402

UNIVERSO = [
    {"ticker": "USDCLP", "nombre": "Dólar / Peso Chileno"},
    {"ticker": "XAUUSD", "nombre": "Oro"},
    {"ticker": "WTI.spot", "nombre": "Petróleo WTI"},
    {"ticker": "US100.spot", "nombre": "Nasdaq 100"},
    {"ticker": "COPPER", "nombre": "Cobre Grado A"},
    {"ticker": "#AAPL", "nombre": "Apple"},
]


def leer(texto: str) -> od.Orden:
    return od.interpretar(texto, universo=UNIVERSO)


def test_oportunidad_no_lleva_argumentos():
    assert od.interpretar("/oportunidad") == od.Orden("oportunidad", {})


def test_seguimiento_resuelve_el_activo():
    universo = [{"ticker": "XAUUSD", "nombre": "Oro"}]
    assert od.interpretar("/seguimiento oro", universo) == od.Orden("seguimiento", {"ticker": "XAUUSD"})
    assert od.interpretar("/seguimiento xau", universo).args == {"ticker": "XAUUSD"}


def test_lo_que_sigue_al_activo_es_el_saludo_al_cliente():
    universo = [{"ticker": "USDCLP", "nombre": "USD/CLP"}]
    o = od.interpretar("/seguimiento oro Juan", universo)
    assert o.args == {"ticker": "XAUUSD"} and o.saludo == "Juan"
    assert od.interpretar("/seguimiento oro Estimado Sr. Pérez", universo).saludo == "Estimado Sr. Pérez"
    assert od.interpretar("/seguimiento oro", universo).saludo == ""
    # El saludo no cambia la identidad de la pieza que se reusa.
    assert o.clave_base() == od.interpretar("/seguimiento oro", universo).clave_base()


def test_el_saludo_no_admite_guion_largo_ni_textos_largos():
    assert od.interpretar("/seguimiento oro Juan — hola", []).saludo == "Juan hola"
    with pytest.raises(od.PedidoInvalido, match="muy largo"):
        od.interpretar("/seguimiento oro " + "x" * 80, [])


def test_seguimiento_sin_activo_explica_como_pedirlo():
    with pytest.raises(od.PedidoInvalido, match="/seguimiento oro"):
        od.interpretar("/seguimiento", [])


@pytest.mark.parametrize("cmd", ["/activo oro", "/calendario hoy", "/dato ipc", "/jornada apertura"])
def test_los_comandos_retirados_responden_con_la_ayuda(cmd):
    assert od.interpretar(cmd, []).pieza == "ayuda"


@pytest.mark.parametrize("texto,ticker", [
    ("/seguimiento USD/CLP", "USDCLP"),
    ("/seguimiento usdclp", "USDCLP"),
    ("/seguimiento dólar", "USDCLP"),
    ("/seguimiento wti", "WTI.spot"),
    ("/seguimiento petróleo", "WTI.spot"),
    ("/seguimiento nasdaq", "US100.spot"),
    ("/seguimiento us100", "US100.spot"),
    ("/seguimiento aapl", "#AAPL"),
    ("/seguimiento Cobre", "COPPER"),
])
def test_resuelve_ticker_del_broker(texto, ticker):
    assert leer(texto).args["ticker"] == ticker


def test_comando_con_arroba_del_bot():
    assert leer("/seguimiento@GI_Analistas_Bot oro").args["ticker"] == "XAUUSD"


def test_activo_desconocido_dice_cual():
    with pytest.raises(od.PedidoInvalido, match="pizza"):
        leer("/seguimiento pizza")


def test_comando_desconocido():
    with pytest.raises(od.PedidoInvalido):
        leer("/borrar todo")


@pytest.mark.parametrize("texto", ["/start", "/ayuda", "/id"])
def test_comandos_de_servicio(texto):
    assert leer(texto).pieza == texto[1:]


@pytest.mark.parametrize("texto", ["/seguimiento oro para Juan Pérez", "/oportunidad para Ana"])
def test_para_trader_ya_no_se_acepta(texto):
    with pytest.raises(od.PedidoInvalido) as exc:
        leer(texto)
    assert str(exc.value) == od.PERSONALIZACION_RETIRADA


def test_orden_no_tiene_trader():
    assert not hasattr(leer("/seguimiento oro"), "trader")


def test_todos_los_alias_apuntan_a_activos_del_catalogo_real():
    import screener_gi as sc

    reales = {a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)}
    assert set(od.ALIAS.values()) <= reales



def test_oportunidad_no_lleva_argumentos_ni_admite_personalizar():
    assert od.interpretar("/oportunidad") == od.Orden("oportunidad", {})
    assert od.interpretar("/oportunidad de hoy") == od.Orden("oportunidad", {})
    with pytest.raises(od.PedidoInvalido, match="ya no se personalizan"):
        od.interpretar("/oportunidad para Juan")
