"""Contrato de `scripts/story_grafico.py`."""
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import story_grafico  # noqa: E402

SERIE = [10.0, 12.0, 11.0, 14.0]
MARCADORES = [{"indice": 3, "precio": 14.0, "clase": "actual", "etiqueta": "14,00"}]


def test_ajuste_por_defecto_conserva_proporcion():
    svg = story_grafico.construir_svg(SERIE, MARCADORES)

    assert 'preserveAspectRatio="xMidYMid meet"' in svg


def test_ajuste_llenar_estira_al_contenedor():
    svg = story_grafico.construir_svg(SERIE, MARCADORES, ajuste="llenar")

    assert 'preserveAspectRatio="none"' in svg


def test_ajuste_desconocido_falla_con_mensaje_accionable():
    with pytest.raises(story_grafico.GraficoError) as exc:
        story_grafico.construir_svg(SERIE, MARCADORES, ajuste="cover")

    assert "cover" in str(exc.value)
    assert "llenar" in str(exc.value)


def test_enriquecer_propaga_el_ajuste_del_recorrido():
    payload = {
        "recorrido": {"serie": SERIE, "marcadores": MARCADORES, "ajuste": "llenar"}
    }

    resultado = story_grafico.enriquecer(payload)

    assert 'preserveAspectRatio="none"' in resultado["grafico"]
    assert "recorrido" not in resultado
