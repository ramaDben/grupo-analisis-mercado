"""Contrato del informe: la regla de frescura, las tablas y el idioma.

Sin red y sin Playwright: se prueban las decisiones (cuándo NO se emite, qué dice
una tabla sin datos, cómo se nombra un indicador), no la maqueta del PDF.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import pipeline_informe as pi  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# La regla de frescura
# ─────────────────────────────────────────────────────────────────────────────
def test_la_apertura_no_se_emite_sin_sesgo_del_playbook(monkeypatch):
    """Un PDF institucional sin régimen ni sesgo se cita después como si fuera de
    hoy. El freno es explícito y nombra el remedio."""
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["sesgo no disponible (STALE_DATA)"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    with pytest.raises(SystemExit) as exc:
        pi.preparar("apertura")
    mensaje = str(exc.value)
    assert "NO se emite" in mensaje
    assert "pipeline_ingesta.py" in mensaje, "el error tiene que nombrar el remedio"
    assert "--con-datos-viejos" in mensaje, "y la salida explicita"


def test_con_datos_viejos_si_emite_pero_estampa_el_aviso(monkeypatch, tmp_path):
    """La decisión de publicar con datos vencidos es del director; que el lector
    lo sepa, no."""
    monkeypatch.setattr(pi, "DIR_TRABAJO", tmp_path)
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["stale"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    res = pi.preparar("apertura", con_datos_viejos=True)
    texto = Path(res["markdown"]).read_text(encoding="utf-8")
    assert "Aviso de frescura" in texto
    assert "sin el sesgo cuantitativo del Motor GI" in texto
    assert "ninguna cifra de este documento debe leerse como lectura del motor" in texto


def test_el_cierre_no_exige_el_playbook_porque_no_lleva_pdf(monkeypatch, tmp_path):
    """El cierre es chat-first por criterio de canal, así que no arrastra la
    exigencia del informe institucional."""
    monkeypatch.setattr(pi, "DIR_TRABAJO", tmp_path)
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["stale"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    res = pi.preparar("cierre")
    assert res["canal"].startswith("chat-first")


def test_rendir_se_niega_si_quedan_secciones_sin_escribir(tmp_path):
    md = tmp_path / "informe_apertura.md"
    md.write_text(f"## 01\n\n{pi.MARCA_EDITORIAL} falta esto\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pi.rendir(tmp_path, "apertura")
    assert pi.MARCA_EDITORIAL in str(exc.value)


def test_el_cierre_escrito_no_produce_pdf(tmp_path):
    """Decisión de canal: un PDF al día, no dos."""
    md = tmp_path / "informe_cierre.md"
    md.write_text("## 01\n\nTexto completo del cierre.\n", encoding="utf-8")
    res = pi.rendir(tmp_path, "cierre")
    assert res["canal"] == "chat-first"
    assert "pdf" not in res


# ─────────────────────────────────────────────────────────────────────────────
# Las tablas: una ausencia declarada, no una tabla vacía
# ─────────────────────────────────────────────────────────────────────────────
def test_la_curva_sin_series_dice_que_no_hay_dato_en_vez_de_quedar_vacia():
    """Una tabla con solo encabezado se lee como "no se movió nada", que es una
    afirmación falsa."""
    salida = pi._tabla_curva({})
    assert "no disponible" in salida
    assert "pipeline_ingesta.py" in salida
    assert "|---|" not in salida


def test_un_delta_nulo_se_muestra_como_sin_dato_y_nunca_como_cero():
    """`null` y `0` son afirmaciones distintas: cero es "no se movió"."""
    curva = {"series": {"DGS10": {
        "nombre": "Tesoro 10 años", "nivel_pct": 4.74,
        "delta_1d_bps": None, "delta_5d_bps": 5.0, "fecha_dato": "2026-08-21",
    }}}
    salida = pi._tabla_curva(curva)
    assert "sin dato" in salida
    assert "+5 puntos base" in salida
    assert "+0 puntos base" not in salida
    assert "bps" not in salida, "bps es taquigrafia de mesa, no va a un cliente"


def test_el_playbook_sin_activos_declara_la_ausencia():
    assert "no disponible" in pi._tabla_playbook({})


# ─────────────────────────────────────────────────────────────────────────────
# Idioma: el informe lo lee un cliente en español
# ─────────────────────────────────────────────────────────────────────────────
def test_los_paises_de_la_fuente_se_traducen():
    eventos = [{"hora_servidor": "2026-08-25 10:00", "pais": "United States",
                "nombre": "X", "impacto": "alto"}]
    assert "EE.UU." in pi._tabla_calendario(eventos)
    assert "United States" not in pi._tabla_calendario(eventos)


def test_el_indicador_usa_el_nombre_en_espanol_y_descarta_el_de_la_fuente():
    """No se traduce a mano: el calendario ya engancha `glosario_siglas.json`.

    El nombre en ingles se descarta y no se arrastra entre parentesis: en un
    informe en espanol es ruido con el que el lector tiene que lidiar antes de
    llegar a la hora y al impacto, que es lo unico que iba a mirar.
    """
    ev = {"nombre": "ADP Employment Change Weekly",
          "diccionario": {"nombre_es": "Empleo privado ADP"}}
    assert pi._nombre_indicador(ev) == "Empleo privado ADP"


def test_el_nombre_conserva_el_periodo_porque_es_lo_que_distingue_dos_filas():
    """Descartar el nombre de la fuente no puede costar la desambiguacion: dos
    lecturas del mismo indicador tienen que poder distinguirse."""
    ev = {"nombre": "CB Consumer Confidence (Aug)",
          "diccionario": {"nombre_es": "Confianza del consumidor (The Conference Board)"}}
    salida = pi._nombre_indicador(ev)
    assert salida == "Confianza del consumidor (The Conference Board) \u00b7 dato de agosto"
    assert salida.count("(") == 1, "un solo parentesis: los anidados son ilegibles"


def test_un_indicador_fuera_del_glosario_conserva_el_nombre_de_la_fuente():
    """Es la senal de que hay una sigla nueva por agregar al JSON, no un error."""
    ev = {"nombre": "Building Permits (Jul)", "glosario_pendiente": True}
    assert pi._nombre_indicador(ev) == "Building Permits (Jul)"


@pytest.mark.parametrize("mes, esperado", [(1, "enero"), (8, "agosto"), (12, "diciembre")])
def test_la_fecha_va_en_espanol_y_no_segun_el_locale(mes, esperado):
    """`strftime('%B')` usa el locale del sistema, que aca es ingles: la portada
    salia "25 de August de 2026"."""
    assert pi._fecha_es(datetime(2026, mes, 25)) == f"25 de {esperado} de 2026"
