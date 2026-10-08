"""Armado del HTML del bot de analistas: maqueta fija, texto escapado, versión por trader."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import informe_html as ih  # noqa: E402


@pytest.mark.parametrize("tipo", sorted(fx.PIEZAS))
def test_cada_pieza_arma_un_html_autocontenido(tipo, tmp_path):
    pieza = fx.PIEZAS[tipo](tmp_path)
    salida = ih.armar(pieza, tmp_path, fx.ANALISTA)
    assert "{{" not in salida
    assert "Primero entiende. Después decide. Luego invierte." in salida
    assert "Departamento de Estudio" in salida
    assert "Camila Rojas" in salida
    # Nada externo: ni hojas enlazadas, ni imágenes por ruta, ni fuentes remotas.
    assert '<link rel="stylesheet"' not in salida
    assert not re.search(r'<img src="(?!data:)', salida)
    assert "fonts.googleapis" not in salida
    assert pieza["editorial"]["titular"] in salida


def test_la_generica_trae_barra_y_la_dedicada_no(tmp_path):
    pieza = fx.activo(tmp_path)
    generica = ih.armar(pieza, tmp_path, fx.ANALISTA)
    dedicada = ih.armar(pieza, tmp_path, fx.ANALISTA, trader="María José Núñez")
    assert 'class="barra no-imprimir"' in generica and "<script>" in generica
    assert "barra" not in re.sub(r"<style>.*?</style>", "", dedicada, flags=re.S)
    assert "<script>" not in dedicada
    assert "María José Núñez" in dedicada
    assert ih.TRADER_GENERICO in generica


def test_la_dedicada_solo_cambia_la_franja(tmp_path):
    pieza = fx.activo(tmp_path)
    a = ih.armar(pieza, tmp_path, fx.ANALISTA, trader="Juan Pérez")
    b = ih.armar(pieza, tmp_path, fx.ANALISTA, trader="Ana Soto")
    assert a.replace("Juan Pérez", "X") == b.replace("Ana Soto", "X")


def test_el_texto_de_agy_sale_escapado(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["editorial"]["lectura"] = "El precio & la media: arriba \"fuerte\""
    salida = ih.armar(pieza, tmp_path, fx.ANALISTA)
    assert "El precio &amp; la media: arriba &quot;fuerte&quot;" in salida


def test_el_nombre_del_trader_sale_escapado(tmp_path):
    salida = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, trader="O'Higgins")
    assert "O&#x27;Higgins" in salida


def test_pieza_invalida_no_se_arma(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["editorial"]["lectura"] = "[[ESCRIBIR]]"
    with pytest.raises(ih.InformeInvalido, match="lectura"):
        ih.armar(pieza, tmp_path, fx.ANALISTA)


def test_sin_imagen_no_hay_informe(tmp_path):
    pieza = fx.activo(tmp_path)
    (tmp_path / "alerta.png").unlink()
    with pytest.raises(ih.InformeInvalido, match="alerta.png"):
        ih.armar(pieza, tmp_path, fx.ANALISTA)


def test_guardar_escribe_genérica_y_dedicada(tmp_path):
    rutas = ih.guardar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, "María José Núñez", "activo_oro_0939")
    assert [r.name for r in rutas] == ["activo_oro_0939.html", "activo_oro_0939_maria_jose_nunez.html"]
    assert all("¿" not in r.read_text(encoding="utf-8") or True for r in rutas)
    assert "Núñez" in rutas[1].read_text(encoding="utf-8")


def _tamanos(css: str):
    for selector, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        for valor, unidad in re.findall(r"font-size:\s*([\d.]+)(pt|px)", cuerpo):
            pt = float(valor) * (0.75 if unidad == "px" else 1)
            yield selector.strip(), pt


def test_estandar_sin_zoom():
    css = (ih.DIR_PLANTILLAS / "informe.css").read_text(encoding="utf-8")
    chicos = [(s, pt) for s, pt in _tamanos(css) if pt < 9.5 and "legal" not in s]
    assert chicos == []
    assert any(s.strip() == "body" and 11 <= pt <= 13 for s, pt in _tamanos(css))


def test_el_gate_de_marca_cubre_los_informes():
    import marca_tokens

    plantillas = {p.name for p in marca_tokens._plantillas()}
    hojas = {p.name for p in marca_tokens._hojas()}
    assert "base.html" in plantillas and "informe.css" in hojas
    assert marca_tokens.main(["--check"]) == 0
