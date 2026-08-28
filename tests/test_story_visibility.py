"""Tests de visibilidad para Stories GI — verifica que tokens se resuelven correctamente.

Valida que los campos del payload se resuelven en el HTML sin quedar como {{token}}.
Esto es más rápido que OCR en PNGs y detecta el mismo problema: tokens no resueltos.

Ejecución: pytest tests/test_story_visibility.py -v
"""
from pathlib import Path
import re

import pytest


class TestStoryVisibility:
    """Verifica que elementos clave de las Stories se resuelven en HTML."""

    def test_alerta_fecha_resuelve(self):
        """Verifica que fecha_hora se resuelve correctamente en el HTML de alerta."""
        import json
        from scripts.story_render import build_html
        from scripts.story_grafico import enriquecer

        raw_payload = json.loads(
            Path("tests/fixtures/stories/payloads/alerta.json").read_text(encoding="utf-8")
        )
        payload = enriquecer(raw_payload)

        html = build_html(payload, Path("templates/stories/alerta.html"))

        assert "{{fecha_hora}}" not in html, "Token {{fecha_hora}} no se resolvio"
        assert "13 JUL 2026" in html, "Fecha debe aparecer resuelta en el HTML"
        assert "{{precio_actual}}" not in html, "Token {{precio_actual}} no se resolvio"
        assert "2.318,40" in html, "Precio debe aparecer resuelto"

    def test_sin_tokens_huerfanos_alerta(self):
        """Meta-test: verifica que alerta.html no deja tokens sin resolver."""
        import json
        from scripts.story_render import build_html
        from scripts.story_grafico import enriquecer

        raw_payload = json.loads(
            Path("tests/fixtures/stories/payloads/alerta.json").read_text(encoding="utf-8")
        )
        payload = enriquecer(raw_payload)

        html = build_html(payload, Path("templates/stories/alerta.html"))
        tokens_huerfanos = re.findall(r'\{\{\s*[\w_]+\s*\}\}', html)
        assert not tokens_huerfanos, f"alerta.html: tokens sin resolver: {tokens_huerfanos}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
