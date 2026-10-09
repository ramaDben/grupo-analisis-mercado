"""Armado del HTML del bot de analistas: maqueta fija, texto escapado, un solo informe general."""
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


def test_informe_general_sin_personalizacion(tmp_path):
    salida = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA)
    for prohibido in ("Preparado para", "Asesor asignado", "in-trader", "btn-guardar", "<script>"):
        assert prohibido not in salida
    assert "Compartido por" in salida and "Análisis" in salida
    assert 'class="barra no-imprimir"' in salida and "window.print()" in salida


def test_contrato_sin_personalizacion_en_paquete_y_plantilla():
    fuentes = [*(RAIZ / "scripts" / "analista").glob("*.py"),
               RAIZ / "templates" / "informes_analista" / "base.html"]
    for f in fuentes:
        texto = f.read_text(encoding="utf-8")
        # La palabra "trader" sí puede aparecer (la ayuda dice "compártelo con tu
        # trader"); lo prohibido es el mecanismo de personalización.
        for prohibido in (".trader", "trader=", "TRADER_GENERICO", "sanear_trader",
                          "Preparado para", "Asesor asignado"):
            assert prohibido not in texto, f"{f.name}: {prohibido}"


def test_el_texto_de_agy_sale_escapado(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["editorial"]["lectura"] = "El precio & la media: arriba \"fuerte\""
    salida = ih.armar(pieza, tmp_path, fx.ANALISTA)
    assert "El precio &amp; la media: arriba &quot;fuerte&quot;" in salida


def test_el_nombre_del_analista_sale_escapado(tmp_path):
    salida = ih.armar(fx.activo(tmp_path), tmp_path, {**fx.ANALISTA, "nombre": "O'Higgins"})
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


def test_guardar_escribe_un_solo_html(tmp_path):
    ruta = ih.guardar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, "activo_oro_0939")
    assert ruta == tmp_path / "activo_oro_0939.html"
    assert [p.name for p in tmp_path.glob("*.html")] == ["activo_oro_0939.html"]


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
