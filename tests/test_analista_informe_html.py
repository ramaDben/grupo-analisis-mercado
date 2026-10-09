"""Armado del HTML del bot de analistas: maqueta fija, texto escapado, un solo informe general."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import informe_html as ih  # noqa: E402

HOY = date(2026, 10, 8)


@pytest.mark.parametrize("tipo", sorted(fx.PIEZAS))
def test_cada_pieza_arma_un_html_autocontenido(tipo, tmp_path):
    pieza = fx.PIEZAS[tipo](tmp_path)
    salida = ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
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
    salida = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
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


def test_firma_con_acreditacion_vigente(tmp_path):
    html = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
    assert "Benjamín Ignacio Bravo Soza" in html and "Dirección de Análisis Técnico" in html
    assert "Acreditación CMV" in html and "A-32915" in html and "31-03-2028" in html
    # El enlace de la CMV no reconoce el certificado (2026-10-08): no se imprime
    # aunque el config lo traiga, porque un enlace que no verifica desacredita.
    assert "cmvsystem" not in html and "Verificable" not in html
    assert ih.FRASE_GENERAL in html and "CMF" not in html


def test_acreditacion_vencida_no_se_imprime(tmp_path):
    html = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, date(2028, 4, 1))
    assert "A-32915" not in html and ih.FRASE_GENERAL in html


def test_sin_foto_ni_firma_no_deja_hueco(tmp_path):
    html = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
    assert 'class="firma-foto"' not in html and 'class="firma-trazo"' not in html


def test_con_foto_va_incrustada(tmp_path):
    from dataclasses import replace

    foto = tmp_path / "foto.png"
    foto.write_bytes(fx.PNG)
    html = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, replace(fx.AUTOR, foto=foto), HOY)
    assert '<img class="firma-foto" src="data:image/png;base64,' in html


def test_seccion_plan_y_sin_plan():
    con = ih.seccion_plan({"hay_plan": True, "sesgo": "Alcista", "gatillo": "G1", "invalidacion": "I1",
                           "recorrido": "R1", "estadistica": "E1", "estado": "S1"})
    for x in ("Gatillo", "Invalidación", "Qué dice la historia", "G1", "I1", "R1", "E1", "S1"):
        assert x in con
    sin = ih.seccion_plan({"hay_plan": False, "sesgo": "Alcista", "motivo": "M1"})
    assert "M1" in sin and "Gatillo" not in sin


def test_el_informe_de_activo_trae_el_plan(tmp_path):
    html = ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
    assert "Plan de escenarios" in html and fx.PLAN["gatillo"] in html


def test_el_texto_de_agy_sale_escapado(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["editorial"]["lectura"] = "El precio & la media: arriba \"fuerte\""
    salida = ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
    assert "El precio &amp; la media: arriba &quot;fuerte&quot;" in salida


def test_el_nombre_del_analista_sale_escapado(tmp_path):
    salida = ih.armar(fx.activo(tmp_path), tmp_path, {**fx.ANALISTA, "nombre": "O'Higgins"}, fx.AUTOR, HOY)
    assert "O&#x27;Higgins" in salida


def test_pieza_invalida_no_se_arma(tmp_path):
    pieza = fx.activo(tmp_path)
    pieza["editorial"]["lectura"] = "[[ESCRIBIR]]"
    with pytest.raises(ih.InformeInvalido, match="lectura"):
        ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, HOY)


def test_sin_imagen_no_hay_informe(tmp_path):
    pieza = fx.activo(tmp_path)
    (tmp_path / "alerta.png").unlink()
    with pytest.raises(ih.InformeInvalido, match="alerta.png"):
        ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, HOY)


def test_guardar_escribe_un_solo_html(tmp_path):
    ruta = ih.guardar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY, "activo_oro_0939")
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


# ───────────────────────────────────────────────────────────── foco técnico


def _visible(html: str) -> str:
    import re

    sin_estilos = re.sub(r"<(style|script)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", sin_estilos)


def test_foco_trae_transparencia_y_frase_fija_sin_estadistica(tmp_path):
    html = ih.armar(fx.oportunidad(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY)
    texto = _visible(html)
    assert "Elegido por el escáner de Grupo Inteligencia entre 10 activos, el 09-10-2026 a las 10:40" in texto
    assert ih.FRASE_ESCENARIO in texto
    assert "FOCO TÉCNICO DEL DÍA · ORO" in texto
    assert "Qué dice la historia" not in texto
    assert "4.131,00" in texto  # el gatillo sigue estando


def test_foco_no_imprime_oportunidad_ni_porcentajes(tmp_path):
    texto = _visible(ih.armar(fx.oportunidad(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY))
    assert "oportunidad" not in texto.lower()
    assert "%" not in texto


def test_el_activo_conserva_la_estadistica(tmp_path):
    texto = _visible(ih.armar(fx.activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, HOY))
    assert "Qué dice la historia" in texto and ih.FRASE_ESCENARIO not in texto


def test_foco_no_imprime_la_tabla_de_tasas_aunque_los_datos_la_traigan(tmp_path):
    from analista import esquema as es

    base = fx.oportunidad(tmp_path)
    datos = {**base["datos"], "contexto": {"curva_tasas": [["Bono del Tesoro a 2 años", "3,61%", "+2 pb", "+1 pb"]]}}
    p = es.nueva_pieza("oportunidad", {"ticker": "XAUUSD"}, datos, base["imagenes"])
    p["editorial"].update(base["editorial"])
    texto = _visible(ih.armar(p, tmp_path, fx.ANALISTA, fx.AUTOR, HOY))
    assert "%" not in texto and "3,61" not in texto
