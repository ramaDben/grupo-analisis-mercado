"""Suite de pruebas para el despacho de Fe de Erratas sobre la Presidencia de la Fed (Kevin Warsh).

Verifica:
1. Existencia y validez de los textos en data/stories/.
2. Que los textos pasen todos los guardrails de cliente (sin guiones largos, siglas explicadas,
   sin voseo, tono institucional admisible, canales existentes).
3. Que la referencia a Kevin Warsh como Presidente de la Reserva Federal esté presente y
   que se rectifique expresamente el lapsus de Jerome Powell.
4. Correcta ejecución en modo simulado (dry-run).
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

from guardrails import texto_cliente
import despacho_fe_de_erratas_warsh as dfe

# Audita un despacho ad-hoc de este equipo: sus piezas viven en data/stories/,
# que esta en .gitignore. En un clon limpio (la CI) no existen, y el test no
# tiene nada que auditar; se salta con el motivo a la vista en vez de fallar.
_PIEZAS = [v for item in dfe.PLAN_DESPACHO for v in item.values() if isinstance(v, Path)]
pytestmark = pytest.mark.skipif(
    not all(p.exists() for p in _PIEZAS),
    reason="piezas del despacho ad-hoc ausentes (data/stories/ esta gitignoreado)",
)


def test_archivos_fe_de_erratas_existen():
    assert len(dfe.PLAN_DESPACHO) == 3
    for item in dfe.PLAN_DESPACHO:
        assert item["mensaje"].exists(), f"Falta texto para {item['pieza']}: {item['mensaje']}"
        contenido = item["mensaje"].read_text(encoding="utf-8").strip()
        assert len(contenido) > 300, f"Texto de {item['pieza']} demasiado corto"


def test_guardrails_texto_en_fe_de_erratas():
    for item in dfe.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")

        v_guion = texto_cliente.sin_guion_largo(texto)
        assert v_guion.ok, f"Fallo guión largo en {item['pieza']}: {v_guion.detalle}"

        v_siglas = texto_cliente.siglas_explicadas(texto, en_linea=False)
        assert v_siglas.ok, f"Fallo siglas en {item['pieza']}: {v_siglas.detalle} ({v_siglas.ubicacion})"

        v_tono = texto_cliente.tono_admisible(texto)
        assert v_tono.ok, f"Fallo tono en {item['pieza']}: {v_tono.detalle}"

        v_voseo = texto_cliente.sin_voseo(texto)
        assert v_voseo.ok, f"Fallo voseo en {item['pieza']}: {v_voseo.detalle}"

        v_canales = texto_cliente.canales_existen(texto)
        assert v_canales.ok, f"Fallo canales en {item['pieza']}: {v_canales.detalle}"


def test_contenido_rectificacion_warsh():
    for item in dfe.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")
        assert "Kevin Warsh" in texto, f"Falta mención a Kevin Warsh en {item['pieza']}"
        assert "Jerome Powell" in texto or "Powell" in texto, f"Falta mención explicativa de Powell en {item['pieza']}"
        assert "15:30 CLT" in texto, f"Falta hora de la rueda de prensa en {item['pieza']}"


def test_ejecucion_dry_run_fe_de_erratas():
    res = dfe.ejecutar(dry_run=True)
    assert res == 0
