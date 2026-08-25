#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_curva_tasas.py
Suite del lector de curva soberana (`curva_reader`) y de la tool MCP get_curva_tasas.

Los casos deterministas usan archivos sintéticos en `tmp_path` en vez del JSON real
de `data central/`: los deltas dependen del histórico, que cambia con cada ingesta, y
un test que se apoye en él pasa hoy y falla mañana sin que nadie haya tocado código.
El archivo real se ejercita en un solo test de humo, con `now_dt` derivado de su
propio `as_of` para que tampoco dependa de cuándo se corre.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from market_data_mcp.curva_reader import (
    ARCHIVO_DEFAULT,
    SERIES_VALIDAS,
    cargar_curva_tasas,
)
from market_data_mcp.tools import curva_tasas


AS_OF = "2026-08-24T20:00:00+00:00"
# Martes, dos días hábiles después del último dato sintético (viernes 21).
AHORA = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def _archivo(tmp_path: Path, yields: dict, **extra) -> Path:
    """Escribe un treasury_fed_data.json sintético y devuelve su ruta."""
    datos = {
        "as_of": extra.pop("as_of", AS_OF),
        "fuente_tesoro": "U.S. Department of the Treasury (Fiscal Data API)",
        "fuente_fed": "Federal Reserve Bank of St. Louis (FRED)",
        "tesoro_status": extra.pop("tesoro_status", "OK"),
        "curva_rendimientos_yields": yields,
        **extra,
    }
    ruta = tmp_path / "treasury_fed_data.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return ruta


def _serie(historico: dict, status: str = "OK", nombre: str = "Serie de prueba") -> dict:
    return {"nombre": nombre, "unidad": "porcentaje", "historico": historico, "status": status}


# ── Conversión a puntos base ────────────────────────────────────────────────────

def test_una_centesima_de_punto_porcentual_es_un_punto_base(tmp_path):
    """4.19 -> 4.20 es +1 bp. Es la unidad de toda la tool: si esta conversión se
    rompe, el umbral del Playbook ("DGS10 > 4,70%") y el del scoring ("≥ 3 bps")
    quedan medidos en escalas distintas."""
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-20": 4.19, "2026-08-21": 4.20}),
    })
    res = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)

    assert "error" not in res, res
    serie = res["series"]["DGS10"]
    assert serie["nivel_pct"] == 4.20
    assert serie["fecha_dato"] == "2026-08-21"
    assert serie["delta_1d_bps"] == 1.0
    assert serie["fecha_base_1d"] == "2026-08-20"


def test_delta_negativo_cuando_la_tasa_baja(tmp_path):
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-20": 4.30, "2026-08-21": 4.12}),
    })
    res = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)
    assert res["series"]["DGS10"]["delta_1d_bps"] == -18.0


def test_delta_5d_cuenta_registros_y_no_dias_corridos(tmp_path):
    """Cinco registros atrás sobre una serie de días hábiles es una semana. El campo
    `fecha_base_5d` lo hace auditable en vez de dejarlo implícito."""
    historico = {
        "2026-08-14": 4.00, "2026-08-17": 4.05, "2026-08-18": 4.10,
        "2026-08-19": 4.15, "2026-08-20": 4.20, "2026-08-21": 4.25,
    }
    ruta = _archivo(tmp_path, {"DGS10": _serie(historico)})
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["delta_5d_bps"] == 25.0
    assert serie["fecha_base_5d"] == "2026-08-14"
    assert serie["frecuencia_publicacion"] == "dias_habiles"


def test_el_historico_desordenado_se_ordena_antes_de_calcular(tmp_path):
    """El extractor acumula el histórico en un dict y las claves NO quedan en orden
    (en el archivo real 2026-08-19 aparece después de 2026-07-08). Sin ordenar, el
    'último dato' sería el que quedó último en el JSON, que es cualquiera."""
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-21": 4.74, "2026-08-19": 4.70, "2026-08-20": 4.69}),
    })
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["fecha_dato"] == "2026-08-21", "el último dato es el más reciente por fecha"
    assert serie["nivel_pct"] == 4.74
    assert serie["delta_1d_bps"] == 5.0  # contra el 20, no contra el 19


# ── Un delta desconocido es null, nunca 0.0 ────────────────────────────────────

def test_un_solo_punto_deja_los_deltas_en_null(tmp_path):
    """Cero significa "no se movió", que es una afirmación distinta de "no sé"."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["nivel_pct"] == 4.74
    assert serie["delta_1d_bps"] is None
    assert serie["delta_5d_bps"] is None


def test_menos_de_seis_puntos_deja_solo_el_delta_5d_en_null(tmp_path):
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-20": 4.70, "2026-08-21": 4.74}),
    })
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["delta_1d_bps"] == 4.0
    assert serie["delta_5d_bps"] is None, "no hay 6 registros para mirar 5 atrás"


def test_serie_vacia_no_lanza_y_se_marca(tmp_path):
    ruta = _archivo(tmp_path, {"DGS10": _serie({})})
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["nivel_pct"] is None
    assert serie["delta_1d_bps"] is None
    assert "nota" in serie


def test_serie_con_status_distinto_de_ok_anula_los_deltas(tmp_path):
    """Los deltas se calcularían sobre datos que no se pudieron refrescar, y una
    cifra como "+5 bps" viaja sola hasta una pieza de cliente. El nivel y la fecha sí
    se informan: dicen de cuándo son."""
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-20": 4.70, "2026-08-21": 4.74}, status="ERROR_FRED"),
    })
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["status"] == "ERROR_FRED"
    assert serie["nivel_pct"] == 4.74
    assert serie["fecha_dato"] == "2026-08-21"
    assert serie["delta_1d_bps"] is None
    assert serie["delta_5d_bps"] is None
    assert "nota" in serie


def test_valores_nulos_en_el_historico_se_descartan(tmp_path):
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-19": 4.60, "2026-08-20": None, "2026-08-21": 4.74}),
    })
    serie = cargar_curva_tasas("DGS10", archivo=ruta, now_dt=AHORA)["series"]["DGS10"]

    assert serie["puntos_disponibles"] == 2
    assert serie["delta_1d_bps"] == 14.0, "compara contra el 19, saltándose el nulo"


# ── Frecuencia de publicación ──────────────────────────────────────────────────

def test_una_serie_con_fines_de_semana_se_marca_como_diaria(tmp_path):
    """DFF (tasa efectiva de fondos federales) publica los siete días porque es un
    promedio diario. Sin este campo, comparar su delta de 5 registros con el de
    DGS10 mezclaría una semana corrida con una semana hábil."""
    historico = {
        f"2026-08-{dia:02d}": 3.63 for dia in range(10, 22)
    }
    ruta = _archivo(tmp_path, {"DFF": _serie(historico)})
    serie = cargar_curva_tasas("DFF", archivo=ruta, now_dt=AHORA)["series"]["DFF"]

    assert serie["frecuencia_publicacion"] == "diaria"


# ── Pendiente 2s10s ────────────────────────────────────────────────────────────

def test_spread_2s10s_usa_solo_fechas_comunes(tmp_path):
    """Restar el último valor de cada serie por separado mezclaría días distintos si
    una viene con más rezago que la otra, y la pendiente es justamente una
    comparación entre tramos de la misma fecha."""
    ruta = _archivo(tmp_path, {
        "DGS2": _serie({"2026-08-20": 4.20, "2026-08-21": 4.24}),
        # El 10Y no trae el 21: la fecha común más reciente es el 20.
        "DGS10": _serie({"2026-08-19": 4.60, "2026-08-20": 4.70}),
    })
    spread = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)["spread_2s10s"]

    assert spread["fecha_dato"] == "2026-08-20"
    assert spread["nivel_pct"] == 0.5  # 4.70 - 4.20
    assert spread["invertida"] is False


def test_spread_invertido_se_marca(tmp_path):
    """Curva invertida (2Y por sobre 10Y) es la señal recesiva que el Playbook usa
    como condición de régimen R4."""
    ruta = _archivo(tmp_path, {
        "DGS2": _serie({"2026-08-20": 4.50, "2026-08-21": 4.60}),
        "DGS10": _serie({"2026-08-20": 4.40, "2026-08-21": 4.30}),
    })
    spread = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)["spread_2s10s"]

    assert spread["nivel_pct"] == -0.3
    assert spread["invertida"] is True
    assert spread["delta_1d_bps"] == -20.0  # la pendiente cayó 20 bps en un día


def test_sin_las_dos_patas_no_hay_spread(tmp_path):
    ruta = _archivo(tmp_path, {"DGS30": _serie({"2026-08-21": 5.27})})
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)
    assert "spread_2s10s" not in res


# ── Frescura y procedencia ─────────────────────────────────────────────────────

def test_archivo_viejo_retorna_stale_data(tmp_path):
    """Umbral de días hábiles: 24 h. AHORA es martes, así que aplica ese umbral y no
    el de 80 h del fin de semana."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})},
                    as_of="2026-08-20T12:00:00+00:00")
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)

    assert res["error"] == "STALE_DATA"
    assert res["antiguedad_horas"] > 24
    assert "pipeline_ingesta.py" in res["message"]


def test_el_rezago_del_dato_no_es_un_error(tmp_path):
    """Dos ejes distintos: el archivo puede estar recién bajado (as_of fresco) y el
    último dato traer rezago, porque FRED publica con un día hábil de retraso.
    Confundirlos marcaría STALE_DATA todos los lunes con datos normales."""
    ruta = _archivo(tmp_path, {
        "DGS10": _serie({"2026-08-20": 4.70, "2026-08-21": 4.74}),
    })
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)

    assert "error" not in res
    assert res["antiguedad_horas"] < 24, "el archivo está fresco"
    serie = res["series"]["DGS10"]
    assert serie["rezago_dias_habiles"] == 2, "lunes 24 y martes 25"
    assert "nota" in serie, "el rezago inusual se informa, sin fallar"


def test_as_of_malformado_retorna_read_error(tmp_path):
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})},
                    as_of="no-es-una-fecha")
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)

    assert res["error"] == "READ_ERROR"
    assert "as_of" in res["message"]


def test_archivo_ausente_retorna_stale_data_con_el_comando_a_correr():
    res = cargar_curva_tasas(archivo=Path("no/existe/treasury_fed_data.json"))
    assert res["error"] == "STALE_DATA"
    assert "pipeline_ingesta.py" in res["message"]


def test_json_ilegible_retorna_read_error(tmp_path):
    ruta = tmp_path / "treasury_fed_data.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)
    assert res["error"] == "READ_ERROR"


def test_fallback_del_tesoro_queda_declarado_en_la_procedencia(tmp_path):
    """La skill ecosistema-datos-macro exige soberanía de fuente, y la sección
    "05. Fuentes Consultadas" del PDF institucional tiene que poder citar de dónde
    salió la cifra. Un número sin procedencia no es auditable."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})},
                    tesoro_status="ERROR_FALLBACK")
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)

    proc = res["procedencia"]
    assert proc["tesoro_status"] == "ERROR_FALLBACK"
    assert "FRED" in proc["fuente_fed"]
    assert "nota" in proc, "el fallback se explica, no se esconde"


def test_sin_bloque_de_curva_retorna_read_error(tmp_path):
    ruta = tmp_path / "treasury_fed_data.json"
    ruta.write_text(json.dumps({"as_of": AS_OF}), encoding="utf-8")
    res = cargar_curva_tasas(archivo=ruta, now_dt=AHORA)
    assert res["error"] == "READ_ERROR"


# ── Contrato de serie pedida ───────────────────────────────────────────────────

def test_serie_fuera_del_catalogo_retorna_error_con_las_opciones(tmp_path):
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    res = cargar_curva_tasas("DGS7", archivo=ruta, now_dt=AHORA)

    assert res["error"] == "SERIE_NO_DISPONIBLE"
    assert "DGS10" in res["message"], "el mensaje lista las opciones válidas"


def test_serie_valida_ausente_del_archivo_retorna_error(tmp_path):
    """Pedir una serie que el catálogo admite pero el archivo no trae es un error
    explícito, no un dict vacío."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    res = cargar_curva_tasas("DGS30", archivo=ruta, now_dt=AHORA)

    assert res["error"] == "SERIE_NO_DISPONIBLE"
    assert "DGS30" in res["message"]


def test_all_omite_las_series_ausentes_sin_fallar(tmp_path):
    """Con "ALL" una serie que falta se omite en vez de tumbar la respuesta: las que
    sí están siguen sirviendo."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    res = cargar_curva_tasas("ALL", archivo=ruta, now_dt=AHORA)

    assert "error" not in res
    assert list(res["series"]) == ["DGS10"]


def test_nombre_de_serie_se_normaliza(tmp_path):
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    for pedida in ("dgs10", " DGS10 ", "Dgs10"):
        res = cargar_curva_tasas(pedida, archivo=ruta, now_dt=AHORA)
        assert "DGS10" in res.get("series", {}), f"no normalizó {pedida!r}"


# ── Solo lectura ───────────────────────────────────────────────────────────────

def test_no_muta_el_archivo(tmp_path):
    """Single-Writer Pattern: el único escritor de data central/ es el pipeline de
    ingesta. Este lector no puede tocar nada."""
    ruta = _archivo(tmp_path, {"DGS10": _serie({"2026-08-21": 4.74})})
    antes = ruta.read_bytes()

    cargar_curva_tasas(archivo=ruta, now_dt=AHORA)

    assert ruta.read_bytes() == antes


# ── Archivo real del repo (humo) ───────────────────────────────────────────────

@pytest.mark.skipif(not ARCHIVO_DEFAULT.exists(), reason="data central/ no disponible")
def test_humo_sobre_el_archivo_real():
    """Ejercita el JSON versionado. `now_dt` se deriva del propio `as_of` para que el
    test no dependa de cuándo se ejecute: lo que se verifica es la forma de la
    respuesta, no la frescura de la ingesta."""
    datos = json.loads(ARCHIVO_DEFAULT.read_text(encoding="utf-8"))
    ahora = datetime.fromisoformat(datos["as_of"]) + timedelta(hours=1)

    res = cargar_curva_tasas(archivo=ARCHIVO_DEFAULT, now_dt=ahora)

    assert "error" not in res, res
    assert set(res["series"]) == set(SERIES_VALIDAS), "las 6 series del extractor"

    for codigo, serie in res["series"].items():
        assert serie["nivel_pct"] is not None, f"{codigo} sin nivel"
        assert serie["unidad"] == "porcentaje"
        assert serie["fecha_dato"], f"{codigo} sin fecha"
        # Rango sanitario amplio: una tasa soberana fuera de -5%..25% es un error de
        # unidad (por ejemplo, haber leído el precio de un ETF en vez de la tasa).
        assert -5.0 < serie["nivel_pct"] < 25.0, (
            f"{codigo} en {serie['nivel_pct']}: revisar que no sea precio de un ETF"
        )

    assert res["spread_2s10s"]["nivel_pct"] is not None


@pytest.mark.skipif(not ARCHIVO_DEFAULT.exists(), reason="data central/ no disponible")
def test_la_tasa_real_es_dfii10_y_no_el_precio_de_un_etf():
    """Regresión de fuente: `US_TIPS_Real_Rates_ETF_Historical_5Y.csv` ronda 105
    porque es el precio de un ETF, no una tasa. La tasa real 10Y es DFII10 y vive en
    un dígito. Si alguien cambia la fuente, este test lo caza."""
    datos = json.loads(ARCHIVO_DEFAULT.read_text(encoding="utf-8"))
    ahora = datetime.fromisoformat(datos["as_of"]) + timedelta(hours=1)

    serie = cargar_curva_tasas("DFII10", archivo=ARCHIVO_DEFAULT, now_dt=ahora)["series"]["DFII10"]
    assert -2.0 < serie["nivel_pct"] < 6.0, (
        "la tasa real TIPS 10Y se mide en porcentaje de un dígito"
    )


# ── Tool MCP ───────────────────────────────────────────────────────────────────

def test_la_tool_queda_registrada_y_devuelve_dict(collector):
    curva_tasas.register(collector)
    assert "get_curva_tasas" in collector.tools

    res = collector.tools["get_curva_tasas"]()
    assert isinstance(res, dict)
    # Con o sin data central fresca, siempre responde el contrato: nunca None.
    assert "series" in res or "error" in res


def test_la_tool_propaga_el_contrato_de_error(collector):
    curva_tasas.register(collector)
    res = collector.tools["get_curva_tasas"](serie="NO_EXISTE")
    assert res["error"] == "SERIE_NO_DISPONIBLE"
