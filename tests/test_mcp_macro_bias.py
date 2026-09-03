#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mcp_macro_bias.py
Suite de pruebas automatizadas para el módulo bias_reader y la tool MCP get_macro_bias.
Valida contratos de Schema v2.0.0, cero mutación de archivos, staleness consciente de fines de semana y fail-closed.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from market_data_mcp.bias_reader import (
    OUTPUT_FILE_DEFAULT,
    cargar_macro_bias,
    validar_staleness,
    VALID_SYMBOLS
)

RAIZ = Path(__file__).resolve().parent.parent


def _reloj_del_snapshot():
    """Un `now_dt` anclado al `as_of_utc` del propio snapshot versionado.

    Los dos tests de contrato de abajo validan la FORMA del payload, no su
    frescura, pero llamaban sin `now_dt` y quedaban a merced del reloj de pared
    contra un archivo que vive en git. El resultado era una bomba de tiempo: el
    2026-09-02 a las 17:53 UTC el snapshot committeado cruzó las 24 h de umbral y
    CI pasó a rojo en master y en las cinco ramas abiertas a la vez, sin que
    nadie hubiera tocado una línea de código. La última corrida verde de master
    fue a las 13:52, con el mismo commit.

    Un test cuyo resultado depende de la hora a la que corre no informa nada:
    ni afirma que el contrato está bien ni que el dato está fresco. La frescura
    ya la cubre `test_mcp_macro_bias_weekend_staleness`, que la ejercita con
    fechas sintéticas y sin depender de qué día se corra la suite.

    Es el mismo criterio que el resto del archivo: los otros cinco tests montan
    su propio JSON en `tmp_path` y pasan `now_dt` explícito.
    """
    if not OUTPUT_FILE_DEFAULT.exists():
        pytest.skip("no hay snapshot del motor en este clon")
    as_of = json.loads(OUTPUT_FILE_DEFAULT.read_text(encoding="utf-8")).get("as_of_utc")
    if not as_of:
        pytest.skip("el snapshot no declara as_of_utc")
    # Una hora después de la emisión: dentro de cualquier umbral, y sigue siendo
    # un instante real relativo al dato en vez de un valor inventado.
    return datetime.fromisoformat(as_of.replace("Z", "+00:00")) + timedelta(hours=1)


def test_mcp_macro_bias_all_contract():
    """Valida que la consulta 'ALL' retorne exactamente el contrato Schema v2.0.0."""
    res = cargar_macro_bias("ALL", now_dt=_reloj_del_snapshot())
    assert "error" not in res, f"Retornó error inesperado: {res.get('error')}"
    assert res.get("schema_version") == "2.0.0"
    assert "config_hash" in res and len(res["config_hash"]) == 16
    assert "as_of_utc" in res
    assert "regimen_macro_global" in res
    assert "metricas_clave" in res
    assert "confianza_general" in res
    assert "activos" in res
    assert "USDCLP" in res["activos"]
    assert "XAUUSD" in res["activos"]


def test_mcp_macro_bias_single_symbol_contract():
    """Valida que la consulta por símbolo individual incluya trazabilidad completa."""
    res = cargar_macro_bias("USDCLP", now_dt=_reloj_del_snapshot())
    assert "error" not in res
    assert res.get("symbol") == "USDCLP"
    assert res.get("schema_version") == "2.0.0"
    assert "config_hash" in res
    assert "regimen_macro_global" in res
    assert "metricas_clave" in res
    assert "confianza_general" in res
    assert "activo" in res
    activo = res["activo"]
    assert activo.get("nombre") == "Dólar / Peso Chileno"
    assert "setups_permitidos" in activo
    assert "setups_prohibidos" in activo
    assert "parametros_riesgo" in activo
    assert activo["parametros_riesgo"]["distancia_sl_h1_puntos"] > 0


def test_mcp_macro_bias_invalid_ticker():
    """Valida el contrato de error unificado TICKER_NOT_IN_CATALOG."""
    res = cargar_macro_bias("EURUSD")
    assert res.get("error") == "TICKER_NOT_IN_CATALOG"
    assert "EURUSD" in res.get("message", "")


def test_mcp_macro_bias_zero_mutation(tmp_path):
    """Valida que la tool MCP sea estrictamente de solo lectura y no altere el archivo."""
    test_json = tmp_path / "test_macro_bias.json"
    dummy_data = {
        "schema_version": "2.0.0",
        "config_hash": "b571f800c4e05148",
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO", "nombre": "Calma"},
        "activos": {"USDCLP": {"nombre": "USDCLP", "parametros_riesgo": {"distancia_sl_h1_puntos": 2.83}}}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    mtime_before = test_json.stat().st_mtime_ns
    content_before = test_json.read_text(encoding="utf-8")

    # Múltiples lecturas
    for _ in range(5):
        res = cargar_macro_bias("USDCLP", output_file=test_json)
        assert "error" not in res

    mtime_after = test_json.stat().st_mtime_ns
    content_after = test_json.read_text(encoding="utf-8")

    assert mtime_before == mtime_after, "El archivo fue mutado durante la lectura MCP"
    assert content_before == content_after


def test_mcp_macro_bias_weekend_staleness(tmp_path):
    """Valida que un dato de 60h sea válido en fin de semana (80h) pero stale un miércoles (24h)."""
    test_json = tmp_path / "test_weekend.json"
    # Fecha de emisión: hace 60 horas
    fecha_emision = datetime(2026, 8, 14, 21, 0, 0, tzinfo=timezone.utc)  # Viernes 21:00 UTC
    dummy_data = {
        "schema_version": "2.0.0",
        "config_hash": "b571f800c4e05148",
        "as_of_utc": fecha_emision.isoformat(),
        "regimen_macro_global": {"codigo": "R0_CALMA_RANGO"},
        "activos": {"USDCLP": {"nombre": "USDCLP"}}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    # 1. Simular Domingo 09:00 UTC (hace 60h desde viernes) -> Domingo = weekday 6
    domingo_dt = datetime(2026, 8, 16, 9, 0, 0, tzinfo=timezone.utc)
    res_domingo = cargar_macro_bias("USDCLP", output_file=test_json, now_dt=domingo_dt)
    assert "error" not in res_domingo, "Falsamente marcado como stale en fin de semana"

    # 2. Simular Miércoles 09:00 UTC (hace 60h desde lunes) -> Miércoles = weekday 2
    miercoles_dt = datetime(2026, 8, 19, 9, 0, 0, tzinfo=timezone.utc)
    res_miercoles = cargar_macro_bias("USDCLP", output_file=test_json, now_dt=miercoles_dt)
    assert res_miercoles.get("error") == "STALE_DATA"
    assert res_miercoles.get("antiguedad_horas") > 24.0


def test_mcp_macro_bias_malformed_date(tmp_path):
    """Valida fail-closed ante fecha as_of_utc corrupta retornando READ_ERROR."""
    test_json = tmp_path / "test_corrupt.json"
    dummy_data = {
        "schema_version": "2.0.0",
        "as_of_utc": "INVALID_DATE_FORMAT_1234",
        "activos": {}
    }
    test_json.write_text(json.dumps(dummy_data), encoding="utf-8")

    res = cargar_macro_bias("USDCLP", output_file=test_json)
    assert res.get("error") == "READ_ERROR"
    assert "as_of_utc" in res.get("message", "")


def test_mcp_macro_bias_missing_file(tmp_path):
    """Valida que si el archivo no existe se retorne STALE_DATA sin auto-ejecutar subprocesos."""
    missing_file = tmp_path / "non_existent_file.json"
    res = cargar_macro_bias("USDCLP", output_file=missing_file)
    assert res.get("error") == "STALE_DATA"
    assert not missing_file.exists(), "No debe crear archivos en lecturas de solo lectura"


# ─────────────────────────────────────────────────────────────────────────────
# El nivel del Chandelier: una sola implementación de la aritmética
# ─────────────────────────────────────────────────────────────────────────────

def test_config_de_riesgo_expone_los_parametros_del_playbook():
    """Los parámetros no se hardcodean en el MCP: salen del YAML que el Playbook
    hashea. Dos fuentes para el mismo número es el error del ATR otra vez."""
    from market_data_mcp.bias_reader import cargar_config_riesgo

    cfg = cargar_config_riesgo()
    assert cfg["trailing_stop_lookback_period"] == 22
    assert cfg["trailing_stop_mult_trend"] == 3.0
    assert cfg["trailing_stop_mult_precautorio"] == 2.0


def test_nivel_chandelier_en_las_dos_direcciones():
    """Largo: máximo menos k×ATR. Corto: mínimo más k×ATR."""
    from market_data_mcp.bias_reader import nivel_chandelier

    largo = nivel_chandelier(extremo=4463.84, atr=20.98, multiplo=3.0, direccion="LARGO", digits=2)
    corto = nivel_chandelier(extremo=4282.38, atr=20.98, multiplo=3.0, direccion="CORTO", digits=2)

    assert largo == pytest.approx(4463.84 - 3.0 * 20.98, abs=0.01)
    assert corto == pytest.approx(4282.38 + 3.0 * 20.98, abs=0.01)
    assert largo < 4463.84, "el stop de un largo queda POR DEBAJO del máximo"
    assert corto > 4282.38, "el stop de un corto queda POR ENCIMA del mínimo"


def test_el_nivel_cambia_con_el_multiplicador_del_snapshot():
    """La consecuencia de la decisión de Kilian: WTI en shock precautorio arrastra
    con 2,0 y no con 3,0, así que su "hasta dónde" es otro nivel. Si el MCP
    horneara el 3,0, publicaríamos el nivel equivocado justo en el activo más
    direccional del día."""
    from market_data_mcp.bias_reader import nivel_chandelier

    tendencia = nivel_chandelier(extremo=92.553, atr=0.755, multiplo=3.0, direccion="LARGO", digits=3)
    precaut = nivel_chandelier(extremo=92.553, atr=0.755, multiplo=2.0, direccion="LARGO", digits=3)

    assert precaut > tendencia, "un trailing más ceñido queda MÁS CERCA del precio"
    assert precaut - tendencia == pytest.approx(0.755, abs=0.001)


def test_el_nivel_rechaza_una_direccion_que_no_existe():
    """Fail-fast: un typo en la dirección no puede devolver un número plausible."""
    from market_data_mcp.bias_reader import nivel_chandelier

    with pytest.raises(ValueError, match="LARGO"):
        nivel_chandelier(extremo=100.0, atr=1.0, multiplo=3.0, direccion="ALCISTA", digits=2)


def test_todo_activo_del_playbook_mapea_a_un_ticker_del_catalogo():
    """El contrato que impide que un activo tenga sesgo y no tenga niveles.

    `TICKER_MT5` traduce el símbolo genérico del Playbook al del broker. Brent
    apuntaba a None con el comentario "el broker no ofrece Brent", cosa que el
    terminal desmintió el 2026-09-02: `BRENT.spot` cotizaba a 96,439.

    Un activo con ficha, régimen, sesgo y setups permitidos pero sin ticker es un
    activo del que el sistema opina y sobre el que no puede medir nada.
    """
    from market_data_mcp.bias_reader import TICKER_MT5, VALID_SYMBOLS
    from market_data_mcp.catalog import VALID_TICKERS

    con_ficha = VALID_SYMBOLS - {"ALL"}
    sin_mapeo = sorted(s for s in con_ficha if not TICKER_MT5.get(s))
    assert not sin_mapeo, f"activos del Playbook sin ticker MT5: {sin_mapeo}"

    fuera_del_catalogo = sorted(
        f"{s} -> {TICKER_MT5[s]}" for s in con_ficha if TICKER_MT5[s] not in VALID_TICKERS
    )
    assert not fuera_del_catalogo, (
        f"mapean a un ticker que el catálogo técnico no conoce: {fuera_del_catalogo}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Las dos gramaticas de vigencia
# ─────────────────────────────────────────────────────────────────────────────
def _sesgo(tp_tipo, score, permitidos=("PULLBACK_EMA20_H1",), mult=3.0, etiqueta="ALCISTA"):
    """Payload de `cargar_macro_bias(sym)` reducido a lo que mira el resolutor."""
    return {
        "symbol": "USDCLP",
        "activo": {
            "sesgo_score": score,
            "sesgo_etiqueta": etiqueta,
            "setups_permitidos": list(permitidos),
            "parametros_riesgo": {
                "take_profit_tipo": tp_tipo,
                "trailing_stop_mult_atr": mult,
                "trailing_stop_lookback": 22,
                "atr_h1": 2.17,
            },
        },
    }


_H1 = {
    "price": 937.25, "s1": 933.10, "r1": 941.80,
    "atr_14": 2.17, "chandelier_max": 939.95, "chandelier_min": 928.40,
    "chandelier_lookback": 22,
}


def test_trailing_asimetrico_se_resuelve_como_un_solo_nivel():
    """Score distinto de cero: posicion sostenida, un solo borde (el Chandelier)."""
    from market_data_mcp.bias_reader import resolver_vigencia

    v = resolver_vigencia(_sesgo("TRAILING_STOP_ASYMMETRIC", 0.80), _H1, digits=2)

    assert v["gramatica"] == "NIVEL"
    assert v["direccion"] == "LARGO"
    assert v["nivel"] == pytest.approx(939.95 - 3.0 * 2.17, abs=0.01)
    assert v["borde_inferior"] is None and v["borde_superior"] is None
    assert v["vigente"] is True, "937,25 esta por encima del stop: la lectura sigue en pie"


def test_un_score_negativo_ancla_en_el_minimo_y_el_nivel_queda_arriba():
    from market_data_mcp.bias_reader import resolver_vigencia

    v = resolver_vigencia(_sesgo("TRAILING_STOP_ASYMMETRIC", -1.20, etiqueta="BAJISTA"), _H1, digits=2)

    assert v["direccion"] == "CORTO"
    assert v["nivel"] == pytest.approx(928.40 + 3.0 * 2.17, abs=0.01)
    assert v["nivel"] > _H1["chandelier_min"], "el stop de un corto va POR ENCIMA del minimo"
    # El precio de la fixture (937,25) esta por encima de ese stop, asi que este
    # corto ya se rompio. Se afirma a proposito: la invalidacion tiene que
    # detectarse en las dos direcciones, no solo cuando cae un largo.
    assert v["vigente"] is False


def test_nivel_opuesto_canal_se_resuelve_como_rango_de_dos_bordes():
    """Score cero: no hay tendencia que sostener, hay un canal por el que rota."""
    from market_data_mcp.bias_reader import resolver_vigencia

    v = resolver_vigencia(
        _sesgo("NIVEL_OPUESTO_CANAL", 0.0, permitidos=("RANGE_DONCHIAN_FADE",),
               mult=None, etiqueta="NEUTRAL / CONSOLIDACIÓN"),
        _H1, digits=2,
    )

    assert v["gramatica"] == "RANGO"
    assert v["nivel"] is None, "un rango no tiene un solo 'hasta donde'"
    assert (v["borde_inferior"], v["borde_superior"]) == (933.10, 941.80)
    assert v["direccion"] is None
    assert v["vigente"] is True, "el precio esta dentro del canal"


def test_el_precio_fuera_del_canal_deja_el_rango_sin_vigencia():
    from market_data_mcp.bias_reader import resolver_vigencia

    fuera = {**_H1, "price": 942.60}
    v = resolver_vigencia(
        _sesgo("NIVEL_OPUESTO_CANAL", 0.0, mult=None), fuera, digits=2
    )

    assert v["vigente"] is False


def test_un_activo_sin_setups_permitidos_no_publica_vigencia():
    """`DATOS_INCOMPLETOS` trae `NIVEL_OPUESTO_CANAL` y score cero, igual que un
    rango genuino. Pero no es lo mismo: ahi el modelo no leyo el activo, no leyo
    que rote. Publicar "vigente entre S1 y R1" afirmaria una lectura que nadie
    hizo, que es exactamente el error que este resolutor existe para evitar."""
    from market_data_mcp.bias_reader import resolver_vigencia

    v = resolver_vigencia(
        _sesgo("NIVEL_OPUESTO_CANAL", 0.0, permitidos=(), mult=None,
               etiqueta="DATOS_INCOMPLETOS"),
        _H1, digits=2,
    )

    assert v is None


def test_sin_anclas_del_chandelier_no_se_inventa_el_nivel():
    """Fail-closed: el MCP viejo no devuelve `chandelier_max`. Sin el ancla no
    hay nivel, y un `s1` cualquiera en su lugar publicaria otro numero."""
    from market_data_mcp.bias_reader import resolver_vigencia

    sin_ancla = {k: v for k, v in _H1.items() if not k.startswith("chandelier")}
    v = resolver_vigencia(_sesgo("TRAILING_STOP_ASYMMETRIC", 0.80), sin_ancla, digits=2)

    assert v is None


def test_un_sesgo_con_error_no_produce_vigencia():
    from market_data_mcp.bias_reader import resolver_vigencia

    assert resolver_vigencia({"error": "STALE_DATA", "message": "..."}, _H1, digits=2) is None
    assert resolver_vigencia(None, _H1, digits=2) is None


def test_todo_take_profit_tipo_del_motor_tiene_gramatica():
    """Contrato de nombres: el motor y el resolutor se hablan por el valor de
    `take_profit_tipo`. Si el motor gana un tipo nuevo y nadie le asigna
    gramatica, la pieza saldria sin su "hasta donde" y en silencio."""
    import re

    from market_data_mcp.bias_reader import GRAMATICA_VIGENCIA

    fuente = (RAIZ / "scripts" / "macro_bias_engine.py").read_text(encoding="utf-8")
    emitidos = set(re.findall(r'tp_tipo\s*=\s*"([A-Z_]+)"', fuente))

    assert emitidos, "el regex dejo de encontrar las asignaciones de tp_tipo"
    huerfanos = emitidos - set(GRAMATICA_VIGENCIA)
    assert not huerfanos, (
        f"el motor emite {sorted(huerfanos)} y el resolutor no sabe con que "
        f"gramatica comunicarlo. Clasificarlo en GRAMATICA_VIGENCIA."
    )


def test_datos_incompletos_siempre_llega_sin_setups_permitidos():
    """El resolutor distingue "no hay lectura" de "la lectura es un rango" por la
    lista de setups vacia, no por el texto de la etiqueta. Este contrato es lo
    que sostiene ese criterio estructural."""
    import re

    fuente = (RAIZ / "scripts" / "macro_bias_engine.py").read_text(encoding="utf-8")
    marcas = list(re.finditer(r'sesgo_etiqueta\s*=\s*"DATOS_INCOMPLETOS"', fuente))

    assert marcas, "el regex dejo de encontrar las ramas de DATOS_INCOMPLETOS"
    for m in marcas:
        ventana = fuente[m.end(): m.end() + 400]
        assert re.search(r"setups_permitidos\s*=\s*\[\s*\]", ventana), (
            "una rama de DATOS_INCOMPLETOS declara setups permitidos: el "
            "resolutor la tomaria por un rango real y publicaria una lectura "
            "que el modelo no hizo"
        )
