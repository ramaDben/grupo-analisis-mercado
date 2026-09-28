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
