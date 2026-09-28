"""Contrato de la medición de la dirección de cuatro ejes.

Todo sintético: la suite no puede depender de las series en disco, que están
gitignoradas.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import medir_direccion as md  # noqa: E402

NY = ZoneInfo("America/New_York")
SCL = ZoneInfo("America/Santiago")


def serie_h1(inicio_utc: datetime, horas: int, *, rotulo: str = "santiago",
             pico_ny: int = 10, paso: float = 0.01) -> pd.DataFrame:
    """Velas H1 de lunes a viernes (NY), con el pico de volumen a `pico_ny`.

    `rotulo="santiago"` estampa la hora local de Santiago, como hacen las series
    reales; `rotulo="utc"` estampa UTC, que es lo que el sello dice y no es.
    """
    filas = []
    for k in range(horas):
        utc = inicio_utc + timedelta(hours=k)
        ny = utc.astimezone(NY)
        if ny.weekday() >= 5:
            continue
        stamp = (utc.astimezone(SCL) if rotulo == "santiago" else utc).replace(tzinfo=None)
        c = 100.0 + paso * k
        filas.append({"time": stamp, "open": c, "high": c + 0.5, "low": c - 0.5, "close": c,
                      "tick_volume": 1000 if ny.hour == pico_ny else 100})
    return pd.DataFrame(filas)


def escribir_serie(directorio: Path, simbolo: str, marco: str, df: pd.DataFrame, **meta) -> None:
    datos = {"symbol": simbolo, "timeframe": marco, "source": "MT5", "broker": "MT5",
             "cuenta": 51492, "timezone": "UTC", "as_of_utc": "2026-09-28T08:20:00+00:00"}
    datos.update(meta)
    filas = df.assign(time=df["time"].dt.strftime("%Y-%m-%dT%H:%M:%S")).to_dict("records")
    datos["rows"] = filas
    (directorio / f"{simbolo}_{marco}.json").write_text(json.dumps(datos), encoding="utf-8")


# ── Sellos ──────────────────────────────────────────────────────────────────
def test_cargar_serie_ordena_y_tipa(tmp_path):
    df = serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30)
    escribir_serie(tmp_path, "XAUUSD", "H1", df.iloc[::-1])
    cargada, meta = md.cargar_serie("XAUUSD", "H1", tmp_path)
    assert cargada["time"].is_monotonic_increasing
    assert list(cargada.index) == list(range(len(cargada)))
    assert meta["cuenta"] == 51492 and "rows" not in meta


@pytest.mark.parametrize("cambio", [{"source": "YFINANCE"}, {"broker": "YFINANCE"},
                                    {"cuenta": 51256}, {"cuenta": None}])
def test_serie_que_no_salio_de_mt5_o_de_la_cuenta_aborta(tmp_path, cambio):
    escribir_serie(tmp_path, "XAUUSD", "H1", serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30), **cambio)
    with pytest.raises(md.MedicionAbortada):
        md.cargar_serie("XAUUSD", "H1", tmp_path)


def test_serie_ausente_aborta(tmp_path):
    with pytest.raises(md.MedicionAbortada, match="extractor"):
        md.cargar_serie("XAUUSD", "H1", tmp_path)


# ── Zona horaria ────────────────────────────────────────────────────────────
def test_localizar_descarta_horas_ambiguas_e_inexistentes():
    df = pd.DataFrame({"time": pd.to_datetime([
        "2025-04-05 22:00", "2025-04-05 23:00", "2025-04-05 23:00",   # abril: 23:00 se repite
        "2025-04-06 00:00", "2025-09-06 23:00", "2025-09-07 00:00",   # septiembre: 00:00 no existe
        "2025-09-07 01:00"])})
    loc = md.localizar(df)
    assert loc["time_ny"].isna().tolist() == [False, True, True, False, False, True, False]
    assert len(loc) == len(df)                      # marca, no borra


def test_la_serie_en_hora_de_santiago_pasa_las_dos_pruebas():
    inicio = datetime(2025, 1, 6, 5, tzinfo=timezone.utc)
    df = serie_h1(inicio, 24 * 360, rotulo="santiago")
    ultima_utc = inicio + timedelta(hours=24 * 360 - 1)
    meta = {"as_of_utc": (ultima_utc + timedelta(minutes=20)).isoformat()}
    assert md.prueba_moda_volumen(md.localizar(df))["ok"] is True
    assert md.prueba_moda_volumen(md.localizar(df))["hora"] == 10
    r = md.prueba_hora_extraccion(df, meta)
    assert r["aplica"] is True and r["ok"] is True


def test_la_misma_serie_rotulada_en_utc_falla_y_aborta():
    inicio = datetime(2025, 1, 6, 5, tzinfo=timezone.utc)
    df = serie_h1(inicio, 24 * 360, rotulo="utc")
    assert md.prueba_moda_volumen(md.localizar(df))["ok"] is False
    ultima_utc = inicio + timedelta(hours=24 * 360 - 1)
    meta = {"as_of_utc": (ultima_utc + timedelta(minutes=20)).isoformat()}
    with pytest.raises(md.MedicionAbortada):
        md.verificar_zona({"US100": (df, meta)}, "US100")


def test_serie_de_mercado_cerrado_no_entra_a_la_prueba_de_extraccion():
    df = serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30)   # termina el martes
    meta = {"as_of_utc": "2025-03-10T08:20:00+00:00"}                   # se extrajo el lunes siguiente
    assert md.prueba_hora_extraccion(df, meta)["aplica"] is False


# ── Indicadores en serie, paridad y punto en el tiempo ──────────────────────
from market_data_mcp import analisis, mt5_client  # noqa: E402


def ohlc_aleatorio(n: int, semilla: int = 7) -> pd.DataFrame:
    rng = __import__("numpy").random.default_rng(semilla)
    c = 100 + rng.normal(0, 1, n).cumsum()
    t = pd.date_range("2025-03-03 08:00", periods=n, freq="h")
    return pd.DataFrame({"time": t, "open": c, "high": c + rng.uniform(0.1, 1, n),
                         "low": c - rng.uniform(0.1, 1, n), "close": c, "tick_volume": 100})


def test_paridad_con_analizar_activo(monkeypatch):
    """Leer la serie completa en t-1 da lo mismo que analizar_activo con df_closed."""
    df = ohlc_aleatorio(300)
    monkeypatch.setattr(mt5_client, "connect", lambda: None)
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df.copy())
    vivo = analisis.analizar_activo("XAUUSD", "H1")
    assert "error" not in vivo, vivo
    ind = md.indicadores(df).iloc[-2]                 # t-1: la última cerrada
    for campo in ("ema_50", "ema_100", "atr_14", "donchian_50_high", "donchian_50_low"):
        assert round(float(ind[campo]), 2) == vivo[campo], campo
    assert round(float(ind["adx_14"]), 1) == vivo["adx_14"]


def test_donchian_rodante_coincide_con_mt5_client():
    df = ohlc_aleatorio(200)
    alto, bajo, _ = mt5_client.donchian(df)
    ind = md.indicadores(df).iloc[-1]
    assert float(ind["donchian_50_high"]) == alto and float(ind["donchian_50_low"]) == bajo


def test_rango_hoy_no_ve_velas_posteriores_del_mismo_dia():
    df = pd.DataFrame({
        "time": pd.to_datetime(["2025-03-03 09:00", "2025-03-03 10:00", "2025-03-03 11:00", "2025-03-04 09:00"]),
        "high": [10.0, 12.0, 30.0, 5.0], "low": [9.0, 8.0, 1.0, 4.0],
    })
    assert md.rango_hoy_intradia(df).tolist() == [1.0, 4.0, 29.0, 1.0]


def test_d1_se_alinea_por_fecha_y_no_por_hora_localizada():
    """La vela D1 del 2025-09-07 tiene marca 00:00, que en Santiago no existe; no se pierde."""
    d1_time = pd.Series(pd.to_datetime(["2025-09-05", "2025-09-07", "2025-09-08"]))
    h1_time = pd.Series(pd.to_datetime(["2025-09-07 10:00", "2025-09-08 10:00", "2025-09-09 10:00"]))
    assert md.indice_d1_cerrado(h1_time, d1_time).tolist() == [0, 1, 2]


def test_lectura_en_t_no_cambia_si_se_altera_el_futuro():
    """Anti fuga: tocar las velas posteriores a t (H1 y D1 del día de t) no cambia la lectura de t."""
    h1 = ohlc_aleatorio(400)                                   # 2025-03-03 08:00 en adelante
    # D1 hasta el 2025-03-19: incluye el día de t (2025-03-15) y los siguientes
    d1 = ohlc_aleatorio(200, semilla=3).assign(time=pd.date_range("2024-09-01", periods=200, freq="D"))
    i = 300
    fecha_t = h1["time"].iloc[i].normalize()

    def leer(h1x, d1x):
        j = md.indice_d1_cerrado(h1x["time"], d1x["time"])[i]
        return md.dicts_en(i, h1x, md.indicadores(h1x), md.rango_hoy_intradia(h1x), d1x, md.indicadores(d1x), j)

    base = leer(h1, d1)
    h1_mod = h1.copy()
    h1_mod.loc[i + 1:, ["high", "low", "close"]] *= 3
    d1_mod = d1.copy()
    futuro_d1 = d1_mod["time"] >= fecha_t
    assert futuro_d1.sum() >= 2                         # el test sí toca el D1 del día de t
    d1_mod.loc[futuro_d1, ["high", "low", "close"]] *= 3
    assert leer(h1_mod, d1_mod) == base
    h1d, d1d = base
    assert h1d["price"] == float(h1["close"].iloc[i])
    assert d1d["fecha_barra"] == fecha_t.date().isoformat()


# ── Instantes que votan, métricas y giros ───────────────────────────────────
def test_ventana_sale_de_la_agenda_por_clase():
    assert md.ventana_votante("forex_commodities") == (8 * 60, 16 * 60)
    assert md.ventana_votante("indices") == (10 * 60, 16 * 60)
    with pytest.raises(md.MedicionAbortada):
        md.ventana_votante("clase_inventada")


def test_giros():
    assert md.contar_giros(["ALCISTA", "LATERAL", "ALCISTA"]) == 0
    assert md.contar_giros(["ALCISTA", "LATERAL", "BAJISTA"]) == 1
    assert md.contar_giros(["ALCISTA", "BAJISTA", "ALCISTA"]) == 2
    assert md.contar_giros([]) == 0


def test_acierta():
    assert md.acierta("ALCISTA", 0.5) and md.acierta("BAJISTA", -0.1)
    assert not md.acierta("ALCISTA", 0.0) and not md.acierta("BAJISTA", 0.0)
    assert not md.acierta("LATERAL", 1.0)


def _serie_mercado(dias: int, pendiente: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """H1 en hora de Santiago con tendencia lineal conocida, y su D1 derivado."""
    h1 = serie_h1(datetime(2024, 1, 8, 5, tzinfo=timezone.utc), 24 * dias, paso=pendiente)
    d1 = (h1.assign(fecha=h1["time"].dt.normalize())
            .groupby("fecha").agg(open=("open", "first"), high=("high", "max"),
                                  low=("low", "min"), close=("close", "last"),
                                  tick_volume=("tick_volume", "sum"))
            .reset_index().rename(columns={"fecha": "time"}))
    return h1, d1


def test_metrica_m_anti_fuga_da_el_valor_esperado():
    """Serie lineal: m = (close[t+4] - close[t]) / ATR[t-1], y el modelo acierta siempre al alza."""
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    votos = lec[lec["vota"]]
    assert len(votos) > 0
    ind = md.indicadores(h1)
    fila = votos.iloc[0]
    i = int(fila.name)
    esperado = (h1["close"].iat[i + 4] - h1["close"].iat[i]) / ind["atr_14"].iat[i - 1]
    assert fila["m"] == pytest.approx(esperado)
    assert (votos["ema50"] == "ALCISTA").all()


def test_horizonte_con_hueco_no_vota():
    """Si falta una vela dentro del horizonte, t+4 cae 5 horas después: no se mide ese m."""
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    fila = lec[lec["vota"]].iloc[5]
    i = int(fila.name)
    con_hueco = h1.drop(index=i + 2).reset_index(drop=True)   # la vela t+2 desaparece
    lec2 = md.lecturas(con_hueco, d1, "forex_commodities")
    misma = lec2[lec2["t_ny"] == fila["t_ny"]].iloc[0]
    assert not misma["vota"]
    assert misma["motivo"] == "horizonte_con_hueco"


def test_indices_cortan_al_cierre_y_exigen_tres_horas():
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "indices")
    en = lec[lec["en_sesion"]]
    cierre = (en["t_ny"] + pd.Timedelta(hours=1)).dt.hour
    assert (en.loc[cierre == 13, "h"] == 3).all() and en.loc[cierre == 13, "vota"].all()
    assert (en.loc[cierre == 14, "motivo"] == "horizonte_corto").all()
    assert not en.loc[cierre == 9].shape[0]            # antes de las 10:00 no está en sesión


def test_sin_historia_d1_se_cuenta_y_no_vota():
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    sin = lec[lec["motivo"] == "sin_historia_d1"]
    assert len(sin) > 0 and not sin["vota"].any()


def test_ic_por_dia_agrupa_y_es_reproducible():
    por_dia = pd.DataFrame({"a": [1.0, 0.0, 1.0, 1.0], "n": [1.0, 1.0, 1.0, 1.0]})
    ic1 = md.ic_por_dia(por_dia, lambda s: s["a"] / s["n"])
    ic2 = md.ic_por_dia(por_dia, lambda s: s["a"] / s["n"])
    assert ic1 == ic2 and 0.0 <= ic1[0] <= 0.75 <= ic1[1] <= 1.0


def test_resumir_trae_las_cuatro_condiciones():
    h1, d1 = _serie_mercado(260, 0.01)
    r = md.resumir(md.lecturas(h1, d1, "forex_commodities"))
    assert r["n_votos"] > 0 and r["n_dias"] > 0
    assert set(r) >= {"c1", "c2", "c3", "c4"}
    assert r["c1"]["acierto_modelo"] == pytest.approx(100.0)


# ── Regla de adopción, informe y CLI ────────────────────────────────────────
def _resumen(n=1000, c1=(55.0, 54.0, 1.0, (-0.5, 2.5)), c2_ic=(-8.0, -2.0),
             med=(0.4, 0.9), giros=(3.0, 5.0), c4=(50.0, 54.0, 58.0)):
    return {
        "n_votos": n, "n_dias": 100,
        "c1": {"acierto_modelo": c1[0], "acierto_ema50": c1[1], "diferencia": c1[2], "ic": c1[3]},
        "c2": {"ic": c2_ic, "mediana_m_lateral": med[0], "mediana_m_direccional": med[1], "n_lateral": 50,
               "acierto_ema50_lateral": 48.0, "acierto_ema50_resto": 54.0, "diferencia": -6.0},
        "c3": {"giros_modelo_100": giros[0], "giros_ema50_100": giros[1]},
        "c4": dict(zip(("debil", "moderada", "fuerte"), c4)),
    }


def test_adopta_si_cumple_1_2_y_3():
    r = md.evaluar_adopcion(_resumen(), {"XAUUSD": _resumen()})
    assert r["adopta"] is True and r["c4"] is True and r["disidentes"] == []


@pytest.mark.parametrize("cambio, condicion", [
    ({"c1": (50.0, 52.0, -2.0, (-3.5, -0.5))}, "c1"),     # límite inferior bajo -1
    ({"c2_ic": (-5.0, 0.5)}, "c2"),                       # la EMA 50 no acierta menos en LATERAL
    ({"med": (1.0, 0.9)}, "c2"),                          # LATERAL no aparta ruido
    ({"giros": (5.0, 5.0)}, "c3"),                        # empate no alcanza
])
def test_no_adopta_si_falla_una_condicion(cambio, condicion):
    r = md.evaluar_adopcion(_resumen(**cambio), {})
    assert r[condicion] is False and r["adopta"] is False


def test_conviccion_solo_si_ordena():
    assert md.evaluar_adopcion(_resumen(c4=(55.0, 54.0, 58.0)), {})["c4"] is False
    assert md.evaluar_adopcion(_resumen(c4=(50.0, None, 58.0)), {})["c4"] is False


def test_disidentes_y_activos_sin_voto():
    por_activo = {
        "XAUUSD": _resumen(c1=(50.0, 53.0, -3.0, (-5.0, -1.0))),      # 1000 votos, 3 pts bajo: disidente
        "WTI": _resumen(c1=(52.0, 53.5, -1.5, (-3.0, 0.0))),          # 1,5 pts bajo: no alcanza
        "BRENT": _resumen(n=300, c1=(40.0, 55.0, -15.0, (-20.0, -10.0))),  # < 500: no vota
    }
    r = md.evaluar_adopcion(_resumen(), por_activo)
    assert r["disidentes"] == ["XAUUSD"]
    assert r["sin_voto"] == ["BRENT"]


def test_medir_carga_us100_aunque_no_se_pida(tmp_path, monkeypatch):
    """La prueba de zona necesita el US100: se carga aunque --series no lo nombre."""
    assert md._series_a_cargar(["XAUUSD"]) == ["XAUUSD", "US100"]
    assert md._series_a_cargar(["US100"]) == ["US100"]
    pedidas = []

    def espia(simbolo, marco, directorio=md.DIR_SERIES):
        pedidas.append((simbolo, marco))
        return pd.DataFrame(columns=md.COLUMNAS), {}

    def zona_que_corta(cargadas, serie_moda):
        raise md.MedicionAbortada(f"corte del test con {sorted(cargadas)}")

    monkeypatch.setattr(md, "cargar_serie", espia)
    monkeypatch.setattr(md, "verificar_zona", zona_que_corta)
    with pytest.raises(md.MedicionAbortada, match="US100"):
        md.medir(["XAUUSD"], tmp_path)
    assert ("US100", "H1") in pedidas and ("XAUUSD", "H1") in pedidas
    assert ("US100", "D1") not in pedidas               # se carga para la prueba, no se mide


def test_main_devuelve_2_si_aborta(monkeypatch, capsys):
    monkeypatch.setattr(md, "medir", lambda *a, **k: (_ for _ in ()).throw(md.MedicionAbortada("x")))
    assert md.main([]) == 2
    assert "MEDICION ABORTADA" in capsys.readouterr().err


def test_informe_se_escribe_en_utf8_sin_guion_largo(tmp_path):
    resultado = {
        "generado": "2026-09-28 10:00", "zona": {"extraccion": {}, "moda_volumen": {}},
        "por_activo": {"XAUUSD": {**_resumen(), "descartes": {"fuera_de_sesion": 3}, "paridad_ema100_atr": 0.01,
                                  "fuera_de_sesion": _resumen(n=40)}},
        "total": _resumen(), "adopcion": md.evaluar_adopcion(_resumen(), {"XAUUSD": _resumen()}),
    }
    md_path, js_path = md.escribir_informe(resultado, tmp_path)
    texto = md_path.read_text(encoding="utf-8")
    assert "Adopción" in texto and "XAUUSD" in texto
    assert "—" not in texto and "–" not in texto
    json.loads(js_path.read_text(encoding="utf-8"))


def test_medicion_de_punta_a_punta_sobre_series_sinteticas(tmp_path, monkeypatch):
    """medir + escribir_informe corren con series en disco que pasan los sellos y la zona."""
    inicio = datetime(2024, 1, 8, 5, tzinfo=timezone.utc)
    horas = 24 * 260
    h1 = serie_h1(inicio, horas)
    ultima = inicio + timedelta(hours=horas - 1)
    while ultima.astimezone(NY).weekday() >= 5:
        ultima -= timedelta(hours=1)
    as_of = (ultima + timedelta(minutes=20)).isoformat()
    d1 = (h1.assign(fecha=h1["time"].dt.normalize()).groupby("fecha")
            .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                 close=("close", "last"), tick_volume=("tick_volume", "sum"))
            .reset_index().rename(columns={"fecha": "time"}))
    for s in ("US100", "XAUUSD"):
        escribir_serie(tmp_path, s, "H1", h1, as_of_utc=as_of)
        escribir_serie(tmp_path, s, "D1", d1, as_of_utc=as_of)
    resultado = md.medir(["XAUUSD", "US100"], tmp_path)
    assert resultado["por_activo"]["XAUUSD"]["n_votos"] > 0
    md_path, _ = md.escribir_informe(resultado, tmp_path / "salida")
    assert "Veredicto" in md_path.read_text(encoding="utf-8")


def test_el_cierre_de_t_no_entra_a_sus_propios_indicadores():
    """Anti fuga en t mismo: alterar solo la vela t cambia price y rango_hoy, nada más."""
    h1 = ohlc_aleatorio(400)
    d1 = ohlc_aleatorio(200, semilla=3).assign(time=pd.date_range("2024-09-01", periods=200, freq="D"))
    i = 300

    def leer(h1x):
        j = md.indice_d1_cerrado(h1x["time"], d1["time"])[i]
        return md.dicts_en(i, h1x, md.indicadores(h1x), md.rango_hoy_intradia(h1x), d1, md.indicadores(d1), j)

    h1b, d1b = leer(h1)
    h1_mod = h1.copy()
    h1_mod.loc[i, "close"] += 50.0
    h1_mod.loc[i, "high"] += 60.0
    h1m, d1m = leer(h1_mod)
    assert h1m["price"] != h1b["price"] and d1m["rango_hoy"] != d1b["rango_hoy"]
    assert {k: v for k, v in h1m.items() if k != "price"} == {k: v for k, v in h1b.items() if k != "price"}
    assert {k: v for k, v in d1m.items() if k not in ("price", "rango_hoy")} == \
           {k: v for k, v in d1b.items() if k not in ("price", "rango_hoy")}


def test_tolerancia_de_hueco_acepta_una_pausa_corta():
    """La sensibilidad: con tolerancia de 2 h, el horizonte que cruza una vela ausente sí vota."""
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    fila = lec[lec["vota"]].iloc[5]
    i = int(fila.name)
    con_hueco = h1.drop(index=i + 2).reset_index(drop=True)
    estricta = md.lecturas(con_hueco, d1, "forex_commodities")
    tolerante = md.lecturas(con_hueco, d1, "forex_commodities", tolerancia_hueco_h=2)
    assert not estricta.loc[estricta["t_ny"] == fila["t_ny"], "vota"].iloc[0]
    assert tolerante.loc[tolerante["t_ny"] == fila["t_ny"], "vota"].iloc[0]


def test_el_informe_declara_donde_cae_la_muestra_y_la_sensibilidad(tmp_path):
    base = _resumen()
    resultado = {
        "generado": "2026-09-28 10:00", "zona": {"extraccion": {}, "moda_volumen": {}},
        "por_activo": {"XAUUSD": {**base, "descartes": {}, "paridad_ema100_atr": 0.01,
                                  "fuera_de_sesion": {"n_votos": 0},
                                  "por_hora_ny": {"09:00": {"votan": 300, "horizonte_con_hueco": 0},
                                                  "14:00": {"votan": 10, "horizonte_con_hueco": 290}}}},
        "total": base, "adopcion": md.evaluar_adopcion(base, {"XAUUSD": base}),
        "sensibilidad_hueco": {"tolerancia_horas": 2, "n_votos": 1500,
                               "adopcion": md.evaluar_adopcion(base, {})},
    }
    texto = md.escribir_informe(resultado, tmp_path)[0].read_text(encoding="utf-8")
    assert "Dónde cae la muestra" in texto and "| 14:00 | 10 | 290 |" in texto
    assert "Sensibilidad" in texto and "1500" in texto


def test_medir_guarda_la_hora_de_la_muestra_y_la_sensibilidad(tmp_path):
    inicio = datetime(2024, 1, 8, 5, tzinfo=timezone.utc)
    horas = 24 * 260
    h1 = serie_h1(inicio, horas)
    ultima = inicio + timedelta(hours=horas - 1)
    while ultima.astimezone(NY).weekday() >= 5:
        ultima -= timedelta(hours=1)
    as_of = (ultima + timedelta(minutes=20)).isoformat()
    d1 = (h1.assign(fecha=h1["time"].dt.normalize()).groupby("fecha")
            .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                 close=("close", "last"), tick_volume=("tick_volume", "sum"))
            .reset_index().rename(columns={"fecha": "time"}))
    for s in ("US100", "XAUUSD"):
        escribir_serie(tmp_path, s, "H1", h1, as_of_utc=as_of)
        escribir_serie(tmp_path, s, "D1", d1, as_of_utc=as_of)
    r = md.medir(["XAUUSD", "US100"], tmp_path)
    horas_x = r["por_activo"]["XAUUSD"]["por_hora_ny"]
    assert sum(v["votan"] for v in horas_x.values()) == r["por_activo"]["XAUUSD"]["n_votos"]
    assert r["sensibilidad_hueco"]["tolerancia_horas"] == md.valor("sensibilidad_hueco_horas")
    assert "adopta" in r["sensibilidad_hueco"]["adopcion"]
