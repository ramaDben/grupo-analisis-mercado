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


def test_marcador_actual_se_ancla_al_vertice_de_la_linea():
    """El punto y la guía del marcador 'actual' deben anclarse exactamente al final
    de la línea, que es lo que lo hace leerse como "acá estamos ahora".

    Este test venía con un marcador de precio 15,0 sobre una serie que terminaba en
    12,0, para probar que el punto seguía a la serie **aunque el precio difiriera**.
    La intención geométrica era correcta y se conserva; lo que se quitó es la
    incoherencia de la fixture, porque era exactamente el defecto que el renderer
    tapaba: dibujar en un precio y rotular otro. Ahora eso levanta, y su propio
    test está más abajo.
    """
    import re

    serie = [10.0, 11.0, 12.0]
    marcadores = [{"indice": 2, "precio": 12.0, "clase": "actual", "etiqueta": "12,00"}]
    svg = story_grafico.construir_svg(serie, marcadores)

    # Extraer el último punto de la línea SVG
    match_linea = re.search(r'class="g-linea"\s+d="M\s+([^"]+)"', svg)
    assert match_linea is not None
    puntos = match_linea.group(1).split(" L ")
    ultimo_x, ultimo_y = puntos[-1].split(",")

    # Extraer cx y cy del punto actual
    match_punto = re.search(r'class="g-punto\s+g-punto-actual"\s+cx="([^"]+)"\s+cy="([^"]+)"', svg)
    assert match_punto is not None
    cx, cy = match_punto.group(1), match_punto.group(2)

    assert cx == ultimo_x
    assert cy == ultimo_y


def test_un_marcador_actual_que_no_coincide_con_su_serie_no_se_dibuja():
    """El caso GLD.US del 2026-09-04, en la capa que lo tapaba.

    El punto se dibujaba en 405,32 (su valor en la serie) con el rótulo "410,37"
    (el precio del marcador), sin un solo error: la pieza se veía impecable con dos
    precios distintos adentro. El renderer era el último lugar donde el defecto
    podía notarse y era justo el que lo escondía.
    """
    serie = [400.0 + i * 0.09 for i in range(60)]
    serie[-1] = 405.32
    marcadores = [{"indice": 59, "precio": 410.37, "clase": "actual",
                   "etiqueta": "410,37"}]
    with pytest.raises(story_grafico.GraficoError) as exc:
        story_grafico.construir_svg(serie, marcadores)
    assert "dos precios distintos" in str(exc.value)


def test_un_hito_de_operacion_si_conserva_su_precio_propio():
    """La asimetría es deliberada y no se toca: en un marcador de meta manda el
    hito real de la operación sobre el muestreo del gráfico. El control nuevo
    aplica solo a `actual`, que es el único donde la serie manda sobre el precio."""
    serie = [10.0, 11.0, 12.0]
    marcadores = [{"indice": 2, "precio": 15.0, "clase": "meta", "etiqueta": "15,00"}]
    svg = story_grafico.construir_svg(serie, marcadores)
    assert "g-punto-meta" in svg


def _y_de(svg: str, clase: str) -> list[float]:
    import re

    return [float(y) for y in re.findall(rf'<text class="{clase}[^"]*" x="[^"]+" y="([^"]+)"', svg)]


def test_el_rol_no_tapa_la_cola_de_la_coma_del_precio():
    # Revisión final Hito 1: con el rol a 15 unidades bajo la línea base del
    # precio, su trazo negro tapaba la cola de la coma y "30.524,40" se leía
    # "30.524.40". El precio mide 26 px (coma que baja ~8 con su trazo) y el
    # rol 17 px en mayúsculas (~14 sobre su línea base con trazo): hacen falta
    # al menos 24 unidades entre las dos líneas base.
    niveles = [{"precio": 12.0, "clase": "soporte", "etiqueta": "12,00", "rol": "SOPORTE"}]
    marcadores = [{**MARCADORES[0], "rol": "AHORA"}]
    svg = story_grafico.construir_svg(SERIE, marcadores, niveles)
    precios, roles = _y_de(svg, "g-precio"), _y_de(svg, "g-rol")
    assert len(precios) == len(roles) == 2
    for y_precio, y_rol in zip(precios, roles):
        assert y_rol - y_precio >= 24


def test_bloques_de_etiqueta_cercanos_no_se_pisan():
    # Resistencia, ahora y soporte casi al mismo precio: cada bloque (precio +
    # rol) tiene que empezar debajo del rol del bloque anterior.
    serie = [100.0, 100.2, 100.1, 100.3]
    niveles = [
        {"precio": 100.35, "clase": "resistencia", "etiqueta": "100,35", "rol": "RESISTENCIA"},
        {"precio": 100.25, "clase": "soporte", "etiqueta": "100,25", "rol": "SOPORTE"},
    ]
    marcadores = [{"indice": 3, "precio": 100.3, "clase": "actual", "etiqueta": "100,30", "rol": "AHORA"}]
    svg = story_grafico.construir_svg(serie, marcadores, niveles)
    precios = sorted(_y_de(svg, "g-precio"))
    roles = sorted(_y_de(svg, "g-rol"))
    for rol_anterior, precio_siguiente in zip(roles, precios[1:]):
        # el tope de las cifras del siguiente precio (~20 sobre su base) queda bajo el rol anterior
        assert precio_siguiente - 20 > rol_anterior
