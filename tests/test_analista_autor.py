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
    "nombre": "Benjamín Ignacio Bravo Soza", "cargo": "Dirección de Análisis Técnico",
    "foto": "config/autor/foto.png", "firma": None,
    "acreditacion": {"entidad": "CMV", "categoria": "Operadores", "numero": "A-32915",
                     "vigente_hasta": "2028-03-31"},
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


@pytest.mark.parametrize("falta", ["entidad", "categoria", "numero", "vigente_hasta"])
def test_acreditacion_incompleta_no_arranca(tmp_path, falta):
    ac = {k: v for k, v in BASE["autor"]["acreditacion"].items() if k != falta}
    with pytest.raises(au.AutorInvalido, match=falta):
        au.cargar({"autor": {**BASE["autor"], "acreditacion": ac}}, tmp_path)


def test_acreditacion_sin_enlace_carga(tmp_path):
    # El enlace de la CMV no reconoce el certificado: la acreditación va sin él.
    a = au.cargar(BASE, tmp_path)
    assert "url" not in a.acreditacion and au.vigente(a, date(2026, 10, 8))


def test_fecha_mal_escrita_no_arranca(tmp_path):
    ac = {**BASE["autor"]["acreditacion"], "vigente_hasta": "31-03-2028"}
    with pytest.raises(au.AutorInvalido, match="vigente_hasta"):
        au.cargar({"autor": {**BASE["autor"], "acreditacion": ac}}, tmp_path)


def test_el_informe_no_nombra_a_la_cmf(tmp_path):
    ac = {**BASE["autor"]["acreditacion"], "entidad": "CMF"}
    with pytest.raises(au.AutorInvalido, match="CMF"):
        au.cargar({"autor": {**BASE["autor"], "acreditacion": ac}}, tmp_path)
