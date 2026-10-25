"""Los drivers del día, medidos por Python: nivel, fecha, cambio, efecto y si acompañan la lectura."""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import hechos as hc  # noqa: E402

HOY = date(2026, 10, 17)  # sábado
CURVA = {"series": {
    "DFII10": {"status": "OK", "nivel_pct": 2.78, "fecha_dato": "2026-10-15", "delta_1d_bps": -6.0, "delta_5d_bps": -14.0},
    "DGS10": {"status": "OK", "nivel_pct": 5.10, "fecha_dato": "2026-10-15", "delta_1d_bps": -9.0, "delta_5d_bps": -18.0},
    "DFF": {"status": "OK", "nivel_pct": 3.88, "fecha_dato": "2026-10-15", "delta_1d_bps": 0.0, "delta_5d_bps": 0.0},
}}
DECISION = {"dia": "miércoles 21/10", "hora": "15:00 CLST", "fuente_nombre": "Fed Interest Rate Decision"}


def serie(*cierres, hasta=date(2026, 10, 16)):
    return [(hasta - timedelta(days=len(cierres) - 1 - i), c) for i, c in enumerate(cierres)]


DXY = serie(101.848, 101.9, 101.95, 101.85, 101.80, 101.753, 101.56)


def lector(series):
    return lambda simbolo, n: series.get(simbolo, [])


def medir_oro(series=None, curva=CURVA, direccion="BAJISTA", **kw):
    return hc.medir("XAUUSD", "Oro", direccion, curva, [DECISION], lector({"USDIDX": DXY} if series is None else series), HOY, **kw)


def test_los_signos_salen_de_drivers_json():
    assert hc.signos("XAUUSD") == {"dxy": -1, "tasa_real": -1, "fed": -1}
    assert hc.signos("USDCLP") == {"cobre": -1, "dxy": 1}


def test_el_dxy_del_oro_trae_nivel_fecha_cambio_y_efecto():
    hechos, avisos = medir_oro()
    assert [h["id"] for h in hechos] == ["dxy", "tasa_real", "fed"] and avisos == []
    dxy = hechos[0]
    assert (dxy["nivel"], dxy["cambio_1d"], dxy["cambio_5d"]) == ("101,560", "0,193", "0,340")
    assert dxy["fecha"] == "viernes 16/10" and dxy["en_curso"] is False  # un sábado, el cierre es del viernes
    assert dxy["sentido"] == "bajó" and dxy["efecto"] == "juega a favor del alza del oro"
    assert dxy["con_la_lectura"] == "va en contra de nuestra lectura" and dxy["fuente"] == "MT5 (USDIDX)"


def test_la_tasa_real_va_en_por_ciento_y_puntos_base_sin_signo_porcentaje():
    tasa = medir_oro()[0][1]
    assert tasa["nivel"] == "2,78 por ciento" and tasa["cambio_5d"] == "14 pb" and tasa["fecha"] == "jueves 15/10"
    assert tasa["efecto"] == "juega a favor del alza del oro"
    assert "%" not in json.dumps(medir_oro()[0], ensure_ascii=False)


def test_la_fed_quieta_no_tiene_efecto_y_dice_su_proxima_decision():
    fed = medir_oro()[0][2]
    assert fed["sentido"] == "estable" and fed["efecto"] is None and fed["con_la_lectura"] is None
    assert fed["proxima_decision"] == "miércoles 21/10 15:00 CLST"


def test_con_lectura_alcista_el_mismo_efecto_acompana():
    assert medir_oro(direccion="ALCISTA")[0][0]["con_la_lectura"] == "acompaña nuestra lectura"


def test_con_lectura_lateral_no_se_compara():
    assert medir_oro(direccion="LATERAL")[0][0]["con_la_lectura"] is None


def test_bajo_el_umbral_es_estable_y_sin_efecto():
    quieto = serie(101.5, 101.5, 101.5, 101.5, 101.5, 101.55, 101.6)
    dxy = medir_oro({"USDIDX": quieto})[0][0]
    assert dxy["sentido"] == "estable" and dxy["efecto"] is None


def test_la_vela_de_hoy_queda_en_curso():
    hoy = serie(101.848, 101.9, 101.95, 101.85, 101.80, 101.753, 101.56, hasta=HOY)
    assert medir_oro({"USDIDX": hoy})[0][0]["en_curso"] is True


def test_sin_usdidx_el_dxy_sale_del_respaldo_y_lo_dice():
    hechos, _ = medir_oro({}, respaldo_dxy=lambda n: DXY)
    assert "yfinance" in hechos[0]["fuente"] and hechos[0]["nivel"] == "101,560"


def test_lo_que_no_se_puede_medir_se_avisa_y_no_se_inventa():
    hechos, avisos = medir_oro(curva={})
    assert [h["id"] for h in hechos] == ["dxy"]
    assert any("Tasa real" in a for a in avisos) and any("Fed" in a for a in avisos)


def test_un_activo_sin_ficha_recibe_los_generales_sin_efecto():
    hechos, _ = hc.medir("BTCUSD", "Bitcoin", "ALCISTA", CURVA, [], lector({"USDIDX": DXY}), HOY)
    assert [h["id"] for h in hechos] == ["dxy", "bono_10"]
    assert all(h["efecto"] is None and h["con_la_lectura"] is None for h in hechos)


def test_usdchf_y_gbpusd_tienen_ficha_de_drivers_y_no_caen_en_generales_sin_signo():
    chf = hc.signos("USDCHF")
    assert chf["dxy"] == 1 and set(chf) >= {"dxy", "bono_10"}
    assert chf["bono_10"] == 0  # correlacion no confirmada: se describe, no se interpreta
    gbp = hc.signos("GBPUSD")
    assert gbp["dxy"] == -1 and gbp["bono_10"] == 0


def test_el_cobre_del_dolar_usa_los_digitos_del_simbolo():
    cobre = serie(14600.0, 14550.0, 14500.0, 14450.0, 14400.0, 14300.0, 14197.0)
    hechos, _ = hc.medir("USDCLP", "Dólar", "ALCISTA", CURVA, [], lector({"USDIDX": DXY, "COPPER": cobre}), HOY)
    c = next(h for h in hechos if h["id"] == "cobre")
    assert c["nivel"] == "14197" and c["cambio_5d"] == "353" and c["sentido"] == "bajó"
    assert c["efecto"] == "juega a favor del alza del USD/CLP" and c["con_la_lectura"] == "acompaña nuestra lectura"


def test_con_el_terminal_caido_el_dxy_sale_del_respaldo():
    def cae(simbolo, n):
        raise RuntimeError("MT5 cerrado")

    hechos, avisos = hc.medir("XAUUSD", "Oro", "BAJISTA", CURVA, [DECISION], cae, HOY, respaldo_dxy=lambda n: DXY)
    dxy = hechos[0]
    assert dxy["id"] == "dxy" and "yfinance" in dxy["fuente"] and dxy["nivel"] == "101,560"
    assert not any("Dollar Index" in a for a in avisos)


def test_con_pocos_puntos_en_mt5_el_dxy_sale_del_respaldo():
    corta = serie(101.9, 101.8, 101.7)
    hechos, _ = medir_oro({"USDIDX": corta}, respaldo_dxy=lambda n: DXY)
    assert "yfinance" in hechos[0]["fuente"] and hechos[0]["nivel"] == "101,560"


def test_sin_respaldo_y_con_el_terminal_caido_el_dxy_se_avisa():
    def cae(simbolo, n):
        raise RuntimeError("MT5 cerrado")

    hechos, avisos = hc.medir("XAUUSD", "Oro", "BAJISTA", CURVA, [], cae, HOY)
    assert "dxy" not in [h["id"] for h in hechos] and any("Dollar Index" in a for a in avisos)


def test_la_fed_sin_decision_en_la_ventana_no_trae_proxima_decision():
    hechos, _ = hc.medir("XAUUSD", "Oro", "BAJISTA", CURVA, [], lector({"USDIDX": DXY}), HOY)
    assert next(h for h in hechos if h["id"] == "fed")["proxima_decision"] is None


def test_brent_cobre_y_plata_tienen_ficha_de_drivers():
    brent = hc.signos("BRENT.spot")
    assert brent["petroleo"] == 1 and brent["dxy"] == -1
    cobre = hc.signos("COPPER")
    assert cobre["dxy"] == -1 and set(cobre) >= {"dxy", "bono_10"}
    plata = hc.signos("XAGUSD")
    assert plata["dxy"] == -1 and plata["tasa_real"] == -1
    # correlacion no confirmada: sin signo
    assert brent["bono_10"] == 0 and cobre["bono_10"] == 0


def test_los_inventarios_eia_calculan_su_hora_con_el_helper():
    import shutil
    import subprocess

    if shutil.which("powershell") is None:  # el helper es PowerShell de Windows; el CI corre en Linux
        pytest.skip("sin powershell")

    datos = json.loads((RAIZ / "config" / "drivers.json").read_text(encoding="utf-8"))
    pub = datos["WTI"]["drivers"]["inventarios_eia"]["publicacion"]
    assert pub["zona_origen"] == "Eastern Standard Time" and re.fullmatch(r"\d\d:\d\d", pub["hora_origen"])
    assert "hora_chile" not in pub and "CLT" not in json.dumps(pub)  # ninguna hora de Chile escrita a mano
    salida = subprocess.run(["powershell", "-NoProfile", "-File", str(RAIZ / "scripts" / "hora_chile.ps1"),
                             "-Hora", pub["hora_origen"], "-ZonaOrigen", pub["zona_origen"],
                             "-Fecha", "2026-10-21"], capture_output=True, text=True, check=True).stdout.strip()
    assert re.fullmatch(r"\d\d:\d\d CLS?T", salida)


def test_cada_indice_tiene_ficha_y_no_cae_en_generales():
    generales = {"dxy": 0, "bono_10": 0}
    for t in ("US500.spot", "US30.spot", "GER40.spot"):
        assert hc.signos(t) != generales, t
    assert hc.signos("US500.spot")["fed"] == -1 and hc.signos("US500.spot")["bono_10"] == -1
    # GER40: sin correlacion confirmada con el dolar ni la energia, va sin signo
    assert hc.signos("GER40.spot").get("dxy") == 0 and hc.signos("GER40.spot").get("petroleo") == 0


def test_xetra_tiene_feriados_y_alemania_esta_en_la_agenda():
    import json
    from analista import agenda as ag
    from market_data_mcp.tools import symbol_spec as ss

    datos = json.loads(ss._FERIADOS_PATH.read_text(encoding="utf-8"))
    assert len(datos["XETRA"]) >= 7 and "2026-12-25" in datos["XETRA"]
    assert ss._TICKER_EXCHANGE["GER40.spot"] == "XETRA"
    assert ss._cargar_feriados()["XETRA"] == datos["XETRA"]
    assert ag.PAISES["Germany"] == "Alemania"


def test_spy_hereda_los_drivers_del_sp500_como_qqq_los_del_nasdaq():
    """Revisión final: SPY.US caía en los generales; su subyacente US500 tiene ficha propia."""
    assert hc.signos("SPY.US") == hc.signos("US500.spot")
    assert hc.signos("SPY.US") != {m: 0 for m in hc.GENERALES}
    assert hc.signos("QQQ.US") == hc.signos("US100.spot")
