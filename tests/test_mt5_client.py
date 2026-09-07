"""`get_rates` tiene que seleccionar el símbolo antes de pedirle velas.

MT5 solo sirve `copy_rates_from_pos` para símbolos presentes en el Market Watch
del terminal. Sin `symbol_select` previo, la tool funciona para lo que el
director tenga abierto y falla para el resto, con un mensaje que no dice por qué:

    MT5_UNAVAILABLE: No se pudieron obtener datos para XAUUSD H1:
                     (-1, 'Terminal: Call failed')

Medido el 2026-09-02 desde un proceso nuevo: USDCLP respondió y XAUUSD, US100 y
WTI dieron ese error los tres. No es que el terminal estuviera caído —USDCLP
salió del mismo terminal en la misma llamada— sino que los otros tres no estaban
seleccionados.

Importa porque el sesgo del Playbook cubre cinco activos y la pieza que publica
«vigente hasta X» necesita la serie H1 de cada uno. Una dependencia invisible
del Market Watch deja piezas sin salir sin explicar la causa.

El fake de MetaTrader5 se inyecta en `sys.modules` porque `mt5_client` lo importa
de forma perezosa dentro de la función, justamente para no exigirlo en CI.
"""
from __future__ import annotations

import os
import sys
import types

import numpy as np
import pytest

from market_data_mcp import mt5_client


def _velas(n: int = 200):
    """El dtype estructurado que devuelve `copy_rates_from_pos`."""
    return np.array(
        [(1_700_000_000 + i * 3600, 100.0, 101.0, 99.0, 100.5, 10, 1, 0) for i in range(n)],
        dtype=[
            ("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
            ("close", "f8"), ("tick_volume", "u8"), ("spread", "i4"), ("real_volume", "u8"),
        ],
    )


@pytest.fixture
def mt5_falso(monkeypatch):
    """Un MetaTrader5 de mentira que registra el orden de las llamadas."""
    llamadas: list[str] = []
    fake = types.ModuleType("MetaTrader5")
    fake.TIMEFRAME_H1 = 16385
    fake.TIMEFRAME_D1 = 16408
    fake.seleccionable = True

    def symbol_select(ticker, habilitar):
        llamadas.append(f"symbol_select({ticker})")
        return fake.seleccionable

    def copy_rates_from_pos(ticker, tf, desde, n):
        llamadas.append(f"copy_rates_from_pos({ticker})")
        return _velas(n)

    fake.symbol_select = symbol_select
    fake.copy_rates_from_pos = copy_rates_from_pos
    fake.last_error = lambda: (-1, "Terminal: Call failed")
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    return fake, llamadas


def test_get_rates_selecciona_el_simbolo_antes_de_pedir_velas(mt5_falso):
    fake, llamadas = mt5_falso

    df = mt5_client.get_rates("XAUUSD", "H1", n_bars=200)

    assert len(df) == 200
    assert llamadas == ["symbol_select(XAUUSD)", "copy_rates_from_pos(XAUUSD)"], (
        f"orden incorrecto: {llamadas}"
    )


def test_un_simbolo_que_no_se_puede_seleccionar_lo_dice(mt5_falso):
    """`Terminal: Call failed` no orienta a nadie. El error tiene que nombrar la
    causa real y qué hacer, que es agregarlo al Market Watch."""
    fake, _ = mt5_falso
    fake.seleccionable = False

    with pytest.raises(RuntimeError, match="Market Watch"):
        mt5_client.get_rates("SIMBOLO_RARO", "H1")


# ---------------------------------------------------------------------------
# El .env lo carga quien necesita las credenciales, no solo el servidor MCP.
#
# Hasta el 2026-09-07 el parseo vivía únicamente en `server.py`, dentro del
# lifespan. Los siete scripts que llaman `connect()` directo (`extractor_precios`,
# `screener_gi`, `serie_mt5`, `pipeline_informe`, `generar_graficos_sesion_asiatica`)
# nunca cargaban ese archivo, así que las credenciales no tenían efecto **justo en
# el camino de la corrida automática**: el del reloj, con el terminal cerrado,
# donde `initialize()` sin credenciales se engancha a cualquier cuenta. El
# 2026-09-06 eso devolvió la 51256 en vez de la 51492.
#
# Es el modo de falla más caro del repo: no rompe nada visible, produce datos de
# otra cuenta con cara de correctos.
# ---------------------------------------------------------------------------


def test_cargar_env_lee_el_archivo_sin_pisar_lo_ya_definido(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# comentario\n"
        "\n"
        "MT5_LOGIN=51492\n"
        "MT5_SERVER=UnServidor-Server\n"
        "YA_DEFINIDA=del_archivo\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MT5_LOGIN", raising=False)
    monkeypatch.delenv("MT5_SERVER", raising=False)
    # Una variable exportada manda sobre el archivo: es lo que permite apuntar a
    # otra cuenta en una corrida puntual sin editar nada.
    monkeypatch.setenv("YA_DEFINIDA", "del_entorno")

    mt5_client.cargar_env(env)

    assert os.environ["MT5_LOGIN"] == "51492"
    assert os.environ["MT5_SERVER"] == "UnServidor-Server"
    assert os.environ["YA_DEFINIDA"] == "del_entorno"


def test_un_env_inexistente_no_revienta(tmp_path):
    # En CI y en un clon nuevo el archivo no está, y `connect()` tiene que poder
    # seguir hasta el initialize() sin credenciales.
    mt5_client.cargar_env(tmp_path / "no_existe.env")


def test_connect_carga_el_env_antes_de_leer_las_credenciales():
    """Contrato de orden, y el orden ES el arreglo.

    Leer `MT5_LOGIN` antes de cargar el archivo lo deja en 0 y cae al
    `initialize()` sin credenciales, que es exactamente el camino no determinista
    que esto viene a cerrar. El test mira el AST porque comprobarlo de verdad
    exigiría un terminal.
    """
    import ast
    import inspect
    import textwrap

    arbol = ast.parse(textwrap.dedent(inspect.getsource(mt5_client.connect)))

    linea_carga = None
    linea_login = None
    for nodo in ast.walk(arbol):
        if (
            linea_carga is None
            and isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "cargar_env"
        ):
            linea_carga = nodo.lineno
        # La constante exacta, no el texto suelto: `MT5_LOGIN` se nombra también
        # en el docstring, y comparar sobre la fuente cruda daba un falso rojo.
        if (
            linea_login is None
            and isinstance(nodo, ast.Constant)
            and nodo.value == "MT5_LOGIN"
        ):
            linea_login = nodo.lineno

    assert linea_carga is not None, (
        "connect() ya no llama a cargar_env(): los scripts que lo llaman directo se "
        "quedan sin credenciales y initialize() se engancha a la cuenta que haya."
    )
    assert linea_login is not None, "connect() ya no lee MT5_LOGIN; revisá este test"
    assert linea_carga < linea_login, (
        "connect() lee MT5_LOGIN antes de cargar el .env, así que el archivo no "
        "surte efecto y la conexión vuelve a ser no determinista."
    )


def test_el_server_no_tiene_su_propio_parseo_de_env():
    # Dos copias de la misma lectura divergen: el server terminaría cargando un
    # .env distinto del que cargan los scripts. Es el contrato por nombre de
    # siempre, y acá se evita delegando.
    from pathlib import Path

    fuente = (
        Path(__file__).resolve().parent.parent / "src" / "market_data_mcp" / "server.py"
    ).read_text(encoding="utf-8")
    assert "cargar_env" in fuente, "server.py tiene que delegar en mt5_client.cargar_env"
    assert "os.environ.setdefault" not in fuente, (
        "server.py volvió a parsear el .env por su cuenta en vez de delegar"
    )
