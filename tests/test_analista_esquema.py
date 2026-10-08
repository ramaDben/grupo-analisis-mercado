"""Contrato de la pieza que agy rellena: solo textos, sin tocar datos ni maqueta."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import esquema as es  # noqa: E402

DATOS = {"precio": "4.110,65", "soporte": "4.098,20", "resistencia": "4.131,00", "fecha_hora": "08/10/2026 09:39"}


def pieza_llena(**editorial) -> dict:
    p = es.nueva_pieza("activo", {"ticker": "XAUUSD"}, DATOS, {"principal": "alerta.png"})
    for campo in es.CAMPOS["activo"]:
        p["editorial"][campo] = "El oro mantiene presión compradora mientras siga sobre 4.110,65."
    p["editorial"].update(editorial)
    return p


def test_pieza_nueva_trae_todos_los_campos_sin_escribir():
    p = es.nueva_pieza("activo", {"ticker": "XAUUSD"}, DATOS, {})
    assert set(p["editorial"]) == set(es.CAMPOS["activo"])
    assert all(v == es.MARCA for v in p["editorial"].values())
    assert es.errores(p)  # sin escribir no pasa


def test_pieza_bien_escrita_pasa():
    assert es.errores(pieza_llena()) == []


def test_campo_sin_escribir():
    errs = es.errores(pieza_llena(titular=es.MARCA))
    assert any("titular" in e and "sin escribir" in e for e in errs)


@pytest.mark.parametrize("texto", ["sube fuerte — ojo", "sube fuerte – ojo"])
def test_guion_largo_o_medio(texto):
    assert es.errores(pieza_llena(lectura=texto))


def test_voseo():
    assert es.errores(pieza_llena(lectura="Si tenés posición, cuidado."))


@pytest.mark.parametrize("texto", ["<b>alza</b>", "ver <img src=x onerror=alert(1)>", "<!-- x -->"])
def test_rechaza_html(texto):
    errs = es.errores(pieza_llena(lectura=texto))
    assert any("HTML" in e for e in errs)


def test_rechaza_cifra_que_no_esta_en_los_datos():
    errs = es.errores(pieza_llena(lectura="El objetivo es 4.200,00."))
    assert any("4.200,00" in e for e in errs)


def test_acepta_cifra_de_los_datos_aunque_cambie_el_formato():
    assert es.errores(pieza_llena(lectura="Sobre 4110,65 sigue arriba.")) == []


def test_acepta_numeros_chicos_sin_decimales():
    assert es.errores(pieza_llena(lectura="Mira las 2 zonas y los 3 escenarios en 15 minutos.")) == []


def test_no_puede_agregar_ni_quitar_campos():
    p = pieza_llena()
    p["editorial"]["extra"] = "hola mundo"
    assert any("extra" in e for e in es.errores(p))
    p = pieza_llena()
    del p["editorial"]["titular"]
    assert any("titular" in e for e in es.errores(p))


def test_no_puede_tocar_los_datos():
    p = pieza_llena()
    p["datos"]["precio"] = "4.200,00"
    assert any("datos" in e for e in es.errores(p))


def test_no_puede_tocar_las_imagenes():
    p = pieza_llena()
    p["imagenes"]["principal"] = "otra.png"
    assert any("datos" in e for e in es.errores(p))


def test_campos_anidados_se_validan_uno_a_uno():
    p = es.nueva_pieza("calendario", {"alcance": "hoy"}, {"eventos": []}, {}, extra_campos={"explicaciones": ["1", "2"]})
    for campo in es.CAMPOS["calendario"]:
        p["editorial"][campo] = "Texto suficientemente largo para pasar."
    p["editorial"]["explicaciones"] = {"1": "Explica el dato uno con calma.", "2": es.MARCA}
    errs = es.errores(p)
    assert len(errs) == 1 and "explicaciones.2" in errs[0]


def test_cada_pieza_tiene_campos():
    assert set(es.CAMPOS) == {"activo", "calendario", "dato", "jornada"}


def test_titular_largo_no_cabe_en_la_lamina():
    errs = es.errores(pieza_llena(titular="El oro " * 15))
    assert any("titular" in e and "máximo" in e for e in errs)


def test_no_puede_tocar_las_laminas():
    p = es.nueva_pieza("calendario", {"alcance": "hoy"}, {"eventos": []}, {},
                       laminas={"calendario.png": {"titular": es.MARCA}})
    for campo in es.CAMPOS["calendario"]:
        p["editorial"][campo] = "Texto suficientemente largo para pasar."
    assert es.errores(p) == []
    p["laminas"]["calendario.png"]["titular"] = "otra cosa"
    assert any("datos" in e for e in es.errores(p))
