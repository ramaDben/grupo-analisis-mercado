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


def test_activo_por_alias_en_espanol():
    o = leer("/activo oro")
    assert (o.pieza, o.args, o.trader) == ("activo", {"ticker": "XAUUSD"}, None)


@pytest.mark.parametrize("texto,ticker", [
    ("/activo USD/CLP", "USDCLP"),
    ("/activo usdclp", "USDCLP"),
    ("/activo dólar", "USDCLP"),
    ("/activo wti", "WTI.spot"),
    ("/activo petróleo", "WTI.spot"),
    ("/activo nasdaq", "US100.spot"),
    ("/activo us100", "US100.spot"),
    ("/activo aapl", "#AAPL"),
    ("/activo Cobre", "COPPER"),
])
def test_resuelve_ticker_del_broker(texto, ticker):
    assert leer(texto).args["ticker"] == ticker


def test_trader_con_tildes_y_espacios():
    o = leer("/activo oro para María José Núñez")
    assert o.trader == "María José Núñez"


def test_comando_con_arroba_del_bot():
    assert leer("/activo@GI_Analistas_Bot oro").args["ticker"] == "XAUUSD"


@pytest.mark.parametrize("nombre", [
    "Juan <script>",
    "Juan; rm -rf",
    "Juan {{titular}}",
    "x",
    "a" * 61,
    "Juan 123",
])
def test_rechaza_nombres_de_trader_peligrosos_o_raros(nombre):
    with pytest.raises(od.PedidoInvalido):
        leer(f"/activo oro para {nombre}")


def test_activo_desconocido_dice_cual():
    with pytest.raises(od.PedidoInvalido, match="pizza"):
        leer("/activo pizza")


def test_activo_sin_argumento():
    with pytest.raises(od.PedidoInvalido):
        leer("/activo")


@pytest.mark.parametrize("texto,alcance", [
    ("/calendario", "hoy"),
    ("/calendario hoy", "hoy"),
    ("/calendario semana", "semana"),
])
def test_calendario(texto, alcance):
    o = leer(texto)
    assert (o.pieza, o.args) == ("calendario", {"alcance": alcance})


def test_calendario_alcance_invalido():
    with pytest.raises(od.PedidoInvalido):
        leer("/calendario mes")


def test_dato_por_defecto_es_el_ultimo():
    assert leer("/dato").args == {"busqueda": "ultimo"}


def test_dato_con_nombre_y_trader():
    o = leer("/dato IPC para Juan Pérez")
    assert o.args == {"busqueda": "ipc"} and o.trader == "Juan Pérez"


def test_dato_rechaza_simbolos():
    with pytest.raises(od.PedidoInvalido):
        leer("/dato ipc; borrar")


@pytest.mark.parametrize("texto,momento", [
    ("/jornada", None),
    ("/jornada apertura", "apertura"),
    ("/jornada cierre", "cierre"),
])
def test_jornada(texto, momento):
    assert leer(texto).args == {"momento": momento}


def test_comando_desconocido():
    with pytest.raises(od.PedidoInvalido):
        leer("/borrar todo")


@pytest.mark.parametrize("texto", ["/start", "/ayuda", "/id"])
def test_comandos_de_servicio(texto):
    assert leer(texto).pieza == texto[1:]


def test_clave_de_reuso_ignora_al_trader():
    a = leer("/activo oro para Juan Pérez")
    b = leer("/activo oro")
    assert a.clave_base() == b.clave_base()


def test_todos_los_alias_apuntan_a_activos_del_catalogo_real():
    import screener_gi as sc

    reales = {a["ticker"] for a in sc.cargar_universo(solo_renderizables=False)}
    assert set(od.ALIAS.values()) <= reales
