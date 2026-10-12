"""El registro semanal: una foto por semana, reusada por todos los ejecutivos."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import registro_semanal as rg  # noqa: E402

SCL = ZoneInfo("America/Santiago")


def _pieza(tmp_path: Path, nombre: str) -> Path:
    d = tmp_path / nombre
    d.mkdir()
    (d / "pieza.json").write_text("{}", encoding="utf-8")
    return d


def test_sin_registro_no_hay_foto(tmp_path):
    assert rg.foto("2026-W42", tmp_path / "registro.json") is None


def test_anotar_y_reusar_la_foto_de_la_semana(tmp_path):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, "a")
    rg.anotar_foto("2026-W42", d, datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD", "USDCLP"], ruta)
    f = rg.foto("2026-W42", ruta)
    assert f["dir"] == str(d) and f["tickers"] == ["XAUUSD", "USDCLP"]
    assert f["creada"].startswith("2026-10-12T09:00")


def test_la_foto_de_la_semana_anterior_no_se_reusa(tmp_path):
    ruta = tmp_path / "registro.json"
    rg.anotar_foto("2026-W41", _pieza(tmp_path, "a"), datetime(2026, 10, 5, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    assert rg.foto("2026-W42", ruta) is None


def test_una_foto_cuya_carpeta_se_borro_no_se_reusa(tmp_path):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, "a")
    rg.anotar_foto("2026-W42", d, datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    (d / "pieza.json").unlink()
    assert rg.foto("2026-W42", ruta) is None


def test_los_seguimientos_quedan_en_la_historia_de_la_foto(tmp_path):
    ruta = tmp_path / "registro.json"
    rg.anotar_foto("2026-W42", _pieza(tmp_path, "a"), datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    rg.anotar_seguimiento("2026-W42", "XAUUSD", {"estado": "en_curso", "ejecutivo": "111"}, ruta)
    assert rg.foto("2026-W42", ruta)["seguimientos"] == [
        {"ticker": "XAUUSD", "estado": "en_curso", "ejecutivo": "111"}]


def test_un_registro_corrupto_no_se_sobrescribe(tmp_path):
    import pytest

    ruta = tmp_path / "registro.json"
    ruta.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError):
        rg.anotar_foto("2026-W42", _pieza(tmp_path, "a"), datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    assert ruta.read_text(encoding="utf-8") == "{no es json"
