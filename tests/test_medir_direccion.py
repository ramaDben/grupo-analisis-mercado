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
