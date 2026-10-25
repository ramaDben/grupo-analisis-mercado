"""El dato de tasas del banco central que mueve al activo (spec 2026-10-24 §3)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import tasa_banco as tb  # noqa: E402

AHORA = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)  # viernes


def _raiz(tmp_path: Path, as_of: str = "2026-10-23T12:00:00+00:00") -> Path:
    fed = tmp_path / "data central" / "DATA USA" / "raw" / "treasury_fed_data.json"
    fed.parent.mkdir(parents=True)
    fed.write_text(json.dumps({"as_of": as_of, "curva_rendimientos_yields": {"DFF": {
        "historico": {"2026-10-21": 3.88, "2026-10-22": 3.875}}}}), encoding="utf-8")
    cl = tmp_path / "data central" / "DATA CHILE" / "raw" / "bcch_macro_data.json"
    cl.parent.mkdir(parents=True)
    cl.write_text(json.dumps({"as_of": as_of, "series": {"TPM": {"historico": {"2026-10-20": 4.5}}}}), encoding="utf-8")
    return tmp_path


def test_oro_lee_la_fed(tmp_path):
    t, aviso = tb.leer("XAUUSD", "forex_commodities", AHORA, raiz=_raiz(tmp_path))
    assert aviso is None
    assert t["banco"] == "fed" and t["serie"] == "Tasa efectiva de fondos federales"
    assert t["fecha"] == "22/10" and t["motivo_imagen"] == "banco_central"


def test_valor_con_coma_y_dos_decimales(tmp_path):
    t, _ = tb.leer("XAUUSD", "forex_commodities", AHORA, raiz=_raiz(tmp_path))
    assert t["valor"] == "3,88"  # 3,875 redondeado a dos decimales


def test_usdclp_lee_el_bcch(tmp_path):
    t, _ = tb.leer("USDCLP", "forex_commodities", AHORA, raiz=_raiz(tmp_path))
    assert t["banco"] == "bcch" and t["valor"] == "4,50" and t["fecha"] == "20/10"


def test_activo_sin_banco_devuelve_none(tmp_path):
    assert tb.leer("RARO", "clase_inexistente", AHORA, raiz=_raiz(tmp_path)) == (None, None)


def test_archivo_vencido_devuelve_aviso(tmp_path):
    t, aviso = tb.leer("XAUUSD", "forex_commodities", AHORA, raiz=_raiz(tmp_path, "2026-10-15T12:00:00+00:00"))
    assert t is None and "Reserva Federal" in aviso


def test_archivo_ausente_devuelve_aviso(tmp_path):
    t, aviso = tb.leer("EURUSD", "forex_commodities", AHORA, raiz=_raiz(tmp_path))
    assert t is None and aviso


def test_config_real_tiene_linea_por_banco():
    cfg = tb.cargar_config()
    assert set(cfg["bancos"]) == {"fed", "bcch", "bce"}
    assert all(b["linea"] and b["serie"] for b in cfg["bancos"].values())
    assert "tasa de la Fed" not in json.dumps(cfg["bancos"], ensure_ascii=False)
