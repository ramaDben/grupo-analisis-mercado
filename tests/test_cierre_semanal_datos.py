"""Cifras de la tabla de curva del cierre semanal.

El cierre semanal es un documento de cliente: toda sigla va explicada (issue #46),
y en una celda de tabla no cabe la explicación, así que la unidad va en palabras,
con el mismo término que ya usa la prosa del documento ("puntos base").
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import cierre_semanal_datos as csd  # noqa: E402


def test_la_variacion_va_en_puntos_base_y_sin_la_sigla():
    assert csd._bps(13.0) == "+13 puntos base"
    assert csd._bps(-4.0) == "-4 puntos base"


def test_un_delta_incalculable_se_dice_y_no_se_publica_como_cero():
    assert csd._bps(None) == "no disponible"


# ─────────────────────────────────────────────────────────────────────────────
# Enchufe de estrategia: niveles y dirección salen de la `Lectura` (spec §6)
# ─────────────────────────────────────────────────────────────────────────────
import pytest  # noqa: E402

import cierre_semanal_contenido as C  # noqa: E402
from estrategia.contrato import Escenario, Lectura, Linea, Referencia  # noqa: E402


def _lectura(ticker, precio, vigilar, invalidacion, objetivo, direccion="ALCISTA", estado="TENDENCIA"):
    lin = Linea("seguridad", "diagonal", ((100, vigilar - 1), (200, vigilar)), "H4", 3, "A+", vigilar)
    ref = Referencia(vigilar, f"línea {direccion.lower()} de seguridad", lin)
    inv = Referencia(invalidacion, "invalida la lectura") if invalidacion is not None else None
    obj = Referencia(objetivo, "objetivo") if objetivo is not None else None
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(
        ticker=ticker, marco="H4", precio=precio, direccion=direccion, estado=estado,
        lineas=(lin,), en_prueba=None, vigilar=ref, invalidacion=inv, objetivo=obj,
        escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


ACTIVO = {"ticker": "USDCLP", "slug": "usdclp", "digits": 2,
          "previo_txt": "925,00", "actual_txt": "931,40", "var_txt": "+0,69%"}


def test_significa_sale_de_la_lectura_alcista():
    capas = C.capas_de("usdclp", ACTIVO, _lectura("USDCLP", 931.4, 925.0, 920.5, 938.25))
    sig = capas["significa"]
    assert "Lectura de 4 horas: tendencia alcista" in sig
    assert "925,00" in sig and "línea alcista de seguridad" in sig
    assert "la lectura deja de valer con un cierre de 4 horas bajo 920,50" in sig.lower()


def test_significa_bajista_invalida_por_arriba():
    activo = {**ACTIVO, "slug": "wti", "digits": 3}
    capas = C.capas_de("wti", activo, _lectura("WTI.spot", 88.1, 90.25, 91.5, 86.502, "BAJISTA"))
    assert "cierre de 4 horas sobre 91,500" in capas["significa"]


def test_significa_sin_invalidacion_omite_la_frase():
    capas = C.capas_de("usdclp", ACTIVO, _lectura("USDCLP", 931.4, 925.0, None, None))
    assert "deja de valer" not in capas["significa"]


def test_significa_en_rango_nombra_soporte_y_resistencia():
    lect = _lectura("USDCLP", 931.4, 925.0, None, 938.25, "LATERAL", "RANGO")
    sig = C.capas_de("usdclp", ACTIVO, lect)["significa"]
    assert "925,00" in sig and "938,25" in sig
    assert "soporte" in sig.lower() and "resistencia" in sig.lower()


def test_ninguna_capa_trae_otra_lectura_tecnica_ni_guion_largo():
    lect = _lectura("USDCLP", 931.4, 925.0, 920.5, 938.25)
    for slug in C.CAPAS:
        assert "significa" not in C.CAPAS[slug], f"{slug}: la capa significa sale de la lectura"
        capas = C.capas_de(slug, ACTIVO, lect)
        for texto in capas.values():
            bajo = texto.lower()
            assert "promedio" not in bajo and "fuerza de tendencia" not in bajo
            assert "canal de las últimas 50" not in bajo
            assert "—" not in texto and "–" not in texto
            assert "{" not in texto


def test_leer_lectura_usa_la_estrategia_con_los_digits_del_catalogo(monkeypatch):
    import referencia_semanal as rs
    from estrategia import registro

    llamadas = []

    def falsa(estrategia, ticker, digits, lector, ahora, base=None, referencia=None):
        llamadas.append((estrategia, ticker, digits))
        return _lectura(ticker, 88.1, 90.25, 91.5, 86.502, "BAJISTA"), None

    monkeypatch.setattr(registro, "activa", lambda: "tori")
    monkeypatch.setattr(rs, "lectura_actual", falsa)
    lect = csd.leer_lectura("WTI.spot")
    assert llamadas == [("tori", "WTI.spot", 3)]
    assert lect.direccion == "BAJISTA"


def test_el_modulo_no_lee_analizar_activo():
    fuente = (RAIZ / "scripts" / "cierre_semanal_datos.py").read_text(encoding="utf-8")
    assert "analizar_activo" not in fuente and "leer_niveles" not in fuente


def test_el_grafico_traza_la_lectura_y_no_las_medias(monkeypatch, tmp_path):
    import grafico_informe as gi

    lect = _lectura("USDCLP", 931.4, 925.0, 920.5, 938.25)
    monkeypatch.setattr(csd, "leer_lectura", lambda ticker: lect)
    vistos = {}

    def falso(ticker, nombre, destino, **kw):
        vistos.update(kw)
        return destino

    monkeypatch.setattr(gi, "construir_grafico", falso)
    activo = {**ACTIVO, "nombre": "Dólar", "unidad": ""}
    csd.generar_graficos([activo], tmp_path)
    assert vistos["medias"] is False
    assert vistos["niveles"] == {"price": 931.4}
    assert (925.0, "Nivel a vigilar", "nivel") in vistos["horizontales"]
    assert vistos["subtitulo"].startswith("Cerró la semana en 931,40")
