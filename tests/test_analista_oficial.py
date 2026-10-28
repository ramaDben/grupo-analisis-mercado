"""Pruebas del resolutor de fuentes oficiales por activo (spec 2026-10-28, Task 1)."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import noticia_oficial  # noqa: E402
from analista.oficial import VENTANA_OFICIAL_DIAS, fuente_de, piso  # noqa: E402


def test_ventana_oficial_son_45_dias():
    assert VENTANA_OFICIAL_DIAS == 45


def test_accion_resuelve_por_su_ancla():
    assert fuente_de("#GS") == {
        "organismo": "Goldman Sachs",
        "pagina_prensa": "https://www.goldmansachs.com/investor-relations/",
        "lector": "edgar_8k",
        "cik": "0000886982",
    }


def test_feed_oficial_por_activo_con_sufijo():
    f_wti = fuente_de("WTI.spot")
    assert f_wti is not None
    assert f_wti["lector"] == "feed_oficial"
    assert f_wti["fuente"] == "eia"

    f_usdclp = fuente_de("USDCLP")
    assert f_usdclp is not None
    assert f_usdclp["fuente"] == "fed"


def test_activo_sin_fuente():
    assert fuente_de("BTCUSD") is None
    assert piso("COPPER") is None


def test_piso_trae_organismo_y_enlace_https():
    p = piso("#GS")
    assert p is not None
    assert p["organismo"] == "Goldman Sachs"
    assert p["pagina_prensa"].startswith("https://")


def test_toda_fuente_de_feeds_tiene_pagina_prensa():
    assert len(noticia_oficial.FUENTES) >= 3
    for nombre, datos in noticia_oficial.FUENTES.items():
        assert "pagina_prensa" in datos, f"Falta pagina_prensa en {nombre}"
        assert isinstance(datos["pagina_prensa"], str), f"pagina_prensa no es str en {nombre}"
        assert datos["pagina_prensa"].startswith("https://"), (
            f"pagina_prensa en {nombre} debe empezar con https://: {datos['pagina_prensa']}"
        )
