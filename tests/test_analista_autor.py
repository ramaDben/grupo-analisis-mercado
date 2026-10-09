"""Quién firma el informe del bot: el director, con su acreditación vigente."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import autor as au  # noqa: E402

BASE = {"autor": {
    "nombre": "Benjamín Ignacio Bravo Soza", "cargo": "Director de Análisis Técnico",
    "foto": "config/autor/foto.png", "firma": None,
    "acreditacion": {"entidad": "CMV", "categoria": "Operadores", "numero": "A-32915",
                     "vigente_hasta": "2028-03-31",
                     "url": "https://cmvsystem.cmvchile.cl/certificados/635409A1A002"},
}}


def test_sin_autor_no_arranca(tmp_path):
    with pytest.raises(au.AutorInvalido):
        au.cargar({}, tmp_path)


def test_sin_cargo_no_arranca(tmp_path):
    with pytest.raises(au.AutorInvalido):
        au.cargar({"autor": {"nombre": "X"}}, tmp_path)


def test_vigencia_hasta_el_ultimo_dia_inclusive(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert au.vigente(a, date(2028, 3, 31)) and not au.vigente(a, date(2028, 4, 1))


def test_foto_declarada_y_ausente_avisa(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert a.foto is None
    assert any("foto" in x for x in au.avisos(a, date(2026, 10, 8)))


def test_foto_presente_se_usa(tmp_path):
    (tmp_path / "config" / "autor").mkdir(parents=True)
    (tmp_path / "config" / "autor" / "foto.png").write_bytes(b"x")
    a = au.cargar(BASE, tmp_path)
    assert a.foto == tmp_path / "config" / "autor" / "foto.png"
    assert au.avisos(a, date(2026, 10, 8)) == []


def test_vencida_avisa(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert any("venció" in x for x in au.avisos(a, date(2028, 4, 1)))
