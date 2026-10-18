"""La guía «qué conversar / qué no decir» que lee el ejecutivo: completa y sin lenguaje de asesoría."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parent.parent / "config" / "guia_eventos.json"
TIPOS = ("tasas", "inflacion", "empleo", "actividad", "petroleo")
CAMPOS = ("mueve", "conversar", "no_decir", "titular")
PROHIBIDAS = re.compile(r"\b(compra\w*|vende\w*|oportunidad\w*|cobertura\w*)\b", re.IGNORECASE)


def guia():
    datos = json.loads(RUTA.read_text(encoding="utf-8"))
    return {k: v for k, v in datos.items() if not k.startswith("_")}  # `_nota`, como en el glosario


def textos(tipo):
    g = guia()[tipo]
    return [g["conversar"], g["no_decir"], g["titular"]]


def test_la_guia_tiene_los_cinco_tipos():
    assert set(guia()) == set(TIPOS)


@pytest.mark.parametrize("tipo", TIPOS)
def test_cada_tipo_tiene_los_cuatro_campos(tipo):
    g = guia()[tipo]
    for campo in CAMPOS:
        assert g.get(campo), f"{tipo}: falta {campo}"
    assert isinstance(g["mueve"], list) and all(isinstance(a, str) and a for a in g["mueve"])


@pytest.mark.parametrize("tipo", TIPOS)
def test_sin_guion_largo(tipo):
    for t in textos(tipo):
        assert "—" not in t and "–" not in t, t


@pytest.mark.parametrize("tipo", TIPOS)
def test_sin_palabras_de_asesoria(tipo):
    for t in textos(tipo):
        assert not PROHIBIDAS.search(t), f"{tipo}: «{PROHIBIDAS.search(t).group(0)}» en: {t}"


@pytest.mark.parametrize("tipo", TIPOS)
def test_el_titular_abre_con_semana_de(tipo):
    assert guia()[tipo]["titular"].startswith("Semana de ")
