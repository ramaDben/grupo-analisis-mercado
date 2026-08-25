"""Tests de visibilidad para Stories GI — verifica que tokens se resuelven correctamente.

Valida que los campos del payload se resuelven en el HTML sin quedar como {{token}}.
Esto es más rápido que OCR en PNGs y detecta el mismo problema: tokens no resueltos.

Ejecución: pytest tests/test_story_visibility.py -v
"""
from pathlib import Path

import pytest


class TestStoryVisibility:
    """Verifica que elementos clave de las Stories se resuelven en HTML."""

    def test_oportunidad_fecha_resuelve(self):
        """Verifica que fecha_hora se resuelve correctamente en el HTML."""
        from scripts.story_render import build_html

        payload = {
            "sello": "MOTOR GI ANALISIS EN VIVO",
            "fecha_hora": "2026-08-12 10:06 CLT",
            "activo_nombre": "Dolar Peso",
            "activo_ticker": "USDCLP",
            "activo_slug": "usdclp",
            "activo_imagen": "assets/activos/usdclp.jpg",
            "modo_imagen": "foto-activo",
            "sesgo": "Bajista",
            "sesgo_slug": "bajista",
            "direccion_etiqueta": "BAJANDO",
            "titular": "El dolar busca los 902,65",
            "razon": "IPC de EE.UU. bajando.",
            "precio": "909,80",
            "objetivo": "902,65",
            "objetivo_rotulo": "Objetivo",
            "nota_nivel": "Romper 907,70",
            "dato_rotulo": "IPC EE.UU.",
            "dato_lectura": "Inflacion anual",
            "dato_detalle": "En linea con consenso",
            "dato_veredicto": "En linea",
            "dato_veredicto_slug": "en-linea",
            "cta": "Operar ahora",
            "cta_sub": "Accede con Grupo Inteligencia",
            "grafico": "<svg></svg>",
        }

        html = build_html(payload, Path("templates/stories/oportunidad.html"))

        # Validar que tokens criticos se resolvieron (no quedaron como {{token}})
        assert "{{fecha_hora}}" not in html, \
            "Token {{fecha_hora}} no se resolvio"
        assert "2026-08-12" in html, \
            "Fecha debe aparecer resuelta en el HTML"
        assert "{{precio}}" not in html, \
            "Token {{precio}} no se resolvio"
        assert "909,80" in html, \
            "Precio debe aparecer resuelto"
        assert "{{activo_nombre}}" not in html, \
            "Token {{activo_nombre}} no se resolvio"

    def test_oportunidad_precio_resuelve(self):
        """Verifica que precio se resuelve correctamente."""
        from scripts.story_render import build_html

        payload = {
            "sello": "MOTOR GI ANALISIS EN VIVO",
            "fecha_hora": "2026-08-12 10:06 CLT",
            "activo_nombre": "Dolar Peso",
            "activo_ticker": "USDCLP",
            "activo_slug": "usdclp",
            "activo_imagen": "assets/activos/usdclp.jpg",
            "modo_imagen": "foto-activo",
            "sesgo": "Bajista",
            "sesgo_slug": "bajista",
            "direccion_etiqueta": "BAJANDO",
            "titular": "El dolar busca los 902,65",
            "razon": "IPC de EE.UU. bajando.",
            "precio": "909,80",
            "objetivo": "902,65",
            "objetivo_rotulo": "Objetivo",
            "nota_nivel": "Romper 907,70",
            "dato_rotulo": "IPC EE.UU.",
            "dato_lectura": "Inflacion anual",
            "dato_detalle": "En linea con consenso",
            "dato_veredicto": "En linea",
            "dato_veredicto_slug": "en-linea",
            "cta": "Operar ahora",
            "cta_sub": "Accede con Grupo Inteligencia",
            "grafico": "<svg></svg>",
        }

        html = build_html(payload, Path("templates/stories/oportunidad.html"))

        # Validar que precio y objetivo se resolvieron
        assert "{{precio}}" not in html, \
            "Token {{precio}} no se resolvio"
        assert "909,80" in html, \
            "Precio debe aparecer resuelto"
        assert "{{objetivo}}" not in html, \
            "Token {{objetivo}} no se resolvio"
        assert "902,65" in html, \
            "Objetivo debe aparecer resuelto"

    def test_sin_tokens_huerfanos(self):
        """Meta-test: verifica que ninguna plantilla deja tokens sin resolver."""
        from scripts.story_render import build_html
        import re

        plantillas_test = [
            ("oportunidad.html", {
                "sello": "TEST",
                "fecha_hora": "2026-08-12 10:00 CLT",
                "activo_nombre": "Test",
                "activo_ticker": "TEST",
                "activo_slug": "test",
                "sesgo": "Bajista",
                "sesgo_slug": "bajista",
                "direccion_etiqueta": "TEST",
                "titular": "Test",
                "razon": "Test",
                "precio": "100,00",
                "objetivo": "95,00",
                "objetivo_rotulo": "Test",
                "nota_nivel": "Test",
                "dato_rotulo": "Test",
                "dato_lectura": "Test",
                "dato_detalle": "Test",
                "dato_veredicto": "Test",
                "dato_veredicto_slug": "test",
                "cta": "Test",
                "cta_sub": "Test",
                # Ruta real y no "test.jpg": la plantilla es de producción, así que
                # build_html verifica que el asset exista (un src roto deja el ícono
                # de imagen rota en la pieza).
                "activo_imagen": "assets/activos/oro.jpg",
                "modo_imagen": "foto-activo",
                "grafico": "<svg></svg>",
            }),
        ]

        for plantilla_nombre, payload in plantillas_test:
            html = build_html(payload, Path(f"templates/stories/{plantilla_nombre}"))

            # Buscar tokens sin resolver
            tokens_huerfanos = re.findall(r'{{[\w_]+}}', html)
            assert not tokens_huerfanos, \
                f"{plantilla_nombre}: tokens sin resolver: {tokens_huerfanos}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
