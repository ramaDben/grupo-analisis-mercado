"""La procedencia solo se apoya en filas verificadas de fuentes.md (spec §4)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import Fundamento, Procedencia  # noqa: E402
from estrategia.procedencia import leer_estados, validar  # noqa: E402

FUENTES = "docs/investigacion/fundamentos/fuentes.md"
BUENO = Fundamento("en lateral no se opera", ("Tori Trades, E6dUU [02:52]",), ("F3 p. 78",),
                   ("F6",), "")
PROC = Procedencia("docs/metodologia-tendencias.md", FUENTES, (BUENO,), ("reversiones bruscas",))


def test_lee_el_estado_de_cada_fila_del_resumen():
    estados = leer_estados(RAIZ / FUENTES)
    assert estados["F3"] == "verificada"
    assert estados["F1"].startswith("verificada vía")
    assert estados["F5"] == "verificada parcial"
    assert estados["F11"] == "no encontrada"


def test_una_procedencia_completa_es_valida():
    assert validar(PROC) == []


def test_una_regla_sin_origen_no_pasa():
    errores = validar(replace(PROC, fundamentos=(replace(BUENO, origen=()),)))
    assert any("sin origen" in e for e in errores)


def test_una_regla_sin_respaldo_no_pasa():
    errores = validar(replace(PROC, fundamentos=(replace(BUENO, canonico=(), empirico=()),)))
    assert any("sin respaldo" in e for e in errores)


def test_sin_evidencia_empirica_tiene_que_confesar_lo_no_probado():
    sin_emp = replace(BUENO, empirico=(), no_probado="")
    errores = validar(replace(PROC, fundamentos=(sin_emp,)))
    assert any("no_probado" in e for e in errores)


def test_una_cita_a_fila_parcial_o_inexistente_no_sirve_de_respaldo():
    parcial = replace(BUENO, empirico=("F5",))
    inexistente = replace(BUENO, canonico=("F99 p. 1",))
    errores = validar(replace(PROC, fundamentos=(parcial, inexistente)))
    assert any("F5" in e and "verificada parcial" in e for e in errores)
    assert any("F99" in e for e in errores)


def test_el_metodo_declara_como_falla():
    assert any("modos_de_falla" in e for e in validar(replace(PROC, modos_de_falla=())))
