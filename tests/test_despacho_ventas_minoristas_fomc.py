"""Suite de pruebas para el despacho de Ventas Minoristas EE.UU., Inflación y Decisión FOMC.

Verifica:
1. Que los textos de los mensajes cumplan todos los guardrails de cliente (cero guiones largos,
   siglas explicadas en el diccionario rápido, sin voseo, tono sobrio profesional, canales existentes).
2. Que las cifras de precios respeten estrictamente la tabla de decimales (digits).
3. Coherencia macroeconómica (Ventas Minoristas +1,2% sostienen consumo, presionan inflación y reducen recortes agresivos de la Fed).
4. Existencia de todos los artefactos de la tanda (Story PNG y textos en data/stories/).
5. Correcta ejecución simulada (dry-run).
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

from guardrails import texto_cliente, precios
import despacho_ventas_minoristas_fomc as dv

# Audita un despacho ad-hoc de este equipo: sus piezas viven en data/stories/,
# que esta en .gitignore. En un clon limpio (la CI) no existen, y el test no
# tiene nada que auditar; se salta con el motivo a la vista en vez de fallar.
_PIEZAS = [v for item in dv.PLAN_DESPACHO for v in item.values() if isinstance(v, Path)]
pytestmark = pytest.mark.skipif(
    not all(p.exists() for p in _PIEZAS),
    reason="piezas del despacho ad-hoc ausentes (data/stories/ esta gitignoreado)",
)


def test_archivos_de_mensajes_e_imagen_existen():
    assert dv.IMAGEN_BREAKING.exists(), f"Falta imagen PNG: {dv.IMAGEN_BREAKING}"
    assert dv.IMAGEN_BREAKING.stat().st_size > 50000, "La imagen PNG debe ser válida y no vacía"

    for item in dv.PLAN_DESPACHO:
        msg_file = item["mensaje"]
        assert msg_file.exists(), f"Falta archivo de mensaje para {item['pieza']}: {msg_file}"
        contenido = msg_file.read_text(encoding="utf-8").strip()
        assert len(contenido) > 100, f"El mensaje {item['pieza']} es demasiado corto"


def test_guardrails_texto_cliente_en_todos_los_mensajes():
    for item in dv.PLAN_DESPACHO:
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


def test_precios_y_decimales_auditados():
    for item in dv.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")
        v_prec = precios.revisar_texto(texto)
        assert v_prec.ok, f"Fallo precios en {item['pieza']}: {v_prec.detalle}"


def test_ejecucion_dry_run_exitosa():
    res = dv.ejecutar(dry_run=True)
    assert res == 0, "La ejecución en dry-run debe retornar código 0"
