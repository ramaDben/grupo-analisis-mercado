"""Las instrucciones de agy dicen lo que el validador exige: un test que los ata."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import fuentes as fu  # noqa: E402

TEXTO = (RAIZ / ".claude" / "commands" / "analista.md").read_text(encoding="utf-8")


def test_nombra_cada_campo_de_la_fuente():
    for campo in fu.CAMPOS:
        assert f"`{campo}`" in TEXTO


def test_permite_la_web_solo_para_las_fuentes():
    assert "búsqueda web" in TEXTO.lower() or "busca en la web" in TEXTO.lower()
    assert "no uses la web" not in TEXTO.lower()


def test_ya_no_manda_invitar_a_operar_y_lo_prohibe():
    bajo = TEXTO.lower()
    assert "invita a operar el escenario" not in bajo
    assert "nunca invites a operar" in bajo


def test_pide_revisar_la_plataforma_y_no_pone_cifras_de_bancos_sin_atribucion():
    assert "revisar" in TEXTO.lower() and "atribu" in TEXTO.lower()


def test_enumera_las_entidades_de_la_lista_cerrada():
    lista = fu.cargar_lista()
    assert all(e in TEXTO for e in ("Goldman Sachs", "Banco Central de Chile", "Fed"))
    assert len(lista["medios"]) > 10  # la lista real vive en config/fuentes_prestigio.json
