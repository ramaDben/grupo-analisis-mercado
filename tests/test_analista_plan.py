"""Plan de escenarios del informe de activo: textos de Python, cifras con los digits del activo."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import esquema as es  # noqa: E402
from analista import plan as pl  # noqa: E402
from analista.estadistica import Estadistica  # noqa: E402

H1 = {"price": 4010.0, "s1": 3990.0, "r1": 4020.0, "atr_14": 8.0, "ema_50": 4000.0,
      "niveles_origen": {"s1": "swing", "r1": "swing", "s2": "atr", "r2": "atr"}}
VELA = {"close": 4012.0, "hh22": 4030.0, "ll22": 3970.0, "atr22": 9.0, "vela": "2026-10-08 10:00:00"}
CON_VENTAJA = Estadistica(42, 64, 55, "2025-01-27", "2026-10-08")


def test_plan_alcista_con_ventaja():
    p = pl.armar(H1, 2, "Alcista", "Oro", CON_VENTAJA, VELA)
    assert p["hay_plan"] and "cierre de vela de 1 hora sobre 4.020,00" in p["gatillo"]
    assert "4.003,00" in p["invalidacion"]  # 4030 - 3 x 9
    assert "12,00" in p["recorrido"] and "4.032" not in p["recorrido"]  # distancia, nunca precio
    assert "27-01-2025" in p["estadistica"] and "2025-01-27" not in p["estadistica"]
    assert "42 veces" in p["estadistica"] and "64 %" in p["estadistica"] and "55 %" in p["estadistica"]
    assert "misma tendencia" in p["estadistica"] and "no ha mostrado ventaja" not in p["estadistica"]
    assert p["estado"].startswith("Armado")
    assert p["niveles"] == {"gatillo": 4020.0, "invalidacion": 4003.0, "recorrido": 12.0, "vela": "2026-10-08 10:00:00"}


def test_sin_ventaja_lo_dice():
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(42, 57, 55, "2025-01-27", "2026-10-08"), VELA)
    assert "no ha mostrado ventaja" in p["estadistica"]


def test_muestra_insuficiente_sin_porcentaje():
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(12, None, 55, "2025-01-27", "2026-10-08"), VELA)
    assert "Muestra insuficiente" in p["estadistica"] and "%" not in p["estadistica"]


def test_sin_historia():
    p = pl.armar(H1, 2, "Alcista", "Oro", None, VELA)
    assert p["hay_plan"] and "Sin historia suficiente" in p["estadistica"]


def test_nivel_de_respaldo_atr_no_tiene_plan():
    h1 = {**H1, "niveles_origen": {**H1["niveles_origen"], "r1": "atr"}}
    p = pl.armar(h1, 2, "Alcista", "Oro", CON_VENTAJA, VELA)
    assert not p["hay_plan"] and "estructura" in p["motivo"]


def test_bajista_es_espejo():
    p = pl.armar(H1, 2, "Bajista", "Oro", Estadistica(35, 60, 50, "2025-01-27", "2026-10-08"), VELA)
    assert "bajo 3.990,00" in p["gatillo"] and "sobre 3.997,00" in p["invalidacion"]  # 3970 + 27


def test_activacion_reciente_manda_sobre_el_r1_de_ahora():
    # El precio ya rompio 4.015,00 hace unas velas: el R1 de ahora es la resistencia
    # siguiente, pero el plan informa la ruptura que si ocurrio.
    p = pl.armar(H1, 2, "Alcista", "Oro", None, {**VELA, "close": 4018.0}, activacion=4015.0)
    assert p["estado"].startswith("Activado") and "4.015,00" in p["gatillo"]
    assert p["niveles"]["gatillo"] == 4015.0


def test_activacion_invalidada():
    p = pl.armar(H1, 2, "Alcista", "Oro", None, {**VELA, "close": 4000.0}, activacion=4015.0)
    assert p["estado"].startswith("Invalidado")


def test_sin_activacion_esta_armado():
    assert pl.armar(H1, 2, "Alcista", "Oro", None, VELA)["estado"].startswith("Armado")


def test_cobre_sin_decimales():
    h1 = {**H1, "r1": 14420.0, "atr_14": 30.0}
    p = pl.armar(h1, 0, "Alcista", "Cobre", None, {**VELA, "close": 14400.0, "hh22": 14450.0, "atr22": 32.0})
    assert "sobre 14420." in p["gatillo"] and "unos 45." in p["recorrido"]


def test_textos_del_plan_pasan_los_candados():
    p = pl.armar(H1, 2, "Alcista", "Oro", CON_VENTAJA, VELA)
    for k in ("gatillo", "invalidacion", "recorrido", "estadistica", "estado"):
        assert es.frases_prohibidas(p[k]) == [] and "—" not in p[k] and "–" not in p[k]
