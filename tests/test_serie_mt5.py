"""Tests del puente serie MT5 -> bloque `recorrido` (`scripts/serie_mt5.py`).

Cubren `construir_recorrido` y `_indice_hito`, que son lógica pura: no tocan el
terminal MT5 (el import de `mt5_client` vive dentro de `obtener_serie`, así que
el módulo se importa sin MetaTrader5 instalado). El módulo vive en `scripts/`
igual que `story_render.py`, así que se inserta `scripts/` en `sys.path` acá
mismo y no se toca `conftest.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import serie_mt5  # noqa: E402 (import tras el ajuste de sys.path)

SERIE = [500.0, 505.0, 490.0, 512.3]


def test_etiqueta_del_hito_se_propaga_al_marcador():
    """La etiqueta formateada sobrevive al viaje hito -> marcador.

    Es el campo que respeta los `digits` del activo (`512,30`, no `512.3`). Si se
    descarta, `story_grafico.py` cae a `str(precio)` y el gráfico publica el
    precio crudo de MT5, saltándose la regla de formato de precios del proyecto.
    """
    recorrido = serie_mt5.construir_recorrido(
        SERIE,
        [{"precio": 512.3, "clase": "actual", "etiqueta": "512,30", "rol": "AHORA"}],
    )

    assert recorrido["marcadores"][0]["etiqueta"] == "512,30"


def test_hito_sin_etiqueta_no_inventa_la_clave():
    """Sin etiqueta, la clave no viaja: `story_grafico.py` aplica su propio default.

    Que la clave falte y que llegue vacía no son lo mismo — una cadena vacía
    borraría el precio del gráfico en lugar de caer al valor crudo.
    """
    recorrido = serie_mt5.construir_recorrido(SERIE, [{"precio": 512.3, "clase": "actual"}])

    assert "etiqueta" not in recorrido["marcadores"][0]


def test_marcador_actual_se_ancla_a_la_ultima_vela():
    """"Ahora" es el extremo derecho por definición, no el cierre más parecido.

    El precio 505,0 aparece en el índice 1, así que un anclaje por proximidad de
    precio pondría el marcador en medio de la serie.
    """
    recorrido = serie_mt5.construir_recorrido(SERIE, [{"precio": 505.0, "clase": "actual"}])

    assert recorrido["marcadores"][0]["indice"] == len(SERIE) - 1


def test_hito_de_origen_sin_fecha_cae_a_proximidad_de_precio():
    """Un nivel que efectivamente se tocó puede anclarse por precio."""
    recorrido = serie_mt5.construir_recorrido(SERIE, [{"precio": 489.5, "clase": "origen"}])

    assert recorrido["marcadores"][0]["indice"] == 2
