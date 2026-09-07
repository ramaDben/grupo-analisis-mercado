"""El guardia de cuenta de MT5.

Contexto del caso que lo motiva, porque cambia lo que hay que probar. El
2026-09-06 el terminal expuso DOS cuentas segun como se conectara: el camino del
repo (`mt5_client.connect()`, que se engancha al terminal que ya corre) daba la
51492, y un `mt5.initialize()` pelado en un proceso nuevo daba la 51256. La
ingesta usa el primer camino, asi que los datos estaban bien; pero el segundo
camino es alcanzable, y `connect()` cae en el cuando el terminal NO esta abierto,
porque el `.env` del repo no tiene credenciales de MT5.

O sea que el riesgo no es hipotetico: es la corrida automatica de las 09:30 con
el terminal cerrado. Y sin sello en el archivo, nadie lo notaria.
"""

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from guardrails import cuenta  # noqa: E402
from guardrails.motivos import MOTIVOS  # noqa: E402


ESPERADA = 51492


# ── el caso feliz ────────────────────────────────────────────────────────────
def test_la_cuenta_correcta_aprueba():
    assert cuenta.cuenta_correcta(ESPERADA, ESPERADA).ok


def test_acepta_el_login_como_texto():
    # Un JSON puede traerlo como cadena y eso no es un problema de cuenta.
    assert cuenta.cuenta_correcta("51492", ESPERADA).ok


# ── lo que tiene que frenar ──────────────────────────────────────────────────
def test_otra_cuenta_falla_y_nombra_las_dos():
    v = cuenta.cuenta_correcta(51256, ESPERADA)
    assert not v.ok
    assert v.motivo == "cuenta_mt5_inesperada"
    # Las dos cifras en el detalle: saber que "esta mal" no dice a que cambiar.
    assert "51256" in v.detalle and "51492" in v.detalle


def test_sin_sello_falla():
    """No saber vale lo mismo que estar mal.

    Es la decision central del modulo. Tratar la ausencia como permiso seria la
    puerta de atras que el guardia existe para cerrar: bastaria con que el
    extractor dejara de estampar el campo.
    """
    assert not cuenta.cuenta_correcta(None, ESPERADA).ok
    assert not cuenta.cuenta_correcta("", ESPERADA).ok


def test_un_sello_que_no_es_numero_falla():
    assert not cuenta.cuenta_correcta("demo", ESPERADA).ok
    assert not cuenta.cuenta_correcta({"login": 51492}, ESPERADA).ok


# ── el config, y el fail-closed cuando no se puede leer ──────────────────────
def test_el_config_declara_la_cuenta_del_director():
    """Cable trampa deliberado: la cifra esta escrita a mano aca.

    Si el director cambia de cuenta, este test se pone rojo. Es lo que se busca:
    cambiar la cuenta que alimenta los stops del Playbook tiene que ser una
    decision visible, no un config que alguien edita de paso. El resto de los
    tests usa ESPERADA como valor local y no depende del config.
    """
    assert cuenta.login_esperado() == ESPERADA


def test_config_ilegible_no_da_pase_libre(tmp_path):
    roto = tmp_path / "cuenta_mt5.json"
    roto.write_text("{ esto no es JSON", encoding="utf-8")
    assert cuenta.login_esperado(roto) is None
    # Y sin nada con que comparar, se niega en vez de aprobar.
    assert not cuenta.cuenta_correcta(ESPERADA, cuenta.login_esperado(roto)).ok


def test_config_ausente_no_lanza(tmp_path):
    # Los hooks consumen este modulo: uno que muere no protege.
    assert cuenta.login_esperado(tmp_path / "no_existe.json") is None


@pytest.mark.parametrize("valor", [None, "", "demo", {}, []])
def test_un_login_basura_en_el_config_no_pasa(tmp_path, valor):
    p = tmp_path / "cuenta_mt5.json"
    p.write_text(json.dumps({"login": valor}), encoding="utf-8")
    assert cuenta.login_esperado(p) is None


# ── varios activos a la vez ──────────────────────────────────────────────────
def test_revisar_aprueba_cuando_todos_coinciden():
    sellos = {a: ESPERADA for a in ("USDCLP", "XAUUSD", "WTI")}
    assert cuenta.revisar(sellos, ESPERADA).ok


def test_revisar_nombra_el_activo_que_esta_mal():
    sellos = {"USDCLP": ESPERADA, "XAUUSD": 51256, "WTI": ESPERADA}
    v = cuenta.revisar(sellos, ESPERADA)
    assert not v.ok
    # La ubicacion es el activo: "algo salio de otra cuenta" no dice que revisar,
    # y ese fue justamente el problema del caso de yfinance.
    assert v.ubicacion == "XAUUSD"


def test_revisar_sin_sellos_aprueba_porque_no_hay_nada_que_juzgar():
    """El vacio se decide arriba, no aca.

    `revisar({})` no tiene ningun dato que contradiga al config. Quien traduce
    "ningun activo trae sello" en un error es `pipeline_datos._motivo_cuenta`,
    que si sabe que un resumen de precios sin sellos es sospechoso.
    """
    assert cuenta.revisar({}, ESPERADA).ok


# ── el contrato con el catalogo ──────────────────────────────────────────────
def test_el_motivo_esta_en_el_catalogo():
    assert "cuenta_mt5_inesperada" in MOTIVOS


def test_el_motivo_no_es_publicable():
    # Un problema nuestro de datos no es contenido para el cliente.
    assert MOTIVOS["cuenta_mt5_inesperada"].publicable is False
