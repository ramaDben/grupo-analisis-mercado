"""Tests para el guardrail de autoridades vigentes."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from scripts.guardrails.autoridades import autoridad_vigente
from scripts.guardrails.motivos import MOTIVOS

def test_aprueba_texto_sin_autoridades():
    v = autoridad_vigente("Las tasas se mantuvieron estables tras la reunion.")
    assert v.ok

def test_aprueba_texto_con_autoridad_vigente():
    v1 = autoridad_vigente("Kevin Warsh anunció un recorte de tasas en Jackson Hole.")
    assert v1.ok
    v2 = autoridad_vigente("Lagarde subió las tasas del BCE por el IPC.")
    assert v2.ok

def test_falla_texto_con_autoridad_obsoleta_powell():
    v = autoridad_vigente("Jerome Powell dijo que la inflación está bajando rápidamente.")
    assert not v.ok
    assert v.motivo == "autoridad_obsoleta"
    assert "vigente" in v.detalle
    assert "Kevin Warsh" in v.detalle
    assert v.ubicacion == "Jerome Powell"

def test_falla_solo_con_apellido_obsoleto():
    v = autoridad_vigente("Se esperan palabras de Powell hoy en la tarde.")
    assert not v.ok
    assert v.motivo == "autoridad_obsoleta"
    assert v.ubicacion == "Powell"

def test_motivo_existe_en_catalogo():
    assert "autoridad_obsoleta" in MOTIVOS
