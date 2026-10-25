"""Tests de los textos y el payload del suceso único de seguimiento.

Plan: docs/superpowers/plans/2026-10-21-seguimiento-suceso-unico.md (Task 3).
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)


from analista.suceso import Resumen  # noqa: E402
from analista import suceso_texto as st  # noqa: E402
from analista import comercial as cm  # noqa: E402
from analista.seguimiento import MARCA_SALUDO  # noqa: E402


CLAVES_ESPERADAS_PAYLOAD = {
    "logo_src",
    "chip",
    "datos_al",
    "activo",
    "direccion",
    "estado",
    "flecha",
    "titular",
    "linea_chica",
    "nota_semana",
    "chart_png",
    "pie_imagen",
    "firma",
    "aviso",
}


def test_lamina_cada_estado_alcista_y_bajista():
    # Alcista
    casos_alcista = [
        (
            Resumen("esperando", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
            ("⬆️", "Esperamos los 4.000,00 para un rebote al alza", "Si se da, el siguiente paso es 4.060,00"),
        ),
        (
            Resumen("en_nivel", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
            ("⬆️", "El precio está en los 4.000,00: aquí se define el rebote", "Lo confirma una vela de 5 minutos que cierre sobre la línea"),
        ),
        (
            Resumen("rebotando", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
            ("⬆️", "Rebotó en los 4.000,00 y va camino a 4.060,00", "La línea de control sigue en 4.000,00"),
        ),
        (
            Resumen("cumplido", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
            ("✅", "Rebotó en los 4.000,00 y llegó a 4.060,00", "Lectura cumplida"),
        ),
        (
            Resumen("ruptura", "ALCISTA", 4000.0, None, 3950.0, "A+", ""),
            ("⬇️", "Perdió los 4.000,00: ahora la presión es a la baja", "El siguiente nivel a vigilar es 3.950,00"),
        ),
        (
            Resumen("sin_direccion", None, None, None, None, "", ""),
            ("↔️", "Hoy el precio se mueve en rango", "Esperamos que salga de la zona antes de marcar un nivel"),
        ),
        (
            Resumen("cerrado", None, None, None, None, "", ""),
            ("↔️", "El mercado está cerrado", "El seguimiento de hoy parte con la apertura"),
        ),
        (
            Resumen("semana", "ALCISTA", 4000.0, 4060.0, None, "", ""),
            ("⬆️", "La semana sigue al alza: el precio consolida sobre 4.000,00",
             "Mientras no cierre bajo 4.000,00, el objetivo es 4.060,00. Esperamos una señal clara de hoy para el punto de entrada"),
        ),
    ]
    for r, esperado in casos_alcista:
        assert st.lamina(r, digits=2) == esperado

    # Bajista
    casos_bajista = [
        (
            Resumen("esperando", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
            ("⬇️", "Esperamos los 4.000,00 para un rechazo a la baja", "Si se da, el siguiente paso es 3.940,00"),
        ),
        (
            Resumen("en_nivel", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
            ("⬇️", "El precio está en los 4.000,00: aquí se define el rechazo", "Lo confirma una vela de 5 minutos que cierre bajo la línea"),
        ),
        (
            Resumen("rebotando", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
            ("⬇️", "Se devolvió en los 4.000,00 y va camino a 3.940,00", "La línea de control sigue en 4.000,00"),
        ),
        (
            Resumen("cumplido", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
            ("✅", "Se devolvió en los 4.000,00 y llegó a 3.940,00", "Lectura cumplida"),
        ),
        (
            Resumen("ruptura", "BAJISTA", 4000.0, None, 4050.0, "A+", ""),
            ("⬆️", "Superó los 4.000,00: ahora la fuerza es al alza", "El siguiente nivel a vigilar es 4.050,00"),
        ),
        (
            Resumen("sin_direccion", "BAJISTA", None, None, None, "", ""),
            ("↔️", "Hoy el precio se mueve en rango", "Esperamos que salga de la zona antes de marcar un nivel"),
        ),
        (
            Resumen("cerrado", "BAJISTA", None, None, None, "", ""),
            ("↔️", "El mercado está cerrado", "El seguimiento de hoy parte con la apertura"),
        ),
    ]
    casos_bajista.append((
        Resumen("semana", "BAJISTA", 4000.0, 3940.0, None, "", ""),
        ("⬇️", "La semana sigue a la baja: el precio consolida bajo 4.000,00",
         "Mientras no cierre sobre 4.000,00, el objetivo es 3.940,00. Esperamos una señal clara de hoy para el punto de entrada"),
    ))
    for r, esperado in casos_bajista:
        assert st.lamina(r, digits=2) == esperado


def test_lamina_sin_objetivo_y_sin_siguiente():
    # Alcista sin objetivo
    r_esp_alc = Resumen("esperando", "ALCISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_esp_alc, digits=2) == (
        "⬆️",
        "Esperamos los 4.000,00 para un rebote al alza",
        "Lo confirma una vela de 5 minutos que rebote sobre la línea",
    )
    r_reb_alc = Resumen("rebotando", "ALCISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_reb_alc, digits=2) == (
        "⬆️",
        "Rebotó en los 4.000,00: la fuerza sigue al alza",
        "La línea de control sigue en 4.000,00",
    )
    # Alcista sin siguiente en ruptura
    r_rup_alc = Resumen("ruptura", "ALCISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_rup_alc, digits=2) == (
        "⬇️",
        "Perdió los 4.000,00: ahora la presión es a la baja",
        "Esperamos que el precio defina antes de leer otro nivel",
    )

    # Bajista sin objetivo
    r_esp_baj = Resumen("esperando", "BAJISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_esp_baj, digits=2) == (
        "⬇️",
        "Esperamos los 4.000,00 para un rechazo a la baja",
        "Lo confirma una vela de 5 minutos que rechace bajo la línea",
    )
    r_reb_baj = Resumen("rebotando", "BAJISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_reb_baj, digits=2) == (
        "⬇️",
        "Se devolvió en los 4.000,00: la presión sigue a la baja",
        "La línea de control sigue en 4.000,00",
    )
    # Bajista sin siguiente en ruptura
    r_rup_baj = Resumen("ruptura", "BAJISTA", 4000.0, None, None, "A+", "")
    assert st.lamina(r_rup_baj, digits=2) == (
        "⬆️",
        "Superó los 4.000,00: ahora la fuerza es al alza",
        "Esperamos que el precio defina antes de leer otro nivel",
    )


def test_nota_semana_tres_casos():
    # 1. Reemplazada
    assert st.nota_semana("ALCISTA", "ALCISTA", reemplazada=True) == "Ojo: lo que vimos el lunes cambió. La semana ahora se lee al alza."
    assert st.nota_semana("BAJISTA", "BAJISTA", reemplazada=True) == "Ojo: lo que vimos el lunes cambió. La semana ahora se lee a la baja."
    assert st.nota_semana("ALCISTA", "LATERAL", reemplazada=True) == "La semana ahora no marca dirección."

    # 2. No reemplazada pero dirección semana ALCISTA/BAJISTA distinta de sentido
    assert st.nota_semana("ALCISTA", "BAJISTA", reemplazada=False) == "Es un retroceso de hoy: la tendencia de la semana sigue a la baja."
    assert st.nota_semana("BAJISTA", "ALCISTA", reemplazada=False) == "Es un retroceso de hoy: la tendencia de la semana sigue al alza."

    # 3. Cualquier otro caso -> ""
    assert st.nota_semana("ALCISTA", "ALCISTA", reemplazada=False) == ""
    assert st.nota_semana("BAJISTA", "BAJISTA", reemplazada=False) == ""
    assert st.nota_semana("ALCISTA", "LATERAL", reemplazada=False) == ""
    assert st.nota_semana("LATERAL", "LATERAL", reemplazada=False) == ""
    assert st.nota_semana(None, "ALCISTA", reemplazada=False) == ""


def test_whatsapp_cfd_una_vez_y_sin_cifras():
    resumenes = [
        Resumen("esperando", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
        Resumen("en_nivel", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
        Resumen("rebotando", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
        Resumen("cumplido", "ALCISTA", 4000.0, 4060.0, None, "A+", ""),
        Resumen("ruptura", "ALCISTA", 4000.0, None, 3950.0, "A+", ""),
        Resumen("sin_direccion", None, None, None, None, "", ""),
        Resumen("cerrado", None, None, None, None, "", ""),
        Resumen("esperando", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
        Resumen("en_nivel", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
        Resumen("rebotando", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
        Resumen("cumplido", "BAJISTA", 4000.0, 3940.0, None, "A+", ""),
        Resumen("ruptura", "BAJISTA", 4000.0, None, 4050.0, "A+", ""),
        Resumen("rebotando", "ALCISTA", 4000.0, 4060.0, None, "A+", "Es un retroceso de hoy: la tendencia de la semana sigue a la baja."),
    ]
    for r in resumenes:
        txt = st.whatsapp(r, "Oro")
        assert txt.startswith(MARCA_SALUDO + " ")
        assert txt.count("CFD") == 1
        # Ningún dígito fuera de MARCA_SALUDO
        cuerpo = txt.replace(MARCA_SALUDO, "")
        assert not any(c.isdigit() for c in cuerpo), f"Texto con dígitos: {txt}"
        if r.nota_semana:
            assert txt.endswith(r.nota_semana)


def test_textos_sin_guion_largo_ni_voseo():
    prohibidos = ["—", "–", "stop", "techo", "suelo", "tenés", "podés", "mirá", "hacé", "querés", "sabés"]
    textos = []

    for sentido in ("ALCISTA", "BAJISTA"):
        for estado in ("esperando", "en_nivel", "rebotando", "cumplido", "ruptura"):
            r = Resumen(estado, sentido, 4000.0, 4050.0, 3950.0, "A+", "")
            flecha, titular, linea = st.lamina(r, digits=2)
            textos.extend([titular, linea])
            textos.append(st.whatsapp(r, "Oro"))

    r_sin = Resumen("sin_direccion", None, None, None, None, "", "")
    flecha, titular, linea = st.lamina(r_sin, digits=2)
    textos.extend([titular, linea, st.whatsapp(r_sin, "Oro")])

    r_cer = Resumen("cerrado", None, None, None, None, "", "")
    flecha, titular, linea = st.lamina(r_cer, digits=2)
    textos.extend([titular, linea, st.whatsapp(r_cer, "Oro")])

    for r_flag in (True, False):
        for s in ("ALCISTA", "BAJISTA"):
            for d in ("ALCISTA", "BAJISTA", "LATERAL"):
                textos.append(st.nota_semana(s, d, r_flag))

    for t in textos:
        for p in prohibidos:
            assert p not in t.lower(), f"Encontrado {p!r} en {t!r}"


def test_payload_suceso_claves(tmp_path):
    chart = tmp_path / "chart.png"
    chart.write_bytes(b"fake_chart")
    activo = {
        "nombre": "Oro",
        "ticker_visible": "XAU/USD",
        "digits": 2,
    }
    resumen = {
        "estado": "rebotando",
        "sentido": "ALCISTA",
        "nivel": 4000.0,
        "objetivo": 4060.0,
        "siguiente": None,
        "calidad": "A+",
        "nota_semana": "",
    }
    autor = SimpleNamespace(nombre="Benjamín Bravo", cargo="Departamento de Estudios")
    payload = cm.payload_suceso(activo, resumen, "21-10 · 11:30 CLST", autor, chart)

    assert set(payload.keys()) == CLAVES_ESPERADAS_PAYLOAD
    assert payload["chip"] == "SEGUIMIENTO DE HOY"
    assert payload["activo"] == "Oro · XAU/USD"
    assert payload["direccion"] == "alcista"
    assert payload["estado"] == "rebotando"
    assert payload["flecha"] == "⬆️"
    assert payload["titular"] == "Rebotó en los 4.000,00 y va camino a 4.060,00"
    assert payload["linea_chica"] == "La línea de control sigue en 4.000,00"
    assert payload["chart_png"] == str(chart)
    assert payload["pie_imagen"] == "Oro · velas de 15 minutos · MetaTrader 5"
    assert "Benjamín Bravo" in payload["firma"]


def test_whatsapp_semana_habla_de_la_tendencia_sin_precios():
    r = Resumen("semana", "BAJISTA", 158.361, 156.631, None, "", "")
    msg = st.whatsapp(r, "Dólar / Yen japonés")
    assert "sigue a la baja" in msg and "consolidando" in msg
    assert "158" not in msg and "—" not in msg
