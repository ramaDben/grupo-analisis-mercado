"""Pruebas del HTML de mensajes de contexto: render, guardar, tarjetas y boton copiar."""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import mensajes_html as mh  # noqa: E402


def pieza_con_todo() -> dict[str, Any]:
    return {
        "orden": {"pieza": "contexto"},
        "datos": {
            "ticker": "XAUUSD",
            "nombre": "Oro",
            "tecnico": {
                "digits": 2,
                "nivel": 4100.0,
                "objetivo": 4200.0,
                "siguiente": None,
            },
        },
        "editorial": {
            "noticia_1": {
                "medio": "FXStreet",
                "fecha": "2026-10-25",
                "url": "https://www.fxstreet.es/news/oro-al-alza-20261025",
                "titular_original": "El oro sube con fuerza",
                "titular": "El oro sube con fuerza por la demanda global",
                "mensaje": "[[SALUDO]] te comparto esta nota: el oro sube con fuerza. ¿Cómo lo ves?",
            },
            "noticia_2": {
                "medio": "Investing.com",
                "fecha": "2026-10-24",
                "url": "https://es.investing.com/news/commodities-news/oro-rompe-resistencia-123456",
                "titular_original": "Oro supera resistencia clave",
                "titular": "Oro supera resistencia clave tras compras técnicas",
                "mensaje": "[[SALUDO]] mira esta otra noticia: el oro superó su nivel técnico clave. ¿Revisamos?",
            },
            "tecnico": "[[SALUDO]] la lectura técnica del oro se mantiene alcista sobre [[NIVEL]]. ¿Lo revisamos?",
        },
        "motivos": {},
    }


def test_html_trae_tres_tarjetas_con_su_boton_copiar():
    html_str = mh.render(pieza_con_todo())
    tarjetas = re.findall(r'data-tarjeta(?:="[^"]*")?', html_str)
    assert len(tarjetas) == 3
    botones = re.findall(r'<button[^>]*>.*?Copiar.*?</button>', html_str, re.DOTALL | re.IGNORECASE)
    assert len(botones) == 3


def test_html_no_carga_recursos_externos():
    html_str = mh.render(pieza_con_todo())
    assert not re.search(r'src=["\']https?://', html_str, re.IGNORECASE)
    assert not re.search(r'<link[^>]*href=["\']https?://', html_str, re.IGNORECASE)
    assert "@import" not in html_str
    todas_las_urls = re.findall(r'https?://[^\s"\'<>]+', html_str)
    assert len(todas_las_urls) > 0
    enlaces_a = re.findall(r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\']', html_str, re.IGNORECASE)
    assert set(todas_las_urls) == set(enlaces_a)


def test_html_escapa_el_texto():
    p = pieza_con_todo()
    p["editorial"]["tecnico"] = '[[SALUDO]] texto con <script>alert("xss")</script> & "comillas"'
    html_str = mh.render(p)
    assert '<script>alert("xss")</script>' not in html_str
    assert "&lt;script&gt;" in html_str
    assert "&amp;" in html_str
    copias = [html.unescape(m) for m in re.findall(r'data-copiar="([^"]+)"', html_str)]
    assert any('<script>alert("xss")</script> & "comillas"' in c for c in copias)


def test_tarjeta_vacia_muestra_el_motivo_y_no_tiene_boton():
    p = pieza_con_todo()
    p["editorial"]["noticia_2"] = None
    p["motivos"]["noticia_2"] = "Hoy no hay una segunda noticia directa de Oro"
    p["editorial"]["tecnico"] = None
    p["motivos"]["tecnico"] = "El mercado está cerrado"
    html_str = mh.render(p)
    assert "Hoy no hay una segunda noticia directa de Oro" in html_str
    assert "El mercado está cerrado" in html_str
    botones = re.findall(r'<button[^>]*>.*?Copiar.*?</button>', html_str, re.DOTALL | re.IGNORECASE)
    assert len(botones) == 1
    tarjetas = re.findall(r'data-tarjeta(?:="[^"]*")?', html_str)
    assert len(tarjetas) == 3


def test_html_aplica_el_saludo_del_ejecutivo():
    html_str = mh.render(pieza_con_todo(), saludo="Juan")
    assert "Hola Juan," in html_str


def test_guardar_escribe_utf8_con_acentos(tmp_path: Path):
    p = pieza_con_todo()
    p["editorial"]["tecnico"] = "[[SALUDO]] ¿Cómo estás? · Operación con tildes: acción, índice."
    ruta = mh.guardar(p, tmp_path, saludo="Juan")
    assert ruta == tmp_path / "mensajes.html"
    assert ruta.exists()
    contenido = ruta.read_text(encoding="utf-8")
    assert "¿Cómo estás?" in contenido
    assert "·" in contenido
    assert "acción, índice" in contenido


def test_html_sin_guion_largo():
    codigo_modulo = (RAIZ / "scripts" / "analista" / "mensajes_html.py").read_text(encoding="utf-8")
    assert "\u2014" not in codigo_modulo
    assert "\u2013" not in codigo_modulo
    html_str = mh.render(pieza_con_todo())
    assert "\u2014" not in html_str
    assert "\u2013" not in html_str


def test_html_avisa_que_noticia_y_tecnico_pueden_apuntar_a_lados_distintos():
    assert "lados distintos" in mh.render(pieza_con_todo())
