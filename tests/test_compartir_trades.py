"""El mensaje de trades para el grupo de colegas: formato, riesgo y reglas de texto."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import compartir_trades as ct  # noqa: E402

CUENTA = SimpleNamespace(equity=9_000_000.0, currency="CLP", login=1)


def _fila(**extra):
    base = {
        "ticket": 1, "simbolo": "WTI.spot", "nombre": "Petróleo WTI", "digits": 3, "compra": False,
        "volumen": 0.62, "entrada": 100.344, "sl": 101.83, "tp": 97.407, "actual": 100.639,
        "flotante": -17949.0, "riesgo": 90414.0, "recompensa": 178625.0,
    }
    base.update(extra)
    return base


def test_numeros_en_notacion_chilena():
    assert ct.numero(4149.51, 2) == "4.149,51"
    assert ct.numero(100.344, 3) == "100,344"
    assert ct.numero(14197.0, 0) == "14197"
    assert ct.monto(9_125_619.4) == "9.125.619"


def test_el_signo_va_en_los_pesos():
    assert ct.con_signo(33083) == "+33.083"
    assert ct.con_signo(-17949) == "-17.949"


def test_el_riesgo_se_expresa_como_porcentaje_del_equity():
    texto = "\n".join(ct.bloque(_fila(), CUENTA.equity, True))
    assert "Riesgo si toca el stop: 1,00 % del capital (90.414 CLP)" in texto
    assert "Si llega al take profit: +178.625 CLP" in texto
    assert "Resultado ahora: -17.949 CLP" in texto


def test_sin_flotante_no_muestra_el_resultado():
    texto = "\n".join(ct.bloque(_fila(), CUENTA.equity, False))
    assert "Resultado ahora" not in texto


def test_sin_stop_ni_take_profit_lo_dice_en_vez_de_inventar():
    texto = "\n".join(ct.bloque(_fila(sl=0.0, tp=0.0, riesgo=None, recompensa=None), CUENTA.equity, True))
    assert "Sin stop loss" in texto and "Sin take profit" in texto
    assert "Riesgo si toca el stop" not in texto


def test_la_flecha_sigue_la_direccion_de_la_operacion():
    assert "⬆️" in ct.bloque(_fila(compra=True), CUENTA.equity, True)[0]
    assert "⬇️" in ct.bloque(_fila(compra=False), CUENTA.equity, True)[0]


def test_el_mensaje_lleva_capital_y_cumple_las_reglas_de_texto():
    uno = ct.armar_mensaje(CUENTA, [_fila()], True)
    assert "Capital de referencia: *9.000.000 CLP*" in uno
    assert uno.startswith("📌 *Trade abierto*")
    varios = ct.armar_mensaje(CUENTA, [_fila(), _fila(ticket=2)], True)
    assert varios.startswith("📌 *Trades abiertos*")
    for texto in (uno, varios):
        assert "—" not in texto and "–" not in texto, "guion largo en texto de cliente"
        assert "$" not in texto
