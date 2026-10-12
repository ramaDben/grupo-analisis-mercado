"""Guardias del gráfico del informe: formato, rutas de imagen y qué se traza.

Se eligieron porque fallan en silencio. (Hasta el 2026-10-12 también se verificaba
la EMA calculada a mano; el banner ya no dibuja medias y la función se borró.)

**Los decimales.** La regla del proyecto los toma del catálogo. Un WTI escrito a
2 decimales en vez de 3 no se ve mal: se ve normal, y es otro precio.

**Las rutas de imagen.** El HTML del informe se renderiza en `scratch/` y no
donde vive el markdown, así que una ruta relativa apunta a un archivo que no
está. El navegador no considera eso un error, dibuja el hueco y sigue: el PDF
sale sin gráficos y nada lo avisa. Es el mismo fallo que ya tuvo `marca.css`.

Ninguno de estos tests necesita MT5 ni matplotlib: verifican la lógica que
rodea al dibujo, que es la parte que se puede romper sin que se note.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for sub in ("scripts", "src", ".agents/skills/generar-reporte-editorial/scripts"):
    ruta = str(RAIZ / sub)
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import grafico_informe as gi  # noqa: E402


# ── Los decimales ────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "valor, digits, esperado",
    [
        (889.6, 2, "889,60"),        # el cero final no se trunca
        (4539.72, 2, "4.539,72"),    # miles con punto, decimales con coma
        (90.18, 3, "90,180"),        # WTI va a 3 aunque el float traiga 2
        # `digits 0` es solo el Cobre, y CLAUDE.md lo lista entero
        # (`$14197 USD/t`) marcando `$14.197` como incorrecto: el punto se
        # confunde con el decimal ingles, y el mismo metal cotiza tambien en
        # USD/libra con 4 decimales (6,602). Sin separador no hay ambiguedad.
        (13720, 0, "13720"),
        (14386, 0, "14386"),
        (163.7315, 3, "163,732"),    # redondeo, no truncado
    ],
)
def test_formatear_precio_respeta_el_catalogo(valor, digits, esperado):
    assert gi.formatear_precio(valor, digits) == esperado


# ── El lienzo ────────────────────────────────────────────────────────────────
def test_tema_desconocido_se_rechaza_antes_de_dibujar():
    """Falla temprano y nombra las opciones, en vez de rendir con la paleta equivocada."""
    with pytest.raises(gi.GraficoError, match="Tema"):
        gi.construir_grafico("XAUUSD", "Oro", Path("no_se_escribe.png"), tema="neon")


def test_los_dos_temas_declaran_los_mismos_roles():
    """Un rol que falte en un tema es un KeyError recién al renderizar ese tema."""
    claro, oscuro = gi.TEMAS["claro"], gi.TEMAS["oscuro"]
    assert set(claro) == set(oscuro)


def test_el_subtitulo_largo_se_envuelve_y_no_se_corta():
    """El caso real: el sesgo del Nasdaq medía 88 caracteres y salía cortado."""
    import textwrap

    largo = (
        "Hoy lo vemos con más probabilidad de subir, acompañado por el buen "
        "momento de la economía"
    )
    lineas = textwrap.wrap(largo, width=gi.ANCHO_SUBTITULO, max_lines=2, placeholder="…")
    assert 1 < len(lineas) <= 2
    assert all(len(l) <= gi.ANCHO_SUBTITULO for l in lineas)
    # Nada se pierde: envolver reparte, no recorta.
    assert " ".join(lineas) == largo


# ── Las rutas de imagen del PDF ──────────────────────────────────────────────
def _absolutizar():
    pytest.importorskip("markdown")
    pytest.importorskip("playwright")
    pytest.importorskip("pypdf")
    import generar_pdf

    return generar_pdf._absolutizar_imagenes


def test_ruta_relativa_existente_se_resuelve_contra_el_markdown(tmp_path):
    (tmp_path / "graficos").mkdir()
    (tmp_path / "graficos" / "oro.png").write_bytes(b"\x89PNG")
    salida = _absolutizar()('<img alt="o" src="graficos/oro.png">', tmp_path)
    assert salida.startswith('<img alt="o" src="file:///')
    assert salida.rstrip('">').endswith("graficos/oro.png")


@pytest.mark.parametrize(
    "src",
    ["https://ejemplo.cl/a.png", "data:image/png;base64,AAAA", "file:///C:/x.png"],
)
def test_las_rutas_que_ya_resuelven_no_se_tocan(src, tmp_path):
    html = f'<img src="{src}">'
    assert _absolutizar()(html, tmp_path) == html


def test_una_ruta_rota_se_deja_rota(tmp_path):
    """A propósito: convertirla en absoluta la deja igual de rota, pero esconde
    el hueco de la revisión visual, que es donde se detecta."""
    html = '<img src="graficos/no_existe.png">'
    assert _absolutizar()(html, tmp_path) == html


def test_con_la_lectura_se_trazan_sus_niveles():
    """Enchufe, fase 3: el banner traza lo que nombra el texto (la lectura)."""
    lineas = gi.lineas_de_nivel(
        [(925.0, "Nivel a vigilar", "nivel"), (910.0, "Invalida la lectura", "soporte")])
    rotulos = [r for _, _, _, r in lineas]
    assert rotulos == ["Nivel a vigilar", "Invalida la lectura"]


def test_sin_lectura_no_hay_horizontales():
    """Director 2026-10-12: sin lectura no caen los pivotes crudos (R1, S1, Fibo)."""
    assert gi.lineas_de_nivel(None) == []


def test_el_banner_ya_no_sabe_dibujar_medias():
    import inspect

    assert "medias" not in inspect.signature(gi.construir_grafico).parameters
    assert not hasattr(gi, "_ema") and not hasattr(gi, "EMA_LARGA")
