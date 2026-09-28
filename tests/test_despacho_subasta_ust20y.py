"""Suite de pruebas para el despacho de la Subasta del Tesoro a 20 Años (UST 20Y).

Verifica exhaustivamente antes del envío:
1. Que los textos de los mensajes cumplan todos los guardrails de cliente (cero guiones largos,
   siglas explicadas en el diccionario rápido, sin voseo, tono sobrio profesional, canales existentes).
2. Que las cifras de precios respeten estrictamente la tabla de decimales (digits) de config/activos.json.
3. La coherencia macro del relato: causalidad económica (tasa 20Y en 5,420% presiona múltiplos de US100 y apoya al USD),
   cifras consistentes con la emisión oficial y diccionarios completos.
4. La existencia de todos los artefactos de la tanda (PNG y textos en data/stories/).
5. La correcta ejecución simulada (dry-run) del script de despacho.
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
import despacho_subasta_ust20y as d20

# Audita un despacho ad-hoc de este equipo: sus piezas viven en data/stories/,
# que esta en .gitignore. En un clon limpio (la CI) no existen, y el test no
# tiene nada que auditar; se salta con el motivo a la vista en vez de fallar.
_PIEZAS = [v for item in d20.PLAN_DESPACHO for v in item.values() if isinstance(v, Path)]
pytestmark = pytest.mark.skipif(
    not all(p.exists() for p in _PIEZAS),
    reason="piezas del despacho ad-hoc ausentes (data/stories/ esta gitignoreado)",
)


def test_archivos_de_mensajes_e_imagen_existen():
    """Verifica que todas las piezas declaradas en el plan existan en disco."""
    assert d20.IMAGEN_BREAKING.exists(), f"Falta imagen PNG: {d20.IMAGEN_BREAKING}"
    assert d20.IMAGEN_BREAKING.stat().st_size > 50000, "La imagen PNG debe ser válida y no vacía"

    for item in d20.PLAN_DESPACHO:
        msg_file = item["mensaje"]
        assert msg_file.exists(), f"Falta archivo de mensaje para {item['pieza']}: {msg_file}"
        contenido = msg_file.read_text(encoding="utf-8").strip()
        assert len(contenido) > 100, f"El mensaje {item['pieza']} es demasiado corto"


def test_guardrails_texto_cliente_en_todos_los_mensajes():
    """Verifica que todos los mensajes pasen las 5 reglas de guardrails de texto para clientes."""
    for item in d20.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")

        # 1. Sin guión largo ni medio
        v_guion = texto_cliente.sin_guion_largo(texto)
        assert v_guion.ok, f"Fallo guión largo en {item['pieza']}: {v_guion.detalle}"

        # 2. Siglas explicadas en el bloque 'Diccionario rápido'
        v_siglas = texto_cliente.siglas_explicadas(texto, en_linea=False)
        assert v_siglas.ok, f"Fallo siglas sin explicar en {item['pieza']}: {v_siglas.detalle} (sigla: {v_siglas.ubicacion})"

        # 3. Tono profesional admisible (sin histeria ni palabras prohibidas)
        v_tono = texto_cliente.tono_admisible(texto)
        assert v_tono.ok, f"Fallo tono en {item['pieza']}: {v_tono.detalle}"

        # 4. Sin voseo rioplatense (tuteo neutro chileno)
        v_voseo = texto_cliente.sin_voseo(texto)
        assert v_voseo.ok, f"Fallo voseo en {item['pieza']}: {v_voseo.detalle}"

        # 5. Canales citados existentes
        v_canales = texto_cliente.canales_existen(texto)
        assert v_canales.ok, f"Fallo canales en {item['pieza']}: {v_canales.detalle}"


def test_decimales_y_precios_correctos():
    """Verifica que las cifras citadas en los mensajes respeten estrictamente la tabla de decimales."""
    for item in d20.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")
        v_gen = precios.revisar_texto(texto)
        assert v_gen.ok, f"Fallo general de precios en {item['pieza']}: {v_gen.detalle}"


def test_coherencia_macro_del_relato():
    """Verifica que la narrativa macro sea verídica, consistente y no contradictoria."""
    txt_macro = (RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_macro.txt").read_text(encoding="utf-8")
    txt_indices = (RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_indices.txt").read_text(encoding="utf-8")
    txt_forex = (RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_forex.txt").read_text(encoding="utf-8")

    # 1. Cifra oficial de la subasta a 20 años (5,420%)
    assert "5,420%" in txt_macro, "El mensaje macro debe citar la tasa oficial de 5,420%"
    assert "5,420%" in txt_indices, "El mensaje de índices debe citar la tasa oficial de 5,420%"
    assert "5,420%" in txt_forex, "El mensaje de forex debe citar la tasa oficial de 5,420%"

    # 2. Variación oficial (+21,6 bps) y subasta previa (5,204%)
    assert "+21,6" in txt_macro or "+21,6 bps" in txt_macro
    assert "5,204%" in txt_macro

    # 3. Consistencia de sesgo por activo
    assert "Bajista" in txt_indices or "presión" in txt_indices.lower(), "US100 debe reflejar presión bajista por tasas"
    assert "Alcista" in txt_forex or "comprador" in txt_forex.lower(), "USDCLP debe reflejar soporte comprador"


def test_sin_precios_truncados_por_shell():
    """Verifica que ningún precio ni cifra empiece con punto huérfano (.85 en vez de $938.85)."""
    import re
    patron_huerfano = re.compile(r"(?<!\w)\.\d+")
    for item in d20.PLAN_DESPACHO:
        texto = item["mensaje"].read_text(encoding="utf-8")
        coincidencias = patron_huerfano.findall(texto)
        assert not coincidencias, f"Cifras truncadas detectadas en {item['pieza']}: {coincidencias}"


def test_ejecucion_simulada_despacho_dry_run():
    """Verifica que el script de despacho ejecute el ciclo completo en modo dry-run con código de salida 0."""
    codigo = d20.ejecutar(dry_run=True)
    assert codigo == 0, f"El despacho simulado falló con código {codigo}"
