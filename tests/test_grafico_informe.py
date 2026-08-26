"""Guardias del gráfico del informe: aritmética, formato y rutas de imagen.

Tres cosas se verifican acá, y las tres se eligieron porque fallan en silencio.

**La media.** Se calcula a mano en vez de con pandas para no arrastrar la
dependencia al script. Una EMA mal implementada no lanza ninguna excepción:
dibuja una curva de aspecto razonable con la pendiente equivocada, y el cliente
lee la señal al revés. El test la contrasta contra `ewm(adjust=False)`, que es
la definición de referencia.

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


# ── La media ─────────────────────────────────────────────────────────────────
def test_ema_coincide_con_la_definicion_de_referencia():
    pd = pytest.importorskip("pandas")
    serie = [10.0, 11.0, 10.5, 12.0, 13.5, 13.0, 12.5, 14.0, 15.0, 14.5]
    esperado = pd.Series(serie).ewm(span=5, adjust=False).mean().tolist()
    obtenido = gi._ema(serie, 5)
    assert len(obtenido) == len(serie)
    for a, b in zip(obtenido, esperado):
        assert a == pytest.approx(b, rel=1e-12)


def test_ema_de_una_serie_plana_es_la_misma_constante():
    """Sin esto, un error de signo en el recurrente pasa desapercibido."""
    assert gi._ema([7.0] * 30, 10) == pytest.approx([7.0] * 30)


# ── Los decimales ────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "valor, digits, esperado",
    [
        (889.6, 2, "889,60"),        # el cero final no se trunca
        (4539.72, 2, "4.539,72"),    # miles con punto, decimales con coma
        (90.18, 3, "90,180"),        # WTI va a 3 aunque el float traiga 2
        (13720, 0, "13.720"),        # digits 0: sin parte decimal
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


# ── El mapeo Playbook → broker ───────────────────────────────────────────────
def test_todo_simbolo_del_playbook_declara_su_ticker():
    """Una ficha sin entrada acá deja al informe y al escáner buscando un símbolo
    que MT5 no conoce, sin que ninguno de los dos se entere."""
    from market_data_mcp.bias_reader import TICKER_MT5, VALID_SYMBOLS

    assert set(TICKER_MT5) == VALID_SYMBOLS - {"ALL"}


def test_brent_declara_explicitamente_que_no_tiene_ticker():
    """El broker no ofrece Brent. Es un hecho del catálogo, no un olvido."""
    from market_data_mcp.bias_reader import TICKER_MT5

    assert TICKER_MT5["BRENT"] is None


def test_los_tickers_declarados_existen_en_el_catalogo():
    from market_data_mcp.bias_reader import TICKER_MT5
    from market_data_mcp.catalog import VALID_TICKERS

    for simbolo, ticker in TICKER_MT5.items():
        if ticker is not None:
            assert ticker in VALID_TICKERS, f"{simbolo} apunta a {ticker}, ausente del catálogo"


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
